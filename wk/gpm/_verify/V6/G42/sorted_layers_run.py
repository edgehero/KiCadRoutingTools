# Counterfactual: hand the fill-model region discovery its zone_layers in a
# fixed (sorted) order instead of a str set whose order follows PYTHONHASHSEED.
import sys, os, runpy
sys.path.insert(0, os.path.join(os.getcwd(), 'py_router'))
import plane_region_connector as prc
_orig = prc._regions_from_fill_models
def _wrapped(net_id, pcb_data, coord, plane_layer, zone_layers, *a, **k):
    return _orig(net_id, pcb_data, coord, plane_layer, sorted(zone_layers), *a, **k)
prc._regions_from_fill_models = _wrapped
sys.argv = ['py_router/route.py'] + sys.argv[1:]
runpy.run_path('py_router/route.py', run_name='__main__')
