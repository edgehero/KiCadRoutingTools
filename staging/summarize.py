#!/usr/bin/env python3
"""gpm: one summary per compared board, and the campaign table (gp14's summarize.py + gp14 / fa10 / verifier columns).

    python3 -X utf8 wk/gpm/_staging/summarize.py            # every board with a _cmp/<stem>/grade_ours.json

Reads only Phase-4 outputs (_cmp/<stem>/, _control/<stem>/). Writes
_cmp/<stem>/summary.json, _cmp/metrics.json, and prints the markdown table.
"""
import glob
import json
import os
import re

FA = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load(p):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def comparison(p):
    try:
        t = open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return None
    m = re.search(r'^JSON_COMPARISON: (.*)$', t, re.M)
    return json.loads(m.group(1)) if m else None


def placement(render):
    if not render:
        return {}
    m = render.get('metrics') or {}
    return {k: m.get(k) for k in ('crossings', 'hpwl', 'overlap_area', 'pad_conflict_pairs', 'oob_count') if k in m}


def verdict(d):
    vs = sorted(glob.glob(os.path.join(d, 'verdict_[0-9].txt')) + glob.glob(os.path.join(d, 'verdict_[0-9][0-9].txt')))
    if not vs:
        return None
    t = open(vs[-1], encoding='utf-8', errors='replace').read()
    m = re.findall(r'VERDICT\s*[=:]\s*(PASS|FAIL)', t)
    return m[-1] if m else None


def main():
    fa10 = {b['board']: b for b in (load(os.path.join(FA, '_staging', 'fa10', 'metrics.json')) or [])}
    gp14 = {b['board']: b for b in (load(os.path.join(FA, '_staging', 'gp14', 'metrics.json')) or [])}
    rows = []
    for d in sorted(glob.glob(os.path.join(FA, '[0-9][0-9]_*'))):
        nn, stem = os.path.basename(d).split('_', 1)
        C = os.path.join(FA, '_cmp', stem)
        g = load(os.path.join(C, 'grade_ours.json'))
        if not g:
            continue
        ctl = load(os.path.join(FA, '_control', stem, 'grade_control.json')) or {}
        hum = comparison(os.path.join(C, 'compare_to_human.txt')) or {}
        ctlc = comparison(os.path.join(C, 'control_to_human.txt')) or {}
        meas = (load(os.path.join(C, 'measure.json')) or {}).get('main') or {}
        bs = load(os.path.join(C, 'board_score.json')) or {}
        o = hum.get('original') or {}
        s = {
            'board': stem, 'nn': nn,
            'ours': {k: g.get(k) for k in ('done', 'blocking', 'unrouted', 'broken', 'drc', 'vias', 'copper_mm',
                                           'segments', 'crossings', 'hpwl', 'check_complete',
                                           'check_complete_authored', 'buildable')}
                    | {'joins_needed': bs.get('joins_needed'), 'blocking_by': bs.get('blocking_by')},
            'human': {'vias': o.get('n_vias'), 'copper_mm': o.get('total_length_mm'), 'segments': o.get('n_segments')},
            'control': {k: ctl.get(k) for k in ('done', 'blocking', 'unrouted', 'broken', 'vias', 'copper_mm',
                                                'segments', 'check_complete')},
            'placement_ours': placement(load(os.path.join(C, 'place_ours_render.json'))),
            'placement_human': placement(load(os.path.join(C, 'place_human_render.json'))),
            'time_s': {k: meas.get(k) for k in ('wall_seconds', 'waiting_on_jobs_seconds', 'other_tool_seconds',
                                                'model_seconds')},
            'design_clearance': hum.get('design_clearance'),
            'verifier': verdict(d),
            'fa10': {k: ((fa10.get(stem) or {}).get('ours') or {}).get(k) for k in ('done', 'blocking', 'vias', 'copper_mm', 'crossings')}
                    | {'wall_seconds': ((fa10.get(stem) or {}).get('time_s') or {}).get('wall_seconds')} if stem in fa10 else None,
            'gp14': {k: ((gp14.get(stem) or {}).get('ours') or {}).get(k) for k in ('done', 'blocking', 'vias', 'copper_mm', 'segments')}
                    | {'wall_seconds': ((gp14.get(stem) or {}).get('time_s') or {}).get('wall_seconds'),
                       'verifier': (gp14.get(stem) or {}).get('verifier')} if stem in gp14 else None,
            'control_vs_human': {'vias': (ctlc.get('ours') or {}).get('n_vias'),
                                 'copper_mm': (ctlc.get('ours') or {}).get('total_length_mm')},
        }
        with open(os.path.join(C, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2)
        rows.append(s)
    with open(os.path.join(FA, '_cmp', 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)

    def h(x):
        return '-' if x is None else (f'{x / 3600:.1f} h' if x >= 3600 else f'{x / 60:.0f} min')
    print('| # | board | result (verifier) | gp14 | fa10 | vias ours / gp14 / human / control | copper mm ours / gp14 / human / control '
          '| crossings ours / human | wall ours / gp14 | agent / tools / waiting |')
    print('|---|---|---|---|---|---|---|---|---|---|')

    def res(x, ver=None):
        if not x:
            return '-'
        return ('DONE' if x.get('done') else f"blocking {x.get('blocking')}") + (f" ({ver})" if ver else '')
    for s in rows:
        o, hu, c, po, ph, t = s['ours'], s['human'], s['control'], s['placement_ours'], s['placement_human'], s['time_s']
        gp, fa = s['gp14'] or {}, s['fa10'] or {}
        cres = '' if c.get('blocking') in (None, 0) else f" (ctl blocking {c['blocking']})"
        print(f"| {s['nn']} | {s['board']} | {res(o, s['verifier'])} | {res(gp, gp.get('verifier'))} | {res(fa)} "
              f"| {o['vias']} / {gp.get('vias', '-')} / {hu['vias']} / {c.get('vias')}{cres} "
              f"| {o['copper_mm']} / {gp.get('copper_mm', '-')} / {hu['copper_mm']} / {c.get('copper_mm')} "
              f"| {po.get('crossings')} / {ph.get('crossings')} "
              f"| {h(t.get('wall_seconds'))} / {h(gp.get('wall_seconds'))} | {h(t.get('model_seconds'))} / {h(t.get('other_tool_seconds'))} / "
              f"{h(t.get('waiting_on_jobs_seconds'))} |")

if __name__ == '__main__':
    main()
