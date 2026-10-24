#!/usr/bin/env python3
"""Widen routed segments of named nets up to a minimum width, one at a time,
keeping only the widenings py_tools/check_join.py grades CLEAN against all
board copper.

Why a helper: board_score --net-min-widths grades a per-net minimum, but no
routing tool here can be told "never neck these nets below W": route.py necks a
power net to --track-width (or to the board floor under --escalation board) at
pad entries and in plane-finalize straps.

usage: widen_power.py IN.kicad_pcb OUT.kicad_pcb SPEC.json [--rounds N]
SPEC.json is the same {"<net>": <min mm>} file board_score reads.
"""
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'py_router'))
from kicad_parser import parse_kicad_pcb  # noqa: E402


def main():
    src, out, spec = sys.argv[1:4]
    rounds = int(sys.argv[sys.argv.index('--rounds') + 1]) if '--rounds' in sys.argv else 2
    want = {k: float(v) for k, v in json.load(open(spec)).items() if isinstance(v, (int, float))}
    # copy board + siblings via the repo tool so the .kicad_pro travels
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(REPO, 'py_router', 'copy_board.py'), src, out],
                   check=True, stdout=subprocess.DEVNULL)
    tmp = out[:-len('.kicad_pcb')] + '_probe.kicad_pcb'
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(REPO, 'py_router', 'copy_board.py'), src, tmp],
                   check=True, stdout=subprocess.DEVNULL)
    tried, widened = set(), []
    for rnd in range(rounds):
        pcb = parse_kicad_pcb(out)
        names = {n.net_id: n.name for n in pcb.nets.values()}
        cands = []
        for s in pcb.segments:
            nm = names.get(s.net_id)
            if nm in want and s.width < want[nm] - 1e-9 and s.uuid:
                cands.append((nm, s))
        if not cands:
            break
        accepted = 0
        for nm, s in cands:
            tried.add(s.uuid)
            w = want[nm]
            pts = [f"{s.start_x:.6f},{s.start_y:.6f},{s.layer}", f"{s.end_x:.6f},{s.end_y:.6f},{s.layer}"]
            text = open(out, encoding='utf-8').read()
            i = text.find(f'"{s.uuid}"')
            if i < 0:
                continue
            a = text.rfind('(segment', 0, i)
            depth, j = 0, a          # the whole (segment ...) block, to drop it in the probe
            while True:
                c = text[j]
                depth += (c == '(') - (c == ')')
                j += 1
                if depth == 0:
                    break
            open(tmp, 'w', encoding='utf-8').write(text[:a] + text[j:])
            r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(REPO, 'py_tools', 'check_join.py'),
                                tmp, nm] + pts + ['--width', str(w), '-q'],
                               capture_output=True, text=True)
            if r.returncode != 0 or 'CLEAN' not in r.stdout:
                continue
            blk = text[a:i]
            nb = re.sub(r'\(width [0-9.]+\)', f'(width {w})', blk, count=1)
            if nb == blk:
                continue
            open(out, 'w', encoding='utf-8').write(text[:a] + nb + text[i:])
            widened.append((nm, round(s.width, 3), round(math.hypot(s.end_x - s.start_x, s.end_y - s.start_y), 3),
                            round(s.start_x, 3), round(s.start_y, 3), s.layer))
            accepted += 1
        print(f'round {rnd}: {len(cands)} candidate(s), {accepted} widened', flush=True)
        if not accepted:
            break
    print('JSON_SUMMARY: ' + json.dumps({'widened': len(widened), 'tried': len(tried), 'rows': widened}))


if __name__ == '__main__':
    main()
