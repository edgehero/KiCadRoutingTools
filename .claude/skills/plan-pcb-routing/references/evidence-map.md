# Evidence map: produce X → read key Y → do Z

Every artifact the placement tools emit, the exact JSON key to read from it, and
the decision that key drives. Read this before quoting any number.

**The governing rule: never read a picture on its own.** Every render is paired
with a number that either confirms or contradicts it, and the number wins.

Keys are literal. If a key below is not in the output you are looking at, you are
looking at the wrong artifact — do not substitute a similar-looking one.

---

## A. Lock advisor — `place_optimize.py BOARD --suggest-locks --suggest-locks-json wk/locks.json`

Writes no board. Run it **before** the first placement run, and read the reasons.

| key | decision |
|---|---|
| `JSON_SUMMARY.unlocked_high` | **The gate.** Must be `0` before placement runs. Re-run with your `--lock` list until it is, or name each finding you are leaving free and why |
| `findings[].evidence.npth_pads > 0` and `plated_pads == 0` | A structural mounting hole. It has **no net, so no airwire at all** — nothing but the halo term decides where the optimizer slides it. Always lock |
| `findings[].evidence.outside_amount_mm > 0` | The body legitimately leaves the outline (card edge, USB shell, HAT header). Lock it **and** add it to the intent's `edge_connectors` |
| `findings[].evidence.edge_clearance_mm` | Measured, exact. Use it as the intent's own limit rather than inventing one |
| `findings[].evidence.connected_pins` | `0` → invisible to the cost. `>= 40` → see `advisories` |
| `findings[].evidence.side` | Which face — decides whether the verify render needs `--per-side` |
| `advisories[].kind == "high_pin_count"` | `place_optimize` has **no** `--max-target-pins` guard (`place_route_loop` does). Either lock these or use the loop. Never let a ≥40-pin part move in a bare `place_optimize` run |
| `lock_argv` | Paste verbatim — it is already argv-shaped. Do not retype `lock_patterns` by hand |
| `locked_refs` | Refs the FILE already pins. Advice telling the user to move one of these is wrong |
| `findings_covered` vs `findings_high` | Round-trip proof your `--lock` list actually matched, rather than matching nothing |

A **quiet result is "nothing detected", not "nothing to lock"** — the lexical
rules (footprint name, reference prefix) miss house libraries entirely.

---

## A2. Board brief — `py_tools/board_brief.py BOARD --json wk/brief.json [--fit WxH]`

What to read BEFORE authoring a placement, assembled from the emitters that
own each number (`sources` names the function per section, so a disagreement
with a grader is a bug in one of them, never a second opinion here).

| key | decision |
|---|---|
| `state.unplaced` / `state.stacked_suspect_refs` / `state.reasons` | is this a pile at all, which refs form it, and which signal fired |
| `position_dependent.invalid` | **read this before any number below it.** On a piled board the keys it names are `null` — measured from part positions, and there are none yet. Includes `structure.decap_tethers`, `structure.groups.decap` and `structure.groups.netprefix`, so the grouping an author reaches for first is among them |
| `position_dependent.also_pose_derived` | KEPT but pose-derived, each with its caveat: `parts[*].extent_mm` (swaps W/H with rotation — a staged board carries rotation 0, so 25–43% of parts are transposed), the per-face escape table, `worst[]` membership, `renders.*`. Not null, not trustworthy as-is |
| `position_dependent.gate` | which test fired — `state.unplaced`, or the pile fraction. The stager's mechanical exemptions can keep `state.unplaced` False on a board that is 89% piled, so the fraction is the one that catches it |
| `board.milled_contours` | **non-zero means #628 territory** — an interior milled ring a pad can sit inside while every placement gate calls it legal |
| `board.cutout_rings` / `outline_rings` / `milled_contour_rings` | ring vertices in board coordinates. These are the source for `place_keepout`'s `rect`: a part in a cutout is unroutable and no bounding-box view shows it |
| `board.outline_source` | `edge_cuts_contours` or `bounding_box`. The parser short-circuits a plain axis-aligned rectangle and returns no contour, so on those boards `outline_rings` is the bbox — correct, but derived rather than read |
| `board.copper_area_mm2` | outline minus cutouts, by shoelace. **Not** `options.grow_board`'s `usable_area_mm2`, which is the bbox minus the edge band and is cutout-blind |
| `parts.<ref>.at` / `.rect` | where the part is now, board frame. `rect` is the same absolute rect `legality.graded_parts_from_file` grades. On an unplaced board this is the pile coordinate — cross-read `state` |
| `parts.<ref>.extent_source` | `pad_bbox` means that part has NO courtyard, so its extent carries no margin — do not treat it like a courtyard number |
| `mechanical.refs` | the parts whose position is a mechanical fact, with class, confidence and evidence. **Pose-independent**, so unlike `measurements.locks` it still answers on a pile |
| `mechanical.refs.<ref>.pose_shared_with` | empty = that part sits alone at its coordinate, so its `at` is a real pose and can be asserted with `place_fixed`. Non-empty = it is in the pile and the coordinate means nothing |
| `fit[].fits` / `.centre_bounds` | whether a `WxH` part has anywhere to go at all, and roughly where. `fits: false` is a capacity finding, not a placement one — go to A3. **Valid on an unplaced board** — it probes the outline, never another part |
| `measurements.escape.deficit_lanes` | lanes short across the board. Non-zero is a BINDING constraint: net ordering only chooses which nets strand. `null` on an unplaced board |
| `measurements.locks.tally.unlocked_high` | same gate as section A; the brief carries it so one read covers both. `null` on an unplaced board — use `mechanical` there instead |
| `skipped` | **a section that did not run.** Non-empty means the brief is incomplete — never read a missing section as "nothing to report" |

`null` and absent are different answers here: `null` means "this key exists and
this board cannot support it" (with the path named in `position_dependent`),
while an absent section means it did not run and `skipped` says why.

## A3. Capacity options — `py_tools/check_capacity.py BOARD --json wk/capacity.json`

Reports; never acts. Exit is always 0 — a gate here would refuse boards that
route fine, because the area test is necessary and not sufficient.

| key | decision |
|---|---|
| `options.grow_board.fits_by_area` | `false` = the parts CANNOT fit, whatever the arrangement. Stop placing and report |
| `options.grow_board.measured.shortfall_mm2_at_least` | **the number the outline prohibition asks for.** Quote this, not an estimate. "at_least" is literal: it is a lower bound |
| `options.grow_board.measured.utilisation` | ≥ ~0.55 means they fit but will fight the router |
| `options.add_layers.measured.floors_differ` | `false` = more layers change the fab floor not at all, so they buy no extra lanes on a face. Do not recommend layers off this option alone |
| `options.move_blocker.measured.worst[].span_needed_mm` | millimetres of span to free, and `blockers[0]` is who to move. This is the actionable pair |
| `options.relax_clearance.measured.ladder[].below_fab_floor` | `true` rows are UNMEASURED, deliberately — capacity nobody can etch is not capacity |
| `options.<name>.error` | `true` = the option CRASHED. Not the same as `ran: false`, which means it did not apply |

## A4. Placement plan run — `py_placer/place_plan.py BOARD plan.json -o OUT --json wk/plan.json`

| key | decision |
|---|---|
| `parks[]` | **every part the plan could not seat**, with `target`, `within` and `reason`. Empty is the only clean result; exit 4 means non-empty |
| `parks[].blockers` / `.censused` | issue #629's answer. `censused: false` means nobody looked; `censused: true` with all-zero values means the parts you named are innocent |
| `parks[].census_step_mm` / `.census_radius_mm` | the window those counts were taken in. **Counts are commensurate WITHIN one park and not across budgets** — 253 poses at 0.1 mm and 113 at 0.25 mm are not a decrease. A `census_radius_mm` below the op's `within` means the sweep was capped and the counts are the near field |
| `parks[].constraint` / `.tol` | the zone this seat had to satisfy. Non-null means every count in the park is **inside that zone** — do not compare it with an unconstrained park's. When the zone itself is the problem, read the op's capacity note (`the usable zone is X mm2 and these parts need AT LEAST Y`), not the blocker list: the blockers answer "what is in the way *within the zone*", the note answers "is the zone big enough at all" |
| `seats[].moved_mm` | how far the seat landed from what the plan asked for. A large value means the BOARD disagreed with your intent — read it before concluding the plan worked |
| `seats[].rot_changed` | the requested rotation was not legal and the lattice fallback fired |
| `summary.relaxed` | seats taken at a courtyard clearance below the asked-for floor |
| exit `2` | the plan is not executable as written; **nothing was placed**. Read the refusal — it names the op or key |

## B. `place_optimize.py IN OUT ... 2>&1 | tee wk/place.log`

The `JSON_SUMMARY` goes to **stdout only**; `tee` is what makes it citable.

| key | decision |
|---|---|
| `parts_moved` | `0` → nothing happened. Do not render a delta or claim improvement; widen `--max-displacement` or narrow `--lock` |
| `crossings_before` / `crossings_after` | **Report only -- NEVER a gate** (run-6: crossings correlates POSITIVELY with distance-to-truth, r = +0.78, so gating on it rejects correct homecomings). Gate on hpwl + PAD-PAD + the assembly channel. Any increase → route from the original board |
| `hpwl_before` / `hpwl_after` | **Discard gate.** Same |
| `overlap_area` | Courtyard overlap of the output. Must not increase. **Absolute zero is the wrong test** -- one shipped, legitimately placed corpus board carries 81 of its 82 parts in courtyard violation |
| `oob_count` | Parts leaving the outline. Must not increase, and every one should be in the intent's `edge_connectors` |
| `oob_amount` | Severity. Count flat but amount up = an already-overhanging part got pushed further out |
| `oob_area` | **Do not gate on this.** Measured against the bounding-box inset, so a part sitting entirely inside a **cutout** scores `0.0` |
| `cost_before` / `cost_after`, `airwire_length_*` | **Weighted.** Comparable only within one run. A big `cost` drop with flat crossings/hpwl means halo and edge moved: cosmetic spreading, not routability. Do not report it as an improvement |
| `blocks` / `block_parts` | Proof `--group-by` did anything. `blocks: 0` → drop the flag |

---

## C. `render_placement.py ... --json --ignore-nets <same set as B> -o wk/view/`

Always pass `-o`. Without it the tool writes `<board>_placement.png` **next to
the board**.

**Pass the same `--ignore-nets` you gave `place_optimize`, or the re-measurement
below compares two different net sets and always "fails".** B's numbers exclude
the plane nets; this tool's do not unless told to. On one run, GND
alone moved the same board from 53 crossings to 116 — which reads exactly like a
corrupted write and is not one.

| key | decision |
|---|---|
| `metrics.crossings`, `metrics.hpwl` | **The re-measurement channel.** Run this on the *written output board*; with the same `--ignore-nets` it must reproduce B's `*_after` **exactly** (53 / 587.3150 on both sides, not "about the same"). A mismatch means something was lost between the objective and the file — this is the self-assertion ban with teeth |
| `metrics.overlap_area`, `metrics.oob_*` | Independent read of B's legality numbers off the file |
| `metrics.halo`, `metrics.edge` | Cost decomposition. `total` improved while `length` and `crossings` did not ⇒ the win was halo/edge only ⇒ not a routability win |
| `no_outline: true` | The oob metrics are **unavailable**, not zero. Say "unavailable" — never "0 parts off board" |
| `unplaced: true` | The placement CLIs would exit 3. Report and stop |
| `moved` | Cross-check against B's `parts_moved`. A mismatch means you rendered the wrong `--before`/board pair |
| `failed_nets`, `blocker_nets` | Which nets the picture colours. Non-empty only when `--summary-json` was given — this is what ties a render to a specific route log |
| `panels[].path` | The exact PNG to `Read`, and what goes in a verifier's `evidence=` |
| `panels[].view` | The world rect that panel covers. **A finding at a coordinate outside it was not visible in that panel** — reject the claim |

---

## D. `wk/loop_round{N}.json` — the `place_route_loop` sidecars

Nobody reads these today, and they are where the loop's actual history lives.
`place_route_loop` prints **no** `JSON_SUMMARY` for a normal run.

| key | decision |
|---|---|
| `accepted` | Only accepted rounds are progress. Never quote a rejected round's board as the result |
| `parent` | **The board this round derived from — the last ACCEPTED board, not N−1.** Use it as `--before`. Using N−1 renders a delta that never existed |
| `screened` | `true` → the ratsnest screen skipped the routing run and `metrics` is empty. Never report failures for a screened round |
| `metrics.failures` | **The ratchet.** Unchanged across two consecutive non-accepted rounds → floorplan-limited → stop, do not raise `--rounds` |
| `metrics.failed_nets` | Feed to `--ratsnest-nets` and to `/diagnose-routing-failures` |
| `metrics.blockers` | The other half of the move-candidate set. **Empty blockers with non-empty failures means there is nothing to move** — not a placement problem |
| `metrics.iterations` | `better()` requires `< best × 0.95`, so a round improving effort by under 5% at equal failures is **rejected by construction**. That is the tool working, not evidence the placement is wrong |
| `metrics.vias` | The cost side of the trade. Report it; do not hide a failures win paid for in vias |
| `metrics.pad_pairs_connected` / `_total` | A round that lowers `failures` while lowering the connected ratio is not progress |
| `metrics.ratsnest_crossings` / `_hpwl` | The proxy beside the router's verdict. Proxy improving while `failures` is flat ⇒ proxy exhausted, stop |
| `metrics.ratsnest_length` | **Weighted, report-only.** Never compare across rounds |
| `targets` | Which refs the round was allowed to move. Any `must_lock` ref here → tighten `--lock` and re-run |
| `groups` | What blocks pulled extra parts in. A 40-part block here means the round moved far more than you targeted |
| `moved[].reference` / `.from` / `.to` | Exact per-part deltas. Intersect with the lock advisor's high-confidence findings; a non-empty intersection is a blocker, not a note |

---

## E. `check_floorplan.py BOARD --intent ... [--health]`

| key | decision |
|---|---|
| exit code | `0` clean · `2` argparse or malformed intent · `3` board state / untrustworthy outline · `4` **violations found** |
| `pass` | The gate |
| `violations_by_rule` | Which rule fired, and how often — names the thing to fix |
| `violations[].measured` vs `.expected` | The falsifiable number. This is what goes in a verifier's `evidence=` |
| `rules_run` / `rules_skipped` | **Anti-vacuity.** `0 violations` with `rules_run: 0` means nothing was checked. Quote both |
| `blocks_resolved` vs `blocks` | A block resolving to nothing is reported as an error, but check this too |
| `state_*` | `duplicate_fraction`, `spread_ratio`, `outside_fraction`, `partially_unplaced` — the signals behind the exit-3 verdict, and the only place they are emitted at all. `partially_unplaced` is the case exit 3 **hides**: a netlist re-import dropped a few new parts at the origin on an otherwise-placed board, and "place these specific refs" is the right instruction |
| `state.stacked_refs` vs `state.stacked_suspect_refs` | Co-located refs, and the subset `partially_unplaced` is actually decided on. They differ **by design** — parts the far side of the board cannot reach, and marker classes (fiducial / mount_hole / testpoint) that share a coordinate deliberately, are excluded. Quote the SUSPECT list; a non-empty `stacked_refs` beside `partially_unplaced: false` is normal, not a broken check. Two traps: a **drilled** part counts on both sides, so it is never excluded by side; and being `(locked yes)` is **not** an excuse, because this toolchain stamps its own locks |
| `outline.cutouts` / `.edge_contours` / `.simple_rectangle` | What the parts must avoid. `edge_contours` are clearance-bearing and **invisible in every render** |
| `health_block_displacement_max_mm`, `health_blocks_displaced` | How far a block sits from what it connects to. The 80 mm-magnetics failure mode a nudge cannot fix |
| `health_bus_foreign_crossings` | What crosses a declared bus corridor |
| `health_signals_skipped` | Signals that did not run, each with a reason. `blocked_cell_share` always needs a route first |

---

## F. Routing summary — `route.py`'s `JSON_SUMMARY`, in `wk/route.log`

The feedback edge back into placement.

| key | decision |
|---|---|
| `failed_single`, `failed_multipoint[].net_name` | The failure set → Step 9's classifier, and `--summary-json` for the render |
| `blockers[].blocked_by[].net` | Which routed nets wall off each failure → the move-anchor set |
| `pad_pairs_connected` / `pad_pairs_total` | The honest completion number for comparing two placements |
| `total_iterations` | Effort. A placement that halves iterations at equal completion is a real win |
| `total_vias` | The cost side of the same trade |
| `power_trace_ampacity[].bottleneck_width_mm` | **Did the width you asked for actually happen?** `--power-nets-widths` degrades quietly: a wide tap that will not fit is re-routed at the layer default (#72's neckdown retry), and on a dense board that fallback can take the *whole* run, not just the pad. Measured, `--power-nets-widths 0.8` on a pair produced **1.30 mm of 0.8 mm copper out of 41 mm** — three of the four nets got none at all. Compare this key against what you asked for, every time; the routed board is DRC-clean either way |
| `min_clearance_used` | The floor the run actually reached, which is **not** what you asked for. Below your netclass means the gap-rescue stepped down toward the fab floor. Measured: nominal 0.16, `min_clearance_used` 0.127, and **25% of all copper (180 of 710 mm) ended up at 0.127** — under the board's own 0.15 minimum. The `.kicad_pro` writeback then clamps the DRC floor to the routed value, so **KiCad grades it clean**. This key is the only place the step-down is visible |
| `rescue.unchanged` | Nets the rescue pass could not improve. Distinguishes "nearly made it" from "never had a path" |

### Routed length: half of it is already built, and the half that is not will bite you

**Matching IS supported — use it.** `route.py` / `route_diff.py` take
`--length-match-group NETS --length-match-tolerance MM`, `length_matching.py`
measures each net with `net_queries.calculate_route_length` and prints
`WARNING: <net> is X mm SHORT of the group target`, and
`/review-routed-board` Step 2 grades the spread. A spec clause like *"XTAL legs
symmetric to within 1 mm"* or *"QSPI intra-group skew <= 5 mm"* is a
`--length-match-group`, not something to hand-roll.

**An ABSOLUTE cap is not expressible anywhere.** No `check_*.py` says "this net
must be under N mm" or "this net must have 0 vias". (`check_orthonormal
--max-len` is per-segment non-orthonormality; `check_impedance
--min-void-length` is a void run.) So `QSPI <= 15 mm pad-to-pad, 0 vias` and
`XTAL <= 10 mm/leg` have to be measured from `pcb.segments` by hand — do it, and
say plainly that you did.

One routed board graded **`check_floorplan` PASS** and 86%
connected while breaking **19** such limits, including a QSPI net at 32.6 mm
against a 15 mm HARD budget and crystal legs 6.03 mm apart against 1 mm. Green
on the KRT gates is not green on the spec.

### The DRC writeback RATCHETS — check it between chain steps

`route.py` clamps the sibling `.kicad_pro` down to what the run actually
achieved, and **that includes `track_width`, which the next step reads back as
its nominal**. Measured across one chain:

| project | `Default.clearance` | `Default.track_width` |
|---|---|---|
| `placed.kicad_pro` (authored) | 0.16 | 0.16 |
| after the signal route | **0.127** | **0.127** |
| after the plane pour | 0.127 | 0.127 |
| after the repair route | 0.127 | 0.127 |

One rescue at 0.127 became the default width for every later step, and 25% of
the final copper (180 of 710 mm) sits at 0.127 — under the board's own 0.15 HARD
minimum. Because the project now *says* 0.127, `check_drc` and KiCad both grade
it clean; grading the same board at the pre-clamp 0.16 gives **34** violations.
`min_clearance_used` and `Default.track_width` are the two places this is
visible. Diff the `.kicad_pro` between steps whenever the spec has a width floor.

---

## G. Blocks

| output | decision |
|---|---|
| `route.py --list-groups`: `parts=`, `touching=`, `internal=` | The routing-scope decision. `internal ≈ 0` ⇒ only `touching` is meaningful (always true of `decap`) |
| `render_placement.py --list-groups`: `parts=`, `front=`, `back=` | A block with parts on both faces cannot be reviewed in one panel |

---

## H. The board score — `scripts/board_score.py BOARD --json wk/score.json`

The only number that decides better-from-worse in the Step 9 loop, and the only
one produced by something **other than the tool being graded**. Everything else
on this page describes what a step *claims*; this describes what the board *is*.

| key | decision |
|---|---|
| `blocking` | **must reach 0 before the board is deliverable.** `unrouted + broken + drc + undersized + floorplan + impedance + length` |
| `blocking_by.<component>` | names WHERE the blocking sits. **The largest entry is NOT automatically the lever** -- that rule wrecked a run. Choose by the connectivity-first ladder (unrouted -> broken -> widths -> floorplan -> drc); an entry's size ranks within a rung, never across rungs |
| `quality` = `{vias, copper_mm, segments}` | tie-break **only** at `blocking == 0`. Comparing it earlier lets a router trade a disconnected net for a lower via count |
| `ungraded` | components nothing examined (no `--intent`, no `--impedance-nets`, no `--length-groups`). **Report as unexamined, never as clean** |
| `unknown` | a component that was asked for and could not run. `blocking` is `null`, not 0 — the loop must not stop here |
| `components.drc.graded_at` | the clearance actually graded at. Confirm it is the routed floor; stricter invents violations, looser hides them |
| `components.drc.by_type` | `segment-segment`, `pad-segment`, … — clearance conflicts |
| `components.undersized.by_type` | `track-width`, `via-size`, `via-drill-size` — **sub-spec copper** |
| `components.floorplan.rules_run` / `.rules_skipped` | `0 violations` with `0 rules run` is a vacuous pass. Quote both |
| `connectivity_nets` | *which* nets failed. Same nets every iteration ⇒ parameters; different nets ⇒ congestion |
| exit code | `0` blocking is zero · `4` graded with blockers · `3` board state · `2` args · `1` crash |

**The size floors default to the FAB minimum, not the spec.** `check_drc` derives
them from the copper-layer count, so a via that clears the fab and violates the
board's own tighter spec **grades clean**. That is not hypothetical: 141 of 141
vias at 0.25 mm ⌀ passed against a 0.6 mm spec requirement. If the spec states
sizes, pass them:

```bash
python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/board_score.py board.kicad_pcb \
    --intent wk/floorplan.json \
    --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3
```

**Omit `--clearance`.** `check_drc` then reads the sibling `.kicad_pro`, which is
the floor the board was actually routed to (see F's writeback ratchet). Pass one
only when you know better than the board.

### `ledger.jsonl` — the Step 9 ledger (one `converge.py record` line per iteration)

| key | decision |
|---|---|
| `parent_sha` | the last **accepted** board (content hash; `step-back --to` checks it out). Resolve it for `render_placement --before`; using N−1 renders a delta that never existed |
| `lever` + `lever_argv` | `lever` is the one-line intent, `lever_argv` the reproducible command — `replay` refuses prose-only entries. "tuned parameters" is not a lever. Verdicts and stop-condition claims have no field of their own: name them **in the `--lever` text** |
| `accepted` (`--rejected` at record time) | a rejected iteration is data — keeping it is what makes "five unchanged iterations" (stop-3) detectable |
| `score.blocking` | flat across FIVE consecutive iterations, after the rip lever / finer grid / layer change ⇒ stop condition 3 (9.5 and convergence.md both say five; the connectivity components are what must be flat, not drc) |
| `kind` | `systemic` = budget went to the instrument; `status` warns when that share hits half |
| accepted `result_sha`s, in order | the frame list for `make_movie.py`. Reverted boards animate a change that was undone |

Full procedure: [`convergence.md`](convergence.md).
