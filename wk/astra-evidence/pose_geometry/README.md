# Placement pose / geometry evidence

Tested upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3` on 2026-09-13, Windows, KiCad 10.0.0 Python 3.11.5, NumPy 2.4.2. No production source or original board was modified. The scripts expect this directory at `wk/astra-evidence/pose_geometry` under the repository root.

## Final evidence runs

- `reproduce.py` → **run-20260913-222129**: #960 armed regime + sanctioned writer/undeclared writer controls; #961 real USB1 transformations, two intent bands, requested/effective margin controls, pad geometry and DRC JSON. The earlier `run-20260913-222018` is a preliminary run without the independent DRC calls/effective-margin capture; use the final run.
- `prototype_guard.py` → **guard-20260913-222230**: five arms of an isolated experimental destination-provenance guard. The prototype is NOT a production patch and its limitations are in the #960 addendum.
- `graphic_probe.py` → **graphic-20260913-222528**: #962 final three arms through the sanctioned pose CLI, native KiCad geometry, repository DRC and assembly. Earlier graphic runs were exploratory (one rotated a part instead of retaining its original rotation); use the final three-arm run.
- `issue-960-addendum.md`, `issue-961-addendum.md`, `issue-962-addendum.md`: detailed issue-ready findings, limits, proposals and acceptance tests.

Run the scripts with:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/reproduce.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/prototype_guard.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 wk/astra-evidence/pose_geometry/graphic_probe.py
```

Each script creates a timestamped output directory. `results.json` and child-command logs carry measured results and subprocess argv. `esp_prog` has no tracked `.kicad_pro`; no sibling was dropped. Every existing sibling is carried using repository helpers. Geometry checks explicitly record their chosen floors; these fallback floors are not claimed to be an independently established manufacturing specification.

KiCad's native `GetBoundingBox()` geometry for graphic shapes includes stroke. Repository pad-edge aggregate counts footprints while `check_drc` lists individual pads. The reports deliberately preserve that distinction.

## Narrow existing regression checks

Also executed unchanged on this pinned revision:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 tests/test_run26_edge_seat_body_basis.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 tests/test_892_place_pose.py
```

- Existing edge-seating/body-basis test: **ALL PASS**, exit 0.
- Existing pose battery: **133 passed, 0 failed**, exit 0.

These tests passing alongside the reproductions show the specific integration gaps are not covered by the existing checks. They do not imply complete placement correctness. Existing tool output warns about duplicate `Ref*` footprints and missing courtyard fallback on this board; all blocks are retained and the report does not claim an independently finished layout.

## Input identity

`kicad_files/esp_prog.kicad_pcb` SHA256 before and after the experiments:

`165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`

These are controlled tool-contract tests, not a blinded or repeated model benchmark. Source poses are deliberately known in positive controls. Improved proxy metrics are never presented as proof of final PCB quality.
