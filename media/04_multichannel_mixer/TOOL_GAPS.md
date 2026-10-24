# TOOL_GAPS -- gpm board 04 multichannel_mixer

Ranked by what each one cost this run. Every repro command runs from the WT root
(`~/Documents/git/krt-gpm`) after
`export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`.
The boards they need are in `wk/gpm/04_multichannel_mixer/repro/` (copied with
`copy_board.py`, so each keeps its `.kicad_pro`). `R=wk/gpm/04_multichannel_mixer`.

---

## 1. route.py cages a plane-net SMD pin on its own layer and cannot reconnect it at the board's via floor (the router, not the placement)

- **Tool / command:** `py_router/route.py` (in-run plane finalize, KiCad oracle reconnect, reconciliation),
  routing the kept seed 11 at the board's own floors:
  `route.py IN OUT --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --power-nets GND +12V --power-nets-widths 0.3 0.3 --layer-costs 1.0 2.0 --via-cost 600 --escalation board`.
- **What it claimed:** `JSON_ORACLE ... links_failed ... remaining 1`, `Plane finalize: ... unroutable without rip
  authority on GND`, hint "boxed in by static obstacles ... try a finer grid and/or smaller clearance/track"
  (it names the blockers it may not rip: `vbias`, `Net-(IC2A-OUT)`).
- **What was true:** the GND pin is caged by the run's OWN copper, not by the placement. On the routed board
  (`repro/gap4_a5_routed.kicad_pcb`, = arm_a5/step2), `check_reachability --pad IC2.4 --clearance 0.3 --track 0.3 --via 1.5`
  says **PASSABLE without the routing (bottleneck 6.0 mm, margin +5707 um) and CAGED with it**. The pour cannot
  enter: pin 3 (vbias) on one side, a vbias 1.5 mm via above it, an `IC2A-OUT` track 0.45 mm off its other side.
  Every TL072's pin 4 (GND) sits between pin 3 and pin 5 (both vbias), so the same cage recurs at IC2.4 / IC4.4 /
  IC5.4 / IC1.4 depending on the arm. Measured on seed 11 over 7 strict arms (layer costs 1/1, 1/2, 1/3, plane
  fragility 6, max-ripup 5, same-net-pad-clearance 0.1, iteration lap): every one left 1-4 GND joins. `--rip-existing-nets`
  on the hinted nets restored the original copper ("original copper restored [was blocking 'GND']"); only
  `--force-reroute` of the cage nets (with GND in `--nets`) ever closed it, and only on some seeds. The 4 vias it
  would have saved (via-cost 800/1000 arms: 38 vias with one caged GND pin) were never recoverable.
- **Cost:** the largest of the run: ~25 route runs and two changes of the kept seed (11 -> 2 -> 10).
- **Repro:**
  ```
  python3 -X utf8 py_tools/check_reachability.py $R/repro/gap4_a5_routed.kicad_pcb --pad IC2.4 --clearance 0.3 --track 0.3 --via 1.5
  # -> VERDICT PASSABLE ... "with the routing in place: CAGED"
  python3 -X utf8 py_router/route.py $R/repro/gap2_s11.kicad_pcb $R/repro/gap1_out.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --power-nets GND +12V --power-nets-widths 0.3 0.3 --layer-costs 1.0 2.0 --via-cost 600 --escalation board
  # -> JSON_SUMMARY_MIN failed_single ["GND"], board_score broken 1
  ```
- **gh issue list** `"caged plane pad"`: #1348 (closed) is the same shape for `route_bus` caging a ball; nothing for
  route.py caging a poured net's own-layer pad. `"boxed in GND pad oracle"`: #1339, #572 (closed, about re-grade
  credit and link authority, not this). Not covered.

## 2. With the default `--escalation fab`, route.py lays vias below the board's own Board Setup minimum and rewrites that minimum; board_score and check_complete then call the board DONE

- **Tool / command:** `py_router/route.py` default (`--fab-tier auto --escalation fab`) on a board whose Board Setup
  says `min_via_diameter 1.5`, `min_track_width 0.3`, `min_clearance 0.3`; then `board_score.py` / `check_complete.py`
  without spec flags.
- **What it claimed:** `board_score` BLOCKING=0, `check_complete` VERDICT: DONE on `final_route_old1/step2.kicad_pcb`.
- **What was true:** 9 GND oracle-reconnect vias were laid at 0.45/0.2 mm (`design_rules.narrowed`, site
  "oracle reconnect"), and the writeback lowered the project to `rules.min_via_diameter: 1.5 -> 0.45`,
  `min_via_annular_width 0.3 -> 0.125`, `min_through_hole_diameter 0.3 -> 0.2`. Every grader then reads the rewritten
  `.kicad_pro`. Graded at the board's declared floors (`--min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3`)
  the same board is **blocking 18 (undersized 18: 9 via-size + 9 via-drill)**. Only `check_complete --authored-from`
  (report-only) says UNSOUND. The fast judging route did the same at the seed stage (vbias via-in-pad 0.6 and a
  last-resort 0.25 mm via; `rules.min_via_diameter: 1.5 -> 0.25`).
- **Skill gap inside it:** SKILL.md §1 says "DONE is measured with every spec the board declares. Pass ...
  `--min-track-width` / `--min-via-diameter` / `--min-via-drill`", and verifier.md asks for "Spec flags the board
  declares", but neither says that the Board Setup constraints ARE that declaration, nor that the routing chain's
  default escalation will descend below them. I recorded a false "first DONE" ledger row and corrected it.
- **Cost:** one false DONE row, a correction row, and the switch of the whole chain to `--escalation board`.
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $R/repro/gap2_s11.kicad_pcb $R/repro/gap2_out.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --power-nets GND +12V --power-nets-widths 0.3 0.3 --layer-costs 1.0 1.0 --via-cost 600
  python3 -X utf8 py_tools/board_score.py $R/repro/gap2_out.kicad_pcb --quiet          # BLOCKING=0
  python3 -X utf8 py_tools/board_score.py $R/repro/gap2_out.kicad_pcb --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --quiet   # undersized 18
  ```
- **gh issue list** `"escalation board floor min_via_diameter writeback"`: #1287, #1170 (closed; neighbouring
  escalation bugs). `"authored-from UNSOUND"`: #1198, #1160 (closed). None covers "graders read the floor the run
  rewrote, so a default chain reaches DONE below the authored via floor".

## 3. fill_for_delivery saves in KiCad 10 format, which turns 20 accepted vias-in-paste into 20 blocking violations

- **Tool / command:** `py_tools/fill_for_delivery.py <routed board> -o delivered.kicad_pcb` (§3.9 step 2).
- **What it claimed:** `Filled ... net classes preserved ... unconnected (no --refill-zones): 31 -> 0`, EXIT 0.
- **What was true:** the input was file format 20241229 (KiCad 9), on which `check_drc` accepts the router's
  vias-in-pad as "undeclarable in this file format". The filled copy is written as 20260206 (KiCad 10), where the
  per-via `(capping)(filling)` tokens exist, so the same 20 vias are now "unprotected (violations)":
  **board_score on the routed board BLOCKING=0, on its filled copy BLOCKING=20 (drc_via_in_paste=20)**, and
  check_complete INCOMPLETE. The deliverable the verifier grades would have failed while every pre-delivery grade
  passed. Nothing in fill_for_delivery's output mentions the format change.
- **Workaround:** upgrade the routing input with `kicad-cli pcb upgrade` before the first route step, so route.py's
  own Type VII stamping (`fab_notes.via_protection_stamps`) can write the tokens ("20 stamped"); then re-route the
  whole chain. That step is not recorded by the REDO recorder (gap 8). It also happened to route better (42 vs 47 vias).
- **Cost:** one full re-route chain and a second label/fill pass (~15 min).
- **Repro:**
  ```
  python3 -X utf8 py_tools/board_score.py $R/repro/gap1_routed_v9.kicad_pcb --baseline $R/multichannel_mixer.kicad_pcb --quiet   # BLOCKING=0
  python3 -X utf8 py_tools/fill_for_delivery.py $R/repro/gap1_routed_v9.kicad_pcb -o $R/repro/gap1_filled.kicad_pcb
  head -3 $R/repro/gap1_filled.kicad_pcb        # (version 20260206)
  python3 -X utf8 py_tools/board_score.py $R/repro/gap1_filled.kicad_pcb --baseline $R/multichannel_mixer.kicad_pcb --quiet      # BLOCKING=20 drc_via_in_paste=20
  ```
- **gh issue list** `"fill_for_delivery"`: #1335 (closed; the skills never ran the fill). `"via in paste delivered"`,
  `"Type VII stamp file format"`, `"undeclarable format upgrade"`: nothing relevant. Not covered.

## 4. judge_seeds' quick-2 route cannot see poured-net closure, so it kept a seed that never reached DONE

- **Tool / command:** `py_placer/judge_seeds.py judge.json --chain judge_chain.txt --intent intent.json --jobs 2`.
- **What it claimed:** "best seed 11: keep its placement" (blocking 0, joins 0, 31 vias); every judged seed's
  `poured` line showed 6-12 GND joins "not counted".
- **What was true:** at the board's declared floors, seed 11 never closed GND in 8 full-route arms (gap 1); seed 2
  (judge rank 3) reached DONE at 57 vias and seed 10 (rank 2) at 46, later 42. The judge's ranking is by design
  blind to the plane finalize, and the judging chain ran at `--escalation fab` (gap 2), so neither the GND cage nor the
  via floor could reach the ranking. The skill gives no step for "the kept seed cannot be DONE but another judged
  seed can"; I full-routed the next judged seeds and switched (CHOSEN.json records seed 10).
- **Cost:** two changes of the kept placement, ~6 extra full routes.
- **Repro:** the judge's own record is `$R/judge_pass1.log` and `$R/s11_fast.score.json` / `$R/s10_fast.score.json`
  (both blocking 0, `poured: broken 8 / 9`; re-running judge_seeds would overwrite the filmed `s*_route/` files, so
  read them instead). Then the full route of gap 1's second command on `repro/gap2_s11.kicad_pcb` (broken 1), and the
  same command on `repro/gap3_s10.kicad_pcb` with `--layer-costs 1.0 1.0` followed by
  `route.py OUT OUT2 --nets GND vbias --force-reroute <same flags>` (board_score blocking 0 at the spec floors).
- **gh issue list** `"judge quick poured"`, `"judge_seeds poured nets"`: #1358, #1323 (closed, unrelated). Not covered.

## 5. A board check_complete calls DONE ships KiCad starved_thermal ERRORS; no repo tool removes them

- **Tool / command:** `route.py` chain -> `check_complete.py ... DONE`; `tests/stress/kicad_drc_compare.py` reports them.
- **What it claimed:** check_complete VERDICT: DONE on `final_route/lap_loops.kicad_pcb`.
- **What was true:** the project sets `starved_thermal` to **error** with `min_resolved_spokes 2`;
  kicad_drc_compare: `thermal=3` (IC1.4, C12.1, IC4.4 GND, each boxed by a signal track on B.Cu). KiCad's own DRC on
  that board shows 3 errors. Re-routing the named neighbours with `--force-reroute` moved the starvation around
  (3 -> 1, +4 vias); I cleared them with three hand GND stub joins (`check_join.py`, 1.8-2.4 mm each into open pour).
- **Cost:** ~10 min of laps and stub probing.
- **Repro:**
  ```
  python3 -X utf8 check_complete.py $R/repro/gap5_lap_loops.kicad_pcb --intent $R/intent.json --baseline $R/multichannel_mixer.kicad_pcb --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3   # DONE
  python3 -X utf8 tests/stress/kicad_drc_compare.py $R/repro/gap5_lap_loops.kicad_pcb --baseline $R/final.kicad_pcb   # thermal=3
  ```
- **gh issue list** `"starved_thermal"`: **#1334 (closed)** "A DONE board ships KiCad starved_thermal errors ... that
  no repo grader reports" -- covered for REPORTING (kicad_drc_compare now prints them); still not gated by
  check_complete and not fixed by any routing step.

## 6. route.py leaves redundant copper loops that check_complete does not grade

- **Tool / command:** `route.py` chain -> `py_tools/check_cycles.py`.
- **What it claimed:** check_complete DONE, check_weird "NO WEIRD THINGS FOUND".
- **What was true:** check_cycles: `Net-(IC3A-IN-)` and `Net-(IC3B-IN-)` each carry 1 redundant loop (2 independent
  loops) on `final_route/lap_vbias.kicad_pcb`. A `--force-reroute` lap of the two nets removed them (and 11 mm of copper).
- **Repro:** `python3 -X utf8 py_tools/check_cycles.py $R/repro/gap6_lap_vbias.kicad_pcb` (2 loops) vs
  `check_complete.py` on it (DONE).
- **gh issue list** `"redundant loop route.py"`: #162 (closed, same-net redundant copper: self-crossings and stacked
  duplicates, not cycles), #1166 (closed, dangling vias). `"check_cycles loop check_complete"`: nothing. Not covered.

## 7. route.py ships a sub-floor pad web that check_weird flags (check_complete INCOMPLETE)

- **Tool / command:** `route.py` (seed 2, `--escalation board`), then `check_complete.py`.
- **What it claimed:** route JSON_SUMMARY_MIN failed 0; board_score blocking 0.
- **What was true:** check_complete INCOMPLETE -- `weird_copper`: `narrow-pad-joint vbias (B.Cu) at (164.9, 80.8):
  terminal cap joins pad IC1.6 through a copper web below the 0.300mm min-track floor` (a 1.5 mm via placed in a
  0.6 mm SOIC pad). Cleared by `--nets vbias GND --force-reroute`.
- **Repro:** `python3 -X utf8 py_router/check_weird.py $R/repro/gap7_s2_lc1.kicad_pcb`.
- **gh issue list** `"narrow-pad-joint"`: #1161, #1187, #1063 (closed: phantom flags / floor choice). This one is a
  real web the router laid. Not covered.

## 8. The REDO manifest records neither `kicad-cli pcb upgrade` nor `check_join` hand joins

- **Tool / command:** the REDO recorder (`REDO_RUNDIR` / `REDO_MANIFEST`) during the final chain.
- **What was true:** `final_route/redo_commands.sh` got copy_board and the route.py steps only. The format upgrade
  (gap 3) and the three `check_join.py --keep-staged` joins had to be appended by hand (marked `# MANUAL STEP`), or a
  replay would reproduce neither the stamping nor the shipped copper.
- **gh issue list** `"redo manifest check_join"`, `"kicad-cli upgrade"`: nothing relevant.

## 9. The skill's "bake two iteration passes into every plan" added vias here

- **Tool / command:** plan-pcb-routing Step 2d, `route.py ... --nets '*'` x2 with the Step 2 flag string verbatim.
- **What was true:** seed 2: 56 -> 58 vias after the iterations (lap after them 59 vs 57 without); seed 10:
  `it2 -> lap` 51 vias vs 46 without. The iterations never closed a join here and only re-stitched GND. The shipped
  chain leaves them out; measured, kept the better.
- **gh issue list** `"iteration passes vias"`: nothing on this.

## 10. check_floorplan exits 4 on the finished board because the given (pile-emitted) intent can never be fully graded

- **Tool / command:** `check_floorplan.py delivered.kicad_pcb --intent intent.json --allow-routed` (also inside grade.py).
- **What it claimed:** EXIT 4, `"pass": false`, "NOT FULLY GRADED: 2 budget_abstained, 1 rules_skipped_armed", 4 rules OWED.
- **What was true:** 0 errors, 0 warnings. The intent was emitted from the pile, so its legality budgets are withheld
  for ever and four rules are dark without dispositions; the intent is read-only in this campaign, so no run can
  clear it. grade.py reports `floorplan_pass: false` next to `done: true`.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py $R/delivered.kicad_pcb --intent $R/intent.json --allow-routed; echo $?`.
- **gh issue list** `"authored-from UNSOUND"` / floorplan searches: nothing on this.

## 11. check_reachability defaults to the netclass sizes, not the board's floors

- **What was true:** a bare `check_reachability --pad IC2.4` graded at clearance 0.2 / track 0.2 / via 0.6
  (`knobs ... board netclass`) on a board whose Board Setup forbids vias under 1.5 mm. It printed the knobs, so it was
  readable, but the PASSABLE it gives is for a via the board does not allow. Pass `--clearance --track --via`.
- **gh issue list** `"check_reachability netclass default"`: nothing.

## 12. No PDF reader in this environment for §3.5 / analyze-power-nets datasheets

- **What was true:** `pdftotext` / `pdftoppm` (poppler) are not installed, so the Read tool cannot open a downloaded
  datasheet PDF and WebFetch returns compressed streams. I took the TL072 supply current from a WebSearch summary of
  TI's parametric table (Iq 1.4 mA typ / 2.5 mA max per channel). No template was needed on this board, so the cost
  was small.
- **gh issue list** `"poppler pdftotext datasheet"`, `"datasheet pdf"`: nothing.

## 13. converge.py record: quick_score payloads carry no board_sha; the --rejected lever heuristic

- **What was true:** every judged-seed row warned "score payload carries no board_sha ... cannot verify it grades
  THIS board" (quick_score writes none), and "entry is --rejected but the lever text never says so" for levers that
  said "not kept". Cosmetic; rows were recorded.
- **gh issue list** `"quick_score board_sha"`: nothing; #1323 (closed) is a different quick_score/ledger interaction.

---

Helpers written: none (`helpers/` is empty; one convenience wrapper was drafted and moved to `old/` unused).
