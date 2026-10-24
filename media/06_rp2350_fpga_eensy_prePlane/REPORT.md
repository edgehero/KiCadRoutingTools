# REPORT -- gpm 06 rp2350_fpga_eensy_prePlane (`/plan-pcb-placement full`)

I followed `plan-pcb-placement/SKILL.md` (with verifier.md, part-roles.md and placement-lessons.md) by hand. Its §3.8 route is `plan-pcb-routing/SKILL.md`, **followed by hand**. The `/analyze-power-nets` step that the routing skill asks for (`analyze-power-nets/SKILL.md`) was also **followed by hand**.

## 1. Result

**DONE.** The delivered board is `delivered.kicad_pcb`, sha256 `b9225a0cf3c4c32825c2fa0037798effade8b6be8bb2e12721d1f4d3dcf6804b`. It is the `fill_for_delivery` copy of `routed.kicad_pcb`, which is `final_route/s8_iter2.kicad_pcb`.

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking | **0** |
| unrouted | **0** |
| broken | **0** |
| `check_complete` | **DONE**. Diff pairs, impedance, length and net widths are UNEXAMINED, not passed: the board declares no such spec. |
| `check_connected` | All nets fully connected |
| `check_drc --baseline <input> --clearance-margin 0.1` | 0 violations; 1 same-net self-crossing warning, which KiCad permits |
| `check_assembly --baseline` | buildable (blocking 0, advisory 0) |
| `check_floorplan --intent intent_run.json` | 0 errors, 3 warnings (below) |
| KiCad DRC (`kicad_drc_compare --baseline <input>`) | CONSISTENT: 0 KiCad-only items once the input's 33 are subtracted; 0 courtyard, 0 connection_width, 0 starved thermal |
| `check_orphan_stubs`, `check_weird` | none, none |

The three floorplan warnings:
- U5's /VIN rail has no decap anywhere on the board; that is how the input is.
- U8's pin rows face the board edges, which is the design.
- In the U7 template, C27 is 0.60 mm off its template pose.

The 33 subtracted KiCad items are U8's own castellated hole pairs.

`blocking_by` is 0 in every graded component (assembly, broken, drc, drc_via_in_paste, floorplan, undersized, unrouted). Diff pairs, impedance, length and net widths are ungraded.

**Quality:** 173 vias, 929.26 mm of copper, 1068 segments, joins_needed 0.

`grade.py --mode full` returns `done: true`, blocking/unrouted/broken/drc all 0, the same quality numbers, check_complete DONE, assembly buildable, 0 floorplan errors (in `grade_output.txt` and `grade_delivered.json`). Its `check_complete_authored: UNSOUND` is the floor disclosure in section 4, not a defect the DONE graders missed.

Other measurements, none of them blocking:
- **Redundant copper loops** (`check_cycles`): `/RP2354A/1V1` and `/T8F49I2X/PIN.22` (5 independent loops in total). This is extra copper, not an open or a DRC item.
- **USB intra-pair skew** (the verifier measured it; nothing declares a limit): `/RP2354A/USB_D±` 10.18 mm, `/Power Supply and USB/D±` 1.25 mm. This is full-speed USB, so it does not matter.
- **Mechanical facts:**
  - U8 is exactly at (148.500, 105.005, 270).
  - J1 is on the north edge, facing north.
  - J1's body overhangs the edge by 0.995 mm, inside the declared 0.99–1.05 mm band.

## 2. Groups, intent rows and judgement calls

The board is a Teensy-4.0-format carrier: 17.78 × 35.81 mm, 6 copper layers, 61 parts, 101 nets. U8 is the Teensy40 pin frame, with castellated rows on the long west and east edges and a short row on the south edge; the intent's `fixed_poses[]` seats it. J1 (USB-C) is declared on the north edge.

`groups.json` has 6 groups, with every unseated part in exactly one:

| Group | Parts | Anchor; near | What it is |
|---|---|---|---|
| usb_in | J1 U3 R1 R2 D2 | J1; power, core | USB-C, CC pull-downs, flow-through ESD array, VBUS Schottky |
| power | U7 L2 C26 C1 C27 U5 R11–R13 U4 C3 | U7; usb_in, core, fpga | 5 V rail and what is made from it: TPS62162 buck to +3V3, TPS7A2011 LDO to +1V1, LM73100 ideal diode from VIN with its UVLO/OVLO divider |
| core | U6 C7–C13 L1 C6 C28–C30 C5 R3 Y1 C14 C15 R4 R5 J2 J3 | U6; usb_in, psram, fpga, power | RP2354A, its decaps, its on-chip DC-DC parts, the 12 MHz crystal, the USB 27 Ω pair, and two back-side connectors |
| psram | U1 C2 | U1; core | PSRAM and its decap, both on the back |
| fpga | U2 C16–C25 Y2 R6 RN1 RN2 | U2; core, ui, power | Trion T8 FPGA (WLCSP-49), its decaps, the 32 MHz oscillator and its enable pull-down, the pull-up arrays |
| ui | D1 R7 R8 R9 SW1 | D1; fpga | RGB LED with its resistors, and the button |

Judgement calls:
- **U4 (+1V1 LDO) and C3 sit in power, not with the FPGA.** The lessons say to place a regulator by its input, between the entry and its loads, so I kept it there with a `near fpga` hint.
- **R4/R5 (USB 27 Ω) sit in core.** On an RP2040 or RP2350 this pair usually sits at the chip.
- **J2 (SWD Tag-Connect) and J3 (I2C JST-SH, side-entry) sit in core,** because both wire only to U6. No edge can take J3:
  - the west and east edges are the castellated rows;
  - the south edge has the 15–19 pin row;
  - the north edge has J1's shell legs.

  The brief declares no edge for J3, so it was placed freely.
- **SW1 stays in ui** despite `check_groups`' warning that its only link is to the FPGA, because it is user interface. It has no edge hint because it is top-actuated.
- **EMC rows:** none were given. `board_context` proposed two `keep_away` rules (the regulator switch nodes against the Y1/Y2 clock nets, at a default 3 mm); I did not declare them.
- **Mechanical facts:** used exactly as given (U8's pose, J1's edge).

`intent_run.json` is `intent.json` plus the rows below; nothing else was added, and `waive_locked_overlaps` found 0 pairs.
- **J1 `overhang_mm` {0.99, 1.05} and `mating_face "+y"`.** In the HRO TYPE-C-31-M-12 recommended PCB layout (LCSC C165948), the PCB edge is 5.79 mm from the rear shell-leg centre line. That puts the edge at y = +2.66 in the footprint frame, while the body front is at +3.65, so the body overhangs by 0.99 mm.
- **Templates for U7 and U6** (section 3).
- No `overlap_waivers[]` or `proximity[]` rows were added.

## 3. Templates (§3.5)

**U7, TPS62162 buck.** Source: TI SLVSAM2E (May 2017), §11.1 layout guidelines and §11.2 Figure 42.
- **Frame:** the footprint has the figure's pin layout, so no turn and no mirror.
- **Members:**
  - C26 is the input cap, on the −x side across VIN and PGND.
  - L2 is on the +x side, turned 90°, with its switch pad level with pin 7.
  - C27 is the output cap, on the −y side: its output pad sits on L2's output pad and its ground pad next to C26's ground.
- **Fit:** legs 1.20, 0.75 and 1.26 mm; ground returns 0.60 and 0.72 mm.
- **C1 is left out:** it is the 5 V bypass/LDO input cap, held by the decap rule.
- **Drift on the delivered board:** C27 0.60 mm, the others 0.

**U6, RP2354A on-chip DC-DC.** Source: Raspberry Pi "Hardware design with RP2350" §2.1, Figures 3 and 4 (the Pico 2 regulator layout).
- **Frame:** no turn and no mirror.
- **Members, in order:**
  - C13, the regulator input cap, across pins 49 and 47.
  - C6, the 1.1 V output cap, stacked beyond C13.
  - L1 beyond both, turned so its polarity pad (pad 1, the 1.1 V side) is on −x, as the guide insists.
  - C5 and R3, the VREG_AVDD RC filter, at the +x/−y corner.
- **Fit:** legs 1.00, 1.60, 2.45, 1.49 and 0.40 mm.
- **Drift on the delivered board:** 0.00 mm (as drawn).

## 4. Stop rule, remaining blockers, floors

**Stop rule 1 (DONE)** was reached at 11:33Z on the first kept placement. I then spent a bounded effort on vias until 11:46Z. There are no remaining blockers.

**Floors.** `check_complete --authored-from <input>` reports UNSOUND for one reason: the via annular ring went from 0.1 to 0.05 mm.
- **Vias:** all 173 are 0.25/0.15 mm. That is the board's own minimum via size, but the authored 0.1 mm annular minimum cannot hold with that pair. The organiser set the floors from the source copper, so 0.25/0.15 is the human's own via.
- **Hole clearance:** the FPGA fanout's writeback lowered `min_hole_clearance` from 0.25 to 0.09 mm. NPTH walls are still held at 0.25.
- **Tracks and clearance:** signal tracks are 0.0762 mm (above the board's 0.075 minimum, below the Default class's 0.09); clearance is 0.09 mm.
- **Power widths:** 8 power nets shipped partly under their requested width, necked to 0.0762–0.35 mm at fine-pitch pads; they are listed in `final_route/s8_iter2.json` under `design_rules`.
- **Via-in-pad:** 116 vias sit in pads and are stamped filled and capped (IPC-4761 Type VII), which needs a fab note.

## 5. Silkscreen and fill

- **Silkscreen** (KiCad `--severity-all`): the routed board has 3 items:
  - one `silk_overlap` between U4's and C26's outlines;
  - two `silk_over_copper`, where U5's and U7's outlines are clipped by U8's pads 32 and 30.

  `beautify_labels` also gives 3: all 61 reference labels are hidden, so it moved nothing. The count did not drop, so I **kept `routed.kicad_pcb`**.
- **Fill:** `fill_for_delivery` ran: 2 filled polygons, net classes preserved, unconnected items (without a refill) 62 → 0.

## 6. Timeline and where the time went (UTC)

| Time | Step |
|---|---|
| 11:13–11:18 | Read the skills and the board; wrote groups; ran check_groups and check_floorplan |
| 11:18–11:23 | Datasheets through a PDFKit helper; fitted the two templates; set J1's overhang |
| 11:23–11:25 | place_simple pass 1, 12 seeds: every seed carried a decap_distance error |
| 11:26–11:28 | Repaired s9 by hand (first legal placement); its fast route: blocking 1, 165 vias |
| 11:29–11:31 | Power widths; plan and `route_plan_check`; full chain left FPGA.~STATUS broken |
| 11:31–11:33 | `check_reachability` said PASSABLE; a rip lap failed; a grid-0.05 lap gave the **first DONE** (175 vias) |
| 11:34–11:41 | Repaired and judged seeds 7, 6, 2 and 4 (all worse); routing arms B (worse), C (qfn_fanout on U6, 170 vias), E (worse) |
| 11:38–11:45 | Removed C17's courtyard overlaps that KiCad grades as errors; routed C17 variants (178, 184 and 174 vias) |
| 11:45–11:46 | Final chain in `final_route/`: DONE, 173 vias |
| 11:46–11:49 | Verification, label tidy, fill, delivery |
| 11:49–11:54 | Verifier, grade, ledger close, measure |

Placing and routing are fast on this board: a full routing chain takes about 50 s. Most of the time went to judgement (groups, two datasheet templates), the seed repairs that §3.6 forced, and routing noise after DONE: a 0.05 mm move of one 0201 cap swung the via count between 174 and 184.

## 7. Placement passes, seeds and the routing chain

**One pass,** default arguments (`place_args []`), intent `intent_run.json`.
- `judge.json` named seeds 9, 6, 2, 3, 7 and 4, every one with a floorplan error.
- **Kept seed 9 (clustered).**

**Fast routes of the judged seeds:**

| Seed | blocking | joins_needed | vias | copper_mm |
|---|---|---|---|---|
| 9 | 1 | 1 | 165 | 926 |
| 7 | 1 | 1 | 195 | — |
| 6 | 3 | 3 | 160 | — |
| 2 | 3 | 3 | 173 | — |
| 4 | 3 | 3 | 177 | — |

Seed 3 could not be repaired: `place_pose` refused every pose for C5 because each one stacks on C7. Seeds 2, 4, 6, 7 and 9 were repaired in place; their pre-repair files are in `old/s*_as_placed.kicad_pcb`.

**Hand moves on the kept seed** (recorded in CHOSEN.json `after`):
1. C17 `--near 153.4 112.7`, to bring it within the 1.3073 mm decap limit of U2 (it was 1.51 mm).
2. C17 to (154.0, 112.45), to clear its courtyard overlaps with U2 and Y2.
3. C17 to (153.95, 112.4), the final pose: the courtyard-clean pose that routed best.

**Routing chain shipped** (`final_route/redo_commands.sh`, `board_plan.sh`, `board_plan.json`):
1. **Pours:** GND on In1, +3V3 on In2 (inner-only pours, because the board is in the standard density tier).
2. **FPGA (U2) fanout:** via-in-pad at 0.25/0.15 mm; 30/30 balls escaped, 0 grazes.
3. **RP2354A (U6) fanout:** stubs; 33/33 escaped.
4. **Decap pass:** 2 caps moved, decap limits held.
5. **route_diff:** both USB full-speed pairs are shorter than its 3 mm coupling floor, so it left them single-ended and `route.py` routed them.
6. **route.py `*`:** track 0.0762, clearance ceiling 0.09, vias 0.25/0.15, layer costs 1/6/2.5/1/1/1, max-ripup 5, power widths below.
7. **Two iteration passes:** the first one closed `/T8F49I2X/PIN.6`.

**Power widths** (analyze-power-nets by hand, because the tool's own output was unusable; see tool gap 3):
- 0.7 mm: GND, +3V3, Net-(D2-K), /VIN, Net-(D2-A), Net-(U7-SW).
- 0.5 mm: +1V1, /RP2354A/1V1, Net-(U6-VREG_LX).
- 0.3 mm: VREG_AVDD.
- **The currents are my estimates:** RP2354A 150 mA, T8 FPGA 60 mA, PSRAM 30 mA, Qwiic port 50 mA, LED 15 mA, oscillator 5 mA. I found no published current figure for the T8.

**High-speed scan:** medium tier at most, so no GND-via tail. There is no impedance spec, and the stackup is KiCad's default.

## 8. Tool gaps (details and repro commands in TOOL_GAPS.md)

1. `place_simple` left a decap_distance error in all 12 seeds, so §3.6 judges one seed; there is no decap-repair tool.
2. `route.py` boxed in a net that `check_reachability` called PASSABLE, and never tried the grid-0.05 lap that closed it.
3. `analyze_power_paths` charges a sink once per power pin and adds the source's rating on top.
4. There is no PDF renderer on this machine (poppler is absent); I wrote the helper `helpers/pdftool.swift`.
5. `place_pose` and `check_assembly` passed two courtyard overlaps that KiCad grades as errors.
6. `manifest_to_plan` rejects the plain `> log 2>&1` redirect the skill tells you to use; I converted `redo_commands.sh` instead.
7. `check_floorplan` names the nearest rail chip (Y2, or U1 on the other face) as "the IC it decouples".
8. `route_diff` says terminal pads were "far-apart" and peeled, when it routed the pairs single-ended for being short.
9. The `quick_score` payload has no board_sha, so the ledger cannot verify it.
10. A bare `kicad-cli` is not on PATH on macOS.

## 9. Verifier

There was one verifier (one subagent, one call). Its verdict is **`VERDICT=PASS`** (`verdict_1.txt`; the lens files `verdict_1_connectivity.txt`, `verdict_1_drc.txt` and `verdict_1_spec.txt` all PASS).
- **Identity and rules:** sha256 matches; graded at clearance 0.09.
- **Assembly and placement:**
  - `check_assembly` buildable; no gating off-outline or mating-keepout parts.
  - `check_floorplan` 0 errors.
  - The render's off-outline checklist has no gating pad, graphic or keep-out copper.
  - U8's pose matches exactly, and J1 faces north with a 0.995 mm overhang.
- **Routing:**
  - `board_score` blocking 0; `check_complete` DONE; the authored-floors run is UNSOUND (annular 0.1 → 0.05; `min_hole_clearance` 0.25 → 0.09).
  - `check_connected` all connected.
  - `check_drc` 0 violations; 116 via-in-paste, all filled and capped.
- **Declared classes:** UNEXAMINED: diff pairs, impedance, length, net widths. None is declared, so this is not a FAIL.

## 10. Ledger and hand-back

**Ledger:** `ledger.jsonl` has 21 rows and is closed with `--final --stop-condition 1` and the three lens files.

**Run records:** `CHOSEN.json` (seed 9, clustered, pass 1, `intent_run.json`, `place_args []`, three C17 moves), `placed_from/` (`fixed.kicad_pcb` with its `.kicad_pro`, `groups.json`, `intent_run.json`), `final.kicad_pcb`, `routed.kicad_pcb`.

**Delivered board:** `delivered.kicad_pcb` with `DELIVERED.sha256` and `DONE`.

**Other files:**
- `final_route_old1/` and `final_route_old2/`: the superseded routing chains.
- `arms/` and `laps/`: exploratory routes; they were not recorded in a manifest.
- `measure_output.txt`: the `measure.py --self --evidence` output.
- `datasheets/` moved to `old/datasheets/` for you to delete.
- Input sha256s re-checked: all match the README.
