"""Remove the board's zone block(s) for one net (by net name) so route_planes can
re-pour that net fresh.  Workaround helper (TOOL_GAPS): route_planes cannot
replace a MULTI-LAYER zone even when every one of its layers is poured in the
same call (it keeps the old zone and adds a second same-net zone per layer).
usage: python3 helpers/drop_zone.py IN.kicad_pcb OUT.kicad_pcb NETNAME
(copies siblings with py_router/copy_board.py semantics by hand: .kicad_pro next to OUT)"""
import sys, re, shutil, os
src, dst, net = sys.argv[1:4]
txt = open(src, encoding='utf-8').read()
out, i, n = [], 0, 0
while True:
    j = txt.find('\n\t(zone', i)
    if j < 0:
        out.append(txt[i:]); break
    # balance parens from the '(' of '(zone'
    k = j + 2; d = 0
    while True:
        c = txt[k]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: break
        k += 1
    block = txt[j:k + 1]
    if re.search(r'\(net_name "%s"\)' % re.escape(net), block):
        out.append(txt[i:j]); n += 1
    else:
        out.append(txt[i:k + 1])
    i = k + 1
open(dst, 'w', encoding='utf-8').write(''.join(out))
for ext in ('.kicad_pro', '.kicad_prl', '.kicad_dru', '.design-brief.json'):
    s = os.path.splitext(src)[0] + ext
    if os.path.exists(s):
        shutil.copy(s, os.path.splitext(dst)[0] + ext)
print(f'removed {n} zone block(s) of net {net!r}: {dst}')
