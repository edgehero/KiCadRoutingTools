# REPORT: gpm board 02, sonde_xilinx (`/plan-pcb-placement full`)

**Result: DONE.** Delivered board `wk/gpm/02_sonde_xilinx/delivered.kicad_pcb`
(sha256 `224e30a84609ec9f80fb8ce3cbe06a2c86d7d35887744dbaa1f55ff777810059`), filled, with its `.kicad_pro`.
The verifier PASSed on call 1 of 3. Wall time from FIRST_CMD (16:49:21Z) to DONE was about 21 min.

## 1. Result

| DONE condition (full mode) | measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking | **0** |
| unrouted / broken | **0 / 0** |
| `check_complete` (all spec flags) | **DONE** |
| `check_complete --authored-from <input>` | DONE, no floor listed |
| `check_assembly --baseline <input>` | buildable (blocking 0) |
| `check_floorplan --intent intent_run.json` | 0 errors, 1 warning (U2 pins_to_edge, 1.82 mm) |
| `check_connected` | all nets fully connected |
| `check_drc --baseline <input> --clearance-margin 0.1` | no violations |
| KiCad DRC (`kicad_drc_compare`) | kicad=0, check_drc=0, CONSISTENT; connwidth 0, starved thermal 0 |
| off-outline copper (render_placement `a_off_outline`) | pad_copper_gating [], graphic_copper [], keepout_copper [] |
| independent `grade.py --mode full` | `done: true`, blocking 0, drc 0 |

**`blocking_by`:** unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, net_widths 0, drc_via_in_paste 0.

**Quality:** **vias 0 / copper_mm 556.16 / segments 116**. joins_needed 0.

**Spec flags used** (in every board_score, check_complete and grade.py call): `--net-min-widths net_min_widths.json`
(VCC and /PWR_3,3-5V at ≥ 0.5 mm, from analyze-power-nets), `--min-track-width 0.2032 --min-via-diameter 0.889
--min-via-drill 0.508` (the board's own Constraints). **UNEXAMINED** (ungraded, not passed): diff_pairs, impedance,
length. The board declares none of them: no P/N pairs, no impedance nets, no length groups. Its signals are a PC
parallel port bit-banging JTAG through 74LS125 buffers.

## 2. The board, the groups and every judgement call

The board is 80.4 x 43.18 mm, 2 layers, 25 parts and 43 nets, all through-hole except the two DSUB edge-mount pad rows.
The input was a pile: every part sat off the outline, nothing was locked, and there was no mechanical.json, so there
were no fixed poses. The design brief declares J1 on the west edge and J2 on the east edge, both with `along_edge`
unknown. The source's board-wide GND pour on B.Cu was kept.

**What the circuit is** (read from the nets; a Xilinx "Parallel Cable III"-style JTAG probe):
- J1 (DB25) goes to the PC's parallel port. Its data lines D0-D4 (pins 2-6) pass through 100R R6-R10 into U1 (74LS125).
- U1's four outputs each carry a 100 pF edge-rate cap (C2-C5) and a 100R series resistor (R11-R14) out to TDI, TCK, TMS and DONE.
- Those signals leave on J2 (DB9, bottom side) and on P1 (1x6 header), which is wired in parallel with J2.
- U1A is the PROG driver: input tied low, R2 5.1K pull-up. U2 (74LS125) buffers that node back to J1 pin 13 through R4 (47R).
- Power comes from the target: J2.1 / P1.1 through D2 (BAT46) onto VCC, with C1 (1 uF) and R5 (1K load). D1 + R1 report VCC to J1 pin 15.
- J1 pins 8/11/12 are tied together, the cable-detect loop.

**groups.json** (5 groups; `check_groups`: 0 errors, 0 warnings, 0 template hints):

| group | refs | why / judgement |
|---|---|---|
| pc_port (interface) | J1, R6, R7, R8, R9, R10, D1, R1 | R6-R10 sit at the port end because the PC is the driver on D0-D4 (series R at the driver); they border core. D1/R1 are the VCC-sense path to J1.15. |
| core | U1, C1, C2, C3, C4, C5, R2 | C2-C5 sit on U1's output nodes, before the series R. R2 is U1A's pull-up. C1 is the only VCC cap, so it is put with U1 as its decap (place_simple: "decap C1 on VCC serves U1"). |
| readback | U2, R4 | U2 buffers U1A-O back to the port. R4 is at U2 because U2 pin 3 is the output (driver end). |
| target_port (interface) | J2, P1, R11, R12, R13, R14 | The output series R are put at the connector end. Between a chip and a connector there is no preferred end (placement-lessons), and this balances the group sizes. |
| power (power) | D2, R5 | D2 is the reverse-blocking diode from the target's supply; R5 is the VCC load. near target_port and core, no edge hint. |

- **No template candidates.** There is no switching stage (no inductor, transformer, flying or bootstrap cap) and no RF chip, so §3.5 made no templates and no `skip` rows were needed.
- **No crystal claims, no proximity rows.** `emc_roles` found no converter, crystal, oscillator or ESD part.
- **EMC rows:** none were given by the user (the user was unavailable), none were invented, and the board has none to propose.

**Rows added to `intent_run.json`** (a copy of the read-only `intent.json`, used for every step from placing on):

| row | value | reason |
|---|---|---|
| `edge_connectors[J1].overhang_mm` | min 25.12, max 25.17 | The footprint draws its "PCB edge" on Dwgs.User at local y=+1.99, so this edge-mount DSUB is built straddling the board edge: its body is designed to sit past the edge. The band is graded on the courtyard (legacy_occupancy@margin=0), summed over every side crossed. J1's 54.1 mm courtyard is longer than the 43.18 mm west edge, so at the pose where the PCB-edge line meets the board edge the reading is 14.2 (west) + 10.92 (north + south) = 25.12. max 25.17 is where pad copper reaches the 0.2 mm edge floor. Without the band J1 got no seat at all (see TOOL_GAPS 1). |
| `edge_connectors[J2].overhang_mm` | min 14.20, max 14.25 | The same reasoning for the DB9 (14.2 mm of courtyard past the east edge at the marker pose). Without it J2 was seated with its pads 5.30 mm inside the board, which cannot be assembled, and every grader passed it. |

No other row was added: no overlap_waivers (nothing locked), no proximity, no templates.
`waive_locked_overlaps.py` was not needed because no part is locked.

**Other judgements** (the user was unavailable):
- I measured J1's and J2's seat (rotation 270, mating face out) with `place_pose` on scratch copies and `check_floorplan` (`facing west/east [courtyard+fab+marker, strong] pass`) before placing.
- I kept the designer's GND pour as drawn (B.Cu, thermal relief, 0.508 clearance) and ran no `route_planes` step. A re-pour would make it solid, which matters on a hand-soldered THT board, and the plan checker's R07 refuses `--thermal-relief`. route.py's in-run finalize welds GND into the existing zone.
- `/VCC_SENSE-ERROR*` is listed as a "power" net by `list_nets` (its name only). It is a status line through R1 100R, so it was routed as a signal.

## 3. Placement (§3.6-3.7)

- **Pass 1** (the only pass): `place_simple` with the default 12 seeds (6 scattered, 6 clustered), `--jobs 4`, and no extra place_args. All 12 seeds came out legal, buildable and floorplan-clean in 10 s. The judge named seeds 4, 9, 0, 11, 1, 6.
- **Judging chain** (`judge_chain.txt`, run by judge_seeds at `--quick 2`, `KICAD_ROUTE_TRACE=1`, `--jobs 3`): one `route.py '*'` step with track 0.3, via 0.889/0.508, and power VCC, /PWR_3,3-5V and GND at 0.5.

| seed | start | final.cost | fast blocking | vias | copper_mm | segments |
|---|---|---|---|---|---|---|
| **4 (kept)** | scattered | 568.3 | 0 | **5** | **534.76** | 286 |
| 1 | scattered | 637.2 | 0 | 5 | 546.45 | 386 |
| 6 | clustered | 657.2 | 0 | 5 | 586.16 | 350 |
| 9 | clustered | 578.1 | 0 | 8 | 524.67 | 380 |
| 11 | clustered | 635.5 | 0 | 9 | 568.27 | 370 |
| 0 | scattered | 629.3 | 0 | 12 | 547.88 | 381 |

- **Kept:** seed 4 → `final.kicad_pcb` (sha `d66354ce...`). CHOSEN.json is `{"seed": 4, "start": "scattered", "pass": 1, "intent": "intent_run.json", "place_args": [], "after": []}`.
- `route_review` on `s4_fast` listed 0 turned two-pad parts, so no `place_pose` changes were made after place_simple. `placed_from/` holds `fixed.kicad_pcb` (+ .kicad_pro), `groups.json` and `intent_run.json`.

## 4. Routing (§3.8: `/plan-pcb-routing`, followed by hand)

I followed `/plan-pcb-routing` by hand from its SKILL.md, and `/analyze-power-nets` by hand from its SKILL.md.

**Analysis:**
- **Step 0 gate:** check_assembly buildable; the baseline board_score was unrouted 25, broken 4.
- **2 layers; stackup** is KiCad's default (1.51 mm, εr 4.5). That is irrelevant because no net is impedance-controlled.
- **Fanout:** none. Every part is THT except the DSUB edge rows at 2.77 mm pitch.
- **Diff pairs:** none. **DDR / length / impedance:** none.
- **High-speed scan:** low-speed bit-banged JTAG. GND return vias and stitching were skipped (Step 10 rule 10, Step 3 "skip on low-speed boards"). **Keep-away:** none (all digital).
- **analyze-power-nets:**
  - Classifications: J2 and P1 are POWER_SOURCE (the target's 3.3-5 V on pin 1; 100 mA is an estimate). D2 is PASS_THROUGH (BAT46, IF 150 mA). J1 and D1 are SHUNT. U1 and U2 are CURRENT_SINK at 22 mA each (TI SN74LS125A supply current max 22 mA).
  - Recommendation: VCC 0.5 mm. I also carried /PWR_3,3-5V (the same current, upstream of D2) and GND (poured) at 0.5 mm.
  - Currents are datasheet maxima plus an estimate for the target supply. The tracer under-counts the input path (TOOL_GAPS 2); the true total, under 100 mA, still maps to 0.5 mm.
- **Design rules:** clearance 0.254 (Default class, passed by default), via 0.889/0.508 (the board's min via = working floor), signals 0.3 mm. That fits one track between any two 2.54 mm-pitch pins at 0.254 clearance; the netclass's 0.635 drawing width does not.
- **Step 5b reconciliation:** one route step `'*'`, no exclusions, poured GND in `--power-nets`; all three asserts are empty.
- **Step 9:** `final_route/sonde_xilinx_plan.sh` passes `route_plan_check.py` (17 rules ok). `sonde_xilinx_plan.json` was emitted by manifest_to_plan (1 step).

**Arms** (Step 8, "2-layer THT board WITHOUT the buses": route both and keep the better). Same placement (final.kicad_pcb), full routes:

| arm | flags beyond the base chain | blocking | vias | copper_mm | segments |
|---|---|---|---|---|---|
| A (final_route_old1/) | defaults (F 1.0 / B 3.0, via cost 75) | 0 | 8 | 546.10 | 127 |
| B (final_route_old2/) | `--layer-costs 1.0 1.0 --via-cost 600` | 0 | 0 | 560.31 | 115 |
| **C (final_route/, shipped)** | B + `--direction-preference-cost 2000` | 0 | **0** | **556.16** | 116 |

Scratch arms, not shipped:
- B + direction preference 1000: 0 vias / 559.86 mm.
- B + 4000 and turn 2000: 0 vias / 559.01 mm.
- The THT-bus bundle (via cost 150): 7 vias.
- Direction preference 0, or turn cost 300/500: 3 vias each.

Arm B on the other five judged seeds: s1 1 via / 537.72 mm, s0 1 / 562.83, s9 2 / 605.09, s6 2 / 632.72, s11 3 vias plus undersized 2. Seed 4 stays best.

The shipped chain is `final_route/redo_commands.sh` (copy_board + one route.py):
`route.py in.kicad_pcb routed.kicad_pcb --nets '*' --track-width 0.3 --via-size 0.889 --via-drill 0.508 --power-nets VCC '/PWR_3,3-5V' GND --power-nets-widths 0.5 0.5 0.5 --layer-costs 1.0 1.0 --via-cost 600 --direction-preference-cost 2000`

- route.py: 26/26 nets routed, 0 vias, `design_rules.count` 0 (nothing narrowed), `power_widths` under_mm 0 on all three nets.
- Plane finalize: "all zone nets complete (fill-aware)"; JSON_ORACLE available, 0 rounds, 0 remaining.
- Copied out with copy_board to `routed.kicad_pcb`.

**Remaining blockers:** none.

## 5. Stop rule

**Stop condition 1: DONE.** The first DONE was arm A, about 11 min after FIRST_CMD. After DONE, vias were optimised to 0 (their floor, arm B), then copper: 8 parameter arms and 5 alternative seeds were tried, and arm C was the best 0-via result. I stopped there: the remaining gains were under 1% of copper and every cheaper-copper arm added vias. The ledger is closed with `--final --stop-condition 1` and the three verifier lens files.

## 6. Floors

- Routed at the board's Default-class clearance 0.254. min_clearance_used is 0.254.
- Signal tracks are 0.3 mm: above the board's min_track_width 0.2032, below the netclass drawing width 0.635, which is not a DRC floor. Power tracks are 0.5 mm.
- Vias are 0.889/0.508 (= the board's min_via_diameter); none were placed.
- route.py's project writeback: `min_copper_edge_clearance` 0.01 → 0.2 (fab-edge pin), `min_via_drill` None → 0.508.
- `check_complete --authored-from <input>`: DONE, no floor listed. Nothing went below an authored or fab floor.

## 7. Silkscreen (§3.9.1)

KiCad's silk classes, `kicad-cli pcb drc --severity-all`:
- **Before** the tidy (routed.kicad_pcb): 8 (silk_overlap 1, silk_over_copper 4, silk_edge_clearance 3).
- **After** `beautify_labels` (labelled.kicad_pcb): 3 (silk_edge_clearance 3).

**Kept: labelled.kicad_pcb.** The 3 left are J1's own footprint silk clipped by the board edge the connector straddles. They are footprint art, not labels.

## 8. Fill (§3.9.2)

`fill_for_delivery` ran on labelled.kicad_pcb → `delivered.kicad_pcb`: 5 filled polygon blocks, net classes preserved, KiCad unconnected 18 → 0. The board needs no refill before plotting.

Note: B.Cu carries signal tracks at layer cost 1.0, so the GND fill is in several islands, every one connected (KiCad 0 unconnected, check_connected clean). This board is low-speed, so that was accepted.

## 9. Timeline and where the time went

| time (Z) | step |
|---|---|
| 16:49:21 | FIRST_CMD; read the task, the skill and the references |
| 16:50-16:53 | board_brief, board_context, groups.json, check_groups |
| 16:53 | J1/J2 seat measured on scratch copies; intent_run.json with overhang bands |
| 16:54:07-16:54:17 | place_simple pass 1 (12 seeds, 10 s) |
| 16:55-16:58 | checks, renders, ledger, analyze-power-nets (datasheet lookups), judging chain |
| 16:58:41-16:58:47 | judge_seeds (6 seeds, 6 s) → seed 4 |
| 17:00 | arm A full route: first routed board, **first DONE** |
| 17:01-17:04 | arm B; 5 other seeds and 8 parameter arms in scratch; arm C shipped chain |
| 17:05-17:06 | labels, silk grading, fill_for_delivery, self-checks |
| 17:06-17:09 | verifier (call 1, PASS), meanwhile TOOL_GAPS evidence and repros |
| 17:10 | ledger closed, grade.py, measure.py |

`measure.py --self --evidence wk/gpm/02_sonde_xilinx` gives a wall clock of 0:20:58, made of 941 s of model time, 311 s of tool time and 6 s waiting on jobs, over 117 tool calls (`measure_output.txt`).

The tools were fast throughout: placing 10 s, judging 6 s, each full route 4 s. Most of the wall time was reading the skill and deciding things: the DSUB seat measurement, the groups, and the analyze-power-nets lookups.

## 10. Tool gaps (detail and repros in TOOL_GAPS.md)

1. **Edge-mount DSUB depth.**
   - The footprint's own "PCB edge" marker is read by nothing.
   - Without a band, J2 seats with its pads 5.30 mm inside the board and is graded `pass`; J1 gets no seat.
   - SKILL §3.4's "an overhang of x reads x" is false for a part longer than its edge, because the band sums the corner crossings. The literal reading (min 14.2) seats J1 with pads 2.51 mm in and grades `pass`.
2. **`analyze_power_paths.trace_power_paths`** keeps one sink per net (dict overwrite). It traced 1 path at 22 mA through D2 where 2 sinks draw 44 mA, a silent under-count of a pass-through path's current.
3. **The `check_assembly` echo** prints "pad copper off-board: J1 (0.009mm), J2 (0.009mm)" for pads that are 0.245 mm inside the outline. It measures pad AABBs against the outline inflated by the 0.254 clearance. It is not gating, but the label is false.
4. **No PDF reader on this machine.** poppler, pypdf and fitz are all absent, and Read's PDF pages need pdftoppm. ST's site refused the BAT46 download. Datasheet numbers came from TI's HTML product page and search excerpts.

Tools that said "fine" about something that was not: check_floorplan and check_assembly on J2 seated 5.30 mm deep (gap 1). I caught it before placing and did not ship it.

## 11. Verifier verdicts

- **verdict_1.txt: VERDICT=PASS** (call 1 of 3). Lenses: connectivity PASS, drc PASS, spec PASS.
- It re-measured the mechanical facts: J1 is on the west edge facing out and J2 on the east edge facing out, each with its "PCB edge" line 0.005 mm from the board edge and pad copper 0.245 mm inside.
- Its non-gating notes: check_floorplan exits 4 with `pass:false` for ungraded/owed rules only (5 rules owed a written answer: zone_containment, zone_side, decap_distance, decap_pin_distance, legality). It also reports a body-to-edge band warning on U2 0.547, C1 0.623, D1 1.175, R1 1.274, R2 1.753 and R5 2.063 mm.

## 12. Hand-back

- Delivered: `delivered.kicad_pcb` (+ .kicad_pro, .kicad_prl, .design-brief.json), `DELIVERED.sha256`, `DONE`.
- Boards: `routed.kicad_pcb` (unfilled, unlabelled-tidy), `final.kicad_pcb` (the kept placement), `labelled.kicad_pcb`.
- Run files: `groups.json`, `intent.json` (given, unchanged), `intent_run.json`, `CHOSEN.json`, `placed_from/`, `final_route/` (with redo_commands.sh and the plan .sh/.json), `ledger.jsonl` (13 rows, closed).
- Grading: `grade_output.txt` / `grade_delivered.json` (grade.py) and `measure_output.txt` (measure.py).
- Datasheets: the folder was moved to `old/datasheets/` (§6.4; the orchestrator deletes it).
- Input sha256s were re-checked at the end and match the README for intent.json, the design brief, the .kicad_pcb and the .kicad_pro.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE** (stop condition 1). The verifier passed on its first call, with all three lenses passing. The harness refused the REPORT.md write, so REPORT_DONE was not created and the full REPORT.md is below.

- **Delivered board:** `wk/gpm/02_sonde_xilinx/delivered.kicad_pcb`, sha256 `224e30a84609ec9f80fb8ce3cbe06a2c86d7d35887744dbaa1f55ff777810059`. It is filled, and the DONE marker and DELIVERED.sha256 are written.
- **Score:** blocking 0, joins_needed 0, vias 0, copper_mm 556.16, segments 116.
- **Wall time from FIRST_CMD:** about 21 min (16:49:21Z to 17:10Z); measure.py reports 0:20:58.
- **TOOL_GAPS:** 4 entries; the top three:
  1. **Edge-mount DSUB depth.** Nothing reads the footprint's own "PCB edge" marker. Without an overhang band, J2 is seated with its pads 5.30 mm inside the board and graded `pass`, and J1 gets no seat. Following SKILL §3.4's "an overhang of x reads x" literally puts J1's pads 2.51 mm in, also graded `pass`.
  2. **`analyze_power_paths.trace_power_paths`** keeps only one current sink per net, so it traced 22 mA through D2 where U1 and U2 together draw 44 mA, with no warning.
  3. **`check_assembly`'s echo line** reports "pad copper off-board 0.009mm" for J1 and J2, whose pads are actually 0.245 mm inside the outline. It is not gating, but the label is wrong.
