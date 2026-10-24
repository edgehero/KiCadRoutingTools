# REPORT — gpm board 14 imx6ulz_4l (mode `full`)

The run followed `/plan-pcb-placement full` by hand. `/analyze-power-nets` was also done by hand: its tool output was absurd (TOOL_GAPS 12), so I set the power track widths myself.

There was an orchestrator restart after ~1 h of no activity (09:45Z–10:45Z). That hour is inside the wall time but no work happened in it.

## 1. Result

**Delivered:** `wk/gpm/14_imx6ulz_4l/delivered.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.design-brief.json`), sha256 `51268e00d9c4d836aecaef7384bc39a4438a83918ab136b146205c996250be40` (in `DELIVERED.sha256` and `DONE`).

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking | **0** |
| `check_complete` (with spec flags) | **DONE**; `--authored-from` input: **DONE** |
| `check_connected` | all 134 nets connected; the KiCad refill agrees |
| `check_drc` (`--clearance-margin 0.1`) | 0 violations; 8 length-rule nets graded, 0 out of range; via-in-paste 0 unprotected, 193 filled+capped |
| `check_assembly` | buildable (blocking 0; 16 advisory, 1 waived) |
| `check_floorplan` | 0 errors, 9 warnings |
| mechanical (7 fixed poses) | 7/7 exact; Edge.Cuts identical to the input |
| `kicad_drc_compare` | CONSISTENT; KiCad reports 0 unconnected |
| `grade.py` (`--spec min-track-width=0.1 min-via-diameter=0.45 min-via-drill=0.25`) | `done: true` |
| Independent verifier | call 1 **FAIL** (spec lens), call 2 **PASS** on all three lenses |

`blocking_by`: unrouted 0, broken 0, drc 0, drc_via_in_paste 0, undersized 0, floorplan 0, assembly 0. Four components have no spec on this board, so nothing graded them: diff_pairs, impedance, length, net_widths. The verifier examined the pairs and the length group itself (below).

**Quality:** 377 vias, 2496.77 mm of copper, 2361 segments. The first DONE board had 461 vias and 2488.31 mm.

**DDR3 length group** (`.kicad_dru` rule "byte0 delay matching", 11.5–14.5 mm) — all eight in the window:

| Net | Length (mm) |
|---|---|
| DQ0 | 13.06 |
| DQ1 | 12.83 |
| DQ2 | 14.41 |
| DQ3 | 13.25 |
| DQ4 | 12.10 |
| DQ5 | 14.29 |
| DQ6 | 12.03 |
| DQ7 | 12.86 |

**Differential pairs** (named `_P`/`_N` only; all coupled at a 0.1 mm gap):

| Pair | Skew (mm) | Coupled length (mm) |
|---|---|---|
| DQS0 | 0.424 | 15.16 of 16.55 |
| DQS1 | 0.309 | 6.80 of 11.12 |
| CLK0 | 0.020 | 23.65 of 27.76 |

The `.kicad_dru` rule "target length and skew" targets netclass `DF_100ohm`. The project has no such netclass, so the rule applies to no net, in KiCad as well.

## 2. Groups and judgement calls

`groups.json` (v2) has 9 groups:

- **core:** U1 plus 41 parts — its decaps, FB2/FB3, the crystal Y1 with C11/C15, R16, R2, C39, and U8/C19/C20.
- **dram:** U2 plus 18 parts — VMEM decaps, the VREF divider R13/R14 and R1.
- **power:** the three TLV62568 bucks U4–U6 with their templates.
- **power_in:** J1, at the north edge.
- **boot_cfg:** SW2 plus 48 strap resistors.
- **boot_mode:** SW1, R65, R66.
- **reset:** U7, R3, R67, C17, SW3, C16.
- **io_south:** J2, J3, J6, J7 and R68–R73, at the south edge.
- **storage:** J4 (declared pose), C60, J5.

Judgement calls, each with its reason:

1. **U8/C19/C20 moved into the core group (pass 2).** U8's output is U1's SNVS supply at ball P12.
2. **Added an intent row** in `intent_run.json`: proximity `U8.2 → U1.P12, max 7.0 mm, pad_edge`, error-graded. In passes 1 and 2, 11 of 12 seeds broke the P12 decap limit, because place_simple prices it flat (TOOL_GAPS 9). With the row, pass 3 gave 6 clean seeds out of 12.
3. **Added three TLV62568 templates** (U4: C25/L2/C26/R8/R7; U5: C21/L1/C22/R5/R6; U6: C27/L3/C28/R11/R10). They follow TI SLVSD89B §10.1 Figure 20, turned 180°, read through `helpers/pdfpage`.
4. **J1 at the north edge and the io_south connectors at the south edge.** These are cable entries placed next to the U1 balls that serve them.
5. **Kept seed 6 of pass 3** (judge order 6, 11, 9, 7, 3, 1; fast route: blocking 2, joins 2, 404 vias).
6. **Made 19 hand `place_pose` moves** (`CHOSEN.json` `after`). 14 boot resistors, C13, C23, C48 and C33 came out from under U1's ball field, and R2 came out of the DDR corridor. Dog-bone vias in their pads had shorted them (TOOL_GAPS 4).
7. **Planes:** In1 is a solid GND pour; In2 is split between +3V3 and VMEM.
8. **Power track widths set by hand** (0.2–0.6 mm) instead of the tool's 3.0 mm recommendations.
9. **DQ0–7 routed first, in four length-matched steps:** DQ4+DQ6, then DQ2+DQ5, then DQ3+DQ7, then DQ0+DQ1. Settings: amplitude 0.5, tolerance 0.8.
10. **DQS0/1 and CLK0 treated as declared pairs** and routed coupled from the bare balls, before the fanouts. The gap is 0.1 mm, the board's clearance floor; no impedance is declared.
11. **Two hand vias placed before later steps:** a VMEM via-in-pad at U2.C1 (73.6, 107.8) and a DQ13 dog-bone via at (82.4, 105.0).
12. **Kept the 17 KiCad `courtyards_overlap` errors.** check_assembly grades them advisory, and two courtyard-clean re-layouts (A7, A8) each left blocking 1.
13. **Kept the label-tidied board** (silk 257 → 106).
14. **Stamped IPC-4761 Type VII on 194 via-in-pad sites** after the fill (TOOL_GAPS 5).
15. **EMC rows:** none were given, so none were added.

## 3. Stop rule and remaining items

Stop rule **1 (DONE)**. No blocker remains. Disclosed items that do not gate:

- **17 KiCad `courtyards_overlap` errors:** C23/C33, R19/R28, R2/SW1, R20/R28, R21/R27, R27/R28, R27/R29, R28/R53, R33/R37, R37/R41, R38/R39, R38/R47, R43/R56, R43/R64, R53/R55, R56/R62, R56/R64. check_assembly grades them 16 advisory plus 1 waived (R2/SW1, edge class).
- **check_floorplan warnings (9):**
  - `decap_pin_uncovered` ×4: U1 VDD_HIGH_CAP, and the switch nodes of U4, U5 and U6.
  - `decap_ungraded` ×4: C16, C22, C28, C60.
  - Y1 pad 3 is 8.23 mm from U1 T17; the limit is 8.10.
- **Return paths:** check_impedance finds 40 of 49 DRAM nets crossing a void, 182.3 mm in total. DQS0 runs on In2.Cu and is read as 95% over void, because the tool takes the unpoured B.Cu as its reference. The stackup is a placeholder (every dielectric 0.01 mm), so this is not conclusive.
- **GND return vias:** 25 of 113 DRAM signal vias are more than 3 mm from a GND via; the worst is CAS_L at 8.2 mm. Every strobe and clock via is within 2.26 mm.
- **KiCad checks that do not gate:** 149 lib_footprint_mismatch, 2 lib_footprint_issues, 106 silk.

## 4. Floors

- **Spec flags:** track 0.1, via 0.45 / drill 0.25, clearance 0.1, hole-to-hole 0.25, edge 0.3. Routing ran with `--escalation board`.
- **`rules.min_clearance` became 0.08.** That number is U2's footprint-level clearance override, not the board's 0.1 (TOOL_GAPS 16). Every netclass stays at 0.1.
- **U1 fanout went below the board floor:** its under-pad shrink rescue ran at 0.09 mm clearance and rescued 2 of 2 dropped balls. The U2 rescue at 0.09 rescued 0 of 3. check_drc grades the shipped copper clean at 0.1.
- **`check_complete --authored-from` lists one floor:** min_hole_clearance authored 0.15, declared 0.1. kicad-cli measured the copper still at 0.15 (0 violations).
- **9 power nets narrowed to 0.1 mm** at some sites (route.py's `Design rules` line):

  | Net | Requested (mm) | Length at 0.1 mm |
  |---|---|---|
  | VDD_ARM_SOC_IN | 0.4 | 14.6 mm |
  | GND | 0.3 | 36.8 mm |
  | VDD_SOC_CAP | 0.3 | 19.7 mm |
  | VDD_ARM_CAP | 0.3 | 8.4 mm |
  | VDD_HIGH_CAP | 0.25 | 1.9 mm |
  | VDD_SNVS_IN | 0.2 | 2.2 mm |
  | +3V3 | 0.3 | 13.8 mm |
  | VDD_HIGH_IN | 0.3 | 5.8 mm |
  | VMEM | 0.4 | 31.6 mm |

## 5. Silkscreen

KiCad silk counts went from **257** (134 silk_overlap + 123 silk_over_copper) to **106** (66 + 40) after `beautify_labels`. The tidied board, `labelled.kicad_pcb`, was kept and is the one that was filled.

## 6. Fill

`fill_for_delivery` ran on `labelled.kicad_pcb`. It re-saved the file in KiCad 10 format, which wrote an explicit all-"no" via-protection block on all 377 vias. That would have made the board grade blocking.

`helpers/stamp_type_vii.py` removed exactly that block, then ran the repo's own `fab_notes.ship_via_protection_file`, which stamped 194 vias Type VII. No copper changed and the zone fill is intact. The board does not need a refill before plotting.

## 7. The routing chain (`final_route/`)

1. copy_board, then route_planes: GND on In1; +3V3/VMEM split on In2.
2. Four DQ route.py steps (judgement call 9).
3. **Hand join 1:** check_join VMEM via-in-pad at U2.C1.
4. route_diff for CLK0 and DQS* (`--diff-pair-intra-match`).
5. **Hand join 2:** check_join DQ13 dog-bone via at (82.4, 105.0).
6. bga_fanout U1 and U2 (dogbone, `--check-for-previous`; pair nets, planes and DQ8/DQM0 excluded).
7. place_fanout_clearance.
8. route.py `--nets '*'` three times, with power widths. The third run gave blocking 0.
9. Hygiene:
   - j1: check_join for NVCC_PLL_OUT.
   - j2: `helpers/remove_segments.py` removed 2 dangling VMEM stubs, 1 dangling DQ1 via and 1 pad-internal stub.

The last board is copied to `routed.kicad_pcb`. The hand joins are in `hand_join_1.sh` and `hand_join_2.sh` and the split plan files, but they are not in `redo_commands.sh` (TOOL_GAPS 8).

## 8. Timeline (UTC)

| Time | Event |
|---|---|
| 09:06 | FIRST_CMD |
| 09:16 | groups v1, templates written |
| 09:17–09:24 | placement passes 1 and 2 rejected (P12 decap limit, 11/12 seeds) |
| 09:24 | proximity row added; pass 3 |
| 09:26 | pass 3: 6 clean seeds |
| 09:31–09:37 | judged; seed 6 kept |
| 09:37 | full-route arm A and bus arm B launched (arm A's first start died on route_diff `--json-out`) |
| 09:45–10:45 | **orchestrator stall** (~1 h of no activity, restart) |
| 10:48 | bus arm rejected; arm A at blocking 17 |
| 10:48–11:30 | 19 hand moves; arms A2–A4: blocking 15 → 8 → 6 |
| 11:33–11:59 | DQ length-window order search (25 orders) |
| 12:03–12:07 | A5 blocking 7, then A6 **blocking 0** |
| 12:17 | **first DONE** (461 vias) |
| 12:17–12:36 | arms opt1, opt2, A7, A8 rejected |
| 12:37 | verifier call 1 |
| 12:47 | verifier 1 **FAIL** (pairs uncoupled) |
| 12:47–13:26 | arms A9–A17 (pairs early, 2 hand vias); A17 blocking 0, 378 vias |
| 13:31 | DONE #2 delivered |
| 13:35 | verifier 2 **PASS** |
| 13:36–13:40 | ledger closed, markers written, TOOL_GAPS updated |

## 9. Where the time went

`measure.py --self --evidence`, at 13:36Z: wall 4:30:13, of which:

| | Time |
|---|---|
| Waiting on jobs | 28 min |
| Other tool time | 2 h 52 min (includes the stall hour) |
| Model time | 1 h 11 min |

That was 421 assistant turns and 430 tool calls. The most-used scripts: board_score 46, check_drc 44, route.py 34, check_weird 25.

By topic:

| Topic | Time |
|---|---|
| Length window | ~1 h |
| Verifier-1 pair fix | ~40 min |
| Foreign-pad via shorts and hand moves | ~40 min |
| Placement passes and judging | ~30 min |
| Courtyard arms | ~25 min |
| Hygiene, fill and stamping | ~35 min |

## 10. Tool gaps

`TOOL_GAPS.md` has 17 ranked entries, each with a repro under `repro/` and a gh issue search:

1. The `.kicad_dru` length window is not routed to.
2. A declared-by-name pair is ungraded, so DONE shipped an uncoupled pair. Each tool said "fine".
3. Pairs routed early wall in plane and escape balls (#677 open).
4. Dog-bone vias land in foreign far-side pads (contact shorts).
5. fill_for_delivery's KiCad-10 re-save marks every via "not filled, not capped". The board graded 212 blocking on unchanged copper.
6. route.py leaves dangling stubs and sub-floor webs on a blocking-0 board.
7. route_diff has no rip or force-reroute.
8. check_join does not record into the redo manifest.
9. place_simple's flat decap-limit price (#1320).
10. `bga_fanout --check-for-previous` puts vias on an existing track.
11. No courtyard-aware move.
12. analyze-power-nets recommends 3 mm widths.
13. route_bus drops the `.kicad_dru` and locks its lanes.
14. No PDF renderer.
15. route_plan_check R17 treats a split layer as a solid plane.
16. A footprint clearance override becomes the board floor.
17. route_diff has no `--json-out`.

Helpers, each tied to an entry: `dq_sequence_search` (1), `pair_order_search` (3), `stamp_type_vii` (5), `remove_segments` (6), `strip_nets` (7), `power_widths_repro` (12), `pdfpage` (14).

## 11. Verifier verdicts

- **Call 1** (delivered sha e9774a68…, 461 vias): **FAIL** on the spec lens: "declared diff pair /DRAM/DRAM_DQS1 has diff_pairs UNGRADED and ships uncoupled (0.00 of 25.10 mm coupled) with P/N skew 15.467 mm, CLK0 skew 4.242 mm". Connectivity and drc passed. Files: `verdict_1*.txt`; the board is saved in `old/done1`.
- **Call 2** (sha 51268e00…be40): **PASS** on connectivity, drc and spec. Files: `verdict_2.txt`, `verdict_2_connectivity.txt`, `verdict_2_drc.txt`, `verdict_2_spec.txt`.
  - It examined the pairs (coupled, skew 0.42 / 0.31 / 0.02 mm) and the DQ group (spread 2.38 mm, inside the window, meander gaps at least 1.00 W) independently.
  - Caveat it recorded: board_score's diff_pairs component is still formally ungraded, because the board has no dru skew rule.
  - Two of the three allowed calls were used.
