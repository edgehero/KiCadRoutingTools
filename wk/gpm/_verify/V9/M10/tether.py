import sys
sys.path[:0] = ['py_router', 'py_placer']
from kicad_parser import parse_kicad_pcb
from placement import groups
for p in sys.argv[1:]:
    pcb = parse_kicad_pcb(p)
    near, beyond, orphans = groups.decap_populations(pcb)
    hit = [(ic, c, d) for ic, lst in near.items() for c, d in lst if c in ('C9','C13','C8','C10')]
    print(p, 'near', hit, 'beyond', [b for b in beyond if b[0] in ('C9','C13','C8','C10')])
