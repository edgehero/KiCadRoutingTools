# TOOL_GAPS -- fa10 board 06 (rp2350_fpga_eensy_prePlane)

All commands run from the worktree root `C:/Users/rob/Documents/prive/git/krt-fa10` in Git Bash with
`export MSYS2_ARG_CONV_EXCL='*'`. `D=wk/fa10/06_rp2350_fpga_eensy_prePlane`. Repro boards are in `$D/repro/`
(each copied with `py_router/copy_board.py`, so its `.kicad_pro` is beside it). `K="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"`.

Ranked by what each cost this run (time, and what shipped because of it).

---

## 1. route.py announces a 0.25 mm copper-to-hole floor, then ships 0.1425 mm; every repo checker reads it clean

**Cost:** ~25 min of measuring plus a time-boxed re-route experiment, and an unrecovered floor descent in the
shipped board (169 of 185 vias have other-net copper inside 0.25 mm of their hole).

- **Tools / commands:** every `py_router/route.py` step (and `bga_fanout.py`) of the chain, e.g.
  `route.py $D/r3/p3_fc.kicad_pcb ... --track-width 0.09 --clearance-ceiling 0.09 --via-size 0.25 --via-drill 0.15`;
  `py_router/route_planes.py` (the pour); `check_complete.py --authored-from`.
- **What they claimed:**
  - route.py and bga_fanout print, on every step:
    `Copper-to-hole clearance 0.25mm (from the floor the board ORIGINALLY declared, which a later step's writeback relaxed in the project, above the 0.2mm fab floor)`.
  - `check_drc`, `board_score` (`drc 0`), `check_complete` (DONE) and KiCad's DRC under the shipped project all read
    clean.
  - `check_complete --authored-from` names only one relaxed floor in its verdict line (`via annular ring 0.1 -> 0.05`);
    in its JSON, `min_hole_clearance` (authored 0.25) sits under `unmeasured`.
- **What was true:**
  - `route_planes.py` (the FIRST routing step) wrote `rules.min_hole_clearance: 0.25 -> 0.09` into the project
    (printed as "FAB FLOOR RELAXED"); nothing asked for it.
  - The router holds TRACKS off EXISTING holes at 0.25, but a via it places beside a track (or a track it lays beside a
    via placed in the same run) is held only at copper clearance 0.09 + the 0.05 annular ring.
  - KiCad 10 DRC on a copy whose project says the authored `min_hole_clearance 0.25`: **199 `hole_clearance`
    violations** (162 track-via, 26 via-via, 9 pad-via, 2 PTH-via), **minimum 0.1425 mm**. At the toolchain's own
    0.2 mm fab floor: still 199. At 0.15: 21.
  - The verifier counted 555 copper features within 0.25 mm of another net's hole (min 0.1425).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_drc.py $D/repro/r_final.kicad_pcb --clearance-margin 0.1        # NO DRC VIOLATIONS
  python3 -X utf8 check_complete.py $D/repro/r_final.kicad_pcb --intent $D/intent.json \
      --authored-from $D/rp2350_fpga_eensy_prePlane.kicad_pcb --json $D/repro/authored.json      # verdict names only the annular ring; min_hole_clearance under "unmeasured"
  python3 -X utf8 py_router/copy_board.py $D/repro/r_final.kicad_pcb $D/repro/hc025.kicad_pcb
  python3 -c "import json;p='$D/repro/hc025.kicad_pro';d=json.load(open(p));d['board']['design_settings']['rules']['min_hole_clearance']=0.25;json.dump(d,open(p,'w'),indent=2)"
  "$K" pcb drc --format json --severity-error --refill-zones -o $D/repro/hc025.json $D/repro/hc025.kicad_pcb   # 199 hole_clearance, min 0.1425 mm
  ```
- **Existing issues:** `gh issue list --search "copper-to-hole clearance writeback"` -> **#1038 (CLOSED)** is the same
  claim-vs-copper gap for NPTH holes (run 32); this run shows it for VIA holes. **#1198 (OPEN)** covers
  check_complete --authored-from calling hole floors "NOT measured". **#1160 (OPEN)** covers a writeback lowering a
  project floor that later steps then route to.

---

## 2. The container exemption hides a real KiCad DRC error, and over-counts the container everywhere else (U8 = Teensy40 frame)

**Cost:** the first DONE board (`r2/p7_clean`, 58 min) shipped 2 KiCad DRC **errors** that no repo checker saw; fixing
it cost a placement move plus a complete re-route chain (~25 min). The opposite half made `render_placement` useless
on this board, so I wrote `helpers/plot_sides.py`.

- **Tools:** `check_assembly.py`, `check_drc.py`, `board_score.py`, `check_complete.py` (miss it);
  `render_placement.py`, `check_floorplan.py --plan-only`, `place_seed` PLAN lines (over-count).
- **What they claimed:**
  - check_assembly `buildable (blocking 0)`; check_drc `NO DRC VIOLATIONS`; board_score blocking 0;
    check_complete DONE -- on `r2/p7_clean` and on its placement `b/s06_seed4`.
  - render_placement: `b_courtyard_blocking_pairs` = 60 pairs, every one `X <-> U8`, courtyard overlap 403.09 mm2,
    `b_body_overlap_pairs [["U6","U8"]]`; both the F and B panels painted solid orange (every part drawn as an overlap).
  - check_floorplan --plan-only / place_seed: `plan_board_crowded: the busiest face is 165% covered` and
    `plan_fixed_overlap: J1 and U8 ... overlap by 77.310mm2`.
- **What was true:**
  - KiCad 10 DRC: **2 `pth_inside_courtyard` errors**: U8 PTH pads 16 (+3V3) and 17 (GND) at y=121.515 (drill 1.1)
    inside SW1's courtyard (y 117.285..120.985). The exemption that keeps U8 out of courtyard checks also drops this pair.
    Moving SW1 0.335 mm north (`place_pose set SW1 147.8 118.8`) took KiCad's count 2 -> 0.
  - U8 has no courtyard; its pad-bbox fallback covers the board. Real front-side courtyard demand without U8 is ~321 mm2
    of ~479 mm2 interior (~64 %), not 165 %; J1/U8 do not overlap physically (U8 is a frame of edge pins).
- **Repro:**
  ```bash
  python3 -X utf8 py_tools/check_assembly.py $D/repro/r06_seed4.kicad_pcb --intent $D/intent.json   # buildable (blocking 0)
  "$K" pcb drc --format json --severity-error -o $D/repro/r06_kdrc.json $D/repro/r06_seed4.kicad_pcb  # 2 x pth_inside_courtyard (U8 pad 16/17 vs SW1)
  python3 -X utf8 py_tools/render_placement.py $D/repro/r06_seed4.kicad_pcb --json-out $D/repro/r06_render.json  # 60 courtyard pairs, all X<->U8
  python3 -X utf8 py_tools/check_floorplan.py $D/repro/r01_fixed.kicad_pcb --intent $D/intent.json --plan-only  # 165% crowded, J1/U8 77.31 mm2
  ```
- **Helper written:** `helpers/plot_sides.py` (per-side placement plot that draws the container as an outline only).
- **Existing issues:** `gh issue list --search "container footprint courtyard"` -> **#1184 (OPEN)**: the seeder exempts a
  container from every courtyard check while check_assembly gates it -- same exemption, different consumer. Nothing
  found for `pth_inside_courtyard` (`--search "pth_inside_courtyard"`: #856, #489, #487 are unrelated).

---

## 3. place_seed: "U6: no legal pose anywhere on the board" -- its pad layer sees a U6/U8 pad stack that does not exist

**Cost:** ~20 min (diagnosis, hand-seating U6), and `rank_rotations.py` could not rank the board's biggest IC (every arm
seats through the same seeder), so U6's rotation was ranked by hand with four extra seeds.

- **Tool / command:** `py_placer/place_seed.py $D/repro/r01_fixed.kicad_pcb OUT --intent $D/intent.json --seed 0 --force`
  (U8 and J1 placed and locked, everything else in the pile).
- **What it claimed:** exit 4, `place_seed: 1 part(s) UNSEATED ... U6`, `NOTE: U6: no legal pose anywhere on the board`,
  `no_pose_verdict {"U6": "no_single_lift_frees"}`.
- **What was true:**
  - `place_pose.py ... --dry-run --strict-legal set U6 148.5 103.5 --rot 0` on the same board: `no_worse true`; pad
    stacks 357 -> 322, pad conflicts 475 -> 427 (U6 leaving the pile only removed conflicts); the ranker even proposed
    (146.5, 103) as a nearest legal pose. Seated there by hand, the rest of the board seeded with 0 unseated.
  - The seeder's own predicate, asked directly (`helpers/diag_u6_seat.py`): every on-board pose at every rotation is
    refused by `candidate_veto = ('pads', 'U8')`; `legality_ctx.pair_shortfall(U6, U8)` at (148.5,103.5) =
    `PairShortfall(pad=13.63, pad_overlap=True, stack=True)` against a seed baseline of zero. U8's pads are only on the
    board edges (x <= 141.7 or >= 155.3, y >= 121.5), nowhere near U6's courtyard (144.4..152.6). U6 is the one part
    with drilled pads (QFN-60 EP thermal vias), and U8 is a drilled container; the seeder's pad model places one of
    them wrongly.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_seed.py $D/repro/r01_fixed.kicad_pcb $D/repro/out_seed.kicad_pcb --intent $D/intent.json --seed 0 --force   # exit 4, U6 unseated
  python3 -X utf8 py_placer/place_pose.py $D/repro/r01_fixed.kicad_pcb $D/repro/out_pose.kicad_pcb --dry-run set U6 148.5 103.5 --rot 0      # no_worse true
  python3 -X utf8 $D/helpers/diag_u6_seat.py $D/repro/r01_fixed.kicad_pcb $D/intent.json $D/repro/out_diag.kicad_pcb | grep -A2 DIAG       # ('pads','U8'), pad=13.63 stack=True
  ```
- **Helper written:** `helpers/diag_u6_seat.py` (wraps the seeder's `_try_place` and prints the refusing conjunct).
- **Existing issues:** `--search "no legal pose anywhere"` -> #1101, #982, #629, #1099 (all CLOSED, different causes);
  `--search "pair_shortfall container"`, `--search "drilled thermal vias seed"`: none. **New.**

---

## 4. bga_fanout (underpad) drops balls with free inner layers and no reason, suggests an impossible via, and leaves an inner ball neither tool connects

**Cost:** ~25 min (three fanout retries, a rotation sweep, a seed switch) plus two hand-written joins (`check_join.py`).

- **Tool / command:**
  `py_router/bga_fanout.py $D/repro/r_seed3_pour.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1 -1 1 1 -1 1 --track-width 0.09 --clearance 0.09 --via-size 0.25 --via-drill 0.15 --escape-method underpad --plane-net-layers GND:In1.Cu +3V3:In4.Cu --grid-step 0.05 --output OUT`
- **What it claimed:**
  - `escaped 27, failed 3, unescaped_nets [PIN.16, PIN.17, GPIOL_20_PLLIN]` and
    `Retry the fanout with a smaller --clearance (toward the manufacturing floor)`. Retrying at 0.075 (with
    `--fab-overrides` declaring the board's own 0.075 floor) and at 0.0889 gave the identical 3 drops; a second pass for
    the 3 nets alone with `--check-for-previous` escaped 0/3.
  - `Under-pad: WARNING via 0.25mm is large for 0.40mm pitch ... Try via <= 0.04mm.` (0.04 mm is not a via any fab
    makes; on another call `Try via <= 0.07mm`.)
  - On the kept placement (seed 4): `escaped 30/30` -- while also printing
    `1 extra ball(s) had no escape room; strapped 0 ... (1 left for the router): +1V1 ball C4`.
- **What was true:**
  - The dropped balls (B3, B4 on the east face, C6 on the south) had In3 and B.Cu completely free (the plot of the
    output shows only F.Cu and In2 copper); the engine prints no per-ball reason, so the only lever left was to move
    parts (seed 3 had U7 1 mm off U2's east face; seed 4 fanned out 30/30).
  - U2.C4 (+1V1, an inner ball) shipped with no copper and no via. route.py then failed it as
    `no rippable blockers`. A single F.Cu segment C4 -> D5 (its diagonal same-net neighbour, already via'd) of width
    0.09 has 23 um of slack past C5/D4 and `check_join.py` grades it **CLEAN**; neither the fanout's strap pass nor the
    router finds it (off-grid 45 degree path through a 0.283 mm half-gap on a 0.05 grid).
- **Repro:**
  ```bash
  python3 -X utf8 py_router/bga_fanout.py $D/repro/r_seed3_pour.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' --output $D/repro/out_fan.kicad_pcb --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1 -1 1 1 -1 1 --track-width 0.09 --clearance 0.09 --via-size 0.25 --via-drill 0.15 --escape-method underpad --plane-net-layers GND:In1.Cu +3V3:In4.Cu --grid-step 0.05   # failed 3, "Try via <= 0.04mm"
  python3 -X utf8 py_tools/check_join.py $D/repro/r_p3_fc.kicad_pcb '+1V1' 149.172,110.185,F.Cu 148.772,110.585,F.Cu --width 0.09   # CLEAN (the strap neither tool makes)
  ```
- **Existing issues:** `--search "under-pad drops"` -> **#1189 (OPEN)** (under-pad A* never tests its exit cell -- a
  different defect in the same engine); `--search "inner ball diagonal same net strap"` -> **#129 (CLOSED)** asked
  for same-net ball strapping (the strap pass exists and strapped 0 here). Nothing for the missing per-ball reason or
  the 0.04 mm suggestion. **New.**

---

## 5. A footprint's own rule area (J2 Tag-Connect keep-out) is not moved with the footprint

**Cost:** ~10 min plus `helpers/move_fp_zone.py`; without it the board would ship a keep-out over U1's pads and no
keep-out under J2's pogo pins.

- **Tools:** the pile maker that built the input, and the placement writer used by `place_pose.py` / `place_seed.py`.
- **What they claimed:** nothing -- the move is silent; place_pose/place_seed report the part moved and legal.
- **What was true:** J2 (TC2030-IDC-NL, B.Cu) owns a keep-out (vias not allowed, footprints not allowed). In every
  board of the run its polygon stayed at (147.23..149.77, 95.365..96.635) while J2 sat at (147.09, 136.33) in the
  pile, (150.07, 114.89) in seed 0 and (148.19, 115.31) in seed 4. The parser reads footprint keep-outs as board
  keep-outs (`board_info.keepouts`, `in_footprint: True`), so the router honoured the keep-out at the STALE place, over
  U1's B-side pads, and allowed vias between J2's real pads (a 0.25 via fits their 0.48 mm gap).
- **Repro:**
  ```bash
  python3 -X utf8 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as P;p=P('$D/repro/r06_seed4.kicad_pcb');f=p.footprints['J2'];print(f.x,f.y,[k['polygon'] for k in p.board_info.keepouts])"
  # -> 148.186 115.308 [[(147.23, 95.365), (149.77, 95.365), (149.77, 96.635), (147.23, 96.635)]]
  ```
- **Helper written:** `helpers/move_fp_zone.py` (re-centres the zone on J2's pad field after placement).
- **Existing issues:** `--search "keepout zone footprint stale position"`, `--search "footprint zone not transformed"`:
  none (#829 is about Edge.Cuts owned by a footprint). **New.**

---

## 6. route.py's `failed` headline reads 0 on a run that left two nets open

**Cost:** ~10 min: my chain helper trusted `failed` and stopped its rip loop early, so a whole optimisation round
under-ran and had to be repeated.

- **Tool / command:** the rip pass of `o1/base` (exact argv on line 1 of `$D/o1/base_r2.log`):
  `route.py $D/repro/r_base_r1.kicad_pcb OUT --nets '*' ... --rip-existing-nets 'Net-(J2-~{RESET})' /RP2354A/FPGA.MOSI ... --json-out OUT.json`
- **What it claimed:** `JSON_SUMMARY_MIN: {"failed": 0, ...}` and `--json-out` `"failed": 0`.
- **What was true:** the same JSON says `failed_single: ["/RP2354A/FPGA.~{RESET}"]`, `multipoint_deficit: 1`,
  `pad_pairs_open: {"count": 2, nets: [FPGA.~{RESET}, PIN.9]}`; board_score on its successor graded broken 2.
- **Repro:** run the argv on line 1 of `$D/o1/base_r2.log` with the input path replaced by
  `$D/repro/r_base_r1.kicad_pcb`, then
  `python3 -c "import json;d=json.load(open('OUT.json'));print(d['failed'],d['failed_single'],d['pad_pairs_open'])"`.
- **Existing issues:** `--search "failed 0 failed_single"` -> #1069 (CLOSED, json-out dropping broken nets from earlier
  laps -- related, not the same field). **New.**

---

## 6b. route.py --routing-clearance-margin is documented as a track-via clearance multiplier and does nothing to single-ended routing

**Cost:** ~10 min (one 2-arm experiment aimed at gap 1: hold tracks 1.7 x further from vias so copper-to-hole clears
the 0.2 mm fab floor).

- **What it claimed:** `route.py --help`: `--routing-clearance-margin  Multiplier on track-via clearance (1.0 = minimum DRC)`;
  the run's CMD line shows `--routing-clearance-margin 1.7` was received.
- **What was true:** with the flag at 1.7 the routed copper is identical to the 1.0 run -- same 1070 segment endpoints
  and the same via set (`r3/basenj_r1` vs `r3/hm17nj_r1`), and identical scores (185 vias / 986.91 mm and 176 / 987.09
  for the joined pair). In `py_router/`, `config.routing_clearance_margin` is read only by `diff_pair_routing.py`; no
  single-ended path consumes it.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route.py $D/repro/r_p3_fc.kicad_pcb $D/repro/m10.kicad_pcb --nets '*' --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1 4 1 1 4 1 --track-width 0.09 --clearance-ceiling 0.09 --via-size 0.25 --via-drill 0.15 --grid-step 0.05
  python3 -X utf8 py_router/route.py $D/repro/r_p3_fc.kicad_pcb $D/repro/m17.kicad_pcb --nets '*' --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1 4 1 1 4 1 --track-width 0.09 --clearance-ceiling 0.09 --via-size 0.25 --via-drill 0.15 --grid-step 0.05 --routing-clearance-margin 1.7
  # compare sorted segment endpoints and via positions of m10 vs m17: identical
  grep -rn "routing_clearance_margin" py_router/*.py
  ```
- **Existing issues:** `--search "routing-clearance-margin"`: none relevant. **New.**

---

## 7. Reaching DONE takes three route.py runs by hand (route.py prints, but does not apply, its own rip hint; a hand-completed net keeps removable copper)

**Cost:** ~10 min plus `helpers/route_chain.sh`.

- **What happened:** pass 1 left `Net-(U2-GPIOR_35_CSO)` boxed in by fanout copper and printed the exact
  `--rip-existing-nets '<9 nets>'` to use; pass 2 with it routed the net; after the hand join on +1V1,
  `check_complete` said INCOMPLETE (`orphan_stubs: 1 layer`, `weird_copper: removable-segment 5` on +1V1, copper the
  earlier passes left while the net was open); only a third `route.py --nets '*'` pass cleaned it to DONE.
- **Repro:** `bash $D/helpers/route_chain.sh $D/repro/r_p3_fc.kicad_pcb $D/repro/chain` runs the three steps and prints
  each pass's files (`chain_r1.log` carries the hint; `chain_c.kicad_pcb` is the cleaned board).
- **Helper written:** `helpers/route_chain.sh`.
- **Existing issues:** the hint is #103's mechanism (by design opt-in). Nothing found for the leftover removable copper
  on a hand-completed net. Low severity.

---

## 8. check_weird / check_orphan_stubs say clean; KiCad flags two dangling stubs

**Cost:** none to the run (found by the verifier); listed because a tool said "clean" about something that was not.

- **What they claimed:** `check_weird`: `NO WEIRD THINGS FOUND!` (dangling-end 0); `check_orphan_stubs`: `NO ORPHAN STUBS FOUND!`
- **What was true:** KiCad 10 DRC (warnings) on the final board: 2 `track_dangling` -- GND F.Cu 0.0354 mm at
  (151.05, 97.525) and +3V3 F.Cu 0.0236 mm at (143.033, 100.667).
- **Repro:** `"$K" pcb drc --format json --severity-warning --refill-zones -o $D/repro/w.json $D/repro/r_final.kicad_pcb`
  then count `track_dangling`; `python3 -X utf8 py_router/check_weird.py $D/repro/r_final.kicad_pcb`.
- **Existing issues:** `--search "track_dangling stub"`: none relevant (#483, #530). **New** (minor).

---

## 9. place_seed refuses a pile once the fixed parts are placed and locked -- the order the skill prescribes

**Cost:** ~3 min (`--force` works and keeps the locked parts).

- **What it claimed:** exit 3, `place_seed: this board already looks PLACED`.
- **What was true:** `board_brief` on the same board: `"pile": true, "unplaced": false`; 59 of 61 parts in the pile.
- **Repro:** `python3 -X utf8 py_placer/place_seed.py $D/repro/r01_fixed.kicad_pcb $D/repro/out_refuse.kicad_pcb --intent $D/intent.json --seed 0` -> exit 3.
- **Existing issues:** **#1165 (OPEN)** -- exactly this.

---

## 10. measure.py cannot find a subagent session's transcript

**Cost:** ~5 min.

- **What it claimed:** `measure.py --root .` -> `refuse: no transcript under ...\C--Users-rob-Documents-prive-git-krt-fa10`;
  pointed at the launching checkout it measured the ORCHESTRATOR's 2-day transcript, not this run.
- **What was true:** this run's transcript is `.../C--Users-rob-Documents-prive-git-KiCadRoutingTools/<parent>/subagents/agent-a3e971d5ca668a482.jsonl`; passed explicitly it measures 1h36m at the time of the call.
- **Existing issues:** **#1177 (OPEN)** -- exactly this.
