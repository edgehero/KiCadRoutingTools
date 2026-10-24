#!/usr/bin/env python3
"""Part heights from KiCad's own 3D models, and two placement checks that need them. One file, run from a
KiCadRoutingTools checkout (it uses py_router/kicad_parser for footprint poses and pads).

    python3 -X utf8 height_checks.py BOARD.kicad_pcb [--lib KICAD_3DMODEL_DIR] [--list N]

  * heights: kicad-cli exports the board as GLB (one node per footprint, named by its reference) from a temp
    copy whose model paths point at real files (${KICAD*_3DMODEL_DIR} / ${KISYS3DMOD} -> --lib, ${KIPRJMOD}
    -> the board's folder, a missing .wrl -> the .step of the same name). Height = the model's top above its
    own board face; the plan rectangle is the model's footprint in board mm.
  * plug   : a vertical connector (J/P/CN/X ref, Vertical / PinHeader / PinSocket / IDC / Box footprint) with a
             part TALLER than itself within 1.5 mm of its body -- the plug housing and the fingers need that ring.
  * jammed : a part <= 2 mm tall with parts >= 4 mm (and >= 3x its height) on two OPPOSITE sides, each closer
             than half its own height -- no iron, 45-degree AOI camera or rework nozzle reaches it.
"""
import json
import os
import platform
import re
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.getcwd(), 'py_router'))
from kicad_parser import parse_kicad_pcb  # noqa: E402

CLI = {'Darwin': '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'}.get(platform.system(), 'kicad-cli')
LIB = {'Darwin': '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels',
       'Linux': '/usr/share/kicad/3dmodels'}.get(platform.system(), r'C:\Program Files\KiCad\10.0\share\kicad\3dmodels')
board = sys.argv[1]
lib = sys.argv[sys.argv.index('--lib') + 1] if '--lib' in sys.argv else LIB
NLIST = int(sys.argv[sys.argv.index('--list') + 1]) if '--list' in sys.argv else 8


def fix_models(text):
    def one(m):
        p = re.sub(r'\$\{(KISYS3DMOD|KICAD\d+_3DMODEL_DIR)\}', lambda _: lib, m.group(1))
        p = p.replace('${KIPRJMOD}', os.path.dirname(os.path.abspath(board)))
        if not os.path.isfile(p) and p.lower().endswith('.wrl') and os.path.isfile(p[:-4] + '.step'):
            p = p[:-4] + '.step'
        return '(model "%s"' % p
    return re.sub(r'\(model\s+"([^"]+)"', one, text)


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def local(n):
    if 'matrix' in n:
        m = n['matrix']
        return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]], [m[2], m[6], m[10], m[14]], [0, 0, 0, 1]]
    x, y, z, w = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1]); t = n.get('translation', [0, 0, 0])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]


with tempfile.TemporaryDirectory() as td:
    tmp = os.path.join(td, 'b.kicad_pcb')
    open(tmp, 'w', encoding='utf-8').write(fix_models(open(board, encoding='utf-8').read()))
    subprocess.run([CLI, 'pcb', 'export', 'glb', tmp, '-o', os.path.join(td, 'b.glb')], capture_output=True)
    raw = open(os.path.join(td, 'b.glb'), 'rb').read()
n = struct.unpack('<I', raw[12:16])[0]
g = json.loads(raw[20:20 + n])
boxes = {}


def walk(i, m, owner):
    node = g['nodes'][i]
    w = mat_mul(m, local(node))
    name = node.get('name')
    own = owner or (name if name and not name.startswith('=>') else None)
    if 'mesh' in node:
        for prim in g['meshes'][node['mesh']]['primitives']:
            a = g['accessors'][prim['attributes']['POSITION']]
            for cx in (a['min'][0], a['max'][0]):
                for cy in (a['min'][1], a['max'][1]):
                    for cz in (a['min'][2], a['max'][2]):
                        p = [w[k][0] * cx + w[k][1] * cy + w[k][2] * cz + w[k][3] for k in range(3)]
                        bb = boxes.setdefault(own or '', [[1e9] * 3, [-1e9] * 3])
                        for k in range(3):
                            bb[0][k] = min(bb[0][k], p[k]); bb[1][k] = max(bb[1][k], p[k])
    for c in node.get('children', []):
        walk(c, w, own)


for r in g['scenes'][g.get('scene', 0)]['nodes']:
    walk(r, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], None)
brd = boxes.pop('')
ax = min(range(3), key=lambda k: brd[1][k] - brd[0][k])          # the board's thickness axis
pl = [k for k in range(3) if k != ax]
u = 1000.0 if brd[1][pl[0]] - brd[0][pl[0]] < 2 else 1.0           # GLB in metres
pcb = parse_kicad_pcb(board)
pairs = [(pcb.footprints[r], b) for r, b in boxes.items() if r in pcb.footprints and pcb.footprints[r].pads]


def centre(b):
    return [(b[0][k] + b[1][k]) / 2 * u for k in pl]


def pad_c(f):
    return (sum(p.global_x for p in f.pads) / len(f.pads), sum(p.global_y for p in f.pads) / len(f.pads))


best = None
for swap in (0, 1):
    for sx in (1, -1):
        for sy in (1, -1):
            offs = []
            for f, b in pairs:
                c = centre(b); gx, gy = (c[1], c[0]) if swap else (c[0], c[1]); px, py = pad_c(f)
                offs.append((px - sx * gx, py - sy * gy))
            ox = sorted(o[0] for o in offs)[len(offs) // 2]; oy = sorted(o[1] for o in offs)[len(offs) // 2]
            err = sum(abs(o[0] - ox) + abs(o[1] - oy) for o in offs)
            if best is None or err < best[0]:
                best = (err, swap, sx, sy, ox, oy)
_, swap, sx, sy, ox, oy = best
parts = {}
for r, b in boxes.items():
    if r not in pcb.footprints:
        continue
    f = pcb.footprints[r]
    p0 = [b[0][k] * u for k in pl]; p1 = [b[1][k] * u for k in pl]
    xs = sorted(sx * (p[1] if swap else p[0]) + ox for p in (p0, p1))
    ys = sorted(sy * (p[0] if swap else p[1]) + oy for p in (p0, p1))
    top, bot = brd[1][ax], brd[0][ax]
    h = (b[1][ax] - top) * u if f.layer == 'F.Cu' else (bot - b[0][ax]) * u
    parts[r] = {'h': round(h, 2), 'side': f.layer, 'rect': (xs[0], ys[0], xs[1], ys[1]), 'fp': f.footprint_name.split(':')[-1]}
print(f'{len(parts)} of {len(pcb.footprints)} footprints have a model; tallest:',
      ', '.join(f'{r} {v["h"]} mm' for r, v in sorted(parts.items(), key=lambda kv: -kv[1]['h'])[:NLIST]))


def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0); dy = max(a[1] - b[3], b[1] - a[3], 0)
    return (dx * dx + dy * dy) ** .5


VERT = re.compile(r'Vertical|PinHeader(?!.*Horizontal)|PinSocket(?!.*Horizontal)|IDC|Box', re.I)
plug = []
for r, v in parts.items():
    if re.match(r'(J|P|CN|X)\d', r) and VERT.search(v['fp']):
        near = [(rr, vv['h'], round(gap(v['rect'], vv['rect']), 2)) for rr, vv in parts.items()
                if rr != r and vv['side'] == v['side'] and vv['h'] > v['h'] and gap(v['rect'], vv['rect']) < 1.5]
        if near:
            plug.append((r, v['fp'], v['h'], near))
jam = []
for r, v in parts.items():
    if v['h'] > 2.0:
        continue
    x0, y0, x1, y1 = v['rect']; sides = {}
    for rr, vv in parts.items():
        if rr == r or vv['side'] != v['side'] or vv['h'] < max(4.0, 3 * v['h']) or gap(v['rect'], vv['rect']) >= vv['h'] / 2:
            continue
        a = vv['rect']
        for s, hit in (('W', a[2] <= x0), ('E', a[0] >= x1), ('N', a[3] <= y0), ('S', a[1] >= y1)):
            if hit:
                sides.setdefault(s, []).append((rr, vv['h'], round(gap(v['rect'], a), 2)))
    if ('W' in sides and 'E' in sides) or ('N' in sides and 'S' in sides):
        jam.append((r, v['fp'], v['h'], sides))
print(f'plug: {len(plug)} vertical connector(s) with a taller part within 1.5 mm')
for row in plug[:NLIST]:
    print('   ', row)
print(f'jammed: {len(jam)} part(s) <= 2 mm between tall parts on opposite sides')
for row in jam[:NLIST]:
    print('   ', row)
