"""place_simple.py with ONE change: a container footprint (a pin frame -- here the
Teensy40 frame U8, whose pads ring the whole board and which has no courtyard)
is left out of the anneal's courtyard-OVERLAP term.

Why (TOOL_GAPS.md, entry "anneal overlap counts the pin frame"): the anneal
(`placement/simple_anneal.Annealer`) grows every part's rect and sums pairwise
overlaps, and it does not skip `state.container_refs`. A pin frame's rect is its
pad bounding box -- the whole board (U8: 138.575..158.425 x 87.695..123.82) -- so
every part on the board overlaps it. Measured on a finished seed: overlap term
464.5 mm2, of which 442.0 mm2 is U8-frame pairs. Consequences in the anneal:
`v['ov'] < CLEAN` is never true, so no state is ever recorded as the best one;
every part looks "overlapping", so `escape` moves fire for every part all run;
and `repair` can never come clean. The halo term already skips containers
(`simple.py` halo_pair: "a container is a frame, not a body"); the overlap term
does not.

Everything else is place_simple's own code, unchanged: the frame's PINS still
bind through the exact legality (`pose_ok` / `_pin_hits_at`, #1212) at the end
of every run, and the intent's keep-outs (the pin rows, intent_frame.json) are
priced by the anneal's own `_intent` term.

`--seeds`/`--round` re-run "this script" per seed through
`os.path.abspath(__file__)` in place_simple's module globals; that global is
pointed at THIS file so every seed process gets the same one-line change.

Usage: exactly place_simple.py's arguments.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'py_placer'))
os.chdir(REPO)

import _path  # noqa: E402,F401  (py_placer -> py_router/py_tools on sys.path)
import numpy as np  # noqa: E402
from placement import simple_anneal  # noqa: E402

_orig_init = simple_anneal.Annealer.__init__


def _init(self, model, movable, **kw):
    _orig_init(self, model, movable, **kw)
    cont = set(getattr(self.st, 'container_refs', ()) or ())
    for r in cont:
        if r in self.faces:
            self.faces[r] = 0          # shares no face with any part: no overlap pair
    self.face_ids = np.asarray([self.faces[r] for r in self.names], dtype=np.int64)


simple_anneal.Annealer.__init__ = _init

import place_simple  # noqa: E402

place_simple.__file__ = os.path.abspath(__file__)

if __name__ == '__main__':
    sys.exit(place_simple.main(sys.argv[1:]))
