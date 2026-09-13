import hashlib, json, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
board=ROOT/'tests/fixtures/run23/tigard_placed.kicad_pcb'
records=[]
def run(name,args):
    t=time.monotonic()
    p=subprocess.run([sys.executable,'-X','utf8',*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/(name+'.stdout.txt')).write_text(p.stdout,encoding='utf-8')
    (OUT/(name+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    records.append(dict(name=name,argv=[sys.executable,'-X','utf8',*map(str,args)],exit=p.returncode,seconds=round(time.monotonic()-t,3),stdout_lines=len(p.stdout.splitlines()),stdout_chars=len(p.stdout),checklist_on_stdout='"checklist"' in p.stdout))
run('P1-no-zone-plan',[ROOT/'.claude/skills/plan-pcb-placement/scripts/placement_driver.py','--stage','P1','--board',board])
for label,extra in [('render-default',[]),('render-quiet',['--quiet'])]:
    run(label,[ROOT/'py_tools/render_placement.py',board,'--json-out',OUT/(label+'.json'),'-o',OUT/(label+'.png'),*extra])
run('L5-stale-score-control',[ROOT/'.claude/skills/plan-pcb-placement-and-routing/scripts/loop_driver.py','--stage','L5','--board',ROOT/'tests/fixtures/run23/tigard_damaged.kicad_pcb','--ledger',OUT/'audit-ledger.jsonl','--score',OUT/'placed-score.json'])
run('loop-self-test',[ROOT/'.claude/skills/plan-pcb-placement-and-routing/scripts/loop_driver.py','--self-test'])
paths=['.claude/skills/plan-pcb-placement/SKILL.md','.claude/skills/plan-pcb-placement-and-routing/SKILL.md','.claude/skills/plan-pcb-routing/SKILL.md','.claude/skills/plan-pcb-placement/scripts/placement_driver.py','.claude/skills/plan-pcb-placement-and-routing/scripts/loop_driver.py']
summary={'commands':records,'files':{p:{'lines':len((ROOT/p).read_text(encoding='utf-8').splitlines()),'bytes':len((ROOT/p).read_bytes())} for p in paths}}
for label in ('placed','damaged'):
    s=json.loads((OUT/(label+'-score.json')).read_text())
    summary[label]={'blocking':s['blocking'],'blocking_by':s['blocking_by'],'terms':{k:v.get('value') for k,v in s['placement']['terms'].items()}}
(OUT/'supplement-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
