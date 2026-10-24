#!/usr/bin/env bash
# Stage board NN from boards.tsv:  bash wk/gpm/_staging/stage_one.sh NN   (from krt-gpm)
set -uo pipefail
NN=$1
LINE=$(awk -F'\t' -v n="$NN" '$1==n' wk/gpm/_staging/boards.tsv)
[ -n "$LINE" ] || { echo "no board $NN"; exit 2; }
STEM=$(printf '%s' "$LINE" | cut -f2); SRC=$(printf '%s' "$LINE" | cut -f3); ARGS=$(printf '%s' "$LINE" | cut -f5)
if [[ "$ARGS" == *"--why "* ]]; then
  FIX=${ARGS%%--why *}; WHY=${ARGS#*--why }
  # shellcheck disable=SC2086
  bash wk/gpm/_staging/stage_board.sh "$NN" "$STEM" "$SRC" $FIX --why "$WHY" > /dev/null 2>&1
else
  bash wk/gpm/_staging/stage_board.sh "$NN" "$STEM" "$SRC" > /dev/null 2>&1
fi
echo "$NN $STEM exit $? :: $(tail -1 wk/gpm/_truth/$STEM/stage.log | cut -c1-250)"
