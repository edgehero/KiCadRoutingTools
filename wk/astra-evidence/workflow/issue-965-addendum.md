Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

## Follow-up: two claims are already corrected; a live model-choice conflict remains

Audit pinned to **5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3**, with the shipped drivers executed under KiCad 10 Python 3.11.5. Scope remains the placement skill and combined skill. The routing skill's enforcement prose should not be cut by a volume target before its required checks have another reliable implementation.

### Correct the current baseline

1. **The cited crossings contradiction at placement line 1214 is already fixed.** The `discard` instruction applies to increased HPWL; the following sentence says increased crossings “does not bar anything.” Do not remove a current safeguard by treating that corrected sentence as the obsolete crossings veto.
2. **Per-stage output caps already exist.** The grep in the issue missed `_BODY_CEILING` and `_ARM_CEILING`. Running placement `--self-test` exits 0/OK and checks populated bodies against individual ceilings. Running loop `--dump-all` exits 0 and prints the populated-arm ceilings. These are stage-output caps, not whole-file caps, and their existence does not resolve document growth.

Measured examples:

| emitted body | actual lines | ceiling |
|---|---:|---:|
| placement P-brief | 54 | 60 |
| placement P0 | 75 | 78 |
| placement P1 | 57 | 60 |
| placement P3 | 79 | 80 |
| placement P4 | 98 | 100 |
| loop L1 delegated / inline | 100 / 21 | 105 / 25 |
| loop L2 delegated / inline | 223 / 91 | 225 / 95 |
| loop L5 terminal arms | 161 | 170 |

These counts come from the drivers' controlled populated fixtures, **not token measurements or actual agent cost savings**. Driver source-line counts are also not the same as model input: Python comments/functions the agent never reads do not automatically consume its context.

Current file lengths remain placement skill 1,682; combined skill 1,449; placement driver 3,388; loop driver 5,113. Routing skill 2,895 is counted for context only, outside the shortening target.

### A current contradiction more relevant to Astra's placement capability

The placement skill around lines 937–949 explicitly supports a model-authored from-scratch placement loop: inspect the context, choose poses/rotations/locks with `place_pose.py`, render, adjust, and use seeding/repair/quench as final polish. That is a valuable supported action surface.

But the **P1 “unplaced” driver**:

* First calls `_guard_zone_plan`, requiring every movable part to be covered by zone rectangles before it will emit the stage.
* Emits an ordered seeder ladder, ranking seed candidates, then a face adjustment.
* Ends with “This toolchain does not invent a placement,” conflating unknown mechanical geometry with ordinary placement decisions.

The P1 missing-zone-plan branch was exercised against the existing Tigard fixture and returns exit 4 in 0.125 s, asking for zone rectangles. This is an **interface/guard test**, not a claim that the already placed Tigard board is a from-scratch board or that an autonomous model failed at it. Source inspection establishes that this guard also fronts the unplaced path. The real question is why the model-authored path endorsed by the skill has to satisfy the seeder's specific input representation.

There is another current mismatch: combined SKILL line 968 declares increased aggregate `overlap_area` an illegal placement and tells the executor to discard it; placement SKILL around lines 1234–1236 says to report aggregate overlap area and **never gate on it**, using real assembly checks instead. The same model can read both instructions. Replace the combined row with the actual graded conditions and their provenance, rather than reintroducing an aggregate proxy as an absolute legal constraint.

### Proposed structure: preserve board knowledge, reduce algorithm prescriptions

Use a concise entry contract with three explicit task modes:

* **Placement design:** the model may choose poses, rotations, functional grouping, board-side choices where supported, and candidate strategies within the supplied engineering requirements. Direct pose arrangements and zone/seeder arrangements are supported alternatives.
* **Placement repair:** preserve established mechanical facts and declared intent; use a measured damage target. Recovery-specific HPWL or similarity gates apply only in their justified scope.
* **Verification/handoff:** board/dependency-bound results for connectivity, actual pad/body geometry, mechanical constraints, requirement coverage, and declared tradeoffs. The same final checks apply regardless of placement method.

Require zone coverage **when invoking the zone seeder**, not as a precondition for every placement strategy. For a model-authored arrangement, accept an explicit pose/candidate artifact plus the requirement/provenance data and validate its resulting board. Preserve the existing multi-verb `place_pose.py` transaction capability. Do not force a supported but different arrangement strategy to call its normal operation a waiver of engineering correctness.

Separate candidate exploration from accepted output. A bounded candidate transaction may have an intermediate overlap or longer wire estimate; it must finish with the required geometry checks before promotion. A hard requirement cannot be traded away, but an advisory objective need not improve after every elementary move. Add a first-class experiment mode instead of making the model choose between abandoning a coordinated move and using a broadly named `--force` waiver.

Keep detailed PCB guidance in references keyed by the relevant task/decision. Keep one operative rule, its scope, the evidence it requires, and a short example in the loaded entry/stage. Existing stage ceilings provide a starting point: strengthen them to cover all populated/refusal arms and explicitly review ceiling changes. A file-length cap can guard growth, but cannot establish that shortening improved placements or preserved useful knowledge.

### Refine mechanism 1: absent action is not causal evidence of useless text

“No run acted on this paragraph” identifies a review candidate, not proof it can be deleted or converted into a refusal. A prohibition can be successful precisely because the forbidden action never occurs. A diagnostic explanation may change which pose a model chooses without producing a distinct command. And the repeated L3 advice problem in #963 can be fixed by an equivalent-evidence contract, rather than mandating one exact call/delegation sequence.

Use matched experiments: identical board/dependencies/task/tool versions and comparable budgets, with current instructions versus concise task contract plus on-demand references. Record requirement and geometry results, candidate diversity, accepted/rejected moves, invalid early stops, user-approval pauses, tool calls and measured runtime, and actual model/harness token counters where available. A single run is a pilot, not a general model benchmark. Separate instruction failures from missing tool capabilities and inaccurate checkers.

Useful regression cases include: direct multi-part pose arrangement without invoking a seeder; a recovery task preserving mechanical anchors; a coordinated move requiring a temporary local regression; an HPWL-increasing but requirement-improving final candidate; and the existing Tigard damaged fixture. Every relaxed workflow case needs a negative control showing that real pad collisions, stale scores, or changed fixed geometry still fail final acceptance.

### Existing multi-pose transactions are an enabling capability, not a restriction to remove

The parent also ran deterministic action-granularity controls on three existing boards, then repeated them unchanged:

| Board | Same-footprint pair | Move either part alone into the other's occupied pose | Apply both poses atomically |
|---|---|---|---|
| esp_prog | R3 / R4 | Both refuse, exit 4 | Accept, exit 0, no force |
| flat_hierarchy | R1 / R2 | Both refuse, exit 4 | Accept, exit 0, no force |
| tigard | R1 / R10 | Both refuse, exit 4 | Accept, exit 0, no force |

That is six appropriate single-move collision refusals and three accepted complete arrangements per run. These same-footprint swaps test the action interface, **not a better circuit placement or routability**. The current tool already supports the needed transaction; prose that insists on only one part/parameter or monotonic elementary moves can hide that useful capability.

A separate parent-proposed R4 pose at (140.6,97.4) was correctly refused: the actual pad override requires 1.016 mm clearance and the candidate missed it by .3114 mm. The same target with bounded `--near` legalization accepted (140.6,97.9), .5 mm away, without force; independent pad/assembly checks passed. The exact oracle corrected the model's proposed coordinate while preserving its placement intent. This is a measured example of tool assistance enhancing model choice, not evidence that the model's first proposal should override geometry.

Commands, input/output hashes and raw summaries: `model_placement/confirmed_run/`. The first completed run is corroborating local replication; the confirmed run is the published detailed dataset.

### Actual Astra partial-placement pilot: both chose layouts, but common validation caught a missed edge check

Two fresh-context Astra agents in the Codex collaboration harness received byte-identical copies derived from the repository's esp_prog board: U1/Y1/C2/C4 piled at (128,99.5,0), all other 17 footprint blocks explicitly fixed and locked. Both had eight minutes, at most 20 board-mutating calls, the same named oscillator pad-distance brief, and no routing, force, fixed-part unlock, code changes or access to the original placement/other arm. The current arm could load the current placement skill/driver; the other received a concise tool-and-verification contract and could not load the three planning skills/drivers. Each could inspect tool help/source and render its own board. This is **one partial-placement pilot per arm**, not a blind whole-board reconstruction or a repeated benchmark.

| Observed result | Current placement skill | Concise contract |
|---|---|---|
| Model-chosen U1 orientation | 270 degrees | 180 degrees |
| Board-mutating invocations / reported elapsed time | 4 / 451 s | 2 / 324 s |
| Fixed poses/locks, nets, outline, brief preserved | Yes | Yes |
| Declared Y1.1-to-U1.9 / Y1.2-to-U1.10 gaps | 1.2125 / 3.0465 mm | 2.642551 / 2.245500 mm |
| Explicit study proximity limit, 8 mm | Both pass | Both pass |
| Independent assembly check with original arm baseline | Exit 0, blocking 0 | Exit 0, blocking 0 |
| Identical parent DRC: clearance .25, edge .55, margin 0, pad-edge enabled | **Exit 1: two Y1 edge shortfalls, .05 mm each** | **Exit 0: zero violations** |
| Arm's own close-out | Congestion disposition remains incomplete | Emitted overlap-budget grade remains incomplete |
| Final HPWL / crossings (proxies only) | 233.4564 mm / 40 | 232.5 mm / 39 |

The current arm's initial DRC was reported clean, but its JSON records `board_edge_clearance: 0.0`. The parent reran both frozen candidates with .55 explicitly and found the two edge shortfalls. .55 is the pose tool's reported fallback, **not a fabrication specification or an explicitly preregistered numeric requirement in TASK.md**. No deliberate waiver is inferred. Both candidates keep actual pad copper inside the outline; physical outline containment differs from satisfying a .55-mm inset. This is a concrete example of why “DRC passed” must include effective parameters and coverage. It also prevents mislabeling this edge discrepancy as merely a conservative renderer false positive.

The pilot did not exercise the P1 mandatory-zone path; that source/interface finding is separate. The pose grader also omits `edge_margin` when calling its lower-level legality check, despite displaying .55; #964 documents that additional integration defect. Both agents used the sanctioned multi-pose setter and chose different arrangements. The current skill therefore demonstrably permits model-authored placement in this task. The concise arm needed fewer mutation calls in this sample, but we cannot attribute that to shorter instructions: there is one stochastic trial per arm, their checks/close-out paths differ, and no harness token/cost counters were available. Neither whole-board readiness nor routing quality was established. Body/courtyard coverage is incomplete, inherited fixed advisories remain, and the intentionally loose 8-mm oscillator limit is a study requirement rather than circuit-specific electrical validation.

Independent evaluation compiles only the shared explicit brief, checks invariants, and applies identical final geometry commands; it does not accept candidate-derived budgets as ground truth. Preserve arm reports alongside this audit correction. Publish and repeat this pilot across boards/task modes before claiming a model-performance improvement. The immediately supported fix is a shared effective-rule manifest plus independent final verification, while retaining alternative model-chosen arrangements.

### Additional measured reduction that preserves the instrument

On `tests/fixtures/run23/tigard_placed.kicad_pcb` (SHA `830288017ade8d29ca67614bb07ff9dd2f3b489cfbd5f8c05e7e18b9d653e2c6`), `render_placement.py BOARD --json-out FILE -o IMAGE` returned 36 stdout lines / 8,513 characters and echoed `checklist`; the same call with `--quiet` returned 3 lines / 536 characters and no checklist, while writing the PNG and JSON in both cases. This is measured interface noise removal, not an estimated token or placement-quality gain. The four placement-driver render templates still omit the quiet/review-sheet options despite the refusal text mentioning them.

Both driver self-tests pass; delegation handoff regression reports 25 passed/0 failed. Therefore the changes above need behavioral acceptance tests in addition to existing accuracy checks. Official Astra advice to audit inherited skills and evaluate lighter task-specific instructions supports the experimental direction; it is not evidence of board-level performance by itself: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

Reproducible public evidence: [scripts, command manifests, raw reports and controls](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence/workflow).
