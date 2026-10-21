#!/bin/bash
# The judging chain (plan-pcb-placement 3.6 step 1), identical for every seed:
#   pour GND on B.Cu -> qfn_fanout U2 -> place_fanout_clearance -> route_diff USB (--quick 2)
#   -> route.py '*' --quick 2 -> copy out -> quick_score.
# usage: judge_chain.sh ROUND_DIR SEED      (run from the worktree root)
# Why a script: no repo tool runs "the board's routing chain" over judge.json's seeds;
# this only sequences repo CLIs with fixed arguments so every candidate gets the same chain.
set -u
R=$1; S=$2
W=$R/s${S}_route
mkdir -p "$W"
PY="python3 -X utf8"
{
date -u +"START %H:%M:%S"
$PY py_router/copy_board.py "$R/s$S.kicad_pcb" "$W/s${S}_in.kicad_pcb" || exit 11
$PY py_router/route_planes.py "$W/s${S}_in.kicad_pcb" "$W/s${S}_p.kicad_pcb" --nets GND --plane-layers B.Cu \
    --clearance-ceiling 0.2 || exit 12
$PY py_router/qfn_fanout.py "$W/s${S}_p.kicad_pcb" --output "$W/s${S}_f.kicad_pcb" --component U2 \
    --nets '*' '!GND' --width 0.127 --clearance 0.2 || exit 13
$PY py_placer/place_fanout_clearance.py "$W/s${S}_f.kicad_pcb" "$W/s${S}_c.kicad_pcb" --clearance 0.2 \
    --intent "$R/intent.json" || exit 14
$PY py_router/route_diff.py "$W/s${S}_c.kicad_pcb" "$W/s${S}_d.kicad_pcb" --nets '/D+' '/D-' \
    --track-width 0.15 --diff-pair-gap 0.2 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --quick 2 || exit 15
$PY py_router/route.py "$W/s${S}_d.kicad_pcb" "$W/s${S}_fast_w.kicad_pcb" --nets '*' --quick 2 \
    --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 \
    --power-nets GND +5V +3.3V --power-nets-widths 0.3 0.4 0.3 --layer-costs 1.0 3.0 \
    --json-out "$W/route.json" || echo "route.py exit $?"
$PY py_router/copy_board.py "$W/s${S}_fast_w.kicad_pcb" "$R/s${S}_fast.kicad_pcb" || exit 17
$PY py_tools/quick_score.py "$R/s${S}_fast.kicad_pcb" --route "$W/route.json" --json "$R/s${S}_fast.score.json"
date -u +"END %H:%M:%S"
} > "$W/chain.log" 2>&1
echo "seed $S done: $(grep -E '^blocking=' "$W/chain.log")"
