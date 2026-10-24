cd ~/Documents/git/krt-gpm
python3 -X utf8 py_router/route_planes.py wk/gpm/12_steppenprobe/repro/s11.kicad_pcb /tmp/t1.kicad_pcb --nets GND +3V3 --plane-layers B.Cu F.Cu --thermal-relief
python3 -X utf8 py_router/route.py /tmp/t1.kicad_pcb /tmp/t2.kicad_pcb --nets '*' --power-nets GND +3V3 --power-nets-widths 0.7 0.7
# python3 -X utf8 py_router/check_drc.py /tmp/t2.kicad_pcb
# python3 -X utf8 py_router/check_connected.py /tmp/t2.kicad_pcb
# python3 -X utf8 py_tools/check_orphan_stubs.py /tmp/t2.kicad_pcb
