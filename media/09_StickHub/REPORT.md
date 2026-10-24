# REPORT — 09 StickHub, `/plan-pcb-placement full` (gpm campaign, WT bda59fa0)

I could not invoke any skill, so I followed these by hand from their SKILL.md files:
- `plan-pcb-placement`, with its verifier.md, part-roles.md and placement-lessons.md;
- `plan-pcb-routing` (§3.8);
- `analyze-power-nets`, which plan-pcb-routing Step 4 asks for;
- the parts of `find-high-speed-nets`, `recommend-plane-mappings` and `identify-diff-pairs` that plan-pcb-routing says to follow inline: the speed tier, the 2-layer plane map, and the USB pairs found by name.

## 1. Result
**DONE** on `delivered.kicad_pcb`, sha256 `dea19c19e394fd2ff104cae5299adb94086d7875860fc37ac5b35d940fe430cc`.

| DONE condition | Measured |
|---|---|
| `board_score` blocking / unrouted / broken | 0 / 0 / 0 |
| `check_complete` (intent + baseline) | DONE. Ungraded: diff_pairs, impedance, length, net_widths (the board declares no spec for any of them) |
| `check_connected` | All nets fully connected |
| `check_drc --clearance-margin 0.1` | 0 violations (3 same-net self-crossing warnings, which KiCad permits) |
| `check_assembly --baseline` | Buildable |
| `check_floorplan --intent intent_run.json` | 0 errors |
| `kicad_drc_compare` | kicad 0, check_drc 0, CONSISTENT; connwidth 0, thermal 0 |
| `kicad-cli pcb drc` on the filled board | 0 unconnected; only `lib_footprint_issues` (the footprint library is not on this machine) |

- **blocking_by:** every component is 0. diff_pairs, impedance, length and net_widths are ungraded.
- **Quality:** 133 vias, 907.16 mm of copper, 1234 segments.
- **grade.py:** done true, check_complete DONE, check_complete with `--authored-from` UNSOUND (see §6).

## 2. Board, groups and judgement calls
The board is 2-layer, 16.5 × 40 mm, with 90 parts on both faces (37 on F, 53 on B):
- an XR22417 7-port hub (LQFP-48, on B);
- 7 JST-SH ports and a USB-A PCB-plug tongue;
- an SLG5NT1487V load switch;
- per-port TVS diodes and duo status LEDs.

`groups.json` has 13 groups:

| Group | Parts and reason |
|---|---|
| host | J1 with its D-/D+ TVS diodes D22/D23 |
| power | U2, C21, C28, D24, JP1 (EXTPWR jumper), J9 (EXTGND pad), D25 |
| core | U1, Y1, C1–C13, R1–R6 |
| bulk5v | The +5V bulk caps: C14–C20 (0.1 µF 100 V, F side) and the fifteen 22 µF caps (B side). **Judgement:** kept apart from U1's group. The error-graded decap limits are still priced for them; only the per-pin matching term is dropped, which would have pulled 23 caps onto U1's single VCC5 pin |
| bulk_edge | C38 alone |
| leds | D15–D21 with R7–R13, edge N |
| p1–p7 | Each JST port with its TVS pair |

- **Templates:** none. `check_groups` found 0 template hints. U2 is a load switch with no inductor, U1's regulators are internal and linear, and there is no radio.
- **EMC rows:** none were given, and I invented none.
- **Row added to `intent_run.json`** (the given `intent.json` is untouched): an `edge_connectors[]` row for C38, edge north, class `connector_affinity`, mating_face `+y`.
  - **Judgement:** C38 is a 330 µF electrolytic whose footprint (`CP_Elec_6.3x11_Board_Edge_Mirrored`) draws its can past local y=0, outside its courtyard. Placed inside the board, the can sits over other B-side parts, which `check_assembly` gates. The south edge is the plug and the east/west edges carry the JST mating faces, so the can goes off the north edge.
  - The class was added before pass 2, after the classless row was ignored (TOOL_GAPS #1).
- **Mechanical facts:** H1 and J1–J8 sit at their `mechanical.json` poses through `fixed_poses[]`; the verifier measured 0.0000 mm error on all nine. C38 is on the north edge with its can outward.

## 3. Placement
1. **Pass 1** used the defaults. Every seed carried floorplan errors, and the same `edge_connector` error on C38 appeared in 9 of 12. That is the input's fault, so I rejected the pass (files in old/pass1/).
2. **Pass 2** added `--decap-limit-weight 40`. Every seed carried decap errors at a different pin each, so I followed §3.6 case 2:
   - hand-repaired s7 (C11 moved 0.087 mm) and judged it alone: quick blocking 39;
   - routing it gave a best of 8.
   - I classified the remaining failures as placement: the power group sat 17 mm north of the plug, and the failures clustered at U1's escape faces.
3. **Pass 3** used `--decap-limit-weight 40 --near-weight 10`. Seeds 10 and 3 were floorplan-clean and buildable.
   - Judged with the pour-first chain: **s10 quick blocking 7 (kept)**, s3 51.
   - `CHOSEN.json`: seed 10, clustered, pass 3, `after: []`.

## 4. Routing (plan-pcb-routing by hand)
- **Board class:** a STANDARD 2-layer board; the stackup has a 1.51 mm core.
- **Diff pairs:** the 8 USB pairs were routed with `route_diff` at 0.1/0.1. There was no `--impedance` pass: 90 Ω is not achievable on this 2-layer board, and the board declares no impedance.
- **Speed tier:** USB 2.0 HS is high tier, so the chain ends with a stitch-only Step 3 tail. No single-ended net is high speed, so there is no `--add-gnd-vias`.
- **Pours:** the designer's two GND pours are kept as drawn (`--skip-existing-zones`).
- **Power widths (`/analyze-power-nets`):** the tool's recommendation was wrong (TOOL_GAPS #6), so I used my own estimates:

  | Nets | Width asked for |
  |---|---|
  | GND | 0.3 |
  | +5V, VIN, Net-(J1-Pin_1) | 0.7 |
  | +3.3V, +1V8 | 0.5 |

  The XR22417 draws 167 mA (datasheet). Each port's 100 mA and the plug's 500 mA are estimates.
- **Widths actually delivered fall well short** (no width spec is declared, so none of this is graded):
  - Net-(J1-Pin_1): 9.7 of 10.2 mm at 0.1 mm.
  - VIN: 20.5 of 32.8 mm at 0.1 mm.
  - +5V: minimum 0.175 mm.
  - +3.3V: 94% narrower than asked.

  This is the main electrical caveat: the upstream VBUS path runs about 30 mm at 0.1 mm, roughly 0.45 A for a 10 °C rise and about 0.15 Ω. A `--force-reroute` of those two nets did not widen them and added 4 vias, so I discarded it.

**Shipped chain** (`final_route/StickHub_plan.sh`; route_plan_check 17/17; `StickHub_plan.json`; `redo_commands.sh`):
1. Bare `route_planes` with `--skip-existing-zones`.
2. `route_diff`: 5 pairs coupled; /U6D partial; /U2D and /U5D finished single-ended by `route.py`.
3. `route.py --nets '*'`, GND included, with the Step 2c small features: `--track-width 0.0762 --clearance-ceiling 0.0889 --via-size 0.25 --via-drill 0.15 --layer-costs 1.0 1.0 --via-cost 150`.
4. The same command again (iteration).
5. `route_planes --stitch-vias --stitch-max-freq 480`.
6. A closing `route.py`.
7. **Hand join** with `check_join` (CLEAN): +3.3V on B.Cu from (143.2, 95.9) to (142.967, 96.133), width 0.25. It closes a soft joint that `check_weird` reported as a dangling end (TOOL_GAPS #5).

`routed.kicad_pcb` is a `copy_board` copy of `final_route/s6_join`. Older chains are in `final_route_old1..4/` and the experiments in `arms/`.

## 5. Stop rule and remaining blockers
**Stop condition 1: DONE.** No blocker remains.

How blocking came down (from `board_score`):

| Step | Blocking |
|---|---|
| Pour-last chain (Step 8) | 40 |
| Pour-first, GND routed in the main step | 8 |
| Parameter variants C, D, F | 14, 14, 16 |
| Failed-first ordering (G) | 13 |
| Pass 3 placement, plus the Step 3 tail | 7, then 6 |
| Scoped lap | 3 |
| Narrower power widths (H) / Step 2c small features (I) | 2 / 1 |
| Final chain | 0 |

- **First DONE:** 12:53Z, with 151 vias.
- **Via optimisation:** the round-1 arm with via cost 150 and a stitch-only tail reached 133. Round 2 (via cost 300, via cost 600, layer costs 1.0/1.3) was worse every time, so I stopped.

Caveats that DONE does not grade:
- the power-width shortfall in §4;
- 60 vias in pads or paste openings, stamped filled and capped (IPC-4761 Type VII), which costs extra at the fab;
- 3 USB pairs not fully coupled, and measured skews up to 5.9 mm (/U4D);
- tracks on the F face of the USB-A plug tongue, which the designer had left unpoured. If that matters, the fix is a `User.2` keep-out drawn there by the user.

## 6. Floors
- `check_complete --authored-from` reports **UNSOUND** (reported, not gating). Floors moved below the input project's values:
  - track width 0.15 → 0.1 mm;
  - via diameter 0.5 → 0.25 mm;
  - annular ring 0.1 → 0.05 mm;
  - hole 0.25 → 0.15 mm;
  - clearance 0.15 → 0.1 mm (the fab floor).
- `route.py` reports: "Design rules [...]: 6 feature(s) on 6 net(s) delivered below the requested size".
- The 0.25/0.15 via is JLC's "advanced" tier. Confirm the fab can build it before ordering.

## 7. Silkscreen
- KiCad silk count: `silk_edge_clearance` 4 before the label tidy, 0 after. I kept `labelled.kicad_pcb`.
- `beautify_labels` left the R1, R2, R3, R7 and R9 labels where they were (no legal spot).

## 8. Fill
`fill_for_delivery` ran and kept the net classes. KiCad's unconnected count without a refill went from 38 to 0.

## 9. Timeline (UTC) and where the time went

| Time | Step |
|---|---|
| 11:55 | Start |
| 11:56–12:06 | Read the skills and the board |
| 12:06–12:14 | Groups, pass 1 (rejected), pass 2, hand repair, judge, power analysis |
| 12:14–12:37 | Full route and routing arms on the pass-2 board (best: 8) |
| 12:38–12:41 | Pass 3 and its judge |
| 12:41–12:53 | Route, tail, scoped laps, small-feature arm; DONE at 12:53 |
| 12:55–12:58 | Via optimisation |
| 12:59–13:02 | Shipping chain re-run, label tidy, fill |
| 13:01–13:06 | Verifier, report |

`measure.py` shows 1:11:20 of wall clock. About 922 s of it was spent waiting on jobs, mostly routing runs of 2–3 minutes each, up to three at a time.

## 10. Tool gaps
All 9 are in `TOOL_GAPS.md`, ranked:
1. `place_simple` drops a classless edge row that its own grade fails.
2. The default seed pass gave no floorplan-clean seed, twice.
3. Step 8's pour-last recipe was reverted by `route.py`'s own improvement gate.
4. `route.py`'s merged verdict leaves out GND links that its own oracle reports open (the same symptom as #1339).
5. `check_weird` calls an overlapping soft joint a dangling end; this needed two hand joins.
6. `analyze_power_paths` recommends the wrong widths (per-pin current multiplication, connector sinks dropped, no path traced).
7. No PDF reader on this machine (I wrote a helper).
8. No tool scores a chip's rotation on one net group (I wrote a helper).
9. The skill names `--rip-existing-nets` where `--force-reroute` is needed.

## 11. Verifier
There was one verifier call, and its verdict in `verdict_1.txt` is **PASS**. Lens files: connectivity PASS, drc PASS, spec PASS. It measured:
- the sha matches the claim;
- buildable; no mating-region or off-outline pad copper;
- floorplan 0 errors;
- the 9 declared poses exact; C38 on the north edge, overhang 0, facing north;
- board_score 0 / 0 / 0 with 133 vias;
- check_complete DONE, and UNSOUND with `--authored-from` (the four floors above);
- check_connected clean; check_drc 0 violations;
- no declared classes. diff_pairs, impedance, length and net_widths are UNEXAMINED.

Its advisory notes: USB skews up to 5.87 mm (/U4D); 142 crossings of plane voids by the USB nets on this 2-layer board; the GND via nearest to a USB via is 0.63–4.39 mm away.
