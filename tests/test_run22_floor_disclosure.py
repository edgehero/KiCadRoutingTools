#!/usr/bin/env python3
"""Run 22: the two relaxations nobody could see.

That run produced a board reporting `unrouted 0, broken 0` while carrying 39
objects below its own declared floors. It was caught only because the routing
agent re-graded at the ORIGINAL floors on its own initiative. Two of the
instruments it should have been able to rely on were blind:

  * `min_clearance` 0.15 -> 0.125 was relaxed and NOT disclosed. It is
    deliberately absent from FAB_FLOOR_KEYS -- that tuple feeds
    check_complete's UNSOUND verdict, and clearance is the one floor with a
    measured reason to be treated as aspirational (zynq ships 499 violations
    of its own 0.2 class) -- but "not a fab claim" is not "not worth saying".
    Three of four relaxations were named and the fourth was silent.

  * the standard->advanced fab-floor escalation that put 0.25/0.15 vias on the
    board printed a WARNING to a routing log and reached nothing else: no
    summary key, no .kicad_pro, no grader. Disclosed, but not instrumented, so
    no automated reader could see it.

Run: python3 -X utf8 tests/test_run22_floor_disclosure.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'py_router'))
os.environ.setdefault('KRT_NO_BANNER', '1')

import fab_tiers as FT                                         # noqa: E402
import fix_kicad_drc_settings as FX                            # noqa: E402

FAILURES = []


def check(name, cond, detail=''):
    print(f'  {"PASS" if cond else "FAIL"}  {name}'
          + (f'\n        {detail}' if not cond and detail else ''))
    if not cond:
        FAILURES.append(name)


def main():
    print('the clearance relaxation run 22 could not see')
    lines = FX._grading_floor_disclosure(
        {'min_clearance': 0.15}, {'min_clearance': 0.125}, {})
    text = ' '.join(lines)
    check('a relaxed min_clearance is disclosed',
          bool(lines), 'the exact run-22 relaxation is still silent')
    check('...naming both numbers',
          '0.15' in text and '0.125' in text, text)
    check('...in its OWN block, not the fab one',
          'GRADING FLOOR RELAXED' in text and 'FAB FLOOR' not in text, text)
    check('...and saying why there is no object census',
          'PAIRWISE' in text, text)

    check('an UNCHANGED clearance says nothing',
          FX._grading_floor_disclosure(
              {'min_clearance': 0.15}, {'min_clearance': 0.15}, {}) == [])
    # TIGHTENED means a LARGER clearance -- more copper-to-copper space, not
    # less. Only a drop is a relaxation, and only a relaxation is disclosed.
    check('a TIGHTENED clearance says nothing',
          FX._grading_floor_disclosure(
              {'min_clearance': 0.15}, {'min_clearance': 0.2}, {}) == [])

    # The origin is what keeps a multi-step chain honest: by step 2 the
    # relaxed value IS the input, so without it nothing has "moved" and the
    # board keeps sliding in silence (run 14's fab-side lesson, applied here).
    check('a chain step that INHERITS a relaxed clearance still says so',
          FX._grading_floor_disclosure({'min_clearance': 0.125},
                                       {'min_clearance': 0.125},
                                       {'min_clearance': 0.15}) != [])

    check('min_clearance is NOT in FAB_FLOOR_KEYS',
          'min_clearance' not in {k for k, _ in FX.FAB_FLOOR_KEYS},
          'promoting it there reaches check_complete UNSOUND and '
          're-manufactures the phantom storm the clamp exists to avoid')

    print('the escalation that reached only a log line')
    FT.set_default_fab_tier('standard')
    check('a fresh run starts with no escalations', FT.fab_escalations() == [])
    FT.warn_fab_escalation('net rescue /AD4')
    FT.warn_fab_escalation('net rescue /AD4')          # deduped
    FT.warn_fab_escalation('qfn escape U3')
    ev = FT.fab_escalations()
    check('each distinct escalation is recorded once', len(ev) == 2, str(ev))
    check('...naming the context that escalated',
          {e['context'] for e in ev} == {'net rescue /AD4', 'qfn escape U3'},
          str(ev))
    check('...and the direction it went',
          all(e['from'] == 'standard' and e['to'] == 'advanced' for e in ev),
          str(ev))
    FT.set_default_fab_tier('standard')
    check('a new run resets them', FT.fab_escalations() == [])

    check('the caller cannot mutate the record',
          (FT.warn_fab_escalation('x'),
           FT.fab_escalations().clear(),
           len(FT.fab_escalations()) == 1)[-1])

    print('route.py publishes them')
    src = open(os.path.join(ROOT, 'py_router', 'route.py'),
               encoding='utf-8').read()
    check("summary['fab_escalations'] is emitted",
          "summary['fab_escalations']" in src)

    print()
    if FAILURES:
        print(f'FAIL: {len(FAILURES)} check(s): {", ".join(FAILURES)}')
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
