"""run-23 C4: the zero-pose census carries a NEAR-MISS report.

Run 23 hit `count_legal_poses == 0` three times (J5 "0 legal poses in a 20mm
disc incl. staying put", U6, J1), and each dead end was resolved by an
UNCHECKED place_fixed assert that shipped a courtyard overlap. The checked
assert (test_place_fixed.py pins that contract) closes the bypass; this file
pins the information that makes the honest move findable instead: a park
whose census counted zero reports the K nearest-to-legal poses, each with
its residual overlap and the refs in the way.

Fixture: the board run 23 actually shipped (tests/fixtures/run23), so the
census runs on real density, not a synthetic pile.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'tests', 'fixtures', 'run23',
                     'tigard_placed.kicad_pcb')
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}"
          f"{(' -- ' + detail) if ok else (' -- ' + detail)}")


def main():
    from kicad_parser import parse_kicad_pcb
    from placement.plan_ops import parse_placement_plan
    from placement.plan_resolve import resolve

    pcb = parse_kicad_pcb(BOARD)

    # Ask for a seat DEAD ON U3's centre with a budget too small to escape
    # it: the census must count 0 and the near-miss must name U3 (or a
    # neighbour) as what is in the way.
    u3 = pcb.footprints['U3']
    ops, errs = parse_placement_plan(json.dumps([
        {'action': 'place_at', 'ref': 'C1', 'at': [u3.x, u3.y],
         'within': 1.0},
    ]))
    assert not errs, errs
    res = resolve(pcb, BOARD, ops)

    park = next((p for p in res.parks if p.ref == 'C1'), None)
    check('the impossible seat parks, censused',
          park is not None and park.censused,
          str(park and park.reason))
    check('the census counted zero poses',
          park is not None and park.baseline_poses == 0,
          f'baseline_poses={park and park.baseline_poses}')
    check('the park carries a near-miss report',
          bool(park and park.near_miss),
          json.dumps(park.near_miss if park else None))
    nm = (park.near_miss or [None])[0] if park else None
    check('the nearest miss names who is in the way',
          bool(nm and nm['hits']), str(nm))
    check('...with a measured residual overlap',
          bool(nm and nm['overlap_mm2'] > 0), str(nm))
    check('the reason SENTENCE carries the next move',
          bool(park and 'nearest-to-legal pose' in park.reason),
          str(park and park.reason[-160:]))
    check('near-miss entries have distinct blocker sets',
          park is not None and len({tuple(e['hits'])
                                    for e in (park.near_miss or [])})
          == len(park.near_miss or []),
          str(park and park.near_miss))
    check('to_dict round-trips the report',
          park is not None and park.to_dict().get('near_miss')
          == park.near_miss, '')

    # A seat that SUCCEEDS must not pay for or carry a near-miss.
    ops2, errs2 = parse_placement_plan(json.dumps([
        {'action': 'place_at', 'ref': 'C1',
         'at': [pcb.footprints['C1'].x, pcb.footprints['C1'].y],
         'within': 2.0},
    ]))
    assert not errs2, errs2
    res2 = resolve(pcb, BOARD, ops2)
    check('a seatable op parks nothing (the report is not noise)',
          not [p for p in res2.parks if p.ref == 'C1'],
          str([(p.ref, p.reason) for p in res2.parks]))

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
