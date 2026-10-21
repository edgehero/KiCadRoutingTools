#!/usr/bin/env python3
"""gp14 staging: remove every board-level drawing except the outline.

    python3 -X utf8 wk/gp14/_staging/strip_drawings.py BOARD.kicad_pcb   (in place)

Drops these top-level forms:

  * text of any kind, on any layer: gr_text, gr_text_box, dimension, table,
    barcode;
  * graphics on every layer except Edge.Cuts: gr_line, gr_rect, gr_circle,
    gr_arc, gr_poly, gr_curve, gr_bbox, gr_vector, image, target. That covers
    silkscreen logos, fab/user/courtyard drawings and board copper graphics.

  * padless artwork footprints (logos, kibuzzard labels, QR codes): a
    footprint with no pad that draws no Edge.Cuts.

Edge.Cuts graphics stay, because they ARE the outline. Footprints with pads
are not touched; their own text and graphics are part of the part. A `group` loses the members
that were dropped; a group left with no members goes too. Prints a count per
kind and refuses (exit 2) if the outline would change.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests', 'stress'))
from strip_copper_only import _forms, _atoms  # noqa: E402

TEXT = {'gr_text', 'gr_text_box', 'dimension', 'table', 'barcode'}
GRAPHIC = {'gr_line', 'gr_rect', 'gr_circle', 'gr_arc', 'gr_poly', 'gr_curve',
           'gr_bbox', 'gr_vector', 'image', 'target'}
EDGE = re.compile(r'\(layer\s+"?Edge\.Cuts"?\s*\)')


def _cut_spans(text, spans):
    """Remove each (start, end) span with the indentation and newline before it."""
    out, prev = [], 0
    for s, e, rep in sorted(spans):
        if s < prev:
            continue
        b = s
        if rep == '':
            while b > prev and text[b - 1] in ' \t':
                b -= 1
            if b > prev and text[b - 1] == '\n':
                b -= 1
                if b > prev and text[b - 1] == '\r':
                    b -= 1
        out.append(text[prev:b])
        out.append(rep)
        prev = e
    out.append(text[prev:])
    return ''.join(out)


def strip(text):
    forms = list(_forms(text))
    top = [f for f in forms if f[2] == 1]
    own_id = {}
    for f in forms:
        if f[2] == 2 and f[3] in ('uuid', 'tstamp', 'id') and f[4] not in own_id:
            atoms = _atoms(text, f)
            if atoms:
                own_id[f[4]] = atoms[0]
    cuts, dropped_ids, counts = [], set(), collections.Counter()
    edge_kept = 0
    for s, e, _d, head, _p in top:
        body = text[s:e]
        artwork = head == 'footprint' and '(pad ' not in body and not EDGE.search(body)
        if head in TEXT or (head in GRAPHIC and not EDGE.search(body)) or artwork:
            if artwork:
                head = 'footprint (padless artwork)'
            cuts.append((s, e, ''))
            counts[head] += 1
            if s in own_id:
                dropped_ids.add(own_id[s])
        elif head in GRAPHIC:
            edge_kept += 1
    # groups: drop the members that went, and a group that is left empty
    for s, e, _d, head, _p in top:
        if head != 'group':
            continue
        members = [f for f in forms if f[3] == 'members' and f[4] == s]
        if not members:
            continue
        mf = members[0]
        ids = _atoms(text, mf)
        keep = [i for i in ids if i not in dropped_ids]
        if len(keep) == len(ids):
            continue
        if not keep:
            cuts.append((s, e, ''))
            counts['group (emptied)'] += 1
        else:
            cuts.append((mf[0], mf[1], '(members %s)' % ' '.join('"%s"' % i for i in keep)))
            counts['group (members pruned)'] += 1
    return _cut_spans(text, cuts), counts, edge_kept


def _outline(text):
    """The Edge.Cuts graphics, whitespace-normalised, as a sorted list."""
    return sorted(' '.join(text[s:e].split()) for s, e, d, h, _p in _forms(text)
                  if d == 1 and h in GRAPHIC and EDGE.search(text[s:e]))


def main(path):
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read()
    new, counts, edge_kept = strip(text)
    if _outline(new) != _outline(text):
        raise SystemExit('strip_drawings: REFUSED -- the outline would change')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print('strip_drawings: dropped ' + (', '.join('%s %d' % kv for kv in sorted(counts.items())) or 'nothing')
          + f'; kept {edge_kept} Edge.Cuts graphic(s)')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: strip_drawings.py BOARD.kicad_pcb')
    main(sys.argv[1])
