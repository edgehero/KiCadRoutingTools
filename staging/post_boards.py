#!/usr/bin/env python3
"""gp14: render the per-board <details> sections of POST.md from _cmp/<stem>/summary.json,
fa10's metrics.json and a hand-written bullets file, and splice them into POST.md at
<!-- BOARDS --> (in a copy: POST.md is never overwritten; writes POST.rendered.md).

    python3 -X utf8 wk/gp14/_staging/post_boards.py

Links use the placeholders __RAW__ / __BLOB__ (asset branch, filled in after the push).
"""
import glob
import json
import os

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
fa10 = {b['board']: b for b in json.load(open(os.path.join(G, '_staging', 'fa10', 'metrics.json')))}
B = json.load(open(os.path.join(G, '_staging', 'post_bullets.json'), encoding='utf-8'))


def num(x, nd=None):
    if x is None:
        return '-'
    if nd is not None and isinstance(x, float):
        return f'{x:.{nd}f}'
    return f'{x}'


out = []
for d in sorted(glob.glob(os.path.join(G, '[0-9][0-9]_*'))):
    nn_stem = os.path.basename(d)
    nn, stem = nn_stem.split('_', 1)
    s = json.load(open(os.path.join(G, '_cmp', stem, 'summary.json')))
    o, h, c, po, ph = s['ours'], s['human'], s['control'], s['placement_ours'], s['placement_human']
    f = fa10.get(stem)
    fo = (f or {}).get('ours') or {}
    fp = (f or {}).get('placement_ours') or {}
    b = B[nn_stem]
    R = f'__RAW__/media/{nn_stem}'
    L = f'__BLOB__/media/{nn_stem}'
    out.append(f'<details><summary><b>{nn} {stem}</b>: {b["result"]} &middot; {b["desc"]}</summary>\n')
    out.append(f'[![{stem}: place_movie, then route_movie]({R}/film_andy.gif)]({R}/film_andy.mp4)  ')
    out.append(f'[3D film]({R}/film_3d.gif) ([mp4]({R}/film_3d.mp4)) '
               f'&middot; [fa10-style film]({R}/film.gif) &middot; [REPORT.md]({L}/REPORT.md) '
               f'&middot; [TOOL_GAPS.md]({L}/TOOL_GAPS.md) &middot; [what it was given]({L}/README.md)\n')
    out.append('| the pile it started from | what it shipped | the human board |')
    out.append('|---|---|---|')
    out.append(f'| ![start]({R}/iso_start.png) | ![ours]({R}/iso_final.png) | ![human]({R}/iso_ref.png) |\n')
    out.append(f'![human vs ours, front]({R}/compare_F.png)\n')
    fcol = f is not None
    hdr = '| | gp14 |' + (' fa10 |' if fcol else '') + ' human | human placement, our router (1 pass) |'
    out.append(hdr)
    out.append('|---|---:|' + ('---:|' if fcol else '') + '---:|---:|')

    def row(label, ov, fv, hv, cv):
        return f'| {label} | {ov} |' + (f' {fv} |' if fcol else '') + f' {hv} | {cv} |'
    out.append(row('blocking', o['blocking'], num(fo.get('blocking')), 'n/a', num(c.get('blocking'))))
    out.append(row('vias', o['vias'], num(fo.get('vias')), num(h['vias']), num(c.get('vias'))))
    out.append(row('copper mm', o['copper_mm'], num(fo.get('copper_mm')), num(h['copper_mm']), num(c.get('copper_mm'))))
    out.append(row('segments', o['segments'], num(fo.get('segments')), num(h['segments']), num(c.get('segments'))))
    out.append(row('airwire crossings', num(po.get('crossings')), num(fp.get('crossings')), num(ph.get('crossings')), ''))
    out.append(row('hpwl mm', num(po.get('hpwl'), 1), num(fp.get('hpwl'), 1), num(ph.get('hpwl'), 1), '') + '\n')
    for line in b['bullets']:
        out.append(f'- {line}')
    out.append('\n</details>\n')

post = open(os.path.join(G, 'POST.md'), encoding='utf-8').read()
post = post.replace('<!-- BOARDS -->', '\n'.join(out))
for key in ('FINDINGS', 'CAVEATS'):
    p = os.path.join(G, '_staging', f'post_{key.lower()}.md')
    if os.path.exists(p):
        post = post.replace(f'<!-- {key} -->', open(p, encoding='utf-8').read().strip())
open(os.path.join(G, 'POST.rendered.md'), 'w', encoding='utf-8').write(post)
print('wrote POST.rendered.md', len(post), 'chars')
p2 = open(os.path.join(G, 'POST_2.md'), encoding='utf-8').read()
p2 = p2.replace('<!-- FINDINGS -->', open(os.path.join(G, '_staging', 'post_findings.md'), encoding='utf-8').read().strip())
open(os.path.join(G, 'POST_2.rendered.md'), 'w', encoding='utf-8').write(p2)
print('wrote POST_2.rendered.md', len(p2), 'chars')
