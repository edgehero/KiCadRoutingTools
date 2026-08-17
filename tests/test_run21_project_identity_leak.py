#!/usr/bin/env python3
"""The staged `.kicad_pro` must not name the source, in ANY key.

`sanitize_staged_project` sanitised `meta.filename` and a list of five known
author keys, and `fence_audit --mode create` still refused run 21's work dir
on the first try:

    LEAK board.kicad_pro: NAMES THE SOURCE:
      "_note": "MIGRATED, not authored and not guessed. tigard is a KiCad 5 ...
      "source": "https://raw.githubusercontent.com/tigard-tools/tigard/...

Both strings live under `kicad_routing_tools.floor_provenance` -- an
annotation THIS REPO authored, in a node the key list never contained, and
the URL serves the upstream board pose for pose. So the stager reported
success while handing the run a path back to the original placement.

The lesson is the one `stage_unaided`'s own comments already state about
extensions and stems -- "the next carrier will have a different name" -- and
the key list is not a way to honour it. The backstop is content-shaped: a
string that spells the source's stem is a leak wherever it lives.

This file pins that, and pins the half that must NOT change with it: every
value the #441 floor is graded at is numeric, so the sweep must leave the
floor untouched. A sweep that redacted the clearance would trade an identity
leak for a mis-graded board.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
          os.path.join(REPO, 'py_placer'), os.path.join(REPO, 'tests', 'stress')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'kicad_files', 'tigard.kicad_pcb')
PROJECT = os.path.join(REPO, 'kicad_files', 'tigard.kicad_pro')

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not (os.path.isfile(BOARD) and os.path.isfile(PROJECT)):
    print("SKIP: tigard fixture missing")
    sys.exit(0)

import fence_audit as FA
import stage_unaided as SU


def staged(stem_arg):
    """Copy the REAL leaking project into a work dir and sanitise it."""
    d = tempfile.mkdtemp()
    board = os.path.join(d, 'board.kicad_pcb')
    shutil.copyfile(BOARD, board)
    shutil.copyfile(PROJECT, os.path.join(d, 'board.kicad_pro'))
    out = SU.sanitize_staged_project(board, stem_arg)
    with open(os.path.join(d, 'board.kicad_pro'), encoding='utf-8') as f:
        return out, json.load(f), os.path.join(d, 'board.kicad_pro')


# --------------------------------------------------------------------------
# Without the stem, the leak is still there. This is the run-21 observation,
# and it is asserted rather than described so the fix cannot be "simplified"
# back out and read as always-passing.
# --------------------------------------------------------------------------
_old, _olddoc, oldpro = staged(None)
check("key-only sanitisation leaves the source named (the run-21 leak)",
      FA._names_control(oldpro, 'tigard'),
      f"{len(FA._names_control(oldpro, 'tigard'))} string(s) still name it")

# --------------------------------------------------------------------------
# With it, the fence's own detector is satisfied.
# --------------------------------------------------------------------------
rep, doc, pro = staged('tigard')
check("the stem sweep clears fence_audit's identity check",
      FA._names_control(pro, 'tigard') == [],
      str(FA._names_control(pro, 'tigard'))[:160])
check("and it is DECLARED, by key path, not silently dropped",
      rep.get('redacted_source_strings'),
      str(rep.get('redacted_source_strings')))
check("the keys it names are the ones that carried the prose",
      set(rep.get('redacted_source_strings') or []) >= {
          'kicad_routing_tools.floor_provenance._note',
          'kicad_routing_tools.floor_provenance.source'},
      str(rep.get('redacted_source_strings')))

# --------------------------------------------------------------------------
# The floor is numeric, and it must survive untouched (#441).
# --------------------------------------------------------------------------
with open(PROJECT, encoding='utf-8') as f:
    src_doc = json.load(f)
src_rules = src_doc['board']['design_settings']['rules']
out_rules = doc['board']['design_settings']['rules']
check("board.design_settings.rules survive the sweep byte for byte",
      out_rules == src_rules, f"{out_rules} vs {src_rules}")

src_cls = {c['name']: c for c in src_doc['net_settings']['classes']}
out_cls = {c['name']: c for c in doc['net_settings']['classes']}
check("every netclass clearance/track/via value survives",
      all(out_cls.get(n, {}).get(k) == c.get(k)
          for n, c in src_cls.items()
          for k in ('clearance', 'track_width', 'via_diameter', 'via_drill')),
      f"Default now {out_cls.get('Default', {}).get('clearance')}, "
      f"was {src_cls.get('Default', {}).get('clearance')}")

# The stem appears in no VALUE, but a case-shifted spelling must not sneak
# through either -- corpus stems and KiCad filenames disagree on case.
def _strings(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)
    elif isinstance(node, str):
        yield node


check("no remaining string names the source in any case",
      not [s for s in _strings(doc) if 'tigard' in s.lower()],
      str([s[:60] for s in _strings(doc) if 'tigard' in s.lower()])[:200])

# --------------------------------------------------------------------------
# A synthetic carrier nobody has met yet: the point of a content sweep is
# that it does not need to have been enumerated.
# --------------------------------------------------------------------------
d = tempfile.mkdtemp()
board = os.path.join(d, 'board.kicad_pcb')
shutil.copyfile(BOARD, board)
with open(os.path.join(d, 'board.kicad_pro'), 'w', encoding='utf-8') as f:
    json.dump({'meta': {'filename': 'board.kicad_pro', 'version': 1},
               'some_future_tool': {'nested': [{'why': 'derived from '
                                                       'TIGARD.kicad_pcb'}]},
               'board': {'design_settings': {'rules': {'min_clearance': 0.15}}}},
              f)
rep2 = SU.sanitize_staged_project(board, 'tigard')
with open(os.path.join(d, 'board.kicad_pro'), encoding='utf-8') as f:
    doc2 = json.load(f)
check("a key the list never heard of is swept too",
      doc2['some_future_tool']['nested'][0]['why'] == SU._REDACTED,
      repr(doc2['some_future_tool']['nested'][0]['why']))
check("...and reported under its real path",
      'some_future_tool.nested.0.why' in (rep2.get('redacted_source_strings') or []),
      str(rep2.get('redacted_source_strings')))
check("the floor in that project is still 0.15",
      doc2['board']['design_settings']['rules']['min_clearance'] == 0.15,
      str(doc2['board']['design_settings']['rules']))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
