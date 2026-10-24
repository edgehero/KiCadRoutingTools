"""Run bga_fanout.py with a patched under-pad 'already fanned' tolerance (verifier causal test, M05)."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(HERE, 'patched'), os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
import bga_fanout
assert bga_fanout.__file__.startswith(os.path.join(HERE, 'patched')), bga_fanout.__file__
sys.argv = ['bga_fanout.py'] + sys.argv[1:]
runpy.run_path(os.path.join(ROOT, 'py_router', 'bga_fanout.py'), run_name='__main__')
