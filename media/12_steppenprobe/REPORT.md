# REPORT: gpm board 12, steppenprobe (`/plan-pcb-placement full`)

I followed `plan-pcb-placement/SKILL.md` by hand, with `references/verifier.md`, `part-roles.md` and `placement-lessons.md`.

§3.8 `/plan-pcb-routing` was also followed by hand, from its SKILL.md. So were the skills it hands work to:
- `/analyze-power-nets` (Step 4), by hand, in `helpers/power_analysis.py`;
- `/find-high-speed-nets`' tier table (Step 4);
- `/recommend-plane-mappings`' rule for STANDARD boards (Step 5);
- `review-routed-board` Steps 2–4, inside the verifier.

No skill was invoked as a skill.

## 1. Result

**DONE.** The board is `delivered.kicad_pcb`, sha256 `997dde0f87bc9be85e6b47caf481bcd50dd65fe159c56d8097147e5ba8972da0`, filled.

The spec flags are the board's own Board Constraints, plus the Power net class width as a per-net minimum:
`--min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3 --net-min-widths net_min_widths.json` (0.3 mm on the 8 Power-class nets).

| full-mode DONE condition | measured |
|---|---|
| `board_score` blocking (spec flags) | **0** |
| unrouted / broken / joins_needed | 0 / 0 / 0 |
| `check_complete` (spec flags) | **DONE** |
| `check_complete --authored-from` the input | DONE; it lists no floor (but see §4, min_hole_clearance) |
| `check_connected` | all nets fully connected |
| `check_drc --baseline --clearance-margin 0.1` | no violations |
| KiCad DRC (`kicad_drc_compare`) | 0 / 0, CONSISTENT; connection_width 1, starved_thermal 0 |
| `check_assembly --intent --baseline` | buildable |
| `check_floorplan --intent` | 0 errors; 1 warning: C3 is 2.36 mm from Y1 pad 1 against a warn-graded 2.2 mm limit |
| `render_placement` a_off_outline | pad_copper_gating, graphic_copper and keepout_copper all empty |
| Mechanical facts | H1–H4 exactly at (104,54), (104,106), (146,54), (146,106), rot 0; J1 on the north edge, facing north; SW1 on the west edge |
| `grade.py --mode full` | `done: true`, blocking 0, vias 123, copper 1066.84, segments 966 (`grade/grade_output.txt`) |

- **blocking_by:** every component is 0, including net_widths and drc_via_in_paste.
- **Copper:** 123 vias, all 0.6/0.3. 1066.84 mm of copper (F.Cu 575, B.Cu 492). 966 segments. No via sits in an SMD pad.
- **Ungraded (UNEXAMINED):**
  - diff_pairs: KiCad does not recognise `/USB_DP` + `/USB_DM` as a pair, and no rule exists to grade them against.
  - impedance: the stackup is KiCad's default.
  - length: no groups are declared.
- **USB pair, measured anyway:** skew 0.632 mm, 17.2 mm coupled, 18.2 mm uncoupled. Every USB via has a GND via within 2.94 mm.

## 2. Groups and every judgement call

**The board.** It is an FT2232HL USB-to-JTAG/SWD/UART probe: 84 parts, 2 layers, 50 x 60 mm with 3 mm corner radii. It carries a +3V3 pour on F.Cu and a GND pour on B.Cu; I kept both.

The board has no Value fields, so I identified parts from their MPN properties:
- U2 XC6206 LDO, U3 SRV05-4 ESD array, U4 93C46-class EEPROM (DNF);
- U5–U12 74LVC1G125/126 buffers, Q1 2N7002, Y1 12 MHz crystal;
- J1 GCT USB4085 USB-C, J2 2x7 1.27 mm Cortex debug header, J4 1x16 2.54 mm breakout;
- SW1 EG1215 slide switch, SW2 6x6 top-actuated button.

**Groups.** `check_groups` reports 0 errors, 2 warnings and no template hints.

| group | refs | hints | why |
|---|---|---|---|
| usb_in | J1, R1, R2, U3 | anchor J1; near power, core | The receptacle, its CC pull-downs, and the ESD array right behind its pin row |
| power | FB1, U2, C1, C2 | anchor U2; near usb_in, core | VBUS ferrite and the LDO with its in/out caps; no edge hint |
| core | U1, Y1, C3, C4, C5–C16, C22, FB2, FB3, R4, R6, TP1, TP2 | anchor U1 | FT2232H, crystal, VPLL/VPHY filters, 1V8 and 3V3 decaps, REF resistor, RESET# pull-up, RTS#/CTS# test points |
| eeprom | U4, R3, R5, C18 | near core | EEPROM and its parts; C18 is DNF like U4, so it is U4's decap |
| buffers | U5–U12, C17, C19–C21, R17, R25, R22, R23, Q1, R24, SW1, SW2 | near core, target_io | Level shifters with their Vdrive decaps, OE biasing, the SRST stage and reset button, and the SWO/RXD select switch |
| target_io | J2, J4, R11–R16, R19, R20 | anchor J4; edge S; near buffers | Both target headers and their 100R series resistors |
| leds | D1–D6, R7–R10, R18, R21 | edge E; near core | Status LEDs with their resistors |

**Judgement calls:**
- **Fiducials.** FID1–3 are declared nowhere. I seated them with `intent_run.json` `fixed_poses[]` (`derived_default`) at (103, 60.5), (147, 60.5) and (147, 99.5). That puts an L near three corners, beside the holes. I used the intent rather than a KiCad lock because the input carries no locks and a lock voids the marker waiver.
- **J1 overhang.** The GCT USB4085 drawing (Rev B, sheet 2/3 and sheet 1) puts the board edge 1.74 mm past the front shell tabs, with the shell front 4.25 mm past them, so the body reaches 2.51 mm past the edge. On this rounded outline `check_floorplan` grades the band on the courtyard, so I wrote `overhang_mm` as 3.0–3.1.
- **SW1 overhang.** The EG1215 datasheet draws no board-edge line, so SW1 keeps the flush default.
- **No templates.** The board has no switching stage and no RF front end.
- **EMC rows.** None were given, and I invented none.
- **Kept seed.** The fast judge picked pass-1 seed 8. Full-routed, seed 11 does better: 133–136 vias against 143–155. I switched the kept placement to seed 11 (clustered, pass 1, place_args [], after []).
- **Power widths.** After verifier call 1 failed the board, I treat the Power net class's 0.3 mm as a spec, and the delivered board meets it everywhere.
- **Routing choices:**
  - Solid pours: route_plan_check rule R07 refuses `--thermal-relief`.
  - `--escalation board`, to stay at the board's own 0.6 mm via and 0.15 mm floors.
  - `--same-net-pad-clearance 0.1`: with the defaults, 77 of 155 vias were in SMD pads, LQFP pins included.
  - `--min-thickness 0.15`, matching the designer's zones; this took KiCad's connection_width items from 9 to 0–1.
  - Layer costs 1.0 1.5.
  - Rails routed first and pours finalised last, both at 0.3 mm; signals at 0.15 mm in between.
  - `route_diff --diff-pair-intra-match`, which took the USB skew from 4.5 mm to 0.63 mm.
- **The 109-via board was not shipped.** `--via-cost 300` gave a DONE routed board, but 4 of its +3V3 vias sit in pads. The delivery fill made those 4 vias blocking (TOOL_GAPS 1 and 5), and I would not override the via tokens it had written by hand.
- **GND return-via tail skipped.** USB is high-tier, but there is no second GND plane; the other pour is +3V3 on F.Cu.

**Rows I added to `intent_run.json`:**
1. FID1/2/3 `fixed_poses` (above).
2. `edge_connectors[J1].overhang_mm` = {3.0, 3.1}, with its datasheet reason.

## 3. Stop rule

Stop condition 1 (DONE). The first DONE came at 20:37:55Z with 155 vias. Then I optimised:

| # | approach | result | kept |
|---|---|---|---|
| 1 | No via-in-pad, layer costs, +1V8 force-reroute (seed 8) | 143 vias | yes |
| 2 | Full-route the judge's runner-up, seed 11 | 133–136 vias, ~1100 mm | yes |
| 3 | Placement pass 2 with `--decap-limit-weight 50` | its seeds route worse | no |
| 4 | Turn R25 as route_review suggests | 142 vias | no |
| 5 | Layer-cost rebalance | 1.0 3.0: 136 vias, 1090 mm | yes |
| 6 | Via-cost sweep | 109 vias, but rejected at delivery (TOOL_GAPS 1) | no |
| 7 | The via-cost-300 chain on other placements | 120–123 vias | no |
| 8 | Step 2c retry levers | +1V8 broken | no |
| 9 | Pass 3 without the target_io edge hint | 0 floorplan-clean seeds | no |
| — | Verifier fix: width chain plus intra-pair match | **123 vias, 1066.84 mm, widths ≥ 0.3** | yes |

No blocker remains.

## 4. Floors

- The board routes at its authored values: clearance 0.15, track ≥ 0.15, vias 0.6/0.3, hole-to-hole 0.25, edge 0.3.
- route.py's `Design rules` line says 1 feature was delivered narrower than requested, the narrowest at 0.3 mm, so nothing went below the Power-class floor.
- One authored floor was lowered: route_diff's writeback changed `min_hole_clearance` from 0.25 to 0.15. The copper still meets 0.25: check_drc grades at 0.25, and the verifier re-ran KiCad DRC with 0.25 restored and got 0 violations.
- The stackup is KiCad's default, so there was no impedance pass. A 90-ohm pair is not achievable on this 2-layer board at a routable width.

## 5. Silkscreen and fill

- **Silk (KiCad):** before the tidy, edge 4, over copper 50, overlap 54 (108). After `beautify_labels`: 2, 3, 13 (18). I kept the tidied board.
- **But:** the tidy also introduced 5 `text_height` warnings, references shrunk below the board's 0.8 mm minimum (TOOL_GAPS 16).
- **Fill:** `fill_for_delivery` ran and exited 0, taking unrefilled unconnected items from 69 to 0. The board is filled.

## 6. Timeline (UTC) and where the time went

| time | event |
|---|---|
| 20:11:51 | FIRST_CMD; read the skills |
| ~20:15–20:21 | Board analysis, datasheets (PDF helper), groups, intent_run |
| 20:22:06 | Pass 1 placed (28 s) |
| 20:25:58 | Judged seeds 11 and 8 (18 s) |
| 20:27–20:37 | Chain A/B: thermal, fanout, pour-last, escalation |
| 20:37:55 | **First DONE** (155 vias) |
| 20:38–20:52 | Via-in-pad, stubs, min-thickness, seed 11 full route; kept placement switched |
| 20:52–21:11 | Passes 2 and 3, route_review, layer costs, via-cost sweep; the 109-via board rejected at delivery |
| 21:15:50 | First delivery (136 vias) |
| 21:17–21:24 | Verifier call 1: **FAIL** (power widths; USB pair ungraded, skew 4.5 mm) |
| 21:25–21:31 | Width chain plus intra-pair match: 123 vias |
| 21:31–21:37 | Verifier call 2: **PASS** |
| 21:39 | measure.py: 1:27:10 wall |

Placing is cheap on this board: 28 s for a 12-seed pass and about 40 s for a full chain. The time went to reading the skills (about 10 min), about 50 full routing chains for A/B and optimisation (about 50 min, three at a time), and the two verifier calls (about 12 min). measure.py splits the time as model 2595 s, tools 2382 s, waiting on jobs 254 s.

**Process note.** I made verifier call 2 by spawning a fresh subagent instead of sending the first one a message, and TaskStop could not cancel it. So two verifier subagents ran: two calls in total, within the 3-call cap, but not "one subagent".

## 7. Tool gaps

`TOOL_GAPS.md` has 16 entries plus a table of the helpers I wrote. These are the ones where a tool said "fine" about something that was not:
- `fill_for_delivery` reported "54 -> 0", exit 0, while turning a DONE board into blocking 4.
- `--same-net-pad-clearance 0.3` still left 4 vias in pads.
- With the default settings, board_score, check_complete and check_drc all passed a board with 77 vias in SMD pads.
- `judge_seeds` picked the seed that full-routes 12 % worse on vias.
- `check_complete --authored-from` missed the lowered `min_hole_clearance`.
- The skill's silk count hid the 5 new `text_height` warnings.

## 8. Verifier verdicts

- **verdict_1.txt: FAIL.**
  - The Power class's 0.3 mm width was ungraded. Graded, GND, VBUS, +3V3 and +1V8 carried 1.65–19 mm of copper at 0.15 mm.
  - The USB pair was ungraded, with 4.52 mm skew.
  - Lenses: connectivity PASS, drc PASS, spec FAIL.
  - Fixed by the width chain and `--diff-pair-intra-match`.
- **verdict_2.txt: PASS.**
  - All checks pass; net_widths graded with 0 violations.
  - USB skew 0.632 mm; every USB via has a GND via within 2.94 mm (the 3.0 mm high-tier limit).
  - Lenses: connectivity, drc and spec all PASS.
  - The ledger is closed with these lens files.

Everything is in `wk/gpm/12_steppenprobe/`. The datasheet folder was moved to `old/datasheets/`.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE.** The board passed the verifier on its second call, after the first call failed it.

- **Delivered board:** `wk/gpm/12_steppenprobe/delivered.kicad_pcb`, sha256 `997dde0f87bc9be85e6b47caf481bcd50dd65fe159c56d8097147e5ba8972da0`. It is filled by `fill_for_delivery`.
- **Score:** blocking 0, joins_needed 0, vias 123, copper_mm 1066.84, segments 966.
- **Stop rule:** stop condition 1 (DONE). After DONE I kept optimising and stopped when three different approaches in a row (7, 8, 9) failed to improve it.
- **Wall time from FIRST_CMD (20:11:51Z):** 1:27:10, measured by `measure.py`.
- **TOOL_GAPS.md:** 16 entries. The top three:
  1. `fill_for_delivery` rewrites the board as KiCad 10 with an explicit `(capping no)(filling no)` on every via. That turned a DONE 109-via board into blocking 4 (via-in-paste), so I could not ship it.
  2. The skills disagree on whether a net-class track width is a spec. The verifier failed call 1 on it, and the default chain cannot meet the Power class's 0.3 mm. A chain I wrote myself (rails first and pours last at 0.3 mm) fixed it and also cut vias from 136 to 123.
  3. `route_diff` lowers the board's own `min_hole_clearance` from 0.25 to 0.15, and `check_complete --authored-from` does not report it.

**REPORT.md could not be written.** The harness refused it ("Subagents should return findings as text"), so there is no REPORT_DONE and the full report follows.
