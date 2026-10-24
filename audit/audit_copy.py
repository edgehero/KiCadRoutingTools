#!/usr/bin/env python3
"""gpm audit B: does any shipped board carry the human placement or the human copper?

    python3 -X utf8 wk/gpm/_audit/audit_copy.py        (from krt-gpm)

The pile puts every part off the outline, so a part can only land on its human pose by chance (to the
micrometre) or because the pose was declared (intent fixed_poses, from mechanical.json). Copper the
router lays meets the human board's copper exactly only where both connect the same pad centres of a
part at the same pose. So, per board, on delivered.kicad_pcb:
  - parts at the human pose (0.005 mm, 0.05 deg, same side), split into declared / undeclared;
  - segments whose two end points both coincide (1 um) with one human segment on the same layer,
    and vias at a human via's centre;
  - the same for the human placement routed by main (the control), as the reference rate for a
    placement that IS the human one.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [HERE]
from sexp_census import census, top_items  # noqa: E402

G = os.path.join(ROOT, 'wk', 'gpm')


def poses(path):
    return {f['ref']: (f['x'], f['y'], f['rot'] % 360, f['layer']) for f in census(path)[1]}


def same(a, b):
    return a and b and abs(a[0] - b[0]) < .005 and abs(a[1] - b[1]) < .005 and \
        min(abs(a[2] - b[2]), 360 - abs(a[2] - b[2])) < .05 and a[3] == b[3]


def copper(path):
    segs, vias = set(), set()
    for head, blk in top_items(open(path, encoding='utf-8', errors='replace').read()):
        if head in ('segment', 'arc'):
            s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk); e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
            ly = re.search(r'\(layer "?([^")\s]+)', blk).group(1)
            a = (round(float(s.group(1)), 3), round(float(s.group(2)), 3))
            b = (round(float(e.group(1)), 3), round(float(e.group(2)), 3))
            segs.add((ly,) + tuple(sorted([a, b])))
        elif head == 'via':
            m = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', blk)
            vias.add((round(float(m.group(1)), 3), round(float(m.group(2)), 3)))
    return segs, vias


rows = []
for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*'))):
    nn_stem = os.path.basename(d); stem = nn_stem[3:]
    human = os.path.join(G, '_truth', stem, 'human.kicad_pcb')
    deliv = os.path.join(d, 'delivered.kicad_pcb')
    declared = {fp['ref'] for fp in json.load(open(os.path.join(d, 'intent.json'))).get('fixed_poses', [])}
    hp, op = poses(human), poses(deliv)
    at = [r for r in op if same(op[r], hp.get(r))]
    und = [r for r in at if r not in declared]
    hs, hv = copper(human); os_, ov = copper(deliv)
    ctl = sorted(glob.glob(os.path.join(G, '_control', stem, '*routed*.kicad_pcb')) or
                 glob.glob(os.path.join(G, '_control', stem, '*.kicad_pcb')))
    cs = cv = set()
    if ctl:
        cs, cv = copper(ctl[-1])
    r = {'board': nn_stem, 'parts': len(op), 'at_human_pose': len(at), 'declared': len(declared),
         'at_human_undeclared': und, 'segments': len(os_), 'segments_identical_to_human': len(os_ & hs),
         'vias': len(ov), 'vias_at_human_via': len(ov & hv),
         'control_segments_identical_to_human': f'{len(cs & hs)}/{len(cs)}' if ctl else None}
    rows.append(r)
    print(f'{nn_stem:32s} parts at human pose {len(at):3d}/{len(op):3d} (declared {len(declared):2d}, undeclared {und}) | '
          f'segments identical to human {len(os_ & hs):4d}/{len(os_):5d} | vias at a human via {len(ov & hv):3d}/{len(ov):3d} | '
          f'control (human placement, our router): {r["control_segments_identical_to_human"]}')
json.dump(rows, open(os.path.join(HERE, 'audit_copy.json'), 'w'), indent=1)
