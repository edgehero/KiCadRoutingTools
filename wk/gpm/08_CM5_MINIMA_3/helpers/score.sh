#!/bin/bash
# board_score with every spec flag this board declares (impedance classes, via floor). usage: score.sh BOARD OUT.json
cd ~/Documents/git/krt-gpm
R=wk/gpm/08_CM5_MINIMA_3
python3 -X utf8 py_tools/board_score.py "$1" --intent $R/intent_run.json --baseline $R/fixed.kicad_pcb \
  --impedance-nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK*' '/CM5/DPHY0_P.*' '/CM5/PCIE_PI.CLK_*' '/CM5/PCIE_PI.RX_*' '/CM5/PCIE_PI.TX_*' '/CM5/USB2P.D_*' '/USB_C.D_*' \
  --min-via-diameter 0.45 --min-via-drill 0.3 --json "$2"
