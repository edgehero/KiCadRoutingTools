#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/17_environment_sensor/final.kicad_pcb wk/gpm/17_environment_sensor/final_route/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/17_environment_sensor/final_route/in.kicad_pcb wk/gpm/17_environment_sensor/final_route/in10.kicad_pcb
# KiCad-10 file format, so route.py can DECLARE Type VII on the vias it lays in pads (fill_for_delivery saves KiCad 10 anyway; see TOOL_GAPS). Run by hand, not by the recorder:
# cwd=~/Documents/git/krt-gpm
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb upgrade wk/gpm/17_environment_sensor/final_route/in10.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_diff.py wk/gpm/17_environment_sensor/final_route/in10.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2a_diff.kicad_pcb --nets '/USB_D_*' --impedance 90 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.5 --via-drill 0.2 --layers F.Cu --board-edge-clearance 0.22
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2a_diff.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2a_usb.kicad_pcb --nets /USB_D_P /USB_D_N --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --layers F.Cu --board-edge-clearance 0.22
# cwd=~/Documents/git/krt-gpm
KICAD_ATTRACT_POTENTIAL=65 KICAD_FINALIZE_REAUDIT=1 KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_PACK_INLINE=1 KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2a_usb.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2_route.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 --json-out wk/gpm/17_environment_sensor/final_route/s2_route.json
# cwd=~/Documents/git/krt-gpm
KICAD_ATTRACT_POTENTIAL=65 KICAD_FINALIZE_REAUDIT=1 KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_PACK_INLINE=1 KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2_route.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2d_iter1.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 --json-out wk/gpm/17_environment_sensor/final_route/s2d_iter1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ATTRACT_POTENTIAL=65 KICAD_FINALIZE_REAUDIT=1 KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_PACK_INLINE=1 KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/17_environment_sensor/final_route/s2d_iter1.kicad_pcb wk/gpm/17_environment_sensor/final_route/s2d_iter2.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 --json-out wk/gpm/17_environment_sensor/final_route/s2d_iter2.json
# Hand-written copper after the last route step (SKILL.md sec 4 'Hand-written copper'), appended by hand: KiCad wants each JST-SH connector's two MP tabs (one net, two pads) joined.
# cwd=~/Documents/git/krt-gpm
python3 -u -X utf8 py_tools/check_join.py wk/gpm/17_environment_sensor/final_route/s2d_iter2.kicad_pcb 'unconnected-(J2-PadMP)' 197.65,138.855,F.Cu 203.25,138.855,F.Cu --width 0.25 --keep-staged wk/gpm/17_environment_sensor/final_route/s3_join_j2.kicad_pcb
# cwd=~/Documents/git/krt-gpm
python3 -u -X utf8 py_tools/check_join.py wk/gpm/17_environment_sensor/final_route/s3_join_j2.kicad_pcb 'unconnected-(J3-PadMP)' 190.34,138.855,B.Cu 195.94,138.855,B.Cu --width 0.25 --keep-staged wk/gpm/17_environment_sensor/final_route/s3_joins.kicad_pcb
