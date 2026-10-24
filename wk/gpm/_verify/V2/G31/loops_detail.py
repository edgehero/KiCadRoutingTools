"""List check_cycles' loop edges per net (non-bridge edges of its own graph)
and test, per 2-edge-connected block, whether deleting one loop segment changes
authoritative pad connectivity (check_net_connectivity with pcb_data). Read-only."""
import sys, math, fnmatch
from collections import defaultdict
sys.path[:0] = ['py_tools', 'py_router', '.']
from kicad_parser import parse_kicad_pcb, pour_zones
from check_connected import points_match, point_on_segment, check_net_connectivity
TOL = 0.02

def graph(segs, vias, pads):
    P = []; seg_ep = []
    for s in segs:
        i = len(P); P.append((s.start_x, s.start_y, s.layer)); j = len(P); P.append((s.end_x, s.end_y, s.layer)); seg_ep.append((i, j))
    n = len(P); par = list(range(n))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def u(a, b): par[f(a)] = f(b)
    for a in range(n):
        for b in range(a+1, n):
            if P[b][2] == P[a][2] and abs(P[b][0]-P[a][0]) < TOL and abs(P[b][1]-P[a][1]) < TOL: u(a, b)
    def jn(cx, cy, r):
        near = [i for i in range(n) if math.hypot(P[i][0]-cx, P[i][1]-cy) < r]
        for k in near[1:]: u(near[0], k)
    for v in vias: jn(v.x, v.y, max(v.size/4, TOL))
    for p in pads:
        if p.drill and p.drill > 0: jn(p.global_x, p.global_y, max(max(p.size_x, p.size_y)/4, TOL))
    reps = {}; rl = defaultdict(set)
    for i in range(n): r = f(i); reps.setdefault(r, P[i]); rl[r].add(P[i][2])
    edges = []  # (nodeA, nodeB, seg_index)
    for si, s in enumerate(segs):
        ra, rb = f(seg_ep[si][0]), f(seg_ep[si][1])
        on = []
        for r, (cx, cy, _) in reps.items():
            if r in (ra, rb) or s.layer not in rl[r]: continue
            if point_on_segment(cx, cy, s.start_x, s.start_y, s.end_x, s.end_y, TOL) and not points_match(cx, cy, s.start_x, s.start_y, TOL) and not points_match(cx, cy, s.end_x, s.end_y, TOL):
                on.append(r)
        edges.append((ra, rb, si))
        for r in on: edges.append((ra, r, si))
    return edges, reps

def bridges(edges):
    adj = defaultdict(list)
    for k, (a, b, _) in enumerate(edges): adj[a].append((b, k)); adj[b].append((a, k))
    disc = {}; low = {}; br = set(); t = [0]
    sys.setrecursionlimit(100000)
    def dfs(v, pe):
        disc[v] = low[v] = t[0]; t[0] += 1
        for w, k in adj[v]:
            if k == pe: continue
            if w in disc: low[v] = min(low[v], disc[w])
            else:
                dfs(w, k); low[v] = min(low[v], low[w])
                if low[w] > disc[v]: br.add(k)
    for v in list(adj):
        if v not in disc: dfs(v, -1)
    return br

def main(path, pat='*'):
    pcb = parse_kicad_pcb(path)
    zoned = {z.net_id for z in pour_zones(pcb.zones)}
    by = defaultdict(list)
    for s in pcb.segments: by[s.net_id].append(s)
    for nid, segs in sorted(by.items()):
        name = pcb.nets[nid].name
        if nid in zoned or not fnmatch.fnmatchcase(name, pat): continue
        vias = [v for v in pcb.vias if v.net_id == nid]; pads = pcb.pads_by_net.get(nid, [])
        edges, reps = graph(segs, vias, pads)
        br = bridges(edges)
        cyc = sorted({edges[k][2] for k in range(len(edges)) if k not in br and edges[k][0] != edges[k][1]} |
                     {edges[k][2] for k in range(len(edges)) if edges[k][0] == edges[k][1]})
        if not cyc: continue
        base = check_net_connectivity(nid, segs, vias, pads, [z for z in pcb.zones if z.net_id == nid], pcb_data=pcb)
        tot = sum(math.hypot(segs[i].end_x-segs[i].start_x, segs[i].end_y-segs[i].start_y) for i in cyc)
        print(f"NET {name}: loop segments {len(cyc)}, loop copper {tot:.3f} mm, base connected={base['connected']} comps={base['num_components']}")
        for i in cyc:
            s = segs[i]; L = math.hypot(s.end_x-s.start_x, s.end_y-s.start_y)
            rest = [x for j, x in enumerate(segs) if j != i]
            r = check_net_connectivity(nid, rest, vias, pads, [z for z in pcb.zones if z.net_id == nid], pcb_data=pcb)
            same = (r['connected'] == base['connected'] and r['num_components'] == base['num_components'])
            print(f"   {s.layer} ({s.start_x:.4f},{s.start_y:.4f})-({s.end_x:.4f},{s.end_y:.4f}) w{s.width} len {L:.4f}  delete-alone keeps connectivity: {same}")

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '*')
