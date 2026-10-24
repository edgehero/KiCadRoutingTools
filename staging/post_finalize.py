#!/usr/bin/env python3
"""gpm: turn POST.rendered.md / POST_2.rendered.md / POST_3.rendered.md (from post_boards.py) into the posted text:
asset links at the pushed commit and, once the issues are filed, issue numbers after each finding ID. Checks that
every linked asset exists and each comment fits GitHub's 65,536-character limit.

    python3 -X utf8 wk/gpm/_staging/post_finalize.py SHA            # links only -> POST*.final.md
    python3 -X utf8 wk/gpm/_staging/post_finalize.py SHA --issues   # + numbers from _issues/filed.tsv

Exit 0 = every check passed.
"""
import os
import re
import sys

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
A = os.path.expanduser('~/Documents/git/gpm-assets')
SHA = sys.argv[1]
RAW = f'https://raw.githubusercontent.com/edgehero/KiCadRoutingTools/{SHA}'
BLOB = f'https://github.com/edgehero/KiCadRoutingTools/blob/{SHA}'
TREE = f'https://github.com/edgehero/KiCadRoutingTools/tree/{SHA}'

num = {}
if '--issues' in sys.argv:
    for line in open(os.path.join(G, '_issues', 'filed.tsv'), encoding='utf-8'):
        k, u = line.rstrip('\n').split('\t')[:2]
        num[k] = '#' + u.rsplit('/', 1)[1]
    # the six clusters that equal gp14 issues were filed as those issues' follow-ups
    for g, o in (('G13', 'O1318'), ('G22', 'O1343'), ('G24', 'O1359'), ('G27', 'O1349'), ('G37', 'O1311'), ('G43', 'O1320')):
        if o in num:
            num[g] = num[o]


def links(s):
    return s.replace('](__BLOB__)', f']({TREE})').replace('__RAW__', RAW).replace('__BLOB__', BLOB)


def outside_links(s, fn):
    parts = re.split(r'(\]\([^)]*\))', s)
    return ''.join(p if p.startswith('](') else fn(p) for p in parts)


def ids(p):
    """G01 / M01 -> 'G01 #N' (bold or plain), once per mention, never inside a link target."""
    p = re.sub(r'\*\*([GM]\d\d)\*\*', lambda m: f'**{m.group(1)}** {num[m.group(1)]}' if m.group(1) in num else m.group(0), p)
    return re.sub(r'(?<![\w#/*])([GM]\d\d)(?![\w*])',
                  lambda m: f'{m.group(1)} {num[m.group(1)]}' if m.group(1) in num else m.group(0), p)


def old_rows(p):
    """the gp14 table: '| #1320 | ...' -> '| #1320 → #N | ...' (the follow-up filed for it)."""
    return re.sub(r'^\| #(13\d\d) \|', lambda m: f'| #{m.group(1)} → {num["O" + m.group(1)]} |' if 'O' + m.group(1) in num
                  else m.group(0), p, flags=re.M)


FILED = ('The bundles are in the replies below, with issue drafts ready; nothing is filed yet.',
         'Nothing is filed yet; there is an issue draft for each confirmed or partly confirmed finding.')
ok = True
for name in ('POST', 'POST_2', 'POST_3'):
    text = links(open(os.path.join(G, f'{name}.rendered.md'), encoding='utf-8').read())
    if num:
        nums = {int(v[1:]) for v in num.values()}
        lo, hi = min(nums), max(nums)
        text = outside_links(text, ids)
        text = old_rows(text)
        text = text.replace(FILED[0], f'The bundles are in the replies below. Every confirmed or partly confirmed finding, '
                                      f'and every gp14 issue still open on main, is filed: **#{lo}–#{hi}** ({len(nums)} issues).')
        text = text.replace(FILED[1], f'Each confirmed or partly confirmed finding is filed; its number follows its ID '
                                      f'(**#{lo}–#{hi}**, {len(nums)} issues, the gp14 follow-ups included).')
    bad = [u for u in re.findall(r'\((https://(?:raw\.githubusercontent\.com|github\.com)/edgehero/KiCadRoutingTools/'
                                 r'[^)\s]+)\)', text)
           if u.split(SHA, 1)[1].lstrip('/') and not os.path.exists(os.path.join(A, u.split(SHA, 1)[1].lstrip('/')))]
    left = re.findall(r'__RAW__|__BLOB__|<!-- [A-Z_0-9]+ -->', text)
    print(f'{name}.final.md: {len(text)} chars, missing link targets {len(bad)}, placeholders left {len(left)}', bad[:3])
    ok &= not bad and not left and len(text) <= 65536
    open(os.path.join(G, f'{name}.final.md'), 'w', encoding='utf-8').write(text)
sys.exit(0 if ok else 1)
