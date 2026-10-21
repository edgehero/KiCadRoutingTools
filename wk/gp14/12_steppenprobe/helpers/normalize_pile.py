#!/usr/bin/env python3
"""Workaround helper (gp14 board 12, TOOL_GAPS entry #1).

Problem: every pad in this board carries the KiCad-6 per-pad `locked` token
(`(pad "1" smd roundrect locked (at x y a) ...)`).  The placement writer's
`_rotate_pad_angles` regex (py_placer/placement/writer.py) does not allow that
token between the pad shape and `(at ...)`, so when a part is turned its pads'
ABSOLUTE angles are left behind.  The pile this campaign hands over already
carries that damage: every footprint sits at angle 0 while its pads keep the
absolute angle they had at the source rotation, so 38 of 84 parts have pads
turned 90 deg against their own bodies (U1's west-row pads read 0.3 x 1.55 mm
in pcbnew; check_pads reports 126 overlapping different-net pads on U1).

Fix, on a COPY of the board (edits a working file only):
  1. per footprint, set the footprint angle to the most common pad angle, so
     every pad's local angle is 0 (or 180) again -- the library geometry;
  2. drop the per-pad `locked` token so the writer's regex matches and later
     rotations carry the pads along.
Positions are untouched (a pile pose carries no information).

usage: normalize_pile.py BOARD_IN BOARD_OUT   (BOARD_OUT may equal BOARD_IN)
"""
import re
import sys
from collections import Counter


def blocks(text):
    """Yield (start, end) of every top-level (footprint ...) block."""
    for m in re.finditer(r'\n\s*\(footprint ', text):
        s = m.start() + text[m.start():].index('(footprint ')
        d = 0
        for j in range(s, len(text)):
            c = text[j]
            if c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    yield s, j + 1
                    break


PAD_AT = re.compile(r'(\(pad\s+"[^"]*"\s+\S+\s+\S+\s+)(locked\s+)?'
                    r'\(at\s+(\S+)\s+(\S+)(?:\s+([-\d.]+))?\)')


def fix_block(b):
    angs = [float(m.group(5) or 0) % 360 for m in PAD_AT.finditer(b)]
    if not angs:
        return b, None
    cnt = Counter(round(a, 6) for a in angs)
    best = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    # footprint's own (at X Y [a]) is the first (at ...) after the (layer ...)
    m = re.search(r'(\n\s*)\(at\s+(\S+)\s+(\S+)(?:\s+([-\d.]+))?\)', b)
    old = float(m.group(4) or 0)
    ang = f' {best:.6g}' if best else ''
    b = b[:m.start()] + f'{m.group(1)}(at {m.group(2)} {m.group(3)}{ang})' + b[m.end():]
    b = PAD_AT.sub(lambda p: p.group(1) + p.group(0)[len(p.group(1)) + len(p.group(2) or ''):], b)
    return b, (old, best)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src, encoding='utf-8').read()
    out, last, changed = [], 0, []
    for s, e in blocks(text):
        b, res = fix_block(text[s:e])
        ref = re.search(r'\(fp_text reference "([^"]+)"', b)
        if res and res[0] != res[1]:
            changed.append(f'{ref.group(1) if ref else "?"}:{res[0]:g}->{res[1]:g}')
        out.append(text[last:s]); out.append(b); last = e
    out.append(text[last:])
    new = ''.join(out)
    n_locked = len(re.findall(r'\(pad\s+"[^"]*"\s+\S+\s+\S+\s+locked\s', new))
    open(dst, 'w', encoding='utf-8').write(new)
    print(f'footprint angles set to their pads\' common angle: {len(changed)}')
    print('  ' + ' '.join(changed))
    print(f'pads still carrying `locked`: {n_locked}')


if __name__ == '__main__':
    main()
