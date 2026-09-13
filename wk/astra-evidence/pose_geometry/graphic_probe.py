"""Placement-scoped #962 probe using real esp_prog U2 graphic copper/paste."""
from pathlib import Path
import json, subprocess, sys, time, hashlib
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
for p in ('','py_placer','py_router','py_tools'): sys.path.insert(0,str(ROOT/p))
import pcbnew
from placement.writer import write_placed_output
from placement.portfolio import copy_siblings
from kicad_parser import parse_kicad_pcb
from placement.legality import grade_pad_legality
OUT=HERE/('graphic-'+time.strftime('%Y%m%d-%H%M%S')); OUT.mkdir()
SRC=ROOT/'kicad_files/esp_prog.kicad_pcb'
source_part=parse_kicad_pcb(str(SRC)).footprints['U2']
results={'input_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'cases':[]}
for case,x,y,rot in [('original',source_part.x,source_part.y,source_part.rotation),
                     ('west_oob',115.34,93.6,90),('west_inboard',116.70,93.6,90)]:
    dst=OUT/f'U2_{case}.kicad_pcb'
    pose_cmd=[sys.executable,'-X','utf8',str(ROOT/'py_placer/place_pose.py'),str(SRC),str(dst),
              'set','U2',str(x),str(y),'--rot',str(rot)]
    r=subprocess.run(pose_cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    (OUT/(dst.stem+'.pose.log')).write_text(r.stdout+'\nSTDERR:\n'+r.stderr,encoding='utf8')
    summary=[json.loads(l.split('JSON_SUMMARY:',1)[1]) for l in r.stdout.splitlines() if l.startswith('JSON_SUMMARY:')]
    native=pcbnew.LoadBoard(str(dst)); part=native.FindFootprintByReference('U2')
    def rect(o):
        b=o.GetBoundingBox()
        return [pcbnew.ToMM(x) for x in (b.GetLeft(),b.GetTop(),b.GetRight(),b.GetBottom())]
    row={'case':case,'pose_command':pose_cmd,'pose_exit':r.returncode,'pose_summary':summary,
        'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
        'pcbnew_pose':[pcbnew.ToMM(part.GetPosition().x),pcbnew.ToMM(part.GetPosition().y),part.GetOrientationDegrees()],
        'native_graphics':[{'layer':g.GetLayerName(),'rect':rect(g)} for g in part.GraphicalItems() if g.GetLayerName() in ('F.Cu','F.Paste','F.Mask')],
        'native_pads':[{'pad':p.GetNumber(),'rect':rect(p)} for p in part.Pads()]}
    parsed=parse_kicad_pcb(str(dst)); row['bounds']=parsed.board_info.board_bounds
    row['pad_legality']=grade_pad_legality(parsed,0.25,edge_margin=0.25,pcb_file=str(dst))
    row['commands']=[]
    for tool,extra in [('py_router/check_drc.py',['--check-pad-edge','--board-edge-clearance','0.25','--clearance-margin','0']),
                       ('py_tools/check_assembly.py',[])]:
        name=Path(tool).stem; report=dst.with_suffix('.'+name+'.json')
        cmd=[sys.executable,'-X','utf8',str(ROOT/tool),str(dst),*extra,'--json',str(report)]
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
        (OUT/(dst.stem+'.'+name+'.log')).write_text(r.stdout+'\nSTDERR:\n'+r.stderr,encoding='utf8')
        row['commands'].append({'argv':cmd,'exit':r.returncode})
        row[name]=json.loads(report.read_text(encoding='utf8')) if report.exists() else {'missing':True}
    results['cases'].append(row)
(OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print('RESULTS',OUT/'results.json')
