# REPORT: gp14 board 02 sonde_xilinx (`/plan-pcb-placement full`)

## Result: DONE

`wk/gp14/02_sonde_xilinx/final.kicad_pcb` with `final.kicad_pcb`'s sibling `final.kicad_pro`. sha256 `e7ff67549ded28985a6cf72ccc5686511437d54c0012327a126f0f86734c7f53` (also in `FINAL.sha256` and `DONE`).

| DONE condition (full mode) | Measured | Tool |
|---|---|---|
| board_score blocking | **0** | `board_score --intent intent_seat.json --min-track-width 0.2032 --min-via-diameter 0.889 --min-via-drill 0.508 --baseline sonde_xilinx.kicad_pcb` |
| unrouted / broken | **0 / 0** | board_score |
| check_complete | **DONE** with the same spec flags; with `--authored-from` the input it is also DONE and lists no floor | check_complete.py |
| check_connected | all nets fully connected | check_connected.py |
| check_drc (`--baseline`, margin 0.1 and 0) | 0 violations | check_drc.py |
| KiCad DRC (kicad-cli, zones refilled) | 0 copper violations, 0 unconnected; only silkscreen and library warnings | kicad_drc_compare: kicad=0, check_drc=0, CONSISTENT |
| check_assembly | buildable (blocking 0) | `check_assembly --intent --baseline` |
| check_floorplan | 0 errors, 1 warning (U2 pins_to_edge), against both `intent_seat.json` and the given `intent.json` | `--allow-routed` |
| copper off the outline | none: pad_copper_gating, graphic_copper and keepout_copper are all empty | render_placement `--json-out` |
| independent grade | `{"done": true, "blocking": 0, "vias": 0, "copper_mm": 516.67, "segments": 119, "check_complete": "DONE", "check_complete_authored": "DONE", "floorplan_errors": 0}` | scripts/grade.py `--mode full` (output in `grade/`) |
| verifier | PASS (verdict_1.txt and its 3 lens files) | one fresh subagent, 1 call |

- **`blocking_by`:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, undersized 0, unrouted 0.
- **UNEXAMINED (ungraded):** impedance, length and net_widths. The board declares only one Default class and no impedance, length or width spec.
- **Quality:** 0 vias, 516.67 mm of copper, 119 segments. The first DONE board had 16 vias, 539.07 mm and 144 segments.

**Advisories (none gate DONE):**
- **Unfilled pour.** The shipped file has zone outlines but no `filled_polygon`, which is the repo default. KiCad DRC without a refill reports 18 phantom GND opens; with a refill it reports 0. Refill the zones in KiCad before plotting Gerbers. `py_tools/fill_for_delivery.py` exists for this, but neither skill mentions it and I did not run it.
- **Thin necks in the pour.** If min_connection is staged at 0.2032 (the board itself declares 0, so the check is off), KiCad finds two necks in the B.Cu GND pour, 0.1654 mm and 0.1111 mm.
- **Pour settings changed.** The routing chain's `route_planes` rebuilt the designer's GND pour with its own defaults (TOOL_GAPS #6). It is still GND on B.Cu.
- **Silkscreen.** KiCad reports 8 silk_overlap, 3 silk_over_copper and 2 silk_edge_clearance items.

## Inputs and the one intent change

**The board.** 25 parts, 43 nets, 2 layers, almost all through-hole. The outline is 80.4 x 43.18 mm and was not changed. It is a Xilinx parallel-port download cable:
- DB25 J1 → 100R series resistors R6-R10 → 74LS125 U1, which buffers TDI/TCK/TMS and drives the open-drain PROG/DONE line through U1A with the 5k1 pull-up R2.
- U1 → 100R R11-R14 with 100 pF C2-C5 → DB9 J2 on B.Cu and the 1x6 header P1.
- U2A reads DONE back to J1.13 through R4.
- Power comes from the target through D2 (BAT46). C1 decouples VCC, R5 bleeds it, and D1+R1 feed VCC-sense to J1.15.

**Brief.** J1 on the west edge, J2 on the east edge; position along the edge unknown for both. There is no mechanical.json, no mounting hole and no keep-out.

**EMC rows: none were given.** board_context names no converter, crystal, oscillator or ESD array, and I invented no proximity limit or keep-away rule.

**`intent_seat.json`.** This is the given `intent.json` (left unedited) plus an `overhang_mm` band on each DSUB:

| Part | min (mm) | max (mm) |
|---|---|---|
| J1 | 25.88 | 26.2 |
| J2 | 14.45 | 14.8 |

- **Why it was needed.** Both connectors are edge-mount and straddle the board. Their footprints draw the PCB edge (a Dwgs.User line) 1.99 mm from the pad row.
- **What the given intent does.** With no band the seat aims for "flush". For J1 that cannot be met, because its 54.1 mm flange is wider than the 43.18 mm west edge. `place_simple` then places J1 like any other part: near the north edge, facing north, 2 ERRORs, and still exit 0.
- **How the numbers were measured.** Each part was posed with its pad row 1.99 mm inside the edge, and the band was read as graded (`legacy_occupancy@margin=0.254`):
  - J1: 14.45 mm past the west edge plus 11.43 mm of flange past north and south = 25.88.
  - J2: 14.45.
- **Result.** This is the skill's §3.4 overhang step. Every seed then seated J1 on the west edge and J2 on the east edge, facing out, with pads 0.25 mm inside the outline.

No `--decaps-from` was used, because no placed reference board was available.

## Groups and judgement calls (`groups.json`)

| Group | Role | Refs | Hints | Why |
|---|---|---|---|---|
| pc_port | interface | J1, R6-R10, R4, R1, D1 | near core | the DB25 plus every part whose far pad is a J1 pin |
| core | core | U1, U2, R2, C1 | near pc_port, outputs | the two 74LS125s, the PROG/DONE pull-up, the only VCC decap |
| outputs | interface | R11-R14, C2-C5 | near core, target | output series resistors and 100 pF edge caps on U1's side of each resistor |
| target | interface | J2, P1 | near outputs, power | DB9 and header, wired pin for pin to the same signals |
| power | power | D2, R5 | near target, core | power entry through D2 and the VCC bleed, kept by its entry rather than at an edge |

The judgement calls:
- **Series resistors R6-R10** go with the connector. check_groups lists them as bridges.
- **C2-C5** are output load caps, not decaps, because their nets are U1 outputs, not a rail.
- **D1/R1** go with J1, because their far end is J1.15.
- **Edge and side hints:** no group gets an `edge` hint (the connectors hold their groups) and no group gets a `side`.
- **Datasheets:** no lookup was needed.

`check_groups`: 0 errors, 0 warnings.

## Rounds

There was **one round** (`r1/`): 12 seeds (6 scattered, 6 clustered), all legal, placed in 7 s. The judge picked seeds 11, 10, 7, 8, 1 and 3.

Every judged seed got the same judging chain:
1. `route_planes --nets GND --plane-layers B.Cu`
2. `route.py --nets '*' --power-nets GND VCC /PWR_3,3-5V --power-nets-widths 0.635 x3 --track-width 0.254 --via-size 0.889 --via-drill 0.508 --quick 2`
3. `quick_score`

| Seed | Start | Cost | Blocking | Vias | Copper (mm) | Segments |
|---|---|---|---|---|---|---|
| **11** | clustered | 582.3 | **0** | **3** | 530.02 | 333 |
| 10 | clustered | 598.4 | 0 | 9 | 514.97 | 282 |
| 7 | clustered | 624.3 | 1 | 7 | 547.18 | 398 |
| 8 | clustered | 626.0 | 0 | 10 | 572.13 | 336 |
| 1 | scattered | 626.7 | 0 | 8 | 606.05 | 488 |
| 3 | scattered | 631.1 | 0 | 9 | 573.60 | 442 |

The best fast route was clean, so the rounds stopped there: no review round and no input change. `route_review` on s11 found 0 open nets and 0 turned two-pad parts. `CHOSEN.json` is round 1, seed 11, clustered, `after: []`.

## Routing (§3.7, plan-pcb-routing followed by hand)

**Step 0 gate:** buildable; the baseline score had 25 unrouted and 4 broken.

**The plan** (`final_route/sonde_xilinx_plan.sh`; `route_plan_check` passed all 17 rules):
- **Plane first,** because this is a 2-layer board with light signal content: GND on B.Cu, the board's own board-wide pour.
- **`route.py '*'`** with power nets at 0.635 mm, signals at 0.254 mm and vias at 0.889/0.508 mm, then two Step-2d iteration passes.
- **Signal width.** 0.254 mm is above the authored floor of 0.2032 mm and fits every pin gap on the board (0.92-0.94 mm). The class width of 0.635 mm does not.
- **Steps skipped and why:**
  - No fanout or diff pairs.
  - No impedance or length matching: the stackup is a default-looking 1.51 mm core and nothing needs it.
  - No keep-away: the board is all digital.
  - No GND-via or stitching tail: low-speed board, Step 10 rule 10.

**Progress:**
- **First DONE** (`final_route_old1/`, default `--layer-costs 1.0 3.0`, via cost 75): 16 vias, 539.07 mm, 144 segments.
- **Optimisation:** 25 routing arms on the same placement (`opt/`, all DONE, all recorded as rejected), plus the zero-via recipe on the other 5 judged seeds (none better).
  - `--layer-costs 1.0 1.0` gave 8 vias.
  - `--via-cost 300` gave 2.
  - Layer costs 1.0 1.0 with via cost 600 gave **0 vias at 535.08 mm**.
  - Adding `--grid-step 0.05 --direction-preference-cost 0 --turn-cost 2000` gave **0 vias, 516.67 mm, 119 segments**.
  - The next three arms (turn cost 3000, turn cost 4000, direction preference 4000) were all worse on copper, so I stopped.
- **After the verifier,** one more arm kept the designer's own GND zone instead of running route_planes. It was DONE with 0 vias but 539.94 mm, so it was rejected.

**The shipped chain** (`final_route/`, with REDO_RUNDIR, REDO_MANIFEST and KICAD_ROUTE_TRACE=1 set; `redo_commands.sh` recorded): copy of `placed.kicad_pcb` → step1 (the pour) → step2 (the route) → iter1 → iter2. Both iterations changed nothing. The result is `final.kicad_pcb`.

## Stop rule

**Stop condition 1, DONE.** blocking 0, unrouted 0, broken 0, check_complete DONE, verifier PASS. There is no remaining blocker. The ledger is closed: 46 rows, the last one `--final --stop-condition 1` with the three lens files.

## Floors

Nothing was routed below the authored or fab floors:
- route.py `Design rules`: 0 features narrowed, 0 escalations, smallest clearance used 0.254 mm.
- Track 0.254 mm is at least the 0.2032 mm minimum; vias 0.889/0.508 mm are the board's own minimum.
- `check_complete --authored-from`: DONE, nothing relaxed.

The chain also wrote two values into the project:
- `min_copper_edge_clearance` 0.01 → 0.2 mm (made stricter, by route_planes).
- `min_via_drill` None → 0.635 → 0.508 mm (TOOL_GAPS #4).

## Timeline (UTC) and where the time went

| Time | Step |
|---|---|
| 19:28:44 | FIRST_CMD |
| 19:28-19:31 | read the skill, its references and the routing recipe |
| 19:31-19:33 | board_brief, board_context, design rules; connector-geometry probes; a probe with the given intent showed J1 gets no seat; wrote intent_seat.json and groups.json; check_groups |
| 19:33:37 | round 1 placed (7 s) |
| 19:34:40 | six judging routes and scores done; s11 kept |
| 19:35-19:37 | ledger rows, Step 0 gate, plan and route_plan_check; first DONE at 19:36:57 |
| 19:37-19:47 | 25 routing arms and the 5 other seeds; plateau |
| 19:49:01 | final chain re-run; final.kicad_pcb |
| 19:49-19:53 | verification suite; grade.py at 19:51 |
| 19:53-19:57 | verifier, about 5.6 min (PASS); in parallel, TOOL_GAPS, repro checks and the keep-zone arm |
| 19:58 | ledger closed, DONE marker, measure.py |

measure.py (`measure.txt`, `measure.json`) for this transcript: 29:20 of wall clock. Of that, 1082 s was model time (61%), 636 s tool time and 41 s waiting on background jobs. Compute was small: 7 s of placement, about 30 s of judging routes, about 6 min across all routing arms, and about 1 min for the final chain. The verifier's own 5.6 min is not attributed to this transcript.

## Tool gaps (details and repro commands in `TOOL_GAPS.md`; repro inputs in `repro/`)

1. **place_simple misreports an unseatable edge connector.** With the given intent it places the edge-mount DB25 like any other part, exits 0 with `illegal: []`, and blames "no room along the west edge". The real cause is that a "flush" overhang target cannot be met. (About 15-20 min.)
2. **Route-step writeback flips a placement grade.** The Default clearance drops 0.254 → 0.2223 after a descent, and route_planes pins the edge clearance 0.01 → 0.2. With no part moved, a passing placement becomes 2 `edge_connector` ERRORs. This hit seeds 7 and 1 and is related to #1160. (About 10-15 min.)
3. **Skill gap on via cost.** The routing recipe gives 16 vias on a light 2-layer through-hole board where 0 cost no copper, and the `--quick 2` judge's 3 vias did not predict the full route's 16. Related to #658. (About 10 min.)
4. **Invented floor, misleading warning.** route_planes writes an undeclared `min_via_drill` of 0.635, and route.py then warns about lowering "the original number". (About 5 min.)
5. **check_floorplan can never exit 0 here.** It exits 4 on a 0-error board, permanently, because the emitter withheld budgets when the input was a pile. (About 2 min.)
6. **route_planes overwrites the designer's pour.** It replaces the existing GND pour's settings without listing them: thermal → solid connection, clearance 0.508 → 0.254, min thickness 0.254 → 0.1 (which enables the two thin necks). The skill's Step 1 sends you there. (About 5 min.)

Tools that reported "fine" about something that was not:
- **place_simple** (gap 1): exit 0 and `illegal: []` with J1 off its declared edge.
- **board_score / check_complete:** they do not see the two thin pour necks, which only the staged kicad_drc_compare check reports.

No helper scripts were written; `helpers/` is empty.

## Verifier verdicts

**verdict_1.txt: `VERDICT=PASS`.** Lens files: connectivity PASS, drc PASS, spec PASS.

What it confirmed:
- **Identity:** the sha256 matches, and all four input files are unmodified.
- **Board unchanged where it should be:** outline, netlist and sides are the same as the input.
- **Gates:** check_assembly buildable with no off-outline pads and no mating-keepout parts. check_floorplan 0 errors against both intents. board_score blocking 0 / 0 / 0. check_complete DONE, and DONE with `--authored-from`. check_connected all connected. check_drc 0, also with `--check-pad-edge`.
- **J1:** front side, rotation 270, PCB-edge marker at x = 103.302 against the west edge at 103.3. It mates west, with every pad inside the outline (nearest 0.252 mm from the edge).
- **J2:** back side, rotation 270, marker at x = 183.696 against the east edge at 183.7. It mates east, with every pad inside (nearest 0.254 mm).

Its four advisories, all non-gating, are the ones listed under "Advisories" above: unfilled pour, rebuilt pour settings, the two thin necks, and the silkscreen items.
