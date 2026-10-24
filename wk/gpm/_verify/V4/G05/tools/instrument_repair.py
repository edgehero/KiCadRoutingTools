"""Run place_simple with Annealer.repair and anneal() wrapped, to log the
model's own decap-limit breakage before the post-anneal repair, after it, and
after the reseat. Diagnostic only; no tracked file is edited."""
import os, sys, runpy
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_placer'), os.path.join(ROOT, 'py_router'),
                os.path.join(ROOT, 'py_tools'), ROOT]
from placement import simple_anneal as sa

def broken(model):
    model.reprice_all()
    t = model.total()
    return t.get('decap_broken'), round(t.get('decap_limits', 0.0), 3)

_orig_repair = sa.Annealer.repair
def repair(self, *a, **k):
    print(f"  [instr] before repair: decap_broken/limits {broken(self.model)}", flush=True)
    out = _orig_repair(self, *a, **k)
    print(f"  [instr] after repair: decap_broken/limits {broken(self.model)}", flush=True)
    return out
sa.Annealer.repair = repair

_orig_anneal = sa.anneal
def anneal(model, movable, **kw):
    res = _orig_anneal(model, movable, **kw)
    print(f"  [instr] anneal returned (after reseat): decap_broken/limits {broken(model)} "
          f"reseated {res.get('reseated')} repaired {res.get('repaired')}", flush=True)
    return res
sa.anneal = anneal

sys.argv = ['place_simple.py'] + sys.argv[1:]
runpy.run_path(os.path.join(ROOT, 'py_placer', 'place_simple.py'), run_name='__main__')
