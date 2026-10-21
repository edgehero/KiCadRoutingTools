# REPORT: gp14 board 11, daplink (`/plan-pcb-placement full`)

**Result: DONE.** `final.kicad_pcb` (sha256 `4d7a27e5291f5f87dc74e9f0bda9dde2e446a2f532acf09de804838b3b1b476b`) was routed from round 1 seed 3 (scattered start). No part was moved after `place_simple`, so `CHOSEN.json` has `"after": []`.

## 1. The result

| DONE condition (full mode) | measured |
|---|---|
| `board_score` blocking | **0** |
| unrouted / broken | **0 / 0** |
| `check_complete --intent intent_edges.json --baseline daplink.kicad_pcb` | **DONE**. Impedance, length and net widths are UNEXAMINED because the board declares no spec for them. |
| `check_complete --authored-from daplink.kicad_pcb` (report only) | DONE. It lists copper-to-hole 0.25 mm: 8 places at 0.1751 mm, all P1's own pads against P1's own NPTH pegs. That is the footprint's own geometry (see Floors). |
| `check_connected` | all 30 routed nets fully connected; the KiCad refill cross-check agrees |
| `check_drc --baseline --clearance-margin 0.1` | 0 violations, plus 2 same-net self-crossing warnings that KiCad permits |
| KiCad's own DRC (`kicad_drc_compare`, baseline r1/s3) | kicad 0, check_drc 0, CONSISTENT. 4 pre-existing items were subtracted: P1 pads against P1's NPTH pegs at 0.1751 mm, below the shipped 0.2 mm. |
| `check_weird` | no weird copper |
| `check_assembly --intent --baseline` | buildable, blocking 0 |
| `check_floorplan --allow-routed` | 0 errors |
| `grade.py --mode full` | done: true, blocking 0, drc 0, check_complete DONE, authored-from DONE, floorplan 0 |

- **blocking_by:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, undersized 0, unrouted 0. Impedance, length and net_widths are null (nothing declared).
- **Quality:** 56 vias, 598.78 mm copper, 435 segments.
  - All 56 vias are 0.5/0.3 mm, the board's own minimum via.
  - No via sits in a pad.
  - Signal tracks are 0.127 mm. Power tracks are 0.3/0.4 mm, narrowed at the 0.5 mm-pitch pins.

## 2. Inputs, groups and every judgement call

**What I was given:**
- A 50 x 20 mm two-layer board with rounded corners: 35 parts in the pile, 50 nets, no copper, no pours, no stackup.
- The design brief puts P1 (GCT USB4105 USB-C) on the west edge and RST1 (Alps SKRK) on the north edge. Where along each edge is "unknown".
- There is no `mechanical.json`.
- `intent.json` has crystal proximity rows for Y1, C5 and C6, and a 13.93 mm decap pin budget.

**EMC:** `board_context` names one EMC role, the 8 MHz crystal Y1, and no converter or switch node, so `keep_away` stays empty. No EMC limits were given and the user was not available. I added none beyond the given crystal rows.

**What the parts are:**
- U2: STM32F103CB, the probe's MCU (LQFP-48, 0.5 mm pitch).
- U1: AMS1117-3.3 regulator fed from USB power, with C1 10 nF and C2 10 uF on its input and C3 10 uF on its output. C3 is the only +3.3V capacitor on the board.
- P1: USB-C connector, with CC pull-downs R1/R14 (5k1) and series resistors R12/R13 (33 ohm) on D-/D+.
- Around the MCU's USB pins: C7/C9 (18 pF) and R15, the 1k5 D+ pull-up.
- Y1: 8 MHz crystal with load capacitors C5/C6.
- MCU support parts:
  - the reset network R2/C4;
  - the boot and pin straps R3, R4, R9 and R10;
  - R5, a 100 ohm resistor on the target SWD data line.
- LEDs D1–D3 with resistors R6–R8.
- RST1 resets the target, with pull-up R11 and capacitor C8 on that line.
- J1: 1x4 vertical header for programming the probe MCU itself.
- J3 (top face) and J2 (bottom face): Harwin M20-89005 right-angle SMD 1x5 headers to the target.
- RST1 is a top-push button with a round cap (checked on distributor listings), so it sits flush at its edge and does not overhang.

**Groups** (`groups.json`, 6 groups; `check_groups` gives 0 errors and 1 warning):

| group | parts | why |
|---|---|---|
| usb_in | P1, R1, R14, R12, R13 | connector, CC pull-downs, and the series pair kept at the connector end |
| power | U1, C1, C2, C3 | regulator between the USB entry and the MCU; placed near usb_in and core, no edge hint |
| core | U2, Y1, C5, C6, C4, R2, R3, R4, R9, R10, R5, C7, C9, R15 | MCU, crystal, reset network, straps, R5 at the pin that drives it, and the MCU-side USB parts |
| target | J3, J2 | the two target headers, stacked on opposite faces |
| ui | RST1, R11, C8, D1, R6, D2, R7, D3, R8 | north-edge button with its reset network beside it, plus the LEDs |
| prog | J1 | a short vertical header gets no edge rule; only "near core" |

The one warning is that J2 has 2 signal links to core and none to its own group, which is normal for a connector.

**Judgement calls**, written into `intent_edges.json`. That file keeps every row of `intent.json`, which itself is unchanged.

1. **J2 and J3 go on the east edge.** They are right-angle headers whose pins must stick out past the board, because the mating socket cannot sit on the board surface. East is the end opposite the USB connector. Both sit at the same point on opposite faces; they are SMD, so their copper does not collide.
2. **Overhang bands.**
   - Because the outline has rounded corners, the band is measured on the courtyard plus the 0.55 mm board margin, not on the drawn body.
   - J2/J3 get 7.0–7.4 mm: the plastic body flush with the edge and 6 mm of pins past it.
   - P1 gets 1.05–1.35 mm. The footprint's own "PCB Edge" line puts the connector mouth flush with the edge. The default band of 0 would have seated it 1.055 mm inside the board (TOOL_GAPS 5).
3. **J2 and J3 were locked by hand** at the centre of the east edge (149.18, 110.0, rotation 0) with `place_pose`, because `place_simple` refused to seat them (TOOL_GAPS 1). Being locked costs at most ±3.9 mm of slide along the edge.

## 3. Placement round

Round 1 (`r1/`) placed 12 seeds (6 scattered, 6 clustered) in 9 s, and all 12 were legal. The 6 cheapest were judged with one fixed chain, `helpers/judge_chain.sh`, at about 4 s per seed. The chain is:
1. GND pour on the bottom layer.
2. `qfn_fanout` on U2.
3. `place_fanout_clearance`.
4. `route_diff --quick 2`.
5. `route.py --quick 2`.

| seed | start | anneal cost | fast-route blocking | vias | copper (mm) | segments |
|---|---|---|---|---|---|---|
| 8 | clustered | 505.8 | 1 | 52 | 548.83 | 700 |
| 10 | clustered | 511.5 | 2 | 56 | 590.16 | 634 |
| **3** | scattered | 524.7 | **0** | 49 | 554.99 | 633 |
| 4 | scattered | 526.8 | 1 | 53 | 522.62 | 616 |
| 1 | scattered | 548.3 | 2 | 54 | 533.39 | 598 |
| 0 | scattered | 591.8 | 2 | 59 | 574.48 | 703 |

Seed 3's fast route had no blocking net (`check_connected` agreed), so placement stopped (§3.6): no review round and no input changes. `route_review` found 0 open nets and 0 two-pad parts turned against their wiring.

## 4. The full route (plan-pcb-routing, by hand)

**Analysis:**
- Two layers, KiCad's default stackup, so there is no impedance pass.
- USB is full speed (12 Mbit/s). The D+/D- pair went through `route_diff` at 0.15 mm width / 0.2 mm gap, and the tool routed it single-ended as "electrically short".
- U2 (LQFP-48, 0.5 mm pitch) gets a fanout with `qfn_fanout`.
- Standard density tier with light signal content, so the plane goes in first: GND poured on the bottom layer, +5V and +3.3V as wide traces.
- No high-speed nets, so no GND-via or stitching tail. No keep-away rules (all digital).
- Net coverage (Step 5b): the route step excludes nothing, which matches the empty impedance set, and the poured GND is in `--power-nets`.
- `route_plan_check` passed all 17 rules on every arm.

| arm | how it differs | result |
|---|---|---|
| A (`final_route_old1/`) | the judge chain without `--quick`; `--clearance-ceiling 0.2`, default fab tier and escalation | complete, but the router lowered the board's own clearance and via size: 14 vias dropped to 0.25/0.15 mm and clearance to 0.1818 mm. Its edge-clearance write then caused 3 floorplan errors. Rejected. |
| B (`final_route_old2/`) | board's own minimums held: `--fab-tier standard --escalation board`, `--board-edge-clearance 0.55` | blocking 0 and 55 vias, but `check_complete` INCOMPLETE because of one dangling +3.3V segment that KiCad flags, and 15 vias inside SMD pads. Rejected. |
| **C** (`final_route/`, shipped) | B plus `--same-net-pad-clearance 0.1` | **DONE**: 56 vias, 598.78 mm, 435 segments, no via in a pad, no size reductions |

Each arm took 14–15 s. Arm C was re-run from scratch in `final_route/` with `REDO_RUNDIR`, `REDO_MANIFEST` and `KICAD_ROUTE_TRACE=1` set, and gave identical counts. The files are:
- `final_route/daplink_plan.sh`: the plan.
- `final_route/redo_commands.sh`: replays the chain.
- `final_route/daplink_plan.json`: the GUI plan, converted from the manifest (see TOOL_GAPS 10).

**Cutting vias after DONE.** I tried three different changes; none improved the board in the required order (blocking first, then vias, copper, segments):

| try | change | result |
|---|---|---|
| D (`opt_d/`) | GND poured on both layers | 53 vias, but 1 broken net and 1 copper defect |
| E (`opt_e/`) | `--layer-costs 1.0 1.5` | blocking 0, but 57 vias and 665.6 mm |
| F (`opt_f/`) | `place_pose` moved C4/R2 beside U2's reset pin (that net had 6 vias), plus one more routing pass | 52 vias, but +3.3V left open at U2 |

## 5. Stop rule

Stop rule 1, DONE: blocking 0, `check_complete` DONE, verifier PASS. Placement stopped after round 1 because the first clean fast route came in that round. After DONE, I stopped optimising when three different tries each failed to improve the board. No blockers remain.

## 6. Floors

- **Kept at the board's own rules:**
  - Default class clearance 0.2 mm.
  - Every via 0.5/0.3 mm.
  - Hole-to-hole 0.25 mm.
- **Power tracks:** the route step reported "3 feature(s) on 3 net(s) delivered below the requested size (smallest track width 0.127 mm)". These are power tracks narrowed at the 0.5 mm-pitch pins: GND 20 mm, +3.3V 17 mm and +5V 12 mm at 0.127 mm. That is below the requested power widths but above every floor the board sets (its minimum track width is 0). No power-width spec is declared.
- **Lowered in the shipped project:** minimum copper-to-hole clearance went from 0.25 to 0.2 mm. `route_planes` wrote this without being asked (TOOL_GAPS 4).
  - Only P1's own GND/VBUS pads are closer than 0.25 mm to a hole, and only to P1's own NPTH pegs (0.1751 / 0.2099 mm). That geometry is the same on the unrouted placement.
  - KiCad reports the 4 instances under 0.2 mm as errors on both the placed and the routed board.
  - No routed copper is involved: `check_drc --hole-clearance 0.25` finds 0 violations.
- **Tightened:** minimum copper-to-edge clearance went from 0 to 0.55 mm, because I routed with `--board-edge-clearance 0.55` so the overhang bands keep one meaning (TOOL_GAPS 2).

## 7. Timeline (UTC) and where the time went

| time | step |
|---|---|
| 19:00:58 | FIRST_CMD |
| 19:01–19:05 | README, brief and intent; both skills and their references; `board_brief`, `board_context` |
| 19:05–19:09 | groups and `intent_edges`; exploratory seeds e1–e3; diagnosed `place_simple` refusing J2/J3; locked them by hand; P1 band |
| 19:09:28–19:09:37 | round 1, 12 seeds |
| 19:10:38–19:11:20 | 6 judging routes; seed 3 clean |
| 19:13:08–19:13:22 | full route, arm A |
| 19:13–19:17 | diagnosed the lowered rules and the band problem; arms B and C |
| 19:18 | first DONE |
| 19:19–19:22 | via tries D, E, F (all worse) |
| 19:23–19:28 | verifier, TOOL_GAPS, grade, measure |

Almost all of the 27 minutes went to reading and to diagnosing tool behaviour. The machine work itself was small: placement 9 s, judging about 25 s, about 15 s per full route. `measure.py`: 26:18 wall, 1245.6 s model time, 322.2 s other tool time, 9.7 s waiting on jobs.

## 8. Tool gaps

`TOOL_GAPS.md` has 10 entries, ranked by cost:

1. The `place_simple` edge seat counts silk-only "pads", so it found no room for the right-angle headers.
2. An overhang band changes meaning once routing writes the board's edge clearance.
3. The skills' routing chain lowers the board's own clearance and via size on a board that routes completely without that.
4. `route_planes` ignores `--board-edge-clearance` when it writes the project, and lowers the hole clearance unasked.
5. The default overhang band of 0 seats the USB-C mouth 1.055 mm inside a rounded-corner board.
6. `route.py` leaves a segment KiCad flags as dangling, and the scoped retry does nothing.
7. Default routing puts 15 vias inside SMD pads (filled-and-capped vias) on a cheap 2-layer board, and the skill never mentions the flag that prevents it.
8. Helper `seat_probe.py`.
9. Helper `judge_chain.sh`.
10. `manifest_to_plan` silently drops the pour and fanout steps from a plan.sh.

Tools that reported "fine" about something that was not: `route.py`'s own tally on arm B reported clean while KiCad flags the dangling segment; and `route_planes` lowered the project's hole clearance, so `check_drc` and KiCad then grade against the lowered value.

## 9. Verifier verdicts

`verdict_1.txt` (call 1 of 3): **VERDICT=PASS**. The lens files read connectivity PASS, drc PASS, spec PASS. In summary:
- The sha256 matches, and the input files match the README hashes.
- `check_assembly`: buildable, nothing off the outline, nothing on a plug's mating area.
- `check_floorplan`: 0 errors.
- `board_score`: blocking 0.
- `check_complete`: DONE; the authored-from floor is the P1 pad-to-own-hole footprint geometry.
- `check_connected`: all connected. `check_drc`: 0.
- Mechanical facts:
  - P1 faces west, its PCB Edge marker 0.005 mm inside the edge.
  - RST1 sits at the north edge.
  - J2/J3 are on the east edge, housing 0.049 mm inside, pins 6 mm out.
- The verifier also ran KiCad DRC itself: 4 errors, all the P1 pad-to-own-hole pairs, plus cosmetic silkscreen warnings.

The ledger (`ledger.jsonl`, 21 rows) is closed with `--final --stop-condition 1` and the three lens files.
