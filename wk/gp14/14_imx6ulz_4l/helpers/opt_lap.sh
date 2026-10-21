#!/bin/bash
# one optimisation lap: re-run the chain's main route + 3 iterations from final_route/s2a_diff with EXTRA flags,
# then the two cleanup helpers, then grade. (Driver for the post-DONE via/copper laps; see TOOL_GAPS "no lap runner".)
# usage: helpers/opt_lap.sh OUTDIR "EXTRA FLAGS" [ENV=VAL ...]
set -u
cd <krt-checkout>; export PATH="$HOME/.venvs/krt/bin:$PATH"
W=wk/gp14/14_imx6ulz_4l; O=$1; EXTRA=$2; shift 2
mkdir -p $O
L="F.Cu In1.Cu In2.Cu B.Cu"
PW=(--power-nets GND +3V3 +5V +1V2 VMEM '/SOC Power/VDD_SOC_CAP' '/SOC Power/VDD_ARM_SOC_IN' '/SOC Power/VDD_ARM_CAP' '/SOC Power/VDD_HIGH_IN' '/SOC Power/VDD_HIGH_CAP' '/SOC Power/VDD_SNVS_IN' '/SOC Power/*_SW' --power-nets-widths 0.2 0.2 0.4 0.3 0.2 0.15 0.2 0.15 0.2 0.15 0.15 0.4)
SZ=(--track-width 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers $L --layer-costs ${LCOST:-1.0 6.0 1.5 1.0} --no-bga-zones --max-ripup ${RIP:-5})
python3 -X utf8 py_router/copy_board.py $W/final_route/s2a_diff.kicad_pcb $O/s2a_diff.kicad_pcb > /dev/null
prev=$O/s2a_diff.kicad_pcb
for k in 0 1 2 3; do
  env "$@" python3 -X utf8 -u py_router/route.py $prev $O/r$k.kicad_pcb --nets '*' "${SZ[@]}" "${PW[@]}" $EXTRA --json-out $O/r$k.json > $O/r$k.log 2>&1 || { echo "route $k failed"; exit 1; }
  prev=$O/r$k.kicad_pcb
  grep "^JSON_SUMMARY_MIN" $O/r$k.log | python3 -c "import sys,json;d=json.loads(sys.stdin.read().split(': ',1)[1]);print('r$k failed',d['failed'],'deficit',d['multipoint_deficit'],d['pad_pairs_open']['nets'][:6])"
done
python3 -X utf8 $W/helpers/strict_collapse.py $prev $O/c1.kicad_pcb | tail -1
python3 -X utf8 $W/helpers/strict_collapse.py $O/c1.kicad_pcb $O/c2.kicad_pcb | tail -1
python3 -X utf8 $W/helpers/strict_collapse.py $O/c2.kicad_pcb $O/c3.kicad_pcb | tail -1
python3 -X utf8 $W/helpers/vip_joins.py $O/c3.kicad_pcb $O/final.kicad_pcb /DRAM/DRAM_DQ0 /DRAM/DRAM_DQ1 /DRAM/DRAM_DQ2 /DRAM/DRAM_DQ3 /DRAM/DRAM_DQ4 /DRAM/DRAM_DQ5 /DRAM/DRAM_DQ6 /DRAM/DRAM_DQ7 | tail -1
python3 -X utf8 py_tools/board_score.py $O/final.kicad_pcb --intent $W/intent.json --baseline $W/fixed.kicad_pcb --length-groups $W/length_groups.json --json $O/final.score.json --quiet 2>&1 | grep BLOCKING
python3 -X utf8 check_complete.py $O/final.kicad_pcb --intent $W/intent.json --baseline $W/fixed.kicad_pcb --length-groups $W/length_groups.json --json $O/final.complete.json 2>&1 | grep VERDICT | cut -c1-80
python3 -X utf8 $W/helpers/kicad_length_check.py $O/final.kicad_pcb | head -3
