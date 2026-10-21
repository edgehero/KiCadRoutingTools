"""Debug probe: why does place_simple's edge seat find 'no room' for a part?
Builds place_simple's own state and evaluates edge_seat's conjuncts for REF
on EDGE at the seat coordinate, along the edge.
usage: seat_probe.py BOARD GROUPS INTENT REF"""
import json, sys, os, argparse
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
for p in ('py_placer', 'py_router', 'py_tools'):
    sys.path.insert(0, os.path.join(WT, p))
import place_simple as ps
from kicad_parser import parse_kicad_pcb
from placement import floorplan, edge_seat
from placement.groups import parse_sources
from placement.grouping import load_groups

board, groups, intent_p, ref = sys.argv[1:5]
ns = argparse.Namespace(congestion_weight=5.0, track_pitch=0.33, rail_weight=0.3,
    ground_weight=0.02, pad_weight=2.0, crossing_weight=2.0, claim_weight=1.0,
    decap_weight=2.0, group_weight=5.0, halo_coef=0.25, halo_weight=10.0,
    claim_limit_weight=10.0, decap_limit_weight=0.0, near_weight=2.0,
    apart_weight=5.0, edge_weight=2.0)
doc = load_groups(groups); base = json.load(open(intent_p)); intent = floorplan.load_intent(intent_p)
pcb = parse_kicad_pcb(board)
blocks, _ = floorplan.resolve_blocks(intent, pcb, parse_sources('auto'))
state, model, movable, notes = ps.build(pcb, board, doc, base, ns, intent, blocks, set())
print('unseated:', model.edge_unseated)
c = [e for e in intent.edge_connectors if e['ref'] == ref][0]
edge = c['edge']
from placement.body import board_bodies
bodies = board_bodies(pcb, board)
probe = edge_seat._Probe(state, pcb, board, bodies, floorplan.outline_state(pcb, board))
rots, face = edge_seat._turns(state, pcb, bodies, c, edge)
probe.faces[ref] = face
print('turns', rots, 'face', face, 'bounds', pcb.board_info.board_bounds,
      'edge clr', state.board_edge_clearance, 'margin', state.edge_gate.margin)
part = state.parts[ref]
axis = 0 if edge in ('north', 'south') else 1
target = float((c.get('overhang_mm') or {}).get('min', 0.0))
b = pcb.board_info.board_bounds
for rot in rots:
    part.ensure_rotation(rot)
    cr = part.rect(0.0, 0.0, rot)
    pb = edge_seat._pad_box(pcb, ref, (0.0, 0.0, rot)) or cr
    e = state.board_edge_clearance + edge_seat.COPPER_SLACK_MM
    lo = b[axis] + e - pb[axis]; hi = b[axis + 2] - e - pb[axis + 2]
    coord = edge_seat._seat_coord(probe, ref, edge, rot, axis, (lo + hi) / 2.0, target)
    print(f'rot {rot}: courtyard(local) {cr} padbox {pb} along [{lo:.3f},{hi:.3f}] coord {coord:.3f}')
    for k in range(0, 11):
        a = lo + (hi - lo) * k / 10.0
        pose = (a, coord, rot) if axis == 0 else (coord, a, rot)
        band = probe.band(ref, edge, pose)
        cc = probe.copper_clear(ref, pose)
        from placement.floorplan import _nearest_edge, drawn_body_rect, edge_seat_rect
        from placement.mating import facing_edge
        from types import SimpleNamespace
        sr, basis = edge_seat_rect(c, part.rect(*pose), lambda: drawn_body_rect(bodies.get(ref), SimpleNamespace(x=pose[0], y=pose[1], rotation=rot)))
        ne = _nearest_edge(sr, probe.bounds, state.edge_gate.margin, facing=facing_edge(face, rot) if face else None)
        from placement.seeder import _fixed_pose_check
        fpc = _fixed_pose_check(state, ref, pose, {})
        print(f'   along {a:8.3f} band {band:7.3f} copper_clear {cc} nearest {ne} fixed_pose_check {fpc[0]} {fpc[1][:2] if fpc[1] else ""}')
