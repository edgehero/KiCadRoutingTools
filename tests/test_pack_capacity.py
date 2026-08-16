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


def run(zone, policy='rows', refs=None, extra_rot=None):
    step = {"action": "place_pack", "refs": refs or REFS, "zone": list(zone),
            "policy": policy, "within": 8}
    if extra_rot is not None:
        step["rot"] = extra_rot
    plan = {"schema": 1, "steps": [step]}
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
      rnotes and 'total area is not the reason' in rnotes[0]
      and 'Packing overhead' in rnotes[0], str(rnotes))
# ...and it must NOT promise that widening fixes it. Measured: the zone that
# actually seats all 8 is 2400mm2 against a stated need of 626.5 -- packing
# efficiency ~26% -- so an author who widens to the stated number still has
# parks. The note hedges instead of saying "Widen the zone".
check("the has-area branch does not promise that widening is enough",
      rnotes and 'may still not be enough' in rnotes[0], str(rnotes))

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

# --------------------------------------------------------------------------
# THE ARITHMETIC, not the wording
#
# The previous version of this file asserted only the message strings, and an
# audit showed four independent injections passing against it: summing only
# the PARKED refs, replacing (w+clr)(h+clr) with a bare w*h, zeroing the
# clearance, and DOUBLING the zone area all left it 14/14 green. The check
# named "uses the same (w+clr)(h+clr) charge as grow_board" was a one-sided
# grep of options.py -- it could not fail on any change to _zone_capacity at
# all. Parse the numbers out of the note and compare them to an independent
# computation.
import re as _re2


def note_numbers(note):
    """(usable_zone_mm2, need_mm2) as the note actually published them."""
    z = _re2.search(r'usable zone is ([\d.]+) mm2', note)
    n = _re2.search(r'need AT LEAST ([\d.]+) mm2', note)
    if n is None:
        n = _re2.search(r'for ([\d.]+) mm2 of parts', note)
    return (float(z.group(1)) if z else None,
            float(n.group(1)) if n else None)


def expected_need(pcb, refs, clearance):
    """Independent: busiest-side sum of (w+clr)(h+clr) over the NAMED refs."""
    import pose_score
    st = pose_score.make_state(pcb, BOARD, clearance=clearance,
                               board_edge_clearance=0.55, grid_step=0.1)
    per_side = {}
    for ref in refs:
        part = st.parts.get(ref)
        if part is None:
            continue
        r = part.rect(0.0, 0.0, part.rot)
        a = (r[2] - r[0] + clearance) * (r[3] - r[1] + clearance)
        side = getattr(part, 'side', None) or 'F'
        per_side[side] = per_side.get(side, 0.0) + a
    return max(per_side.values()) if per_side else 0.0


_zone = (100, 30, 108, 36)
_res = run(_zone)
_z, _n = note_numbers(pack_notes(_res)[0])
_want_need = expected_need(SRC, REFS, 0.25)
check("the published NEED equals an independent (w+clr)(h+clr) sum",
      _n is not None and abs(_n - _want_need) < 0.05,
      f"note says {_n}, independently {_want_need:.2f} -- a bare w*h gives "
      f"{expected_need(SRC, REFS, 0.0):.2f}")
check("and the clearance term is really in it",
      abs(_want_need - expected_need(SRC, REFS, 0.0)) > 1.0,
      "if these were equal, zeroing the clearance would be undetectable")
check("the published ZONE area equals the rect (nothing clipped here)",
      _z is not None and abs(_z - 48.0) < 0.05,
      f"note says {_z}, rect is 48.0")

# Summing only the PARKED refs would change the number whenever some seat.
_partial = run((100, 25, 180, 55))
_pz, _pn = note_numbers(pack_notes(_partial)[0])
_parked_only = expected_need(SRC, [p.ref for p in _partial.parks], 0.25)
check("NEED is over every ref the op named, not only the parked ones",
      _pn is not None and abs(_pn - _want_need) < 0.05
      and abs(_pn - _parked_only) > 1.0,
      f"note {_pn}, all-named {_want_need:.2f}, parked-only "
      f"{_parked_only:.2f} -- the zone must hold all of them")

# A zone hanging off the board must be CLIPPED, or "the zone has the area" is
# asserted from area the board does not offer. Measured before: 2400mm2 of
# rect against ~127mm2 of board, reported as "not by total area".
_off = run((218.52, 30.4, 298.52, 60.4))
_oz, _on = note_numbers(pack_notes(_off)[0])
check("a zone overhanging the outline is clipped to the usable board",
      _oz is not None and _oz < 400.0,
      f"note says {_oz} mm2; the raw rect is 2400.0 and the board ends at "
      f"x=223.52")
check("and it is then correctly called SHORT, not blamed on shape",
      'short by at least' in pack_notes(_off)[0],
      pack_notes(_off)[0][:150])

# A park that is NOT a capacity question must not be re-labelled as one. The
# deadline case is the worst: its own reason says "nothing was measured".
_lat = run((100, 25, 180, 55), extra_rot=45)
check("an illegal-rotation park is not reported as a capacity failure",
      not pack_notes(_lat) or 'did not fit' not in pack_notes(_lat)[0],
      f"parks {[(p.ref, p.reason[:40]) for p in _lat.parks][:2]} "
      f"notes {pack_notes(_lat)}")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
