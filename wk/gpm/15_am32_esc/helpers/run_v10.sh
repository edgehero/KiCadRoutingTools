#!/bin/bash
# run_v10.sh <dir>: the shipped chain (S1 flags) on the placement saved in KiCad 10 format, through the delivery fill.
# Why (TOOL_GAPS): fill_for_delivery re-saves a KiCad-8 board as KiCad 10, which turns its 52 accepted
# "undeclarable" vias-in-paste into blocking drc_via_in_paste; the route step stamps Type VII only on a KiCad-10 file.
cd ~/Documents/git/krt-gpm || exit 9
export PATH="$HOME/.venvs/krt/bin:$PATH:/Applications/KiCad/KiCad.app/Contents/MacOS"
R=wk/gpm/15_am32_esc/$1
mkdir -p $R
export REDO_RUNDIR=$R REDO_MANIFEST=$R/redo_commands.sh KICAD_ROUTE_TRACE=1
PW=(--power-nets GND VDD BAT+ BAT_IN+ FD6288_VS1 FD6288_VS2 FD6288_VS3 'Net-(U4-VOUT)' 5v 3.3v --power-nets-widths 0.5 2.0 2.0 2.0 2.0 2.0 2.0 0.7 0.7 0.3)
FL=(--via-cost 300 --layer-costs 1.0 3.0 3.0 1.0 --grid-step 0.05 --escalation board)
python3 -X utf8 py_router/copy_board.py wk/gpm/15_am32_esc/final.kicad_pcb $R/in.kicad_pcb || exit 3
python3 -X utf8 py_router/copy_board.py $R/in.kicad_pcb $R/in_v10.kicad_pcb || exit 3
kicad-cli pcb upgrade $R/in_v10.kicad_pcb; echo "UPGRADE_EXIT=$?"; head -2 $R/in_v10.kicad_pcb
prev=$R/in_v10.kicad_pcb
for step in step2 iter1 iter2; do
  python3 -X utf8 py_router/route.py $prev $R/$step.kicad_pcb --nets '*' "${PW[@]}" "${FL[@]}" --json-out $R/$step.json
  echo "ROUTE_EXIT $step=$?"; prev=$R/$step.kicad_pcb
done
python3 -X utf8 py_router/check_weird.py $prev 2>&1 | grep -E "FOUND|NO WEIRD|^    net"
python3 -X utf8 py_tools/board_score.py $prev --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb --json ${prev%.kicad_pcb}.score.json --quiet
echo "ARM_DONE $1 $prev"
