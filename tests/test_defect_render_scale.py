#!/usr/bin/env python3
"""The picture is cropped from the MEASUREMENT, not from the parts.

Run 20's board is 33.8 x 46.0 mm. At `--size 1600` that is ~35 px/mm, and the
defect it was trying to show was 41 um -- about 1.2 px. Every render was of the
right board at a scale where the finding could not exist as an image. No mandate
in the chain ever asked for a crop AT a routing failure; crops were reserved for
legality findings and stop-condition claims.

So the defect panel derives its own view: tighten until the SHORTFALL spans
`DEFECT_MIN_PX`. That is the difference between a picture of the neighbourhood
and a picture of the finding, and when even that is not enough the caption says
INVISIBLE AT THIS SCALE rather than shipping a lie.

    python3 tests/test_defect_render_scale.py
"""
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_tools'),
           os.path.join(REPO, 'py_placer')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SKIP_EXIT = 77
try:
    from PIL import ImageChops                                     # noqa: F401
except ImportError as exc:
    print(f'SKIP: needs Pillow ({exc})')
    sys.exit(SKIP_EXIT)

import render_placement as RP                                      # noqa: E402

passed = failed = 0


def check(label, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  OK   {label}')
    else:
        failed += 1
        print(f'  FAIL {label} -- {detail}')


_D = tempfile.mkdtemp()

# The run-20 measurement, verbatim from what check_reachability produces.
_DEFECT = {
    'kind': 'throat', 'verdict': 'CAGED', 'net': 'Net-(U4-XTAL_P)',
    'seed': {'x': 86.8575, 'y': 91.01, 'layer': 'F.Cu'},
    'at': {'x': 87.4825, 'y': 91.235, 'layer': 'F.Cu'},
    'refs': ['R7', 'U4'], 'pads': ['R7.2', 'U4.53'],
    'measure': {'space': 'track_width', 'have_mm': 0.11231, 'need_mm': 0.15,
                'short_mm': 0.03769, 'resolution_mm': 0.01,
                'gap_mm': 0.41231, 'gap_need_mm': 0.45,
                'derived_from': 'have_mm + 2 * instrument.floors.clearance.value'},
    'view': [82.8575, 87.01, 90.8575, 95.01],
    'span': {'a': {'x': 88.0067, 'y': 90.92, 'layer': 'F.Cu', 'kind': 'pad'},
             'b': {'x': 86.8575, 'y': 91.41, 'layer': 'F.Cu', 'kind': 'pad'}},
    'relief': [], 'instrument': {'source': 'check_reachability', 'floors': {}},
}


def _rec(path, sha=None, defect=None):
    doc = {'kind': 'defect-record', 'version': 1, 'count': 1,
           'defects': [defect or _DEFECT]}
    if sha:
        doc['board_sha'] = sha
    p = os.path.join(_D, path)
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh)
    return p


print('--- the crop is sized from the shortfall, not from the parts ---')

for size in (800, 1600, 3200):
    view, ppmm, spx = RP.defect_view(_DEFECT, size)
    side = view[2] - view[0]
    check(f'at --size {size} the shortfall spans >= {RP.DEFECT_MIN_PX} px',
          spx >= RP.DEFECT_MIN_PX - 0.5,
          f'{spx:.2f} px over a {side:.3f}mm crop -- at the board\'s own '
          f'extent this defect is about 1.2 px')
    check(f'...and the throat is centred in it (--size {size})',
          abs((view[0] + view[2]) / 2 - _DEFECT['at']['x']) < 1e-9
          and abs((view[1] + view[3]) / 2 - _DEFECT['at']['y']) < 1e-9,
          str(view))

view, ppmm, spx = RP.defect_view(_DEFECT, 1600)
check('the crop still frames both blocking pads',
      view[0] <= min(_DEFECT['span']['a']['x'], _DEFECT['span']['b']['x'])
      and view[2] >= max(_DEFECT['span']['a']['x'], _DEFECT['span']['b']['x']),
      f'{view} vs span x '
      f"{_DEFECT['span']['a']['x']}, {_DEFECT['span']['b']['x']} -- a crop so "
      f"tight the two pieces of copper leave frame answers 'how much' and "
      f"loses 'between what'")
check('and it is far tighter than the record\'s own search view',
      (view[2] - view[0]) < (_DEFECT['view'][2] - _DEFECT['view'][0]) / 2,
      f"{view[2] - view[0]:.3f}mm vs "
      f"{_DEFECT['view'][2] - _DEFECT['view'][0]:.3f}mm")

# A defect carrying no shortfall must not have a scale invented for it.
_nos = dict(_DEFECT, measure={'space': 'track_width'})
v2, _, _ = RP.defect_view(_nos, 1600)
check('a defect with no shortfall falls back to its own view, not a guess',
      v2 is not None and abs((v2[2] - v2[0])
                             - (_DEFECT['view'][2] - _DEFECT['view'][0])) < 1e-6,
      str(v2))
v3, _, _ = RP.defect_view({'kind': 'throat'}, 1600)
check('and a defect with neither gets no panel at all',
      v3 is None, str(v3))

print('--- a record is BOUND to its board ---')

_board = os.path.join(REPO, 'wk', 'run20', 'frozen.kicad_pcb')
if not os.path.isfile(_board):
    _board = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
_sha = RP._board_sha(_board)
check('the board hashes', bool(_sha), _board)

d, notes = RP.load_defect_records([_rec('good.json', sha=_sha)], board_sha=_sha)
check('a matching record loads', len(d) == 1 and not notes, str(notes))
check('and remembers which file it came from',
      d[0].get('_source', '').endswith('good.json'), str(d[0].get('_source')))

d, notes = RP.load_defect_records([_rec('other.json', sha='0' * 64)],
                                  board_sha=_sha)
check('a record from a DIFFERENT board is dropped',
      not d and notes, f'{len(d)} defects, notes={notes}')
check('...loudly, naming both hashes',
      notes and 'SKIPPED' in notes[0] and '000000000000' in notes[0],
      str(notes))

d, notes = RP.load_defect_records([_rec('nosha.json')], board_sha=_sha)
check('a record with NO sha is drawn, but the doubt is recorded',
      len(d) == 1 and notes and 'cannot be proven' in notes[0], str(notes))

d, notes = RP.load_defect_records([os.path.join(_D, 'nope.json')],
                                  board_sha=_sha)
check('an unreadable record is a note, not a crash', not d and notes, str(notes))

_wrong = os.path.join(_D, 'wrongkind.json')
with open(_wrong, 'w', encoding='utf-8') as fh:
    json.dump({'kind': 'board-score', 'blocking': 3}, fh)
d, notes = RP.load_defect_records([_wrong], board_sha=_sha)
check('another tool\'s JSON is refused BY KIND',
      not d and notes and 'board-score' in notes[0], str(notes))

print('--- and the panel actually draws it ---')

if os.path.isfile(_board):
    _out = os.path.join(_D, 'panels')
    _js = os.path.join(_D, 'r.json')
    p = subprocess.run(
        [sys.executable, '-X', 'utf8',
         os.path.join(REPO, 'py_tools', 'render_placement.py'), _board,
         '--defect-json', _rec('live.json', sha=_sha), '--size', '1600',
         '-o', _out + os.sep, '--json-out', _js],
        capture_output=True, text=True, timeout=900)
    ok = os.path.isfile(_js)
    check('the render runs and writes its JSON', ok,
          (p.stdout or '')[-300:] + (p.stderr or '')[-300:])
    if ok:
        doc = json.load(open(_js, encoding='utf-8'))
        check("doc['defects'] carries what it was asked to show",
              len(doc.get('defects') or []) == 1
              and doc['defects'][0]['pads'] == ['R7.2', 'U4.53'],
              str(doc.get('defects'))[:200])
        check("instrument.defect_json mirrors instrument.summary_json",
              isinstance(doc['instrument'].get('defect_json'), list)
              and doc['instrument']['defect_json'],
              str(doc['instrument'].get('defect_json'))
              + ' -- a gate asserts a defect render the same way '
                '_guard_route_render asserts a focus render')
        dp = (doc.get('defect_panels') or [])
        check('a defect panel was produced', len(dp) == 1, str(dp)[:200])
        if dp:
            check('and it reports the px figure it achieved, not a promise',
                  dp[0]['shortfall_px'] >= RP.DEFECT_MIN_PX - 0.5,
                  str(dp[0]))
            check('the caption carries the scale so a reader can audit it',
                  'px/mm ->' in dp[0]['label'], dp[0]['label'])
            check('and names the two pads forming the throat',
                  'R7.2' in dp[0]['label'] and 'U4.53' in dp[0]['label'],
                  dp[0]['label'])
        _pngs = [x['path'] for x in doc['panels'] if x.get('view')]
        check('the panel was written to disk', _pngs and
              all(os.path.isfile(x) for x in _pngs), str(_pngs))

    # ImageChops: prove `draw_defects` actually drew, rather than trusting a
    # code path that ran. Same panel, same view, defects on vs off.
    from kicad_parser import parse_kicad_pcb                        # noqa: E402
    m = RP.PlacementModel(parse_kicad_pcb(_board), _board)
    if m is not None:
        _v, _, _ = RP.defect_view(_DEFECT, 420)
        _o = dict(borders=False, labels=False, ratsnest=False, pads=True,
                  legality=False, legend=False)
        a = RP.render_panel(RP.PanelSpec(m, view=_v, opts=_o), size=420,
                            supersample=1)
        b = RP.render_panel(RP.PanelSpec(m, view=_v, opts=_o,
                                         defects=[_DEFECT]), size=420,
                            supersample=1)
        check('drawing the defect measurably changes the image',
              ImageChops.difference(a, b).getbbox() is not None,
              'a code path that runs is not a mark that appears')
else:
    check('a board fixture is available', False, _board)

print(f'\n{passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
