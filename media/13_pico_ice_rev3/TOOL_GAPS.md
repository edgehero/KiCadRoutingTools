# TOOL_GAPS -- gp14 board 13 (pico_ice_rev3)

Ranked by what each cost this run. No helper scripts were written (`helpers/` is empty): every workaround
below was done with the repo's own CLIs (`place_pose`, `check_floorplan`, `route.py` ...) driven from the shell.
All repro commands run from the WT root (`~/Documents/git/krt-gp14`) with the venv on PATH; their inputs
are copied into `wk/gp14/13_pico_ice_rev3/repro/`.

---

## 1. The round judge cannot see the intent's decap limits, and DONE grades them as blocking (cost: highest)

- **Tool / step:** SKILL §3.5-3.6, the round flow: `place_simple --round` names the cheapest legal seeds
  (`judge.json`), `py_tools/quick_score.py` scores their `--quick 2` routes, "keep the best by blocking,
  then vias ... If its blocking is 0, stop here: that board is the placement".
- **What it claimed:** the kept seed is the round's best placement, and a clean fast route ends the loop.
- **What was true:** `quick_score`'s `blocking` is the route tally only. This board's intent arms
  `decaps.max_distance_mm` 2.42 and `max_pin_distance_mm` 2.19 at ERROR, and `board_score --intent` counts every
  such finding in `blocking` (component `floorplan`). Every judged seed of every round broke them
  (`final.decap_broken` in `r<N>/s<S>.json`: r1 4-20, r2 2-12, r3 4-8, r4 3-15, r5 4-8, r6 2-7). So the judge
  ranked placements none of which could reach DONE, and picked r1/s6 (8 floorplan errors) over seeds with 4. Had a
  fast route come back 0, the skill's stop rule would have ended the loop on a board `board_score` grades
  `blocking` 8. Each kept placement then needed a hand decap pass (gap 2) before a full route was worth running.
- **Repro:**
  `python3 -X utf8 py_tools/board_score.py wk/gp14/13_pico_ice_rev3/repro/r1_s6.kicad_pcb --intent wk/gp14/13_pico_ice_rev3/repro/intent_rows.json --baseline wk/gp14/13_pico_ice_rev3/repro/r1_fixed.kicad_pcb --quiet`
  -> `floorplan=8` in the BLOCKING line, while `r1/judge.json` names seed 6 first and `quick_score` (route tally) knows
  nothing of it.
- **gh issue list:** `--search "quick_score"` -> none; `--search "decap_pin_distance"` -> #1188, #1150, #1067,
  #1043, #1102 (all closed; repair passes / measurement, none about the judge or the round's stop rule ignoring the
  floorplan component).

## 2. No tool repairs a placed board's decap limits; place_simple leaves the same structural pins broken every seed

- **Tool:** `py_placer/place_simple.py --round --decap-limit-weight 100` (default 10), and the absence of any decap
  repair CLI on this branch (`--repair-decaps` from #1188 is not in the tree: `grep -rn "repair-decaps" py_placer
  py_tools` finds nothing).
- **What it claimed:** the anneal prices "each supply pin's gap to its nearest cap, measured as the grade measures
  them" at `decap_limit_weight` per mm.
- **What was true:** across 72 placed seeds (6 rounds x 12) at weight 10 and 100, the errors never reached 0, and from
  r3 on they were always the same pins: the QFN supply pins whose side faces the 2x20 header rows (U3 pins 10 and
  33, U6 pins 29/33 with U6 at 180 deg). Raising the weight 10x moved the count (r1 4-20 -> r2 2-12) but never
  closed it, because the only legal spots within 2.19 mm of those pins are in the QFN's own fan-out halo. I fixed
  them by hand on every candidate: computed a pose beside the pin, tried each +3V3 cap there with `place_pose`
  in a shell loop, re-ran `check_floorplan`. Five hand passes (fix1, fix2, r5s6_fix, r6s10_fix, plus the probe
  loop), and each one costs routability (fix1's fast route 9 -> 31 on the same seed: the caps sit in the side
  escapes).
- **Repro:**
  `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/13_pico_ice_rev3/repro/r5_s6.kicad_pcb --intent wk/gp14/13_pico_ice_rev3/repro/intent_rows.json | grep ERROR`
  -> U3 pin 10, U3 pin 33, U6 pin 29, U6 pin 33 (r5/s6 was placed with `--decap-limit-weight 100`).
- **gh issue list:** `--search "decap repair placed board tool"` -> #1051, #487 (unrelated); `--search
  "decap_pin_distance"` -> #1188 (closed: the repair pass tried one cap per finding) -- the repair it describes is
  not on this branch.

## 3. The quick judging route does not predict the full route on this board (router noise > placement signal)

- **Tool:** `route.py --quick 2` + `quick_score.py` as the seed judge (SKILL §3.6 steps 1-2).
- **What it claimed (skill text):** "Level 2 ... picks seeds as well (measured over 16 seeds of five corpus boards
  against their full routes)".
- **What was true here:**
  - the same placement (r1/s6), re-routed with small parameter changes, scored 8, 12, 16, 17, 18, 19, 21, 21, 22,
    42 blocking (`exp/s6_v*.log`);
  - six seeds sharing one LOCKED IC skeleton (r3) scored 9 .. 33;
  - quick -> full did not keep order: r3/s10 (+ decap fix) quick 20 -> full 17; r5/s6 (+ decap fix) quick 22 ->
    full 9 (cl 0.09); r6/s10 (+ fix) quick 14 (seed) -> full 12; r1/s6 quick 12 -> full 32 (incl. floorplan 8,
    drc 6).
  The best board of the run came from a seed the quick judge ranked mid-pack.
- **Repro:**
  `python3 -X utf8 py_router/route.py wk/gp14/13_pico_ice_rev3/repro/r1_s6_step2a.kicad_pcb /tmp/a.kicad_pcb --nets '*' --quick 2 --json-out /tmp/a.json --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --track-width 0.0889 --clearance-ceiling 0.1`
  then the same with `--track-width 0.0762` (12 vs 21 blocking by `quick_score`).
- **gh issue list:** `--search "judging route noise seeds variance"` -> none; `--search "quick 2 judge"` -> #504,
  #424, #8 (unrelated).

## 4. route_planes (a bare pour) rewrites the board's authored copper-to-hole floor

- **Tool:** `py_router/route_planes.py <board> <out> --nets GND +3V3 --plane-layers In1.Cu In2.Cu`
- **What it claimed:** "the plane step places no taps" (it routes nothing near a hole), and it prints
  `FAB FLOOR RELAXED ... copper-to-hole clearance: 0.254 -> 0.127 mm`.
- **What was true:** the input project's `min_hole_clearance` 0.254 is the board's own authored rule; a step that
  lays no copper near any hole lowered it, and every later checker grades against the new value. By the end of the
  chain the shipped project declares `min_hole_clearance` 0.09. It is disclosed (loudly), not silent -- the gap is
  that nothing asked for it and the pour did not need it.
- **Repro:**
  `python3 -X utf8 py_router/route_planes.py wk/gp14/13_pico_ice_rev3/repro/r1_s6.kicad_pcb /tmp/p.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu | grep min_hole_clearance`
  -> `rules.min_hole_clearance: 0.254 -> 0.127 mm`.
- **gh issue list:** `--search "min_hole_clearance"` -> #1285 (closed: `--no-fix-drc-settings` still lowers it via
  in-run floor sync), #1198, #1038 (closed). Related, not the same case (a bare pour, default flags).

## 5. Step 2d iterations were byte-identical no-ops on the plateaued board

- **Tool:** `route.py <prev> <next> --nets '*' <the Step 2 flags>` twice (routing SKILL Step 2d: "bake two passes
  into every plan ... historically descend frontier boards 25->15").
- **What was true:** chain A (`final_route_old1/`): step2 -> iter1 -> iter2 all graded `broken 16, drc 1`, vias
  334, copper 2928.06 (same numbers to the hundredth). The passes cost 4 min each and changed no copper. On the
  best chain one more `'*'` pass made it worse (broken 8 -> 9, `exp/r5s6c09/iter1`). Only scoped rip laps moved
  anything (drc 1 -> 0). Not wrong, but the skill's "near-free and descends" did not hold here.
- **Repro:** `python3 -X utf8 py_router/route.py wk/gp14/13_pico_ice_rev3/repro/old1_step2.kicad_pcb /tmp/i.kicad_pcb --nets '*' --power-nets GND +3V3 VBUS VDC 'Net-(D5-K)' +1V1 +1V2 '/+1.2V_CORE' '/VCC_PLL' '/VIO_BANK_2' '/+3V3_STDBY' --power-nets-widths 0.25 0.25 0.4 0.4 0.4 0.25 0.25 0.25 0.2 0.2 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --track-width 0.0889 --clearance-ceiling 0.1`
  then `board_score` both: identical.
- **gh issue list:** `--search "plateau iteration"` -> #656, #529, #412, #385 (none on this).

## 6. SKILL instruction gaps met on this board

- §3.4 says to declare a plug-in module's pin rows in the intent's `fixed_poses[]`; the run's intent is given and
  may not be edited, so the rows (J2/J3) and SW2's `mating_face` went into a new `intent_rows.json`.
- The skill has no step for the intent's decap limits after `place_simple` (gap 2), although DONE grades them.
- The skill caps placement at `--rounds 3` but §3.7/§4 send a placement-classified routing failure back to
  "re-place"; it does not say whether those re-placements are rounds 4+ (this run treated them as rounds 4-6).
- `check_floorplan --intent` exits 4 on the final board with **0 errors**, because the given intent leaves three
  rules dark and OWED (`zone_containment`, `zone_side`, `legality`); `grade.py` records `floorplan_pass: false`
  next to `floorplan_errors: 0`. The verifier brief only asks for 0 errors, so the two say different things.
- **gh issue list:** `--search "fixed_poses module"` -> none; `--search "dark rule"` -> #997, #959 (closed).

## 7. place_pose on a pile prints ~280 KB of JSON for a six-fiducial `set`

- **Tool:** `python3 -X utf8 py_placer/place_pose.py wk/gp14/13_pico_ice_rev3/repro/pile.kicad_pcb /tmp/f.kicad_pcb set FID1 67.3 75.0 lock FID1`
- **What was true:** the `JSON_SUMMARY` line carries every off-board pad row of the 97-part pile (the harness
  truncated it to a file). A refusal's one-line reason (`REFUSED ... pad_conflict_pairs new: FID2/U8, FID4/U8`)
  is buried in it. Cost: context, and one retry to find the reason.
- **gh issue list:** `--search "place_pose"` -> #1064, #1266, #1211, #1100 (none on output size).

---

Not a repo tool: the PTS820 datasheet could not be fetched (arrow.com PDF timed out twice, ckswitches.com
redirected, curl blocked), so SW2's `mating_face` was decided from the footprint's geometry (see REPORT.md).
