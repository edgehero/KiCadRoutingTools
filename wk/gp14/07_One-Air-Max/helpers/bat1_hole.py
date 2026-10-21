"""gp14 helper (TOOL_GAPS: place_simple's anneal blocks the far face under a
whole courtyard of a part that has ONE drilled pad).

BAT1 (BH-18650-B5BA016) is an SMD battery holder on F.Cu with a single
unnetted 1.8 mm locating-peg hole.  `footprint_has_through_pads` makes the
whole part two-sided, and `simple_anneal.Annealer.overlap` prices its FULL
fallback courtyard (the 87.5 x 49 mm pad box) on B.Cu as well -- unlike
`legality.rect_on`, which gives the far face only the drilled-pad box -- so no
B-side part could enter the 4200 mm2 under the holder and 12/12 seeds of
round 1 left connectors with "no legal pose".

strip   IN OUT        : write IN without BAT1's peg-hole pad (siblings copied)
restore IN REF OUT    : write IN with BAT1's footprint block taken from REF
                        (the board with the hole, BAT1 at the same pose);
                        refuses when the two BAT1 `(at ...)` differ.
"""
import os
import re
import shutil
import sys

REF = 'BAT1'
SIBS = ('.kicad_pro', '.kicad_prl', '.kicad_dru', '.design-brief.json')


def block(text, ref):
    i = text.find(f'(property "Reference" "{ref}"')
    if i < 0:
        raise SystemExit(f'{ref} not found')
    s = text.rfind('(footprint ', 0, i)
    d = 0
    for j in range(s, len(text)):
        c = text[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return s, j + 1
    raise SystemExit('unbalanced footprint block')


def sub_block(text, start_pat):
    k = text.find(start_pat)
    if k < 0:
        return None
    d = 0
    for j in range(k, len(text)):
        c = text[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                # take the leading whitespace of the line too
                ls = text.rfind('\n', 0, k)
                return ls, j + 1
    return None


def copy_sibs(src, dst):
    sb, db = src[:-len('.kicad_pcb')], dst[:-len('.kicad_pcb')]
    for ext in SIBS:
        if os.path.exists(sb + ext) and os.path.abspath(sb + ext) != os.path.abspath(db + ext):
            shutil.copyfile(sb + ext, db + ext)


def at_of(blk):
    m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', blk)
    return tuple(float(v) for v in m.groups() if v is not None)


def main(argv):
    mode = argv[1]
    if mode == 'strip':
        src, dst = argv[2], argv[3]
        t = open(src, encoding='utf-8').read()
        s, e = block(t, REF)
        b = t[s:e]
        r = sub_block(b, '(pad "" thru_hole circle')
        if r is None:
            raise SystemExit('no peg hole in BAT1')
        nb = b[:r[0]] + b[r[1]:]
        open(dst, 'w', encoding='utf-8').write(t[:s] + nb + t[e:])
        copy_sibs(src, dst)
        print(f'stripped BAT1 peg hole: {src} -> {dst}')
    elif mode == 'restore':
        src, ref, dst = argv[2], argv[3], argv[4]
        t = open(src, encoding='utf-8').read()
        r = open(ref, encoding='utf-8').read()
        s, e = block(t, REF)
        rs, re_ = block(r, REF)
        if at_of(t[s:e]) != at_of(r[rs:re_]):
            raise SystemExit(f'BAT1 pose differs: {at_of(t[s:e])} vs {at_of(r[rs:re_])}')
        open(dst, 'w', encoding='utf-8').write(t[:s] + r[rs:re_] + t[e:])
        copy_sibs(src, dst)
        print(f'restored BAT1 block from {ref}: {src} -> {dst}')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
