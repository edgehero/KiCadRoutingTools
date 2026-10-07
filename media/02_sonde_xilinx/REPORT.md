<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# fa10 board 02: sonde_xilinx, `/pcb-free-agent full`

**Result: DONE, 0 vias.** The final board is `wk/fa10/02_sonde_xilinx/final.kicad_pcb`, with `final.kicad_pro` and `final.design-brief.json` (a copy of the given brief). sha256 `6bd86fd8f999be12439998ce50f517f44a8e7f17f0fc88c60d486c639300ec57`.

## 1. Result

| DONE condition (mode `full`) | Measured on final.kicad_pcb | Source |
|---|---|---|
| board_score blocking | **0** | `board_score --intent intent.json --baseline sonde_xilinx.kicad_pcb` |
| unrouted | **0** | same |
| broken | **0** | same |
| check_complete | **DONE** | `check_complete.py --intent intent.json` |
| check_connected | ALL NETS FULLY CONNECTED | `py_router/check_connected.py` |
| KiCad oracle | 0 unconnected (18 before the fill, 0 after) | `kicad_unconnected.py`, `fill_for_delivery.py` |
| check_drc (margin 0.1, baseline = input) | no violations | `py_router/check_drc.py` |
| check_weird | nothing found | `py_router/check_weird.py` |
| check_assembly | buildable (blocking 0) | `check_assembly.py --intent` |
| check_floorplan | 0 errors in the 4 rules that ran | `check_floorplan.py --intent --allow-routed` |
| grade.py (independent) | done true, blocking 0, drc 0, vias 0, copper 713.57, segments 142 | `scripts/grade.py --mode full`, written to `grade_fa10-02-final.json` |

check_floorplan exits 4 ("not fully graded") on every board in this run, including the input, because the given intent withheld three budgets.

blocking_by: unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0. Impedance, length and net widths are **UNEXAMINED**: the board declares none of them and has only the Default net class.

| Quality | Final |
|---|---|
| vias | **0** |
| copper_mm | **713.57** |
| segments | **142** (all 0.635 mm; 99 on F.Cu, 43 on B.Cu) |

**Mechanical facts from the design brief:**
- **J1** (DB25, F side) is on the west edge at rot 270. Its pads span x 103.55–107.03, 0.25 mm inside the edge, and its shell sits 14.2 mm off the board.
- **J2** (DB9, B side) is on the east edge at rot 270. Its pads span x 179.97–183.45 and its shell sits 14.2 mm off the board (courtyard x 179.46–197.9).
- Both are centred on y 88.9, because the brief gives their position along the edge as `unknown`. Both are KiCad-locked.
- **P1**, the 1x6 header wired in parallel with J2, is locked beside J2 at (176.5, 83.36) rot 0. Its pin order matches J2's.

## 2. Stop rule that fired

**Stop condition 3, plateau after DONE:** stop when two consecutive rounds each cut vias by less than 5%.

| Round | Lever | Best result | Via cut |
|---|---|---|---|
| R1 | 10 seeds with U1 at 180°, each routed | seed 7: 3 → **1** via | 67% |
| R2 | P1 locked beside J2, 10 seeds, plus routing-cost variants | p2 seed 9 with `--layer-costs 1.0 2.0`: 1 → **0** vias, 713.57 mm | 100% |
| R3 | 6 routing variants on p2 seed 9 | 0 vias; best 713.57 mm (via cost 3000 gave an identical board) | 0% |
| R4 | seeds 10–19 on p2 | best 1 via | 0% |

No blocker remains.

## 3. Floors

- **Nothing was routed below the authored floors.**
  - The final route reports 0 narrowed features and 0 fab-tier escalations, so route.py printed no `Design rules [...]` line.
  - The net class is unchanged: clearance 0.254, track 0.635, via 1.651/0.635.
- **route.py tightened two rules in the output project:** board-edge clearance went from 0.01 to 0.2 mm, and minimum via drill went from unset to 0.635 mm.
- **`check_complete --authored-from` says INCOMPLETE**, only because it does not measure three declared floors: via diameter 0.889, annular ring 0.05 and copper-to-hole 0.0. The board has no vias, so the first two cannot be broken, and check_drc and KiCad's own DRC grade the third clean.
- **An early run with the default `--escalation fab` went below the floors.** It used a 0.25 mm via, a 0.4657 mm track and a 0.2223 mm clearance, and still left a net broken. That is why every later route held the authored floors.
- **The decoupling-cap rule was never armed.** The intent withheld it because no cap in the source was within 5 mm of an IC, and no placed reference of this design was available. C2–C5 are 100 pF caps on the buffer outputs; C1 is the 1 µF bulk cap. I did not write an alternative intent.

## 4. Timeline (from FIRST_CMD 03:51:06)

| Time | Elapsed | Event |
|---|---|---|
| 03:51 | 0:00 | First command |
| 03:55 | 0:04 | J1 and J2 seated and locked. J2 was at rot 90, which later proved to be reversed |
| 03:57 | 0:06 | First legal placement (place_seed seed 0; needed `--force`, gap 5) |
| 04:00 | 0:09 | First routed board (blocking 1) |
| 04:07 | 0:16 | First "DONE" (26 vias), **invalid**: J2's shell lay over the board (gap 1) |
| 04:15 | 0:24 | Reversal found on the B-side render; J2 re-seated at rot 270 |
| 04:21 | 0:30 | **First valid DONE**: 3 vias, 745.5 mm (U1 turned to 180° by rank_rotations) |
| 04:31 | 0:40 | 1 via |
| 04:41 | 0:50 | **0 vias, DONE** (713.57 mm) |
| 04:55 | 1:04 | Stop rule fired; final board frozen and filled for delivery |
| 04:57 | 1:06 | Verifier call 1 |
| 05:06 | 1:15 | Verdict 1: PASS |
| 05:09 | 1:18 | Ledger closed, film made |

## 5. Where the time went

measure.py on this run's own transcript (`subagents/agent-a898b7f5f6880b797.jsonl`):

| Item | Value |
|---|---|
| Wall clock | 1:18:05 |
| Waiting on background jobs | 19.8 min |
| Foreground tool time | 36.5 min, mostly 1–1.5 min route.py runs, three at a time |
| Model time | 21.7 min |
| Tool calls | 153 |
| Agent spawns | 1 (the verifier) |
| Forbidden uses | none |

- One routing candidate takes about 1–1.5 min, of which the plane finalize's oracle steps are about 20 s.
- One place_seed takes about 6 s; each 10-seed sweep took about 10 min.
- The biggest waste was about 23 min of work built on the reversed J2 (gap 1).

## 6. What worked and what didn't

| Lever | Measurement |
|---|---|
| `--escalation off` instead of the default `fab` | Default: 1 net broken, 49 vias, a 0.25 mm via. `off` with layer costs 1/1 and via cost 150: blocking 0, 26 vias |
| Raising `--via-cost` (every part is through-hole) | 150 → 26 vias, 400 → 21, 1000 → 16 (copper rose from 1013 to 1235 mm) |
| `rank_rotations --ref U1` after the J2 fix | U1 at 180°: crossings 44 → 17 (median of 3 seeds); routed 3 vias instead of 16 |
| B.Cu layer cost 1.5–2.0 (keeps signals off the B.Cu ground pour) | On one placement: cost 1.0 gave 4 vias + 2 DRC errors, 1.5 gave 3 vias DONE. On p2 seed 9: 1.5 gave 0 vias plus an orphan stub, 2.0 gave 0 vias DONE |
| Seed sweeps judged on routed vias, not crossings | Seeds 0–9 ranged from 1 to 12 vias; crossings did not predict vias (gap 7) |
| P1 locked beside J2 with matching pin order | Best seed went from 1 via to 0; J2's four GND pads reach ground on top-layer copper instead of through tap vias |
| `rank_rotations --ref U2` | No gain (U2 stays at 0°, crossings 17 → 17) |
| Direction-preference 0, turn cost 300, B.Cu cost 2.5/3.0 | Still 0 vias, but 769–811 mm of copper, worse than 713.6 |
| `helpers/dedup_stacked.py` | Turned 4 INCOMPLETE boards into DONE (removed 42/10/10/6 duplicate GND segments); removed 0 on the final board |

**A mistake of mine:** Windows filenames ignore case, so routing variant `s0_ra` overwrote `route/s0_rA.kicad_pcb` and its score. Ledger row 3 describes the default-escalation run (49 vias), but its board and score are actually the `--escalation off` variant (42 vias, 1 broken net). Both were broken and rejected, and nothing later used them.

## 7. Tool gaps

There are 9 entries in `TOOL_GAPS.md`, each with measurements, a repro command and the issue search. Ranked by cost:
1. **Reversed J2 passed every check.** With its shell lying 14 mm over the board, place_pose, check_floorplan ("overhang 0.514mm pass"), board_context, check_assembly, board_score and check_complete all passed it. No existing issue.
2. **Silent stacked copper from route.py.** The plane finalize left 36 duplicate GND segments without mentioning them, so check_complete said INCOMPLETE. Open issue #162 covers this class.
3. **Checkers disagree on a joint.** check_complete (via check_orphan_stubs) refuses a 0.547 mm near-miss joint that check_weird, check_connected and KiCad accept. Closed issue #601 is the opposite case.
4. **Plane finalize DRC errors.** It shipped a GND joint with a 1.1 mm gap and a track inside the board-edge clearance (2 real DRC errors).
5. **place_seed refused the pile.** It called the board "already PLACED" once the connectors were seated, which is the order the skill prescribes.
6. **Dangling vias from route.py.** It left 2 dangling GND vias at J1, confirmed on its raw output before my helper ran.
7. **Seed and rotation rankers ignore vias.** compare_seeds and rank_rotations fall back to crossings when every probe routes, and crossings did not predict vias here.
8. **check_assembly mislabels clearance as off-board copper.** It reports pads 0.25 mm inside the outline as "pad copper off-board (0.004mm)"; the 0.004 mm is a clearance shortfall.
9. **measure.py can't find this run's transcript.** It found nothing by default, and the transcript it could find was the orchestrator's 2-day session, measured without warning.

## 8. Verifier

Verifier call 1, at 04:57: **VERDICT=PASS**, from `verdict_1.txt`.
- The sha matched, and still matched after all its runs.
- check_assembly: buildable; no part in a connector's mating region and no pad copper past the outline.
- check_floorplan: 0 errors.
- render_placement: nothing off the outline. Looking at the F and B images, J1 is on the west edge and J2 on the east, and no part is left in the pile.
- Mechanical facts measured from the file: J1's shell is 14.20 mm west of the outline and J2's 14.20 mm east, both pointing away from the board. Pad copper is 0.250 mm inside the edge on both.
- board_score: blocking 0, 0 vias, 713.57 mm, 142 segments.
- check_complete: DONE. With `--authored-from` it reports the same three unmeasured floors, with no via on the board.
- check_connected: all connected. check_drc: 0 violations.
- kicad-cli DRC (it ran this on its own initiative): 0 copper or unconnected problems, plus 65 cosmetic silkscreen and library items that the brief does not grade.
- Lens files: connectivity PASS, drc PASS, spec PASS. They were used to close the ledger with `--final --stop-condition 3`.
