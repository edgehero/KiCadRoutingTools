# Matched partial-placement pilot

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

## Inspect and reproduce

Inputs, task sheets, selected final boards and returned reports are under `arms/`. The concise arm also has `CONTRACT.md`; current instructions are the placement skill and driver at the pinned code revision. `protocol.json` records input identity and budgets. `evaluation-final/results.json` and raw per-command outputs are the parent's common evaluation. The current arm's own original `drc-final.json` is intentionally retained to show the effective-floor difference.

Run `evaluate_pilot.py --output <fresh-directory>` with KiCad Python to recheck the stored candidates. To prepare a new trial, copy `setup_pilot.py` into a fresh sibling area at the same directory depth before running it; it refuses an existing pilot directory. Replaying recorded mutations reproduces the chosen candidate, not an independent model trial. Actual repeated model trials must start fresh agents with the same respective TASK/CONTRACT access conditions.
