# REPORT: gp14 board 07, One-Air-Max (`/plan-pcb-placement full`)

## 1. Result

| DONE condition (`full`) | measured |
|---|---|
| `board_score` blocking | **0** |
| unrouted / broken | **0 / 0** |
| `check_complete` | **DONE** (impedance, length, net_widths UNEXAMINED: the board declares no such spec) |
| `check_assembly --baseline` | buildable (blocking 0, courtyard_blocking 0) |
| `check_floorplan --intent intent_gp.json` | 0 errors, 2 warnings (the two waived BAT1 overlaps) |
| `check_connected` | all nets fully connected |
| `check_drc --baseline --clearance-margin 0.1` | 0 violations |
| mechanical facts (`mechanical.json`) | all 6 poses at offset 0.0000 (measured by the verifier) |

- **blocking_by:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, undersized 0, unrouted 0. Impedance, length and net_widths are not graded.
- **Quality:** vias 225, copper_mm 2824.74, segments 1563. The first DONE board had 273 / 2484.15 / 1499; the via-cost-300 route was kept because vias rank first.
- **`grade.py --mode full`** (`grade/grade_final.json`): done true, blocking 0, drc 0, vias 225, check_complete DONE, check_complete_authored UNSOUND (§5), assembly buildable, floorplan_errors 0.

## 2. Inputs and judgement calls

**EMC rows:** none were given (user unavailable). No proximity limits or keep-away rules were added, and `board_context`'s proposed crystal/switch-node keep-away was not declared.

**Intent:** I placed with `intent_gp.json`, a copy of the given `intent.json`; the original is unchanged and its sha256 checks out. The additions:

- **Three judged poses in `fixed_poses[]`** (basis `derived_default`):
  - **U1 (ESP32-C6 module):** B.Cu at (175.0, 66.57), rot 180. Its antenna is flush with the north edge. That keeps it outside the F-side battery holder's shadow and inside the pocket the board's own GND pour leaves empty (x > 164.2 above y 60.6, x > 165.7 above y 76.1). A first try with the antenna on the south edge was aborted after 2 minutes.
  - **DC1 (solar DC jack):** F.Cu at (189.56, 76.57), rot 180, mouth flush on the east edge between BAT1's solder tabs.
  - **PWR_SW1 (slide switch):** F.Cu at (189.91, 94.5), rot 90, knob flush on the east edge.
  - DC1 and PWR_SW1 would normally be `edge_connectors[]` entries, but `classify_part` gives them no class, so an edge entry would not hold them to the edge (gap 4).
- **Keep-outs:**
  - `U1_antenna`, on F and B.
  - `BAT1_peg_hole_far_face`, on B with BAT1 allowed. Placement ran on a copy of the board without that hole (gap 1), and this keep-out keeps back-side parts off it. The `allow BAT1` was added after placement and changes no pose.
- **`overlap_waivers` for BAT1/DC1 and BAT1/PWR_SW1:** BAT1 draws no courtyard, so its pad-box fallback covers the gap between its own tabs (gap 5).

**Groups (13; `check_groups` 0 errors, 0 warnings):**

| group | members | why |
|---|---|---|
| usb_in | USB1, R1, R2, C1, R3, C71, C72, R62, R63 | USB-C with CC pull-downs, shield RC, D+/D- caps and the 22 Ω series pair |
| pwr5v | U6 buck, L2, C42–C49, R39, R40, TP2, R42, TP1, R72, R73, U7 mux, R43, R44, R45, F1, FB1 | battery → +5VBAT buck plus the USB/battery power mux; the decap rule ties C42–C45 to U7 |
| buck3v3 | U2, L3, C4, R52, R56, R57, C2, C14, C68, C3, C6 | +5V → +3V3 buck with its input and output caps |
| core | U1 plus decaps, BOOT/EN RCs, TPL5010 watchdog U3, LED2 driver, SW1, LED2, JP2, JP3 | JP2/JP3 moved here because 2 of their 3 links go to U1 and the I²C bus |
| ext_io | IO1, R76–R78, I2C3, U12 EEPROM, I²C pull-ups, C63 | I²C bus parts |
| pm | PM1, PM2, U13 load switch and its parts | PM sensors |
| uart_exp | U8 WK2132, X1, its load caps, D4–D7, RC/strap resistors, C65 | the PM sensors' UART bridge |
| co2 / ce / no2 | each sensor connector with its load switch(es) | one group per sensor |
| charger | U5 BQ25672 and its parts, Battery1, F2, LED3 | solar charger |
| solar_in | DC1, Solarpower1, D3, C31, C33–C35 | solar input |
| batt_prot | U4 BQ77905, Q1, Q2, shunt and tap filters, NTC1, PWR_SW1 | 3-cell battery protector |

Hints are `near` only. There are no edge or side hints, so all 192 back-side parts stay on B.Cu.

## 3. Placement

- **First attempt (`scratch/r1_withhole/`):** 12 of 12 seeds exited 4, each leaving 2–4 connectors with no legal pose (gap 1). I re-ran on `fixed_nohole.kicad_pcb`.
- **Round 1 (`r1/`):** 12 of 12 seeds legal, about 30 s each. I judged the six cheapest with the same quick route (`--quick 2`):

| seed | fast blocking | vias | copper_mm | segments |
|---|---|---|---|---|
| **8 (clustered, kept)** | **0** | **217** | 2465.91 | 2676 |
| 2 | 0 | 229 | 2528.66 | 2683 |
| 7 | 0 | 230 | 2378.35 | 2514 |
| 10 | 1 | 208 | 2423.73 | 2623 |
| 9 | 1 | 215 | 2388.93 | 2492 |
| 11 | 3 | 267 | 2706.73 | 2849 |

Seed 8's quick route had no blocking net, so round 1 was clean and no review round ran.

**Changes after placement** (listed in `CHOSEN.json` "after", with `place_args: []`), because seed 8 was not buildable (gap 2):
- restored BAT1's peg hole;
- moved C10, C13, NTC1 and Solarpower1 (front side) out of the battery holder's body;
- nudged L1, D1, L2, R46 and X1 with `helpers/fix_courtyards.py`;
- moved D5 by hand;
- turned R14 and R76 by 180°, as `route_review` suggested.

The result, `placed.kicad_pcb`, is buildable with 0 floorplan errors.

## 4. Routing and optimisation

- **Board facts:** 4-layer, STANDARD tier, default-like stackup, no impedance targets (USB is full-speed), no BGA. U5 (0.4 mm-pitch QFN) routed without a fanout step in every quick route.
- **Planes:** GND and PGND split on In2.Cu, +3V3 on In1.Cu. The board's own GND zone is one zone on F, B and In2, and `route_planes` cannot replace it one layer at a time, so its outer-layer GND floods stay.
- **Chain in `final_route/`** (recorded in `redo_commands.sh`):
  1. copy the placement (`copy_board`);
  2. antenna keep-out on all layers (`add_rule_area ANT_KEEPOUT`);
  3. pour the planes (`route_planes`);
  4. USB pairs at 0.1 mm width and gap (`route_diff '/USB*'`);
  5. `route.py --nets '*'` at 0.127 mm tracks and 0.45/0.2 mm vias, layer costs 1/3/3/1, `--via-cost 300`, 21 power nets at 0.3–0.8 mm;
  6. two more identical `route.py` passes (nothing new routed);
  7. `helpers/dedupe_segments.py` removed 54 exact duplicate segments (gap 3). This step is not in the manifest.

**Via optimisation (`opt/`, recorded in the ledger as rejected):**

| variant | vias | copper_mm | check_complete |
|---|---|---|---|
| default via cost (first DONE) | 273 | 2484.15 | DONE |
| via-cost 150 | 232 | 2561 | DONE |
| **via-cost 300 (kept)** | **225** | 2825 | **DONE** |
| via-cost 375 / 450 / 525 / 600 / 1000 | 224 / 221 / 220 / 217 / 218 | 2854–3030 | INCOMPLETE (leftover redundant stubs) |
| via-cost 300 + standard fab tier | 219 | 2831 | INCOMPLETE, blocking 2 |
| via-cost 300 + inner-layer cost 6 | 233 | 2938 | INCOMPLETE |
| GND/PGND also poured on B.Cu | 289 | 2125 | DONE |
| via-cost 300, no via-in-pad | 212 | 3048 | INCOMPLETE, blocking 3 |

## 5. Stop rule, remaining items, floors

**Stop:** condition 1, DONE. The ledger is closed with `--final` and the verifier's three lens files. There are no remaining blockers.

Things that do not block DONE but you should know before fabrication:

- **KiCad's own DRC** reports errors only inside individual footprints, and the identical set appears on the unrouted placement, so routing did not cause them:
  - Q1 and Q2: drain pads 5–8 touch the exposed pad 9, which has no net.
  - F2: a PCB-trace fuse whose net-less copper strip touches both its pads.
  - U6: its custom pads read `padstack_invalid` (also on the input).
- **Via-in-pad:** 145 of the 225 vias sit inside a same-net solder-paste opening. This KiCad 9 file cannot declare via protection, so the fab drawing must specify IPC-4761 Type VII (filled and capped) vias. The variant that avoided via-in-pad left 3 nets open.
- **Floors:** `check_complete --authored-from` reads UNSOUND (reported only):
  - **Vias below the authored 0.3 mm minimum:** one at 0.25/0.15 mm. Five more have 0.3 mm pads on 0.15 mm drills; all 219 others are 0.45/0.2 mm.
  - **Minimum hole:** lowered from 0.508 to 0.15 mm. Every via drill is under 0.508; the board's own Default net class via (0.8/0.4) was already under it.
  - **Minimum hole clearance:** lowered from 0.127 to 0.1 mm.
  - **Router disclosure:** "30 feature(s) on 21 net(s) delivered below the requested size … 13 fab-tier escalation(s) to advanced".

## 6. Verifier

Call 1: **VERDICT=PASS**. All three lens files pass. It checked:
- the sha256 matches;
- `check_assembly` buildable;
- 0 floorplan errors;
- nothing off the outline;
- all 9 declared poses exact;
- the antenna keep-out covers the antenna on all four layers, with 0 tracks or vias inside;
- `board_score` blocking 0;
- `check_complete` DONE;
- every net connected;
- `check_drc` 0.

It also reported the floor descent, the via-in-pad count and the footprint-internal KiCad errors listed in §5.

## 7. Timeline (UTC) and where the time went

| time | step |
|---|---|
| 22:04–22:12 | read the skill, board brief and context |
| 22:12–22:16 | intent and fixed poses; first round aborted (antenna moved north) |
| 22:16–22:23 | round with the peg hole: 12 of 12 seeds illegal |
| 22:23–22:26 | diagnosed the anneal problem; wrote `bat1_hole.py` |
| 22:26–22:28 | round 1: 12 of 12 legal |
| 22:28–22:31 | six quick routes; seed 8 clean |
| 22:31–22:41 | made the placement buildable; turns; ledger; `CHOSEN.json` |
| 22:41–22:44 | full route |
| 22:44–22:47 | removed stacked copper → **first DONE** |
| 22:47–23:08 | 11 routing variants; re-ran the winner in `final_route/` |
| 23:09–23:18 | verifier PASS, `grade.py`, KiCad DRC comparison, write-up |

`measure.py`: wall 1:13:12; model 1926 s; tool time 2018 s; waiting on background jobs 448 s; 230 tool calls. About 25 minutes went to tool problems: 12 on the anneal problem, 11 on making the placement buildable, 5 on stacked copper, and the rest on smaller ones.

## 8. Tool gaps

`TOOL_GAPS.md` has all 10 with reproduce commands; inputs are in `repro/`:
1. The anneal blocks the back face under BAT1 because of its one peg hole.
2. `place_simple` and `check_assembly` disagree on part occupancy, and nothing repairs the resulting overlaps.
3. `route.py`'s finalize writes undisclosed stacked copper.
4. `classify_part` does not recognise the DC jack or the slide switch.
5. `check_assembly` ignores `accept_courtyard_overlap`; only `overlap_waivers` works.
6. `list_nets --design-rules` suggests a 0.45 mm via with a 0.508 mm drill.
7. `kicad_drc_compare --baseline` subtracts by position, so footprint-internal findings on moved parts look router-made.
8. `render_placement` tells you to use `--allow-unplaced`, which does not exist.
9. `place_pose rotate` sets an absolute angle while `route_review` means a relative turn.
10. Skill gaps:
    - nothing makes the placement buildable after the judge;
    - the STANDARD-tier plane map cannot be followed when the board has a multi-layer pour;
    - the quick review lists the poured GND as an open net.

Helpers written, each a TOOL_GAPS entry: `helpers/bat1_hole.py` (1), `helpers/fix_courtyards.py` (2), `helpers/dedupe_segments.py` (3).
