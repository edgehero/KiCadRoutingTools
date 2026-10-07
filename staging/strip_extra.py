#!/usr/bin/env python3
"""fa10 staging: drop the routing OUTPUT that strip_copper_only.py keeps.

    python3 -X utf8 wk/fa10/_staging/strip_extra.py BOARD.kicad_pcb   (in place)

strip_copper_only removes segments, arcs, vias and zone fills, but two more
top-level forms encode the human copper:

  * teardrop zones -- `(zone ... (attr (teardrop ...)))`, named
    `$teardrop_padvia$`: KiCad generates them from the tracks, and the parser
    reads them as net pours (complex_hierarchy has 165);
  * `(generated (type tuning_pattern) ...)` -- length-tuning meanders, whose
    `base_line` and `members` point at the deleted tracks (One-Air-Max 2, CM5 15).

Everything else is untouched. Prints what it dropped.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests', 'stress'))
from strip_copper_only import _forms  # noqa: E402


def strip(text):
    cuts, teardrops, tuning = [], 0, 0
    for s, e, depth, head in _forms(text):
        if depth != 1:
            continue
        body = text[s:e]
        if head == 'zone' and ('(teardrop' in body or '$teardrop' in body):
            cuts.append((s, e))
            teardrops += 1
        elif head == 'generated' and 'tuning_pattern' in body:
            cuts.append((s, e))
            tuning += 1
    cuts.sort()
    out, prev = [], 0
    for s, e in cuts:
        b = s
        while b > prev and text[b - 1] in ' \t':
            b -= 1
        if b > prev and text[b - 1] == '\n':
            b -= 1
        out.append(text[prev:b])
        prev = e
    out.append(text[prev:])
    return ''.join(out), teardrops, tuning


def main(path):
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read()
    new, td, tp = strip(text)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print(f'strip_extra: dropped {td} teardrop zone(s), {tp} tuning pattern(s)')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[3].strip())
    main(sys.argv[1])
