"""Repro (TOOL_GAPS #power): analyze_power_paths sums every sink->source path,
including paths traced BACKWARDS through regulators, so a 350 mA board gets
2.0 mm +3V3/GND recommendations. Run from WT:
    python3 -X utf8 wk/gpm/13_pico_ice_rev3/repro/power_paths_repro.py
"""
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole as R)
components, pcb = analyze_pcb("wk/gpm/13_pico_ice_rev3/repro/pile.kicad_pcb")
for ref, role, ma in [('J1', R.POWER_SOURCE, 500), ('J3', R.POWER_SOURCE, 500),
                      ('U4', R.POWER_SOURCE, 300), ('U1', R.POWER_SOURCE, 300),
                      ('U3', R.CURRENT_SINK, 100), ('U6', R.CURRENT_SINK, 50),
                      ('U2', R.CURRENT_SINK, 25), ('U8', R.CURRENT_SINK, 25),
                      ('U5', R.CURRENT_SINK, 40), ('D5', R.PASS_THROUGH, 500),
                      ('PTC1', R.PASS_THROUGH, 350), ('D4', R.PASS_THROUGH, 40),
                      ('D1', R.PASS_THROUGH, 10), ('SJ4', R.PASS_THROUGH, 50),
                      ('SJ5', R.PASS_THROUGH, 30)]:
    classify_component(components, ref, role, current_rating_ma=ma)
paths = trace_power_paths(pcb, components)
for p in paths:
    print(p)
print(get_power_net_recommendations(pcb, components, paths))
