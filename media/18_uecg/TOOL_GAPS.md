# TOOL_GAPS -- gpm 18 uecg

Ranked by what each cost this run. Every repro command runs from the worktree root
(`cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH"`); its inputs
are copied into `wk/gpm/18_uecg/repro/`.

## 1. place_simple places parts inside a FIXED part's pad copper that reaches past its courtyard; every seed then fails check_assembly

- **Tool / command:** `py_placer/place_simple.py wk/gpm/18_uecg/fixed.kicad_pcb 'wk/gpm/18_uecg/s{seed}.kicad_pcb' --groups ... --intent intent_run.json --jobs 4` (pass 1, before the keep-outs were added).
- **What it claimed:** all 12 seeds placed, 10 of them with no `illegal` part, and `judge.json` named 6 seeds to judge (9, 1, 4, 0, 8, 11).
- **What was true:** all 12 seeds were NOT BUILDABLE, every one on the electrode pads. E+1 / E-1 are
  `PinHeader_1x01_P2.54mm_Vertical` footprints whose pad 1 is a **12 mm round pad with an 8.5 mm drill**
  (a snap-electrode site), inside a **3.6 mm** courtyard. check_assembly occupies a part by courtyard ∪ pad
  copper (`legality.occupancy_shape`, #1094), so it sees the 12 mm disc; the anneal's overlap term prices the
  3.6 mm courtyard, so it parks parts in the disc's footprint. Measured per seed (check_assembly
  `--baseline fixed.kicad_pcb`): s0 J2 pads SHORT onto E-1's pad (pad_intersection 0.18 mm²); s1 U9
  courtyard 0.63 mm² / 0.35 mm deep into E+1; s2 U4 pads on E-1 (0.63 mm²) and R12 on E+1; s3 U2 pads on
  E+1 (6.25 mm², depth 4.03 mm); s4 U8; s5 U9 pads on E+1; s6 R4 on E+1 + J6 on E-1; s7 U2 on E+1; s8 J5/J6
  on E-1; s9 U3; s10 J5 pads on E-1; s11 J5 on E+1. The JUDGE named seeds that could not be DONE.
  A whole placement pass was lost; the fix was an input change (intent `keepouts[]` circles r 6.05 mm round
  E+1 and E-1, F and B), after which 10 of 12 pass-2 seeds were buildable.
  Nothing in the chain WARNED that a fixed part's pad reaches 4.2 mm past its courtyard:
  not `check_floorplan --emit-intent`, not `check_groups`, not place_simple's own pre-flight.
- **Reproduce:**
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gpm/18_uecg/repro/fixed.kicad_pcb 'wk/gpm/18_uecg/repro/p{seed}.kicad_pcb' --groups wk/gpm/18_uecg/repro/groups.json --intent wk/gpm/18_uecg/repro/intent_pass1_like.json --seeds 1 --json 'wk/gpm/18_uecg/repro/p{seed}.json'
  python3 -X utf8 py_tools/check_assembly.py wk/gpm/18_uecg/repro/p1.kicad_pcb --baseline wk/gpm/18_uecg/repro/fixed.kicad_pcb
  ```
  (`intent_pass1_like.json` is the run's intent with `keepouts` emptied.) An already-placed pass-1 seed is
  kept too: `python3 -X utf8 py_tools/check_assembly.py wk/gpm/18_uecg/repro/pass1_s1.kicad_pcb --baseline wk/gpm/18_uecg/repro/fixed.kicad_pcb` -> `E+1 <-> U9 ... COURTYARD-BLOCKING`, NOT BUILDABLE.
- **gh issue search** (`"pad larger than courtyard"`, `"pad copper past courtyard place_simple"`): nothing
  covers it. Closest: #1297 (place_simple and pad bounding boxes on DECLARED poses, closed) and #628
  (milled contours invisible to placement legality, closed) -- neither is this.

## 2. (skill + tools) The power widths a route step REQUESTS reach no grader: judge, board_score, check_complete and grade.py all leave `net_widths` ungraded, and the verifier FAILs on it

- **Tool / command:** the chain's `route.py ... --power-nets ... --power-nets-widths 0.4 0.4 0.3 0.3 0.3 0.5 0.5 0.7 0.7 0.7`
  (the /analyze-power-nets widths), then `board_score` / `check_complete` / `grade.py` with the spec flags the
  board declares, as SKILL.md §1 says.
- **What it claimed:** board_score BLOCKING=0, check_complete DONE, grade.py `"done": true` -- with
  `net_widths` listed as UNGRADED ("no --net-min-widths given").
- **What was true:** graded at the requested widths, 7 power nets are under: e.g. the battery path
  `Net-(F1-Pad1)` 31.34 of 42.11 mm under 0.7 (narrowest 0.127), VBUS 9.09 mm under 0.7, +3V3 5.61 mm
  under 0.3 (verifier call 1, which FAILed the spec lens on it). route.py does print it
  (`power copper shipped under width` rows, "Wide route blocked - retrying at default track width
  (neck-down)"), but nothing turns the requested widths into the `--net-min-widths` file the DONE graders
  need: SKILL.md §1 passes `--net-min-widths` only when "the board declares" one, §4 says "grade power widths
  with board_score --net-min-widths", and the board's own files declare none. A requested width also cannot
  be met at the pads by construction: the neck-down caps a rail at the pad's short side (#1318), so
  +3V3 / GND at the 0.2 mm QFN pads can never pass a per-segment 0.3 / 0.4 spec. Cost: one of the three
  verifier calls and ~20 min (arms P, Q, R, W1 to deliver the widths: none got there without losing
  completion; the board was kept and the spec re-declared from IPC-2221, REPORT §2).
- **Reproduce:** `python3 -X utf8 py_tools/board_score.py wk/gpm/18_uecg/repro/delivered_copy.kicad_pcb --net-min-widths wk/gpm/18_uecg/power_widths.json --quiet` (net_widths=7) against the same command without the flag (net_widths ungraded, BLOCKING=0).
- **gh issue search** (`"power widths requested net-min-widths"`): **#1033** (CLOSED) "route.py: the bulk route lays power nets at the signal --track-width instead of --power-nets-widths (~34% of +3V3 length at 0.127)" is the same symptom, still present here (74% of `Net-(F1-Pad1)` length at 0.127 where 0.7 was asked); #1169 (closed, oracle straps at class width) and #1318 (closed, neck-down rule) are related. None covers the grading half (no grader sees the requested widths).

## 3. `board_score --impedance-nets` / check_complete grade only the reference plane, so a declared 50 Ω net that ships at 64-80 Ω reads DONE

- **Tool / command:** `py_tools/board_score.py BOARD --impedance-nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)' ...` and
  `check_complete.py` with the same flag, on the board whose `.kicad_pro` records both nets under
  `net_impedance` (`ohms 50, coplanar_gap 0.25, applied: true`, written by `route.py --impedance 50 --coplanar-gap 0.25`).
- **What it claimed:** `impedance 0`, BLOCKING=0; check_complete DONE.
- **What was true:** route.py solved 0.920 mm and logged `Wide impedance route blocked - routed short edge at
  0.4601mm (down from 0.9201)`; the shipped copper is 0.46-0.59 mm / 0.23-0.46 mm, and
  `check_impedance.py --coplanar-gap 0.25` measures **64.4 Ω and 80.5 Ω** (exit 1, gap off-target 57-58 %).
  The impedance component counts only reference-plane crossings (`segments_over_void`), never Z0 or the
  solved width, so the declaration the project file carries is never held to. Verifier call 2 FAILed the
  spec lens on it. A forced re-route of `Net-(AE1-Pad1)` (`--force-reroute --impedance 50 --grid-step 0.05`)
  again shipped 0.46 mm, half the solved width. Cost: one verifier call and ~10 min; the fix was to drop the
  declaration (both nets are electrically short; REPORT §2) and re-route the chain.
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/board_score.py wk/gpm/18_uecg/repro/final_route_old2_iter2.kicad_pcb --impedance-nets 'Net-([CA][1E][0-9]-Pad1)' --quiet
  python3 -X utf8 py_tools/check_impedance.py wk/gpm/18_uecg/repro/final_route_old2_iter2.kicad_pcb --coplanar-gap 0.25 --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)'
  ```
  (first: impedance=0; second: measured 64.4 / 80.5 Ω, exit 1).
- **gh issue search** (`"impedance width not met"`): nothing covers it; #607 (closed, stripline asymmetry) and #175 (closed, meander clearance) are other impedance bugs.

## 4. board_score / check_complete keep only the LAST `--impedance-nets`, and grade.py's repeatable `--spec` produces exactly that, silently

- **Tool / command:** `py_tools/board_score.py BOARD --impedance-nets 'Net-(AE1-Pad1)' --impedance-nets 'Net-(C10-Pad1)'`;
  `.claude/skills/plan-pcb-placement/scripts/grade.py ... --spec impedance-nets=A --spec impedance-nets=B`
  (grade.py turns each `--spec` into its own `--impedance-nets X` pair).
- **What it claimed:** impedance component ran, `count 0`, BLOCKING=0.
- **What was true:** only the last flag's net was analysed (`nets_analyzed: 1`). On the first routed board,
  whose `Net-(AE1-Pad1)` has 0.436 mm over a B.Cu void: flags in the order AE1, C10 -> `impedance 0`,
  BLOCKING=0 (passes); order C10, AE1 -> `impedance 1`, BLOCKING=1. A defect is hidden by argument order.
  Workaround used for grade.py: one glob that matches exactly the two RF nets, `Net-([CA][1E][0-9]-Pad1)`.
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/board_score.py wk/gpm/18_uecg/repro/final_route_old1_iter2.kicad_pcb --impedance-nets 'Net-(AE1-Pad1)' --impedance-nets 'Net-(C10-Pad1)' --quiet
  python3 -X utf8 py_tools/board_score.py wk/gpm/18_uecg/repro/final_route_old1_iter2.kicad_pcb --impedance-nets 'Net-(C10-Pad1)' --impedance-nets 'Net-(AE1-Pad1)' --quiet
  ```
  (first: impedance=0; second: impedance=1).
- **gh issue search** (`"impedance-nets repeated flag"`, `"grade.py --spec repeated"`): nothing covers it.

## 5. route.py's shipped-rules disclosure lists via narrowings and "advanced" fab-tier escalations on a net that ships with no via; signal-net taps are called "plane tap"

- **Tool / command:** `py_router/route.py in_ka.kicad_pcb s2b.kicad_pcb --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)' --impedance 50 --coplanar-gap 0.25 --layers F.Cu --clearance-ceiling 0.15 --via-size 0.45 --via-drill 0.3` (the RF step).
- **What it claimed:** `WARNING: plane tap U1.30: escalated standard->advanced fab floor (0.25/0.15 via etc.)`
  (U1.30 is the ANT pin, a signal net), `3 fab-tier escalation(s) to advanced`, and in
  `JSON_SHIPPED_RULES` two `via_diameter 0.45 -> 0.25, site "via-in-pad clamp (floor)"` rows on net 29
  (`Net-(C10-Pad1)`). check_complete --authored-from later reads such rows as floors the board went below.
- **What was true:** `s2b.kicad_pcb` carries **0 vias** (parsed: `[]`); no via on either RF net ships in the
  delivered board. The "shipped" rows describe candidates that were not shipped. The same "plane tap"
  wording appears on the signal step for SCLK/COPI/CIPO/CS pins (U7.13, U1.17, U7.14, U7.1, U1.18, U2.14).
  Cost: a few minutes deciding whether the RF feed had a via-in-pad (it does not).
- **Reproduce:**
  ```
  python3 -X utf8 py_router/route.py wk/gpm/18_uecg/repro/final_route_in_ka.kicad_pcb wk/gpm/18_uecg/repro/rf_out.kicad_pcb --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)' --impedance 50 --coplanar-gap 0.25 --layers F.Cu --clearance-ceiling 0.15 --via-size 0.45 --via-drill 0.3 --json-out wk/gpm/18_uecg/repro/rf_out.json
  python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb;print(len(parse_kicad_pcb('wk/gpm/18_uecg/repro/rf_out.kicad_pcb').vias))"
  ```
  (log: `plane tap U1.30 ... escalated`; JSON_SHIPPED_RULES: via_diameter rows; board: 0 vias.)
- **gh issue search** (`"JSON_SHIPPED_RULES via not shipped"`, `"plane tap escalation signal net"`): no
  match. Related, closed: #857 (fab-tier escalation disclosure), #1318 (fine-pitch tap widths).

## 6. render_placement reports BODY STACKS and pad conflicts against a round pad's bounding box

- **Tool / command:** `py_tools/render_placement.py wk/gpm/18_uecg/delivered.kicad_pcb --json-out ...`
- **What it claimed:** `2 BODY STACK(S) -- pads of two parts physically overlapping (solid red). Not a
  clearance graze; no router can fix one.`, `b_body_overlap_pairs [[E-1, L2], [E-1, L3]]`,
  `metrics.pad_intersection_pairs 2`, `pad_shortfall 0.71`, and the PNG frames L2/L3 in orange.
- **What was true:** L2 / L3 pad copper is **0.81-2.87 mm clear** of E-1's 12 mm round pad (shapely, pad
  rect to the disc); they only fall inside the disc's 12 x 12 mm bounding box. check_assembly (0 pad pairs,
  buildable) and check_drc (no violations) agree the board is clean. The skill warns render's pad-stack list
  and metrics are bbox counts (§4), but the PNG and the headline still say "physically overlapping", which
  a verifier told to LOOK at the PNG has to argue with.
- **Reproduce:** `python3 -X utf8 py_tools/render_placement.py wk/gpm/18_uecg/repro/delivered_copy.kicad_pcb -o wk/gpm/18_uecg/repro/delivered_copy.png --json-out wk/gpm/18_uecg/repro/delivered_copy_render.json` then `python3 -X utf8 py_tools/check_assembly.py wk/gpm/18_uecg/repro/delivered_copy.kicad_pcb --baseline wk/gpm/18_uecg/uecg.kicad_pcb`.
- **gh issue search** (`"render_placement body stack bounding box round pad"`, `"body stack false positive render_placement"`): nothing covers it.

## 7. No PDF reader on this machine: poppler is missing, so the skill's datasheet recipe and the Read tool cannot open a datasheet (helper written)

- **Tool / command:** the skill's §3.5 recipe (`pdftotext`, `pdftoppm`, `pdfimages`) and the Read tool's PDF mode.
- **What it claimed:** Read on a PDF: `pdftoppm is not installed. Install poppler-utils`; `which pdftotext pdftoppm pdfimages`: not found.
- **What was true:** no repo or system tool could read the nRF52832 product specification. Wrote
  `wk/gpm/18_uecg/helpers/pdfpages.swift` (macOS PDFKit: page count, text search, text dump, page -> PNG),
  which found the reference-circuitry pages (539-543 of 544) and rendered Figures 168 and 170. ~5 min.
- **Reproduce:** `which pdftoppm pdftotext; swift wk/gpm/18_uecg/helpers/pdfpages.swift count <any.pdf>`.
- **gh issue search** (`"poppler pdftoppm datasheet"`): nothing.

## 8. Nordic's datasheet hosts are behind a Cloudflare challenge; the skill's maker-first recipe returns an HTML page saved as `.pdf`

- **Tool / command:** `curl -sSL -o ... https://infocenter.nordicsemi.com/pdf/nRF52832_PS_v1.4.pdf` (and
  docs.nordicsemi.com v1.8, docs-be, nordicsemi.com/-/media); WebFetch of the HTML reference-circuitry page.
- **What it claimed:** curl exit 0 and a file named `.pdf`.
- **What was true:** each was a 5-6 kB "Just a moment..." Cloudflare page (`file`: HTML). The HTML page via
  WebFetch gives the BOM but no layout figure. The usable copy was SparkFun's CDN
  (`cdn.sparkfun.com/datasheets/Wireless/Bluetooth/nRF52832_PS_v1.0.pdf`, PS v1.0, 2016-02-17, Nordic's own
  file), an older revision than v1.4-v1.9. ~4 min of tries. Not a repo bug; the skill could name
  "check `file <pdf>` after every download" -- the saved name lies.
- **Reproduce:** `curl -sSL -o /dev/stdout https://infocenter.nordicsemi.com/pdf/nRF52832_PS_v1.4.pdf | head -c 200`.
- **gh issue search:** not a repo issue; none searched beyond the above.

## 9. (skill) The judge key ignores a template member the anneal left far off its template; nothing says to repair it

- **Tool / command:** `py_placer/judge_seeds.py` ranking (`quick_score.judge_key`), SKILL.md §3.7 "Keep the best".
- **What it claimed:** best seed 8 (quick blocking 2).
- **What was true:** seed 8's `check_floorplan` WARN: `templates[0] (U1): 2 of 6 member(s) off the template
  -- worst L2, a pad 5.94 mm from its template position` -- the nRF52's DC/DC inductor 6 mm from DCC, with
  L3 sitting on L2's template spot. §3.5 says the router cannot see this and the board "can route clean and
  still work badly", but §3.7 keeps by routed blockers only and §3.5 step 7 only asks to REPORT the drift.
  I restored L2/L3 with `place_pose set` (the CHOSEN.json `after` list); the full route of the restored
  board was better on every metric (139 vias / 929.6 mm vs 141 / 1007.5 mm for seed 8 as placed).
- **Reproduce:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/18_uecg/s8.kicad_pcb --intent wk/gpm/18_uecg/intent_run.json | grep template`.
- **gh issue search** (`"template drift judge"`): nothing.
