#!/usr/bin/env python3
"""Removing copper that is proven redundant -- and refusing the copper that is not.

`check_weird.py` is read-only by design, and `check_complete` gates on it. So a
board `route.py` had just routed 83/83 with DRC 0 and connectivity 0 reported
`weird_copper: not clean` (89 removable segments, 1 dangling via), L5 refused to
close on the instrument disagreement, and the finding named no tool that could
act on it. `clean_weird_copper.py` is that tool.

THE LESSON THIS FILE EXISTS TO PIN: per-segment redundancy does not compose.
Removing all 89 at once broke GND and /MOTOR_E_PHASE_B, because two
individually-redundant segments were jointly load-bearing -- drop either and the
other carries the net; drop both and it splits. So candidates are accepted ONE
AT A TIME against the copper as it stands, and a post-write connectivity gate
backstops that.

Measured on the real board (kicad_files/splitflap_driver.kicad_pcb, routed):
88 of 89 segments removed, 0 vias, connectivity unchanged on all 83 multi-pad
nets. The refusals are the interesting half -- 3 vias `check_weird` calls
"joins none" are each holding their net together, one of them 10 GND pads.

    python3 tests/test_clean_weird_copper.py
"""
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kicad_parser import parse_kicad_pcb                           # noqa: E402
import clean_weird_copper as CWC                                   # noqa: E402

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
_TOOL = os.path.join(REPO, 'py_router', 'clean_weird_copper.py')


def _parse(path):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return parse_kicad_pcb(path)


print('--- the scope is narrow, and stated ---')
check('only two categories are ever deleted',
      CWC.REMOVABLE_CATEGORIES == ('removable-segment', 'dangling-via'),
      f'{CWC.REMOVABLE_CATEGORIES} -- everything else check_weird reports is '
      f'either a real defect needing a decision or copper another pass owns')
_doc = CWC.__doc__ or ''
check('and the docstring says what it will NOT touch',
      'unsupported-via' in _doc and 'soft-joint' in _doc, _doc[:200])

print('--- a board with genuinely redundant copper ---')
# Two pads joined TWICE: a direct track and a parallel detour. Either is
# removable; both are not. That is the composition trap, in four segments.
_PAR = os.path.join(_D, 'parallel.kicad_pcb')
with open(_PAR, 'w', encoding='utf-8') as fh:
    fh.write(
        '(kicad_pcb (version 20260206) (generator test)\n'
        ' (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (44 "Edge.Cuts" user))\n'
        ' (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") (width 0.1))\n'
        ' (net 0 "") (net 1 "SIG")\n'
        ' (footprint "t:r" (layer "F.Cu") (at 10 15)\n'
        '  (property "Reference" "U1" (at 0 0) (layer "F.SilkS"))\n'
        '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net 1 "SIG")))\n'
        ' (footprint "t:r" (layer "F.Cu") (at 30 15)\n'
        '  (property "Reference" "U2" (at 0 0) (layer "F.SilkS"))\n'
        '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net 1 "SIG")))\n'
        # the direct path
        ' (segment (start 10 15) (end 30 15) (width 0.3) (layer "F.Cu") (net 1))\n'
        # a parallel detour joining the same two points
        ' (segment (start 10 15) (end 20 20) (width 0.3) (layer "F.Cu") (net 1))\n'
        ' (segment (start 20 20) (end 30 15) (width 0.3) (layer "F.Cu") (net 1))\n'
        ')')
_pcb = _parse(_PAR)
_segs, _vias, _keep, _refused = CWC.collect_removable(_pcb, tolerance=0.0)
check('redundant copper IS found',
      len(_segs) >= 1, f'{len(_segs)} segments, {len(_refused)} refused')
check('but NOT the whole redundant set -- the survivors still carry the net',
      len(_segs) < 3,
      f'{len(_segs)} of 3 -- taking every individually-redundant segment is '
      f'exactly the composition bug: all three are individually droppable and '
      f'the net needs one')

_before = CWC._conn_key(_pcb)
_out = os.path.join(_D, 'parallel_clean.kicad_pcb')
with redirect_stdout(io.StringIO()):
    _ns, _nv, _abort = CWC.clean_once(_PAR, _out)
check('the write is not aborted', not _abort, '')
check('and connectivity is IDENTICAL afterwards',
      CWC._conn_key(_parse(_out)) == _before,
      f'{CWC._conn_key(_parse(_out))} != {_before}')

print('--- a clean board is left exactly alone ---')
_CLEAN = os.path.join(_D, 'clean.kicad_pcb')
with open(_CLEAN, 'w', encoding='utf-8') as fh:
    fh.write(open(_PAR, encoding='utf-8').read()
             .replace(' (segment (start 10 15) (end 20 20) (width 0.3) '
                      '(layer "F.Cu") (net 1))\n', '')
             .replace(' (segment (start 20 20) (end 30 15) (width 0.3) '
                      '(layer "F.Cu") (net 1))\n', ''))
_s2, _v2, _k2, _r2 = CWC.collect_removable(_parse(_CLEAN), tolerance=0.0)
check('nothing is removed from a board with one path',
      not _s2 and not _v2, f'{len(_s2)} segs, {len(_v2)} vias')

print('--- --dry-run writes nothing ---')
_dry = os.path.join(_D, 'never.kicad_pcb')
p = subprocess.run([sys.executable, '-X', 'utf8', _TOOL, _PAR, _dry,
                    '--dry-run', '--tolerance', '0'],
                   capture_output=True, text=True, timeout=600)
check('exit 0 and no output board', p.returncode == 0
      and not os.path.isfile(_dry), f'rc={p.returncode}')
check('and it says what it would do',
      'DRY RUN' in (p.stdout or ''), (p.stdout or '')[-200:])

print('--- usage errors are exit 2, not a traceback ---')
p = subprocess.run([sys.executable, '-X', 'utf8', _TOOL, _PAR],
                   capture_output=True, text=True, timeout=600)
check('no output and no --in-place is refused',
      p.returncode == 2 and 'Traceback' not in (p.stdout + p.stderr),
      f'rc={p.returncode}')
p = subprocess.run([sys.executable, '-X', 'utf8', _TOOL,
                    os.path.join(_D, 'nope.kicad_pcb'), '--dry-run'],
                   capture_output=True, text=True, timeout=600)
check('a missing board is exit 2', p.returncode == 2, f'rc={p.returncode}')

print('--- the real board that produced the blocker ---')
_R = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
if os.path.isfile(_R):
    _w = os.path.join(_D, 'sf')
    os.makedirs(_w, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(REPO, 'py_router',
                                                 'copy_board.py'),
                    _R, os.path.join(_w, 'in.kicad_pcb')],
                   capture_output=True, text=True, timeout=600)
    r = subprocess.run([sys.executable, '-X', 'utf8',
                        os.path.join(REPO, 'py_router', 'route.py'),
                        os.path.join(_w, 'in.kicad_pcb'),
                        os.path.join(_w, 'routed.kicad_pcb'), '--nets', '*'],
                       capture_output=True, text=True, timeout=1800)
    if os.path.isfile(os.path.join(_w, 'routed.kicad_pcb')):
        _rb = os.path.join(_w, 'routed.kicad_pcb')
        _before_r = CWC._conn_key(_parse(_rb))
        _cb = os.path.join(_w, 'cleaned.kicad_pcb')
        buf = io.StringIO()
        with redirect_stdout(buf):
            _ns, _nv, _ab = CWC.clean_once(_rb, _cb)
        check('a real routed board yields a large safe removal',
              not _ab and _ns > 50, f'removed {_ns} segs, aborted={_ab}')
        check('and its connectivity is untouched',
              CWC._conn_key(_parse(_cb)) == _before_r,
              'the whole point: 83 multi-pad nets, none worse')
        check('the refusals are reported, not silently dropped',
              'REFUSED' in buf.getvalue(),
              buf.getvalue()[:300] + ' -- a finding that cannot be acted on is '
              'the shape of the original problem; hiding it recreates it')
        check('...and a refused dangling via is named as load-bearing',
              'would BREAK the net' in buf.getvalue(), buf.getvalue()[:400])
    else:
        check('the fixture board routed', False, (r.stdout or '')[-300:])
else:
    print('  (splitflap_driver absent -- corpus witness skipped)')

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
