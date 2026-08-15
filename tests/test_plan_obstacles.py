#!/usr/bin/env python3
"""A plan must not place a part on top of one that is already there.

This property had no test, and its absence shipped a real defect: the resolver
excluded EVERY unlocked part from its own obstacle set, so

    place_at R1 at U1's exact coordinate

seated at 0.0mm and reported `complete: true, parked: 0, exit 0` on a board
that `check_assembly` grades NOT BUILDABLE (COINCIDENT ORIGINS). The rule was
borrowed from `seed_from_intent`, where it is correct -- that function owns
the whole board, so "every unlocked part" and "every part I am about to
place" are the same set. A plan does not own the whole board.

The three cases below are the ones that distinguish a correct obstacle set
from the bug, and each of them PASSED with the bug present:

  1. an unnamed part at a distinct pose blocks a seat
  2. `place_lock` makes a part an obstacle -- locking one used to make it
     INVISIBLE, so the next op could seat on top of it, exactly backwards
  3. a genuine PILE still behaves as before: parts stacked at one coordinate
     are staging artifacts, not placements, and must not veto each other

Case 3 is why the rule is per-part rather than a whole-board placed/unplaced
verdict. Without it the fix regresses every from-scratch seeding run, which is
the toolchain's whole purpose.
"""
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not os.path.isfile(BOARD):
    print("SKIP: fixture missing")
    sys.exit(0)

from kicad_parser import parse_kicad_pcb
from placement.plan_ops import parse_placement_plan
from placement.plan_resolve import resolve

pcb = parse_kicad_pcb(BOARD)
U1 = pcb.footprints['U1']
TARGET = [round(U1.x, 3), round(U1.y, 3)]


def run(steps):
    ops, errors = parse_placement_plan({"schema": 1, "steps": steps})
    assert ops is not None, errors
    return resolve(pcb, BOARD, ops, clearance=0.25,
                   board_edge_clearance=0.55, grid_step=0.1)


# --------------------------------------------------------------------------
# 1. an unnamed part is an obstacle at its own pose
# --------------------------------------------------------------------------
res = run([{"action": "place_at", "ref": "R1", "at": TARGET, "rot": 0,
            "within": 0.5}])
check("a part the plan never names blocks a seat at its coordinate",
      not res.seats and len(res.parks) == 1,
      f"seated {[s.ref for s in res.seats]}, parked {[p.ref for p in res.parks]}")
check("and the run says how many parts it is holding as obstacles",
      any('held there as obstacles' in n for n in res.notes),
      str(res.notes[:2]))

# The seat is refused, not silently relocated: the board is left alone.
check("the refused seat writes no placement at all", not res.placements,
      str(res.placements))

# --------------------------------------------------------------------------
# 2. place_lock makes a part an obstacle (it used to make it invisible)
# --------------------------------------------------------------------------
res = run([{"action": "place_lock", "refs": ["U1"]},
           {"action": "place_at", "ref": "R1", "at": TARGET, "rot": 0,
            "within": 0.5}])
check("locking a part does not make it invisible to a later seat",
      not res.seats and [p.ref for p in res.parks] == ['R1'],
      f"seated {[(s.ref, s.pose[:2]) for s in res.seats]}")
check("and the lock is still recorded", res.lock_refs == ['U1'],
      str(res.lock_refs))

# --------------------------------------------------------------------------
# 3. a real PILE is still excluded -- the from-scratch case must not regress
# --------------------------------------------------------------------------
# Stack three parts on one coordinate, the way a staged pile arrives. Their
# poses are artifacts; if they vetoed each other, seeding would be impossible.
import copy

piled = copy.deepcopy(pcb)
stack = ['R1', 'R2', 'R3']
for ref in stack:
    if ref in piled.footprints:
        piled.footprints[ref].x = float(U1.x)
        piled.footprints[ref].y = float(U1.y)
present = [r for r in stack if r in piled.footprints]

ops, _ = parse_placement_plan({"schema": 1, "steps": [
    {"action": "place_at", "ref": present[0], "at": TARGET, "rot": 0,
     "within": 0.5}]})
res = resolve(piled, BOARD, ops, clearance=0.25, board_edge_clearance=0.55,
              grid_step=0.1)
check("parts stacked at one coordinate do not veto each other",
      len(res.seats) == 1 and not res.parks,
      f"seated {[s.ref for s in res.seats]}, parked "
      f"{[(p.ref, p.reason) for p in res.parks]}")
check("(and the fixture really is a stack, or the case proves nothing)",
      len(present) >= 2, f"stacked {present}")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
