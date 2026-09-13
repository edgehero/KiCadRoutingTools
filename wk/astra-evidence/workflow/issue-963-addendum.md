Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

## Follow-up: reproduce evidence gaps, enforce evidence rather than one agent topology

Tested at **5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3**, Windows, KiCad 10 Python 3.11.5. This is a bounded tool/driver reproduction on the repository's existing Tigard fixtures, not a replay of run 29 and not a measured Astra-versus-other-model benchmark. The ledger declarations below are explicitly marked AUDIT TEST; they are inputs testing validation, not actual claims that placement or routing was exhausted.

### Existing-board measurements

`board_score.py BOARD --placement-terms --json SCORE` produced:

| fixture | board SHA-256 | blocking | copper |
|---|---|---:|---:|
| `tests/fixtures/run23/tigard_placed.kicad_pcb` | `830288017ade8d29ca67614bb07ff9dd2f3b489cfbd5f8c05e7e18b9d653e2c6` | 85 | 0 segments |
| `tests/fixtures/run23/tigard_damaged.kicad_pcb` | `36ef90f7d6db76c16962aa3b9dcd1ca7497d4ae7148cae9f9530cbb26135ff02` | 261 | 0 segments |

Both sibling `.kicad_pro` files hash to `a98a45e0a8a0e864c1c9f62c81699744f212441deefd00049377487802c8712b`. These are intentionally unrouted placement fixtures: blocking is not a PCB readiness verdict. Both scores explicitly leave floorplan, impedance, length, and per-net widths ungraded.

### Reproduced behaviors and controls

1. Record a fixture row with `converge.py record --kind completion --score-file ...`, then invoke `loop_driver.py --stage L5` twice against its matching board/score/ledger, with no L3 or L4 event. **Both calls return exit 0 and CONTINUE instructions**, including the next L3 command. This confirms the advice-only branch. No router was run in this test; the completion row is a controlled input exercising the same ledger shape. The positive control `--stage L4` with no `--shape` returns exit 4.
2. Record `--kind systemic --exhausted placement` and `--exhausted routing` on the placed fixture, each with a nonempty AUDIT TEST reason. Record the damaged fixture as a new systemic board replacement. Run `converge.py verdict` with the **fresh, matching damaged-board score**. **Both halves remain `declared-exhausted`, and the verdict is STUCK at blocking 261.** The declaration is invalidated by a subsequent placement lap, but not by this changed-board/systemic row. Control: recording one actual `kind placement` ledger lap on the damaged fixture changes placement to `declared_superseded`, `flat:false`, `too-few-laps`, and CONTINUE.
3. Important correction to “as `--score-file` already is”: `record` carries the score's SHA and **warns**, but does not always refuse a mismatch. Attaching the placed score to the damaged board with `--kind systemic --score-file` returned exit 0 and recorded `accepted:true`, with `record WARNING: score payload grades a DIFFERENT board` on stderr. In contrast, **L5 with that stale score refuses at exit 4**. These are different enforcement strengths.
4. The L5 changed-board test does **not** prove that shipping bypasses every check: L5 refuses the missing `--routing-close`. Preserve that boundary. The demonstrated defect is stale exhaustion influencing the stop verdict, not a delivered clean-board claim.
5. Render the placed fixture with `render_placement.py BOARD --json-out FILE -o IMAGE`: exit 0, **36 stdout lines / 8,513 characters**, including `checklist`. Add `--quiet`: exit 0, **3 lines / 536 characters**, no checklist on stdout. Paths contribute to character counts; these are character counts, not tokens. Both PNG/JSON pairs are written. The four placement-driver templates at lines 522, 629, 1300, and 1603 still omit the relevant quiet/review-sheet flags. This proves avoidable checklist disclosure; it does not quantify model bias or visual-review accuracy.
6. `tests/test_890_delegation_handoff.py`: **25 passed, 0 failed**. `loop_driver.py --self-test`: **exit 0, OK**. Existing tests pass while the behaviors above remain observable.

### Refine the proposed fix for Astra/Codex placement

The essential requirement is current evidence for a decision. Requiring an exact L3 invocation plus a new prompt filename can detect the original failure, but it can also reject a model that performs equivalent diagnosis inline or uses another harness's agent mechanism. A stage invocation alone also does not prove that its emitted commands ran.

Use a **board-bound decision record** at the retry boundary:

* Board and relevant dependency digests, candidate/parent IDs, observed blocker IDs, scoped affected refs/nets, hypothesis, evidence paths and hashes, chosen action, and experiment budget.
* Default L3/L4 commands should produce/validate this record. A Codex agent, an inline execution path, or another analysis tool can supply an equivalent record under the same schema/checks.
* Refuse promotion or exhausted/terminal claims when required measurements are missing, stale, or contradictory. Explain the missing fact and offer the command that can establish it. Do not require a fresh worker merely to repeat already current evidence.
* Bind exhaustion to the board and relevant project/intent dependencies; report which changed input invalidated it. A safe initial implementation invalidates on any digest change. Later scope-aware reuse must explicitly prove unchanged dependencies. Distinguish “no improvement within this bounded search” from “no geometrically feasible placement exists.”
* Represent multi-step placement/routing experiments separately from the best accepted board. Preserve the accepted board, allow a bounded candidate to worsen temporarily, measure the completed candidate, and promote only if it satisfies the declared engineering acceptance conditions. Unaccepted intermediate states must never satisfy completion or become the next baseline by accident.

This matters because L4 currently commands “Change ONE parameter” and the combined skill says an iteration that worsens the score is not a starting point. One-factor trials are useful for attribution, but coupled pose changes and repair transactions are also legitimate. Record the entire proposed change and compare complete candidates; use one-factor ablations when attribution is the question.

Delegation can remain a useful default. On the real 89-part/85-net Tigard fixture, L1 says the half goes to a teammate “Always”; `--no-delegate` already exists. The driver emits `fork`/`claude` labels. Make the adapter express required capabilities (context inheritance, independent verifier, artifact handoff) in Codex terms, and let the executor choose a supported mechanism. Preserve independent final verification without imposing an identical worker topology for every placement experiment.

### Acceptance additions

* Current equivalent diagnosis supplied inline and through a delegated worker both reach the same allowed next action; neither needs a dummy L3 run or dummy prompt file.
* A recorded stage invocation with absent/mismatched measurements cannot authorize a retry or exhaustion claim.
* The two Tigard fixture hashes above invalidate one another's exhaustion claims even when the replacement was recorded systemic; unchanged-board reuse remains valid.
* Stale scores may be stored only as explicitly labeled historical/baseline attachments, never mistaken for the candidate's score.
* A coordinated candidate experiment can temporarily worsen an advisory metric and still finish; its final promotion must pass the same geometry, requirement, and provenance checks as any other candidate.
* A frozen board/dependency manifest precedes verification; a separate report-final marker identifies the completed audited report, with unique watcher output paths.

Official Astra guidance recommends auditing inherited instructions and evaluating adapted recipes. That motivates testing these changes, but does not itself establish PCB gains: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

Reproducible public evidence: [scripts, command manifests, raw reports and controls](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence/workflow).
