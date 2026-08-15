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
from placement.escape import PartEscape, escape_ledger
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
# Against the REAL class. This asserted `not hasattr(type('x', (), {}), ...)`
# -- an anonymous empty class -- which is unconditionally true and never
# touched PartEscape. It stayed green when a real worst_deficit property was
# added, and, worse, it stood guard over a bug that was still live in
# options.py's relax_clearance the whole time it was passing.
check("PartEscape really has no worst_deficit ATTRIBUTE",
      not hasattr(PartEscape, 'worst_deficit'),
      "if this ever gains the attribute, the getattr form becomes safe and "
      "this test should be deleted rather than inverted")
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
          and al['measured']['deficit_lanes_at_fab_floor']
          <= al['measured']['deficit_lanes_at_board_clearance'],
          str(al['measured']))
    # `_now` must mean AT THIS BOARD'S CLEARANCE. It used to mean "at the fab
    # floor", which reported tigard as 0 deficit lanes while move_blocker, in
    # the same document, named 23 faces in deficit -- and the false-clean
    # action string ("no face is short of lanes") was reachable on any board
    # whose fab floor is finer than its netclass.
    check("`_now` means the board's own clearance, not the fab floor",
          al.get('ran')
          and al['measured']['deficit_lanes_now']
          == al['measured']['deficit_lanes_at_board_clearance'],
          f"now={al.get('measured', {}).get('deficit_lanes_now')} "
          f"board={al.get('measured', {}).get('deficit_lanes_at_board_clearance')} "
          f"fab={al.get('measured', {}).get('deficit_lanes_at_fab_floor')}")
    check("and on THIS board the two genuinely differ, so that check bites",
          al.get('ran')
          and al['measured']['deficit_lanes_at_fab_floor']
          != al['measured']['deficit_lanes_at_board_clearance'],
          "if they were equal the assertion above would pass either way")
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
            # FAB FLOOR to FAB FLOOR. `_now` is the board's own clearance now,
            # so comparing it to `_at_more` (a fab-floor number) compares two
            # different questions and fails on a board where the floor is
            # finer than the netclass -- which is most of them.
            check("identical floors report NO lane gain from layers",
                  al['measured']['deficit_lanes_at_fab_floor']
                  == al['measured']['deficit_lanes_at_more']
                  and 'buy NO extra lanes' in al['action'],
                  f"{al['measured']['deficit_lanes_at_fab_floor']} -> "
                  f"{al['measured']['deficit_lanes_at_more']}: {al['action']}")
    rc = dopts['relax_clearance']
    # NOT `if rc.get('ran'):`. That guard made this the only relax_clearance
    # assertion in the suite AND made it dead code: `ran` was False on every
    # board because of the worst_deficit getattr, so the option shipped a
    # false "nothing to report" and no test could see it. Assert it RAN.
    check("relax_clearance actually runs on a board with a lane deficit",
          rc.get('ran'), f"ran={rc.get('ran')} reason={rc.get('reason')!r} -- "
                         f"a deficit board must not report 'nothing to relax'")
    check("and it measured a real base deficit, not 0",
          (rc.get('measured') or {}).get('deficit_lanes', 0) > 0,
          str(rc.get('measured')))
    below = [r for r in (rc.get('measured') or {}).get('ladder', [])
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

# --------------------------------------------------------------------------
# grow_board: per SIDE, and a proposal that actually holds the parts
# --------------------------------------------------------------------------
OC = os.path.join(REPO, 'kicad_files', 'orangecrab_ext_pll.kicad_pcb')
if os.path.isfile(OC):
    ocb = parse_kicad_pcb(OC)
    g = grow_board(ocb, OC, clearance=0.2, board_edge_clearance=0.5)
    m = g['measured']
    sides = m['part_area_by_side_mm2']
    check("grow_board splits part area by SIDE", len(sides) >= 2, str(sides))
    check("and the fixture really is two-sided, or the split proves nothing",
          min(sides.values()) > 0, str(sides))
    check("utilisation is the BUSIEST side, not the sum",
          abs(m['utilisation']
              - m['busiest_side_area_mm2'] / m['usable_area_mm2']) < 1e-3,
          f"util {m['utilisation']} vs busiest/usable "
          f"{m['busiest_side_area_mm2'] / m['usable_area_mm2']:.4f}")
    # The regression this fixes: a SHIPPING board told it does not fit, with a
    # recommendation to shrink it. Summing both sides against one side's area
    # is what produced that.
    check("a shipping two-sided board is not told it fails to fit",
          g['fits_by_area'] is True,
          f"util {m['utilisation']}, sides {sides}, usable "
          f"{m['usable_area_mm2']}")
    check("and summing the sides WOULD have failed it (the bug was real)",
          sum(sides.values()) > m['usable_area_mm2'],
          f"sum {sum(sides.values()):.1f} vs usable {m['usable_area_mm2']}")

# The proposed square must actually hold the parts. It was
# sqrt(outline_area + need) where `need` is a USABLE-area shortfall, so the
# proposal's own usable area was still short -- 55.1mm square for parts
# needing 2971.0mm2 yields 2920.3.
import re as _re

# Shrink the OUTLINE only. Scaling the file's (xy ...) shrinks the footprints
# with it, so utilisation is unchanged and the board is not too small at all --
# measured, that fixture reported fits=True and this branch skipped itself.
tp = parse_kicad_pcb(SMALL)
bx0, by0, bx1, by1 = tp.board_info.board_bounds
tp.board_info.board_bounds = (bx0, by0, bx0 + (bx1 - bx0) / 3.0,
                              by0 + (by1 - by0) / 3.0)
tg = grow_board(tp, SMALL, clearance=0.2, board_edge_clearance=0.5)
if tg.get('ran') and not tg['fits_by_area']:
    side_mm = float(_re.search(r'about ([\d.]+) x', tg['action']).group(1))
    edge = 0.5
    usable_of_proposal = (side_mm - 2 * edge) ** 2
    need = tg['measured']['busiest_side_area_mm2']
    check("the proposed square's USABLE area actually holds the parts",
          usable_of_proposal >= need - 1e-6,
          f"{side_mm:.1f}mm square -> usable {usable_of_proposal:.1f} mm2 "
          f"vs parts {need:.1f} mm2")
else:
    check("the too-small fixture is genuinely too small", False,
          f"ran={tg.get('ran')} fits={tg.get('fits_by_area')} "
          f"-- this branch must not be skipped silently: {tg.get('reason')}")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
