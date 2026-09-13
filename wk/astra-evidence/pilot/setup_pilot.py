"""Prepare matched partial-placement pilot inputs, no hidden truth exposed.

Four oscillator-subassembly footprints are piled. All remaining footprints
are explicitly fixed at the existing test fixture's poses. This is a partial
placement task, not blind reconstruction or whole-board design.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
if (HERE/'arms').exists() or (HERE/'preparation').exists():
    raise SystemExit('Run a copy of this script in a fresh sibling area; pilot artifacts are preserved')
(HERE/'preparation').mkdir(parents=True)
for p in ('py_router','py_placer','tests/stress'):
    sys.path.insert(0,str(ROOT/p))
from kicad_parser import parse_kicad_pcb
from placement.writer import write_placed_output
from placement.seeder import stamp_locked
from strip_copper_only import strip
source=ROOT/'kicad_files/esp_prog.kicad_pcb'
prepared=HERE/'preparation/partial_subject.kicad_pcb'
pcb=parse_kicad_pcb(str(source))
free=['U1','Y1','C2','C4']
placements=[dict(reference=r,new_x=128.0,new_y=99.5,new_rotation=0.0) for r in free]
write_placed_output(str(source),str(prepared),placements)
text,n=strip(prepared.read_text(encoding='utf-8'))
prepared.write_text(text,encoding='utf-8')
fixed={r:[f.x,f.y,f.rotation,f.layer] for r,f in pcb.footprints.items() if r not in free}
stamp_locked(str(prepared),list(fixed))
brief={'schema':1,'kind':'design-brief','units':'mm',
 'product':{'form_factor':'partial-placement research fixture'},
 'proximity':[{'ref':'Y1','near':'U1','max_mm':8.0,'basis':'pad_edge',
  'pads':{'Y1':['1','2'],'U1':['9','10']},'requirement':'PILOT-OSC',
  'why':'Controlled pilot limit, not a verified product electrical specification.'}]}
protocol='''Partial-placement research task. Arrange U1, Y1, C2 and C4 from their
stacked starting position into a legal, sensible oscillator subassembly. Keep
every other footprint at its input x/y/rotation/layer and retain its lock.
Preserve outline, netlist, pads, layers and electrical rules. Remain on the
existing front side. Respect board.design-brief.json; its 8mm named oscillator
pad-distance ceiling is a controlled study requirement, not a production spec.
Use connectivity and component/pad context to choose poses; don't consult the
original board or other arm. Use exact geometry checks plus visual inspection.
Write final.kicad_pcb and a concise RETURN.md with decisions, all mutations,
validation results, unsatisfied/unmeasured requirements and elapsed time.
You have a bounded 8-minute research trial and at most 20 board-mutating tool
invocations; stop at that boundary and report incomplete work honestly. Read-only
measurements are allowed. Do not route, change production code, waive checks,
change design constraints, use --force, unlock fixed parts or ask the user to
approve intermediate work. Work on your arm's copies. Each CLI can run at most
60 seconds. Do not spawn agents. You may read repository tooling, help and skill
files as specified for your arm, but never kicad_files, tests/fixtures, another
arm, preparation, truth, or earlier research artifacts. The only board input is
the board.kicad_pcb inside your arm directory. This is a partial placement pilot,
not a blind whole-board or fabrication-readiness benchmark.
'''
meta={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'prepared_sha256':hashlib.sha256(prepared.read_bytes()).hexdigest(),'free_refs':free,
 'fixed_poses':fixed,'stripped_copper_forms':n,'model':'inherited Astra via collaboration tools',
 'trial_count_per_arm':1,'wall_clock_budget_seconds':480,'mutating_invocation_limit':20}
for arm in ('current_skill','concise_contract'):
    d=HERE/'arms'/arm
    d.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(prepared,d/'board.kicad_pcb')
    (d/'board.design-brief.json').write_text(json.dumps(brief,indent=2),encoding='utf-8')
    (d/'FIXED_POSES.json').write_text(json.dumps(fixed,indent=2),encoding='utf-8')
    (d/'TASK.md').write_text(protocol,encoding='utf-8')
    if arm=='concise_contract':
        (d/'CONTRACT.md').write_text('''Use the repository as a tool library. Choose
the arrangement yourself; use py_tools/board_context.py to inspect component
roles, pad functions and partners. py_placer/place_pose.py accepts set/rotate
verbs, including several parts in a single arrangement; --near enables bounded
legalization. Read its --help. Apply exact poses with that sanctioned tool.
Inspect renders using py_tools/render_placement.py and image viewing. Check
py_router/check_drc.py and py_tools/check_assembly.py, supplying the original
arm board as assembly baseline. Use py_tools/check_floorplan.py to compile and
grade the explicit design brief. Carry the brief to each candidate. Measurements
propose/validate changes; choose your own sequence. An inherited defect is not
proof that every candidate is invalid, and a no-worse tool verdict is not proof
that the final board is clean. Keep failed proposals as logged experiments;
never promote one that breaks a declared requirement. Report coverage gaps.
Do not load the three plan-pcb-* SKILL.md files or their drivers in this arm.
''',encoding='utf-8')
(HERE/'protocol.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta,indent=2))
