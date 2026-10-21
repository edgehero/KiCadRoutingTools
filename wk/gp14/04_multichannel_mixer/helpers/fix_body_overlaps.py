#!/usr/bin/env python3
"""Clear check_assembly's COURTYARD-BLOCKING pairs on a place_simple board.

Why this exists (TOOL_GAPS #1): place_simple's anneal keeps parts apart by
their courtyard, falling back to the PAD BOUNDING BOX for a footprint that
draws no courtyard. check_assembly grades the same parts by their drawn .Fab
body. On multichannel_mixer the 11 THT electrolytics (CAPPRB254-500X840: a
5 mm can on 2.54 mm pads) and J5 draw no courtyard, so every seed place_simple
calls legal is NOT BUILDABLE (3-7 can-on-can / can-on-jack overlaps per seed).
No repo tool legalises a body overlap, so this walks the movable member of
each gating pair away from the overlap with place_pose (`set REF --near X Y`,
which snaps to a pad-legal pose) and keeps a move only when check_assembly's
gating courtyard count (then its area) drops and nothing else gets worse.

Parts the intent seats (fixed_poses) are never moved. Every accepted move is
written to OUT.moves.json as place_pose ops, for CHOSEN.json's "after".

usage: fix_body_overlaps.py IN OUT --intent INTENT --baseline BASE [--clearance MM]
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
PY = sys.executable


def run(argv):
    r = subprocess.run([PY, '-X', 'utf8'] + argv, cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def copy_board(src, dst):
    rc, out = run(['py_router/copy_board.py', src, dst])
    if rc != 0:
        raise SystemExit(f'copy_board failed: {out[-500:]}')


CLEARANCE = []


def assembly(board, intent, baseline, tmpdir):
    js = os.path.join(tmpdir, 'asm.json')
    if os.path.exists(js):
        os.remove(js)
    rc, out = run(['py_tools/check_assembly.py', board, '--baseline', baseline,
                   '--intent', intent, '--json', js] + CLEARANCE)
    if not os.path.exists(js):
        raise SystemExit(f'check_assembly wrote no JSON (rc {rc}): {out[-800:]}')
    d = json.load(open(js))
    pairs = d.get('courtyard_blocking_gating_pairs') or []
    def n(v):
        return len(v) if isinstance(v, (list, dict)) else int(v or 0)
    other = (n(d.get('blocking')), n(d.get('hole_conflicts')), n(d.get('pad_conflicts')),
             n(d.get('oob_pad_copper_gating_count')), n(d.get('coincident_origins')),
             n(d.get('containment_blocking')))
    area = round(sum(p.get('area_mm2', 0.0) for p in pairs), 4)
    return d, pairs, (len(pairs), area), other


def poses(board):
    sys.path.insert(0, os.path.join(REPO, 'py_router'))
    from kicad_parser import parse_kicad_pcb
    p = parse_kicad_pcb(os.path.join(REPO, board) if not os.path.isabs(board) else board)
    return {r: (f.x, f.y, (f.rotation or 0.0) % 360.0) for r, f in p.footprints.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp')
    ap.add_argument('out')
    ap.add_argument('--intent', required=True)
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--max-moves', type=int, default=40)
    ap.add_argument('--clearance', type=float, default=None,
                    help='pad clearance for place_pose and check_assembly (both default to the '
                         'Default net class, 0.2 here, below the board min_clearance 0.3 that '
                         'check_drc / board_score grade at: TOOL_GAPS #3)')
    a = ap.parse_args()
    if a.clearance is not None:
        CLEARANCE.extend(['--clearance', str(a.clearance)])

    fixed = {fp['ref'] for fp in json.load(open(os.path.join(REPO, a.intent))).get('fixed_poses', [])}
    work = os.path.join(os.path.dirname(a.out), '_fixwork_' + os.path.basename(a.out).replace('.kicad_pcb', ''))
    os.makedirs(os.path.join(REPO, work), exist_ok=True)
    cur = os.path.join(work, 'cur.kicad_pcb')
    cand = os.path.join(work, 'cand.kicad_pcb')
    copy_board(a.inp, cur)
    d, pairs, score, other = assembly(cur, a.intent, a.baseline, os.path.join(REPO, work))
    print(f'start: {score[0]} gating courtyard pair(s), {score[1]} mm2; other blockers {other}')
    moves = []
    tried_fail = set()
    while pairs and len(moves) < a.max_moves:
        P = poses(cur)
        improved = False
        for pr in sorted(pairs, key=lambda q: -q.get('area_mm2', 0)):
            movers = [r for r in (pr['a'], pr['b']) if r not in fixed]
            if not movers:
                print(f"  pair {pr['a']}-{pr['b']}: both seated by the intent; cannot move")
                continue
            orc = pr.get('overlap_rect') or [0, 0, 0, 0]
            ocx, ocy = (orc[0] + orc[2]) / 2, (orc[1] + orc[3]) / 2
            depth = pr.get('depth_mm', 1.0)
            for m in movers:
                other_ref = pr['b'] if m == pr['a'] else pr['a']
                x, y, rot = P[m]
                vx, vy = x - ocx, y - ocy
                if math.hypot(vx, vy) < 1e-3:
                    ox, oy = P[other_ref][:2]
                    vx, vy = x - ox, y - oy
                if math.hypot(vx, vy) < 1e-3:
                    vx, vy = 1.0, 0.0
                base = math.atan2(vy, vx)
                # axis-aligned direction too: a pure x or y shift keeps rows tidy
                ax = math.atan2(0, 1 if vx >= 0 else -1) if abs(vx) >= abs(vy) else math.atan2(1 if vy >= 0 else -1, 0)
                dirs = [base, ax, base + math.pi / 4, base - math.pi / 4,
                        base + math.pi / 2, base - math.pi / 2]
                for dist in (depth + 0.35, depth + 0.9, depth + 1.6, depth + 2.6, depth + 4.0):
                    for th in dirs:
                        tx, ty = round(x + dist * math.cos(th), 3), round(y + dist * math.sin(th), 3)
                        key = (m, tx, ty)
                        if key in tried_fail:
                            continue
                        rc, out = run(['py_placer/place_pose.py', cur, cand, 'set', m,
                                       '--near', str(tx), str(ty), '--rot', str(rot)] + CLEARANCE)
                        if rc != 0:
                            tried_fail.add(key)
                            continue
                        d2, pairs2, score2, other2 = assembly(cand, a.intent, a.baseline, os.path.join(REPO, work))
                        if other2 <= other and (score2 < score):
                            Pn = poses(cand)
                            nx, ny, nr = Pn[m]
                            moves.append({'ref': m, 'from': [x, y, rot], 'to': [round(nx, 4), round(ny, 4), nr],
                                          'pair': [pr['a'], pr['b']], 'score_after': list(score2)})
                            print(f"  moved {m} ({x:.3f},{y:.3f}) -> ({nx:.3f},{ny:.3f}) for {pr['a']}-{pr['b']}: "
                                  f"{score} -> {score2}")
                            copy_board(cand, cur)
                            d, pairs, score, other = d2, pairs2, score2, other2
                            improved = True
                            break
                        tried_fail.add(key)
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
        if not improved:
            print('  no candidate move improves the remaining pairs')
            break
    copy_board(cur, a.out)
    with open(os.path.join(REPO, a.out.replace('.kicad_pcb', '.moves.json')), 'w') as f:
        json.dump({'input': a.inp, 'moves': moves, 'final_score': list(score),
                   'remaining': [[q['a'], q['b'], q.get('area_mm2')] for q in pairs],
                   'buildable': d.get('buildable'), 'verdict': d.get('verdict')}, f, indent=1)
    shutil.rmtree(os.path.join(REPO, work), ignore_errors=True)
    print(f"end: {score[0]} gating pair(s), {score[1]} mm2; verdict {d.get('verdict')}; {len(moves)} move(s)")
    print('JSON_SUMMARY: ' + json.dumps({'out': a.out, 'moves': len(moves), 'remaining': score[0],
                                         'buildable': d.get('buildable')}))
    return 0 if d.get('buildable') else 4


if __name__ == '__main__':
    sys.exit(main())
