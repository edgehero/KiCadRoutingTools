Partial-placement research task. Arrange U1, Y1, C2 and C4 from their
stacked starting position into a legal, sensible oscillator subassembly. Keep
every other footprint at its input x/y/rotation/layer and retain its lock.
Preserve outline, netlist, pads, layers and electrical rules. Remain on the
existing front side. Respect board.design-brief.json; its 8mm named oscillator
pad-distance ceiling is a controlled study requirement, not a production spec.
Use connectivity and component/pad context to choose poses; don't consult the
original board or other arm. Use exact geometry checks plus visual inspection.
Write final.kicad_pcb and a concise RETURN.md with decisions, all mutations,
validation results, unsatisfied/unmeasured requirements and elapsed time.
You have a bounded 8-minute research trial and at most 20 board-mutating tool
invocations; stop at that boundary and report incomplete work honestly. Read-only
measurements are allowed. Do not route, change production code, waive checks,
change design constraints, use --force, unlock fixed parts or ask the user to
approve intermediate work. Work on your arm's copies. Each CLI can run at most
60 seconds. Do not spawn agents. You may read repository tooling, help and skill
files as specified for your arm, but never kicad_files, tests/fixtures, another
arm, preparation, truth, or earlier research artifacts. The only board input is
the board.kicad_pcb inside your arm directory. This is a partial placement pilot,
not a blind whole-board or fabrication-readiness benchmark.
