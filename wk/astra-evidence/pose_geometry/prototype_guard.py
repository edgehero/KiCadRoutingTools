"""Isolated proof of concept: guard the destination before promotion and ledger final bytes.
This monkeypatch is experimental only and does not alter production source.
"""
from pathlib import Path
import contextlib, hashlib, json, sys, time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
for p in ('','py_placer','py_router','py_tools','tests/stress'): sys.path.insert(0,str(ROOT/p))
from placement import pose_ops, provenance as pv
from placement.portfolio import copy_siblings
from placement.writer import write_placed_output
from kicad_parser import parse_kicad_pcb
from stage_unaided import stage
from provenance_audit import audit, poses
OUT=HERE/('guard-'+time.strftime('%Y%m%d-%H%M%S')); OUT.mkdir()
real_promote=pose_ops._promote
def checked_promote(staged, out_path, summary=None):
    root=pv.regime_for(out_path)
    if root is None: return real_promote(staged,out_path,summary)
    if not summary or not summary.get('input'):
        raise pv.UnaidedViolation('promotion into a regime requires explicit source context')
    src=summary['input']
    before=parse_kicad_pcb(src); after=parse_kicad_pcb(staged)
    # Ledger what the FINAL candidate actually contains, including snaps and locks.
    pp=[{'reference':r,'new_x':f.x,'new_y':f.y,'new_rotation':f.rotation}
        for r,f in after.footprints.items() if r in before.footprints]
    pv.record_write(src,out_path,pp,pending=True)
    try:
        real_promote(staged,out_path,summary)
    except BaseException:
        # Public cancellation API is missing: production needs one.
        pv._PENDING.pop(str(Path(out_path).resolve()),None)
        raise
    pv.commit_write(out_path)
pose_ops._promote=checked_promote
results={'kind':'experimental runtime monkeypatch; no production changes','cases':[]}
for name,declared,dry,lock,bad in [('accepted',True,False,False,False),
    ('accepted_lock',True,False,True,False),('dry_run',True,True,False,False),
    ('refused_geometry',True,False,False,True),('undeclared',False,False,False,False)]:
    work=OUT/name; work.mkdir(); board=work/'board.kicad_pcb'; dest=work/'out.kicad_pcb'
    stage(str(ROOT/'kicad_files/esp_prog.kicad_pcb'),str(board))
    op={'kind':'set','ref':'R1','x':500 if bad else 136.4,'y':98.8,'rot':270}
    ctx=pv.declare_lever('place_pose.py',['prototype',name]) if declared else contextlib.nullcontext()
    try:
        with ctx:
            s=pose_ops.apply_poses(str(board),str(dest),[op],dry_run=dry,lock_refs=['R1'] if lock else [])
        row={'case':name,'error':None,'summary':s}
    except Exception as e:
        row={'case':name,'error':type(e).__name__,'message':str(e)}
    rows=pv.read_ledger(str(work))
    row.update({'output_exists':dest.exists(),'ledger_rows':len(rows),'rows':rows})
    if dest.exists():
        row['audit']=audit(str(work),str(dest))
        row['sha_matches_ledger']=rows[-1]['board_sha256']==hashlib.sha256(dest.read_bytes()).hexdigest()
        row['pose']=poses(str(dest))['R1']
    results['cases'].append(row)
(OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
for c in results['cases']: print(c['case'],c['error'],c['output_exists'],c['ledger_rows'],c.get('audit',[None])[0],c.get('sha_matches_ledger'))
print('RESULTS',OUT/'results.json')
