# TOOL_GAPS -- gp14 board 06 (rp2350_fpga_eensy_prePlane)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`) with the venv first on PATH
(`export PATH="$HOME/.venvs/krt/bin:$PATH"`); `R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`.
The input boards each repro needs are copied into `repro/` (with `copy_board.py`).

---

## 1. place_simple's anneal counts a pin-frame container's whole-board rect as overlap, so no state is ever "best" (helper written)

- **Tool / command:** `py_placer/place_simple.py` (its anneal, `placement/simple_anneal.Annealer.overlap`), any seed on this board, e.g.
  `python3 -X utf8 py_placer/place_simple.py $R/fixed_u8lock.kicad_pcb $R/gap2_plain_s0.kicad_pcb --groups $R/groups.json --intent $R/intent_frame.json --seed 0`
- **What it claimed:** `WARNING: no legal pose found for: SW1` (exit 4). Every seed of round 1 left 3-5 parts with "no legal pose" (`J3, R2, U6`; `U1, U5`; `C1, L1, L2, SW1`; ...). A 4x `--moves` run still left `C27, SW1, U5`. It reads as "the board is too full".
- **What was true (measured):** the Teensy40 frame U8 has no courtyard, so its rect is its pad bbox -- the whole board (138.575..158.425 x 87.695..123.82). `Annealer.overlap` sums grown-rect overlaps over every pair sharing a face and does not skip `state.container_refs` (the halo term does: `simple.py` "a container is a frame, not a body"). On a finished seed the overlap term was **464.5 mm2, of which 442.0 mm2 is U8-frame pairs**. So `v['ov'] < CLEAN` is never true (no state ever becomes the best one), `escape` fires for every part all run, and `repair` can never come clean. With the frame given no face in that term (`helpers/place_simple_frame_fix.py`) plus keep-outs over U8's pin rows (`intent_frame.json`, because the pins are then priced only by the final legality) the same seed is **legal on its first run** (`annealed 30000 moves in 10.1 s`, exit 0), and round 2 gave **11/12 legal seeds** against 0/12. Keep-outs alone (plain place_simple + intent_frame) still left SW1 illegal -- the helper is the part that matters.
- **Reproduce:**
  ```bash
  python3 -X utf8 py_placer/place_simple.py $R/fixed_u8lock.kicad_pcb $R/gap2_plain_s0.kicad_pcb --groups $R/groups.json --intent $R/intent_frame.json --seed 0     # exit 4, SW1 illegal
  python3 -X utf8 wk/gp14/06_rp2350_fpga_eensy_prePlane/helpers/place_simple_frame_fix.py $R/fixed_u8lock.kicad_pcb $R/gap2_helper_s0.kicad_pcb --groups $R/groups.json --intent $R/intent_frame.json --seed 0   # exit 0
  ```
  The 442-of-464.5 split: build the model as `place_simple.build` does on `scratch/t_4x_s0.kicad_pcb`, then sum `Annealer._grown(r)` x `_grown('U8')` intersections over the movable parts (done inline this run; no file kept).
- **Helper:** `helpers/place_simple_frame_fix.py` (monkeypatches `Annealer.__init__` to zero the container's face bits; points `place_simple.__file__` at itself so `--round` seed processes get it too).
- **Existing issues:** `gh issue list --search "container overlap anneal place_simple"` and `"pin frame overlap place_simple"`: none. Related but different: #1212 (frame pins not checked by graders, closed), #1213 (seeder prices a hollow container by its extent, closed), #1184 (seeder exempts containers, closed).

## 2. place_simple refuses a declared pose whose castellated half-holes sit on the outline -- every seed exit 4, judge.json empty

- **Tool / command:** `py_placer/place_simple.py` (`placement/seeder._fixed_pose_check` -> `_holes_outside`), on the given input and intent:
  `python3 -X utf8 py_placer/place_simple.py $R/input.kicad_pcb $R/gap1_s0.kicad_pcb --groups $R/groups.json --intent $R/intent.json --seed 0 --moves 3000`
- **What it claimed:** `WARNING: U8's declared pose is not legal: 33 of 66 drill hole(s) past the outline`, then `no legal pose found for: ..., U8`, exit 4. With `--round`, all 12 seeds listed U8 and `judge.json` named no seed ("judge seeds none"), so round 1 produced nothing the skill lets you judge.
- **What was true:** the 33 holes are the frame's castellated half-holes (`(property pad_prop_castellated)`, centred ON the outline by design -- a Teensy-footprint board). The pad-copper test exempts castellated pads; the hole test does not. check_assembly, check_floorplan and render_placement all accept the same pose ("on the outline by design, not gated: U8 (castellated pads...)").
- **Workaround:** lock U8 at the mechanical.json pose with `place_pose ... set U8 148.5 105.005 --rot 270 lock U8` (skill 3.1) and drop U8's `fixed_poses` row in a variant intent (`intent_u8lock.json` -> `intent_frame.json`).
- **Existing issues:** `"castellated declared pose"`, `"fixed_poses castellated"`, `"castellated"`: none covers it (#1257 is the seat search vs pad copper past a courtyard, closed; #324 drill-offset paddles, closed).

## 3. The intent's error-graded decap limit is out of the anneal's reach for an 0805 bulk cap (scoped re-anneals + hand poses needed)

- **Tool / command:** `place_simple.py --decap-limit-weight N` against `intent.json`'s `decaps.max_distance_mm 1.0925` (cap pad centroid to the owner chip's pad bbox), graded at ERROR by check_floorplan and so by board_score's `floorplan` -> `blocking`.
- **What it claimed:** nothing wrong -- the seed is "legal"; `check_floorplan` then reports e.g. `decap_distance: C27 is 1.22mm from U7, the IC it decouples (limit 1.09mm)`. Scoped re-anneals of r2/s7 with everything but the caps locked, at `--decap-limit-weight 100 / 300 / 1000` and `--moves 60000`, left C27 at 1.22 mm on 9 of 10 seeds.
- **What was true:** for C27 (0805, courtyard half-width 0.98 mm) the limit is reachable only against an owner side whose pad bbox has ~0 margin to its courtyard -- U7's north/south sides (1.07 mm with the 0.09 gap), RN1/RN2 -- never on U7's pin side (margin 0.15 -> >= 1.22 mm) or any QFN/WLCSP side. The decap term pulls the cap to the supply PIN (VOS, on U7's pin side), so the anneal sits in a local minimum the limit cannot price its way out of. Fixed by hand: C27 south of U7 at (153.5, 102.16, 0), C7 and C15 moved out of its way (CHOSEN.json `after`).
- **Reproduce:** `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/06_rp2350_fpga_eensy_prePlane/scratch/s7_fx30_0.kicad_pcb --intent $R/intent.json` -> 1 error, C27 1.22 mm from U7 (that board is a scoped re-anneal at weight 100; `scratch/fix/b3_0.kicad_pcb` is the weight-1000 one, same answer).
- **Existing issues:** `"decap_distance 0805"`: none.

## 4. route.py leaves kicad-dangling micro-segments that fail check_complete, and no repo actor removes them (helper written)

- **Tool / command:** `py_router/route.py` (final chain `final_route/plan.sh`, both route.py steps), graded by `check_complete.py` (`weird_copper` = `py_router/check_weird.py`).
- **What it claimed:** `JSON_SUMMARY_MIN ... "failed": 0`, board_score blocking 0 -- but `check_complete` says `INCOMPLETE -- weird_copper: not clean`.
- **What was true:** 1 (first chain) or 3 (via-cost-150 chain) power-width segments 0.011-0.025 mm long, e.g. `GND (F.Cu) segment (150.200, 112.714)-(150.200, 112.700) w0.200: both ends lie on other GND track(s) ...` -- KiCad's track_dangling. A closing `route.py --nets GND +3V3` pass, a `--rip-existing-nets GND` pass and eleven route variants all left at least one. Deleting exactly those segments (each is fully covered by the tracks holding both its ends) gave check_complete DONE with connectivity unchanged (check_connected "ALL NETS FULLY CONNECTED", board_score unchanged).
- **Reproduce:** `python3 -X utf8 py_router/check_weird.py $R/s7_close.kicad_pcb` -> `kicad-dangling: 3`; `python3 -X utf8 wk/gp14/06_rp2350_fpga_eensy_prePlane/helpers/drop_kicad_dangling.py $R/s7_close.kicad_pcb $R/s7_clean.kicad_pcb` removes them.
- **Helper:** `helpers/drop_kicad_dangling.py` (runs check_weird's own analysis, deletes only `kicad-dangling` segments, refuses any longer than 0.05 mm).
- **Existing issues:** `"kicad-dangling"`: #1234 OPEN (route.py leaves chains of 0.025-0.075 mm segments, nothing reports them) and #162 OPEN (same-net redundant copper, delete-only removal) cover the producer; #1217 (detection, closed) and #1291 (off-grid tap points -> dangling T-junction stubs, closed 2026-10-20, likely not in this worktree's 8328f157).

## 5. converge.py refuses a board_score-scored completion after the skill's quick_score-scored judging rows

- **Tool / command:** `py_placer/converge.py record --kind completion --score-file <board_score json>` after the round's `--kind completion` rows scored with `py_tools/quick_score.py` (what SKILL.md 3.6 step 2 prescribes).
- **What it claimed:** `record: this lap looks like an IMPROVEMENT only because it graded FEWER components ... Nothing was written.` (exit 2).
- **What was true:** quick_score's payload has `blocking_by {"broken": N}` and no `ungraded`, so `ungraded_set()` reads it as grading everything; board_score honestly lists `impedance, length, net_widths` as ungraded. The full-route row graded MORE, not fewer. Workaround: recorded the first full route with a quick_score payload too (blocking 2 -> 0 like for like), then the DONE row with board_score (0 -> 0 is only warned).
- **Reproduce:**
  ```bash
  rm -f $R/gap4_ledger.jsonl
  python3 -X utf8 py_placer/converge.py record --ledger $R/gap4_ledger.jsonl --board $R/s7_fast.kicad_pcb --kind completion --parent $R/input.kicad_pcb --lever "fast route" --score-file $R/quick.score.json
  python3 -X utf8 py_placer/converge.py record --ledger $R/gap4_ledger.jsonl --board $R/final_copy.kicad_pcb --kind completion --parent $R/s7_fast.kicad_pcb --lever "full route" --score-file $R/board.score.json   # exit 2, nothing written
  ```
- **Existing issues:** `"quick_score converge commensur"`, `"converge record ungraded quick_score"`, `"quick_score"`: none.

## 6. Skill gap (plan-pcb-routing): the QFN fanout step does not exclude the plane nets, and its stubs on them end as dangling copper

- **Tool / command:** `py_router/qfn_fanout.py --component U6` as the routing skill's QFN section writes it (no `--nets`), followed by the pour-first chain.
- **What it claimed:** `escaped 35/35, failed 0`, drc_grazes 0.
- **What was true:** the stubs it lays on GND/+3V3 pins (e.g. U6 pin 47 VREG_PGND) are left as free ends once route.py welds those pins to the pours: `dangling-end: GND (F.Cu) at (143.300, 111.600) ... rooted at (143.492, 111.400)` -> check_complete INCOMPLETE. The skill tells you to exclude plane nets for `bga_fanout` (Step 1b, "that exclusion marks them for plane-drop vias") but its `qfn_fanout` examples carry no `--nets`. With `--nets '*' '!GND' '!+3V3'` the dangling ends went away.
- **Reproduce:** `python3 -X utf8 py_router/check_weird.py $R/v2_qfn_plane_stubs.kicad_pcb` -> `dangling-end: 2` (that board is the chain with the skill's qfn_fanout command).
- **Existing issues:** `"qfn_fanout plane nets dangling stub"`: none specific (#84, orphan dead-end stubs on multipoint nets, closed, is a different producer).

## 7. Skill gap (plan-pcb-placement 3.5/3.6): no path for a round in which EVERY seed is illegal

- **What happened:** round 1 ended with `judge.json` `"judge": []` (all 12 illegal, gaps 1-2). The skill says never judge or keep an illegal seed, and its review loop (3.6 steps 3-6) starts from "the best fast route" -- of which there was none. It does not say whether such a round counts toward `--rounds`, or what input to change. I counted it as round 1, diagnosed the tools, and changed the inputs (lock + keep-outs + helper + `--decap-limit-weight 30`) for round 2; round 3 was the one review round.
- **Reproduce:** `wk/gp14/06_rp2350_fpga_eensy_prePlane/r1/judge.json`.
- **Existing issues:** `"all seeds illegal judge"`: none.

## 8. route_planes lowers the board's declared copper-to-hole floor without being asked

- **Tool / command:** `py_router/route_planes.py ... --nets GND +3V3 --plane-layers In1.Cu In2.Cu` (final_route s1).
- **What it claimed:** `FAB FLOOR RELAXED ... copper-to-hole clearance: 0.25 -> 0.09 mm` written to the output `.kicad_pro` (disclosed, then every checker grades the new value).
- **What was true:** the board declared `min_hole_clearance 0.25`; the shipped board has 199 items at down to 0.1431 mm against it (`check_complete --authored-from`: UNSOUND, via annular ring 0.1 -> 0.05 being the other relaxed floor). Disclosed, but a floor the author set moved by a pour step nobody asked to change it.
- **Reproduce:** `python3 -X utf8 py_router/route_planes.py $R/placed.kicad_pcb $R/pour.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu` and read the "FAB FLOOR RELAXED" block.
- **Existing issues:** `"min_hole_clearance"`: #1285 (CLI --no-fix-drc-settings still lowers min_hole_clearance, closed), #1198 (closed), #1217 (copper-to-hole announcement, closed).

## 9. A KiCad connection_width warning no repo checker reports

- **Tool / command:** `tests/stress/kicad_drc_compare.py final.kicad_pcb --baseline <input>` (KiCad 10 kicad-cli).
- **What it claimed:** `kicad=0 check_drc=0 ... CONSISTENT`, plus `CONNWIDTH track ['Net-(J1-D+-PadA6)'] @ (147.55, 94.85) Copper connection too narrow ... <0.075mm` (project severity: warning).
- **What was true:** check_weird (`narrow-pad-joint: 0`), check_drc and check_complete all call the board clean; only the KiCad leg sees the narrow web at J1's D+ pad. The verifier's own kicad-cli run (zones refilled) adds a second KiCad-only item on the same board: **1 track_dangling**, a 0.1 mm GND stub on F.Cu at (154.1, 91.4)-(154.1, 91.5) whose end lies on another GND track -- `check_weird` reports `NO WEIRD THINGS FOUND` on it (its #1217 kicad-dangling rule abstains when a via, pad or zone touches the segment). Both are KiCad warnings, not errors; connectivity is intact.
- **Reproduce:** `python3 -X utf8 tests/stress/kicad_drc_compare.py $R/final_copy.kicad_pcb --baseline $R/input.kicad_pcb` (needs `/Applications/KiCad/KiCad.app/Contents/MacOS` on PATH).
- **Existing issues:** `"connection_width narrow USB pad"`: #547 (tap landings churn connection_width webs, closed).

## 10. Minor

- **board_score `--quiet` still prints the full `SCORE_JSON=` line** (21 kB on this board per call): `python3 -X utf8 py_tools/board_score.py $R/input.kicad_pcb --quiet --json $R/bs_quiet_probe.json | wc -c` -> 21318. It filled the context on every ledger score. No issue found.
- **Resistor arrays and an RGB LED are elected decap "owner ICs":** `python3 -X utf8 py_tools/check_floorplan.py $R/rn_owner.kicad_pcb --intent $R/intent.json` -> `decap_distance: C25 is 2.54mm from RN1, the IC it decouples` (RN1 is a 10k pull-up array; D1, the RGB LED, is also an owner of +3V3). It decides which part a cap is graded against. No issue found.
- **place_pose's `legal` can never be true on this board:** `python3 -X utf8 py_placer/place_pose.py $R/placed.kicad_pcb $R/pp_probe.kicad_pcb --dry-run rotate C2 0` -> `"legal": false`, `pad_edge_conflicts_after: 33` (U8's castellated pads), on a board check_assembly calls buildable. `no_worse` is the usable verdict. No issue found.
