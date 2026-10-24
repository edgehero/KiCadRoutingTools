import sys
sys.path.insert(0,'py_router')
from kicad_parser import parse_kicad_pcb
def segs(p):
    pcb=parse_kicad_pcb(p)
    ids={n.net_id:n.name for n in pcb.nets.values() if n.name in ('/USB_DP','/USB_DM')}
    out=set()
    for s in pcb.segments:
        if s.net_id in ids:
            out.add((ids[s.net_id],s.layer,round(s.start_x,4),round(s.start_y,4),round(s.end_x,4),round(s.end_y,4)))
    vias=sum(1 for v in pcb.vias if v.net_id in ids)
    return out,vias
base,bv=segs(sys.argv[1])
print(sys.argv[1],'pair segs',len(base),'vias',bv)
for p in sys.argv[2:]:
    s,v=segs(p)
    print(p,'segs',len(s),'surviving from first',len(base&s),'vias',v)
