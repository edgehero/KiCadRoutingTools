#!/usr/bin/env python3
"""A park must name what is in the way.

Before this, every park from an ordinary seat came back `blockers: {},
censused: false`. Only `place_lift` censused -- and `place_lift` is the op
whose whole job is evicting a blocker, so the author had to GUESS which part
to name. A goal-test agent placing a 165-part board guessed, and got the
honest but useless reply *"lifting C22, C35 frees no pose either, so they are
not what is in the way"*.

The machinery already existed for the seeder's stage 3c (issue #629,
`_evict_candidates` + `count_legal_poses`); this pins the plan path using it
at the ONE seam every geometric seat failure passes through, the tail of
`_Resolver.seat`.

Three properties, and the third is the one that keeps the other two honest:

  1. a park names its blockers, with the baseline it is measured against
  2. `censused` distinguishes "nothing movable is near" from "nothing was
     measured" -- an empty `blockers` means both, so the flag carries it
  3. the census is BOUNDED. `count_legal_poses` sweeps 4356 poses per call
     (1.10s when the cap fires, 2.64s when the count is 0), a blocked part
     has baseline 0 so it is always the slow case, and a full census is one
     baseline plus up to 8 candidates. `max_disp` from the op's own `within`
     is what makes it affordable.
"""
import json
import os
import subprocess
import sys
import time

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
    print(f"SKIP: {BOARD} absent")
    sys.exit(77)

from kicad_parser import parse_kicad_pcb
from placement.plan_ops import parse_placement_plan
from placement.plan_resolve import resolve

pcb = parse_kicad_pcb(BOARD)
U1 = pcb.footprints['U1']
ON_U1 = [round(U1.x, 3), round(U1.y, 3)]


def run(steps, **kw):
    ops, errors = parse_placement_plan({"schema": 1, "steps": steps})
    assert ops is not None, errors
    return resolve(pcb, BOARD, ops, clearance=0.25,
                   board_edge_clearance=0.55, grid_step=0.1, **kw)


# --------------------------------------------------------------------------
# 1. a park names its blockers
# --------------------------------------------------------------------------
res = run([{"action": "place_at", "ref": "R1", "at": ON_U1, "rot": 0,
            "within": 0.5}])
check("the part parks (the fixture must actually fail to seat)",
      len(res.parks) == 1 and not res.seats,
      f"seats {[s.ref for s in res.seats]}, parks {[p.ref for p in res.parks]}")
park = res.parks[0]
check("the park is censused", park.censused, str(park.to_dict()))
check("it names blockers", bool(park.blockers), str(park.blockers))
check("U1 -- the part it was told to sit on -- is named",
      'U1' in park.blockers, str(sorted(park.blockers)))
check("lifting U1 frees poses, and the others free none",
      park.blockers.get('U1', 0) > 0
      and all(v == 0 for k, v in park.blockers.items() if k != 'U1'),
      str(park.blockers))
check("the baseline is carried, so an absolute count can be read",
      park.baseline_poses == 0,
      f"baseline={park.baseline_poses} -- blockers are absolute counts WITH "
      f"that blocker lifted, not deltas")
check("and the reason SAYS which part to lift",
      'U1' in park.reason and 'lifting' in park.reason, park.reason)

# --------------------------------------------------------------------------
# 2. censused distinguishes "nothing near" from "nothing measured"
# --------------------------------------------------------------------------
res2 = run([{"action": "place_at", "ref": "R1", "at": ON_U1, "rot": 0,
             "within": 0.5}], census_parks=False)
check("with the census off, the park reports censused=False",
      res2.parks and res2.parks[0].censused is False,
      str(res2.parks[0].to_dict() if res2.parks else None))
check("and blockers is empty -- NOT measured, which is a different fact "
      "from 'nothing is in the way'",
      res2.parks and not res2.parks[0].blockers,
      str(res2.parks[0].blockers if res2.parks else None))

# A non-geometric park (a ref that is not a movable part) must NOT claim to
# have been censused -- there is nothing to census.
res3 = run([{"action": "place_at", "ref": "NOSUCHREF", "at": ON_U1,
             "rot": 0, "within": 0.5}])
check("a non-geometric park is not censused",
      res3.parks and res3.parks[0].censused is False,
      str(res3.parks[0].to_dict() if res3.parks else None))

# --------------------------------------------------------------------------
# 3. the census is bounded
# --------------------------------------------------------------------------
many = [{"action": "place_at", "ref": r, "at": ON_U1, "rot": 0, "within": 0.5}
        for r in ('R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10')]
t0 = time.time()
res4 = run(many)
dt = time.time() - t0
check("ten censused parks stay affordable", len(res4.parks) == 10 and dt < 60.0,
      f"{len(res4.parks)} parks in {dt:.1f}s -- an unbounded census is "
      f"~10-24s PER park, so this failing means max_disp stopped pruning")
check("and every one of them is censused",
      all(p.censused for p in res4.parks),
      str([(p.ref, p.censused) for p in res4.parks[:3]]))

# The seeder's own census must stay consistent with the plan's: same shape.
check("the plan's blockers shape matches the seeder's no_pose_blockers",
      all(isinstance(k, str) and isinstance(v, int)
          for k, v in park.blockers.items()), str(park.blockers))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
