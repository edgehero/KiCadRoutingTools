# Counterfactual: honour the stashed exact-name rip overrides in every
# protection_map() call (plane finalize + nested sub-runs), then run route.py.
import sys, os, runpy
sys.path.insert(0, os.path.join(os.getcwd(), 'py_router'))
import protected_nets as pn
_orig = pn.protection_map
def _pm(pcb_data, input_file=None):
    m = _orig(pcb_data, input_file)
    ov = pn.rip_override_names(pcb_data)
    for n in list(m):
        if n in ov and not pn.never_lifts(m[n]):
            m.pop(n)
    return m
pn.protection_map = _pm
sys.argv = ['py_router/route.py'] + sys.argv[1:]
runpy.run_path('py_router/route.py', run_name='__main__')
