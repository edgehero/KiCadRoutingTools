#!/usr/bin/env bash
# fa10: gather the per-board media into the asset worktree (orphan branch fa10-campaign-assets).
#   bash wk/fa10/_staging/build_assets.sh ASSET_WT      (from the campaign worktree root)
set -euo pipefail
A=$1; FA=wk/fa10
mkdir -p "$A/media" "$A/staging/truth"
python3 -X utf8 $FA/_staging/summarize.py > "$A/media/TABLE.md"
cp $FA/_cmp/metrics.json "$A/media/metrics.json"
for d in $FA/[0-9][0-9]_*; do
  nn_stem=$(basename "$d"); stem=${nn_stem#??_}; C=$FA/_cmp/$stem
  [ -f "$C/summary.json" ] || continue
  python3 -X utf8 $FA/_staging/compose_compare.py "$stem" > /dev/null
  M="$A/media/$nn_stem"; mkdir -p "$M"
  for f in REPORT.md TOOL_GAPS.md README.md; do [ -f "$d/$f" ] && cp "$d/$f" "$M/"; done
  cp "$C/summary.json" "$C/grade_ours.json" "$M/" 2>/dev/null || true
  [ -f "$C/measure.json" ] && cp "$C/measure.json" "$M/"
  for f in film.gif film.mp4 iso_start.png iso_final.png iso_ref.png compare_F.png compare_B.png \
           place_ours_F.png place_ours_B.png place_human_F.png place_human_B.png; do
    [ -f "$C/$f" ] && cp "$C/$f" "$M/"
  done
  cp "$FA/_truth/$stem/stage.json" "$A/staging/truth/${stem}_stage.json" 2>/dev/null || true
  cp "$FA/_truth/$stem/decl.json" "$A/staging/truth/${stem}_decl.json" 2>/dev/null || true
  echo "$nn_stem: $(ls "$M" | wc -l) files, $(du -sk "$M" | cut -f1) KB"
done
cp $FA/_staging/*.py $FA/_staging/*.sh $FA/_staging/teammate_prompt.md "$A/staging/"
cp $FA/CAMPAIGN.md "$A/CAMPAIGN.md"
cp $FA/_issues/filed.tsv "$A/staging/issues_filed.tsv"
du -sh "$A"
