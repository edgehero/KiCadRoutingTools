#!/usr/bin/env python3
"""Workaround helper (gp14 board 12, TOOL_GAPS entry): drop stacked same-net
duplicate track segments.

route.py prints "WARNING: N stacked-copper finding(s) on the write model
(same-net duplicates KiCad will not flag)" and writes them anyway; check_weird
counts them as `stacked-copper` and check_complete then refuses DONE
("weird_copper: not clean").  No repo tool removes them.

This removes a segment only when ANOTHER segment of the same net, on the same
layer, has the same two endpoints (either direction, to 1 um); the widest copy
is kept.  Nothing else is touched, so connectivity and clearance cannot get
worse (the kept copy covers the dropped one).

usage: dedupe_segments.py BOARD_IN BOARD_OUT   (BOARD_OUT may equal BOARD_IN)
"""
import re
import sys

SEG = re.compile(r'\(segment\b')


def block_end(t, s):
    d = 0
    for j in range(s, len(t)):
        if t[j] == '(':
            d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0:
                return j + 1
    raise ValueError('unbalanced')


def field(b, name):
    m = re.search(r'\(' + name + r'\s+([^()]*?)\)', b)
    return m.group(1).strip() if m else None


def main():
    src, dst = sys.argv[1], sys.argv[2]
    t = open(src, encoding='utf-8').read()
    segs = []
    for m in SEG.finditer(t):
        s = m.start()
        e = block_end(t, s)
        b = t[s:e]
        st = tuple(round(float(v), 3) for v in field(b, 'start').split())
        en = tuple(round(float(v), 3) for v in field(b, 'end').split())
        key = (field(b, 'net'), field(b, 'layer'), tuple(sorted([st, en])))
        segs.append((s, e, key, float(field(b, 'width'))))
    best = {}
    for i, (s, e, key, w) in enumerate(segs):
        if key not in best or w > segs[best[key]][3]:
            best[key] = i
    drop = [i for i, (s, e, key, w) in enumerate(segs) if best[key] != i]
    out, last = [], 0
    for i in sorted(drop, key=lambda i: segs[i][0]):
        s, e = segs[i][0], segs[i][1]
        out.append(t[last:s])
        last = e
    out.append(t[last:])
    open(dst, 'w', encoding='utf-8').write(''.join(out))
    print(f'segments {len(segs)}; dropped {len(drop)} stacked duplicate(s):')
    for i in drop:
        net, layer, (a, b) = segs[i][2]
        print(f'  net {net} {layer} {a}-{b} w{segs[i][3]}')


if __name__ == '__main__':
    main()
