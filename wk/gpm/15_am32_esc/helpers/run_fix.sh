#!/bin/bash
# run_fix.sh: one scoped lap on arm F's board -- rip FD6288_VS1 (its redundant loop edge) and re-route with F's flags.
cd ~/Documents/git/krt-gpm || exit 9
export PATH="$HOME/.venvs/krt/bin:$PATH"
R=wk/gpm/15_am32_esc/arm_F_vc300_lc
export REDO_RUNDIR=$R REDO_MANIFEST=$R/redo_commands.sh KICAD_ROUTE_TRACE=1
python3 -X utf8 py_router/route.py $R/iter2.kicad_pcb $R/fix1.kicad_pcb --nets '*' --power-nets GND VDD BAT+ BAT_IN+ FD6288_VS1 FD6288_VS2 FD6288_VS3 'Net-(U4-VOUT)' 5v 3.3v --power-nets-widths 0.5 2.0 2.0 2.0 2.0 2.0 2.0 0.7 0.7 0.3 --via-cost 300 --layer-costs 1.0 3.0 3.0 1.0 --rip-existing-nets FD6288_VS1 --json-out $R/fix1.json
echo "ROUTE_EXIT fix1=$?"
python3 -X utf8 py_tools/board_score.py $R/fix1.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb --json $R/fix1.score.json --quiet
python3 -X utf8 check_complete.py $R/fix1.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb 2>&1 | grep VERDICT | cut -c1-160
echo "ARM_DONE fix1"
