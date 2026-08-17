#!/usr/bin/env python3
"""A requested width is a request. Nothing here measured the copper.

Run 20 routed with `--power-nets-widths 0.3 0.3 0.4 0.3` and delivered:

    +3V3   narrowest 0.15 vs 0.3 requested   103 of 226 segments under
    GND    narrowest 0.15 vs 0.3              59 of 60
    VBUS   narrowest 0.20 vs 0.4               2 of 73
    VDD    narrowest 0.15 vs 0.3               1 of 2

Not one of those is a floor violation -- every segment is at or above the
board's declared `min_track_width` of 0.15 -- so `check_drc` had nothing to say,
`board_score.net_widths` is `ungraded` unless `--net-min-widths` is passed, and
the only reason anybody found out was measuring the copper by hand afterwards.

The distinction that makes this actionable rather than noisy: a power trace
deliberately NECKS DOWN to reach a pad narrower than the request. Counting those
as shortfalls would flag correct copper on every board, so `tap_segments` are
separated out and only a TRUNK segment under the request is a finding.

    python3 tests/test_run20_power_widths.py
"""
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kicad_parser import BoardInfo, parse_kicad_pcb                # noqa: E402
from synth import make_net, make_pad, make_pcb, make_seg           # noqa: E402

RAIL, SIG = 1, 2
CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append((name, ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {name}" + (f' -- {detail}' if not ok else ''))


def _board():
    """A rail from a fat pad to a NARROW one, plus a signal net.

    The narrow pad is the point: the last hop into it cannot be 0.4 mm wide,
    so if the report counts that as a shortfall it will do so on every real
    board and the number becomes noise.
    """
    bi = BoardInfo(layers={0: 'F.Cu', 31: 'B.Cu'},
                   copper_layers=['F.Cu', 'B.Cu'],
                   board_bounds=(0.0, 0.0, 20.0, 20.0))
    pads = {
        RAIL: [make_pad(RAIL, 2.0, 10.0, ref='J1', num='1', net_name='VBUS',
                        size_x=2.0, size_y=2.0),
               # 0.2mm wide: a 0.4mm trunk physically cannot land on it.
               make_pad(RAIL, 16.0, 10.0, ref='U1', num='1', net_name='VBUS',
                        size_x=0.2, size_y=0.5)],
        SIG: [make_pad(SIG, 2.0, 4.0, ref='J1', num='2', net_name='SIG',
                       size_x=0.6, size_y=0.6),
              make_pad(SIG, 16.0, 4.0, ref='U1', num='2', net_name='SIG',
                       size_x=0.6, size_y=0.6)],
    }
    # The copper is BUILT, not routed. A router run on this fixture happened
    # to lay one 0.4mm segment straight into the narrow pad and neck down
    # nowhere, so the tap classification -- the whole point -- went untested.
    # Three segments, one of each kind, so every branch is exercised:
    segs = [
        # TRUNK at the requested width: not a finding.
        make_seg(2.0, 10.0, 10.0, 10.0, net_id=RAIL, width=0.4),
        # TRUNK under the request, nowhere near a narrow pad: THE finding.
        make_seg(10.0, 10.0, 14.0, 10.0, net_id=RAIL, width=0.2),
        # TAP: ends on U1.1, whose own narrow dimension (0.2) is below the
        # request, so the neckdown is the pad's doing and not a defect.
        make_seg(14.0, 10.0, 16.0, 10.0, net_id=RAIL, width=0.15),
    ]
    return make_pcb(nets={RAIL: make_net(RAIL, 'VBUS'),
                          SIG: make_net(SIG, 'SIG')},
                    segments=segs, pads_by_net=pads, board_info=bi)


def main():
    from route import batch_route
    buf = io.StringIO()
    with redirect_stdout(buf):
        batch_route('synthetic', '', ['VBUS', 'SIG'], layers=['F.Cu', 'B.Cu'],
                    clearance=0.15, track_width=0.15, via_size=0.5,
                    via_drill=0.3, grid_step=0.1,
                    power_nets=['VBUS'], power_nets_widths=[0.4],
                    ordering_strategy='original', final_reconcile=False,
                    return_results=True, pcb_data=_board())
    out = buf.getvalue()
    m = re.findall(r'JSON_SUMMARY: (\{.*\})', out)
    check('JSON_SUMMARY present', bool(m))
    summary = json.loads(m[-1]) if m else {}

    pw = summary.get('power_widths')
    check("summary carries 'power_widths' when --power-nets was used",
          isinstance(pw, dict) and 'VBUS' in pw, str(pw))
    if isinstance(pw, dict) and 'VBUS' in pw:
        r = pw['VBUS']
        check('it records what was REQUESTED, not only what landed',
              abs(r['requested_mm'] - 0.4) < 1e-9, str(r))
        check('and the narrowest copper actually delivered',
              isinstance(r['narrowest_mm'], float)
              and r['narrowest_mm'] <= 0.4 + 1e-9, str(r))
        check('with a total to make the counts readable',
              r['segments_total'] >= 1, str(r))
        check('THE DISTINCTION: the neckdown into a 0.2mm pad is a TAP, '
              'not a shortfall',
              r['tap_segments'] == 1 and r['segments_under'] == 1,
              f"{r} -- a power trace must neck down to reach a narrow pad; "
              f"counting that as a defect would flag correct copper on every "
              f"board and the number would be ignored")
        check('and the two counts are separate numbers, not one blended one',
              set(r) == {'requested_mm', 'narrowest_mm', 'segments_total',
                         'segments_under', 'tap_segments'}, str(sorted(r)))
        check('the disclosure line is PRINTED, not left in the JSON',
              'requested power width NOT delivered' in out
              and 'VBUS' in out, out[-800:])
        check('...and it names the tap exclusion, so the number can be trusted',
              'pad tap(s) excluded' in out, out[-800:])

    check('a net with NO width request is not reported on',
          'SIG' not in (pw or {}), str(pw))

    # No --power-nets at all: the key must be absent, not an empty dict. An
    # empty dict reads as "measured, nothing wrong"; absence reads as "not
    # asked", which is the truth.
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        batch_route('synthetic', '', ['VBUS', 'SIG'], layers=['F.Cu', 'B.Cu'],
                    clearance=0.15, track_width=0.15, via_size=0.5,
                    via_drill=0.3, grid_step=0.1,
                    ordering_strategy='original', final_reconcile=False,
                    return_results=True, pcb_data=_board())
    m2 = re.findall(r'JSON_SUMMARY: (\{.*\})', buf2.getvalue())
    s2 = json.loads(m2[-1]) if m2 else {}
    check('without --power-nets the key is ABSENT, not an empty dict',
          'power_widths' not in s2, str(s2.get('power_widths')))

    print('--- and the board that produced the finding ---')
    _r20 = os.path.join(REPO, 'wk', 'run20', 'routed.kicad_pcb')
    if os.path.isfile(_r20):
        b2 = io.StringIO()
        with redirect_stdout(b2):
            pcb = parse_kicad_pcb(_r20)
        name = {n.name: i for i, n in pcb.nets.items()}
        want = {'GND': (0.3, 0.15, 59, 60), '+3V3': (0.3, 0.15, 103, 226),
                'VBUS': (0.4, 0.20, 2, 73), 'VDD': (0.3, 0.15, 1, 2)}
        bad = []
        for nm, (req, narrow, under, total) in want.items():
            nid = name.get(nm)
            segs = [s for s in pcb.segments if s.net_id == nid and s.width]
            got = (round(min(s.width for s in segs), 2) if segs else None,
                   sum(1 for s in segs if s.width < req - 1e-9), len(segs))
            if got != (narrow, under, total):
                bad.append(f'{nm}: {got} != {(narrow, under, total)}')
        check('the run-20 shortfalls are exactly as measured', not bad,
              '; '.join(bad) + ' -- these four rows are the reason this '
              'exists; if they drift, the board changed, not the tool')
    else:
        print('  (wk/run20/routed.kicad_pcb absent -- corpus witness skipped)')

    bad = [n for n, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(bad)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
