Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

### New placement-specific reproduction: accepted model pose moves graphic copper off the board

The placement half can be reproduced without routing or via generation. On upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`, Windows / KiCad 10.0.0 / Python 3.11.5 / NumPy 2.4.2, I used tracked `kicad_files/esp_prog.kicad_pcb` (SHA256 `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`). Source board preserved; each candidate is a separate output.

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_placer/place_pose.py kicad_files/esp_prog.kicad_pcb OUT.kicad_pcb set U2 115.34 93.6 --rot 90
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_router/check_drc.py OUT.kicad_pcb --check-pad-edge --board-edge-clearance 0.25 --clearance-margin 0 --json OUT.drc.json
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 py_tools/check_assembly.py OUT.kicad_pcb --json OUT.assembly.json
```

All **three commands exit 0**. The pose setter reports `forced=false`, `legal=true`, `no_worse=true`; pad conflicts, hole conflicts and off-board-pad count remain 0. DRC prints **NO DRC VIOLATIONS FOUND**. Assembly reports **buildable (blocking 0)** and `oob_pad_copper_count=0`.

But independent geometry from KiCad's native `pcbnew` loader shows:

| U2 geometry, native stroke-inclusive bounding box | West X | West board edge | Off-outline extent |
|---|---:|---:|---:|
| F.Cu footprint shape | 112.89 mm | 114.00 mm | **1.11 mm** |
| F.Paste footprint shape | 112.99 mm | 114.00 mm | **1.01 mm** |
| F.Mask footprint shape | 112.84 mm | 114.00 mm | **1.16 mm** |

The footprint pads remain inside. DRC's JSON contains **three `accepted: immutable-graphic` records**. The copper geometry is therefore present in the routing checker, but its routing-specific exemption is applied to a placement-created defect. [Current unconditional graphic acceptance](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_router/check_drc.py#L3209).

Positive controls matter here:

| Candidate | `place_pose` | DRC accepted graphics | DRC violations | Assembly blocking |
|---|---|---:|---:|---:|
| Original U2 pose | legal, exit 0 | 0 | 0 | 0 |
| U2 `(115.34,93.6,90)` | legal, exit 0 | **3** | 0 | 0 |
| U2 `(116.70,93.6,90)` | legal, exit 0 | **0** | 0 | 0 |

The third pose shifts the same rotated part 1.36 mm inward. Its native F.Cu west extent is 114.25 mm, exactly .25 mm inside; paste begins 114.35 mm. Thus the checker should discriminate a real geometric defect while retaining the nearby usable model-selected pose. Neither alternative is asserted to be an electrically optimized or production-ready placement.

### How to enhance Astra placement without prescribing its layout

1. **Give placement a complete geometry oracle.** Return pads and footprint graphic copper separately, with owner, layer, physical outline overrun and required edge-clearance shortfall. Add paste/mask geometry as distinct engineering channels. For emitted shapes, compare native KiCad geometry on these real footprints as an independent control; do not test only a duplicate of the repository parser.
2. **Scope acceptance to the operation and actual requirement.** Routing can classify immutable input geometry as pre-existing without claiming it is manufacturable. Placement can change footprint position, so `immutable-graphic` cannot authorize a newly created overrun. A lock means the model should not silently move that part; it does **not** prove off-board copper is an acceptable board requirement. Report inherited defects, permitted mechanical exceptions and newly introduced defects distinctly.
3. **Separate final validation from candidate exploration.** The model may hypothesize and inspect any pose in a sandbox; the checked promotion boundary should prevent a board with a newly introduced nonexempt copper overrun from being treated as clean. A numerical explanation plus valid nearby candidates is more useful than prescribing where U2 must go.
4. **Make partial claims visibly partial.** Rename or qualify the pose setter's `legal` result as pad-geometry legality unless every required placement channel is covered. A high-level `buildable` or final-ready claim must incorporate missing required geometry checks or report them unmeasured.
5. **Treat via-in-paste manufacturing as an explicit process choice.** The new tests here did not exercise routing or establish a particular via fill/cap process. Detection should distinguish paste overlap, actual copper/pad overlap, via treatment, and declared assembly/fabrication policy. Do not silently mutate via manufacturing attributes merely to make a checker pass; machine-readable requirements must reflect an actually chosen, supported process.

### Placement acceptance tests to add

- Reproduce the three actual U2 poses above via `place_pose`, without `--force`; flag the off-board graphic copper candidate while retaining both controls.
- A full placement validator reports the native F.Cu overrun even though `oob_pad_copper_count=0` and the part has no track/via changes.
- A routing-only comparison may separately disclose unchanged inherited graphic geometry; the same exemption cannot erase a placement-created change.
- Include rotated/back-side graphic copper, paste and mask shapes, polygon and line primitives, stroke width, and nonrectangular outline cases; publish unsupported primitives as unmeasured.
- Detect per-pad paste expansion/reduction and explicit aperture shapes as separate carriers when implementing via-in-paste checks; bounding extents alone are insufficient for holes/windows/nonrectangular apertures.
- Cross-check native KiCad DRC/geometry on the final board; report what each instrument checked rather than treating one successful subprocess as a complete engineering sign-off.

Artifacts: `pose_geometry/graphic_probe.py`, `graphic-20260913-222528/results.json`, all three candidate boards, pose logs, DRC JSON/logs and assembly JSON/logs. This is a direct placement-tool reproduction of the graphic-copper waiver gap; the original issue's 11-arm routing/paste-via claims were not rerun in this experiment.
