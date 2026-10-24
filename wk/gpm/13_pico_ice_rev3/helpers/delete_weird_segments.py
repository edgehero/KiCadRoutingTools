"""delete_weird_segments.py -- delete exactly the segments check_weird names as dangling-end / kicad-dangling.

    python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/delete_weird_segments.py IN.kicad_pcb OUT.kicad_pcb

Runs `py_router/check_weird.py IN --max-print 0`, and for every
  * `dangling-end` finding ("free end, dangling segment L mm (rooted at (rx, ry))") whose free end and
    root are the two ends of ONE segment of that net and layer, and every
  * `kicad-dangling` finding ("segment (ax, ay)-(bx, by)"), matched to its one segment,
deletes that segment's block from IN's text by uuid. A finding that does not match exactly one
segment is reported and left alone (nothing is guessed). OUT's siblings are the caller's
(copy_board first). The caller re-checks connectivity, DRC and check_weird.

Written because route.py ships these and no repo tool removes them: a scoped route.py re-run over
the four nets left all 11 (TOOL_GAPS "dangling copper"). A first attempt that walked the graph
itself (old/abandoned_helpers/prune_dangling.py) wrongly chose 1327 segments and was not used.
"""
import math
import re
import subprocess
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402


def main():
    inp, out = sys.argv[1:3]
    rep = subprocess.run([sys.executable, '-X', 'utf8', 'py_router/check_weird.py', inp, '--max-print', '0'],
                         capture_output=True, text=True).stdout
    pcb = parse_kicad_pcb(inp)
    names = {n.net_id: n.name for n in pcb.nets.values()}
    segs = [s for s in pcb.segments if not getattr(s, 'graphic', False)]

    def find(net, layer, p, q):
        hits = []
        for s in segs:
            if names.get(s.net_id) != net or s.layer != layer:
                continue
            a, b = (s.start_x, s.start_y), (s.end_x, s.end_y)
            d = lambda u, v: math.hypot(u[0] - v[0], u[1] - v[1])
            if (d(a, p) < 0.002 and d(b, q) < 0.002) or (d(b, p) < 0.002 and d(a, q) < 0.002):
                hits.append(s)
        return hits

    chosen, skipped = [], []
    for m in re.finditer(r'net (\S+) \((\S+)\) at \(([-\d.]+), ([-\d.]+)\): free end, dangling segment ([\d.]+)mm '
                         r'\(rooted at \(([-\d.]+), ([-\d.]+)\)\)', rep):
        net, layer, x, y, L, rx, ry = m.groups()
        h = find(net, layer, (float(x), float(y)), (float(rx), float(ry)))
        (chosen if len(h) == 1 else skipped).append((('dangling', net, layer, L), h))
    for m in re.finditer(r'net (\S+) \((\S+)\) at \(([-\d.]+), ([-\d.]+)\): segment \(([-\d.]+), ([-\d.]+)\)-'
                         r'\(([-\d.]+), ([-\d.]+)\)', rep):
        net, layer, _x, _y, ax, ay, bx, by = m.groups()
        h = find(net, layer, (float(ax), float(ay)), (float(bx), float(by)))
        (chosen if len(h) == 1 else skipped).append((('sliver', net, layer, ''), h))
    uuids = {h[0].uuid for _, h in chosen}
    for what, h in chosen:
        print('delete', *what, h[0].uuid)
    for what, h in skipped:
        print('SKIP (matched %d segments)' % len(h), *what)
    text = open(inp, encoding='utf-8').read()
    n = 0

    def drop(m):
        nonlocal n
        u = re.search(r'\(uuid "([^"]+)"\)', m.group(0))
        if u and u.group(1) in uuids:
            n += 1
            return ''
        return m.group(0)
    new = re.sub(r'\n\t\(segment\n.*?\n\t\)', drop, text, flags=re.S)
    if n != len(uuids):
        sys.exit(f'refuse: matched {n} of {len(uuids)} blocks; nothing written')
    open(out, 'w', encoding='utf-8').write(new)
    print(f'removed {n} segment(s)')


if __name__ == '__main__':
    main()
