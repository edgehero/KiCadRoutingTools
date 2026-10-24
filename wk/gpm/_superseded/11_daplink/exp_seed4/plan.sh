cd ~/Documents/git/krt-gpm
# daplink (gpm 11) full route, /plan-pcb-routing followed by hand. 2-layer STANDARD board, dense 2-layer flow (Step 8): signals on both layers at cost 1.0, GND poured LAST on both faces, closing route.py, two iterations (Step 2d).
# Step 2a: USB D+/D- pair (no stackup: no --impedance, Step 10 rule 1)
python3 -X utf8 py_router/route_diff.py wk/gpm/11_daplink/exp_seed4/in.kicad_pcb wk/gpm/11_daplink/exp_seed4/s1_diff.kicad_pcb --nets '/D+' '/D-' --track-width 0.2 --diff-pair-gap 0.2 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 > wk/gpm/11_daplink/exp_seed4/s1_diff.log 2>&1
# Step 2: all signal nets, GND left for the closing step after the pour (Step 8 pour-last)
python3 -X utf8 py_router/route.py wk/gpm/11_daplink/exp_seed4/s1_diff.kicad_pcb wk/gpm/11_daplink/exp_seed4/s2_signal.kicad_pcb --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/exp_seed4/s2_signal.json > wk/gpm/11_daplink/exp_seed4/s2_signal.log 2>&1
# Step 1 (late, 2-layer pour-last): bare GND pour on both faces
python3 -X utf8 py_router/route_planes.py wk/gpm/11_daplink/exp_seed4/s2_signal.kicad_pcb wk/gpm/11_daplink/exp_seed4/s3_pour.kicad_pcb --nets GND GND --plane-layers F.Cu B.Cu > wk/gpm/11_daplink/exp_seed4/s3_pour.log 2>&1
# closing route step: every net, GND included (its in-run plane finalize welds the pour)
python3 -X utf8 py_router/route.py wk/gpm/11_daplink/exp_seed4/s3_pour.kicad_pcb wk/gpm/11_daplink/exp_seed4/s4_route.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/exp_seed4/s4_route.json > wk/gpm/11_daplink/exp_seed4/s4_route.log 2>&1
# Step 2d: two iterations with the same flag string
python3 -X utf8 py_router/route.py wk/gpm/11_daplink/exp_seed4/s4_route.kicad_pcb wk/gpm/11_daplink/exp_seed4/s5_iter1.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/exp_seed4/s5_iter1.json > wk/gpm/11_daplink/exp_seed4/s5_iter1.log 2>&1
python3 -X utf8 py_router/route.py wk/gpm/11_daplink/exp_seed4/s5_iter1.kicad_pcb wk/gpm/11_daplink/exp_seed4/s6_iter2.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --json-out wk/gpm/11_daplink/exp_seed4/s6_iter2.json > wk/gpm/11_daplink/exp_seed4/s6_iter2.log 2>&1
# verification (comments, Step 9):
# python3 -X utf8 py_router/check_drc.py wk/gpm/11_daplink/exp_seed4/s6_iter2.kicad_pcb
# python3 -X utf8 py_router/check_connected.py wk/gpm/11_daplink/exp_seed4/s6_iter2.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gpm/11_daplink/exp_seed4/s6_iter2.kicad_pcb
