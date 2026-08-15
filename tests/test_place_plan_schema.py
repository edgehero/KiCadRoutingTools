#!/usr/bin/env python3
"""The placement plan schema: every op round-trips, and every refusal NAMES
what it refused.

The second half is the load-bearing one. A placement plan whose op was
silently dropped produces a DIFFERENT PLACEMENT and reports success -- the
exact failure `manifest_to_plan.REFUSED_TOOLS` exists to prevent on the
routing side ("the unknown-tool path only bumps a `skipped` counter -- a
number, not a name -- so the converted plan looks complete when it is not").
So each negative case here asserts the offending key or value appears in the
error text, not merely that some error was raised.

The positive case is the urchin plan: the arrangement `wk/run19/urchin/
arrange.py` wrote as 221 lines of arithmetic, said as ops. If this stops
validating, the vocabulary has drifted away from the thing it exists to
express.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)
        sys.path.insert(0, os.path.join(p, 'py_router'))
        sys.path.insert(0, os.path.join(p, 'py_tools'))
        sys.path.insert(0, os.path.join(p, 'py_placer'))

from placement.plan_ops import (PLACEMENT_ACTIONS, PLACEMENT_PLAN_SCHEMA,
                                format_errors, parse_placement_plan,
                                parse_ref_selector, validate_ops)

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


def refuses(name, steps, *needles):
    """The plan is refused AND the message names each needle."""
    ops, errors = parse_placement_plan({'schema': 1, 'steps': steps})
    if ops is not None:
        check(name, False, "accepted a plan that should have been refused")
        return
    text = '\n'.join(errors)
    missing = [n for n in needles if n not in text]
    check(name, not missing,
          f"error text names none of {missing}: {text!r}" if missing else "")


# --------------------------------------------------------------------------
# The urchin plan -- arrange.py, said instead of computed.
# --------------------------------------------------------------------------
URCHIN = {
    "schema": 1,
    "steps": [
        # The two-hop electrical join: a switch carries COL<n> (R_ prefix =
        # right half); its diode carries ROW<n>; the two share an
        # auto-generated private net. arrange.py:41-72.
        {"action": "place_index", "name": "diode",
         "select": r"^D\d+$",
         "fields": {"row": {"pattern": r"^(R_)?ROW(\d)$", "group": 2,
                            "as": "int"}}},
        {"action": "place_index", "name": "switch",
         "select": r"^SW\d+$",
         "fields": {"col": {"pattern": r"^(R_)?COL(\d)$", "group": 2,
                            "as": "int"},
                    "half": {"pattern": r"^(R_)?COL(\d)$", "group": 1,
                             "as": "str", "map": {"R_": "R", "": "L"}}},
         "partner": {"index": "diode", "pattern": r"^Net-\(",
                     "inherit": ["row"], "as": "partner"}},

        {"action": "place_at", "ref": "U1", "at": [28.0, 60.0], "within": 5.0},
        {"action": "place_at", "ref": "Display1", "at": [30.0, 61.5],
         "within": 8.0},

        # The 5x3 matrix. The per-column y0 is PROBED against the real
        # outline, with the diode strip's own rect kept legal too
        # (arrange.py:85-103), instead of the solved constants
        # {34.0, 28.5, 25.5, 30.0, 39.5} being typed in.
        {"action": "place_array", "refs": "index:switch",
         "pitch": [17.0, 17.0],
         "origin": {"x": 46.0,
                    "y": {"solve": "outline_probe", "from": 24.0,
                          "step": 0.5, "limit": 48,
                          "also": [{"offset": [0.0, 8.5],
                                    "extent": [6.8, 2.0]}]}},
         "index_x": "col", "index_y": "row",
         "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
         "where": {"row": {"lt": 3}},
         "order": ["half", "col", "row"], "within": 2.5},

        # Row 3 is not a row: it is the thumb class, and its two pockets are
        # named coordinates. Per half the higher column takes the inner slot.
        {"action": "place_slots", "refs": "index:switch",
         "slots": [[78.0, 79.5], [95.5, 82.0]],
         "mirror": {"axis": "board:xmid", "when": {"half": {"eq": "R"}}},
         "where": {"row": {"eq": 3}},
         "group_by": ["half"], "order": ["col"], "within": 9.0},

        # The diode follows its switch's RESOLVED pose, not its target.
        {"action": "place_relative", "refs": "index:diode",
         "of": "index:switch", "pair_by": "partner",
         "offset": [0.0, 8.5], "rot": 90, "within": 4.0},

        {"action": "place_lift", "refs": ["D14", "D31"],
         "for": ["SW17", "SW34"], "restore": True},
    ],
}

ops, errors = parse_placement_plan(URCHIN)
check("urchin plan validates", ops is not None, format_errors(errors))
check("urchin plan keeps every op",
      ops is not None and len(ops) == len(URCHIN['steps']),
      f"{len(ops) if ops else 0} of {len(URCHIN['steps'])}")
check("urchin plan round-trips through JSON",
      parse_placement_plan(json.dumps(URCHIN))[0] is not None)

# --------------------------------------------------------------------------
# Every action is reachable, and the prompt schema advertises all of them.
# --------------------------------------------------------------------------
MINIMAL = {
    'place_index': {"action": "place_index", "name": "i", "select": "^R"},
    'place_keepout': {"action": "place_keepout", "rect": [0, 0, 1, 1]},
    'place_at': {"action": "place_at", "ref": "U1", "at": [1, 2]},
    'place_array': {"action": "place_array", "refs": ["R*"], "pitch": [1, 1],
                    "origin": {"x": 0, "y": 0}},
    'place_slots': {"action": "place_slots", "refs": ["R*"],
                    "slots": [[1, 1]]},
    'place_relative': {"action": "place_relative", "refs": ["D*"],
                       "of": ["SW*"], "offset": [0, 1]},
    'place_edge': {"action": "place_edge", "refs": ["J1"], "edge": "north"},
    'place_pack': {"action": "place_pack", "refs": ["R*"],
                   "zone": [0, 0, 10, 10]},
    'place_lift': {"action": "place_lift", "refs": ["D1"]},
    'place_repair': {"action": "place_repair"},
    'place_polish': {"action": "place_polish"},
    'place_lock': {"action": "place_lock", "refs": ["MH*"]},
}
check("every action has a minimal form",
      sorted(MINIMAL) == sorted(PLACEMENT_ACTIONS),
      f"{sorted(set(PLACEMENT_ACTIONS) ^ set(MINIMAL))}")
from placement.plan_ops import UNIMPLEMENTED_ACTIONS as _UNIMPL
for act, step in sorted(MINIMAL.items()):
    if act in _UNIMPL:
        continue          # asserted to REFUSE, further down
    o, e = parse_placement_plan({'schema': 1, 'steps': [step]})
    check(f"minimal {act}", o is not None, format_errors(e))
missing_in_prompt = [a for a in PLACEMENT_ACTIONS
                     if f'"{a}"' not in PLACEMENT_PLAN_SCHEMA]
check("prompt schema advertises every action", not missing_in_prompt,
      f"absent: {missing_in_prompt}")

# --------------------------------------------------------------------------
# Refusals, each naming what it refused.
# --------------------------------------------------------------------------
refuses("unknown action is named",
        [{"action": "place_everything", "refs": ["R1"]}],
        "place_everything", "unknown action")

# --------------------------------------------------------------------------
# The contract must not advertise what it refuses, and must not validate a
# key nothing reads. Both shipped: the schema offered `place_keepout` (the
# first op in its own canonical example) while the resolver refused the whole
# plan for it, and `clearance` was a validated key on five ops that no code
# path ever read -- the exact silent-ignore this module exists to prevent.
# --------------------------------------------------------------------------
import inspect

from placement import plan_resolve
from placement.plan_ops import UNIMPLEMENTED_ACTIONS, _OP_FIELDS

check("the resolver's action list is DERIVED from the validator's",
      set(plan_resolve.RESOLVED_ACTIONS)
      == set(PLACEMENT_ACTIONS) - set(UNIMPLEMENTED_ACTIONS),
      str(sorted(set(plan_resolve.RESOLVED_ACTIONS)
                 ^ (set(PLACEMENT_ACTIONS) - set(UNIMPLEMENTED_ACTIONS)))))
for act in UNIMPLEMENTED_ACTIONS:
    minimal = dict(MINIMAL[act])
    o, e = parse_placement_plan({'schema': 1, 'steps': [minimal]})
    check(f"{act} is refused at VALIDATION, naming itself",
          o is None and any(act in x and 'no resolver' in x for x in e),
          str(e))
check("the prompt schema marks what is not implemented",
      all(a in PLACEMENT_PLAN_SCHEMA.split('NOT IMPLEMENTED YET')[-1]
          for a in UNIMPLEMENTED_ACTIONS),
      "an author reading the contract must not write an op that refuses")

_resolver_src = inspect.getsource(plan_resolve)
unread = []
for act, (req, opt) in sorted(_OP_FIELDS.items()):
    if act in UNIMPLEMENTED_ACTIONS:
        continue
    for key in list(req) + list(opt):
        if key in ('note', 'params'):
            continue          # carried for the reader / forwarded wholesale
        if f"'{key}'" not in _resolver_src:
            unread.append(f"{act}.{key}")
check("every validated key is read by the resolver", not unread,
      f"validated and never read: {unread}")

refuses("misspelled key is named, not ignored",
        [{"action": "place_array", "refs": ["R*"], "pich": 17.0,
          "origin": {"x": 0, "y": 0}}],
        "pich", "unknown key")

refuses("missing required key is named",
        [{"action": "place_array", "refs": ["R*"], "origin": {"x": 0, "y": 0}}],
        "pitch", "missing required key")

refuses("forward index reference is named",
        [{"action": "place_array", "refs": "index:switch", "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}}],
        "switch", "no earlier place_index")

refuses("index defined AFTER its use is still refused",
        [{"action": "place_at", "ref": "U1", "at": [0, 0]},
         {"action": "place_array", "refs": "index:sw", "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}},
         {"action": "place_index", "name": "sw", "select": "^SW"}],
        "sw", "no earlier place_index")

refuses("duplicate index name is named",
        [{"action": "place_index", "name": "sw", "select": "^SW"},
         {"action": "place_index", "name": "sw", "select": "^S"}],
        "sw", "already defined")

refuses("order on a field the index does not define",
        [{"action": "place_index", "name": "sw", "select": "^SW",
          "fields": {"col": {"pattern": r"^COL(\d)$", "as": "int"}}},
         {"action": "place_array", "refs": "index:sw", "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}, "order": ["rank"]}],
        "rank", "not defined by index")

refuses("where on a field the index does not define",
        [{"action": "place_index", "name": "sw", "select": "^SW",
          "fields": {"col": {"pattern": r"^COL(\d)$", "as": "int"}}},
         {"action": "place_array", "refs": "index:sw", "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}, "where": {"row": {"lt": 3}}}],
        "row", "not defined by index")

refuses("unknown where predicate is named",
        [{"action": "place_array", "refs": ["R*"], "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}, "where": {"row": {"below": 3}}}],
        "below", "unknown predicate")

refuses("unknown mirror axis is named",
        [{"action": "place_array", "refs": ["R*"], "pitch": [1, 1],
          "origin": {"x": 0, "y": 0}, "mirror": {"axis": "board:diagonal"}}],
        "board:diagonal", "unknown axis")

refuses("unknown solve is named",
        [{"action": "place_array", "refs": ["R*"], "pitch": [1, 1],
          "origin": {"x": 0, "y": "solve:vibes"}}],
        "solve:vibes", "unknown solve")

# place_pack is refused up front while it has no resolver, so its VALUE
# checks are unreachable through parse_placement_plan. Exercise them directly
# so they do not rot before the op lands.
import placement.plan_ops as _po
_saved_unimpl = _po.UNIMPLEMENTED_ACTIONS
_po.UNIMPLEMENTED_ACTIONS = tuple(a for a in _saved_unimpl
                                  if a != 'place_pack')
try:
    _errs = _po.validate_ops([{"action": "place_pack", "refs": ["R*"],
                               "zone": [0, 0, 1, 1], "policy": "spiral"}])
finally:
    _po.UNIMPLEMENTED_ACTIONS = _saved_unimpl
check("unknown pack policy is named (checked directly: op not live yet)",
      any('spiral' in x and 'unknown policy' in x for x in _errs), str(_errs))

refuses("unknown edge is named",
        [{"action": "place_edge", "refs": ["J1"], "edge": "up"}],
        "up", "unknown edge")

refuses("bad regex in select is named",
        [{"action": "place_index", "name": "sw", "select": "^SW(\\d"}],
        "select", "regex")

# Same as place_pack: place_keepout is refused up front, so its rect check
# is exercised directly rather than left to rot until the op lands.
_saved_unimpl = _po.UNIMPLEMENTED_ACTIONS
_po.UNIMPLEMENTED_ACTIONS = tuple(a for a in _saved_unimpl
                                  if a != 'place_keepout')
try:
    _errs = _po.validate_ops([{"action": "place_keepout",
                               "rect": [10, 10, 5, 5]}])
finally:
    _po.UNIMPLEMENTED_ACTIONS = _saved_unimpl
check("empty rect is refused (checked directly: op not live yet)",
      any('empty rect' in x for x in _errs), str(_errs))

refuses("pitch that is not two numbers",
        [{"action": "place_array", "refs": ["R*"], "pitch": 17.0,
          "origin": {"x": 0, "y": 0}}],
        "pitch", "two numbers")

refuses("zero pitch on both axes",
        [{"action": "place_array", "refs": ["R*"], "pitch": [0, 0],
          "origin": {"x": 0, "y": 0}}],
        "pitch")

refuses("negative within",
        [{"action": "place_at", "ref": "U1", "at": [0, 0], "within": -1.0}],
        "within")

refuses("partner inheriting a field the other index lacks",
        [{"action": "place_index", "name": "d", "select": "^D"},
         {"action": "place_index", "name": "sw", "select": "^SW",
          "partner": {"index": "d", "pattern": "^Net-", "inherit": ["row"]}}],
        "row", "defines no field")

refuses("no steps",
        [],
        "no steps")

o, e = parse_placement_plan("not json at all")
check("non-JSON is refused with the parser's reason",
      o is None and any('not valid JSON' in x for x in e), str(e))

o, e = parse_placement_plan({'schema': 99, 'steps': [MINIMAL['place_repair']]})
check("wrong schema version is named",
      o is None and any('99' in x for x in e), str(e))

# --------------------------------------------------------------------------
# ALL errors are reported, not just the first: an author fixing one at a time
# pays a round trip per mistake.
# --------------------------------------------------------------------------
o, e = parse_placement_plan({'schema': 1, 'steps': [
    {"action": "place_nothing"},
    {"action": "place_array", "refs": ["R*"], "pich": 1,
     "origin": {"x": 0, "y": 0}},
]})
check("multiple problems all reported", o is None and len(e) >= 3,
      f"{len(e)} error(s): {e}")

# --------------------------------------------------------------------------
# Ref selectors.
# --------------------------------------------------------------------------
check("selector: bare glob", parse_ref_selector("SW*") == ('list', ["SW*"]))
check("selector: list", parse_ref_selector(["A", "B"]) == ('list', ["A", "B"]))
check("selector: index", parse_ref_selector("index:sw") == ('index', "sw"))
check("selector: group",
      parse_ref_selector("group:sheet:1a2b") == ('group', "sheet:1a2b"))

# --------------------------------------------------------------------------
# format_errors says nothing was placed -- the refusal must not read as a
# partial success.
# --------------------------------------------------------------------------
text = format_errors(["step 1: unknown action 'x'"])
check("refusal states that nothing was placed",
      'REFUSED' in text and 'Nothing was placed' in text, text)
check("no errors formats to nothing", format_errors([]) == '')

# A plan with an error must not be executable even if a caller ignores the
# return value's None-ness and reaches for validate_ops directly.
check("validate_ops agrees with parse_placement_plan",
      bool(validate_ops([{"action": "nope"}])))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
