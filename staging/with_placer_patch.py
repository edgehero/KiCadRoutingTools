#!/usr/bin/env python3
"""gp14: run a film tool (place_movie / movie3d make_movie) with a teammate's in-process
place_simple patch applied, so a board placed with that patch re-films to the shipped poses.

    python3 -X utf8 wk/gp14/_staging/with_placer_patch.py HELPER.py SCRIPT.py [SCRIPT args...]

HELPER is imported as a module (not run): its top level patches the placer in this process.
SCRIPT then runs as __main__ with the remaining arguments.
"""
import importlib.util
import os
import runpy
import sys

helper, script = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
spec = importlib.util.spec_from_file_location('gp14_placer_patch', helper)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.argv = [script] + sys.argv[3:]
sys.path.insert(0, os.path.dirname(script))
runpy.run_path(script, run_name='__main__')
