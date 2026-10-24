import sys, math
sys.path.insert(0,'py_router')
from kicad_parser import parse_kicad_pcb
b=parse_kicad_pcb(sys.argv[1])
px,py=float(sys.argv[2]),float(sys.argv[3]); R=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
def dseg(s):
    ax,ay,bx,by=s.start_x,s.start_y,s.end_x,s.end_y
    dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(ax+t*dx-px, ay+t*dy-py)
near={}
for s in b.segments:
    d=dseg(s)
    if d<R: near.setdefault((b.nets[s.net_id].name if s.net_id in b.nets else s.net_id, s.layer),[]).append(round(d,3))
for v in b.vias:
    d=math.hypot(v.x-px,v.y-py)
    if d<R: near.setdefault((b.nets[v.net_id].name,'via'),[]).append(round(d,3))
for k,v in sorted(near.items(), key=lambda kv:min(kv[1])): print(k, sorted(v)[:4])
