Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

### Evidence update: preserve model-authored placement while fixing provenance

Reproduced on upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`, Windows, KiCad 10.0.0 / its Python 3.11.5 / NumPy 2.4.2. Input: tracked `kicad_files/esp_prog.kicad_pcb`, SHA256 `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`. These are controlled tool-contract experiments with existing board geometry, not an unaided Astra layout benchmark. The source pose is deliberately used as a known-good control, not represented as a newly discovered layout.

I staged this board with the real `tests/stress/stage_unaided.py`, then ran:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 tests/stress/stage_unaided.py kicad_files/esp_prog.kicad_pcb WORK TRUTH
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py WORK/board.kicad_pcb WORK/pose.kicad_pcb set R1 136.4 98.8 --rot 270
```

| Arm | Actual result |
|---|---|
| Sanctioned `place_pose` on the armed pile | Exit 0; `forced=false`, `no_worse=true`; R1 lands at the requested pose |
| Pad metrics | Conflicts 83 → 72; total shortfall 27.1331 → 22.5783 mm; hole conflicts and off-board-pad count remain 0 |
| Provenance after that command | **0 rows**; audit exit **4**, `UNAIDED VIOLATION`, `unclaimed_refs=["R1"]` |
| Same baseline + exact same pose through `write_placed_output` inside declared `place_pose.py` lever | One row; audit **0 / CLEAN**, R1 claimed |
| Undeclared direct writer into the armed directory | `UnaidedViolation` before output creation |
| Undeclared writer into a system temporary directory, followed by real `_promote` into the armed directory | Output created, R1 moved, **zero added ledger rows**, no exception |

The sanctioned action improves the measured pile without claiming the board is finished (`legal=false` is correctly retained). The audit incorrectly labels precisely that legitimate use as a violation. This is a concrete way the skills can constrain a capable model: the model follows the recommended pose setter and receives an authorship failure unrelated to its placement decision.

The production cause remains [external staging at pose_ops.py:638](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/pose_ops.py#L638), [destination-based early return in record_write](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/provenance.py#L223), and [promotion without provenance](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/pose_ops.py#L939).

### A tested direction that preserves freedom

I also tested an **isolated runtime prototype**, without changing production files: validate provenance against the final destination before promotion; derive the ledger poses from the final candidate; use `record_write(..., pending=True)` before promotion and `commit_write` after successful promotion. The guard does not decide coordinates or require an optimizer to have selected them.

| Prototype arm on the same real board | Result |
|---|---|
| Registered model pose | Accepted, exactly one ledger row, audit CLEAN |
| Registered model pose + lock in the same transaction | Accepted, one row, audit CLEAN; ledger SHA matches final bytes after lock stamping |
| Dry run | No output, no ledger row |
| Off-board geometric refusal | `PoseRefusal`, no output, no ledger row |
| Undeclared pose | `UnaidedViolation`, no output, no ledger row |

This establishes feasibility, **not a production-ready patch**. The prototype needs a public cancel-pending API, exact handling of side changes, crash recovery, concurrency, sibling-file failures and all snap branches before adoption.

Simply staging beside the output deserves care: rejected trial candidates could then acquire ledger entries; lock stamping can change the final hash after the writer records the candidate; snap candidates can differ from the requested coordinates. A final promotion boundary can distinguish `candidate evaluated`, `candidate accepted`, and `board committed` explicitly. Recording only after copying would restore accounting but would still make an undeclared-write refusal too late.

### Make the authorship claim precise for Astra/Codex

Keep **decision provenance** separate from **execution provenance**: e.g. `decision_source=model` with `applied_by=place_pose.py`, alongside model/harness identifiers where available. A registered application tool is not evidence that its optimizer chose the arrangement. Explicit model-chosen poses are an intended capability here and should remain first-class.

The unaided engine-only regime is a benchmark claim. An ordinary placement task may legitimately use another checked adapter; it should be disclosed as such rather than conflated with engineering invalidity. Do not weaken the geometric requirements to fix an authorship bug, and do not restrict model pose selection to hide the missing ledger.

### Expanded acceptance

1. Sanctioned `set`, `rotate`, `face`, multi-pose, lock/unlock, snap and in-place outputs reconcile to the **final** board, including the accepted pose and final SHA.
2. A refused candidate, dry run or failed promotion creates no successful-commit row and preserves the previous deliverable and siblings.
3. An undeclared promotion into an armed destination refuses **before publication**, even when its temporary file is outside the regime.
4. The exact improving-pile move above remains available without `--force`; inherited defects still do not become an absolute placement gate.
5. Ordinary model-assisted work and engine-only benchmark attribution have distinct, truthful labels.

Evidence artifacts in the audit package: `pose_geometry/reproduce.py`, `run-20260913-222129/results.json` plus command logs; `prototype_guard.py`, `guard-20260913-222230/results.json`. The source board was preserved.
