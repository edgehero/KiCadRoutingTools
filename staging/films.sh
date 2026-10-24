#!/usr/bin/env bash
# gpm: the films of one finished run, movie3d only (main removed the 2D film tools), from the files the run left.
#   bash wk/gpm/_staging/films.sh RUNDIR OUTDIR STEM   (from krt-gpm)
# RUNDIR holds CHOSEN.json, placed_from/{fixed.kicad_pcb, groups.json, <intent>}, the seeds (s<S>.*),
# judge.json, s<S>_route/, s<S>_fast.score.json and final_route/. Writes into OUTDIR:
#   film_seed.mp4/.gif  movie3d of the KEPT seed's anneal (re-placed in-process; pose_diff proves it is the shipped seed)
#   film_flow.mp4/.gif  movie3d --route of the whole run: the seeds, the judged seeds' fast routes side by side,
#                       the best one, then its full route (final_route/), from a work dir film_work.py links
#                       out of RUNDIR -- nothing is placed or routed again
#   films.json          what rendered, and whether each film tells the run's own story
set -uo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
R=$1; O=$2; STEM=$3
mkdir -p "$O/work"
PY="python3 -B -X utf8"; S=wk/gpm/_staging
CH=$R/CHOSEN.json
read -r SEED START INTENT < <($PY -c "import json;c=json.load(open('$CH'));print(c['seed'],c.get('start','scattered'),c.get('intent','intent.json'))")
PF=$R/placed_from; IN=$PF/fixed.kicad_pcb
EXTRA=(); [ "$START" = clustered ] && EXTRA=(--clustered-seeds "$SEED")
PA=$($PY -c "import json;print(' '.join(json.load(open('$CH')).get('place_args',[])))")
[ -z "$PA" ] && PA=${FILM_PLACE_ARGS:-}
# the run's own seed selection (--seeds / --clustered-seeds / --anchored-seeds) picks which seeds a pass places,
# not how one is placed: drop it, and keep the kept seed's own start (EXTRA's --clustered-seeds S)
PLACE=(); skip=0; for a in $PA; do
  if [ $skip = 1 ]; then skip=0; continue; fi
  case "$a" in --seeds|--clustered-seeds|--anchored-seeds) skip=1; continue;; --seeds=*|--clustered-seeds=*|--anchored-seeds=*) continue;; esac
  PLACE+=("$a")
done
SDIR=$R; K=$($PY -c "import json;print(json.load(open('$CH')).get('pass',''))")
[ ! -f "$R/judge.json" ] && [ -f "$R/old/pass$K/judge.json" ] && SDIR=$R/old/pass$K
echo "== chosen: seed $SEED ($START), pass ${K:-?}, intent $INTENT, place_args: ${PLACE[*]+"${PLACE[*]}"}, seeds in $SDIR"
gif() {  # mp4 -> gif under 3 MB (fa10's recipe, then a stronger pass)
  local FF; FF=$(command -v ffmpeg)
  "$FF" -y -loglevel error -i "$1" -vf "fps=4,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$2"
  if [ "$(du -k "$2" | cut -f1)" -gt 3000 ]; then
    "$FF" -y -loglevel error -i "$1" -vf "fps=3,scale=560:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=48:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$2"
  fi
  if [ "$(du -k "$2" | cut -f1)" -gt 3000 ]; then
    "$FF" -y -loglevel error -i "$1" -vf "fps=2,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=32:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" "$2"
  fi
  echo "gif $(basename "$2"): $(du -k "$2" | cut -f1) KB"
}
echo "== 1 film_seed: movie3d of the kept seed"
t0=$(date +%s)
$PY movie3d/make_movie.py "$IN" "$O/work/seed.kicad_pcb" --groups "$PF/groups.json" --intent "$PF/$INTENT" \
    --seed "$SEED" ${EXTRA[@]+"${EXTRA[@]}"} ${PLACE[@]+"${PLACE[@]}"} --movie "$O/film_seed.mp4" > "$O/film_seed.log" 2>&1
echo "film_seed exit $? in $(( $(date +%s) - t0 )) s :: $(grep -iE 'model|box' "$O/film_seed.log" | tail -2 | tr '\n' ' ' | cut -c1-250)"
$PY $S/pose_diff.py "$O/work/seed.kicad_pcb" "$SDIR/s$SEED.kicad_pcb" > "$O/film_seed_posediff.txt" 2>&1
echo "film_seed = shipped seed? exit $? :: $(head -1 "$O/film_seed_posediff.txt") :: $($PY - "$O/film_seed_posediff.txt" "$CH" <<'EOF2'
import json, re, sys
diff = [l.split(':')[0].strip() for l in open(sys.argv[1]).read().splitlines()[1:] if ':' in l]
after = ' '.join(json.load(open(sys.argv[2])).get('after', []))
hand = [r for r in diff if re.search(r'\b' + re.escape(r) + r'\b', after)]
rest = [r for r in diff if r not in hand]
print(f"differing {diff}: moved by hand afterwards (CHOSEN after) {hand}, unexplained {rest}")
EOF2
)"
[ -f "$O/film_seed.mp4" ] && gif "$O/film_seed.mp4" "$O/film_seed.gif"
echo "== 2 film_flow: movie3d of the whole run (film_work.py links the run into run_flow's layout)"
$PY $S/film_work.py "$R" "$O/flow_work" > "$O/film_work.log" 2>&1; FW=$?
echo "film_work exit $FW :: $(grep JSON_SUMMARY "$O/film_work.log" | cut -c1-400)"
if [ $FW -eq 0 ]; then
  NJ=$($PY -c "import json,sys;print(next(json.loads(l.split('JSON_SUMMARY: ',1)[1])['judge'] for l in open(sys.argv[1]) if l.startswith('JSON_SUMMARY: ')))" "$O/film_work.log")
  t0=$(date +%s)
  $PY movie3d/make_movie.py "$IN" "$O/work/flow.kicad_pcb" --groups "$PF/groups.json" --intent "$PF/$INTENT" \
      ${PLACE[@]+"${PLACE[@]}"} --route "$STEM:0" --route-work "$O/flow_work" --judge "$NJ" --movie "$O/film_flow.mp4" > "$O/film_flow.log" 2>&1
  echo "film_flow exit $? in $(( $(date +%s) - t0 )) s :: $(grep -E 'make_movie:|place_movie:' "$O/film_flow.log" | tail -3 | tr '\n' ' ' | cut -c1-300)"
  [ -f "$O/film_flow.mp4" ] && gif "$O/film_flow.mp4" "$O/film_flow.gif"
else
  echo "film_flow SKIPPED: the flow film would not tell this run's story (film_work exit $FW)"
fi
$PY - "$O" <<'EOF'
import json, os, re, sys
O = sys.argv[1]
def first(p):
    try:
        return open(os.path.join(O, p)).readline().strip()
    except OSError:
        return None
fw = next((json.loads(l.split('JSON_SUMMARY: ', 1)[1]) for l in open(os.path.join(O, 'film_work.log'))
           if l.startswith('JSON_SUMMARY: ')), None) if os.path.isfile(os.path.join(O, 'film_work.log')) else None
doc = {'film_seed': os.path.isfile(os.path.join(O, 'film_seed.mp4')), 'film_seed_posediff': first('film_seed_posediff.txt'),
       'film_flow': os.path.isfile(os.path.join(O, 'film_flow.mp4')), 'film_work': fw}
json.dump(doc, open(os.path.join(O, 'films.json'), 'w'), indent=1)
print('films.json:', json.dumps(doc)[:400])
EOF
ls -la "$O" | grep -E "mp4|gif|png"
