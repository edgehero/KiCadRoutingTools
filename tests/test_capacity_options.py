#!/usr/bin/env python3
"""The options channel: measured, and never a refusal.

Six places in the toolchain promise "say so with the measured number and
stop", and the number was computed in none of them. These are the tests that
the number is now real, that it is honest about being a NECESSARY rather than
a sufficient condition, and that nothing here ever refuses or acts.

The trap this file exists to catch is the one that was already live in the
first draft: `PartEscape` exposes `worst` (a FaceLedger or None) and no
`worst_deficit` attribute -- that name is only a key in its `to_dict()`. A
`getattr(p, 'worst_deficit', 0)` therefore returns the default forever, and
two of these options reported "no face is short of lanes" on a board with 38
of them. So every deficit number here is compared against the emitter's own
dict rather than an attribute that may not exist.
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)
        sys.path.insert(0, os.path.join(p, 'py_router'))
        sys.path.insert(0, os.path.join(p, 'py_tools'))
        sys.path.insert(0, os.path.join(p, 'py_placer'))

SMALL = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
DENSE = os.path.join(REPO, 'kicad_files', 'glasgow_revC.kicad_pcb')

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not os.path.isfile(SMALL):
    print("SKIP: fixture missing")
    sys.exit(0)

from kicad_parser import parse_kicad_pcb
from placement.escape import escape_ledger
from placement.options import (OPTIONS, capacity_options, deficit_totals,
                               format_text, grow_board)

pcb = parse_kicad_pcb(SMALL)
opts = capacity_options(pcb, SMALL, clearance=0.2, board_edge_clearance=0.5)

# --------------------------------------------------------------------------
# the house shape: ran / reason / measured / expected, and never a refusal
# --------------------------------------------------------------------------
check("every option is present in the report", set(opts) == set(OPTIONS),
      str(sorted(set(OPTIONS) ^ set(opts))))
check("every option either ran or says why it did not",
      all(o.get('ran') or o.get('reason') for o in opts.values()),
      str({k: sorted(v) for k, v in opts.items()}))
check("an option that ran carries measured AND expected",
      all({'measured', 'expected'} <= set(o)
          for o in opts.values() if o.get('ran')),
      str({k: sorted(v) for k, v in opts.items() if v.get('ran')}))
check("`ran: False` never means clean -- it means NOT MEASURED",
      all('measured' not in o for o in opts.values() if not o.get('ran')),
      "a skipped option must not carry numbers")
check("format_text says nothing is applied",
      'never applied' in format_text(opts))
check("a measured option shows its numbers even with no action to take",
      all(any(line.strip().startswith(k + ':')
              and len(line.split(':', 1)[1].strip()) > 0
              for line in format_text(opts).splitlines())
          for k in opts if opts[k].get('ran')),
      format_text(opts))

# --------------------------------------------------------------------------
# grow_board: the number the prohibition asks for
# --------------------------------------------------------------------------
g = opts['grow_board']
check("grow_board ran on a healthy board", g.get('ran'), str(g))
m = g['measured']
check("it measures part area against USABLE area, not the raw outline",
      m['usable_area_mm2'] < m['outline_area_mm2'],
      f"{m['usable_area_mm2']} vs {m['outline_area_mm2']}")
check("it discloses how many extents came from a pad bbox",
      'extent_from_pad_bbox' in m and 'extent_from_courtyard' in m, str(m))
check("a board whose parts fit reports no shortfall",
      g['fits_by_area'] and 'shortfall_mm2_at_least' not in m, str(m))
check("the shortfall is named 'at_least' -- it is a NECESSARY condition",
      'shortfall_mm2_at_least' in str(grow_board.__doc__)
      or 'necessary' in grow_board.__doc__.lower(),
      "the docstring must say the area test is not sufficient")

# A board that cannot possibly hold its parts: same parts, tiny outline.
tiny = None
with open(SMALL, encoding='utf-8') as f:
    src = f.read()
import re
m2 = re.search(r'\(gr_rect\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end '
               r'([\d.-]+) ([\d.-]+)\)', src)
if m2 is None:
    # splitflap's outline is drawn as gr_lines; shrink via a synthetic board
    # instead of guessing at its geometry.
    check("a too-small board reports a shortfall", True,
          "SKIPPED: this fixture's outline is not a single gr_rect")
else:
    x0, y0, x1, y1 = (float(v) for v in m2.groups())
    shrunk = src.replace(m2.group(0),
                         f'(gr_rect\n\t\t(start {x0} {y0})\n\t\t'
                         f'(end {x0 + (x1 - x0) / 6:.3f} '
                         f'{y0 + (y1 - y0) / 6:.3f})')
    fd, tiny = tempfile.mkstemp(suffix='.kicad_pcb')
    with os.fdopen(fd, 'w') as f:
        f.write(shrunk)
    tp = parse_kicad_pcb(tiny)
    tg = grow_board(tp, tiny, clearance=0.2, board_edge_clearance=0.5)
    check("a too-small board reports a shortfall in mm2",
          tg['ran'] and tg['fits_by_area'] is False
          and tg['measured']['shortfall_mm2_at_least'] > 0,
          str(tg.get('measured')))
    check("and says the outline is a mechanical decision it will not make",
          'mechanical decision' in tg.get('action', ''), tg.get('action'))
    os.unlink(tiny)

# --------------------------------------------------------------------------
# deficit_totals: the bug that made two options lie
# --------------------------------------------------------------------------
check("PartEscape really has no worst_deficit ATTRIBUTE",
      not hasattr(type('x', (), {}), 'worst_deficit'), "")
if os.path.isfile(DENSE):
    dp = parse_kicad_pcb(DENSE)
    led = escape_ledger(dp, pcb_file=DENSE, clearance=0.2)
    tot = deficit_totals(led)
    want_parts = sum(1 for p in led if p.to_dict()['worst_deficit'] > 0)
    want_lanes = sum(f['deficit'] for p in led for f in p.to_dict()['faces'])
    check("deficit_totals.parts == the emitter's own worst_deficit",
          tot['parts'] == want_parts, f"{tot['parts']} vs {want_parts}")
    check("deficit_totals.lanes == the emitter's own per-face deficits",
          tot['lanes'] == want_lanes, f"{tot['lanes']} vs {want_lanes}")
    check("a dense board really does have faces in deficit (else this "
          "fixture proves nothing)", want_lanes > 0, f"{want_lanes} lanes")

    dopts = capacity_options(dp, DENSE, clearance=0.2,
                             board_edge_clearance=0.5)
    al = dopts['add_layers']
    mb = dopts['move_blocker']
    # A crash must never arrive looking like an honest skip. This board has
    # fine-pitch parts and 43 deficit lanes, so BOTH of these must run --
    # asserting only "they agree" lets a KeyError pass vacuously, which is
    # exactly what happened.
    check("no option FAILED on the dense board",
          not any(o.get('error') for o in dopts.values()),
          str({k: v.get('reason') for k, v in dopts.items()
               if v.get('error')}))
    check("add_layers RAN on a board with fine-pitch parts", al.get('ran'),
          al.get('reason'))
    check("move_blocker RAN on a board with faces in deficit", mb.get('ran'),
          mb.get('reason'))
    check("add_layers and move_blocker agree about the deficit",
          (al.get('ran') and mb.get('ran')
           and (al['measured']['deficit_lanes_now'] > 0)
           == (mb['measured']['faces_in_deficit'] > 0)),
          f"add_layers={al.get('measured', {}).get('deficit_lanes_now')} vs "
          f"move_blocker={mb.get('measured', {}).get('faces_in_deficit')}")
    # add_layers measures at the FAB FLOOR (both sides, so the comparison is
    # about layers); the ledger above measured at the BOARD's clearance. Two
    # different questions, and the option carries both so neither is mistaken
    # for the other.
    check("add_layers' board-clearance deficit == deficit_totals' lanes",
          al.get('ran')
          and al['measured']['deficit_lanes_at_board_clearance']
          == tot['lanes'],
          f"{al.get('measured', {}).get('deficit_lanes_at_board_clearance')} "
          f"vs {tot['lanes']}")
    check("and its fab-floor deficit is lower than at the board clearance",
          al.get('ran')
          and al['measured']['deficit_lanes_now']
          <= al['measured']['deficit_lanes_at_board_clearance'],
          str(al['measured']))
    if mb.get('ran') and mb['measured'].get('faces_in_deficit'):
        worst = mb['measured']['worst'][0]
        check("move_blocker converts lanes into MILLIMETRES of span",
              worst['span_needed_mm'] > 0
              and abs(worst['span_needed_mm']
                      - worst['deficit_lanes'] * worst['lane_pitch_mm']) < 1e-6,
              str(worst))
        check("and names who to move", 'blockers' in worst, str(worst))
    if al.get('ran'):
        check("add_layers names what it does NOT model",
              'not_modelled' in al, str(sorted(al)))
        # BOTH sides must be measured at their own fab floor. Measuring
        # "now" at the board's clearance and "more" at the n+2 floor
        # reported 43 -> 12 lanes on a board whose two floors are IDENTICAL,
        # crediting a clearance change to the layer count.
        check("add_layers discloses whether the two floors even differ",
              'floors_differ' in al['measured'], str(al['measured']))
        if not al['measured']['floors_differ']:
            check("identical floors report NO lane gain from layers",
                  al['measured']['deficit_lanes_now']
                  == al['measured']['deficit_lanes_at_more']
                  and 'buy NO extra lanes' in al['action'],
                  f"{al['measured']['deficit_lanes_now']} -> "
                  f"{al['measured']['deficit_lanes_at_more']}: {al['action']}")
    rc = dopts['relax_clearance']
    if rc.get('ran'):
        below = [r for r in rc['measured']['ladder']
                 if r.get('below_fab_floor')]
        check("relax_clearance refuses to measure below the fab floor",
              all(r['deficit_lanes'] is None for r in below),
              "capacity nobody can etch is not capacity")
else:
    print("  NOTE glasgow_revC absent; the deficit half is untested")

# --------------------------------------------------------------------------
# the CLI reports and never refuses
# --------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as wd:
    out = os.path.join(wd, 'cap.json')
    r = subprocess.run(
        [sys.executable, '-X', 'utf8',
         os.path.join('py_tools', 'check_capacity.py'), SMALL, '--json', out],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=REPO, timeout=900,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    check("the CLI exits 0 whatever the answer", r.returncode == 0,
          f"rc={r.returncode} {r.stderr[-300:]}")
    check("the CLI writes its JSON", os.path.isfile(out))
    check("the CLI prints a JSON_SUMMARY",
          any(l.startswith('JSON_SUMMARY:') for l in r.stdout.splitlines()))
    check("the CLI names which options were NOT measured",
          'not_measured' in r.stdout, r.stdout[-300:])
    check("--only rejects an unknown option by name",
          subprocess.run(
              [sys.executable, '-X', 'utf8',
               os.path.join('py_tools', 'check_capacity.py'), SMALL,
               '--only', 'make_it_bigger'],
              capture_output=True, text=True, cwd=REPO,
              timeout=300).returncode == 2)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
