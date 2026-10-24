#!/usr/bin/env python3
"""For each quarter turn of a chip, count the crossings among straight
chip-pin -> connector-pin airwires of a NAMED set of nets, and their summed
length, with the chip at a given centre.

Why (TOOL_GAPS.md): render_placement's crossings/hpwl are board-wide, so
turning one chip with place_pose leaves its decaps behind and the count is
swamped by them; no repo tool scores a candidate turn on one net group.

    python3 -I helpers/usb_rot.py BOARD CHIP X Y NETGLOB [NETGLOB ...]
"""
import fnmatch
import math
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402


def seg_cross(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) * o(a, b, d) < 0) and (o(c, d, a) * o(c, d, b) < 0)


def main():
    board, chip, cx, cy = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    globs = sys.argv[5:]
    pcb = parse_kicad_pcb(board)
    fp = pcb.footprints[chip]
    # pad offsets from the footprint origin in board frame at the CURRENT turn
    base = {p.pad_number: (p.global_x - fp.x, p.global_y - fp.y) for p in fp.pads}
    nets = {}
    for p in fp.pads:
        if p.net_name and any(fnmatch.fnmatchcase(p.net_name, g) for g in globs):
            nets[p.net_name] = p.pad_number
    others = {}
    for ref, f in pcb.footprints.items():
        if ref == chip:
            continue
        for q in f.pads:
            if q.net_name in nets:
                others.setdefault(q.net_name, []).append((q.global_x, q.global_y))
    for turn in (0, 90, 180, 270):
        t = math.radians(turn)
        lines = []
        total = 0.0
        for n, num in nets.items():
            dx, dy = base[num]
            # extra turn about the origin, KiCad sense (y down, CCW on screen)
            rx = dx * math.cos(t) + dy * math.sin(t)
            ry = -dx * math.sin(t) + dy * math.cos(t)
            a = (cx + rx, cy + ry)
            tgt = min(others.get(n, []), key=lambda q: math.dist(a, q), default=None)
            if tgt is None:
                continue
            lines.append((a, tgt))
            total += math.dist(a, tgt)
        cr = sum(seg_cross(*lines[i], *lines[j]) for i in range(len(lines))
                 for j in range(i))
        print(f"extra turn {turn:3d} (abs {(fp.rotation + turn) % 360:5.1f}): "
              f"crossings {cr:3d}  length {total:6.1f} mm  nets {len(lines)}")


if __name__ == '__main__':
    main()
