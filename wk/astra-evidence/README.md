# Astra placement evidence, 2026-09-13

This branch preserves a research audit for upstream issues **#959–#965**. It changes no production code, skills, original test boards, or default behavior. The user authorized this study and the issue updates. Three research subagents investigated separate interfaces, two fresh-context Astra agents ran a matched partial-placement pilot, and the parent agent ran action-granularity tests and reviewed the results.

Code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`. Environment: Windows, KiCad 10.0.0, its Python 3.11.5, NumPy 2.4.2. The small route-writer test uses the existing matching `grid_router` 0.22.0 binary; no Rust implementation changed between the user's original checkout and the audited revision. Artifact commits on this branch do not change the code-under-test identity.

## Findings and evidence locations

| Issue | Tested finding | Directory |
|---|---|---|
| #959 | Carried connector metadata does not affect grading; named pin-proximity requirements do. Decap declaration activates two additional rules on the tested fixture. | `requirements/` |
| #960 | Sanctioned model pose is accepted but unrecorded; its provenance audit falsely reports a violation. A bounded destination-guard prototype preserves legitimate poses. | `pose_geometry/` |
| #961 | Real USB footprint overhang is confused with clearance shortfall and a different geometry basis. | `pose_geometry/` |
| #962 | Accepted U2 pose moves graphic copper 1.11 mm outside the board while three repository tools pass. A nearby inward control retains legality. | `pose_geometry/` |
| #963 | Controlled exhaustion declarations survive board replacement; stage advice does not establish current evidence. Final routing-close protection still operates. | `workflow/` |
| #964 | Nested unmeasured assembly checks are absent from top-level coverage; stale budget provenance blocks a zero-overlap control; successful route writer drops a brief. | `requirements/`, `model_placement/` |
| #965 | Crossings contradiction is already corrected and stage-output caps already exist. A live model-choice/zone-seeder conflict remains. Atomic pose arrangements work on three boards. | `workflow/`, `model_placement/`, `pilot/` |

The [matched pilot](pilot/README.md) produced distinct model-chosen arrangements in both arms. Under identical explicit final geometry parameters, the current-skill candidate had two .05-mm pad-edge shortfalls and the concise candidate had zero DRC findings. This is a single exploratory trial per arm, not proof of a performance gain from shorter instructions.

Read each issue addendum for commands, controls, measured values, limitations, proposed changes, and acceptance tests. Sources are the existing esp_prog, flat_hierarchy and Tigard boards, plus the placed/damaged Tigard fixtures and brief fixtures711/902. Original input hashes are recorded in result manifests. A narrow unchanged regression selection was also executed and reported passing (driver/handoff logs are retained; pose/edge test results were captured in the tool session): pose battery 133/133, delegation handoff 25/25, edge-body-seating test, and both driver self-tests. Passing those checks does not establish complete PCB correctness.

## Reproduce without overwriting the recorded evidence

Keep these scripts at `wk/astra-evidence/<area>`; they derive the repository root from that depth. Work from the repository root with KiCad's Python:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/model_placement/run_actions.py --output wk/astra-evidence/model_placement/replay-001
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/reproduce.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/prototype_guard.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/graphic_probe.py
```

The pose scripts create timestamped directories; the action script requires a fresh output directory. For requirements and workflow scripts, copy the scripts to another sibling area at the same directory depth (for example `wk/astra-evidence/requirements-replay`) and run there; the workflow script deliberately refuses to overwrite its existing ledger. These scripts exercise the pinned production code, so rerunning on a different revision tests that revision, not historical results.

`prototype_guard.py` is an isolated runtime experiment, not a production-ready fix. It uses internal interfaces, and its missing cancellation/crash/concurrency/side/sibling cases are documented explicitly.

## Evidence boundaries

- The model pilot is one partial-placement trial per arm, with the same input bytes, four movable oscillator components, 17 fixed footprints, an explicit study brief, and an eight-minute/20-mutation limit. It is not whole-board placement, a repeated benchmark, or a model ranking.
- Exact tool commands, raw reports, proposal refusals, and usage errors are retained. In the parent's exploratory rendering calls, `--review-sheet` was first missing its path, then supplied a JSON path instead of a PNG. The corrected call succeeded; neither failure is counted as a geometry refusal or a renderer success.
- No source board or requirement was relaxed to create a favorable result. Deliberately loose requirements and injected stale ledger/budget data are named as controls, not proposed production settings.
- Some fixtures lack project rules and body/courtyard geometry. Measured fallback floors and coverage gaps are disclosed. A clean pad or assembly check is not an assertion of fabrication readiness.
- Byte hashes bind evidence to its actual files; geometric comparisons, not random output UUID differences, support the action tests. Claims also need relevant project/brief/baseline identity.
- The study supports measurement-backed freedom to choose placement strategies. It does not justify removing engineering checks, treating no-action prose as useless by definition, or shortening routing's enforcement text before those checks have another reliable home.

Generated board variants are generally omitted because the scripts reconstruct them from existing fixtures. The two pilot inputs and final boards are retained to make the model results independently inspectable. The six controlled USB/U2 geometry variants are also retained for inspection. Private boards, credentials, and model hidden reasoning are not included.
