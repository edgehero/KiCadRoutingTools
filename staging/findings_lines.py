#!/usr/bin/env python3
"""gpm: one line per verified finding, grouped by verifier batch, for the findings reply.

    python3 -X utf8 wk/gpm/_staging/findings_lines.py > wk/gpm/_staging/post_findings_auto.md

C = confirmed, P = confirmed in part, N = not a bug as claimed, R = not reproducible; 'head' = still so
at main 0c05be08. Hand-edit the output into post_findings.md; this only saves the copying.
"""
import glob
import os
import re
import sys

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def normalize(b):
    b = re.sub(r'^(\s*)- \*\*([^*\n]+?):?\*\*:?', r'\1- \2:', b, flags=re.M)
    return re.sub(r'^(\s*)> ?', r'\1', b, flags=re.M)


def blocks(text, head):
    return {m.group(1): (m.group(2).strip(), normalize(m.group(m.lastindex)))
            for m in re.finditer(head + r'(.*?)(?=^### |\Z)', text, re.M | re.S)}


def bullet(b, key):
    m = re.search(r'^- ' + key + r'[^:\n]*:\s?(.*)', b, re.M)
    return m.group(1).strip() if m else ''

CODE = {'CONFIRMED-PARTIAL': 'P', 'CONFIRMED': 'C', 'NOT A BUG': 'N', 'NOT REPRODUCIBLE': 'R'}
topics = dict(l.rstrip('\n').split('\t')[:2] for l in open(os.path.join(G, '_verify', 'batches.tsv')) if l[0] == 'V')
tally = {}
for f in sorted(glob.glob(os.path.join(G, '_verify', 'V[0-9].md'))):
    batch = os.path.basename(f)[:-3]
    print(f'\n#### {topics.get(batch, batch)}\n')
    for k, (v, b) in sorted(blocks(open(f, encoding='utf-8').read(), r'^### ([GM]\d\d) -- VERDICT: ([A-Z][A-Z\- ]+)([^\n]*)$').items()):
        v = v.split('(')[0].strip().rstrip('.')
        code = next((c for name, c in CODE.items() if v.startswith(name)), '?')
        tally[code] = tally.get(code, 0) + 1
        title = bullet(b, 'title').split('\n')[0].rstrip('.')
        boards = re.search(r'^- boards:\s*(.*?)\s*(?:\**severity.*)?$', b, re.M | re.I)
        head = bullet(b, 'head').split('\n')[0]
        h = 'head' if head.lower().startswith('unchanged') else 'head?'
        print(f'- **{k}** {code}, {h}: {title} ({(boards.group(1).strip().rstrip('.*').strip() if boards else "?")}).')
print('\n<!-- tally', tally, '-->')
