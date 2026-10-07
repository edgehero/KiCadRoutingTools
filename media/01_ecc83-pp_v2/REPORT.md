<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT: fa10 board 01, ecc83-pp_v2 (`/pcb-free-agent full`, from the pile)

## 1. Result

| DONE condition (`full` mode) | Measured on final.kicad_pcb |
|---|---|
| board_score blocking / unrouted / broken | **0 / 0 / 0** |
| check_complete (with the spec flags below) | **DONE** |
| check_connected | all nets fully connected |
| check_drc `--baseline <input> --clearance-margin 0.1` | no violations |
| KiCad DRC with zone refill (`kicad_unconnected`) | 0 unconnected; only 15 `lib_footprint_issues` warnings from the local library setup |
| check_assembly | buildable (blocking 0) |
| check_floorplan `--intent intent.json` | 0 errors, 0 violations |
| Mounting holes | P5–P8 exactly at their mechanical.json poses, rotation 0, locked; outline unchanged |

- **blocking_by:** unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0. Impedance, length and net widths are UNEXAMINED; the board declares none of them.
- **Quality:** 0 vias, 195.6 mm copper, 39 segments (27 top, 12 bottom), every track 0.8636 mm.
- **Spec flags used for DONE:** `--min-track-width 0.8636 --min-via-diameter 1.905 --min-via-drill 0.635`. These are the board's Default netclass sizes, which are stricter than its rule floors (0.2 / 0.4 / 0.3).
- **Independent check:** `grade.py --mode full` agrees: done true, blocking 0, 0 vias, 195.6 mm, 39 segments.

## 2. Stop rule

**Condition 3:** two consecutive rounds after DONE each cut vias by less than 5%. Vias were 0 at the first DONE, so both rounds cut 0% while copper fell 218.02 → 203.68 (−6.6%) → 195.6 mm (−4.0%). `place_portfolio` was never tried.

**Remaining blockers: none.** Non-gating items:
- **check_floorplan exits 4 ("not fully graded").** The given intent leaves zone_containment, decap_distance and legality unarmed, and withholds three budgets. That is a property of `intent.json`, which I may not edit.
- **`check_complete --authored-from` reports INCOMPLETE.** It lists via floors as "not measured" on a board with no vias (TOOL_GAPS #7).
- **P5–P8 courtyards stick out 0.766 mm past the outline.** That follows from their declared corner positions; no copper is off the outline.
- **The decap rule was never armed.** The intent withholds it, and `--decaps-from` would need the reference board, which I'm not allowed to read.

## 3. Floors

- Routing ran exactly at the Default netclass: clearance 0.508, track 0.8636, via 1.905/0.635 (no via was placed).
- route.py never printed a `Design rules [...]` line: 0 escalations, nothing narrowed, in every route of the final chain.
- **Nothing went below an authored or fab floor.** The DRC writeback only tightened the project: `min_copper_edge_clearance` 0.01 → 0.2 and `min_via_drill` added at 0.635. Those are the only two differences from the input `.kicad_pro`.
- `check_complete --authored-from` lists via diameter 0.4, via annular ring 0.05 and copper-to-hole 0.0 as not measured. There are 0 vias and check_drc is clean.

## 4. Timeline (UTC)

| time | event |
|---|---|
| 19:14:09 | FIRST_CMD |
| 19:15 | P5–P8 placed and locked (`b/01_fixed`) |
| 19:16 | rank_rotations refused, "board looks placed" (gap #2); rerun with `--force` |
| 19:16:46–19:25:53 | rank_rotations on U1: the 90° arm wins with seed 1 |
| 19:25:53 | first legal placement (`b/02_rotbest`) |
| 19:27:29 | first fully routed board (`b/03_r1`): 3 vias, blocked by the narrow joint (gap #1) |
| 19:34:46 | **first DONE** (frozen as `b/04_done` at 19:35:55): 0 vias, 218.02 mm |
| 19:38:23 | round 1 best: 203.68 mm |
| 19:49:31 | round 2 best: 195.6 mm; stop rule fires |
| 19:59:36 | silkscreen labels tidied (KiCad silk violations 4 → 0) |
| 20:02:39 | final board, with the GND pour filled |
| 20:05–20:10 | verifier call 1: PASS |
| 20:11:04 | ledger closed |
| 20:13 | film written |

## 5. Where the time went

`measure.py` at about 20:13 counted 59m11s of wall clock:
- **Waiting on my own background jobs:** 7m24s.
- **Other tool time:** 36m20s (route batches, seeding runs, KiCad DRC runs, the verifier).
- **Model time:** 15m27s.

The only long job was rank_rotations at 9m07s. Diagnosing gap #1 took about 10 min, re-verifying the GND pour about 5 min, and the labels about 4 min.

## 6. What worked and what didn't

- **Locking the holes first, then seeding.** Works only with `--force`, which keeps the locked holes in place.
- **rank_rotations.** Median crossings: 90° → 7, 180° → 8, 270° → 11, 0° → 12. The 90° winner probe-routed clean with 3 vias, but the final board uses U1 at 180° because it routes with less copper.
- **route.py with default settings.** 3 vias, 212.3 mm, not DONE because of the narrow joint at P1.2.
- **Via-cost and layer-cost variants.**
  - Via cost 300 left 1 via; via cost 1000 gave 0 vias.
  - Equal layer costs alone, or a 0.05 mm grid, still gave 3 vias.
  - Equal layer costs with via cost 300 gave 0 vias and was the best recipe: less copper than via cost 1000 on 3 of the 4 round-1 placements.
- **A second route.py pass.** It adds the missing connector ("Bridged 1 soft joint") and turns INCOMPLETE into DONE.
- **Round 1 (4 placements x 2 settings).** U1 at 180°, seed 1 → 203.68 mm.
- **Round 2 (12 more seeds).**
  - C1 was left unseated in 4 of the 12 seeds.
  - Best: U1 at 180°, seed 3 → 195.6 mm, 39 segments.
  - `place_seed --reseat C1` failed on both unseated seeds (exit 4, reported honestly).
- **beautify_labels.** Needed a second, targeted run on P2 to clear the last KiCad silkscreen violation; copper was untouched.
- **fill_for_delivery.** Every grade stayed the same after filling.
- **Intents.** Everything was graded against the given `intent.json`. The placement runs also used rank_rotations' per-angle intent files, which only add U1's rotation so the seeder holds it; no rule was relaxed.
- **Film.** The progress curve rises back to "not working" at 0:25 and 0:36. Those are the two placements I kept after DONE, which stay unrouted until they are routed — real history, not a regression.

## 7. Tool gaps (detail in TOOL_GAPS.md)

1. route.py's final cleanup recreates the narrow joint at P1.2; only a second pass fixes it.
2. The seeder refuses a mostly piled board once the holes are locked.
3. rank_rotations' control baseline includes a seed with C1 still in the pile.
4. board_brief never mentions the input's GND pour.
5. beautify_labels put P2's label on C1's silkscreen circle and called it placed; it and `check_floorplan --allow-routed` also print a refusal message they don't act on.
6. board_score's `poured_nets` reads `[]` on any fully connected board, even when a pour exists.
7. `check_complete --authored-from` calls via floors "not measured" on a board with no vias.

Helpers written: `route2pass.sh`, `route_variants.sh`, `grade_variants.sh`. The issue searches found no open issue covering any of these gaps; the closest closed ones are #416, #1063, #1109 and #481.

## 8. Verifier verdicts

- **Call 1 of 3: VERDICT=PASS** (`verdict_1.txt`), with all three lens files PASS.
- **What it measured itself:**
  - sha256 match.
  - Buildable, with 0 floorplan errors and no copper off the outline.
  - Exact hole positions and an unchanged outline.
  - Blocking 0, 0 vias, 195.6 mm, 39 segments.
  - check_complete DONE, all nets connected, DRC clean.
  - KiCad's own check: 0 unconnected, and the stored GND fill is one region touching all 7 GND pads.
- No further calls were needed.
