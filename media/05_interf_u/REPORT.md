# REPORT -- gp14 board 05: interf_u (`/plan-pcb-placement full`)

**DONE.** Final board `wk/gp14/05_interf_u/final.kicad_pcb` (+ `final.kicad_pro`), sha256 `3401266d8d3fcb044b301df21a0e7147f508589d26e038d04fba027f0d34644c`, verifier **PASS** (verdict_1).

## 1. Result

| DONE condition (full mode) | measured | source |
|---|---|---|
| `board_score` blocking | **0** | `final.score.json`, `verify_1_score.json` |
| unrouted | 0 | board_score |
| broken | 0 | board_score |
| `check_complete` | **DONE**, with `intent_r3.json` and with the given `intent.json` | my own run + verifier |
| `check_complete --authored-from interf_u.kicad_pcb` | DONE, no relaxed floor | verifier |
| `check_connected` | all 109 routed nets connected; KiCad refill cross-check agrees | `checks/connected.txt`, verifier |
| `check_drc --baseline --clearance-margin 0.1` | 0 (also 0 unfiltered, 0 with `--check-pad-edge`) | `checks/drc*.txt`, verifier |
| KiCad DRC (`kicad_drc_compare`, kicad-cli 10.0.7) | 0 copper violations, consistent with check_drc | `checks/kicad_drc_compare.txt` |
| `check_assembly` | buildable (blocking 0, advisory 0) | verifier |
| `check_floorplan` | 0 errors, 1 warning, with both intents | verifier |
| mechanical facts | BUS1 (131.445, 138.43, 0°) and P1 (182.1, 72.4, 90°), exact | verifier |

`blocking_by`: unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, drc_via_in_paste 0. Impedance, length and net_widths are ungraded (unexamined, not passed); the board declares none of them.

**Quality:** 157 vias, 4630.48 mm of copper, 1017 segments.

`grade.py --mode full` gives the same result with `intent_r3.json` and with the given `intent.json`: done, blocking 0, unrouted 0, broken 0, drc 0, 157 vias, 4630.48 mm, 1017 segments, check_complete DONE (also with `--authored-from`), buildable, 0 floorplan errors. The outputs are `grade_final.json`, `grade_final_intent_r3.json` and `grade_final_intent_given.json`.

Things that do not gate, but are worth knowing:
- **One floorplan warning.** X1 pad 1 is 14.86 mm from U9 pad L1. The intent's crystal row is a derived default of 8.1 mm (the corpus 75th percentile) and is graded as a warning. X1 is a horizontal HC18 can, 13 x 17 mm.
- **7 silkscreen items in KiCad's DRC.** 5 are label overlaps around R1, R2, R3, RR1/JP1 and U5; 2 are reference labels clipped by pads (C2 by X1 pad 1, RR1 by JP1 pad 8). They are cosmetic, and the skill does not grade silkscreen.
- **13 narrow GND pour necks.** `kicad_drc_compare` stages a minimum copper width of 0.2 mm (the project's minimum track) and finds 13 places where the GND pour is narrower. The board's own rule is 0, so KiCad's real DRC does not flag them. Re-pouring at 0.2 mm minimum thickness removed them but broke a net (arm P), so they stay. See TOOL_GAPS #5.
- **VCC width.** VCC was routed at 0.5 mm (the Power netclass width), but 59.7 mm of its 394.6 mm is narrower, down to 0.2 mm, the board's minimum track width. The router reports this in its `Design rules [...]` line. No width spec is declared, so it is ungraded.

## 2. Inputs, groups and judgement calls

The board is an 8-bit ISA I/O card: 2 copper layers, 24 parts, all through-hole on the front, 111 routable nets.
- BUS1 is the ISA edge fingers on the bottom tab; P1 is a DB25 female at the east (bracket) edge. Both are seated at their declared poses from `mechanical.json` (`fixed_poses[]`), so no lock was needed.
- U9 is an XC4003A FPGA (PGA120, 2.54 mm pitch, through-hole) and U5 a 128K x 8 SRAM (628128).
- U8 is an EP600 PLD. U1 is a 74LS245 data transceiver, U2 a 74LS688 address comparator, U3 a 74LS541 buffer.
- JP1 is a 2x8 address-jumper header with RR1, a 9 x 1K pull-up resistor pack.
- X1 is an 8 MHz crystal with C2, C3, R1 (100K) and R2 (1K).
- D1/D2 are LEDs with R4/R5. C1, C4, C5 and C6 are four 47 µF axial bulk caps. R3 is the pull-up on U5's CS2.

I identified every part from its value and its nets. No datasheet lookup was needed, so no `datasheets/` folder was created.

**EMC limits:** none were given, and I invented none. `board_context` found one crystal (X1) and no switching nodes, so it proposes no keep-away rule. The board is all digital, so the router got no keep-away rule either.

**Intent files:**
- Round 1 used the given `intent.json`: a decap rule of at most 34.08 mm from each VCC pin to a cap, plus derived-default crystal rows.
- `intent_r2.json` and `intent_r3.json` sit beside it. Each is the given intent plus two error-graded proximity claims that tie a bulk cap to each VCC side of U9: C4 pad 1 to U9 pin G12, and C1 pad 1 to U9 pin C3. The limit was 10 mm in round 2 and 20 mm in round 3.
- Why they exist: round 1's best seed broke the given intent's decap rule on three U9 VCC pins (TOOL_GAPS #1).
- The final board passes both `intent_r3.json` and the given `intent.json`.

**Groups.** `groups.json` was used in rounds 1 and 2, `groups_r3.json` in round 3. Each round's exact copy is in `r<N>/groups.json`.

| group | parts | why / judgement |
|---|---|---|
| isa_if | BUS1 (fixed), U1, U3, U8, C6 | The bus interface: the data transceiver and the address/strobe buffer straight off the fingers. U8 decodes the buffered strobes, drives the transceiver's direction and enable lines and the FPGA config pins, so I kept it with the bus side, near the core. C6 is the bulk cap at the power entry. |
| addr_decode | U2 (plus JP1 and RR1 in rounds 1-2) | The 74LS688 compares address lines A4-A11 and AEN against the jumper-set reference lines. |
| addr_jumpers (round 3) | JP1, RR1 | Split away from U2 in round 3: kept near addr_decode and apart from isa_if, so the reference lines stop crossing the address fingers' fan-out (see round 2 below). |
| core | U9, X1, C2, C3, R1, R2, C1, C4 | The FPGA with its crystal oscillator; R2 is the series resistor from the 8MH-OUT pin. C1 and C4 are bulk caps on U9's VCC. |
| memory | U5, R3, C5 | The SRAM (30 nets to U9) with its CS2 pull-up and a bulk cap; near the core. |
| lpt | P1 (fixed) | The DB25: 18 of its nets go straight to U9. It is a fixed-only group so the core can be placed near it. |
| leds | D1, R4, D2, R5 | Given an east-edge hint (my judgement): east is the bracket edge where P1 mates, so the LEDs can be seen. The hint was not met in round 1. On the shipped board (round 3, seed 7) the LEDs sit at the east edge beside P1. |

`check_groups` reported 0 errors and 0 warnings in every round.

## 3. Placement rounds

Every round ran `place_simple --round`: 6 scattered and 6 clustered seeds, with the 6 cheapest judged by a fast route. No extra arguments were passed (`place_args: []`).

The judging chain was the same for every candidate, at `--quick 2`:
1. `route_planes.py --nets GND --plane-layers B.Cu` (the board's own pour layer).
2. `route.py --nets '*' --quick 2 --no-bga-zones --layer-costs 1.0 1.0 --direction-preference-cost 4000 --turn-cost 2000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.5 --power-nets VCC GND --power-nets-widths 0.5 0.5`. These are the routing skill's Step 8 flags for 2-layer through-hole bus boards. There is no fanout step because the PGA is through-hole at 2.54 mm.

I chose to pour GND first for judging after testing both orders on round 1 seed 8. Pour-first gave blocking 1 and 107 vias. Pour-last gave blocking 4, because at `--quick 2` there is no plane finalize to connect a late GND pour.

| round | input change | judged seeds (blocking / vias) | best | what the route showed |
|---|---|---|---|---|
| 1 | given intent, groups.json | s8 1/107, s7 3/112, s3 3/159, s4 9/170, s9 11/160, s5 12/182 | s8 | /PC-A9 open at its ISA finger, boxed in where the address fingers fan out. s8 also breaks the decap rule on U9 pins D11, G12 and L10 (39-41 mm against 34.08). That blocks DONE, but the judge does not see it. |
| 2 | intent_r2: C4 to U9.G12 and C1 to U9.C3 at 10 mm | s4 1/115, s10 2/147, s1 3/128, s2 4/132, s7 5/97, s6 5/119 | s4 | The decap rule is now met, but C4 is 17.3 mm from G12, against my own 10 mm claim. /PC-A3 is open at its finger. `route_review` puts the congestion in the address-finger fan-out, with JP1/RR1 at the left end above fingers A0-A2, so the reference lines shared that corridor. |
| 3 | groups_r3 (JP1 and RR1 split out, kept apart from the bus group); intent_r3 (claims at 20 mm) | **s0 0/126**, s11 1/135, s7 2/120, s5 2/143, s9 3/142, s4 12/160 | s0 | The first clean fast route, so placement rounds stopped there (skill §3.6). JP1/RR1 now sit west of U2, away from the fingers. |

Counting the decap floorplan errors as blocking, round 2's s4 beat round 1's s8 (1 + 0 against 1 + 3), and round 3's s0 beat both.

**After place_simple (round 3, seed 0):** C1 pad 1 was 20.83 mm from U9 pin C3, just past my own 20 mm claim. One `place_pose` call moved C1 to (131.0, 61.3) and R2 to (140.36, 65.0); R2 moved 0.62 mm so the C1/R2 courtyards stay buildable. The fast route of the result (`r3/s0_after`) was still clean: blocking 0, 122 vias.

## 4. Routing (full mode) and optimisation

I followed `/plan-pcb-routing` by hand:
- **Step 0 gate:** buildable.
- **No fanout:** the PGA is through-hole.
- **Nothing special to route:** no differential pairs and no impedance nets, so the default stackup does not matter.
- **Low speed:** 8 MHz ISA, LPT and SRAM, so no GND return vias and no stitching.
- **Planes:** GND poured on B.Cu, the board's own pour layer. VCC is a 0.5 mm power trace, the norm for a standard 2-layer board.
- **Signals:** routed with the skill's Step 8 flags for through-hole bus boards.

The first full routes, both on `r3/s0_after` and both blocking 0, compared the two pour orders:
- **Arm A** poured GND first, then ran `route.py '*'` plus 2 iterations. It ended with 191 vias and 4518 mm. Its plane finalize also stepped the clearance down to 0.1588 mm, below the board's 0.254 mm.
- **Arm B** used the Step 8 dense 2-layer order: `route.py '*' '!GND'`, pour GND last, then `route.py '*'` plus one iteration. It ended with 160 vias and 4358 mm, and stayed at the board's own minimums. **This was the first DONE board, at about 22:12Z.**

**Optimisation after DONE (fewer vias first).** Each arm changed one thing from arm B's chain:

| arm | change | result |
|---|---|---|
| C | via cost 300 | 123 vias, but the default fab escalation dropped clearance and track to 0.127 mm and vias to 0.45/0.2 mm, below the board's own minimums. Rejected. |
| D | direction preference 2000 | 140 vias, but clearance stepped down to 0.2223 mm. Rejected. |
| E | via cost 300, escalation bounded at the board's minimums | 124 vias, but /PC-A10 broken. Three repair passes all failed: ripping the hinted pair, a scoped finer grid, ripping the hinted three nets. Rejected. |
| G | via cost 220 | DONE at 160 vias: no gain. |
| K, L | via cost 250 and 200 | nets left open. |
| H | via cost 300, rip-up depth 5 | 2 broken. |
| **I** | round 3 seed 7 placement (judged, floorplan clean, no post-placement move), arm B's chain with escalation bounded at the board's minimums | **DONE, 157 vias, 4630 mm. Best by vias.** |
| J, M, N | seed 7 at via cost 300, 250 and 200 | nets left open. |
| O | arm I's chain with GND kept in the first route step | 2 broken, 182 vias. |
| P | arm I's chain with the GND pour at 0.2 mm minimum thickness | 1 broken. |

The kept chain is arm I. I re-ran it from scratch in `final_route/` with `REDO_RUNDIR`, `REDO_MANIFEST` and `KICAD_ROUTE_TRACE=1`, and it reproduced arm I exactly (157 vias, 4630.48 mm). The commands are recorded in `final_route/redo_commands.sh`; the plan is `final_route/interf_u_plan.sh` and `interf_u_plan.json`. The chain:
1. `copy_board r3/s7 -> placed`
2. `route.py placed s1_sig --nets '*' '!GND' <F>`
3. `route_planes.py s1_sig s2_pour --nets GND --plane-layers B.Cu --clearance-ceiling 0.254`
4. `route.py s2_pour s3_route --nets '*' <F>`
5. `route.py s3_route s4_iter1 --nets '*' <F>`
6. `copy_board s4_iter1 -> final.kicad_pcb`

where `<F>` is `--no-bga-zones --layer-costs 1.0 1.0 --turn-cost 2000 --direction-preference-cost 4000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.6 --power-nets VCC GND --power-nets-widths 0.5 0.5 --clearance-ceiling 0.254 --escalation board`.

**route_plan_check refused this plan on rule R14**, even though it is the routing skill's own Step 8 order. R14 sees GND excluded in step 2 and calls it unclaimed, but the pour and both closing `'*'` steps claim it. The only variant R14 accepts is arm O, which routes worse. I ran the refused plan (TOOL_GAPS #2). All its other rules pass.

**CHOSEN.json:** `{"round": 3, "seed": 7, "start": "clustered", "after": [], "place_args": []}`. The judge kept round 3 seed 0, and its full route is DONE at 160 vias. I shipped seed 7 because its full route is DONE at 157. Fewer vias decides once both are DONE, but the margin is only 3 vias. The seed-0 lineage stays in the ledger as the first DONE board.

## 5. Stop rule

**Stop condition 1: DONE, verified PASS.** After DONE, via optimisation plateaued over 12 routing arms: no DONE board came in under 157 vias at the board's own minimums. Lower via counts (123-137) came only with an open net or a drop below the board's own minimums. No blocker remains, so there is nothing to list.

## 6. Floors

- `check_complete --authored-from interf_u.kicad_pcb`: DONE, no relaxed floors.
- **Final chain sizes:**
  - Clearance: 0.254 mm in every step (the Default and Power class value).
  - Track: 0.2 mm, the board's minimum track width.
  - Vias: 0.9 mm diameter (the board's minimum) with a 0.6 mm drill (the netclass drill).
  - No "FAB FLOOR RELAXED" line appears anywhere in the final chain.
- **Escalation:** bounded at the board's own minimums, so no step went below them. The only narrowing reported is VCC under its requested 0.5 mm: 15% of its length, down to 0.2 mm.
- **Project values the chain wrote:**
  - Minimum copper-to-edge clearance went from 0 to 0.2 mm. The ISA fingers sit 0.254 mm from the tab edge, so they still pass.
  - Minimum via drill went from undeclared to 0.6 mm. The GND pour step wrote it, although it places no vias (TOOL_GAPS #3).
- **GND zone settings:** `route_planes` replaced the original zone's settings. Clearance went 0.5 → 0.254 mm and minimum thickness 0.2 → 0.1 mm, and pads now connect solidly instead of through thermal reliefs. The skill says to leave the connection style alone, so I did not override it (TOOL_GAPS #5).
- **Judging routes:** these were never shipped. They ran at the default fab escalation with a 0.5 mm via drill.

## 7. Timeline (UTC, 2026-10-20) and where the time went

| time | step |
|---|---|
| 21:44:43 | FIRST_CMD. Read the skill, its references and the routing skill; ran board_brief, board_context and the design-rule listing. |
| 21:47 | groups.json and check_groups; round 1 placement (12 seeds in about 20 s). |
| 21:49 | Chose the judging chain on round 1 seed 8 (pour-first against pour-last, about 35 s each). |
| 21:50-21:52 | Round 1 judging routes (6 seeds, 2 at a time). |
| 21:52-22:01 | Ledger, route_review, renders. About 10 min was lost to a wait loop of mine that never matched (my error, not a tool's). |
| 22:02-22:04 | Round 2 intent, placement, judging. |
| 22:05-22:07 | Round 3 groups and intent, placement, judging: first clean fast route. |
| 22:07-22:10 | C1/R2 nudge (10 candidate poses checked) and a fast-route recheck. |
| 22:10-22:12 | Full-route arms A and B; **first DONE at about 22:12**. |
| 22:13-22:38 | Optimisation arms C to N. |
| 22:39-22:44 | plan.sh, the R14 refusal, arm O, the `final_route/` chain. |
| 22:44-22:46 | My own checks, kicad_drc_compare, arm P. |
| about 22:46-22:50 | Verifier (234 s). |
| 22:50-22:52 | grade.py, measure.py, ledger closed, DONE marker; then TOOL_GAPS and this report. |

`measure.py --self --evidence` (in `measure.txt`, taken at about 22:50):
- Wall time 3942 s: model 1141 s, waiting on jobs 709 s, other tool time 2093 s.
- 169 tool calls, 1 subagent.

Placement itself was cheap: about 20 s per round of 12 seeds. A judging route took about 35 s and a full chain 1-2 min. The time went to reading the skills, to the optimisation sweep after DONE (about 25 min), and to my own waiting mistake (about 10 min).

Small notes:
- One STATE.md line carries an early "22:50Z" timestamp. It was written at about 22:48.
- Trial pose boards for the C1 nudge were written to the session scratchpad, outside my folder, and then deleted.
- All five input sha256 values match README.md at the end. No helper scripts were written (no `helpers/` folder), and no datasheet folder was created.

## 8. Tool gaps (detail in TOOL_GAPS.md)

1. The seed judge (`quick_score` and `judge.json`) and §3.6's "keep the best" ignore error-graded floorplan rules. Round 1's best seed could never be DONE (3 decap-rule errors), which cost a review round.
2. `route_plan_check` rule R14 refuses the routing skill's own Step 8 pour-last chain. The variant it accepts routes worse.
3. `route_planes` places no vias but writes a 0.6 mm via-drill minimum. `route.py` then reports a false "FAB FLOOR RELAXED 0.6 -> 0.5" for vias at the 0.5 mm drill that `list_nets --design-rules` suggests.
4. `place_pose` reports `legal: false` for every pose on this board, because BUS1's 62 edge fingers are graded against a 0.55 mm edge clearance. It also writes a courtyard-blocking (NOT BUILDABLE) pose with exit 0.
5. `route_planes` replaces the existing GND zone's clearance, minimum thickness and thermal style and does not say which settings changed.
6. Intent rows spell their free-text reason `why` in one place and `note` in another, and each refuses the other's spelling.

Apart from #3's false relaxation message and #4's `legal: false` noise, no tool reported "fine" about something that was not. Every checker that decides DONE agreed with KiCad's own DRC.

## 9. Verifier verdicts

One verifier, one call: **verdict_1 = VERDICT=PASS** (`verdict_1.txt`). The lenses connectivity, drc and spec all PASS (`verdict_1_connectivity.txt`, `verdict_1_drc.txt`, `verdict_1_spec.txt`).

The verifier re-measured the sha256, check_assembly, check_floorplan with both intents, the render, the mechanical poses, board_score, check_complete (including `--authored-from`), check_connected and check_drc. It also ran KiCad's own DRC: 0 copper errors, 0 unconnected items, 7 silkscreen-only items. It deleted a `final.kicad_prl` file that the kicad-cli run created; the board's sha256 is unchanged.

## 10. Files

All in `wk/gp14/05_interf_u/`:
- **Final board:** `final.kicad_pcb`, `final.kicad_pro`, `FINAL.sha256`, `DONE`, `CHOSEN.json`
- **Placement inputs:** `groups.json`, `groups_r3.json`, `intent_r2.json`, `intent_r3.json`
- **Rounds:** `r1/` to `r3/`, each with its fixed board, groups, intent, seed files, `judge.json`, judging-route folders and fast-routed boards
- **Routing:** `final_route/` (`redo_commands.sh`, plan.sh, plan.json, route traces) and `arms/` (every routing arm above)
- **Ledger:** `ledger.jsonl`, closed with `--final` at stop condition 1
- **Verification:** `verdict_1*.txt`, `verify_1_*`, `grade_final*.json`, `grade_intent_*.txt`, `measure.txt`, `checks/`
- **Tool gaps:** `TOOL_GAPS.md`, and `repro/` with the inputs each reproduction needs
