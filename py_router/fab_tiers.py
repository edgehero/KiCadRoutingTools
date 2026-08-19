"""JLCPCB fab-capability floors, modelled as selectable cost tiers (issue #237).

A *fab tier* is the manufacturing floor the router shrinks tracks/vias/clearances
DOWN toward when a route needs it. The selected tier is a **floor ladder**:

  - ``standard``  (default, no extra fab cost): the cheap floor. Routing prefers it
                  but **auto-escalates to ``advanced`` (with a warning)** when a
                  fine-pitch fan-out genuinely cannot escape at the standard floor.
  - ``advanced``  (JLC "more costly" tier): the tight floor (0.25/0.15 via, 0.09 mm
                  track/clearance, ...). A **hard** floor — no escalation.

An optional ``--fab-overrides FILE`` (a plain ``key = value`` text file) overlays
the selected tier, replacing **only** the floor values listed in the file (the rest
come from the base tier). Supplying overrides pins the floor to a single **hard**
rung — escalation is disabled, because the file states the user's exact fab limits.

Values are sourced from jlcpcb.com/capabilities (saved at ~/Downloads/pcb_specs.mhtml,
2026-06): standard via 0.20 drill / 0.45 dia, advanced 0.15 / 0.25 ("more costly");
min drill 0.20 vs 0.15; track/clearance 0.10/0.10 (1-2 layer) vs 0.09/0.09 multilayer
(3 mil OK in BGA fan-outs); PTH annular recommended 0.25 (2L) / 0.20 (ML) vs absolute
minimum 0.18 / 0.15; Via hole-to-hole 0.20, Pad hole-to-hole 0.45.

This module is intentionally **stdlib-only** so the lightweight DRC-settings script can
import it without pulling in the PCB parser. ``list_nets`` re-exports the public names,
so ``from list_nets import fab_floors`` keeps working.
"""

import os
import re

# Flat floor keys every tier dict carries. Also the set an override file may set.
FLOOR_KEYS = ('clearance', 'track_width', 'via_diameter', 'via_drill',
              'hole_to_hole', 'pad_hole_to_hole', 'annular', 'board_edge')

# _FAB_FLOORS[layer_count][tier] -> flat floor dict. Layer count is bucketed to
# 2 (1-2 layer) vs 4 (multilayer). 'standard' preserves the historical floors so a
# bare default run is unchanged; 'advanced' is the JLC tighter/more-costly tier and
# is also the rung 'standard' escalates to. 'pad_hole_to_hole' and the annular
# recommended/abs-min split are per the JLC spec.
#
# 'annular' here is the fab's RECOMMENDED ring and is enforced against NO via
# pair -- not these tables' (every rung would fail it: 4-layer standard ships
# (0.45-0.20)/2 = 0.125 against a declared 0.20) and not an override file's
# either, because the file's own reference table quotes these very numbers, so
# honouring them silently inflated the via the user had just asked for. The key
# is a DECLARATION to grade, and check_drc grades it. `_pin_via_ring` fixes only
# the structural case: a ring of zero or less.
_FAB_FLOORS = {
    2: {
        'standard': {'clearance': 0.127, 'track_width': 0.127,
                     'via_diameter': 0.45, 'via_drill': 0.20,
                     'hole_to_hole': 0.20, 'pad_hole_to_hole': 0.45,
                     'annular': 0.25, 'board_edge': 0.20},
        'advanced': {'clearance': 0.10, 'track_width': 0.10,
                     'via_diameter': 0.25, 'via_drill': 0.15,
                     'hole_to_hole': 0.20, 'pad_hole_to_hole': 0.45,
                     'annular': 0.18, 'board_edge': 0.20},
    },
    4: {
        'standard': {'clearance': 0.10, 'track_width': 0.0889,
                     'via_diameter': 0.45, 'via_drill': 0.20,
                     'hole_to_hole': 0.20, 'pad_hole_to_hole': 0.45,
                     'annular': 0.20, 'board_edge': 0.20},
        'advanced': {'clearance': 0.09, 'track_width': 0.0762,
                     'via_diameter': 0.25, 'via_drill': 0.15,
                     'hole_to_hole': 0.20, 'pad_hole_to_hole': 0.45,
                     'annular': 0.15, 'board_edge': 0.20},
    },
}

TIERS = ('standard', 'advanced')


# --- Process-wide selected tier ----------------------------------------------
# The active tier is a module-global so the dozens of deep ``fab_floors(n)`` call
# sites need not each thread a tier param. It is set once per run, near the start:
# each CLI calls ``set_default_fab_tier`` after arg parsing, and each in-process GUI
# routing action calls ``set_fab_tier_from_config`` at entry. There is no
# save/restore around an engine body — the global simply holds the last value set,
# so a caller that routes without first setting the tier inherits the previous run's
# value. The in-process GUI avoids one tab's custom file leaking into the next by
# re-setting the tier from its own config at the start of every routing action.
# NOTE: process-wide, not thread-local — engines run serially.
_DEFAULT_TIER = 'standard'
_DEFAULT_OVERRIDES = {}
_escalation_warned = set()
#: Every standard->advanced escalation this run performed, as
#: ``{'context': str}`` records. `warn_fab_escalation` printed to a log and
#: reached NOTHING else -- not a summary key, not the .kicad_pro, not a grader
#: -- so an escalation was "disclosed but not instrumented" and no automated
#: reader could see it. Run 22's board silently took 0.25/0.15 vias this way
#: while every checker read clean. Cleared per run by set_default_fab_tier,
#: alongside the dedupe set.
_escalation_events = []


def set_default_fab_tier(tier, overrides=None):
    """Set the process-wide active fab tier (and custom overrides). Resets the
    per-run escalation-warning dedupe so a new run warns afresh."""
    global _DEFAULT_TIER, _DEFAULT_OVERRIDES
    _DEFAULT_TIER = tier or 'standard'
    _DEFAULT_OVERRIDES = dict(overrides or {})
    _escalation_warned.clear()
    del _escalation_events[:]


def get_default_fab_tier():
    """Return the active ``(tier, overrides_dict)`` — pass back to
    ``set_default_fab_tier(*prev)`` to restore."""
    return (_DEFAULT_TIER, dict(_DEFAULT_OVERRIDES))


def _layer_floors(copper_layer_count):
    return _FAB_FLOORS[2] if (copper_layer_count or 2) <= 2 else _FAB_FLOORS[4]


# The via ring is a RELATION -- ring = (via_diameter - via_drill)/2 -- not a key,
# and nothing here validated it. Run 20 measured the cost: an override file
# declaring `via_diameter = 0.3` and `via_drill = 0.3` together produced a ladder
# rung whose ring is ZERO, net_rescue._escalation_ladder escalated onto it, and
# three vias shipped as holes with no barrel land that every grader called clean.
_RING_EPS = 1e-9

#: The pin target: the smallest ring any built-in tier actually ships. "ring > 0"
#: is the invariant, but pinning to a nanometre would satisfy it with a number no
#: fab can make, so the target is a value this repo already treats as achievable
#: (the advanced rung's own ring, 2- and 4-layer alike).
#:
#: Derived from the tables rather than written down, so it cannot drift out of
#: sync -- but `min()` derives it in the direction that ERODES it: adding a
#: tighter tier would silently lower the floor every zero-ring via is pinned to.
#: `_MIN_SHIPPED_RING_FLOOR` is the backstop, and the test asserts the derivation
#: against a recomputation rather than against a literal.
_MIN_SHIPPED_RING_FLOOR = 0.05
_MIN_SHIPPED_RING = max(_MIN_SHIPPED_RING_FLOOR, min(
    (f['via_diameter'] - f['via_drill']) / 2.0
    for _bylayer in _FAB_FLOORS.values() for f in _bylayer.values()
))


def _pin_via_ring(floor, where='', _warned=set()):
    """Raise ``via_diameter`` when the via ring is STRUCTURALLY impossible (<= 0).

    Structural only, and that scope was cut down after a verification pass. An
    earlier version also fired when the ring fell below an ``annular`` declared in
    the override file, which looked principled and was not:

      * `fab_overrides.example.txt` PRINTS the tiers' annular values as a
        reference table, so a user copying `annular = 0.15` onto the advanced
        tier moved its `via_diameter` from the 0.25 they had just asked for to
        0.45 -- LARGER than the standard tier, from a file requesting something
        tighter. A lone `annular = 0.20` line moved 4-layer standard 0.45 -> 0.60.
        Measured: 32 of 56 override combinations changed behaviour.
      * those tiers declare a *recommended* ring their own absolute-minimum via
        pairs do not meet (4L standard: (0.45-0.20)/2 = 0.125 vs a declared 0.20),
        which is exactly why this guard must not enforce that key against a via
        pair. Honouring it from a FILE re-entered the same trap by another door.

    So the declaration is graded, not silently satisfied: a ring below a declared
    floor is a finding for `check_drc`, where the number is reported and the user
    decides. Only "this via has no copper ring at all" is fixed here, because no
    fab makes one and no value of any other key redeems it.

    Clamp-and-continue matches ``enforce_fab_floors``' doctrine. Warns once per
    distinct (dia, drill, target) -- the ladder is rebuilt per parameter, per
    query and per net, and an undeduped warning printed 788 identical lines in
    one routing run, 46% of its output.
    """
    dia, drill = floor.get('via_diameter'), floor.get('via_drill')
    if dia is None or drill is None:
        return False
    ring = (dia - drill) / 2.0
    if ring > _RING_EPS:
        return False
    # Round like the neighbouring `fine` rung does: this value is persisted as a
    # floor and printed to users, and raw arithmetic produced 0.44999999999999996
    # -- one ULP below 0.45. This repo has been bitten by a one-ULP floor before.
    need = round(drill + 2.0 * _MIN_SHIPPED_RING, 4)
    if dia >= need - _RING_EPS:
        return False
    key = (round(dia, 6), round(drill, 6), need)
    if key not in _warned:
        _warned.add(key)
        print(f"WARNING: {where}via_diameter {dia:g} with via_drill {drill:g} leaves "
              f"an annular ring of {ring:g}mm -- a hole with no barrel land, which "
              f"no fab makes. Pinning via_diameter to {need:g}mm (the smallest ring "
              f"any built-in tier ships). Declare `annular` in the override file to "
              f"state a real limit; it is GRADED by check_drc, not silently applied "
              f"here.")
    floor['via_diameter'] = need
    return True


# --- The board's OWN declared fab floors (run 22) -----------------------------
#
# Run 22 routed a board declaring min_clearance 0.15 / min_track_width 0.15 /
# min_via_diameter 0.5 / min_via_drill 0.25. The router stepped BELOW those
# floors and the .kicad_pro writeback then relaxed the declaration to match, so
# the board reported `unrouted 0, broken 0` while carrying 39 objects under its
# own declared floors and every checker read clean. The declaration
# participated at exactly ONE point in the pipeline: as the baseline the
# writeback overwrote.
#
# THE AUTHORITY PROBLEM, and why the obvious rule is wrong. "A declaration that
# differs from KiCad's stock defaults was authored, so bind it" is disproved on
# this repo's own corpus (measured over kicad_files/, 2026-08-19):
#
#     33 boards; 18 have NO .kicad_pro at all -> binding is inert for them.
#     15 have one; 14 declare rules differing from stock.
#     BUT 10 of those 15 carry kicad_routing_tools.fab_floor_origin -- they are
#     tool OUTPUTS whose current rules block IS the relaxed writeback.
#     fanout_output1.kicad_pro declares via 0.3 / drill 0.2 / annular 0.05
#     while its own origin records 0.45 / 0.25 / 0.15.
#
# Binding that board's declaration would bind a number the router itself wrote
# -- a floor with no author, cementing the very ratchet this exists to stop. So
# the ORIGIN outranks the current rules: it is the pre-toolchain declaration.
#
# Only tigard and watchy are human-authored with no origin key, and only tigard
# carries `floor_provenance`, whose per-field map names the upstream
# s-expression each value came from -- the single piece of positive evidence in
# the tree that a number was authored rather than inherited. Its
# `deliberately_absent` map is the mirror: a field the author never declared,
# which must never be inferred from anywhere.

#: KiCad's stock design-rule defaults. A declaration equal to one of these is
#: evidence of nothing. Witness in-repo: kicad_files/flat_hierarchy.kicad_pro
#: carries exactly this table, so it is a value with a corpus witness rather
#: than a remembered constant.
_KICAD_STOCK_RULES = {
    'min_clearance': 0.2, 'min_track_width': 0.2, 'min_via_diameter': 0.5,
    'min_via_drill': 0.3, 'min_through_hole_diameter': 0.3,
    'min_via_annular_width': 0.1, 'min_hole_clearance': 0.25,
    'min_hole_to_hole': 0.25, 'min_copper_edge_clearance': 0.5,
}

#: rules key -> the FLOOR_KEYS name the ladder uses.
_RULE_TO_FLOOR_KEY = {
    'min_track_width': 'track_width',
    'min_via_diameter': 'via_diameter',
    'min_via_drill': 'via_drill',
}

#: Keys the ROUTE-TIME clamp may raise. `clearance` is NOT one, and that is the
#: most consequential judgement here:
#:
#:   plane_pad_tap._clearance_ladder computes floor = min(nominal, fab_floor)
#:   and collapses to a single rung when nominal <= floor. route.py sets
#:   args.clearance from the board's own Default netclass, and on tigard that
#:   netclass clearance (0.15) EQUALS rules.min_clearance (0.15) -- so binding
#:   clearance makes nominal == fab_floor, the ladder collapses, and the rescue
#:   loses its entire clearance neck-down. A large, predictable completion loss
#:   for the one floor this repo has twice documented as NOT a fab claim
#:   (GRADING_FLOOR_KEYS in fix_kicad_drc_settings; _FLOOR_SOURCES in list_nets,
#:   "an unreliable edit-floor -- 0.0 on the measured board").
#:
#: The WRITEBACK still holds min_clearance, which closes run 22's fourth
#: relaxation completely: the declaration is not rewritten, so every checker
#: keeps grading at 0.15 and sub-floor copper stays visible. "Do not rewrite my
#: declaration" and "never route below it" are different claims.
BOARD_FLOOR_KEYS = ('track_width', 'via_diameter', 'via_drill')

#: `annular` is deliberately NOT bindable. _pin_via_ring's own docstring
#: records that honouring a declared annular moved 32 of 56 override
#: combinations (advanced via 0.25 -> 0.45, 4L standard 0.45 -> 0.60) from a
#: file asking for something TIGHTER. It is a RELATION, graded by check_drc,
#: and binding it from a project is that same trap through another door.

BOARD_FLOOR_MODES = ('off', 'authored', 'all')

_DEFAULT_BOARD_FLOORS = {}      # {floor_key: value}, already authority-filtered
_DEFAULT_BOARD_SOURCES = {}     # {floor_key: 'board provenance' | ...}
_DEFAULT_BOARD_MODE = 'off'


def _read_project(pcb_path):
    """The sibling .kicad_pro as raw JSON, or {}.

    Read directly rather than through list_nets.read_design_rules: that helper
    flattens the netclass and the rules block into one shape, and the
    distinction between them is exactly what the authority rule turns on. It
    also keeps this module stdlib-only, a property it states at the top.
    """
    import json as _json
    base = os.path.splitext(pcb_path or '')[0]
    try:
        with open(base + '.kicad_pro', encoding='utf-8') as fh:
            return _json.load(fh)
    except (OSError, ValueError):
        return {}


def _resolve_declared(pcb_path, mode, rule_map):
    """The authority ladder, shared by the route-time binder and the
    writeback hold so the two can never disagree about what a board declared.
    """
    return _declared_impl(pcb_path, mode, rule_map)


def declared_fab_floors(pcb_path, mode='authored'):
    """The board's own fab floors, with the authority each one rests on.

    Returns ``(floors, sources)`` -- ``{floor_key: mm}`` and
    ``{floor_key: why}``. Empty when the board declares nothing bindable, which
    is the common case: 18 of 33 corpus boards have no project file at all.

    Precedence per key, highest authority first:

      1. `floor_provenance.deliberately_absent` names it -> NEVER bind, in any
         mode. A field the author explicitly did not declare must not be
         inferred from a netclass, a tier, or a seeded origin.
      2. `floor_provenance.fields` names it -> bind the value at that path.
         The only positive evidence that a number was authored.
      3. `fab_floor_origin[rule]` -> bind the ORIGIN, not the current rule. The
         current rule may be this toolchain's own ratchet (10 of 15 corpus
         projects), and the origin is the pre-toolchain declaration.
      4. `design_settings.rules[rule]`, positive and NOT stock-equal.
      5. mode 'all' only: the Default netclass, then a stock-equal rule.
      6. otherwise unset.
    """
    return _declared_impl(pcb_path, mode, _RULE_TO_FLOOR_KEY)


def _declared_impl(pcb_path, mode, rule_map):
    if mode == 'off':
        return {}, {}
    proj = _read_project(pcb_path)
    if not proj:
        return {}, {}
    krt = proj.get('kicad_routing_tools') or {}
    prov = krt.get('floor_provenance') or {}
    fields = prov.get('fields') or {}
    absent = prov.get('deliberately_absent') or {}
    origin = krt.get('fab_floor_origin') or {}
    rules = (((proj.get('board') or {}).get('design_settings') or {})
             .get('rules') or {})
    default_class = {}
    for c in ((proj.get('net_settings') or {}).get('classes') or []):
        if isinstance(c, dict) and c.get('name') == 'Default':
            default_class = c
            break

    def _num(v):
        return float(v) if isinstance(v, (int, float)) and v > 0 else None

    floors, sources = {}, {}
    for rule, key in rule_map.items():
        rule_path = 'board.design_settings.rules.' + rule
        class_path = 'net_settings.classes[Default].' + key
        if rule_path in absent or class_path in absent:
            sources[key] = 'deliberately absent'
            continue
        v = why = None
        if rule_path in fields:
            v, why = _num(rules.get(rule)), 'board provenance'
        if v is None and class_path in fields:
            v, why = _num(default_class.get(key)), 'board provenance'
        if v is None and rule in origin:
            v, why = _num(origin.get(rule)), 'fab_floor_origin'
        if v is None:
            rv = _num(rules.get(rule))
            if rv is not None and rv != _KICAD_STOCK_RULES.get(rule):
                v, why = rv, 'board rules'
        if v is None and mode == 'all':
            cv = _num(default_class.get(key))
            if cv is not None:
                v, why = cv, 'board netclass'
            else:
                rv = _num(rules.get(rule))
                if rv is not None:
                    v, why = rv, 'board rules (stock, mode=all)'
        if v is not None:
            floors[key] = v
            sources[key] = why
    return floors, sources


#: Rules the WRITEBACK may be held at, keyed by rule name. Wider than
#: BOARD_FLOOR_KEYS by exactly one: `min_clearance`.
#:
#: The asymmetry is the point. Binding clearance at ROUTE time collapses the
#: rescue's clearance ladder (see BOARD_FLOOR_KEYS), so it is not bound there.
#: But refusing to REWRITE the declaration costs nothing and closes run 22's
#: fourth relaxation completely: the project keeps saying 0.15, so check_drc,
#: board_score and KiCad all keep grading at 0.15 and any 0.125 copper stays
#: visible instead of being graded against a rewritten rule.
#:
#: "Do not rewrite my declaration" and "never route below it" are different
#: claims, and this repo already splits them along this exact line.
_HOLD_RULE_KEYS = {
    'min_track_width': 'track_width',
    'min_via_diameter': 'via_diameter',
    'min_via_drill': 'via_drill',
    'min_clearance': 'clearance',
}


def declared_writeback_hold(pcb_path, mode='authored'):
    """Rule floors the writeback may not lower, as ``{rule_key: mm}``.

    Same authority precedence as :func:`declared_fab_floors` -- provenance,
    then the pre-toolchain origin, then a non-stock rules value -- so a project
    whose current rules block is this toolchain's own ratchet is held at what
    it declared BEFORE the ratchet, not at the ratchet.

    Deliberately NOT held: `min_through_hole_diameter` (it spans PADS, and a
    0.25 pad drill legitimately sits below a via floor) and
    `min_via_annular_width` (a relation, graded by check_drc).
    """
    if mode == 'off':
        return {}
    floors, _ = _resolve_declared(pcb_path, mode, _HOLD_RULE_KEYS)
    out = {}
    for rule, key in _HOLD_RULE_KEYS.items():
        if key in floors:
            out[rule] = floors[key]
    return out

def set_board_floors(floors=None, sources=None, mode='off'):
    """Set the process-wide board-declared floor clamp.

    Rides the same mechanism as the tier (see the doctrine above
    ``set_default_fab_tier``): set once per run at the CLI/GUI entry point,
    never derived inside an engine. Deriving it from `pcb_data` down in the
    engines would reach every synthetic test fixture and would give the GUI and
    the CLI two different answers for the same board.
    """
    global _DEFAULT_BOARD_FLOORS, _DEFAULT_BOARD_SOURCES, _DEFAULT_BOARD_MODE
    _DEFAULT_BOARD_FLOORS = dict(floors or {})
    _DEFAULT_BOARD_SOURCES = dict(sources or {})
    _DEFAULT_BOARD_MODE = mode or 'off'
    del _board_floor_blocks[:]
    _board_floor_block_keys.clear()
    del _board_floor_costs[:]


def get_board_floors():
    """``(floors, sources, mode)`` -- the active clamp."""
    return (dict(_DEFAULT_BOARD_FLOORS), dict(_DEFAULT_BOARD_SOURCES),
            _DEFAULT_BOARD_MODE)


#: Ladder rungs the clamp removed that WOULD have been an escalation. Keeps
#: fab_escalations() accountable across the change: on a board whose floor sits
#: at or above rung 0, every rung collapses and no escalation is recorded --
#: because none happened. That is honest, but the information has to go
#: somewhere, and this is where.
_board_floor_blocks = []
_board_floor_block_keys = set()


#: Nets whose rescue/escalation ladder was EMPTY while a board floor was
#: bound. The flip commit's headline number: a floor that removes a net's last
#: recovery rung is a real completion cost, and a run that simply reports the
#: net failed has not told anyone why.
_board_floor_costs = []


def note_board_floor_cost(net_id, stage, detail=None):
    """Record that a ladder came back empty under an active board floor."""
    _board_floor_costs.append({'net_id': net_id, 'stage': stage,
                               'detail': dict(detail or {})})


def board_floor_costs():
    """Ladders the board floor emptied, as records."""
    return [dict(c) for c in _board_floor_costs]


def board_floor_blocks():
    """Rungs the board-floor clamp removed, as records."""
    return [dict(b) for b in _board_floor_blocks]


def _clamp_rungs(rungs, copper_layer_count):
    """Raise every rung to the board's declared floors; keep the ladder sane.

    Identity when nothing is bound -- the same list object -- which is the
    `off`-mode guarantee and what keeps every existing ladder byte-identical.
    """
    if not _DEFAULT_BOARD_FLOORS:
        return rungs
    src = ','.join(sorted(set(_DEFAULT_BOARD_SOURCES.values()))) or 'board'
    # What rung 0 becomes after clamping -- the yardstick warn_fab_escalation
    # will actually use.
    clamped_rung0 = max(rungs[0].get('via_diameter', 0.0),
                        _DEFAULT_BOARD_FLOORS.get('via_diameter', 0.0))
    out, seen = [], set()
    for f in rungs:
        g = dict(f)
        for k, v in _DEFAULT_BOARD_FLOORS.items():
            if k in g and v > g[k]:
                g[k] = v
        # MANDATORY per rung. _pin_via_ring fires only on a structurally
        # impossible ring and is called at just two sites today, NEITHER on the
        # escalation-rung path -- so a board declaring only min_via_drill 0.25,
        # clamped onto the advanced rung (via_diameter 0.25), lands a ZERO
        # annular ring: a hole with no land. That is the run-20 defect arrived
        # at through a new door.
        _pin_via_ring(g, where='board-declared floor (' + src + '): ')
        # ACCOUNTABILITY. A rung that WAS an escalation (a via smaller than
        # rung 0's) and no longer is, because the clamp raised it, is an
        # escalation that will not happen. warn_fab_escalation compares against
        # ladder[0] and so will correctly stay silent -- which is honest, but
        # the information has to go somewhere or the run looks like it simply
        # never needed the cheaper tier.
        was_escalation = (f.get('via_diameter', 0.0)
                          < rungs[0].get('via_diameter', 0.0) - _RING_EPS)
        still_escalation = (g.get('via_diameter', 0.0)
                            < clamped_rung0 - _RING_EPS)
        if was_escalation and not still_escalation:
            # DEDUPED. fab_floor_ladder is called on every rescue attempt and
            # every tap, so an undeduped counter reported 5454 "prevented
            # escalations" on one board -- a number that describes how often
            # the ladder was asked, not what the floor did. Same reason
            # _escalation_warned dedupes its warning: a disclosure nobody can
            # read is not a disclosure.
            rec = {'from': {k: f.get(k) for k in ('via_diameter', 'via_drill',
                                                  'track_width')},
                   'to': {k: g.get(k) for k in ('via_diameter', 'via_drill',
                                                'track_width')},
                   'reason': 'raised out of escalation range by the board floor'}
            _key = (tuple(sorted(rec['from'].items())),
                    tuple(sorted(rec['to'].items())))
            if _key not in _board_floor_block_keys:
                _board_floor_block_keys.add(_key)
                _board_floor_blocks.append(rec)
        key = tuple(round(g.get(k, 0.0), 6) for k in FLOOR_KEYS)
        if key in seen:
            # Collapsed exactly onto an earlier rung: dropping it is required,
            # not cosmetic. Identical numbers would make warn_fab_escalation
            # report an escalation that did not happen.
            continue
        seen.add(key)
        out.append(g)
    return out or [dict(rungs[0])]


def fab_floor_ladder(copper_layer_count, tier=None, overrides=None):
    """Ordered list of floor dicts for the tier: the nominal (preferred) floor
    first, then any escalation rungs (smaller). Routing tries them in order.

      standard           -> [standard, advanced]   (escalates with a warning)
      advanced           -> [advanced]             (hard floor)
      <tier> + overrides -> [<tier> with the file's keys overlaid]  (hard, no escalation)

    Supplying an override file collapses the ladder to one hard rung built from the
    selected base tier, since the file states the user's exact fab limits.
    ``tier=None`` uses the process-wide default set by ``set_default_fab_tier``.
    """
    if tier is None:
        tier = _DEFAULT_TIER
        if overrides is None:
            overrides = _DEFAULT_OVERRIDES
    base = _layer_floors(copper_layer_count)
    if tier not in base:
        raise ValueError(f"unknown fab tier {tier!r} (expected one of {TIERS})")
    if overrides:
        floor = dict(base[tier])
        floor.update({k: v for k, v in overrides.items() if k in floor})
        # Guard the RELATION, not just the keys. The merged floor can pair an
        # override's via_drill with the tier's via_diameter (or vice versa) and
        # land on a ring the user never inspected, so this runs on every
        # override path -- not only when both keys came from the file.
        _pin_via_ring(floor, where='--fab-overrides (merged with the '
                                   f'{tier} tier): ')
        # An explicit override key WINS over the board declaration for that
        # key: a file is a typed statement about the fab, a declaration is an
        # inference about the design. _clamp_rungs only raises keys the board
        # bound, so a file that states them keeps its own numbers.
        return _clamp_rungs([floor], copper_layer_count)
    if tier == 'standard':
        std = dict(base['standard'])
        adv = dict(base['advanced'])
        rungs = [std]
        # Intermediate fan-out / via-in-pad escape rung: the 0.30/0.15 "fine" via
        # the router used pre-#237. Multilayer boards try it before escalating to
        # the advanced 0.25/0.15, so fine-pitch escapes that fit a 0.30 via keep
        # their previous result instead of jumping straight to the smaller (more
        # costly) advanced via. (2-layer had no smaller-than-standard fine via, and
        # the rung is only added when 0.30 sits strictly between the two floors.)
        # Only the via dia/drill differ from standard; this is NOT the ladder's
        # first rung (fab_floors -> nominal) nor its last (fab_floor_min -> DRC).
        if (copper_layer_count or 2) > 2 and adv['via_diameter'] < 0.30 < std['via_diameter']:
            fine = dict(std)
            fine.update({'via_diameter': 0.30, 'via_drill': 0.15,
                         'annular': round((0.30 - 0.15) / 2.0, 4)})
            rungs.append(fine)
        rungs.append(adv)
        return _clamp_rungs(rungs, copper_layer_count)
    return _clamp_rungs([dict(base['advanced'])], copper_layer_count)


def fab_floors(copper_layer_count, tier=None, overrides=None):
    """The NOMINAL (preferred) fab floor for the tier — what routing targets and
    necks down to first. Flat dict of FLOOR_KEYS."""
    return fab_floor_ladder(copper_layer_count, tier, overrides)[0]


def fab_floor_min(copper_layer_count, tier=None, overrides=None):
    """The DEEPEST fab floor the tier can reach (the escalation rung for
    ``standard``; the hard floor for ``advanced``/``custom``). Use this to grade
    DRC, so legitimately-escalated fine geometry isn't false-flagged."""
    return fab_floor_ladder(copper_layer_count, tier, overrides)[-1]


# Routing-parameter name (CLI flag / GUI control) -> fab floor dict key. Used to
# stop a track/clearance/via/drill/hole param being set below the fab can make.
_PARAM_FLOOR_KEY = {
    'track_width': 'track_width',
    # The plane-repair strap NECK floor (--min-track-width) is still copper the
    # fab must etch, so it floors at the same track minimum (#513 item 9:
    # allwinner_h3_ddr3 shipped 217 GND straps necked to 0.0889 on a 2-layer
    # board because only --track-width was enforced).
    'min_track_width': 'track_width',
    'clearance': 'clearance',
    'via_size': 'via_diameter',
    'via_diameter': 'via_diameter',
    'via_drill': 'via_drill',
    'hole_to_hole_clearance': 'hole_to_hole',
    'hole_to_hole': 'hole_to_hole',
    # Copper-to-board-edge: JLC routed-outline min 0.2 mm. A board declaring a
    # smaller (or 0.0) min_copper_edge_clearance is pinned up so routed copper does
    # not run to the milled edge (#439 follow-up).
    'board_edge_clearance': 'board_edge',
    'board_edge': 'board_edge',
    # The diff-pair P/N gap is copper-to-copper spacing, so it floors at the same
    # copper-clearance minimum (parity with the GUI, which floors it at 'clearance').
    'diff_pair_gap': 'clearance',
}


def fab_floor_for_param(param_name, copper_layer_count, tier=None, overrides=None):
    """The fab floor (deepest reachable value) for a routing parameter, or None if
    the parameter has no fab floor. Uses fab_floor_min so it's the smallest value
    the fab can actually make for the active tier."""
    key = _PARAM_FLOOR_KEY.get(param_name)
    if key is None:
        return None
    return fab_floor_min(copper_layer_count, tier, overrides).get(key)


def count_copper_layers_in_file(pcb_path):
    """Count copper layers in a .kicad_pcb (matches `(0 "F.Cu" signal)`-style layer
    defs, not pad layer lists). Returns 0 on any read error. Stdlib-only."""
    try:
        with open(pcb_path, encoding='utf-8') as f:
            return len(re.findall(r'\(\d+\s+"[^"]*\.Cu"', f.read())) or 0
    except OSError:
        return 0


def enforce_fab_floors(copper_layer_count, tier=None, overrides=None, **params):
    """CLI guard: pin any routing parameter that is below the fab floor UP to the
    floor, warn, and keep running (issue #237). The fab physically can't make
    sub-floor geometry, so rather than abort the run we clamp each out-of-range
    value to the smallest the selected --fab-tier can make and print a warning.

    Each CLI passes the params it accepts (track_width, clearance, via_size,
    via_drill, hole_to_hole_clearance); None values skip. Returns a
    ``{param_name: pinned_floor}`` dict of the clamps applied (empty if all in
    range) so the caller can write the pinned values back onto its parsed args."""
    viols = check_param_floors(copper_layer_count, tier, overrides, **params)
    pinned = {}
    for name, val, floor in viols:
        print(f"  WARNING: --{name.replace('_', '-')} {val} is below the fab floor {floor} "
              f"for the selected --fab-tier; pinning up to {floor} (the fab can't "
              f"make it smaller). Pass --fab-overrides to declare a smaller fab "
              f"capability, or raise the value to silence this.")
        pinned[name] = floor
    return pinned


def check_param_floors(copper_layer_count, tier=None, overrides=None, **params):
    """Return a list of (name, value, floor) for any param below its fab floor.
    Params whose value is None or which have no fab floor are skipped."""
    viols = []
    for name, val in params.items():
        if val is None:
            continue
        floor = fab_floor_for_param(name, copper_layer_count, tier, overrides)
        if floor is not None and val < floor - 1e-9:
            viols.append((name, val, floor))
    return viols


_escalation_lever_said = []


def warn_fab_escalation(context):
    """Emit a one-line warning (deduped per run, per context) that a routing step
    dropped below the standard floor to the more-costly advanced floor."""
    if not context or context in _escalation_warned:
        return
    _escalation_warned.add(context)
    _escalation_events.append({'context': context,
                               'from': 'standard', 'to': 'advanced'})
    print(f"  WARNING: {context}: escalated standard->advanced fab floor "
          f"(0.25/0.15 via etc., more costly to fab); pass --fab-tier advanced to "
          f"silence, or --fab-overrides to pin your own floor (forbids escalation)")
    if not _escalation_lever_said:
        _escalation_lever_said.append(True)
        print("           NOTE: --via-size cannot prevent this. The via is "
              "re-derived from min(pad.size_x, pad.size_y) floored at the fab "
              "ladder, so RAISING --via-size makes the clamp fire more "
              "readily, never less. --fab-overrides collapses the ladder to a "
              "single rung and is the only flag that forbids the escalation.")


def fab_escalations():
    """Escalations performed since the last ``set_default_fab_tier``.

    Exists so a SUMMARY can carry what only a log line used to: an escalation
    means the board now needs a more costly fab process than the one it was
    asked for, and a run that reports `unrouted 0` while having quietly taken
    0.25/0.15 vias has not told you that. Report it; do not gate on it --
    it is a cost disclosure, not a defect.
    """
    return [dict(e) for e in _escalation_events]


# --- Override file + argparse helpers ----------------------------------------

def parse_fab_overrides(path):
    """Parse a human-editable fab-floor override file into a {key: float} dict.

    Lines are ``key = value`` / ``key: value`` / ``key value``; ``#`` starts a
    comment; blank lines ignored. Unknown keys, non-numeric or non-positive values
    are warned and skipped.
    """
    overrides = {}
    with open(path, encoding='utf-8') as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            parts = re.split(r'\s*[=:]\s*|\s+', line, maxsplit=1)
            if len(parts) != 2:
                print(f"WARNING: fab-overrides {path}:{lineno}: cannot parse "
                      f"{raw.strip()!r}")
                continue
            key, val = parts[0], parts[1]
            if key not in FLOOR_KEYS:
                print(f"WARNING: fab-overrides {path}:{lineno}: unknown key {key!r} "
                      f"(known: {', '.join(FLOOR_KEYS)})")
                continue
            try:
                fval = float(val)
            except ValueError:
                print(f"WARNING: fab-overrides {path}:{lineno}: {val!r} is not a number")
                continue
            if fval <= 0:
                print(f"WARNING: fab-overrides {path}:{lineno}: {key} must be > 0 "
                      f"(got {fval})")
                continue
            overrides[key] = fval
    # Report the relation at the point the user can act on it -- the file and its
    # line numbers are in hand here, and they are not in fab_floor_ladder. Only
    # pin when the file itself supplied BOTH via keys; a lone via_drill is
    # completed by the tier and is guarded there instead.
    if 'via_diameter' in overrides and 'via_drill' in overrides:
        _pin_via_ring(overrides, where=f'{path}: ')
    return overrides


def add_fab_tier_args(parser):
    """Add ``--fab-tier`` / ``--fab-overrides`` to an argparse parser. Shared by
    every routing/DRC CLI so the flag is identical everywhere."""
    parser.add_argument(
        '--fab-tier', choices=list(TIERS), default='standard',
        help="JLC fab capability floor (default standard). 'standard' = cheap "
             "no-extra-cost floor that auto-escalates to advanced (with a warning) "
             "when a fine-pitch fan-out needs it; 'advanced' = tight 0.25/0.15 via "
             "etc. (more costly), a hard floor.")
    parser.add_argument(
        '--fab-overrides', metavar='FILE', default=None,
        help="Path to a fab-floor override file (key=value lines, e.g. "
             "'via_drill = 0.15') overlaying the selected --fab-tier; only the "
             "listed values are replaced. Supplying it disables escalation (the "
             "floor becomes exactly the file + base tier). See the template "
             "fab_overrides.example.txt for the format and every key.")
    return parser


def add_board_floor_args(parser):
    """Add ``--board-floors`` -- ROUTE-TIME CLIs only.

    Deliberately NOT part of add_fab_tier_args, which check_drc.py and
    list_nets.py also call. Those two GRADE, and raising a grading floor makes
    them flag the author's own pre-existing copper -- the phantom-violation
    storm this repo has measured twice. They must not bind, so they must not
    advertise the flag either: an accepted-but-ignored flag is the same class
    of lie this whole change is removing.
    """
    parser.add_argument(
        '--board-floors', choices=list(BOARD_FLOOR_MODES),
        default='authored',
        help="Bind the BOARD'S OWN declared fab floors (min_track_width / "
             "min_via_diameter / min_via_drill) so the router may not emit "
             "copper under them. 'off' (default) = today's behaviour, the "
             "declaration is only a writeback baseline; 'authored' = bind a "
             "declaration backed by floor_provenance, by fab_floor_origin, or "
             "differing from KiCad's stock defaults; 'all' = also bind stock "
             "values and the Default netclass. min_clearance is never bound at "
             "route time (it collapses the rescue clearance ladder) -- the "
             "writeback holds it instead.")
    return parser


def set_fab_tier_from_config(config):
    """GUI helper: set the process-wide fab tier from a config / shared-params dict
    carrying 'fab_tier' and (optionally) 'fab_overrides_path'. Tolerates a missing
    or unreadable override file (warns, falls back to the bare tier)."""
    tier = (config.get('fab_tier') or 'standard')
    path = (config.get('fab_overrides_path') or '').strip()
    overrides = {}
    if path:
        try:
            overrides = parse_fab_overrides(path)
        except OSError as exc:
            print(f"WARNING: could not read fab overrides {path}: {exc}")
    set_default_fab_tier(tier, overrides)
    # The board-declared clamp rides the same call, so extending THIS function
    # reaches all five GUI entry points (swig_gui, fanout_gui x2,
    # differential_gui, planes_gui) with no new call sites -- the same property
    # that makes the tier itself GUI-safe.
    #
    # `board_floors` defaults to 'off', so a config that predates this key --
    # every saved setting today -- behaves exactly as before. A GUI that wants
    # to bind must pass BOTH the mode and the board path; without a path there
    # is nothing to read a declaration from, and inventing one is the failure
    # this whole change removes.
    mode = (config.get('board_floors') or 'off')
    pcb = (config.get('board_path') or config.get('input_file') or '')
    if mode != 'off' and pcb:
        floors, sources = declared_fab_floors(pcb, mode)
        set_board_floors(floors, sources, mode)
    else:
        set_board_floors(None, None, 'off')


def fab_tier_from_args(args):
    """Resolve ``(tier, overrides_dict)`` from parsed args; load the override file
    once. The override file (if any) overlays whichever tier was selected."""
    tier = getattr(args, 'fab_tier', 'standard') or 'standard'
    path = getattr(args, 'fab_overrides', None)
    if path and not os.path.isfile(path):
        raise SystemExit(f"error: --fab-overrides file not found: {path}")
    overrides = parse_fab_overrides(path) if path else {}
    return tier, overrides


def bind_board_fab_floors(args, pcb_path, announce=True):
    """Resolve and install the board's own declared floors. Returns the mode.

    Call ONCE per run at a route-time CLI entry point, right after
    ``set_default_fab_tier`` -- never from inside an engine. GRADING tools
    (check_drc, list_nets) deliberately do NOT call this: raising their floor
    would flag the AUTHOR'S OWN pre-existing copper and re-manufacture the
    phantom-violation storm this repo has measured twice.
    """
    mode = getattr(args, 'board_floors', 'off') or 'off'
    if mode == 'off' or not pcb_path:
        set_board_floors(None, None, 'off')
        return 'off'
    floors, sources = declared_fab_floors(pcb_path, mode)
    set_board_floors(floors, sources, mode)
    if announce:
        if floors:
            print('  board floors BOUND (--board-floors %s): %s' % (
                mode, ', '.join(
                    '%s %g [%s]' % (k, v, sources.get(k, '?'))
                    for k, v in sorted(floors.items()))))
        else:
            print('  --board-floors %s: this board declares no bindable '
                  'floor; nothing bound.' % mode)
    return mode
