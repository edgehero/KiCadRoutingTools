#!/usr/bin/env bash
# gp14 Phase 3 for one FINISHED board (ported from fa10): independent grade + comparison artefacts.
#   bash wk/gp14/_staging/compare_board.sh NN STEM [TRANSCRIPT.jsonl]   (from krt-gp14)
# Writes everything to wk/gp14/_cmp/STEM/. Reads the teammate's folder, never writes it.
set -uo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
NN=$1; STEM=$2; TX=${3:-}
W=wk/gp14/${NN}_$STEM; T=wk/gp14/_truth/$STEM; C=wk/gp14/_cmp/$STEM; K=wk/gp14/_control/$STEM
FILM_WT=$(cd ../krt-film && pwd); S=wk/gp14/_staging
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
F=$W/final.kicad_pcb
echo "final sha256 $(shasum -a 256 "$F" | cut -d' ' -f1) | FINAL.sha256 $(cat "$W/FINAL.sha256" 2>/dev/null)"
echo "== 1 independent grade (grade.py --mode full)"
$PY $G/grade.py "$F" --baseline "$W/$STEM.kicad_pcb" --intent "$W/intent.json" \
    --mode full --label ours --out-dir "$C" > "$C/grade_ours.log" 2>&1; echo "grade ours exit $?"
head -1 "$C/grade_ours.log" | cut -c1-400
$PY py_router/check_connected.py "$F" > "$C/connected.log" 2>&1; echo "check_connected exit $?: $(grep -v '^\s*$' "$C/connected.log" | tail -2 | head -1)"
echo "== 2 copper-free twins and placement renders"
$PY tests/stress/strip_copper_only.py "$F" "$C/ours_stripped.kicad_pcb"
$PY py_router/copy_board.py "$T/human_stripped.kicad_pcb" "$C/human_stripped.kicad_pcb" > /dev/null
for side in ours human; do
  $PY py_tools/render_placement.py "$C/${side}_stripped.kicad_pcb" --per-side -o "$C/place_${side}.png" \
      --json-out "$C/place_${side}_render.json" > "$C/place_${side}.log" 2>&1; echo "render $side exit $?"
  $PY py_placer/placement_score.py "$C/${side}_stripped.kicad_pcb" --json "$C/placement_score_${side}.json" \
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
echo "== 5 film from the ledger (krt-film's make_film), then the GIF"
if [ -f "$W/ledger.jsonl" ]; then
  (cd "$FILM_WT" && $PY py_tools/make_film.py --from-ledger "$OLDPWD/$W/ledger.jsonl" --store "$OLDPWD/$W/boards" \
      --title "$STEM" --theme light --aspect 4:3 -o "$OLDPWD/$C/film.mp4") > "$C/film.log" 2>&1
  echo "make_film exit $?: $(grep -E 'beats|wrote' "$C/film.log" | tail -2 | tr '\n' ' ' | cut -c1-250)"
fi
if [ -f "$C/film.mp4" ]; then
  FF=$(command -v ffmpeg)
  "$FF" -y -loglevel error -i "$C/film.mp4" -vf "fps=4,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$C/film.gif"
  if [ "$(du -k "$C/film.gif" | cut -f1)" -gt 3000 ]; then
    "$FF" -y -loglevel error -i "$C/film.mp4" -vf "fps=3,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$C/film.gif"
  fi
  echo "gif $? $(du -k "$C/film.gif" | cut -f1) KB"
else echo "no film mp4"; fi
echo "== 6 where the time went"
[ -n "$TX" ] && { $PY $G/measure.py "$TX" --root . --json "$C/measure.json" > "$C/measure.log" 2>&1; echo "measure exit $?"; tail -25 "$C/measure.log"; }
echo "== 7 fence (krt-film's fence_audit)"
$PY "$FILM_WT/tests/stress/fence_audit.py" --control "$T/human_stripped.kicad_pcb" --workdir "$W" --mode audit 2>&1 | grep -E "VERDICT|LEAK" | head -5
echo "== 8 repo untouched outside wk/"
git status --porcelain -- . ':!wk' | head -5; echo "(end)"
