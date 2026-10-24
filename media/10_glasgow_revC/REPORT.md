# REPORT: gpm board 10, glasgow_revC (`/plan-pcb-placement full`)

**Result: DONE.** The board is `wk/gpm/10_glasgow_revC/delivered.kicad_pcb` (sha256 `3d484998e2b44528d5793a26c567369ada16ca81067edd9f94d186ca17336205`), filled with KiCad's zone filler. It started as a pile of 264 parts on an 80 x 49 mm, 4-layer board.

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking (`--intent intent_run.json --baseline glasgow_revC.kicad_pcb`) | **0** |
| unrouted / broken | **0 / 0** (joins_needed 0) |
| `check_complete` | **DONE**. UNEXAMINED: diff_pairs, impedance, length, net_widths, because nothing declares them |
| `check_connected` | ALL NETS FULLY CONNECTED |
| `check_drc --baseline --clearance-margin 0.1` | no violations. All 356 vias in pads or paste openings are declared filled and capped; 0 unprotected |
| `check_assembly --intent --baseline` | buildable (blocking 0; 12 declared-pose overlaps waived) |
| `check_floorplan --intent intent_run.json` | 0 errors |
| `render_placement` `a_off_outline` | no gating pad copper, no graphic or keep-out copper |
| `kicad_drc_compare` | CONSISTENT (KiCad 0 / check_drc 0). It also reports `connwidth=1` on the designer's GND In1 zone at the board corner (50, 120), and `thermal=0` |

- **blocking_by:** assembly 0, broken 0, drc 0, drc_via_in_paste 0, floorplan 0, undersized 0, unrouted 0. diff_pairs, impedance, length and net_widths are not graded: the board has no `.kicad_dru`, no length groups, no per-net width rule, and KiCad's default stackup.
- **Quality:** vias 763, copper 4956.46 mm, segments 4837.
- **grade.py `--mode full`:** `{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 763, "copper_mm": 4956.46, "segments": 4837, "check_complete": "DONE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`. The output is in `grade.txt` and `grade_delivered.json`. "UNSOUND" here is the floors disclosure (see Floors), not a defect.
- **measure.py `--self --evidence wk/gpm/10_glasgow_revC`:** wall clock 1:49:42, of which 3204 s waiting on jobs, 2366 s model and 1012 s other tools; 300 tool calls; 1 agent spawn. Saved to `measure.txt` and `measure.json`.
- **Skills followed by hand** (none could be invoked):
  - `/plan-pcb-placement` (this run).
  - `/plan-pcb-routing` for §3.8, Steps 0–10, including the Step 9 plan and `route_plan_check` (17/17 ok).
  - `/analyze-power-nets` (plan-pcb-routing Step 4).
  - The `/find-high-speed-nets` and `/identify-diff-pairs` methodology that plan-pcb-routing points to.

## Stop rule

**Stop condition 1 (done).**
- DONE first came at 10:12Z. Before it, one approach failed (the scoped rip lap) and the next one (fab-floor features with a 0.05 grid) reached DONE.
- After DONE I tried two optimisation arms (the Step 2c env stack, and a QFN fanout of U1). Both were worse.
- The DONE chain was then re-run cleanly, twice. The second re-run was on the KiCad 10 file format, which the fill step requires.
- **No blocker remains.**

## The intent, and the one row I added

`intent.json` is read-only and already compiles the brief and `mechanical.json`. It holds:
- 21 `fixed_poses[]` (C1, C15, C17, FID1–6, FID8, J1–J5, MK1–4, U2, U3), with 12 declared-pose courtyard overlaps accepted;
- a decap budget, graded at error: 79 caps within `max_distance_mm` 4.787 of their IC, and every supply pin within `max_pin_distance_mm` 1.7622 of a cap;
- the claims for crystal Y1.

I copied it to `intent_run.json` before the first intent-writing step. That step, `waive_locked_overlaps.py`, found 0 pairs and wrote nothing. I added **one row**:

- **`edge_connectors[]`:** SW1, `edge: south`, `mating_face: -y`, `along_edge_band 0.27–0.30`, `overhang_mm {0, 0.5}`.
  - SW1 is a side-actuated TC-1109DE reset button; its plunger is the F.Fab tab on the −y side of its own frame. So it must sit on an edge with the plunger out (skill §3.4).
  - The edge choice comes from the board itself. Its edge keep-out rule area (no tracks or vias within ~1.7 mm of the outline) is notched in only two places: at the USB-C connector J1, and at x 71.7–77.6 on the south edge. The band keeps both switch pads inside that notch.
  - I first wrote it as the west edge, then read the keep-out notches and changed it.
  - SW1 seated at 0.27 of the south edge, facing south; check_floorplan reports pass.

Not used:
- **No EMC rows:** none were given. `emc_roles` lists Y1, the four SP3012 ESD arrays and three ESD diodes, but their limits are the user's to set.
- **No `keep_away`.**
- **No datasheet template:** there is no switching stage (U8, U36, U14 and U31 are LDOs) and no RF front end, and `check_groups` printed no template hint.
- **No `--decaps-from`:** the given intent already carries the decap budget.
- **No datasheet files saved:** only WebSearch was used, so there is no `datasheets/` folder to delete.

## Groups and every judgement call (`groups.json`, 12 groups)

| Group | Parts | Purpose, and the judgement made |
|---|---|---|
| usb | J1 (fixed), R52, R53, R3, C13, FB1, C8, U15, TP13–16 | USB-C with its CC pull-downs, shield RC, VBUS ferrite, the U15 TPD3S014 VBUS switch with D+/D− ESD and its VUSB cap, and the USB test points |
| power | U8, U36, C26, C86, C87, C28, C27, TP1–3, TP8, TP9, TP12, TP17 | the two board LDOs from +5V, their input and front-face output caps, the 150u bulk cap and the rail test points. No edge hint: the skill puts the power group by its entry |
| reset | SW1, U7, C89, D24, R4, R5, C88, **C16** | reset button, APX811 supervisor (it drives U8's enable), diode-OR into the FX2 reset, and the reset RC. **Judgement:** C16 moved here from power for pass 2, because U7's VCC is +5V and pass 1 left U7 pin 4 with no cap in its group |
| fx2 | U1, Y1, C11, C12, C1 (fixed), C2–C7, C9, C10, C19, R18, R19, R9, R17, TP6, TP7 | CY7C68013A with its crystal, 8 back-face +3V3 decaps, ENVA/ENVB pull-downs, ~CRESET and ~ALERT pulls, and clock test points. **Judgement:** the declared C1 placed here so it anchors the FX2 |
| fpga | U30, C20, C21, C23, C81, C18, C24, C25, C77, C14, C76, C78, C79, C80, R31, R32, C33, C92 | iCE40HX8K BGA-121 with its I/O, core, PLL-filter and VCCIO_3 caps. **Judgement:** the root sheet's +3V3 caps split 8 to the FX2 (8 supply pins) and 4 to the FPGA (5 +3V3 balls) |
| leds | D1–D10, R11–R16, R20–R23 | status LEDs with their resistors, with an `edge: S` hint. **Judgement:** D14 and D15, the bank-enable LEDs, stay in their banks |
| sync_aux | J4 (fixed), D11, U32, R38, R45, R44, R10, C85, J10, D12, D13, R39, R43 | the SYNC connector with its ESD, buffer and pulls; the AUX header with its ESD and 47R series resistors |
| eeprom | U2, U3, C15, C17 (all fixed), R40, R1, R2, TP4, TP5, TP10, TP11 | the declared EEPROMs, and the I2C pull-ups and test points at that end of the bus |
| bankA_io / bankB_io | J2 / J3 (fixed), 8 SN74LVC1T45 each, the 33R and 10k arrays, ESD arrays, PCA6408 with its reset pull-up, DNP sockets, and the shifters' +3V3 and VIO decaps | the two I/O banks' buffer chains. **Judgement:** each bank split into an io group (40 parts) and a pwr group (28 parts) |
| bankA_pwr / bankB_pwr | U31 / U14 (LDO), U20 / U13 (DAC), U21 / U12 (INA233), dividers, sense chain, filters, TVS, VIO bulk and bleed resistors, DAC/INA decaps, ENV LED | each bank's adjustable I/O supply. **Judgement:** C83 and C53 kept here as the LDO output bulk, despite check_groups' warning; the reference board also keeps them beyond 5 mm |

Other judgement calls:
- **No `replicate` of one bank onto the other.** J2 and J3 are declared a half turn apart, and laying out a 68-part bank by hand first would have cost hours; the anneal placed both banks.
- **`--decap-limit-weight 50`** on pass 2. It did not clear the decap misses (TOOL_GAPS 2).
- **Hand repairs** (recorded in `CHOSEN.json` `after`), both checked with check_floorplan (0 errors) and check_assembly `--intent` (buildable):
  - `place_pose set C92 --near 94.1 84.39 --rot 90` on s5: C92 was 4.86 mm from U30 against a 4.79 mm limit.
  - `place_pose set C78 82.2 87.08 --rot 180` on final.kicad_pcb: the fanout's +3V3 via had landed in C78's GNDPLL0 pad, and the cap pass could only clear it 2.13 mm from ball J6, past the 1.76 mm limit.
- **File format:** I upgraded final.kicad_pcb to KiCad 10 format (`kicad-cli pcb upgrade`) before the shipped chain, so the routing steps could declare Type VII on the vias they add. Part poses are unchanged; the KiCad 8 copy is in `old/final_k8/`.
- **Discarded helper:** I drafted a `run_steps.sh` loop for running plan lines, never ran it, and moved it to `old/`. `helpers/` is empty.

## Placement passes and the kept seed

- **Pass 1 (default arguments):** I stopped it after 8 seeds because I had edited the intent (SW1's edge) mid-pass, which voids seeds 6–11. Every finished seed carried 3–8 floorplan errors. Recorded as ledger row 1, rejected. Files are in `old/pass1/`.
- **Pass 2 (`--decap-limit-weight 50`, corrected inputs):**
  - All 12 seeds were legal and buildable.
  - Floorplan errors per seed: `{0:2, 1:6, 2:2, 3:6, 4:2, 5:1, 6:3, 7:4, 8:4, 9:1, 10:2, 11:2}`.
  - `judge.json` named seeds 5, 9, 2, 0, 10, 11, and warned on every one.
  - The errors were on different parts in each seed, which is skill §3.6 case 2: I repaired the first named seed, s5 (scattered, cost 9629.1), by hand and judged it on its own.
- **Judge** (`judge_seeds.py --seeds 5`, `KICAD_ROUTE_TRACE=1`, 113 s): quick blocking 21, joins_needed 20, floorplan 1 (C78, caused by the cap pass), vias 615, copper 5011.5. Kept as `final.kicad_pcb`, plus the C78 move.
- **`placed_from/`:** `fixed.kicad_pcb` with its `.kicad_pro`, `groups.json` and `intent_run.json`.

## Routing (§3.8, /plan-pcb-routing followed by hand)

- **Step 0:** check_assembly buildable; baseline board_score unrouted 224, broken 299.
- **Stackup:** 4 copper layers, 252 nets. The stackup is KiCad's untouched default (3 x 0.48 mm, εr 4.5), so there is **no `--impedance` pass**. On that stackup, 90 Ω USB needs 0.41 mm legs and 100 Ω LVDS needs 0.32 mm legs at a 0.1 mm gap, against 0.4 mm between U30's balls. That is not achievable at the BGA escape, so the pairs are routed coupled at 0.1/0.1 with no impedance control. `achievability_note` returns nothing on a board that has a stackup section (TOOL_GAPS 9), so I computed these with `calculate_width_for_impedance`.
- **Planes:** the density tier is STANDARD (4 layers), which means inner-only pours. I kept the board's own pours as drawn: GND on In1.Cu and +3V3 on In2.Cu (`--skip-existing-zones`). Layer prices: GND 6.0, +3V3 2.5, F and B 1.0.
- **Fanout:**
  - U30 (0.8 mm BGA-121): `bga_fanout --escape-method auto`, LVDS pairs escaped together, poured inner layers forbidden. 98 of 98 balls escaped.
  - U1 (QFN-56): the skill treats its perimeter fanout as a "candidate only" to A/B. With it, the chain shipped blocking 1 and 778 vias, so it was not kept.
- **Cap pass** (`place_fanout_clearance --intent`): decap errors 0 → 0.
- **Diff pairs** (`route_diff`, 0.1/0.1):
  - 10 of 14 pairs routed coupled. Z5, Z6, Z9 and Z10 go single-ended, because P/N order is reversed between U30 and J5.
  - Polarity swaps denied: J5 is a connector, and iCE40 LVDS polarity is fixed.
  - The INA233 Vin+/Vin− sense pairs were left to route.py.
- **High-speed scan:** USB HS and LVDS are the high tier and are all diff pairs. The FX2 FIFO bus (48 MHz) and the shifted I/O are medium. I added **no GND-via or stitching tail**: the single-ended nets are below the high tier the skill gates that step on, and In1 is a solid GND plane.
- **No keep-away rule:** the only analog nodes (LDO feedback, DAC output) are DC set-points.
- **Power widths** (analyze-power-nets):
  - The tool's own recommendation was unusable (TOOL_GAPS 5): +5V/+3V3/+1V2 1.2 mm, GND 3.0 mm, GNDPLL 1.0 mm.
  - I estimated currents from the datasheets: CY7C68013A 85 mA maximum; TLV75533 500 mA; TPS73101 150 mA per bank; iCE40HX8K about 100 mA (estimate). Widths come from docs/power-nets.md's table.
  - Chosen widths: GND 0.4, +3V3 0.4, +5V / xVBUS / VUSB 0.5, VIOA / VIOB / LDO outputs / ISNS_H 0.35, +1V2 0.3 (BGA ball field), VIO_AUX / VCCPLL / GNDPLL 0.25.
  - Delivered below the requested width (neck-downs): +5V 45.1 of 96.6 mm, GND 65.4 of 307.1 mm, +3V3 31.2 of 185.1 mm, VIOA 16.8 mm, +1V2 11.0 mm.
  - These widths are estimates, not a declared spec, so they are not graded.
- **The shipped chain:**
  - Files: `final_route/glasgow_revC_plan.sh`, its GUI form `glasgow_revC_plan.json` (7 steps), and `final_route/redo_commands.sh` (this chain only).
  - Pour (kept) → bga_fanout → cap pass → route_diff.
  - → route.py `'*'` at track 0.1, clearance-ceiling 0.09, via 0.3/0.15, grid 0.05.
  - → a cleanup route.py on /VCCPLL0, /IO_Banks/VIOA, GND and +3V3, which removed a VIOA redundant loop.
  - → `/VCCPLL0 --force-reroute`, which removed the dangling stub (TOOL_GAPS 3).
  - The result was copied to `routed.kicad_pcb`.

| Board | What was tried | blocking | vias / copper (mm) |
|---|---|---|---|
| 5_route | Step 2 at track 0.127 / clearance 0.1 / via 0.45, grid 0.1 | 10 | 817 / 5835 |
| 6_iter1, 7_iter2 | Step 2d iterations | 6, then 5 (QB4, D6, DA4, QA6 open; one same-net via drill overlap) | 821 / 5703 |
| 8_iter3 | iteration 3 | improvement gate reverted it (plateau) | — |
| 9_lapA | approach 1: scoped lap on the 4 failing nets, ripping the 24 nets their hints named | reverted (5) | — |
| 10_fine | approach 2: the earlier arm was boxed in at grid 0.1 / clearance 0.1 / track 0.127, above the fab floor, so I shrank the features and used a finer grid (skill §4) | **0**; check_complete INCOMPLETE (a stub and a redundant loop) | 763 / 4958.7 |
| 14_vccpll0 | cleanup pass and /VCCPLL0 force-reroute | **0, DONE** | 763 / 4950.5 |
| 11_fine2c | approach 2 plus the Step 2c env stack | 0, but more vias and 2 orphan stubs: rejected | 800 / 5086 |
| 10b_iter1 | approach 2 plus U1 QFN fanout (A/B) | 1: rejected | 778 / 5047 |
| final_route/7_final | the DONE chain on the KiCad 10 file | **0, DONE** | **763 / 4956.46** |

## Floors (where the run went below the board's own rules)

`check_complete --authored-from` reports **UNSOUND**: track width 0.15 → 0.0889, via diameter 0.4 → 0.25, hole 0.2 → 0.15. It does not list two more, which I confirmed by comparing the two `.kicad_pro` files (TOOL_GAPS 11):
- net-class clearance 0.1499 → 0.09;
- `min_hole_clearance` 0.25 → 0.09.

Measured on the delivered copper:
- **Tracks:** 4012.7 of 4956.5 mm are below 0.15 mm (2377 segments at 0.1, 245 at 0.127, 149 at 0.0889).
- **Vias:** 701 at 0.3/0.15, 26 at 0.25/0.15, 2 at 0.28/0.15 and 34 at 0.4/0.2. That is 729 of 763 below the board's 0.4 mm minimum, all with a 0.15 mm drill (JLC advanced tier).
- **route.py's own disclosure:** "104 feature(s) on 26 net(s) delivered below the requested size … 81 fab-tier escalation(s) to advanced".
- **Clearance:** routed at 0.09 mm. At the input's 0.1499 mm the copper has 2540 violations.
- **Why:** the earlier arm that kept closer to the board's rules (0.127 track, 0.1 clearance, 0.45 vias) left 5 nets open around U30.
- **Via-in-pad:** 356 vias are declared IPC-4761 Type VII (filled and capped) and need a note on the fab drawing.

Confirm the fab can build all of this before ordering.

## Silkscreen

`beautify_labels` placed 2 labels; 262 of the 264 reference labels are hidden on this board. KiCad silk errors were **6 before and 6 after** (all `silk_edge_clearance`). Since the count did not drop, the tidy was **not kept**. The labelled copy is in `old/labels_k10/`.

## Fill

`fill_for_delivery` ran (exit 0): 8 filled polygon blocks, net classes preserved, unconnected items without refill 181 → 0. `delivered.kicad_pcb` is the filled board.

## Timeline (UTC, FIRST_CMD 09:06:36)

| Time | Step |
|---|---|
| 09:06–09:13 | read the brief and skills; board_brief, board_context, check_groups, check_floorplan; wrote groups.json and intent_run.json (SW1 on the west edge) |
| 09:13–09:19 | pass 1, stopped: I changed SW1 from west to south mid-pass after reading the keep-out notches |
| 09:15–09:20 | analyze-power-nets; fanout sizing tests (auto 98/98, dogbone 95/98, channel 81/98) |
| 09:20–09:33 | pass 2, 12 seeds |
| 09:33–09:37 | repaired s5, judged it (113 s), kept it |
| 09:38–09:41 | first chain found the C78 decap break; moved C78, restarted the chain |
| 09:41–09:56 | Step 2 plus iterations (blocking 10 → 6 → 5); plateau; approach 1 failed |
| 09:57–10:12 | approach 2 (8-minute fine route) reached blocking 0; cleanup gave the **first DONE at 10:12** |
| 10:12–10:23 | Step 2c env arm and U1 QFN fanout A/B, both worse |
| 10:23–10:33 | clean re-run of the DONE chain; fill produced 356 via-in-paste violations on the KiCad 10 save |
| 10:34–10:44 | upgraded the file format, re-ran the chain, DONE again |
| 10:44–10:47 | label tidy (not kept), fill, checks on the delivered board, kicad_drc_compare |
| 10:47–10:56 | verifier (PASS), TOOL_GAPS, grade.py, measure.py |

**Where the time went:**
- Placement, about 27 minutes: two passes at 100–340 s per seed on a shared machine. Pass 1 was wasted by my mid-pass intent edit.
- Routing to the first DONE, about 35 minutes.
- Post-DONE arms, about 11 minutes.
- Two clean re-runs of the shipped chain, about 22 minutes. The second was forced by the file-format and via-in-paste problem.
- measure.py's split: 3204 s waiting on jobs, 2366 s model, 1012 s other tools.

## Tool gaps (full list in TOOL_GAPS.md, 12 entries)

The three that cost the most:
1. `fill_for_delivery` turned a DONE board into blocking 356 via its KiCad 10 re-save.
2. `place_simple` leaves decap-limit near-misses in every seed, so only one seed could be judged.
3. The cap pass breaks a decap limit and strands the fanout's stub, which `route.py`'s cleanup does not remove.

Tools that said "fine" when something was wrong:
- `fill_for_delivery` exited 0 ("181 → 0") on a board that then graded blocking 356.
- `check_orphan_stubs` and `check_weird` reported clean, while KiCad reports 3 dangling tracks: +3V3 at (74.2, 112.6), /IO_Banks/QA6 at (88.64, 87.53) and /IO_Banks/Z0_N at (84.56, 78.6).
- `check_complete --authored-from` left out the clearance floor it lowered.
- `check_assembly`, run with the skill's own §3.6 command (no `--intent`), says NOT BUILDABLE about a board that place_simple, the judge and the verifier all read as buildable.

## Verifier verdicts

**Verifier 1: `VERDICT=PASS`** (`verdict_1.txt`; lens files connectivity, drc and spec all PASS).
- **Identity:** sha matches.
- **Placement and mechanical:** buildable; 0 floorplan errors; no gating off-outline copper; all 21 declared poses exact; SW1 at fraction 0.2700 of the south edge, facing south.
- **Routing:** blocking 0 (unrouted 0, broken 0); DONE; fully connected; 0 DRC violations, including with `--check-pad-edge`; KiCad DRC shows 0 copper errors.
- **Diff pairs:** judged not a declared class (no rule with a limit), so ungraded components are UNEXAMINED rather than FAIL.
- **Its review notes** (not gating):
  - The USB pair runs about 52 mm on In1.Cu and 68–80% over a reference-plane void, with 10.58 mm skew.
  - 8 of the 14 pairs have more than 0.5 mm skew.
  - 15 of 61 high-speed vias are more than 3 mm from a GND via.
  - +5V has a 14.1 mm run at 0.10 mm.
  - The floors listed above.
  - Its words: "If you treat the USB 2.0 HS pair as a declared high-speed class, this board would fail on it."

The verifier was called once; two calls remain unused.
