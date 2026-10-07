# TOOL_GAPS -- fa10 board 05 (interf_u)

Ranked by what each cost this run (most first). Every repro runs from the
worktree root with `export MSYS2_ARG_CONV_EXCL='*'` set.

## Ranking by cost to this run

| rank | gap | cost |
|---|---|---|
| 1 | G4 route.py's rip-up cascade turns a near-complete first pass into 18-34 open nets, runs 60-90+ min, and a stopped run leaves no board | ~4 h of route wall time on runs stopped without a usable board; a 2 h background cap killed one in its last phase |
| 2 | G5 no escape tool for a card-edge finger row; the router boxes later fingers in (helpers add_finger_stubs.py, trim_stub_tails.py) | decided the routing approach; without the stubs every pass left BUS1 address fingers sealed |
| 3 | G6 the rescue rewrote the Default class clearance 0.254 -> 0.127 and every grader then read the board clean (#1160) | one 81-min route unusable as authored, plus the re-run with the clearance pinned |
| 4 | G2 no capacity tool checks whether the class width threads a 2.54 mm THT pin row; check_channels says a THT PGA's inner pins "need a via" | ~1 h of routing at 0.4 mm before I found it by hand (first pass 6 vs 2 failures) |
| 5 | G7 an iteration pass with --keep-input-copper writes stacked GND copper (3 -> 15 -> 17) and leaves the previous pass's loops (helper dedupe_stacked.py) | a scoped cleanup pass + a dedupe helper; check_complete INCOMPLETE until then |
| 6 | G1 place_seed refuses a grid pile as "already PLACED" once the fixed parts are seated | one run, then --force on every seed |
| 7 | G3 qfn_fanout writes nothing for an edge-finger row and still relaxes the project's via/hole floors | 5 min on a scratch copy; would have loosened the spec in a chain |

Helpers written (all in `helpers/`): `add_finger_stubs.py`, `trim_stub_tails.py`
(both G5), `dedupe_stacked.py` (G7).

## G7. An iteration pass with --keep-input-copper writes duplicate (stacked) GND copper and leaves the previous pass's loops

- **Tool / command:** the routing skill's Step 2d iteration, `route.py <pass-1 board> <pass-2 board> --nets '*' <the pass-1 flag string, verbatim>`,
  where the flag string carries `--keep-input-copper` (required here so the
  first pass's cleanup could not sweep the locked BUS1 escape stubs, G5).
- **What it claimed:** route.py's own summary does not mention it; check_weird
  does: `stacked-copper`, `2 duplicate segments stacked on (143.500,
  83.500)-(143.900, 83.100)` (net GND, F.Cu), plus `redundant-cycle` and
  `removable-segment` findings on /PC-A10 and /REF5.
- **What was true (check_weird counts):** pass 1 (r/d4_all): stacked-copper
  3, dangling-via 1, dangling-end 2. After ONE iteration pass with the same
  flags: r/d4_i1 stacked-copper 12, redundant-cycle 1, removable-segment 3,
  dangling-via 3; r/d4_i2 stacked-copper 15, redundant-cycle 2,
  removable-segment 3, dangling-via 2. The in-run plane finalize re-lays GND
  taps the input already has, and `--keep-input-copper` stops the cleanup
  from removing either the old copy or the previous pass's loops. The flag
  protects ALL input copper, not just the copper the caller meant (the stubs).
  check_complete reports such a board INCOMPLETE (`weird_copper: not clean`).
- **Cost:** a separate scoped cleanup pass without the flag, and the risk
  that the iteration recipe ("pass the identical flag string") cannot be
  followed as written on a board that needs protected hand copper (medium).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_weird.py wk/fa10/05_interf_u/repro/gap7_pass1.kicad_pcb --max-print 0 | grep -E "^  [a-z-]+: [1-9]"
  python3 -X utf8 py_router/check_weird.py wk/fa10/05_interf_u/repro/gap7_pass2.kicad_pcb --max-print 0 | grep -E "^  [a-z-]+: [1-9]"
  ```
  (pass1 = r/d4_all, pass2 = r/d4_i2; the command that made pass 2 is the
  first line of r/d4_i2.log.)
- **Existing issues:** #162 (OPEN, "Same-net redundant copper (self-crossings
  + stacked duplicates): find the producers, remove delete-only") is the
  general class; this is one producer of it (finalize re-tap under
  `--keep-input-copper`). Searched also "keep-input-copper stacked copper",
  "keep-input-copper iteration cleanup".

## G6. The rescue rewrites the Default class clearance 0.254 -> 0.127, and every grader then reads the board clean (check_complete --authored-from lists nothing)

- **Tool / command:** `route.py ... --escalation board` (r/d3_all), then
  `py_tools/board_score.py` and `check_complete.py --authored-from wk/fa10/05_interf_u/interf_u.kicad_pcb`
  on its output.
- **What it claimed:** board_score `drc=0` (`graded_at: 0.127`);
  check_complete `fab_floors.relaxed: []` (no relaxed floor). The route's own
  line was honest: `min_clearance_used: 0.127`, `54 feature(s) on 45 net(s)
  delivered below the requested size`.
- **What was true:** the output project's Default class reads
  `clearance 0.127` where the input declared `0.254`; the fine-parameter
  rescue reconnected nets at 0.127/0.159/0.19/0.222 mm. Graded at the
  authored 0.254, the intermediate board of the same run had 192 DRC findings
  (segment-segment 78, via-segment 77, pad-segment 31) such as `/ENBBUF <->
  Net-(U3-Y2) Overlap 0.101mm`. This board's Board Setup leaves
  `min_clearance` unset (0.0), so `--escalation board` descends to the FAB
  clearance floor, and the floor comparison sees no rule change because it
  compares `rules.*` only.
- **Cost:** one 81-min route whose result cannot be DONE as authored, and a
  second route to repeat it with the clearance pinned (`--fab-overrides` with
  `clearance = 0.254`, file `fab_floor_board.txt`) (high).
- **Repro:**
  ```bash
  python3 -c "import json;p=json.load(open('wk/fa10/05_interf_u/repro/gap6_d3_all.kicad_pro'));print([(c['name'],c['clearance']) for c in p['net_settings']['classes']])"   # Default 0.127
  python3 -X utf8 check_complete.py wk/fa10/05_interf_u/repro/gap6_d3_all.kicad_pcb --intent wk/fa10/05_interf_u/intent.json --authored-from wk/fa10/05_interf_u/interf_u.kicad_pcb --json /dev/stdout | grep -o '"relaxed": \[\]'
  ```
- **Existing issues:** #1160 (OPEN, "One net's rescue lowers the Default
  class clearance in the project, and the next step routes every net there
  even under --escalation off") covers it, including "check_complete
  --authored-from compare rules only". This run adds a second board where
  the rewrite comes from `--escalation board` on a board with no declared
  `min_clearance`.

## G4. route.py's rip-up turns a near-complete first pass into dozens of open nets, runs 90+ min, and a stopped run leaves no board

- **Tool / command:** `py_router/route.py wk/fa10/05_interf_u/repro/gap4_seed0_u9at180.kicad_pcb out.kicad_pcb --nets '*' --no-bga-zone --max-ripup 5 --power-nets GND VCC --power-nets-widths 0.5 0.5 --escalation board`
  (the routing skill's own recipe for a hard 2-layer PGA board: `--no-bga-zone
  --max-ripup 5`).
- **What it claimed:** nothing false while running, but the progress line
  reads as if the run were converging, and there is no bound and no
  intermediate output.
- **What was true (measured, logs kept in r/):**

  | run | first pass ended | reroutes | casualties left for final reconciliation | wall when stopped |
  |---|---|---|---|---|
  | a0_r1 (seed 0, U9 at 180) | `[110/110]`, 0 failed | 347 (queue reached 457) | 31 nets | 90 min, still in reconciliation |
  | a1_r1 (seed 1) | 1 failed | 479 (queue 589) | 34 nets | 90 min, still in reconciliation |
  | b0_t3 (U9 pinned, 0.3 mm) | 2 failed | 59 (queue 169) | 18 nets | ~60 min, still in reconciliation |

  So the in-pass rip-up cascade, not the first pass, created most of the open
  nets: each ripped net failed to re-route and ripped up to 5 more. The final
  reconciliation then rescued casualties one at a time, at ~1 min per net.
  Stopping the process leaves nothing (no checkpoint of the best state), so
  each experiment had to run to the end or be lost. `--max-ripup 0` is no
  escape: on the same placement it left 16 first-pass failures and 17+
  failed Phase 3 taps (r/b0_t3m0.log).
- **Cost:** the largest of the run. ~4 h of route wall time went into runs I
  stopped without a board (a0, a1, b0_r1, b0_t3, b0_t3m0, c0_r1, c0_env, d0_a,
  d0_b). What fixed it was placement plus staging (G5), not a router flag.
- **Repro:** the command above on `repro/gap4_seed0_u9at180.kicad_pcb`; watch
  `grep -c '^\[REROUTE'` grow and `Final reconciliation ... N net(s)` appear.
- **Existing issues:** #651 (CLOSED, "Rip/reroute passes need casualty
  accounting: roll back when a pass creates more zero-copper/open nets than it
  fixes") is this problem and is marked done; the cascade above happens inside
  one pass. #358 (OPEN, "Understand and optimize the largest (monster) stress
  boards") is about runtime, but this is a 25-part board. Searched "rip-up
  cascade", "reroute queue", "casualties never re-routed", "route.py wall
  time checkpoint".

## G5. No escape tool for a card-edge finger row, and route.py boxes the fingers in (helper: helpers/add_finger_stubs.py)

- **Tool / command:** `py_router/route.py <placed board> --nets '*' --no-bga-zone --max-ripup 5 --power-nets GND VCC --power-nets-widths 0.5 0.5 --escalation board --track-width 0.3`
  on a board whose BUS1 is an ISA edge-finger row (62 SMD fingers at 2.54 mm,
  1.778 x 7.62 mm, 0.762 mm gaps, on a tab below the main outline).
- **What it claimed:** nothing false; the failure shows only in the log. In
  Phase 3 the address-finger edges fail with the search from the FINGER side
  boxed in: `/PC-A9 ... target=(116.20, 138.43) backward stuck (2958 < 5000)
  ... Failed to route MST edge`, `/PC-RST ... target=(167.00, 138.43)
  backward stuck (3170 < 5000)`. Tracks from neighbouring fingers turn
  sideways right above the finger tops and seal a later finger's only exit;
  a finger on the tab has no legal via site (0.762 mm gaps), so once sealed
  it cannot escape on either layer. The rip-up then thrashes (one tap in r/d0_a
  ripped /PC-A8, /PC-A1, /PC-A0 in turn).
- **Why the repo tools were not enough:** `qfn_fanout.py` misreads the row
  (0.50 mm pitch, 0 pads, see G3); `bga_fanout.py` is for grids; there is no
  `--keepout`-style "reserve the exit" option for a connector in route.py.
- **What the helper does:** one straight locked stub per used finger from the
  pad centre to y=131 (into a reserved band), 0.3 mm (0.5 mm for GND/VCC), on
  the finger's own layer; each stub is then verified with
  `py_tools/check_join.py` (28 of 28 CLEAN) and the board with `check_drc`
  (clean). With stubs, a boxed finger can still drop a via at its tip, since a
  1.4 mm via plus clearances (1.908 mm) fits the 2.24 mm gap between stubs.
- **Second helper, `helpers/trim_stub_tails.py`:** `--keep-input-copper`
  (needed so the cleanup cannot sweep the stubs) also stops the cleanup from
  trimming the part of a stub BEYOND where the router attached, so
  check_weird reports a `dangling-end` per such stub (r/d3_all: /PC-A9 tail
  1.5 mm, VCC tail 2.4 mm). No repo tool shortens input copper to its last
  attachment. The helper moves each stub's tip to its farthest same-net
  attachment (copper overlap, not only centreline contact; a first version
  missed a via 0.3 mm off-axis and removed a needed stub, caught by
  check_weird's `dangling-via`) and removes a stub with nothing attached past
  its pad. Verified on r/d3_all: check_weird 3 -> 1 finding, check_connected
  unchanged.
- **Cost:** see the result in REPORT.md (high; it decided the routing approach).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route.py wk/fa10/05_interf_u/repro/placed_z_s3c.kicad_pcb wk/fa10/05_interf_u/repro/gap5_routed.kicad_pcb --nets '*' --no-bga-zone --max-ripup 5 --power-nets GND VCC --power-nets-widths 0.5 0.5 --escalation board --track-width 0.3 2>&1 | grep -E "backward stuck|NOT CONNECTED \(so far\).*BUS1"
  ```
- **Existing issues:** #592 (OPEN, "Connector-row escape combing:
  direction-aware field that prices parallel travel through a pin row's
  escape band") is this problem, unimplemented. Searched also "edge connector
  fingers fanout", "card edge fingers escape", "ISA edge connector": only
  roll-ups (#513).

## G3. qfn_fanout writes nothing for an edge-finger row, then relaxes the project's via/hole floors anyway

- **Tool / command:** `py_router/qfn_fanout.py <placed board> --output f1.kicad_pcb --component BUS1 --layer F.Cu --width 0.3 --clearance 0.254 --nets '*' '!GND' '!VCC'`
  -- looking for an escape-stub tool for the ISA edge fingers (62 SMD pads,
  2.54 mm pitch, one row), because no repo tool covers a card-edge row.
- **What it claimed:** `Detected pad pitch: 0.50 mm`, `Found 0 pads to
  fanout`, `No fanout tracks generated`, `Wrote board through ... (unchanged)`
  -- and then `FAB FLOOR RELAXED -- the output project declares a smaller
  minimum than the board originally did: via diameter 0.9 -> 0.45 mm, hole
  diameter 0.5 -> 0.25 mm`, exit 0.
- **What was true:** the pitch is 2.54 mm (pads at x 93.34, 95.89, 98.42 ...).
  The output board has 0 segments and 0 vias, the same as the input, but its
  `.kicad_pro` differs in four rules: `min_via_diameter 0.9 -> 0.45`,
  `min_through_hole_diameter 0.5 -> 0.25`, `min_via_drill None -> 0.25`,
  `min_copper_edge_clearance 0.0 -> 0.2`. A run that produced no copper
  lowered the board's authored floors, and every later step and checker reads
  the new ones. In a chain this would silently loosen DONE's spec grade. (I
  ran it on a scratch copy, so the run board was not affected.)
- **Cost:** 5 min, no damage because it was a scratch copy (low). The missing
  edge-connector escape tool itself is G5.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/qfn_fanout.py wk/fa10/05_interf_u/repro/placed_z_s3c.kicad_pcb --output wk/fa10/05_interf_u/repro/gap3_out.kicad_pcb --component BUS1 --layer F.Cu --width 0.3 --clearance 0.254 --nets '*' '!GND' '!VCC'
  # then diff the rules blocks of repro/placed_z_s3c.kicad_pro and repro/gap3_out.kicad_pro
  ```
- **Existing issues:** "qfn_fanout floor relaxed no copper", "FAB FLOOR
  RELAXED", "qfn_fanout edge connector pitch": none covers a no-op write.
  Same family, other tools: #1160 (OPEN, a rescue lowers the Default class
  clearance in the project), #1170 (OPEN, oracle reconnect drops to hardcoded
  0.45/0.2 vias under `--escalation off`).

## G2. No capacity tool measures whether the class width threads a 2.54 mm THT pin row; check_channels says a THT PGA's inner pins "need a via"

- **Tool / command:** `py_tools/check_channels.py wk/fa10/05_interf_u/repro/placed_z_s3c.kicad_pcb`
  and `py_tools/check_capacity.py <same> --intent wk/fa10/05_interf_u/repro/intent_band2.json`
  -- the skill's "will it fit, can it escape" row.
- **What it claimed:** check_channels models only U9 (the PGA120) and prints
  `U9 interior: 70 pad(s) on no face -- they need a via, not a lane; 40 net(s)
  left the faces because of it`, `Faces in DEFICIT at the finest legal grid: 0`.
  check_capacity: `relax_clearance: not measured -- no face is short of lanes`,
  `add_layers: not measured -- this board has no fine-pitch part`.
- **What was true:** (a) U9 is THROUGH-HOLE (0.8 mm drills, 1.4 mm pads, 2.54
  mm pitch): every inner pin is on both layers and a 0.3 mm track at 0.254 mm
  clearance passes between two outer pins (needs 0.808 of 1.14 mm), so no via
  is needed. (b) The binding limit on this board is the DIP rows (U1-U3, U5,
  U8, RR1: 1.6 mm pads at 2.54 mm, a 0.94 mm gap). The Default class (0.4 mm
  track, 0.254 mm clearance) needs 0.908 mm there, i.e. a centreline within
  +-0.016 mm of the midpoint, which the 0.1 mm routing grid hits only at some
  pin pairs. No tool reports this. Measured on the same placement (r/b0):
  first-pass failures 6/110 at the class 0.4 mm vs 2/110 at `--track-width
  0.3`; every 0.4 mm run then fell into a 400+-reroute cascade.
- **Cost:** about 1 h of routing at the class width before I worked it out by
  hand (medium).
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/check_channels.py wk/fa10/05_interf_u/repro/placed_z_s3c.kicad_pcb   # "70 pad(s) on no face -- they need a via"
  ```
- **Existing issues:** searched "check_channels", "lane ledger",
  "check_channels interior via through-hole", "track between pins netclass
  width": nothing on THT. Nearest: #700 (CLOSED, "nothing in py_placer behaves
  differently on a 2-layer board than on a 6-layer one").

## G1. place_seed refuses a grid pile as "already PLACED" once the fixed parts are seated

- **Tool / command:** `py_placer/place_seed.py wk/fa10/05_interf_u/b/p01_fixed.kicad_pcb out.kicad_pcb --intent wk/fa10/05_interf_u/intent.json`
  -- run on the board the skill's own recipe produces (§4: "place and lock the
  connectors and mechanically fixed parts first ... then seed").
- **What it claimed:** `place_seed: this board already looks PLACED. Seeding would discard that placement; use place_portfolio.py ... or --force`, exit 3.
- **What was true:** 22 of 24 pad-bearing parts were still in the staging pile
  south of the outline. `placement_state.assess_placement` on that board:
  `unplaced False, partially_unplaced False`, signals
  `outside_fraction 0.958, spread_ratio 0.7037, distinct_positions 24,
  duplicate_fraction 0.0`. On the pile before the two moves it read
  `unplaced True` (`spread_ratio 0.1`). Seating two locked parts (BUS1 at the
  south tab, P1 at the east edge) widened the spread, and `partially_unplaced`
  only fires on parts STACKED at one coordinate (`_suspect_in`); a 2.8 mm grid
  pile has no stacks. The code's own comment says "a seeder that pinned only
  the spec-fixed parts" is "a legitimate seeding target, not a refusal".
- **Cost:** one wasted run and a `--force` on every seed after it (low).
  `--force` widens the scope to every unlocked part, which is what a pile
  needs here, so no harm beyond the refusal -- but a caller who reads exit 3
  as "the board is placed" would route a pile.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_seed.py wk/fa10/05_interf_u/repro/gap1_fixed_pile.kicad_pcb wk/fa10/05_interf_u/repro/gap1_out.kicad_pcb --intent wk/fa10/05_interf_u/intent.json   # exit 3, "already looks PLACED"
  ```
- **Existing issues:** `gh issue list --search "already PLACED --force"`,
  `"partially unplaced"`, `"assess_placement"`: none covers it. Nearest is
  #1109 (CLOSED: "board_brief reports unplaced: false on a 93% pile"), which
  fixed `board_brief` by adding a `pile` reading; `place_seed`'s gate still
  reads `unplaced` / `partially_unplaced`, not `pile`.
