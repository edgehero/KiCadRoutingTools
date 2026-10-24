import sys, math, os
sys.path.insert(0, os.path.join(os.getcwd(), 'py_router'))
from kicad_parser import parse_kicad_pcb
from collections import Counter
p = parse_kicad_pcb(sys.argv[1])
for nm in sys.argv[2:]:
    nid = [i for i, n in p.nets.items() if n.name == nm][0]
    c = Counter()
    for s in p.segments:
        if s.net_id == nid and not getattr(s, 'graphic', False):
            c[(round(s.width, 4), s.layer)] += math.hypot(s.end_x - s.start_x, s.end_y - s.start_y)
    print(nm, {k: round(v, 2) for k, v in c.items()})
print([(l.name, l.layer_type, l.thickness, l.epsilon_r) for l in p.board_info.stackup][:6])
