# TOOL_GAPS -- board 12 steppenprobe

Ranked by what each cost this run. Every repro command runs from the worktree root
(`cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH"`); its inputs are copies in
`wk/gpm/12_steppenprobe/repro/` (outputs to `repro/out/`). Issue searches were read-only
`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`.

---

## 1. check_floorplan / place_simple misread an edge connector's overhang on a rounded-corner outline: J1 was seated 2.2 mm too deep and graded "pass"

- **Tool / command:** `place_simple.py` (edge seat) and `check_floorplan.py --intent` with J1's
  `edge_connectors[].overhang_mm = {min 2.51, max 2.60}` (from the GCT USB4085 drawing: the board edge 1.74 mm past
  the rear shield slot = the footprint's own "PCB Edge" marker; drawn body 2.51 mm past it).
- **Claimed:** `J1 north: overhang 2.5149mm [legacy_occupancy@margin=0] pass` on every seed; the seat placed J1 "in band".
- **True:** the board outline has rounded corners, so the body reading abstains and the grade falls back to
  `legacy_occupancy`, which (as the verifier traced through `rect_outside_amount`) sums the bbox term plus one
  term per off-board corner: 3 x 0.838 mm = 2.5149 for a courtyard 0.838 mm past the edge. The F.Fab body
  actually reached **0.338 mm** past the edge (front at y = 49.662), the "PCB Edge" marker sat 2.17 mm INSIDE the
  outline -- the receptacle was 2.2 mm too deep. Moved to the drawing's pose (body 2.55 mm past), the same grade
  reads **9.15 mm** and errors past the 2.60 max. So the band can be neither seated nor graded on this outline;
  I removed it from `intent_run.json` and seated J1 by `place_pose` (CHOSEN.json `after`). Cost: verifier FAIL
  (D1), a re-placement and every route redone.
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/check_floorplan.py wk/gpm/12_steppenprobe/repro/seed2_placed.kicad_pcb --intent wk/gpm/12_steppenprobe/repro/intent_run_J1band.json | grep "J1 north: overhang"   # 2.5149 pass (real body overhang 0.338)
  python3 -X utf8 py_tools/check_floorplan.py wk/gpm/12_steppenprobe/repro/seed2_J1moved.kicad_pcb --intent wk/gpm/12_steppenprobe/repro/intent_run_J1band.json | grep "J1 north: overhang"  # 9.1500 fail (real body overhang 2.55)
  ```
- **Issues:** "overhang rounded outline legacy_occupancy" -> #1301 (closed: band graded on courtyard changes with
  floors), #987, #961 (closed) -- the same rule, not this outline case. Not covered.

## 2. The DRC writeback lowers the board's own `min_hole_clearance` 0.25 -> 0.15, the delivered fill is then poured 0.15 mm from NPTH holes, and no DONE grader sees it

- **Tool / command:** `route_diff.py ... --escalation board` (and every later route.py step keeps it):
  `rules.min_hole_clearance: 0.25 -> 0.15 mm` / `FAB FLOOR RELAXED -- copper-to-hole clearance`. Then
  `fill_for_delivery.py` fills at the project's 0.15.
- **Claimed:** `check_complete --authored-from <input>` DONE (no floor listed); check_drc 0 violations;
  board_score blocking 0; KiCad DRC with the delivered project 0 hole errors.
- **True:** the verifier measured the shipped +3V3 / GND fills **0.1505 mm** from the NPTH hole edges of H1-H4
  (3.2 mm) and SW1's two pegs -- 12 hole/layer pairs -- against the authored 0.25 (KiCad under the input
  project would flag each). No track needed the relaxation (KiCad DRC of the routed copper under the ORIGINAL
  project, refilled: 0 hole_clearance). check_drc "does not grade zone fill"; `--authored-from` does not list
  `min_hole_clearance`. Workaround: `--no-fix-drc-settings` on route_planes / route_diff / route.py (the project
  then keeps 0.25 and the fill honours it). Cost: verifier FAIL (D2) and a re-route.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route_diff.py wk/gpm/12_steppenprobe/repro/diff_in.kicad_pcb wk/gpm/12_steppenprobe/repro/out/diff_out.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1
  # "rules.min_hole_clearance: 0.25 -> 0.15 mm"; then check_complete <any board of that chain> --authored-from wk/gpm/12_steppenprobe/steppenprobe.kicad_pcb -> DONE
  ```
- **Issues:** #1319 (closed, route_planes lowering min_hole_clearance), #1285 (closed, --no-fix-drc-settings),
  #1198 (closed, --authored-from vs min_hole_clearance), #1038 (closed). This route_diff path plus the silent
  `--authored-from` looks like a regression of that family.

## 3. No routing step can hold a per-net minimum width; route.py's taps fail where a one-segment stub fits; and the skills disagree on whether a net-class width is a spec

- **Tool / command:** `route.py` with `--power-nets ... --power-nets-widths` (the board's `Power` class: 0.3 mm on
  +1V8, +3V3, +5V, /VPHY, /VPLL, GND, VBUS, Vdrive), graded `board_score --net-min-widths power_min_widths.json`.
- **Claimed / instructed:**
  - plan-pcb-routing Step 4: net-class `track_width` is "not DRC floors -- they are just defaults ... the human
    originals do use smaller"; SKILL.md §4: "grade power widths with board_score --net-min-widths"; the verifier
    brief rule 5 FAILs a board whose declared "power widths" class is ungraded -- it did (D3).
  - `--escalation board` "down to the board's own declared floors"; `--escalation off` "a wide power ... net may
    still neck for at most 2 mm".
- **True (measured, J1-moved placement):**
  - Every `--escalation board` route necks power copper to the board's 0.15 floor at pads and in finalize straps:
    net_widths 4-6 nets failing (e.g. K5: 153 segments under 0.3). No flag sets a per-net neck floor.
  - `--track-width 0.3 --escalation off` on the power nets: GND taps on U1 pins 15/25/35/51, VBUS at J1 and a
    +1V8 pin left "STILL FLOATING" (N2: 7 joins) -- yet `check_join` graded a plain 1.2 mm stub + via from U1.15
    CLEAN on the same board, so the tap search, not the geometry, failed there.
  - `--no-bga-zones` and `--grid-step 0.05` changed nothing (improvement gate reverted).
  - What finally worked (no hand copper): power widths at the class 0.3 (not my 0.7), the 8 power nets routed
    FIRST at exact 0.3, then the signals (`'*'` minus the power nets, `--escalation board`) twice, then the power
    nets again at exact 0.3, at `--layer-costs 1.0 1.0` (arm P6 = the shipped chain: DONE with net_widths 0, 140
    vias). The same chain at 1.0 1.2 / 1.5 / 2.0 left 1-2 pads open (U1.20 on a +3V3 pour island). It took 14
    arms to find; the skill's chain (one `route.py --nets '*'` with `--power-nets`) cannot express it.
  - On the way I wrote two helpers, neither used on the shipped board: `helpers/widen_power.py` (widen each
    narrow power segment when check_join grades the 0.3 version CLEAN: 124-140 of ~150 per board, always 13-36
    left) and `helpers/find_tap.py` (search stub+via joins for check_join; found U1.35's, not U1.20's).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route.py wk/gpm/12_steppenprobe/repro/N2_p2.kicad_pcb wk/gpm/12_steppenprobe/repro/out/n2.kicad_pcb --nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --clearance-ceiling 0.15 --layer-costs 1.0 1.5 --same-net-pad-clearance 0.1 --no-fix-drc-settings --track-width 0.3 --escalation off
  # "Pads still unconnected: U1.15 (GND), U1.25 (GND), U1.35 (GND), U1.51 (GND)"
  python3 -X utf8 py_tools/check_join.py wk/gpm/12_steppenprobe/repro/N2_p2.kicad_pcb GND 129.137,83.0,F.Cu 129.137,81.8,F.Cu via:129.137,81.8 --width 0.3 --via-size 0.6 --via-drill 0.3   # CLEAN
  ```
- **Issues:** "netclass track_width net-min-widths verifier" -> nothing; "power net width recommendation" ->
  nothing relevant. Not covered.

## 4. `--no-fix-drc-settings` also drops the protected-nets record, so the later steps re-route the routed USB pair single-ended

- **Tool / command:** the shipped chain needs `--no-fix-drc-settings` (gap #2) on route_diff and route.py. route_diff
  then writes no `kicad_routing_tools.protected_nets` (the project stays byte-identical to the input's).
- **Claimed:** CLAUDE.md / #521: "routed diff pairs are recorded in the sibling .kicad_pro and later steps will NOT
  rip them"; `--no-fix-drc-settings` is documented only as "Do not adjust the output's .kicad_pro DRC constraints".
- **True:** with the flag, `protected_nets` is None after route_diff; the next `route.py` steps (whose `--nets` hold
  the pair's single-ended follow-up members) re-route /USB_DP and /USB_DM from scratch: of route_diff's 103 pair
  segments (31.3 mm coupled) only 35 survive on the delivered board, and the verifier reports the pair "not routed
  as a coupled pair" (DP 42.96 mm / 2 vias, DM 38.76 mm / 5 vias). The same chain WITHOUT the flag on route_diff
  (arm Q) records the pair, keeps 75 of 103 segments -- and puts `min_hole_clearance 0.15` back into the project
  (gap #2). No flag gives both. I shipped the uncoupled pair (diff pairs are undeclared, so ungraded) and say so.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route_diff.py wk/gpm/12_steppenprobe/repro/diff_in.kicad_pcb wk/gpm/12_steppenprobe/repro/out/d_nofix.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --no-fix-drc-settings
  python3 -c "import json;print(json.load(open('wk/gpm/12_steppenprobe/repro/out/d_nofix.kicad_pro')).get('kicad_routing_tools'))"   # no protected_nets
  ```
- **Issues:** "no-fix-drc-settings protected_nets" -> #521 (closed: the protection itself). This interaction is not covered.

## 5. place_simple: a group's `edge` hint is met when ANY one member touches that side -- the skill says it puts the group on the side

- **Tool / command:** `py_placer/place_simple.py ... --groups groups.json` with `"edge": "S"` on the 27-part
  `target` group holding the 41.7 mm 1x16 header J4. Cost term in `placement/simple.py` `_hint_full`:
  `min((side(P[r].rect()), (r,)) for r in h['a'])` -- the least distance of ANY member.
- **Claimed:** SKILL.md §3.3 "`edge` ... a group that belongs on a board side"; grouping.py "the board side a group belongs on".
- **True:** in all three floorplan-clean pass-1 seeds J4 stood mid-board (s1: vertical at x=130.5, pads
  y 69.8-107.9; s2: horizontal across the north half; s3: vertical down the centre) while the hint read
  satisfied -- on the s1 repro `edge:target:S` is absent from the `hints` breakdown (cost 0) because J4's end is
  2.1 mm from the south edge. A long connector standing up from the edge scores the same as one lying along it.
  The workaround (pass 2: J4 in `edge_connectors[]` east, `mating_face` +x) routed worse (183 vias / blocking 1)
  and was rejected.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gpm/12_steppenprobe/repro/pile.kicad_pcb wk/gpm/12_steppenprobe/repro/out/edge_s1.kicad_pcb --groups wk/gpm/12_steppenprobe/repro/groups_pass1.json --intent wk/gpm/12_steppenprobe/repro/intent_run_pass1.json --seed 1
  # J4 at (130.52, 69.8) rot 0; the 'hints' line carries no edge:target:S term
  ```
- **Issues:** #1330 (closed: `apart` constant when groups touch) is the same family; nothing covers `edge`.

## 6. route.py leaves a redundant +1V8 loop on most routes of one placement; check_complete then stays INCOMPLETE

- **Tool / command:** the chain (route_planes, route_diff, route.py x3) on pass-1 seed 2 (pre-J1 move), then
  `check_complete.py` / `check_weird.py`.
- **Claimed:** route.py's end-of-run "Strict collapse (#1063)" / stacked-copper dedup; MIN `failed: 0`; board_score blocking 0.
- **True:** 4 of 5 recipe variants (F, G, H = `--max-ripup 5`, I = first-choice retry) left
  `redundant-cycle: 1 -- net +1V8 (F.Cu) loop edge (130.175, 80.725)-(130.175, 81.615); removal leaves
  connectivity identical` -> check_complete INCOMPLETE. `--rip-existing-nets +1V8` is a no-op on a connected net;
  `route.py --nets +1V8 GND +3V3 --force-reroute` cleared it.
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/12_steppenprobe/repro/regrade_in.kicad_pcb` (redundant-cycle 1, +1V8).
- **Issues:** #162 (OPEN, same-net redundant copper producers) covers it.

## 7. Skill step "leave `--min-thickness` at 0.1" replaces the designer's 0.15 mm pours and leaves sub-floor pour webs

- **Tool / command:** `route_planes.py --nets +3V3 GND --plane-layers F.Cu B.Cu` on a board that already carries
  both board-wide pours at `min_thickness 0.15`.
- **Claimed:** plan-pcb-routing Step 1: "`--min-thickness` (default 0.1) ... leave it unless a fab demands wider";
  route_planes discloses `minimum width: 0.15 mm -> 0.1 mm [--min-thickness]`.
- **True:** at 0.1 the route left 12 KiCad `connection_width` webs on +3V3 (kicad_drc_compare, graded at the
  board's 0.15 min_track_width; no DONE grader sees them). Re-pouring at the designer's 0.15 removed all 12 AND
  routed better (140 vias / 1400 mm vs 142 / 1484).
- **Repro:** `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/12_steppenprobe/repro/connwidth_in.kicad_pcb` (connection_width: 12)
  and `python3 -X utf8 py_router/route_planes.py wk/gpm/12_steppenprobe/repro/seed2_placed.kicad_pcb wk/gpm/12_steppenprobe/repro/out/pour_out.kicad_pcb --nets +3V3 GND --plane-layers F.Cu B.Cu` ("minimum width: 0.15 mm -> 0.1 mm").
- **Issues:** none found ("connection_width zone min_thickness", "route_planes min-thickness replaced zone").

## 8. analyze_power_paths counts each sink's current once per power pin -- every rail comes out several times too wide

- **Tool / command:** the `/analyze-power-nets` recipe (`get_power_net_recommendations`).
- **Claimed:** "Each net's current is the sum of the traced paths through it plus the power pins of the sinks and sources on it".
- **True:** the loop adds a sink's whole `current_rating_ma` for EVERY power pin (U1 FT2232HL, 70 mA, has 19
  power pins -> 1330 mA) and a source's rating on top of its sinks: GND 2.0 mm, +3V3 1.0, VBUS 1.0, +1V8 0.7 for
  a board drawing ~250 mA through a 200 mA LDO. I overrode them (0.7 / 0.5 / 0.3; later the class 0.3 -- see #3).
- **Repro:**
  ```bash
  python3 -X utf8 -c "
  import sys; sys.path[:0]=['py_tools','py_router']
  from analyze_power_paths import *
  c,p=analyze_pcb('wk/gpm/12_steppenprobe/repro/pile.kicad_pcb')
  classify_component(c,'U1',ComponentRole.CURRENT_SINK,current_rating_ma=70)
  classify_component(c,'U2',ComponentRole.POWER_SOURCE,current_rating_ma=200)
  print(get_power_net_recommendations(p,c,trace_power_paths(p,c)))"   # {'+3V3': 1.2, 'GND': 1.2, 'Vdrive': 1.0, ...}
  ```
- **Issues:** none found.

## 9. Default via-in-pad: 79-82 vias in SMD pads on a KiCad 6 file that cannot declare their protection; check_drc accepts

- **Tool / command:** `route.py` defaults (`--same-net-pad-clearance` unset), then `check_drc.py`.
- **Claimed:** `79 undeclarable in this file format (accepted; Type VII belongs on the fab drawing)`.
- **True:** arm B 79, arm D 82 vias in paste openings (mostly 0603 decap ground pads). `--same-net-pad-clearance 0.1`
  (arm F) cut it to 2 AND used fewer vias (150 vs 160).
- **Repro:** route `wk/gpm/12_steppenprobe/repro/seed1_placed.kicad_pcb` with/without `--same-net-pad-clearance 0.1`; `check_drc.py <out> --clearance-margin 0.1 | grep "Vias in"`.
- **Issues:** #1025 (closed wontfix, explicit via-in-pad policy) covers the policy.

## 10. route.py's own regrade / oracle disagree with KiCad in both directions on a +3V3 pour pad

- **Tool / command:** route.py finalize (`JSON_REGRADE`, "Pads still unconnected").
- **True:** (a) on the arms/P1s2 board `JSON_SUMMARY_MIN` said `failed 1, pad_pairs_open +3V3 (U1 126.71,86.96)` while
  check_connected, board_score and `kicad-cli pcb drc --refill-zones` all found it connected; (b) on arms/P2/p3
  route.py said "Pads still unconnected: none (all model-only; confirmed connected by the oracle)" while
  check_connected ("Disconnected pads: (126.71, 86.96) [U1]") and KiCad (1 unconnected: two pieces of the +3V3
  zone) found U1.20 on an island.
- **Repro:** (b) `python3 -X utf8 py_router/route.py wk/gpm/12_steppenprobe/repro/P2_p2.kicad_pcb wk/gpm/12_steppenprobe/repro/out/p2b.kicad_pcb --nets +3V3 GND --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --clearance-ceiling 0.15 --layer-costs 1.0 1.5 --same-net-pad-clearance 0.1 --no-fix-drc-settings --track-width 0.3 --escalation board`
  ("confirmed connected by the oracle") then `python3 -X utf8 py_router/check_connected.py wk/gpm/12_steppenprobe/repro/out/p2b.kicad_pcb` ("Disconnected pads: (126.71, 86.96) on F.Cu [U1]");
  (a) `python3 -X utf8 py_router/route.py wk/gpm/12_steppenprobe/repro/regrade_in.kicad_pcb wk/gpm/12_steppenprobe/repro/out/regrade_out.kicad_pcb --nets +1V8 GND +3V3 --force-reroute --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1` then `check_connected.py` on the output.
- **Issues:** #1339 (closed) is the GND "recovered" direction; not these.

## 11. The judge's quick-route ranking inverted on the full routes (§3.7)

- **Claimed:** judge_seeds best = seed 1 (blocking 0, 131 vias), then seed 3 (blocking 0), seed 2 last (blocking 4).
- **True (full routes, same recipe):** seed 2 142 vias DONE, seed 1 147, seed 3 blocking 1. §3.7 has no step letting
  the full route overrule the judge; I kept seed 2 on that evidence.
- **Repro:** route `repro/seed1_placed.kicad_pcb` and `repro/seed2_placed.kicad_pcb` with `plan/final_plan.sh`'s commands.
- **Issues:** documented statistical behaviour; none filed.

## 12. A flag token inside `--nets` is taken as a net name (route.py, route_diff.py)

- **True:** zsh passed `--power-nets GND ... 0.3` / `--layer-costs 1.0 1.5` as ONE argv word; both tools warned
  "Net '...' does not exist" and routed at exit 0 without the widths/costs (one lap of three arms lost).
- **Repro:** `python3 -X utf8 py_router/route.py wk/gpm/12_steppenprobe/repro/diff_in.kicad_pcb wk/gpm/12_steppenprobe/repro/out/x.kicad_pcb --nets '*' '--layer-costs 1.0 1.5'` (warns, "Layer costs: F.Cu=1.0x, B.Cu=3.0x", exit 0).
- **Issues:** none found.

## 13. route_diff's GND return vias dangle on a 2-layer board whose F.Cu pour is not GND

- **True:** route_diff placed GND vias at the USB pair's layer changes (e.g. (141.85, 73.89), (142.81, 74.85));
  their F.Cu end lands in the +3V3 pour, so `check_weird` reports `dangling-via` ("same-net copper reaches it on
  B.Cu only") whenever no later route step welds them -- every chain that left GND out of a later step.
- **Repro:** `python3 -X utf8 py_router/check_weird.py wk/gpm/12_steppenprobe/repro/N2_s2a.kicad_pcb` (dangling-via 4).
- **Issues:** none found.

## 14. place_pose reports `legal: false` on a clean placement because the rounded outline is only sampled

- **True:** every measured channel 0; `pad_edge.complete` false ("outline uses sampled perimeter check", 306 pads); check_assembly buildable.
- **Repro:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/12_steppenprobe/repro/seed1_placed.kicad_pcb wk/gpm/12_steppenprobe/repro/out/pp.kicad_pcb set R16 139.6076 95.6985 --rot 270` (`"legal": false`).
- **Issues:** #1326 (CLOSED, "`legal` is unreachable on any non-rectangular outline") -- still reproduces at bda59fa0.

## 15. The skill's `kicad-cli` lines assume it is on PATH; on macOS it is not

- **True:** `kicad-cli: command not found` (127); binary at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`
  (repo tools find it themselves; only SKILL.md §3.9 / plan-pcb-routing 4c copy-paste lines fail).
- **Issues:** none specific (#420 is oracle speed).
