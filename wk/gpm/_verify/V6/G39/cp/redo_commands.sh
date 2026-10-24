#!/bin/bash
# Auto-recorded stress-test command manifest (issue #132).
# Replay with redo_stress_test.py.
set -e
# cwd=~/Documents/git/krt-gpm
python3 -u -X utf8 py_router/copy_board.py wk/gpm/_verify/V6/G39/dq_first.kicad_pcb wk/gpm/_verify/V6/G39/cp/x.kicad_pcb
