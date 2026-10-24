#!/usr/bin/env python3
"""G34 verifier: audit every traced path for (a) a regulator crossed INPUT->OUTPUT
while walking from the sink toward the source (i.e. downstream into another
branch), (b) the sink's own-rail source being skipped, (c) paths per sink.

usage: paths_audit.py BOARD 'REF:ROLE:mA' ...
"""
import sys
from collections import Counter
sys.path[:0] = ['py_tools', 'py_router']
from analyze_power_paths import (analyze_pcb, classify_component, ComponentRole,
                                 trace_power_paths)

board = sys.argv[1]
c, p = analyze_pcb(board)
for spec in sys.argv[2:]:
    ref, role, ma = spec.split(':')
    classify_component(c, ref, ComponentRole[role], current_rating_ma=float(ma))

# regulator out/in nets exactly as trace_power_paths derives them (lines 262-289)
reg = {}
for ref, comp in c.items():
    if comp.role != ComponentRole.POWER_SOURCE:
        continue
    outs, ins = set(), set()
    for pad, pt in comp.pin_types.items():
        net = comp.net_connections.get(pad, '')
        fn = comp.pin_functions.get(pad, '').upper()
        if pt == 'power_out' or fn in ('OUT', 'VOUT', 'OUTPUT'):
            outs.add(net)
        elif fn in ('IN', 'VIN', 'INPUT'):
            ins.add(net)
    if outs and ins:
        reg[ref] = (outs, ins)
print('regulators with out->in adjacency:', {r: (sorted(o), sorted(i)) for r, (o, i) in reg.items()})

paths = trace_power_paths(p, c)
print(f'paths: {len(paths)}')
per_sink = Counter(x.sink_component for x in paths)
print('paths per sink:', dict(per_sink))
bad = 0
for x in paths:
    # trace_power_paths reverses its reconstruction, so nets_in_path runs
    # SINK ... SOURCE and components_in_path likewise (sink side first)
    nets = list(x.nets_in_path)
    comps = list(x.components_in_path)
    flags = []
    for i, cref in enumerate(comps):
        if cref in reg:
            a, b = nets[i], nets[i + 1]      # sink-side net, source-side net
            outs, ins = reg[cref]
            if a in ins and b in outs:
                flags.append(f'{cref} crossed IN({a})->OUT({b}) walking upstream = downstream into another branch')
    own = [r for r, (o, i) in reg.items() if nets[0] in o]
    if own and x.source_component not in own:
        flags.append(f'sink rail {nets[0]} is the OUTPUT of {own}, never credited (line 343 skips the sink net)')
    if flags:
        bad += 1
    print(f"  {x.source_component} -> {x.sink_component} {x.estimated_current_ma:g} mA nets {x.nets_in_path} via {x.components_in_path}" + (f"  <-- {'; '.join(flags)}" if flags else ''))
print(f'paths flagged: {bad} of {len(paths)}')
