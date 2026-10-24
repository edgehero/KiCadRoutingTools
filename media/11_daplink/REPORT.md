# REPORT.md — 11_daplink, /plan-pcb-placement full (gpm campaign)

Invocation followed: `/plan-pcb-placement full wk/gpm/11_daplink/daplink.kicad_pcb wk/gpm/11_daplink/intent.json`, with the defaults (12 seeds: 6 scattered, 6 clustered; the 6 the objective rates best are judged).

I followed these skills **by hand** from their SKILL.md files:
- `/plan-pcb-placement` (this report);
- `/plan-pcb-routing` (§3.8, the full route);
- `/analyze-power-nets` (routing Step 4);
- the parts of `/find-high-speed-nets`, `/recommend-plane-mappings` and `/review-routed-board` that plan-pcb-routing hands off to them.

## 1. Result

**DONE.** Board: `wk/gpm/11_daplink/delivered.kicad_pcb`, sha256 `6a44b372f28eb282dda316c9c694e055a4cca19740d151c12f9d4bdeb13d42a9`. It was filled by KiCad's own zone filler, and its `.kicad_pro` is beside it.

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking (with `--min-via-diameter 0.5 --min-via-drill 0.3`, the board's own floors) | **0** |
| unrouted / broken | 0 / 0 |
| `check_complete` (same spec flags) | **DONE** |
| `check_complete --authored-from daplink.kicad_pcb` | DONE |
| `check_connected` | ALL NETS FULLY CONNECTED (KiCad refill agrees) |
| `check_drc --baseline <input> --clearance-margin 0.1` | 0 violations (also 0 at margin 0 and with `--check-pad-edge`) |
| `check_assembly --baseline <input>` | buildable, blocking 0 |
| `check_floorplan --intent intent_run.json` | 0 errors, 2 warnings (`pins_to_edge` J1, U1) |
| render checklist `a_off_outline` | no gating pad, graphic or keep-out copper |
| `kicad_drc_compare` | kicad 0, check_drc 0, CONSISTENT |
| `check_weird`, `check_orphan_stubs`, `check_cycles` | none / none / 0 loops |

- **`blocking_by`:** unrouted 0, broken 0, drc 0, drc_via_in_paste 0, undersized 0, floorplan 0, assembly 0.
- **UNGRADED (not examined, not passed):** diff_pairs, impedance, length, net_widths. The board declares no rule for any of them: no `.kicad_dru`, only the Default net class, no stackup, no per-net width spec.

| Quality | Value |
|---|---|
| vias | **22** (all 0.5/0.3 mm, none in a pad) |
| copper_mm | 411.74 |
| segments | 257 |
| joins_needed | 0 |

Independent grade (`scripts/grade.py ... --mode full --spec min-via-diameter=0.5 --spec min-via-drill=0.3`, output in `grade/`):
`{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 22, "copper_mm": 411.74, "segments": 257, "check_complete": "DONE", "check_complete_authored": "DONE", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`

## 2. Inputs, and every row I added to the intent

**The board:** 50 x 20 mm with rounded corners, 2 copper layers, 35 parts (J2 is on B, the rest on F), 50 nets (29 routable). Every part started in the pile; there was no copper and no zone. The README says board-wide pours are kept, but this board had none.

`intent.json` was used read-only. Before my first change I copied it to `intent_run.json`, and every later step used that copy: placing, judging, scoring and both verifier calls. Rows added to `intent_run.json`:
1. **`edge_connectors[]` J3:** `edge east`, `overhang_mm {min 6.0, max 6.5}`.
2. **`edge_connectors[]` J2:** `edge east`, `overhang_mm {min 6.0, max 6.5}`.
   - J2 and J3 are `Harwin_M20-89005xx_1x05_P2.54mm_Horizontal`: right-angle SMD male headers (target SWD on F, target UART on B) whose pins run 6.0 mm past the plastic body.
   - Why (my judgement, SKILL §3.4): a right-angle header mates off the edge with its pins out (98% of human boards keep one within 3 mm of the edge). East is the free short edge opposite the USB-C. Both headers are SMD, so they stack on opposite faces without any hole conflict.
   - Without these rows the placer put J2 in the middle of the bottom face (TOOL_GAPS #5).
3. **`edge_connectors[]` P1 `overhang_mm {min 0.45, max 0.6}`**, added after verifier call 1.
   - The GCT USB4105 footprint draws its own "PCB Edge" line at the shell front, 0.505 mm inside its courtyard front.
   - On this rounded outline `check_floorplan` reads P1's overhang on the courtyard (`legacy_occupancy`). A shell flush with its drawing is therefore a 0.505 mm courtyard overhang (TOOL_GAPS #1).

Not added: no `overlap_waivers[]`, `proximity[]`, `fixed_poses[]` or `templates[]` rows. There was no `mechanical.json`. The brief declares only P1 on the west edge and RST1 on the north edge, along-edge position unknown; both are met.

**EMC rows:**
- `emc_roles` names one crystal (Y1 at U2's PD0/PD1, `max_mm` left null) and no switching converter, so there is no keep_away proposal.
- **No EMC limits were given, and I invented none.** The intent's crystal claims (8.1 / 2.2 mm, derived defaults) were kept unchanged.

## 3. Groups and every judgement call

`groups.json` has 7 groups. `check_groups` reported 0 errors and 1 WARN: J2 has 2 signal links to core and none to its own group, which is expected for a connector.

| Group | Refs | Why |
|---|---|---|
| usb_in (anchor P1; near power, core) | P1, R1, R14, R12, R13, C7, C9, R15 | USB-C with its CC1/CC2 5K1 pull-downs at the connector, the D-/D+ 33R series pair, 18 pF line caps on PA11/PA12, and the 1K5 D+ pull-up the F103 needs |
| power (anchor U1; near usb_in, core) | U1, C1, C2, C3 | AMS1117-3.3 from VBUS with 10 nF / 10 uF in and 10 uF out. The output cap is the LDO's stability cap and the board's only +3.3 V bulk cap. Placed by its power entry, with no edge hint |
| core (anchor U2) | U2, Y1, C5, C6, C4, R2, R3, R4, R5, R9, R10 | STM32F103CB with its 8 MHz crystal and 20 pF load caps (claimed by place_simple), the NRST RC (no button on IF_RST, so it stays at the MCU), BOOT0/PC13/PA0 straps, and R5 joining PB12 to PB14 |
| target (anchor J3; near core, target_reset) | J3, J2 | The target headers, on the east edge |
| target_reset (anchor RST1; near target, core) | RST1, R11, C8 | Reset button (north, declared) with its TGT_RST pull-up and debounce cap |
| leds (anchor D1; near core) | D1, D2, D3, R6, R7, R8 | Three status LEDs, each with its resistor |
| prog (anchor J1; near core) | J1 | 1x04 vertical SWD header for the interface MCU; a short vertical header gets no edge claim |

Judgements, each with its reason:
- **C3 in power, not core.** It is the LDO's required output cap, and it still meets the intent's 13.93 mm limit to U2's supply pins.
- **USB series parts in usb_in.** On a non-RP2040 chip, USB series resistors have no preferred end, so they sit in the chain between P1 and U2.
- **No template candidates.** There is no switching stage (the AMS1117 is an LDO) and no RF chain, and check_groups printed no template hint. §3.5 therefore had nothing to fetch, and no `datasheets/` folder was created: datasheets were read through WebSearch only.
- **The kept seed changed after the first DONE** (seed 1 to seed 10), and **P1 was moved 0.505 mm west** after verifier call 1 (§4, §5).

## 4. Placement (§3.6–3.7)

**The pass:** one pass of 12 seeds, `place_simple --jobs 4` with no extra arguments, 14 s.
- All 12 seeds were buildable.
- Seeds 0, 2, 3 and 4 each had a `decap_pin_distance` floorplan error, so they were not judged.
- judge.json named seeds 10, 11, 7, 1, 9 and 6. For each I checked `check_assembly` (buildable) and `check_floorplan` (0 errors) and looked at the render.

**The judging route:** `judge_chain.txt`, run with `judge_seeds.py --jobs 3` and `KICAD_ROUTE_TRACE=1`, about 30 s in total. The chain: route_diff for the USB pair → `route.py '*' '!GND'` → GND pour on F and B → `route.py '*'`, all at `--quick 2`.

| Seed | Start | Blocking | Joins | Vias | copper_mm | Segments |
|---|---|---|---|---|---|---|
| **1** (judge's pick) | scattered | 0 | 0 | 31 | 370.35 | 460 |
| 6 | clustered | 0 | 0 | 39 | 483.37 | 493 |
| 10 | clustered | 1 | 1 | 30 | 438.31 | 517 |
| 11 | clustered | 1 | 1 | 41 | 478.10 | 543 |
| 9 | clustered | 1 | 1 | 43 | 459.77 | 535 |
| 7 | clustered | 2 | 2 | 26 | 388.20 | 436 |

**Re-judging after the first DONE:** I routed all six judged seeds with the shipping chain (full, not `--quick`).
- Seed 10: blocking 0 with 22 vias.
- Seed 1: its best weird-free arm had 27 vias.
- Seeds 6, 11 and 9 left 1–4 nets open in some arms.

So the kept placement became **seed 10 (clustered)**.

**Hand repair:** `place_pose.py s10.kicad_pcb final.kicad_pcb --intent intent_run.json set P1 103.675 113.2369 --rot 270`. This moves P1 0.505 mm west, with its position along the edge and its turn unchanged, so the shell front meets the outline. Afterwards `check_assembly` was buildable and `check_floorplan` had 0 errors.

`CHOSEN.json`: `{"seed": 10, "start": "clustered", "pass": 1, "intent": "intent_run.json", "place_args": [], "after": ["place_pose.py s10.kicad_pcb final.kicad_pcb --intent intent_run.json set P1 103.675 113.2369 --rot 270"]}`.

- `route_review` listed 0 turned two-pad parts, and the cap pass moved 0 parts.
- `placed_from/` holds the files the pass read: `fixed.kicad_pcb` with its siblings, `groups.json`, and `intent_run.json` as it stood before the P1 band row.

## 5. Route (§3.8, /plan-pcb-routing by hand)

**Analysis:**
- **Step 0 gate:** buildable. Baseline board_score: unrouted 29, broken 0.
- **Stackup:** none (KiCad default), so there is no impedance pass. USB 90 Ω on a nominal stack would need a 1.191 mm leg (a 2.58 mm pair) against a 0.2 mm pin gap, 12.9 times too wide: not achievable.
- **Fanout:** the LQFP-48 at 0.5 mm pitch is a perimeter candidate. I routed with and without it and kept it: 41 against 42 vias on seed 1, blocking 0 both ways.
- **Diff pair /D+ /D-** (USB 2.0 full speed, 12 Mb/s): route_diff deferred it ("electrically short, < 4 mm coupled"), and route.py routed both members single-ended. Polarity swaps were denied (USB).
- **High-speed check** (find-high-speed-nets method): the fastest interfaces are USB FS and SWD/UART on a 72 MHz MCU with an 8 MHz crystal, so the top tier is medium. That means no GND return-via or stitching tail (Step 10 rule 10), and no keep-away (an all-digital board).
- **Power (analyze-power-nets by hand):**

  | Part | Role | Current |
  |---|---|---|
  | P1 | POWER_SOURCE | 500 mA |
  | U1 AMS1117 | POWER_SOURCE | 1 A rating |
  | U2 | CURRENT_SINK | 50 mA (datasheet IDD max) |
  | J3 | CURRENT_SINK | 150 mA **(estimate: target power)** |
  | J2 | CURRENT_SINK | 50 mA **(estimate)** |
  | LEDs | CURRENT_SINK | 1–3 mA **(estimate)** |

  - The tool recommended +3.3V 1.2 mm, GND 2.0 mm, +5V 1.2 mm. Those numbers are inflated (TOOL_GAPS #3).
  - From the real draw of about 0.26 A (an estimate), the skill's IPC table gives **0.7 mm**, which I used for +5V, +3.3V and GND.
  - Delivered: +3.3V is under 0.7 mm for 22.6 of its 120.0 mm (narrowest 0.127 mm; the bottleneck carries 0.54 A at a 10 °C rise). +5V is under for 4.5 of 18.6 mm (narrowest 0.175 mm). GND is under for its whole 1.0 mm of track (it is the pour net).
- **Planes** (recommend-plane-mappings, 2-layer board): a GND flood on both sides, rails as traces.
- **Design rules:** Default class clearance 0.2 mm, signals at 0.127 mm, vias 0.5/0.3 mm, hole-to-hole 0.25 mm.

**Arms tried.** Every number is from board_score with the board's via floors, plus check_weird.

| Arm | Seed | Result |
|---|---|---|
| Pour-last (the Step 8 dense 2-layer flow) with the default `--escalation fab` | 1 | Every net connected, but C4's GND pad was boxed in by +3.3V, /IF_RST and /PA0. Connecting it took a 0.3/0.2 mm via and a 0.1452 mm clearance. **Blocking 2 (undersized)** at the 0.5/0.3 via floor, and `--authored-from` read UNSOUND. Rejected (`final_route_old1/`) |
| Pour-last with `--escalation board` | 1 | GND broken (1 pad). The rip retry the hint suggested was reverted by the improvement gate |
| Plane-first with `--escalation board` | 1 | **First DONE**: 42 vias, 389.56 mm (`final_route_old2/s2_route`). Its 2 iteration passes added a dangling /PA12 segment (TOOL_GAPS #2) |
| Layer costs 1.0 3.0 / 1.0 1.5 | 1 | 36 / 42 vias, both with weird copper |
| Via cost 150 / 300 / 600 / 1000 | 1 | 32 / 27 / 27 (weird) / 27 (weird) vias |
| Via cost 75 / 300, shipping chain | 10 | 39 / 24 vias |
| `--same-net-pad-clearance 0.1`, via cost 200 / 300 / 400 | 10 | 31 / **22** / 24 vias, no via-in-pad |
| Same chain after the P1 move | 10r | 22 vias, 421.07 mm. KiCad flagged a 0.6 mm +3.3V `track_dangling` tail (TOOL_GAPS #6) |
| + scoped `route.py --nets '+3.3V' GND --force-reroute` | 10r | **22 vias, 411.74 mm, 257 segments, no loop, no KiCad dangling: shipped** |

**The shipped chain** is in `final_route/`. Its plan, `in_plan.sh`, passed `route_plan_check` (17 rules OK); `in_plan.json` is the GUI form, and `redo_commands.sh` the recorded manifest (8 commands). The steps:
1. `route_planes.py --nets GND GND --plane-layers F.Cu B.Cu` (a bare pour, first).
2. `qfn_fanout.py --component U2 --nets '*' '!GND' --width 0.127 --clearance-ceiling 0.2 --escalation board --power-nets '+5V' '+3.3V' --power-nets-widths 0.7 0.7`.
3. `place_fanout_clearance.py --clearance 0.2 --intent intent_run.json` (moved nothing).
4. `route_diff.py --nets '/D+' '/D-' --track-width 0.2 --diff-pair-gap 0.2 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --escalation board` (deferred; laid no copper).
5. `route.py --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --layer-costs 1.0 1.0 --via-cost 300 --same-net-pad-clearance 0.1 --escalation board --power-nets GND '+5V' '+3.3V' --power-nets-widths 0.7 0.7 0.7`.
6–7. The same `route.py` twice (Step 2d iterations).
8. The same flags with `--nets '+3.3V' GND --force-reroute`.

**Where I departed from the skill's defaults, each measured on this board:**
- Plane-first instead of pour-last for a dense 2-layer board, because pour-last needed copper below the board's own floors.
- `--escalation board`, which keeps every feature at or above the authored floors.
- `--via-cost 300` and `--same-net-pad-clearance 0.1`. Once DONE, vias come first: 42 dropped to 22, with no via-in-pad. The skill's corpus default via cost of 75 is a completion setting, and completion was already 100%.

## 6. Stop rule and what remains

**Stop condition 1 (done).** No blocker remains.

Observations that do not block:
- **USB pair**, measured but not graded (no rule): /D+ 4.41 mm, /D- 14.85 mm, skew 10.44 mm, 0 mm coupled, all on F.Cu at 0.127 mm. That is about 65 ps of skew at 12 Mb/s, which is negligible. 7.4 mm of the USB tracks cross voids in the B.Cu GND pour. R12 and R13 sit 4.7 mm apart.
- **Copper-to-hole:** the input declares 0.25 mm, and the chain's writeback relaxed the project to 0.2 mm (TOOL_GAPS #4). Graded with kicad-cli at the authored 0.25 mm there are 8 items, the smallest 0.1751 mm, and **all of them are P1's own pads against P1's own NPTH pegs**. That is library geometry, identical on the input. KiCad will show 4 of them as hole_clearance errors at the relaxed 0.2 mm.
- **J3:** its north-east body corner sits 0.033 mm outside the rounded north-east board corner (0.7365 mm radius). Left as placed.
- **Worktree:** `docs/floorplan-intent.md` shows as modified in WT. Its file time is 22:10:16, before my FIRST_CMD; neither I nor the verifiers touched it.

## 7. Floors

- **Copper below the board's authored floors: none.** `check_complete --authored-from` reads DONE; its only floor note is the copper-to-hole item above, which the reference breaks too.
- **route.py `Design rules [--escalation board]`:** the only features delivered under their requested size are the power-width shortfalls in §5 (narrowest track 0.127 mm). There was no fab-tier escalation, no clearance descent (the smallest clearance used was 0.2 mm), and every via is 0.5/0.3 mm.
- **Project writeback:** `min_hole_clearance` 0.25 → 0.2, `min_copper_edge_clearance` 0 → 0.2, `min_via_drill` set to 0.3.
- The rejected pour-last arm is the only one that went below the floors. It was not shipped.

## 8. Silkscreen (§3.9 step 1)

`beautify_labels.py` moved 35 labels. KiCad silk counts (`kicad-cli pcb drc --severity-all`):
- `routed.kicad_pcb`: silk_edge_clearance 26, silk_overlap 29, silk_over_copper 28, **83 in all**.
- `labelled.kicad_pcb`: silk_edge_clearance 24, silk_overlap 10, **34 in all**.

The tidy also added 2 `text_height` warnings: R13's and R1's references were shrunk to 0.70 and 0.75 mm, below the board's 0.8 mm minimum (TOOL_GAPS #8). I kept `labelled.kicad_pcb`.

## 9. Fill (§3.9 step 2)

`fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` ran with exit 0. It filled 2 polygon blocks and kept the net classes. Unconnected items without `--refill-zones` went from 30 to 0. The board does not need refilling before it is plotted.

## 10. Timeline and where the time went

FIRST_CMD was 22:11:21; the run finished at 23:07:24, **56 min**.

| Time | Step |
|---|---|
| 22:11–22:15 | Read README, SKILL.md, verifier.md, part-roles, placement-lessons, plan-pcb-routing (3569 lines) and analyze-power-nets; ran board_brief, board_context, emc_roles |
| 22:15 | intent_run.json, groups.json, check_groups, check_floorplan |
| 22:16 | place_simple pass 1 (14 s) |
| 22:17–22:21 | Checked and rendered the judged seeds; datasheets (STM32F103CB, AMS1117); power analysis; judge chain and judge_seeds |
| 22:22–22:24 | Full route attempt 1 (pour-last): sub-floor via, investigated |
| 22:24–22:29 | Arms (escalation board, plane-first, fanout); **first DONE at 22:28** |
| 22:30–22:44 | Via sweep (seeds × via cost × via-in-pad), switched to seed 10, final chain, §3.9, delivered v1 |
| 22:45–22:52 | Verifier call 1: PASS, plus the P1 shell finding |
| 22:52–22:57 | P1 repair, re-route, +3.3V scoped lap, §3.9 again, delivered v2 |
| 22:57–23:07 | Verifier call 2: PASS; grade, measure, ledger, tool gaps |

`measure.py --self --evidence wk/gpm/11_daplink` (taken at about 23:07): wall 0:55:41, model 1790 s, other tools 1052 s, waiting on jobs 499 s. 209 tool calls, including route.py 30, board_score 32 and check_weird 19. 2 agent spawns, 13 converge records at that moment (18 rows in the end).

**Where it went:** compute never held anything up (a placement pass takes 14 s, a full chain about 15 s). Roughly a quarter went on reading the skills and the board, a third on routing arms and grading them, a fifth on tool behaviour for TOOL_GAPS, and the rest on the two verifier calls and the report.

## 11. Tool gaps

TOOL_GAPS.md has 10 entries, ranked by what they cost:
1. P1 seated on its courtyard because a rounded-corner outline makes the body "unmeasured".
2. An iteration pass added a dangling segment.
3. analyze_power_paths over-counts current.
4. The copper-to-hole floor was relaxed under an "unchanged by this step" claim.
5. Right-angle headers are not treated as edge parts.
6. A KiCad `track_dangling` that check_weird, check_orphan_stubs and check_complete all miss.
7. route_diff discloses escalations for copper it threw away.
8. beautify_labels shrinks text below the board minimum, and §3.9's silk count does not see it.
9. route_plan_check R12 demands the BGA cap pass after a QFP fanout.
10. A bare `kicad-cli` is not on PATH on this machine.

Tools that said "fine" about something that was not:
- The P1 overhang grade passed in courtyard units while the shell sat 0.5 mm inboard.
- route.py's iteration pass reported a clean run while adding a dangling end.
- The floor writeback said "unchanged by this step" while lowering 0.25 to 0.2.
- check_weird and check_orphan_stubs passed a tail that KiCad flags.
- route_diff disclosed 20 escalations for a step that shipped no copper.

## 12. Verifier

**Call 1** (delivered v1, sha `f23b9798...`): `VERDICT=PASS`, with all three lens files PASS. It also measured P1's shell 0.455 mm inside the west edge, behind the footprint's own PCB-Edge line, and a KiCad `track_dangling` on +3.3V. I fixed both (P1 moved 0.505 mm west; +3.3V re-routed with `--force-reroute`) and replaced v1; its files are in `old/delivered_v1/`.

**Call 2** (delivered v2, sha `6a44b372...`): `VERDICT=PASS`; `verdict_2_connectivity`, `verdict_2_drc` and `verdict_2_spec` are all PASS. Its main findings:

| Check | Finding |
|---|---|
| check_assembly | buildable |
| check_floorplan | 0 errors |
| board_score | blocking 0 |
| check_complete | DONE |
| check_connected | all connected |
| check_drc | 0 violations |
| P1 | its PCB-Edge line lies exactly on the west outline; courtyard overhang 0.505 mm, inside the 0.45–0.6 band |
| RST1 | on the north edge |
| J3 / J2 | east edge, overhang 6.49 / 6.01 mm |

The verifier added:
- Its PASS rests on treating the name-matched USB pair as not declared, since no rule constrains it.
- KiCad shows 4 hole_clearance errors, all inside P1's own footprint, and 2 text_height warnings.

The ledger is closed: 18 rows, `--final --stop-condition 1`, with the call-2 lens files.

## 13. Files

All in `wk/gpm/11_daplink/`:
- **Boards:** `delivered.kicad_pcb` (with `.kicad_pro`, `.kicad_prl` and the brief), `DELIVERED.sha256`, `DONE`, `routed.kicad_pcb`, `labelled.kicad_pcb`, `final.kicad_pcb`.
- **Run inputs and choices:** `groups.json`, `intent_run.json` (the given `intent.json` untouched; all input sha256s re-checked unchanged), `CHOSEN.json`, `placed_from/`.
- **Routing chains:** `final_route/` (the shipped chain), `final_route_old1/` (pour-last), `final_route_old2/` (seed-1 plane-first), `final_route_old3/` (seed 10 before the P1 move).
- **Placement and judging:** `ledger.jsonl`, `judge.json`, `judge_chain.txt`, and the `s<S>.*`, `s<S>_route/`, `s<S>_fast.*` seed files.
- **Grading:** `verdict_1*.txt`, `verdict_2*.txt`, `verify_*`, `grade/`, `measure_output.txt`.
- **Gaps:** `TOOL_GAPS.md`, `repro/`.
- **Probes:** under `old/`. `helpers/` is empty: I wrote no helper scripts.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE.** The verifier passed the delivered board on its second call.

- **Delivered board:** `wk/gpm/11_daplink/delivered.kicad_pcb`, sha256 `6a44b372f28eb282dda316c9c694e055a4cca19740d151c12f9d4bdeb13d42a9`. It is the filled board, with its `.kicad_pro` beside it.
- **Score:** blocking 0, joins_needed 0, vias 22 (all 0.5/0.3 mm, none in a pad), copper_mm 411.74, segments 257.
- **Stop rule:** condition 1, done. First DONE came at 22:28. Optimising vias after that took them from 42 to 22.
- **Wall time:** 56 min (FIRST_CMD 22:11:21, finished 23:07).
- **TOOL_GAPS.md:** 10 entries. The top three:
  1. The USB-C seat lines up the courtyard with the edge, not the shell. The outline has rounded corners, so the drawn body counts as "unmeasured" and the courtyard is used instead. That left P1 0.505 mm inside its own drawn PCB-Edge line, while the grade said "pass". Verifier 1 caught it and I fixed it by hand.
  2. A Step 2d `route.py` iteration pass, with nothing left to route, added a 1.5 mm dangling /PA12 segment and still reported a clean run. `check_complete` then read INCOMPLETE.
  3. `analyze_power_paths` counts each part's current once per power pin, and counts the regulator's rating as load. It recommended 2.0 mm GND and 1.2 mm rails for a board drawing about 0.26 A.

The harness refused to let me write REPORT.md ("Subagents should return findings as text"), so REPORT_DONE was not created. The full report is below. TOOL_GAPS.md, DONE and DELIVERED.sha256 are written.
