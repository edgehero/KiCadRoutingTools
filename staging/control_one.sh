#!/usr/bin/env bash
# Run one board's control and print its one-line result:  bash wk/gpm/_staging/control_one.sh STEM
STEM=$1
bash wk/gpm/_staging/control.sh "$STEM" > "wk/gpm/_control/$STEM.log" 2>&1
echo "$STEM: $(grep -E '^route exit|^grade control' "wk/gpm/_control/$STEM.log" | tr '\n' ' ' | cut -c1-300)"
