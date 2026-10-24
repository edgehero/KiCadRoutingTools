#!/usr/bin/env python3
"""gpm audit C: did any teammate (or its verifier) download a board or read a forbidden copy of one?

    python3 -X utf8 wk/gpm/_audit/audit_transcripts.py        (from krt-gpm)

Reads every tool call in the 20 teammate transcripts and their nested verifier transcripts, and flags:
  NET     anything that can fetch from the network (curl, wget, git clone/fetch/pull, gh api/repo/release,
          pip/npm/brew, urllib/requests, a URL in a shell command, WebFetch);
  WEB     every WebSearch query (listed, for a human read);
  GIT     git history reads (log/show/diff/checkout/cat-file/grep/blame/stash);
  PATH    a forbidden location (_truth, _src, _staging, _cmp, _control, _watch, _phase0, _oldissues,
          _verify, wk/gp14, krt-gp14, gp14-assets, krt-film, the main checkout, KiCad demos, Downloads,
          kicad_files, tests/fixtures, stress manifests/corpora, another board's folder, discussion #118,
          the bodies of #1296-#1360);
  BROAD   a search with no path (it runs in the main checkout) or over ~, /, .., ~/Documents.
Writes audit_transcripts.json; prints a per-agent summary and every flagged call.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.expanduser('~/.claude/projects/-Users-rob-Documents-git-KiCadRoutingTools/'
                       'eb786c6b-7005-4b5c-a65d-b9aba5d8feb9/subagents')
meta = {}
for m in glob.glob(os.path.join(S, '*.meta.json')):
    a = os.path.basename(m)[len('agent-'):-len('.meta.json')]
    meta[a] = json.load(open(m))
team = {a: re.match(r'gpm teammate (\d\d)', d.get('description', '')).group(1)
        for a, d in meta.items() if re.match(r'gpm teammate \d\d', d.get('description', ''))}
agents = dict(team)
for a, d in meta.items():
    if d.get('parentAgentId') in team:
        agents[a] = team[d['parentAgentId']] + 'v'

NET = re.compile(r'\b(curl|wget|aria2c|git\s+(clone|fetch|pull|remote|ls-remote|submodule)|gh\s+(api|repo|release|gist|run|search\s+code|browse)'
                 r'|pip3?\s+(install|download)|python3? -m pip|npm\s+(i|install)|npx|brew|urllib|requests\.|http\.client|socket\.)'
                 r'|https?://|raw\.githubusercontent|codeload\.github', re.I)
GIT = re.compile(r'\bgit\s+(-C\s+\S+\s+)?(log|show|diff|checkout|cat-file|grep|blame|stash|restore|switch|archive|rev-list|ls-tree)\b')
FORB = [r'/_truth\b', r'/_src\b', r'\b_src/', r'/_staging\b', r'/_cmp\b', r'/_control\b', r'/_watch\b', r'/_phase0\b',
        r'/_oldissues\b', r'/_verify\b', r'wk/gp14', r'krt-gp14', r'gp14-assets', r'krt-film', r'krt-gpm-oi', r'gpm_oi',
        r'git/KiCadRoutingTools\b', r'\.\./KiCadRoutingTools', r'kicad_dmg', r'Downloads', r'kicad_files', r'tests/fixtures',
        r'manifest_set', r'stress/(corpus|runs|sets|boards)', r'discussions?/118', r'discussioncomment',
        r'gh\s+issue\s+view\s+(13[0-5]\d|1360|129[6-9])\b']
FORB = re.compile('|'.join(FORB))
BOARD = re.compile(r'wk/gpm/(\d\d)_')


def call_text(name, inp):
    if name == 'Bash':
        return inp.get('command', '')
    if name in ('Read', 'Write', 'Edit', 'NotebookEdit'):
        return inp.get('file_path', '')
    if name in ('Grep', 'Glob'):
        return f'{inp.get("pattern", "")} @ {inp.get("path", "<cwd>")} glob={inp.get("glob", "")}'
    if name == 'WebFetch':
        return inp.get('url', '')
    if name == 'WebSearch':
        return inp.get('query', '')
    if name == 'Agent':
        return inp.get('prompt', '')[:4000]
    return json.dumps(inp)[:2000]


out = {}
for a, nn in sorted(agents.items(), key=lambda x: x[1]):
    f = os.path.join(S, f'agent-{a}.jsonl')
    if not os.path.isfile(f):
        continue
    calls, flags = 0, []
    for line in open(f, encoding='utf-8'):
        try:
            m = json.loads(line).get('message') or {}
        except ValueError:
            continue
        if m.get('role') != 'assistant' or not isinstance(m.get('content'), list):
            continue
        for c in m['content']:
            if not (isinstance(c, dict) and c.get('type') == 'tool_use'):
                continue
            calls += 1
            name, inp = c.get('name'), c.get('input') or {}
            t = call_text(name, inp)
            own = nn[:2]
            kinds = []
            if name == 'WebSearch':
                kinds.append('WEB')
            if name == 'WebFetch' or (name == 'Bash' and NET.search(t)):
                kinds.append('NET')
            if name == 'Bash' and GIT.search(t):
                kinds.append('GIT')
            if name != 'Agent' and (FORB.search(t) or any(b != own for b in BOARD.findall(t))):
                kinds.append('PATH')
            if name in ('Grep', 'Glob') and (not inp.get('path') or re.fullmatch(r'(~|/|\.\.|~(/Documents(/git)?)?)/?', inp.get('path', ''))):
                kinds.append('BROAD')
            if name == 'Bash' and re.search(r'\b(find|grep -r|rg|fd|mdfind|locate)\b[^|;&]*\s(~|/|\.\.|~(/Documents(/git)?)?)(/?\s|$)', t):
                kinds.append('BROAD')
            if kinds:
                flags.append({'kinds': kinds, 'tool': name, 'text': t[:600]})
    out[a] = {'board': nn, 'calls': calls, 'flags': flags}
    by = {}
    for fl in flags:
        for k in fl['kinds']:
            by[k] = by.get(k, 0) + 1
    print(f'{nn:4s} {a} {meta[a].get("description", "")[:40]:40s} calls {calls:5d}  flags {by}')
json.dump(out, open(os.path.join(HERE, 'audit_transcripts.json'), 'w'), indent=1)
