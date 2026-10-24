#!/usr/bin/env python3
"""gpm: file every draft in _issues/plan.tsv on drandyhaas/KiCadRoutingTools, in plan order, filling the links the
drafts carry (the posted comments, the asset commit). Resumable: _issues/filed.tsv (ID, URL, title) records each
issue as soon as it exists, and a re-run skips those.

    python3 -X utf8 wk/gpm/_staging/file_issues.py SHA [--dry-run]
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SHA = sys.argv[1]
DRY = '--dry-run' in sys.argv
posted = json.load(open(os.path.join(G, 'posted.json')))
FILL = {'__MAIN__': posted['POST']['url'], '__REPLY__': posted['POST_3']['url'],
        '__TREE__': f'https://github.com/edgehero/KiCadRoutingTools/tree/{SHA}',
        '__BLOB__': f'https://github.com/edgehero/KiCadRoutingTools/blob/{SHA}'}
REC = os.path.join(G, '_issues', 'filed.tsv')
filed = {l.split('\t')[0] for l in open(REC, encoding='utf-8')} if os.path.exists(REC) else set()
plan = [l.rstrip('\n').split('\t') for l in open(os.path.join(G, '_issues', 'plan.tsv'), encoding='utf-8')]
for k, kind, title in plan:
    if k in filed:
        continue
    body = open(os.path.join(G, '_issues', f'{k}.md'), encoding='utf-8').read()
    for a, b in FILL.items():
        body = body.replace(a, b)
    left = re.findall(r'__[A-Z]+__', body)
    if left:
        sys.exit(f'{k}: placeholders left {left}')
    if DRY:
        print(f'{k}: {len(body)} chars, title {len(title)}: {title[:90]}')
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(body)
    r = subprocess.run(['gh', 'issue', 'create', '--repo', 'drandyhaas/KiCadRoutingTools', '--title', title,
                        '--body-file', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    if r.returncode:
        sys.exit(f'{k}: gh issue create failed: {r.stderr.strip()[:400]}')
    url = r.stdout.strip().splitlines()[-1]
    with open(REC, 'a', encoding='utf-8') as fh:
        fh.write(f'{k}\t{url}\t{title}\n')
    print(k, url, flush=True)
    time.sleep(5)
