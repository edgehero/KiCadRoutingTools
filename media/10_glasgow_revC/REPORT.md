# REPORT.md — gp14 board 10, glasgow_revC

`/plan-pcb-placement full wk/gp14/10_glasgow_revC/glasgow_revC.kicad_pcb wk/gp14/10_glasgow_revC/intent.json`, run with the defaults: up to 3 rounds, 6 scattered + 6 clustered seeds per round, the 6 cheapest judged.

## 1. Result: NOT DONE

| Full-mode DONE condition | Measured on final.kicad_pcb | Met |
|---|---|---|
| `board_score` blocking 0 | **7**: broken 6, drc 1; unrouted, assembly, floorplan and undersized all 0 | no |
| zero unrouted | 0 | yes |
| zero broken | **6** | no |
| `check_complete` DONE | **INCOMPLETE**: blocking 7, orphan stubs on 3 layers, check_weird not clean | no |
| `check_assembly --intent --baseline <input>` | buildable (blocking 0) | yes |
| `check_floorplan --intent` | 0 errors, 3 warnings | yes |
| mechanical facts | all 21 poses in mechanical.json match; MK1–MK4 are 4.0 mm in from each corner | yes |
| `check_drc --baseline <input> --clearance-margin 0.1` | **1** pad-via contact | no |
| `check_connected` | 6 nets with disconnected pads | no |

**Breakdown.** `blocking_by` = {assembly 0, broken 6, drc 1, drc_via_in_paste 0, floorplan 0, undersized 0, unrouted 0, impedance null, length null, net_widths null}. Quality: 869 vias, 6115.67 mm of copper, 5831 segments. Impedance, length and net widths were never graded (UNEXAMINED), because the board declares none of them.

### Remaining blockers, with their measurements

| Blocker | Where | Measurement |
|---|---|---|
| /D0 broken | U30.H7 (72.89, 90.80) | 2 components. `check_reachability` on the routed board: CAGED for any track width |
| /D6 broken | U30.L8 (73.69, 93.20) | CAGED |
| /IO_Banks/DA4 broken | U30.B8 (73.69, 86.00) | CAGED |
| /IO_Banks/DA6 broken | U30.B9 (74.49, 86.00) | 2 components |
| /OE broken | U30.L3 (69.69, 93.20) | 2 components |
| /IO_Banks/QB5 broken | RN2.2 (65.06, 94.80) | CAGED |
| DRC short | C76 pad 2 (/GNDPLL0, 73.10, 91.25) on a +3V3 dog-bone via at (73.29, 91.20), B.Cu | 0.25 mm overlap |

- **C76 short:** the decoupling-cap pass (`place_fanout_clearance`) left C76 unresolved. A search of B.Cu on the routed board found no 0603 site within 4.6 mm of U30 with 0.13 mm clearance to existing copper. C76 must stay within 4.79 mm of U30 (the intent's decap limit), so it cannot simply be moved after routing.
- **Open nets:** every one ends in U30's 0.8 mm ball field or at the series-resistor array RN2 next to it. Each route attempt left a different set of 6–23 nets open around the same BGA.

## 2. Groups and judgement calls

**Board.** 264 parts (92 on B.Cu), 252 nets, 4 layers: F.Cu, In1.Cu (GND pour), In2.Cu (+3V3 pour), B.Cu. 80 × 49 mm, KiCad default stackup. Main parts:
- U30: iCE40HX8K FPGA, BGA-121, 0.8 mm pitch
- U1: CY7C68013A USB controller, QFN-56
- 16 SN74LVC1T45 level shifters
- per I/O port: a PCA6408 expander, an INA233 current monitor, a DAC081 setting a TPS73101 LDO
- TLV755 (3V3) and TLV733 (1V2) regulators, and the TPD3S014 USB power switch

**Groups.** The final file is `groups.json` (= `groups_v3.json`); the round-1 version is kept as `groups_v1.json`.

| Group | Members | Why |
|---|---|---|
| usb_power | 27 + J1, C1 fixed | Power entry: USB-C and its CC pull-downs, shield RC, VBUS ferrite, TPD3S014, both LDOs with their caps, the supervisor, bulk cap, test points. C1 (declared pose) is the 3V3 output cap and anchors the LDOs. |
| core | 39 + J5, FID8 fixed | U30 and U1 share a 27-net bus, so they form one core. Also: crystal Y1 and its load caps, the FX2 reset RC and diode, FPGA_RESET and ALERT pulls, root-sheet decaps, PLL filters, VIO_AUX caps, and J5, whose 13 LVDS pairs go straight to U30. |
| leds | 20 | Each LED moves with its resistor. Rounds 2 and 3 add `edge: W`. |
| bank_a / bank_b | 42 / 41 + J2 / J3 | One I/O port each: shifters, 33R arrays, expander, 10k pull arrays, ESD, TVS, DNP sockets, decaps. |
| bank_a_pwr / bank_b_pwr | 26 / 27 | Each port's adjustable supply: LDO, current shunts, INA233, DAC and feedback divider, enable and alert, port LED. |
| sync_aux | 12 + J4 | SYNC port shifter, series resistors and ESD; AUX header J10 with its series resistors and ESD. |
| eeprom_i2c | 7 + U2, U3, C15, C17 fixed | The two EEPROMs, I2C pull-ups, test points. |
| reset_btn | C89 + SW1 | Reset button and its debounce cap. |

`check_groups` reported 0 errors and 3 warnings. All three are intended: C46, C53 and C83 are LDO-output caps that the source board itself keeps outside the decap radius.

**Judgement calls:**
- **SW1** had no declared pose. I declared it in `intent_v1.json` at (74.65, 116.65), rotated 180°, actuator tip flush with the south edge. That is the board's own notch in its 1.7 mm track keep-out band, and the README places SW1 at the south edge.
- **J5 / MK2:** their declared poses overlap courtyards by 4.07 mm², so I added an `overlap_waivers` pair.
- **FID1–6 and MK1–4** hit tool gap 1. In round 1 I picked the judge seeds by hand. For rounds 2 and 3 I KiCad-locked those parts in `fixed.kicad_pcb` (`intent_v2.json`, plus courtyard waivers for the J2/J3/J5 touches). On the kept board I unlocked them again because of tool gap 4; their poses did not change.
- **EMC rows:** none were given, so none were invented.
- **Route chain** (`final_route/plan.sh`; `route_plan_check` passed all 17 rules):
  - Kept the board's own GND and +3V3 pours on the inner layers (STANDARD tier).
  - U30: dog-bone fanout. U1: stub fanout. One cap pass with `--intent`.
  - `route_diff` at 0.1 / 0.1 for USB, the LVDS pairs and the INA233 sense pairs. No impedance pass, because the stackup is KiCad's default.
  - `route.py --nets '*'` at track 0.1, clearance ceiling 0.1, via 0.4/0.2, layer costs 1/3/3/1, per-rail power widths, `--max-ripup 5`, plus the first-choice retry levers (`--ripped-route-avoidance-cost 3 --track-proximity-cost 2`). Those levers took the same chain from blocking 15 to 7.

## 3. Rounds

Every judging route used the same chain at `--quick 2`.

| Round | Input change | Judged seeds, quick blocking | Best |
|---|---|---|---|
| r1 | groups v1, intent_v1 | s5 36, s11 42, s3 59, s0 67, s8 78, s2 81 | r1/s5 |
| (r2 attempt) | leds `apart: core` | killed: placements identical to round 1 (tool gap 2) | — |
| r2 | leds `edge: W`. Review of r1/s5: its only congested cell was east of U30 at LED resistor R23. | s0 39, s7 46, s4 48, s3 52, s5 56, s8 141 | none better |
| (r3 attempt) | U30→J5 proximity claim without pads | killed: unsatisfiable (tool gap 3) | — |
| r3 | claim U30→J5 on the 26 LVDS pads, max 20 mm. Review of r2/s0: U30 sat mid-board, LVDS mean 26 mm. | s3 21 (claim broken, 22 floorplan errors, not keepable), **s4 25**, s7 26 (claim broken), s11 41, s0 49, s9 85 | **r3/s4** |

**Kept placement:** r3/s4 (`CHOSEN.json`). After it, with `place_pose`:
- six decap nudges of 0.03–0.3 mm (C18, C6, C46, C53, C59, C85) that clear every floorplan error
- R20 and R39 turned 180°
- FID/MK unlocked

### Full routes of the kept placement

`final_route/` holds the shipped chain; `final_route_old1/` holds the exploratory branches.

| Attempt | Blocking (broken / DRC) |
|---|---|
| plan as written, plus 2 all-nets passes | 15 (14 / 1); both passes were reverted |
| **retry levers on the route step** | **7 (6 / 1)**: shipped, re-run cleanly with an identical result |
| all-nets pass on that board | reverted |
| chain B: C76 moved off the via grid first | 20 (17 / 3) |
| chain C: LVDS pairs left to route.py | 12 (12 / 0) |
| all-nets pass on chain C | 42 (23 / 17); the gate accepted it (tool gap 6) |
| chain C at default soft costs | 16 (16 / 0) |
| failed-first split | 35 (14 / 21) |

## 4. Floors (below the board's authored rules)

- `check_complete --authored-from <input>` says **UNSOUND**: track width 0.15 → 0.0889 mm, via diameter 0.4 → 0.25 mm, hole 0.2 → 0.15 mm.
- Net-class clearance 0.1499 mm was routed at the 0.10 ceiling (the fab floor is 0.09).
- route.py delivered 285 features on 70 nets below the requested size, and escalated to the fab's advanced tier 413 times.
- The dog-bone vias under U30 are 0.30 mm.
- 342 vias sit in solder-paste openings. This file format cannot declare the filled-and-capped via spec, so check_drc accepts them; it belongs on the fab drawing.

## 5. Timeline

| UTC | Step |
|---|---|
| 19:00–19:08 | read the README and skills, analysed the board, wrote the intent and groups |
| 19:08–19:31 | round 1 placement and judging |
| 19:33–19:41 | round-2 attempt that changed nothing (killed) |
| 19:41–20:00 | round 2 |
| 20:00–20:04 | unsatisfiable claim (killed) |
| 20:04–20:26 | round 3 |
| 20:26–20:29 | kept placement and fixes |
| 20:29–20:41 | full route |
| 20:41–21:28 | retries |
| 21:28–21:36 | stop rule; clean re-run of the shipped chain |
| 21:36–21:43 | verifier, grade, ledger close |

**Where the time went:** placement about 45 min, judging about 25 min, full routing and retries about 65 min, tool diagnosis about 20 min. `measure.py`: wall clock 2:42:37 (model 2269 s, waiting on jobs 6261 s, other tools 1227 s). Output in `measure_output.txt` and `measure.json`.

## 6. Tool gaps

There are 8 entries in `TOOL_GAPS.md`. Ranked by cost:
1. **#7** route.py strips BGA escape stubs it cannot restore, then its hint blames the fanout.
2. **#1** place_simple measures declared round pads by their bounding boxes, so every seed is illegal and the judge list is empty.
3. **#6** route.py's improvement gate accepted an all-nets pass that added 17 DRC violations.
4. **#2** an `apart` hint between groups that already touch is a constant, so the round repeated round 1 pose for pose.
5. **#4** KiCad-locking the markers, as the skill says to, flips check_assembly to NOT BUILDABLE.
6. **#3** the skill's proximity-claim example, used on a many-pad part, claims every shared pad including GND and cannot be satisfied.
7. **#5** converge.py refuses the first board_score row after the quick_score rows.
8. **#8** (skill) quick_score counts poured-net pads that `--quick 2` never connects, so the round-stop condition cannot fire. All 18 judged routes had GND/+3V3 pads open.

Tools that said "fine" about something that was not:
- the improvement gate's "ACCEPTED" (#6)
- route.py's "fanout-dropped ball" hint (#7)
- place_simple's "illegal" verdicts (#1)

## 7. Verifier

`verdict_1.txt`: **VERDICT=FAIL**.

**Passed:**
- sha256 matches
- check_assembly buildable
- check_floorplan 0 errors
- render_placement off-outline checklist clean
- mechanical 21 of 21 poses

**Failed:**
- board_score blocking 7 (6 broken, 1 DRC)
- check_connected: 6 nets
- check_drc: 1 short, +3V3 via inside C76 pad 2
- check_complete INCOMPLETE: orphan stubs, and 539 findings from the stray-copper checker (`check_weird`)
- `--authored-from`: UNSOUND, with the floors listed in §4

**Informational:**
- USB D+/D− skew is 50.7 mm (P 91.5 mm, N 40.8 mm).
- The worst USB return-via distance is 6.24 mm.

**Lens files**, all FAIL: `verdict_1_connectivity.txt` (6 broken nets), `verdict_1_drc.txt` (1 short), `verdict_1_spec.txt` (check_complete INCOMPLETE; the mechanical facts themselves pass).

**Independent grade:** `grade.py` reports done false, blocking 7, vias 869, copper 6115.67 mm, check_complete INCOMPLETE, authored-from UNSOUND, assembly buildable, floorplan errors 0 (`grade_output.txt`).

The ledger has 49 rows, closed with `--final --stop-condition 3`. The input files' sha256 were re-checked and are unchanged. No datasheets were downloaded.
