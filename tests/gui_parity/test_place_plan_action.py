#!/usr/bin/env python3
"""The `place_plan` plan action, through the REAL executor path.

Needs KiCad's bundled python (pcbnew + wx); it re-execs into it automatically,
so plain `python3 tests/gui_parity/test_place_plan_action.py` is the way to
run it.

Two things are worth testing and one is not. Worth testing: that a placement
step VALIDATES like every other plan step, and that executing it moves the
same footprints to the same poses the CLI would -- because the whole reason
the executor calls `plan_resolve.resolve` directly, rather than driving a tab,
is that a second implementation is what CLI/GUI parity keeps losing to. Not
worth testing here: the wx event loop, which `replay_plan_vs_run.py` already
exercises for the routing actions.

So this drives the engine exactly as `PlanExecutor._run_place_plan` does --
`build_pcb_data_from_board` off a live pcbnew board, `resolve`, then
`SetPosition`/`SetOrientationDegrees` -- and compares against the CLI's own
output board for the same plan. A divergence here is a real parity break.
"""
import json
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(REPO, 'tests', 'gui_parity'))

try:
    import headless_plan  # noqa: F401
except Exception:
    sys.path.insert(0, os.path.join(REPO, 'py_router'))

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


def have_kicad():
    try:
        import pcbnew  # noqa: F401
        import wx      # noqa: F401
        return True
    except Exception:
        return False


def reexec():
    """Re-exec into KiCad's bundled python, the way the sibling gates do."""
    cands = [
        '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/'
        'Versions/Current/bin/python3',
        r'C:\Program Files\KiCad\10.0\bin\python.exe',
        r'C:\Program Files\KiCad\9.0\bin\python.exe',
        r'C:\Program Files\KiCad\8.0\bin\python.exe',
        '/usr/bin/python3',
    ]
    for c in cands:
        if os.path.exists(c) and os.path.abspath(c) != os.path.abspath(
                sys.executable):
            argv = [c, os.path.abspath(__file__)] + sys.argv[1:]
            if os.name == 'nt':
                # os.execv goes through the CRT on Windows, which re-splits the
                # argument vector on spaces -- "C:\Program Files\KiCad\10.0\
                # bin\python.exe" arrives torn in two and the run dies with a
                # bogus "can't open file ...\Files\KiCad\...". subprocess
                # quotes it correctly. (test_gui_engine_parity.py:112 same.)
                sys.exit(subprocess.run(argv).returncode)
            os.execv(c, argv)


if not have_kicad():
    reexec()
    print("SKIP: no python with pcbnew + wx (checked the KiCad bundles)")
    sys.exit(0)

for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer'),
          os.path.join(REPO, 'kicad_routing_plugin')):
    if p not in sys.path:
        sys.path.insert(0, p)

import pcbnew
import ai_plan
from kicad_parser import build_pcb_data_from_board, mm_to_iu, parse_kicad_pcb
from placement.plan_ops import parse_placement_plan
from placement.plan_resolve import resolve

BOARD = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
PLAN = {"schema": 1, "steps": [
    {"action": "place_at", "ref": "U1", "at": [60.0, 40.0], "within": 6.0},
    {"action": "place_at", "ref": "U2", "at": [90.0, 40.0], "within": 6.0},
    {"action": "place_pack", "refs": ["C1", "C2", "C3"],
     "zone": [40.0, 34.0, 80.0, 46.0], "policy": "rows", "within": 8.0},
    # A forced PARK. The board is a strip spanning y 25.4..55.88, so a part
    # told to sit at y=200 with a 1 mm budget has no legal pose. Without this
    # the parks comparison below is `[] == []`, which passes on a GUI arm that
    # cannot park at all -- exactly the class of parity break it exists to
    # catch.
    {"action": "place_at", "ref": "D1", "at": [200.0, 200.0], "within": 1.0},
]}

# --------------------------------------------------------------------------
# It is a first-class plan action
# --------------------------------------------------------------------------
check("place_plan is a known plan action",
      "place_plan" in ai_plan.KNOWN_ACTIONS, str(ai_plan.KNOWN_ACTIONS))
steps, errs = ai_plan.parse_plan_result(json.dumps(
    {"steps": [{"action": "place_plan", "plan": PLAN}]}))
check("a placement step survives plan validation",
      steps is not None and steps[0]["action"] == "place_plan", str(errs))
bad, errs2 = ai_plan.parse_plan_result(json.dumps(
    {"steps": [{"action": "place_plan"}]}))
check("a placement step with no plan is refused, naming what is missing",
      bad is None and any('without a plan' in e for e in errs2), str(errs2))
check("the executor has a handler for it",
      hasattr(ai_plan.PlanExecutor, '_run_place_plan'))

# --------------------------------------------------------------------------
# PARITY: the live-board path must land the same poses as the CLI
# --------------------------------------------------------------------------
wd = tempfile.mkdtemp()
plan_path = os.path.join(wd, 'plan.json')
with open(plan_path, 'w', encoding='utf-8') as f:
    json.dump(PLAN, f)

# --- CLI arm ---
cli_out = os.path.join(wd, 'cli.kicad_pcb')
r = subprocess.run(
    [sys.executable, '-X', 'utf8', os.path.join('py_placer', 'place_plan.py'),
     BOARD, plan_path, '-o', cli_out, '--clearance', '0.25',
     '--board-edge-clearance', '0.55', '--grid-step', '0.1'],
    capture_output=True, text=True, cwd=REPO, timeout=1800,
    env=dict(os.environ, PYTHONIOENCODING='utf-8'))
check("the CLI arm ran", os.path.isfile(cli_out),
      (r.stdout[-400:] + r.stderr[-400:]))
cli_pose = {ref: (round(f.x, 4), round(f.y, 4),
                  round((f.rotation or 0.0) % 360.0, 4))
            for ref, f in parse_kicad_pcb(cli_out).footprints.items()}

# --- GUI arm: exactly what PlanExecutor._run_place_plan does ---
board = pcbnew.LoadBoard(BOARD)
pcb_data = build_pcb_data_from_board(board)
ops, errors = parse_placement_plan(PLAN)
assert ops is not None, errors
res = resolve(pcb_data, board.GetFileName(), ops, clearance=0.25,
              board_edge_clearance=0.55, grid_step=0.1)
for p in res.placements:
    fp = board.FindFootprintByReference(p['reference'])
    if fp is None:
        continue
    fp.SetOrientationDegrees(p['new_rotation'])
    fp.SetPosition(pcbnew.VECTOR2I(mm_to_iu(p['new_x']), mm_to_iu(p['new_y'])))
gui_pose = {}
for fp in board.GetFootprints():
    gui_pose[fp.GetReference()] = (
        round(pcbnew.ToMM(fp.GetPosition().x), 4),
        round(pcbnew.ToMM(fp.GetPosition().y), 4),
        round(fp.GetOrientationDegrees() % 360.0, 4))

# Compare the ARMS, not a magic number. This asserted `>= 5`, which was
# calibrated to a bug: the resolver excluded every unlocked part from its own
# obstacle set, so these ops seated on top of whatever was already there.
# splitflap_driver is a PLACED board, so some of them park now -- correctly.
# A count baked in here just re-freezes whatever the engine currently does;
# what this gate exists to prove is that both fronts do the SAME thing.
check("the GUI arm moved parts at all (else parity is vacuous)",
      len(res.placements) > 0, f"{len(res.placements)} placement(s)")

moved = [p['reference'] for p in res.placements]
diffs = []
for ref in moved:
    a, b = cli_pose.get(ref), gui_pose.get(ref)
    if a is None or b is None:
        diffs.append((ref, a, b))
        continue
    if (abs(a[0] - b[0]) > 1e-3 or abs(a[1] - b[1]) > 1e-3
            or abs(((a[2] - b[2]) + 180.0) % 360.0 - 180.0) > 1e-3):
        diffs.append((ref, a, b))
check("every pose matches the CLI's, to a micron", not diffs,
      f"{len(diffs)} divergence(s): {diffs[:4]}")

# The parks must match too: a GUI arm that seated a part the CLI parked would
# be a parity break that pose-comparison alone cannot see.
cli_json = os.path.join(wd, 'cli.json')
subprocess.run(
    [sys.executable, '-X', 'utf8', os.path.join('py_placer', 'place_plan.py'),
     BOARD, plan_path, '--dry-run', '--json', cli_json, '--clearance', '0.25',
     '--board-edge-clearance', '0.55', '--grid-step', '0.1'],
    capture_output=True, text=True, cwd=REPO, timeout=1800,
    env=dict(os.environ, PYTHONIOENCODING='utf-8'))
if os.path.isfile(cli_json):
    with open(cli_json, encoding='utf-8') as f:
        cli_rep = json.load(f)
    cli_parks = sorted(p['ref'] for p in cli_rep['parks'])
    gui_parks = sorted(p.ref for p in res.parks)
    check("both arms SEAT the same number of parts",
          len(cli_rep['seats']) == len(res.placements),
          f"CLI {len(cli_rep['seats'])} vs GUI {len(res.placements)}")
    check("the parks comparison is not vacuous (something actually parked)",
          bool(cli_parks), f"CLI parked {cli_parks}")
    check("the two arms park the same refs", cli_parks == gui_parks,
          f"CLI {cli_parks} vs GUI {gui_parks}")
    check("and both give the same reason, so the park report survives too",
          [p['reason'] for p in sorted(cli_rep['parks'],
                                       key=lambda p: p['ref'])]
          == [p.reason for p in sorted(res.parks, key=lambda p: p.ref)],
          f"CLI {[p['reason'] for p in cli_rep['parks']][:2]} vs GUI "
          f"{[p.reason for p in res.parks][:2]}")
else:
    check("the CLI dry-run report was written", False, "no cli.json")

# --------------------------------------------------------------------------
# DEFAULTS PARITY: the case a plan that states no clearance actually hits
#
# Both arms above were handed --clearance/--board-edge-clearance explicitly,
# which is precisely the configuration in which a GUI arm that hardcodes
# 0.25/0.55 still agrees. The CLI resolves its floors from the BOARD
# (list_nets.board_floor_knobs), so the fronts can only diverge when the plan
# is SILENT -- the common case. Run that.
#
# The fixture must be staged with a project whose floor is NOT 0.25/0.55.
# splitflap_driver has no sibling .kicad_pro and board_floor_knobs falls back
# to exactly those two constants, so running this on the bare board compares
# 0.25 against 0.25 and passes with the bug fully present. Measured: it did.
# --------------------------------------------------------------------------
STAGED_CLR = 0.15
staged = os.path.join(wd, 'staged.kicad_pcb')
pcbnew.SaveBoard(staged, pcbnew.LoadBoard(BOARD))    # authors the .kicad_pro
staged_pro = os.path.splitext(staged)[0] + '.kicad_pro'
with open(staged_pro, encoding='utf-8') as f:
    pro = json.load(f)
for cls in pro.setdefault('net_settings', {}).setdefault('classes', [{}]):
    cls['clearance'] = STAGED_CLR
with open(staged_pro, 'w', encoding='utf-8') as f:
    json.dump(pro, f, indent=2)

from list_nets import board_floor_knobs
_clr, _edge, _ = board_floor_knobs(staged, clearance=None,
                                   board_edge_clearance=None)
check("the defaults fixture actually carries a non-default floor "
      "(else this whole section is vacuous)",
      abs(_clr - 0.25) > 1e-9, f"board_floor_knobs -> clearance {_clr}, "
                               f"edge {_edge}; wanted clearance != 0.25")

cli_def = os.path.join(wd, 'cli_default.kicad_pcb')
subprocess.run(
    [sys.executable, '-X', 'utf8', os.path.join('py_placer', 'place_plan.py'),
     staged, plan_path, '-o', cli_def],
    capture_output=True, text=True, cwd=REPO, timeout=1800,
    env=dict(os.environ, PYTHONIOENCODING='utf-8'))
cli_dpose = {ref: (round(f.x, 4), round(f.y, 4),
                   round((f.rotation or 0.0) % 360.0, 4))
             for ref, f in parse_kicad_pcb(cli_def).footprints.items()}

board2 = pcbnew.LoadBoard(staged)
ops2, _ = parse_placement_plan(PLAN)


class _Log:
    def __init__(self):
        self.lines = []

    def __call__(self, m):
        self.lines.append(m)


# Drive the REAL executor method, unbound, with only what it reads. Copying
# its body into the test is how a defaults gate ends up testing the copy.
_prev_get = pcbnew.GetBoard
pcbnew.GetBoard = lambda: board2
try:
    ex = ai_plan.PlanExecutor.__new__(ai_plan.PlanExecutor)
    ex.log = _Log()
    res2 = ai_plan.PlanExecutor._run_place_plan(
        ex, {"action": "place_plan", "plan": PLAN})
finally:
    pcbnew.GetBoard = _prev_get

gui_dpose = {}
for fp in board2.GetFootprints():
    gui_dpose[fp.GetReference()] = (
        round(pcbnew.ToMM(fp.GetPosition().x), 4),
        round(pcbnew.ToMM(fp.GetPosition().y), 4),
        round(fp.GetOrientationDegrees() % 360.0, 4))

ddiffs = [(r, cli_dpose.get(r), gui_dpose.get(r)) for r in moved
          if cli_dpose.get(r) is None or gui_dpose.get(r) is None
          or abs(cli_dpose[r][0] - gui_dpose[r][0]) > 1e-3
          or abs(cli_dpose[r][1] - gui_dpose[r][1]) > 1e-3]
check("with NO clearance stated, both arms still agree "
      "(both read the board's floor)", not ddiffs,
      f"{len(ddiffs)} divergence(s): {ddiffs[:4]}")

# --------------------------------------------------------------------------
# The converter carries it, so a recorded chain replays
# --------------------------------------------------------------------------
sys.path.insert(0, os.path.join(REPO, 'tests', 'stress'))
import manifest_to_plan as m2p

step = m2p.parse_command(['python3', 'py_placer/place_plan.py',
                          'a.kicad_pcb', 'plan.json', '-o', 'b.kicad_pcb'])
check("a recorded place_plan command converts to the action",
      step and step.get('action') == 'place_plan'
      and step.get('plan_path') == 'plan.json', str(step))
check("and it keeps the board chain intact for the pruner",
      step and step.get('_files') == ['a.kicad_pcb', 'b.kicad_pcb'],
      str(step and step.get('_files')))
refused = m2p.parse_command(['python3', 'py_placer/place_plan.py',
                             'a.kicad_pcb', '-o', 'b.kicad_pcb'])
check("a place_plan with no plan file is refused, not silently mapped",
      refused and '_refused' in refused, str(refused))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
