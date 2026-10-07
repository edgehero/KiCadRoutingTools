# TOOL_GAPS -- fa10 / 01_ecc83-pp_v2

Ranked by what each cost this run. Every command runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) in Git Bash after
`export MSYS2_ARG_CONV_EXCL='*'`. Repro inputs are in `wk/fa10/01_ecc83-pp_v2/repro/`.
Issue searches were read-only (`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`).

---

## 1. route.py's end-of-run strict collapse creates the narrow-pad-joint that check_weird flags, so the first DONE needed a second route pass

**Cost: highest.** About 10 min of diagnosis, plus a second `route.py` pass on every
candidate for the rest of the run (helper `helpers/route2pass.sh`).

- **Tool and command:** `python3 -X utf8 py_router/route.py <placed> <out> --nets '*'`.
  It is placement-specific but independent of the arguments. All 8 first-pass routes
  of the first legal placement (`rot_90_seed_1`, U1 at 90) carry it, across via
  costs 75/300/1000, grid 0.1/0.05 and layer costs 1:3 and 1:1. 0 of 14 first passes
  on the 7 other placements I routed carry it (`check_weird` on every `*.p1.kicad_pcb`
  in `rv2/` and `rv3/`).
- **What it claimed:** `JSON_SUMMARY_MIN` failed 0, `board_score` blocking 0. The
  `StrictRemovalModel` docstring says a removal is accepted only when it leaves
  "no NEW narrow pad joint (#416 ...)".
- **What was true:** `check_weird` reports `narrow-pad-joint: 1`, net
  `Net-(P1-PM)` (F.Cu) at (130.300, 105.900): the track's end cap meets pad
  P1.2 (oval, 1.7 x 1.7, centre 129.722, 105.581) through a web below the
  0.864 mm floor. `check_complete` gives `INCOMPLETE -- weird_copper: not clean`.
  With `KICAD_COLLAPSE_DEBUG='Net-(P1-PM)'`, the end-of-run collapse is the pass
  that creates it:
  ```
  [COLLAPSE_DEBUG] net Net-(P1-PM): ACCEPT seg (130.3,105.9)->(130.2,106.0) F.Cu
  [COLLAPSE_DEBUG] net Net-(P1-PM): ACCEPT seg (130.2,106.0)->(130.1,106.0) F.Cu
  [COLLAPSE_DEBUG] net Net-(P1-PM): ACCEPT seg (130.1,106.0)->(129.7,105.6) F.Cu
    Strict collapse (#1063, end of run): removed 13 redundant segment(s) on 5 net(s)
  ```
  It removes the in-pad tail into P1.2's centre and leaves the end at
  (130.3, 105.9). On that geometry both `pcb_modification.circular_pad_web_shortfall`
  and `terminal_web_neck_exact` return True (a neck), and `close_soft_joints`
  adds the `terminal_web_connector` when called again (`added 1`). A second
  `route.py --nets '*'` over the routed board prints `Bridged 1 same-net soft
  joint(s)` and the board then reaches `check_complete` DONE. So the joint
  repair runs BEFORE the collapse that breaks the joint, and the collapse's
  #416 guard misses this round pad.
- **Repro:**
  ```bash
  KICAD_COLLAPSE_DEBUG='Net-(P1-PM)' python3 -X utf8 py_router/route.py \
      wk/fa10/01_ecc83-pp_v2/repro/gap2_placed.kicad_pcb wk/fa10/01_ecc83-pp_v2/repro/gap2_out.kicad_pcb --nets '*'
  python3 -X utf8 py_router/check_weird.py wk/fa10/01_ecc83-pp_v2/repro/gap2_out.kicad_pcb   # narrow-pad-joint: 1
  python3 -X utf8 check_complete.py wk/fa10/01_ecc83-pp_v2/repro/gap2_out.kicad_pcb          # INCOMPLETE
  ```
- **Existing issues:** related, both closed: #416 (terminal corner-graze web, which
  added the connector) and #1063 (check_weird vs route.py cleanup). Neither covers
  the collapse removing a tail and recreating the #416 joint. Searched
  "narrow-pad-joint", "strict collapse narrow pad joint", "terminal web connector
  close_soft_joints": no open issue.

---

## 2. Placing the mechanical parts first, as the skill says, makes place_seed and rank_rotations refuse the board as "already placed"

**Cost:** about 3 min (one refused rank_rotations run, then diagnosis), and every
later seed had to carry `--force`.

- **Tool and command:** `place_pose.py ... set P5..P8 <mechanical.json poses> lock P5 P6 P7 P8`
  (the skill: "Place and lock the connectors and mechanically fixed parts first
  ... Then zone the rest and seed"), then
  `rank_rotations.py <board> --intent intent.json --ref U1 --probe ...`.
- **What it claimed:** rank_rotations: `place_seed will not seed this board (exit 3:
  it looks placed)`, `"refused": "board_placed"`. place_seed: `this board already
  looks PLACED. Seeding would discard that placement`. board_brief on the same
  board: `state: placed`, `"pile": false`.
- **What was true:** 11 of the 15 parts (C1, C2, P1-P4, R1-R4, U1) were still in
  the staging pile south of the outline. Only the four locked corner holes were on
  the board. In `placement_state.assess_placement` the four corner holes raise the
  spread ratio to the board diagonal (s2 false). `outside_fraction` is 11/15 = 73%,
  and the piled parts sit at distinct coordinates, so there are no stacked
  suspects and `partially_unplaced` is false. The refusal comment in place_seed
  names exactly this case ("a seeder that pinned only the spec-fixed parts") as a
  legitimate seeding target. Workaround: `--force` (locked parts are kept).
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_seed.py wk/fa10/01_ecc83-pp_v2/repro/gap1_fixed_holes.kicad_pcb \
      wk/fa10/01_ecc83-pp_v2/repro/gap1_out.kicad_pcb --intent wk/fa10/01_ecc83-pp_v2/repro/intent.json   # exit 3
  python3 -X utf8 py_tools/board_brief.py wk/fa10/01_ecc83-pp_v2/repro/gap1_fixed_holes.kicad_pcb       # "pile": false
  ```
- **Existing issues:** related, closed: #1109 (board_brief `unplaced: false` on a
  93% pile; it added the `pile` field). That field also reads false here. Searched
  "looks placed pile partially_unplaced", "place_seed refuses placed fixed parts
  locked pile", "staging ring pile unplaced": no open issue.

---

## 3. rank_rotations' control baseline counts a seed whose part is still in the pile

**Cost:** one wasted trial route (about 2 min), plus a misleading headline.

- **Tool and command:** `rank_rotations.py wk/.../01_fixed.kicad_pcb --intent intent.json --ref U1 --seeds 0 1 2 --probe --seed-args='--force' ...`
- **What it claimed:** the control (undeclared-rotation) arm prints
  `crossings 4  hpwl 257.035  U1 written at 270.0` for seed 2. It prints no
  unseated count on control lines, although every rotation arm prints one. The
  verdict reads `best rotation for U1: 90 -- crossings 4 -> 7 ... against the
  undeclared seed`, and `JSON_SUMMARY.control_crossings` is 4. The header also prints
  `U1 (? connected pad(s), selected by argument)`.
- **What was true:** `rotations.json` has `unseated: 1` for `control_seed_2`. C1,
  the 12.5 mm cap, is still in the pile: its courtyard is 10.17 mm off the outline
  (`render_placement checklist.a_off_outline.courtyard`). The low hpwl (257) and
  crossings (4) are those of a board missing its largest passive. I routed that
  board as a trial, and Net-(P3-P1) failed because C1.1 is in the pile. The rotation
  arms are gated on unseated; the control baseline they are compared against is not.
- **Repro:**
  ```bash
  python3 -c "import json;d=json.load(open('wk/fa10/01_ecc83-pp_v2/repro/gap3_rotations.json'));print([(r['seed'],r['crossings'],r['unseated']) for r in d['control']['rows']] if isinstance(d['control'],dict) and 'rows' in d['control'] else d['control'])"
  python3 -X utf8 py_tools/render_placement.py wk/fa10/01_ecc83-pp_v2/repro/gap3_control_seed_2.kicad_pcb --json-out wk/fa10/01_ecc83-pp_v2/repro/gap3_render.json   # C1 courtyard 10.17 mm off
  ```
- **Existing issues:** searched "rank_rotations control unseated", "rank_rotations":
  only #1121 (closed, unrelated: place_portfolio's poses strategy). None.

---

## 4. board_brief never mentions the input board's GND pour

**Cost:** about 5 min of re-verification, and a gap in what I graded. I found
the zone 30 min in, from a `poured_nets: ["GND"]` in a board_score JSON. Until then
my grades were our router's model only. KiCad's real refill (kicad_unconnected,
fill_for_delivery) was needed to confirm that GND, routed as no tracks at all, is
connected and thermal-clean.

- **Tool and command:** `python3 -X utf8 py_tools/board_brief.py ecc83-pp_v2.kicad_pcb --json brief.json`
- **What it claimed:** `state: UNPLACED; copper no (0 segs, 0 vias)`, `power: gnd [['GND', 7]], vcc []`.
  The console output and brief.json have no zone, pour or plane entry anywhere
  (grep for zone/pour/plane: nothing).
- **What was true:** the input carries `(zone (net 1) (net_name "GND") (layer "B.Cu") ...)`,
  unfilled, clearance 0.635, thermal gap 0.254. route.py's finalize treats GND as
  served by it ("Plane finalize (#562): all zone nets complete (fill-aware)") and
  routes no GND track. The brief is the skill's "read the board" tool, and it
  should say a pour exists, on which layer and for which net, because that decides
  the routing plan.
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/board_brief.py wk/fa10/01_ecc83-pp_v2/repro/gap5_input.kicad_pcb | grep -ciE 'zone|pour|plane'   # 0
  grep -c '^\s*(zone' wk/fa10/01_ecc83-pp_v2/repro/gap5_input.kicad_pcb                                                      # 1
  ```
- **Existing issues:** searched "board_brief zone", "board_brief pour": only #1001
  and #711 (closed, about design-intent channels). None.

---

## 5. beautify_labels puts a label on another footprint's silkscreen and reports it placed; it and check_floorplan print a refusal they do not act on

**Cost:** about 3 min (two extra scoped runs and KiCad DRCs).

- **Tool and command:** `python3 -X utf8 py_placer/beautify_labels.py <routed> <out> --min-size 0.8`
- **What it claimed:** `placed 15`, `unchanged 0`. Re-run with `--refs P2
  --max-distance 4`: `placed 1` but `Modified 0`, so the tool considered P2's
  label fine.
- **What was true:** `kicad-cli pcb drc` (via `py_tools/kicad_unconnected.py --json`)
  reports `silk_overlap` (error severity): P2's reference at (127.838, 111.552)
  over `Cirkel van C1 op F.Silkscreen` (C1's body circle). The tool checks label
  to label and label to pad copper, not label to other footprints' silk graphics.
  It did cut KiCad's silk violations 4 to 1, and `--orientation vertical` or
  `--anchor-gap 1.0` on P2 cleared the last one.
- **Second half, both tools:** `beautify_labels` and `check_floorplan --allow-routed`
  print `this board carries 39 segment(s) ... Placement moves FOOTPRINTS and does
  not move copper ... Override with --allow-routed`, then proceed and exit 0.
  beautify_labels moves only text (footprints and copper verified byte-equal
  after it). check_floorplan was given `--allow-routed` and moves nothing.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/beautify_labels.py wk/fa10/01_ecc83-pp_v2/repro/gap4_routed_prelabels.kicad_pcb wk/fa10/01_ecc83-pp_v2/repro/gap4_labels.kicad_pcb --min-size 0.8
  python3 -X utf8 py_tools/kicad_unconnected.py wk/fa10/01_ecc83-pp_v2/repro/gap4_labels.kicad_pcb --json wk/fa10/01_ecc83-pp_v2/repro/gap4_labels.kdrc.json
  python3 -c "import json;print([v['type'] for v in json.load(open('wk/fa10/01_ecc83-pp_v2/repro/gap4_labels.kdrc.json'))['violations'] if v['type']!='lib_footprint_issues'])"   # ['silk_overlap']
  ```
- **Existing issues:** searched "beautify_labels silk overlap", "beautify_labels",
  "silk_overlap", "allow-routed warning": #481 (closed, the tool's introduction).
  None.

---

## 6. board_score's `poured_nets` is empty on a connected board that has a zone

**Cost:** about 1 min of confusion (the same pour read `["GND"]` on the
placement board and `[]` on every routed board).

- **Tool and command:** `python3 -X utf8 py_tools/board_score.py <board> --json out.json`
- **What it claimed:** `components.broken.poured_nets: []`, next to
  `poured_nets_meaning: "nets with at least one zone on the board ..."`.
- **What was true:** the board has one GND zone. `score_connectivity` returns
  early on `ALL NETS FULLY CONNECTED`, before the zone scan, so the field is
  missing and the JSON writer defaults it to `[]`. It does not mean "no zone".
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/board_score.py wk/fa10/01_ecc83-pp_v2/repro/gap4_routed_prelabels.kicad_pcb --json wk/fa10/01_ecc83-pp_v2/repro/gap6.score.json --quiet
  python3 -c "import json;print(json.load(open('wk/fa10/01_ecc83-pp_v2/repro/gap6.score.json'))['components']['broken'].get('poured_nets'))"   # []
  grep -c '^\s*(zone' wk/fa10/01_ecc83-pp_v2/repro/gap4_routed_prelabels.kicad_pcb                                                                 # 1
  ```
- **Existing issues:** searched "poured_nets": none.

---

## 7. check_complete --authored-from calls via floors "not measured" on a board with no vias

**Cost:** negligible (report noise), recorded because it reads like an open item.

- **Tool and command:** `python3 -X utf8 check_complete.py final.kicad_pcb --intent intent.json --authored-from ecc83-pp_v2.kicad_pcb`
- **What it claimed:** `INCOMPLETE -- declared fab floor(s) NOT measured by this check,
  so unknown rather than honoured: via diameter (declared 0.4), via annular ring
  (declared 0.05), copper-to-hole clearance (declared 0.0)`.
- **What was true:** the board has 0 vias, so both via floors hold vacuously.
  The copper-to-hole floor (0.0) is graded by check_drc, which is clean.
- **Repro:** the command above on `wk/fa10/01_ecc83-pp_v2/final.kicad_pcb`.
- **Existing issues:** searched "authored-from via floor not measured": none.

---

## Helpers written (each because no single repo tool did the job)

- `helpers/route2pass.sh`: the workaround for gap 1. It runs `route.py --nets '*'`
  twice, the second time over the first's output, so `close_soft_joints` repairs
  the joint the end-of-run collapse broke.
- `helpers/route_variants.sh`: runs N `route.py` argument sets on one board in
  parallel, each to a fresh output path. route.py has no multi-arm mode, and
  `rank_rotations --probe` / `place_portfolio --route-args` route at ONE argument
  set.
- `helpers/grade_variants.sh`: one line per board from board_score + check_complete +
  check_weird. `.claude/skills/pcb-free-agent/scripts/grade.py` grades one board
  per call with a longer report, and nothing in the repo tabulates candidate boards
  by the lexicographic key (blocking, vias, copper_mm, segments).
