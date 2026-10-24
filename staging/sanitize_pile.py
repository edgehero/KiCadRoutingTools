#!/usr/bin/env python3
"""gp14 staging (ported from fa10): remove what a pile still says about the human layout.

    python3 -B -X utf8 wk/gpm/_staging/sanitize_pile.py PILE.kicad_pcb [--dry-run] [--min-frac 0.25]

Two channels the staging verifier measured:

  * LOCAL ZONES. strip_copper_only keeps zone definitions, but a small pour
    drawn around a switching node or a power island outlines where the human
    put those parts (One-Air-Max: 54 parts located by zones under 0.3 % of the
    board). Zones whose polygon bounding box covers less than --min-frac of the
    board bounding box are dropped -- net pours and rule areas alike. Board-wide
    planes stay: which net pours where is design intent.
  * TEXT ANGLES. A footprint's text angle is stored as an absolute board
    angle, and the pile writer rotated each part to 0 while keeping the text's
    angle relative to it, so the pile's text angle is (human text angle - human
    rotation): an upright human label hands the human rotation back. Every
    `property` / `fp_text` angle inside a padded footprint is reset to 0.

Prints what it dropped and how many angles it reset.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests', 'stress'))
sys.path.insert(0, os.path.join(ROOT, 'py_router'))
from strip_copper_only import _forms  # noqa: E402

XY = re.compile(r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)')
AT3 = re.compile(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)')
NET = re.compile(r'\(net_name\s+"([^"]*)"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pile')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--min-frac', type=float, default=0.25)
    a = ap.parse_args()
    from kicad_parser import parse_kicad_pcb
    b = parse_kicad_pcb(a.pile).board_info.board_bounds
    board_area = (b[2] - b[0]) * (b[3] - b[1])
    text = open(a.pile, encoding='utf-8', newline='').read()
    forms = list(_forms(text))
    cuts, edits, kept, dropped = [], [], [], []
    padded = []
    for s, e, depth, head, _parent in forms:
        if depth == 1 and head == 'zone':
            body = text[s:e]
            poly = body.find('(polygon')
            pts = [(float(x), float(y)) for x, y in XY.findall(body[poly:] if poly >= 0 else body)]
            if not pts:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            frac = (max(xs) - min(xs)) * (max(ys) - min(ys)) / board_area
            m = NET.search(body)
            kind = 'rule area' if ('(keepout' in body or '(placement' in body) else 'pour'
            label = f'{kind} {m.group(1) if m else "-"} ({100 * frac:.2f}% of the board)'
            if frac < a.min_frac:
                cuts.append((s, e))
                dropped.append(label)
            else:
                kept.append(label)
        elif depth == 1 and head == 'footprint' and '(pad ' in text[s:e]:
            padded.append((s, e))
    for s, e, depth, head, _parent in forms:
        if depth == 2 and head in ('property', 'fp_text') and \
                any(ps <= s and e <= pe for ps, pe in padded):
            m = AT3.search(text, s, e)
            if m and m.end() <= e and float(m.group(3)) != 0.0:
                edits.append((m.start(3), m.end(3)))
    print(f'zones kept {len(kept)}: ' + '; '.join(kept))
    print(f'zones dropped {len(dropped)}: ' + '; '.join(dropped))
    print(f'text angles reset: {len(edits)}')
    if a.dry_run:
        return
    ops = sorted([(s, e, '') for s, e in cuts] + [(s, e, '0') for s, e in edits])
    out, prev = [], 0
    for s, e, rep in ops:
        if s < prev:
            continue  # an angle inside a dropped zone (none expected)
        b0 = s
        if rep == '':
            while b0 > prev and text[b0 - 1] in ' \t':
                b0 -= 1
            if b0 > prev and text[b0 - 1] == '\n':
                b0 -= 1
        out.append(text[prev:b0])
        out.append(rep)
        prev = e
    out.append(text[prev:])
    with open(a.pile, 'w', encoding='utf-8', newline='') as f:
        f.write(''.join(out))


if __name__ == '__main__':
    main()
