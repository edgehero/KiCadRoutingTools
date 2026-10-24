#!/usr/bin/env python3
"""gp14: turn POST.rendered.md / POST_2.rendered.md (from post_boards.py) into the posted text:
asset links at the pushed commit, issue numbers after each finding ID, and checks that every
linked asset exists and each comment fits GitHub's 65,536-character limit.

    python3 -X utf8 wk/gpm/_staging/post_finalize.py      # writes POST.final.md, POST_2.final.md
"""
import os
import re
import sys

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
A = os.path.expanduser('~/Documents/git/gp14-assets')
SHA = '0e209606296a9435ea9fd5575bc35ca51eca3d39'
RAW = f'https://raw.githubusercontent.com/edgehero/KiCadRoutingTools/{SHA}'
BLOB = f'https://github.com/edgehero/KiCadRoutingTools/blob/{SHA}'
TREE = f'https://github.com/edgehero/KiCadRoutingTools/tree/{SHA}'

num = {}
for line in open(os.path.join(G, '_issues', 'filed.tsv'), encoding='utf-8'):
    k, u, _ = line.rstrip('\n').split('\t')
    num[k] = '#' + u.rsplit('/', 1)[1]
num['H01'], num['H03'] = '#1291', '#162'


def links(s):
    return s.replace('](__BLOB__)', f']({TREE})').replace('__RAW__', RAW).replace('__BLOB__', BLOB)


def outside_links(s, fn):
    parts = re.split(r'(\]\([^)]*\))', s)
    return ''.join(p if p.startswith('](') else fn(p) for p in parts)


def plain_ids(p):
    return re.sub(r'(?<![\w#/])([HML]\d\d)(?![\w])',
                  lambda m: f'{m.group(1)} {num[m.group(1)]}' if m.group(1) in num else m.group(0), p)


def bold_ids(p):
    return re.sub(r'\*\*([HML]\d\d)\*\*',
                  lambda m: f'**{m.group(1)}** {num[m.group(1)]}' if m.group(1) in num else m.group(0), p)


main = outside_links(links(open(os.path.join(G, 'POST.rendered.md'), encoding='utf-8').read()), plain_ids)
main = main.replace('Nothing is filed yet; the bundles are in the reply below, with issue drafts ready.',
                    'Filed upstream as **#1296–#1360** (65 new issues), with evidence added to #1291 and #162; '
                    'the bundles are in the reply below.')
reply = outside_links(links(open(os.path.join(G, 'POST_2.rendered.md'), encoding='utf-8').read()), bold_ids)
reply = reply.replace('Full verdicts with repro commands and issue drafts are in',
                      'Each finding is filed: **#1296–#1360** (65 new issues; L07 and M22 are already fixed at head, '
                      'H01 and H03 went to #1291 and #162 as evidence). Full verdicts with repro commands are in')
reply = reply.replace('**H01** #1291 duplicate of #1291:', '**H01** duplicate of #1291 (evidence added there):')
reply = reply.replace('**H03** #162 C, head, main:', '**H03** C, head, main, evidence added to #162:')
reply = reply.replace('Evidence for #162.', '')

ok = True
for name, text in (('POST.final.md', main), ('POST_2.final.md', reply)):
    bad = [u for u in re.findall(r'\((https://(?:raw\.githubusercontent\.com|github\.com)/edgehero/KiCadRoutingTools/'
                                 r'[^)\s]+)\)', text)
           if u.split(SHA, 1)[1].lstrip('/') and not os.path.exists(os.path.join(A, u.split(SHA, 1)[1].lstrip('/')))]
    left = re.findall(r'__RAW__|__BLOB__|<!-- [A-Z]+ -->', text)
    print(f'{name}: {len(text)} chars, missing link targets {len(bad)}, placeholders left {len(left)}')
    ok &= not bad and not left and len(text) <= 65536
    open(os.path.join(G, name), 'w', encoding='utf-8').write(text)
sys.exit(0 if ok else 1)
