"""Bounded driver/ledger audit against existing Tigard fixtures; no production edits."""
import hashlib, json, pathlib, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent
PY = sys.executable
records = []
def run(name, args):
    start = time.monotonic()
    p = subprocess.run([PY, '-X', 'utf8', *map(str,args)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (OUT/(name+'.stdout.txt')).write_text(p.stdout, encoding='utf-8')
    (OUT/(name+'.stderr.txt')).write_text(p.stderr, encoding='utf-8')
    records.append(dict(name=name, argv=[PY,'-X','utf8',*map(str,args)], exit=p.returncode, seconds=round(time.monotonic()-start,3), stdout_lines=len(p.stdout.splitlines()), stdout_chars=len(p.stdout)))
    return p
A = ROOT/'tests/fixtures/run23/tigard_placed.kicad_pcb'
B = ROOT/'tests/fixtures/run23/tigard_damaged.kicad_pcb'
score = ROOT/'.claude/skills/plan-pcb-placement-and-routing/scripts/board_score.py'
loop = ROOT/'.claude/skills/plan-pcb-placement-and-routing/scripts/loop_driver.py'
conv = ROOT/'py_placer/converge.py'
ledger = OUT/'audit-ledger.jsonl'
if ledger.exists():
    raise SystemExit('Use a fresh artifact directory; refusing to append/rewrite a previous run')
for label,board in [('placed',A),('damaged',B)]:
    run(label+'-score',[score,board,'--placement-terms','--json',OUT/(label+'-score.json')])
run('L1-default',[loop,'--stage','L1','--board',A,'--ledger',OUT/'l1-default/ledger.jsonl'])
run('L1-inline',[loop,'--stage','L1','--board',A,'--ledger',OUT/'l1-inline/ledger.jsonl','--no-delegate'])
run('record-initial',[conv,'record','--board',A,'--ledger',ledger,'--store',OUT/'store','--kind','completion','--score-file',OUT/'placed-score.json','--lever','audit-fixture'])
run('L5-no-classification-1',[loop,'--stage','L5','--board',A,'--ledger',ledger,'--score',OUT/'placed-score.json'])
run('L5-no-classification-2',[loop,'--stage','L5','--board',A,'--ledger',ledger,'--score',OUT/'placed-score.json'])
run('L4-no-shape',[loop,'--stage','L4','--board',A,'--ledger',ledger])
run('exhaust-placement',[conv,'record','--board',A,'--ledger',ledger,'--store',OUT/'store','--kind','systemic','--exhausted','placement','--exhausted-reason','AUDIT TEST declaration on placed fixture; deliberately not a real exhaustion claim'])
run('exhaust-routing',[conv,'record','--board',A,'--ledger',ledger,'--store',OUT/'store','--kind','systemic','--exhausted','routing','--exhausted-reason','AUDIT TEST declaration on placed fixture; deliberately not a real exhaustion claim'])
run('verdict-original-board',[conv,'verdict','--ledger',ledger,'--score',OUT/'placed-score.json'])
run('record-changed-systemic',[conv,'record','--board',B,'--ledger',ledger,'--store',OUT/'store','--kind','systemic','--score-file',OUT/'damaged-score.json','--lever','audit-board-replacement'])
run('verdict-changed-board',[conv,'verdict','--ledger',ledger,'--score',OUT/'damaged-score.json'])
run('L5-changed-board',[loop,'--stage','L5','--board',B,'--ledger',ledger,'--score',OUT/'damaged-score.json'])
run('record-stale-score-control',[conv,'record','--board',B,'--ledger',ledger,'--store',OUT/'store','--kind','systemic','--score-file',OUT/'placed-score.json'])
run('record-placement-lap-control',[conv,'record','--board',B,'--ledger',ledger,'--store',OUT/'store','--kind','placement','--score-file',OUT/'damaged-score.json','--lever','audit-lap-control'])
run('verdict-after-placement-lap',[conv,'verdict','--ledger',ledger,'--score',OUT/'damaged-score.json'])
run('handoff-regression',[ROOT/'tests/test_890_delegation_handoff.py'])
summary={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (A,B,A.with_suffix('.kicad_pro'),B.with_suffix('.kicad_pro')) if p.exists()},'commands':records}
for label in ('placed','damaged'):
    s=json.loads((OUT/(label+'-score.json')).read_text())
    summary[label]={k:s.get(k) for k in ('board_sha','blocking','blocking_by','quality','placement','ungraded','unknown')}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
