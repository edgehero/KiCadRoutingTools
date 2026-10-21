# TOOL_GAPS -- gp14 board 05 (interf_u)

Ranked by what each cost this run. All commands run from the worktree root
(`~/Documents/git/krt-gp14`) with the venv python first on PATH. Every
input a repro needs is copied under `wk/gp14/05_interf_u/repro/`. No helper
scripts were written (`helpers/` does not exist): every step used a repo tool.

---

## 1. The seed judge cannot see a DONE-blocking floorplan error, and `place_simple` names such a seed first

**Tools:** `py_placer/place_simple.py --round` (its `judge.json`), `py_tools/quick_score.py`, and the
skill text `.claude/skills/plan-pcb-placement/SKILL.md` §3.6 steps 2 and 6 ("keep the best by blocking, then
vias, copper_mm, segments").

**What they claimed.** Round 1: `place_simple` named seed 8 first in `r1/judge.json` (cheapest
`final.cost` 5329.5, `illegal: []`), and its fast route scored best (`quick_score` blocking 1, 107 vias).
By the skill's rule s8 was the round's (and the run's) best placement.

**What was true.** s8 breaks the intent's error-graded `decaps.max_pin_distance_mm` (34.08 mm) on three
U9 VCC pins: `check_floorplan` reports `U9 pin D11 39.01 mm`, `G12 41.19 mm`, `L10 37.23 mm` from the nearest
47 uF cap. Those are `floorplan` errors, which `board_score` counts in `blocking`, so s8 could never reach DONE
whatever the router did. `place_simple`'s own report said it (`decap_broken: 3`, "3 decap limit(s) broken")
but the seed was still legal and judged first, and `quick_score` (route tally only) has no floorplan term, so
the skill's "keep the best" picked a placement that cannot be DONE. Cost: a whole review round (r2) spent
mainly on adding error-graded decap claims (`intent_r2.json`), and the claims I had to invent then became
error rows of their own (r2's best seed broke my 10 mm claim; r3 loosened it to 20 mm and the chosen r3 s0
still needed a post-placement `place_pose` nudge of C1/R2 to meet it).

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent.json   # 3 x [ERROR] decap_pin_distance
cat wk/gp14/05_interf_u/repro/r1_judge.json                                                                                         # "judge": [8, ...]
python3 -X utf8 py_tools/quick_score.py wk/gp14/05_interf_u/repro/r1_s8_fast.kicad_pcb --route wk/gp14/05_interf_u/repro/r1_s8_route.json   # blocking=1, no floorplan term
```

**Existing issues:** `gh issue list --search "judge seed floorplan errors"`, `"decap limit broken"`,
`"quick_score"`: none covers it (nearest: #1099 "decaps unarmed", #1258 place_seed exit code on NOT BUILDABLE).

---

## 2. `route_plan_check` R14 refuses the routing skill's own Step 8 pour-last chain

**Tool:** `.claude/skills/plan-pcb-routing/scripts/route_plan_check.py`, rule R14 (`r_net_coverage_reconciles`).

**What it claimed.** `FAIL R14 net coverage reconciles (Step 5b) -- Net-coverage gap: ['GND'] handled by no
stage -- the route step excludes ['GND'] and Step 2b routes []`, then `REFUSED ... Fix the plan; do not run it.`

**What was true.** The plan is the Step 8 "dense 2-layer" order the routing skill prescribes: route signals
first (`route.py --nets '*' '!GND'`), pour GND last (`route_planes.py --nets GND`), and close on
`route.py --nets '*'` (twice). GND is claimed by the pour and by both closing `'*'` steps, and
`check_connected` on the result reports every net connected. R14 unions the `!X` exclusions of EVERY
`route.py` step in the plan, so any net excluded by an early step is an "orphan" even when a later step
claims it. The only plan R14 accepts keeps GND in the first step; measured on the same placement (arm O) that
variant ends with 2 broken nets and 182 vias, against 0 broken and 157 vias for the refused plan (arm I /
`final_route/`). I ran the refused plan and say so in REPORT.md; the skill's "do not run it" and its Step 8
recipe cannot both be followed.

**Reproduce:**
```bash
python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py wk/gp14/05_interf_u/repro/interf_u_plan.sh --board wk/gp14/05_interf_u/repro/r3_s7.kicad_pcb   # FAIL R14
```

**Existing issues:** `"route_plan_check"`, `"Step 5b"`, `"pour last 2-layer net coverage"`: none (nearest
#377, plane nets claimed by nobody -- the opposite case).

---

## 3. A pour that places no via writes a via-drill floor, and the next step reports a fab-floor relaxation the board never had

**Tools:** `py_router/route_planes.py` (project writeback) then `py_router/route.py` (`FAB FLOOR RELAXED`
disclosure); `py_router/list_nets.py --design-rules` (the suggestion followed).

**What they claimed.** `list_nets --design-rules` suggests `--via-size 0.9 --via-drill 0.5` (the board's own
`min_through_hole_diameter` is 0.5, `min_via_diameter` 0.9; the board declares no via-drill rule). After a bare
GND pour, `route.py` with that drill printed `FAB FLOOR RELAXED -- via drill: 0.6 -> 0.5 mm; 107 of 107
object(s) on this board are below the ORIGINAL 0.6mm`.

**What was true.** The input project has no `min_via_drill` (`None`). `route_planes.py`, which placed 0 vias,
wrote `rules.min_via_drill: None -> 0.6 mm` (the Default netclass DRAWING drill) into its output project, and the
next step treated that invented value as the board's original floor. Every via was flagged as below a floor
nobody declared. Cost: ~5 min tracing it; the final chain uses `--via-drill 0.6` so no step reports a
relaxation at all.

**Reproduce:**
```bash
python3 -X utf8 py_router/route_planes.py wk/gp14/05_interf_u/repro/placed.kicad_pcb wk/gp14/05_interf_u/repro/out/pour.kicad_pcb --nets GND --plane-layers B.Cu   # "rules.min_via_drill: None -> 0.6 mm", 0 vias on the board
python3 -X utf8 py_router/route.py wk/gp14/05_interf_u/repro/out/pour.kicad_pcb wk/gp14/05_interf_u/repro/out/route.kicad_pcb --nets '*' --quick 2 --no-bga-zones --layer-costs 1.0 1.0 --direction-preference-cost 4000 --turn-cost 2000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.5 --power-nets VCC GND --power-nets-widths 0.5 0.5   # "via drill: 0.6 -> ...; 122 of 122 ... below the ORIGINAL 0.6mm"
```

**Existing issues:** `"min_via_drill route_planes"`, `"FAB FLOOR RELAXED via drill"`: none for route_planes;
closest is #1195 (closed) "qfn_fanout lowers the via and hole floors on a run that places no via" -- the same
family (a no-via step writing via floors), on a different tool.

---

## 4. `place_pose` says `legal: false` on every pose of this board, and writes a NOT BUILDABLE one with exit 0

**Tool:** `py_placer/place_pose.py ... set C1 ... set R2 ...` (the post-placement nudge of CHOSEN.json's `after`).

**What it claimed.** `legal: false`, `no_worse: true`, exit 0, board written -- for every candidate pose,
including the one shipped.

**What was true.** The `false` comes from `pad_edge_conflicts 62` (before and after): BUS1's 62 ISA edge
fingers graded against a "fixed default" 0.55 mm board-edge clearance (`BUS1.61: edge shortfall 0.296 mm`).
The fingers sit on the outline by design (a PCB-edge plug at its declared pose), and the board's own
`min_copper_edge_clearance` is 0 (0.2 after the routing writeback), so on this board the flag carries no
information about the move. Meanwhile the real defect of a bad pose -- a courtyard-blocking C1<->R2 or C1<->U5
overlap, which `check_assembly` calls NOT BUILDABLE -- was written with exit 0 (the skill already warns that
place_pose's "legal" is not "buildable"). Cost: ten candidate poses tried by hand with `check_assembly` after
each (~4 min).

**Reproduce:**
```bash
python3 -X utf8 py_placer/place_pose.py wk/gp14/05_interf_u/repro/r3_s0.kicad_pcb wk/gp14/05_interf_u/repro/out/nudge.kicad_pcb set C1 131.4 60.9 --rot 180   # legal false (pad_edge_conflicts 62: BUS1 fingers), exit 0, written
python3 -X utf8 py_tools/check_assembly.py wk/gp14/05_interf_u/repro/out/nudge.kicad_pcb --baseline wk/gp14/05_interf_u/fixed.kicad_pcb                # NOT BUILDABLE: C1 <-> R2 courtyard 0.51 mm2, GATES
```

**Existing issues:** `"place_pose edge fingers legal"`, `"edge fingers board edge clearance"`: none (nearest
#1098, parts on a USB plug tongue's mating area -- a different channel).

---

## 5. `route_planes` replaces the board's GND zone settings and says only "with new parameters"

**Tool:** `py_router/route_planes.py --nets GND --plane-layers B.Cu` on a board that already pours GND on B.Cu.

**What it claimed.** `Note: Replacing existing zone on B.Cu for net 'GND' with new parameters`.

**What was true.** The human zone (`clearance 0.5`, `min_thickness 0.2`, thermal-relief pad connections,
`thermal_gap/bridge 0.508`) became `clearance 0.254`, `min_thickness 0.1`, `connect_pads yes` (solid),
`thermal 0.2/0.2`. Nothing names those changes. Consequence measured on the final board:
`tests/stress/kicad_drc_compare.py` (staged `min_connection` = the project's 0.2 mm min track) finds 13 GND
webs narrower than 0.2 mm; re-pouring at the original `--min-thickness 0.2` (arm P) cleared all 13 but left a
net broken, so the shipped board keeps them (they are not violations of the board's own rules,
`min_connection` 0). Cost: one arm (~2 min) and a report caveat. (The routing skill says to leave the
connection style alone, so the solid connection was not overridden.)

**Reproduce:**
```bash
grep -n "(zone" -A12 wk/gp14/05_interf_u/interf_u.kicad_pcb | grep -E "clearance|min_thickness|thermal"
python3 -X utf8 py_router/route_planes.py wk/gp14/05_interf_u/repro/placed.kicad_pcb wk/gp14/05_interf_u/repro/out/pour.kicad_pcb --nets GND --plane-layers B.Cu
grep -n "(zone" -A12 wk/gp14/05_interf_u/repro/out/pour.kicad_pcb | grep -E "connect_pads|clearance|min_thickness|thermal"
```

**Existing issues:** `"replacing existing zone"`, `"zone settings route_planes"`: none (nearest #1056, Planes tab
layer choice / duplicate zones).

---

## 6. Intent rows spell their reason two ways

**Tool:** the intent reader (`check_groups.py` / `check_floorplan.py` / `place_simple`).

**What it claimed.** Adding `"why"` to a `proximity[]` row (the key `fixed_poses[]` rows use) is refused:
`proximity[5]: unknown key(s) why. Known: basis, context, max_mm, near, note, pads, ref, source`; and `"note"`
is refused on `fixed_poses[]` (`Known: ..., why, x, y`).

**What was true.** Both are free-text reasons; each row type accepts only one spelling. Cost: one failed
check and a regenerated intent (~1 min). Reproduce (`repro/intent_with_why.json` is the given intent with
`"why": "x"` added to `proximity[0]`):
```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent_with_why.json   # proximity[0]: unknown key(s) why
```

**Existing issues:** `"proximity why note intent"`: none.
