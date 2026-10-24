# TOOL_GAPS -- 09 StickHub

Ranked by what each cost this run. Every command runs from WT
(`~/Documents/git/krt-gpm`) with the venv python
(`export PATH="$HOME/.venvs/krt/bin:$PATH"`); the boards they need are in
`wk/gpm/09_StickHub/repro/`.

## 1. `place_simple` silently drops a classless `edge_connectors[]` row that `check_floorplan` grades at ERROR

- **Tool / command:** `py_placer/place_simple.py ... --intent <intent with an edge row for C38>` -- C38 is a `CP_Elec_6.3x11_Board_Edge_Mirrored` electrolytic whose can is drawn on B.Fab past its courtyard, off the board, so it must sit at an edge.
- **What it claimed:** each seed log says `NOTE: C38 is declared on the north edge but is not an edge part (no part class): placed as any other part`, and the seeds are written and judged as normal.
- **What was true:** `check_floorplan --intent` grades the very row it ignored at ERROR (`edge_connector: C38 sits nearest the east edge but is declared on the north edge`) in 9 of 12 seeds of pass 1, so the whole pass was unusable and had to be placed again (one of the stop rule's three approaches spent). The placer and its own grade disagree about whether the row binds. Adding `"class": "connector_affinity"` (found by reading `placement/edge_seat.py` `SEATED_CLASSES`) made the seat honour it: pass 2 had no `edge_connector` error. Neither SKILL.md §3.4 nor `docs/floorplan-intent.md` says a non-connector edge part needs a `class` before the seat reads its edge.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/09_StickHub/repro/fixed.kicad_pcb wk/gpm/09_StickHub/repro/out_x.kicad_pcb --seed 3 --groups wk/gpm/09_StickHub/repro/groups.json --intent wk/gpm/09_StickHub/repro/intent_classless_c38.json 2>&1 | grep -E "C38|floorplan"` then `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/09_StickHub/repro/out_x.kicad_pcb --intent wk/gpm/09_StickHub/repro/intent_classless_c38.json | grep C38`
- **Existing issue:** #1331 (CLOSED, "place_simple's edge seat ignores an intent `edge_connectors[].class`") is the declared-class half; nothing covers the classless half (`gh issue list --search "edge_connectors class place_simple ignored"`, `"edge connector not an edge part"`).

## 2. The default 12-seed pass gave no floorplan-clean seed, twice (decap limits)

- **Tool / command:** `place_simple.py ... --jobs 4` (defaults), then again with `--decap-limit-weight 40`.
- **What it claimed:** `judge.json` named 6 seeds each pass, each with `WARNING: seed N is judged with K floorplan error(s) ... it cannot be DONE as placed`.
- **What was true:** 24 of 24 seeds carried 1-11 error-graded decap findings, a different pin in each (decap_pin_distance 1.81 vs 1.77 mm, 2.02 vs 1.77, 2.61 vs 1.77; decap_distance 4.36-4.91 vs 4.31 mm; decap_ungraded on held caps). The decap-limit term does not drive these limits to zero even at 4x its weight, so the skill's 6-seed judge collapsed into §3.6 case 2 (hand-repair one seed, judge it alone), and the board this run spent 25 minutes routing (pass 2 s7) was chosen without a judge. Only pass 3 (`--near-weight 10` added) produced two clean seeds.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/09_StickHub/repro/fixed.kicad_pcb 'wk/gpm/09_StickHub/repro/out_r{seed}.kicad_pcb' --groups wk/gpm/09_StickHub/repro/groups.json --intent wk/gpm/09_StickHub/intent_run.json --jobs 4 --decap-limit-weight 40 2>&1 | grep floorplan`
- **Existing issue:** #1320 (CLOSED) is a related decap-limit pricing bug; nothing open covers this (`gh issue list --search "decap_pin_distance place_simple seeds floorplan errors"`, `"decap limit anneal"`).

## 3. SKILL instruction: plan-pcb-routing Step 8's dense-2-layer pour-last recipe was rejected by route.py's own gate

- **Tool / command:** the chain Step 8 prescribes for a dense 2-layer board: `route_diff` -> `route.py --nets '*' '!GND'` -> `route_planes.py` (late pour) -> closing `route.py --nets '*'`.
- **What it claimed:** "route signals on BOTH layers at cost 1.0, then pour GND last ... and close the chain with one more `route.py --nets '*'`".
- **What was true:** the closing step printed `IMPROVEMENT GATE: this run broke 4 previously-connected net(s) [+3.3V, /LED3, /LED5, /U1D-], worsened 1 [+1V8 1->5] ... REJECTED` and `REVERTED ... to the input board`, so the chain ended with GND never welded: board_score blocking 40 (GND 34 joins). The same placement with GND routed IN the main step (the pour-first chain, the designer's pours present) gave blocking 8. Separately, re-running the late pour without `--skip-existing-zones` replaced the designer's GND outlines with the board bounding box, flooding the F face of the USB-A plug tongue the designer had left bare (disclosed in `zone_replacements`, and Step 1 does mention the flag; Step 8 does not).
- **Repro:** `python3 -X utf8 py_router/route.py wk/gpm/09_StickHub/repro/pourlast_s1.kicad_pcb wk/gpm/09_StickHub/repro/out_pl.kicad_pcb --nets '*' '!GND' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.5 --via-drill 0.25 --layer-costs 1.0 1.0 --power-nets '+5V' 'VIN' 'Net-(J1-Pin_1)' '+3.3V' '+1V8' --power-nets-widths 0.7 0.7 0.7 0.5 0.5`, then `route_planes.py ... --nets GND GND --plane-layers F.Cu B.Cu --clearance-ceiling 0.1 --skip-existing-zones`, then `route.py ... --nets '*' --power-nets GND '+5V' 'VIN' 'Net-(J1-Pin_1)' '+3.3V' '+1V8' --power-nets-widths 0.3 0.7 0.7 0.7 0.5 0.5 | grep "IMPROVEMENT GATE"` (logs of the measured run: `final_route_old2/s4_route.log`).
- **Existing issue:** none found (`gh issue list --search "pour-last improvement gate reverted"`).

## 4. route.py's merged verdict drops GND links its own oracle reports open (#1339 again)

- **Tool / command:** `route.py ... --nets '*'` on the pass-3 board (`repro/gnd_verdict_route.log` is the run's log).
- **What it claimed:** `JSON_SUMMARY_MIN` `pad_pairs_open: {"count": 2, "nets": ["+5V", "/LED3"]}` and `JSON_REGRADE` lists GND under `routed_single`.
- **What was true:** the same log's `JSON_ORACLE` says `"remaining": 1, "remaining_links": [["GND", ...]]` ("1 link(s) still unconnected per KiCad after 2 round(s)"), and `board_score` on the written board reports GND broken with **5** joins (6 components; `check_connected`'s KiCad refill cross-check: "5 unconnected link(s) copper grading missed"). Blocking was 7, not the 2 the router's verdict implies.
- **Repro:** `grep -E "JSON_ORACLE|JSON_SUMMARY_MIN" wk/gpm/09_StickHub/repro/gnd_verdict_route.log | cut -c1-300` and `python3 -X utf8 py_tools/board_score.py wk/gpm/09_StickHub/repro/gnd_verdict.kicad_pcb --quiet --json wk/gpm/09_StickHub/repro/out_gnd.score.json | grep BLOCKING`
- **Existing issue:** #1339 (CLOSED, "route.py's end-of-run re-grade reports GND "recovered" (failed 0) after its own oracle left 5 exact-fill links open") -- the same symptom on this board at bda59fa0.

## 5. `check_weird` calls an overlapping same-net soft joint a dangling end; route.py leaves it; check_complete fails on it

- **Tool / command:** `py_router/check_weird.py`, and `check_complete.py` (its `weird_copper` component) on the closing route's output.
- **What it claimed:** `dangling-end: 1  net +3.3V (B.Cu) at (143.200, 95.900): free end, dangling segment 0.600mm`, so `check_complete` said `VERDICT: INCOMPLETE -- weird_copper: not clean` on a board with board_score blocking 0.
- **What was true:** the "free end" is 0.33 mm from the next +3.3V segment's end, with half-widths 0.125 + 0.25 = 0.375 mm: the copper overlaps, KiCad sees it connected (`kicad-dangling: 0` in the same report, check_connected all connected). It is a soft joint (check_weird has a `soft-joint` category, which reads 0), and route.py's end-of-run cleanup left it (the same happened on +5V on the first DONE chain). Each needed a hand `check_join` to make check_complete say DONE.
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/09_StickHub/repro/soft_joint.kicad_pcb | grep -E "dangling-end:|soft-joint:|kicad-dangling|net \+3"`
- **Existing issue:** related but closed: #722 (soft-joint anchor test credits a via by radius but a pad by centre), #1063, #1166, #984; none covers segment-to-segment overlap read as a dangling end.

## 6. `analyze_power_paths.get_power_net_recommendations` is silently wrong on this board

- **Tool / command:** the `/analyze-power-nets` skill's Step 5; classifications in `power_analysis.txt`.
- **What it claimed:** `+3.3V 1.2 mm, +1V8 1.0 mm, +5V 0.7 mm, GND 1.0 mm` with an empty "Traced Power Paths" section.
- **What was true:**
  - it adds a sink's whole current once PER power pin (`analyze_power_paths.py` 418-428: `for pad_num ... net_currents[net_name] += current`): U1's seven VCC33 pins give 7 x 167 mA = 1169 mA -> 1.2 mm for a rail whose regulator is rated 100 mA (XR22417 datasheet);
  - the seven JST ports, classified CURRENT_SINK 100 mA, add nothing to +5V because their VBUS pins are `passive` and `is_power_pin` drops them;
  - no path from the plug J1 (POWER_SOURCE) through JP1 and the load switch U2 (both PASS_THROUGH) was traced (`paths == []`), so VIN and Net-(J1-Pin_1) get no width at all.
  The run used its own estimates and says so in the report.
- **Repro:** `python3 -X utf8 -c "import sys;sys.path[:0]=['py_tools','py_router'];from analyze_power_paths import *;c,p=analyze_pcb('wk/gpm/09_StickHub/repro/s7.kicad_pcb');classify_component(c,'J1',ComponentRole.POWER_SOURCE,current_rating_ma=500);[classify_component(c,j,ComponentRole.CURRENT_SINK,current_rating_ma=100) for j in ['J2','J3','J4','J5','J6','J7','J8']];classify_component(c,'U2',ComponentRole.PASS_THROUGH,current_rating_ma=500);classify_component(c,'JP1',ComponentRole.PASS_THROUGH,current_rating_ma=500);classify_component(c,'U1',ComponentRole.CURRENT_SINK,current_rating_ma=167);t=trace_power_paths(p,c);print(len(t),get_power_net_recommendations(p,c,t))"`
- **Existing issue:** none found (`"analyze_power_paths sink current"`, `"power-nets-widths recommendation"`).

## 7. No way to read a datasheet PDF on this machine (helper written)

- **Tool / command:** the Read tool with `pages`, and SKILL.md §3.5's `pdftotext` / `pdftoppm`.
- **What it claimed:** §3.5 step 2: "open it with the Read tool and `pages`".
- **What was true:** the Read tool refuses every PDF page (`pdftoppm is not installed`); poppler is absent and the venv has neither `pypdf` nor `fitz`. Wrote `helpers/pdf_text.py` (inflate streams, print Tj/TJ text) to read the XR22417 Electrical Characteristics (ICC 167 mA max, 7 ports high speed) and its REXT/crystal notes. The SLG5NT1487V datasheet URL returned an HTML page, so U2 stayed an estimate.
- **Repro:** `python3 -I wk/gpm/09_StickHub/helpers/pdf_text.py wk/gpm/09_StickHub/old/datasheets/XR22417/xr22417.pdf --grep "mA"` (the Read tool on the same file fails).
- **Existing issue:** none found (`"pdftotext poppler datasheet"`). Environment, not repo code.

## 8. No tool scores a candidate chip turn on one net group (helper written)

- **Tool / command:** `place_pose.py ... set U1 ... --rot R` + `render_placement.py --json-out` to compare U1's four turns for the USB airwires.
- **What it claimed:** `metrics.crossings` 421 / 711 / 394 / 231 for the four turns.
- **What was true:** those counts are board-wide and dominated by U1's decaps left behind at the old pose (and `--ratsnest-nets` does not scope them), so they say nothing about the USB fan-out. `helpers/usb_rot.py` (straight pin-to-connector airwires of the named nets only) gave 4 / 45 / 60 / 15 crossings, confirming the anneal's turn.
- **Repro:** `python3 -X utf8 wk/gpm/09_StickHub/helpers/usb_rot.py wk/gpm/09_StickHub/repro/s7.kicad_pcb U1 147.97 101.28 '/U*D*' '/D+' '/D-'`
- **Existing issue:** none found.

## 9. SKILL instruction: `--rip-existing-nets <exact names>` does not re-route an already-connected net

- **Tool / command:** `route.py --nets 'Net-(J1-Pin_1)' VIN GND --rip-existing-nets 'Net-(J1-Pin_1)' VIN` (to widen the VBUS path that shipped at 0.1 mm).
- **What it claimed:** plan-pcb-routing "Retrying a failed net": "To change the geometry of copper the router is happy with you must rip it (`--rip-existing-nets <exact names>`)".
- **What was true:** route.py prints `WARNING: 2 net(s) named in both --nets and --rip-existing-nets are already fully connected and will NOT be re-routed ... pass --force-reroute` and routes nothing (`routed: 0`). The tool is honest; the skill names the wrong flag. (`--force-reroute` re-routed them, still at 0.1 mm, with 4 more vias.)
- **Repro:** `python3 -X utf8 py_router/route.py wk/gpm/09_StickHub/routed.kicad_pcb wk/gpm/09_StickHub/repro/out_w.kicad_pcb --nets 'Net-(J1-Pin_1)' VIN GND --rip-existing-nets 'Net-(J1-Pin_1)' VIN 2>&1 | grep -E "will NOT be re-routed"`
- **Existing issue:** #515 (CLOSED) added `--force-reroute`; the skill text was not updated (`"rip-existing-nets force-reroute connected"`).
