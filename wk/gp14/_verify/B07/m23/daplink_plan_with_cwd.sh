cd <krt-checkout>
# cwd=<krt-checkout>
export REDO_RUNDIR=wk/gp14/11_daplink/final_route
export REDO_MANIFEST=$REDO_RUNDIR/redo_commands.sh
export KICAD_ROUTE_TRACE=1
# Shipped chain (arm C; arms A and B are final_route_old1/old2, arm C first run final_route_old3): arm B + --same-net-pad-clearance 0.1 (no via in a same-net pad: no IPC-4761 Type VII vias). ARM B was: authored floors held (no clearance flag = Default class 0.2; --fab-tier standard --escalation board --same-net-pad-clearance 0.1), edge clearance 0.55 = the placement margin.
# plan-pcb-routing, by hand, for daplink (2-layer, 35 parts, 50 nets, no stackup).
# Step 5b ledger: route-step exclusions = {} = impedance SE set {} (no stackup -> no impedance pass);
#   poured nets {GND} are all in the route step's --power-nets {GND, +5V, +3.3V}.
#   route_exclusions = set(); impedance_se = set(); plane_nets = {"GND"}; power_nets = {"GND", "+5V", "+3.3V"}
#   assert not (route_exclusions ^ impedance_se); assert not (plane_nets - power_nets)
# Step 0 input: the kept placement r1/s3 (round 1, seed 3, scattered), copied with its project.
python3 -X utf8 py_router/copy_board.py wk/gp14/11_daplink/r1/s3.kicad_pcb wk/gp14/11_daplink/final_route/daplink_in.kicad_pcb
# Step 1: bare GND pour on B.Cu (light-signal 2-layer MCU board: plane first, the judging chain's order)
python3 -X utf8 py_router/route_planes.py wk/gp14/11_daplink/final_route/daplink_in.kicad_pcb wk/gp14/11_daplink/final_route/step1_pour.kicad_pcb --nets GND --plane-layers B.Cu --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1
# Step 1b: QFP fanout of U2 (LQFP-48, 0.5 mm pitch, 48 pads), every net but the poured one
python3 -X utf8 py_router/qfn_fanout.py wk/gp14/11_daplink/final_route/step1_pour.kicad_pcb --output wk/gp14/11_daplink/final_route/step1b_fanout.kicad_pcb --component U2 --nets '*' '!GND' --width 0.127 --clearance 0.2 --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1
# Step 1c: one cap pass after the last fanout
python3 -X utf8 py_placer/place_fanout_clearance.py wk/gp14/11_daplink/final_route/step1b_fanout.kicad_pcb wk/gp14/11_daplink/final_route/step1c_caps.kicad_pcb --clearance 0.2 --intent wk/gp14/11_daplink/intent_edges.json
# Step 2a: the USB full-speed pair (no impedance: default stackup, 12 Mbit/s); gap floored at the 0.2 clearance
python3 -X utf8 py_router/route_diff.py wk/gp14/11_daplink/final_route/step1c_caps.kicad_pcb wk/gp14/11_daplink/final_route/step2a_diff.kicad_pcb --nets '/D+' '/D-' --track-width 0.15 --diff-pair-gap 0.2 --via-size 0.5 --via-drill 0.3 --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1
# Step 2: route ALL nets, GND included (pour-launch + in-run plane finalize)
python3 -X utf8 py_router/route.py wk/gp14/11_daplink/final_route/step2a_diff.kicad_pcb wk/gp14/11_daplink/final_route/step2_route.kicad_pcb --nets '*' --track-width 0.127 --via-size 0.5 --via-drill 0.3 --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1 --power-nets GND +5V +3.3V --power-nets-widths 0.3 0.4 0.3 --layer-costs 1.0 3.0 --json-out wk/gp14/11_daplink/final_route/step2_route.json
# Step 2d: two guided iterations at the Step 2 flag string, verbatim
python3 -X utf8 py_router/route.py wk/gp14/11_daplink/final_route/step2_route.kicad_pcb wk/gp14/11_daplink/final_route/step2_iter1.kicad_pcb --nets '*' --track-width 0.127 --via-size 0.5 --via-drill 0.3 --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1 --power-nets GND +5V +3.3V --power-nets-widths 0.3 0.4 0.3 --layer-costs 1.0 3.0 --json-out wk/gp14/11_daplink/final_route/step2_iter1.json
python3 -X utf8 py_router/route.py wk/gp14/11_daplink/final_route/step2_iter1.kicad_pcb wk/gp14/11_daplink/final_route/step2_iter2.kicad_pcb --nets '*' --track-width 0.127 --via-size 0.5 --via-drill 0.3 --board-edge-clearance 0.55 --fab-tier standard --escalation board --same-net-pad-clearance 0.1 --power-nets GND +5V +3.3V --power-nets-widths 0.3 0.4 0.3 --layer-costs 1.0 3.0 --json-out wk/gp14/11_daplink/final_route/step2_iter2.json
# Verify (commented on purpose):
# python3 -X utf8 py_router/check_drc.py wk/gp14/11_daplink/final_route/step2_iter2.kicad_pcb --baseline wk/gp14/11_daplink/daplink.kicad_pcb --clearance-margin 0.1
# python3 -X utf8 py_router/check_connected.py wk/gp14/11_daplink/final_route/step2_iter2.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gp14/11_daplink/final_route/step2_iter2.kicad_pcb
