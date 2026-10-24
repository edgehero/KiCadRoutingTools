#!/usr/bin/env bash
# gpm Phase 3 for one FINISHED board (ported from gp14 for main bda59fa0): independent grade + comparison artefacts.
#   bash wk/gpm/_staging/compare_board.sh NN STEM [AGENT_ID]   (from krt-gpm; AGENT_ID = the teammate subagent, for measure.py)
# Writes everything to wk/gpm/_cmp/STEM/. Reads the teammate's folder, never writes it (kicad-cli runs on copies).
# The graded board is main's §3.9 hand-back, delivered.kicad_pcb (filled); routed.kicad_pcb when the fill failed.
set -uo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
NN=$1; STEM=$2; TX=${3:-}
W=wk/gpm/${NN}_$STEM; T=wk/gpm/_truth/$STEM; C=wk/gpm/_cmp/$STEM; K=wk/gpm/_control/$STEM
FILM_WT=$(cd ../krt-film && pwd); S=wk/gpm/_staging
mkdir -p "$C"
PY="python3 -B -X utf8"
G=.claude/skills/plan-pcb-placement/scripts
exec > >(tee "$C/compare.log") 2>&1
echo "== 0 inputs unchanged?"
$PY - "$T/stage.json" "$W" <<'EOF'
import hashlib, json, os, sys
st = json.load(open(sys.argv[1])); W = sys.argv[2]
bad = [n for n, h in st['inputs'].items()
       if hashlib.sha256(open(os.path.join(W, n), 'rb').read()).hexdigest() != h]
print('inputs changed:', bad or 'none')
EOF
F=$W/delivered.kicad_pcb; [ -f "$F" ] || F=$W/routed.kicad_pcb
echo "graded board: $F"
echo "sha256 $(shasum -a 256 "$F" | cut -d' ' -f1) | DELIVERED.sha256 $(cat "$W/DELIVERED.sha256" 2>/dev/null) | DONE $(cat "$W/DONE" 2>/dev/null)"
RI=$($PY -c "import json;print(json.load(open('$W/CHOSEN.json')).get('intent',''))" 2>/dev/null)
echo "== 1 independent grade (grade.py --mode full), on the GIVEN intent and on the run's intent ($RI)"
$PY $G/grade.py "$F" --baseline "$W/$STEM.kicad_pcb" --intent "$W/intent.json" \
    --mode full --label ours --out-dir "$C" > "$C/grade_ours.log" 2>&1; echo "grade ours exit $?"
head -1 "$C/grade_ours.log" | cut -c1-400
if [ -n "$RI" ] && [ "$RI" != intent.json ] && [ -f "$W/$RI" ]; then
  $PY $G/grade.py "$F" --baseline "$W/$STEM.kicad_pcb" --intent "$W/$RI" \
      --mode full --label ours_runintent --out-dir "$C" > "$C/grade_ours_runintent.log" 2>&1; echo "grade ours (run intent) exit $?"
  head -1 "$C/grade_ours_runintent.log" | cut -c1-400
fi
$PY py_router/check_connected.py "$F" > "$C/connected.log" 2>&1; echo "check_connected exit $?: $(grep -v '^\s*$' "$C/connected.log" | tail -2 | head -1)"
# DRC at the floor the route wrote back into the board's .kicad_pro (check_drc reads it), against the input
$PY py_router/check_drc.py "$F" --baseline "$W/$STEM.kicad_pcb" --json "$C/drc.json" > "$C/drc.log" 2>&1; echo "check_drc exit $?: $(tail -1 "$C/drc.log" | cut -c1-200)"
$PY py_tools/board_score.py "$F" --intent "$W/intent.json" --baseline "$W/$STEM.kicad_pcb" --json "$C/board_score.json" --quiet > /dev/null 2>&1; echo "board_score exit $?"
echo "== 2 copper-free twins and placement renders"
$PY tests/stress/strip_copper_only.py "$F" "$C/ours_stripped.kicad_pcb"
$PY py_router/copy_board.py "$T/human_stripped.kicad_pcb" "$C/human_stripped.kicad_pcb" > /dev/null
for side in ours human; do
  $PY py_tools/render_placement.py "$C/${side}_stripped.kicad_pcb" --per-side -o "$C/place_${side}.png" \
      --json-out "$C/place_${side}_render.json" > "$C/place_${side}.log" 2>&1; echo "render $side exit $?"
  # placement_score is not on main; krt-film's (upstream main b118ad48) is fa10's instrument
  $PY "$FILM_WT/py_placer/placement_score.py" "$C/${side}_stripped.kicad_pcb" --json "$C/placement_score_${side}.json" \
      > "$C/placement_score_${side}.log" 2>&1; echo "placement_score $side exit $?"
done
echo "== 3 copper against the human board"
$PY tests/stress/compare_to_original.py --ours "$F" --orig "$T/human.kicad_pcb" --json > "$C/compare_to_human.txt" 2>&1
echo "compare human exit $?"
[ -f "$K/control.kicad_pcb" ] && { $PY tests/stress/compare_to_original.py --ours "$K/control.kicad_pcb" \
    --orig "$T/human.kicad_pcb" --json > "$C/control_to_human.txt" 2>&1; echo "compare control exit $?"; }
echo "== 4 3D stills (krt-film's kicad_iso_render, model paths resolved on a temp copy)"
for pair in "start:$W/$STEM.kicad_pcb" "final:$F" "ref:$T/human.kicad_pcb"; do
  name=${pair%%:*}; b=${pair#*:}
  $PY $S/iso_render.py "$b" "$STEM" -o "$PWD/$C/iso_$name.png" --width 1600 --height 1000 --quality high >> "$C/iso.log" 2>&1
  echo "iso $name exit $? $(grep -o '3D models [0-9/]*' "$C/iso.log" | tail -1)"
done
echo "== 5 films (movie3d: the kept seed, and the whole run)"
bash $S/films.sh "$W" "$C" "$STEM" > "$C/films.log" 2>&1; echo "films exit $?"; grep -E "exit|shipped|gif |SKIPPED" "$C/films.log"
echo "== 6 where the time went"
[ -n "$TX" ] && { $PY $G/measure.py --agent-id "$TX" --json "$C/measure.json" > "$C/measure.log" 2>&1; echo "measure exit $?"; grep -E 'wall_clock|waiting_on_jobs|other_tool|model_seconds' "$C/measure.log" | head -4; }
echo "== 7 fence (krt-film's fence_audit)"
$PY "$FILM_WT/tests/stress/fence_audit.py" --control "$T/human_stripped.kicad_pcb" --workdir "$W" --mode audit 2>&1 | grep -E "VERDICT|LEAK" | head -5
echo "== 8 repo untouched outside wk/"
git status --porcelain -- . ':!wk' | head -5; echo "(end)"
