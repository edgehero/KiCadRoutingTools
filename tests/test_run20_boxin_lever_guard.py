#!/usr/bin/env python3
"""A grid lever the router has already said cannot help.

Run 20's router printed "boxed in by static obstacles (neighboring pads +
clearance), not by congestion" on every residual failure. Three grid
refinements were spent against it -- 0.05 -> 0.025 -> 0.0125, about 40 minutes
-- with `unrouted` at exactly BUSY / Net-(U4-XTAL_P) / SCK at every resolution.

Two separate defects made that possible:

  * the HINT advised the geometry already in force. It hardcoded
    `--clearance 0.15 --track-width 0.15` regardless of the config, and the run
    was routing at exactly 0.15/0.15 -- so the only novel token in the whole
    sentence was the grid.
  * nothing GATED on the verdict. Warn-only was tried by circumstance: the
    warning was on screen every time and the laps were spent anyway.

A finer grid resolves the SAME obstacles more precisely. It does not make a gap
wider. When the geometry is at the board's declared floor there is nothing left
to pair it with, and the parameter family is spent.

    python3 tests/test_run20_boxin_lever_guard.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
DRIVER = os.path.join(REPO, '.claude', 'skills',
                      'plan-pcb-placement-and-routing', 'scripts',
                      'loop_driver.py')
CONVERGE = os.path.join(REPO, 'py_placer', 'converge.py')

import routing_diagnostics as RD                                   # noqa: E402

passed = failed = 0


def check(label, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  OK   {label}')
    else:
        failed += 1
        print(f'  FAIL {label} -- {detail}')


_D = tempfile.mkdtemp()

print('--- the hint stops advising the geometry already in use ---')

_HB = os.path.join(_D, 'hint.kicad_pcb')
with open(_HB, 'w', encoding='utf-8') as fh:
    fh.write('(kicad_pcb (version 20260206) (generator t)\n'
             ' (layers (0 "F.Cu" signal) (2 "B.Cu" signal))\n (net 0 ""))')
with open(os.path.join(_D, 'hint.kicad_pro'), 'w', encoding='utf-8') as fh:
    json.dump({'board': {'design_settings': {
        'rules': {'min_track_width': 0.15},
        'defaults': {'track_width': 0.15}}}}, fh)


class _Cfg:
    grid_step, clearance, track_width, via_diameter = 0.05, 0.15, 0.15, 0.6


class _Pcb:
    source_path = _HB

    class board_info:
        board_bounds = (0, 0, 40, 30)


_RESULT = {'iterations_forward': 400, 'iterations_backward': 400}
hint, verdict = RD.static_boxin_hint(_RESULT, _Cfg(), _Pcb(),
                                     return_verdict=True)
check('at the declared floor the hint says the parameter family is spent',
      'ALREADY at this board' in hint and 'PLACEMENT/FLOORPLAN FINDING' in hint,
      hint)
check('and it does NOT advise the values already in force',
      '--track-width 0.15' not in hint and '--clearance 0.15' not in hint,
      hint + ' -- run 20\'s hint advised exactly what was running, so the only '
             'novel token in it was the grid')
check('the verdict says so as DATA, not only as prose',
      verdict.get('at_floor') is True, str(verdict))
check('and carries the floors it compared against',
      (verdict.get('floors') or {}).get('track_width') == 0.15,
      str(verdict.get('floors')))


class _Cfg2(_Cfg):
    clearance, track_width = 0.25, 0.3


hint2, verdict2 = RD.static_boxin_hint(_RESULT, _Cfg2(), _Pcb(),
                                       return_verdict=True)
check('with travel left it advises the geometry, paired with the grid',
      '--track-width 0.15' in hint2 and '--grid-step' in hint2, hint2)
check('and says the grid is the COMPLEMENT, never the lever alone',
      'COMPLEMENT' in hint2, hint2)
check('the verdict agrees', verdict2.get('at_floor') is False, str(verdict2))


class _NoSrc:
    source_path = None

    class board_info:
        board_bounds = (0, 0, 40, 30)


hint3, verdict3 = RD.static_boxin_hint(_RESULT, _Cfg(), _NoSrc(),
                                       return_verdict=True)
check('with no readable floor it says UNKNOWN rather than guessing',
      verdict3.get('at_floor') is None and 'unknown' in hint3.lower(), hint3)

print('--- and L4 refuses the lever, rather than warning about it ---')

_B = os.path.join(_D, 'r.kicad_pcb')
with open(_B, 'w', encoding='utf-8') as fh:
    fh.write('(kicad_pcb (version 20260206) (generator t)\n'
             ' (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))\n'
             ' (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") (width 0.1))\n'
             ' (net 0 ""))')
_SHA = hashlib.sha256(open(_B, 'rb').read()).hexdigest()
_LED = os.path.join(_D, 'l.jsonl')
open(_LED, 'w').close()
subprocess.run([sys.executable, CONVERGE, 'record', '--ledger', _LED,
                '--board', _B, '--kind', 'completion', '--lever', 'the route'],
               capture_output=True, text=True, timeout=300)


def _w(name, doc):
    p = os.path.join(_D, name)
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh)
    return p


_SC = _w('s.json', {'kind': 'board-score', 'blocking': 10, 'board_sha': _SHA,
                    'blocking_by': {'unrouted': 3}, 'quality': {},
                    'components': {}, 'ungraded': [], 'unknown': []})
_CG = _w('cg.json', {'metrics': {'crossings': 100, 'hpwl': 500.0},
                     'instrument': {'board': os.path.abspath(_B)}})
_CGB = _w('cgb.json', {'metrics': {'crossings': 400, 'hpwl': 900.0},
                       'instrument': {'board': os.path.abspath(_B)}})


def _boxsum(name, at_floor, geom):
    return _w(name, {'boxed_in': [
        {'net': 'BUSY', 'verdict': 'boxed_in_static', 'iterations': 812,
         'geometry': geom, 'floors': {'clearance': 0.15, 'track_width': 0.15},
         'at_floor': at_floor}]})


_ATF = _boxsum('atf.json', True,
               {'grid_step': 0.05, 'clearance': 0.15, 'track_width': 0.15})
_TRV = _boxsum('trv.json', False,
               {'grid_step': 0.05, 'clearance': 0.25, 'track_width': 0.3})
_UNK = _boxsum('unk.json', None,
               {'grid_step': 0.05, 'clearance': 0.15, 'track_width': 0.15})
_NONE = _w('none.json', {'blockers': []})


def _l4(*extra):
    p = subprocess.run(
        [sys.executable, '-X', 'utf8', DRIVER, '--stage', 'L4',
         '--shape', 'parameter', '--board', _B, '--ledger', _LED,
         '--score', _SC, '--no-delegate',
         '--congestion-json', _CG, '--congestion-baseline', _CGB] + list(extra),
        capture_output=True, text=True, timeout=600)
    return (p.stdout or '') + (p.stderr or '')


out = _l4('--route-summary', _ATF)
check('a static-boxin verdict at the floor REFUSES the parameter lever',
      '<error>' in out and 'boxed in by STATIC obstacles' in out
      and 'ALREADY at this board' in out, out[:400])
check('the refusal names the nets and the geometry that was running',
      'BUSY' in out and 'grid 0.05' in out, out[:500])
check('it quotes the measurement rather than asserting the rule',
      '0.05 -> 0.025 -> 0.0125' in out and '40 min' in out, out[:900])
check('and it hands over the placement measurement to take instead',
      'check_reachability' in out and 'COPPER-FREE' in out
      and '--defect-json' in out, out[:1200])

out = _l4('--route-summary', _TRV)
check('with travel left it REPORTS and does not refuse',
      '<error>' not in out and 'boxed in by STATIC' in out, out[:400])
check('...and the note reaches the stage body, not just the console',
      'complement, never the lever alone' in out, out[:800])

out = _l4('--route-summary', _UNK)
check('an UNKNOWN floor does not refuse -- "I could not tell" is not "you '
      'failed"',
      '<error>' not in out and 'UNKNOWN' in out, out[:500])

out = _l4('--route-summary', _NONE)
check('no box-in verdict at all is silent', '<error>' not in out
      and 'boxed in by STATIC' not in out, out[:300])

out = _l4()
check('and with no --route-summary the guard is a no-op',
      '<error>' not in out and 'boxed in by STATIC' not in out, out[:300])

_WHY = '0.4mm pitch pads; a via-in-pad fanout is planned and changes the field'
out = _l4('--route-summary', _ATF, '--accept-boxin', _WHY)
check('--accept-boxin proceeds',
      '<error>' not in out, out[:400])
check('and the REASON is echoed into the body, so it reaches the ledger',
      _WHY in out, out[:600])

out = _l4('--route-summary', _ATF, '--accept-boxin', '   ')
check('a blank reason does NOT waive it',
      '<error>' in out and 'ALREADY at this board' in out, out[:300])

_BAD = os.path.join(_D, 'missing.json')
out = _l4('--route-summary', _BAD)
check('an unreadable summary is a NOTE, never a refusal',
      '<error>' not in out and 'unreadable' in out, out[:400])

print('--- the skill says the same thing, in the row that misdirected ---')
_SK = os.path.join(REPO, '.claude', 'skills', 'plan-pcb-routing', 'SKILL.md')
_t = open(_SK, encoding='utf-8').read()
check('the box-in row is SPLIT on whether the geometry has travel',
      'geometry has travel' in _t and 'geometry at the declared floor' in _t,
      'one row that says "try a finer grid" for both cases is the misdirection')
check('and the at-floor half sends the reader to placement',
      'the parameter family is spent' in _t, '')
check('`ripup budget` is gone from the box-in row',
      'ripup budget' not in _t.split('boxed_in` names the net')[-1][:1200],
      'run 20 measured the rip lever at 10 -> 15 on exactly this verdict, and '
      '"no rippable blockers found" means the blockers are not rippable copper')
check('the measurement that produced the rule is quoted with it',
      '0.05 -> 0.025 -> 0.0125' in _t, 'a rule without its measurement becomes '
      'folklore and gets deleted by the next reader')

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
