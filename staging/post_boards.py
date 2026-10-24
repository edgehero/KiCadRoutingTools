#!/usr/bin/env python3
"""gpm: render the per-board <details> sections from _cmp/<stem>/summary.json, films.json and the
hand-written post_bullets.json, and splice them into the post templates (in copies: POST*.md are
never overwritten; writes POST*.rendered.md).

    python3 -X utf8 wk/gpm/_staging/post_boards.py

Templates: POST.md carries <!-- BOARDS_OLD --> (boards 01-14, gp14's set), POST_2.md carries
<!-- BOARDS_NEW --> (15-20) and POST_3.md the findings. Any <!-- KEY --> with a
_staging/post_<key>.md is filled from that file.
Links use the placeholders __RAW__ / __BLOB__ (asset branch, filled in after the push).
"""
import glob
import json
import os
import re

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
B = json.load(open(os.path.join(G, '_staging', 'post_bullets.json'), encoding='utf-8'))


def num(x, nd=None):
    if x is None:
        return '-'
    if nd is not None and isinstance(x, float):
        return f'{x:.{nd}f}'
    return f'{x}'


def wall(sec):
    if not sec:
        return '-'
    m = round(sec / 60)
    return f'{m // 60}h{m % 60:02d}'


def posediff(C):
    """'0 of 93 parts differ' / '1 of 264 differs: C92, moved by hand after place_simple'."""
    lines = [l for l in open(os.path.join(C, 'film_seed_posediff.txt'), encoding='utf-8').read().splitlines()
             if l.strip() and not l.startswith('WARNING')]
    m = re.match(r'(\d+) footprints, (\d+) differ', lines[0]) if lines else None
    if not m:
        return None
    n, k = int(m.group(1)), int(m.group(2))
    if k == 0:
        return f'the seed film reproduces the shipped seed exactly (0 of {n} parts differ)'
    refs = [l.split(':')[0].strip() for l in lines[1:] if ':' in l]
    return (f'the seed film reproduces the shipped seed except {", ".join(refs)}, '
            f'which the teammate moved by hand after `place_simple` (recorded in CHOSEN.json)')


def board(d):
    nn_stem = os.path.basename(d)
    nn, stem = nn_stem.split('_', 1)
    C = os.path.join(G, '_cmp', stem)
    s = json.load(open(os.path.join(C, 'summary.json')))
    fl = json.load(open(os.path.join(C, 'films.json')))
    o, h, c, po, ph = s['ours'], s['human'], s['control'], s['placement_ours'], s['placement_human']
    g14, f10 = s.get('gp14') or {}, s.get('fa10') or {}
    b = B[nn_stem]
    R = f'__RAW__/media/{nn_stem}'
    L = f'__BLOB__/media/{nn_stem}'
    out = [f'<details><summary><b>{nn} {stem}</b>: {b["result"]} &middot; {b["desc"]}</summary>\n']
    if fl.get('film_flow'):
        out.append('**movie3d `--route`**, the whole run: the 12 seeds, the judged seeds\' quick routes side by side, '
                   'the best one, then its full route:  ')
        out.append(f'[![{stem}: movie3d of the whole run]({R}/film_flow.gif)]({R}/film_flow.mp4)\n')
    out.append('**movie3d `--seed`**, the kept seed\'s anneal from the pile:  ')
    out.append(f'[![{stem}: movie3d of the kept seed]({R}/film_seed.gif)]({R}/film_seed.mp4)\n')
    notes = [p for p in [posediff(C)] if p]
    if not fl.get('film_flow'):
        why = next((p for p in ((fl.get('film_work') or {}).get('problems') or []) if 'would pick seed' in p), '')
        m = re.search(r'pick seed (\d+), the run kept seed (\d+)', why)
        if m:
            notes.append(f'no whole-run film: movie3d re-judges the seeds on their quick routes and would pick seed '
                         f'{m.group(1)}, but the run kept seed {m.group(2)}, so the film would end on a board that was '
                         f'not shipped')
    if notes:
        out.append('<sub>' + '; '.join(notes) + '.</sub>\n')
    out.append(f'[REPORT.md]({L}/REPORT.md) &middot; [TOOL_GAPS.md]({L}/TOOL_GAPS.md) '
               f'&middot; [what it was given]({L}/README.md) &middot; [grade]({L}/grade_ours.json)\n')
    out.append('| the pile it started from | what it shipped | the human board |')
    out.append('|---|---|---|')
    out.append(f'| ![start]({R}/iso_start.png) | ![ours]({R}/iso_final.png) | ![human]({R}/iso_ref.png) |\n')
    out.append(f'![human vs ours, front]({R}/compare_F.png)\n')
    has14, has10 = bool(g14), bool(f10)
    hdr = '| | main |' + (' gp14 |' if has14 else '') + (' fa10 |' if has10 else '') + \
          ' human | human placement, main\'s router (1 pass) |'
    out.append(hdr)
    out.append('|---|---:|' + ('---:|' if has14 else '') + ('---:|' if has10 else '') + '---:|---:|')

    def row(label, ov, gv, fv, hv, cv):
        return f'| {label} | {ov} |' + (f' {gv} |' if has14 else '') + (f' {fv} |' if has10 else '') + f' {hv} | {cv} |'
    out.append(row('blocking', o['blocking'], num(g14.get('blocking')), num(f10.get('blocking')), 'n/a',
                   num(c.get('blocking'))))
    out.append(row('vias', o['vias'], num(g14.get('vias')), num(f10.get('vias')), num(h['vias']), num(c.get('vias'))))
    out.append(row('copper mm', o['copper_mm'], num(g14.get('copper_mm')), num(f10.get('copper_mm')),
                   num(h['copper_mm']), num(c.get('copper_mm'))))
    out.append(row('segments', o['segments'], num(g14.get('segments')), '-', num(h['segments']),
                   num(c.get('segments'))))
    out.append(row('airwire crossings', num(po.get('crossings')), '-', num(f10.get('crossings')),
                   num(ph.get('crossings')), ''))
    out.append(row('hpwl mm', num(po.get('hpwl'), 1), '-', '-', num(ph.get('hpwl'), 1), ''))
    out.append(row('teammate wall', wall(s['time_s'].get('wall_seconds')), wall(g14.get('wall_seconds')),
                   wall(f10.get('wall_seconds')), '', '') + '\n')
    for line in b['bullets']:
        out.append(f'- {line}')
    out.append('\n</details>\n')
    return int(nn), '\n'.join(out)


def result(x, ver=None):
    if not x:
        return '-'
    r = 'DONE' if x.get('done') else f'blocking {x.get("blocking")}'
    return f'{r} ({ver})' if ver else r


def mm(x):
    return '-' if x is None else f'{x:.0f}'


def table():
    rows = ['| # | board | result (verifier) | at the board\'s own rules | gp14 | fa10 | vias main / gp14 / human / control '
            '| copper mm main / gp14 / human | crossings main / human | wall main / gp14 |',
            '|---|---|---|---|---|---|---:|---:|---:|---:|']
    for d in ready:
        nn, stem = os.path.basename(d).split('_', 1)
        s = json.load(open(os.path.join(G, '_cmp', stem, 'summary.json')))
        o, h, c = s['ours'], s['human'], s['control']
        g14, f10 = s.get('gp14') or {}, s.get('fa10') or {}
        own = {'DONE': 'DONE', 'UNSOUND': 'below'}.get(o.get('check_complete_authored'), 'no') if o['done'] else '-'
        res = f'**{result(o, s.get("verifier"))}**' if o['done'] and s.get('verifier') == 'PASS' else result(o, s.get('verifier'))
        ctl = f'{c.get("vias")}' + ('' if c.get('done') else f' (blk {c.get("blocking")})')
        rows.append(f'| {nn} | {stem} | {res} | {own} | {result(g14, g14.get("verifier"))} | {result(f10)} '
                    f'| {o["vias"]} / {num(g14.get("vias"))} / {h["vias"]} / {ctl} '
                    f'| {mm(o["copper_mm"])} / {mm(g14.get("copper_mm"))} / {mm(h["copper_mm"])} '
                    f'| {num(s["placement_ours"].get("crossings"))} / {num(s["placement_human"].get("crossings"))} '
                    f'| {wall(s["time_s"].get("wall_seconds"))} / {wall(g14.get("wall_seconds"))} |')
    return '\n'.join(rows)


ready = [d for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*')))
         if os.path.isfile(os.path.join(G, '_cmp', os.path.basename(d)[3:], 'summary.json'))]
for d in sorted(set(glob.glob(os.path.join(G, '[0-9][0-9]_*'))) - set(ready)):
    print('NOT GRADED YET, left out:', os.path.basename(d))
boards = dict(board(d) for d in ready)
fill = {'BOARDS_OLD': '\n'.join(boards[n] for n in sorted(boards) if n <= 14),
        'BOARDS_NEW': '\n'.join(boards[n] for n in sorted(boards) if n > 14),
        'TABLE': table()}
for name in ('POST', 'POST_2', 'POST_3'):
    src = os.path.join(G, f'{name}.md')
    if not os.path.exists(src):
        continue
    text = open(src, encoding='utf-8').read()
    for key in re.findall(r'<!-- ([A-Z_0-9]+) -->', text):
        p = os.path.join(G, '_staging', f'post_{key.lower()}.md')
        if key in fill:
            text = text.replace(f'<!-- {key} -->', fill[key])
        elif os.path.exists(p):
            text = text.replace(f'<!-- {key} -->', open(p, encoding='utf-8').read().strip())
    open(os.path.join(G, f'{name}.rendered.md'), 'w', encoding='utf-8').write(text)
    left = re.findall(r'<!-- [A-Z_0-9]+ -->', text)
    print(f'wrote {name}.rendered.md: {len(text)} chars, placeholders left {left}')
