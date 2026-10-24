#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/17_environment_sensor/final.kicad_pcb wk/gpm/17_environment_sensor/final_route/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_diff.py wk/gpm/17_environment_sensor/final_route/in.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2a_diff.kicad_pcb --nets '/USB_D_*' --impedance 90 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.5 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2a_diff.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2_route.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --json-out wk/gpm/17_environment_sensor/final_route/s2_route.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2_route.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2d_iter1.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --json-out wk/gpm/17_environment_sensor/final_route/s2d_iter1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2d_iter1.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2d_iter2.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --json-out wk/gpm/17_environment_sensor/final_route/s2d_iter2.json
