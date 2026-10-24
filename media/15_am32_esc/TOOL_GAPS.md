# TOOL_GAPS -- 15 am32_esc

Ranked by what each cost this run. Every command runs from WT (`~/Documents/git/krt-gpm`) with the venv's
python3 first on PATH (`export PATH="$HOME/.venvs/krt/bin:$PATH"`); the boards each needs are in
`wk/gpm/15_am32_esc/repro/`. Issue searches are read-only `gh issue list --repo drandyhaas/KiCadRoutingTools
--state all --search "<keywords>"`.

## 1. route.py ships redundant copper loops / dangling ends that check_complete rejects, and nothing removes them

- **Tool / command:** `py_router/route.py ... --nets '*' --power-nets ... --via-cost 300 --layer-costs 1.0 3.0 3.0 1.0
  --grid-step 0.05` (and the same chain with other levers), then `check_complete.py`.
- **What it claimed:** route.py's `JSON_SUMMARY_MIN` `failed: 0`, and `board_score` `BLOCKING=0 ... joins_needed=0`.
  `--force-reroute` of the named net printed `routed: 1`.
- **What was true:** `check_complete` `VERDICT: INCOMPLETE -- weird_copper: not clean` on **7 of the 12** full-chain
  route arms I ran (C2, F, I, J, R1, R2, S1; the other 5 were DONE). The items, from `check_weird`: redundant-cycle
  loop edges (`net 5v (F.Cu) ... loop edge (162.400, 92.550)-(162.018, 93.020); removal leaves connectivity
  identical` on R1 and S1 -- a 0.13 mm track to U7 pad 5 that a via sitting in that same pad already joins;
  FD6288_VS1 on F; FD6288_VS2 x2 on C), dangling ends (5v 0.283 mm on C, VDD 1.436 mm on J), and narrow-pad-joints
  (GND at C3.2 on I, FD6288_HO2 at R20.2 on J). The two best boards by vias (R1 and S1, 104 vias against 111+ for
  everything else) were both blocked only by the one 5v loop edge.
  - `--rip-existing-nets NET` on such a net does nothing (route.py warns the net is connected; correct, documented).
  - `--force-reroute` (`--nets NET GND`) fixed F's VS1 loop (111 -> 112 vias) and J's two items, but on R1 it
    **re-created the 5v loop** 0.25 mm away (`loop edge (162.150, 92.400)-(162.018, 93.020)`) at 107 vias, and on I it
    cannot touch the GND item at all (a zone-owning net is skipped; a `--nets GND` finalize re-run left it).
  - No repo tool removes a named segment: `check_weird.py` has no fix mode, `py_router/cleanup_pipeline.py` has no
    CLI. I wrote `helpers/drop_segment.py` (removes exactly one segment by net, layer and end points, refusing 0 or
    >1 matches) and removed the S1 loop edge; the board then grades DONE at 104 vias with check_weird, check_connected,
    check_drc, board_score, check_complete and KiCad's DRC all clean. That board is the one I ship.
- **Cost:** the largest of the run: about 25 min of force-reroute laps (F x2, J, R1 x2, I x2) plus the helper, and
  the plan needed a closing `route.py --nets GND` after the hand edit so Step 9's R04 ("the chain ends on route.py")
  still holds.
- **Repro:**
  ```
  python3 -X utf8 check_complete.py wk/gpm/15_am32_esc/repro/r1_iter2.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/repro/am32_esc_input.kicad_pcb
  python3 -X utf8 py_router/check_weird.py wk/gpm/15_am32_esc/repro/r1_iter2.kicad_pcb
  python3 -X utf8 py_router/route.py wk/gpm/15_am32_esc/repro/r1_iter2.kicad_pcb /tmp/r1_fix.kicad_pcb --nets 5v GND --force-reroute --power-nets GND VDD BAT+ BAT_IN+ FD6288_VS1 FD6288_VS2 FD6288_VS3 'Net-(U4-VOUT)' 5v 3.3v --power-nets-widths 0.5 2.0 2.0 2.0 2.0 2.0 2.0 0.7 0.7 0.3 --via-cost 300 --layer-costs 1.0 3.0 3.0 1.0 --grid-step 0.05
  python3 -X utf8 py_router/check_weird.py /tmp/r1_fix.kicad_pcb      # the loop is back
  ```
  (`repro/f_iter2.kicad_pcb` is arm F's board, the VS1 loop.)
- **Existing issues:** `"redundant-cycle"`, `"redundant copper loop"`, `"weird_copper check_complete"`,
  `"dangling-end route.py"`: none open for this case. Nearest, all CLOSED: #1063 (check_weird flags in-pad/in-via
  wiggles route.py's cleanup keeps, so no route.py output reaches DONE), #162 (same-net redundant copper: find the
  producers, remove delete-only), #1312 (the end-of-run strict collapse strips nothing on a pre-KiCad-10 board -- this
  board's file format is pre-KiCad-10: check_drc calls its 52 vias-in-paste "undeclarable in this file format").
  #1234 (OPEN) is micro-segment chains, a different shape.

## 2. fill_for_delivery turns a DONE KiCad-8 board into a blocking one: it re-saves as KiCad 10 and 52 accepted vias-in-paste become violations

- **Tool / command:** `py_tools/fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` (SKILL.md §3.9 step 2,
  the last step before the verifier), on a board whose input file is KiCad 8 (`(version 20240108)`).
- **What it claimed:** `Filled ... net classes preserved: 8 ... unconnected (no --refill-zones): 63 -> 0`, `EXIT=0`.
- **What was true:** the input to the fill graded `BLOCKING=0` and `check_complete` DONE, check_drc reporting
  `Vias in a solder-paste opening: 0 unprotected (violations) ... 52 undeclarable in this file format (accepted)`.
  The filled output is `(version 20260206)` (KiCad 10) and carries `(capping no) (filling no)` on every via, so the
  same 52 vias are now `52 unprotected (violations)`: grade.py `"done": false, "blocking": 52`
  (`drc_via_in_paste 52`), check_complete INCOMPLETE, and verifier call 1 FAILED on exactly that. Nothing stamped them:
  route.py's Type VII stamp (`fab_notes.via_protection_stamps`) is written only when the ROUTED file's format can carry
  it, and the fill neither stamps nor warns that its format change voids the "undeclarable" acceptance. The §3.9 text
  says only that the fill "copies the siblings and keeps the net classes".
- **Workaround:** run the route chain on the placement upgraded to KiCad 10 (`kicad-cli pcb upgrade` on a copy),
  so route.py stamps the vias it puts under solder (`54 stamped`) and the fill keeps them.
- **Cost:** about 20 min: one of the three verifier calls, a re-run of the whole route chain, the re-grade.
- **Repro:**
  ```
  python3 -X utf8 py_tools/board_score.py wk/gpm/15_am32_esc/repro/labelled_k8.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/repro/am32_esc_input.kicad_pcb --quiet
  python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/15_am32_esc/repro/labelled_k8.kicad_pcb -o /tmp/filled.kicad_pcb
  python3 -X utf8 py_tools/board_score.py /tmp/filled.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/repro/am32_esc_input.kicad_pcb --quiet
  ```
  (first `BLOCKING=0`, last `BLOCKING=52 (... drc_via_in_paste=52)`).
- **Existing issues:** `"fill_for_delivery via-in-paste"`, `"via in paste file format upgrade"`, `"undeclarable
  via"`, `"fill_for_delivery version"`: none. #1335 (CLOSED) added the delivery fill to the skills.

## 3. Nothing in the toolchain sees that the outline splits the board into two copper islands (check_reachability says PASSABLE)

- **Tool / command:** `py_tools/check_reachability.py`, `py_tools/check_assembly.py`, `py_tools/check_floorplan.py`,
  `py_placer/place_pose.py`, `py_tools/board_brief.py` (and so `place_simple`, which seats on the same legality).
- **What it claimed:** with R26 moved into the motor-mount section north of the mouse-bite row
  (`place_pose ... set R26 150 66 --rot 0`): place_pose `no_worse: true`; check_assembly `VERDICT: buildable`;
  check_floorplan (the given intent) `0 error(s)`; `check_reachability --pad R26.2`: `BOTTLENECK >= 69.21mm -- the
  path never approached foreign copper inside the view ... VERDICT PASSABLE at track 0.13mm (nothing is in the way)`.
- **What was true:** the outline's mouse-bite row at y=75 (0.6 mm holes on a 1.0 mm pitch, x 132.7-137.3 and
  162.7-167.3, the 137.5-162.5 x 70-75 cutout between) leaves webs of 0.2-0.4 mm, under twice the 0.2 mm board-edge
  clearance, so no copper crosses it. `route.py --nets CAN_SILENT` on that board: `ROUTE FAILED - no rippable
  blockers found`, `Single-ended: 0/1 routed (1 FAILED)`. board_brief reports `cutouts 26, milled contours 0` and
  nothing about islands. check_reachability is the instrument the skill names for an "impossible" claim (§5 rule
  4); here it certifies a route the outline forbids, because it does not model Edge.Cuts cutouts or edge clearance.
- **Cost:** about 15 min: found by reading the outline render, measured, then worked around with a keep-out row
  (`intent_run.json` `keepouts[motor-mount-section]`) so no seed could strand a group on the island.
- **Repro:**
  ```
  python3 -X utf8 py_tools/check_reachability.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb --pad R26.2
  python3 -X utf8 py_tools/check_assembly.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb --baseline wk/gpm/15_am32_esc/repro/am32_esc_input.kicad_pcb
  python3 -X utf8 py_tools/check_floorplan.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb --intent wk/gpm/15_am32_esc/intent.json
  python3 -X utf8 py_router/route.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb /tmp/x.kicad_pcb --nets CAN_SILENT
  ```
- **Existing issues:** `"check_reachability cutout"`, `"reachability outline edge cuts"`, `"mouse bite"`,
  `"outline island"`: none. Nearest: #628 (CLOSED: interior milled contours invisible to placement legality -- a pad
  inside a milled ring), a different case.

## 4. analyze_power_paths never traces the motor current through the FET bridge

- **Tool / command:** `py_tools/analyze_power_paths.py` (`trace_power_paths`, `get_power_net_recommendations`), the
  engine of `/analyze-power-nets`, which plan-pcb-routing Step 4 makes mandatory for the route step's widths.
- **What it claimed:** with J1 classified a 30 A POWER_SOURCE, the fuse R11, the shunt RSHUNT1 and all six AON7544 FETs
  30 A PASS_THROUGH and the phase pads J2 a 30 A CURRENT_SINK (as the skill's Step 3 asks), the traced paths reach the
  LDOs and logic loads only. Recommendations on the full classification: `VDD 0.7, BAT+ 0.5, BAT_IN+ 0.5`, and no entry
  at all for FD6288_VS1/2/3; only GND gets 3.0 mm (from the summed sink current).
- **What was true:** the 30 A path is J1 -> R11 -> BAT+ -> RSHUNT1 -> VDD -> Q1/Q3/Q5 -> FD6288_VS1/2/3 -> J2. The
  repro prints `paths reaching J2: []` and `phase nets recommended: NONE`. Silently wrong by more than an order of
  magnitude for the board's heaviest nets; I sized them by hand from the skill's IPC table (2.0 mm requested).
- **Cost:** about 10 min; read as written it would have routed the battery and motor rails at 0.5-0.7 mm.
- **Repro:** `python3 -X utf8 wk/gpm/15_am32_esc/repro/power_paths_repro.py`
- **Existing issues:** `"analyze_power_paths"`, `"power path trace FET"`, `"power nets motor"`: none (#91, CLOSED, is
  list_nets name detection).

## 5. No PDF reader on this machine: the skill's datasheet steps do not work as written

- **Tool / command:** SKILL.md §3.5 step 2 (`pdftotext -layout`, `pdftoppm -r 300`, `pdfimages -j`; "open it with
  the Read tool and `pages`"); WebFetch on the PDF.
- **What it claimed:** download the PDF and read it with the Read tool's `pages`, or with poppler.
- **What was true:** `which pdftotext pdftoppm pdfimages` finds none; the Read tool refuses a PDF page
  (`pdftoppm is not installed`); WebFetch returns `It's a raw PDF byte dump, not readable datasheet text`
  (FlateDecode streams); the venv has no PyMuPDF / pypdf. I wrote `helpers/pdfpages.swift` (Apple PDFKit: one PNG and
  one text file per page) to read the FD6288 datasheet. (The LCSC link returned an HTML page, not the PDF.)
- **Cost:** about 10 min.
- **Repro:** `which pdftotext pdftoppm pdfimages; python3 -c "import fitz"` (all fail); the Read tool on any PDF
  with `pages: "1-2"` (the FD6288 copy is in `wk/gpm/15_am32_esc/old/datasheets/fd6288q/`).
- **Existing issues:** `"pdftoppm poppler"`, `"datasheet PDF render"`: none.

## 6. place_pose reports `"legal": false` for every pose on this outline

- **Tool / command:** `py_placer/place_pose.py ... set REF X Y --rot R`.
- **What it claimed:** `"legal": false` on a no-op `set R4 162.7109 109.1375 --rot 180` of the kept, buildable board.
- **What was true:** nothing is illegal (check_assembly `buildable`, floorplan 0 errors); the flag is false only
  because `pad_edge_after.complete` is false -- all 304 pads `unmeasured`, reason `outline uses sampled perimeter
  check` (the outline has rounded slots and round cutouts). `legal_basis` discloses the conjunct, but a flag that can
  never be true on a board carries no information there.
- **Cost:** about 3 min (a no-op to tell it apart from a real defect).
- **Repro:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/15_am32_esc/repro/final_copy.kicad_pcb /tmp/noop.kicad_pcb set R4 162.7109 109.1375 --rot 180`
- **Existing issues:** `"place_pose legal sampled perimeter"`, `"sampled perimeter check"`: none.

## 7. No tool runs "this chain with one lever changed" as an arm (helpers/run_arm.sh, run_fix.sh, run_fixI.sh, run_v10.sh)

- **Tool / command:** the post-DONE optimisation the skill asks for (fewer vias, then copper), which needs the same
  chain re-run with one flag changed, each in its own recorded run dir so `final_route/` keeps the shipped chain.
- **What was true:** `tests/stress/ab_replay_grade.py` / `redo_diff_stage.py` replay RECORDED corpus manifests; none
  takes a plan and a flag to add. I wrote `helpers/run_arm.sh` (copy + route step + the 2 Step-2d iterations with the
  same flags, REDO_RUNDIR per arm, board_score + check_complete), two one-lap variants and `run_v10.sh` (the same chain
  on a KiCad-10-format copy, TOOL_GAPS 2). 16 arms ran through them.
- **Cost:** about 3 min.
- **Repro:** `bash wk/gpm/15_am32_esc/helpers/run_arm.sh arm_X --via-cost 300` (writes `wk/gpm/15_am32_esc/arm_X/`).
- **Existing issues:** `"replay chain one flag"`: none (#153, OPEN, a "tune" mode, is the nearest idea).

## 8. `kicad-cli` is not on PATH; the skill's §3.9 commands call it bare

- **Tool / command:** SKILL.md §3.9 step 1 (`kicad-cli pcb drc ...`).
- **What was true:** `which kicad-cli` finds nothing; the binary is
  `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` (KiCad 10.0.7), which I put on PATH for those calls.
  `tests/stress/kicad_drc_compare.py` found it on its own.
- **Cost:** about 1 min.
- **Repro:** `which kicad-cli`
- **Existing issues:** `"kicad-cli PATH"`: none.

## 9. route.py's clearance-descent record names fewer nets than the copper the lowered floor admits

- **Tool / command:** `py_router/route.py ... --escalation board` (the shipped chain's step 2): its
  `DEFAULT CLASS CLEARANCE LOWERED BY A DESCENT -- 0.13 -> 0.1075 mm: an automatic clearance descent on FD6288_HIN2,
  FD6288_VS1` line and `JSON_SUMMARY design_rules.narrowed` (2 nets, sites `fine-pitch plane tap`).
- **What was true:** the writeback lowers the whole Default class to 0.1075, and the shipped copper uses it on other
  nets the record never names. `check_drc --clearance 0.13 --clearance-margin 0` on the routed board: 7 items, e.g.
  `Via:FD6288_VS2 <-> Seg:FD6288_HIN1  Layer: B.Cu, Overlap: 0.020mm` at (152.95,116.20), three
  FD6288_LIN2/FD6288_LIN1 F.Cu pairs at 0.010 mm, `Via:COMP_INM_B <-> Seg:3.3v` at 0.005 mm. All legal at the written
  0.1075 floor, so every grader reads clean; but a reader of the disclosure would look at the wrong two nets. Found by
  the verifier (call 2), confirmed here.
- **Cost:** about 3 min.
- **Repro:** `python3 -X utf8 py_router/check_drc.py wk/gpm/15_am32_esc/repro/routed_v3.kicad_pcb --clearance 0.13 --clearance-margin 0`
  against `grep -A1 "DEFAULT CLASS CLEARANCE LOWERED" wk/gpm/15_am32_esc/final_route/plan_run.log`.
- **Existing issues:** `"clearance descent record nets"`: none open. Nearest: #1160 (CLOSED: one net's rescue
  lowers the Default class clearance in the project and later steps route every net there) -- the same mechanism;
  this entry is about the record not naming the nets that then use it.
