#!/usr/bin/env python3
"""Lattices: pitch, mirror, and an origin SOLVED against the real outline.

These three are what the floorplan intent schema cannot express, and
therefore what forced run 19's arrangement to be written as arithmetic:

  * pitch/rows/columns -- no numeric repeat construct exists in the intent
    schema, so 34 switches would be 34 hand-written zones, at which point
    the file IS the placement;
  * mirror -- `arrange.py:28` carried the axis as a transcribed constant
    (`MIRROR_X = 17.599913 + 239.1983`, the sum of the board's own x bounds);
  * the solved origin -- `arrange.py`'s per-column stagger
    {34.0, 28.5, 25.5, 30.0, 39.5} was PROBED against the outline's arcs
    (arrange.py:85-103). It is a measurement of that board, and a zone rect
    can only be authored.

The fixture is a NOTCHED board, because on a rectangle every column solves
to the same origin and a broken probe would still look right. Here column 1
sits in the notch and must start 10mm lower than its neighbours, and the
mirrored half's column 1 does NOT -- so the test also pins that the probe
runs per line and per side rather than once for the board.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)
        sys.path.insert(0, os.path.join(p, 'py_router'))
        sys.path.insert(0, os.path.join(p, 'py_tools'))
        sys.path.insert(0, os.path.join(p, 'py_placer'))

from kicad_parser import parse_kicad_pcb
from placement.plan_ops import parse_placement_plan
from placement.plan_resolve import resolve

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


# --------------------------------------------------------------------------
# fixture: 0..100 x 0..60 with a notch cut out of the top edge over x 28..42,
# where the board starts at y = 10 instead of y = 0.
# --------------------------------------------------------------------------
NETS = ['', 'COL0', 'COL1', 'COL2', 'R_COL0', 'R_COL1', 'R_COL2',
        'ROW0', 'ROW1']

OUTLINE = ('\t(gr_poly\n\t\t(pts (xy 0 0) (xy 28 0) (xy 28 10) (xy 42 10) '
           '(xy 42 0) (xy 100 0) (xy 100 60) (xy 0 60))\n'
           '\t\t(layer "Edge.Cuts")\n\t\t(uuid "e1")\n\t)\n')


def _part(ref, x, y, nets, cy=2.0):
    body = ''
    for i, net in enumerate(nets):
        nid = NETS.index(net) if net in NETS else 0
        body += (f'\t\t(pad "{i + 1}" smd rect\n\t\t\t(at {i * 0.5} 0)\n'
                 f'\t\t\t(size 0.4 0.4)\n\t\t\t(layers "F.Cu")\n'
                 f'\t\t\t(net {nid} "{net}")\n\t\t\t(uuid "p{i}-{ref}")\n\t\t)\n')
    return f'''\t(footprint "test:P{ref}"
\t\t(layer "F.Cu")
\t\t(uuid "fp-{ref}")
\t\t(at {x} {y})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 0)
\t\t)
\t\t(fp_rect
\t\t\t(start {-cy} {-cy})
\t\t\t(end {cy} {cy})
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "cy-{ref}")
\t\t)
{body}\t)
'''


def board():
    fps = ''
    n = 0
    for half, pre in (('L', 'COL'), ('R', 'R_COL')):
        for col in range(3):
            for row in range(2):
                n += 1
                fps += _part(f'SW{n}', 50, 30, [f'{pre}{col}', f'ROW{row}'])
    nets = ''.join(f'\t(net {i} "{s}")\n' for i, s in enumerate(NETS))
    body = ('(kicad_pcb\n\t(version 20241229)\n' + nets + OUTLINE + fps + ')\n')
    fd, path = tempfile.mkstemp(suffix='.kicad_pcb')
    with os.fdopen(fd, 'w') as f:
        f.write(body)
    return parse_kicad_pcb(path), path


INDEX = {"action": "place_index", "name": "sw", "select": r"^SW\d+$",
         "fields": {"col": {"pattern": r"^(R_)?COL(\d)$", "group": 2,
                            "as": "int"},
                    "half": {"pattern": r"^(R_)?COL(\d)$", "group": 1,
                             "as": "str", "map": {"R_": "R", "": "L"}},
                    "row": {"pattern": r"^ROW(\d)$", "group": 1,
                            "as": "int"}}}


def run(steps):
    pcb, path = board()
    ops, errors = parse_placement_plan({'schema': 1, 'steps': steps})
    assert ops is not None, errors
    try:
        return resolve(pcb, path, ops, clearance=0.2,
                       board_edge_clearance=0.5, grid_step=0.1)
    finally:
        os.unlink(path)


ARRAY = {"action": "place_array", "refs": "index:sw", "pitch": [15.0, 10.0],
         "origin": {"x": 16.0,
                    "y": {"solve": "outline_probe", "from": 1.0, "step": 0.5,
                          "limit": 60}},
         "index_x": "col", "index_y": "row",
         "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
         "order": ["half", "col", "row"], "rot": 0, "within": 1.0}

r = run([INDEX, ARRAY])
seats = {s.ref: s for s in r.seats}
check("every lattice member seats", len(r.seats) == 12 and not r.parks,
      str(r.summary()) + ' ' + str([(p.ref, p.reason) for p in r.parks]))

# The index assigns col/half/row; SW1..SW6 are the left half.
targets = {ref: s.target for ref, s in seats.items()}


def t(col, row, half):
    for ref, s in seats.items():
        m = r.indexes['sw']['members'][ref]
        if m['col'] == col and m['row'] == row and m['half'] == half:
            return s.target
    return None


# x: origin 16 + pitch 15 * col, mirrored about the board's own midpoint
# (bounds 0..100, so mirror(x) = 100 - x). No column lands ON the axis --
# both halves would then want the same seat, which is a real collision and
# not what this test is about.
check("pitch places the columns", t(0, 0, 'L')[0] == 16.0
      and t(1, 0, 'L')[0] == 31.0 and t(2, 0, 'L')[0] == 46.0,
      f"{[t(c, 0, 'L')[0] for c in range(3)]}")
check("mirror reflects about the board's midpoint, read not typed",
      t(0, 0, 'R')[0] == 84.0 and t(1, 0, 'R')[0] == 69.0
      and t(2, 0, 'R')[0] == 54.0,
      f"{[t(c, 0, 'R')[0] for c in range(3)]}")

# y: solved per line. A 4x4 courtyard at 0.5mm edge clearance needs its top
# at y >= 0.5, so a column clear of the notch starts at 2.5; column 1 sits in
# the notch (board starts at y=10 there) and must start at 12.5.
check("the solved origin clears the outline where it is open",
      t(0, 0, 'L')[1] == 2.5 and t(2, 0, 'L')[1] == 2.5,
      f"col0 {t(0, 0, 'L')[1]}, col2 {t(2, 0, 'L')[1]}")
check("the solved origin STAGGERS around the notch",
      t(1, 0, 'L')[1] == 12.5,
      f"col1 solved to {t(1, 0, 'L')[1]}, expected 12.5")
check("the probe runs per line, not once for the board",
      t(1, 0, 'L')[1] != t(0, 0, 'L')[1],
      "" if t(1, 0, 'L')[1] != t(0, 0, 'L')[1]
      else "every column solved to the same origin")
check("the probe runs per SIDE: the mirrored column 1 is clear of the notch",
      t(1, 0, 'R')[1] == 2.5,
      f"mirrored col1 solved to {t(1, 0, 'R')[1]}, expected 2.5")
check("row pitch stacks within a line",
      t(0, 1, 'L')[1] == t(0, 0, 'L')[1] + 10.0,
      f"{t(0, 0, 'L')[1]} -> {t(0, 1, 'L')[1]}")

# `also` keeps a satellite rect legal too: a 6x2 strip 8.5mm below each member
# pushes column 0 down, because the strip would otherwise hang off the bottom
# is not the case here -- it is the TOP edge that binds, so `also` above the
# member is what moves it.
r2 = run([INDEX, dict(ARRAY, origin={
    "x": 20.0,
    "y": {"solve": "outline_probe", "from": 1.0, "step": 0.5, "limit": 60,
          "also": [{"offset": [0.0, -4.0], "extent": [6.0, 2.0]}]}})])
s2 = {s.ref: s for s in r2.seats}


def t2(col, row, half):
    for ref, s in s2.items():
        m = r2.indexes['sw']['members'][ref]
        if m['col'] == col and m['row'] == row and m['half'] == half:
            return s.target
    return None


check("`also` constrains the solve too",
      t2(0, 0, 'L')[1] == 5.5,
      f"with a strip 4mm above, col0 solved to {t2(0, 0, 'L')[1]}, "
      f"expected 5.5")

# --------------------------------------------------------------------------
# a member the index cannot position is PARKED, not defaulted to zero
# --------------------------------------------------------------------------
r3 = run([{"action": "place_index", "name": "sw", "select": r"^SW\d+$",
           "fields": {"col": {"pattern": r"^(R_)?COL(\d)$", "group": 2,
                              "as": "int"},
                      "half": {"pattern": r"^(R_)?COL(\d)$", "group": 1,
                               "as": "str", "map": {"R_": "R", "": "L"}},
                      "row": {"pattern": r"^NOSUCH(\d)$", "group": 1,
                              "as": "int"}}},
          ARRAY])
check("a member with no index value for the lattice is parked",
      not r3.seats and len(r3.parks) == 12, str(r3.summary()))
check("the park names the missing field",
      r3.parks and "'row'" in r3.parks[0].reason,
      r3.parks[0].reason if r3.parks else '')

# --------------------------------------------------------------------------
# place_slots: named pockets, grouped and ordered, mirrored per member
# --------------------------------------------------------------------------
r4 = run([INDEX,
          {"action": "place_slots", "refs": "index:sw",
           "slots": [[10.0, 40.0], [25.0, 45.0]],
           "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
           "where": {"row": {"eq": 0}, "col": {"lt": 2}},
           "group_by": ["half"], "order": ["col"], "rot": 0, "within": 2.0}])
s4 = {s.ref: s for s in r4.seats}
check("place_slots seats one member per slot per group",
      len(r4.seats) == 4 and not r4.parks,
      str(r4.summary()) + str([(p.ref, p.reason) for p in r4.parks]))
left = sorted(s.target for ref, s in s4.items()
              if r4.indexes['sw']['members'][ref]['half'] == 'L')
right = sorted(s.target for ref, s in s4.items()
               if r4.indexes['sw']['members'][ref]['half'] == 'R')
check("the ordered group takes the slots in order",
      left == [(10.0, 40.0), (25.0, 45.0)], str(left))
check("the mirrored group takes the mirrored slots",
      right == [(75.0, 45.0), (90.0, 40.0)], str(right))

# More members than slots is reported, not silently truncated.
r5 = run([INDEX,
          {"action": "place_slots", "refs": "index:sw",
           "slots": [[10.0, 40.0]],
           "where": {"row": {"eq": 0}, "half": {"eq": "L"}},
           "order": ["col"], "within": 2.0}])
check("more members than slots parks the remainder with the count",
      len(r5.parks) == 2 and 'only 1 slot' in r5.parks[0].reason,
      str([(p.ref, p.reason) for p in r5.parks]))

# --------------------------------------------------------------------------
# place_at can mirror its own coordinate, so the other half of a symmetric
# board needs no hand arithmetic (arrange.py:189-202 carries thirteen
# hand-mirrored constants).
# --------------------------------------------------------------------------
r6 = run([{"action": "place_at", "ref": "SW1", "at": [16.0, 30.0],
           "within": 1.0},
          {"action": "place_at", "ref": "SW7", "at": [16.0, 30.0],
           "within": 1.0, "mirror": {"axis": "board:xmid"}}])
s6 = {s.ref: s.target for s in r6.seats}
check("place_at --mirror reflects the stated coordinate",
      s6.get('SW1') == (16.0, 30.0) and s6.get('SW7') == (84.0, 30.0),
      str(s6))

# --------------------------------------------------------------------------
# determinism (#457)
# --------------------------------------------------------------------------
check("the same lattice resolves identically twice",
      run([INDEX, ARRAY]).placements == run([INDEX, ARRAY]).placements)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
