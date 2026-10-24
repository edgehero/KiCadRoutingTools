#!/usr/bin/env python3
"""gp14 staging (ported from fa10): an intent must not name the source board's path.

    python3 -X utf8 wk/gpm/_staging/redact_intent.py INTENT.json

`--decaps-from` records `context.decap_census.reference_board` and repeats the
path in `budget_withheld` strings; that path is the answer key, one Read away.
Every string carrying a source-board path is rewritten in place to say the
source was withheld. The numbers derived from it stay.
"""
import json
import re
import sys

PATH = re.compile(r'[A-Za-z]:[\\/][^\s"\']*?\.kicad_pcb|/(?:Users|private|tmp|Volumes)/[^\s"\']*?\.(?:kicad_pcb|json)'
                  r'|[^\s"\']*(?:_truth|_src|krt-run\d+)[^\s"\']*?\.(?:kicad_pcb|json)'
                  r'|[^\s"\']*(?:human_stripped|glasgow_ref|stickhub_ref)\.kicad_pcb')
MARKERS = ('_truth', '_src/', 'krt-run', 'human_stripped', 'glasgow_ref', 'stickhub_ref', '/Users/')
HITS = 0


def walk(v):
    global HITS
    if isinstance(v, dict):
        return {k: walk(x) for k, x in v.items()}
    if isinstance(v, list):
        return [walk(x) for x in v]
    if isinstance(v, str):
        new = PATH.sub('<the source board, withheld>', v)
        if new != v and any(t in v for t in MARKERS):
            HITS += 1
            return new
        return v
    return v


path = sys.argv[1]
doc = json.load(open(path, encoding='utf-8'))
doc = walk(doc)
json.dump(doc, open(path, 'w', encoding='utf-8'), indent=2)
left = [t for t in MARKERS if t in open(path, encoding='utf-8').read()]
print(f'redact_intent: {HITS} string(s) rewritten; remaining source markers: {left or "none"}')
if left:
    raise SystemExit(2)
