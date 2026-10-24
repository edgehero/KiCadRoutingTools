"""Apply the route step's own ship-time via-protection rule (#962) to a board AFTER
fill_for_delivery has rewritten it in the KiCad 10 file format.

Why: route.py stamps `(capping yes) (filling yes)` on a via it put under solder, but only
when the board's FILE FORMAT can carry the tokens. This board is KiCad 6 format (20211014)
through the whole chain, so route.py recorded its 4 via-in-pad sites as `unstampable`
and check_drc accepted them as `undeclarable-via-in-paste`. fill_for_delivery then saves
the board through pcbnew as version 20260206, the sites become declarable, and check_drc /
board_score grade the same 4 vias as blocking `via-in-paste`. This helper calls the repo's
own fab_notes.ship_via_protection_file on the filled board, with the run's INPUT board's
via snapshot (the pile: no vias), i.e. exactly the decision route.py would have made.
Copper and zone fills are not touched; only the 4 (via ...) blocks gain the tokens.
usage: python3 helpers/stamp_type_vii.py <filled_board.kicad_pcb> <run input board>"""
import sys
sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb
import fab_notes
board, inp = sys.argv[1], sys.argv[2]
snap = fab_notes.via_snapshot(parse_kicad_pcb(inp).vias, parse_kicad_pcb(inp))
rec = fab_notes.ship_via_protection_file(board, snap, context='stamp_type_vii helper')
print('RECORD', rec)
