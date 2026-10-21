#!/bin/bash
# Fast judging route of one placed seed (plan-pcb-placement §3.6 steps 1-2).
# No repo tool runs the skill's judging chain over the seeds place_simple
# names, so this hand-writes it (TOOL_GAPS: "no judge runner").
# usage: helpers/judge_chain.sh <run dir> <round N> <seed S>   (run from WT)
set -u
W=$1; N=$2; S=$3
R=$W/r$N; D=$R/s${S}_route
export PATH="$HOME/.venvs/krt/bin:$PATH"
mkdir -p $D
LAYERS="F.Cu In1.Cu In2.Cu B.Cu"
PAIRS=('/DRAM/DRAM_DQS0_*' '/DRAM/DRAM_DQS1_*' '/DRAM/DRAM_CLK0_*')
T0=$(date +%s)
python3 -X utf8 py_router/copy_board.py $R/s$S.kicad_pcb $D/in.kicad_pcb > $D/copy.log 2>&1 || exit 11
python3 -X utf8 py_router/route_planes.py $D/in.kicad_pcb $D/p1.kicad_pcb --nets GND +3V3 \
    --plane-layers In1.Cu In2.Cu --skip-existing-zones > $D/p1.log 2>&1 || exit 12
python3 -X utf8 py_router/bga_fanout.py $D/p1.kicad_pcb --component U1 --nets '*' '!GND' '!+3V3' \
    --layers $LAYERS --layer-costs 1.0 -1 1.5 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 \
    --track-width 0.1 --clearance 0.1 --diff-pairs "${PAIRS[@]}" --diff-pair-gap 0.1 \
    --output $D/f1.kicad_pcb > $D/f1.log 2>&1 || exit 13
python3 -X utf8 py_router/bga_fanout.py $D/f1.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' \
    --layers $LAYERS --layer-costs 1.0 -1 1.5 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 \
    --track-width 0.1 --clearance 0.1 --diff-pairs "${PAIRS[@]}" --diff-pair-gap 0.1 \
    --output $D/f2.kicad_pcb > $D/f2.log 2>&1 || exit 14
python3 -X utf8 py_placer/place_fanout_clearance.py $D/f2.kicad_pcb $D/c1.kicad_pcb --clearance 0.1 \
    --intent $R/intent.json > $D/c1.log 2>&1 || exit 15
python3 -X utf8 py_router/route_diff.py $D/c1.kicad_pcb $D/d1.kicad_pcb --nets "${PAIRS[@]}" \
    --track-width 0.1 --diff-pair-gap 0.1 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 \
    --layers $LAYERS --layer-costs 1.0 6.0 1.5 1.0 --no-bga-zones --quick 2 > $D/d1.log 2>&1 || exit 16
python3 -X utf8 -u py_router/route.py $D/d1.kicad_pcb $D/r1.kicad_pcb --nets '*' --track-width 0.1 \
    --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers $LAYERS --layer-costs 1.0 6.0 1.5 1.0 \
    --no-bga-zones --max-ripup 5 \
    --power-nets GND +3V3 +5V +1V2 VMEM '/SOC Power/VDD_SOC_CAP' '/SOC Power/VDD_ARM_SOC_IN' \
      '/SOC Power/VDD_ARM_CAP' '/SOC Power/VDD_HIGH_IN' '/SOC Power/VDD_HIGH_CAP' '/SOC Power/VDD_SNVS_IN' \
      '/SOC Power/*_SW' \
    --power-nets-widths 0.2 0.2 0.4 0.3 0.2 0.15 0.2 0.15 0.2 0.15 0.15 0.4 \
    --quick 2 --json-out $D/route.json > $D/r1.log 2>&1 || exit 17
python3 -X utf8 py_router/copy_board.py $D/r1.kicad_pcb $R/s${S}_fast.kicad_pcb > $D/copy2.log 2>&1 || exit 18
python3 -X utf8 py_tools/quick_score.py $R/s${S}_fast.kicad_pcb --route $D/route.json \
    --json $R/s${S}_fast.score.json > $D/score.log 2>&1
echo "seed $S chain done in $(( $(date +%s) - T0 )) s, quick_score exit $?"
