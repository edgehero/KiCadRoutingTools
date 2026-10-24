"""Run route.py with the #230 same-path via guard instrumented (verifier probe, M08)."""
import os, sys, runpy, json
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
import single_ended_routing as ser
log = open(os.environ['GUARD_LOG'], 'w')
_close = ser._path_has_close_vias
_once = ser._probe_route_with_frontier_once
_wrap = ser._probe_route_with_frontier
def close(path, config):
    r = _close(path, config)
    if r:
        cells = [(path[i][0], path[i][1]) for i in range(1, len(path))
                 if path[i][0] == path[i-1][0] and path[i][1] == path[i-1][1] and path[i][2] != path[i-1][2]]
        log.write(json.dumps({'ev': 'close_vias', 'grid': config.grid_step, 'via_cells': cells[:12]}) + '\n'); log.flush()
    return r
def once(*a, **k):
    r = _once(*a, **k)
    if k.get('via_exclusion_radius', 0):
        log.write(json.dumps({'ev': 'guarded_retry', 'ver': k['via_exclusion_radius'], 'connected': r[0] is not None, 'net': a[9] if len(a) > 9 else k.get('current_net_id')}) + '\n'); log.flush()
    return r
ser._path_has_close_vias = close
ser._probe_route_with_frontier_once = once
sys.argv = ['route.py'] + sys.argv[1:]
runpy.run_path(os.path.join(ROOT, 'py_router', 'route.py'), run_name='__main__')
