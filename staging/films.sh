#!/usr/bin/env bash
# gp14: every film of one finished run, from the files the run left (never re-routes).
#   bash wk/gp14/_staging/films.sh RUNDIR OUTDIR TITLE   (from krt-gp14)
# RUNDIR holds CHOSEN.json, r<N>/{fixed.kicad_pcb,groups.json,intent.json,s<S>.kicad_pcb},
# final_route/ and ledger.jsonl. Writes into OUTDIR:
#   film.mp4/.gif       krt-film's make_film --from-ledger (fa10's film, for comparison)
#   film_andy.mp4/.gif  place_movie of the chosen seed, then route_movie of final_route/
#   film_3d.mp4/.gif    movie3d of the chosen seed (KiCad models)
#   films.json          what rendered, and whether each re-filmed placement is the shipped one
set -uo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
WT=$(pwd); R=$1; O=$2; TITLE=$3
mkdir -p "$O/work"
PY="python3 -B -X utf8"; S=wk/gp14/_staging
FILM_WT=$(cd ../krt-film && pwd)
CH=$R/CHOSEN.json
read -r N SEED START < <($PY -c "import json;c=json.load(open('$CH'));print(c['round'],c['seed'],c.get('start','scattered'))")
RD=$R/r$N; IN=$RD/fixed.kicad_pcb
EXTRA=(); [ "$START" = clustered ] && EXTRA=(--clustered-seeds "$SEED")
# place_simple weights the run used beyond groups/intent/seed (e.g. --decap-limit-weight 100):
# CHOSEN.json "place_args" [list], else FILM_PLACE_ARGS (space-separated)
PA=$($PY -c "import json;print(' '.join(json.load(open('$CH')).get('place_args',[])))")
[ -z "$PA" ] && PA=${FILM_PLACE_ARGS:-}
for a in $PA; do EXTRA+=("$a"); done
[ -n "${FILM_PLACER_PATCH:-}" ] && echo "== placer patch: $FILM_PLACER_PATCH"
echo "== chosen: round $N seed $SEED ($START), input $IN, extra: ${EXTRA[*]+"${EXTRA[*]}"}"
gif() {  # mp4 -> gif under 3 MB (fa10's recipe)
  local FF; FF=$(command -v ffmpeg)
  "$FF" -y -loglevel error -i "$1" -vf "fps=4,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$2"
  if [ "$(du -k "$2" | cut -f1)" -gt 3000 ]; then
    "$FF" -y -loglevel error -i "$1" -vf "fps=3,scale=560:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=48:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$2"
  fi
  echo "gif $(basename "$2"): $(du -k "$2" | cut -f1) KB"
}
RA=$(cd "$R" && pwd); OA=$(cd "$O" && pwd)
if [ -z "${FILMS_SKIP_FA10:-}" ]; then
echo "== 1 fa10 film (krt-film make_film --from-ledger)"
(cd "$FILM_WT" && $PY py_tools/make_film.py --from-ledger "$RA/ledger.jsonl" --store "$RA/boards" \
    --title "$TITLE" --theme light --aspect 4:3 -o "$OA/film.mp4") > "$O/film.log" 2>&1
echo "make_film exit $?"; [ -f "$O/film.mp4" ] && gif "$O/film.mp4" "$O/film.gif"
fi
echo "== 2 place_movie of the chosen seed"
$PY ${FILM_PLACER_PATCH:+$S/with_placer_patch.py "$FILM_PLACER_PATCH"} py_placer/place_movie.py "$IN" "$O/work/place_movie.kicad_pcb" --groups "$RD/groups.json" --intent "$RD/intent.json" \
    --seed "$SEED" ${EXTRA[@]+"${EXTRA[@]}"} --movie "$O/work/place.mp4" > "$O/place_movie.log" 2>&1
echo "place_movie exit $?"
$PY $S/pose_diff.py "$O/work/place_movie.kicad_pcb" "$RD/s$SEED.kicad_pcb" > "$O/place_movie_posediff.txt" 2>&1
echo "place_movie = shipped seed? exit $? :: $(head -1 "$O/place_movie_posediff.txt")"
echo "== 3 route_movie of final_route/"
$PY py_router/route_movie.py "$R/final_route" -o "$O/work/route.mp4" > "$O/route_movie.log" 2>&1
echo "route_movie exit $?"
if [ -f "$O/work/place.mp4" ] && [ -f "$O/work/route.mp4" ]; then
  ffmpeg -y -loglevel error -i "$O/work/place.mp4" -i "$O/work/route.mp4" -filter_complex \
    "[0:v]scale=1000:750:force_original_aspect_ratio=decrease,pad=1000:750:(ow-iw)/2:(oh-ih)/2:color=0x1e1e1e,setsar=1,fps=12[a];[1:v]scale=1000:750:force_original_aspect_ratio=decrease,pad=1000:750:(ow-iw)/2:(oh-ih)/2:color=0x1e1e1e,setsar=1,fps=12[b];[a][b]concat=n=2:v=1:a=0[v]" \
    -map "[v]" -c:v libx264 -pix_fmt yuv420p -crf 22 "$O/film_andy.mp4"
  echo "concat exit $?"; gif "$O/film_andy.mp4" "$O/film_andy.gif"
fi
echo "== 4 movie3d of the chosen seed"
BR=(); [ -n "${MOVIE3D_BROWSER:-}" ] && BR=(--browser "$MOVIE3D_BROWSER")
$PY ${FILM_PLACER_PATCH:+$S/with_placer_patch.py "$FILM_PLACER_PATCH"} movie3d/make_movie.py "$IN" "$O/work/movie3d.kicad_pcb" --groups "$RD/groups.json" --intent "$RD/intent.json" \
    --seed "$SEED" ${EXTRA[@]+"${EXTRA[@]}"} --movie "$O/film_3d.mp4" ${BR[@]+"${BR[@]}"} > "$O/movie3d.log" 2>&1
echo "movie3d exit $? :: $(grep -iE 'model|box' "$O/movie3d.log" | tail -2 | tr '\n' ' ' | cut -c1-250)"
$PY $S/pose_diff.py "$O/work/movie3d.kicad_pcb" "$RD/s$SEED.kicad_pcb" > "$O/movie3d_posediff.txt" 2>&1
echo "movie3d = shipped seed? exit $? :: $(head -1 "$O/movie3d_posediff.txt")"
[ -f "$O/film_3d.mp4" ] && gif "$O/film_3d.mp4" "$O/film_3d.gif"
ls -la "$O" | grep -E "mp4|gif"
