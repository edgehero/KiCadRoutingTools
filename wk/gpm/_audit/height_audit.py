#!/usr/bin/env python3
"""gpm audit F: height-aware placement checks, on every delivered board against its human board.

    python3 -X utf8 wk/gpm/_audit/height_audit.py        (from krt-gpm)

Part heights and plan rectangles come from KiCad's own 3D models (part_heights.py). Three measures:
  under    a part under a FLOATING body on its side (a body whose underside is >= 0.5 mm above the board: a
           module on a stacking connector, a display) that is taller than that underside;
  plug     a connector mated from above (not declared on an edge) with a part taller than itself within
           1.5 mm of its body: the plug and the fingers that hold it need that ring;
  jammed   a part <= 2 mm tall with parts >= 4 mm (and >= 3x its height) on two OPPOSITE sides, each closer
           than half its own height: it cannot be soldered, inspected or reworked from the side.
Parts without a model are not graded; the model coverage is printed.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [HERE, os.path.join(ROOT, 'py_router')]
from part_heights import heights  # noqa: E402
from kicad_parser import parse_kicad_pcb  # noqa: E402

G = os.path.join(ROOT, 'wk', 'gpm')
CONN = re.compile(r'^(J|P|CN|X)\d', re.I)
VERT = re.compile(r'Vertical|PinHeader(?!.*Horizontal)|PinSocket(?!.*Horizontal)|IDC|Box|JST.*_B\d|Molex.*Vertical', re.I)


def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return max(dx, dy) if (dx == 0 or dy == 0) else (dx * dx + dy * dy) ** .5


def underside(path, stem):
    """per-part height of the body's bottom above its own face (from the same GLB pass)."""
    return None


def measure(board, stem, edge_refs):
    hs, info = heights(board, stem)
    pcb = parse_kicad_pcb(board)
    parts = {r: v for r, v in hs.items() if v['height'] is not None and v['rect']}
    res = {'under': [], 'plug': [], 'jammed': [], 'info': info}
    # under: a FLOATING body (its underside >= 0.5 mm above its face: a module on a stacking connector, a
    # display) over a part on the same side that is taller than that underside
    for r, v in parts.items():
        if v.get('bottom') is None or v['bottom'] < 0.5:
            continue
        x0, y0, x1, y1 = v['rect']
        for rr, vv in parts.items():
            if rr == r or vv['side'] != v['side']:
                continue
            ff = pcb.footprints[rr]
            if x0 < ff.x < x1 and y0 < ff.y < y1 and vv['height'] > v['bottom']:
                res['under'].append((r, round(v['bottom'], 2), rr, vv['height']))
    for r, v in parts.items():
        f = pcb.footprints[r]
        if CONN.match(r) and VERT.search(f.footprint_name) and r not in edge_refs:
            near = [(rr, vv['height']) for rr, vv in parts.items() if rr != r and vv['side'] == v['side']
                    and vv['height'] > v['height'] and gap(v['rect'], vv['rect']) < 1.5]
            if near:
                res['plug'].append((r, round(v['height'], 1), near[:4]))
    for r, v in parts.items():
        if v['height'] > 2.0:
            continue
        x0, y0, x1, y1 = v['rect']
        sides = set()
        for rr, vv in parts.items():
            if rr == r or vv['side'] != v['side'] or vv['height'] < max(4.0, 3 * v['height']):
                continue
            if gap(v['rect'], vv['rect']) < vv['height'] / 2:
                a = vv['rect']
                if a[2] <= x0: sides.add('W')
                elif a[0] >= x1: sides.add('E')
                if a[3] <= y0: sides.add('N')
                elif a[1] >= y1: sides.add('S')
        if {'W', 'E'} <= sides or {'N', 'S'} <= sides:
            res['jammed'].append(r)
    return res


if __name__ == '__main__':
    out = {}
    for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*'))):
        stem = os.path.basename(d)[3:]
        intent = json.load(open(os.path.join(d, 'intent.json')))
        edges = {e['ref'] for e in intent.get('edge_connectors', [])}
        try:
            run = json.load(open(os.path.join(d, 'intent_run.json')))
            edges |= {e['ref'] for e in run.get('edge_connectors', [])}
        except (OSError, ValueError):
            pass
        h = measure(os.path.join(G, '_truth', stem, 'human.kicad_pcb'), stem, edges)
        o = measure(os.path.join(d, 'delivered.kicad_pcb'), stem, edges)
        out[stem] = {'human': h, 'delivered': o}
        print(f"{stem:28s} models {o['info']['with_model']}/{o['info']['parts']} | under-cover human {len(h['under'])} delivered {len(o['under'])} "
              f"| plug-ring human {len(h['plug'])} delivered {len(o['plug'])} | jammed human {len(h['jammed'])} delivered {len(o['jammed'])}", flush=True)
    json.dump(out, open(os.path.join(HERE, 'height_audit.json'), 'w'), indent=1, default=str)
