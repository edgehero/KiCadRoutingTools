# TOOL_GAPS -- fa10 board 10 (glasgow_revC)

Tools at upstream main 04a2c68d, worktree `krt-fa10`. All commands run from WT
with `export MSYS2_ARG_CONV_EXCL='*'`; `R=wk/fa10/10_glasgow_revC/repro`.
Ranked by what each cost this run. Issue searches were read-only
`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`.

---

## 1. The floorplan overlap budget grades a circular courtyard as its bounding square; the exact-shape tools disagree with it

- **Tool / command:** `py_tools/check_floorplan.py <board> --intent intent.json`
  (and `board_score`, whose `floorplan` term is blocking).
- **What it claimed:** `[ERROR] legality: courtyard overlap area (mm2): 4.909
  exceeds the declared budget 0.000`, naming no pair. On the same board
  `render_placement` lists `b_courtyard_blocking_pairs: []` (exact shapes) and
  `check_assembly` says `buildable (blocking 0)`.
- **What was true:** the budget sums rectangle overlaps
  (`legality.placement_overlap_area` over `GradedPart.rect`). MK1-4 use
  `MountingHole_3.5mm_Pad_Via_CrtYd`, whose F.CrtYd is a 129-point circle,
  r = 5 mm. Each is graded as its 10 x 10 mm square. J2 was seated against the
  circle (corner at 5.16 mm from MK3's centre), which is legal by shape, but
  its rectangle clips MK3's square by 1.21 x 1.5 mm = **1.815 mm²** (pair
  breakdown from `helpers/overlap_pairs.py`: `1.815 J2/MK3`, `2.1164 C92/MK2`,
  `0.978 C87/TP3`, `0.0358 SW1/TP2`). With the corner squares, the north edge has
  62 mm between MK2 and MK3 for J2 (34.06 mm) plus J5 (29 mm), so both
  north-declared headers cannot be flush on that edge at all. Nothing in the
  plan check (`--plan-only`: 0 errors) warns of it.
- **Cost:** ~1.5 h. Seeds, the decap repair and 9 hand moves were built on a
  connector layout that could never grade 0, then two re-layouts and re-seeds
  (layout v1 -> v3).
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/check_floorplan.py $R/g4_overlap_bbox.kicad_pcb --intent $R/intent.json   # 4.909, no pair named
  python3 -X utf8 py_tools/render_placement.py $R/g4_overlap_bbox.kicad_pcb --json-out $R/g4.json -o $R/g4.png   # checklist.b_courtyard_blocking_pairs == []
  python3 -X utf8 py_tools/check_assembly.py $R/g4_overlap_bbox.kicad_pcb --intent $R/intent.json   # buildable
  python3 -X utf8 wk/fa10/10_glasgow_revC/helpers/overlap_pairs.py $R/g4_overlap_bbox.kicad_pcb | grep -v " none"   # the pairs
  ```
- **Existing issues:** none for this. Nearest is #761 (CLOSED, the NPTH
  keep-out circle tested against an uninflated rect), the same circle-vs-rect
  family.

## 2. route.py rips out-of-scope routed nets without `--rip-existing-nets`, and a ripped BGA net loses its escape stub for good

- **Tool / command:** `py_router/route.py r1/route.kicad_pcb r2/a.kicad_pcb --nets
  +3V3 /D3 /FPGA_DONE /GNDPLL1 /IO_Banks/DB7 /IO_Banks/QB4 /IO_Banks/QB5
  /IO_Banks/Z10_N '/~{FPGA_RESET}' GND <flags>`: no `--rip-existing-nets` on the
  command line.
- **What it claimed:** `--help`: *"Without this flag, committed tracks are never
  ripped."* The log: `PRE-EXISTING rip: '/IO_Banks/U5' (earlier-step copper)
  removed -- queued for reroute this run; original restored if the reroute
  fails`.
- **What was true:** the tap-retry cascade ripped /D5, then /IO_Banks/U5 (both
  outside `--nets`, both fully routed in r1). U5 ended `NOT RECOVERED (still
  open)` and was not restored. Its U30.E8 fanout stub went with it, so every
  later lap printed `Hint: pad U30.E8 is a fanout-dropped ball (no escape stub)`.
  `check_reachability --pad U30.E8` on the final board: **CAGED (margin
  -38 um)**. The improvement gate accepted the lap overall (11 -> 8), so a net
  that was routed became unrouted. It is one of the six blockers on the shipped
  board. Lap d (from r1, `--rip-existing-nets '+1V2'`) did the same to U5.
  Re-fanning it afterwards (`bga_fanout --nets /IO_Banks/U5 --check-for-previous`)
  escaped the ball, but see gap 7.
- **Cost:** 1 of the 6 final blockers, plus ~25 min of laps (e1, e2, f1, f2) that
  started from the re-fanned board.
- **Reproduce:**
  ```
  bash $R/lap.sh $R/g13_rip_strips_stub.kicad_pcb $R/g13_out.kicad_pcb $R/g13.nets
  grep -nE "PRE-EXISTING rip: '/IO_Banks/U5'|'/IO_Banks/U5'.*NOT RECOVERED" $R/g13_out.log
  head -1 $R/g13_out.log | grep -c rip-existing     # 0: the flag was never given
  ```
- **Existing issues:** #734 (CLOSED: pre-existing rip candidacy at
  registration), #651 (CLOSED: casualty accounting / roll back a pass that
  creates opens), #655 (CLOSED: tap rip victim ships at zero copper), #652
  (CLOSED: fanout-dropped balls diagnosed downstream). None covers "help says
  never, log says ripped".

## 3. check_floorplan's overlap error names no pair, and the obvious public API over-counts pad-less logos (my wrong turn)

- **Tool / command:** `check_floorplan` (error text above), then
  `placement.legality.graded_parts_from_file` + `pair_overlap_area` to list pairs
  (`helpers/overlap_pairs.py`).
- **What it claimed:** the grade prints only a total. The public API includes
  KiCad-locked, pad-less, courtyard-less logos (REF** at 86.9,85.3; REF**~2 at
  65.7,87.65) as synthetic 1 x 1 mm bodies (`source 'none'`).
- **What was true:** the grade's own part list (seeder state) leaves the logos
  out. On layout v2's seed b0 my helper reported `1.0 J5/REF**~2`,
  `1.0 J5/REF**` (2.0 mm²), while check_floorplan's JSON says
  **`"overlap_area": 0.0`**. I read the helper, abandoned a legal layout and
  re-laid out a second time. The tool gap is the unattributed error. The wrong
  conclusion was mine: I did not check the grader's own JSON before acting
  (the "call the grader, do not mirror it" lesson, again).
- **Cost:** ~45 min (layout v2 seeds discarded, v3 seeded).
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/check_floorplan.py $R/g8_logo_phantom.kicad_pcb --intent $R/intent.json | grep -o '"overlap_area": [0-9.]*'   # 0.0
  python3 -X utf8 wk/fa10/10_glasgow_revC/helpers/overlap_pairs.py $R/g8_logo_phantom.kicad_pcb   # TOTAL 2.0 (J5 vs two logos)
  ```
- **Existing issues:** none found ("floorplan overlap error names no pair").

## 4. `decap_pin_distance` errors are charged to the IC, so `--repair --repair-decaps` cannot fix them and nothing names a spare cap

- **Tool / command:** `py_placer/place_seed.py seeds/s0.kicad_pcb out --intent
  intent.json --repair --repair-decaps`
- **What it claimed:** `repaired 12`, with `unresolved_by_rule
  {"decap_distance": 3, "decap_pin_distance": 16}` and unresolved refs that are
  ICs (U10, U11, U16, U19, U32, U4, U6, U9, ...). `--reseat C82 C16 C54 C87 U2`
  on another seed: `0 re-seated ... [GATE REFUSED]`.
- **What was true:** each error is "IC pin X has no cap on its rail within
  2.5 mm". The cap to move is not named, and the repair only moves caps a
  finding charges. Whether a cap on the rail is spare (it alone serves no other
  pin) is computed nowhere. I wrote `helpers/decap_audit.py`, which calls the
  grader's own `supply_pins` / `decap_pin_caps` / `_pin_gap` /
  `decap_populations`, then made 9 hand moves on layout v1 (19 -> 0) and 5 on v3
  (5 -> 0, after `--decap-claim-after-ics` + repair had taken 7 -> 5).
- **Cost:** ~40 min of hand work, plus the helper.
- **Reproduce:**
  ```
  python3 -X utf8 py_placer/place_seed.py $R/g5_decap_pin_seed.kicad_pcb $R/g5_out.kicad_pcb --intent $R/intent.json --repair --repair-decaps
  #   JSON_SUMMARY unresolved_by_rule.decap_pin_distance = 16, unresolved_refs are ICs
  python3 -X utf8 wk/fa10/10_glasgow_revC/helpers/decap_audit.py $R/g5_decap_pin_seed.kicad_pcb $R/intent.json
  ```
- **Existing issues:** #1150 (OPEN) "Stranded decouplers are never pulled back
  ... --repair nudges decap_distance caps" covers part of it. #1066 (CLOSED) is
  the earlier "no post-seed actor seats caps".

## 5. rank_rotations runs its arms one after another

- **Tool / command:** `py_placer/rank_rotations.py p02_conn.kicad_pcb --intent
  intent.json --ref U30 --seeds 0 --out-dir rot_u30 --seed-args='--force'`
- **What it claimed:** nothing false; it ranks correctly. But the control arm
  alone took **21 min** (place_seed on this 264-part board, shared machine), and
  it runs control + 4 angles in series, so about **105 min for one part**. There
  is no `--jobs`.
- **What I did:** stopped it and ran the arms' own `rot_*.intent.json` as 6
  parallel `place_seed` processes (U30 and U1 at once, ~30 min wall).
- **Cost:** ~20 min before I noticed.
- **Reproduce:** `python3 -X utf8 py_placer/rank_rotations.py $R/g2_conn_locked.kicad_pcb --intent $R/intent.json --ref U30 --seeds 0 --out-dir $R/rot --seed-args='--force'`
  (read the arm timestamps in the log).
- **Existing issues:** none ("rank_rotations parallel", "rank_rotations
  sequential slow").

## 6. place_seed seats declared header connectors perpendicular to their edge, overlapping

- **Tool / command:** `place_seed p01_mk.kicad_pcb out --intent intent.json --force`
  (only MK1-4 placed and locked).
- **What it claimed:** a seed (exit 4, 48 grade errors).
- **What was true:** J2 and J3 (IDC 2x10, declared north and south) were
  vertical in mid-board, overlapping each other (**88.7 mm²** courtyard
  overlap). J5 (declared north) ran down the west side, and J1 sat 7.31 mm off
  its declared west edge. J2 and J5 pass the edge rule because a short end
  touches the north edge, so the rule cannot tell this from a correct seat.
- **Cost:** ~15 min, then every connector was placed by hand with `place_pose`.
- **Reproduce:** `python3 -X utf8 py_placer/place_seed.py $R/g1_mk_locked_pile.kicad_pcb $R/g6_out.kicad_pcb --intent $R/intent.json --force`, then
  `python3 -X utf8 py_tools/check_floorplan.py $R/g6_out.kicad_pcb --intent $R/intent.json`.
- **Existing issues:** none matching. #988 and #1000 (both CLOSED) touch
  stage 1 and connector clauses.

## 7. bga_fanout `--check-for-previous` on a routed board adds a via that fails DRC

- **Tool / command:** `py_router/bga_fanout.py r3/d.kicad_pcb -o r3/df.kicad_pcb
  --component U30 ... --nets /IO_Banks/U5 --check-for-previous`
- **What it claimed:** `"escaped": 1, "failed": 0`, `drc_grazes` pad_via 0.
- **What was true:** `board_score` on the output: **drc 1 (`via-segment`)** plus 1
  via-in-paste, against 0 on its input. Blocking went 6 -> 7, and every later lap
  started from that worse board.
- **Cost:** ~10 min, and one more blocker on the board the last four laps used.
- **Reproduce:**
  ```
  python3 -X utf8 py_router/bga_fanout.py $R/g12_refanout_drc.kicad_pcb -o $R/g12_out.kicad_pcb --component U30 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 4.0 2.5 1.0 --track-width 0.0762 --clearance-ceiling 0.0889 --clearance 0.0889 --via-size 0.25 --via-drill 0.15 --nets /IO_Banks/U5 --check-for-previous --plane-net-layers GND:In1.Cu +3V3:In2.Cu
  python3 -X utf8 py_tools/board_score.py $R/g12_out.kicad_pcb --intent $R/intent.json --quiet | tail -3   # drc=1
  ```
- **Existing issues:** none found ("check-for-previous via segment DRC").
  #805 (CLOSED) is about obstacle bookkeeping in general.

## 8. `decap_distance` elects a cap's IC as the nearest part sharing ANY net, GND included

- **Tool / command:** `check_floorplan <board> --intent intent.json`
- **What it claimed:** `decap_distance: C92 is 2.88mm from J5, the IC it
  decouples`.
- **What was true:** C92 is a /IO_Banks/VIO_AUX cap, and the only IC on that rail
  is U30. J5 (a pin header) shares only GND with it. Below J5 the 2.5 mm limit
  needs the cap inside J5's courtyard. The way out was to put C92 at J5's west
  end, diagonal to its pad box. The rule grades a connector as the decoupled IC.
- **Cost:** ~10 min.
- **Reproduce:** `python3 -X utf8 wk/fa10/10_glasgow_revC/helpers/decap_audit.py $R/g6_c92_gnd_election.kicad_pcb $R/intent.json C92`
  (owner `('J5', 2.88, 'graded')`), or check_floorplan on the same board.
- **Existing issues:** none found ("decap tether shares net GND").

## 9. place_pose: several `set --near` ops in one call never snap

- **Tool / command:** `place_pose.py s1_late_rep.kicad_pcb out --intent intent.json
  --radius 1.5 set C53 --near ... set C82 --near 116.3 94.7 set C16 --near ... set C83 --near ...`
- **What it claimed:** `"snapped": null`, refused (`pad_stack_pairs new: C16/U36,
  C82/R35, C83/U6`). Each op was placed at its exact `--near` point.
- **What was true:** the same ops one per call snapped (C82 to 116.55, C16 to
  108.7,94.85). The help says only that several verbs describe one arrangement.
  It does not say `--near` stops snapping.
- **Cost:** ~3 min.
- **Reproduce:** `python3 -X utf8 py_placer/place_pose.py $R/g7_multi_near.kicad_pcb $R/g7_out.kicad_pcb --intent $R/intent.json --radius 1.5 set C82 --near 116.3 94.7 set C16 --near 108.7 94.6`
- **Existing issues:** none found.

## 10. place_seed refuses the pile once the mechanical parts are locked on the board

- **Tool / command:** `rank_rotations.py p01_mk.kicad_pcb ...`, which calls
  `place_seed` without `--force`.
- **What it claimed:** `place_seed will not seed this board (exit 3: it looks
  placed)`.
- **What was true:** 4 of 272 blocks (MK1-4, locked at their mechanical.json
  poses) were on the board and 268 were still in the pile. The skill's own recipe
  (lock the fixed parts first, then seed) trips it, and `--force` is the only way
  through.
- **Cost:** ~2 min.
- **Reproduce:** `python3 -X utf8 py_placer/place_seed.py $R/g1_mk_locked_pile.kicad_pcb $R/g10_out.kicad_pcb --intent $R/intent.json`
  (exit 3).
- **Existing issues:** none (#892, CLOSED, is the place_pose request).

## 11. Routing outputs drop the `.design-brief.json` sibling

- **Tool / command:** `route_planes.py place1.kicad_pcb r1/pour.kicad_pcb ...`
  (and bga_fanout / route.py down the chain).
- **What was true:** `place1.design-brief.json` exists. `r1/pour.*`,
  `r1/fan.*`, `r1/route.*` and `r3/d.*` carry only `.kicad_pro`, so
  `check_floorplan` on a routed board grades without the brief.
  (`copy_board.py` does carry it.) It had no measured effect here, because the
  intent already compiles the brief's clauses and d graded floorplan 0.
- **Cost:** none measured.
- **Reproduce:** `ls wk/fa10/10_glasgow_revC/place1.* wk/fa10/10_glasgow_revC/r1/pour.*`
- **Existing issues:** none found.

## 12. A via under solder shipped unstamped, and board_score calls it advisory while check_drc fails it

- **Tool / command:** the route chain (route.py's ship-time via-under-solder
  stamping, `fab_notes.via_protection_stamps`), then `board_score` and
  `check_drc --baseline <input> --clearance-margin 0.1` on its output.
- **What it claimed:** board_score `drc 0` (blocking), with
  `advisory.drc_via_in_paste 1`. I reported "DRC 0", and the verifier corrected
  me.
- **What was true:** check_drc exits 1 with **1 violation, VIA-IN-PASTE**: the
  +1V2 via at (117.00, 92.60), uuid 8bd3038d..., has its barrel 0.006 mm into
  U36.2's F.Paste opening with no protection tokens. 375 other in-paste vias on
  the same board were stamped `(capping yes) (filling yes)` by the chain. So the
  stamping missed one via the chain created, and the two graders disagree on
  whether that is a DRC. Stamping the same two tokens on that via
  (`helpers/stamp_via_type7.py`) took check_drc to 0, with blocking unchanged.
- **Cost:** ~15 min, and a second verifier call.
- **Reproduce:**
  ```
  python3 -X utf8 py_router/check_drc.py wk/fa10/10_glasgow_revC/r4/final_v1_d.kicad_pcb --baseline wk/fa10/10_glasgow_revC/glasgow_revC.kicad_pcb --clearance-margin 0.1 | tail -12   # 1 VIA-IN-PASTE
  python3 -X utf8 py_tools/board_score.py wk/fa10/10_glasgow_revC/r4/final_v1_d.kicad_pcb --intent $R/intent.json --quiet | tail -3   # drc=0, advisory via_in_paste 1
  ```
- **Existing issues:** none found ("via-in-paste unstamped advisory").
  #962/#996 (the via-in-paste work) are the origin of the rule.

## 13. The skill says `--stop-condition <1|2|3|4>`; the recorder refuses 3 beside a FAIL lens

- **Tool / command:** `converge.py record --final --stop-condition "3: plateau ..."`
  with the verifier's lens files (connectivity FAIL, drc PASS, spec FAIL).
- **What it claimed:** `record: 2 lens FAILED ... --stop-condition must be 2
  (budget spent), 4 (measured-unfixable and said so), or the loop verdict naming
  the same thing (STUCK, BUDGET), not '3: plateau ...'` (exit 2, nothing written).
- **What was true:** converge.py's own comments define STUCK as "stop condition
  3, a plateau", so `--stop-condition STUCK --stop-reason "..."` was accepted.
  SKILL.md §5 rule 6 tells the agent to use `<1|2|3|4>` and never mentions that
  3 must be spelled STUCK when the run ends NOT DONE.
- **Cost:** ~2 min.
- **Reproduce:** re-run the refused command above against a copy of `ledger.jsonl`.
- **Existing issues:** #901 (the stop-condition vocabulary) defines the tokens.
  It is a doc gap in the skill, not a recorder bug.

Also seen, not ranked (no cost to the result): the film's title reads `_film` (from `--from-ledger` with no label), as in run 34. And check_weird reports 21
`stacked-copper` items (verifier call 2's count; call 1 said 22) (duplicate +3V3/GND segments from the plane finalize)
and 3 dangling vias on the shipped board. #162 (OPEN, same-net redundant copper)
covers the stacked copper.

---

## Helpers written (each because no repo tool answered the question)

- `helpers/decap_audit.py` (gap 4): per cap, which supply pins it alone serves,
  plus its elected owner and distance; per failing pin, the candidate caps. It
  calls the grader's functions and mirrors none of them.
- `helpers/overlap_pairs.py` (gaps 1 and 3): lists the pairs behind
  check_floorplan's unattributed overlap total. **Caveat:** it includes pad-less
  logos, which the grade does not. Read its `source none` rows as noise.
- `helpers/stamp_via_type7.py` (gap 12): writes `(capping yes) (filling yes)`
  on one via by uuid, keeping the file's CRLF. No repo CLI re-stamps a single
  existing via. My first version assumed LF and matched nothing, the same trap
  the free-agent smoke run noted.
