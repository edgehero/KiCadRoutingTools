# TOOL_GAPS -- gpm board 10 glasgow_revC

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gpm`) with the venv's `python3`; the boards it
needs are copied into `wk/gpm/10_glasgow_revC/repro/`.

No helper scripts were written (`helpers/` is empty). `repro/power_paths_repro.py`
is the analyze-power-nets skill's own Step 1-5 python, saved only to reproduce
gap 5.

---

## 1. fill_for_delivery turns a DONE board into a blocking-356 board: the KiCad 10 re-save makes 356 "undeclarable" vias in paste declarable, and unprotected

- **Tool / command:** `py_tools/fill_for_delivery.py routed.kicad_pcb -o delivered.kicad_pcb` (skill §3.9 step 2), on a board whose file is KiCad 8 format (`(version 20240108)`, as the input board is).
- **What it claimed:** `Filled: ... unconnected (no --refill-zones): 181 -> 0`, exit 0 -- the deliverable.
- **What was true:** the routed board grades `board_score` BLOCKING=0 and `check_complete` DONE; `check_drc` on it reports `344-356 undeclarable in this file format (accepted; Type VII belongs on the fab drawing)`. The filled copy is written by KiCad 10's pcbnew (`(version 20260206)`), the vias can now carry IPC-4761 tokens and none does, so the same copper grades `BLOCKING=356 (drc_via_in_paste=356)`, `check_complete` INCOMPLETE, `check_drc` `Vias in a solder-paste opening: 356 unprotected (violations)`. Nothing in fill_for_delivery or in the skill warns that the format upgrade changes the grade. The fix that worked: `kicad-cli pcb upgrade final.kicad_pcb` BEFORE the routing chain, so bga_fanout / route_diff / route.py stamp Type VII on the vias they add (measured on the fanout step: `0 unprotected, 41 filled+capped`), then route the whole chain again (~12 min) and fill.
- **Repro:** `python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/10_glasgow_revC/repro/k8_routed.kicad_pcb -o wk/gpm/10_glasgow_revC/repro/k8_delivered.kicad_pcb` then `python3 -X utf8 py_router/check_drc.py wk/gpm/10_glasgow_revC/repro/k8_routed.kicad_pcb --clearance-margin 0.1` (`356 undeclarable ... (accepted)`) vs the same on `repro/k8_delivered.kicad_pcb` (`356 unprotected (violations)`); `board_score.py <board> --intent wk/gpm/10_glasgow_revC/repro/intent_run.json --baseline wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb --quiet` reads blocking 0 vs 356 (without `--baseline` it does not arm the via-in-paste grade and reads 0 for both).
- **Issues:** "fill_for_delivery via-in-paste format", "undeclarable via in paste KiCad 10", "fill_for_delivery": #1335 (closed: the skills never ran the fill) -- not this.

## 2. place_simple leaves error-graded decap limits broken in every seed, so no seed can be judged as placed

- **Tool / command:** `py_placer/place_simple.py fixed.kicad_pcb 's{seed}.kicad_pcb' --groups groups.json --intent intent_run.json --jobs 4 --json 's{seed}.json'` (pass 1, default weights) and the same with `--decap-limit-weight 50` (pass 2).
- **What it claimed:** the decap limits the intent grades at error (`decaps.max_distance_mm` 4.787, `max_pin_distance_mm` 1.7622) are *priced* ("NOTE: decap limits priced: 146 term(s)"), and pass 2 ends with every seed `buildable`.
- **What was true:** every one of the 12 seeds of each pass ended with 1-14 error-graded decap findings, almost all near-misses that a 0.1-0.4 mm nudge clears: pass 1 seeds 3-14 errors (e.g. `U20 pin 2 (+3V3) is 1.83mm from C55 (limit 1.76mm)`, `C87 is 5.07mm from U36`); pass 2 at `--decap-limit-weight 50` still 1-6 per seed (`floorplan` in `judge.json`: `{'0': 2, '1': 6, '2': 2, '3': 6, '4': 2, '5': 1, '6': 3, '7': 4, '8': 4, '9': 1, '10': 2, '11': 2}`), e.g. s5 `C92 is 4.86mm from U30 (limit 4.79mm)`, s9 one pin at 1.77-1.84 mm. The anneal's final legalisation (overlap lambda ramps to 10^4) pushes caps a hair past the limits it priced. Consequence: skill §3.6 case 2 -- no judged seed is floorplan-clean, so only ONE seed (s5, hand-repaired with one `place_pose`) could be judged; the 6-seed comparison the skill is built on was lost, and a second placing pass (13 min) was spent.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb wk/gpm/10_glasgow_revC/repro/s5.kicad_pcb --groups wk/gpm/10_glasgow_revC/repro/groups.json --intent wk/gpm/10_glasgow_revC/repro/intent_run.json --decap-limit-weight 50 --seed 5 --json wk/gpm/10_glasgow_revC/repro/s5.json` -> log line `1 floorplan error(s) (decap_distance)`; `repro/s5_placed.kicad_pcb` is that output.
- **Issues:** `gh issue list --search "place_simple decap limit"`: #1296 (closed: judge ranks seeds with floorplan errors), #1320 (closed: pin limit wider than the tether radius), #1267 (closed). None covers limits within the radius left broken by the final legalisation.

## 3. The cap pass breaks a decap limit and strands the fanout's same-net stub; route.py's cleanup does not remove it

- **Tool / command:** `py_placer/place_fanout_clearance.py 2_fanout.kicad_pcb 3_caps.kicad_pcb --clearance 0.1 --intent intent_run.json` (plan Step 1c), then `route.py`.
- **What it claimed:** with `--intent` the pass "holds the intent's decap limits no worse per claim"; the board it hands on is "0 unresolved".
- **What was true:** (a) on the first chain it printed `Decap limit broken to clear foreign copper (no clear pose kept it): C78 (decap_pin_distance U30.J6 2.13mm, was -0.05mm)` and `Decap grade (intent): errors 0 -> 1`: the fanout's +3V3 gap via had landed inside C78's GNDPLL0 pad under the BGA, and the only clear pose was past the limit. The judging route then graded the seed `floorplan 1` for a defect the PLACEMENT did not have. Fixed by moving C78 in the placement (`place_pose set C78 82.2 87.08 --rot 180`) and re-running the chain. (b) After that, the pass still moves C78 a little, and the fanout's #1332 stub that ended on C78's old pad is left behind: `check_weird`: `dangling-end: net /VCCPLL0 (B.Cu) at (80.666, 87.575): free end, dangling segment 1.150mm`, `check_orphan_stubs`: 1 orphan -> `check_complete` INCOMPLETE on a board with blocking 0. A `route.py --nets /VCCPLL0 ... GND +3V3` cleanup pass removed a VIOA redundant cycle but kept the stub; `--rip-existing-nets /VCCPLL0` was a no-op on the connected net (it warns); only `--force-reroute` cleared it.
- **Repro:** (a) `python3 -X utf8 py_placer/place_fanout_clearance.py wk/gpm/10_glasgow_revC/repro/c78_2_fanout.kicad_pcb wk/gpm/10_glasgow_revC/repro/c78_3_caps.kicad_pcb --clearance 0.1 --intent wk/gpm/10_glasgow_revC/repro/intent_run.json` -> `Decap limit broken ... C78`. (b) `python3 -X utf8 py_router/check_weird.py wk/gpm/10_glasgow_revC/repro/stub_10_fine.kicad_pcb` -> the /VCCPLL0 dangling end.
- **Issues:** searched "place_fanout_clearance decap limit broken", "orphan stub fanout cap moved", "dangling stub cap moved fanout": none.

## 4. route.py ships a same-net via pair whose drills overlap (hole-to-hole), at the 0.127/0.1/0.45 arm

- **Tool / command:** `route.py 4_diff.kicad_pcb 5_route.kicad_pcb --nets '*' ... --via-size 0.45 --via-drill 0.2 ...` and both iteration passes after it.
- **What it claimed:** JSON_SUMMARY_MIN names failed / open nets only; nothing about the via pair.
- **What was true:** `check_drc`: `VIA-DRILL-HOLE ... Via:+3V3 <-> Via:+3V3 (drill hole clearance) Overlap: 0.176mm Via1: (91.30,85.70) Via2: (91.50,85.80)` -- two +3V3 vias 0.22 mm apart, present in 5_route, 6_iter1 and 7_iter2 (board_score `drc 1`). The shipped arm (grid 0.05, via 0.3) does not have it.
- **Repro:** `python3 -X utf8 py_router/check_drc.py wk/gpm/10_glasgow_revC/repro/vdh_7_iter2.kicad_pcb --clearance-margin 0.1`
- **Issues:** "same-net via hole-to-hole" / "via-drill-hole same net": #1341 (closed: route_diff GND return vias below min_hole_to_hole), #162 (open: same-net redundant copper). Neither is this producer.

## 5. analyze_power_paths traces current backward through regulator outputs and recommends absurd widths

- **Tool / command:** the analyze-power-nets skill's `trace_power_paths` / `get_power_net_recommendations` (py_tools/analyze_power_paths.py).
- **What it claimed:** traced power paths and a width per net from them.
- **What was true:** paths run from one LDO's OUTPUT back through the +5V INPUT net into another LDO's output: `PowerPath(source_component='U14', sink_component='U30', nets_in_path=['+1V2', '+5V', 'Net-(U14-OUT)'], components_in_path=['U36', 'U14'])` (U14 is the bank-B I/O LDO, U36 the 1V2 LDO). With every IC and regulator classified: `+3V3 1.2, +5V 1.2, +1V2 1.2, GND 3.0, /GNDPLL0 1.0, /GNDPLL1 1.0` mm -- a 1 mm track on a 3-pad PLL ground under a BGA. With fewer parts classified the repro gives `+3V3 2.0, +5V 2.0, /GNDPLL1 2.0`. The widths were set by hand from docs/power-nets.md's table at estimated currents (REPORT.md).
- **Repro:** `python3 -X utf8 wk/gpm/10_glasgow_revC/repro/power_paths_repro.py`
- **Issues:** "analyze_power_paths" / "trace_power_paths regulator": none on this.

## 6. Skill §3.6 tells you to read check_assembly without --intent, which gates the declared-pose overlaps everything else waives

- **Tool / command:** `py_tools/check_assembly.py s5.kicad_pcb --baseline fixed.kicad_pcb` (the skill's §3.6 "Check and LOOK" command).
- **What it claimed:** `VERDICT: NOT BUILDABLE` -- `J5 <-> MK2 courtyard 4.0669mm2 side F COURTYARD-BLOCKING`.
- **What was true:** that pair is a declared-pose overlap the intent accepts (`fixed_poses[].accept_courtyard_overlap`); place_simple's own report, judge.json (`assembly 0`) and the verifier's command (which passes `--intent`) all read `buildable (blocking 0)`, `waived 12`. The skill's command, as written, contradicts the run's own judge.
- **Repro:** `python3 -X utf8 py_tools/check_assembly.py wk/gpm/10_glasgow_revC/repro/s5_placed.kicad_pcb --baseline wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb` (NOT BUILDABLE) vs the same with `--intent wk/gpm/10_glasgow_revC/repro/intent_run.json` (buildable).
- **Issues:** #1298 (closed) added `accept_courtyard_overlap`; it does not touch the skill's command line.

## 7. A decap past the limit by 0.07 mm is an ERROR; moved 0.4 mm FURTHER away it is only a warning

- **Tool / command:** `py_tools/check_floorplan.py <board> --intent intent_run.json` (`decap_distance` / `decap_ungraded`).
- **What it claimed:** s5: `[ERROR] decap_distance: C92 is 4.86mm from U30 (limit 4.79mm)`.
- **What was true:** moving C92 from x 94.447 to 94.85 (away from U30) gives `0 error(s)` and only `[warn] decap_ungraded: C92 is 5.26mm from U30 ... beyond the 5.00mm tether search radius`, because C92 is one of the 4 caps the reference keeps beyond 5 mm (`stay warn`). The repair that improves the grade can be the one that makes the design worse.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/10_glasgow_revC/repro/s5_placed.kicad_pcb --intent wk/gpm/10_glasgow_revC/repro/intent_run.json` (1 error) vs `.../repro/s5_c92_far.kicad_pcb` (0 errors).
- **Issues:** "decap_ungraded decap_distance radius": #1142 (closed: decap_ungraded promotion), #1150 (closed). Neither covers the window between the limit and the radius grading harder than beyond it.

## 8. route_planes --skip-existing-zones pours nothing but lowers the project's Default clearance

- **Tool / command:** `py_router/route_planes.py in.kicad_pcb 1_planes.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu --skip-existing-zones`
- **What it claimed:** `Min clearance used: 0.12 mm (below nominal 0.1499; fine-pitch taps) - grading at this floor`, `net_class[Default].clearance: 0.1499 -> 0.12 mm`.
- **What was true:** both zones already existed and were skipped; the step drew no copper and placed no tap ("Bare pour (no track or via drawn)"), yet it wrote a lower DRC floor into the project.
- **Repro:** `python3 -X utf8 py_router/route_planes.py wk/gpm/10_glasgow_revC/repro/final.kicad_pcb wk/gpm/10_glasgow_revC/repro/planes_out.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu --skip-existing-zones`
- **Issues:** "route_planes skip-existing-zones": #1329 (closed: replacing a designer's zone), not this.

## 9. impedance.achievability_note says nothing on a board with KiCad's default stackup

- **Tool / command:** `impedance.achievability_note(pcb, 'F.Cu', 90.0, is_differential=True, spacing=0.1, ...)` (plan-pcb-routing Step 10 rule 1).
- **What it claimed:** `('', None)`.
- **What was true:** the board carries a `(stackup)` section that is the untouched default (three 0.48 mm dielectrics, er 4.5), which the skill tells you to treat as "no stackup"; the function only answers when the section is absent. The numbers had to be computed with `calculate_width_for_impedance` by hand: 90 ohm USB 0.41 mm legs, 100 ohm LVDS 0.32 mm legs at a 0.1 mm gap.
- **Repro:** `python3 -c "import sys; sys.path.insert(0,'py_router'); from kicad_parser import parse_kicad_pcb; from impedance import achievability_note; print(achievability_note(parse_kicad_pcb('wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb'),'F.Cu',90.0,is_differential=True,spacing=0.1))"`
- **Issues:** "achievability_note stackup": none.

## 10. route_diff routes the USB pair mostly INSIDE the GND plane layer, and nothing on the DONE path sees it

- **Tool / command:** `py_router/route_diff.py 3_caps.kicad_pcb 4_diff.kicad_pcb --nets '/IO_Banks/Z*' '/USB_P' '/USB_N' --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --via-size 0.4 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0` (In1.Cu is the board's solid GND pour, priced 6x as plan-pcb-routing Step 5a-tuned says).
- **What it claimed:** `/USB` in `routed_diff_pairs`; board_score / check_complete later DONE (diff_pairs, impedance ungraded: no spec).
- **What was true:** of the USB pair's copper, `/USB_N` 28.1 mm and `/USB_P` 25.1 mm run on In1.Cu (vs 10.3 / 5.1 mm on F/B), i.e. ~80% inside the GND plane layer, cutting it; LVDS 64.6 mm on In1.Cu. The verifier's check_impedance pass: USB_N 68.7% and USB_P 80.5% of length over a reference-plane void, intra-pair skew 10.58 mm. The 6x price did not keep the most sensitive pair off the plane layer, and no gate on the DONE path reports it unless the board declares an impedance/diff-pair spec.
- **Repro:** measure per-layer length on `wk/gpm/10_glasgow_revC/repro/usb_4_diff.kicad_pcb` (the route_diff output): `python3 -c "import sys,math,collections; sys.path.insert(0,'py_router'); from kicad_parser import parse_kicad_pcb; p=parse_kicad_pcb('wk/gpm/10_glasgow_revC/repro/usb_4_diff.kicad_pcb'); n={i:x.name for i,x in p.nets.items()}; L=collections.Counter(); [L.update({(n[s.net_id],s.layer):math.hypot(s.end_x-s.start_x,s.end_y-s.start_y)}) for s in p.segments if n.get(s.net_id,'').startswith('/USB_')]; print(L)"`; and `python3 -X utf8 py_tools/check_impedance.py wk/gpm/10_glasgow_revC/repro/delivered.kicad_pcb --nets '/USB_*'`.
- **Issues:** "route_diff inner plane layer GND diff pair layer-costs": none on this.

## 11. check_complete --authored-from lists the track/via/hole floors it lowered but not the clearance it lowered

- **Tool / command:** `check_complete.py delivered.kicad_pcb --intent intent_run.json --baseline glasgow_revC.kicad_pcb --authored-from glasgow_revC.kicad_pcb`
- **What it claimed:** `UNSOUND -- ... (track width 0.15 -> 0.0889, via diameter 0.4 -> 0.25, hole diameter 0.2 -> 0.15)`.
- **What was true:** the two projects also differ in the net classes' clearance (`Default` and `Power` 0.1499 -> 0.09) and `min_hole_clearance` (0.25 -> 0.09) -- the clearance the whole board's DRC now grades at; the verifier measured 2540 check_drc violations at the input's 0.1499. The one floor that decides whether this copper is legal at the authored rules is the one the disclosure leaves out (found by the verifier, confirmed by reading both `.kicad_pro`).
- **Repro:** `python3 -X utf8 check_complete.py wk/gpm/10_glasgow_revC/repro/delivered.kicad_pcb --authored-from wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb` and compare `net_settings.classes[].clearance` in `repro/fixed.kicad_pro` and `repro/delivered.kicad_pro`.
- **Issues:** "authored-from clearance netclass lowered": #900 (closed: pad-override cap into the net class), not this.

## 12. check_orphan_stubs / check_weird say clean; KiCad reports 3 dangling tracks on the same board

- **Tool / command:** `py_tools/check_orphan_stubs.py delivered.kicad_pcb`, `py_router/check_weird.py delivered.kicad_pcb` (both: none) vs `kicad-cli pcb drc delivered.kicad_pcb --severity-all`.
- **What it claimed:** `NO ORPHAN STUBS FOUND!`, `NO WEIRD THINGS FOUND!`; `check_complete` DONE (its orphan/weird instruments clean).
- **What was true:** KiCad 10.0.7 DRC: `track_dangling` x3 -- `+3V3` F.Cu 0.354 mm at (74.2, 112.6), `/IO_Banks/QA6` F.Cu 0.875 mm at (88.64, 87.53), `/IO_Banks/Z0_N` In1.Cu 0.600 mm at (84.56, 78.6). `kicad_drc_compare` reads CONSISTENT because it compares copper classes only.
- **Repro:** `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc wk/gpm/10_glasgow_revC/repro/delivered.kicad_pcb --severity-all --format json -o wk/gpm/10_glasgow_revC/repro/delivered_kdrc.json` then count `track_dangling`; `python3 -X utf8 py_tools/check_orphan_stubs.py wk/gpm/10_glasgow_revC/repro/delivered.kicad_pcb`.
- **Issues:** "track_dangling check_orphan_stubs kicad": none.
