# analyze-power-nets skill Steps 1-5 on the fixed board, with the classifications used in this run
import sys; sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
    get_power_net_recommendations, ComponentRole as CR)
components, pcb_data = analyze_pcb("wk/gpm/20_sam9g25/repro/fixed.kicad_pcb")
C = classify_component
C(components,'J2',CR.POWER_SOURCE,current_rating_ma=1000); C(components,'J3',CR.POWER_SOURCE,current_rating_ma=500)
C(components,'D2',CR.PASS_THROUGH,current_rating_ma=500); C(components,'Q1',CR.PASS_THROUGH,current_rating_ma=1000)
C(components,'U2',CR.POWER_SOURCE,current_rating_ma=1000); C(components,'U1',CR.CURRENT_SINK,current_rating_ma=250)
C(components,'U200',CR.CURRENT_SINK,current_rating_ma=150); C(components,'U6',CR.CURRENT_SINK,current_rating_ma=170)
C(components,'U5',CR.CURRENT_SINK,current_rating_ma=25); C(components,'J1',CR.CURRENT_SINK,current_rating_ma=100)
C(components,'J6',CR.CURRENT_SINK,current_rating_ma=100); C(components,'D4',CR.CURRENT_SINK,current_rating_ma=20)
for r in ['J4','J5','J7','AE1','C217','H1','H2','H4','TP4','TP6','TP7','TP8','TP9','Y1','Y2']:
    C(components, r, CR.SHUNT)
paths = trace_power_paths(pcb_data, components)
print('paths traced:', len(paths))
print(get_power_net_recommendations(pcb_data, components, paths))
