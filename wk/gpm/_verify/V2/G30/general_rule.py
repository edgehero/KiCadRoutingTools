"""Candidate generalisation of check_weird.kicad_dangling_end (#1217): keep its
via/pad/zone abstention, but count a track touching ONE end for that end (not
abstain). Compare the ends it names with KiCad's track_dangling list. Read-only."""
import sys, math, json
from collections import defaultdict
sys.path[:0] = ['py_router', '.']
from kicad_parser import parse_kicad_pcb
from check_weird import kicad_dangling_end
from pcb_modification import _pt_seg_dist
from connectivity import endpoint_reaches_pad, via_copper_layers
from check_connected import point_in_polygon
def gen(s, others, vias, pads, zones, cl):
    acc = s.width / 2.0; ends = ((s.start_x, s.start_y), (s.end_x, s.end_y))
    t = []
    for o in others:
        if o is s or o.layer != s.layer or getattr(o, 'graphic', False): continue
        h = [_pt_seg_dist(x, y, o.start_x, o.start_y, o.end_x, o.end_y) <= o.width/2 + acc + 1e-9 for x, y in ends]
        if any(h): t.append((o, h))
    if not t: return None
    if any(s.layer in via_copper_layers(v, cl) and min(math.hypot(v.x-x, v.y-y) for x, y in ends) <= v.size/2 + acc + 1e-9 for v in vias): return None
    if any(endpoint_reaches_pad(x, y, acc, (s.layer,), p) for p in pads for x, y in ends): return None
    if any(z.layer == s.layer and z.polygon and any(point_in_polygon(x, y, z.polygon) for x, y in ends) for z in zones): return None
    c = [0, 0]
    for o, h in t:
        if h[0] and h[1]:
            d0, d1 = (min(math.hypot(o.start_x-x, o.start_y-y), math.hypot(o.end_x-x, o.end_y-y)) for x, y in ends)
            c[0 if d0 < d1 else 1] += 1
        else:
            c[0 if h[0] else 1] += 1
    if all(c): return None
    return ends[0] if c[0] == 0 else ends[1]
pcb = parse_kicad_pcb(sys.argv[1]); kd = json.load(open(sys.argv[2]))
K = [(v['items'][0]['pos']['x'], v['items'][0]['pos']['y'], v['items'][0]['description']) for v in kd['violations'] if v['type'] == 'track_dangling']
cl = pcb.board_info.copper_layers
segs = defaultdict(list)
for s in pcb.segments: segs[s.net_id].append(s)
vias = defaultdict(list)
for v in pcb.vias: vias[v.net_id].append(v)
zones = defaultdict(list)
for z in pcb.zones: zones[z.net_id].append(z)
hits_old, hits_new = [], []
for nid, ss in segs.items():
    if nid == 0: continue
    for s in ss:
        a = kicad_dangling_end(s, ss, vias[nid], pcb.pads_by_net.get(nid, []), zones[nid], cl)
        b = gen(s, ss, vias[nid], pcb.pads_by_net.get(nid, []), zones[nid], cl)
        if a: hits_old.append((pcb.nets[nid].name, s.layer, a, s))
        if b: hits_new.append((pcb.nets[nid].name, s.layer, b, s))
def matched(h):
    s = h[3]
    return any(min(math.hypot(kx-x, ky-y) for x, y in ((s.start_x, s.start_y), (s.end_x, s.end_y))) < 0.005 for kx, ky, _ in K)
print(f"KiCad track_dangling: {len(K)}")
print(f"current kicad_dangling_end: {len(hits_old)} findings, {sum(map(matched, hits_old))} match KiCad")
print(f"generalised (one-end touchers counted): {len(hits_new)} findings, {sum(map(matched, hits_new))} match KiCad")
for h in hits_new: print("   ", h[0], h[1], tuple(round(c, 3) for c in h[2]), 'KiCad agrees' if matched(h) else 'KiCad SILENT')
