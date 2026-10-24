# gpm findings, verified (pin bda59fa0; main head 0c05be08)

Each cluster of `FINDINGS_CLUSTERED.md` (G01-G47) was re-run at the pin by a separate verifier (batches V1-V7, `_verify/`).
**41 clusters verified: 24 confirmed, 16 confirmed in part, 1 not a bug as claimed, 0 not reproducible.**
Six clusters equal gp14 issues already re-checked in Phase 4 and are not repeated here: G13 = #1318, G22 = #1343, G24 = #1359, G27 = #1349, G37 = #1311, G43 = #1320 (see `old_issues/OLD_ISSUES.md`).
Sixteen of the minor and environment items (M01-M16, `_verify/minor.md`) were verified the same way in batches V8-V9: **11 confirmed, 5 confirmed in part, 0 not a bug, 0 not reproducible.**
Boards 11 (daplink) and 12 (steppenprobe) were re-run after the start-state audit (`AUDIT.md`); the findings cite their first runs, whose files are in `wk/gpm/_superseded/`.

<!-- batch V1 -->
### G01 -- VERDICT: CONFIRMED
- title: fill_for_delivery re-saves a pre-KiCad-10 board in the KiCad 10 format with `(capping no)(filling no)` written on every via. Vias in paste that were accepted become blocking, and the repo's stamper will not fix them.
- boards: 04 07 10 13 14 15 17 19   severity: high
- repro at bda59fa0:
  - Board 04 (copy of `repro/gap1_routed_v9`, format 20241229, 47 vias):
    - `board_score --baseline` on the routed board: BLOCKING=0, `via_in_paste.undeclarable 20`.
    - After `fill_for_delivery`: the output is version 20260206 with 48 `(capping` tokens (47 vias plus setup). `board_score` gives BLOCKING=20, `drc_via_in_paste=20`.
    - The fill log only says "Filled / net classes preserved / unconnected 31 -> 0", EXIT=0.
  - Board 07 (copy of `repro/fill_routed_v9`): BLOCKING goes 0 -> 4.
  - `fab_notes.ship_via_protection_file` on the filled copy, with an empty snapshot and with the baseline's: 0 stamped, all 20 "own spec kept".
  - `kicad-cli pcb upgrade` on the routed copy writes the same 48 tokens and gives BLOCKING=20.
- cause (sure):
  - `py_router/kicad_exact_fill.py:86` (`pcbnew.SaveBoard` in `_REFILL_SCRIPT`), copied to the destination at :686, called from `py_tools/fill_for_delivery.py:134`.
  - The tokens pcbnew writes equal the new setup block (covering/plugging/capping/filling all `no`).
  - `py_router/fab_notes.py:285` (`if 'capping' in base or 'filling' in base`) treats them as a decision and never overrides them.
- head 0c05be08: unchanged (none of these files are in bda59fa0..upstream/main).
- upstream: new. Related: #1335 and #910 (the delivery fill), #992 and #1171 (Type VII stamping), #749. Not a duplicate.
- side notes:
  - board_score without `--baseline` keeps via-in-paste advisory, so the filled board reads BLOCKING=0. That is by design (#1171).
  - `fill_for_delivery.py:127` runs kicad-cli on the INPUT in place, which writes a `.kicad_prl` beside it.
- issue draft:
  **fill_for_delivery's KiCad 10 re-save turns accepted vias-in-paste into blocking violations, and the Type VII stamper cannot undo it**
  - On a pre-KiCad-10 routed board, `fill_for_delivery` saves through pcbnew as `(version 20260206)`. Every via gains `(capping no) (covering (front no)(back no)) (plugging ...) (filling no)`, the same values as the new setup block.
  - check_drc accepted those vias as "undeclarable in this file format". On the filled copy they read "unprotected (violations)".
  - Measured: board 04 BLOCKING 0 -> 20 (`drc_via_in_paste=20`); board 07 0 -> 4. The tool exits 0 and does not mention the format change.
  - `ship_via_protection_file` on the filled file stamps 0 of 20 ("own spec kept"), because pcbnew's explicit `no` reads as a decision (`fab_notes.py:285`). `kicad-cli pcb upgrade` does the same thing.
  - Repro (WT):
    1. `py_router/copy_board.py wk/gpm/04_multichannel_mixer/repro/gap1_routed_v9.kicad_pcb $T/in.kicad_pcb`
    2. `py_router/copy_board.py wk/gpm/04_multichannel_mixer/multichannel_mixer.kicad_pcb $T/base.kicad_pcb`
    3. `py_tools/board_score.py $T/in.kicad_pcb --baseline $T/base.kicad_pcb --quiet` -> BLOCKING=0
    4. `py_tools/fill_for_delivery.py $T/in.kicad_pcb -o $T/f.kicad_pcb; sed -n 2p $T/f.kicad_pcb` -> 20260206
    5. Same `board_score` on `$T/f.kicad_pcb` -> BLOCKING=20
  - Expected: keep the input's format, or strip the setup-equal protection tokens pcbnew added and then run `ship_via_protection_file` with the input's via snapshot. Print the version change, and refuse when the filled copy scores worse than its input.
  - Code: `kicad_exact_fill.py:86` / :686, `fill_for_delivery.py:134`, `fab_notes.py:285`.

### G19 -- VERDICT: CONFIRMED
- title: The DRC writeback lowers project floors that no shipped copper needed.
- boards: 10 12 14 17   severity: medium
- repro at bda59fa0 (all on copies under `G19/`):
  - **10:** `route_planes final --nets GND +3V3 --plane-layers In1.Cu In2.Cu --skip-existing-zones`. Both zones are kept, 0 vias and 0 tracks are drawn, zone blocks are unchanged. It still prints "Bare pour ... writing the copper clearance only (#1319)" and writes `net_class[Default].clearance 0.1499 -> 0.12`.
  - **17:** the same flag on `placed`. Every zone is kept at its own 0.25.
    - It prints "Zone clearance tightened 0.15 -> 0.119mm so the pour threads U6's via lattice".
    - U6 is `LGA-8_2.5x2.5mm_BME280` (8 pads) and the input has 0 vias.
    - It writes Default class, `min_clearance` and `min_hole_clearance` 0.15 -> 0.119.
  - **12:** `route_diff diff_in ... --escalation board`. Its own log says "Copper-to-hole 0.25mm for NPTH holes (from the board's own min_hole_clearance)", yet it writes `rules.min_hole_clearance 0.25 -> 0.15`. KiCad DRC of its output under the input project (0.25, refilled) finds 0 `hole_clearance`.
  - **14:**
    - `route_planes pile --nets GND --plane-layers In1.Cu --clearance-ceiling 0.1` writes `rules.min_clearance 0.1 -> 0.08`, taken from U2's footprint `(clearance 0.08)`.
    - `bga_fanout U1 --escalation board` on that output reports `board_floors.clearance 0.08` and runs "Under-pad shrink rescue @ clearance 0.0900mm ... BOARD's own declared minimums" (rescued 3 of 59). On the input there is no such rescue.
    - In this repro the shipped copper is identical (460 segments, 35 vias). The recorded chain `14_imx6ulz_4l/final_route_old3/s2_fanU1.log` shows the 0.09 rescues shipping.
- cause:
  - `route_planes.py:3346` resolves the zone clearance and records it in `clearance_ledger` (:2331) before the per-layer skip at :3416. `fix_kicad_drc_settings.py:2087` (`plane_fix_kwargs`) then always writes that clearance (sure).
  - `route_planes.py:2356` takes `find_components_by_type(pcb_data,'BGA')` as the via-lattice field set, so an LGA-8 counts (sure).
  - `route_diff.py:3057-3063` passes no `hole_clearance`, so `fix_kicad_drc_settings.py:1366-1370` sets `min_hole_clearance` to the copper clearance (sure).
  - `fab_tiers.py:238-257` (`board_floors_from_rules`) reads the `rules.min_clearance` that the #530 pad-override cap (`fix_kicad_drc_settings.py:1364`) wrote (sure).
- head 0c05be08: unchanged.
- upstream: incomplete fix of #1319. Its rule "copper clearance always written, because a refill regrows the pour" does not hold when no zone was created, and its copper-to-hole fix covered route_planes only. Related: #900, #530, #1160, #1285, #1329.
- issue draft:
  **The writeback lowers floors no shipped copper needed (#1319 follow-up): skip-existing pours, an LGA treated as a BGA lattice, route_diff's hole clearance, and a pad override read as the board floor**
  - `route_planes --skip-existing-zones` keeps every zone and draws nothing (board 10), yet writes Default 0.1499 -> 0.12. On board 17 it lowers Default, `min_clearance` and `min_hole_clearance` 0.15 -> 0.119 "for U6's via lattice". U6 is an 8-pad LGA on a board with 0 vias.
  - route_diff (board 12) holds NPTH at 0.25 itself but writes `min_hole_clearance 0.25 -> 0.15`. KiCad finds 0 hole_clearance errors on its copper at 0.25. The delivered fill then follows 0.15 (see G28).
  - The #530 cap writes U2's 0.08 pad override into `rules.min_clearance`. `--escalation board` then reads 0.08 as "the board's own declared minimum" and rescues U1 balls, which have no override, at 0.09.
  - Repro (WT):
    1. `copy_board wk/gpm/10_glasgow_revC/repro/final.kicad_pcb $T/in10.kicad_pcb`
    2. `route_planes.py $T/in10.kicad_pcb $T/o10.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu --skip-existing-zones | grep -E "Bare pour|net_class"`
    3. For 17: the same flag with `--nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu`.
  - Expected: a step writes only the floors its own drawn copper needs. No zone clearance is recorded for kept zones. A field must really be a ball grid. route_diff passes the hole clearance it held. A pad override never becomes a board floor for escalation.
  - Code: `route_planes.py:2331/2356/3346`, `fix_kicad_drc_settings.py:2087,1364,1366-1370`, `route_diff.py:3057`, `fab_tiers.py:238`.

### G28 -- VERDICT: CONFIRMED-PARTIAL
- title: check_complete `--authored-from` passes a lowered copper-to-hole floor.
- boards: 10 12   severity: medium
- repro at bda59fa0:
  - **12 (holds):** route_diff output from G19 (`min_hole_clearance` 0.15), filled with `fill_for_delivery`.
    - KiCad at 0.25 without refill: 12 `hole_clearance`, all `NPTH pad of H1..H4 <-> Zone [+3V3]/[GND]` at 0.1505 mm.
    - KiCad at 0.25 with `--refill-zones`: 0.
    - `check_complete fill12 --authored-from steppenprobe`: `fab_floors.measured_kept: min_hole_clearance violations 0`.
  - **10, copper-to-hole (holds, though not as the cluster describes):**
    - It is listed, then excused: "DECLARED, AND BROKEN BY THE REFERENCE TOO ... (this board 0.1402 over 199, the reference 0.0 over 199)".
    - The reference `fixed.kicad_pcb` / `glasgow_revC.kicad_pcb` is the unplaced pile (0 segments). Its 199 errors are pads stacked on J1's NPTH at 0.0. The delivered board's 199 are track-to-via at 0.14-0.24, a different population, and both counts sit at KiCad's 199-per-type cap.
    - Against the human-routed `_src/glasgow_revC` (4715 segments) the same check reports "copper-to-hole clearance 0.25 -> 0.1578" as relaxed (UNSOUND).
  - **10, class clearance (not a bug):** Default/Power 0.1499 -> 0.09 is not listed. The chain passed `--clearance-ceiling 0.09` (3 steps) and the project has no `class_clearance_relaxed` record. `check_complete.py:346-362` counts only automatic descents (#1160), by design.
- cause (sure):
  - `check_complete.py:188`: `kicad_hole_clearance` grades with `--refill-zones`, so the shipped fill is re-poured at the authored value. Result: `measured_kept` at :321.
  - `check_complete.py:329-334`: `reference_too` compares only `min_actual` (which is capped) and never the items themselves.
- head 0c05be08: unchanged.
- upstream: incomplete fix of #1198 (closed; its fix added both the refill grade and `reference_too`). Related: #1160.
- issue draft:
  **check_complete --authored-from passes a lowered copper-to-hole floor: the KiCad grade refills zones at the authored value, and `reference_too` compares a minimum against an unplaced pile**
  - A delivered fill poured at the lowered 0.15 sits 0.1505 mm from NPTH H1-H4: 12 KiCad `hole_clearance` errors without refill at the authored 0.25. check_complete re-grades with `--refill-zones`, sees 0, and records `measured_kept`.
  - On board 10, 199+ track-to-via errors at 0.14 are excused as `reference_too`, because the reference (the run's unplaced pile) has pads on holes at 0.0. That is a different set of items. Against the human-routed source the same board is UNSOUND (0.25 -> 0.1578).
  - Repro (WT):
    1. G19's route_diff output: `fill_for_delivery.py $T/rd12.kicad_pcb -o $T/f12.kicad_pcb`
    2. `check_complete.py $T/f12.kicad_pcb --authored-from <copy of 12_steppenprobe/steppenprobe.kicad_pcb> --json $T/c.json` -> `measured_kept`
    3. `kicad-cli pcb drc` on a copy of the project with `min_hole_clearance` 0.25, without `--refill-zones` -> 12
  - Expected: grade copper-to-hole on the fill as shipped. Excuse a floor only when the reference breaks it on the same items, or say the reference cannot be compared (a pile, or capped counts).
  - Code: `check_complete.py:188`, :321, :329-334.

### G04 -- VERDICT: CONFIRMED-PARTIAL
- title: check_complete without `--authored-from` says DONE and "nothing left to compare", although the project's own `fab_floor_origin` records the floor the copper breaks.
- boards: 04 11 16 (+10 authored UNSOUND)   severity: medium
- repro at bda59fa0 (board 16, the cluster's route.py command on a copy of `s8_diff`):
  - **Holds, ignored floor record:**
    - 2 IO0 vias ship at 0.25/0.15 against Board Setup 0.4/0.2.
    - The writeback sets `min_via_diameter 0.4 -> 0.25` and `min_via_drill 0.2 -> 0.15`. The output `.kicad_pro` still carries `fab_floor_origin.min_via_diameter 0.4`.
    - `board_score` bare: BLOCKING=0. With `--min-via-diameter 0.4 --min-via-drill 0.2 --min-track-width 0.127`: BLOCKING=4 (undersized 4).
    - `check_complete` bare: DONE, exit 0, `fab_floors {ran: false, reason: "no --authored-from: the chain rewrites the floors in place, so there is nothing left to compare against"}`. The UNEXAMINED list does not name it.
    - `--authored-from in16`: UNSOUND.
  - **Holds, escalation not needed:** the same command with `--fab-tier standard` gives BLOCKING=0 at the declared floors, 83 vias, IO0 vias 0.45/0.2.
  - **Not a bug:** descending below Board Setup minimums under the default `--escalation fab`, and the writeback lowering them, are documented design (CLAUDE.md, `routing_defaults.py:23-24`, #857, #1025 wontfix).
  - Board 04's oracle-via instance was not re-run (needs a full chain).
- cause (sure): `check_complete.py:237-240` returns `ran: False` without reading `fab_floor_origin`, and the verdict at :520-541 ignores `ran: False`. board_score takes its floors only from the board's current project.
- head 0c05be08: unchanged.
- upstream: new. Related: #857, #1025, #1198, #1160, #1287.
- issue draft:
  **check_complete (no --authored-from) says DONE on copper below the project's own recorded fab_floor_origin**
  - With the default auto/fab policy, route.py ships two IO0 vias at 0.25/0.15 on a 0.4/0.2 board and lowers the project's minimums. The project keeps `kicad_routing_tools.fab_floor_origin` = {min_via_diameter 0.4, min_through_hole_diameter 0.2, ...}.
  - Bare check_complete: DONE, exit 0. Its JSON claims "nothing left to compare against". board_score bare: 0; with the board's own spec: 4.
  - The same chain at `--fab-tier standard` completes at the declared floors (blocking 0, 83 vias).
  - Repro (WT):
    1. `copy_board wk/gpm/16_esp_rust_board/repro/s8_diff.kicad_pcb $T/in.kicad_pcb`
    2. `route.py $T/in.kicad_pcb $T/o.kicad_pcb` with the G04 cluster's flags
    3. `check_complete.py $T/o.kicad_pcb` -> DONE
    4. `board_score.py $T/o.kicad_pcb --min-via-diameter 0.4 --min-via-drill 0.2 --min-track-width 0.127 --quiet` -> BLOCKING=4
  - Expected: with no `--authored-from`, fall back to `fab_floor_origin`, or list fab_floors as UNEXAMINED instead of DONE. The skill should say that Board Setup minimums are the spec flags.
  - Code: `check_complete.py:237-240`, :520-541.

### G35 -- VERDICT: CONFIRMED
- title: The `design_rules` disclosure records attempts, not shipped copper.
- boards: 15 16 18   severity: medium
- repro at bda59fa0:
  - **16 route.py (the G04 run):**
    - Both sub-0.4 vias are on IO0 (net 6), from "Boxed endpoint unblocked by rung-0.25/0.15 via search" (log line 471).
    - `design_rules.nets [1,4,26,29]` holds track-width rows only. `min_delivered {track_width: 0.127}` has no via key.
    - The escalations are listed as `['net rescue net_1' x2]`, and that GND weld was "REJECTED".
    - So #1025's test ("reject if `min_delivered[k] < board_floors[k]`") passes this board.
  - **16 route_diff** (copy of `s11_pour`, `--via-size 0.45 --via-drill 0.2`): ships a USB_D- via at 0.25/0.15 at (149.8, 120.0). JSON_SUMMARY has no `design_rules` key and 0 "Design rules [" lines. Only the writeback's FAB FLOOR RELAXED mentions it.
  - **18 RF step:** 3 `via_diameter 0.45->0.25` rows on net 29 and 4 escalations (`plane tap U1.30` x2, last-resort via, net rescue). The output has 0 vias. U1.30 is the ANT signal pin, yet it is called a "plane tap".
  - **15:**
    - step2's record says "descent on FD6288_HIN2, FD6288_VS1" (clearance rows 0.1075/0.1225, site fine-pitch plane tap), and the Default class goes 0.13 -> 0.1075.
    - KiCad on step2 with Default 0.13: 0 clearance errors; check_drc `--clearance 0.13`: 0. The class was lowered for copper that did not ship.
    - The final `routed_v3` has KiCad 5 / check_drc 7 sub-0.13 items on other nets (LIN1/LIN2, VB3/LO1, 3.3v/COMP_INM_B, VS2/HIN1). Those came from later steps reading the lowered class, which is documented #1160 behaviour.
- cause:
  - `single_ended_routing.py:3256-3279`: the rung-1 search ships small vias without `note_narrowing` / `warn_fab_escalation` (sure).
  - `plane_pad_tap.py:77-101`, `net_rescue.py`, `single_ended_routing.py:2984` record per attempt. Only `track_width` rows are replaced by a census of the shipped copper (`fab_tiers.replace_track_rows`, #1033) (sure).
  - route_diff's via path: likely the same unrecorded rung path, not pinned to a line.
- head 0c05be08: unchanged (the `plane_pad_tap.py` and `phase3_routing.py` changes do not touch this code).
- upstream: new. Incomplete against #857's "every narrowing is recorded" contract. Related: #1033, #1160, #1025, #1318.
- issue draft:
  **design_rules lists narrowings that never shipped and misses one that did (rung-1 via search; route_diff)**
  - route.py on board 16 ships two IO0 vias at 0.25/0.15, placed by the rung-1 via search. `design_rules` names neither net nor via (`min_delivered` holds only `track_width`), and attributes both escalations to a GND rescue whose weld was rejected.
  - route_diff ships a USB_D- 0.25/0.15 via with no `design_rules` key at all.
  - Conversely, board 18's RF step lists 3 via narrowings and 4 escalations on a run that ships 0 vias, and calls the ANT pin a "plane tap".
  - Board 15's step lowers the Default class for a descent whose copper KiCad grades clean at 0.13.
  - Repro (WT):
    1. G04's route.py run, then `grep JSON_SHIPPED_RULES` and parse the vias below 0.4.
    2. `route.py wk/gpm/18_uecg/repro/final_route_in_ka.kicad_pcb $T/rf.kicad_pcb --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)' --impedance 50 --coplanar-gap 0.25 --layers F.Cu --clearance-ceiling 0.15 --via-size 0.45 --via-drill 0.3` (on a copy) -> via rows, 0 vias.
  - Expected: build the via and clearance rows (and the class writeback's descent record) from a census of the written copper against the requested sizes and board floors, as #1033 did for track width, in both route.py and route_diff.
  - Code: `single_ended_routing.py:3256-3279`, `plane_pad_tap.py:77-101`, `fab_tiers.py:821`.

Outputs are under `wk/gpm/_verify/V1/<Gnn>/`.

V1: CONFIRMED 3, PARTIAL 2, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V2 -->
The six clusters came out as 2 confirmed, 3 partly confirmed and 1 not a bug as claimed. I re-ran every one at bda59fa0. None of the code involved changed between bda59fa0 and 0c05be08. Outputs are under `wk/gpm/_verify/V2/<Gnn>/`. Every command below starts from `cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`, and kicad-cli was only ever run on copies made with `copy_board.py`.

### G02 -- VERDICT: CONFIRMED-PARTIAL
- **title:** route.py's end-of-run cleanup leaves dangling vias and redundant loops (a second identical run removes the loops), and no CLI deletes copper.
- **boards:** 07 08 10 11 12 13 14 15 19 20   **severity:** high
- **repro at bda59fa0:**
  - **11, fresh:** `route.py <copy of 11/repro/gap1_s1_diff> G02/r11/gap1_out.kicad_pcb` with the cluster's arguments. The run reports `failed 0`. check_weird finds `dangling-via 4`, and kicad-cli finds `via_dangling 4` (/OSCIN, /OSCOUT, /PA0, /TGT_SWDIO).
  - **07, fresh fixpoint test** (`G02/r07/run.sh`): the try4 '*' pass run twice with identical arguments. Pass 1 leaves 3 `redundant-cycle` loops (/SDA, /Solar+, /VOUT1). Pass 2 removes all 3.
  - **Stored boards, re-graded** (`G02/stored_check_weird.txt`): every finding is still there.
    - 08: a 0.25 mm In2 tail.
    - 14: a 1.27 mm +3V3 stub and a 4.96 mm VMEM tail.
    - 20 `stub_s10`: a 1.27 mm GND stub.
    - 12 `N2_s2a`: 4 dangling vias.
    - 12 `regrade_in` and 15 `r1_iter2`: 1 loop each.
  - **What does not hold:** 07's SW2 "free end" and 13's VBUS end are G23 misreads, not dead copper: their copper overlaps same-net copper by 0.077 and 0.112 mm.
  - **Not re-run:** 10 and 19.
- **cause:**
  - 11 (sure): `pcb_modification.py:2806`, the gate in `sweep_dangling_via_branches`.
    - Each via is the only thing joining two F.Cu ends 0.07 mm apart. Their 0.127 mm caps overlap.
    - The gate's grade (`:2712`) calls `_check_dangles` with join_tol 0, so dropping the via counts as "2 new dangling ends" and the removal is refused.
  - Loops (likely): the cycle prune runs once per call (`cleanup_pipeline.py:419`). Only late via (#1166) and stacked-copper (#162) sweeps run after the finalize and reconciliation.
  - Zone-owning nets are skipped by `--force-reroute` (`route.py:3042-3062`), by design.
- **head 0c05be08:** unchanged.
- **upstream:** incomplete fix of #1166 (the via gate). Related: #1063, #84, #162 (closed today), #1234 (open).
- **issue draft:**
  > **route.py ships dangling vias its #1166 sweep refuses to remove, and loops only a second identical run removes**
  > - daplink, fresh at bda59fa0: `python3 -X utf8 py_router/route.py wk/gpm/_superseded/11_daplink/repro/gap1_s1_diff.kicad_pcb OUT.kicad_pcb --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0`
  > - Result: `failed 0`, but check_weird `dangling-via 4` and KiCad `via_dangling 4`. These are the #535 via-in-pad unblock vias.
  > - Each via joins two F.Cu ends 0.07 mm apart, and their caps overlap. `sweep_dangling_via_branches` removes the via, grades the two ends as new dangling ends (`_check_dangles` with join_tol 0, pcb_modification.py:2712), and its gate refuses (`:2806`).
  > - One-Air-Max try4: the same '*' route.py twice. Pass 1 leaves 3 redundant-cycle loops; the identical pass 2 removes them. The cleanup does not reach a fixed point within one run.
  > - Stored boards also ship dead tails: CM5 0.25 mm, imx6ulz 1.27 and 4.96 mm, sam9g25 GND 1.27 mm.
  > - Expected:
  >   - weld two ends that met inside a removed via's barrel;
  >   - re-run the cycle prune after the late passes;
  >   - one recorded CLI that deletes named or flagged copper and re-verifies connectivity.

### G23 -- VERDICT: CONFIRMED-PARTIAL
- **title:** check_weird calls a track end "dangling" when its copper overlaps the end cap of same-net copper.
- **boards:** 07 09 13 (16 is not a bug; 08 not separated)   **severity:** medium
- **repro at bda59fa0:**
  - `check_weird.py wk/gpm/09_StickHub/repro/soft_joint.kicad_pcb` reports `dangling-end 1` (+3.3V at 143.2,95.9; caps overlap 0.045 mm). The same report says `kicad-dangling 0`.
  - check_orphan_stubs is clean on that board, and kicad-cli on a copy flags no +3.3V track.
  - 13 `routed`: the VBUS end at (72.9,124.525) sits inside a 0.7 mm track's end cap (overlap 0.112 mm), and KiCad has no VBUS track_dangling. The classifier is `G23/classify_dangles.py`.
  - Of the delivered boards, only 13 still ships one. The others were hand-fixed.
  - **Not a bug:** 16's USB_D- 0.0415 mm edge overlap. KiCad reports it connected with no connection_width issue, and the fused contact is about 0.21 mm long, wider than the 0.127 mm track.
- **cause (sure):**
  - `check_weird.py` credits same-net track copper only three ways: an exact vertex (`:208`), an interior T (`_point_anchored`, `pcb_modification.py:84-96`), or an end-to-end gap of at most 0.1 mm (`:356`).
  - The soft-joint pass pairs only two unanchored ends (`:221`, `:244`) and drops pairs that are joined elsewhere (#984).
  - So an end that overlaps an anchored or already-joined partner's end cap falls through both checks.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #722, #695, #984, and #1167 (the same credit, already fixed in check_orphan_stubs).
- **issue draft:**
  > **check_weird reports a dangling end where the track's copper overlaps another same-net track's end (KiCad and check_orphan_stubs say connected)**
  > - `python3 -X utf8 py_router/check_weird.py wk/gpm/09_StickHub/repro/soft_joint.kicad_pcb` gives `dangling-end 1` (+3.3V B.Cu 143.2,95.9): a 0.25 mm track end 0.33 mm from a 0.5 mm track's end, caps overlapping 0.045 mm.
  > - The same report has `kicad-dangling 0`. check_orphan_stubs is clean, and kicad-cli flags no +3.3V track.
  > - pico_ice routed.kicad_pcb: VBUS (72.9,124.525) lies inside a 0.7 mm track's end cap (0.112 mm overlap). Deleting the "dangling" segments split VBUS (blocking 3→5).
  > - check_complete fails `weird_copper` on both boards.
  > - Cause: `_check_dangles` credits track copper only by vertex, interior T or a gap of at most 0.1 mm (check_weird.py:332-375). The soft-joint pass pairs only two unanchored ends (`:221`, `:244`).
  > - Expected: an end whose cap overlaps same-net track copper on its layer counts as anchored, as check_orphan_stubs has done since #1167. If it is fragile, report it as `soft-joint`.

### G30 -- VERDICT: CONFIRMED
- **title:** check_weird and check_orphan_stubs are clean on delivered boards where KiCad reports track_dangling.
- **boards:** 10 20   **severity:** medium
- **repro at bda59fa0:**
  - kicad-cli on copies of the delivered boards: 10 gives `track_dangling 3` (+3V3, QA6, Z0_N). 20 gives 8 on the stored fill and 1 with `--refill-zones` (VBUS).
  - check_weird and check_orphan_stubs: clean on both.
  - kicad_drc_compare, check_complete and board_score never read `track_dangling`.
- **cause (sure), three mechanisms:**
  1. **Track-only shape skipped.** `check_weird.py:562`, the #1217 model only reports a segment when every track touching it touches both its ends. 10's +3V3 and 20's VBUS T-stubs also have a vertex neighbour, so they are skipped.
     - A sketch that counts one-end touchers (`G30/general_rule.py`) catches 2 of 10's 3 and 8 of 13's KiCad hits, with no false positives.
  2. **Short tails allowed.** `check_weird.py:418` and `check_orphan_stubs.py:197` accept a tail up to 3× the track width past a body anchor. QA6's 0.32 mm and Z0_N's 0.24 mm tails pass that allowance, and KiCad flags both.
  3. **Zone credited by outline.** `check_weird.py:349` credits the zone outline, not the fill. The 7 GND stubs on 20 end in hatch gaps of the stored fill.
- **head 0c05be08:** unchanged.
- **upstream:** incomplete fix of #1217 (mechanism 1). Mechanisms 2 and 3 are new. Related: #1291, #1167.
- **issue draft:**
  > **KiCad track_dangling on delivered boards that check_weird and check_orphan_stubs call clean**
  > - glasgow delivered: KiCad 10 gives 3 track_dangling. sam9g25 delivered: 8 on the stored fill, 1 after refill. Both repo checkers are clean.
  > - Repro: copy with `py_router/copy_board.py`, then `kicad-cli pcb drc <copy> --severity-all --format json -o a.json` and count `track_dangling`.
  > - (a) +3V3 (74.2,112.6) and sam9g25 VBUS (110.1,77.3): stubs whose start lies mid-body on a track that also touches the far end. `kicad_dangling_end` abstains because a vertex neighbour touches one end only (check_weird.py:562).
  > - (b) QA6 and Z0_N: tails of 0.32 and 0.24 mm past a T or via anchor, under the 3× width allowance (check_weird.py:418, check_orphan_stubs.py:197).
  > - (c) 7 GND stubs ending in hatch gaps of the stored fill. The zone credit is the outline (`:349`).
  > - Expected:
  >   - count a one-end toucher for its own end;
  >   - flag any tail KiCad would flag;
  >   - credit zones by the stored fill;
  >   - surface `track_dangling` in kicad_drc_compare.

### G31 -- VERDICT: NOT A BUG (as claimed). The real defect runs the other way.
- **title:** check_cycles counts sub-0.02 mm segments and collinear overlaps as loops. None of its 37 loops on these boards encloses area.
- **boards:** 04 16 17   **severity:** low
- **repro at bda59fa0:** the counts reproduce: 16 delivered 19, 17 delivered 13, 04 repro 2, 17 repro 1. Classifying each loop (`G31/classify_cycles.py`):
  - 27 are self-loops: segments under 0.02 mm in both axes (max 0.0236 mm) that the 0.02 mm tolerance collapses to a single node.
  - 6 are zero-area folds spanning at most 0.3 mm, where every segment is removable.
  - 3 are not loops at all: collinear overlaps where deleting either segment splits the net.
  - check_weird's `redundant-cycle` is 0 even at `--tolerance 0 --thorough`.
  - So check_complete is right not to fail these boards. The skill's plan check (`route_plan_check.py:77`) still sends agents to check_cycles.
- **cause (sure):**
  - `py_tools/check_cycles.py:79-81` clusters ports with a per-axis 0.02 mm tolerance, so a segment shorter than that becomes an edge with E+1 and V+0.
  - `:108-118` splits two collinear overlapping segments on each other, which forms a 2-cycle.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #811, #1234, #606.
- **issue draft (re-scoped):**
  > **check_cycles reports zero-area "loops" (sub-tolerance segments, collinear overlaps), and the routing plan check names it as a DONE condition**
  > - `python3 -X utf8 py_tools/check_cycles.py wk/gpm/16_esp_rust_board/delivered.kicad_pcb` gives 19 loops.
  > - 14 are single segments of 0.012-0.024 mm. Their two ports merge under TOL 0.02 (check_cycles.py:79-81).
  > - 2 are collinear overlap joints where deleting either segment disconnects the net (`:108-118`).
  > - environment_sensor delivered: all 13 loops are segments shorter than 0.017 mm.
  > - check_weird `redundant-cycle` is 0 on the same boards.
  > - Expected:
  >   - count a cycle only if every edge in it can be deleted with connectivity unchanged;
  >   - ignore segments shorter than the tolerance;
  >   - or drop check_cycles from the "no redundant copper loop" row of route_plan_check.py and point it at check_weird.

### G26 -- VERDICT: CONFIRMED
- **title:** route.py writes a tracks_crossing short between different nets (RMII-TX0 / VDD-IO) and reports `failed 0`.
- **boards:** 20   **severity:** high
- **repro at bda59fa0:** `route.py <copy of 20/repro/short_s6>` with the cluster's arguments (`G26/`), about 2 min.
  - The run reports `failed 0`.
  - check_drc: 5 violations, including a SEGMENT-CROSSING at (141.150,91.850).
  - kicad-cli: `tracks_crossing` plus a clearance error (0.0398 mm) between RMII-TX0 and VDD-IO.
  - Identical to the teammate's 3 runs.
- **cause:**
  - The producer (sure): route-trace event 240 is VDD-IO's multipoint Phase-3 tap edge [55/116]. Its 278-segment path starts at the #535 via-in-pad unblock via (139.05,85.7) and makes a roughly 14 mm U-turn back to a pad 1 mm away, through RMII-TX0's track. That track was laid at event 95 and never deleted.
  - Location: the retry search at `single_ended_routing.py:3334` (the "Via-in-pad unblock: dropped 1 fab-floor via(s)" line).
  - Why RMII-TX0 is passable in that search is not isolated. It is not the allowed rect, which only lifts BGA-zone blocking.
  - route.py runs no different-net crossing audit before writing.
  - The cluster's "poured-net reconnect" label is wrong: the path comes from a Phase-3 tap edge, not a reconnect.
- **head 0c05be08:** unchanged (848cb2ca touches the seam re-ask only).
- **upstream:** new. Related: #238, #673, #805, #1228.
- **issue draft:**
  > **route.py ships a different-net tracks_crossing (sam9g25 RMII-TX0 × VDD-IO) and reports failed 0**
  > - `python3 -X utf8 py_router/route.py wk/gpm/20_sam9g25/repro/short_s6.kicad_pcb OUT.kicad_pcb --nets '*' --no-bga-zones --clearance-ceiling 0.1016 --track-width 0.1016 --via-size 0.45 --via-drill 0.3 --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2`
  > - `JSON_SUMMARY_MIN failed 0`. check_drc: SEGMENT-CROSSING at (141.15,91.85). KiCad: tracks_crossing plus clearance 0.0398 mm. Deterministic over 4 runs.
  > - The trace (`KICAD_ROUTE_TRACE=1`): VDD-IO tap edge [55/116] fails, the #535 unblock drops a 0.3/0.15 via, and the retry (single_ended_routing.py:3334) lays a 278-segment detour through RMII-TX0's committed track.
  > - Expected:
  >   - the unblock retry respects in-run foreign copper;
  >   - before writing, route.py audits same-layer different-net crossings and rips or refuses them.

### G25 -- VERDICT: CONFIRMED-PARTIAL
- **title:** route.py's final re-grade disagrees with exact-fill connectivity in both directions, and the plane repair prints "confirmed connected by the oracle" for an open pad.
- **boards:** 09 12   **severity:** medium
- **repro at bda59fa0:**
  - **09, from stored artifacts** (`repro/gnd_verdict*` = `final_route_old3/s2_route.*`, same sha):
    - The log shows the oracle's forced GND link landed, and `JSON_REGRADE` lists GND under `recovered`.
    - The board measured now: board_score GND broken with 5 joins (blocking 7), check_connected 6 components, and route.py's own `_exact_open_grades` gives 45 pads off across 5 exact-fill clusters.
    - Two fresh re-runs (`G25/r09`, `G25/r09old3`) took a different oracle path: the leftover link was zero-length and was dropped. On those runs the #1339 re-grade fired correctly (GND open, 45 pads).
  - **12(a), fresh** (`G25/r12a`):
    - route.py says `failed 1` (+3V3 in pad_pairs_open).
    - Its own oracle says `remaining 0`, and its plane repair prints "U1.20 CONNECTED per KiCad's exact fill".
    - check_connected says all nets connected after KiCad's refill, and board_score gives blocking 0. So the `failed 1` is false.
  - **12(b), fresh** (`G25/r12b`): the final verdict is right (`failed 1`, +3V3, matching check_connected). Only the plane repair's console line "Pads still unconnected: none (... confirmed connected by the oracle)" is false. It sits next to JSON_ORACLE `remaining 1` for +3V3.
- **cause (sure):**
  - 09: `route.py:8012-8015` drops a net from the #1339 exact-fill re-grade as soon as any one of its forced links lands (keyed by net name), without re-checking the exact fill.
  - 12(a): `_regrade_pour_fill` skips KiCad's refill whenever the oracle ran (`route.py:458`). `_exact_open_grades` only re-grades nets the model calls connected (`:715-719`), so a model-only false open stands.
  - 12(b): `repair_planes.py:3221-3226` counts a pad as open only if an oracle link endpoint lies within 0.1 mm of the pad's centre. KiCad anchors the island's link elsewhere, so the open pad is missed.
- **head 0c05be08:** unchanged. 6027937e touches the oracle's via spacing only.
- **upstream:** incomplete fix of #1339 (09). 12(a) and 12(b) are new. Related: #572.
- **issue draft:**
  > **route.py's final re-grade: a landed forced link exempts the whole net from the #1339 exact-fill check; a model-only open is never cleared; "confirmed by the oracle" is a centre-distance match**
  > - StickHub (`wk/gpm/09_StickHub/final_route_old3/s2_route.log` and its board): the forced GND oracle link lands, `JSON_REGRADE` puts GND in `recovered`, and the written board has GND in 5 exact-fill pad clusters (45 pads off, board_score 5 joins).
  > - Cause: route.py:8012-8015 removes a net from `_pending_links1339` when any one of its links lands.
  > - steppenprobe: `python3 -X utf8 py_router/route.py wk/gpm/_superseded/12_steppenprobe/repro/regrade_in.kicad_pcb OUT.kicad_pcb --nets +1V8 GND +3V3 --force-reroute --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1`
  >   - Result: `failed 1` (+3V3), while oracle `remaining 0` and check_connected says all connected after KiCad's refill.
  >   - Cause: the refill is skipped when the oracle ran (`:458`), and `_exact_open_grades` only re-grades model-connected nets (`:715-719`).
  > - Also: P2_p2 prints "confirmed connected by the oracle" for U1.20 while the oracle leaves its link open (repair_planes.py:3221-3226).
  > - Expected: re-grade every pour net the run touched on the exact fill, in both directions, and match oracle links by island, not by pad centre.

V2: CONFIRMED 2, PARTIAL 3, NOT A BUG 1, NOT REPRODUCIBLE 0

<!-- batch V3 -->
### G03 -- VERDICT: CONFIRMED
- title: analyze_power_paths charges a part's whole current once per power pad, and adds a source's rating on top of the sinks it feeds
- boards: 06 08 09 11 12 13 17   severity: high
- repro at bda59fa0: the cluster's daplink one-liner gives `{'+3.3V': 1.0, 'GND': 2.0, '+5V': 0.7}`. I wrote `wk/gpm/_verify/V3/G03/measure_net_currents.py`, which reads each net's summed current through the public API (it bisects `min_current_ma`) and breaks it down by part:
  - **11 daplink:** +3.3V is 550 mA = U1 AMS1117 300 (source, VO pin) + U2 STM32 50 × 5 pads. GND is 2500 mA = P1 500 × 4 + U1 300 + U2 50 × 4. The only sink is 50 mA.
  - **09 StickHub:** +3.3V is 1169 mA = 167 × 7 pads, so 1.2 mm. Counted once it is 167 mA, so 0.7 mm.
  - **12 steppenprobe:** U1 FT2232HL 70 mA × 19 pads (4 on +1V8, 5 on +3V3, 9 on GND, 1 on /VPHY). +3V3 is 1020 mA, including U2's 200 mA source rating.
  - **06 rp2350:** +3V3 is 1020 mA, so 1.2 mm; the sinks counted once give 240 mA. Net-(U6-VREG_AVDD) gets all 150 mA of U6.
  - **08 and 17:** their recommendation outputs reproduce.
  - **Corrections to two instances:** 06's "ten pins / 1.5 A" is really 5 counted pins / 750 mA, because the passive `IOVDD_*` pins are dropped. 11's "8 GND pads / 4 A" is really 4 pads / 2000 mA, because SHIELD is dropped. Both boards still land on the claimed widths.
  - **Ground nets:** every net whose name contains GND is also given the board's total sink current. On icebreaker, `/ET_GND` and `/EB_GND` each read 570 mA (1.0 mm) although no part has a power pin on them.
- cause: `py_tools/analyze_power_paths.py:418-439` (the per-pad `+= current` loop, for sinks and sources alike) and `:481-486` (every GND-named net set to `max(net, total_sink)`). Sure.
- head 0c05be08: unchanged. The diff touches neither analyze_power_paths.py nor net_queries.py, and no test covers the module.
- upstream: new. #124 (closed, wontfix) is the opposite complaint; #489 §6 and #705 touched this module for other reasons.
- issue draft:
  **analyze_power_paths: get_power_net_recommendations sizes a net by part current × power-pad count, plus the source's rating (widths 2-7x)**
  The skill says a sink's `current_rating_ma` is its total supply current ("For ICs: Total supply current"). Its own example sizes +3.3V as "U102 200mA + U301 150mA", once per part. The code instead adds the rating once per power pad, and adds a source's rating to the same nets on top of that.
  - Measured at bda59fa0 by bisecting `min_current_ma`: daplink +3.3V is 550 mA (AMS1117 300 + STM32 50 × 5 pads) and GND is 2500 mA (USB-C 500 × 4 + 300 + 50 × 4). That gives 1.0 mm and 2.0 mm for a 50 mA load.
  - StickHub +3.3V is 167 × 7 = 1169 mA (1.2 mm) on a 100 mA LDO rail.
  - steppenprobe's FT2232HL is charged 70 mA × 19 pads.
  - Every GND-named net is also given the board's total sink current: icebreaker's isolated `/ET_GND` and `/EB_GND` read 570 mA with no load on them.
  - Repro: `python3 -X utf8 -c "import sys;sys.path[:0]=['py_tools','py_router'];from analyze_power_paths import *;c,p=analyze_pcb('wk/gpm/_superseded/11_daplink/repro/gap2_pile.kicad_pcb');classify_component(c,'P1',ComponentRole.POWER_SOURCE,current_rating_ma=500);classify_component(c,'U1',ComponentRole.POWER_SOURCE,current_rating_ma=300);classify_component(c,'U2',ComponentRole.CURRENT_SINK,current_rating_ma=50);print(get_power_net_recommendations(p,c,trace_power_paths(p,c)))"`. It gives GND 2.0 and +3.3V 1.0.
  - Expected:
    - charge each part once per supply net;
    - never add a source's rating to the sinks it feeds, since a rating is a limit, not a load;
    - size each ground from the sinks on that ground, once;
    - add a multi-pin IC test, because no test covers this module today.
  - Code: `py_tools/analyze_power_paths.py:418-439` and `:481-486`.
  - Seven boards were hit, and every agent overrode the widths by hand.

### G07 -- VERDICT: CONFIRMED
- title: analyze_power_paths ignores the classification unless pins are typed power_in/power_out; 3-terminal pass-throughs never conduct; no warning
- boards: 01 07 09 15 19 20   severity: high
- repro at bda59fa0:
  - **01 ecc83:** `analyze_power_heater.py` gives `paths: []` and `{'GND': 0.7}`, with `Net-(P4-P1)` and `Net-(P4-PM)` missing. The heater pins are typed `input` (F1/F2) and P4's pins `passive`.
  - **15 am32:** no path reaches J2 and no phase net is recommended. J2's pins are passive. Q1 (AON7544) has three nets (S/G/D), so it never gets an adjacency.
  - **19 icebreaker:** 0 paths, and +5V/+3V3 are absent. U2's pads carry no pintype and no pinfunction.
  - **20 sam9g25:** 0 paths, and VIN/VBUS are absent.
  - **09 StickHub:** 0 paths. The load switch U2 classified as PASS_THROUGH has 4 nets, and the VBUS pins are passive (`is_power_pin('VBUS','passive')` is False).
  - **07 One-Air-Max:** 0 paths and +5V absent are reproduced. The claim "no +3V3 entry" is not: the cited one-liner gives +3V3 0.7, from VDD-named pins.
- cause: `py_tools/analyze_power_paths.py`:
  - `:302-313`: sinks come only from `pintype == 'power_in'`;
  - `:315-332`: sources come only from power_out or OUT/VOUT-named pins, or from every net of a J/P/TB part;
  - `:252`: a pass-through conducts only with exactly 2 net entries;
  - `:418-439`, via `py_router/net_queries.py:1543-1608`: only pintype power_in/out or a VCC/VDD/VSS/GND-prefix pinfunction counts, so VBUS, IOVDD_*, F1 and Pin_1 drop.
  - Nothing warns when a classified part contributes nothing.
  Sure.
- head 0c05be08: unchanged
- upstream: new (#124 is the nearest; it is unrelated)
- issue draft:
  **analyze_power_paths: classified sources and sinks never reach a net unless their pins are typed power_in/power_out, and FETs or load switches never pass current**
  Step 3d tells the agent to classify parts, but `trace_power_paths` does not use those roles to find path ends.
  - ecc83: P4 is classified POWER_SOURCE 300 mA and the ECC83 CURRENT_SINK 300 mA. The result is `paths=[]` and `{'GND': 0.7}`; the 300 mA heater nets are missing.
  - am32: a 30 A J1 → fuse → shunt → FETs → J2 chain is classified as the skill asks, yet no path reaches J2 and FD6288_VS1/2/3 get no width.
  - icebreaker and sam9g25: 0 paths, so the input rails (+5V/+3V3, VIN/VBUS) get nothing.
  - The report still lists the classified sink and prints no warning.
  - Repro: `python3 -X utf8 wk/gpm/01_ecc83-pp_v2/repro/analyze_power_heater.py` and `python3 -X utf8 wk/gpm/15_am32_esc/repro/power_paths_repro.py`.
  - Causes: sink nets need `pintype=='power_in'` (`:302-313`). Sources need power_out or OUT-named pins (`:315-332`). A PASS_THROUGH conducts only with exactly 2 net entries (`:252`), which excludes every FET and load switch. The direct-pin loop drops passive pins that are not VCC/VDD/GND-prefixed (`:418-439`).
  - Expected:
    - a classified part's supply pads act as sink or source pins whatever their pintype;
    - a 3-terminal pass-through conducts between its power nets;
    - warn when a classified part ends up on no net.

### G33 -- VERDICT: CONFIRMED
- title: trace_power_paths keeps one sink per net, so every other sink on a rail is dropped from path tracing
- boards: 02 16   severity: low
- repro at bda59fa0:
  - **02 sonde:** U1 and U2 (74LS125, both with power_in VCC) give 1 path, J2→U1 22 mA. The bisect puts /PWR_3,3-5V at 22 mA instead of 44.
  - **16 esp_rust:** +3V3 has power_in pads on D9, U1, U2, U3 and U4, yet there is 1 path (U5→D9 60 mA via L1). /Buck_Coil gets 60 mA from paths instead of 710.
  - Widths do not move on either board: G03's source-on-top count hides it (02 stays under the 50 mA threshold; 16's /Buck_Coil is 1.0 mm either way).
- cause: `py_tools/analyze_power_paths.py:303` (`sink_nets: Dict[int, str]`) and `:312` (the last writer wins). `source_nets` has the same shape (`:316`, `:328`, `:331`). Sure.
- head 0c05be08: unchanged
- upstream: new. It should be fixed together with G34: switching to a list of sinks without G34's one-path-per-sink fix would multiply the overlapping paths.
- issue draft:
  **trace_power_paths: sink_nets maps net → one sink, so a rail feeding several loads through a fuse, diode or ferrite is traced for one load only**
  - sonde_xilinx: two 22 mA ICs on VCC behind D2 give one path, so the input net carries 22 mA instead of 44.
  - esp_rust_board: five sinks on +3V3 give one path (a 60 mA LED), and the 350 mA module is never traced.
  - Repro: the one-liner in `wk/gpm/16_esp_rust_board/TOOL_GAPS.md` §5 prints one path, U5→D9.
  - Code: `py_tools/analyze_power_paths.py:303,312`; `source_nets` at `:316-331` overwrites the same way.
  - Expected: one path per sink, as `Dict[int, List[str]]` plus G34's directed tracing. No width changed on these two boards because G03 hides it, so low.

### G34 -- VERDICT: CONFIRMED
- title: trace_power_paths walks regulators both ways, credits every reachable source, skips the sink's own regulator, and sums the overlapping paths
- boards: 08 10 13 14 17   severity: medium
- repro at bda59fa0: I wrote `wk/gpm/_verify/V3/G34/paths_audit.py` to check every traced path.
  - **10 glasgow:** all 10 of 10 paths are wrong. U30 sits on +1V2, the output of U36, but is credited to U14, U31 and U8 via +1V2 → +5V → each sibling regulator's output. U36 itself is never credited. U7 on +5V is credited to all four regulators whose input is +5V.
  - **13 pico_ice:** 23 paths for 3 sinks; U6 (50 mA) is traced 15 times. Paths alone put 860 mA on +3V3 and 695 mA on VBUS, against 240 mA of declared sinks.
  - **14 imx6:** U1 (650 mA) is traced 12 times, and the paths put 9 × 650 on +5V, so 3.0 mm.
  - **08 CM5:** "U702 → Module301, nets +5V → M2_LX" is reproduced; U702 is a buck fed by +5V.
  - **17:** the GND → GNDREF path through FB1 is reproduced.
- cause: `py_tools/analyze_power_paths.py`:
  - `:291-300`: regulator out↔in adjacency is added in both directions;
  - `:342-375`: the BFS records a path at every source net it reaches and keeps expanding past it;
  - `:343`: `net_id != sink_net_id` skips the regulator on the sink's own rail;
  - `:329-331`: every net of a J/P/TB source counts as a source, GND and data nets included;
  - `:399-403`: all paths are summed.
  Sure.
- head 0c05be08: unchanged
- upstream: new
- issue draft:
  **trace_power_paths: regulators are traversed in both directions and every reachable source becomes a path, so loads are credited to the wrong regulators many times over**
  - glasgow_revC: all 10 traced paths are wrong. The 1V2 load U30 is credited to the 3V3 and bank LDOs through their shared +5V input. Its real LDO U36 is never credited, because a source on the sink's own net is skipped.
  - pico_ice: one 50 mA sink is traced 15 times; +3V3 gets 860 mA from paths for 240 mA of loads.
  - imx6ulz: the 650 mA SoC is traced 12 times; +5V reaches 3.0 mm.
  - Repro: `python3 -X utf8 wk/gpm/10_glasgow_revC/repro/power_paths_repro.py`, or my audit script `wk/gpm/_verify/V3/G34/paths_audit.py`.
  - Code: `:291-300` (both directions), `:342-375` (no stop at the first source), `:343` (own-rail source skipped), `:399-403` (sum).
  - Expected: a directed source → output net → sink graph that never enters a regulator from its input; stop at the first source; one path per sink.

### G14 -- VERDICT: CONFIRMED-PARTIAL
- title: requested power widths and a board's power netclass widths reach no grader, and the skills disagree on whether they are a spec
- boards: 09 12 18   severity: medium
- repro at bda59fa0:
  - **18 uecg:** `board_score delivered_copy --quiet` gives BLOCKING=0 with net_widths UNGRADED (exit 0), and `check_complete` gives DONE. With `--net-min-widths wk/gpm/18_uecg/power_widths.json` it gives BLOCKING=7, net_widths=7, exit 4. For example, Net-(F1-Pad1) has 30.30 of 42.11 mm under 0.65 mm (narrowest 0.127), and GND has 79.25 of 163.5 mm under 0.2.
  - The delivered `.kicad_pro` records `net_impedance` but no width record.
  - **12 steppenprobe:** the board's `.kicad_pro` declares a Power class (track_width 0.3 on 8 nets). Arms A and B score BLOCKING 0, and 5 and 4 when that class is passed as a widths file.
  - **What holds:** there is no channel that carries the widths to the graders, and the skills contradict each other.
  - **What does not hold:** the "false-OK" label. check_complete's DONE line names net_widths as UNEXAMINED, by design (`check_complete.py:39-41`).
- cause:
  - `py_tools/board_score.py:1101-1102`: skipped without a file.
  - `py_router/route.py:8313-8408`: `power_widths` is measured into the JSON summary only.
  - `py_router/tool_records.py`: has no width key.
  - Skill text: `plan-pcb-routing/SKILL.md:582-585` says net-class track_width is "not DRC floors -- just defaults". Against that, `plan-pcb-placement/references/verifier.md:38-40` FAILs a declared power-width class left ungraded, `SKILL.md:45-48` says "every spec the board declares", and `SKILL.md:931-933` says "Widths are requests ... grade power widths with board_score --net-min-widths".
  Sure.
- head 0c05be08: unchanged (no skill, board_score, check_complete or route.py change)
- upstream: new; related #1237 (open audit design that reads netclasses), #1033, #1318
- issue draft:
  **The power widths route.py is asked for, and a board's own Power netclass widths, reach no DONE grader; the routing and placement skills disagree on whether they are a spec**
  - uecg: the delivered board scores BLOCKING=0 and check_complete says DONE. The same board graded at its requested widths scores BLOCKING=7 (battery path Net-(F1-Pad1) is 72% under width, narrowest 0.127 mm).
  - steppenprobe: the board declares a Power class at 0.3 mm on 8 nets. Arms graded as shipped score 0; graded at the class they score 5 and 4.
  - route.py measures `power_widths` in JSON_SUMMARY and records `net_impedance` in the `.kicad_pro`, but records no widths. So a later grader can only see widths through a hand-written `--net-min-widths` file.
  - The skills disagree: plan-pcb-routing Step 4 calls net-class widths defaults, not floors, while the placement verifier (rule 5) FAILs a declared power-width class left ungraded. Board 12 lost a verifier call and 14 arms to this.
  - Repro: `python3 -X utf8 py_tools/board_score.py wk/gpm/18_uecg/repro/delivered_copy.kicad_pcb --quiet` (BLOCKING=0), then add `--net-min-widths wk/gpm/18_uecg/power_widths.json` (BLOCKING=7).
  - Code: `board_score.py:1101`, `route.py:8313-8408`, `tool_records.py`.
  - Expected:
    - route.py records the requested widths in `kicad_routing_tools`;
    - board_score and check_complete read them automatically, with a pad-neck allowance (#1318);
    - one rule in both skills for a netclass track_width.

Notes for the filer: G03, G07, G33 and G34 are four defects in one 600-line module with no tests, so one issue with four sections is a reasonable alternative to four issues. All outputs and the two scripts are under `wk/gpm/_verify/V3/<Gnn>/`, each folder with a `commands.txt`.

V3: CONFIRMED 4, PARTIAL 1, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V4 -->
V4 verdicts for G05, G09, G40, G17, G32 and G29 are below. No cluster is refuted outright, but three need corrections (G05's mechanism, G29's #1095 framing, G40's board-08 case), and the drafts are written with those fixes. Upstream 0c05be08 changes none of these clusters: its one placement code change, in `simple_anneal.py`, only drops the unused wall-clock budget. All outputs are under `wk/gpm/_verify/V4/<Gnn>/`.

### G05 -- VERDICT: CONFIRMED-PARTIAL
- **title:** place_simple ends every seed with error-graded decap misses it priced, and nothing repairs them.
- **boards:** 06, 09, 10, 12, 13. **Severity:** high.
- **repro at bda59fa0:**
  - Board 10 s5, `--decap-limit-weight 50`: cost 9629.1, the same as recorded. `[ERROR] decap_distance: C92 is 4.86mm from U30 (limit 4.79mm)`.
  - Board 09 s3 at the default weight: C18 is 4.70 against 4.31, U1 pin 21 is 2.54 against 1.77, and C17 gets `decap_ungraded` at 5.93. With C38's class added the same seed has 13 decap errors, up to 5.07 against 1.77. So they are not all near-misses.
  - Recorded `judge.json` floorplan counts: board 10 has 12/12 seeds with at least 1 error, board 13 12/12 (3-19), board 06 12/12 (1-7).
  - `--repair-decaps` was removed in ecd673eb.
- **The cluster's mechanism is refuted.** I wrapped `Annealer.repair` and `anneal()` (`G05/tools/instrument_repair.py`). On board 10 s5 the model counts 1 broken limit (0.069 mm) before the repair, after it, and after the reseat. On board 09 none of the broken caps is in the reseated list, and that run came clean without repair. The misses are in the anneal's own final state. The final legalisation does not cause them.
- **cause** (likely):
  - The limits are a soft term: `place_simple.py:266-273` (`model.set_limits`), weight 10 per mm at `:562`. A 0.07 mm miss costs about 3.5 against a total of about 9600.
  - Nothing enforces the limits after the anneal (`simple_anneal.py:1245-1275`).
  - `judge_order` (`place_simple.py:440-470`) then ranks by error count. On board 13 that skips the cheapest seed, s4.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #1296, #1320, #1188 (its repair tool was retired).
- **issue draft:**
  `place_simple: decap limits are soft-priced, so every seed ships error-graded decap misses, and no tool repairs them`
  > `place_simple` prints "decap limits priced", but on 4 boards every seed ends with check_floorplan `decap_distance` / `decap_pin_distance` errors. Board 10: 12/12 seeds, 1-6 errors at `--decap-limit-weight 50`. Board 13: 12/12, 3-19. Board 06: 12/12, 1-7.
  > Repro: `python3 -X utf8 py_placer/place_simple.py wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb OUT.kicad_pcb --groups wk/gpm/10_glasgow_revC/repro/groups.json --intent wk/gpm/10_glasgow_revC/repro/intent_run.json --decap-limit-weight 50 --seed 5` gives `C92 is 4.86mm from U30 (limit 4.79mm)`.
  > Instrumenting `Annealer.repair` and the reseat shows the 0.069 mm miss is already present when the anneal loop ends; repair and reseat do not change it. On board 09 s3 none of the broken caps was reseated.
  > The limit is a soft term (weight x mm past, `place_simple.py:266-273`). A sub-0.1 mm miss costs about 3.5 against a total near 9600, so the anneal stops on it. Nothing holds the limits afterwards; `--repair-decaps` (#1188) left with the old flows.
  > Consequence: the judge (`judge_order`, which ranks by error count) collapses to the §3.6 case-2 hand repair. On board 13 the lowest-cost seed (s4) was never judged.
  > Expected: a hard post-anneal pass that moves each cap to the nearest legal pose inside its limit. Also show the residual decap errors per seed.

### G09 -- VERDICT: CONFIRMED-PARTIAL
- **title:** The quick seed judge mis-ranks seeds against full routes, and the skill does not say which routing arm the judge chain should carry.
- **boards:** 01, 03, 04, 12 (07 is unsupported: no measurement, no reason given). **Severity:** medium.
- **repro at bda59fa0:**
  - I copied board 01's six pass-3 seeds to `G09/armA` and `G09/armB` and ran `judge_seeds --jobs 1` on each. Arm A says `best seed 9` (quick: 0 vias, 126.84 mm). Arm B says `best seed 1` (quick: 107.27 mm). Both reproduce.
  - Recorded full routes, arm B: s1 105.52 mm, s9 122.01 mm.
  - The judge is wrong within arm A too. Quick says s9 0 vias and s7 1 via; the full arm-A routes give s9 3 vias / 125.97 mm and s7 1 via / 109.13 mm.
  - Board 03 records: quick s23 701.45 < s18 728.86, but full s18 715.41 < s23 755.13.
  - Boards 04 and 12 are records only; re-running them is too long (well over 20 min).
- **cause** (sure for the text, likely for the ranking):
  - `quick_score.py:160-190` (`judge_key`) ranks on `--quick 2` vias and copper, which skip the rescue tail and the plane finalize. Board 04's `poured` joins are shown but not ranked.
  - plan-pcb-placement `SKILL.md:778-780` says to use "the board's routing chain", while plan-pcb-routing `SKILL.md:2298-2307` says to route two arms and keep the better.
- **head 0c05be08:** unchanged. 2caf66c9 touched only README wording.
- **upstream:** new. Related: #1296, #1327, #1321.
- **issue draft:**
  `judge_seeds: the quick-2 ranking inverts full-route rankings when every seed routes, and the skill gives no rule for which arm the judge chain carries`
  > On board 01 (2-layer THT), judging the same six seeds with plan-pcb-routing's two prescribed arms gives different winners.
  > Repro: `KICAD_ROUTE_TRACE=1 python3 -X utf8 py_placer/judge_seeds.py wk/gpm/_verify/V4/G09/armA/judge.json --chain .../chain_armA.txt --intent wk/gpm/01_ecc83-pp_v2/intent_run.json` gives `best seed 9`. The same with armB gives `best seed 1`.
  > Full arm-B routes put s1 at 105.52 mm and s9 at 122.01 mm (+16%).
  > Within arm A the quick route reports s9 at 0 vias; its full route has 3 (s7: 1 via, 109.13 mm).
  > Board 03: quick ranks s23 (701.45) over s18 (728.86); full routes give s18 715.41 and s23 755.13. The quick-vs-full delta per seed (-2% to +8%) is larger than the spread between the top seeds.
  > Board 04: the judge's pick never closed GND at the board's floors, which quick-2 cannot see.
  > Expected: the skill names which arm the judge chain uses (or the judge runs each prescribed arm), and when the top quick scores lie within the quick/full spread, the top k are full-routed.
  > Code: `py_tools/quick_score.py:160` (`judge_key`); plan-pcb-placement §3.7 step 1 against plan-pcb-routing Step 8.

### G40 -- VERDICT: CONFIRMED-PARTIAL
- **title:** Template drift is a WARN, so the judge ranks a broken switching-stage layout first.
- **boards:** 08, 18. **Severity:** low-medium.
- **repro at bda59fa0:**
  - `check_floorplan` on 08 `old/pass4/s10`: `[warn] template ... worst L701 ... 19.00mm`.
  - On 18 `s8`: `worst L2 ... 5.94mm`, also a warn.
  - Both seeds were the judge's best.
- **Board 08 is not a placer failure.** In s10, U702 sits at (113.52, 50.62), inside keep-out `m2-card-2242`, which allows `U*`. L701's template pose, about (113.52, 46.09), is in the same keep-out, which excludes L701. The run's own intent made the template impossible, and no tool reports that contradiction.
- **Board 18 is a genuine anneal minimum:** L3 sits on L2's template spot. The record shows the restored board routing better (139 vias / 929.6 mm against 141 / 1007.5). That is one pair of full routes; I did not re-run it.
- **cause** (sure):
  - `quick_score.py:160` `judge_key` counts floorplan errors only.
  - The template rule's default severity is WARN (`floorplan.py:6775`).
  - SKILL §3.5 step 7 (`SKILL.md:634-640`) says only to report the drift.
  - Workaround: an intent `severity: {"template": "error"}` does reach the judge.
- **head 0c05be08:** unchanged.
- **upstream:** new.
- **issue draft:**
  `Template drift is WARN-only, so judge_seeds ranks a seed with a buck inductor 6-19 mm off its datasheet pose first; a keep-out that forbids a template member is not flagged`
  > Repro: `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/18_uecg/s8.kicad_pcb --intent wk/gpm/18_uecg/intent_run.json | grep template` gives L2 5.94 mm, WARN. s8 was the judge's best.
  > Restoring L2/L3 routed better (139 / 929.6 against 141 / 1007.5; one pair).
  > Board 08 s10 (L701 19.00 mm off): the intent keep-out `m2-card-2242` admits U702 (`U*`) but not L701, so the template pose is forbidden wherever its anchor sits under the card. Neither place_simple nor check_floorplan says so.
  > Expected: §3.7 restores template members, or `judge_key` penalises template drift past tolerance, and the intent check flags a template member excluded from a region its anchor may occupy.
  > Code: `quick_score.py:160`, `floorplan.py:6775`.

### G17 -- VERDICT: CONFIRMED
- **title:** A classless `edge_connectors[]` row is dropped by the edge seat but graded ERROR by check_floorplan.
- **boards:** 08, 09, 16. **Severity:** medium.
- **repro at bda59fa0:**
  - `place_simple` 09 seed 3 with `intent_classless_c38.json` prints `NOTE: C38 is declared on the north edge but is not an edge part (no part class)`.
  - `check_floorplan` on the result: `[ERROR] edge_connector: C38 sits nearest the east edge but is declared on the north edge`.
  - Adding `"class": "connector_affinity"` makes it `edge connector C38 on the north edge, facing it (+y)`, with no edge_connector error.
  - `classify_part` returns None for all three refs (16 U3 ESP32-C3-MINI-1, 09 C38, 08 J501 EDAC).
  - Correction to the cluster: the seed summary is not fully silent. It lists `edge_connector` among its floorplan rules, but does not tie it to the dropped row.
- **cause** (sure): `edge_seat.py:478-488` skips classes not in `SEATED_CLASSES`, while `floorplan.py:4901` `rule_edge_connector` grades every row's edge (`:5017-5030`). `docs/floorplan-intent.md:895` covers only the emitter.
- **head 0c05be08:** unchanged.
- **upstream:** new. #1331 fixed only the declared-class half.
- **issue draft:**
  `Edge seat drops a classless edge_connectors row that check_floorplan grades as an ERROR`
  > Repro: `python3 -X utf8 py_placer/place_simple.py wk/gpm/09_StickHub/repro/fixed.kicad_pcb OUT.kicad_pcb --seed 3 --groups wk/gpm/09_StickHub/repro/groups.json --intent wk/gpm/09_StickHub/repro/intent_classless_c38.json`
  > Then `check_floorplan OUT --intent <same>` gives `[ERROR] edge_connector: C38 sits nearest the east edge but is declared on the north edge`.
  > The seed log only NOTEs that C38 is "not an edge part (no part class): placed as any other part".
  > The same row with `"class": "connector_affinity"` is seated on the north edge, and the error goes away.
  > Hit on 08 J501 (4/12 seeds), 09 C38 (9/12), and 16 U3 antenna module (12/12, whole pass discarded).
  > Code: `py_placer/placement/edge_seat.py:478-488` against `floorplan.py:4901` (`rule_edge_connector`).
  > Expected: seat a classless declared row as `connector_affinity`, or refuse or warn at intent load in both tools. Document that a non-connector edge row needs `class`.

### G32 -- VERDICT: CONFIRMED
- **title:** The anneal prices a part's drawn courtyard while check_assembly gates courtyard plus pad copper, so parts are parked over a big pad that reaches past its courtyard.
- **boards:** 18. **Severity:** medium.
- **repro at bda59fa0:**
  - `place_simple` 18 `--seeds 1` with `intent_pass1_like.json` prints "floorplan: no error" and "NOT BUILDABLE".
  - `check_assembly --baseline fixed`: `E+1 <-> U9 courtyard 0.6304mm2 depth 0.3509mm COURTYARD-BLOCKING`. This matches the recorded s1.
  - E+1 / E-1 have a 12 mm round pad with an 8.5 mm drill inside a 3.6 mm courtyard. They are posed by `fixed_poses` (unlocked in the file).
  - No pre-flight warning anywhere.
- **cause** (sure):
  - `simple_anneal.py:490-510` (`overlap`) prices `P[r].rect()`, the drawn courtyard. Pad copper is priced only for pin frames (`_pins`) and far-face lead boxes.
  - `simple.legal` → `seeder.pose_ok` checks pad copper against the outline only (#1257), not against neighbours.
  - `check_assembly` grades `legality.occupancy_shape` (`legality.py:2001`), which is courtyard ∪ pad copper.
- **head 0c05be08:** unchanged. The upstream additions there are only a restored test for #1257 and wall-clock removal.
- **upstream:** new. Related: #1257 (outline only), #1094.
- **issue draft:**
  `place_simple prices a part's drawn courtyard, but check_assembly gates courtyard plus pad copper: neighbours are parked over a pad that reaches past its courtyard`
  > Repro: `python3 -X utf8 py_placer/place_simple.py wk/gpm/18_uecg/repro/fixed.kicad_pcb 'OUT/p{seed}.kicad_pcb' --groups wk/gpm/18_uecg/repro/groups.json --intent wk/gpm/18_uecg/repro/intent_pass1_like.json --seeds 1`
  > Then `check_assembly OUT/p1.kicad_pcb --baseline wk/gpm/18_uecg/repro/fixed.kicad_pcb` gives `E+1 <-> U9 0.63mm2 depth 0.35mm COURTYARD-BLOCKING`, NOT BUILDABLE.
  > E+1 / E-1 are 12 mm snap-electrode pads in a 3.6 mm courtyard. All 12 pass-1 seeds were NOT BUILDABLE (one was a 0.18 mm² pad short), so the pass was lost. Keep-out circles of r 6.05 were the workaround.
  > Code: `simple_anneal.Annealer.overlap` (`simple_anneal.py:490`) and `seeder.pose_ok` use `_Part.rect()`. `legality.occupancy_shape` (`legality.py:2001`) adds the pads.
  > Expected: the anneal and the legality pass price `occupancy_shape`, and place_simple pre-flight warns when a part's pad copper exceeds its courtyard.

### G29 -- VERDICT: CONFIRMED-PARTIAL
- **title:** Courtyard overlaps that the project grades as KiCad errors stay advisory below the run-23 floors, and `place_pose --near` never checks courtyards.
- **boards:** 06, 14. **Severity:** medium.
- **repro at bda59fa0:**
  - Board 06: `place_pose set C17 --near 153.4 112.7` exits 0 with pad legality clean. `check_assembly --baseline fixed` gives C17↔Y2 0.1505 mm² and C17↔U2 0.0951 mm², both advisory, verdict buildable. kicad-cli DRC on my copy gives 2 `courtyards_overlap` at severity error; the project sets it to error.
  - Board 14 delivered (copied): 17 KiCad errors against `buildable`, with 16 advisory and 1 waived (`edge_class`). The largest advisory pair is 0.308 mm², depth 0.27, fraction 0.18, all under the floors.
- **The cluster's framing is wrong in one point.** #1095 asked only that `ignore`/`warning` waive and said `error` keeps gating as before. These pairs are advisory because of the deliberate run-23 floors. This is not a regression or incomplete fix of #1095.
- **cause** (sure):
  - `legality.py:243-261` and `:2551-2575` gate only when area ≥ 0.5 mm² (or a quarter of the smaller courtyard) and depth ≥ 0.3 mm. The project severity `error` is not consulted.
  - `place_pose --snap/--near` grades pads and holes only, as its docs say.
  - `check_complete` does not run `kicad_drc_compare`, which does show `COURTYARD kicad=2 krt_blocking=0`.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #1095, #1300.
- **issue draft:**
  `On a project with courtyards_overlap=error, sub-floor courtyard overlaps created by the run ship DONE while KiCad reports them as errors; place_pose --near snaps into courtyards`
  > Repro: `python3 -X utf8 py_placer/place_pose.py wk/gpm/06_rp2350_fpga_eensy_prePlane/repro/s9_as_placed.kicad_pcb OUT.kicad_pcb set C17 --near 153.4 112.7 --rot 0` exits 0, legal.
  > `check_assembly OUT --baseline .../repro/fixed.kicad_pcb`: C17↔Y2 0.15 mm² and C17↔U2 0.095 mm², advisory, buildable.
  > `kicad-cli pcb drc OUT --severity-all`: 2 `courtyards_overlap` errors.
  > Board 14 delivered: 17 KiCad errors, all graded advisory, `buildable`.
  > Cause: the run-23 floors (`legality.py:253-261`) keep slivers advisory so that pristine boards don't flip. They do so even for pairs whose members this run moved, and on a project that declares the rule `error`. place_pose's snap ignores courtyards.
  > Expected: when the project severity is error, a pair that a moved member created gates (or at least fails DONE). `place_pose --near` searches courtyard-clean poses or reports the new overlap.

V4: CONFIRMED 2, PARTIAL 4, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V5 -->
## V5 verification report (pin bda59fa0, head 0c05be08)

All six clusters reproduce. G08 and G21 hold only in part. None of the files that cause them changed between bda59fa0 and 0c05be08: the 8 commits touch only kicad_oracle, phase3_routing, plane_obstacle_builder, plane_pad_tap, qfn_fanout, stub_layer_switching, simple_anneal, READMEs and tests. Evidence is under `wk/gpm/_verify/V5/<Gnn>/`.

### G08 -- VERDICT: CONFIRMED-PARTIAL
- **title:** A board's diff pairs are measured but never graded without a `.kicad_dru` skew rule, so check_complete says DONE on a board the placement verifier's rule 5 fails.
- **boards:** 08, 14 (12 does not hold). **severity:** medium.
- **repro at bda59fa0:**
  - Board 14: `board_score.py wk/gpm/14_imx6ulz_4l/repro/done1_delivered.kicad_pcb --intent … --baseline …/pile.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25 --quiet` gives `BLOCKING=0`. The diff_pairs component has `ran:false`. DQS1 is coupled 0.00 of 25.10 mm with 15.467 mm skew; CLK0 is coupled 3.13 of 42.19 mm with 4.242 mm skew. check_complete says `VERDICT: DONE`.
  - Board 08 (copy `G08/b08_routed`): the project declares diff-pair netclasses (100ohm and 90ohm, diff_pair_gap 0.25 / 0.154) and has no dru. 18 pairs are measured, worst `/CM5/PCIE_PI.RX_P` at 5.213 mm, and the verdict is DONE.
  - Same board with `repro/skew_rule.kicad_dru` beside it (`G08/b08_rule`): `diff_pairs=17`, INCOMPLETE. So grading works once a rule exists.
- **What does not hold:**
  - "Neither skill says to write a rule" is wrong. `plan-pcb-routing/SKILL.md:2459-2462` says to declare a `(constraint skew … (within_diff_pairs))` rule. Only the placement skill and its verifier lack that step.
  - Board 12 is not an instance. `/USB_DP` / `/USB_DM` is not a KiCad P/N pair, the project has no diff class, and board_score finds no pair at all. Nothing declares it.
- **cause (sure):**
  - `py_tools/board_score.py:891-951` (`score_diff_pairs`) returns `skipped(...)` at 948-950 when no skew or uncoupled rule exists. The docstring at 903-912 says this is deliberate and matches KiCad.
  - It contradicts `.claude/skills/plan-pcb-placement/references/verifier.md:38-43` (rule 5: a declared class left ungraded is FAIL).
  - Side note: board 14's rule `target length and skew` names netclass `DF_100ohm`, which the project lacks. check_drc reports "2 rule(s); 8 net(s) graded" and never says that rule matches nothing.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #1303 (closed; added the measured component and rule grading) and #1134 (closed; a different P/N self-check).
- **issue draft:**
  > **Declared diff pairs are measured, never graded without a .kicad_dru skew rule; check_complete reads DONE while the placement verifier FAILs the same board**
  >
  > On `wk/gpm/08_CM5_MINIMA_3/repro/routed.kicad_pcb` the project declares diff-pair netclasses (100ohm/90ohm with diff_pair_gap) and has no `.kicad_dru`. `board_score` measures 18 pairs (worst `/CM5/PCIE_PI.RX_P`, skew 5.213 mm) and reports `diff_pairs` as UNGRADED. `check_complete` says DONE.
  > On `14_imx6ulz_4l/repro/done1_delivered.kicad_pcb`, DQS1 has 0.00 of 25.10 mm coupled and 15.467 mm skew, and the verdict is still DONE.
  > Adding a 0.15 mm `within_diff_pairs` skew rule makes board 08 read `diff_pairs=17`, INCOMPLETE, so the grader works once a rule exists.
  > `plan-pcb-placement/references/verifier.md:38-43` FAILs any declared class left ungraded, but the placement skill has no step that writes that rule. Only `plan-pcb-routing/SKILL.md:2459` mentions it, and only as an option.
  > Repro: `python3 -X utf8 py_tools/board_score.py <board> --quiet` with and without the rule file beside the board.
  > Cause: `board_score.py:948-950` (deliberately skipped without a rule).
  > Expected, one of:
  > (a) The placement skill writes a skew rule, or tells the user to, whenever the board has a diff-pair netclass or the chain ran route_diff.
  > (b) board_score grades declared pairs against a disclosed `derived_default`.
  > (c) verifier rule 5 is changed to match what the tools can grade.
  > Also name any `.kicad_dru` rule whose condition matches zero nets (board 14's `DF_100ohm`).

### G15 -- VERDICT: CONFIRMED
- **title:** Impedance grading ignores the project's `net_impedance` records and never compares Z0 or the solved width.
- **boards:** 18, 20. **severity:** high.
- **repro at bda59fa0:**
  - Board 18, `final_route_old2_iter2`: `board_score.py … --impedance-nets 'Net-([CA][1E][0-9]-Pad1)'` gives impedance `{count 0, nets_analyzed 2}`, `BLOCKING=0`. check_complete with no flag says DONE and lists impedance as "UNEXAMINED … no spec was given", although the `.kicad_pro` records both nets at 50 Ω with coplanar gap 0.25, `applied:true`.
  - `check_impedance.py … --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)'` exits 1: the gap is off-target on 57.5 % of the length, and measured Z0 is 64.4 Ω / 80.5 Ω.
  - I re-ran the route step (`G15/rf_out.log`): it solved 0.9201 mm, logged "routed short edge at 0.4601mm", and shipped 0.23-0.59 mm copper with `failed: 0`.
  - The under-width copper is disclosed only in `JSON_SHIPPED_RULES.design_rules` (`site: "impedance copper shipped under width"`).
  - Board 20 (copy `G15/b20`): the project carries 11 `net_impedance` records. check_complete says DONE. With `--impedance-nets 'USB*-D*' '/IO?expansions/usb-a*'`: `impedance=8` (42 crossings), INCOMPLETE.
- **cause (sure):**
  - `board_score.py:960-963` skips when no `--impedance-nets` is given and never calls `read_impedance_specs`. `check_complete.py:395-396` only forwards the CLI flag.
  - `board_score.py:981`: `count` is `nets_with_crossing` only. It ignores check_impedance's broken-promise exit, `length_gap_wrong_mm`, and `z0_measured`.
  - check_impedance itself never compares against the declared ohms. Its `z0_nominal` is computed at the shipped width (`check_impedance.py:741`), so "assumed 60.1 Ω" is never set against the 50 Ω declaration.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #964 (closed; this channel is not among its five) and #610 (closed; the under-width disclosure now exists).
- **issue draft:**
  > **board_score/check_complete never read the project's net_impedance and grade only plane crossings: a 50 Ω declaration shipped at 64-80 Ω reads DONE**
  >
  > `route.py --impedance 50 --coplanar-gap 0.25` on `wk/gpm/18_uecg/repro/final_route_in_ka.kicad_pcb` solves 0.9201 mm and ships 0.23-0.59 mm copper with `failed 0`. The only trace is a `design_rules` narrowing.
  > `check_impedance` on the result exits 1 (gap off-target 57 %, Z0 64.4 / 80.5 Ω).
  > `board_score --impedance-nets 'Net-([CA][1E][0-9]-Pad1)'` reports impedance 0 and BLOCKING 0. `check_complete` without the flag says DONE with impedance "no spec was given", although the `.kicad_pro` records both nets.
  > On `20_sam9g25/repro/dru_delivered_v3` the project records 11 declarations from route_diff. check_complete says DONE; with the flag it is INCOMPLETE, impedance 8.
  > Cause: `board_score.py:960-963` (no auto-read; check_impedance already auto-reads via `protected_nets.read_impedance_specs`) and `:981` (count = crossings only). check_impedance compares Z0 only to its own nominal at the shipped width (`check_impedance.py:741`), never to the declared ohms.
  > Expected: both graders auto-read `net_impedance`. The component counts crossings, check_impedance's broken coplanar promise, and |Z0 − declared| above a tolerance. route.py counts "impedance copper shipped under width" as a failure, not only as a disclosure.

### G16 -- VERDICT: CONFIRMED
- **title:** A `.kicad_dru` track_width rule conditioned on `insideCourtyard()` is graded by nothing.
- **boards:** 20. **severity:** medium.
- **repro at bda59fa0** (copy `G16/b20` of `dru_delivered_v3`):
  - `check_drc.py --clearance-margin 0.1` prints `NO DRC VIOLATIONS FOUND!`. Its only notes are three "clearance 0.1016mm has a non-layer scope -- skipped"; the track_width half of the same rules is never mentioned.
  - `kicad_drc_compare.py … --baseline base20` reports `kicad=0 check_drc=0 … CONSISTENT`.
  - `kicad-cli pcb drc --refill-zones --severity-all` reports **20 `track_width` errors**, e.g. "rule 'DRAM BGA fanout' min width 0.1016 mm; actual 0.0889 mm" (18 on `/memory/ddr-d6`, 2 on `LED-BLUE`). It also reports 3 `solder_mask_bridge` errors, which the comparer drops too.
  - board_score says BLOCKING 0 and check_complete says DONE; neither mentions the rules.
  - Correction to the board's TOOL_GAPS entry: route.py does warn. Its log prints `.kicad_dru rule '…': NOT honoured (condition: predicate insideCourtyard() not modelled)` and lists the rules in `design_rules.unsupported_rules`, then escalates below them anyway.
- **cause (sure):**
  - `py_router/design_rules.py:442-450`: `insideCourtyard` is not modelled, so the rule is `unsupported`.
  - `py_router/check_drc.py:4105-4121` builds `DesignRules` for size floors but never prints its unsupported-rule notes. Length rules do get a NOT GRADED note (#1313).
  - `tests/stress/kicad_drc_compare.py:96-102` and `:213` keep only the copper classes; track_width is out of scope by design.
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #770 (closed; the modelled dru subset), #530 (closed; listed intersectsCourtyard as skipped) and #1313 (closed; the NOT GRADED pattern, so far for length only).
- **issue draft:**
  > **A .kicad_dru track_width rule with an insideCourtyard() condition is graded by nothing: check_drc clean, kicad_drc_compare CONSISTENT, KiCad 20 track_width errors**
  >
  > `wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_dru` requires `track_width min 0.1016` on outer layers for `A.insideCourtyard('U1'|'U200'|'J6')`. route.py's default fab escalation narrows to 0.0889 there. It prints "NOT honoured … KiCad will still enforce it" and narrows anyway.
  > On a `copy_board` copy, `check_drc.py --clearance-margin 0.1` reports NO DRC VIOLATIONS. It notes only the rules' clearance half as skipped and says nothing about track_width.
  > `kicad_drc_compare.py <copy> --baseline <source copy>` reports `kicad=0 … CONSISTENT`, and board_score / check_complete say DONE.
  > `kicad-cli pcb drc --refill-zones --severity-all` reports 20 track_width errors (18 on `/memory/ddr-d6`, 2 on `LED-BLUE`).
  > Cause: `design_rules.py:442-450` (unmodelled predicate). `check_drc.py:4105-4121` never discloses an unsupported SIZE rule. `kicad_drc_compare.py:96-102,213` silently drops every KiCad type outside its copper set (track_width, solder_mask_bridge).
  > Expected: model `insideCourtyard` / `intersectsCourtyard` for size and clearance (courtyards are already parsed for check_assembly), or at least print a NOT GRADED note per unsupported size rule and carry it into board_score's `ungraded`. While a rule is unsupported, the router should not escalate below its min. kicad_drc_compare should list every KiCad error type it does not classify instead of dropping it.

### G44 -- VERDICT: CONFIRMED
- **title:** board_score and check_complete keep only the last `--impedance-nets`.
- **boards:** 18. **severity:** medium.
- **repro at bda59fa0** (`final_route_old1_iter2`):
  - `--impedance-nets 'Net-(AE1-Pad1)' --impedance-nets 'Net-(C10-Pad1)'` gives `nets_analyzed 1`, impedance 0, BLOCKING=0.
  - The reverse order gives impedance 1, BLOCKING=1.
  - Both nets after one flag give `nets_analyzed 2`, impedance 1.
  - check_complete: DONE in the first order, INCOMPLETE (blocking 1) in the second.
- **cause (sure):**
  - `py_tools/board_score.py:1357` and `check_complete.py:583` use `nargs='+'` without `action='extend'`.
  - `.claude/skills/plan-pcb-placement/scripts/grade.py:176-186,71` turns each `--spec impedance-nets=X` into its own repeated flag.
  - No other `nargs='+'` flag exists in these two files. route.py and route_diff already use `extend` for `--keep-away`.
- **head 0c05be08:** unchanged.
- **upstream:** new.
- **issue draft:**
  > **board_score / check_complete keep only the last --impedance-nets; grade.py's repeatable --spec produces exactly that, so argument order hides a defect**
  >
  > On `wk/gpm/18_uecg/repro/final_route_old1_iter2.kicad_pcb`:
  > `board_score.py … --impedance-nets 'Net-(AE1-Pad1)' --impedance-nets 'Net-(C10-Pad1)' --quiet` gives impedance 0, BLOCKING 0, `nets_analyzed 1`.
  > Swapping the order gives impedance 1, BLOCKING 1.
  > check_complete flips between DONE and INCOMPLETE the same way.
  > `grade.py --spec impedance-nets=A --spec impedance-nets=B` emits the repeated form (`grade.py:71,176-186`).
  > Cause: `board_score.py:1357` and `check_complete.py:583`, `nargs='+'` with no `action='extend'`.
  > Expected: both values are used (`action='extend'`). Audit the other `nargs='+'` spec and net flags that skills pass repeatedly: check_impedance `--nets` and check_drc `--nets`.

### G21 -- VERDICT: CONFIRMED-PARTIAL
- **title:** route.py length matching cannot aim at a `.kicad_dru` length window.
- **boards:** 14. **severity:** medium.
- **repro at bda59fa0** (copy `G21/dq_poured`):
  - One call (verbatim 14 §1 flags, `G21/route_all8.log`):
    - It prints "length is not routed to" for both rules.
    - The match targets 15.23 mm, which is DQ5's natural length, against a window of 11.5-14.5.
    - DQ2 gets "No straight run … Can't fit more bumps (got 0, need 1)" and stays at 9.75 mm.
    - "Matched nets" lists all 8, and JSON_SUMMARY has no per-member status.
    - `check_drc` then reports **8/8 length-out-of-range**: 7 long by 0.43-1.33 mm, DQ2 short at 9.55.
  - Protection drop (`G21/s1_46.log`, `s2_25.log`):
    - Step 1 matches DQ4 and DQ6 at about 12.1 mm and protects them.
    - Step 2, with the same group glob, prints `Matched nets: [DQ2, DQ5]`, target 14.49. DQ4 and DQ6 appear only in "excluded from pre-existing rip candidacy", not as group members, and nothing warns.
  - "Rip victims are re-matched short": not reproduced. No repro was given, so I did not build one.
  - Also observed: route.py's own lengths run 0.2 mm above check_drc's KiCad-equivalent measure on 6 of 8 nets (DQ5 15.23 vs 15.028; DQ2 9.75 vs 9.546). Not root-caused.
- **cause:**
  - `py_router/length_matching.py:2042`: `target_length = max(member lengths)`; no dru window is read (sure).
  - `py_router/design_rules.py:1399-1407`: length is parsed but not consumed (sure).
  - `py_router/routing_common.py:829,888`: group members come only from `routed_results`, and protected nets are excluded from it as rip candidates, so `_seed_group_members_from_board` (`length_matching.py:1878`, scoped to `net_names`) never sees them (likely, consistent with the measurement).
- **head 0c05be08:** unchanged.
- **upstream:** new for route.py. Related: #1363 (open; the bus-step half), #1313 (closed; grading only, the router still prints "not routed to") and #521.
- **issue draft:**
  > **route.py length matching cannot aim at a .kicad_dru length window: the target is the longest member, protected members leave the target silently, and an unmeanderable member ships with no status**
  >
  > The board's dru declares DRAM_LDQ length 11.5-14.5 mm.
  > `route.py wk/gpm/14_imx6ulz_4l/repro/dq_poured.kicad_pcb <out> --nets /DRAM/DRAM_DQ0..7 --length-match-group '/DRAM/DRAM_DQ[0-7]' --length-match-tolerance 0.8 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 2.5 1.0 --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --no-bga-zones --escalation board` targets 15.23 mm. check_drc then reports 8/8 nets out of window.
  > DQ2 cannot be meandered ("got 0, need 1"), ships at 9.55 mm, and is still listed as matched. JSON_SUMMARY carries no per-member status.
  > Routing DQ4+DQ6 first and then DQ2+DQ5 with the same group glob drops the protected DQ4 and DQ6 from the second target without a word.
  > It took a 25-order search to land all 8 nets.
  > Cause: `length_matching.py:2042` (max member), `design_rules.py:1399-1407` (length not consumed), `routing_common.py:829,888` (members come from this run's results only).
  > Expected: clamp the target into the binding dru window (meander short members up to min, never past max). Count board-resident and protected members toward the target. Report per-member matched/unmatched (with the shortfall) in JSON_SUMMARY. Measure length as check_drc does: route.py currently reads 0.2 mm long on 6 of 8 nets.

### G36 -- VERDICT: CONFIRMED
- **title:** check_floorplan prints nothing for an edge part whose facing is exempt (edge_actuator).
- **boards:** 20. **severity:** medium.
- **repro at bda59fa0** (copy `G36/facing`): `check_floorplan.py … --intent intent_run.json` reports 0 errors.
  - The SW1 and SW2 rows carry no facing clause at all; J2 prints `facing west [courtyard+fab+marker, strong] pass`.
  - The JSON shows `disposition: "exempt"`, `policy: "exempt: part_class class edge_actuator"`, `reason: "symmetric about its pads"`.
  - The F.Fab actuator tab sits at local y 1.45→2.1. SW1 at rot 0 therefore faces south, along the west edge; SW2 at rot 270 faces west, along the south edge.
  - With `mating_face: "+y"` on both rows: 2 errors, `facing south [declared, strong] FAIL` and `facing west … FAIL`.
- **mechanism correction:** this is not "abstains". It is a deliberate class exemption (`floorplan.py:3779-3784` docstring, `:3802`) that the CLI drops. `_facing_tail` returns '' for `exempt` (`floorplan.py:5170-5171`). The placement skill (`SKILL.md:302-310`) tells the reader to expect only `pass` or `abstained`, and asks for `mating_face` only when facing abstained (sure).
- **head 0c05be08:** unchanged.
- **upstream:** new. Related: #1155 (closed; it added the facing conjunct and the actuator exemption).
- **issue draft:**
  > **check_floorplan prints no facing clause for an exempt edge part, so a side-push switch facing along its edge reads "pass"**
  >
  > On `wk/gpm/20_sam9g25/repro/facing_final_v1.kicad_pcb` (with its `intent_run.json`), SW1 and SW2 (EVQP7C side-push, actuator on local +y) are declared on the west and south edges. Both actuators point along their edges.
  > `check_floorplan` prints `overhang … pass` with no facing word. Its JSON says `exempt: part_class class edge_actuator` ("symmetric about its pads").
  > Declaring `mating_face: "+y"` on both rows makes both FAIL (strong), so the conjunct works once the face is declared.
  > Cause: `floorplan.py:3802`, plus `_facing_tail` returning '' for `exempt` at `:5170-5171`. The placement skill §3.4 (`SKILL.md:302-310`) prompts for `mating_face` only on `abstained`.
  > Expected: print `facing exempt (<policy>)`. Have the skill ask for `mating_face` on an exempt edge_actuator too, since a side-push switch has a face. Optionally infer the face from an F.Fab protrusion beyond the body rectangle, here 0.65 mm on +y.

V5: CONFIRMED 4, PARTIAL 2, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V6 -->
I re-ran all seven V6 clusters at bda59fa0. Five are confirmed and two are confirmed in part. For G42 and G46 I also found the cause in code, by measurement. bda59fa0..0c05be08 changes none of the code behind any of the seven. Every repro and log is under `wk/gpm/_verify/V6/<Gnn>/`. Nothing was written into a board folder, and I did not run kicad-cli.

### G06 -- VERDICT: CONFIRMED-PARTIAL
- title: route.py fails a pad its own copper cages as "no rippable blockers / boxed in by static obstacles" even after the rip ladder ran, and the hint asks for a wider clearance and track
- boards: 04, 06, 11, 13, 20 (re-run: 06, 11)   severity: high
- repro at bda59fa0:
  - Board 06, verbatim §2 on a copy (`G06/in.kicad_pcb`):
    - Run 1 gives `failed_single ["/RP2354A/FPGA.~{STATUS}"]`. The rip ladder ripped 5 nets, restored them, then printed `ROUTE FAILED - no rippable blockers found` and the hint `boxed in by static obstacles ... --grid-step 0.05 --clearance 0.15 --track-width 0.15 (current: grid 0.1, clearance 0.09, track 0.0762)`.
    - `check_reachability --pad U2.A4 --track 0.0762 --clearance 0.09`: PASSABLE (+346.6 µm) on the input; on out1 it says "with the routing in place: CAGED (margin -75.6 um), throat between U2.A1 and via@GND, ROUTED COPPER cages this pad".
    - A scoped lap at `--grid-step 0.05` gives `failed 0`. Its frontier blames `Net-(U2-GPIOL_20_PLLIN)` (via-in-pad decline), rips it and re-routes it. The result passes check_connected (ALL NETS FULLY CONNECTED) and check_drc (clean). The same lap at grid 0.1 gives `failed 2` and the improvement gate reverts it.
  - Board 11, verbatim §2:
    - `failed_single ["/OSCOUT"]`; reachability says PASSABLE (+173.3 µm), CAGED with the routing.
    - A grid-0.05 lap routes /OSCOUT but opens /OSCIN (one net traded for another).
    - Adding the hint's rips opens +3.3V, and the gate reverts it.
  - What does not hold: "the rescue never tries the finer grid" is wrong. net_rescue rung 0 tried grid 0.025 at the run's own clearance and failed ("Rescuing /RP2354A/FPGA.~{STATUS}", 2→2 parts). That rung is scoped and never rips. What worked on 06 was a finer grid together with a rip, and no in-run stage does both. On 11 even that is not a fix.
  - Boards 04, 13 and 20 were not re-run. Board 13's instance is the same USB-pair wall as G18 and G38.
- cause (sure):
  - `py_router/routing_diagnostics.py:971` gates the static verdict on iteration count only (`iters >= 20000`), so it does not see that the rip ladder ran.
  - `routing_diagnostics.py:990` hardcodes `--clearance 0.15 --track-width 0.15`.
  - `single_ended_loop.py:1689-1693` prints "no rippable blockers found" whenever `not ripped_up`, including after a ladder that ripped 5 nets.
  - `net_rescue.py` rung 0 is no-rip by design.
- head 0c05be08: unchanged
- upstream: related #95 (closed; the static hint came from its fix), #331 (closed; the rescue rungs), #1348 (closed; same pattern in route_bus). New.
- issue draft:
  **route.py: a pad caged by the run's own copper fails as "no rippable blockers, boxed in by static obstacles", and the hint asks for a wider clearance and track**
  - On rp2350_fpga_eensy (06), `/RP2354A/FPGA.~{STATUS}` fails at grid 0.1. check_reachability `--pad U2.A4` says PASSABLE (+346.6 µm) on the placement and CAGED (-75.6 µm) only with the run's own routing (a GND via next to U2.A1).
  - The log runs the rip ladder to N=5, restores, then prints `ROUTE FAILED - no rippable blockers found` and `boxed in by static obstacles ... --clearance 0.15 --track-width 0.15`. That clearance and track are wider than the run's 0.09 / 0.0762.
  - The per-net rescue retries at grid 0.025 without rips and fails. A scoped `--grid-step 0.05` lap rips `Net-(U2-GPIOL_20_PLLIN)` and routes the pad: failed 0, connected, DRC clean. The same lap at grid 0.1 fails 2 and is reverted.
  - Repro (WT): `route.py wk/gpm/06_rp2350_fpga_eensy_prePlane/repro/status_s4_diff.kicad_pcb OUT --nets '*' <06 §2 flags>`, then the same flags on OUT with `--nets '/RP2354A/FPGA.~{STATUS}' GND +3V3 --grid-step 0.05`. Outputs are in `wk/gpm/_verify/V6/G06/`.
  - Board 11 (/OSCOUT, PASSABLE +173 µm, CAGED with routing) shows the same message and hint. There the grid-0.05 lap only trades /OSCOUT for /OSCIN, so the lever is not universal.
  - Expected:
    - (a) No "static" verdict and no "no rippable blockers" line after a ladder that ripped nets.
    - (b) The hint never suggests a clearance or track above the run's own.
    - (c) For a CAGED-by-routing pad, an in-run retry that combines a finer grid with the rip ladder.
  - Code: `routing_diagnostics.py:971` and `:990`, `single_ended_loop.py:1689-1693`, `net_rescue.py` rung 0 (no rip).

### G18 -- VERDICT: CONFIRMED
- title: Naming a protected net exactly in --rip-existing-nets lifts protection in the main pass only; the plane finalize and its nested sub-runs still refuse it
- boards: 13   severity: medium
- repro at bda59fa0:
  - `copy_board` of `13_pico_ice_rev3/explore_E/6_lap1.kicad_pcb`, then `bash wk/gpm/_verify/V6/G18/lap2_v.sh`. This is lap2.sh retargeted to my folder (about 3 min).
  - The protection lines match the teammate's log exactly:
    - l.32: the main pass lists /USB_P and /USB_N as "eligible for rip-up".
    - l.336: the finalize prints `4 PROTECTED net(s) excluded from blocker rip-up (/USB_D+, /USB_D-, /USB_N, /USB_P)`.
    - l.345: `Pad C12.1 ... blocked by /USB_P (protected, cannot rip)`.
    - l.387: the nested sub-run excludes /USB_P and /USB_N.
    - l.162 and later: hints say "The router will NEVER rip these" about nets the run had made eligible.
  - Result: `failed_single ["+3V3", "/~{ICE_RST}"]`.
  - Counterfactual (`G18/override_patch_run.py`): `protection_map` drops the stashed exact-name overrides. The finalize then excludes only /USB_D+ and /USB_D-, rips /USB_N at C12.1, and +3V3 closes. check_connected goes from 3 open nets to 2. check_drc is clean on both boards.
- cause (sure):
  - `py_router/repair_planes.py:1369-1377` builds the never-rip set from `protection_map(pcb_data)` and never subtracts `protected_nets.rip_override_names(pcb_data)`. The finalize runs on the live pcb_data, so the run-6 z2 stash is right there.
  - `py_router/route.py:3672-3677`: a nested sub-run's pre-existing filter uses `override_patterns = rip_existing_nets + caller pats`. Neither is forwarded (`_FINALIZE_ROUTE_KNOBS`, route.py:296), and the filter does not read the stash.
  - `routing_diagnostics.py:528-572`: the "NEVER rip" hint reads the raw protection map.
- head 0c05be08: unchanged
- upstream: new. Related #521 (the override) and #677 (open, the wall). It is an incomplete coverage of the run-6 z2 `stash_rip_overrides` fix, which reached only the in-run ladders.
- issue draft:
  **An exact-name --rip-existing-nets override is ignored by the plane finalize and its sub-runs, so a plane tap is refused on a net the run made rippable**
  - On pico_ice_rev3 (13), `--rip-existing-nets '/USB_N' '/USB_P' ...` makes both nets eligible in the main pass (log l.32).
  - The in-run plane finalize still prints `4 PROTECTED net(s) excluded from blocker rip-up (/USB_D+, /USB_D-, /USB_N, /USB_P)` (l.336) and fails `Pad C12.1 ... blocked by /USB_P (protected, cannot rip)` (l.345). Its nested sub-run excludes them again (l.387).
  - The failure hints keep saying "The router will NEVER rip these" for the overridden nets.
  - Measured cost: honouring the stashed overrides in `protection_map` (a monkeypatch, `wk/gpm/_verify/V6/G18/override_patch_run.py`) closes +3V3. Open nets go 3 → 2, DRC clean.
  - Repro (WT): `copy_board.py wk/gpm/13_pico_ice_rev3/explore_E/6_lap1.kicad_pcb D/6_lap1.kicad_pcb`, then lap2.sh's route.py command pointed at D, then `grep -n "PROTECTED\|eligible for rip-up\|cannot rip" log`.
  - Expected: one effective protected set per run, the protection map minus `rip_override_names` (never 'locked' or `sense:`). The finalize's blocker rip-up, the nested sub-runs and the hints should all read it.
  - Code: `repair_planes.py:1369-1377`; `route.py:3672-3677` (and `_FINALIZE_ROUTE_KNOBS` at :296 has no rip override); `routing_diagnostics.py:528-572`.

### G38 -- VERDICT: CONFIRMED
- title: Diff pairs routed before the fanout and planes take the only drop site of a plane ball (VMEM), and #521 protection keeps them there
- boards: 13, 14   severity: medium
- repro at bda59fa0:
  - `board_score` (verbatim 14 §3) on a copy of `a9_routed`: `BLOCKING=1 (broken=1)`; check_connected: VMEM, U2 pad at (73.60, 107.80) F.Cu disconnected.
  - check_reachability `--net VMEM --at 73.6,107.8`: PASSABLE on the placement, CAGED with the routing.
  - Copper near U2.C1 on a9:
    - /DRAM/DRAM_DQS0_P on In2.Cu at 0.30 mm and DQS0_N at 0.50 mm. A 0.45 mm via needs 0.375 mm. The pair is in `protected_nets` (diff-pair).
    - DQ11 on In1.Cu at 0.0 mm and DQ12 on B.Cu at 0.1 mm. These are not protected.
  - On `dq_first` (the board before the pair step), only the DQ6 and DQ1 F.Cu stubs are within 0.8 mm.
  - The pairs share the wall with the later, unprotected DQ8-15 lane. The protected part is the In2 pair, on the layer the drop needs.
  - Board 13's instance is the USB pair at C12.1. In G18 it is shown decisive: releasing it closes +3V3.
- cause (likely): route_diff reserves nothing for balls a later step must drop to a plane. Protected copper then joins the never-rip set in the finalize (`repair_planes.py:1369-1377`) and the rip filters (`protected_nets.py`). No single line.
- head 0c05be08: unchanged
- upstream: dup of #677 (open). These are new instances: a plane ball (14) and a plane tap (13).
- issue draft:
  **#677 instances: a pair routed before the fanout takes a plane ball's only drop site; the ball ships open**
  - imx6ulz_4l (14), arm A9: route_diff lays DQS0, DQS1 and CLK0 on the DQ-routed board before bga_fanout. The final board scores BLOCKING=1 with VMEM U2.C1 (73.6, 107.8) stranded.
  - That ball is PASSABLE on the placement and CAGED with the routing. The protected DQS0_P/N run on In2.Cu 0.30 / 0.50 mm from it, inside the 0.375 mm a 0.45 mm via needs. No later step may rip them.
  - Six re-orderings each lost a pair or opened 1-4 nets. Only a hand via-in-pad placed before the pair step fixed it.
  - Repro (WT): `board_score.py wk/gpm/14_imx6ulz_4l/repro/a9_routed.kicad_pcb --intent wk/gpm/14_imx6ulz_4l/intent_run.json --baseline wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25 --quiet` gives BLOCKING=1 VMEM.
  - pico_ice_rev3 (13): the routed USB pair walls the +3V3 tap at C12.1; releasing it (see the override issue) closes the net.
  - Expected: reserve the escape and drop sites of poured-net balls when pairs route early, or rip a pair as a pair when it is the decisive wall (#677 option 1).

### G39 -- VERDICT: CONFIRMED-PARTIAL
- title: check_join --keep-staged writes a board the chain continues from but does not record itself in the redo manifest
- boards: 04, 14, 19   severity: low
- repro at bda59fa0:
  - `REDO_RUNDIR=…/G39/cj REDO_MANIFEST=…/G39/cj/redo_commands.sh check_join.py <copy of 14's dq_first> VMEM 73.6,107.8,F.Cu 73.6,107.8,In2.Cu via:73.6,107.8 --keep-staged …/cj/c1via.kicad_pcb` prints CLEAN. `cj/` then holds only c1via.* and no redo_commands.sh.
  - Control: `copy_board.py` with the same env writes `cp/redo_commands.sh` and `.timings.jsonl`.
  - Board manifests: `grep -c check_join` on 14's final_route manifest gives 0. 04's manifest has 4 `MANUAL STEP` lines. `grep -c "pcb upgrade"` gives 0 on 19's manifest and 1 on its plan.sh.
  - What does not hold: `kicad-cli pcb upgrade` and the agents' helper scripts are not repo CLIs, so their absence is not a recorder defect. The upgrade is only needed as a G01 workaround.
- cause (sure): `py_tools/check_join.py:273-280` writes `--keep-staged`, and the module never calls `redo_record.record_invocation` (fill_for_delivery, copy_board, route*, fanouts and place_* do).
- head 0c05be08: unchanged
- upstream: new. Related #132 (self-recording), #1302 (closed, env knobs), #1360 (closed; no tool commits joins).
- issue draft:
  **check_join --keep-staged is a board-mutating step that never records into redo_commands.sh, so a chain with hand joins does not replay**
  - plan-pcb-placement SKILL.md:939 prescribes `check_join.py <board> <NET> ... --keep-staged <out>` and says "continue from it".
  - With REDO_RUNDIR and REDO_MANIFEST set, check_join writes `<out>` and siblings but appends nothing to the manifest. copy_board with the same env does append.
  - Measured: 14's shipped manifest holds 13 commands and no check_join. Its route_diff step reads `s1e_c1via.kicad_pcb`, which only a hand join wrote, so a no-LLM replay dies at step 7. Board 04 needed three joins appended by hand.
  - Repro (WT): `REDO_RUNDIR=$PWD/X REDO_MANIFEST=$PWD/X/redo_commands.sh python3 -X utf8 py_tools/check_join.py wk/gpm/14_imx6ulz_4l/repro/dq_first.kicad_pcb VMEM 73.6,107.8,F.Cu 73.6,107.8,In2.Cu via:73.6,107.8 --keep-staged X/c1via.kicad_pcb; ls X` shows no manifest.
  - Expected: `record_invocation()` when `--keep-staged` is given (a pure check writes nothing, so it need not record).
  - Code: `py_tools/check_join.py:273-280`, which has no redo_record import.
  - The missing kicad-cli upgrade step (19) is a consequence of G01, not of the recorder.

### G42 -- VERDICT: CONFIRMED
- title: route.py's plane finalize depends on PYTHONHASHSEED: a set of layer names decides which island an anchor joins
- boards: 17, 20   severity: medium
- repro at bda59fa0:
  - Board 17, verbatim §4 loop, 4 runs on a copy: segment+via lines (each name below is a run's output md5) alternate 1188 (de4b…) / 1183 (b610…) / 1183 / 1188. The logs are identical until the #611 F.Cu follow-up's `Region discovery from fill model: 16 vs 15 region(s)`, with the same counts of 40 fill islands, 10 off-fill anchors and 4 orphans.
  - Board 17 with fixed hash seeds:
    - With the Step 2c env stack, `PYTHONHASHSEED` 0, 0, 1 and 2 give b610 / 1183; seed 3 gives de4b / 1188.
    - Without the env stack, seeds 0 and 3 give the same board.
    - With `zone_layers` sorted at that one call (`G42/sorted_layers_run.py`), seeds 0 and 3 both give de4b.
  - Board 20, verbatim §5 copy, 3 unseeded runs:
    - Run a printed `Zone SPLIT: 3 island(s) (23.8 mm^2)` (373 via lines, md5 ef11…); runs b and c printed 4 islands (117.8 mm²), 378 via lines (md5 a1ab…).
    - Seeds 0 and 3 gave a1ab.
    - With sorted `zone_layers`, seeds 0 and 3 both gave ef11, the same board as unseeded run a.
- cause (sure that the order of `zone_layers` into this function decides it):
  - `py_router/plane_region_connector.py:617` loops `[plane_layer] + [l for l in zone_layers ...]` and attaches each anchor to the first layer's island it touches.
  - `zone_layers` is a `set()` of layer-name strings, built at `repair_planes.py:1304` and passed raw at :1838, :1919 and :2519. str hashing is randomized per process.
  - The same set is also iterated at :568/:575 and :597. Those look harmless for connectivity, but should be sorted too.
- head 0c05be08: unchanged (the `kicad_oracle.py` changes there are unrelated)
- upstream: new. Same class as #457 (closed; placement quench Set[str] order). Related #490 (closed; refill jitter).
- issue draft:
  **route.py is not deterministic across processes: fill-model region discovery iterates a set of layer names, so the plane finalize follows PYTHONHASHSEED**
  - CLAUDE.md says routing is deterministic run to run. On environment_sensor (17, with the Step 2c env stack), identical runs alternate between two boards: 1188 / 1183 segments+vias (923.97 vs 917.32 mm).
  - On sam9g25 (20), the boards differ by 5 via lines (373 vs 378) and by `Zone SPLIT: 3 island(s) (23.8 mm^2)` against `4 island(s) (117.8 mm^2)`.
  - With a pinned `PYTHONHASHSEED`, both boards are reproducible. On 17, seeds 0, 1 and 2 give one board and seed 3 the other.
  - Handing `_regions_from_fill_models` a sorted `zone_layers` makes seeds 0 and 3 agree on both boards. On 20 that board is the one the unseeded "rare" run produced.
  - Repro (WT): run 17 §4's command twice as `PYTHONHASHSEED=0 …` and `PYTHONHASHSEED=3 …` and compare `grep -E '^\s*\((start|end|at) ' OUT | md5`. Scripts are in `wk/gpm/_verify/V6/G42/` (loop17_seed.sh, cf_sorted.sh, seed20.sh).
  - Code: `plane_region_connector.py:617` (first-match anchor attribution over `zone_layers`), fed by the set built at `repair_planes.py:1304`. Also sort :568/:575/:597.
  - Expected: iterate layers in a fixed order (stackup order or sorted), and add a two-hash-seed determinism test for the finalize.

### G45 -- VERDICT: CONFIRMED
- title: route_diff cannot re-route an already-connected pair (no --force-reroute or --rip-existing-nets), and Step 2d's `--nets P N --force-reroute` re-routes a protected pair single-ended
- boards: 08, 14   severity: medium
- repro at bda59fa0:
  - `route_diff.py --help | grep -c -E 'rip-existing|force-reroute'` prints 0.
  - Verbatim 14 §7 on a copy of done1 prints `Skipping 6 already-routed net(s): Already fully connected` and `All nets are already fully connected - nothing to route!`, writes an unchanged copy and exits 0.
  - `route_diff.py … --force-reroute` exits 2 with "unrecognized arguments".
  - On the same done1, board_score says DQS1_P is coupled 0.00 of 25.10 mm (skew 15.467 mm), and BLOCKING=0, so the uncoupled pair passes the gate.
- cause (sure):
  - `py_router/route_diff.py:1087` calls `filter_already_routed` with no bypass, and the parser has no rip or force flag.
  - `plan-pcb-routing/SKILL.md:1928-1931` prescribes `--nets P N --force-reroute`. That runs route.py, which is single-ended only (its own help says to use route_diff for pairs).
- head 0c05be08: unchanged (route_diff.py and the skills are untouched)
- upstream: related #515 (closed; `--force-reroute` landed on route.py only, and its comment notes route_diff has no rip flag), #677 (open). New.
- issue draft:
  **route_diff has no way to re-route a connected pair, and the routing skill's #521 override recipe de-pairs it**
  - On imx6ulz_4l (14) the DONE board's DDR strobes are connected but uncoupled: DQS1_P is coupled 0.00 of 25.10 mm with a skew of 15.47 mm.
  - Re-running route_diff on them prints "Skipping 6 already-routed net(s) ... nothing to route!", writes an unchanged copy and exits 0. `--force-reroute` is "unrecognized" (exit 2).
  - The teammate had to write strip_nets.py to delete the copper first.
  - plan-pcb-routing SKILL.md:1928-1931 says to name both members "EXACTLY with `--nets P N --force-reroute`". That is a route.py command, and route.py routes single-ended, so the protected pair comes back uncoupled (08).
  - Repro (WT): `python3 -X utf8 py_router/route_diff.py wk/gpm/14_imx6ulz_4l/repro/done1_routed.kicad_pcb OUT --nets '/DRAM/DRAM_CLK0_*' '/DRAM/DRAM_DQS*' --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 2.5 1.0 --via-size 0.45 --via-drill 0.25 --escalation board --diff-pair-intra-match`.
  - Expected:
    - route_diff takes `--force-reroute` (rip both members, route as a pair, keep #521 exact-name semantics) and threads it through the GUI and FLAG_PARAMS.
    - Step 2d points at route_diff for pairs.
  - Code: `route_diff.py:1087`.

### G46 -- VERDICT: CONFIRMED
- title: Phase-3 rip-up blames the wrong net on a power tap because, when the neck-down retry fails, the blocker analysis keeps the WIDE attempt's frontier
- boards: 05   severity: medium
- repro at bda59fa0:
  - Verbatim 05 §1 on a copy gives the same output as the teammate's:
    - `blocked_by /PC-DB6 (blocked_count 1)`;
    - `Ripping /PC-DB6 ... No previously-routed nets blocking ... No additional rippable blockers from retry analysis`;
    - VCC open at BUS1 (164.465, 138.43).
  - The wall is as claimed:
    - /PC-RST runs on B.Cu, 0.2 mm wide: (162.4,134.2)→(165.6,134.2)→(167.0,135.6). It caps the finger and both 0.762 mm side channels.
    - /PC-DB6 is pad 34 on F.Cu.
    - /PC-RST has 4 segments and 0 vias, so it qualifies as a pre-existing rip candidate.
    - check_reachability `--pad BUS1.3`: PASSABLE, CAGED with the routing.
  - Discriminating arm: the same command with `--power-nets-widths 0.2 0.2` (no wide→neck-down). The cascade then names `/PC-RST (was blocking 'VCC')`, rips it, and VCC routes; /PC-RST re-routes PARTIAL. The same board and the same layers, only the width changed.
- cause (likely, revised from the cluster's "layer-blind attribution"):
  - `py_router/single_ended_routing.py:3574-3577`: when the neck-down retry fails, the code deliberately returns the wide (0.7 mm) attempt's frontier for rip analysis.
  - The wide search cannot leave the 1.778 mm finger past its static neighbours, so its frontier never meets /PC-RST's cells. `blocking_analysis.compute_net_obstacle_cells` rasterizes those at the default width.
  - The narrow frontier, which would name /PC-RST, is discarded.
- head 0c05be08: unchanged (the `phase3_routing.py` diff only touches the seam re-ask)
- upstream: new. Related #510 (closed), #592 (open), #675 (closed; phase-1 vs phase-3 metrics).
- issue draft:
  **A power-net tap that fails its neck-down retry is analysed for rip-up on the wide attempt's frontier, so the real wall is never named**
  - interf_u (05): VCC's phase-3 tap to edge finger BUS1.3 (B.Cu) fails at the 0.7 mm power width and then at the 0.2 mm neck-down.
  - The rip cascade blames `/PC-DB6`, the F.Cu finger opposite, with one cell. It rips and restores it, and prints "No additional rippable blockers". VCC ships open.
  - The real wall is /PC-RST's B.Cu track, 0.42 mm above the finger and spanning both side channels. It is a 4-segment candidate that no selector names.
  - With `--power-nets-widths 0.2 0.2` the same cascade names /PC-RST, rips it and routes VCC. Only the frontier differs.
  - Repro (WT): verbatim 05 §1 (`route.py wk/gpm/05_interf_u/repro/vcc_finger_walled.kicad_pcb OUT --nets VCC GND ... --power-nets-widths 0.7 0.7 ... --escalation board`). Then the same with `0.2 0.2`. `grep -E "Ripping|was blocking|No additional rippable"` on both.
  - Cost on the board: this single open set the lowest reachable via count (72 vias with it open vs 88 shipped) across about 10 laps.
  - Code: `single_ended_routing.py:3574-3577` returns `result` (the wide frontier) when `retry[0] is None`. The attribution in `blocking_analysis.analyze_frontier_blocking` then cannot see a wall the narrow route meets.
  - Expected:
    - Attribute on the frontier of the attempt at the width the net will actually route at, or on the union of both frontiers.
    - Order a forced re-route of the named wall after the tap it walls in.

V6: CONFIRMED 5, PARTIAL 2, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V7 -->
### G10 -- VERDICT: CONFIRMED
- title: check_assembly never gates a part inside another courtyard-less part's silk-drawn body; BAT1 stopped gating after #1201
- boards: 07, 08   severity: high
- repro at bda59fa0: `python3 -X utf8 py_tools/check_assembly.py wk/gpm/07_One-Air-Max/repro/silk_body_inside.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/silk_body_inside.intent.json --baseline wk/gpm/07_One-Air-Max/fixed.kicad_pcb` -> `contained 7  courtyard_blocking 0 ... VERDICT: buildable (blocking 0)`. Solarpower1, NTC1, C10 and C13 each sit 100% inside BAT1, and each reads `[does not gate: a silk-drawn body, which never gates (#896)]`. The JSON has `courtyard_pairs` = 0, so no channel gates. 08 `s6.kicad_pcb` (same tool, `--baseline fixed.kicad_pcb --intent intent_run.json`) -> `CN1 <-> Module302 pads_under_body ... CONTAINED 100%`, buildable. Control: `place_pose ... set LED2 125 70` (LED2 draws a courtyard) -> `BAT1 <-> LED2 COURTYARD-BLOCKING`, NOT BUILDABLE. So the blind spot is a silk body against a silk body. Outputs are in `wk/gpm/_verify/V7/G10/`.
- cause: `py_placer/placement/legality.py:3245-3249` (`_silk_drawn_pair` exemption) and `:3263`; `py_tools/check_assembly.py:59`. Sure.
- head 0c05be08: unchanged (`legality.py`, `body.py` and `check_assembly.py` are untouched).
- upstream: regression of #1184. At #1184's close, BAT1's five pairs gated (22 of 22), but only because BAT1's occupancy came from a 0.06 mm F.Fab dot. The #1201 fix rejected that dot, so BAT1's body became silk-sourced. #1201's own comment measured this drop and asked for a decision, and none was recorded. Related: #896, #1250, #1106, #1300.
- issue draft:
  **check_assembly never gates a part wholly inside another part's silk-drawn body; One-Air-Max's battery holder stopped gating after #1201**
  - On One-Air-Max, 197 of 204 footprints draw no courtyard. Solarpower1, NTC1, C10 and C13 sit 100% inside BAT1's 18650-holder silk body, and U3, R5 and R63 sit under U1's module silk. check_assembly says `buildable (blocking 0)` with `contained 7`.
  - Each containment prints `does not gate: a silk-drawn body (#896)`. No courtyard pair is formed (`courtyard_pairs` 0), so no channel gates.
  - CM5_MINIMA_3: CN1's pads sit 100% under the CM5 module's silk body, reported as advisory `pads_under_body`.
  - Repro: `python3 -X utf8 py_tools/check_assembly.py wk/gpm/07_One-Air-Max/repro/silk_body_inside.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/silk_body_inside.intent.json --baseline wk/gpm/07_One-Air-Max/fixed.kicad_pcb`
  - Control: a part that draws a courtyard, moved into BAT1 (`place_pose ... set LED2 125 70`), gates COURTYARD-BLOCKING. Only the silk-vs-silk case is blind.
  - History: under #1184 these BAT1 pairs gated, only through a 0.06 mm F.Fab dot. #1201 rejected the dot, and the drop was measured and flagged in #1201's comments without a decision.
  - Expected: a CLOSED silk outline that wholly contains another part's pads gates. Open corner brackets do not, which keeps the esp_prog SOT89 case #896 guarded.
  - Code: `py_placer/placement/legality.py:3245-3249`, `:3263`.
  - Cost: 07 failed the verifier and needed 14 parts repaired by hand plus a full re-route; 08 needed one re-route.
  - Secondary: DC1 overlaps the fixed I2C2 header by 4.83 mm² (I2C2 pin 4 inside DC1's housing), and that pair reads `waived:edge_class`.

### G11 -- VERDICT: CONFIRMED
- title: check_reachability ignores the board outline and certifies PASSABLE across mouse-bite rows; placement cannot see isolated outline regions
- boards: 15, 19   severity: high
- repro at bda59fa0:
  - 15: `check_reachability.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb --pad R26.2` -> `nearest other island 28.04mm away ... BOTTLENECK >= 69.21mm ... VERDICT PASSABLE`, exit 0.
  - 15: `route.py <same> wk/gpm/_verify/V7/G11/g11_route.kicad_pcb --nets CAN_SILENT` -> `ROUTE FAILED - no rippable blockers found`, `0/1 routed`.
  - 15: check_assembly `buildable`; check_floorplan `0 error(s)`.
  - 15 geometry, measured: holes r=0.3 at y=75 on a 1.0 mm pitch plus the 137.5-162.5 x 70-75 slot leave webs of 0.2-0.4 mm, against a 0.2 mm edge floor.
  - 19: re-ran `place_simple ... --clustered-seeds 6-11 --seed 7` (61 s). `region_check.py` -> 23 parts outside the run's region plan. 13 of them sit on the two frame strips that the x=80/82 drill columns isolate (0.5 mm drills at 0.8 mm pitch): C32, C33, C34, C5, C8, R3, U2 and SW4 on the bottom strip; D6, D7, D9, R17 and SW2 on the top strip. U2's +5V and +3V3 nets have pads on the main board. check_assembly `buildable`; check_floorplan `0 error(s)`.
- cause: `py_placer/placement/reachability.py:199-255` (`slack_field` rasterises segments, vias, copper pads and rule areas only; NPTH holes are skipped explicitly at `:232`; there is no Edge.Cuts or edge-clearance term anywhere in the file or in `check_reachability.py`). Sure. The placement side has no concept of copper-connectable regions; that is a missing feature, not a regression.
- head 0c05be08: unchanged.
- upstream: new. Related: #1031 (rule areas were added to reachability; this is the outline analogue), #628.
- issue draft:
  **check_reachability ignores the board outline, so it certifies a route across a mouse-bite row the router cannot cross, and no placement grader sees outline regions**
  - am32_esc: R26 sits north of a mouse-bite row whose webs are 0.2-0.4 mm against a 0.2 mm edge floor. check_reachability says `PASSABLE, bottleneck >= 69.21mm`, and route.py fails CAN_SILENT with `no rippable blockers`.
  - Repro: `python3 -X utf8 py_tools/check_reachability.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb --pad R26.2`, then `python3 -X utf8 py_router/route.py wk/gpm/15_am32_esc/repro/s8_island_north.kicad_pcb <fresh>.kicad_pcb --nets CAN_SILENT`
  - check_reachability is the instrument the skill names for "impossible" claims. Here it certifies a route the outline forbids.
  - Code: `slack_field` (`py_placer/placement/reachability.py:199-255`) models no Edge.Cuts and no edge clearance, and skips NPTH holes (`:232`).
  - icebreaker_v10e: a single place_simple seed (seed 7) puts 13 parts on frame strips that mouse-bite drill columns isolate. U2's +5V and +3V3 nets reach the main board. check_assembly says buildable and check_floorplan reports 0 errors.
  - Expected: reachability treats the outline, cutouts and NPTH holes as obstacles at the edge and hole clearances. Placement derives copper-connectable regions and refuses, or at least reports, a part whose nets cannot leave its region.
  - Cost: about 40 min and 4 placement passes on 19; about 15 min on 15.

### G12 -- VERDICT: CONFIRMED
- title: The edge_connector overhang reading sums every crossed side and off-board corner, so #1301's "an overhang of x reads x" is false
- boards: 02, 12   severity: high
- repro at bda59fa0:
  - 12 (`_superseded/12_steppenprobe/repro`): `check_floorplan.py seed2_placed.kicad_pcb --intent intent_run_J1band.json` -> `J1 north: overhang 2.5149mm [legacy_occupancy@margin=0] pass`. With J1 moved 2.2117 mm north (`seed2_J1moved`) -> `9.1500mm ... fail`. Both readings are exactly 3x the courtyard's overshoot past the north edge (0.838 and 3.050): the bbox term plus two off-board corner terms. The rounded outline makes the body reading abstain.
  - 02: re-ran `place_simple ... --intent intent.json --seed 0`, then check_floorplan -> `J2 east: overhang 4.1645mm pass; pad copper 5.3022mm vs 0.2mm pass; facing east pass`. Measured directly: J2's courtyard is flush with the declared EAST edge (x 183.70). The 4.16 is its flange past the NORTH edge, and 5.30 is pad copper to the north edge. The footprint's "PCB edge" line sits 14.2 mm inside the east edge and the pads 14.45 mm inside it, all graded pass.
  - 02: `out_literal` (min 14.2) -> `J1 west: overhang 14.2050mm pass; pad copper 2.5111mm`.
- cause: `py_placer/placement/connector_geometry.py:443-450` (`courtyard_overhang` = `rect_outside_amount`) and `py_placer/placement/legality.py:1257-1267` / `:1298-1357` (sum of per-axis overshoot plus per-corner ring distance). The body reading sums too (`connector_geometry.py:362`), and abstains on any non-rectangular outline. Used at `py_placer/placement/floorplan.py:4938/4952`. Sure. Correction to the cluster: the "PCB Edge" marker IS read since #1245, but only to confirm the facing, never for seat depth.
- head 0c05be08: unchanged.
- upstream: incomplete fix of #1301. Its resolution states "an overhang of x reads x" while quoting sonde J1 = 25.118, which is the summed 14.20 + 10.92. SKILL.md:337 repeats the claim. Related: #961, #1245, #1155, #987.
- issue draft:
  **edge_connector's overhang reading sums every side and off-board corner, so "an overhang of x reads x" (#1301) is false: 3x on rounded outlines, and another edge's overhang read as the mating edge's**
  - steppenprobe J1 (rounded outline): the courtyard is 0.838 mm past the north edge and the grade reads 2.5149 (3 x 0.838), pass. At the drawing's pose (3.05 mm past) it reads 9.15 and fails a 2.60 max.
  - Repro: `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/_superseded/12_steppenprobe/repro/seed2_placed.kicad_pcb --intent wk/gpm/_superseded/12_steppenprobe/repro/intent_run_J1band.json | grep "J1 north"` (and `seed2_J1moved`).
  - sonde_xilinx J2 (declared east): the seat leaves the courtyard flush with the east edge and the flange 4.16 mm past the NORTH edge. The grade prints `J2 east: overhang 4.1645 pass; pad copper 5.3022` (that 5.30 is to the north edge). The footprint's own "PCB edge" line sits 14.2 mm inside the east edge.
  - Repro: `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/02_sonde_xilinx/repro/out_given.kicad_pcb --intent wk/gpm/02_sonde_xilinx/repro/intent.json | grep "J2 east"`
  - Following SKILL.md §3.4 literally (min = real reach 14.2) seats sonde J1 with its pads 2.51 mm inside the edge instead of 0.245, graded pass.
  - Code: `connector_geometry.courtyard_overhang` (`:443`) -> `legality.rect_outside_amount` (`:1298`); the body reading sums at `:362`.
  - Expected: one signed distance past the DECLARED edge along its normal, with other-edge overshoot graded on its own. Use the marker line, when present, as the seat depth.
  - Fix the "x reads x" text at SKILL.md:337 and in the `courtyard_overhang` docstring.
  - Cost: 12 failed the verifier and every route was redone; 02 needed hand-measured bands.

### G20 -- VERDICT: CONFIRMED-PARTIAL
- title: Router tracks 2 µm inside the board-edge floor at Edge.Cuts arcs are accepted by check_drc's margin and subtracted by kicad_drc_compare as "#408 intentional edge"
- boards: 17 (holds, but by a different mechanism), 08 (holds as measured, but the condition comes from the human design)   severity: medium
- repro at bda59fa0:
  - 17 (copy `e17`): kicad-cli -> 5 `copper_edge_clearance` errors, tracks 0.1976-0.1978 mm from Edge.Cuts arcs against 0.2000. check_drc -> 0. kicad_drc_compare -> `[#408: -5 kicad / -5 check_drc intentional edge] CONSISTENT`, exit 0.
  - 17: check_drc `--json` shows all 5 as `accepted: quantization-margin` (overlap 2.2 µm, under 0.05 x 0.2). They are NOT `edge-exempt-pad`, so the cluster's mechanism is wrong. `--check-pad-edge` changes nothing; `--clearance-margin 0` reports all 5.
  - 08 (copy `r08`): kicad-cli -> 2 J1 shield-tab copper_edge_clearance errors. check_drc -> 0 by default and 2 with `--check-pad-edge`. board_score drc 0.
  - 08: kicad_drc_compare does NOT hide them (`kicad_only=4`, diverged, exit 1).
  - 08: the human board (`_truth/CM5_MINIMA_3/human.kicad_pcb`, J1 at the same pose) has the same 2 pad-edge hits. The footprint's 16.2 mm tab span is wider than the 15.79 mm notch.
- cause: `tests/stress/kicad_drc_compare.py:523-550`, `:1064-1067` (KiCad edge errors matched to ANY accepted check_drc edge item are dropped and counted as "intentional", including quantization-margin ones); `py_router/check_drc.py:5424-5436` (sub-margin edge grazes published as accepted, by #448's design). Router side, likely but not proven: Edge.Cuts arcs are linearised at `chord_eps=0.005` (`py_router/kicad_parser.py:2406`), so copper on an arc's convex side can land up to about 5 µm short.
- head 0c05be08: unchanged (`check_drc`, `kicad_drc_compare`, `kicad_parser` and `obstacle_map` untouched; `plane_obstacle_builder` changed for plane taps only).
- upstream: related #448 (the publish-accepted contract), #408, #438, #447. New as stated.
- issue draft:
  **route.py lays tracks 2 µm inside the board-edge floor at Edge.Cuts arcs; KiCad reports 5 errors, and kicad_drc_compare subtracts them as "#408 intentional edge"**
  - environment_sensor: KiCad reports 5 copper_edge_clearance ERRORS. They are GND and I2C tracks 0.1976-0.1978 mm from the L-slot and notch arcs, against 0.2000.
  - check_drc reports 0 and kicad_drc_compare reports CONSISTENT, labelling them `[#408: -5 kicad / -5 check_drc intentional edge]`.
  - Repro: copy `wk/gpm/17_environment_sensor/repro/edgearc_routed.kicad_pcb` with `copy_board.py`, then run `check_drc.py <copy> --json x.json` (5 items, `accepted: quantization-margin`), `kicad_drc_compare.py <copy>` and `kicad-cli pcb drc <copy> --refill-zones`.
  - These are not pad-covered edge items; they are sub-margin grazes. `check_drc --clearance-margin 0` reports all 5.
  - kicad_drc_compare drops every KiCad edge error that matches any accepted edge item (`kicad_drc_compare.py:523-550`, `:1064`), so a real KiCad error ships under the #408 label.
  - Router cause, likely: arcs linearised at a 5 µm sagitta (`kicad_parser.py:2406`). The workaround `--board-edge-clearance 0.22` gives KiCad 0 errors at the same 101 vias.
  - Expected: the router clears arcs at the exact floor. The compare tool reports quantization-margin subtractions separately from #408 intentional items, so a delivered board's KiCad errors are visible.
  - Not part of this issue: CM5_MINIMA_3's 2 J1 shield-tab hits come from the human design (same pose, same 2 hits), and kicad_drc_compare does flag them.

### G41 -- VERDICT: CONFIRMED
- title: A multi-pad `unconnected-*` net is skipped by the router and every DONE grader while KiCad reports it unconnected
- boards: 17   severity: medium
- repro at bda59fa0 (copy `mp`):
  - `check_connected.py` -> `ALL NETS FULLY CONNECTED!`, exit 0, with a WARNING that `'unconnected-(J2-PadMP)' (2 pads), 'unconnected-(J3-PadMP)' (2 pads)` were skipped.
  - board_score -> blocking 0, no mention of either net.
  - check_complete -> `DONE`, no mention.
  - kicad-cli -> 2 unconnected items, `Pad MP ... of J2` (197.65 / 203.25, 138.855) and J3 on B.Cu.
  - The human board joins both pairs (J2 1 segment, J3 6 segments) and KiCad reports 0 unconnected on it.
  - The file has no jumper-pad token. The parser keeps both pads on the net, so the cluster's "treated as a one-pad net" is wrong; the skip is by net name.
- cause: `py_router/check_connected.py:2109-2124` (auto-named no-connect nets skipped, #479; multi-pad ones only warned, #513 item 7); `py_router/net_queries.py:1155-1170` (`expand_net_patterns` drops them from wildcard routing). Sure.
- head 0c05be08: unchanged.
- upstream: related #479 (the skip) and #513 item 7 (the warning). New as a DONE-gate false-OK.
- issue draft:
  **A multi-pad `unconnected-*` net (a JST-SH's two MP tabs) is never routed and every DONE grader passes it, while KiCad reports it unconnected**
  - environment_sensor: J2 and J3 each carry two `MP` pads on `unconnected-(Jn-PadMP)`. KiCad DRC reports 2 unconnected items.
  - check_connected prints `ALL NETS FULLY CONNECTED!` (exit 0) with only a WARNING; board_score blocking 0; check_complete DONE.
  - Repro: copy `wk/gpm/17_environment_sensor/repro/mptabs_routed.kicad_pcb` with `copy_board.py`, then run `check_connected.py <copy>`, `check_complete.py <copy>` and `kicad-cli pcb drc <copy>`.
  - The human reference joins both pairs and grades 0 unconnected, which is the disambiguation the #513 warning asks for.
  - Cause: `check_connected.py:2109-2124` skips auto-named no-connect nets with no copper (#479). `net_queries.py:1155` removes them from `--nets '*'`, so the router never tries.
  - Expected: follow KiCad's rule. Join, or count as open, every multi-pad `unconnected-*` net, unless the footprint declares its same-number pads as jumpers.
  - Cost: about 10 min and two hand check_join tracks.

### G47 -- VERDICT: CONFIRMED-PARTIAL
- title: plan-pcb-routing advises `--thermal-relief`, which its own R07 refuses; kicad_drc_compare labels KiCad 10 PTH starved thermals as pad "?"
- boards: 04, 05, 19   severity: medium
- repro at bda59fa0:
  - 05 (copies `r05`, `in05`): `kicad_drc_compare.py r05 --baseline in05` -> `thermal=5 CONSISTENT`, exit 0, five rows `STARVED-THERMAL ? ['GND'] @ (193.675, 133.35)`, which is the zone corner.
  - 05: kicad-cli 10.0.7 -> 5 `starved_thermal` at error severity, items `PTH pad 10 [GND] of U2`, `PTH pad 12 of U8`, and `PTH pad G2/K3/L7 of U9`; unconnected 0.
  - 04 (`gap5_lap_loops` vs `final`): `thermal=3 CONSISTENT`, with pads named correctly (IC1.4, C12.1, IC4.4). The regex fails only on "PTH pad".
  - Skill: a plan containing `route_planes ... --thermal-relief` -> `FAIL R07 ... passes --thermal-relief, which the skill says to leave alone` (exit 4). SKILL.md:1468 tells the agent to add that flag.
- cause: `tests/stress/kicad_drc_compare.py:147` (`_THERMAL_PAD_RE` is case-sensitive `Pad`, from 7b0d386a for #1334). `.claude/skills/plan-pcb-routing/SKILL.md:1468` (added by 88a5a460 for #1329) contradicts `:1411` and `scripts/route_plan_check.py:267-276`, `:597` (R07). Sure.
- head 0c05be08: unchanged.
- upstream:
  - The regex is an incomplete fix of #1334, whose channel claims to list each pad.
  - The skill contradiction is new, introduced by #1329's fix text.
  - NOT A BUG: starved_thermal not gating DONE. @drandyhaas decided in #1334 that it is reported, not gated; reversing that is the owner's call.
- issue draft:
  **plan-pcb-routing tells the agent to add `--thermal-relief`, which its own R07 refuses; kicad_drc_compare names every KiCad 10 PTH starved thermal as pad "?" at the zone corner**
  - SKILL.md:1468 (from #1329's fix) says to add `--thermal-relief` to keep a designer's relief pour. SKILL.md:1411 and `route_plan_check.py` R07 (`:267-276`) refuse that flag.
  - So a plan cannot re-pour a hand-soldered board's relief pour and keep its reliefs. On interf_u the agent kept the designer's pour instead, which left 5 KiCad starved_thermal errors.
  - Repro (skill): run `route_plan_check.py` on a plan containing `route_planes.py ... --thermal-relief` -> `FAIL R07`.
  - Repro (label): copy `wk/gpm/05_interf_u/routed.kicad_pcb` and `final_route/in.kicad_pcb` with `copy_board.py`, then run `kicad_drc_compare.py <routed copy> --baseline <in copy>`. It prints 5 rows `STARVED-THERMAL ? @ (193.675, 133.35)`, while KiCad names `PTH pad 10 [GND] of U2`, U8.12 and U9.G2/K3/L7.
  - Cause: `_THERMAL_PAD_RE = r"Pad\s+..."` (`kicad_drc_compare.py:147`) misses KiCad 10's lower-case `PTH pad`. SMD `Pad` rows (multichannel_mixer IC1.4) resolve.
  - Expected: `re.IGNORECASE` (or `(?:PTH )?[Pp]ad`) and the pad's own position. R07 either allows `--thermal-relief` when the plan replaces a designer's relief pour, or SKILL.md:1468 is changed to match R07.
  - Out of scope: whether starved_thermal gates DONE was settled by the owner in #1334 (report only).

V7: CONFIRMED 4, PARTIAL 2, NOT A BUG 0, NOT REPRODUCIBLE 0

<!-- batch V8 -->
### M01 -- VERDICT: CONFIRMED
- title: The placement writer crashes on KiCad 6/7's `(at x y unlocked)` text form, so piling or rotating such a part dies with a traceback
- boards: 11 (daplink source); 16 (esp_rust_board source also has 6 such tokens, but only on pad-less artwork that does not move)   severity: medium
- repro at bda59fa0: `copy_board.py wk/gpm/_src/daplink/orig/daplink.kicad_pcb V8/M01/src.kicad_pcb`, then `strip_copper_only.py`, then `make_unplaced.py V8/M01/s.kicad_pcb V8/M01/p.kicad_pcb` -> EXIT 1, `ValueError: could not convert string to float: 'unlocked'` at writer.py:296. `place_pose.py s.kicad_pcb pp.kicad_pcb rotate P1 180 --force` -> the same ValueError, EXIT 1. A pure move (`set P1 104 110 --rot 270`) works (EXIT 0). With the token changed to the 4-token form `(at x y 0 unlocked)`, make_unplaced still dies, on an uncaught `SideFlipUnsupported` ("expected two or three plain numbers").
- cause: sure. `py_placer/placement/writer.py:274`: `_TEXT_AT` captures `unlocked` as the angle group, and `rotated()` at :296 calls `float(a)` on it. The 4-token form does not match the regex, so :346-353 raises. `_flip_at_angle` (:641-666) refuses the 4-token form on purpose; the rotate path has no handling for either form.
- head 0c05be08: unchanged (writer.py is not in bda59fa0..upstream/main).
- upstream: new. Related: #1163 (pile text angles) and #714 (flip refusal).
- issue draft:
  **Placement writer crashes on a KiCad 6/7 text `(at x y [a] unlocked)` when it rotates a footprint**
  - KiCad 6/7 writes a free-orientation footprint text as `(fp_text reference "P1" (at -5.987 2.555 unlocked) ...)` or `(at 0 5 -90 unlocked)`.
  - `_rotate_text_angles` reads `unlocked` as the angle: `ValueError: could not convert string to float: 'unlocked'` (writer.py:296). The 4-token form instead raises `SideFlipUnsupported` (writer.py:346-353).
  - Every write that rotates such a part fails: `make_unplaced` (the pile) and `place_pose rotate` both exit 1 with a traceback. place_simple and place_seed go through the same writer.
  - Repro: `strip_copper_only.py wk/gpm/_src/daplink/orig/daplink.kicad_pcb s.kicad_pcb && make_unplaced.py s.kicad_pcb p.kicad_pcb`, or `place_pose.py s.kicad_pcb o.kicad_pcb rotate P1 180 --force`.
  - Expected: parse `[angle] [unlocked]` after x y and keep the `unlocked` keyword in place, so the angle composes as it does for KiCad 10 texts.
  - Hit on daplink (4 tokens). The campaign worked around it by re-saving the board through pcbnew 10.

### M02 -- VERDICT: CONFIRMED-PARTIAL
- title: make_unplaced cannot remove a KiCad 6 footprint lock (`(footprint "X" locked (layer ...))`), so the pile ships the part moved off the board and still locked
- boards: 16 (esp_rust_board U4), 18 (uecg E+1/E-1); 12 for the pad-lock aspect, which does not hold   severity: medium
- repro at bda59fa0: `strip_copper_only.py` then `make_unplaced.py` on `wk/gpm/_src/{esp_rust_board,uecg}/orig/*.kicad_pcb` (outputs in V8/M02/<board>/) -> EXIT 1, `FAIL: meant to unlock ['U4'], unlocked [], still locked ['U4']` (uecg: `['E+1','E-1']`). The pile is written anyway. Parsed pile: U4 `locked=True` at (147.29, 155.74), with the board ending at y 128.5. E+1/E-1 `locked=True` at y 120.77, with the board ending at y 111.0. All three are off the board and locked, and placement never moves a locked part.
  - Pad-lock aspect, not a bug: on steppenprobe the run exits 0 and 312 `(pad "N" smd rect locked ...)` tokens remain. But the parser deliberately ignores pad locks when it decides whether a part is locked (kicad_parser.py:4546-4556), so every part stays movable. The docstring promises unlocked parts, not unlocked pads, and a pad flag carries no pose.
- cause: sure. `.claude/skills/plan-pcb-placement/scripts/make_unplaced.py:186-189`: `_unlock` removes only a `(locked yes)` child line. The parser reads KiCad 6's bare head flag through `footprint_head_flags` (kicad_parser.py:4555-4556), so the part reads as locked but is never unlocked. By code reading (not measured), the 20210108-20210423 `(locked)` child is not removed either. The failed check runs after `write_placed_output` (:259-262), so the pile is already written when it fails.
- head 0c05be08: unchanged (make_unplaced.py and kicad_parser.py are untouched).
- upstream: new. Related: #1305 (KiCad 6 `locked` pad rotation, fixed; the pile's pads now rotate correctly).
- issue draft:
  **make_unplaced leaves a KiCad 6 footprint lock in place: the pile ships the part moved off the board and still locked**
  - KiCad 6 (20211014) writes a footprint lock as a bare head flag: `(footprint "Rust_Board:Rust_Board" locked (layer "F.Cu")`.
  - `_unlock` (make_unplaced.py:181-197) removes only a `(locked yes)` child. The parser reads the bare flag, so the verify step prints `FAIL: meant to unlock ['U4'], unlocked [], still locked ['U4']` and exits 1.
  - By then the pile is written. U4 sits at (147.29, 155.74), 27 mm south of the outline, still locked. No placement tool moves a locked part, so it stays there.
  - Repro: `strip_copper_only.py wk/gpm/_src/esp_rust_board/orig/esp-rust-board.kicad_pcb s.kicad_pcb && make_unplaced.py s.kicad_pcb p.kicad_pcb`. The same happens on uecg (E+1, E-1).
  - Expected: remove the bare head flag (and the `(locked)` child) too, or refuse before writing.
  - Not in scope: KiCad 6 pad-level `locked` tokens (312 on steppenprobe) are ignored by the parser's lock test and carry no pose.

### M03 -- VERDICT: CONFIRMED
- title: The outline-owner classification depends on the part's current pose: a part carrying a milled window is "structural" once it is off the board, so it can neither be piled nor moved back on
- boards: tfgps01 (replaced in the campaign; D3-D7 `Mlab_D:LED_1206_mill`)   severity: medium
- repro at bda59fa0: `strip_copper_only.py wk/gpm/_src/tfgps01/TFGPS01.kicad_pcb` then `make_unplaced.py` -> EXIT 1, `OutlineOwnerMove: this write would have CHANGED THE BOARD OUTLINE`.
  - Probe (`V8/M03/probe_owners.py`) of the two fingerprint calls: BEFORE, D3-D7 are all `carried`; AFTER, all five are `STRUCTURAL`.
  - `place_pose set D3 130 100` (inside the board) -> EXIT 0. `set D3 145 135` (off the board) -> EXIT 4, the same refusal.
  - The second leg: I built the pile with the tripwire disabled in memory only (`pile_bypass.py`), then ran `place_pose set D3 126.2035 94.994` back to its human pose -> EXIT 4, `D3 draws the board outline (Edge.Cuts geometry outside the board-level outline), so moving it would resize the board`.
- cause: sure. `py_router/kicad_parser.py:3262` (`classify_outline_owners`: `out[ref] = not all(inside(*p) ...)`) judges containment at the footprint's current pose. `structural_outline_fingerprint` (:3153-3175) and the parser's `owns_board_outline` both read it. The writer's tripwire at `writer.py:1343-1356` compares the BEFORE and AFTER fingerprints.
- head 0c05be08: unchanged.
- upstream: new. Related: #829 (the classification rule) and #1074.
- issue draft:
  **A footprint-carried Edge.Cuts window is reclassified as board outline once its part is off the board: the pile fails, and a part already off the board cannot come back**
  - #829 calls a footprint's closed Edge.Cuts ring "carried" only while the ring lies inside the outline. That is judged at the part's current pose (kicad_parser.py:3262).
  - make_unplaced on tfgps01 (D3-D7 `LED_1206_mill`, each drawing a milled window): the AFTER text classifies all 5 as STRUCTURAL, so the fingerprint changes and the writer raises `OutlineOwnerMove` (writer.py:1343-1356). Nothing is written.
  - On a pile made by any other means, `owns_board_outline` is already True. `place_pose set D3 <its human pose>` then refuses: "D3 draws the board outline ... moving it would resize the board".
  - Repro: `strip_copper_only.py wk/gpm/_src/tfgps01/TFGPS01.kicad_pcb s.kicad_pcb && make_unplaced.py s.kicad_pcb p.kicad_pcb`.
  - Expected: decide carried vs structural once, on the input board (or on the footprint's local geometry). Two writes of the same part should not classify it differently because it moved.
  - Any board with part-carried reliefs is affected (#628: crkbd's 184 LED windows).

### M04 -- VERDICT: CONFIRMED
- title: route.py/route_diff.py: a missing input board and a `--power-nets`/`--power-nets-widths` length mismatch end in raw tracebacks, and a shell-joined flag word inside `--nets` is routed at exit 0
- boards: 07, 09, 12, 14   severity: low
- repro at bda59fa0 (V8/M04/):
  - (a) `route.py does_not_exist.kicad_pcb x.kicad_pcb --nets '*'` -> it prints the #441 "NO .kicad_pro" banner, then `FileNotFoundError` from `parse_kicad_pcb` (route.py:9606), EXIT 1. route_diff does the same.
  - (b) `route.py diff_in.kicad_pcb o.kicad_pcb --nets GND --power-nets GND +3V3 --power-nets-widths 0.5` -> traceback `ValueError: --power-nets (2) and --power-nets-widths (1) must have same length` (route.py:2962, inside `batch_route`), EXIT 1.
  - (c) `route.py diff_in.kicad_pcb o.kicad_pcb --nets /VPLL '--layer-costs 1.0 1.5'` -> `WARNING: Net '--layer-costs 1.0 1.5' does not exist`, `Routing 2 nets`, default `Layer costs: F.Cu=1.0x, B.Cu=3.0x`, routed 1, EXIT 0. route_diff does the same (EXIT 0).
- cause: sure. There is no existence or length validation in the CLI `main()`s. argparse treats a word that contains a space as positional, so `--nets` (nargs='+') swallows it, and `net_queries.py:1296-1303` only warns about an unknown literal.
- head 0c05be08: unchanged.
- upstream: new. Related: #597 (dash-prefixed net names such as `-3V3` must stay legal, so a fix must not refuse every token that starts with `-`).
- issue draft:
  **route.py CLI: raw tracebacks for a missing board and mismatched power-net widths; a joined flag word in --nets routes silently at exit 0**
  - A missing input board: route.py prints the #441 project banner, then a `FileNotFoundError` traceback (route.py:9606), EXIT 1. route_diff does the same.
  - `--power-nets` with N patterns and `--power-nets-widths` with M != N: a `ValueError` traceback from `batch_route` (route.py:2962), EXIT 1, rather than an argparse error (exit 2).
  - `--nets '*' '--layer-costs 1.0 1.5'` (zsh passed the flag as one word): argparse keeps it as a net name, route.py warns "does not exist", routes at the default layer costs and exits 0. route_diff does the same.
  - Repro: `route.py wk/gpm/_verify/V8/M04/diff_in.kicad_pcb o.kicad_pcb --nets /VPLL '--layer-costs 1.0 1.5'`.
  - Expected: a one-line refusal at exit 2 for a missing input and for a length mismatch (checked in `main()`, so the engine's ValueError stays as the GUI's guard). Also refuse a `--nets` token whose first word is one of the parser's own option strings. Dash-digit names (#597) stay legal.

### M05 -- VERDICT: CONFIRMED
- title: bga_fanout `--check-for-previous` treats a net as already fanned only when a track ends within 0.05 mm of the ball centre: off-centre routes are re-fanned, and other nets' dog-bone vias land on their tracks
- boards: 14   severity: medium
- repro at bda59fa0: `bga_fanout.py V8/M05/in.kicad_pcb --output out.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' '!VMEM' --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 -1 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 --track-width 0.1 --clearance-ceiling 0.1 --escalation board --check-for-previous` -> `requested 46, escaped 46, failed 0`, `3 already-fanned skipped`. JSON `drc_grazes.via_segment 3` is its only sign.
  - `check_drc out.kicad_pcb --clearance-margin 0.1 --nets /DRAM/DRAM_DQ7` -> 6 violations: 3 VIA-SEGMENT (all in contact, DQ8/DQM0 vias at (71.6, 106.6) and (72.4, 106.6) on DQ7's lane) and 3 SEGMENT-SEGMENT.
  - Why: DQ1, DQ2, DQ5, DQ6 and DQ7 are already routed, but their tracks start 0.200 mm from the ball centre, inside the 0.41 mm ball. So they are not "fanned", and each is re-escaped (11 new segments each on DQ2/5/6/7). Their existing copper is also left out of the occupancy grid.
  - Causal test: the same run with only `TOL = 0.25` in a patched copy (`V8/M05/run_patched.py`) -> `8 already-fanned skipped`, DQ7 0 violations. Whole board: SEGMENT-SEGMENT 11->2, VIA-SEGMENT 3->0, LENGTH-OUT-OF-RANGE 3->0, total 146->129 (the input has 102).
- cause: sure. `py_router/bga_fanout/underpad.py:857-867` (an endpoint within `TOL = 0.05` of a pad centre means "fanned"), combined with `:1173-1179`: segments of nets in `route_net_ids` are skipped as "our own future nets". The channel path has the same centre-point rule (`reroute.py:753`, `constants.py:8 FANOUT_DETECTION_TOLERANCE = 0.05`).
- head 0c05be08: unchanged (bga_fanout/ is untouched).
- upstream: related to #1315 (same symptom, different cause: #1315's `segment_reaches_window` fix, ab61c20b, is in the pin and holds here). Not a regression.
- issue draft:
  **bga_fanout --check-for-previous misses routes that end off a ball's centre: it re-fans them and lays foreign dog-bone vias on their tracks (shorts, failed 0)**
  - The under-pad/dog-bone engine marks a net as fanned only when a segment endpoint is within 0.05 mm of one of the BGA's pad centres (underpad.py:857-867).
  - On imx6ulz U2, DQ1/2/5/6/7 were routed by route.py and start 0.200 mm off-centre, inside their 0.41 mm balls. They are treated as unfanned, re-escaped (11 new segments each), and their existing copper is dropped from the obstacle grid as "our own future nets" (:1173).
  - Result: DQ8's and DQM0's gap vias sit on DQ7's F.Cu lane. check_drc finds 3 VIA-SEGMENT in contact and 3 SEGMENT-SEGMENT, LENGTH-OUT-OF-RANGE goes 0->3, and the run reports `failed 0`.
  - Repro: the command in board 14's TOOL_GAPS §10 on `wk/gpm/14_imx6ulz_4l/repro/u2_fanout_input.kicad_pcb`, then `check_drc.py <out> --clearance-margin 0.1 --nets /DRAM/DRAM_DQ7`.
  - Causal check: a 0.25 mm tolerance gives 8 fanned nets skipped and 0 DQ7 violations.
  - Expected: "fanned" should mean a same-net segment end inside the pad's copper (pad shape), not within 0.05 mm of its centre. The same applies to `find_existing_fanouts` (FANOUT_DETECTION_TOLERANCE).
  - #1315's fix (start-point window filter) is a different hole in the same filter.

### M06 -- VERDICT: CONFIRMED
- title: The edge seat measures its seat depth at the edge's midpoint only. On a notched edge it sets DC1 9.3 mm inside the real edge, where the fixed BAT1 blocks every position.
- boards: 07   severity: medium
- repro at bda59fa0: `place_simple.py V8/M06/notch_seat.kicad_pcb s0.kicad_pcb --groups notch_seat.groups.json --intent dc1_west.intent.json --seed 0` -> `DC1 ... no room along the south edge: of the 188 positions tested, 145 refused by the declared-pose check against BAT1, 32 ..., 11 ...`. 12 of the 12 recorded seed logs carry the same warning, and the seat runs before the anneal, so it is seed-independent.
  - Trace (`trace_seat.py`): every tested position is at rot 90 and y = 108.665. DC1's rect there spans y 103.92-113.52, against a south edge at y 122.82.
  - The outline: the south edge has notches at x 141.09-151.09 (up to y 113.82), 124.18-128.18 and 110.84-112.87. The sampled midpoint, x 146.26, lies in the deepest notch, so the seat line is that notch's bottom (113.82) minus the 0.3 mm margin.
  - Causal test: sampling at x 172 instead (`SHIFT_ALONG=172`) gives a seat line at y 117.665 and `edge connector DC1 on the south edge`.
  - The seed-0 anneal pose (170.746, 117.39, 0) passes the seat's own `_fixed_pose_check` ('contained', no conflicts).
  - The `dc1_west` repro grades `[ERROR] edge_connector: DC1 sits nearest the west edge`.
- cause: sure. `py_placer/placement/edge_seat.py:533` calls `_seat_coord(..., (lo + hi) / 2.0, aim)`: one sample along the edge. `_seat_coord` (:263-305) reads the band and copper limit at that one `along`, and `_free_stretches` (:310) then scans the whole edge at that single depth.
- head 0c05be08: unchanged (edge_seat.py is untouched; c4e6e916 changes the anneal budget only).
- upstream: related to #1325. Its fault (b) fix reads the outline "where the part stands", but where it stands is only the edge's midpoint. Not one of #1325's three faults, so this is not a regression. Same root cause as board 07 §3 (U1 seated at the north notch's depth): merge the two.
- issue draft:
  **Edge seat on a notched edge: the seat depth is measured at the edge's midpoint and used along the whole edge**
  - `seats()` computes one seat coordinate per rotation, `_seat_coord(..., (lo+hi)/2, ...)` (edge_seat.py:533). The position along the edge is fixed at the midpoint, and `_free_stretches` scans every position at that depth.
  - One-Air-Max's south edge (y 122.82) has a 10 x 9 mm notch at x 141.09-151.09, and the midpoint (x 146.26) falls inside it. DC1 is seated at y 108.665 (rect bottom 113.52, 9.3 mm inside the real edge), where BAT1's courtyard refuses 145 of the 188 positions.
  - The warning names BAT1, which hides the real cause. DC1 is then "placed as any other part", and 5 of 12 seeds grade `[ERROR] DC1 sits nearest the west edge`.
  - The anneal's own south seat (seed 0, (170.75, 117.39)) passes the seat's `_fixed_pose_check`, so a seat exists.
  - Repro: `place_simple.py wk/gpm/07_One-Air-Max/repro/notch_seat.kicad_pcb o.kicad_pcb --groups .../notch_seat.groups.json --intent .../dc1_west.intent.json --seed 0`.
  - Causal check: sampling at x 172 gives seat y 117.665 and DC1 seats.
  - Expected: compute the seat depth per tested position (or per straight run of the edge), not once at the midpoint. Board 07 §3 (U1 6.4 mm inside the north edge) is the same defect.

### M07 -- VERDICT: CONFIRMED-PARTIAL
- title: place_simple refuses declared mouse-bite NPTH drills that straddle the outline (16 per seed, exit 4), and accepts 16 identical ones on slot contours its gate does not model
- boards: 19   severity: low
- repro at bda59fa0: `place_simple.py V8/M07/icebreaker_v10e.kicad_pcb p1_s7.kicad_pcb --groups groups_pass1.json --intent intent.json --clustered-seeds 6-11 --seed 7 --json p1_s7.json` -> 16 x `declared pose is not legal: 1 of 1 drill hole(s) past the outline`, EXIT 4. check_assembly reports buildable.
  - Measured on the output (`drill_vs_outline.py`, `probe_gate.py`): 32 of the 58 declared 0.5 mm drills have their centre exactly on an Edge.Cuts edge. The 16 refused ones lie on the outer outline or on the 2 cutouts the `BoardOutlineGate` models. The 16 accepted ones straddle the other 3 slot contours, which the gate keeps as milled rings whose interior is not off-board (#291).
  - (b) is not a bug as stated. On `old/pass2/s9`, check_assembly reports 10 `GATES` drill pairs (NOT BUILDABLE). 5 of the 10 drills are within the 0.25 mm NPTH hole clearance of the socket's pad copper, and 2 cut into it: J31/REF**~20 -0.035 mm, J33/REF**~13 -0.184 mm. check_assembly's own hole channel only echoes these ("7 hole conflict(s)", blocking 0), so the courtyard gate is the only thing that refuses that board. The other 5 put a perforation drill under a 2.54 mm socket body.
  - The SKILL §3.1 sentence is accurate for marker pairs: an unlocked mount_hole + fiducial pair is waived (legality.py:2490-2492). It is only loose about mount_hole + mount_hole pairs, which are never waived.
- cause: sure for (a). `py_placer/placement/seeder.py:399-426` (`_holes_outside` exempts a castellated half-hole only), called from the overhang branch at :743/:756. The inconsistency comes from `legality.BoardOutlineGate` (legality.py:893-930), which treats `board_edge_contours` interiors as on-board.
- head 0c05be08: unchanged.
- upstream: related to #1297. Its fix judges holes on the drill circle and exempts castellated pads only, by design, so this is not a regression. New.
- issue draft:
  **Declared mouse-bite drills on the outline are refused in every seed (exit 4), and the gate judges identical drills differently by slot type**
  - icebreaker_v10e declares 58 `pkl_mechanical:Drill_0.5mm` NPTH perforations (mechanical.json). 32 have their centre exactly on an Edge.Cuts edge, as a mouse-bite needs.
  - `_fixed_pose_check`'s overhang branch counts a straddling drill as "past the outline" (`_holes_outside`, seeder.py:399-426, castellated exemption only). 16 are refused in every seed, and place_simple exits 4 although check_assembly calls the board buildable.
  - The other 16 straddling drills are accepted only because they lie on slot contours the `BoardOutlineGate` keeps as milled rings (interior on-board, #291). The same 0.5 mm hole on the same kind of edge gets two verdicts.
  - Repro: `place_simple.py wk/gpm/19_icebreaker_v10e/repro/icebreaker_v10e.kicad_pcb o.kicad_pcb --groups .../groups_pass1.json --intent .../intent.json --clustered-seeds 6-11 --seed 7`; `grep -c "declared pose is not legal"` gives 16, and the exit is 4.
  - Expected: a copper-less NPTH drill whose hole straddles the outline at its declared pose should be exempt, as a castellated half-hole is. At the least, all straddling drills should get the same verdict.
  - Not in scope: the courtyard gate on drills under sockets. On the board 19 repro it is the only check that refuses drills cut into socket pads.

### M08 -- VERDICT: CONFIRMED
- title: route.py ships same-net vias below the drill hole-to-hole floor and says nothing: when the #230 guarded retry fails, it silently keeps the flawed path
- boards: 10 (+3V3, cause still live), 08 (GND, fixed at head)   severity: medium
- repro at bda59fa0:
  - Board 10, re-run: the recorded route step on `final_route_old2/4_diff` (copied to V8/M08/g4_diff), 411 s -> `check_drc g5_route.kicad_pcb --clearance-margin 0.1` gives VIA-DRILL-HOLE +3V3 (91.30, 85.70)/(91.50, 85.80), overlap 0.176 mm. Both vias are 0.3/0.15, centres 0.2236 mm apart. The drills do not touch (0.074 mm gap), but they are under the 0.25 floor. `g5_route.json` and the log never mention it.
  - Instrumented re-run (`trace_guard.py`): `_path_has_close_vias` flags exactly this pair on net 2 (+3V3); the guarded retry (`ver 3`) returns `connected: false`; the unguarded path ships.
  - Board 08: `check_drc v3_s4_tidy.kicad_pcb` gives VIA-DRILL-HOLE GND (85.25, 53.20)/(85.20, 53.15), overlap 0.479 mm. Centres are 0.0707 mm apart and the 0.3 mm drills physically overlap. They are joined by a 0.8 mm In2 segment. The run log shows `KiCad-oracle recheck round 1: GND: (85.25,53.20)<->(74.99,20.22) OK 38 seg(s), 2 via(s), w=0.80mm`, so the oracle reconnect's width-upgrade link laid them.
- cause:
  - Board 10, sure: `py_router/single_ended_routing.py:1586-1603`. `_probe_route_with_frontier` returns the first (DRC-flawed) result when the guarded re-route fails to connect, with no print and no summary key. The guard radius `ceil((drill+h2h)/grid/2)` = 3 cells blocks within 0.6 mm (Chebyshev) where 0.45 mm is required, which likely makes the retry harder than it needs to be.
  - Board 08, sure: `kicad_oracle.oracle_reconnect` never compared a link's own new vias with each other.
- head 0c05be08: changed for board 08. 6027937e holds a link's new vias to `drill + hole_to_hole` and folds or bridges a close one; read from the diff, not run. Unchanged for board 10 (single_ended_routing.py is untouched).
- upstream: incomplete fix of #230 (its two-pass fix keeps the flawed path when the retry fails, and nothing discloses that). Board 08's instance has no issue and is fixed by 6027937e. Related: #1341 and #1070.
- issue draft:
  **route.py keeps a path with two same-net vias closer than the drill floor when the #230 guarded retry fails, and reports nothing**
  - #230 made `_probe_route_with_frontier` re-route a leg with the via-spacing guard on when its path drops two own vias closer than `via_drill + hole_to_hole`. If that retry does not connect, the function returns the flawed path (single_ended_routing.py:1601-1603).
  - glasgow_revC route step (`--via-size 0.45 --via-drill 0.2`, h2h 0.25): +3V3's route flags vias (91.3, 85.7)/(91.5, 85.8), 0.224 mm apart. The guarded retry fails, and the pair ships.
  - check_drc then reports VIA-DRILL-HOLE (overlap 0.176 mm), KiCad grades hole-to-hole, and route.py's console and `--json-out` say nothing.
  - Repro: re-run `wk/gpm/10_glasgow_revC/final_route_old2/redo_commands.sh` line 16 on a copy of `4_diff.kicad_pcb` (about 7 min), then `check_drc.py <out> --clearance-margin 0.1`. It is deterministic: 2 of 2 runs.
  - Expected: when the guarded retry fails, merge or fold the close via pair (as 6027937e now does for oracle links), or try a larger via rung. At the least, name the pair in JSON_SUMMARY and the console. Also consider sizing the guard on true distance, not a 2*radius Chebyshev box (0.6 mm where 0.45 mm is needed).
  - The sibling producer on CM5 (oracle width-upgrade link, two GND vias 0.071 mm apart) is fixed at 0c05be08 by 6027937e.

V8: CONFIRMED 6, PARTIAL 2, NOT A BUG 0, NOT REPRODUCIBLE 0

All repro outputs, logs and probe scripts are under `wk/gpm/_verify/V8/<Mnn>/`. Nothing was written outside that tree.

<!-- batch V9 -->
I re-ran all eight items at bda59fa0. Five are confirmed (M09, M10, M12, M13, M16) and three hold only in part (M11, M14, M15). None was refuted outright. Head 0c05be08 does not touch any of the code or skill files involved (`git diff --stat bda59fa0 upstream/main` over those paths is empty). All evidence is under `wk/gpm/_verify/V9/<Mnn>/`.

### M09 -- VERDICT: CONFIRMED
- title: `--no-fix-drc-settings` also skips the #521 protected-nets record (and the #581 same-net-pad record), so a later route.py re-routes the pair
- boards: 12   severity: m
- repro at bda59fa0: I replayed board 12's chain from `_superseded/12_steppenprobe/final_route/step1.kicad_pcb` in two arms. Arm A ran `route_diff.py ... --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --escalation board`. Arm B ran the same command without the flag. Both arms then ran the recorded pwr1 and sig1 `route.py` steps -> arm A: `kicad_routing_tools` is None and the .kicad_pro is byte-identical to the input; 35 of 103 pair segments survive sig1. Arm B: `protected_nets {'/USB_DP','/USB_DM': 'diff-pair'}` and `same_net_pad_clearance 0.1` are recorded, the log prints "seam re-ask skipped: /USB_DM is protected", and 75 of 103 survive. This matches the board's 35/75 exactly.
- cause: `py_router/route_diff.py:3048-3085` and `py_router/route.py:10099-10134`. The `persist_protected_nets` / `persist_impedance_specs` / `persist_same_net_pad_clearance` block sits inside `if not args.no_fix_drc_settings`. Sure. The GUI diff tab has the same coupling: its record is consumed inside `update_live_drc_floors`, which only runs under `fix_drc_settings` (`differential_gui.py:1518`). That GUI part is from reading the code, not measured.
- head 0c05be08: unchanged
- upstream: new; related #521 (the protection), #1286 (the same class of fault: the flag skipped non-DRC work, fixed there for the sibling files only), #1285/#1319 (the floor lowering that pushes chains onto this flag)
- issue draft:
  **`--no-fix-drc-settings` drops the #521 protected-nets record, so the next route.py rips and re-routes a routed diff pair**
  - The help says only "Do not adjust the output's .kicad_pro DRC constraints", yet route_diff then records no `protected_nets`, `net_impedance` or `same_net_pad_clearance`.
  - Measured on steppenprobe (board 12 chain, step1 -> route_diff -> pwr1 -> sig1): with the flag, `kicad_routing_tools` is None and 35/103 pair segments survive sig1. Without it, the pair is recorded and 75/103 survive.
  - Repro (WT): `python3 -X utf8 py_router/route_diff.py <step1> out.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --no-fix-drc-settings`, then `python3 -c "import json;print(json.load(open('out.kicad_pro')).get('kicad_routing_tools'))"` prints None.
  - No flag gives both: chains use `--no-fix-drc-settings` to stop the floor writeback lowering `min_hole_clearance` (0.25 -> 0.15), and doing so silently voids the protection.
  - Cause: the persist block at route_diff.py:3066-3085 and route.py:10116-10134 is nested in the `if not args.no_fix_drc_settings` writeback gate. The GUI diff tab consumes its candidates inside `update_live_drc_floors`, which is also gated on the checkbox.
  - Expected: the tool records (protected nets, impedance, same-net-pad clearance) are written on every successful run, independent of the DRC-floor writeback, as #1286 did for the sibling files.

### M10 -- VERDICT: CONFIRMED
- title: fit_template takes `--intent` but never checks members against its `decaps` limit, so the row it writes puts C9 at 5.76 mm from U2 against a 4.24 mm limit
- boards: 20   severity: l
- repro at bda59fa0: the item's own command exits 2 as written (`--intent and --write-intent go together`). Corrected command: `python3 -X utf8 py_tools/fit_template.py wk/gpm/20_sam9g25/repro/fixed.kicad_pcb --sketch wk/gpm/20_sam9g25/repro/u2_sketch_v1.json --intent wk/gpm/20_sam9g25/repro/intent_given.json --write-intent V9/M10/intent_with_row.json -o V9/M10/u2_row_v1.json` -> exit 0. It prints `C9 at (-1.317, +8.223) ... (4.86 mm off the chip)` and only a ground-return NOTE. I then seated all 16 members exactly at the template on pass-1 seed s0 (`place_pose set ... --force`, template graded "as drawn, worst 0.00mm") and ran `check_floorplan --intent old/pass1/intent_run.json` -> exit 4 with `[ERROR] decap_ungraded: C9 is 5.76mm from U2 ... beyond the 5.00mm tether search radius ... 4.24mm limit. The reference board keeps it WITHIN that radius`.
- cause: `py_tools/fit_template.py:196-212` (the intent is only appended to and load-checked). `py_placer/placement/templates.py:365` (`fit` has no decap term; it minimises leg gaps only). The intent's `decaps.max_distance_mm` / `within_radius_refs` are never read. Sure.
- head 0c05be08: unchanged
- upstream: new; related #1142 (held caps are ERROR), #1150
- issue draft:
  **fit_template writes a template row whose members violate the decap limit of the intent it was given**
  - fit_template accepts `--intent` and writes the row into it, but never compares members against that intent's `decaps.max_distance_mm` / `decaps.within_radius_refs`.
  - On sam9g25 (U2 MCP16501 sketch), it seats C9 at template (-1.317, +8.223), printing only "4.86 mm off the chip" and a ground-return NOTE.
  - With every member exactly at the template on a pass-1 seed, check_floorplan grades `decap_ungraded` ERROR: C9 is 5.76 mm from U2 against a 4.2375 limit, and C9 is in `within_radius_refs`. That was 7 of 12 pass-1 seeds; the cost was a placement pass.
  - Repro (WT): the fit_template command above, then `place_pose` the row onto `wk/gpm/20_sam9g25/old/pass1/s0.kicad_pcb` and `check_floorplan --intent wk/gpm/20_sam9g25/old/pass1/intent_run.json`.
  - Expected: when `--intent` is given, fit_template measures each member it seats with the grade's own tether metric. It should refuse, or WARN by name, for a held cap that ends beyond `max_distance_mm` or the 5 mm radius. Better, it could treat that limit as a constraint in `templates.fit`.
  - Code: py_tools/fit_template.py:196-212; py_placer/placement/templates.py:365 (fit).

### M11 -- VERDICT: CONFIRMED-PARTIAL
- title: the datasheet step (§3.5) depends on poppler; nothing in the repo reads a PDF, and the skill names no fallback
- boards: 02 03 04 06 07 08 09 13 14 15 16 17 18 20   severity: m
- repro at bda59fa0: `V9/M11/probe.txt`.
  - Holds: pdftoppm, pdftotext, pdfimages, mutool, qpdf and gs are all absent. fitz, pypdf, PyPDF2, pdfplumber and pdfminer are absent from both the venv and KiCad's Python. `requirements.txt` has no PDF package. Read with `pages="1"` on `07_One-Air-Max/repro/tps62902.pdf` fails with "pdftoppm is not installed".
  - Refuted: "the Read tool needs pdftoppm". Read without `pages` worked in this session, both on a 2-page PDF and on the 51-page, 6.3 MB TPS62902 datasheet (all pages, text and images). That is a fallback, though a costly one in context. The tool's own description says `pages` is required past 10 pages, so this may differ by harness.
  - Not tested: the WebFetch claim (§3.5 already says WebFetch mangles a PDF).
- cause: `.claude/skills/plan-pcb-placement/SKILL.md:391-392` ("open it with the Read tool and `pages`") and `:418-425` (the only page-finding recipe is "Where poppler is installed"). Environment gap; sure.
- head 0c05be08: unchanged
- upstream: new (searches for "pdf", "poppler", "pdftoppm" and "datasheet PDF" return nothing relevant)
- issue draft:
  **Placement §3.5 cannot read a datasheet without poppler, and names no fallback**
  - §3.5 says to open the downloaded PDF "with the Read tool and `pages`". On macOS without poppler, Read with `pages` fails ("pdftoppm is not installed").
  - The repo has no PDF reader: no poppler binaries, and no fitz/pypdf/pdfplumber in the venv, in KiCad's Python or in requirements.txt.
  - 14 of 20 gpm boards lost 4-10 min each. Teammates wrote PDFKit Swift helpers (9 boards), a FlateDecode inflater (09), or pip-installed PyMuPDF (249 MB, board 20).
  - Measured: Read WITHOUT `pages` returned a 51-page, 6.3 MB TI datasheet whole, so a fallback exists in some harnesses, at the cost of the whole document in context.
  - Repro (WT): `which pdftoppm pdftotext; python3 -c "import fitz"; python3 -c "import pypdf"`, then Read `wk/gpm/07_One-Air-Max/repro/tps62902.pdf` with pages=1.
  - Expected: ship a small page/text extractor (e.g. pypdf in requirements, or a `py_tools` helper), or have §3.5 name the fallback order: poppler, then helper, then whole-file Read on small PDFs.
  - Code: .claude/skills/plan-pcb-placement/SKILL.md:391-392, :418-425.

### M12 -- VERDICT: CONFIRMED
- title: the skills call `kicad-cli` bare; on macOS it is not on PATH, and §3.9's fallback then ships "silk ungraded" on a machine that has KiCad
- boards: 01 06 08 12 15 17   severity: l
- repro at bda59fa0: `zsh -lc 'command -v kicad-cli'` -> not found. `env -i HOME=$HOME PATH=/usr/bin:/bin:/usr/sbin:/sbin zsh -c 'kicad-cli version'` -> exit 127. `kicad_oracle.find_kicad_cli()` -> `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Log: `V9/M12/probe.txt`.
- cause: bare calls at `.claude/skills/plan-pcb-placement/SKILL.md:863-864`, fallback at `:873`; `.claude/skills/plan-pcb-routing/SKILL.md:3308`; `.claude/skills/review-routed-board/SKILL.md:60`. The repo's tools resolve it through `py_router/kicad_oracle.py:35-39,122` (`KICAD_CLI` env, then the app bundle) and `kicad_locate.py`. Sure.
- head 0c05be08: unchanged
- upstream: new; related #1356 (whose fix added the §3.9 / 4c silk step with the bare calls)
- issue draft:
  **Skill silk-check commands call bare `kicad-cli`, which is not on PATH on macOS**
  - The placement skill §3.9 step 1, plan-pcb-routing 4c and review-routed-board call `kicad-cli pcb drc ...` directly. A stock macOS KiCad install puts the binary at /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli and not on PATH, so the call exits 127.
  - §3.9 then says "Without `kicad-cli`, keep the board as it was and say the silk is ungraded", so following the skill exactly ships ungraded silk on a machine with KiCad 10 installed.
  - The repo's own tools find the binary (`kicad_oracle.find_kicad_cli`, `KICAD_CLI` env, `kicad_locate`), so only the copy-paste lines fail. That was 1-2 min on each of 6 boards.
  - Repro (WT): `env -i HOME=$HOME PATH=/usr/bin:/bin zsh -c 'kicad-cli version'` (127), then `python3 -c "import sys;sys.path.insert(0,'py_router');import kicad_oracle;print(kicad_oracle.find_kicad_cli())"`.
  - Expected: the skills resolve the binary the way the tools do: a one-line shim (e.g. `py_router/kicad_locate.py --cli`) or `"${KICAD_CLI:-$(python3 ... find_kicad_cli)}"`. The fallback should apply only when that resolver also fails.
  - Code: plan-pcb-placement/SKILL.md:863-864, :873; plan-pcb-routing/SKILL.md:3308; review-routed-board/SKILL.md:60.

### M13 -- VERDICT: CONFIRMED
- title: build_router.py compares rust_router/ against `origin/main`; on a fork whose main lags, a clean upstream checkout refuses the prebuilt and builds from source
- boards: (campaign setup, lead prep #2)   severity: l
- repro at bda59fa0: in WT, origin is the fork (edgehero) at fd90311e and upstream/main is 0c05be08. `git diff --quiet origin/main -- rust_router` gives rc=1 and `git diff --quiet upstream/main -- rust_router` gives rc=0. `python3 -c "import build_router as b; print(b._crate_matches_release_source('<WT>'))"` -> False, which makes `main()` print "differs from main ... Building from source instead." I did not run the build itself, to avoid disturbing other verifiers. Precise condition: this happens whenever the fork's main differs in rust_router/. A synced fork would pass, so "always" in the item is an overstatement.
- cause: `build_router.py:403-407` (`ref = next(r for r in ('origin/main', 'main') ...)`), consumed at `main()` (`if args.tag is None and _crate_matches_release_source(...) is False: build_from_source`). Sure.
- head 0c05be08: unchanged
- upstream: new; related #615 (introduced the check)
- issue draft:
  **build_router.py judges "matches the release source" against `origin/main`, which on a fork is the fork**
  - `_crate_matches_release_source` compares the working tree's rust_router/ with `origin/main` (else `main`). Release assets are built from drandyhaas/main, but in a fork clone `origin` is the fork.
  - Measured: a worktree at bda59fa0, whose rust_router/ is identical to upstream/main, returns False because the fork's origin/main (fd90311e) is stale. build_router then prints "differs from main ... Building from source instead" and never downloads the matching prebuilt.
  - Cost: a cargo build per setup, and a hard failure on a machine without Rust (build_from_source prints the "install Rust" error).
  - Repro (WT): `python3 -c "import build_router as b; print(b._crate_matches_release_source('.'))"` -> False, while `git diff --quiet upstream/main -- rust_router` exits 0.
  - Expected: compare against the release remote, i.e. the remote whose URL is drandyhaas/KiCadRoutingTools (or the release tag's commit), and fall back to origin/main only when none exists. Alternatively, compare rust_router/ against the tag the download would use.
  - Code: build_router.py:403-407.

### M14 -- VERDICT: CONFIRMED-PARTIAL
- title: check_floorplan exits 4 / `pass: false` with 0 errors on a pile-emitted intent, and the remedy it prints (dispositions) does not clear it
- boards: 03 04 (11 16 noted)   severity: l
- repro at bda59fa0:
  - `check_floorplan.py V9/M14/b03_final.kicad_pcb --intent V9/M14/b03_intent_run.json` (board 03 copy) -> exit 4, "0 error(s), 1 warning(s)", `pass False`, `not_graded {'budget_abstained': 3, 'rules_skipped_armed': 3}`. The three withheld keys are decaps.max_distance_mm, oob_count and overlap_area, read from the intent's `context.budget_withheld`.
  - I copied the intent with `dispositions.withheld` set for all three keys and `dispositions.rules` for the three OWED rules. The roster then shows `[dispositioned]` for each, but the run is still exit 4 with the same `not_graded`.
  - Partial because "incomplete is not a pass" is deliberate (#713 item 5, `GradeResult.complete`). The defects are that the prescribed disposition path cannot clear it, and that the module docstring still documents exit 4 as "error-severity violations found".
  - board_score reads errors only, so DONE is not blocked; only callers that branch on the exit code are hit (grade.py printed `floorplan_pass: false` next to `done: true`).
- cause: `py_placer/placement/floorplan.py:9002-9004` (abstained comes from `intent.budget_withheld`, overridden only by a hand-declared value, never by a disposition). `floorplan.py:7815-7841` (`complete`/`passed`). `py_tools/check_floorplan.py:1061-1072` (exit 4 on incomplete) against the docstring at `check_floorplan.py:26-33`. Sure.
- head 0c05be08: unchanged
- upstream: new; related #713 (item 5), #1103 (pile withholding)
- issue draft:
  **An intent emitted from a pile can never grade complete: check_floorplan exits 4 at 0 errors, and dispositions do not clear it**
  - An intent emitted from a pile withholds `oob_count`, `overlap_area` and (with no cap in radius) `decaps.max_distance_mm` in `context.budget_withheld`. Every later grade then reports `budget_abstained 3, rules_skipped_armed 3`, `pass: false`, exit 4, whatever the placement.
  - Measured on complex_hierarchy's final board: exit 4 with 0 errors and 1 warning. After adding `dispositions.withheld` for all three keys and `dispositions.rules` for zone_containment, decap_distance and legality (the remedy the roster prints: "or write why it does not: dispositions.rules.X"), the roster shows `[dispositioned]`, but `not_graded` and the exit are unchanged.
  - Repro (WT): `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/_verify/V9/M14/b03_final.kicad_pcb --intent wk/gpm/_verify/V9/M14/b03_intent_disp.json; echo $?` -> 4.
  - Expected: a withheld budget answered by a disposition counts as answered, not as "not graded". At minimum, the exit-code table in the docstring (which still says 4 = error-severity violations) names the incomplete case and how to clear it.
  - Code: floorplan.py:9002-9004, :7815-7841; check_floorplan.py:26-33, :1061-1072.

### M15 -- VERDICT: CONFIRMED-PARTIAL
- title: route_diff.py has no `--json-out` (route.py has), so a judging chain that passes one fails every seed at exit 2
- boards: 07 14   severity: l
- repro at bda59fa0: `python3 -X utf8 py_router/route_diff.py <board> V9/M15/x.kicad_pcb --nets '/USB_D*' --json-out V9/M15/x.json` -> `route_diff.py: error: unrecognized arguments: --json-out`, EXIT=2. Of the routing CLIs, only route.py has the flag (route_planes, bga_fanout, qfn_fanout and repair_planes do not). Refuted part: §3.7's example does not pass `--json-out` to route_diff. It passes it only to route.py; the placeholder note "`{dir}` ... (`--json-out {dir}/route.json`)" is what invites the generalisation. No skill or doc passes it to route_diff.
- cause: `py_router/route_diff.py:2439` (its parser has no `--json-out`; its summary is stdout-only at `:2230`) against `py_router/route.py:9204`. Sure.
- head 0c05be08: unchanged
- upstream: new; related #1327 (judge_seeds)
- issue draft:
  **route_diff.py lacks route.py's `--json-out`; one chain flag fails one of the two routing CLIs**
  - route.py takes `--json-out FILE` (the merged JSON_SUMMARY), and its help says to prefer it over scraping stdout. route_diff only prints JSON_SUMMARY to stdout and rejects the flag at exit 2.
  - judge_seeds chains (§3.7) document `{dir}` "for `--json-out {dir}/route.json`". Two boards put it on their route_diff line: board 07's judge failed all six seeds ("step 3 (route_diff.py) exited 2 and wrote no board"), and board 14's plan ran on with no input.
  - Repro (WT): `python3 -X utf8 py_router/route_diff.py wk/gpm/_verify/V9/M09/A/step1.kicad_pcb /tmp/x.kicad_pcb --nets '/USB_D*' --json-out /tmp/x.json` -> exit 2.
  - The §3.7 example itself uses the flag only on route.py, so this is a parity gap, not a wrong example.
  - Expected: route_diff accepts `--json-out FILE` with the same meaning (its final JSON_SUMMARY written to FILE), or §3.7 / judge_seeds' docstring say the flag is route.py-only.
  - Code: py_router/route_diff.py:2439 (parser), :2230 (summary print); route.py:9204 for the reference.

### M16 -- VERDICT: CONFIRMED
- title: plan-pcb-routing says `--rip-existing-nets <exact names>` is how to change copper the router is happy with; on a connected net that is a no-op, and `--force-reroute` is the flag
- boards: 09 19 (10 12 15)   severity: l
- repro at bda59fa0: on a copy of `09_StickHub/routed.kicad_pcb`, `python3 -X utf8 py_router/route.py V9/M16/routed.kicad_pcb V9/M16/out_rip.kicad_pcb --nets 'Net-(J1-Pin_1)' VIN GND --rip-existing-nets 'Net-(J1-Pin_1)' VIN` -> "WARNING: 2 net(s) named in both --nets and --rip-existing-nets are already fully connected and will NOT be re-routed ... pass --force-reroute (#515)". It routed 0 nets, and both nets' copper is identical to the input (55 segments, 3 vias). With `--force-reroute`, it logs "stripped 55 segment(s) / 3 via(s) from 2 net(s) for a from-scratch re-route". On this two-net scope the improvement gate then reverted, because VIN failed.
- cause: `.claude/skills/plan-pcb-routing/SKILL.md:3097-3099`, written 2026-08-22, after #515 closed on 2026-07-29. The tool itself is right: `py_router/route.py:3116-3131`. Sure.
- head 0c05be08: unchanged
- upstream: new skill-text error; related #515 (added `--force-reroute` and the warning). Not an incomplete fix of #515, since the text postdates it.
- issue draft:
  **plan-pcb-routing "Retrying a failed net" names `--rip-existing-nets` where `--force-reroute` is needed**
  - The text (SKILL.md:3097-3099) says: "To change the geometry of copper the router is happy with you must rip it (`--rip-existing-nets <exact names>`)".
  - For a net that is already connected, that is a no-op. route.py drops the net as already connected before any rip, warns "will NOT be re-routed ... pass --force-reroute (#515)", routes 0 nets, and ships identical copper.
  - Measured on StickHub (`--nets 'Net-(J1-Pin_1)' VIN GND --rip-existing-nets 'Net-(J1-Pin_1)' VIN`): routed 0 nets, 55 segments and 3 vias byte-identical. `--force-reroute` strips the 55 segments and 3 vias and re-routes them.
  - It cost a lap on boards 09 and 19 and was noted on 10, 12 and 15.
  - Repro (WT): `python3 -X utf8 py_router/route.py wk/gpm/_verify/V9/M16/routed.kicad_pcb /tmp/o.kicad_pcb --nets 'Net-(J1-Pin_1)' VIN GND --rip-existing-nets 'Net-(J1-Pin_1)' VIN | grep "will NOT be re-routed"`.
  - Expected: the paragraph names `--force-reroute` for re-shaping a connected net, and keeps `--rip-existing-nets` for nets that block another route (route.py's own definition).

V9: CONFIRMED 5, PARTIAL 3, NOT A BUG 0, NOT REPRODUCIBLE 0
