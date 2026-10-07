# TOOL_GAPS -- fa10 board 09 (StickHub), /pcb-free-agent full

Ranked by what each one cost this run. Every repro runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) after
`export MSYS2_ARG_CONV_EXCL='*'`, with inputs copied into
`wk/fa10/09_StickHub/repro/` (`R=wk/fa10/09_StickHub/repro` below). Issue
searches were read-only: `gh issue list --repo drandyhaas/KiCadRoutingTools
--state all --search "<keywords>"`.

---

## 1. route.py and the copper grader count two same-net pads 15 um apart as joined; KiCad does not

- **Tool / command:** `py_router/route.py b/rep_s4.kicad_pcb r/r2_s4_io.kicad_pcb --nets '*' --track-width 0.1 --clearance 0.1 --via-size 0.3 --via-drill 0.15 --ordering inside_out --json-out r/r2_s4_io.json`, then `py_router/check_connected.py`.
- **What it claimed:**
  - route.py's `--json-out` lists the open nets as /LED3, /U4D+, /U4D- and Net-(D16-1). +5V is not among them, so route.py treated +5V as routed and never laid copper between C34.1 and C24.1.
  - check_connected's copper grading also passes +5V.
- **What was true:** check_connected's own KiCad-refill cross-check reports `1 net(s) UNCONNECTED per KiCad refill though copper grading passed them: +5V`, with one unconnected link between pads (148.292, 106.027) and (147.727, 106.717). Those are C24.1 and C34.1, both 0.55 x 0.8 mm on B.Cu, with a rectangle gap of **0.015 mm** in x (they overlap in y). board_score counted +5V as broken (1 join).
  - It was one of the six blockers the run carried through six failed approaches, and no routing approach could fix it, because the router believed the net was complete.
  - A 0.89 mm hand join (`check_join` CLEAN) fixed it.
  - The seeder also packed two same-net caps' pads to within 15 um, which is the trigger.
- **Repro:** `python3 -X utf8 py_router/check_connected.py $R/r2_s4_io.kicad_pcb` (prints the refill-only +5V line), and `python3 -c "import json;d=json.load(open('wk/fa10/09_StickHub/r/r2_s4_io.json'));print([m['net_name'] for m in d['failed_multipoint']])"`.
- **Existing issues:** #320 (closed, "Unify the net-connectivity definition/tolerance") is the same family but closed; #659 (closed) is a different KiCad-only open class (the IO_SDA welds). Nothing open covers a pad-to-pad tolerance join.
- **Cost:** about 20 min of diagnosis, plus one of six blockers that no router approach could address.

## 2. The improvement gate decides by NET count and threw away a 24-join improvement

- **Tool / command:** the second step of the run-39 recipe, routing non-GND nets first and then `route.py --nets '*'` to finalize GND: `python3 -X utf8 py_router/route.py $R/r7_nognd_io_a.kicad_pcb out.kicad_pcb --nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.3 --via-drill 0.15`.
- **What it claimed:** `JSON_IMPROVEMENT_GATE: {"lost": ["+5V","/LC","/LED2","/U4D-"], "gained": ["/LED3","/U4D+","Net-(D21-1)"], "disconnected_pads_before": 63, "disconnected_pads_after": 33, "verdict": "reject"}`. It REVERTED the output to the input.
- **What was true:** the same command with `KICAD_IMPROVEMENT_GATE=0` ships the run's board. board_score:
  - **input:** blocking 33 (broken 33, of which 29 are GND joins);
  - **reverted run:** blocking 10 (unrouted 1, broken 8, DRC 1).

  By the skill's own lexicographic measure (unrouted + broken first), the rejected step was 33 → 9. Losing 4 nets and gaining 3 outvoted 30 reconnected pads. It did add 1 DRC violation, so it was not clean, but the gate's verdict names neither number.
- **Repro:** the command above (gate on) prints the `reject` line. With `KICAD_IMPROVEMENT_GATE=0`, then `py_tools/board_score.py out.kicad_pcb --intent wk/fa10/09_StickHub/intent.json`, it gives BLOCKING=10. Measured outputs are in `wk/fa10/09_StickHub/gapm/`.
- **Existing issues:** #600 (closed; introduced the gate) and #1032 (closed; a scoped call without GND is rejected for GND pads). Neither covers net-count-versus-pad-count disagreement.
- **Cost:** it made run 39's winning recipe (one non-GND pass, then the plane finalize) unusable here, at about 20 min of wall.

## 3. route.py ships a dead branch ending in a dangling via, so check_complete is "not clean" (helper written)

- **Tool / command:** `route.py hj/sc3_a.kicad_pcb hj/sc4_v3.kicad_pcb --nets VIN GND --grid-step 0.025 --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.3 --via-drill 0.15`.
- **What it claimed:** the run's own cleanup passed it. board_score gave blocking 0.
- **What was true:**
  - `check_weird`: `dangling-via` VIN at (147.85, 113.4), whose copper reaches it on B.Cu only, at the end of a 4-segment B.Cu branch (about 9 mm) that serves nothing. It is left over from the earlier VIN route, which this run replaced.
  - Also `stacked-copper` 1 (see #4).
  - So `check_complete` says `INCOMPLETE -- weird_copper: not clean` on a fully connected, DRC-clean board.
  - route.py's dead-end sweep does not remove a branch that ends at a via, and the repo has no standalone delete-only pruner (`cleanup_pipeline` runs only inside route.py).
- **Helper:** `wk/fa10/09_StickHub/helpers/prune_dead_branch.py BOARD NET X Y [--write OUT]`. It walks from the via, stops at a pad, junction or tee, removes the via and 4 segments, and trims the last segment at the D24 tee. Afterwards check_weird is clean and check_complete DONE.
- **Repro:** `python3 -X utf8 py_router/check_weird.py $R/sc4_v3.kicad_pcb`.
- **Existing issues:** #162 (open, same-net redundant copper) is adjacent; nothing covers a dangling via that route.py keeps.
- **Cost:** about 15 min including the helper.

## 4. The plane finalize leaves exact duplicate GND segments (helper written)

- **What was true:** check_weird `stacked-copper: 10` on r2_s4_io and 1 on sc4_v3, all GND, all exact duplicates, from the in-run plane finalize. check_complete reports weird copper as not clean.
- **Helper:** `helpers/dedupe_stacked.py IN OUT` removes exact duplicates (same net, layer, width and endpoints): 16 on r2_s4_io and 9 on sc4_v3. connectivity, DRC and blocking were unchanged.
- **Repro:** `python3 -X utf8 py_router/check_weird.py $R/r2_s4_io.kicad_pcb` gives `stacked-copper: 10`.
- **Existing issues:** **#162 OPEN** ("Same-net redundant copper (self-crossings + stacked duplicates): find the producers"); #606 (closed) added a trim pass that does not catch these.
- **Cost:** about 10 min.

## 5. compare_seeds probes nothing on a pile whose intent arms the decap rule

- **Tool / command:** `python3 -X utf8 py_placer/compare_seeds.py $R/pile.kicad_pcb --intent $R/intent_rot.json --seeds 4 --out-dir wk/fa10/09_StickHub/repro/cmp --ignore-nets GND --seed-args='--decap-claim-after-ics' --route-args='--track-width 0.1 --clearance 0.1 --via-size 0.3 --via-drill 0.15'`
- **What it claimed:** `compare_seeds: every seed failed its intent gate -- nothing rankable. Fix the intent or the pile first.` (exit 4, `probed 0`; seen on all six seeds 2-7).
- **What was true:**
  - The only intent errors were decap_distance / decap_pin_distance, which no raw seed from a pile can satisfy before the repair pass.
  - `place_seed --repair --repair-decaps` cleared seeds 4 and 5 to 0 errors in about 80 s each, and seed 4 became the board that reached DONE.
  - The advice "fix the intent or the pile" points the wrong way, and the default (no `--probe-gated`) ranks nothing on exactly the input this skill is for.
- **Existing issues:** none found (searched "compare_seeds", "compare_seeds intent gate probe", "probe-gated").
- **Cost:** one wasted 6-way fan-out (about 5 min) and a hand-written seed → repair → route → score pipeline.

## 6. route.py `--json-out` describes a REVERTED attempt, not the shipped board

- **Tool / command:** `python3 -X utf8 py_router/route.py $R/r1_s4_fine.kicad_pcb out.kicad_pcb --json-out out.json --nets /D- /LED7 /U1D+ /U3D- /U4D+ /U7D+ /U7D- VIN +5V GND --rip-existing-nets '*' --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.3 --via-drill 0.15`
- **What it claimed:** `out.json` says `failed 3`, `successful 6`, `total_vias 91`, `failed_multipoint` = [+3.3V, /D-, /LC, /U4D-, /U7D+, D19-1, D21-1, J1-Pin_1, VIN] and `improvement_gate: null`.
- **What was true:** the log ends `IMPROVEMENT GATE ... REJECTED`, and only `JSON_SUMMARY_MIN` carries `"improvement_gate": "reverted"`. The shipped file is byte-identical to the input: blocking 11, 147 vias. The documented machine channel describes a board that does not exist.
- **Existing issues:** #600 (closed, the gate) does not mention the JSON file. Nothing open.
- **Cost:** about 5 min, because I grade with board_score. An automated consumer of `--json-out` would be misled.

## 7. No tool removes plane vias that the pours make redundant (helper written)

- **What was true:**
  - The DONE board carried 53 GND vias on a 2-layer board with GND poured on BOTH layers.
  - Removing a via and its tap branch and re-checking with `check_connected --nets GND` (KiCad refill) showed **6 of 15** candidates removable together: 174 → 168 vias, still DONE.
  - One more is a GND via INSIDE J1's GND contact finger at (146.2, 115.2). It touched 2 tiny stubs, so the helper skipped it; removing it by hand kept GND connected through the F.Cu pour (167 → 166). That is the open #1116 class.
- **Helper:** `helpers/thin_plane_vias.py IN OUT --net GND` (single removals in parallel, then greedy chunks, each checked by check_connected with the KiCad refill).
- **Repro:** `python3 -X utf8 py_router/copy_board.py $R/done1.kicad_pcb $R/thin_out.kicad_pcb && python3 -X utf8 wk/fa10/09_StickHub/helpers/thin_plane_vias.py $R/done1.kicad_pcb $R/thin_out.kicad_pcb` gives `THIN removed 6 GND via(s)` (about 4 min).
- **Existing issues:** **#1116 OPEN** ("route_planes drops a GND via inside a USB plug contact finger, and no checker sees it"). Here the in-run finalize produced it, not route_planes. Nothing covers redundant plane-via thinning.
- **Cost:** about 15 min to write. It gained 7 vias.

## 8. A locked hand join freezes its whole net, and the log points at an override that does not exist

- **Tool / command:** `route.py hj/done1.kicad_pcb opt/b1_5v.kicad_pcb --nets +5V GND --force-reroute --via-cost 150 ...`
- **What it claimed:** `1 PROTECTED net(s) excluded from --force-reroute (locked: +5V) -- name a net exactly (no glob) to override`.
- **What was true:** +5V WAS named exactly, and the run was a no-op (output identical to input). CLAUDE.md says KiCad-locked copper has NO override, so the hint is wrong for locks. The skill tells you to stamp hand joins `(locked yes)`, which silently removes those nets from every later optimisation step.
- **Repro:** run the command above on `$R/../final.kicad_pcb` (carries the locked +5V join), then `cmp` the output with the input.
- **Existing issues:** #150 (closed; locked tracks as obstacles). None about the message.
- **Cost:** one wasted round-1 variant (about 8 min of a parallel slot).

## 9. place_route_loop's built-in accept test cannot see the intent (helper written)

- **What was true:** its own `--help` says the failures-then-iterations test "cannot see ... a decap-proximity limit"; on this board the decap rule is part of `blocking`. I wrote `helpers/accept_blocking.py` (SCORE = board_score unrouted + broken, then the rest, then vias) and passed it as `--accept-cmd`. It worked as documented. The gap is that a skill run needs a hand-written scorer to use the loop on a spec'd board.
- **Existing issues:** none found.
- **Cost:** about 5 min.

## 10. Nothing reports where an edge-mount part's BODY goes (helper written)

- **What was true:** C38 (`CP_Elec_6.3x11_Board_Edge_Mirrored`) has a courtyard over its pads only (local y -4.5..0) and a 6.3 x 11.5 mm fab body beyond them.
  - render_placement draws only the courtyard, and check_assembly lists no pair for it.
  - `helpers/body_overlap.py BOARD --refs C38` showed the body 39.7-61.8 mm² past the east edge and 0 same-side body overlaps, so it was fine. Only the helper could say so.
- **Repro:** `python3 -X utf8 wk/fa10/09_StickHub/helpers/body_overlap.py $R/rep_s4.kicad_pcb --refs C38`
- **Existing issues:** #1000 / #959 (closed) compile edge-mount setbacks only when the brief declares an interface; this brief declares none.
- **Cost:** about 10 min to rule out a suspected defect.

## 11. `place_seed --repair` exits 4 on a placement every grader passes

- **Tool / command:** `python3 -X utf8 py_placer/place_seed.py $R/seed_4.kicad_pcb out.kicad_pcb --intent $R/intent_rot.json --repair --repair-decaps --ignore-nets GND`
- **What it claimed:** exit 4 (the seed does not satisfy its intent), with `1 unrepairable`.
- **What was true:**
  - JSON_SUMMARY has `grade_errors 0`, `unresolved_refs []` and `complete true`. check_floorplan gives 0 errors, and check_assembly says buildable.
  - The "unrepairable" part is J5, KiCad-locked at its DECLARED pose. Its MP pad is 0.35 mm from the north edge, graded at `edge 0.55 (fixed default)` while the board declares `min_copper_edge_clearance 0.0`.
- **Existing issues:** #967 (closed, a place_pose edge-floor mismatch) is similar but different.
- **Cost:** about 3 min.

## 12. measure.py cannot find a teammate session's transcript

- **Tool / command:** `python3 -X utf8 .claude/skills/pcb-free-agent/scripts/measure.py --root .` (the skill's command).
- **What it claimed:** `refuse: no transcript under C:\Users\rob\.claude\projects\C--Users-rob-Documents-prive-git-krt-fa10`.
- **What was true:** this run is a teammate subagent, and its transcript is `...\C--Users-rob-Documents-prive-git-KiCadRoutingTools\<parent>\subagents\agent-<id>.jsonl`. Passing that path positionally works.
- **Existing issues:** none found.
- **Cost:** about 5 min.

## 13. kicad_parser silently drops a segment whose `(locked yes)` precedes `(width)`

- **What was true:**
  - I inserted `(locked yes)` before `(width ...)` in two hand joins. KiCad accepts that order, and board_score's KiCad refill saw the +5V join.
  - kicad_parser's segment regex accepts the token only after width or layer, so both segments vanished from the repo's model (747 segments instead of 749). board_score then reported Net-(D16-1) still broken, with copper unchanged.
  - The order was my non-canonical edit; the silent drop is the tool's part (the #748 shape, for segments).
- **Repro:** `python3 -X utf8 -c "import sys;sys.path[:0]=['.','py_router'];from kicad_parser import parse_kicad_pcb;print(len(parse_kicad_pcb('wk/fa10/09_StickHub/repro/locked_before_width.kicad_pcb').segments))"` gives 747. The same board with the token after width (`hj/cand2.kicad_pcb`) gives 749.
- **Existing issues:** none found (searched "locked yes segment parser order").
- **Cost:** about 10 min.

## 14. make_film `--from-ledger` titles every film `_film`

- **Tool / command:** `python3 -X utf8 py_tools/make_film.py --from-ledger wk/fa10/09_StickHub/ledger.jsonl --theme light --aspect 4:3 -o wk/fa10/09_StickHub/09_StickHub_film.mp4` (the skill's command).
- **What it showed:** the title bar of the final frames reads `_film`. That is the name of the scratch work directory `make_film.py` creates beside the ledger (`work = <ledger dir>/_film`, make_film.py:142-143), not the board or the run. The output file was named `09_StickHub_film.mp4`, and `--help` offers no title option.
- **Repro:** the command above, then look at the last frame (`grade/frames/t50.png`).
- **Existing issues:** none found (searched "make_film title"). Cosmetic.
- **Cost:** about 3 min.

---

Not tool gaps, but measured here and worth knowing:
- **route_diff-first chains wall in later nets.** USB pairs first (all connected), then route.py: LED and misc nets failed (blocking 10-20 against 6 without it). This is open **#677** ("A diff pair from an earlier step can wall in later signal nets").
- **Copper on the USB-A plug tongue (verifier observation).** There is a GND F.Cu ring around the tip and VBUS F.Cu crossing near the finger tips, all under mask. The input carries no keep-out (the fa10 staging removed small rule areas), so nothing can grade it. #1098 (closed) covers parts only, not copper.
