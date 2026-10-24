"""drop_segment.py -- remove ONE track segment named by its net, layer and end points (a redundant loop edge).

Why (TOOL_GAPS): route.py ships redundant copper loops that check_weird names ("loop edge ... removal leaves
connectivity identical") and check_complete gates as weird_copper; a --force-reroute of the net re-creates the same
loop, and no repo tool removes a named segment (check_weird has no fix mode, cleanup_pipeline has no CLI).

Usage (from WT):
  python3 -X utf8 wk/gpm/15_am32_esc/helpers/drop_segment.py IN.kicad_pcb OUT.kicad_pcb NET LAYER X1 Y1 X2 Y2
The siblings (.kicad_pro, ...) are copied with py_router/copy_board.py first; then exactly one (segment ...) block
whose net, layer and end points (either order, within 0.002 mm) match is deleted. Refuses (exit 2) on 0 or >1 match.
"""
import re
import subprocess
import sys


def blocks(text, head):
    """Yield (start, end) spans of each top-level `(head ...)` block."""
    i = 0
    tok = '(' + head
    while True:
        j = text.find(tok, i)
        if j < 0:
            return
        nxt = text[j + len(tok)]
        if nxt not in ' \n\t\r':
            i = j + 1
            continue
        depth, k = 0, j
        while True:
            c = text[k]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        yield j, k + 1
        i = k + 1


def main(argv):
    if len(argv) != 9:
        print(__doc__)
        return 2
    src, dst, net, layer = argv[1:5]
    x1, y1, x2, y2 = map(float, argv[5:9])
    r = subprocess.run([sys.executable, '-X', 'utf8', 'py_router/copy_board.py', src, dst])
    if r.returncode != 0:
        return 3
    text = open(dst, encoding='utf-8').read()
    # net name -> number, for the numeric (net N) dialect
    nums = {m.group(2): m.group(1) for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', text)}
    want_num = nums.get(net)
    hits = []
    for a, b in blocks(text, 'segment'):
        blk = text[a:b]
        m_s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk)
        m_e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
        m_l = re.search(r'\(layer "([^"]+)"\)', blk)
        m_n = re.search(r'\(net (?:"([^"]*)"|(\d+))\)', blk)
        if not (m_s and m_e and m_l and m_n):
            continue
        nname, nnum = m_n.group(1), m_n.group(2)
        if not (nname == net or (nnum is not None and nnum == want_num)):
            continue
        if m_l.group(1) != layer:
            continue
        s = (float(m_s.group(1)), float(m_s.group(2)))
        e = (float(m_e.group(1)), float(m_e.group(2)))
        close = lambda p, q: abs(p[0] - q[0]) < 0.002 and abs(p[1] - q[1]) < 0.002
        if (close(s, (x1, y1)) and close(e, (x2, y2))) or (close(s, (x2, y2)) and close(e, (x1, y1))):
            hits.append((a, b, blk))
    if len(hits) != 1:
        print(f"REFUSED: {len(hits)} matching segment(s) for {net} {layer} ({x1},{y1})-({x2},{y2})")
        return 2
    a, b, blk = hits[0]
    # drop the block and the whitespace line it sat on
    la = text.rfind('\n', 0, a)
    text = text[:la] + text[b:]
    open(dst, 'w', encoding='utf-8').write(text)
    print(f"removed 1 segment: {' '.join(blk.split())[:160]}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
