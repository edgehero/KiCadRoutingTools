"""Delete router-left dangling segments that check_weird names (icebreaker_v10e).

Why this helper exists (TOOL_GAPS.md): route.py shipped four dangling +3V3
F.Cu stubs (0.7-2.7 mm, one free end each) that its own end-of-run cleanup
kept through five route steps, and check_complete grades the board INCOMPLETE
for them (orphan_stubs, weird_copper).  No repo CLI removes them: check_weird
and check_orphan_stubs are read-only, `--rip-existing-nets` only permits
ripping a net that BLOCKS another, and `--force-reroute` skips zone-owning
nets such as +3V3.  The deletion itself uses the repo's own
kicad_writer.remove_segments_from_content.

Usage:
  python3 -X utf8 helpers/drop_dangling.py IN.kicad_pcb OUT.kicad_pcb NET X,Y,LAYER|via:X,Y [...]
Each X,Y,LAYER is a FREE END as check_weird prints it; via:X,Y is a via
check_weird calls `dangling-via` (copper reaches it on one layer only).
For a via the helper refuses unless at most one segment, on one layer,
reaches it and no pad touches it.  The helper refuses
unless exactly one segment of NET on LAYER ends there and nothing else of the
net (another segment end, a via, a pad) touches that point -- so it can only
remove copper that connects nothing at that end.  OUT gets IN's siblings
(copy_board) and then the edited board text.
"""
import math
import subprocess
import sys

sys.path.insert(0, "py_router")
from kicad_parser import parse_kicad_pcb, board_uses_name_nets  # noqa: E402
from kicad_writer import remove_segments_from_content  # noqa: E402

TOL = 0.02


def main(argv):
    src, dst, net = argv[1], argv[2], argv[3]
    ends = []
    via_pts = []
    for tok in argv[4:]:
        if tok.startswith("via:"):
            x, y = tok[4:].split(",")
            via_pts.append((float(x), float(y)))
            continue
        x, y, layer = tok.split(",")
        ends.append((float(x), float(y), layer))
    pcb = parse_kicad_pcb(src)
    nid = [n.net_id for n in pcb.nets.values() if n.name == net]
    if len(nid) != 1:
        sys.exit(f"REFUSED: net {net!r} not found once on the board")
    nid = nid[0]
    segs = [s for s in pcb.segments if s.net_id == nid and not getattr(s, "graphic", False)]
    vias = [v for v in pcb.vias if v.net_id == nid]
    pads = [p for fp in pcb.footprints.values() for p in fp.pads if p.net_id == nid]
    # A dangling via (check_weird's `dangling-via`): same-net copper reaches it
    # on at most ONE layer and through at most one segment, and no pad touches
    # it -- so it joins no two layers and removing it disconnects nothing.
    drop_vias = []
    for (x, y) in via_pts:
        hit = [v for v in vias if math.hypot(v.x - x, v.y - y) <= TOL]
        if len(hit) != 1:
            sys.exit(f"REFUSED: {len(hit)} {net} via(s) at {x},{y} (need exactly 1)")
        v = hit[0]
        r = v.size / 2 + TOL
        touching = [s for s in segs if math.hypot(s.start_x - x, s.start_y - y) <= r
                    or math.hypot(s.end_x - x, s.end_y - y) <= r]
        # The via must touch AT MOST ONE copper item. A via touching a segment
        # AND a pad on one layer can be the only bridge between them (measured:
        # A5's /iCE_SI via joined a 0.0889 mm track to J16.1's rounded corner,
        # 0.005 mm short of the pad; removing it disconnected J16).
        touching_pads = [p for p in pads
                         if abs(p.global_x - x) <= p.size_x / 2 + r
                         and abs(p.global_y - y) <= p.size_y / 2 + r]
        if len(touching) + len(touching_pads) > 1:
            sys.exit(f"REFUSED: via at {x},{y} touches {len(touching)} segment(s) and "
                     f"{len(touching_pads)} pad(s): it may be the bridge between them")
        drop_vias.append(v)
        print(f"drop {net} via ({v.x:.3f},{v.y:.3f}) {v.size}/{v.drill}")
    vias = [v for v in vias if v not in drop_vias]
    drop = []
    for (x, y, layer) in ends:
        def at(px, py):
            return math.hypot(px - x, py - y) <= TOL
        hit = [s for s in segs if s.layer == layer
               and (at(s.start_x, s.start_y) or at(s.end_x, s.end_y))]
        if len(hit) != 1:
            sys.exit(f"REFUSED: {len(hit)} segment(s) of {net} end at {x},{y} on {layer} (need exactly 1)")
        if any(math.hypot(v.x - x, v.y - y) <= v.size / 2 + TOL for v in vias):
            sys.exit(f"REFUSED: a {net} via touches {x},{y}")
        for p in pads:
            if layer in p.layers or "*.Cu" in p.layers:
                if abs(p.global_x - x) <= p.size_x / 2 + TOL and abs(p.global_y - y) <= p.size_y / 2 + TOL:
                    sys.exit(f"REFUSED: pad {p.component_ref}.{p.pad_number} touches {x},{y}")
        drop.append(hit[0])
        s = hit[0]
        print(f"drop {net} {layer} ({s.start_x:.3f},{s.start_y:.3f})-({s.end_x:.3f},{s.end_y:.3f}) w={s.width}")
    content = open(src, encoding="utf-8").read()
    name_map = {n.net_id: n.name for n in pcb.nets.values()} if board_uses_name_nets(content) else None
    unmatched = []
    new, count = remove_segments_from_content(content, drop, net_id_to_name=name_map,
                                              unmatched_out=unmatched, match_width=True)
    if count != len(drop):
        sys.exit(f"REFUSED: removed {count} of {len(drop)} segment block(s); unmatched {unmatched}")
    if drop_vias:
        from kicad_writer import remove_vias_from_content
        new, vcount = remove_vias_from_content(new, drop_vias, net_id_to_name=name_map)
        if vcount != len(drop_vias):
            sys.exit(f"REFUSED: removed {vcount} of {len(drop_vias)} via block(s)")
        count += vcount
    subprocess.run([sys.executable, "-X", "utf8", "py_router/copy_board.py", src, dst], check=True,
                   stdout=subprocess.DEVNULL)
    open(dst, "w", encoding="utf-8").write(new)
    print(f"removed {count} segment(s) -> {dst}")


if __name__ == "__main__":
    main(sys.argv)
