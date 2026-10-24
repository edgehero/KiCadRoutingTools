import sys, math
from collections import defaultdict, deque
sys.path[:0] = ['wk/gpm/_verify/V2/G31', 'py_tools', 'py_router', '.']
from loops_detail import graph
from kicad_parser import parse_kicad_pcb
pcb = parse_kicad_pcb(sys.argv[1]); name = sys.argv[2]
nid = [n for n, v in pcb.nets.items() if v.name == name][0]
segs = [s for s in pcb.segments if s.net_id == nid]
vias = [v for v in pcb.vias if v.net_id == nid]; pads = pcb.pads_by_net.get(nid, [])
edges, reps = graph(segs, vias, pads)
par = {}; adj = defaultdict(list)
for k, (a, b, si) in enumerate(edges): adj[a].append((b, k)); adj[b].append((a, k))
tree = set(); seen = set()
for r in adj:
    if r in seen: continue
    seen.add(r); q = deque([r]); par[r] = (None, None)
    while q:
        v = q.popleft()
        for w, k in adj[v]:
            if w not in seen: seen.add(w); par[w] = (v, k); tree.add(k); q.append(w)
def path(v):
    out = [v]
    while par[v][0] is not None: v = par[v][0]; out.append(v)
    return out
def desc(k):
    a, b, si = edges[k]; s = segs[si]
    return f"seg#{si} {s.layer} ({s.start_x:.4f},{s.start_y:.4f})-({s.end_x:.4f},{s.end_y:.4f}) w{s.width}" + ("" if (a, b) == (None, None) else "")
for k, (a, b, si) in enumerate(edges):
    if k in tree: continue
    pa, pb = path(a), path(b); sa = set(pa)
    lca = next(x for x in pb if x in sa)
    ks = [k]
    for p in (pa, pb):
        v = p[0]
        while v != lca: ks.append(par[v][1]); v = par[v][0]
    print("CYCLE:"); [print("   ", desc(x), "[T-split edge]" if edges[x][1] != reps and (edges[x][0], edges[x][1]) != (None,) and False else "") for x in ks]
    print("   nodes:", [tuple(round(c, 4) if isinstance(c, float) else c for c in reps[n]) for n in set([edges[x][0] for x in ks] + [edges[x][1] for x in ks])])
