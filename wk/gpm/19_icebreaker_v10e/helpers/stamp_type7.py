"""Declare IPC-4761 Type VII on a delivered board's via-in-pad/paste vias (icebreaker_v10e).

Why this helper exists (TOOL_GAPS.md): the routed board is KiCad 8 format
(version 20240108), so route.py's ship-time stamp (`fab_notes.
via_protection_stamps`) could not write `(capping yes) (filling yes)` and
counted the 69 vias in paste openings `unstampable` -- check_drc accepts them
there as "undeclarable in this file format".  `py_tools/fill_for_delivery.py`
saves through KiCad 10's pcbnew, which upgrades the file to 20260206; the same
69 vias then grade as 69 UNPROTECTED via-in-paste violations and the delivered
board reads blocking 69.  No repo CLI stamps an existing board.

This calls the route step's own ship-time function on the written file,
`fab_notes.ship_via_protection_file`, with the chain's ORIGINAL input board as
the snapshot (the pile: zero vias), so exactly the vias the routing chain
added under solder are stamped -- what route.py does on a board whose format
can carry the tokens.  Nothing else in the file changes (vias matched by uuid).

Usage: python3 -X utf8 helpers/stamp_type7.py BOARD.kicad_pcb INPUT_BOARD.kicad_pcb
(BOARD is edited in place.)
"""
import sys

sys.path.insert(0, "py_router")
from kicad_parser import parse_kicad_pcb  # noqa: E402
import fab_notes  # noqa: E402


def main(argv):
    board, input_board = argv[1], argv[2]
    src = parse_kicad_pcb(input_board)
    snap = fab_notes.via_snapshot(src.vias, src)
    print(f"input snapshot: {len(snap)} via(s) on {input_board}")
    record = fab_notes.ship_via_protection_file(board, snap, context="stamp_type7")
    print("RECORD:", {k: record.get(k) for k in ("count", "stamped", "protected", "unstampable",
                                                 "unprotected", "written") if k in record}
          if record else None)


if __name__ == "__main__":
    main(sys.argv)
