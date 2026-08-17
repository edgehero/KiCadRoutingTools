#!/usr/bin/env python3
"""Two footprints, one reference, and every tool says one part.

`PCBData.footprints` is a dict keyed by reference, so a second block with the
same reference silently REPLACES the first. Measured on wk/run20/board.kicad_pcb:
86 footprint blocks, 84 distinct references -- TP4 and TP5 each appear twice, at
exactly coincident positions.

The sharp end is `check_assembly`'s `coincident_origins`, the one check that
exists to catch two parts at one point. It read **0** on that board, because it
iterates the dict: the coincident partner was not there to be compared against.
A check cannot see a part the parser dropped.

Advisory, not blocking. A duplicate reference is legal in KiCad and can be
deliberate -- a paired testpoint, a net tie. It just must not be SILENT.

    python3 tests/test_run20_duplicate_refs.py
"""
import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kicad_parser import parse_kicad_pcb                           # noqa: E402

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

_FP = ('(footprint "t:tp" (layer "F.Cu") (at {x} {y})\n'
       '  (property "Reference" "{ref}" (at 0 0) (layer "F.SilkS"))\n'
       '  (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") '
       '(net {net} "N{net}")))\n')


def _board(name, blocks):
    body = ''.join(_FP.format(**b) for b in blocks)
    p = os.path.join(_D, name)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('(kicad_pcb (version 20260206) (generator test)\n'
                 ' (layers (0 "F.Cu" signal) (2 "B.Cu" signal) '
                 '(44 "Edge.Cuts" user))\n'
                 ' (gr_rect (start 0 0) (end 40 30) (layer "Edge.Cuts") '
                 '(width 0.1))\n (net 0 "") (net 1 "N1") (net 2 "N2")\n'
                 + body + ')')
    return p


# Two blocks, ONE reference, at exactly coincident positions -- the run-20 shape.
_DUP = _board('dup.kicad_pcb', [
    {'ref': 'TP4', 'x': 10, 'y': 10, 'net': 1},
    {'ref': 'TP4', 'x': 10, 'y': 10, 'net': 2},
    {'ref': 'R1', 'x': 20, 'y': 10, 'net': 1},
])
# The CONTROL, and it must not use TP* refs: check_assembly excludes marker
# classes (fiducial / mount_hole / testpoint) from `coincident_origins` by
# design, so a TP-only fixture would "prove" the check is blind for a reason
# that has nothing to do with the dict keying under test.
_CLEAN = _board('clean.kicad_pcb', [
    {'ref': 'U7', 'x': 10, 'y': 10, 'net': 1},
    {'ref': 'U8', 'x': 10, 'y': 10, 'net': 2},
    {'ref': 'R1', 'x': 20, 'y': 10, 'net': 1},
])
# ...and the ISOLATING case: the same two coincident parts, but sharing one
# reference. Same refs, same positions, same classes as _CLEAN -- the ONLY
# difference is the name, so a difference in `coincident_origins` between them
# is attributable to the dict keying and to nothing else.
_DUP_U = _board('dup_u.kicad_pcb', [
    {'ref': 'U7', 'x': 10, 'y': 10, 'net': 1},
    {'ref': 'U7', 'x': 10, 'y': 10, 'net': 2},
    {'ref': 'R1', 'x': 20, 'y': 10, 'net': 1},
])

print('--- the parser counts what it dropped ---')

buf = io.StringIO()
with redirect_stdout(buf):
    pcb = parse_kicad_pcb(_DUP)
out = buf.getvalue()
check('the duplicate is recorded on PCBData',
      pcb.duplicate_references == {'TP4': 2}, str(pcb.duplicate_references))
check('and the dict still holds only ONE entry for it -- unchanged behaviour',
      len(pcb.footprints) == 2 and 'TP4' in pcb.footprints,
      f'{sorted(pcb.footprints)} -- this is additive; nothing about how a '
      f'board parses changes')
check('the warning fires at parse time, where every tool will see it',
      'WARNING' in out and 'TP4 x2' in out, out[:400])
check('and it says what the count downstream will be short by',
      'short by 1' in out and '3 blocks' not in out, out[:400])

buf = io.StringIO()
with redirect_stdout(buf):
    pcb2 = parse_kicad_pcb(_CLEAN)
check('a board with distinct references records nothing and is silent',
      not pcb2.duplicate_references and 'DUPLICATE' not in buf.getvalue()
      and 'share' not in buf.getvalue(), str(pcb2.duplicate_references))

print('--- check_assembly names it, and says why it could not see it ---')

_CA = os.path.join(REPO, 'py_tools', 'check_assembly.py')
_JS = os.path.join(_D, 'a.json')
p = subprocess.run([sys.executable, '-X', 'utf8', _CA, _DUP, '--json', _JS],
                   capture_output=True, text=True, timeout=600)
o = (p.stdout or '') + (p.stderr or '')
check('the audit reports the duplicate', 'DUPLICATE REFERENCES' in o
      and 'TP4 x2' in o, o[:500])
check('as ADVISORY, not as a blocking finding',
      'advisory' in o.split('DUPLICATE REFERENCES')[1][:40], o[:500])
check('and it explains why coincident_origins cannot see it',
      'coincident_origins` cannot compare' in o, o[:800])

if os.path.isfile(_JS):
    d = json.load(open(_JS, encoding='utf-8'))
    check("the JSON carries duplicate_references",
          d.get('duplicate_references') == {'TP4': 2},
          str(d.get('duplicate_references')))
    check('and the block count, beside the part count',
          d.get('footprint_blocks') == 3,
          f"{d.get('footprint_blocks')} -- 3 blocks, 2 references")
    check('coincident_origins states its own basis',
          'distinct references only' in (d.get('coincident_origins_basis') or ''),
          str(d.get('coincident_origins_basis')))
    check('coincident_origins reads 0 here', d.get('coincident_origins') == 0,
          str(d.get('coincident_origins')))
else:
    check('check_assembly wrote its JSON', False, o[-300:])

# The clean board must gain nothing.
_JS2 = os.path.join(_D, 'b.json')
p = subprocess.run([sys.executable, '-X', 'utf8', _CA, _CLEAN, '--json', _JS2],
                   capture_output=True, text=True, timeout=600)
o2 = (p.stdout or '') + (p.stderr or '')
check('a board with distinct references gains no new finding',
      'DUPLICATE REFERENCES' not in o2, o2[:400])
if os.path.isfile(_JS2):
    d2 = json.load(open(_JS2, encoding='utf-8'))
    check('...and there coincident_origins DOES see the pair',
          d2.get('coincident_origins', 0) >= 1,
          f"{d2.get('coincident_origins')} -- two distinctly-named parts at "
          f"one point is exactly what that check is for, and it still works")

print('--- THE ISOLATING PAIR: same parts, same point, one name vs two ---')
_JS3 = os.path.join(_D, 'c.json')
subprocess.run([sys.executable, '-X', 'utf8', _CA, _DUP_U, '--json', _JS3],
               capture_output=True, text=True, timeout=600)
if os.path.isfile(_JS3) and os.path.isfile(_JS2):
    _two = json.load(open(_JS2, encoding='utf-8'))     # U7 + U8, coincident
    _one = json.load(open(_JS3, encoding='utf-8'))     # U7 + U7, coincident
    check('two coincident parts with DISTINCT names are caught',
          _two.get('coincident_origins', 0) >= 1,
          f"{_two.get('coincident_origins')} -- if this is 0 the fixture is "
          f"not exercising the check at all and the comparison below is void")
    check('the SAME two parts sharing one name are NOT -- the dict keying, '
          'isolated',
          _one.get('coincident_origins') == 0
          and _one.get('duplicate_references') == {'U7': 2},
          f"{_one.get('coincident_origins')} / "
          f"{_one.get('duplicate_references')} -- this is why the duplicate "
          f"needs its own channel: the check that would have caught it cannot "
          f"see the block the parser dropped")

print('--- and on the board that produced the finding ---')
_R20 = os.path.join(REPO, 'wk', 'run20', 'board.kicad_pcb')
if os.path.isfile(_R20):
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = parse_kicad_pcb(_R20)
    check('run 20: 86 blocks, 84 references, TP4 and TP5 duplicated',
          r.duplicate_references == {'TP4': 2, 'TP5': 2}
          and len(r.footprints) == 84,
          f'{r.duplicate_references}, {len(r.footprints)} parts')
else:
    print('  (wk/run20/board.kicad_pcb absent -- corpus witness skipped)')

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
