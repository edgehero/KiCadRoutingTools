"""Real-board action-granularity probes; not a model-quality benchmark.

Run from repository root with KiCad Python. Every subprocess has a timeout,
and raw outputs, exact argv, elapsed times, input hashes and JSON summaries
are retained. Inputs are never edited. Multi-part swaps are capability probes,
not proposed production layouts or evidence of improved routability.
"""
import hashlib
import argparse
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output', type=Path, required=True, help='Fresh output directory')
opts = ap.parse_args()
OUT = opts.output.resolve()
if OUT.exists():
    raise SystemExit('Use a fresh output directory; no existing evidence is overwritten')
OUT.mkdir(parents=True)
os.chdir(ROOT)
for directory in ('py_router', 'py_placer', 'py_tools', 'tests/stress'):
    sys.path.insert(0, str(ROOT / directory))
from kicad_parser import parse_kicad_pcb
from copy_board import copy_board
from placement.pose_ops import grade, resolve_knobs
from strip_copper_only import strip

records = []

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(label, args, timeout=90):
    argv = [sys.executable, '-X', 'utf8'] + list(map(str, args))
    started = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout,
                           env=dict(os.environ, KRT_NO_BANNER='1', PYTHONHASHSEED='0'))
        stdout, stderr, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or b''
        stderr = e.stderr or b''
        if isinstance(stdout, bytes): stdout = stdout.decode('utf-8', 'replace')
        if isinstance(stderr, bytes): stderr = stderr.decode('utf-8', 'replace')
        code = 'TIMEOUT'
    (OUT / (label + '.stdout.txt')).write_text(stdout, encoding='utf-8')
    (OUT / (label + '.stderr.txt')).write_text(stderr, encoding='utf-8')
    summaries = []
    for line in stdout.splitlines():
        if line.startswith('JSON_SUMMARY:'):
            try: summaries.append(json.loads(line.split(':', 1)[1]))
            except ValueError: pass
    item = dict(label=label, argv=argv, exit=code,
                seconds=round(time.monotonic() - started, 3), summaries=summaries)
    records.append(item)
    (OUT / 'commands.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(label, code, item['seconds'], flush=True)
    return item

def pose_args(ref, part):
    return ['set', ref, str(part.x), str(part.y), '--rot', str(part.rotation)]

results = {'purpose': __doc__, 'commit': subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], text=True).strip(), 'python': sys.version,
    'boards': []}
for name, selected in [('esp_prog', ('R3','R4')), ('flat_hierarchy', ('R1','R2')),
                       ('tigard', None)]:
    src = ROOT / 'kicad_files' / (name + '.kicad_pcb')
    base = OUT / (name + '_base.kicad_pcb')
    copy_board(str(src), str(base))
    text, removed = strip(base.read_text(encoding='utf-8'))
    base.write_text(text, encoding='utf-8')
    pcb = parse_kicad_pcb(str(base))
    if selected is None:
        parts = [(r, f) for r, f in sorted(pcb.footprints.items())
                 if r.startswith('R') and len(f.pads) == 2]
        pairs = [(a, b) for a, b in itertools.combinations(parts, 2)
                 if a[1].footprint_name == b[1].footprint_name
                 and a[1].layer == b[1].layer
                 and (a[1].x-b[1].x)**2+(a[1].y-b[1].y)**2 > 4]
        selected = (pairs[0][0][0], pairs[0][1][0])
    a, b = selected
    pa, pb = pcb.footprints[a], pcb.footprints[b]
    entry = dict(board=name, source_sha256=sha(src), prepared_sha256=sha(base),
                 stripped_copper_forms=removed, refs=[a,b],
                 source_poses={r:[p.x,p.y,p.rotation] for r,p in [(a,pa),(b,pb)]})
    for label, verbs in [('single_a', pose_args(a,pb)), ('single_b', pose_args(b,pa)),
                         ('atomic', pose_args(a,pb)+pose_args(b,pa))]:
        target = OUT / (name + '_' + label + '.kicad_pcb')
        item = run(name+'_'+label, ['py_placer/place_pose.py',base,target]+verbs)
        entry[label] = {'exit':item['exit'], 'summaries':item['summaries'],
                        'output_exists':target.exists()}
        if target.exists():
            entry[label]['sha256'] = sha(target)
    results['boards'].append(entry)
    (OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

# A model-chosen local repair motivated by the rendered R4/CON1 collision.
base = OUT/'esp_prog_base.kicad_pcb'
repair = OUT/'esp_repair.kicad_pcb'
item=run('esp_local_repair',['py_placer/place_pose.py',base,repair,
                           'set','R4','140.6','97.4','--rot','180'])
results['local_proposal']={'exit':item['exit'],'summaries':item['summaries']}
snapped=OUT/'esp_snapped.kicad_pcb'
item=run('esp_snap',['py_placer/place_pose.py',base,snapped,
                    'set','R4','--near','140.6','97.4','--rot','180'])
results['snapped_proposal']={'exit':item['exit'],'summaries':item['summaries']}
for label, board in [('base',base),('snapped',snapped)]:
    if not board.exists(): continue
    run('esp_'+label+'_assembly',['py_tools/check_assembly.py',board,'--baseline',base])
    run('esp_'+label+'_drc',['py_router/check_drc.py',board,'--clearance-margin','0'])
    run('esp_'+label+'_render',['py_tools/render_placement.py',board,'--quiet',
        '--review-sheet',OUT/('esp_'+label+'_review.png'),
        '--json-out',OUT/('esp_'+label+'_render.json'),
        '-o',OUT/('esp_'+label+'.png')])

# Actual route writer versus copy_board sibling-preservation positive control.
brief = base.with_suffix('.design-brief.json')
shutil.copyfile(ROOT/'tests/fixtures/711/esp_prog.design-brief.json',brief)
copy_target = OUT/'brief_copy.kicad_pcb'
copy_board(str(base),str(copy_target))
pcb=parse_kicad_pcb(str(base))
candidates=[]
for net in pcb.nets.values():
    pads=pcb.pads_by_net.get(net.id,[]) if hasattr(net,'id') else []
    if len(pads)==2:
        d=(pads[0].global_x-pads[1].global_x)**2+(pads[0].global_y-pads[1].global_y)**2
        candidates.append((d,net.name))
if not candidates:
    for net_id,pads in pcb.pads_by_net.items():
        if len(pads)==2:
            candidates.append(((pads[0].global_x-pads[1].global_x)**2+
                (pads[0].global_y-pads[1].global_y)**2,pcb.nets[net_id].name))
net=sorted(candidates)[0][1]
routed=OUT/'brief_routed.kicad_pcb'
route=run('brief_route',['py_router/route.py',base,'--output',routed,'--nets',net,
    '--max-iterations','5000','--max-probe-iterations','1000',
    '--fab-tier','standard','--escalation','off'],timeout=120)
results['brief_writer']={'input_brief_sha256':sha(brief),'net':net,
    'copy_brief_exists':copy_target.with_suffix('.design-brief.json').exists(),
    'route_exit':route['exit'],'route_board_exists':routed.exists(),
    'route_brief_exists':routed.with_suffix('.design-brief.json').exists(),
    'route_summaries':route['summaries']}
(OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('RESULTS',OUT/'results.json',flush=True)
