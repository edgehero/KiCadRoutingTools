"""free_via_sites.py -- list through-via sites near a point that clear every other net's copper.

    python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/free_via_sites.py BOARD NET X Y \
        [--radius 2.0] [--step 0.025] [--via 0.45] [--drill 0.2] [--clearance 0.1] [--h2h 0.254] [--top 15]

A through via touches all copper layers, so a site is free when, on EVERY copper layer,
its ring keeps `clearance` from every foreign segment (as a capsule), via and pad (pad
rectangle, rotated by its rect_rotation; circles for round pads), and its drill keeps
`h2h` from every other drill. Same-net copper is ignored (it joins). Sites are ranked by
distance to (X, Y). Zones are not obstacles (they flow around a via).

Written because no repo tool PROPOSES a join: `check_join.py` only verifies a polyline
the caller already chose (TOOL_GAPS: "no join proposer"). Read-only.
"""
import argparse
import math
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rect_dist(px, py, cx, cy, hx, hy, rot_deg):
    th = math.radians(rot_deg or 0.0)
    lx = (px - cx) * math.cos(th) + (py - cy) * math.sin(th)
    ly = -(px - cx) * math.sin(th) + (py - cy) * math.cos(th)
    ex, ey = max(abs(lx) - hx, 0.0), max(abs(ly) - hy, 0.0)
    return math.hypot(ex, ey)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board'); ap.add_argument('net'); ap.add_argument('x', type=float); ap.add_argument('y', type=float)
    ap.add_argument('--radius', type=float, default=2.0); ap.add_argument('--step', type=float, default=0.025)
    ap.add_argument('--via', type=float, default=0.45); ap.add_argument('--drill', type=float, default=0.2)
    ap.add_argument('--clearance', type=float, default=0.1); ap.add_argument('--h2h', type=float, default=0.254)
    ap.add_argument('--top', type=int, default=15)
    a = ap.parse_args()
    pcb = parse_kicad_pcb(a.board)
    nid = [n.net_id for n in pcb.nets.values() if n.name == a.net]
    if not nid:
        sys.exit(f'no net {a.net!r}')
    nid = nid[0]
    r = a.via / 2
    x0, y0, R = a.x, a.y, a.radius
    segs = [s for s in pcb.segments if s.net_id != nid
            and min(math.hypot(s.start_x - x0, s.start_y - y0), math.hypot(s.end_x - x0, s.end_y - y0),
                    seg_dist(x0, y0, s.start_x, s.start_y, s.end_x, s.end_y)) < R + 2]
    vias = [v for v in pcb.vias if math.hypot(v.x - x0, v.y - y0) < R + 2]
    pads = [(f, p) for f in pcb.footprints.values() for p in f.pads
            if math.hypot(p.global_x - x0, p.global_y - y0) < R + 3]
    out = []
    n = int(R / a.step)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = x0 + i * a.step, y0 + j * a.step
            d0 = math.hypot(x - x0, y - y0)
            if d0 > R:
                continue
            ok = True
            for s in segs:
                if seg_dist(x, y, s.start_x, s.start_y, s.end_x, s.end_y) < r + s.width / 2 + a.clearance:
                    ok = False; break
            if not ok:
                continue
            for v in vias:
                dd = math.hypot(v.x - x, v.y - y)
                if dd < a.drill / 2 + v.drill / 2 + a.h2h or (v.net_id != nid and dd < r + v.size / 2 + a.clearance):
                    ok = False; break
            if not ok:
                continue
            for f, p in pads:
                if p.drill and p.drill > 0:
                    hx_, hy_ = (p.hole_x if p.hole_x is not None else p.global_x,
                                p.hole_y if p.hole_y is not None else p.global_y)
                    if math.hypot(hx_ - x, hy_ - y) < a.drill / 2 + p.drill / 2 + a.h2h:
                        ok = False; break
                if p.net_id == nid or p.pad_type == 'np_thru_hole':
                    continue
                if p.shape == 'circle':
                    dd = math.hypot(p.global_x - x, p.global_y - y) - p.size_x / 2
                else:
                    dd = rect_dist(x, y, p.global_x, p.global_y, p.size_x / 2, p.size_y / 2, p.rect_rotation)
                if dd < r + a.clearance:
                    ok = False; break
            if ok:
                out.append((d0, round(x, 4), round(y, 4)))
    out.sort()
    print(f'{len(out)} free via site(s) within {R} mm of ({x0}, {y0}) for {a.net} (via {a.via}/{a.drill}, clearance {a.clearance})')
    for d, x, y in out[:a.top]:
        print(f'  {x:.3f} {y:.3f}   {d:.2f} mm')


if __name__ == '__main__':
    main()
