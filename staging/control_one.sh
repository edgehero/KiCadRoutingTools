#!/usr/bin/env bash
# Run one board's control and print its one-line result:  bash wk/gp14/_staging/control_one.sh STEM
STEM=$1
bash wk/gp14/_staging/control.sh "$STEM" > "wk/gp14/_control/$STEM.log" 2>&1
echo "$STEM: $(grep -E '^route exit|^grade control' "wk/gp14/_control/$STEM.log" | tr '\n' ' ' | cut -c1-300)"
