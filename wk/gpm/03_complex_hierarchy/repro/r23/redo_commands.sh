#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/03_complex_hierarchy/repro/s23.kicad_pcb wk/gpm/03_complex_hierarchy/repro/r23/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_planes.py wk/gpm/03_complex_hierarchy/repro/r23/in.kicad_pcb wk/gpm/03_complex_hierarchy/repro/r23/s1_pour.kicad_pcb --nets GND --plane-layers B.Cu --skip-existing-zones
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/03_complex_hierarchy/repro/r23/s1_pour.kicad_pcb wk/gpm/03_complex_hierarchy/repro/r23/s2_route.kicad_pcb --nets '*' --clearance-ceiling 0.3 --via-size 0.889 --via-drill 0.508 --power-nets GND VCC HT '?VAA' /12Vext +12V --power-nets-widths 0.7 0.7 0.6 0.6 0.6 0.6 --layer-costs 1.0 1.0 --via-cost 600 --json-out wk/gpm/03_complex_hierarchy/repro/r23/route.json
