#!/usr/bin/env python3
"""Eviction with ORDERING, and a no-pose verdict that names its blockers.

Issue #630 asks for a part whose only pocket is blocked by one movable
incumbent to be seated without hand intervention. Issue #629 asks that a
no-legal-pose verdict name what is in the way, with the count of poses each
blocker frees.

The ordering is the whole thing, and run 19 proved it by getting it wrong
three times. `reseat_scope` already lifts a set and re-seats it, and the run
called it on exactly this case and got a null every time -- because its queue
re-seated the blockers FIRST, at their net centroids, which is back into the
very pockets they block; the blocked switches then swept against a re-blocked
board. `wk/run19/urchin/apply_c2_seats.py:1-12` records that measurement, and
a second hand script had to do evict-then-seat by hand.

The fixture makes the block a THEOREM rather than an observation. On a
16 x 14 board at 0.5mm edge clearance, BIG's 10x10 courtyard confines its
centre to x in [5.5, 10.5], y in [5.5, 8.5]. With SMALL's 1x1 courtyard at
(8, 7), clearing it by 0.2mm needs |cx - 8| >= 5.7 or |cy - 7| >= 5.7, and
neither interval intersects BIG's legal range. So BIG has exactly zero legal
poses while SMALL sits there, and a full rim of them once it moves.
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


def _part(ref, x, y, cy, net):
    return f'''\t(footprint "test:P{ref}"
\t\t(layer "F.Cu")
\t\t(uuid "fp-{ref}")
\t\t(at {x} {y})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 0)
\t\t)
\t\t(fp_rect
\t\t\t(start {-cy} {-cy})
\t\t\t(end {cy} {cy})
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "cy-{ref}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at 0 0)
\t\t\t(size 0.4 0.4)
\t\t\t(layers "F.Cu")
\t\t\t(net {net} "N{net}")
\t\t\t(uuid "p1-{ref}")
\t\t)
\t)
'''


def board():
    fps = (_part('BIG', 8, 7, 5.0, 1) + _part('SMALL', 8, 7, 0.5, 1)
           + _part('OTHER', 8, 7, 0.5, 2))
    body = ('(kicad_pcb\n\t(version 20241229)\n'
            '\t(net 0 "")\n\t(net 1 "N1")\n\t(net 2 "N2")\n'
            '\t(gr_rect\n\t\t(start 0 0)\n\t\t(end 16 14)\n'
            '\t\t(layer "Edge.Cuts")\n\t\t(uuid "e1")\n\t)\n' + fps + ')\n')
    fd, path = tempfile.mkstemp(suffix='.kicad_pcb')
    with os.fdopen(fd, 'w') as f:
        f.write(body)
    return parse_kicad_pcb(path), path


def run(steps):
    pcb, path = board()
    ops, errors = parse_placement_plan({'schema': 1, 'steps': steps})
    assert ops is not None, errors
    try:
        return resolve(pcb, path, ops, clearance=0.2,
                       board_edge_clearance=0.5, grid_step=0.1)
    finally:
        os.unlink(path)


SEAT_SMALL = {"action": "place_at", "ref": "SMALL", "at": [8.0, 7.0],
              "within": 0.5}
SEAT_BIG = {"action": "place_at", "ref": "BIG", "at": [8.0, 7.0],
            "within": 3.0}

# --------------------------------------------------------------------------
# the premise: BIG genuinely cannot seat while SMALL is there
# --------------------------------------------------------------------------
r = run([SEAT_SMALL, SEAT_BIG])
check("the incumbent seats", any(s.ref == 'SMALL' for s in r.seats),
      str(r.summary()))
check("the blocked part has NO legal pose behind it",
      [p.ref for p in r.parks] == ['BIG'], str(r.summary()))

# Retrying it changes nothing -- this is the null run 19 got, three times.
r = run([SEAT_SMALL, SEAT_BIG, SEAT_BIG])
check("simply retrying it is still a null",
      [p.ref for p in r.parks] == ['BIG', 'BIG'],
      str([(p.ref, p.reason) for p in r.parks]))

# --------------------------------------------------------------------------
# the issue's own pin: lift, seat, restore -- no hand intervention
# --------------------------------------------------------------------------
LIFT = {"action": "place_lift", "refs": ["SMALL"], "for": ["BIG"],
        "within": 8.0, "restore": True}
r = run([SEAT_SMALL, SEAT_BIG, LIFT])
seats = {s.ref: s for s in r.seats}
check("#630: the blocked part seats after the lift", 'BIG' in seats,
      str([(p.ref, p.reason) for p in r.parks]))
check("nothing is left parked", not r.parks,
      str([(p.ref, p.reason) for p in r.parks]))
check("the evicted incumbent is seated too, not dropped", 'SMALL' in seats,
      str(r.summary()))
if 'SMALL' in seats:
    check("the incumbent actually moved out of the pocket",
          abs(seats['SMALL'].pose[0] - 8.0) > 1.0
          or abs(seats['SMALL'].pose[1] - 7.0) > 1.0,
          f"SMALL ended at {seats['SMALL'].pose}, still in the pocket")
if 'BIG' in seats and 'SMALL' in seats:
    check("the two do not overlap after the trade",
          abs(seats['BIG'].pose[0] - seats['SMALL'].pose[0]) >= 5.7 - 1e-6
          or abs(seats['BIG'].pose[1] - seats['SMALL'].pose[1]) >= 5.7 - 1e-6,
          f"BIG {seats['BIG'].pose} vs SMALL {seats['SMALL'].pose}")
check("the earlier park is retracted, not carried alongside the seat",
      'BIG' not in {p.ref for p in r.parks})

# --------------------------------------------------------------------------
# #629: the verdict names its blockers, with the count each one frees
# --------------------------------------------------------------------------
note = next((n for n in r.notes if n.startswith('BIG:')), '')
check("#629: the run reports which blocker was lifted", 'SMALL' in note, note)
check("#629: it reports the poses BEFORE, and they are zero",
      '0 before' in note, note)
check("#629: it reports the poses each blocker frees, and they are not zero",
      'with SMALL lifted' in note and ' 0 with SMALL lifted' not in note,
      note)

# --------------------------------------------------------------------------
# lifting the wrong part says so, instead of reporting a bare null again
# --------------------------------------------------------------------------
r2 = run([SEAT_SMALL, SEAT_BIG,
          {"action": "place_lift", "refs": ["OTHER"], "for": ["BIG"],
           "within": 8.0}])
big_park = next((p for p in r2.parks if p.ref == 'BIG'), None)
check("lifting the wrong part still parks the blocked one",
      big_park is not None, str(r2.summary()))
if big_park:
    check("#629: the park is CENSUSED rather than bare",
          big_park.censused, str(big_park.to_dict()))
    check("#629: the census names the part that was tried and its zero",
          big_park.blockers.get('OTHER') == 0, str(big_park.blockers))
    check("the reason says the lifted part is not what is in the way",
          'not what is in the way' in big_park.reason, big_park.reason)

# --------------------------------------------------------------------------
# a locked blocker is refused with the source named, not silently skipped
# --------------------------------------------------------------------------
r3 = run([SEAT_SMALL, SEAT_BIG,
          {"action": "place_lock", "refs": ["SMALL"]},
          {"action": "place_lift", "refs": ["SMALL"], "for": ["BIG"]}])
check("a lock declared by the plan does not silently block the lift",
      any(s.ref == 'BIG' for s in r3.seats),
      "place_lock records an intent to stamp; it does not freeze the state "
      "mid-run")

# --------------------------------------------------------------------------
# nothing to retry is said, not guessed
# --------------------------------------------------------------------------
r4 = run([SEAT_SMALL,
          {"action": "place_lift", "refs": ["SMALL"], "for": ["BIG"]}])
p = next((p for p in r4.parks if p.ref == 'BIG'), None)
check("a part nothing parked has no target to retry, and says so",
      p is not None and 'no target to retry' in p.reason,
      p.reason if p else str(r4.summary()))

# --------------------------------------------------------------------------
# determinism (#457)
# --------------------------------------------------------------------------
plan = [SEAT_SMALL, SEAT_BIG, LIFT]
check("the same lift resolves identically twice",
      run(plan).placements == run(plan).placements)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
