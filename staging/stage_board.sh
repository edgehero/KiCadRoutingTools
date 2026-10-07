#!/usr/bin/env bash
# fa10 staging for one board.
#   bash wk/fa10/_staging/stage_board.sh NN STEM SRC.kicad_pcb [derive_decl args...]
# Run from the campaign worktree root. Writes wk/fa10/_truth/STEM/ and
# wk/fa10/NN_STEM/. Every step's output is in _truth/STEM/stage.log.
set -euo pipefail
NN=$1; STEM=$2; SRC=$3; shift 3
T=wk/fa10/_truth/$STEM; B=wk/fa10/${NN}_$STEM
mkdir -p "$T" "$B"
exec > >(tee "$T/stage.log") 2>&1
PY="python3 -B -X utf8"
echo "== 1 copy source: $SRC"
$PY py_router/copy_board.py "$SRC" "$T/human.kicad_pcb"
echo "== 2 strip copper"
$PY tests/stress/strip_copper_only.py "$T/human.kicad_pcb" "$T/human_stripped.kicad_pcb"
$PY wk/fa10/_staging/strip_extra.py "$T/human_stripped.kicad_pcb"
echo "== 3 pile"
$PY .claude/skills/pcb-free-agent/scripts/make_unplaced.py "$T/human_stripped.kicad_pcb" "$B/$STEM.kicad_pcb"
$PY - "$B/$STEM.kicad_pcb" <<'EOF'
import json, sys
sys.path[:0] = ['tests/stress', 'py_router', 'py_placer', 'tests']
from stage_unaided import sanitize_staged_project
print('sanitize:', json.dumps(sanitize_staged_project(sys.argv[1]), default=str)[:600])
EOF
echo "== 3b sanitize the pile (local zones, text angles)"
$PY wk/fa10/_staging/sanitize_pile.py "$B/$STEM.kicad_pcb"
echo "== 4 declarations"
$PY wk/fa10/_staging/derive_decl.py "$T/human_stripped.kicad_pcb" --stem "$STEM" --out "$B" --json-out "$T/decl.json" "$@"
MECH=(); [ -f "$B/mechanical.json" ] && MECH=(--mechanical "$B/mechanical.json") || MECH=(--no-mechanical)
echo "== 5a validate on the human board"
$PY py_tools/check_floorplan.py "$T/human_stripped.kicad_pcb" --brief "$B/$STEM.design-brief.json" "${MECH[@]}" \
    --emit-intent "$T/human_intent.json" --decaps-from "$T/human_stripped.kicad_pcb" || echo "EMIT-ON-HUMAN exit $?"
$PY py_tools/check_floorplan.py "$T/human_stripped.kicad_pcb" --intent "$T/human_intent.json" --brief "$B/$STEM.design-brief.json" \
    "${MECH[@]}" --require-brief-coverage --json "$T/human_grade.json" || echo "GRADE-ON-HUMAN exit $?"
echo "== 5b emit the run intent on the pile"
$PY py_tools/check_floorplan.py "$B/$STEM.kicad_pcb" --emit-intent "$B/intent.json" --allow-unplaced \
    --decaps-from "$T/human_stripped.kicad_pcb" || echo "EMIT-ON-PILE exit $?"
$PY wk/fa10/_staging/redact_intent.py "$B/intent.json"
echo "== 6 record"
$PY - "$T" "$B" "$STEM" "$SRC" <<'EOF'
import hashlib, json, os, sys
T, B, stem, src = sys.argv[1:]
def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else None
files = {n: sha(os.path.join(B, n)) for n in sorted(os.listdir(B)) if os.path.isfile(os.path.join(B, n))}
json.dump({'stem': stem, 'source': src, 'source_sha256': sha(src), 'inputs': files},
          open(os.path.join(T, 'stage.json'), 'w'), indent=2)
print(json.dumps(files, indent=1))
EOF
