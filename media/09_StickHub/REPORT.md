# REPORT: gp14 board 09, StickHub (`/plan-pcb-placement full`)

## 1. Result: NOT DONE

Final board: `wk/gp14/09_StickHub/final.kicad_pcb` (+ `final.kicad_pro`), sha256 `9385042e55dea348799de5adac4130f72b33c09993d398709657e88b2b0bd1b2`.

| DONE condition (full mode) | measured | met |
|---|---|---|
| `board_score` blocking 0 | **1** | no |
| unrouted 0 | 0 | yes |
| broken 0 | **1** (`/U7D-`: pad U1.37 is off the net) | no |
| `check_complete` DONE | **INCOMPLETE** (blocking 1; `weird_copper` exit 1) | no |
| DRC (`check_drc --baseline --clearance-margin 0.1`) | 0 violations (4 same-net self-crossing warnings) | yes |
| `check_assembly` | buildable (blocking 0) | yes |
| `check_floorplan --intent intent.json` | 0 errors; 3 warnings (decap_ungraded C19, C20, C38, all graded as warnings) | yes |
| pad, graphic or keep-out copper off the outline | none | yes |
| mechanical facts (9 declared poses) | 9 of 9 exact | yes |

- **`blocking_by`:** unrouted 0, broken 1, drc 0, undersized 0, floorplan 0, assembly 0, drc_via_in_paste 0.
- **Quality:** vias 132, copper_mm 773.42, segments 1147 (F.Cu 367 mm, B.Cu 406 mm).
- **UNEXAMINED (no spec declared):** impedance, length, net_widths.
- **`grade.py --mode full`:** `{"done": false, "blocking": 1, "unrouted": 0, "broken": 1, "drc": 0, "vias": 132, "copper_mm": 773.42, "segments": 1147, "check_complete": "INCOMPLETE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`

## 2. Remaining blockers, with measurements

1. **`/U7D-` (net 31) is broken.**
   - It is in two pieces 8.58 mm apart (`converge.py where`):
     - J8.2 (148.15, 90.25) and D13.2, joined on F.Cu;
     - U1.37 (145.91, 98.53) on B.Cu, running to a via at (145.45, 99.25) that no F.Cu copper reaches (`check_weird`: dangling via).
   - Copper walling it in:
     - at the J8 end: /LED1 and /LED2 on B.Cu, 0.32 to 0.99 mm away;
     - at the U1 end: +3.3V on F.Cu at 0.24 mm, /U6D- on F.Cu at 0.43 mm, /U7D+ on B.Cu at 0.48 mm.
   - `check_reachability --pad U1.37 --track 0.127` reads CAGED on the routed board but PASSABLE (+273 µm) on the unrouted placement. So this is congestion, not geometry (see TOOL_GAPS #5).
2. **Two `check_weird` narrow-pad-joints.** These are not counted in `blocking`, but they keep `check_complete`'s weird-copper check failing:
   - +3.3V at R3.1 (145.90, 103.25, B.Cu);
   - Net-(D20-1) at D20.GA (142.85, 82.70, F.Cu).
   - Each joins its pad through copper narrower than the 0.127 mm floor.

## 3. Which stop rule fired

**§5 rule 3, "If DONE will not come":** three (here four) consecutive different approaches failed to lower unrouted + broken.

After approach B reached blocking 1, each of these was measured with `board_score` and none went below it:
- **C:** `--ripped-route-avoidance-cost 3 --track-proximity-cost 2`. Best of 3 passes: 2.
- **Scoped lap:** `--nets /U7D- GND`, ripping the named blocker. Result: 2.
- **D:** fab-floor 0.1/0.1 track and clearance. Result: 5, including 3 DRC.
- **E:** GND tap width 0.2. Result: 1, a tie.

The ledger is closed with `--final --stop-condition 3`. The placement rounds had already stopped at `--rounds 3`, because no round's best fast route was clean.

Two rungs were left untried:
- a placement fix for the /U7 pair: its ESD diode D14 sits 5.61 mm from J8's pin, and U1's USB7 pins face away from J8;
- a hand join staged with `check_join.py`.

## 4. Inputs, groups and judgement calls

- **Mechanical poses:**
  - The 9 `mechanical.json` poses (H1, J1, J2–J8) were set and locked in `fixed.kicad_pcb` with `place_pose`.
  - **C38 is my own call.** It is a 330 µF board-edge electrolytic whose can is drawn 11.5 mm beyond its pads.
  - I locked it at (150.0, 81.3), rotation 180, on B.Cu. Its pads sit at the 4.0 mm north-edge notch (148–152 × 80–81, exactly its pad span), with the can off the north edge.
- **EMC rows:** none were given, and I invented no limits. `emc_roles` named only Y1.
- **Datasheets:** none fetched. The pin functions were enough to identify every part:
  - U1: XR22417 USB hub;
  - U2: SLG5NT1487V load switch, D = VIN, S = +5V;
  - Y1: 12 MHz crystal, with no load caps on the board.
- **Intent:**
  - Everything is graded against the given `intent.json`.
  - Rounds 2 and 3 were placed with my own **`intent_r2.json`**, written beside it:
    - Y1's crystal claim tightened from 8.1 mm to 3.5 mm and made error-graded;
    - new claims: C28 at U2's CAP pin (pin 7, 1.0 mm) and C1 at U1 pin 8 (VCC5, 1.2 mm).
  - These answer round 1's review: on the best seed, Y1 was 14.8 mm from U1's crystal pins, Net-(U2-CAP) had no copper, and U1 pin 8 had no cap within 1.77 mm.
  - The final board comes from round 1, so it was placed with `intent.json`. It passes both intents with 0 errors.
- **Groups (6):**
  - **upstream:** J1, D22, D23.
  - **power:** U2, C21, C28, D24, D25, JP1, J9, C36, C37.
  - **core:** U1, its 13 decaps, R1/R2/C2 (VBUS_SENSE divider), R3–R5, R6, Y1.
  - **ports_east:** J2–J5, D1–D8, C14–C17, and 22 µF caps C22–C27 and C29.
  - **ports_west:** J6–J8, D9–D14, C18–C20, C30–C35.
  - **leds:** D15–D21 and R7–R13.
  - `check_groups` warned that the port VBUS and bulk caps are exempt from the decap rule. That is intended; the intent's decap limits still apply to them.
- **Judging chain** (the same for every seed): `route_planes` GND on F.Cu and B.Cu, then `route_diff --quick 2`, then `route.py --quick 2` (0.15/0.15, via 0.5/0.25, `--layer-costs 1 1`). I tried the QFN fanout step on the LQFP-48 first; it made seed 0 worse (25 → 30 blocking), so I left it out.
- **CHOSEN.json:** round 1, seed 8, clustered, `place_args: []`, plus 4 `place_pose` moves made after placement (Y1, C12, C1, C18). These took the given intent from 2 errors to 0.

| round | inputs | fast-route blocking of the 6 judged seeds | review finding → change |
|---|---|---|---|
| r1 | groups + `intent.json` | s8 **21**, s0 25, s5 50, s6 61, s3 74, s7 81 | Y1 far from U1; Net-(U2-CAP) with no copper; U1 pin 8 cap at 2.23 mm → `intent_r2` claims |
| r2 | groups + `intent_r2` | s6 23, s11 38, s2 39, s4 39, s3 73, s8 81 | Y1 fixed; LED pins boxed in at U1; decap limits still broken → raise the limit weights |
| r3 | + `--decap-limit-weight 30 --claim-limit-weight 30` | s5 34, s2 43, s1 48, s3 66, s6 67, s11 101 | worse |

Kept: round 1, seed 8. The spread between seeds (21 to 81) dwarfed every input change.

| route chain | sizes | `board_score` blocking |
|---|---|---|
| `final_route_old1` | 0.15/0.15, via 0.5/0.25, grid 0.1 | 13, then 11, then 12 |
| A | 0.127/0.127, via 0.45/0.25 | 5 |
| B | A + grid 0.05 | 1 (+3.3V had no copper), then 1, then 2 |
| C | B + retry costs | 6, 2, 2 |
| scoped lap | B's 2nd pass, `--nets /U7D- GND` | 2 |
| D | 0.1/0.1 | 6, 5, 5 (3 DRC) |
| E | B + GND tap width 0.2 | 2, **1**, 1 |

The shipped board is chain E, re-run fresh in `final_route/`. Its manifest is `redo_commands.sh` (4 commands) and its plan is `StickHub_plan.sh`, which `route_plan_check` passed 17/17.

**I broke the letter of the keep-best rule.** B's first pass scores better by the skill's tie-break (1 blocking, 117 vias). But its one "unrouted" net is the entire +3.3V rail: 17 pads with no copper. I shipped the board with one stranded pad instead (TOOL_GAPS #4).

## 5. Floors (below the board's authored rules; disclosed, not gating)

`check_complete --authored-from` returns **UNSOUND**. Against the board's authored values:

| rule | authored | on the board |
|---|---|---|
| track width | 0.15 | 0.127 |
| via diameter | 0.5 | 0.25 |
| via annular ring | 0.1 | 0.05 |
| hole diameter | 0.25 | 0.15 |
| Default class clearance | 0.15 | 0.127 |

- These come from `route.py`'s automatic `--escalation fab` descents, written back to the project file.
- Vias on the board: 124 at 0.45/0.25, 2 at 0.40/0.25, 2 at 0.30/0.20, and 4 at 0.25/0.15 (JLC "advanced" tier).
- The JLC fab floor of 0.1 mm is not crossed.
- No impedance pass: the board has KiCad's default stackup, and 90 Ω is not achievable at these pin pitches.

## 6. Verifier verdicts

- **`verdict_1.txt`: VERDICT=FAIL.**
  - Connectivity lens: FAIL, `/U7D-` broken at U1.37.
  - Spec lens: FAIL, `check_complete` INCOMPLETE.
  - DRC lens: PASS.
- It also confirmed:
  - 9 of 9 mechanical poses exact;
  - `check_assembly` buildable;
  - `check_floorplan` 0 errors;
  - the two narrow-pad-joints;
  - the authored floors listed above.
- Reported for information only (none of these is a declared spec):
  - P/N length differences up to 21.18 mm (/U3D);
  - 86.3 mm of diff-pair copper crossing plane voids.
- There was no second verifier call: the stop rule had already fired.

## 7. Timeline and where the time went

Wall time from FIRST_CMD (21:53:21Z) to the closed ledger (22:49:32Z) was **56 min**. `measure.txt` breaks it down as 1420 s of model time, 1751 s of tool time and 208 s waiting on jobs, over 176 tool calls and 1 subagent.

| UTC | what happened |
|---|---|
| 21:53–22:00 | read the README and skill files; board brief and context; fixed board, C38 call, groups |
| 22:00–22:05 | round 1 placement (about 12 s per seed); fanout A/B test; 6 judging routes |
| 22:05–22:20 | round 1 review; rounds 2 and 3 placed and judged |
| 22:20–22:26 | four `place_pose` fixes; routing plan and plan check |
| 22:26–22:45 | full routes: first plan, then approaches A–E; about 10 min lost to TOOL_GAPS #3 |
| 22:45–22:50 | fresh `final_route`, verifier (3.4 min), `grade.py`, `measure.py`, ledger close |

Most of the tool time went to the 29 `route.py` runs, at about 30–90 s each.

## 8. Tool gaps

Full detail, repro commands and issue searches are in `TOOL_GAPS.md` (9 entries).

1. `route.py`'s GND plane repair ripped the routed +3.3V rail and wrote the board with no +3.3V copper. Closest issues: #600 and #1156, both closed.
2. `place_simple` left decap limits broken while reporting seeds legal; it also placed the crystal and the ESD diodes far from where they belong.
3. `converge.py record` refused a full-route row that followed `quick_score` rows, reading it as a "false improvement".
4. `board_score`'s blocking count ties a 17-pad rail with no copper against one stranded pad, and the skill's tie-break then prefers the board without the rail.
5. The skill's "CAGED is geometry" rule does not say which board to measure. On a routed board, `check_reachability` reports congestion as CAGED.
6. Automatic clearance descents lower the Default class for the whole chain, even under `--clearance-ceiling` (the tool does say so).
7. The routing skill's fanout test selects the LQFP-48, but fanout measured worse on this board.
8. `board_context` prints about 650 pin-order verdicts computed from staging poses on an unplaced pile.
9. No helper scripts were written; the entry lists the inline measurements I had to make.

Tools that reported "fine" when it was not:
- `place_simple`: `illegal: []` while decap limits were broken;
- `route.py`: `pad_pairs_open` listed one net while +3.3V had no copper;
- `check_reachability`: CAGED on a routed board for a congestion problem.
