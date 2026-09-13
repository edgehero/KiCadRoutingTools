"""Independent identical checks of completed pilot arms; no optimizer score as truth."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output',type=Path,required=True,help='Fresh evidence directory')
OUT=ap.parse_args().output.resolve()
if OUT.exists():
    raise SystemExit('Choose a fresh output directory; recorded evidence is not overwritten')
OUT.mkdir(parents=True)
for p in ('py_router','py_placer','py_tools','tests/stress'):
    sys.path.insert(0,str(ROOT/p))
from kicad_parser import parse_kicad_pcb
from placement.parser import extract_locked_refs
from placement.design_brief import load_brief,compile_brief
from placement.floorplan import intent_from_dict,grade,to_json
from strip_copper_only import _forms

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pose(f): return [f.x,f.y,f.rotation,f.layer]
def nets(pcb):
    return sorted((r,str(p.pad_number),str(p.net_name))
                  for r,f in pcb.footprints.items() for p in f.pads)
def outlines(path):
    text=path.read_text(encoding='utf-8')
    return sorted(text[s:e] for s,e,d,h in _forms(text)
                  if h.startswith('gr_') and '(layer "Edge.Cuts")' in text[s:e])
def run(label,args):
    argv=[sys.executable,'-X','utf8']+list(map(str,args))
    start=time.monotonic()
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,
                     encoding='utf-8',errors='replace',timeout=60)
    (OUT/(label+'.stdout.txt')).write_text(p.stdout,encoding='utf-8')
    (OUT/(label+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    return {'argv':argv,'exit':p.returncode,'seconds':round(time.monotonic()-start,3)}
results={'purpose':__doc__,'arms':[],'limits':[
 'One partial-placement trial per arm; no statistical claim or general model ranking.',
 'Clearance .25mm and edge .55mm are shared repository fallback floors, not fab-validated specs.',
 'Explicit oscillator pad-distance limit8mm is a study requirement, not a product electrical specification.',
 'No routing, timing/signal-integrity or fabrication readiness established.',
 'Current pose/body/graphic coverage gaps remain; missing coverage is reported.']}
for arm in ('current_skill','concise_contract'):
    d=HERE/'arms'/arm
    if not (d/'RETURN.md').exists():
        raise SystemExit('Arm has not finished: '+arm)
    base=d/'board.kicad_pcb'; final=d/'final.kicad_pcb'
    row={'arm':arm,'input_sha256':sha(base),'return_sha256':sha(d/'RETURN.md'),
         'final_exists':final.exists()}
    if not final.exists(): results['arms'].append(row); continue
    pb=parse_kicad_pcb(str(base)); pf=parse_kicad_pcb(str(final))
    fixed=json.loads((d/'FIXED_POSES.json').read_text(encoding='utf-8'))
    row.update({'final_sha256':sha(final),'input_footprints':len(pb.footprints),
     'final_footprints':len(pf.footprints),'fixed_pose_changes':{
      r:{'expected':v,'actual':pose(pf.footprints[r]) if r in pf.footprints else None}
      for r,v in fixed.items() if r not in pf.footprints or pose(pf.footprints[r])!=v},
     'fixed_locks_missing':sorted(set(fixed)-set(extract_locked_refs(str(final)))),
     'net_assignment_unchanged':nets(pb)==nets(pf),
     'outline_unchanged':outlines(base)==outlines(final),
     'brief_unchanged':final.with_suffix('.design-brief.json').exists() and
        sha(base.with_suffix('.design-brief.json'))==sha(final.with_suffix('.design-brief.json')),
     'free_poses':{r:pose(pf.footprints[r]) for r in ('U1','Y1','C2','C4')}})
    # Compile only the explicit brief fragment. Do not derive acceptance limits
    # from either candidate, or inherit stale budgets from the input pile.
    frag,coverage=compile_brief(load_brief(str(base.with_suffix('.design-brief.json'))),
                               board_refs=list(pb.footprints))
    intent=intent_from_dict({'schema':1,'kind':'floorplan-intent',**frag})
    g=grade(intent,pf,str(final),clearance=.25,board_edge_clearance=.55)
    row['explicit_brief_grade']=to_json(g)
    row['brief_compilation_coverage']=coverage
    for kind,tool,extra in [('drc','py_router/check_drc.py',['--check-pad-edge',
         '--clearance','.25','--board-edge-clearance','.55','--clearance-margin','0']),
         ('assembly','py_tools/check_assembly.py',['--clearance','.25','--baseline',base])]:
        report=OUT/(arm+'_'+kind+'.json')
        row[kind+'_command']=run(arm+'_'+kind,[tool,final,*extra,'--json',report])
        row[kind]=json.loads(report.read_text(encoding='utf-8')) if report.exists() else None
    results['arms'].append(row)
(OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
