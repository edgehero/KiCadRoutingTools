# UPGRADE 1 — lift-and-re-seat a subset (`place_seed --reseat`)

Target of the upgrade: **zero unrouted and zero broken nets**, by getting every
pad onto the board. Not by restoring original poses.

Everything below was **re-derived by running the tools**, on
`wk/run10/smartknob/board.kicad_pcb` (107 parts, 90 nets, 0 segments, 0 vias,
clearance floor 0.2 from the board's own `Default` netclass). The report's
numbers were not trusted; where they differ from mine the difference is
explained.

---

## 0. HEADLINE — the diagnosis in the brief is right about the symptom and
## wrong about the cause, and the corrected cause is much cheaper to fix

The brief says the three repair tools all "search outward from the part's
CURRENT pose", and that `place_seed --repair`'s census is "CONFLICT PAIRS
ONLY … printed `oob_pad_count: 23` and attempted none of them."

The first half is true. The second half is not the reason the 11 parts were
skipped, and the real reason is a one-line exemption plus an intent bug:

1. `repair_placement` **does** carry an off-board census
   (`placement/seeder.py:944-962`). It charges any part whose pad extent
   leaves the outline at zero margin.
2. That census opens with `if ref in edge_refs: continue`
   (`placement/seeder.py:951-952`), where `edge_refs` is every ref the intent
   declares an edge connector (`placement/seeder.py:838`).
3. `check_floorplan --emit-intent`, run on the **damaged** board, declared
   **every one of the 11 off-board parts an edge connector, with an overhang
   band equal to its damage displacement.** From `wk/run10/smartknob/fp.json`:

   ```
   R7  east  max 34.792      R10 east  max 57.292      U4  north max 103.762
   R8  east  max 42.292      R11 east  max 64.792      U5  east  max  31.182
   R9  east  max 49.792      R12 east  max 72.292      U8  north max 157.612
                                                       TP4 north max 160.062
                                                       TP5 north max 160.062
   ```

   The emission site is `placement/floorplan.py:1311` and `:1318`,
   `'max': round(amt + 0.5, 3)` — the observed overhang plus half a
   millimetre, **with no cap**. The code four lines above it
   (`placement/floorplan.py:1279-1288`) already knows this failure mode and
   refuses it *for mounting holes only*: *"never bless a mounting hole's
   overhang — an observation entry here records damage as an allowance."*
   It is the same bug for every other part class.

So the run-10 chain laundered a 160 mm displacement into a spec allowance, and
then every consumer of that allowance went blind. Measured:

```
$ python3 -X utf8 place_seed.py wk/run10/smartknob/board.kicad_pcb <out> \
      --intent wk/run10/smartknob/fp.json --repair --dry-run --clearance 0.2

  Repair census: 5 conflict pair(s), all listed
  Assembly census: 4 blocking body pair(s), all listed
Repair: 5 violator(s), 3 repaired (3 moved, max 3.00mm), 0 unresolved, 2 unrepairable
JSON_SUMMARY: {..., "oob_pad_count_before": 23, "repaired": 3, ...}
EXIT=4

real    4m55.225s
```

**5 violators. None of them off-board. 4m55s.**

### The same allowance blinds the reconstruct gate (latent, did not fire in run 10)

`place_reconstruct.py:193-217` builds `edge_bands` from the same
`overhang_mm.max` and hands it to `reconstruct.measure()`, where
`pad_oob_amount` charges only `max(0, amt - band)`
(`placement/reconstruct.py:75-111`). Measured on the damaged board:

```
edge_bands entries: 28
NO   bands: locked_contacts=0 pad_pairs=10 hole=0 oob=944.014 stacks=13 hpwl=2685.54 overlap=100.265
WITH bands: locked_contacts=0 pad_pairs=10 hole=0 oob=  4.348 stacks=13 hpwl=2685.54 overlap=100.265
```

**`oob` reads 4.35 on a board with parts 158 mm off the outline.** Run 10 got
away with it only because it never passed `--intent` to `place_reconstruct`
(checked: all four recorded `place_reconstruct` invocations in
`wk/run10/smartknob/` omit it). The skill's own P3/R3 rung
(`.claude/skills/plan-pcb-placement/scripts/placement_driver.py:250-251`)
offers `--intent fp.json` as an option, so the next run can walk into it.

### The 11 parts caused exactly the 13 unrouted nets

Re-derived, not quoted. For each of the 13 nets the run named as unrouted, the
pads whose **centres** are outside the Edge.Cuts outline:

```
BEFORE — nets with off-board pad centres: 13
  /STRAIN_DO   U4.12        /TMC_VH  U5.4 R8.1      Net-(C15-Pad2) U5.2
  /STRAIN_SCK  U4.11        /TMC_VL  U5.10 R12.1    Net-(C21-Pad1) U5.13
  /TMC_DIAG    U5.12        /TMC_WH  U5.5 R9.1      Net-(C22-Pad2) U4.6
  /TMC_UH      U5.3 R7.1    /TMC_WL  U5.7 R11.1     Net-(Q1-Pad1)  U4.2
  /TMC_UL      U5.6 R10.1
AFTER (re-seated) — 0
```

One-to-one. This is the whole capability gap.

---

## 1. What can be reused — the subset-seating path ALREADY EXISTS

**`placement/seeder.py:338-345` — `seed_from_intent(..., seed_refs=...)`.**

> `seed_refs`, when given, scopes the seeding to exactly those refs: every
> other part is treated as authoritatively placed where it stands
> (`placement/seeder.py:352-356`).

The mechanism is `placement/seeder.py:386-390`: any ref outside `seed_refs`
(or locked in the file) goes straight into `placed` and out of `unplaced`.
`placed` parts are **not** in the `exclude` set that stage 3 passes to
`_try_place` (`placement/seeder.py:679`), so they are live obstacles for
`candidate_valid`. That is precisely "hold every other part fixed as an
obstacle".

The seating itself is the from-scratch path the brief asks for:

| what | where | what it does |
|---|---|---|
| stage 3, connectivity centroid | `placement/seeder.py:653-693` | targets `_partner_centroid(...) or board centre` — **the part's current pose is never consulted** |
| `_partner_centroid` | `placement/seeder.py:301-335` | one vote per (partner footprint, net), fanout-capped at 20 so GND/rails cannot drag everything mid-board |
| `_try_place` | `placement/seeder.py:70-202` | nearest-FULLY-CONTAINED legal pose to a target: 3 clearance levels × 4 rotations × 3 ring bands (30/1.0, 16/0.25, 4/grid), then a 2.0 mm whole-board fallback sweep. `_ok` (`:111-114`) demands `rect_outside_amount == 0`, so a seat is on the board by construction |
| ring enumeration | `pose_score.py:33-52` `_offsets` | concentric, **nearest-first**, caller stops early |
| per-seat legality | `placement/quench.py:1005-1113` `candidate_valid` → `placement/legality.py:1094-1119` `pads_ok` | baseline-relative; a NEW different-net pad conflict, a NEW any-net stack, or a worsened hole shortfall is never admitted |
| gated re-seat precedent | `placement/seeder.py:695-736` (`--anchor-rounds`) | already snapshots, re-seats over the full placement, measures `reconstruct.measure`, and reverts the whole round if the tuple worsens. **The pattern to copy.** |

### It works. Measured, on the real damaged board.

Prototype: `seed_from_intent(pcb, board, intent_with_scope_edge_decls_stripped,
Random("0"), clearance=0.2, seed_refs={R7,R8,R9,R10,R11,R12,U4,U5,U8,TP4,TP5})`,
then write **only** the 11 scope moves.

```
=== seed_from_intent(seed_refs) took 6.3s ===
placements: 101 unseated: []

moves (dist, ref, new_x, new_y):
    (64.35, 'U8',  84.47,  81.70)    (49.88, 'U5', 101.02, 109.05)
    (59.81, 'TP4', 78.76,  78.78)    (49.53, 'R7',  98.14,  93.61)
    (57.32, 'R10', 94.44, 103.06)    (49.51, 'R9', 100.79,  97.16)
    (54.89, 'R11', 98.31, 101.28)    (49.00, 'R8', 100.24,  93.10)
    (53.75, 'TP5', 88.45,  78.63)    (38.06, 'U4',  66.95,  73.02)
    (53.56, 'R12',101.14, 100.71)
```

**11/11 seated, 0 unseated, 6.3 seconds.** Byte-identical across two runs
(md5 of the move table: `3d0bf880…` twice).

Gate and legality, before vs after (`reconstruct.measure`, no edge bands):

```
[BEFORE] locked_contacts=0 pad_pairs=10 hole=0 oob=944.014 stacks=13 hpwl=2685.54 overlap=100.265
[BEFORE] pad_conflicts=5 hole=0 oob_pad_count=23 blocking_body=4
[AFTER ] locked_contacts=0 pad_pairs=10 hole=0 oob= 18.691 stacks=13 hpwl=1658.85 overlap=100.265
[AFTER ] pad_conflicts=5 hole=0 oob_pad_count=12 blocking_body=4

gate improves (<=)?  True
  locked_contacts    0 ->    0  same
  pad_pairs         10 ->   10  same
  hole             0.0 ->  0.0  same
  oob          944.014 -> 18.69  BETTER
  stacks            13 ->   13  same
  hpwl        2685.542 -> 1658.8 BETTER
  overlap     100.2649 -> 100.26 same
```

Off-outline parts 18 → 7, and the 7 survivors are the LED ring / USB shell
(`J1 0.166, D6 0.124, D2 0.124, D4 0.098, D5 0.071, D3 0.071, D1 0.071` mm) —
genuine rounded-outline cosmetics, correctly declared edge connectors, exactly
what the report calls the human board's own nonzero floor.

Nothing above `oob` in the tuple moved. `pads_ok` held the line: it is a
structural guarantee (`placement/legality.py:1108-1118`), not luck.

### Cross-check of the report's numbers

The report's per-part figures (`R7 7.08 … TP4 32.50`) come from
`render_placement.py:214-233`, which measures the pad extent against the board
**bounding box**. My census uses `legality.BoardOutlineGate` against the real
**Edge.Cuts** rings, which on this rounded-square outline is tighter, so it
reads `R7 33.487 … TP4 158.512`. **The two channels disagree in magnitude and
agree exactly on the set of 11.** Use the outline channel; `render_placement`
itself documents the two-channel hazard at `:203-210`.

---

## 2. Does something close already exist? — yes, and here is what each is NOT

| candidate | verdict |
|---|---|
| `place_seed --repair` | Right census, right seating primitive, **wrong anchor and one fatal exemption**. Its cap ladder `REPAIR_CAPS_MM = (0.5, 1.0, 2.0, 5.0)` (`placement/seeder.py:781`) targets `ox, oy` = the part's own pose (`placement/seeder.py:1060`). For R7 at x=147.2 against a board ending at x=140.6, no cap reaches a contained pose. |
| `place_seed` `seed_refs` | **This is the pass.** Already engine-complete. It has **no CLI surface**: `place_seed.py:208-213` sets it only from `assess_placement(...).stacked_refs` on a *partially unplaced* board. |
| `--anchors-first` / `--anchor-rounds` | `placement/seeder.py:695-736`. Re-seats at partner centroids over the full placement with a gate+revert — the right shape, but scoped to *everything placed*, and only reachable on the from-scratch (`--force`) path, which is refused on a placed board (`place_seed.py:194-203`). |
| `place_portfolio` | `placement/portfolio.py:180-313`. Every strategy (`jitter`, `poses`, `swap`) is a **perturbation of the incumbent pose**. Same wrong centre. |
| `reconstruct` assign/exchange | `placement/reconstruct.py`. Candidate set per part is `{stay, +v, −v, pattern slots}` — no free-space enumeration exists anywhere in it. On this board `fit_proposals {}`, `vectors []`, so the candidate sets were singletons. |
| `placement/reseat.py` | **NAME COLLISION, different problem.** It re-seats a *proximity-tethered cluster* (decaps around an anchor IC) by Hungarian assignment over rings around the anchor's pins. It refuses outright when the members' nets are rails (`placement/reseat.py:385-388`), which is most clusters. Tested by `tests/test_reseat.py`. **Do not extend it, and do not reuse the module name.** |

**Conclusion: do not write a new script.** Add a flag to `place_seed.py` and a
stage to `place_reconstruct.py`, both calling one new engine function that is
mostly a wrapper over `seed_from_intent`.

---

## 3. The violator census — exact anchors, and the two lines to change

`repair_placement`'s census, `placement/seeder.py:850-987`:

| lines | channel |
|---|---|
| `:887-896` | intent grade errors carrying a ref |
| `:901-920` | `grade_pad_legality(worst_n=0)` conflict pairs → preferred mover charged, partner kept as fallback |
| `:926-941` | `grade_body_overlap` blocking body pairs |
| **`:944-962`** | **off-board pad/hole extents at zero margin** |
| `:980-987` | file-locked refs pulled out into `unrepairable`; the rest sorted by descending weight |

The exemption:

```python
# placement/seeder.py:950-953
for ref, part in state.parts.items():
    if ref in edge_refs:
        continue    # declared overhang is by design
```

with `edge_refs = {c['ref'] for c in intent.edge_connectors}`
(`placement/seeder.py:838`) — **unfiltered by band size**.

### The repo already computes the right answer and throws it away

`placement/seeder.py:867-872`:

```python
try:
    from placement import reconstruct as _recon
    witnesses = set(_recon.damage_witnesses(state))
except Exception:
    witnesses = set()
```

It is used **only** as a sort key in `_mover_key` (`placement/seeder.py:874-885`).
`damage_witnesses` (`placement/reconstruct.py:572-609`) returns refs with a pad
**centre** off the outline — "you cannot solder to air" — and is
corpus-calibrated to **zero on all 33 healthy boards plus 5 controls**
(`:583-590`). Measured now:

```
damaged board   damage_witnesses: 11  ['R10','R11','R12','R7','R8','R9','TP4','TP5','U4','U5','U8']
re-seated board damage_witnesses:  0  []
run-10 final    damage_witnesses: 12  ['R10','R11','R12','R7','R8','R9','TP4','TP5','U2','U4','U5','U8']
```

Exactly the 11, computed in 0.1 s, and **the shipped run-10 board has one
MORE** (U2, pushed off by the run's own moves). This is the auto-scope oracle.

### Is the "escalating cap from current pose" strategy pluggable?

**Hard-wired**, in two places, both trivially parameterisable:

* `placement/seeder.py:1056` `ox, oy, orot = part.x, part.y, part.rot` — the target.
* `placement/seeder.py:1058-1068` the `for cap in caps:` ladder calling
  `_try_place(..., ox, oy, ..., max_disp=cap)`.

`_try_place` itself is already target-agnostic: it takes `(tx, ty)` and an
optional `max_disp`, and with `max_disp=None` it skips both the per-offset cap
filter (`:172-174`) and the "a capped repair never sweeps the whole board"
early-out (`:183-184`). Passing a *centroid* target and `max_disp=None` is all
that is needed — which is exactly what stage 3 already does.

---

## 4. The gate — the brief's worry is real but points the wrong way here

Gate tuple: `placement/reconstruct.py:159-160`

```
GATE_TERMS = ('locked_contacts','pad_pairs','hole','oob','stacks','hpwl','overlap')
```
lexicographic, smaller-or-equal accepted (`:173-208`).

**Would the run-10 `oob`-over-`overlap` inversion sabotage a re-seat? No — the
opposite risk applies.** In run 10, `assign` reverted H2 because `oob` worsened
by 1.5 against an 8.25 mm² `overlap` win, and `oob` (index 3) outranks
`overlap` (index 6). A re-seat moves `oob` **hugely in its own favour**
(944.014 → 18.691), so the comparison is decided at index 3 in the pass's
favour. Measured above: `gate improves (<=)? True`.

That is the hazard. Lexicographic comparison **stops at the first differing
term**, so a large `oob` win *hides everything below it*: a re-seat could
create new `stacks` (index 4), blow up `hpwl` (index 5) or pile on `overlap`
(index 6) and the board-wide tuple would still accept. That is the mirror
image of the run-10 complaint, and it is the one to defend against.

**The gate this pass should use — three conjuncts, not one tuple:**

1. **Per-seat, structural (already free).** `_try_place._ok` →
   `candidate_valid` → `pads_ok` refuses any pose that worsens a pad pair,
   introduces an any-net stack, or worsens a hole shortfall
   (`placement/legality.py:1108-1118`). Measured: `pad_pairs 10→10`,
   `stacks 13→13`, `overlap` unchanged. Keep it; do not pass `--courtyard-only`
   equivalents through.
2. **Board-wide `measure()` on the round, with `edge_bands` computed
   EXCLUDING the scope refs.** Non-negotiable. With the auto-intent's bands
   in place the tuple reads `oob=4.348` and the pass looks inert; with the
   scope refs excluded it reads `oob=929.671`. Concretely:
   `bands = {r: m for r, m in edge_bands.items() if r not in scope}`. A ref
   being re-seated has forfeited its band — the band was measured off the pose
   being discarded.
3. **A pass-specific success conjunct that the tuple cannot express:**
   `oob` must **strictly improve** and `len(damage_witnesses)` must not
   increase. Report both; refuse the round otherwise. This is what stops the
   pass from "succeeding" by moving a part sideways, and it is the same
   both-conjuncts discipline the skill's R2 rung already demands.

**Per-part revert sweep, not all-or-nothing.** Reuse
`reconstruct.prune_assignment` (`placement/reconstruct.py:638-708`): walk the
moved refs by descending displacement, tentatively restore each, keep the
revert iff the tuple strictly improves. Pass `evidenced=scope` so an *equal*
tuple does **not** revert a scope ref (`:656-662` — a part coming back onto the
board is gate-neutral on several terms by construction, exactly like the
mounting-hole homecoming that rule was written for).

---

## 5. Cost

Measured, this board, 107 parts, 11 in scope:

| step | time |
|---|---|
| parse + `make_state` | 0.8 s |
| `damage_witnesses` (auto scope) | 0.1 s |
| **`seed_from_intent(seed_refs=11)`** | **6.3 s** |
| `write_placed_output` + `copy_siblings` | < 0.5 s |
| post-gate `measure` + `grade_pad_legality` + `grade_body_overlap` | 1.2 s |
| **total** | **≈ 8–9 s** |

Against `place_seed --repair` at **4m55s** for 5 violators and none of the 11,
and `place_reconstruct --stages classify,legalize --max-move 40` at
**>8.5 min**.

**Why it is cheap — and it is not mainly "small N".** The census is already
fast (`floorplan.grade` 0.8 s, `grade_pad_legality` 0.2 s,
`grade_body_overlap` 0.2 s, measured). The 4m55s is spent in **failed ring
sweeps**. Each `_try_place` call costs up to 3 clearance levels × 4 rotations
× 3 bands = 36 sweeps, and `_offsets(16, 0.25)` alone materialises ~16 000
positions; a capped call filters nearly all of them by
`hypot(dx,dy) > max_disp` (`placement/seeder.py:172-174`) **after** generating
them, then fails, then the next cap does it again. Four caps × a violator that
cannot be seated = the whole bill.

A re-seat pays none of that:

* **`_offsets` is nearest-first** (`pose_score.py:33-52`) and `_try_place`
  returns on the first legal pose. Targeted at a *good* centroid on a board
  with real free space, that hit comes in the first few rings of the first
  band at the first clearance level — one sweep, not 36×4.
* **`max_disp=None`**, so no ladder and no post-hoc filtering.
* Others held fixed means `candidate_valid` uses the cached neighbour lists
  and the `_incumbent_violation` cache without invalidation churn.
* N=11 is a linear factor on top of all that, not the reason.

Scaling estimate: cost is ≈ `O(|scope| × sweeps-to-first-hit × |neighbours|)`.
On the run-9 217-part board expect ~2–4× per part; a 20-part scope should land
well inside 60 s. Ship `--deadline` anyway (§6).

---

## 6. Concrete diff plan

### 6.1 `placement/seeder.py` — new engine function `reseat_scope()`

Add after `repair_placement` (i.e. after `placement/seeder.py:1186`).

```python
RESEAT_BAND_SANITY_MM = 5.0   # see 6.5

def reseat_scope(pcb_data, pcb_file, intent, *, refs=None,
                 group_sources=(), clearance=0.25,
                 board_edge_clearance=0.55, grid_step=0.1,
                 seed=0, deadline=None, progress=None) -> Dict
```

Body, in order:

1. `state = pose_score.make_state(...)` (mirror `placement/seeder.py:831-833`).
2. **Scope resolution.** `refs is None` → auto:
   `scope = set(reconstruct.damage_witnesses(state))`
   (`placement/reconstruct.py:572-609`). Otherwise the caller's list, glob-
   expanded with `fnmatch` over `sorted(pcb_data.footprints)`.
3. **Refusals, each named in `notes`, never silent:**
   * ref not on the board;
   * `state.parts[ref].locked` → into `refused`, with the exact wording
     `repair_placement` uses at `placement/seeder.py:980-985` ("not this
     tool's to move"). Applies to `must_lock` too, for the run-7 reason
     recorded at `placement/seeder.py:964-979`.
   * empty scope → return `{'reseated': [], 'reason': 'no off-board parts'}`,
     exit 0. A no-op is a result.
4. **Strip the scope's edge declarations** —
   `intent2 = dataclasses.replace(intent, edge_connectors=tuple(
        c for c in intent.edge_connectors if c['ref'] not in scope))`,
   and emit one note per dropped entry naming the band. **This is mandatory,
   not hygiene.** Measured with the bands left in:

   ```
   TP4 -> (   75.64, 30255.61)  moved 30227.73mm
   U8  -> (  124.36, 29936.63)  moved 29909.73mm
   R12 -> ( -3971.03,   89.85)  moved  4125.75mm
   ```

   Stage 1 (`placement/seeder.py:403-434`) places declared edge connectors
   **with no legality gate** at `(min+max)/2` overhang, and `_edge_correct`
   (`:223-245`) then walks toward an 80 mm target. Thirty metres off the board.
5. `res = seed_from_intent(pcb_data, pcb_file, intent2, random.Random(f"{seed}"),
   group_sources=..., clearance=..., seed_refs=scope)`.
6. **Emit only the scope's moves**: `[p for p in res['placements'] if
   p['reference'] in scope]`. `seed_from_intent` returns a placement row for
   every *placed* ref (101 of 107 here — the 6 missing are zero-pad
   footprints dropped by `QuenchState.__init__`,
   `placement/quench.py:~443-452`), and `state.parts[ref].rot` is
   **normalised mod 360**, so returning all of them would rewrite
   `-112.5 → 247.5` on 40 untouched parts. Harmless numerically, noise in
   every diff and every movie frame. Filter.
7. **Gate** (§4): `bands = {r: m for r, m in edge_bands.items() if r not in scope}`;
   `before/after = reconstruct.measure(state, bands)`; then
   `reconstruct.prune_assignment(state, old_poses, notes, edge_bands=bands,
   evidenced=scope)`; then the strict conjunct
   `after[3] < before[3] and len(damage_witnesses(state)) <= len(before_witnesses)`.
   On failure revert every scope move and set `accepted: False`.
8. `deadline` / `progress`: check `deadline.check('reseat')` **between refs**,
   mirroring `placement/seeder.py:1002-1008`. Partial is coherent — a ref is
   either fully seated or untouched. Report `deadline_skipped` and
   `complete: False`. (Note: `seed_from_intent` has no deadline parameter
   today; either thread one into its stage-3 loop at
   `placement/seeder.py:675-693`, or — simpler and sufficient at these
   runtimes — loop `_try_place` per ref inside `reseat_scope` and skip
   `seed_from_intent` entirely. Prefer the former: it keeps ONE seating
   implementation.)

Return dict:
`{'moves', 'reseated', 'refused', 'unseated', 'scope', 'notes',
  'gate_before', 'gate_after', 'accepted', 'witnesses_before',
  'witnesses_after', 'deadline_skipped', 'complete'}`.

### 6.2 `place_seed.py` — the flag

* argparse, beside `--repair` at `place_seed.py:88-93`:

  ```
  --reseat [REF ...]   LIFT the named parts and re-seat them from scratch at
                       their net centroids, holding every other part fixed as
                       an obstacle. With no REF, the scope is derived from the
                       off-outline pad-centre census (reconstruct.damage_
                       witnesses). Unlike --repair, the part's current pose is
                       NOT the search centre: a part 30mm from where it belongs
                       carries no information about where it belongs. Any
                       edge_connector declaration on a scope ref is DROPPED
                       (the band was measured off the pose being discarded).
  --reseat-deadline S  (or reuse a new global --deadline)
  ```
* Mutual exclusion: `--reseat` with `--force` is an error (same reason as
  `--repair`, `place_seed.py:98-100`). `--reseat` **composes with** `--repair`
  and should run **before** it — re-seat the off-board parts, then let the
  minimal-move repair clean up the local conflicts the new seats created.
  `--dry-run` must accept `--reseat` (`place_seed.py:101-102` currently
  rejects it unless `--repair`).
* Placement guard: `--reseat` requires a **placed** board, same as `--repair`
  (`place_seed.py:141-145`), and must bypass the "already looks PLACED"
  refusal at `place_seed.py:194-203`.
* Handler: insert a branch before the `--repair` branch at `place_seed.py:141`,
  modelled on `:146-192` — `write_placed_output` + `copy_siblings`
  (`:174-176`), then re-grade (`:177-188`).
* `JSON_SUMMARY` keys (additive; `place_seed.py:165-172`):

  ```json
  {"reseat": true,
   "scope": ["R10","R11","R12","R7","R8","R9","TP4","TP5","U4","U5","U8"],
   "scope_source": "auto:damage_witnesses",
   "reseated": 11, "unseated": [], "refused": [],
   "edge_bands_dropped": {"TP4": 160.062, "TP5": 160.062, "U8": 157.612, "...": 0},
   "witnesses_before": 11, "witnesses_after": 0,
   "oob_pad_count_before": 23, "oob_pad_count_after": 12,
   "gate_before": [0,10,0.0,944.014,13,2685.542,100.2649],
   "gate_after":  [0,10,0.0,18.6907,13,1658.845,100.2649],
   "accepted": true, "max_move_mm": 64.35,
   "complete": true, "deadline_skipped": [],
   "output": "..."}
  ```

  `witnesses_after` is the load-bearing number: **it is the one that predicts
  routability.** Exit 4 if `unseated` or `refused` is non-empty or
  `accepted` is false; exit 7 on a deadline hit (matching
  `place_reconstruct.py`).

### 6.3 `place_reconstruct.py` — the ladder rung

* `_STAGES` at `place_reconstruct.py:53`: insert `'reseat'` **between
  `'exchange'` and `'legalize'`**, and update the default string at `:73` and
  the help at `:75`. Order matters: re-seat the parts no vector can carry,
  *then* let legalize do minimal-move cleanup with everything already on the
  board.
* Wire it exactly like `_run_legalize` (`place_reconstruct.py:482-501`),
  including the `--dry-run` preview-in-tempdir path (`:513-527`) and the
  staged-write/promote invariant (`:530-541`).
* `edge_bands` (`place_reconstruct.py:193-217`): the reseat stage must call
  `measure` with the scope-filtered bands (§4.2). Add a printed line naming
  every band it dropped, next to the existing "Declared edge parts (band max
  mm)" line at `:213-216`.

### 6.4 Skill / driver

`.claude/skills/plan-pcb-placement/scripts/placement_driver.py:230-262` (P3
rung R3): add R3b — *"a part whose pad centres are off the outline is not
repairable by a minimal-move sweep; lift it. `place_seed.py --reseat`
(no refs = auto). The number to read is `witnesses_after`, not `repaired`."*
`:671` already carries the `a_off_outline` channel to key it off.

### 6.5 Companion fixes (small, independent, and this bug class recurs)

1. **`placement/floorplan.py:1311` and `:1318` — cap the emitted band.**
   `'max': round(min(amt + 0.5, RESEAT_BAND_SANITY_MM_or_part_extent), 3)`,
   and when `amt` exceeds the cap, emit the entry **without** an `edge` key
   plus a note ("observed overhang N mm exceeds any plausible band; treated as
   damage, no edge declared") — the schema already supports edge-less entries
   and both the seeder (`placement/seeder.py:409-417`) and repair
   (`placement/seeder.py:1024-1033`) already handle them. Generalises the
   mounting-hole refusal already at `placement/floorplan.py:1279-1288`.
2. **`placement/seeder.py:951-952` — narrow the exemption.** Skip a declared
   edge ref only while `amt <= band_max`; charge the **excess** otherwise. As
   it stands the exemption is unbounded.
3. **`place_seed.py` has no `--deadline`.** Its `repair_placement` call at
   `:146-150` passes neither `deadline=` nor `progress=`, while
   `place_reconstruct.py:488-494` passes both. That is run-10's T5, at
   file:line. Add `--deadline` + `krt_deadline.arm/emit` to `place_seed.py`
   while touching it.

### 6.6 GUI parity — **none required**

`tests/stress/manifest_to_plan.py:45-65` lists every `place_*.py` in
`REFUSED_TOOLS`: *"placement is CLI-only by design (there is no placement
tab)"*. No `FLAG_PARAMS` entry, no dialog control, no
`settings_persistence.py`, no `reset_params_to_defaults`. Confirmed by grep:
`kicad_routing_plugin/` contains no reference to any `place_*` script. And
`tests/gui_parity/test_cli_postpass_coverage.py:42-44` scopes `CLI_MAINS` to
`route.py, route_diff.py, route_planes.py, route_disconnected_planes.py,
bga_fanout/__init__.py, qfn_fanout/__init__.py` — no placement script, so the
Class-2-drift gate needs no registration either. Verified, not assumed.

---

## 7. Tests to extend (no new files where a row will do)

| file | what to add |
|---|---|
| `tests/test_place_seed.py` | The file already synthesizes a pile from `kicad_files/splitflap_driver.kicad_pcb` and grades against an emitted intent (`:44-76`). Add a **damaged-board fixture**: `write_placed_output` two or three parts to coordinates outside the outline, then assert (a) `damage_witnesses` names exactly those refs, (b) `--reseat` with no refs seats all of them, (c) `witnesses_after == 0`, (d) `gate_after <= gate_before`, (e) byte-identical across `PYTHONHASHSEED` (the file's existing `run(argv, hashseed=...)` helper at `:31-38` does this for `--seed`), (f) `--reseat` on a healthy board is a **no-op with exit 0** — auto-scope empty. |
| `tests/test_place_seed.py` | **The laundered-band regression.** Emit an intent off the damaged board, assert the emitted `overhang_mm.max` for a 30 mm-displaced part is capped and carries no `edge`; and assert `--reseat` drops any surviving band on a scope ref. Pin the 30-metre number as the counterfactual — it is the kind of finding that gets re-litigated. |
| `tests/test_place_reconstruct.py` | A `--stages classify,reseat --dry-run` row: the stage reports, moves nothing on a healthy board, and the ladder order `exchange < reseat < legalize` holds. Plus a row asserting the reseat stage's `measure` call filters `edge_bands` by scope — the value under test is `oob=929.671`, not `4.348`. |
| `tests/test_run4_reconstruct.py` | Its edge-band cases (`edge_bands` allowance, run-4 F2) are the ones most likely to break under §6.5.1. Re-run; if the cap changes an expectation, that is the finding, not a test to loosen. |
| `tests/test_reseat.py` | **Do not touch.** Different mechanism (`placement/reseat.py`). Add one line to the new engine function's docstring pointing at it, and vice versa, or someone will merge them. |
| `tests/test_placement_ab.py` | Not applicable — this is a legality/manufacturability pass, not a placement *objective* term, so the `ROWS` protocol (≥3 boards, paired, directional) does not govern it. Its acceptance is `witnesses_after == 0`, which is binary and per-board. Say so in the commit message; the CLAUDE.md rule is worded to catch objective terms and someone will ask. |

---

## 8. What this does not fix

* **Recovery** (distance to the original poses) is not the goal and this pass
  will not improve it — it seats by net centroid, so parts land where the
  netlist wants them, not where they were. On the run-10 subject that is a
  ~50 mm move per part in a board-centre direction. Judge it on
  `witnesses_after`, `unrouted` and `broken`, and expect
  `collateral_pad_rms` to grow. If the run also wants recovery, the
  reconstruct ladder's structural rungs are still the only source of it, and
  T2 (no pattern model beyond corner-inset mounting holes; this board's
  8-fold LED ring is invisible) is still open.
* The residual `oob = 18.69` / 7 courtyard-overhang parts are the outline's
  real cosmetic floor and should stay.
* `pad_pairs 10` and `stacks 13` are untouched by this pass **by design** —
  they are `--repair`'s job, and `--reseat` composes with it.
