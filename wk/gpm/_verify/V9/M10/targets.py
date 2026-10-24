import sys, json, math
sys.path[:0] = ['py_router', 'py_placer']
from kicad_parser import parse_kicad_pcb
from placement import templates
pcb = parse_kicad_pcb(sys.argv[1])
row = json.load(open(sys.argv[2]))
u = pcb.footprints[row['anchor']]
ap = (u.x, u.y, u.rotation)
print('# anchor', row['anchor'], ap, u.layer, file=sys.stderr)
ops = []
for m in row['members']:
    x, y, r = templates.member_target(ap, m)
    ops += ['set', m['ref'], f'{x:.4f}', f'{y:.4f}', '--rot', f'{r % 360:.1f}']
print(' '.join(ops))
