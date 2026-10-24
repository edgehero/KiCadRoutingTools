"""Repro for TOOL_GAPS: analyze_power_paths traces power BACKWARD through LDO outputs.

Run from the worktree root:
    python3 -X utf8 wk/gpm/10_glasgow_revC/repro/power_paths_repro.py
It classifies the board's parts as the analyze-power-nets skill (Step 3d) asks,
then prints the traced paths that run from one regulator's OUTPUT, back through
the +5V INPUT net, into another regulator's output rail, and the widths.
"""
import sys
sys.path.insert(0, "py_tools")
sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
                                 get_power_net_recommendations, ComponentRole as R)

components, pcb = analyze_pcb("wk/gpm/10_glasgow_revC/repro/fixed.kicad_pcb")


def C(ref, role, ma=None):
    if ma is None:
        classify_component(components, ref, role)
    else:
        classify_component(components, ref, role, current_rating_ma=ma)


C('J1', R.POWER_SOURCE, 500)
C('U15', R.PASS_THROUGH, 500)
C('U8', R.POWER_SOURCE, 500)
C('U36', R.POWER_SOURCE, 300)
C('U14', R.POWER_SOURCE, 150)
C('U31', R.POWER_SOURCE, 150)
C('U1', R.CURRENT_SINK, 85)
C('U30', R.CURRENT_SINK, 100)
paths = trace_power_paths(pcb, components)
rec = get_power_net_recommendations(pcb, components, paths)
for p in paths:
    txt = str(p)
    if 'U14' in txt and 'U30' in txt or 'U36' in txt and 'U14' in txt:
        print(txt[:400])
print(rec)
