# TOOL_GAPS -- fa10 board 08 CM5_MINIMA_3

All commands run from the worktree root `C:/Users/rob/Documents/prive/git/krt-fa10` with
`export MSYS2_ARG_CONV_EXCL='*'`. Repro inputs live in `wk/fa10/08_CM5_MINIMA_3/repro/`
(`input.*` = the given pile board, `conn2.*` = the connector frame, `r1_*` = the first chain,
`r4b_p5.*`, `best_p6e.*`, `final_v2.*` = later boards; intents `intent_given.json`, `intent_cm5*.json`).

## Ranking (by what each cost this run)

| rank | gap | cost |
|---|---|---|
| 1 | G6. check_impedance counts every net's OWN via antipad as a reference-plane void -> impedance can never reach 0 | impedance term can never reach 0 (41 of blocking 42); ~1.5 h of experiments r3fb/r6/r6b before the analysis proved it |
| 2 | G1. check_assembly / board_score: a DECLARED shared origin is an unwaivable "coincident origins" stack | assembly term >= 1 on every compliant board: DONE unreachable by declaration |
| 3 | G12. board_score took 61 min (vs ~1.5 min for every other board) with no timing to say where | 61 min of the 10 h budget waiting on one pair of board_score runs |
| 4 | G11. A rip-and-route lap cannot free a boxed diff-pair escape: it trades one leg for the other | ~30 min of rip laps trading CLK_P/CLK_N, then hand surgery |
| 5 | G3. board_brief / render_placement show the outline's BOUNDING BOX, hiding a notch and four corner ears | one full re-placement (~20 min) after placing against the outline bbox |
| 6 | G2. check_assembly synthesizes a B-side connector an F-side "courtyard" = bbox of its two NPTH mount holes | J601 unseated on two seeds (2 x 8 min) + six waivers to reason out |
| 7 | G7. route_diff's GND return vias violate the pair's own netclass clearance (61 VIA-SEGMENT DRC errors) | 61 DRC errors in r1; a whole chain (~25 min) re-run with --no-gnd-vias |
| 8 | G8. One rescue at 0.1 mm silently lowers the Default netclass 0.13 -> 0.1 for the whole board; the Design-rules line does not mention it | r1 routed at 0.1 mm against the authored 0.13; floor file needed (#1160) |
| 9 | G14. board_score's drc term (check_drc default) skips pad-to-board-edge on a routed board, so KiCad's 2 edge errors read as drc 0 | a verifier round and a defect (C709/C710) the run grade could not see |
| 10 | G10. Net patterns match case-INSENSITIVELY on Windows only (fnmatch.fnmatch) -- platform-dependent grading | 1 point of blocking on Windows; platform-dependent net scope |
| 11 | G9. place_pose `--near` refuses every candidate, then advises `--snap` on the pose it just refused | ~10 min chasing an SW501 pose the hole keep-out could never allow |
| 12 | G4. place_seed refuses the pile once the fixed parts are locked, naming the declared module pair as "the pile" | ~5 min; --force workaround (#1165 family) |
| 13 | G5. emit-intent withheld the decap budget because the declared module pair "is a pile" | ~5 min; decap limit re-armed by hand from the intent's own census |
| 14 | G13. check_floorplan exits 4 ("violations found") on "0 error(s)"; grade.py then reports floorplan_pass false | ~2 min; grade.py reports floorplan_pass false on 0 errors |

## G6. check_impedance counts every net's OWN via antipad as a reference-plane void -> impedance can never reach 0

- **Tool / command:** `python3 -X utf8 py_tools/check_impedance.py wk/fa10/08_CM5_MINIMA_3/repro/r1_p4_route.kicad_pcb --nets '/*USB_*' '/*PCIE*' '/*USB2*' '/*ETH_PI*' '/*HDMI_P*.D*' '/*DPHY0*' '/*HDMI_P*.CK*' --json /tmp/imp.json`
  (board_score `--impedance-nets` runs exactly this and adds `nets_with_crossing` to `blocking`).
- **Claimed:** `nets_with_crossing 39` of 42; 232 crossings; F.Cu->In1 and B.Cu->In4 crossings on 38 / 34 nets
  although In1/In4 were FORBIDDEN to every signal (`--layer-costs ... -1 ... -1`) and carry no copper but GND.
- **True:** all 107 F/B crossings lie within 0.6 mm of a via of the SAME net (measured by distance to every via).
  The fixed `DEFAULT_MIN_VOID_LENGTH = 0.30` ("quantization noise around a via antipad") is shorter than the
  antipad a 0.45 mm via gets at the impedance netclass clearance 0.2 (0.225 + 0.2 = 0.425 mm radius, and a
  P/N via pair merges two). Nothing in `analyze()` (~line 480-530) exempts a trace's own via. Every impedance
  net on this board must change layers (CM5 pads on B.Cu, every connector on F.Cu), so the component has a
  floor equal to the number of routed impedance nets with a via. Even `--min-void-length 0.5` leaves 18 B/In4
  and 11 F/In1 own-via crossings (merged pair antipads).
- **gh issue search:** `check_impedance via antipad`, `min-void-length` -> none.

## G1. check_assembly / board_score: a DECLARED shared origin is an unwaivable "coincident origins" stack

- **Tool / command:** `python3 -X utf8 py_tools/check_assembly.py wk/fa10/08_CM5_MINIMA_3/repro/conn2.kicad_pcb --intent wk/fa10/08_CM5_MINIMA_3/repro/intent_cm5_v2.json`
- **Claimed:** `COINCIDENT ORIGINS (1): Module301 Module302 @ (127.25, 77.6)` and `VERDICT: NOT BUILDABLE`
  (`blocking 0`, `courtyard_blocking 0`, no other gating channel). board_score folds it into
  `assembly`, so `blocking >= 1` on every board that honours `mechanical.json`.
- **True:** `mechanical.json` (fa10-decl-v1 JUDGMENT) declares BOTH CM5 connector footprints at
  (127.25, 77.6, rot 180) -- the Raspberry-Pi-5-Compute-Module GPIO/HSS footprints share the module
  origin by library design; their pads are 34 mm apart (x 126.2-129.3 vs x 92.2-95.3) and never touch.
  `stack_groups` in `check_assembly.py` (~line 207-224) consults no `overlap_waivers[]` entry and no
  fixed-pose declaration, so the stack can never be accepted; the intent DOES accept the pair's
  courtyard overlap (`waived:intent_declared`). DONE (`blocking 0`) is therefore unreachable on this
  board by any placement that meets the mechanical declaration.
- **gh issue search:** `coincident origins`, `coincident_origins waiver`, `stacked origin connector` -> no issue covers it.

## G12. board_score took 61 min (vs ~1.5 min for every other board) with no timing to say where

- **Tool / command:** two concurrent `board_score.py r3/p4_route.kicad_pcb` / `r3fb/p4_route.kicad_pcb --intent ... --impedance-nets ... --min-via-diameter 0.45 --min-via-drill 0.3 --baseline ...` at 12:53Z; both JSON files written 13:53Z. The identical concurrent pair on r2/r2t took 1.5 min.
- **True:** the score JSON and log carry no per-component wall time, so the 40x outlier cannot be attributed (an oracle / kicad-cli stall is my guess, unverified). It cost ~1 hour of the 10-hour budget. Not reproduced.
- **gh issue search:** `board_score slow timing` -> none.

## G11. A rip-and-route lap cannot free a boxed diff-pair escape: it trades one leg for the other

- **Tool / command:** from `wk/fa10/08_CM5_MINIMA_3/repro/r4b_p5.kicad_pcb`: `py_router/route.py ... --nets '/CM5/PCIE_PI.CLK_P' '/CM5/PCIE_PI.CLK_N' '/CM5/PCIE_PI.PWR_EN' '/CM5/PCIE_PI.nWAKE' '/CM5/PCIE_PI.nCLKREQ' GND +5V --rip-existing-nets <same names> GND` (flag string in `helpers/lap.sh`).
- **Claimed:** each lap `ACCEPTED` by the improvement gate ("connected 1, broke 1").
- **True:** r4a/r4b/r4c alternated CLK_P and CLK_N between connected and broken. The cause, read off the copper: the finalize tapped Module302 GND pin 48.7 WEST to USB701's GND leg, fencing the 1.6 mm corridor the CLK pair needs, while the same GND pins were already linked on the inner side. A GND via INSIDE the column (93.05, 48.1; check_join CLEAN) plus deleting the 4-segment west tap let a CLK_N-only lap connect in 2.5 min. The plane finalize has no notion of "tap toward the side no signal escape needs"; route.py also refuses to rip GND once any GND copper is locked (my hand joins), with no message naming the lock.
- **gh issue search:** `force-reroute` -> #1192 (OPEN, the lock-override wording) is adjacent, not this.

## G3. board_brief / render_placement show the outline's BOUNDING BOX, hiding a notch and four corner ears

- **Tool / command:** `python3 -X utf8 py_tools/board_brief.py wk/fa10/08_CM5_MINIMA_3/repro/input.kicad_pcb --json /tmp/b.json`
  and `python3 -X utf8 py_tools/render_placement.py wk/fa10/08_CM5_MINIMA_3/repro/conn2.kicad_pcb -o /tmp/r.png --per-side`
- **Claimed:** `outline 61.199 x 64.2 mm (3929.0 mm2)`; the render fills that rectangle.
- **True:** the Edge.Cuts ring (30 primitives) is a 54.5 x 57.1 mm body (x 78.36-132.90, y 23.93-81.07)
  with four mounting-hole ears and an 11.1 x 15.8 mm RJ45 notch (x 78.37-89.48, y 28.24-44.03).
  I placed J501/J802/SW501/SW101 against the bbox edges first; only place_seed's `pad_edge_after`
  (`J1.16 off-board`, `SW501.4 off-board shortfall 1.61`) exposed it. Cost: one full re-placement.
- **gh issue search:** `board_brief outline bbox`, `render_placement outline` -> no direct match (#1162 is a different bbox problem).

## G2. check_assembly synthesizes a B-side connector an F-side "courtyard" = bbox of its two NPTH mount holes

- **Tool / command:** same as G1, then read `courtyard_pairs` in `--json`.
- **Claimed:** `J503 <-> Module302 courtyard 25.8mm2 side F COURTYARD-BLOCKING`, `L701 <-> Module302
  18.54mm2 F`, `J601 <-> Module302 15.6mm2 F` (overlap_rect x 125.75-128.75); the Module301 twins
  read `waived:edge_class` until the intent carried ANY explicit `overlap_waivers`, then they read
  COURTYARD-BLOCKING too.
- **True:** Module302 is a B-side SMD connector whose B.CrtYd is x 91.86-95.64, y 44.7-67.5. Its two
  NPTH holes sit at (127.25, 29.6) and (127.25, 77.6); the tool unites them into one F-side
  rectangle x 125.75-128.75, y 28.1-79.1 -- a 3 x 51 mm strip where Module302 has nothing on F.
  The seeder honours the same phantom: J601 came back `unseated` with `no_pose_verdict keepout_blocks`
  on two seeds because its every pose near Module301's GPIO pins lies in that strip.
- **Workaround:** six `overlap_waivers` pairs in `intent_cm5.json`, each naming this measurement.
- **gh issue search:** `NPTH courtyard`, `courtyard mount hole bbox` -> no issue covers it.

## G7. route_diff's GND return vias violate the pair's own netclass clearance (61 VIA-SEGMENT DRC errors)

- **Tool / command:** `python3 -X utf8 py_router/route_diff.py wk/fa10/08_CM5_MINIMA_3/repro/r1_p1_pour.kicad_pcb /tmp/d90.kicad_pcb --nets '/*USB_*' '/*PCIE*' '/*USB2*' --impedance 90 --diff-pair-gap 0.154 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 2.0 3.0 -1 1.0 --via-size 0.45 --via-drill 0.3 --escalation board`
  then `python3 -X utf8 py_router/check_drc.py <out> --clearance-margin 0.1`.
- **Claimed:** route_diff reports the pairs routed, no DRC finding of its own.
- **True:** the run adds GND vias beside each pair's via pair (12 in the 90 ohm call, 26 more in the 100 ohm
  call); 35 of those 38 sit inside the pairs' 0.2 mm class clearance -> `VIA-SEGMENT violations (61)`, every one
  `Via:GND <-> Seg:<pair net>`, "Required clearance: 0.2000mm (local/netclass override; global 0.1000mm)".
  Workaround: `--no-gnd-vias`.
- **gh issue search:** `route_diff gnd vias clearance`, `diff pair gnd via netclass clearance` -> none (#435 fixed the pair's own gap/clearance, not the return vias).

## G8. One rescue at 0.1 mm silently lowers the Default netclass 0.13 -> 0.1 for the whole board; the Design-rules line does not mention it

- **Tool / command:** `python3 -X utf8 py_router/route.py wk/fa10/08_CM5_MINIMA_3/repro/r1_p3_d100.kicad_pcb /tmp/p4.kicad_pcb --nets '*' --power-nets GND +5V M2_3V3 VBUS_USB2.0 +3V3_PI HDMI_+5V --power-nets-widths 0.3 0.4 0.3 0.4 0.25 0.25 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.5 2.5 -1 1.0 --track-width 0.1 --via-size 0.45 --via-drill 0.3 --escalation board --max-ripup 5`
- **Claimed:** `Design rules [--escalation board, --fab-tier auto]: 46 feature(s) on 15 net(s) delivered below the requested size (smallest track width 0.0889 mm)`; every `design_rules.narrowed` entry is a track width.
- **True:** one GND gap rescue ran at `clearance 0.1` (log line `rescued a gap: grid 0.025, clearance 0.1, track 0.0889`), and the run then wrote `net_class[Default].clearance: 0.13 -> 0.1` and `rules.min_hole_clearance -> 0.1`; check_drc then grades EVERY net at 0.1. `--escalation board` treats `min_clearance 0.0` as "no floor" although KiCad enforces the 0.13 netclass clearance. Workaround: `--fab-overrides` with `clearance = 0.13`.
- **gh issue search:** `rescue clearance writeback default class` -> **#1160 (OPEN)** "One net's rescue lowers the Default class clearance in the project, and the next step routes every net there even under --escalation off" -- same defect; this run adds that the disclosure line omits it.

## G14. board_score's drc term (check_drc default) skips pad-to-board-edge on a routed board, so KiCad's 2 edge errors read as drc 0

- **Tool / command:** `python3 -X utf8 py_router/check_drc.py wk/fa10/08_CM5_MINIMA_3/repro/final_v2.kicad_pcb --baseline wk/fa10/08_CM5_MINIMA_3/repro/input.kicad_pcb --clearance-margin 0.1` vs the same with `--check-pad-edge`, and `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/fa10/08_CM5_MINIMA_3/repro/final_v2.kicad_pcb`.
- **Claimed:** `NO DRC VIOLATIONS FOUND!` and board_score `drc=0` ("Skipping pad-to-board-edge checks (--check-pad-edge is off; pads are edge-exempt by default because on a routed board the hits are usually pre-existing edge connectors)").
- **True:** KiCad reports `copper_edge_clearance` on J1.15 and J1.16 (Net-(J1-MP1), 0.204 mm from the RJ45 notch edge vs 0.372). In `full` mode every part was PLACED by the run, so "pre-existing" does not hold; `--baseline` is given and could tell inherited from new. (Here the two hits are forced by the notch width -- disclosed in the report -- but the exemption would hide a placement-created one the same way.) Also: check_assembly files a 0.075 mm / 0.24 mm2 courtyard overlap (C709/C710, created by a decap nudge) as `advisory` (below its 0.3 mm depth floor) while KiCad reports it as a courtyard ERROR -- found by the verifier, fixed by me.
- **gh issue search:** `check_drc pad edge default routed`, `check-pad-edge` -> #338 (CLOSED, edge clearance not honoured by router/grading) is the ancestor; nothing open on the default exemption.

## G10. Net patterns match case-INSENSITIVELY on Windows only (fnmatch.fnmatch) -- platform-dependent grading

- **Tool / command:** `python3 -X utf8 py_tools/check_impedance.py wk/fa10/08_CM5_MINIMA_3/repro/best_p6e.kicad_pcb --nets '/*PCIE*' --json /tmp/i.json`
  (and every `--nets` / `--impedance-nets` filter: they all go through `net_queries.net_pattern_matches`).
- **Claimed:** `/PCIe-M2/FB` (the M.2 buck's FEEDBACK divider net) is analyzed as a 90-ohm impedance net.
- **True:** the project's netclass pattern is `/*PCIE*`; `fnmatch.fnmatch` folds case on Windows (`fnmatch('/PCIe-M2/FB','/*PCIE*') -> True`, `fnmatchcase -> False`), so the same command selects a different net set on Linux/macOS. It is NOT harmless here: `/PCIe-M2/M2_LX` (the buck's switch node) is matched too and carries a reference crossing, so it is 1 of the final board's `impedance 41` -- on a POSIX host the same board scores 40 (FB has no via and no crossing). `board_score` blocking and every `--nets` scope are platform-dependent.
- **gh issue search:** `fnmatch case windows`, `case-insensitive net pattern` -> none.

## G9. place_pose `--near` refuses every candidate, then advises `--snap` on the pose it just refused

- **Tool / command:** `python3 -X utf8 py_placer/place_pose.py <b02d board> <out> --intent <intent> --radius 4 --snap-tries 30 set SW501 --near 130.9 31.0 --rot 0`
- **Claimed:** "REFUSED ... The pose ranker's nearest candidate is x=130.9 y=31 rot=0 (0.000 mm away) -- try it with --snap" (the call already carried `--near`, which implies `--snap`).
- **True:** the conflict is the CM5 mount-hole NPTH keep-out (local_clearance 1.5-1.7 mm -> 3.2 mm radius at (127.25, 29.6)); no pose within 4 mm clears it, and the message names neither the radius nor the hole.
- **gh issue search:** `snap refused nearest candidate` -> none.

## G4. place_seed refuses the pile once the fixed parts are locked, naming the declared module pair as "the pile"

- **Tool / command:** `python3 -X utf8 py_placer/place_seed.py wk/fa10/08_CM5_MINIMA_3/repro/seed_refuse_input.kicad_pcb /tmp/s.kicad_pcb --intent wk/fa10/08_CM5_MINIMA_3/repro/intent_cm5.json --seed 0`
- **Claimed:** `place_seed: partially unplaced -- seeding only the 2 stacked part(s) that look like a pile; the rest stand as placed`, then exit 3 because those 2 are locked.
- **True:** 69 parts sat in the staging pile south of the outline (board_brief: `pile: true`). `--force` seeds them (locked parts kept).
- **gh issue search:** `place_seed partially unplaced locked` -> #1165 (OPEN) "place_seed refuses a pile as already PLACED once the fixed parts are placed and locked" -- same family; this board adds the variant where a declared co-located pair is read as the pile.

## G5. emit-intent withheld the decap budget because the declared module pair "is a pile"

- **Where:** the given `intent.json` `context.budget_withheld.decaps.max_distance_mm`: "it is not placed (2 footprint(s) are stacked on another (Module301, Module302) ...): a limit read off it would bless a pile".
- **True:** the census the same file carries (`decap_census`: 19 tethers, max 3.79 mm, beyond_radius 0) is a usable budget; the only "stack" is the declared co-location (G1). I armed `decaps.max_distance_mm 3.8` in `intent_cm5.json`.
- **gh issue search:** `decap budget withheld stacked` -> none.

## G13. check_floorplan exits 4 ("violations found") on "0 error(s)"; grade.py then reports floorplan_pass false

- **Tool / command:** `python3 -X utf8 py_tools/check_floorplan.py wk/fa10/08_CM5_MINIMA_3/final.kicad_pcb --intent wk/fa10/08_CM5_MINIMA_3/intent_cm5.json --allow-routed; echo $?`
- **Claimed:** exit 4, which the tool's own exit table defines as "graded successfully, violations found"; `scripts/grade.py` turns that into `"floorplan_pass": false` next to `"floorplan_errors": 0`.
- **True:** the text says `0 error(s), 3 warning(s)` (decap_ungraded warnings); the only other non-pass content is "ALSO NOT FULLY GRADED: 2 budget_abstained, 1 rules_skipped_armed" and OWED rule dispositions. A reader of exit codes (or of grade_final.json) sees a floorplan failure that the grader itself does not report. board_score's `floorplan` component reads 0.
- **gh issue search:** `check_floorplan exit 4 warnings`, `floorplan_pass grade.py` -> none (#959 is the declare-stage work, not this exit code).

## Helpers written (each is a gap: no repo tool did it)
- `helpers/fp_geom.py` -- per-layer local courtyard/fab/silk bbox of named footprints (to decide a connector's mating face). v1 used a regex that ran across elements and misreported courtyards (cost me a wrong belief that Module30x courtyards cover the whole CM5).
- `helpers/seedsum.py` -- prints the useful fields of place_seed's ~200 KB JSON_SUMMARY line.
- `helpers/chain.sh`, `chain_fb.sh`, `chain_split.sh`, `lap.sh`, `lap_fb.sh` -- replay the pour/diff/route chain and single laps with one identical flag string (no repo driver may be used; the routing skill's Step 2d demands verbatim flag strings).
- `helpers/lock_copper.py` -- check_join `--keep-staged` writes hand copper UNLOCKED and there is no tool to lock it (the skill says to stamp it). My v1 put `(locked yes)` before a via's `(layers ...)` and kicad_parser silently DROPPED both vias (its via prefix is positional) -- no warning; fixed in v2.
- `helpers/edit_copper.py` -- delete a specific mis-placed tap, move a segment endpoint onto its via centre, lock a chosen subset: no repo tool edits existing copper surgically.
