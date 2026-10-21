# gp14 -- clustered candidate findings (pin 8328f157)

Consolidation only: nothing below was re-run or verified. Every number is quoted from a
teammate's `TOOL_GAPS.md`, from `FINDINGS_PREP.md` (PREP) or from `GRADE_NOTES.md` (GRADE).
"NN #k" is board NN's TOOL_GAPS entry k.

**Sources read** (mtime): the 14 `NN_*/TOOL_GAPS.md` (01 .. 14), `FINDINGS_PREP.md` (Oct 21 02:26),
`GRADE_NOTES.md` (Oct 21 02:43). **Board 12 was rewritten while this was compiled**: the version
used is the one saved Oct 21 02:50:07 (12 entries). It inserted two entries (#2 netclass width,
#3 power neck-down), so its later entries moved down by two against the 22:41 version. Re-check
board 12's numbers if the file changes again.

**Repro commands** are copied verbatim. They run from the worktree root
`~/Documents/git/krt-gp14` with `export PATH="$HOME/.venvs/krt/bin:$PATH"`. Where a command
uses a variable, the line that defines it in the board's file is given above it.

**Severity rule used:**
- **HIGH**: blocked or voided a board or round, damaged copper or geometry, or a tool's "fine" was
  false and only KiCad, the verifier or a hand check caught it.
- **MEDIUM**: cost real time and needed a workaround, or gave a false or misleading message that the
  skill's own later checks (board_score / check_complete / check_drc) caught.
- **LOW**: cosmetic, docs, skill text, output noise.

Within a severity, clusters are ordered by the number of boards that hit them.

**Upstream search**: `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --limit 10 --search ...`,
read-only. Teammates' own results are quoted per cluster. Issues I found that they did not list
are marked "(my search)". My searches: place_pose rotate / rotate absolute relative,
converge record quick_score, ungraded_set, declared pose castellated, fixed_poses illegal judge,
stacked copper duplicate, kicad_dru length rule, length_out_of_range, redo_record environment,
redo manifest env, multi-layer zone replace, pad locked rotate writer, strict collapse (+ mixed
dialect), NOT FULLY GRADED exit 4, check_floorplan exit code, movie3d (+ box model), apart hint,
improvement gate DRC, quick 2 plane fragility, quick_score floorplan, courtyard overlap floors KiCad,
local clearance margin check_drc, route_diff coupled skew, single_ended_diff_pairs,
kicad_drc_compare (+ baseline), board_score weird copper, rip-existing-nets already connected,
manifest_to_plan relative path, bga_fanout check-for-previous, route_bus, via-in-pad length graph,
edge seat no room, classify_part, check_impedance zone split, repair-decaps, decap limit tether
radius, halo back face BGA, proximity claim, list_nets design-rules via, allow-unplaced,
board_brief pile, check_reachability CAGED, check_assembly min_clearance, write-fill, silkscreen
skill, mechanical.json kind, ortools, check_pads overlapping, route_plan_check, container frame,
accept_courtyard_overlap, SCORE_JSON quiet, route_review turn, fanout-dropped,
footprint_has_through_pads, place_simple, track_dangling, judge.json, marker_class, min_via_drill,
zone settings replaced, board_context pin-order, pad_pairs_open, overhang margin edge clearance,
qfn_fanout single pad, qfn_fanout stub, GIF size film, net_widths netclass, board_score net widths,
power netclass track width, decoupling owner resistor array, judge chain runner seeds.

---

## Summary

| id | title | severity | #boards |
|---|---|---|---|
| H01 | route.py: redundant micro-segments, off-grid T-stubs and dangling tails (KiCad track_dangling) that nothing removes, so check_complete refuses DONE | HIGH | 7 |
| H02 | Seed judge (quick_score + judge.json) is blind to error-graded floorplan findings (decap limits) that DONE counts | HIGH | 5 |
| H03 | route.py ships stacked same-net duplicate segments; the in-run finalize lays them after its own census | HIGH | 5 |
| H04 | place_simple: declared-pose check refuses legitimate declared poses (castellated holes, round pads by bbox, shared-origin modules), so every seed is illegal and judge.json is empty | HIGH | 3 |
| H05 | check_assembly gates courtyard overlaps the intent itself declares (pile baseline, lock disables marker waiver, accept_courtyard_overlap unread) | HIGH | 3 |
| H06 | route_planes stacks new zones over a multi-layer same-net zone instead of replacing it; check_impedance reads the overlap as plane splits | HIGH | 3 |
| H07 | place_simple prices courtyard-less parts by pad box, check_assembly by drawn body: every judged seed NOT BUILDABLE, no repair tool | HIGH | 2 |
| H08 | Edge-connector overhang band graded in a currency the router rewrites: a passing placement fails floorplan after routing with nothing moved | HIGH | 2 |
| H09 | redo_record drops env-knob prefixes: redo_commands.sh does not replay the shipped board | HIGH | 2 |
| H10 | Diff pairs: route_diff "coupled"/"matched" ignores terminal legs, falls back to single-ended silently; no DONE grader checks routed pairs | HIGH | 2 |
| H11 | check_assembly's courtyard floors pass overlaps the project calls errors and KiCad reports | HIGH | 2 |
| H12 | A declared netclass track width is graded nowhere (net_widths UNGRADED -> DONE); explicit --track-width overrides it | HIGH | 2 |
| H13 | Placement writer never rotates pads carrying the KiCad-6 `locked` token (the given pile is already damaged) | HIGH | 1 |
| H14 | No placement grade sees a footprint whose own pads overlap (only check_pads, which no skill runs) | HIGH | 1 |
| H15 | place_simple anneal counts a courtyard-less pin-frame container as a whole-board overlap body: 0/12 legal seeds | HIGH | 1 |
| H16 | place_simple anneal blocks the whole far face under an SMD part with one drilled peg: 12/12 seeds exit 4 | HIGH | 1 |
| H17 | route.py's in-run GND plane repair rips a fully routed 17-pad rail and ships it with no copper; pad_pairs_open omits it | HIGH | 1 |
| H18 | route.py's improvement gate accepts an all-nets pass that adds 17 DRC violations (shorts) | HIGH | 1 |
| H19 | route.py strips BGA dog-bone escapes it cannot restore, then its hint blames the fanout | HIGH | 1 |
| H20 | route.py's end-of-run strict collapse reports 291 removals and writes none (mixed-dialect file) | HIGH | 1 |
| H21 | No tool grades or honours a .kicad_dru length window; route_bus and the default chain break it | HIGH | 1 |
| H22 | board_score's length component cannot see a via-in-pad join: a connected group reads UNGRADED | HIGH | 1 |
| H23 | bga_fanout --check-for-previous lays escapes over existing foreign-net tracks (KiCad short) | HIGH | 1 |
| H24 | route_bus writes its output without the board's .kicad_dru and design-brief siblings | HIGH | 1 |
| H25 | check_drc's default relative margin passes tracks under a footprint's local clearance that KiCad rejects | HIGH | 1 |
| H26 | route.py necks power nets to 0.15 mm at 0.5 mm-pitch pins, and no flag stops it without breaking the net | HIGH | 1 |
| M01 | Steps that lay no copper (bare pour) rewrite the project's authored floors; route.py then calls the invented value "original" | MEDIUM | 7 |
| M02 | place_simple leaves error-graded decap limits broken; no decap repair CLI on the branch | MEDIUM | 6 |
| M03 | Skill: no path when a round yields no usable seed; silent on whether re-placements count toward --rounds | MEDIUM | 6 |
| M04 | The `--quick 2` judge does not predict the full route (vias, blocking) | MEDIUM | 4 |
| M05 | place_pose `rotate` is absolute and pivots on the origin; route_review "turn 180" + skill text mislead; false "Modified 1 footprint positions" | MEDIUM | 4 |
| M06 | converge.py record refuses the first board_score row after quick_score rows ("graded FEWER components") | MEDIUM | 4 |
| M07 | `--rip-existing-nets` on a connected net is a no-op, yet route.py's Hint prescribes it | MEDIUM | 4 |
| M08 | place_simple edge seat says "no room along the edge" for connectors that fit, places them in the interior | MEDIUM | 3 |
| M09 | place_pose `legal` is false on every pose of boards with on-outline copper or a slightly non-rectangular outline | MEDIUM | 3 |
| M10 | check_floorplan exits 4 ("pass": false) on a finished board with 0 errors | MEDIUM | 3 |
| M11 | No tool runs the skill's seed-judging chain; boards hand-write judge_chain.sh | MEDIUM | 3 |
| M12 | Default chain (escalation fab / tier auto / descents) spends authored floors it did not need; --clearance-ceiling bounds neither descents nor qfn_fanout | MEDIUM | 3 |
| M13 | board_score and check_orphan_stubs say clean on boards check_complete refuses for weird copper | MEDIUM | 3 |
| M14 | route_planes replaces a designer zone's settings (solid pads, 0.1 min thickness) and only says "with new parameters" | MEDIUM | 2 |
| M15 | place_simple `apart`/`edge`/`near` hints saturate to a constant when groups touch | MEDIUM | 2 |
| M16 | Edge-part classification: declared `class` ignored; DC jack, slide switch, HDMI, RJ45 unclassified | MEDIUM | 2 |
| M17 | qfn_fanout stubs end as dangling copper after routing (plane-net stubs; stub past a same-net pad) | MEDIUM | 2 |
| M18 | kicad_drc_compare --baseline misreports boards placed from a pile | MEDIUM | 2 |
| M19 | KiCad-only DRC items no repo checker grades: connection_width, starved_thermal | MEDIUM | 2 |
| M20 | Skills ship the pour unfilled: KiCad opens the DONE board with unconnected items | MEDIUM | 2 |
| M21 | Routing skill's 2-layer recipe: default via/layer costs on THT boards, vias in SMD pads | MEDIUM | 2 |
| M22 | `--quick 2` skips the plane finalize, so judge-time tools count poured-net pads open | MEDIUM | 2 |
| M23 | manifest_to_plan rejects an existing relative intent path, prunes upstream steps, reports "1 skipped" | MEDIUM | 2 |
| M24 | Board Setup min_clearance above the Default class is ignored by check_assembly/place_pose and by the --clearance-ceiling spelling | MEDIUM | 1 |
| M25 | route.py's end-of-run re-grade reports failed 0 while the exact fill has GND in 5 pieces | MEDIUM | 1 |
| M26 | board_score `blocking` ties a 17-pad rail with no copper with one stranded pad | MEDIUM | 1 |
| M27 | route_diff's GND return vias break the hole-to-hole floor even with --hole-to-hole-clearance | MEDIUM | 1 |
| M28 | qfn_fanout escapes single-pad (no-connect) nets | MEDIUM | 1 |
| M29 | place_simple lets back-face parts pile under a front-face BGA (halo prices own face only) | MEDIUM | 1 |
| M30 | place_simple objective blind to warning-graded claims (crystal) and ESD diode placement | MEDIUM | 1 |
| M31 | Skill's proximity-claim form is unsatisfiable on a many-pad part (claims GND pads too) | MEDIUM | 1 |
| M32 | route_plan_check R14 refuses the routing skill's own Step 8 pour-last chain | MEDIUM | 1 |
| M33 | check_reachability calls congestion "CAGED" on a routed board | MEDIUM | 1 |
| M34 | route_bus hands on a caged ball and lane copper on the GND plane layer | MEDIUM | 1 |
| M35 | list_nets --design-rules suggests a via whose drill exceeds its diameter | MEDIUM | 1 |
| M36 | mechanical.json carrying `"kind"` is refused (check_floorplan exit 2) | MEDIUM | prep |
| L01 | movie3d draws boxes where kicad-cli's iso render has the model | LOW | 8 |
| L02 | Decap owner election picks non-IC owners (resistor array, RGB LED) | LOW | 2 |
| L03 | Output volume: board_score --quiet 21 kB, place_pose on a pile ~280 KB | LOW | 2 |
| L04 | Pile-blind pose claims in board_brief and board_context --md | LOW | 2 |
| L05 | Film GIFs over 3 MB | LOW | 2 |
| L06 | `--allow-unplaced`: render_placement names a flag it lacks; board_score on a pile does not pass it | LOW | 1 + prep |
| L07 | movie3d tools not registered with manifest_to_plan: parity tests fail at branch head | LOW | prep |
| L08 | ortools missing from requirements.txt | LOW | prep |
| L09 | Silkscreen graded by no step of the skills; DONE board carries 4 KiCad silk errors | LOW | 1 |
| L10 | Intent rows spell their free-text reason two ways (`why` vs `note`) | LOW | 1 |
| L11 | Routing skill's fanout predicate sends an LQFP-48 to qfn_fanout, which hurt | LOW | 1 |
| L12 | Step 2d all-nets iterations were byte-identical no-ops | LOW | 1 |
| L13 | Skill's DENSE layer price vector vs declared impedance (reference-plane continuity) | LOW | 1 |
| L14 | Skill says to lock hand joins; check_join stages but no tool stamps the lock | LOW | 1 |

---

## HIGH

### H01 -- route.py: redundant micro-segments, off-grid T-junction stubs and dangling tails (KiCad `track_dangling`) that no repo actor removes, so check_complete refuses DONE

- **Boards (7):** 03_complex_hierarchy #1; 04_multichannel_mixer #4 (dangling-end half);
  06_rp2350_fpga_eensy_prePlane #4 (+ #9, checker half); 07_One-Air-Max #3 (kicad-dangling at
  via-cost >= 375); 08_CM5_MINIMA_3 #3 (micro-segments + dangling tails); 11_daplink #6;
  14_imx6ulz_4l #3 (hygiene half: KiCad-dangling slivers).
- **Defect:** route.py writes same-net segments 0.011-0.075 mm long whose ends both lie on other
  same-net track (check_weird `kicad-dangling`, KiCad `track_dangling`), off-grid T-junction stubs, and
  longer dangling-end tails. Its cleanup ("Strict collapse (#1063)", dead-end sweep, dangle trim), extra
  `--nets '*'` passes and `--rip-existing-nets` leave them, and check_complete then reads INCOMPLETE
  (weird_copper). Clearest measurement (03): net /ampli_ht_horizontal/S_OUT+ carries a 0.0381 mm-long,
  0.4 mm-wide F.Cu segment (115.600, 81.773)-(115.627, 81.800). Its start is 27 um off the 0.1 grid. The
  same stub appeared on 7 of 8 boards routed at grid 0.1 and on none of the 2 routed at 0.05, and
  `--force-reroute` at 0.1 laid it again. Root cause matches #1291:
  `py_router/single_ended_routing.py` ~l.4707 still reads `num_steps = max(1, int(length / coord.grid_step))`.
  #1291's fix is not on 8328f157. 06: 1-3 power-width segments 0.011-0.025 mm long survived a closing pass,
  a rip pass and eleven route variants. Variants: 04 a 3.677 mm /CH1/OUT dangling end on every route
  of that placement at via cost 75-135; 08 ETH TRD2 P/N tails 0.424 mm past their via anchor.
  Checker half (06 #9): check_weird abstains (its #1217 rule) on a 0.1 mm GND stub at (154.1, 91.4)-(154.1, 91.5)
  that KiCad flags `track_dangling`, because a via, pad or zone touches it.
- **Repro** (03 #1):
  ```bash
  python3 -X utf8 py_router/route.py wk/gp14/03_complex_hierarchy/repro/gap1_placed.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb --nets '*' --clearance-ceiling 0.3 --via-size 0.889 --via-drill 0.508 --power-nets GND HT VCC '*VAA' /12Vext --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --via-cost 600 --direction-preference-cost 0 --layer-costs 1.0 1.0
  python3 -X utf8 py_tools/board_score.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb      # BLOCKING=0
  python3 -X utf8 py_router/check_weird.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb     # kicad-dangling: 1
  python3 -X utf8 check_complete.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb            # INCOMPLETE -- weird_copper
  ```
  (`repro/gap1_kicad_drc.json` is KiCad's report on that output.)
- **Cost / "fine":**
  - 03: ~10 min and two extra chain runs.
  - 04: one more final chain plus a cleanup step.
  - 06: a helper and 11 route variants.
  - 07: the 4-8 extra vias found by the via-cost 375-1000 variants could not ship.
  - 08: part of ~15 min plus a helper.
  - 11: ~5 min, arm B rejected.
  - 14: part of ~25 min plus a helper.
  - Tools said fine: route.py `JSON_SUMMARY_MIN failed 0`, `board_score BLOCKING=0`, and
    check_orphan_stubs "NO ORPHAN STUBS FOUND!" (04).
- **Workarounds:**
  - 06 `helpers/drop_kicad_dangling.py`: deletes only kicad-dangling segments of 0.05 mm or less.
  - 08 `helpers/clean_copper.py`: trims named tails and drops named micro-segments.
  - 14 `helpers/strict_collapse.py`: hygiene pass.
  - 03: forced re-route of the one net at `--grid-step 0.05`.
  - 04: `--force-reroute` of the nets check_weird names, with GND in `--nets`.
- **Upstream:**
  - #1291 CLOSED: the cause; the fix is not on the branch (03, 06).
  - #1234 OPEN: route.py leaves chains of 0.025-0.075 mm segments and nothing reports them (03, 06).
  - #162 OPEN: same-net redundant copper, delete-only (06, 11).
  - #1217 CLOSED: check_weird learned this shape (03, 06, 11).
  - #1186 CLOSED: the opposite direction (04).
  - (my search) #1294 CLOSED, plane-finalize sub-runs weld sub-cell tracks onto forbidden layers:
    possibly related, not checked.
- **Severity / category:** HIGH: it blocks DONE wherever it appears, while route.py and board_score say
  clean. Routing tool. See M13 for the grader side.

### H02 -- Seed judge (quick_score + place_simple's judge.json) is blind to error-graded floorplan findings (decap limits) that DONE counts as blocking

- **Boards (5):** 05_interf_u #1; 09_StickHub #2 (judge half); 12_steppenprobe #8; 13_pico_ice_rev3 #1
  (+ #6 bullet 2); 14_imx6ulz_4l #6 (judge half) + #14 bullet 4.
- **Defect:** place_simple reports broken error-graded decap limits only in its `--json` (`decap_broken`).
  It still marks the seed legal and names it in judge.json (05: cheapest first). quick_score's `blocking`
  is the route tally only, while board_score `--intent` counts every floorplan ERROR in `blocking`. So the
  skill's "keep the best by blocking" and its stop rule ("blocking 0 -> stop") can rank, keep and stop
  on placements that cannot reach DONE.
  - 13: every judged seed of all 6 rounds broke the limits (r1 4-20, r2 2-12, r3 4-8, r4 3-15, r5 4-8,
    r6 2-7). The judge picked r1/s6, with 8 floorplan errors, over seeds with 4.
  - 05: s8 was judged first (final.cost 5329.5, quick_score blocking 1, 107 vias). Its U9 pins D11, G12
    and L10 sit 39.01, 41.19 and 37.23 mm from a cap against a 34.08 limit, so it could never be DONE.
  - 12: all 6 judged r2 seeds broke 1-4 limits.
  - 14: a pin 22.34 mm from its only cap (limit 8.46) is priced at 5.0.
- **Repro** (05 #1):
  ```bash
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent.json   # 3 x [ERROR] decap_pin_distance
  cat wk/gp14/05_interf_u/repro/r1_judge.json                                                                                         # "judge": [8, ...]
  python3 -X utf8 py_tools/quick_score.py wk/gp14/05_interf_u/repro/r1_s8_fast.kicad_pcb --route wk/gp14/05_interf_u/repro/r1_s8_route.json   # blocking=1, no floorplan term
  ```
  13 #1 also:
  `python3 -X utf8 py_tools/board_score.py wk/gp14/13_pico_ice_rev3/repro/r1_s6.kicad_pcb --intent wk/gp14/13_pico_ice_rev3/repro/intent_rows.json --baseline wk/gp14/13_pico_ice_rev3/repro/r1_fixed.kicad_pcb --quiet`
  (`floorplan=8` in BLOCKING).
- **Cost / "fine":**
  - 05: a whole review round (r2).
  - 13: the highest cost of its run; every kept placement needed a hand decap pass.
  - 14: the first full route failed DONE on floorplan 1.
  - 12: small.
  - Tools said fine: place_simple `illegal: []`, exit 0; quick_score's blocking.
- **Upstream:** teammates found none. 05 lists nearest #1099 and #1258; 13 lists #1188, #1150, #1067, #1043
  and #1102 (all closed, none about the judge). (my search) "quick_score floorplan", "judge.json": nothing.
- **Severity / category:** HIGH: the ranking is silently wrong. Grader/checker (+ skill text). Related:
  M02 (the placer cannot meet the limits), M03 (the skill has no step for it).

### H03 -- route.py ships stacked same-net duplicate segments (despite its own warning; the in-run plane finalize lays them after the census)

- **Boards (5):** 04 #4 (two stacked GND segments inside a via); 07 #3; 08 #3; 12 #7; 14 #3 (63 exact
  same-net duplicates in the hygiene half).
- **Defect:** route.py writes exact duplicate same-net segments: same endpoints, sometimes different
  widths (0.3 over 0.127), once a triple. check_weird flags them `stacked-copper`, check_complete then
  reads INCOMPLETE, and no repo tool removes them.
  - 08 and 12: route.py prints `WARNING: N stacked-copper finding(s) on the write model (same-net
    duplicates KiCad will not flag)` and writes them anyway.
  - 07: route.json has no `stacked_copper` key and the log no warning, because the census
    (`stacked_copper_over_model`, route.py ~l.4397) runs before the in-run plane finalize that lays
    them.
  - Counts: 07 23 exact pairs on GND/B.Cu; 08 60-87 per run (85 removed from the final); 12 23 on
    GND/+3V3 F.Cu; 14 63 on +3V3/GND.
- **Repro** (07 #3, producer known):
  ```
  python3 -X utf8 py_router/check_weird.py wk/gp14/07_One-Air-Max/repro/gap3_route_out.kicad_pcb     # FOUND 9 WEIRD THINGS: stacked-copper 9
  # (route input: repro/gap3_route_in.kicad_pcb; the exact route.py argv is the 5th/6th/7th line group of
  #  wk/gp14/07_One-Air-Max/final_route/redo_commands.sh)
  ```
  08 #3:
  ```bash
  python3 -X utf8 py_router/check_weird.py wk/gp14/08_CM5_MINIMA_3/repro/gap_weird.kicad_pcb    # 52 weird things
  python3 -X utf8 check_complete.py wk/gp14/08_CM5_MINIMA_3/repro/gap_weird.kicad_pcb            # INCOMPLETE (weird_copper, orphan_stubs)
  ```
- **Cost / "fine":**
  - 07: ~6 min, and the lower-via variants could not ship.
  - 08: ~15 min, plus re-verifying the helper's output on every candidate.
  - 12: a helper.
  - 04 and 14: part of a chain and of ~25 min.
  - Tool said fine: route.py `failed 0`; on 07 nothing disclosed it at all.
- **Workarounds:**
  - `helpers/dedupe_segments.py` (07, 12): drops a segment only when another of the same net and
    layer has the same endpoints, keeping the widest.
  - `helpers/clean_copper.py` (08) and `helpers/strict_collapse.py` (14).
  - GRADE notes that 07's dedupe_segments.py is **not** in redo_commands.sh, so a manifest replay does
    not reproduce its final. 08's helpers are recorded only as commented non-repo steps.
- **Upstream:** #162 OPEN, find the producers and remove delete-only (08, 12, 14). #606 CLOSED, the trim
  pass, which "did not stop it here" (08, 12). #1063 CLOSED (08, 12). 07 searched "stacked copper
  finalize duplicate": nothing; the finalize-after-census ordering is not mentioned.
- **Severity / category:** HIGH: it blocks DONE until a hand-written helper runs. Routing tool.

### H04 -- place_simple: the declared-pose check (`placement.seeder._fixed_pose_check`) refuses legitimate declared poses, so every seed is "illegal" and judge.json is empty

- **Boards (3):** 06 #2 (+ #7); 08 #2 (+ #9 bullet 1); 10 #1.
- **Defect:** the check grades declared parts by bounding boxes, without the exemptions check_assembly
  applies:
  - (a) Castellated half-holes centred on the outline count as "drill hole(s) past the outline". 06 U8
    (Teensy frame): "33 of 66". The pad-copper test exempts castellated pads; the hole test does not.
  - (b) Round pads are graded by their bounding square. 10 MK1: "pad copper 0.950mm past the outline"
    at a rounded corner. 08 H102-H105: ~2.17 mm, although each 5.4 mm round pad sits 0.4 mm inside the
    ear arc. 10 FID1: "pad clearance to MK1 short by 0.250mm", where the true copper gap is 0.842 mm
    against 0.375 required; the 0.25 mm is the gap between the two bounding squares.
  - (c) 08 Module301/Module302, one CM5 drawn as two footprints sharing an origin: "courtyard overlaps
    Module302 by 0.00x22.80mm (14.580mm2)". The rects include the shared NPTH holes; the B.CrtYd
    rectangles do not overlap.

  A declared part cannot move, yet it is counted as each seed's illegal part. So one refused declared
  pose disqualifies all 12 seeds and `--round` writes `"judge": []`. check_assembly on the same poses
  says "on the outline by design, not gated" and buildable.
- **Repro** (08 #2, shows the contrast):
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s0.kicad_pcb --groups wk/gp14/08_CM5_MINIMA_3/repro/gap1_groups.json --intent wk/gp14/08_CM5_MINIMA_3/repro/gap1_intent.json --seed 0
  # -> WARNING ... H102..H105 "pad copper ~2.17mm past the outline", Module301/302 courtyard overlap; no legal pose for ...; exit 4
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s0.kicad_pcb --baseline wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb | grep "by design"
  ```
  Castellated case (06 #2; `R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`):
  `python3 -X utf8 py_placer/place_simple.py $R/input.kicad_pcb $R/gap1_s0.kicad_pcb --groups $R/groups.json --intent $R/intent.json --seed 0 --moves 3000`
- **Cost / "fine":**
  - 08: a whole aborted round (`r1_aborted/`, 12 seeds) plus ~20 min.
  - 10: round 1 judged by hand, and the lock workaround that then hit H05.
  - 06: round 1 produced nothing judgeable (together with H15).
  - check_assembly, check_floorplan and render_placement all accept the same poses.
- **Workarounds:** KiCad-lock the parts at their mechanical.json poses with `place_pose ... set ... lock`
  and drop them from `fixed_poses[]` (06 `intent_u8lock.json`/`intent_frame.json`; 08 `intent_cm5.json`;
  10 `intent_v2.json`), plus `overlap_waivers` (08, 10).
- **Upstream:** none found. 06 lists #1257 and #324 (closed, different); 08 lists #1060 and #1152 (closed,
  different); 10 found none. (my search) "declared pose castellated" returns #1257 only; "fixed_poses
  illegal judge" returns nothing.
- **Severity / category:** HIGH: it blocked whole rounds. Placement tool. Skill side in M03 (SKILL 3.1/3.5
  "a pose the intent declares in `fixed_poses[]` needs no lock").

### H05 -- check_assembly gates courtyard overlaps the intent itself declares (pile baseline makes declared parts "moved"; a lock disables the marker waiver; `fixed_poses[].accept_courtyard_overlap` is not read)

- **Boards (3):** 10 #4 + PREP #7 + GRADE; 08 (PREP #7, GRADE; workaround in 08 #2); 07 #5 + GRADE.
- **Defect:** with `--baseline <input pile>` every part counts as moved, so `courtyard_blocking_gating`
  fires on pairs whose poses both come from mechanical.json and that the human board carries identically:
  - glasgow J5<->MK2, 4.0669 mm2;
  - CM5 Module301<->Module302, 14.58 mm2, and H102<->J1, 4.62 mm2 (human board: 14.58 / 4.64).

  The lead's re-grade on the GIVEN intent: 07 and 08 done false (NOT BUILDABLE); 10 blocking +1. Two
  more channels have the same effect:
  - (10 #4) KiCad-locking FID1-6 and MK1-4 at their declared poses, as SKILL 3.1 and part-roles.md
    prescribe, disables the marker_class waiver: 6 gating FID/MK pairs (FID1<->MK1 2.0554 mm2), NOT
    BUILDABLE. Unlocked, the same poses read `waived:marker_class`, buildable.
  - (07 #5) `fixed_poses[].accept_courtyard_overlap` is honoured by place_simple and check_floorplan,
    but check_assembly reads only `overlap_waivers[]`, so BAT1<->DC1 (38.7 mm2) and BAT1<->PWR_SW1
    (16.6 mm2) gate.

  Caveat (GRADE): on 07 the overlapping poses are the teammate's own `derived_default` choice, not
  mechanical.json. BAT1 draws no courtyard, so its occupancy falls back to the pad box. That makes 07
  the weaker instance.
- **Repro** (PREP #7):
  `py_tools/check_assembly.py wk/gp14/10_glasgow_revC/final.kicad_pcb --intent wk/gp14/10_glasgow_revC/intent.json --baseline wk/gp14/10_glasgow_revC/glasgow_revC.kicad_pcb`
  -> NOT BUILDABLE; same on `_truth/glasgow_revC/human_stripped.kicad_pcb` without --baseline -> buildable
  with the same pair listed.
  Lock channel (10 #4):
  `python3 -X utf8 py_tools/check_assembly.py wk/gp14/10_glasgow_revC/repro/gap4_kept_locked.kicad_pcb --intent wk/gp14/10_glasgow_revC/repro/gap4_intent_v3.json --baseline wk/gp14/10_glasgow_revC/repro/input_pile.kicad_pcb`
  (NOT BUILDABLE, 6 gating FID/MK pairs) against the same with `repro/gap4_kept_unlocked.kicad_pcb` (buildable).
- **Cost / "fine":** every one of the three boards had to add `overlap_waivers` to its own intent. Each
  graded DONE only on that intent: 07 `intent_gp.json`, 08 `intent_cm5.json`, 10 `intent_v3`. 07 also
  spent ~3 min. The human board reads buildable only because no baseline is passed.
- **Upstream:** 10 lists #897 and #1250 as related; neither covers a lock disabling the marker waiver. 07
  found none. (my search) #1060 CLOSED created the `fixed_poses` waiver channel (glasgow U30 x FID8);
  nothing covers check_assembly not reading it.
- **Severity / category:** HIGH: on the given intent no placement that honours the declarations can be
  buildable. Grader/checker.

### H06 -- route_planes cannot replace a multi-layer same-net zone: it stacks new zones on top (even when all of its layers are passed), and check_impedance reads the overlap as plane splits

- **Boards (3):** 08 #1; 04 #8 (zone half); 07 #10 bullet 2.
- **Defect:**
  - 08: the input GND zone spans F/In1/In2/In4/B. `route_planes --nets GND GND GND GND GND +5V
    --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu` prints "cannot be replaced for F.Cu alone ...
    To replace it outright, run those layers together" although they were run together. It writes 11
    zones: the original plus five new GND zones at priority 1.
  - check_impedance (08) keys reference copper by (zone index, fill component). Where the two
    overlapping GND fills differ, a trace "moves" between zones and counts as a split: board_score
    impedance **28 nets** (114 crossings) on a connected, DRC-clean board. Experiment G vs H isolates
    it: 25 nets, all "split", 0.000 mm over void. With only the stale zone removed the count fell to 22;
    it reached 0 after the layer-use fixes in L13.
  - `--skip-existing-zones` (08) keeps the designer zone, but the oracle then left GND broken 2.
  - 04: one F.Cu+B.Cu GND zone becomes 3 GND zones, although the help says "an existing same-net zone
    is REPLACED in place".
  - 07: the board's single F/B/In2 GND zone cannot be replaced per layer, so the STANDARD-tier
    inner-only plane map cannot be followed. The finalize then repaired 20 pads on "a pinched fill
    island" and laid 2.0 mm GND tracks, one of them on In1.Cu (the +3V3 plane layer).
- **Repro** (08 #1):
  ```bash
  python3 -X utf8 py_router/route_planes.py wk/gp14/08_CM5_MINIMA_3/repro/gap_pour_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/pour.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu
  python3 -X utf8 -c "import sys,collections; sys.path.insert(0,'py_router'); from kicad_parser import parse_kicad_pcb; p=parse_kicad_pcb('wk/gp14/08_CM5_MINIMA_3/repro/out/pour.kicad_pcb'); print(collections.Counter((z.layer,p.nets[z.net_id].name) for z in p.zones))"
  # -> 2 GND zones on each of F/B/In1/In2/In4
  ```
- **Cost / "fine":** 08's largest cost: ~25 min, 9 routed experiments (A-I) and three helpers. 04: ~3 min.
  route_planes reported `status ok`.
- **Workarounds:**
  - 08 `helpers/drop_zone.py`: deletes the input GND zone before the pour; recorded as a commented
    non-repo step.
  - 08 `helpers/plane_components.py` and `helpers/imp_summary.py`: diagnosis only; no repo tool shows
    the fill components.
  - 04: `--skip-existing-zones`.
- **Upstream:** 08 lists #1131, #662, #598, #657, #488 and #487; 04 lists #598, #483 and #488. None
  covers it. (my search) "multi-layer zone replace", "check_impedance zone split": nothing on point.
- **Severity / category:** HIGH: a phantom impedance failure blocked DONE until a helper ran. Routing
  tool (+ grader: check_impedance's zone keying).

### H07 -- place_simple prices courtyard-less footprints by their pad box while check_assembly grades the drawn .Fab/silk body: every judged seed legal but NOT BUILDABLE, and no repo tool legalises a body overlap

- **Boards (2):** 04 #1 (+ #10 bullet 1); 07 #2 (+ #10 bullet 1).
- **Defect:** the anneal's overlap term (`simple_anneal._grown_at` -> courtyard, else pad bbox) and
  check_assembly use different occupancy models.
  - 04: 12 parts have no courtyard (THT electrolytics `CAPPRB254-500X840`, and J5). The anneal sees a
    ~4.3 x 1.6 mm pad pair; check_assembly sees the drawn 5 mm can (`b_body_sources: fab`). All 6 judged
    seeds were NOT BUILDABLE with 3-7 COURTYARD-BLOCKING pairs (seed 10: 7 pairs, 35.1 mm2; C2<->C4
    depth 2.55 mm).
  - 07: 197 of 204 footprints have no courtyard. Every judged seed had 10-12 gating pairs (C40<->L1
    6.375 mm2; BAT1's 87.5 x 56.8 mm fab body against its pad box).
  - place_pose snaps to pad legality only. The skill has no repair step between the judge and the
    route.
- **Repro** (04 #1; `P=wk/gp14/04_multichannel_mixer/repro`):
  ```bash
  python3 -X utf8 py_placer/place_simple.py $P/pile.kicad_pcb $P/s3.kicad_pcb --groups $P/groups.json --intent $P/intent.json --seed 3 --json $P/s3.json
  python3 -X utf8 py_tools/check_assembly.py $P/s3.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json
  # -> place_simple JSON_SUMMARY illegal [] ; check_assembly: 6 COURTYARD-BLOCKING pairs (C13<->RV4, C13<->C22, C14<->J7, C32<->J9, C5<->J1, C5<->J7), VERDICT: NOT BUILDABLE
  ```
- **Cost / "fine":** 04's largest cost: ~20 of the 28 min to its first DONE, and every shipped placement
  carries 4-13 extra place_pose moves. 07: ~11 min. place_simple said `illegal: []`; render_placement
  said "no legality findings".
- **Workarounds:** 04 `helpers/fix_body_overlaps.py` and 07 `helpers/fix_courtyards.py`. Both walk a
  gating part with `place_pose set --near` and keep a move only if check_assembly's gating count drops.
  07 also made 4 hand moves and placed D5 by hand.
- **Upstream:** #1182 CLOSED is the same defect, fixed for the retired seeder; place_simple's anneal
  still uses pad boxes (04). #896 and #1106 CLOSED. #1266 CLOSED is the drawn-copper variant (07).
- **Severity / category:** HIGH. Placement tool.

### H08 -- Edge-connector overhang band is graded in a currency the router rewrites: a passing placement fails floorplan after routing with no part moved

- **Boards (2):** 02 #2; 11 #2 and #5.
- **Defect:** the band is graded as the courtyard at a margin taken from the board's edge clearance or
  Default netclass clearance (`legacy_occupancy@margin=...`), and the routing writeback changes that
  margin.
  - 11 (rounded outline, so no drawn body is measurable): the placed board declares
    `min_copper_edge_clearance` 0, so the margin is the fixed default 0.55. route_planes' "fab-edge pin"
    writes 0.2, after which every courtyard overhang reads 0.35 mm less. J2/J3 go 7.006 -> 6.66 against
    a 7.00 minimum and P1 goes 1.050 -> 0.70 against 1.05: 3 ERRORs. board_score counts them as
    floorplan blocking and check_complete reads INCOMPLETE.
  - 02: the descent writeback lowers Default 0.254 -> 0.2223, and route_planes moves
    `min_copper_edge_clearance` 0.01 -> 0.2. J1's overhang goes from 25.8800 (pass) to 25.7849 (fail,
    declared 25.88), J2 to 14.4183 (fail), and J1's pad copper reads 0.0150 against 0.2 (fail). Result:
    `BLOCKING=2 (floorplan=2)` on a connected, DRC-clean board.
  - 11 #5: the emitted band 0 on a rounded outline puts the courtyard 0.55 mm inside the edge and the
    USB-C body front 1.055 mm inside. Seating it flush needs a hand-written band of 1.05, which then
    grades 0.70 after routing.
- **Repro** (11 #2):
  ```bash
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/11_daplink/repro/placed_s3.kicad_pcb  --intent wk/gp14/11_daplink/repro/intent_edges.json
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/11_daplink/repro/armA_routed.kicad_pcb --intent wk/gp14/11_daplink/repro/intent_edges.json --allow-routed
  ```
- **Cost / "fine":** 11: ~15 min, a rejected full route (arm A), and `--board-edge-clearance 0.55` forced
  on every routing step; #5 another ~10 min. 02: ~10-15 min, and 2 of 6 judged seeds became ineligible
  after a full route.
- **Upstream:** #1160 CLOSED is the same writeback with a different consequence (02). #987 and #1174
  CLOSED are nearest (11). (my search) #961 CLOSED (`rule_edge_connector` grades `overhang_mm` with a
  clearance-shortfall magnitude): same family.
- **Severity / category:** HIGH: a correct placement is graded failing with nothing moved, which blocked
  DONE. Grader/checker. Cross-ref M01 (route_planes ignores `--board-edge-clearance`, 11 #4).

### H09 -- redo_record drops env-knob prefixes, so the auto-recorded redo_commands.sh does not replay the shipped board (and manifest_to_plan drops the knob silently)

- **Boards (2):** 01 #1; 08 #8 (+ GRADE 08: `KICAD_PLANE_FRAGILITY_LAYERS` in the chain).
- **Defect:** `record_invocation` writes `["python3","-u","-X","utf8"] + sys.argv` (redo_record.py
  ~l.93-104) and never reads the environment.
  - 01: the route step ran with `KICAD_PLANE_FRAGILITY_COST=0` and is recorded without it, although the
    run's own JSON_SUMMARY lists `env_knobs`. Replaying the recorded line gives **2 vias / 146.10 mm**;
    the shipped board has **0 vias / 131.72 mm**.
  - 01: manifest_to_plan then writes a 1-step plan without the knob and prints "0 command(s) skipped".
  - 08: `KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'` is likewise absent.
  - The routing skill (Step 2c item 4, Step 9, DENSE rule 1) and #670 say env prefixes ride the
    manifest.
- **Repro** (01 #1):
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  F=$(pwd)/$RP/rec; mkdir -p $F
  REDO_RUNDIR=$F REDO_MANIFEST=$F/redo_commands.sh KICAD_PLANE_FRAGILITY_COST=0 python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/rec/out.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05
  tail -1 $F/redo_commands.sh          # no KICAD_PLANE_FRAGILITY_COST=0 prefix
  # replay of that line (no env) vs the real run (env):
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/replay_noenv.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05
  python3 -X utf8 py_tools/board_score.py $RP/replay_noenv.kicad_pcb --quiet   # vias=2 copper_mm=146.1
  ```
- **Cost / "fine":** 01 hand-wrote `final_route/placed_plan.sh` to carry the prefix. 08 spent ~3 min and
  annotated the manifest by hand. manifest_to_plan said "0 command(s) skipped".
- **Upstream:** #670 OPEN covers the plan-JSON half; its premise ("env knobs replay fine in redo-manifest
  plan files") is false for the AUTO-recorded manifest. #465 CLOSED promoted env knobs to flags, but
  the fragility knob was not promoted. (my search) "redo_record environment": nothing.
- **Severity / category:** HIGH: the no-LLM replay silently yields a different board. Routing tool (redo
  harness).

### H10 -- Routed differential pairs: route_diff's "coupled"/"matched" ignores the terminal legs, a single-ended fallback goes unnoticed, and no DONE grader checks routed pairs

- **Boards (2):** 14 #2 (+ #14 bullet 3, GRADE 14); 08 #5.
- **Defect:**
  - 14: route_diff reports DQS0 `"outcome": "coupled"`. With `--diff-pair-intra-match` it reports CLK0
    `"status": "matched", "delta_mm": 0.0003`.
  - 14, measured: DQS0 has only 0.57 of 21.08 mm coupled (P on In2.Cu 19.95 + F 1.13; N on B.Cu 15.92 +
    F 0.57) and a pad-to-pad skew of 4.60 mm, which intra-match made 5.29 mm. CLK0 skew is 2.97 mm
    (16.80 vs 19.77). The coupled middle and the matching cover only route_diff's own middle span; 35.8 mm
    of uncoupled terminal legs is in neither number.
  - 08: declared 100-ohm lane `/CM5/DPHY0_P.D0` was routed as two uncoupled single-ended traces
    (`single_ended_diff_pairs` in JSON_SUMMARY). route_diff said exit 0 and `failed_diff_pairs: []`;
    board_score gave blocking 0 and check_complete DONE. It was the fewest-via board of that run (193).
  - Neither board_score nor check_complete has a diff-pair component. verifier.md rules an ungraded
    declared class a FAIL, so a DDR board cannot get a clean verdict from the stack. 14 is machine-DONE
    but failed the verifier's DDR3 pair lens.
- **Repro** (08 #5, repo tools only):
  ```bash
  KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0' python3 -X utf8 py_router/route_diff.py wk/gp14/08_CM5_MINIMA_3/repro/gap_single_ended_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/se.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.25 --via-drill 0.15 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0 --via-cost 250 | grep -o '"single_ended_diff_pairs[^]]*\]'
  ```
  14 #2 (`W=wk/gp14/14_imx6ulz_4l`): `grep -o '"pair": "/DRAM/DRAM_DQS0"[^}]*}' $W/repro/pairs_route_diff.log`, then
  `python3 -X utf8 $W/helpers/pair_check.py $W/repro/pairs_final.kicad_pcb /DRAM/DRAM_DQS0 /DRAM/DRAM_DQS1 /DRAM/DRAM_CLK0`
- **Cost / "fine":** 14: ~40 min (a verifier FAIL and three fix attempts). 08: small; it rejected the 193-
  and 210-via boards and shipped 217.
- **Workarounds:** 14 `helpers/pair_check.py` reports coupled length, layers and skew per pair.
- **Upstream:** 08 lists #226 and #221 CLOSED (fallback via clearance), which are not this. 14 lists #677
  OPEN, which is different. (my search) #766 CLOSED ("--diff-pair-intra-match length-matches only ONE
  pair per invocation, silently") and #210 CLOSED wontfix (a USB pair de-coupled by the 3 mm floor):
  related, neither covers this.
- **Severity / category:** HIGH. Routing tool + grader/checker.

### H11 -- check_assembly's courtyard gating floors pass overlaps the project grades as errors and KiCad reports (`courtyards_overlap`)

- **Boards (2):** 04 #6 (+ the consequence in #3); 14 #12.
- **Defect:** check_assembly gates a pair only past area >= 0.5 mm2 or 25 % AND depth >= 0.3 mm. That is a
  documented policy.
  - 04: R39<->R42 (0.0823 mm2, depth 0.217 mm) is "advisory" with VERDICT buildable, although
    check_assembly's own JSON says `courtyard_severity "error"`, basis project. KiCad reports a
    `courtyards_overlap` error. That board passed board_score, check_complete and verifier call 1; only
    the verifier's KiCad cross-check caught it.
  - 14: `place_pose set C20 75.55 112.4 --rot 90` was legal and no_worse, and check_assembly said
    buildable, while KiCad reported `courtyards_overlap` FB2/C20.
- **Repro** (04 #6; `P=wk/gp14/04_multichannel_mixer/repro`):
  ```bash
  python3 -X utf8 py_tools/check_assembly.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json   # R39 <-> R42 advisory, buildable
  python3 -X utf8 tests/stress/kicad_drc_compare.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb               # COURTYARD kicad=1 ... R39<->R42 krt=advisory sev=error ; connwidth=10@<0.3mm
  ```
- **Cost / "fine":** 04: a shipped-then-superseded final chain and a second verifier call (~20 min, shared
  with M05). 14: ~5 min.
- **Upstream:** #1095 CLOSED (check_assembly ignored the project's severity): it now reads the severity,
  but the floors still downgrade a small overlap. 14 found none.
- **Severity / category:** HIGH: only KiCad or the verifier caught it, though it is a documented
  policy. Grader/checker.

### H12 -- A declared netclass track width is graded nowhere (net_widths UNGRADED, so DONE); the skill chain's explicit `--track-width` overrides class widths

- **Boards (2):** 12 #2 (+ GRADE 12, verifier FAIL); 08 #9 bullet 4.
- **Defect:**
  - 12: the input is a KiCad-6 project whose `Power` class lists its members inside
    `net_settings.classes[].nets`: +1V8, +3V3, +5V, /VPHY, /VPLL, GND, VBUS, Vdrive.
  - `list_nets --design-rules` prints `[Power] clearance=0.15 track_width=0.3 ...` with no members, the
    same as an unassigned class. board_context never mentions the class.
  - board_score and check_complete report `UNGRADED (not scored, not passed): ... net_widths` and DONE.
  - The skill chain's `--track-width 0.15` overrides every class width. The shipped v4 had 6 of 8 Power
    nets under 0.3 mm (~124 mm of copper): +1V8 and Vdrive at 0.25, /VPHY and /VPLL at 0.15. Only the
    independent verifier read the class and failed the board.
  - 08: the final DONE board has the buck switch node `/PCIe-M2/M2_LX` 36.4 mm long, 29.5 mm of it at
    0.1 mm (0.6 requested), and `M2_3V3` necked to 0.1 mm for 4.4 mm; route.py's
    `power_trace_ampacity` puts both at 0.45 A. No gating tool flagged either. (No EMC row was given, by
    campaign rule.)
  - Teammate caveat (12): "My own miss too: I looked for netclass patterns/assignments, the KiCad 7+
    fields."
- **Repro** (12 #2):
  ```bash
  python3 -X utf8 py_router/list_nets.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb --design-rules | grep Power   # no members
  python3 -c "import json; print([(c['name'],c.get('nets')) for c in json.load(open('wk/gp14/12_steppenprobe/repro/pile.kicad_pro'))['net_settings']['classes']])"
  python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/final.kicad_pcb --quiet   # net_widths UNGRADED
  python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/final.kicad_pcb --net-min-widths wk/gp14/12_steppenprobe/widths.json --quiet   # net_widths 6
  ```
- **Cost / "fine":** 12: a verifier call, the re-route rounds P1b-P5b, and the run ends without DONE
  (through H26). 08: reported in REPORT.md only.
- **Upstream:** 12 searched "netclass track width net_widths" and found none; "Power netclass width" and
  "net-min-widths netclass" give #1237 OPEN (an audit design) as nearest and #530 CLOSED (clearance
  only). (my search) #1033 CLOSED (the bulk route laid power nets at the signal `--track-width`): same
  family.
- **Severity / category:** HIGH: only the verifier caught it. Grader/checker (+ skill text: the chain
  overrides class widths).

### H13 -- Placement writer never rotates a pad that carries the KiCad-6 `locked` token (and the given pile already carries that damage)

- **Boards (1):** 12 #1.
- **Defect:** `py_placer/placement/writer.py::_rotate_pad_angles` matches
  `\(pad\s+"[^"]*"\s+\S+\s+\S+\s*\n?\s*\(at ...`, which allows exactly two tokens before `(at`. So a pad
  written `(pad "1" smd roundrect locked (at x y a)` never matches, and its absolute angle stays put
  when the footprint turns.
  - The given pile already has 38 of 84 parts with pads turned 90 deg against their bodies.
    `check_pads` reports 126 overlapping different-net pad pairs on U1.
  - Round 1: with U1 at 0 deg, qfn_fanout escaped 0/31 ("dropped 31 stub(s) grazing a foreign pad")
    and the judge route left 35-46 nets open. With U1 at 90/270 it escaped 31/31. The judge was
    ranking seeds by U1's angle.
- **Repro** (12 #1):
  ```bash
  python3 -X utf8 py_placer/place_pose.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb \
      wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb rotate U4 90 --force
  python3 -c "t=open('wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb').read(); i=t.find('(fp_text reference \"U4\"'); s=t.rfind('(footprint ',0,i); b=t[s:s+60000]; import re; print(re.search(r'\(at [^)]*\)',b).group(0), re.search(r'\(pad \"1\"[^\n]*',b).group(0)[:60])"
  #   -> (at 125.690300 123.359000 90) (pad "1" smd rect locked (at -2.7 -1.905) ...   footprint turned, pad angle still 0
  python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb --component U4   # overlapping pads
  python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb --component U1       # 126 overlaps in the GIVEN pile
  ```
- **Cost / "fine":** round 1 voided (12 placements + 6 judge routes), ~15 min of diagnosis, and a
  helper. place_simple said all 12 seeds legal; check_assembly said buildable.
- **Workaround:** `helpers/normalize_pile.py`: sets each footprint angle to its pads' common angle and
  drops the per-pad `locked` token.
- **Upstream:** none. Nearest #1163 and #1214 (closed). (my search) "pad locked rotate writer": nothing on
  point.
- **Severity / category:** HIGH: corrupted geometry. Placement tool. Cross-ref H14.

### H14 -- No placement grade sees a footprint whose own pads overlap each other

- **Boards (1):** 12 #4.
- **Defect:** r1/s9 is legal per place_simple and `VERDICT: buildable (blocking 0)` per check_assembly
  with `--baseline` and `--intent`, while U1 has 129+ overlapping different-net pad pairs. Only
  `check_pads`, which no step of either skill runs, and qfn_fanout's warning ("U1 has 158 overlapping
  different-net pad pair(s)") noticed.
- **Repro** (12 #4):
  ```bash
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/12_steppenprobe/repro/r1_s9.kicad_pcb   # buildable
  python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/r1_s9.kicad_pcb       # 129+ overlapping pad pairs on U1
  ```
- **Cost / "fine":** it let H13 run a full round and judge before anything refused.
- **Upstream:** none; nearest #1106 and #1204, both about other parts. (my search) #1111 CLOSED (check_pads
  models custom pads by bbox) is different.
- **Severity / category:** HIGH. Grader/checker.

### H15 -- place_simple's anneal counts a courtyard-less pin-frame container (Teensy footprint) as a whole-board overlap body, so no state is ever "best"

- **Boards (1):** 06 #1 (+ GRADE 06).
- **Defect:** U8 (the Teensy40 frame) has no courtyard, so its rect is its pad bbox, which is the whole
  board (138.575..158.425 x 87.695..123.82). `Annealer.overlap` sums grown-rect overlaps over every pair
  sharing a face and does not skip `state.container_refs`; the halo term does skip them ("a container
  is a frame, not a body").
  - On a finished seed the overlap term was 464.5 mm2, 442.0 mm2 of it from U8-frame pairs. That split
    was measured inline and no file was kept.
  - So `v['ov'] < CLEAN` is never true. Every round-1 seed left 3-5 parts with "no legal pose", and 4x
    `--moves` still left three.
  - With the frame's face bits zeroed and keep-outs over U8's pin rows, the same seed was legal on its
    first run (30000 moves in 10.1 s, exit 0). Round 2 had 11/12 legal seeds against 0/12.
  - Keep-outs alone still left SW1 illegal.
- **Repro** (06 #1; `R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`):
  ```bash
  python3 -X utf8 py_placer/place_simple.py $R/fixed_u8lock.kicad_pcb $R/gap2_plain_s0.kicad_pcb --groups $R/groups.json --intent $R/intent_frame.json --seed 0     # exit 4, SW1 illegal
  python3 -X utf8 wk/gp14/06_rp2350_fpga_eensy_prePlane/helpers/place_simple_frame_fix.py $R/fixed_u8lock.kicad_pcb $R/gap2_helper_s0.kicad_pcb --groups $R/groups.json --intent $R/intent_frame.json --seed 0   # exit 0
  ```
- **Cost / "fine":** together with H04, round 1 was unjudgeable, and a helper was needed. It reads as
  "the board is too full". GRADE: this board's films use the patched placer (disclose).
- **Workaround:** `helpers/place_simple_frame_fix.py`: monkeypatches `Annealer.__init__` and points
  `place_simple.__file__` at itself so `--round` subprocesses pick it up. Plus keep-outs
  (`intent_frame.json`).
- **Upstream:** none. Related CLOSED: #1212, #1213, #1184.
- **Severity / category:** HIGH. Placement tool.

### H16 -- place_simple's anneal blocks the entire far face under an SMD part that has one drilled (locating-peg) pad

- **Boards (1):** 07 #1.
- **Defect:** BAT1 is an SMD 3x18650 holder on F.Cu with one unnetted 1.8 mm peg hole.
  `footprint_has_through_pads` therefore makes the whole part two-sided, and `Annealer.overlap` prices
  BAT1's full 87.5 x 49 mm fallback courtyard on B.Cu too. `legality.rect_on` gives the far face only
  the drilled-pad box.
  - No B-side part entered the ~4200 mm2 under BAT1, and 12/12 seeds exited 4.
  - With the peg removed, the same seed costs 3870.9 in 27.9 s, against 8300.9 in 99.9 s, and exits 0.
  - Neither check_assembly nor place_pose objects to a B part under BAT1.
- **Repro** (07 #1):
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gp14/07_One-Air-Max/repro/withhole.kicad_pcb 'wk/gp14/07_One-Air-Max/repro/gap1_withhole_s{seed}.kicad_pcb' --groups wk/gp14/07_One-Air-Max/repro/groups.json --intent wk/gp14/07_One-Air-Max/repro/intent_gap1.json --seeds 7 --clustered-seeds 7 --json 'wk/gp14/07_One-Air-Max/repro/gap1_withhole_s{seed}.json'
  #   -> exit 4, "no legal pose for CO2, I2C3, L3, PM2", cost 8300.9
  python3 -X utf8 py_placer/place_simple.py wk/gp14/07_One-Air-Max/repro/nohole.kicad_pcb 'wk/gp14/07_One-Air-Max/repro/gap1_nohole_s{seed}.kicad_pcb' --groups wk/gp14/07_One-Air-Max/repro/groups.json --intent wk/gp14/07_One-Air-Max/repro/intent_r1.json --seeds 7 --clustered-seeds 7 --json 'wk/gp14/07_One-Air-Max/repro/gap1_nohole_s{seed}.json'
  #   -> exit 0, cost 3870.9
  ```
- **Cost / "fine":** ~12 min, including one wasted 12-seed round (6.5 min).
- **Workaround:** `helpers/bat1_hole.py strip/restore`, plus an intent keep-out `BAT1_peg_hole_far_face`
  on B. GRADE: placement ran on `fixed_nohole`.
- **Upstream:** none. (my search) "footprint_has_through_pads" returns #835, #878 and #836 CLOSED, the
  per-face accounting family: related.
- **Severity / category:** HIGH. Placement tool.

### H17 -- route.py's in-run GND plane repair rips a fully routed 17-pad rail and ships it with no copper; `pad_pairs_open` omits it

- **Boards (1):** 09 #1 (+ #9, GRADE 09).
- **Defect:** the log says "blocked by +3.3V - ripping... (#517 ordering: immediate reconnect of 1 ripped
  net(s): +3.3V)".
  - The written board has 0 segments and 0 vias on +3.3V: 17 pads, 7 of them U1 supply pins.
    check_connected reports `Unrouted nets (1): +3.3V (17 pads)`.
  - `JSON_SUMMARY_MIN.pad_pairs_open` = `{"count": 1, "nets": ["/U7D-"]}` omits it, although
    `failed_multipoint` lists it (deficit 17).
  - It happened on 3 of 3 first passes with the fine parameters; the next route.py pass re-routes it.
  - Nothing in the log says the run REMOVED a routed net's copper.
- **Repro** (09 #1, ~60 s):
  ```
  python3 -X utf8 py_router/route.py wk/gp14/09_StickHub/repro/g1_step2.kicad_pcb wk/gp14/09_StickHub/repro/g1_out.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.25 --power-nets GND '+5V' VIN 'Net-(J1-Pin_1)' '+3.3V' '+1V8' --power-nets-widths 0.2 0.3 0.3 0.3 0.2 0.2 --layer-costs 1.0 1.0 --grid-step 0.05 --json-out wk/gp14/09_StickHub/repro/g1_out.json
  python3 -X utf8 py_router/check_connected.py wk/gp14/09_StickHub/repro/g1_out.kicad_pcb   # -> Unrouted nets: +3.3V (17 pads)
  ```
- **Cost / "fine":** a full extra iteration on every chain, and step4 had to be the shipped board. It
  also made a rail-less board rank as well as the shipped one (M26).
- **Upstream:** #600 and #1156 CLOSED, same family. (my search) #1215 CLOSED (`failed` covers only pass
  1's net list) and #1069 CLOSED (`--json-out` drops nets broken in an earlier lap) are reporting-side
  relatives.
- **Severity / category:** HIGH. Routing tool.

### H18 -- route.py's improvement gate accepts an all-nets pass that adds DRC shorts

- **Boards (1):** 10 #6.
- **Defect:** `IMPROVEMENT GATE: this run broke 9 previously-connected net(s) [...], worsened 0,
  connected 9 -- ACCEPTED`. The gate weighs nets lost against nets gained and never looks at DRC.
  - board_score: input blocking 12 (12 broken, 0 DRC) -> output 42 (23 broken, **17 DRC**, 2 unrouted).
  - `check_drc --clearance-margin 0.1` on the output: 4 segment-segment (3 in CONTACT), 9 via-segment
    (5 CONTACT), 1 via-via (CONTACT) and 3 via-drill-hole (CONTACT).
- **Repro** (10 #6): run with input `wk/gp14/10_glasgow_revC/repro/gap6_s2_c.kicad_pcb` (and its
  `.kicad_pro`):
  `python3 -X utf8 py_router/route.py final_route/s2_c.kicad_pcb final_route/iterC1.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.4 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --power-nets GND +3V3 +5V +1V2 /IO_Banks/VIOA /IO_Banks/VIOB /IO_Banks/VIO_AUX /VUSB /xVBUS '*ISNS_H' 'Net-(U14-OUT)' 'Net-(U31-OUT)' --power-nets-widths 0.25 0.25 0.4 0.25 0.3 0.3 0.25 0.4 0.4 0.3 0.3 0.3 --no-bga-zones --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2`
  then grade both with `python3 -X utf8 py_router/check_drc.py <board> --clearance-margin 0.1`.
- **Cost / "fine":** ~5 min; trusting the gate would have continued from a board with shorts. The two
  earlier all-nets passes of the same run were reverted correctly.
- **Upstream:** #600 nearest. (my search) #1114 CLOSED (the gate judged GND before plane repair) and #1173
  CLOSED (`--json-out` described the rejected attempt): neither covers DRC.
- **Severity / category:** HIGH. Routing tool.

### H19 -- route.py strips BGA dog-bone escapes during rip-up, cannot restore them, then its hint blames the fanout

- **Boards (1):** 10 #7.
- **Defect:** the fanout reported "Dog-bone escape: 105/105 signals escaped ... 0 failed".
  - The escape stubs of C9, B9 and E8 are on the route step's input (1, 1 and 3 segments) and gone from
    its output.
  - route.py's hint: "pad U30.C9 is a fanout-dropped ball (no escape stub) ... Re-run the fanout for this
    net". It says the same for E8, J5 and D7. Re-running the fanout changes nothing the route step will
    not undo.
  - This is the mechanism behind most of the run's open nets (GRADE: ships blocking 7, i.e. 6 broken +
    1 short).
- **Repro** (10 #7): count copper at U30.C9 on `wk/gp14/10_glasgow_revC/repro/gap7_s2a_c.kicad_pcb`
  (1 segment), run
  `python3 -X utf8 py_router/route.py final_route/s2a_c.kicad_pcb final_route/s2_c.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.4 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --power-nets ... --no-bga-zones --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2`
  on it (the `...` is in the teammate's text; the full list is #6's), and read the hint and the ball's
  copper (0 segments) on the output.
- **Cost / "fine":** a misdirected diagnosis to rule out, since the skill's section 4 reads "fanout
  dropped balls" as a fanout/placement problem. These nets are a large share of every open list in the
  run.
- **Upstream:** #1156 CLOSED, same family (there the nets were out of scope and the escapes VIP). (my
  search) #652 CLOSED is where the "fanout-dropped ball" diagnosis came from.
- **Severity / category:** HIGH. Routing tool.

### H20 -- route.py's end-of-run strict collapse (#1063) reports removals it never writes on a mixed-dialect file

- **Boards (1):** 14 #3.
- **Defect:** route.py prints "Strict collapse (#1063, end of run): removed 291 redundant segment(s) on
  100 net(s)" but removes nothing.
  - On a non-KiCad-10 file (`(version 20240108)`) the CLI calls
    `remove_segments_from_content(content, removed, net_id_to_name=None)`.
  - The chain's boards are mixed-dialect: 2785 segments carry `(net "/name")` and 440 carry `(net 13)`.
    So every name-ref target matches 0 blocks, and the returned count is discarded.
  - Measured: 3014 segments in, 3014 out; removable-segment 144 -> 144. Each of 4 passes "removed" ~291
    again.
  - With the name map, 293/293 match. The leftovers fail check_complete.
- **Repro** (14 #3; `R=$W/repro`, `W=wk/gp14/14_imx6ulz_4l`):
  ```bash
  L="F.Cu In1.Cu In2.Cu B.Cu"
  python3 -X utf8 py_router/check_weird.py $R/collapse_noop.kicad_pcb | grep removable-segment        # 144
  python3 -X utf8 py_router/route.py $R/collapse_noop.kicad_pcb $R/out_cn.kicad_pcb --nets '*' --track-width 0.1 \
    --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers $L --layer-costs 1.0 6.0 1.5 1.0 \
    --no-bga-zones --max-ripup 5 --via-cost 250 --power-nets GND +3V3 --power-nets-widths 0.2 0.2 | grep "Strict collapse"
  python3 -X utf8 py_router/check_weird.py $R/out_cn.kicad_pcb | grep removable-segment                    # still 144
  ```
- **Cost / "fine":** ~25 min and a helper. The helper's first version removed check_weird's whole
  removable set at once and disconnected +5V at U6, because that set is graded per segment, not
  jointly.
- **Workaround:** `helpers/strict_collapse.py` runs route.py's own `collapse_strict_redundant` and strips
  with the name map. It also runs the hygiene pass that feeds H01/H03.
- **Upstream:** #1063 CLOSED is the collapse itself; "late_strict_collapse" finds nothing; #162 OPEN is
  general. (my search) "strict collapse", "net_id_to_name remove_segments": nothing on point.
- **Severity / category:** HIGH: the tool reports something false. Routing tool.

### H21 -- No tool grades or honours a `.kicad_dru` LENGTH window; route_bus and the default chain break it

- **Boards (1):** 14 #1 (+ #14 bullet 1, GRADE 14).
- **Defect:** the board's `.kicad_dru` declares
  `(rule "byte0 delay matching" (condition "A.NetClass == 'DRAM_LDQ'") (constraint length (min 11.5mm) (opt 13mm) (max 14.5mm)))`.
  - Every routing step prints "parsed, but length has no consumer in this tool yet".
  - check_drc has no length check. `board_score --length-groups` grades a spread only.
  - route_bus plans the bus with no length term, though Step 1a says "use it on every such bus".
  - `--length-match-group` only extends nets toward the longest, and skips already-routed nets.

  Lane-0 nets outside the window per KiCad:

  | chain | nets outside 11.5-14.5 mm |
  |---|---|
  | default chain | 8 of 8 (9.2-20.9 mm) |
  | route_bus joint | 3-4 |
  | route_bus escape mode | 6 (DQ5 52.6 mm) |
  | shipped chain: lane 0 routed first, in protected matched steps | 0 (12.5-14.1 mm) |
- **Repro** (14 #1; `W=wk/gp14/14_imx6ulz_4l`, `R=$W/repro`):
  ```bash
  python3 -X utf8 py_tools/board_score.py $R/viainpad_len.kicad_pcb --length-groups $R/length_groups.json --quiet   # length: spread only
  python3 -X utf8 py_router/check_drc.py $R/viainpad_len.kicad_pcb --clearance-margin 0.1                        # no length check at all
  python3 -X utf8 $W/helpers/kicad_length_check.py $R/viainpad_len.kicad_pcb                                   # KiCad: 8 length_out_of_range
  ```
- **Cost / "fine":** ~1 h 30 min, most of the run. Every repo grader read the board clean.
- **Workaround:** `helpers/kicad_length_check.py` (kicad-cli DRC on a temp copy). The route-order recipe
  that met the window is in #14 bullet 1.
- **Upstream:** none. #1246 and #1248 CLOSED are about spread measurement. (my search) #1237 OPEN, a design
  for an audit judging a board against a spec, is an umbrella only.
- **Severity / category:** HIGH. Routing tool + grader/checker.

### H22 -- board_score's length component cannot see a via-in-pad join, so a connected group reads UNGRADED

- **Boards (1):** 14 #4.
- **Defect:** board_score reports `DRAM_LDQ: 4 of 8 member(s) have pads not joined by track copper ...`,
  so length is UNGRADED, although all 8 are connected and KiCad measures each one.
  - The track graph links a pad disc and a via disc only through a TRACK node inside both. A via in a
    pad whose tracks leave on another layer is never linked to the pad.
  - Through check_complete this turns a declared spec into "UNEXAMINED", which verifier.md rules a FAIL.
- **Repro** (14 #4; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  python3 -X utf8 py_tools/board_score.py $R/viainpad_len.kicad_pcb --length-groups $R/length_groups.json --json $R/out_l.json --quiet
  python3 -c "import json;print(json.load(open('$R/out_l.json'))['components']['length'])"   # DQ3, DQ7 'unjoined'
  python3 -X utf8 py_router/check_connected.py $R/viainpad_len.kicad_pcb --nets /DRAM/DRAM_DQ3 /DRAM/DRAM_DQ7  # connected
  ```
- **Cost / "fine":** ~20 min and a helper. The joins must go on last, because route.py's strict-collapse
  model removes them as in-pad wiggles.
- **Workaround:** `helpers/vip_joins.py`: 0.05 mm joins staged with `check_join.py`.
- **Upstream:** none (#1246 and #1248 closed, different).
- **Severity / category:** HIGH: a false "unjoined" blocks DONE. Grader/checker.

### H23 -- bga_fanout `--check-for-previous` lays escapes over existing foreign-net tracks

- **Boards (1):** 14 #5.
- **Defect:** bga_fanout reports requested 41, escaped 41, failed 0, but adds 34 check_drc violations
  (64 -> 98), 20 of them `/DRAM/DRAM_DQ5 <-> VMEM`.
  - In exp_l6 one survived the whole chain as a KiCad `shorting_items` (a DQS0_N fanout via on DQ5's
    track at (69.20, 109.00)) plus a `tracks_crossing`.
  - The exit planning treats only earlier fanout copper (`find_existing_fanouts`) as occupied.
- **Repro** (14 #5; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  L="F.Cu In1.Cu In2.Cu B.Cu"
  python3 -X utf8 py_router/check_drc.py $R/fanout_over_tracks.kicad_pcb --clearance-margin 0.1 | grep FOUND   # 64
  python3 -X utf8 py_router/bga_fanout.py $R/fanout_over_tracks.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' \
    --check-for-previous --layers $L --layer-costs 1.0 -1 1.5 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 \
    --track-width 0.1 --clearance 0.1 --diff-pairs '/DRAM/DRAM_DQS0_*' '/DRAM/DRAM_DQS1_*' '/DRAM/DRAM_CLK0_*' \
    --diff-pair-gap 0.1 --output $R/out_fo.kicad_pcb | grep JSON_SUMMARY            # failed 0
  python3 -X utf8 py_router/check_drc.py $R/out_fo.kicad_pcb --clearance-margin 0.1 | grep FOUND                    # 98
  ```
- **Cost / "fine":** ~20 min, and one shipped-candidate short.
- **Upstream:** #1189 CLOSED is related (exit cell vs a foreign via).
- **Severity / category:** HIGH: it shorts copper. Routing tool.

### H24 -- route_bus writes its output without the board's `.kicad_dru` and design-brief siblings

- **Boards (1):** 14 #8.
- **Defect:** `final_route_old2/` holds `s1a_bus.kicad_pcb` and `.kicad_pro` only, although the input had
  `.kicad_dru` and `.design-brief.json`.
  - Every later step read no dru.
  - KiCad graded the bus board with no length rule: the first check printed `length_out_of_range 0`,
    which was false; with the dru restored by hand it was 4.
  - This breaks the repo's own sibling-carrying rule (`copy_board.SIBLING_EXTS`).
- **Repro** (14 #8; `W=wk/gp14/14_imx6ulz_4l`, `R=$W/repro`): `ls $W/final_route_old2/ | grep s1a_bus`
  (no `.kicad_dru`); to regenerate (~35 min):
  `python3 -X utf8 awx/route_bus.py $R/bus_in.kicad_pcb $R/out_bus.kicad_pcb --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25; ls $R/out_bus.*`
- **Cost / "fine":** ~10 min.
- **Upstream:** none ("route_bus kicad_dru", "route_bus sibling"; (my search) "route_bus": nothing).
- **Severity / category:** HIGH: later steps silently lost the board's rules. Routing tool.

### H25 -- check_drc's default relative margin passes tracks under a footprint's local clearance that KiCad rejects

- **Boards (1):** 14 #10.
- **Defect:** U1's footprint declares a local clearance of 0.12 mm, and the router lays tracks at
  0.115-0.1186 mm. So the router also undershoots the override.
  - check_drc at its default 5 % margin is clean, and board_score reports `drc 0`.
  - `--clearance-margin 0` finds 15 PAD-SEGMENT violations ("Required clearance: 0.1200mm
    (local/netclass override)").
  - kicad_drc_compare: kicad=6 check_drc=0, DIVERGED.
- **Repro** (14 #10; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  python3 -X utf8 py_router/check_drc.py $R/u1_local_clearance.kicad_pcb | grep FOUND                       # default margin
  python3 -X utf8 py_router/check_drc.py $R/u1_local_clearance.kicad_pcb --clearance-margin 0 | grep FOUND   # 15
  python3 -X utf8 tests/stress/kicad_drc_compare.py $R/u1_local_clearance.kicad_pcb --baseline $R/r1_fixed.kicad_pcb | tail -3
  ```
- **Cost / "fine":** ~10 min. The shipped board is 0 either way after a fine-grid force-reroute of
  BOOT_CFG1_3.
- **Upstream:** none on point. (my search) #326 CLOSED (check_drc ignored pad overrides, fixed), #697
  CLOSED (placement census) and #1207 CLOSED: none is about the margin.
- **Severity / category:** HIGH: only KiCad caught it, although the margin is a documented tolerance.
  Grader/checker (+ routing tool, for undershooting the override).

### H26 -- route.py necks power nets to 0.15 mm at 0.5 mm-pitch pins, and no flag stops it without breaking the net

- **Boards (1):** 12 #3. Possibly related: 08 #9 bullet 4 (`M2_3V3` necked to 0.1 mm for 4.4 mm); not
  established.
- **Defect:** variant P1b routed all 8 Power-class nets at `--power-nets-widths 0.3`.
  - Every remaining under-width segment is a 0.15 mm neck-down of up to ~2.5 mm at U1's LQFP pins:
    VCORE 12/37/49, VPHY 4, VPLL 9, GND 1/5/13/15/25/35/47/51 and one +3V3.
  - Yet a straight 0.3 mm exit along a 0.3 mm pad clears the neighbouring pads by 0.2 mm (> 0.15).
  - `--escalation off` (P2b) still necks ("a wide power net may still neck for at most 2 mm of path at a
    pad entry") and adds an undersized item.
  - Adding `--no-power-tap-neckdown` (P3b) breaks +1V8.
  - `--grid-step 0.05` (P4b: 5 nets, 27 mm under, 116 vias) and `--neckdown-length 0.5` (P5b: 5 nets,
    20 mm under) do not remove it.
- **Repro** (12 #3):
  ```bash
  bash wk/gp14/12_steppenprobe/expP1b/plan.sh   # writes into expP1b/ (fresh copy first: copy_board s0_fix.kicad_pcb expP1b/placed.kicad_pcb)
  python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb --net-min-widths wk/gp14/12_steppenprobe/widths.json --quiet
  ```
- **Cost / "fine":** five extra chains, and the run ends NOT DONE (blocking 5 = net_widths 5).
  `Design rules [...]` disclosed the narrowed sites; the run reported 0 failed.
- **Upstream:** #72 CLOSED introduced the tap neck-down. #593 OPEN (width-aware corridor reservation for
  power nets) is related. None covers necking at a pin a full-width track can reach.
- **Severity / category:** HIGH: the board cannot reach DONE with repo tools. Routing tool.

---

## MEDIUM

### M01 -- Steps that lay no copper (bare pour) rewrite the project's authored DRC floors; route.py then calls the invented value "the original number"

- **Boards (7):** 02 #4; 04 #8 (floor half); 05 #3; 06 #8; 11 #4; 12 #10; 13 #4.
- **Defect:** route_planes, run as a bare pour that places no via or track, writes into the output
  `.kicad_pro`:
  - **`min_via_drill` from None to the Default netclass's DRAWING drill** (02 0.635, 05 0.6, 11 0.4).
    The next route.py then prints
    `FAB FLOOR RELAXED -- via drill: 0.6 -> 0.5 mm; 107 of 107 object(s) on this board are below the ORIGINAL 0.6mm`
    and asks you to "re-route at that floor" if "the original number was a real process limit". The
    toolchain wrote that number one step earlier.
  - **`min_hole_clearance` lowered**: 06 0.25 -> 0.09 by chain end, so `check_complete --authored-from`
    reads UNSOUND with 199 items down to 0.1431 mm; 11 0.25 -> 0.2; 12 0.25 -> 0.15; 13 0.254 -> 0.127,
    and 0.09 by chain end.
  - With `--track-width`/`--via-size` omitted (04): `min_track_width` 0.3 -> 0.2, `min_connection`
    0.3 -> 0.2, `min_via_diameter` 1.5 -> 0.6.
  - **`min_copper_edge_clearance` 0.0 -> 0.2 ("fab-edge pin")** although `--board-edge-clearance 0.55`
    was passed (11). route_diff later writes 0.55, so the rule flips 0 -> 0.2 -> 0.55 down the chain.
  - All of it is disclosed ("FAB FLOOR RELAXED"), and every later checker grades against the new value.
- **Repro** (05 #3):
  ```bash
  python3 -X utf8 py_router/route_planes.py wk/gp14/05_interf_u/repro/placed.kicad_pcb wk/gp14/05_interf_u/repro/out/pour.kicad_pcb --nets GND --plane-layers B.Cu   # "rules.min_via_drill: None -> 0.6 mm", 0 vias on the board
  python3 -X utf8 py_router/route.py wk/gp14/05_interf_u/repro/out/pour.kicad_pcb wk/gp14/05_interf_u/repro/out/route.kicad_pcb --nets '*' --quick 2 --no-bga-zones --layer-costs 1.0 1.0 --direction-preference-cost 4000 --turn-cost 2000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.5 --power-nets VCC GND --power-nets-widths 0.5 0.5   # "via drill: 0.6 -> ...; 122 of 122 ... below the ORIGINAL 0.6mm"
  ```
  Edge half (11 #4):
  `python3 -X utf8 py_router/route_planes.py wk/gp14/11_daplink/repro/placed_s3.kicad_pcb /tmp/rp.kicad_pcb --nets GND --plane-layers B.Cu --board-edge-clearance 0.55`
- **Cost / "fine":** ~5 min each on 02, 05 and 11; ~3 min on 04; report noise on 12 and 13. 06 ships a
  project declaring a hole clearance the author never set.
- **Upstream:**
  - #1195 CLOSED: qfn_fanout lowered floors on a run that placed no via; same pattern (02, 05, 12).
  - #1170 CLOSED (02).
  - #1285 CLOSED (`--no-fix-drc-settings` still lowers `min_hole_clearance`), #1198, #1038 and #1217
    CLOSED (06, 13).
  - #1290 OPEN ("Some passes ignore --board-edge-clearance and net-class clearance (v0.23.1)"): nearest
    for 11's edge half.
- **Severity / category:** MEDIUM: disclosed, but authored floors are lost. Routing tool. Cross-ref H08
  (the edge pin flips a placement grade) and M12.

### M02 -- place_simple leaves error-graded decap limits broken, and the branch has no decap repair CLI (`--repair-decaps`, #1188, absent), so hand place_pose passes are needed

- **Boards (6):** 06 #3; 09 #2; 12 #8 (hand fix); 13 #2; 14 #6; 05 #1 (partial: a post-placement C1/R2
  nudge to meet claims the teammate wrote).
- **Defect:**
  - 13: 72 seeds at weight 10 and 100 never reached 0 errors. From r3 on it was always the same pins:
    U3 10/33 and U6 29/33, on the QFN sides facing the header rows. The only legal spots within 2.19 mm
    are in the QFN's fan-out halo.
  - 06: C27 (0805) sat 1.22 mm from U7 against a 1.0925 limit on 9 of 10 scoped re-anneals (weight
    100/300/1000, 60000 moves). The decap term pulls the cap to the VOS pin on U7's pin side, where the
    pad-bbox margin makes the limit unreachable.
  - 14: `set_limits` caps a pin limit wider than the 5 mm tether radius at "the radius past the limit",
    on the reasoning that any cap on the rail meets it. VDD_SNVS_IN has ONE cap, C20, so the pin sat
    22.34 mm away against 8.46, priced at 5.0, in 33 of 36 seeds.
  - 09: `decap_broken` 2..10 on the judged seeds, and still 0..5 with `--decap-limit-weight 30
    --claim-limit-weight 30`.
  - 12: 1-4 broken per judged seed.
- **Repro** (14 #6; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  python3 -X utf8 py_placer/place_simple.py $R/r1_fixed.kicad_pcb $R/out_s2.kicad_pcb --groups $R/r1_groups.json \
    --intent $R/r1_intent.json --seed 2 --json $R/out_s2.json | tail -1          # decap_broken 1, decap_limits 5.0
  python3 -X utf8 py_tools/check_floorplan.py $R/out_s2.kicad_pcb --intent $R/r1_intent.json | grep ERROR    # P12 22.34 mm from C20
  ```
  13 #2: `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/13_pico_ice_rev3/repro/r5_s6.kicad_pcb --intent wk/gp14/13_pico_ice_rev3/repro/intent_rows.json | grep ERROR`
- **Cost / "fine":**
  - 13: five hand passes, each costing routability (fix1's fast route went 9 -> 31).
  - 09: ~25 min (shared with M30).
  - 14: ~15 min, three moves.
  - 06: scoped re-anneals plus hand poses.
  - 12: two moves.
  - place_simple's seeds are "legal" throughout.
- **Upstream:** #1188 CLOSED: the repair exists but is not on this branch (13). #1249 CLOSED (a 3-pad
  regulator can never own a cap; 14). #1150 CLOSED. (my search) also #1066 and #1142 CLOSED, same family.
- **Caveat:** 06's 1.0925 mm limit comes from the given intent, so part of 06 may be the intent rather
  than the tool.
- **Severity / category:** MEDIUM. Placement tool.

### M03 -- Skill (plan-pcb-placement): no path when a round yields no usable seed, and silent on whether re-placements count toward `--rounds`

- **Boards (6):** 04 #10 bullet 1; 06 #7; 07 #10 bullet 1; 08 #9 bullet 1; 12 #8; 13 #6 bullets 2-3 (+
  GRADE 13).
- **Defect:** §3.5/3.6 say never to judge or keep an illegal seed, start the review loop from "the best
  fast route", and stop at the first clean fast route. They give no step for:
  - an empty judge.json (06);
  - every judged seed NOT BUILDABLE (04, 07). The skill also says a hand-moved part is moved back.
  - every judged seed failing the verifier's floorplan gate (12);
  - a declared pose the placer refuses, while §3.1 says a declared pose "needs no lock" (08);
  - placement-classified re-placements: are they rounds 4+? (13 ran 6 rounds.)
- **Repro:** `wk/gp14/06_rp2350_fpga_eensy_prePlane/r1/judge.json` (06 #7).
- **Cost / "fine":** teammates improvised and counted rounds differently. The underlying tool cost is in
  H02, H04, H07 and M02.
- **Upstream:** none ("all seeds illegal judge").
- **Severity / category:** MEDIUM: skill text, but it cost rounds.

### M04 -- The `--quick 2` judge does not predict the full route (vias and blocking)

- **Boards (4):** 01 #3; 02 #3 (judge half); 04 #10 bullet 2; 13 #3.
- **Defect:** §3.6 claims level 2 "picks seeds as well" as full routes.
  - 01: `--quick 2` skips the plane-fragility field (`"why": "--quick 2"`). The kept seed judged 0 vias /
    135.64 mm against a full route of 2 vias / 146.29 mm. Matching the judge needed
    `KICAD_PLANE_FRAGILITY_COST=0`, which then hit H09.
  - 02: the judge gave 3 vias against the full route's 16 under identical flags (Phase-3 tap vias).
  - 04: the full route added 30-40 vias on every seed (63->99, 59->92, 65->97, 55->106, 61->104),
    reversing the seed order.
  - 13: the same placement scored 8..42 blocking under small parameter changes, and quick -> full did
    not keep the order (r5/s6 quick 22 -> full 9). The best board came from a mid-pack seed.
- **Repro** (01 #3):
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/q2.kicad_pcb --nets '*' --quick 2 --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --json-out $RP/q2.route.json
  python3 -X utf8 py_tools/quick_score.py $RP/q2.kicad_pcb --route $RP/q2.route.json      # vias=0 copper_mm=135.64
  python3 -X utf8 py_router/route.py $RP/placed.kicad_pcb $RP/full.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0
  python3 -X utf8 py_tools/board_score.py $RP/full.kicad_pcb --quiet                        # vias=2 copper_mm=146.29
  ```
- **Cost / "fine":** 04: ~15 min of post-DONE full routes. 02: ~10 min of arms (with M21). 01 led to H09.
  04 and 13 themselves call it "a property, not a tool defect"; the defect is the skill's claim.
- **Upstream:** 01: none (#875 and #424 unrelated). 02: #658 CLOSED, #153 OPEN. 13: #504, #424 and #8
  unrelated.
- **Severity / category:** MEDIUM. Skill text (+ routing tool, for 01's skipped fragility field).

### M05 -- place_pose `rotate REF DEG` is absolute and pivots on the footprint origin; route_review's "turn 180" and the skill's "place_pose ... rotate" give no turn, a quarter turn or a body swing, and a no-op prints "Modified 1 footprint positions"

- **Boards (4):** 01 #2; 03 #2; 04 #3; 07 #9.
- **Defect:** `rotate` SETS the angle (`--relative` adds; `--help` says so on one line) and turns about
  the origin, which on THT axials is pad 1.
  - 01: R2 was already at 180, so the output was byte-identical, with exit 0 and "Modified 1 footprint
    positions" (alongside "unmoved", `"moved": []`). A batch of 10 "turns" gave 10 identical routes and
    nearly became a false finding. With `--relative`, the axials' bodies swing 7.62 mm: 6 of 10 were
    refused and 3 were written but NOT BUILDABLE.
  - 03: R207 90 -> 180 was refused (pad stack with Q201). `--relative` was written but NOT BUILDABLE.
    The intended pad swap is `set R207 152.2729 107.6242 --rot 270`: buildable, and it routed 809.75 ->
    781.94 mm.
  - 04: C8 not turned, and R39 270 -> 180, a quarter turn into R42's courtyard (0.082 mm2). The board
    shipped a KiCad `courtyards_overlap` error that only the verifier caught (see H11).
  - 07: R14 was refused (pad stack).
- **Repro** (03 #2):
  ```bash
  python3 -X utf8 py_tools/route_review.py wk/gp14/03_complex_hierarchy/repro/gap2_s6_routed.kicad_pcb        # "R207 ... (turn 180)"
  python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_abs.kicad_pcb rotate R207 180              # exit 4, pad stack Q201/R207
  python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_rel.kicad_pcb rotate R207 180 --relative   # written
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/03_complex_hierarchy/repro/gap2_rel.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb               # NOT BUILDABLE
  python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_set.kicad_pcb set R207 152.2729 107.6242 --rot 270
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/03_complex_hierarchy/repro/gap2_set.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb               # buildable
  ```
- **Cost / "fine":** 04: ~20 min, a shipped-then-superseded final chain and a second verifier call. 03:
  ~4 min. 07: ~1 min. 01: small. 03 suggests route_review print the pad-swap command and SKILL §3.6
  name it.
- **Upstream:** none (01, 03, 04, 07). (my search) "place_pose rotate", "rotate absolute relative",
  "route_review turn": nothing on point.
- **Severity / category:** MEDIUM. Placement tool + skill text.

### M06 -- converge.py record refuses the first board_score-scored row after the skill's quick_score rows ("graded FEWER components")

- **Boards (4):** 06 #5; 09 #3; 10 #5; 14 #11.
- **Defect:** quick_score's payload `{blocking, blocking_by: {broken: N}, quality}` declares no `ungraded`
  list, so `converge.ungraded_set` reads it as grading everything. board_score honestly lists
  impedance/length/net_widths as ungraded, so the full route's row looks like it graded fewer
  components: "this lap looks like an IMPROVEMENT only because it graded FEWER components ... Nothing
  was written." (exit 2). The skill prescribes quick_score for judge rows (§3.6 step 2) and board_score
  for full routes (§5.6) in the same ledger.
- **Repro** (06 #5; `R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`):
  ```bash
  rm -f $R/gap4_ledger.jsonl
  python3 -X utf8 py_placer/converge.py record --ledger $R/gap4_ledger.jsonl --board $R/s7_fast.kicad_pcb --kind completion --parent $R/input.kicad_pcb --lever "fast route" --score-file $R/quick.score.json
  python3 -X utf8 py_placer/converge.py record --ledger $R/gap4_ledger.jsonl --board $R/final_copy.kicad_pcb --kind completion --parent $R/s7_fast.kicad_pcb --lever "full route" --score-file $R/board.score.json   # exit 2, nothing written
  ```
- **Cost / "fine":** ~10 min each on 09, 10 and 14.
- **Workarounds:**
  - 09, 10: re-score the fast route with board_score and record that row first.
  - 06, 14: record with a quick_score-shaped payload.
  - 14: record the first full route `--rejected`.
- **Upstream:** none ("quick_score converge commensur", "converge record ungraded quick_score",
  "FEWER components quick"). (my search) "converge record quick_score", "ungraded_set": nothing.
- **Severity / category:** MEDIUM. Placement tool (ledger) / grader payload format.

### M07 -- `--rip-existing-nets <net>` is a no-op on a connected net, yet route.py's own Hint prescribes it (and `--force-reroute` did not join the island)

- **Boards (4):** 04 #9; 03 #1 (retry half); 11 #6; 12 #6.
- **Defect:**
  - 04: the plane finalize printed `GND: (152.05,114.91)<->(151.15,114.93) FAILED (exact-fill strap
    unroutable) ... Hint: ... Retry with --rip-existing-nets 'Net-(IC5A-IN-)'`.
  - Following the hint routed 0 nets ("WARNING: already connected ... pass --force-reroute"). With
    `--force-reroute` there were 71 vias and GND still had 2 components.
  - 03, 11 and 12: `--rip-existing-nets` on the net carrying a stub or tail is likewise a no-op. On 03
    `--force-reroute` at grid 0.1 laid the identical stub again.
- **Repro** (04 #9, as the teammate wrote it): "route `$P/pour_s3.kicad_pcb` as in gap 5 with `--via-cost 200`
  (or replay `$R/opt/sweep/s2_v200/` from `r1/s2_fixc.kicad_pcb`), then the two retries above"
  (`--nets GND 'Net-(IC5A-IN-)' --rip-existing-nets 'Net-(IC5A-IN-)'`, then with `--force-reroute`).
- **Cost / "fine":** 04: ~5 min, and the low-via arms (v150-v300) were abandoned.
- **Upstream:** none (04: #677 different). (my search) "rip-existing-nets already connected" returns
  #1215, #1156, #600 and #162: none on the hint.
- **Severity / category:** MEDIUM. Routing tool.

### M08 -- place_simple's edge seat says "no room along the <edge>" for connectors that fit, and places them in the interior

- **Boards (3):** 02 #1; 11 #1 (+ #8 helper); 08 #7 (SW501 half).
- **Defect:**
  - 02: a DB25 J1 declared with no `overhang_mm` is seated flush in courtyard currency. Its 54.1 mm
    flange courtyard is wider than the 43.18 mm edge, so the band reads >= 11.43 mm at every pose.
    `_seat_coord`'s bisection never leaves the centre and `_free_stretches` finds nothing, which is
    reported as "no room". place_simple then "placed as any other part" with `illegal: []` and exit 0,
    while check_floorplan gives 2 ERRORs (nearest edge north; mating face north).
  - 11: the Harwin right-angle header draws its pins as silk-only pads,
    `pad "" smd rect (size 6 0.76) (layers "F.SilkS")`. `edge_seat._pad_box` keeps every non-NPTH pad, so
    the seat holds those silk pads 0.55 mm inside the edge. The pad box comes out as
    `(-6.775, -5.58, 6.895, 5.58)` while the copper ends at x -4.275, and the seat's band is 0.38 against
    a 7.0 minimum. The "impossible" pose is legal and grades 7.006, pass.
  - 08: SW501 (3.7 x 4.6 mm) gets "no room" on a straight 44.6 mm east edge; a hand pose is legal and
    buildable. The teammate's unverified suspicion is that the edge span comes from `board_bounds`
    (corner ears at x 136.25).
- **Repro** (11 #1):
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb /tmp/rep1.kicad_pcb \
      --groups wk/gp14/11_daplink/repro/groups.json --intent wk/gp14/11_daplink/repro/intent_edges.json --seed 1
  python3 -X utf8 wk/gp14/11_daplink/helpers/seat_probe.py wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb \
      wk/gp14/11_daplink/repro/groups.json wk/gp14/11_daplink/repro/intent_edges.json J3
  ```
  02 #1:
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gp14/02_sonde_xilinx/repro/sonde_xilinx.kicad_pcb \
      wk/gp14/02_sonde_xilinx/repro/out/gap1_s0.kicad_pcb --groups wk/gp14/02_sonde_xilinx/repro/groups.json \
      --intent wk/gp14/02_sonde_xilinx/repro/intent_given.json --seed 0      # WARNING ... no room; exit 0
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/02_sonde_xilinx/repro/out/gap1_s0.kicad_pcb \
      --intent wk/gp14/02_sonde_xilinx/repro/intent_given.json               # 2 x [ERROR] edge_connector J1
  ```
- **Cost / "fine":**
  - 11: ~25 min, and J2/J3 were hand-locked so they can no longer slide.
  - 02: 15-20 min to derive `intent_seat.json` overhang bands.
  - 08: ~10 min (with M16).
  - On 02, place_simple said exit 0 and `illegal: []`.
- **Workarounds:** 02 hand-measured `overhang_mm` bands. 11 `helpers/seat_probe.py` is the only tool that
  says WHY a seat failed. 08 and 11 used `place_pose set ... lock`.
- **Upstream:** 02 found none (#987, #1155, #1240/#1242 closed, different). 11 lists #1257 CLOSED, whose
  pad-box check is presumably where silk pads entered. 08 lists #1242, #1155 and #706. (my search)
  "edge seat no room": nothing.
- **Severity / category:** MEDIUM: check_floorplan catches it, but the reason is false. Placement tool.

### M09 -- place_pose's `legal` is false on every pose of boards with copper on the outline by design, or a slightly non-rectangular outline (and it writes NOT BUILDABLE poses with exit 0)

- **Boards (3):** 03 #4; 05 #4; 06 #10 bullet 3.
- **Defect:** `no_worse` is the only usable verdict on these boards.
  - 03: one Edge.Cuts corner sits at y=51.816 against 51.8 elsewhere, so the outline is not an exact
    axis-aligned rectangle. The analytic pad-to-edge check is skipped and all 165 pads are "unmeasured"
    ("outline uses sampled perimeter check"), so `legal` is false on every call.
  - 05: BUS1's 62 ISA edge fingers are graded against a "fixed default" 0.55 mm edge clearance
    (`BUS1.61: edge shortfall 0.296 mm`), although the board's `min_copper_edge_clearance` is 0. A
    courtyard-blocking C1<->R2 (0.51 mm2) pose was written with exit 0.
  - 06: U8's castellated pads give `pad_edge_conflicts_after: 33`.
- **Repro** (05 #4):
  ```bash
  python3 -X utf8 py_placer/place_pose.py wk/gp14/05_interf_u/repro/r3_s0.kicad_pcb wk/gp14/05_interf_u/repro/out/nudge.kicad_pcb set C1 131.4 60.9 --rot 180   # legal false (pad_edge_conflicts 62: BUS1 fingers), exit 0, written
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/05_interf_u/repro/out/nudge.kicad_pcb --baseline wk/gp14/05_interf_u/fixed.kicad_pcb                # NOT BUILDABLE: C1 <-> R2 courtyard 0.51 mm2, GATES
  ```
  03 #4:
  `python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb /tmp/pp_probe.kicad_pcb --dry-run set R207 152.2729 107.6242 --rot 270 | grep -o '"legal": [a-z]*\|"pad_edge_unmeasured_after": [0-9]*'`
- **Cost / "fine":** 05: ten hand poses checked one by one with check_assembly (~4 min). 03: ~2 min. 06:
  none.
- **Upstream:** none (03 "sampled perimeter"; 05 nearest #1098). (my search) #967 CLOSED (place_pose
  reports an edge-clearance floor its legality grader does not enforce): same family.
- **Severity / category:** MEDIUM. Placement tool.

### M10 -- check_floorplan exits 4 (`"pass": false`) on a finished board with 0 errors

- **Boards (3):** 01 #4; 02 #5; 13 #6 bullet 4.
- **Defect:**
  - 01, 13: the given intent leaves rules dark and OWED (zone_containment and legality; 13 also
    zone_side), giving `rules_dark_undispositioned` and exit 4.
  - 02: the emitter withheld three budgets (`decaps.max_distance_mm`, `oob_count`, `overlap_area`)
    because the source was a pile (#1103). The result is "NOT FULLY GRADED: 3 budget_abstained" and an
    exit of 4 forever, on any board staged from a pile.
  - The verifier brief grades "0 errors". The campaign's grade.py records `floorplan_pass: false` next
    to `floorplan_errors: 0` (13).
- **Repro** (02 #5):
  ```bash
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/02_sonde_xilinx/repro/final.kicad_pcb \
      --intent wk/gp14/02_sonde_xilinx/repro/intent_seat.json --allow-routed ; echo $?     # 0 errors, exit 4
  ```
- **Cost / "fine":** 1-2 min of reading each. A script gating on the exit code would fail every board of
  the campaign.
- **Upstream:** none ("check_floorplan OWED exit 4", "rules_dark_undispositioned", "NOT FULLY GRADED exit 4
  pile budgets"). #1103 is the withholding; 13 lists #997 and #959 CLOSED. (my search) "check_floorplan
  exit code": nothing on point.
- **Severity / category:** MEDIUM. Grader/checker.

### M11 -- No tool runs the skill's seed-judging chain (or a post-DONE lap); each board hand-writes one

- **Boards (3):** 08 #9 bullet 2; 11 #9; 14 #13.
- **Defect:** SKILL §3.6 step 1 has the agent run the board's routing chain identically on each
  judge.json seed, copy the result out and run quick_score. No repo tool sequences a chain over a seed
  list. On 08 that is a 9-command chain per seed.
- **Repro:** `bash wk/gp14/11_daplink/helpers/judge_chain.sh wk/gp14/11_daplink/r1 3` (11 #9; helper
  usage).
- **Cost / "fine":** minutes per board, and a risk of non-identical chains across seeds.
- **Workarounds:** `helpers/judge_chain.sh` (08, 11, 14); 08 `exp_chain.sh` and `final_chain.sh`; 14
  `opt_lap.sh`.
- **Upstream:** none ("judge runner"). (my search) "judge chain runner seeds": nothing.
- **Severity / category:** MEDIUM. Skill text / missing tool.

### M12 -- The default routing chain (escalation fab / fab-tier auto, clearance descents) spends authored floors it did not need, and the writeback lowers the project so every checker reads clean; `--clearance-ceiling` bounds neither descents nor qfn_fanout's default

- **Boards (3):** 12 #5 and #9; 11 #3; 09 #6.
- **Defect:**
  - 12: the skill's chain with the board's own sizes escalated 11 plane taps standard -> advanced
    (0.3/0.15 vias), descended clearance to 0.127 and laid one track at 0.1496. The project was then
    written down to match: `min_via_diameter` 0.6 -> 0.45, `min_through_hole` 0.3 -> 0.2, Default
    0.15 -> 0.127.
  - 12: board_score with the spec flags placement §1 requires shows `undersized=3`.
    `--escalation board --fab-tier standard` held the floors (0 undersized).
  - 11: the same placement routes complete at the authored floors (arm C: 0 escalations, vias 0.5/0.3,
    Default 0.2, 56 vias). The default chain put 19 features on 6 nets below the requested size, with 14
    escalations and 61 vias.
  - 09: one 0.1442 mm descent on /D- in the diff step re-graded every Default net. A later descent on
    +1V8 took the board to 0.127 under `--clearance-ceiling 0.15`.
  - 12 #9: qfn_fanout without `--clearance` used 0.1, the fab floor rather than the board's 0.15
    Default class. It wrote Default 0.15 -> 0.1 and `min_hole_clearance` 0.25 -> 0.1, and
    `--clearance-ceiling 0.15` printed "no cap applied -- --clearance 0.1 is already at or below it".
- **Repro** (12 #5):
  ```bash
  python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/repro/v1_step2a.kicad_pcb wk/gp14/12_steppenprobe/repro/v1_out.kicad_pcb \
      --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.25 \
      --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 1.5
  #  -> "Design rules [--escalation fab, --fab-tier auto]: ... below the requested size", WARNING plane tap ... escalated standard->advanced
  python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/repro/v1_out.kicad_pcb --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3
  ```
- **Cost / "fine":**
  - 12: one full re-route, the +1V8 corridor fight the honest floors exposed, and a judge run redone
    (#9).
  - 11: ~10 min, and arm A rejected.
  - 09: none directly.
  - It is disclosed (`Design rules [...]`); downstream graders then read clean.
- **Upstream:** #857 CLOSED, #1262 OPEN (`--escalation board` clearance misreport), #1160 CLOSED, #1287
  CLOSED, #1195 CLOSED (qfn_fanout). None says the skill chain should hold the declared floors.
- **Severity / category:** MEDIUM. Routing tool + skill text. Cross-ref M01 and M24.

### M13 -- board_score and check_orphan_stubs report clean on boards check_complete refuses for weird copper

- **Boards (3):** 03 #1 (second point); 04 #4; 06 #4.
- **Defect:** board_score has no weird-copper component, so it reports BLOCKING=0 while check_complete
  reads INCOMPLETE (weird_copper). On 04, check_orphan_stubs says "NO ORPHAN STUBS FOUND!" with a
  3.677 mm dangling segment on the board. The skill's §5.6 ledger example scores with board_score only,
  so a run that stops there calls the board DONE.
- **Repro** (04 #4; `P=wk/gp14/04_multichannel_mixer/repro`):
  ```bash
  python3 -X utf8 py_tools/board_score.py $P/s2r_v125_step4.kicad_pcb --intent $P/intent.json --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --baseline $P/pile.kicad_pcb --quiet   # BLOCKING=0
  python3 -X utf8 py_tools/check_orphan_stubs.py $P/s2r_v125_step4.kicad_pcb    # NO ORPHAN STUBS FOUND!
  python3 -X utf8 py_router/check_weird.py $P/s2r_v125_step4.kicad_pcb          # dangling-end 3.677 mm + stacked-copper
  python3 -X utf8 check_complete.py $P/s2r_v125_step4.kicad_pcb --intent $P/intent.json --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --baseline $P/pile.kicad_pcb   # INCOMPLETE -- weird_copper
  ```
- **Cost / "fine":** shared with H01/H03.
- **Upstream:** 04 lists #1186 CLOSED (the opposite direction). Nothing covers the grader gap ((my
  search) "board_score weird copper": nothing).
- **Severity / category:** MEDIUM. Grader/checker.

### M14 -- route_planes replaces an existing zone's designer settings and only says "with new parameters"

- **Boards (2):** 02 #6; 05 #5.
- **Defect:**
  - 02: clearance 0.508 -> 0.254; thermal 0.508/0.508 -> solid (`connect_pads yes`), reliefs 0.2;
    `min_thickness` 0.254 -> 0.1; polygon 105.41..182.88 -> 103.5..183.5. The 0.1 min thickness lets the
    refilled pour form 0.1654 and 0.1111 mm necks.
  - 05: clearance 0.5 -> 0.254, `min_thickness` 0.2 -> 0.1, thermal -> solid, thermal 0.508 -> 0.2. The
    result is 13 GND webs narrower than 0.2 mm. Re-pouring at 0.2 cleared them but left a net broken.
  - The routing skill's Step 1 sends you there ("a bare pour", "do not set --thermal-relief").
- **Repro** (02 #6):
  ```bash
  python3 -X utf8 py_router/route_planes.py wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb \
      wk/gp14/02_sonde_xilinx/repro/out/g6_planes.kicad_pcb --nets GND --plane-layers B.Cu    # "Replacing existing zone ... with new parameters"
  grep -A12 '(zone$' wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb | head -14          # input: clearance 0.508, min_thickness 0.254, thermal 0.508
  grep -A12 '(zone$' wk/gp14/02_sonde_xilinx/repro/out/g6_planes.kicad_pcb | head -14        # output: connect_pads yes, clearance 0.254, min_thickness 0.1
  ```
- **Cost / "fine":** 02: ~5 min, and the verifier spent more. 05: one arm (~2 min) plus a report caveat.
- **Upstream:** #487 and #531 CLOSED, general (02); #1056 nearest (05).
- **Severity / category:** MEDIUM. Routing tool (+ skill text).

### M15 -- place_simple's group hints saturate: `apart` (and `edge`, `near`) between groups that already touch is a constant with no gradient

- **Boards (2):** 10 #2; 14 #7 (apart half).
- **Defect:** the hint is `weight * max(0, 3 - least gap between ANY member of A and ANY member of B)`
  (`placement/simple.py` `hint_cost`/`_hint_value`). When two groups interleave, the least gap is 0 at
  every pose, so the term is the constant 15.0.
  - 10: seeds 2 and 3 of the hinted round are pose-for-pose identical to round 1 (0 of 264 parts
    moved), with `final.cost` exactly 15.0 higher (10831.9 -> 10846.9).
  - The same shape applies to `edge` (only the nearest member counts) and `near` (0 once any two
    members touch).
  - 14: `apart` between the straps and the core still left 10-15 straps under U1.
- **Repro** (10 #2):
  `python3 -X utf8 py_placer/place_simple.py wk/gp14/10_glasgow_revC/repro/gap2_fixed.kicad_pcb /tmp/gap2_s2.kicad_pcb --groups wk/gp14/10_glasgow_revC/repro/gap2_groups_apart.json --intent wk/gp14/10_glasgow_revC/repro/gap2_intent_v2.json --seed 2`
  and the same with `--groups wk/gp14/10_glasgow_revC/repro/gap2_groups_v1.json`: identical poses,
  costs 15.0 apart.
- **Cost / "fine":** 10: a placement round (~7 min of 4 cores) killed. 14: one round. Nothing in the
  output says the hint had no gradient.
- **Upstream:** none ("apart hint", "apart groups no effect", "apart term constant"; only unrelated hits
  and #548).
- **Severity / category:** MEDIUM. Placement tool.

### M16 -- Edge-part classification: a declared `class` is ignored, and DC jacks, slide switches, HDMI and RJ45 get no class (no edge seat, no emitted entry)

- **Boards (2):** 07 #4; 08 #7 (class half).
- **Defect:**
  - 07: `classify_part` gives DC1 (`DC-IN-SMD_DC-045A-13A`) and PWR_SW1 (`SW-TH_TK-6580A8-1`) None, so
    both are "placed as any other part". USB1 is `edge_receptacle` and SW1 `edge_actuator`.
  - 08: J501, a full-size HDMI declared `"class": "edge_receptacle"`, gets "NOTE: J501 ... is not an edge
    part (no part class): placed as any other part", and the seed put the HDMI mouth facing into the
    board.
  - 08: `--declare-classes` wrote no entry for J1 (Kycon RJ45 MagJack) or J501.
- **Repro** (07 #4):
  ```
  cd py_placer && python3 -X utf8 -c "import sys; sys.path[:0]=['../py_router','.']; from kicad_parser import parse_kicad_pcb; from placement.part_class import classify_part; p=parse_kicad_pcb('../wk/gp14/07_One-Air-Max/repro/input.kicad_pcb'); print({r: classify_part(p.footprints[r], r).name for r in ('DC1','PWR_SW1','USB1','SW1')})"
  #   -> {'DC1': None, 'PWR_SW1': None, 'USB1': 'edge_receptacle', 'SW1': 'edge_actuator'}
  ```
  08 #7:
  `python3 -X utf8 py_placer/place_simple.py wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s7.kicad_pcb --groups wk/gp14/08_CM5_MINIMA_3/repro/gap1_groups.json --intent wk/gp14/08_CM5_MINIMA_3/repro/gap1_intent.json --seed 7 | grep -E "J501|SW501"`
- **Cost / "fine":** 07: ~5 min plus hand poses (which then fed H05's waivers). 08: ~10 min (shared with
  M08).
- **Upstream:** 07 found none; 08 lists #1242, #1155 and #706 CLOSED. (my search) #1176 CLOSED (part_class
  reads a DSUB as a mounting hole): same family.
- **Severity / category:** MEDIUM. Placement tool.

### M17 -- qfn_fanout stubs end as dangling copper after routing (stubs on plane nets the skill does not exclude; a stub laid across and past a same-net pad)

- **Boards (2):** 12 #6; 06 #6.
- **Defect:**
  - 12: U1 pin 64's +1V8 stub runs (118.054, 77.993) -> (116.300, 79.800), across C11's +1V8 pad 1 and
    0.27 mm past its edge. After routing it shows as a check_weird dangling-end (1.203 mm), plus
    kicad-dangling and a check_orphan_stubs orphan. Two cleanup laps did not remove it, and the
    `--rip-existing-nets` retry was a no-op (M07). The fanout had said escaped 31/31, drc_grazes 0.
  - 06: the skill's qfn_fanout examples carry no `--nets`; Step 1b excludes plane nets for bga_fanout
    only. Stubs on GND/+3V3 pins are left free once route.py welds those pins to the pours:
    `dangling-end: GND (F.Cu) at (143.300, 111.600)`. With `--nets '*' '!GND' '!+3V3'` they went away.
- **Repro** (12 #6):
  ```bash
  python3 -X utf8 py_router/qfn_fanout.py wk/gp14/12_steppenprobe/repro/v3_step1.kicad_pcb --component U1 \
      --nets '*' '!GND' '!+3V3' --output wk/gp14/12_steppenprobe/repro/v3_step1b_out.kicad_pcb \
      --clearance 0.15 --track-width 0.15 --escalation board --fab-tier standard
  # +1V8 segment (118.0538, 77.9925) -> (116.3, 79.8); C11 pad 1 spans x 116.57..117.45
  ```
  06 #6: `python3 -X utf8 py_router/check_weird.py $R/v2_qfn_plane_stubs.kicad_pcb` -> `dangling-end: 2`
  (`R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`).
- **Cost / "fine":** 12: two laps and a chain variant; the fix was to keep +1V8 out of the U1 fanout.
- **Upstream:** none specific (#601 and #84 CLOSED are route.py producers). (my search) #845 and #846
  CLOSED are underpad-stub issues, different.
- **Severity / category:** MEDIUM. Routing tool + skill text.

### M18 -- kicad_drc_compare `--baseline` misreports boards placed from a pile

- **Boards (2):** 03 #3; 07 #7.
- **Defect:**
  - 03: the output opens with "FOUND 729 DRC VIOLATIONS: PAD-PAD violations (729) -- 536 in CONTACT".
    Those are the baseline pile's violations (pads at y ~136-145 mm, south of the outline). Only the
    trailing summary is about the graded board ("kicad=0 check_drc=0 ... CONSISTENT").
  - 07: the baseline is subtracted by position, so footprint-inherent findings on moved parts read as
    router-introduced. Examples: Q1/Q2 (CSD18534 PQFN) drain pads overlapping a net-less EP 9; F2, a
    PCB-trace fuse whose fp_line touches both its pads. The report says
    "kicad=8 (+2 pre-existing on input, subtracted) ... kicad_only=8 DIVERGED", and the same 8 appear on
    the unrouted placement.
- **Repro** (03 #3):
  `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gp14/03_complex_hierarchy/repro/gap3_final.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap3_baseline_pile.kicad_pcb | head -12`
  07 #7: `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gp14/07_One-Air-Max/kicad_drc/placed.kicad_pcb --baseline wk/gp14/07_One-Air-Max/repro/input.kicad_pcb`
- **Cost / "fine":** ~3 min each.
- **Upstream:** none (03: #405 and #450 are about DRC content). (my search) "kicad_drc_compare baseline":
  nothing on point.
- **Severity / category:** MEDIUM: a misleading verdict. Grader/checker.

### M19 -- KiCad-only DRC items no repo checker grades: connection_width webs and starved_thermal

- **Boards (2):** 04 #6 (second half); 06 #9 (connection_width half).
- **Defect:**
  - 04: on every routed board there are 10-12 `connection_width` items under `min_connection` 0.3. They
    are GND pour necks down to 0.244 mm (the input zone's own `min_thickness` 0.25 is below its own 0.3
    rule) and one router T-joint at a via (0.148 mm, /CH1/OUT).
  - 04: two `starved_thermal` GND pads (IC1.4, IC2.4: 1 spoke of 2).
  - 04: kicad_drc_compare prints the connwidth count but still says CONSISTENT.
  - 06: CONNWIDTH at J1's D+ pad (147.55, 94.85), <0.075 mm. check_weird (narrow-pad-joint 0), check_drc
    and check_complete all call the board clean. These are KiCad warnings on 06.
- **Repro** (04 #6, second line):
  `python3 -X utf8 tests/stress/kicad_drc_compare.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb`
  (`P=wk/gp14/04_multichannel_mixer/repro`). 06 #9:
  `python3 -X utf8 tests/stress/kicad_drc_compare.py $R/final_copy.kicad_pcb --baseline $R/input.kicad_pcb`
  (needs `/Applications/KiCad/KiCad.app/Contents/MacOS` on PATH).
- **Cost / "fine":** found only by the verifier's KiCad cross-check.
- **Upstream:** #547 CLOSED (tap landings churn connection_width webs) for 06. Nothing on starved_thermal.
  (my search) #1161 and #1187 CLOSED (connection_width web tests in check_weird): related.
- **Severity / category:** MEDIUM. Grader/checker.

### M20 -- The skills ship the pour unfilled: KiCad opens the DONE board with unconnected items

- **Boards (2):** 01 #5; 02 ("Not a gap" note).
- **Defect:** neither skill uses `--write-fill` or `fill_for_delivery`. The repo's graders refill
  themselves (check_connected's "KiCad refill cross-check").
  - 01: plain `kicad-cli pcb drc` (no `--refill-zones`) on the shipped file finds 6 unconnected items,
    every GND pad. With `route.py --write-fill` (#910) it finds 0, and the tracks are unchanged.
  - 02: 18 phantom GND opens without a refill.
- **Repro** (01 #5):
  ```bash
  RP=wk/gp14/01_ecc83-pp_v2/repro
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-all -o $RP/final_kicad_drc.json $RP/final_copy.kicad_pcb     # "Found 6 unconnected items" (unfilled first final)
  /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-all -o $RP/final2_kicad_drc.json $RP/final2_copy.kicad_pcb   # "Found 0 unconnected items" (--write-fill)
  ```
- **Cost / "fine":** the verifier noted it on 01. check_connected says "ALL NETS FULLY CONNECTED!" and
  check_complete DONE.
- **Upstream:** #910 CLOSED added the opt-in flag; nothing makes the skills use it.
- **Severity / category:** MEDIUM: a documented default, but it is what the user opens. Skill text.

### M21 -- The routing skill's 2-layer recipe leaves free quality: default via/layer costs on THT boards, and vias in SMD pads without `--same-net-pad-clearance`

- **Boards (2):** 02 #3; 11 #7.
- **Defect:**
  - 02: the recipe as written (`1.0 3.0`, via cost 75) gives 16 vias / 539.07 mm.
    `--layer-costs 1.0 1.0 --via-cost 600` gives 0 vias / 535.08 mm, since every THT pad is already a
    layer change. Via cost appears only in the "2-Layer Through-Hole Bus Boards" section (150).
  - 11: default routing put 15 vias in pads, some of them signal pads (C6.1 /OSCOUT, U2.12 /TGT_RX),
    each stamped IPC-4761 Type VII on a cheap 2-layer probe. `--same-net-pad-clearance 0.1` gives 0
    via-in-pad (56 vias vs 55). The skill names that flag only under route_planes options.
- **Repro** (02 #3):
  ```bash
  P=wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb; O=wk/gp14/02_sonde_xilinx/repro/out
  python3 -X utf8 py_router/route_planes.py $P $O/g3_planes.kicad_pcb --nets GND --plane-layers B.Cu
  python3 -X utf8 py_router/route.py $O/g3_planes.kicad_pcb $O/g3_default.kicad_pcb --nets '*' --power-nets GND VCC '/PWR_3,3-5V' \
      --power-nets-widths 0.635 0.635 0.635 --track-width 0.254 --via-size 0.889 --via-drill 0.508 --layers F.Cu B.Cu --layer-costs 1.0 3.0   # 16 vias
  python3 -X utf8 py_router/route.py $O/g3_planes.kicad_pcb $O/g3_via600.kicad_pcb --nets '*' --power-nets GND VCC '/PWR_3,3-5V' \
      --power-nets-widths 0.635 0.635 0.635 --track-width 0.254 --via-size 0.889 --via-drill 0.508 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 600   # 0 vias
  ```
- **Cost / "fine":** 02: ~10 min of arms. 11: ~5 min (a third arm). Both routes were DONE.
- **Upstream:** 02 lists #658 CLOSED and #153 OPEN; 11 found none. (my search) #581 CLOSED (the option to
  avoid via-in-pad on SMD pads) and #1025 CLOSED wontfix (an explicit via-in-pad policy).
- **Severity / category:** MEDIUM. Skill text.

### M22 -- `--quick 2` skips the plane finalize, so judge-time tools count poured-net pads open and the round stop cannot fire on boards with pours

- **Boards (2):** 10 #8; 07 #10 bullet 3.
- **Defect:**
  - 10: every one of 18 judged fast routes left poured-net pads open (GND 1-57, +3V3 0-26; r3/s4: +3V3 3
    and GND 5 of its 25). quick_score's `blocking` therefore mixes the placement signal with plane-pad
    noise of the same size, and the loop always runs all rounds.
  - 07: route_review under `--quick 2` reports "GND (poured): disconnected at C1, C11, ...", while
    quick_score scores it 0.
  - Unexplained difference: on 07 quick_score leaves the poured net out, while on 10 GND/+3V3 pads
    count in `pad_pairs_open`. 10's pours were kept from the source; why the two differ was not checked.
- **Repro** (10 #8):
  `python3 -c "import json;d=json.load(open('wk/gp14/10_glasgow_revC/r3/s4_route/route.json'));print([x for x in d['pad_pairs_open'] if x['net'] in ('GND','+3V3')])"`
- **Cost / "fine":** 10: no lost time beyond the rounds the skill runs anyway, but the ranking is partly
  noise. 07: reader confusion.
- **Upstream:** none ("quick 2 plane finalize judge blocking", "quick_score poured pads").
- **Severity / category:** MEDIUM. Grader/checker + skill text.

### M23 -- manifest_to_plan rejects a command whose relative intent path exists, prunes the steps upstream of it, and reports "1 command(s) skipped"

- **Boards (2):** 11 #10; 12 #11.
- **Defect:** the plan's first line `cd`s to the worktree root, but the converter resolves the relative
  intent path elsewhere:
  `command 8: place_fanout_clearance.py refuses its arguments after parsing: cannot load intent wk/gp14/11_daplink/intent_edges.json: [Errno 2] No such file`.
  - 11: the dependency pruner then silently drops route_planes and the fanout too. The JSON holds
    `route_diff, route, route, route` while the summary says one command was skipped. The recorded
    manifest (absolute paths) converts to all 7 steps.
  - 12: the cap pass is lost (6 steps written).
- **Repro** (11 #10):
  `python3 -X utf8 tests/stress/manifest_to_plan.py wk/gp14/11_daplink/repro/m2p/daplink_plan.sh -o /tmp/m2p_from_plan.json`
- **Cost / "fine":** ~5 min (11), small (12). The GUI plan JSON is wrong; the board and the redo manifest
  are unaffected.
- **Upstream:** none ("manifest_to_plan dropped steps relative intent", "manifest_to_plan prune",
  "manifest_to_plan place_fanout_clearance"; #1067 is different). (my search) "manifest_to_plan relative
  path": nothing.
- **Severity / category:** MEDIUM. Routing tool (plan converter).

### M24 -- Board Setup `min_clearance` above the Default netclass is ignored by check_assembly/place_pose and by the `--clearance-ceiling` chain spelling

- **Boards (1):** 04 #2 and #7.
- **Defect:** the Default class is 0.2 and Board Setup `min_clearance` 0.3. KiCad, check_drc and
  board_score grade 0.3 (since #1210).
  - check_assembly and place_pose grade at 0.2 ("grading at clearance 0.2mm [board netclass]").
  - Asked for 0.3, check_assembly prints a false note: "--clearance 0.3mm overrides this board's own
    Default net-class clearance ... STRICTER than the board asks for".
  - Two pads moved by the fixer sat 0.24-0.25 mm apart, passed, and surfaced after a full route as
    board_score drc=2.
  - #7: the chain spelling `--clearance-ceiling 0.3` caps at min(class 0.2, 0.3) = 0.2. The run routes at
    0.2 and lowers `rules.min_clearance` 0.3 -> 0.2. Honouring the board's floor needed a bare
    `--clearance 0.3`.
- **Repro** (04 #2; `P=wk/gp14/04_multichannel_mixer/repro`):
  ```bash
  python3 -X utf8 py_tools/check_assembly.py $P/s3_fix_at02.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json   # buildable (blocking 0), "grading at clearance 0.2mm [board netclass]"
  python3 -X utf8 py_router/check_drc.py $P/s3_fix_at02.kicad_pcb                                                            # FOUND 2: PAD-PAD C39.2<->C32.1, C5.2<->C6.1
  python3 -X utf8 py_tools/check_assembly.py $P/s3_fix_at02.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json --clearance 0.3   # prints the false "STRICTER than the board asks for" note
  ```
- **Cost / "fine":** one wasted full route, a second fixer pass on six seeds and a re-judge (~8 min).
- **Upstream:** #1210 CLOSED fixed check_drc and board_score only; #1160, #1287 CLOSED. (my search)
  "check_assembly min_clearance": #1210 only.
- **Severity / category:** MEDIUM. Grader/checker + skill text.

### M25 -- route.py's end-of-run re-grade reports a clean run while the exact fill has GND in pieces

- **Boards (1):** 04 #5.
- **Defect:** route.py reports "Multi-point: 177/177 pads connected", "Recovered after a summary reported
  them failing: 2", `JSON_SUMMARY_MIN failed 0, multipoint_deficit 0`.
  - Yet the same run's finalize had logged `GND: exact-fill verdict OPEN`, and the oracle links on GND
    had FAILED.
  - check_connected: GND unconnected per KiCad refill, in 5 components; board_score broken=1.
  - 23 of 33 post-DONE routes shipped GND in pieces, and 21 of those printed `failed 0`.
  - The final re-grade credits the fill model, not the exact fill.
- **Repro** (04 #5; `P=wk/gp14/04_multichannel_mixer/repro`):
  ```bash
  python3 -X utf8 py_router/route.py $P/pour_s3.kicad_pcb $P/A3_out.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 150 --json-out $P/A3_out.json
  python3 -X utf8 py_router/check_connected.py $P/A3_out.kicad_pcb     # GND UNCONNECTED per KiCad refill, 5 components
  ```
- **Cost / "fine":** low, since board_score caught every one. Anyone trusting `JSON_SUMMARY_MIN` would
  ship a broken ground.
- **Upstream:** #572 CLOSED, the same pattern (model credit clearing an oracle-open link).
- **Severity / category:** MEDIUM. Routing tool.

### M26 -- board_score `blocking` ties a 17-pad rail with no copper with one stranded pad; the skill's tie-break then prefers the rail-less board

- **Boards (1):** 09 #4 (+ GRADE 09).
- **Defect:**
  - Scratch B s3: `BLOCKING=1 (unrouted=1 broken=0) vias=117 copper_mm=704.04`. Its +3.3V (17 pads,
    every VCC33 pin of U1) is wholly unconnected.
  - Shipped board: `BLOCKING=1 (unrouted=0 broken=1) vias=132 copper_mm=773.42`, with one pad (U1.37)
    off its net.
  - The lexicographic rule picks B s3, whose fewer vias and less copper are exactly the missing rail.
- **Repro** (09 #4):
  ```
  python3 -X utf8 py_tools/board_score.py wk/gp14/09_StickHub/repro/g4_rail_missing.kicad_pcb --quiet
  python3 -X utf8 py_tools/board_score.py wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --quiet
  python3 -X utf8 py_router/check_connected.py wk/gp14/09_StickHub/repro/g4_rail_missing.kicad_pcb   # +3.3V (17 pads) unrouted
  ```
- **Cost / "fine":** a judgement call against the skill's own rule.
- **Upstream:** none.
- **Severity / category:** MEDIUM. Grader/checker (+ skill tie-break).

### M27 -- route_diff's GND return vias break the hole-to-hole floor, even with `--hole-to-hole-clearance` given

- **Boards (1):** 08 #4.
- **Defect:** two GND return vias beside the DPHY0 clock vias, at (96.80, 52.47) and (97.00, 52.16), give
  check_drc VIA-DRILL-HOLE with a 0.038 mm overlap against `min_hole_to_hole` 0.25.
  - It happened in three chains, including with the explicit flag.
  - On seed 9 (204 vias) the overlap is 0.016 mm, which made that seed unshippable.
  - `--via-size 0.25` avoids it.
- **Repro** (08 #4):
  ```bash
  python3 -X utf8 py_router/route_diff.py wk/gp14/08_CM5_MINIMA_3/repro/gap_diffvia_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/d100.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 --hole-to-hole-clearance 0.25 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0
  python3 -X utf8 py_router/check_drc.py wk/gp14/08_CM5_MINIMA_3/repro/out/d100.kicad_pcb | grep -A5 VIA-DRILL
  ```
- **Cost / "fine":** ~8 min, and it disqualified the fewest-via seed. route_diff exited 0.
- **Upstream:** #221 and #308 CLOSED. (my search) #1207 CLOSED (GND return vias placed at the base
  clearance, not the pair's class): same producer, different rule.
- **Severity / category:** MEDIUM: check_drc caught it. Routing tool.

### M28 -- qfn_fanout escapes single-pad (no-connect) nets

- **Boards (1):** 08 #6.
- **Defect:** Module302 reports requested 70, escaped 70, but 33 of the via-in-pads are on nets with ONE
  pad: unused DPHY1/HDMI1/USB3/SD pins. Those are dangling vias that only block routing. Module301
  reports "failed 5" on five single-pad nets. This is what the routing skill prescribes for CM4/CM5
  connectors.
- **Repro** (08 #6):
  ```bash
  python3 -X utf8 py_router/qfn_fanout.py wk/gp14/08_CM5_MINIMA_3/repro/gap_fanout_in.kicad_pcb --output wk/gp14/08_CM5_MINIMA_3/repro/out/fan.kicad_pcb --component Module302 --nets '*' '!GND' '!+5V' --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1
  # -> requested 70 escaped 70; 33 of the 70 new vias are on single-pad nets
  ```
- **Cost / "fine":** ~5 min.
- **Workaround:** compute the multi-pad non-plane net list per module (`work/fan_Module30x.lst`) and pass
  it as `--nets`.
- **Upstream:** #110 and #669 (not this).
- **Severity / category:** MEDIUM. Routing tool.

### M29 -- place_simple lets back-face parts pile under a front-face BGA (its halo prices only the BGA's own face)

- **Boards (1):** 14 #7.
- **Defect:** the 44 B-side 0402 strap resistors, wired only to U1, sit under U1's ball field where its
  dog-bone vias must go.
  - r1 had 36-43 B parts under U1, 16 of them straps on the kept seed. Their nets
    (BOOT_CFG1_x/2_x/4_x) were the recurring open nets.
  - `apart` still left 10-15 (M15). Only an intent keep-out with an `allow` list cleared them.
- **Repro** (14 #7; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  python3 -X utf8 py_placer/place_simple.py $R/r1_fixed.kicad_pcb $R/out_s.kicad_pcb --groups $R/r1_groups.json --intent $R/r1_intent.json --seed 2
  python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as p;b=p('$R/out_s.kicad_pcb');print(sum(1 for r,f in b.footprints.items() if f.layer=='B.Cu' and 79.8<=f.x<=93.8 and 103.2<=f.y<=117.2))"
  ```
- **Cost / "fine":** ~15 min and one round. The seeds were legal and buildable.
- **Upstream:** #456 CLOSED (different).
- **Severity / category:** MEDIUM. Placement tool.

### M30 -- place_simple's objective is blind to warning-graded claims (crystal) and to ESD-diode placement along the connector path

- **Boards (1):** 09 #2 (second half).
- **Defect:**
  - The crystal claim (`placement.crystals`, 8.1 mm, warning-graded) was broken by ~7 mm: Y1 sat
    14.8 mm from U1's XI/XO.
  - The MST wire term does not care where a 3-pad ESD net's diode sits along the connector-to-chip
    path. D7 ended up 9.41 mm from J5's pin, D3 6.49 mm from J3 and D14 5.61 mm from J8;
    placement-lessons says 2.0 mm.
  - D14's detour lies on the path of the one net the board ships open.
- **Repro** (09 #2):
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gp14/09_StickHub/repro/g2_fixed.kicad_pcb 'wk/gp14/09_StickHub/repro/g2_s{seed}.kicad_pcb' --groups wk/gp14/09_StickHub/repro/g2_groups.json --intent wk/gp14/09_StickHub/repro/g2_intent.json --seeds 8 --clustered-seeds 8 --json 'wk/gp14/09_StickHub/repro/g2_s{seed}.json'
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/09_StickHub/repro/g2_s8.kicad_pcb --intent wk/gp14/09_StickHub/repro/g2_intent.json   # 2 ERRORs
  ```
- **Cost / "fine":** part of ~25 min of hand moves (4 moves in CHOSEN `after`).
- **Upstream:** none. (my search) #1254 CLOSED ("Nothing proposes proximity[] rows for hot loops, crystals
  or ESD") is the closest.
- **Severity / category:** MEDIUM. Placement tool.

### M31 -- The skill's proximity-claim form is unsatisfiable on a many-pad part (it claims every pad on every shared net, GND included)

- **Boards (1):** 10 #3.
- **Defect:** `{"ref": "U30", "near": "J5", "max_mm": 5.0}`, written as SKILL §3.6 step 4's example
  shows. Both the objective (`claim_cost`/`claim_over`) and the grade (check_floorplan `proximity`) take
  every subject pad on every shared net, including the GND and +3V3 balls.
  - Seed 0 scored `claims 659.0, claim_limits 371.9` (3719 of a 15887 cost), against 16.7 before.
  - check_floorplan reported "U30 pad L1 is 12.46mm from J5 pad 43", where L1 is a GND ball.
  - The form that works is an explicit `pads` map (26 LVDS balls to their 26 J5 pins) at 20 mm.
  - Nothing warns about a claim on a 121-pad part.
- **Repro** (10 #3):
  `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/10_glasgow_revC/r1/s5.kicad_pcb --intent wk/gp14/10_glasgow_revC/repro/gap3_intent_v3_badclaim.json`
- **Cost / "fine":** a round killed after one seed (~3 min) plus the diagnosis.
- **Upstream:** none ("proximity claim pads ground", "proximity claim multi-pad", "claim every pad shared
  net").
- **Severity / category:** MEDIUM. Skill text (+ placement tool: no warning).

### M32 -- route_plan_check R14 refuses the routing skill's own Step 8 pour-last chain

- **Boards (1):** 05 #2.
- **Defect:** R14 (`r_net_coverage_reconciles`) unions the `!X` exclusions of every route.py step. GND is
  excluded by the first step and claimed by the pour and both closing `'*'` steps, yet reads as an
  orphan: "FAIL R14 ... REFUSED ... Fix the plan; do not run it."
  - The only variant R14 accepts (GND kept in the first step) ended with 2 broken nets and 182 vias.
  - The refused plan ended with 0 broken and 157 vias.
- **Repro** (05 #2):
  `python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py wk/gp14/05_interf_u/repro/interf_u_plan.sh --board wk/gp14/05_interf_u/repro/r3_s7.kicad_pcb`
- **Cost / "fine":** the teammate ran the refused plan and disclosed it. The skill's "do not run it" and
  its Step 8 recipe cannot both be followed.
- **Upstream:** none (#377 is the opposite case). (my search) "route_plan_check": #941 CLOSED, general.
- **Severity / category:** MEDIUM. Skill text / plan checker.

### M33 -- check_reachability calls congestion "CAGED" on a routed board; the skill's "CAGED is geometry" does not say which board to measure

- **Boards (1):** 09 #5.
- **Defect:** on the routed board, 10 of 11 stranded pads read "CAGED for any track width". Every one is
  PASSABLE on the unrouted placement (+150 to +2119 um at 0.15 mm), and the next router parameters
  connected all but one.
- **Repro** (09 #5):
  ```
  python3 -X utf8 py_tools/check_reachability.py wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --pad U1.37 --track 0.127   # CAGED
  python3 -X utf8 py_tools/check_reachability.py wk/gp14/09_StickHub/repro/g6_placed.kicad_pcb --pad U1.37 --track 0.127   # PASSABLE
  ```
- **Cost / "fine":** ~5 min, and it nearly sent the run to re-placement for a router problem.
- **Upstream:** none.
- **Severity / category:** MEDIUM. Grader/checker + skill text.

### M34 -- route_bus hands on a board with a caged ball and lane copper on the GND plane layer

- **Boards (1):** 14 #9.
- **Defect:** route_bus reports "BUS U1->U2 ... connected=1 drc=1", and its joint fanout says "every ball
  served".
  - After the chain, VMEM stays open at U2.F1 (73.60, 105.40). check_reachability says "CAGED for any
    track width", walled in by locked bus lanes that no later step may rip.
  - VMEM tails sit on In1.Cu, the solid GND plane layer; for example a 4.4 mm dangling VMEM segment at
    (88.40, 103.38).
- **Repro** (14 #9; `R=wk/gp14/14_imx6ulz_4l/repro`):
  ```bash
  python3 -X utf8 py_tools/check_reachability.py $R/bus_vmem_caged.kicad_pcb --pad U2.F1 | tail -2
  python3 -X utf8 py_router/check_weird.py $R/bus_vmem_caged.kicad_pcb | grep "VMEM (In1.Cu)"
  ```
- **Cost / "fine":** ~10 min.
- **Upstream:** none.
- **Severity / category:** MEDIUM. Routing tool.

### M35 -- list_nets `--design-rules` suggests a via whose drill is larger than its diameter

- **Boards (1):** 07 #6.
- **Defect:** it prints `SUGGESTED ... --via-size 0.45 --via-drill 0.508`. `working_via_drill` is max(board
  `min_through_hole_diameter` 0.508, fab drill); `working_via_diameter` is max(`min_via_diameter` 0.3,
  fab 0.45). The two are never reconciled, though the diameter must be at least drill + 2 x annular.
- **Repro** (07 #6):
  `python3 -X utf8 py_router/list_nets.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb --design-rules`
- **Cost / "fine":** ~2 min. The teammate used the fab tier's standard 0.45/0.2 via instead.
- **Upstream:** #603 CLOSED, an inconsistent manufacturing floor (hole-to-hole): same family.
- **Severity / category:** MEDIUM: the advice is wrong. Routing tool.

### M36 -- mechanical.json carrying `"kind": "mechanical-declaration"` is refused (check_floorplan exit 2)

- **Boards:** campaign prep (every board with a mechanical.json). PREP #2.
- **Defect:** e1e4777e, d2e4c4c1 and 9eb8ec40 dropped the stage_unaided shape from
  `placement/reconcile.py`, and the `kind` key with it. Every check_floorplan call on such a board exits 2
  ("unknown key(s) ['kind']"). Upstream main's `tests/stress/stage_unaided.py` still writes that key.
- **Repro:** none recorded (the campaign dropped the key).
- **Cost / "fine":** a prep-phase workaround (key dropped; content otherwise identical to fa10's).
- **Upstream:** (my search) "mechanical.json kind": nothing.
- **Severity / category:** MEDIUM (compatibility). Placement tool.

---

## LOW

### L01 -- movie3d draws boxes where kicad-cli's iso render has the model

- **Boards (8):** PREP #6 + GRADE, as model counts in movie3d / boxes / kicad-cli iso:

  | board | movie3d models | boxes | iso |
  |---|---|---|---|
  | 01 | | 1 (U1, noval socket) | 11/11 |
  | 05 | | BUS1, P1, U9 | 21/23 |
  | 06 | 48/61 | 12 | 51/60 |
  | 08 | 52/84 | 20 | 63/77 |
  | 09 | 70/90 | 17 (USB-A J2-J9, LEDs, U2, Y1) | 93/93 |
  | 10 | 214/264 | 11 | 213/224 |
  | 13 | | 13 (U2, U6, U8, J1, SW1/SW2, D2, FIDs) | 75/82 |
  | 14 | 130/159 | 25 (BGAs U1/U2 + 23 resistors) | 153/153 |

  04 and 07 are not counted: their models are missing for the iso render too.
- **Defect / repro:** none recorded. PREP's open question: "which model path U1 names and why
  `movie3d/models.py` misses it".
- **Severity / category:** LOW (cosmetic). Film tool.

### L02 -- Decap owner election picks non-IC owners

- **Boards (2):** 06 #10 bullet 2; 14 #6 (note).
- **Defect:** this decides which part a cap is graded against.
  - 06: the resistor array RN1 and the RGB LED D1 are elected owners of +3V3. Example:
    `decap_distance: C25 is 2.54mm from RN1, the IC it decouples`.
  - 14: C20 is graded against U1 because a 3-pad regulator cannot own a cap (#1249).
- **Repro** (06): `python3 -X utf8 py_tools/check_floorplan.py $R/rn_owner.kicad_pcb --intent $R/intent.json`
  (`R=wk/gp14/06_rp2350_fpga_eensy_prePlane/repro`).
- **Upstream:** #1249 CLOSED (14). 06 found none.
- **Severity / category:** LOW. Grader/checker.

### L03 -- Output volume

- **Boards (2):** 06 #10 bullet 1; 13 #7.
- **Defect:**
  - 06: `board_score --quiet` still prints the full `SCORE_JSON=` line (21318 bytes per call).
  - 13: `place_pose` on a 97-part pile prints ~280 KB of JSON for a six-fiducial `set`, which buries a
    refusal's one-line reason.
- **Repro** (06): `python3 -X utf8 py_tools/board_score.py $R/input.kicad_pcb --quiet --json $R/bs_quiet_probe.json | wc -c`
  -> 21318. (13): `python3 -X utf8 py_placer/place_pose.py wk/gp14/13_pico_ice_rev3/repro/pile.kicad_pcb /tmp/f.kicad_pcb set FID1 67.3 75.0 lock FID1`.
- **Upstream:** (my search) #1194 CLOSED ("board_score --quiet prints 590 KB"): the same symptom, reported
  fixed, and still 21 kB here.
- **Severity / category:** LOW. Grader/checker + placement tool output.

### L04 -- Pile-blind pose claims in board_brief and board_context `--md`

- **Boards (2):** 08 #10; 09 #8.
- **Defect:**
  - 08: board_brief on a pile (its own summary says `pile: true`) names 12 "mechanical facts" read off
    staging poses. It also recommends `place_fixed`/`place_at`/`place_pack`, which do not exist in
    `py_placer/`.
  - 09: `board_context --md` prints a ~650-row CROSSED/AGREES pin-order table off staging poses, while
    its other sections do withhold pose-derived claims on a pile.
- **Repro** (08): `python3 -X utf8 py_tools/board_brief.py wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb | grep -E "mechanical:|place_fixed"; ls py_placer | grep -E "place_(fixed|at|pack)"`.
  (09): `python3 -X utf8 py_tools/board_context.py wk/gp14/09_StickHub/repro/g8_pile.kicad_pcb --md`.
- **Upstream:** 08 lists #711 (not this). (my search) #1109 and #1103 CLOSED (pile handling): same family.
- **Severity / category:** LOW. Placement tool (context/brief output).

### L05 -- Film GIFs over 3 MB

- **Boards (2):** GRADE 10 (film.gif 6400 KB, film_andy.gif 4352 KB); GRADE 14 (film.gif 4.8 MB).
- **Defect:** "need a stronger fallback at asset build". It is unclear whether this is the repo's film tool
  or the campaign's films.sh asset step.
- **Severity / category:** LOW. Film tool.

### L06 -- `--allow-unplaced` mismatch on a pile

- **Boards:** 07 #8 + PREP #5.
- **Defect:**
  - 07: render_placement's refusal says "Override with --allow-unplaced", renders anyway, and then
    rejects `--allow-unplaced` (exit 2). Its suggested crop commands write to `wk/worst1.png`, outside the
    run folder.
  - PREP #5: board_score's floorplan component reports check_floorplan exit 3 on a pile instead of
    passing `--allow-unplaced`.
- **Repro** (07): `python3 -X utf8 py_tools/render_placement.py wk/gp14/07_One-Air-Max/repro/input.kicad_pcb -o x.png`.
- **Severity / category:** LOW. Placement tool / grader.

### L07 -- movie3d tools not registered with manifest_to_plan, so the parity tests fail at branch head

- **Boards:** PREP #1.
- **Defect:** `movie3d/make_movie.py` and `movie3d/record.py` declare `KRT_TOOL kind 'actor'`, but
  `tests/stress/manifest_to_plan.py` neither maps, refuses nor no-ops them. As a result
  `tests/gui_parity/test_manifest_plan_parity.py`, `test_route_flag_plan_coverage.py` and
  `test_route_flag_plan_coverage_controls.py` fail.
- **Repro:** `python3 -X utf8 tests/test_route_flag_plan_coverage.py`.
- **Severity / category:** LOW. Film tool / tests.

### L08 -- ortools missing from requirements.txt

- **Boards:** PREP #3.
- **Defect:** plan-pcb-routing says to use `awx/route_bus.py` on every array-to-array bus, but ortools is
  not in `requirements.txt`, and 7 test_622 tests self-skip without it. The campaign installed
  9.15.6755, the pin in `awx/modal_whole.py`.
- **Severity / category:** LOW. Environment.

### L09 -- Silkscreen is graded by no step of the skills; a verified-DONE board carries 4 KiCad silk errors

- **Boards (1):** 01 #6.
- **Defect:** the final board has 3 `silk_overlap` errors and 1 `silk_over_copper` error.
  kicad_drc_compare compares copper only and prints CONSISTENT. `py_placer/beautify_labels.py` (#481)
  fixes these and records itself into the redo manifest, but neither skill names it.
- **Repro:** the first kicad-cli command of 01 #5 (M20).
- **Upstream:** #481 and #1202 CLOSED (the tool and its papercuts).
- **Severity / category:** LOW. Skill text.

### L10 -- Intent rows spell their free-text reason two ways

- **Boards (1):** 05 #6.
- **Defect:** `proximity[]` rows refuse `why` (they accept `note`), and `fixed_poses[]` rows refuse `note`
  (they accept `why`).
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/05_interf_u/repro/r1_s8.kicad_pcb --intent wk/gp14/05_interf_u/repro/intent_with_why.json`.
- **Severity / category:** LOW. Placement tool (intent schema).

### L11 -- The routing skill's fanout predicate sends an LQFP-48 to qfn_fanout, which hurt

- **Boards (1):** 09 #7.
- **Defect:** the predicate `pad_count > 40 and pitch <= 0.8` marks U1 (LQFP-48, 0.5 mm). With the fanout
  the judge route went from blocking 25 to 30 and from 70 to 77 vias. The skill does say to check the
  benefit.
- **Upstream:** #97 CLOSED, related.
- **Severity / category:** LOW. Skill text.

### L12 -- Step 2d all-nets iterations were byte-identical no-ops on a plateaued board

- **Boards (1):** 13 #5.
- **Defect:** step2 -> iter1 -> iter2 all graded broken 16, drc 1, 334 vias, 2928.06 mm, at ~4 min each.
  One more `'*'` pass on the best chain made it worse (broken 8 -> 9). The skill says the passes are
  "near-free and descend".
- **Upstream:** #656, #529, #412, #385 (none on this).
- **Severity / category:** LOW. Skill text.

### L13 -- The skill's DENSE-tier layer price vector vs declared impedance

- **Boards (1):** 08 #9 bullet 3.
- **Defect:** any routed copper on a GND or +5V reference layer fragments that plane, and the
  declared-impedance grade then fails (8-28 nets). Forbidding In1/In3/In4 took it to 0. The skill never
  says that `--impedance-nets` grades reference-plane continuity.
- **Severity / category:** LOW. Skill text.

### L14 -- The skill says to lock hand-written joins, but no tool stamps the lock

- **Boards (1):** 14 #14 bullet 2.
- **Defect:** check_join stages a join but no tool stamps `(locked yes)` on a segment, so the four 0.05 mm
  joins ship unlocked.
- **Severity / category:** LOW. Skill text.

---

## Not clustered, or not a tool defect

| entry | reason |
|---|---|
| PREP #4 (Playwright 1.52 headless-shell install stalls at extract on macOS 27) | environment, not the repo (PREP says so) |
| 12 #12 (no PDF reader: pdftoppm / pypdf / fitz absent) | host environment; not a repo tool (teammate says so) |
| 13 closing note (PTS820 datasheet fetch timed out / redirected) | network / web access, not a repo tool |
| 13 #6 bullet 1 (plug-in module rows had to go into a new `intent_rows.json`) | consequence of the campaign rule that the given intent may not be edited |
| GRADE 13 and 06 (first film pass differed: films.sh did not pass `place_args` / used the stock placer) | campaign script (`films.sh`), since fixed via CHOSEN.json `place_args`; for 06 the root is H15 |
| GRADE 14 (first films pass died on a syntax error) | lead edited films.sh while bash was reading it -- operator error |
| GRADE 12 (a Bash call did not run for ~2 h; stopped and resumed 00:44Z) | harness stall; subtract from wall time |
| GRADE 04 / 07 (3D stills are boxes) | board data: the models are absent from KiCad 10's mac library (04) or point at `${EASYEDA2KICAD}` / `C:\` private libs (07); not a film-tool defect |
| GRADE 10 (final ships one short, C76 pad 2 / +3V3 via) | a routing outcome with no TOOL_GAPS entry tracing it to a tool; might relate to H18/H19, not established |
| 06 #1 (the 442-of-464.5 mm2 overlap split) | measured inline, no file kept, so not reproducible as written; H15 rests on the helper's 0/12 -> 11/12 instead |
| 08 #7 SW501 cause (`board_bounds`) | the teammate's own unverified suspicion; the symptom is in M08 |
| 06 #3 (C27 limit unreachable) | partly the given intent's 1.0925 mm limit, not only the tool; kept in M02 with that caveat |
| 04 #10 bullet 2, 13 #3 | the teammates themselves call quick-vs-full divergence "a property, not a tool defect"; kept in M04 as a skill-claim gap |
| 09 #6, 11 #3, 11 #7 | disclosed, as-designed behaviour under the default escalation / via-in-pad policy; kept in M12 / M21 as skill-chain issues, weak as tool defects |
| 01 #2 (`rotate` absolute) | partly reader error, since `--help` states it; kept in M05 for the route_review / skill wording and the false "Modified 1 footprint positions" |
| 12 #2 (netclass members missed) | partly teammate error ("my own miss too": looked only at KiCad 7+ netclass fields); the grading gap in H12 stands regardless |
| 07 #5 / GRADE 07 (BAT1 overlaps) | the gated poses are the teammate's own `derived_default` choices, not mechanical.json; kept in H05 as the weaker instance |
| 05 #1 (C1/R2 nudge) | the decap claims it had to meet were the teammate's own; only partial evidence for M02 |
| 02 "Not a gap" (unfilled zones), 09 #9, 11 #8, 08 helpers table | notes and helper descriptions, attached to M20, H17, M08 and H06/H03 respectively |
