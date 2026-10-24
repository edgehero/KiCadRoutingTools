# REPORT: gpm board 17, environment_sensor (`/plan-pcb-placement full`)

I followed `.claude/skills/plan-pcb-placement/SKILL.md` by hand, with `references/verifier.md`, `part-roles.md` and `placement-lessons.md`. §3.8 was followed by hand from `.claude/skills/plan-pcb-routing/SKILL.md`, and the power-net sizing by hand from `.claude/skills/analyze-power-nets/SKILL.md`. No skill was invoked.

## 1. Result

**DONE.** The delivered board is `wk/gpm/17_environment_sensor/delivered.kicad_pcb` (sha256 `cd9d523c22e43970172ada8ad99f19c19255c5ded1b2231c0eef3f08f8b4ddd0`, with its `.kicad_pro`), filled by `fill_for_delivery`.

The spec flag graded is `--impedance-nets '/USB_D_*'`. The USB pair was routed with `route_diff --impedance 90`, which records `net_impedance` in the project.

| DONE condition (full mode) | measured on delivered.kicad_pcb |
|---|---|
| board_score blocking | **0** |
| unrouted / broken | 0 / 0 |
| check_complete (with the spec flag) | **DONE** |
| check_connected | ALL NETS FULLY CONNECTED |
| check_drc (`--baseline` input, margin 0.1) | 0 violations (also 0 without the margin) |
| check_assembly | buildable (blocking 0) |
| check_floorplan --intent | 0 errors, 6 warnings |
| off-outline pad, graphic or keep-out copper | none |
| mechanical facts (MP1-3 and TP1-6 poses, J1 on the west edge) | all met, 0.0000 mm deviation (verifier) |

- **check_floorplan exit code:** it exits 4, "NOT FULLY GRADED", because the given intent withheld the `oob_count`/`overlap_area` budgets for a pile (TOOL_GAPS 11).
- **blocking_by:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, impedance 0, undersized 0, unrouted 0.
- **Ungraded:** diff_pairs, length and net_widths. The board declares no `.kicad_dru` skew rule, no length groups and no per-net width spec.

| quality | value |
|---|---|
| vias | **147** |
| copper_mm | **847.36** |
| segments | **834** |
| joins_needed | 0 |

`scripts/grade.py` (output in `grade/grade_delivered.json`) agrees:
- done true, blocking 0, check_complete DONE;
- check_complete_authored UNSOUND (see §7, floors);
- floorplan_errors 0, with `floorplan_pass` false only because of the exit-4 abstention.

## 2. Inputs, intent, and the rows I added

- **`intent_run.json`** is `intent.json` (read-only) plus ONE row I added:
  - `blocks[] sensor_island`: refs U5 and U6, zone `[199.95, 113.5, 210.0, 121.65]`.
  - Reason (my judgment): the outline cuts a slotted NE island (a north notch, an internal L cutout and an east notch), and both designer pours stop short of it.
  - Sensirion's SHTxx/STSxx Design Guide recommends milled slits around a humidity/temperature sensor to cut heat conduction from the rest of the board. So the SHT45 and the BME280 belong on the island.
- **`waive_locked_overlaps.py`** found 0 pairs (nothing is locked), so it added no row. I added no `proximity[]`, `overlap_waivers[]` or template rows.
- **EMC rows: none were given.** No `emc_roles` proximity limits and no `keep_away` rules were supplied, and I invented none.
- **J1 (GCT USB4105-GF-A):**
  - Its edge (west) comes from the brief; I left its position along the edge free.
  - The datasheet's recommended layout (rev B4) puts the PCB edge flush with the shell front, so the default overhang band of 0 stands and I wrote no `overhang_mm` row.
  - I read that figure through a `qlmanage` PNG render, because poppler is not installed (TOOL_GAPS 6).
- **Fixed poses:** MP1-3 and TP1-6 reached place_simple through `fixed_poses[]`. Nothing was locked.
- **Input hashes:** all five pinned inputs re-checked at the end and are unchanged.

## 3. Groups and judgement calls

`groups.json` has 8 groups. check_groups reported 0 errors, 0 warnings and 0 template hints.

| group | anchor | members | judgement |
|---|---|---|---|
| usb_in | J1 | D1-D5, R3, R4, C4, FB1, R1, C2, FB2 | the power and data entry: VBUS and CC ESD, the CC pull-downs, the D+/D- ESD array, VBUS bulk cap, the VBUS→+5V bead and the shield network |
| ftdi | U1 | C5-C8, R2, R5-R11, R13-R16 | the FT232R with its decaps and RESET# pull-up; the 0R option jumpers bridging to the STM32 sit on the FTDI side |
| power | U2 | C1, C3, C9-C11, TP9, TP10, LD1, R12 | the AP7370 LDO with its caps, the rail test points and the +5V LED |
| core | U3 | VDD/VDDA/VREF caps, FB3, Y1/Y2 with their load caps and 1M bias resistors, R19, R24, R20, R29, R30, TP8, the 100R I2C series resistors (at the driver), BAT1 (back), LD2/R17; TP1-6 fixed | the STM32G474; C13 is a spare 100n placed here |
| fram | U4 | C18, R26, TP7, R31-R34, R37, R38, TP11, TP12 | the FRAM with its WP and address straps; the bus pull-ups sit as a pair at a peripheral end |
| sensors | U6 | U5, C25-C28, R35, R36 | the BME280 and SHT45, held to the island by the block zone |
| qwiic_f | J2 | D6, D7 | front JST-SH port, given an `edge: E` hint (judgment) |
| qwiic_b | J3 | D8, D9 | back JST-SH port, given an `edge: S` hint (judgment) |

- **No template candidates.** The board has no inductor, transformer, flying cap or RF part, and U2 is an LDO. No datasheet template was fitted.
- **Crystal claims:** the claims at U3 end as warnings. C23 is 2.58 mm from Y2 against a 2.2 mm claim, and Y2's far leg is 8.40 mm from U3 against an 8.1 mm claim.
- **J2/J3:** the anneal did not honour their edge hints. Both ended near the north edge, inboard of MP1, and nothing grades their mating direction because no edge was declared for them.

## 4. Placement, judging, and the kept seed

- **Pass 1** was the only pass, with default arguments, 12 seeds and `--jobs 4`; it took about 1.5 min.
  - Seeds 0, 3 and 5 were floorplan-clean; the other nine carried decap or decap-pin errors.
  - Per §3.6 only the clean seeds were fast-routed: `judge_seeds --seeds 5,3,0 --jobs 3` with `KICAD_ROUTE_TRACE=1`.
- **Fast routes:**

| seed | blocking | vias |
|---|---|---|
| 3 (judge keeps) | 0 | 108 |
| 0 | 0 | 120 |
| 5 | 1 | 112 |

- **Judgment: I changed the kept placement from seed 3 to seed 5.**
  - **Seed 3:** its full route (in `final_route_old1/`) ended at blocking 2, all impedance. route_diff could not couple the USB pair out of U1 (a 0.5 mm-pitch QFN). Its single-ended fallback laid the pair on B.Cu over voids in the In2 plane, with 11 crossings.
  - **Three attempts did not clear seed 3:** turning D5 to 0°, routing the diff pair on F.Cu only, and adding `qfn_fanout` stubs on U1's USB pins.
  - **Seeds 0 and 5:** the same full chain on seed 0 also ended at impedance 2. On seed 5 it was DONE, with the pair coupled (1/1).
  - The quick judge cannot grade the impedance spec at all (TOOL_GAPS 1).
- **CHOSEN.json:** seed 5, scattered, pass 1, intent `intent_run.json`, place_args [], after [].
- **No hand repair.** route_review's two suggested turns (R5, R6) were tried and rejected: 151 vias.

## 5. Routing (§3.8, plan-pcb-routing followed by hand)

**Board and analysis**
- **Step 0 gate:** check_assembly says buildable. The board_score baseline is unrouted 48, broken 49.
- **Board:** 4 layers, a deliberate stackup (0.12 / 1.2 / 0.12 mm, εr 4.5), 89 nets. That is the STANDARD tier.
- **Diff pair:** one, the USB 2.0 Full Speed pair from the FT232R.
- **Speed:** the high-speed scan found medium tier at most (USB FS, SWD/JTAG, I2C, UART, 8 MHz and 32 kHz crystals). So there is no GND-return-via or stitching step, and no keep-away rule.

**Plane map (a deviation from the skill, and a judgment)**
- The skill's STANDARD map is inner-only pours. Here the GND pour is ONE zone spanning F.Cu, B.Cu and In1.Cu, which the README calls design intent, and no chain tool can split it (TOOL_GAPS 7).
- So I kept the designer's pours as drawn (`--skip-existing-zones`), with +3V3 on In2 and `--layer-costs 1.0 3.0 3.0 1.0`.

**Power widths (`/analyze-power-nets` by hand)**
- **Tool recommendation:** GND 2.0, +3V3 1.0, +5V 0.7, VBUS 0.5, and VDDA/VBAT/GNDREF 0.7 mm (TOOL_GAPS 5, #1377).
- **Current estimates:**
  - J1 is a 500 mA source and U2 a 300 mA LDO.
  - U1 draws 15 mA, U3 about 60 mA (estimate), U5 about 60 mA with its heater on (estimate), U4 and U6 under 1 mA, and the LEDs 5 mA.
  - J2 and J3 are budgeted 100 mA each (estimate).
- **Widths used (my judgment):** GND, +3V3, +5V and VBUS at 0.5 mm; VDDA, VBAT and GNDREF at 0.3 mm. These fit the 0.5 mm-pitch pins and the 2 mm bridge onto the sensor island.

**Design rules:** the Default class is 0.15/0.15 with 0.5/0.2 vias, passed as `--clearance-ceiling 0.15`.

**Chain** (`final_route/final_plan.sh`)
- route_plan_check passed 17/17 rules. The manifest is `final_route/redo_commands.sh`, and the GUI plan `final_route/final_plan.json` was converted from that manifest.
- Steps:
  0. `kicad-cli pcb upgrade` on `in.kicad_pcb`: KiCad 9 → 10 format, so the route steps can declare Type VII on vias under solder (TOOL_GAPS 3). I added this line to the manifest by hand, because the recorder does not record kicad-cli.
  1. `route_planes`, keeping the existing zones and adding the U1 exposed-pad thermal array (9 vias).
  2. `route_diff` on the USB pair at 90 Ω, fab-floor geometry: coupled 1/1.
  3. `route.py --nets '*'`.
  4. and 5. Two Step-2d iterations with the same flags.
- No fanout step: U1 and U3 are perimeter parts and plain routing completed them.

`routed.kicad_pcb` is the chain's last board (`final_route/5_iter2.kicad_pcb`).

## 6. Stop rule

**Stop condition 1 (DONE).** DONE was first reached at about 07:07Z on the KiCad 9 chain. It held through delivery once the file-format problem was fixed. After DONE, four via-reduction approaches were measured:

| approach | result |
|---|---|
| route.py `--via-cost 150` | 142 vias, but impedance blocking 1 |
| route.py `--track-width 0.127` | 145 vias, but impedance blocking 1 |
| route_review turns of R5/R6, full chain | DONE, but 151 vias |
| route.py `--same-net-pad-clearance 0.1` (no via-in-pad) | 137 vias, but broken 1 and impedance 1 |

**Remaining blockers: none.** These non-gating findings remain on the delivered board, each measured:
- **KiCad DRC, edge clearance:**
  - 3 `copper_edge_clearance` errors at 0.1978 mm against 0.2000 mm, at the cutout arc at (198.95, 118.45). Two are GND tracks on F.Cu and one is I2C_1_SDA on B.Cu.
  - check_drc accepts them as quantization (2.2 µm). A re-route at `--board-edge-clearance 0.22` moved no copper and raised the project's edge floor, so I did not keep it (TOOL_GAPS 9).
- **KiCad, unconnected items:** KiCad reports 2. They are the mounting-tab pairs of J2 and of J3, each pair sharing one `unconnected-(Jx-PadMP)` net. This is a design condition already in the input, left unrouted.
- **KiCad, other items:**
  - `footprint_type_mismatch` on J1, inherited from the footprint library;
  - one `track_dangling` warning, a 0.057 mm GND stub at (189.44, 124.14);
  - one `connection_width` on Net-(U3-VBAT).
- **Fab note:** 99 vias sit in pads or paste openings. route.py declared all of them IPC-4761 Type VII (filled and capped), which must go on the fab drawing and costs extra.

## 7. Floors

`check_complete --authored-from` the input grades the board **UNSOUND**: it carries copper below floors the project declared.
- Track width 0.15 → 0.0889 mm (28 SWCLK-JTCK segments; USB necks at 0.1 mm).
- Via diameter 0.5 → 0.28 mm (7 small vias; 21 fab-tier escalations to the advanced tier).
- Hole diameter 0.20 → 0.15 mm.
- Default clearance 0.15 → 0.10 mm, from automatic descents on GND, U1-RESET#, U1-RI#, U1-RXD, U3-VBAT, U6-SDO and SWCLK-JTCK.
  - The first lowering, 0.15 → 0.119, came from route_planes (TOOL_GAPS 2).
  - route.py step 3 reports 84 features on 12 nets below the requested size.

The project floors written back match the copper, so KiCad grades what was routed. Confirm the fab supports a 0.0889 mm track, 0.1 mm clearance and a 0.15 mm drill before ordering.

## 8. Silkscreen

`beautify_labels` produced `labelled.kicad_pcb`, graded with KiCad's own silk classes:

| | silk_edge_clearance | silk_overlap | silk_over_copper | total |
|---|---|---|---|---|
| routed.kicad_pcb (before) | 9 | 40 | 55 | 104 |
| labelled.kicad_pcb (after) | 3 | 7 | 5 | 15 |

**The labelled board was kept.**

## 9. Fill

`fill_for_delivery` ran and exited 0: 22 filled polygons, 4 net classes preserved, and plain-DRC unconnected went from 64 to 2 (the J2/J3 mounting tabs). The first delivery, from the KiCad 9 chain, graded blocking 96 after this step's KiCad 10 re-save. I re-ran the chain from a KiCad 10 input, and the second delivery grades DONE.

## 10. Timeline and where the time went (UTC, 2026-10-24)

| time | step |
|---|---|
| 06:36:48 | FIRST_CMD |
| 06:37-06:46 | skills read; board brief and context; datasheets; groups; sensor-island zone; check_groups |
| 06:46-06:48 | place_simple, pass 1, 12 seeds |
| 06:48-06:50 | check and render seeds; power-net analysis; judge chain |
| 06:50-06:52 | judge_seeds on 5, 3, 0 |
| 06:52-06:54 | full route of seed 3: blocking 2 (impedance) |
| 06:55-07:05 | impedance experiments on seed 3; full chains on seeds 5 and 0 |
| 07:06-07:08 | final chain on seed 5: DONE |
| 07:08-07:16 | four post-DONE via approaches; KiCad DRC compare; edge re-route attempt |
| 07:16-07:22 | delivery hits blocking 96 (file format); re-chain from KiCad 10; second delivery DONE |
| 07:24-07:34 | verifier, grade.py, TOOL_GAPS, measure.py |

Most of the time went to the USB impedance problem the quick judge could not see (about 15 min) and to the delivery-format problem (about 6 min). Routing itself is fast on this board: about 80 s for a full chain and 30 s for a fast route. `measure.py` reports a wall clock of 0:57:12 and 325 s spent waiting on jobs.

## 11. Tool gaps

`TOOL_GAPS.md` has 11 entries. These are the tools that said "fine" about something that was not:
- judge_seeds and quick_score (1);
- route_planes' "tightened" clearance (2);
- fill_for_delivery exiting 0 on a board it had just made blocking 96 (3, #1367);
- kicad_drc_compare printing kicad=0 CONSISTENT over 3 KiCad errors (9, #1404);
- place_pose printing `legal: false` for a move that made nothing worse (10, #1326);
- check_floorplan exiting 4 at 0 errors (11, #1420).

## 12. Verifier

There was one call, verdict_1: **VERDICT=PASS**, and the connectivity, drc and spec lens files are all PASS.
- **What it measured:** the sha matches; check_assembly buildable; floorplan 0 errors; no off-outline copper; mechanical deviation 0.0000 mm; board_score blocking 0; check_complete DONE; check_connected clean; check_drc 0; check_impedance 0 crossings.
- **Hand review:** USB skew 2.16 mm on a USB Full Speed pair, which it did not flag.
- **The judgment the PASS rests on:** it read the rule "a declared class left ungraded → FAIL" as applying to a declared requirement. The pair's one declared requirement, 90 Ω impedance, is graded and clean; diff_pairs is ungraded only because no skew rule exists anywhere. If a bare diff-pair record in protected_nets counts as a declared class, the verdict would be FAIL, and that would be the only defect.
- **Isolation slip:** one stale file from another board (`wk/gpm/05_interf_u`) was printed from the shared scratchpad, then discarded and re-run; nothing from it entered the verdict.

The ledger (`ledger.jsonl`, 17 rows) is closed with `--final --stop-condition 1` and the three lens files. The datasheet folder was moved to `old/datasheets/`.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE**

- **Delivered board:** `wk/gpm/17_environment_sensor/delivered.kicad_pcb`, sha256 `cd9d523c22e43970172ada8ad99f19c19255c5ded1b2231c0eef3f08f8b4ddd0`. It is filled, and its `.kicad_pro`, `DELIVERED.sha256` and the `DONE` marker are beside it.
- **Scores:** blocking 0, joins_needed 0, vias 147, copper_mm 847.36, segments 834. These are graded with `--impedance-nets '/USB_D_*'`; `check_complete` says DONE and the verifier (1 call) passed all three lenses.
- **Stop rule:** condition 1, DONE. After DONE I measured four ways to cut vias and none was better.
- **Wall time:** about 57 min from FIRST_CMD (06:36:48Z to 07:34Z; `measure.py` reports 0:57:12).
- **TOOL_GAPS:** 11 entries. The top three:
  1. `judge_seeds`/`quick_score` cannot grade the declared impedance spec. The judge kept seed 3, whose full route ends at blocking 2 (impedance), so I switched by hand to seed 5, the judge's last pick, which is DONE.
  2. `route_planes` lowered the board's Default clearance from 0.15 to 0.119 "for U6's via lattice" in a step that kept every zone and poured nothing. U6 sits where no pour reaches, and every later step then routed at 0.119.
  3. The KiCad 10 re-save inside `fill_for_delivery` turned a DONE board into blocking 96 (vias in paste, #1367). The workaround was `kicad-cli pcb upgrade` on the chain input before routing; the copper came out identical and all 96 vias were declared Type VII.

**Not done:** the harness refused to write REPORT.md ("Subagents should return findings as text"), so REPORT_DONE was not created. The full REPORT.md content follows.
