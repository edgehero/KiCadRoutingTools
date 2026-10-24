#!/usr/bin/env python3
"""gp14: did staging turn any footprint's pads against its body?

    python3 -X utf8 wk/gpm/_staging/pile_pad_check.py HUMAN.kicad_pcb PILE.kicad_pcb

For every footprint (by reference, first block), compares each pad's angle RELATIVE to its
footprint (pad absolute angle - footprint angle, mod 360) between the two boards. KiCad stores
a pad's (at x y a) angle as absolute, so a move/turn that skips a pad shows here. Prints the
count of footprints whose relative pad angles differ and exits 1 if any do.
"""
import re
import sys


def blocks(text, head):
    out, i = [], 0
    while True:
        i = text.find('(' + head, i)
        if i < 0:
            return out
        d, j = 0, i
        while True:
            c = text[j]
            if c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append(text[i:j + 1])
        i = j + 1


AT = re.compile(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?')


def rel(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    res = {}
    for fb in blocks(t, 'footprint '):
        m = re.search(r'\(property\s+"Reference"\s+"([^"]*)"', fb) or re.search(r'\(fp_text\s+reference\s+"?([^"\s)]+)', fb)
        ref = m.group(1) if m else '?'
        if ref in res:
            continue
        a = AT.search(fb)
        fa = float(a.group(3) or 0) if a else 0.0
        pads = []
        for pb in blocks(fb, 'pad '):
            p = AT.search(pb)
            pa = float(p.group(3) or 0) if p else 0.0
            name = re.match(r'\(pad\s+"?([^"\s]*)"?', pb).group(1)
            pads.append((name, round((pa - fa) % 360, 3), 'locked' in pb.split('(at', 1)[1][:60] if '(at' in pb else False))
        res[ref] = pads
    return res


def turned(human, pile):
    """[(ref, n_turned, n_pads, first_diff)] and the pile's pad `locked` token count."""
    h, p = rel(human), rel(pile)
    bad = []
    for r, hp in h.items():
        pp = p.get(r)
        if pp is None or len(pp) != len(hp):
            continue
        diffs = [(a[0], a[1], b[1]) for a, b in zip(hp, pp) if a[1] != b[1]]
        if diffs:
            bad.append((r, len(diffs), len(hp), diffs[0]))
    locked = sum(1 for v in p.values() for x in v if x[2])
    return len(h), bad, locked


if __name__ == '__main__':
    n, bad, locked = turned(sys.argv[1], sys.argv[2])
    print(f'{n} footprints; {len(bad)} with pads turned against the body; pads with an (at ... locked) token in pile: {locked}')
    for b in bad[:8]:
        print('  ', b)
    sys.exit(1 if bad else 0)
