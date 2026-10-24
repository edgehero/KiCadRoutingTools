"""Helper (TOOL_GAPS: no repo tool removes a dead-end segment of a POURED net that
route.py's cleanup leaves and check_weird reports as `dangling-end`; --force-reroute
skips plane nets). Copies BOARD to OUT with copy_board (siblings carried), then
removes the one top-level (segment ...) block whose net, layer and endpoints match
(either direction, 1 um). Refuses unless exactly one block matches.
usage: drop_segment.py BOARD OUT NET LAYER X1 Y1 X2 Y2"""
import os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'py_router'))
from copy_board import copy_board
board, out, net, layer = sys.argv[1:5]
x1, y1, x2, y2 = map(float, sys.argv[5:9])
copy_board(board, out)
txt = open(out, encoding='utf-8').read()
blocks = []
for m in re.finditer(r'\n\t\(segment\n(.*?)\n\t\)', txt, re.S):
    b = m.group(1)
    s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b); e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    ly = re.search(r'\(layer "([^"]+)"\)', b); nt = re.search(r'\(net "([^"]*)"\)', b)
    if not (s and e and ly and nt) or ly.group(1) != layer or nt.group(1) != net:
        continue
    a = (float(s.group(1)), float(s.group(2)), float(e.group(1)), float(e.group(2)))
    ok = lambda p, q: abs(p[0]-q[0]) < 1e-3 and abs(p[1]-q[1]) < 1e-3
    if (ok(a[:2], (x1, y1)) and ok(a[2:], (x2, y2))) or (ok(a[:2], (x2, y2)) and ok(a[2:], (x1, y1))):
        blocks.append(m)
if len(blocks) != 1:
    os.remove(out); sys.exit(f'refused: {len(blocks)} matching segment block(s)')
m = blocks[0]
open(out, 'w', encoding='utf-8').write(txt[:m.start()] + txt[m.end():])
print(f'removed 1 segment {net} {layer} ({x1},{y1})-({x2},{y2}) -> {out}')
