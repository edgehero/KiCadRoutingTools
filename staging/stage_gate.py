#!/usr/bin/env python3
"""gpm staging gate (ported from gp14): a staged board must carry nothing of the human layout.

    python3 -X utf8 wk/gpm/_staging/stage_gate.py BOARD_DIR STEM [--human HUMAN.kicad_pcb] [--json OUT]

Every count below must be 0, or the gate exits 2:

  copper          top-level segment / arc / via forms
  fills           filled_polygon forms (zone fills)
  teardrops       teardrop zones
  tuning          (generated ...) tuning patterns
  drawings        board-level text, dimensions and graphics off Edge.Cuts
  artwork         padless footprints that draw no Edge.Cuts
  locked          locked footprints (parser), and `(locked yes)` on any footprint
  on_board        footprints with pads whose pad copper touches the board bounds
  text_angles     property / fp_text angles != 0 inside footprints with pads
  leaks           source-path markers in any input file of BOARD_DIR
  pads_turned     with --human: footprints whose pads turned against their body
                  between the human board and the pile (gp14 finding #8, #1305)

and two load checks: pcbnew (KiCad's bundled python) loads the board with the
same footprint count, and `kicad-cli pcb drc` runs on it.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
for sub in ('tests/stress', 'py_router'):
    sys.path.insert(0, os.path.join(ROOT, sub))
from strip_copper_only import _forms  # noqa: E402
from kicad_parser import parse_kicad_pcb  # noqa: E402
sys.path.insert(0, HERE)
from pile_pad_check import turned  # noqa: E402

KICAD_PY = '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
EDGE = re.compile(r'\(layer\s+"?Edge\.Cuts"?\s*\)')
AT3 = re.compile(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)')
TEXT = {'gr_text', 'gr_text_box', 'dimension', 'table', 'barcode'}
GRAPHIC = {'gr_line', 'gr_rect', 'gr_circle', 'gr_arc', 'gr_poly', 'gr_curve',
           'gr_bbox', 'gr_vector', 'image', 'target'}
MARKERS = ('_truth', '_src/', 'kicad_dmg', '/demos/', 'human_stripped', 'human.kicad_pcb',
           '~', 'kicad_stress_test', 'krt-run')


def census(path):
    text = open(path, encoding='utf-8', newline='').read()
    forms = list(_forms(text))
    padded = []
    c = dict(copper=0, fills=0, teardrops=0, tuning=0, drawings=0, artwork=0,
             locked_text=0, locked_pads=0, text_angles=0)
    c['locked_pads'] = len(re.findall(r'\(pad "[^"]*" \S+ \S+ locked(?=[\s)])', text))
    for s, e, d, h, _p in forms:
        body = text[s:e] if d <= 2 else ''
        if d == 1 and h in ('segment', 'arc', 'via'):
            c['copper'] += 1
        elif h == 'filled_polygon':
            c['fills'] += 1
        elif d == 1 and h == 'zone' and '(teardrop' in body:
            c['teardrops'] += 1
        elif d == 1 and h == 'generated':
            c['tuning'] += 1
        elif d == 1 and (h in TEXT or (h in GRAPHIC and not EDGE.search(body))):
            c['drawings'] += 1
        elif d >= 3 and h == 'locked':
            c['locked_pads'] += 1
        elif d == 1 and h == 'footprint':
            if '(pad ' in body:
                padded.append((s, e))
            elif not EDGE.search(body):
                c['artwork'] += 1
            head = body[:body.find('(property') if '(property' in body else 400]
            if re.search(r'\(locked(\s+yes)?\s*\)|\slocked\s', head):
                c['locked_text'] += 1
    for s, e, d, h, _p in forms:
        if d == 2 and h in ('property', 'fp_text') and any(ps <= s and e <= pe for ps, pe in padded):
            m = AT3.search(text, s, e)
            if m and m.end() <= e and float(m.group(3)) != 0.0:
                c['text_angles'] += 1
    return c


def on_board(pcb):
    b = pcb.board_info.board_bounds
    out = []
    for ref, fp in pcb.footprints.items():
        for p in fp.pads:
            hx, hy = (p.size_x or 0) / 2, (p.size_y or 0) / 2
            if (p.global_x + hx > b[0] and p.global_x - hx < b[2]
                    and p.global_y + hy > b[1] and p.global_y - hy < b[3]):
                out.append(ref)
                break
    return sorted(out)


def leaks(board_dir):
    hits = []
    for f in sorted(glob.glob(os.path.join(board_dir, '*'))):
        if not os.path.isfile(f) or f.endswith('README.md'):
            continue
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for m in MARKERS:
            if m in t:
                hits.append(f'{os.path.basename(f)}: {m}')
    return hits


def dir_hashes(board_dir):
    import hashlib
    return {n: hashlib.sha256(open(os.path.join(board_dir, n), 'rb').read()).hexdigest()
            for n in sorted(os.listdir(board_dir)) if os.path.isfile(os.path.join(board_dir, n))}


def load_checks(path, n_fp):
    """Load a COPY: kicad-cli writes a .kicad_prl (and may rewrite the
    .kicad_pro) beside the board it opens, which must not touch the inputs."""
    with tempfile.TemporaryDirectory() as td:
        stem = os.path.splitext(os.path.basename(path))[0]
        for f in glob.glob(os.path.join(os.path.dirname(path), stem + '.*')):
            shutil.copy2(f, td)
        tmp = os.path.join(td, stem + '.kicad_pcb')
        r = subprocess.run([KICAD_PY, '-c', 'import pcbnew,sys; b=pcbnew.LoadBoard(sys.argv[1]); '
                            'print(len(b.GetFootprints()))', tmp], capture_output=True, text=True)
        lines = [ln for ln in r.stdout.split() if ln.isdigit()]
        pcbnew_n = int(lines[-1]) if lines else None
        d = subprocess.run([KICAD_CLI, 'pcb', 'drc', '--format', 'json', '-o',
                            os.path.join(td, 'drc.json'), tmp], capture_output=True, text=True)
    return {'pcbnew_footprints': pcbnew_n, 'parser_footprints': n_fp,
            'pcbnew_ok': pcbnew_n == n_fp, 'kicad_cli_drc_exit': d.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board_dir')
    ap.add_argument('stem')
    ap.add_argument('--human', help='the board the pile was made from, for pads_turned')
    ap.add_argument('--json')
    a = ap.parse_args()
    path = os.path.join(a.board_dir, a.stem + '.kicad_pcb')
    c = census(path)
    pcb = parse_kicad_pcb(path)
    c['locked'] = sum(1 for fp in pcb.footprints.values() if getattr(fp, 'locked', False))
    ob = on_board(pcb)
    c['on_board'] = len(ob)
    pt = []
    if a.human:
        _n, pt, _lk = turned(a.human, path)
        c['pads_turned'] = len(pt)
    lk = leaks(a.board_dir)
    c['leaks'] = len(lk)
    before = dir_hashes(a.board_dir)
    lc = load_checks(path, len(pcb.footprints))
    c['gate_touched_inputs'] = int(dir_hashes(a.board_dir) != before)
    bad = {k: v for k, v in c.items() if v}
    if not lc['pcbnew_ok'] or lc['kicad_cli_drc_exit'] != 0:
        bad['load'] = lc
    verdict = 'PASS' if not bad else 'FAIL'
    doc = {'stem': a.stem, 'verdict': verdict, 'counts': c, 'on_board_refs': ob,
           'pads_turned_refs': [list(map(str, b[:3])) for b in pt],
           'leak_hits': lk, 'load': lc, 'footprints': len(pcb.footprints)}
    print(f'stage_gate {a.stem}: {verdict} ' + json.dumps(c) + ' load ' + json.dumps(lc))
    if ob:
        print('  on board:', ob[:20])
    if pt:
        print('  pads turned:', pt[:8])
    if lk:
        print('  leaks:', lk[:20])
    if a.json:
        json.dump(doc, open(a.json, 'w'), indent=2)
    sys.exit(0 if verdict == 'PASS' else 2)


if __name__ == '__main__':
    main()
