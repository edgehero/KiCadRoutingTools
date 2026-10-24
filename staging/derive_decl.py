#!/usr/bin/env python3
"""gp14 staging (ported from fa10): derive what a designer knows BEFORE placing, by one rule.

    python3 -B -X utf8 wk/gpm/_staging/derive_decl.py HUMAN_STRIPPED.kicad_pcb \
        --stem STEM --out BOARD_DIR [--fix REF ...] [--why TEXT] [--json-out F]

Rule `fa10-decl-v1`, read off the HUMAN board, one channel per part:

  * mechanical.json `fixed[]` (exact x, y, rot): every part with pads that the
    human LOCKED, every `MountingHole*` footprint, every part that is a mounting hole by its
    drill (`_drilled_mount`, added after the gpm hole audit), and the per-board
    judgments passed with --fix (recorded with --why). The part still starts
    in the pile -- a declared pose is a target, not a placement.
  * <stem>.design-brief.json `interfaces[]` (EDGE only, along_edge unknown):
    every `edge_receptacle` / `edge_actuator` part and every DSUB that is not
    already posed, and only when its seat rect (the rect the grader reads,
    `reconcile._Geometry.seat_rect`) is within `part_class.SEAT_TOL_MM` of
    that edge or overhangs it. Otherwise it is listed as not claimed.

No mechanical.json is written when nothing is posed (an empty declaration
exits 2 in the loader). Prints the table the board README records.
"""
import argparse
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
for sub in ('py_router', 'py_placer', 'py_tools', ''):
    sys.path.insert(0, os.path.join(ROOT, sub))

from kicad_parser import parse_kicad_pcb  # noqa: E402
from placement.part_class import classify_part, SEAT_TOL_MM  # noqa: E402
from placement.reconcile import _Geometry  # noqa: E402

RULE = 'fa10-decl-v1'  # unchanged in gp14, so the declarations compare


def _fp_name(fp):
    return (fp.footprint_name or '').split(':')[-1]


def _drilled_mount(fp):
    """A mounting hole whatever its library calls it (environment_sensor's `MP_Pad5.4mm_Drill2.7mm`): at most
    9 pads, every one drilled >= 2.0 mm, and none on a signal net (no net, `unconnected-*`, or a GND net).
    Added 2026-10-24 after the mounting-hole audit; on the 20 gpm boards it adds exactly environment_sensor's
    MP1-MP3, which the name test alone missed."""
    pads = fp.pads
    return (bool(pads) and len(pads) <= 9 and all(p.drill and p.drill >= 2.0 for p in pads)
            and not any(p.net_name and not re.match(r'(unconnected-|.*GND)', p.net_name, re.I) for p in pads))


def derive(path, fix=(), why=''):
    pcb = parse_kicad_pcb(path)
    bounds = pcb.board_info.board_bounds
    geo = _Geometry(pcb, path)
    fixed, interfaces, rows = [], [], []
    for ref in sorted(pcb.footprints):
        fp = pcb.footprints[ref]
        if not fp.pads or ref.startswith('#'):
            continue
        cls = classify_part(fp, ref).name
        name = _fp_name(fp)
        reason = None
        if ref in fix:
            reason = f'{RULE} JUDGMENT: {why}'
        elif getattr(fp, 'locked', False):
            reason = f'{RULE}: locked in the human board'
        elif name.lower().startswith('mountinghole'):
            reason = f'{RULE}: MountingHole footprint'
        elif _drilled_mount(fp):
            reason = f'{RULE}: mounting part by drill (every pad drilled >= 2.0 mm, no signal net)'
        if reason:
            fixed.append({'ref': ref, 'x': round(fp.x, 4), 'y': round(fp.y, 4),
                          'rot': round((fp.rotation or 0.0) % 360.0, 3),
                          'reason': reason})
            rows.append((ref, 'mechanical.fixed', name, reason))
            continue
        is_dsub = 'dsub' in name.lower()
        if cls not in ('edge_receptacle', 'edge_actuator') and not is_dsub:
            continue
        entry = {'class': 'edge_receptacle' if is_dsub else cls}
        rect = geo.seat_rect(ref, entry)
        if rect is None or bounds is None:
            rows.append((ref, 'not claimed', name, 'no seat rect'))
            continue
        d = {'west': rect[0] - bounds[0], 'north': rect[1] - bounds[1],
             'east': bounds[2] - rect[2], 'south': bounds[3] - rect[3]}
        edge = min(d, key=d.get)
        if d[edge] > SEAT_TOL_MM:
            rows.append((ref, 'not claimed', name,
                         f'{cls}: nearest edge {edge} is {d[edge]:.2f} mm away '
                         f'(> {SEAT_TOL_MM})'))
            continue
        interfaces.append({'ref': ref, 'edge': edge, 'along_edge': 'unknown',
                           'why': f'{RULE}: {cls}{" (DSUB)" if is_dsub else ""}'
                                  f' seated at the {edge} edge in the source'})
        rows.append((ref, f'brief.edge={edge}', name,
                     f'{cls}, seat {d[edge]:.2f} mm from the edge'))
    missing = sorted(set(fix) - {f['ref'] for f in fixed})
    if missing:
        raise SystemExit(f'--fix names refs with no padded part: {missing}')
    return fixed, interfaces, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('human')
    ap.add_argument('--stem', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--fix', nargs='*', default=[])
    ap.add_argument('--why', default='')
    ap.add_argument('--json-out')
    a = ap.parse_args()
    if a.fix and not a.why:
        raise SystemExit('--fix needs --why: a judgment is recorded with its reason')
    fixed, interfaces, rows = derive(a.human, set(a.fix), a.why)
    os.makedirs(a.out, exist_ok=True)
    mech = os.path.join(a.out, 'mechanical.json')
    if fixed:
        with open(mech, 'w', encoding='utf-8') as f:
            json.dump({'schema': 1,
                       'fixed': fixed, 'context': {'rule': RULE}}, f, indent=2)
    elif os.path.exists(mech):
        os.remove(mech)
    brief = {'schema': 1, 'kind': 'design-brief', 'units': 'mm',
             'board': f'{a.stem}.kicad_pcb', 'interfaces': interfaces,
             'context': {'rule': RULE}}
    with open(os.path.join(a.out, f'{a.stem}.design-brief.json'), 'w',
              encoding='utf-8') as f:
        json.dump(brief, f, indent=2)
    print(f'{RULE}: {len(fixed)} posed, {len(interfaces)} edge claim(s)')
    print('| ref | channel | footprint | why |\n|---|---|---|---|')
    for r in rows:
        print('| %s | %s | %s | %s |' % r)
    if a.json_out:
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump({'rule': RULE, 'fixed': fixed, 'interfaces': interfaces,
                       'rows': rows}, f, indent=2)


if __name__ == '__main__':
    main()
