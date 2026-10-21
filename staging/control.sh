#!/usr/bin/env bash
# gp14 control for one board (ported from fa10): the HUMAN placement, routed by our
# router in one plain route.py pass at the board's own netclass (no clearance flags),
# then graded the same way as the human original.
#   bash wk/gp14/_staging/control.sh STEM      (from krt-gp14)
set -uo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
STEM=$1
T=wk/gp14/_truth/$STEM; C=wk/gp14/_control/$STEM
mkdir -p "$C"
PY="python3 -B -X utf8"
G=.claude/skills/plan-pcb-placement/scripts/grade.py
t0=$(date +%s)
$PY tests/stress/tee_cmd.py --workdir "$C" route -- python3 -u -X utf8 py_router/route.py \
    "$T/human_stripped.kicad_pcb" --output "$C/control.kicad_pcb" --nets '*' --json-out "$C/route.json"
echo "route exit $? in $(( $(date +%s) - t0 )) s"
$PY $G "$C/control.kicad_pcb" --baseline "$T/human_stripped.kicad_pcb" --mode full --label control --out-dir "$C" \
    > "$C/grade_control.log" 2>&1
echo "grade control exit $?: $(head -1 "$C/grade_control.log" | cut -c1-300)"
$PY $G "$T/human.kicad_pcb" --baseline "$T/human_stripped.kicad_pcb" --mode full --label human --out-dir "$C" \
    > "$C/grade_human.log" 2>&1
echo "grade human exit $?: $(head -1 "$C/grade_human.log" | cut -c1-300)"
