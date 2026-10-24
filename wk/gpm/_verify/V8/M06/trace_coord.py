"""Log _seat_coord's single along-edge sample for DC1; with SHIFT_ALONG set, sample there instead (verifier causal test, M06)."""
import os, sys, runpy
ROOT = os.getcwd()
sys.path[:0] = [os.path.join(ROOT, 'py_router'), os.path.join(ROOT, 'py_placer')]
from placement import edge_seat
orig = edge_seat._seat_coord
shift = os.environ.get('SHIFT_ALONG')
def wrapped(probe, ref, edge, rot, axis, along, target):
    use = float(shift) if (shift and ref == 'DC1') else along
    coord, floor = orig(probe, ref, edge, rot, axis, use, target)
    if ref == 'DC1':
        print(f"TRACE _seat_coord DC1 {edge} rot={rot} along(sampled)={use:.3f} (midpoint {along:.3f}) -> coord={coord} floor={floor}")
    return coord, floor
edge_seat._seat_coord = wrapped
sys.argv = ['place_simple.py'] + sys.argv[1:]
runpy.run_path(os.path.join(ROOT, 'py_placer', 'place_simple.py'), run_name='__main__')
