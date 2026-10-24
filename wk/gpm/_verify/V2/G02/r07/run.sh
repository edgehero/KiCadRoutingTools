#!/bin/bash
# Same route.py args twice: s3_diff -> p1, then p1 -> p2 (fixpoint test).
cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
V=wk/gpm/_verify/V2/G02/r07
ARGS=(--nets '*' --track-width 0.15 --via-size 0.608 --via-drill 0.508 --clearance-ceiling 0.1 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --max-ripup 5 --via-cost 150 --escalation board --same-net-pad-clearance 0.1 --power-nets GND PGND +3V3 +5V +5VBAT +5VUSB /VMUX /Solar_module/Solar+ /Solar_module/VBAT /Solar_module/SYS 'Net-(U5-PMID)' /Solar_module/SW1 /Solar_module/SW2 'Net-(U6-EN)' 'Net-(U6-SW)' 'Net-(U2-SW)' /Battery_holder/VBAT+ 'Net-(F2-Pad2)' BAT- 'Net-(C24-Pad2)' 'Net-(Q1-D)' /VOUT1 /VOUT2 /VOUT3 /VOUT4 /VOUT5 /VOUT6 --power-nets-widths 0.5 0.7 0.7 1.0 1.0 0.7 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 0.7 0.7 0.7 0.7 0.7 0.7)
python3 -u -X utf8 py_router/route.py $V/s3_diff.kicad_pcb $V/p1.kicad_pcb "${ARGS[@]}" --json-out $V/p1.json > $V/p1.log 2>&1 || echo "p1 rc=$?"
python3 -u -X utf8 py_router/route.py $V/p1.kicad_pcb $V/p2.kicad_pcb "${ARGS[@]}" --json-out $V/p2.json > $V/p2.log 2>&1 || echo "p2 rc=$?"
for f in p1 p2; do echo "== $f"; python3 -X utf8 py_router/check_weird.py $V/$f.kicad_pcb 2>&1 | grep -E "FOUND|^  [a-z-]+: [1-9]|NO WEIRD|^    net"; grep -E "^JSON_SUMMARY_MIN" $V/$f.log | cut -c1-200; done
