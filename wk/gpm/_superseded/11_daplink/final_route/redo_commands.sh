#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/11_daplink/final.kicad_pcb wk/gpm/11_daplink/final_route/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_diff.py wk/gpm/11_daplink/final_route/in.kicad_pcb wk/gpm/11_daplink/final_route/s1_diff.kicad_pcb --nets /D+ /D- --track-width 0.2 --diff-pair-gap 0.2 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/11_daplink/final_route/s1_diff.kicad_pcb wk/gpm/11_daplink/final_route/s2_signal.kicad_pcb --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets +5V +3.3V GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/final_route/s2_signal.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_planes.py wk/gpm/11_daplink/final_route/s2_signal.kicad_pcb wk/gpm/11_daplink/final_route/s3_pour.kicad_pcb --nets GND GND --plane-layers F.Cu B.Cu
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/11_daplink/final_route/s3_pour.kicad_pcb wk/gpm/11_daplink/final_route/s4_route.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets +5V +3.3V GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/final_route/s4_route.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/11_daplink/final_route/s4_route.kicad_pcb wk/gpm/11_daplink/final_route/s5_iter1.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets +5V +3.3V GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/final_route/s5_iter1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/11_daplink/final_route/s5_iter1.kicad_pcb wk/gpm/11_daplink/final_route/s6_iter2.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets +5V +3.3V GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/final_route/s6_iter2.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/11_daplink/final_route/s6_iter2.kicad_pcb wk/gpm/11_daplink/final_route/s7_force.kicad_pcb --nets /TGT_RST GND --force-reroute --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets +5V +3.3V GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/final_route/s7_force.json
