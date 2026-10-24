#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/12_steppenprobe/final.kicad_pcb wk/gpm/12_steppenprobe/final_route/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_planes.py wk/gpm/12_steppenprobe/final_route/in.kicad_pcb wk/gpm/12_steppenprobe/final_route/step1.kicad_pcb --nets +3V3 GND --plane-layers F.Cu B.Cu
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_diff.py wk/gpm/12_steppenprobe/final_route/step1.kicad_pcb wk/gpm/12_steppenprobe/final_route/step2a.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/step2a.kicad_pcb wk/gpm/12_steppenprobe/final_route/step2.kicad_pcb --nets '*' --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1 --json-out wk/gpm/12_steppenprobe/final_route/step2.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/step2.kicad_pcb wk/gpm/12_steppenprobe/final_route/iter1.kicad_pcb --nets '*' --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1 --json-out wk/gpm/12_steppenprobe/final_route/iter1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/iter1.kicad_pcb wk/gpm/12_steppenprobe/final_route/iter2.kicad_pcb --nets '*' --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1 --json-out wk/gpm/12_steppenprobe/final_route/iter2.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/iter2.kicad_pcb wk/gpm/12_steppenprobe/final_route/fix1.kicad_pcb --nets +1V8 GND +3V3 --force-reroute --clearance-ceiling 0.15 --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.5 0.3 0.3 0.3 --layer-costs 1.0 1.5 --escalation board --same-net-pad-clearance 0.1 --json-out wk/gpm/12_steppenprobe/final_route/fix1.json
