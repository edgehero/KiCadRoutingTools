# Upgrade 3 — re-point the objective, and a second structural pattern model

Research note for run 11. Two questions, both aimed at the next run producing a
**better board**: parts that work together, zero unrouted, zero broken.

Everything below is measured on `wk/run10/smartknob/board.kicad_pcb` (the
DAMAGED input), `wk/run10/smartknob/final.kicad_pcb` (what run 10 shipped), the
33 in-repo corpus boards in `kicad_files/`, and the run-10 report's own
published aggregates. **Nothing under `wk/run10/_truth/` or any
`smartknob_base` / `kicad_stress_test` path was opened.** Where a claim depends
on the perturbed member list I derive it arithmetically from published
aggregates and say so.

---

## 0. What run 10 actually did — the finding that re-frames both questions

Run 10's placement half **moved five parts**. Measured, pad-space
(`recovery.part_displacement`), damaged → final:

| ref | pad-space move | centre move | rotation | what it is |
|---|---|---|---|---|
| **C7** | **30.021 mm** | 29.981 mm | 303.7° → 123.7° (flipped 180°) | ring decap, **undamaged** |
| J3 | 10.344 mm | 3.000 mm | 270° → 180° | 8-pad solder-pad header |
| **D7** | **7.257 mm** | 7.257 mm | unchanged | ring LED, **undamaged** |
| C20 | 1.096 mm | 0.000 mm | 180° → 270° (rotation only) | 0603 cap, **undamaged** |
| C18 | 1.000 mm | 1.000 mm | unchanged | 0805 cap, **undamaged** |

**Only ONE of the 30 damaged parts was moved at all, and the other four moves
were to parts the damage never touched.** That is derivable without opening the
record. `board_poses` admits the 101 footprints that have pads; the block is 30,
so `collateral_pad_rms` is an RMS over 71 non-members. Taking C7, D7, C18, C20
as non-members and J3 as the member:

    (30.021² + 7.257² + 1.000² + 1.096²) / 71 = 956.13 / 71 = 13.4666
    sqrt(13.4666) = 3.6698

The report's measured `collateral_pad_rms` is **3.6697**. No other partition of
those five refs reproduces it. So: J3 is the single block member the run moved
(and moving it made `perturbed_pad_rms` slightly worse, 38.6529 → 38.7068,
which is the entire −0.001393 recovery); the other four are collateral.

### And two of the four are members of an intact structure the run broke

On the DAMAGED board the LED ring is **geometrically perfect**:

    D1..D8   r = 17.343809 mm about (100.000000, 100.000000), pitch exactly 45.0000°
    C1..C8   r = 18.000308 mm about the same centre, 4-fold × 2 residues
             (33.7483° and 56.2517° mod 90°)

All eight of each were present and at seat. The prompt's premise — "D7/C7,
D8/C8 dragged away" — is **not what the damaged board says**; the damage did not
touch the ring at all. What happened is worse and more useful: run 10's own lap
3 (`place_optimize --max-displacement 30` with 105 refs locked, *freeing only C7
and D7*) **tore two members out of it** to buy legality, and the shipped board
carries the wreckage:

    final:  D radii 13.11 .. 18.25 (D7 pulled to r = 12.648)
            C radii 14.30 .. 46.40 (C7 flung to (63.000, 72.000), r = 46.400)

C7 is D7's decoupling cap. It now sits 30 mm away, in the opposite corner of an
81 mm board.

**So the run-10 board is not "slightly further from truth". It is a board whose
one perfectly-intact functional structure was disassembled by the repair, while
the actual damage went untouched.** That is the failure the next run has to stop
— and it is invisible to `recovery` (−0.0014, reads as "inert") *and* to
`board_score` (blocking fell, quality improved) *and* to `check_assembly`
(buildable). Only `collateral_pad_rms` saw it, and only as a scalar with no name
attached.

---

## Q1 — Re-point the objective and the experiment's scoring

### 1.1 What `score_board(..., routed_path=...)` reports today

`placement/recovery.py:479-492` parses the routed board, resolves the frozen net
list, and calls `connectivity_tally` (`:280-371`), which returns:

| key | meaning |
|---|---|
| `prr_denominator` | pad-pair count, **frozen from the control** |
| `rr_denominator` | routable-net count (≥2 pads), frozen |
| `pairs_connected` | pad pairs actually joined, zone/fill-aware |
| `nets_connected` / `nets_open` | nets with no break / with a break |
| `PRR_connected` | % of required pad pairs connected |
| `RR_connected` / `Open` | % of required nets whole / open |
| `PRR` / `NRR` | the same, restricted to **DRC-clean** nets |
| `drc_clean_ran`, `drc_clean_reason` | vacuity flags |

It is careful in exactly the ways this repo has learned to be: it refuses to
read `route.py`'s per-run `pad_pairs_total` (a net the router never scoped is
simply absent from it), it refuses `check_connected.run_connectivity_check`
(which skips nets with no copper — the ones that must stay in the denominator),
and the denominators are frozen once on the control (`placement/perturb.py:524-526`).

**Is it sufficient as the PRIMARY score? Yes — with two conditions.**

Computed on the run-10 boards, denominators frozen from the damaged board's
topology (57 routable nets, 238 pad pairs):

| board | pairs connected | PRR | nets whole | RR | open |
|---|---|---|---|---|---|
| damaged input (no copper) | 9 / 238 | **3.78 %** | 0 / 57 | 0.0 % | 57 |
| **run 10 final** | **182 / 238** | **76.47 %** | **28 / 57** | **49.12 %** | **29** |

That is the number the user asked for, it already exists, and it says the
opposite of the headline run 10 printed. `recovery −0.0014` called the run inert;
`PRR 3.78 → 76.47` calls it a large step toward a routable board that stopped
29 nets short.

The two conditions:

1. **`routed_path` has never once been supplied.** Grep across the whole repo:
   the only `score_board` call sites are `placement/perturb.py:556-557` and
   `tests/stress/perturb_batch.py:313,342`, and none passes `routed_path`. Every
   perturb record ever written carries
   `route: {'ran': False, 'reason': 'no routed board supplied'}`. The block is
   correct, tested (`tests/test_411_recovery.py:253-255`) and **dead**.
2. **`dirty_nets` has never been supplied either**, so `PRR`/`NRR` (the
   DRC-clean forms, which are the ones OmniRouting defines) are always `None`
   and only the `_connected` forms carry a number. A producer is one loop:
   `check_drc.py --json` writes `items[].net1` / `net2` as net **names**
   (verified in `wk/run10/smartknob/drc_final.json`), so
   `{pcb.nets[i].name: i}` maps them to ids.

### 1.2 What the reports lead with today

| script | its headline | routed outcome? |
|---|---|---|
| `tests/stress/arm_report.py:216-226` | `\| run \| recovery \| home /N \| vias \| copper mm \| buildable \|` | **none.** `vias`/`copper_mm` are `board_score.quality`, which is defined as a tiebreak *only comparable once `blocking == 0`* — so the two "routing" columns are the two that are meaningless until the thing nobody prints is zero. |
| `tests/stress/perturb_report.py:117-145` (`table`) and `:68-82` (`caption`) | `dose recov dist NC OO oob HPWL failures acc secs`; movie captions put `recovery ±0.000` first | **none.** `failures` is the quench arm's own `failures_before→after`, not a connectivity grade. |
| `tests/stress/grade_final.py:208` | `DRC=… conn=True/False (agent reported …)` | closest to right, but `fully_connected` is a **boolean** (`"ALL NETS FULLY CONNECTED" in out`) so it cannot rank two incomplete boards, and it is the stress-harness backstop, not the #411 rig. |

### 1.3 The headline the rig should print

Lexicographic, in the user's own order of caring — **routed first, legality
second, effort third, distance-to-truth demoted to a diagnostic**:

```
| run            | unrouted | broken | PRR    | RR     | drc | assembly | vias | copper mm | recovery |
|----------------|----------|--------|--------|--------|-----|----------|------|-----------|----------|
| damaged input  |       57 |      0 |  3.78% |  0.00% |   9 | NOT BUILDABLE |   0 |     0.0 | 0 (def.) |
| this run       |       13 |     37 | 76.47% | 49.12% |   0 | buildable     | 175 |  1712.4 |  -0.0014 |
| human original |        0 |      0 | 100%   | 100%   |   0 | buildable     | 174 |  2391.0 |    (n/a) |
```

Rules that make it honest:

- **Rank on `(unrouted + broken + drc, −PRR, vias, copper_mm)`.** `unrouted` and
  `broken` are already `board_score`'s own blocking terms with their work lists
  attached (`blocking_by.unrouted`, `blocking_by.broken`, and the per-net
  `broken_detail` with stranded pads and the naming of `route` vs
  `route_disconnected_planes`). PRR is the continuous channel that distinguishes
  two boards that both have blockers — a counts-only headline cannot tell "one
  net short" from "half the board".
- **Print `PRR` next to `unrouted`/`broken`, never instead of them.** They
  disagree by construction and the gap is informative: `check_connected` skips
  nets with no copper at all, `connectivity_tally` keeps them in the
  denominator. On the run-10 final that is 13 unrouted + 37 broken-separations
  vs 29 open nets of 57.
- **Recovery, `home /N`, `collateral_pad_rms` and `unit_spread_ratio` move to a
  DIAGNOSTIC block below the table**, under a heading that says what they are
  for: *not* the score, but the answer to "did the run move the parts it was
  asked to move". `collateral_pad_rms` in particular should be printed **with
  the names and distances of the parts it counted** — on run 10 it was the only
  instrument that saw the ring being torn apart, and it reported it as the
  single number `3.6697` with nothing attached. `arm_report.py:196-201` already
  prints a loud warning above 0.5 mm; it should name the refs.
- **`ungraded` stays loud.** Nothing here changes run 10's correct refusal to
  read `floorplan / impedance / length / net_widths` as passes.

### 1.4 What the human original's row becomes

**A benchmark to approach, never a pose to match.** Its `recovery` and `home`
cells are struck out entirely (they are `1.0` and `N/N` by definition and carry
zero information). What it contributes is the **cost floor at blocking 0**:
measured on the run-10 subject, **174 vias, 2391.0 mm copper, 834 segments**.

Read it as: *a human solved this board's connectivity for 174 vias and 2391 mm.*
Run 10 spent 175 vias and 1712 mm and got 76 % of the pad pairs — i.e. it was
already spending a human's via budget for three quarters of a board, which is a
finding about the router's economy that the recovery-led table could not
express. Two guards on that reading:

- The comparison is only legitimate **once both rows are at blocking 0**;
  `board_score`'s own doctrine ("`quality` is compared only once `blocking == 0`")
  applies to the table too. Below that, print the quality columns greyed or
  parenthesised.
- `arm_report.py:152-157` already calls `compare_to_original.original_degeneracy`
  and prints "the human reference is degenerate" when it has no copper (7 of 75
  wave references had none). Keep that; a degenerate reference contributes a
  placement row only.

### 1.5 Minimal changes, file by file

1. **`placement/recovery.py`** — no signature change needed. Add one helper
   beside `connectivity_tally`:
   `dirty_net_ids(pcb, drc_json_path) -> List[int]`, mapping `items[].net1/net2`
   names through `pcb.nets`. ~15 lines. This is what turns `PRR`/`NRR` from
   `None` into numbers.
2. **`tests/stress/arm_report.py`** — the load-bearing change, and it is small.
   The module **already imports `board_score`** for `quality()` (`:59-66`). Add a
   sibling `blocking(board)` that runs `board_score.py --json` and returns
   `blocking_by`, and a `route(board, record)` that calls
   `R.score_board(board, record, routed_path=board, dirty_nets=…)` — the result
   board *is* the routed board, so `routed_path` is just `a.result`. Then swap
   the header at `:216-218` for the one in §1.3 and move the recovery lines from
   the table into the diagnostic block at `:227-234`. Nothing else in the file
   moves; truth still opens at exactly one point (`:159`).
3. **`tests/stress/perturb_report.py`** — add `unrouted`, `broken`, `PRR` columns
   to `table()` (`:117-145`) and put `PRR` first in `caption()` (`:74-82`) so the
   movie frames narrate routability instead of distance. Its rows come from the
   scoreboard, so this needs `perturb_batch.py:313` to pass
   `routed_path=b, dirty_nets=…` — a two-argument change — and the arm boards to
   be routed, which the `loop@*` arms already are.
4. **`tests/stress/grade_final.py`** — replace the boolean `fully_connected`
   (`:189-194`) with the parsed counts it already has in front of it
   (`check_connected` prints them) plus `PRR` from `connectivity_tally`, so two
   incomplete boards are comparable. Keep `misgrade`.
5. **`placement/perturb.py:556-557`** — nothing required (the control and emit
   boards are unrouted by construction, and the `route: ran False` there is
   honest). Do **not** "fix" it by routing them.

Total: one new helper, one changed table header, two call sites gaining a kwarg.

### 1.6 Can a HIGH recovery ever be actively BAD for routability?

**No — and I am not going to invent a case.** The corpus has no bad seeds: every
control is a placement a human iterated until it routed and shipped
(`placement/recovery.py:1-8`). Restoring a part to its control pose therefore
moves it toward a configuration that is *known* to route. There is no measured
example, and no mechanism I can construct, where arriving at the true pose costs
routability.

What is true, and is a different statement, is that **the recovery SCALAR can
rise while the board gets worse**, in three ways the rig already instruments and
one it does not:

- **Block tear.** `recovery` is a mean over the block; dragging half a block home
  while the other half stays put lowers the mean and shreds the unit.
  `unit_spread_ratio` exists for exactly this (`recovery.py:203-225`) and is
  already reported — but its sensitivity is conditional on the unit being
  compact, which is why `unit_gyration_orig_mm` must be printed beside it.
- **Collateral.** Recovery is computed only over members, so a run can improve it
  while wrecking the other 71 parts. That is precisely run 10 inverted:
  recovery ≈ 0, collateral 0 → 3.67, and the damage was to an intact ring.
- **Rotation.** `part_displacement` matches pads by index, so a 180° flip of a
  symmetric passive reads `2 × pad_offset` rather than 0. Correct — but it means
  a run can *lower* pad RMS while leaving a part electrically reversed. C7's
  final pose is flipped 180° *and* 30 mm out.
- **Not instrumented at all: structure.** Nothing measures "was this part on a
  regular pattern, and is it still". That is Q2.

So the recommendation is not "recovery is wrong", it is: **recovery is a
diagnostic about the perturbed set only, and it must never again be the row a
human reads first.**

---

## Q2 — A second structural pattern model for `place_reconstruct`

### 2.1 What exists today (surveyed across the whole repo)

- `placement/reconstruct.py::fit_corner_insets` (`:365`) is the **only**
  part-level geometric pattern model: corner + mid-edge inset seats for zero-net
  drilled holes, grouped on the rounded `(inset_x, inset_y)` pair.
- `rigid_vectors` (`:483`) and `conflict_offset_vectors` (`:1010`) are
  **translation-only** and, in `rigid_vectors`' case, **pattern-gated** — no
  pattern, no vectors.
- `airwire_cluster_vectors` (`:1087`) is REFUTED and unwired.
- **Nothing in the repo fits a circle, an arc, an angular pitch, a regular line
  of parts, a grid of parts, or a rotation.** No `atan2` is ever taken on a part
  position. `bga_fanout/grid.py` and `escape.pad_pitch` do lattice/pitch
  detection over **pads inside one footprint**, never over parts.
  `reseat.slot_pool` (`:149`) emits concentric rings but never measures one.
- The closest existing thing to a "family" is `quench.QuenchState._build_peers`
  (`:621`): same `footprint_name` within a span, consumed only by
  `_align_pair_penalty` (`:664`), a soft **axis-aligned** row attractor. It
  cannot see a ring, and it does not detect — it pulls.
- `placement/groups.py::derive_groups` groups on KiCad groups, sheet path, net
  prefix (with a 20 mm scatter radius) and decap tethers. Never on footprint
  name, value, reference prefix, or arrangement.
- `part_class.classify_part` is footprint-name-first; reference prefix is a
  deliberately weak tiebreak ("prefix evidence alone never makes a receptacle").

### 2.2 The proposal — a family ORBIT fitter

Not "circle OR line OR grid" as three detectors, but one model that subsumes the
ring case and the regular-line case as the two things a 2-D placement actually
repeats: **the orbit of a small seed set under an m-fold rotation**.

`fit_family_orbits(state, tiers) -> Dict[ref, List[(x, y)]]`, the **same
propose-only contract as `fit_corner_insets`**, feeding the same three consumers
(`build_candidates`' `proposals`, `rigid_vectors`, and — see §2.4 — the gate).

    family      parts sharing footprint_name (see §2.5 for why not value/prefix)
    centre      RANSAC over circumcentres of member triples, deduped at 0.01 mm
    radius      consensus radius, tolerance 0.20 mm
    orbit       for m in 3..24: reduce each inlier's angle mod 360/m, cluster the
                residues at 0.75°; slots = |residues| x m
    pick        the m with the FEWEST FREE SLOTS (ties -> larger m)
    propose     the free slots, to the family members that are not inliers

Five guards, each of which was added because the un-guarded form fired on a
healthy board (measurements in §2.3):

| guard | value | what it kills |
|---|---|---|
| scale | `r <= 0.75 × board diagonal`, centre inside the bbox | near-collinear families fitted with a 2588 mm or 7545 mm circle whose slots are metres off-board |
| curvature | `m >= 3` | a 2-fold "orbit" is a point reflection and has no curvature at all |
| over-determination | every residue class occupied ≥ 3 times | a residue seen once is a fitted free parameter, not evidence |
| occupancy | `inliers >= 0.60 × slots` | 5 parts spread over a 21-slot orbit is a coincidence |
| pigeonhole | offer only when `stragglers <= free slots` | `fit_corner_insets`' own "recognise generously, offer conservatively" |

On the smartknob board this model recovers, exactly, without being told:

    sk6812:SK6812-SIDE-A    m = 8 × 1 residue, r = 17.3438, c = (100.000, 100.000)
    C_0603_1608Metric       m = 4 × 2 residues, r = 18.0003, same centre
    MountingHole_M1.6       m = 3 × 1 residue,  r = 10.2509, same centre  (H1,H2,H3)
    MountingHole_2.2mm_M2   m = 4 × 1 residue,  r = 29.8000, same centre  (H4..H7)

Note the last two. **The mounting holes on this board are a rotational pattern,
not a corner-inset pattern**, and that has a direct bearing on run 10's own T1
fix — see §2.6.

### 2.3 The no-op guarantee — does it inherit `fit_corner_insets`', or is it the refuted shape?

This is the load-bearing question and it deserves the direct answer:
**structurally it inherits the guarantee; empirically the naive form does not,
and I measured that before proposing anything.**

The structural argument is the same one `airwire_cluster_vectors`' docstring
(`reconstruct.py:1116-1120`) gives for why the two shipped sources are safe: *"a
hole-pattern fit needs a hole pattern; conflict offsets need conflicts. Both are
silent on a healthy board by construction rather than by threshold."* An orbit
fit needs **a free slot in a nearly-complete orbit**. A healthy board's ring is
full: 8 slots, 8 members, zero proposals, by construction — not by tuning.
Connectivity has no such property because *a long airwire is ordinary layout*;
a **gap in an otherwise complete rotational orbit is not ordinary layout.**

But "structurally sound" is exactly what was claimed for the airwire source too,
so I ran the same experiment that refuted it — the 33 in-repo corpus boards,
plus the run-10 damaged input and the run-10 final:

| configuration | healthy corpus boards firing |
|---|---|
| naive orbit fit (no guards) | **6 of 33** — glasgow_revC, rp2350, sonde_u ×3, ulx3s |
| + scale + curvature + over-determination | 1 of 33 (orangecrab: 5 parts over a 21-slot orbit) |
| **+ occupancy ≥ 0.60** | **0 of 33** |
| the same, with `MIN_INLIERS` lowered 5 → 4 → 3 | **0 of 33** |

**The naive form fires on 6 of 33 — the identical rate the refuted airwire
source scored, and for a related reason** (a near-collinear family of resistors
fits an enormous circle just as a long airwire fits a damage vector). Had it
gone in un-guarded it would have been the second refutation in this family. The
four failures are all one class — degenerate curvature — and two cheap physical
guards (the circle must be on the board; a residue seen once is not evidence)
remove them completely.

**Recommendation: propose it, with the guards, and pin the sweep in a test.** The
right home is a `tests/test_orbit_fit_noop.py` in the shape of
`tests/test_run8_airwire_refuted.py`: assert **0 of 33** healthy boards fire, and
pin the un-guarded 6-of-33 number in the docstring so a future relaxation of a
guard is visible as a regression rather than rediscovered.

### 2.4 How it would be refereed — and the measured hazard

`fit` proposes; the assign-stage gate decides. Three things about that:

**(a) The proposals reach the ILP unchanged.** `build_candidates` (`:1166`) takes
`proposals` and marks them `pattern`; `_solve_ilp` gives each pattern slot
`−PATTERN_BONUS_MM` and adds a **slot-exclusion row** so two parts cannot claim
the same seat (`:1329-1336`). `rigid_vectors` then over-determines a translation
from ≥2 agreeing offsets exactly as it does for holes. Nothing new is needed on
the consumer side.

**(b) The measured hazard is real and this proposal walks straight into it.** In
run 10 `assign` *did* try H2's move and the gate reverted it, because
`oob 940.914 → 942.414` (worse) outranks `overlap 100.265 → 92.015` (better) —
`GATE_TERMS` puts `oob` at index 3 and `overlap` at index 6
(`reconstruct.py:159-160`). Any orbit proposal that moves a part *toward* the
board edge or centre in a way that perturbs `pad_oob_amount` by a fraction of a
millimetre will be reverted the same way, however exact the geometric evidence.
Two mitigations, in order of preference:

  - **Do not touch the gate order.** It is measured, and run 7 already showed
    what happens when `oob` can be gamed. Instead give the orbit slot the same
    treatment `edge_bands` gets: a part whose proposed seat is a *fitted orbit
    seat* is charged `oob` **relative to its own seat** rather than absolutely —
    `pad_oob_amount(state, edge_bands)` already implements exactly that
    allowance mechanism (`:75-111`) and needs only the seat refs added to
    `edge_bands`. This is the smallest change that lets a correct homecoming
    through a term it legitimately worsens by design.
  - Add the ref to `evidenced` so `prune_assignment` (`:638`) does not revert it
    on an EQUAL tuple. An orbit seat corroborated by 6 members is precisely the
    "real evidence" that set exists for.

**(c) The higher-value use is as a GATE TERM, not as a proposal source.** Run 10
did not fail to *restore* the ring — the ring was intact. It **broke** the ring.
So the intervention with the largest measured payoff is:

    pattern_breaks = the number of parts that were AT SEAT on a family orbit
                     fitted at stage ENTRY and are not at seat now

placed in `measure()` **above `hpwl` and `overlap`, below `oob`** — the same
position, and for the same reason, as the run-8 `locked_contacts` term: a fitted
seat is a decision the board already made, and no wirelength gain may buy it.
Its no-op property is identical to `locked_contacts`': a board with no fitted
orbit has the term pinned at 0 forever, and a board whose orbits stay intact
scores 0 forever. Verified on the corpus by the same sweep — 0 of 33 boards have
a fitted orbit with a free slot, so the term is 0 on all of them.

**And the cheapest lever of all is a lock.** The parts run 10 destroyed were free
to move because `lock_advisor` rated them `MEDIUM` and the run's `--lock` list
took only `HIGH` (see `wk/run10/smartknob/locks.txt` and `q1.txt`: the lock list
was `C1 C2 C3 C4 C5 C6 J1 J2 TP9 H1..H9` — C7, C8 and every one of D1..D8 were
`MEDIUM` and left free). The advisor protected six of the eight ring caps **by
accident**, on an edge-proximity rule ("courtyard leaves the board outline by
0.07 mm" — the inner keep-out ring), and had no idea a ring existed.
**`lock_advisor` should promote "at seat on a fitted family orbit with ≥3
corroborating members" to a HIGH finding with that as its stated reason.** That
single change would have made lap 3 impossible.

### 2.5 The opportunity on the run-10 board, quantified honestly

**On the damaged input, a circle fitter would have proposed positions for ZERO
parts.** Both rings were complete (8/8 and 8/8 seats occupied), the M1.6 hole
orbit was complete (3/3) and the M2 hole orbit was complete (4/4). Free slots:
none. Proposals: none. That is the no-op guarantee working correctly, and it is
also the honest answer to "quantify the opportunity": as a *recovery* rung on
this board, the value is **nil**.

**On the board run 10 SHIPPED it proposes two, both exact:**

    sk6812:SK6812-SIDE-A   7 inliers, 1 free slot -> D7 -> (95.0620, 83.3740)
    C_0603_1608Metric      7 inliers, 1 free slot -> C7 -> (90.0000, 85.0330)

Both are the parts' damaged-board (= undamaged) poses to the last digit.

**Do 6 survivors over-determine a circle? Comprehensively.** The model has four
continuous parameters (cx, cy, r, θ₀) plus a discrete m; six members give twelve
observations. Measured, by deleting members and re-fitting from survivors alone:

| survivors | fit | predicted seats vs. the true poses |
|---|---|---|
| D1–D6 (6) | c = (100.000000, 100.000001), r = 17.343809, m = 8 | D7 and D8 seats, **error 0.00 µm** |
| D1–D5 (5) | same centre/radius, m = 8 | D6, D7, D8 seats, **error 0.00 µm** |
| D1–D4 (4) | no fit (below `MIN_INLIERS`) | — |
| C1–C6 (6) | c = (100.000000, 100.000000), r = 18.000308, m = 4 × 2 | C7 and C8 seats, **error 0.00 µm** |
| C1–C5 (5) | no fit (a residue class drops below 3) | — |

So six survivors are not merely sufficient, they are sufficient with three
orders of magnitude of margin, and the guards fail *closed* at four.

**One honest limitation, measured.** The C ring's family key is
`Capacitor_SMD:C_0603_1608Metric`, which on this board has **22 members** — the
8 ring caps plus 14 ordinary 0603s. The fit finds the ring correctly and names
the free slot correctly, but the **pigeonhole rule then refuses to offer it**
(15 stragglers, 1 free slot). Three ways out, ranked:

1. **Prefer the gate term (§2.4c) over the proposal.** It does not care how many
   stragglers there are — it only asks whether a part that *was* at seat still
   is. On the C ring that is unambiguous, and it is the use with the payoff.
2. Scope the family by `(footprint_name, sheet)` using `groups._sheet_of`. On
   this board the sheet path is empty for every part (the corpus normalisation
   strips it), so it changes nothing here — but on a board that keeps its
   hierarchy it splits the ring caps from the rest for free.
3. **Do NOT try to pick the claimant by net.** I checked: C1..C8 share only
   `+5V` and `GND` with their LEDs, so net adjacency does not distinguish C7
   from the other 14 caps, and the nearest-slot tiebreak
   (`DIST_TIEBREAK_PER_MM`) would pick C28 at 15.7 mm over C7 at 30 mm — the
   wrong cap onto the ring. A claimant rule that can seat the wrong part is
   worse than no proposal.

### 2.6 A false positive the run-10 T1 fix introduced, which this model refutes

Run 10's `classify` fix took `zero_net` from 0 to 7 and made `fit_corner_insets`
propose `H2 → [(94.8722, 91.1237), (94.8722, 108.8787)]`. The report treats that
as the fix working. **It is very likely a false positive.** Measured on the
damaged board:

    H1  r = 10.250853 mm, θ =  59.999997°
    H2  r = 10.250854 mm, θ = 180.000000°
    H3  r = 10.250854 mm, θ = -60.000000°   about (100, 100)

H1, H2, H3 are an exact 3-fold orbit — radii agreeing to **0.8 nanometres** and
angles to 3 × 10⁻⁶ degrees. H2 is at seat. The corner-inset model, which has no
hypothesis for a rotational pattern, reads H2's *nearest-corner* insets, finds
they match nothing, calls it displaced, and offers it H1/H3's mirror at
x = 94.8722 — a **5.2 mm move of a mounting hole that is already home**. Only the
`oob` revert described in §2.4b prevented it from shipping.

The orbit fitter recognises that family (`m = 3 × 1, r = 10.2509`, complete, zero
free slots) and would supply the `at_seat` fact that refutes the corner model's
claim — the same "recognise generously" asymmetry `fit_corner_insets` already
uses internally to stop offering a hole the seat it is standing on
(`reconstruct.py:437-450`), just extended to a second pattern vocabulary.

**Recommendation:** run the orbit fit *before* the corner fit and let a part that
is at seat on any fitted pattern be removed from the other model's candidate
list. That direction only ever removes candidates, which is the safe one.

### 2.7 What this would NOT have fixed

Stated plainly so nobody expects it to carry run 11:

- **R7–R12** — six 0603s at exactly 1.5 mm pitch on y = 100.400, all six
  15–20 mm off the board's east edge. A perfect regular line, and **unfittable**:
  every member is displaced, so there are no survivors to anchor the line. A
  pattern fitter with no survivors proposes nothing, and that is correct
  behaviour, not a gap to patch. These need the large-displacement repair that
  run 10's T5 says no tool has.
- **U4, U5, U8, TP4, TP5** — singletons with no family, 7–32 mm off-board. Same
  answer.
- So the 11 off-board parts and the 13 unrouted nets that follow from them are
  **untouched by this proposal**. Its value on run 11 is (a) stopping the repair
  from breaking intact structure, and (b) making that breakage visible if it
  happens anyway.

---

## Recommended order of work for run 11

1. **`arm_report.py` headline swap** (§1.5 item 2) — half a day, no new
   measurement, and it is the change that stops the rig from reporting failure
   about a board that got better.
2. **`lock_advisor` promotes orbit-seated parts to HIGH** (§2.4) — the single
   change that would have prevented run 10's actual damage.
3. **`fit_family_orbits` + the 0-of-33 no-op test** (§2.2, §2.3).
4. **`pattern_breaks` gate term in `measure()`** (§2.4c), above `hpwl`.
5. **`dirty_nets` producer** so `PRR`/`NRR` stop being `None` (§1.1).
6. Only then the orbit proposals into `build_candidates`, with the `edge_bands`
   allowance for the `oob` hazard (§2.4b).
