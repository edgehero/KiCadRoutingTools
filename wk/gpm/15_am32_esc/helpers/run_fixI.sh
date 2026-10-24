#!/bin/bash
# run_fixI.sh: one lap on arm I's board -- re-run the GND plane finalize (route.py --nets GND, I's flags) to clear the
# GND narrow-pad-joint at C3.2 (GND is zone-owning, so --force-reroute skips it).
cd ~/Documents/git/krt-gpm || exit 9
export PATH="$HOME/.venvs/krt/bin:$PATH:/Applications/KiCad/KiCad.app/Contents/MacOS"
R=wk/gpm/15_am32_esc/arm_I_vc300_lc_board
export REDO_RUNDIR=$R REDO_MANIFEST=$R/redo_commands.sh KICAD_ROUTE_TRACE=1
python3 -X utf8 py_router/route.py $R/iter2.kicad_pcb $R/fix1.kicad_pcb --nets GND --power-nets GND VDD BAT+ BAT_IN+ FD6288_VS1 FD6288_VS2 FD6288_VS3 'Net-(U4-VOUT)' 5v 3.3v --power-nets-widths 0.5 2.0 2.0 2.0 2.0 2.0 2.0 0.7 0.7 0.3 --via-cost 300 --layer-costs 1.0 3.0 3.0 1.0 --escalation board --json-out $R/fix1.json
echo "ROUTE_EXIT fix1=$?"
python3 -X utf8 py_tools/board_score.py $R/fix1.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb --json $R/fix1.score.json --quiet
python3 -X utf8 check_complete.py $R/fix1.kicad_pcb --intent wk/gpm/15_am32_esc/intent_run.json --baseline wk/gpm/15_am32_esc/am32_esc.kicad_pcb 2>&1 | grep VERDICT | cut -c1-160
python3 -X utf8 py_router/check_weird.py $R/fix1.kicad_pcb 2>&1 | grep -E "^    net|FOUND"
echo "ARM_DONE fixI"
