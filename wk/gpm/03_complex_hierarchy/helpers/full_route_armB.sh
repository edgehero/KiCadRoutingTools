#!/bin/bash
# Full route (arm B chain, as final_route/final_plan.sh) of one placement, in its own folder.
# Why: judge_seeds runs only the --quick judging chain; comparing placements AFTER DONE (copper, segments)
# needs the full chain on each, and no repo tool runs a full chain over a list of placements.
# usage: full_route_armB.sh <placement.kicad_pcb> <outdir>
set -e
cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:$PATH"
P=$1; O=$2; D=wk/gpm/03_complex_hierarchy
mkdir -p $O
export REDO_RUNDIR=$PWD/$O REDO_MANIFEST=$PWD/$O/redo_commands.sh KICAD_ROUTE_TRACE=1
python3 -X utf8 py_router/copy_board.py $P $O/in.kicad_pcb > /dev/null
python3 -X utf8 py_router/route_planes.py $O/in.kicad_pcb $O/s1_pour.kicad_pcb --nets GND --plane-layers B.Cu --skip-existing-zones > $O/step1_pour.log 2>&1
python3 -X utf8 py_router/route.py $O/s1_pour.kicad_pcb $O/s2_route.kicad_pcb --nets '*' --clearance-ceiling 0.3 --via-size 0.889 --via-drill 0.508 --power-nets GND VCC HT '?VAA' /12Vext +12V --power-nets-widths 0.7 0.7 0.6 0.6 0.6 0.6 --layer-costs 1.0 1.0 --via-cost 600 --json-out $O/route.json > $O/step2_route.log 2>&1
python3 -X utf8 py_tools/board_score.py $O/s2_route.kicad_pcb --intent $D/intent_run.json --baseline $D/fixed.kicad_pcb --net-min-widths $D/net_min_widths.json --json $O/s2_route.score.json --quiet > /dev/null 2>&1 || true
python3 -c "import json,sys;d=json.load(open('$O/s2_route.score.json'));print('$P', 'blocking',d['blocking'],'joins',d['joins_needed'],d['quality'])"
