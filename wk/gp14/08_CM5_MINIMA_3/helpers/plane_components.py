"""Render the fill-component map check_impedance uses for one reference layer,
with the impedance nets' crossings overlaid.  Diagnosis helper (TOOL_GAPS):
no repo tool shows WHY check_impedance reports a 'split' (which fill
components the trace moves between).
usage: python3 helpers/plane_components.py BOARD LAYER OUT.png [imp.json]"""
import sys, json
sys.path.insert(0, 'py_router'); sys.path.insert(0, 'py_tools')
import numpy as np
from PIL import Image, ImageDraw
from kicad_parser import parse_kicad_pcb
from plane_fill_model import get_zone_model
board, layer, out = sys.argv[1:4]
pcb = parse_kicad_pcb(board)
SC = 20  # px per mm
bx0, by0, bx1, by1 = pcb.board_info.board_bounds
W, H = int((bx1 - bx0) * SC) + 1, int((by1 - by0) * SC) + 1
im = Image.new('RGB', (W, H), (255, 255, 255)); dr = ImageDraw.Draw(im)
rng = np.random.default_rng(1)
for z in pcb.zones:
    if z.layer != layer or not z.net_id:
        continue
    m = get_zone_model(pcb, z)
    lab = m.labels; n = int(lab.max())
    counts = np.bincount(lab.ravel())
    print(layer, pcb.nets[z.net_id].name, 'components', n, 'largest cells', sorted(counts[1:], reverse=True)[:8])
    cols = (rng.random((n + 1, 3)) * 200 + 40).astype(np.uint8); cols[0] = (255, 255, 255)
    big = int(np.argmax(np.r_[0, counts[1:]])); cols[big] = (200, 200, 200)
    for i in range(lab.shape[0]):
        for j in range(lab.shape[1]):
            c = lab[i, j]
            if c:
                x = (m.x0 + i * m.cell - bx0) * SC; y = (m.y0 + j * m.cell - by0) * SC
                dr.rectangle([x, y, x + m.cell * SC, y + m.cell * SC], fill=tuple(int(v) for v in cols[c]))
if len(sys.argv) > 4:
    d = json.load(open(sys.argv[4]))
    for net in d['nets']:
        for c in net.get('crossing_detail', []):
            if c['ref_layer'] == layer:
                x = (c['x'] - bx0) * SC; y = (c['y'] - by0) * SC
                col = (0, 0, 0) if c['kind'] == 'split' else (255, 0, 0)
                dr.line([x - 8, y - 8, x + 8, y + 8], fill=col, width=3); dr.line([x - 8, y + 8, x + 8, y - 8], fill=col, width=3)
im.save(out); print('wrote', out)
