#!/usr/bin/env python3
"""G03 verifier: measure analyze_power_paths' per-net current through its PUBLIC API.

get_power_net_recommendations(min_current_ma=m) includes a non-GND net iff its
accumulated current >= m, so bisecting m recovers the exact accumulated current
for every net (GND-named nets use max(net, total_sink), reported separately).
Then decompose it by (part, role, rating, power pads on that net) to show the
per-pin multiplication and the source-on-top addition.

usage: measure_net_currents.py BOARD 'REF:ROLE:mA' ...
"""
import sys
sys.path[:0] = ['py_tools', 'py_router']
from analyze_power_paths import (analyze_pcb, classify_component, ComponentRole,
                                 trace_power_paths, get_power_net_recommendations,
                                 is_power_pin)

board = sys.argv[1]
c, p = analyze_pcb(board)
for spec in sys.argv[2:]:
    ref, role, ma = spec.split(':')
    classify_component(c, ref, ComponentRole[role], current_rating_ma=float(ma))
paths = trace_power_paths(p, c)
print(f"paths traced: {len(paths)}")
for x in paths:
    print(f"  {x.source_component} -> {x.sink_component} {x.estimated_current_ma} mA via {x.components_in_path} nets {x.nets_in_path}")

base = get_power_net_recommendations(p, c, paths, min_current_ma=0.0)


def measured(net):
    lo, hi = 0.0, 1e7
    for _ in range(80):
        mid = (lo + hi) / 2
        r = get_power_net_recommendations(p, c, paths, min_current_ma=mid)
        if net in r:
            lo = mid
        else:
            hi = mid
    return lo

# contributions from the direct-pin loop (lines 418-439)
contrib = {}
for ref, comp in c.items():
    if comp.role not in (ComponentRole.CURRENT_SINK, ComponentRole.POWER_SOURCE):
        continue
    cur = comp.current_rating_ma or 100.0
    for pad, pt in comp.pin_types.items():
        fn = comp.pin_functions.get(pad, '')
        ok = is_power_pin(fn, pt) or (comp.role == ComponentRole.POWER_SOURCE and pt == 'power_out')
        if not ok:
            continue
        net = comp.net_connections.get(pad, '')
        if not net or 'unconnected' in net.lower():
            continue
        d = contrib.setdefault(net, {})
        k = (ref, comp.role.name, cur)
        d[k] = d.get(k, 0) + 1

total_sink = sum(cc.current_rating_ma or 100.0 for cc in c.values() if cc.role == ComponentRole.CURRENT_SINK)
print(f"\nsum of every CURRENT_SINK's rating (once each): {total_sink:.1f} mA")
print("\nnet | width | accumulated mA (bisected) | contributors: ref role rating x power-pads")
for net, w in sorted(base.items()):
    m = f"{measured(net):.1f}" + (" (GND: =max(net, total_sink))" if 'GND' in net.upper() else '')
    parts = contrib.get(net, {})
    s = ', '.join(f"{r} {ro[:6]} {cu:g}x{n}" for (r, ro, cu), n in sorted(parts.items()))
    pin_sum = sum(cu * n for (r, ro, cu), n in parts.items())
    once = sum(cu for (r, ro, cu), n in parts.items() if ro == 'CURRENT_SINK')
    print(f"{net} | {w} | {m} | pin-sum {pin_sum:g} ; sinks-once {once:g} | {s}")
