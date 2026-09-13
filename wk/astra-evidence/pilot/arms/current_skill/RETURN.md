# Current-skill placement pilot

Status: incomplete placement candidate in `final.kicad_pcb`; independent audit found two 0.55 mm edge-clearance violations, and current-skill close-out remains incomplete (congestion disposition gate). No routing, force, unlock, waiver, production edit, or subagent was used.

Started 2026-09-13 20:26:48 UTC. Completed 20:34:19 UTC: 451 seconds, within 480 seconds. Four board-mutating tool invocations, all under 60 seconds.

The model chose U1 rotation 270 degrees to put its USB pins toward fixed USB1 and its oscillator pins at the lower left. Y1 sits below those pins; C4 and C2 flank its corresponding oscillator nets. Exact pad-clearance feedback moved U1 away from U2/C3 and C4 away from U1. Final poses (mm, degrees): U1=(126.6,97.75,270); Y1=(124.7,103.2,270); C2=(126.9,103.5,90); C4=(122.4,102.2,90). All remain front-side.

## Exact board mutation commands

Run from the repository root of this audit checkout. These are the complete four invocations, in order; the tool's printed angles may normalize to equivalent -90 degrees in KiCad.

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py wk/astra-evidence/pilot/arms/current_skill/board.kicad_pcb wk/astra-evidence/pilot/arms/current_skill/candidate1.kicad_pcb set U1 128 97.3 --rot 270 set Y1 124.7 103 --rot 90 set C2 126.9 103.5 --rot 90 set C4 122.4 102.8 --rot 90
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py wk/astra-evidence/pilot/arms/current_skill/candidate1.kicad_pcb wk/astra-evidence/pilot/arms/current_skill/final.kicad_pcb set U1 127.2 97.3 --rot 270 set Y1 124.7 103 --rot 270 set C4 122.4 101.3 --rot 270
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py wk/astra-evidence/pilot/arms/current_skill/final.kicad_pcb wk/astra-evidence/pilot/arms/current_skill/final.kicad_pcb set U1 126.6 97.3 --rot 270
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py wk/astra-evidence/pilot/arms/current_skill/final.kicad_pcb wk/astra-evidence/pilot/arms/current_skill/final.kicad_pcb set U1 126.6 97.75 --rot 270 set Y1 124.7 103.2 --rot 270 set C4 122.4 102.2 --rot 90
```

## Checks and limits

- `drc0.json` to `drc-final.json`: six pad contacts to zero DRC findings **at the DRC checker's 0.0 mm default edge clearance**. Final check used `--clearance 0.25 --clearance-margin 0 --check-pad-edge` but omitted `--board-edge-clearance`; this did not verify the actor's displayed 0.55 mm edge fallback. The 0.25 mm pad clearance is a fixed fallback because this input declares no floor. No rule was altered.
- `assembly-final.json`, measured with `--baseline board.kicad_pcb`: buildable; zero pad intersections, zero off-board pad copper, no coincident stack, zero new gating courtyard pairs. Fixed USB1/Ref*~2 courtyard overlap remains. Advisory silk-derived contacts remain, including CON2/U1; many library footprints lack proper courtyards or fabrication bodies, limiting assembly certainty.
- `output-checks.json` from read-only `verify_output.py`: all 17 fixed footprints unchanged including locks; exactly U1/Y1/C2/C4 moved; footprint identities, values, pad local geometry/net/layers, and board drawings preserved. Zero actual KiCad tracks and zones both before and after. The DRC parser's reported eight segments are not actual tracks (native KiCad reports zero).
- Named, net-matched pad-edge gaps: Y1.1 to U1.9 = **1.2125 mm**; Y1.2 to U1.10 = **3.0465 mm**; both pass the unchanged 8 mm brief.
- `floorplan-final.json`: three declared rules pass (must-lock, front assembly, named proximity); brief coverage complete. Eleven undeclared rules skipped. `intent.json` retains only task/brief requirements. The emitted observational intent was preserved as `emitted-intent.json`; its inferred Y1 edge-connector exception and inferred legality budget were removed before the final grade, per P6. They were not accepted as permissions.
- The actor reported `legal: true` and displayed a 0.55 mm edge fallback, but **that does not establish edge-clearance compliance**: its pad-legality call does not forward the edge floor. Render/floorplan reported one pad-conflict pair, 0.066 mm shortfall, and Y1's 0.05 mm boundary-clearance shortfall. The independent explicit 0.55 mm DRC confirms two Y1 pad-edge violations; the earlier clean-at-0.55 statement was unsupported and is corrected here. Copper being inside the outline is weaker than satisfying the edge clearance.
- `channels-final.json`: delta gate passes with zero new escape damage; absolute USB1 east deficit remains (demand 4, finest-grid supply 1, fallback track 0.3 mm/clearance 0.25 mm). Floorplan health uses a different census, demand 5/supply 1. Routability is unproven.
- Rigid-consistency check exits 0, zero inconsistent new contacts; this does not imply recovering a historical placement.
- `render-final.json` and inspected `final_F_after.png`: HPWL 250.7 to 233.4564 mm; crossings 52 to 40; aggregate modeled overlap 15.39 to 1.1400 mm2. Viewed the input image and final front image, plus oscillator crop. Four moved footprints are visibly separated.

Driver P0/P2/P3/P4/P6 were consulted with their prerequisite artifacts. P-close refused to finish without congestion disposition despite the improved legality; no waiver was passed. This bounded task forbids routing and changing fixed neighbors. No movie, alternate portfolio, routed validation, or fabrication-readiness verdict was produced. Treat the result as the actual model-chosen pilot candidate, with the above limitations.

## Independent audit correction — 2026-09-13, 20:39 UTC

After the trial ended, the parent ran an identical explicit-floor audit. `../../evaluation/current_skill_drc.json` records `board_edge_clearance: 0.55`, two `pad-board-edge` findings, and 0.05 mm shortfall for each of Y1.3 (GND, centre 123.9,104.3) and Y1.2 (Net-(C2-Pad1), centre 125.5,104.3). The parent reports exit 1. The audit labels the edge `top`; coordinates place these pads by the high-Y boundary. These are reported violations, not asserted false positives.

Source explanation: `py_router/check_drc.py` defines `--board-edge-clearance` with default 0.0, which this trial's `graded_at` also records. In contrast, `place_pose.py` resolves/displays 0.55 through its pose implementation, but `py_placer/placement/pose_ops.py`'s `grade` calls `grade_pad_legality(pcb_data, clearance, pcb_file=board_path)` without `edge_margin`. `grade_pad_legality` consequently uses the 0.25 mm pad clearance as its coarse outline margin, and separately checks physical pad copper at margin zero. Thus its `legal: true` is not a successful 0.55 mm edge test. The differing effective parameters and omitted DRC edge argument explain why the trial missed the independent explicit-floor violations. The task did not itself declare 0.55 mm: the independent evaluator selected the actor's reported fallback as the common evaluation floor. This is not described as a deliberate waiver or violation of a user-declared numerical specification.

This correction is documentation-only: no board mutation, additional placement attempt, or extension of the 451-second pilot occurred. Original board and trial check artifacts are preserved.

Native KiCad read-only confirmation during this audit: the lower Y1.2 and Y1.3 pad bounding boxes end at Y=105.0 mm, while the Edge.Cuts centreline is Y=105.5 mm. Their physical gap is 0.50 mm, hence 0.05 mm short of the independent 0.55 mm evaluation floor. They do not extend outside the outline. `GetBoardEdgesBoundingBox()` includes the 0.05 mm drawing stroke and reaches 105.525 mm; that stroke-inclusive value is not the outline centreline used in this comparison.
