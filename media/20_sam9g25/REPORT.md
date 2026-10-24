# REPORT — 20_sam9g25 (`/plan-pcb-placement full`)

**The board:**
- 111 parts: AT91SAM9G15 (BGA-217, 0.8 mm pitch), DDR2 (BGA-84, 0.8 mm), MCP16501 PMIC (QFN-24), RTL8188CUS WiFi module + U.FL, USB-C, microSD, and headers (2x18, 2x22, three 2x04).
- 246 nets, 4 copper layers, 66 x 42 mm.
- It started as a pile of parts with no copper.

**Skills followed by hand from their SKILL.md:** `plan-pcb-placement`; `plan-pcb-routing` (§3.8); `analyze-power-nets` (Step 4 of plan-pcb-routing asks for it).

## 1. Result

DONE. Delivered `delivered.kicad_pcb`, sha256 `c854a3ea650000edb6b5311f8b438a1f55cdb4166ea6fe357e5196d0c049b70c` (also in `DELIVERED.sha256` and `DONE`).

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| board_score blocking / unrouted / broken | **0 / 0 / 0** |
| check_complete | **DONE**. Unexamined: diff_pairs, impedance, length, net_widths (the board declares no spec for any of them). |
| check_assembly (baseline = input) | buildable; blocking 0; 0 parts with pad copper off-board |
| check_floorplan, intent_run.json | 0 errors; 3 pins_to_edge warnings (J1, J4, J7) |
| check_connected | all nets fully connected; the KiCad refill cross-check agrees |
| check_drc, --clearance-margin 0.1 | 0 violations |
| check_weird / check_orphan_stubs | clean / clean |
| kicad-cli pcb drc --refill-zones | 0 unconnected; 0 clearance, track-width or short errors |
| grade.py --mode full | `done: true`, blocking 0 (`grade_out/grade_delivered.json`) |

What kicad-cli still reports:
- 3 `solder_mask_bridge` errors on AE1. They come from the stock U.FL footprint's own mask rectangle and are inherited from the input.
- 1 `track_dangling` warning on VBUS at (110.1, 77.3). It is a T-joint onto VBUS's own track, so it is electrically joined.

`blocking_by` is 0 everywhere. diff_pairs, impedance, length and net_widths are `null` (ungraded).

Quality: vias 355, copper_mm 4076.04, segments 2491.

## 2. Groups and judgement calls

`groups.json` has 11 groups; check_groups reports 0 errors and 0 warnings.

| Group | Members | Anchor |
|---|---|---|
| core | U1; Y1/Y2 with C1–C4; C16/R14 (VBG bias); R2–R5, R15, R16 (39 Ω USB series at the MPU); decaps C100–C104, C15, C17–C23, C5–C7, C34, C36 | U1 |
| ddr | U200; C201–C213, C215; R17/R18 with C200/C217/C218 (VREF divider) | U200 |
| power | U2; L1–L3; C24–C27; C8–C14; C11; R9/R10; R7/R8; Q1, D2 (power path); R1/R6; TP4, TP6–TP9; SW1 (power button) | U2 |
| usb | J2, U7, R12/R13, C33, R11, R25/R26 | J2 |
| wifi | U6, AE1, C912, C914 | U6 |
| sdcard | J1 | J1 |
| flash | U5, C38 | U5 |
| lcd | J6 | J6 |
| expansion | J3 | J3 |
| aux_headers | J4, J5, J7 | J4 |
| ui | SW2, C37, D4, R20–R22 | SW2 |

**Judgement calls in the groups:**
- **C34/C36 moved into core.** check_groups warned that no IC in their first group (sdcard) carries VDD-IO. There they would sit outside the decap term, while the grade still holds every VDD-IO cap within 5 mm of an IC to the 4.24 mm limit.
- **The power path and the power button ride with the PMIC.** D2, Q1 and SW1 (declared on the west edge, beside the USB-C entry) keep the PMIC next to its power entry.
- **U6 recorded as template `kind: none`.** It is a WiFi module with its own RF front end; AE1 sits directly on its antenna pad with nothing in between.

**Rows I added to `intent_run.json`.** `intent.json` is untouched; all six input sha256 values match the README.
1. **`templates[]` U2** (switching stage, 16 members). See the template section below.
2. **`edge_connectors[]` J6 east, `mating_face +x`.** Judgement: the 2x22 1.27 mm header is a through-hole wall with no room for a track between pins. With only a group `edge` hint it lay across the board interior in 6 of 12 pass-1 seeds.
3. **`edge_connectors[]` J3 north, `mating_face +x`.** Judgement: the 45.7 mm header can only lie along a 66 mm edge. The north edge is free from H4 to the NE corner; the south edge holds H1, H2 and SW2.
4. **SW1 and SW2 `mating_face +y`.** Added after the first verifier failed the board. The EVQP7C actuator is drawn on the footprint's local +y, and the facing check had stayed silent about it.

`waive_locked_overlaps.py` found 0 locked pairs and added nothing.

**Other judgements:**
- **J2's overhang band left at the emitted 0 (flush).** The footprint's own "PCB Edge" marker sits on the front of its fab body, which matches GCT's USB4105 drawing.
- **No EMC rows were given**, so none were invented: no proximity limits from `emc_roles`, no `keep_away`, and no `--keep-away` on any routing step.

### Template: U2 (MCP16501A)

- **Source.** Microchip MCP16501 datasheet DS20006388B (rev B, 2020): the Typical Application Circuit on p.3 and §4.1/§4.2. It has **no layout figure and no layout guidelines**. The template is built from the schematic's pin assignments and carries no `side`s.
- **Parts matched by net:**
  - Input caps: C24 (PVIN1 24 / PGND1 22), C25 (pins 7/9), C26 (pins 12/10), and C27 as the VIN bypass (pins 17/16).
  - Inductors: L1 on SW1 (pin 23), L2 on SW2 (pin 8), L3 on SW3 (pin 11).
  - LDO: C11 at LOUT (pin 18); R9 from LOUT to LFB; R10 from LFB to GND.
  - Output caps, two 10 µF per rail: C12+C8 (VDD-IO), C13+C9 (VDD_DDR), C14+C10 (VDD_CORE).
  - R7/R8 were left to the group: they sit on B.Cu and are shared with U1.
- **Fitting.** The first fit stranded C9 4.86 mm from the chip, which caused a `decap_ungraded` error in 7 of 12 seeds (TOOL_GAPS #9). The third fit names each second output cap as a partner of the first. Every output cap then sits within 2.4 mm of the chip, with ground returns of 0.61–2.70 mm.
- **Graded on the delivered board:** drift is 0.0 mm for all 16 members, and no ground return is over 3 mm.

## 3. Placement

**Pass 1** (12 seeds) was archived to `old/pass1/` before judging, because of the two input defects above (the stranded C9 and the J6/J3 edges).

**Pass 2** (6 scattered + 6 clustered, `place_args []`) placed seeds 11, 7, 1, 3, 0 and 5 buildable and floorplan-clean. I judged them with `judge_chain.txt` at `--quick 2`, `--jobs 2`, `KICAD_ROUTE_TRACE=1`:

| Seed | Start | Blocking | Joins | Vias | copper_mm | Segments |
|---|---|---|---|---|---|---|
| **11** | clustered | **2** | 2 | 381 | 3721.63 | 3776 |
| 1 | scattered | 5 | 5 | 478 | 4399.55 | 4597 |
| 0 | scattered | 6 | 6 | 477 | 4452.98 | 5447 |
| 3 | scattered | 9 | 9 | 473 | 4323.64 | 4457 |
| 7 | clustered | 14 | 14 | 450 | 4174.47 | 4368 |
| 5 | scattered | 20 | 20 | 519 | 4797.97 | 5444 |

**Seed 11 was kept.** It was then hand-repaired after verifier call 1, and the repair is recorded in `CHOSEN.json` `after`:
- `place_pose set SW1 102.1 67.053 --rot 270`
- `place_pose set SW2 128.9 97.9 --rot 0`

The previous kept placement is in `old/final_v1/`. During routing, `place_fanout_clearance` (Step 1c) moved 16 BGA decaps; the intent's decap gate held throughout (errors 0 → 0).

## 4. Routing (§3.8, plan-pcb-routing by hand)

**Step 0 gate:** buildable.
**Stackup:** real (FR408-HR prepreg 0.0994 mm, FR4 core 0.865 mm).

**Pours.** The board is STANDARD tier (4 layers), so pours are inner-only:
- GND solid on In1.
- VDD-IO, VDD_DDR and VDD_CORE split on In2.
- The designer's two hatched F/B GND zones were kept as drawn.

**Fanout:** `bga_fanout --escape-method dogbone` on both BGAs, with escapes forbidden on the inner layers. U1 escaped 133/133 balls and U200 45/45.

**Power widths (analyze-power-nets).**
- Its recommendations were unusable: GND 3.0 mm, VDD-IO/VDD_DDR 2.0 mm, and no width at all for VIN or VBUS (TOOL_GAPS #8).
- Currents for U1, U200, U5, J1 and J6 are my estimates. U6's 170 mA is from vendor module sheets.
- Widths used: GND, VDD-IO, VDD_DDR, VDD_CORE 0.3 mm; +1V0_LDO 0.25 mm; VIN and VBUS 0.5 mm.
- Some copper shipped narrower than the requested width (BGA taps and necks): GND 145 mm of length, VDD_DDR 36, VDD_CORE 15, VIN 12, VDD-IO 6, +1V0_LDO 2.5, VBUS 0.

**Chains.** Each ran in its own folder; `final_route/` holds the one shipped.

| Chain | What changed | Result |
|---|---|---|
| v1 (`final_route_old1/`) | the recipe as planned | blocking 1. U1.C13 (`ddr-d11`) lost its escape when the route step ripped it (TOOL_GAPS #7). check_reachability: passable on the placement, caged by the routing. |
| arm rA | adds `--ripped-route-avoidance-cost 3 --track-proximity-cost 2` | 0 open, but an RMII-TX0 × VDD-IO crossing short (TOOL_GAPS #4). Fixed by `--force-reroute RMII-TX0 LCD-D10`; dangling ddr-ck vias fixed by force-rerouting that pair. First DONE: 527 vias. |
| v3 (`final_route_old3/`) | via cost 1200 | 373 vias. Verifier call 1 FAILED it on three defects: SW1/SW2 facing along their edges; 11 impedance declarations ungraded; 20 KiCad `track_width` errors inside the BGA courtyards. |
| v4 (`final_route_old4/`) | SW1/SW2 repair; pairs routed without `--impedance`; DDR clock glob narrowed to `[+-]` (it had wrongly matched `ddr-cke`) | 26 `track_width` errors remained |
| **v5 = shipped** | v4 + `--fab-overrides helpers/fab_track_floor.txt`: the advanced tier's via and clearance floors, but the track floor held at 0.1016 mm | **DONE, 355 vias.** `route_plan_check` 17/17 OK; `redo_commands.sh` recorded. |

Why `fab_track_floor.txt`: with `--escalation off`, a lap was reverted; with `--escalation board`, an arm left 3 DDR nets open. The override file was the only setting that kept tracks at 0.1016 inside the courtyards and still routed everything.

**Hand copper removal on the shipped board.** No CLI can remove a dead-end stub of a poured net (TOOL_GAPS #6). I removed two GND F.Cu stubs with `helpers/drop_segment.py`:
- (125.3, 67.3) – (126.4, 67.3)
- (124.8, 91.0) – (125.0, 91.2)

Both ended in the 1 mm gap between the designer's two hatched GND zones. After the removal I re-ran check_weird, check_connected, check_drc, board_score, check_complete and kicad-cli; all clean.

**Search for fewer vias after DONE.** Done in `arms/`, at the v3 settings:

| Lever on the route steps | Vias |
|---|---|
| via cost 150 | 473 |
| via cost 300 | 420 |
| via cost 600 | 377 |
| via cost 1200 | 368 |
| via cost 2400 | 371 |
| auto escape (via cost 75) | 540 |
| auto escape (via cost 1200) | 402, plus 1 DRC |
| topo bus step, `awx/route_bus.py` (41/41 lanes, 68 min), via cost 75 | 506 |
| topo bus step, via cost 1200 | 370 |

**Not done, by judgement:**
- **Length matching.** The board's `.kicad_dru` declares no length or skew rule, and the DDR netclasses carry no tolerance.
- **GND return vias / stitching.** This is an optional tail, and every via it adds works against the post-DONE objective.
- **Declared impedance.** The USB pairs are drawn at the stackup's 90 Ω geometry (0.171 / 0.1016 mm) and the DDR clock at 100 Ω geometry (0.139 / 0.1016 mm), but nothing is declared, because the input declares nothing.

**What you should know about signal quality** (the verifier's advisory findings; none of it is graded):
- The DDR clock pair is routed uncoupled.
- USB2 has 10.6 mm of path skew.
- 323.7 of 922.6 mm of USB/DDR copper runs over a void in its reference plane: inner-layer routing cuts the In1 and In2 pours.

## 5. Stop rule

**DONE was reached (stop condition 1).** After DONE, three different approaches in a row did not beat the best board I measured (368 vias): via cost 2400, auto escape at 1200, and the bus step at 1200.

I shipped 355 vias because the fixes for verifier 1 changed the chain:
- 355 is the v5 chain re-run in `final_route/`.
- The 368 board itself could not be re-run identically: identical inputs gave 368 once and 373 three times (TOOL_GAPS #5).

No blocker remains.

## 6. Floors

The chain was routed at `--clearance-ceiling 0.1016` (the board's own min_clearance and its `.kicad_dru` rules), track 0.1016 mm, via 0.45/0.3. The fab escalation then descended for clearance and vias, disclosed on each step's `Design rules [...]` line.

`check_complete --authored-from` the input reports **UNSOUND**. This is reported, not gating:

| Floor | Authored | Shipped |
|---|---|---|
| via diameter | 0.4 | 0.25 |
| via annular ring | 0.075 | 0.05 |
| hole | 0.3 | 0.15 |
| Default class clearance | 0.195 | 0.0987 |
| track width | 0.1016 | 0.1016 (held) |

These are the advanced fab tier; confirm the fab supports it before ordering. 101 vias sit in a pad or a paste opening and are stamped IPC-4761 Type VII (filled and capped).

## 7. Silkscreen

`beautify_labels` produced `labelled.kicad_pcb`. KiCad silk counts went from **133** (silk_overlap 53, silk_over_copper 74, silk_edge_clearance 6) to **29** (15 / 12 / 2), so the labelled board was kept.

## 8. Fill

`fill_for_delivery` ran with exit 0: 71 filled polygons, 10 net classes kept, and unconnected items without a refill went from 135 to 0. Do not route anything further from this board.

## 9. Timeline (UTC) and where the time went

| Time | Step |
|---|---|
| 10:58 | FIRST_CMD |
| 10:58–11:08 | read the skills and board, wrote groups, read the datasheet (PDF helper), template v1 |
| 11:08–11:13 | placement pass 1 |
| 11:13–11:19 | template v3, J6/J3 edge rows, placement pass 2 |
| 11:20–11:24 | judged 6 seeds (28–83 s each) |
| 11:25–11:45 | v1, laps, arms rA/rB, v2: **first DONE at 11:45** |
| 11:45–12:51 | post-DONE arms (the bus step ran 11:36–12:45 alongside) |
| 12:23–12:55 | v3 chain, labels and fill, repro runs, verifier call 1 (FAIL) |
| 12:59–13:23 | SW1/SW2 repair, v4, track-width arms, v5 |
| 13:23–13:32 | labels and fill again, verifier call 2 (PASS) |

`measure.py --self --evidence`: wall 2:35:04, waiting on jobs 3841 s, other tools 2583 s, model 2880 s, 321 tool calls, 2 verifier spawns. The longest single job was the experimental bus step (68 min).

## 10. Tool gaps

Twelve entries in `TOOL_GAPS.md`, ranked by what they cost:
1. The edge check passed SW1/SW2 with their actuators along the edge: its facing check abstained without saying so.
2. Courtyard-scoped `.kicad_dru` rules are invisible to route.py, check_drc and kicad_drc_compare; only kicad-cli sees them.
3. `route_diff --impedance` writes impedance declarations that board_score and check_complete never grade.
4. route.py shipped a crossing short and reported `failed: 0`.
5. The plane finalize diverged on 1 of 4 identical runs.
6. Dead-end stubs of a poured net can't be removed by any CLI (worked around with `helpers/drop_segment.py`).
7. A hint blamed the fanout for a ball the route step had ripped (the #1311 class).
8. analyze_power_paths traced 0 power paths and gave no width for VIN or VBUS.
9. fit_template placed a part past the intent's own decap limit without warning.
10. A group `edge` hint does not lay a long header along the edge.
11. Reading datasheet PDFs needs poppler, which is not installed (worked around with `helpers/pdftool.py`).
12. check_weird and KiCad disagree on a T-joint (`track_dangling`).

Tools that said "fine" about something that was not: #1, #2, #3, #4 and #9.

## 11. Verifier

- **Call 1 (`verdict_1.txt`): FAIL** on the board with sha256 `de85413c…`. Defects: SW1/SW2 actuators facing along their edges; 11 impedance declarations ungraded (graded, all 11 blocking; `ddr-cke` wrongly declared differential); 20 KiCad `track_width` errors against the `.kicad_dru` courtyard rules. All three were fixed as described above.
- **Call 2 (`verdict_2.txt`): PASS** on `c854a3ea…`. All three lens files pass (connectivity, drc, spec). It re-measured every mechanical fact: H1/H2/H4 are exactly at their declared poses, and J2, SW1 and SW2 face out of their declared edges. Its advisory findings are the skew, clock-coupling and reference-plane notes in section 4.

The ledger (`ledger.jsonl`, 32 rows) is closed with `--final --stop-condition 1` and the call-2 lens files. `old/datasheets/` is ready for deletion.

Everything is in `wk/gpm/20_sam9g25/`:
- `delivered.kicad_pcb`
- `TOOL_GAPS.md`
- `verdict_2.txt`
- `ledger.jsonl`
- `CHOSEN.json`
- `STATE.md`
