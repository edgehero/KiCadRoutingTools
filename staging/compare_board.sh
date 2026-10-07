#!/usr/bin/env bash
# fa10 Phase 4 for one FINISHED board: independent grade + comparison artefacts.
#   bash wk/fa10/_staging/compare_board.sh NN STEM TRANSCRIPT.jsonl   (from the worktree root)
# Writes everything to wk/fa10/_cmp/STEM/. Reads the teammate's folder, never writes it.
set -uo pipefail
export MSYS2_ARG_CONV_EXCL='*'
NN=$1; STEM=$2; TX=${3:-}
W=wk/fa10/${NN}_$STEM; T=wk/fa10/_truth/$STEM; C=wk/fa10/_cmp/$STEM; K=wk/fa10/_control/$STEM
mkdir -p "$C"
PY="python3 -B -X utf8"
exec > >(tee "$C/compare.log") 2>&1
echo "== 0 inputs unchanged?"
$PY - "$T/stage.json" "$W" <<'EOF'
import hashlib, json, os, sys
st = json.load(open(sys.argv[1])); W = sys.argv[2]
bad = [n for n, h in st['inputs'].items() if n != 'README.md'
       and hashlib.sha256(open(os.path.join(W, n), 'rb').read()).hexdigest() != h]
print('inputs changed:', bad or 'none')
EOF
F=$W/final.kicad_pcb
echo "final sha256 $(sha256sum "$F" | cut -d' ' -f1) | FINAL.sha256 $(cat "$W/FINAL.sha256" 2>/dev/null)"
echo "== 1 independent grade (grade.py --mode full)"
$PY .claude/skills/pcb-free-agent/scripts/grade.py "$F" --baseline "$W/$STEM.kicad_pcb" --intent "$W/intent.json" \
    --mode full --label ours --out-dir "$C" > "$C/grade_ours.log" 2>&1; echo "grade ours exit $?"
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
echo "== 4 3D stills"
$PY py_router/kicad_iso_render.py "$W/$STEM.kicad_pcb" -o "$C/iso_start.png" --width 1600 --height 1000 --quality high > "$C/iso.log" 2>&1; echo "iso start $?"
$PY py_router/kicad_iso_render.py "$F" -o "$C/iso_final.png" --width 1600 --height 1000 --quality high >> "$C/iso.log" 2>&1; echo "iso final $?"
$PY py_router/kicad_iso_render.py "$T/human.kicad_pcb" -o "$C/iso_ref.png" --width 1600 --height 1000 --quality high >> "$C/iso.log" 2>&1; echo "iso ref $?"
echo "== 5 film GIF"
MP4=$(ls "$W"/*_film.mp4 2>/dev/null | head -1)
if [ -n "$MP4" ]; then
  FF=$(python3 -c 'import imageio_ffmpeg as m; print(m.get_ffmpeg_exe())')
  cp "$MP4" "$C/film.mp4"
  "$FF" -y -loglevel error -i "$MP4" -vf "fps=4,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$C/film.gif"
  if [ "$(du -k "$C/film.gif" | cut -f1)" -gt 3000 ]; then
    "$FF" -y -loglevel error -i "$MP4" -vf "fps=3,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$C/film.gif"
  fi
  echo "gif $? $(du -k "$C/film.gif" | cut -f1) KB"
else echo "no film mp4"; fi
echo "== 6 where the time went"
[ -n "$TX" ] && { $PY .claude/skills/pcb-free-agent/scripts/measure.py "$TX" --root . --json "$C/measure.json" > "$C/measure.log" 2>&1; echo "measure exit $?"; tail -25 "$C/measure.log"; }
echo "== 7 fence"
$PY tests/stress/fence_audit.py --control "$T/human_stripped.kicad_pcb" --workdir "$W" --mode audit 2>&1 | grep -E "VERDICT|LEAK" | head -5
echo "== 8 repo untouched outside wk/"
git status --porcelain -- . ':!wk' | head -5; echo "(end)"
