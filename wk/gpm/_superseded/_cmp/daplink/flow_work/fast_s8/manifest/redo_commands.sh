#!/bin/bash
# synthesized by gpm film_work.py from judge_seeds step order
python3 step.py in.kicad_pcb 1_route_diff.kicad_pcb
python3 step.py 1_route_diff.kicad_pcb 2_route.kicad_pcb
python3 step.py 2_route.kicad_pcb 3_route_planes.kicad_pcb
python3 step.py 3_route_planes.kicad_pcb 4_route.kicad_pcb
