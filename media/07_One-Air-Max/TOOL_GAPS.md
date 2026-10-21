# TOOL_GAPS -- gp14 board 07 (One-Air-Max)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`) after
`export PATH="$HOME/.venvs/krt/bin:$PATH"`. The inputs it needs are in
`wk/gp14/07_One-Air-Max/repro/`. Issue searches were read-only
(`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`).

## 1. place_simple's anneal blocks the WHOLE far face under a one-hole SMD part's courtyard

- **Tool / command:** `py_placer/place_simple.py` (its `simple_anneal.Annealer.overlap`).
- **What it claimed:** `seed 7 (clustered): cost 8300.9, 97500 moves in 99.9 s, no legal pose for CO2, I2C3, L3, PM2`. In round 1, all 12 of 12 seeds exited 4, each leaving 1-4 connectors with no legal pose (`scratch/r1_withhole/round.log`).
- **What was true:** the board had room. BAT1 is an SMD 3x18650 holder on F.Cu. Its only drilled pad is one unnetted 1.8 mm locating peg. `footprint_has_through_pads` therefore makes the whole part two-sided. `Annealer.overlap` then prices BAT1's full fallback courtyard (its 87.5 x 49 mm pad box) on B.Cu as well. `legality.rect_on` and its docstring give the far face only the drilled-pad box. As a result, no B-side part entered the ~4200 mm2 under the holder: every render showed the B face empty inside BAT1's box, with all 192 B-side parts crammed round the rim. With the peg pad removed (and nothing else changed), the same seed is legal: cost 3870.9 in 27.9 s, against 8300.9 in 99.9 s. Neither `check_assembly` nor `place_pose` objects to a B part under BAT1 (measured: U8 and PM2 set at (140, 85) on B, with no BAT1 pair).
- **Workaround:** `helpers/bat1_hole.py strip` (placement runs on `fixed_nohole.kicad_pcb`), plus an intent keep-out `BAT1_peg_hole_far_face` on B so no B part sits on the hole. `bat1_hole.py restore` then puts the hole back into each placed board before routing.
- **Reproduce:**
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gp14/07_One-Air-Max/repro/withhole.kicad_pcb 'wk/gp14/07_One-Air-Max/repro/gap1_withhole_s{seed}.kicad_pcb' --groups wk/gp14/07_One-Air-Max/repro/groups.json --intent wk/gp14/07_One-Air-Max/repro/intent_gap1.json --seeds 7 --clustered-seeds 7 --json 'wk/gp14/07_One-Air-Max/repro/gap1_withhole_s{seed}.json'
  #   -> exit 4, "no legal pose for CO2, I2C3, L3, PM2", cost 8300.9
  python3 -X utf8 py_placer/place_simple.py wk/gp14/07_One-Air-Max/repro/nohole.kicad_pcb 'wk/gp14/07_One-Air-Max/repro/gap1_nohole_s{seed}.kicad_pcb' --groups wk/gp14/07_One-Air-Max/repro/groups.json --intent wk/gp14/07_One-Air-Max/repro/intent_r1.json --seeds 7 --clustered-seeds 7 --json 'wk/gp14/07_One-Air-Max/repro/gap1_nohole_s{seed}.json'
  #   -> exit 0, cost 3870.9
  ```
- **Cost:** about 12 min: one wasted 12-seed round (6.5 min), plus the diagnosis and the helper.
- **Existing issues:** none found ("anneal far side through-hole courtyard", "NPTH both sides courtyard place_simple": no results).

## 2. A placement place_simple calls legal reads NOT BUILDABLE: two occupancy models, and no repair tool

- **Tool / command:** `py_placer/place_simple.py` against `py_tools/check_assembly.py --baseline`.
- **What it claimed:** `r1/s8.json`: `illegal: []` and `repaired: false`. The round log says every seed is legal, and `render_placement` says "no legality findings".
- **What was true:** `check_assembly` reads NOT BUILDABLE, with 12 gating courtyard pairs, for example C40<->L1 6.375 mm2 and D5<->U8 1.66 mm2. Both F-side caps C10 and C13 also sit under the BAT1 holder body. 197 of the 204 footprints draw no courtyard. The placer's anneal falls back to the pad box. `check_assembly` grades the drawn body (silk/fab), for example L1's 7.1 x 6.5 silk outline against its 7.6 x 3.4 pad box, and BAT1's 87.5 x 56.8 fab body against its pad box. Every one of the 6 judged seeds had 10-12 such pairs (s7: 10, s2: 10). No repo tool moves parts out of courtyard overlaps after `place_simple`.
- **Workaround:** `helpers/fix_courtyards.py`, which tries nudges under `place_pose`'s pad-legality gate and keeps one only when `check_assembly` shows it lowers the gating count. It took 8 pairs down to 1. I also made 4 manual F-side moves and placed D5 by hand. All are listed in `CHOSEN.json` `after`.
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/07_One-Air-Max/repro/s8_placed.kicad_pcb --intent wk/gp14/07_One-Air-Max/repro/intent_r1.json --baseline wk/gp14/07_One-Air-Max/repro/nohole.kicad_pcb
  #   -> VERDICT: NOT BUILDABLE, 12 COURTYARD-BLOCKING pairs; the same board's place_simple report
  #      (repro/s8_place_simple_report.json) says illegal [] .
  ```
- **Cost:** about 11 min, including the helper, its iterations and the hand moves.
- **Existing issues:** none that covers it. #1266 (closed) is the drawn-copper variant of a placement-vs-check_assembly blind spot.

## 3. route.py's in-run plane finalize writes stacked duplicate copper and does not disclose it

- **Tool / command:** `py_router/route.py --nets '*' ...`. This is the full route step, which runs the in-run plane finalize and the oracle reconnect.
- **What it claimed:** the run summary is clean (`failed 0`). `route.json` has no `stacked_copper` key, and the log has no stacked-copper warning. route.py's own census (`stacked_copper_over_model`, route.py ~l.4397) runs before the finalize.
- **What was true:** `check_weird` finds stacked-copper on GND/B.Cu: 14 findings at tolerance 0.1 mm, out of 23 exact duplicate segment pairs (one of them a triple). Some pairs have different widths (0.3 over 0.127). Two more `route.py` passes leave them in place. `check_complete` then reads INCOMPLETE (`weird_copper`). With `--via-cost` of 375 or more, the same chains also leave `kicad-dangling` redundant segments (3 on the 600 run). Those boards reach 217-224 vias but are not DONE. The kept 300 run has 225 vias.
- **Workaround:** `helpers/dedupe_segments.py`, which drops exact duplicates and keeps the widest copy, so connectivity cannot change. It took the board to DONE. I did not remove the near-duplicate `kicad-dangling` stubs, so the variants with lower via counts stay not DONE.
- **Reproduce:**
  ```
  python3 -X utf8 py_router/check_weird.py wk/gp14/07_One-Air-Max/repro/gap3_route_out.kicad_pcb     # FOUND 9 WEIRD THINGS: stacked-copper 9
  # (route input: repro/gap3_route_in.kicad_pcb; the exact route.py argv is the 5th/6th/7th line group of
  #  wk/gp14/07_One-Air-Max/final_route/redo_commands.sh)
  ```
- **Cost:** about 6 min. It also cost the 4-8 extra vias that the via-cost 375-1000 variants found but could not ship.
- **Existing issues:** none found ("stacked copper finalize duplicate").

## 4. classify_part gives a DC jack and a slide switch no class, so an edge entry cannot seat them

- **Tool / command:** `placement.part_class.classify_part` via `edge_seat.seats` (`SEATED_CLASSES`).
- **What it claimed:** DC1 `easyeda2kicad:DC-IN-SMD_DC-045A-13A` and PWR_SW1 `SW-TH_TK-6580A8-1` both classify as `None`. An `edge_connectors[]` entry for either is "placed as any other part". `check_floorplan` lists only SW1 and USB1 as edge parts.
- **What was true:** DC1 is a right-angle DC barrel jack whose mouth is on the footprint's -x end. PWR_SW1 is a right-angle slide switch whose knob is drawn at +y. Both belong on an edge with that face out.
- **Workaround:** I chose exact poses and declared them in `intent_gp.json` `fixed_poses[]` (basis `derived_default`): DC1 and PWR_SW1 on the east edge, between BAT1's solder tabs.
- **Reproduce:**
  ```
  cd py_placer && python3 -X utf8 -c "import sys; sys.path[:0]=['../py_router','.']; from kicad_parser import parse_kicad_pcb; from placement.part_class import classify_part; p=parse_kicad_pcb('../wk/gp14/07_One-Air-Max/repro/input.kicad_pcb'); print({r: classify_part(p.footprints[r], r).name for r in ('DC1','PWR_SW1','USB1','SW1')})"
  #   -> {'DC1': None, 'PWR_SW1': None, 'USB1': 'edge_receptacle', 'SW1': 'edge_actuator'}
  ```
- **Cost:** about 5 min (reading `edge_seat`, plus placing by hand).
- **Existing issues:** none found ("classify_part DC jack", "edge_actuator slide switch").

## 5. Two waiver channels: `fixed_poses[].accept_courtyard_overlap` is not read by check_assembly

- **Tool / command:** `py_tools/check_assembly.py --intent`.
- **What it claimed:** `BAT1 <-> DC1 courtyard 38.7 mm2 COURTYARD-BLOCKING` and `BAT1 <-> PWR_SW1 16.6 mm2`, although the intent waives both with `fixed_poses[].accept_courtyard_overlap: ["BAT1"]`. `place_simple` and `check_floorplan` honour that key (`fixed_pose_overlap_waived`).
- **What was true:** `check_assembly` reads only `overlap_waivers[]`. `floorplan.courtyard_waiver_pairs` is documented as "read by the plan check of fixed poses only". BAT1 draws no courtyard, so its pad-box fallback reaches into the gap between its own solder tabs, where both parts sit 0.87 mm or more clear of every BAT1 pad.
- **Workaround:** I added the same pairs to `overlap_waivers[]`.
- **Reproduce:** remove `overlap_waivers` from a copy of `intent_gp.json` and run `check_assembly` on `final.kicad_pcb` with it. Both pairs then gate.
- **Cost:** about 3 min.
- **Existing issues:** none found ("accept_courtyard_overlap check_assembly").

## 6. `list_nets --design-rules` suggests an impossible via (drill larger than the via)

- **Tool / command:** `python3 -X utf8 py_router/list_nets.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb --design-rules`
- **What it claimed:** `Manufacturing floor ... via 0.45/0.508` and `SUGGESTED route.py/... flags: --via-size 0.45 --via-drill 0.508`.
- **What was true:** the drill is wider than the via. `working_via_drill` = max(board `min_through_hole_diameter` 0.508, fab drill), but `working_via_diameter` = max(`min_via_diameter` 0.3, fab 0.45). The two floors are never reconciled (the diameter needs to be at least drill + 2 x annular).
- **Workaround:** I used the fab tier's own standard via, 0.45/0.2, and disclosed the authored-floor descent.
- **Cost:** about 2 min.
- **Existing issues:** #603 (closed) is the same family of "internally inconsistent manufacturing floor" (hole-to-hole); it does not cover this case.

## 7. kicad_drc_compare's `--baseline` subtracts by position, so footprint-inherent findings on moved parts read as router-introduced

- **Tool / command:** `python3 -X utf8 tests/stress/kicad_drc_compare.py <final> --baseline <input>` (kicad-cli on PATH).
- **What it claimed:** `kicad=8 (+2 pre-existing on input, subtracted) ... kicad_only=8 DIVERGED`, all `['<no net>', 'Net-(Q1-D)']` and `['<no net>', 'Net-(F2-Pad2)']` clearance at 0.0000 mm.
- **What was true:** all 8 come from the library footprints, not from routing. The same 8 appear on the UNROUTED placement (`kicad_drc/compare_placed.log`). Q1 and Q2 (CSD18534 PQFN) have drain pads 5-8 overlapping a net-less exposed pad 9. F2 is a PCB-trace fuse whose net-less fp_line touches both of its pads. Placement moved the parts, so the baseline's position match cannot recognise them.
- **Reproduce:** `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gp14/07_One-Air-Max/kicad_drc/placed.kicad_pcb --baseline wk/gp14/07_One-Air-Max/repro/input.kicad_pcb` returns the same 8 on a board with no copper.
- **Cost:** about 3 min to prove them inherent.
- **Existing issues:** none found.

## 8. render_placement's refusal names a flag it does not have

- **Tool / command:** `python3 -X utf8 py_tools/render_placement.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb -o x.png`
- **What it claimed:** "this board does not look PLACED ... Override with --allow-unplaced." It then renders anyway. Passing `--allow-unplaced` fails with `error: unrecognized arguments: --allow-unplaced` (exit 2).
- **Also:** its suggested crop commands write to `wk/worst1.png` and `wk/clean.png`, which is outside the run folder.
- **Cost:** about 1 min.
- **Existing issues:** none found ("allow-unplaced render_placement").

## 9. `place_pose rotate REF DEG` is absolute; `route_review` says "turn 180" (relative)

- **What happened:** route_review listed `R14 at ... rot 90: saves 1.0 mm` under "turn 180". `place_pose ... rotate R14 180` set the absolute angle 180, a quarter turn, and was refused (pad stack R14/U4). `rotate R14 270` was what was meant.
- **Cost:** about 1 min (one refusal).
- **Existing issues:** none found ("place_pose rotate absolute").

## 10. Gaps in the skill's instructions

- **No buildability step between the judge and the route.** SKILL.md §3.6 stops at "the first round whose best fast route has no blocking net", and §3.7 then routes. But the round's boards were not buildable (gap 2), and `board_score`'s `assembly` term counts that as blocking. The skill gives no step to repair assembly after `place_simple`, and says a part moved by hand is moved back. That is true only if you re-place.
- **The STANDARD-tier plane map cannot be followed on a board that keeps a multi-layer pour.** The routing skill prescribes inner-only pours for STANDARD boards. But the board's own GND zone is ONE zone on F.Cu, B.Cu and In2.Cu (design intent, kept by the campaign). `route_planes` cannot replace it per layer ("cannot be replaced for In2.Cu alone without destroying that copper"), so the outer GND floods ride along. The finalize then repaired 20 pads that reached only "a pinched fill island", and it joined GND islands with 2.0 mm GND tracks, including one on In1.Cu (the +3V3 plane layer).
- **The judge's route_review lists a poured net as open.** With `--quick 2` the plane finalize is skipped, so `route_review` reports "GND (poured): disconnected at C1, C11, ...". `quick_score` rightly scores it 0. A reader of the review alone would think the board has an open GND.
