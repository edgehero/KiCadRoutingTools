"""Repro (TOOL_GAPS): analyze_power_paths never traces the 30 A motor path through the FET bridge.
Run from WT:  python3 -X utf8 wk/gpm/15_am32_esc/repro/power_paths_repro.py
Classifies the parts the way analyze-power-nets Step 3 asks (battery pads J1 = 30 A source, fuse, shunt and
the six FETs = 30 A pass-through, phase pads J2 = 30 A sink) and prints the recommendations."""
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole as R)
components, pcb = analyze_pcb("wk/gpm/15_am32_esc/repro/am32_esc_input.kicad_pcb")
c = lambda ref, role, ma=None: classify_component(components, ref, role, current_rating_ma=ma, notes="")
c('J1', R.POWER_SOURCE, 30000); c('R11', R.PASS_THROUGH, 30000); c('RSHUNT1', R.PASS_THROUGH, 30000)
for q in ('Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6'): c(q, R.PASS_THROUGH, 30000)
c('J2', R.CURRENT_SINK, 30000); c('J5', R.SHUNT)
c('U4', R.POWER_SOURCE, 100); c('U5', R.POWER_SOURCE, 100)
paths = trace_power_paths(pcb, components)
rec = get_power_net_recommendations(pcb, components, paths)
print("paths reaching J2:", [p for p in paths if 'J2' in str(p)])
print("recommendations:", rec)
print("phase nets recommended:", {k: v for k, v in rec.items() if 'VS' in k} or "NONE")
