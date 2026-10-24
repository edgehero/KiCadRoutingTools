"""Ask the declared-pose check and the edge gate about each straddling drill (verifier probe, M07)."""
import os, sys, json, math, collections
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
from kicad_parser import parse_kicad_pcb, pad_drill_capsule
from placement import floorplan
from placement.groups import parse_sources
from placement.edge_seat import seat_state, _near
from placement.seeder import _fixed_pose_check, _holes_outside
from placement.legality import footprint_at_pose
from list_nets import board_floor_knobs
board, intent_path = sys.argv[1:3]
intent = floorplan.load_intent(intent_path)
pcb = parse_kicad_pcb(board)
blocks, _ = floorplan.resolve_blocks(intent, pcb, parse_sources('auto'))
fixed, _ = floorplan.declared_moves(intent, {}, pcb)
clearance, edge, _ = board_floor_knobs(board)
st = seat_state(pcb, board, intent, blocks, clearance, edge, set(fixed), estimate_courtyards=True)
gate = st.edge_gate
print('edge gate', type(gate).__name__, 'margin', getattr(gate, 'margin', None),
      'cutouts modelled', len(getattr(gate, 'cutouts', None) or getattr(gate, '_cutouts', None) or []))
fpd = {f['ref']: f for f in json.load(open(intent_path))['fixed_poses']}
tally = collections.Counter()
for r in sorted(fpd):
    if not r.startswith('REF**~'):
        continue
    pose = (fpd[r]['x'], fpd[r]['y'], fpd[r].get('rot', 0.0))
    part = st.parts[r]
    part.ensure_rotation(pose[2])
    rect = part.grade_rect(*pose)
    rect_out = gate.rect_outside_amount(rect)
    n, out = _holes_outside(st, gate, r, *pose)
    pool = {o: (q.x, q.y, q.rot) for o, q in st.parts.items() if o != r}
    how, reasons, _c = _fixed_pose_check(st, r, pose, _near(st, r, pose, pool))
    tally[(how, round(rect_out, 3) > 0, out)] += 1
    if r in ('REF**~10', 'REF**~11', 'REF**~9', 'REF**~14'):
        print(r, pose, 'rect', [round(v, 2) for v in rect], 'rect_outside', round(rect_out, 4), 'holes_outside', (n, out), '->', how, reasons[:2])
print('(how, courtyard leaves outline, holes outside): count', dict(tally))
