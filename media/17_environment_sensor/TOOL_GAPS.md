# TOOL_GAPS -- gpm board 17 (environment_sensor)

Ranked by what each cost this run. Every repro runs from WT
(`~/Documents/git/krt-gpm`, with `export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`)
on inputs copied into `wk/gpm/17_environment_sensor/repro/`.

## 1. The seed judge cannot see a declared spec, so it kept a seed that can never be DONE

- **Tool / command:** `py_placer/judge_seeds.py wk/gpm/17_environment_sensor/judge.json --chain judge_chain.txt --intent intent_run.json --seeds 5,3,0` (which scores each seed with `py_tools/quick_score.py`), as SKILL.md §3.7 prescribes.
- **What it claimed:** "best seed 3: keep its placement s3.kicad_pcb" (seed 3: blocking 0, vias 108; seed 5: blocking 1, ranked last).
- **What was true:** the board declares the USB pair impedance-controlled (route_diff `--impedance 90`, netclass `90Ohm-diff_USB`), and DONE is graded with `--impedance-nets '/USB_D_*'`. `quick_score.py` has no `--impedance-nets` (its only options are `--intent`, `--baseline`, `--json`) and `judge_seeds.py` has no way to pass a spec flag, so the judge ranked seeds blind to it. Full (non-quick) routes of the same chain, measured with the spec:
  - seed 3 (judge best): blocking **2** (impedance: USB pair single-ended on B.Cu, 11 crossings of In2 voids), vias 143;
  - seed 0: blocking **2** (impedance), vias 164;
  - seed 5 (judge last): blocking **0**, check_complete DONE, vias 147.
  The kept placement had to be changed by hand from 3 to 5 after a wasted full route, three placement/route experiments on seed 3 (D5 turn, F.Cu-only diff, qfn_fanout stubs) and two more full chains (~20 min). SKILL.md §3.7 says nothing about specs the quick route cannot grade.
- **Repro:**
  ```
  zsh wk/gpm/17_environment_sensor/repro/full_chain.sh wk/gpm/17_environment_sensor/repro/s3.kicad_pcb wk/gpm/17_environment_sensor/repro/out_s3   # BLOCKING=2 ... impedance=2
  zsh wk/gpm/17_environment_sensor/repro/full_chain.sh wk/gpm/17_environment_sensor/repro/s5.kicad_pcb wk/gpm/17_environment_sensor/repro/out_s5   # BLOCKING=0
  python3 -X utf8 py_tools/quick_score.py --help    # no --impedance-nets
  ```
  (full_chain.sh hard-codes `intent_run.json` / `fixed.kicad_pcb` from the run folder for its final board_score; both are also in repro/.)
- **gh issue search:** `judge seeds spec flags impedance`, `quick_score impedance`: no issue covers it (closest: #1323, closed, about quick_score's ungraded list in converge).

## 2. route_planes lowered the board's Default clearance 0.15 -> 0.119 for a part no pour covers, in a step that poured nothing

- **Tool / command:** `py_router/route_planes.py in.kicad_pcb 1_planes.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones`
- **What it claimed:** "Zone clearance tightened 0.15 -> 0.119mm so the pour threads U6's via lattice (0.648mm pitch, 0.3mm vias ...)", then `PROJECT_WRITES_JSON ... rules.min_clearance: 0.15 -> 0.119 mm ... net_class[Default].clearance: 0.15 -> 0.119 mm`.
- **What was true:** every existing zone was KEPT (four "keeping it" notes), so no pour was made at all; and U6 (BME280, LGA-8) sits at (205.0, 119.8), inside the NE sensor island that both designer zones exclude (GND polygon and +3V3 polygon stop at x 197.95 / y 123.65), and has no vias. The written Default class (0.119) then capped every later `--clearance-ceiling 0.15` step, so the whole board routed at 0.119 instead of the authored 0.15 (later descents reached 0.1), and `check_complete --authored-from` grades the delivered board UNSOUND for the clearance descent. Same line on a plain (non-skip) run.
- **Repro:**
  ```
  python3 -X utf8 py_router/route_planes.py wk/gpm/17_environment_sensor/repro/final.kicad_pcb wk/gpm/17_environment_sensor/repro/planes_skip.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones 2>&1 | grep -E "tightened|keeping it|PROJECT_WRITES"
  ```
- **gh issue search:** `zone clearance tightened via lattice`, `route_planes zone clearance tightened`, `pour clearance lowered no zone`: none.

## 3. fill_for_delivery's KiCad 10 re-save turned a DONE board into blocking 96 (vias in paste)

- **Tool / command:** `py_tools/fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` (§3.9 step 2), then `board_score ... --impedance-nets '/USB_D_*'`.
- **What it claimed:** `Filled ... EXIT=0`; the routed and labelled boards graded blocking 0 / DONE (check_drc: "96 undeclarable in this file format (accepted)").
- **What was true:** the input board is KiCad 9 format (`version 20241229`); the fill saves KiCad 10 (`version 20260206`), where the protection tokens are declarable, so the same 96 vias under solder become 96 undeclared violations: `BLOCKING=96 (... drc_via_in_paste=96)`, check_complete INCOMPLETE. Workaround used: `kicad-cli pcb upgrade` on the chain's input copy (`final_route/in.kicad_pcb`) before the route chain; route.py then stamps Type VII on all 96 ("96 filled+capped (accepted)") with identical copper (vias 147, copper 847.36), and the filled delivery grades DONE. The upgrade is a kicad-cli step, which the redo recorder does not record (added to redo_commands.sh by hand). Cost: one full re-route and re-delivery (~6 min).
- **Repro:**
  ```
  python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/17_environment_sensor/repro/labelled_k9.kicad_pcb -o wk/gpm/17_environment_sensor/repro/delivered_k9.kicad_pcb
  python3 -X utf8 py_tools/board_score.py wk/gpm/17_environment_sensor/repro/delivered_k9.kicad_pcb --intent wk/gpm/17_environment_sensor/repro/intent_run.json --baseline wk/gpm/17_environment_sensor/repro/fixed.kicad_pcb --impedance-nets '/USB_D_*' --quiet | grep BLOCKING   # drc_via_in_paste=96
  ```
- **gh issue search:** `fill_for_delivery via-in-paste undeclarable format`: **#1367** (open) covers it.

## 4. route_diff's single-ended fallback ships an impedance pair over reference-plane voids

- **Tool / command:** `py_router/route_diff.py 1_planes.kicad_pcb 2_diff.kicad_pcb --nets '/USB_D_*' --track-width 0.1 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --impedance 90 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0` on seed 3.
- **What it claimed:** `single_ended_diff_pairs: ["/USB_D"]`, "SE fallback: 2/2 member net(s) routed" (honest about the fallback), and net_impedance recorded for both nets.
- **What was true:** the leg from U1 (0.5 mm-pitch QFN) "escape direction blocked at every setback", the coupled route failed, and the fallback laid both members ~12 mm on B.Cu over In2, whose +3V3 pour stops at x 169.7 and is carved by via antipads: `check_impedance`: 9 segments / 11 crossings over voids, 6.45 mm. The fallback has no reference-plane cost, so a pair it records as impedance-controlled is routed where the impedance grade must block it. The same happened with `--layers F.Cu` only (0/2 routed) and with `qfn_fanout` stubs on U1 (the D5->U1 leg still failed).
- **Repro:**
  ```
  python3 -X utf8 py_router/route_diff.py wk/gpm/17_environment_sensor/repro/s3_1_planes.kicad_pcb wk/gpm/17_environment_sensor/repro/s3_diff.kicad_pcb --nets '/USB_D_*' --track-width 0.1 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --impedance 90 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 | grep -E "SE fallback|Diff pairs"
  python3 -X utf8 py_tools/check_impedance.py wk/gpm/17_environment_sensor/repro/s3_diff.kicad_pcb --nets '/USB_D_*' --verbose --exit-zero | grep -A14 "Reference-plane"
  ```
- **gh issue search:** `single-ended fallback impedance crossing`, `route_diff single-ended fallback reference plane void`, `route_diff polarity mismatch USB-C`: #486 (closed: reference-plane continuity check added), #90 (closed: USB-C dual-row pairs); neither covers the fallback routing over voids.

## 5. analyze_power_paths recommends widths no 0402/0.5 mm-pitch board can carry

- **Tool / command:** `/analyze-power-nets` Steps 1-6 (inline Python; saved as `helpers/power_classify.py`).
- **What it claimed:** `--power-nets-widths 2.0 0.7 0.5 1.0 0.7 0.7 0.7` for GND, +5V, /VBUS, +3V3, VDDA, VBAT, GNDREF; traced "Path 1: J1 -> U6, Nets: GND -> GNDREF, Via: FB1".
- **What was true:** worst-case currents are ~0.35 A on +5V/+3V3 and microamps on VBAT (a coin cell), ~60 mA on VDDA; the sensors' GND/+3V3 must cross a 2 mm bridge to the NE island, which a 2.0 mm GND track cannot do. The traced "GND -> GNDREF" path is a shield bead, not a power path. Widths used instead (a judgment): 0.5 / 0.5 / 0.5 / 0.5 / 0.3 / 0.3 / 0.3.
- **Repro:** `python3 -X utf8 wk/gpm/17_environment_sensor/helpers/power_classify.py wk/gpm/17_environment_sensor/repro/fixed.kicad_pcb | tail -12`
- **gh issue search:** `analyze_power_paths width`: **#1377** (open) covers the over-sizing.

## 6. SKILL §3.5 cannot read a datasheet on this machine (no poppler), and names no fallback

- **Tool / command:** the Read tool with `pages` on a downloaded PDF; `pdftotext` / `pdftoppm` as §3.5 suggests.
- **What it claimed:** §3.5: "download it ... and open it with the Read tool and `pages`".
- **What was true:** `Read` refuses ("pdftoppm is not installed"); `pdftotext`, `pdftoppm`, PyMuPDF and pypdf are all absent; WebFetch of the PDF returns compressed streams. Workaround: macOS `qlmanage -t -s 2400` renders page 1 of the PDF to PNG (used for the GCT USB4105 drawing: PCB edge flush with the shell front, so no `overhang_mm` row was needed). Multi-page datasheets remain unreadable.
- **Repro:** `which pdftotext pdftoppm; python3 -c "import fitz" ; python3 -c "import pypdf"` (all fail).
- **gh issue search:** `poppler pdftotext datasheet`: **#1417** (open) covers it.

## 7. The STANDARD-tier plane map ("inner-only, no outer floods") cannot be executed on this board

- **Tool / command:** plan-pcb-routing Step 5a-tuned (STANDARD: inner-only pours) with `route_planes.py --nets GND +3V3 --plane-layers In1.Cu In2.Cu`.
- **What it claimed:** the skill prescribes inner-only pours for a 4-layer, 89-net board.
- **What was true:** the board's GND pour is ONE zone on F.Cu+B.Cu+In1.Cu. route_planes: "it is ONE multi-layer zone that also covers B.Cu, F.Cu ... so it cannot be replaced ... Keeping it and pouring the new plane over it"; no chain tool deletes a zone, so the outer floods stay whatever the plan says. This run kept the designer's pours as drawn (`--skip-existing-zones`, the README calls them design intent) and noted the deviation from the skill.
- **Repro:** `python3 -X utf8 py_router/route_planes.py wk/gpm/17_environment_sensor/repro/final.kicad_pcb wk/gpm/17_environment_sensor/repro/inner_only.kicad_pcb --nets GND +3V3 --plane-layers In1.Cu In2.Cu | grep -A1 "multi-layer zone"`
- **gh issue search:** `outer flood existing zone inner-only skip-existing-zones`, `multi-layer zone cannot be replaced`: #1299 (closed, about replacing it when every layer is poured); nothing about the skill's map being unexecutable.

## 8. manifest_to_plan rejects the plain redirects the skill says to use in plan.sh

- **Tool / command:** `python3 tests/stress/manifest_to_plan.py final_plan.sh -o final_plan.json`
- **What it claimed:** plan-pcb-routing "Capture Logs": "In the plan file use a plain redirect, `> /tmp/step.txt 2>&1`" (route_plan_check also passes R02).
- **What was true:** `command 2: route_diff.py rejects its arguments: ... --layer-costs: invalid float value: '>'`; 2 of 5 steps dropped. Converting the recorded `redo_commands.sh` instead (no redirects) gives all 5 steps.
- **Repro:** `python3 tests/stress/manifest_to_plan.py wk/gpm/17_environment_sensor/repro/plan_with_redirects.sh -o wk/gpm/17_environment_sensor/repro/plan.json 2>&1 | grep -E "rejects|skipped"`
- **gh issue search:** `manifest_to_plan redirect`, `plan.sh redirect manifest_to_plan`: none.

## 9. kicad_drc_compare reports kicad=0 CONSISTENT while KiCad reports 3 edge-clearance errors

- **Tool / command:** `python3 -X utf8 tests/stress/kicad_drc_compare.py delivered.kicad_pcb --baseline environment_sensor.kicad_pcb`
- **What it claimed:** `kicad=0 check_drc=0 ... [#408: -3 kicad / -3 check_drc intentional edge] ... CONSISTENT`.
- **What was true:** `kicad-cli pcb drc --refill-zones` reports 3 `copper_edge_clearance` errors (actual 0.1978 mm vs 0.2000) on two GND F.Cu tracks and one I2C_1_SDA B.Cu track at the internal-cutout arc (198.95, 118.45). check_drc accepts them as `quantization-margin` (2.2 um), and the compare drops them under the #408 "intentional edge" label. 2 um is fab noise, but the delivered board opens in KiCad with 3 DRC errors and the compare's label names the wrong reason. Re-routing with `--board-edge-clearance 0.22` moved no copper and raised the project's edge floor (board_score then graded drc=3), so it was not kept.
- **Repro:** `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/17_environment_sensor/repro/delivered.kicad_pcb --baseline wk/gpm/17_environment_sensor/repro/fixed.kicad_pcb | grep "kicad="` and `kicad-cli pcb drc wk/gpm/17_environment_sensor/repro/delivered.kicad_pcb --refill-zones --format json -o wk/gpm/17_environment_sensor/repro/d.json` (3 copper_edge_clearance).
- **gh issue search:** `kicad_drc_compare intentional edge quantization`: **#1404** (open) covers it.

## 10. place_pose reports `legal: false` for a no-worse move on any non-rectangular outline

- **Tool / command:** `py_placer/place_pose.py final.kicad_pcb out.kicad_pcb --intent intent_run.json set R5 181.5042 123.8039 --rot 90 set R6 184.4048 128.5549 --rot 0`
- **What it claimed:** `"legal": false` (exit 0, written).
- **What was true:** `no_worse: true`, every conflict count 0 -> 0; `legal` is false only because `pad_edge` is "incomplete": 323 pads "outline uses sampled perimeter check" (this outline has a notch and an L cutout). check_assembly: buildable.
- **Repro:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/17_environment_sensor/repro/final.kicad_pcb wk/gpm/17_environment_sensor/repro/turn.kicad_pcb --intent wk/gpm/17_environment_sensor/repro/intent_run.json set R5 181.5042 123.8039 --rot 90 | grep -o '"legal": [a-z]*'`
- **gh issue search:** `place_pose legal false outline sampled`: **#1326** (closed) says `legal` is unreachable on a non-rectangular outline; the behaviour is still there.

## Helpers written (each is part of an entry above)

- `helpers/full_chain.sh` -- replays the final route chain (non-quick) on any placement and grades it with the impedance spec (entry 1: the judge cannot).
- `helpers/route_variant.sh` -- replays the route.py x3 tail with one knob changed for post-DONE A/B; no repo tool replays a chain tail with an override.
- `helpers/power_classify.py` -- the /analyze-power-nets inline session saved for entry 5's repro.

## 11. check_floorplan exits 4 on the finished board at 0 errors, so grade.py reports `floorplan_pass: false`

- **Tool / command:** `python3 -X utf8 py_tools/check_floorplan.py delivered.kicad_pcb --intent intent_run.json --allow-routed`; `scripts/grade.py ... --mode full`.
- **What it claimed:** `0 error(s), 6 warning(s)` ... `NOT FULLY GRADED: 2 budget_abstained, 1 rules_skipped_armed ... an absent verdict, not a clean one. EXIT=4`; grade.py: `"floorplan_errors": 0, "floorplan_pass": false, "check_floorplan_rc": 4`.
- **What was true:** the two abstained budgets (`oob_count`, `overlap_area`) were withheld by the emitter because the INPUT was a pile ("its off-board count is staging, not a baseline (#1103)"); the delivered board is fully placed, buildable, and has 0 floorplan errors, but no placement can ever make the given (read-only) intent grade complete. Not acted on (the intent is the user's); reported here and in REPORT.md.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/17_environment_sensor/repro/delivered.kicad_pcb --intent wk/gpm/17_environment_sensor/repro/intent_run.json --allow-routed | tail -3`
- **gh issue search:** `budget_abstained pile NOT FULLY GRADED`: **#1420** (open) covers it.
