"""Delete the micro-segments check_weird reports as `kicad-dangling` (#1217 shape).

Why (TOOL_GAPS.md, entry "route.py leaves a kicad-dangling micro-segment"):
route.py's output carries a 0.011 mm GND segment whose two ends both lie on
other same-net tracks that hold the other end too. check_weird (and so
check_complete) fails the board on it -- KiCad's DRC reports track_dangling --
and no repo actor removes it: a closing `route.py --nets GND +3V3` pass, a
`--rip-existing-nets GND` pass and eleven routing variants all left one.

What this does, and nothing else: runs check_weird's own analysis
(`check_weird.check_weird`) on the board, takes every `kicad-dangling` finding,
and deletes exactly that segment -- matched on net, layer and both endpoints to
1 um -- from the board text, refusing any segment longer than --max-len (default
0.05 mm). By check_weird's definition every other track touching the segment
holds BOTH its ends, so removing it cannot disconnect anything; the caller
re-runs check_connected / check_weird / board_score to prove that.

Usage: drop_kicad_dangling.py IN.kicad_pcb OUT.kicad_pcb [--max-len 0.05]
The siblings (.kicad_pro etc.) are copied with py_router/copy_board.py first.
"""
import argparse
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'py_router'))

from kicad_parser import parse_kicad_pcb  # noqa: E402
import check_weird  # noqa: E402

SEG_RE = re.compile(r"segment \(([-\d.]+), ([-\d.]+)\)-\(([-\d.]+), ([-\d.]+)\) w([\d.]+)")


def _blocks(text, head):
    i = text.find(head)
    while i != -1:
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
        yield i, j + 1
        i = text.find(head, j + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('out')
    ap.add_argument('--max-len', type=float, default=0.05)
    a = ap.parse_args()
    pcb = parse_kicad_pcb(a.board)
    findings, _skipped = check_weird.check_weird(pcb, quiet=True)
    targets = []
    for f in findings:
        if f['category'] != 'kicad-dangling':
            continue
        m = SEG_RE.search(f['detail'])
        if not m:
            print(f"cannot read segment from: {f['detail']}", file=sys.stderr)
            return 2
        x1, y1, x2, y2, _w = map(float, m.groups())
        ln = math.hypot(x2 - x1, y2 - y1)
        if ln > a.max_len:
            print(f"refused: {f['net']} {f['layer']} segment {ln:.4f} mm > --max-len {a.max_len}",
                  file=sys.stderr)
            return 4
        targets.append((f['net'], f['layer'], x1, y1, x2, y2))
    text = open(a.board, encoding='utf-8').read()
    name_of = {n.net_id: n.name for n in pcb.nets.values()}
    cut = []
    for s, e in _blocks(text, '(segment'):
        blk = text[s:e]
        st = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk)
        en = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
        ly = re.search(r'\(layer "([^"]+)"\)', blk)
        nt = re.search(r'\(net (\d+|"[^"]*")\)', blk)
        if not (st and en and ly and nt):
            continue
        net = nt.group(1)
        net = name_of.get(int(net), net) if net.isdigit() else net.strip('"')
        p = (float(st.group(1)), float(st.group(2)), float(en.group(1)), float(en.group(2)))
        for (tn, tl, x1, y1, x2, y2) in targets:
            if tn != net or tl != ly.group(1):
                continue
            fw = max(abs(p[0] - x1), abs(p[1] - y1), abs(p[2] - x2), abs(p[3] - y2))
            bw = max(abs(p[0] - x2), abs(p[1] - y2), abs(p[2] - x1), abs(p[3] - y1))
            if min(fw, bw) <= 1e-3:
                cut.append((s, e, tn, tl, p))
    if len(cut) != len(targets):
        print(f"matched {len(cut)} segment block(s) for {len(targets)} finding(s); nothing written",
              file=sys.stderr)
        return 3
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(REPO, 'py_router', 'copy_board.py'),
                    a.board, a.out], check=True, stdout=subprocess.DEVNULL)
    out = text
    for s, e, tn, tl, p in sorted(cut, key=lambda c: -c[0]):
        # drop the block and the whitespace before it
        k = s
        while k > 0 and out[k - 1] in ' \t\n\r':
            k -= 1
        out = out[:k] + out[e:]
        print(f"removed {tn} {tl} segment ({p[0]}, {p[1]})-({p[2]}, {p[3]})")
    open(a.out, 'w', encoding='utf-8').write(out)
    print(f"DROP_JSON: {{\"removed\": {len(cut)}, \"out\": \"{a.out}\"}}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
