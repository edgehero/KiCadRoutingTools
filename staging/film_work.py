#!/usr/bin/env python3
"""gpm: build movie3d's flow work dir from a finished teammate folder, so the flow film re-routes nothing.

    python3 -X utf8 wk/gpm/_staging/film_work.py RUNDIR WORKDIR [--judge N]

`movie3d/make_movie.py ... --route NAME:SET --route-work WORKDIR` runs
`place_movie.run_flow`, which reuses whatever WORKDIR already holds:

  s<S>.kicad_pcb, s<S>.json            every seed's placement and report
  fast_s<S>/{in,out,manifest,score.json}  each judged seed's fast route
  full_s<best>/{in,out,manifest,score.json}  the best seed's full route

The teammate's folder has all of it under the skill's names (s<S>_route/,
s<S>_fast.score.json, final_route/), so this links it into that layout:
nothing is placed or routed again, and `NAME:SET` is never read.

`--judge` defaults to the number of seeds the run actually fast-routed
(s<S>_fast.score.json present for a seed judge.json names): the skill
judges only the clean seeds, or one hand-repaired seed alone, so the film
judges the same ones -- valid only when they are the FIRST N of the
judge order. Pass the printed `judge` on to make_movie's `--judge`.

The film can only tell the run's story if run_flow picks the seed the run
kept. It re-derives the judged seeds (`place_simple.judge_order` over the
s<S>.json reports) and the best (`quick_score.judge_key` over the fast
scores) exactly as the film will, and exits 3, naming the mismatch, when
either disagrees with judge.json / CHOSEN.json. films.sh then ships the
seed film only.

Exit 0 = work dir ready; 3 = the film would tell a different story; 2 = inputs missing.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
for sub in ('py_placer', 'py_tools', 'py_router'):
    sys.path.insert(0, os.path.join(ROOT, sub))


def link(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    os.symlink(os.path.abspath(src), dst)


def link_board(src, dst_dir, name=None):
    """A board plus its same-stem siblings (.kicad_pro/.kicad_dru/_routetrace.json/.design-brief.json)."""
    stem = os.path.splitext(os.path.basename(src))[0]
    new = os.path.splitext(name)[0] if name else stem
    for f in glob.glob(os.path.join(os.path.dirname(src), glob.escape(stem) + '*')):
        rest = os.path.basename(f)[len(stem):]
        if rest == '.kicad_pcb' or rest in ('.kicad_pro', '.kicad_dru', '_routetrace.json', '.design-brief.json'):
            link(f, os.path.join(dst_dir, new + rest))


def seed_dir(run, chosen):
    """The folder holding the kept pass's seeds: the run folder, or old/pass<K>/ for an earlier pass."""
    k = chosen.get('pass')
    old = os.path.join(run, 'old', f'pass{k}')
    if k is not None and os.path.isfile(os.path.join(old, 'judge.json')) \
            and not os.path.isfile(os.path.join(run, 'judge.json')):
        return old
    return run


def fast_chain(sdir, s, work):
    """fast_s<S>/ from judge_seeds' s<S>_route/: in/in.kicad_pcb, out/<N>_<script>.kicad_pcb,
    and a manifest naming them in step order (judge_seeds records none)."""
    r = os.path.join(sdir, f's{s}_route')
    sc = os.path.join(sdir, f's{s}_fast.score.json')
    if not (os.path.isfile(os.path.join(r, 'in.kicad_pcb')) and os.path.isfile(sc)):
        return False
    d = os.path.join(work, f'fast_s{s}')
    link_board(os.path.join(r, 'in.kicad_pcb'), os.path.join(d, 'in'))
    steps = sorted((b for b in glob.glob(os.path.join(r, '*.kicad_pcb'))
                    if re.match(r'\d+_', os.path.basename(b))),
                   key=lambda b: int(os.path.basename(b).split('_', 1)[0]))
    lines, prev = ['#!/bin/bash', '# synthesized by gpm film_work.py from judge_seeds step order'], 'in.kicad_pcb'
    for b in steps:
        link_board(b, os.path.join(d, 'out'))
        lines.append(f'python3 step.py {prev} {os.path.basename(b)}')
        prev = os.path.basename(b)
    os.makedirs(os.path.join(d, 'manifest'), exist_ok=True)
    open(os.path.join(d, 'manifest', 'redo_commands.sh'), 'w').write('\n'.join(lines) + '\n')
    link(sc, os.path.join(d, 'score.json'))
    return True


def full_chain(run, best, sdir, work, intent):
    fr = os.path.join(run, 'final_route')
    man = os.path.join(fr, 'redo_commands.sh')
    if not (os.path.isfile(os.path.join(fr, 'in.kicad_pcb')) and os.path.isfile(man)):
        return None, 'final_route/in.kicad_pcb or redo_commands.sh missing'
    d = os.path.join(work, f'full_s{best}')
    link_board(os.path.join(fr, 'in.kicad_pcb'), os.path.join(d, 'in'))
    for b in glob.glob(os.path.join(fr, '*.kicad_pcb')):
        if os.path.basename(b) != 'in.kicad_pcb':
            link_board(b, os.path.join(d, 'out'))
    os.makedirs(os.path.join(d, 'manifest'), exist_ok=True)
    link(man, os.path.join(d, 'manifest', 'redo_commands.sh'))
    from route_movie import run_boards
    boards = [b for b in run_boards(os.path.join(d, 'out'), os.path.join(d, 'manifest', 'redo_commands.sh'))
              if os.path.basename(b) != 'in.kicad_pcb']
    if not boards:
        return None, 'final_route manifest names no board in final_route/'
    last = os.path.realpath(boards[-1])
    cmd = [sys.executable, '-X', 'utf8', os.path.join(ROOT, 'py_tools', 'board_score.py'), last,
           '--baseline', os.path.join(sdir, f's{best}.kicad_pcb'), '--json', os.path.join(d, 'score.json'), '--quiet']
    if intent:
        cmd[4:4] = ['--intent', intent]
    subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.isfile(os.path.join(d, 'score.json')):
        return None, f'board_score wrote no score for {last}'
    return last, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('run')
    ap.add_argument('work')
    ap.add_argument('--judge', type=int, default=0, help='0 = the number of seeds the run fast-routed')
    a = ap.parse_args()
    run = os.path.abspath(a.run)
    try:
        chosen = json.load(open(os.path.join(run, 'CHOSEN.json')))
    except (OSError, ValueError) as e:
        print(f'film_work: CHOSEN.json unreadable: {e}')
        return 2
    sdir = seed_dir(run, chosen)
    jpath = os.path.join(sdir, 'judge.json')
    if not os.path.isfile(jpath):
        print(f'film_work: no judge.json in {sdir}')
        return 2
    judge = json.load(open(jpath)).get('judge', [])
    os.makedirs(a.work, exist_ok=True)
    reps = {}
    for rep in glob.glob(os.path.join(sdir, 's*.json')):
        m = re.fullmatch(r's(\d+)\.json', os.path.basename(rep))
        board = os.path.join(sdir, f's{m.group(1)}.kicad_pcb') if m else None
        if m and os.path.isfile(board):
            s = int(m.group(1))
            link(rep, os.path.join(a.work, f's{s}.json'))
            link_board(board, a.work)
            reps[s] = json.load(open(rep))
    from place_simple import judge_order
    from quick_score import judge_key
    order = judge_order(reps)
    routed = [s for s in judge if os.path.isfile(os.path.join(sdir, f's{s}_fast.score.json'))]
    # the shortest prefix of the judge order holding every seed the run fast-routed: a seed in it
    # that the run did not route (it could not repair it) has no fast route, and run_flow's own
    # attempt to route it fails at once (route_placed finds no corpus chain), so the film drops it
    n = a.judge or (max((order.index(s) for s in routed if s in order), default=-1) + 1) or 6
    film_judged = order[:n]
    skipped = [s for s in film_judged if s not in routed]
    fast = [s for s in film_judged if fast_chain(sdir, s, a.work)]
    scores = {s: json.load(open(os.path.join(a.work, f'fast_s{s}', 'score.json'))) for s in fast}
    best = min(scores, key=lambda s: judge_key(scores[s])) if scores else None
    seed = chosen.get('seed')
    intent = os.path.join(run, 'placed_from', chosen['intent']) if chosen.get('intent') else None
    problems = []
    if not a.judge and not set(routed) <= set(film_judged):
        problems.append(f'the run fast-routed {routed}, not all inside the judge order {order}')
    if skipped:
        problems.append(f'note: judged by order but not fast-routed by the run (it could not judge them): {skipped}')
    if order[:len(judge)] != judge:
        problems.append(f'judge order differs: film {order} vs judge.json {judge}')
    if set(fast) != set(routed) & set(film_judged):
        problems.append(f'fast routes missing for {sorted((set(routed) & set(film_judged)) - set(fast))}')
    if best != seed:
        problems.append(f'the film would pick seed {best}, the run kept seed {seed}')
    if chosen.get('after'):
        problems.append(f'note: the kept seed was hand-changed after place_simple: {chosen["after"]}')
    full, why = (None, 'no best seed') if best is None else full_chain(run, best, sdir, a.work, intent)
    if full is None:
        problems.append(f'full route not linked: {why}')
    else:
        shipped = os.path.join(run, 'routed.kicad_pcb')
        if os.path.isfile(shipped):
            import hashlib
            h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
            if h(shipped) != h(full):
                cu = lambda p: sum(1 for l in open(p, encoding='utf-8', errors='replace')
                                   if l.lstrip().startswith(('(segment', '(via', '(arc')))
                problems.append(f'note: the film ends on {os.path.basename(full)} (the manifest\'s last board); '
                                f'the shipped routed.kicad_pcb differs ({cu(full)} vs {cu(shipped)} copper items): '
                                f'steps after the manifest (hand joins, clean-up) are not filmed')
    summary = {'seed_dir': sdir, 'judge': n, 'judged': film_judged, 'run_routed': routed, 'skipped': skipped, 'fast_routed': fast, 'best': best, 'kept': seed,
               'full_route_last': full, 'problems': problems}
    print('JSON_SUMMARY: ' + json.dumps(summary))
    hard = [p for p in problems if not p.startswith('note:')]
    return 3 if hard else 0


if __name__ == '__main__':
    sys.exit(main())
