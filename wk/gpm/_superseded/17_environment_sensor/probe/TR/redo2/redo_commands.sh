#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ATTRACT_POTENTIAL=65 KICAD_FINALIZE_REAUDIT=1 KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_PACK_INLINE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/probe/TR/b.kicad_pcb wk/gpm/17_environment_sensor/probe/TR/x2.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 --json-out wk/gpm/17_environment_sensor/probe/TR/x2.json
