"""body_overlaps.py -- list parts whose pad copper or drawn body (silk/fab extents) intrude into the
drawn body of the board's big silk-bodied parts (BAT1 on F, U1 on B), and same-face body overlaps among
the front parts. check_assembly treats silk-drawn bodies as never gating (#896), so it does not see these.
Usage: python3 body_overlaps.py BOARD"""
import re, sys, math
sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb
B = sys.argv[1]
pcb = parse_kicad_pcb(B)
t = open(B, encoding='utf-8').read()
starts = [m.start() for m in re.finditer(r'\n\t\(footprint ', t)] + [len(t)]
def body(ref):
    for a, b in zip(starts, starts[1:]):
        blk = t[a:b]
        if f'(property "Reference" "{ref}"' not in blk:
            continue
        fp = pcb.footprints[ref]
        pts = []
        for m in re.finditer(r'\(fp_(line|rect|poly|arc|circle)\s(.*?)\(layer "([FB])\.(SilkS|Fab)"\)', blk, re.S):
            pts += [(float(x), float(y)) for x, y in re.findall(r'\((?:start|end|xy|mid) ([-\d.]+) ([-\d.]+)\)', m.group(2))]
        if not pts:
            return None
        th = math.radians(fp.rotation)
        out = []
        for x, y in pts:
            if fp.layer == 'B.Cu':
                pass  # stored already mirrored
            gx = fp.x + x * math.cos(th) + y * math.sin(th)
            gy = fp.y - x * math.sin(th) + y * math.cos(th)
            out.append((gx, gy))
        xs = [p[0] for p in out]; ys = [p[1] for p in out]
        return (min(xs), min(ys), max(xs), max(ys))
    return None
def padbox(ref):
    fp = pcb.footprints[ref]
    xs = [p.global_x - p.size_x / 2 for p in fp.pads] + [p.global_x + p.size_x / 2 for p in fp.pads]
    ys = [p.global_y - p.size_y / 2 for p in fp.pads] + [p.global_y + p.size_y / 2 for p in fp.pads]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None
def ov(a, b):
    if not a or not b: return 0
    w = min(a[2], b[2]) - max(a[0], b[0]); h = min(a[3], b[3]) - max(a[1], b[1])
    return (w, h) if w > 0 and h > 0 else 0
for big, side in (('BAT1', 'F.Cu'), ('U1', 'B.Cu')):
    bb = body(big)
    print(big, 'body', [round(v, 2) for v in bb])
    for ref, fp in pcb.footprints.items():
        if ref == big or fp.layer != side:
            continue
        for kind, box in (('pads', padbox(ref)), ('body', body(ref))):
            o = ov(bb, box)
            if o:
                print('  %-12s %s intrude %.2f x %.2f mm' % (ref, kind, o[0], o[1]))
front = [r for r, fp in pcb.footprints.items() if fp.layer == 'F.Cu' and r != 'BAT1']
for i, a in enumerate(front):
    for b in front[i + 1:]:
        o = ov(body(a), body(b))
        if o:
            print('  F body overlap %s/%s %.2f x %.2f' % (a, b, o[0], o[1]))
