# TOOL_GAPS -- gp14 board 01 (ecc83-pp_v2)

Ranked by what each cost this run. All commands run from WT
(`cd ~/Documents/git/krt-gp14 && export PATH="$HOME/.venvs/krt/bin:$PATH"`).
The input board for every repro is `wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb`
(a `copy_board.py` copy of the kept placement `r1/s7.kicad_pcb`, with its `.kicad_pro`).
No helper scripts were written (`helpers/` is empty): every measurement below is a repo tool.

## 1. The auto-recorded `redo_commands.sh` drops env-knob prefixes, so the shipped chain does not replay

- **Tool / command:** `py_router/redo_record.py` (`record_invocation`, called at the top of
  `route.py`'s `main()`), with `REDO_RUNDIR`/`REDO_MANIFEST` exported, running
  `KICAD_PLANE_FRAGILITY_COST=0 python3 -X utf8 py_router/route.py ... --grid-step 0.05 ...`.
  Also `tests/stress/manifest_to_plan.py` on the plan.
- **What it claims:** the module docstring: "The stress-test redo harness replays the exact command
  sequence a board run executed". The routing skill (Step 2c item 4, Step 9) says env knobs ride
  "as env-var prefixes on the command line so the manifest replays them"; issue #670 says "Env knobs
  replay fine in redo-manifest plan files (shell env prefixes)".
- **What was true:** `record_invocation` writes `["python3","-u","-X","utf8"] + sys.argv` only
  (redo_record.py lines ~93-104); the environment is never read. `final_route/redo_commands.sh`
  records the route step with NO `KICAD_PLANE_FRAGILITY_COST=0` prefix, although the same run's own
  `JSON_SUMMARY` lists `"env_knobs": {"KICAD_PLANE_FRAGILITY_COST": "0", ...}`. Replaying the recorded
  line gives a different board: **2 vias / 146.10 mm** against the shipped **0 vias / 131.72 mm**
  (board_score). `manifest_to_plan.py` then writes a 1-step `placed_plan.json` with the knob silently
  gone and prints "0 command(s) skipped" -- no warning that the plan JSON will not reproduce the board.
  Workaround: the hand-written `final_route/placed_plan.sh` carries the prefix (it is the
  authoritative chain); `redo_commands.sh` was left exactly as the tool wrote it.
- **Reproduce:**
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  F=$(pwd)/$RP/rec; mkdir -p $F
  REDO_RUNDIR=$F REDO_MANIFEST=$F/redo_commands.sh KICAD_PLANE_FRAGILITY_COST=0 python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/rec/out.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05
  tail -1 $F/redo_commands.sh          # no KICAD_PLANE_FRAGILITY_COST=0 prefix
  # replay of that line (no env) vs the real run (env):
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/replay_noenv.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05
  python3 -X utf8 py_tools/board_score.py $RP/replay_noenv.kicad_pcb --quiet   # vias=2 copper_mm=146.1
  ```
  (Recorded outputs: `repro/replay_noenv.*` vs `repro/replay_env.*`.)
- **gh issue search:** `redo_commands env knob`, `record_invocation env`: nothing. `redo manifest env`,
  `manifest_to_plan env`: **#670 (OPEN)** covers only the plan-JSON half, and its premise ("env knobs
  replay fine in redo-manifest plan files") is false for the AUTO-recorded manifest.
  `KICAD_PLANE_FRAGILITY_COST`: #465 (closed, "promote experimental env knobs to real flags") -- the
  fragility knob was not promoted; it has no CLI flag.

## 2. `place_pose rotate REF 180` is absolute and turns about the footprint origin; the skill's "turn it" step does not say so

- **Tool / command:** `py_placer/place_pose.py <in> <out> rotate R2 180`, as SKILL.md §3.6 step 4
  and the place-mode paragraph write it ("turn each two-pad part ... with `place_pose ... rotate`").
- **What it claimed:** exit 0, "Modified 1 footprint positions", "Successfully wrote ...".
- **What was true:** `rotate REF DEG` sets an ABSOLUTE angle (`--relative` adds); R2 was already at
  180, so the written board is byte-identical to the input (sha256 88e6f1af... both). The tool does
  print `rotate R2       unmoved` and `"moved": []`, but also the false "Modified 1 footprint
  positions". I ran a batch of 10 "turns" this way and got 10 identical routes before noticing --
  it nearly became the finding "no turn changes the route". With `--relative`, a turn is about the
  footprint ORIGIN, which on these THT parts is pad 1, so a 180 deg "turn" of an axial resistor moves
  its body 7.62 mm rather than swapping its pads in place: of the 10 two-pad parts, 6 relative turns
  were refused (pad stack R2/U1, R4/P6, pad conflicts P2/R3, P4/R2, R1 and C2 off the outline) and 3
  were written but `check_assembly` NOT BUILDABLE (P3, R3, C1). An in-place pad swap needs a computed
  `set REF X Y --rot` instead. (Cost here was small because `route_review` listed 0 turned parts.)
- **Reproduce:**
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  python3 -X utf8 py_placer/place_pose.py $RP/placed.kicad_pcb $RP/rot_R2_abs.kicad_pcb rotate R2 180   # exit 0, "Modified 1 footprint positions", "unmoved"
  shasum -a 256 $RP/placed.kicad_pcb $RP/rot_R2_abs.kicad_pcb                                              # identical
  python3 -X utf8 py_placer/place_pose.py $RP/placed.kicad_pcb $RP/rot_R2_rel.kicad_pcb rotate R2 180 --relative   # exit 4, pad stack R2/U1
  ```
- **gh issue search:** `place_pose rotate relative`, `place_pose rotate unmoved`, `Modified 1 footprint
  positions`: no issue covers it.

## 3. The seed judge (`route.py --quick 2`) ranks vias without the plane-fragility field the shipping route uses

- **Tool / command:** SKILL.md §3.6 steps 1-2: `route.py --quick 2` + `quick_score.py`, "Keep the best
  by blocking, then vias, copper_mm, segments"; then §3.7 routes the kept placement with the full chain.
- **What it claimed:** level 2 "picks seeds as well" as the full route; the judged numbers rank seeds by
  vias first.
- **What was true:** `--quick 2` skips the plane-fragility field (`"plane_fragility": {"why":
  "--quick 2"}`), so a judging route crosses the board's B.Cu GND pour for free. On the kept seed s7,
  same sizes and layer costs: judge **0 vias / 135.64 mm**; full chain **2 vias / 146.29 mm** (the B+
  net detours and jumps the heater track with a 2-via B.Cu jumper to avoid cutting the pour). Every
  judged seed's via count was therefore measured under a pricing the shipping route does not use;
  reaching the judged via count on the shipped board needed the non-default env knob
  `KICAD_PLANE_FRAGILITY_COST=0` (which in turn hit gap 1). On a 2-layer board with a back-side pour
  the judge's via ranking and the full route's can disagree.
- **Reproduce:**
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/q2.kicad_pcb --nets '*' --quick 2 --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --json-out $RP/q2.route.json
  python3 -X utf8 py_tools/quick_score.py $RP/q2.kicad_pcb --route $RP/q2.route.json      # vias=0 copper_mm=135.64
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/full.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0
  python3 -X utf8 py_tools/board_score.py $RP/full.kicad_pcb --quiet                        # vias=2 copper_mm=146.29
  ```
- **gh issue search:** `quick 2 plane fragility`, `quick seed judge fragility vias`: nothing relevant
  (#875 and #424 are about oracle reproducibility / connectivity, not this).

## 4. `check_floorplan --intent intent.json` exits 4 ("pass": false) on the finished board with 0 errors and 0 violations

- **Tool / command:** `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/01_ecc83-pp_v2/final.kicad_pcb --intent wk/gp14/01_ecc83-pp_v2/intent.json --allow-routed`
- **What it claimed:** exit 4, `"pass": false`.
- **What was true:** `"errors": 0, "violations": 0, "warnings": 0`; the only reason is
  `rules_dark_undispositioned: ["zone_containment", "legality"]` -- two rules the GIVEN intent leaves
  "OWED" (no `blocks[].zone`, no `legality_budget`, no written disposition). The verifier brief grades
  "0 errors", so the board passes, but a run that reads the exit code reads a failure it cannot act on
  without editing an intent it is not allowed to edit. Cost: a minute of reading; noted so a grader
  does not take exit 4 for a floorplan error.
- **Reproduce:** the command above (`repro/floorplan_final.log`).
- **gh issue search:** `check_floorplan OWED exit 4`, `rules_dark_undispositioned`: nothing.

## 5. The skills' chain ships the pour unfilled: KiCad opens the "DONE" board with 6 unconnected items (skill step missing)

- **Tool / command:** the routing chain as `/plan-pcb-routing` writes it (no `--write-fill` anywhere
  in either skill), graded by `board_score` / `check_complete` / `check_connected`.
- **What it claimed:** `check_connected`: "ALL NETS FULLY CONNECTED!"; `check_complete`: DONE.
- **What was true:** those graders refill the zone themselves (check_connected's "KiCad refill
  cross-check"), so they grade the board KiCad WOULD have after a refill. The file as shipped carried
  the GND zone outline only; plain `kicad-cli pcb drc` (no `--refill-zones`) on it reports
  **6 unconnected items** -- every GND pad, which reaches GND only through the B.Cu pour. The verifier
  (call 1) noted it. Re-routing with `route.py --write-fill` (#910's opt-in) wrote the fill and the
  same plain DRC reported **0 unconnected**; tracks unchanged (0 vias / 131.72 mm / 30 segments). The
  fix exists; neither SKILL.md says to use it, so every run of these skills ships an unfilled board.
- **Reproduce:**
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-all -o $RP/final_kicad_drc.json $RP/final_copy.kicad_pcb     # "Found 6 unconnected items" (unfilled first final)
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-all -o $RP/final2_kicad_drc.json $RP/final2_copy.kicad_pcb   # "Found 0 unconnected items" (--write-fill)
  ```
- **gh issue search:** `write-fill`, `unfilled zone deliverable`: **#910 (closed)** added the opt-in
  flag; nothing makes the skills use it.

## 6. No check in the skills grades silkscreen: a verified-DONE board carries 4 KiCad silkscreen errors

- **Tool / command:** the skill's verification set (`board_score`, `check_complete`, `check_drc`,
  `tests/stress/kicad_drc_compare.py`, which prints "CONSISTENT").
- **What it claimed:** DONE / no DRC violations / `kicad=0 check_drc=0 ... CONSISTENT`.
- **What was true:** `kicad-cli pcb drc` on the final board: 3 `silk_overlap` errors (P1 reference vs
  U1 silk circle; U1 reference vs P3 reference; P4 reference vs R2 silk segment) and 1
  `silk_over_copper` error (U1 reference clipped by R2 pad 1's mask). `kicad_drc_compare` compares
  copper only. The tool that fixes them exists (`py_placer/beautify_labels.py`, #481, which records
  itself into the redo manifest), but neither skill names it or grades silkscreen, so a run that
  follows the skill as written never sees these. Not run here (outside the skill's workflow, which
  this campaign measures); left as found and reported in REPORT.md.
- **Reproduce:** the first `kicad-cli` command in entry 5 (the silk errors are identical on both files).
- **gh issue search:** `silk_overlap`, `beautify_labels`: #481 (closed, the tool), #1202 (closed,
  papercuts in it). Nothing about grading silkscreen in the placement/routing skills.
