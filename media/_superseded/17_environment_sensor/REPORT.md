# REPORT -- gpm board 17 environment_sensor, `/plan-pcb-placement full`

**DONE.** The delivered board is `wk/gpm/17_environment_sensor/delivered.kicad_pcb`, sha256 `4dc62b18dc40ab44616e3c7d94581355ed2d0b52b19b889d4c92efd34b384381`. It is labelled and filled with KiCad's zone filler, and it passed the independent verifier on its first call. Stop condition 1 (done). Wall time from FIRST_CMD (14:01:52Z) is about 1 h 25 min.

**Skills followed by hand** (none could be invoked), each from its SKILL.md:
- `/plan-pcb-placement`: the whole workflow.
- `/plan-pcb-routing`: §3.8, Steps 0-10, including the plan file and `route_plan_check`.
- `/analyze-power-nets`: Step 4 of the routing skill.
- I also used the methods the routing skill describes for `/find-high-speed-nets`, `/recommend-plane-mappings` and `/review-routed-board`.

## 1. Result

| DONE condition (full mode) | measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking (with `--impedance-nets '/USB_D_*'`) | **0** |
| unrouted / broken | **0 / 0** |
| `check_complete` | **DONE** (UNEXAMINED, not passed: diff_pairs, length, net_widths) |
| `check_assembly --baseline` | buildable (blocking 0) |
| `check_floorplan --intent intent_run.json` | 0 errors, 5 warnings |
| `check_connected` | ALL NETS FULLY CONNECTED (KiCad refill cross-check agrees) |
| `check_drc --baseline --clearance-margin 0.1` | 0 violations (3 same-net self-crossing warnings) |
| KiCad DRC (`kicad-cli pcb drc --refill-zones`) | 0 copper violations, 0 unconnected. Also: 1 `footprint_type_mismatch` on J1 (inherited from the input board), 24 silk warnings, 107 `lib_footprint_issues` (no library configured) |
| `grade.py --mode full --spec impedance-nets='/USB_D_*'` | `"done": true, "blocking": 0` |

- **`blocking_by`:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, impedance 0, undersized 0, unrouted 0. diff_pairs, length and net_widths are null (ungraded).
- **Quality:** 101 vias, 933.23 mm copper, 881 segments. The first DONE board had 156 vias and 879.75 mm. The 933.23 mm includes 11.2 mm of MP-tab joins.
- **Spec flags:** `--impedance-nets '/USB_D_*'`. The routing declared 90 Ω differential on the USB pair, following the board's own `90Ohm-diff_USB` net class, which has no member nets.
  - The board declares nothing else: no net is in a non-Default class, there is no `.kicad_dru`, no length group and no per-net width spec.
  - `check_impedance` finds 0 crossings and 0 mm over a void: the pair runs on F.Cu over the intact In1 GND plane.
  - Z0 measures 7-8 % low because of the coplanar ground. That is immaterial for USB Full-Speed (the FT232R).

## 2. Groups and judgement calls

Nine groups, written to `groups.json`; `check_groups` reports 0 errors. TP1-TP6 are placed by `fixed_poses[]` from mechanical.json, and MP1-MP3 by rows I added.

- **usb_in:** J1, D1-D5, R1, R3, R4, C2, C4, FB1, FB2. The USB-C connector with its ESD, CC pull-downs, shield RC and VBUS ferrite.
- **ftdi:** U1, C5-C8, R2.
- **bridge:** the 0R jumper bank R5-R11 and R13-R16, between the FT232R and the STM32.
- **power:** U2 (AP7370 LDO), C1, C3, C9, C10, TP9, TP10.
- **mcu:** U3 with its decaps, the VDDA filter, the VREF caps, crystals Y1 and Y2 with their caps and resistors, the straps, the I2C series resistors, and BAT1 on the back.
- **fram:** U4, C25, R26, TP7, R31-R34.
- **sensors:** U5, U6, C26-C28, R35, R36.
- **i2c_conn:** J2, J3, D6-D9, R37, R38, TP11, TP12, C13.
- **ui:** LD1/R12 and LD2/R17, edge S.

Judgement calls (the user was not available):
- **Thermal tongue.** The NE corner of the outline is a 10 x 8 mm tongue, cut off by a notch, an L-slot and a second notch so it joins the board only through two 2 mm bridges. I read it as the sensors' thermal island and added the `blocks[]` row `sensor_tongue`, zone [200, 113.5, 210, 121.65]. All 7 sensor parts are inside it on the delivered board.
- **MP1-MP3.** These M2.5 mounting pads are not declared anywhere. I put them in the NW, SW and SE corners, inset 3.2 mm (`fixed_poses`, `basis: derived_default`). The NE corner is the tongue.
- **J2/J3.** Both are side-entry JST-SH, so their cables must leave over an edge. I put both on the south edge. The `mating_face` values (J2 `+y`, J3 `-y`) come from the JST eSH side-entry drawing.
- **J1 overhang.** The GCT USB4105 drawing puts the PCB edge and the shell front both 2.60 mm from the front pegs, so the connector sits flush and needs no extra row. The verifier confirms overhang 0 and the opening facing west.
- **Templates.** None: there is no switching stage or RF front end, and `check_groups` printed 0 hints. No EMC limits were given, and I invented none.
- **Hand moves after place_simple** (CHOSEN.json `after`):
  - D1 to (162.0, 132.5, 0°) and D2 to (161.5, 133.6, 0°).
  - Why: these VBUS ESD diodes sat in the USB D+/D- corridor, and D1's VBUS via voided the ground reference under D+.
  - Effect: impedance blocking went from 1 to 0, and vias from 134 to 129.
- **Rows added to `intent_run.json`:**
  - `edge_connectors[]`: J2 and J3.
  - `fixed_poses[]`: MP1-MP3.
  - `blocks[]`: sensor_tongue.

## 3. Placement and route

- **Placement:** one pass of 12 seeds, `place_args` `[]`. Seeds 5 and 7 each had one decap-distance floorplan error, so I judged only seeds 4, 6, 2 and 8. Seed 4 (scattered) won: blocking 0, 106 vias, 748 mm on the fast route. Seed 6 had blocking 1, seed 2 blocking 2, seed 8 blocking 5.
- **Routing chain** (`final_route/final_plan.sh`; `route_plan_check` passes 17/17):
  1. `kicad-cli pcb upgrade` on a copy of the input board.
  2. `route_diff` on the USB pair, 90 Ω, F.Cu only.
  3. `route.py` on the pair's leftover legs, F.Cu only.
  4. `route.py '*'` with the Step 2c environment settings and `--via-cost 300`.
  5. Two more `route.py '*'` iterations with the same flags.
  6. Two `check_join` hand joins.

  Every routing step ran at edge clearance 0.22 mm, with clearance ceiling 0.15, track 0.15 and via 0.5/0.2. The board's own pours were kept: GND on F.Cu, In1 and B.Cu; +3V3 on In2. There is no fanout step and no extra ground-via step, because the board is low-speed.
- **Optimisation after DONE:**

  | change | vias | copper | note |
  |---|---|---|---|
  | first chain | 156 | 879.8 mm | |
  | USB pair on F.Cu only | 134 | 818.7 mm | |
  | D1/D2 moved | 129 | 828.0 mm | impedance clean |
  | via cost 250 | 106 | 907.3 mm | |
  | env settings + via cost 300 | 101 | 917.0 mm | |

  I stopped when a sweep around the best via cost found nothing better. Rejected arms: no via-in-pad, diff gap 0.2, the pair on F.Cu+B.Cu, a forced VBUS reroute, D5 moved, other layer costs, ripup 5, and `--escalation board`/`off` (neither was DONE).
- **Hand copper:** two 0.25 mm tracks, each checked CLEAN with `check_join`:
  - J2's MP tabs, on F.Cu: (197.65, 138.855) to (203.25, 138.855).
  - J3's MP tabs, on B.Cu: (190.34, 138.855) to (195.94, 138.855).
- **Power widths:** the tool recommended GND 2.0 mm and +3V3 1.0 mm, but it counts current once per power pin (TOOL_GAPS 5).
  - I applied its own width table once per part to about 190 mA: GND, +3V3, +5V and VBUS at 0.7 mm; VDDA, VBAT and GNDREF at 0.3 mm.
  - The currents are estimates: FT232R 15 mA, STM32G474 60 mA, Qwiic 50 mA per port, sensors 1 mA each.
  - These are routing requests, not a board spec.

## 4. Stop rule and remaining items

Stop condition **1 (done)**; nothing is blocking. Non-gating warnings that remain:
- The Y1 32 kHz crystal leg is 8.49 mm against an 8.10 mm warning limit.
- Net-(U3-VBAT) has no decoupling cap.
- `pins_to_edge` warnings on BAT1 and U2.
- The verifier's advisory: the USB pair has 3.27 mm skew and 10 mm uncoupled. It is Full-Speed and no skew rule is declared.
- `check_cycles` counts 11 pad-local loops on the USB nets.
- 68 vias sit in pads or paste openings, declared IPC-4761 Type VII (filled and capped). The fab drawing must carry that.

## 5. Floors

`check_complete --authored-from` says UNSOUND (not gating). The router's default escalation took some copper below the board's authored floors:
- track 0.15 → 0.0889 mm (12 segments of /USB_D_P at its pads);
- via 0.5/0.2 → 0.28/0.15 mm (5 vias on the advanced fab tier);
- Default clearance 0.15 → 0.1187 mm.

The edge clearance became 0.22 mm because I set it (the board declared 0.0). With `--escalation board` or `off` the board was not DONE (3-4 broken nets), so the escalation stays. The fab needs to confirm it can make 0.0889 mm track, 0.28 mm vias and 0.1187 mm clearance.

## 6. Silkscreen

KiCad silk warnings: 109 before the label tidy, 24 after. I kept `labelled.kicad_pcb`; its copper is identical to the routed board. `beautify_labels` exited 4 because it found no legal spot for U6's label.

## 7. Fill

`fill_for_delivery` ran: KiCad's unconnected count without a refill went from 45 to 0, and all 4 net classes were kept. Nothing was routed after the fill.

## 8. Timeline (UTC)

| time | step |
|---|---|
| 14:01-14:12 | reading, datasheets (helper written), intent rows, groups |
| 14:13-14:14 | place_simple |
| 14:18-14:20 | judge_seeds |
| 14:21-14:23 | first full chain: DONE at about 21 min |
| 14:23-14:57 | USB impedance and via optimisation probes; final chains 2-3 |
| 14:57-15:05 | KiCad-only findings (edge arcs, MP tabs); chain 4 |
| 15:05-15:15 | fill/via-in-pad format issue; upgrade-first chain 5; delivery |
| 15:15-15:19 | escalation probes |
| 15:19-15:25 | verifier |
| 15:25-15:30 | grading and report |

`measure.py --self --evidence` reports 1:23:58 wall, 37 min of model time, 45 min of tool time and 1.8 min waiting on jobs. Placement and judging took about 3 min of compute. Most of the time went to probe routes after DONE (about 50 at 1-2 min each, 3 at a time) and to the three KiCad-only findings.

## 9. Tool gaps

Details and repro commands are in TOOL_GAPS.md.
1. `fill_for_delivery` re-saves the board as KiCad 10, which turns 68 accepted via-in-pad vias into blocking errors. The skill has no step for it.
2. Tracks land 2 µm inside the edge floor at arcs; `check_drc` and `kicad_drc_compare` hide it ("#408"), while KiCad reports 5 errors.
3. KiCad requires the MP-tab joins; the repo's connectivity checkers miss them.
4. route.py is not run-to-run deterministic with the Step 2c settings: identical input gave 1183 or 1188 copper items.
5. `analyze_power_paths` multiplies current by the number of power pins.
6. There is no poppler for the PDF steps, so I wrote `helpers/pdfpage.swift`.
7. `route_planes --skip-existing-zones` tightens the clearance for a via lattice that does not exist.
8. Bare `kicad-cli` is not on PATH.
9. `place_pose` prints `legal: false` with zero conflicts on an outline with arcs.
10. `check_cycles` counts pad-local back-tracks as loops.

Tools that said "fine" when it was not: gap 1 (`fill_for_delivery` exited 0, and the routed board graded blocking 0), gap 2 (`check_drc` clean, `kicad_drc_compare` "CONSISTENT"), and gap 3 (`check_connected`, `board_score` and `check_complete` all reported full connection).

## 10. Verifier

One subagent, one call: `verdict_1.txt` is `VERDICT=PASS`, and the connectivity, drc and spec lens files are all PASS. Its note: it treated `diff_pairs` as unexamined rather than a FAIL, because the pair's only declared requirement is the 90 Ω impedance, which grades clean, and no skew rule exists.

## 11. Files

All in `wk/gpm/17_environment_sensor/`:
- **Boards:** `delivered.kicad_pcb` (with its siblings), `DELIVERED.sha256`, `DONE`, `routed.kicad_pcb`, `labelled.kicad_pcb`, `final.kicad_pcb`.
- **Inputs to the placement:** `groups.json`, `intent_run.json`, `CHOSEN.json`, `placed_from/`.
- **Routing:** `final_route/`, with the earlier chains in `final_route_old1` to `final_route_old4`.
- **Records and grades:**
  - `ledger.jsonl`: 45 rows, closed `--final --stop-condition 1`.
  - `grade_output.txt` and `grade_delivered.json`.
  - `measure_output.txt`.
  - `verdict_1*.txt`.
  - `silk_before.json` and `silk_after.json`.
- **Gap material:** `TOOL_GAPS.md`, `repro/`, `helpers/pdfpage.swift`.
- **To delete:** the datasheets, moved to `old/datasheets/`.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE**: board 17 is placed, routed, and passed the verifier on its first call.

- **Delivered board:** `wk/gpm/17_environment_sensor/delivered.kicad_pcb`, sha256 `4dc62b18dc40ab44616e3c7d94581355ed2d0b52b19b889d4c92efd34b384381`. `DONE` and `DELIVERED.sha256` are written.
- **Score:** blocking 0, joins_needed 0, 101 vias, 933.23 mm copper, 881 segments. `grade.py` says done and `check_complete` says DONE, with `--impedance-nets '/USB_D_*'`. KiCad's own DRC finds 0 copper errors and 0 unconnected items.
- **Stop rule:** condition 1, done. After DONE I kept cutting vias; I stopped when a further via-cost sweep improved nothing.
- **Wall time:** about 1 h 25 min from FIRST_CMD (14:01:52Z); first DONE came at about 21 min.
- **Input hashes:** the five given files are unchanged.
- **TOOL_GAPS.md:** 10 entries. The top three:
  1. `fill_for_delivery` re-saves the board in KiCad 10 format, which turns 68 accepted via-in-pad vias into 68 blocking `drc_via_in_paste` errors (grade.py then says `done: false`). The fix was to upgrade the input with `kicad-cli pcb upgrade` before routing, so route.py marks those vias filled and capped itself. The skill has no step for this.
  2. Five tracks sat about 2 µm inside the 0.2 mm edge clearance at the slot's arcs. `check_drc` said clean and `kicad_drc_compare` filed KiCad's 5 errors as "#408 intentional edge" and reported CONSISTENT. Fixed by routing every step at 0.22 mm.
  3. KiCad requires the two `MP` tabs of J2 and J3 to be joined; `check_connected`, `board_score` and `check_complete` all said fully connected. Fixed with two hand-checked joins (`check_join`, CLEAN).

The harness refused the REPORT.md write ("Subagents should return findings as text"), so REPORT_DONE was not created. The full report follows.
