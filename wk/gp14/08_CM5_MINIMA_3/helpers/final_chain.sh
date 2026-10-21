#!/bin/zsh
# The DONE chain (final_route v2) as one script, for optimisation trials. Repo CLIs + the two
# workaround helpers (drop_zone.py, clean_copper.py auto-trim not available: dangling tails are reported).
# usage: helpers/final_chain.sh <placed board> <out dir> "<extra route_diff args>" "<extra route.py args>"
set -u
D=wk/gp14/08_CM5_MINIMA_3
IN=$1; E=$2; XD=(${=3}); XR=(${=4})
mkdir -p $E
export PATH="$HOME/.venvs/krt/bin:$PATH"
export KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'
L=(--layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0)
P=(--power-nets GND +5V +3V3_PI VBUS_USB2.0 HDMI_+5V M2_3V3 /PCIe-M2/M2_LX +1V8 +BATT --power-nets-widths 0.25 0.4 0.25 0.5 0.3 0.6 0.6 0.2 0.2)
IMP=('/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*')
echo "start $(date -u +%T) $E XD=$XD XR=$XR"
python3 -X utf8 py_router/copy_board.py $IN $E/f0.kicad_pcb > /dev/null 2>&1 || exit 11
python3 -X utf8 $D/helpers/drop_zone.py $E/f0.kicad_pcb $E/f0b.kicad_pcb GND > /dev/null || exit 12
python3 -X utf8 py_router/route_planes.py $E/f0b.kicad_pcb $E/f1.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu > $E/f1.log 2>&1 || exit 13
python3 -X utf8 py_router/qfn_fanout.py $E/f1.kicad_pcb --output $E/f2a.kicad_pcb --component Module302 --nets ${(f)"$(<$D/work/fan_Module302.lst)"} --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1 > $E/f2a.log 2>&1 || exit 14
python3 -X utf8 py_router/qfn_fanout.py $E/f2a.kicad_pcb --output $E/f2b.kicad_pcb --component Module301 --nets ${(f)"$(<$D/work/fan_Module301.lst)"} --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1 > $E/f2b.log 2>&1 || exit 15
python3 -X utf8 py_placer/place_fanout_clearance.py $E/f2b.kicad_pcb $E/f3.kicad_pcb --clearance 0.13 --intent $D/r2/intent.json > $E/f3.log 2>&1 || exit 16
python3 -X utf8 -u py_router/route_diff.py $E/f3.kicad_pcb $E/f4.kicad_pcb --nets '/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' --impedance 90 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.25 --via-drill 0.15 $L $XD > $E/f4.log 2>&1 || exit 17
python3 -X utf8 -u py_router/route_diff.py $E/f4.kicad_pcb $E/f5.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.25 --via-drill 0.15 $L $XD > $E/f5.log 2>&1 || exit 18
python3 -X utf8 -u py_router/route.py $E/f5.kicad_pcb $E/f6.kicad_pcb --nets '*' --no-bga-zones --max-ripup 5 --track-width 0.1 --clearance-ceiling 0.13 $P $L $XR --json-out $E/f6.json > $E/f6.log 2>&1
echo "route exit $? $(date -u +%T)"
python3 -X utf8 $D/helpers/clean_copper.py $E/f6.kicad_pcb $E/f7.kicad_pcb > $E/f7.log 2>&1; cat $E/f7.log
python3 -X utf8 py_router/check_weird.py $E/f7.kicad_pcb 2>&1 | grep -E "FOUND|^  [a-z-]+: [1-9]|NO WEIRD" | tr '\n' ' '; echo
python3 -X utf8 py_tools/board_score.py $E/f7.kicad_pcb --intent $D/r2/intent.json --baseline $D/CM5_MINIMA_3.kicad_pcb --impedance-nets $IMP --json $E/f7.score.json > $E/f7.score.log 2>&1
grep '^BLOCKING' $E/f7.score.log; python3 -c "import json;print(json.load(open('$E/f7.score.json'))['quality'])"
