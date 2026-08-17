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

    print('--- the two cases that discriminate the classifier ---')
    # Neither of these is exercised by the fixture above or by the run-20
    # board, and without them the test cannot tell the shipped classifier from
    # the one it replaced -- a mutation run proved exactly that.
    from route import power_width_report
    from kicad_parser import BoardInfo as _BI

    def _one_net(pads, segs):
        bi = _BI(layers={0: 'F.Cu', 31: 'B.Cu'},
                 copper_layers=['F.Cu', 'B.Cu'],
                 board_bounds=(0.0, 0.0, 20.0, 20.0))
        return make_pcb(nets={RAIL: make_net(RAIL, 'VBUS')}, segments=segs,
                        pads_by_net={RAIL: pads}, board_info=bi)

    # (a) A LONG pad: 2.0 x 0.4 at (16,10), so its copper spans x 15.0..17.0.
    # The segment ends at x=15.1 -- 0.1mm INSIDE the pad, and 0.9mm from its
    # CENTRE. A centre box of 0.6 calls that a trunk shortfall; the pad
    # rectangle calls it the tap it physically is.
    _long = make_pad(RAIL, 16.0, 10.0, ref='U1', num='1', net_name='VBUS',
                     size_x=2.0, size_y=0.4)
    _feed = make_pad(RAIL, 2.0, 10.0, ref='J1', num='1', net_name='VBUS',
                     size_x=2.0, size_y=2.0)
    r = power_width_report(
        _one_net([_feed, _long],
                 [make_seg(2.0, 10.0, 15.1, 10.0, net_id=RAIL, width=0.2)]),
        {RAIL: 0.5})['VBUS']
    check('a track ending INSIDE a long pad is a tap, not a shortfall',
          r['tap_segments'] == 1 and r['segments_under'] == 0,
          f"{r} -- 0.9mm from the pad CENTRE but 0.1mm inside its copper; "
          f"under a centre box, landing further onto the pad turned a tap into "
          f"a defect, on every SOT-223 tab and thermal paddle")

    # (b) The same geometry on a layer the pad is not on. An F.Cu-only SMD pad
    # must not excuse B.Cu copper it can never touch.
    r = power_width_report(
        _one_net([_feed, _long],
                 [make_seg(2.0, 10.0, 15.1, 10.0, net_id=RAIL, width=0.2,
                           layer='B.Cu')]),
        {RAIL: 0.5})['VBUS']
    check('...but only on a layer that pad is actually on',
          r['tap_segments'] == 0 and r['segments_under'] == 1,
          f"{r} -- the pad is F.Cu-only; on run 20 this excused a 5.275mm "
          f"B.Cu trunk at half the requested width")

    # (c) A through-hole pad IS on every layer, so the same B.Cu segment is a
    # tap again. Without this the layer test would be too strict.
    _thru = make_pad(RAIL, 16.0, 10.0, ref='U1', num='1', net_name='VBUS',
                     size_x=2.0, size_y=0.4, drill=0.3, pad_type='thru_hole',
                     layers=('*.Cu',))
    r = power_width_report(
        _one_net([_feed, _thru],
                 [make_seg(2.0, 10.0, 15.1, 10.0, net_id=RAIL, width=0.2,
                           layer='B.Cu')]),
        {RAIL: 0.5})['VBUS']
    check('a barrel is on every layer, so it still excuses the neckdown',
          r['tap_segments'] == 1 and r['segments_under'] == 0, str(r))

    print('--- and the board that produced the finding ---')
    # THE WITNESS CALLS THE SHIPPED CODE. The first version of this block
    # recomputed the numbers with a one-line comprehension and never executed a
    # line of route.py -- so it asserted the RAW under-count while the shipped
    # classifier emitted the tap-subtracted one, and passed while the two
    # disagreed. Deleting the entire tap branch could not have failed it.
    from route import power_width_report
    _r20 = os.path.join(REPO, 'wk', 'run20', 'routed.kicad_pcb')
    if os.path.isfile(_r20):
        b2 = io.StringIO()
        with redirect_stdout(b2):
            pcb = parse_kicad_pcb(_r20)
        name = {n.name: i for i, n in pcb.nets.items()}
        req = {'GND': 0.3, '+3V3': 0.3, 'VBUS': 0.4, 'VDD': 0.3}
        rep = power_width_report(
            pcb, {name[k]: v for k, v in req.items() if k in name})
        # (requested, narrowest, segments_under, segments_total, tap_segments)
        want = {'+3V3': (0.3, 0.15, 86, 226, 17),
                'GND':  (0.3, 0.15, 59,  60,  0),
                'VBUS': (0.4, 0.20,  1,  73,  1),
                'VDD':  (0.3, 0.15,  0,   2,  1)}
        bad = []
        for nm, (rq, narrow, under, total, taps) in want.items():
            r = rep.get(nm)
            if not r:
                bad.append(f'{nm}: absent')
                continue
            got = (r['requested_mm'], r['narrowest_mm'], r['segments_under'],
                   r['segments_total'], r['tap_segments'])
            if got != (rq, narrow, under, total, taps):
                bad.append(f'{nm}: {got} != {(rq, narrow, under, total, taps)}')
        check('the run-20 rows are what the SHIPPED classifier emits', not bad,
              '; '.join(bad) + ' -- these are the tap-SUBTRACTED counts. The '
              'raw ones (103/59/2/1) are what the first version of this test '
              'and the commit message both quoted, and they are not what the '
              'code produces')
        check('VDD is the case that separates the two: its one under-width '
              'segment is a TAP, so it warns about nothing',
              rep['VDD']['segments_under'] == 0
              and rep['VDD']['tap_segments'] == 1, str(rep.get('VDD')))
        check('and +3V3 lost 3 taps to the layer test',
              rep['+3V3']['tap_segments'] == 17,
              f"{rep['+3V3']} -- 20 before the layer test; three were excused "
              f"by a pad the segment's layer does not carry, one of them a "
              f"5.275mm B.Cu trunk at half the requested width")
    else:
        print('  (wk/run20/routed.kicad_pcb absent -- corpus witness skipped)')

    bad = [n for n, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(bad)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
