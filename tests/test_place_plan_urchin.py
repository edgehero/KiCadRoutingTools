#!/usr/bin/env python3
"""The acceptance test: run 19's arrangement, said instead of computed.

Run 19's seeder could not produce a key field -- 7 switches "no legal pose
inside zone", 3 "no legal pose anywhere" -- so a teammate wrote
`wk/run19/urchin/arrange.py`: 221 lines with PITCH = 17.0, X0 = 46.0,
MIRROR_X = 17.599913 + 239.1983 and THUMB_SLOTS = [(78.0,79.5),(95.5,82.0)]
baked in, plus a per-column stagger probed against the outline. It placed 80
of 85 and left SW17, SW34, D16, D17 and D33 at their pile poses. SW17 and
SW34 then cost the run a whole further routing cycle and a SECOND hand script
(`apply_c2_seats.py`) to seat.

This runs the same arrangement as a placement plan and requires it to do at
least as well, with nothing hand-computed: the mirror axis is read from the
board, the per-column origin is solved against the outline, and the two
scripts' arithmetic is gone.

The plan should also do BETTER on exactly one axis, and it is worth naming
because it is the vocabulary earning its keep rather than luck: a plan can say
`"rot": 0`. arrange.py could not -- `seeder.py:26-32` records that the intent
schema cannot express a rotation, and arrange.py's own "diode strip: below the
switch, rot 90" is a COMMENT (arrange.py:30). So its thumb switches searched
from their pile angles (SW17 at r330), where no legal pose exists.

That causal claim was ABLATED rather than asserted: removing `"rot": 0` from
the place_slots op alone -- changing nothing else -- parks SW17 and SW34 and
takes the run from 82 seated to 79, i.e. WORSE than the hand script's 80. The
mechanism is visible in `_try_place`, which searches `[part.rot, +90, +180,
+270]`: from SW17's pile rot 330 that is {330, 60, 150, 240} and from SW34's
15 it is {15, 105, 195, 285}. Neither set contains 0.

SKIPS when the board is absent: `wk/` is gitignored, so a fresh clone has no
run-19 assets and this test must not fail for that.
"""
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(REPO, 'wk', 'run19', 'urchin', 'base.kicad_pcb')

# What arrange.py achieved, from the recorded run of the version that is
# STILL IN THE TREE -- arranged3, not arranged. The two agree (80 placed, the
# same five refs), but `arranged.kicad_pcb.arrange.json` came from an earlier
# arrange.py whose thumb slots were (97.0,80.5)/(159.8,80.5); citing it would
# be comparing against a version nobody can re-run.
HAND_SEATED = 80
HAND_PARKED = {'SW17', 'SW34', 'D16', 'D17', 'D33'}

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not os.path.isfile(BOARD):
    # EXIT 77, not 0. `wk/` is gitignored and this board is untracked, so on
    # every clone but the one that produced it this file asserts nothing --
    # and `run_all.py` used to map exit 0 to PASS, so it reported a green
    # headline acceptance result on machines where it had never run. 77 is the
    # runner's SKIP code: counted in its own bucket, never as a pass.
    # tests/test_unaided_acceptance.py is the TRACKED end-to-end gate; this
    # one stays as the richer measurement for anyone who has the board.
    print("SKIP: wk/run19/urchin/base.kicad_pcb absent (wk/ is gitignored, "
          "and this board is untracked -- see tests/test_unaided_acceptance.py "
          "for the tracked equivalent)")
    sys.exit(77)

# The whole arrangement. Compare with arrange.py: no pitch multiplication, no
# mirror arithmetic, no probed constants, no ordering loop.
PLAN = {"schema": 1, "steps": [
    {"action": "place_index", "name": "diode", "select": r"^D\d+$",
     "fields": {"row": {"pattern": r"^(R_)?ROW(\d)$", "group": 2,
                        "as": "int"}}},
    {"action": "place_index", "name": "switch", "select": r"^SW\d+$",
     "fields": {"col": {"pattern": r"^(R_)?COL(\d)$", "group": 2,
                        "as": "int"},
                "half": {"pattern": r"^(R_)?COL(\d)$", "group": 1,
                         "as": "str", "map": {"R_": "R", "": "L"}}},
     "partner": {"index": "diode", "pattern": r"^Net-\(",
                 "inherit": ["row"], "as": "partner"}},

    {"action": "place_at", "ref": "U1", "at": [28.0, 60.0], "within": 5.0},
    {"action": "place_at", "ref": "U2", "at": [28.0, 60.0], "within": 5.0,
     "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "Display1", "at": [30.0, 61.5],
     "within": 8.0},
    {"action": "place_at", "ref": "Display2", "at": [30.0, 61.5],
     "within": 8.0, "mirror": {"axis": "board:xmid"}},

    # The 5x3 matrix per half. The per-column origin is SOLVED against the
    # real outline, with the diode strip that follows kept legal too -- that
    # is arrange.py's probe (arrange.py:85-103), stated.
    {"action": "place_array", "refs": "index:switch", "pitch": [17.0, 17.0],
     "origin": {"x": 46.0,
                "y": {"solve": "outline_probe", "from": 24.0, "step": 0.5,
                      "limit": 48,
                      "also": [{"offset": [0.0, 8.5], "extent": [6.8, 2.0]}]}},
     "index_x": "col", "index_y": "row",
     "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
     "where": {"row": {"lt": 3}},
     "order": ["half", "col", "row"], "rot": 0, "within": 2.5},

    # Row 3 is not a row, it is the thumb class, and its pockets are named
    # coordinates. Per half the higher column takes the inner slot.
    {"action": "place_slots", "refs": "index:switch",
     "slots": [[78.0, 79.5], [95.5, 82.0]],
     "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
     "where": {"row": {"eq": 3}},
     "group_by": ["half"], "order": ["col"], "rot": 0, "within": 9.0},

    # Each diode follows its own switch's RESOLVED pose.
    {"action": "place_relative", "refs": "index:diode", "of": "index:switch",
     "pair_by": "partner", "offset": [0.0, 8.5], "within": 6.0},

    {"action": "place_at", "ref": "SW_POWER0", "at": [31.0, 99.0],
     "within": 8.0},
    {"action": "place_at", "ref": "SW_POWER1", "at": [31.0, 99.0],
     "within": 8.0, "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "RSW0", "at": [33.0, 93.0], "within": 8.0},
    {"action": "place_at", "ref": "RSW1", "at": [33.0, 93.0], "within": 8.0,
     "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "Bat+0", "at": [39.0, 92.0], "within": 8.0},
    {"action": "place_at", "ref": "Bat+1", "at": [39.0, 92.0], "within": 8.0,
     "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "BatGND0", "at": [39.0, 95.0],
     "within": 8.0},
    {"action": "place_at", "ref": "BatGND1", "at": [39.0, 95.0],
     "within": 8.0, "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "H1", "at": [28.0, 38.0], "within": 8.0},
    {"action": "place_at", "ref": "H3", "at": [28.0, 38.0], "within": 8.0,
     "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "H2", "at": [28.0, 84.0], "within": 8.0},
    {"action": "place_at", "ref": "H4", "at": [28.0, 84.0], "within": 8.0,
     "mirror": {"axis": "board:xmid"}},
    {"action": "place_at", "ref": "Ref**", "at": [44.0, 90.0], "within": 8.0},
]}


def run(workdir):
    plan_path = os.path.join(workdir, 'plan.json')
    out_path = os.path.join(workdir, 'seeded.kicad_pcb')
    rep_path = os.path.join(workdir, 'report.json')
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(PLAN, f)
    r = subprocess.run(
        [sys.executable, '-X', 'utf8', os.path.join('py_placer', 'place_plan.py'),
         BOARD, plan_path, '-o', out_path, '--json', rep_path,
         '--clearance', '0.2', '--board-edge-clearance', '0.5',
         '--grid-step', '1.0'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=REPO, timeout=1800,
        env=dict(os.environ, PYTHONHASHSEED='0', PYTHONIOENCODING='utf-8'))
    if not os.path.isfile(rep_path):
        print(r.stdout[-3000:])
        print(r.stderr[-3000:])
        raise SystemExit("place_plan produced no report")
    with open(rep_path, encoding='utf-8') as f:
        return r, json.load(f), out_path


with tempfile.TemporaryDirectory() as wd:
    proc, rep, out_board = run(wd)

    seats = {s['ref']: s for s in rep['seats']}
    parks = {p['ref']: p for p in rep['parks']}

    check("the plan runs to completion", rep['complete'] is True,
          proc.stderr[-500:])
    check("a board is written", os.path.isfile(out_board))
    check("the run exits 4 when anything parked, 0 otherwise",
          proc.returncode == (4 if parks else 0),
          f"rc={proc.returncode}, parked={sorted(parks)}")

    # --- the bar: at least as good as 221 lines of arithmetic ---------------
    check(f"seats at least as many as the hand script ({HAND_SEATED})",
          rep['seated'] >= HAND_SEATED,
          f"{rep['seated']} seated, {rep['parked']} parked "
          f"({sorted(parks)})")
    # The other half of the bar, which was defined and then never asserted:
    # every part the hand script could not seat must be seated here or named
    # as a park. A ref in neither list has gone missing.
    accounted = set(seats) | set(parks)
    check("every part the hand script parked is accounted for",
          HAND_PARKED <= accounted,
          f"unaccounted: {sorted(HAND_PARKED - accounted)}")
    check("no park is unexplained: each names a reason",
          all(p['reason'] for p in parks.values()),
          str({r: p['reason'] for r, p in parks.items() if not p['reason']}))

    # --- the two the hand script could not seat -----------------------------
    for ref in ('SW17', 'SW34'):
        check(f"{ref} seats -- arrange.py could not, and it cost run 19 a "
              f"cycle", ref in seats,
              f"pose {seats[ref]['pose']}" if ref in seats
              else parks.get(ref, {}).get('reason', 'absent from the report'))
    check("both thumbs land ON their declared pocket, not near it",
          all(seats.get(r, {}).get('moved_mm', 9e9) < 0.01
              for r in ('SW17', 'SW34')),
          str({r: seats.get(r, {}).get('moved_mm') for r in ('SW17', 'SW34')}))
    check("the thumbs are seated at the rotation the plan asked for",
          all(abs(seats.get(r, {}).get('pose', [0, 0, 99])[2]) < 1e-6
              for r in ('SW17', 'SW34')),
          str({r: seats.get(r, {}).get('pose') for r in ('SW17', 'SW34')}))

    # --- the index did the electrical join ----------------------------------
    sw = rep['indexes']['switch']
    check("the index found all 34 switches", len(sw) == 34, str(len(sw)))
    check("every switch paired with its diode through the private net",
          sum(1 for m in sw.values() if m.get('partner')) == 34,
          str(sum(1 for m in sw.values() if m.get('partner'))))
    check("both halves were identified from the net prefix",
          {m.get('half') for m in sw.values()} == {'L', 'R'},
          str({m.get('half') for m in sw.values()}))

    # --- the mirror was read, not typed -------------------------------------
    # arrange.py:28 carried MIRROR_X = 17.599913 + 239.1983 by hand. The plan
    # names `board:xmid`, so U1 and U2's seats must be symmetric about it.
    if 'U1' in seats and 'U2' in seats:
        s = seats['U1']['pose'][0] + seats['U2']['pose'][0]
        check("the mirrored pair is symmetric about the board's own axis",
              abs(s - 256.798213) < 0.01, f"x sum {s}")

    # --- the origin was solved, and it is a stagger --------------------------
    # arrange.py probed {34.0, 28.5, 25.5, 30.0, 39.5} for its five columns.
    by_col = {}
    for ref, m in sw.items():
        if ref in seats and m.get('half') == 'L' and m.get('row', 9) < 3:
            by_col.setdefault(m['col'], []).append(
                (m['row'], seats[ref]['target'][1]))
    origins = {c: min(y - 17.0 * r for r, y in v)
               for c, v in sorted(by_col.items())}
    check("every column solved an origin", len(origins) == 5, str(origins))
    check("the solved origins STAGGER -- they are a measurement of the "
          "outline, not a constant", len(set(round(v, 3) for v
                                             in origins.values())) > 1,
          str(origins))

    # --- parks are measurements ---------------------------------------------
    check("every park carries a reason and a target",
          all(p['reason'] and p['target'] for p in parks.values()),
          str(parks))
    check("no park is a silent drop: every named ref is seated or parked",
          len(seats) + len(parks) == rep['seated'] + rep['parked'])

    # --- determinism (#457) --------------------------------------------------
    with tempfile.TemporaryDirectory() as wd2:
        _, rep2, _ = run(wd2)
    same = ([s['pose'] for s in rep['seats']]
            == [s['pose'] for s in rep2['seats']])
    check("the same plan resolves identically twice", same,
          "" if same else "poses differed between runs")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
