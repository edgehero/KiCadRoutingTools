#!/bin/zsh
# Experimental full-route chain variants (diagnosis of the impedance component), repo CLIs only.
# usage: helpers/exp_chain.sh <placed board> <out dir> <fanout: stub|underpad|none> <layer costs "1.0 6.0 1.0 2.5 3.0 1.0"> [pour flags...]
set -u
D=wk/gp14/08_CM5_MINIMA_3
IN=$1; E=$2; FAN=$3; LC=(${=4}); shift 4; POUR=("$@")
mkdir -p $E
export PATH="$HOME/.venvs/krt/bin:$PATH"
export KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'
L=(--layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs $LC)
P=(--power-nets GND +5V +3V3_PI VBUS_USB2.0 HDMI_+5V M2_3V3 /PCIe-M2/M2_LX +1V8 +BATT --power-nets-widths 0.25 0.4 0.25 0.5 0.3 0.6 0.6 0.2 0.2)
IMP=('/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*')
echo "start $(date -u +%T) $E fan=$FAN lc=$LC pour=$POUR"
python3 -X utf8 py_router/copy_board.py $IN $E/s0.kicad_pcb > /dev/null 2>&1 || exit 11
python3 -X utf8 py_router/route_planes.py $E/s0.kicad_pcb $E/s1.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu $POUR > $E/s1.log 2>&1 || exit 12
cur=$E/s1.kicad_pcb
if [ $FAN != none ]; then
  extra=(); [ $FAN = underpad ] && extra=(--allow-via-in-pad --via-size 0.25 --via-drill 0.15) || extra=(--via-size 0.3 --via-drill 0.15)
  python3 -X utf8 py_router/qfn_fanout.py $cur --output $E/s2a.kicad_pcb --component Module302 --nets ${(f)"$(<$D/work/fan_Module302.lst)"} --escape-method $FAN $extra --width 0.1 > $E/s2a.log 2>&1 || exit 13
  python3 -X utf8 py_router/qfn_fanout.py $E/s2a.kicad_pcb --output $E/s2b.kicad_pcb --component Module301 --nets ${(f)"$(<$D/work/fan_Module301.lst)"} --escape-method $FAN $extra --width 0.1 > $E/s2b.log 2>&1 || exit 14
  python3 -X utf8 py_placer/place_fanout_clearance.py $E/s2b.kicad_pcb $E/s3.kicad_pcb --clearance 0.13 --intent $D/r2/intent.json > $E/s3.log 2>&1 || exit 15
  cur=$E/s3.kicad_pcb
fi
python3 -X utf8 -u py_router/route_diff.py $cur $E/s4.kicad_pcb --nets '/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' --impedance 90 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 $L > $E/s4.log 2>&1 || exit 16
python3 -X utf8 -u py_router/route_diff.py $E/s4.kicad_pcb $E/s5.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 $L > $E/s5.log 2>&1 || exit 17
python3 -X utf8 -u py_router/route.py $E/s5.kicad_pcb $E/route.kicad_pcb --nets '*' --no-bga-zones --max-ripup 5 --track-width 0.1 --clearance-ceiling 0.13 $P $L --json-out $E/route.json > $E/route.log 2>&1
echo "route exit $? $(date -u +%T)"
grep JSON_SUMMARY_MIN $E/route.log | grep -o '"failed": [0-9]*\|"routed": [0-9]*\|"vias": [0-9]*'
python3 -X utf8 py_tools/check_impedance.py $E/route.kicad_pcb --nets $IMP --json $E/imp.json > $E/imp.log 2>&1
grep -E "Nets with a crossing|Total crossings|Length over void" $E/imp.log
python3 -X utf8 py_tools/board_score.py $E/route.kicad_pcb --intent $D/r2/intent.json --baseline $D/CM5_MINIMA_3.kicad_pcb --impedance-nets $IMP --json $E/score.json > $E/score.log 2>&1
grep '^BLOCKING' $E/score.log
