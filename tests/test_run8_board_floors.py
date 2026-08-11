#!/usr/bin/env python3
"""A tool's default must not contradict the board's own declared floor.

route_planes' --min-thickness defaulted to a fixed 0.1mm while this repo's own
connection-width grader reads the board's min_track_width. On a board whose
author declared a wider floor, the pour emitted ribbons the grader then called
too thin: a violation the pour created against a rule it never read.

Unset now resolves from the board (measured: a board declaring 0.2mm resolves
to 0.2), and falls back to the packaged default only when the board declares
nothing -- which is the case for every board in this repo, since project
siblings are not committed.

Run: python3 -X utf8 tests/test_run8_board_floors.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault('KRT_NO_BANNER', '1')

import routing_defaults as defaults                            # noqa: E402
import route_planes                                            # noqa: E402

FAILURES = []


def check(name, cond, detail=''):
    print(f'  {"PASS" if cond else "FAIL"}  {name}'
          + (f'\n        {detail}' if not cond and detail else ''))
    if not cond:
        FAILURES.append(name)


class A:
    def __init__(self, board, mt=None):
        self.input_file, self.min_thickness = board, mt


# --- D9: three more instruments that substituted a constant for the board ----
#
# check_channels and check_assembly defaulted --clearance to routing_defaults
# 0.25 and never read the board; render_placement documented no default at all.
# Measured on a board whose floor is 0.2 with a 0.254 track: check_channels at
# its old constants reported 334 escape lanes where the board's own floor gives
# 399 -- a 65-lane understatement, and an invented deficit on a face that had
# none. A phantom deficit steers a placement search at the thing that is not
# wrong.

def _fixture(tmp, clearance=0.1, track=0.15, extra_rules=None):
    """A board that DECLARES a floor. Every board in kicad_files/ declares
    none (project siblings are not committed), so board-first resolution is
    untestable without building one."""
    import shutil
    src = os.path.join(ROOT, 'kicad_files', 'splitflap_driver.kicad_pcb')
    dst = os.path.join(tmp, 'declared.kicad_pcb')
    shutil.copyfile(src, dst)
    import json as _json
    rules = {'min_clearance': 0.0}        # the trap: KiCad writes 0 for "unset"
    rules.update(extra_rules or {})
    with open(os.path.splitext(dst)[0] + '.kicad_pro', 'w',
              encoding='utf-8') as f:
        _json.dump({'net_settings': {'classes': [
            {'name': 'Default', 'clearance': clearance, 'track_width': track}]},
            'board': {'design_settings': {'rules': rules}}}, f)
    return dst


def _d9_shared_resolver():
    """One helper, so the three instruments cannot each be wrong differently."""
    import tempfile
    from list_nets import board_floor
    with tempfile.TemporaryDirectory() as tmp:
        b = _fixture(tmp)
        print('board_floor resolves board-first')
        check('an explicit value wins and is labelled cli',
              board_floor(b, 'clearance', 0.42, 0.25) == (0.42, 'cli'))
        check('unset reads the board netclass',
              board_floor(b, 'clearance', None, 0.25) == (0.1, 'board netclass'),
              str(board_floor(b, 'clearance', None, 0.25)))
        check('track width too',
              board_floor(b, 'track_width', None, 0.3) == (0.15, 'board netclass'))
        # THE min_clearance TRAP. The fixture declares min_clearance 0.0, which
        # KiCad writes for "not configured". Reading it as a real floor would
        # resolve a board asking for 0.1 down to 0.0 and relax every consumer
        # to nothing -- so `clearance` must never fall back to that constraint.
        check('min_clearance 0.0 does NOT override the netclass',
              board_floor(b, 'clearance', None, 0.25)[0] == 0.1)
        # A constraint-only floor, which no netclass expresses (D11's case).
        b2 = _fixture(tmp, extra_rules={'min_hole_clearance': 0.25})
        check('a hole floor comes from the board constraint',
              board_floor(b2, 'hole_clearance', None, 0.2)
              == (0.25, 'board constraint'),
              str(board_floor(b2, 'hole_clearance', None, 0.2)))

    print('a board declaring nothing still falls back, and says so')
    nodecl = os.path.join(ROOT, 'kicad_files', 'tigard.kicad_pcb')
    check('fallback is labelled fixed default',
          board_floor(nodecl, 'clearance', None, 0.25) == (0.25, 'fixed default'))
    check('"could not read the project" is not "declares nothing"',
          board_floor(os.path.join(tmp, 'nope.kicad_pcb'), 'clearance',
                      None, 0.25, design_rules=_Boom())[1] == 'unreadable project')

    # THE 0.0 TRAP, in the OLDER helper. board_floor guards it; board_floor_knobs
    # did not, and render_placement is wired to board_floor_knobs -- so a project
    # declaring `min_copper_edge_clearance: 0.0` (KiCad's "not configured") gave
    # the placement model a REAL edge floor of zero, collapsing every edge-halo
    # and oob term, where it had used 0.55 before. The two helpers must agree
    # about the one trap this module documents.
    print('a declared 0.0 is UNSET in both floor helpers, not a floor of zero')
    from list_nets import board_floor_knobs
    import tempfile as _tf
    with _tf.TemporaryDirectory() as z:
        b = _fixture(z, clearance=0.2,
                     extra_rules={'min_copper_edge_clearance': 0.0})
        _clr, _edge, knobs = board_floor_knobs(b)
        check('board_floor_knobs does not return a 0.0 edge floor',
              _edge == 0.55 and knobs['board_edge_clearance']['source']
              == 'fixed default', str(knobs['board_edge_clearance']))
        check('board_floor agrees',
              board_floor(b, 'board_edge_clearance', None, 0.55)
              == (0.55, 'fixed default'))


class _Boom(dict):
    """A design_rules stand-in that raises when read, to exercise the
    'I could not look' branch without corrupting a real project file."""
    def get(self, *a, **k):
        raise OSError('unreadable')


def _d9_instruments(_board):
    """The three CLIs must USE it, and SAY which value they used."""
    import json as _json
    import subprocess
    import tempfile

    def run(script, *args):
        return subprocess.run(
            [sys.executable, '-X', 'utf8', os.path.join(ROOT, script)]
            + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding='utf-8', errors='replace', cwd=ROOT)

    with tempfile.TemporaryDirectory() as tmp:
        b = _fixture(tmp)

        print('check_channels grades at the board, not at 0.25/0.3')
        jp = os.path.join(tmp, 'ch.json')
        r = run('check_channels.py', b, '--json', jp)
        d = _json.load(open(jp, encoding='utf-8'))
        check('clearance came from the board', d['clearance'] == 0.1, str(d['clearance']))
        check('track width came from the board', d['track_width'] == 0.15,
              str(d['track_width']))
        check('the JSON records the source',
              d['floors']['clearance']['source'] == 'board netclass', str(d.get('floors')))
        check('...and stdout names it', 'board netclass' in r.stdout,
              r.stdout[:300])
        r = run('check_channels.py', b, '--clearance', '0.3', '--json', jp)
        d = _json.load(open(jp, encoding='utf-8'))
        check('an explicit --clearance still wins',
              (d['clearance'], d['floors']['clearance']['source']) == (0.3, 'cli'),
              str(d['clearance']))

        print('check_assembly grades at the board too')
        jp = os.path.join(tmp, 'as.json')
        r = run('check_assembly.py', b, '--json', jp)
        d = _json.load(open(jp, encoding='utf-8'))
        check('clearance came from the board', d['clearance'] == 0.1, str(d['clearance']))
        check('the JSON records the source',
              d['clearance_source'] == 'board netclass', str(d.get('clearance_source')))
        check('...and stdout names it', 'board netclass' in r.stdout, r.stdout[:300])

        print('render_placement records the clearance it actually used')
        jp = os.path.join(tmp, 'rp.json')
        r = run('render_placement.py', b, '--json-out', jp, '-o',
                os.path.join(tmp, 'rp.png'), '--size', '300',
                '--supersample', '1')
        d = _json.load(open(jp, encoding='utf-8'))['instrument']
        # It used to record args.clearance -- i.e. None on exactly the runs
        # most likely to be graded at the wrong value.
        check('instrument.clearance is the EFFECTIVE value, not None',
              d['clearance'] == 0.1, str(d['clearance']))
        check('what was requested is kept separately',
              d['clearance_requested'] is None, str(d['clearance_requested']))
        check('the source rides along',
              d['floors']['clearance']['source'] == 'board netclass',
              str(d.get('floors')))
        check('the board edge floor is resolved the same way',
              'board_edge_clearance' in d['floors'], str(d.get('floors')))


def main():
    board = os.path.join(ROOT, 'kicad_files', 'splitflap_driver.kicad_pcb')

    print('an explicit value always wins')
    check('the caller\'s number is used verbatim',
          route_planes._resolve_min_thickness(A(board, 0.33)) == 0.33)

    print('unset asks the board')
    v = route_planes._resolve_min_thickness(A(board))
    check('a board declaring nothing falls back to the packaged default',
          v == defaults.PLANE_MIN_THICKNESS, str(v))

    print('...and uses the declared floor when there is one')
    from list_nets import board_constraint
    withpro = os.path.join(ROOT, 'wk', 'run7', 'glasgow_revC',
                           'perturbed.kicad_pcb')
    if os.path.isfile(withpro) and board_constraint(withpro, 'min_track_width'):
        declared = board_constraint(withpro, 'min_track_width')
        got = route_planes._resolve_min_thickness(A(withpro))
        check(f'the board\'s own {declared}mm is used', got == declared,
              f'got {got}')
        check('...which differs from the packaged default',
              declared != defaults.PLANE_MIN_THICKNESS)
    else:
        print('  SKIP  no board with a committed project sibling '
              '(measured value: a 0.2mm board resolves to 0.2)')

    print('the flag no longer advertises a fixed default')
    src = open(os.path.join(ROOT, 'route_planes.py'), encoding='utf-8').read()
    check('--min-thickness defaults to None, not a constant',
          '"--min-thickness", type=float, default=None' in src)
    check('the help says where the value comes from',
          "min_track_width" in src)

    _d9_shared_resolver()
    _d9_instruments(board)

    print()
    if FAILURES:
        print(f'FAIL: {len(FAILURES)} check(s): {", ".join(FAILURES)}')
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
