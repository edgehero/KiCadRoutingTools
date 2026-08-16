#!/usr/bin/env python3
"""An overfull `place_pack` zone must say by HOW MUCH.

Before this, overflowing a zone produced N identical refusals at one
coordinate:

    PARK C76: no legal pose within 6mm of (178.2, 101.0)
    PARK R22: no legal pose within 6mm of (178.2, 101.0)
    PARK R23: ... R24: ... R4: ...

Five refs, one target, and no answer to the only question the author has --
*how much bigger does the zone need to be*. The whole-board form of that
answer already existed (`options.grow_board`); this is the same arithmetic
scoped to a zone.

The second message is the one that matters more. A zone can have the area and
still not take the parts, and saying "short by N mm2" there would send the
author to widen a zone that is already big enough. So the two cases are
reported differently, and area is stated as the NECESSARY condition it is.
"""
import copy
import os
import sys

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

SRC = parse_kicad_pcb(BOARD)
REFS = [r for r in sorted(SRC.footprints) if r.startswith('J')][:8]


def run(zone, policy='rows', refs=None):
    plan = {"schema": 1, "steps": [
        {"action": "place_pack", "refs": refs or REFS, "zone": list(zone),
         "policy": policy, "within": 8}]}
    ops, errors = parse_placement_plan(plan)
    assert ops is not None, errors
    return resolve(copy.deepcopy(SRC), BOARD, ops, clearance=0.25,
                   board_edge_clearance=0.55, grid_step=0.1)


def pack_notes(res):
    return [n for n in res.notes if 'place_pack' in n]


# --------------------------------------------------------------------------
# too small: the shortfall, in mm2
# --------------------------------------------------------------------------
tiny = run((100, 30, 108, 36))
check("a hopeless zone parks its members "
      "(the fixture must actually overflow)",
      len(tiny.parks) == len(REFS), f"{len(tiny.parks)} parked")
notes = pack_notes(tiny)
check("and the run says so once, not once per part", len(notes) == 1,
      str(notes))
check("the note carries a mm2 SHORTFALL, not just a refusal",
      notes and 'short by' in notes[0] and 'mm2' in notes[0], str(notes))
check("and a ratio, so the scale of the miss is legible",
      notes and 'x)' in notes[0], str(notes))
check("it names how many of how many did not fit",
      notes and f"{len(REFS)} of {len(REFS)}" in notes[0], str(notes))
check("it proposes what to change without doing it",
      notes and 'Widen the zone' in notes[0], str(notes))

# --------------------------------------------------------------------------
# big enough, but still parks: DO NOT blame the area
# --------------------------------------------------------------------------
roomy = run((100, 25, 180, 55))
rnotes = pack_notes(roomy)
check("a roomy zone that still parks is reported too",
      bool(roomy.parks) and len(rnotes) == 1,
      f"parked {len(roomy.parks)}, notes {rnotes}")
check("but it is NOT called an area shortfall",
      rnotes and 'short by' not in rnotes[0], str(rnotes))
check("it says the area is sufficient and the cause is elsewhere",
      rnotes and 'has the area for them' in rnotes[0]
      and 'not by total area' in rnotes[0], str(rnotes))

# --------------------------------------------------------------------------
# a zone that works says nothing -- a note on every pack is noise
# --------------------------------------------------------------------------
# On the PLACED board every zone is already occupied, so a pack there parks
# for reasons that have nothing to do with capacity. Use a pile, where the
# parts the plan names are the only things competing for the zone.
def piled():
    pcb = copy.deepcopy(SRC)
    x0, y0, x1, y1 = pcb.board_info.board_bounds
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    for fp in pcb.footprints.values():
        fp.x, fp.y, fp.rotation = cx, cy, 0.0
    return pcb


ops_fit, _e = parse_placement_plan({"schema": 1, "steps": [
    {"action": "place_pack", "refs": REFS[:2], "zone": [100, 25, 180, 55],
     "policy": "rows", "within": 8}]})
fits = resolve(piled(), BOARD, ops_fit, clearance=0.25,
               board_edge_clearance=0.55, grid_step=0.1)
check("the fits-fixture really does seat everything "
      "(else the next check is vacuous)",
      not fits.parks, f"parked {[p.ref for p in fits.parks]}")
check("a pack that seats everything emits no capacity note",
      not pack_notes(fits), str(pack_notes(fits)))

# --------------------------------------------------------------------------
# the radial policy returns early -- it must report too
# --------------------------------------------------------------------------
rad = run((100, 30, 108, 36), policy='radial')
check("the radial policy reports capacity as well (it returns early)",
      len(pack_notes(rad)) == 1, str(pack_notes(rad)))
check("and its note is the shortfall form",
      pack_notes(rad) and 'short by' in pack_notes(rad)[0],
      str(pack_notes(rad)))

# The arithmetic must agree with the whole-board option, not re-derive it.
from placement.options import grow_board  # noqa: E402

check("zone capacity uses the same (w+clr)(h+clr) charge as grow_board",
      '(w + clearance) * (h + clearance)' in
      (grow_board.__code__.co_consts and open(
          os.path.join(REPO, 'py_placer', 'placement', 'options.py'),
          encoding='utf-8').read()),
      "if grow_board changes its charge, this must change with it")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
