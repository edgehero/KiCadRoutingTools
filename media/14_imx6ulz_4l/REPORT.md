# REPORT — gp14 board 14 `imx6ulz_4l` (`/plan-pcb-placement full`)

## 1. Result

**Status: NOT DONE.** Every machine DONE gate passes. Verifier #1 returned **FAIL** on the spec lens, because the declared DDR3 differential pairs fail review-routed-board Step 4.

Board: `wk/gp14/14_imx6ulz_4l/final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.design-brief.json`, copied with `copy_board`), sha256 `07784f74e41613c8e294776024dacb3c2f1886cdd2645dab89d3303ea3362ee6` (`FINAL.sha256`). Placement: round 1 seed 2, scattered start, plus three hand moves (`CHOSEN.json`).

| DONE condition (full mode) | Measured | Pass |
|---|---|---|
| board_score blocking = 0 | 0 | yes |
| check_complete | DONE (exit 0) | yes |
| check_connected | all 134 of 134 multi-pad nets connected | yes |
| check_drc at 0.1 (margin 0.1, and margin 0) | 0 violations | yes |
| kicad-cli 10.0.7 DRC with `--refill-zones` | 0 errors, 0 unconnected, 0 `length_out_of_range` | yes |
| `.kicad_dru` DRAM_LDQ window, DQ0-7 within 11.5-14.5 mm | pin-pair 12.50-14.11 mm; total 13.34-14.27 mm | yes |
| check_assembly with `--baseline` | buildable, blocking 0 | yes |
| check_floorplan | 0 errors, 7 warnings | yes |
| mechanical.json poses | 7 of 7 exact; outline unchanged | yes |
| grade.py | `done: true` | yes |
| **Verifier** | **verdict_1: FAIL (spec lens, DDR3 pairs)** | **no** |

`blocking_by`: unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, length 0 (DRAM_LDQ spread 1.61 against tolerance 3.0), drc_via_in_paste 0. Impedance and net_widths are ungraded because no spec is declared for either (the stackup is a placeholder).

Quality: **349 vias, 3145.14 mm copper, 2711 segments.** The first DONE was 440 vias and 2733 mm; post-DONE laps cut the vias to 349.

## 2. Groups and judgement calls

Fixed parts: H1-H4, J4 (B.Cu), U1 and U2 sit at their mechanical.json poses in `fixed.kicad_pcb`, unlocked; the intent's `fixed_poses` seats them. No EMC rows were given, so no `emc_roles` or `keep_away` limits were invented.

`groups.json` has 7 groups, and check_groups reports 0 errors:

- **core (59 parts, anchor U1):**
  - U1 and U2 with every decoupling cap on their rails, plus the VREF divider (R13, R14, C36, C38-C40), the ZQ resistors, CLK0 termination R1, ferrites FB2/FB3, and crystal Y1 with its load caps.
  - Judgement: one group for both BGAs, so each VMEM cap matches whichever chip's VMEM pin is nearest.
- **straps (44 parts):** the BOOT_CFG pull-up and pull-down resistors, all on B. Each connects only to a U1 ball on its east face.
- **boot_sw (5 parts), edge E:** SW2 DIP switch and its pull-ups. The user sets it, so it goes at the east edge beside the straps.
- **reset (10 parts):** SW3, supervisor U7 and its RC parts, and SW1 with its pull-ups. All of their U1 balls are on the west face.
- **power (25 parts):** J1, three TLV62568 buck converters with their L/C/R parts, and the U8 LDO with C20.
- **debug (10 parts), edge S:** JTAG, UART1, UART2 and I2C2 connectors. Their U1 balls are on the south face.
- **qspi (1 part):** J5, whose balls are at U1's north-east corner.

**Round changes:**
- `groups_r2.json`: straps set `apart` from core, and reset given edge W.
- `intent_r2.json`, written beside the given intent, which is unchanged: keepouts `ddr_west` and `ddr_north` on F and B, allowing only U1/U2. Reason: round-1 routes left DRAM nets open at U1 because parts were parked in the U2-U1 corridor and on U1's north face.
- `intent_r3.json`: adds B-side keepouts `u1_back` and `u2_back`, which allow only core parts. Reason: `apart` alone still left 10-15 straps under U1.
- The final board was placed with the given `intent.json`, and it is graded against that file.

**Hand moves after placement** (`CHOSEN.json` `after`):
- Moved U8 to (72.0, 114.0, 90°), C20 to (75.1, 112.4, 90°) and C19 to (69.2, 113.6, 270°).
- Reason: a floorplan error. C20 was 22.34 mm from U1 pin P12 (VDD_SNVS_IN); the limit is 8.46 mm.
- The first C20 pose (x 75.55) overlapped FB2's courtyard. KiCad flagged it but check_assembly passed it, so I moved C20 to x 75.1.

## 3. Review rounds

Each round placed 12 seeds (about 25 s each) and judged the 6 cheapest with `helpers/judge_chain.sh`.

| Round | Change | Fast-route blocking per judged seed | Outcome |
|---|---|---|---|
| r1 | given groups and intent | s5 20, s6 10, s1 40, s10 24, s8 13, **s2 8** (391 vias) | best overall |
| r2 | straps apart from core; reset edge W; intent_r2 keepouts | s8 10, s6 10, s3 21, s11 40, s1 27, s9 9 | none beat r1/s2 |
| r3 | adds B keepouts under the BGAs (intent_r3) | s1 15, s3 23, s8 8 (405 vias), s5 16, s7 13, s6 10 | ties at 8 with more vias |

**What the routes showed:**
- Round 1: DRAM nets were open at U1. 36-42 B-side straps sat under U1. Reset parts landed east of U1, so SOC_ONOFF, BOOT_MODE and SOC_RST_L ran 55-60 mm.
- Round 2: straps were still under U1.
- Round 3: the keepouts removed the straps from under U1, but the extra vias cost more than that gained.

I kept r1/s2. The three-round cap was reached.

## 4. Routing attempts (full mode, `/plan-pcb-routing` by hand)

**Chain B** (pour, U1/U2 dogbone fanout at 0.45/0.25, place_fanout_clearance, route_diff for 3 pairs, route.py) on r1/s2:
- 0 unrouted, 0 broken, DRC 0, 373 vias.
- Blocked by the floorplan error on C20.
- The DRAM_LDQ window was broken: 12-21 mm, and board_score read DQ7 as "unjoined".

**Chain B on `kept_d`** with length matching at tolerance 1:
- KiCad reported 8 `length_out_of_range` (9.2-20.9 mm).
- It also reported 8 clearance errors from grazes at U1's 0.12 mm local clearance.

**route_bus joint mode** (three runs, 23-35 min each):
- 43 of 43 lanes routed.
- On r1/s2 plus the rest of the chain: 317 vias and 2673 mm, but 3 lengths out of range (DQ2 10.2, DQ5 17.3, DQ7 21.3 mm) and messy copper (weird_copper).
- On `kept_d`: VMEM ball U2.F1 was caged in.

**Lane-0-first probes:**
- Routing DQ0-7 first on the bare poured board met the window (11.7-14.0 mm). Settings: direction preference 0, turn cost 0, heuristic weight 1, grid 0.05, via cost 25, in three protected length-matched steps.
- But the rest of the chain then left 4-10 nets open.
- Fanout after lane 0 laid copper over the lane-0 tracks: 98 check_drc violations and 1 KiCad short.

**Chain L10** reached the first DONE at 21:08Z with 440 vias and 2733 mm:
- U2 VMEM fanout first.
- Lane 0 in three protected steps: {DQ7, DQ5}, then {DQ2, DQ3, DQ6, DQ1, DQ0}, then all eight plus DQM0 at tolerance 0.5.
- Fanouts with `--check-for-previous`, then caps, route_diff, `route.py '*'` and 3 iterations.
- Then `helpers/strict_collapse.py` and `helpers/vip_joins.py`.

**Post-DONE laps** (`helpers/opt_lap.sh`):

| Variant | Result |
|---|---|
| via cost 100 | DRC 1 |
| via cost 150 + VMEM fine-grid reroute | 389 vias, 2842 mm |
| via cost 150 + grid 0.05 | 6 broken |
| **via cost 250 + BOOT_CFG1_3 fine-grid reroute** | **349 vias, 3145 mm (shipped)** |
| via cost 400 | 370 vias |
| via cost 600 | 379 vias |
| bundle (Step 2c) | 387 vias |

That made a plateau. The shipped chain is in `final_plan.sh` and `final_route/redo_commands.sh`, with the helper lines included. Earlier chains are kept in `final_route_old1` to `final_route_old3`.

**Pair fixes after the verifier** (all recorded `--rejected`):
- **exp_p2, intra-pair matching:** DQS0 skew got worse, 5.29 mm.
- **exp_p1 / exp_p3, pairs routed before lane 0:** DQS0 became acceptable, but DQS1 went to 3.30 and CLK0 to 1.29. The window broke (DQ1 15.48, DQ2 14.60, DQ7 14.84 mm) and KiCad found 2 clearance errors.
- **exp_p4, pairs routed between the lane steps:** DQS1 3.30, window broken on DQ1 and DQ2, and AD0 left open.

## 5. Stop rule and remaining blockers

**Stop rule 3 (plateau)** fired, and the ledger is closed `--final` at 52 rows with `stop_condition 3`. The remaining blockers, by name:

- **/DRAM/DRAM_DQS0:** P runs In2.Cu 19.95 mm + F.Cu 1.13; N runs B.Cu 15.92 + F.Cu 0.57. Only 0.57 of 21.08 mm is coupled. Pad-to-pad, P is 21.07 mm and N is 16.47 mm, a **skew of 4.60 mm**.
- **/DRAM/DRAM_CLK0:** 16.31 of 16.59 mm is coupled on B.Cu, but the gap varies from 0.10 to 0.54 mm. U2 to U1, P is 16.80 mm and N is 19.77 mm, a **skew of 2.97 mm**.
- **/DRAM/DRAM_DQS1:** 7.07 of 16.81 mm coupled; **skew 1.24 mm** pad-to-pad. `helpers/pair_check.py` reads 0.88 mm from total copper.

**Warnings that do not block:**
- 44 of 122 DRAM vias have no GND via within 2.25 mm.
- check_impedance: 705.8 of 1063.6 mm of DRAM routing runs over gaps in the reference planes, mostly In2 (+3V3) carrying signals. No impedance is declared.
- Two KiCad `connection_width` warnings:
  - VREF at C38.1, 0.019 mm.
  - VMEM at R13.1, 0.061 mm.

  Both pads also have a solid track, so neither is an open.
- Seven floorplan warnings:
  - four `decap_pin_uncovered`;
  - C16, C22 and C28 sit 10.6-13.5 mm from U1 (`decap_ungraded`).
- DRAM_UDQ (DQ8-15) has no declared window and runs 7.6-32.75 mm.

## 6. Floors

`check_complete --authored-from` reports **UNSOUND** (report only). These are the board's authored minimums that the route went below:

- **Track width:** 0.1 → 0.0889 mm (68 segments under 0.1).
- **Via diameter:** 0.45 → 0.25 mm. Vias by size/drill:

  | Size / drill (mm) | Count |
  |---|---|
  | 0.45 / 0.25 | 244 |
  | 0.30 / 0.15 | 97 |
  | 0.25 / 0.15 | 4 |
  | 0.37 / 0.22 | 3 |
  | 0.41 / 0.25 | 1 |

- **Annular ring:** 0.07 → 0.05 mm.
- **Through-hole diameter:** 0.25 → 0.15 mm.
- **Minimum clearance:** 0.1 → 0.08 mm. This comes from the given +3V3 zone, so it is the input board's own setting.
- **Hole clearance:** declared 0.15 → 0.1 mm, but measured as kept (0 violations at 0.15).

The fab-tier escalation (default `auto`) is recorded on the `Design rules` lines in `final_route/*.log`.

**Other notes:**
- 89 vias-in-pad. The verifier counted 117 vias inside paste openings. The file format predates KiCad 10, so the board cannot declare via filling; IPC-4761 Type VII (filled and capped) belongs on the fab drawing.
- 63 mm of non-GND copper sits on In1, the GND plane.

## 7. Timeline (UTC, 2026-10-20) and where the time went

| Time | Event |
|---|---|
| 19:00:57 | FIRST_CMD |
| 19:06 | groups written |
| 19:07:40 | round 1 placed |
| ~19:13 | round 1 judged |
| ~19:17 / 19:19 | round 2 placed / judged |
| ~19:22 / 19:24 | round 3 placed / judged |
| 19:27 | first full route |
| 19:36-19:40 | `kept_d` (hand moves) |
| 19:27-20:59 | DDR length-window experiments (route_bus ×3, lane-0 variants) |
| 21:08 | first DONE in `final_route/` |
| 21:19 | best lap, 349 vias |
| ~21:25 | plateau |
| 21:34 | final frozen |
| 21:36 | verifier launched |
| ~21:44 | verdict FAIL |
| 21:45-21:58 | pair-fix attempts |
| ~21:59 | ledger closed |
| ~22:00 | freeze marker and `measure.py` |
| 22:02 | TOOL_GAPS finished |

Where the time went:

| Activity | Time |
|---|---|
| Placement and judging | about 25 min |
| DDR length window | about 1 h 30 (the route_bus runs alone were 23-35 min each) |
| Post-DONE laps | about 25 min |
| Verifier | about 8 min |
| Pair fixes | about 13 min |
| Grading and paperwork | about 20 min |

`measure.py --self --evidence` (`measure_self.txt`):

| Measure | Value |
|---|---|
| Wall clock | 2:58:47 |
| Model time | 3692.7 s |
| Other tool time | 6127.6 s |
| Waiting on jobs | 907.6 s |
| Tool calls | 437 |
| Agent spawns | 1 (the verifier) |

## 8. Tool gaps

There are 14 entries in `TOOL_GAPS.md`, ranked by cost. Each has a repro command using inputs in `repro/`, plus a `gh issue list` search result.

1. **No `.kicad_dru` length window.** No tool grades or follows it, and both the bus step and the default chain break it (about 1 h 30). Workaround: `helpers/kicad_length_check.py`.
2. **`route_diff` false pair claims.** It reports "coupled" and "matched" pairs that are uncoupled and skewed, and nothing in the repo grades a routed pair (about 40 min). Workaround: `helpers/pair_check.py`.
3. **`route.py` strict collapse (#1063) claims removals it never writes.** It drops the net-name map on a mixed-format file (about 25 min). Workaround: `helpers/strict_collapse.py`.
4. **`board_score` length cannot see via-in-pad joins**, so the group reads UNGRADED (about 20 min). Workaround: `helpers/vip_joins.py`.
5. **`bga_fanout --check-for-previous` lays escapes over foreign tracks.** check_drc went from 64 to 98, including 20 DQ5↔VMEM hits (about 20 min).
6. **place_simple leaves the C20 pin limit broken in 33 of 36 seeds**, and the judge never sees floorplan errors (about 15 min).
7. **B-face parts pile up under an F-face BGA**, and `apart` cannot stop it (about 15 min).
8. **route_bus output is missing its `.kicad_dru` and brief sibling files** (about 10 min).
9. **route_bus cages a VMEM ball and puts lane copper on the GND plane layer** (about 10 min).
10. **check_drc's default margin passes U1's 0.12 mm clearance grazes**, which KiCad flags (about 10 min).
11. **`converge record` refuses board_score rows after quick_score rows** (about 10 min).
12. **check_assembly passes the C20/FB2 courtyard overlap** that KiCad flags (about 5 min).
13. **No tool runs the seed judge or a post-DONE lap** (two helpers: `judge_chain.sh`, `opt_lap.sh`).
14. **Skill text gaps.** One example: the verifier brief fails any declared class that is ungraded, but board_score has no diff-pair component at all.

## 9. Verifier verdicts

**verdict_1: FAIL.**

| Lens | Result |
|---|---|
| connectivity | PASS |
| drc | PASS (check_drc 0; kicad-cli 0 errors) |
| spec | FAIL: DQS0 skew 4.60 mm and uncoupled; CLK0 2.97; DQS1 1.24 |

Every stack gate passed:
- identity and rules;
- check_assembly, floorplan, render_placement, mechanical 7 of 7;
- board_score blocking 0, check_complete DONE;
- KiCad length window.

The verifier itself called the FAIL a judgement call: read another way, the spec lens would be PASS. The FAIL stands as reported. Only one verifier call was used. The pair fixes that followed did not produce a candidate worth re-verifying.

Files: `verdict_1.txt`, `verdict_1_{connectivity,drc,spec}.txt`, `verify_1_score.json`, `verify_1_render.json`, `verify_1_F.png`, `verify_1_B.png`.

## 10. Deliverables

All under `wk/gp14/14_imx6ulz_4l/`:
- **Board and placement:**
  - `final.kicad_pcb` with its sibling files, and `FINAL.sha256`;
  - `groups.json` and `intent.json` (unchanged), plus `groups_r2/r3.json` and `intent_r2/r3.json`;
  - `CHOSEN.json`.
- **Routing and rounds:**
  - `final_route/`, holding `redo_commands.sh`;
  - `r1/`, `r2/`, `r3/`, each with `fixed.kicad_pcb`, `groups.json`, `intent.json`, seeds and `judge.json`.
- **Grading:**
  - `ledger.jsonl`, closed `--final`;
  - `grade_self.txt` and `grade/grade_final.json`;
  - `measure_self.txt`.
- **Helpers and gaps:**
  - `TOOL_GAPS.md`;
  - `helpers/` (6 scripts);
  - `repro/`.
- **Markers:** `DONE`, the freeze marker. `REPORT_DONE` was not created because the `REPORT.md` write was refused; this text is that report.
- There is no datasheet folder to delete.
