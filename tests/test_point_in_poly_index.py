#!/usr/bin/env python3
"""`_point_in_poly` is indexed, and the index is EXACT.

Profiled on an 87-part seeding run over a 638-edge outline, this one function
was 35.8s of a 60s window -- 693,893 calls at ~51.6us each, 60% of total
runtime. It scanned every edge of the ring for every query, while the crossing
test only cares about edges whose Y RANGE straddles the point: on that outline
~600 of the ~638 comparisons could not contribute and were performed anyway.

Two properties, and the first is the one that matters. A containment predicate
that is fast and wrong silently changes which poses are legal, which changes
placements, which changes boards.

  1. EXACT: identical to the naive scan for every point, including points on a
     vertex's exact Y (the boundary case a bucketed index is most likely to
     get wrong, since an edge must appear in every bucket its range spans).
  2. Materially faster on a real outline.

A bbox reject alone was tried first and did NOT help: it only rejects points
outside the ring, and the queries that dominate a seeding run are mid-board
candidates, which are inside it. Recorded because the wrong fix looked
plausible and cost a measurement to rule out.
"""
import os
import random
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

import check_drc
from kicad_parser import parse_kicad_pcb

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


def naive(x, y, poly):
    """The implementation this replaced, verbatim."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def rings_of(board):
    pcb = parse_kicad_pcb(board)
    bi = pcb.board_info
    out = list(getattr(bi, 'board_outlines', None) or [])
    out += list(getattr(bi, 'board_cutouts', None) or [])
    return [r for r in out if r and len(r) >= 3]


BOARDS = [os.path.join(REPO, 'kicad_files', b) for b in
          ('watchy.kicad_pcb', 'tigard.kicad_pcb', 'glasgow_revC.kicad_pcb',
           'flat_hierarchy.kicad_pcb')]
BOARDS = [b for b in BOARDS if os.path.isfile(b)]
if not BOARDS:
    print("SKIP: no fixture boards")
    sys.exit(77)

rng = random.Random(11)
mismatch, tested, biggest = [], 0, None
for board in BOARDS:
    for ring in rings_of(board):
        if biggest is None or len(ring) > len(biggest):
            biggest = ring
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        for _ in range(1500):
            x = rng.uniform(min(xs) - 2, max(xs) + 2)
            y = rng.uniform(min(ys) - 2, max(ys) + 2)
            tested += 1
            if check_drc._point_in_poly(x, y, ring) != naive(x, y, ring):
                mismatch.append((os.path.basename(board), x, y))
        # Exact vertex Ys: an edge must be registered in EVERY bucket its
        # y-range spans, or a point level with a vertex sees the wrong edges.
        for vx, vy in ring[:150]:
            for dx in (0.001, -0.001, 0.0):
                tested += 1
                if check_drc._point_in_poly(vx + dx, vy, ring) != naive(
                        vx + dx, vy, ring):
                    mismatch.append((os.path.basename(board), vx + dx, vy))

check("the index agrees with the naive scan on every point",
      not mismatch, f"{len(mismatch)} mismatch(es) of {tested}: {mismatch[:3]}")
check("and enough points were tested for that to mean something",
      tested > 5000, f"{tested} points")
# No TRACKED board has a complex outline -- the largest ring in kicad_files is
# 13 vertices -- so the case the index exists for has to be synthesised. The
# 638-edge milled outline that motivated this lives on an untracked board.
import math

N = 600
cx, cy, rr = 100.0, 100.0, 40.0
complex_ring = [(cx + rr * (1.0 + 0.15 * math.sin(9 * i * math.tau / N))
                 * math.cos(i * math.tau / N),
                 cy + rr * (1.0 + 0.15 * math.sin(9 * i * math.tau / N))
                 * math.sin(i * math.tau / N)) for i in range(N)]
bad = 0
for _ in range(2500):
    x = rng.uniform(cx - rr * 1.3, cx + rr * 1.3)
    y = rng.uniform(cy - rr * 1.3, cy + rr * 1.3)
    if check_drc._point_in_poly(x, y, complex_ring) != naive(x, y,
                                                             complex_ring):
        bad += 1
for vx, vy in complex_ring[:200]:
    if check_drc._point_in_poly(vx + 0.001, vy, complex_ring) != naive(
            vx + 0.001, vy, complex_ring):
        bad += 1
check("the index is exact on a 600-vertex non-convex ring too", not bad,
      f"{bad} mismatch(es)")
check("small rings take the DIRECT scan (the index would cost more)",
      len(biggest) < check_drc._POLY_INDEX_MIN_VERTS,
      f"largest tracked ring {len(biggest)} vertices vs threshold "
      f"{check_drc._POLY_INDEX_MIN_VERTS} -- if a tracked board grows a "
      f"complex outline this note is stale, not wrong")
biggest = complex_ring

# Speed, on the largest ring available. Deliberately a RATIO against the naive
# implementation rather than a wall-clock budget: a budget passes on a machine
# fast enough, which is how a different affordability check in this branch
# stayed green after the thing it guarded had been removed.
xs = [p[0] for p in biggest]
ys = [p[1] for p in biggest]
pts = [(rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys)))
       for _ in range(3000)]
check_drc._point_in_poly(pts[0][0], pts[0][1], biggest)   # warm the index

t0 = time.time()
for x, y in pts:
    check_drc._point_in_poly(x, y, biggest)
t_idx = time.time() - t0
t0 = time.time()
for x, y in pts:
    naive(x, y, biggest)
t_naive = time.time() - t0

check("the indexed form is materially faster than the scan it replaced",
      t_idx < t_naive * 0.6,
      f"indexed {t_idx * 1e6 / len(pts):.1f}us/call vs naive "
      f"{t_naive * 1e6 / len(pts):.1f}us/call on a {len(biggest)}-vertex ring")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
