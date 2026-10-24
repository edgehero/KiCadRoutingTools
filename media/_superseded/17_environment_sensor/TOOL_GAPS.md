# TOOL_GAPS -- board 17 environment_sensor

Ranked by what each cost this run. Every repro command runs from the worktree root
(`~/Documents/git/krt-gpm`, with `PATH="$HOME/.venvs/krt/bin:$PATH:/Applications/KiCad/KiCad.app/Contents/MacOS"`);
the boards it needs are in `wk/gpm/17_environment_sensor/repro/` (copied with `copy_board.py`, siblings included).

---

## 1. `fill_for_delivery.py` re-saves the board in KiCad 10 format, which turns 68 accepted via-in-pad vias into 68 blocking `drc_via_in_paste`

Cost: about 30 minutes (diagnosis, an upgrade-first chain, two more full chains, a second delivery).

- **Tool / command:** `python3 -X utf8 py_tools/fill_for_delivery.py routed.kicad_pcb -o delivered.kicad_pcb` (SKILL.md §3.9 step 2), then `grade.py` / `board_score --baseline`.
- **What it claimed:** fill_for_delivery exits 0 ("Filled ... net classes preserved: 4, unconnected 45 -> 0"). It is described as only filling the zones, and §3.9 says to route nothing further from its output.
- **What was true:** the input is file version `20241229` (KiCad 9). The output is `20260206` (KiCad 10), because pcbnew's SaveBoard writes the current format. On the KiCad 9 file, check_drc / board_score count the 68 vias that route.py put in same-net pads or paste openings as "undeclarable in this file format (accepted)". On the KiCad 10 file the same 68 vias are declarable, carry no protection, and count as violations. Measured: `board_score --baseline <pile>` gives **BLOCKING=0** on the routed board and **BLOCKING=68 (drc_via_in_paste=68)** on its filled copy, with identical copper. grade.py on the first delivered board: `"done": false, "blocking": 68, "check_complete": "INCOMPLETE"`. The fill runs after the last route step, so no route step can declare Type VII any more. Workaround, now in the chain: `kicad-cli pcb upgrade` on a copy of the input BEFORE routing. route.py then declares Type VII itself ("69 stamped (capping yes)"), and the delivered board grades DONE. Neither SKILL.md (§3.9) nor plan-pcb-routing (4d) mentions it: a step is missing.
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/17_environment_sensor/repro/fillfmt_routed.kicad_pcb -o wk/gpm/17_environment_sensor/repro/fillfmt_delivered.kicad_pcb
  head -2 wk/gpm/17_environment_sensor/repro/fillfmt_routed.kicad_pcb wk/gpm/17_environment_sensor/repro/fillfmt_delivered.kicad_pcb
  for b in fillfmt_routed fillfmt_delivered; do python3 -X utf8 py_tools/board_score.py wk/gpm/17_environment_sensor/repro/$b.kicad_pcb --baseline wk/gpm/17_environment_sensor/repro/pile.kicad_pcb --quiet | grep ^BLOCKING; done
  ```
- **Existing issues:** `gh issue list --search "fill_for_delivery format via paste"`, `"via-in-paste undeclarable"` and `"fill_for_delivery KiCad 10 version"` find nothing (the last returns only #937, which is unrelated). Not covered.

## 2. Tracks land 2 µm inside the 0.2 mm edge floor at the slot's Edge.Cuts arcs; check_drc says clean and kicad_drc_compare files KiCad's 5 errors as "#408 intentional edge"

Cost: about 15 minutes (found only by running kicad-cli by hand on the filled board; two re-routes).

- **Tool / command:** `route.py ... --board-edge-clearance` omitted. It used 0.2, the "fab-edge pin" it also wrote into the project, while the board itself declares `min_copper_edge_clearance 0.0`. Then `check_drc.py <board> [--clearance-margin 0.1]` and `tests/stress/kicad_drc_compare.py <board>`.
- **What it claimed:** check_drc: `NO DRC VIOLATIONS FOUND!`. kicad_drc_compare: `kicad=0 check_drc=0 ... [#408: -5 kicad / -5 check_drc intentional edge] ... CONSISTENT`.
- **What was true:** `kicad-cli pcb drc --refill-zones` reports 5 `copper_edge_clearance` **errors**: GND, I2C_1_SCL and I2C_1_SDA tracks 0.1976-0.1978 mm from the arcs of the L-slot and the north notch (the rule is 0.2000 mm). These are routed tracks, not edge-connector pads. They are "accepted" only because check_drc treats them as covered by an edge-exempt pad, and kicad_drc_compare drops KiCad's items to match. Opened in KiCad, the board shows 5 DRC errors. Workaround: `--board-edge-clearance 0.22` on every routing step. KiCad then reports 0, at the same 101 vias. 0.25 was worse: 105 vias and 4 edge errors again, at the 0.25 floor it wrote.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_drc.py wk/gpm/17_environment_sensor/repro/edgearc_routed.kicad_pcb | tail -3
  python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/17_environment_sensor/repro/edgearc_routed.kicad_pcb | head -3
  kicad-cli pcb drc wk/gpm/17_environment_sensor/repro/edgearc_routed.kicad_pcb --refill-zones --format json -o wk/gpm/17_environment_sensor/repro/out/edgearc.json; python3 -c "import json;[print(v['description'],[i['description'] for i in v['items']]) for v in json.load(open('wk/gpm/17_environment_sensor/repro/out/edgearc.json'))['violations'] if v['type']=='copper_edge_clearance']"
  ```
- **Existing issues:** #408 (closed: emit intentional edge-clearance items) is the filter that hides these. #438 (closed: router grazes the copper-edge rule on strict-edge boards) is the nearest; neither covers arcs or tracks accepted by the pad cover. `"edge clearance arc track"` finds #236, #1074 and #908, which are all different.

## 3. KiCad requires the two `MP` tabs of each JST-SH connector to be joined; check_connected, board_score and check_complete say fully connected

Cost: about 10 minutes (found on the KiCad DRC of the filled board; two hand joins with check_join).

- **Tool / command:** `py_router/check_connected.py`, `board_score.py`, `check_complete.py` on the routed board. The router never routes these nets.
- **What it claimed:** `ALL NETS FULLY CONNECTED!`; `unrouted=0 broken=0`; `check_complete: DONE`.
- **What was true:** J2 and J3 each have two pads numbered `MP` on one net, `unconnected-(J2-PadMP)` / `unconnected-(J3-PadMP)`. KiCad's DRC reports 2 unconnected items: "Missing connection between items Pad MP ... of J2 (197.65,138.855) / (203.25,138.855)", and the same for J3 (190.34 / 195.94, 138.855) on B.Cu. The repo's tools treat such a net as a one-pad net. Workaround: one 0.25 mm track per connector between its tabs, with `check_join.py` (CLEAN). KiCad unconnected: 2 -> 0.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_connected.py wk/gpm/17_environment_sensor/repro/mptabs_routed.kicad_pcb | tail -2
  kicad-cli pcb drc wk/gpm/17_environment_sensor/repro/mptabs_routed.kicad_pcb --refill-zones --format json -o wk/gpm/17_environment_sensor/repro/out/mp.json; python3 -c "import json;[print(u['description'],[i['description'] for i in u['items']]) for u in json.load(open('wk/gpm/17_environment_sensor/repro/out/mp.json'))['unconnected_items']]"
  ```
- **Existing issues:** `"unconnected PadMP same pad number"` finds nothing. `"duplicate pad number missing connection"` returns only #489, which is unrelated. Related family: #1334 (closed), "A DONE board ships KiCad ... errors that no repo grader reports" (starved thermals and connection widths, not this case). Not covered.

## 4. route.py is not run-to-run deterministic with the Step 2c env stack (identical input, command and env: 1183 or 1188 copper items)

Cost: about 15 minutes. It also means a single probe arm cannot be trusted to reproduce in the shipped chain.

- **Tool / command:** `route.py <in> <out> --nets '*'`, with the shipped chain's flags and the Step 2c env stack `KICAD_GLOBAL_PLAN=1 ... KICAD_PACK_INLINE=1`.
- **What it claimed:** CLAUDE.md: "Routing is deterministic ... compare check_drc / check_connected counts (stable run-to-run)".
- **What was true:** the same input board, flags and env gave two different boards. Probe E2/c, x1 and x2 gave 1183 segments+vias (917.32 mm after the chain); c_redo and the shipped chain gave 1188 (923.97 mm). The two outcomes alternate between runs. It is not caused by `KICAD_ROUTE_TRACE` (c_trace = c_notrace) or by `REDO_RUNDIR` (x2 with it = x1 without). Vias were 101 either way, so the shipped chain's copper is about 7 mm worse than the arm it was meant to reproduce.
- **Repro** (run it twice or more and compare the md5s):
  ```bash
  K="KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_ATTRACT_POTENTIAL=65 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_FINALIZE_REAUDIT=1 KICAD_PACK_INLINE=1"
  for i in 1 2 3; do env $K python3 -X utf8 py_router/route.py wk/gpm/17_environment_sensor/repro/spread_in.kicad_pcb wk/gpm/17_environment_sensor/repro/out/spread_$i.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 >/dev/null 2>&1; grep -E '^\s*\((start|end|at) ' wk/gpm/17_environment_sensor/repro/out/spread_$i.kicad_pcb | md5; done
  ```
- **Existing issues:** `"nondeterministic route.py run-to-run"` returns #263 (a hang, unrelated). `"deterministic global plan"` returns #589 and #153, neither about determinism. Not covered as such. CLAUDE.md does note an oracle-stage spread for plane chains, on orangecrab.

## 5. `analyze_power_paths`: a part's current is added once per power PIN, so widths scale with pin count (GND 2.0 mm, +3V3 1.0 mm on a ~190 mA board)

Cost: about 10 minutes (worked out the widths by hand).

- **Tool / command:** analyze-power-nets skill steps 1-5 (`get_power_net_recommendations`); `wk/gpm/17_environment_sensor/repro/power_snippet.py` replays them with this run's classifications.
- **What it claimed:** `{'GND': 2.0, '+3V3': 1.0, '+5V': 0.7, '/VBUS': 0.5, 'Net-(U3-VDDA)': 0.7, 'Net-(U3-VBAT)': 0.5, 'GNDREF': 0.7}`.
- **What was true:** the sinks total about 187 mA, which the tool's own table puts at 0.7 mm. The loop at `get_power_net_recommendations` adds `current` for EVERY power pin of a sink or source: J1's four GND pins x 500 mA, U3's 7 VDD/VSS pins x 60 mA, and so on. That gives GND 2.0 mm and +3V3 1.0 mm. The traced paths are wrong too: "J1 -> U6 via FB1" on GND->GNDREF (the USB shield RC), U3's whole 60 mA routed through the VDDA ferrite FB3, and a coin cell's microamps sized at 0.5 mm. The run routed with GND/+3V3/+5V/VBUS 0.7 and VDDA/VBAT/GNDREF 0.3, from the table applied once per part.
- **Repro:** `python3 -X utf8 wk/gpm/17_environment_sensor/repro/power_snippet.py wk/gpm/17_environment_sensor/repro/pile.kicad_pcb | grep -E '^(PATH|REC)'`
- **Existing issues:** `"analyze_power_paths per pin"` returns #937 (unrelated). `"analyze-power-nets width"` and `"power width GND 2.0"` return #124 (closed: rails not widened), #1169 and #1185, all different. Not covered.

## 6. The datasheet steps assume poppler, and so does the Read tool's PDF mode; neither is installed (helper written)

Cost: about 10 minutes.

- **Tool / command:** SKILL.md §3.5 step 2 ("`pdftotext -layout`, `pdftoppm -r 300`") and the Read tool with `pages`, on the GCT USB4105 and JST eSH datasheets (§3.4 overhang and mating face).
- **What it claimed:** the skill says "Where poppler is installed", and gives no fallback. Read said `pdftoppm is not installed`.
- **What was true:** no poppler, PyMuPDF or pypdf, and `sips` renders only page 1 (and clipped this rotated page). Wrote `helpers/pdfpage.swift`, a PDFKit renderer that honours /Rotate, to read the USB4105 PCB-layout figure (the PCB edge and the shell front both sit 2.60 mm from the front pegs, so the receptacle is flush and overhang_mm needs no row) and the JST eSH side-entry drawing (the solder tabs are at the mating opening, so J2 is `+y` and J3 `-y`).
- **Repro:** `which pdftoppm pdftotext; swift wk/gpm/17_environment_sensor/helpers/pdfpage.swift <any.pdf> 1 wk/gpm/17_environment_sensor/repro/out/p1.png 3`
- **Existing issues:** `"pdftoppm"` and `"pdftoppm poppler datasheet"` find nothing.

## 7. `route_planes.py --skip-existing-zones` keeps every zone, yet tightens the zone clearance for a via lattice that does not exist and lowers the Default class clearance

Cost: about 5 minutes. It is why the chain has no pour step.

- **Tool / command:** `route_planes.py placed.kicad_pcb out.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones`
- **What it claimed:** "Zone clearance tightened 0.15 -> 0.119mm so the pour threads U6's via lattice (0.648mm pitch, 0.3mm vias ...)". It then writes `net_class[Default].clearance: 0.15 -> 0.119` and `rules.min_clearance: 0.15 -> 0.119`, and says "FAB FLOOR RELAXED".
- **What was true:** U6 is a BME280 LGA-8 with no vias. Every zone was kept as drawn ("keeping it (no new zone ...)"), with the designer's 0.25 mm zone clearance. The only copper added was a 9-via thermal array under U1's exposed pad. Yet the project floor was relaxed for every later step.
- **Repro:** `python3 -X utf8 py_router/route_planes.py wk/gpm/17_environment_sensor/repro/placed.kicad_pcb wk/gpm/17_environment_sensor/repro/out/pour.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones 2>&1 | grep -E "tightened|keeping it|net_class\[Default\]"`
- **Existing issues:** `"zone clearance tightened lattice"` finds nothing. `"skip-existing-zones"` returns #1329 (closed: the replace path), which is the other branch.

## 8. Skill commands call bare `kicad-cli`, which is not on PATH here; the repo's own tools find KiCad on their own

Cost: about 2 minutes.

- **Tool / command:** SKILL.md §3.9 step 1 (`kicad-cli pcb drc ... silk_before.json`).
- **What it claimed:** the step reads as runnable; it says "Without kicad-cli, keep the board as it was and say the silk is ungraded".
- **What was true:** `kicad-cli not found` (exit 127). Yet `tests/stress/kicad_drc_compare.py` and `fill_for_delivery.py` ran KiCad 10.0.7 at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Followed as written, the step would have reported the silk "ungraded" on a machine that has KiCad. Added the app directory to PATH by hand.
- **Repro:** `env -i PATH=/usr/bin:/bin zsh -c 'kicad-cli version'; ls /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`
- **Existing issues:** `"kicad-cli not found PATH"` and `"kicad-cli path macOS"` return #1334, #1356, #1335 and #1286, none about locating the binary. Not covered.

## 9. `place_pose.py` prints `"legal": false` for a pose with zero conflicts when the outline has arcs

Cost: about 2 minutes (it reads as a refusal).

- **Tool / command:** `place_pose.py s4.kicad_pcb out --intent intent_run.json set D1 162.0 132.5 --rot 0 set D2 161.5 133.6 --rot 0`
- **What it claimed:** `"legal": false` (exit 0, written).
- **What was true:** every counted category was 0 before and after (pad, hole, stack, graphic, keep-out, off-board). `legal` is false only because `pad_edge` is `complete: false`: the outline has arcs, so every pad's edge distance is "unmeasured (outline uses sampled perimeter check)", 323 pads. check_assembly called the board buildable.
- **Repro:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/17_environment_sensor/repro/placed.kicad_pcb wk/gpm/17_environment_sensor/repro/out/pp.kicad_pcb set D1 162.0 132.5 --rot 0 2>&1 | grep -o '"legal": [a-z]*\|"pad_conflicts_after": [0-9]*\|"unmeasured_count": [0-9]*' | head -3`
- **Existing issues:** `"place_pose legal false arc outline"` finds nothing.

## 10. route_diff / route.py leave pad-local back-tracks that check_cycles counts as copper loops (11 on the USB pair); check_weird says clean

Cost: about 5 minutes.

- **Tool / command:** `route_diff.py ... --nets '/USB_D_*' --layers F.Cu`, then `route.py --nets /USB_D_P /USB_D_N --layers F.Cu`. Graded with `py_tools/check_cycles.py`.
- **What it claimed:** check_weird `NO WEIRD THINGS FOUND`; route_diff routed the pair.
- **What was true:** check_cycles finds `/USB_D_N 6 loops`, `/USB_D_P 5 loops` on the shipped board. route_diff's own output already has one. Its D+ copper starts `167.57,132.562 -> 167.6,132.6 -> 167.4,132.4`, out of pad D5.1 and back across it. The legs step adds the rest. They are tiny, but they are stubs on the one signal pair with an impedance spec.
- **Repro:** `python3 -X utf8 py_tools/check_cycles.py wk/gpm/17_environment_sensor/repro/loops_diff.kicad_pcb`
- **Existing issues:** `"check_cycles loops pad"` finds nothing.
