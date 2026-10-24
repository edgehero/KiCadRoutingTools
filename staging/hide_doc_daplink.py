#!/usr/bin/env python3
"""gpm redo of board 11: hide the two sentences of docs/floorplan-intent.md that quote daplink's source
edge bands, for the length of the run only (an uncommitted local edit in the campaign worktree).

    python3 wk/gpm/_staging/hide_doc_daplink.py apply      # before the daplink teammate starts
    python3 wk/gpm/_staging/hide_doc_daplink.py restore    # after it ends: git checkout of the file
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
P = os.path.join(ROOT, 'docs', 'floorplan-intent.md')
A = ("routed. On daplink, with nothing moved, J2/J3 read 7.0062 placed (margin\n"
     "0.55) and 6.6562 routed (margin 0.2), and P1 read 1.0500 and 0.7000; three\n"
     "band errors appeared after routing. An overhang")
A2 = "routed. [Example values hidden for the gpm campaign.] An overhang"
B = ("reads the margin too high: daplink's hand-written J2/J3 `{7.0, 7.4}` and P1\n"
     "`{1.05, 1.35}` added 0.55, and now read 6.4562 and 0.5000 placed and routed\n"
     "alike. The setback")
B2 = "reads the margin too high. [Example values hidden for the gpm campaign.] The setback"
if sys.argv[1] == 'apply':
    t = open(P, encoding='utf-8').read()
    assert A in t and B in t, 'paragraph not found as expected'
    open(P, 'w', encoding='utf-8').write(t.replace(A, A2).replace(B, B2))
    t = open(P, encoding='utf-8').read()
    print('hidden; daplink mentions left:', t.lower().count('daplink'))
elif sys.argv[1] == 'restore':
    subprocess.run(['git', '-C', ROOT, 'checkout', '--', 'docs/floorplan-intent.md'], check=True)
    print('restored; git status:', subprocess.run(['git', '-C', ROOT, 'status', '--short'], capture_output=True, text=True).stdout or 'clean')
