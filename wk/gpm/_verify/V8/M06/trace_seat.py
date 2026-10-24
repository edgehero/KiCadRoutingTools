"""Trace every position the edge seat tests for DC1 and the declared-pose check's answer (verifier probe, M06)."""
import os, sys, runpy, json
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
from placement import edge_seat
log = open(os.environ['TRACE_OUT'], 'w')
orig = edge_seat._Probe.why
def why(self, entry, edge, pose, obstacles):
    kind, read = orig(self, entry, edge, pose, obstacles)
    if entry.get('ref') == 'DC1':
        p = self.state.parts['DC1']
        rect = p.grade_rect(*pose)
        log.write(json.dumps({'pose': [round(v, 3) for v in pose], 'kind': kind,
                              'read': read if not isinstance(read, float) else round(read, 3),
                              'grade_rect': [round(v, 2) for v in rect],
                              'obstacles': sorted(obstacles)[:8]}, default=str) + '\n')
    return kind, read
edge_seat._Probe.why = why
sys.argv = ['place_simple.py'] + sys.argv[1:]
runpy.run_path(os.path.join(ROOT, 'py_placer', 'place_simple.py'), run_name='__main__')
