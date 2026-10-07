<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT: fa10 board 06, rp2350_fpga_eensy_prePlane (`/pcb-free-agent full`)

**Result: DONE.**
- Board: `final.kicad_pcb` plus `final.kicad_pro`, sha256 `e19efd188d0e2f7a6a53bb1212b57f373b2d98724cf14a2a6f073a23cd40adfb`.
- Verifier: one call, **VERDICT=PASS**.
- Stop rule: **after DONE, two consecutive optimisation rounds each cut vias by less than 5%** (ledger `DONE-EXHAUSTED`).
- Time from FIRST_CMD (2026-10-07T15:17:34Z) to the frozen, verified board: **1h40m**. The first DONE came at 58 min.

## 1. Result

| DONE condition (`full`) | Measured on `final.kicad_pcb` | Tool |
|---|---|---|
| board_score blocking 0 | **0** | `py_tools/board_score.py --intent intent.json --baseline <input>` |
| unrouted 0 | **0** | board_score |
| broken 0 | **0** | board_score |
| check_complete DONE | **DONE**. Impedance, length and net widths are UNEXAMINED because the board declares none. | `check_complete.py --intent intent.json` |
| check_connected | all 74 routed nets fully connected | `py_router/check_connected.py` |
| check_drc (`--baseline <input> --clearance-margin 0.1`) | no violations. One permitted same-net self-crossing warning. 91 vias sit in paste openings, all marked filled and capped. | `py_router/check_drc.py` |
| KiCad zone-aware unconnected | **0** | `py_tools/kicad_unconnected.py --items` |
| KiCad 10 DRC (project rules) | **0 errors**, 0 unconnected. 51 warnings (listed under the table). | `kicad-cli pcb drc --severity-error --refill-zones` |
| check_assembly | buildable (blocking 0) | `py_tools/check_assembly.py --intent` |
| check_floorplan | 0 errors, 1 warning: U8's frame pins face the board edge, which is inherent | `py_tools/check_floorplan.py --intent --allow-routed` |
| U8 at (148.5, 105.005), rotation 270 (mechanical.json) | exact, and locked | verifier |
| J1 on the north edge (design brief) | J1 at (148.5, 89.691), rotation 180. The opening faces north and the body overhangs the edge by 0.93 mm. | verifier |

The 51 KiCad warnings:
- 33 hole-to-hole, all between U8's own paired pins;
- 9 footprint-library issues;
- 7 silkscreen over copper;
- 2 dangling track ends shorter than 0.04 mm.

`blocking_by`: assembly 0, broken 0, drc 0, floorplan 0, undersized 0, unrouted 0. Impedance, length and net widths are `null` (ungraded, nothing declared).

| Quality | Final |
|---|---|
| vias | **185**, all 0.25 / 0.15 mm. 48 of them connect pads to the planes (GND 31, +3V3 17). |
| copper_mm | **986.11** |
| segments | **1055** (F 555, In2 174, B 152, In3 107, In1 41, In4 26) |

Independent grade (`scripts/grade.py --mode full`):
`{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 185, "copper_mm": 986.11, "segments": 1055, "check_complete": "DONE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`.
The `UNSOUND` entry is the floor descent described in section 3, not a blocker.

## 2. The stop rule that fired, and what remains

The board reached **DONE first**, at 58 min. Then I ran **two bounded optimisation rounds**, both starting from the same placement with U2 already fanned out.

**Round 1** (`o1/`):
- `--via-cost 150`: 169 vias, but blocking 1.
- `--via-cost 300`: 162 vias, blocking 2.
- `--direction-preference-cost 0`: **DONE at 187 vias**, worse than 185.
- no extra flags (control): blocking 2.

**Round 2** (`o2/`, each with up to 3 rip passes driven by the router's own hints):
- via cost 150: 169 vias, blocking 1 (FPGA.~{RESET} open at RN2.7).
- via cost 200: 170 vias, blocking 1.
- via cost 300: 165 vias, blocking 1 (PIN.9 open at U2.D6).
- direction preference 0 plus via cost 150: 171 vias, blocking 4.

Neither round produced a DONE board under 185 vias, so both cut 0%, and the rule stopped the run. A higher via cost does buy 9–11% fewer vias, but every such board still had one net open after three rip passes. Finishing one by hand would have been a third round, which the rule forbids.

**Remaining blockers: none** (blocking 0). Non-blocking issues still on the board:
- Copper-to-hole clearance is below the authored floor (section 3).
- The via annular ring is 0.05 mm (section 3).
- KiCad warns about 2 dangling track ends: GND on F.Cu, 0.0354 mm long, at (151.05, 97.525), and +3V3 on F.Cu, 0.0236 mm long, at (143.033, 100.667). The repo's checkers report none (TOOL_GAPS #8).
- The USB D+/D- nets are routed single-ended, with no impedance or length check: `Net-(J1-D+-PadA6)`, `Net-(J1-D--PadA7)`, and the R4/R5 nets to U6. The board declares no diff-pair or impedance class, so nothing grades them.

After the first DONE I found a defect (fixed outside the optimisation rounds). The DONE board had **2 KiCad DRC errors** (`pth_inside_courtyard`: U8 pins 16 and 17 sit inside SW1's courtyard) that every repo checker passed. I moved SW1 0.335 mm north on the copper-free placement and re-ran the whole chain. The final board has 0 KiCad errors at the same 185 vias.

## 3. Floors

**route.py's `Design rules` line** (final run, `r3/q2_clean.log`):
`Design rules [--escalation fab, --fab-tier auto]: 1 feature(s) on 1 net(s) delivered below the requested size (smallest track width 0.09 mm).`
- The feature is +1V1: 0.15 mm was requested, and 1.92 mm of it shipped at 0.09 mm. That includes my 0.566 mm hand-drawn link from ball U2.C4 to ball U2.D5.
- The first route pass reported `4 feature(s) on 3 net(s) ... (smallest track width 0.0889 mm)`. Two of those 0.0889 mm pieces survive on the final board (GND on In1.Cu, 0.023 and 0.15 mm long). That is below the 0.09 Default class but above the board's 0.075 minimum.

**`check_complete --authored-from <input>` says UNSOUND.** It lists one relaxed floor, `via annular ring 0.1 -> 0.05`, and puts the authored `min_hole_clearance` (0.25) under `unmeasured`.

*Annular ring 0.05:*
- All 185 vias are 0.25 / 0.15 mm, the JLC "advanced" tier. The fanout escalated from standard to advanced for U2's vias-in-pad and said so.
- U2 is a 0.4 mm-pitch WLCSP. A via in one of its pads larger than about 0.31 mm would break via-to-via clearance with its neighbour. So a 0.1 mm ring is unreachable there with through vias.
- The README gives the board's own via floor as 0.25–0.15, which is itself a 0.05 ring; the 0.1 is the generated project's value.

*Copper-to-hole clearance (not measured by check_complete; I measured it):*
- I ran KiCad 10's DRC on a copy whose project restores the authored 0.25 mm. It reports **199 `hole_clearance` violations, minimum 0.1425 mm**. At the toolchain's own 0.2 mm fab floor it is still 199. Below 0.15 mm: 21.
- The project now says 0.09. The first step, `route_planes.py`, wrote that (`rules.min_hole_clearance: 0.25 -> 0.09`, printed as "FAB FLOOR RELAXED"), which is why every checker reads clean.
- route.py announced "Copper-to-hole clearance 0.25mm" on every step, but new vias don't honour it (TOOL_GAPS #1).
- The one flag that looked like a fix, `--routing-clearance-margin 1.7`, does nothing for single-ended routing: the copper was identical (TOOL_GAPS #6b).
- **Confirm the fab supports about 0.14 mm track-to-via-hole before fabricating.**

**Other floors and fab notes:**
- Clearance 0.09 and track width 0.09 are the board's own Default class, not lowered. The board minimum of 0.075 is unchanged.
- 91 vias sit in solder-paste openings (U2's vias-in-pad and plane vias next to fine-pitch pads). All are marked `(capping yes) (filling yes)`; the fab drawing needs to call for IPC-4761 Type VII.

## 4. Timeline (UTC; minutes from FIRST_CMD at 15:17:34Z)

| Time | +min | Event |
|---|---|---|
| 15:17 | 0 | FIRST_CMD. Read the README, the skill and the verifier brief. board_brief: `pile: true`, `has_copper: false`, so mode `full`. |
| 15:21 | 4 | Set U8 to its declared pose and J1 on the north edge, both locked (`place_pose`). |
| 15:22–15:25 | 5–8 | `place_seed` refused the pile ("already looks PLACED", #1165). With `--force`, it reported U6 "no legal pose anywhere". |
| 15:31–15:33 | 14–16 | Seated U6 by hand (place_pose, rotation 0, locked). **First legal placement**, `b/s03_seed0`: buildable, 0 floorplan errors. |
| 15:36–15:43 | 19–26 | Chose U6's rotation by hand from 4 seeds; `rank_rotations --ref U2` picked 270; ran seeds 1–4. |
| 15:47–15:56 | 30–38 | Pour, then U2 fanout on seed 3: 27 of 30 balls. Retries and a rotation sweep; seed 4 fans out 30/30 and became the kept placement. |
| 15:57–16:01 | 40–44 | First full route, two variants. **First fully routed board**, `r2/p4_routeB`: blocking 2. |
| 16:10–16:15 | 53–58 | Rip pass on the router's hint (blocking 1), then the hand link U2.C4 → U2.D5 (check_join CLEAN, locked), then a cleanup pass. **First DONE**, `r2/p7_clean`, 185 vias. |
| 16:18–16:35 | 61–78 | Optimisation rounds 1 and 2: no DONE board under 185 vias, so the stop rule fired. |
| 16:37 | 80 | KiCad DRC on the DONE board: 2 `pth_inside_courtyard` errors that every repo checker missed. |
| 16:38–16:49 | 81–91 | Moved SW1 0.335 mm north and re-ran pour, fanout, cap clearance, route, rip, link and cleanup. **Final board**, `r3/q2_clean`: DONE, 185 vias, 0 KiCad errors. Frozen as `final.kicad_pcb`. |
| 16:50–16:58 | 92–100 | **Verifier call 1: PASS.** |
| 16:57–17:03 | 99–106 | Copper-to-hole experiment (`--routing-clearance-margin 1.7`): no effect. |
| 17:04–17:05 | 106–108 | Ledger closed (`--final --stop-condition DONE-EXHAUSTED`, three lens files); film rendered. |

## 5. Where the time went

`scripts/measure.py` on this session's own transcript (at 17:07Z, 1h49m35s since the session started):
- **18.8 min** waiting on background jobs;
- **57.3 min** of other tool time;
- **33.5 min** of model time.

The "other tool time" includes my foreground polling of long jobs. A route chain or seed takes 1–10 min, and I spent about 30 min polling in total. So roughly **50 min went to waiting on long jobs and 60 min to working**. The verifier ran for 7.9 min in parallel with report work.

Routing was fast on this board: one full `route.py` pass takes about 4 min, the U2 fanout about 20 s, and a seed about 40 s.

`measure.py --root .` refused to run. The transcript belongs to a subagent and is filed under the launching checkout (#1177), so I passed its path explicitly.

## 6. What worked and what didn't

**Worked:**
- **Seating the biggest IC by hand before seeding.** place_seed could not seat U6 anywhere (TOOL_GAPS #3). With U6 locked at (148.5, 103.5), the same seed placed all 61 parts in 40 s with none left unseated.
- **Choosing U6's rotation from four seeds** (crossings / hpwl):

  | U6 rotation | crossings | hpwl (mm) |
  |---|---|---|
  | 0 | 558 | 968 |
  | 90 | 568 | 925 |
  | 180 | 657 | 1003 |
  | 270 | 609 | 1030 |

  I kept rotation 0, which also points the USB pins at J1.
- **rank_rotations for U2:** 270 gave 334 crossings against 363 at rotation 0.
- **A seed sweep with `--ignore-nets GND +3V3`:** seed 3 had 261 crossings, seed 4 278 and seed 1 295. Seed 2 left one part unseated.
- **Choosing the placement by how well U2 fans out:** seed 3 escaped 27 of 30 balls and seed 1 24 of 30. Seed 4 escaped all 30 and was kept.
- **Letting the router use the plane layers at cost 4**, rather than forbidding them: blocking 2 instead of 7 on the first route.
- **The router's own rip hint** (`--rip-existing-nets` with 9 fanout nets): blocking 2 → 1.
- **A 0.566 mm hand-drawn link** from U2.C4 to U2.D5 on F.Cu (check_join CLEAN, locked): blocking 1 → 0.
- **A cleanup pass with `--nets '*'`:** removable segments 5 → 0, orphan stubs 1 → 0, and check_complete went from INCOMPLETE to DONE.
- **Running KiCad's own DRC before freezing.** It caught 2 errors no repo checker reports. Moving SW1 0.335 mm north fixed them (2 → 0) at no via cost.

**Didn't work:**
- Fanout retries at clearance 0.075, at 0.0889, and with `--fab-overrides` set to the board's own floors: still 27 of 30 on seed 3. A second fanout pass for the 3 missing nets with `--check-for-previous` escaped 0 of 3.
- A higher via cost (150, 200, 300): 165–170 vias, but 1–2 nets stayed open after 3 rip passes.
- `--direction-preference-cost 0`: DONE, but 187 vias (more than 185). Combined with via cost 150: blocking 4.
- `--routing-clearance-margin 1.7`: copper identical to the run without it; the flag does nothing for single-ended nets.

**Decisions to note:**
- **Intent:** everything was graded against the given `intent.json`, unmodified (its sha256 re-checked). For seeding only I used `intent_rot.json`, which is `intent.json` plus one `rotation: 270` block for U2, written by `rank_rotations --write-intent`.
- **The decap rule was not armed.** No placed reference of this design was available (the intent records the source as withheld), so I could not use `--decaps-from`. `decaps.max_distance_mm` stays undeclared, and the seeder's decap stage claimed 0 caps.
- **Planes:** GND on In1 and +3V3 on In4, one solid plane next to each outer layer; F, In2, In3 and B carry signals. The 1.1 V rails are 0.15 mm tracks; VBUS, VIN and the switch nodes are 0.2 mm. All widths were delivered except 1.92 mm of +1V1 at 0.09 mm.
- **J2's keep-out:** placement leaves a footprint's own zone behind (TOOL_GAPS #5), so I moved J2's keep-out back onto its pads with `helpers/move_fp_zone.py`. The final board has 0 vias inside it.
- **Hand-drawn copper:** one locked F.Cu segment on +1V1, from U2.C4 to U2.D5, 0.09 mm wide.

## 7. Tool gaps

`TOOL_GAPS.md` has the full entries, with repro commands against `repro/` and the issue search for each. Ranked by what they cost:

1. route.py says it holds copper 0.25 mm from holes and ships 0.1425 mm. route_planes had already lowered the project rule to 0.09, so every checker reads clean. Related: #1038 (closed), #1198, #1160.
2. Treating U8 as a container hides a real KiCad `pth_inside_courtyard` error from check_assembly, check_drc, board_score and check_complete. Meanwhile render_placement and the plan checks over-count U8 as an overlap. Related: #1184.
3. place_seed says U6 has "no legal pose anywhere". Its pad check reports a U6/U8 pad overlap (13.63 mm) that place_pose's exact check does not see. New.
4. bga_fanout (under-pad escape) drops balls while inner layers are free and gives no reason. It suggests a 0.04 mm via. It also leaves inner ball U2.C4 unconnected, though a short diagonal link that check_join grades clean would connect it. Related: #129, #1189.
5. A footprint's own keep-out (J2) does not move with the footprint, and the router honours it at the stale position. New.
6. route.py's `failed` count reads 0 on a run that left two nets open. New.
   6b. `--routing-clearance-margin` does nothing for single-ended routing. New.
7. Reaching DONE takes three route.py runs by hand: route, a rip pass on the router's hint, and a cleanup pass after the hand-drawn link.
8. check_weird and check_orphan_stubs report clean while KiCad warns about 2 dangling track ends. New, minor.
9. place_seed refuses a pile once the fixed parts are locked (#1165, open).
10. measure.py cannot find a subagent's transcript (#1177, open).

Helpers I wrote, each with its own TOOL_GAPS entry:
- `helpers/plot_sides.py` (#2)
- `helpers/diag_u6_seat.py` (#3)
- `helpers/move_fp_zone.py` (#5)
- `helpers/route_chain.sh` (#7)

## 8. Verifier verdicts

**verdict_1.txt: VERDICT=PASS.** One call, to a fresh general-purpose subagent briefed from `references/verifier.md` for `full`. Lenses: `verdict_1_connectivity.txt` PASS, `verdict_1_drc.txt` PASS, `verdict_1_spec.txt` PASS.

It measured, all clean:
- sha256 recomputed and matching;
- buildable, 0 floorplan errors, both mechanical facts met;
- blocking 0, unrouted 0, broken 0; check_complete DONE;
- check_connected and check_drc clean; KiCad DRC 0 errors.

It flagged as non-gating:
- The relaxed annular ring and copper-to-hole clearance. It counted 555 copper features within 0.25 mm of another net's hole, the closest at 0.1425 mm.
- The undeclared, unchecked USB pair.
- The two KiCad dangling-track warnings.
