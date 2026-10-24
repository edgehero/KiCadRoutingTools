#!/usr/bin/env python3
"""Drop named track segments or vias (by uuid) from a routed board -- gpm run 08 helper.

Why it exists (TOOL_GAPS.md): check_weird / check_orphan_stubs name a 0.25 mm
dangling In2.Cu tail on the protected diff-pair net /CM5/DPHY0_P.D2_P, and
check_complete stays INCOMPLETE on it. route.py's end-of-run dead-end sweep
(a scoped pass with the net and the poured nets in --nets) trimmed the other
dangle it named but not this one, and no repo tool removes one segment.

usage: drop_segment.py IN.kicad_pcb OUT.kicad_pcb UUID [UUID ...]
OUT is written with copy_board (siblings carried), then the segment blocks
whose (uuid ...) matches are cut out of OUT's text (a (via ...) block too: a stacked same-net via
pair 0.07 mm apart graded as a via-drill-hole DRC violation that no route pass removed). Refuses (exit 2) when a
uuid matches no segment, or matches anything that is not a (segment ...).
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'py_router'))
from copy_board import copy_board  # noqa: E402


def block_bounds(text, start):
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError('unbalanced parens')


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    src, dst, uuids = argv[1], argv[2], argv[3:]
    copy_board(src, dst)
    text = open(dst, encoding='utf-8').read()
    for u in uuids:
        hits = [m.start() for m in re.finditer(r'\(uuid "%s"\)' % re.escape(u), text)]
        if len(hits) != 1:
            print(f'REFUSED: uuid {u} matches {len(hits)} object(s)')
            return 2
        cands = [text.rfind(k, 0, hits[0]) for k in ('(segment', '(via')]
        seg = max(cands)
        if seg < 0:
            print(f'REFUSED: uuid {u} is not inside a (segment ...) or (via ...)')
            return 2
        end = block_bounds(text, seg)
        if not (seg < hits[0] < end):
            print(f'REFUSED: uuid {u} is not a segment\'s own uuid')
            return 2
        block = text[seg:end]
        # trim the line the block sits on
        ls = text.rfind('\n', 0, seg)
        text = text[:ls] + text[end:]
        print(f'dropped {u}: ' + ' '.join(block.split())[:160])
    open(dst, 'w', encoding='utf-8').write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
