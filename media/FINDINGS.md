# gp14 findings, verified at 8328f157

Each candidate (from FINDINGS_CLUSTERED.md) re-run by a separate verifier subagent at the pin; checked against branch head 86b54a1d and main 0523df20, and against upstream issues (read-only searches). Verdicts: 38 CONFIRMED, 31 CONFIRMED-PARTIAL, 7 NOT A BUG. Nothing filed yet.

<!-- batch B01 -->
### H01 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster's 03 command with output `wk/gp14/_verify/B01/h01_out.kicad_pcb` (about 5 s).
  - route.py: `JSON_SUMMARY_MIN failed 0`. board_score: `BLOCKING=0`.
  - check_weird: `kicad-dangling: 1`, net /ampli_ht_horizontal/S_OUT+ F.Cu (115.600, 81.773)-(115.627, 81.800) w0.400. This is the teammate's segment exactly.
  - check_complete: `INCOMPLETE -- weird_copper`, exit 4.
  - kicad-cli DRC: exactly 1 `track_dangling`, at (115.6, 81.773), "length 0.0381 mm".
  - Counterfactual: the same run with only `get_all_segment_tap_points` swapped in-process for upstream/main's #1291 version gives `NO WEIRD THINGS FOUND!` and check_complete `DONE` (`h01_fix1291_out.kicad_pcb`).
  - Not every instance is #1291. I replayed 06's s6 route step (`final_route/redo_commands.sh` line 18), plain and with the #1291 patch. Both leave 1 kicad-dangling: /T8F49I2X/PIN.22 In3.Cu (151.210, 111.860)-(151.200, 111.900), 0.0413 mm, off-grid and not octilinear. KiCad confirms it as `track_dangling` (`h01_06_fix_kicad_drc.json`). My replay does not reproduce the teammate's s6 copper byte for byte (mine has failed 2, different stubs).
  - The 04 "3.677 mm /CH1/OUT dangling end" variant is a mislabel; see M13.
  - Not checked: 06 #9 (check_weird abstaining at (154.1, 91.4)), 07, 08, 11, 14.
- cause: `py_router/single_ended_routing.py:4707` `num_steps = max(1, int(length / coord.grid_step))` truncates the step count. Tap points land 27-71 µm off grid, and a route launched from one leaves a sub-cell T stub. This is #1291 exactly, shown by the counterfactual. The 06 residual has another source that I did not establish.
- branch head 86b54a1d: unchanged (same line 4707). main 0523df20: differs; the #1291 fix b0e934c1 is at main `single_ended_routing.py:4838-4840`. b0e934c1 is on main only, not an ancestor of the pin or of 86b54a1d.
- upstream: duplicate of #1291 (closed). Its fix needs main merged into grouped-placement. The 06 residual is evidence for #1234 (open). Searches: track_dangling, "dangling stub tap", kicad-dangling, micro-segment, "off-grid T stub".
- severity after verification: MEDIUM. It blocks DONE, but check_complete catches it and the main fix exists.

### H03 -- VERDICT: CONFIRMED
- repro at 8328f157: I replayed 07's three route.py steps (redo lines 5/6/7) from `repro/gap3_route_in.kicad_pcb`, which is byte-identical to `final_route/s3_diff`. Outputs are `h03_07_s4/s5/s6.*`.
  - s4 (the producing pass): no stacked WARNING in the log, no `stacked_copper` key in the json, and check_weird `stacked-copper: 9`. By an exact-endpoint count, 38 duplicate groups with 54 surplus copies, all on GND B.Cu (45) and PGND B.Cu (9). The input has 0.
  - s5 and s6: `WARNING: 38 stacked-copper finding(s)`, and json `stacked_copper` has 38 entries, yet the copies still ship: 54 surplus in s6, identical to the teammate's gap3_route_out.
  - Instrumented s4 (`h03_07_s4probe.log`): 0 duplicates on the output file before the finalize's `repair_planes`, 46 right after it (GND 39, PGND 7), 54 when the end-of-run strict collapse reads the board.
  - 30 of the 38 groups have an end at a site the finalize's pad repair logged as "reused via at (x, y)". Most are 0.01-0.06 mm long.
  - The 14 board shows the same thing on +3V3 B.Cu: 11 groups, with the warning (`h20_route.log`).
- cause:
  - The census `stacked_copper_over_model` (`py_router/route.py:4400`, inside batch_route) runs before the plane finalize (`_rdp_engine`, route.py:6295), which lays the duplicates. That is why the producing pass discloses nothing.
  - No later pass removes them: the strict collapse skips zoned nets (`py_router/pcb_modification.py:2870,2891`), and the via dedup is vias-only.
  - Correction to the cluster's "on 07 nothing disclosed it": the later passes do warn.
- branch head 86b54a1d: unchanged. main 0523df20: same code. The census sits at main route.py:4346, before the finalize. Main-only repair_planes changes (#1290) touch edge/snpc forwarding only.
- upstream: evidence for #162 (open). #606's comment (now merged into #162) already names the finalize-after-census ordering. New here is the producer: repair_planes pad repair at reused vias. Searches: "stacked copper", "duplicate segments finalize", "repair_planes duplicate", "reused via duplicate", "stacked-copper census".
- severity after verification: MEDIUM. check_complete catches it, but no repo tool removes it.

### M13 -- VERDICT: NOT A BUG
- repro at 8328f157: I ran the cluster's four commands on `04/repro/s2r_v125_step4.kicad_pcb`.
  - board_score `BLOCKING=0`. check_orphan_stubs `NO ORPHAN STUBS FOUND!`.
  - check_weird: `dangling-end` /CH1/OUT 3.677 mm at (131.400, 142.900), plus `stacked-copper` GND F.Cu (152.6, 116.2)-(152.7, 116.3).
  - check_complete: `INCOMPLETE -- weird_copper`, exit 4.
  - The "dangling" segment (128.8, 140.3)-(131.4, 142.9) is not dangling. Its end cap overlaps the body of same-net track (132.4, 143.1)-(131.2, 143.1): 0.20 mm from the centreline, with 0.30 mm of combined half-widths.
  - Removing it in a copy (`m13_minus_seg.kicad_pcb`) makes check_connected report /CH1/OUT in 2 components, with C40 pad 2 disconnected.
  - KiCad DRC flags no `track_dangling` on /CH1/OUT (`m13_kicad_drc.json`).
- cause:
  - board_score having no weird-copper component is documented at `check_complete.py:19-20` ("IT HAS NO COMPONENT AT ALL for orphan stubs, weird copper..."). check_complete is the DONE gate.
  - The skill defines `full`-mode DONE as including `check_complete` DONE (`.claude/skills/plan-pcb-placement/SKILL.md:33`, again at :382). The §5.6 ledger example records the score only; it does not define DONE.
  - check_orphan_stubs is right by its own criterion 2: the cap overlaps another same-net track body (`py_tools/check_orphan_stubs.py:7-9`).
  - Side finding: check_weird is wrong here. `pcb_modification._point_anchored` credits a track landing only when the end's centre lies within the other track's half-width + 0.025 (`py_router/pcb_modification.py:95`). It does not add the stub's own half-width, although its via and pad branches do (:54, :58). This is the #1167 fix for check_orphan_stubs, not mirrored into the shared anchor.
- branch head 86b54a1d: unchanged. main 0523df20: same code (board_score and check_orphan_stubs have no main-only changes; pcb_modification.py:95 is identical).
- upstream: no grader-gap issue applies. The side finding is new: a sibling of closed #1186 (on-centreline near the end) and #1167 (check_orphan_stubs half-width). Searches: "check_weird dangling-end false", "dangling-end cap overlap", "check_weird free end overlap".
- severity after verification: none. The side finding is LOW.
- issue draft (side finding only):
  - title: check_weird calls a segment "dangling-end" when its end cap overlaps a same-net track off-centreline, and removing it disconnects a pad
  - body:
    - On `wk/gp14/04_multichannel_mixer/repro/s2r_v125_step4.kicad_pcb`, check_weird reports `dangling-end: net /CH1/OUT (F.Cu) at (131.400, 142.900): free end, dangling segment 3.677mm`.
    - The segment's end is 0.20 mm off the centreline of the 0.3 mm track (132.4, 143.1)-(131.2, 143.1). The copper overlaps by 0.10 mm.
    - check_orphan_stubs and KiCad (no track_dangling) treat it as connected. Removing it disconnects C40 pad 2 (`check_connected --nets /CH1/OUT` on `wk/gp14/_verify/B01/m13_minus_seg.kicad_pcb`: 2 components).
    - Cause: `_point_anchored`'s track branch (`pcb_modification.py:95`) tests `dist < max(tol, w_other/2 + 0.025)` without the stub's own half-width, unlike its via and pad branches.
    - Expected: credit the joint as anchored, as #1167 did for check_orphan_stubs, or report it as a soft joint. It should not be offered as a dead end.

### H20 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster command on `14/repro/collapse_noop.kicad_pcb` (`(version 20240108)`; 2755 segments carry `(net "/name")`, 259 carry `(net N)`), with output `h20_out.kicad_pcb`.
  - The log prints `Strict collapse (#1063, end of run): removed 291 redundant segment(s) on 100 net(s)`.
  - Segments are 3014 in and 3014 out. check_weird is identical before and after: removable-segment 144, stacked-copper 4, kicad-dangling 6.
  - Instrumented run (only `remove_segments_from_content` wrapped, `h20_probe.log`): `targets=291 matched=0 map=None | with name map: 291`.
- cause: `py_router/route.py:857` `_map = name_of if _k10_1063(_c) else None` gates the name map on the version stamp.
  - Without the map, `kicad_writer.remove_segments_from_content`'s `_canon` (kicad_writer.py:1591-1592) keys the targets by numeric id while each name-ref block resolves to its name, so no name-ref block matches.
  - The returned count is discarded (`_c, _ = _rsc1063(...)`, route.py:859), and the print uses `len(removed)`.
  - The same version gate sits at route.py:1114 (#1166 dangling-via sweep), :1205 (#659 orphan sweep) and :5773. I did not measure those. route.py:1016 uses `board_uses_name_nets` instead.
  - Only the CLI is affected; the GUI path uses `return_results`.
- branch head 86b54a1d: unchanged. main 0523df20: same code (`_late_strict_collapse1063` is byte-identical, gate at main route.py:799).
- upstream: new. It is the same mixed-dialect class as closed #817, whose per-block canonicalisation only works when the caller passes `net_id_to_name`. Searches: "strict collapse", "mixed dialect", "remove_segments_from_content", "is_kicad_10 name map", "net_id_to_name strip".
- severity after verification: MEDIUM. The report is false and the copper is left in place; check_complete catches the leftovers.
- issue draft:
  - title: route.py's end-of-run strict collapse (#1063) prints "removed N" but strips nothing on a pre-KiCad-10 board whose copper uses name refs
  - body:
    - On a `(version 20240108)` board with name-ref segments (`wk/gp14/14_imx6ulz_4l/repro/collapse_noop.kicad_pcb`: 2755 name-ref and 259 numeric-ref segments), route.py prints `Strict collapse (#1063, end of run): removed 291 redundant segment(s) on 100 net(s)`. The written file still has 3014 of 3014 segments, and check_weird's removable-segment count is 144 before and after.
    - Wrapping `remove_segments_from_content` in an otherwise unchanged run: 291 targets, 0 matched, `net_id_to_name=None`. The same call with the board's name map matches all 291.
    - Cause: `_late_strict_collapse1063` (route.py:857) passes the map only when `is_kicad_10(content)`. Without it, #817's per-block matcher compares numeric target ids against block names. The returned count is discarded and the print reports `len(removed)`.
    - The same gate is at route.py:1114, :1205 and :5773 (not measured).
    - Repro (about 11 s): `R=wk/gp14/14_imx6ulz_4l/repro; python3 -X utf8 py_router/route.py $R/collapse_noop.kicad_pcb OUT.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 1.5 1.0 --no-bga-zones --max-ripup 5 --via-cost 250 --power-nets GND +3V3 --power-nets-widths 0.2 0.2`, then `check_weird.py` on input and output (`removable-segment: 144` both).
    - Expected: pass the name map whenever the file carries name refs (`board_uses_name_nets`, as route.py:1016 does), and report the count actually stripped.

### M25 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster command on `04/repro/pour_s3.kicad_pcb` (about 47 s), with output `m25_out.kicad_pcb`.
  - The log matches the claim: `KiCad-oracle recheck: 5 link(s) still unconnected per KiCad after 3 round(s)`, `JSON_ORACLE ... "remaining": 5`, `GND: exact-fill verdict OPEN`, and the reconciliation subset ends `0/1 routed (1 FAILED) GND`.
  - Yet the final tally reads `Multi-point: 177/177 pads connected` and `Recovered after a summary reported them failing: 2`, and `JSON_SUMMARY_MIN` has `failed 0, multipoint_deficit 0, pad_pairs_open 0`.
  - `--json-out`: `regrade.recovered ["GND","Net-(IC5A-OUT)"]`, `oracle_check "disabled"`, no oracle key.
  - check_connected: `GND ... UNCONNECTED per KiCad refill`, 5 components, exit 1.
  - board_score: `BLOCKING=4 (broken=4)`, GND joins_needed 4. The cluster quoted broken=1.
  - Same grader both ways (`improvement_gate.grade_nets`): on the fill model GND is not broken; after `install_kicad_fill(refill_islands_ex(...))` it is broken with 5 failed pads (IC1, C21, IC4, IC2, IC3).
  - Not verified: the "23 of 33 routes" statistic.
- cause: `_regrade_pour_fill` (`py_router/route.py:424-427`) returns None, skipping KiCad's refill, whenever any summary carries an available `oracle_reconnect`, on the premise that the oracle already checked the pours. The oracle's `remaining` links are not folded into the re-grade, so `_final_regrade` (route.py:516) grades GND on the raster model and moves it to `recovered`.
- branch head 86b54a1d: unchanged. main 0523df20: differs. Main has no `_regrade_pour_fill` at all (added on the branch by 99a9575f), so main's #1069 re-grade reads pours on the fill model in every case and the same false credit applies there unconditionally.
- upstream: new. It is the same model-credit pattern as closed #572 (whose forced oracle links fired here and failed, boxed in), now at the #1069 end-of-run re-grade. Searches: "regrade oracle remaining", "JSON_SUMMARY_MIN failed 0 GND", "final re-grade fill model", "oracle remaining links summary", "exact-fill verdict OPEN", "Recovered after a summary reported them failing", "1069 regrade zone".
- severity after verification: MEDIUM. board_score and check_connected catch it, but `JSON_SUMMARY_MIN` and `--json-out` say clean.
- issue draft:
  - title: route.py's end-of-run re-grade reports GND "recovered" (failed 0) after its own oracle left 5 exact-fill links open
  - body:
    - Measured run: `P=wk/gp14/04_multichannel_mixer/repro; python3 -X utf8 py_router/route.py $P/pour_s3.kicad_pcb OUT.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 150 --json-out OUT.json` (about 47 s).
    - The oracle ends with `remaining: 5` GND links, and the reconciliation reports GND FAILED (boxed in).
    - The final re-grade then prints `Multi-point: 177/177`, `Recovered after a summary reported them failing: 2`, and `JSON_SUMMARY_MIN failed 0, multipoint_deficit 0`. `--json-out` has `regrade.recovered: ["GND", ...]`.
    - `check_connected.py OUT.kicad_pcb`: GND unconnected per KiCad refill, 5 components. board_score: broken 4.
    - Cause: `_regrade_pour_fill` (route.py:424-427) skips KiCad's refill when the oracle ran, but nothing carries the oracle's remaining links into `_final_regrade`, which then grades the pour on the raster model. On the same file, `grade_nets` gives GND connected on the model and broken (5 pads) after `install_kicad_fill`.
    - Expected: a net with oracle `remaining_links` is graded open in JSON_REGRADE, JSON_SUMMARY_MIN and `--json-out`, either by folding the oracle verdict in or by grading pours on KiCad's refill regardless.

Notes:
- All outputs are in `wk/gp14/_verify/B01/`. The probe scripts are in `<tmp>
- One stray write outside B01: my kicad-cli DRC on the M13 board created `wk/gp14/04_multichannel_mixer/repro/s2r_v125_step4.kicad_prl`. It is a KiCad local-settings sidecar in gitignored `wk/` that did not exist before. I left it in place because the rules forbid deleting files; it is safe to remove.
- No tracked file changed (`git status` is clean).

<!-- batch B02 -->
### H02 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `check_floorplan.py 05/repro/r1_s8.kicad_pcb --intent 05/repro/intent.json` exits 4 with 3 x `[ERROR] decap_pin_distance`: U9 D11 39.01, G12 41.19 and L10 37.23 mm from C1, against a limit of 34.08 mm.
  - `r1_judge.json` reads `"judge": [8, 7, 3, 4, 9, 5]`, `"illegal": []`.
  - `05/r1/s*.json` gives decap_broken per seed: s8=3 (cheapest, cost 5329.5), s7=1, s3=0, s4=0, s9=0, s5=0.
  - `quick_score.py r1_s8_fast --route r1_s8_route.json` gives `blocking=1 vias=107` with `blocking_by {"broken":1}`. The decap-clean s3 scores blocking 3. So the skill's "keep the best by blocking" keeps s8, which cannot reach DONE.
  - `board_score.py 13/repro/r1_s6 --intent ... --baseline ...` gives `blocking_by.floorplan=8`: the full grade counts these as blocking.
  - On board 14 (see M02), place_simple prints "1 decap limit(s) broken" and exits 0. Outputs are in `wk/gp14/_verify/B02/H02_*`.
- cause:
  - `py_placer/place_simple.py:359-361`: `_name_judged` filters only on `illegal`, not `decap_broken`.
  - `py_tools/quick_score.py:9-13,53-58`: no floorplan term. Its docstring says so on purpose.
  - `.claude/skills/plan-pcb-placement/SKILL.md:337-338` and `:366` keep and stop on quick_score blocking.
  - The §3.5 "Check and LOOK" step (`:300`) names check_assembly and render only, not check_floorplan, although DONE (`:32`) requires `check_floorplan --intent` 0 errors.
  - Each part is documented on its own; the defect is how they combine.
- branch head 86b54a1d: unchanged in substance. quick_score was rewritten (4e0deaee) but still "DRC, assembly and the floorplan are left out". `_name_judged` is unchanged, and the skill's §3.7 step 3 still says "Keep the best by blocking". main 0523df20: not on main (no place_simple, quick_score or skill there).
- upstream: new. Searches: "quick_score floorplan", "judge decap", "judge.json decap_broken", "seed judge floorplan", "decap limit broken judge", "quick_score blocking". Nearest are #1267 (open, seeder decap claims) and #1258 / #1043 (closed); none is about the judge.
- severity after verification: HIGH (it cost board 05 a whole round; the ranking is silently wrong until board_score or check_complete runs).
- issue draft:
  title: Seed judge ranks and stops on placements with error-graded floorplan findings: judge.json filters only `illegal`, quick_score has no floorplan term
  body: `place_simple --round` names the judged seeds by `final.cost` among seeds whose `illegal` list is empty. A seed with `decap_broken > 0` is named, and since the broken limit lowers its cost, often first. quick_score then ranks by route tally only. The skill keeps the best by that blocking and stops at blocking 0. But DONE needs `check_floorplan --intent` 0 errors, and `board_score --intent` counts every floorplan error in `blocking`. Measured on gp14 board 05, round 1: judge.json is `[8,7,3,4,9,5]`. s8 has decap_broken 3: `check_floorplan` reports U9 D11/G12/L10 at 39.01/41.19/37.23 mm against a 34.08 mm limit, yet quick_score gives it blocking 1 / 107 vias, the round's best. s3 (decap_broken 0) scores blocking 3. Board 13: r1_s6 has `board_score` floorplan=8 and was the judge's pick. Repro: `check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent.json`; `cat wk/gp14/05_interf_u/repro/r1_judge.json`; `quick_score.py wk/gp14/05_interf_u/repro/r1_s8_fast.kicad_pcb --route wk/gp14/05_interf_u/repro/r1_s8_route.json`. Expected: the judge and the keep/stop rule rank on error-graded floorplan findings before route blocking. Either judge.json orders by (decap_broken + claim_broken, cost), or quick_score takes `--intent` and adds a floorplan term, or the skill runs check_floorplan before keeping a seed.

### M02 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `place_simple.py 14/repro/r1_fixed.kicad_pcb B02/M02_14_out_s2.kicad_pcb --groups r1_groups.json --intent r1_intent.json --seed 2` exits 0 with "1 decap limit(s) broken", `"decap_limits": 5.0, "decap_broken": 1, "illegal": []`.
  - `check_floorplan` on that board exits 4: `U1 pin P12 (/SOC Power/VDD_SNVS_IN) is 22.34mm from C20 (limit 8.46mm)`, which is 13.9 mm past the limit.
  - The rail carries exactly one cap: VDD_SNVS_IN pads are C20, U1, U5, U8. The intent has `max_pin_distance_mm` 8.455 and `within_radius_mm` 5.0.
  - Board 13 `r5_s6`: 4 decap_pin_distance errors: U3 p10 4.52, U3 p33 3.31, U6 p29 3.55 and U6 p33 2.93 mm against 2.19.
  - On this branch, `py_placer/` has no place_seed.py and no `--repair-decaps`.
- cause: `py_placer/placement/simple.py:1270-1283` with `:1336-1338`. A pin limit wider than the tether radius (5 mm) is priced at `min(over, reach)`, on the stated assumption that "any cap on the rail meets it". With one cap on the rail that assumption fails. The penalty is flat (5.0) beyond limit+5 mm, so nothing pulls C20 back.
  - The confirmed part is the 14 mechanism, the 13 reproduction, and the absent repair CLI.
  - Not verified: 06 (whose limit comes from the given intent) and 09 / 12. "The anneal does not always meet a soft limit" alone is a property of a penalty term, not a bug.
- branch head 86b54a1d: unchanged (`_over_limit` now at simple.py:1376-1378; place_seed is still absent). main 0523df20: differs. simple.py is not on main; main has `place_seed.py --repair-decaps` (#1188 fixed there).
- upstream: new for the pricing cap. Related closed issues: #1188 (repair rung, main only), #1249 (its fix 0b2aeb47 is on the pin and does not cover this), #1150. Searches: "decap pin distance radius", "place_simple decap", "decap limit tether radius", "one cap rail pin limit", "repair-decaps grouped-placement", "decap_pin_distance unreachable".
- severity after verification: MEDIUM.
- issue draft:
  title: place_simple prices a supply-pin decap limit wider than the 5 mm tether radius at a flat 5 mm past the limit, so a one-cap rail's pin is left far past it
  body: `PlacementModel.set_limits` treats a `max_pin_distance_mm` term whose limit exceeds the tether radius as "no tether", because "any cap on the rail meets it". `_over_limit` caps it at `min(over, radius)` (simple.py:1282-1283, 1338). On a rail with a single cap that assumption is false, and the term has no gradient past limit+5 mm. gp14 board 14: VDD_SNVS_IN's only cap is C20. With limit 8.455 mm and radius 5.0, seed 2 leaves U1 P12 22.34 mm from C20. The report reads `decap_limits 5.0, decap_broken 1`, exit 0, and the teammate measured 33 of 36 seeds. Repro: `R=wk/gp14/14_imx6ulz_4l/repro; place_simple.py $R/r1_fixed.kicad_pcb OUT.kicad_pcb --groups $R/r1_groups.json --intent $R/r1_intent.json --seed 2 --json OUT.json`, then `check_floorplan.py OUT.kicad_pcb --intent $R/r1_intent.json`. Expected: an uncapped price whenever a pin's rail has fewer caps than would make the limit trivially met (at least when it has one). Separately, this branch has no post-placement decap repair (`place_seed --repair-decaps` exists only on main), so the broken limits had to be fixed with hand `place_pose` moves.

### M04 -- VERDICT: NOT A BUG
- repro at 8328f157: the board 01 `--quick 2` route plus `quick_score` gives `blocking=0 vias=0 copper_mm=135.64`. The same flags without `--quick` plus `board_score` give `vias=2 copper_mm=146.29`. route.json `plane_fragility` is `{"source":"none","why":"--quick 2"}` against `{"source":"kicad_refill",...}`. So the numbers reproduce.
  - Board 04's recorded artifacts confirm quick→full via counts of s0 61→104, s2 59→92, s4 65→97, s6 60→91 and s10 55→106. But its full chain is three `route.py '*'` passes against one quick pass, so the two chains are not identical.
- cause: documented by design.
  - `py_router/plane_fragility.py:676-681` skips the field at level 2.
  - `py_router/route.py:5061-5069` lists the skips (`plane_finalize` at every quick level, so Phase-3 tap vias like board 02's are absent).
  - SKILL.md:323-326 says level 2 "skips ... plane finalize".
  - The quoted claim misreads `SKILL.md:328`: "about half the time of `--quick` alone, and it picks seeds as well" compares level 2 with level 1. It does not say level 2 predicts the full route's via count. The teammates on 04 and 13 also called it a property.
- branch head 86b54a1d: unchanged (same sentence in skill §3.7; plane_fragility unchanged). main 0523df20: plane_fragility / route.py quick exist there; the skill and judge do not (not on main).
- upstream: none needed. Teammates' searches cited #875 / #424 / #658 / #153; none applies.
- severity after verification: none. A LOW doc nicety at most: the skill could say that judge via counts run low against the full route (taps, fragility).

### M22 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - Board 10 `r3/s4_route/route.json` has `failed_single` 6, `open_single` 2, and a multipoint deficit of 807−790=17. `pad_pairs_open` includes `+3V3 95/98` and `GND 287/292` (`collision_refused`).
  - Pin `quick_score.py r3/s4_fast.kicad_pcb --route .../route.json` gives `blocking=25`, so the poured-net pads are counted.
  - Head's quick_score source, run against the pin tree (board_score.py is identical at pin and head), gives `blocking=16 (poured, not counted: 13 joins)`, with GND and +3V3 under `poured`.
  - Board 07 `r1/s8_route/route.json` gives multipoint 494/494, failed/open empty, quick_score 0, while `review_s8.log` lists "GND (poured): disconnected at C1, C11, …".
  - So the claim holds on 10 (inner-only pours) and not on 07: the route step's own tally treats poured nets differently by board. 07's GND zone includes outer layers (07 TOOL_GAPS #10), and 10's pours are In1/In2 only. The mechanism behind that difference was not established.
- cause: `py_tools/quick_score.py:36-50`: blocking is the route step's tally, including poured nets' multipoint deficit. `py_router/route.py:5061-5064`: `--quick` skips `plane_finalize`, which is the step that taps poured pads into the pour.
- branch head 86b54a1d: changed (fixed). 4e0deaee "Seed judge: grade the fast-routed board's connectivity, poured nets apart": quick_score now grades the board with `board_score.score_connectivity` over the nets without a zone and reports zone nets as `poured`. main 0523df20: not on main.
- upstream: new; no issue, already fixed on branch head by 4e0deaee. Searches: "quick_score poured", "quick 2 plane finalize", "poured net open quick", "seed judge poured".
- severity after verification: LOW at head (fixed); MEDIUM at the pin.

### M03 -- VERDICT: CONFIRMED
- repro at 8328f157: `wk/gp14/06_rp2350_fpga_eensy_prePlane/r1/judge.json` has `"judge": []` with all 12 seeds in `illegal`. The pin skill has:
  - `:293-294`: "never judge or keep that seed", and no alternative step.
  - `:310-315`, `:366-369`: the review loop starts from "the best fast route" and stops at `--rounds`, with no case for an empty judge.json or for judged seeds that all fail check_assembly or the floorplan gate.
  - `:350`: "a part moved by hand is moved back".
  - `:114`: a declared pose "needs no lock" (place_simple refusing it is H04).
  - `:420-421` and `:383`: a full-route failure classified as placement sends the agent back to "Change the inputs (§3.6), re-place", without saying whether that counts toward `--rounds`.
- cause: skill text, `.claude/skills/plan-pcb-placement/SKILL.md` (lines above). The tool causes behind the empty or unbuildable rounds are H04, H07 and M02.
- branch head 86b54a1d: changed. e1c7fdff "one pass of seeds, no review rounds" removed `--rounds` and the review loop, and a placement-classified failure is now itemised (§4), so the round-counting half is gone. The no-usable-seed half remains: §3.6:629-630 still says only "never judge or keep that seed". main 0523df20: not on main (the skill is not there).
- upstream: new. Searches: "all seeds illegal", "judge empty", "plan-pcb-placement rounds", "no legal seed", "plan-pcb-placement skill"; nothing relevant.
- severity after verification: LOW. It is skill text, and the board cost is counted in H04 / H07 / M02.
- issue draft:
  title: plan-pcb-placement: no step when place_simple names no judgeable seed (empty judge.json) or every judged seed is NOT BUILDABLE / fails the floorplan gate
  body: §3.6 (head §3.6-3.7) says never to judge or keep an illegal seed, then fast-routes the seeds judge.json names. When judge.json is `{"judge": []}` (gp14 board 06 round 1: all 12 seeds illegal, `wk/gp14/06_rp2350_fpga_eensy_prePlane/r1/judge.json`), the workflow has no next step. The same holds when every judged seed is legal but `check_assembly` NOT BUILDABLE (boards 04 and 07) or fails `check_floorplan --intent` (board 12). The skill also says a hand-moved part is moved back by the next placement, which rules out hand repair as the obvious fallback. Expected: an explicit branch for each case, for example: diagnose with `place_simple`'s `illegal` / `cost` line, change the named input (lock, keep-out, declared pose, limit weight), re-place; or hand-repair the judged seed and record it. Also state whether that counts as a new pass.

### M11 -- VERDICT: CONFIRMED
- repro at 8328f157: `git grep -l 'judge.json|quick_score|_fast.kicad_pcb'` over tracked .py / .md / .sh finds:
  - the skill, the docs, `place_simple.py` (writes judge.json), and `quick_score.py` (scores one board);
  - `kicad_routing_plugin/placement_run.py`, which only polls artifacts of a headless Claude run;
  - `tests/stress/placement_ab/route_placed.py`.
  - No CLI sequences a routing chain over judge.json's seeds. route_placed.py does replay a chain on a placed board with `--quick 2` plus quick_score, but only from a corpus manifest at `<corpus>/runs_set<SET>/<BOARD>/redo_commands.sh`. The skill does not name it.
  - Board 11's `helpers/judge_chain.sh` hand-codes a 6-step chain (pour, qfn_fanout, place_fanout_clearance, route_diff, route.py `--quick 2`, copy, quick_score), as the skill's §3.6 step 1 (`SKILL.md:316-331`) requires. I did not run the helper: it writes into the board's own r1/.
- cause: missing tool. SKILL.md §3.6 step 1 prescribes a per-seed chain that no repo tool runs.
- branch head 86b54a1d: unchanged (only templates.py and fit_template.py were added). main 0523df20: not on main. main has a different driver, `place_route_loop.py`, and no seed judge; route_placed.py is not on main.
- upstream: new. Searches: "judge runner", "judge chain seeds", "run chain over seeds", "fast route each seed", "route_placed".
- severity after verification: LOW (minutes per board, plus the risk of non-identical chains across seeds).
- issue draft:
  title: No tool runs the placement skill's judging chain over judge.json's seeds; each run hand-writes one
  body: plan-pcb-placement §3.6 step 1 has the agent run the board's routing chain (planes, fanout, decap clearance, route_diff, `route.py --quick 2 --json-out`) identically on every seed judge.json names, copy the result to `s<S>_fast.kicad_pcb`, and run quick_score. No CLI does this, so boards 08, 11 and 14 each wrote a shell helper (`wk/gp14/11_daplink/helpers/judge_chain.sh`, a 6-step chain; board 08 needed 9 commands per seed). `tests/stress/placement_ab/route_placed.py` already replays a recorded chain on a placed board at `--quick 2` and scores it, but it only reads a corpus manifest path (`runs_set<SET>/<BOARD>/redo_commands.sh`). Expected: a runner that takes a chain (a manifest or a command template with `{in}` / `{out}`) and judge.json, runs it identically per seed into `s<S>_route/`, copies the fast board out, and writes `s<S>_fast.score.json`. Generalising route_placed.py to accept a manifest path would cover it.

All outputs are in `wk/gp14/_verify/B02/`. That folder also holds a stray copy of `r1_fixed.kicad_pro`, an extra copy of my own. The krt-gp14 tree is still clean.

<!-- batch B03 -->
### H04 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - **08:** `place_simple.py 08…/repro/gap1_fixed.kicad_pcb _verify/B03/h04_08_s0.kicad_pcb --groups …gap1_groups.json --intent …gap1_intent.json --seed 0` exits 4.
    - It warns `H102..H105 … pad copper 2.177/2.185/2.155/2.164mm past the outline` and `Module301/302 … courtyard overlaps … 0.00x22.80mm (14.580mm2)`, and its `illegal` list includes all six declared refs.
    - Measured directly: the bbox overrun of H102..H105 is 2.15-2.19 mm, but `legality.pad_copper_gating_mm` (the exact outline) gives **0.000** for all four.
    - `check_assembly` says "on the outline by design, not gated: H102..H105". KiCad DRC (`kicad-cli`) has no edge-clearance error on any of them.
  - **06:** `place_simple.py 06…/repro/input.kicad_pcb … --intent …/intent.json --seed 0 --moves 3000` exits 4 with `U8's declared pose is not legal: 33 of 66 drill hole(s) past the outline`. All 33 are `castellated` pads. check_assembly says "on the outline by design, not gated: U8".
  - **10:** `gap1_fixed` + `gap1_intent_v1` seed 0 exits 4 with `FID1 … pad clearance to MK1 short by 0.250mm` and `MK1..MK4 … pad copper 0.950mm past the outline`.
    - Measured: the MK1 7.0 mm pad to FID1 true copper gap is **0.842 mm** (FID1 local clearance 0.375). The 0.125 mm gap behind the 0.25 shortfall is between the two bounding squares.
    - check_assembly on the output says `0 pad pair(s)`, MK1-4 "by design", `VERDICT: buildable`.
  - **Part (c), Module301/302, holds only in part.**
    - The 14.58 mm² is the two co-located NPTH pairs' far-face (F) drill boxes: 2 × 2.7×2.7. The B.CrtYd outlines do not overlap.
    - KiCad reports only `holes_co_located` (a warning) and no `courtyards_overlap`.
    - With `overlap_waivers` for the pair added (`_verify/B03/h04_08_intent_waived.json`) the parts are still refused: `drill Module301's hole is -2.850mm from Module302's hole`. No declaration can accept them.
    - check_assembly measures the same 14.58 mm² pair as COURTYARD-BLOCKING and does not gate it only because no member moved.
    - H102's other refusal (courtyard overlaps J1, 4.616 mm²) is real: KiCad flags `courtyards_overlap J1|H102`.
- cause: there are three causes.
  - **Overhang branch of `_fixed_pose_check`** (`py_placer/placement/seeder.py:564-592`):
    - It counts holes with `_holes_outside` (`seeder.py:290-311`), which uses every drilled pad's bounding square and has no castellated exemption.
    - It counts copper with `connector_geometry.pad_copper_outside` (`connector_geometry.py:393-418`), which uses each pad's bbox.
    - The contained branch (`seeder.py:598-601`) uses the exact, castellated-exempt `_pad_copper_off_board` → `legality.pad_copper_gating_mm` (`legality.py:5627`). That is the #1257 fix, which was applied to the contained branch only.
  - **Pad clearance:** `seeder.py:534` calls `ctx.pair_shortfall`, which judges rect gaps (`legality.py:5130`) as an absolute limit. `grade_pad_legality` (`legality.py:5944`) re-checks AABB hits on exact geometry.
  - **Every seed marked illegal:** a refused declared ref goes into each seed's `illegal` list (`place_simple.py:596`, `:647`), and the judge keeps only seeds with an empty list (`:360`).
- branch head 86b54a1d: unchanged. seeder.py only adds a graphic-copper test to the contained branch; the `refused` → `illegal` logic is at `place_simple.py:638/696`. main 0523df20: same `_fixed_pose_check` / `_holes_outside` / bbox overhang code (seeder.py:4911, :5063, :5230), used by place_seed's stage 0. place_simple is not on main.
- upstream: new. Related: #1257 (closed; its exact measure was not applied to the overhang branch), #1060 (closed). searches: "declared pose castellated", "fixed_poses illegal", "declared pose not legal", "castellated hole outline", "round pad bounding box outline", "place_simple illegal", "judge.json".
- severity after verification: HIGH
- issue draft:
  title: place_simple refuses declared poses on pad bounding boxes and castellated half-holes, so every seed is "illegal" and judge.json is empty
  body:
  - **What happens:** `seeder._fixed_pose_check` judges a declared pose whose courtyard leaves the outline by each pad's bounding box (`pad_copper_outside`) and by every drill hole's bounding square (`_holes_outside`, castellated pads included). It also judges pad-to-pad clearance on rect gaps, as an absolute limit. place_simple then lists the refused, unmovable refs as illegal in every seed, so judge.json names no seed.
  - **Measured at 8328f157:**
    - 08 CM5: H102..H105 refused at 2.15-2.19 mm "past the outline"; the exact gate (`pad_copper_gating_mm`) says 0.000.
    - 06 rp2350: U8 refused for "33 of 66 drill hole(s) past the outline"; all 33 are castellated.
    - 10 glasgow: FID1 refused "short by 0.250mm" to MK1; the true copper gap is 0.842 mm against 0.375 required.
    - check_assembly accepts all of these poses ("on the outline by design", 0 pad pairs).
    - Separately, two footprints sharing co-located NPTH holes (Module301/302) are refused even when named in `overlap_waivers`; KiCad reports this only as a `holes_co_located` warning.
  - **Repro:**
    `python3 -X utf8 py_placer/place_simple.py wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/input.kicad_pcb /tmp/x.kicad_pcb --groups wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/groups.json --intent wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/intent.json --seed 0 --moves 3000`
    and `… wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb … --groups …/gap1_groups.json --intent …/gap1_intent.json --seed 0`. Both exit 4.
  - **Expected:**
    - The overhang branch uses check_assembly's per-pad exact gate (castellated straddling pads exempt), as the contained branch does since #1257.
    - Holes are judged on their circles, and castellated half-holes are exempt.
    - Pad clearance for a declared pose is re-verified on exact geometry.
    - A declared pose the check refuses is reported once, not counted against every seed.

### H15 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - **Plain run:** `place_simple.py 06…/repro/fixed_u8lock.kicad_pcb _verify/B03/h15_plain_s0.kicad_pcb --groups …groups.json --intent …intent_frame.json --seed 0` exits 4 with `no legal pose found for: SW1`. Runs 1-3 left SW1; R2; C10, C11, C13, C22, J1, R7, R8.
  - **Teammate's one-line helper** (gives the container no face in the anneal's overlap term), same args: exits 0 on the first run (`annealed 30000 moves in 11.4 s`).
  - **Probe** (`_verify/B03/measure_overlap.py`: place_simple's own build, no anneal) on the finished plain seed:
    - U8 rect (138.575, 87.695, 158.425, 123.82) is larger than the board (139.61, 86.971, 157.39, 122.785), on faces B and F.
    - Anneal overlap term: 369.69 mm² in total, 15.95 mm² with U8 given no face. So 353.7 mm² (96%) is U8.
- cause: `Annealer.overlap` (`py_placer/placement/simple_anneal.py:286-327`, and the Rust `overlap_sum` path fed by `face_ids` at `:172-174` and `Model._CR`, `simple.py:1658/1763`) sums grown-rect overlaps over every pair that shares a face. It never skips `state.container_refs`.
  - The halo does skip containers (`simple.py:935-936`, "a container is a frame, not a body"), and so does the legality the run is judged by (`quench.py:1562`, `:2022`).
  - So `ov < CLEAN` (`simple_anneal.py:920/946`) can never hold while a pin frame exists, and no best state is recorded.
- branch head 86b54a1d: unchanged (simple_anneal.py changes only add template carry). main 0523df20: not on main.
- upstream: new. Related closed container issues: #1212, #1213, #1184. searches: "container overlap anneal", "pin frame anneal", "container frame overlap", "Teensy frame".
- severity after verification: HIGH
- issue draft:
  title: place_simple's anneal prices a pin-frame container's whole-board rect in its overlap term, so no state is ever overlap-free
  body:
  - **What happens:** a courtyard-less pin frame (06 rp2350's U8, a Teensy40 footprint, pin_frame container) has a pad-box rect that covers the whole board, on both faces. `simple_anneal.Annealer.overlap` does not skip `container_refs`, although the halo (`simple.halo_pair`) and the final legality (`QuenchState.candidate_valid`) both do.
  - **Measured at 8328f157 on a finished seed:** overlap term 369.7 mm², of which 353.7 mm² is U8 pairs. place_simple exits 4 (SW1 has no legal pose). The same seed with only U8's face bits zeroed exits 0 on its first run.
  - **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/fixed_u8lock.kicad_pcb /tmp/x.kicad_pcb --groups wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/groups.json --intent wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/intent_frame.json --seed 0` exits 4. Running `wk/gp14/06_rp2350_fpga_eensy_prePlane/helpers/place_simple_frame_fix.py` with the same args exits 0.
  - **Expected:** the anneal's overlap term skips containers as the halo and legality do, and the frame's pins are priced as pins (`_pin_hits_at`), not as a body.

### H16 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - **With the peg hole:** `withhole.kicad_pcb` + `intent_gap1.json`, `--seeds 7 --clustered-seeds 7` gives `cost 8300.9 … 146.1 s, no legal pose for CO2, I2C3, L3, PM2`, exit 4.
  - **Hole removed, same intent:** `nohole.kicad_pcb` + `intent_gap1.json` (I removed the teammate's confound; they used `intent_r1.json`, which adds a B keep-out) gives cost 3805.3 in 33.9 s, exit 0. With the teammate's `intent_r1` it is cost 3870.9, exit 0, matching their number.
  - **Probe:**
    - With the hole, BAT1 is sides [B, F] and supplies 88.1 of 101.3 mm² of the overlap term; 2 B-side parts are centred inside its rect.
    - Without the hole, BAT1 is sides [F], overlap is 0, and 143 B-side parts are centred inside its rect.
  - **check_assembly:** I put the hole back into the no-hole placement (`bat1_hole.py restore`, `_verify/B03/h16_restored_s7.kicad_pcb`). check_assembly reports 0 BAT1 pairs on side B and 0 hole conflicts. Its other BAT1 lines are F-side, from the strip workaround shrinking BAT1's pad box.
- cause:
  - `footprint_has_through_pads` (`legality.py:331-338`) makes any drilled part two-sided, through `sides_occupied` (`legality.py:590`, `quench.py:866`).
  - The anneal then gives the part a face bit for B (`simple_anneal.py:172`) and prices its full `rect()` (`_grown`, `:189`) on that face too (`:286-327`).
  - The legality, by contrast, presents only the drilled-pad box on the far face (`legality.rect_on`, `legality.py:800-807`).
- branch head 86b54a1d: unchanged. main 0523df20: not on main.
- upstream: new. Related closed per-face family: #848, #878. searches: "anneal far side", "locating peg", "through-hole far face courtyard", "one drilled pad both sides".
- severity after verification: HIGH
- issue draft:
  title: place_simple's anneal prices a drilled part's whole courtyard on the far face: one locating-peg hole blocks the B face under an SMD holder
  body:
  - **What happens:** `Annealer.overlap` gives every drilled part both face bits and prices its full rect on each. `legality.rect_on` gives the far face only the drilled-pad box. One-Air-Max's BAT1 (SMD 3x18650 holder, F.Cu, one unnetted 1.8 mm peg) therefore keeps every B part out of the ~4200 mm² under it.
  - **Measured at 8328f157, seed 7 clustered, same intent:**
    - With the hole: cost 8300.9, exit 4, CO2/I2C3/L3/PM2 have no legal pose, and 2 B parts are under BAT1.
    - Hole removed: cost 3805.3, exit 0, and 143 B parts are under BAT1.
    - check_assembly on that placement with the hole restored reports no BAT1 side-B pair.
  - **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gp14/07_One-Air-Max/repro/withhole.kicad_pcb '/tmp/w_s{seed}.kicad_pcb' --groups wk/gp14/07_One-Air-Max/repro/groups.json --intent wk/gp14/07_One-Air-Max/repro/intent_gap1.json --seeds 7 --clustered-seeds 7`. Repeat with `nohole.kicad_pcb`.
  - **Expected:** on the far face the anneal prices the part's drilled-pad box(es) (`rect_on` / `far_side_local`), as legality and check_assembly do.

### H07 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `place_simple.py 04…/repro/pile.kicad_pcb _verify/B03/h07_04_s3.kicad_pcb --groups … --intent … --seed 3` exits 0 with `illegal []`.
  - `check_assembly.py … --baseline …/pile.kicad_pcb --intent …/intent.json` exits 4 with `COURTYARD BLOCKING (6) … 6 of 6 GATE`: C13<->RV4 5.402 mm² (depth 1.08), C13<->C22 5.400, C14<->J7 6.995, C32<->J9 6.941, C5<->J1 1.886, C5<->J7 0.635. `VERDICT: NOT BUILDABLE`.
  - This is exactly the teammate's list. The 12 courtyard-less parts are warned by place_simple. check_assembly reads 114/114 fab bodies.
- cause: a movable part with no courtyard is seated on its pad bbox (`quench.py:879`). Only locked parts get the fab body (`locked_body_locals`, `quench.py:821-843`; the comment at `:833` says the body model for movable parts was A/B'd and rejected under #1182). check_assembly gates the drawn fab body.
  - #1182's actual remedies were `--body-model`, `--repair --baseline` charging courtyard pairs, and reseat on the grader's ruler (83a077fb, be155efe, both ancestors of the pin). All three lived in place_seed, which ecd673eb ("Retire the old placement flows") removed.
  - place_simple has no body model and no repair step. place_pose grades pad legality only (its `--help`), so no repo tool targets a courtyard-blocking pair.
- branch head 86b54a1d: unchanged. main 0523df20: not on main in this form; main still has place_seed with `--body-model` / `--repair --baseline`.
- upstream: regression of #1182 (closed) on the grouped-placement branch. Related: #1258, #896, #1106 (closed). searches: "place_simple pad box body", "courtyard-less fab body", "check_assembly body place_simple".
- severity after verification: HIGH
- issue draft:
  title: place_simple seats courtyard-less parts on pad boxes while check_assembly gates their fab bodies, and the branch has no mover for courtyard-blocking pairs (#1182 regression)
  body:
  - **What happens:** on the grouped-placement branch, place_simple's anneal and its final legality price a courtyard-less movable part by its pad bbox. check_assembly `--baseline` gates its drawn .Fab body. #1182's remedies (`--body-model`, `--repair --baseline`, grader-ruler reseat) went with place_seed in ecd673eb.
  - **Measured at 8328f157 (04 multichannel_mixer, seed 3):** place_simple exits 0 with `illegal []`. check_assembly reports 6 gating COURTYARD-BLOCKING pairs (e.g. C14<->J7 6.995 mm², C13<->RV4 5.402 mm², depth 1.08 mm) and NOT BUILDABLE.
  - **Repro:** `P=wk/gp14/04_multichannel_mixer/repro; python3 -X utf8 py_placer/place_simple.py $P/pile.kicad_pcb /tmp/s3.kicad_pcb --groups $P/groups.json --intent $P/intent.json --seed 3; python3 -X utf8 py_tools/check_assembly.py /tmp/s3.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json`
  - **Expected:** either place_simple's legality, or a repair step in its flow, charges check_assembly's gating courtyard pairs, so a seed it calls legal is not NOT BUILDABLE on body overlaps.

### M29 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `place_simple.py 14…/repro/r1_fixed.kicad_pcb _verify/B03/m29_s2.kicad_pcb --groups …r1_groups.json --intent …r1_intent.json --seed 2` exits 0 (legal).
  - U1 (F.Cu, 17×17 balls at 0.8 mm pitch) has **40** B-side parts centred in its ball field (0 in the input). 16 of them carry a BOOT_CFG net.
  - By ring from the outside: 7/7/6/5 in rings 0-3, so **25 of 40 sit in the outer 4 escape rows**. `placement-lessons.md:167-168` says to keep those rows clear.
  - The claim that these nets became the recurring open nets was not re-measured: I did no fanout or route. That is the unverified part.
- cause:
  - The halo returns 0 for parts on opposite faces (`simple.py:937-938`), and the anneal's overlap only pairs parts that share a face (`simple_anneal.py:172`, `:310`). So an SMD 0402 on B costs nothing under an SMD BGA on F.
  - No term reserves the BGA's escape or via field on the far face. This is a missing objective term, not a legality bug: the poses are legal.
- branch head 86b54a1d: unchanged. main 0523df20: not on main.
- upstream: new. #456 (closed) is different. searches: "back face BGA", "under BGA placement", "halo opposite face", "escape rows back", "ball field parts", "BGA escape far side".
- severity after verification: MEDIUM
- issue draft:
  title: place_simple prices no far-face escape field under a BGA: back-face parts fill the ball field's outer escape rows
  body:
  - **What happens:** the halo and the overlap term only price parts that share a face. A front-face BGA's ball field, where its escape vias go, is therefore free real estate for back-face SMD parts.
  - **Measured at 8328f157 (14 imx6ulz_4l, seed 2, exit 0):** 40 B-side parts are centred inside U1's 17×17, 0.8 mm-pitch field (0 in the input), and 25 of them are in the outer 4 rows. placement-lessons.md says "Under a BGA … Keep the outer escape rows clear."
  - **Repro:** `R=wk/gp14/14_imx6ulz_4l/repro; python3 -X utf8 py_placer/place_simple.py $R/r1_fixed.kicad_pcb /tmp/s2.kicad_pcb --groups $R/r1_groups.json --intent $R/r1_intent.json --seed 2`, then count B.Cu footprints with 79.8<=x<=93.8 and 103.2<=y<=117.2.
  - **Expected:** a far-face cost (or keep-out) over a BGA's outer escape rows, so back-face parts go to the inner power region or outside the field, as the placement lessons describe.

All my outputs are in `wk/gp14/_verify/B03/`. That folder holds the logs, the placed boards and the KiCad DRC json (`h04_08_kicad_drc.json`). It also holds the two files I wrote there: the probe script `measure_overlap.py` and the waiver test intent `h04_08_intent_waived.json`.

<!-- batch B04 -->
### H05 -- VERDICT: CONFIRMED-PARTIAL
- **Repro at 8328f157** (outputs are `wk/gp14/_verify/B04/h05_*`):
  - **Glasgow, pile baseline.** `check_assembly.py 10_glasgow_revC/final.kicad_pcb --intent .../intent.json --baseline .../glasgow_revC.kicad_pcb` exits 4 with `J5 <-> MK2 4.0669mm2 depth 0.9998mm GATES (moved: J5 MK2)` and NOT BUILDABLE. The human board `_truth/glasgow_revC/human_stripped.kicad_pcb` without a baseline reports the same pair as REPORT-ONLY and reads buildable.
  - **CM5, pile baseline.** `final.kicad_pcb` against the pile: Module301<->Module302 (14.58 mm²) and H102<->J1 (4.6161 mm²) GATE, NOT BUILDABLE. The human board graded against the same pile is also NOT BUILDABLE, with 4 gating pairs (adds J1<->J601 and D702<->J1).
  - **Lock channel.** `repro/gap4_kept_locked`: 6 of 6 pairs GATE (FID1<->MK1 2.0554 mm²), NOT BUILDABLE. `gap4_kept_unlocked`: the same pair reads `waived:marker_class`, buildable.
  - **07 waiver channel.** `intent_gp.json` with `overlap_waivers` removed: BAT1<->DC1 (38.7125 mm²) and BAT1<->PWR_SW1 (16.5825 mm²) GATE, exit 4. With the waivers: buildable.
  - **New measurement.** `check_floorplan.py 10/final.kicad_pcb --intent 10/intent.json --plan-only` reports 12 `plan_fixed_pose_conflict` ERRORs on the given intent (J5/MK2 4.067, FID1/MK1 2.055, J2/J5 0.258 ...). CM5 reports 1 (Module301/302 14.58). Re-emitting the glasgow intent (`--emit-intent --allow-unplaced`) exits 0, prints "21 of them compiled into fixed_poses[]", says nothing about the conflicts and emits no waiver.
  - **Two corrections to the cluster.**
    - CM5 H102<->J1 is not a declared pair. J1 is in neither mechanical.json nor `fixed_poses`, so that gate is the run's own pose choice.
    - Glasgow's project sets `courtyards_overlap` to `warning`. Grading that as error is deliberate: #1095's fix, commit 4e81c161, says "'warning' is graded as error".
- **Cause:** every channel behaves as designed.
  - The courtyard gate is moved-vs-baseline (check_assembly.py:611-627, 644-647), so a pile baseline charges every declared pair.
  - A KiCad lock voids class waivers (legality.py:2422-2433).
  - `accept_courtyard_overlap` is documented as read by the plan check only (docs/floorplan-intent.md:417-422; floorplan.py:583-596).
  - The plan check refuses the same pairs, so the graders agree with each other. The gap is between declaring and grading:
    - `--emit-intent` compiles declared poses that overlap each other (taken from the human board) without a warning or a waiver.
    - The #1060 waiver does not reach check_assembly's courtyard channel. Its documented reason is about the drawn-body containment gate, not courtyards.
    - The skill never mentions `overlap_waivers`.
    - part-roles.md:124-125 says "place and lock" holes and fiducials, while SKILL.md:112-114 says a `fixed_poses` part needs no lock.
- **Branch head 86b54a1d:** unchanged. check_assembly.py and legality.py are untouched. SKILL.md was rewritten, but the §3.1 lock text and part-roles.md:125 are unchanged.
- **Main 0523df20:** same mechanism (lock clause at legality.py:2378, `courtyard_gating` at check_assembly.py:629-631, `accept_courtyard_overlap` documented as plan-only).
- **Upstream:** new as a whole. Related, all closed: #1060 (created the waiver, plan-check-only by design), #897, #1250. Searches: "check_assembly baseline pile moved fixed_poses", "accept_courtyard_overlap check_assembly", "marker_class locked waiver", "declared poses courtyard overlap gating", "emit-intent fixed_poses conflict plan_fixed_pose_conflict", "overlap_waivers mechanical", "fixed_poses waiver", "courtyard baseline moved", "lock fiducial courtyard".
- **Severity after verification:** MEDIUM. The tool prints the remedy (`overlap_waivers`), but on the emitted intent no placement that honours every declaration grades buildable.
- **Issue draft:**
  title: Declared fixed poses that overlap each other grade NOT BUILDABLE, and neither --emit-intent nor fixed_poses[].accept_courtyard_overlap says so
  body:
  **What happens.** `check_floorplan --emit-intent` compiles mechanical.json poses into `fixed_poses[]` and exits 0. On glasgow_revC the same intent's `--plan-only` then reports 12 `plan_fixed_pose_conflict` errors, for example J5/MK2 with 4.067 mm² of courtyard overlap. On CM5_MINIMA_3 it reports 1 (Module301/Module302, 14.58 mm²). Both overlaps are on the human boards. A placement seated exactly at those poses grades NOT BUILDABLE under `check_assembly --intent <emitted> --baseline <pile>`: glasgow J5<->MK2 4.0669 mm² GATES, CM5 Module301<->Module302 14.58 mm² GATES. The CM5 human board graded against the pile is also NOT BUILDABLE (4 gating pairs).
  **The waiver channels.** The waiver #1060 added for this case, `fixed_poses[].accept_courtyard_overlap`, is read by the plan check only. On One-Air-Max, BAT1<->DC1 (38.71 mm²) and BAT1<->PWR_SW1 (16.58 mm²) gate until the same pairs are copied into `overlap_waivers[]`. Locking FIDs and MKs, as part-roles.md prescribes, removes the marker_class waiver (glasgow: 6 FID/MK pairs gate when locked, buildable when unlocked). SKILL.md §3.1 says a `fixed_poses` part needs no lock.
  **Repro:**
  - `py_tools/check_floorplan.py wk/gp14/10_glasgow_revC/final.kicad_pcb --intent wk/gp14/10_glasgow_revC/intent.json --plan-only`
  - `py_tools/check_assembly.py wk/gp14/10_glasgow_revC/final.kicad_pcb --intent wk/gp14/10_glasgow_revC/intent.json --baseline wk/gp14/10_glasgow_revC/glasgow_revC.kicad_pcb`
  - `py_tools/check_assembly.py wk/gp14/10_glasgow_revC/repro/gap4_kept_{locked,unlocked}.kicad_pcb --intent wk/gp14/10_glasgow_revC/repro/gap4_intent_v3.json --baseline wk/gp14/10_glasgow_revC/repro/input_pile.kicad_pcb`
  **Expected.**
  - `--emit-intent` reports the declared pairs its own plan check refuses, or emits a named waiver for them.
  - check_assembly's courtyard channel (not the body channel) honours `accept_courtyard_overlap`.
  - The skill and part-roles agree on whether declared markers are locked.

### H11 -- VERDICT: NOT A BUG
- **Repro at 8328f157:**
  - **04.** `check_assembly.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json` gives `R39 <-> R42 courtyard 0.0823mm2 side B advisory <-- NEW vs baseline` and `VERDICT: buildable`. Its JSON has `courtyard_severity "error"`, basis `project`. `kicad_drc_compare.py` reports `COURTYARD kicad=1 krt_blocking=0 advisory=2 waived=5` and `R39<->R42 krt=advisory sev=error`.
  - **14.** `check_assembly.py repro/courtyard_c20_fb2.kicad_pcb` gives `C20 <-> FB2 courtyard 0.2234mm2 advisory`, buildable. `kicad-cli pcb drc` reports a `courtyards_overlap` **error** for FB2/C20.
- **Cause:** documented policy. legality.py:224-241 sets the run-23 blocking floors: area ≥ 0.5 mm² or ≥ 25 % of the smaller courtyard, AND depth ≥ 0.3 mm. The comment explains them ("tell a by-design kiss from an interpenetration"). #1095's fix (4e81c161) only added the `ignore` waiver; `error` keeps the floors. The cluster itself says it is documented. The consequence is real: an overlap the run created, which the project grades as error, passes check_assembly, board_score and check_complete, and only kicad-cli sees it. That is worth raising as a policy question, not a code defect.
- **Branch head 86b54a1d:** unchanged. **Main 0523df20:** same constants (legality.py:240-248).
- **Upstream:** no issue on the floors. #1095 (closed) covered severity only. Searches: "courtyard floors KiCad courtyards_overlap", "courtyard sliver advisory", "check_assembly buildable KiCad DRC courtyard", "courtyard advisory depth floor", "COURTYARD_BLOCKING_MIN".
- **Severity after verification:** none as a defect. As a policy question, LOW.

### M24 -- VERDICT: CONFIRMED-PARTIAL
- **Repro at 8328f157** (`P=wk/gp14/04_multichannel_mixer/repro`; Default class 0.2, `rules.min_clearance` 0.3):
  - **check_assembly.** `check_assembly.py $P/s3_fix_at02.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json` prints "grading at clearance 0.2mm [board netclass]", 0 pad pairs, buildable.
  - **check_drc.** Prints "Grading at clearance 0.3 mm (from ... board minimum clearance)" and finds 2 PAD-PAD violations: C39.2<->C32.1 and C5.2<->C6.1.
  - **KiCad.** `kicad-cli pcb drc`: 2 clearance errors, "board minimum clearance 0.3000 mm; actual 0.2377 / 0.2519 mm".
  - **place_pose.** `place_pose --dry-run set C39 <its pose>` prints "legality at clearance 0.2 (board netclass)", `legal true`, `pad_conflicts 0`.
  - **The false note.** With `--clearance 0.3`, check_assembly finds 2 pad pairs but prints "...this grade is STRICTER than the board asks for", which is false.
  - **Part #7 (the ceiling chain spelling)** reproduces exactly: `route.py ... --clearance-ceiling 0.3` gives `min_clearance_used 0.2` and `rules.min_clearance: 0.3 -> 0.2`. However, the run discloses it three times: "Clearance 0.2mm is below the board's minimum clearance 0.3mm (Board Setup)...", a `design_rules.narrowed` row (requested 0.3, delivered 0.2), and the "Design rules [...]" line.
- **Cause:**
  - `list_nets.board_floor` takes clearance from the Default netclass only (`_FLOOR_SOURCES['clearance'] = ('clearance', None)`, list_nets.py:428-429). `board_floor_knobs` does the same (list_nets.py:399-402).
  - check_assembly.py:135 uses `board_floor`. Its note at :155-163 compares against the class value.
  - place_pose goes through `pose_ops.resolve_knobs` (pose_ops.py:180) to `board_floor_knobs`.
  - None of them calls `fix_kicad_drc_settings.project_grading_clearance` (:351), which is #1210's max(class, `min_clearance`).
  - The #1210 closing comment says: "The placement tools' class-only clearances are not changed here."
  - Part #7 is documented: the ceiling semantics are min(class, X) in CLAUDE.md, and #1210 deliberately kept the routing base at the class value. At most it is a skill/CLAUDE.md wording gap (LOW).
- **Branch head 86b54a1d:** unchanged. **Main 0523df20:** same code (list_nets.py:429; the check_assembly note at :159).
- **Upstream:** follow-up to closed #1210. Its body named check_assembly as affected; its fix explicitly left the placement tools out. Not a regression. Searches: "min_clearance placement check_assembly", "min_clearance place_pose", "Board Setup min_clearance", "clearance-ceiling min_clearance", "min_clearance ceiling chain".
- **Severity after verification:** MEDIUM. It cost a full route; board_score's drc=2 caught it after #1210.
- **Issue draft:**
  title: check_assembly and place_pose grade pad clearance at the Default net class below Board Setup min_clearance (the #1210 fix did not reach placement)
  body:
  **What happens.** multichannel_mixer has Default class 0.2 and `rules.min_clearance` 0.3. On `wk/gp14/04_multichannel_mixer/repro/s3_fix_at02.kicad_pcb`:
  - kicad-cli DRC: 2 clearance errors ("board minimum clearance 0.3000 mm; actual 0.2377 / 0.2519 mm", C32.1-C39.2 and C5.2-C6.1).
  - check_drc: grades at 0.3 and finds the same 2.
  - check_assembly: "grading at clearance 0.2mm [board netclass]", 0 pad pairs, buildable.
  - place_pose: "legality at clearance 0.2", `legal true`.
  - check_assembly `--clearance 0.3`: finds the 2 pairs but says the grade is "STRICTER than the board asks for".
  **Cause.** `list_nets.board_floor` / `board_floor_knobs` resolve clearance from the class only (list_nets.py:428-429, 399-402). check_assembly.py:135, :155-163 and `pose_ops.resolve_knobs` (:180) consume them. `project_grading_clearance` is used by check_drc and check_join, not by placement.
  **Repro.** The three commands above, plus `kicad-cli pcb drc --severity-all` on the same file.
  **Expected.** The placement graders grade at max(Default class, `min_clearance`), as check_drc does since #1210, and the note compares against that value.

### M09 -- VERDICT: CONFIRMED-PARTIAL
- **Repro at 8328f157:**
  - **06.** `place_pose repro/placed.kicad_pcb ... --dry-run rotate C2 0` gives `legal false` and `pad_edge_conflicts_after 33` ("U8.1: edge shortfall 1 mm (required 0.2 mm)"). All 33 findings are U8 pads with `pad.castellated == True`. check_assembly on the same board lists U8 "on the outline by design, not gated", buildable. Separately, 8 custom pads (U4, U5) are unmeasured ("parsed polygons"), so `legal` stays false here even without the castellated pads.
  - **03.** `place_pose gap2_s6 ... --dry-run set R207 152.2729 107.6242 --rot 270` gives `legal false`, `pad_edge_unmeasured_after 165` (every pad, "outline uses sampled perimeter check"), and 0 findings. The outline's top edge runs from (87.9, 51.8) to (188.595, 51.816).
  - **05.** `place_pose r3_s0 ... set C1 131.4 60.9 --rot 180` gives `legal false`, 62 BUS1 findings ("edge 0.55 (fixed default)", shortfall 0.296), and all 379 pads unmeasured (non-rectangular outline). It wrote the board with exit 0. check_assembly against `fixed.kicad_pcb`: C1<->R2 0.5056 mm² GATES, NOT BUILDABLE. kicad-cli DRC on r3_s0 reports no edge-clearance violation (the project declares `min_copper_edge_clearance` 0.0).
- **Cause:**
  - **Defect: castellated pads.** The pad-edge channel (`EdgeCopperContext._readings` / `grade`, legality.py:5751-5855) has no castellated test. The OOB channel exempts exactly these pads (legality.py:5620-5622, 6194-6197, whose comment names "rp2350's Teensy U8: 33 half-holes"). The same pads are by design in one channel and a violation in the other.
  - **By design: non-rectangular outlines.** `complete` requires `self.rectangular` (legality.py:5853). `_segments_cover_rectangle` (5358-5379) uses EPS 1e-6, so any non-rectangular outline, including a 16 µm drawing skew, makes `legal` permanently false. This is #967's chosen rule (do not claim legality on an unexecuted exact check). It is a usability gap, not a bug.
  - **Documented: declared 0 edge clearance.** A declared 0 is read as unset and falls back to 0.55 (list_nets.py:393-398, 415-425). KiCad grades a real 0.
  - **Documented: courtyards.** place_pose's `legal_unmeasured` lists "component bodies / courtyards", and by default place_pose refuses only when a pose is worse, so writing that pose with exit 0 is documented.
- **Branch head 86b54a1d:** unchanged. **Main 0523df20:** same code (sampled reason at legality.py:5934; castellated exemption only in the OOB channel, 5782/6407).
- **Upstream:** new. #967 (closed) is the design origin of the completeness rule. Searches: "place_pose legal castellated", "pad edge clearance castellated", "sampled perimeter legal", "place_pose legal false non-rectangular outline", "edge fingers edge clearance place_pose", "pad_edge complete rectangular".
- **Severity after verification:** LOW. `no_worse` stays usable; the castellated findings mislead.
- **Issue draft:**
  title: place_pose grades a castellated module's half-holes against the edge-clearance floor (the #1096 exemption stops at the OOB channel); `legal` is unreachable on any non-rectangular outline
  body:
  **Castellated pads.** On `wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/placed.kicad_pcb`, `place_pose ... --dry-run rotate C2 0` reports `pad_edge_conflicts_after 33`. All 33 are U8 pads with `castellated` set ("edge shortfall 1 mm, required 0.2"). `grade_pad_legality`'s OOB channel exempts the same pads (legality.py:5620, 6194), and check_assembly calls the board buildable. `EdgeCopperContext._readings` (legality.py:5751+) has no castellated test.
  **Non-rectangular outlines.** `complete` requires an exactly rectangular outline (legality.py:5853, EPS 1e-6 in `_segments_cover_rectangle`). On `wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb`, one corner at y=51.816 against 51.8 makes all 165 pads "sampled" and `legal` false on every pose.
  **Expected.**
  - The edge-clearance channel exempts an edge-straddling castellated pad, as the OOB channel does.
  - An outline within a small drawing tolerance of a rectangle is treated as one, or the sampled check can certify a pad well clear of the edge.

### H14 -- VERDICT: CONFIRMED
- **Repro at 8328f157** (`R=wk/gp14/12_steppenprobe/repro`):
  - `check_assembly.py $R/r1_s9.kicad_pcb`: "0 pad pair(s)", `VERDICT: buildable (blocking 0)`.
  - `check_pads.py $R/r1_s9.kicad_pcb`: exit 164, "FAILED: 164 overlapping different-net pad pair(s)" (U1.1 GND <-> U1.2 /OSCI, overlap 0.300 mm, ...).
  - `kicad-cli pcb drc`: 176 `shorting_items` errors, 164 of them between two pads of U1.
  - `check_drc.py`: "NO DRC VIOLATIONS FOUND!", so board_score's drc reads 0 too.
  - `place_pose --dry-run lock U1`: `pad_conflicts_after 0`, `pad_stack_count_after 0`.
  - place_simple was not re-run; it uses the same inter-part pad channels.
- **Cause:**
  - check_assembly's pad channel is between two parts by definition (`pad_intersection_pairs`, legality.py:3333-3345).
  - check_drc deliberately skips pads of the same footprint (check_drc.py:4301-4309). The stated premise is that a footprint's own pads are fixed library geometry no placement step changes.
  - The placement writer breaks that premise: it does not rotate pads carrying KiCad 6's `locked` token (cluster H13). The premise also does not justify skipping a different-net INTERSECTION, which no library footprint carries outside a declared net tie.
  - Only check_pads catches it. check_complete runs check_pads (check_complete.py:457), and qfn_fanout warns. The placement skill runs neither.
- **Branch head 86b54a1d:** unchanged. **Main 0523df20:** same (the check_drc skip is at :4374).
- **Upstream:** new. Nearest: #858 (closed, pad-on-pad shorts between parts), #1204, #1111. Searches: "same footprint pads overlap", "check_pads overlapping pads check_assembly", "own pads overlap", "pad locked token rotate", "check_drc same footprint pad skip", "shorting_items same footprint".
- **Severity after verification:** MEDIUM. check_complete's check_pads would refuse DONE at the end, but placement rounds and the judge run on corrupted geometry first.
- **Issue draft:**
  title: check_assembly, place_pose and check_drc skip pad overlaps inside one footprint, so a board KiCad grades with 164 shorting_items reads buildable / clean
  body:
  **What happens.** On `wk/gp14/12_steppenprobe/repro/r1_s9.kicad_pcb`, U1's pads were left at their pre-rotation angle by the placement writer (pads carrying KiCad 6's `locked` token are not rotated).
  - check_pads: 164 overlapping different-net pad pairs on U1 (overlap 0.300 mm).
  - kicad-cli DRC: 176 `shorting_items` errors, 164 of them U1-internal.
  - check_assembly: 0 pad pairs, buildable.
  - place_pose: `pad_conflicts 0`, `pad_stack_count 0`.
  - check_drc: NO DRC VIOLATIONS (so board_score drc 0).
  **Cause.** `pad_intersection_pairs` (legality.py:3333) covers two parts only. check_drc skips same-footprint pads (check_drc.py:4301-4309) on the premise that no placement step changes a footprint's own pad geometry, which the writer bug above breaks.
  **Repro:** `py_tools/check_assembly.py <board>`, `py_router/check_drc.py <board>` and `py_router/check_pads.py <board>` on that file.
  **Expected.** A different-net pad intersection within one footprint, outside a declared net tie, is reported by check_assembly (blocking) and by check_drc, so a placement grade cannot call such a board buildable.

Housekeeping: `kicad-cli pcb drc` wrote four `.kicad_prl` files next to the input boards, outside my output folder: `wk/gp14/05_interf_u/repro/r3_s0.kicad_prl`, `wk/gp14/04_multichannel_mixer/repro/s3_fix_at02.kicad_prl`, `wk/gp14/14_imx6ulz_4l/repro/courtyard_c20_fb2.kicad_prl` and `wk/gp14/12_steppenprobe/repro/r1_s9.kicad_prl`. They are untracked local-settings files. The boards and `.kicad_pro` files are unmodified (mtimes checked). `s2r_v125_step4.kicad_prl` in the 04 repro folder predates my runs and is not mine. Every other output is under `wk/gp14/_verify/B04/`.

<!-- batch B05 -->
### H06 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - Ran `route_planes.py wk/gp14/08_CM5_MINIMA_3/repro/gap_pour_in.kicad_pcb wk/gp14/_verify/B05/h06/pour.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu`. It prints 5x `WARNING: net 'GND' ... ONE multi-layer zone ... cannot be replaced for F.Cu alone ... To replace it outright, run those layers together`, although all five layers were in that call. It exits 0 with `status ok`.
  - The output has 11 zones: the original 5-layer GND zone at priority 0, plus 5 new GND zones at priority 1. +5V on In3 was replaced in place.
  - Board 04 (`pile.kicad_pcb`, `--nets GND GND --plane-layers F.Cu B.Cu`): 1 zone in, 3 zones out, same warnings.
  - check_impedance half, isolated on the same copper. I took `final_route_old1/f6_route.kicad_pcb` and removed only the stale multi-layer GND zone (`_verify/B05/scripts/drop_multilayer_zone.py`). Then I ran `check_impedance --nets <the 9 globs from helpers/exp_chain.sh>`:
    - stacked: **28 nets, 114 crossings (64 split + 50 void)**. This matches the teammate's numbers exactly.
    - stale zone removed: **16 nets, 53 crossings, 0 split**.
    - At all 64 split points the copper on both sides is GND (`scripts/h06_split_probe.py`). At 33 of them both GND zones have fill at the reported point.
- cause:
  - `py_router/plane_io.py:141-148`: `check_existing_zones` decides one layer at a time. Any same-net zone whose span reaches beyond `target_layer` goes to `keep_span`. It is never given the set of layers this call pours for the net.
  - `route_planes.py:3402-3410` only adds to `zones_to_replace` from `zone_to_replace`. So the writer's "remove only when every layer it pours is in the remove set" path (`plane_io.py:369-375`) can never fire for a multi-layer zone. This contradicts `docs/route-plane.md:287-293` ("replace it outright by running those layers together").
  - Grader side: `py_tools/check_impedance.py:253-262` keys copper by (zone index, fill component), first zone in file order wins. `:624-637` then counts any key change between adjacent covered samples as a `split`, even when both zones are the same net.
  - The 07 bullet (finalize taps on In1.Cu) was not re-run.
- branch head 86b54a1d: unchanged (plane_io.py, route_planes.py and check_impedance.py are not touched); main 0523df20: same code (`plane_io.py` and `check_impedance.py` are identical).
- upstream: new; searches: "multi-layer zone route_planes", "route_planes replace zone layers together", "check_impedance split same-net zone", "overlapping zones impedance split", "stacked zone same net", "multi-layer pour replace", "ONE multi-layer zone", "impedance split fill component", "zone index fill component". The hits (#1131, #662, #598, #657, #488, #487, #1056) are other defects.
- severity after verification: HIGH. It blocked DONE on board 08 through a phantom grade; the copper itself is not damaged (same-net overlap, no short).
- issue draft:
  title: route_planes keeps a multi-layer same-net zone even when every layer it covers is poured in the same call; check_impedance then counts the overlap as reference-plane splits
  body:
  - What happens: `route_planes.py wk/gp14/08_CM5_MINIMA_3/repro/gap_pour_in.kicad_pcb out.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu`. The input has one GND zone on F/In1/In2/In4/B. For each layer the run warns "cannot be replaced for X alone ... run those layers together", although it did. It writes 11 zones: the original (priority 0) plus 5 new GND zones (priority 1). On `wk/gp14/04_multichannel_mixer/repro/pile.kicad_pcb` with `--nets GND GND --plane-layers F.Cu B.Cu`, 1 zone becomes 3.
  - Cause: `check_existing_zones` (plane_io.py:141-148) decides per layer and never sees the call's layer set. The removal path in `filter_zones_from_content` is therefore unreachable for multi-layer pours. `docs/route-plane.md` says a pour is replaced "by running those layers together".
  - Downstream: on `wk/gp14/08_CM5_MINIMA_3/final_route_old1/f6_route.kicad_pcb`, check_impedance over the 36 declared nets reports 28 nets / 114 crossings, 64 of them `split`. Deleting only the stale zone gives 16 / 53 / 0 split, on the same copper. `LayerCopper.key_at` keys by (zone index, fill component), so a trace passing from one same-net zone's fill to the other's counts as a split.
  - Expected: when every layer of a same-net zone is in the call, replace that zone. check_impedance should treat overlapping same-net fills on a layer as one reference.

### M14 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - Ran `route_planes.py wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb wk/gp14/_verify/B05/m14/g6_planes.kicad_pcb --nets GND --plane-layers B.Cu`. It prints `Note: Replacing existing zone on B.Cu for net 'GND' with new parameters`.
  - Input zone → output zone:
    - clearance 0.508 → 0.254
    - default (thermal) connection → `connect_pads yes` (solid)
    - thermal_gap/bridge 0.508/0.508 → 0.2/0.2
    - min_thickness 0.254 → 0.1
    - hatch 0.508 → 0.5
    - polygon 105.41..182.88 → 103.5..183.5
- cause:
  - Replacement is the documented intent: commit 05e275e4 "replace clearance and minimum width parameters of the existing planes", and `docs/route-plane.md:28,280` ("Replaces an existing zone ... with new parameters"). `--skip-existing-zones` keeps the zone.
  - The new values are route_planes' own defaults: `--min-thickness` 0.1, solid unless `--thermal-relief`, and zone clearance = run clearance (plane_io.py:150 message, kicad_writer.py:817-818 defaults).
  - What holds, and is a disclosure/skill gap rather than an engine bug:
    1. The note does not say which designer settings were dropped. Thermal → solid matters on a hand-soldered through-hole (THT) board.
    2. The routing skill's Step 1 (SKILL.md:1351, 1383) sends a board that already carries a designer pour into this replacement and never mentions `--skip-existing-zones`.
  - The "0.1 min_thickness necks" point is not a rule violation on this board: its project declares `min_connection 0.0`. The 0.2032 figure came from kicad_drc_compare's staged spec.
- branch head 86b54a1d: unchanged; main 0523df20: same code (same message and defaults).
- upstream: new; searches: "Replacing existing zone new parameters", "route_planes thermal relief existing zone", "replace zone settings min_thickness", "designer zone settings replaced", "preserve zone settings", "skip-existing-zones default". Only general hits (#487, #488, #531); #1056 is unrelated (GUI layer rename).
- severity after verification: LOW
- issue draft:
  title: route_planes replaces a designer's same-net zone (thermal → solid, clearance, min_thickness, outline) and reports only "with new parameters"
  body: `route_planes.py wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb out.kicad_pcb --nets GND --plane-layers B.Cu` turns the input B.Cu GND zone (clearance 0.508, thermal 0.508/0.508, min_thickness 0.254, polygon 105.41..182.88) into clearance 0.254, `connect_pads yes`, thermal 0.2/0.2, min_thickness 0.1, polygon 103.5..183.5. The console says only "Replacing existing zone ... with new parameters". Replacing is documented. Expected: list each changed setting (especially pad connection style), and the routing skill's bare-pour step should say to use `--skip-existing-zones` when the board already has a designer pour it wants kept.

### M01 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157 (all bare pours: 0 vias, 0 traces placed):
  - 05: `route_planes.py wk/gp14/05_interf_u/repro/placed.kicad_pcb _verify/B05/m01/pour.kicad_pcb --nets GND --plane-layers B.Cu` writes `rules.min_via_drill: None -> 0.6`.
    - Then `route.py` (the cluster's command, into `_verify/B05/m01/route.kicad_pcb`) prints `via drill: 0.6 -> 0.2 mm; 122 of 122 object(s) ... below the ORIGINAL 0.6mm`.
    - The same route.py run on `placed.kicad_pcb` directly (no pour step) prints no via-drill line at all.
  - 11: `--board-edge-clearance 0.55` pour writes `min_hole_clearance 0.25 -> 0.2`, `min_via_drill None -> 0.4` and `min_copper_edge_clearance 0.0 -> 0.2 (fab-edge pin)`.
  - 04: with sizes omitted, the pour writes `min_track_width 0.3 -> 0.2`, `min_connection 0.3 -> 0.2`, `min_via_diameter 1.5 -> 0.6`, `min_via_drill None -> 0.3`.
  - 02: `min_via_drill None -> 0.635`.
- cause:
  - `route_planes.py:4777-4782` always passes `track_width`, `via_size`, `via_drill` and `clearance` to `fix_project_for_output`, whether or not the step drew a track or via.
  - `fix_kicad_drc_settings.py:1346-1348`: `min_hole_clearance` is set to the copper clearance when no hole clearance is given.
  - `fix_kicad_drc_settings.py:1371-1409`: the size floors are `min(param, scanned)`.
  - `fix_kicad_drc_settings.py:1182` (`base = origin.get(key, was)`): a key absent from `fab_floor_origin` (the board declared none) falls back to the immediate input's value. That is how the pour's invented 0.6 becomes "ORIGINAL".
  - #1195's fix (384d1511: "via floors reach the writeback only when the run emitted a via"; no-copper runs write no floors) is on the pin but only in qfn_fanout.
  - Not a bug: the edge half (`0.0 -> 0.2 (fab-edge pin)` despite `--board-edge-clearance 0.55`) is deliberate. route_planes records the project's edge rule, not its zone inset (#338, route_planes.py:4772-4776), and pins it to the fab floor (#441, fix_kicad_drc_settings.py:1351-1363).
  - The later hole-clearance drops on 06/13 come from routing steps that did lay copper (the documented, disclosed writeback).
- branch head 86b54a1d: unchanged; main 0523df20: same code (route_planes passes the same kwargs at 4799-4805; same `compute_targets` / `base = origin.get(key, was)`).
- upstream: new for route_planes. It is the same class as #1195 (CLOSED), whose fix was scoped to qfn_fanout; related #1285 (CLOSED). searches: "route_planes min_via_drill", "pour lowers floor", "route_planes writes floors no copper", "min_hole_clearance route_planes", "FAB FLOOR RELAXED original", "floors written for vias that do not exist", "bare pour project floors".
- severity after verification: MEDIUM
- issue draft:
  title: route_planes (bare pour, 0 vias/0 tracks) writes via/track floors and lowers min_hole_clearance; route.py then calls the invented value "ORIGINAL" (#1195 for route_planes)
  body:
  - `route_planes.py wk/gp14/05_interf_u/repro/placed.kicad_pcb out/pour.kicad_pcb --nets GND --plane-layers B.Cu` places 0 vias and 0 traces, yet writes `rules.min_via_drill: None -> 0.6`.
  - On `wk/gp14/11_daplink/repro/placed_s3.kicad_pcb` the same kind of run writes `min_hole_clearance 0.25 -> 0.2`.
  - On `wk/gp14/04_multichannel_mixer/repro/pile.kicad_pcb` (`--nets GND GND --plane-layers F.Cu B.Cu --clearance 0.3`) it writes `min_track_width 0.3 -> 0.2` and `min_via_diameter 1.5 -> 0.6`.
  - The next `route.py ... --via-drill 0.5` on the 05 pour output prints "via drill: 0.6 -> 0.2 mm; 122 of 122 ... below the ORIGINAL 0.6mm". Without the pour step that line does not appear.
  - Cause: route_planes.py:4777-4782 passes its size and clearance params unconditionally; fix_kicad_drc_settings.py:1182 baselines an undeclared key on the immediate input.
  - Expected (as #1195 did for qfn_fanout): a run that drew no via or track writes no via or track floors, and none of the size or hole-clearance floors when it changed no copper. A key the board never declared is not reported as "ORIGINAL".

### M12 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - 12 #5 route: `route.py wk/gp14/12_steppenprobe/repro/v1_step2a.kicad_pcb _verify/B05/m12/v1_out.kicad_pcb ... --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3` produced:
    - `Design rules [--escalation fab, --fab-tier auto]: 17 feature(s) on 4 net(s) ... smallest clearance 0.127 ... 11 fab-tier escalation(s)`
    - writes `min_via_diameter 0.6 -> 0.45`, `Default 0.15 -> 0.127`
    - board_score with spec flags: `BLOCKING=3 (undersized=3)`; without spec flags: `BLOCKING=0`.
  - 12 #9 qfn: `qfn_fanout.py wk/gp14/12_steppenprobe/repro/r2_s0.kicad_pcb --component U1 --nets '*' '!GND' '!+3V3' --clearance-ceiling 0.15 --track-width 0.15` printed:
    - `--clearance-ceiling 0.15: no cap applied -- --clearance 0.1 is already at or below it`
    - writes `net_class[Default].clearance 0.15 -> 0.1`, `[Power] 0.15 -> 0.1`, `min_hole_clearance 0.25 -> 0.1`
    - escaped 31/31.
  - The same command with `--clearance 0.15` also escaped **31/31**, writing only `min_hole_clearance 0.25 -> 0.15`.
  - Downstream: the next `route.py --clearance-ceiling 0.15` on the default-fanout board says `base = the board Default net-class clearance 0.1mm`; on the 0.15-fanout board it says 0.15mm.
- cause:
  - The escalation/descent half is the documented default and is NOT A BUG: CLAUDE.md "Sizes and escalation (#857/#530): ... descents allowed below the board's own declared minimums ... Completion first, DISCLOSED". It is disclosed. #1160's resolution keeps the class ratchet deliberately ("#489 section 2 was declined").
  - `--clearance-ceiling` caps from above by definition. Bounding descents is `--escalation board`'s job.
  - The real defect is qfn_fanout. `qfn_fanout/__init__.py:1741` defaults `--clearance` to `routing_defaults.QFN_CLEARANCE` 0.1 (routing_defaults.py:249), not the board's Default class. `fab_tiers.apply_clearance_ceiling` (fab_tiers.py:1182-1224) then treats that default as "requested" (`min(0.1, 0.15)`), and the writeback clamps every class to it.
  - So the spelling the skill prescribes for qfn_fanout (SKILL.md:567-571, "spell it --clearance-ceiling <value>") lowers the whole chain's clearance from 0.15 to 0.1 with no need.
- branch head 86b54a1d: unchanged; main 0523df20: same code (`QFN_CLEARANCE = 0.1`, same `apply_clearance_ceiling`).
- upstream: the escalation half is documented (#857, #530, #1160 CLOSED). The qfn half is new, same family as #1195 (CLOSED). searches: "qfn_fanout default clearance", "qfn_fanout clearance-ceiling", "fanout default clearance netclass", "escalation fab below board minimums", "clearance-ceiling descent", "fab-tier auto skill chain declared floors".
- severity after verification: MEDIUM (qfn half); none for the escalation half
- issue draft:
  title: qfn_fanout defaults --clearance to 0.1 instead of the board's Default class; with the chain's --clearance-ceiling it lowers every net class and the next route step routes the whole board at 0.1
  body:
  - `qfn_fanout.py wk/gp14/12_steppenprobe/repro/r2_s0.kicad_pcb --component U1 --nets '*' '!GND' '!+3V3' --output out.kicad_pcb --clearance-ceiling 0.15 --track-width 0.15` prints "no cap applied -- --clearance 0.1 is already at or below it". It writes Default 0.15 -> 0.1, Power 0.15 -> 0.1, min_hole_clearance 0.25 -> 0.1.
  - With `--clearance 0.15` the same fanout escapes 31/31 as well.
  - A following `route.py out.kicad_pcb ... --clearance-ceiling 0.15` reports "base = the board Default net-class clearance 0.1mm".
  - Expected: with `--clearance` omitted, qfn_fanout takes the board's Default class, as route.py does ("Both omitted -> base = the board's Default class"). The ceiling then caps that value.

### H26 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - Replayed `wk/gp14/12_steppenprobe/expP1b/plan.sh` with paths rewritten to `_verify/B05/h26/` (`plan.sh`, `chain.log`). `board_score step4b --net-min-widths widths.json` gives **BLOCKING=5 (net_widths=5)**, vias 110, copper 966.97, identical to the teammate's board.
  - Under-width copper by net: GND 17.6 mm (35 segs), +1V8 8.13, /VPLL 1.90, /VPHY 1.08, +3V3 0.30. Total 29.01 mm, all laid by the main route step (step2). Except the +3V3 piece, every segment is within 3 mm of a U1 pad centre.
  - My own geometric probe (`scripts/h26_widen_probe.py`) redraws each under-width segment on its own centreline at 0.3 against all foreign pads, tracks and vias on its layer at 0.15: **20.59 of 29.01 mm fits in place**. That matches the teammate verifier.
  - The disclosure is present: the merged `--json-out` carries `power copper shipped under width` rows for 4 nets.
  - `--no-power-tap-neckdown` on the step2 route (`v_noneck`) still ships necks: GND 28.5 mm, +3V3 7.0 mm, +1V8 8.7 mm, still net_widths=5, 190/190 pads connected. I did not reproduce "+1V8 breaks"; P2b/P4b/P5b were not re-run.
- cause: partly established. Many GND necks are pad→via taps of ~1.1 mm at U1's 0.3 mm-wide LQFP pins, at 0.15. `py_router/plane_pad_tap.py:246` sets the fine-pitch tap width to `max(fab_track, min(pad short side, config.track_width))`, i.e. the call's signal width (0.15), never the net's power width capped at the pad (0.3). b070abbe (#1033 part 1) changed only what this site records, not what it draws. The +1V8/VPHY/VPLL necks come from other narrowing sites (terminal neck / taper); not traced.
- branch head 86b54a1d: unchanged; main 0523df20: `plane_pad_tap.py:246` same code. `single_ended_routing.py` differs on main (#1290-#1295 work); the outcome on main was not measured.
- upstream: new; residual of #1033 (CLOSED: power nets laid at the signal `--track-width`) at fine-pitch pins. Related #593 (OPEN), #72 (CLOSED). searches: "power net neck fine pitch", "fine-pitch tap power width", "neckdown power net width", "power copper shipped under width", "power-tap-neckdown", "power width pad entry neck", "plane tap track width power".
- severity after verification: MEDIUM. It is disclosed, but real copper ships under its declared width (0.6 A bottleneck), and 71% of it was avoidable.
- issue draft:
  title: route.py ships 0.15 mm necks on 0.3 mm power nets at 0.5 mm-pitch LQFP pins where a 0.3 track fits (fine-pitch tap draws the call's --track-width)
  body:
  - Replaying `wk/gp14/12_steppenprobe/expP1b/plan.sh` (`--power-nets-widths 0.3` for 8 nets, `--track-width 0.15`, `--escalation board --fab-tier standard`) gives 29.01 mm of power copper at 0.15. GND 17.6, +1V8 8.13, /VPLL 1.90, /VPHY 1.08, +3V3 0.30, at U1 (LQFP-64, pads 0.3 x 1.55, pitch 0.5). `board_score --net-min-widths wk/gp14/12_steppenprobe/widths.json` reports net_widths=5.
  - Redrawing each under-width segment at 0.3 on its own centreline clears every foreign pad, track and via by ≥ 0.15 for 20.59 mm of the 29.01 mm.
  - `--no-power-tap-neckdown` does not remove the necks (GND 28.5 mm).
  - plane_pad_tap.py:246 sets the fine-pitch tap width to min(pad short side, the call's --track-width), not the net's power width.
  - Expected: try the net's own width (capped at the pad width) before the signal width, and neck only where the wider track does not fit.

### H12 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `list_nets.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb --design-rules` prints `[Power] ... track_width=0.3` with no member line. The `.kicad_pro` lists the members in `net_settings.classes[1].nets` (+1V8, +3V3, +5V, /VPHY, /VPLL, GND, VBUS, Vdrive) and has no `netclass_assignments`.
  - KiCad 10.0.7 (`pcbnew.LoadBoard` → `GetNetClassName()`) resolves +1V8, GND, /VPHY and Vdrive to **Power**.
  - Side-by-side on the same board (`_verify/B05/h12/k6` = as given, `k7` = same members moved into `netclass_assignments`): `route.py --nets '+1V8' '/VPHY' '/VPLL' 'Vdrive'` with `--track-width` omitted.
    - k6: all new copper at **0.15**.
    - k7: prints `Auto-read netclass track widths for 8 non-Default net(s)` and routes at **0.3** (except short necks).
    - list_nets on k7 prints "8 net(s) assigned to non-default classes".
  - `board_score final.kicad_pcb --quiet` gives BLOCKING=0 with net_widths UNGRADED; with `--net-min-widths widths.json` it gives net_widths=5. `check_complete final.kicad_pcb` gives `VERDICT: DONE ... UNEXAMINED, and not passed: ... net_widths`.
- cause (re-diagnosed):
  - The defect is that no netclass reader reads the KiCad-6 membership form `classes[].nets`: `py_router/list_nets.py:166-199` (`read_design_rules`) and `py_router/design_rules.py:846-871` (`DesignRules.from_project`) read only `netclass_assignments` and `netclass_patterns`. Every consumer (route.py class widths and vias, the #530 class-clearance map, list_nets, and the GUI tabs, which use the same readers) therefore treats those nets as Default.
  - Not bugs on their own:
    - net_widths is opt-in by design (`board_score.py:998-999`), and check_complete names it UNEXAMINED.
    - An explicit `--track-width` overriding class widths is documented (#435, route.py:1666-1670).
  - The 08 bullet (M2_LX at 0.1 mm) was not verified.
- branch head 86b54a1d: unchanged; main 0523df20: same reader logic in list_nets.py and design_rules.py (neither reads `classes[].nets`).
- upstream: new (nearest #1237 OPEN audit design, #530 CLOSED clearance, #1033 CLOSED). searches: "KiCad 6 netclass nets", "netclass membership kicad_pro classes nets", "net class assignments KiCad 6 project", "netclass track width net_widths", "legacy netclass", "net_settings classes nets".
- severity after verification: HIGH. Declared class rules are silently dropped for every KiCad-6-format project, and on board 12 only the independent verifier caught the narrow power copper.
- issue draft:
  title: KiCad-6 netclass membership (`net_settings.classes[].nets`) is read by no netclass reader: member nets route at the Default width/clearance/via
  body:
  - `wk/gp14/12_steppenprobe/repro/pile.kicad_pro` (meta version 1) lists the Power class members inside `classes[].nets`. KiCad 10.0.7 resolves them to Power, but `list_nets.py --design-rules` shows `[Power] track_width=0.3` with no members.
  - On `wk/gp14/12_steppenprobe/repro/v1_step2a.kicad_pcb`, `route.py --nets '+1V8' '/VPHY' '/VPLL' 'Vdrive'` with `--track-width` omitted routes them at 0.15. With the same members moved to `netclass_assignments` it prints "Auto-read netclass track widths for 8 non-Default net(s)" and routes at 0.3.
  - Cause: `list_nets.read_design_rules` (list_nets.py:166-199) and `DesignRules.from_project` (design_rules.py:846-871) read only `netclass_assignments` and `netclass_patterns`. Class clearances and vias are lost the same way.
  - Expected: read `classes[].nets` as explicit assignments, as KiCad does when it loads a KiCad-6 project.

Everything I ran is under `wk/gp14/_verify/B05/`, with folders `h06`, `m14`, `m01`, `m12`, `h26`, `h12` and `scripts`. Nothing tracked was modified.

<!-- batch B06 -->
### H08 -- VERDICT: CONFIRMED
- repro at 8328f157 (outputs under `wk/gp14/_verify/B06/h08_*`):
  - **Board 11:** `check_floorplan placed_s3 --intent intent_edges.json` gives 0 errors. The reading is `J2/J3 7.0062mm, P1 1.0500mm [legacy_occupancy@margin=0.55] pass`, and the knob is `edge_clearance_used {"source":"fixed default","value":0.55}`.
    - The same command on `armA_routed --allow-routed` gives 3 ERRORs: `J2/J3 6.6562mm`, `P1 0.7000mm [legacy_occupancy@margin=0.2]`, with `edge_clearance_used {"source":"board constraint","value":0.2}`.
    - Parsed both boards: 0 footprints moved. The projects differ: `min_copper_edge_clearance` 0.0 -> 0.2, and Default class 0.2 -> 0.1818.
  - **Board 02:** I re-ran the chain myself: `route_planes s7 -> h08_02_planes`, then `route.py` with the board's flags.
    - `route_planes` printed `rules.min_copper_edge_clearance: 0.01 -> 0.2 mm (fab-edge pin)`.
    - `route.py` printed `DEFAULT CLASS CLEARANCE LOWERED BY A DESCENT -- 0.254 -> 0.2223`.
    - Before routing: `J1 25.8800 / J2 14.4500 [legacy_occupancy@margin=0.254] pass`, 0 errors.
    - After routing: `J1 25.7849 / J2 14.4183 [legacy_occupancy@margin=0.2223] fail`, 2 ERRORs.
    - J1's `pad copper 0.0150mm vs 0.2mm fail` is a different matter: it is the M01 edge pin, which is a real floor change, not this currency problem.
  - **11 #5:** `check_assembly placed_p1_band0` prints `P1 1.055mm [edge_receptacle]` "in the band but belonging at the edge". So band 0 is not flush on a rounded outline.
- cause:
  - The band is read on the legacy path at `floorplan.py:4751` (`amount = ctx.gate.rect_outside_amount(part.rect)`), passed through `_band_amount` (`floorplan.py:4765`, `4992-4997`), which names the basis at `connector_geometry.py:431-444`.
  - That path measures courtyard overhang + `gate.margin`, and `gate.margin = max(clearance, board_edge_clearance)` (`quench.py:1133`).
  - Both knobs come from the project via `list_nets.board_floor_knobs` (`list_nets.py:375-416`). A declared 0 counts as unset and becomes the fixed default 0.55.
  - The routing writebacks rewrite both knobs: the fab-edge pin at `fix_kicad_drc_settings.py:1510-1514`, and the descent writeback at `fix_kicad_drc_settings.py:1727`. So a band written against the placed board changes meaning after routing.
- branch head 86b54a1d: unchanged (the floorplan/quench diffs only add graphic-copper gating). main 0523df20: same code (`quench.py:1364`, `floorplan.py:4865`, `connector_geometry.py:444`, identical `board_floor_knobs`).
- upstream: new. Related: #961 (closed; added the body path and left the legacy path in margin currency) and #1160 (closed; same writeback, different consequence). Searches: "overhang band margin", "legacy_occupancy", "edge connector overhang routing", "fab-edge pin", "overhang_mm courtyard currency", "edge_connector writeback", "floorplan fails after routing", "rounded outline overhang", "descent writeback placement grade".
- severity after verification: HIGH
- issue draft:
  title: An edge connector's overhang_mm band, graded on the courtyard, changes value when a routing step rewrites the project floors: the same pose passes before routing and fails after
  body: When the drawn body cannot be measured (rounded outline, unusable Fab), `rule_edge_connector` grades `overhang_mm` as `legacy_occupancy@margin=m`, with `m = max(Default class clearance, min_copper_edge_clearance)` read from the board's `.kicad_pro` (`quench.py:1133`, `list_nets.board_floor_knobs`). The routing chain rewrites both values: route_planes' "fab-edge pin" and route.py's descent writeback to the Default class. So a placement that passes fails after routing, with no footprint moved.
  Measured on wk/gp14/11_daplink/repro (0 footprints moved):
  - placed_s3: margin 0.55 (fixed default; the project declares 0). J2/J3 read 7.0062, P1 reads 1.0500: pass.
  - armA_routed: margin 0.2. J2/J3 read 6.6562, P1 reads 0.7000: 3 ERRORs. board_score counts them as blocking.
  On wk/gp14/02_sonde_xilinx/repro/s7, after route_planes then route.py: margin 0.254 -> 0.2223, J1 25.88 -> 25.7849 and J2 14.45 -> 14.4183, 2 ERRORs.
  Repro: `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/11_daplink/repro/placed_s3.kicad_pcb --intent wk/gp14/11_daplink/repro/intent_edges.json` (0 errors), then the same on `armA_routed.kicad_pcb --allow-routed` (3 errors).
  Expected: a declared band grades the same physical pose to the same number before and after routing. Either pin the grade's margin when the band is declared, or grade it at a margin a routing writeback does not move.

### M10 -- VERDICT: NOT A BUG
- repro at 8328f157:
  - 02 `final --intent intent_seat.json --allow-routed`: exit 4, `"errors": 0`, `"pass": false`, `not_graded {"budget_abstained": 3, "rules_skipped_armed": 3}`. The abstained keys are `decaps.max_distance_mm`, `oob_count` and `overlap_area`.
  - 01 `final --intent intent.json`: exit 4, with the same three abstained keys.
  - 13 `final --intent intent.json`: exit 4, abstained `oob_count` and `overlap_area`.
  - Declaring the withheld keys by hand (`legality_budget {oob_count:0, overlap_area:0}`, `decaps.max_distance_mm:6`, in `m10_intent_declared.json`) gives exit 0 and `"pass": true`, with OWED rows still printed. So the exit 4 is not "forever".
  - Writing `dispositions.withheld` for the three keys instead still gives exit 4.
- cause:
  - The exit 4 is deliberate. `check_floorplan.py:1011-1024` exits 4 when `not result.complete` (#713 item 5), and `complete`/`passed` (`floorplan.py:7499-7559`) count pile-withheld budgets as declared-but-ungraded.
  - A key declared by hand clears it (`floorplan.py:8615-8619`, `_declared_by_hand`).
  - Re-diagnosis for 01 and 13: the OWED rows (`rules_dark_undispositioned`) do not affect the exit code at all. On all three boards the cause is the #1103 pile withholding.
  - The skills grade check_floorplan by "0 errors", not by its exit code (`plan-pcb-placement/references/verifier.md:28`).
  - Residual LOW nits:
    - The module's exit-code table still says `4 = error-severity violations found` (`check_floorplan.py:26-31`).
    - `roster_refusal_lines` offers `dispositions.withheld.<k>` as an equal answer (`floorplan.py:7382-7383`), but that answer does not clear `pass`.
- branch head 86b54a1d: unchanged. main 0523df20: same code (the docstring line is at `check_floorplan.py:33`, NOT FULLY GRADED at `:1187`).
- upstream: not filed. Searches: "NOT FULLY GRADED", "check_floorplan exit 4", "budget_abstained", "pile withheld oob_count", "check_floorplan exit code" (#1103 is the withholding itself).
- severity after verification: LOW (docstring and disposition wording only)

### M18 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157 (kicad-cli 10 on PATH):
  - **03:** `kicad_drc_compare gap3_final --baseline gap3_baseline_pile` opens with `FOUND 729 DRC VIOLATIONS: PAD-PAD violations (729) -- 536 in CONTACT` (pads at y 136-145, the pile). The graded board's line is `kicad=0 check_drc=0 ... CONSISTENT`, exit 0.
  - **07:** `kicad_drc_compare kicad_drc/placed --baseline repro/input` prints the pile's 6124 check_drc items first, then `kicad=8 (+2 pre-existing on input, subtracted) check_drc=0 ... kicad_only=8 DIVERGED`, exit 1.
    - In-process: without `--baseline` it is kicad=10, also DIVERGED.
    - The 8 are `clearance ['<no net>','Net-(Q1-D)']` (7) and `['<no net>','Net-(F2-Pad2)']` (1), each actual 0.000 mm.
    - The pile's 907 KiCad items contain only 1 `(clearance, {<no net>, Net-(Q1-D)})` twin.
- cause:
  - **03 half (confirmed):** `kicad_drc_compare.py:949` runs `run_check_drc(baseline)`, i.e. `run_drc(quiet=True, print_summary=False)`. `check_drc.py:5255` (`if not quiet or violations:`) still prints the full listing whenever there are violations. The #383 comment at `kicad_drc_compare.py:268` says it is silent only in the success path. The baseline's listing is therefore printed unlabelled at the head of the report.
  - **07 half (re-diagnosed):**
    - The subtraction is not purely positional. Pass 2 matches `(type, nets)` twins regardless of position (`kicad_drc_compare.py:779-803`).
    - The items survive because KiCad reports a different multiset on a pile (1 Q1 item vs 7).
    - The DIVERGED itself comes from check_drc deliberately skipping same-footprint pad pairs (`check_drc.py:4301-4309`), which KiCad grades. That gap exists with or without a baseline.
- branch head 86b54a1d: unchanged. main 0523df20: same code (`check_drc.py:5328`, `kicad_drc_compare.py:779/949`, same-footprint skip at `check_drc.py:4381`).
- upstream: new. Related: #383 (closed). Searches: "kicad_drc_compare baseline", "kicad_drc_compare pile", "print_summary", "kicad_drc_compare prints", "same footprint pads kicad_only", "baseline subtraction footprint".
- severity after verification: LOW
- issue draft:
  title: kicad_drc_compare --baseline prints the baseline board's full check_drc listing, unlabelled, as the head of the graded board's report
  body: `run_check_drc` calls `check_drc.run_drc(quiet=True, print_summary=False)` for the baseline (`kicad_drc_compare.py:949`). `run_drc` still prints `FOUND N DRC VIOLATIONS` and the per-type listing whenever there are violations (`check_drc.py:5255`, `if not quiet or violations`). `print_summary=False` only silences the success path.
  With a pile as baseline (wk/gp14/03_complex_hierarchy/repro), the report opens with `FOUND 729 DRC VIOLATIONS: PAD-PAD violations (729) -- 536 in CONTACT` for pads south of the outline. The verdict for the graded board is `kicad=0 check_drc=0 CONSISTENT`.
  Repro: `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gp14/03_complex_hierarchy/repro/gap3_final.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap3_baseline_pile.kicad_pcb | head -12`.
  Related, measured on wk/gp14/07_One-Air-Max: on a pile baseline, footprint-inherent KiCad items (Q1's drain pads vs its net-less EP, which check_drc skips as same-footprint) are not cancelled. KiCad reports 7 of them on the placed board and 1 on the pile, so they read as kicad_only=8 DIVERGED.
  Expected: run_drc prints nothing when `print_summary=False`, or the baseline listing is labelled as the baseline. The README/--help should say that a baseline only cancels items KiCad reports identically on both boards, which a pile does not.

### M19 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - **04:** copied `old4_final` (`copy_board`) and ran `kicad-cli pcb drc --refill-zones --severity-all`: **2 `starved_thermal` errors** (IC1.4 and IC2.4 GND, "min spoke count 2; actual 1"; project severity error) and **10 `connection_width` warnings** against min_connection 0.3.
    - Nine are GND zone necks at 0.244-0.286 mm (the input's own zone has `min_thickness 0.25`).
    - One is a router T-joint at a via, `/CH1/OUT` at 0.1477 mm.
    - `check_weird` prints `NO WEIRD THINGS FOUND!`.
    - `kicad_drc_compare --baseline pile` prints `connwidth=10@<0.3mm  CONSISTENT`.
  - **06:** `kicad_drc_compare final_copy --baseline input` gives `connwidth=1@<0.075mm` at J1 D+, and check_weird is clean. But a plain kicad-cli DRC with the board's own project reports **0** connection_width: the project has `min_connection 0.0` (disabled). The item exists only under kicad_drc_compare's staged floor (min_track_width 0.075).
- cause:
  - No repo grader reads `starved_thermal`. It appears only in the severity-demotion list (`fix_kicad_drc_settings.py:101`).
  - kicad_drc_compare filters it as "known-benign" by design (`kicad_drc_compare.py:21`).
  - check_weird's `narrow-pad-joint` models only degree-1 terminal caps on pads (`check_weird.py:779-860`), so via T-joints and pour necks are invisible.
  - Not a defect: kicad_drc_compare's CONSISTENT is documented as the clearance verdict only, with connection_width "graded SEPARATELY" (docstring lines 25-31).
  - The 06 instance is not a KiCad warning under the board's own rules.
- branch head 86b54a1d: unchanged. main 0523df20: same code (no `starved_thermal` in check_weird, board_score or check_complete; same `_check_terminal_web`).
- upstream: new. Related: #1161, #1187, #547, #416, #856 (all closed). Searches: "starved_thermal", "thermal spoke", "connection_width", "min_connection", "narrow web via".
- severity after verification: MEDIUM
- issue draft:
  title: A DONE board ships KiCad starved_thermal errors and sub-min_connection via/pour webs that no repo grader reports
  body: On wk/gp14/04_multichannel_mixer/repro/old4_final.kicad_pcb (project `min_connection 0.3`, `min_resolved_spokes 2`, starved_thermal severity error), `kicad-cli pcb drc --refill-zones` reports:
  - 2 `starved_thermal` errors (IC1.4 and IC2.4 GND, 1 spoke of 2);
  - 10 `connection_width` items: 9 GND pour necks at 0.244-0.286 mm, and 1 router-made via T-joint on /CH1/OUT at 0.1477 mm.
  `check_weird.py` prints NO WEIRD THINGS FOUND (`narrow-pad-joint` models only terminal caps on pads, `check_weird.py:779-860`). check_drc, board_score and check_complete never read either class, and `kicad_drc_compare` filters starved_thermal as benign.
  Repro: `python3 py_router/copy_board.py wk/gp14/04_multichannel_mixer/repro/old4_final.kicad_pcb <tmp>/b.kicad_pcb && kicad-cli pcb drc --refill-zones --format json --severity-all -o <tmp>/d.json <tmp>/b.kicad_pcb`.
  Expected: some grader on the DONE path reports KiCad's starved_thermal (at the project's severity) and connection_width webs at vias and pours, or the skills run the KiCad cross-check and gate on those classes.

### M20 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `kicad-cli pcb drc --format json --severity-all` on `01/repro/final_copy` (0 `filled_polygon`): `Found 6 unconnected items`, every GND pad (P2.2–R3.2, … P1.1–R4.2).
  - The same on `final2_copy` (`--write-fill`, 1 `filled_polygon`): `Found 0 unconnected items`. The other 19 violations are identical on both.
  - The input file's sha was unchanged by the DRC run.
- cause:
  - The tool behaviour is the documented default. The route.py `--write-fill` help (`route.py:8576-8583`) and `py_tools/fill_for_delivery.py` say the deliverable carries zone outlines only and the fill is opt-in (#910).
  - The defect is in the skills. No step of plan-pcb-routing or plan-pcb-placement names `--write-fill` or `fill_for_delivery`. It is reachable only through `krt_registry --door routing`.
  - #910's proposal also asked for the deliverables section to document the "N plane opens until refilled" caveat. That caveat is not in either skill (review-routed-board says only to use `--refill-zones`).
  - KiCad's GUI DRC refills by default, so the user-visible effect is plain kicad-cli and the ratsnest shown before pressing B.
- branch head 86b54a1d: unchanged (the placement SKILL.md was rewritten, still with no fill step). main 0523df20: the `pcb-free-agent` and `plan-pcb-routing` skills do not mention it either.
- upstream: evidence for a skill follow-up to #910 (closed, the tool). #937 (closed) listed fill_for_delivery as "never named" in the skills. Searches: "write-fill", "unfilled zone", "fill_for_delivery", "filled_polygon deliverable".
- severity after verification: LOW
- issue draft:
  title: The placement/routing skills never run the delivery fill (#910), so a DONE board opens with plane "opens" until refilled
  body: Neither plan-pcb-routing nor plan-pcb-placement (nor pcb-free-agent on main) names `route.py --write-fill` or `py_tools/fill_for_delivery.py`, and neither carries #910's "unfilled until refilled" caveat.
  Measured on wk/gp14/01_ecc83-pp_v2/repro: plain `kicad-cli pcb drc` on final_copy.kicad_pcb (the skill chain's output) reports 6 unconnected items, all GND pads. On final2_copy.kicad_pcb (the same chain plus `--write-fill`) it reports 0, with copper otherwise unchanged. check_connected and check_complete refill internally and report fully connected / DONE.
  Expected: the skills' delivery step runs the fill, or the REPORT states the board must be refilled (press B / `--refill-zones`) before plotting.

### L09 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - kicad-cli DRC on `01/repro/final_copy`: `silk_overlap` ×3 (P1 ref vs U1 silk circle, U1 ref vs P3 ref, P4 ref vs R2 silk segment) and `silk_over_copper` ×1 (U1 ref vs R2 pad 1), all severity **error** in this project.
  - `beautify_labels.py` on a `copy_board` copy of `final2_copy` modified 15 labels. KiCad DRC on its output: **0** silk items (only the 15 lib_footprint_issues warnings remain) and 0 unconnected.
- cause:
  - kicad_drc_compare excludes silkscreen by design (`kicad_drc_compare.py:21`, `:703-709`).
  - No DONE-path grader checks silk.
  - `py_placer/beautify_labels.py` (#481) fixes it and is listed in `krt_registry --door placement`, but no skill step names it. This is a skill-text gap.
- branch head 86b54a1d: unchanged (no silk/beautify mention in the placement or routing skills). main 0523df20: `pcb-free-agent` and `plan-pcb-routing` do not mention it either.
- upstream: new as a skill gap. #481 and #1202 (closed) cover the tool itself; #937 (closed) listed beautify_labels as never named. Searches: "silk_overlap", "beautify_labels skill", "silkscreen grade".
- severity after verification: LOW
- issue draft:
  title: No skill step grades or tidies silkscreen: a verified-DONE board carries 4 KiCad silk errors that beautify_labels removes
  body: On wk/gp14/01_ecc83-pp_v2/repro/final_copy.kicad_pcb, `kicad-cli pcb drc --severity-all` reports 3 `silk_overlap` and 1 `silk_over_copper`, both at project severity error. check_complete said DONE, and kicad_drc_compare (copper-only by design) said CONSISTENT.
  Running `python3 -X utf8 py_placer/beautify_labels.py <copy> <out>` (15 labels moved) gives 0 silk items on re-check, with connectivity unchanged.
  Expected: the placement or routing skill's finishing step runs beautify_labels, or the verifier grades KiCad's silk classes.

### H25 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `check_drc u1_local_clearance` (default margin): `NO DRC VIOLATIONS FOUND!`.
  - `--clearance-margin 0`: `FOUND 15 DRC VIOLATIONS`, all PAD-SEGMENT at U1, all `Required clearance: 0.1200mm (local/netclass override; global 0.1000mm)`. Overlaps: 0.005 mm ×11, 0.004 ×2, 0.001 ×2. None is at the 0.1 netclass value.
  - `kicad_drc_compare --baseline r1_fixed`: `kicad=6 check_drc=0 kicad_only=6 DIVERGED` ("footprint U1 clearance 0.1200 mm"), exit 1.
- cause:
  - The 5 % tolerance is documented and deliberate: `--clearance-margin` defaults to 0.05, and its help says "Violations smaller than clearance*margin are ignored" (`check_drc.py:5466-5467`, `_grade_tol` `:43-45`). CLAUDE.md even recommends 0.1.
  - board_score's drc component inherits that default. The repo's own KiCad cross-check catches it as designed.
  - The real defect is upstream of the checker: routed copper sits 1-5 µm inside U1's 0.12 mm footprint override (and nowhere inside the 0.1 netclass value), which KiCad rejects as errors.
  - Which chain step laid it (fanout, route_diff, route.py or a post-pass) is not established. The pad stamp itself resolves the override (`obstacle_map.py:4377-4396`).
- branch head 86b54a1d: unchanged. main 0523df20: same default (`check_drc.py:5539`).
- upstream: new. Related: #326 (closed, check_drc now reads overrides), #1216 (closed, routing clearance margin), #173 and #526 (closed, sub-cell grazes). Searches: "clearance-margin", "clearance margin KiCad rejects", "local clearance override graze", "footprint clearance 0.12", "check_drc tolerance kicad_only", "sub-grid graze pad".
- severity after verification: MEDIUM
- issue draft:
  title: Routed copper lands 1-5 µm inside a footprint's local clearance override; KiCad flags it, but check_drc's default margin and board_score read clean
  body: On wk/gp14/14_imx6ulz_4l/repro/u1_local_clearance.kicad_pcb, U1 declares a footprint clearance of 0.12 mm over a 0.1 mm Default class. `check_drc --clearance-margin 0` finds 15 PAD-SEGMENT items at U1, all "Required 0.1200mm (local/netclass override)" with overlap 0.001-0.005 mm, and none at the 0.1 netclass value. KiCad reports 6 clearance errors: `kicad_drc_compare ... --baseline r1_fixed.kicad_pcb` gives kicad=6, check_drc=0, DIVERGED. At the default 5 % margin, check_drc and board_score report 0, so the DONE gates pass a board KiCad rejects.
  Repro: `python3 -X utf8 py_router/check_drc.py wk/gp14/14_imx6ulz_4l/repro/u1_local_clearance.kicad_pcb --clearance-margin 0 | grep FOUND` (15); without the flag: clean.
  Expected: the router honours a pad or footprint clearance override to KiCad's tolerance, as it does the netclass value here. Failing that, the DONE graders should not tolerate sub-margin grazes against an override KiCad grades exactly.

<!-- batch B07 -->
### H09 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster's command with outputs in `wk/gp14/_verify/B07/h09/`: `REDO_RUNDIR=$F REDO_MANIFEST=$F/redo_commands.sh KICAD_PLANE_FRAGILITY_COST=0 python3 -X utf8 py_router/route.py wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb $F/env_run.kicad_pcb --nets '*' ... --grid-step 0.05`.
  - The run's own JSON_SUMMARY says `"env_knobs": {"KICAD_PLANE_FRAGILITY_COST": "0"}`.
  - `tail -1 $F/redo_commands.sh` records `python3 -u -X utf8 py_router/route.py ...` with no prefix.
  - I replayed the recorded line with no env (`noenv_run.kicad_pcb`). board_score gives env run **vias=0 copper_mm=131.72** and replay **vias=2 copper_mm=146.1**, both blocking 0. That is exactly the claimed numbers.
  - manifest_to_plan on the recorded manifest writes a 1-step plan and prints "0 command(s) skipped". On a hand-written line carrying the prefix (`h09/handplan_env.sh`) the prefix is also dropped with no warning (params `{grid_step: 0.05}` only).
  - Extra: `redo_stress_test.py`, the replayer the manifest header names, cannot replay a hand-added env prefix at all. On `h09/handplan_env_abs.sh` it crashes with `PermissionError: [Errno 13] Permission denied: 'KICAD_PLANE_FRAGILITY_COST=0'` (`h09/rs_replay.log`). So annotating the manifest by hand (board 08's workaround) only works with plain `bash`.
  - Board 08: `grep -c KICAD_PLANE_FRAGILITY final_route_old1/redo_commands.sh` gives 0. The `final_route/*.log` files carry `"env_knobs": {"KICAD_PLANE_FRAGILITY_LAYERS": "GND@F.Cu=0,GND@B.Cu=0", ...}` 4 times.
- cause: `py_router/redo_record.py:97-110` records `["python3","-u","-X","utf8"] + sys.argv` and never reads the environment. `env_knobs.active_env_knobs()` (py_router/env_knobs.py:621) already lists the active knobs and goes into JSON_SUMMARY, but the recorder does not use it. `tests/stress/redo_stress_test.py:197` runs `Popen(argv)` directly, so a `KEY=VAL` token in argv[0] is executed as a program. The skill (plan-pcb-routing SKILL.md:1789-1798, 1154-1158) tells agents to pass these knobs as env prefixes "so the manifest replays them".
- branch head 86b54a1d: unchanged (redo_record.py and redo_stress_test.py have no diff). main 0523df20: same code (redo_record.py identical; redo_stress_test.py differs only in comments and `_OUTPUT_FLAGS`).
- upstream: new. Related: #670 (OPEN) covers only the GUI plan-JSON half, and its premise "env knobs replay fine in redo-manifest plan files" is false for the auto-recorded manifest and for redo_stress_test. #653 (CLOSED) added the knobs to the log and JSON_SUMMARY but not to the manifest. Searches: "redo_record environment", "redo manifest env", "record_invocation env", "redo_commands env knob", "env knob replay", "KICAD_PLANE_FRAGILITY", "redo_stress_test env prefix", "env_knobs manifest", "replay env var", "manifest environment variable".
- severity after verification: HIGH. A no-LLM replay of a skill-recipe chain silently routes a different board, and it voids A/B replays of any chain that uses env knobs.
- issue draft:
  title: redo_record drops KICAD_* env knobs, so redo_commands.sh replays a different board (and redo_stress_test cannot replay an env prefix at all)
  body: `record_invocation` (py_router/redo_record.py:97-110) writes `python3 -u -X utf8` + sys.argv and never the environment. route.py's own JSON_SUMMARY lists `env_knobs`, but the manifest line has no prefix. Measured on `wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb`: the route with `KICAD_PLANE_FRAGILITY_COST=0` gives 0 vias / 131.72 mm. The recorded line replayed gives 2 vias / 146.10 mm (board_score; both blocking 0). Board 08 lost `KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'` the same way. The routing skill tells agents to pass these knobs as env prefixes "so the manifest replays them". Adding the prefix by hand does not help either: `redo_stress_test.py` Popens argv as-is and crashes with `PermissionError: 'KICAD_PLANE_FRAGILITY_COST=0'`. `manifest_to_plan` drops the prefix and still prints "0 command(s) skipped". Repro: `F=$(pwd)/wk/gp14/_verify/B07/h09; REDO_RUNDIR=$F REDO_MANIFEST=$F/redo_commands.sh KICAD_PLANE_FRAGILITY_COST=0 python3 -X utf8 py_router/route.py wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb $F/a.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05; tail -1 $F/redo_commands.sh`. Then run that line without the env and compare with `board_score.py --quiet`. Expected: the recorder writes the active env knobs as a prefix (e.g. from `env_knobs.active_env_knobs()`), redo_stress_test applies a leading `KEY=VAL` as env, and manifest_to_plan warns when it drops one.

### M23 -- VERDICT: CONFIRMED
- repro at 8328f157: `python3 -X utf8 tests/stress/manifest_to_plan.py wk/gp14/11_daplink/repro/m2p/daplink_plan.sh -o wk/gp14/_verify/B07/m23/daplink_from_plan.json`, run from the repo root where `wk/gp14/11_daplink/intent_edges.json` exists.
  - It prints `command 8: place_fanout_clearance.py refuses its arguments after parsing: cannot load intent ... [Errno 2]` and `4 step(s) written (1 command(s) skipped)`. The steps are `['route_diff','route','route','route']`.
  - The same file with one `# cwd=~/Documents/git/krt-gp14` line added (`m23/daplink_plan_with_cwd.sh`) converts to 7 steps: `['route_planes','fanout','optimize_caps','route_diff','route','route','route']`.
  - Board 12 (`steppenprobe_plan.sh`) writes 6 steps against 9 with `# cwd=` added. That is 3 steps lost (route_planes, fanout, optimize_caps), not just the cap pass as the cluster says, and it still reports "1 command(s) skipped".
  - Running the converter from another directory gives the same result, because the cwd is never taken from the process.
- cause: `tests/stress/redo_stress_test.py:245-270` (`parse_manifest`) only honours `# cwd=` comments. The `cd <repo>` line and the `export` lines are parsed as ordinary commands, and every command's cwd stays None. `manifest_to_plan.py:919` and `:973` then resolve relative paths against the manifest's own folder, so the intent check fails. `prune_manifest` (`:926`) breaks the file chain at the rejected command, and the dropped upstream steps are not counted (`skipped = len(rejected)`, `:959`). The defect is a contract mismatch: plan-pcb-routing SKILL.md:3209-3211 says to begin the plan with an explicit `cd <repo>` line, and `route_plan_check.r_starts_with_cd` enforces it, yet the converter the same Step 9 prescribes ignores that line. Not user error.
- branch head 86b54a1d: unchanged (only a REFUSED_TOOLS addition in manifest_to_plan.py). main 0523df20: same code (parse_manifest and the cwd fallback are identical, and the skill has the same `cd` instruction).
- upstream: new. Searches: "manifest_to_plan cd", "manifest_to_plan relative path", "manifest_to_plan cwd", "parse_manifest cd line", "plan.sh cd cwd", "manifest_to_plan skipped dropped steps", "manifest_to_plan intent", "manifest_to_plan" (25 results; #361, #493, #772 and #1067 are different), "redo_stress_test cwd" (#345, different).
- severity after verification: MEDIUM. The GUI plan JSON silently loses upstream board-mutating steps under a misleading count. The board and the `.sh` are unaffected.
- issue draft:
  title: manifest_to_plan ignores the plan.sh's `cd <repo>` line, falsely rejects a relative path, and silently prunes the upstream steps ("1 command skipped")
  body: plan-pcb-routing Step 9 says to begin `<board>_plan.sh` with `cd <repo>`, and route_plan_check enforces it. But `parse_manifest` (redo_stress_test.py:245-270) only reads `# cwd=` comments, so manifest_to_plan resolves relative paths against the manifest's folder (manifest_to_plan.py:919/973). A valid repo-relative `--intent` on place_fanout_clearance is then "rejected". The pruner drops everything upstream of it, and the summary counts 1 skip. Measured: `python3 -X utf8 tests/stress/manifest_to_plan.py wk/gp14/11_daplink/repro/m2p/daplink_plan.sh -o out.json` gives 4 steps (route_diff, route x3). The same file plus one `# cwd=<repo>` line (wk/gp14/_verify/B07/m23/daplink_plan_with_cwd.sh) gives 7 steps (route_planes, fanout, optimize_caps, route_diff, route x3). `wk/gp14/12_steppenprobe/steppenprobe_plan.sh` gives 6 against 9. Expected: a leading `cd DIR` sets the cwd the way `# cwd=` does (as the parse_manifest docstring's "a `cd` persists" implies). Steps lost to pruning should also be counted and named, not reported as "1 command(s) skipped".

### L07 -- VERDICT: CONFIRMED
- repro at 8328f157: all three gates exit 1, and each prints the same two failing rows (logs in `wk/gp14/_verify/B07/l07/`):
  - `python3 -X utf8 tests/test_route_flag_plan_coverage.py`: `FAIL test_the_whole_converter_gate_passes_on_the_fixture`.
  - `tests/test_route_flag_plan_coverage_controls.py`: `FAIL test_0_the_unmutated_copy_passes`.
  - `tests/gui_parity/test_manifest_plan_parity.py`: `Board-writing registry tools: FAILED`.
  - The rows: `movie3d/make_movie.py: a board-writing KRT_TOOL (actor) that manifest_to_plan neither maps, refuses nor lists as a no-op` (and the same for `movie3d/record.py`).
  - With the branch-head `manifest_to_plan.py` loaded in its place (`l07/run_with_head_m2p.py`), test_manifest_plan_parity exits 0 with `Board-writing registry tools: OK (42 declared ...)`.
- cause: `movie3d/make_movie.py:46` and `movie3d/record.py:34` declare `KRT_TOOL kind 'actor'`, and `tests/stress/manifest_to_plan.py` REFUSED_TOOLS (around :50-70) at the pin has no entry for either.
- branch head 86b54a1d: fixed by b5107a40 ("manifest_to_plan: refuse movie3d's two board-writing tools", +10 lines in REFUSED_TOOLS). main 0523df20: not on main (movie3d/ does not exist there).
- upstream: new, but already fixed at branch head without an issue. No issue needed. Searches: "movie3d manifest_to_plan", "make_movie record.py", "test_route_flag_plan_coverage", "movie3d".
- severity after verification: none (fixed at branch head). It was LOW at the pin.

### M36 -- VERDICT: NOT A BUG
- repro at 8328f157: I made two `copy_board` copies of `wk/gp14/01_ecc83-pp_v2/final.kicad_pcb` in `wk/gp14/_verify/B07/m36/{withkind,nokind}/`.
  - With the pre-campaign `_old_a22397f9/01_ecc83-pp_v2/mechanical.json` (keys context, fixed, kind, schema; `kind: mechanical-declaration`), `check_floorplan.py ... --intent wk/gp14/01_ecc83-pp_v2/intent.json` exits **2**: `mechanical.json: unknown key(s) ['kind']; a mechanical declaration carries only ['context','fixed','interfaces','note','project','schema']`.
  - With the campaign file (kind dropped) it reads `mechanical declaration ...: 4 pose(s), 0 edge(s)` and grades (exit 4, for unrelated grading reasons).
- cause: this is intended and documented. `py_placer/placement/reconcile.py:49-50` (`_MECH_KEYS`) and `:110-131` refuse any unknown key by design ("a file named mechanical.json that says nothing this module can read must not grade as 'no mechanical facts'"). `docs/floorplan-intent.md:1162-1163` says: "The file is read in the declaration form `{interfaces, fixed, project}`; anything else exits 2."
  - The `kind` key belonged to stage_unaided's output. This branch retired stage_unaided (ecd673eb deleted `tests/stress/stage_unaided.py`) and then removed its shape from the reader in d2e4c4c1 ("dead code"). The pin tracks no file carrying `kind`.
  - The refusal is loud and names the remedy (drop the key), which is what the campaign did.
  - The only real concern is at merge time: main still writes this key (`tests/stress/stage_unaided.py:299`) and still reads it (`reconcile.py:59,167`), and has the fixture `tests/fixtures/959/run29_mechanical.json`. That is a merge-planning matter, not a defect at the pin.
- branch head 86b54a1d: unchanged (reconcile.py has no diff). main 0523df20: differs. Main accepts both shapes, including `kind: 'mechanical-declaration'` on a declaration-form file.
- upstream: no issue (none needed). Searches: "mechanical.json kind", "mechanical-declaration", "mechanical.json unknown key", "stage_unaided mechanical" (#1001, #959, #903 are related history, not this).
- severity after verification: none (at most LOW, as a compatibility note for the branch-to-main merge).

### L08 -- VERDICT: CONFIRMED
- repro at 8328f157: `requirements.txt` lists numpy, scipy, shapely and Pillow, not ortools. `kicad_routing_plugin/deps_check.py:84-86` `OPTIONAL_PACKAGES` names only Pillow, although `awx/README.md:2032` planned "ortools optional in `deps_check`". Nothing in the repo says `pip install ortools`. To simulate a requirements-only install I blocked ortools with an import hook (`wk/gp14/_verify/B07/l08/no_ortools.py`):
  - 8 `tests/test_622_*` files print `SKIP: needs ortools` (candidate_ctx, crowd_diagnosis, far_face_teeth (5), joint_pairs, joint_rounds (check 3), lane_fixes, pose_heads, walled_balls).
  - `awx/route_bus.py ... --find` still works ("bus U1 -> U2, 47 nets").
  - The skill's Step 1a run itself fails: `awx/route_bus.py wk/gp14/14_imx6ulz_4l/repro/bus_in.kicad_pcb l08/bus_noortools.kicad_pcb --rounds 1 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25` runs 95 s and prints `fanout exit 1 at 95 s`, `WHOLE K=45 round=1 lanes=0/0 ... open=45`, `route_bus: the whole route laid nothing (exit 2)`, then exits 1.
  - The console never names ortools. The `ModuleNotFoundError` is only in `l08/bus_noortools.bus/U1-U2.bus/run/r1/fo.log`, raised at `awx/whole_ends.py:1394`.
- cause: ortools is a hard runtime dependency of the awx bus path (`awx/whole_ends.py:1394`, `awx/joint_escape.py:675,1021`, `awx/whole_solve.py:36`), but it is declared nowhere an install reads. `tests/README.md:113-114` documents the absence only for the test skips. Meanwhile plan-pcb-routing SKILL.md:1286-1292 and 1423-1430 say to use route_bus "on every such bus". The campaign installed 9.15.6755, the pin in `awx/modal_whole.py:34`.
- branch head 86b54a1d: unchanged. main 0523df20: same gap. Main's requirements.txt differs only in comments (an added note about imageio), route_bus.py is identical, and the skill still says "for now, use it on every such bus".
- upstream: new. Searches: "ortools", "ortools requirements", "route_bus ortools", "CP-SAT dependency", "CP-SAT", "requirements.txt", "route_bus".
- severity after verification: LOW. It cost the campaign nothing because ortools was installed. On a fresh install, though, the skill-recommended step burns its run and lays nothing without naming the cause.
- issue draft:
  title: ortools is an undeclared dependency of awx/route_bus.py (skill Step 1a); without it the bus step lays nothing and never names the missing module
  body: plan-pcb-routing Step 1a says to use `awx/route_bus.py` on every array-to-array bus. Its fanout and whole-route stages import `ortools.sat.python.cp_model` (awx/whole_ends.py:1394, awx/joint_escape.py:675, awx/whole_solve.py:36). ortools is not in requirements.txt and not in `deps_check.OPTIONAL_PACKAGES`, and no doc says to install it. Measured with ortools made unimportable: `python3 -X utf8 awx/route_bus.py wk/gp14/14_imx6ulz_4l/repro/bus_in.kicad_pcb OUT.kicad_pcb --rounds 1 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25` runs 95 s, prints `fanout exit 1` / `the whole route laid nothing (exit 2)` and exits 1. The ModuleNotFoundError appears only in `OUT.bus/U1-U2.bus/run/r1/fo.log`. 8 test_622 files self-skip for the same reason. Expected: either list ortools in requirements.txt (awx/modal_whole.py pins 9.15.6755), or have route_bus check for ortools at start and refuse with "needs ortools (pip install ortools)" before spending the run, and add it to deps_check as optional.

<!-- batch B08 -->
### H10 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - **Board 14, `final_route/s1c_caps` → `_verify/B08/h10_base.kicad_pcb`** (same args as the shipped `s2a_diff`). route_diff reports DQS0 `"outcome": "coupled"` (`coupled_terminals: false`, `escape: hybrid`). The console says `#444 seam re-ask: joint whole-connection A* replaces composed pair (score 185.0 -> 100.4)`, then `DIRECT HYBRID: coupled middle on F.Cu`.
  - In the file, route_diff added DQS0_P copper only on In2.Cu (15.18 mm) and DQS0_N copper only on B.Cu (13.61 mm). It added no F.Cu copper. Coupled length is 0.00 of 21.08 mm.
  - My own pad-to-pad Dijkstra (`B08/h10_padpath.py`) gives P 21.08 mm and N 16.48 mm, a skew of 4.60 mm. CLK0 says "coupled middle on In2.Cu", but its added copper is all on B.Cu; pad-to-pad 16.80 vs 19.77 mm, skew 2.97.
  - **Same input with `--diff-pair-intra-match` (`B08/h10_p2`)**:
    - CLK0 reports `matched, delta_mm 0.0003 (before 1.1122)`, "1 bumps added". But CLK0's copper is segment-for-segment identical to the run without the flag (P 16.588, N 19.468 mm), so the bump never reached the file. Skew is still 2.97.
    - DQS0 reports `improved 1.080 -> 0.394`. The matcher read P 12.004 < N 13.084 and lengthened P, which in the file is already the longer leg. Pad-to-pad skew went 4.60 → 5.29.
  - **Board 08** (`B08/h10_se`): `single_ended_diff_pairs: ["/CM5/DPHY0_P.D0"]`, `failed_diff_pairs: []`, exit 0, outcome `deferred` / `polarity-swap-denied`. route_diff did disclose this: the console says `Diff pairs: 12/13 routed` and `Single-ended: 1 (... polarity swap denied)`, and it hinted at `--polarity-swap-nets`. So "silent" is wrong for route_diff itself.
  - Neither `board_score.py` nor `check_complete.py` contains any diff-pair or skew component (grep), so the graders never see any of the above.
- cause:
  - `diff_pair_custody.py:183-188` sets outcome `'coupled'` from "both members have a non-SE result", never from the shipped copper.
  - `diff_pair_routing.py:3475-3561`: the #444 seam re-ask accepts per-net whole-connection routes on `_joint_score` = length + 2·vias + 3·split (`:3516-3521`). Here it swapped the composed pair for two uncoupled routes on different layers. Then `:3619/:3634` still prints the original middle layer.
  - The re-ask is not the only cause. With only it disabled (`B08/h10_noreask.py`), DQS0 still ships 0.00 mm coupled (skew 7.63) and N gets no F.Cu copper.
  - Intra-match measures result segments + stub estimates + pad-to-die (`length_matching.py:3786-3792`), not the shipped pad-to-pad path. Why the CLK0 bump (a 3-pad U2→R1→U1 pair) never reaches the file is not established.
- branch head 86b54a1d: unchanged. main 0523df20: same code; the seam re-ask is now gated by `KICAD_SEAM_REASK`, which defaults on.
- upstream: new. Related closed issues: #602 (coupled vs member audit), #766 (intra-match coverage), #444 (seam re-ask). Searches: "seam re-ask coupled", "route_diff coupled outcome uncoupled", "intra-pair matched skew", "single_ended_diff_pairs", "board_score diff pair", "hybrid escape coupled skew", "diff pair coupling grader", "route_diff in:title".
- severity after verification: HIGH
- issue draft:
  title: route_diff reports a pair "coupled" and "matched" that the written copper is not: the seam re-ask replaces the coupled middle, and an intra-match bump never reaches the file
  body: On `wk/gp14/14_imx6ulz_4l/final_route/s1c_caps.kicad_pcb`, `route_diff.py --nets '/DRAM/DRAM_DQS0_*' '/DRAM/DRAM_DQS1_*' '/DRAM/DRAM_CLK0_*' --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 1.5 1.0 --no-bga-zones` reports DQS0 outcome "coupled" and prints "coupled middle on F.Cu" after "#444 seam re-ask ... (185.0 -> 100.4)". The written copper is P on In2.Cu only and N on B.Cu only: 0 mm coupled, pad-to-pad skew 4.60 mm (21.08 vs 16.48). With `--diff-pair-intra-match`, CLK0 reports "matched, delta 0.0003", but its copper is identical to the run without the flag (skew 2.97 mm). DQS0 is meandered on the already-longer leg (4.60 → 5.29 mm). The outcome is set from result existence (`diff_pair_custody.py:183-188`), not from copper. No grader (board_score, check_complete) has a diff-pair term, so a board like this reads DONE. Expected: outcome and intra-match status computed from the shipped copper, and a graded diff-pair component.

### M27 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - The cluster's route_diff command with `--via-size 0.3 --hole-to-hole-clearance 0.25` → `_verify/B08/m27_d100.kicad_pcb`. Exit 0, 13/13 pairs routed.
  - `check_drc`: `FOUND 1`, VIA-DRILL-HOLE GND↔GND, overlap 0.040 mm, at (111.00,51.87)/(111.20,51.57). Both are new route_diff GND return vias (0.3/0.15), one belonging to DPHY0_P.D2 and one to DPHY0_P.C.
  - KiCad agrees: `hole_to_hole` error, actual 0.2096 mm vs min 0.25.
  - The site differs from the teammate's (96.8,52.47) on this input. It is the same mechanism.
- cause:
  - An instrumented run (`B08/m27_instr.py`, log `m27_instr_gndvias.txt`) shows the C pair's GND via planned at (111.2,51.5323) and settled to 51.5673.
  - The Rust router checks the site at `to_grid_dist` = floor(0.4323/0.1) = 4 cells (`diff_pair_routing.py:2386`, `routing_config.py:1018-1020`, `pose_router.rs:641-644`). That checked site is 0.417 mm from D2's GND drill, which clears the 0.40 hole-to-hole keep-out.
  - Python then places the via at the float offset 0.4323 (`diff_pair_routing.py:1286-1289`), now 0.389 mm away. `_settle_gnd_via` moves it a further 0.035 mm (`:1291-1296`).
  - The settle re-check `via_barrel_clear_of_foreign_copper` excludes the via's own net (`stub_layer_switching.py:813`) and tests copper clearance only, never drill hole-to-hole. So nothing re-checks the final site against other GND drills.
- branch head 86b54a1d: unchanged. main 0523df20: same code.
- upstream: new. Related closed issues: #1207 (its fix added the settle), #282 (P/N vias), #125 (stitching vias), #1070. Searches: "GND via hole-to-hole", "route_diff gnd via hole", "companion GND via", "gnd via drill hole", "settle_gnd_via", "gnd via grid offset".
- severity after verification: MEDIUM (check_drc and KiCad both catch it)
- issue draft:
  title: route_diff GND return vias land below min_hole_to_hole of another pair's GND via (checked on the floored grid site, placed at the float offset, settled without a drill check)
  body: Running `route_diff.py wk/gp14/08_CM5_MINIMA_3/repro/gap_diffvia_in.kicad_pcb OUT --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 --hole-to-hole-clearance 0.25 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0` exits 0. It places GND vias of DPHY0_P.D2 and DPHY0_P.C at (111.0,51.866) and (111.2,51.567), a hole gap of 0.2096 mm against 0.25 (check_drc VIA-DRILL-HOLE 0.040 mm; KiCad hole_to_hole). The Rust router validates the site at the floored grid offset (4 cells = 0.40 mm, 0.417 mm from the other drill). Python places it at 0.4323 mm and `_settle_gnd_via` moves it 0.035 mm closer. The settle re-check skips same-net vias and has no drill rule. Expected: the final placed/settled site is checked against every via drill at hole_to_hole, regardless of net.

### H21 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `kicad-cli pcb drc --refill-zones` on a B08 copy of `repro/viainpad_len` with its `.kicad_dru` gives 8 `length_out_of_range` errors for DRAM_LDQ, from 9.19 to 20.91 mm.
  - On the route_bus output (`final_route_old2/s1a_bus` with the dru) it gives 4: DQ2 10.19, DQ4 18.03, DQ5 21.26, DQ7 20.98.
  - `check_drc --clearance-margin 0.1`: `FOUND 2` (via-segment only). It prints no length check and does not mention the length rule.
  - board_score's length component grades only a spread against `tolerance_mm` (`board_score.py:884-960`).
  - `awx/route_bus.py` has no length term (no occurrence of "length").
  - `routing_common.py:741` prints "Skipping N already-routed net(s)".
- cause: `design_rules.py:107` `CONSUMED_KINDS` excludes `length`, so routing steps print "parsed, but length has no consumer in this tool yet" (`:1150-1151`). That disclosure exists only on the routing side. The graders (check_drc, board_score, and check_complete through them) say nothing about the rule.
- branch head 86b54a1d: unchanged. main 0523df20: length is still not in `CONSUMED_KINDS` (the design_rules diff only adds diff-pair rule context).
- upstream: new. #487 (closed audit) listed "per-net length target" as missing; #1237 (open) is an audit-tool umbrella; #1246 and #1248 (closed) cover spread and die-length. Searches: "length window kicad_dru", "length_out_of_range", "length has no consumer", "dru length constraint min max", "absolute length rule".
- severity after verification: HIGH (the repo graders read clean while KiCad reports 8 errors; only the routers say the rule is unconsumed)
- issue draft:
  title: A `.kicad_dru` length window (min/max) is graded by nothing: check_drc and board_score read clean while KiCad reports length_out_of_range
  body: `wk/gp14/14_imx6ulz_4l/repro/viainpad_len.kicad_dru` declares `(constraint length (min 11.5mm) (opt 13mm) (max 14.5mm))` for class DRAM_LDQ. KiCad DRC on the board reports 8 length_out_of_range errors (9.19–20.91 mm). `check_drc.py` reports 2 unrelated violations and does not mention the rule. `board_score --length-groups` grades only a spread. Routing steps print "length has no consumer in this tool yet", and route_bus has no length term. Expected: at minimum, check_drc / board_score grade (or explicitly list as ungraded) every dru length rule, so a DONE verdict cannot rest on a board KiCad fails.

### H22 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `board_score repro/viainpad_len.kicad_pcb --length-groups repro/length_groups.json --json B08/h22_score.json`: length `ran: false`, `2 of 8 member(s) have pads not joined by track copper`, `unjoined_nets: [DQ3, DQ7]`. The repro shows 2 of 8, not the 4 the cluster states.
  - `check_connected --nets DQ3 DQ7`: ALL NETS FULLY CONNECTED. KiCad measures both (DQ3 9.19 mm, DQ7 18.78 mm).
  - Geometry: U2.A3 (DQ3) has a via (0.3) centred in the F.Cu-only pad and tracks leaving on In2.Cu; U2.C8 (DQ7) is the same with tracks on B.Cu. No F.Cu track touches either pad.
  - `net_match_length` returns None in both `pin_pair` and `total` modes.
- cause: `net_queries.py:571-586`. Each disc (pad or via) creates per-layer hub nodes that join only TRACK nodes inside it on that layer. There is no via-disc-to-pad-disc join, so a via-in-pad whose tracks leave on another layer never links to its pad. The pad hub stays isolated, and `board_score.py:935-951` counts the net as unjoined.
- branch head 86b54a1d: unchanged. main 0523df20: same graph code (the main net_queries diff touches only a docstring elsewhere).
- upstream: new. It is the join test of closed #1246; #1248 is closed and different. Searches: "via in pad length unjoined", "pin_pair_path_length", "net_match_length via", "not joined by track copper", "length UNGRADED via-in-pad", "track graph via pad".
- severity after verification: MEDIUM (this is a false "unjoined", so length is UNGRADED rather than falsely passed; it blocks DONE and needed a helper)
- issue draft:
  title: net_queries track graph never joins a via-in-pad to its pad, so board_score length reads connected nets as "not joined" (UNGRADED)
  body: On `wk/gp14/14_imx6ulz_4l/repro/viainpad_len.kicad_pcb`, `board_score --length-groups repro/length_groups.json` reports DRAM_DQ3 and DRAM_DQ7 unjoined, and length ungraded. Both nets are fully connected (check_connected; KiCad measures 9.19 and 18.78 mm). Each has a via centred in its F.Cu SMD pad (U2.A3, U2.C8) with tracks leaving on In2.Cu/B.Cu. `_net_track_graph` (`net_queries.py:571-586`) joins disc hubs only to track nodes, so via and pad never meet. `net_match_length` returns None in both modes. Expected: a via whose barrel lies within a same-net pad on a layer it spans joins that pad's hub.

### H24 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `awx/route_bus.py repro/bus_in.kicad_pcb B08/h24_bus.kicad_pcb --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu ...` took 31.5 min, exit 0, `BUS U1->U2 ... lanes=43/43 ... connected=1 drc=1`.
  - The output has only `h24_bus.kicad_pcb` and `.kicad_pro`. The input had `.kicad_dru` and `.design-brief.json`.
  - kicad-cli on the output as written: `length_out_of_range 0`. With the input's dru copied beside it: 4 (10.19, 18.03, 21.26, 20.98).
  - Note: `final_route_old2` now does carry both siblings, because they were restored by hand (its `redo_commands.sh` line 11 says so).
- cause: the work boards carry the siblings (`fanned.*`, `run/r1/seq.kicad_dru`). Two steps drop them:
  - `awx/whole_route.py:1629` copies only `.kicad_pcb` and `.kicad_pro` of the best round into `run/best.*`.
  - `awx/flow_frame.py:216` `SIBLINGS = ('.kicad_pro', '.ladder.txt', '.kicad_dru')` has no `.design-brief.json` or `.kicad_prl`.
  - `route_bus.py:584-586` turns `best` into `routed.kicad_pcb`, and `:695` `copy_board(routed_pcb, out)` copies only what `routed.*` has, which is `.kicad_pro`.
- branch head 86b54a1d: unchanged (no awx diff). main 0523df20: same lines in `whole_route.py` (1630) and `flow_frame.py` (216).
- upstream: new, the same class as #1190 and #1286 (both closed). The #1190 fix (b248685f, on the pin) covers `fix_project_for_output`, which this final write does not use. Searches: "route_bus kicad_dru", "route bus", "awx", "bus sibling kicad_dru", "sibling kicad_dru not written", "SIBLING_EXTS".
- severity after verification: HIGH (KiCad's grade of the output silently lost 4 errors, and every later step runs without the board's rules)
- issue draft:
  title: route_bus writes OUT with .kicad_pro only: whole_route's best-round copy and flow_frame.SIBLINGS drop .kicad_dru and .design-brief.json
  body: `awx/route_bus.py wk/gp14/14_imx6ulz_4l/repro/bus_in.kicad_pcb OUT --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25` (exit 0) leaves OUT with `.kicad_pro` only, although the input has `.kicad_dru` and `.design-brief.json`. KiCad DRC on OUT reports 0 length_out_of_range; with the input's dru restored it reports 4. `whole_route.py:1629` copies only pcb+pro into `best.*`. `flow_frame.SIBLINGS` lacks `.design-brief.json` and `.kicad_prl`. `route_bus.py:695` copies `routed.*`'s siblings. Expected: OUT carries every `copy_board.SIBLING_EXTS` member of the input.

### M34 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `check_reachability --pad U2.F1` gives `VERDICT CAGED for any track width` on `repro/bus_vmem_caged`.
  - The stage split shows route_bus's own output does the caging. `repro/bus_in` → PASSABLE; my fresh route_bus output `B08/h24_bus` → CAGED. Likewise `final_route_old2/s1_pour` → PASSABLE and `s1a_bus` → CAGED.
  - After route_bus, U2.F1 has only a 0.43 mm F.Cu stub with no via, and the board has 755 locked segments.
  - `check_weird` on the fresh output: `VMEM (In1.Cu) at (66.775, 104.600): free end, dangling segment 2.025mm`. The 4.4 mm In1.Cu VMEM segment at x=88.4 is already present after route_bus.
  - route_bus's summary says only `connected=1 drc=1 (bus 0, board 0 vs 0 in)`.
- What does not hold:
  - The "serves every ball" line (`fo.log`) is about the bus's own berth plan, not about U2.F1.
  - VMEM copper on In1.Cu follows the caller's `--bus ...:F.Cu,B.Cu,In1.Cu,In2.Cu`. That is what the skill prescribes ("name EVERY copper layer, the planes' layers included" — SKILL.md:1458), so routing on that layer is as requested. Only the dangling tail is a defect.
- cause: not established in code. The defect contradicts the skill's own contract, "Every ball of a bus array must leave the step served" (SKILL.md:1475): U2.F1 got a dead-end stub, then the locked lanes walled it in.
- branch head 86b54a1d: unchanged (no awx diff). main 0523df20: route_bus.py is on main with the same code.
- upstream: new; nothing filed on route_bus. #677 (open) is the analogous problem for diff pairs. Searches: "route_bus caged", "route_bus", "route bus", "bus lanes wall in ball", "caged pad bus", "bus fanout plane layer tail", "joint fanout dangling".
- severity after verification: MEDIUM
- issue draft:
  title: route_bus (joint) cages a non-bus ball of its array: U2.F1 (VMEM) PASSABLE before the step, CAGED for any width after, summary silent
  body: On `wk/gp14/14_imx6ulz_4l/repro/bus_in.kicad_pcb`, `check_reachability --pad U2.F1` says PASSABLE at 0.13 mm. After `awx/route_bus.py bus_in OUT --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25` (exit 0, "connected=1 drc=1"), it says CAGED for any track width. U2.F1 carries only a 0.43 mm F.Cu stub with no via, walled in by locked bus lanes that later steps may not rip, so VMEM ships open at (73.60,105.40). The output also carries a dangling 2.025 mm VMEM segment on In1.Cu at (66.775,104.600). Expected: the joint fanout leaves every non-bus ball of the array reachable (or reports the ones it cages), and lays no dead-end stubs.

All outputs are in `wk/gp14/_verify/B08/`.

<!-- batch B09 -->
### H13 -- VERDICT: CONFIRMED
- repro at 8328f157: `python3 -X utf8 py_placer/place_pose.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb wk/gp14/_verify/B09/h13_pile_rot.kicad_pcb rotate U4 90 --force`. U4 goes from `(at 125.690300 123.359000)` to `(at 125.690300 123.359000 90)`, but pad 1 stays `(pad "1" smd rect locked (at -2.7 -1.905) ...)` with no angle added, and the same holds for pads 2 and 3. `check_pads --component U4` gives OK on the pile and `FAILED: 6 overlapping different-net pad pair(s)` on the rotated board. The given pile is already damaged:
  - `check_pads pile.kicad_pcb --component U1` gives `FAILED: 164` (the cluster said 126). The whole pile gives 175; `human.kicad_pcb` gives OK.
  - `wk/gp14/_staging/pile_pad_check.py human pile` reports `87 footprints; 54 with pads turned against the body` (the cluster said 38 of 84). The repro pile is byte-identical to `12_steppenprobe/steppenprobe.kicad_pcb`.
  - All 312 pads of the KiCad 6 source (`version 20211014`) carry `locked` before `(at`.
  - The pile was written by the repo's own `.claude/skills/plan-pcb-placement/scripts/make_unplaced.py` at the pin (stage.log `== 0 worktree 8328f157`; it calls `write_placed_output` at line 259). So the damage in the given pile is this same defect, not a staging mistake.
  - Calling `_rotate_pad_angles(s, 90)` directly: `(pad "1" smd rect (at 1 2))` becomes `(at 1 2 90)`. `(pad "1" smd rect locked (at 1 2))` is unchanged. An unquoted KiCad-5 spelling `(pad 1 smd rect (at 1 2))` is also unchanged (synthetic string only). `(locked yes)` written after `(at` is handled.
- cause: `py_placer/placement/writer.py:260-263`. The pattern `\(pad\s+"[^"]*"\s+\S+\s+\S+\s*\n?\s*\(at` allows exactly two tokens (type, shape) between the quoted pad name and `(at`. A pad with `locked` there never matches, so `writer.py:1162` (a rotation with no side change) turns the footprint but leaves every pad angle where it was.
- branch head 86b54a1d: unchanged (writer.py has no diff); main 0523df20: same code (`_rotate_pad_angles` at main:251-266), and main's `.claude/skills/pcb-free-agent/scripts/make_unplaced.py` uses the same writer.
- upstream: new; searches: "pad locked rotate", "_rotate_pad_angles", "pad angle rotate writer", "make_unplaced pad angle", "pads turned footprint rotation", "locked pad", "pad angle", "pad rotation", "check_pads overlapping". The nearest are #1163 and #1214 (both closed, about other footprint children).
- severity after verification: HIGH
- issue draft:
  title: Placement writer never rotates a pad written `(pad "N" type shape locked (at ...))` (KiCad 6), so every rotate/pile write turns pads against their body
  body: `writer._rotate_pad_angles` (writer.py:260) matches only `(pad "N" <type> <shape> (at ...)`. KiCad 6 boards write `locked` as a third token, so on those pads the absolute angle is not changed when the footprint rotates. On steppenprobe, where all 312 pads carry the token, `make_unplaced.py` produced a pile with 54 of 87 footprints whose pads are turned against their bodies: `check_pads` gives 175 overlapping different-net pairs on the pile, 164 of them on U1, and 0 on the source. Repro: `python3 -X utf8 py_placer/place_pose.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb /tmp/rot.kicad_pcb rotate U4 90 --force`. The footprint becomes `(at ... 90)`, pad 1 stays `(at -2.7 -1.905)`, and `check_pads --component U4` goes from OK to 6 overlapping pairs. Expected: every pad's angle advances by the rotation whatever tokens come before `(at`. Matching on the pad node rather than a fixed token count would also cover unquoted pad numbers.

### H17 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster command with output `wk/gp14/_verify/B09/h17_out.kicad_pcb` (68 s, exit 0).
  - The output has `+3.3V segs 0 vias 0`, and `check_connected` reports `Unrouted nets (1): +3.3V (17 pads)`.
  - `JSON_SUMMARY_MIN.pad_pairs_open = {"count": 1, "nets": ["/U7D-"]}`, while `failed: 2` and `multipoint_deficit: 17` are correct.
  - `--json-out` says `pad_pairs_connected 209 / pad_pairs_total 210`, but +3.3V alone has 16 pads open.
  - The log shows `Pad D4.1 ... blocked by +3.3V - ripping`, then `+3.3V reconnected in place`; the same happens at J7.4. Then `Pad D3.1 ... blocked by +3.3V - ripping ... (restored 3/3 ripped net(s)) FAILED`.
  - No line says that +3.3V's copper was removed. The improvement gate does not list it, because +3.3V had no copper on the input.
  - An instrumented run (`_verify/B09/h17_probe.py`, in-memory wrapper only) printed `tap D3.1: +3.3V board/write-list segs before=(124, 124) after=(124, 0) success=False`. The probe's output also ships 0 segments.
- cause:
  - `py_router/repair_planes.py:469-478` purges a ripped blocker's entries from the write list. That purge came in with a9996562 (#517 arm 3).
  - When the tap then fails, the restore at `repair_planes.py:577-639` puts the pieces back into `pcb_data` only, never into `write_lists`. The success-path restore at `:542-543` does the same.
  - +3.3V also stays in `inplace_reconnected_ids` (`:1482-1485`), so the writer strips its main-pass copper, and because the restore was counted, the net is never queued for reconnect. The model holds 124 segments; the file gets none.
  - Reporting half: `pad_pairs_open` is a per-summary snapshot (`route.py:5245-5300`, "Computed before the final reconciliation"). `_apply_regrade` (`route_summary.py:631-643`) keeps only entries some summary emitted, so a net broken later never appears there, and `pad_pairs_connected` is derived from that incomplete list.
- branch head 86b54a1d: unchanged (no py_router diff); main 0523df20: same code (only film-capture hooks were added around the rip and restore).
- upstream: new. It is the "mirror direction" of closed #508 (copper in `pcb_data` but not in the write list), introduced after #508 closed by a9996562. Same family as closed #600 and #1156. searches: "plane repair ripped net no copper", "write list restore ripped", "immediate reconnect ripped", "restored ripped net output", "pad_pairs_open stale", "finalize rips routed net".
- severity after verification: HIGH
- issue draft:
  title: Plane repair: a failed tap restores a re-ripped net into pcb_data but not into the write list, so the net ships with zero copper (StickHub +3.3V, 17 pads)
  body: In route.py's in-run GND finalize, +3.3V is ripped for D4.1 and J7.4 and reconnected in place each time, which adds 124 segments to the write list. It is then ripped again for D3.1. `_tap_pad_with_ripup` purges its write-list copper at the rip (repair_planes.py:469-478). The tap fails, and the restore (:577-639) extends pcb_data only. Instrumented: at D3.1 the board/write-list segment counts go from 124/124 to 124/0. Because +3.3V is in `inplace_reconnected_ids`, its main-pass copper is stripped too, so the file has 0 segments and 0 vias on a 17-pad rail. No log line says routed copper was removed. `pad_pairs_open` / `pad_pairs_connected` (209/210) omit the net; `failed` and `multipoint_deficit` 17 are correct. Repro (~70 s): the route.py command in FINDINGS_CLUSTERED H17 on `wk/gp14/09_StickHub/repro/g1_step2.kicad_pcb`, then `check_connected.py` on the output. Expected: a restore re-adds the restored pieces to the write list (board == file), or leaves the net queued for reconnect; `pad_pairs_open` is regraded on the written board.

### H18 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster command on `wk/gp14/10_glasgow_revC/repro/gap6_s2_c.kicad_pcb` with output `wk/gp14/_verify/B09/h18_iterC1.kicad_pcb` (3 min 32 s).
  - The gate line is identical to the teammate's: `IMPROVEMENT GATE: this run broke 9 previously-connected net(s) [+1V2, /D1, ...], worsened 0, connected 9 -- ACCEPTED` (disconnected pads 25 -> 23).
  - `check_drc --clearance-margin 0.1` (graded at 0.1 from the .kicad_pro) gives `NO DRC VIOLATIONS FOUND` on the input and `FOUND 17` on the output: 4 segment-segment (3 in contact), 9 via-segment (5 in contact), 1 via-via (in contact), 3 via-drill-hole (3 in contact).
  - Every listed item involves /RD (against /D0, /IO_Banks/QB4, and a GND via) around x 70-74, y 91-97.
- cause: the gate part is accurate as stated. `improvement_gate.py:25-36` measures only per-net union-find connectivity and disconnected-pad counts; DRC is not an input. The shorts themselves have a different root cause, re-diagnosed here:
  - /RD's output copper (15 segments + 3 vias) is identical to its input copper.
  - /D0 got a new path, (71.1,91.3)->(71.1,94.0)->(73.6,96.5)->(81.7,96.5), replacing (70.8,91.6)->(70.8,93.7)->(73.0,95.9)->(74.2,95.9)->(74.8,96.5). The new path runs 0.025 mm from /RD at y=96.525.
  - An instrumented run (`_verify/B09/h18_probe.py`) shows the three new /D0 segments being laid by `cleanup_pipeline.smooth_octolinear_chains` while the engine's board held **0** /RD segments. The log also says, at line 2565, "ZERO copper (... /RD ...)", after line 2117 "#134 last resort: /RD ... restored 15 segment(s)".
  - A new GND via at (71.0,95.0) is likewise placed on /RD's copper.
  - So /RD is absent from the engine's model during the late passes but present in the shipped file. This is the same mechanism the comment at `route.py:4150-4175` describes (SRAM_A4) and the strip-loop closure was meant to stop. The exact point where /RD's copper re-enters the file is not established.
- branch head 86b54a1d: unchanged; main 0523df20: same gate code (improvement_gate.py has no diff and its route.py has no DRC term in the gate).
- upstream: new (the gate has no DRC axis). The shorts are a new instance of closed #508's pcb_data/file divergence class. #1114 and #1173 (closed) cover other gate gaps. searches: "improvement gate DRC", "improvement gate shorts", "restore shorts smoothing", "octolinear smoothing short", "#134 last resort restored short", "route.py ships shorts".
- severity after verification: HIGH
- issue draft:
  title: route.py ships new shorts (0 -> 17 DRC) and its improvement gate accepts them: /RD's input copper reaches the file while the engine's board has none
  body: Repro (~3.5 min): the H18 command in FINDINGS_CLUSTERED on `wk/gp14/10_glasgow_revC/repro/gap6_s2_c.kicad_pcb`, then `check_drc.py <out> --clearance-margin 0.1`. The input grades clean; the output has 17 violations, 12 of them in contact, all on /RD. /RD ships its input copper unchanged. /D0 was rewritten by octolinear smoothing through /RD's corridor, and a GND via was placed at (71.0,95.0) on it. Instrumented: smoothing ran with 0 /RD segments on the board model, and the log reports /RD at "ZERO copper" after it said "restored 15 segment(s)". The improvement gate prints "broke 9 ... connected 9 -- ACCEPTED" because it measures connectivity only. Expected: the engine's board and the written file agree on /RD (no input copper is emitted for a net the model no longer carries). The gate should also reject a run that adds different-net contacts.

### H19 -- VERDICT: CONFIRMED
- repro at 8328f157: I ran the cluster route command (power-net list from #6) on `wk/gp14/10_glasgow_revC/repro/gap7_s2a_c.kicad_pcb` with output `wk/gp14/_verify/B09/h19_s2_c.kicad_pcb` (8 min 14 s).
  - Same-net segments touching the ball, counted with `_verify/B09/h19_ballcopper.py`, input -> output: C9 1->0, B9 1->0, E8 1->0, J5 1->0, D7 1->1.
  - Whole-net copper: Net-(U30A-IOT_172) goes from 3 segments + 1 via to 0 segments + 1 via; /IO_Banks/DA6 from 7 segments to 0 segments + 1 via.
  - The output is identical to the teammate's `gap6_s2_c` at these balls.
  - "fanout-dropped ball ... Re-run the fanout" hints are printed for U30.C9, D7, E8 and J5. D7 ships with its escape copper anyway.
  - `--json-out` has `terminal_restores["Net-(U30A-IOT_172)"] = "full"` although that net ships 0 segments.
- cause: re-diagnosed. route.py does restore the escapes in its model: the log shows `RIP-RESTORE (#468) ... kept only its escape stub`, `#622 ... restored WHOLE`, and `#134 last resort: Net-(U30A-IOT_172) ... restored 17 segment(s) + 5 via(s)`.
  - An instrumented run (`_verify/B09/h19_probe.py`) shows IOT_172 at 13 segments + 5 vias on the model after its final "original copper restored". It drops to 0/0 right after "Stripped 119 stale input segment(s) of ripped/re-routed nets not on the final board (#220)" / "Strip loop closed". That is the end-of-run stale-input strip at `route.py:4205-4210`, which removes the restored original objects from pcb_data and the file. Why they land in the stale set is not traced.
  - DA6 goes 20 -> 9 -> 0 segments through the same strip and the late orphan sweep (#659).
  - The hint (`routing_diagnostics.py:639-699`, via `entombed_bare_pads`) reads the live board in the middle of the run. For /IO_Banks/U5 it fired at probe-log line 13999, after this run's own rip (13400) and before the #134 restore (14147). It therefore cannot tell a ball the fanout never escaped from one whose escape this run ripped.
- branch head 86b54a1d: unchanged; main 0523df20: same hint code (`fanout_dropped_ball_hint` at main:639); route.py differs on main and I did not check the strip there.
- upstream: regression of closed #1156. Its fix 87df3e27 is on the pin and promised the #468 terminal restore "whole ... else the escape stub"; the restore runs but its copper is stripped before writing. The hint misattribution is new. Related closed issues: #508, #666, #652. searches: "fanout-dropped ball hint ripped", "escape stub stripped stale input", "stale input strip restored copper", "original copper restored ships zero copper", "dog-bone escape ripped".
- severity after verification: HIGH
- issue draft:
  title: route.py's terminal restore of a ripped BGA escape is erased by the end-of-run stale-input strip, and the hint then blames the fanout (regression of #1156)
  body: On glasgow chain C (`wk/gp14/10_glasgow_revC/repro/gap7_s2a_c.kicad_pcb`, the H19 command, ~8 min), U30.C9, B9 and E8 each have 1 escape segment on the input and 0 on the output. Net-(U30A-IOT_172) goes from 3 segments to 0 segments, though the log says "#468 ... kept only its escape stub" and "#134 last resort ... restored 17 segment(s) + 5 via(s)", and `terminal_restores` reports it "full". Instrumented: the model holds 13 segments + 5 vias for that net until the stale-input strip (route.py:4205-4210, "Stripped N stale input segment(s) ... (#220)"), then 0. `fanout_dropped_ball_hint` fires during the reroute, while the net is ripped by this same run, and says "Re-run the fanout", although the fanout escaped every ball. Expected: restored original copper is not classified stale; the hint does not fire for a ball whose escape copper this run removed (or it says the run removed it); `terminal_restores` reflects the written board.

### M26 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `board_score g4_rail_missing --quiet` gives `BLOCKING=1 (unrouted=1 broken=0 ...) vias=117 copper_mm=704.04`.
  - `board_score g4_one_pad --quiet` gives `BLOCKING=1 (unrouted=0 broken=1 ...) vias=132 copper_mm=773.42`.
  - `check_connected g4_rail_missing` gives `Unrouted nets (1): +3.3V (17 pads)`.
  - The score JSON's `unrouted` entry carries only net names, no pad count.
- cause:
  - The part that holds is the skill: `.claude/skills/plan-pcb-placement/SKILL.md:337` and `:368` ("Keep the best by blocking, then vias, copper_mm, segments") apply the via/copper tie-break between boards that both have open nets. That picks the rail-less board, whose fewer vias and less copper are the missing rail.
  - The part that does not hold: board_score's tie is its documented contract. `board_score.py:29-35` counts nets in `blocking`, and `quality ... # only compared once blocking == 0`.
  - board_score also gives no pad-deficit field for unrouted nets that could break such a tie.
- branch head 86b54a1d: unchanged rule (SKILL.md:667 "Keep the best by blocking, then vias, copper_mm, segments"); main 0523df20: differs. pcb-free-agent orders only DONE boards ("better, once DONE") and has no via tie-break below DONE. board_score's contract is the same.
- upstream: new; searches: "board_score blocking tie", "blocking unrouted broken weight", "pad deficit board_score", "tie-break vias missing rail", "quick_score blocking tie". The nearest, #675 and #1191, are different.
- severity after verification: MEDIUM
- issue draft:
  title: plan-pcb-placement ranks boards with open nets by vias/copper, so a board missing a whole 17-pad rail beats one with a single stranded pad
  body: The skill says "Keep the best by blocking, then vias, copper_mm, segments" (SKILL.md:337, :368; branch :667). board_score's own contract compares quality only once blocking is 0 (board_score.py:29-35). On StickHub, `board_score` gives `g4_rail_missing` BLOCKING=1 (unrouted +3.3V, 17 pads) with vias 117 and copper 704.04, and `g4_one_pad` BLOCKING=1 (broken, 1 pad) with vias 132 and copper 773.42. The rule picks the rail-less board because its missing copper reads as quality. Repro: `board_score.py wk/gp14/09_StickHub/repro/g4_{rail_missing,one_pad}.kicad_pcb --quiet`. Expected: below blocking 0, break ties by open pads (pad deficit, which board_score should publish for unrouted nets too), never by vias or copper.

### M33 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `check_reachability g4_one_pad --pad U1.37 --track 0.127` gives `BOTTLENECK none`, `VERDICT CAGED for any track width`, exit 1 (clearance 0.127).
  - `check_reachability g6_placed ... --pad U1.37 --track 0.127` gives `PASSABLE (margin +984.5 um)` (clearance 0.15).
  - To isolate the cause, I stripped only the copper from the routed board (`copy_board` + `tests/stress/strip_copper_only.py` -> `_verify/B09/m33_one_pad_stripped.kicad_pcb`). Same placement, same 0.127 clearance: `PASSABLE (margin +1030.5 um)`. The routed copper alone produces CAGED.
- cause:
  - `py_placer/placement/reachability.py:221-227` rasterises every foreign segment and via as a wall, so on a routed board other nets' rippable copper counts as geometry.
  - The tool's own text (`check_reachability.py:14-15`, "CAGED -- ... This one IS geometry, and the fix is placement") gives no copper caveat and the output does not disclose it. Only an internal docstring (`:60`) mentions "CAGED on the copper-free board".
  - The skills route CAGED straight to re-placement: plan-pcb-placement SKILL.md:417 and :453, and diagnose-routing-failures SKILL.md:142.
- branch head 86b54a1d: unchanged (tool unchanged; skill :717 and :751 same wording); main 0523df20: same. check_reachability.py has no diff, and main's pcb-free-agent :305 and :377 and diagnose-routing-failures :120 carry the same text.
- upstream: new; searches: "check_reachability CAGED", "CAGED routed board", "reachability copper-free", "CAGED congestion", "reachability/CAGED/PASSABLE in:title,body". Closed #1040 only notes PASSABLE on a copper-free board.
- severity after verification: MEDIUM
- issue draft:
  title: check_reachability reports routed copper as geometry: CAGED on a routed board, PASSABLE on the same placement with the copper stripped
  body: On StickHub, `check_reachability.py wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --pad U1.37 --track 0.127` says "CAGED for any track width" (exit 1). The same board with only its copper stripped, at the same 0.127 clearance, says PASSABLE +1030.5 um. reachability.py:221-227 walls every foreign segment and via. The tool says CAGED "IS geometry, and the fix is placement", and plan-pcb-placement (§4, §5 rule 4) and diagnose-routing-failures route CAGED to re-placement, so a congestion failure sends the run back to placement. Expected: the tool either measures without rippable routed copper (or with a flag to), or labels a verdict taken on a board with copper as congestion-inclusive. The skills should say to measure CAGED on the copper-free placement.

The scratch inputs and outputs are under `wk/gp14/_verify/B09/`:
- route logs: `h17_out.log`, `h18_iterC1.log`, `h19_s2_c.log`
- probe scripts and their logs: `h17_probe.py`, `h18_probe.py`, `h19_probe.py`, and `*_probe.log`
- `h19_ballcopper.py`, `h18_drc_*.txt`, and the output boards

<!-- batch B10 -->
### H23 -- VERDICT: CONFIRMED
- repro at 8328f157: `check_drc fanout_over_tracks.kicad_pcb --clearance-margin 0.1` gives **64**. The cluster's bga_fanout command, run with `--layers F.Cu In1.Cu In2.Cu B.Cu` written out (under zsh an unquoted `$L` reaches the tool as one argument), gives `JSON_SUMMARY requested 41, escaped 41, failed 0`. The same check on the output gives **98**. The 34 new violations are 29 SEGMENT-SEGMENT (22 in contact), 1 SEGMENT-CROSSING, 1 VIA-SEGMENT and 3 PAD-VIA. All but the 3 PAD-VIA are against one existing `/DRAM/DRAM_DQ5` F.Cu segment, (79.90,109.00)-(68.75,109.00). One of them is a `/DRAM/DRAM_DQS0_N` via at (69.20,109.00) sitting on that track (overlap 0.300 mm), which is a short. The only disclosure is the JSON `drc_grazes.total 178`, a whole-board count rather than a delta. **Control** (outputs `wk/gp14/_verify/B10/h23_*`): I swapped only that segment's start and end, so the geometry is identical. The fanout then reports `failed 1, unescaped_nets ["VMEM"]` and DRC goes 64 -> **67** (3 PAD-VIA only, no shorts).
- cause (re-diagnosed): the cluster blames `find_existing_fanouts`, but this dogbone/underpad path never calls it. The real cause is `py_router/bga_fanout/underpad.py:1129`, `if not (bounds[0] <= s.start_x <= bounds[2] and bounds[1] <= s.start_y <= bounds[3]): continue`. It tests only a segment's START point against the occupancy window. A foreign track that enters U2's ball field from outside (start x=79.9, window max ≈75.0) is never stamped, so escapes and vias are laid on it.
- branch head 86b54a1d: unchanged (no diff under `py_router/bga_fanout/`). main 0523df20: same code (same line, 1129).
- upstream: new. #1189 (closed, exit cell vs a foreign via) and #567 (closed) are related but are different mechanisms. Searches: "bga_fanout check-for-previous existing tracks", "fanout existing track obstacle", "underpad segment bounds start", "dogbone existing copper short", "fanout over existing routed track", "bga_fanout foreign net track short", "underpad occupancy segment", "escape grid segment outside window", "dog-bone foreign track".
- severity after verification: HIGH
- issue draft:
  title: bga_fanout under-pad/dogbone: an existing track whose start point lies outside the escape window is not stamped, so escapes and vias are laid on it while the run reports failed 0
  body: `underpad.py:1129` filters `pcb_data.segments` into the occupancy grid by the segment's start point only. A foreign track that runs into the ball field from outside the window is invisible to the escape search. On `wk/gp14/14_imx6ulz_4l/repro/fanout_over_tracks.kicad_pcb` (lane 0 already routed through U2), `bga_fanout.py --component U2 --nets '*' '!GND' '!+3V3' --check-for-previous --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 1.5 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 --track-width 0.1 --clearance 0.1 --diff-pairs '/DRAM/DRAM_DQS0_*' '/DRAM/DRAM_DQS1_*' '/DRAM/DRAM_CLK0_*' --diff-pair-gap 0.1` reports escaped 41/41, failed 0. check_drc (`--clearance-margin 0.1`) goes 64 -> 98. Most of the new violations are VMEM escapes crossing `/DRAM/DRAM_DQ5`'s F.Cu segment (79.9,109)-(68.75,109), plus a DQS0_N via centred on that track at (69.20,109.00), which is a short. Reversing that one segment's start and end (same geometry) gives 64 -> 67 and an honest `failed 1 (VMEM)`. Expected: test the segment's extent (bbox intersection or clipping) against the window, so foreign copper crossing the field is an obstacle whatever its direction.

### M17 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: the cluster's qfn_fanout command on `12_steppenprobe/repro/v3_step1.kicad_pcb` (output `B10/m17_v3_step1b_out.kicad_pcb`) reports escaped 31/31, drc_grazes 0. It emits the +1V8 stub (118.0538,77.9925)->(116.3,79.8). C11 pad 1 (+1V8) spans x 116.573..117.448 and y 79.443..80.393. The stub clips its corner and ends 0.273 mm past the pad edge, between C11's two pads. On the teammate's routed board `v3_step4b.kicad_pcb`, `check_weird` gives `dangling-end: net +1V8 at (116.300, 79.800): half-segment tail dangling 1.203mm past body anchor at (117.138, 78.937)`, so the tail survives routing. Board 06: `check_weird v2_qfn_plane_stubs.kicad_pcb` gives `dangling-end: 2`, including `GND (F.Cu) at (143.300, 111.600)`, a stub on a poured net.
- cause: qfn_fanout's stub geometry (`qfn_fanout/geometry.py:14-140`) is blind to same-net copper by design. The obstacle map excludes all of the part's nets (`qfn_fanout/__init__.py:1407-1430`), and nothing truncates a stub at a same-net pad it reaches. route.py's cleanup runs with `keep_input_copper` (`cleanup_pipeline.py:460-498`), so the fanout tail is never trimmed. Skill half: the generic workflow Step 1b (`SKILL.md:1294`) does say to exclude plane nets for "Fanout". Only the QFN example (`SKILL.md:2367-2374`) omits `--nets`. So 06 is a skill inconsistency, not a missing rule.
- branch head 86b54a1d: unchanged (no diff in qfn_fanout or SKILL.md). main 0523df20: same stub logic (`geometry.py` identical; `__init__.py` differs only in help strings).
- upstream: new (related: #162 open, same-net redundant copper producers; #601 and #84 closed are route.py producers). Searches: "qfn_fanout stub same-net pad", "qfn_fanout stub dangling", "fanout stub tail dangling", "qfn_fanout plane nets", "stub past pad", "qfn_fanout nets skill".
- severity after verification: MEDIUM
- issue draft:
  title: qfn_fanout's stub escape crosses a same-net pad and ends past it; the tail ships as dangling copper that route.py keeps
  body: On `wk/gp14/12_steppenprobe/repro/v3_step1.kicad_pcb`, `qfn_fanout.py --component U1 --nets '*' '!GND' '!+3V3' --clearance 0.15 --track-width 0.15 --escalation board --fab-tier standard` lays U1.64's +1V8 stub (118.054,77.993)->(116.300,79.800). It clips C11 pad 1 (+1V8, x 116.573..117.448) and ends 0.273 mm beyond it. escaped 31/31, drc_grazes 0. After routing (`v3_step4b.kicad_pcb`), check_weird reports a 1.203 mm dangling tail at (116.300,79.800), and check_complete refuses DONE. route.py keeps input copper, so its dangle trim never touches it. Expected: end (or skip) a stub once it reaches same-net copper, and have the skill's QFN example carry the plane-net exclusion `--nets '*' '!GND' ...` that Step 1b states (board 06: stubs on GND/+3V3 pins dangle after the pour weld).

### M28 -- VERDICT: CONFIRMED
- repro at 8328f157: the cluster command on `08_CM5_MINIMA_3/repro/gap_fanout_in.kicad_pcb`, Module302: `requested 70, escaped 70, failed 0`. **33 of the 70 new vias** are on nets with one pad board-wide (`/CM5/DPHY1_P.*`, HDMI1, USB3, SD...). Module301, same flags: `requested 66, escaped 59, failed 7`. **24 of its 61 new vias** are on single-pad nets, and 6 of the 7 failures are single-pad nets (SD_DAT0-3, SYNC_OUT, GPIO26; MISO_GPIO19 has 2 pads). The cluster said "failed 5"; I measured 7.
- cause: `py_router/qfn_fanout/__init__.py:1292-1298` skips only net 0 and names starting `unconnected-`. bga_fanout skips board-wide single-pad nets via `single_pad_net_ids` (`bga_fanout/__init__.py:1969`, #122, reported as `skipped_nc`). qfn_fanout has no equivalent. The skill prescribes this command for CM4/CM5 connectors (`SKILL.md:243-244`).
- branch head 86b54a1d: unchanged. main 0523df20: same code (line 1297).
- upstream: new (#1195 closed is a different qfn_fanout issue; #110 and #669 are not this). Searches: "qfn_fanout single-pad nets", "qfn_fanout no-connect", "fanout single pad net via", "qfn_fanout NC pins".
- severity after verification: MEDIUM
- issue draft:
  title: qfn_fanout escapes single-pad (no-connect) nets that bga_fanout skips (#122), leaving useless vias that block routing
  body: `qfn_fanout.py wk/gp14/08_CM5_MINIMA_3/repro/gap_fanout_in.kicad_pcb --component Module302 --nets '*' '!GND' '!+5V' --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1` reports escaped 70/70. 33 of its 70 new vias are on nets with a single pad on the whole board (unused DPHY1/HDMI1/USB3/SD pins). On Module301, 24 of 61 new vias are on single-pad nets, and 6 of its 7 failures are single-pad nets. qfn_fanout filters only net 0 and `unconnected-*` (`qfn_fanout/__init__.py:1292-1298`), while bga_fanout drops `single_pad_net_ids` and reports `skipped_nc`. Expected: the same NC skip and disclosure in qfn_fanout.

### L11 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: I re-ran both arms from `09_StickHub/repro/g7_s0_poured.kicad_pcb` with the teammate's chain (cap pass omitted: it was a recorded no-op, "No vias on the board"). Arm A: route_diff `--quick 2` -> route.py `--quick 2` -> quick_score gives **blocking 25, vias 70, copper 612.94**. Arm B adds `qfn_fanout --component U1 --nets '*' '!GND' --width 0.15 --clearance 0.15` first (escaped 34/34) and gives **blocking 30, vias 77, copper 636.13**. This matches the teammate exactly (outputs `B10/l11_*`).
- cause: U1 (LQFP-48, 0.5 mm) is selected by name (`'QFP'`, `SKILL.md:165-173`) and by the pitch predicate (`:208`). The skill's own benefit check, rule 3 (`:233`), says a perimeter at <=0.65 mm with many pads "genuinely helps". So the skill as written keeps the fanout, which hurt on this board. The confirmed part: selection plus a deterministic harm on this one placement. The part that does not hold: one board and one seed, in quick mode, cannot show the rule is wrong in general (CLAUDE.md requires a corpus A/B for a default change).
- branch head 86b54a1d: unchanged. main 0523df20: same text (`:208`, `:233`).
- upstream: new (related: #97 closed, #95 closed). Searches: "LQFP fanout", "fanout benefit perimeter QFP", "qfn_fanout hurts routing", "fanout predicate skill".
- severity after verification: LOW
- issue draft:
  title: plan-pcb-routing: the fanout benefit check says a <=0.65 mm perimeter part "genuinely" benefits; on one LQFP-48 the fanout made the judged route worse
  body: On `wk/gp14/09_StickHub/repro/g7_s0_poured.kicad_pcb`, U1 (LQFP-48, 0.5 mm) passes both the Step 3 predicate and benefit rule 3. The judged chain (route_diff + route.py `--quick 2`, quick_score) gives blocking 25 / 70 vias without `qfn_fanout --component U1 --nets '*' '!GND' --width 0.15 --clearance 0.15` and 30 / 77 with it. This is one board, so it is not evidence against the rule in general. Expected: soften rule 3 to "candidate; A/B the judged route with and without", or measure the rule on the corpus.

### M07 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: I replayed board 04's step4 (`route.py opt/sweep/s2_v200/step3.kicad_pcb --nets '*' ... --via-cost 200`) into `B10/m07_step4.*`. It prints `GND: (152.05,114.91)<->(151.15,114.93) FAILED (exact-fill strap unroutable)`. The stuck-cell report says `Blocking obstacles: Net-(IC4B-IN-)(1 track), Net-(IC2B-OUT)(1 track)`, yet the hint says `Retry with --rip-existing-nets 'Net-(IC5A-IN-)'`. From that board, four retries:
  - **hint as written** (`--nets GND --rip-existing-nets 'Net-(IC5A-IN-)'`): the rip **does happen** (`PRE-EXISTING rip: 'Net-(IC5A-IN-)' removed`), the strap still fails on `Static blockers: pre-existing tracks: Net-(IC4B-IN-)`, and the net is restored. It is not a no-op.
  - **teammate's form** (that net also in `--nets`): identical, plus the documented #515 warning.
  - **`--force-reroute`**: reroutes IC5A-IN-, GND still fails, and the hint again names IC5A-IN-.
  - **ripping the nets the stuck-cell report names** (`--rip-existing-nets 'Net-(IC4B-IN-)' 'Net-(IC2B-OUT)'`): `RETRY SUCCESS`, IC4B-IN- rerouted, and a follow-up finalize oracle says "KiCad reports all processed nets complete". check_connected still lists a separate GND zone<->zone item at (199.46,154.66), present before and after; that was not chased.
- cause (re-diagnosed): the "no-op on a connected net" part is documented behaviour (#515 warning; boards 03, 11 and 12 used the flag on a net with no blocking role, where `--force-reroute` is the documented path). The real defect is that `preexisting_blocker_hint` (`py_router/routing_diagnostics.py:451`, 1 mm ring at `:490-499`) anchors on `get_net_endpoints` (GND's derived pads at (132.65,79.9) and (108.2,85.8)), not on the #572 forced oracle-link endpoints the search used. Measured: IC5A-IN- copper is 0.200 mm from a derived anchor but 29.9 mm from the strap. IC4B-IN- is 0.451 mm from the strap.
- branch head 86b54a1d: unchanged (`routing_diagnostics.py` not in the diff). main 0523df20: same code.
- upstream: new for the misattributed hint. The no-op half is documented (#515 closed). Related: #572 closed (forced oracle links). Searches: "rip-existing-nets hint wrong net", "preexisting_blocker_hint", "hint names wrong blocker", "exact-fill strap unroutable", "oracle link hint rip-existing-nets", "blocker hint anchors endpoints", "rip-existing-nets already connected".
- severity after verification: MEDIUM
- issue draft:
  title: The #103 pre-existing-blocker hint for a plane-finalize oracle strap names a net far from the failure (it anchors on the net's derived endpoints, not the strap's)
  body: `route.py wk/gp14/04_multichannel_mixer/opt/sweep/s2_v200/step3.kicad_pcb out.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 200` fails the GND strap (152.05,114.91)<->(151.15,114.93). The stuck cells are blocked by Net-(IC4B-IN-) and Net-(IC2B-OUT), but the hint says `Retry with --rip-existing-nets 'Net-(IC5A-IN-)'`. That net is 0.2 mm from GND's derived endpoint (132.65,79.9) and 29.9 mm from the strap. Following the hint rips and restores IC5A-IN-, and the strap fails again; `--force-reroute` does the same. `--rip-existing-nets 'Net-(IC4B-IN-)' 'Net-(IC2B-OUT)'` routes the strap, and the finalize oracle then reports GND complete. Cause: `routing_diagnostics.py:451` takes its anchors from `get_net_endpoints`. Expected: for forced oracle links, attribute blockers at the link's own endpoints, the same ones the stuck-cell report uses.

### M35 -- VERDICT: CONFIRMED
- repro at 8328f157: `list_nets.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb --design-rules` prints `Manufacturing floor ... via 0.45/0.508` and `SUGGESTED route.py/qfn_fanout/bga_fanout/route_planes flags ... --via-size 0.45 --via-drill 0.508`, a drill larger than the via. The board declares `min_via_diameter=0.3` and `min_through_hole_diameter=0.508`. Feeding those flags to route.py raises no warning, and it writes `rules.min_via_drill: None -> 0.508` into the output project. No via was laid in my 5-net test, so the downstream effect is unmeasured.
- cause: `py_router/list_nets.py:103-104` floors `working_via_diameter` (max(min_via_diameter, fab 0.45)) and `working_via_drill` (max(min_through_hole_diameter, fab drill)) independently. Nothing enforces diameter >= drill + 2 x annular. The values are printed at `:789` and `:849-850`.
- branch head 86b54a1d: unchanged. main 0523df20: same `effective_floors` code (main's diff touches only docstrings and help text).
- upstream: new (#603 closed is the same family, a hole-to-hole floor inconsistency). Searches: "list_nets design-rules via drill larger than diameter", "working via drill diameter", "min_through_hole_diameter via drill", "design-rules suggested via", "via drill exceeds via size".
- severity after verification: MEDIUM
- issue draft:
  title: list_nets --design-rules suggests a via whose drill exceeds its diameter (--via-size 0.45 --via-drill 0.508)
  body: On `wk/gp14/07_One-Air-Max/repro/input.kicad_pcb` (min_via_diameter 0.3, min_through_hole_diameter 0.508), `list_nets.py --design-rules` prints "via 0.45/0.508" and SUGGESTS `--via-size 0.45 --via-drill 0.508`. `effective_floors` (list_nets.py:103-104) floors the diameter and the drill separately and never reconciles them. route.py accepts the pair silently. Expected: working diameter >= working drill + 2 x max(min_via_annular_width, fab annular), or a refusal naming the conflicting constraints.

### M21 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157, numbers reproduce:
  - **02**: route_planes then route.py `--layer-costs 1.0 3.0` (default via cost) gives blocking 0, **16 vias / 539.07 mm / 144 seg**. `--layer-costs 1.0 1.0 --via-cost 600` gives blocking 0, **0 vias / 535.08 mm / 124 seg**.
  - **11**: arm B's route step from `final_route_old2/step2a_diff.kicad_pcb` gives `FAB NOTE: 15 via(s) in a pad`, blocking 0, **55 vias / 557.12 mm**. With `--same-net-pad-clearance 0.1` there is no via-in-pad, blocking 0, **56 vias / 599.18 mm**. So the 11 lever is **not free: +42 mm copper (+7.5 %)**.
- cause: these are documented defaults, not code defects. The skill says via cost 75 is corpus-measured with 25 and 100 worse (`SKILL.md:2563`). Allowing via-in-pad by default is an owner decision (#1025, wontfix). The skill does offer a layer-cost retry keyed on high via count (`:3035-3070`). What holds is narrower:
  - the 2-layer through-hole recipe with a raised via cost (`:2146-2155`, from #1219) is scoped to *bus* boards, so a light non-bus through-hole board falls back to the SMD defaults;
  - route.py's `--same-net-pad-clearance` (route.py:8531) appears in the skill only under the route_planes options (`:2500`).
  One-board wins are not default changes under CLAUDE.md.
- branch head 86b54a1d: unchanged. main 0523df20: the same sections are present.
- upstream: related to #1219 (closed; its fix keyed the through-hole recipe on bus boards) and #1025 (closed wontfix); #153 (open, tune mode) and #658 (closed) are adjacent. Searches: "same-net-pad-clearance skill", "via-in-pad 2-layer default", "via cost through-hole 2-layer", "plan-pcb-routing via cost".
- severity after verification: LOW
- issue draft:
  title: plan-pcb-routing: route.py's --same-net-pad-clearance is documented only under route_planes, and the through-hole via-cost advice is scoped to bus boards only
  body: On a light 2-layer through-hole board (`wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb`, GND plane on B.Cu), the default `--layer-costs 1.0 3.0` / via cost 75 route gives 16 vias / 539.07 mm. `--layer-costs 1.0 1.0 --via-cost 600` gives 0 vias / 535.08 mm, both blocking 0. The skill's #1219 section that raises via cost applies only to "bus boards". On `wk/gp14/11_daplink/final_route_old2/step2a_diff.kicad_pcb`, default routing puts 15 vias in pads. route.py `--same-net-pad-clearance 0.1` gives 0, at the cost of +1 via and +42 mm copper. The skill never mentions that route.py takes the flag. Expected: name route.py's flag (with its cost) in the route options, and say whether the through-hole via-cost advice applies to non-bus through-hole boards. Single-board measurements, so this asks for docs, not a default change.

<!-- batch B11 -->
### M05 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157 (outputs in `wk/gp14/_verify/B11/m05_*`):
  - `route_review.py 03/repro/gap2_s6_routed.kicad_pcb` prints `== two-pad parts turned against their wiring (turn 180)` / `R207 at (152.27, 115.24) rot 90: saves 9.0 mm`.
  - `place_pose ... rotate R207 180` exits 4 with a pad stack Q201/R207. From rot 90 this is a quarter turn.
  - `rotate R207 180 --relative` exits 0 and writes the board. Pad 1 stays at y 115.244 and pad 2 moves from 107.624 to 122.864. `check_assembly --baseline` then exits 4, NOT BUILDABLE: R207<->R209 2.0042 mm², D203<->R207 1.2669 mm², both new.
  - `set R207 152.2729 107.6242 --rot 270` swaps the pads in place (pad 1 at 107.624, pad 2 at 115.244). check_assembly: buildable (blocking 0).
  - Board 01: `rotate R2 180` exits 0 and prints `Modified 1 footprint positions` next to `rotate R2 unmoved` and `"moved": []`. sha256 is 88e6f1af... for both input and output.
- cause:
  - That `rotate` is absolute is documented (`py_placer/place_pose.py:102-103`, `:278-283`), so that half is not a bug.
  - The defect is the mismatch. `py_tools/route_review.py:197-205` models the turn as the two pads exchanging positions, but `rotate` (absolute or `--relative`) pivots on the footprint origin, which is pad 1 on THT axials. Yet `.claude/skills/plan-pcb-placement/SKILL.md:361` and `:372-374` prescribe `place_pose ... rotate` for route_review's finding, and no command it names performs the modelled swap.
  - The no-op message comes from `py_placer/placement/writer.py:1192`/`:1349`, which count rewritten blocks, not changed poses.
  - Writing a NOT BUILDABLE `--relative` pose with exit 0 belongs to M09.
- branch head 86b54a1d: unchanged. place_pose.py and route_review.py are untouched, and SKILL.md:673-674 still says "with `place_pose ... rotate`". main 0523df20: place_pose has the same absolute/`--relative` semantics and the same writer message; route_review and the placement skill are not on main.
- upstream: new. Searches: "place_pose rotate", "rotate relative origin", "route_review turned", "pad swap two-pad", "turn 180", "turned against wiring", "rotate absolute", "place_pose no-op", "Modified footprint positions unmoved".
- severity after verification: MEDIUM
- issue draft:
  title: route_review's "turn 180" is a pad swap that `place_pose rotate` cannot perform; a no-op rotate prints "Modified 1 footprint positions"
  body:
  - route_review prices a turned two-pad part as its two pads exchanging positions (route_review.py:197-205). The placement skill (§3.6 step 4, place-mode paragraph) says to act on it with `place_pose ... rotate`.
  - `rotate REF DEG` sets an absolute angle, so from rot 90 `rotate 180` is a quarter turn. `--relative` pivots on the footprint origin (pad 1 on THT axials), so the body swings by the pitch instead.
  - Measured on wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb, R207 (axial P7.62, rot 90; route_review: "saves 9.0 mm"):
    - absolute: exit 4, pad stack Q201/R207;
    - `--relative`: written at exit 0; pad 2 moves 107.624 -> 122.864; check_assembly NOT BUILDABLE (R207<->R209 2.00 mm², D203<->R207 1.27 mm²);
    - `set R207 152.2729 107.6242 --rot 270`: buildable.
  - On wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb, `rotate R2 180` (already 180) writes a byte-identical board, exits 0 and prints "Modified 1 footprint positions" beside "unmoved".
  - Expected: route_review prints the pose that realises the swap (or place_pose offers a pad-swap turn about the pad midpoint), the skill names it, and the writer counts only changed poses.

### M06 -- VERDICT: CONFIRMED
- repro at 8328f157 (ledger `wk/gp14/_verify/B11/m06_ledger.jsonl`):
  - Record 1 (quick.score.json) exits 0.
  - Record 2 (board.score.json) exits 2: `this lap looks like an IMPROVEMENT only because it graded FEWER components. blocking 2 -> 0, but the components that differ are: impedance ...; length ...; net_widths ... Nothing was written.` The ledger keeps 1 line.
  - `converge.ungraded_set` gives `set()` for the quick payload and `{impedance, length, net_widths}` for board_score.
- cause:
  - `py_tools/quick_score.py:55-58` emits `blocking_by: {'broken': N}` with no `ungraded` list and no null components, even though its own docstring (`:9-13`) says it "leaves DRC, assembly and the floorplan out".
  - `py_placer/converge.py:384-413` therefore reads it as grading everything. `:448-453` then flags board_score's honest ungraded list as a strict shrink, and `:1013-1030` refuses.
  - The message is inverted: the quick row graded far less, not more.
- branch head 86b54a1d: converge.py unchanged. quick_score.py was rewritten: it now grades board connectivity, with `blocking_by {unrouted, broken, nets}` and `poured`. It still declares no ungraded set; a head-shaped payload still gives `commensurability(...)` false_improvement True. main 0523df20: same `ungraded_set`, plus an `--accept-incommensurable REASON` override; quick_score is not on main.
- upstream: new. Searches: "quick_score converge", "graded FEWER components", "ungraded_set", "converge record refuses", "incommensurable", "quick_score ungraded".
- severity after verification: MEDIUM
- issue draft:
  title: converge record refuses the first board_score row after a quick_score row ("graded FEWER components"): quick_score's payload declares no ungraded components
  body:
  - quick_score writes `{blocking, blocking_by: {broken}, quality}` and grades only connectivity (no DRC, assembly or floorplan), but declares no `ungraded` list or null `blocking_by` keys. `converge.ungraded_set` therefore reads it as complete.
  - The next row, scored by board_score (which lists impedance/length/net_widths as ungraded), is refused as a "false improvement" with "graded FEWER components" (exit 2, nothing written). The skill scores judge rounds with quick_score and full routes with board_score in one ledger.
  - Repro (R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro): `converge.py record --ledger NEW.jsonl --board $R/s7_fast.kicad_pcb --kind completion --parent $R/input.kicad_pcb --lever "fast route" --score-file $R/quick.score.json`, then the same with `--board $R/final_copy.kicad_pcb --parent $R/s7_fast.kicad_pcb --score-file $R/board.score.json` -> exit 2.
  - Expected: quick_score declares what it leaves out (`ungraded` or null components), so the comparison is honest, or converge treats a payload without `ungraded` as unknown rather than complete.

### M08 -- VERDICT: CONFIRMED
- repro at 8328f157 (outputs in `wk/gp14/_verify/B11/m08_*`):
  - **Board 11:** place_simple exits 0 with `WARNING: J3 ... no room along the east edge` (J2 the same). seat_probe shows `padbox (-6.775, -5.58, 6.895, 5.58)` and a band of 0.380 at every interior position against the declared min 7.0. J3's pads include `'' smd ['F.SilkS'] 6.0x0.76` at local x 3.895, while copper ends at x -4.275.
  - **Board 02:** exits 0 with `J1 ... no room along the west edge` and `"illegal": []`. check_floorplan exits 4 with 2 ERRORs: nearest edge north, mating face north. seat_probe: band 11.428 at every position and seat coord 150.470, which is mid-board; the west edge is at 103.3.
  - **Board 08:** `SW501 ... no room along the east edge`. seat_probe shows `copper_clear False` at every position (coord 130.933). My probe (`m08_sw501_probe.py`) at x 130.90 (0.033 mm inward) gives copper_clear True and `probe.ok` True. The straight east edge is at x 132.90, and the bounds' east edge is 136.25 (the corner ears).
- cause (three different faults, all reported with the one fixed string at `py_placer/placement/edge_seat.py:383-385`):
  - (11) `_pad_box` (`edge_seat.py:117-125`) keeps every non-NPTH pad, including silk-only pads. That box sets `_seat_coord`'s copper limit (`:232-238`), so the part is held back 0.55 mm from silk "copper".
  - (02) `_seat_coord`'s bisection (`:224-231`) starts mid-board and moves out only while band <= target (0). J1's 54.1 mm courtyard is longer than the 43.18 mm edge, so the band never reaches 0, the coordinate stays mid-board, and the nearest-edge conjunct fails.
  - (08) `edge_at` comes from `pcb.board_info.board_bounds` (`:215-217`, `:236-238`), not from the outline at the seat. On a board with ears the copper limit never binds, and a courtyard-less part is left 0.367 mm from the edge against the required 0.372 + slack.
- branch head 86b54a1d: edge_seat.py unchanged. main 0523df20: edge_seat.py and place_simple are not on main.
- upstream: new. Neighbours, all CLOSED and different: #1257 (seeder `pose_ok`, not edge_seat), #1241, #1240, #1242, #1201, #987. Searches: "edge seat no room", "no room along", "seat silk pad", "seat board_bounds outline", "edge seat courtyard wider", "_pad_box", "edge seat", "declared on an edge but has no seat".
- severity after verification: MEDIUM
- issue draft:
  title: place_simple's edge seat says "no room along the <edge> edge" for three different faults, two of them seats that exist
  body:
  - (a) `edge_seat._pad_box` counts silk-only pads as copper. Harwin_M20-89005xx draws pins as `pad "" smd (layers "F.SilkS")`, which pins the seat 0.55 mm inside the edge: band 0.38 vs declared 7.0. The pose is legal; teammate measured 7.006, pass. Repro: `place_simple.py wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb OUT --groups .../groups.json --intent .../intent_edges.json --seed 1`.
  - (b) `_seat_coord` takes the edge from `board_bounds`. On wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb (east bounds 136.25 at the ears, straight edge 132.90), SW501 is placed with copper 0.367 mm from the edge. Every position fails copper_clear, and 0.033 mm inward passes every conjunct.
  - (c) when the courtyard is longer than the edge (wk/gp14/02_sonde_xilinx DB25 J1: 54.1 mm on a 43.18 mm edge), the band never reaches the target, the bisection never leaves mid-board, and place_simple exits 0 with `illegal: []` while check_floorplan gives 2 ERRORs.
  - Expected: copper-only pad box, the outline's edge at the seat, and an unseated reason naming the failing conjunct (e.g. "band >= 11.43 at every pose: the courtyard is longer than the edge").

### M15 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: place_simple on `10/repro/gap2_fixed.kicad_pcb --seed 2`, once with `gap2_groups_apart.json` and once with `gap2_groups_v1.json` (outputs `B11/m15_*`).
  - Both exit 0, and 0 of 264 parts differ in pose.
  - Costs are 10846.92 vs 10831.92; hints are 17.14 vs 2.14.
  - The log shows `apart:core:leds 15.0` (weight 5 × 3.0).
- cause:
  - `py_placer/placement/simple.py:822-828` prices `apart` as `weight*max(0, APART_MM - gap)`. The gap is the least `rect_gap` over all A×B pairs (`:836-858`), and `rect_gap` is 0 on touch or overlap (`:244-248`). For interleaved groups the term is constant, so the anneal's trajectory is unchanged.
  - The `near`/`edge` halves are the documented min semantics (`:815-820`) and were not shown to cause harm here. Only `apart` is confirmed.
  - Nothing warns that a hint is saturated.
- branch head 86b54a1d: the hint code is unchanged (simple.py only gains the template term). main 0523df20: simple.py is not on main.
- upstream: new. Searches: "apart hint", "groups apart", "hint saturate", "apart groups gradient", "place_simple hints".
- severity after verification: MEDIUM
- issue draft:
  title: place_simple's `apart` hint is a constant when the two groups touch anywhere: no gradient, identical placement
  body:
  - The `apart` term is weight × (3 mm − least gap over every pair of members). Once any member of A touches any member of B (interleaved groups), the gap is 0 at every reachable pose, so the term is a flat weight×3.
  - Measured with wk/gp14/10_glasgow_revC/repro: `place_simple.py gap2_fixed.kicad_pcb OUT --groups gap2_groups_apart.json --intent gap2_intent_v2.json --seed 2` vs the same with gap2_groups_v1.json gives identical poses (0/264 parts differ) and costs exactly 15.0 apart (10846.92 vs 10831.92; "apart:core:leds 15.0").
  - Expected: a separation measure that responds to partial separation (e.g. summed overlap/shortfall over member pairs, or group hull gap), or at least a warning that a hint sits at its saturated value.

### M16 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `classify_part`: DC1 `DC-IN-SMD_DC-045A-13A` -> None, PWR_SW1 `SW-TH_TK-6580A8-1` -> None, USB1 -> edge_receptacle, SW1 -> edge_actuator. On board 08: J501 `EDAC 690-019-298-412` -> None and J1 `GLPLXSMT188S7QQYG` -> None.
  - Board 08 seed 7 place_simple: `NOTE: J501 is declared on the south edge but is not an edge part (no part class)`, while the intent row says `"class": "edge_receptacle"`.
  - check_floorplan on that same output grades J501 as one: `[ERROR] edge_connector: J501 is an edge part seated 0.68mm from the nearest edge ...`.
  - `--emit-intent --declare-classes`: J501 is absent, and J1 reads "not an edge part (no part class), so no edge is claimed".
  - Outputs in `B11/m16_*`.
- cause:
  - `py_placer/placement/edge_seat.py:326-334` decides with `classify_part` only and never reads the entry's `class`. `docs/floorplan-intent.md:147` lists `class` as an edge_connectors key, and `:488` says the grade honours a declared `class: edge_receptacle`, so the grade and the seat disagree.
  - The name tables at `part_class.py:79-83` miss `DC-IN`, `SW-TH_` (hyphen, not `sw_`) and part-number-only names. `_prefix('PWR_SW1')` is `PWR`, so the `SW` actuator prefix misses too.
- branch head 86b54a1d: edge_seat.py and part_class.py unchanged. main 0523df20: same name tables in part_class.py; edge_seat is not on main.
- upstream: new. Same family as #1176 (CLOSED, a different misread). Searches: "classify_part", "part_class declared class", "DC jack edge class", "slide switch edge", "HDMI part class", "not an edge part".
- severity after verification: MEDIUM
- issue draft:
  title: place_simple's edge seat ignores an intent `edge_connectors[].class`; DC jacks, slide switches and part-number-named HDMI/RJ45 get no class
  body:
  - `edge_seat.seats` filters entries by `classify_part` alone (edge_seat.py:326-334), so a declared `"class": "edge_receptacle"` is ignored and the part is "placed as any other part". check_floorplan, however, honours the declared class and grades it as an edge part.
  - Repro: `place_simple.py wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb OUT --groups .../gap1_groups.json --intent .../gap1_intent.json --seed 7` -> "J501 ... is not an edge part (no part class)". `check_floorplan OUT --intent .../gap1_intent.json` -> "[ERROR] edge_connector: J501 is an edge part seated 0.68mm from the nearest edge".
  - Name tables also miss DC1 `DC-IN-SMD_DC-045A-13A`, PWR_SW1 `SW-TH_TK-6580A8-1` (wk/gp14/07_One-Air-Max/repro/input.kicad_pcb), J501 `EDAC 690-019-298-412` and J1 `GLPLXSMT188S7QQYG`, and `--declare-classes` emits no class for them.
  - Expected: a declared `class` takes precedence in the seat as it does in the grade, and the tables cover `dc-in`/`dc_jack`, `sw-`/`slide` variants.

### M30 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - The 09 repro (seeds 8, clustered 8) reproduces exactly: `cost 1352.2`, `decap_broken 4`, `claim_broken 1`, `claim_limits 13.22`.
  - check_floorplan exits 4 with 2 ERRORs, plus `[warn] proximity: Y1 pad 1 is 14.83mm from U1 pad 22 on /XI, past ... 8.10mm` and pad 3 at 14.59.
  - With hand ESD rows (2.0 mm, `B11/m30_intent_esd.json`): D3 3.80 mm and D7 7.62 mm on this seed.
  - `board_context` emc_roles finds only the crystal role.
- cause:
  - **Crystal: not "blind".** `py_placer/place_simple.py:166-183` gives every claim row its `max_mm` limit, warning-graded ones included. That limit is priced at `--claim-limit-weight` 10 (`:388`) through `simple.py:581-596`, and the console prints "1 claim limit(s) broken". The anneal leaves a priced soft term 6.7 mm past its limit, so SKILL.md:169 "Crystals take care of themselves" overstates.
  - **ESD: confirmed.** There is no objective term unless a `proximity` row is declared. `emc_roles._esd_arrays` (`py_placer/placement/emc_roles.py:449`) detects ESD only by array pin functions, so the 2-pad D_0402 TVS diodes get no proposed row, and the skill's "ask for ESD rows from emc_roles" (SKILL.md:81-88) yields none here.
- branch head 86b54a1d: claim pricing and emc_roles are unchanged. The head adds datasheet `templates` (switching stages and RF front ends), not crystals or ESD. main 0523df20: emc_roles has the same detector; place_simple is not on main.
- upstream: evidence for #1254 (CLOSED: its emc_roles fix covers ESD arrays only; discrete diodes are a gap). Searches: "crystal claim place_simple", "ESD connector placement", "TVS diode connector", "emc_roles ESD diode", "claim limit broken crystal".
- severity after verification: LOW
- issue draft:
  title: Discrete ESD/TVS diodes get no emc_roles row, so nothing places or grades them at their connector
  body:
  - emc_roles detects ESD only as arrays by pin function (emc_roles.py:449). A 2-pad TVS diode (D_0402, data line to GND) is never a role, so no `proximity` row is proposed and place_simple's objective has no term for it.
  - On wk/gp14/09_StickHub/repro/g2_fixed.kicad_pcb, `board_context --json` reports only the crystal. After `place_simple ... --seeds 8 --clustered-seeds 8`, hand rows (D7->J5, D3->J3 at 2.0 mm) grade D7 at 7.62 mm and D3 at 3.80 mm. The placement lessons cite humans at about 2 mm.
  - Expected: emc_roles reports a two-terminal diode from a connector signal net to ground as an ESD role, with a ready row.
  - (Separately, the skill's "Crystals take care of themselves" is contradicted on this seed: Y1 is 14.8 mm from XI/XO, against 8.1, while the term is priced.)

### M31 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - The repro as written (`r1/s5`) shows **no** proximity finding: adjacency gap 2.53 mm, the claim passes.
  - On round 2's best board `r2/s0`: `[ERROR] proximity: U30 pad L1 is 12.46mm from J5 pad 43`. L1 is `/PKTEND`, not a GND ball, and 12.46 mm is the closest pad pair of any net.
  - The objective's legs are the 43 U30 pads on nets shared with J5 (GND 10, +3V3 5, ...). Their overshoot past 5 mm is 240.87 mm on r1/s5, where the grade passes (worst G4 /IO_Banks/VIO_AUX at 24.13 mm), and 846.91 mm on r2/s0.
  - `r3_badclaim/s0.log`: `claims 659.0, 2 claim limit(s) broken`.
- cause, re-diagnosed: the objective and the grade measure different things for a claim without `pads`.
  - The grade's undeclared arity is part-to-part adjacency: the minimum over all pad pairs, with no net matching. `py_placer/placement/floorplan.py:5721-5742`, and the docstring at `:6077-6089` explicitly forbids net matching here.
  - place_simple builds per-pad legs over every shared net, rails included (`place_simple.py:171-183`), and prices each leg's overshoot (`simple.py:554-596`). That makes the claim unsatisfiable for a 121-ball BGA in the objective only.
  - The skill's text at SKILL.md:353-355 ("pad edge to the nearest pad on a shared net") matches neither.
- branch head 86b54a1d: code unchanged; the skill's C6/SW1 example sentence is removed. main 0523df20: same `proximity_reaches`; place_simple is not on main.
- upstream: new. Searches: "proximity claim pads", "proximity adjacency shared net", "claim_cost proximity", "proximity undeclared pads", "proximity objective grade".
- severity after verification: MEDIUM
- issue draft:
  title: place_simple prices a `proximity` claim without `pads` as every shared-net pad's reach, while check_floorplan grades it as adjacency
  body:
  - For `{"ref":"U30","near":"J5","max_mm":5}` (no `pads`), check_floorplan takes the closest pad pair of any net (floorplan.py:5721-5742). place_simple builds one leg per U30 pad on any net shared with J5, GND and +3V3 included (43 legs), and prices each leg's overshoot.
  - On wk/gp14/10_glasgow_revC/r1/s5.kicad_pcb with wk/gp14/10_glasgow_revC/repro/gap3_intent_v3_badclaim.json, the grade passes (2.53 mm) while the objective carries 240.9 mm of overshoot (worst G4 VIO_AUX at 24.1 mm). Placing with that claim gave `claims 659.0, 2 claim limit(s) broken` (r3_badclaim/s0.log).
  - Expected: the objective uses `floorplan.proximity_pads`/`proximity_reaches` (the grade's two arities), or warns when an undeclared claim spans rails.

### M32 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `route_plan_check.py 05/repro/interf_u_plan.sh --board .../r3_s7.kicad_pcb` exits 4: `FAIL R14 ... Net-coverage gap: ['GND'] handled by no stage -- the route step excludes ['GND'] and Step 2b routes []` / `REFUSED`.
  - The same plan with `'!GND'` removed from step 1 (`B11/m32_plan_gnd_kept.sh`) exits 0: `OK: 17 rule(s) checked`.
  - I did not re-run the routes. The teammate's 0 vs 2 broken comparison is one run per variant.
- cause:
  - R14 (`.claude/skills/plan-pcb-routing/scripts/route_plan_check.py:387-410`) unions `!X` over every non-impedance route.py step and requires the union to equal the impedance set. That faithfully implements Step 5b's asserts (`SKILL.md:1236-1250`) and `:2599` ("the only legitimate exclusions are the Step-2b impedance nets"). So the skill's own chain, read that way, passes; the cluster's "refuses the skill's own Step 8 chain" is too strong.
  - What holds: Step 5b's prose invariant (`:1221-1222`, "A net excluded from any stage MUST be claimed by a later one") is satisfied by the refused plan, since steps 3 and 4 claim GND with `'*'`. Step 8's pour-last text (`:2116-2126`, "route signals ... then pour GND last ... close with route.py --nets '*'") does not say GND stays in the first step. The skill text is ambiguous, and R14 does not credit a later claim.
- branch head 86b54a1d: unchanged. main 0523df20: same R14 code and same Step 8 text.
- upstream: new. Neighbours: #377 (CLOSED, a different coverage hole) and #941 (CLOSED, general skill wording). Searches: "route_plan_check R14", "net coverage reconciles", "pour last route_plan_check", "Net-coverage gap".
- severity after verification: LOW
- issue draft:
  title: Routing skill: Step 5b's prose invariant and its asserts (route_plan_check R14) disagree on a net excluded in one route step and claimed by a later one; Step 8's pour-last flow is silent on which applies
  body:
  - Step 5b says "A net excluded from any stage MUST be claimed by a later one", but its asserts, and R14, require the union of every route step's `!X` to equal the impedance set.
  - Step 8's dense 2-layer flow ("route signals on both layers, then pour GND last, close with route.py --nets '*'") does not say whether GND stays in the signal step. A plan that excludes it there and claims it in the closing `'*'` step is refused.
  - Repro: `route_plan_check.py wk/gp14/05_interf_u/repro/interf_u_plan.sh --board wk/gp14/05_interf_u/repro/r3_s7.kicad_pcb` -> FAIL R14. With `'!GND'` dropped from step 1: OK.
  - Expected: Step 8 states that the signal step keeps GND (`--nets '*'`), or R14 accepts an exclusion claimed by a later route step, with the prose and the assert saying the same thing.

<!-- batch B12 -->
### L01 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: I re-read all 8 `wk/gp14/_cmp/<stem>/movie3d.log` files (102 boxed parts) and sorted each part by cause with `wk/gp14/_verify/B12/L01/classify.py` (output in `classify.txt`). It uses `models.stage_models` itself, plus the campaign iso wrapper's resolution (`_staging/iso_render.py`).
  - **41 cannot be resolved by either renderer.** They point at third-party, absolute or foreign paths, or at library models that KiCad 10 renamed. Examples: CM5 `${KICAD_3RD_PARTY}/EasyEDA...`, glasgow `../../packages3D/...`, pico_ice `E:/KICAD_LIB/...`, rp2350 `QFN-60...step`.
  - **11 have no `(model)` in the footprint at all.** These are imx6 U1/U2 (the BGAs), pico FID1-6, BUS1, J9 and J10. kicad-cli draws nothing for them either.
  - **22 are `${KIPRJMOD}` models.** movie3d resolves KIPRJMOD to the input board's own folder (`r<N>/`), which has no 3D files. The campaign's iso wrapper instead rewrites KIPRJMOD to the source project. With `models.export` pointed at the source project (`export_test.py`):
    - ecc83 U1: drawn (a `.wrl`, which GLB export does load);
    - StickHub: 16 of 17 drawn (the 17th, J9, has no model), 86/90 parts with models;
    - CM5: J501/J601/J802/Module301/Module302 drawn.
  - **28 are DNP parts:** imx6 R13…R71 (23), rp2350 C2/J3/U1/U8, CM5 R103. Their models resolve, but the export passes `--no-dnp`, so they get a box and are listed as "fell back to a box". The iso wrapper's 153/153 on imx6 counts these 23.
- cause:
  - DNP: `movie3d/models.py:202` exports with `--no-dnp`, and `movie3d/record.py:579` puts every modelless part with a body into `boxed`. So a deliberately excluded part is drawn as a grey box and reported as a fallback.
  - KIPRJMOD: `record.py:181` and `models.py:81` set KIPRJMOD to the input board's directory, which is KiCad's own meaning. Running on boards copied out of their project is campaign environment, not a tool defect.
  - The rest: missing model files, or no model at all.
- branch head 86b54a1d: models.py and record.py unchanged (only `make_movie.py` argparse constants moved). main 0523df20: movie3d is not on main; main's `py_router/stage3d/scene.py:344` exports with the same `--no-dnp`.
- upstream: new; searches: "movie3d box", "movie3d models", "dnp 3d model", "no-dnp", "KIPRJMOD model", "3D model box fallback", "stage3d models". Only #1081 came up, which lists the `--no-dnp` flag and does not discuss boxes.
- severity after verification: LOW
- issue draft:
  title: movie3d draws DNP parts as boxes and reports them as "fell back to a box" though their models resolve
  body: `movie3d/models.py:202` exports the parts GLB with `--no-dnp`, so DNP footprints have no node. `record.py:579` then counts every modelless part with a body as `boxed` and prints it under "fell back to a box". On imx6ulz_4l (`wk/gp14/14_imx6ulz_4l/r1/fixed.kicad_pcb`), 23 of the 25 "boxes" are DNP 0402 resistors (`(attr smd dnp)`) whose `R_0402_1005Metric` model resolves (`.wrl -> .step`). rp2350 (C2, J3, U1, U8) and CM5 (R103) behave the same way. Repro: `movie3d/make_movie.py` on that board and read the `record:` line. Expected: either export DNP parts (as `kicad-cli pcb render` has no DNP filter), or omit them or draw them distinctly, and report them as "DNP, not drawn" rather than as a model fallback.

### L02 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `check_floorplan.py .../06_.../repro/rn_owner.kicad_pcb --intent .../intent.json` exits 4 with `decap_distance: C25 is 2.54mm from RN1, the IC it decouples` (`B12/L02/check_floorplan.txt`).
  - `chip_refs` includes D1, RN1 and RN2. Every +3V3 cap's owners are `['U2','U6','U7','D1','Y2','RN2','RN1','U1']`. The election gives C2→D1 (0.26 mm), C22→RN1 (0.97 mm) and C25→RN1 (2.54 mm).
  - RN1 is `R_Array_Convex_4x0402`, role `unknown`. D1 is an RGB LED, role `diode`. Both win their supply pins through the `rail_net` channel, on pads typed `passive`.
  - Counterfactual with RN1/RN2/D1 removed from the owner set: C22→U2 at 4.85 mm and C25→U2 at 5.85 mm. So C22 currently grades clean only because it sits next to a pull-up array.
  - Board 14's part is not reproduced. `_elect_tethers` elects C20 to U8, the MCP1700, at 4.74 mm, through `supply_owner_evidence` ("pad 2 is typed power_out"), so #1249's fix is on the pin. The `U1 pin P12 … from C20` finding is the separate pin rule and is correct.
- cause: `py_placer/placement/groups.py:264-273` (`_ic_list`) makes any part with 4 or more copper pads in a non-collinear layout a cap owner, with no role check. The role filter `_THREE_PAD_ROLES` (`groups.py:285`) applies only to 3-pad owners. `floorplan.py:5461` (the `rail_net` channel) then gives a passive pin on a capped rail supply-pin status.
- branch head 86b54a1d: groups.py unchanged, and the floorplan.py and grouping.py diffs do not touch the election. main 0523df20: same code (`_ic_list` at groups.py:277).
- upstream: new (#1249 is closed and its fix is present; #1267 is open but is about a different stage); searches: "decap owner resistor array", "decap owner LED", "IC it decouples", "chip_refs resistor array", "decap owner election", "resistor array", "rail_net supply pin", "IC by shape", "LED decap".
- severity after verification: MEDIUM (it hides an error-graded decap distance: C22 reads clean at 0.97 mm from RN1 while the nearest real IC is 4.85 mm away)
- issue draft:
  title: Decap owner election makes resistor arrays and LEDs "the IC it decouples" (no role check on ≥4-pad owners)
  body: `groups._ic_list` admits any part with 4 or more copper pads, not in a row, and the `rail_net` supply-pin channel then gives it supply pins on a capped rail. On `wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/rn_owner.kicad_pcb`, RN1/RN2 (`R_Array_Convex_4x0402`, 10k pull-ups) and D1 (RGB LED, `infer_role` = diode) own +3V3. Elections: C25→RN1 at 2.54 mm (reported "C25 is 2.54mm from RN1, the IC it decouples"), C22→RN1 at 0.97 mm (graded clean), C2→D1 at 0.26 mm. With those three excluded, C22→U2 is 4.85 mm and C25→U2 is 5.85 mm. Repro: `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/rn_owner.kicad_pcb --intent wk/gp14/06_rp2350_fpga_eensy_prePlane/repro/intent.json`. Expected: a part whose role is a resistor, resistor array, LED or diode is not a decap owner. This is the same kind of role gate that `_THREE_PAD_ROLES` already applies to 3-pad owners.

### L03 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `board_score.py .../06_.../repro/input.kicad_pcb --quiet --json …` prints 21318 bytes to stdout, of which the SCORE_JSON line is 20761. `components.assembly.pairs` and `.containments` are capped at 20 entries each, with `pairs_count` 362 / `pairs_truncated` 342 and `containments_count` 265 / `containments_truncated` 245.
  - `place_pose.py …/13_pico_ice_rev3/repro/pile.kicad_pcb B12/L03/pp_fid1.kicad_pcb set FID1 67.3 75.0 lock FID1` exits 0 with 315603 bytes of stdout:
    - the JSON_SUMMARY line is 290919 bytes, of which `pad_edge_before` and `pad_edge_after` are 122 KB each (428 `findings` plus 429 `unmeasured` rows each);
    - about 430 extra text lines, one `C1.1: edge shortfall …` per pad.
- cause:
  - board_score is working as #1194's fix intended. `STDOUT_LIST_CAP = 20` is at `py_tools/board_score.py:593`, and `--quiet` is documented as "accepted… changes nothing" (`:1274-1279`). The 21 kB is the capped line; #1194 itself quoted about 19.8 kB after the fix. Not a bug.
  - place_pose is a real defect: `py_placer/placement/pose_ops.py:634-635` copies the whole `pad_edge` grade into the summary uncapped, `py_placer/place_pose.py:718-720` prints every pad-edge finding (pad stacks are capped at 5 two lines below, at `:728`), and `:629` dumps the summary.
- branch head 86b54a1d: place_pose.py, pose_ops.py and board_score.py unchanged. main 0523df20: same code (`place_pose.py:725`, `pose_ops.py:639`, board_score `STDOUT_LIST_CAP` at `:596`).
- upstream: board_score half is a duplicate of #1194 (closed, fix present and working); place_pose half is new; searches: "place_pose output size", "place_pose JSON_SUMMARY", "pad_edge findings", "JSON_SUMMARY large pile", "stdout cap".
- severity after verification: LOW
- issue draft:
  title: place_pose on a pile prints ~300 KB: pad_edge findings uncapped in JSON_SUMMARY and in the text report
  body: `python3 -X utf8 py_placer/place_pose.py wk/gp14/13_pico_ice_rev3/repro/pile.kicad_pcb OUT.kicad_pcb set FID1 67.3 75.0 lock FID1` (97-part pile) writes 315603 bytes to stdout. JSON_SUMMARY is 290919 bytes, of which `pad_edge_before` and `pad_edge_after` are 122 KB each (428 findings plus 429 unmeasured rows each, `pose_ops.py:634-635`). The text report prints one line per pad-edge finding (`place_pose.py:718-720`), while pad stacks are already capped at 5. A refusal's one-line reason is buried in this. Expected: the same treatment as #1194 gave board_score. Cap the stdout lists, add `_count`/`_truncated`, and offer a `--json` file for the full grade.

### L04 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `board_brief.py wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb` (JSON `pile: true`, "100% of footprints lie outside the board outline") prints "State mechanical poses with place_fixed and the rest with place_at/place_pack", then "mechanical: 12 part(s) … 12 of them sit alone at their coordinate, so `at` is assertable with place_fixed".
  - All 12 parts (H101-H105, J101, M701, M702, Module301, SW101, SW501, USB701) are at staging poses around y = 98.9-103.1, below the outline's max y of 84.45. None is at its source pose, and none is locked.
  - The per-part check `pose_shared_with` is empty for all 12 because the repo's own `.claude/skills/plan-pcb-placement/scripts/make_unplaced.py` spreads the pile on a grid of about 0.78 mm. That makes the check vacuous on the repo's own pile format.
  - `ls py_placer | grep -E "place_(fixed|at|pack)"` finds nothing, and `design_brief.py:1288-1289` says so itself: "`place_fixed` is named only in comments".
  - `board_context.py wk/gp14/09_StickHub/repro/g8_pile.kicad_pcb --md` gives a 653-row pin-order table (433 AGREES, 124 CROSSED, 96 UNDETERMINED) with no pile note. The EMC legs (e.g. `Y1.1 → U1.22 2.431 mm`) and per-part poses are also printed from staging poses.
  - The teammate's "its other sections do withhold" is wrong: board_context has no pile handling at all (`grep -i pile` finds nothing).
- cause:
  - `py_tools/board_brief.py:976-989` prints the nonexistent op names, and `mechanical_section` (`:536-573`) uses an "alone at its coordinate" test as its honesty check.
  - `py_tools/board_context.py:366` calls `pin_order_rows`, which uses `pair_order.pair_metrics`. That function measures "at their live poses": its channel axis is the line between the two part centres (`pair_order.py:126-166`).
  - #1103's withholding covers only `check_floorplan --emit-intent`.
- branch head 86b54a1d: unchanged. main 0523df20: same code (board_brief `:990`/`:1000`; board_context has no pile handling).
- upstream: new, same family as #1103 (closed, emit-intent only) and #1109 (closed, the pile predicate); searches: "board_brief place_fixed", "board_brief mechanical pile", "board_context pile", "pin-order pile", "place_fixed", "pose_shared_with".
- severity after verification: LOW
- issue draft:
  title: board_brief and board_context make pose claims off a pile's staging poses; board_brief recommends ops that do not exist
  body: On `wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb` (`pile: true`), board_brief says "12 of them sit alone at their coordinate, so `at` is assertable with place_fixed". All 12 sit at staging coordinates outside the outline. `pose_shared_with` is empty because `make_unplaced.py` spreads the pile on a grid, so the per-part check cannot fire. The text also recommends `place_fixed`/`place_at`/`place_pack`, which do not exist in `py_placer/` (`design_brief.py:1288`). `board_context --md` on `wk/gp14/09_StickHub/repro/g8_pile.kicad_pcb` prints 653 pin-order verdicts (124 CROSSED) and EMC leg distances, all measured at staging poses, with no pile notice. Expected: on a pile, withhold or flag pose-derived claims (as #1103 does for emit-intent), and name the real tools (`place_pose`, intent `fixed_poses[]`).

### L05 -- VERDICT: NOT A BUG
- repro at 8328f157:
  - `films.log` for glasgow shows `gif film.gif: 6400 KB` and `gif film_andy.gif: 4352 KB`; for imx6, `gif film.gif: 5376 KB`. All were produced by `films.sh`'s own `gif()` ffmpeg function (`wk/gp14/_staging/films.sh:27-34`, with a single fallback step).
  - After `_staging/shrink_gifs.sh`, all six GIFs for 10 and 14 are 1.86-2.62 MB.
  - The inputs come from krt-film's `make_film` mp4 (not on the pin), and from mp4s written by place_movie, route_movie, movie3d and the campaign's own ffmpeg concat.
- cause: the campaign's asset step, not a repo tool. No repo tool wrote these GIFs. `place_movie`/`route_movie` can write a GIF only when ffmpeg is missing or a `.gif` output is named, and here they wrote `.mp4`.
- branch head 86b54a1d: n/a (place_movie.py diff is unrelated); main 0523df20: n/a
- upstream: none relevant; searches: "GIF size", "gif 3 MB".
- severity after verification: none

### L06 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157:
  - `render_placement.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb -o B12/L06/x.png` prints "this board does not look PLACED … Override with --allow-unplaced.", then writes `x_F.png` and `x_B.png` and exits 0.
  - The same command with `--allow-unplaced` exits 2: `unrecognized arguments: --allow-unplaced`.
  - Its suggested crop commands write `-o wk/worst1.png` … `wk/worst6.png`, `wk/clean.png` and `wk/focus/`, whatever `-o` was.
  - board_score with `--intent` on the same pile reports the floorplan component `ran: false` with "check_floorplan.py exited 3 … Override with --allow-unplaced" and lists it under `UNGRADED`. That disclosure is honest: a floorplan grade on staging poses means nothing, and the PREP note itself calls this cosmetic.
- cause:
  - `py_tools/render_placement.py:2241` calls `gate_or_exit(..., warn_only=True)` without `allow_unplaced`. `placement_state.py:426` passes only `allow_unplaced` to `format_report`, and `format_report` adds the override line at `:398-399` whenever `allow_unplaced` is False, so the warn-only renderer advertises a flag it does not have.
  - The crop paths are hard-coded at `render_placement.py:1821-1827`.
  - The board_score half is intended behaviour (`board_score.py:839-841`), apart from repeating check_floorplan's override hint.
- branch head 86b54a1d: unchanged. main 0523df20: same code (`placement_state.py:432/459`, `render_placement.py:2174`, `:1759`).
- upstream: new; it is the `allow_unplaced` twin of #1202 item 4 (closed, which fixed only the `allow_routed` text); searches: "render_placement allow-unplaced", "Override with --allow-unplaced", "allow-unplaced render".
- severity after verification: LOW
- issue draft:
  title: render_placement tells the user to "Override with --allow-unplaced", a flag it rejects (exit 2), and renders anyway
  body: `python3 -X utf8 py_tools/render_placement.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb -o x.png` prints "Override with --allow-unplaced." and exits 0 after writing the panels. Adding `--allow-unplaced` gives `error: unrecognized arguments` (exit 2). `gate_or_exit(..., warn_only=True)` (`render_placement.py:2241`) still lets `format_report` (`placement_state.py:398-399`) add the override line. This is the unplaced counterpart of #1202 item 4. The same report's crop suggestions hard-code `-o wk/worst{i}.png` and `wk/clean.png` (`:1821-1827`) instead of following `-o`. Expected: no override advice in `warn_only` mode, and crop paths next to the `-o` target.

### L10 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `check_floorplan.py …/05_interf_u/repro/r1_s8.kicad_pcb --intent …/intent_with_why.json` exits 2: `proximity[0]: unknown key(s) why. Known: basis, context, max_mm, near, note, pads, ref, source`.
  - With `why` renamed to `note` on the proximity rows and `fixed_poses[0]` given `note` instead of `why` (`B12/L10/intent_fixed_note.json`), it exits 2: `fixed_poses[0]: unknown key(s) note. Known: accept_courtyard_overlap, basis, context, ref, rot, side, why, x, y`.
  - Survey of the free-text key per row type (`key_survey.txt`):
    - `why` only: fixed_poses, assembly;
    - `note` only: proximity, blocks, edge_connectors, keepouts, keep_away;
    - both: arrays, replicate;
    - `reason`: waivers.
- cause: `py_placer/placement/floorplan.py:233` (`_FIXED_POSE_KEYS`) versus `:320` (`_PROXIMITY_KEYS`), enforced by `_reject_unknown` (`:672-685`). The refusal names the accepted keys, so it costs one retry.
- branch head 86b54a1d: key sets unchanged. main 0523df20: same (`:239`, `:320`).
- upstream: new; searches: "intent why note", "unknown key why proximity", "fixed_poses note", "intent schema note why".
- severity after verification: LOW
- issue draft:
  title: Intent rows spell their free-text reason three ways (why / note / reason); proximity refuses `why`, fixed_poses refuses `note`
  body: Accepted free-text keys at 8328f157: fixed_poses and assembly take `why`; proximity, blocks, edge_connectors, keepouts and keep_away take `note`; arrays and replicate take both; waivers take `reason`. The unknown-key gate (#710) refuses the others, so `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent_with_why.json` exits 2 on `proximity[0]: unknown key(s) why`, and the mirror case refuses `fixed_poses[0]: note`. Expected: one spelling accepted on every row type (or `why` and `note` as aliases everywhere), still refusing truly unknown keys.

### L12 -- VERDICT: NOT A BUG
- repro at 8328f157: I ran the cluster's exact `route.py … old1_step2.kicad_pcb B12/L12/iter1.kicad_pcb --nets '*' …` command: 2:07 wall, exit 0. Its log ends with `"improvement_gate": "reverted"` and "(improvement gate reverted the output -- … the output is the input board, project and rules included)". `board_score` gives step2 and iter1 the same `BLOCKING=17 (broken=16 drc=1) vias=334 copper_mm=2928.06`.
- cause:
  - The identical output is the improvement gate refusing a pass that did not improve (`py_router/route.py:9187-9195`), as designed. The pass did run.
  - The skill already hedges. `plan-pcb-routing/SKILL.md:1836-1843` says "historically descend" and that the near-free property depends on the Step 5a gate and on pour re-oracle cost. `:1855` covers what to do "when the all-nets passes stop descending" (switch to scoped laps).
  - The "made it worse" case (`exp/r5s6c09`): blocking stayed 9 → 9 (drc 1→0, broken 8→9). The gate accepted with `disconnected_pads 8→8` while board_score counts +3V3 broken (2 components, no stranded pad). That is a gate-versus-board_score disagreement on a copper island. I did not verify it further; it is a side note, not this cluster's claim.
- branch head 86b54a1d: plan-pcb-routing SKILL.md unchanged. main 0523df20: same text (`:1810-1813`).
- upstream: none on this; #1114 and #1032 (closed) are gate-scope relatives; searches: "plateau iteration", "improvement gate reverted", "all-nets iteration no-op".
- severity after verification: none (at most a wording nit in the skill's "near-free")

### L13 -- VERDICT: CONFIRMED-PARTIAL
- repro at 8328f157: I re-graded the teammate's routed boards with `check_impedance.py --nets <the 9 globs from REPORT.md:33>` (`B12/L13/`):
  - `work/expD/route.kicad_pcb` (91/60/1 signal segments on GND-In1, +5V-In3 and GND-In4) gives 36 nets analysed, 8 with a crossing, 24 crossings, 20.616 mm over a void;
  - `work/expG/route.kicad_pcb` (In1/In4 empty, 6 segments on In3) gives 0, 0, 0.000 mm.
  
  Evidence is from one board, and its experiments are confounded with H06's duplicated GND zones (experiment C still scored 25 with the layers forbidden).
- cause:
  - The DENSE recipe in `.claude/skills/plan-pcb-routing/SKILL.md:1160-1161` and `:1784-1787` prices the GND reference at 6.0 and rails at 2.5, which lets signals onto reference layers.
  - The same skill's high-speed rule (`:2251-2255`) says to keep one solid "(not split, not track-fragmented)" GND plane under every high-speed layer. The two are never reconciled for impedance nets.
  - So "the skill never says" is overstated: the continuity rule is there. What is missing is the link to the grade. `--impedance-nets` (`plan-pcb-placement/SKILL.md:44`) is listed without saying it grades reference-plane continuity; only `board_score.py:858` says so.
- branch head 86b54a1d: plan-pcb-routing SKILL.md unchanged. main 0523df20: same text (`:1143`, `:1757`, `:2222`).
- upstream: new; #486 (closed) added the continuity check itself; searches: "layer-costs impedance reference plane", "impedance reference plane fragmented", "DENSE layer costs GND 6.0".
- severity after verification: LOW
- issue draft:
  title: plan-pcb-routing: the DENSE layer-price recipe lets signals onto impedance reference planes, which the declared-impedance grade then fails
  body: The DENSE recipe prices the solid GND plane at 6.0 and rail layers at 2.5, so signals still cross them. `board_score --impedance-nets` (check_impedance) grades reference-plane continuity, and the skill's own high-speed rule says the reference must not be "track-fragmented", but the recipe does not apply that rule to impedance-controlled boards. On CM5_MINIMA_3: `wk/gp14/08_CM5_MINIMA_3/work/expD/route.kicad_pcb` (signals on GND In1/In4 and +5V In3) grades 8 nets / 24 crossings; `work/expG/route.kicad_pcb` (In1/In3/In4 forbidden with `--layer-costs … -1 …`) grades 0. Repro: `python3 -X utf8 py_tools/check_impedance.py <board> --nets '/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*'`. One board only. Expected: the skill says that when `--impedance-nets` is declared, the reference layers under those nets get a negative (forbidden) cost, not 6.0/2.5, and that the impedance component grades plane continuity.

### L14 -- VERDICT: CONFIRMED
- repro at 8328f157:
  - `.claude/skills/plan-pcb-placement/SKILL.md:432-433` says "stage each join with `py_tools/check_join.py` and stamp it `(locked yes)`".
  - `check_join.py --help` has only `--width/--via-size/--via-drill/--keep-staged/-q`, and no commit or lock option. Its staged board is built with `generate_segment_sexpr` (`check_join.py:159-161`), whose signature (`kicad_writer.py:326`) has no lock parameter.
  - The only `(locked yes)` stampers in the tree are footprint ones (`seeder.stamp_locked`, `pose_ops.apply_locks:1098`, the `place_pose lock` verb). No tool locks a segment or via, so the stamp must be a hand text edit. #1158 shows that misplacing it used to make the segment vanish from the parser.
- cause: the skill names a step that no tool performs (`check_join.py` stages only; `kicad_writer.generate_segment_sexpr` cannot emit a lock).
- branch head 86b54a1d: same text at plan-pcb-placement SKILL.md:732-733, check_join unchanged. main 0523df20: the same instruction in `pcb-free-agent/SKILL.md:345-350` (with the rationale "the plane repair rips unlocked hand joins").
- upstream: new; #1158 (closed) is related, on hand-lock parse fragility; searches: "check_join lock", "locked yes segment", "lock hand-written join", "stamp locked track".
- severity after verification: LOW
- issue draft:
  title: Skill says to stamp hand-written joins `(locked yes)`, but no tool commits or locks a segment
  body: plan-pcb-placement (and pcb-free-agent on main) says "stage each join with `py_tools/check_join.py` and stamp it `(locked yes)`", because plane repair rips unlocked hand joins. check_join only verifies. Its `--keep-staged` copy is written through `kicad_writer.generate_segment_sexpr`, which has no lock option. The only lock stampers in the tree are for footprints (`place_pose lock`, `seeder.stamp_locked`). So the stamp is a hand text edit, the position #1158 showed is fragile, and board 14's four 0.05 mm joins (`wk/gp14/14_imx6ulz_4l`) shipped unlocked. Expected: `check_join.py --commit OUT [--lock]` (or a `lock_copper` tool) that writes the verified join with `(locked yes)` at the writer's canonical position, and skill text that names it.

