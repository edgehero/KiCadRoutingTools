"""Count vias whose barrel/annulus overlaps an SMD pad's copper rectangle (via-in-pad).
check_drc only reports these as `via-in-paste` on KiCad-10-format files; on this KiCad-6-format
board they are 'undeclarable' and accepted, so this helper measures them directly.
usage: python3 helpers/via_in_pad.py <board.kicad_pcb>"""
import sys, math
sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb
pcb = parse_kicad_pcb(sys.argv[1])
nm = {n.net_id: n.name for n in pcb.nets.values()}
hits = []
for v in pcb.vias:
    r = v.size / 2
    for fp in pcb.footprints.values():
        for p in fp.pads:
            if p.drill and p.drill > 0:
                continue
            hx, hy = p.size_x / 2, p.size_y / 2
            # rotate into pad frame for residual tilt
            a = math.radians(-(p.rect_rotation or 0))
            dx, dy = v.x - p.global_x, v.y - p.global_y
            dx, dy = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
            ox = max(abs(dx) - hx, 0); oy = max(abs(dy) - hy, 0)
            if math.hypot(ox, oy) < r - 1e-6:
                hits.append((nm.get(v.net_id), f"{fp.reference}.{p.pad_number}", round(v.x, 2), round(v.y, 2), p.net_id == v.net_id))
print(f"vias {len(pcb.vias)}; via-in-SMD-pad overlaps {len(hits)} "
      f"(same-net {sum(1 for h in hits if h[4])}, foreign {sum(1 for h in hits if not h[4])})")
for h in hits[:200]:
    print('  ', h)
