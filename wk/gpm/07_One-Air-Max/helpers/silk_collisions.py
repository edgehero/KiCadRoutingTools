"""silk_collisions.py -- same-face overlaps of footprint SILK outlines (lines/rects/polys only; pin-1
circles and arcs ignored) where at least one of the two parts has a body >= MIN mm2: the collisions
check_assembly does not gate because silk-drawn bodies never gate (#896).
Usage: python3 silk_collisions.py BOARD [MIN_AREA_MM2=12] [MIN_OVERLAP_MM=0.15]"""
import re, sys, math
sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb
B = sys.argv[1]
MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
OV = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
pcb = parse_kicad_pcb(B)
t = open(B, encoding='utf-8').read()
starts = [m.start() for m in re.finditer(r'\n\t\(footprint ', t)] + [len(t)]
bodies = {}
for a, b in zip(starts, starts[1:]):
    blk = t[a:b]
    m = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not m or m.group(1) not in pcb.footprints:
        continue
    ref = m.group(1); fp = pcb.footprints[ref]
    pts = []
    for mm in re.finditer(r'\(fp_(line|rect|poly)\s(.*?)\(layer "([FB])\.SilkS"\)', blk, re.S):
        pts += [(float(x), float(y)) for x, y in re.findall(r'\((?:start|end|xy) ([-\d.]+) ([-\d.]+)\)', mm.group(2))]
    if not pts:
        continue
    th = math.radians(fp.rotation)
    g = [(fp.x + x * math.cos(th) + y * math.sin(th), fp.y - x * math.sin(th) + y * math.cos(th)) for x, y in pts]
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    bodies[ref] = (fp.layer, (min(xs), min(ys), max(xs), max(ys)))
refs = sorted(bodies)
area = {r: (bodies[r][1][2] - bodies[r][1][0]) * (bodies[r][1][3] - bodies[r][1][1]) for r in refs}
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        if bodies[a][0] != bodies[b][0] or max(area[a], area[b]) < MIN:
            continue
        A = bodies[a][1]; Bb = bodies[b][1]
        w = min(A[2], Bb[2]) - max(A[0], Bb[0]); h = min(A[3], Bb[3]) - max(A[1], Bb[1])
        if w > OV and h > OV:
            print('%-8s %-8s %s overlap %.2f x %.2f mm' % (a, b, bodies[a][0], w, h))
