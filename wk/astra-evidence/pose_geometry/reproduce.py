"""Issue #960/#961 controlled reproduction; run with KiCad's Python, -X utf8.

Artifacts are isolated under this file's directory. Source boards remain untouched.
This is a tool-contract experiment, not a blind placement quality benchmark.
"""
from pathlib import Path
import dataclasses, hashlib, json, subprocess, sys, time, shutil, tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for part in ('', 'py_router', 'py_tools', 'py_placer', 'tests/stress'):
    sys.path.insert(0, str(ROOT / part))
from kicad_parser import parse_kicad_pcb
from placement import provenance as pv, pose_ops, floorplan as fp
from placement.writer import write_placed_output
from placement.portfolio import copy_siblings
from placement.legality import BoardOutlineGate, grade_pad_legality
from placement.body import board_bodies
import provenance_audit
import pcbnew, numpy

OUT = HERE / ('run-' + time.strftime('%Y%m%d-%H%M%S'))
OUT.mkdir()
results = {'environment': {'python': sys.version, 'executable': sys.executable,
                          'numpy': numpy.__version__, 'kicad': pcbnew.GetBuildVersion()},
           'commands': [], 'inputs': {}, 'provenance': {}, 'edge': []}
results['commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name, obj): (OUT / name).write_text(json.dumps(obj, indent=2, default=str), encoding='utf8')
def run(name, *args):
    cmd = [sys.executable, '-X', 'utf8', *map(str, args)]
    t = time.monotonic()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf8')
    (OUT / (name + '.log')).write_text(r.stdout + '\nSTDERR:\n' + r.stderr, encoding='utf8')
    results['commands'].append({'name': name, 'argv': cmd, 'exit': r.returncode,
                                'elapsed_s': time.monotonic()-t})
    summaries = [json.loads(l.split('JSON_SUMMARY:',1)[1]) for l in r.stdout.splitlines() if l.startswith('JSON_SUMMARY:')]
    return {'exit': r.returncode, 'summary': summaries[-1] if summaries else None}

src = ROOT / 'kicad_files/esp_prog.kicad_pcb'
results['inputs'][str(src.relative_to(ROOT))] = sha(src)
work = OUT / 'armed'
results['provenance']['stage'] = run('stage', ROOT/'tests/stress/stage_unaided.py', src, work, OUT/'truth')
staged = work / 'board.kicad_pcb'
original = parse_kicad_pcb(str(src))
p = original.footprints['R1']
pose = {'reference': 'R1', 'new_x': p.x, 'new_y': p.y, 'new_rotation': p.rotation}
dest = work / 'pose.kicad_pcb'
results['provenance']['cli'] = run('pose', ROOT/'py_placer/place_pose.py', staged, dest, 'set','R1',p.x,p.y,'--rot',p.rotation)
results['provenance']['rows_after_cli'] = pv.read_ledger(str(work))
results['provenance']['audit_after_cli'] = provenance_audit.audit(str(work), str(dest))
results['provenance']['delivered_pose'] = provenance_audit.poses(str(dest))['R1']
# Positive control: same exact desired pose, same actual baseline, registered writer.
control = work / 'registered_writer.kicad_pcb'
with pv.declare_lever('place_pose.py', ['positive-control']):
    write_placed_output(str(staged), str(control), [pose])
copy_siblings(str(staged), str(control))
results['provenance']['audit_registered_writer'] = provenance_audit.audit(str(work), str(control))
results['provenance']['rows_after_control'] = pv.read_ledger(str(work))
# Negative control: no declared lever in a direct write must refuse before creation.
refused = work/'undeclared_direct.kicad_pcb'
try:
    write_placed_output(str(staged), str(refused), [pose])
    direct = {'raised': None}
except Exception as e:
    direct = {'raised': type(e).__name__, 'message': str(e)}
direct['output_exists'] = refused.exists()
results['provenance']['undeclared_direct'] = direct
# An undeclared external stage + real promote is the exact path guard currently misses.
with tempfile.TemporaryDirectory(prefix='astra_960_control_') as td:
    temp = Path(td)/'candidate.kicad_pcb'
    write_placed_output(str(staged), str(temp), [pose])
    copy_siblings(str(staged), str(temp))
    bypass = work/'undeclared_promote.kicad_pcb'
    n = len(pv.read_ledger(str(work)))
    pose_ops._promote(str(temp), str(bypass))
    results['provenance']['undeclared_promote'] = {'output_exists': bypass.exists(),
        'rows_added': len(pv.read_ledger(str(work)))-n, 'pose': provenance_audit.poses(str(bypass))['R1']}

# #961: actual USB connector geometry translated against the real esp_prog outline.
# Its authored body is at the west edge while its copper-pad bbox is 1.6 mm inboard.
source_pcb = parse_kicad_pcb(str(src))
body, body_source = fp.drawn_body_rect(board_bodies(source_pcb, str(src)).get('USB1'), source_pcb.footprints['USB1'])
bounds = source_pcb.board_info.board_bounds
results['geometry_source'] = {'bounds': bounds, 'body_rect': body, 'body_basis': body_source}
usb = source_pcb.footprints['USB1']
# Translate west by 0/1.45/2.10: pad bbox west gap 1.60/0.15/-0.50.
for dx in (0.0, -1.45, -2.10):
    board = OUT / ('usb_dx_' + str(dx).replace('.','_') + '.kicad_pcb')
    write_placed_output(str(src), str(board), [{'reference':'USB1','new_x':usb.x+dx,'new_y':usb.y,'new_rotation':usb.rotation}])
    copy_siblings(str(src), str(board))
    pcb = parse_kicad_pcb(str(board))
    body_rect, bs = fp.drawn_body_rect(board_bodies(pcb,str(board)).get('USB1'), pcb.footprints['USB1'])
    pads = pcb.footprints['USB1'].pads
    copper_west = min(p.global_x - p.size_x/2 for p in pads if p.pad_type != 'np_thru_hole')
    results['commands'].append({'name':'board_construction', 'call':'write_placed_output',
        'input':str(src),'output':str(board),'USB1_dx_mm':dx,'sibling_copy':True})
    run('drc_dx_'+str(dx), ROOT/'py_router/check_drc.py',board,'--check-pad-edge',
        '--board-edge-clearance','0.25','--clearance-margin','0','--json',board.with_suffix('.drc.json'))
    for margin in (0.0, 0.25, 0.55):
        # Positive min separates false pass/fail from the original 0..0.65 band's permissiveness.
        for band in ({'min':0.0,'max':0.65}, {'min':0.05,'max':0.20}):
            intent = fp.intent_from_dict({'schema':fp.SCHEMA_VERSION,'kind':fp.KIND,'units':'mm',
                'edge_connectors':[{'ref':'USB1','class':'edge_receptacle','edge':'west','overhang_mm':band}]})
            grade = fp.grade(intent,pcb,str(board),board_edge_clearance=margin)
            gate = BoardOutlineGate(pcb.board_info, margin)
            # Capture the exact rect rule_edge_connector consumes, through its real context construction.
            captured = {}
            original_rule = fp.rule_edge_connector
            def capture(ctx):
                captured['part_rect'] = ctx.parts['USB1'].rect
                captured['measured_overhang'] = ctx.gate.rect_outside_amount(ctx.parts['USB1'].rect)
                captured['effective_gate_margin'] = ctx.gate.margin
                captured['direct_gate_at_requested_margin'] = gate.rect_outside_amount(ctx.parts['USB1'].rect)
                return original_rule(ctx)
            old_rules = fp.RULES
            try:
                fp.RULES = [(n,capture if n=='edge_connector' else fn) for n,fn in old_rules]
                grade = fp.grade(intent,pcb,str(board),board_edge_clearance=margin)
            finally: fp.RULES = old_rules
            ev = [dataclasses.asdict(v) for v in grade.violations if v.rule=='edge_connector']
            results['edge'].append({'board':board.name,'board_sha256':sha(board),'dx':dx,'margin':margin,'band':band,
                'copper_west_gap_mm':copper_west-bounds[0], 'body_rect':body_rect,'body_basis':bs,
                'body_signed_west_overhang_mm':bounds[0]-body_rect[0], **captured,
                'edge_violations':ev,'edge_seating':grade.edge_seating,
                'pad_legality':grade_pad_legality(pcb,0.25,edge_margin=margin,pcb_file=str(board))})
dump('results.json',results)
print('RESULTS:', OUT/'results.json')
print(json.dumps({'provenance_cli':results['provenance']['cli'],
                  'audit_cli':results['provenance']['audit_after_cli'],
                  'audit_control':results['provenance']['audit_registered_writer'],
                  'direct':results['provenance']['undeclared_direct'],
                  'promote':results['provenance']['undeclared_promote']},indent=2))
