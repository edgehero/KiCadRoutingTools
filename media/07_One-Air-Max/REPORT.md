# REPORT -- board 07 One-Air-Max, `/plan-pcb-placement full`

I followed `.claude/skills/plan-pcb-placement/SKILL.md` by hand, with `references/verifier.md`, `part-roles.md` and `placement-lessons.md`. I followed the §3.8 route by hand from `/plan-pcb-routing`'s SKILL.md, and its power-net step by hand from `/analyze-power-nets`'s SKILL.md.

## 1. Result

**DONE.** The board is `wk/gpm/07_One-Air-Max/delivered.kicad_pcb` (filled, with its `.kicad_pro`), sha256 `41fbfdfac0e3fd1ed36fa1ba7567352fa63f3faa981332f84ecf2f8d413306dc`.

| DONE condition | Measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking / unrouted / broken | **0 / 0 / 0** |
| `check_complete` | **DONE** |
| `check_connected` | all nets fully connected (KiCad refill agrees) |
| `check_drc --baseline <input> --clearance-margin 0.1` | 0 violations |
| `check_assembly --intent --baseline` | buildable (blocking 0) |
| `check_floorplan --intent --allow-routed` | 0 errors, 3 warnings |
| KiCad 10.0.7 DRC (`kicad_drc_compare`) | 2 KiCad-only items, both inside F2's own footprint (see §4) |

- **`blocking_by`:** every class is 0. diff_pairs, impedance, length and net_widths are ungraded because the board declares no spec for them.
- **Quality:** vias 169, copper_mm 2647.59, segments 1909.
- **`grade.py --mode full`:** `{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 169, "copper_mm": 2647.59, "segments": 1909, "check_complete": "DONE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`. The output is in `grade_output.txt` and `grade_delivered.json`.
- **`measure.py --self --evidence wk/gpm/07_One-Air-Max`:** wall clock 2:52:16, of which 4775 s waiting on jobs, 4027 s model time and 1535 s other tools. Output is in `measure_output.txt`.
- **Floorplan warnings:**
  - U1 "seated 6.08 mm from the nearest edge": its antenna end is 0.06 mm from the edge (TOOL_GAPS 11).
  - PM1 pins_to_edge.
  - U5 template ground return: 4 of 11 caps over 3 mm, worst C27 at 4.02 mm.

## 2. Inputs and what I added to the intent

- `fixed.kicad_pcb` is a `copy_board` copy of the input. `intent.json` is untouched (sha256 `deb408be...`; all five input sha256s re-checked at the end). From the first edit on, every step used `intent_run.json`.
- **Rows I added to `intent_run.json`:**
  1. `templates[]` for U6 (TPS62903-Q1), U2 (TPS62902) and U5 (BQ25672); see §3.
  2. An `edge_connectors[]` entry for **U1: edge east, class connector_affinity, mating_face +y.** This is my judgement, not a mechanical fact. The ESP32-C6-WROOM-1's PCB antenna (the +y end, silk y 9.73..15.75) has to sit at an edge clear of the 3x18650 holder BAT1, whose body covers x 107.0-184.6, y 57.4-114.2 on the front.
     - Pass 1 declared the north edge. The seat put the antenna at the notch's depth, under BAT1 (TOOL_GAPS 3).
     - The east edge leaves the antenna at x ≥ 189.8, more than 4 mm clear of the holder.
     - An `ANT_KEEPOUT` rule area (tracks, vias and pour, on every layer) is written in U1's frame as routing step 0.
- `waive_locked_overlaps`: 0 pairs. I added no `overlap_waivers[]` or `proximity[]` row.
- **EMC rows:** none were given and I invented none. board_context's proposed crystal keep-away (switch nodes vs X1 at 3 mm) was not declared.
- **Datasheets:**
  - Downloaded: TI TPS62902 SLVSFM1A, TI TPS62903-Q1 SLVSG65A, TI BQ25672 SLUSEB9B, and the XKB DC-045A-1.3 drawing.
  - Read through `helpers/pdf_tool.swift`, because poppler is not installed (TOOL_GAPS 8).
  - The datasheet folder was moved to `old/datasheets/` at hand-back.
- **DC1:** the drawing shows no board-edge line, so DC1 keeps a flush band. Its mouth is the footprint's -x end.

## 3. Groups and judgement calls

`groups.json` has 12 groups:

| Group | Anchor | Parts | Notes |
|---|---|---|---|
| charger | U5 | 35 | DC1, Solarpower1, D3 TVS, BQ25672 with its caps, boot caps, L1, set resistors, LED3+R30, TP7/TP8, Battery1 |
| batt_protect | U4 | 36 | BQ77905 protector with cell-tap filters, R11 sense, Q1/Q2 low-side FETs and gate network, NTC1, F2, PWR_SW1. Candidate "none" |
| buck5 | U6 | 17 | TPS62903 to +5VBAT |
| vmux | U7 | 6 | TPS2117 mux, F1, FB1 (the PGND-GND tie). "none" |
| buck3v3 | U2 | 11 | TPS62902 to +3V3 |
| core | U1 | 24 | Module, 3V3 decaps (including front C10/C13), EN RC, TPL5010 watchdog, IO8 and BOOT straps (R5 moved here: a strap belongs at the pin), USB 22R pair, IO pull-ups |
| ui | SW1 | 5 | SW1, C8, LED2, R71, C51 |
| usb | USB1 | 7 | USB1, CC 5.1k, shield RC, 1 nF D± caps |
| pm_bridge | U8 | 23 | WK2132 with crystal, straps, reset RC, the B5817W diodes to PM1/PM2, U13 |
| co2_no2 | U14 | 16 | CO2 + U14, NO2 + U17/U18 |
| ce | U15 | 13 | CE1 + U15/U16, JP2/JP3 (I2C or UART select) |
| i2c_io | IO1 | 8 | I2C3, IO1, EEPROM, I2C pull-ups |

- The back-side cable connectors and PWR_SW1 got no edge: the brief gives none (PWR_SW1 was 4.04 mm from the edge in the source).
- **Templates (§3.5)**, fitted with `fit_template.py`. On the kept board every member drifts 0.00-0.02 mm.
  - **U6 TPS62903-Q1** (§9.6.1, Figure 9-69). Back-side part, so the figure is mirrored left-right. Members: C47 then C46/C48 across VIN/GND, L2 on SW (turned 270), C43/C45 COUT, C49 SS, R42 MODE, R40/R39 FB.
  - **U2 TPS62902** (§8.5.1, Figure 8-86), same mapping. Members: C68/C14 CIN, L3, C6/C3 COUT, C4, R57, R56/R52.
  - **U5 BQ25672** (§11.1 priority list, Figure 11-2), top view transposed onto the back. Members: C26 SYS and C37 PMID (0.1 uF) at the pins, C28/C29 boot caps at the corners, C31 VBUS, C36 REGN, L1 beyond them (legs 3.3 mm, about where the figure puts L5), C23/C30 BAT, and the 10 uF caps behind their small partners (legs up to 4.8 mm against the figure's ~3 mm).
- **Pass 3** tried a U2 template with C4/R57 standing radial. It routed worse and was rejected; the pass-2 template stayed.

## 4. Placement, routing, hand work

### Placement passes

- **Pass 1** (12 seeds, about 32 s each): rejected without judging, because U1 sat at the notch depth.
- **Pass 2:** judged seeds 11, 0, 3, 2, 8, 4 with quick routes of about 30 s each; the judge ranked seed 4 first.

### Routing chain and optimisation

- **Chain:**
  - ANT keep-out.
  - Bare pour of the board's own GND zone (F/B/In2) and +3V3 (In1), plus PGND as a split region on In2. PGND is a secondary ground tied to GND by FB1 (routing skill Step 5b.3).
  - `route_diff` for the USB and SRP/SRN pairs.
  - `route.py '*'`.
- **First full route** (seed 4, `--escalation fab`): first DONE at 16:18Z, with 310 vias and 212 vias in paste.
- **Optimisation:**

| Change | Vias | Outcome |
|---|---|---|
| `--escalation board --same-net-pad-clearance 0.1` | 253 | adopted |
| `--via-cost 150` | 205 | adopted |
| Same recipe, kept placement switched to pass-2 seed 8 | 196 | adopted |
| Via cost 200 / 250 / 300 / 350 on seed 8 | 183 / 182 / 175 / **172** | 350 adopted |
| Rejected tries | | via-cost 300 and 400, pass-3 template, PGND poured on B.Cu, seeds 11/3/0, inner layer cost 6, track 0.127, seed 4 at 350, max-ripup 10 |

### Verifier 1 FAIL (17:54Z) and hand repairs

Verifier 1 found:
- DC1's mouth faced west and its housing overlapped I2C2 by 4.83 mm².
- Solarpower1, PWR_SW1 and NTC1 were inside BAT1's outline.
- U3, R5 and R63 were under U1.

I repaired the placement with `place_pose` (exact poses are in CHOSEN.json `after`):
- DC1 to (189.8,116.5) at rot 90, mouth facing south at the SE corner.
- PWR_SW1 to (178,116.9) at rot 0, actuator facing south.
- Solarpower1 to (170,118.5).
- NTC1 to the west strip at (100.8,76.5).
- U3 to (168.1,99.68); R5 and R63 clear of the module; C7/C66/C70/C73 moved to make room.
- My own silk-collision check (`helpers/silk_collisions.py`) then found three more, which I also moved:
  - U12 0.65 mm west, off the I2C3 housing;
  - D7 0.65 mm south (the D6/D7 bodies overlapped by 0.44 mm);
  - R20 and R18 nudged off the D2 and Q1 bodies.

### Kept route (`final_route/`, manifest `redo_commands.sh`)

- **Steps 0-2:** keep-out, pour, diff pairs, and `route.py --via-cost 350 --escalation board --same-net-pad-clearance 0.1`.
- **Step 3:** the U2.7 MODE net alone. That pin is caged on B.Cu by its own template members.
- **Step 4:** a closing `route.py '*'` to clean up.
- **Step 5:** rescue of MODE, REGN and SYS, with a via in the pad allowed (`--escalation fab --same-net-pad-clearance -1`).

### Hand copper after the last route step

Everything below was re-checked with check_weird, check_connected, check_drc and KiCad's DRC.

- `helpers/fix_copper.py`:
  - two router-written vias at 0.45/0.508 and 0.54/0.508 resized to 0.608, at (137.8,113.8) and (139.45,75.25);
  - three soft joints closed: Solar+, PMID and PGND power tracks that ended 0.5-0.7 mm short of the same-net track they overlap.
- `helpers/prune_removable.py`: 11 redundant in-pad segments deleted.
- On the delivered file: Type VII (`capping yes`, `filling yes`) declared on the five vias in pads, at (180.9,101.1), (138.75,79.45), (141.6,75.6), (189.85,85.35) and (190.45,83.75). The KiCad 10 save in `fill_for_delivery` had turned them into blocking via-in-paste (TOOL_GAPS 4).
- **Fab note:** these five vias need IPC-4761 Type VII (filled and capped).

### KiCad-only DRC items

Both come from F2, easyeda's `PCB_fuse`: its fuse element is a net-less 0.25 mm B.Cu line drawn from pad 1 to pad 2. That is inherent to the library footprint and is present at any pose.

## 5. Stop rule and remaining items

- **Stop: condition 1, DONE.** Optimisation stopped on a plateau after three approaches without improvement following via-cost 350. Verifier 2 passed.
- **Remaining blockers:** none.
- **Unexamined** (no spec declared): diff_pairs, impedance, length, net_widths.
- **Measured but not graded:**
  - USB_D± coupled 37.84 of 49.87 mm, skew 3.06 mm.
  - GND return via over 5 mm from 3 of the 4 USB signal vias.
  - Power widths are requests and stay ungraded (no width spec). Examples under the requested 1 mm: Net-(Q1-D) 9.2/9.2 mm, Net-(U6-SW) 2.2/2.2 mm.
  - A 0.0889 mm +3V3 branch of 11.9 mm runs between U1 pads 19-22. The verifier flagged it as advisory.

## 6. Floors

- `route.py` Design rules: smallest track 0.0889 mm, which is the board's DRC floor. The escalations went to the board's own floors, and the rescue step escalated 3 vias to the advanced tier.
- `check_complete --authored-from`: **UNSOUND.** Via diameter 0.3 → 0.25, and hole 0.508 → 0.15. The affected vias:

| Net | Position | Via |
|---|---|---|
| MODE | (190.45,83.75) | 0.25/0.15 |
| MODE | (189.85,85.35) | 0.30/0.15 |
| SYS | (138.75,79.45) | 0.25/0.15 |
| REGN | (141.6,75.6) | 0.45/0.2 |
| REGN | (143.0,76.6) | 0.45/0.2 |

- The other 164 vias are 0.608/0.508. Confirm the fab takes 0.15 mm drills, or treat the project's 0.508 minimum hole as the EasyEDA default it appears to be.
- Clearance is 0.1 mm and edge clearance 0.3 mm.

## 7. Silkscreen and fill

- **Labels:** KiCad silk counts went from 18/199/199 = 416 before `beautify_labels` to 15/199/199 = 413 after. `labelled.kicad_pcb` was kept.
- **Fill:** `fill_for_delivery` ran, writing 11 filled_polygon blocks and keeping 1 net class; unconnected went 123 → 0.

## 8. Power nets (analyze-power-nets, by hand)

- I classified the 43 unknown parts and the six load switches. All currents are **estimates**:
  - sources: DC1/Solarpower1 2 A, BAT1/Battery1 3 A, U5 3 A, U6 2 A, U2 1 A, USB1 1.5 A;
  - pass-throughs: U7, PWR_SW1, Q1/Q2, U13-U18;
  - sinks: U1 0.5 A, sensors 0.15-0.3 A.
- `trace_power_paths` traced no path (TOOL_GAPS 7), so the widths come from the IPC-2221 table with 2x margin:
  - 1.0 mm on the charger, battery and buck power nets;
  - 0.7 mm on +3V3, PGND, +5VUSB and VOUT1-6;
  - 0.5 mm for the GND taps.

## 9. Timeline (UTC) and where the time went

| Time | Step |
|---|---|
| 15:43 | start |
| 15:58 | groups and three templates done |
| 16:01 | pass 1 placed, then rejected |
| 16:05-16:06 | pass 2 placed and judged |
| 16:14-16:18 | first route, first DONE |
| 16:21-17:32 | optimisation sweep (about 14 full routes) |
| 17:40 | delivered v1 |
| 17:54 | verifier 1 FAIL |
| 17:55-18:28 | three hand repairs, re-routes, deliveries v2 and v3 |
| ~18:33 | verifier 2 PASS |
| 18:35 | measure.py |

Most of the time went to full routes of about 6 min each, plus hand fixes of router artifacts on every candidate. Placement itself took about 10 min.

## 10. Tool gaps

`TOOL_GAPS.md` has 11 entries; the top three are in the summary above. These tools said "fine" when it was not:
- check_assembly: buildable, with a header inside the battery holder and a jack over a header.
- check_floorplan: U1 6.4 mm off its declared edge, graded only as a warning.
- check_drc: clean on a board with a via smaller than its drill.
- fill_for_delivery: exit 0 while turning 4-7 accepted vias into blocking via-in-paste.

## 11. Verifier verdicts

- **verdict_1.txt: FAIL.** Connectivity and DRC passed. Spec failed: DC1 faced west and collided with I2C2; Solarpower1 and PWR_SW1 were under BAT1; NTC1 was under BAT1 and U3/R5/R63 under U1 (advisory). All were fixed in §4.
- **verdict_2.txt: PASS.** Connectivity, DRC and spec all passed; the six mechanical poses are exact, and DC1 faces south, 0.07 mm from the south edge.

Everything is in `wk/gpm/07_One-Air-Max/`:
- delivered.kicad_pcb, DELIVERED.sha256, DONE
- routed.kicad_pcb, final.kicad_pcb
- CHOSEN.json, placed_from/, final_route/
- ledger.jsonl (closed with `--final`)
- TOOL_GAPS.md
- verdict_1*.txt, verdict_2*.txt, grade_output.txt, measure_output.txt

---

## The teammate's final summary (saved with the report by the orchestrator)

I finished board 07 and it is DONE: the second verifier call passed. But REPORT.md is not written to the folder: the harness refused the write ("Subagents should return findings as text"). Its full text is below, and I did not create REPORT_DONE.

- **Delivered board:** `wk/gpm/07_One-Air-Max/delivered.kicad_pcb`, sha256 `41fbfdfac0e3fd1ed36fa1ba7567352fa63f3faa981332f84ecf2f8d413306dc`. Zones are filled and `DONE` is written.
- **Score:** blocking 0, joins_needed 0, vias 169, copper_mm 2647.59, segments 1909.
- **Stop rule:** condition 1, DONE. Optimisation had already stopped on a plateau (three approaches in a row after via-cost 350 did not improve). Verifier call 1 then failed the board on physical defects; I fixed them by hand, routed again, and call 2 passed.
- **Wall time from FIRST_CMD:** about 2 h 54 min (15:43Z to about 18:37Z). measure.py reports 2:52:16.
- **TOOL_GAPS.md has 11 entries.** The top three:
  1. Bodies drawn only on silk never gate. The placer put a header, the power switch and the thermistor inside the battery holder, put the DC jack over I2C2, and put U3/R5/R63 under the ESP32 module. `check_assembly` still said "buildable"; verifier 1 caught it.
  2. `route.py --escalation board` writes vias whose diameter is smaller than their drill (0.45/0.508). `check_drc` calls the board clean while KiCad reports a hole-clearance violation. I had to fix these by hand on almost every routed candidate.
  3. On a notched edge, the edge seat put U1 at the notch's depth, 6.4 mm inside the real north edge with its antenna under the battery. It was graded only as a warning, and a whole placement pass was lost.
