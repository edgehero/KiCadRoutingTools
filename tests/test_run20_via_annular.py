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

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
