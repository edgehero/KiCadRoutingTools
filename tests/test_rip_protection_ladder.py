#!/usr/bin/env python3
"""The in-run rip ladder honours an EXACT-name override; 'locked' never lifts.

This file used to be `test_protect_nets_flag.py` and mostly tested
`--protect-nets`. That flag was REMOVED in 53a5a16e, which pulled it from both
engines, both GUI tabs, four settings keys, ai_plan's alias, the manifest
converter and the parity gate, and deleted three sibling test files -- but
missed this one. The flag half asserted behaviour that no longer exists and
could never pass again; it is gone, and CLAUDE.md records the removal as
deliberate ("there is deliberately no CLI flag or GUI control").

What SURVIVES is the mechanism, and it is still load-bearing: protection is
recorded in the sibling .kicad_pro and honoured automatically, and 53a5a16e
explicitly KEPT `cached_protection_map` ("Removing it broke route.py
outright"). So the unit test below -- no CLI, no removed flag -- is kept
verbatim rather than deleted with the flag it was filed beside.

Run: python3 -X utf8 tests/test_rip_protection_ladder.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for _p in ('py_router', 'py_tools', 'py_placer'):   # #522: the modules moved
    sys.path.insert(0, os.path.join(ROOT, _p))


def test_in_run_ladder_honors_exact_override():
    """Run-6 z2 defect: the pre-run filters lifted 'user' protection for an
    exactly-named net, but the in-run ladders (all six flow through
    filter_rippable_blockers) re-consulted cached_protection_map and refused
    it anyway -- 'protected_skipped {"phase3 tap cascade": {USB_DM_R: user}}'
    while --rip-existing-nets named it. Unit-pins the choke point:
    stashed exact-name overrides lift 'user' in-run; 'locked' never lifts;
    without a stash the refusal + record behave as before."""
    from types import SimpleNamespace
    from blocking_analysis import filter_rippable_blockers
    from protected_nets import (PROTECTED_SKIPPED, clear_skipped,
                                stash_rip_overrides)

    class _Net:
        def __init__(self, name):
            self.name = name

    def _pcb(protection):
        p = SimpleNamespace()
        p.nets = {1: _Net('RAIL_A'), 2: _Net('LOCKED_B'), 3: _Net('FREE_C')}
        # #521 added a KiCad-locked-copper scan to filter_rippable_blockers,
        # so the fake needs these two. They were missing and the test could
        # not have run -- it never did, because the --protect-nets function
        # beside it crashed first and __main__ never reached this one. A dead
        # test hiding a stale one is exactly why the flag half is gone.
        p.segments = []
        p.vias = []
        # The memo attribute protected_nets.cached_protection_map reads.
        # Renamed _protection_map_cache -> _protection_map_memo since
        # this fake was written; with the old name the fake silently
        # supplied NO protection and every net read as rippable.
        p._protection_map_memo = dict(protection)
        return p

    blockers = [SimpleNamespace(net_id=i) for i in (1, 2, 3)]
    routed = {1: object(), 2: object(), 3: object()}
    prot = {'RAIL_A': 'user', 'LOCKED_B': 'locked'}

    # (a) no stash: both protected nets refused, recorded with reasons
    clear_skipped()
    pcb = _pcb(prot)
    kept, _ = filter_rippable_blockers(blockers, routed, {}, lambda n, d: n,
                                       pcb_data=pcb, context='unit cascade')
    assert {b.net_id for b in kept} == {3}, kept
    assert PROTECTED_SKIPPED.get('unit cascade') == prot, PROTECTED_SKIPPED

    # (b) exact-name stash lifts 'user', never 'locked'
    clear_skipped()
    pcb = _pcb(prot)
    stash_rip_overrides(pcb, ['RAIL_A', 'LOCKED_B', 'GLOB_*'])
    kept, _ = filter_rippable_blockers(blockers, routed, {}, lambda n, d: n,
                                       pcb_data=pcb, context='unit cascade')
    assert {b.net_id for b in kept} == {1, 3}, kept
    assert PROTECTED_SKIPPED.get('unit cascade') == {'LOCKED_B': 'locked'}, \
        PROTECTED_SKIPPED

    # (c) a glob in the stash list is NOT an override
    clear_skipped()
    pcb = _pcb({'RAIL_A': 'user'})
    stash_rip_overrides(pcb, ['RAIL_*'])
    kept, _ = filter_rippable_blockers(blockers, routed, {}, lambda n, d: n,
                                       pcb_data=pcb, context='unit cascade')
    assert {b.net_id for b in kept} == {2, 3}, kept
    print("  PASS: in-run ladder honors exact-name overrides ('locked' never)")


if __name__ == '__main__':
    test_in_run_ladder_honors_exact_override()
    print("ALL PASS")
