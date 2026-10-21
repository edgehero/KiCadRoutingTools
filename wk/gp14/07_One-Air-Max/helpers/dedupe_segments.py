"""gp14 helper (TOOL_GAPS: route.py's in-run plane finalize writes same-net
segments stacked on each other -- 23 exact duplicate pairs on GND/B.Cu in
final_route/s4_route.kicad_pcb, carried unchanged through two more route.py
passes -- while route.py's own stacked-copper census (it runs before the
finalize) reports none and its summary carries no `stacked_copper` key;
check_weird then fails check_complete with `weird_copper`).

Removes every `(segment ...)` block that duplicates another one exactly
(same net, same layer, same two end points in either order), keeping the
WIDEST copy.  Nothing else changes, so connectivity cannot change.

usage: dedupe_segments.py IN OUT        (siblings copied)
"""
import os
import re
import shutil
import sys

SIBS = ('.kicad_pro', '.kicad_prl', '.kicad_dru', '.design-brief.json')


def blocks(text, head):
    i = 0
    while True:
        k = text.find(head, i)
        if k < 0:
            return
        d = 0
        for j in range(k, len(text)):
            c = text[j]
            if c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    yield k, j + 1
                    i = j + 1
                    break


def key_of(b):
    s = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', b)
    e = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', b)
    lay = re.search(r'\(layer "([^"]+)"\)', b)
    net = re.search(r'\(net (\d+|"[^"]*")', b)
    w = re.search(r'\(width ([\d.\-]+)\)', b)
    if not (s and e and lay and net and w):
        return None, 0.0
    p = (round(float(s.group(1)), 4), round(float(s.group(2)), 4))
    q = (round(float(e.group(1)), 4), round(float(e.group(2)), 4))
    return (net.group(1), lay.group(1), tuple(sorted((p, q)))), float(w.group(1))


def main(src, dst):
    t = open(src, encoding='utf-8').read()
    found = {}
    order = []
    for a, b in blocks(t, '(segment'):
        k, w = key_of(t[a:b])
        if k is None:
            continue
        found.setdefault(k, []).append((w, a, b))
    drop = []
    for k, lst in found.items():
        if len(lst) > 1:
            lst.sort(key=lambda x: -x[0])
            drop.extend(lst[1:])
            order.append((k, [x[0] for x in lst]))
    drop.sort(key=lambda x: x[1], reverse=True)
    for w, a, b in drop:
        ls = t.rfind('\n', 0, a)
        t = t[:ls] + t[b:]
    open(dst, 'w', encoding='utf-8').write(t)
    for ext in SIBS:
        s = src[:-10] + ext
        if os.path.exists(s) and os.path.abspath(s) != os.path.abspath(dst[:-10] + ext):
            shutil.copyfile(s, dst[:-10] + ext)
    for k, ws in order:
        print(f'  net {k[0]} {k[1]} {k[2]}: widths {ws} -> kept {ws[0]}')
    print(f'dropped {len(drop)} duplicate segment(s) in {len(order)} stack(s): {src} -> {dst}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
