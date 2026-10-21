cd <krt-checkout>
# Routing plan v5 (shipped) for wk/gp14/12_steppenprobe/final_route/placed.kicad_pcb (2-layer, 84 parts, STANDARD tier).
# History: v1 (final_route_old1/) default --escalation fab/--fab-tier auto went below the board's declared floors;
# v2 (old2/) floors held, +1V8 (U1.12) lost its corridor; v3 (old3/) +1V8 routed first -> first DONE, 138 vias;
# v4 (old4/) best of 14 variants (--layer-costs 1.0 6.0, --max-ripup 5, +1V8 out of the U1 fanout): 110 vias, but the
#   verifier FAILED it: the project's Power class (0.3 mm: +1V8 +3V3 +5V /VPHY /VPLL GND VBUS Vdrive) was overridden by --track-width.
# v5 = v4 with all 8 Power-class nets in --power-nets at 0.3 and /VPHY /VPLL also kept out of the 0.15 mm U1 fanout.
# Step 5b ledger: route_exclusions = {} == impedance_se = {}; plane_nets {GND, +3V3} are in the route step's --power-nets.
python3 -X utf8 py_router/route_planes.py wk/gp14/12_steppenprobe/final_route/placed.kicad_pcb wk/gp14/12_steppenprobe/final_route/step1.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --fab-tier standard
python3 -X utf8 py_router/qfn_fanout.py wk/gp14/12_steppenprobe/final_route/step1.kicad_pcb --component U1 --nets '*' '!GND' '!+3V3' '!+1V8' '!/VPHY' '!/VPLL' --output wk/gp14/12_steppenprobe/final_route/step1b.kicad_pcb --clearance 0.15 --track-width 0.15 --escalation board --fab-tier standard
python3 -X utf8 py_placer/place_fanout_clearance.py wk/gp14/12_steppenprobe/final_route/step1b.kicad_pcb wk/gp14/12_steppenprobe/final_route/step1c.kicad_pcb --clearance 0.15 --intent wk/gp14/12_steppenprobe/intent.json
python3 -X utf8 py_router/route_diff.py wk/gp14/12_steppenprobe/final_route/step1c.kicad_pcb wk/gp14/12_steppenprobe/final_route/step2a.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --escalation board --fab-tier standard
# Step 2: all nets, plane nets included
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/final_route/step2a.kicad_pcb wk/gp14/12_steppenprobe/final_route/step2.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/final_route/step2.json
# Step 2d: two iterations, same flag string
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/final_route/step2.kicad_pcb wk/gp14/12_steppenprobe/final_route/iter1.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/final_route/iter1.json
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/final_route/iter1.kicad_pcb wk/gp14/12_steppenprobe/final_route/iter2.kicad_pcb --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/final_route/iter2.json
# Step 3: GND return vias (USB 2.0 HS pair = high tier), then the closing route.py
python3 -X utf8 py_router/route_planes.py wk/gp14/12_steppenprobe/final_route/iter2.kicad_pcb wk/gp14/12_steppenprobe/final_route/step4.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --add-gnd-vias --gnd-via-distance 3.0 --fab-tier standard
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/final_route/step4.kicad_pcb wk/gp14/12_steppenprobe/final_route/step4b.kicad_pcb --nets GND +3V3 --power-nets GND +3V3 +5V VBUS +1V8 Vdrive /VPHY /VPLL --power-nets-widths 0.3 0.3 0.3 0.3 0.3 0.3 0.3 0.3 --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 6.0 --max-ripup 5 --escalation board --fab-tier standard --json-out wk/gp14/12_steppenprobe/final_route/step4b.json
# Verify (commented; run by hand):
# python3 -X utf8 py_router/check_drc.py wk/gp14/12_steppenprobe/final_route/step4b.kicad_pcb
# python3 -X utf8 py_router/check_connected.py wk/gp14/12_steppenprobe/final_route/step4b.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gp14/12_steppenprobe/final_route/step4b.kicad_pcb
