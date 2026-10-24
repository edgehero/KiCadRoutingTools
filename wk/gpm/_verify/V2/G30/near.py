"""Print all same-net copper near a point (segments, vias, pads, zones), with
centerline distances and the segment's own endpoints. Read-only."""
import sys, math
sys.path[:0] = ['py_router', '.']
from kicad_parser import parse_kicad_pcb

def pseg(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-ax-t*dx, py-ay-t*dy), t
pcb = parse_kicad_pcb(sys.argv[1])
for spec in sys.argv[2:]:
    net, x, y, layer = spec.split(',')
    x, y = float(x), float(y)
    nid = [n for n, v in pcb.nets.items() if v.name == net][0]
    print(f"== {net} {layer} ({x},{y})")
    for s in pcb.segments:
        if s.net_id != nid: continue
        d, t = pseg(x, y, s.start_x, s.start_y, s.end_x, s.end_y)
        if d < 1.2: print(f"  seg {s.layer} ({s.start_x},{s.start_y})-({s.end_x},{s.end_y}) w{s.width} d_center={d:.4f} t={t:.3f}")
    for v in pcb.vias:
        if v.net_id == nid and math.hypot(v.x-x, v.y-y) < 1.5: print(f"  via ({v.x},{v.y}) size {v.size} d={math.hypot(v.x-x, v.y-y):.4f} layers {v.layers}")
    for fp in pcb.footprints.values():
        for p in fp.pads:
            if p.net_id == nid and math.hypot(p.global_x-x, p.global_y-y) < 2: print(f"  pad {fp.reference}.{p.pad_number} ({p.global_x},{p.global_y}) {p.size_x}x{p.size_y} {p.shape} {p.layers}")
    for z in pcb.zones:
        if z.net_id == nid: print(f"  zone on {z.layer} (net zone present)")
