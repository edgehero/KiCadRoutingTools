#!/usr/bin/env python3
"""gpm (from gp14): save a teammate's REPORT.md from its final reply, when the harness refused the write.

    python3 wk/gpm/_staging/save_report.py AGENT_TRANSCRIPT.output NN_STEM
"""
import json
import os
import re
import sys

src, d = sys.argv[1], os.path.join(os.path.dirname(__file__), '..', sys.argv[2])
last = None
for line in open(src, encoding='utf-8'):
    try:
        m = json.loads(line).get('message') or {}
    except ValueError:
        continue
    if m.get('role') != 'assistant':
        continue
    c = m.get('content')
    t = '\n'.join(x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text') \
        if isinstance(c, list) else (c or '')
    if re.search(r'^# .*REPORT', t, re.M):
        last = t
if last is None:
    sys.exit('no "# REPORT" in the final replies')
i = re.search(r'^# .*REPORT', last, re.M).start()
rep = last[i:].rstrip() + '\n'
pre = last[:i].strip().rstrip('-').strip()
if pre:  # the teammate's own summary (delivered sha, scores, stop rule) above the report
    rep += "\n---\n\n## The teammate's final summary (saved with the report by the orchestrator)\n\n" + pre + '\n'
p = os.path.join(d, 'REPORT.md')
if os.path.exists(p):
    sys.exit(f'{p} exists; not overwriting')
open(p, 'w', encoding='utf-8').write(rep)
open(os.path.join(d, '.report_saved_by_orchestrator'), 'w').write(
    "REPORT.md saved by the orchestrator from the teammate's final reply (the harness refused the write).\n")
open(os.path.join(d, 'REPORT_DONE'), 'w').close()
print(f'wrote {p}: {len(rep)} chars, first line: {rep.splitlines()[0]}')
