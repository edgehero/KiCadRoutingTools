#!/usr/bin/env python3
"""gpm audit A: did every board start cleared, and did every run start from that board?

    python3 -X utf8 wk/gpm/_audit/audit_start.py        (from krt-gpm)

Per board:
  1. the given inputs in the board folder still hash to what staging recorded (_truth/<stem>/stage.json);
  2. the given pile, raw-text census: 0 segments/arcs/vias, 0 zone fills, 0 board text, 0 drawings off
     Edge.Cuts, 0 locked footprints and 0 locked pads; and, from pad geometry, 0 footprints with a pad
     inside the outline's bounding box (stricter than inside the outline);
  3. every placed_from/fixed.kicad_pcb the run placed from (kept pass and old passes): 0 copper, and every
     footprint either at its pile pose or at a pose the intent it was placed with declares (fixed_poses);
  4. final_route/in.kicad_pcb (where the shipped route started): 0 copper.
Positive control: the same census on the human board must find copper, text and parts on the board.
"""
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [HERE, os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_tools')]
from sexp_census import census  # noqa: E402
from kicad_parser import parse_kicad_pcb  # noqa: E402

G = os.path.join(ROOT, 'wk', 'gpm')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def pads_on_board(path, bbox):
    pcb = parse_kicad_pcb(path)
    x0, y0, x1, y1 = bbox
    on = []
    for key, fp in pcb.footprints.items():
        for p in fp.pads:
            if p.global_x + p.size_x / 2 > x0 and p.global_x - p.size_x / 2 < x1 and \
               p.global_y + p.size_y / 2 > y0 and p.global_y - p.size_y / 2 < y1:
                on.append(key)
                break
    return on


def copper(c):
    return c['segments'] + c['arcs'] + c['vias'] + c['zone_fills']


def poses(fps):
    return {f['ref']: (f['x'], f['y'], f['rot'] % 360, f['layer']) for f in fps}


def same(a, b, tol=0.002):
    return a and b and abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol and \
        min(abs(a[2] - b[2]), 360 - abs(a[2] - b[2])) < 0.05 and a[3] == b[3]


rows, bad = [], []
for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*'))):
    nn_stem = os.path.basename(d)
    stem = nn_stem[3:]
    st = json.load(open(os.path.join(G, '_truth', stem, 'stage.json')))
    r = {'board': nn_stem, 'problems': []}
    # 1 hashes
    for f, h in st['inputs'].items():
        p = os.path.join(d, f)
        if not os.path.isfile(p):
            r['problems'].append(f'given input missing: {f}')
        elif sha(p) != h:
            r['problems'].append(f'given input CHANGED since staging: {f}')
    # 2 the pile
    pile = os.path.join(d, f'{stem}.kicad_pcb')
    c, fps = census(pile)
    r['pile'] = {k: c[k] for k in ('segments', 'arcs', 'vias', 'zone_fills', 'board_text', 'drawings_off_edgecuts',
                                   'images', 'locked_pads', 'footprints')}
    r['pile']['locked_footprints'] = len(c['locked_footprints'])
    on = pads_on_board(pile, c['outline_bbox'])
    r['pile']['parts_with_pads_on_board'] = len(on)
    for k in ('segments', 'arcs', 'vias', 'zone_fills', 'board_text', 'drawings_off_edgecuts', 'images',
              'locked_pads', 'locked_footprints', 'parts_with_pads_on_board'):
        if r['pile'][k]:
            r['problems'].append(f'pile {k} = {r["pile"][k]}' + (f' {on[:8]}' if k == 'parts_with_pads_on_board' else ''))
    pile_pose = poses(fps)
    # positive control: the human board
    hc, hfps = census(os.path.join(G, '_truth', stem, 'human.kicad_pcb'))
    hon = pads_on_board(os.path.join(G, '_truth', stem, 'human.kicad_pcb'), hc['outline_bbox'])
    r['human_control'] = {'copper': copper(hc), 'board_text': hc['board_text'], 'parts_on_board': len(hon),
                          'locked_footprints': len(hc['locked_footprints'])}
    if not (copper(hc) and len(hon)):
        r['problems'].append('positive control did not fire on the human board')
    human_pose = poses(hfps)
    # 3 every fixed.kicad_pcb the run placed from
    r['placed_from'] = []
    for pf in sorted(glob.glob(os.path.join(d, 'placed_from', 'fixed.kicad_pcb')) +
                     glob.glob(os.path.join(d, 'old', '*', 'placed_from', 'fixed.kicad_pcb'))):
        fc, ffps = census(pf)
        intents = [p for p in glob.glob(os.path.join(os.path.dirname(pf), '*.json')) if 'intent' in os.path.basename(p)]
        declared = set()
        for ip in intents:
            try:
                declared |= {fp['ref'] for fp in json.load(open(ip)).get('fixed_poses', [])}
            except (ValueError, OSError):
                pass
        moved = [ref for ref, ps in poses(ffps).items() if not same(ps, pile_pose.get(ref))]
        undeclared = [ref for ref in moved if ref not in declared]
        at_human = [ref for ref in undeclared if same(poses(ffps)[ref], human_pose.get(ref))]
        e = {'file': os.path.relpath(pf, d), 'copper': copper(fc), 'locked': len(fc['locked_footprints']),
             'moved_from_pile': len(moved), 'declared': len(declared), 'moved_undeclared': undeclared[:12],
             'undeclared_at_human_pose': at_human}
        r['placed_from'].append(e)
        if fc['segments'] + fc['arcs'] + fc['vias']:
            r['problems'].append(f'{e["file"]} has copper {copper(fc)}')
        if at_human:
            r['problems'].append(f'{e["file"]}: undeclared parts at the HUMAN pose {at_human}')
    if not r['placed_from']:
        r['problems'].append('no placed_from/fixed.kicad_pcb')
    # 4 where the shipped route started
    fin = os.path.join(d, 'final_route', 'in.kicad_pcb')
    if os.path.isfile(fin):
        ic, _ = census(fin)
        r['final_route_in_copper'] = ic['segments'] + ic['arcs'] + ic['vias']
        if r['final_route_in_copper']:
            r['problems'].append(f'final_route/in.kicad_pcb starts with copper {r["final_route_in_copper"]}')
    else:
        r['problems'].append('no final_route/in.kicad_pcb')
    rows.append(r)
    print(f'{nn_stem:32s} pile: {sum(v for k, v in r["pile"].items() if k != "footprints")} non-zero counts, '
          f'{r["pile"]["footprints"]} parts | human control: copper {r["human_control"]["copper"]}, '
          f'{r["human_control"]["parts_on_board"]} on board, {r["human_control"]["locked_footprints"]} locked | '
          f'placed_from {[(e["moved_from_pile"], e["declared"], len(e["moved_undeclared"]), e["copper"]) for e in r["placed_from"]]} '
          f'| route-in copper {r.get("final_route_in_copper")} | PROBLEMS {r["problems"] or "none"}')
json.dump(rows, open(os.path.join(HERE, 'audit_start.json'), 'w'), indent=1)
print('boards with problems:', [r['board'] for r in rows if r['problems']])
