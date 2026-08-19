#!/usr/bin/env python3
"""The board's OWN declared fab floors bind at route time.

Run 22 routed a board declaring min_clearance 0.15 / min_track_width 0.15 /
min_via_diameter 0.5 / min_via_drill 0.25. The router stepped BELOW those
floors and the .kicad_pro writeback then relaxed the declaration to match, so
the board reported `unrouted 0, broken 0` while carrying 39 objects under its
own declared floors and every checker read clean.

The authority rule is the delicate part, and the corpus disproved the obvious
version of it -- see `fab_tiers.declared_fab_floors`. These tests pin the
measurements that decided it, so a future simplification has to argue with the
data rather than with a preference.

Run: python3 -X utf8 tests/test_run22_board_floor_binding.py
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for _p in ('py_router', 'py_tools', 'py_placer'):
    sys.path.insert(0, os.path.join(ROOT, _p))
os.environ.setdefault('KRT_NO_BANNER', '1')

import fab_tiers as F                                          # noqa: E402

FAILURES = []
BOARDS = os.path.join(ROOT, 'kicad_files')


def check(name, cond, detail=''):
    print(f'  {"PASS" if cond else "FAIL"}  {name}'
          + (f'\n        {detail}' if not cond and detail else ''))
    if not cond:
        FAILURES.append(name)


def _help_text():
    import argparse
    ap = argparse.ArgumentParser()
    F.add_board_floor_args(ap)
    return ap.format_help()


def board(n):
    return os.path.join(BOARDS, n + '.kicad_pcb')


def rungs(n=4, **kw):
    return [(r['track_width'], r['via_diameter'], r['via_drill'])
            for r in F.fab_floor_ladder(n, **kw)]


def ring(r):
    return (r['via_diameter'] - r['via_drill']) / 2.0


def main():
    print('authority: the ORIGIN outranks a ratcheted rules block')
    # THE measurement that overturned "differs from stock therefore authored".
    # fanout_output1 is a tool OUTPUT: its rules block IS the relaxed
    # writeback, while its own fab_floor_origin records what the board
    # declared before this toolchain ever touched it. Binding the rules block
    # would bind a number the router itself wrote.
    fl, src = F.declared_fab_floors(board('fanout_output1'))
    check('a ratcheted project binds its ORIGIN, not its current rules',
          fl.get('via_diameter') == 0.45 and fl.get('via_drill') == 0.25,
          f'{fl} -- current rules are 0.3/0.2, origin is 0.45/0.25')
    check('...and says so', src.get('via_diameter') == 'fab_floor_origin', src)

    print('authority: provenance is the only positive evidence of authorship')
    fl, src = F.declared_fab_floors(board('tigard'))
    check('tigard binds all three floors',
          fl == {'track_width': 0.15, 'via_diameter': 0.5, 'via_drill': 0.25},
          str(fl))
    # via_drill is NOT in tigard's rules block -- 0.25 lives only in the
    # Default netclass. Provenance names that field with the upstream
    # s-expression it came from, which is what lets a netclass value bind in
    # `authored` mode without guessing.
    check('...including via_drill, which exists only in the netclass',
          src.get('via_drill') == 'board provenance', str(src))

    print('authority: stock is evidence of nothing')
    fl, _ = F.declared_fab_floors(board('flat_hierarchy'))
    check('a pure-stock project binds nothing in `authored`', fl == {}, str(fl))
    fl, _ = F.declared_fab_floors(board('flat_hierarchy'), mode='all')
    check('...and binds in `all`', bool(fl), str(fl))

    print('authority: no project, and the hard negative')
    fl, _ = F.declared_fab_floors(board('esp_prog'))
    check('a board with no .kicad_pro binds nothing', fl == {}, str(fl))
    fl, _ = F.declared_fab_floors(board('tigard'), mode='off')
    check('mode off binds nothing at all', fl == {}, str(fl))
    # tigard records min_copper_edge_clearance as deliberately_absent. It is
    # not a bindable key here, but the mechanism must be exercised, so assert
    # the resolver reports the refusal rather than silently omitting it.
    _, src = F.declared_fab_floors(board('tigard'))
    check('the resolver never invents a floor the author left undeclared',
          'deliberately absent' not in src.values()
          or all(k not in F.declared_fab_floors(board('tigard'))[0]
                 for k, v in src.items() if v == 'deliberately absent'),
          str(src))

    print('the clamp: hazards that would ship a hole with no land')
    base = rungs()
    F.set_board_floors({'via_drill': 0.25}, {'via_drill': 'board rules'},
                       'authored')
    lad = F.fab_floor_ladder(4)
    # A board declaring ONLY a drill floor, clamped onto the advanced rung
    # (via_diameter 0.25), lands a ZERO annular ring. _pin_via_ring fires only
    # on that, and before this change it was called at two sites, NEITHER on
    # the escalation-rung path -- so the clamp has to re-run it per rung.
    check('every clamped rung keeps a positive annular ring',
          all(ring(r) > 0 for r in lad),
          str([(r['via_diameter'], r['via_drill']) for r in lad]))

    F.set_board_floors({'via_diameter': 0.5}, {'via_diameter': 'board rules'},
                       'authored')
    F.fab_floor_ladder(4)
    blocks = F.board_floor_blocks()
    # warn_fab_escalation compares against ladder[0]; with rung 0 raised to
    # 0.5 no rung is below it, so no escalation is recorded -- correctly,
    # because none happened. The information still has to go somewhere.
    check('escalations the floor prevented are recorded, not just absent',
          len(blocks) == 2, str(blocks))
    check('...naming what the rung would have been',
          all('from' in b and 'to' in b for b in blocks), str(blocks))

    print('the clamp reaches an EXPLICIT tier, not just the process default')
    # route.py:768 asks for the advanced tier BY NAME to floor a netclass
    # width. If the clamp were gated on `tier is None` that path would slip
    # under a declared min_track_width with no edit visible anywhere.
    F.set_board_floors({'track_width': 0.15}, {'track_width': 'board rules'},
                       'authored')
    adv = F.fab_floor_ladder(4, tier='advanced')
    check('an explicitly-named tier is still clamped',
          all(r['track_width'] >= 0.15 for r in adv),
          str([r['track_width'] for r in adv]))

    print('off is byte-identical -- the compatibility gate')
    F.set_board_floors(None, None, 'off')
    check('the ladder returns to exactly what it was', rungs() == base,
          f'{rungs()} != {base}')
    check('...for 2 layers too', len(rungs(2)) == len(F.fab_floor_ladder(2)))
    check('and nothing is recorded', F.board_floor_blocks() == [])

    print('the writeback HOLD -- run 22 relaxed four floors; hold all four')
    from fix_kicad_drc_settings import compute_targets
    hold = F.declared_writeback_hold(board('tigard'))
    check('tigard holds all four declared rules',
          hold == {'min_track_width': 0.15, 'min_via_diameter': 0.5,
                   'min_via_drill': 0.25, 'min_clearance': 0.15}, str(hold))
    # The exact relaxation run 22 shipped: 0.15 -> 0.125, 0.15 -> 0.0889,
    # 0.5 -> 0.25, 0.25 -> 0.15, with every checker then grading against the
    # rewritten project.
    emitted = {'min_track_width': 0.0889, 'min_via_diameter': 0.25,
               'min_via_drill': 0.15, 'min_through_hole_diameter': 0.15}
    t = compute_targets(clearance=0.125, track_width=0.0889, via_diameter=0.25,
                        via_drill=0.15, minima=emitted, hold=hold)
    check('the declaration is NOT lowered to match emitted copper',
          (t['min_clearance'], t['min_track_width'], t['min_via_diameter'],
           t['min_via_drill']) == (0.15, 0.15, 0.5, 0.25),
          str({k: t.get(k) for k in hold}))
    check('min_connection follows the held track floor',
          t['min_connection'] == 0.15, str(t.get('min_connection')))
    # PADS are not vias. A 0.25 pad drill legitimately sits below a declared
    # via floor, so this key is deliberately outside the hold.
    check('min_through_hole_diameter is NOT held (it spans pads)',
          t['min_through_hole_diameter'] == 0.15,
          str(t.get('min_through_hole_diameter')))

    t0 = compute_targets(clearance=0.125, track_width=0.0889, via_diameter=0.25,
                         via_drill=0.15, minima=emitted)
    check('...and with no hold the old ratchet is unchanged',
          (t0['min_clearance'], t0['min_track_width']) == (0.125, 0.0889),
          str(t0))

    # An INHERITED violation must still pass: the hold is the DECLARATION, so
    # a board that already carried sub-declaration copper keeps its number and
    # does not storm.
    t1 = compute_targets(clearance=0.15, track_width=0.1,
                         minima={'min_track_width': 0.1},
                         hold={'min_track_width': 0.1})
    check('an inherited sub-declaration floor is not raised into a storm',
          t1['min_track_width'] == 0.1, str(t1.get('min_track_width')))

    print('the hold must not raise a declaration ABOVE inherited copper')
    # Found by running the corpus sweep, not by reasoning. kicad_files/
    # fanout_output1 resolves (via fab_floor_origin) to via 0.45 / drill 0.25,
    # while the copper actually on that board is 0.3 / 0.2. A pure declaration
    # hold keeps the project claiming 0.45 and KiCad then flags the board's own
    # INHERITED vias -- the phantom-violation storm, reached from the other
    # direction. The declaration may fall only as far as the input board's
    # copper already went.
    from fix_kicad_drc_settings import scan_board_minima
    hold = F.declared_writeback_hold(board('fanout_output1'))
    mins = scan_board_minima(board('fanout_output1'))
    check('the fixture still has the shape this guards',
          hold.get('min_via_diameter') == 0.45
          and mins.get('min_via_diameter') == 0.3,
          f'hold={hold.get("min_via_diameter")} copper='
          f'{mins.get("min_via_diameter")} -- if this drifted, the case below '
          f'proves nothing')
    capped = dict(hold)
    for k in list(capped):
        v = mins.get(k)
        if isinstance(v, (int, float)) and v > 0:
            capped[k] = min(capped[k], v)
    check('capping keeps the declaration at the inherited copper',
          capped.get('min_via_diameter') == 0.3, str(capped))
    t = compute_targets(via_diameter=0.3, minima={'min_via_diameter': 0.3},
                        hold=capped)
    check('...so the writeback does not flag the board its own vias',
          t['min_via_diameter'] == 0.3, str(t.get('min_via_diameter')))
    # And the capping must not weaken the copper-free case, which is the one
    # run 22 actually shipped.
    hold_t = F.declared_writeback_hold(board('tigard'))
    mins_t = scan_board_minima(board('tigard'))
    check('a copper-free board caps to nothing and holds its full declaration',
          not any(isinstance(mins_t.get(k), (int, float)) and mins_t[k] > 0
                  for k in hold_t),
          str({k: mins_t.get(k) for k in hold_t}))

    print('the escape-via question: NOT exempt, and the message says so')
    # DECIDED, with the measurement that decided it. Flipping the default to
    # `authored` broke test_tigard_usb_diff [underpad-scoped] and
    # test_watchy_diff_hybrid_escape while [bare] stayed clean, which looked
    # like "underpad escapes need sub-declaration vias, so exempt them".
    #
    # The actual failure is one VIA-VIA pair: tigard's U3 escape puts two vias
    # 0.6mm apart (the QFN pad pitch, a property of the PART, not a choice).
    # At 0.45 the edge gap is 0.15 -- exactly the clearance. Pinned up to the
    # board's declared 0.5 the gap is 0.10, and check_drc reports overlap
    # 0.050mm. The arithmetic is the whole story.
    #
    # NOT EXEMPT, because an escape via is drilled and plated by the same
    # process as any other via -- via-in-pad differs in FINISHING (filled,
    # capped; the repo models that separately via tenting_attrs and
    # fab_notes.print_via_in_pad_note), not in drill capability. Exempting it
    # would let `authored` emit sub-declaration copper on exactly the path
    # that produced run 22's defect. The failure is the flag WORKING: tigard
    # cannot escape U3 underpad at its own declared via size.
    check('a QFN pitch of 0.6 fits a 0.45 via at 0.15 clearance',
          round(0.6 - 0.45, 6) >= 0.15)
    check('...and its declared 0.5 misses by the 0.050 check_drc reports',
          abs((0.15 - (0.6 - 0.5)) - 0.050) < 1e-9,
          str(round(0.15 - (0.6 - 0.5), 6)))

    # The message that pin prints used to blame `--fab-tier` and recommend
    # `--fab-overrides`. Under a board binding that advice is not merely
    # unhelpful, it is PROVABLY USELESS -- the board clamp is applied on top
    # of the tier and its overrides:
    ov = {'via_diameter': 0.35, 'via_drill': 0.2, 'track_width': 0.1}
    F.set_board_floors(None, None, 'off')
    check('an override alone reaches 0.35',
          F.fab_floor_for_param('via_size', 4, 'standard', ov) == 0.35)
    F.set_board_floors({'via_diameter': 0.5},
                       {'via_diameter': 'board provenance'}, 'authored')
    check('...and cannot undercut a bound board floor',
          F.fab_floor_for_param('via_size', 4, 'standard', ov) == 0.5,
          'if this ever passes, the old --fab-overrides advice became true '
          'again and the message below should go back')

    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        pinned = F.enforce_fab_floors(4, 'standard', ov, via_size=0.45)
    msg = buf.getvalue()
    check('the pin still happens', pinned.get('via_size') == 0.5, str(pinned))
    check('...and names THIS BOARD, not the tier',
          "THIS BOARD'S declared floor" in msg, msg.strip()[:200])
    check('...and cites the provenance', 'board provenance' in msg,
          msg.strip()[:200])
    check('...and gives a remedy that works',
          '--board-floors off' in msg and '--fab-overrides cannot' in msg,
          msg.strip()[:200])

    # The unbound path must keep the original message -- there the tier IS the
    # source and --fab-overrides IS the remedy.
    F.set_board_floors(None, None, 'off')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        F.enforce_fab_floors(4, 'standard', None, via_size=0.05)
    msg = buf.getvalue()
    check('an unbound pin still blames the tier and offers --fab-overrides',
          'selected --fab-tier' in msg and 'Pass --fab-overrides' in msg,
          msg.strip()[:200])
    check('...and does not claim the board declared anything',
          "THIS BOARD" not in msg, msg.strip()[:200])

    check('the flag help states the escape incompatibility',
          'not exempt' in (F.add_board_floor_args.__doc__ or '').lower()
          or 'NOT exempt' in _help_text(),
          'the --board-floors help must say that binding can make an underpad '
          'escape infeasible, since that is the documented consequence of not '
          'exempting')

    print()
    if FAILURES:
        print(f'FAIL: {len(FAILURES)} check(s): {", ".join(FAILURES)}')
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
