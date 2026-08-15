#!/usr/bin/env python3
"""`place_pack` policies, and a keepout that is HONOURED rather than graded.

The keepout half is the one with a scar behind it. The intent schema has
carried a `keepouts` rule since #549, `floorplan.py` grades it, and NO seeding
module reads it -- so a reserved strip could only ever be reported after the
parts were already in it. `wk/run19/urchin/arrange.py:27` is what that costs:
its `X0 = 46.0` exists to keep the key lattice clear of U1's vertical strip,
and the reservation lives in a COMMENT ("the outer strip x<38 is U1's"),
because nothing in the toolchain could hold it.

So the test that matters is the negative one: the same plan, with and without
the keepout, must put the part in DIFFERENT places. A keepout that changes
nothing is decoration.

`place_pack`'s `radial` policy is named rather than defaulted, because it is
the CURRENT zone-stage behaviour and it is also the one that measurably
failed run 19 -- pin-count-descending order seated 34 six-pad diodes before 34
fifteen-millimetre switches, and the smalls took the centre.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)
        sys.path.insert(0, os.path.join(p, 'py_router'))
        sys.path.insert(0, os.path.join(p, 'py_tools'))
        sys.path.insert(0, os.path.join(p, 'py_placer'))

from kicad_parser import parse_kicad_pcb
from placement.plan_ops import parse_placement_plan
from placement.plan_resolve import resolve

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


def _part(ref, x, y, cy, side='F.Cu'):
    return f'''\t(footprint "test:P{ref}"
\t\t(layer "{side}")
\t\t(uuid "fp-{ref}")
\t\t(at {x} {y})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 0)
\t\t)
\t\t(fp_rect
\t\t\t(start {-cy} {-cy})
\t\t\t(end {cy} {cy})
\t\t\t(layer "{side[0]}.CrtYd")
\t\t\t(uuid "cy-{ref}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at 0 0)
\t\t\t(size 0.4 0.4)
\t\t\t(layers "{side}")
\t\t\t(net 1 "N1")
\t\t\t(uuid "p1-{ref}")
\t\t)
\t)
'''


def board(extra=''):
    fps = ''.join(_part(f'R{i}', 50, 30, 1.0) for i in range(1, 7))
    fps += _part('MH1', 50, 30, 1.0) + extra
    body = ('(kicad_pcb\n\t(version 20241229)\n'
            '\t(net 0 "")\n\t(net 1 "N1")\n'
            '\t(gr_rect\n\t\t(start 0 0)\n\t\t(end 100 60)\n'
            '\t\t(layer "Edge.Cuts")\n\t\t(uuid "e1")\n\t)\n' + fps + ')\n')
    fd, path = tempfile.mkstemp(suffix='.kicad_pcb')
    with os.fdopen(fd, 'w') as f:
        f.write(body)
    return parse_kicad_pcb(path), path


def run(steps, extra=''):
    pcb, path = board(extra)
    ops, errors = parse_placement_plan({'schema': 1, 'steps': steps})
    assert ops is not None, errors
    try:
        return resolve(pcb, path, ops, clearance=0.2,
                       board_edge_clearance=0.5, grid_step=0.1)
    finally:
        os.unlink(path)


ZONE = [10.0, 10.0, 50.0, 40.0]

# --------------------------------------------------------------------------
# place_pack policies
# --------------------------------------------------------------------------
for policy in ('radial', 'rows', 'grid', 'ring'):
    r = run([{"action": "place_pack", "refs": ["R*"], "zone": ZONE,
              "policy": policy, "within": 6.0}])
    seats = {s.ref: s.pose for s in r.seats}
    check(f"policy {policy}: every member seats",
          len(r.seats) == 6 and not r.parks,
          str(r.summary()) + str([(p.ref, p.reason) for p in r.parks]))
    inside = all(ZONE[0] - 1 <= p[0] <= ZONE[2] + 1
                 and ZONE[1] - 1 <= p[1] <= ZONE[3] + 1
                 for p in seats.values())
    check(f"policy {policy}: all of them land in the zone", inside,
          str(sorted(seats.items())))
    check(f"policy {policy}: no two share a pose",
          len({(round(p[0], 3), round(p[1], 3))
               for p in seats.values()}) == len(seats),
          str(sorted(seats.items())))

# The policies must actually DIFFER -- four names for one behaviour would be
# worse than one name.
poses = {}
for policy in ('radial', 'rows', 'grid', 'ring'):
    r = run([{"action": "place_pack", "refs": ["R*"], "zone": ZONE,
              "policy": policy, "within": 6.0}])
    poses[policy] = sorted((s.ref, round(s.target[0], 2),
                            round(s.target[1], 2)) for s in r.seats)
check("the four policies are four different layouts",
      len({str(v) for v in poses.values()}) == 4,
      str({k: v[:2] for k, v in poses.items()}))

# --------------------------------------------------------------------------
# THE KEEPOUT: graded-but-not-honoured is the bug; this is the fix
# --------------------------------------------------------------------------
STRIP = [10.0, 10.0, 30.0, 40.0]     # the left half of the zone
without = run([{"action": "place_pack", "refs": ["R*"], "zone": ZONE,
                "policy": "rows", "within": 20.0}])
with_ko = run([{"action": "place_keepout", "rect": STRIP,
                "reason": "reserved for U1"},
               {"action": "place_pack", "refs": ["R*"], "zone": ZONE,
                "policy": "rows", "within": 20.0}])


def in_strip(pose):
    return STRIP[0] <= pose[0] <= STRIP[2] and STRIP[1] <= pose[1] <= STRIP[3]


n_without = sum(1 for s in without.seats if in_strip(s.pose))
n_with = sum(1 for s in with_ko.seats if in_strip(s.pose))
check("without the keepout, parts DO land in the strip", n_without > 0,
      f"{n_without} of {len(without.seats)} -- if this is 0 the fixture "
      f"proves nothing")
check("the keepout is HONOURED during seeding, not merely graded after",
      n_with == 0, f"{n_with} part(s) still seated inside the reserved strip")
check("and the parts are still seated, just elsewhere",
      len(with_ko.seats) == len(without.seats),
      f"{len(with_ko.seats)} vs {len(without.seats)}")
check("the run says what it reserved and why",
      any('reserved' in n and 'U1' in n for n in with_ko.notes),
      str(with_ko.notes[:2]))

# `allow`: a keepout drawn FOR a part must not exclude that part.
allowed = run([{"action": "place_keepout", "rect": STRIP,
                "allow": ["MH*"], "reason": "mount pad"},
               {"action": "place_at", "ref": "MH1",
                "at": [20.0, 25.0], "within": 2.0},
               {"action": "place_at", "ref": "R1",
                "at": [20.0, 25.0], "within": 2.0}])
seats = {s.ref: s.pose for s in allowed.seats}
check("`allow` exempts the part the keepout was drawn for",
      'MH1' in seats and in_strip(seats['MH1']),
      str(seats.get('MH1')))
check("and still refuses everything else",
      'R1' not in seats or not in_strip(seats['R1']),
      f"R1 at {seats.get('R1')} -- inside a keepout that does not allow it")

# `sides`: a keepout on one face must not block the other.
back = run([{"action": "place_keepout", "rect": STRIP, "sides": ["B"],
             "reason": "back-side only"},
            {"action": "place_at", "ref": "R1", "at": [20.0, 25.0],
             "within": 2.0}])
s_back = {s.ref: s.pose for s in back.seats}
check("a B-side keepout does not block an F-side part",
      'R1' in s_back and in_strip(s_back['R1']), str(s_back.get('R1')))

# Ops run IN ORDER: a keepout cannot retroactively invalidate earlier seats.
after = run([{"action": "place_at", "ref": "R1", "at": [20.0, 25.0],
              "within": 2.0},
             {"action": "place_keepout", "rect": STRIP}])
s_after = {s.ref: s.pose for s in after.seats}
check("a keepout declared AFTER a seat leaves it alone, and says so",
      'R1' in s_after and in_strip(s_after['R1'])
      and any('already seated' in n for n in after.notes),
      str(after.notes[-1:]))

# --------------------------------------------------------------------------
# determinism (#457)
# --------------------------------------------------------------------------
plan = [{"action": "place_keepout", "rect": STRIP},
        {"action": "place_pack", "refs": ["R*"], "zone": ZONE,
         "policy": "grid", "within": 20.0}]
check("the same pack resolves identically twice",
      run(plan).placements == run(plan).placements)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
