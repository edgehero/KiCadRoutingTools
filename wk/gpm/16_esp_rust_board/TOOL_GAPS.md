# TOOL_GAPS -- gpm board 16 (esp_rust_board)

Ranked by what each cost this run. Every repro command runs from the worktree root
(`cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH"`); its inputs are
copies in `wk/gpm/16_esp_rust_board/repro/`. R = `wk/gpm/16_esp_rust_board/repro`.

## 1. check_floorplan grades an `edge_connectors[]` row that place_simple will not seat (a module antenna): a whole placement pass wasted

- **Tool / command:** `py_placer/place_simple.py` + `py_tools/check_floorplan.py`, with an intent whose
  `edge_connectors[]` holds `{"ref": "U3", "edge": "north", "mating_face": "-y"}` for the ESP32-C3-MINI-1
  module (the skill gives no other way to put a PCB-antenna module's antenna end on an edge; placement-lessons
  says it must, and SKILL.md §3.1 treats edge parts this way).
- **What it claimed:** `check_floorplan --intent` on the pile accepted the row and graded it
  (`U3 north: ... facing north [courtyard+fab, strong] pass`). place_simple ran all 12 seeds, exit 0, and
  then judged six of them with `WARNING: seed N is judged with 2 floorplan error(s) (edge_connector): it
  cannot be DONE as placed`.
- **What was true:** place_simple never seated U3. The only trace is one NOTE inside each seed's own
  `s<S>.log` -- `U3 is declared on the north edge but is not an edge part (no part class): placed as any
  other part` (`placement/edge_seat.py:485`) -- nothing in the run summary. The grade then failed every seed
  on the row the placer had dropped: `[ERROR] edge_connector: U3 sits nearest the east edge but is declared
  on the north edge` (seed 10: U3 at (150.306, 82.068), its courtyard 6 mm below the north edge). 12 of 12
  seeds carried the error, so the pass was unusable (ledger row 1, `old/pass1/`). Fixed in pass 2 by
  declaring U3 in `fixed_poses[]` (`basis: derived_default`) instead. The grader and the seat should agree on
  which rows are seatable: either the grade refuses/warns a classless row up front, or the seat honours it
  (or the intent can say `class` for a non-connector, which #1331 added for connectors only).
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_simple.py R/fixed.kicad_pcb R/p1.kicad_pcb --groups R/groups.json \
      --intent R/intent_pass1_u3edge.json --seed 0 --json R/p1.json; grep "not an edge part" R/p1.log 2>/dev/null
  python3 -X utf8 py_tools/check_floorplan.py R/p1.kicad_pcb --intent R/intent_pass1_u3edge.json | grep edge_connector
  ```
  (replace `R` with the repro path; the second line prints the ERROR.)
- **gh issue search** (`edge_connectors not an edge part`, `not an edge part`, `edge_connectors class seat
  module`, `antenna`): #1331 (CLOSED, the seat ignored an intent `edge_connectors[].class` -- fixed for
  connectors), #1325 (CLOSED, "no room along the edge" wording), #1200 (CLOSED, rule-area writer). None
  covers a classless row the grade enforces and the seat drops, or an antenna module's edge.

## 2. route.py's default `--fab-tier auto` ships 0.25/0.15 vias below the board's own 0.4 mm minimum (on a net its disclosure does not name) and rewrites that minimum, on a board the standard tier routes completely

- **Tool / command:** `py_router/route.py` (defaults `--fab-tier auto --escalation fab`) on this 2-layer
  board, e.g. with `--layer-costs 1.0 1.0 --via-cost 150` (arm A).
- **What it claimed:** one WARNING (`net rescue net_1: escalated standard->advanced fab floor (0.25/0.15
  via etc.)`) and a `Design rules [...]: 2 fab-tier escalation(s) to advanced` line; the writeback then set
  `rules.min_via_diameter: 0.4 -> 0.25 mm`, `min_via_drill -> 0.15`, so `check_drc`, KiCad's DRC and a bare
  `board_score` grade the board clean.
- **What was true:** the shipped 0.25/0.15 vias are not where the disclosure points. In arm A (and the repro)
  both are on **IO0**, at (143.4, 82.4) and (143.5, 81.5), an F->B->F hop beside U3 pin 12 (a 0.4 x 0.8 pad),
  while the warning and `JSON_SHIPPED_RULES.design_rules` name only GND's rescue (`fab_tier_contexts: ["net
  rescue net_1"]`, `nets: [1, 4, 26, 29]` -- IO0, net 6, is not listed). In arm C the one small via is the
  GND rescue's own, in U2's GND pad (151.75, 87.75). All are below the board's declared Board Setup minimum
  of 0.4/0.2. `board_score --min-via-diameter 0.4
  --min-via-drill 0.2` reads `undersized=4` (blocking 4) for arm A and 2 for arm C. The same arm with
  `--fab-tier standard` routed every net with no small via (A2: blocking 0, 83 vias), so the escalation was
  not needed for completion. It is disclosed by design (CLAUDE.md "completion first, disclosed"), but
  plan-pcb-routing's chain never says to pass `--fab-tier standard` when the board declares a via minimum,
  and without the spec flags the relaxed project hides it. Cost: two arms rejected and a re-run round.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route.py R/s8_diff.kicad_pcb /tmp/x.kicad_pcb --nets '*' --track-width 0.127 \
      --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.2 --power-nets +3V3 /Buck_Coil +5V VBUS \
      'Net-(D6-Pad2)' +BATT GND 'Net-(J1-PadS1)' --power-nets-widths 1.0 1.0 1.0 0.7 1.2 0.7 0.5 0.5 \
      --layer-costs 1.0 1.0 --via-cost 150
  python3 -X utf8 py_tools/board_score.py /tmp/x.kicad_pcb --min-via-diameter 0.4 --min-via-drill 0.2 \
      --min-track-width 0.127 --quiet          # BLOCKING=4 (undersized=4)
  ```
  (use a scratch path for `/tmp/x`; measured here: `undersized=4`, `rules.min_via_diameter: 0.4 -> 0.25`.)
- **gh issue search** (`escalated standard advanced via`, `fab-tier auto undersized via board_score`,
  `undersized via`): #857 (CLOSED, `--fab-tier standard` escalating silently -- the opposite case), #502
  (OPEN, drill aspect ratio). No issue covers an auto escalation the standard tier did not need.

## 3. route.py ships a USB_D- connection that is only a 0.042 mm pad-edge overlap, and the instruments disagree on whether it is connected

- **Tool / command:** the arm-E chain's `route.py --nets '*'` + 2 iterations (final_route steps 10-13) on
  final.kicad_pcb; graded by `check_connected.py`, `board_score.py`, `check_weird.py`, `check_join.py`.
- **What it claimed:** check_connected "ALL NETS FULLY CONNECTED", KiCad 0 unconnected, check_weird clean,
  check_complete DONE. board_score meanwhile listed `diff_pairs.unjoined_pairs: [USB_D+/USB_D-]` (measured,
  not graded, so DONE did not move).
- **What was true** (found by the verifier, re-measured): USB_D- was two separate traces, J1.A7 -> U4.20 and
  J1.B7 -> via (150.5,119.4) -> D5.1 -> U3.26, which met only where the F.Cu segment (150.9,119.9)-(150.9,119.5)
  w0.127 passes D5 pad 1 (x 150.178-150.878): its edge at x 150.8365 overlaps the pad by 0.0415 mm over about
  0.21 mm. A hand join landing that trace on the pad centre was `CLEAN` by `check_join`, and then
  `check_weird` reported 5 `removable-segment`s on USB_D- (`removal does not change net connectivity`) and
  `check_complete` went `INCOMPLETE -- weird_copper`, so check_weird's graph had not seen the overlap as a
  connection either, yet it called the overlap board clean. Fixed by `route.py --nets USB_D- GND
  --force-reroute` (final_route step 15): pair joined, copper -13 mm. Cost: one verifier call and ~10 min.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_connected.py R/routed_v2.kicad_pcb | tail -2          # ALL NETS FULLY CONNECTED
  python3 -X utf8 py_tools/board_score.py R/routed_v2.kicad_pcb --json /tmp/s.json --quiet >/dev/null; \
      python3 -c "import json;print(json.load(open('/tmp/s.json'))['components']['diff_pairs']['unjoined_pairs'])"
  python3 -X utf8 py_tools/check_join.py R/routed_v2.kicad_pcb USB_D- 150.9,119.6,F.Cu 150.6,119.6,F.Cu \
      --width 0.127 --keep-staged /tmp/j.kicad_pcb                                     # CLEAN
  python3 -X utf8 py_router/check_weird.py /tmp/j.kicad_pcb | grep removable-segment    # 5
  ```
- **gh issue search** (`check_cycles loops`, `redundant cycle prune`): #1063 (CLOSED, check_weird in-pad
  wiggles), #162 (CLOSED). None covers a connection made only by an edge overlap.

## 4. route_diff ships a 0.25/0.15 via under `--via-size 0.45 --via-drill 0.2` with no design-rules record

- **Tool / command:** `py_router/route_diff.py <pour board> <out> --nets USB_D+ USB_D- --track-width 0.127
  --diff-pair-gap 0.127 --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.2` on pass-2 seed 11.
- **What it claimed:** `JSON_SUMMARY` with no `design_rules` key and no escalation, no `Design rules [...]`
  line (route.py prints one for every narrowing); only the project writeback's `FAB FLOOR RELAXED ... via
  diameter: 0.4 -> 0.25 mm; 1 of 14 object(s) on this board are below the ORIGINAL 0.4mm`.
- **What was true:** one USB_D- via at (149.8, 120.0) is 0.25/0.15, below the asked 0.45/0.2 and the board's
  0.4/0.2 minimum; it rides through every later step and makes the seed's board `undersized=2` (blocking 2)
  under the board's spec flags. The skill's "diff pairs did not silently peel" check reads
  `failed/partial/single_ended_diff_pairs`, none of which says this.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route_diff.py R/s11_pour.kicad_pcb /tmp/d.kicad_pcb --nets USB_D+ USB_D- \
      --track-width 0.127 --diff-pair-gap 0.127 --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.2 \
      | grep -c "Design rules \["        # 0
  python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as p;b=p('/tmp/d.kicad_pcb');print([(v.x,v.y,v.size) for v in b.vias if v.size<0.4])"
  ```
- **gh issue search** (`route_diff via size`, `route_diff fab floor relaxed`): #1207, #1218 (CLOSED,
  route_diff via spacing at the wrong clearance), #530 (CLOSED). None covers an undisclosed via shrink.

## 5. analyze_power_paths drops every sink but one per rail, so the 350 mA module is never traced

- **Tool / command:** the analyze-power-nets skill's own recipe (`trace_power_paths`,
  `get_power_net_recommendations` in `py_tools/analyze_power_paths.py`), with U3 (ESP32-C3-MINI-1) classified
  `CURRENT_SINK 350 mA`, D9 (WS2812B) `CURRENT_SINK 60 mA`, U5 (SY8088) `POWER_SOURCE 500 mA`.
- **What it claimed:** "Traced Power Paths: U5 -> D9 60 mA (+3V3 -> /Buck_Coil, via L1); J1 -> D9 60 mA",
  i.e. the +3V3 rail's only load is a 60 mA LED.
- **What was true:** `sink_nets: Dict[int, str]` keeps ONE sink per net id (the last one iterated), so U3,
  U1 and U2 on +3V3 are overwritten by D9 and never appear in any path. The widths then come from summing the
  sources' ratings instead (a header frame classified as a source on +3V3/VBUS/+BATT counts again on each),
  and the USB shell net `Net-(J1-PadS1)` (tied to GND through a 0R, no supply current) came back at 2.0 mm,
  as wide as GND. I overrode GND and the shell net to 0.5 mm by judgment. Cost: about 10 minutes of
  re-classification runs to understand the numbers.
- **Repro:**
  ```bash
  python3 -X utf8 -c "
  import sys; sys.path[:0]=['py_tools','py_router']
  from analyze_power_paths import analyze_pcb, classify_component as c, trace_power_paths, ComponentRole as R
  comps,p=analyze_pcb('wk/gpm/16_esp_rust_board/repro/fixed.kicad_pcb')
  c(comps,'U3',R.CURRENT_SINK,current_rating_ma=350); c(comps,'D9',R.CURRENT_SINK,current_rating_ma=60)
  c(comps,'U5',R.POWER_SOURCE,current_rating_ma=500)
  print([vars(x) for x in trace_power_paths(p,comps)])"
  ```
  prints one path, `U5 -> D9, 60 mA`; U3 is absent.
- **gh issue search** (`trace_power_paths sink`, `analyze_power_paths`, `power path current width`): no
  issue covers it.

## 6. No PDF renderer for the §3.5 datasheet step: poppler absent, the Read tool's `pages` fails -- helper written

- **Tool / command:** SKILL.md §3.5 (`pdftotext -layout`, `pdftoppm -r 300`, `pdfimages -j`) and the Read
  tool on a downloaded PDF with `pages`.
- **What it claimed:** the skill says to open the PDF "with the Read tool and `pages`" and use poppler "where
  it is installed".
- **What was true:** `which pdftotext pdftoppm pdfimages` -> not found; Read with `pages` -> "pdftoppm is not
  installed". No Python PDF library in the venv either (no fitz/pypdf/pdfplumber). I wrote
  `helpers/pdf_render.swift` (macOS PDFKit: page text, and PNG render at a chosen dpi, cropped with `sips`) to
  read the SY8088 application note, the GCT USB4105 drawing and the ESP32-C3-MINI-1 datasheet. Cost: about 5
  minutes. The skill names no fallback for a machine without poppler.
- **Repro:** `which pdftotext pdftoppm pdfimages; swift wk/gpm/16_esp_rust_board/helpers/pdf_render.swift
  R/usb4105.pdf text 1 1 | head`
- **gh issue search** (`poppler pdftoppm datasheet`, `pdf datasheet render`): none.

## 7. check_floorplan warns that the buck's switch node has no decoupling capacitor

- **Tool / command:** `py_tools/check_floorplan.py <any placed seed> --intent intent_run.json`.
- **What it claimed:** `[warn ] decap_pin_uncovered: U5 rail /Buck_Coil (e.g. pin 3) has NO decoupling
  capacitor on it anywhere on the board` -- on every seed of both passes.
- **What was true:** U5 pin 3 is the SY8088's LX (switch) pin (pintype `power_out`, net /Buck_Coil = U5.3 and
  L1.1 only). A switch node is never decoupled; a cap there would short the converter's switching. The decap
  census counts a `power_out` pin as a supply pin. It cost reading time only, but it is a permanent false
  warning on every buck.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py R/final.kicad_pcb --intent R/intent_run.json | grep decap_pin_uncovered`
- **gh issue search** (`decap_pin_uncovered switch node`, `LX switch node decap`, `decap uncovered`): #705
  (CLOSED, decap graded to the IC bbox) -- not this.

## 8. 19 redundant copper loops ship on a DONE board, and no DONE grader reads them

- **Tool / command:** `py_tools/check_cycles.py wk/gpm/16_esp_rust_board/routed.kicad_pcb` after the full
  chain (route.py `'*'` + 2 iterations; its cleanup has `prune_redundant_cycles`).
- **What it claimed:** board_score blocking 0, check_complete DONE, check_weird "NO WEIRD THINGS FOUND",
  orphan stubs none.
- **What was true:** `+3V3 155 segs 18 vias 14 loops`, `USB_D+ 57 segs 5 vias 3 loops`, `VBUS 52 segs 3 vias
  2 loops`: 19 independent loops on 3 signal nets (22 on 5 nets on the first routed board). The skill lists
  "no redundant copper loop -> check_cycles" among what the final board should meet, but check_complete does
  not run it, so DONE says nothing about it. Not diagnosed further (loops through wide power copper and its
  neck-downs, or the USB-C receptacle's A6/B6 pad pair, are my guesses, not measurements). Cost: none to the
  verdict; disclosed in REPORT.md.
- **Repro:** `python3 -X utf8 py_tools/check_cycles.py wk/gpm/16_esp_rust_board/routed.kicad_pcb`
- **gh issue search** (`check_cycles loops`, `redundant cycle prune`): #162 (CLOSED, same-net redundant
  copper producers), #444 (CLOSED). None for loops left on a DONE board.
