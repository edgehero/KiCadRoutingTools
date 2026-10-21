#!/usr/bin/env bash
# gp14: gather the per-board media into a local asset folder (pushed to edgehero's gp14-campaign-assets ONLY after Rob approves).
#   bash wk/gp14/_staging/build_assets.sh ASSET_DIR      (from krt-gp14)
set -euo pipefail
A=$1; G=wk/gp14; PY="$HOME/.venvs/krt/bin/python3 -X utf8"
mkdir -p "$A/media" "$A/staging/truth"
$PY $G/_staging/summarize.py > "$A/media/TABLE.md"
cp $G/_cmp/metrics.json "$A/media/metrics.json"
scrub() {  # local absolute paths -> repo-relative
  sed -e "s#$HOME/Documents/git/krt-gp14/##g" -e "s#$HOME/Documents/git/krt-film/#krt-film/#g" \
      -e "s#/private/tmp/claude-[0-9]*/[^ )\"']*#<tmp>#g" -e "s#$HOME#~#g" "$1" > "$2"
}
for d in $G/[0-9][0-9]_*; do
  nn_stem=$(basename "$d"); stem=${nn_stem#??_}; C=$G/_cmp/$stem
  [ -f "$C/summary.json" ] || continue
  M="$A/media/$nn_stem"; mkdir -p "$M"
  for f in REPORT.md TOOL_GAPS.md README.md CHOSEN.json; do [ -f "$d/$f" ] && scrub "$d/$f" "$M/$f"; done
  for f in summary.json grade_ours.json measure.json films.log; do [ -f "$C/$f" ] && scrub "$C/$f" "$M/$f"; done
  for f in film.gif film.mp4 film_andy.gif film_andy.mp4 film_3d.gif film_3d.mp4 film_3d_start.png film_3d_final.png \
           iso_start.png iso_final.png iso_ref.png compare_F.png compare_B.png \
           place_ours_F.png place_ours_B.png place_human_F.png place_human_B.png \
           place_movie_posediff.txt movie3d_posediff.txt; do
    [ -f "$C/$f" ] && cp "$C/$f" "$M/"
  done
  [ -f "$C/widths_final/class_widths_score.json" ] && scrub "$C/widths_final/class_widths_score.json" "$M/class_widths_final.json"
  cp "$G/_truth/$stem/stage.json" "$A/staging/truth/${stem}_stage.json" 2>/dev/null || true
  cp "$G/_truth/$stem/decl.json" "$A/staging/truth/${stem}_decl.json" 2>/dev/null || true
  echo "$nn_stem: $(ls "$M" | wc -l | tr -d ' ') files, $(du -sk "$M" | cut -f1) KB"
done
for f in $G/_staging/*.py $G/_staging/*.sh $G/_staging/teammate_prompt.md $G/_staging/boards.tsv; do scrub "$f" "$A/staging/$(basename "$f")"; done
for f in GRADE_NOTES.md LAUNCH.md PIN; do scrub "$G/$f" "$A/$f"; done
scrub $G/FINDINGS_VERIFIED.md "$A/media/FINDINGS.md"; scrub $G/FINDINGS_CLUSTERED.md "$A/media/FINDINGS_CLUSTERED.md"
[ -f $G/CAMPAIGN.md ] && scrub $G/CAMPAIGN.md "$A/CAMPAIGN.md"
du -sh "$A"
