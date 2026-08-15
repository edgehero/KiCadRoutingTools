#!/usr/bin/env python3
"""Resolving a placement plan: statements in, seated poses out.

The properties worth pinning are the ones the hand scripts got right and a
naive implementation gets wrong:

  * a target is a HINT -- the seat is the nearest legal pose to it, and how
    far that was is reported rather than hidden;
  * a failed op leaves the board EXACTLY as it found it (arrange.py left a
    refused part at its pile pose and carried on);
  * `place_relative` resolves against the parent's RESOLVED pose, not its
    target (arrange.py:182-184) -- and refuses when the parent is unseated,
    because a pile coordinate means nothing;
  * a park is a measurement with a reason, never a silence;
  * an op the resolver cannot execute refuses the run instead of being
    skipped, which would place a different board and report success.

The board is synthetic (the test_456 idiom) so the geometry is arithmetic:
a 100x60 outline, everything piled at one point, and nets named the way a
keyboard matrix names them so `place_index`'s two-hop join is exercised for
real rather than mocked.
"""
import math
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
from placement.plan_ops import PlanError, parse_placement_plan
from placement.plan_resolve import resolve

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


# --------------------------------------------------------------------------
# fixture
# --------------------------------------------------------------------------
NETS = ['', 'COL0', 'COL1', 'ROW0', 'ROW1',
        'Net-(SW1-Pad2)', 'Net-(SW2-Pad2)', 'VCC']


def _part(ref, x, y, pads, cy=3.0, locked=False):
    lock = '\t\t(locked yes)\n' if locked else ''
    body = ''
    for i, (num, dx, dy, net) in enumerate(pads):
        nid = NETS.index(net) if net in NETS else 0
        body += (f'\t\t(pad "{num}" smd rect\n\t\t\t(at {dx} {dy})\n'
                 f'\t\t\t(size 0.6 0.8)\n\t\t\t(layers "F.Cu")\n'
                 f'\t\t\t(net {nid} "{net}")\n\t\t\t(uuid "p{i}-{ref}")\n\t\t)\n')
    return f'''\t(footprint "test:P{ref}"
\t\t(layer "F.Cu")
{lock}\t\t(uuid "fp-{ref}")
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
{body}\t)
'''


def board():
    """Every free part piled at (50, 30) -- the place-from-scratch task."""
    fps = (
        _part('SW1', 50, 30, [('1', -0.5, 0, 'COL0'),
                              ('2', 0.5, 0, 'Net-(SW1-Pad2)')]) +
        _part('SW2', 50, 30, [('1', -0.5, 0, 'COL1'),
                              ('2', 0.5, 0, 'Net-(SW2-Pad2)')]) +
        _part('D1', 50, 30, [('1', -0.5, 0, 'ROW0'),
                             ('2', 0.5, 0, 'Net-(SW1-Pad2)')], cy=1.0) +
        _part('D2', 50, 30, [('1', -0.5, 0, 'ROW1'),
                             ('2', 0.5, 0, 'Net-(SW2-Pad2)')], cy=1.0) +
        _part('U1', 50, 30, [('1', 0, 0, 'VCC')], cy=4.0) +
        _part('J1', 50, 30, [('1', 0, 0, 'VCC')], cy=2.0) +
        _part('MH1', 90, 50, [('1', 0, 0, '')], cy=1.5, locked=True)
    )
    nets = ''.join(f'\t(net {i} "{n}")\n' for i, n in enumerate(NETS))
    body = ('(kicad_pcb\n\t(version 20241229)\n' + nets +
            '\t(gr_rect\n\t\t(start 0 0)\n\t\t(end 100 60)\n'
            '\t\t(layer "Edge.Cuts")\n\t\t(uuid "e1")\n\t)\n'
            + fps + ')\n')
    fd, path = tempfile.mkstemp(suffix='.kicad_pcb')
    with os.fdopen(fd, 'w') as f:
        f.write(body)
    return parse_kicad_pcb(path), path


def run(steps, **kw):
    pcb, path = board()
    ops, errors = parse_placement_plan({'schema': 1, 'steps': steps})
    assert ops is not None, errors
    try:
        return resolve(pcb, path, ops, clearance=0.2,
                       board_edge_clearance=0.5, grid_step=0.1, **kw)
    finally:
        os.unlink(path)


INDEXES = [
    {"action": "place_index", "name": "diode", "select": r"^D\d+$",
     "fields": {"row": {"pattern": r"^(R_)?ROW(\d)$", "group": 2,
                        "as": "int"}}},
    {"action": "place_index", "name": "switch", "select": r"^SW\d+$",
     "fields": {"col": {"pattern": r"^(R_)?COL(\d)$", "group": 2,
                        "as": "int"},
                "half": {"pattern": r"^(R_)?COL(\d)$", "group": 1,
                         "as": "str", "map": {"R_": "R", "": "L"}}},
     "partner": {"index": "diode", "pattern": r"^Net-\(",
                 "inherit": ["row"], "as": "partner"}},
]

# --------------------------------------------------------------------------
# place_index: structure out of net names, including the two-hop join
# --------------------------------------------------------------------------
r = run(INDEXES)
sw = r.indexes['switch']['members']
di = r.indexes['diode']['members']
check("index selects by reference regex",
      sorted(sw) == ['SW1', 'SW2'] and sorted(di) == ['D1', 'D2'],
      f"{sorted(sw)} / {sorted(di)}")
check("field from a net name, cast to int",
      sw.get('SW1', {}).get('col') == 0 and sw.get('SW2', {}).get('col') == 1,
      str(sw))
check("absent optional capture group maps to a real value",
      sw.get('SW1', {}).get('half') == 'L', str(sw))
check("partner join through the shared private net",
      sw.get('SW1', {}).get('partner') == 'D1'
      and sw.get('SW2', {}).get('partner') == 'D2', str(sw))
check("inherited field crosses the join",
      sw.get('SW1', {}).get('row') == 0 and sw.get('SW2', {}).get('row') == 1,
      str(sw))

# --------------------------------------------------------------------------
# place_at
# --------------------------------------------------------------------------
r = run([{"action": "place_at", "ref": "U1", "at": [20.0, 20.0],
          "within": 5.0}])
check("place_at seats the part", len(r.seats) == 1 and not r.parks,
      str(r.summary()))
if r.seats:
    s = r.seats[0]
    check("place_at lands within its budget of the target",
          s.moved_mm <= 5.0 + 1e-6, f"moved {s.moved_mm:.3f}mm")
    check("the seat reports how far from the target it landed",
          'moved_mm' in s.to_dict())

r = run([{"action": "place_at", "ref": "U1", "at": [20.0, 20.0], "rot": 90}])
check("place_at honours a requested rotation",
      r.seats and abs(r.seats[0].pose[2] - 90.0) < 1e-6,
      str(r.seats[0].pose) if r.seats else 'no seat')

# A target well outside the outline, with a budget too small to reach it.
r = run([{"action": "place_at", "ref": "U1", "at": [-50.0, -50.0],
          "within": 1.0}])
check("an unreachable target parks rather than placing something else",
      not r.seats and len(r.parks) == 1, str(r.summary()))
if r.parks:
    p = r.parks[0]
    check("the park names the target and the budget",
          '-50.0' in p.reason and p.within == 1.0, p.reason)

# --------------------------------------------------------------------------
# a failed op leaves the board exactly as it found it
# --------------------------------------------------------------------------
pcb, path = board()
ops, _ = parse_placement_plan({'schema': 1, 'steps': [
    {"action": "place_at", "ref": "U1", "at": [-50.0, -50.0], "within": 1.0}]})
import pose_score
st = pose_score.make_state(pcb, path, clearance=0.2,
                           board_edge_clearance=0.5, grid_step=0.1)
before = {r_: (st.parts[r_].x, st.parts[r_].y, st.parts[r_].rot)
          for r_ in st.parts}
resolve(pcb, path, ops, state=st)
after = {r_: (st.parts[r_].x, st.parts[r_].y, st.parts[r_].rot)
         for r_ in st.parts}
check("a parked op restores every pose it touched", before == after,
      str({k: (before[k], after[k]) for k in before if before[k] != after[k]}))
os.unlink(path)

# --------------------------------------------------------------------------
# place_relative: against the parent's RESOLVED pose
# --------------------------------------------------------------------------
r = run(INDEXES + [
    {"action": "place_at", "ref": "SW1", "at": [20.0, 20.0], "within": 3.0},
    {"action": "place_at", "ref": "SW2", "at": [40.0, 20.0], "within": 3.0},
    {"action": "place_relative", "refs": "index:diode", "of": "index:switch",
     "pair_by": "partner", "offset": [0.0, 8.5], "within": 4.0},
])
seats = {s.ref: s for s in r.seats}
check("place_relative seats both children",
      'D1' in seats and 'D2' in seats, str(r.summary()))
if 'D1' in seats and 'SW1' in seats:
    want = (seats['SW1'].pose[0], seats['SW1'].pose[1] + 8.5)
    got = seats['D1'].target
    check("the child's target is the parent's RESOLVED pose plus the offset",
          abs(got[0] - want[0]) < 1e-6 and abs(got[1] - want[1]) < 1e-6,
          f"target {got} vs parent-resolved {want}")
    check("the child pairs with its own parent, not by position",
          abs(seats['D2'].target[0] - seats['SW2'].pose[0]) < 1e-6,
          f"D2 target {seats['D2'].target} vs SW2 {seats['SW2'].pose}")

# The parent is never seated: the child must refuse, not resolve against a
# pile coordinate.
r = run(INDEXES + [
    {"action": "place_relative", "refs": "index:diode", "of": "index:switch",
     "pair_by": "partner", "offset": [0.0, 8.5], "within": 4.0},
])
check("an unseated parent parks its child instead of using the pile pose",
      not r.seats and len(r.parks) == 2, str(r.summary()))
check("the park says why",
      r.parks and 'not seated yet' in r.parks[0].reason,
      r.parks[0].reason if r.parks else '')

# --------------------------------------------------------------------------
# where / order
# --------------------------------------------------------------------------
r = run(INDEXES + [
    {"action": "place_at", "ref": "SW1", "at": [20.0, 20.0], "within": 3.0},
    {"action": "place_relative", "refs": "index:diode", "of": "index:switch",
     "pair_by": "partner", "offset": [0.0, 8.5], "within": 4.0,
     "where": {"row": {"lt": 1}}},
])
check("`where` filters the selection",
      [s.ref for s in r.seats if s.action == 'place_relative'] == ['D1'],
      str([s.ref for s in r.seats]))

# --------------------------------------------------------------------------
# place_edge
# --------------------------------------------------------------------------
r = run([{"action": "place_edge", "refs": ["J1"], "edge": "north",
          "overhang": 1.0}])
check("place_edge seats the connector", len(r.seats) == 1 and not r.parks,
      str(r.summary()))
if r.seats:
    check("place_edge puts it past the north edge",
          r.seats[0].pose[1] < 3.0,
          f"y={r.seats[0].pose[1]:.3f} (outline starts at y=0)")

# --------------------------------------------------------------------------
# place_lock, and the file-locked part
# --------------------------------------------------------------------------
r = run([{"action": "place_lock", "refs": ["MH*", "J1"]}])
check("place_lock records the refs it would stamp",
      r.lock_refs == ['J1', 'MH1'], str(r.lock_refs))

r = run([{"action": "place_at", "ref": "MH1", "at": [10.0, 10.0]}])
check("a file-locked part is refused, not moved",
      not r.seats and r.parks and 'locked yes' in r.parks[0].reason,
      r.parks[0].reason if r.parks else str(r.summary()))

# --------------------------------------------------------------------------
# an op the resolver does not execute refuses the run
# --------------------------------------------------------------------------
# `plan_ops` now refuses an unimplemented op at VALIDATION, so this path is
# only reachable by a caller that skipped validation -- which is exactly when
# a defence-in-depth guard has to hold. Call resolve() with an unvalidated op.
from placement.plan_ops import UNIMPLEMENTED_ACTIONS
if not UNIMPLEMENTED_ACTIONS:
    check("every op is implemented, so there is nothing to refuse", True)
else:
    # Whichever op is still unimplemented, not a hardcoded name: this used to
    # name `place_pack`, and when place_pack shipped the test started asserting
    # that a working op refuses.
    _act = UNIMPLEMENTED_ACTIONS[0]
    pcb_, path_ = board()
    try:
        resolve(pcb_, path_, [{"action": _act}])
        check("an unimplemented op refuses", False, "it ran anyway")
    except PlanError as e:
        check("an unimplemented op refuses at resolve too, naming itself",
              _act in str(e) and 'nothing was placed' in str(e), str(e))
    finally:
        os.unlink(path_)

# --------------------------------------------------------------------------
# determinism (#457): the same plan on the same board resolves identically
# --------------------------------------------------------------------------
plan = INDEXES + [
    {"action": "place_at", "ref": "SW1", "at": [20.0, 20.0], "within": 3.0},
    {"action": "place_at", "ref": "SW2", "at": [40.0, 20.0], "within": 3.0},
    {"action": "place_relative", "refs": "index:diode", "of": "index:switch",
     "pair_by": "partner", "offset": [0.0, 8.5], "within": 4.0},
]
a = run(plan).placements
b = run(plan).placements
check("the same plan resolves to the same poses twice", a == b,
      f"{a}\n{b}")

# --------------------------------------------------------------------------
# the summary is machine-readable and counts what a caller gates on
# --------------------------------------------------------------------------
r = run(plan)
s = r.summary()
check("summary carries seated/parked/parked_refs/complete",
      {'seated', 'parked', 'parked_refs', 'complete'} <= set(s), str(s))
check("parked_refs is names, not a count",
      isinstance(s['parked_refs'], list), str(s))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
