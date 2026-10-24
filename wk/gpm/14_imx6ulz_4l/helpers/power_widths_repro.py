"""Reproduce analyze-power-nets' width recommendations for imx6ulz_4l (TOOL_GAPS entry).
Run from WT: python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/power_widths_repro.py wk/gpm/14_imx6ulz_4l/repro/pile.kicad_pcb
Applies the same classifications the run used (SKILL Step 3d) and prints the recommendation table."""
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole as S)
components, pcb = analyze_pcb(sys.argv[1])
C = classify_component
C(components, 'J1', S.POWER_SOURCE, current_rating_ma=1000, notes='+5V input header')
for r in ('J2', 'J3', 'J5', 'J6', 'J7', 'C36', 'H1', 'H2', 'H3', 'H4', 'Y1'):
    C(components, r, S.SHUNT)
C(components, 'J4', S.CURRENT_SINK, current_rating_ma=100)
C(components, 'U1', S.CURRENT_SINK, current_rating_ma=650)
C(components, 'U2', S.CURRENT_SINK, current_rating_ma=200)
for r in ('U4', 'U5', 'U6'):
    C(components, r, S.POWER_SOURCE, current_rating_ma=1000)
C(components, 'U8', S.POWER_SOURCE, current_rating_ma=250)
C(components, 'U7', S.CURRENT_SINK, current_rating_ma=1)
paths = trace_power_paths(pcb, components)
rec = get_power_net_recommendations(pcb, components, paths)
print(f"{len(paths)} paths")
for p in paths:
    print(' ', p.source if hasattr(p, 'source') else '', '->', getattr(p, 'sink', ''), getattr(p, 'current_ma', ''), getattr(p, 'nets', ''))
for n, w in sorted(rec.items()):
    print(f"  {n:45s} {w}")
