#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/copy_board.py wk/gp14/07_One-Air-Max/placed.kicad_pcb wk/gp14/07_One-Air-Max/final_route/in.kicad_pcb
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/add_rule_area.py wk/gp14/07_One-Air-Max/final_route/in.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s1_ant.kicad_pcb --name ANT_KEEPOUT --ref U1 --rect -9 9.73 9 15.75
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route_planes.py wk/gp14/07_One-Air-Max/final_route/s1_ant.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s2_pour.kicad_pcb --nets GND PGND +3V3 --plane-layers In2.Cu In2.Cu In1.Cu --clearance-ceiling 0.1
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route_diff.py wk/gp14/07_One-Air-Max/final_route/s2_pour.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s3_diff.kicad_pcb --nets '/USB*' --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.2 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route.py wk/gp14/07_One-Air-Max/final_route/s3_diff.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s4_route.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.2 --max-ripup 5 --power-nets GND PGND +3V3 +5V +5VBAT +5VUSB /VMUX BAT- /Battery_holder/VBAT+ 'Net-(F2-Pad2)' /Solar_module/VBAT 'Net-(Q1-D)' 'Net-(C24-Pad2)' /Solar_module/Solar+ /Solar_module/SYS 'Net-(U5-PMID)' /Solar_module/SW1 /Solar_module/SW2 'Net-(U6-EN)' 'Net-(U6-SW)' 'Net-(U2-SW)' --power-nets-widths 0.3 0.5 0.3 0.4 0.5 0.4 0.5 0.8 0.8 0.8 0.8 0.8 0.8 0.6 0.6 0.6 0.6 0.6 0.5 0.5 0.4 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --json-out wk/gp14/07_One-Air-Max/final_route/s4_route.json
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route.py wk/gp14/07_One-Air-Max/final_route/s4_route.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s5_iter1.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.2 --max-ripup 5 --power-nets GND PGND +3V3 +5V +5VBAT +5VUSB /VMUX BAT- /Battery_holder/VBAT+ 'Net-(F2-Pad2)' /Solar_module/VBAT 'Net-(Q1-D)' 'Net-(C24-Pad2)' /Solar_module/Solar+ /Solar_module/SYS 'Net-(U5-PMID)' /Solar_module/SW1 /Solar_module/SW2 'Net-(U6-EN)' 'Net-(U6-SW)' 'Net-(U2-SW)' --power-nets-widths 0.3 0.5 0.3 0.4 0.5 0.4 0.5 0.8 0.8 0.8 0.8 0.8 0.8 0.6 0.6 0.6 0.6 0.6 0.5 0.5 0.4 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --json-out wk/gp14/07_One-Air-Max/final_route/s5_iter1.json
# cwd=<krt-checkout>
python3 -u -X utf8 py_router/route.py wk/gp14/07_One-Air-Max/final_route/s5_iter1.kicad_pcb wk/gp14/07_One-Air-Max/final_route/s6_iter2.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.2 --max-ripup 5 --power-nets GND PGND +3V3 +5V +5VBAT +5VUSB /VMUX BAT- /Battery_holder/VBAT+ 'Net-(F2-Pad2)' /Solar_module/VBAT 'Net-(Q1-D)' 'Net-(C24-Pad2)' /Solar_module/Solar+ /Solar_module/SYS 'Net-(U5-PMID)' /Solar_module/SW1 /Solar_module/SW2 'Net-(U6-EN)' 'Net-(U6-SW)' 'Net-(U2-SW)' --power-nets-widths 0.3 0.5 0.3 0.4 0.5 0.4 0.5 0.8 0.8 0.8 0.8 0.8 0.8 0.6 0.6 0.6 0.6 0.6 0.5 0.5 0.4 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --json-out wk/gp14/07_One-Air-Max/final_route/s6_iter2.json
