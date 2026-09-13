Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

## Reproduction on the current upstream revision, and implications for Astra placement

Tested upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3` on Windows with KiCad 10.0.0's Python 3.11.5 and NumPy 2.4.2. These are deterministic tool and declaration experiments on repository boards, not an Astra-vs-other-model benchmark. No production source or original board was modified. Full commands, output, and JSON are in the linked evidence bundle's `requirements/` directory; run `reproduce.py` with the KiCad Python from the repository root.

### 1. Declaration controls confirm a real coverage boundary

Input: `kicad_files/esp_prog.kicad_pcb` and the existing `tests/fixtures/711/esp_prog.design-brief.json`. Emit with `check_floorplan --declare-classes --brief ...`; grade the emitted intent with `--require-brief-coverage --require-rules 1`.

| Controlled change, same physical board | Rules run | Brief graded / carried / unknown | Brief drift | Coverage complete | Errors / warnings |
|---|---:|---:|---:|---|---:|
| Existing fixture, default emission | 6 | 8 / 8 / 3 | 0 | true | 5 / 3 |
| Add `--declare-decaps` at emission | 8 | 8 / 8 / 3 | 0 | true | 5 / 4 |
| Keep the original intent; change USB1 `mount_mode` and `cable_entry`, plus `product.user_top_side`, in the brief | 6 | 8 / 8 / 3 | 0 | true | 5 / 3 |
| Keep the original intent; change USB1 edge east → west in the brief | 6 | 8 / 8 / 3 | 1 | false | 5 / 3 |

The board has existing fixture violations, so the first three cases all exit 4 already. The evidence is the controlled equality/difference of the measurements and coverage fields, not a claim that this board passed. The edge-change control shows that brief drift detection does work for a compiled field. The carried-field change shows exactly which facts it does not evaluate. `brief_clauses=19` includes three declared-unknown clause rows; `brief_declared=16`, not 19. Eight carried rows are visible, but `brief_coverage_complete=true` deliberately excludes them from completion.

There is also a correction to the proposed decap fix: **`--declare-decaps` arms two additional rules on this fixture, not three.** It adds `decap_distance` and `decap_ungraded`; `decap_pin_distance` remains skipped because no `decaps.max_pin_distance_mm` was declared. The emitter observes four candidate caps, three tethers, and C1 beyond the 5 mm search radius. The warning becomes visible when declaration is enabled, which is useful, but a board-derived limit that grades clean by construction is a regression baseline, not evidence that a circuit-specific electrical requirement is met. [Flag semantics](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_tools/check_floorplan.py#L88)

### 2. An existing named-relationship channel gives a better model-facing contract

Second input brief: the existing `tests/fixtures/902/esp_prog_proximity.design-brief.json`, on exactly the same board. This explicitly names the crystal pins, regulator/cap relationships, and transistor pair. Four expanded proximity clauses are graded. The measured failures are:

| Requirement | Measured gap | Declared maximum |
|---|---:|---:|
| C1 pad 1 → U2 pad 2 | 4.4111 mm | 2 mm |
| Y1 pad 1 → U1 pad 9 | 4.7425 mm | 2 mm |
| Y1 pad 2 → U1 pad 10 | 2.5220 mm | 2 mm |

This grade has three errors and exits 4. As a negative control, setting all four limits to 100 mm in both the intent and brief, without touching the board, yields zero errors and exits 0. That intentionally loose control is not a recommended design limit. It proves the findings respond to the declared relationships and their limits. It also demonstrates why explicit C1/C3 → U2 intent adds information beyond generic tether discovery: the fixture documents that U2 has three pads and cannot be elected by the generic IC tether criterion.

For Astra, this is an enabling interface: return the exact measured failing relationship and let the model choose which poses, rotations, and functional arrangement to change. The validator need not prescribe a seeding order or a particular optimizer. A model's alternative placement should satisfy the same real requirements, regardless of which strategy produced it.

### 3. Proposed changes, with safeguards against turning incomplete knowledge into artificial restrictions

1. **Build a declaration coverage ledger before placement.** Each requirement needs an identity, authority/source, compiled geometric/electrical consequence where supported, responsible grader, and disposition. Distinguish graded-pass, graded-fail, carried-context, unmeasured, unknown, and explicitly inapplicable. A count of rules or `coverage_complete` that excludes carried fields is insufficient for a claim of full design compliance.
2. **Expose inference as inference.** Default-on decap discovery/census is helpful. Activating a baseline-derived budget must also say that it preserves an observed distance rather than validates electrical adequacy. Show inferred partner elections and allow the model to replace them with declared, pin-specific relations from the circuit requirements. A missing inferred tether must not prohibit an explicitly justified placement.
3. **Compile connector consequences only with sufficient geometry.** `user_top_side` is the user's viewing face, not necessarily the assembly face. `cable_entry: perpendicular_top` does not specify cable dimensions, insertion travel, or a z-height envelope. Automatically inventing a 2D keepout or forcing every user-facing part onto one face would constrain legitimate boards without evidence. Compile a supported declared envelope; otherwise show what physical dimension is missing and keep it visible for review. Do not report a metadata label as a validated physical claim.
4. **Make conflicts actionable before pose writes.** Reconcile actual authoritative inputs, showing both values and their sources. Conflicting user/mechanical requirements may need clarification; a model-generated working hypothesis does not acquire equal authority merely by being serialized. Avoid a universal 'every dark rule is fatal' gate: an unused rule needs a machine-readable applicability reason, and advisory/irrelevant dimensions should not prevent legitimate exploration.
5. **Validate candidate outcomes independently of the chosen placement method.** Let Astra propose direct poses, group arrangements, alternative seeding, and bounded repair experiments. Freeze actual mechanical invariants; preserve best accepted candidates; check declared proximity, side, keepout, clearance, and connectivity on each candidate promoted for delivery. This supplies measurements the model cannot obtain by prose reasoning alone without obligating it to follow one search trajectory.

### Additional acceptance tests

- Existing fixture711 field-change and edge-change controls above remain distinguishable; top-level completion names carried design facts and never implies they were physically checked.
- Fixture902 gives the recorded three failures at the stated 2 mm limits and zero at the deliberately loose control, with the same input board hash.
- A declared pin-specific relation to a three-pad regulator is graded even when generic decap tether discovery does not elect that regulator.
- Every automatically chosen budget reports 'observed regression baseline' vs 'declared design requirement'; changing an inference does not silently weaken a declared requirement.
- Connector geometry is not fabricated from enums. Unsupported z/insertion constraints remain explicitly unmeasured.

### Reproduction identity and scope

- esp_prog SHA256: `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.
- Fixture711 SHA256: `c1869c27b552e71d4f0a4c2ba8887c252f092c8ab17b5d9f2bb212a5531df26a`.
- These tests establish declaration/measurement behavior. They do not establish superior routability, successful manufacturing, or an improvement in Astra's task completion rate. Those require separate placement/routing and repeated model-run experiments.
