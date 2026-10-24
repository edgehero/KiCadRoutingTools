"""Ask the edge seat's own declared-pose check (seeder._fixed_pose_check) about DC1 at the anneal's south poses."""
import os, sys, json
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
from kicad_parser import parse_kicad_pcb
from placement import floorplan
from placement.groups import parse_sources
from placement.edge_seat import seat_state, _near
from placement.seeder import _fixed_pose_check
from list_nets import board_floor_knobs
board, intent_path = sys.argv[1], sys.argv[2]
poses = [tuple(map(float, p.split(','))) for p in sys.argv[3:]]
intent = floorplan.load_intent(intent_path)
pcb = parse_kicad_pcb(board)
blocks, _ = floorplan.resolve_blocks(intent, pcb, parse_sources('auto'))
fixed, _flips = floorplan.declared_moves(intent, {}, pcb)
clearance, edge, _ = board_floor_knobs(board)
st = seat_state(pcb, board, intent, blocks, clearance, edge, set(fixed), estimate_courtyards=True)
for r in ('DC1', 'BAT1', 'I2C2'):
    p = st.parts[r]
    print(r, 'pose', (p.x, p.y, p.rot), 'grade_rect', tuple(round(v, 2) for v in p.grade_rect()),
          'drawn_rect', tuple(round(v, 2) for v in p.drawn_rect()), 'locked', p.locked)
pool = {o: (q.x, q.y, q.rot) for o, q in st.parts.items() if o != 'DC1'}
for pose in poses:
    st.parts['DC1'].ensure_rotation(pose[2])
    how, reasons, conflicts = _fixed_pose_check(st, 'DC1', pose, _near(st, 'DC1', pose, pool))
    print('DC1 at', pose, '->', how, '| reasons:', reasons[:6], '| conflicts:', conflicts)
