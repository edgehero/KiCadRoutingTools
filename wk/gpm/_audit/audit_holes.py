#!/usr/bin/env python3
"""gpm audit D: are the mounting holes right on every delivered board?

    python3 -X utf8 wk/gpm/_audit/audit_holes.py        (from krt-gpm)

A hole part = a footprint with <= 9 pads whose largest drill is >= 2.0 mm (a screw hole, a standoff, a spacer),
or whose library name says MountingHole / Standoff / Spacer. For each one, on delivered.kicad_pcb against the
human board:
  pose     at the human pose (0.005 mm, 0.05 deg, same side), and declared in the given intent's fixed_poses;
  net      its pads' net, human vs delivered (a plated hole tied to GND must stay tied);
  ring     the keep-out ring = the hole's own courtyard radius (else drill/2 + 1.0 mm): other parts whose
           courtyard reaches into it, and other-net copper (tracks, vias, pads) inside it, both faces --
           the same count on the human board is the reference.
"""
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
from kicad_parser import parse_kicad_pcb, iter_footprint_blocks  # noqa: E402
from placement.parser import extract_courtyard_bboxes  # noqa: E402

G = os.path.join(ROOT, 'wk', 'gpm')
NAME = re.compile(r'MountingHole|Standoff|Spacer|9774', re.I)


def holes(pcb):
    out = {}
    for r, f in pcb.footprints.items():
        drills = [p.drill for p in f.pads if p.drill]
        if f.pads and len(f.pads) <= 9 and ((drills and max(drills) >= 2.0) or NAME.search(f.footprint_name)):
            out[r] = f
    return out


def ring_radius(text, ref, f):
    """the hole's courtyard circle radius from its own fp_circle on *.CrtYd, else drill/2 + 1.0"""
    for _s, _e, blk, _raw, key in iter_footprint_blocks(text):
        if key != ref:
            continue
        for m in re.finditer(r'\(fp_circle\s*\(center ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(.*?)\(layer "?([FB]\.CrtYd)', blk, re.S):
            cx, cy, ex, ey = map(float, m.groups()[:4])
            return math.hypot(ex - cx, ey - cy), 'courtyard'
    d = max((p.drill for p in f.pads if p.drill), default=2.0)
    return d / 2 + 1.0, 'drill+1.0'


def census(path):
    pcb = parse_kicad_pcb(path)
    text = open(path, encoding='utf-8', errors='replace').read()
    cy = extract_courtyard_bboxes(path)
    out = {}
    for r, f in holes(pcb).items():
        R, basis = ring_radius(text, r, f)
        nets = sorted({p.net_name or '' for p in f.pads})
        own = {p.net_id for p in f.pads if p.net_id}
        parts = []
        for rr, bb in cy.items():
            if rr == r or rr not in pcb.footprints:
                continue
            x0, y0, x1, y1 = bb
            dx = max(x0 - f.x, 0, f.x - x1); dy = max(y0 - f.y, 0, f.y - y1)
            if math.hypot(dx, dy) < R - 0.05:
                parts.append(rr)
        cu = 0
        for s in pcb.segments:
            if getattr(s, 'graphic', False) or s.net_id in own:
                continue
            ax, ay, bx, by = s.start_x, s.start_y, s.end_x, s.end_y
            L2 = (bx - ax) ** 2 + (by - ay) ** 2
            t = 0 if L2 == 0 else max(0, min(1, ((f.x - ax) * (bx - ax) + (f.y - ay) * (by - ay)) / L2))
            if math.hypot(ax + t * (bx - ax) - f.x, ay + t * (by - ay) - f.y) - s.width / 2 < R:
                cu += 1
        for v in pcb.vias:
            if v.net_id not in own and math.hypot(v.x - f.x, v.y - f.y) - v.size / 2 < R:
                cu += 1
        for rr, ff in pcb.footprints.items():
            if rr == r:
                continue
            for p in ff.pads:
                if p.net_id and p.net_id not in own and math.hypot(p.global_x - f.x, p.global_y - f.y) - max(p.size_x, p.size_y) / 2 < R:
                    cu += 1
        out[r] = {'pose': (round(f.x, 3), round(f.y, 3), round(f.rotation % 360, 2), f.layer), 'nets': nets,
                  'R': round(R, 2), 'basis': basis, 'parts': parts, 'foreign_cu': cu,
                  'name': f.footprint_name.split(':')[-1]}
    return out


rows = []
tot = {'holes': 0, 'moved': 0, 'undeclared': 0, 'net_changed': 0, 'parts_new': 0, 'cu_new': 0}
for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*'))):
    stem = os.path.basename(d)[3:]
    h = census(os.path.join(G, '_truth', stem, 'human.kicad_pcb'))
    o = census(os.path.join(d, 'delivered.kicad_pcb'))
    declared = {fp['ref']: fp for fp in json.load(open(os.path.join(d, 'intent.json'))).get('fixed_poses', [])}
    for r in sorted(set(h) | set(o)):
        a, b = h.get(r), o.get(r)
        if not (a and b):
            rows.append(f'{stem} {r}: only on the {"human" if a else "delivered"} board')
            continue
        tot['holes'] += 1
        moved = not (abs(a['pose'][0] - b['pose'][0]) < .005 and abs(a['pose'][1] - b['pose'][1]) < .005 and a['pose'][3] == b['pose'][3])
        und = r not in declared
        netc = a['nets'] != b['nets']
        newp = sorted(set(b['parts']) - set(a['parts']))
        tot['moved'] += moved; tot['undeclared'] += und; tot['net_changed'] += netc
        tot['parts_new'] += bool(newp); tot['cu_new'] += b['foreign_cu'] > a['foreign_cu']
        flag = []
        if moved: flag.append(f'MOVED {a["pose"]} -> {b["pose"]}')
        if und: flag.append('not declared')
        if netc: flag.append(f'NET {a["nets"]} -> {b["nets"]}')
        if newp: flag.append(f'parts in its ring not on the human board: {newp} (human: {a["parts"]})')
        if b['foreign_cu'] > a['foreign_cu']: flag.append(f'other-net copper in the ring {a["foreign_cu"]} -> {b["foreign_cu"]}')
        rows.append(f'{stem} {r} ({b["name"][:34]}, ring r {b["R"]} {b["basis"]}, nets {b["nets"]}): ' + ('; '.join(flag) if flag else 'ok'))
print('\n'.join(rows))
print('TOTAL', tot)
