# Repro: analyze_power_paths counts a sink's current once PER POWER PIN.
# Run from WT: python3 -X utf8 wk/gpm/05_interf_u/repro/power_double_count.py
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole)
comps, pcb = analyze_pcb("wk/gpm/05_interf_u/repro/interf_u_pile.kicad_pcb")
for ref in comps:
    if comps[ref].role == ComponentRole.CURRENT_SINK:
        classify_component(comps, ref, ComponentRole.CURRENT_SINK, current_rating_ma=10)
classify_component(comps, 'BUS1', ComponentRole.POWER_SOURCE, current_rating_ma=100)
sinks = [r for r in comps if comps[r].role == ComponentRole.CURRENT_SINK]
rec = get_power_net_recommendations(pcb, comps, trace_power_paths(pcb, comps))
print(f"{len(sinks)} sinks at 10 mA each = {10*len(sinks)} mA total; source 100 mA")
print("recommended:", rec, "(IPC table: <100 mA -> 0.5 mm, <50 mA -> 0.3 mm)")
