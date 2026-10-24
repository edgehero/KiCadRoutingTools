# REPORT — gpm board 13 pico_ice_rev3 (`/plan-pcb-placement full`)

## 1. Result

| DONE condition (full mode) | measured on delivered.kicad_pcb | pass? |
|---|---|---|
| board_score blocking 0 | **3** | no |
| unrouted 0 | 0 | yes |
| broken 0 | **3** | no |
| check_complete DONE | **INCOMPLETE**: blocking 3; orphan stubs on F.Cu/In1.Cu; weird copper 11 (some are false findings, TOOL_GAPS 4) | no |
| check_assembly | buildable (blocking 0) | yes |
| check_floorplan --intent | 0 errors, 0 warnings | yes |
| check_drc (--baseline, margin 0.1) | 0 violations; 113 vias in paste declared filled+capped | yes |
| mechanical facts | H1-H4 exact; J1 on the south edge; SW2 on the north edge | yes |

- **blocking_by:** unrouted 0, broken 3, drc 0, undersized 0, floorplan 0, assembly 0, drc_via_in_paste 0.
- **Quality:** vias 368 (270 at 0.45/0.20, 44 at 0.25/0.15, 43 at 0.30/0.15, 11 at 0.508/0.254); copper 2606.79 mm; segments 3294; joins_needed 3.
- **grade.py:** `done: false, blocking 3, broken 3, drc 0, check_complete INCOMPLETE, check_complete_authored UNSOUND, assembly buildable, floorplan_errors 0` (grade_delivered.json, grade_output.txt).
- **Ungraded, therefore unexamined:** diff_pairs, impedance, length, net_widths. The board declares none of them.
- **USB, measured only:** /USB_D+/- coupled 5.5 mm with 16.4 mm skew; /USB_P/N coupled 6.0 mm with 7.1 mm skew.

## 2. Stop rule and remaining blockers

**The stop rule fired twice.**

- **First firing (11:02Z).** After arm C reached blocking 11, three arms failed to lower it: the repaired seed s4 (18), the R4/R5 pairing v2 (14) and the finer grid D (11, a tie). Arm E had already been launched (10:54) and was in flight. It reached 7, then 3, which reset the count. I let in-flight work finish and say so here (TOOL_GAPS 5).
- **Second firing.** After E reached 3, these all failed to lower it: arm G (advanced-tier sizes, 13), scoped laps 1-5 (3 every time), v2E (12) and the failed-first split FF (6). I shipped E's best board.

**Remaining blockers.** Each is PASSABLE on the placement and CAGED only by routed copper, so they are router capacity/ordering failures, not geometry.

| net | stranded pad | reachability (placement) | blocker named by the router's Hint |
|---|---|---|---|
| +3V3 | C12.1 (73.43, 99.74) F.Cu | PASSABLE (no throat within view); CAGED with routing (margin −88.9 µm) | the protected /USB_P in the plane-tap repair ("blocked by /USB_P (protected, cannot rip)"); also /USB_D- |
| /LED_R | U6.41 (68.71, 93.83) F.Cu | PASSABLE, bottleneck 4.06 mm; CAGED with routing | 8-10 pre-existing nets incl. /ICE_38, /ICE_42, and the protected /USB_D- |
| /~{ICE_RST} | U3.39 (76.13, 106.21) F.Cu | PASSABLE, bottleneck 0.42 mm; CAGED with routing | /USB_N, /USB_P (protected), /LED_R, /ICE_DONE_ADC0, /ADC2\|PB, Net-(U3-GPIO25), /ADC3 |

A hand join is ruled out by measurement. `helpers/free_via_sites.py` finds no through-via site within 2.5 mm of C12.1 that clears every foreign track, via and pad on all four layers, even for a 0.25 mm via. The joins needed are 1.6 mm (+3V3), 4.8 mm (/LED_R) and 8.2 mm (/~{ICE_RST}), all through the most congested area.

Other defects on the shipped board:
- check_weird reports 9 dangling ends and 2 KiCad-dangling slivers. One "dangling" VBUS end is really a copper-overlap joint; deleting it split VBUS at PTC1, so no stub was removed (TOOL_GAPS 4).
- check_orphan_stubs reports 3: two 0.05 mm +3V3 slivers on F.Cu and a 2.1 mm /USB_N stub on In1.Cu.

## 3. Groups and judgement calls

- **Intent.** `intent.json` (read-only, sha 9c5e235b…) was copied to `intent_run.json` before the first intent-writing step. Rows added, with reasons:
  1. **`fixed_poses[]` J2 (63.5, 80.01, rot 0, derived_default).** SKILL §3.4: the pin rows of a plug-in module (Pico form factor).
     - The two 2x20 headers are the module's rows: parallel, along the long edges, centred, on one 0.1 in grid.
     - The outer columns are 17.78 mm (0.7 in) apart, the Pico row pitch. That is also the most that keeps every pad 0.635 mm from the edge; 20.32 mm would leave the outer pads 0.42 mm from the edge.
     - The declared holes H1-H4 sit on the outer-column lines.
     - Rot 0 puts J2 pins 35-40 (SWD, RUN, CLKOUT, USB_BOOT) at the USB end. JUDGMENT.
  2. **`fixed_poses[]` J3 (78.74, 80.01, rot 0, derived_default).** The east row, by the same rule; rot 0 puts VBUS, VDC, PWR_EN and +3V3_STDBY (pins 36-39) at the USB end. JUDGMENT.
  3. **`edge_connectors[J1].overhang_mm` = {min 0.99, max 1.3}.** From the HRO TYPE-C-31-M-12 drawing (2020.12.08, rev A, "RECOMMEND P.C.B LAYOUT"): the PCB edge is 5.79 mm from the rear shell-leg centre (local y −3.13; the 4.18 mm leg pitch identifies the legs). So the drawn body's front (F.Fab, local y 3.65) reaches 0.99 mm past the edge.
  - `waive_locked_overlaps.py` ran: 0 locked pairs, nothing written.
- **EMC rows:** none were given, and none were invented. `emc_roles` names only the crystal Y1.
- **Templates:** none. `check_groups` printed 0 template hints. U1/U4 are NCP115 LDOs, the RP2040's regulator is linear, and there is no RF chip.
- **Edge parts.** SW2 (PTS820, which is top-actuated per C&K) sits on the north edge as the brief declares; SW1 is free.
- **Fiducials.** FID1-6 have no declared pose and the corners hold the holes, so each fiducial is its own one-part group. JUDGMENT; in hindsight one (FID4, on B.Cu) landed in the U3/U6 west channel.

| group | anchor | members | why |
|---|---|---|---|
| usb_in | J1 | J1 R10 R24 R20 R22 | USB-C with CC pull-downs and the DNI CC options |
| power | U4 | U4 U1 D5 PTC1 C3 C7 C9 C13 C37 D6 R6 C36 SJ2 | entry Schottky and polyfuse, the 3.3 V and 1.2 V LDOs with their caps, U4's EN delay |
| core | U3 | U3 Y1 C1 C2 R1 C4 C5 C6 C10 C11 C12 C15-C19 C21 C22 U2 R2 R3 C8 R4 R5 R9 R12 R23 | RP2040, crystal, decaps, QSPI flash, and the series parts it drives |
| fpga | U6 | U6 C24 C25 C28 C27 C29 C30 C31 C33 C34 D1 R11 SJ4 SJ5 R7 R25 | iCE40, rail caps, VPP diode, PLL RC, CRESET pull-down, CDONE series R |
| fpga_mem | U8 | U8 U5 Q1 R13 R15 RN1 R8 C26 C42 D4 | config flash, PSRAM with its STDBY diode, CS FET, SPI pulls |
| leds | D2 | D2 R17 R18 R19 SJ1 C32 D3 R14 | RGB LED with resistors, jumper and cap; CDONE LED |
| btn_rst | SW1 | SW1 J4 R16 | RP2040 button, mode jumper, RUN pull-up |
| btn_ice | SW2 | SW2 R21 C14 | FPGA button, pull-up, debounce cap |
| fid1..fid6 | – | one fiducial each | no declared pose |

Judgement calls within the groups:
- +3V3 decaps split: 8×0.1 µF + 2×4.7 µF to the RP2040's 9 supply pins; 2×0.1 µF + 4.7 µF to the iCE40's two; one back-side 0.1 µF to each back-side flash; the back 4.7 µF to U4's output.
- Series terminations go at the driver: the RP2040 drives USB, ICE_CLK, ICE_SCK and CLKOUT; the iCE40 drives CDONE.

## 4. Placement

- **Pass 1.** 12 seeds (6 scattered, 6 clustered), skill defaults, `place_args []`. All legal, all with decap errors (3-19 each).
- **Hand repair (§3.6 case 2).** On s1, the first seed judge.json names, 5 `place_pose` moves:
  - C21 to U3 pin 10;
  - C8 (back face) under U3 pin 22;
  - C17 beside U3 pin 33;
  - C29 0.46 mm toward U6;
  - C2 to Y1 pad 1.
  Result: 0 errors, 0 warnings, buildable. s1 alone was judged: quick route blocking 43, joins 43, 186 vias.
- **Kept placement.** route_review advised one turn (D6 rot 90, saves 1.7 mm), applied to make `final.kicad_pcb` (sha eb9ba645…). CHOSEN.json: seed 1, scattered, pass 1, `intent_run.json`, `place_args []`, and these 6 `after` moves.
- **Placement arms tried and rejected:**
  - s4 hand-repaired (7 moves): blocking 18 on attempt 1's chain, against s1's 12.
  - R4/R5 USB series resistors paired: 14 with arm C's flags, 12 (with 9 DRC) with arm E's.
  - Rotations: U3 and U6 were already at their best quarter turns (`helpers/rot_probe.py`).
- **Decap templates and EMC templates:** none (see section 3).

## 5. Routing (`/plan-pcb-routing`, followed by hand)

- **Stackup:** a real FR4 stack (0.0994 mm cores beside the outer layers).
- **Tier:** STANDARD (4 layers, no BGA), so inner-only pours, GND In1 and +3V3 In2, matching the designer's zones. The designer's F.Cu/B.Cu GND zones were kept as drawn.
- **USB:** full-speed on the RP2040, so the pairs were routed coupled with no `--impedance`.
- **High-speed tier:** medium (QSPI/SPI ≤ ~60 MHz), so no GND-via or stitch tail.
- **Ripup:** default 3.
- **Shipped chain** (`final_route/pico_ice_rev3_plan.sh`, proved 17/17 by route_plan_check):
  1. `route_planes`
  2. `route_diff`, gap 0.127 = clearance
  3. `route.py '*'`: JLC multilayer standard floor (via 0.45/0.20, track 0.0889, clearance-ceiling 0.1), grid 0.025, layer costs 1 / 6 / 1.5 / 1, power widths from my analysis
  4. one iteration
  5. a scoped lap ripping /USB_D- (named exactly)

  The re-run reproduced exploration arm E's 6_lap1 exactly. The manifest's last line is a copy_board to 7_pruned, an abandoned cleanup whose files are now in `old/abandoned_helpers/`.
- **Arms, by blocking:**

  | arm | change | blocking |
  |---|---|---|
  | attempt 1 | grid 0.05, track/clearance 0.127, via 0.508 | 12 |
  | Step 2c env stack | global plan / attract / river | 14 |
  | B | soft-cost retry levers; stopped early | – |
  | C | track/clearance 0.1, In2 at 1.5 | 11 |
  | D | C + grid 0.025 | 11 |
  | F | standard floor at grid 0.05 | 13 |
  | E | standard floor + grid 0.025 | 7 → **3** |
  | G | advanced-tier sizes | 13 |
  | v2E | R4/R5 paired, E params | 12 |
  | FF | failed-first split | 6 |
  | laps 1-5 | on E | 3 |

- **Power widths.** By hand from the IPC table, because the analyzer overcounts (TOOL_GAPS 6): VDC, VBUS, Net-(D5-K) 0.7 mm; GND, +3V3, +1V2, /+1.2V_CORE 0.5 mm; others 0.3 mm. These are estimates, not datasheet maxima. Delivered short of the request: VBUS 73.7 mm and VDC 65.6 mm below 0.7 mm (down to 0.0889 mm, about 0.41 A by route.py's ampacity table).

## 6. Floors

- **route.py's Design rules line:** "568 feature(s) on 46 net(s) delivered below the requested size (smallest track width 0.0889 mm, smallest via diameter 0.25 mm); 730 fab-tier escalation(s) to advanced". Then 93/213 and 20/58 on the iteration and the lap.
- **Clearance** 0.1 mm, below the board's min_clearance of 0.127.
- **check_complete --authored-from input: UNSOUND.**
  - Track width 0.1524 → 0.0889 mm.
  - Via diameter 0.508 → 0.25 mm.
  - Annular ring 0.12446 → 0.05 mm.
  - Hole 0.254 → 0.15 mm.
  - Copper-to-hole 0.254 is broken by the reference too.
- **Via-in-pad.** 119 vias sit in pads or paste openings and are declared IPC-4761 Type VII (filled and capped). That is a fab cost.

## 7. Silkscreen

KiCad silk counts, before / after `beautify_labels`:
- silk_edge_clearance 2 / 2;
- silk_over_copper 14 / 1;
- total **16 / 3**.

`labelled.kicad_pcb` was kept. Its copper is identical (3294 segment blocks).

## 8. Fill

- `fill_for_delivery` ran with exit 0 (unconnected without refill: 84 → 3).
- Its KiCad 10 re-save stamped explicit no-protection overrides on all 368 vias. `helpers/restamp_after_fill.py` removed only the setup-equal tokens and ran the repo's `fab_notes.ship_via_protection_file`, which stamped Type VII on 119 vias. That leaves DRC 0, with fill and copper unchanged.
- The raw fill output is kept in `old/fill_raw/`.
- The delivered board is filled; no refill is needed before plotting.

## 9. Timeline (UTC) and where the time went

| time | event |
|---|---|
| 09:06 | FIRST_CMD |
| 09:13 | intent_run.json |
| 09:15 | groups.json |
| 09:15-09:17 | 12 seeds placed |
| 09:19-09:26 | s1 repaired and judged; final.kicad_pcb |
| 09:27-09:50 | attempt 1 (12) |
| 09:53 | Step 2c arm (14) |
| 10:07 | arm C (11) |
| 10:29 | s4 (18) |
| 10:35 | v2 (14) |
| 10:58 | arm D (11); stop rule fires |
| 11:08 | arm F (13) |
| 11:31 | arm E pass 1 (7) |
| 11:46 | arm E iter 1 (3) |
| 11:59 | arm G (13) |
| 12:10 | laps 1-4 (3) |
| 12:14 | lap 5 (3) |
| 12:39 | v2E (12) |
| 12:55 | FF (6) |
| 12:49-13:44 | shipping chain re-run |
| 13:45-14:00 | §3.9, verifier, ledger close |

Where the time went (measure.py): wall 4h53m, of which 13 016 s (74%) waiting on routing jobs. The grid 0.025 passes are about 40 min each. Model time 3552 s, other tools 1050 s; 329 turns, 369 tool calls, 1 agent spawn (the verifier).

## 10. Tool gaps

See TOOL_GAPS.md, 9 entries:

1. Protected USB pairs wall the last nets; the exact-name override is only half honoured.
2. `fill_for_delivery`'s KiCad 10 re-save creates 113 via-in-paste DRC violations.
3. `place_simple` leaves decap errors on every seed; judge.json ranks by error count.
4. check_weird reports a copper-overlap joint as "dangling"; route.py leaves real stubs and no tool removes them.
5. The stop rule is ambiguous with parallel arms.
6. `analyze_power_paths` overcounts through regulators.
7. No hand-join proposer.
8. No rotation ranker.
9. Datasheet PDFs: no poppler on this machine, and LCSC blocks downloads.

Tools that said "fine" about something that was not:
- `fill_for_delivery` (exit 0, nothing said about the vias);
- check_weird's VBUS "dangling end";
- the protected-net Hint, which kept saying "will NEVER rip" for nets the run had made eligible.

Helpers written, in `helpers/`: rot_probe.py, free_via_sites.py, restamp_after_fill.py and delete_weird_segments.py (the last produced a board that was rejected). The abandoned prune_dangling.py is in `old/abandoned_helpers/` and was never applied.

## 11. Verifier verdicts

One verifier, one call. `verdict_1.txt`: **VERDICT=FAIL**.
- sha matches;
- buildable; floorplan 0 errors; nothing off the outline; mechanical facts exact;
- board_score blocking 3 (broken: +3V3 at C12.1, /LED_R at U6.41, /~{ICE_RST} at U3.39);
- check_connected: 3 nets disconnected;
- check_drc 0, PASS;
- check_complete INCOMPLETE, with orphan stubs and 11 weird-copper findings;
- authored floors UNSOUND (reported, not gating).

Lens files:
- connectivity: FAIL, evidence 3;
- drc: PASS;
- spec: FAIL, evidence 3.

The named defects are the 3 nets (past the stop rule) and the dangling copper. The one attempt to delete the dangling copper made the board worse and was rejected.

**Skills followed by hand:** `/plan-pcb-placement`, `/plan-pcb-routing` and `/analyze-power-nets`, each from its SKILL.md, with `/recommend-plane-mappings` and `/find-high-speed-nets` applied inline. The datasheet folder was moved to `old/datasheets/`.

---

## The teammate's final summary (saved with the report by the orchestrator)

**NOT DONE.** The delivered board has 3 broken nets.

- **Delivered board:** `wk/gpm/13_pico_ice_rev3/delivered.kicad_pcb`, sha256 `c457c559aa16e0cabc32f1845976f51a7da3d3e06a436018c51022ae7034ca33`.
- **Score:** blocking 3 (unrouted 0, broken 3, DRC 0), joins_needed 3, vias 368, copper 2606.79 mm, segments 3294.
- **Stop rule:** §5 rule 3, plateau. Three consecutive different approaches failed to lower blocking 3, and a fourth already in flight also failed.
- **Wall time:** 4h53m from FIRST_CMD (09:06:40Z to about 14:00Z).
- **TOOL_GAPS:** 9 entries. The top three:
  1. The routed USB pairs wall in the last 3 nets. Naming them exactly in `--rip-existing-nets` lifts protection in route.py's main pass only; the plane finalize and its sub-runs still refuse to rip them.
  2. `fill_for_delivery` re-saves the KiCad-8 board through KiCad 10, which writes an explicit no-protection override on all 368 vias. That turns 113 accepted vias-in-paste into 113 DRC violations (blocking 3 → 116) and blocks the repo's own Type VII stamper. My helper restores the repo's own stamping policy.
  3. `place_simple` left decap-limit errors on all 12 seeds, so judge.json ranked by error count and dropped the anneal's cheapest seed.

The harness refused to let me write REPORT.md, so REPORT_DONE was not created. Its full content follows.
