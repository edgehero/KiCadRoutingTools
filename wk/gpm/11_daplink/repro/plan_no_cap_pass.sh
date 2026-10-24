cd ~/Documents/git/krt-gpm
python3 -X utf8 py_router/route_planes.py wk/gpm/11_daplink/repro/s10_placed.kicad_pcb wk/gpm/11_daplink/repro/r1.kicad_pcb --nets GND GND --plane-layers F.Cu B.Cu
python3 -X utf8 py_router/qfn_fanout.py wk/gpm/11_daplink/repro/r1.kicad_pcb --component U2 --nets '*' '!GND' --width 0.127 --clearance-ceiling 0.2 --output wk/gpm/11_daplink/repro/r2.kicad_pcb
python3 -X utf8 py_router/route.py wk/gpm/11_daplink/repro/r2.kicad_pcb wk/gpm/11_daplink/repro/r3.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets GND '+5V' '+3.3V' --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0
# python3 -X utf8 py_router/check_drc.py wk/gpm/11_daplink/repro/r3.kicad_pcb
# python3 -X utf8 py_router/check_connected.py wk/gpm/11_daplink/repro/r3.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gpm/11_daplink/repro/r3.kicad_pcb
