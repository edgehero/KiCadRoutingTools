"""Undo fill_for_delivery's per-via protection rewrite and declare IPC-4761
Type VII on the run's vias under solder (TOOL_GAPS entry).

What happens without this: the routed board is version 20240108 (KiCad 8). Its
461 vias carry no protection token (they inherit the board setup), route.py
could not stamp Type VII on the 215 that sit in a pad or paste opening (the
format predates the tokens: `unstampable`), and check_drc accepts those as
`undeclarable-via-in-paste`. fill_for_delivery saves the board through KiCad
10's pcbnew, which writes version 20260206 AND an explicit `(capping no)
(covering (front no) (back no)) (plugging (front no) (back no)) (filling no)`
on EVERY via. The same 215 sites now read as decided "not filled, not capped",
and board_score counts 212 of them as blocking `drc_via_in_paste` -- on a board
whose copper did not change.

This helper (1) strips exactly that all-"no" block from each via, restoring the
inherit-from-board state the routed board had, then (2) runs the repo's own
ship-time pass, fab_notes.ship_via_protection_file, with the unrouted input's
via snapshot (no vias: every via under solder is the run's own), which stamps
`(capping yes) (filling yes)` where route.py would have stamped it on a KiCad 10
file. No copper, no zone fill and no other token is touched.

usage (from WT): python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/stamp_type_vii.py BOARD.kicad_pcb INPUT.kicad_pcb
"""
import re
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402
from fab_notes import via_snapshot, ship_via_protection_file  # noqa: E402

NO_BLOCK = re.compile(
    r'\n\t\t\(capping no\)'
    r'\n\t\t\(covering\n\t\t\t\(front no\)\n\t\t\t\(back no\)\n\t\t\)'
    r'\n\t\t\(plugging\n\t\t\t\(front no\)\n\t\t\t\(back no\)\n\t\t\)'
    r'\n\t\t\(filling no\)')

board, input_board = sys.argv[1], sys.argv[2]
text = open(board, encoding='utf-8').read()
n_vias = len(re.findall(r'\n\t\(via\b', text))
text, n = NO_BLOCK.subn('', text)
open(board, 'w', encoding='utf-8').write(text)
print(f"stripped the all-'no' protection block from {n} of {n_vias} via(s)")
inp = parse_kicad_pcb(input_board)
snap = via_snapshot(inp.vias, inp)
print(f"input {input_board}: {len(inp.vias)} via(s) in the snapshot")
rec = ship_via_protection_file(board, snap, context='stamp_type_vii (post fill_for_delivery)')
print({k: rec.get(k) for k in ('count', 'stamped', 'restored', 'protected', 'unstampable')} if rec else rec)
