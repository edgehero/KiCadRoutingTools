# REPORT: gp14 board 12, steppenprobe (`/plan-pcb-placement full`)

## 1. Result

**NOT DONE**: stop condition 3, plateau. `final.kicad_pcb`, sha256 `4c7c27a8998e93d5575f176c78e7d5c00d930d2ab4d214e68c3a60a9d12b9656`. Placed from round 2, seed 0 (scattered start), plus two decap moves.

All grades use the spec flags `--min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3 --net-min-widths widths.json`. `widths.json` holds the input project's KiCad-6 `Power` class: 0.3 mm for +1V8, +3V3, +5V, /VPHY, /VPLL, GND, VBUS and Vdrive.

| DONE condition (full mode) | measured |
|---|---|
| `board_score` blocking | **5** (all `net_widths`) |
| unrouted / broken | 0 / 0 |
| `check_complete` (spec flags) | INCOMPLETE (blocking 5) |
| `check_complete --authored-from <input>` | DONE; no relaxed floor listed (it does not grade widths) |
| `check_connected` | all nets fully connected (KiCad refill cross-check agrees) |
| `check_drc --baseline --clearance-margin 0.1`, graded at 0.15 | 0 violations |
| KiCad's own DRC (`kicad_drc_compare.py`) | KiCad 0 / check_drc 0, consistent |
| `check_floorplan --intent --allow-routed` | 0 errors, 1 warning (pins_to_edge on J2) |
| `check_assembly --intent --baseline` | buildable (blocking 0) |
| `check_weird` / `check_orphan_stubs` | clean / none |
| `grade.py` | done false, blocking 5, everything else clean |

**`blocking_by`:** net_widths 5; every other component is 0. Impedance and length are UNEXAMINED because the board declares neither.

**Quality:** 110 vias, 962.4 mm copper, 693 segments. By comparison:
- the first DONE under the incomplete spec (20:25Z) had 138 vias / 1177.6 mm;
- v4 (verifier 1) had 110 vias / 967.9 mm.

## 2. What was given, and the input defect that shaped the run

**The board.**
- 2 layers, 50 × 60 mm, 84 parts, all piled south of the outline.
- Main parts: an FT2232H-class USB bridge (U1, LQFP-64), eight SC-70 buffers, an LDO, a USB ESD array, an EEPROM, a USB-C receptacle (J1), a 2×7 1.27 mm header (J2) and a 1×16 2.54 mm header (J4), a slide switch, a reset button and six LEDs.
- Board-wide pours: +3V3 on F.Cu, GND on B.Cu.
- Rules: 0.15 mm clearance and track, 0.6/0.3 mm vias.

**Declared mechanics.**
- Mounting holes H1–H4 at (104,54), (104,106), (146,54), (146,106), from `mechanical.json`; seated by the intent's `fixed_poses`.
- J1 on the north edge and SW1 on the west edge, from the brief; position along the edge unknown.

**EMC rows: none were given.** The user was unavailable, and no proximity limits or keep-away rules were invented.

**Defect in the given pile.**
- Every pad carries KiCad-6's per-pad `locked` token, and the placement writer never turns such pads with their footprint.
- The pile was written that way: 38 of 84 parts have pads turned 90° against their bodies. For example, pcbnew reads U1's pad 1 as 0.30 × 1.55 mm, and `check_pads` finds 126 overlapping pad pairs on U1.
- Round 1 ran on this geometry and is **void**.
- `helpers/normalize_pile.py` turns each footprint to its pads' common angle and strips the per-pad `locked` token. Everything shipped was placed from the result (`fixed2.kicad_pcb`).

## 3. Groups and judgement calls

**Fixed parts.**
- H1–H4: held by the intent's `fixed_poses`.
- J1 and SW1: held to their edges by `edge_connectors[]`.
- FID1–3 had no declared pose. I placed and locked them by judgement at (110,53), (140,107) and (103,100): beside the corner holes, out of the connector and LED areas.

**`groups.json`:** 9 groups; `check_groups` reports 0 errors and 0 warnings.

| group | parts | anchor / hints | reason |
|---|---|---|---|
| usb_in | J1, U3, R1, R2 | anchor J1; near power, core | USB-C, its ESD array and the CC pull-downs |
| power | FB1, U2, C1, C2 | anchor U2; near usb_in, core | VBUS ferrite → LDO. C2 is assumed to be the output cap because the board's part values are blank |
| core | U1 + VCORE/VCCIO decaps, VPLL and VPHY bead-cap filters, R4, R6, TP1, TP2, Y1, C3, C4 | anchor U1; near usb_in, eeprom, buffers | the USB bridge and everything that serves its pins |
| eeprom | U4, R3, R5 | anchor U4; near core | configuration EEPROM and its resistors |
| buffers | U5–U10, U12, C17, C19–C21, R11, R22, R23 | near core, target | target-side buffers, their decaps, Vdrive feed and enable resistors |
| target | J4, J2, R12–R16, R19 | anchor J4; edge E; near buffers, reset | both headers share 9 nets. J4 is 41.7 mm long and fits only along an east or west edge, and west already has SW1 |
| uart_sel | SW1, U11, R25, R20 | anchor SW1; near buffers, core, target | the SWO/RXD selector switch with its RXD buffer |
| reset | SW2, Q1, R24, R17 | anchor SW2; near target, buffers | target reset; SW2 is top-actuated, so no edge |
| leds | D1–D6, R7–R10, R18, R21 | edge S; near core | six status LEDs as one unit toward an edge |

**Other calls.**
- **Decaps after placement.** All six judged seeds broke 1–4 decap limits. The chosen s0 broke two (C12 at 3.00 mm and C6 at 3.79 mm from U1; limit 2.92). I fixed them with `place_pose set C12 115.6 78.02 --rot 180` and `set C6 120.9 83.3 --rot 180`. `CHOSEN.json` records these under `after`, with `place_args: []`.
- **J1 overhang.** The USB4085 drawing could not be read (no PDF reader on this machine), so J1 keeps the intent's flush seat.
- **USB pair.**
  - A 90 Ω differential pair would need 1.13 mm legs on this 1.51 mm core; routed at 0.15/0.15 mm it is about 169 Ω. I did not run an impedance pass.
  - The pair is detected by name only; the board does not declare it.
  - Verifier, advisory: it runs mostly on B.Cu, with 2.9 mm skew.
- **GND return-via tail:** included, because USB 2.0 HS puts the board in the high tier.

## 4. Placement rounds and routing

**Placement rounds.**
- **r1** (given pile): 12/12 placements "legal". The judge route found s8 clean, while the three seeds with U1 at 0° left 35–46 nets open (their `qfn_fanout` escaped 0 of 31 pads). Voided because of the turned pads.
- **r2** (normalized pile): 12/12 legal with no turned-pad parts. Judged seeds:

  | seed | blocking | vias |
  |---|---|---|
  | s0 | 0 | 84 |
  | s10 | 0 | 95 |
  | s1 | 0 | 99 |
  | s7 | 0 | 106 |
  | s8 | 0 | 132 |
  | s2 | 1 | 107 |

  r2's best judge route (s0) has no blocking net, so placement rounds stopped there. No review round was needed.

**Full routing.** `/plan-pcb-routing` was followed by hand; every plan passed `route_plan_check` (17/17 rules).

| attempt | change | result |
|---|---|---|
| v1 (`final_route_old1/`) | the skill's chain as written | went below the board's declared floors (0.3 mm plane-tap vias, a 0.1496 mm track); rejected |
| v2 (`final_route_old2/`) | `--escalation board --fab-tier standard` | floors held, but +1V8 at U1 pin 12 was left stranded. The pin is reachable before routing (margin +0.43 mm), so this is corridor competition, not placement |
| v3 (`final_route_old3/`) | route +1V8 first, then cleanup laps and `dedupe_segments.py` | **first DONE** under the then-incomplete spec: 138 vias, 1177.6 mm |
| 14 variants (`exp*/`) | layer costs, failed-first split on/off, +1V8 in/out of the fanout, no fanout, max ripup 4/5 | best: costs 1.0 6.0, ripup 5, +1V8 out of the fanout → 110 vias |
| v4 (`final_route_old4/`) | best variant + one cleanup lap | 110 vias / 967.9 mm; **verifier 1 FAIL**: Power-class widths ungraded, 6 of 8 nets under 0.3 mm (about 124 mm) |
| P1b–P5b | all 8 Power nets at 0.3, kept out of the 0.15 mm U1 fanout; then `--escalation off`, `+--no-power-tap-neckdown`, `--grid-step 0.05`, `--neckdown-length 0.5` | P1b brought it to 5 nets / about 12 mm under. P2b–P5b: 5, 5+1 undersized, 5 + broken +1V8 |
| v5 (`final_route/`) | P1b re-run fresh, plus one cleanup lap | **shipped**: blocking 5, 110 vias, 962.4 mm, 693 segments |

## 5. Stop rule and remaining blockers

**Stop condition 3 (plateau).** After P1b, four different approaches did not lower blocking.

Remaining blockers (all `net_widths`, all at U1), as measured by verifier 2:

| net | length under 0.3 mm | narrowest | where |
|---|---|---|---|
| +1V8 | 8.13 mm | 0.15 | U1 pins 37, 12, 49 (about 2.5 mm each, tapered) |
| GND | 17.60 mm | 0.15 | U1 pins 5, 11, 13, 15, 25, 35, 47 (to C22.2), 51; 4.8 mm of it is via-to-via runs on B.Cu |
| /VPLL | 1.90 mm | 0.15 | U1 pin 9 → C8.1 |
| /VPHY | 1.08 mm | 0.15 | U1 pin 4 → C9.1 |
| +3V3 | 0.30 mm | 0.15 | via stub under U1 |

- **Totals:** 29.01 mm on 59 segments. 20.59 mm of it could be widened to 0.3 mm in place, and a 0.3 mm track clears every U1 pad by 0.192–0.204 mm.
- **Why it stays:** this is the router's neck-down behaviour, not geometry. No repo actor widens existing copper, and the routing skill forbids hand copper.

**Disclosed, not gating.**
- 62 vias sit in a pad or paste opening. The KiCad-6 file format cannot declare them, so IPC-4761 Type VII (filled and capped) must go on the fab drawing.
- Both pours are stored unfilled; refill them before exporting Gerbers.
- KiCad's `connection_width` check reports 4 narrow +3V3 fill necks (that check is off by default).

## 6. Floors

- **Held:** clearance 0.15 (smallest used 0.15), track ≥ 0.15, vias 0.6/0.3, hole-to-hole 0.25, edge 0.3.
- **One project value lowered:** `min_hole_clearance` went 0.25 → 0.15, written by the bare pour step. KiCad measures 0 violations at the authored 0.25.
- **Power widths:** see §5.
- **v1:** went below the board's floors and was rejected for it.

## 7. Verifier

- **verdict_1: FAIL** (board v4, sha 1566157c…).
  - Finding: the Power class's 0.3 mm width was ungraded; 6 of 8 nets were under it.
  - Every other check passed: buildable, floorplan 0 errors, mechanical facts exact, blocking 0 under the other flags, `check_complete` DONE, all nets connected, DRC 0.
- **verdict_2: FAIL** (board v5, the shipped one).
  - Finding: 5 of 8 Power nets are under 0.3 mm (29.01 mm), and 20.59 mm of that is widenable in place.
  - Lenses: connectivity PASS, DRC PASS, spec FAIL.
  - Everything else passed.

## 8. Timeline (UTC) and where the time went

| time | event |
|---|---|
| 19:59:36 | FIRST_CMD |
| 20:00–20:03 | read the skills and the board; wrote groups |
| 20:04 | round 1 placed |
| 20:05–20:08 | round 1 judged |
| 20:08–20:11 | found the turned pads; wrote `normalize_pile.py` |
| 20:12–20:14 | round 2 placed and judged; decap fixes |
| 20:16–20:25 | full routes v1–v3; **first DONE at 20:25:35** (under the incomplete spec) |
| 20:26–20:37 | 14 routing variants; v4 written as final |
| 20:38–20:45 | verifier 1, grade, tool-gap write-up |
| 20:46–00:43 | **stalled**: my call (it included an `rm -rf`) sat on a permission prompt nobody could answer and never ran |
| 00:43–00:50 | Power-width fix (P1b–P5b), v5 shipped |
| 00:50–00:59 | verifier 2, ledger closed, measure |

- **Wall time:** 4 h 59 m (`measure.py`).
- **Active time:** about 1 h 03 m, spent roughly on the void round and its diagnosis (8 min), routing v1–v3 (9 min), post-DONE variants (11 min) and the width fix (10 min).

## 9. Tool gaps

There are 12 entries in `TOOL_GAPS.md`. Each has a reproduction command, with its input boards in `repro/`. The entries, ranked by what they cost:

1. The writer never rotates pads carrying the `locked` token, and the pile already carried that damage.
2. Declared net-class widths are graded nowhere and their member nets are never listed.
3. `route.py` narrows power nets at fine-pitch pins, and no flag stops it.
4. `place_simple` and `check_assembly` don't see a footprint whose own pads overlap.
5. The routing recipe, run with the tools' default escalation settings, ships copper below the board's declared floors, and the project write-back hides it.
6. A `qfn_fanout` stub runs through C11's pad (same net) and leaves a dangling tail.
7. `route.py` writes stacked same-net duplicate segments it has already detected (issue #162 covers this).
8. Placement rounds stop at a clean fast route even when every judged seed fails the floorplan gate.
9. `qfn_fanout` defaults to the 0.1 mm fab floor rather than the board's class clearance.
10. A bare pour lowers the project's copper-to-hole floor.
11. `manifest_to_plan` drops the cap-pass step, claiming a path that exists does not.
12. No PDF reader on this machine (environment, not the repo).

**Tools that said "fine" when it wasn't:**
- `place_simple` called all round-1 placements legal (gap 1).
- `check_assembly` called r1/s9 buildable despite U1's overlapping pads (gap 4).
- `board_score` reported blocking 0 on v1 when run without the spec flags (gap 5).
- `board_score` and `check_complete` left net widths UNGRADED while the board declares them (gap 2).

**Helpers I wrote:** `helpers/normalize_pile.py` and `helpers/dedupe_segments.py` (gaps 1 and 7).
