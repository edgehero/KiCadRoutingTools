#!/bin/bash
# run_arm.sh <arm_dir_name> <extra route.py flags...> -- one route arm of the final chain, recorded in its own REDO_RUNDIR:
# copy_board final.kicad_pcb -> in, route.py step 2 with the plan's power widths + the extra flags, then (ITERS, default 2)
# Step-2d iterations with the SAME flag string, then board_score + check_complete on the last board.
# Why: the skill's chain is a command list; an A/B arm needs the same chain with one lever changed, in its own
# REDO_RUNDIR so final_route/ keeps the shipped chain. No repo tool runs "the plan with one flag added".
cd ~/Documents/git/krt-gpm || exit 9
export PATH="$HOME/.venvs/krt/bin:$PATH"
A=$1; shift
R=wk/gpm/15_am32_esc/$A
mkdir -p $R
export REDO_RUNDIR=$R REDO_MANIFEST=$R/redo_commands.sh KICAD_ROUTE_TRACE=1
PW=(--power-nets GND VDD BAT+ BAT_IN+ FD6288_VS1 FD6288_VS2 FD6288_VS3 'Net-(U4-VOUT)' 5v 3.3v --power-nets-widths 0.5 2.0 2.0 2.0 2.0 2.0 2.0 0.7 0.7 0.3)
python3 -X utf8 py_router/copy_board.py wk/gpm/15_am32_esc/final.kicad_pcb $R/in.kicad_pcb || exit 3
prev=$R/in.kicad_pcb
for step in step2 iter1 iter2; do
  [ "$step" != step2 ] && [ "${ITERS:-2}" = 0 ] && break
  python3 -X utf8 py_router/route.py $prev $R/$step.kicad_pcb --nets '*' "${PW[@]}" "$@" --json-out $R/$step.json
  echo "ROUTE_EXIT $step=$?"
  prev=$R/$step.kicad_pcb
done
python3 -X utf8 py_tools/board_score.py $prev --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb --json ${prev%.kicad_pcb}.score.json --quiet
python3 -X utf8 check_complete.py $prev --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb 2>&1 | grep VERDICT | cut -c1-160
echo "ARM_DONE $A $prev"
