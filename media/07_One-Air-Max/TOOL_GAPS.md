# TOOL_GAPS -- board 07 One-Air-Max

Ranked by what each cost this run. Every repro command runs from WT
(`~/Documents/git/krt-gpm`) with `export PATH="$HOME/.venvs/krt/bin:$PATH"`.
Helpers written (`helpers/`), each because no repo tool does the job: `pdf_tool.swift` (entry 8), `trim_spur.py` and `fix_copper.py` (entries 2, 4, 5, 6: resize/re-drill/delete vias, close soft joints, delete segments, declare Type VII), `prune_removable.py` (entry 6), `body_overlaps.py` and `silk_collisions.py` (entry 1: the body collisions no grader gates).


## 1. Silk-drawn bodies never gate (#896): place_simple put a header, the power switch and the DC jack inside the 3x18650 holder BAT1 and parts under the ESP32 module U1, and every grader called it buildable -- only the verifier saw it

- **Tool / command:** `py_placer/place_simple.py` (pass 2, seed 8) and `py_tools/check_assembly.py <board> --intent intent_run.json --baseline fixed.kicad_pcb`, `board_score`, `check_complete`, `check_floorplan`.
- **What it claimed:** `VERDICT: buildable (blocking 0)`; board_score assembly 0; check_complete DONE. check_assembly does list `BAT1 <-> Solarpower1 body(silk/silk) 13.7mm2 side F advisory CONTAINED 100%`, but as advisory (`gate_exempt: silk_drawn`).
- **What was true:** 197 of 204 footprints draw no courtyard (easyeda2kicad); BAT1's holder (77.6 x 56.8 mm) and U1's module (18 x 25.6 mm) exist only as silk/fab drawings, so nothing keeps other parts out of them. On the kept placement: Solarpower1 (a vertical 2-pin header) 100% inside BAT1's outline on the same face; PWR_SW1 (slide switch) with its actuator under BAT1, unreachable; NTC1 inside BAT1; DC1 (barrel jack) overlapping the fixed I2C2 header by 4.83 mm2 with I2C2 pin 4 inside its housing, and turned with its mouth to the west (DC1's south seat was refused in every seed, entry 9, so it was "placed as any other part"; check_assembly prints the DC1/I2C2 overlap as `waived:edge_class`); on the back U3's pads 0.76 mm, R5 and R63 0.5-0.65 mm under the module. The verifier failed the board on these (verdict_1.txt). Cost: verifier call 1, a hand repair of 14 parts (CHOSEN.json `after`, with `helpers/body_overlaps.py` written to measure what the tools would not) and a full re-route.
- **Repro:** `python3 -X utf8 py_tools/check_assembly.py wk/gpm/07_One-Air-Max/repro/silk_body_inside.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/silk_body_inside.intent.json --baseline wk/gpm/07_One-Air-Max/fixed.kicad_pcb` (buildable; the BAT1/Solarpower1 containment only advisory) and `python3 -X utf8 wk/gpm/07_One-Air-Max/helpers/body_overlaps.py wk/gpm/07_One-Air-Max/repro/silk_body_inside.kicad_pcb` (Solarpower1, PWR_SW1, NTC1, DC1 pads inside BAT1; U3, R5, R63 under U1).
- **gh issue search** (`silk body never gates`, `896`, `no courtyard estimated courtyard silk body`): #1250 (CLOSED) "check_assembly calls a board buildable when a test point is moved fully under another part's body" is the same family; #896 / #916 / #1300 (CLOSED) are the body model. None covers a silk-only body of a large holder or module.

## 2. `route.py --escalation board` writes a via whose diameter (0.45) is SMALLER than its drill (0.508); check_drc calls the board clean, KiCad finds a GND/PGND hole-clearance violation

- **Tool / command:** route try 2, `py_router/route.py .../s3_diff.kicad_pcb .../s4_route.kicad_pcb --nets '*' ... --via-size 0.608 --via-drill 0.508 --escalation board --same-net-pad-clearance 0.1` (manifest `final_route/redo_commands.sh`).
- **What it claimed:** `Design rules [--escalation board, --fab-tier auto]: 95 feature(s) on 28 net(s) delivered below the requested size (smallest track width 0.0889 mm, smallest via diameter 0.45 mm); 47 fab-tier escalation(s) to the board's own declared floors`; `check_drc.py --clearance-margin 0.1`: `NO DRC VIOLATIONS FOUND!`.
- **What was true:** the board carries one GND via at (140.9, 105.3) with `(size 0.45) (drill 0.508)`: copper 0.029 mm smaller in radius than its hole. The escalation took the board's `min_via_diameter` 0.3 as the via floor and kept the 0.508 drill (`min_through_hole_diameter`) -- the two rules this board declares contradict each other, and the clamp honoured both. `kicad_drc_compare` on the same board: `KICAD-ONLY hole_clearance ['GND', 'PGND'] @ (140.2, 106.3)`. Fixed by hand (`helpers/fix_copper.py --delete-via 140.9 105.3`: resizing it to 0.608 grazed a PGND In2 track by 0.054 mm; deleting it left U7.1 on the B.Cu GND pour, which KiCad's refill confirms connected).
- **Repro:** `python3 -X utf8 py_router/check_drc.py wk/gpm/07_One-Air-Max/repro/malformed_via.kicad_pcb --clearance-margin 0.1` (clean) vs `PATH=/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/07_One-Air-Max/repro/malformed_via.kicad_pcb` (the hole_clearance item); the via: `grep -n -A3 "140.900000 105.300000" wk/gpm/07_One-Air-Max/repro/malformed_via.kicad_pcb`. To regenerate it: the route.py line above on `repro/try2_s3_diff.kicad_pcb`.
- **How often:** every `--escalation board` route of this board wrote at least one such via: try 2 one (GND 0.45/0.508), try 4 two (SW2, GND), seed 8 two (/USB_D- 0.45/0.508, GND 0.54/0.508), seed 11 fourteen, seed 3 three, the shipped via-cost-350 chain five (0.45/0.508 x3, 0.54/0.508 x2). Each one was a hand fix (resize to 0.608, or a smaller drill where 0.608 grazed). No grader names them: `check_drc`, `board_score` and `check_complete` are clean on the shipped chain's `s7_two.kicad_pcb`; only KiCad flagged one of them, and only once.
- **gh issue search** (`annular via diameter smaller than drill`, `escalation board via drill`): #502 (OPEN, drill aspect ratio not modelled) and #1287 / #1170 (CLOSED, other escalation floors) are related; none covers a diameter clamped below the drill.

## 3. Edge seat on a notched edge: a part "declared north" is seated at the notch's depth, 6.4 mm inside the real edge, and the grade only WARNs

- **Tool / command:** `py_placer/place_simple.py` (edge seat, `py_placer/placement/edge_seat.py`) with an
  `edge_connectors[]` entry `{"ref": "U1", "edge": "north", "class": "connector_affinity", "mating_face": "+y"}`,
  graded by `py_tools/check_floorplan.py --intent`.
- **What it claimed:** edge_seat's docstring: the seat puts the part "past the outline by the low end of the entry's
  `overhang_mm` band ... flush, without one", and slides it only where "the edge the grade reads it on" holds. Every
  seed's `s<S>.log` said the seat was taken; `check_floorplan` printed `U1 north: overhang 0.0000mm ... facing north
  [silk, strong] pass` and 0 errors on seeds 1, 9, 11.
- **What was true:** this board's north side is four runs (0.99, 0.50, 42.79, 0.99 mm -- check_floorplan's own
  `edge_seating.abstained` text) with a 40 x 6.4 mm notch (x 104.76-145.11, bottom at y 57.22). In all 12 pass-1 seeds
  U1 sat at y = 73.0 (antenna end at y 57.25 = the notch bottom) and slid in x from 120.2 to 167.3. In seeds 1, 4, 7,
  8, 9, 11 (x 156-167) the part is under the 42.79 mm run whose edge is y 50.82: 6.43 mm from the real edge, its PCB
  antenna on the board under the BAT1 battery holder. The grade's only finding is a WARN:
  `edge_connector: U1 is an edge part seated 13.47mm from the nearest edge with no overhang (courtyard; seat tolerance
  3.00mm)`. Cost: one full placement pass thrown away (pass 1, ~15 min with the analysis), and the declaration had to
  move to the east edge.
- **Repro:**
  `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/07_One-Air-Max/repro/notch_seated.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/notch_seated.intent.json`
  (pass-1 seed 1: U1 at (166.4, 73.0, 180); prints the 13.47 mm WARN and `U1 north ... pass`, 0 errors). To re-place:
  `python3 -X utf8 py_placer/place_simple.py wk/gpm/07_One-Air-Max/repro/notch_seat.kicad_pcb wk/gpm/07_One-Air-Max/repro/out.kicad_pcb --groups wk/gpm/07_One-Air-Max/repro/notch_seat.groups.json --intent wk/gpm/07_One-Air-Max/repro/notch_seat.intent.json --seed 1`
  (needs templates in the intent: this copy carries them).
- **gh issue search** (`edge seat notch`, `edge seat setback seated from the nearest edge`,
  `edge_connector corner nearest edge seat`): #712 (CLOSED, "edge_connectors cannot say 'centered'") and #1201
  (CLOSED, an F.Fab pin-1 circle read as a body) are related seat/grade issues; neither covers a notched edge. No issue
  covers it.

## 4. `fill_for_delivery.py` saves through pcbnew, which upgrades the file to KiCad 10 and writes explicit `(capping no) (filling no)` on every via: four `undeclarable` vias-in-pad become a blocking `drc_via_in_paste` 4 on the delivered board

- **Tool / command:** `python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/07_One-Air-Max/labelled.kicad_pcb -o wk/gpm/07_One-Air-Max/delivered.kicad_pcb` (SKILL.md §3.9 step 2).
- **What it claimed:** `Filled: ... filled_polygon blocks: 11, net classes preserved: 1, unconnected (no --refill-zones): 129 -> 0, EXIT=0`. The skill: "It fills with KiCad's own zone filler, copies the siblings and keeps the net classes."
- **What was true:** the routed board is `(version 20241229)` (KiCad 9), where a via cannot declare protection, so the four vias in pads (U2.7 MODE x2, REGN at R35.1 and C36.2) were graded `undeclarable` and accepted: `board_score` blocking 0, `check_complete` DONE. The delivered file is `(version 20260206)` and every via now carries `(capping no) (covering (front no) (back no)) (plugging ...) (filling no)`; the same four vias then grade `VIA-IN-PASTE ... not filled+capped (capping no, filling no)`: `board_score` BLOCKING=4 (`drc_via_in_paste=4`), `check_complete` INCOMPLETE, `check_drc` 4 violations. Nothing in the chain re-stamps them (route.py's Type VII stamp counted them `unstampable` because of the old format). Fixed by hand: `helpers/fix_copper.py --type-vii X Y` on the four vias of the filled board (then DONE again). Cost ~10 min.
- **Repro:** `python3 -X utf8 py_tools/board_score.py wk/gpm/07_One-Air-Max/repro/fill_unstamped.kicad_pcb --baseline wk/gpm/07_One-Air-Max/One-Air-Max.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/fill.intent.json` (BLOCKING=4, drc_via_in_paste 4) against the same command on `wk/gpm/07_One-Air-Max/repro/fill_routed_v9.kicad_pcb` (BLOCKING=0, the four counted undeclarable).
- **gh issue search** (`fill_for_delivery via-in-paste version`, `unstampable via in paste KiCad 9 format`): none covers it.

## 5. route_diff + route.py ship a dead-end /USB_D+ spur that KiCad reports as `track_dangling`; check_complete fails on it and no tool removes it (helper written)

- **Tool / command:** the final routing chain (route_diff for `/USB*`, then route.py `'*'`), both tries; `check_complete.py`.
- **What it claimed:** route.py ran its `#1217` kicad-dangling split pass twice and its strict collapse (`Diff-pair Strict collapse: removed 28 redundant segment(s)` in route_diff) and reported `failed 0`; `check_connected`: `ALL NETS FULLY CONNECTED!`; `check_drc`: clean.
- **What was true:** `check_complete`: `VERDICT: INCOMPLETE -- weird_copper: not clean`; `check_weird`: `kicad-dangling: 1 net /USB_D+ (F.Cu) at (139.750, 116.062): segment (139.750, 116.062)-(139.750, 116.100) w0.145: both ends lie on other /USB_D+ track(s)`. The spur is the end of a 0.0889 mm segment (138.0,114.3)-(139.8,116.1) past the T where the R63-side chain lands at (139.35, 115.66), plus two 0.05 mm and 0.038 mm stubs -- a dead end with no pad or via, the same in both tries (route_diff is deterministic). Removed with `helpers/fix_copper.py --trim-usb-spur` (try 1: `helpers/trim_spur.py`).
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/07_One-Air-Max/repro/usb_spur.kicad_pcb` and `python3 -X utf8 check_complete.py wk/gpm/07_One-Air-Max/repro/usb_spur.kicad_pcb` (INCOMPLETE, weird_copper).
- **gh issue search** (`kicad-dangling`, `track_dangling kicad-dangling route_diff`): #1234 (OPEN) "route.py leaves chains of 0.025-0.075 mm segments that enter no pad or via, and nothing reports them" is the same family (here check_weird does report it, but nothing removes it); #1166 / #1291 (CLOSED) are related.

## 6. route.py's first pass leaves redundant loops and dangling segments that a second, identical route.py pass removes

- **Tool / command:** the shipped chain's step 2 (`route.py ... --nets '*' --via-cost 350 ...`) on the seed-4 placement at via-cost 150 (`try4_route`).
- **What it claimed:** `failed 0` apart from the caged MODE net; the run's own cleanup passes (strict collapse, kicad-dangling split, orphan sweep) reported done.
- **What was true:** `check_weird` on that board: 3 `redundant-cycle` loops (/SDA In2.Cu, /Solar_module/Solar+ In2.Cu, /VOUT1 F.Cu) and a 2.1 mm "free end" on /Solar_module/SW2; `check_complete` fails `weird_copper`. A second route.py with the same arguments, which had nothing left to route, removed the 3 loops (`check_weird`: 2 left). So the shipped chain carries a closing `route.py '*'` (step 4) for that. The SW2 one was a 0.5 mm track ending 0.67 mm short of the L1 track it overlaps (a soft joint): hand-closed and four redundant pieces deleted (`fix_copper.py --seg-end ... --delete-seg ...`).
- **Also:** on every later route a `free end` that was really a soft joint (a 0.7-1.0 mm power track ending 0.5-0.7 mm short of a same-net track it overlaps: /Solar_module/Solar+, Net-(U5-PMID), PGND, +5V, SW2) had to be closed by hand (`fix_copper.py --seg-start/--seg-end`), and closing it then exposed 11-21 `removable-segment` stubs inside pads that check_weird had not reported while the net had a free end; `helpers/prune_removable.py` deletes them one at a time, re-running check_weird after each. Both pass check_complete's `weird_copper` only after that.
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/07_One-Air-Max/try4_route/s5_mode.kicad_pcb` (4 loops/dangles + spur) vs `.../try4_route/s6_clean.kicad_pcb` (after the second pass: 2).
- **gh issue search** (`kicad-dangling`): #1234 (OPEN, short segment chains nothing reports) and #1166 (CLOSED) are related; none covers a cleanup that converges only on a second run.

## 7. `analyze_power_paths` traces no power path on a board whose pins carry no `power_in` / `power_out` types, and recommends only GND 3.0 mm / PGND 3.0 mm

- **Tool / command:** the `/analyze-power-nets` skill's API, `py_tools/analyze_power_paths.py`:
  `trace_power_paths(...)` and `get_power_net_recommendations(...)` after classifying all 43 unknown parts and the six
  load switches with `classify_component` (sources DC1, Solarpower1, BAT1, Battery1, U5, U6, U2, USB1 with currents;
  pass-throughs U7, PWR_SW1, Q1, Q2, U13-U18; sinks U1, the sensor connectors).
- **What it claimed:** `## Traced Power Paths` empty; `--power-nets "GND" "PGND" --power-nets-widths 3.0 3.0`.
- **What was true:** this easyeda2kicad board's pads carry pin types `unspecified`/`passive`; `trace_power_paths`
  finds sinks only by `pintype == 'power_in'` and sources by `power_out` or a pin named OUT/VOUT, so all the
  classifications are ignored. +5V, +3V3, VBAT, SYS, PMID and every switch node got no width, and the 3.0 mm GND/PGND
  is the sum of all sink currents applied to a ground that is poured anyway. The widths had to be set by hand from the
  IPC-2221 table (REPORT.md).
- **Repro:** `python3 -X utf8 -c "import sys; sys.path[:0]=['py_tools','py_router']; from analyze_power_paths import *; c,p=analyze_pcb('wk/gpm/07_One-Air-Max/fixed.kicad_pcb'); classify_component(c,'U1',ComponentRole.CURRENT_SINK,current_rating_ma=500); classify_component(c,'U2',ComponentRole.POWER_SOURCE,current_rating_ma=1000); pa=trace_power_paths(p,c); print(len(pa), get_power_net_recommendations(p,c,pa))"`
  prints `0 {...}` with no +3V3/+5V entry.
- **gh issue search** (`power paths`, `analyze-power-nets`, `power paths pintype power_in`): #124 (CLOSED wontfix,
  power buses not widened) is the nearest; nothing covers the pintype dependence.

## 8. No PDF renderer: the Read tool's PDF pages need `pdftoppm`, poppler is not installed, and the skill's `pdftotext` / `pdftoppm` commands do not exist here (helper written)

- **Tool / command:** the Read tool on `datasheets/tps62902/tps62902.pdf` with `pages: "1-2"`; SKILL.md §3.5 step 2
  "Finding the pages ... Where poppler is installed: pdftotext / pdftoppm / pdfimages".
- **What it claimed:** `pdftoppm is not installed. Install poppler-utils`.
- **What was true:** no `pdftotext`, `pdftoppm`, `gs`, `mutool` or Python PDF module (fitz, pypdf, pdfplumber) on
  the machine, and installing poppler would write outside the run folder. The §3.5 datasheet step cannot be done at
  all without a renderer: the layout figures are vector drawings. Wrote `helpers/pdf_tool.swift` (PDFKit; `text`,
  `find`, `render PAGE DPI OUT [crop]`), compiled with `swiftc`; it read all four datasheets. Cost ~5 min.
- **Repro:** `which pdftotext pdftoppm; python3 -c "import fitz"` (both fail); the helper:
  `wk/gpm/07_One-Air-Max/helpers/pdf_tool find wk/gpm/07_One-Air-Max/repro/tps62902.pdf "layout example"`.
- **gh issue search** (`pdftoppm poppler datasheet`): none.

## 9. DC1's south-edge seat is refused in every seed, and the anneal then leaves it where the grade reads it on the WEST edge (floorplan ERROR) in a third of the seeds

- **Tool / command:** `py_placer/place_simple.py` (edge seat) + `check_floorplan --intent`, for the brief's
  `DC1 edge south` declaration.
- **What it claimed:** every `s<S>.log` of both passes: `WARNING: DC1 is declared on an edge but has no seat there (no
  room along the south edge: of the 188 positions tested, 145 refused by the declared-pose check against BAT1, 32
  reading nearest the east/west edge, 11 with pad copper inside the board's 0.30mm edge clearance); placed as any
  other part`.
- **What was true:** DC1 does fit flush on the south edge: in pass-2 seeds 0, 2, 4, 8, 11 (and the kept seed 4, at
  (172.0, 114.6, 90)) the anneal itself put it there, buildable, and `check_floorplan` graded it `DC1 south: overhang
  0.0000mm ... pass`. So the seat's refusal (145 of 188 positions "against BAT1") is not what the legality the
  anneal and `check_assembly` use says. And because DC1 was then "placed as any other part", seeds 1, 5, 6, 7, 9 (pass
  2) and 3, 4, 5, 8 (pass 1) left it in the SW corner, where the grade fails it:
  `[ERROR] edge_connector: DC1 sits nearest the west edge but is declared on the south edge` -- 5 of 12 pass-2 seeds
  unusable for that alone. Cost: fewer clean seeds to judge; no time.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/07_One-Air-Max/repro/dc1_west.kicad_pcb --intent wk/gpm/07_One-Air-Max/repro/dc1_west.intent.json`
  (pass-2 seed 6, DC1 at (103.7, 112.4, 0): the ERROR above). The seat refusal prints in any
  `place_simple.py ... --seed N` run on `repro/notch_seat.kicad_pcb` with `repro/dc1_west.intent.json`.
- **gh issue search** (`nearest the west edge but is declared`, `edge_connector corner nearest edge seat`): no issue
  covers it.

## 10. `route_diff.py` has no `--json-out`, unlike `route.py`; a judging chain that passes it fails every seed

- **Tool / command:** `py_placer/judge_seeds.py ... --chain judge_chain.txt` whose route_diff line carried
  `--json-out {dir}/diff.json` (SKILL.md §3.7 names `{dir}` with "`--json-out {dir}/route.json`").
- **What it claimed:** `route_diff.py: error: unrecognized arguments: --json-out` (exit 2), all six seeds
  `FAILED: step 3 (route_diff.py) exited 2 and wrote no board`.
- **What was true:** route_diff writes its `JSON_SUMMARY` to stdout only; the run's other steps (route.py,
  add_rule_area) take or ignore the flag differently. My chain error, but the two routing CLIs disagree on a flag the
  skill's chain format leans on. Cost ~3 min (the judge failed fast).
- **Repro:** `python3 -X utf8 py_router/route_diff.py wk/gpm/07_One-Air-Max/fixed.kicad_pcb /tmp/x.kicad_pcb --nets '/USB*' --json-out x.json`
  -> exit 2.
- **gh issue search** (`route_diff json-out`): #1327 (CLOSED, no tool ran the judging chain) is related; none covers
  the flag.

## 11. `check_floorplan` reports U1 "seated 6.08mm from the nearest edge" while its antenna end is flush (0.06 mm)

- **Tool / command:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/07_One-Air-Max/final.kicad_pcb --intent wk/gpm/07_One-Air-Max/intent_run.json`.
- **What it claimed:** `[warn ] edge_connector: U1 is an edge part seated 6.08mm from the nearest edge with no overhang (courtyard; seat tolerance 3.00mm) -- a plug may not reach it`.
- **What was true:** U1 at (180.0, 99.4, rot 90): its drawn silk body ends at local y 15.75, board x 195.75, and the east edge is x 195.81 -- 0.06 mm. 6.08 mm is the antenna region (silk y 9.73..15.75 = 6.02 mm) plus that: the grade's estimated courtyard (the part draws no courtyard) stops where the shield can's silk line does, while the seat used the drawn body. A WARN only; cost nothing but a check.
- **Repro:** the command above (or on `routed.kicad_pcb`, `--allow-routed`).
- **gh issue search** (`edge seat setback seated from the nearest edge`): none.
