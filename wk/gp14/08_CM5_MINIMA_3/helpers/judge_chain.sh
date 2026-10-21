#!/bin/zsh
# Judging chain (plan-pcb-placement 3.6 step 1) for one placed seed, using only repo CLIs.
# usage: helpers/judge_chain.sh <round dir> <seed>   (run from the worktree root)
# Writes <round>/s<S>_route/*, <round>/s<S>_fast.kicad_pcb (copy_board) and <round>/s<S>_fast.score.json
set -u
D=wk/gp14/08_CM5_MINIMA_3
RD=$1; S=$2
R=$RD/s${S}_route
mkdir -p $R
export PATH="$HOME/.venvs/krt/bin:$PATH"
L=(--layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 6.0 1.0 2.5 3.0 1.0)
P=(--power-nets GND +5V +3V3_PI VBUS_USB2.0 HDMI_+5V M2_3V3 /PCIe-M2/M2_LX +1V8 +BATT --power-nets-widths 0.25 0.4 0.25 0.5 0.3 0.6 0.6 0.2 0.2)
export KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'
echo "chain start $(date -u +%T) $RD s$S"
python3 -X utf8 py_router/copy_board.py $RD/s$S.kicad_pcb $R/s0.kicad_pcb > $R/s0_copy.log 2>&1 || exit 11
python3 -X utf8 py_router/route_planes.py $R/s0.kicad_pcb $R/s1_pour.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu > $R/s1_pour.log 2>&1 || exit 12
python3 -X utf8 py_router/qfn_fanout.py $R/s1_pour.kicad_pcb --output $R/s2_fan302.kicad_pcb --component Module302 --nets ${(f)"$(<$D/work/fan_Module302.lst)"} --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1 > $R/s2_fan302.log 2>&1 || exit 13
python3 -X utf8 py_router/qfn_fanout.py $R/s2_fan302.kicad_pcb --output $R/s2_fan301.kicad_pcb --component Module301 --nets ${(f)"$(<$D/work/fan_Module301.lst)"} --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1 > $R/s2_fan301.log 2>&1 || exit 14
python3 -X utf8 py_placer/place_fanout_clearance.py $R/s2_fan301.kicad_pcb $R/s3_capfix.kicad_pcb --clearance 0.13 --intent $RD/intent.json > $R/s3_capfix.log 2>&1 || exit 15
python3 -X utf8 -u py_router/route_diff.py $R/s3_capfix.kicad_pcb $R/s4_d90.kicad_pcb --nets '/USB_C.D_*' '/CM5/USB2P.D_*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' --impedance 90 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 $L --quick 2 > $R/s4_d90.log 2>&1 || exit 16
python3 -X utf8 -u py_router/route_diff.py $R/s4_d90.kicad_pcb $R/s5_d100.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 $L --quick 2 > $R/s5_d100.log 2>&1 || exit 17
python3 -X utf8 -u py_router/route.py $R/s5_d100.kicad_pcb $R/s6_route.kicad_pcb --nets '*' --no-bga-zones --max-ripup 5 --track-width 0.1 --clearance-ceiling 0.13 $P $L --quick 2 --json-out $R/route.json > $R/s6_route.log 2>&1
rc=$?
echo "route.py exit $rc $(date -u +%T)"
python3 -X utf8 py_router/copy_board.py $R/s6_route.kicad_pcb $RD/s${S}_fast.kicad_pcb > $R/s7_copy.log 2>&1 || exit 18
python3 -X utf8 py_tools/quick_score.py $RD/s${S}_fast.kicad_pcb --route $R/route.json --json $RD/s${S}_fast.score.json > $R/s8_score.log 2>&1
echo "chain done $(date -u +%T) $RD s$S score: $(tail -c 400 $R/s8_score.log)"
