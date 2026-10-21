# TOOL_GAPS -- gp14 board 09 (StickHub)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`, venv python 3.13 first on PATH); every
input it needs is under `wk/gp14/09_StickHub/repro/`.

## 1. route.py: the in-run GND plane repair rips a fully routed 17-pad rail (+3.3V) and ships it with NO copper at all

- **Tool / command:** `py_router/route.py` (the route step's in-run plane finalize: GND pad repair).
- **What it claimed:** the log reports, during the GND pad repair, `blocked by +3.3V - ripping... (#517 ordering: immediate reconnect of 1 ripped net(s): +3.3V)`;
  `routed_single` earlier in the run lists `+3.3V`; `JSON_SUMMARY_MIN.pad_pairs_open` = `{"count": 1, "nets": ["/U7D-"]}` (no +3.3V).
- **What was true:** the written board has **0 segments and 0 vias on +3.3V** (17 pads, 7 of them U1 supply pins).
  `check_connected` reports `Unrouted nets (1): +3.3V (17 pads)`; `board_score` unrouted=1. The run's own regrade does see it
  (`failed_multipoint` +3.3V 16 pads, `multipoint_deficit` 17), so `failed` is right but `pad_pairs_open` omits the net
  and nothing says the copper of an already-routed net was removed. Hit three times, on every first `route.py` pass with the
  fine parameters (scratch B, scratch E, and the shipped chain's `final_route/step3`); the next `route.py` pass re-routes it.
- **Cost:** a full extra iteration on every chain, and it made a board missing a whole rail rank as well as the shipped one (gap 4).
  It also forced `final_route/step4` to be the shipped board rather than step3.
- **Reproduce (about 60 s):**
  ```
  python3 -X utf8 py_router/route.py wk/gp14/09_StickHub/repro/g1_step2.kicad_pcb wk/gp14/09_StickHub/repro/g1_out.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.25 --power-nets GND '+5V' VIN 'Net-(J1-Pin_1)' '+3.3V' '+1V8' --power-nets-widths 0.2 0.3 0.3 0.3 0.2 0.2 --layer-costs 1.0 1.0 --grid-step 0.05 --json-out wk/gp14/09_StickHub/repro/g1_out.json
  python3 -X utf8 py_router/check_connected.py wk/gp14/09_StickHub/repro/g1_out.kicad_pcb   # -> Unrouted nets: +3.3V (17 pads)
  ```
  (measured on the repro copy: `+3.3V segments 0 vias 0`; `grep -c 'immediate reconnect of 1 ripped net(s): +3.3V' g1_out.log` = 2.)
- **Existing issues:** `gh issue list --search "plane finalize ripped net lost"` -> #600 (CLOSED, "route.py rip-and-restore ships
  disconnected nets: in-run finalize and --rip-existing-nets both regress already-routed copper"), #1156 (CLOSED, route.py rips
  out-of-scope routed nets...). Same family, both closed; this is a live instance on the current branch. No open issue found.

## 2. place_simple: error-graded intent limits left broken on every judged seed, a crystal 15 mm from its IC, ESD diodes up to 9.4 mm from their connector pins

- **Tool / command:** `py_placer/place_simple.py --round` (r1, r2, r3; 36 placements).
- **What it claimed:** every seed `illegal: []`, exit 0, and the judge list names them as candidates; the `--json` report carries
  `decap_broken` but nothing on the console or in `judge.json` says an error-graded limit is still broken.
- **What was true:** `decap_broken` was 2..10 on the judged seeds of every round (r1 s8, the kept seed: 4; r3 with
  `--decap-limit-weight 30 --claim-limit-weight 30`: still 0..5, and the one seed with 0 had `claim_broken` 3).
  `check_floorplan --intent intent.json` on r1 s8: 2 ERRORs (`decap_pin_distance` U1 pin 8 at 2.23 mm vs 1.77;
  `decap_ungraded` C18 at 5.65 mm). The crystal claim (`placement.crystals`, 8.1 mm, warning-graded) was broken by ~7 mm:
  Y1 sat 14.8 mm from U1 XI/XO. 4 hand `place_pose` moves were needed (CHOSEN.json `after`). Separately, the MST wire term is
  indifferent to where a 3-pad ESD net's diode sits along the connector-to-chip path, so TVS diodes landed far from their
  connector pins: on the kept placement D7 (/U4D-) is 9.41 mm from J5's pin, D3 6.49 mm from J3, D14 5.61 mm from J8
  (placement-lessons: ESD 2.0 mm from the D pins). D14's detour is on the path of the one net the board ships open (/U7D-'s partner).
- **Cost:** ~25 min of hand moves and measurement; and a structural weakness on the shipped board (ESD far from pins) that the objective never saw.
- **Reproduce (about 15 s, gives exactly r1 seed 8):**
  ```
  python3 -X utf8 py_placer/place_simple.py wk/gp14/09_StickHub/repro/g2_fixed.kicad_pcb 'wk/gp14/09_StickHub/repro/g2_s{seed}.kicad_pcb' --groups wk/gp14/09_StickHub/repro/g2_groups.json --intent wk/gp14/09_StickHub/repro/g2_intent.json --seeds 8 --clustered-seeds 8 --json 'wk/gp14/09_StickHub/repro/g2_s{seed}.json'
  python3 -X utf8 py_tools/check_floorplan.py wk/gp14/09_StickHub/repro/g2_s8.kicad_pcb --intent wk/gp14/09_StickHub/repro/g2_intent.json   # 2 ERRORs
  ```
  (`g2_s8.json` final: cost 1352.2, decap_broken 4, claim_broken 1, illegal [].)
- **Existing issues:** searches "decap_broken place_simple", "crystal claim warning place_simple", "ESD TVS connector place_simple": none.

## 3. converge.py record refuses the first full-route row after the skill's quick_score rows ("false improvement")

- **Tool / command:** `py_placer/converge.py record --kind completion --score-file <board_score --json>`.
- **What it claimed:** `record: this lap looks like an IMPROVEMENT only because it graded FEWER components ... blocking 21 -> 13,
  but the components that differ are: impedance ...; length ...; net_widths ... Nothing was written.` (exit 2).
- **What was true:** the opposite. The "previous accepted lap" was a judging route scored with `py_tools/quick_score.py`, which is
  what SKILL.md §3.6 step 2 prescribes. quick_score's JSON (`blocking_by: {"broken": N}`) grades only the route tally but declares
  no `ungraded` list, so `converge.ungraded_set` reads it as having graded EVERYTHING, and board_score's honest
  `ungraded: [impedance, length, net_widths]` then looks like fewer components. Every full-route lap after a fast-route lap hits it.
- **Workaround used:** re-scored `r1/s8_fast` with `board_score` and recorded that row first (ledger row 27), so later rows compare like with like.
- **Cost:** ~10 min.
- **Reproduce:**
  ```
  python3 -X utf8 py_placer/converge.py record --ledger wk/gp14/09_StickHub/repro/g3_ledger.jsonl --board wk/gp14/09_StickHub/repro/g3_s8_fast.kicad_pcb --kind completion --lever quick --score-file wk/gp14/09_StickHub/repro/g3_quick.score.json
  python3 -X utf8 py_placer/converge.py record --ledger wk/gp14/09_StickHub/repro/g3_ledger.jsonl --board wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --kind completion --lever full --score-file wk/gp14/09_StickHub/repro/g3_full.score.json   # exit 2, refused
  ```
- **Existing issues:** "quick_score ungraded converge record", "commensurability quick_score": none.

## 4. board_score's `blocking` ties "a 17-pad rail with no copper" with "one stranded pad", and the skill's lexicographic tie-break then prefers the rail-less board

- **Tool / command:** `py_tools/board_score.py` (and the skill's "fewest blocking, then vias, copper_mm, segments").
- **What it claimed:** scratch B s3: `BLOCKING=1 (unrouted=1 broken=0) vias=117 copper_mm=704.04`;
  shipped board: `BLOCKING=1 (unrouted=0 broken=1) vias=132 copper_mm=773.42`. By the rule, B s3 is the better board.
- **What was true:** B s3 has +3.3V (17 pads, every VCC33 pin of U1) completely unconnected (pad deficit 16); the shipped board
  has one pad (U1.37) off its net. The fewer vias and less copper on B s3 are exactly the missing rail. I shipped the one-pad board
  against the letter of the rule; REPORT.md says why.
- **Cost:** a judgement call against the skill's own rule; no time.
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/board_score.py wk/gp14/09_StickHub/repro/g4_rail_missing.kicad_pcb --quiet
  python3 -X utf8 py_tools/board_score.py wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --quiet
  python3 -X utf8 py_router/check_connected.py wk/gp14/09_StickHub/repro/g4_rail_missing.kicad_pcb   # +3.3V (17 pads) unrouted
  ```
- **Existing issues:** "blocking unrouted pads tie": none relevant.

## 5. SKILL wording: "CAGED is geometry" does not say which board to measure; on a routed board check_reachability calls every congestion failure CAGED

- **Tool / command:** `py_tools/check_reachability.py --pad`; plan-pcb-placement SKILL.md §4 ("PASSABLE is a router problem, CAGED is geometry") and §5 rule 4.
- **What it claimed:** on the routed board (`final_route_old1/step4`), 10 of 11 stranded pads read `CAGED for any track width`
  (C28.1, J4.2, D12.2, D11.2, R3.2, U1.41, D17.GK ...); on the shipped board U1.37 reads `CAGED for any track width`.
- **What was true:** every one of them is `PASSABLE` on the unrouted placement (+150 to +2119 um at 0.15 mm), and the next router
  parameters connected all but one. The tool walls the pad with other nets' rippable copper, so "CAGED" there means congestion,
  which the skill's rule would misclassify as a placement (geometry) problem. I measured on the placement board instead.
- **Cost:** ~5 min, and it nearly sent the run to re-placement on a router problem.
- **Reproduce:**
  ```
  python3 -X utf8 py_tools/check_reachability.py wk/gp14/09_StickHub/repro/g4_one_pad.kicad_pcb --pad U1.37 --track 0.127   # CAGED
  python3 -X utf8 py_tools/check_reachability.py wk/gp14/09_StickHub/repro/g6_placed.kicad_pcb --pad U1.37 --track 0.127   # PASSABLE
  ```
- **Existing issues:** "check_reachability CAGED routed board": none.

## 6. route_diff / route.py descents lower the Default class chain-wide even under `--clearance-ceiling`

- **Tool / command:** `py_router/route_diff.py ... --clearance-ceiling 0.15` then `route.py ... --clearance-ceiling 0.15`.
- **What it claimed:** disclosed (`DEFAULT CLASS CLEARANCE LOWERED BY A DESCENT -- 0.15 -> 0.1442 mm`, then `0.15 -> 0.127`).
- **What was true:** as disclosed, but the consequence is that the ceiling a later step passes no longer bounds anything: one
  0.1442 mm descent on /D- in the diff step re-graded every Default net of the chain at 0.1442, then a descent on +1V8 took the
  whole board to 0.127. Not silent, so ranked low; it means a chain cannot hold the board's authored 0.15 clearance with the default
  `--escalation fab` without passing a different escalation policy.
- **Cost:** none directly (the final chain deliberately routes at 0.127).
- **Reproduce:** `grep -n 'LOWERED BY A DESCENT' wk/gp14/09_StickHub/final_route_old1/step2.log wk/gp14/09_StickHub/final_route_old1/step3.log`
- **Existing issues:** "finalize rip no copper" search surfaced #1262 (OPEN, `--escalation board` clearance reporting) -- related area, not this.

## 7. Routing skill's fanout predicate selects LQFP-48 for qfn_fanout; on this board it made the judging route worse

- **Tool / command:** plan-pcb-routing SKILL.md Step 3 predicate (`pad_count > 40 and pitch <= 0.8`) -> `py_router/qfn_fanout.py --component U1`.
- **What it claimed:** the predicate marks U1 (LQFP-48, 0.5 mm) as needing fanout; `qfn_fanout` escaped 34/34, 0 grazes.
- **What was true:** the r1 s0 judging route went from blocking 25 (no fanout) to 30 (with fanout + the cap pass), vias 70 -> 77.
  The skill does say to check benefit; I measured it and dropped the step.
- **Cost:** ~3 min.
- **Reproduce:**
  ```
  python3 -X utf8 py_router/qfn_fanout.py wk/gp14/09_StickHub/repro/g7_s0_poured.kicad_pcb --output wk/gp14/09_StickHub/repro/g7_fan.kicad_pcb --component U1 --nets '*' '!GND' --width 0.15 --clearance 0.15
  ```
  then the judging chain (route_diff --quick 2, route.py --quick 2) on each and `py_tools/quick_score.py`.
- **Existing issues:** "qfn_fanout LQFP": #97 (CLOSED, stubs unroutable at default parameters) -- related.

## 8. board_context --md on a pile prints ~650 pin-order CROSSED/AGREES verdicts read off staging poses

- **Tool / command:** `python3 -X utf8 py_tools/board_context.py wk/gp14/09_StickHub/repro/g8_pile.kicad_pcb --md`
- **What it claimed:** a 650-row "Pin-order agreement" table (e.g. `J1 | U1 | pair /D+//D- ... CROSSED`, `C1 | U2 ... CROSSED`).
- **What was true:** every part is in the staging pile (board_brief: `pile: true`, 100% off the outline); pin order between parts
  at staging poses means nothing, while board_context's own other sections do withhold pose-derived claims on a pile.
- **Cost:** ~2 min of reading; a reader could take "CROSSED J1/U1" as a fact about the design.
- **Existing issues:** "pin-order pile board_context": none.

## 9. No helper scripts were saved; inline measurements I had to write

No file was written to `helpers/`. I did use short inline python (read-only) where no tool printed the number I needed:
a compact part table from `board_context --json`; each Y1 rotation's leg lengths before a `place_pose`; each TVS diode's distance
to its connector pin (gap 2); and the per-net segment/via count that exposed gap 1. The last two are worth a tool:
`check_connected` says "+3.3V unrouted" but nothing in the route log says the run REMOVED it.
