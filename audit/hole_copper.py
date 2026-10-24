#!/usr/bin/env python3
"""Other-net copper around each mounting hole of one board (the screw head / washer / standoff area).

    python3 -X utf8 wk/gpm/_audit/hole_copper.py BOARD.kicad_pcb [--ring 1.3]     (from a repo checkout)

A mounting hole = a footprint with <= 9 pads whose pads ALL carry a drill >= 2.0 mm and no signal net (none,
`unconnected-*`, or a GND-named net). For each one: the drill, the plated pad's diameter, and every track, arc
and via of another net whose copper comes within RING mm of the hole edge (default 1.3 mm, about an ISO 7380
M3 head; a washer reaches further), with its distance to the pad copper.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'py_router'))
from kicad_parser import parse_kicad_pcb  # noqa: E402

board = sys.argv[1]
RING = float(sys.argv[sys.argv.index('--ring') + 1]) if '--ring' in sys.argv else 1.3
pcb = parse_kicad_pcb(board)
for ref, f in sorted(pcb.footprints.items()):
    pads = f.pads
    if not pads or len(pads) > 9 or not all(p.drill and p.drill >= 2.0 for p in pads):
        continue
    if any(p.net_name and not re.match(r'(unconnected-|.*GND)', p.net_name, re.I) for p in pads):
        continue
    d = max(p.drill for p in pads)
    pr = max(max(p.size_x, p.size_y) for p in pads) / 2 if any(p.pad_type == 'thru_hole' for p in pads) else d / 2
    own = {p.net_id for p in pads if p.net_id}
    hits = []
    for s in pcb.segments:
        if getattr(s, 'graphic', False) or s.net_id in own:
            continue
        ax, ay, bx, by = s.start_x, s.start_y, s.end_x, s.end_y
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        t = 0 if L2 == 0 else max(0, min(1, ((f.x - ax) * (bx - ax) + (f.y - ay) * (by - ay)) / L2))
        g = math.hypot(ax + t * (bx - ax) - f.x, ay + t * (by - ay) - f.y) - s.width / 2
        if g < d / 2 + RING:
            hits.append((round(g - pr, 2), s.layer, pcb.nets[s.net_id].name if s.net_id in pcb.nets else s.net_id))
    for v in pcb.vias:
        g = math.hypot(v.x - f.x, v.y - f.y) - v.size / 2
        if v.net_id not in own and g < d / 2 + RING:
            hits.append((round(g - pr, 2), 'via', pcb.nets[v.net_id].name if v.net_id in pcb.nets else v.net_id))
    hits.sort()
    nets = sorted({h[2] for h in hits})
    print(f'{ref} {f.footprint_name.split(":")[-1]}: drill {d}, pad dia {2 * pr:.2f}; {len(hits)} other-net items within '
          f'{RING} mm of the hole edge; closest to the pad copper (mm, layer, net): {hits[:3]}; nets {nets[:6]}')
