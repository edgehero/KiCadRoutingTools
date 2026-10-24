#!/bin/zsh
# helpers/full_chain.sh IN_BOARD OUT_DIR -- the final_plan.sh chain (pour, USB diff, route x3) on any placed board,
# for A/B of placements; writes OUT_DIR/{1_planes,2_diff,3_route,4_iter1,5_iter2}.kicad_pcb + logs.
# Why a helper: judge_seeds runs --quick 2 and quick_score cannot grade --impedance-nets, so the declared USB impedance
# spec is invisible to the seed judge; this replays the full (non-quick) chain so the spec can be graded per seed.
set -e
cd ~/Documents/git/krt-gpm
IN=$1; O=$2; mkdir -p $O
python3 -X utf8 py_router/copy_board.py $IN $O/in.kicad_pcb > /dev/null
python3 -X utf8 py_router/route_planes.py $O/in.kicad_pcb $O/1_planes.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones > $O/1_planes.log 2>&1
python3 -X utf8 py_router/route_diff.py $O/1_planes.kicad_pcb $O/2_diff.kicad_pcb --nets '/USB_D_*' --track-width 0.1 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --impedance 90 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 > $O/2_diff.log 2>&1
A=(--clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.5 0.5 0.5 0.5 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0)
python3 -X utf8 py_router/route.py $O/2_diff.kicad_pcb $O/3_route.kicad_pcb --nets '*' $A --json-out $O/3_route.json > $O/3_route.log 2>&1
python3 -X utf8 py_router/route.py $O/3_route.kicad_pcb $O/4_iter1.kicad_pcb --nets '*' $A --json-out $O/4_iter1.json > $O/4_iter1.log 2>&1
python3 -X utf8 py_router/route.py $O/4_iter1.kicad_pcb $O/5_iter2.kicad_pcb --nets '*' $A --json-out $O/5_iter2.json > $O/5_iter2.log 2>&1
python3 -X utf8 py_tools/board_score.py $O/5_iter2.kicad_pcb --intent wk/gpm/17_environment_sensor/intent_run.json --baseline wk/gpm/17_environment_sensor/fixed.kicad_pcb --impedance-nets '/USB_D_*' --json $O/5_iter2.score.json --quiet 2>&1 | grep BLOCKING
grep -E "Diff pairs:|SE fallback" $O/2_diff.log
