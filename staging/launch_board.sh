#!/usr/bin/env bash
# gp14: prepare one staged board for its teammate (ported from fa10).
#   bash wk/gpm/_staging/launch_board.sh NN STEM SHA ROUTE_CAP   (from krt-gpm; ROUTE_CAP 2 on a hard board, else 3)
# 1. fence_audit --mode create (krt-film's; the branch removed it) records the work
#    dir's starting files against the human placement;
# 2. the bug and cheat watchers start, detached, logging to wk/gpm/_watch/STEM;
# 3. the teammate prompt is written to wk/gpm/_staging/prompt_NN.md.
set -euo pipefail
export PATH="$HOME/.venvs/krt/bin:$PATH"
NN=$1; STEM=$2; SHA=$3; CAP=${4:-3}
T=wk/gpm/_truth/$STEM; W=wk/gpm/${NN}_$STEM; L=wk/gpm/_watch/$STEM
FILM_WT=$(cd ../krt-film && pwd)
[ "$(git rev-parse --short=8 HEAD)" = "${SHA:0:8}" ] || { echo "worktree is at $(git rev-parse --short=8 HEAD), not $SHA"; exit 2; }
mkdir -p "$L"
python3 -B -X utf8 "$FILM_WT/tests/stress/fence_audit.py" --control "$T/human_stripped.kicad_pcb" --workdir "$W" --mode create 2>&1 \
    | grep -v '^WARNING' | tail -3
nohup python3 -X utf8 tests/stress/run_watch.py bugs --workdir "$W" > "$L/bugs.log" 2>&1 &
nohup python3 -X utf8 tests/stress/run_watch.py cheats --workdir "$W" --done "$W/DONE" \
    --report-done "$W/REPORT_DONE" --report-wait 0 > "$L/cheats.log" 2>&1 &
sed -e "s/{SHA}/${SHA:0:8}/g" -e "s/{ROUTE_CAP}/$CAP/g" -e "s/{NN}/$NN/g" -e "s/{STEM}/$STEM/g" wk/gpm/_staging/teammate_prompt.md \
    > "wk/gpm/_staging/prompt_$NN.md"
sleep 5
head -2 "$L/cheats.log" "$L/bugs.log"
echo "placeholders left: $(grep -c '{[A-Z]*}' "wk/gpm/_staging/prompt_$NN.md" || true)"
