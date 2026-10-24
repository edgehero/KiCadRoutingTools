# TOOL_GAPS -- board 03 complex_hierarchy

Ranked by what each one cost (time, or copper shipped if I had not caught it). Every repro runs from WT
(`~/Documents/git/krt-gpm`) with `export PATH="$HOME/.venvs/krt/bin:$PATH"`; its input boards are in
`wk/gpm/03_complex_hierarchy/repro/`.

## 1. The judging route's ranking inverted the full route's ranking on copper, in both passes (judge_seeds.py + SKILL §3.7 / plan-pcb-routing Step 8)

- **Tool and command:** `py_placer/judge_seeds.py wk/gpm/03_complex_hierarchy/judge.json --chain wk/gpm/03_complex_hierarchy/judge_chain.txt --intent wk/gpm/03_complex_hierarchy/intent_run.json --jobs 3` (KICAD_ROUTE_TRACE=1), which routes each seed at `--quick 2` and ranks by `quick_score.judge_key`.
- **What it claimed:** pass 1: "best seed 1: keep its placement" (quick: 2 vias 778.18 mm). Pass 2 (judging chain = the final chain, arm B): "best seed 23" (quick: 0 vias 701.45 mm, seed 18 second at 728.86 mm). SKILL §3.6/§3.7 say the quick level "picks seeds as well" as full routes.
- **What was true (measured, the same final chain on each placement, `helpers/full_route_armB.sh`):** every judged seed routed blocking 0 with 0-1 vias, so the pick came down to copper, and there the quick ranking was wrong both times:
  - pass 1: seed 1 full = 0 vias 783.78 mm; seed 9 full = 0 vias **740.56 mm** (seed 8 745.49, 10 787.5, 11 893.9, 5 882.36);
  - pass 2: seed 23 full = 0 vias **755.13 mm** (the judge's pick); seed 18 full = 0 vias **715.41 mm** (s16 769.85, s22 764.11, s19 787.7, s12 812.83).
  - quick-vs-full copper moves by -2% to +8% per seed (s23 701.4 -> 755.1, s18 728.9 -> 715.4), larger than the spread between the top seeds, so on a board where every seed is DONE the quick judge is choosing on noise. Per net, s23's full route adds +19.4 mm on +12V and +18.5 mm on -VAA over its quick route.
  - A SKILL gap underlies pass 1: §3.7 says the judging chain is "the board's routing chain", but plan-pcb-routing Step 8 (2-layer through-hole without buses) prescribes TWO arms (defaults vs `--layer-costs 1.0 1.0 --via-cost 600`) to be compared on the full route. The judging chain has to be written before that comparison exists; I judged pass 1 with arm A, and arm B won the full route (0 vias 783.78 mm vs 4 vias 805.0 mm on seed 1).
- **Cost:** ~10 min of extra full routes and a second placement pass; had I shipped the judge's pick, +73 mm (pass 1) / +44 mm (pass 2) of copper (6-10%).
- **Reproduce:**
  ```bash
  cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH"
  wk/gpm/03_complex_hierarchy/helpers/full_route_armB.sh wk/gpm/03_complex_hierarchy/repro/s23.kicad_pcb wk/gpm/03_complex_hierarchy/repro/r23   # 755.13 mm
  wk/gpm/03_complex_hierarchy/helpers/full_route_armB.sh wk/gpm/03_complex_hierarchy/repro/s18.kicad_pcb wk/gpm/03_complex_hierarchy/repro/r18   # 715.41 mm
  # vs the quick scores the judge used: wk/gpm/03_complex_hierarchy/s23_fast.score.json (701.45) and s18_fast.score.json (728.86)
  ```
  (the helper writes into its out dir, a path relative to WT.)
- **gh issue list --search:** "judge quick full route copper" -> #424, #8 (neither about seed judging); "judge_seeds ranking full route" -> none. Not covered.

## 2. No PDF reader for the datasheet step (Read tool `pages`, poppler) -- helper written

- **Tool and command:** the Read tool on `wk/gpm/03_complex_hierarchy/datasheets/icl7660/icl7660_renesas.pdf` with `pages: 1-10`, as SKILL §3.5 step 2 prescribes ("download it ... and open it with the Read tool and pages").
- **What it claimed:** error "pdftoppm is not installed. Install poppler-utils".
- **What was true:** this machine has no poppler (`which pdftotext pdftoppm` -> not found), no PyMuPDF, no pypdf in the venv. The skill names poppler only "where poppler is installed" and offers nothing else. I wrote `helpers/pdfpages.swift` (macOS PDFKit) to render pages to PNG and dump their text; with it the ICL7660 datasheet (FN3072 Rev 7.00) read fine.
- **Cost:** ~5 min.
- **Reproduce:** `which pdftoppm pdftotext; python3 -c "import fitz"; python3 -c "import pypdf"` (all fail), then Read any PDF with `pages`.
- **gh issue list --search "poppler pdftoppm datasheet":** none.

## 3. A net named `-VAA` cannot be passed to route.py (`--power-nets`, `--nets`): #597 fixed dash-DIGIT names only

- **Tool and command:** `python3 -X utf8 py_router/route.py wk/gpm/03_complex_hierarchy/repro/final.kicad_pcb /tmp/x.kicad_pcb --nets '*' --power-nets GND -VAA --power-nets-widths 0.7 0.6`
- **What it claimed:** `route.py: error: unrecognized arguments: -VAA` (exit 2). `--nets -VAA` -> `argument --nets/-n: expected at least one argument`.
- **What was true:** `-VAA` is a real net of this board (the ICL7660's output rail, in the board's `power` net class). #597's fix (`cli_nets.pin_dash_digit_values`) pins argparse's negative-number matcher to `^-\d`, so `-3V3` parses but `-VAA` (dash-letter) still does not. Workarounds: `--power-nets=-VAA` (equals form, one value only) or a glob `'?VAA'`, which I used -- and which would also match a `+VAA` if a board had one.
- **Cost:** ~2 min; a silent-risk workaround in the shipped chain.
- **Reproduce:** the command above (exit 2); `--power-nets=-VAA --power-nets-widths 0.6 --skip-routing` passes.
- **gh issue list --search "power-nets dash":** #597 (CLOSED, dash-digit only). Not covered for dash-letter names.

## 4. Screw terminal blocks are not classified as connectors, so nothing can hold them to an edge

- **Tool and command:** `placement.part_class.classify_part` (read by check_floorplan, board_context, edge_seat, the intent emitter). Repro:
  ```bash
  cd py_placer && python3 -X utf8 -c "
  import sys; sys.path.insert(0,'../py_router'); sys.path.insert(0,'.')
  from kicad_parser import parse_kicad_pcb; from placement import part_class
  pcb=parse_kicad_pcb('../wk/gpm/03_complex_hierarchy/repro/final.kicad_pcb')
  print(part_class.classify_part(pcb.footprints['P101'],'P101'))"
  ```
- **What it claimed:** `PartClass(name=None, confidence=None, evidence=())` for all six terminal blocks (P101 P102 P201 P202 P301 P302: footprint `Altech_AK300_1x02_P5.00mm_45-Degree`, tags "Altech AK300 serie connector", value CONN_2); board_context prints them as `unknown (looked)`; check_floorplan: "edge_connector: no part classifies as an edge receptacle or actuator, so nothing has an edge to claim".
- **What was true:** they are wire-entry screw terminals (the board's power and signal I/O). With no class, the only lever left is a group `edge` hint, which prices only the group's NEAREST courtyard. I gave power_entry edge N and the channel groups E/W; on the shipped placement P102, P101 and P302 still sit mid-board.
- **Cost:** placement realism (not graded by DONE).
- **gh issue list --search:** "terminal block classify" -> #1004, #963, #318, #296; "terminal block edge connector" -> #1136, #505, #256, #165...; "AK300" -> none. Not covered.

## 5. Name-based diff-pair detection calls the ICL7660's flying-cap nets a differential pair

- **Tool and command:** `python3 py_router/list_nets.py wk/gpm/03_complex_hierarchy/repro/final.kicad_pcb --diff-pairs` (also board_context: "Differential pairs: Net-(U102-CAP+)/Net-(U102-CAP-)").
- **What it claimed:** "Differential Pairs (1 found): Net-(U102-CAP+) / Net-(U102-CAP-)".
- **What was true:** they are the two pins of a charge pump's flying capacitor (U102 pins 2 and 4, each net is U102 <-> C105 only). Not a pair; routed single-ended. board_score then lists `diff_pairs` among UNGRADED, and the verifier brief's rule is FAIL for a declared class left ungraded, so the false pair is a trap for the grade.
- **Cost:** a judgment to make and justify; no copper.
- **gh issue list --search:** "diff pair false positive CAP+" -> #1251, #217, ... (none about CAP+/CAP-); "charge pump diff pair" -> none.

## 6. check_floorplan exits 4 on a clean placement when the given intent withholds budgets

- **Tool and command:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/03_complex_hierarchy/repro/final.kicad_pcb --intent wk/gpm/03_complex_hierarchy/intent_run.json`
- **What it claimed:** exit 4, `"pass": false`, "NOT FULLY GRADED: 3 budget_abstained, 3 rules_skipped_armed".
- **What was true:** `errors: 0`, 1 warning (template_ground_return). The non-pass comes from the read-only intent the run was given (its emitter withheld `decaps.max_distance_mm`, `oob_count`, `overlap_area` because the source was a pile). No placement can turn it into a pass, so the exit code cannot be the gate; "0 errors" is.
- **Cost:** ~1 min; a trap for any caller reading the exit code.
- **gh issue list --search:** "check_floorplan exit 4 budget_abstained" -> #964 (closed, declared-but-unread channels, not this); "NOT FULLY GRADED exit" -> #1236, #1323, #1259, #974, #1242, #1002 (none about the exit code); "check_floorplan pass false zero errors" -> #959. Not covered.

## 7. REPORT.md could not be written (harness)

- **Tool and command:** the Write tool on `wk/gpm/03_complex_hierarchy/REPORT.md`.
- **What it claimed:** "Subagents should return findings as text, not write report files."
- **What was true:** SKILL §6.2 and the TASK require `wk/<run>/REPORT.md`. Per the TASK, REPORT_DONE was not created and the
  full REPORT.md text is at the end of the final reply for the orchestrator to save. (TOOL_GAPS.md itself was accepted.)
- **Cost:** none beyond the hand-off.
- **Reproduce:** a subagent's Write of any `REPORT.md`.
- **gh issue list:** not applicable (harness, not repo).
