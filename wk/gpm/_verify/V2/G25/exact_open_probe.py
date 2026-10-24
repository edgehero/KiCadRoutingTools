"""Call route.py's own _exact_open_grades on a written board, for a pour net,
and print the exact-fill clusters (with and without pads). Read-only on the
board (refill_islands stages a temp copy)."""
import sys
sys.path[:0] = ['py_router', '.']
from kicad_parser import parse_kicad_pcb
import route
from kicad_exact_fill import refill_islands, exact_clusters
f, net = sys.argv[1], sys.argv[2]
b = parse_kicad_pcb(f)
nid = [i for i, n in b.nets.items() if n.name == net][0]
isl = refill_islands(f)
polys = [(layer, poly) for (n, layer), ps in isl.items() if n == net for poly in ps]
cl = exact_clusters(b, nid, polys)
print(f"exact clusters for {net}: {len(cl)}; with pads: {sum(1 for c in cl if c['pads'])}; pad counts: {sorted((len(c['pads']) for c in cl), reverse=True)}")
links = [[net, [0, 0, 'F.Cu', 'zone'], [0, 0, 'B.Cu', 'zone']]]
print("_exact_open_grades ->", {k: (v[1], len(v[0]['failed_pads'])) for k, v in route._exact_open_grades(b, f, [net], links).items()})
