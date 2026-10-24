# Tool gaps hit on 11_daplink (gpm campaign)

Ranked by what each cost this run. Every repro command runs from WT
(`~/Documents/git/krt-gpm`) with `export PATH="$HOME/.venvs/krt/bin:$PATH"`;
the boards they need are in `wk/gpm/11_daplink/repro/` (copied with `copy_board.py`,
siblings included). `gh issue list` searches were read-only.

## 1. The USB-C seat flushes the courtyard, not the shell: on a rounded-corner outline the drawn body is "unmeasured", so the receptacle sits 0.505 mm behind its own PCB-Edge line

- **Tool / command:** `place_simple.py`'s edge seat and `check_floorplan.py`'s `edge_connector` overhang
  (`placement/connector_geometry.band_amount`), for P1 `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`,
  declared `edge: west` with no band (the emitter's default low end, 0).
- **What it claimed:** `P1 west: overhang 0.0000mm [legacy_occupancy@margin=0] pass; ... facing west [courtyard+fab+marker, strong] pass`.
  SKILL §3.4 says the band "is read at zero margin, on the drawn body or else the courtyard (#1301)".
- **What was true:** the footprint has a clean F.Fab rectangle and draws its own `PCB Edge` line on Dwgs.User at the
  shell front (local y 3.675, the same as the F.Fab front); its courtyard reaches 0.505 mm further (4.18). The body
  was not read because the board's outline is a rectangle with ROUNDED corners, and `connector_geometry` measures a
  body only against "a rectangular Edge.Cuts outline with no other cuts. Anything else is unmeasured" -- so every
  edge part on this board is graded and SEATED on its courtyard. The seat therefore put the courtyard on the outline
  and the shell front 0.505 mm inboard (x = 100.505 against the outline at 100.000; the verifier measured the body
  front 0.455 mm in). A plug's overmold then meets the board edge before it is fully home. Nothing failed: the grade
  is "pass" in the courtyard currency, and only reading `overhang_basis` shows the body was never measured.
- **Cost:** the largest of the run: verifier call 1 found it after a PASS; a hand repair (`place_pose set P1 103.675
  113.2369 --rot 270`), an `overhang_mm` 0.45-0.6 row for P1 in the courtyard currency, a full re-route, re-label,
  re-fill and verifier call 2 (~15 min).
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/check_floorplan.py wk/gpm/11_daplink/repro/s10_placed.kicad_pcb --intent wk/gpm/11_daplink/intent.json --json wk/gpm/11_daplink/repro/s10_floorplan.json | grep "P1 west"
  # -> overhang 0.0000mm [legacy_occupancy@margin=0]; body_overhang_mm null in the JSON; P1 at x=104.18 rot 270,
  #    so the F.Fab front / PCB-Edge line (local y 3.675) is at x = 104.18 - 3.675 = 100.505, the courtyard (4.18) at 100.000
  ```
- **Existing issues:** searches "body overhang unmeasured rounded outline", "legacy_occupancy courtyard overhang
  receptacle", "rounded corners outline unmeasured": none on the rounded-outline fallback. Related: #1301 (the
  zero-margin courtyard reading; its docstring cites this board's J2/J3), #1155 and #987 (CLOSED, edge seat / band).

## 2. route.py: an all-nets iteration pass with nothing to route ships a new 1.5 mm dangling segment

- **Tool / command:** `py_router/route.py` as plan-pcb-routing's Step 2d iteration pass
  ("bake two passes into every plan"), on a board that was complete and clean.
- **What it claimed:** exit 0, `JSON_SUMMARY_MIN` failed 0 / open_single [] / multipoint_deficit 0;
  its log says "Octolinear smoothing: collapsed 2 staircase span(s) on 1 net(s)", "Merged 1
  collinear joint(s)", "Stripped 2 stale input segment(s) of ripped/re-routed nets", "Removed 10
  dead-end input segment(s) from the output" -- i.e. a tidy, nothing-to-do pass.
- **What was true:** the input graded `check_weird` NO WEIRD THINGS; the output carries
  `dangling-end: net /PA12 (F.Cu) at (115.300, 112.200): free end, dangling segment 1.500mm
  (rooted at (113.800, 112.200))`. `check_complete` then reads **INCOMPLETE -- weird_copper: not
  clean (exit 1)** on a board that was DONE one step earlier. Nothing in route.py's own summary
  says it made the board worse, and its improvement gate did not revert it.
- **Cost:** the seed-1 chain's two "free" iteration passes turned a DONE board into an INCOMPLETE
  one; I had to find the step that did it and re-plan (kept: on the shipped seed-10 chain the same
  two passes stayed clean and trimmed 0.84 mm of copper).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_weird.py wk/gpm/11_daplink/repro/iter_in.kicad_pcb     # NO WEIRD THINGS FOUND
  python3 -X utf8 py_router/route.py wk/gpm/11_daplink/repro/iter_in.kicad_pcb wk/gpm/11_daplink/repro/iter_out.kicad_pcb \
      --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --layer-costs 1.0 1.0 \
      --escalation board --power-nets GND '+5V' '+3.3V' --power-nets-widths 0.7 0.7 0.7
  python3 -X utf8 py_router/check_weird.py wk/gpm/11_daplink/repro/iter_out.kicad_pcb    # dangling-end /PA12, 1.500 mm
  ```
- **Existing issues:** searches "dangling", "smoothing dangling", "Stripped stale input segment":
  nearest are #1311 (CLOSED, terminal restore erased by the end-of-run stale-input strip), #1234
  (OPEN, micro-segment chains entering no pad), #1063 (CLOSED, check_weird vs cleanup). None covers
  a dangling segment created by an iteration pass on a complete board.

## 3. analyze_power_paths sizes a ~0.3 A board's rails at 1.2 / 1.2 / 2.0 mm: current counted once per power PIN, plus each source's full rating

- **Tool / command:** `py_tools/analyze_power_paths.get_power_net_recommendations` (the
  `/analyze-power-nets` skill, which plan-pcb-routing Step 4 now requires on every board).
- **What it claimed:** `{'+3.3V': 1.2, 'GND': 2.0, '+5V': 1.2}` after classifying the STM32F103CB
  at its datasheet 50 mA max, the AMS1117 at its 1 A rating and USB VBUS at 500 mA.
- **What was true:** the function adds a component's `current_rating_ma` once for EVERY power pin it
  has (`for pad_num ... if is_power_pin(...): net_currents[net] += current`): U2's 50 mA lands on
  +3.3V five times (VBAT, VDDA, 3x VDD = 250 mA) and on GND four times; P1's 500 mA lands on GND
  once per GND contact (A1, A12, B1, B12 = 2000 mA); the LDO's 1 A rating is added to +3.3V, +5V
  and GND as if it were load. The board's real draw is about 50 mA MCU + ~5 mA LEDs + a target-power
  ESTIMATE of 200 mA through J2/J3, so ~0.26 A; by the skill's own IPC table that is 0.7 mm. A
  2.0 mm GND / 1.2 mm rail request on a 50 x 20 mm board with a 0.5 mm-pitch LQFP is unroutable
  as asked and would have been carried into every route step.
- **Cost:** hand-correcting the widths (0.7 / 0.7 / 0.7 mm, recorded in REPORT.md as estimates);
  ~10 minutes reading the function to find why.
- **Repro:** `python3 -X utf8 wk/gpm/11_daplink/repro/power_overcount.py` prints
  `{'+3.3V': 1.2, 'GND': 2.0, '+5V': 1.2}`.
- **Existing issues:** searches "analyze_power_paths current power pin", "get_power_net_recommendations",
  "power width overestimate", "analyze-power-nets width": nothing covering it (#124, CLOSED wontfix,
  is the opposite complaint).

## 4. route.py lowers the board's copper-to-hole floor 0.25 -> 0.2 and says "unchanged by this step"; route_diff does it on a step that lays no copper

- **Tool / command:** `py_router/route.py` (and `route_diff.py`) DRC-settings writeback.
- **What it claimed:** route.py: `PROJECT_WRITES_JSON` lists only `min_copper_edge_clearance` and
  `min_via_drill`, then "FAB FLOOR RELAXED ... copper-to-hole clearance: 0.2 mm, **unchanged by
  this step** but still below the board's ORIGINAL 0.25mm".
- **What was true:** the input project has `rules.min_hole_clearance: 0.25`, the output project
  `0.2` (line 148 of both files). The step that changed it reports it as inherited. route_diff
  (`--nets /D+ /D-`, pair deferred, **0 segments and 0 vias written**) writes the same 0.25 -> 0.2
  and lists it. With the floor at 0.2, `check_drc`, `board_score` and KiCad's DRC grade copper-to-hole
  at 0.2. On this board the 8 copper-to-hole items under 0.25 (min 0.1751 mm) are all P1's own pads
  against P1's own NPTH pegs (library geometry, measured with kicad-cli at 0.25), so no routed copper
  hides behind it -- but nothing in the chain would have said so if it had.
- **Cost:** ~10 minutes tracing which step relaxed it; an extra kicad-cli DRC at the authored 0.25.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route.py wk/gpm/11_daplink/repro/hole_in.kicad_pcb wk/gpm/11_daplink/repro/hole_route_out.kicad_pcb \
      --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --escalation board
  grep -n '"min_hole_clearance"' wk/gpm/11_daplink/repro/hole_in.kicad_pro wk/gpm/11_daplink/repro/hole_route_out.kicad_pro
  ```
- **Existing issues:** search "hole clearance writeback relaxed": #1285 (CLOSED, "CLI
  --no-fix-drc-settings still lowers min_hole_clearance via in-run floor sync"), #1038 (CLOSED,
  routed copper vs the 0.25 copper-to-hole route.py announces; check_drc reads the relaxed value),
  #1195 (CLOSED, qfn_fanout lowers floors on a run that places no via). This is the same family
  still firing on main, with a false "unchanged by this step" on top.

## 5. A right-angle SMD pin header is not an edge part, so an undeclared one is placed mid-board

- **Tool / command:** `py_placer/placement/part_class.classify_part` (read by place_simple's edge seat
  and check_floorplan's edge rule).
- **What it claimed:** J2 and J3 (`Connector_Harwin:Harwin_M20-89005xx_1x05_P2.54mm_Horizontal`,
  male pins that stick 6 mm past the body) classify `connector_affinity`, confidence low, "no edge
  claim"; check_floorplan lists no edge row for them.
- **What was true:** a right-angle header mates off the board edge (placement-lessons: "Right-angle
  header | pins hang out | 98%" within 3 mm of the edge). With the intent as given (no row for them),
  place_simple put J2 at x = 127.4 / 117.8 mm on a 100-150 mm board (the middle of the bottom face) and
  J3 8.7 mm inboard of the east edge (probe: `old/probe_noJ/`, 2 seeds).
- **Cost:** a judgement and two hand-written `edge_connectors[]` rows in `intent_run.json` (east edge,
  overhang 6.0-6.5 mm), plus checking the facing/overhang reading.
- **Repro:**
  ```bash
  python3 -X utf8 -c "import sys;sys.path[:0]=['py_router','py_placer'];from kicad_parser import parse_kicad_pcb;from placement.part_class import classify_part;p=parse_kicad_pcb('wk/gpm/11_daplink/repro/s10_placed.kicad_pcb');print(classify_part(p.footprints['J3'],'J3'))"
  ```
- **Existing issues:** searches "right-angle header edge part_class", "horizontal pin header edge
  connector", "connector_affinity edge claim": none (#711, CLOSED, is the design-intent channel the
  workaround uses).

## 6. A 0.6 mm dangling +3.3V tail that KiCad flags (track_dangling) passes check_weird, check_orphan_stubs and check_complete

- **Tool / command:** `py_router/check_weird.py`, `py_tools/check_orphan_stubs.py`, `check_complete.py` on the
  routed board of the seed-10 chain (before the scoped +3.3V lap).
- **What it claimed:** "NO WEIRD THINGS FOUND!", "NO ORPHAN STUBS FOUND!", check_complete DONE.
- **What was true:** `kicad-cli pcb drc --refill-zones`: `track_dangling` "Track has unconnected end" on a +3.3V
  B.Cu segment (126.3,117.4)-(126.9,117.4), 0.7 mm wide, whose only contact is overlapping the copper of a +3.3V via
  at (126.4,117.9) 0.5 mm away; the (126.9,117.4) end touches nothing. `check_cycles` also counted 1 loop on +3.3V.
  KiCad shows the user a warning the repo's DONE never saw. Cleared by `route.py --nets '+3.3V' GND --force-reroute`
  (22 vias kept, 421.07 -> 411.74 mm, loop gone).
- **Cost:** one scoped lap and its checks (~5 min).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_weird.py wk/gpm/11_daplink/repro/dangling_kicad.kicad_pcb            # NO WEIRD THINGS FOUND
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc wk/gpm/11_daplink/repro/dangling_kicad.kicad_pcb --refill-zones --severity-all --format json -o wk/gpm/11_daplink/repro/dangling_kicad_drc.json
  # -> one track_dangling, Track [+3.3V] on B.Cu, length 0.6000 mm, at (126.9, 117.4)
  ```
- **Existing issues:** search "track_dangling check_weird": #1217 (CLOSED, fa10 papercuts incl. a KiCad
  track_dangling); search "dangling": #1234 (OPEN, micro-segment chains). Neither covers a full-width tail held
  only by overlap with a via.

## 7. route_diff discloses narrowed sizes and 20 advanced-tier escalations for copper it threw away

- **Tool / command:** `py_router/route_diff.py --nets '/D+' '/D-'` (default `--escalation fab`).
- **What it claimed:** `JSON_SUMMARY.design_rules`: count 28, `fab_tier_escalations` 20 (contexts
  "layer-switch pad via", "plane tap P1.A6" ...), `min_delivered` via 0.25 mm / track 0.127 mm.
- **What was true:** the pair was deferred ("electrically short (< 4.0mm coupled)"), the
  single-ended fallback failed, and the board was written through with **0 segments, 0 vias** from
  this step. The disclosure describes attempts, not shipped copper, on a step whose summary is read as
  "what was delivered below the request".
- **Cost:** a few minutes to confirm no sub-floor copper came from it.
- **Repro:** `python3 -X utf8 py_router/route_diff.py wk/gpm/11_daplink/repro/hole_in.kicad_pcb wk/gpm/11_daplink/repro/hole_diff_out.kicad_pcb --nets '/D+' '/D-' --track-width 0.2 --diff-pair-gap 0.2 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3`
  then read the `JSON_SUMMARY` line's `design_rules` and `grep -c '(segment' .../hole_diff_out.kicad_pcb` (0).
- **Existing issues:** search "route_diff design_rules no copper escalation": none; #1362 (CLOSED) is
  about the deferred pair's single-ended fallback, not its disclosure.

## 8. beautify_labels shrinks references below the board's own minimum text height, and §3.9's silk count cannot see it

- **Tool / command:** `py_placer/beautify_labels.py routed.kicad_pcb labelled.kicad_pcb` (SKILL §3.9 step 1), graded
  with the skill's own one-liner that counts only `silk*` violation types.
- **What it claimed:** "Modified 35 reference label(s)", `shrunk` 1 + `shrunk_rotated` 3; the §3.9 comparison read
  83 -> 34 silk violations.
- **What was true:** KiCad adds 2 `text_height` warnings the input did not have: R13's reference 0.70 mm and R1's
  0.75 mm against the board's `min_text_height` 0.8 mm (`.kicad_pro` line 154). The skill's counter filters on
  `type.startswith('silk')`, so the regression is invisible to the comparison that decides which board is kept.
  (Kept anyway: 34 silk + 2 text_height warnings against 83.)
- **Cost:** a few minutes (found only by reading the full KiCad report).
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/beautify_labels.py wk/gpm/11_daplink/repro/labels_in.kicad_pcb wk/gpm/11_daplink/repro/labels_out.kicad_pcb
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc wk/gpm/11_daplink/repro/labels_out.kicad_pcb --severity-all --format json -o wk/gpm/11_daplink/repro/labels_out_drc.json
  # labels_in: 0 text_height; labels_out: 2 text_height
  ```
- **Existing issues:** search "beautify_labels text height": none.

## 9. Skill: route_plan_check R12 demands the BGA cap pass after a QFP perimeter fanout

- **Tool / command:** `.claude/skills/plan-pcb-routing/scripts/route_plan_check.py` on a plan with
  `qfn_fanout.py --component U2` (LQFP-48) and no BGA.
- **What it claimed:** `FAIL R12 one cap pass, after the last fanout -- the plan fans out but never
  runs place_fanout_clearance.py`.
- **What was true:** SKILL.md Step 1c and the Step 3 text describe the cap pass as the BGA/PGA
  decoupling-cap collision fix ("only touches caps near a BGA, and is a no-op when nothing collides").
  Added anyway, it moved 0 parts (`"moved": 0`). Not harmful, but the rule and the text disagree.
- **Cost:** one plan rewrite.
- **Repro:** `python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py wk/gpm/11_daplink/repro/plan_no_cap_pass.sh`
- **Existing issues:** search "R12 cap pass qfn": none found.

## 10. Skill: §3.9 and Step 4c call a bare `kicad-cli`, which is not on PATH on this macOS install

- **Tool / command:** SKILL.md §3.9 step 1 (`kicad-cli pcb drc ...`) and plan-pcb-routing 4c.
- **What was true:** `which kicad-cli` -> not found; the binary is
  `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, which the repo's own tools find on their
  own (`kicad_oracle.py` probes that path). Followed literally, the silk grade would have been
  recorded as "ungraded". I added the app directory to PATH.
- **Cost:** one failed command.
- **Repro:** `which kicad-cli; ls /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`
- **Existing issues:** not searched as a defect of the tools (environment), noted for the skill text.
