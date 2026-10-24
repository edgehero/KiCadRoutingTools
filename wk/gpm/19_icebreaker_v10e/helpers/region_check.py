"""Count parts placed in an outline region their nets cannot reach (icebreaker_v10e).

Why this helper exists (TOOL_GAPS.md #1): the board's outline is four
electrically separate regions -- the main board (x < 80), the snap-off PMOD
board (x 82-103, y 37.2-57.8, joined only by two 1.5 mm tabs) and two frame
strips (y < 35.2 / y > 59.8 at x > 82) cut off by mouse-bite drill lines that
leave no copper channel at the board's 0.25 mm hole clearance.  No repo tool
(place_simple, check_floorplan, check_assembly, board_score before routing)
says a part sits in a region its nets cannot reach, so this counts it.

Usage: python3 -X utf8 helpers/region_check.py GROUPS.json BOARD [BOARD ...]
Each group's intended region: 'breakaway' -> breakaway,
everything else -> main (the pass-5 assignment; pass 1 had ext_top -> top
strip and ext_bot -> bottom strip).
"""
import json
import sys

sys.path.insert(0, "py_router")
from kicad_parser import parse_kicad_pcb  # noqa: E402

REGION_OF_GROUP = {"breakaway": "brk"}


def region(x, y):
    if x < 80.5:
        return "main"
    if x > 81.5:
        if y < 36.2:
            return "top"
        if y > 58.8:
            return "bot"
        return "brk"
    return "tab"


def main(argv):
    groups = json.load(open(argv[1]))["groups"]
    want = {}
    for g in groups:
        for r in g["refs"]:
            want[r] = REGION_OF_GROUP.get(g["name"], "main")
    for path in argv[2:]:
        pcb = parse_kicad_pcb(path)
        bad = [f"{r}:{region(pcb.footprints[r].x, pcb.footprints[r].y)}"
               for r, reg in sorted(want.items())
               if region(pcb.footprints[r].x, pcb.footprints[r].y) != reg]
        print(f"{path}: {len(bad)} misplaced {' '.join(bad)}")


if __name__ == "__main__":
    main(sys.argv)
