"""For each declared REF** drill, the hole centre's side of the outline and its distance to the nearest outline/cutout edge."""
import sys, json, math, os
sys.path[:0] = [os.path.join(os.getcwd(), 'py_router'), os.path.join(os.getcwd(), 'py_placer')]
from kicad_parser import parse_kicad_pcb, extract_board_contours, _pt_in_ring
board, summary, intent_path = sys.argv[1:4]
p = parse_kicad_pcb(board)
t = open(board, encoding='utf-8').read()
outers, cuts = extract_board_contours(t)
def dseg(px, py, a, b):
    (x1, y1), (x2, y2) = a, b; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))
refused = json.load(open(summary)).get('refused', {})
fpd = {f['ref']: f for f in json.load(open(intent_path)).get('fixed_poses', [])}
rows = []
for r in sorted(fpd):
    if not r.startswith('REF**'):
        continue
    fp = p.footprints[r]
    at_decl = abs(fp.x - fpd[r]['x']) < 1e-3 and abs(fp.y - fpd[r]['y']) < 1e-3
    for pd in fp.pads:
        if pd.drill > 0:
            hx = pd.hole_x if pd.hole_x is not None else pd.global_x
            hy = pd.hole_y if pd.hole_y is not None else pd.global_y
            in_out = any(_pt_in_ring(hx, hy, rg) for rg in outers)
            in_cut = any(_pt_in_ring(hx, hy, rg) for rg in cuts)
            d = min(dseg(hx, hy, rg[i], rg[(i + 1) % len(rg)]) for rg in outers + cuts for i in range(len(rg)))
            rows.append(dict(ref=r, refused=r in refused, at_declared=at_decl, drill=pd.drill,
                             centre=('in board' if in_out and not in_cut else 'in cutout' if in_cut else 'outside'),
                             centre_to_edge=round(d, 3), straddles=d < pd.drill / 2 - 1e-6, xy=(round(hx, 3), round(hy, 3))))
for k in (True, False):
    sub = [r for r in rows if r['refused'] == k]
    print(f"refused={k}: n={len(sub)} at_declared={sum(r['at_declared'] for r in sub)} straddle={sum(r['straddles'] for r in sub)} "
          f"centres={sorted(set(r['centre'] for r in sub))} centre_to_edge min/max={min(r['centre_to_edge'] for r in sub)}/{max(r['centre_to_edge'] for r in sub)}")
for r in [r for r in rows if r['refused']][:5]:
    print(r)
# which ring does each straddling hole sit on?
def nearest_ring(hx, hy):
    best = None
    for name, rg in [('outer', o) for o in outers] + [(f'cutout{i}', c) for i, c in enumerate(cuts)]:
        d = min(dseg(hx, hy, rg[i], rg[(i + 1) % len(rg)]) for i in range(len(rg)))
        if best is None or d < best[1]:
            best = (name, d)
    return best[0]
import collections
c = collections.Counter((nearest_ring(*r['xy']), r['refused']) for r in rows if r['straddles'])
print('straddling holes by ring and refusal:', dict(c))
for i, cu in enumerate(cuts):
    xs = [p[0] for p in cu]; ys = [p[1] for p in cu]
    print(f'cutout{i} bbox', round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2), 'pts', len(cu))
print('board_bounds', p.board_info.board_bounds)
