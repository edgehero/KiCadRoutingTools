#!/usr/bin/env python3
"""gpm: compose one upstream issue per verified finding, and one per gp14 issue that is still broken or only
partly fixed on main.

    python3 -X utf8 wk/gpm/_staging/compose_issues.py

Reads wk/gpm/_verify/V*.md (finding verdicts) and krt-gpm-oi/wk/gpm_oi/B*.md (old-issue re-checks).
Writes wk/gpm/_issues/<ID>.md (body) and wk/gpm/_issues/plan.tsv (ID, kind, title).
Only CONFIRMED / CONFIRMED-PARTIAL findings and PARTLY / STILL BROKEN old issues are composed; IDs in SKIP
are not (they go to an existing issue as evidence, or need Rob's call first).

The links __MAIN__ / __REPLY__ (the posted comments) and __TREE__ / __BLOB__ (the pushed asset commit) are
filled in by file_issues at filing time.
"""
import glob
import os
import re
import textwrap

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OI = os.path.expanduser('~/Documents/git/krt-gpm-oi/wk/gpm_oi')
SKIP = set(os.environ.get('GPM_SKIP', '').split())
STOP = re.compile(r'^(Notes for the filer|Outputs are under|All (my )?outputs|Everything I ran|V\d: CONFIRMED)', re.M)


def normalize(b):
    """One shape for every verifier's block: `- key: value` labels (V2/V4/V5 bolded them) and an issue
    draft without blockquote marks, its title on the first line (bold or backticked)."""
    b = re.sub(r'^(\s*)- \*\*([^*\n]+?):?\*\*:?', r'\1- \2:', b, flags=re.M)
    return re.sub(r'^(\s*)> ?', r'\1', b, flags=re.M)


def blocks(text, head):
    return {m.group(1): (m.group(2).strip(), normalize(m.group(3)))
            for m in re.finditer(head + r'(.*?)(?=^### |\Z)', text, re.M | re.S)}


def bullet(b, key):
    """A top-level '- key: ...' bullet with its indented continuation, dedented."""
    m = re.search(r'^- ' + key + r'[^:\n]*:\s?(.*(?:\n(?!- |\S).*)*)', b, re.M)
    if not m:
        return ''
    first, _, rest = m.group(1).partition('\n')
    return (first.strip() + ('\n' + textwrap.dedent(rest).rstrip() if rest.strip() else '')).strip()


def draft(b):
    i = b.find('- issue draft:')
    if i < 0:
        return None, None
    d = STOP.split(b[i + len('- issue draft:'):])[0]
    d = textwrap.dedent(d.strip('\n')).strip()
    title, _, body = d.partition('\n')
    title = title.strip().strip('*`').strip()
    return title, textwrap.dedent(body).strip()


FOOT = ('\n\n---\nFound in the gpm campaign (20 boards through `/plan-pcb-placement full` on main bda59fa0, '
        'every part starting off the board): [results](__MAIN__), [findings](__REPLY__), finding **{k}**. '
        'A separate verifier re-ran it at the pin (verdict {v}); the full verdict is in '
        '[`verify/{batch}.md`](__BLOB__/verify/{batch}.md). The `wk/gpm/...` inputs are on '
        '[`gpm-campaign-assets`](__TREE__) at the same paths: copy its `wk/` into a checkout at bda59fa0 and run '
        'from the root.')
OLD_FOOT = ('\n\n---\nFollow-up to #{n}, closed {how}. Re-checked in the gpm campaign (20 boards through '
            '`/plan-pcb-placement full` on main bda59fa0): [results](__MAIN__), [old issues](__REPLY__). '
            'The re-check is in [`old_issues/{batch}.md`](__BLOB__/old_issues/{batch}.md); its `wk/gp14/...` inputs '
            'are the ones #{n} cites, on `gp14-campaign-assets`.')

os.makedirs(os.path.join(G, '_issues'), exist_ok=True)
plan = []
for f in sorted(glob.glob(os.path.join(G, '_verify', 'V[0-9].md'))):
    batch = os.path.basename(f)[:-3]
    for k, (v, b) in sorted(blocks(open(f, encoding='utf-8').read(), r'^### ([GM]\d\d) -- VERDICT: ([A-Z][A-Z\- ]+?)(?:\s*\([^\n]*\))?\.?\s*$').items()):
        if v not in ('CONFIRMED', 'CONFIRMED-PARTIAL') or k in SKIP:
            continue
        title, body = draft(b)
        if not title:
            print(f'{k}: no issue draft in {batch}')
            continue
        part = ('\n\n*Verified in part: the claim as first reported was broader; what holds is what is described '
                'here. The verdict names what did not hold.*') if v == 'CONFIRMED-PARTIAL' else ''
        where = []
        for key, label in (('cause', 'Cause (at bda59fa0)'), ('head', 'Main head 0c05be08'), ('upstream', 'Upstream')):
            s = bullet(b, key)
            if s:
                s = re.sub(r'^0c05be08:\s*', '', s)
                q = re.match(r'\((sure|likely)[^)]*\):?\s*', s)
                if q:
                    label, s = label[:-1] + f', {q.group(1)})', s[q.end():]
                if s.startswith('- '):
                    s = '\n' + s
                where.append(f'- {label}: ' + s.replace('\n', '\n  '))
        sev = re.search(r'severity:?\**:?\s*\**([a-z][a-z\-]*)', b, re.I)
        out = body + part + '\n\n**Where**\n' + '\n'.join(where) + FOOT.format(k=k, v=v, batch=batch)
        out = re.sub(r'wk/gpm/(1[12]_(?:daplink|steppenprobe))/', r'wk/gpm/_superseded/\1/', out)  # first runs (AUDIT.md)
        open(os.path.join(G, '_issues', f'{k}.md'), 'w', encoding='utf-8').write(out.strip() + '\n')
        plan.append((k, f'finding {v} {sev.group(1) if sev else "?"}', title))

for f in sorted(glob.glob(os.path.join(OI, 'B[0-9].md'))):
    batch = os.path.basename(f)[:-3]
    for m in re.finditer(r'^### ([HML]\d\d) \(#(\d+)\) -- VERDICT: ([A-Z][A-Z ]+?)(?:\s*\([^\n]*\))?\s*$(.*?)(?=^### |\Z)',
                         open(f, encoding='utf-8').read(), re.M | re.S):
        fid, n, v, b = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
        k = f'O{n}'
        if v not in ('PARTLY', 'STILL BROKEN') or k in SKIP:
            continue
        d = re.search(r'^- \*\*[Nn]ew-issue draft[^*\n]*:\*\*\s*(.*(?:\n(?!- \*\*|### ).*)*)', b, re.M)
        if not d:
            print(f'{k} ({fid}): no new-issue draft in {batch}')
            continue
        how = 'as not planned' if 'NOT_PLANNED' in b or 'not planned' in b.lower() else 'as completed'
        body = re.sub(r'^\s*> ?', '', textwrap.dedent(d.group(1)), flags=re.M).strip()
        out = body + OLD_FOOT.format(n=n, how=how, batch=batch)
        open(os.path.join(G, '_issues', f'{k}.md'), 'w', encoding='utf-8').write(out.strip() + '\n')
        t = re.search(r'\| ' + fid + r' \| #' + n + r' \| [A-Z ]+ \| (.+?) \|', open(os.path.join(OI, 'OLD_ISSUES.md'), encoding='utf-8').read())
        plan.append((k, f'old #{n} {v} (closed {how})', (t.group(1).strip() if t else fid) + ' (still on main)'))

with open(os.path.join(G, '_issues', 'plan.tsv'), 'w', encoding='utf-8') as fh:
    for row in plan:
        fh.write('\t'.join(row) + '\n')
print(len(plan), 'issues composed:', sum(1 for r in plan if r[0][0] == 'G'), 'findings,',
      sum(1 for r in plan if r[0][0] == 'O'), 'old-issue follow-ups')
