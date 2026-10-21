cd <krt-checkout>
# interf_u full route (plan-pcb-routing, by hand). 2-layer through-hole ISA board, U9 PGA120 at 2.54 mm (no fanout: THT, Step 3),
# no diff pairs, no impedance nets, low-speed (no GND return vias / stitching, Step 10 rule 10).
# Step 8 "2-Layer Through-Hole Bus Boards" flags; Step 8 dense 2-layer order: signals first on both layers, GND poured LAST on B.Cu
# (the board's own pour layer), and the chain closes on route.py '*' whose in-run finalize welds GND (End every chain on route.py).
# Net coverage (Step 5b): step 1 claims every net but GND; GND is poured (step 2) and claimed by steps 3/4 ('*'); no impedance set.
python3 -X utf8 py_router/copy_board.py wk/gp14/05_interf_u/r3/s7.kicad_pcb wk/gp14/05_interf_u/final_route/placed.kicad_pcb
python3 -X utf8 py_router/route.py wk/gp14/05_interf_u/final_route/placed.kicad_pcb wk/gp14/05_interf_u/final_route/s1_sig.kicad_pcb --nets '*' '!GND' --no-bga-zones --layer-costs 1.0 1.0 --turn-cost 2000 --direction-preference-cost 4000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.6 --power-nets VCC GND --power-nets-widths 0.5 0.5 --clearance-ceiling 0.254 --escalation board --json-out wk/gp14/05_interf_u/final_route/s1_sig.json
python3 -X utf8 py_router/route_planes.py wk/gp14/05_interf_u/final_route/s1_sig.kicad_pcb wk/gp14/05_interf_u/final_route/s2_pour.kicad_pcb --nets GND --plane-layers B.Cu --clearance-ceiling 0.254
python3 -X utf8 py_router/route.py wk/gp14/05_interf_u/final_route/s2_pour.kicad_pcb wk/gp14/05_interf_u/final_route/s3_route.kicad_pcb --nets '*' --no-bga-zones --layer-costs 1.0 1.0 --turn-cost 2000 --direction-preference-cost 4000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.6 --power-nets VCC GND --power-nets-widths 0.5 0.5 --clearance-ceiling 0.254 --escalation board --json-out wk/gp14/05_interf_u/final_route/s3_route.json
python3 -X utf8 py_router/route.py wk/gp14/05_interf_u/final_route/s3_route.kicad_pcb wk/gp14/05_interf_u/final_route/s4_iter1.kicad_pcb --nets '*' --no-bga-zones --layer-costs 1.0 1.0 --turn-cost 2000 --direction-preference-cost 4000 --via-cost 150 --track-width 0.2 --via-size 0.9 --via-drill 0.6 --power-nets VCC GND --power-nets-widths 0.5 0.5 --clearance-ceiling 0.254 --escalation board --json-out wk/gp14/05_interf_u/final_route/s4_iter1.json
# verification (commented, Step 9):
# python3 -X utf8 py_router/check_drc.py wk/gp14/05_interf_u/final_route/s4_iter1.kicad_pcb
# python3 -X utf8 py_router/check_connected.py wk/gp14/05_interf_u/final_route/s4_iter1.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py wk/gp14/05_interf_u/final_route/s4_iter1.kicad_pcb
