"""fix_copper.py -- two hand fixes the repo's tools have no command for, on a routed board.

1. --trim-usb-spur: the dead-end /USB_D+ F.Cu spur route_diff leaves at (139.75, 116.06)
   (check_weird `kicad-dangling`, which fails check_complete's weird_copper gate; route.py's
   #1217 split pass leaves it). Matched by COORDINATES, not uuid, so it works on any replay:
     * (138.0,114.3)-(139.8,116.1) -> end moved to (139.35,115.662132), the T-joint where
       the R63-side 0.15 mm chain ends on it;
     * (139.8,116.1)-(139.75,116.1) and (139.75,116.062132)-(139.75,116.1) deleted.
2. --via X Y SIZE: set the outer diameter of the via at (X, Y) to SIZE. route.py
   --escalation board left a GND via 0.45/0.508 (diameter below its own drill), which KiCad
   grades as a GND/PGND hole_clearance violation and check_drc does not see.

3. --type-vii X Y: declare IPC-4761 Type VII (capping yes, filling yes) on the via at (X, Y),
   for a via-in-pad that `fill_for_delivery` turned from `undeclarable` (KiCad 9 file) into a
   blocking via-in-paste (its pcbnew save writes KiCad 10 with explicit `(capping no)
   (filling no)` on every via). Matches pcbnew's shortest-number format or the router's %.6f.

Usage: python3 fix_copper.py IN OUT [--trim-usb-spur] [--via X Y SIZE]...
OUT must be a copy_board copy of IN (siblings in place); it is rewritten.
"""
import argparse
import re

ap = argparse.ArgumentParser()
ap.add_argument('inp')
ap.add_argument('out')
ap.add_argument('--trim-usb-spur', action='store_true')
ap.add_argument('--via', nargs=3, action='append', default=[], metavar=('X', 'Y', 'SIZE'))
ap.add_argument('--via-drill', nargs=3, action='append', default=[], metavar=('X', 'Y', 'DRILL'),
                help='set the drill of the via at (X, Y)')
ap.add_argument('--seg-end', nargs=6, action='append', default=[],
                metavar=('SX', 'SY', 'EX', 'EY', 'NX', 'NY'),
                help='move the END (EX, EY) of the segment SX,SY-EX,EY to (NX, NY): closes a soft joint')
ap.add_argument('--seg-start', nargs=6, action='append', default=[],
                metavar=('SX', 'SY', 'EX', 'EY', 'NX', 'NY'),
                help='move the START (SX, SY) of the segment SX,SY-EX,EY to (NX, NY)')
ap.add_argument('--delete-seg', nargs=4, action='append', default=[], metavar=('SX', 'SY', 'EX', 'EY'),
                help='delete the segment SX,SY-EX,EY (redundant copper check_weird names)')
ap.add_argument('--type-vii', nargs=2, action='append', default=[], metavar=('X', 'Y'))
ap.add_argument('--delete-via', nargs=2, action='append', default=[], metavar=('X', 'Y'),
                help='delete the via at (X, Y) and every track that ends on it and nowhere else')
a = ap.parse_args()
t = open(a.inp, encoding='utf-8').read()

usb = None
if a.trim_usb_spur:
    usb = re.search(r'\(net (\d+) "/USB_D\+"\)', t).group(1)


def seg_block(start, end):
    pat = (r'\n\t\(segment\n\t\t\(start ' + start + r'\)\n\t\t\(end ' + end +
           r'\)\n(?:(?!\n\t\)).)*?\(net ' + usb + r'\)(?:(?!\n\t\)).)*?\n\t\)')
    ms = list(re.finditer(pat, t, re.S))
    assert len(ms) == 1, (start, end, len(ms))
    assert '(layer "F.Cu")' in ms[0].group(0)
    return ms[0]


if a.trim_usb_spur:
    m = seg_block('138.000000 114.300000', '139.800000 116.100000')
    t = t[:m.start()] + m.group(0).replace('(end 139.800000 116.100000)',
                                           '(end 139.350000 115.662132)') + t[m.end():]
    for s, e in (('139.800000 116.100000', '139.750000 116.100000'),
                 ('139.750000 116.062132', '139.750000 116.100000')):
        m = seg_block(s, e)
        t = t[:m.start()] + t[m.end():]
    print('trimmed the /USB_D+ spur (1 shortened, 2 deleted)')

for x, y, size in a.via:
    pat = (r'\n\t\(via\n(?:(?!\n\t\)).)*?\(at ' + '%.6f %.6f' % (float(x), float(y)) +
           r'\)\n\t\t\(size ([\d.]+)\)')
    ms = list(re.finditer(pat, t, re.S))
    assert len(ms) == 1, (x, y, len(ms))
    m = ms[0]
    old = m.group(1)
    blk = m.group(0)
    t = t[:m.start()] + blk[:blk.rfind('(size ')] + '(size %s)' % size + t[m.end():]
    print('via at (%s, %s): size %s -> %s' % (x, y, old, size))
for x, y, drill in a.via_drill:
    pat = (r'\n\t\(via\n\t\t\(at ' + '%.6f %.6f' % (float(x), float(y)) +
           r'\)\n\t\t\(size [\d.]+\)\n\t\t\(drill ([\d.]+)\)')
    ms = list(re.finditer(pat, t, re.S))
    assert len(ms) == 1, (x, y, len(ms))
    m = ms[0]
    blk = m.group(0)
    t = t[:m.start()] + blk[:blk.rfind('(drill ')] + '(drill %s)' % drill + t[m.end():]
    print('via at (%s, %s): drill %s -> %s' % (x, y, m.group(1), drill))
for sx, sy, ex, ey, nx, ny in a.seg_end:
    f = lambda u, v: '%.6f %.6f' % (float(u), float(v))
    pat = (r'\n\t\(segment\n\t\t\(start ' + f(sx, sy) + r'\)\n\t\t\(end ' + f(ex, ey) + r'\)')
    ms = list(re.finditer(pat, t))
    assert len(ms) == 1, (sx, sy, ex, ey, len(ms))
    m = ms[0]
    t = t[:m.start()] + m.group(0).replace('(end ' + f(ex, ey) + ')', '(end ' + f(nx, ny) + ')') + t[m.end():]
    print('segment (%s,%s)-(%s,%s): end -> (%s,%s)' % (sx, sy, ex, ey, nx, ny))
for sx, sy, ex, ey, nx, ny in a.seg_start:
    f = lambda u, v: '%.6f %.6f' % (float(u), float(v))
    pat = (r'\n\t\(segment\n\t\t\(start ' + f(sx, sy) + r'\)\n\t\t\(end ' + f(ex, ey) + r'\)')
    ms = list(re.finditer(pat, t))
    assert len(ms) == 1, (sx, sy, ex, ey, len(ms))
    m = ms[0]
    t = t[:m.start()] + m.group(0).replace('(start ' + f(sx, sy) + ')', '(start ' + f(nx, ny) + ')') + t[m.end():]
    print('segment (%s,%s)-(%s,%s): start -> (%s,%s)' % (sx, sy, ex, ey, nx, ny))
for sx, sy, ex, ey in a.delete_seg:
    f = lambda u, v: '%.6f %.6f' % (float(u), float(v))
    pat = (r'\n\t\(segment\n\t\t\(start ' + f(sx, sy) + r'\)\n\t\t\(end ' + f(ex, ey) +
           r'\)\n(?:(?!\n\t\)).)*?\n\t\)')
    ms = list(re.finditer(pat, t, re.S))
    assert len(ms) == 1, (sx, sy, ex, ey, len(ms))
    t = t[:ms[0].start()] + t[ms[0].end():]
    print('deleted segment (%s,%s)-(%s,%s)' % (sx, sy, ex, ey))
for x, y in a.delete_via:
    at = '%.6f %.6f' % (float(x), float(y))
    pat = r'\n\t\(via\n\t\t\(at ' + at + r'\)\n(?:(?!\n\t\)).)*?\n\t\)'
    ms = list(re.finditer(pat, t, re.S))
    assert len(ms) == 1, (x, y, len(ms))
    net = re.search(r'\(net (\d+)\)', ms[0].group(0)).group(1)
    t = t[:ms[0].start()] + t[ms[0].end():]
    n = 0
    for key in ('start', 'end'):
        spat = (r'\n\t\(segment\n(?:(?!\n\t\)).)*?\(' + key + ' ' + at +
                r'\)(?:(?!\n\t\)).)*?\(net ' + net + r'\)(?:(?!\n\t\)).)*?\n\t\)')
        for m in reversed(list(re.finditer(spat, t, re.S))):
            t = t[:m.start()] + t[m.end():]
            n += 1
    print('deleted via at (%s, %s) on net %s and %d track(s) ending on it' % (x, y, net, n))
def _num(v):
    r = ('%.6f' % float(v)).rstrip('0').rstrip('.')
    return r
for x, y in a.type_vii:
    ats = ['(at %.6f %.6f)' % (float(x), float(y)), '(at %s %s)' % (_num(x), _num(y))]
    ms = [m for m in re.finditer(r'\n\t\(via\n(?:(?!\n\t\)).)*?\n\t\)', t, re.S)
          if any(at in m.group(0) for at in ats)]
    assert len(ms) == 1, (x, y, len(ms))
    m = ms[0]
    b = m.group(0)
    for tok in ('capping', 'filling'):
        if '(%s no)' % tok in b:
            b = b.replace('(%s no)' % tok, '(%s yes)' % tok)
        elif '(%s yes)' % tok not in b:
            b = b.replace('\n\t\t(net ', '\n\t\t(%s yes)\n\t\t(net ' % tok, 1)
    t = t[:m.start()] + b + t[m.end():]
    print('via at (%s, %s): Type VII declared (capping yes, filling yes)' % (x, y))
open(a.out, 'w', encoding='utf-8').write(t)
