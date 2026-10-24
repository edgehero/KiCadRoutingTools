"""Record footprint_outline_owners on the BEFORE and AFTER text the #829 tripwire compares."""
import os, sys, runpy
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
import kicad_parser as kp
orig = kp.structural_outline_fingerprint
calls = []
def wrapped(content):
    owners = kp.footprint_outline_owners(content)
    calls.append(owners)
    print(f"fingerprint call {len(calls)}: owners =", {k: ('STRUCTURAL' if v else 'carried') for k, v in sorted(owners.items())})
    return orig(content)
kp.structural_outline_fingerprint = wrapped
sys.argv = ['make_unplaced.py', sys.argv[1], sys.argv[2]]
try:
    runpy.run_path(os.path.join(ROOT, '.claude/skills/plan-pcb-placement/scripts/make_unplaced.py'), run_name='__main__')
except SystemExit as e:
    print('exit', e.code)
except Exception as e:
    print('raised', type(e).__name__)
