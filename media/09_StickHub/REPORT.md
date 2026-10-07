<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT -- fa10 board 09: StickHub, `/pcb-free-agent full`

**Result: DONE.** The input was a pile: all 94 parts were south of the outline and there was no routing. The final board is `wk/fa10/09_StickHub/final.kicad_pcb` (+ `final.kicad_pro`):

- sha256 `4d6fc83894c93f9d310500be9919e4a7cbe655fd94b7f5573a56b488d55810d0`
- **blocking 0, 166 vias, 829.96 mm copper, 830 segments**
- independent verifier: call 1 FAIL, call 2 **PASS**

## 1. Result

| DONE condition (mode `full`) | measured on final.kicad_pcb | source |
|---|---|---|
| board_score blocking 0 | **0** | board_score `--intent intent.json` (also grade.py, verifier call 2) |
| unrouted 0 | **0** | board_score |
| broken 0 | **0** | board_score; check_connected: all 45 nets connected (KiCad refill agrees) |
| check_complete DONE | **DONE** (exit 0) | `check_complete.py final.kicad_pcb --intent intent.json` |
| DRC | 0 violations | check_drc `--baseline` input `--clearance-margin 0.1` (6 same-net self-crossing warnings, permitted by KiCad) |
| weird copper | clean | check_weird |
| assembly | buildable (blocking 0) | check_assembly `--intent` |
| floorplan | 0 errors, 0 violations | check_floorplan `--intent --allow-routed` (exit 4 INCOMPLETE only because the intent withholds the oob_count/overlap_area budgets on a pile) |
| mechanical facts | 9/9 poses exact (H1, J1-J8), 0 side changes | measured against mechanical.json |

- **`blocking_by`:** assembly 0, broken 0, drc 0, floorplan 0, undersized 0, unrouted 0; impedance / length / net_widths `null` (ungraded).
- **Ungraded (UNEXAMINED, not passed):** impedance, length, net_widths. The project declares only the Default class: no diff-pair class, no impedance, no length groups, no per-net widths. The USB pairs (/D±, /U1D±../U7D±) are pairs by name only, so no spec flags apply.
- **Quality (the tie-break once blocking is 0):** vias **166**, copper **829.96 mm**, segments **830**.
- **For comparison only (not a target):** run 39 on the same design reached blocking 0 with 175 vias, 726 mm and 935 segments, but it started with J1-J8 and H1 already placed and locked. Here they started in the pile.

## 2. Stop rules that fired

1. **"If DONE will not come"** fired at about **+2:31**, at blocking 6. After the best route of the search phase (blocking 6, at +0:53), six consecutive different approaches each failed to lower unrouted + broken, measured:
   - route parameters (rip-up 6, via cost 40, grid 0.05, backward direction, equal layer costs, seed 5): 8-18;
   - scoped re-routes with named blockers and with `'*'` at grid 0.1: all reverted by the improvement gate;
   - more placements (seeds 8-11 at U1=270): 12-34;
   - USB diff pairs first via route_diff (+5 second-step variants): 10-20;
   - non-GND nets first, then the GND finalize (run 39's recipe): 33/40, finalize reverted by the gate;
   - place_route_loop (4 rounds, board_score accept test): 15/14/6 (tie, more vias)/7.

   I froze the blocking-6 board and called the verifier with every blocker itemised. All five stranded pads were PASSABLE on the copper-free board (check_reachability, margins 0.40-1.10 mm).
2. **Verifier call 1 FAILED**, naming those five nets. Rule 5 says "fix what it names and continue", so I fixed them:
   - two locked hand joins, each staged with check_join CLEAN: +5V and a D16-1 stub (6 → 4). I staged them while call 1 was still running and applied them after its FAIL named those nets;
   - then a lever none of the six approaches had used: scoped route.py on the named nets **plus GND, at grid 0.05 / 0.025, with no rip flag** (4 → 2 → 1 → 0);
   - then delete-only cleanup of the router's leftovers.

   First DONE came at **+3:25**.
3. **The optimisation stop rule** fired after round 2: two consecutive rounds each cut vias by less than 5% (round 1: 174 → 168, 3.4%; round 2: 168 → 167, 0.6%). After that, one more via (167 → 166) came out as the fix for verifier call 1's observation of a GND via inside J1's GND contact finger. It was not an extra round.

**Remaining blockers: none.** Advisory, graded by no tool: J1 is a PCB-trace USB-A plug, and its tongue still carries F.Cu copper under solder mask:
- a 0.1 mm GND ring around the tip;
- a /D- via at (149.6, 113.2) between the D+ and D- fingers;
- the VBUS and /D+ diagonals near the finger tops (the verifier measured 0.119 mm from the D- finger corner).

The input carries no keep-out for the tongue (the fa10 staging removed small rule areas), so nothing could steer the router off it. A designer should check this.

## 3. Floors (below the board's authored rules; disclosed)

- `check_complete final.kicad_pcb --intent intent.json --authored-from StickHub.kicad_pcb` gives **UNSOUND**: "track width 0.15 -> 0.1, via diameter 0.5 -> 0.25, via annular ring 0.1 -> 0.05, hole diameter 0.25 -> 0.15". The Default class clearance and `min_clearance` also went **0.15 → 0.10** (`--clearance 0.1`, then `--clearance-ceiling 0.1` on later steps). Every checker grades against the new values. **Confirm the fab supports 0.1/0.1 mm and 0.25/0.15 mm vias (the advanced tier).**
- route.py's `Design rules` lines:
  - best search-phase route: "11 feature(s) on 6 net(s) delivered below the requested size (smallest via diameter 0.25 mm); 38 fab-tier escalation(s) to advanced";
  - the scoped DONE-chain steps: 2/5/1/3 features delivered below request (smallest via 0.25 mm), with 12/17/5/4 escalations.
- Routing at the authored floors (0.15/0.15, via 0.5/0.3) was measured and rejected: blocking 28, with route.py escalating 595 features anyway.
- **Via-in-pad:** 84 vias are stamped capped and filled, and 70 of them sit in paste openings (verifier call 2). That is IPC-4761 Type VII work at the fab.

## 4. Timeline (UTC; FIRST_CMD 2026-10-06T20:21:47Z)

| elapsed | event |
|---|---|
| 0:00 | first command |
| 0:28 | **first legal placement**: `b/rep_s4` (seed 4, U1 rot 270, decap repair), floorplan 0 errors, buildable |
| 0:40 | **first routed board**: `r/r1_s4_fine`, blocking 11 (0 unrouted, 11 broken) |
| 0:53 | best of the search phase: `r/r2_s4_io`, blocking 6 |
| ~2:31 | "DONE will not come" stop rule fires (six approaches failed) |
| 2:36 | verifier call 1 on the blocking-6 board (sha 5acd509b...) → **FAIL** at 2:44 |
| 2:50 | hand joins (+5V, D16-1 stub) → blocking 4 (`hj/cand2`) |
| 3:02 / 3:07 / 3:14 | scoped grid-0.05/0.025 re-routes → 2 → 1 → **0** (`hj/sc4_v3`) |
| **3:25** | **first DONE**: `hj/done1` (prune + dedupe), 174 vias |
| 3:37 | opt round 1: GND via thinning → 168 |
| 3:41 | opt round 2: scoped +3.3V/+1V8 force-reroute → 167 (stop rule) |
| 3:55 | J1 finger via removed → 166, **final board frozen** |
| ~4:00 | verifier call 2 → **PASS** at ~4:08 |
| ~4:09 | ledger closed (`--final --stop-condition 1`), film, report |

## 5. Where the time went

measure.py on this session's transcript (`grade/measure.json`), at about 4h10m of wall:
- **1h00m** waiting on background jobs (seeds, rotation ranking, routes, the loop, the verifier);
- **2h38m** in other tool calls. That includes foreground seeds, routes and scoring, and my foreground sleep-polls while background jobs ran, so most of it is also waiting on the router;
- **32 min** of model time.

That is 222 tool calls, 1 subagent (the verifier, 2 calls), 17 ledger records and 0 forbidden uses. Wall time is dominated by route.py: about 7-8 min per full-board pass, and 3-6 min per scoped grid-0.05 step.

## 6. What worked and what didn't (measured)

**Worked:**
- **U1 rotation by rank_rotations:** 270 beat the pile's 0 on two seeds (probe failures 8 vs 24 on seed 0, 5 vs 8 on seed 1; crossings 117/110 vs 159-272).
- **`--decap-claim-after-ics` + `--repair --repair-decaps`:** 16 caps claimed late; seeds 4 and 5 reached 0 floorplan errors after repair (the grade errors were 19 without the flag and 8 with it on seed 0, before repair).
- **Routing at 0.1/0.1, via 0.3/0.15, `--ordering inside_out`:** blocking 11 → 6 against the default mps ordering (`original` gave the identical board).
- **Scoped route.py on the named nets plus GND at a finer grid (0.05, then 0.025), no rip flag:** 4 → 2 → 1 → 0. The same scope at grid 0.1 with `--rip-existing-nets` was reverted every time.
- **Hand joins staged with check_join:** the +5V 15 µm pad gap and a 0.67 mm D16-1 last leg, both CLEAN.
- **GND via thinning against KiCad's refill:** -6 vias, plus the finger via -1.

**Didn't work:**
- authored floors (28);
- `--layer-costs 1 1` (15);
- `--max-ripup 6` (13-18);
- via cost 40 (9);
- full-board grid 0.05 (8);
- backward direction (17);
- seeds 8-11 (12-34);
- route_diff first (10-20; matches open #677);
- non-GND first (33/40);
- place_route_loop (no improvement in 4 rounds);
- force-rerouting all signal nets at via cost 150/300 (reverted);
- /LC /D- /U7D- at via cost 150 (179 vias, worse).

**Intent:**
- I graded everything against the given `intent.json` (unchanged, sha re-checked).
- For seeding I wrote `intent_rot.json`: the given intent plus the one `rotation:U1 = 270` block rank_rotations writes. The seed holds a ranked angle only when the intent declares it.
- The given intent already carried the decap rule armed from the source, so I did not run `--decaps-from`.

## 7. Tool gaps

Full detail, with repro commands and issue searches, is in `TOOL_GAPS.md`: 14 entries, ranked. The top three:
1. route.py and the copper grader count two same-net pads **15 µm apart** as joined, while KiCad does not. +5V shipped broken while route.py's JSON called it routed. Fixed by hand.
2. The **improvement gate decides by net count**: it reverted a GND finalize that board_score measures as 33 → 9 unrouted + broken (63 → 33 disconnected pads), because 4 nets were lost and 3 gained.
3. route.py ships a **dead branch ending in a dangling via** plus exact-duplicate GND segments (open #162), so `check_complete` reports "weird_copper: not clean" on a connected, DRC-clean board. No standalone pruner exists; I wrote helpers.

Others:
- the reverted run's `--json-out` describes the rejected attempt;
- compare_seeds probes nothing on a decap-armed pile;
- there is no remover for redundant plane vias (one sat inside a USB finger, open #1116);
- the locked-net override hint is wrong;
- place_route_loop needs a hand-written accept scorer;
- no tool reports where an edge-mount body goes;
- `--repair` exits 4 on a clean grade;
- measure.py misses a teammate's transcript;
- the parser silently drops a segment with `(locked yes)` before `(width)`;
- every ledger film is titled `_film`.

Helpers written (each is a TOOL_GAPS entry), all in `helpers/`: `body_overlap.py`, `accept_blocking.py`, `dedupe_stacked.py`, `prune_dead_branch.py`, `thin_plane_vias.py`.

## 8. Verifier verdicts (one verifier, 2 of 3 calls)

- **Call 1 (blocking-6 board, sha 5acd509b...): FAIL.** It named /U4D+ (U1.12), /U4D- (U1.11), Net-(D16-1) (D16.RK, R8.1), /LED3 (U1.5) and +5V (C24.1 / C34.1, KiCad refill). DRC PASS; mechanical 9/9. It observed copper on the J1 tongue. Files: `verdict_1.txt`, `verdict_1_{connectivity,drc,spec}.txt`.
- **Call 2 (final board, sha 4d6fc838...): PASS.** connectivity, DRC and spec all PASS:
  - blocking 0, check_complete DONE, all connected, DRC 0, check_weird clean;
  - buildable, floorplan 0 errors, mechanical 9/9 exact;
  - the authored floors were reported (UNSOUND, not gating);
  - the J1 tongue remains advisory.

  Files: `verdict_2.txt`, `verdict_2_{connectivity,drc,spec}.txt`.
- **Independent grade** (`grade/grade_output_final.txt`): `{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 166, "copper_mm": 829.96, "segments": 830, "check_complete": "DONE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`

## Deliverables

- `final.kicad_pcb`, `final.kicad_pro`, `FINAL.sha256`, `DONE`
- `ledger.jsonl` (closed `--final --stop-condition 1`)
- `09_StickHub_film.mp4` (3D board box, 306 frames; title reads `_film`, see TOOL_GAPS #14)
- `TOOL_GAPS.md`, `helpers/`, `repro/`
- verdicts (`verdict_1*`, `verdict_2*`), `grade/`
