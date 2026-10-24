"""Remove named dangling track segments from a routed board (TOOL_GAPS entry).

No tool in the repo deletes a dead-end stub that route.py's own cleanup left
(check_weird reports it, check_complete gates on it, nothing removes it), so
this one does exactly that and nothing else: each SPEC is NET|LAYER|x1,y1|x2,y2,
matched to a `(segment ...)` block -- or VIA|NET|x,y for a `(via ...)` block at that point with that net, layer and end points (either
direction, 1 um tolerance). The board is copied with its siblings first
(copy_board.py), then the blocks are cut from the copy's text. Refuses if a
spec matches no segment or more than one.

usage (from WT): python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/remove_segments.py IN.kicad_pcb OUT.kicad_pcb SPEC [SPEC ...]
"""
import re
import subprocess
import sys


def blocks(text):
    for m in re.finditer(r'\n\t\(segment\b', text):
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


def net_names(text):
    return {m.group(1): m.group(2) for m in re.finditer(r'\n\t\(net (\d+) "([^"]*)"\)', text)}


def main():
    src, dst, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
    subprocess.run([sys.executable, '-X', 'utf8', 'py_router/copy_board.py', src, dst], check=True)
    text = open(dst, encoding='utf-8').read()
    names = net_names(text)
    cuts = []
    for spec in specs:
        if spec.startswith('VIA|'):
            _, net, a = spec.split('|')
            a = tuple(float(v) for v in a.split(','))
            hits = []
            for m in re.finditer(r'\n\t\(via\b', text):
                s0 = m.start() + 1
                depth = 0
                for j in range(s0, len(text)):
                    if text[j] == '(':
                        depth += 1
                    elif text[j] == ')':
                        depth -= 1
                        if depth == 0:
                            break
                blk = text[s0:j + 1]
                at = re.search(r'\(at ([\d.-]+) ([\d.-]+)\)', blk)
                nn = re.search(r'\(net (\d+)\)', blk) or re.search(r'\(net "([^"]*)"\)', blk)
                if at and nn and names.get(nn.group(1), nn.group(1)) == net and abs(float(at.group(1)) - a[0]) < 1e-3 and abs(float(at.group(2)) - a[1]) < 1e-3:
                    hits.append((s0, j + 1))
            if len(hits) != 1:
                sys.exit(f"REFUSED: {spec} matches {len(hits)} via(s)")
            cuts.append(hits[0])
            print(f"removing {spec}")
            continue
        net, layer, a, b = spec.split('|')
        a = tuple(float(v) for v in a.split(','))
        b = tuple(float(v) for v in b.split(','))
        hits = []
        for s, e, blk in blocks(text):
            lay = re.search(r'\(layer "([^"]+)"\)', blk)
            st = re.search(r'\(start ([\d.-]+) ([\d.-]+)\)', blk)
            en = re.search(r'\(end ([\d.-]+) ([\d.-]+)\)', blk)
            nn = re.search(r'\(net (\d+)\)', blk) or re.search(r'\(net "([^"]*)"\)', blk)
            if not (lay and st and en and nn):
                continue
            nname = names.get(nn.group(1), nn.group(1))
            p, q = (float(st.group(1)), float(st.group(2))), (float(en.group(1)), float(en.group(2)))
            close = lambda u, v: abs(u[0] - v[0]) < 1e-3 and abs(u[1] - v[1]) < 1e-3
            if nname == net and lay.group(1) == layer and ((close(p, a) and close(q, b)) or (close(p, b) and close(q, a))):
                hits.append((s, e))
        if len(hits) != 1:
            sys.exit(f"REFUSED: {spec} matches {len(hits)} segment(s)")
        cuts.append(hits[0])
        print(f"removing {spec}")
    for s, e in sorted(cuts, reverse=True):
        # drop the block and the newline that preceded it
        text = text[:s - 1] + text[e:]
    open(dst, 'w', encoding='utf-8').write(text)
    print(f"wrote {dst}: {len(cuts)} segment(s) removed")


if __name__ == '__main__':
    main()
