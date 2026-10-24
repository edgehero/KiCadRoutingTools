# Reproduces the analyze_power_paths per-power-pin current multiplication.
# Run from WT:  python3 -X utf8 wk/gpm/11_daplink/repro/power_overcount.py
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole)
components, pcb = analyze_pcb("wk/gpm/11_daplink/repro/s10_placed.kicad_pcb")
classify_component(components, 'U2', ComponentRole.CURRENT_SINK, current_rating_ma=50)   # STM32F103CB, 50 mA max IDD
classify_component(components, 'U1', ComponentRole.POWER_SOURCE, current_rating_ma=1000) # AMS1117 1 A rating
classify_component(components, 'P1', ComponentRole.POWER_SOURCE, current_rating_ma=500)  # USB VBUS
paths = trace_power_paths(pcb, components)
print(get_power_net_recommendations(pcb, components, paths))
# U2 alone (50 mA) is counted on +3.3V once per VDD/VBAT/VDDA pin (5x) and on GND once per VSS pin (4x);
# P1's four GND contacts count its 500 mA four times: GND -> 2.0 mm on a ~0.3 A board.
