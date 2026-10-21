"""gp14 helper (TOOL_GAPS: place_simple's anneal prices a part with no
courtyard at its PAD box, while check_assembly grades its occupancy on the
drawn body -- so a placement place_simple calls legal reads NOT BUILDABLE
(12 courtyard-blocking pairs on r1/s8), and no repo tool repairs them).

For each gating courtyard pair (check_assembly --json, with --baseline), try
candidate nudges -- either movable member, four directions, distances from
the overlap depth upward -- and keep the first that place_pose accepts
(pad legality no worse) AND that check_assembly shows lowers the gating
count without adding a new pair.  Repeat until buildable or nothing helps.

usage: fix_courtyards.py IN OUT --intent I --baseline B [--fixed REF,...]
                         [--rounds N] [--log FILE]
The last line is a JSON summary with every pose set (for CHOSEN.json).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

WT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(WT, 'py_router'))
from kicad_parser import parse_kicad_pcb  # noqa: E402

PY = sys.executable
SIBS = ('.kicad_pro', '.kicad_prl', '.kicad_dru', '.design-brief.json')


def cp_board(src, dst):
    shutil.copyfile(src, dst)
    for ext in SIBS:
        s = src[:-10] + ext
        if os.path.exists(s):
            shutil.copyfile(s, dst[:-10] + ext)


def rm_board(p):
    for ext in ('.kicad_pcb',) + SIBS:
        q = p[:-10] + ext
        if os.path.exists(q):
            os.remove(q)


def run(cmd, log):
    r = subprocess.run(cmd, cwd=WT, capture_output=True, text=True)
    if log:
        with open(log, 'a', encoding='utf-8') as f:
            f.write('$ ' + ' '.join(cmd) + f'  [exit {r.returncode}]\n')
    return r


def grade(board, a):
    js = board + '.asm.json'
    run([PY, '-X', 'utf8', 'py_tools/check_assembly.py', board, '--intent', a.intent,
         '--baseline', a.baseline, '--json', js], a.log)
    with open(js, encoding='utf-8') as f:
        d = json.load(f)
    os.remove(js)
    pairs = d.get('courtyard_blocking_gating_pairs') or []
    return d, {(p['a'], p['b']): p for p in pairs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--intent', required=True); ap.add_argument('--baseline', required=True)
    ap.add_argument('--fixed', default='BAT1,I2C1,I2C2,LED2,SW1,USB1,U1,DC1,PWR_SW1')
    ap.add_argument('--rounds', type=int, default=3)
    ap.add_argument('--log', default=None)
    a = ap.parse_args()
    fixed = set(a.fixed.split(','))
    cur = a.out
    cp_board(a.inp, cur)
    tmp = cur[:-10] + '_try.kicad_pcb'
    moves = {}
    d, gp = grade(cur, a)
    print(f'start: buildable={d.get("buildable")} gating={len(gp)}')
    for rnd in range(a.rounds):
        if not gp:
            break
        progressed = False
        for key in list(gp):
            if key not in gp:
                continue
            p = gp[key]
            pcb = parse_kicad_pcb(cur)
            x0, y0, x1, y1 = p['overlap_rect']
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            w, h = x1 - x0, y1 - y0
            movers = [r for r in key if r not in fixed]
            movers.sort(key=lambda r: len(pcb.footprints[r].pads))
            cands = []
            for m in movers:
                fm = pcb.footprints[m]
                sx = 1.0 if fm.x >= cx else -1.0
                sy = 1.0 if fm.y >= cy else -1.0
                for extra in (0.15, 0.4, 0.8):
                    # away from the overlap first, along each axis, then the other ways
                    cands.append((m, fm.x + sx * (w + extra), fm.y, fm.rotation or 0.0))
                    cands.append((m, fm.x, fm.y + sy * (h + extra), fm.rotation or 0.0))
                for extra in (0.15, 0.6):
                    cands.append((m, fm.x - sx * (w + extra + (fm.x - cx) * 0), fm.y, fm.rotation or 0.0))
                    cands.append((m, fm.x, fm.y - sy * (h + extra), fm.rotation or 0.0))
            cands.sort(key=lambda c: abs(c[1] - pcb.footprints[c[0]].x) + abs(c[2] - pcb.footprints[c[0]].y))
            done = False
            for m, x, y, rot in cands[:10]:
                r = run([PY, '-X', 'utf8', 'py_placer/place_pose.py', cur, tmp,
                         'set', m, f'{x:.3f}', f'{y:.3f}', '--rot', str(rot)], a.log)
                if r.returncode != 0:
                    continue
                d2, gp2 = grade(tmp, a)
                new = set(gp2) - set(gp)
                if key not in gp2 and not new and len(gp2) < len(gp):
                    cp_board(tmp, cur)
                    moves[m] = (round(x, 3), round(y, 3), rot)
                    print(f'  {key}: set {m} {x:.3f} {y:.3f} rot {rot}  -> gating {len(gp2)}')
                    d, gp = d2, gp2
                    done = progressed = True
                    break
            rm_board(tmp)
            if not done:
                print(f'  {key}: no accepted nudge')
        if not progressed:
            break
    print(f'end: buildable={d.get("buildable")} gating={len(gp)} {sorted(gp)}')
    print('JSON_SUMMARY: ' + json.dumps({
        'buildable': d.get('buildable'), 'courtyard_blocking_gating': len(gp),
        'remaining': sorted(f'{a}<->{b}' for a, b in gp),
        'moves': {r: list(v) for r, v in moves.items()}}))


if __name__ == '__main__':
    main()
