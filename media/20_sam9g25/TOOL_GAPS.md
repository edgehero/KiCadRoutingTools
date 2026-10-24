# TOOL_GAPS -- 20_sam9g25

Ranked by what each cost this run. Every command runs from the worktree root
(`cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`),
with its inputs in `wk/gpm/20_sam9g25/repro/`. Issue searches are read-only
`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"`.

## 1. The edge rule passes a side-push switch whose actuator faces ALONG its edge (facing abstains silently)

- **Tool / command:** `check_floorplan` (and `place_simple`'s edge seat, which reads the same facing):
  ```
  python3 -X utf8 py_tools/check_floorplan.py wk/gpm/20_sam9g25/repro/facing_final_v1.kicad_pcb --intent wk/gpm/20_sam9g25/repro/intent_run.json
  ```
- **What it claimed:** `0 error(s)`; `SW1 west: overhang 0.0000mm ... pass` and
  `SW2 south: ... pass`, with **no facing word at all** (J2 on the same run
  prints `facing west [courtyard+fab+marker, strong] pass`). The skill (§3.4)
  says to read `facing ... pass` or `facing abstained (...)`; neither is printed.
- **What was true:** the EVQP7C actuator is drawn on the footprint's local +y
  (F.Fab lines y 1.45 -> 2.1). SW1 sat at rot 0 (actuator pointing SOUTH,
  along the west edge), SW2 at rot -90 (actuator WEST, along the south edge).
  The verifier read the tab out of pcbnew and failed the board on it. With
  `mating_face: "+y"` added to the two `edge_connectors[]` rows the same
  command prints `facing south [declared, strong] FAIL` / `facing west ...
  FAIL`, so the rule works once told -- it just never says it could not tell.
- **Cost:** verifier call 1 failed; a hand repair (`place_pose set SW1 102.1
  67.053 --rot 270`, `set SW2 128.9 97.9 --rot 0`) and a full re-route (two
  more chains, v4 and v5).
- **Issues:** `"facing abstained switch"`, `"side push switch edge"`,
  `"mating_face actuator"`: none.

## 2. Courtyard-conditioned `.kicad_dru` rules are invisible to the router, check_drc and kicad_drc_compare

- **Tool / command:**
  ```
  python3 -X utf8 py_router/check_drc.py wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_pcb --clearance-margin 0.1
  python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_pcb --baseline wk/gpm/20_sam9g25/sam9g25.kicad_pcb
  kicad-cli pcb drc wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_pcb --refill-zones --severity-all --format json -o wk/gpm/20_sam9g25/repro/dru_kdrc.json
  ```
- **What it claimed:** check_drc `NO DRC VIOLATIONS FOUND!` (it prints that the
  three rules have "a non-layer scope -- skipped, KiCad will still enforce
  it"); kicad_drc_compare `kicad=0 check_drc=0 ... CONSISTENT`; route.py's
  fab escalation narrowed tracks to 0.0889 mm with no warning about the rule.
- **What was true:** the board's own `.kicad_dru` (`CPU BGA fanout`, `DRAM BGA
  fanout`, `LCD Bus Connections`: `track_width (min 0.1016mm)` on outer layers
  `A.insideCourtyard('U1'|'U200'|'J6')`) is violated: kicad-cli reports **20
  `track_width` errors** (`/memory/ddr-d6` 18 segments at 0.0889, LED-BLUE 2
  at 0.0974). kicad_drc_compare's `kicad=0` counts only its copper classes, so
  the one channel meant to catch what check_drc misses read CONSISTENT.
- **Cost:** verifier call 1 failed; v4 still had 26 such errors; two arms
  (`--escalation off` lap reverted; `--escalation board` left 3 DDR nets
  open); fixed with `helpers/fab_track_floor.txt` passed as `--fab-overrides`
  (track floor 0.1016, advanced via/clearance floors kept).
- **Issues:** `"insideCourtyard"`, `"kicad_dru condition courtyard"`,
  `"track_width kicad_drc_compare"`: none (#447 is board-edge width).

## 3. route_diff `--impedance` writes a spec that board_score / check_complete never grade (DONE printed)

- **Tool / command:**
  ```
  python3 -X utf8 check_complete.py wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_pcb --intent wk/gpm/20_sam9g25/repro/intent_run.json --baseline wk/gpm/20_sam9g25/sam9g25.kicad_pcb
  python3 -X utf8 py_tools/board_score.py wk/gpm/20_sam9g25/repro/dru_delivered_v3.kicad_pcb --intent wk/gpm/20_sam9g25/repro/intent_run.json --baseline wk/gpm/20_sam9g25/sam9g25.kicad_pcb --impedance-nets 'USB*-D*' '/IO?expansions/usb-a*' --quiet
  ```
- **What it claimed:** check_complete `VERDICT: DONE` with impedance
  "UNEXAMINED ... no spec was given".
- **What was true:** the project carries `kicad_routing_tools.net_impedance` on
  11 nets (written by `route_diff.py --impedance 90/100`; `check_impedance`
  prints "Auto-read 11 net impedance declaration(s) from the sibling
  .kicad_pro"), so a spec WAS given -- by the chain. Graded:
  `impedance=8` blocking on the 8 USB nets (42 reference-plane crossings, 30
  segments over In1 voids); the verifier counted 11/11. My own glob
  `/memory/ddr-ck*` also declared `ddr-cke` a 100-ohm differential net.
- **Cost:** verifier call 1 failed; re-route without `--impedance` (pairs drawn
  at the stackup geometry, 0.171/0.1016 USB and 0.139/0.1016 CK, undeclared).
- **Issues:** `"net_impedance check_complete"`, `"impedance declaration
  ungraded"`: #964 (closed, "Declared but never read: five channels where a
  fact is written down and no grader joins it") is the class; this channel is
  not among its five.

## 4. route.py ships a different-net crossing short and reports `failed: 0`

- **Tool / command:**
  ```
  python3 -X utf8 py_router/route.py wk/gpm/20_sam9g25/repro/short_s6.kicad_pcb wk/gpm/20_sam9g25/repro/short_out.kicad_pcb \
    --nets '*' --no-bga-zones --clearance-ceiling 0.1016 --track-width 0.1016 --via-size 0.45 --via-drill 0.3 \
    --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 \
    --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5 \
    --ripped-route-avoidance-cost 3 --track-proximity-cost 2
  python3 -X utf8 py_router/check_drc.py wk/gpm/20_sam9g25/repro/short_out.kicad_pcb --clearance-margin 0.1
  ```
- **What it claimed:** `JSON_SUMMARY_MIN` `failed: 0`, `pad_pairs_open: 0`, no
  warning about the copper it wrote.
- **What was true:** check_drc FOUND 5 DRC VIOLATIONS, all RMII-TX0 <-> VDD-IO
  on F.Cu, one `SEGMENT-CROSSING` at (141.150, 91.850). The route trace
  (`KICAD_ROUTE_TRACE=1`, `arms/rA/s7_routetrace.json`) shows event 95 laying
  RMII-TX0's 45-degree track (141.3,91.7)-(139.2,93.8) and event 240, a VDD-IO
  route of 377 0.05 mm segments (the poured net's reconnect), running straight
  through it at (141.15,91.85). Reproduced 3 times (arm rA, the v2 re-run,
  the repro command).
- **Cost:** an extra lap (`--force-reroute RMII-TX0` alone broke LCD-D10 and was
  reverted; RMII-TX0 + LCD-D10 together fixed it).
- **Issues:** `"crossing short route.py"`, `"segment crossing different
  nets"`: #169 (closed), #673 (closed), #1260 (closed) -- the same class, not
  this producer.

## 5. route.py's plane finalize diverged on one of four identical runs

- **Tool / command:**
  ```
  for k in a b; do python3 -X utf8 py_router/route.py wk/gpm/20_sam9g25/repro/jitter_s6.kicad_pcb wk/gpm/20_sam9g25/repro/jitter_$k.kicad_pcb \
    --nets '*' --no-bga-zones --clearance-ceiling 0.1016 --track-width 0.1016 --via-size 0.45 --via-drill 0.3 \
    --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 \
    --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5 \
    --ripped-route-avoidance-cost 3 --track-proximity-cost 2 --via-cost 1200 > wk/gpm/20_sam9g25/repro/jitter_$k.log 2>&1; done
  grep -h "Zone SPLIT" wk/gpm/20_sam9g25/repro/jitter_?.log
  ```
- **What it claimed:** nothing (CLAUDE.md: "Routing is deterministic").
- **What was true:** arm rH (`arms/rH/s7_route.log`) printed `Zone SPLIT: 3
  island (23.8 mm^2)`, the re-run in `final_route_old3/` and the two repro
  runs (and one on a copy carrying the other run's uuids) all print `4
  island(s) (117.8 mm^2)`, on boards identical with uuids stripped and the same
  argv; escalations 337 vs 335, final 368 vs 373 vias. No timeout logged.
  **1 of 4 runs diverged**, and nothing in its log says why.
- **Cost:** the best measured board (368 vias) could not be reproduced in
  `final_route/`.
- **Issues:** `"determinism exact fill"`, `"nondeterministic route"`: #490
  (closed, refill jitter); CLAUDE.md notes oracle-chain spread. Known class.

## 6. A dead-end stub of a POURED net survives every route.py pass; no CLI removes it

- **Tool / command:**
  ```
  python3 -X utf8 py_router/check_weird.py wk/gpm/20_sam9g25/repro/stub_s10.kicad_pcb
  ```
  then any route.py pass with GND in `--nets` (pours-only or `'*'`).
- **What it claimed:** the late cleanups (#1166 sweep, dead-end prune) leave
  the board clean; check_complete then says INCOMPLETE on weird_copper.
- **What was true:** `dangling-end: net GND (F.Cu) ... free end` survived a
  pours-only lap and a `'*'` lap (arms/rE). Every such stub this run ended in
  the 1 mm gap between the designer's two hatched F/B GND zones (x 125-126):
  the router's fill model credits the zone edge, the fill does not reach it
  (KiCad also flags them `track_dangling`). `--force-reroute` skips plane nets
  by design. Wrote `helpers/drop_segment.py` (removes exactly one matching
  `(segment ...)` after `copy_board`); used on the SHIPPED board for two GND
  stubs (F.Cu (125.3,67.3)-(126.4,67.3), (124.8,91.0)-(125.0,91.2)), each
  re-verified.
- **Issues:** `"dangling segment GND"`, `"dead-end stub poured net"`: #1166
  (closed, dangling VIAS), #162 (open, same-net redundant copper).

## 7. A later pass's hint blames the fanout for a ball the first route step stripped

- **Tool / command:**
  ```
  python3 -X utf8 py_router/route.py wk/gpm/20_sam9g25/repro/hint_s7.kicad_pcb wk/gpm/20_sam9g25/repro/hint_out.kicad_pcb --nets '*' --no-bga-zones --clearance-ceiling 0.1016 \
    --track-width 0.1016 --via-size 0.45 --via-drill 0.3 --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS \
    --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5
  ```
- **What it claimed:** `Hint: pad U1.C13 is a fanout-dropped ball (no escape
  stub) ... Re-run the fanout for this net`.
- **What was true:** the fanout escaped 133/133. The FIRST route step (v1
  `s7_route.log` l.1008) ripped `/memory/ddr-d11` as a blocker; `PARTIAL ...
  dropped 5 colliding piece(s)`, `terminal_restores_broken`. check_reachability
  `--pad U1.C13`: PASSABLE on the placement, CAGED with the routing. Two scoped
  laps did not recover it.
- **Cost:** a whole extra chain (arm rA).
- **Issues:** #1311 (closed: "terminal restore of a ripped BGA escape is erased
  ... and the hint then blames the fanout"), #1156 (closed): a regression or
  an uncovered path.

## 8. analyze_power_paths traces no path and sizes the wrong nets

- **Tool / command:** `python3 -X utf8 wk/gpm/20_sam9g25/repro/power_repro.py`
  (the analyze-power-nets skill's Steps 1-5 with every unknown classified).
- **What it claimed:** GND 3.0 mm, VDD-IO 2.0, VDD_DDR 2.0, VDD_CORE 1.0,
  +1V0_LDO 1.0, BAT_GND 1.0.
- **What was true:** `paths traced: 0` with J2/J3/U2 as sources and D2/Q1 as
  pass-throughs; the real input path (VBUS -> Q1 -> VIN -> U2) gets no width
  (VIN, VBUS absent) while 2-3 mm is recommended for rails into 0.8 mm-pitch
  BGA balls. Overridden by hand (planes 0.3, +1V0_LDO 0.25, VIN/VBUS 0.5).
- **Issues:** `"analyze_power_paths width"`, `"power paths traced"`: none.

## 9. fit_template seats a member outside the intent's own decap limit, silently

- **Tool / command:**
  ```
  python3 -X utf8 py_tools/fit_template.py wk/gpm/20_sam9g25/repro/fixed.kicad_pcb --sketch wk/gpm/20_sam9g25/repro/u2_sketch_v1.json \
    --intent wk/gpm/20_sam9g25/repro/intent_given.json -o wk/gpm/20_sam9g25/repro/u2_row_v1.json
  ```
- **What it claimed:** C9 `at (-1.317, +8.223) ... (4.86 mm off the chip)`,
  only a ground-return NOTE.
- **What was true:** the intent holds C9 in `decaps.within_radius_refs` with
  `max_distance_mm` 4.2375; at that pose C9 is 5.76 mm from U2 ->
  `decap_ungraded` ERROR in 7 of 12 pass-1 seeds. Cost: a placement pass.
- **Issues:** `"fit_template decap"`, `"template decap limit"`: none.

## 10. A group `edge` hint does not lay a long through-hole header on the edge

- **Tool / command:**
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gpm/20_sam9g25/repro/fixed.kicad_pcb wk/gpm/20_sam9g25/repro/p1_s5.kicad_pcb \
    --groups wk/gpm/20_sam9g25/repro/groups_pass1.json --intent wk/gpm/20_sam9g25/repro/intent_pass1.json --seed 5
  ```
- **What it claimed:** `"edge": "E"` (J6, 2x22 1.27 mm THT) and `"edge": "N"`
  (J3, 2x18) are objective terms.
- **What was true:** J6 lay across the interior in 6 of 12 pass-1 seeds (s5
  horizontal at y~73 from x 165 to 138), a 28 mm wall on all 4 layers; J3 sat on
  the SOUTH edge in 7 of 12. Fixed with `edge_connectors[]` rows (+`mating_face`).
- **Issues:** `"edge hint header"`, `"edge hint group"`: none (#1330 is `apart`).

## 11. The skill's PDF step needs poppler (absent); Microchip refuses the download

- **Tool / command:** the Read tool with `pages` on a datasheet PDF
  (`plan-pcb-placement` §3.5 step 2).
- **What it claimed:** "open it with the Read tool and `pages`".
- **What was true:** `pdftoppm is not installed`; pdftotext/pdfimages absent
  too. Wrote `helpers/pdftool.py` over PyMuPDF (`pip --target
  helpers/pylib`). `ww1.microchip.com` returned Access Denied; the Farnell copy
  (DS20006388B) was used.
- **Issues:** `"pdftoppm poppler"`: none.

## 12. check_weird calls a T-junction connected; KiCad calls it `track_dangling`

- **Tool / command:** `python3 -X utf8 py_router/check_weird.py wk/gpm/20_sam9g25/delivered.kicad_pcb`
  against `kicad-cli pcb drc ... --refill-zones` on the same board.
- **What it claimed:** `NO WEIRD THINGS FOUND!`.
- **What was true:** KiCad reports `track_dangling` VBUS B.Cu (110.1, 77.3),
  0.42 mm: the end lies on the middle of VBUS's own (110.6,77.3)-(109.7,77.3)
  segment. Electrically joined (0.5 mm copper overlaps), so left as shipped,
  but the two graders disagree. Cost: small.
- **Issues:** `"track_dangling T-junction"`: #1291 (closed, off-grid tap
  T-junction stubs), #1217 (closed).
