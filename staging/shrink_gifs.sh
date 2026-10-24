#!/usr/bin/env bash
# gp14: re-encode every film GIF over 3 MB from its mp4, stepping down fps/width/colours until it fits.
#   bash wk/gpm/_staging/shrink_gifs.sh     (from krt-gpm)
set -uo pipefail
for g in wk/gpm/_cmp/*/film*.gif; do
  k=$(du -k "$g" | cut -f1); [ "$k" -le 3000 ] && continue
  m=${g%.gif}.mp4; [ -f "$m" ] || { echo "no mp4 for $g"; continue; }
  for s in "3 520 48" "2 480 40" "2 420 32" "1.5 400 32"; do
    set -- $s
    ffmpeg -y -loglevel error -i "$m" -vf "fps=$1,scale=$2:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=$3:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$g"
    k2=$(du -k "$g" | cut -f1); [ "$k2" -le 3000 ] && break
  done
  echo "$g: ${k}K -> ${k2}K (fps $1, width $2, colours $3)"
done
