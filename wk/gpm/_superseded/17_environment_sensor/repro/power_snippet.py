# analyze-power-nets steps 1-5 (the skill's own inline code), classifications used in the run.
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
    get_power_net_recommendations, ComponentRole as R)
components, pcb_data = analyze_pcb(sys.argv[1])
c = lambda ref, role, ma: classify_component(components, ref, role, current_rating_ma=ma, notes='')
c('J1', R.POWER_SOURCE, 500); c('U2', R.POWER_SOURCE, 300); c('BAT1', R.POWER_SOURCE, 1)
c('U1', R.CURRENT_SINK, 15); c('U3', R.CURRENT_SINK, 60)
for u in ('U4', 'U5', 'U6'): c(u, R.CURRENT_SINK, 1)
c('J2', R.CURRENT_SINK, 50); c('J3', R.CURRENT_SINK, 50); c('LD1', R.CURRENT_SINK, 6); c('LD2', R.CURRENT_SINK, 3)
for d in ('D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'): c(d, R.SHUNT, 0)
paths = trace_power_paths(pcb_data, components)
for p in paths: print('PATH', p.source_ref if hasattr(p, 'source_ref') else '', p.estimated_current_ma, p.nets_in_path)
print('REC', get_power_net_recommendations(pcb_data, components, paths))
