# TOOL_GAPS -- gpm board 08 CM5_MINIMA_3

Ranked by what each cost this run (wall time and passes). Every repro command
runs from the worktree root (`~/Documents/git/krt-gpm`) with the venv
python first on PATH; the inputs it needs are copied into
`wk/gpm/08_CM5_MINIMA_3/repro/`.

---

## 1. Nothing models a card or module that covers the board: place_simple seats tall parts under the declared M.2 card (skill gap)

- **Tool / step:** `py_placer/place_simple.py` with the given intent; plan-pcb-placement §3.1/§3.4 (no step asks what a declared mezzanine covers).
- **What it claimed:** pass 2 placed all 12 seeds legal, buildable and floorplan-clean (`judge.json` named seeds 8, 0, 2, 11, 7, 4).
- **What was true:** the intent declares the M.2 socket J701 (113.6, 30.725) and the 2242 standoff M702 (113.6, 70.85), i.e. a 22 x 42 mm card over x 102.6-124.6, y 34-72. Nothing in the toolchain turns that into an occupied volume (J701's footprint draws only the socket; `keepouts` is empty by design), so pass 2 seed 8 put the 3.1 mm XAL5030 inductor L701, the 3225 oscillator U703, C708-C711 and the FPC connector J802 under the card. Likewise CN1 (a 2.9 mm JST-SH battery connector) was seated under the CM5 module body on B (check_assembly reports it only as `pads_under_body ... advisory`, `gate_exempt: silk_drawn`). I had to add a keep-out by hand (intent_run.json `keepouts[0]`), iterate its `allow` list twice (pass 3 too crowded with a strict keep-out; pass 4 split the buck template at the keep-out edge), and move CN1 by hand at the end.
- **Cost:** passes 2, 3, 4 and 5 (four placement passes and one judge, about 35 min), plus a final re-route for the CN1 move.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/08_CM5_MINIMA_3/repro/fixed.kicad_pcb wk/gpm/08_CM5_MINIMA_3/repro/nokeep_s8.kicad_pcb --groups wk/gpm/08_CM5_MINIMA_3/repro/groups.json --intent wk/gpm/08_CM5_MINIMA_3/repro/intent_nokeepout.json --seed 8` then list the F-side parts whose centre lies in [102.6,34]-[124.6,72] (L701 among them).
- **gh issue search** ("M.2 card", "mezzanine module body keep-out", "keep-out under module"): no issue covers it.

## 2. The DENSE routing recipe lets tracks onto the reference planes; the impedance grade then blocks 9-16 nets (skill gap, known)

- **Tool / step:** plan-pcb-routing Step 5a-tuned / Step 2c layer prices (GND plane 6.0, rails 2.5) with `board_score --impedance-nets` (the board declares 100/90 ohm classes).
- **What it claimed:** the recipe is "measured-optimal"; route.py routed with `--layer-costs 1.0 6.0 1.0 2.5 6.0 1.0` and reported its tally.
- **What was true:** board_score's impedance component (check_impedance reference-plane continuity) blocked 9 nets on the first full route (36 segments over a void, 29.5 mm) and 16 on the stub-fanout chain (59 crossings, 37.9 mm): tracks on In1/In3 (33 + 40 mm) and via fields void the planes under F.Cu/In2.Cu pairs. Forbidding tracks on In1/In3/In4 (`--layer-costs 1.0 -1 1.0 -1 -1 1.0`) took impedance 16 -> 0 with completion intact (trial C, blocking 23 -> 10).
- **Cost:** two full chains (about 10 min) and the diagnosis.
- **Repro:** `python3 -X utf8 py_tools/check_impedance.py wk/gpm/08_CM5_MINIMA_3/repro/trialB_route.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK*' '/CM5/DPHY0_P.*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/USB2P.D_*' '/USB_C.D_*'` (16 nets with a crossing).
- **gh issue search** ("impedance reference plane layer costs"): #1359 "plan-pcb-routing: the DENSE layer-price recipe lets signals onto impedance reference planes, which the declared-impedance grade ..." (CLOSED) covers it; the skill text on main still prescribes 6.0 / 2.5.

## 3. plan-pcb-routing prescribes `qfn_fanout --escape-method underpad --allow-via-in-pad` for CM4/CM5 connectors; at the board's 0.45 mm via floor it drops pads, and the plain stub escape is what works (skill gap)

- **Tool / step:** plan-pcb-routing Step 3 ("Dense 2-row mezzanine/card-edge connectors at 0.4mm (CM4/CM5, 200+ pads) DO benefit -- use qfn_fanout.py --escape-method underpad --allow-via-in-pad").
- **What it claimed:** that recipe escapes the connector.
- **What was true:** on Module302 (0.4 mm, 2 x 50) with the board's `min_via_diameter` 0.45: `underpad` escaped 18/38 nets, `underpad --allow-via-in-pad` 35/38, `stub` 38/38 with 0 grazes (Module301 likewise 38/38). Without any fanout the first full route left 12 nets failed at the connector rows; with the stub fanout 3.
- **Cost:** one chain without fanout (blocking 29 -> 28 after iterations) before trying it.
- **Repro:** `python3 -X utf8 py_router/qfn_fanout.py wk/gpm/08_CM5_MINIMA_3/repro/s1_pour.kicad_pcb --component Module302 --nets '*' --escape-method underpad --allow-via-in-pad --via-size 0.45 --via-drill 0.3 --width 0.1 --escalation board --output /tmp/x.kicad_pcb` (JSON_SUMMARY escaped 35 failed 3) vs `--escape-method stub` (38 / 0).
- **gh issue search** ("qfn_fanout underpad connector", "stub fanout CM4"): #410, #164, #195 concern underpad features; none covers the recipe's choice for a 0.45 mm via floor.

## 4. place_simple leaves a template member 19-24 mm off its datasheet pose, and the judge ranks that seed first (tool)

- **Tool / command:** `place_simple.py` (template weight 100/mm) + `judge_seeds.py`.
- **What it claimed:** pass 5 seed 0 ranked best (blocking 6), `check_floorplan` 0 errors.
- **What was true:** seed 0 left 4 of 9 U702 template members off the AP3441 template, worst C709 at 24.27 mm, ground return 25.9 mm (`template`, `template_ground_return` are WARN only); pass 4 seed 10 (judge's best) left L701 19 mm off (LX node ~23 mm long). The judge key reads floorplan errors only, so a broken buck layout wins on a one-join quick-route difference. I kept seed 7 (template worst 1.28 mm) by judgment.
- **Cost:** one extra placement pass (pass 5) and a judgment deviation from `judge_key`.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/08_CM5_MINIMA_3/old/pass4/s10.kicad_pcb --intent wk/gpm/08_CM5_MINIMA_3/repro/intent_pass4.json | grep template` (L701 19.00 mm).
- **gh issue search** ("template member drift keepout"): none.

## 5. Every DONE grader reports 0 DRC while KiCad reports 2 copper-edge errors on pads this run placed (tool)

- **Tool / command:** `board_score.py` (drc 0), `check_complete.py` (DONE), `check_drc.py --baseline --clearance-margin 0.1` (the verifier's prescribed command: "NO DRC VIOLATIONS FOUND!"), and place_simple's declared-pose check.
- **What it claimed:** clean; check_drc prints "Skipping pad-to-board-edge checks (--check-pad-edge is off; pads are edge-exempt by default because on a routed board the hits are usually pre-existing edge connectors)".
- **What was true:** `kicad-cli pcb drc` reports 2 `copper_edge_clearance` errors: J1's shield tabs (Net-(J1-MP1)) at (84.196, 26.985) and (84.196, 45.285), 0.201 / 0.206 mm from the notch edge against the board's 0.372 mm. The input was a pile, so they are not pre-existing; `check_drc --check-pad-edge` finds both. place_simple seated the declared pose without a word (its `refused` named only the H102 courtyard); `place_pose` had printed "pad-edge clearance: 2 -> 2 violations". The verifier failed the board on it. (The pose itself cannot do better: the footprint's 16.2 mm inner tab span vs the outline's 15.79 mm notch caps both gaps at 0.2035 mm.)
- **Cost:** one verifier FAIL; not fixable within the inputs.
- **Repro:** `python3 -X utf8 py_router/check_drc.py wk/gpm/08_CM5_MINIMA_3/repro/routed.kicad_pcb --check-pad-edge --clearance-margin 0.1` (2 PAD-BOARD-EDGE) vs the same without `--check-pad-edge` (0).
- **gh issue search** ("pad edge clearance check_drc"): #1297 (declared poses on pad bounding boxes, CLOSED), #961, #1266 are related edge/pad-grading issues; none covers the default-off pad-edge check on the DONE path. #408 is the intentional edge-connector exemption kicad_drc_compare cites.

## 6. The verifier fails any board whose diff-pair net classes carry no `.kicad_dru` skew rule, and no skill step declares one (skill gap)

- **Tool / step:** verifier.md rule 5 ("If the board declares a class (diff pairs ...) and its component is ungraded, the verdict is FAIL") vs `board_score`'s diff_pairs component, which grades only `.kicad_dru` skew / diff_pair_uncoupled rules ("A board that declares neither is measured, not graded").
- **What was true:** the board's 100ohm/90ohm classes declare pair width/gap, no `.kicad_dru` exists, so board_score `diff_pairs ran=false` and check_complete lists it UNEXAMINED on every board this chain can produce; the verifier FAILed on it (13 of 18 pairs over 0.5 mm skew by its own KiCad-equivalent measure, worst /CM5/PCIE_PI.RX 5.213 mm). Declaring a rule myself (0.15 mm `within_diff_pairs`) and routing with `route_diff --diff-pair-intra-match` left every pair `unmatched`: "Warning: No suitable straight run found for meanders" (board_score diff_pairs 17). Neither plan-pcb-placement nor plan-pcb-routing says to write a skew rule, or what to do when the board declares none.
- **Cost:** a verifier FAIL plus one full chain (trial M, about 6 min).
- **Repro:** copy `wk/gpm/08_CM5_MINIMA_3/repro/skew_rule.kicad_dru` beside a copy of `repro/routed.kicad_pcb` as `<board>.kicad_dru` and run `bash wk/gpm/08_CM5_MINIMA_3/helpers/score.sh <board> /tmp/s.json` (diff_pairs 17); without it diff_pairs is UNGRADED.
- **gh issue search** ("diff pair skew ungraded"): #1134 (P/N self-checks, CLOSED) is the nearest; none covers the verifier/board_score mismatch.

## 7. route.py's cleanup leaves a dangling In2 tail and a stacked duplicate GND via; no tool removes them, so check_complete stays INCOMPLETE (tool; helper written)

- **Tool / command:** `route.py` (end-of-run cleanup), then a scoped `route.py --nets '/CM5/ETH_PI.TRD3_P' '/CM5/DPHY0_P.D2_P' GND +5V ...` whose dead-end sweep the skill relies on.
- **What it claimed:** the scoped pass prints `Dead-end sweep: trimmed 3 dead-end segment(s)` and `JSON_SUMMARY_MIN failed 0`; board_score blocking 0.
- **What was true:** the 0.25 mm In2.Cu tail on the protected pair net /CM5/DPHY0_P.D2_P at (95.65, 55.9)-(95.65, 56.15) survives every pass (check_weird `dangling-end`, check_orphan_stubs 1) and check_complete says INCOMPLETE. Its root is a 0.046 mm soft joint between two overlapping In2 paths of the same net. On the final chain, route.py also shipped two GND vias 0.071 mm apart ((85.25, 53.2) / (85.2, 53.15), joined by a 0.8 mm In2 stub): check_drc `VIA-DRILL-HOLE ... Overlap 0.479mm`, board_score drc 1, and the tidy pass did not remove it. Wrote `helpers/drop_segment.py` (drop a segment or via by uuid) and bridged the exposed soft joint with `check_join.py ... --keep-staged`.
- **Cost:** about 20 min over two chains.
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/08_CM5_MINIMA_3/repro/v3_s4_tidy.kicad_pcb` and `python3 -X utf8 py_router/check_drc.py wk/gpm/08_CM5_MINIMA_3/repro/v3_s4_tidy.kicad_pcb --clearance-margin 0.1`.
- **gh issue search** ("dangling segment diff pair cleanup", "soft joint"): #1166 (dangling via, CLOSED), #1063, #162 (same-net redundant copper, CLOSED) are related; none covers a protected-pair tail or a near-stacked same-net via pair.

## 8. analyze_power_paths sizes every rail a multi-rail sink touches at the sink's whole current (tool)

- **Tool / command:** `py_tools/analyze_power_paths.get_power_net_recommendations` (analyze-power-nets skill Step 5).
- **What it claimed:** +1V8 2.0 mm, /CM5/GPIO_VREF 2.0 mm, +3V3_PI 2.0 mm, VBUS_USB2.0 3.0 mm, M2_3V3 3.0 mm, /PCIe-M2/M2_LX 3.0 mm.
- **What was true:** Module301 was classified as a 3000 mA +5V sink; its +1V8/GPIO_VREF/+3V3_PI pins inherit 3 A (they are module outputs/a reference input of a few mA). VBUS_USB2.0 with a 1500 mA sink reads 3.0 mm (the table gives 1.2 mm for <2 A). A traced "path" U702 -> Module301 over +5V is invented (U702 consumes +5V). I used judgment widths instead.
- **Cost:** small (10 min).
- **Repro:** `python3 -X utf8 wk/gpm/08_CM5_MINIMA_3/repro/power_analysis.py | grep REC`.
- **gh issue search** ("power_net_recommendations", "analyze_power_paths"): none.

## 9. An `edge_connectors[]` entry without `class` is silently not seated, while the grade still grades it as an edge connector (tool)

- **Tool / command:** `place_simple.py` edge seat.
- **What it claimed:** J501 declared on the south edge; the run printed no warning (only a `notes[]` entry in `s<S>.json`: "J501 is declared on the south edge but is not an edge part (no part class): placed as any other part").
- **What was true:** `check_floorplan` graded J501 as declared (`[ERROR] edge_connector: J501 sits nearest the west edge but is declared on the south edge`) and 4 of 12 pass-3 seeds carried that error. Adding `"class": "edge_receptacle"` fixed it.
- **Cost:** one placement pass.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/08_CM5_MINIMA_3/repro/fixed.kicad_pcb wk/gpm/08_CM5_MINIMA_3/repro/noclass_s0.kicad_pcb --groups wk/gpm/08_CM5_MINIMA_3/repro/groups.json --intent wk/gpm/08_CM5_MINIMA_3/repro/intent_noclass.json --seed 0` (NOTE line; JSON floorplan error edge_connector).
- **gh issue search** ("edge seat class"): #1331 "place_simple's edge seat ignores an intent edge_connectors[].class ..." (CLOSED) is the class-read fix; the silent skip with a graded error remains.

## 10. The edge seat cannot express a setback: a negative `overhang_mm.min` never reads (tool / doc)

- **Tool / command:** `place_simple.py` edge seat with `"overhang_mm": {"min": -1.05, "max": 0.0}` (the brief says the source seats J101/USB701 1.05 mm inside the west edge).
- **What it claimed:** "declare overhang_mm.min at the reading where its mating face meets the edge".
- **What was true:** the courtyard reading clamps at 0 ("its overhang reads at least 0.00mm wherever it stands"), so both receptacles were left unseated in every seed of pass 1; the validator accepts the negative value without a word. `max_setback_mm` is the channel, which neither message names.
- **Cost:** half a pass (pass 1 had a second cause too).
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/08_CM5_MINIMA_3/repro/fixed.kicad_pcb wk/gpm/08_CM5_MINIMA_3/repro/negband_s0.kicad_pcb --groups wk/gpm/08_CM5_MINIMA_3/repro/groups.json --intent wk/gpm/08_CM5_MINIMA_3/repro/intent_negband.json --seed 0` (`unseated` in the JSON).
- **gh issue search** ("overhang band setback"): #987, #961 concern band grading; none covers a negative minimum.

## 11. No PDF renderer on this Mac; the skill's datasheet recipe assumes poppler (environment / skill)

- **Tool / step:** plan-pcb-placement §3.5 step 2 (`pdftotext`, `pdftoppm`, `pdfimages` "where poppler is installed"); the Read tool also needs pdftoppm for PDFs.
- **What was true:** none installed; Read on a PDF refuses. Wrote `helpers/pdf_render.swift` (PDFKit: page PNG + text) to read the Kycon GLPLX and Diodes AP3441 / EVB documents.
- **Cost:** about 5 min.
- **Repro:** `which pdftoppm pdftotext` (not found).
- **gh issue search** ("poppler"): none.

## 12. Smaller items

- **judge_seeds chain lines cannot carry an env knob** (`KICAD_PLANE_FRAGILITY_LAYERS`): lines run without a shell; the knob had to be exported in the judge's environment and is not recorded in `judge_chain.txt`, so a re-film needs the comment at its head. gh search "judge_seeds env": none.
- **Step 2d names `--force-reroute` for a pair** ("name BOTH members EXACTLY with --nets P N --force-reroute"); only route.py has the flag (`route_diff.py: error: unrecognized arguments: --force-reroute`), and route.py re-routes the members single-ended. gh search "force-reroute route_diff": #515 (the flag, CLOSED), #677 (OPEN, "A diff pair from an earlier step can wall in later signal nets").
- **check_floorplan `decap_pin_uncovered` warns that U702's LX switch node (pin 6) has no decoupling capacitor** -- LX is not a supply rail. gh search "LX decap": none.
- **The hint "pad Module302.133 is a fanout-dropped ball (no escape stub) ... Re-run the fanout"**: the stub had existed (qfn_fanout escaped 38/38, route_diff's SE fallback connected the net); route.py ripped the member for another net and did not restore it. Re-running qfn_fanout for that pad failed (no room). gh search "fanout-dropped ball": #652, #1311 (CLOSED) related.
- **kicad-cli is not on PATH** (`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`); `kicad_drc_compare.py` and the §3.9 silk check needed PATH extended.
