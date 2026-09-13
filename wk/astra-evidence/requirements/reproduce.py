import copy, hashlib, json, pathlib, shutil, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
rows=[]
def run(label,args):
    cmd=[sys.executable,'-X','utf8']+list(map(str,args))
    start=time.time()
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=240)
    (OUT/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf8')
    summary=[json.loads(x.split('JSON_SUMMARY: ',1)[1]) for x in p.stdout.splitlines() if x.startswith('JSON_SUMMARY: ')]
    row={'label':label,'argv':cmd,'rc':p.returncode,'seconds':round(time.time()-start,2),'summary':summary[-1] if summary else None}
    rows.append(row)
    (OUT/'runs.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(label,p.returncode,row['seconds'],flush=True)
    return row
def dump(path,doc): path.write_text(json.dumps(doc,indent=2),encoding='utf8')
board=ROOT/'kicad_files/esp_prog.kicad_pcb'
brief=ROOT/'tests/fixtures/711/esp_prog.design-brief.json'
dump(OUT/'manifest.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [board,brief,ROOT/'kicad_files/flat_hierarchy.kicad_pcb']}})
for tag,extra in [('observed',[]),('decaps',['--declare-decaps'])]:
    intent=OUT/('esp_'+tag+'.json')
    run('emit_'+tag,['py_tools/check_floorplan.py',board,'--emit-intent',intent,'--declare-classes','--brief',brief]+extra)
    run('grade_'+tag,['py_tools/check_floorplan.py',board,'--intent',intent,'--brief',brief,'--require-brief-coverage','--require-rules','1','--json',OUT/('grade_'+tag+'.json')])
original=json.loads(brief.read_text())
for tag in ['carried_changed','edge_changed']:
    variant=copy.deepcopy(original)
    if tag=='carried_changed':
        variant['product']['user_top_side']='B'
        variant['interfaces'][0]['mount_mode']='through_edge'
        variant['interfaces'][0]['cable_entry']='perpendicular_top'
    else: variant['interfaces'][0]['edge']='west'
    path=OUT/(tag+'.design-brief.json');dump(path,variant)
    run('grade_'+tag,['py_tools/check_floorplan.py',board,'--intent',OUT/'esp_observed.json','--brief',path,'--require-brief-coverage','--json',OUT/('grade_'+tag+'.json')])
run('grade_no_brief',['py_tools/check_floorplan.py',board,'--intent',OUT/'esp_observed.json','--no-brief','--require-brief-coverage','--json',OUT/'grade_no_brief.json'])
flat=ROOT/'kicad_files/flat_hierarchy.kicad_pcb'
run('emit_flat',['py_tools/check_floorplan.py',flat,'--emit-intent',OUT/'flat_observed.json'])
flatdoc=json.loads((OUT/'flat_observed.json').read_text())
flatdoc.setdefault('legality_budget',{}).pop('overlap_area',None)
flatdoc['context'].setdefault('budget_withheld',{})['overlap_area']='83 blocking body pair(s) on the emitting board (controlled stale provenance)'
dump(OUT/'flat_stale.json',flatdoc)
run('grade_flat_stale',['py_tools/check_floorplan.py',flat,'--intent',OUT/'flat_stale.json','--require-rules','1','--json',OUT/'grade_flat_stale.json'])
flatdoc['legality_budget']['overlap_area']=0.0
dump(OUT/'flat_declared_zero.json',flatdoc)
run('grade_flat_declared_zero',['py_tools/check_floorplan.py',flat,'--intent',OUT/'flat_declared_zero.json','--require-rules','1','--json',OUT/'grade_flat_declared_zero.json'])
run('score_esp',['.claude/skills/plan-pcb-placement-and-routing/scripts/board_score.py',board,'--intent',OUT/'esp_observed.json','--json',OUT/'score_esp.json','--quiet'])
run('assembly_baseline',['py_tools/check_assembly.py',board,'--baseline',board,'--json',OUT/'assembly_baseline.json'])
prox=ROOT/'tests/fixtures/902/esp_prog_proximity.design-brief.json'
run('emit_proximity',['py_tools/check_floorplan.py',board,'--emit-intent',OUT/'esp_proximity.json','--brief',prox])
run('grade_proximity',['py_tools/check_floorplan.py',board,'--intent',OUT/'esp_proximity.json','--brief',prox,'--require-brief-coverage','--json',OUT/'grade_proximity.json'])
proxdoc=json.loads((OUT/'esp_proximity.json').read_text())
for row in proxdoc['proximity']: row['max_mm']=100.0
dump(OUT/'esp_proximity_relaxed.json',proxdoc)
relaxed=json.loads(prox.read_text())
for row in relaxed['proximity']: row['max_mm']=100.0
dump(OUT/'proximity_relaxed.design-brief.json',relaxed)
run('grade_proximity_relaxed',['py_tools/check_floorplan.py',board,'--intent',OUT/'esp_proximity_relaxed.json','--brief',OUT/'proximity_relaxed.design-brief.json','--require-brief-coverage','--json',OUT/'grade_proximity_relaxed.json'])
