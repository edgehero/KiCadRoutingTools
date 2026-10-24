"""prune_removable.py -- delete, one at a time, every segment check_weird reports as
`removable-segment` ("removal does not change net connectivity"), re-running check_weird after
each deletion so two segments that cover each other are never both removed.
No repo tool removes these (route.py's late passes left them; a second route.py over the net did not).
Usage: python3 prune_removable.py IN OUT   (OUT must be a copy_board copy of IN)"""
import re, subprocess, sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
open(dst, 'w', encoding='utf-8').write(t)
f = lambda u, v: '%.6f %.6f' % (float(u), float(v))
for it in range(200):
    out = subprocess.run([sys.executable, '-X', 'utf8', 'py_router/check_weird.py', dst],
                         capture_output=True, text=True).stdout
    m = re.search(r'segment \(([-\d.]+), ([-\d.]+)\)-\(([-\d.]+), ([-\d.]+)\) w[\d.]+: removal does not change net connectivity', out)
    if not m:
        print('done after %d deletion(s)' % it)
        print('\n'.join(l for l in out.splitlines() if 'WEIRD' in l))
        break
    sx, sy, ex, ey = m.groups()
    t = open(dst, encoding='utf-8').read()
    want = sorted([(float(sx), float(sy)), (float(ex), float(ey))])
    ms = []
    for mm in re.finditer(r'\n\t\(segment\n\t\t\(start ([-\d.]+) ([-\d.]+)\)\n\t\t\(end ([-\d.]+) ([-\d.]+)\)\n(?:(?!\n\t\)).)*?\n\t\)', t, re.S):
        got = sorted([(float(mm.group(1)), float(mm.group(2))), (float(mm.group(3)), float(mm.group(4)))])
        if all(abs(g[0] - w[0]) < 0.0006 and abs(g[1] - w[1]) < 0.0006 for g, w in zip(got, want)):
            ms.append(mm)
    assert len(ms) == 1, (m.groups(), len(ms))
    t = t[:ms[0].start()] + t[ms[0].end():]
    open(dst, 'w', encoding='utf-8').write(t)
    print('deleted segment (%s,%s)-(%s,%s)' % (sx, sy, ex, ey))
