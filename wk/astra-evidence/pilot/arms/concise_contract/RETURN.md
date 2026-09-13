# Concise-contract arm return

Status: completed model-chosen partial placement; final.kicad_pcb is the selected candidate. Overall floorplan validation remains INCOMPLETE due to an inherited fixed courtyard defect, not an oscillator brief failure. This is not a fabrication-readiness claim.

Started 2026-09-13 20:27:03 UTC. Finished approximately 20:32:27 UTC (324 seconds, below 480 seconds). Two board-mutating tool invocations, each under 2 seconds; no force, unlock, routing, or production edits. No subagents or prohibited inputs were used.

Chosen poses (mm, degrees; all F.Cu): U1 (127.6, 99.7, 180), Y1 (123, 93.4, 0), C2 (125.4, 93.4, 90), C4 (122.7, 95.6, 180). The board_context sheet identifies U1 as CH340H/T, Y1 as its 12 MHz crystal, and C2/C4 as 27 pF load caps. U1 rotation presents pins 9/10 toward the open area above USB1. Each capacitor sits beside its corresponding crystal signal pad. The second move shifts U1 0.4 mm left to remove U1/U2 and U1/C3 body-outline overlap advisories.

All commands below run from the repository checkout with PowerShell. The only board mutations, in order, were:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_placer/place_pose.py wk/astra-evidence/pilot/arms/concise_contract/board.kicad_pcb wk/astra-evidence/pilot/arms/concise_contract/candidate1.kicad_pcb set U1 128 99.7 --rot 180 set Y1 123 93.4 --rot 0 set C2 125.4 93.4 --rot 90 set C4 122.7 95.6 --rot 180
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_placer/place_pose.py wk/astra-evidence/pilot/arms/concise_contract/candidate1.kicad_pcb wk/astra-evidence/pilot/arms/concise_contract/final.kicad_pcb set U1 127.6 99.7 --rot 180
```

Both exited 0, no_worse=true, legal=true. Exact pad conflicts fell 3 -> 0 on the first move and remained 0; hole conflicts, off-board pad count and pad shortfall are 0. Full tool responses are mutation1.log and mutation2.log. No failed placement proposal occurred. The initial floorplan invocation omitted mandatory --intent/--emit-intent, returned usage error without grading, and was corrected by compilation below. Original board.design-brief.json was copied unchanged to candidate1.design-brief.json and final.design-brief.json.

Final validation commands:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_tools/check_floorplan.py wk/astra-evidence/pilot/arms/concise_contract/candidate1.kicad_pcb --emit-intent wk/astra-evidence/pilot/arms/concise_contract/intent1.json --require-brief --require-brief-coverage
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_tools/check_floorplan.py wk/astra-evidence/pilot/arms/concise_contract/final.kicad_pcb --intent wk/astra-evidence/pilot/arms/concise_contract/intent1.json --require-brief --require-brief-coverage --require-rules 1 --json wk/astra-evidence/pilot/arms/concise_contract/floorplan-final.json
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_tools/check_assembly.py wk/astra-evidence/pilot/arms/concise_contract/final.kicad_pcb --baseline wk/astra-evidence/pilot/arms/concise_contract/board.kicad_pcb --json wk/astra-evidence/pilot/arms/concise_contract/assembly-final.json
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_router/check_drc.py wk/astra-evidence/pilot/arms/concise_contract/final.kicad_pcb --clearance 0.25 --board-edge-clearance 0.55 --check-pad-edge --json wk/astra-evidence/pilot/arms/concise_contract/drc-final.json
& 'C:/Program Files/KiCad/10.0/bin/python.exe' py_tools/render_placement.py wk/astra-evidence/pilot/arms/concise_contract/final.kicad_pcb --before wk/astra-evidence/pilot/arms/concise_contract/board.kicad_pcb --side F --no-ghosts --no-arrows --no-delta-first --ratsnest-nets 'Net-(C2-Pad1)' 'Net-(C4-Pad1)' -o wk/astra-evidence/pilot/arms/concise_contract/final.png --expect-moved 4 --json-out wk/astra-evidence/pilot/arms/concise_contract/render-final.json --quiet
& 'C:/Program Files/KiCad/10.0/bin/python.exe' wk/astra-evidence/pilot/arms/concise_contract/audit_final.py
```

Results:

- Exact DRC: exit 0, no violations at 0.25 mm copper and 0.55 mm board-edge clearance, with pad-edge checking enabled. These match placement-tool fallback floors; the input declares no project/netclass rules. No electrical rules were added or changed.
- Assembly: exit 0, blocking 0, new advisories versus original 0, advisory 7. One inherited Ref*~2/USB1 courtyard intersection remains (1 mm2, depth 1 mm); both members are fixed. C3/U1 courtyard advisory is 0.2611 mm2. The tool's baseline-relative buildable verdict does not mean all courtyards are clean.
- Floorplan: tool exit 4, 4 rules run, 0 violations, complete=false/pass=false because overlap_area auto-budget abstains on the inherited courtyard intersection. The named oscillator brief clause is graded, with zero uncovered, abstained or drifted brief clauses. product.form_factor is carried, not graded. No budget/constraint was waived or edited.
- Independent exact rectangular-pad calculation: Y1.1 -> U1.9 = 2.642551 mm; Y1.2 -> U1.10 = 2.245500 mm. Both satisfy 8 mm. C4.1 -> Y1.1 = 0.635444 mm and C2.1 -> Y1.2 = 0.561595 mm. Capacitor-to-U1 corresponding signal distances are 1.704500 and 1.319209 mm. Actual pad shape/orientation and matching nets are asserted by audit_final.py; results are in invariants-and-distances.json.
- Preservation: all 17 fixed footprint blocks byte-identical, locks retained; only C2/C4/U1/Y1 changed, all layers preserved. Non-footprint board data is byte-identical, including outline and rules. Movable local pad/footprint geometry is unchanged; only poses and required global pad/text angles rotate. The independent audit passed.
- Visual inspection: viewed before.png, candidate1.png, final.png. Final oscillator parts are separated, inside the outline, with short signal airwires. The remaining render warnings concern fixed geometry: Ref*~2/USB1 courtyard overlap and a conservative pad-conflict marker at the right connector/fiducial region. Renderer/floorplan show one pad pair with 0.066 mm shortfall while exact place_pose/assembly/DRC checks show none; this instrument discrepancy is retained, not declared repaired. Final render reports exactly four moved parts, no off-board pads, HPWL 232.5 mm and 39 crossings versus initial 250.7 mm and 52 crossings.

Coverage limits: 18 footprints have no courtyard and use pad-box fallback; body checking covers 14/21 footprints, with silk fallback for U1 and others. Physical assembly cannot be fully certified from those sources. Load-cap grounding/return-current layout, routed oscillator length, routing feasibility and signal integrity remain unmeasured; this trial is placement only. Native KiCad DRC was not run. The unchanged duplicate Ref* references and inherited fixed defects remain. final.kicad_pcb is a valid bounded placement result with those reported limitations, not a globally clean board.

