#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/copy_board.py wk/gpm/12_steppenprobe/final.kicad_pcb wk/gpm/12_steppenprobe/final_route/in.kicad_pcb
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_planes.py wk/gpm/12_steppenprobe/final_route/in.kicad_pcb wk/gpm/12_steppenprobe/final_route/step1.kicad_pcb --nets +3V3 GND --plane-layers F.Cu B.Cu --min-thickness 0.15 --no-fix-drc-settings
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route_diff.py wk/gpm/12_steppenprobe/final_route/step1.kicad_pcb wk/gpm/12_steppenprobe/final_route/step2a.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --escalation board
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/step2a.kicad_pcb wk/gpm/12_steppenprobe/final_route/pwr1.kicad_pcb --nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --track-width 0.3 --escalation off --json-out wk/gpm/12_steppenprobe/final_route/pwr1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/pwr1.kicad_pcb wk/gpm/12_steppenprobe/final_route/sig1.kicad_pcb --nets '*' '!GND' '!+3V3' '!VBUS' '!+5V' '!+1V8' '!/VPLL' '!/VPHY' '!Vdrive' --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --escalation board --json-out wk/gpm/12_steppenprobe/final_route/sig1.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/sig1.kicad_pcb wk/gpm/12_steppenprobe/final_route/sig2.kicad_pcb --nets '*' '!GND' '!+3V3' '!VBUS' '!+5V' '!+1V8' '!/VPLL' '!/VPHY' '!Vdrive' --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --escalation board --json-out wk/gpm/12_steppenprobe/final_route/sig2.json
# cwd=~/Documents/git/krt-gpm
KICAD_ROUTE_TRACE=1 python3 -u -X utf8 py_router/route.py wk/gpm/12_steppenprobe/final_route/sig2.kicad_pcb wk/gpm/12_steppenprobe/final_route/pwr2.kicad_pcb --nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets GND +3V3 VBUS +5V +1V8 /VPLL /VPHY Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --clearance-ceiling 0.15 --same-net-pad-clearance 0.1 --no-fix-drc-settings --layer-costs 1.0 1.0 --track-width 0.3 --escalation off --json-out wk/gpm/12_steppenprobe/final_route/pwr2.json
