#!/usr/bin/env python3
"""The via annular ring: a relation nothing in this repo graded.

Run 20 delivered a board carrying three vias at 0.3 mm diameter / 0.3 mm drill --
a ZERO annular ring, a hole with no barrel land -- against the board's own
declared `min_via_annular_width: 0.05`, and every instrument called it clean.
`check_drc` and `board_score` test diameter >= floor and drill >= floor
SEPARATELY; the relation `(dia - drill)/2` was tested by nobody.

The producer was named too: `net_rescue._escalation_ladder` builds its via rungs
straight from `fab_floor_ladder()`, and the run's own `--fab-overrides` declared
`via_diameter = 0.3` and `via_drill = 0.3` together, so the single rung WAS
(0.3, 0.3). `parse_fab_overrides` validated only `> 0` per key.

This file covers the producer-side guard. Two things it must get right, and both
were got wrong once during implementation:

  * the TRIGGER is a ring at or below zero (or below an annular the user actually
    declared) -- NOT merely a small ring. `via_drill = 0.18` overlaid on the
    advanced tier leaves 0.035 mm, which is positive and manufacturable, and
    raising via_diameter there would silently change a key the user never listed.
    `tests/test_fab_tiers.py` pins that overlay contract and caught the mistake.
  * the built-in tiers must be UNTOUCHED. Every one of them ships a via pair
    whose ring is below its own declared `annular` (4-layer standard is
    (0.45-0.20)/2 = 0.125 against a declared 0.20) because the pair is the
    absolute minimum while the key is the comfortable one. Enforcing the key
    against the table would resize every default run's vias.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fab_tiers as FT  # noqa: E402

passed = failed = 0


def check(label, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  OK   {label}')
    else:
        failed += 1
        print(f'  FAIL {label} -- {detail}')


def overrides(text, name):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return FT.parse_fab_overrides(p)


print('--- the run-20 override file, and its neighbours ---')

# The exact shape run 20 shipped: both via keys, equal, no annular declared.
ov = overrides('via_diameter = 0.3\nvia_drill = 0.3\n', 'run20.txt')
check('a zero-ring via pair is pinned, not accepted',
      ov['via_diameter'] > ov['via_drill'],
      f"{ov} -- this is the pair that shipped three unmanufacturable vias")
check('and it is pinned to a ring the repo actually ships, not an epsilon',
      abs(ov['via_diameter'] - 0.4) < 1e-9,
      f"{ov['via_diameter']} -- a nanometre ring satisfies '> 0' and no fab")

# A declared `annular` is a DECLARATION TO GRADE, never a silent resize. This
# whole block is the regression guard for a real defect in the first version of
# this guard: `fab_overrides.example.txt` prints the tiers' annular values as a
# reference table, so a user copying one back in had the via they had just asked
# for inflated -- 0.25 became 0.45, LARGER than the standard tier, from a file
# requesting something tighter. Measured then: 32 of 56 combinations changed.
ov = overrides('via_diameter = 0.25\nvia_drill = 0.15\nannular = 0.15\n', 'refcopy.txt')
check('a declared annular copied from the file\'s OWN reference table does not '
      'resize the via the file asked for',
      abs(ov['via_diameter'] - 0.25) < 1e-9,
      f"{ov} -- the user asked for the advanced 0.25 via and must keep it")

lad = FT.fab_floor_ladder(4, tier='standard', overrides={'annular': 0.20})[0]
check('a lone `annular` line does not move the tier\'s via either',
      abs(lad['via_diameter'] - 0.45) < 1e-9,
      f"{lad['via_diameter']} -- 4L standard must stay 0.45, not become 0.60")

ov = overrides('via_diameter = 0.6\nvia_drill = 0.3\nannular = 5.0\n', 'absurd.txt')
check('an absurd declared annular inflates nothing (no 10.3mm via)',
      abs(ov['via_diameter'] - 0.6) < 1e-9, str(ov))

ov = overrides('via_diameter = 0.2\nvia_drill = 0.3\n', 'negative.txt')
check('a NEGATIVE ring is pinned too (drill wider than the pad)',
      abs(ov['via_diameter'] - 0.4) < 1e-9, str(ov))

ov = overrides('via_diameter = 0.6\nvia_drill = 0.3\n', 'healthy.txt')
check('a healthy pair is left exactly alone',
      abs(ov['via_diameter'] - 0.6) < 1e-9, str(ov))

# The regression the overlay contract cares about.
ov = overrides('via_diameter = 0.25\nvia_drill = 0.18\n', 'small.txt')
check('a SMALL BUT POSITIVE ring is left alone (0.035mm is manufacturable)',
      abs(ov['via_diameter'] - 0.25) < 1e-9,
      f"{ov} -- firing here would change a key the user did not list; "
      f"test_fab_tiers pins that contract")

print('--- the ladder guards the merged floor, not just the file ---')

# A drill-only override is completed by the tier's diameter and can land on a
# ring the user never inspected -- the file-level guard cannot see this case.
lad = FT.fab_floor_ladder(4, tier='standard', overrides={'via_drill': 0.45})
ring = (lad[0]['via_diameter'] - lad[0]['via_drill']) / 2.0
check('a drill-only override merged onto the tier is still guarded',
      ring >= FT._MIN_SHIPPED_RING - 1e-9,
      f"via {lad[0]['via_diameter']}/{lad[0]['via_drill']} ring {ring}")

print('--- the built-in tiers must not move ---')

bad = []
for n in (2, 4):
    for tier in FT.TIERS:
        f = FT.fab_floor_ladder(n, tier=tier)[0]
        r = (f['via_diameter'] - f['via_drill']) / 2.0
        if r <= 0:
            bad.append(f'{n}L {tier} ring {r}')
check('every built-in rung still ships a positive ring', not bad, str(bad))

expect = {(2, 'standard'): (0.45, 0.20), (2, 'advanced'): (0.25, 0.15),
          (4, 'standard'): (0.45, 0.20), (4, 'advanced'): (0.25, 0.15)}
drift = []
for (n, tier), (dia, drill) in expect.items():
    f = FT.fab_floor_ladder(n, tier=tier)[0]
    if abs(f['via_diameter'] - dia) > 1e-9 or abs(f['via_drill'] - drill) > 1e-9:
        drift.append(f"{n}L {tier}: {f['via_diameter']}/{f['via_drill']} != {dia}/{drill}")
check('and no tier via pair was resized by the guard', not drift,
      ' | '.join(drift) + " -- the tiers declare an `annular` their own pairs do "
      "not meet, by design; enforcing it against them would move every run")

# NOT asserted here: "derived from the tables rather than hardcoded". A mutant
# that replaces the derivation with a literal 0.05 is behaviourally identical
# while the tables ship 0.05, so the claim is untestable from outside and
# asserting it would be theatre. The property that MATTERS is the backstop --
# `min()` derives in the direction that erodes the guard, and a future tighter
# tier must not silently lower the ring every pinned via gets.
check('the pin target never falls below the backstop',
      FT._MIN_SHIPPED_RING >= FT._MIN_SHIPPED_RING_FLOOR > 0,
      f'{FT._MIN_SHIPPED_RING} vs {FT._MIN_SHIPPED_RING_FLOOR}')

print('--- the pin target is a persisted floor, so it must be clean ---')
# It is written into a project and printed to users, so it must not be one ULP
# off. `0.2 + 2*0.05` is 0.30000000000000004 in binary, which is why the pin
# rounds like the neighbouring `fine` rung does.
for drill, want in ((0.3, 0.4), (0.45, 0.55), (0.2, 0.3), (0.25, 0.35)):
    lad = FT.fab_floor_ladder(4, tier='standard',
                              overrides={'via_diameter': drill, 'via_drill': drill})[0]
    check(f'a zero-ring pair at drill {drill:g} pins to exactly {want:g}',
          lad['via_diameter'] == want,
          f"{lad['via_diameter']!r} -- an unrounded floor is a one-ULP bug "
          f"waiting to be persisted (cf. #493)")

print('--- one warning per distinct pin, not one per ladder rebuild ---')
import io                                                        # noqa: E402
import contextlib                                                # noqa: E402
FT._pin_via_ring.__defaults__[1].clear()   # the dedupe set
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for _ in range(200):
        FT.fab_floor_ladder(4, tier='standard', overrides={'via_drill': 0.45})
n = buf.getvalue().count('annular ring of')
check('200 ladder rebuilds warn once, not 200 times',
      n == 1, f'{n} warnings -- an undeduped guard printed 788 lines in one '
              f'routing run, 46% of its output')

print('--- the writeback must never declare a floor of zero ---')
# `compute_targets` maps the board's measured minima onto the only-loosen project
# writeback. `min_via_annular_width: 0.0` does not mean "no annular requirement" to
# KiCad -- it means the annular rule is OFF, i.e. the writeback would disable the
# one grader that catches the vias being measured. This guard is a no-op TODAY
# (`scan_board_minima` filters `size > drill`, so the key is always positive) and
# becomes load-bearing the moment that measurement stops filtering.
import fix_kicad_drc_settings as FK                                # noqa: E402

t = FK.compute_targets(minima={'min_via_annular_width': 0.0})
check('a measured annular of 0.0 is not written as a floor',
      'min_via_annular_width' not in t,
      f"{t} -- writing 0.0 switches OFF KiCad's annular rule")

t = FK.compute_targets(minima={'min_via_annular_width': -0.05})
check('nor is a negative one', 'min_via_annular_width' not in t, str(t))

t = FK.compute_targets(minima={'min_via_annular_width': 0.075})
check('a positive measurement still lands, unchanged',
      abs(t.get('min_via_annular_width', -1) - 0.075) < 1e-12, str(t))

t = FK.compute_targets(minima={})
check('an absent measurement leaves the rule alone',
      'min_via_annular_width' not in t, str(t))

print('--- the measurement stops filtering out the pathological case ---')
# One board, three vias: a healthy 0.6/0.3 (ring 0.15), a marginal 0.45/0.3
# (ring 0.075), and the run-20 shape 0.3/0.3 (ring 0.0, a hole with no barrel
# land). The two keys must disagree, and the disagreement is the fix.
_BOARD = '''(kicad_pcb (version 20260206) (generator test)
 (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))
 (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") (width 0.1))
 (net 0 "") (net 1 "GND")
 (segment (start 5 5) (end 9 5) (width 0.2) (layer "F.Cu") (net 1))
 (via (at 10 10) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))
 (via (at 12 10) (size 0.45) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))
 (via (at 14 10) (size 0.3) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))
)'''
_d = tempfile.mkdtemp()
_b = os.path.join(_d, 'annular.kicad_pcb')
with open(_b, 'w', encoding='utf-8') as fh:
    fh.write(_BOARD)

m = FK.scan_board_minima(_b)
check('the WRITEBACK TARGET stays the positive-ring minimum (unchanged)',
      abs(m.get('min_via_annular_width', -1) - 0.075) < 1e-9,
      f"{m.get('min_via_annular_width')} -- compute_targets, "
      f"gui_utils.board_minima_from_live and pcb_modification read this key")
check('the MEASUREMENT reports the zero ring',
      abs(m.get('min_via_annular_width_measured', -1) - 0.0) < 1e-9,
      f"{m.get('min_via_annular_width_measured')} -- a measurement that filters "
      f"out the defect is how three unmanufacturable vias graded clean")
check('and the count of vias with no annular ring is published',
      m.get('vias_without_annular') == 1, str(m.get('vias_without_annular')))
check('the other minima are untouched by the split',
      abs(m.get('min_via_diameter', -1) - 0.3) < 1e-9
      and abs(m.get('min_via_drill', -1) - 0.3) < 1e-9
      and abs(m.get('min_track_width', -1) - 0.2) < 1e-9, str(m))

# A board with no pathology must not grow the new keys' bad news.
_b2 = os.path.join(_d, 'healthy.kicad_pcb')
with open(_b2, 'w', encoding='utf-8') as fh:
    fh.write(_BOARD.replace(' (via (at 14 10) (size 0.3) (drill 0.3) '
                            '(layers "F.Cu" "B.Cu") (net 1))\n', ''))
m2 = FK.scan_board_minima(_b2)
check('a healthy board reports no ringless vias at all',
      'vias_without_annular' not in m2, str(m2))
check('and there its two annular keys agree',
      abs(m2['min_via_annular_width'] - m2['min_via_annular_width_measured']) < 1e-12,
      str(m2))

print('--- check_complete grades the measurement, not the target ---')
sys.path.insert(0, REPO)
import check_complete as CC                                        # noqa: E402

check('exactly one floor key is redirected to a measurement',
      CC.MEASURED_KEY == {'min_via_annular_width': 'min_via_annular_width_measured'},
      str(CC.MEASURED_KEY))

# The authored project declares the floor the run-20 board declared.
_pro = os.path.join(_d, 'annular.kicad_pro')
with open(_pro, 'w', encoding='utf-8') as fh:
    fh.write('{"board": {"design_settings": {"rules": '
             '{"min_via_annular_width": 0.05}}}}')
res = CC.fab_floor_integrity(_b, _b)
keys = [r['key'] for r in res.get('relaxed', [])]
check('a zero-ring via makes the board UNSOUND against its own declaration',
      'min_via_annular_width' in keys,
      f"{res} -- graded against the filtered target this reads `relaxed: []`, "
      f"which is what run 20 reported on a board carrying three of them")
under = [r for r in res.get('relaxed', []) if r['key'] == 'min_via_annular_width']
check('and it reports the measured 0.0, not the surviving 0.075',
      under and abs(under[0]['on_board']) < 1e-12, str(under))

res2 = CC.fab_floor_integrity(_b2, _b2)
check('the healthy board is not newly condemned',
      not [r for r in res2.get('relaxed', [])
           if r['key'] == 'min_via_annular_width'],
      str(res2) + ' -- 0.075 is above the declared 0.05')

print('--- the check itself: a relation, not two scalars ---')
import check_drc as CD                                            # noqa: E402


class _V:                                                  # a Via, minimally
    def __init__(self, size, drill, net_id=1, x=0.0, y=0.0):
        self.size, self.drill, self.net_id, self.x, self.y = size, drill, net_id, x, y


# The whole point: this via passes BOTH scalar checks at the 4-layer floor and
# is unmanufacturable. That is the hole check_via_size cannot see.
_run20 = _V(0.3, 0.3)
d_bad, dr_bad, _sa, _sb = CD.check_via_size(_run20, 0.25, 0.15)
check('the run-20 via passes both scalar size checks',
      not d_bad and not dr_bad,
      'if this ever fails, the annular check is no longer the only thing '
      'standing between this via and a fab')
bad, ring, short = CD.check_via_annular(_run20, 0.0, strict=True)
check('and fails the relation', bad and ring == 0.0 and short == 0.0,
      f'{bad} {ring} {short}')

check('a negative ring fails too',
      CD.check_via_annular(_V(0.2, 0.3), 0.0, strict=True)[0], '')
check('a healthy ring passes the structural rung',
      not CD.check_via_annular(_V(0.6, 0.3), 0.0, strict=True)[0], '')
# The boundary IS the defect, so it belongs to the violation on the structural
# rung and to the PASS on a declared one -- KiCad's own semantic. Getting this
# backwards silently un-does the whole check: the first version of this code
# used `> margin` in both modes and reported the run-20 board clean.
check('the structural rung owns the boundary (ring == 0 fails)',
      CD.check_via_annular(_V(0.3, 0.3), 0.0, strict=True)[0], '')
check('a DECLARED floor does not (ring exactly at the floor passes)',
      not CD.check_via_annular(_V(0.5, 0.3), 0.1, strict=False)[0],
      'ring 0.1 against a declared 0.1')
check('but below a declared floor fails',
      CD.check_via_annular(_V(0.45, 0.3), 0.1, strict=False)[0],
      'ring 0.075 against a declared 0.1')
# size_margin must keep LOOSENING in both modes, or a tolerance becomes a trap.
check('size_margin loosens the strict rung too',
      not CD.check_via_annular(_V(0.3, 0.3), 0.0, size_margin=0.01,
                               strict=True)[0], '')

print('--- the boundary survives float representation error ---')
# The annular ring is the only size quantity here that is a DIFFERENCE of two
# stored numbers, so it inherits their representation error where a direct
# comparison would not. `(0.3 - 0.2) / 2` is 0.04999999999999999. Without an
# epsilon, 379 vias on kicad_files/routed_output.kicad_pcb were reported as
# violating a floor they exactly meet -- the report printing its own refutation,
# "Ring: 0.0500mm ... <= min 0.0500mm (short 0.0000mm)" -- while 0.8/0.5 vias
# with the same nominal ring graded clean because that pair is float-exact.
check('the fixture is a real ULP case, not a hand-picked one',
      (0.3 - 0.2) / 2.0 < 0.05, f'{(0.3 - 0.2) / 2.0!r} vs 0.05')
check('a via EXACTLY at a declared floor passes despite the ULP',
      not CD.check_via_annular(_V(0.3, 0.2), 0.05, strict=False)[0],
      f'ring {(0.3 - 0.2) / 2.0!r} against a declared 0.05')
for _dia, _dr, _fl in ((0.7, 0.4, 0.15), (0.35, 0.2, 0.075), (0.6, 0.4, 0.1)):
    check(f'...and so does {_dia:g}/{_dr:g} against {_fl:g}',
          not CD.check_via_annular(_V(_dia, _dr), _fl, strict=False)[0],
          f'ring {(_dia - _dr) / 2.0!r}')
check('one nanometre under a declared floor is still NOT a violation',
      not CD.check_via_annular(_V(0.3, 0.2 + 1e-10), 0.05, strict=False)[0],
      'the epsilon is 1nm -- four orders of magnitude below any fab tolerance')
check('but a micrometre under one IS',
      CD.check_via_annular(_V(0.3 - 2e-6, 0.2), 0.05, strict=False)[0], '')

print('--- a degenerate via is not quietly skipped ---')
# The via with the WORST possible ring -- a hole wider than its pad -- was
# dropped by a `via.size and via.drill` truthiness guard at the call site,
# re-introducing at the consumer exactly the "filter out the pathological
# input" defect this whole change set removes. It survived only because
# via-size happens to catch a zero diameter separately.
_bad, _ring, _ = CD.check_via_annular(_V(0.0, 0.3), 0.0, strict=True)
check('a via with zero diameter has a NEGATIVE ring and is flagged',
      _bad and _ring < 0, f'{_bad} {_ring}')

print('--- and it is wired end to end ---')
_DEGEN = '''(kicad_pcb (version 20260206) (generator test)
 (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))
 (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") (width 0.1))
 (net 0 "") (net 1 "GND")
 (via (at 10 10) (size 0) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))
)'''
import subprocess                                                  # noqa: E402
_drc = os.path.join(REPO, 'py_router', 'check_drc.py')


def _drc_run(board, *extra):
    r = subprocess.run([sys.executable, _drc, board, '--max-print', '0']
                       + list(extra), capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


_bd = os.path.join(_d, 'degen.kicad_pcb')
with open(_bd, 'w', encoding='utf-8') as fh:
    fh.write(_DEGEN)
rc, out = _drc_run(_bd)
check('the degenerate via reaches the annular check AT THE CALL SITE',
      'VIA-ANNULAR violations (1)' in out,
      out[-400:] + ' -- a `via.size and via.drill` truthiness guard dropped it, '
      'which is the same "filter out the pathological input" defect at the '
      'consumer instead of the producer; only via-size caught it, separately')

rc, out = _drc_run(_b)
check('the three-via fixture reports VIA-ANNULAR and exits 1',
      rc == 1 and 'VIA-ANNULAR violations (1)' in out,
      f'rc={rc}; ' + '; '.join(ln for ln in out.splitlines()
                               if 'violation' in ln.lower())[:200])
check('the message says what is wrong, not just that it is',
      'no barrel land' in out, out[-400:])
rc, out = _drc_run(_b, '--no-annular-check')
check('--no-annular-check turns it off and says so',
      rc == 0 and 'via annular UNCHECKED' in out, f'rc={rc}')

# The NEGATIVE test that decides the default. A 0.25/0.15 via is the advanced
# tier's OWN pair -- the rung the router legitimately escalates to -- and it has
# a real 0.05 ring. It must grade CLEAN by default even beside a project
# declaring 0.1, because a stock never-edited KiCad project declares exactly
# that against a 0.5 via. Measured: 12 boards in this tree carry a real zero
# ring and all 12 are run 20's own lineage; making the declaration a default
# rung would instead flag legitimate fine vias on boards whose only sin is an
# unedited default.
_fine = '\n'.join(ln.replace('(size 0.6) (drill 0.3)', '(size 0.25) (drill 0.15)')
                  for ln in _BOARD.splitlines()
                  if '(size 0.3) (drill 0.3)' not in ln
                  and '(size 0.45) (drill 0.3)' not in ln)
_bf = os.path.join(_d, 'fine.kicad_pcb')
with open(_bf, 'w', encoding='utf-8') as fh:
    fh.write(_fine)
with open(os.path.join(_d, 'fine.kicad_pro'), 'w', encoding='utf-8') as fh:
    fh.write('{"board": {"design_settings": {"rules": '
             '{"min_via_annular_width": 0.1}}}}')
rc, out = _drc_run(_bf)
check("the router's escalated fine via grades clean by default",
      rc == 0, f'rc={rc}; ' + out[-300:])
rc, out = _drc_run(_bf, '--annular-vs-board')
check('--annular-vs-board is what opts into the declaration',
      rc == 1 and 'VIA-ANNULAR' in out and 'board:' in out,
      f'rc={rc}; ' + out[-300:])
rc, out = _drc_run(_bf, '--min-via-annular-width', '0.2')
check('and an explicit CLI floor wins over everything',
      rc == 1 and 'annular >= 0.2mm (cli)' in out, f'rc={rc}; ' + out[-300:])

print('--- the score puts it in the right list ---')
_bs = os.path.join(REPO, '.claude', 'skills', 'plan-pcb-routing', 'scripts',
                   'board_score.py')
_r = subprocess.run([sys.executable, _bs, _b, '--quiet'],
                    capture_output=True, text=True, timeout=900)
_line = [ln for ln in (_r.stdout or '').splitlines() if ln.startswith('SCORE_JSON=')]
if _line:
    import json as _j                                              # noqa: E402
    sc = _j.loads(_line[0][len('SCORE_JSON='):])
    check('a ringless via lands in `undersized`, not `drc`',
          sc['components']['undersized']['by_type'].get('via-annular') == 1
          and sc['components']['drc']['count'] == 0,
          str(sc['blocking_by']) + ' -- different lever: a size finding is fixed '
          'by re-routing that copper bigger, a clearance finding by moving it')
    check('and it is INSIDE blocking, so removing one scores better',
          sc['blocking_by']['undersized'] == 1,
          str(sc['blocking_by']) + ' -- run 20 rejected a cycle that removed '
          'three of these, because nothing counted the vias it removed')
else:
    check('board_score produced a score line', False,
          (_r.stdout or _r.stderr)[-300:])

print('--- the corpus, not just the fixture ---')
# The board that exposed the ULP defect is in the repo: 379 vias at 0.3/0.2
# against a project declaring exactly 0.05.
_rp = os.path.join(REPO, 'kicad_files', 'routed_output.kicad_pcb')
if os.path.isfile(_rp):
    rc, out = _drc_run(_rp, '--annular-vs-board')
    _n = 0
    for _ln in out.splitlines():
        if _ln.startswith('VIA-ANNULAR violations ('):
            _n = int(_ln.split('(')[1].split(')')[0])
    check('379 vias exactly at their declared floor are not flagged',
          _n == 0, f'{_n} flagged -- ' + '; '.join(
              _l.strip() for _l in out.splitlines()
              if 'Ring:' in _l)[:160])
else:
    check('kicad_files/routed_output.kicad_pcb is present as a fixture',
          False, 'the ULP regression has no corpus witness without it')

print('--- what the score publishes about how it graded ---')
_r2 = subprocess.run([sys.executable, _bs, _b, '--quiet',
                      '--fab-tier', 'advanced'],
                     capture_output=True, text=True, timeout=900)
_l2 = [ln for ln in (_r2.stdout or '').splitlines()
       if ln.startswith('SCORE_JSON=')]
if _l2:
    import json as _j2                                              # noqa: E402
    sc2 = _j2.loads(_l2[0][len('SCORE_JSON='):])
    _fl2 = (sc2['components']['drc'] or {}).get('floors') or {}
    check('--fab-tier is FORWARDED to the check_drc child',
          (_fl2.get('size_floors') or {}).get('fab_tier') == 'advanced',
          f"{_fl2.get('size_floors')} -- dropping it made an override floor "
          f"unreachable from the score, and the two tools graded one board at "
          f"two different fab tiers with nothing saying so")
    check('and the size floors travel with their SOURCES',
          set(_fl2.get('size_floor_sources') or {}) >= {
              'min_track_width', 'min_via_diameter', 'min_via_drill',
              'min_via_annular_width'}, str(_fl2.get('size_floor_sources')))
    check('the annular check reports its EFFECTIVE state',
          _fl2.get('annular_check') is True, str(_fl2.get('annular_check')))
else:
    check('board_score ran with --fab-tier', False,
          (_r2.stdout or _r2.stderr)[-300:])

_r3 = subprocess.run([sys.executable, _drc, _b, '-q', '--max-print', '0',
                      '--no-size-checks', '--json',
                      os.path.join(_d, 'ns.json')],
                     capture_output=True, text=True, timeout=300)
if os.path.isfile(os.path.join(_d, 'ns.json')):
    import json as _j3                                              # noqa: E402
    _g3 = _j3.load(open(os.path.join(_d, 'ns.json'), encoding='utf-8'))['graded_at']
    check('--no-size-checks reports annular_check FALSE, because it is off',
          _g3.get('annular_check') is False
          and _g3.get('annular_check_requested') is True,
          f"{_g3.get('annular_check')} -- the rung lives inside the size-check "
          f"block, and reporting `true` there told a reader the structural "
          f"check had run on a board carrying three unmanufacturable vias")

print('--- KiCad is no longer gagged on the category ---')
# The run-20 board read clean in KiCad's OWN DRC too, and not because its
# annular rule had been ratcheted (it was still 0.05, identical to its origin):
# this repo wrote `rule_severities.annular_width = "ignore"`, on the stated
# grounds that "the router does not create or fix these". For pad annular rings
# that is true. For VIA annular rings it is false, and run 20 is the proof.
import fix_kicad_drc_settings as _FK2                                # noqa: E402
_plan = _FK2.severity_plan()
check('annular_width is no longer ignored',
      _plan.get('annular_width') != 'ignore', str(_plan))
check('it is demoted to a WARNING -- visible in KiCad, blocking in check_drc',
      _plan.get('annular_width') == 'warning',
      'an error would restore the pad-annular noise the ignore was for; '
      'silence would restore the gag. Same resolution as run 6 gave '
      'courtyards_overlap')
check('and the pad/library categories it used to travel with are unchanged',
      all(_plan.get(c) == 'ignore' for c in _FK2.FOOTPRINT_CATS)
      and 'annular_width' not in _FK2.FOOTPRINT_CATS, str(_FK2.FOOTPRINT_CATS))

print('--- the census counts the vias it exists to name ---')
_cens = _FK2._fab_floor_disclosure(
    _b, {'min_via_annular_width': 0.05},
    {'board': {'design_settings': {'rules': {'min_via_annular_width': 0.0}}}},
    {'min_via_annular_width': 0.05})
check('the disclosure counts the ringless via, not just the surviving ones',
      any('1 of 3' in ln for ln in _cens),
      f'{_cens} -- the census filtered `size > drill`, which excluded exactly '
      f'the vias it exists to disclose')

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
