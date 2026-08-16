#!/usr/bin/env python3
"""`place_fixed`: a pose the plan is not entitled to choose.

On a PILE every part sits at the board centre, so a mounting hole or an edge
receptacle -- whose position the mechanical drawing already fixed -- has no
meaningful coordinate and no way to be told one. Measured before this op
existed, trying to say it with `place_at`:

    place_at H1 at its own pose, within 0.0   -> REFUSED ("within must be > 0")
    place_at H1 at its own pose, within 0.01  -> PARK
    place_at H1 at its own pose, within 0.1   -> PARK (also at --grid-step 0.05)
    place_at H1 at its own pose, within 3.0   -> seated, MOVED 1.4142mm

A hole is not a request, and the last line is the worst of the four: it looks
like success. `place_lock` does not help either -- it pins a part where it
already is, which on a pile is the middle of the board.

So `place_fixed` is the one op that runs no seat gate. What it may and may
not do -- the "may not" half is all counterexamples an audit found after the
first version shipped claiming otherwise:

  1. it sets the pose EXACTLY, whatever the geometry says
  2. it is an obstacle for every op, BEFORE and after its own step (it is
     excluded from the pile set at construction, not only when its op runs --
     on a pile every part is piled, so the `plan_target_refs` skip alone was
     inert exactly where this op matters)
  3. an illegal fixed pose is DISCLOSED and NAMES what it overlaps
  4. it will NOT move a `(locked yes)` part -- a lock is precisely the
     statement that a pose is not this tool's to change, and `place_at` and
     `place_lift` both refuse one. Asserting the pose a locked part already
     has is a legitimate no-op. It used to move them, and the writer
     committed it.
  5. it will NOT assert a rotation outside the part's legality lattice --
     there is no courtyard for it, so `part.rect` silently returns the
     0-degree box, the disclosure in (3) grades a shape the part does not
     have, and every later op treats it as an obstacle with that wrong shape
  6. `place_lift` will NOT lift it -- lifting one wrote it 4.000mm from its
     assertion, emitted two placements for the same ref, and reported
     `complete: true` with no note
"""
import copy
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'kicad_files', 'flat_hierarchy.kicad_pcb')
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

SRC = parse_kicad_pcb(BOARD)
TRUE = {r: (round(f.x, 3), round(f.y, 3), (f.rotation or 0.0) % 360.0)
        for r, f in SRC.footprints.items()}


def piled():
    """Every part at the board centre, rotation 0 -- what staging produces."""
    pcb = copy.deepcopy(SRC)
    x0, y0, x1, y1 = pcb.board_info.board_bounds
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    for fp in pcb.footprints.values():
        fp.x, fp.y, fp.rotation = cx, cy, 0.0
    return pcb


def run(pcb, steps):
    ops, errors = parse_placement_plan({"schema": 1, "steps": steps})
    assert ops is not None, errors
    return resolve(pcb, BOARD, ops, clearance=0.2,
                   board_edge_clearance=0.5, grid_step=0.1)


# UNLOCKED mechanical-ish parts. HOLE1-6 are `(locked yes)` in this board, and
# place_fixed refuses to MOVE a locked part -- correctly, since a lock is
# exactly the statement that a pose is not this tool's to change. An earlier
# version of this file fixed those six and asserted "every fixed part is
# seated", which encoded the bug: place_fixed was moving locked parts and the
# writer was committing the move.
HOLES = ['J1', 'C1', 'C2', 'D1', 'U1']
LOCKED = 'HOLE1'

# --------------------------------------------------------------------------
# 1. it sets the pose exactly, from a pile
# --------------------------------------------------------------------------
pcb = piled()
res = run(pcb, [{"action": "place_fixed", "ref": h, "at": list(TRUE[h][:2]),
                 "rot": TRUE[h][2]} for h in HOLES])
check("every fixed part is seated", len(res.seats) == len(HOLES),
      f"{[s.ref for s in res.seats]}, parks {[p.ref for p in res.parks]}")
placed = {s.ref: s.pose for s in res.seats}
off = [(r, placed.get(r), TRUE[r]) for r in HOLES
       if placed.get(r) is None
       or abs(placed[r][0] - TRUE[r][0]) > 1e-6
       or abs(placed[r][1] - TRUE[r][1]) > 1e-6]
check("each lands EXACTLY on the asserted coordinate", not off, str(off[:3]))
check("and the run reports how far each came (they were on the pile)",
      all(s.moved_mm > 1.0 for s in res.seats),
      str([(s.ref, round(s.moved_mm, 1)) for s in res.seats[:3]]))
check("no fixed part is parked", not res.parks,
      str([(p.ref, p.reason) for p in res.parks]))

# The same thing said with place_at cannot work -- this is why the op exists.
pcb2 = piled()
res2 = run(pcb2, [{"action": "place_at", "ref": "HOLE1",
                   "at": list(TRUE['HOLE1'][:2]), "rot": TRUE['HOLE1'][2],
                   "within": 0.1}])
check("place_at with a tight budget PARKS the same hole "
      "(the op is not redundant)",
      not res2.seats and len(res2.parks) == 1,
      f"seats {[(s.ref, round(s.moved_mm, 3)) for s in res2.seats]}")

# And on THIS board it is worse than a budget problem: the holes' own true
# poses are ILLEGAL by the seat gate -- they hang 1.38mm off the outline, which
# is correct for a mounting hole and fatal for `pose_ok`. So no `within` can
# ever place them, and a search-based op is the wrong tool by construction.
import pose_score
from placement import seeder as _seeder

_st = pose_score.make_state(SRC, BOARD, clearance=0.2,
                            board_edge_clearance=0.5, grid_step=0.1)
_h = _st.parts['HOLE1']
check("the hole's OWN true pose fails the seat gate "
      "(so no search op could ever reach it)",
      not _seeder.pose_ok(_st, 'HOLE1', _h.x, _h.y, _h.rot, set()),
      "it hangs off the outline by design, like every mounting hole")
pcb3 = piled()
res3 = run(pcb3, [{"action": "place_at", "ref": "HOLE1",
                   "at": list(TRUE['HOLE1'][:2]), "rot": TRUE['HOLE1'][2],
                   "within": 3.0}])
at_true = [s for s in res3.seats
           if abs(s.pose[0] - TRUE['HOLE1'][0]) < 1e-6
           and abs(s.pose[1] - TRUE['HOLE1'][1]) < 1e-6]
check("so place_at at a LOOSE budget still cannot put it where it belongs",
      not at_true,
      f"place_at reached {[round(v, 4) for v in res3.seats[0].pose[:2]]}"
      if res3.seats else "it parked, which is the honest failure")

# --------------------------------------------------------------------------
# 2. a fixed part is an OBSTACLE, not an invisible one
# --------------------------------------------------------------------------
pcb4 = piled()
res4 = run(pcb4, [
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
    {"action": "place_at", "ref": "C3", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2], "within": 0.5},
])
check("a later op cannot seat on top of a fixed part",
      [s.ref for s in res4.seats] == ['C1']
      and [p.ref for p in res4.parks] == ['C3'],
      f"seats {[s.ref for s in res4.seats]}, parks {[p.ref for p in res4.parks]}")
check("the park is censused", res4.parks and res4.parks[0].censused,
      str(res4.parks[0].to_dict() if res4.parks else None))

# A LOCKED part is not this tool's to move, and place_fixed is not an
# exemption -- place_at and place_lift both refuse one. It used to move them,
# and the writer committed it: HOLE1 went from (229.87, 44.45) to (10, 10)
# with nothing disclosing it.
res_lock = run(copy.deepcopy(SRC), [
    {"action": "place_fixed", "ref": LOCKED, "at": [10.0, 10.0]}])
check("place_fixed REFUSES to move a (locked yes) part",
      [p.ref for p in res_lock.parks] == [LOCKED] and not res_lock.seats,
      f"seats {[(s.ref, s.pose[:2]) for s in res_lock.seats]}")
check("and the refusal names the lock and what to do instead",
      res_lock.parks and 'locked yes' in res_lock.parks[0].reason
      and 'EXISTING pose' in res_lock.parks[0].reason,
      str(res_lock.parks[0].reason if res_lock.parks else None))
# ...but ASSERTING the pose it already has is a legitimate no-op.
res_lock2 = run(copy.deepcopy(SRC), [
    {"action": "place_fixed", "ref": LOCKED, "at": list(TRUE[LOCKED][:2]),
     "rot": TRUE[LOCKED][2]}])
check("asserting a locked part's EXISTING pose is allowed, and moves nothing",
      [s.ref for s in res_lock2.seats] == [LOCKED]
      and res_lock2.seats[0].moved_mm < 1e-6,
      f"parks {[(p.ref, p.reason[:40]) for p in res_lock2.parks]}")

# A rotation outside the part's legality lattice has NO courtyard, so
# `part.rect` silently returns the 0-degree box -- the disclosure below would
# then grade a shape the part does not have, and every later op would treat it
# as an obstacle with that wrong shape. seat() guards this; place_fixed did not.
res_rot = run(piled(), [
    {"action": "place_fixed", "ref": "U3", "at": [96.52, 71.247], "rot": 45}])
check("a rotation outside the legality lattice is REFUSED, not asserted",
      [p.ref for p in res_rot.parks] == ['U3'] and not res_rot.seats,
      f"seats {[(s.ref, s.pose) for s in res_rot.seats]}")
check("and the refusal names the lattice",
      res_rot.parks and 'legality lattice' in res_rot.parks[0].reason,
      str(res_rot.parks[0].reason if res_rot.parks else None))

# place_lift must not relocate an asserted mechanical fact. It used to: the
# fixed part was written TWICE, ending 4.000mm from its assertion, with
# `complete: true` and no note.
res_lift = run(copy.deepcopy(SRC), [
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
    {"action": "place_at", "ref": "C2", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2], "within": 0.5},
    {"action": "place_lift", "refs": ["C1"], "for": ["C2"], "within": 5.0},
])
check("place_lift refuses to lift a place_fixed part",
      any(p.ref == 'C1' and 'mechanical fact' in p.reason
          for p in res_lift.parks),
      str([(p.ref, p.reason[:50]) for p in res_lift.parks]))
_c1 = [pl for pl in res_lift.placements if pl['reference'] == 'C1']
check("so the fixed part is written exactly once, at its assertion",
      len(_c1) == 1 and abs(_c1[0]['new_x'] - TRUE['C1'][0]) < 1e-6,
      str(_c1))

# With an UNLOCKED part fixed, the census does name it.
pcb4b = piled()
res4b = run(pcb4b, [
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
    {"action": "place_at", "ref": "C2", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2], "within": 0.5},
])
check("an UNLOCKED fixed part IS named as the blocker of a later park",
      res4b.parks and 'C1' in (res4b.parks[0].blockers or {}),
      str(res4b.parks[0].blockers if res4b.parks else
          [s.ref for s in res4b.seats]))

# A fixed part must be an obstacle from the START, not only from the moment
# its op runs. `op_place_fixed` discards from `pending` itself, so putting
# place_fixed first hides whether `plan_target_refs` also skips it -- and
# without that skip a fixed part declared LATER in the plan is a plan target,
# i.e. invisible, and an earlier op seats straight through it. Measured on the
# PLACED board (on a pile every part is excluded anyway, so the case cannot
# appear there).
res_order = run(copy.deepcopy(SRC), [
    {"action": "place_at", "ref": "C2", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2], "within": 0.5},
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
])
check("a part fixed LATER in the plan is already an obstacle EARLIER",
      'C2' in [p.ref for p in res_order.parks],
      f"seats {[(s.ref, s.action) for s in res_order.seats]}, "
      f"parks {[p.ref for p in res_order.parks]}")

# --------------------------------------------------------------------------
# 3. an illegal assertion is disclosed, not silently accepted
# --------------------------------------------------------------------------
pcb5 = piled()
res5 = run(pcb5, [
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
    # deliberately on top of the one just fixed
    {"action": "place_fixed", "ref": "C2", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]},
])
check("both assertions are honoured -- a mechanical fact outranks the gate",
      len(res5.seats) == 2, str([s.ref for s in res5.seats]))
check("and the illegal one is DISCLOSED in the notes",
      any('not a legal pose' in n and 'C2' in n for n in res5.notes),
      str(res5.notes[-2:]))
# The note must NAME what it hit. "not a legal pose" alone leaves the author
# to find the other part by eye, and the commonest cause is a part this same
# plan seated there.
check("the disclosure names the part it overlaps",
      any('C2' in n and 'overlaps C1' in n for n in res5.notes),
      str([n for n in res5.notes if 'C2' in n]))
# ...and it must NOT fire on a legal assertion, or it is noise.
res5b = run(piled(), [
    {"action": "place_fixed", "ref": "C1", "at": list(TRUE['C1'][:2]),
     "rot": TRUE['C1'][2]}])
check("a LEGAL assertion produces no such note (the check is not vacuous)",
      not [n for n in res5b.notes if 'not a legal pose' in n],
      str(res5b.notes))

# A ref that is not on the board parks rather than crashing.
res6 = run(piled(), [{"action": "place_fixed", "ref": "NOSUCH",
                      "at": [50.0, 50.0]}])
check("a ref that is not on the board parks, naming why",
      res6.parks and 'not a movable part' in res6.parks[0].reason,
      str([(p.ref, p.reason) for p in res6.parks]))

# --------------------------------------------------------------------------
# "never moves that part" -- against EVERY op, not just place_lift
#
# Only place_lift was ever given a check. place_at, place_array, place_slots,
# place_edge and a SECOND place_fixed all moved an asserted pose, emitted a
# second Seat for the same ref, and reported `complete: true` with no note --
# and `placements` is in seating order, so the writer applied the later pose.
# The schema text promises "never moves that part"; this is where it is kept.
# --------------------------------------------------------------------------
_T = list(TRUE['C1'][:2])
_FIX = {"action": "place_fixed", "ref": "C1", "at": _T, "rot": TRUE['C1'][2]}
_ROUTES = {
    'place_at': {"action": "place_at", "ref": "C1", "at": [_T[0] + 6, _T[1]],
                 "rot": TRUE['C1'][2], "within": 8},
    'place_fixed_again': {"action": "place_fixed", "ref": "C1",
                          "at": [_T[0] + 6, _T[1]], "rot": TRUE['C1'][2]},
    'place_array': {"action": "place_array", "refs": ["C1"], "pitch": [2, 2],
                    "origin": {"x": _T[0] + 4, "y": _T[1]}, "within": 8},
    'place_slots': {"action": "place_slots", "refs": ["C1"],
                    "slots": [[_T[0] + 6, _T[1]]], "within": 8},
    'place_edge': {"action": "place_edge", "refs": ["C1"], "edge": "north",
                   "overhang": 0.5},
    'place_lift': {"action": "place_lift", "refs": ["C1"], "for": ["C2"],
                   "within": 5},
}
_moved = []
for _name, _step in _ROUTES.items():
    _r = run(copy.deepcopy(SRC), [_FIX, _step])
    _pl = [q for q in _r.placements if q['reference'] == 'C1']
    if len(_pl) != 1 or abs(_pl[0]['new_x'] - _T[0]) > 1e-6 \
            or abs(_pl[0]['new_y'] - _T[1]) > 1e-6:
        _moved.append((_name, len(_pl),
                       [(round(q['new_x'], 3), round(q['new_y'], 3))
                        for q in _pl]))
check("NO op moves a place_fixed part, and it is written exactly once",
      not _moved, f"{len(_moved)} route(s) moved it: {_moved}")
check("and all six routes were exercised", len(_ROUTES) == 6,
      str(sorted(_ROUTES)))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
