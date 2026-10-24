#!/bin/zsh
# Grade a routed board as DONE is measured in this run: board_score + check_complete with the
# board's declared DRC size floors; then (disclosure only) board_score with the Power-netclass
# 0.3 mm width as a per-net minimum. usage (repo root): zsh helpers/grade_quick.sh <board.kicad_pcb>
R=wk/gpm/12_steppenprobe
b=$1
SPEC=(--min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3 --net-min-widths $R/net_min_widths.json)
python3 -X utf8 py_tools/board_score.py $b --intent $R/intent_run.json --baseline $R/fixed.kicad_pcb $SPEC --json ${b%.kicad_pcb}.score.json --quiet 2>&1 | grep -E '^BLOCKING'
python3 -X utf8 check_complete.py $b --intent $R/intent_run.json --baseline $R/fixed.kicad_pcb $SPEC 2>&1 | grep -E '^ *VERDICT' | cut -c1-200
python3 -X utf8 py_tools/board_score.py $b --intent $R/intent_run.json --baseline $R/fixed.kicad_pcb $SPEC --net-min-widths $R/net_min_widths.json --json ${b%.kicad_pcb}.widths.json --quiet >/dev/null 2>&1
python3 -c "
import json;j=json.load(open('${b%.kicad_pcb}.widths.json'));nw=j['components']['net_widths']
print('  [disclosure] power copper under 0.3mm (mm, narrowest):', {k:(v['length_under_mm'],v['narrowest_mm']) for k,v in (nw.get('nets') or {}).items()})"
