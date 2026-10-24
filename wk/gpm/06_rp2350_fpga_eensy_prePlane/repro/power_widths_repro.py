# Reproduce: analyze_power_paths adds a POWER_SOURCE's rating to the sinks it feeds on the same net,
# and gives every supply net of a sink the sink's whole current.
# run from WT:  python3 -X utf8 wk/gpm/06_rp2350_fpga_eensy_prePlane/repro/power_widths_repro.py
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole as R)
comps, pcb = analyze_pcb("wk/gpm/06_rp2350_fpga_eensy_prePlane/repro/fixed.kicad_pcb")
classify_component(comps, 'U7', R.POWER_SOURCE, current_rating_ma=280)   # 3V3 buck, load 280 mA
classify_component(comps, 'U6', R.CURRENT_SINK, current_rating_ma=150)   # RP2354A
classify_component(comps, 'U2', R.CURRENT_SINK, current_rating_ma=60)
classify_component(comps, 'U1', R.CURRENT_SINK, current_rating_ma=30)
rec = get_power_net_recommendations(pcb, comps, trace_power_paths(pcb, comps))
print(rec)
# Observed: '+3V3' 1.2 mm (the 1-2 A row) although the +3V3 sinks sum to 240 mA and the source
# delivers exactly that; 'Net-(U6-VREG_AVDD)' 0.7 mm for a pin that draws ~200 uA (U6's whole
# 150 mA is charged to each of its supply nets).
