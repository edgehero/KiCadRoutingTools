"""The placement plan: what an AI writes instead of a per-board python script.

`ai_plan.KNOWN_ACTIONS` is six ROUTING verbs and no placement verb, and
`tests/stress/manifest_to_plan.py` records why -- "there is nothing to map TO:
the plan format has no placement step". So when run 19's seeder could not
produce a key field, the arrangement was written as arithmetic instead:
`wk/run19/urchin/arrange.py`, 221 lines, with PITCH = 17.0, X0 = 46.0 and
THUMB_SLOTS = [(78.0, 79.5), (95.5, 82.0)] baked in.

That script was not cheating -- it seated every pose through the engine's own
`seeder._try_place` gate, so legality stayed engine-verified and the geometry
layer was never the problem. What it lacked was any way to SAY what it said: a
pitch, a mirror axis, a per-column stagger solved against the outline, or "the
diode sits PITCH/2 below its switch". This module is that vocabulary.

The ops are deliberately the primitives that hand scripts across wk/run2..run19
actually reached for, not a general layout language:

    place_index      structure from NET NAMES -- COL(\\d)/ROW(\\d) -> column,
                     row, half, and the partner part found through a shared
                     auto-generated private net. arrange.py:41-72.
    place_at         one part at a coordinate, within a budget
    place_array      a lattice: pitch, origin, mirror, order
    place_slots      named irregular pockets, assigned by a rule
    place_relative   a child at an offset from its parent's RESOLVED pose
                     (arrange.py:182-184 -- the parent's real seat, not its
                     target, which is why this cannot be an array)
    place_edge       an edge connector in its overhang band
    place_pack       a set into a zone, by a stated policy
    place_lift       eviction WITH ORDERING -- run 19's one-call reseat failed
                     three times because it re-seated the blockers first
    place_keepout    reserve space DURING seeding (keepouts are graded today
                     and honoured by no seeding module)
    place_repair / place_polish / place_lock

Two divergences from `ai_plan.parse_plan_result`, both deliberate:

* **Any error is fatal here.** A routing plan whose step was dropped routes
  fewer nets and says so; a placement plan whose op was dropped produces a
  DIFFERENT PLACEMENT and nothing downstream can tell. So this returns
  (None, errors) rather than a filtered list.
* **An unrecognised op KEY is an error, not a note.** Routing params are
  advisory tab options and ignoring one is survivable. Here a key is
  structural: a misspelled `pitch` would silently place a lattice at spacing
  zero. `params` stays open, like routing's, because it forwards knobs.

Nothing here executes. Resolution is `plan_resolve.py`.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA_VERSION = 1

PLACEMENT_ACTIONS = (
    'place_index', 'place_keepout', 'place_fixed', 'place_at', 'place_array',
    'place_slots', 'place_relative', 'place_edge', 'place_pack', 'place_lift',
    'place_repair', 'place_polish', 'place_lock',
)

# Where a mirror axis may come from. `board:xmid` replaces arrange.py:28's
# hand-transcribed `MIRROR_X = 17.599913 + 239.1983` -- the sum of the board's
# own x bounds, typed in by a human who had read them off the file.
MIRROR_AXES = ('board:xmid', 'board:ymid')

# `place_pack` policies. `radial` is what the zone stage does today
# (seeder.py:516-552, members ordered by descending pin count, jittered around
# the zone centre) and is named so a plan can ask for the current behaviour
# explicitly; the others are new.
PACK_POLICIES = ('radial', 'rows', 'grid', 'ring')

EDGES = ('north', 'south', 'east', 'west')

# Ops whose SCHEMA is settled but whose resolver is not written yet. They are
# refused by name at validation rather than at resolve time, and the authoring
# contract below marks them, because the alternative is what shipped first: an
# AI reads the schema, writes the canonical plan (whose own first op is
# `place_keepout`), and has the WHOLE plan refused for using a documented key.
# `plan_resolve.RESOLVED_ACTIONS` is derived from this, so the two cannot drift.
UNIMPLEMENTED_ACTIONS = ('place_repair', 'place_polish')

# `where` filter predicates. Structured rather than a string expression: a
# parser for "row<3" is a second language to get wrong, and every filter these
# ops need is one comparison against one field.
WHERE_OPS = ('eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in')

# A field value extracted from a net name is one of these.
FIELD_TYPES = ('int', 'str')

_REF_SELECTOR = re.compile(r'^(index|group):(.+)$')


class PlanError(ValueError):
    """A placement plan that cannot be executed as written."""


# --------------------------------------------------------------------------
# op field specs: (required, optional). `params` is open everywhere it appears.
# --------------------------------------------------------------------------
_OP_FIELDS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    'place_index':    (('name', 'select'), ('fields', 'partner', 'note')),
    'place_keepout':  (('rect',), ('reason', 'sides', 'allow', 'note')),
    # A MECHANICAL FACT, not a request: set the pose, never search, never
    # move it, and treat it as an obstacle from then on.
    'place_fixed':    (('ref', 'at'), ('rot', 'note')),
    'place_at':       (('ref', 'at'),
                       ('rot', 'rot_prefer', 'within', 'mirror', 'note')),
    'place_array':    (('refs', 'pitch', 'origin'),
                       ('mirror', 'rot', 'rot_prefer', 'within', 'order',
                        'where', 'index_x', 'index_y', 'note')),
    'place_slots':    (('refs', 'slots'),
                       ('mirror', 'rot', 'rot_prefer', 'within', 'order',
                        'group_by', 'where', 'note')),
    'place_relative': (('refs', 'of', 'offset'),
                       ('pair_by', 'rot', 'rot_prefer', 'within', 'where',
                        'order', 'note')),
    'place_edge':     (('refs', 'edge'),
                       ('overhang', 'rot', 'order', 'note')),
    'place_pack':     (('refs', 'zone'),
                       ('policy', 'rot', 'within', 'order', 'where',
                        'tolerance', 'note')),
    'place_lift':     (('refs',),
                       ('for', 'restore', 'within', 'rot', 'note')),
    'place_repair':   ((), ('refs', 'caps', 'params', 'note')),
    'place_polish':   ((), ('refs', 'params', 'note')),
    'place_lock':     (('refs',), ('note',)),
}

# Sub-object field specs, same shape.
_INDEX_FIELD_FIELDS = (('pattern',), ('from', 'group', 'as', 'map'))
_PARTNER_FIELDS = (('index', 'pattern'), ('from', 'inherit', 'as'))
_ORIGIN_SOLVE_FIELDS = ((), ('from', 'step', 'limit', 'also', 'direction'))
_ALSO_FIELDS = (('offset', 'extent'), ())
_MIRROR_FIELDS = (('axis',), ('when',))


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _num_list(v, n: int) -> bool:
    return (isinstance(v, (list, tuple)) and len(v) == n
            and all(_is_num(x) for x in v))


def _str_list(v) -> bool:
    return isinstance(v, (list, tuple)) and all(isinstance(x, str) for x in v)


def _check_keys(where: str, obj: Dict, spec, errors: List[str],
                open_keys: Sequence[str] = ()) -> None:
    """Required present, and every key recognised.

    Naming an unrecognised key is the point: a plan that carries `pich: 17.0`
    and runs anyway has placed a lattice at spacing zero and reported success.
    """
    required, optional = spec
    known = set(required) | set(optional) | set(open_keys)
    for k in required:
        if obj.get(k) is None:
            errors.append(f"{where}: missing required key {k!r}")
    for k in sorted(obj):
        if k not in known and k != 'action':
            errors.append(
                f"{where}: unknown key {k!r} (known: "
                f"{', '.join(sorted(known))})")


def parse_ref_selector(value) -> Tuple[str, Any]:
    """('list', [globs]) | ('index', name) | ('group', key).

    Globs are fnmatch, the same syntax `--lock` and the intent's `refs` use.
    """
    if isinstance(value, str):
        m = _REF_SELECTOR.match(value)
        if m:
            return m.group(1), m.group(2)
        return 'list', [value]
    if _str_list(value):
        return 'list', list(value)
    raise PlanError(
        f"refs must be a glob, a list of globs, 'index:<name>' or "
        f"'group:<key>', got {value!r}")


def _check_refs(where: str, value, indexes: Dict[str, Dict],
                errors: List[str]) -> Optional[str]:
    """Validate a ref selector; return the index name when it names one."""
    try:
        kind, arg = parse_ref_selector(value)
    except PlanError as e:
        errors.append(f"{where}: {e}")
        return None
    if kind == 'index':
        if arg not in indexes:
            errors.append(
                f"{where}: refs names index {arg!r}, which no earlier "
                f"place_index defines (defined so far: "
                f"{', '.join(sorted(indexes)) or 'none'})")
            return None
        return arg
    return None


def _check_where(where: str, obj, index: Optional[Dict],
                 errors: List[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{where}.where: must be an object of "
                      f"{{field: {{op: value}}}}, got {obj!r}")
        return
    for field, pred in sorted(obj.items()):
        if index is not None and field not in index['fields']:
            errors.append(
                f"{where}.where: field {field!r} is not defined by index "
                f"{index['name']!r} (has: "
                f"{', '.join(sorted(index['fields'])) or 'none'})")
        if not isinstance(pred, dict) or not pred:
            errors.append(f"{where}.where.{field}: must be an object like "
                          f"{{\"lt\": 3}}, got {pred!r}")
            continue
        for op in sorted(pred):
            if op not in WHERE_OPS:
                errors.append(
                    f"{where}.where.{field}: unknown predicate {op!r} "
                    f"(known: {', '.join(WHERE_OPS)})")


def _check_order(where: str, value, index: Optional[Dict],
                 errors: List[str]) -> None:
    if not _str_list(value):
        errors.append(f"{where}.order: must be a list of field names, "
                      f"'-name' for descending, got {value!r}")
        return
    if index is None:
        return
    for tok in value:
        name = tok[1:] if tok.startswith('-') else tok
        if name not in index['fields'] and name != 'ref':
            errors.append(
                f"{where}.order: field {name!r} is not defined by index "
                f"{index['name']!r} (has: "
                f"{', '.join(sorted(index['fields'])) or 'none'}, or 'ref')")


def _check_origin(where: str, obj, errors: List[str]) -> None:
    """origin is {x, y}; each axis is a number or a solve spec.

    The solve spec exists because the per-column stagger arrange.py used
    ({34.0, 28.5, 25.5, 30.0, 39.5}) was PROBED against the real outline
    (arrange.py:85-103), not authored. It is a measurement of that board, and
    a zone rect -- the only thing the intent schema can express -- can only be
    authored.
    """
    if not isinstance(obj, dict):
        errors.append(f"{where}.origin: must be an object {{x, y}}, "
                      f"got {obj!r}")
        return
    _check_keys(f"{where}.origin", obj, (('x', 'y'), ()), errors)
    for axis in ('x', 'y'):
        v = obj.get(axis)
        if v is None or _is_num(v):
            continue
        if isinstance(v, str):
            if v != 'solve:outline_probe':
                errors.append(
                    f"{where}.origin.{axis}: unknown solve {v!r} "
                    f"(known: 'solve:outline_probe')")
            continue
        if isinstance(v, dict):
            if v.get('solve') != 'outline_probe':
                errors.append(
                    f"{where}.origin.{axis}: solve must be 'outline_probe', "
                    f"got {v.get('solve')!r}")
            _check_keys(f"{where}.origin.{axis}", v,
                        (('solve',), _ORIGIN_SOLVE_FIELDS[1]), errors)
            for k in ('from', 'step', 'limit'):
                if k in v and not _is_num(v[k]):
                    errors.append(f"{where}.origin.{axis}.{k}: must be a "
                                  f"number, got {v[k]!r}")
            also = v.get('also')
            if also is not None:
                if not isinstance(also, list):
                    errors.append(f"{where}.origin.{axis}.also: must be a "
                                  f"list, got {also!r}")
                else:
                    for j, a in enumerate(also):
                        w = f"{where}.origin.{axis}.also[{j}]"
                        if not isinstance(a, dict):
                            errors.append(f"{w}: must be an object "
                                          f"{{offset, extent}}")
                            continue
                        _check_keys(w, a, _ALSO_FIELDS, errors)
                        for k in ('offset', 'extent'):
                            if k in a and not _num_list(a[k], 2):
                                errors.append(f"{w}.{k}: must be two numbers, "
                                              f"got {a[k]!r}")
            continue
        errors.append(f"{where}.origin.{axis}: must be a number or a solve "
                      f"spec, got {v!r}")


def _check_mirror(where: str, obj, index: Optional[Dict],
                  errors: List[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{where}.mirror: must be an object {{axis, when}}, "
                      f"got {obj!r}")
        return
    _check_keys(f"{where}.mirror", obj, _MIRROR_FIELDS, errors)
    if obj.get('axis') not in MIRROR_AXES:
        errors.append(f"{where}.mirror.axis: unknown axis "
                      f"{obj.get('axis')!r} (known: {', '.join(MIRROR_AXES)})")
    when = obj.get('when')
    if when is not None:
        if not isinstance(when, dict):
            errors.append(f"{where}.mirror.when: must be a where-object like "
                          f"{{\"half\": {{\"eq\": \"R\"}}}}, got {when!r}")
        else:
            _check_where(f"{where}.mirror", when, index, errors)


def _check_index(where: str, op: Dict, indexes: Dict[str, Dict],
                 errors: List[str]) -> None:
    name = op.get('name')
    if not isinstance(name, str) or not name:
        errors.append(f"{where}.name: must be a non-empty string, "
                      f"got {name!r}")
        name = None
    elif name in indexes:
        errors.append(f"{where}.name: index {name!r} is already defined")
    sel = op.get('select')
    if sel is not None and not isinstance(sel, str):
        errors.append(f"{where}.select: must be a reference regex, "
                      f"got {sel!r}")
    elif isinstance(sel, str):
        try:
            re.compile(sel)
        except re.error as e:
            errors.append(f"{where}.select: not a valid regex ({e})")

    fields: Dict[str, Dict] = {}
    spec = op.get('fields') or {}
    if not isinstance(spec, dict):
        errors.append(f"{where}.fields: must be an object, got {spec!r}")
        spec = {}
    for fname, fspec in sorted(spec.items()):
        w = f"{where}.fields.{fname}"
        if not isinstance(fspec, dict):
            errors.append(f"{w}: must be an object {{pattern, group, as}}, "
                          f"got {fspec!r}")
            continue
        _check_keys(w, fspec, _INDEX_FIELD_FIELDS, errors)
        src = fspec.get('from', 'net')
        if src != 'net':
            errors.append(f"{w}.from: only 'net' is supported, got {src!r}")
        pat = fspec.get('pattern')
        if isinstance(pat, str):
            try:
                re.compile(pat)
            except re.error as e:
                errors.append(f"{w}.pattern: not a valid regex ({e})")
        elif pat is not None:
            errors.append(f"{w}.pattern: must be a regex string, got {pat!r}")
        grp = fspec.get('group', 1)
        if not isinstance(grp, int) or isinstance(grp, bool) or grp < 1:
            errors.append(f"{w}.group: must be a capture-group number >= 1, "
                          f"got {grp!r}")
        as_ = fspec.get('as', 'str')
        if as_ not in FIELD_TYPES:
            errors.append(f"{w}.as: unknown type {as_!r} "
                          f"(known: {', '.join(FIELD_TYPES)})")
        mp = fspec.get('map')
        if mp is not None and not isinstance(mp, dict):
            errors.append(f"{w}.map: must be an object, got {mp!r}")
        fields[fname] = dict(fspec)

    partner = op.get('partner')
    if partner is not None:
        w = f"{where}.partner"
        if not isinstance(partner, dict):
            errors.append(f"{w}: must be an object {{index, pattern}}, "
                          f"got {partner!r}")
        else:
            _check_keys(w, partner, _PARTNER_FIELDS, errors)
            other = partner.get('index')
            if other is not None and other not in indexes:
                errors.append(
                    f"{w}.index: names index {other!r}, which no earlier "
                    f"place_index defines (defined so far: "
                    f"{', '.join(sorted(indexes)) or 'none'})")
            pat = partner.get('pattern')
            if isinstance(pat, str):
                try:
                    re.compile(pat)
                except re.error as e:
                    errors.append(f"{w}.pattern: not a valid regex ({e})")
            inherit = partner.get('inherit')
            if inherit is not None:
                if not _str_list(inherit):
                    errors.append(f"{w}.inherit: must be a list of field "
                                  f"names, got {inherit!r}")
                elif other in indexes:
                    have = indexes[other]['fields']
                    for f in inherit:
                        if f not in have:
                            errors.append(
                                f"{w}.inherit: index {other!r} defines no "
                                f"field {f!r} (has: "
                                f"{', '.join(sorted(have)) or 'none'})")
                        else:
                            fields[f] = dict(have[f])
            fields[partner.get('as') or 'partner'] = {'from': 'partner'}

    if name:
        indexes[name] = {'name': name, 'fields': fields, 'op': op}


def _check_rect(where: str, value, errors: List[str]) -> None:
    if not _num_list(value, 4):
        errors.append(f"{where}: must be four numbers [x0, y0, x1, y1], "
                      f"got {value!r}")
        return
    x0, y0, x1, y1 = value
    if x1 <= x0 or y1 <= y0:
        errors.append(f"{where}: empty rect [x0, y0, x1, y1] = {list(value)} "
                      f"(needs x1 > x0 and y1 > y0)")


def _check_common(where: str, op: Dict, index: Optional[Dict],
                  errors: List[str]) -> None:
    """Fields shared by the seating ops."""
    for k in ('within', 'clearance', 'tolerance', 'overhang'):
        if k in op and op[k] is not None and not _is_num(op[k]):
            errors.append(f"{where}.{k}: must be a number (mm), got {op[k]!r}")
    if 'within' in op and _is_num(op.get('within')) and op['within'] <= 0:
        errors.append(f"{where}.within: must be > 0 mm, got {op['within']!r}")
    rot = op.get('rot')
    if rot is not None and not _is_num(rot):
        errors.append(f"{where}.rot: must be a number (degrees), got {rot!r}")
    rp = op.get('rot_prefer')
    if rp is not None:
        if not isinstance(rp, (list, tuple)) or not all(_is_num(x) for x in rp):
            errors.append(f"{where}.rot_prefer: must be a list of angles in "
                          f"preference order, got {rp!r}")
    if 'order' in op and op['order'] is not None:
        _check_order(where, op['order'], index, errors)
    if 'group_by' in op and op['group_by'] is not None:
        _check_order(f"{where}.group_by", op['group_by'], index, errors)
    if 'where' in op and op['where'] is not None:
        _check_where(where, op['where'], index, errors)
    if 'mirror' in op and op['mirror'] is not None:
        _check_mirror(where, op['mirror'], index, errors)


def validate_ops(ops: Sequence[Dict]) -> List[str]:
    """Every reason this plan cannot be executed as written.

    Ops are validated IN ORDER, because `index:` selectors resolve against the
    indexes defined before them -- a forward reference is a real error, not a
    scheduling detail.
    """
    errors: List[str] = []
    indexes: Dict[str, Dict] = {}
    for i, op in enumerate(ops):
        where = f"step {i + 1}"
        if not isinstance(op, dict):
            errors.append(f"{where}: not an object, got {op!r}")
            continue
        action = op.get('action')
        if action not in PLACEMENT_ACTIONS:
            errors.append(
                f"{where}: unknown action {action!r} (known: "
                f"{', '.join(PLACEMENT_ACTIONS)})")
            continue
        if action in UNIMPLEMENTED_ACTIONS:
            live = ', '.join(a for a in PLACEMENT_ACTIONS
                             if a not in UNIMPLEMENTED_ACTIONS)
            errors.append(
                f"{where}: {action!r} has a settled schema but no resolver "
                f"yet, so a plan using it cannot be executed. "
                f"Implemented: {live}")
            continue
        where = f"{where} ({action})"
        open_keys = ('params',) if action in ('place_repair',
                                              'place_polish') else ()
        _check_keys(where, op, _OP_FIELDS[action], errors, open_keys)

        if action == 'place_index':
            _check_index(where, op, indexes, errors)
            continue

        idx: Optional[Dict] = None
        if op.get('refs') is not None:
            name = _check_refs(where, op['refs'], indexes, errors)
            idx = indexes.get(name) if name else None
            # `where`, `group_by` and `mirror.when` all name INDEX FIELDS.
            # On a glob or `group:` selection there is no index to evaluate
            # them against, and `select_refs` simply dropped them -- a
            # recognised key producing a different placement in silence,
            # which is the failure this validator exists to prevent.
            if idx is None:
                for key in ('where', 'group_by'):
                    if op.get(key) is not None:
                        errors.append(
                            f"{where}.{key}: names index fields, but refs is "
                            f"not an 'index:<name>' selection, so there are "
                            f"no fields to filter on")
                mir = op.get('mirror')
                if isinstance(mir, dict) and mir.get('when') is not None:
                    errors.append(
                        f"{where}.mirror.when: names index fields, but refs "
                        f"is not an 'index:<name>' selection, so there are "
                        f"no fields to test")

        if action == 'place_keepout':
            _check_rect(f"{where}.rect", op.get('rect'), errors)
            sides = op.get('sides')
            if sides is not None and not (_str_list(sides) and
                                          all(s in ('F', 'B') for s in sides)):
                errors.append(f"{where}.sides: must be a list from ['F','B'], "
                              f"got {sides!r}")
            if op.get('allow') is not None and not _str_list(op['allow']):
                errors.append(f"{where}.allow: must be a list of ref globs, "
                              f"got {op['allow']!r}")
            continue

        _check_common(where, op, idx, errors)

        if action == 'place_at':
            if not isinstance(op.get('ref'), str):
                errors.append(f"{where}.ref: must be a single reference, "
                              f"got {op.get('ref')!r}")
            if not _num_list(op.get('at'), 2):
                errors.append(f"{where}.at: must be two numbers [x, y], "
                              f"got {op.get('at')!r}")

        elif action == 'place_array':
            if not _num_list(op.get('pitch'), 2):
                errors.append(f"{where}.pitch: must be two numbers "
                              f"[dx, dy] in mm, got {op.get('pitch')!r}")
            elif op['pitch'][0] <= 0 and op['pitch'][1] <= 0:
                errors.append(f"{where}.pitch: at least one axis must be "
                              f"> 0, got {list(op['pitch'])}")
            _check_origin(where, op.get('origin'), errors)
            for k in ('index_x', 'index_y'):
                v = op.get(k)
                if v is not None and not isinstance(v, str):
                    errors.append(f"{where}.{k}: must name an index field, "
                                  f"got {v!r}")
                elif isinstance(v, str) and idx is not None \
                        and v not in idx['fields']:
                    errors.append(
                        f"{where}.{k}: field {v!r} is not defined by index "
                        f"{idx['name']!r} (has: "
                        f"{', '.join(sorted(idx['fields'])) or 'none'})")

        elif action == 'place_slots':
            slots = op.get('slots')
            if not isinstance(slots, list) or not slots:
                errors.append(f"{where}.slots: must be a non-empty list of "
                              f"[x, y], got {slots!r}")
            else:
                for j, s in enumerate(slots):
                    if not _num_list(s, 2):
                        errors.append(f"{where}.slots[{j}]: must be two "
                                      f"numbers [x, y], got {s!r}")

        elif action == 'place_relative':
            if not _num_list(op.get('offset'), 2):
                errors.append(f"{where}.offset: must be two numbers "
                              f"[dx, dy] in mm, got {op.get('offset')!r}")
            of = op.get('of')
            of_idx = _check_refs(f"{where}.of", of, indexes, errors) \
                if of is not None else None
            pair_by = op.get('pair_by')
            if pair_by is not None:
                if not isinstance(pair_by, str):
                    errors.append(f"{where}.pair_by: must name a field, "
                                  f"got {pair_by!r}")
                elif of_idx and pair_by not in indexes[of_idx]['fields']:
                    errors.append(
                        f"{where}.pair_by: field {pair_by!r} is not defined "
                        f"by index {of_idx!r} (has: "
                        f"{', '.join(sorted(indexes[of_idx]['fields'])) or 'none'})")

        elif action == 'place_edge':
            if op.get('edge') not in EDGES:
                errors.append(f"{where}.edge: unknown edge "
                              f"{op.get('edge')!r} (known: {', '.join(EDGES)})")

        elif action == 'place_pack':
            _check_rect(f"{where}.zone", op.get('zone'), errors)
            pol = op.get('policy', 'radial')
            if pol not in PACK_POLICIES:
                errors.append(f"{where}.policy: unknown policy {pol!r} "
                              f"(known: {', '.join(PACK_POLICIES)})")

        elif action == 'place_lift':
            for k in ('for',):
                if op.get(k) is not None:
                    _check_refs(f"{where}.{k}", op[k], indexes, errors)
            restore = op.get('restore')
            if restore is not None and not isinstance(restore, bool):
                errors.append(f"{where}.restore: must be true or false, "
                              f"got {restore!r}")

        elif action == 'place_repair':
            caps = op.get('caps')
            if caps is not None and not (isinstance(caps, list) and caps
                                         and all(_is_num(c) for c in caps)):
                errors.append(f"{where}.caps: must be a non-empty list of "
                              f"displacement caps in mm, got {caps!r}")

    return errors


def parse_placement_plan(value) -> Tuple[Optional[List[Dict]], List[str]]:
    """Parse and validate a placement plan. Returns (ops, errors).

    `ops` is None whenever anything is wrong: see the module docstring for why
    a placement plan is all-or-nothing where a routing plan is not.
    """
    if isinstance(value, (dict, list)):
        data = value
    else:
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            return None, [f"placement plan is not valid JSON: {e}"]
    if isinstance(data, list):
        data = {'steps': data}
    if not isinstance(data, dict):
        return None, ['placement plan JSON is not an object']
    schema = data.get('schema', SCHEMA_VERSION)
    if schema != SCHEMA_VERSION:
        return None, [f"placement plan schema {schema!r} is not "
                      f"{SCHEMA_VERSION}"]
    steps = data.get('steps')
    if not isinstance(steps, list):
        return None, ['placement plan JSON has no "steps" list']
    if not steps:
        return None, ['placement plan has no steps']
    errors = validate_ops(steps)
    if errors:
        return None, errors
    return list(steps), []


def format_errors(errors: Sequence[str]) -> str:
    """The refusal, in the shape the placement CLIs already print."""
    if not errors:
        return ''
    head = (f"placement plan REFUSED: {len(errors)} problem(s). Nothing was "
            f"placed -- an op this tool cannot execute as written would "
            f"produce a different placement and report success.")
    return '\n'.join([head] + [f"  - {e}" for e in errors])


# Appended to the placement skill prompt so the plan lands as parseable JSON.
# Kept beside PLACEMENT_RESULT_SCHEMA (kicad_routing_plugin/placement_run.py),
# which is the COMPLETION contract; this is the AUTHORING one.
PLACEMENT_PLAN_SCHEMA = (
    'PLACEMENT_PLAN=<compact single-line JSON> with this exact schema: '
    '{"schema": 1, "steps": [ '
    '{"action": "place_index", "name": "<index name>", '
    '"select": "<regex over REFERENCES, e.g. ^SW\\\\d+$>", '
    '"fields": {"<field>": {"pattern": "<regex over the part\'s NET NAMES>", '
    '"group": <capture group, default 1>, "as": "int"|"str", '
    '"map": {"<raw>": "<value>"}}}, '
    '"partner": {"index": "<other index>", '
    '"pattern": "<regex matching the net the two share, e.g. ^Net-\\\\(>", '
    '"inherit": ["<field to copy from the partner>"], "as": "partner"}} | '
    '{"action": "place_keepout", "rect": [x0,y0,x1,y1], "reason": "<why>"} | '
    '{"action": "place_fixed", "ref": "<ref>", "at": [x,y], "rot": <deg>} | '
    '{"action": "place_at", "ref": "<ref>", "at": [x,y], "rot": <deg>, '
    '"within": <mm>, "mirror": {"axis": "board:xmid"}} | '
    '{"action": "place_array", "refs": "index:<name>", "pitch": [dx,dy], '
    '"origin": {"x": <mm>|"solve:outline_probe", "y": <mm>|{"solve": '
    '"outline_probe", "from": <mm>, "step": <mm>, "limit": <steps>, '
    '"also": [{"offset": [dx,dy], "extent": [w,h]}]}}, '
    '"index_x": "<field giving the column number>", '
    '"index_y": "<field giving the row number>", '
    '"mirror": {"axis": "board:xmid", "when": {"<field>": {"eq": "<value>"}}}, '
    '"where": {"<field>": {"lt": <n>}}, "order": ["<field>", "-<field>"], '
    '"rot": <deg>, "within": <mm>} | '
    '{"action": "place_slots", "refs": "index:<name>", '
    '"slots": [[x,y], ...], "group_by": ["<field>"], "order": ["<field>"], '
    '"mirror": {...}, "within": <mm>} | '
    '{"action": "place_relative", "refs": "index:<name>", '
    '"of": "index:<name>", "pair_by": "partner", "offset": [dx,dy], '
    '"rot": <deg>, "where": {...}, "within": <mm>} | '
    '{"action": "place_edge", "refs": ["<ref>"], '
    '"edge": "north"|"south"|"east"|"west", "overhang": <mm>} | '
    '{"action": "place_pack", "refs": "group:<key>"|["<glob>"], '
    '"zone": [x0,y0,x1,y1], "policy": "radial"|"rows"|"grid"|"ring", '
    '"within": <mm>} | '
    '{"action": "place_lift", "refs": ["<blocker>"], "for": ["<blocked>"], '
    '"restore": true} | '
    '{"action": "place_repair", "caps": [<mm>, ...]} | '
    '{"action": "place_polish", "params": {"max_displacement": <mm>}} | '
    '{"action": "place_lock", "refs": ["<glob>"]} '
    ']} '
    'Ops run IN ORDER and each seats against everything already seated, so '
    'put the parts whose position is a mechanical fact first (place_fixed), '
    'then the large anchors, then the lattices, then their satellites, then '
    'the rest. '
    'place_fixed is the ONE op that does not search: it ASSERTS a pose the '
    'mechanical drawing already fixed (a mounting hole, an edge receptacle), '
    'never moves that part, and makes it an obstacle for everything after. '
    'Use it instead of place_at for anything whose position is not yours to '
    'choose -- place_at with a tiny `within` parks, and with a large one it '
    'MOVES the hole. '
    'A target is a HINT: every op seats at the nearest fully-legal pose to it '
    'and reports how far that was, so state intent rather than solved '
    'coordinates. Use "solve:outline_probe" instead of typing a coordinate '
    'you measured off the outline yourself. '
    'ANY op this tool cannot execute as written refuses the WHOLE plan and '
    'places nothing, so do not guess at key names. '
    'NOT IMPLEMENTED YET, and refused if used: '
    + ', '.join(UNIMPLEMENTED_ACTIONS) +
    ' -- their schema is settled but no resolver is written, so do not put '
    'them in a plan you intend to run. '
    # GENERATED from _OP_FIELDS, never hand-listed. The prose above is a
    # readable sketch and was missing fields the validator accepts -- `note`
    # on every op, plus rot_prefer / sides / allow / tolerance -- discoverable
    # only by sending a bad key and reading the refusal. A contract that says
    # "do not guess at key names" must not omit the names. This suffix cannot
    # drift: tests/test_place_plan_schema.py asserts every _OP_FIELDS entry
    # appears in it.
    'EVERY accepted key, by action (required | optional): '
    + '; '.join(
        f"{action}: "
        + (' '.join(_OP_FIELDS[action][0]) or '-')
        + ' | '
        + (' '.join(_OP_FIELDS[action][1]) or '-')
        for action in PLACEMENT_ACTIONS if action in _OP_FIELDS)
    + '.'
)
