#!/usr/bin/env python3
"""gpm audit: an independent census of a .kicad_pcb's top-level items, read from the raw text with a
paren-balancing scan (no repo parser). Used to prove a board's start state.

    python3 sexp_census.py BOARD.kicad_pcb [--json]
"""
import json
import re
import sys


def top_items(text):
    """Yield (head, block_text) for each direct child of (kicad_pcb ...), skipping strings."""
    i = text.index('(kicad_pcb') + 1
    depth, start, n, s = 1, None, len(text), False
    while i < n:
        c = text[i]
        if s:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                s = False
        elif c == '"':
            s = True
        elif c == '(':
            depth += 1
            if depth == 2:
                start = i
        elif c == ')':
            depth -= 1
            if depth == 1 and start is not None:
                blk = text[start:i + 1]
                yield re.match(r'\((\S+)', blk).group(1), blk
                start = None
            if depth == 0:
                return
        i += 1


def layer_of(blk):
    m = re.search(r'\(layer "?([^")\s]+)"?', blk)
    return m.group(1) if m else None


def census(path):
    text = open(path, encoding='utf-8', errors='replace').read()
    c = {'segments': 0, 'arcs': 0, 'vias': 0, 'zones': 0, 'zone_fills': 0, 'board_text': 0,
         'drawings_off_edgecuts': 0, 'edgecuts_items': 0, 'images': 0, 'footprints': 0,
         'locked_footprints': [], 'locked_pads': 0, 'locked_other': 0, 'groups': 0}
    edge_pts = []
    fps = []
    for head, blk in top_items(text):
        if head == 'segment':
            c['segments'] += 1
        elif head == 'arc':
            c['arcs'] += 1
        elif head == 'via':
            c['vias'] += 1
        elif head == 'zone':
            c['zones'] += 1
            c['zone_fills'] += blk.count('(filled_polygon')
        elif head in ('gr_text', 'gr_text_box', 'dimension', 'target'):
            c['board_text'] += 1
        elif head == 'image':
            c['images'] += 1
        elif head == 'group':
            c['groups'] += 1
        elif head.startswith('gr_'):
            if layer_of(blk) == 'Edge.Cuts':
                c['edgecuts_items'] += 1
                edge_pts += [(float(a), float(b)) for a, b in re.findall(r'\((?:start|end|mid|center|xy) ([-\d.]+) ([-\d.]+)\)', blk)]
                m = re.search(r'\(center ([-\d.]+) ([-\d.]+)\).*?\(end ([-\d.]+) ([-\d.]+)\)', blk, re.S)
                if head == 'gr_circle' and m:
                    cx, cy, ex, ey = map(float, m.groups()); r = ((cx - ex) ** 2 + (cy - ey) ** 2) ** .5
                    edge_pts += [(cx - r, cy - r), (cx + r, cy + r)]
            else:
                c['drawings_off_edgecuts'] += 1
        elif head in ('footprint', 'module'):
            c['footprints'] += 1
            hdr = blk[:blk.find('(', 1)]
            ref = re.search(r'\(property "Reference" "([^"]*)"|\(fp_text reference "?([^"\s)]*)"?', blk)
            ref = (ref.group(1) or ref.group(2)) if ref else '?'
            if re.search(r'\slocked\b', hdr) or re.search(r'^\t*\(locked yes\)', blk, re.M) \
                    or re.search(r'\n\t\t\(locked(?: yes)?\)', blk):
                c['locked_footprints'].append(ref)
            c['locked_pads'] += len(re.findall(r'\(pad "[^"]*" \S+ \S+ locked', blk)) + \
                len(re.findall(r'\(pad [^\n]*?\(locked yes\)', blk))
            at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)|\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
            g = [x for x in at.groups() if x is not None] if at else []
            fps.append({'ref': ref, 'x': float(g[0]) if g else None, 'y': float(g[1]) if g else None,
                        'rot': float(g[2]) if len(g) > 2 else 0.0, 'layer': layer_of(blk),
                        'fp_edgecuts': blk.count('"Edge.Cuts"')})
    if edge_pts:
        xs, ys = zip(*edge_pts)
        c['outline_bbox'] = [min(xs), min(ys), max(xs), max(ys)]
    c['version'] = (re.search(r'\(version (\d+)\)', text) or [None, None])[1]
    return c, fps


if __name__ == '__main__':
    c, fps = census(sys.argv[1])
    print(json.dumps(c if '--json' in sys.argv else {k: v for k, v in c.items()}, indent=1))
