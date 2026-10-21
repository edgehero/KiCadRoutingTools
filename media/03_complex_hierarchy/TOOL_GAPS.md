# TOOL_GAPS -- gp14 board 03 (complex_hierarchy)

Ranked by what each cost this run. No helper scripts were written (`helpers/` is empty); every
measurement below is a repo tool or a one-line parse of a board with `kicad_parser`. All commands run
from WT (`~/Documents/git/krt-gp14`) with the venv on PATH; the inputs they need are in
`wk/gp14/03_complex_hierarchy/repro/`.

---

## 1. route.py leaves an off-grid T-junction stub (KiCad `track_dangling`) that board_score calls clean

**Cost:** about 10 minutes and two extra chain runs: the tuned chain's board graded DONE on board_score
(blocking 0) but `check_complete` said INCOMPLETE; three repair attempts and a second fresh `final_route/`.

**Tool and command:** `py_router/route.py` (any route of this placement at the default 0.1 mm grid).

**What it claimed:** `JSON_SUMMARY_MIN` failed 0, open 0; `board_score` BLOCKING=0; the end-of-run "Strict
collapse (#1063)" removed 20 redundant segments and kept this one.

**What was true:** net `/ampli_ht_horizontal/S_OUT+` (3 pads: R309.1, R310.1, RV301.3) carries a
0.0381 mm, 0.4 mm-wide F.Cu segment (115.600, 81.773)-(115.627, 81.800) joining the R310 vertical run
to the branch towards RV301. Its start sits 27 um off the 0.1 grid, mid-segment on the vertical.
`check_weird` reports `kicad-dangling: 1` and `check_complete` returns INCOMPLETE (weird_copper);
KiCad 10.0.7 `kicad-cli pcb drc` reports `track_dangling` (warning) at (115.6, 81.773077),
"length 0.0381 mm". The same stub appeared on 7 of the 8 0.1-grid boards checked in `opt/` (every
seed-6 variant; the one seed-11 board was clean); both 0.05-grid variants were clean. Neither iteration pass nor
`--rip-existing-nets <net>` touched it (the latter is a no-op on a connected net and says so with a
WARNING); `--force-reroute` at grid 0.1 laid the identical stub again (deterministic). A forced re-route
of that one net at `--grid-step 0.05` removed it (final_route step 04).

**Root cause (matches an existing issue):** `py_router/single_ended_routing.py` line 4707 on this branch
still reads `num_steps = max(1, int(length / coord.grid_step))` -- the truncation #1291 describes (tap
points 35-71 um off grid, dangling T-junction stubs). #1291 was closed 2026-10-20 15:48 with a fix on a
fork; it is not on `grouped-placement` 8328f157.

**Reproduce:**
```bash
python3 -X utf8 py_router/route.py wk/gp14/03_complex_hierarchy/repro/gap1_placed.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb --nets '*' --clearance-ceiling 0.3 --via-size 0.889 --via-drill 0.508 --power-nets GND HT VCC '*VAA' /12Vext --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --via-cost 600 --direction-preference-cost 0 --layer-costs 1.0 1.0
python3 -X utf8 py_tools/board_score.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb      # BLOCKING=0
python3 -X utf8 py_router/check_weird.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb     # kicad-dangling: 1
python3 -X utf8 check_complete.py wk/gp14/03_complex_hierarchy/repro/gap1_out.kicad_pcb            # INCOMPLETE -- weird_copper
```
(`repro/gap1_kicad_drc.json` is KiCad's own report on that output.)

**Existing issues:** `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "track_dangling"`
-> **#1291** (CLOSED, the cause; fix not on this branch), #1217 (CLOSED, a KiCad track_dangling papercut on
fa10 board 06); `--search "kicad-dangling"` -> **#1234** (OPEN: "route.py leaves chains of 0.025-0.075 mm
segments that enter no pad or via, and nothing reports them") is the same family. A second, smaller point
not in either: `board_score` has no weird-copper component, so its `blocking 0` on this board reads DONE
while `check_complete` does not.

---

## 2. route_review's "turn 180" cannot be applied with `place_pose rotate` to an axial part (and the skill says to)

**Cost:** about 4 minutes: one refused call, one written-but-unbuildable board that was routed before
check_assembly caught it, and a hand computation of the replacement pose.

**Tool and command:** `py_tools/route_review.py` + `py_placer/place_pose.py ... rotate`, as SKILL.md
§3.6 / step 4 prescribe ("turn each two-pad part it lists as turned against its wiring with
`place_pose ... rotate`").

**What it claimed:** route_review: "two-pad parts turned against their wiring (turn 180): R207 at
(152.27, 115.24) rot 90: saves 9.0 mm".

**What was true:**
- `place_pose rotate R207 180` is ABSOLUTE by default (`--relative` adds): it set 90 -> 180, which is a
  quarter turn, and was refused for a pad stack with Q201 (exit 4).
- `rotate R207 180 --relative` turns about the footprint ORIGIN, which on
  `R_Axial_DIN0204_L3.6mm_D1.6mm_P7.62mm_Horizontal` is pad 1, so the whole body swings 7.62 mm to the
  other side of pad 1. place_pose wrote it (`no_worse: true`); check_assembly: NOT BUILDABLE
  (R207/R209 2.00 mm2 and D203/R207 1.27 mm2 courtyard interpenetration).
- What route_review means -- the two pads exchanged in place -- is
  `set R207 <pad 2 x> <pad 2 y> --rot 270` (= `set R207 152.2729 107.6242 --rot 270`): buildable, and it
  routed 809.75 -> 781.94 mm (then 787.71 -> 758.1 mm under the final chain parameters).

**Reproduce:**
```bash
python3 -X utf8 py_tools/route_review.py wk/gp14/03_complex_hierarchy/repro/gap2_s6_routed.kicad_pcb        # "R207 ... (turn 180)"
python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_abs.kicad_pcb rotate R207 180              # exit 4, pad stack Q201/R207
python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_rel.kicad_pcb rotate R207 180 --relative   # written
python3 -X utf8 py_tools/check_assembly.py wk/gp14/03_complex_hierarchy/repro/gap2_rel.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb               # NOT BUILDABLE
python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb wk/gp14/03_complex_hierarchy/repro/gap2_set.kicad_pcb set R207 152.2729 107.6242 --rot 270
python3 -X utf8 py_tools/check_assembly.py wk/gp14/03_complex_hierarchy/repro/gap2_set.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb               # buildable
```

**Existing issues:** `--search "turned against its wiring"`, `--search "route_review turn 180"`,
`--search "rotate relative place_pose"`: nothing covering it. Suggested fix: route_review prints the
`place_pose` command that swaps the pads (a `set` to the other pad's position at rot+180, or a
body-centred turn), and SKILL.md §3.6 names it.

---

## 3. kicad_drc_compare.py with `--baseline` prints the BASELINE's 729 violations as the head of the graded board's report

**Cost:** about 3 minutes (ran `kicad-cli pcb drc` by hand to be sure the final board was not the one with
729 violations).

**Tool and command:** `tests/stress/kicad_drc_compare.py <final> --baseline <unrouted input>`, as the
routing skill recommends.

**What it claimed:** the output opens with "FOUND 729 DRC VIOLATIONS: PAD-PAD violations (729) -- 536 in
CONTACT", listing pads at y ~136-145 mm, i.e. the staging pile south of the outline -- not the board being
graded. Only the summary at the end is about the graded board ("kicad=0 check_drc=0 ... CONSISTENT").

**What was true:** the final board has 0 check_drc violations and KiCad reports 0 copper violations and
0 unconnected items (only silkscreen and lib_footprint_issues warnings). The 729 are the pile's.

**Reproduce:**
```bash
python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gp14/03_complex_hierarchy/repro/gap3_final.kicad_pcb --baseline wk/gp14/03_complex_hierarchy/repro/gap3_baseline_pile.kicad_pcb | head -12
```

**Existing issues:** `--search "kicad_drc_compare baseline"`: nothing covering it (#405/#450 are about DRC
content, not this output).

---

## 4. place_pose reports `legal: false` for every pose on this board (outline 16 um off rectangular)

**Cost:** about 2 minutes (one probe to learn that `legal: false` was not about the move).

**Tool and command:** `py_placer/place_pose.py <board> <out> set R207 ...` (any pose op).

**What it claimed:** `"legal": false` on every call, including on poses check_assembly calls buildable.

**What was true:** `pad_edge_after.complete` is false with all 165 pads `unmeasured` ("outline uses sampled
perimeter check"): the Edge.Cuts rectangle has one corner at y=51.816 against 51.8 elsewhere, so it is not
an exact axis-aligned rectangle and the analytic pad-to-edge check is skipped. Every other channel was 0;
`no_worse` was the usable answer.

**Reproduce:**
```bash
python3 -X utf8 py_placer/place_pose.py wk/gp14/03_complex_hierarchy/repro/gap2_s6.kicad_pcb /tmp/pp_probe.kicad_pcb --dry-run set R207 152.2729 107.6242 --rot 270 | grep -o '"legal": [a-z]*\|"pad_edge_unmeasured_after": [0-9]*'
```

**Existing issues:** `--search "sampled perimeter"`: nothing covering it.
