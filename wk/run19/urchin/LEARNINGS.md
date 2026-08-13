# Run 19 learnings — what the piled board taught us, and what to fix before run 20

Provenance: run 19, urchin (103 parts / 82 nets / 2 layers), staged
`--kind pile` (declared), L0 blocking 13,708 → closed DONE-EXHAUSTED at
blocking 0, 68/68 nets, fence CLEAN. Evidence lives in `REPORT.md`,
`journal.md` (31 entries), `ledger.jsonl` (26 rows), and `stages.log` in this
directory. Engine patches from the run are committed at `d0feafb4`.

STATUS (2026-08-13 pre-merge wave): findings 4 and 6 and 7 and 10 are FIXED
and pinned on the open PRs (#623: coincident-origin blocking + pile-baseline
guard + both riders from 12; #624: flag accumulation + the disclosure
clause). Findings 1, 2, 3 are filed as issues #628, #629, #630. Findings 5,
8, 9, 11 remain follow-up.

Findings are ranked by what they COST this run. Each carries: the defect, the
measured evidence, what it cost, the concrete fix, and the pin that should
hold it.

---

## P0 — cost a full cycle or masked the truth

### 1. Interior milled contours are invisible to placement legality

**Defect.** A pad placed inside an interior milled ring (an Edge.Cuts contour
that is an inner outline / keep-out, not a hole) passes every placement gate.

**Evidence.** SW17 at (128.399, 61.001) rot 330: pad copper x-span
127.095–129.645 vs milled slot x 127.127–129.667 — the pad sits INSIDE the
ring. Placement gates all green: copper-free `check_drc` 0 @ 0.2,
`check_assembly` buildable / blocking 0, channels 0 deficit. The parser even
KNOWS about the contour — staging printed *"WARNING: reclassified 1 Edge.Cuts
contour(s) mis-read as board cutout(s)... Kept as a milled edge for
clearance"* — but legality never consumes that classification. Only the
ROUTER found it: a COL4-only probe on the poured-but-empty board failed at
219k iterations with zero copper competition, and `check_reachability`
answered PASSABLE because it does not model contour/edge clearance either.

**Cost.** One entire routing cycle: a 65-net route, close-out, verifier
dispatch, classification, and re-entry — hours — to discover what a placement
gate could have said in milliseconds.

**Fix.** `placement/legality.py`: treat reclassified interior contours as
keepouts in `rect_blocked` / pad legality (the reclassification already
exists at parse time; thread it through). Same model into
`check_reachability` so PASSABLE stops being refutable by a milled edge.
Related sibling defect, measured in the same run: a contour FULLY SWALLOWED
by a candidate rect is invisible to the outline gate (`rect_outside_amount`
only sees edges that cross the rect boundary).

**Pin.** A fixture board with an interior milled ring: a pad inside the ring
must flag in legality and grade CAGED/blocked in reachability; a candidate
rect that swallows the ring entirely must be refused.

### 2. "No legal pose" comes back without saying WHAT blocKED it

**Defect.** The seeder/reseat sweep returns "no legal pose anywhere on the
board" as a bare verdict. The engine can measure the blockers — it just never
volunteers them.

**Evidence.** Three sweeps returned bare no-legal-pose for SW17/SW34/
REF_PUCK_R (repair1, repair2, and the cycle-2 scoped reseat — the third was a
complete null: all three refs still at (128.40, 61.00), a passthrough board
written). When the widened attempt finally asked the right question, the
engine answered precisely: with D14 in place, 0 legal thumb-pocket poses; with
D14 lifted, 46. With D31: 0 → 32. That census IS the fix — it took one
eviction each and both switches seated.

**Cost.** One wasted scoped-reseat invocation (the cycle-2 null), plus the
entire hand-arrange detour in cycle 1 arguably traces here: five generator
versions were tried because nothing said WHY seats did not exist.

**Fix.** `placement/seeder.py`: when a sweep ends at 0 legal poses for a ref,
run a bounded second pass that lifts each nearby incumbent in turn and counts
poses freed; return `no_pose_blockers: {ref: {blocker: poses_freed}}` in the
JSON summary and print the top entries. A verdict that names its blockers
converts directly into the next move.

**Pin.** Fixture with a pocket blocked by exactly one movable part: the
no-pose result must name that part with a nonzero poses-freed count.

### 3. The seeder has no eviction/restructuring rung

**Defect.** Seeding places parts one at a time against a frozen rest. It
never lifts a blocker, so a piled board (or any seat behind a movable
obstacle) is unreachable even when legal space exists — the original design
proves room exists for every part.

**Evidence.** The pile needed a hand-arranged seed (`arrange.py`, disclosed)
before the engine could finish; the engine's own contribution was the last
mile (2× `place_seed --reseat --repair`). Cycle 2's winning pattern —
census the blockers, evict D14/D31, reseat — was executed MANUALLY through a
widened scope.

**Fix.** Make finding 2's census an automatic ladder rung:
seed → 0 poses → census → evict-and-retry (bounded depth, every move
gated and recorded). This composes with `reseat_scope` (PR #623's
lift-and-reseat) — the machinery exists; the ladder just never invokes it on
its own behalf.

**Pin.** The pile fixture itself: `place_seed` from a pile must seat a part
whose only pocket is blocked by one movable incumbent, without a hand seed.

### 4. Three parts stacked at one coordinate graded assembly-clean

**Defect.** `check_assembly` counts pad-intersection PAIRS. Three parts at
literally the same origin, rotated apart (330°/15°), happened to interleave
pads without pairwise contact — blocking 0, buildable.

**Evidence.** SW17+SW34+REF_PUCK_R all at (128.399, 61.001) graded
buildable / blocking 0 twice (cycle-1 close and the cycle-2 null). Only
advisory channels (courtyard oob, hole shortfalls SW17↔SW34 1.8227 mm,
SW27↔SW34 0.783 mm) hinted, and advisories do not gate.

**Cost.** The stack sailed through L2 twice; the router had to discover it.

**Fix.** `py_tools/check_assembly.py`: a coincident-origin check — N parts
with origins within ε of one point is a blocking finding (or at minimum flips
the verdict channel), regardless of pad-pair geometry. O(n log n), a dozen
lines.

**Pin.** Two clearing-pad parts at one origin → NOT BUILDABLE.

---

## P1 — real defects with bounded cost

### 5. Cooperative deadlines overshoot ~31%

**Evidence.** Both repair invocations: 1176.8 s and 1188.7 s against
`--deadline 900`, `stopped_in: legalize` both times. The mechanism worked
(exit 7, honest partial summary — it is why the run survived), but the
overshoot band is wide.

**Fix.** Tighten `cancel_check` polling granularity inside the legalize loop
heads (the coarse-grained sites are the overshoot); consider documenting an
expected overshoot bound in `krt_deadline`'s help so budgets can be set
against it. `bga_fanout.py`/`qfn_fanout.py` remain deadline-less (issue #621).

**Pin.** A deadline-tier test with a heavy legalize asserting overshoot below
a stated bound.

### 6. The pile baseline licenses pad intersections (`pads_ok` loophole)

**Evidence.** From cycle 1's repair currency: a pile baseline carries
thousands of pad intersections, and baseline-relative grading then accepts
any SMALLER intersection as improvement — this produced the SW23/SW28↔U2
blocker pairs that survived into the repair scope.

**Fix.** When the baseline is degenerate (pair count above a threshold, or a
declared pile stage), switch the acceptance test to absolute: zero pad
intersections or named residue. Where: the baseline comparison in the
repair/quench acceptance path.

**Pin.** Pile fixture: any output pad intersection flags despite the
baseline's thousands.

### 7. `--accept-unclosed` silently replaces on repeated use

**Evidence.** Measured live at L5: `--accept-unclosed agreement
--accept-unclosed ungraded` left only `ungraded` (argparse `nargs='*'`
replacement — the `--power-nets` bug class). The cross-check re-fired and the
close stalled until the flags were merged into one occurrence.

**Fix.** `loop_driver.py:~2151`: `action='extend'`, or an explicit refusal on
a repeated flag naming both occurrences. Same audit for `--accept-residue`
and every other `nargs='*'` flag in the drivers.

**Pin.** Self-test: two occurrences → both honored (or loudly refused);
either behavior pinned, silence forbidden.

### 8. Gates cannot read the close-out's own dispositions

**Evidence.** L2's oob gate refused on residue the placement close-out had
already NAMED AND MEASURED — twice across runs 18/19 (K32's 0.0933 mm AABB
echo; REF_PUCK_R's 1.3813 mm zero-net pads). The refusal is generic; the
orchestrator must re-derive the justification each time.

**Fix.** Keep the gate; improve its dialogue. When the close-out carries a
disposition for the exact failing check (a structured `residues:` block in
`check_assembly`'s JSON), the refusal should QUOTE it and print the exact
`--accept-residue <name>` invocation. The human decision stays explicit; the
evidence stops being re-typed.

**Pin.** Close-out with a named residue → the refusal text contains the
residue's own measurement and the ready-to-paste flag.

---

## P2 — orchestration and rig (wall-clock and honesty)

### 9. Teammate stalls dominated wall-clock

**Evidence.** Six-plus manual nudges. The reseat finished 07:08; the teammate
slept until nudged ~09:10. The cycle-2 route finished 09:52; asleep again
until nudged. Rough estimate: the run's wall-clock doubled from arm-a-watcher
-and-stop patterns whose watchers misfire.

**Fix.** Doctrine for run 20's briefs (and worth a line in the skill): drive
on FILES with bounded poll loops — a teammate that launches a detached search
must poll its output on a stated interval with a stated ceiling, never
arm-and-stop. Orchestrator side: poll the contract paths on a timer as the
primary signal and treat notifications as an accelerator, not the mechanism.

### 10. Hand-script disclosure must be in the delegated prompt

**Evidence.** The cycle-1 teammate built `arrange.py` v1→v5 and disclosed the
drift only when challenged with a directory listing. Once challenged, the
disclosed hand-seed → engine-legalize path was legitimate and is quoted in
the ledger; undisclosed, it would have invalidated the run.

**Fix.** Add to L1/L2's emitted subagent prompts (loop_driver): use the
repo's engine tools for every board mutation; any script that computes or
writes poses/copper must be disclosed immediately and named in every ledger
lap it feeds — a disclosed hand-assist is a finding, an undisclosed one
invalidates the run.

**Pin.** The instruction-quality suite greps the emitted prompt for the
clause.

### 11. Choose damage kinds the fence can adjudicate

**Evidence.** Run 18 (swap on a grid-homed keyboard): perfect recovery is
byte-identical to truth — the fence's LEAK verdict was undecidable by
construction. Run 19 (pile): a from-scratch placement cannot byte-match
truth — fence CLEAN was decisive, twice.

**Fix.** RUNBOOK "choosing a subject": on grid-homed boards prefer
pile/scatter, or pre-declare that byte-identity will be undecidable and name
the secondary tell (a session file-access audit) before staging.

### 12. Small rig papercuts

- `qualify_subject --json` dies if the output directory does not exist
  (mkdir it).
- `strip_copper_only` prints a prose fragment as its usage line (docstring
  index slip).
- `stamp_locked` returned 28 stamps for 25 refs (multi-block footprints) and
  36 for 37 (an already-locked ref) — correct behavior, confusing count;
  print `refs matched / blocks stamped` separately.

---

## What worked and must be kept

- **The probe → classify → scoped-fix cycle.** Routing evidence (a pad in a
  milled slot, 219k failed iterations) re-entered placement as a scoped
  repair and the reroute closed 68/68. This is the run's headline and the
  design's justification.
- **Every run-17 D-series fix held under live fire**: the printed `--final`
  command ran as printed (D1, twice); cycle-2's close-out graded against
  cycle 1's authored baseline (D5); the cross-check and ungraded gates
  refused exactly when they should and took only NAMED waivers; `_cN`
  suffixes protected cycle 1's artifacts; both halves closed by reasoned
  `--exhausted` declarations that the verdict then honored.
- **Honest instruments compound.** check_complete's UNSOUND caught a 0.2 µm
  sub-floor write (cycle 1); the fail-closed posture and the disclosure
  discipline (arrange.py chain quoted in the ledger) made the final CLEAN
  fence verdict meaningful.
- **One ledger, one film.** 116 frames spanning both halves and both cycles,
  reconstructed entirely from recorded laps.
