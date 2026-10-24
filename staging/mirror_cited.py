#!/usr/bin/env python3
"""gpm: copy every `wk/gpm/...` path that the findings, issue drafts or posts cite into ASSET_DIR/wk/gpm/
at the same path, so each repro runs unchanged from a checkout at the pin with the asset branch's `wk/` copied in.

    python3 -X utf8 wk/gpm/_staging/mirror_cited.py ASSET_DIR      (from krt-gpm)

A cited board brings its same-stem siblings (.kicad_pro/.kicad_dru/.design-brief.json/_routetrace.json),
as copy_board does. A cited folder is copied whole when it is under 60 MB. Text files are scrubbed of local
paths. PDFs and pip installs (helpers/pylib) are never copied. Prints what was cited but does not exist.
"""
import glob
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
G = os.path.join(ROOT, 'wk', 'gpm')
A = os.path.abspath(sys.argv[1])
HOME = os.path.expanduser('~')
TEXT = ('.md', '.txt', '.log', '.json', '.jsonl', '.py', '.sh', '.tsv', '.swift')
SIB = ('.kicad_pro', '.kicad_dru', '.design-brief.json', '_routetrace.json')
CAP = 60 * 1024 * 1024

sources = [os.path.join(G, 'FINDINGS_VERIFIED.md'), os.path.join(G, 'FINDINGS_CLUSTERED.md'),
           *glob.glob(os.path.join(G, '_verify', 'V*.md')), *glob.glob(os.path.join(G, '_issues', '*.md')),
           *glob.glob(os.path.join(G, 'POST*.rendered.md'))]
cited = set()
for s in sources:
    if os.path.isfile(s):
        for m in re.finditer(r'wk/gpm/[A-Za-z0-9_.+\-/]+', open(s, encoding='utf-8', errors='replace').read()):
            # boards 11 and 12 were re-run: what the findings cite is their first run (AUDIT.md)
            cited.add(re.sub(r'^wk/gpm/(1[12]_(?:daplink|steppenprobe)|17_environment_sensor)/', r'wk/gpm/_superseded/\1/',
                             m.group(0).rstrip('.,;:)/')))


def scrub(src, dst):
    t = open(src, encoding='utf-8', errors='replace').read()
    for a, b in ((os.path.join(HOME, 'Documents/git/krt-gpm') + '/', ''), (HOME, '~')):
        t = t.replace(a, b)
    t = re.sub(r'/private/tmp/claude-\d+/[^\s)"\'`]*', '<tmp>', t)
    open(dst, 'w', encoding='utf-8').write(t)


def put(src):
    rel = os.path.relpath(src, ROOT)
    if '/pylib/' in rel or rel.endswith('.pdf') or rel.endswith('.kicad_prl'):
        return 0
    dst = os.path.join(A, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    (scrub if rel.endswith(TEXT) else shutil.copy2)(src, dst)
    return os.path.getsize(src)


def files(d):
    for r, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f)
            if not os.path.islink(p) and os.path.isfile(p):
                yield p


def size(d):
    return sum(os.path.getsize(p) for p in files(d))


n = b = 0
missing, big = [], []
for c in sorted(cited):
    p = os.path.join(ROOT, c)
    if os.path.islink(p) or c.rstrip('/').count('/') < 2:
        continue  # a link, or `wk/gpm` itself
    if os.path.isdir(p):
        # a verifier's whole work folder is mostly intermediate boards: its scripts, logs and records
        # are what a reader re-runs; a board it cites by name is copied by name
        small = size(p) <= CAP and not c.startswith('wk/gpm/_verify')
        if not small:
            big.append(c)
        for f in files(p):
            if small or f.endswith(TEXT):  # an over-cap folder still brings its scripts, logs and records
                b += put(f); n += 1
    elif os.path.isfile(p):
        b += put(p); n += 1
        stem = p[:-len('.kicad_pcb')] if p.endswith('.kicad_pcb') else None
        for sfx in SIB if stem else ():
            if os.path.isfile(stem + sfx):
                b += put(stem + sfx); n += 1
    elif not any(ch in c for ch in '*<>$'):
        missing.append(c)
print(f'mirrored {n} files, {b // 1024} KB, from {len(cited)} cited paths')
for c in big:
    print('  folder over 60 MB, text files only:', c)
for c in missing:
    print('  cited but not found:', c)
