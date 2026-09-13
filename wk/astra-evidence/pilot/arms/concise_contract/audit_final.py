import json, math, pathlib, re, pcbnew
root=pathlib.Path('wk/astra-evidence/pilot/arms/concise_contract')
a=(root/'board.kicad_pcb').read_text(); b=(root/'final.kicad_pcb').read_text()
pat=re.compile(r'\t\(footprint .*?\n\t\)\n', re.S)
old=pat.findall(a); new=pat.findall(b)
assert len(old)==len(new)==21
allowed={'U1','Y1','C2','C4'}; changed=[]; fixed=[]
at=re.compile(r'\(at ([^()]*)\)')
for x,y in zip(old,new):
 ref=re.search(r'\(property "Reference" "([^"]*)"',x).group(1)
 if ref not in allowed:
  assert x==y, ref
  fixed.append(ref)
 else:
  assert at.sub('(at POSE)',x)==at.sub('(at POSE)',y),ref
  ax=[list(map(float,t.split())) for t in at.findall(x)]; ay=[list(map(float,t.split())) for t in at.findall(y)]
  delta=(ay[0][2] if len(ay[0])>2 else 0)-(ax[0][2] if len(ax[0])>2 else 0)
  for p,q in zip(ax[1:],ay[1:]):
   assert p[:2]==q[:2], (ref,p,q)
   pd=p[2] if len(p)>2 else 0; qd=q[2] if len(q)>2 else 0
   assert abs((qd-pd-delta)%360)<1e-7,(ref,p,q)
  if x!=y: changed.append(ref)
assert pat.sub('',a)==pat.sub('',b),'outside footprint data changed'
ba=pcbnew.LoadBoard(str(root/'board.kicad_pcb')); bb=pcbnew.LoadBoard(str(root/'final.kicad_pcb'))
fa={str(f.m_Uuid.AsString()):f for f in ba.GetFootprints()}; fb={str(f.m_Uuid.AsString()):f for f in bb.GetFootprints()}
assert fa.keys()==fb.keys()
for uid,f in fa.items():
 g=fb[uid]
 assert f.IsLocked()==g.IsLocked(), f.GetReference()
 assert f.GetLayer()==g.GetLayer(),f.GetReference()
 if f.GetReference() not in allowed:
  assert f.IsLocked()
  assert f.GetPosition()==g.GetPosition() and f.GetOrientationDegrees()==g.GetOrientationDegrees()
fps={f.GetReference():f for f in bb.GetFootprints()}
def pad(ref,num): return next(p for p in fps[ref].Pads() if p.GetNumber()==num)
def rect(p):
 assert p.GetShape()==pcbnew.PAD_SHAPE_RECT
 x,y=p.GetPosition().x/1e6,p.GetPosition().y/1e6
 sx,sy=p.GetSize().x/1e6,p.GetSize().y/1e6
 angle=p.GetOrientationDegrees()%180
 assert abs(angle)<1e-7 or abs(angle-90)<1e-7
 if abs(angle-90)<1e-7:sx,sy=sy,sx
 return x-sx/2,y-sy/2,x+sx/2,y+sy/2
def gap(a,b):
 r,s=rect(a),rect(b)
 return math.hypot(max(r[0]-s[2],s[0]-r[2],0),max(r[1]-s[3],s[1]-r[3],0))
links=[('Y1','1','U1','9'),('Y1','2','U1','10'),('C4','1','Y1','1'),('C2','1','Y1','2'),('C4','1','U1','9'),('C2','1','U1','10')]
measurements=[]
for ar,ap,br,bp in links:
 p,q=pad(ar,ap),pad(br,bp)
 assert p.GetNetname()==q.GetNetname()
 measurements.append({'a':ar+'.'+ap,'b':br+'.'+bp,'net':p.GetNetname(),'exact_rect_pad_edge_mm':round(gap(p,q),6)})
result={'immutable_outside_movable_poses':True,'fixed_footprints_byte_identical':len(fixed),'all_fixed_locks_retained':True,'all_layers_unchanged':True,'changed_refs':changed,'movable_footprint_local_geometry_retained':True,'measurement_basis':'exact axis-aligned rectangular copper pad edges; actual pad orientations verified multiples of 90 degrees','measurements':measurements,'brief_8mm_pass':all(m['exact_rect_pad_edge_mm']<=8 for m in measurements[:2])}
(root/'invariants-and-distances.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
