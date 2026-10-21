# TOOL_GAPS -- gp14 board 10 (glasgow_revC)

Ranked by what each cost the run (most first). Each entry: tool and command, what it
claimed, what was true (measured), a reproduction from the worktree root, and the
read-only `gh issue list` search result.

Sections are numbered in the order they were hit. **Ranked by what each cost the run:**

1. **#7** route.py strips BGA dog-bone escapes it cannot restore, then blames the fanout -- the mechanism behind
   most of the open nets this run ships, and a misdirected diagnosis.
2. **#1** place_simple refuses the declared FID/MK poses on bounding boxes -> every seed "illegal", empty judge list
   (manual judging in round 1, the lock workaround that led to #4).
3. **#6** route.py's improvement gate accepted an all-nets pass that added 17 DRC violations (board 12 -> 42).
4. **#2** an `apart` hint between touching groups is a constant -> a pose-identical round (killed, ~7 min).
5. **#4** KiCad-locking the markers as the skill prescribes flips check_assembly to NOT BUILDABLE.
6. **#3** the skill's proximity-claim form is unsatisfiable on a many-pad part (killed round, ~3 min).
7. **#5** converge.py refuses the first board_score row after the skill's quick_score rows.
8. **#8** (skill) quick_score counts poured-net pads `--quick 2` never welds, so the round stop cannot fire.

## 1. place_simple refuses user-declared poses of round pads on their bounding box, so every seed is "illegal" and `judge.json` names none

- **Tool / command:** `py_placer/place_simple.py r1/fixed.kicad_pcb 'r1/s{seed}.kicad_pcb' --groups r1/groups.json --intent r1/intent.json --round --jobs 4`
  (its declared-pose check, `placement.seeder._fixed_pose_check`, called from `place_simple.main`).
- **What it claimed:** for every one of the 12 seeds, `no legal pose for FID1, FID2, FID3, FID4, FID5, FID6, J2, J3, J5, MK1, MK2, MK3, MK4`
  (exit 4), e.g. `FID1's declared pose is not legal: ... pad clearance to MK1 short by 0.250mm` and
  `MK1's declared pose is not legal: ... pad copper 0.950mm past the outline`. `--round` then writes
  `judge.json` with `"judge": []` -- the round cannot name a single seed to judge, whatever the anneal did.
- **What was true:** the 7.0 mm round GND pad of MK1 (54, 116) and FID1's 0.75 mm pad (58, 118.5) are
  4.717 mm apart centre to centre: true copper gap **0.842 mm**, against a required 0.375 mm (FID1's
  local clearance). The 0.25 mm "shortfall" is the gap between the two pads' BOUNDING SQUARES
  (0.125 mm vs 0.375 mm). The "0.95 mm past the outline" is the bounding square's corner past the
  rounded board corner. `check_assembly` on the same placed board: `pad/hole/oob echo: 0 pad pair(s)`,
  `on the outline by design, not gated: MK1, MK2, MK3, MK4 (... a round pad whose bounding box, not its
  copper, crosses)`, VERDICT buildable. The courtyard overlaps among J2/J3/J5/FID/MK the same check
  lists are KiCad courtyard touches between declared poses (0.01-0.26 mm2), which `check_assembly`
  waives (marker class) or reports advisory. None of the 13 parts is movable: their illegality is
  identical in every seed and says nothing about the seed.
- **Workaround:** round 1: the 6 judge seeds picked by hand as the 6 lowest `final.cost` among seeds whose
  `illegal` list holds nothing but those 13 declared parts (seed 4, which also left U30 illegal, excluded).
  From round 2: FID1-6 and MK1-4 KiCad-locked in `fixed.kicad_pcb` at their mechanical.json poses
  (skill section 3.1's own method) and removed from `fixed_poses` (`intent_v2.json`), plus `overlap_waivers`
  for the J2/J3/J5 courtyard touches.
- **Reproduce:**
  `python3 -X utf8 py_placer/place_simple.py wk/gp14/10_glasgow_revC/repro/gap1_fixed.kicad_pcb /tmp/gap1_s0.kicad_pcb --groups wk/gp14/10_glasgow_revC/repro/gap1_groups.json --intent wk/gp14/10_glasgow_revC/repro/gap1_intent_v1.json --seed 0`
  -> the WARNING lines above and `"illegal": [...FID..., ...MK...]`, exit 4.
- **Issues:** `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "declared pose illegal judge"`,
  `"place_simple illegal fiducial mounting hole"`, `"judge.json empty"`, `"fixed_poses illegal"`,
  `"declared pose not legal bounding box"`: none found.

## 2. An `apart` hint between two groups that already touch is a constant: the round it was given to replayed the previous round pose for pose

- **Tool / command:** `py_placer/place_simple.py r2/fixed.kicad_pcb 'r2/s{seed}.kicad_pcb' --groups r2/groups.json --intent r2/intent.json --round --jobs 4`
  with `"apart": ["core"]` added to the `leds` group (the skill's section 3.6 step 4: "two groups crowding one
  area: an `apart` hint").
- **What it claimed:** nothing false in words; it ran, reported `hints 17.1: apart:core:leds 15.0` and wrote 12 new
  placements, which read as a new round. The skill says "an input change reshuffles the whole anneal".
- **What was true:** the hint is `weight * max(0, 3 - least gap between ANY member of A and ANY member of B)`
  (`placement/simple.py`, `hint_cost`/`_hint_value`). Two groups whose parts interleave anywhere on the board have a
  least gap of 0 at every pose the anneal visits, so the term is the constant 5 x 3 = 15.0 and never changes an
  accept/reject decision. Measured: seeds 2 and 3 of the hinted round are pose-for-pose IDENTICAL to round 1 (0 of 264
  parts at a different pose), `final.cost` higher by exactly 15.0 (10831.9 -> 10846.9, 12929.1 -> 12944.1), wire,
  crossings, decaps and groups terms identical to the last digit. Nothing in the output says the hint had no gradient.
  The same shape applies to `edge` (only the group's NEAREST member's distance counts) and `near` (0 once any two
  members touch).
- **Cost:** a placement round (about 7 minutes of 4 cores) killed after 3 seeds when the identity was noticed; one of
  the run's 3 rounds would otherwise have been spent judging a replay.
- **Reproduce:**
  `python3 -X utf8 py_placer/place_simple.py wk/gp14/10_glasgow_revC/repro/gap2_fixed.kicad_pcb /tmp/gap2_s2.kicad_pcb --groups wk/gp14/10_glasgow_revC/repro/gap2_groups_apart.json --intent wk/gp14/10_glasgow_revC/repro/gap2_intent_v2.json --seed 2`
  and the same with `--groups wk/gp14/10_glasgow_revC/repro/gap2_groups_v1.json`: the two boards' footprints are at identical poses,
  and the two `final.cost` differ by exactly 15.0 (the hint's saturated value).
- **Issues:** `gh issue list ... --search "apart hint"`, `"apart groups no effect"`, `"apart term constant"`: nothing
  that covers it (the hits are unrelated routing issues and #548).

## 3. The skill's `proximity` claim, written as its example shows, is unsatisfiable on a many-pad part: every pad on every shared net (GND included) is claimed

- **Tool / command:** SKILL.md section 3.6 step 4: "a part far from the pins it serves: ... give it a `proximity`
  claim in the intent (`{"ref": "C6", "near": "SW1", "max_mm": 2}`, pad edge to the nearest pad on a shared net)".
  Written for the FPGA as `{"ref": "U30", "near": "J5", "max_mm": 5.0}` and placed with
  `place_simple.py r3/fixed.kicad_pcb 'r3/s{seed}.kicad_pcb' --groups r3/groups.json --intent r3/intent.json --round --jobs 4`.
- **What it claimed:** the skill text reads as one distance ("pad edge to the nearest pad on a shared net"); `check_groups`
  accepted it (U30 listed as a follower) and `place_simple` ran.
- **What was true:** both the objective (`simple.py claim_cost` / `claim_over`) and the grade (`check_floorplan`
  `proximity`) take EVERY subject pad on EVERY net the two parts share -- for U30/J5 that includes the GND and +3V3
  balls -- and price each one's distance and each one's overshoot. A 9 mm BGA cannot have all its GND balls within
  5 mm of J5's GND pins, so the claim is unsatisfiable by construction. Seed 0 of that round: `claims 659.0,
  2 claim limit(s) broken, claim_limits 371.9` (371.9 mm of overshoot x 10 = 3719 of a 15887 cost), against 16.7 for
  the round before; `check_floorplan` on round 2's best board reported `U30 pad L1 is 12.46mm from J5 pad 43` (L1 a
  GND ball). Nothing warns that a claim on a 121-pad part spans its ground pins. The fix that works is the
  crystal claims' own form, an explicit `pads` map (26 LVDS balls to their 26 J5 pins) with a limit measured on a
  real arrangement (20 mm).
- **Cost:** a round-3 placement killed after one seed (about 3 minutes of 4 cores), plus the diagnosis.
- **Reproduce:** `python3 -X utf8 py_tools/check_floorplan.py wk/gp14/10_glasgow_revC/r1/s5.kicad_pcb --intent wk/gp14/10_glasgow_revC/repro/gap3_intent_v3_badclaim.json`
  -> `[ERROR] proximity: U30 pad ... from J5 pad ...` on GND/+3V3 pads although r1/s5 has U30 directly under J5.
- **Issues:** `gh issue list ... --search "proximity claim pads ground"`, `"proximity claim multi-pad"`,
  `"claim every pad shared net"`: none.

## 4. Locking the mechanical markers, as the skill says, makes check_assembly NOT BUILDABLE on the courtyard touches it waives when they are unlocked

- **Tool / command:** SKILL.md section 3.1 ("Place each with `place_pose ... set REF X Y --rot DEG lock REF`") and
  part-roles.md ("Holes and fiducials are mechanical: place and lock them first"), then
  `py_tools/check_assembly.py <board> --intent <intent> --baseline <input pile>` -- the verifier's own command, and
  `board_score`'s `assembly` component.
- **What it claimed:** with FID1-6 and MK1-4 KiCad-locked at their mechanical.json poses: `COURTYARD BLOCKING (6) ...
  6 of 6 GATE`, `FID1 <-> MK1 2.0554mm2 ... GATES (moved: FID1 MK1)` (and FID2/MK3, FID3/MK4, FID4-6 on B), VERDICT
  NOT BUILDABLE; `board_score` blocking 1 (assembly).
- **What was true:** the same board with the same poses, only the ten locks removed: `FID1 <-> MK1 courtyard 2.0554mm2
  waived:marker_class`, VERDICT buildable. The courtyards touch because the user declared both poses (fiducials 4.7 mm
  from 7.0 mm-pad mounting holes; true copper gap 0.84 mm). By design a lock disables the class waiver ("A locked pose
  is a decision somebody made ... waiver class chosen for unlocked parts does not apply here"), and the `moved vs
  baseline` arm fires because the baseline is the pile. So the skill's prescribed lock turns a placement the checker
  calls buildable into one it calls not buildable, with nothing moved. The way out the checker offers is
  `overlap_waivers` pairs in the intent; the skill never says that a lock needs them.
- **Workaround:** the locks (taken in round 2 to get round TOOL_GAPS 1's judge list working) removed again on the kept
  board (`CHOSEN.json` "after"); the declared poses are unchanged and still graded through mechanical.json.
- **Reproduce:**
  `python3 -X utf8 py_tools/check_assembly.py wk/gp14/10_glasgow_revC/repro/gap4_kept_locked.kicad_pcb --intent wk/gp14/10_glasgow_revC/repro/gap4_intent_v3.json --baseline wk/gp14/10_glasgow_revC/repro/input_pile.kicad_pcb`
  (NOT BUILDABLE, 6 gating FID/MK pairs) against the same with `repro/gap4_kept_unlocked.kicad_pcb` (buildable).
- **Issues:** `"locked fiducial courtyard marker"`, `"marker_class waiver locked"`: #897 (closed; authored waivers
  before part class) and #1250 are related, none covers a lock disabling the marker waiver.

## 5. `converge.py record` refuses the first full-route row after the skill's quick_score rows ("graded FEWER components")

- **Tool / command:** `python3 -X utf8 py_placer/converge.py record --ledger ledger.jsonl --board final_route/iter2.kicad_pcb --kind completion --parent kept.kicad_pcb --score-file final_route/iter2.score.json`
  (the score from `board_score.py --intent --baseline --json`, as SKILL.md section 5.6 prescribes), after the
  judging routes were recorded with `--score-file r<N>/s<S>_fast.score.json` from `quick_score.py`, as section 3.6
  step 2 prescribes.
- **What it claimed:** `record: this lap looks like an IMPROVEMENT only because it graded FEWER components.
  blocking 25 -> 15, but the components that differ are: impedance ...; length ...; net_widths ...` -- exit 2,
  "Nothing was written".
- **What was true:** neither score graded impedance, length or net widths (the board declares none of them).
  `quick_score`'s payload is `{blocking, blocking_by: {broken: N}, quality}` with no `ungraded` list and no nulls, so
  `converge.ungraded_set` reads it as having graded EVERYTHING, and `board_score`'s honest nulls then look like a
  strictly smaller graded set. The refusal is a payload-format mismatch between the two scorers the skill tells the
  run to use, not a false improvement.
- **Workaround:** re-scored the round-3 seed-4 fast route with `board_score` (same flags as the full route) and recorded
  that as a completion row first; the full route's row was then accepted.
- **Reproduce:** with `wk/gp14/10_glasgow_revC/repro/gap5_ledger_before_fullroute.jsonl` copied to a scratch ledger,
  `python3 -X utf8 py_placer/converge.py record --ledger <copy> --board wk/gp14/10_glasgow_revC/final_route/iter2.kicad_pcb --kind completion --parent wk/gp14/10_glasgow_revC/kept.kicad_pcb --score-file wk/gp14/10_glasgow_revC/final_route/iter2.score.json`
  -> the refusal above, exit 2.
- **Issues:** `"quick_score ungraded converge"`, `"commensurability quick_score"`, `"FEWER components quick"`: none.

## 6. route.py's improvement gate ACCEPTS an all-nets pass that trades 9 nets for 9 and adds 17 DRC violations (board 12 -> 42 blocking)

- **Tool / command:** Step 2d's all-nets pass on the chain-C board:
  `python3 -X utf8 py_router/route.py final_route/s2_c.kicad_pcb final_route/iterC1.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.4 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --power-nets GND +3V3 +5V +1V2 /IO_Banks/VIOA /IO_Banks/VIOB /IO_Banks/VIO_AUX /VUSB /xVBUS '*ISNS_H' 'Net-(U14-OUT)' 'Net-(U31-OUT)' --power-nets-widths 0.25 0.25 0.4 0.25 0.3 0.3 0.25 0.4 0.4 0.3 0.3 0.3 --no-bga-zones --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2`
- **What it claimed:** `IMPROVEMENT GATE: this run broke 9 previously-connected net(s) [+1V2, /D1, /D2, /D3, /FLAGB, /FLAGD, +3 more], worsened 0, connected 9 -- ACCEPTED`; `JSON_SUMMARY_MIN` failed 10 (the input's own count).
- **What was true:** `board_score` (same intent, baseline): input s2_c blocking 12 (12 broken, 0 DRC) -> output
  blocking 42 (23 broken, **17 DRC**, 2 unrouted); `check_drc --clearance-margin 0.1`: input EXIT 0, output 4
  segment-segment (3 in CONTACT), 9 via-segment (5 in CONTACT), 1 via-via (CONTACT), 3 via-drill-hole (CONTACT) --
  shorts. The gate weighs nets lost against nets gained and never looks at DRC, so a tie that ships shorts is
  "accepted". (The two earlier all-nets passes of the same run were reverted correctly; this one was not.)
- **Cost:** about 5 minutes of routing plus the cross-check; had the gate's word been trusted, the run would have
  continued from a board with shorts.
- **Reproduce:** run the command above with input `wk/gp14/10_glasgow_revC/repro/gap6_s2_c.kicad_pcb` (with its
  `.kicad_pro`) and grade both boards with `python3 -X utf8 py_router/check_drc.py <board> --clearance-margin 0.1`.
- **Issues:** `"improvement gate accepted DRC"`, `"improvement gate tie"`, `"route.py iteration shorts"`: #600
  (closed: rip-and-restore regressing routed copper) is the nearest; none covers the gate ignoring DRC.

## 7. route.py strips a BGA ball's fanout escape, fails the net, then blames the fanout ("fanout-dropped ball ... Re-run the fanout")

- **Tool / command:** chain C's route step,
  `python3 -X utf8 py_router/route.py final_route/s2a_c.kicad_pcb final_route/s2_c.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.4 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --power-nets ... --no-bga-zones --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2`
- **What it claimed:** `Hint: pad U30.C9 is a fanout-dropped ball (no escape stub) -- it sits inside U30's pad field
  with no copper of Net-(U30A-IOT_172) attached, so no rip authority or retry can reach it. Re-run the fanout for
  this net (bga_fanout.py ...)`; the same for U30.E8 (/IO_Banks/U5), U30.J5, U30.D7.
- **What was true:** the fanout escaped every ball (`Dog-bone escape: 105/105 signals escaped ... 0 failed`), and the
  escape stubs of C9, B9 and E8 are present on every board of the chain up to the route step's INPUT (s1b, s1q, s1c,
  s1d, s2a_c: 1, 1 and 3 segments at the ball); on the route step's OUTPUT they have 0. The route step ripped those
  nets' escapes during rip-up, failed to re-route them, shipped the ball bare, and its hint then sends the user to
  re-run a fanout that did its job. Re-running the fanout as advised changes nothing the route step will not undo.
- **Cost:** a misdirected diagnosis to rule out (the classification in section 4 of the skill reads "fanout dropped
  balls" as a fanout/placement problem); these nets are a large share of every open list in this run.
- **Reproduce:** count copper at U30.C9 on `wk/gp14/10_glasgow_revC/repro/gap7_s2a_c.kicad_pcb` (1 segment), run the
  route command above on it, and read the hint and the ball's copper (0 segments) on the output.
- **Issues:** `"fanout-dropped ripped escape stub"`: #1156 (closed: "route.py rips out-of-scope routed nets ... a
  failed victim ships with its BGA via-in-pad escape stripped") is the same family; here the nets are in scope
  (`'*'`) and the escapes are dog-bones, and the misleading hint is not covered.

## 8. (skill) The round stop "best fast route has no blocking net" cannot fire on a board with pours: quick_score counts plane pads that `--quick 2` never welds

- **Tool / command:** SKILL.md section 3.6 ("If the best fast route has no blocking net, stop") with step 1's
  `route.py --quick 2` ("Level 2 skips ... plane finalize") and step 2's `quick_score.py ... --route route.json`.
- **What it claimed:** the round loop stops at the first clean fast route; quick_score's `blocking` is "the route
  step's own tally of open nets".
- **What was true:** on this board (GND and +3V3 pours kept from the source) every one of the 18 judged fast routes
  left poured-net pads open -- GND 1-57 and +3V3 0-26 per seed (e.g. r3/s4: +3V3 3, GND 5 of its 25) -- because the
  plane finalize that welds them is exactly what level 2 skips. A seed could only stop the loop if pour-launch alone
  happened to reach every plane pad. So the loop always runs all `--rounds`, and the per-seed `blocking` mixes a
  placement signal with plane-pad noise of the same size (GND alone ranged 1-57 between seeds).
- **Cost:** no lost time beyond the rounds the skill runs anyway, but the judge's ranking is partly plane-pad noise,
  and "a placement whose fast routes all leave nets open" is true by construction here.
- **Reproduce:** `python3 -c "import json;d=json.load(open('wk/gp14/10_glasgow_revC/r3/s4_route/route.json'));print([x for x in d['pad_pairs_open'] if x['net'] in ('GND','+3V3')])"`
  (and the same for any `r<N>/s<S>_route/route.json`).
- **Issues:** `"quick 2 plane finalize judge blocking"`, `"quick_score poured pads"`: none.
