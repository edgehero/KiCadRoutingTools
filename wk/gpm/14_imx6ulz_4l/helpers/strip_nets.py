"""Delete every track segment and via of the named nets from a routed board (TOOL_GAPS entry).

route_diff.py has no --force-reroute / --rip-existing-nets: a pair that a
chain routed single-ended (route_diff's own fallback) cannot be re-routed as a
pair later, because route_diff skips nets that are already connected and offers
no rip of them. This strips the pair's copper so a later route_diff call sees
it unrouted. The board is copied with its siblings first (copy_board.py).

usage (from WT): python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/strip_nets.py IN.kicad_pcb OUT.kicad_pcb NET [NET ...]
"""
import re
import subprocess
import sys


def blocks(text, kind):
    for m in re.finditer(r'\n\t\(%s\b' % kind, text):
        s = m.start() + 1
        depth = 0
        for j in range(s, len(text)):
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0:
                    yield s, j + 1, text[s:j + 1]
                    break


src, dst, nets = sys.argv[1], sys.argv[2], set(sys.argv[3:])
subprocess.run([sys.executable, '-X', 'utf8', 'py_router/copy_board.py', src, dst], check=True)
text = open(dst, encoding='utf-8').read()
names = {m.group(1): m.group(2) for m in re.finditer(r'\n\t\(net (\d+) "([^"]*)"\)', text)}
cuts = []
for kind in ('segment', 'via', 'arc'):
    for s, e, blk in blocks(text, kind):
        nn = re.search(r'\(net (\d+)\)', blk)
        nq = re.search(r'\(net "([^"]*)"\)', blk)
        name = names.get(nn.group(1)) if nn else (nq.group(1) if nq else None)
        if name in nets:
            cuts.append((s, e, kind))
for s, e, _k in sorted(cuts, reverse=True):
    text = text[:s - 1] + text[e:]
open(dst, 'w', encoding='utf-8').write(text)
print(f"wrote {dst}: removed " + ', '.join(f"{sum(1 for c in cuts if c[2] == k)} {k}(s)" for k in ('segment', 'via', 'arc')))
