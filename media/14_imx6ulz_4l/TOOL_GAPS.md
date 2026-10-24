# TOOL_GAPS -- gpm board 14 imx6ulz_4l

Ranked by what each cost this run. Every command runs from WT (`~/Documents/git/krt-gpm`) with the venv's
`python3`; the boards they need are copied into `wk/gpm/14_imx6ulz_4l/repro/`. `gh` searches are read-only
`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "<keywords>"` (titles only).

## 1. No router step routes to the board's `.kicad_dru` length window, and `--length-match-group` cannot aim at one

- **Tool / command:** `py_router/route.py ... --length-match-group '/DRAM/DRAM_DQ[0-7]' --length-match-tolerance T`, on a board whose `.kicad_dru` declares `byte0 delay matching`: DRAM_LDQ (DQ0-7) total length 11.5-14.5 mm.
- **What it claimed:** every route step prints `.kicad_dru rule 'byte0 delay matching': length is not routed to; check_drc grades it`. The length matcher's only target is the group's longest member.
- **What was true:** the first full route (arm A) shipped 6 of the 8 DQ nets out of the window (DQ1 11.15, DQ2 10.67, DQ3 11.30, DQ6 9.04 short; DQ5 17.44, DQ7 21.54 long) -- 6 blocking `length-out-of-range` DRC rows that no routing flag addresses. Re-routing the lane on the full board with matching made it worse (target 21.87 mm: all 8 out). On the bare poured board DQ5 routes 14.76 alone with all 8 together, so a one-call match targets 14.76 > 14.5 and fails by construction. Three further behaviours made it a search, not a setting: (a) a member already in a matched group is PROTECTED and silently drops out of every later group's target ("route the whole group in one step to meander it"), (b) a mid-bus net gets `No straight run with clearance found for meanders` and ships at its natural 8.7 mm while the call reports the group matched, (c) a rip victim re-routed by the same call is re-matched short. It took 25 route.py orders (`helpers/dq_sequence_search.py`) to find one that lands all 8 in the window: `DQ4+DQ6 | DQ2+DQ5 | DQ3+DQ7 | DQ0+DQ1`, each step pairing a short net with a longer anchor, `--meander-amplitude 0.5 --length-match-tolerance 0.8`, laid BEFORE the BGA fanout. Shipped: DQ0 13.06, DQ1 12.83, DQ2 14.41, DQ3 13.25, DQ4 12.10, DQ5 14.29, DQ6 12.03, DQ7 12.86 mm.
- **Cost:** ~1 h of the run (11:00-12:00Z) plus a helper.
- **Reproduce:** `python3 -X utf8 py_router/route.py wk/gpm/14_imx6ulz_4l/repro/dq_poured.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/dq_all8.kicad_pcb --nets /DRAM/DRAM_DQ0 /DRAM/DRAM_DQ1 /DRAM/DRAM_DQ2 /DRAM/DRAM_DQ3 /DRAM/DRAM_DQ4 /DRAM/DRAM_DQ5 /DRAM/DRAM_DQ6 /DRAM/DRAM_DQ7 --length-match-group '/DRAM/DRAM_DQ[0-7]' --length-match-tolerance 0.8 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 2.5 1.0 --track-width 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --no-bga-zones --escalation board` then `python3 -X utf8 py_router/check_drc.py wk/gpm/14_imx6ulz_4l/repro/dq_all8.kicad_pcb` (length rows); the search: `python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/dq_sequence_search.py wk/gpm/14_imx6ulz_4l/repro/dq_poured.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/seq "57|012346m"` (DQ3 short), and with `DQ_AMP=0.5 DQ_TOL=0.8` in the environment, `"46m|25m|37m|01m"` (all 8 in the window).
- **gh search** `"length-match target window"`, `"length window kicad_dru router"`: none for route.py. #1363 (OPEN) "Bus step: tune its lanes to the board's .kicad_dru length and skew rules" is the bus-step half only.

## 2. A DDR3 strobe pair ships uncoupled (DQS1 0.00 of 25.10 mm coupled, skew 15.47 mm) on a board every gate calls DONE
- **Tool / command:** the first shipped chain's `py_router/route_diff.py <fanned board> s5_diff.kicad_pcb --nets '/DRAM/DRAM_CLK0_*' '/DRAM/DRAM_DQS*' ... --diff-pair-intra-match` after both BGA fanouts. Then `py_tools/board_score.py`, `check_complete.py` and the skill's `grade.py` on the delivered board.
- **What it claimed:** route_diff did say it: `Diff pairs: 0/3 routed`, `single_ended_diff_pairs` = all three. It then routed the six members single-ended (`SE FALLBACK ROUTED` x5) and left DQS0_N for route.py. Downstream, board_score printed `BLOCKING=0` with `DIFF PAIRS: 3 measured (not graded: no .kicad_dru skew / diff_pair_uncoupled rule)`. check_complete printed `VERDICT: DONE` with diff_pairs listed UNEXAMINED. grade.py printed `done: true`.
- **What was true:** the delivered board (DONE #1) had DQS1 coupled 0.00 of 25.10 mm with 15.467 mm P/N skew, and CLK0 coupled 3.13 of 42.19 mm with 4.242 mm skew. The board names these pairs only by `_P`/`_N`, and its one pair rule (`target length and skew`, netclass `DF_100ohm`) names a netclass the project does not have, so it applies to nothing. No gate fails a DDR3 strobe routed as two unrelated tracks. Verifier call 1 failed the board on the spec lens for this. The fix cost a re-built chain: the pairs routed coupled from the bare balls BEFORE the fanouts (arms A9-A17, gap 3), which shipped DQS0 skew 0.424, DQS1 0.309, CLK0 0.020 mm.
- **Cost:** one verifier call, ~40 min (12:47-13:26Z), two helpers (gaps 3, 7).
- **Reproduce:** `python3 -X utf8 py_tools/board_score.py wk/gpm/14_imx6ulz_4l/repro/done1_delivered.kicad_pcb --intent wk/gpm/14_imx6ulz_4l/intent_run.json --baseline wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25 --quiet` (BLOCKING=0; DIFF PAIRS: DQS1 15.467mm, coupled 0.00 of 25.10mm). Then `python3 -X utf8 check_complete.py wk/gpm/14_imx6ulz_4l/repro/done1_delivered.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25` (VERDICT: DONE).
- **gh search** `"diff pair skew ungraded"`, `"diff_pairs ungraded"`: none. `"pair coupling not graded"`: #1303 (CLOSED) "route_diff reports a pair "coupled" and "matched" that the written copper is not...". That is the dru-rule half, which board_score now grades. Nothing covers a pair the board declares by name only.

## 3. Pairs routed before the fanout wall in a plane ball and an escape ball, and only hand vias freed them
- **Tool / command:** the fix for gap 2: `py_router/route_diff.py final_route/s1e_dq01.kicad_pcb ... --nets '/DRAM/DRAM_CLK0_*' '/DRAM/DRAM_DQS*' --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 2.5 1.0 ... --diff-pair-intra-match`, laid on the DQ-routed board before `bga_fanout` (arm A9). Then the same fanout / cap / route.py x3 chain.
- **What it claimed:** route_diff `Diff pairs: 3/3` coupled. The later route.py steps reported failed 0 and ran their in-run plane finalize.
- **What was true:** A9's last board is BLOCKING 1. VMEM is broken, with U2 pad at (73.6, 107.8) F.Cu stranded. The early pair and DQ lanes take the only drop site next to U2.C1, and neither the fanout nor the plane finalize (nor a rip lap) can reach the In2 pour from it. route_diff reserves nothing for a ball that a later step must drop to a plane. Six re-orderings (A10-A15: pairs after the fanouts, split pair steps, In2 cost 4/6, DQS0 alone first) each lost a pair to single-ended or broke 1-4 nets. They were explored with `helpers/pair_order_search.py`. What worked was a hand VMEM via-in-pad at U2.C1 placed BEFORE the pair step (`check_join ... VMEM 73.6,107.8,F.Cu 73.6,107.8,In2.Cu via:73.6,107.8 --keep-staged`, A16). That moved the box to DQ13 at U1.P3. A second hand dog-bone via (82.4, 105.0) before the fanouts (A17) gave BLOCKING 0.
- **Cost:** part of gap 2's 40 min, six rejected arms, a helper.
- **Reproduce:** `python3 -X utf8 py_tools/board_score.py wk/gpm/14_imx6ulz_4l/repro/a9_routed.kicad_pcb --intent wk/gpm/14_imx6ulz_4l/intent_run.json --baseline wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25 --quiet` (BLOCKING=1, broken VMEM, stranded U2 73.6,107.8). The order search runs from the DQ-routed board: `python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/pair_order_search.py wk/gpm/14_imx6ulz_4l/repro/dq_first.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/po "10C@2.5" "0@6|1C@2.5"`.
- **gh search** `"diff pair blocks plane via"`, `"route_diff force-reroute"`: #677 (OPEN) "A diff pair from an earlier step can wall in later signal nets". Same family, still open. It reproduces here on a plane ball and a fanout ball.

## 4. `bga_fanout` and `place_fanout_clearance` leave escape vias inside foreign pads on the far face (shorts), which only hand moves fixed

- **Tool / command:** `py_router/bga_fanout.py --escape-method dogbone ...` on U1/U2 (0.8 mm, via 0.45 -- the board's own via floor), then `py_placer/place_fanout_clearance.py --clearance 0.1 --intent intent_run.json` (judging chain and arm A).
- **What it claimed:** the fanout `failed: 0` (its `drc_grazes` 23 pad_via); the cap pass `Moved 46 cap(s); resolved 32/44 initial violations; 12 unresolved`, the 12 named as needing manual attention.
- **What was true:** the unresolved list is 4 decaps and 8 boot-config 0402 resistors that place_simple had put on B.Cu UNDER U1's ball field; no cap pass can free them because every gap site carries a dog-bone via. Routed (arm A) they shipped 4 PAD-VIA violations **in CONTACT** (GND vias in R19.1, C23.1, R53.2, ... -- shorts) and 6 pad-segment grazes. Clearing it took 19 hand `place_pose` moves (14 resistors out of the field, C13/C23/C48/C33 to via-free sites, R2 out of the DDR corridor) and four re-routes (arms A2-A4: 17 -> 15 -> 8 -> 6 blocking). place_simple has no notion of a BGA's escape field, so it seats strap resistors there on every seed.
- **Cost:** ~40 min (10:48-11:30Z), and the courtyard overlaps of gap 11.
- **Reproduce:** `python3 -X utf8 py_router/check_drc.py wk/gpm/14_imx6ulz_4l/repro/armA_routed.kicad_pcb --clearance-margin 0.1` (PAD-VIA ... in CONTACT) and `python3 -X utf8 py_placer/place_fanout_clearance.py wk/gpm/14_imx6ulz_4l/repro/armA_fanned.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/armA_caps.kicad_pcb --clearance 0.1 --intent wk/gpm/14_imx6ulz_4l/intent_run.json` (12 unresolved).
- **gh search** `"dog-bone via foreign pad"`, `"place_fanout_clearance unresolved"`: #213 (CLOSED) "bga/qfn fanout: escape vias violate clearance to neighbouring pads (esp. cap pads); cap-placement remedy incomplete on dense boar...", #130 (CLOSED), #313 (CLOSED) "fanout/cap-opt: residual foreign-pad grazes survive to the final board". Same family, closed; it reproduces here as contact.

## 5. `fill_for_delivery` re-saves the board as KiCad 10 with explicit `(capping no) ... (filling no)` on every via: a DONE board grades 212 blocking

- **Tool / command:** `python3 -X utf8 py_tools/fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` (skill §3.9 step 2).
- **What it claimed:** `Filled ... net classes preserved: 4; unconnected (no --refill-zones): 145 -> 0`, exit 0.
- **What was true:** the input is version 20240108; the output is version 20260206 and every one of the 461 vias gained `(capping no) (covering (front no) (back no)) (plugging (front no) (back no)) (filling no)` (the input vias carried no token). board_score: `routed.kicad_pcb` BLOCKING 0 (`via_in_paste: undeclarable 212`), `delivered.kicad_pcb` **BLOCKING 212 (`drc_via_in_paste=212`)** on identical copper; check_complete INCOMPLETE. The 215 via-in-pad/paste sites are the chain's own vias, which route.py would have stamped Type VII had the format allowed. Fixed with `helpers/stamp_type_vii.py`: strip exactly the all-"no" block, then run the repo's own `fab_notes.ship_via_protection_file` (215 stamped `(capping yes) (filling yes)`) -> BLOCKING 0, check_complete DONE, kicad-cli loads it, fill intact. The shipped DONE #2 board (377 vias) went the same way: fill_for_delivery rewrote every via, and the helper stamped 194 Type VII (check_drc: `193 filled+capped`, 0 unprotected). `repro/delivered2_unstamped.kicad_pcb` is that fill output before the helper.
- **Cost:** ~15 min and a helper.
- **Reproduce:** `python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/14_imx6ulz_4l/repro/labelled.kicad_pcb -o wk/gpm/14_imx6ulz_4l/repro/filled.kicad_pcb` then `python3 -X utf8 py_tools/board_score.py wk/gpm/14_imx6ulz_4l/repro/filled.kicad_pcb --baseline wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb --quiet` (drc_via_in_paste=212); the same on `repro/labelled.kicad_pcb` reads 0. `repro/delivered_unstamped.kicad_pcb` is this run's own filled output before the helper.
- **gh search** `"fill_for_delivery via-in-paste"`, `"fill_for_delivery capping"`: none. `"via protection tokens KiCad 10 save"`: #751 (CLOSED, the GUI reader) only.

## 6. route.py ships dangling stubs, sub-floor pad webs and pad-internal redundant stubs on a blocking-0 board, and nothing removes them

- **Tool / command:** the full chain's last `route.py --nets '*'` (and two more iterations with the same flags, and a `--force-reroute` lap, which the improvement gate reverted).
- **What it claimed:** `JSON_SUMMARY_MIN` failed 0; board_score BLOCKING 0.
- **What was true:** check_weird: 5 items -- +3V3 F.Cu stub dangling 1.27 mm at (97.6, 99.2); a 4.96 mm VMEM F.Cu tail past L3.2 at (93.1, 96.4); three terminal caps joining a pad through a web below the 0.1 mm floor (GND U1.F8, DRAM_VREF C39.1, NVCC_PLL_OUT C9.1) -- and, once those webs were widened, 7 pad-internal stubs on DRAM_VREF/NVCC_PLL_OUT that the narrow-joint finding had been masking. check_complete INCOMPLETE on them. Fixed after the last route step: 4 `check_join` joins (CLEAN each) and `helpers/remove_segments.py` for the 2 + 7 dead segments, because no repo tool deletes a dead-end stub. The shipped DONE #2 chain needed the same after its last route.py step: 1 `check_join` join (NVCC_PLL_OUT at C9.1, `--width 0.15`) and 4 removals (2 dangling VMEM B.Cu stubs, 1 dangling DQ1 via at 73.2,108.2, 1 pad-internal NVCC_PLL_OUT stub).
- **Cost:** ~20 min and a helper.
- **Reproduce:** `python3 -X utf8 py_router/check_weird.py wk/gpm/14_imx6ulz_4l/repro/route_weird.kicad_pcb` (5 items) and `python3 -X utf8 check_complete.py wk/gpm/14_imx6ulz_4l/repro/route_weird.kicad_pcb` (INCOMPLETE: orphan_stubs, weird_copper).
- **gh search** `"dangling stub cleanup"`, `"narrow-pad-joint"`: #1063 (CLOSED) "check_weird flags in-pad/in-via wiggles that route.py's cleanup keeps by design, so no route.py output reaches check_complete DO...", #1334 (CLOSED), #162 (OPEN, same-net redundant copper). Closed, and it reproduces.

## 7. `route_diff.py` cannot re-route a pair that is already connected (no `--force-reroute`, no `--rip-existing-nets`)
- **Tool / command:** `py_router/route_diff.py <DONE #1 routed board> out.kicad_pcb --nets '/DRAM/DRAM_CLK0_*' '/DRAM/DRAM_DQS*' ... --diff-pair-intra-match` (the obvious fix for gap 2: re-route the single-ended pairs as pairs).
- **What it claimed:** `Skipping 6 already-routed net(s): Already fully connected`, `All nets are already fully connected - nothing to route!`, exit 0.
- **What was true:** the pairs were connected but uncoupled. route.py has `--force-reroute` and `--rip-existing-nets`, but route_diff has neither, so no CLI turns a single-ended pair back into a coupled one. I wrote `helpers/strip_nets.py` to delete the six members' copper so that route_diff saw them unrouted. In the end the chain was re-built instead (gap 3).
- **Cost:** ~5 min and a helper.
- **Reproduce:** `python3 -X utf8 py_router/route_diff.py wk/gpm/14_imx6ulz_4l/repro/done1_routed.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/done1_rediff.kicad_pcb --nets '/DRAM/DRAM_CLK0_*' '/DRAM/DRAM_DQS*' --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 2.5 1.0 --via-size 0.45 --via-drill 0.25 --escalation board --diff-pair-intra-match` (log kept as `repro/done1_rediff.log`). `python3 -X utf8 py_router/route_diff.py --help | grep -c -E 'rip-existing|force-reroute'` prints 0.
- **gh search** `"route_diff force-reroute"`, `"route_diff rip-existing-nets"`: #515 (CLOSED) "Proposal: --force-reroute flag to rip + freshly re-route already-connected nets". It landed on route.py only. #677 (OPEN) is related.

## 8. `check_join --keep-staged` does not record into the redo manifest, so the shipped chain's `redo_commands.sh` is not replayable
- **Tool / command:** `py_tools/check_join.py <board> NET a b via:x,y --keep-staged <out>`, run with `REDO_RUNDIR`/`REDO_MANIFEST` set (TASK.md). The shipped chain has two such joins mid-chain (gap 3) and one after the last route step.
- **What it claimed:** `CLEAN`, and the staged board written.
- **What was true:** no line is appended to the manifest (copy_board, route_planes, route, route_diff, bga_fanout and place_fanout_clearance all record themselves). `final_route/redo_commands.sh` holds 13 commands and no check_join. Its route_diff step reads `final_route/s1e_c1via.kicad_pcb`, and its U1 fanout reads `s1f_dq13.kicad_pcb`. Only the hand joins write those files, so a no-LLM replay of the manifest dies at step 7. Documented by hand in `final_route/hand_join_1.sh` / `hand_join_2.sh` and the split plan files. The post-route `helpers/remove_segments.py` step is likewise unrecorded.
- **Cost:** small. The replay contract is broken for this chain.
- **Reproduce:** `REDO_RUNDIR=$PWD/wk/gpm/14_imx6ulz_4l/repro/cj REDO_MANIFEST=$PWD/wk/gpm/14_imx6ulz_4l/repro/cj/redo_commands.sh python3 -X utf8 py_tools/check_join.py wk/gpm/14_imx6ulz_4l/repro/dq_first.kicad_pcb VMEM 73.6,107.8,F.Cu 73.6,107.8,In2.Cu via:73.6,107.8 --keep-staged wk/gpm/14_imx6ulz_4l/repro/cj/c1via.kicad_pcb` (CLEAN). Then `ls wk/gpm/14_imx6ulz_4l/repro/cj` shows no redo_commands.sh, and `grep -c check_join wk/gpm/14_imx6ulz_4l/final_route/redo_commands.sh` prints 0.
- **gh search** `"check_join redo manifest"`, `"redo_commands hand join"`, `"redo manifest not replayable"`: none. `"check_join keep-staged"`: #1360 (CLOSED) "Skill says to stamp hand-written joins `(locked yes)`, but no tool commits or locks a segment". That is related (hand joins have no committing tool), not this.

## 9. place_simple prices a one-cap supply pin's decap limit flat, and breaks it in 11/12 seeds

- **Tool / command:** `py_placer/place_simple.py fixed.kicad_pcb 's{seed}.kicad_pcb' --groups groups.json --intent intent_run.json --jobs 4` (passes 1 and 2).
- **What it claimed:** `NOTE: decap limits priced: 123 term(s) (decap_distance 4.39 mm, decap_pin_distance 8.455 mm)`.
- **What was true:** U1 pin P12 (VDD_SNVS_IN) has one decap, C20 (U8's output cap). Pass 1: 11/12 seeds broke `decap_pin_distance` there (21-32 mm against 8.455); pass 2, with U8/C19/C20 moved into U1's group: still 11/12. Every seed's JSON reports `"decap_limits": 5.0, "decap_broken": 1` -- a flat 5 for a 12-24 mm breach. Only an explicit error-graded `proximity[]` row (U8.2 -> U1.P12, 7 mm) fixed it: pass 3 gave 6/12 clean seeds.
- **Cost:** two wasted placement passes (~15 min) and an intent row.
- **Reproduce:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb 'wk/gpm/14_imx6ulz_4l/repro/r{seed}.kicad_pcb' --groups wk/gpm/14_imx6ulz_4l/repro/groups_pass2.json --intent wk/gpm/14_imx6ulz_4l/repro/intent_pass2.json --jobs 4 --json 'wk/gpm/14_imx6ulz_4l/repro/r{seed}.json'`, then read `final.decap_limits` and `floorplan` in each `r<S>.json`.
- **gh search** `"decap limit place_simple"`: #1320 (CLOSED) "place_simple prices a supply-pin decap limit wider than the 5 mm tether radius at a flat 5 mm past the limit, so a one-cap rail's pin is l..." -- the same defect by title; it reproduces on main bda59fa0.

## 10. `bga_fanout --check-for-previous` drops dog-bone vias onto an existing foreign track

- **Tool / command:** `py_router/bga_fanout.py <board with DQ0-7 already routed> --component U2 --nets '*' '!GND' '!+3V3' '!VMEM' ... --escape-method dogbone --check-for-previous` (arm A5).
- **What it claimed:** `requested 46, escaped 46, failed 0`.
- **What was true:** DQ8's and DQM0's gap vias at (71.6, 106.6) and (72.4, 106.6) sit on DQ7's pre-routed F.Cu lane: check_drc 3 VIA-SEGMENT (3 in CONTACT) + 3 SEGMENT-SEGMENT (1 in contact). Worked around by excluding DQ8/DQM0 from U2's fanout (route.py then routed them clean: arm A6 blocking 0).
- **Cost:** one re-route (~10 min).
- **Reproduce:** `python3 -X utf8 py_router/bga_fanout.py wk/gpm/14_imx6ulz_4l/repro/u2_fanout_input.kicad_pcb --output wk/gpm/14_imx6ulz_4l/repro/u2_fanout_out.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' '!VMEM' --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 -1 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 --track-width 0.1 --clearance-ceiling 0.1 --escalation board --check-for-previous` then `python3 -X utf8 py_router/check_drc.py wk/gpm/14_imx6ulz_4l/repro/u2_fanout_out.kicad_pcb --clearance-margin 0.1 --nets /DRAM/DRAM_DQ7` (6 violations).
- **gh search** `"check-for-previous fanout via"`: #1315 (CLOSED) "bga_fanout under-pad/dogbone: an existing track whose start point lies outside the escape window is not stamped, so escapes and ..." -- likely the same defect; it reproduces.

## 11. No courtyard-aware move: place_pose and the cap pass leave 17 KiCad `courtyards_overlap` errors that the repo grades advisory

- **Tool / command:** `py_placer/place_pose.py ... set REF --near X Y` (gap 4's 19 hand moves) and `place_fanout_clearance.py`.
- **What it claimed:** place_pose `legal True, no_worse True` for every move; check_assembly `buildable (blocking 0)`, 16 advisory pairs.
- **What was true:** KiCad DRC on the delivered board: 17 `courtyards_overlap` at severity error (R21/R27, R53/R55, R20/R28, R33/R37, C23/C33, R2/SW1, ...). place_pose grades pads and holes only (documented: courtyards are check_assembly's), so `--near` happily snaps into a neighbour's courtyard; finding courtyard-clean poses took check_assembly in a loop. A courtyard-clean re-layout of the same 19 parts (arms A7, A8) routed to blocking 1 twice, so the shipped board keeps the 17 advisory overlaps.
- **Cost:** ~25 min (two rejected re-route arms).
- **Reproduce:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/14_imx6ulz_4l/repro/s6_placed.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/s6_moved.kicad_pcb set R2 77.2 113.0 --rot 180.0 set C48 87.2 103.0 --rot 180.0 set R45 99.0 118.5 --rot 270.0 set R53 95.25 112.0 --rot 90.0 set R40 97.75 118.95 --rot 90.0 set R54 99.0 114.3 --rot 90.0 set R50 94.5 106.95 --rot 180.0 set R46 95.0 115.45 --rot 0.0 set R20 95.0 110.5 --rot 180.0 set C13 86.4 111.4 --rot 180.0 set R38 97.5 116.8 --rot 90.0 set R27 97.25 109.9 --rot 180.0 set R37 94.75 116.85 --rot 90.0 set C23 88.0 117.6 --rot 180.0 set R56 97.5 113.6 --rot 0.0 set C33 86.6 117.6 --rot 0.0 set R63 98.5 116.5 --rot 270.0 set R64 97.5 114.45 --rot 180.0 set R19 97.5 111.2 --rot 180.0` (legal True, no_worse True) then `python3 -X utf8 py_tools/check_assembly.py wk/gpm/14_imx6ulz_4l/repro/s6_moved.kicad_pcb --baseline wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb` (buildable, 19 advisory courtyard pairs); the routed board's 17 KiCad errors: `python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/14_imx6ulz_4l/delivered.kicad_pcb` (COURTYARD kicad=17 krt_blocking=0).
- **gh search** `"courtyard place_pose snap"`: #1256 (CLOSED, snap ranker) -- not this.

## 12. analyze-power-nets recommends 3.0 mm tracks for BGA rails and 1.2 mm for a DDR reference

- **Tool / command:** the skill's Step 1-5 (`py_tools/analyze_power_paths.py`), followed by hand with the run's classifications.
- **What it claimed:** VMEM 3.0, /SOC Power/VDD_SOC_CAP 3.0, VDD_ARM_SOC_IN 3.0, +3V3 3.0, +5V 3.0, GND 3.0, /DRAM/DRAM_VREF 1.2, NVCC_PLL_OUT 1.0, VDD_SNVS_CAP 1.0 mm.
- **What was true:** the tracer chains every regulator through the shared +5V net and through the other bucks' switch nodes (`Path 11: U6 -> U1 ... VDD_ARM_SOC_IN -> +1V2 -> V1P27_SW -> +5V -> VMEM_SW`) and sums the overlapping paths, so a 650 mA sink lands on every rail of every regulator. DRAM_VREF is a microamp 1.5k/1.5k divider; VDD_SOC_CAP/VDD_SNVS_CAP are bypass rails of the SoC's internal LDOs; a 3 mm track cannot enter a 0.8 mm ball field. Widths set by hand (0.2-0.6 mm).
- **Cost:** ~10 min.
- **Reproduce:** `python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/power_widths_repro.py wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb`
- **gh search** `"power net width recommendation"`, `"analyze-power-nets"`, `"power paths"`: none covers it (#124, closed wontfix, is about widening).

## 13. The bus step's output loses the `.kicad_dru`, and its locked lanes cannot be length-tuned

- **Tool / command:** `python3 -X utf8 awx/route_bus.py <poured board> <out> --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25` (the routing skill's Step 1a, 1841 s).
- **What it claimed:** `BUS U1->U2 ... lanes=39/39 ... on the board: connected=1 drc=1`, exit 0, `locked: 760 track(s) and via(s) of the 41 lane(s) handed on`.
- **What was true:** OUT has `.kicad_pro` only -- no `.kicad_dru`, no `.design-brief.json` -- so `check_drc` on it grades no length rule and prints NO DRC VIOLATIONS while DQ0 15.4, DQ3 16.5, DQ4 16.9, DQ5 28.2, DQ7 26.5 mm are outside the 11.5-14.5 window (DQ6 open). The lanes are KiCad-locked, so no later step can tune them. Arm rejected.
- **Cost:** 31 min of background compute, ~5 min of mine.
- **Reproduce:** `ls wk/gpm/14_imx6ulz_4l/repro/bus_out.*` (no .kicad_dru) and `python3 -X utf8 py_router/check_drc.py wk/gpm/14_imx6ulz_4l/repro/bus_out.kicad_pcb` (no "Length rules" line).
- **gh search** `"route_bus kicad_dru"`: #1316 (CLOSED) "route_bus writes OUT with .kicad_pro only: whole_route's best-round copy and flow_frame.SIBLINGS drop .kicad_dru and .design-bri..." -- same, reproduces; #1363 (OPEN) for the tuning.

## 14. No PDF renderer: the skill's §3.5 datasheet workflow cannot open a page

- **Tool / command:** the Read tool on `datasheets/tlv62568/tlv62568.pdf` (`pages: "1-3"`), and the skill's `pdftotext` / `pdftoppm` recipe.
- **What it claimed:** §3.5 step 2: "open it with the Read tool and `pages`"; "Where poppler is installed: pdftotext ... pdftoppm".
- **What was true:** Read refused (`pdftoppm is not installed`); no poppler, no pypdf/fitz, and installing is outside the folder. Wrote `helpers/pdfpage.swift` (PDFKit page text and PNG crops) to read SLVSD89B Figure 20.
- **Cost:** ~5 min.
- **Reproduce:** `which pdftoppm pdftotext` (empty).
- **gh search** `"poppler pdftoppm"`, `"datasheet PDF"`: none.

## 15. route_plan_check R17 calls a split power layer a "solid plane"; forbidding it cost a ball

- **Tool / command:** `.claude/skills/plan-pcb-routing/scripts/route_plan_check.py final_route/imx6ulz_4l_plan.sh --board final.kicad_pcb`.
- **What it claimed:** `FAIL R17 ... bga_fanout.py --layers includes ['In2.Cu'], which the plan pours a solid plane on`.
- **What was true:** In2 carries a +3V3/VMEM split (route_planes `Spine split`), not a solid plane; the skill's Step 10 rule 3 binds "an INNER layer carrying a solid plane". With In2 priced 2.5 the judging chain escaped U1 108/108; forbidden as R17 demands, arm A dropped BOOT_CFG2_4 (107/108, later routed by route.py).
- **Cost:** small (one dropped ball, routed later).
- **Reproduce:** `python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py wk/gpm/14_imx6ulz_4l/repro/plan_r17_in2_cost.sh --board wk/gpm/14_imx6ulz_4l/repro/s6_placed.kicad_pcb`
- **gh search** `"R17 route_plan_check"`: none.

## 16. One footprint's clearance override becomes the board floor for `--escalation board`

- **Tool / command:** `route_planes.py` (any run on this board), then `bga_fanout.py ... --escalation board`.
- **What it claimed:** route_planes `DRC settings: rules.min_clearance: 0.1 -> 0.08 mm`; the fanout `Under-pad shrink rescue @ ... clearance 0.0900mm` with "dropped ... to the BOARD's own declared minimums; --escalation board bounds it there".
- **What was true:** 0.08 is U2's footprint-level `(clearance 0.08)` override (the board's min_clearance is 0.1), read as `board_floors.clearance: 0.08`; the rescue then escaped U1 balls (no override) at 0.09. check_drc grades the shipped copper clean at the 0.1 classes, so nothing failed, but the descent was below the board's declared 0.1 floor while claiming to stop at it.
- **Cost:** none measurable; disclosed.
- **Reproduce:** `python3 -X utf8 py_router/route_planes.py wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/rp.kicad_pcb --nets GND --plane-layers In1.Cu --clearance-ceiling 0.1` (prints `rules.min_clearance: 0.1 -> 0.08`).
- **gh search** `"footprint clearance override min_clearance escalation"`: #530, #417 (CLOSED, general) -- not this.

## 17. `route_diff.py` has no `--json-out` (route.py has)

- **Tool / command:** the first full-route plan's `route_diff.py ... --json-out s5_diff.json`.
- **What it claimed:** argparse `unrecognized arguments: --json-out`, exit 2; the plan (no `set -e`) ran on and the route steps found no input.
- **What was true:** route.py's merged-summary flag does not exist on route_diff; route_plan_check did not catch it. My error to pass it, but the two siblings disagree.
- **Cost:** one wasted chain start (~2 min).
- **Reproduce:** `python3 -X utf8 py_router/route_diff.py wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb wk/gpm/14_imx6ulz_4l/repro/x.kicad_pcb --nets '/DRAM/DRAM_DQS*' --json-out wk/gpm/14_imx6ulz_4l/repro/x.json` (exit 2).
- **gh search** `"route_diff json-out"`: none.
