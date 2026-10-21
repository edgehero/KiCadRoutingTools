#!/usr/bin/env python3
"""Diff-pair coupling and intra-pair skew, measured from a routed board.

Why this exists (TOOL_GAPS): no repo instrument grades a routed diff pair
(board_score and check_complete have no diff-pair component; route_diff's own
summary called /DRAM/DRAM_DQS0 'coupled' while 0.57 of its 21.08 mm ran beside
the N leg -- the verifier measured that by hand from review-routed-board Step 4).

Per pair: each leg's track length (sum of its segments, plus via barrels as
KiCad counts them is NOT added -- the stackup is 0.17 mm thick), the length of
P copper that runs within --couple mm (centre to centre) of N copper on the same
layer, and the skew |P - N|. Lengths are whole-net track copper, so a pair with
a termination stub (CLK0 -> R1) includes the stub on both legs.

usage: python3 helpers/pair_check.py BOARD [--couple 0.35] PAIRBASE ...
  e.g. /DRAM/DRAM_DQS0 /DRAM/DRAM_DQS1 /DRAM/DRAM_CLK0
"""
import math, sys

sys.path.insert(0, 'py_router')


def seg_pts(s, step=0.05):
    L = math.hypot(s.end_x - s.start_x, s.end_y - s.start_y)
    n = max(1, int(L / step))
    return [(s.start_x + (s.end_x - s.start_x) * (i + 0.5) / n,
             s.start_y + (s.end_y - s.start_y) * (i + 0.5) / n, L / n) for i in range(n)]


def dist_pt_seg(px, py, s):
    ax, ay, bx, by = s.start_x, s.start_y, s.end_x, s.end_y
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def main():
    args = sys.argv[1:]
    couple = 0.35
    if '--couple' in args:
        i = args.index('--couple'); couple = float(args[i + 1]); del args[i:i + 2]
    board, bases = args[0], args[1:]
    from kicad_parser import parse_kicad_pcb
    pcb = parse_kicad_pcb(board)
    by = {n.name: i for i, n in pcb.nets.items()}
    worst = 0.0
    for b in bases:
        P, N = by[b + '_P'], by[b + '_N']
        ps = [s for s in pcb.segments if s.net_id == P]
        ns = [s for s in pcb.segments if s.net_id == N]
        lp = sum(math.hypot(s.end_x - s.start_x, s.end_y - s.start_y) for s in ps)
        ln = sum(math.hypot(s.end_x - s.start_x, s.end_y - s.start_y) for s in ns)
        cpl = 0.0
        for s in ps:
            same = [t for t in ns if t.layer == s.layer]
            for (x, y, w) in seg_pts(s):
                if same and min(dist_pt_seg(x, y, t) for t in same) <= couple:
                    cpl += w
        layers_p = sorted({s.layer for s in ps}); layers_n = sorted({s.layer for s in ns})
        from net_queries import pin_pair_path_length
        def pp(nid):
            pads = pcb.pads_by_net.get(nid, [])
            a = [x for x in pads if x.component_ref == 'U2']; b = [x for x in pads if x.component_ref == 'U1']
            return pin_pair_path_length(pcb, nid, a[0], b[0]) if a and b else None
        ppp, ppn = pp(P), pp(N)
        skew = abs(ppp - ppn) if (ppp is not None and ppn is not None) else abs(lp - ln)
        print(f'   U2->U1 path: P {ppp if ppp is None else round(ppp, 2)}  N {ppn if ppn is None else round(ppn, 2)}'
              + ('' if (ppp is not None and ppn is not None) else '  (unmeasurable: total copper used for skew)'))
        worst = max(worst, skew)
        print(f'{b}: P {lp:.2f} mm {layers_p}  N {ln:.2f} mm {layers_n}  coupled {cpl:.2f}/{lp:.2f} mm '
              f'({100 * cpl / max(lp, 1e-9):.0f}%)  skew {skew:.2f} mm')
    print(f'worst skew {worst:.2f} mm')


if __name__ == '__main__':
    main()
