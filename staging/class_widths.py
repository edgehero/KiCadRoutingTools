#!/usr/bin/env python3
"""gp14: grade a routed board against its project's declared non-Default net-class track widths.

    python3 -X utf8 wk/gp14/_staging/class_widths.py PROJECT.kicad_pro BOARD.kicad_pcb OUT_DIR

Builds {net: width} for every net in a class whose track_width exceeds Default's (KiCad 6 `nets`
lists and KiCad 7+ `netclass_patterns` globs, resolved against BOARD's nets), writes
OUT_DIR/class_widths.json, runs board_score --net-min-widths on BOARD, and prints the
net_widths component. KiCad's own DRC does not enforce net-class widths; this is a
supplementary grade.
"""
import fnmatch
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'py_router')]
from kicad_parser import parse_kicad_pcb  # noqa: E402

pro, board, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
ns = json.load(open(pro)).get('net_settings', {})
cls = {c['name']: c for c in ns.get('classes', [])}
dw = (cls.get('Default') or {}).get('track_width') or 0
wide = {n: c['track_width'] for n, c in cls.items() if n != 'Default' and (c.get('track_width') or 0) > dw}
nets = [n.name for n in parse_kicad_pcb(board).nets.values() if n.name]
w = {}
for n, c in cls.items():
    if n in wide:
        for net in c.get('nets') or []:
            w[net] = wide[n]
for p in ns.get('netclass_patterns') or []:
    if p.get('netclass') in wide:
        for net in fnmatch.filter(nets, p.get('pattern', '')):
            w.setdefault(net, wide[p['netclass']])
for net, c in (ns.get('netclass_assignments') or {}).items():
    if isinstance(c, str) and c in wide:
        w.setdefault(net, wide[c])
wj = os.path.join(out, 'class_widths.json')
json.dump(w, open(wj, 'w'), indent=1)
sj = os.path.join(out, 'class_widths_score.json')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'py_tools', 'board_score.py'), board,
                '--net-min-widths', wj, '--json', sj, '--quiet'], cwd=ROOT, capture_output=True)
c = (json.load(open(sj)).get('components') or {}).get('net_widths') or {}
short = {k: v for k, v in c.items() if k in ('count', 'graded', 'nets_under', 'under_mm', 'worst', 'status', 'nets')}
print(json.dumps({'classes': wide, 'nets_declared': len(w), 'net_widths': short})[:900])
