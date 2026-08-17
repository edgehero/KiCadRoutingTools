#!/usr/bin/env python3
"""The baseline a grader compares against, when nobody handed it one.

`kicad_routing_tools.fab_floor_origin` -- the floors the board declared BEFORE
the chain's only-loosen writeback touched them -- has existed since run 14. It
is seeded on the first writeback and carried project-to-project exactly like
`protected_nets`. And `check_complete`, the one tool whose entire job is asking
"does this board grade itself against floors it rewrote", never looked at it: a
run without `--authored-from` reported `ran: False`, on a board whose own
project carried the answer.

Two things this file pins that are easy to get wrong:

  * the fallback must SAY it is the fallback. It is strictly narrower than
    `--authored-from` (the origin holds only the keys the project DECLARED at
    the first writeback), so a reader who cannot tell the two apart cannot tell
    a narrow pass from a real one.
  * `check_drc` adopts the origin for `min_hole_clearance` ONLY. Extending it
    to the size floors storms: run 7 measured 5629 of 5933 segments under the
    original floor on a stock-default board. That belongs at check_complete's
    verdict altitude as one line with counts.
"""
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_complete as CC                                        # noqa: E402
import fix_kicad_drc_settings as FK                                # noqa: E402

passed = failed = 0


def check(label, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  OK   {label}')
    else:
        failed += 1
        print(f'  FAIL {label} -- {detail}')


# A board whose copper is BELOW what its project once declared: 0.15 track
# against a declared 0.2, and a via ring of 0.075 against a declared 0.1.
_BOARD = '''(kicad_pcb (version 20260206) (generator test)
 (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))
 (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") (width 0.1))
 (net 0 "") (net 1 "GND")
 (segment (start 5 5) (end 9 5) (width 0.15) (layer "F.Cu") (net 1))
 (via (at 12 10) (size 0.45) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))
)'''
_ORIGIN = {'min_track_width': 0.2, 'min_via_annular_width': 0.1,
           'min_hole_clearance': 0.254}


def _stage(name, *, origin=None, rules=None):
    """A board + project in a fresh dir. `origin` goes in kicad_routing_tools."""
    d = tempfile.mkdtemp()
    b = os.path.join(d, name + '.kicad_pcb')
    with open(b, 'w', encoding='utf-8') as fh:
        fh.write(_BOARD)
    pro = {'board': {'design_settings': {'rules': dict(rules or {})}}}
    if origin is not None:
        pro['kicad_routing_tools'] = {'fab_floor_origin': dict(origin)}
    with open(os.path.join(d, name + '.kicad_pro'), 'w', encoding='utf-8') as fh:
        json.dump(pro, fh)
    return d, b


print('--- the fallback exists, and names itself ---')

# The RATCHETED project: its rules now match the copper, which is exactly the
# state every chain output is in. Without the origin there is nothing to catch.
_d, _b = _stage('routed', origin=_ORIGIN,
                rules={'min_track_width': 0.15, 'min_via_annular_width': 0.05})
r = CC.fab_floor_integrity(_b, None)
check('with no --authored-from the check RUNS on the origin',
      r.get('ran') is True and r.get('baseline') == 'fab_floor_origin', str(r))
keys = {x['key'] for x in r.get('relaxed', [])}
check('and it catches copper below the ORIGINAL declaration',
      'min_track_width' in keys,
      f"{r} -- 0.15 copper against an origin of 0.2, while the project's own "
      f"rules say 0.15 because the writeback lowered them")
check('the payload names WHICH project it read',
      r.get('baseline_source', '').endswith('routed.kicad_pro'), str(r))

print('--- --authored-from still wins, and is still better ---')

# The AUTHORED board declares a floor the origin does not carry at all. That is
# the whole difference between the two baselines, so it is what gets asserted.
_d2, _b2 = _stage('authored', rules={'min_track_width': 0.2,
                                     'min_via_annular_width': 0.1,
                                     'min_via_diameter': 0.6})
r2 = CC.fab_floor_integrity(_b, _b2)
check('--authored-from is reported as the baseline when given',
      r2.get('baseline') == 'authored-from', str(r2))
k2 = {x['key'] for x in r2.get('relaxed', [])}
check('and it sees a floor the origin never recorded',
      'min_via_diameter' in k2 and 'min_via_diameter' not in keys,
      f'authored found {sorted(k2)}, origin found {sorted(keys)} -- this gap is '
      f'why the driver still tells the operator to pass --authored-from')

print('--- and a board with no baseline at all says so ---')

_d3, _b3 = _stage('bare', rules={'min_track_width': 0.15})
r3 = CC.fab_floor_integrity(_b3, None)
check('no origin, no --authored-from -> ran False, baseline None',
      r3.get('ran') is False and r3.get('baseline') is None, str(r3))
check('and the reason names fab_floor_origin so it can be fixed',
      'fab_floor_origin' in (r3.get('reason') or ''), str(r3))

print('--- the origin is seeded even when the first writeback changes nothing ---')

# The moment a first writeback happens to move nothing is the MOST valuable
# moment to record a baseline -- the floors are still the human's. The old code
# returned early there and threw it away.
_d4, _b4 = _stage('noop', rules={})
_pro4 = os.path.join(_d4, 'noop.kicad_pro')
with open(_pro4, 'w', encoding='utf-8') as fh:
    json.dump({'board': {'design_settings': {'rules': {
        'min_track_width': 0.15, 'min_clearance': 0.15,
        'min_via_annular_width': 0.075}}}}, fh)
_before = json.load(open(_pro4, encoding='utf-8'))
FK.fix_project_for_output(_b4, clearance=0.15, verbose=False)
_after = json.load(open(_pro4, encoding='utf-8'))
_org = (_after.get('kicad_routing_tools') or {}).get('fab_floor_origin') or {}
check('a writeback that changes nothing still records the origin',
      bool(_org),
      f'{_after.get("kicad_routing_tools")} -- the rules were already exactly '
      f'the routed values, so `changes` was empty and the function returned '
      f'before writing the baseline')
check('and the origin holds what the project declared, not what was routed',
      abs(_org.get('min_track_width', 0) - 0.15) < 1e-9, str(_org))
FK.fix_project_for_output(_b4, clearance=0.05, verbose=False)
_org2 = ((json.load(open(_pro4, encoding='utf-8')).get('kicad_routing_tools')
          or {}).get('fab_floor_origin') or {})
check('a second, LOWERING writeback does not overwrite it',
      _org2 == _org,
      f'{_org2} != {_org} -- the origin is the FIRST baseline, not the '
      f'previous step; overwriting it makes the ratchet invisible again')

print('--- check_drc adopts the origin for copper-to-hole, and only that ---')

_drc = os.path.join(REPO, 'py_router', 'check_drc.py')


def _drc_run(board, *extra):
    p = subprocess.run([sys.executable, _drc, board, '--max-print', '0']
                       + list(extra), capture_output=True, text=True, timeout=300)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


rc, out = _drc_run(_b)
check('the copper-to-hole floor comes from the origin, and says so',
      'Copper-to-hole clearance 0.254' in out and 'fab_floor_origin' in out,
      '; '.join(ln for ln in out.splitlines() if 'Copper-to-hole' in ln))
rc, out = _drc_run(_b, '--no-fab-floor-origin')
check('--no-fab-floor-origin restores grading at what the board declares TODAY',
      'fab_floor_origin' not in out, '; '.join(
          ln for ln in out.splitlines() if 'Copper-to-hole' in ln))

# The size floors must NOT follow the origin. On this board the origin declares
# min_track_width 0.2 and the copper is 0.15; if check_drc adopted it, that
# would be a TRACK-WIDTH violation. It must not be one -- 5629 of 5933 segments
# is what that looked like on run 7.
rc, out = _drc_run(_b)
check('the SIZE floors are deliberately not raised to the origin',
      'TRACK-WIDTH violations' not in out,
      'grading min_track_width at the origin on a stock-default board storms; '
      'that belongs at check_complete as one line with counts')

print('--- unmeasured resolves by REFERENCE to the drc component ---')

f = {'ran': True, 'relaxed': [], 'unmeasured': [
    {'key': 'min_hole_clearance', 'label': 'copper-to-hole clearance',
     'authored': 0.254},
    {'key': 'min_clearance', 'label': 'copper clearance', 'authored': 0.2}]}
CC._resolve_graded_elsewhere(f, {'components': {'drc': {
    'ran': True, 'by_type': {'track-hole': 36, 'pad-pad': 2}}}})
check('a key another instrument graded moves out of `unmeasured`',
      [x['key'] for x in f['unmeasured']] == ['min_clearance'], str(f))
check('and it carries that instrument\'s own count, not a re-measurement',
      f['graded_elsewhere'][0]['count'] == 36
      and f['graded_elsewhere'][0]['graded_by'] == 'check_drc',
      str(f.get('graded_elsewhere')))
check('it discloses that the FLOOR was not confirmed',
      f['graded_elsewhere'][0].get('floor_confirmed') is False,
      'the score payload carries no hole-clearance floor to confirm against; '
      'saying so is better than assuming it silently')

f2 = {'ran': True, 'relaxed': [], 'unmeasured': [
    {'key': 'min_hole_clearance', 'label': 'copper-to-hole clearance',
     'authored': 0.254}]}
CC._resolve_graded_elsewhere(f2, {'components': {'drc': {'ran': False}}})
check('when the drc component did NOT run it stays unmeasured, with a reason',
      len(f2['unmeasured']) == 1 and 'did not run' in f2['unmeasured'][0]['reason'],
      str(f2))
check('exactly one key is delegated, and to a named instrument',
      list(CC.FAB_FLOOR_KEYS_GRADED_BY_DRC) == ['min_hole_clearance'],
      str(CC.FAB_FLOOR_KEYS_GRADED_BY_DRC))

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
