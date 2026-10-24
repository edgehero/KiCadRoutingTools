"""Repro (TOOL_GAPS #1): analyze_power_paths drops the 300 mA heater nets.
Run from WT:  python3 -X utf8 wk/gpm/01_ecc83-pp_v2/repro/analyze_power_heater.py
"""
import sys
sys.path.insert(0, "py_tools")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole)
components, pcb = analyze_pcb("wk/gpm/01_ecc83-pp_v2/repro/pile.kicad_pcb")
classify_component(components, 'P4', ComponentRole.POWER_SOURCE, current_rating_ma=300,
                   notes="heater header, ECC83 heater 6.3 V / 300 mA (pins 4+5 tied, pin 9)")
classify_component(components, 'P3', ComponentRole.POWER_SOURCE, current_rating_ma=5, notes="B+")
classify_component(components, 'U1', ComponentRole.CURRENT_SINK, current_rating_ma=300, notes="ECC83")
paths = trace_power_paths(pcb, components)
rec = get_power_net_recommendations(pcb, components, paths)
print("paths:", paths)
print("recommendations:", rec)
missing = [n for n in ("Net-(P4-P1)", "Net-(P4-PM)") if n not in rec]
print("heater nets missing from the recommendations:", missing)
