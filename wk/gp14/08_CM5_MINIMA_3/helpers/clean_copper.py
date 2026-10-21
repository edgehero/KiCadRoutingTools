"""Delete-only copper hygiene for a routed board (workaround, TOOL_GAPS):
route.py ships same-net exactly-duplicate segments ('stacked-copper', which it
only discloses -- open issue #162) and the odd half-segment tail past its
anchor ('dangling-end'), and check_complete then calls the board INCOMPLETE.
1. removes every exactly-duplicate segment (same net, layer, endpoints to 1 um,
   check_weird's own key), keeping the widest copy;
2. for each --trim 'X Y AX AY' moves a segment endpoint at (X,Y) to (AX,AY)
   (shortening a dangling tail back to its anchor; the anchor must lie on the
   segment). Nothing is added. Siblings (.kicad_pro ...) are copied.
usage: python3 helpers/clean_copper.py IN OUT [--trim "x y ax ay"]..."""
import sys, re, os, shutil, math, argparse
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--trim', action='append', default=[])
ap.add_argument('--drop-seg', action='append', default=[], help='"x1 y1 x2 y2": delete the one segment with exactly these endpoints (a redundant micro-segment check_weird names kicad-dangling)')
a = ap.parse_args()
txt = open(a.src, encoding='utf-8').read()

def blocks(tag):
    i = 0
    while True:
        j = txt.find('(%s' % tag, i)
        if j < 0:
            return
        if txt[j + len(tag) + 1] not in ' \n\t(':
            i = j + 1; continue
        d = 0; k = j
        while True:
            c = txt[k]
            if c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            k += 1
        yield j, k + 1
        i = k + 1

num = r'(-?[\d.]+)'
segs = []
for j, k in blocks('segment'):
    b = txt[j:k]
    s = re.search(r'\(start ' + num + ' ' + num + r'\)', b); e = re.search(r'\(end ' + num + ' ' + num + r'\)', b)
    w = re.search(r'\(width ' + num + r'\)', b); L = re.search(r'\(layer "([^"]+)"\)', b)
    n = re.search(r'\(net (\d+|"[^"]*")', b)
    segs.append(dict(j=j, k=k, b=b, s=(float(s.group(1)), float(s.group(2))), e=(float(e.group(1)), float(e.group(2))),
                     w=float(w.group(1)), layer=L.group(1), net=n.group(1)))
groups = {}
for sg in segs:
    a0 = tuple(round(v, 3) for v in sg['s']); b0 = tuple(round(v, 3) for v in sg['e'])
    lo, hi = (a0, b0) if a0 <= b0 else (b0, a0)
    groups.setdefault((sg['net'], sg['layer'], lo, hi), []).append(sg)
drop = set()
for key, ss in groups.items():
    if len(ss) > 1:
        keep = max(ss, key=lambda q: q['w'])
        for q in ss:
            if q is not keep:
                drop.add(q['j'])
for t in a.drop_seg:
    x1, y1, x2, y2 = map(float, t.split())
    hit = [q for q in segs if q['j'] not in drop and (
        (math.hypot(q['s'][0]-x1, q['s'][1]-y1) < 1e-3 and math.hypot(q['e'][0]-x2, q['e'][1]-y2) < 1e-3) or
        (math.hypot(q['s'][0]-x2, q['s'][1]-y2) < 1e-3 and math.hypot(q['e'][0]-x1, q['e'][1]-y1) < 1e-3))]
    if len(hit) != 1:
        sys.exit(f'--drop-seg {t}: {len(hit)} segments match (need exactly 1)')
    drop.add(hit[0]['j'])
edits = {}
for t in a.trim:
    x, y, ax, ay = map(float, t.split())
    hit = [q for q in segs if q['j'] not in drop and (math.hypot(q['s'][0] - x, q['s'][1] - y) < 1e-3 or math.hypot(q['e'][0] - x, q['e'][1] - y) < 1e-3)]
    if len(hit) != 1:
        sys.exit(f'--trim {t}: {len(hit)} segments end there (need exactly 1)')
    q = hit[0]
    end = 'start' if math.hypot(q['s'][0] - x, q['s'][1] - y) < 1e-3 else 'end'
    other = q['e'] if end == 'start' else q['s']
    # anchor must lie on the segment
    (x1, y1), (x2, y2) = (x, y), other
    L2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    tpar = ((ax - x1) * (x2 - x1) + (ay - y1) * (y2 - y1)) / L2
    dist = math.hypot(x1 + tpar * (x2 - x1) - ax, y1 + tpar * (y2 - y1) - ay)
    if not (0 < tpar < 1 and dist < 1e-3):
        sys.exit(f'--trim {t}: anchor not on the segment (t={tpar:.3f}, off {dist:.4f})')
    nb = re.sub(r'\(%s ' % end + num + ' ' + num + r'\)', f'({end} {ax:g} {ay:g})', q['b'], count=1)
    edits[q['j']] = (q['k'], nb)
out, i = [], 0
for q in sorted(segs, key=lambda q: q['j']):
    if q['j'] in drop:
        # also drop the preceding newline+indent
        jj = q['j']
        while jj > i and txt[jj - 1] in ' \t': jj -= 1
        if jj > i and txt[jj - 1] == '\n': jj -= 1
        out.append(txt[i:jj]); i = q['k']
    elif q['j'] in edits:
        out.append(txt[i:q['j']]); out.append(edits[q['j']][1]); i = q['k']
out.append(txt[i:])
open(a.dst, 'w', encoding='utf-8').write(''.join(out))
for ext in ('.kicad_pro', '.kicad_prl', '.kicad_dru', '.design-brief.json'):
    s = os.path.splitext(a.src)[0] + ext
    if os.path.exists(s):
        shutil.copy(s, os.path.splitext(a.dst)[0] + ext)
print(f'removed {len(drop)} segment(s) ({len(a.drop_seg)} by --drop-seg, the rest exact duplicates); trimmed {len(edits)} tail(s) -> {a.dst}')
