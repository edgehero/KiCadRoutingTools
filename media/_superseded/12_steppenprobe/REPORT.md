# REPORT: board 12, steppenprobe (`/plan-pcb-placement full`)

**Result: DONE.** `wk/gpm/12_steppenprobe/delivered.kicad_pcb`, sha256 `ee65591b183de86d3cc4c04e7e9557d0b9f0cd765c30d097618da9b0223597b6`.
- Worktree: `~/Documents/git/krt-gpm`, upstream main at bda59fa0.
- The board is an FT2232HL USB debug probe: 50 x 60 mm, 2 layers, 84 parts and 84 nets.
- It started as a pile with no copper. The board-wide pours (+3V3 on F.Cu, GND on B.Cu) were kept.

I followed both `/plan-pcb-routing` (§3.8) and `/analyze-power-nets` by hand from their SKILL.md files.

## 1. Result

| DONE condition (full mode) | Measured on delivered.kicad_pcb |
|---|---|
| board_score blocking (with `--intent intent_run.json --net-min-widths power_min_widths.json --baseline steppenprobe.kicad_pcb`) | **0** |
| unrouted / broken / joins_needed | 0 / 0 / 0 |
| net_widths (Power net class 0.3 mm on +1V8, +3V3, +5V, /VPHY, /VPLL, GND, VBUS, Vdrive) | 0 failing. All 411 power segments are ≥ 0.3 mm (the verifier counted them independently) |
| check_complete (same flags) | **DONE** |
| check_complete `--authored-from` (report only) | DONE; no floor listed. The delivered .kicad_pro is byte-identical to the input's |
| check_connected | all nets fully connected |
| check_drc `--clearance-margin 0.1` | no violations |
| kicad_drc_compare | consistent; connection_width 0; starved_thermal 0 |
| KiCad DRC of the stored fills under the original project | no clearance, hole_clearance, edge, short or hole-to-hole errors; 0 unconnected. 28 solder_mask_bridge, all between J1's own pads and present before routing |
| check_assembly `--baseline` | buildable, blocking 0 |
| check_floorplan `--intent` | 0 errors, 0 warnings |
| orphan stubs / check_weird / check_cycles | none / none / 0 loops |

- **`blocking_by`:** every component is 0: assembly, broken, drc, drc_via_in_paste, floorplan, net_widths, undersized, unrouted.
- **UNEXAMINED** (nothing declares them): diff_pairs, impedance, length.
- **Quality:** 140 vias (all 0.6/0.3, the board's floor); 1323.85 mm of copper (F.Cu 602, B.Cu 722); 877 segments; minimum track 0.15 mm.
- **grade.py:** `{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 140, "copper_mm": 1323.85, "segments": 877, "check_complete": "DONE", "check_complete_authored": "DONE", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`. Files: `grade_output.txt`, `grade_delivered.json`.
- **measure.py `--self --evidence`:** wall 2:05:07; 353 tool calls; 2 agent spawns (`measure_output.txt`).

**Mechanical facts:**
- H1-H4 sit exactly at the mechanical.json poses (104,54), (104,106), (146,54) and (146,106), rotation 0. They were seated through `fixed_poses[]`.
- J1 is at (137.2123, 56.06), rotation 180, on the north edge, facing out.
  - Its F.Fab body reaches **2.55 mm** past the edge; the GCT drawing gives 2.51.
  - Its "PCB Edge" marker lands 0.04 mm past the outline.
- SW1 is on the west edge with its actuator facing out. The tip is 0.25 mm inside the edge.

## 2. Inputs, intent rows and judgement calls

**Intent rows.** `intent.json` was used as given. `intent_run.json` is its copy, used for every later step. Rows I added to it:
1. **J1 overhang band, `overhang_mm` {2.51, 2.60}.**
   - Source: GCT USB4085 drawing rev B sheet 2. The PCB edge is 1.74 mm past the rear shield slot, at the footprint's own "PCB Edge" marker.
   - **Removed after placement.** check_floorplan cannot measure the band on this rounded outline (TOOL_GAPS #1).
   - J1 was instead seated to the drawing with `place_pose` (CHOSEN.json `after`), and its overhang was measured by hand.
   - `placed_from/intent_run.json` keeps the version the pass read, with the band. `old/intent_run_with_J1band.json` is a copy.
2. **`fixed_poses[]` for the three fiducials:** FID1 (111, 53.5), FID2 (139, 106.5), FID3 (111, 106.5), basis `derived_default`. No declaration names them, so this is a judgement: an L near the corners, about 3.5 mm in, clear of the holes.
3. **(Pass 2 only, reverted.)** J4 as an edge connector on the east edge with `mating_face` +x.

**Other inputs:**
- **EMC rows:** none were given and none were invented. emc_roles found only crystal Y1, with no switch node and no keep_away rows.
- **Templates:** none. There is no switching stage (U2 is an XC6206 LDO, and the FT2232H's regulator is an internal LDO) and no RF. check_groups printed no hints.
- **Spec file I wrote:** `power_min_widths.json`, the input project's Power class at 0.3 mm. The first verifier failed the board until this was graded (D3).

**Groups** (`groups.json`, 7 groups):
- `usb_in`: J1, R1/R2 (CC 5k1) and U3 (SRV05-4 ESD).
- `power`: FB1, U2, C1 and C2. Near usb_in and core; no edge.
- `core`: U1 FT2232HL with:
  - Y1, C3 and C4;
  - C7 and C10-C12 on +1V8;
  - C13-C16 on +3V3;
  - the VPLL filter FB2/C5/C8 and the VPHY filter FB3/C6/C9;
  - R4, R6, TP1 and TP2.
- `eeprom`: U4 93LC46B, R3, R5 and C18.
- `target`: J4, J2, U5-U12, R11-R16, R19, R20, R22, R23, R25, C17, C19-C22 and SW1. Hint `edge: S`, which never moved J4 to the edge (TOOL_GAPS #5).
- `reset`: Q1, R24, R17 and SW2.
- `leds`: D1-D6 with their resistors. Hint `edge: E`.

Judgement calls inside the groups:
- C18 goes to the EEPROM and C22 to the read-back buffers: six +3V3 100 nF caps serve nine +3V3 pins.
- R17 stays with the reset circuit, despite a check_groups warning.

**Kept seed: pass 1, seed 2 (scattered).** CHOSEN.json `after` is the J1 move.
- The quick judge picked seed 1, then seed 3, with seed 2 last (blocking 4).
- Full routes ranked them the other way: seed 2 at 142 vias, seed 1 at 147, seed 3 at blocking 1 (TOOL_GAPS #11).
- §1 says the routed board judges a placement, so I kept seed 2.

**Pass 2** (J4 declared on the east edge) routed worse (183 vias, or blocking 1) and was rejected. Its files are in `old/pass2/`.

## 3. Stop rule and blockers

- **Stop condition 1 (DONE).** No blocker remains.
- **The first DONE** was routing arm B (154 vias). The first verifier call then FAILED delivered v1 on three defects:
  - **D1:** J1's body overhung only 0.338 mm, against the drawing's 2.51.
  - **D2:** the fill sat 0.1505 mm from the NPTH holes, against the authored 0.25.
  - **D3:** the Power net class was ungraded.
- **The fixes:**
  - J1 moved north 2.21 mm.
  - The chain runs with `--no-fix-drc-settings`, so the project keeps 0.25.
  - The 0.3 mm power class is graded and met: power nets routed first at exact 0.3, then the signals, then power again.
- The second verifier call PASSED.

## 4. Routing (`/plan-pcb-routing`, by hand)

**Board and analysis:**
- Step 0: buildable. Baseline unrouted 59, broken 62.
- Stackup: a 1.51 mm core at εr 4.5. USB HS 90 Ω would need a 1.133 mm leg against a 0.15 mm pin gap, so it is **not achievable** and no impedance pass was run.
- U1 is a perimeter LQFP-64 at 0.5 mm pitch, so no fanout step. The board is the STANDARD tier, not DENSE.

**`/analyze-power-nets`:**
- Classification (estimates are marked):
  - J1: source, 500 mA, estimate;
  - U2: source, 200 mA;
  - U1: sink, 70 mA (distributor figure);
  - buffers: 5 mA each, estimate;
  - LEDs: 2 mA each;
  - J4: 100 mA, estimate.
- The tool's widths (GND 2.0, +3V3 1.0, ...) over-count, per power pin (TOOL_GAPS #8). I first used 0.7/0.5/0.3. The shipped board uses the Power class's **0.3 mm** for all 8 power nets, which carries the ≤ 250 mA these rails see.

**No GND-via or stitching tail.** USB HS is the only high-tier net. On this board the F.Cu pour is +3V3, so a GND via's top end would be an island. No keep-away rules (no clock or switch-node near analog circuitry).

**Shipped chain** (`final_route/`, manifest `final_route/redo_commands.sh`; `plan/final_plan.sh` passes route_plan_check 17/17; GUI form `plan/final_plan.json`):
1. `route_planes --nets +3V3 GND --plane-layers F.Cu B.Cu --min-thickness 0.15 --no-fix-drc-settings`.
2. `route_diff --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --escalation board`.
3. `route.py --nets <8 power> --power-nets … 0.3×8 --track-width 0.3 --escalation off`, plus the same clearance, pad-clearance, no-fix and layer-cost flags.
4. `route.py --nets '*' !<8 power> --escalation board`, run twice.
5. `route.py --nets <8 power>`, exact 0.3 again.

Older chains are kept in `final_route_old1/` (recipe G) and `final_route_old2/` (recipe F).

**Routing arms, summarised** (all in `arms/`; every one is in the ledger):

| Arm or step | Board | Change | Result |
|---|---|---|---|
| A | pre-J1-move placement | default layer costs | 167 vias, dangling stub |
| B | pre-J1-move placement | `--layer-costs 1.0 1.5` | first DONE, 154 vias; clearance descended to 0.1442 |
| D | pre-J1-move placement | + `--escalation board` | 160 vias; 82 vias in pads |
| F | pre-J1-move placement | + `--same-net-pad-clearance 0.1` | 150 vias |
| full routes | pre-J1-move placement | the three judged seeds | seed 2 best at 142; +1V8 loop fixed by force-reroute |
| G | pre-J1-move placement | `--min-thickness 0.15` | 140 vias, 1400 mm (delivered v1) |
| K, L, M, N1, N2, K4-K8, P1-P5 | J1-moved placement | various width strategies | each failed on width or connectivity |
| P6 | J1-moved placement | power-first chain | DONE, 140 vias, 1323.85 mm (shipped) |
| Q | J1-moved placement | P6 with route_diff writeback | keeps the USB pair coupled; 1330 mm and needs min_hole_clearance restored; not kept |

**Floors:**
- No copper is below the authored floors: clearance 0.15, track ≥ 0.15, vias 0.6/0.3, min_hole_clearance 0.25.
- The project is unchanged from the input.

**Known shortfall: the USB pair.** It is ungraded and reported:
- route_diff routed it coupled (31.3 mm).
- Without the protected-nets record (`--no-fix-drc-settings`), the later steps re-routed it single-ended: DP 42.96 mm with 2 vias, DM 38.76 mm with 5 vias (TOOL_GAPS #4).

## 5. Silkscreen, fill

- **Silk:** `beautify_labels` placed 66 labels (U8's label was left unchanged).
  - KiCad silk before: edge 3, over_copper 37, overlap 38 (78 in all).
  - After: edge 2, overlap 7 (9 in all).
  - **The labelled board was kept.**
- **Fill:** `fill_for_delivery` ran on `labelled.kicad_pcb`: unconnected without refill went from 53 to 0, and the net classes were preserved. The fills honour the 0.25 hole clearance.

## 6. Timeline (CEST; FIRST_CMD 11:06:41)

| Time | Step |
|---|---|
| 11:07-11:14 | Read the skills (plan-pcb-routing is 3570 lines) |
| 11:14 | Brief/context, the USB4085 drawing, intent_run, groups |
| 11:15 | Pass 1 (12 seeds, about 12 s each) |
| 11:16-11:18 | Judged seeds 2, 3 and 1 |
| 11:18-11:26 | Routing arms A-F (one lap lost to zsh word-splitting, TOOL_GAPS #12) |
| 11:27-11:31 | Pass 2 |
| 11:31-11:41 | Full routes of the other seeds, +1V8 fix, recipe G |
| 11:42 | Delivered v1 |
| 11:43-11:56 | Verifier 1: FAIL |
| 11:57-13:05 | Fixes: J1 move, hole clearance, power widths (about 15 arms, 2 helpers) |
| 13:05-13:10 | Shipped chain, delivered v2 |
| 13:10-13:16 | Verifier 2: PASS |

Where the time went: reading about 8 min; placement about 3 min; routing arms and width work about 75 min; verifiers about 18 min.

## 7. Tool gaps

`TOOL_GAPS.md` has 15 entries; the top three are in the summary above.
- **Helpers:**
  - `helpers/widen_power.py` widens power segments only where check_join passes the result.
  - `helpers/find_tap.py` searches stub-and-via joins.
  - Neither touched the shipped board.
- **Tools that said "fine" about something that was not:**
  - check_floorplan's "J1 overhang 2.5149 pass".
  - `check_complete --authored-from` DONE over a relaxed `min_hole_clearance`.
  - route.py's "confirmed connected by the oracle" on an islanded +3V3 pad.

## 8. Verifier verdicts

- **verdict_1: FAIL.**
  - D1: J1 overhang 0.338 mm against the 2.51-2.60 band.
  - D2: zone fill 0.1505 mm from 12 NPTH hole/layer pairs, against the authored 0.25.
  - D3: the Power net class was ungraded.
  - Lenses: connectivity PASS, drc FAIL, spec FAIL.
- **verdict_2: PASS.** Every gate is clean and the identity checks out. 411/411 power segments are ≥ 0.3. J1 body 2.55 mm past the edge; the hole clearance holds on the stored and refilled fills. Lenses: connectivity, drc and spec all PASS.
  - Non-gating notes: the USB pair is undeclared and uncoupled, SW1's actuator is 0.25 mm inside the edge, and the 28 mask bridges come from J1's own footprint.

## 9. Datasheets

- GCT USB4085 drawing (gct.co), used for the J1 overhang.
- A web search for FT2232H supply current (distributor figure, 70 mA).
- `datasheets/` was moved to `old/datasheets/`.
