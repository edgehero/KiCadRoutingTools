# REPORT — gp14 board 06, rp2350_fpga_eensy_prePlane (`/plan-pcb-placement full`)

## Result: DONE

- **Board:** `final.kicad_pcb` with `final.kicad_pro`, sha256 `59696295866598d1567c0cf6e6a490e4392bc7f43e2b2d734c00235d84dd040f`. It is the same board as `final_route/s8_clean.kicad_pcb`.
- **Placement:** round 2, seed 7 (clustered start), plus 13 capacitor poses listed in CHOSEN.json.
- **Routing:** `final_route/plan.sh`; the recorded manifest is `final_route/redo_commands.sh`.

| DONE condition (full mode) | Measured |
|---|---|
| board_score blocking | **0** (unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, drc_via_in_paste 0) |
| check_complete | **DONE**. Impedance, length and net_widths are UNEXAMINED because the board declares no such spec. |
| check_connected | All 74 multi-pad nets connected (27 of the 101 nets have a single pad). |
| check_drc (`--clearance-margin 0.1`, baseline = input) | 0 violations |
| check_assembly (`--intent --baseline`) | Buildable, blocking 0, courtyard_blocking 0, no gating pad, graphic or keep-out copper off the outline. |
| check_floorplan (`intent.json`) | 0 errors, 2 warnings: U5 /VIN has no decap anywhere on the board (a schematic matter), and U8's edge pin rows. |
| Mechanical facts | U8 exactly at (148.5, 105.005, 270) and locked. J1 on the north edge, mating face out, body front on the outline (0.000 mm overhang), 1.40 mm off centre. |
| KiCad DRC (kicad_drc_compare, KiCad 10) | kicad=0, check_drc=0, CONSISTENT. Warnings only: one connection_width, one track_dangling, and hole_to_hole inside U8's own footprint. |
| Independent verifier | **PASS** (`verdict_1.txt`; connectivity, drc and spec lenses all PASS) |
| grade.py --mode full | `done: true`, blocking 0, 152 vias, 995.18 mm copper, 1059 segments |

`blocking_by`: every graded component is 0 (assembly, broken, drc, drc_via_in_paste, floorplan, undersized, unrouted); impedance, length and net_widths are null (ungraded).

**Quality:** 152 vias, 995.18 mm of copper, 1059 segments. The first DONE board, before via optimisation, had 159 / 958.41 / 1303.

## Stop rule

**Stop rule 1 — DONE** (board_score blocking 0, check_complete DONE, verifier PASS). After DONE I optimised vias. `--via-cost 150` cut vias from 159 to 152. The next three variants did not beat it:
- via cost 200 left one net open;
- via cost 150 with max-ripup 3 gave 155 vias;
- via cost 120 left one net broken.

No blocker remains. The residual items, none of them blocking:
- **KiCad connection_width warning** on `Net-(J1-D+-PadA6)` at (147.55, 94.85): a copper web narrower than 0.075 mm at J1's D+ pad.
- **KiCad track_dangling warning:** a 0.1 mm GND stub on F.Cu at (154.1, 91.4)–(154.1, 91.5). Its end lies on another GND track, so it is still connected.
- **check_drc:** one same-net self-crossing warning.
- **Via-in-pad:** 89 vias in pad or paste openings, all declared filled and capped (IPC-4761 Type VII). This is a fab cost item.
- **Power-width necking** (`power_widths` from route.py). No `--net-min-widths` spec was given, so none of this is graded:

  | Net | Length under the requested width | Requested | Narrowest |
  |---|---|---|---|
  | +3V3 | 8.3 of 93.1 mm | 0.2 | 0.0762 |
  | GND | 0.7 of 101.0 mm | 0.2 | 0.0762 |
  | Net-(D2-K) | 4.5 of 17.0 mm | 0.25 | 0.125 |
  | +1V1 | 2.0 of 32.4 mm | 0.15 | 0.0889 |
  | /RP2354A/1V1 | 2.4 of 32.4 mm | 0.15 | 0.0762 |
  | Net-(U6-VREG_LX) | 1.2 of 2.1 mm | 0.2 | 0.0889 |

- **EMC rows:** the user was unavailable, so no emc_roles proximity limits or keep_away rules were given, and I invented none. board_context proposed keeping the U6/U7 switch nodes 3 mm from the Y1/Y2 clock nets (a derived default); I did not apply it.

## Floors (where the run went below the board's authored or fab floors)

`check_complete --authored-from <input>` reports **UNSOUND** (reported, not gating; see `check_complete_authored.txt`):
- **Via annular ring 0.1 → 0.05 mm.** These are the 0.25/0.15 mm via-in-pad escapes under U2, a 0.4 mm-pitch WLCSP. No via with a 0.1 mm ring fits that pitch at 0.09 mm clearance. The verifier counted 29 vias at 0.25/0.15 (ring 0.05) and 3 at 0.30/0.15 (ring 0.075). This is JLC's "advanced" tier. route.py reported: "125 feature(s) on 20 net(s) delivered below the requested size (smallest track width 0.0762 mm, smallest via diameter 0.25 mm); 130 fab-tier escalation(s) to advanced".
- **Via drill 0.2 → 0.15 mm**, on the same vias. 0.15 mm is the board's own min_through_hole_diameter.
- **Copper-to-hole clearance (min_hole_clearance) 0.25 → 0.09 mm.** The pour step's writeback lowered it ("FAB FLOOR RELAXED"). Against the authored 0.25 mm, the board measures 0.1431–0.1557 mm over 199 items (TOOL_GAPS 8).

Clearance stayed at the Default class value of 0.09 mm (`--clearance-ceiling 0.09`). Signal tracks are 0.0762 mm: below the Default class width of 0.09 (a drawing default, not a DRC floor) and above the board's min_track_width of 0.075. **Confirm the fab supports advanced-tier 0.25/0.15 via-in-pad, filled and capped, before ordering.**

## Inputs, and the judgement calls

**What I was given:**
- **Board:** a pile with no routing.
- **`intent.json`:**
  - U8's fixed pose, from mechanical.json;
  - J1 on the north edge;
  - decap limits of 1.0925 / 5.904 mm, taken from the source board;
  - the crystal claims.
- **Design brief:** J1 on the north edge, position along it unknown.

**The board itself:**
- 6 copper layers, 17.78 × 35.81 mm (Teensy 4.0 form factor);
- 61 parts (4 on B.Cu), 101 nets;
- U6 is an RP2354A in a 0.4 mm QFN-60;
- U2 is an Efinix T8 in a 0.4 mm WLCSP-49;
- U8 is a Teensy40 pin frame whose castellated pins run along both long edges and the south end.

**Intent variants.** The given `intent.json` was never edited, and it is the intent every grade above used.
- **`intent_u8lock.json`:** U8's `fixed_poses` row is removed. U8 is instead KiCad-locked in the input board at exactly that pose (`place_pose set U8 148.5 105.005 --rot 270 lock U8`, skill §3.1). place_simple refuses U8's declared pose (TOOL_GAPS 2), which made every seed illegal.
- **`intent_frame.json`** (identical to `r2/intent.json`, the round the board came from): adds three keep-out strips over U8's pin rows (pad edge + 0.09 mm, both faces). With my helper the anneal no longer sees the frame at all, so without these strips the pins would only be checked at the very end.
- **`intent_r3.json`** (round 3 only): adds three review-round proximity claims putting U1, J2 and J3 at the U6 pins they serve, graded as warnings.

**Placer.** `helpers/place_simple_frame_fix.py` is place_simple with the pin frame left out of the anneal's overlap term (TOOL_GAPS 1). Plain place_simple left 3–5 parts illegal on all 12 seeds. With the helper, 11 of 12 seeds were legal in round 2 and 9 of 12 in round 3.

**J1 overhang.** I could not fetch the PCB-layout drawing from the HRO TYPE-C-31-M-12 datasheet (the LCSC PDF links returned only a title page). So I declared no `overhang_mm`, and J1 sits flush with its body front on the outline.

**J3 (side-entry Qwiic JST-SH) and SW1 (side-actuated button).** The brief claims neither. There is no free edge for them:
- both long edges carry U8's castellated pins;
- the south end carries U8 pins 15–19;
- J1 occupies the north edge.

I left both to the anneal, so they sit inside the board. A cable to J3, or a finger on SW1, has to reach them from above. I am reporting this, not solving it.

**Groups.** `groups.json` (identical to `r2/groups.json`) has 7 groups; check_groups reports 0 errors.

| Group | Parts | Anchor / hints | Why |
|---|---|---|---|
| usb_in | J1 U3 R1 R2 D2 | J1; near power, mcu | USB-C (north edge, declared), CC 5.1k pull-downs, USBLC6 ESD right behind D+/D-, VBUS Schottky into Net-(D2-K) |
| power | U5 R11 R12 R13 U7 L2 C1 C26 C27 | U7; near usb_in | LM73100 ideal diode / eFuse from the Teensy /VIN pin with its UVLO/OVLO divider, ORed with VBUS; TPS62162 3V3 buck with L2, its input caps on Net-(D2-K) and the 22 µF output cap C27 |
| mcu | U6 L1 C5 C6 C28 C29 C30 R3 R4 R5 C7–C13 C19–C21 Y1 C14 C15 | U6; near usb_in, fpga, psram | RP2354A with its core-regulator inductor L1 and /RP2354A/1V1 caps, the VREG_AVDD RC, ten 3V3 caps for its ten 3V3 pins, the USB 27R pair at the chip (the usual RP2040/RP2350 layout), and the crystal and load caps claimed at XIN/XOUT |
| psram | U1 C2 | U1; near mcu | QSPI PSRAM on the back face with its back-face decap |
| debug | J2 J3 | J2; near mcu | Back-face Tag-Connect SWD and Qwiic connector; both talk only to U6 |
| fpga | U2 C3 C16 C17 C18 C22–C25 U4 Y2 R6 RN1 RN2 | U2; near mcu, ui | T8 FPGA with its +1V1 and VCCIO caps; the TPS7A20 1V1 LDO U4, which goes with its only load (the point-of-load rule); the 32 MHz oscillator on PLLIN with its enable pull-down; the two configuration resistor arrays |
| ui | D1 R7 R8 R9 SW1 | D1; near fpga | RGB LED and its three resistors (driven by FPGA R/G/B), and the button on the FPGA's CSO pin |

**Other judgement calls:**
- **U4 with the FPGA, not the power group.** check_groups warns that U4 has 2 signal links to power and 1 to its own group; I kept it with the FPGA under the point-of-load rule.
- **R4/R5 with U6, and C27 in the power group.**
- **No `side` or `edge` hints anywhere.** The power group stays by its entry, and the ui group has no free edge to go to.
- **`--decap-limit-weight 30`.** Measured in scratch on seeds 0–3 against 10 and 100:

  | Weight | Legal seeds | decap errors on legal seeds |
  |---|---|---|
  | 10 | 0 of 2 new seeds | 7–8 |
  | 100 | 0 of 2 | – |
  | 30 | 2 of 2 | 0–1 |

## Rounds

| Round | Inputs | Legal seeds | Judged seeds | Fast-route blocking (vias) | Best |
|---|---|---|---|---|---|
| r1 | fixed.kicad_pcb, groups.json, intent.json, defaults | 0/12 | none (judge.json empty) | – | – |
| r2 | U8 locked (fixed_u8lock), intent_frame, helper, decap weight 30 | 11/12 | 2, 3, 0, 7, 5, 8 | 8 (146), 13 (141), 11 (154), **2 (143)**, 11 (161), 17 (145) | **s7** |
| r3 | as r2, plus intent_r3 claims and groups_r3 (psram and debug folded into mcu) | 9/12 | 7, 5, 0, 2, 3, 8 | 9, 8, 5, 6, 3 (151), 19 | s3 at 3, worse than r2 s7 |

**Round 1.** Every seed was illegal. The diagnosis found two tool faults (TOOL_GAPS 1 and 2), not an over-full board: place_simple refused U8's pose, and its anneal counted U8's whole-board rectangle as overlap. I changed the inputs, not the board.

**Review of r2 s7** (route_review on its fast route):
- **Open nets:** `/RP2354A/SDA` at J3 and `/T8F49I2X/PIN.11` at U2. +3V3 is listed open only because `--quick 2` skips the plane finalize.
- **The common failure across all six r2 fast routes** was the back-face parts' nets to U6:
  - SWDIO on s2, s3 and s8;
  - SDA on s2, s0 and s7;
  - QSPI SIO0/SIO3 on s2 and s5.
- **The cause on s7:** J2 sat north of U6 although its SWD pins are on U6's south row; U1 sat south although its QSPI pins are on the north row.
- **Change for round 3:** proximity claims for U1, J2 and J3 at those pins, and the psram and debug groups folded into mcu.

**Effect of round 3.** The back-face nets mostly closed, but the FPGA configuration nets opened instead; the best fast route was 3 against round 2's 2. The three rounds were then used up, so I kept r2 s7 (fewest blocking).

**After the rounds.** CHOSEN.json `after` lists 13 `place_pose set`s, applied in one call to produce `placed.kicad_pcb`. r2 s7 had 5 decap_distance **errors**: C17, C27, C28, C29 and C6 were past 1.0925 mm. These block DONE through board_score's floorplan component. The fixes:
- **C28 and C29:** moved 0.34–0.5 mm up against U6.
- **C6, C17 and their neighbours:** re-seated by a scoped re-anneal with everything else locked and `--decap-limit-weight 1000`.
- **C27 (0805):** it only fits within 1.09 mm on U7's north or south side (TOOL_GAPS 3), so I placed it south of U7 by hand and moved C7 and C15 out of its way.

The result has 0 floorplan errors and is buildable. Its fast route scored 7 against s7's 2 (the fast route is noisy at this density), but its full route closed.

## Routing (plan-pcb-routing, followed by hand)

The board is STANDARD tier: it has 6 layers, but only 49 balls (under 100) and 101 nets (under 150). So the planes are inner-layer pours only. The stackup is KiCad's default (εr 4.5 everywhere), so no `--impedance` step; USB runs at full speed anyway. The chain is `final_route/plan.sh`; `route_plan_check.py` checked it and all 17 rules passed.

1. Bare pour: GND solid on In1, +3V3 solid on In2.
2. U2 fanout with `bga_fanout --escape-method underpad`:
   - via 0.25/0.15, track 0.0762, clearance 0.09;
   - In1/In2 forbidden (`--layer-costs 1 -1 -1 1 1 1`), plane nets excluded;
   - result: 30/30 escaped, 0 failed, 0 grazes, 11 plane balls dropped with in-pad vias.
3. U6 `qfn_fanout` stubs with GND/+3V3 excluded (`--nets '*' '!GND' '!+3V3'`). Without that, the GND stubs ended up as dangling copper (TOOL_GAPS 6).
4. One `place_fanout_clearance` pass; it moved one cap and the decap limits held.
5. `route_diff` on both USB pairs at 0.1/0.1; both coupled, none single-ended.
6. `route.py --nets '*'`:
   - plane nets in `--power-nets`, `--layer-costs 1 6 2.5 1 1 1`;
   - track 0.0762, `--clearance-ceiling 0.09`, via 0.35/0.15, `--max-ripup 5`;
   - **`--grid-step 0.05`** for the 0.4 mm-pitch parts and **`--via-cost 150`**;
   - the Step 2c environment bundle.
7. A closing `route.py --nets GND +3V3`, so the chain ends on route.py.
8. `helpers/drop_kicad_dangling.py` removed three 0.011–0.025 mm "kicad-dangling" power-width segments the route left behind (TOOL_GAPS 4).

How I got there (all on the same placement, each run about 20–60 s):
- **Baseline flags at grid 0.1:** 2–4 U2 nets left open, boxed in by the fanout copper. Two Step 2d iteration passes were reverted by the improvement gate.
- **Step 2c environment bundle at grid 0.1:** 0 nets open, but dangling GND stubs.
- **Plane nets excluded from the QFN fanout:** the stubs went away.
- **Grid 0.05:** 0 nets open.
- **Via cost 150:** 7 fewer vias.

The chain that produced the first DONE board is kept in `final_route_old1/`.

## Timeline (UTC; FIRST_CMD 22:52:14)

| Time | Step |
|---|---|
| 22:52–22:58 | Read prompt, README and skills; board_brief, board_context; wrote groups.json; check_groups |
| 22:58–23:00 | Round 1 placement: all 12 seeds illegal |
| 23:00–23:08 | Diagnosed the U8 pose refusal and the frame in the overlap term; locked U8, wrote the intent variants and the helper; calibrated moves, keep-outs and decap weight in scratch |
| 23:08–23:13 | Round 2 placement (1.5 min) and six fast judging routes (about 30 s each) |
| 23:13–23:18 | Review, round 3 inputs, round 3 placement and six fast routes |
| 23:18–23:25 | Decap-limit repair (scoped re-anneals, hand poses), placed.kicad_pcb, CHOSEN.json |
| 23:21–23:32 | Full-route probes and routing variants (environment bundle, grid, QFN-fanout nets, cleanup) |
| 23:32–23:33 | final_route chain → first DONE (159 vias) |
| 23:34–23:38 | Via optimisation; final_route re-run with via cost 150 → 152 vias |
| 23:38–23:43 | KiCad DRC compare, grade.py, verifier (PASS, about 4 min), ledger `--final`, DONE marker |
| 23:43–23:45 | TOOL_GAPS.md, report, measure.py |

**Where the time went** (`measure.py --self --evidence`, saved in `measure_output.txt`). At the time of measuring, wall clock was 0:51:32:

| Category | Seconds | Share |
|---|---|---|
| Model | 1907 | 62% |
| Tool calls | 1067 | 35% |
| Waiting on background jobs | 118 | 4% |

There were 245 tool calls, 199 of them Bash. Placement runs were cheap: about 1.5 min for 12 seeds in rounds 2 and 3. A full route took about 20–50 s. Most of the time went into diagnosing the two place_simple faults and repairing the decap limits.

## Tool gaps (TOOL_GAPS.md: 10 entries, ranked by cost)

1. **place_simple's overlap term counts the pin frame.** The anneal counts U8's whole-board rectangle as overlap (442 of 464.5 mm²), so no state is ever "best" and 3–5 parts end illegal per seed. I wrote a helper.
2. **place_simple refuses U8's declared pose.** Its castellated half-holes count as "drill holes past the outline", so every seed exits 4 and `judge.json` is empty.
3. **The decap limit is out of the anneal's reach for C27.** The error-graded limit cannot be met for the 0805 bulk cap C27: the decap term pulls it to the pin side, where 1.09 mm is geometrically unreachable. Hand poses were needed.
4. **route.py leaves "kicad-dangling" micro-segments.** They fail check_complete and nothing in the repo removes them. I wrote a helper; #1234 and #162 are open on the producer.
5. **converge.py refuses a board_score-scored completion row** recorded after the quick_score-scored judging rows the skill prescribes.
6. **Skill gap:** the QFN fanout recipe in plan-pcb-routing does not exclude plane nets, which leaves dangling GND stubs.
7. **Skill gap:** plan-pcb-placement has no path for a round in which every seed is illegal.
8. **route_planes lowers a declared floor unasked.** It moved min_hole_clearance from 0.25 to 0.09 without being asked (it does disclose it).
9. **KiCad-only warnings.** KiCad reports a connection_width at J1 D+ and one track_dangling that no repo checker reports.
10. **Minor:**
    - board_score `--quiet` still prints a 21 kB line;
    - the resistor arrays and the RGB LED are elected decap "owner ICs";
    - place_pose's `legal` is never true on a castellated-frame board.

**Tools that said "fine" about something that was not:**
- place_simple's illegal list read as "board too full" when it was gaps 1–2.
- route.py reported `failed: 0` while check_complete said INCOMPLETE (gap 4).
- check_weird and check_complete were clean while KiCad reported connection_width and track_dangling (gap 9).

## Verifier

**`verdict_1.txt`: VERDICT=PASS** (one call of the three allowed).
- sha256 matches.
- check_assembly: buildable.
- check_floorplan: 0 errors.
- render_placement: no gating copper off the outline.
- U8 and J1 mechanical facts: measured and met.
- board_score: blocking 0.
- check_complete: DONE.
- check_complete `--authored-from`: UNSOUND (annular ring 0.1 → 0.05, min_hole_clearance 0.25 → 0.09), reported, not gating.
- check_connected: all connected.
- check_drc: 0 violations.
- KiCad DRC: 0 errors, 0 unconnected.
- Lenses `verdict_1_connectivity.txt`, `verdict_1_drc.txt` and `verdict_1_spec.txt`: all PASS.
- The diff pairs are not declared, but the verifier reviewed them: skew is 1.61 mm on the connector side and 0.77 mm on the MCU side.

## Files

Everything is in `wk/gp14/06_rp2350_fpga_eensy_prePlane/`:
- **Board and markers:** `final.kicad_pcb` / `.kicad_pro`, `FINAL.sha256`, `DONE`.
- **Placement record:** `CHOSEN.json`; `groups.json` (same as `r2/groups.json`).
- **Intents:** `intent.json` (given); `intent_frame.json` (the one the board was placed with); `intent_u8lock.json`; `intent_r3.json`.
- **Routing:** `final_route/` (plan.sh, redo_commands.sh, every step's board and log); `final_route_old1/` (the first DONE chain).
- **Rounds:** `r1/` to `r3/` (fixed board, groups, intent, seeds, judge.json, fast routes).
- **Ledger:** `ledger.jsonl`, 35 rows, closed with `--final --stop-condition 1`.
- **Verification output:** `verdict_1*.txt`, `grade_output.txt`, `grade_final.json`, `check_complete_authored.txt`, `kicad_drc_compare.txt`, `measure_output.txt`.
- **Tool problems:** `helpers/` (2 scripts), `repro/`, `TOOL_GAPS.md`.

No datasheet folder was created. All five input files still match their README sha256s.
