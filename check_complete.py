#!/usr/bin/env python3
"""Is this board DONE? The one command that answers it, and fails closed.

    python3 -X utf8 check_complete.py BOARD [--authored-from ORIGINAL] \
        [--intent J] [--impedance-nets G...] [--length-groups J] \
        [--net-min-widths J] [--min-track-width MM] [--min-via-diameter MM] \
        [--clearance MM] [--json PATH]

`board_score` is the authority on `blocking`, and it is honest about being
incomplete -- but read alone it says "done" too easily, three separate ways:

  * IT EXITS 0 WITH FOUR OF NINE COMPONENTS UNGRADED. floorplan, impedance,
    length and net_widths return `skipped(...)` when their flag is absent, and
    `ungraded` does not touch the exit code. A board nobody graded exits 0.
  * `undersized` IS SILENTLY PERMISSIVE without spec numbers. It runs at the
    FAB floor for the layer count, so `undersized == 0` is not "the sizes are
    right" -- one board had 141 of 141 vias violating a 0.6mm spec while
    clearing the 0.25mm two-layer floor.
  * IT HAS NO COMPONENT AT ALL for orphan stubs, weird copper, pad overlaps or
    channel starvation. Several of those are run by the routing chain and none
    of them reaches the scalar.

And underneath all of it, the DRC writeback rewrites the board's own
manufacturing floors down to whatever was produced and then everything grades
against the new value. That is disclosed in a printed line and enforced by
nothing.

So this aggregates, and the difference from board_score is the direction it
fails in. Three verdict classes, and only one of them is "done":

    DONE        every component that could be graded is graded and clean
    INCOMPLETE  a component RAN and could not answer, or an instrument this
                adds found something -- exit 4
    UNSOUND     the board grades clean against floors it rewrote -- exit 5

UNGRADED components do NOT block DONE -- a board with no spec files has nothing
to grade them against, and making that fatal would put every corpus board
permanently in the failing state -- but they are NAMED in the verdict line,
because a component nothing examined is UNEXAMINED and never clean.

Exit: 0 done, 2 usage, 3 board state, 4 incomplete, 5 unsound floors.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILL_SCRIPTS = os.path.join(ROOT, '.claude', 'skills', 'plan-pcb-routing',
                             'scripts')
PY = [sys.executable, '-X', 'utf8']

DONE, USAGE, BOARD_STATE, INCOMPLETE, UNSOUND = 0, 2, 3, 4, 5


def _run(args, timeout=3600):
    p = subprocess.run(PY + args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', cwd=ROOT,
                       timeout=timeout, env=dict(os.environ, KRT_NO_BANNER='1'))
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def copper_layers(board):
    from kicad_parser import parse_kicad_pcb
    return list(parse_kicad_pcb(board).board_info.copper_layers or [])


def fab_floor_integrity(board, authored_from):
    """Does this board's copper sit below the floors its project ONCE declared?

    The writeback only ever loosens: every constraint is set to min(current,
    target) and the target is the smallest object actually placed. So a board
    that routed at 0.0889 rewrites its own 0.2 minimum and then grades clean
    against it -- measured at 5629 of 5933 segments below the original floor,
    with check_drc, board_score and KiCad's own DRC all reading clean.

    Needs the ORIGINAL project to compare against, because a chain overwrites
    the floors in place. Without it, say the check did not run rather than
    implying it passed.
    """
    from fix_kicad_drc_settings import (FAB_FLOOR_KEYS, find_project,
                                        scan_board_minima)
    if not authored_from:
        return {'ran': False, 'reason': 'no --authored-from: the chain rewrites '
                                        'the floors in place, so there is '
                                        'nothing left to compare against'}
    pro = find_project(authored_from)
    if not os.path.isfile(pro):
        return {'ran': False, 'reason': f'no project beside {authored_from}'}
    try:
        with open(pro, encoding='utf-8') as fh:
            authored = ((json.load(fh).get('board') or {})
                        .get('design_settings') or {}).get('rules') or {}
    except Exception as exc:                                # noqa: BLE001
        return {'ran': False, 'reason': f'unreadable project: {exc}'}
    now = scan_board_minima(board) or {}
    relaxed = []
    for key, label in FAB_FLOOR_KEYS:
        was, is_ = authored.get(key), now.get(key)
        if isinstance(was, (int, float)) and isinstance(is_, (int, float)) \
                and is_ < was - 1e-9:
            relaxed.append({'key': key, 'label': label, 'authored': was,
                            'on_board': is_})
    return {'ran': True, 'relaxed': relaxed, 'authored_from': authored_from}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board')
    ap.add_argument('--authored-from', default=None,
                    help='the board the chain STARTED from -- its project '
                         'carries the floors this one should still respect')
    ap.add_argument('--clearance', type=float, default=None)
    ap.add_argument('--intent', default=None)
    ap.add_argument('--impedance-nets', nargs='+', default=None)
    ap.add_argument('--length-groups', default=None)
    ap.add_argument('--net-min-widths', default=None)
    ap.add_argument('--min-track-width', type=float, default=None)
    ap.add_argument('--min-via-diameter', type=float, default=None)
    ap.add_argument('--min-via-drill', type=float, default=None)
    ap.add_argument('--skip-slow', action='store_true',
                    help='the added instruments only; board_score always runs')
    ap.add_argument('--json', default=None, metavar='PATH')
    a = ap.parse_args(argv)

    if not os.path.isfile(a.board):
        print(f'no such board: {a.board}', file=sys.stderr)
        return BOARD_STATE

    doc = {'board': os.path.abspath(a.board), 'components': {}}

    # ---- 1. board_score, with every spec flag the caller has ---------------
    # The intermediate goes to a temp dir, not next to the board: a checker
    # that drops files into the directory it is inspecting turns a read-only
    # question into a write, and on a corpus directory that is somebody's
    # source tree.
    import tempfile
    scratch = tempfile.mkdtemp(prefix='check_complete.')
    score_path = os.path.join(scratch, 'score.json')
    args = [os.path.join(SKILL_SCRIPTS, 'board_score.py'), a.board,
            '--json', score_path, '--quiet']
    for flag, val in (('--clearance', a.clearance), ('--intent', a.intent),
                      ('--length-groups', a.length_groups),
                      ('--net-min-widths', a.net_min_widths),
                      ('--min-track-width', a.min_track_width),
                      ('--min-via-diameter', a.min_via_diameter),
                      ('--min-via-drill', a.min_via_drill)):
        if val is not None:
            args += [flag, str(val)]
    if a.impedance_nets:
        args += ['--impedance-nets'] + list(a.impedance_nets)
    code, out = _run(args)
    score = {}
    if os.path.isfile(score_path):
        with open(score_path, encoding='utf-8') as fh:
            score = json.load(fh)
    doc['score'] = score
    blocking = score.get('blocking')
    ungraded = sorted(score.get('ungraded') or [])
    unknown = sorted(score.get('unknown') or [])

    # ---- 2. the instruments board_score has no component for ---------------
    extra = {}
    if not a.skip_slow:
        layers = copper_layers(a.board)
        # check_orphan_stubs hardcodes four layers, so on a 6+ layer board the
        # inner ones are never scanned and it says nothing about them. Ask per
        # layer instead of accepting a partial sweep as a clean one.
        stub_hits, stub_ran = 0, []
        for ly in layers:
            c, o = _run(['check_orphan_stubs.py', a.board, '--layer', ly])
            stub_ran.append(ly)
            if c == 1:
                stub_hits += 1
        extra['orphan_stubs'] = {'ran': True, 'layers': stub_ran,
                                 'layers_with_orphans': stub_hits}
        for name, cmd in (
                ('weird_copper', ['check_weird.py', a.board]),
                ('pad_overlaps', ['check_pads.py', a.board,
                                  '--cross-footprint'])):
            c, o = _run(cmd)
            extra[name] = {'ran': True, 'exit': c, 'clean': c == 0}
    doc['components'] = extra

    # ---- 3. the fab floors this board grades itself against ----------------
    floors = fab_floor_integrity(a.board, a.authored_from)
    doc['fab_floors'] = floors

    # ---- the verdict -------------------------------------------------------
    reasons = []
    if unknown:
        reasons.append('a component RAN and could not answer: '
                       + ', '.join(unknown))
    if blocking is None:
        reasons.append('blocking is null -- something was not graded, and a '
                       'null is not a zero')
    elif blocking:
        reasons.append(f'blocking = {blocking}')
    for name, r in sorted(extra.items()):
        if r.get('layers_with_orphans'):
            reasons.append(f'{name}: {r["layers_with_orphans"]} layer(s) carry '
                           f'orphan stubs')
        elif r.get('clean') is False:
            reasons.append(f'{name}: not clean (exit {r.get("exit")})')

    if floors.get('relaxed'):
        worst = ', '.join(f'{r["label"]} {r["authored"]} -> {r["on_board"]}'
                          for r in floors['relaxed'])
        verdict, code_out = 'UNSOUND', UNSOUND
        why = (f'this board carries copper below floors its project once '
               f'declared ({worst}). Every checker grades against the NEW '
               f'value, so a clean report here means the rule moved, not the '
               f'copper. Confirm the fab supports it before calling it done.')
    elif reasons:
        verdict, code_out = 'INCOMPLETE', INCOMPLETE
        why = '; '.join(reasons)
    else:
        verdict, code_out = 'DONE', DONE
        why = 'every component that could be graded is graded and clean'

    if ungraded:
        why += ('. UNEXAMINED, and not passed: ' + ', '.join(ungraded)
                + ' -- nothing was asked to grade them, so they are unknown '
                  'rather than clean')
    doc['verdict'] = verdict
    doc['reason'] = why
    doc['ungraded'] = ungraded
    shutil.rmtree(scratch, ignore_errors=True)
    print(f'VERDICT: {verdict} -- {why}')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(doc, fh, indent=1, sort_keys=True, default=str)
        print(f'  JSON -> {a.json}')
    return code_out


if __name__ == '__main__':
    import cli_banner
    cli_banner.install()
    sys.exit(main())
