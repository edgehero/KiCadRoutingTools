#!/usr/bin/env bash
# gpm: gather the per-board media and records into a local asset folder
# (pushed to edgehero's gpm-campaign-assets ONLY after Rob approves).
#   bash wk/gpm/_staging/build_assets.sh ASSET_DIR      (from krt-gpm)
set -euo pipefail
A=$1; G=wk/gpm; OI=$HOME/Documents/git/krt-gpm-oi/wk/gpm_oi; PY="$HOME/.venvs/krt/bin/python3 -X utf8"
mkdir -p "$A/media" "$A/staging/truth" "$A/old_issues" "$A/verify"
$PY $G/_staging/summarize.py > "$A/media/TABLE.md"
scrub() {  # local absolute paths -> repo-relative
  sed -e "s#$HOME/Documents/git/krt-gpm-oi/##g" -e "s#$HOME/Documents/git/krt-gpm/##g" \
      -e "s#$HOME/Documents/git/krt-film/#krt-film/#g" -e "s#$HOME/Documents/git/KiCadRoutingTools/##g" \
      -e "s#/private/tmp/claude-[0-9]*/[^ )\"'\`]*#<tmp>#g" -e "s#$HOME#~#g" "$1" > "$2"
}
for d in $G/[0-9][0-9]_*; do
  nn_stem=$(basename "$d"); stem=${nn_stem#??_}; C=$G/_cmp/$stem
  [ -f "$C/summary.json" ] || continue
  M="$A/media/$nn_stem"; mkdir -p "$M"
  for f in REPORT.md TOOL_GAPS.md README.md CHOSEN.json STATE.md; do [ -f "$d/$f" ] && scrub "$d/$f" "$M/$f"; done
  for f in summary.json grade_ours.json grade_ours_runintent.json board_score.json measure.json films.json films.log \
           film_work.log compare_to_human.txt control_to_human.txt drc.log connected.log; do
    [ -f "$C/$f" ] && scrub "$C/$f" "$M/$f"
  done
  for f in film_seed.gif film_seed.mp4 film_flow.gif film_flow.mp4 \
           film_seed_start.png film_seed_final.png film_flow_seeds.png film_flow_fast_route.png film_flow_final.png \
           iso_start.png iso_final.png iso_ref.png compare_F.png compare_B.png \
           place_ours_F.png place_ours_B.png place_human_F.png place_human_B.png film_seed_posediff.txt; do
    [ -f "$C/$f" ] && cp "$C/$f" "$M/"
  done
  # what it was given and what it shipped, plus its repro inputs and helpers, at their own wk/gpm paths
  W="$A/wk/gpm/$nn_stem"; mkdir -p "$W"
  for f in "$d/$stem".kicad_pcb "$d/$stem".kicad_pro "$d/$stem".kicad_dru "$d/$stem".design-brief.json \
           "$d"/intent.json "$d"/mechanical.json "$d"/README.md \
           "$d"/delivered.kicad_pcb "$d"/delivered.kicad_pro "$d"/delivered.kicad_dru "$d"/delivered.design-brief.json; do
    [ -f "$f" ] || continue
    case "$f" in *.json|*.md) scrub "$f" "$W/$(basename "$f")";; *) cp "$f" "$W/";; esac
  done
  for f in delivered.kicad_pcb delivered.kicad_pro delivered.kicad_dru; do [ -f "$d/$f" ] && cp "$d/$f" "$M/"; done
  if [ -d "$d/repro" ]; then
    (cd "$d/repro" && find . -type f -size -8M ! -name '*.pdf' ! -name '*.kicad_prl' ! -path '*/pylib/*' -print0) | while IFS= read -r -d '' f; do
      mkdir -p "$W/repro/$(dirname "$f")"
      case "$f" in *.md|*.txt|*.log|*.json|*.jsonl|*.py|*.sh) scrub "$d/repro/$f" "$W/repro/$f";; *) cp "$d/repro/$f" "$W/repro/$f";; esac
    done
  fi
  for f in "$d"/helpers/*; do
    [ -f "$f" ] || continue
    case "$f" in *.py|*.sh|*.swift|*.txt) mkdir -p "$W/helpers"; scrub "$f" "$W/helpers/$(basename "$f")";; esac
  done
  cp "$G/_truth/$stem/stage.json" "$A/staging/truth/${stem}_stage.json" 2>/dev/null || true
  cp "$G/_truth/$stem/decl.json" "$A/staging/truth/${stem}_decl.json" 2>/dev/null || true
  echo "$nn_stem: $(find "$M" -type f | wc -l | tr -d ' ') files, $(du -sk "$M" | cut -f1) KB"
done
for f in $G/_staging/*.py $G/_staging/*.sh $G/_staging/teammate_prompt.md $G/_staging/boards.tsv; do
  scrub "$f" "$A/staging/$(basename "$f")"
done
mkdir -p "$A/audit" "$A/media/_superseded"
for f in $G/_audit/*.py $G/_audit/*.json; do scrub "$f" "$A/audit/$(basename "$f")"; done
for d in $G/_superseded/[0-9][0-9]_*; do
  S="$A/media/_superseded/$(basename "$d")"; mkdir -p "$S"
  for f in REPORT.md TOOL_GAPS.md README.md CHOSEN.json; do [ -f "$d/$f" ] && scrub "$d/$f" "$S/$f"; done
done
for f in GRADE_NOTES.md LAUNCH.md PIN STAGING_DIFF.md FINDINGS_PREP.md AUDIT.md; do [ -f "$G/$f" ] && scrub "$G/$f" "$A/$f"; done
scrub $G/_phase0/PHASE0.md "$A/PHASE0.md"
[ -f $G/FINDINGS_VERIFIED.md ] && scrub $G/FINDINGS_VERIFIED.md "$A/FINDINGS.md"
scrub $G/FINDINGS_CLUSTERED.md "$A/FINDINGS_CLUSTERED.md"
for f in $G/_verify/V*.md $G/_verify/batches.tsv $G/_verify/verifier_prompt.md $G/_verify/LAUNCH.md; do
  [ -f "$f" ] && scrub "$f" "$A/verify/$(basename "$f")"
done
scrub $OI/OLD_ISSUES.md "$A/old_issues/OLD_ISSUES.md"
for f in $OI/B[0-9].md $OI/batches.tsv $OI/verifier_prompt.md; do [ -f "$f" ] && scrub "$f" "$A/old_issues/$(basename "$f")"; done
[ -d $G/_issues ] && { mkdir -p "$A/issues"; for f in $G/_issues/*.md $G/_issues/*.tsv; do [ -f "$f" ] && scrub "$f" "$A/issues/$(basename "$f")"; done; }
# the verifier reports and the clusters describe boards 11/12's FIRST runs, which live in _superseded/ (AUDIT.md)
for f in "$A"/verify/V*.md "$A/FINDINGS_CLUSTERED.md"; do
  [ -f "$f" ] && sed -i '' -E 's#wk/gpm/(1[12]_(daplink|steppenprobe)|17_environment_sensor)/#wk/gpm/_superseded/\1/#g' "$f"
done
$PY $G/_staging/mirror_cited.py "$A"
# nothing local may survive the scrub
# (the boards themselves keep their designers' own model paths, which are in the public sources)
left=$( { grep -rIl -e "$HOME" "$A"; grep -rIl "/private/tmp/claude" "$A" | grep -v "^$A/staging/"; } | grep -v -e '\.git/' -e 'staging/build_assets.sh$' || true)
if [ -n "$left" ]; then echo "$left"; echo "LOCAL PATHS LEFT (above)"; exit 1; fi
du -sh "$A"
