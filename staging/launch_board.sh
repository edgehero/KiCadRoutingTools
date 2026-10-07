#!/usr/bin/env bash
# fa10: prepare one staged board for its teammate.
#   bash wk/fa10/_staging/launch_board.sh NN STEM      (from the campaign worktree root)
# 1. the human placement goes into the truth dir as control.kicad_pcb, which the
#    cheat watcher's fence audit compares the work dir against;
# 2. fence_audit --mode create records the work dir's starting files;
# 3. the bug and cheat watchers start, detached, logging to wk/fa10/_watch/STEM;
# 4. the teammate prompt is written to wk/fa10/_staging/prompt_NN.md.
set -euo pipefail
NN=$1; STEM=$2
T=wk/fa10/_truth/$STEM; W=wk/fa10/${NN}_$STEM; L=wk/fa10/_watch/$STEM
mkdir -p "$L"
python3 -B -X utf8 py_router/copy_board.py "$T/human_stripped.kicad_pcb" "$T/control.kicad_pcb"
python3 -B -X utf8 tests/stress/fence_audit.py --control "$T/control.kicad_pcb" --workdir "$W" --mode create 2>&1 \
    | grep -v '^WARNING' | tail -3
nohup python3 -X utf8 tests/stress/run_watch.py bugs --workdir "$W" > "$L/bugs.log" 2>&1 &
nohup python3 -X utf8 tests/stress/run_watch.py cheats --workdir "$W" --truthdir "$T" --done "$W/DONE" \
    --report-done "$W/REPORT_DONE" --report-wait 0 > "$L/cheats.log" 2>&1 &
sed -e 's/{SHA}/04a2c68d/g' -e "s/{NN}/$NN/g" -e "s/{STEM}/$STEM/g" wk/fa10/_staging/teammate_prompt.md \
    > "wk/fa10/_staging/prompt_$NN.md"
sleep 8
head -2 "$L/cheats.log" "$L/bugs.log"
grep -c '{' "wk/fa10/_staging/prompt_$NN.md" || true
