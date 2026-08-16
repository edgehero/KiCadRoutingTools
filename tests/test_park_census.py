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
_TEN = ('R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10')
many = [{"action": "place_at", "ref": r, "at": ON_U1, "rot": 0, "within": 0.5}
        for r in _TEN]
t0 = time.time()
res4 = run(many)
dt = time.time() - t0
check("ten censused parks stay affordable", len(res4.parks) == 10 and dt < 60.0,
      f"{len(res4.parks)} parks in {dt:.1f}s")
# ...AT A BUDGET THAT IS NOT THE CHEAP ONE. `within: 0.5` is the single
# budget the window change made FASTER (3.19s -> 1.41s, the radius clamp),
# so measuring only there reported "affordable" about the one case that
# could not regress. `within: 2.0` is the worst measured ratio (5.36 ->
# 10.99, 2.05x) and is what this bound is set against.
_t0 = time.time()
_res_costly = run([{"action": "place_at", "ref": r, "at": ON_U1, "rot": 0,
                    "within": 2.0} for r in _TEN])
_dt_costly = time.time() - _t0
check("and stay affordable at the budget the change made most expensive",
      len(_res_costly.parks) == 10 and _dt_costly < 45.0,
      f"{len(_res_costly.parks)} parks in {_dt_costly:.1f}s (measured 11.0s; "
      f"the pre-change rule took 5.4s -- the extra buys a lattice the seat "
      f"search visits)")
# A wall-clock budget is NOT a guard, and this one was measured not guarding:
# injecting `max_disp=None` took the run from 6.5s to 13.1s and the check
# stayed green. The real hazard is the opposite of slowness anyway --
# CENSUS_STEP_MM is 1.0mm, so a park with `within: 0.5` had exactly ONE offset
# survive the prune and the census reported a confident all-zero for a part
# whose blocker was 0.4mm away. Pin the RESOLUTION, which is the property that
# was broken and the one a timing check cannot see.
C10 = pcb.footprints['C10']
near = run([{"action": "place_at", "ref": "R1",
             "at": [round(C10.x + 0.4, 3), round(C10.y, 3)],
             "rot": 0, "within": 0.9}])
check("the fixture parks (else the resolution check proves nothing)",
      len(near.parks) == 1 and not near.seats,
      f"seats {[s.ref for s in near.seats]}")
np_ = near.parks[0]
check("a sub-millimetre budget still finds the blocker 0.4mm away",
      np_.blockers.get('C10', 0) > 0,
      f"blockers {np_.blockers} -- at CENSUS_STEP_MM the only sampled offset "
      f"is (0,0), which reports a confident zero for every candidate")
check("and it does not report a confident all-zero census",
      any(v > 0 for v in np_.blockers.values()),
      f"censused={np_.censused} blockers={np_.blockers} -- an all-zero census "
      f"with censused=true is worse than no census")
check("and every one of them is censused",
      all(p.censused for p in res4.parks),
      str([(p.ref, p.censused) for p in res4.parks[:3]]))

# The seeder's own census must stay consistent with the plan's: same shape.
check("the plan's blockers shape matches the seeder's no_pose_blockers",
      all(isinstance(k, str) and isinstance(v, int)
          for k, v in park.blockers.items()), str(park.blockers))

# --------------------------------------------------------------------------
# 4. THE WINDOW. A census must count poses the seat search can actually
# reach, and must not build a 16mm disc to hand back 81 offsets.
# --------------------------------------------------------------------------
from placement.seeder import (CENSUS_MAX_LOCATIONS, SEARCH_FINE_STEP_MM,
                              SEARCH_RADIUS_MM, census_window)
from pose_score import _offsets

# The floor a census must reach before it is allowed to truncate. Stated as
# a literal so a change that quietly shrinks the window shows up here: an
# injected `min(radius, 4.0)` -- the same bug class as the fixed 16mm this
# replaced, in the other direction -- passed every check in this file.
MIN_UNTRUNCATED_MM = 6.0

_off_lattice, _short, _counts, _grids = [], [], [], (0.05, 0.1, 0.2, 0.25, 0.3)
for _g in _grids:
    _allowed = {_g, SEARCH_FINE_STEP_MM} if _g <= SEARCH_FINE_STEP_MM else {_g}
    for _w in (0.05, 0.2, 0.3, 0.5, 0.8, 0.9, 1.2, 1.5, 2.0, 2.4, 3.0, 3.9,
               5.0, 5.99, 6.0, 6.05, 8.0, 12.0, 30.0, 200.0, 500.0):
        _r, _s = census_window(_w, _g)
        # EXACT membership, not "a multiple of 0.1": an injected step of 0.3
        # is a multiple of 0.1 and lands on no ring _try_place sweeps past
        # SEARCH_XFINE_RADIUS_MM.
        if _s not in _allowed:
            _off_lattice.append((_g, _w, _s))
        # Lower bound. Without it a window that truncates every budget is
        # invisible -- the old check only tested that the radius was not too
        # LARGE, which is half a contract.
        if _r < min(_w, MIN_UNTRUNCATED_MM) - 1e-9:
            _short.append((_g, _w, _r))
        _counts.append((_g, _w, _s, _r, len(_offsets(_r, _s))))

check("the census step is always a lattice _try_place searches, exactly",
      not _off_lattice,
      f"{_off_lattice[:4]} -- `within/8` gave 0.1125 at 0.9 and 0.1875 at "
      f"1.5, so a park could report poses the retry can never find")
check("the census never renders a verdict on the 1.0mm ring",
      all(s <= max(SEARCH_FINE_STEP_MM, g) + 1e-9
          for g, _w, s, _r, _n in _counts),
      str([(g, w, s) for g, w, s, _r, _n in _counts
           if s > max(SEARCH_FINE_STEP_MM, g) + 1e-9][:4]))
check(f"and it looks at least {MIN_UNTRUNCATED_MM}mm out before truncating",
      not _short,
      f"{_short[:4]} -- a silently shrunk window is the same confident-zero "
      f"failure as a coarse one")
check("the sweep is BOUNDED for every budget, including absurd ones",
      max(n for *_x, n in _counts) <= CENSUS_MAX_LOCATIONS,
      f"worst {max(n for *_x, n in _counts)} vs cap {CENSUS_MAX_LOCATIONS} -- "
      f"an unclamped radius built 1,002,001 offsets (~72MB) at within=500")
check("the radius never exceeds what _try_place will even visit",
      all(r <= SEARCH_RADIUS_MM + 1e-9 for *_x, r, _n in
          [(g, w, s, r, n) for g, w, s, r, n in _counts]),
      str([(w, r) for _g, w, _s, r, _n in _counts
           if r > SEARCH_RADIUS_MM][:3]))
check("and the pinned defaults still apply when there is no budget",
      census_window(None, 0.1) == (16.0, 1.0), str(census_window(None, 0.1)))
check("a budget finer than the grid cannot ask for a sub-grid lattice",
      census_window(0.05, 0.1)[1] >= 0.1, str(census_window(0.05, 0.1)))

# A plan can carry `Infinity` (json.loads accepts it) and plan_ops only
# checks `within > 0`. `math.ceil(inf)` raised OverflowError straight out of
# op_place_lift, which has no census guard -- so this crashed resolve().
_hostile = {}
for _bad in (float('inf'), float('nan'), -1.0, 0.0, 1e9):
    try:
        _hostile[str(_bad)] = census_window(_bad, 0.1)
    except Exception as _e:                                  # noqa: BLE001
        _hostile[str(_bad)] = f'RAISED {type(_e).__name__}'
check("a hostile `within` returns a window instead of raising",
      all(isinstance(v, tuple) for v in _hostile.values()), str(_hostile))
check("and inf is clamped to something finite and bounded",
      isinstance(_hostile['inf'], tuple)
      and _hostile['inf'][0] <= SEARCH_RADIUS_MM, str(_hostile['inf']))

# --------------------------------------------------------------------------
# 5. ONE PARK, ONE MEASUREMENT.
#
# `op_place_lift` censused at the default 1.0mm while `_census` censused at
# the scaled step, and then each wrote a DIFFERENT SUBSET of the same Park:
# `blockers` from before the lift at 1.0mm, `baseline_poses` and the reason
# sentence from after it at 0.1mm -- naming a part the op had never been
# asked about. Measured on this fixture, the reason read
#   "...; lifting U1 would free 64 pose(s) ... -- and lifting C7 frees no
#    pose either, so they are not what is in the way"
# with blockers {'C7': 0}: two contradictory sentences and no entry backing
# the first.
# --------------------------------------------------------------------------
C7 = pcb.footprints['C7']
lift = run([{"action": "place_at", "ref": "C7",
             "at": [round(C7.x, 3), round(C7.y, 3)], "rot": 0, "within": 1.0},
            {"action": "place_at", "ref": "R1", "at": ON_U1,
             "rot": 0, "within": 0.5},
            {"action": "place_lift", "refs": ["C7"], "for": ["R1"],
             "within": 2.0}])
lp = [p for p in lift.parks if p.action == 'place_lift' and p.ref == 'R1']
check("the lift fixture parks R1 (else there is no record to check)",
      len(lp) == 1, str([(p.ref, p.action) for p in lift.parks]))
if lp:
    p0 = lp[0]
    check("place_lift's park is censused at a REPORTED step",
          p0.censused and p0.census_step_mm in (0.1, SEARCH_FINE_STEP_MM),
          f"censused={p0.censused} step={p0.census_step_mm}")
    check("and it censused at the retry budget's resolution, not 1.0mm",
          p0.census_step_mm == 0.1,
          f"{p0.census_step_mm} -- the retry budget is 0.5mm, at which "
          f"CENSUS_STEP_MM leaves only the (0,0) offset")
    check("every blocker the reason names has an entry in `blockers`",
          all(b in p0.blockers for b in ('C7',) if b in p0.reason),
          f"reason={p0.reason!r} blockers={p0.blockers}")
    # The contradiction, stated as its own check: the reason must not quote
    # a pose count that no `blockers` entry and no `baseline_poses` backs.
    import re as _re
    quoted = {int(n) for n in _re.findall(r'(\d+) pose\(s\)', p0.reason)}
    known = set(p0.blockers.values()) | {p0.baseline_poses or 0}
    check("and every pose count in the reason comes from THIS measurement",
          quoted <= known,
          f"reason quotes {sorted(quoted - known)} which appears in neither "
          f"blockers={p0.blockers} nor baseline_poses={p0.baseline_poses}")
    check("the park names only blockers this op was asked about",
          set(p0.blockers) <= {'C7'},
          f"{sorted(p0.blockers)} -- anything else came from a census taken "
          f"AFTER the lift, when `pending` held different parts")

# A successful lift must report the poses its own lift actually freed. At
# CENSUS_STEP_MM this said "0 before, 0 with C10 lifted" about a lift that
# demonstrably worked -- the record contradicting the outcome.
ok_lift = run([{"action": "place_at", "ref": "C10",
                "at": [round(C10.x, 3), round(C10.y, 3)],
                "rot": 0, "within": 0.6},
               {"action": "place_at", "ref": "R1",
                "at": [round(C10.x + 0.4, 3), round(C10.y, 3)],
                "rot": 0, "within": 0.5},
               {"action": "place_lift", "refs": ["C10"], "for": ["R1"],
                "within": 3.0}])
note = next((n for n in ok_lift.notes if 'seated after lifting' in n), '')
check("a lift that worked says so (the fixture seats R1)",
      'R1' in [s.ref for s in ok_lift.seats] and note,
      f"seats={[s.ref for s in ok_lift.seats]} note={note!r}")
_freed = _re.search(r'(\d+) with C10 lifted', note)
# `> 4`, NOT `> 0`. The retry budget here is 0.5mm, so at the old default
# 1.0mm step exactly ONE offset -- (0,0) -- survives the max_disp prune, and
# four rotations of it is the ceiling. Any count above 4 is proof that a
# FINER lattice was actually swept, which `> 0` was not: an injection that
# REPORTED census_window's step while USING CENSUS_STEP_MM kept every
# step-reporting check green, and this was the only red.
check("and reports a count only a finer lattice could have produced",
      _freed and int(_freed.group(1)) > 4,
      f"{note!r} -- at CENSUS_STEP_MM only the (0,0) offset survives a 0.5mm "
      f"budget, so 4 is the ceiling there; this read '0 with C10 lifted' "
      f"about a lift that had just succeeded")
check("and discloses the step those counts were taken at",
      'mm:' in note, note)

# --------------------------------------------------------------------------
# 6. THE SENTENCE THAT CARRIES THE STEP TO A HUMAN. `stamp`'s improving
# branch -- "lifting X would take it from N to M pose(s) (measured at Smm,
# before the lift)" -- executed ZERO times across the whole suite, so the
# only place the step reaches a `place_plan` reader was untested.
# --------------------------------------------------------------------------
imp = run([{"action": "place_at", "ref": "C10",
            "at": [round(C10.x, 3), round(C10.y, 3)], "rot": 0,
            "within": 0.6},
           {"action": "place_at", "ref": "R1", "at": ON_U1,
            "rot": 0, "within": 0.5},
           {"action": "place_lift", "refs": ["C10"], "for": ["R1"],
            "within": 2.0}])
ip = [p for p in imp.parks if p.action == 'place_lift' and p.ref == 'R1']
check("the improving-branch fixture parks R1", len(ip) == 1,
      str([(p.ref, p.action) for p in imp.parks]))
if ip:
    _p = ip[0]
    check("a park that names a count states the step it was measured at",
          ('pose(s)' not in _p.reason) or ('mm' in _p.reason),
          f"{_p.reason!r} -- a bare count is the '253 at 0.1mm vs 113 at "
          f"0.25mm is not a decrease' confusion this field exists to stop")
    _q2 = {int(n) for n in _re.findall(r'(\d+) pose\(s\)', _p.reason)}
    check("and every count it names is one of ITS OWN numbers",
          _q2 <= (set(_p.blockers.values()) | {_p.baseline_poses or 0}),
          f"reason quotes {sorted(_q2)}, blockers={_p.blockers}, "
          f"baseline={_p.baseline_poses}")
    check("the census window is reported in full, radius as well as step",
          _p.census_step_mm is not None and _p.census_radius_mm is not None,
          str(_p.to_dict()))

# `census_parks=False` turns OFF the automatic census on ordinary parks; it
# does NOT disable place_lift, which is an explicit request to measure. That
# also gives the rollback path an UNCENSUSED park to fill -- without one,
# deleting rollback's whole stamping loop changed nothing observable.
rb2 = run([{"action": "place_at", "ref": "C10",
            "at": [round(C10.x, 3), round(C10.y, 3)], "rot": 0, "within": 0.6},
           {"action": "place_at", "ref": "R1",
            "at": [round(C10.x, 3), round(C10.y, 3)], "rot": 0, "within": 0.5},
           {"action": "place_lift", "refs": ["C10"], "for": ["R1"],
            "within": 0.1}], census_parks=False)
check("the census_parks=False fixture still reverts",
      any('REVERTED' in n for n in rb2.notes), str([n[:50] for n in rb2.notes]))
_r2 = next((p for p in rb2.parks if p.ref == 'R1'), None)
check("with the automatic census off, place_lift still measures",
      _r2 is not None and _r2.censused and bool(_r2.blockers),
      str(_r2.to_dict() if _r2 else None))
if _r2 is not None:
    check("and the reverted park carries that measurement whole",
          _r2.baseline_poses is not None and _r2.census_step_mm is not None,
          str(_r2.to_dict()))

# The ROLLBACK path is the other place a park gets stamped, and there the
# restored park is the EARLIER op's -- already censused by `_census`, with a
# reason sentence quoting its own numbers. Overwriting its `blockers` and
# leaving that sentence is the same contradiction from the other direction,
# so a park that already carries a census must be left whole.
rb = run([{"action": "place_at", "ref": "C10",
           "at": [round(C10.x, 3), round(C10.y, 3)], "rot": 0, "within": 0.6},
          {"action": "place_at", "ref": "R1",
           "at": [round(C10.x, 3), round(C10.y, 3)], "rot": 0, "within": 0.5},
          {"action": "place_lift", "refs": ["C10"], "for": ["R1"],
           "within": 0.1}])
check("the rollback fixture really reverts (else it proves nothing)",
      any('REVERTED' in n for n in rb.notes),
      str([n[:60] for n in rb.notes]))
r1 = next((p for p in rb.parks if p.ref == 'R1'), None)
check("the reverted park still carries a census", r1 is not None
      and r1.censused, str(r1.to_dict() if r1 else None))
if r1 is not None:
    check("and it is the park's OWN census, not the lift's stamped over it",
          r1.action == 'place_at' and len(r1.blockers) > 1,
          f"action={r1.action} blockers={r1.blockers} -- the lift censuses "
          f"only the refs it was given ({{'C10'}}), so a single-entry "
          f"blockers here means it overwrote the earlier measurement while "
          f"leaving that measurement's reason sentence in place")
    _q = {int(n) for n in _re.findall(r'(\d+) pose\(s\)', r1.reason)}
    check("so the reverted park's reason still matches its own numbers",
          _q <= (set(r1.blockers.values()) | {r1.baseline_poses or 0}),
          f"reason quotes {sorted(_q)}, blockers={r1.blockers}, "
          f"baseline={r1.baseline_poses}")

# --------------------------------------------------------------------------
# 7. THE ZONE. `count_legal_poses` had no constraint while `_try_place`
# filtered every candidate through `_in_zone`, so a zone-constrained park was
# censused over the open board. Measured on this fixture before the fix:
# three parts packed into a 2x2mm zone parked, and one came back
#   baseline_poses: 64, blockers {U1..J8: all 64}
# -- "64 legal poses with nothing lifted", about a part the same op had just
# refused to seat. The other two advised lifting U1 when the zone was the
# problem. The op's own capacity note was correct at the same time ("the
# usable zone is 4.0 mm2 and these parts need AT LEAST 16.5 mm2"), so one
# result object carried a right diagnosis and a wrong one.
# --------------------------------------------------------------------------
import math

from placement import seeder
from placement.seeder import _try_place, zone_census_offsets, zone_gate
from pose_score import make_state

U1fp = pcb.footprints['U1']
ZONE = [round(U1fp.x - 1.0, 3), round(U1fp.y - 1.0, 3),
        round(U1fp.x + 1.0, 3), round(U1fp.y + 1.0, 3)]
zres = run([{"action": "place_pack", "refs": ["R1", "R2", "R3"],
             "zone": ZONE, "policy": "rows", "within": 3.0}])
zparks = [p for p in zres.parks if p.action == 'place_pack']
check("the zone fixture parks all three members",
      len(zparks) == 3 and not zres.seats,
      f"{len(zparks)} parks, seats {[s.ref for s in zres.seats]}")

# --- THE INVARIANT. Phrased as "a park means the seat found nothing", not
# as "the zone is respected", so no partial fix can satisfy it by moving the
# error somewhere else: a positive baseline at the same target, budget,
# rotations and predicate the seat used is a contradiction whatever caused
# it. Deadline / locked / rotation-lattice parks are already censused=False.
bad_base = [(p.ref, p.baseline_poses) for p in zres.parks
            if p.censused and p.baseline_poses]
check("every censused geometric park reports baseline_poses == 0",
      not bad_base,
      f"{bad_base} -- a park says the seat found nothing; a positive "
      f"baseline in the same record says it found plenty")

# --- The zone must be ON the record, or the counts are unreadable and
# place_lift cannot reconstruct the constraint it has to satisfy.
check("a zone-constrained park carries its zone and tolerance",
      all(p.constraint is not None and p.tol is not None for p in zparks),
      str([(p.ref, p.constraint, p.tol) for p in zparks]))
check("and says so in the reason, so counts are not read as board-wide",
      all('INSIDE the zone' in p.reason for p in zparks),
      str([p.reason[-90:] for p in zparks[:1]]))

# --- INDEPENDENT RECOUNT. Re-derived here from `_try_place`'s own two
# branches rather than by calling the function under test, and compared to
# every published number. Same discipline test_pack_capacity uses after four
# injections passed a string-only check.
def recount(ref, tx, ty, excl, zone, tol, step):
    """An INDEPENDENT restatement of what a zone census must count.

    It calls neither `zone_census_offsets` nor `zone_gate`: the containment
    rule, the anchor relaxation and the two-lattice sample set are all
    written out longhand here. That matters -- the earlier version of this
    helper called both functions under test, so an error inside either was
    reproduced identically on both sides and the check agreed with it. Two
    real bugs sailed past it that way (a max-half-extent box that dropped
    the pose the search seats, and a silently truncated sample set).
    """
    part = zres_state.parts[ref]
    rots = [part.rot] + [(part.rot + d) % 360 for d in (90.0, 180.0, 270.0)]
    z0, z1, z2, z3 = (float(v) for v in zone)

    # anchor relaxation, longhand: does the tol-inflated zone hold the
    # courtyard at 0 or 90 degrees?
    zw, zh = (z2 - z0) + 2 * tol, (z3 - z1) + 2 * tol
    anchor = True
    for r in (part.rot % 360, (part.rot + 90) % 360):
        b = part.rect(0.0, 0.0, r)
        w, h = b[2] - b[0], b[3] - b[1]
        if (w <= zw + 1e-9 and h <= zh + 1e-9) or \
           (h <= zw + 1e-9 and w <= zh + 1e-9):
            anchor = False

    def contained(x, y, rot):
        if anchor:
            return z0 - tol <= x <= z2 + tol and z1 - tol <= y <= z3 + tol
        b = part.rect(x, y, rot)
        return (z0 - tol <= b[0] and b[2] <= z2 + tol
                and z1 - tol <= b[1] and b[3] <= z3 + tol)

    # the sample set _try_place visits, longhand: grid out to 4mm, then
    # 0.25 out to the budget.
    pts, seen = [], set()
    for st_, rmax in ((0.1, min(3.0, 4.0)), (0.25, 3.0)):
        k = int(3.0 / st_) + 1
        for i in range(-k, k + 1):
            for j in range(-k, k + 1):
                dx, dy = round(i * st_, 6), round(j * st_, 6)
                if math.hypot(dx, dy) > rmax + 1e-9:
                    continue
                if (dx, dy) not in seen:
                    seen.add((dx, dy))
                    pts.append((dx, dy))
    pts.sort(key=lambda d: d[0] * d[0] + d[1] * d[1])
    n = 0
    for dx, dy in pts:
        x, y = round(tx + dx, 3), round(ty + dy, 3)
        for rot in rots:
            if not contained(x, y, rot):
                continue
            if seeder.pose_ok(zres_state, ref, x, y, rot, excl, ()):
                n += 1
                if n >= seeder.CENSUS_CAP:
                    return n
    return n


zres_state = make_state(pcb, BOARD, clearance=0.25,
                        board_edge_clearance=0.55, grid_step=0.1)
mismatch, ground = [], []
# The resolver excludes every part the PLAN may move (`self.pending`), not
# just the one being seated -- an unseated sibling is not an obstacle. The
# recount has to mirror that or it measures a different board and the
# comparison is meaningless rather than failing.
PLAN_MOVABLE = {'R1', 'R2', 'R3'}
for p in zparks:
    tx, ty = p.target
    for b, n in p.blockers.items():
        want = recount(p.ref, tx, ty, (PLAN_MOVABLE - {p.ref}) | {b},
                       p.constraint, p.tol, p.census_step_mm)
        if want != n:
            mismatch.append((p.ref, b, n, want))
        # GROUND TRUTH: if the seat search really seats with `b` lifted, the
        # census must not report zero. This is the assertion that rejects
        # "thread the constraint but keep the disc window" -- under that,
        # R1/R2/R3 all censused 0 while _try_place seated.
        seats = _try_place(zres_state, p.ref, tx, ty,
                           (PLAN_MOVABLE - {p.ref}) | {b},
                           constraint=tuple(p.constraint), tol=p.tol,
                           max_disp=3.0) is not None
        # BIDIRECTIONAL. `seats and n == 0` is the confident zero; the other
        # direction is the phantom -- a count of poses the retry can never
        # collect, which is what sampling a lattice the search does not visit
        # produces. One direction alone let a whole class through.
        if seats != (n > 0):
            ground.append((p.ref, b, n, 'seats' if seats else 'no seat'))
check("every published blocker count survives an independent recount",
      not mismatch, str(mismatch[:4]))
check("and no blocker reads 0 where the seat search actually seats",
      not ground,
      f"{ground} -- the census would be telling the author that lifting a "
      f"part which demonstrably works frees nothing")
check("the fixture has a blocker that DOES free poses (else the above is "
      "free)", any(v > 0 for p in zparks for v in p.blockers.values()),
      str([p.blockers for p in zparks]))

# --- ANTI-MIRROR GUARD. `_try_place` relaxes a zone too small to hold the
# courtyard to anchor-point-in-zone. A census that mirrors only the strict
# branch under-counts exactly there: C1 into a 0.4mm zone censuses 0 with the
# strict rule and seats anyway. This is the guard AGAINST the fix, and it is
# the one a naive patch trips.
C1 = pcb.footprints['C1']
Z04 = (round(C1.x - 0.2, 3), round(C1.y - 0.2, 3),
       round(C1.x + 0.2, 3), round(C1.y + 0.2, 3))
_gate, _anchor = zone_gate(zres_state.parts['C1'], Z04, 0.5)
check("the anchor fixture really is an anchor zone (else it proves nothing)",
      _anchor, "zone_fits_courtyard said the courtyard fits a 0.4mm zone")
c1_seats = _try_place(zres_state, 'C1', C1.x, C1.y, {'C1'},
                      constraint=Z04, tol=0.5, max_disp=1.0) is not None
c1_census = seeder.count_legal_poses(zres_state, 'C1', C1.x, C1.y, {'C1'},
                                     max_disp=1.0, constraint=Z04, tol=0.5)
check("a zone too small for the courtyard censuses > 0 where it seats",
      c1_seats and c1_census > 0,
      f"seats={c1_seats} census={c1_census} -- the strict containment rule "
      f"alone gives 0 here, which is a confident zero on a pose the search "
      f"takes")

# --- THE RETRY KEEPS THE ZONE. The correctness half: `op_place_lift` re-seats
# a part an earlier op parked, and with no zone on the record it retried
# unconstrained -- measured, R1 was written 3.86mm outside the zone
# place_pack gave it and the run reported a SEAT, with a note crediting a
# lift that had freed nothing (64 poses before, 64 after).
C7 = pcb.footprints['C7']
esc = run([{"action": "place_at", "ref": "C7",
            "at": [round(C7.x, 3), round(C7.y, 3)], "rot": 0, "within": 1.0},
           {"action": "place_pack", "refs": ["R1"], "zone": ZONE,
            "policy": "rows", "within": 8.0},
           {"action": "place_lift", "refs": ["C7"], "for": ["R1"],
            "within": 8.0}])
outside = []
for s in esc.seats:
    if s.ref != 'R1':
        continue
    if not (ZONE[0] - 0.5 <= s.pose[0] <= ZONE[2] + 0.5
            and ZONE[1] - 0.5 <= s.pose[1] <= ZONE[3] + 0.5):
        outside.append((s.action, s.pose))
check("a lift retry never seats a zone-constrained part outside its zone",
      not outside,
      f"{outside} vs zone {ZONE} -- a seat that satisfies the plan by "
      f"dropping the plan's own constraint is a wrong board, not a result")
check("the lift fixture reaches the retry (else the check above is free)",
      any(p.ref == 'R1' and p.action == 'place_lift' for p in esc.parks)
      or any(s.ref == 'R1' and s.action == 'place_lift' for s in esc.seats),
      str([(p.ref, p.action) for p in esc.parks]
          + [(s.ref, s.action) for s in esc.seats]))

# --------------------------------------------------------------------------
# 8. THE ZONE OFFSET GENERATOR gets the same invariants `census_window` has.
# It was exempt from all four and violated three: it could pick the 1.0mm
# ring (the verdict census_window refuses to render), sample at 0.1mm past
# 4mm where the search only reaches 0.25mm, and materialise a 4,004,001-entry
# list for a hostile zone -- ten times per park, uncached.
# --------------------------------------------------------------------------
from placement.seeder import (SEARCH_FINE_RADIUS_MM, SEARCH_XFINE_RADIUS_MM,
                              _feasible_centre_box)

zpart = zres_state.parts['R1']
bad_step, bad_far, bad_big, bad_reach = [], [], [], []
far_seen = 0
# OFFSET zones as well as centred ones. With the zone centred on the target
# the location cap truncates at ~2.7mm, so the far branch is never reached
# and an injection that sampled 0.1mm everywhere passed every check here.
for zs in (0.4, 2.0, 8.0, 12.5, 20.0, 60.0, 400.0, 2000.0):
    for md in (None, 0.5, 3.0, 20.0):
      for ox, oy in ((0.0, 0.0), (10.0, 0.0), (0.0, 7.0), (9.0, 9.0)):
        z = (100.0 + ox - zs / 2, 50.0 + oy - zs / 2,
             100.0 + ox + zs / 2, 50.0 + oy + zs / 2)
        stp, offs, rch = zone_census_offsets(zpart, z, 0.5, 100.0, 50.0,
                                             0.1, md)
        far_seen += sum(1 for d in offs
                        if math.hypot(*d) > SEARCH_XFINE_RADIUS_MM)
        if stp not in (0.1, 0.25):
            bad_step.append((zs, md, stp))
        if len(offs) > seeder.CENSUS_MAX_LOCATIONS:
            bad_big.append((zs, md, len(offs)))
        for dx, dy in offs:
            d = math.hypot(dx, dy)
            # Past the x-fine ring the search only visits 0.25; anything
            # finer out there is a pose the retry cannot collect.
            if d > SEARCH_XFINE_RADIUS_MM + 1e-9:
                if abs(round(dx / 0.25) * 0.25 - dx) > 1e-6 or \
                   abs(round(dy / 0.25) * 0.25 - dy) > 1e-6:
                    bad_far.append((zs, md, dx, dy))
            if d > SEARCH_FINE_RADIUS_MM + 1e-9:
                bad_reach.append((zs, md, round(d, 3)))

check("the sweep actually reaches past the x-fine ring (else the far-lattice "
      "check below is free)", far_seen > 0,
      f"{far_seen} offset(s) past {SEARCH_XFINE_RADIUS_MM}mm -- with only "
      f"target-centred zones the cap truncates first and nothing gets there")
check("the zone census never renders a verdict on the 1.0mm ring",
      not bad_step, str(bad_step[:4]))
check("and never samples finer than the search reaches at that distance",
      not bad_far,
      f"{bad_far[:3]} -- past {SEARCH_XFINE_RADIUS_MM}mm _try_place visits "
      f"only the 0.25 lattice, so a finer offset out there is a pose the "
      f"retry can never collect")
check("and never counts past what the search will even visit",
      not bad_reach, str(bad_reach[:3]))
check("and is BOUNDED for any zone, including absurd ones",
      not bad_big,
      f"{bad_big[:3]} -- a 2000mm zone built a 4,004,001-entry list, ten "
      f"times per park")

# The box is the ALGEBRA, not a symmetric bound: the courtyard is not
# centred on the footprint origin for 17 of 65 parts here, and a symmetric
# half-extent deflation shifts the box off the poses that actually seat.
offc = [r for r, pt in zres_state.parts.items()
        if abs(sum(pt.rect(0.0, 0.0, pt.rot)[0::2]) / 2.0) > 1e-6
        or abs(sum(pt.rect(0.0, 0.0, pt.rot)[1::2]) / 2.0) > 1e-6]
check("the fixture HAS off-centre courtyards (else the box check is free)",
      len(offc) >= 5, f"{len(offc)} part(s): {sorted(offc)[:6]}")
shifted = []
for ref in sorted(offc)[:8]:
    pt = zres_state.parts[ref]
    fp = pcb.footprints[ref]
    r = pt.rect(fp.x, fp.y, pt.rot)
    z = (round(r[0], 3), round(r[1], 3), round(r[2], 3), round(r[3], 3))
    lo_x, lo_y, hi_x, hi_y = _feasible_centre_box(pt, z, 0.5, False)
    # the part's OWN pose must be feasible for a zone that is its own
    # courtyard bbox -- if the box says otherwise it has been shifted
    if not (lo_x - 1e-6 <= fp.x <= hi_x + 1e-6
            and lo_y - 1e-6 <= fp.y <= hi_y + 1e-6):
        shifted.append((ref, (round(lo_x, 3), round(hi_x, 3)),
                        round(fp.x, 3)))
check("an off-centre part's own pose is inside its own feasible box",
      not shifted,
      f"{shifted[:3]} -- a symmetric half-extent deflation shifts the box, "
      f"and J18/J19/J20 then censused 0 while _try_place seated them at "
      f"full clearance")

# --------------------------------------------------------------------------
# 9. THE OTHER TWO ESCAPE ROUTES. Fixing the retry was not enough: a park
# that carried a target but NO constraint (the rotation-lattice and deadline
# branches never set one) put `None` on the record, and `parked_at` kept the
# FIRST park -- so an unconstrained earlier park outranked the later op that
# demanded a zone, and the retry ran unconstrained anyway.
# --------------------------------------------------------------------------
esc2 = run([{"action": "place_at", "ref": "R1", "at": ON_U1, "rot": 45,
             "within": 8.0},
            {"action": "place_at", "ref": "C7",
             "at": [round(C7.x, 3), round(C7.y, 3)], "rot": 0, "within": 1.0},
            {"action": "place_pack", "refs": ["R1"], "zone": ZONE,
             "policy": "rows", "within": 8.0},
            {"action": "place_lift", "refs": ["C7"], "for": ["R1"],
             "within": 8.0}])
out2 = [(s.action, s.pose) for s in esc2.seats if s.ref == 'R1'
        and not (ZONE[0] - 0.5 <= s.pose[0] <= ZONE[2] + 0.5
                 and ZONE[1] - 0.5 <= s.pose[1] <= ZONE[3] + 0.5)]
check("an earlier UNCONSTRAINED park cannot outrank a later zoned one",
      not out2,
      f"{out2} vs zone {ZONE} -- first-wins in `parked_at` was bookkeeping "
      f"until the tuple carried a constraint; then it silently chose the "
      f"weaker demand and the seat escaped by 4.5mm")
check("the rot-45 fixture really parks R1 first (else the above is free)",
      any(p.ref == 'R1' for p in esc2.parks)
      or any(s.ref == 'R1' for s in esc2.seats),
      str([(p.ref, p.action) for p in esc2.parks]))

# The rotation-lattice branch returns BEFORE the ordinary park is built, so
# it needs its own constraint or a zoned pack that asks for an off-lattice
# angle leaves `parked_at` with no zone at all -- and then the retry escapes
# even with `parked_at`'s upgrade rule in place.
# Inspected WITHOUT the lift: `place_lift` supersedes the park it retried
# (`p.ref == ref and p.step != step` are dropped), so the lattice park is
# gone from the result by the time the full plan finishes.
lat = run([{"action": "place_pack", "refs": ["R1"], "zone": ZONE,
            "policy": "rows", "rot": 45, "within": 8.0}])
r1p = [p for p in lat.parks if p.ref == 'R1']
check("a zoned pack at an off-lattice angle parks via the lattice branch",
      any('legality lattice' in p.reason for p in r1p),
      str([p.reason[:70] for p in r1p]))
check("and that park carries the zone, so the retry cannot escape through it",
      all(p.constraint is not None for p in r1p
          if 'legality lattice' in p.reason),
      str([(p.reason[:40], p.constraint) for p in r1p]))

esc3 = run([{"action": "place_at", "ref": "C7",
             "at": [round(C7.x, 3), round(C7.y, 3)], "rot": 0, "within": 1.0},
            {"action": "place_pack", "refs": ["R1"], "zone": ZONE,
             "policy": "rows", "rot": 45, "within": 8.0},
            {"action": "place_lift", "refs": ["C7"], "for": ["R1"],
             "within": 8.0}])
out3 = [(s.action, s.pose) for s in esc3.seats if s.ref == 'R1'
        and not (ZONE[0] - 0.5 <= s.pose[0] <= ZONE[2] + 0.5
                 and ZONE[1] - 0.5 <= s.pose[1] <= ZONE[3] + 0.5)]
check("so no lift retry escapes via a rotation-lattice park either",
      not out3, f"{out3} vs zone {ZONE}")

# --------------------------------------------------------------------------
# 10. `_evict_candidates` under a zone. Reverting its whole hunk left the
# suite green, so the widened box and the zone-centred ranking were untested.
# --------------------------------------------------------------------------
far_zone = (ZONE[0] - 12.0, ZONE[1], ZONE[2] - 12.0, ZONE[3])
placed_refs = {r for r in zres_state.parts} - PLAN_MOVABLE
near = seeder._evict_candidates(zres_state, 'R1', ON_U1[0], ON_U1[1],
                                placed_refs, set(),
                                constraint=far_zone, tol=0.5)
plain = seeder._evict_candidates(zres_state, 'R1', ON_U1[0], ON_U1[1],
                                 placed_refs, set())
check("a far zone changes which blockers are considered at all",
      set(near) != set(plain),
      f"zone-aware {sorted(near)} vs target-only {sorted(plain)} -- if these "
      f"match, the zone is not reaching _evict_candidates")
zc = [(zres_state.parts[b].x, zres_state.parts[b].y) for b in near]
mid = ((far_zone[0] + far_zone[2]) / 2.0, (far_zone[1] + far_zone[3]) / 2.0)
check("and the candidates it picks sit nearer the ZONE than the target's do",
      zc and (sum(math.hypot(x - mid[0], y - mid[1]) for x, y in zc) / len(zc))
      < (sum(math.hypot(zres_state.parts[b].x - mid[0],
                        zres_state.parts[b].y - mid[1])
             for b in plain) / max(1, len(plain))),
      f"zone-ranked {sorted(near)} vs {sorted(plain)}")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
