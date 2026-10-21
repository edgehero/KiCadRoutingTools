#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route.py wk/gp14/01_ecc83-pp_v2/repro/placed.kicad_pcb wk/gp14/01_ecc83-pp_v2/repro/rec/out.kicad_pcb --nets '*' --clearance 0.508 --track-width 0.8636 --via-size 0.45 --via-drill 0.3 --power-nets GND --power-nets-widths 0.8636 --layers F.Cu B.Cu --layer-costs 1.0 3.0 --grid-step 0.05
