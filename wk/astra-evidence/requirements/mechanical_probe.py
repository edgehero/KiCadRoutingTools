import hashlib, json, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
CASE=OUT/'mechanical_case'; CASE.mkdir(exist_ok=True)
board=CASE/'esp_prog.kicad_pcb'
shutil.copy2(ROOT/'kicad_files/esp_prog.kicad_pcb',board)
shutil.copy2(ROOT/'tests/fixtures/711/esp_prog.design-brief.json',CASE/'esp_prog.design-brief.json')
rows=[]
for tag in ['absent','contradictory']:
    mech=CASE/'mechanical.json'
    if tag=='absent' and mech.exists(): mech.unlink()
    if tag=='contradictory':
        mech.write_text(json.dumps({'interfaces':[{'ref':'USB1','edge':'west'}],'fixed':[{'ref':'C1','x':0,'y':0,'reason':'controlled deliberately incompatible declaration'}],'project':{'floors':{'clearance':0.4}}},indent=2),encoding='utf8')
    intent=OUT/('mechanical_'+tag+'.json')
    cmd=[sys.executable,'-X','utf8','py_tools/check_floorplan.py',str(board),'--emit-intent',str(intent),'--declare-classes']
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding='utf8',errors='replace',timeout=60)
    (OUT/('mechanical_'+tag+'.log')).write_text(p.stdout+p.stderr,encoding='utf8')
    rows.append({'label':tag,'argv':cmd,'rc':p.returncode,'intent_sha256':hashlib.sha256(intent.read_bytes()).hexdigest(),'brief_contradictions':json.loads(intent.read_text())['context']['brief']['contradictions']})
(OUT/'mechanical_runs.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print(json.dumps(rows,indent=2))
