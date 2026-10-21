#!/usr/bin/env python3
"""gp14: do two boards place every footprint at the same pose?

    python3 -X utf8 wk/gp14/_staging/pose_diff.py A.kicad_pcb B.kicad_pcb [--tol 1e-4]

Prints the footprints whose x, y, rotation or side differ (beyond --tol mm / deg)
and exits 0 when none do, 1 otherwise. Used to check that a re-filmed seed
(place_movie / movie3d) is the placement the run shipped.
"""
import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'py_router')]
from kicad_parser import parse_kicad_pcb  # noqa: E402


def poses(path):
    pcb = parse_kicad_pcb(path)
    return {r: (f.x, f.y, f.rotation % 360, f.layer) for r, f in pcb.footprints.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--tol', type=float, default=1e-4)
    a = ap.parse_args()
    pa, pb = poses(a.a), poses(a.b)
    diff = []
    for r in sorted(set(pa) | set(pb)):
        if r not in pa or r not in pb:
            diff.append(f'{r}: only in {"A" if r in pa else "B"}')
            continue
        (xa, ya, ra, la), (xb, yb, rb, lb) = pa[r], pb[r]
        dr = min(abs(ra - rb), 360 - abs(ra - rb))
        if abs(xa - xb) > a.tol or abs(ya - yb) > a.tol or dr > a.tol or la != lb:
            diff.append(f'{r}: A ({xa:.4f}, {ya:.4f}, {ra:g}, {la}) B ({xb:.4f}, {yb:.4f}, {rb:g}, {lb})')
    print(f'{len(pa)} footprints, {len(diff)} differ')
    for d in diff[:20]:
        print('  ' + d)
    return 1 if diff else 0


if __name__ == '__main__':
    sys.exit(main())
