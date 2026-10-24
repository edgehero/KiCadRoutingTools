#!/bin/zsh
# Width-respecting variant of helpers/full_chain.sh: the power rails route first and the pours are finalised last,
# both with --track-width 0.3 (the Power netclass width), so a neck-down never goes below 0.3; signals route between
# them at 0.15. usage (repo root): zsh helpers/full_chain_w.sh <placed.kicad_pcb> <outdir> <F cost> <B cost> ["extra route.py args"] ["extra route_diff args"]
set -e
cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:$PATH" KICAD_ROUTE_TRACE=1
IN=$1; D=$2; LF=$3; LB=$4; EXTRA=(${=5}); DIFFX=(${=6})
mkdir -p $D
C=(--clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --power-nets GND +3V3 VBUS +5V +1V8 /VPHY /VPLL Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 0.3 --layer-costs $LF $LB --escalation board --same-net-pad-clearance 0.1 $EXTRA)
python3 -X utf8 py_router/copy_board.py $IN $D/in.kicad_pcb > /dev/null
python3 -X utf8 py_router/route_planes.py $D/in.kicad_pcb $D/a1.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --min-thickness 0.15 > $D/a1.log 2>&1
python3 -X utf8 py_router/route_diff.py $D/a1.kicad_pcb $D/a2.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --same-net-pad-clearance 0.1 $DIFFX > $D/a2.log 2>&1
python3 -X utf8 py_router/route.py $D/a2.kicad_pcb $D/a3.kicad_pcb --nets VBUS +5V +1V8 /VPHY /VPLL Vdrive --track-width 0.3 $C --json-out $D/a3.json > $D/a3.log 2>&1
python3 -X utf8 py_router/route.py $D/a3.kicad_pcb $D/a4.kicad_pcb --nets '*' '!GND' '!+3V3' --track-width 0.15 $C --json-out $D/a4.json > $D/a4.log 2>&1
python3 -X utf8 py_router/route.py $D/a4.kicad_pcb $D/a5.kicad_pcb --nets GND +3V3 --track-width 0.3 $C --json-out $D/a5.json > $D/a5.log 2>&1
python3 -X utf8 py_router/route.py $D/a5.kicad_pcb $D/a6.kicad_pcb --nets '*' '!GND' '!+3V3' --track-width 0.15 $C --json-out $D/a6.json > $D/a6.log 2>&1
python3 -X utf8 py_router/route.py $D/a6.kicad_pcb $D/a7.kicad_pcb --nets GND +3V3 --track-width 0.3 $C --json-out $D/a7.json > $D/a7.log 2>&1
echo CHAIN_DONE
