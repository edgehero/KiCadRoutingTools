#!/bin/zsh
# helpers/route_variant.sh DIFF_BOARD OUT_DIR [extra route.py args...] -- the final_plan.sh route.py x3 tail on a board
# that already carries the pour + USB diff step, with extra/overriding route.py args, then board_score with the spec.
# Why a helper: A/B of route parameters needs the same 3-pass tail replayed with one knob changed; no repo tool does that.
set -e
cd ~/Documents/git/krt-gpm
IN=$1; O=$2; shift 2; mkdir -p $O
python3 -X utf8 py_router/copy_board.py $IN $O/2_diff.kicad_pcb > /dev/null
A=(--clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.5 0.5 0.5 0.5 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0)
python3 -X utf8 py_router/route.py $O/2_diff.kicad_pcb $O/3_route.kicad_pcb --nets '*' $A "$@" --json-out $O/3_route.json > $O/3_route.log 2>&1
python3 -X utf8 py_router/route.py $O/3_route.kicad_pcb $O/4_iter1.kicad_pcb --nets '*' $A "$@" --json-out $O/4_iter1.json > $O/4_iter1.log 2>&1
python3 -X utf8 py_router/route.py $O/4_iter1.kicad_pcb $O/5_iter2.kicad_pcb --nets '*' $A "$@" --json-out $O/5_iter2.json > $O/5_iter2.log 2>&1
python3 -X utf8 py_tools/board_score.py $O/5_iter2.kicad_pcb --intent wk/gpm/17_environment_sensor/intent_run.json --baseline wk/gpm/17_environment_sensor/fixed.kicad_pcb --impedance-nets '/USB_D_*' --json $O/5_iter2.score.json --quiet 2>&1 | grep BLOCKING
