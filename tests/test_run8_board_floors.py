#!/usr/bin/env python3
"""A tool's default must not contradict the board's own declared floor.

route_planes' --min-thickness defaulted to a fixed 0.1mm while this repo's own
connection-width grader reads the board's min_track_width. On a board whose
author declared a wider floor, the pour emitted ribbons the grader then called
too thin: a violation the pour created against a rule it never read.

Unset now resolves from the board (measured: a board declaring 0.2mm resolves
to 0.2), and falls back to the packaged default only when the board declares
nothing.

NOT "which is the case for every board in this repo, since project siblings
are not committed" -- that claim, which D9 (5894b95) used as its evidence of
no behaviour change, is FALSE. `git ls-files kicad_files/*.kicad_pro` returns
TWO: flat_hierarchy and routed_output, and both declare real floors. See
_q5_committed_projects_are_real below for what D9 actually changed on them.

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
    """A board that DECLARES a floor, built to order.

    Most boards in kicad_files/ declare nothing -- but NOT all of them, which
    is the correction in the module docstring: flat_hierarchy and
    routed_output ship committed .kicad_pro siblings. Those two are used
    directly by _q5_committed_projects_are_real; this fixture exists so the
    resolver's OTHER branches (a value the corpus does not happen to declare,
    the 0.0 trap, a malformed project) are reachable at all."""
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
    # the placement model a REAL edge floor of zero where it had used 0.55.
    #
    # WHAT THAT ACTUALLY COSTS, measured on interf_u_unrouted_placed with a
    # 0.0-declaring project (NOT the "every edge/halo term collapses" I first
    # wrote in the commit message -- quench takes max(clearance, edge), so 0.0
    # degrades to the 0.2 pad clearance rather than to nothing, and `edge` and
    # `halo` do not move at all):
    #
    #     edge  15.516 -> 15.516     halo 303.803 -> 303.803   (unchanged)
    #     oob_amount  22.039 -> 24.489      oob_area 398.51 -> 445.44
    #
    # i.e. it UNDER-REPORTS off-board pad copper by ~11%, which CLAUDE.md names
    # as the top-priority placement defect ("converts one-for-one into unrouted
    # and broken"). Under-reporting that is the harm; it is smaller and more
    # specific than the sweeping claim, and the number is the point.
    # The two helpers must agree about the one trap this module documents.
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


# --- Q3: the ROUTING half read the same two constraints its own way ---------
#
# D9 put the `> 0` guard in the placement helpers and stopped there. The four
# routing mains each kept a private copy of
# `board_constraint(...) if ... is not None else <default>` -- eight sites, an
# `is not None` test with no positivity guard -- so one declared floor got two
# answers depending on which half of the loop asked.
#
# On a board declaring `min_copper_edge_clearance: 0.0` (KiCad's "not
# configured"): placement / floorplan / render resolved 0.55 [fixed default];
# route.py took a REAL floor of 0.0 while printing "using the board
# min_copper_edge_clearance 0.0mm" -- announcing a declaration that was not
# one. The plane engines were worse than misleading: their inset fell from
# PLANE_EDGE_CLEARANCE 0.5 to 0.0, on the very comment that says they keep 0.5
# "only when the board declares no edge rule of its own". The GUI's plane tab
# was already right (swig_gui._effective_plane_edge_clearance guards `> 1e-9`),
# so this was a CLI-only divergence from the GUI as well.

_CLI_FLOOR_SITES = ('route.py', 'route_diff.py', 'route_planes.py',
                    'route_disconnected_planes.py')
_RAW_KEYS = ('min_hole_to_hole', 'min_copper_edge_clearance')


def _q3_routing_half_uses_the_same_resolver():
    import io
    import contextlib
    import tempfile
    from list_nets import (board_floor, board_floor_knobs, resolve_cli_floor)

    print('one declared floor, one number, on both halves of the loop')
    with tempfile.TemporaryDirectory() as tmp:
        # A board that DECLARES a positive edge rule. Both halves must land on
        # it -- this is the "one number" claim in its testable form.
        decl = _fixture(tmp, extra_rules={'min_copper_edge_clearance': 0.3,
                                          'min_hole_to_hole': 0.3})
        _c, edge_place, knobs = board_floor_knobs(decl)
        with contextlib.redirect_stdout(io.StringIO()):
            edge_sig = resolve_cli_floor(decl, 'board_edge_clearance', None,
                                         defaults.BOARD_EDGE_CLEARANCE, '--x')
            edge_pln = resolve_cli_floor(decl, 'board_edge_clearance', None,
                                         defaults.PLANE_EDGE_CLEARANCE, '--x')
        check('a DECLARED 0.3 edge rule is 0.3 on the placement half',
              edge_place == 0.3
              and knobs['board_edge_clearance']['source'] == 'board constraint',
              str(knobs['board_edge_clearance']))
        check('...and 0.3 on the routing half, signal and plane alike',
              edge_sig == 0.3 and edge_pln == 0.3,
              f'signal {edge_sig}, plane {edge_pln}')

    print('a DECLARED 0.0 is UNSET on the routing half too')
    with tempfile.TemporaryDirectory() as tmp:
        z = _fixture(tmp, extra_rules={'min_copper_edge_clearance': 0.0,
                                       'min_hole_to_hole': 0.0})
        _c, edge_place, knobs = board_floor_knobs(z)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            edge_sig = resolve_cli_floor(z, 'board_edge_clearance', None,
                                         defaults.BOARD_EDGE_CLEARANCE, '--x')
            edge_pln = resolve_cli_floor(z, 'board_edge_clearance', None,
                                         defaults.PLANE_EDGE_CLEARANCE, '--x')
            h2h = resolve_cli_floor(z, 'hole_to_hole', None,
                                    defaults.HOLE_TO_HOLE_CLEARANCE, '--y')
        said = buf.getvalue()

        # BOTH halves must reach the same VERDICT about the board: it declared
        # nothing. The fallbacks then legitimately differ -- BOARD_EDGE_CLEARANCE
        # 0.0 is a deliberate "no edge rule, use the copper-copper clearance"
        # sentinel (route.py:896, obstacle_map.py:797), the plane engines want
        # 0.5, the placement model 0.55 -- and are NOT unified here.
        check('placement half: declared 0.0 reads as fixed default',
              edge_place == 0.55
              and knobs['board_edge_clearance']['source'] == 'fixed default',
              str(knobs['board_edge_clearance']))
        check('routing half agrees the board declared nothing',
              board_floor(z, 'board_edge_clearance', None, 0.0)[1]
              == 'fixed default'
              and board_floor(z, 'hole_to_hole', None, 0.2)[1]
              == 'fixed default')
        # The value fixes, each measured against what the old raw read gave.
        check('plane inset stays PLANE_EDGE_CLEARANCE (was 0.0)',
              edge_pln == defaults.PLANE_EDGE_CLEARANCE, f'got {edge_pln}')
        check('hole-to-hole stays the packaged floor (was 0.0)',
              h2h == defaults.HOLE_TO_HOLE_CLEARANCE, f'got {h2h}')
        check('the signal sentinel is unchanged at 0.0',
              edge_sig == defaults.BOARD_EDGE_CLEARANCE, f'got {edge_sig}')
        # And it must stop claiming the board said so.
        check('the print no longer attributes 0.0 to the board',
              'min_copper_edge_clearance' not in said
              and 'min_hole_to_hole' not in said, said.strip())
        check('the print names its source in the placement vocabulary',
              said.count('[fixed default]') == 3, said.strip())

    # THE WIRING. Every check above passes with all eight call sites reverted
    # to the raw read -- the exact hole D10 was pulled up for. So assert the
    # mains actually route through the resolver, and that the raw read is gone.
    print('all four routing mains go through the one resolver')
    import ast
    for fn in _CLI_FLOOR_SITES:
        src = open(os.path.join(ROOT, fn), encoding='utf-8').read()
        tree = ast.parse(src)
        floors = set()
        raw = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            fname = getattr(node.func, 'id', None) or getattr(
                node.func, 'attr', None)
            first_str = [a.value for a in node.args
                         if isinstance(a, ast.Constant)
                         and isinstance(a.value, str)]
            if fname == 'resolve_cli_floor':
                floors.update(first_str)
            elif fname == 'board_constraint':
                raw += [s for s in first_str if s in _RAW_KEYS]
        check(f'{fn}: both floors via resolve_cli_floor',
              {'hole_to_hole', 'board_edge_clearance'} <= floors,
              f'found {sorted(floors)}')
        check(f'{fn}: no raw board_constraint read of either key',
              not raw, f'raw reads: {raw}')

    # ...and the mains ACTUALLY PRINT it, which the AST check cannot show. Each
    # runs in ~1.3s on a net that matches nothing, so this is the CLI's own
    # answer rather than a model of it. At 62f7c13^ these lines read "using the
    # board min_copper_edge_clearance 0.0mm" and the plane engines resolved 0.0.
    print('...and each main prints the resolved floor, crediting the right source')
    import subprocess
    import tempfile
    # (flag-shape, edge-floor-expected) per main; hole-to-hole is 0.2 for all.
    mains = [
        ('route.py', lambda i, o: [i, o, '--nets', '__none__'], 0.0),
        ('route_diff.py', lambda i, o: [i, '--output', o, '--nets', '__none__'], 0.0),
        ('route_planes.py', lambda i, o: [i, '--output', o, '--nets', '__none__',
                                          '--plane-layers', 'B.Cu'], 0.5),
        ('route_disconnected_planes.py',
         lambda i, o: [i, '--output', o, '--nets', '__none__',
                       '--plane-layers', 'B.Cu'], 0.5),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        z = _fixture(tmp, extra_rules={'min_copper_edge_clearance': 0.0,
                                       'min_hole_to_hole': 0.0})
        for fn, argv, edge in mains:
            out = os.path.join(tmp, 'o_' + fn.replace('.py', '') + '.kicad_pcb')
            r = subprocess.run([sys.executable, '-X', 'utf8', fn] + argv(z, out),
                               cwd=ROOT, capture_output=True, text=True,
                               timeout=300)
            lines = [ln.strip() for ln in (r.stdout or '').splitlines()
                     if ln.startswith('--hole-to-hole-clearance not given')
                     or ln.startswith('--board-edge-clearance not given')]
            said = ' '.join(lines)
            check(f'{fn}: prints both resolved floors',
                  len(lines) == 2, said or (r.stderr or '')[-300:])
            check(f'{fn}: hole-to-hole 0.2 [fixed default], not a declared 0.0',
                  f'--hole-to-hole-clearance not given; using 0.2mm '
                  f'[fixed default].' in said, said)
            check(f'{fn}: board edge {edge} [fixed default]',
                  f'--board-edge-clearance not given; using {edge}mm '
                  f'[fixed default].' in said, said)
            check(f'{fn}: does not credit the board for what it left unset',
                  'min_copper_edge_clearance' not in said
                  and 'min_hole_to_hole' not in said, said)


# --- Q4: board_floor is NOT raise-only, and a drill consumer must wrap it ---
#
# board_floor returns the declared value whenever it is positive, with no
# max() against the fallback. For most of its table that is exactly right --
# check_channels / check_assembly must grade at the board's own clearance even
# when it is BELOW their default. For a DRILL floor it is a fab hazard, and the
# qfn underpad escape claimed "Raise-only in practice" while doing no such
# thing: a project declaring `min_hole_to_hole: 0.10` spaced that run's drills
# at 0.10, under the 0.20 JLC floor. `resolve_hole_clearance` is raise-only
# only because ITS consumers wrap it; this is the same wrap, and the same
# demonstration.

def _qfn_fixture(tmp, h2h):
    """tigard (a real QFN board) with a project declaring min_hole_to_hole."""
    import shutil
    import json as _json
    src = os.path.join(ROOT, 'kicad_files', 'tigard.kicad_pcb')
    if not os.path.exists(src):
        return None
    dst = os.path.join(tmp, 'h2h.kicad_pcb')
    shutil.copyfile(src, dst)
    with open(os.path.splitext(dst)[0] + '.kicad_pro', 'w',
              encoding='utf-8') as f:
        _json.dump({'net_settings': {'classes': [
            {'name': 'Default', 'clearance': 0.2, 'track_width': 0.25}]},
            'board': {'design_settings': {'rules': {'min_hole_to_hole': h2h}}}},
            f)
    return dst


def _qfn_effective_h2h(board):
    """The hole_to_hole the underpad escape actually routes with.

    Read off what the engine FEEDS run_output_conflict, which is where
    f1dd280 said the value goes -- not re-derived, or the test would only be
    checking arithmetic it wrote itself.
    """
    import io
    import contextlib
    from kicad_parser import parse_kicad_pcb
    import qfn_fanout as Q

    seen = []
    real = Q.run_output_conflict

    def spy(*a, **kw):
        seen.append(kw.get('hole_to_hole'))
        return real(*a, **kw)

    Q.run_output_conflict = spy
    try:
        pcb = parse_kicad_pcb(board)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            Q.generate_qfn_fanout(
                pcb.footprints["U3"], pcb, net_filter=["/USB_DP", "/USB_DN"],
                layer="F.Cu", track_width=0.1, clearance=0.1, grid_step=0.05,
                escape_method="underpad", via_size=0.45, via_drill=0.25)
    finally:
        Q.run_output_conflict = real
    return (set(v for v in seen if v is not None), buf.getvalue())


def _q4_a_declared_value_must_not_relax_a_fab_floor():
    import tempfile
    from list_nets import board_floor
    from fab_tiers import fab_floor_min

    print('board_floor is board-authoritative, NOT raise-only')
    with tempfile.TemporaryDirectory() as tmp:
        b = _fixture(tmp, extra_rules={'min_hole_to_hole': 0.10})
        # The CLAIM, corrected: this is the documented behaviour, not a bug to
        # fix in the helper -- check_channels needs exactly this freedom.
        check('a declared 0.10 resolves DOWN, and says it came from the board',
              board_floor(b, 'hole_to_hole', None, 0.2)
              == (0.1, 'board constraint'),
              str(board_floor(b, 'hole_to_hole', None, 0.2)))

    fab = fab_floor_min(4).get('hole_to_hole')
    check('the fab hole-to-hole floor is the thing being protected',
          fab == 0.20, f'got {fab}')

    print('...so the qfn DRILL consumer wraps it, and discloses the pin')
    with tempfile.TemporaryDirectory() as tmp:
        b = _qfn_fixture(tmp, 0.10)
        if b is None:
            print('  SKIP  no tigard board (qfn drill floor)')
            return
        got, said = _qfn_effective_h2h(b)
        check('a declared 0.10 does NOT space this run\'s drills at 0.10',
              got == {0.20}, f'engine used {sorted(got)}')
        check('...and it is not relaxed SILENTLY',
              'below the 0.2mm fab hole-to-hole floor' in said, said.strip())

    print('...while a declared value ABOVE the floor still wins')
    with tempfile.TemporaryDirectory() as tmp:
        b = _qfn_fixture(tmp, 0.30)
        got, said = _qfn_effective_h2h(b)
        check('a declared 0.30 raises the drill spacing to 0.30',
              got == {0.30}, f'engine used {sorted(got)}')
        check('...and says the board is where it came from',
              "from the board's own" in said, said.strip())

    print('...and a board declaring nothing is byte-identical')
    with tempfile.TemporaryDirectory() as tmp:
        import shutil
        src = os.path.join(ROOT, 'kicad_files', 'tigard.kicad_pcb')
        dst = os.path.join(tmp, 'silent.kicad_pcb')
        shutil.copyfile(src, dst)          # no .kicad_pro sibling at all
        got, said = _qfn_effective_h2h(dst)
        check('the packaged default stands, unannounced',
              got == {defaults.HOLE_TO_HOLE_CLEARANCE}
              and 'hole-to-hole' not in said.lower(), f'{sorted(got)}')


# --- Q5: D9's "no board declares a floor" evidence was false ----------------
#
# 5894b95 justified its no-behaviour-change claim with "every board in
# kicad_files/ declares no floor (project siblings are not committed)". Two
# ARE committed:
#
#     kicad_files/flat_hierarchy.kicad_pro   Default clearance 0.2  track 0.2
#     kicad_files/routed_output.kicad_pro    Default clearance 0.09 track 0.09
#
# against the old constants clearance 0.25 / track 0.3. So on those two boards
# D9 was a real, unmeasured behaviour change. Measured here, 5894b95^ vs HEAD,
# check_channels:
#
#     flat_hierarchy   0 faces          -- no change (nothing to measure)
#     routed_output    supply 390 -> 1084 (+694 lanes), deficit_faces 5 -> 0
#
# BENIGN, and in the direction D9 exists to fix: routed_output's own copper is
# 1701 segments at track widths 0.1 / 0.111 / 0.178 -- it contains NO 0.3mm
# track anywhere. The old constant measured a width the board never uses, and
# the 5 "deficits" it reported (including "IC1 E: DEFICIT AT FINEST GRID
# (floorplan-shaped)", demand 59 vs supply 25) were phantoms on a board that
# is routed through those faces. check_assembly: pad_conflicts 0 -> 0 and
# buildable True -> True on both boards; only the recorded clearance and its
# source changed.
#
# DIRECTION, stated because it is what makes this safe rather than lucky: for
# these instruments a LOOSER declared floor is the conservative direction
# (check_assembly reports more conflicts, check_channels fewer lanes). The
# risky direction is a TIGHTER declared floor, which is what both boards have
# -- and it is justified only because the copper really is that tight, which
# is asserted below rather than assumed.

_COMMITTED_PROJECTS = {
    'flat_hierarchy': (0.2, 0.2),        # (Default clearance, Default track)
    'routed_output': (0.09, 0.09),
}
_OLD_D9_CONSTANTS = (0.25, 0.3)          # clearance, track


def _q5_committed_projects_are_real():
    import subprocess
    from list_nets import board_floor

    print('kicad_files/ DOES ship committed project siblings')
    out = subprocess.run(['git', 'ls-files', 'kicad_files/*.kicad_pro'],
                         cwd=ROOT, capture_output=True, text=True).stdout
    tracked = {os.path.splitext(os.path.basename(p))[0]
               for p in out.split() if p.strip()}
    check('at least the two known .kicad_pro siblings are tracked',
          set(_COMMITTED_PROJECTS) <= tracked, f'git ls-files -> {sorted(tracked)}')

    for name, (clr, trk) in sorted(_COMMITTED_PROJECTS.items()):
        b = os.path.join(ROOT, 'kicad_files', name + '.kicad_pcb')
        if not os.path.exists(b):
            print(f'  SKIP  {name} board missing')
            continue
        got_c = board_floor(b, 'clearance', None, _OLD_D9_CONSTANTS[0])
        got_t = board_floor(b, 'track_width', None, _OLD_D9_CONSTANTS[1])
        check(f'{name}: the board ANSWERS, it does not fall back',
              got_c == (clr, 'board netclass') and got_t == (trk, 'board netclass'),
              f'{got_c} {got_t}')
        # The change direction, pinned: these declare TIGHTER than the old
        # constants, which is the direction that needs justifying.
        check(f'{name}: declared floor is tighter than the old D9 constants',
              clr < _OLD_D9_CONSTANTS[0] and trk < _OLD_D9_CONSTANTS[1],
              f'declared {clr}/{trk} vs {_OLD_D9_CONSTANTS}')

    # ...and the justification, measured off the copper rather than asserted:
    # a floor is only honest if the board's own tracks fit under the constant
    # it replaced. If routed_output ever gains a 0.3mm track this fails, and
    # the "the old constant measured a width this board never uses" claim
    # above has to be re-derived instead of inherited.
    print('...and the tighter floor matches the copper actually on the board')
    b = os.path.join(ROOT, 'kicad_files', 'routed_output.kicad_pcb')
    if os.path.exists(b):
        from kicad_parser import parse_kicad_pcb
        widths = {s.width for s in parse_kicad_pcb(b).segments}
        check('routed_output contains no track as wide as the old 0.3 constant',
              widths and max(widths) < _OLD_D9_CONSTANTS[1],
              f'widths {sorted(round(w, 4) for w in widths)}')
        check('...and none below the floor it declares',
              min(widths) >= _COMMITTED_PROJECTS['routed_output'][1] - 1e-9,
              f'min {min(widths)} vs declared {_COMMITTED_PROJECTS["routed_output"][1]}')

    # THE INSTRUMENT, not just the resolver -- and this is the part that fails
    # at 5894b95^. There check_channels ran at the 0.25/0.3 constants and
    # reported 5 deficit faces on this board (IC1 E "DEFICIT AT FINEST GRID
    # (floorplan-shaped)", demand 59 vs supply 25) out of a total supply of
    # 390. At the board's own 0.09/0.09 it reports 0 deficits and 1084. The
    # supply figure is asserted as a DIRECTION, not a digit, so a grid or
    # algorithm change does not turn this into a false alarm; the deficit
    # count is the decision the loop actually consumes, so that is exact.
    print('...and check_channels reports the board floor, with no phantom deficit')
    import json
    import subprocess
    import tempfile
    if os.path.exists(b):
        with tempfile.TemporaryDirectory() as tmp:
            jp = os.path.join(tmp, 'ch.json')
            r = subprocess.run(
                [sys.executable, '-X', 'utf8', 'check_channels.py', b,
                 '--json', jp], cwd=ROOT, capture_output=True, text=True)
            if not os.path.exists(jp):
                check('check_channels produced JSON', False,
                      (r.stderr or r.stdout)[-400:])
                return
            d = json.load(open(jp, encoding='utf-8'))
            floors = d.get('floors') or {}
            supply = sum(f['supply_finest_grid']
                         for fs in d['ledgers'].values() for f in fs)
            check('both floors are credited to the board, not a constant',
                  all(floors.get(k, {}).get('source') == 'board netclass'
                      for k in ('clearance', 'track_width')), str(floors))
            check('no phantom deficit face remains (was 5 at the constants)',
                  len(d.get('deficit_faces') or []) == 0,
                  str(d.get('deficit_faces'))[:300])
            check('escape supply exceeds the 390 the old constants reported',
                  supply > 390, f'supply {supply}')


# --- Q6: board-first ran D9 BACKWARDS in the one tool that PREDICTS ---------
#
# Q4 established that board_floor is board-authoritative, not raise-only, and
# that a consumer for which "downward" is a fab question must wrap it. Q4 then
# listed check_channels as correctly board-authoritative. That was wrong, and
# this is the correction.
#
# check_assembly GRADES existing geometry, so the board's own clearance is the
# right threshold. check_channels PREDICTS routability: a lane is
# `track + clearance` wide, so a declared pitch finer than the fab can etch
# makes it promise escape capacity nobody can manufacture. Measured on tigard
# --refs U3, fab floors 0.09 / 0.0762:
#
#     declared 0.2 /0.2    supply  29   deficit faces 3   (above the fab floor)
#     declared 0.05/0.05   supply 120   deficit faces 1   two real deficits gone
#     declared 0.02/0.02   supply 242   deficit faces 1
#
# That is the OPTIMISTIC direction and the dangerous one: a phantom DEFICIT
# wastes a placement search's effort, a phantom SUPPLY hides the defect
# entirely and steers the search away from it.
#
# After the wrap, 0.05 and 0.02 both pin to 0.09/0.0762 -> supply 68, deficit
# faces 2. NOTE: 2, not the 3 that a 0.2/0.2 board reports. Pinning restores
# the fab floor, not some other board's floor -- 0.09/0.0762 is genuinely
# finer than 0.2/0.2 and legitimately fits more lanes. Asserting "3" would be
# asserting the wrong invariant.

def _q6_a_predictor_must_not_promise_unetchable_lanes():
    import io
    import json
    import contextlib
    import shutil
    import subprocess
    import tempfile
    from fab_tiers import fab_floor_min, count_copper_layers_in_file

    src = os.path.join(ROOT, 'kicad_files', 'tigard.kicad_pcb')
    if not os.path.exists(src):
        print('  SKIP  no tigard board (channels fab floor)')
        return

    print('check_channels never predicts a lane finer than the fab can etch')
    fab = fab_floor_min(count_copper_layers_in_file(src))

    def run(tmp, clr, trk):
        """check_channels on tigard/U3 with a project declaring clr/trk."""
        b = os.path.join(tmp, 'ch.kicad_pcb')
        shutil.copyfile(src, b)
        if clr is not None:
            with open(os.path.splitext(b)[0] + '.kicad_pro', 'w',
                      encoding='utf-8') as f:
                json.dump({'net_settings': {'classes': [
                    {'name': 'Default', 'clearance': clr,
                     'track_width': trk}]}}, f)
        jp = os.path.join(tmp, 'ch.json')
        r = subprocess.run(
            [sys.executable, '-X', 'utf8', 'check_channels.py', b,
             '--refs', 'U3', '--json', jp], cwd=ROOT, capture_output=True,
            text=True, timeout=600)
        d = json.load(open(jp, encoding='utf-8'))
        d['_supply'] = sum(f['supply_finest_grid']
                           for fs in d['ledgers'].values() for f in fs)
        d['_said'] = r.stdout or ''
        return d

    with tempfile.TemporaryDirectory() as t1, \
            tempfile.TemporaryDirectory() as t2, \
            tempfile.TemporaryDirectory() as t3:
        sub = run(t1, 0.05, 0.05)      # below the fab floor
        deep = run(t2, 0.02, 0.02)     # further below -- must not differ
        okay = run(t3, 0.2, 0.2)       # above it -- must be untouched

    check('a sub-fab declaration is pinned UP to the fab floor',
          sub['clearance'] >= fab['clearance'] - 1e-9
          and sub['track_width'] >= fab['track_width'] - 1e-9,
          f"resolved {sub['clearance']}/{sub['track_width']} "
          f"vs fab {fab['clearance']}/{fab['track_width']}")
    # THE INVARIANT, stated so it cannot drift with the corpus: below the fab
    # floor the tool must stop responding to the declaration entirely. 0.05 and
    # 0.02 are both unetchable, so they must predict identically. Before the
    # wrap they gave supply 120 and 242.
    check('declaring finer buys NOTHING once below the fab floor',
          (sub['clearance'], sub['track_width'], sub['_supply'],
           len(sub['deficit_faces']))
          == (deep['clearance'], deep['track_width'], deep['_supply'],
              len(deep['deficit_faces'])),
          f"0.05 -> supply {sub['_supply']} / {len(sub['deficit_faces'])} faces; "
          f"0.02 -> supply {deep['_supply']} / {len(deep['deficit_faces'])}")
    # ...and the real deficits come back. Unwrapped, 0.05 reported 1.
    check('the deficits a sub-fab lane pitch hid are restored',
          len(sub['deficit_faces']) > 1,
          f"{len(sub['deficit_faces'])} deficit faces, supply {sub['_supply']}")
    check('and it SAYS it pinned, rather than quietly predicting elsewhere',
          'below the' in sub['_said'] and 'fab floor' in sub['_said'],
          sub['_said'][:300])
    # The control: a declaration ABOVE the fab floor is the board's business
    # and must pass through untouched, or this wrap has become the phantom
    # deficit D9 removed.
    check('a declaration above the fab floor is untouched',
          (okay['clearance'], okay['track_width']) == (0.2, 0.2)
          and 'fab floor' not in okay['_said'],
          f"resolved {okay['clearance']}/{okay['track_width']}")
    check('...and it is strictly less optimistic than the fab floor allows',
          okay['_supply'] < sub['_supply'],
          f"0.2/0.2 supply {okay['_supply']} vs fab-floor supply {sub['_supply']}")


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
    _q3_routing_half_uses_the_same_resolver()
    _q4_a_declared_value_must_not_relax_a_fab_floor()
    _q5_committed_projects_are_real()
    _q6_a_predictor_must_not_promise_unetchable_lanes()

    print()
    if FAILURES:
        print(f'FAIL: {len(FAILURES)} check(s): {", ".join(FAILURES)}')
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
