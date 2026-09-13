Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

## Current-revision controls: incomplete verification risks false confidence and policy-dependent placement stops

Tested upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`, Windows, KiCad 10.0.0 Python 3.11.5, NumPy 2.4.2. The linked evidence bundle's `requirements/` directory contains `reproduce.py`, `mechanical_probe.py`, exact subprocess argv/exit codes in JSON, all raw stdout/stderr, emitted intents, and grades. These controlled tool tests use existing repository boards; they are not a full Astra benchmark.

### Routing output drops the brief: actual writer test

The independent placement experiment also staged esp_prog with its existing fixture711 brief sibling and routed the real net `Net-(Q2-Pad1)`. `route.py` exited 0, completed one route with no failed/open routes, and wrote its board output, but the output brief sibling was absent. The `copy_board` control on the same staged input retained the brief. This exercises a successful routing writer, not a simulated file copy. Full command and stdout: `model_placement/confirmed_run/commands.json`, `brief_route.stdout.txt`; result: `results.json -> brief_writer`. The brief's SHA256 is `c1869c27b552e71d4f0a4c2ba8887c252f092c8ab17b5d9f2bb212a5531df26a`. This directly reproduces item 1 for `route.py`; it does not by itself establish the behavior of `route_diff.py` or `route_planes.py`.

**Change:** make every final writer preserve the canonical requirement-sibling set, with a post-write equality check for copied declarations. Validate the next output against those declarations, and refuse a completion claim if an input requirement disappears from its artifact set. `brief_absent == 0` is insufficient as an acceptance condition: the no-brief control in this bundle also reports `brief: null, brief_absent: 0`, because that counter tracks undeclared fields within a found brief. Require the expected sibling/hash or an explicitly referenced brief identity instead.

### A. Nested unmeasured assembly check does not reach top-level `ungraded`

Run `board_score.py kicad_files/esp_prog.kicad_pcb --intent <emitted-intent> --json score_esp.json --quiet`.

Observed:

```json
{
  "ungraded": ["impedance", "length", "net_widths"],
  "unknown": [],
  "components.assembly.buildable": true,
  "components.assembly.verdict": "buildable (blocking 0)",
  "components.assembly.conjuncts_unmeasured": ["courtyard_blocking_gating"],
  "components.assembly.courtyard_gating_armed": false
}
```

The missing assembly check is omitted from the top-level list. Unlike the original run-29 evidence, this test does not produce an empty `ungraded` list: the three unrelated optional checks were intentionally not requested. The reproduced defect is the missing nested entry. The overall score exits 4 for other findings; this experiment does not claim an overall falsely passing board.

Positive control: `check_assembly.py <same-board> --baseline <same-board> --json assembly_baseline.json` yields `courtyard_blocking_gating: 0`, `courtyard_gating_basis: "moved-vs-baseline"`, and exits 0. The check exists and can be armed. Using the same board as baseline proves activation, not that a moved component would be safe. The scorer has no `--baseline` option and explicitly records that it never supplies one. [Aggregation](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/.claude/skills/plan-pcb-placement-and-routing/scripts/board_score.py#L1179)

**Change:** accept/forward the actual starting-board baseline, propagate component subchecks to qualified top-level entries such as `assembly.courtyard_blocking_gating`, and print the unarmed check plus the activating argument in the verdict. Baseline choice must be recorded and bound to the run; an agent must not replace it with its latest candidate to make moved-vs-baseline checks disappear. Keep baseline-relative checks separate from absolute manufacturing constraints: a pre-existing defect is not automatically acceptable.

### B. Controlled stale overlap provenance blocks an unchanged zero-overlap board

On `kicad_files/flat_hierarchy.kicad_pcb`, emit an intent. The board's measured overlap is zero. To isolate the issue, remove only `legality_budget.overlap_area` and insert `context.budget_withheld.overlap_area = "83 blocking body pair(s) on the emitting board (controlled stale provenance)"`. No board geometry is changed. This is explicitly an injected stale-provenance control, not a replay of the original 83-pair pile.

| Same board, same intent except one budget field | Measured overlap | Errors / warnings | Budget abstained | Complete | Exit |
|---|---:|---:|---:|---|---:|
| Stale withheld note, overlap budget absent | 0.0 mm² | 0 / 0 | 1 | false | 4 |
| Explicit `legality_budget.overlap_area = 0.0`; historical note retained | 0.0 mm² | 0 / 0 | 0 | true | 0 |

Five rules run in both cases. The existing `_declared_by_hand` path correctly makes the historical note nonbinding when a budget is explicitly supplied. This confirms an available recovery path and a policy-dependent stop when it is not supplied. This control alone does not establish that automatically accepting zero overlap was authorized by the original task. The source initializes abstentions from the historical intent before grading; it does not retire that overlap abstention after observing zero overlap. [Current code](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/floorplan.py#L4135)

**Change:** preserve the withheld note as provenance, but separately report the current measurement and whether the missing budget has become resolvable. A zero-overlap recovery can arm an explicit zero-overlap baseline according to a documented policy; positive overlap must not auto-convert into an accepted budget. Keep measurement semantics explicit: courtyard/body overlap and copper clearance are different checks, and zero in one channel does not prove the others. If user action is actually needed, print the precise existing remedy instead of a generic exit 4. An unresolved engineering violation must remain a failure; a stale derivation failure should not train Astra to ignore all exit-4 results.

### C. A separate mechanical file is invisible, but the proposed `must_lock` shortcut needs revision

On a copy of esp_prog with the existing fixture711 sibling brief, emit an intent with `mechanical.json` absent. Add a deliberately incompatible synthetic `mechanical.json` declaring USB1 west while the brief says east, C1 fixed at (0,0), and a 0.4 mm clearance floor; emit again. Both commands exit 0 and produce **byte-identical intent files**, SHA256 `a8bdb1bc1587b95008c8fb80f1dd41e6b014bb756a8aabb824db9a236763ea57`; both report `context.brief.contradictions: []`.

The placement intent emitter/grader does not recognize this adjacent file as a requirement input. The synthetic contents do not test a supported mechanical schema. This is not a claim that the entire repository has no mechanical consumer: `tests/stress/stage_unaided.py` has its own `read_mechanical` parser and schema. The missing integration is with placement requirement compilation and grading.

However, **do not simply compile every fixed mechanical reference into current `must_lock`.** The source documents a previous loop where `place_seed --repair` treated `must_lock` refs as seeder-owned and lifted their locks. It explains that a lock-at-finish requirement is not an immutable pose requirement. [Compiler rationale](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/design_brief.py#L986), [emitter rationale](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/floorplan.py#L4854). This historical behavior was not separately reproduced here, so treat it as a source-grounded design warning.

**Change:** define a canonical mechanical requirement input with pose coordinates, rotation, side, tolerance, unit system, and authority/provenance. Preserve/validate immutable pose invariants independently of lock bits. Compile clearance floors into the actual project/rule resolution used by tools, not just an unrelated JSON default. Reject or explicitly reconcile authoritative conflicts before a candidate is accepted. Also distinguish a model-authored proposal from a user-declared mechanical fact; otherwise Astra's own temporary choices become accidental permanent constraints.

### D. The live placement pilot found a displayed rule floor that the pose grader does not consume

This is an additional placement-specific instance of the issue's central problem. In the current-skill partial-placement pilot, `place_pose` displayed `board_edge_clearance: 0.55` and returned `legal:true`. The arm's separate DRC command omitted its edge flag and reported zero findings at its recorded default of **0.0 mm**. The parent's identical final audit of both pilot candidates explicitly supplied clearance .25, edge .55 and margin 0 with pad-edge checking enabled. It found **two Y1 pad-edge shortfalls of .05 mm** on the current-skill candidate; the concise-contract candidate had zero findings under that same command.

Native KiCad confirms the physical measurement: the affected Y1.2 and Y1.3 pads end at Y=105.0 against the outline centreline Y=105.5, a .50-mm gap. This is insufficient for .55 but does not put copper outside the board. Source inspection explains the actor discrepancy: [pose_ops.grade](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/pose_ops.py#L358) calls `grade_pad_legality` without `edge_margin`; the lower-level gate uses the .25-mm clearance instead. Separately, [check_drc's CLI default](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_router/check_drc.py#L3762) is zero. A displayed/resolved parameter and a measured parameter are not currently the same guarantee.

The .55-mm floor was chosen for this **post-hoc common audit from the actor's reported fallback**. TASK.md did not preregister that number, and it is not a fabrication specification. No deliberate waiver or user-rule violation is inferred. The one-trial-per-arm result does not establish that shorter instructions caused better placement; #965 documents the balanced pilot results. Evidence: `pilot/evaluation-final/`, `pilot/native_edge_audit.py`, `pilot/native_edge_audit.json`, and both original arm reports.

**Change:** resolve effective requirements once into a typed rule manifest and pass them explicitly to every relevant measurement, including the pose grader. Each result should report requested value, effective value, source, units, and check coverage. Add a boundary regression that distinguishes actual off-outline copper from a .50-mm inset failing an explicit .55-mm floor. This corrects the instrument while leaving Astra free to choose another compliant pose.

### Proposed acceptance additions

- Top-level coverage includes every nested unmeasured component check, using qualified identities; preserve unknown, unrequested, inapplicable, and failed states separately.
- The scorer accepts a genuine initial-board baseline and forwards it; the baseline identity is recorded with the score.
- Flat_hierarchy stale-provenance control remains incomplete until the declared zero-overlap policy or explicit recovery resolves it; positive-overlap control cannot be silently accepted.
- The mechanical parser has positive/negative tests for pose drift and rule-floor conflicts. A mechanical-fixed footprint cannot be unlocked or moved by repair, even if also present in `must_lock`.
- Requirements, effective project rules, brief, and baseline hashes travel with the board and score. A board hash alone cannot bind the verification claim because sibling declarations affect its meaning.
- A rule floor displayed by the actor is actually passed to its grader; the same explicit rule manifest yields consistent edge-clearance results in placement and final DRC. Any intentionally different geometry/check scope is named.
- Record model-authored intent and pose files in an artifact manifest with their producer and role. A shell command log is a command log, not a complete authorship ledger; legitimate direct JSON/pose authoring should be supported and auditable.

### Scope / input hashes

- esp_prog SHA256: `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.
- flat_hierarchy SHA256: `f756cec11151f79a9c8fe7123089130ad166f5abfd6d5f4d59aaf828b08eb05a`.
- These controls address items 1–4 and artifact provenance implications. They do not reproduce the original run29 outputs, prove a routability improvement, or establish a model performance gain.
