"""Make the tfgps01 pile with the #829 tripwire disabled IN MEMORY ONLY (to test the move-back-in leg)."""
import os, sys, runpy
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
import kicad_parser as kp
kp.structural_outline_fingerprint = lambda content: 0
sys.argv = ['make_unplaced.py', sys.argv[1], sys.argv[2]]
runpy.run_path(os.path.join(ROOT, '.claude/skills/plan-pcb-placement/scripts/make_unplaced.py'), run_name='__main__')
