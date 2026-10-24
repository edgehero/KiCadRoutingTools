#!/bin/zsh
# The §3.8 chain (plan-pcb-routing, followed by hand) parameterised for A/B experiments.
# usage (repo root): zsh helpers/full_chain.sh <placed.kicad_pcb> <outdir> <F.Cu cost> <B.Cu cost> [same-net-pad-clearance=0.1] [zone min-thickness=0.15] ["extra route.py args"]
set -e
cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:$PATH" KICAD_ROUTE_TRACE=1
IN=$1; D=$2; LF=$3; LB=$4; SNP=${5:-0.1}; MT=${6:-0.15}; EXTRA=(${=7})
mkdir -p $D
F=(--track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --power-nets GND +3V3 VBUS +5V +1V8 /VPHY /VPLL Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 0.3 --layer-costs $LF $LB --escalation board --same-net-pad-clearance $SNP $EXTRA)
python3 -X utf8 py_router/copy_board.py $IN $D/in.kicad_pcb > /dev/null
python3 -X utf8 py_router/route_planes.py $D/in.kicad_pcb $D/a1.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --min-thickness $MT > $D/a1.log 2>&1
python3 -X utf8 py_router/route_diff.py $D/a1.kicad_pcb $D/a2.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --same-net-pad-clearance $SNP > $D/a2.log 2>&1
python3 -X utf8 py_router/route.py $D/a2.kicad_pcb $D/a3.kicad_pcb --nets '*' $F --json-out $D/a3.json > $D/a3.log 2>&1
python3 -X utf8 py_router/route.py $D/a3.kicad_pcb $D/a4.kicad_pcb --nets '*' $F --json-out $D/a4.json > $D/a4.log 2>&1
python3 -X utf8 py_router/route.py $D/a4.kicad_pcb $D/a5.kicad_pcb --nets '*' $F --json-out $D/a5.json > $D/a5.log 2>&1
echo CHAIN_DONE
