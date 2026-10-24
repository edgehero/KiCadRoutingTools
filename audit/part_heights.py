#!/usr/bin/env python3
"""gpm audit E: every part's real height, from KiCad's own 3D models.

    python3 -X utf8 wk/gpm/_audit/part_heights.py BOARD.kicad_pcb STEM [--json OUT]

Exports the board as GLB through kicad-cli, from a temp copy whose model paths iso_render.py resolves, and reads
one node per footprint (KiCad names each by its reference). Per part: the side, its height above its own board
face, and its body's plan rectangle in KiCad board coordinates (mm, y down). A part with no model is listed with
height None. Prints how many parts have a model.
"""
import json
import math
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'wk', 'gpm', '_staging'), os.path.join(ROOT, 'py_router')]
import iso_render as ir  # noqa: E402
from kicad_parser import parse_kicad_pcb  # noqa: E402

CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def compose(parent, node):
    """4x4 world matrix (row-major lists) of node under parent."""
    if 'matrix' in node:
        m = node['matrix']
        local = [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]], [m[2], m[6], m[10], m[14]], [0, 0, 0, 1]]
    else:
        r = qmat(node.get('rotation', [0, 0, 0, 1]))
        s = node.get('scale', [1, 1, 1])
        t = node.get('translation', [0, 0, 0])
        local = [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]
    return [[sum(parent[i][k] * local[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def apply(m, p):
    return [m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] for i in range(3)]


def glb_boxes(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n])
    acc = j.get('accessors', [])
    boxes = {}
    I = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    def walk(ni, mat, owner):
        node = j['nodes'][ni]
        w = compose(mat, node)
        name = node.get('name')
        own = owner
        if owner is None and name and not name.startswith('=>'):
            own = name
        if 'mesh' in node:
            for prim in j['meshes'][node['mesh']]['primitives']:
                a = acc[prim['attributes']['POSITION']]
                lo, hi = a['min'], a['max']
                for cx in (lo[0], hi[0]):
                    for cy in (lo[1], hi[1]):
                        for cz in (lo[2], hi[2]):
                            p = apply(w, (cx, cy, cz))
                            bb = boxes.setdefault(own or '__board__', [[1e9] * 3, [-1e9] * 3])
                            for k in range(3):
                                bb[0][k] = min(bb[0][k], p[k]); bb[1][k] = max(bb[1][k], p[k])
        for c in node.get('children', []):
            walk(c, w, own)
    for root in j['scenes'][j.get('scene', 0)]['nodes']:
        walk(root, I, None)
    return boxes


def heights(board, stem):
    prj = ir.source_dir(stem)
    text = open(board, encoding='utf-8', newline='').read()

    def fix(m):
        p = ir.resolve(m.group(1), prj)
        if not os.path.isfile(p) and p.lower().endswith('.wrl') and os.path.isfile(p[:-4] + '.step'):
            p = p[:-4] + '.step'
        return '(model "%s"' % p
    new = ir.MODEL.sub(fix, text)
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, 'b.kicad_pcb')
        open(tmp, 'w', encoding='utf-8', newline='').write(new)
        subprocess.run([CLI, 'pcb', 'export', 'glb', tmp, '-o', os.path.join(td, 'b.glb')], capture_output=True)
        boxes = glb_boxes(os.path.join(td, 'b.glb'))
    pcb = parse_kicad_pcb(board)
    brd = boxes.pop('__board__')
    # the thickness axis is the one along which the board body is thinnest
    ax = min(range(3), key=lambda k: brd[1][k] - brd[0][k])
    plan = [k for k in range(3) if k != ax]
    unit = 1000.0 if (brd[1][plan[0]] - brd[0][plan[0]]) < 2 else 1.0  # GLB in metres
    top, bot = brd[1][ax], brd[0][ax]
    # map GLB plan axes to KiCad x/y by least squares over the parts' positions (sign and swap)
    out = {}
    pairs = [(pcb.footprints[r], bb) for r, bb in boxes.items() if r in pcb.footprints]
    best = None
    for swap in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                err = 0
                for f, bb in pairs:
                    c = [(bb[0][k] + bb[1][k]) / 2 * unit for k in plan]
                    gx, gy = (c[1], c[0]) if swap else (c[0], c[1])
                    err += abs(sx * gx - f.x) + abs(sy * gy - f.y)
                if best is None or err < best[0]:
                    best = (err, swap, sx, sy)
    _, swap, sx, sy = best
    off = []
    for f, bb in pairs:
        c = [(bb[0][k] + bb[1][k]) / 2 * unit for k in plan]
        gx, gy = (c[1], c[0]) if swap else (c[0], c[1])
        off.append((f.x - sx * gx, f.y - sy * gy))
    ox = sorted(o[0] for o in off)[len(off) // 2] if off else 0
    oy = sorted(o[1] for o in off)[len(off) // 2] if off else 0
    for r, f in pcb.footprints.items():
        bb = boxes.get(r)
        if not bb:
            out[r] = {'side': f.layer, 'height': None, 'rect': None}
            continue
        p0 = [bb[0][k] * unit for k in plan]; p1 = [bb[1][k] * unit for k in plan]
        xs = sorted(sx * (p[1] if swap else p[0]) + ox for p in (p0, p1))
        ys = sorted(sy * (p[0] if swap else p[1]) + oy for p in (p0, p1))
        h = (bb[1][ax] - top) * unit if f.layer == 'F.Cu' else (bot - bb[0][ax]) * unit
        under = (bb[0][ax] - top) * unit if f.layer == 'F.Cu' else (bot - bb[1][ax]) * unit
        out[r] = {'side': f.layer, 'height': round(h, 2), 'bottom': round(under, 2),
                  'rect': [round(xs[0], 2), round(ys[0], 2), round(xs[1], 2), round(ys[1], 2)]}
    return out, {'thickness_mm': round((top - bot) * unit, 2), 'parts': len(pcb.footprints),
                 'with_model': sum(1 for v in out.values() if v['height'] is not None),
                 'fit_mm_per_part': round(best[0] / max(len(pairs), 1), 3)}


if __name__ == '__main__':
    o, info = heights(sys.argv[1], sys.argv[2])
    print(json.dumps(info))
    if '--json' in sys.argv:
        json.dump({'info': info, 'parts': o}, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    for r, v in sorted(o.items(), key=lambda kv: -(kv[1]['height'] or 0))[:8]:
        print(r, v)
