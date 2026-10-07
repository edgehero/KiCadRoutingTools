#!/usr/bin/env bash
# fa10 control for one board: the HUMAN placement, routed by our router in one
# plain route.py pass at the board's own netclass (no clearance flags), then
# graded the same way as the human original.
#   bash wk/fa10/_staging/control.sh STEM      (from the campaign worktree root)
set -uo pipefail
export MSYS2_ARG_CONV_EXCL='*'
STEM=$1
T=wk/fa10/_truth/$STEM; C=wk/fa10/_control/$STEM
mkdir -p "$C"
PY="python3 -B -X utf8"
$PY tests/stress/tee_cmd.py --workdir "$C" route -- python3 -u -X utf8 py_router/route.py \
    "$T/human_stripped.kicad_pcb" --output "$C/control.kicad_pcb" --nets '*' --json-out "$C/route.json"
echo "route exit $?"
$PY .claude/skills/pcb-free-agent/scripts/grade.py "$C/control.kicad_pcb" --baseline "$T/human_stripped.kicad_pcb" \
    --mode route --label control --out-dir "$C" > "$C/grade_control.log" 2>&1
echo "grade control exit $?"
$PY .claude/skills/pcb-free-agent/scripts/grade.py "$T/human.kicad_pcb" --baseline "$T/human_stripped.kicad_pcb" \
    --mode route --label human --out-dir "$C" > "$C/grade_human.log" 2>&1
echo "grade human exit $?"
