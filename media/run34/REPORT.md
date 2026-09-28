# run34 — glasgow from scratch, free agent: report

## Result first

**Not DONE.** The best board routes every net but 15. Each of those 15 is one join short. I stopped under the stop rule for "DONE will not come", after the last three different approaches all failed to beat blocking 15. All 15 blockers are itemised below.

- **Board:** `wk/run34/best_q_in1.kicad_pcb` (+ `best_q_in1.kicad_pro`). It is byte-identical to `r/q_in1.kicad_pcb`.
- **sha256:** `2f2eeae7874073651d109a3e2fbf4e0cfa814f72938f4a0dcac5a0e9b4e8fd02`

| metric | value |
|---|---|
| `blocking` (board_score) | **15** |
| unrouted | 0 |
| broken | 15 |
| DRC (check_drc, `--clearance-margin 0.1`, `--baseline` unplaced) | 0 (8 same-net self-crossing warnings; 384 vias in paste, all declared filled+capped) |
| floorplan errors (official intent) | 0 |
| vias | 1370 |
| copper_mm | 8124.64 |
| segments | 8030 |
| `check_complete` (plain) | **INCOMPLETE**: blocking 15; orphan stubs on F.Cu and B.Cu (1 each); weird_copper not clean |
| `check_complete --authored-from glasgow_unplaced` | **UNSOUND**. The copper is below the authored floors: track 0.2 → 0.0762, via 0.5 → 0.25, annular ring 0.1 → 0.05, hole 0.3 → 0.15 |
| `check_assembly` | buildable (blocking 0; 2 advisory J5↔REF** courtyard contacts of 1.0 mm² each) |
| mechanical facts | MK1-4 are exactly 4.00 mm from each corner. J1 is on the west edge, J2/J5 north, J3/J4 south (checked by the verifier) |

Against the control, run 32 (full loop, ~32 h, graded by the same `grade.py` recipe), this board has fewer blocking items (15 vs 35), fewer broken nets (15 vs 19), less DRC (0 vs 4) and less copper (8125 vs 9175 mm), with more vias (1370 vs 1271).

**The 15 open nets.** Each has 2 islands and needs 1 join. They fall in two clusters:
- **U30 balls:** /CLKREF (99.20,101.00), /D7 (100.80,100.20), /FLAGB (99.20,100.20), /OE (97.60,101.00), /FPGA_DONE (101.60,100.20).
- **Bank-B resistor networks just south of U30:** /IO_Banks/QB0 RN1 (98.76,104.80), /IO_Banks/QB1 RN1 (98.76,105.40), /IO_Banks/QB3 RN1 (98.76,106.51), /IO_Banks/IO_Buffer_B/P4 RN6 (96.72,104.83), /IO_Banks/IO_Buffer_B/Z3 RN5 (96.02,107.04), /IO_Banks/IO_Buffer_B/Z5 RN4 (107.81,98.42), /IO_Banks/IO_Buffer_B/Y0 RN3 (112.78,95.10).
- **Others:** Net-(U30A-IOT_172) R43 (84.91,97.62), /IO_Banks/DB5 U28 (87.08,106.14), /IO_Banks/Z12_P J5 (66.47,83.62).

The router's own view of them: on every scoped re-route of these nets, the improvement gate reported `gained: []`. At every setting I tried, the router found no path for them without losing other nets.

## Timeline (wall clock from the first command, 15:39)

| t | event |
|---|---|
| 0:00 | start |
| 0:12 | fixed parts hand-placed and locked (MK1-4, J1-J5, SW1, fiducials, U30, U1). Three `place_seed` runs finished |
| **0:12** | **first legal placement** (seed 2: overlap 0, pad conflicts 0, but 38 decap floorplan errors) |
| 0:53 | kept placement `dc0b`: floorplan 43 → 0, buildable |
| **1:52** | **first routed board** (`b_plain`: all nets attempted, blocking 59). No board was ever fully routed |
| 3:29 | blocking 33 (fine features) |
| 5:32 | blocking 17 (`m3`, DRC-clean targeted line) |
| **6:45** | **final board** (`q_in1`: GND plane priced 4.0, blocking 15) |
| 7:06-7:09 | verifier call 1 → FAIL (only the 15 broken nets; everything else passed) |
| 7:51 | stopped (stop rule: three consecutive approaches failed to lower blocking) |
| first DONE | never |

The verifier was called once. The board did not change after that call, so a second call would have measured the same board.

## Where the time went

- **Waiting on long jobs: roughly 6 of the 7.9 hours.**
  - A full `route.py` pass on this board takes 45-100 min, most of it in post-route cleanup and plane finalize.
  - A scoped re-route of the open nets takes 7-20 min.
  - `place_seed` takes about 5 min, not the 15 the prompt warned of. Three seeds ran in parallel.
  - `decap_seat.py` takes 3-7 min per seed.
- **Working: roughly 1.9 h.** That covered placement decisions, writing and debugging `decap_seat.py`, reading renders and logs, and choosing the next arm.
- Up to five routing arms ran in parallel on the 8 cores. Every background job was watched by a monitor or an `until` loop. `e_grid` (grid 0.05) was killed after 2 h 40 min.

## What worked, what didn't, and why

**Placement**

| lever | measured | kept? |
|---|---|---|
| Hand-place the mechanical and spec parts with `place_pose`, then lock them | 18 parts placed and locked. MK1-4 hit 4.00 mm exactly | yes |
| `place_seed --intent --force`, seeds 0/1/2 | all 264 seated, overlap 0. Floorplan errors 43/48/38, all decap-distance | yes |
| North edge: J2 at the edge, J5 set back behind MK1's courtyard | J2 (34 mm) + J5 (29 mm) need 63 mm, but only 61.8 mm lie between the MK courtyards. With `overlap_area` 0 they cannot both sit on the edge. J5 is vertical, so the seat rule does not apply to it: it only needs to be nearest the north edge, and it is | yes |
| `place_seed --repair` on decap errors | moved 1 part; errors unchanged | no |
| `place_seed --reseat ... --evict-depth 2` | refused: "nothing improved". Its gate's intent term read 0 while the grader reported 4 decap errors | no |
| **`decap_seat.py` (mine)**: seat caps next to uncovered supply pins using the grader's own predicates, applied through one `place_pose` call | seed 0: 43 → 2. Seed 2: 38 → 4 | yes |
| Hand fixes on seed 0 (`C92` re-seat, `U15` rotated 180°) | 2 → 0 | yes |
| Re-seed with a 2 mm F-side keep-out ring around U30 (seeding-only intent) | seed 3 → 1 decap error with no legal fix within 9 mm. After fanout: 8 DRC + 3 decap | no (rejected) |

**Routing** (pour GND/In1 + +3V3/In2 → `bga_fanout` U30 → `place_fanout_clearance` → decap re-seat → `route.py`)

| lever | blocking | notes |
|---|---|---|
| base: 0.1 track / 0.1 clearance, via 0.3/0.15, In1 6.0 / In2 2.5 | 59 | first routed board |
| + the skill's tuned global-plan env | 44 | |
| guided iteration (Step 2d), plain and tuned | 59 / 44 | the improvement gate reverted both |
| **fine features** (0.0762 / 0.0889, via 0.25/0.15) + In2 1.5 + tuned env | **33** | but 15 via hole-to-hole DRC |
| `repair_planes --rip-blocker-nets` | 40 | shipped 3 ripped nets open (rejected) |
| **scoped re-route of only the open nets** (tuned env) | 33 → 29 → 27 → 26 | DRC stuck at 14 |
| fine features, **no** tuned env | 31, **DRC 0** | isolates the env's river/pack knobs as the source of the via DRC |
| scoped re-routes, no env | 31 → 29 → **19** → **17** | |
| round variants: `--max-ripup 12`, In2 1.0, grid 0.05, 0.0762 clearance, tuned env | 17-21 | no gain |
| force-reroute of the 51 nets around the stranded parts | reverted | lost 12 nets to gain 5 |
| **GND plane (In1) priced 4.0 instead of 6.0**, full route | **15** | DRC 0, 1370 vias: the best board |
| In1 3.0 / 2.0 | 20 / 34 | 4.0 is the optimum of these three |
| scoped rounds on the 4.0 board (4 variants) | 15 | no gain: stop |

Why:
- The two real wins were the finer features and the cheaper GND-plane price. Both open more usable lanes around the 0.8 mm BGA, where the busiest face is 72 % covered.
- Everything left is in one hot spot, U30 and the bank-B RN arrays south of it. The router cannot find lanes there without losing others. My one attempt to open space by placement (the keep-out ring) left the zone too packed to satisfy the decap rules.

## Tool gaps I hit

**Written by me** (all in `wk/run34/`):
- **`decap_seat.py`** (+ `helper_one.py`, `ic_move.py`) seats decoupling caps against the intent's `decap_distance` and `decap_pin_distance`. No repo actor acts on those rules:
  - `place_seed --repair` and `--reseat` ignore them;
  - `place_fanout_clearance` breaks them. It moved C63 off U30.C10 (2.96 mm) and did not say so.
- **`via_nudge.py`** was an attempt to clear the hole-to-hole grazes. It traded 14 hole grazes for 8 via-to-track grazes, so I did not use its output.
- **`timeline.py`** reads the ledger.
- `prune_weird.py` (copied from run 33) is too slow at this scale: one `check_weird` per candidate, 319 candidates, 9,600 segments. Weird-copper cleanup therefore never ran.

**Tools that said "fine" about something that was not:**
- **`route.py` reported `failed 19` on `b_plain`, and board_score measured 57 broken nets.** The router's own tally understated the damage 3×.
- **With the tuned env (`KICAD_GLOBAL_PLAN_RIVER`/`KICAD_PACK_INLINE`), `route.py` produced 14-16 via hole-to-hole violations even with an explicit `--hole-to-hole-clearance 0.3`.** The router said nothing, and `check_drc` caught them.
- **`bga_fanout` defaulted to 0.25 clearance and 0.3 track on a 0.8 mm BGA, which gave 895 grazes.** It did print a warning line, and passing `--clearance 0.1` fixed it.
- `place_seed --reseat` said "nothing improved" (intent 0 → 0) on a board its own grade printed with 4 intent errors.
- `route_planes` relaxed the project's copper-to-hole clearance from 0.25 to 0.2. It disclosed this in its log, and the authored-from check reports the resulting floor drift.
- `place_pose` does not grade courtyards. It says so in `legal_unmeasured`, but it meant every `place_pose` result needed a separate `check_floorplan` / `check_assembly` pass.

**My own error:** an unquoted `$ARGS` globbed `--nets *` into file names (a known Git Bash trap). It cost one relaunch. `route_arm.sh` now uses `set -f`.

**Not used:** the original `kicad_files/glasgow_revC.kicad_pcb`, `_truth/` and `_control/`. The 4.0 mm MK corners came from the prompt. The J1/SW1 notches in the board's own keep-out band happened to match where I had put them.

## Verifier verdicts

1. **Call 1 (22:45, board sha `2f2eeae7…`): `VERDICT=FAIL`.** It found 15 broken nets. board_score blocking 15; check_complete INCOMPLETE; check_connected 15 issues. It confirmed:
   - DRC 0;
   - buildable;
   - no pad or graphic copper off the outline;
   - MK1-4 at 4.00 mm;
   - connector edges correct;
   - render sane.

   The authored-from check was UNSOUND, on track, via, annular ring and hole. The full text is in `verdict_1.txt`.

No further verifier calls were made. The FAIL names only the 15 nets, and I had no approach left that could fix them.

## Hand-back files

- `wk/run34/run34_film.mp4`: light, 4:3, sidebar, xray+iso, placement panels. 342 frames; spot-checked at 3 s and 56 s.
- `wk/run34/ledger.jsonl`: 23 rows, rejected tries included.
- `wk/run34/best_q_in1.kicad_pcb` + `.kicad_pro`: the shipped board.
