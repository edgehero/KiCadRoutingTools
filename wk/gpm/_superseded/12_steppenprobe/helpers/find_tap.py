#!/usr/bin/env python3
"""Search for a hand join (a straight or one-bend 0.3 mm stub from a pad, ending
in a via or at a target point) that py_tools/check_join.py grades CLEAN.

Why a helper: route.py --escalation off --track-width 0.3 left these power
pads unconnected ("FAILED ... STILL FLOATING") although a simple stub fits, and
no repo tool proposes a join -- check_join only grades one you already drew.

usage: find_tap.py BOARD NET X Y [--via | --to X2 Y2] [--layer F.Cu]
       [--width 0.3] [--max 4.0] [--first]
Prints every CLEAN candidate as the check_join argv tail (shortest first).
"""
import argparse
import math
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def clean(board, net, pts, width, via_size, via_drill):
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(REPO, 'py_tools', 'check_join.py'),
                        board, net] + pts + ['--width', str(width), '--via-size', str(via_size),
                                             '--via-drill', str(via_drill), '-q'],
                       capture_output=True, text=True)
    return r.returncode == 0 and 'CLEAN' in r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board'); ap.add_argument('net'); ap.add_argument('x', type=float); ap.add_argument('y', type=float)
    ap.add_argument('--via', action='store_true'); ap.add_argument('--to', nargs=2, type=float)
    ap.add_argument('--layer', default='F.Cu'); ap.add_argument('--width', type=float, default=0.3)
    ap.add_argument('--via-size', type=float, default=0.6); ap.add_argument('--via-drill', type=float, default=0.3)
    ap.add_argument('--max', type=float, default=4.0); ap.add_argument('--first', action='store_true')
    a = ap.parse_args()
    L = a.layer
    cands = []
    dirs = [(math.cos(k * math.pi / 4), math.sin(k * math.pi / 4)) for k in range(8)]
    steps = [round(0.6 + 0.2 * i, 2) for i in range(int((a.max - 0.6) / 0.2) + 1)]
    if a.via:
        for dx, dy in dirs:
            for l1 in steps:
                p1 = (a.x + dx * l1, a.y + dy * l1)
                cands.append((l1, [p1]))
                for ex, ey in dirs:
                    if abs(ex * dx + ey * dy) > 0.99:
                        continue
                    for l2 in (0.6, 1.0, 1.4, 2.0):
                        cands.append((l1 + l2, [p1, (p1[0] + ex * l2, p1[1] + ey * l2)]))
    else:
        tx, ty = a.to
        cands.append((math.hypot(tx - a.x, ty - a.y), []))
        for dx, dy in dirs:
            for l1 in steps:
                p1 = (a.x + dx * l1, a.y + dy * l1)
                cands.append((l1 + math.hypot(tx - p1[0], ty - p1[1]), [p1]))
    cands.sort(key=lambda c: c[0])
    seen = 0
    for length, mids in cands:
        pts = [f"{a.x:.4f},{a.y:.4f},{L}"] + [f"{px:.4f},{py:.4f},{L}" for px, py in mids]
        if a.via:
            end = mids[-1]
            pts.append(f"via:{end[0]:.4f},{end[1]:.4f}")
        else:
            pts.append(f"{a.to[0]:.4f},{a.to[1]:.4f},{L}")
        if clean(a.board, a.net, pts, a.width, a.via_size, a.via_drill):
            print(f"CLEAN len={length:.2f} :: {a.net} " + ' '.join(pts), flush=True)
            seen += 1
            if a.first or seen >= 3:
                return 0
    print('no CLEAN candidate')
    return 1


if __name__ == '__main__':
    sys.exit(main())
