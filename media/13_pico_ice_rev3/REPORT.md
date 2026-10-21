# REPORT: gp14 board 13, pico_ice_rev3 (`/plan-pcb-placement full`)

**Result: NOT DONE.** The stop rule that fired is *three consecutive different approaches that each failed to lower `unrouted + broken`* (SKILL §5.3). The ledger records it as plateau, stop condition 3.

Wall time from FIRST_CMD to the frozen board was about 1 h 14 min (20:32:42Z to 21:46:33Z). `measure.py` reports 1:17:58 for the session up to the end of the paperwork.

- **Final board:** `wk/gp14/13_pico_ice_rev3/final.kicad_pcb` with its `final.kicad_pro`, sha256 `5295dcfdff51933acb272bb5014aa08f442736e58d45877d2dc70801117ccb12`.
- **Placement inputs:** `groups.json` and `intent_rows.json` (see "Intent" in §2).
- **Routing chain:** `final_route/redo_commands.sh`.

## 1. Result (measured on the final board)

| DONE condition (full mode) | measured | pass? |
|---|---|---|
| `board_score` blocking 0 | **8** | no |
| unrouted 0 | 0 | yes |
| broken 0 | **8** (7 nets, 8 joins) | no |
| `check_complete` DONE | **INCOMPLETE**, exit 4 (see note) | no |
| check_assembly | buildable (blocking 0) | yes |
| check_floorplan --intent errors | 0 (it exits 4 only because the given intent leaves 3 rules dark and owed) | yes |
| check_drc (baseline, margin 0.1) | 0 violations | yes |
| mechanical facts (H1-H4, J1 south, SW2 north, J2/J3 rows) | all exact | yes |

Note on `check_complete`: it reports blocking 8, orphan stubs (9 on F.Cu, 4 on B.Cu) and 136 weird-copper findings, 113 of them stacked GND segments.

- **`blocking_by`:** unrouted 0, **broken 8**, drc 0, undersized 0, floorplan 0, assembly 0, drc_via_in_paste 0.
- **Ungraded (UNEXAMINED):** impedance, length, net_widths. The board declares none of them.
- **Quality:** **vias 303, copper 2670.69 mm, segments 2874.**

Independent grade (`grade.py --mode full`, written to `grade/grade_final.json`): done false, blocking 8, broken 8, drc 0, `check_complete` INCOMPLETE, `check_complete --authored-from` UNSOUND, assembly buildable, floorplan_errors 0.

### Remaining blockers, by name

On the unrouted placement (`final_route/placed.kicad_pcb`), `check_reachability --track 0.0889 --clearance 0.09` finds every stranded pad **PASSABLE**, with margins of +349 to +3113 µm. On the routed board they are **CAGED** by other nets' copper. So this is router capacity: congestion in the 9 mm channel between the header rows, not a geometric dead end.

| net | stranded pad(s) | final board | placed board |
|---|---|---|---|
| /+1.2V_CORE (2 joins) | U6.30 (68.68, 89.93) F; SJ4 (72.07, 92.30) B | CAGED, no positive-slack path | PASSABLE +451 µm |
| /ICE_19 | U6.19 (71.87, 86.74) F | CAGED, bottleneck 0.024 mm | PASSABLE +475 µm |
| /ICE_26 | U3.6 (69.20, 104.57) F | CAGED, no path | PASSABLE +349 µm |
| /ICE_45 | U6.45 (73.37, 93.62) F | CAGED, bottleneck 0.014 mm | PASSABLE +3113 µm |
| /ICE_46 | U6.46 (73.87, 93.62) F | CAGED, bottleneck 0.020 mm | PASSABLE +980 µm |
| /QSPI_SD2 | U2 (68.79, 97.06) B | not measured (verifier: a via at (71.15, 102.45) reaches F.Cu only) | not measured |
| Net-(D2-BK) | D2.4 (69.40, 97.23) F | CAGED, no path | PASSABLE +1251 µm |

The verifier also found these, which I did not work on because the stop rule had already fired:
- orphan +3V3 stubs (9 on F.Cu, 4 on B.Cu);
- a dangling /ICE_FLASH_IO3 via at (80.30, 83.90);
- two tracks KiCad will report as dangling;
- 113 stacked duplicate GND segments;
- on the USB pairs, 28.2 of 70.5 mm runs over reference-plane voids, and /USB_P vs /USB_N skew is 7.4 mm at the pins.

## 2. Board, decisions and judgement calls

**The board:**
- **Parts:**
  - RP2040 (U3, QFN-56, 0.4 mm pitch) and iCE40UP5K (U6, QFN-48, 0.5 mm pitch)
  - two W25Q32 flashes: U2 is the RP2040 boot flash, U8 the FPGA flash
  - an APS6404 PSRAM (U5) and two NCP115 LDOs (U4 3V3, U1 1V2)
  - a USB-C connector J1 and two 2x20 headers J2/J3
- **Size and layers:** 97 parts and 98 nets on 4 layers, 22.86 x 60.96 mm (Raspberry Pi Pico form factor), with 30 parts on the back.
- **Existing zones:** GND on F.Cu, In1.Cu and B.Cu; +3V3 on In2.Cu.

**Intent.** I used `intent.json` unedited and added two things in a new file, `intent_rows.json`. SKILL §3.4 asks for them, and the given intent may not be edited.
- **J2 and J3 as plug-in module pin rows** in `fixed_poses[]` (`basis: derived_default`):
  - The rows run parallel along the long edges, on the 0.1 in grid, centred on the board.
  - The outer rows are 17.78 mm (7 x 2.54) apart. That is the Pico socket spacing, and also the widest spacing that keeps every pad 0.635 mm inside the edge.
  - Poses: J2 (63.5, 80.01, 0°) and J3 (78.74, 80.01, 0°).
  - Rotation 0 puts J3 pin 39 (VBUS) at the south end beside the USB-C, as on a Pico.
  - Which end is pin 1, and which column is outer, are my judgement: no brief field states the pinout.
- **SW2 `mating_face: -y`:**
  - check_floorplan could not tell which way SW2 faces, because its courtyard is symmetric.
  - I could not fetch the PTS820 datasheet.
  - From the footprint, the terminals are on the short ends and the side plunger on a long side. The footprint is symmetric under 180°, so -y and +y give the same seat.
- **EMC rows:** none were given (the user was unavailable), and I invented none. `emc_roles` reported one crystal (Y1 to U3 XIN, 4.6 mm apart in the pile). I added no proximity limit beyond the crystal claims the emitter already wrote.

**Fixed parts.**
- H1-H4 are seated by `fixed_poses` from `mechanical.json`.
- The fiducials are declared nowhere, so I placed and locked them near the board ends, about 1.2-1.3 mm from the edge (the corners are taken by the holes):
  - front: FID1 (67.3, 75.0), FID3 (77.5, 75.0), FID5 (65.95, 133.35)
  - back: FID2 (77.5, 75.0), FID4 (67.3, 75.0), FID6 (78.85, 133.35)
- SW1 is not claimed by the brief, so I left it free.

**Groups** (`groups.json`, 8 groups; `check_groups` reports 0 errors):
- **usb_in:** J1, its CC resistors, and the D5/PTC1 power entry.
- **power:** U4 and U1 with their VBUS and output caps, U4's EN network, and SJ2.
- **rp2040:** U3; the crystal; 8 x 0.1 µF plus one 4.7 µF +3V3 decaps; the +1V1 caps; the USB 27 Ω pair R4/R5 at the chip (per the placement lessons); and the 27 Ω source terminations it drives (R9, R12, R23).
- **qspi:** U2, R2, R3, C8.
- **fpga:** U6 with its rail caps, its VIO/PLL/VPP/CDONE/CRESET parts, and SJ4/SJ5.
- **fpga_mem:** U8 and U5 on the shared SPI bus, RN1, Q1/R13/R15, R8, and D4 with the standby cap.
- **ui:** SW2 with R21/C14, and the RGB LED D2 with R17-R19, SJ1 and C32.
- **reset:** SW1, the PB_SEL jumper J4, and the RUN pull-up R16.

Judgement calls within the groups:
- I split the +3V3 decaps by supply-pin count: U3 has 9 pins, U6 has 2, U2 and U8 have 1 each. The back-side caps C8 and C26 go with the back-side flashes, and C13 sits at U4.
- I moved SJ4 from power to fpga after `check_groups` warned that it has 2 signal links to the FPGA side.
- R25 (CDONE to ADC0) goes with the FPGA, because CDONE is the driver.

## 3. Rounds and review: what each route showed, what I changed, and the effect

**Judging chain.** The same chain judged every candidate, recorded per seed in `r<N>/s<S>_route/`:
1. `route_planes` pours GND on In1 and +3V3 on In2.
2. `qfn_fanout` on U3 and U6 (`* !GND !+3V3`).
3. `place_fanout_clearance --clearance 0.1 --intent`.
4. `route_diff '/USB_*' --track-width 0.1 --diff-pair-gap 0.127 --impedance 90`.
5. `route.py '*' --quick 2` with power widths, layer costs 1/6/2.5/1 (the standard tier: inner-only pours), `--track-width 0.0889 --clearance-ceiling 0.1`.

I calibrated the chain once on r1/s6 before comparing anything. At the board's own 0.1524 mm track and 0.127 mm clearance, the six r1 seeds scored 26-41. Thinner 0.0889 mm tracks took r1/s6 from 26 to 12, and I re-judged all of r1 with them so every round compares on one chain.

| round | input change | judged (quick blocking) | kept / outcome |
|---|---|---|---|
| r1 | groups v1, `intent_rows.json` | s6 12, s9 19, s0 22, s11 24, s10 25, s4 28 | Kept r1/s6. The review showed +1.2V_CORE and VCC_PLL open (R11/SJ4 had been pulled to U1 at the USB end) and the SPI bus open. **Every seed broke 4-20 decap limits.** |
| r2 | U1/C37/C9 moved to the fpga group (a point-of-load LDO); `--decap-limit-weight 100` | s9 15 … s6 32 | Nothing better. U1 ended up at the south end anyway. Decap errors 2-12. |
| r3 | locked r1/s6's IC skeleton (U2 U3 U5 U6 U8 J1 SW2) and re-placed the rest at weight 100 | **s10 9**, s0 16, s6 17 … s7 33 | r3/s10 was the best of the three rounds (5 decap errors). |

**First full route.** The three rounds ended with no clean fast route.
1. I kept r3/s10 and fixed its 5 decap errors by hand (`kept/fix2`): C26 onto the back under U3 pin 10, C12 at pin 33, C19 nudged, C34 at U6 pin 29, C29 beside U6. I also turned R6 by 180°, as `route_review` suggested.
2. The full route (`final_route_old1/`) left **16 broken and 1 DRC violation** (blocking 17).
3. Two more all-nets passes (the routing skill's Step 2d iterations) changed nothing; the tally was byte-identical.
4. I classified the failure as PLACEMENT (recorded as a `classification` row in the ledger). The failures sat at U6's escape faces, and at U2 and U5, which the anneal had put on the back directly under U6.

**Re-placements after that classification** (SKILL §3.7 and §4):

| round | change | quick | full route (`--clearance-ceiling 0.09`) |
|---|---|---|---|
| r4 | rp2040 group `edge: S` | s10 14 … s11 29 | not routed (no seed beat r3/s10) |
| r5 | r1/s6's U3/U6/J1/SW2, plus U8 (72.39, 78) and U5 (72.39, 83.5) north of U6 and U2 (72.39, 97.7) between U6 and U3, all locked on the back so U6's back side stays free | s6 10, s7 13 … s10 26 | **r5/s6 with 4 decap fixes: 8 broken, 1 DRC** (at clearance 0.1: 14 broken) |
| r6 | the r5 skeleton with U6 turned 90° (west face to J2, east face to J3 and the SPI bus) | s10 14 … s1 31 | r6/s10 with 2 decap fixes: 12 broken (worse) |

**Work on the best (r5/s6) route:**
- another all-nets pass: 8 broken went to 9;
- vias 0.45/0.2 mm: 8 (no change);
- vias 0.45/0.2 plus grid 0.05: 11;
- scoped rip-up laps on the blockers the router's hints named: 8 broken, DRC 1 went to **0** (blocking 8). This is the shipped board.

**The three failed approaches that fired the stop rule:**
1. the r6 placement with U6 at 90°: 12 broken;
2. routing the 7 failed nets first, then everything else: 16;
3. the first-choice retry levers (`--ripped-route-avoidance-cost 3 --track-proximity-cost 2`): 20.

**CHOSEN.json:** round 5, seed 6, clustered start, plus four `place_pose` decap moves: C21 to U3 pin 10, C24 to U3 pin 33, C28 to U6 pin 33, C34 to U6 pin 29.

**Final chain** (`final_route/`), replayed from `kept/r5s6_fix.kicad_pcb`. It reproduced the exploratory result: step2 blocking 9, step3 blocking 8.
1. `route_planes`
2. `qfn_fanout` on U3
3. `qfn_fanout` on U6
4. `place_fanout_clearance` (moved 0 parts)
5. `route_diff` (USB, 90 Ω)
6. `route.py '*'` (track 0.0889 mm, `--clearance-ceiling 0.09`, layer costs 1/6/2.5/1)
7. a scoped `route.py` lap on the 7 failed nets plus GND/+3V3, with `--rip-existing-nets /ICE_45 /ICE_48 /LED_B /LED_G /SRAM_SS`

## 4. Floors: where the board went below its authored rules

| rule | input project | shipped project | why |
|---|---|---|---|
| min_clearance | 0.127 | **0.09** | JLC floor: `--clearance-ceiling 0.09` on the route steps, 0.1 on the fanouts |
| min_track_width | 0.1524 | **0.0889** | signals routed at `--track-width 0.0889` |
| min_via_diameter | 0.508 | **0.25** | the router escalated to advanced 0.25/0.15 mm vias in rescue (464 escalations on step2) |
| via annular ring | 0.124 | 0.05 | same escalation |
| min_through_hole | 0.254 | 0.15 | same escalation |
| min_hole_clearance | 0.254 | 0.09 | the bare pour first lowered it to 0.127 (TOOL_GAPS 4), the route steps then to 0.09 |
| hole-to-hole | 0.254 | 0.254 | unchanged |
| copper-to-edge | 0.635 | 0.635 | unchanged |

`route.py` on step2 reported: `Design rules [--escalation fab, --fab-tier auto]: 396 feature(s) on 61 net(s) delivered below the requested size (smallest track width 0.0889 mm, smallest via diameter 0.25 mm)`.

`check_complete --authored-from` the input board says **UNSOUND** (exit 5) and names track 0.1524 to 0.0889, via 0.508 to 0.25, annular 0.12446 to 0.05, and hole 0.254 to 0.15.

Also, 102 vias sit in paste openings. This file format cannot declare their Type VII protection, so it has to go on the fab drawing.

## 5. Timeline and where the time went

| UTC | step |
|---|---|
| 20:32 | FIRST_CMD; read the skill files, `board_brief`, `board_context`, nets |
| 20:38 | fiducials placed and locked; `intent_rows.json`, `groups.json`; `check_groups`, `check_floorplan` |
| 20:41 | r1 placed (12 seeds, about 1 min) |
| 20:43-20:52 | r1 judged; chain calibrated on r1/s6 (10 variants); r1 re-judged with the thin-track chain |
| 20:53-21:00 | r2 placed and judged; full-route probe of r1/s6 (6 min) |
| 21:00-21:03 | r3 placed and judged (best: s10, 9); first hand decap fixes |
| 21:04-21:17 | two full routing chains (layer-cost variants A and B), two iterations each: 16 broken |
| 21:09-21:16 | r4 and r5 placed and judged, in parallel with those chains |
| 21:18-21:24 | r5/s6 decap fix, full routes at clearance 0.1 and 0.09: 8 broken |
| 21:24-21:35 | via, grid and iteration variants; scoped rip laps (blocking 8); r6 placed and judged |
| 21:35-21:42 | r6 full route (12), failed-nets-first (16), retry levers (20): stop rule fires |
| 21:43-21:46 | best chain replayed into `final_route/`; `final.kicad_pcb` frozen |
| 21:47-21:50 | verifier (1 call), `grade.py`, ledger closed, `measure.py` |

Where the time went, per `measure.py`:
- wall clock 1:17:58: 19 min waiting on background jobs, 24 min of other tool time, 35 min of model time;
- 246 tool calls: `route.py` 35, `quick_score` 20, `board_score` 20, `route_planes`, `qfn_fanout` and `route_diff` 17 each, `place_simple` 10.

Placement itself was cheap, about 1 minute per 12-seed round. The time went into judging and full routes (each full route took 4-6 minutes) and into the hand decap fixes.

## 6. Tool gaps (details and repro commands in TOOL_GAPS.md)

1. The round judge (`quick_score`) cannot see the intent's decap limits, which `board_score` counts as blocking. Every judged seed of every round could never have reached DONE, and the "stop at the first clean fast route" rule would have shipped a board that `board_score` blocks.
2. No tool repairs decap limits on a placed board. `place_simple --decap-limit-weight 100` left the same QFN side pins (the ones facing the header rows) broken on every seed; I did five hand passes with `place_pose`.
3. The quick judging route did not predict the full route here. One placement ranged from 8 to 42 under small parameter changes, and the eventual best went from 22 quick to 9 full.
4. A bare `route_planes` pour lowered the authored `min_hole_clearance` from 0.254 to 0.127. It says so loudly, but nothing asked for it.
5. The Step 2d iterations were byte-identical no-ops on the plateaued board.
6. Skill instruction gaps:
   - declaring module rows in `fixed_poses` needs a new intent file when the given intent is fixed;
   - there is no step for repairing decap limits after `place_simple`;
   - the skill does not say whether re-placements after a classification count against the 3-round limit;
   - `check_floorplan` exits 4, and `grade.py` reports `floorplan_pass: false`, with 0 errors (the given intent's dark, owed rules).
7. `place_pose` on a pile prints about 280 KB of JSON for a six-part `set`.

No tool said "fine" about a broken board in this run. The closest is gap 1: the judge's score says nothing about the floorplan component.

## 7. Verifier

One verifier call, `verdict_1.txt`: **VERDICT=FAIL**.

| check | result |
|---|---|
| sha256 | matches |
| check_assembly | buildable |
| check_floorplan | 0 errors |
| mechanical facts | exact |
| board_score | blocking 8 (broken 8) |
| check_complete | INCOMPLETE |
| check_connected | 8 disconnected pads |
| check_drc | clean |
| check_complete --authored-from | UNSOUND (the floors in §4) |

Lenses: connectivity FAIL (evidence 8), drc PASS, spec FAIL (`check_complete` INCOMPLETE; mechanical facts pass).

It also reviewed the USB pairs, which the chain recorded as 90 Ω: 28.2 of 70.5 mm runs over reference voids, and /USB_P vs /USB_N skew is 7.4 mm. I did not call the verifier again: the stop rule had already fired, so there was no fix to verify.

## 8. Ledger

`ledger.jsonl` has 94 rows, closed by one `--final --stop-condition 3` row carrying the three lens files. It records:
- every judged seed of rounds 1-6 (the placement and its fast route, `--rejected` where not kept);
- the hand-fixed placements;
- every full route and rip-up lap;
- the classification row.
