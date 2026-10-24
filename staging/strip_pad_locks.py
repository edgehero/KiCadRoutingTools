#!/usr/bin/env python3
"""gpm staging: remove pad-level locks from a pile, in place.

    python3 -X utf8 wk/gpm/_staging/strip_pad_locks.py BOARD.kicad_pcb

make_unplaced unlocks every footprint, but KiCad 6 also locks pads one by one,
`(pad "1" smd rect locked (at ...))`, and those tokens survive it (steppenprobe:
312). A pad lock does not pin the part, and the repo's parser ignores it when it
decides whether a footprint is locked, but a pile is meant to carry no lock at
all. This drops the KiCad 6 token and any pad-level `(locked yes)` child (KiCad
7+), and nothing else; it prints how many it removed.
"""
import re
import sys

p = sys.argv[1]
t = open(p, encoding='utf-8', newline='').read()
t, n6 = re.subn(r'(\(pad "[^"]*" \S+ \S+) locked(?=[\s)])', r'\1', t)
out, n7, i = [], 0, 0
for m in re.finditer(r'\(pad "', t):          # pad-level (locked yes) in the KiCad 7+ form
    if m.start() < i:
        continue
    d, k = 0, m.start()
    while True:
        c = t[k]
        if c == '"':
            k = t.index('"', k + 1)
        elif c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                break
        k += 1
    blk = t[m.start():k + 1]
    new, n = re.subn(r'\s*\(locked(?: yes)?\)', '', blk)
    if n:
        out.append(t[i:m.start()]); out.append(new); n7 += n; i = k + 1
out.append(t[i:])
t = ''.join(out)
open(p, 'w', encoding='utf-8', newline='').write(t)
print(f'strip_pad_locks: removed {n6} KiCad 6 pad locks and {n7} pad-level (locked yes) from {p}')
