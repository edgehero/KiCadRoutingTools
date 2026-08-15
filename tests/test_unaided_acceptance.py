#!/usr/bin/env python3
"""The unaided loop, end to end, on a board that is committed to this repo.

    stage a pile  ->  run an AI-authored plan  ->  is the result BUILDABLE?

This is the falsification point for "an AI can place a board without human hand
placement". Everything it needs is tracked: the board, its project, and the
plan. Nothing here reads the original placement.

WHY IT REPLACES `test_place_plan_urchin.py`, which measured a better thing and
measured it nowhere: that test needs `wk/run19/urchin/base.kicad_pcb`, `wk/` is
gitignored, and the board is untracked. On every clone but one it prints SKIP
and exits 0 -- and `run_all.py:125` maps exit 0 to PASS. The branch's headline
acceptance evidence has therefore never run in CI. So the first thing this file
does is FAIL, loudly, if its fixture is missing.

TWO THINGS THIS GATE DOES NOT CLAIM, both measured rather than assumed:

  * **It does not prove the placement ROUTES.** `CLAUDE.md` is right that the
    router is the only judge. A buildable board can still be unroutable; this
    catches the stacking / off-board / pad-copper class, which is what actually
    shipped broken.
  * **It is GREEN today, before the place_edge and park-census work.**
    `flat_hierarchy` is roomy (utilisation 0.36) and the plan seats everything
    with `place_at`/`place_pack`, so it does not reproduce the defects those
    rows fix -- verified by running `place_edge` on this same pile, which seats
    both connectors correctly on-board. Saying so here matters: a gate that
    passes for reasons unrelated to the work it guards is the exact failure
    this branch's audit found nine times. Per-defect tests live with their own
    rows; this file's job is that the LOOP closes and keeps closing.

The off-outline baseline is the other lesson. `HOLE1-6` and `J1` hang off the
outline **in the source board too** (identical courtyard amounts, measured), so
asserting `off_outline == []` would fail on correct work. Baseline against the
source; assert only that PAD COPPER is clean, which is the defect that converts
1:1 into unrouted nets.

WHAT THIS GATE IS SENSITIVE TO, established by fault injection rather than
hope:

  * making `seeder.pose_ok` accept every pose -> **3 checks go red**
    (`check_assembly` exit 4, `overlap_area 315.89`, 3 pad-conflict pairs). So
    it does detect a real legality regression.
  * disabling ONLY the containment conjunct of `pose_ok` -> **stays green**.
    Every target in this plan is comfortably interior, so nothing moves. That
    is a genuine blind spot of THIS fixture+plan pair, not of the checks: a
    containment regression needs a part whose target is near an edge, which is
    what the `place_edge` row's own test provides. Recorded here so the next
    person does not read a green run as "containment is covered".
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'kicad_files', 'flat_hierarchy.kicad_pcb')
PLAN = os.path.join(REPO, 'tests', 'fixtures', 'unaided',
                    'flat_hierarchy_plan.json')
PY = [sys.executable, '-X', 'utf8']
ENV = dict(os.environ, PYTHONIOENCODING='utf-8')

# The staged board carries these at their source pose because their position is
# a mechanical fact a real new board would already know. Everything else piles.
EXEMPT = {'HOLE1', 'HOLE2', 'HOLE3', 'HOLE4', 'HOLE5', 'HOLE6', 'J1'}
FREE = 57

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


def run(args, **kw):
    return subprocess.run(PY + args, capture_output=True, text=True,
                          cwd=REPO, env=ENV, timeout=1800, **kw)


# --------------------------------------------------------------------------
# The fixture is TRACKED. Missing means FAIL, never skip.
# --------------------------------------------------------------------------
missing = [p for p in (BOARD, PLAN, os.path.splitext(BOARD)[0] + '.kicad_pro')
           if not os.path.isfile(p)]
if missing:
    print("FAIL the acceptance fixture is missing: "
          + ', '.join(os.path.relpath(m, REPO) for m in missing))
    print("  These are committed files. A skip here is how the test this one "
          "replaces passed everywhere while asserting nothing.")
    print("\n0 passed, 1 failed")
    sys.exit(1)

from kicad_parser import parse_kicad_pcb

work_root = tempfile.mkdtemp()
work = os.path.join(work_root, 'work')
truth = os.path.join(work_root, 'truth')      # MUST be a sibling of work

# --------------------------------------------------------------------------
# 1. stage the pile
# --------------------------------------------------------------------------
r = run([os.path.join('tests', 'stress', 'stage_unaided.py'), BOARD, work,
         truth])
staged = os.path.join(work, 'board.kicad_pcb')
check("the board stages into an unaided pile", os.path.isfile(staged),
      (r.stdout[-300:] + r.stderr[-300:]))
check("the staged board keeps its .kicad_pro (the DRC floor, #441)",
      os.path.isfile(os.path.join(work, 'board.kicad_pro')))

pile = parse_kicad_pcb(staged)
seen = {}
for ref, fp in pile.footprints.items():
    seen.setdefault((round(fp.x, 2), round(fp.y, 2)), []).append(ref)
biggest = max(seen.values(), key=len)
check("it really is a pile -- the free parts share one coordinate",
      len(biggest) == FREE, f"{len(biggest)} stacked, expected {FREE}")
check("and only the mechanical refs are carried",
      set(pile.footprints) - set(biggest) == EXEMPT,
      str(sorted(set(pile.footprints) - set(biggest))))
check("every piled part is at rotation 0 (a staged angle is a leaked decision)",
      all((pile.footprints[r].rotation or 0.0) % 360 == 0 for r in biggest),
      str([r for r in biggest
           if (pile.footprints[r].rotation or 0.0) % 360 != 0][:5]))

# --------------------------------------------------------------------------
# 2. run the committed plan -- nothing reads the original placement
# --------------------------------------------------------------------------
placed = os.path.join(work, 'placed.kicad_pcb')
report = os.path.join(work, 'report.json')
r = run([os.path.join('py_placer', 'place_plan.py'), staged, PLAN,
         '-o', placed, '--json', report, '--deadline', '480'])
check("the plan runs", os.path.isfile(placed),
      (r.stdout[-500:] + r.stderr[-300:]))

with open(report, encoding='utf-8') as f:
    rep = json.load(f)
check("it seats every free part", len(rep['seats']) == FREE,
      f"seated {len(rep['seats'])}, parked {len(rep['parks'])}: "
      f"{[(p['ref'], p['reason']) for p in rep['parks']][:4]}")
check("nothing is parked", not rep['parks'],
      str([(p['ref'], p['reason']) for p in rep['parks']][:4]))
# A park is a measurement, not a silence -- if one ever appears it must say why.
check("and any park that does appear carries a reason and a target",
      all(p.get('reason') and p.get('target') is not None
          for p in rep['parks']), str(rep['parks'][:2]))
check("the run reports it held the mechanical parts as obstacles",
      any('held there as obstacles' in n for n in rep.get('notes', [])),
      str(rep.get('notes', [])[:2]))

# --------------------------------------------------------------------------
# 3. THE VERDICT: is it buildable?
# --------------------------------------------------------------------------
r = run([os.path.join('py_tools', 'check_assembly.py'), placed])
check("check_assembly says BUILDABLE (exit 0)", r.returncode == 0,
      f"exit {r.returncode}: " + '\n'.join(
          l for l in r.stdout.splitlines()
          if 'VERDICT' in l or 'blocking' in l or 'COINCIDENT' in l)[:400])
check("and it reports no coincident origins",
      'COINCIDENT ORIGINS' not in r.stdout,
      "parts stacked at one point -- the defect da2917f9 fixed")

# --------------------------------------------------------------------------
# 4. pad copper on the board, baselined against the SOURCE
# --------------------------------------------------------------------------
def render(board, out_json):
    run([os.path.join('py_tools', 'render_placement.py'), board,
         '--json-out', out_json, '-o', out_json + '.png'])
    with open(out_json, encoding='utf-8') as f:
        return json.load(f)


got = render(placed, os.path.join(work, 'render.json'))
src = render(BOARD, os.path.join(work, 'render_src.json'))

check("no part has pad copper off the outline",
      got['checklist']['a_off_outline']['pad_copper'] == [],
      str(got['checklist']['a_off_outline']['pad_copper']))
check("and the source board is clean too, so that check means something",
      src['checklist']['a_off_outline']['pad_copper'] == [],
      "if the SOURCE had off-board pad copper this assertion would be vacuous")

# Courtyard overhang is a FIXTURE property here: HOLE1-6 and J1 hang off the
# outline in the source board by the same amounts. Baseline, do not assert [].
src_court = {ref for ref, _amt in src['checklist']['a_off_outline']['courtyard']}
got_court = {ref for ref, _amt in got['checklist']['a_off_outline']['courtyard']}
check("no part the PLAN placed hangs off the outline",
      got_court <= src_court,
      f"new off-outline refs: {sorted(got_court - src_court)}")

m = got['metrics']
check("no body overlap", m['overlap_area'] == 0.0, str(m['overlap_area']))
check("no pad conflicts", m['pad_conflict_pairs'] == 0,
      str(m['pad_conflict_pairs']))
check("no hole conflicts", got['checklist']['c_hole_conflicts'] == [],
      str(got['checklist']['c_hole_conflicts']))

shutil.rmtree(work_root, ignore_errors=True)
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
