#!/usr/bin/env python3
"""The board brief assembles; it does not compute.

That is the whole claim, and it is the one worth testing: a brief that
re-derived any number would become a SECOND source of truth for it, and the
first time the two disagreed nobody would know which one the graders use. So
each section here is compared against the emitter that owns it, called
directly, and required to be equal -- not merely plausible.

The other half is honesty about absence. A section that cannot run has to
appear in `skipped` WITH A REASON and be absent from the body; a brief that
silently omitted a measurement would read as "nothing to report", which is the
failure `check_channels` names when it exits 3 rather than answering "clean"
for a gate that examined nothing.
"""
import json
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

BOARD = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not os.path.isfile(BOARD):
    print("SKIP: fixture missing")
    sys.exit(0)

from kicad_parser import parse_kicad_pcb
from board_brief import build_brief, format_text

pcb = parse_kicad_pcb(BOARD)
brief = build_brief(pcb, BOARD, requirements="USB on the north edge",
                    fit=[(15.5, 15.5), (400.0, 400.0)])

# --------------------------------------------------------------------------
# shape
# --------------------------------------------------------------------------
check("the brief carries every section",
      {'board', 'state', 'parts', 'structure', 'measurements', 'fit',
       'sources', 'skipped'} <= set(brief), str(sorted(brief)))
check("nothing was skipped on a healthy board", not brief['skipped'],
      str(brief['skipped']))
check("every section names the function that produced it",
      all(k in brief['sources'] for k in
          ('board', 'state', 'parts', 'structure', 'measurements', 'fit')),
      str(sorted(brief['sources'])))
check("the brief is JSON-serialisable",
      isinstance(json.dumps(brief, default=str), str))
check("format_text produces something to read",
      len(format_text(brief).splitlines()) > 4)

# --------------------------------------------------------------------------
# ASSEMBLES, DOES NOT COMPUTE: each number equals its emitter's
# --------------------------------------------------------------------------
check("board.footprints == the parsed count",
      brief['board']['footprints'] == len(pcb.footprints),
      f"{brief['board']['footprints']} vs {len(pcb.footprints)}")
check("board.bounds == board_info.board_bounds",
      brief['board']['bounds'] == list(pcb.board_info.board_bounds))

from placement.placement_state import assess_placement
st = assess_placement(pcb, BOARD)
check("state.unplaced == assess_placement's",
      brief['state']['unplaced'] == st.unplaced)
check("state.stacked_suspect_refs == assess_placement's",
      brief['state']['stacked_suspect_refs'] == list(st.stacked_suspect_refs))

from placement.groups import derive_groups
for src in ('decap', 'sheet'):
    want = derive_groups(pcb, (src,))
    got = (brief['structure']['groups'] or {}).get(src)
    if want:
        check(f"structure.groups[{src}] == derive_groups'",
              got == {k: sorted(v) for k, v in sorted(want.items())},
              f"{len(got or {})} vs {len(want)}")
    else:
        check(f"structure.groups has no empty {src} bucket", got is None,
              f"emitter returned nothing but the brief carries {got!r}")

from placement.escape import escape_ledger
led = escape_ledger(pcb, pcb_file=BOARD, clearance=brief['clearance'])
esc = brief['measurements'].get('escape') or {}
check("measurements.escape.parts == escape_ledger's length",
      esc.get('parts') == len(led), f"{esc.get('parts')} vs {len(led)}")
# `PartEscape` has no `worst_deficit` ATTRIBUTE -- only a to_dict() key -- so
# a getattr with a 0 default silently reports every board as deficit-free.
# Compare against the emitter's own dict, which is where the name is real.
want_parts = sum(1 for p in led if p.to_dict()['worst_deficit'] > 0)
check("measurements.escape.deficit_parts == the emitter's own worst_deficit",
      esc.get('deficit_parts') == want_parts,
      f"{esc.get('deficit_parts')} vs {want_parts}")

from placement.lock_advisor import advise_locks, to_json as lock_json
adv = lock_json(advise_locks(pcb, pcb_file=BOARD,
                             conflict_clearance=brief['clearance']))
check("measurements.locks.unlocked_high == the advisor's own tally",
      (brief['measurements']['locks']['tally'].get('unlocked_high')
       == adv.get('unlocked_high')),
      f"{brief['measurements']['locks']['tally'].get('unlocked_high')} vs "
      f"{adv.get('unlocked_high')}")
check("measurements.locks.lock_argv is the advisor's paste-ready form",
      brief['measurements']['locks']['lock_argv'] == adv.get('lock_argv'))

# --------------------------------------------------------------------------
# the parts table
# --------------------------------------------------------------------------
parts = brief['parts']
check("every footprint appears in the parts table",
      set(parts) == set(pcb.footprints), str(len(parts)))
check("a part's extent says whether it came from a courtyard or a pad bbox",
      all(p['extent_source'] in ('courtyard', 'pad_bbox', 'none')
          for p in parts.values()),
      str({p['extent_source'] for p in parts.values()}))
check("at least one part fell back to its pad bbox, and says so",
      any(p['extent_source'] == 'pad_bbox' for p in parts.values()),
      "this board's H6/H7 have no courtyard, so the distinction must show")

# --------------------------------------------------------------------------
# fit: opt-in, and honest when the answer is nowhere
# --------------------------------------------------------------------------
fits = {tuple(r['extent_mm']): r for r in brief['fit']}
check("a part that fits reports where", fits[(15.5, 15.5)]['fits']
      and fits[(15.5, 15.5)]['legal_cells'] > 0, str(fits[(15.5, 15.5)]))
check("a part larger than the board reports NOWHERE, not an empty success",
      fits[(400.0, 400.0)]['fits'] is False
      and fits[(400.0, 400.0)]['legal_cells'] == 0,
      str(fits[(400.0, 400.0)]))
check("fit names itself as computed rather than assembled",
      'COMPUTED' in brief['sources']['fit'], brief['sources']['fit'])
check("fit is absent unless asked for",
      'fit' not in build_brief(pcb, BOARD))

# --------------------------------------------------------------------------
# requirements are carried VERBATIM -- they are the constraints that live
# nowhere in the board file, and paraphrasing them would be this tool
# inventing mechanical geometry
# --------------------------------------------------------------------------
check("requirements are carried verbatim",
      brief['requirements'] == "USB on the north edge", brief['requirements'])
check("no requirements key when none were given",
      'requirements' not in build_brief(pcb, BOARD))

# --------------------------------------------------------------------------
# absence is disclosed, not silent
# --------------------------------------------------------------------------
import board_brief as bb
real = bb.escape_ledger if hasattr(bb, 'escape_ledger') else None


def _boom(*a, **kw):
    raise RuntimeError("deliberate")


import placement.escape as esc_mod
_saved = esc_mod.escape_ledger
esc_mod.escape_ledger = _boom
try:
    broken = build_brief(pcb, BOARD)
finally:
    esc_mod.escape_ledger = _saved
check("a section that raises is reported in `skipped` with its reason",
      any('escape' in k for k in broken['skipped'])
      and 'deliberate' in ' '.join(broken['skipped'].values()),
      str(broken['skipped']))
check("and is absent from the body rather than present-and-empty",
      'escape' not in (broken['measurements'] or {}),
      str(sorted(broken['measurements'] or {})))

# The advisor's tally is a TALLY: counts, not the whole findings list. A
# `startswith('findings')` filter also matches `findings` itself, which
# silently embedded every per-part reason and evidence blob under it.
tally = brief['measurements']['locks']['tally']
check("locks.tally carries counts only",
      all(isinstance(v, int) for v in tally.values()),
      str({k: type(v).__name__ for k, v in tally.items()}))
check("locks.tally does not embed the findings list",
      'findings' not in tally, str(sorted(tally)))

# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as wd:
    out = os.path.join(wd, 'brief.json')
    r = subprocess.run(
        [sys.executable, '-X', 'utf8', os.path.join('py_tools',
                                                    'board_brief.py'),
         BOARD, '--json', out, '--fit', '15.5x15.5'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=REPO, timeout=900,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    check("the CLI exits 0 on a healthy board", r.returncode == 0,
          r.stderr[-400:])
    check("the CLI writes the JSON it says it wrote", os.path.isfile(out))
    check("the CLI prints a JSON_SUMMARY",
          any(l.startswith('JSON_SUMMARY:') for l in r.stdout.splitlines()))
    # The floors path takes no --clearance here, which is the call shape that
    # crashed while board_floor_knobs' TRIPLE return was read as a mapping.
    check("the CLI resolves floors without an explicit --clearance",
          'Traceback' not in r.stderr, r.stderr[-400:])

# --------------------------------------------------------------------------
# extent_mm is BOARD-FRAME and includes the pads' own size
#
# Two defects that shipped together, both silent:
#   * the pad fallback measured max(global_x) - min(global_x), i.e. pad
#     CENTRES, so a two-pad part had ZERO width along its pad axis;
#   * both geometry sources return the footprint-LOCAL frame and nothing
#     rotated them, so every 90/270 part was transposed.
# The brief's own `fit` section IS board-frame, so `extent_mm` could not be
# fed to --fit WxH for half a board -- and the understated area fed
# grow_board's utilisation.
# --------------------------------------------------------------------------
from placement.legality import rotate_local_bounds
from placement.parser import extract_courtyard_bboxes
from placement.utility import compute_footprint_bbox_local

for _bd in (BOARD, os.path.join(REPO, 'kicad_files', 'esp_prog.kicad_pcb')):
    if not os.path.isfile(_bd):
        continue
    _pcb = parse_kicad_pcb(_bd)
    _brief = build_brief(_pcb, _bd)
    _cy = extract_courtyard_bboxes(_bd) or {}
    bad, rotated, twopad = [], 0, 0
    for _ref, _row in _brief['parts'].items():
        _fp = _pcb.footprints.get(_ref)
        if _fp is None or _row['extent_source'] == 'none':
            continue
        _box = _cy.get(_ref) or compute_footprint_bbox_local(_fp)
        _g = rotate_local_bounds(*_box, _fp.rotation or 0.0)
        want = [round(_g[2] - _g[0], 3), round(_g[3] - _g[1], 3)]
        if want != _row['extent_mm']:
            bad.append((_ref, _row['extent_mm'], want))
        if (_fp.rotation or 0.0) % 180 not in (0.0,):
            rotated += 1
        if len(_fp.pads or ()) == 2 and _row['extent_source'] == 'pad_bbox':
            twopad += 1
            if min(_row['extent_mm']) <= 0.0:
                bad.append((_ref, _row['extent_mm'], 'zero-width two-pad part'))
    name = os.path.basename(_bd)
    check(f"{name}: every extent matches the canonical board-frame bbox",
          not bad, f"{len(bad)} mismatch(es): {bad[:3]}")
    check(f"{name}: the fixture has rotated parts, so the frame check bites",
          rotated > 0, f"{rotated} part(s) at a non-0/180 rotation")

_ep = os.path.join(REPO, 'kicad_files', 'esp_prog.kicad_pcb')
if os.path.isfile(_ep):
    _b = build_brief(parse_kicad_pcb(_ep), _ep)
    c1 = _b['parts'].get('C1', {}).get('extent_mm')
    check("esp_prog C1 (an 0603) has real width on both axes",
          c1 and min(c1) > 0.5, f"{c1} -- it used to read [0.0, 1.778]")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
