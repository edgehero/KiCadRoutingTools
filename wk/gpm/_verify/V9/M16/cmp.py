import sys
sys.path.insert(0,'py_router')
from kicad_parser import parse_kicad_pcb
names=('Net-(J1-Pin_1)','VIN')
def geo(p):
    pcb=parse_kicad_pcb(p)
    ids={n.net_id:n.name for n in pcb.nets.values() if n.name in names}
    s={(ids[x.net_id],x.layer,round(x.start_x,4),round(x.start_y,4),round(x.end_x,4),round(x.end_y,4),round(x.width,4)) for x in pcb.segments if x.net_id in ids}
    v={(ids[x.net_id],round(x.x,4),round(x.y,4)) for x in pcb.vias if x.net_id in ids}
    return s,v
s0,v0=geo(sys.argv[1])
for p in sys.argv[2:]:
    s,v=geo(p); print(p,'segs',len(s),'identical_to_input',s==s0 and v==v0,'vias',len(v),'(input segs',len(s0),'vias',len(v0),')')
