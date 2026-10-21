# REPORT: gp14 board 08, CM5_MINIMA_3 (`/plan-pcb-placement full`)

**Result: DONE.** The final board is `wk/gp14/08_CM5_MINIMA_3/final.kicad_pcb` with `final.kicad_pro`, sha256 `547516266702dff793d5047d6f55bf951e4b485288afe0a737a211ab60bd29f1`. It was placed from round 2, seed 3 (scattered start) and routed by `final_route/redo_commands.sh`. The independent verifier returned **VERDICT=PASS** (`verdict_1.txt`). Wall time from FIRST_CMD (22:53:39Z) to hand-back (00:20Z) was about 1 h 27 min.

## 1. Result

| DONE condition (full mode) | Measured on final.kicad_pcb |
|---|---|
| `board_score` blocking (`--impedance-nets`, `--intent intent_cm5.json`, `--baseline` input) | **0** |
| unrouted / broken | **0 / 0** |
| `check_complete` (same spec flags) | **DONE** (exit 0) |
| `check_connected` | all 95 routed nets connected; the KiCad refill cross-check agrees |
| `check_drc --baseline <input> --clearance-margin 0.1` | 0 violations |
| `check_assembly --baseline <input>` | buildable (blocking 0, courtyard gating 0) |
| `check_floorplan --intent` | 0 errors, 3 `decap_pin_uncovered` warnings |
| pad, graphic or keep-out copper off the outline (`render_placement`) | none |
| mechanical.json poses (10 parts) | exact: 0.000 mm and 0.000° (verifier) |
| `grade.py --mode full` (`grade/grade_final.json`) | `done: true` |

`blocking_by` is zero in every channel:
- unrouted 0, broken 0, drc 0, undersized 0
- floorplan 0, assembly 0, drc_via_in_paste 0
- impedance 0 (36 declared nets, 0 reference-plane crossings)

Length and net widths are not graded, because the board declares neither.

| Quality | Value |
|---|---|
| vias | **217** |
| copper_mm | **2962.33** |
| segments | **1794** |

**Spec flags used for DONE:** `--impedance-nets '/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*'`. These are the nets claimed by the project's `90ohm` and `100ohm` net classes.

The board's own minimums (via 0.45/0.3) are reported as floors in section 4, not passed as gating `--min-via-*` flags. This follows verifier.md, where `--authored-from` is report-only.

## 2. What I decided, and why

### Inputs I changed

All changes are in `intent_cm5.json` and `fixed.kicad_pcb`. The given brief, `mechanical.json` and `intent.json` are untouched; their sha256 still match.

- **EMC limits: none were given** (campaign rule), so there are no `proximity` limits and no `keep_away` rules. This matters for the buck stage; see section 3.
- **Mechanical poses.** All 10 mechanical.json parts are seated exactly and KiCad-locked in `fixed.kicad_pcb`.
  - H102–H105 and Module301/302 are removed from `fixed_poses[]`, because place_simple's declared-pose check refused them in every seed (TOOL_GAPS 2). H101, J701, M701 and M702 stay declared.
  - `overlap_waivers` cover two pairs:
    - Module301/Module302: one module drawn as two footprints with a shared origin, by design.
    - H102/J1: only J1's courtyard box overlaps; its drawn body is 2.3 mm clear of the hole.
- **J1 (Kycon GLPLX-SMT-188S7, a mid-mount RJ45 with magnetics).** Hand-placed and locked into the outline's NW notch at (89.08, 36.135, rot 270).
  - The footprint's cut-out rectangle (15.5 × 13.3 mm) matches the notch (15.79 × 11.11 mm), with the mouth 2.2 mm past the west edge. The datasheet calls it a mid-mount, board-edge jack.
  - Consequence: its shield tabs 15/16 sit 0.20 mm from the notch edges, against a 0.372 mm minimum copper-to-edge clearance. No pose clears both, because the two gaps total 0.407 mm, less than 2 × 0.372. KiCad's DRC reports these two; `check_drc` does not by default.
- **J501 (full-size HDMI).** South edge, mouth out, at (94.0, 72.0, rot 0), locked, directly south of Module302's HDMI pins. I first put it at x = 95.0, which pushed its courtyard 0.9 mm into my M.2 keep-out. That was my error; `check_floorplan` caught it and I fixed it for round 2.
- **J802 (camera FFC, Hirose FH12-22S).** East edge, rot 90, cable entering from the east. Hirose lists the FH12 actuator at the front, which matches the tool's +y mating face. The south edge is blocked by the M702 standoff.
- **SW501 (power button, side-actuated).** East edge, actuator out, at (130.5, 68.0, rot 0), locked. Placed by hand because the edge seat reported "no room" (TOOL_GAPS 7).
- **`edge_connectors[]` entries:**
  - J101 and USB701 (the two USB-C ports) on the west edge.
  - SW101 (nRPIBOOT button, side-actuated) and CN1 (RTC battery, side-entry) on the west edge **on B.Cu**. The CM5's 55 × 40 mm body covers x 90.75–130.75, y 26.1–81.1 on B (worked out from the module's mounting holes), so the west strip is the only place on B where a tall part or a button can be reached.
- **Keep-out `m2_card_F`** at [102.6, 31.0, 124.6, 72.5], F side only: the area under the M.2 2242 card. Tall parts may not sit there (L701 inductor, C702 tantalum, J502/J503/J601 vertical JST connectors, J802, SW501). Every low-profile part may.

### Groups

There are 12 groups in `groups.json`:

| Group | Members | Hint |
|---|---|---|
| usb_pwr_in | J101, ESD D101, bulk C701, bleeder R101, TP101 | |
| usb2_host | USB701, D701, power switch U701 + R701, C702/C703, CC pull-ups R702/R703 | |
| hdmi | J501, ESD D401/D402/D403, 5 V switch U405, C502 | |
| ethernet | J1, ESD U401/U402 (on B), LED resistors R401/R402, R403, C401 | |
| camera | J802 | |
| cm5 | Module301/302, +5 V decaps C101/C102/C501, R102/R103 (GPIO_VREF select), R104, test points | |
| m2_power | AP3441 buck U702, L701, input caps C704/C705/C706, output caps C708/C709, FB divider R705/R706 + C707, EN pull-down R704 | `near` m2_slot |
| m2_slot | J701, C710/C711/C712, 32 kHz oscillator U703, D702/R707 | |
| i2c_sensor | Qwiic J502 + ESD D502 + pull-ups R501/R502, LIS3DH U1 (on B) with C503/C601, R107/R108 | |
| gpio_conn | J503 SPI display, J601 fan | `near` cm5 |
| ui | SW501, inverter U602, R605/D605, R606/D606 | |
| b_west | CN1, SW101 | |

`check_groups` reports 0 errors. Its warnings that C701, C708 and C709 are "decaps of another group" are correct as written: C701 is bulk at the power entry, and C708/C709 are the buck's output caps.

### Rounds

- **r1_aborted** (12 seeds): every seed was "illegal" because of the declared holes and modules (TOOL_GAPS 2), so `judge.json` was empty. Nothing was judged; I repaired the inputs as described above.
- **r1** (12 seeds, 3 legal): seeds 7, 8 and 10 were judged with the judging chain.
  - The chain is `helpers/judge_chain.sh`: pour, CM5 via-in-pad fanout, cap clearance pass, `route_diff` 90 Ω and 100 Ω, `route.py`, all at `--quick 2`.
  - Seed 7's fast route had blocking 0 and 287 vias, but its locked J501 sat in the keep-out (my input error). I shifted J501 1 mm west and changed nothing else.
- **r2** (12 seeds, 9 legal): seeds 6, 7, 10, 3, 9 and 1 were judged.
  - Their fast routes had blocking 5, 0, 0, 0, 0 and 0. The best was s10 (0 blocking, 256 vias, 2774.7 mm copper).
  - A clean fast route stops the placement rounds (SKILL §3.6). No review round was needed, and `route_review` found no two-pad parts turned against their wiring.
- **After DONE**, I ran the full DONE chain on every clean r2 seed. Seed 3 routed better than seed 10 (237 vs 260 vias), so the shipped placement is **r2 seed 3**.
  - `CHOSEN.json` has `place_args: []` and `after: []`.
  - The routing chain's cap clearance pass (`place_fanout_clearance`) moved 1 capacitor.

### The full route (`final_route/`, manifest `redo_commands.sh`)

The chain, in order:
1. `copy_board`.
2. `helpers/drop_zone.py` removes the input's multi-layer GND zone (TOOL_GAPS 1).
3. `route_planes` pours GND on F/In1/In2/In4/B and +5V on In3 — the design's own pour map.
4. `qfn_fanout --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15` on both CM5 connectors, using lists of nets with at least two pads (TOOL_GAPS 6).
   - Module302: 37 nets.
   - Module301: 36 nets; MISO_GPIO19 did not escape and was left to `route.py`.
5. `place_fanout_clearance`.
6. `route_diff --impedance 90` (USB_C, USB2P, PCIe) and `route_diff --impedance 100` (Ethernet, HDMI, DPHY0), gap 0.13, 0.25/0.15 vias.
7. `route.py --nets '*' --via-cost 600`.
8. `helpers/clean_copper.py`, deletions only: 85 exact duplicate segments and 2 redundant 0.03 mm segments (TOOL_GAPS 3).

Every routing step also used:
- `--clearance-ceiling 0.13`
- `--layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0` (signals only on F, In2 and B)
- env `KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'`

**The layer map was the decision that got to DONE.** The first full route (the judging chain without `--quick`) had unrouted 0 and broken 0, but 28 impedance-controlled nets crossing gaps or splits in their reference plane. I then ran nine measured experiments:

| Experiment | Change | Impedance nets | Other blocking |
|---|---|---|---|
| v1 | skill's dense-board layer prices 1/6/1/2.5/3/1, via-in-pad fanout, duplicated GND zones | 28 | drc 1 |
| A | no fanout | 34 | 1 open |
| B | surface (stub) fanout | 22 | — |
| C | stub fanout, routing forbidden on In1/In3/In4 | 25 (all splits, 0 mm over a gap) | 1 open |
| D | keep the input GND zone (`--skip-existing-zones`), stub fanout | 8 | broken 2 |
| E | keep the input GND zone, via-in-pad fanout | 13 | broken 1, drc 1 |
| F | keep the zone, stub fanout, In1/In4 forbidden | 12 | broken 3, drc 1 |
| G | keep the zone, stub fanout, In1/In3/In4 forbidden | **0** | broken 2, drc 1 |
| H | fresh GND pour, stub fanout, In1/In3/In4 forbidden | 0 | broken 2 |
| I | fresh GND pour, via-in-pad fanout, In1/In3/In4 forbidden | 0 | drc 1 (route_diff GND vias, TOOL_GAPS 4) |
| I′ | as I, with 0.25 mm diff-pair vias | **0** | **0 → DONE** (seed 10, 260 vias) |

### Optimisation after DONE (vias, then copper, then segments)

| Trial | Vias | Copper (mm) | Verdict |
|---|---|---|---|
| s10, DONE chain | 260 | 2834.0 | first DONE |
| s3 / s7 / s9, same chain | 237 / 247 / 224 | — | s7 and s9 not clean (s7 drc 2; s9 drc 1 plus a dangling via) |
| s3, route.py via cost 250 / 600 / 1000 | 220 / **217** / 221 | 2961 / **2962** / 3081 | via cost 600 shipped |
| s3, route_diff via cost 250 plus route.py via cost 250 / 1000 | 210 / 193 | — | **rejected**: route_diff fell back to two uncoupled single traces on the DPHY0_P.D0 pair (TOOL_GAPS 5) |
| s9 / s10 / s1 with via cost | 204 / 205 / 236 | — | s9 and s10 not clean; s1 no better |

Via count flattened at 217–221 across three via costs and four seeds, so I stopped.

## 3. Stop rule and remaining issues

**Stop rule 1 (DONE)** fired. The via optimisation that followed flattened out. Nothing is blocking.

These weaknesses are measured on the shipped board; DONE grades none of them:
- **The M.2 buck stage is split.**
  - L701 sits 31.0 mm from U702's switch pin: U702 is in the SW corner, L701 at (111.9, 76.6).
  - The switch-node net `/PCIe-M2/M2_LX` is 36.4 mm long, and 29.5 mm of it is 0.1 mm wide (0.6 mm was requested).
  - The SSD supply `M2_3V3` narrows to 0.1 mm for 4.4 mm.
  - `route.py`'s current estimate is 0.45 A for both nets.
  - Every r2 seed had the same split (11–51 mm). The keep-out holds L701 out from under the M.2 card while U702 is allowed there, and with no EMC limit given for the inductor-to-switch-pin distance, nothing pulls the stage together.
  - This board needs that limit, or U702 also kept out from under the card, before it can power an SSD.
- **Skew within a differential pair** (verifier, pad to pad):
  - HDMI_PI.CK 21.5 mm and ETH_PI.TRD1 21.9 mm: the ESD part sits in one leg's path and on a branch of the other.
  - USB_C.D 5.2 mm, HDMI D1 4.5 mm, DPHY0 D0 2.8 mm.
  - All other pairs are 1.5 mm or less.
  - No length or skew spec is declared, so none was routed for.
- **Trace impedance next to the ground pour.** The F/B GND pours sit 0.10 mm beside the controlled traces, which were sized assuming no ground beside them. Measured impedance is 10–37% low; the worst is PCIE_PI.CLK_P at 32.8 Ω against 52.2 Ω single-ended.
- **GND return vias:** 28 of the 76 signal vias on the declared nets have no GND via within 2.25 mm.
- **J1 shield-tab edge clearance:** 0.20 mm against 0.372 mm. KiCad's DRC reports 2 copper-to-edge errors; this is inherent to the notch (section 2).
- **Floorplan warnings:** 3 `decap_pin_uncovered`, for Module301 pin 88 (+1V8), Module301 pin 78 (GPIO_VREF) and U702 pin 6 (switch pin).
- **Tall parts under the CM5 module** were handled only by assigning edges; nothing in the tools measures height.

## 4. Floors (where the run went below the board's authored or fab minimums)

- `check_complete --authored-from <input>` returns UNSOUND (report only):
  - via diameter 0.45 → 0.25, annular ring 0.075 → 0.05, hole 0.3 → 0.15. This affects 122 of 217 vias: 110 at 0.25/0.15 (the CM5 via-in-pad escapes and the diff-pair vias) and 12 at 0.30/0.15. These are JLC advanced-tier sizes.
  - copper-to-hole 0.2 is broken at 90 sites (0.15). The input board also breaks it.
- The project's net-class clearances were lowered to 0.1 mm (from Default 0.13 and 0.2 for the 90 Ω/100 Ω classes) by the chain's `--clearance-ceiling` and the fanout floors.
- The pour step relaxed `min_hole_clearance` from 0.2 to 0.13.
- `route.py` reports escalations to the advanced fab tier for plane taps.
- The CM5 via-in-pads are filled and capped (IPC-4761 Type VII); 104 vias are declared that way in the file.

## 5. Timeline (UTC) and where the time went

| Time | Step |
|---|---|
| 22:53 | FIRST_CMD; read the skills, brief and board context; looked up datasheets (RJ45, USB-C, FH12) |
| 23:03 | fixed parts seated, J1 into the notch; intent edges and keep-out; groups |
| 23:05 | r1_aborted: all 12 seeds illegal (declared-pose check) |
| 23:11 | r1 placed; 23:14–23:16 seeds 7/8/10 judged (seed 7 clean) |
| 23:17 | J501 keep-out error found; r2 placed; 23:19–23:21 six seeds judged; seed 10 kept |
| 23:21 | full route v1: 28 impedance nets |
| 23:25–23:44 | experiments A–I on impedance; zone duplication found |
| 23:45–23:50 | **first DONE** (seed 10, 260 vias) after the deletions-only cleanup |
| 23:50–00:09 | via optimisation; final route on seed 3 (217 vias) |
| 00:10–00:20 | verifier (PASS), grade.py, measure.py, TOOL_GAPS |

`measure.py --self --evidence wk/gp14/08_CM5_MINIMA_3` (`measure_stdout.txt`), taken at 1:25:19 of wall time:
- model 2355 s, tool calls 2425 s, waiting on background jobs 339 s;
- 248 tool calls, led by route.py 25, board_score 20, check_weird 20, route_diff 17.

Placement was cheap: about 30 s per seed, four at a time, and a judging route took 20–35 s. Most of the time went into diagnosing the impedance failure (TOOL_GAPS 1) and into the copper-cleanup and via trials.

## 6. Tool gaps

The full list, with reproduction commands, is in `TOOL_GAPS.md` (10 entries).

1. `route_planes` adds a second GND zone on every layer of a multi-layer input zone. Its own advice, "run those layers together", does not work. `check_impedance` then counts the overlap as plane splits, giving impedance 28.
2. `place_simple`'s declared-pose check calls the four corner holes "2.2 mm past the outline" (they are 0.4 mm inside) and calls the CM5 connector pair overlapping. Every seed was illegal and a round was wasted.
3. `route.py` leaves 50–87 same-net duplicate segments and some redundant tiny segments. `check_complete` rejects them, and no repo tool removes them (#162 open).
4. `route_diff`'s GND return vias break the 0.25 mm hole-to-hole minimum, even when that flag is given explicitly.
5. `route_diff` fell back to uncoupled single traces on a 100 Ω pair, and the DONE grade did not notice.
6. `qfn_fanout` escapes nets that have only one pad: 33 of 70 via-in-pads lead nowhere.
7. Edge seating ignores a declared `class`; the RJ45 and HDMI connectors are not recognised as connectors; and it reports "no room" on a free 44 mm edge.
8. The redo recorder does not record environment variables.
9. Skill instructions:
   - a declared pose that the placer refuses is a dead end;
   - there is no runner for the judging chain;
   - the skill's dense-board layer prices fail the impedance grade on this board;
   - DONE says nothing about power widths or the switch node.
10. `board_brief` on a pile reports staging positions as mechanical facts and points at operations that do not exist.

Places where a tool said "fine" about something that was not:
- Gap 1: `route_planes` says it is "keeping it … same net, so no short".
- Gap 5: `route_diff` exits 0 with an uncoupled lane, and the board grades DONE.
- The buck stage on the DONE board (section 3).

## 7. Verifier verdicts

**`verdict_1.txt`: VERDICT=PASS**, with connectivity, DRC and spec all PASS. It was one verifier call.
- It re-measured every gating check above and the 10 mechanical poses (0.000 mm).
- It reported, without gating, the authored floors and the findings in section 3: pair skew, ground-pour impedance, return vias and the J1 tabs.

## Files

All in `wk/gp14/08_CM5_MINIMA_3/`:

- **Final board:** `final.kicad_pcb` and `final.kicad_pro`, `FINAL.sha256`, `DONE` marker, `CHOSEN.json`.
- **Placement inputs:** `groups.json` (same as `r2/groups.json`), `intent_cm5.json` (same as `r2/intent.json`, the intent I placed with), `fixed.kicad_pcb`.
- **Rounds:** `r1_aborted/`, `r1/`, `r2/`. Each holds `fixed.kicad_pcb`, `groups.json`, `intent.json`, the `s<S>.*` files and `judge.json`; `r1/` and `r2/` also hold the judged seeds' fast routes.
- **Routing:** `final_route/` (manifest and every step), and the superseded chains `final_route_old1/` to `final_route_old3/`.
- **Records:** `ledger.jsonl` (closed, stop condition 1), `verdict_1*.txt`, `grade/`, `measure_stdout.txt`, `STATE.md`.
- **Tool problems:** `TOOL_GAPS.md`, `helpers/`, `repro/`.
- **Experiments:** `work/`.

No datasheet folder was created.
