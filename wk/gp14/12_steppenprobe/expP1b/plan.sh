cd <krt-checkout>
# Routing plan v3 for wk/gp14/12_steppenprobe/expP1b/placed.kicad_pcb (2-layer, 84 parts, STANDARD tier).
# v1 (final_route_old1/): default --escalation fab / --fab-tier auto went below the board's declared floors (0.3 mm vias).
# v2 (final_route_old2/): floors held, but +1V8 (U1 pin 12) lost its corridor to /RESET_N and /ACT_LED_N; the pin is PASSABLE
#   before routing (check_reachability margin +0.43 mm), so v3 routes +1V8 first (failed-first split, Diagnose and Retry).
# Step 5b ledger: route_exclusions = {} == impedance_se = {}; plane_nets {GND, +3V3} are in the route step's --power-nets.
python3 -X utf8 py_router/route_planes.py wk/gp14/12_steppenprobe/expP1b/placed.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step1.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --fab-tier standard
python3 -X utf8 py_router/qfn_fanout.py wk/gp14/12_steppenprobe/expP1b/step1.kicad_pcb --component U1 --nets '*' '!GND' '!+3V3' '!+1V8' '!/VPHY' '!/VPLL' --output wk/gp14/12_steppenprobe/expP1b/step1b.kicad_pcb --clearance 0.15 --track-width 0.15 --escalation board --fab-tier standard
python3 -X utf8 py_placer/place_fanout_clearance.py wk/gp14/12_steppenprobe/expP1b/step1b.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step1c.kicad_pcb --clearance 0.15 --intent wk/gp14/12_steppenprobe/intent.json
python3 -X utf8 py_router/route_diff.py wk/gp14/12_steppenprobe/expP1b/step1c.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step2a.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --escalation board --fab-tier standard
# Step 2, failed-first split: +1V8 alone (poured nets carried), then all nets
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/expP1b/step2a.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step2.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/expP1b/step2.json
# Step 2d: two iterations, same flag string
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/expP1b/step2.kicad_pcb wk/gp14/12_steppenprobe/expP1b/iter1.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/expP1b/iter1.json
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/expP1b/iter1.kicad_pcb wk/gp14/12_steppenprobe/expP1b/iter2.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/expP1b/iter2.json
# Step 3: GND return vias (USB 2.0 HS pair = high tier), then the closing route.py
python3 -X utf8 py_router/route_planes.py wk/gp14/12_steppenprobe/expP1b/iter2.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step4.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --add-gnd-vias --gnd-via-distance 3.0 --fab-tier standard
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/expP1b/step4.kicad_pcb wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb --nets GND +3V3 --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/expP1b/step4b.json
# Verify (commented; run by hand):
# python3 -X utf8 py_router/check_drc.py wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb
# python3 -X utf8 py_router/check_connected.py wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb
