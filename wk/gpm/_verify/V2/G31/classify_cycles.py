"""Classify every fundamental cycle check_cycles counts: span (max node-node
distance), whether it is a self-loop (one segment shorter than the 0.02 tol),
and whether EVERY segment in it can be deleted alone with authoritative
connectivity unchanged (a genuinely redundant loop). Read-only."""
import sys, math
from collections import defaultdict, deque
sys.path[:0] = ['wk/gpm/_verify/V2/G31', 'py_tools', 'py_router', '.']
from loops_detail import graph
from kicad_parser import parse_kicad_pcb, pour_zones
from check_connected import check_net_connectivity
pcb = parse_kicad_pcb(sys.argv[1])
zoned = {z.net_id for z in pour_zones(pcb.zones)}
by = defaultdict(list)
for s in pcb.segments: by[s.net_id].append(s)
tot = defaultdict(int)
for nid, segs in by.items():
    if nid in zoned: continue
    vias = [v for v in pcb.vias if v.net_id == nid]; pads = pcb.pads_by_net.get(nid, [])
    zones = [z for z in pcb.zones if z.net_id == nid]
    edges, reps = graph(segs, vias, pads)
    adj = defaultdict(list)
    for k, (a, b, si) in enumerate(edges): adj[a].append((b, k)); adj[b].append((a, k))
    par = {}; tree = set(); seen = set()
    for r in adj:
        if r in seen: continue
        seen.add(r); q = deque([r]); par[r] = (None, None)
        while q:
            v = q.popleft()
            for w, k in adj[v]:
                if w not in seen: seen.add(w); par[w] = (v, k); tree.add(k); q.append(w)
    base = None
    for k, (a, b, si) in enumerate(edges):
        if k in tree: continue
        def path(v):
            out = [v]
            while par[v][0] is not None: v = par[v][0]; out.append(v)
            return out
        pa, pb = path(a), path(b); sa = set(pa); lca = next(x for x in pb if x in sa)
        ks = [k]
        for p in (pa, pb):
            v = p[0]
            while v != lca: ks.append(par[v][1]); v = par[v][0]
        nodes = {edges[x][0] for x in ks} | {edges[x][1] for x in ks}
        pts = [reps[n] for n in nodes]
        span = max((math.hypot(p[0]-q[0], p[1]-q[1]) for p in pts for q in pts), default=0)
        sids = sorted({edges[x][2] for x in ks})
        if base is None: base = check_net_connectivity(nid, segs, vias, pads, zones, pcb_data=pcb)
        allrem = True
        for si in sids:
            r = check_net_connectivity(nid, [x for j, x in enumerate(segs) if j != si], vias, pads, zones, pcb_data=pcb)
            if (r['connected'], r['num_components']) != (base['connected'], base['num_components']): allrem = False; break
        kind = 'self-loop(<0.02mm seg)' if a == b else ('genuine' if allrem and span > 0.3 else ('zero-area(span<=0.3)' if span <= 0.3 else 'not-a-loop(deletion splits)'))
        if a != b and not allrem: kind = 'not-a-loop(deletion splits)'
        tot[kind] += 1
        print(f"{pcb.nets[nid].name:20s} span {span:7.3f} mm  segs {len(sids)}  every-seg-removable {allrem}  -> {kind}")
print("TOTAL", dict(tot))
