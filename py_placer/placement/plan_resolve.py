"""Execute a placement plan: statements in, seated poses out.

Every op resolves to `seeder._try_place` calls, which is what makes this
cheap: the target a plan states is a HINT, and `_try_place` returns the
nearest FULLY-CONTAINED legal pose to it, trying the requested rotation in
full before the rest of the 90-degree lattice, and relaxing courtyard
clearance in three steps before giving up. So legality, the rotation
fallback, the clearance ladder and the pile-exclusion rule all behave exactly
as they do for `seed_from_intent`, and a plan cannot author an illegal board.

`wk/run19/urchin/arrange.py` used the same primitive for all 80 of its seats
(`arrange.py:154-171`). The difference is that the ARRANGEMENT is now stated
rather than computed, so it is inspectable, diffable and replayable.

Two reporting rules, both taken from what the hand scripts got right:

* **A park is a measurement, not a silence.** A ref no legal pose was found
  for is reported with its target, its budget and the reason -- never
  dropped, and never left half-moved (the pose is restored, so a failed op
  leaves the board exactly as it found it).
* **A relaxed clearance is a NOTE.** `_try_place` returns the clearance it
  succeeded at; when that is below the asked-for floor the run says so, the
  way `arrange.py:169-170` did.

Ops this module does not implement yet REFUSE, naming themselves. Silently
skipping an op would produce a different placement and report success, which
is the failure `plan_ops`' all-or-nothing validation exists to prevent.
"""
from __future__ import annotations

import fnmatch
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from placement import seeder
from placement.plan_ops import PlanError, parse_ref_selector

# Implemented so far. An op outside this set refuses by name rather than
# being skipped -- see the module docstring.
RESOLVED_ACTIONS = (
    'place_index', 'place_at', 'place_relative', 'place_edge', 'place_lock',
)

DEFAULT_EDGE_OVERHANG_MM = 0.5


@dataclass
class Seat:
    """One part, seated. `moved_mm` is target-to-seat, which is the number
    that says whether the plan's intent survived contact with the board."""
    ref: str
    step: int
    action: str
    target: Tuple[float, float]
    pose: Tuple[float, float, float]
    clearance: float
    moved_mm: float
    rot_requested: Optional[float] = None
    rot_changed: bool = False

    def to_dict(self) -> Dict:
        return {'ref': self.ref, 'step': self.step, 'action': self.action,
                'target': [round(v, 4) for v in self.target],
                'pose': [round(v, 4) for v in self.pose],
                'clearance': round(self.clearance, 4),
                'moved_mm': round(self.moved_mm, 4),
                'rot_requested': self.rot_requested,
                'rot_changed': self.rot_changed}


@dataclass
class Park:
    """One part the plan named and could not seat. `blockers` is filled by the
    lift op's census (issue #629) and is empty until then -- an empty list
    means "not censused", which is why `censused` is carried separately."""
    ref: str
    step: int
    action: str
    reason: str
    target: Optional[Tuple[float, float]] = None
    within: Optional[float] = None
    blockers: Dict[str, int] = field(default_factory=dict)
    censused: bool = False

    def to_dict(self) -> Dict:
        return {'ref': self.ref, 'step': self.step, 'action': self.action,
                'reason': self.reason,
                'target': None if self.target is None
                else [round(v, 4) for v in self.target],
                'within': self.within,
                'blockers': dict(self.blockers), 'censused': self.censused}


@dataclass
class ResolveResult:
    seats: List[Seat] = field(default_factory=list)
    parks: List[Park] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    lock_refs: List[str] = field(default_factory=list)
    indexes: Dict[str, Dict] = field(default_factory=dict)
    complete: bool = True

    @property
    def placements(self) -> List[Dict]:
        """Writer format, in seating order."""
        return [{'reference': s.ref, 'new_x': s.pose[0], 'new_y': s.pose[1],
                 'new_rotation': s.pose[2]} for s in self.seats]

    def summary(self) -> Dict:
        return {'seated': len(self.seats), 'parked': len(self.parks),
                'parked_refs': [p.ref for p in self.parks],
                'locked': len(self.lock_refs),
                'worst_move_mm': round(max((s.moved_mm for s in self.seats),
                                           default=0.0), 4),
                'relaxed': sum(1 for n in self.notes
                               if 'relaxed clearance' in n),
                'complete': self.complete}


# --------------------------------------------------------------------------
# index: structure from net names
# --------------------------------------------------------------------------
def _pad_nets(pcb_data, ref: str) -> List[str]:
    fp = pcb_data.footprints.get(ref)
    if fp is None:
        return []
    return [p.net_name for p in fp.pads if p.net_id and p.net_name]


def _extract_field(nets: Sequence[str], spec: Dict):
    """The first net matching `pattern`, reduced to this field's value.

    An absent optional capture group reads as '' rather than None, so a
    prefix-or-nothing group (`^(R_)?COL(\\d)$`, arrange.py:47) can be mapped
    to a real value on both branches.
    """
    pat = re.compile(spec['pattern'])
    grp = int(spec.get('group', 1))
    for net in nets:
        m = pat.match(net)
        if not m or grp > (m.re.groups or 0):
            continue
        raw = m.group(grp) or ''
        mp = spec.get('map')
        if mp is not None:
            if raw not in mp:
                continue
            raw = mp[raw]
        if spec.get('as', 'str') == 'int':
            try:
                return int(raw)
            except (TypeError, ValueError):
                continue
        return raw
    return None


def _build_index(pcb_data, op: Dict, indexes: Dict[str, Dict],
                 notes: List[str]) -> Dict:
    name = op['name']
    select = re.compile(op['select'])
    members: Dict[str, Dict] = {}
    for ref in sorted(pcb_data.footprints):
        if not select.search(ref):
            continue
        nets = _pad_nets(pcb_data, ref)
        row: Dict[str, Any] = {}
        for fname, fspec in sorted((op.get('fields') or {}).items()):
            v = _extract_field(nets, fspec)
            if v is not None:
                row[fname] = v
        members[ref] = row

    partner = op.get('partner')
    if partner:
        other = indexes[partner['index']]
        pat = re.compile(partner['pattern'])
        as_ = partner.get('as') or 'partner'
        # Which of the other index's members sits on each matching net.
        by_net: Dict[str, str] = {}
        for oref in sorted(other['members']):
            for net in _pad_nets(pcb_data, oref):
                if pat.match(net):
                    by_net.setdefault(net, oref)
        paired = 0
        for ref, row in sorted(members.items()):
            for net in _pad_nets(pcb_data, ref):
                if not pat.match(net):
                    continue
                oref = by_net.get(net)
                if oref is None or oref == ref:
                    continue
                row[as_] = oref
                for f in (partner.get('inherit') or ()):
                    v = other['members'].get(oref, {}).get(f)
                    if v is not None:
                        row[f] = v
                paired += 1
                break
        notes.append(f"index {name!r}: {len(members)} member(s), "
                     f"{paired} paired with {partner['index']!r}")
    else:
        notes.append(f"index {name!r}: {len(members)} member(s)")
    return {'name': name, 'members': members}


def index_refs(index: Dict, where: Optional[Dict] = None,
               order: Optional[Sequence[str]] = None) -> List[str]:
    """Members passing `where`, in `order` (then by ref, always -- an index
    whose order leaves ties must still resolve the same way twice, #457)."""
    refs = [r for r, row in index['members'].items() if _passes(row, where)]
    return sorted(refs, key=lambda r: _sort_key(index['members'][r], r, order))


def _passes(row: Dict, where: Optional[Dict]) -> bool:
    if not where:
        return True
    for fname, pred in where.items():
        v = row.get(fname)
        for op, want in pred.items():
            if v is None:
                return False
            try:
                if op == 'eq' and not v == want:
                    return False
                if op == 'ne' and not v != want:
                    return False
                if op == 'lt' and not v < want:
                    return False
                if op == 'le' and not v <= want:
                    return False
                if op == 'gt' and not v > want:
                    return False
                if op == 'ge' and not v >= want:
                    return False
                if op == 'in' and v not in want:
                    return False
            except TypeError:
                return False
    return True


def _sort_key(row: Dict, ref: str, order: Optional[Sequence[str]]):
    key: List[Any] = []
    for tok in (order or ()):
        desc = tok.startswith('-')
        name = tok[1:] if desc else tok
        v = ref if name == 'ref' else row.get(name)
        # None sorts last either way: an unindexed member is not "smallest".
        missing = v is None
        if isinstance(v, str):
            key.append((missing, _Neg(v) if desc else v))
        else:
            num = 0.0 if missing else float(v)
            key.append((missing, -num if desc else num))
    key.append(ref)
    return key


class _Neg:
    """Reverse ordering for a string sort key, without a cmp_to_key detour."""
    __slots__ = ('v',)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        return self.v > other.v

    def __eq__(self, other):
        return self.v == other.v


# --------------------------------------------------------------------------
# ref selection
# --------------------------------------------------------------------------
def select_refs(value, pcb_data, indexes: Dict[str, Dict], *,
                where: Optional[Dict] = None,
                order: Optional[Sequence[str]] = None,
                groups: Optional[Dict[str, List[str]]] = None) -> List[str]:
    kind, arg = parse_ref_selector(value)
    if kind == 'index':
        return index_refs(indexes[arg], where, order)
    if kind == 'group':
        if not groups or arg not in groups:
            raise PlanError(
                f"refs names group {arg!r}, which this board does not "
                f"derive (have: {', '.join(sorted(groups or {})) or 'none'})")
        refs = sorted(groups[arg])
    else:
        all_refs = sorted(pcb_data.footprints)
        refs = sorted({r for pat in arg for r in fnmatch.filter(all_refs, pat)})
    if order:
        refs = sorted(refs, key=lambda r: _sort_key({}, r, order))
    return refs


# --------------------------------------------------------------------------
# the resolver
# --------------------------------------------------------------------------
class _Resolver:
    def __init__(self, pcb_data, pcb_file, state, deadline=None,
                 progress=None):
        self.pcb = pcb_data
        self.pcb_file = pcb_file
        self.st = state
        self.deadline = deadline
        self.progress = progress
        self.res = ResolveResult()
        # The pile: parts not yet seated by this plan. They are passed as
        # `exclude` so their meaningless input coordinates cannot veto a real
        # pose -- seed_from_intent's own rule (seeder.py:78-79). A part locked
        # in the FILE is authoritatively placed and never in this set.
        self.pending: Set[str] = {r for r, p in state.parts.items()
                                  if not p.locked}
        self._groups: Optional[Dict[str, List[str]]] = None

    # -- seating ---------------------------------------------------------
    def seat(self, ref: str, tx: float, ty: float, step: int, action: str,
             *, within: Optional[float] = None, rot=None, rot_prefer=None,
             constraint=None, tol: float = 0.5) -> bool:
        if ref not in self.st.parts:
            self.res.parks.append(Park(
                ref=ref, step=step, action=action,
                reason='not a movable part on this board'))
            return False
        part = self.st.parts[ref]
        if part.locked:
            self.res.parks.append(Park(
                ref=ref, step=step, action=action,
                reason='(locked yes) in the file -- not this tool\'s to move'))
            return False

        home = (part.x, part.y, part.rot)
        # `_try_place` tries the part's CURRENT rotation in full before the
        # rest of its lattice, so a requested angle is applied first and is
        # therefore what gets searched first. That is the whole mechanism for
        # `rot`, and it is why the intent schema -- which has no rotation --
        # could never express one (seeder.py:26-32).
        angles: List[Optional[float]] = list(rot_prefer) if rot_prefer \
            else [rot]
        info: Dict = {}
        for angle in angles:
            if angle is not None:
                self.st.apply_move(ref, part.x, part.y, float(angle) % 360.0)
            info = {}
            clr = seeder._try_place(self.st, ref, tx, ty, self.pending - {ref},
                                    constraint=constraint, tol=tol,
                                    max_disp=within, info=info,
                                    deadline=self.deadline)
            if clr is not None:
                self.pending.discard(ref)
                p = self.st.parts[ref]
                moved = math.hypot(p.x - tx, p.y - ty)
                requested = None if angle is None else float(angle) % 360.0
                changed = requested is not None and abs(
                    ((p.rot - requested + 180.0) % 360.0) - 180.0) > 1e-6
                self.res.seats.append(Seat(
                    ref=ref, step=step, action=action, target=(tx, ty),
                    pose=(p.x, p.y, p.rot), clearance=clr, moved_mm=moved,
                    rot_requested=requested, rot_changed=changed))
                if clr < self.st.clearance - 1e-9:
                    self.res.notes.append(
                        f"{ref}: seated at relaxed clearance {clr:g} "
                        f"(none at {self.st.clearance:g})")
                if changed:
                    self.res.notes.append(
                        f"{ref}: asked for rot {requested:g}, seated at "
                        f"{p.rot:g} -- no legal pose at the requested angle")
                return True
        # Nothing took. Leave the board exactly as it was found.
        self.st.apply_move(ref, *home)
        if info.get('deadline'):
            self.res.complete = False
            self.res.parks.append(Park(
                ref=ref, step=step, action=action, target=(tx, ty),
                within=within,
                reason='the deadline expired during this search -- nothing '
                       'was measured'))
            return False
        budget = f"within {within:g}mm of " if within is not None else "near "
        self.res.parks.append(Park(
            ref=ref, step=step, action=action, target=(tx, ty), within=within,
            reason=f"no legal pose {budget}({tx:.1f}, {ty:.1f})"))
        return False

    # -- ops -------------------------------------------------------------
    def op_place_index(self, op, step):
        self.res.indexes[op['name']] = _build_index(
            self.pcb, op, self.res.indexes, self.res.notes)

    def op_place_at(self, op, step):
        x, y = op['at']
        self.seat(op['ref'], float(x), float(y), step, 'place_at',
                  within=op.get('within'), rot=op.get('rot'),
                  rot_prefer=op.get('rot_prefer'))

    def op_place_relative(self, op, step):
        children = set(self.refs(op['refs'], op.get('where')))
        parents_idx = self._index_of(op['of'])
        dx, dy = op['offset']
        pair_by = op.get('pair_by')
        pairs: List[Tuple[str, str]] = []
        if parents_idx is not None and pair_by:
            for pref in index_refs(parents_idx, None, op.get('order')):
                cref = parents_idx['members'][pref].get(pair_by)
                if isinstance(cref, str) and cref in children:
                    pairs.append((pref, cref))
        else:
            # No join declared: pair positionally, which is only honest when
            # the two selections are the same length.
            parents = self.refs(op['of'], None, op.get('order'))
            kids = sorted(children)
            if len(parents) != len(kids):
                for r in kids:
                    self.res.parks.append(Park(
                        ref=r, step=step, action='place_relative',
                        reason=f"no pair_by declared and the two selections "
                               f"differ in size ({len(parents)} parents, "
                               f"{len(kids)} children) -- nothing to pair on"))
                return
            pairs = list(zip(parents, kids))

        seated = {s.ref for s in self.res.seats}
        for pref, cref in pairs:
            if pref not in self.st.parts:
                self.res.parks.append(Park(
                    ref=cref, step=step, action='place_relative',
                    reason=f"its parent {pref} is not a part on this board"))
                continue
            if pref in self.pending and pref not in seated \
                    and not self.st.parts[pref].locked:
                # The offset is against the parent's RESOLVED pose
                # (arrange.py:182-184). An unseated parent is still at its
                # pile coordinate, so the child would be placed against a
                # number that means nothing.
                self.res.parks.append(Park(
                    ref=cref, step=step, action='place_relative',
                    reason=f"its parent {pref} is not seated yet -- a "
                           f"relative offset against an unseated parent "
                           f"would resolve against its pile pose"))
                continue
            p = self.st.parts[pref]
            self.seat(cref, p.x + float(dx), p.y + float(dy), step,
                      'place_relative', within=op.get('within'),
                      rot=op.get('rot'), rot_prefer=op.get('rot_prefer'))

    def op_place_edge(self, op, step):
        refs = self.refs(op['refs'], None, op.get('order'))
        overhang = op.get('overhang')
        overhang = DEFAULT_EDGE_OVERHANG_MM if overhang is None \
            else float(overhang)
        entry = {'edge': op['edge'],
                 'overhang_mm': {'min': overhang, 'max': overhang}}
        n = len(refs)
        for k, ref in enumerate(refs):
            if ref not in self.st.parts:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_edge',
                    reason='not a movable part on this board'))
                continue
            part = self.st.parts[ref]
            if part.locked:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_edge',
                    reason='(locked yes) in the file -- not this tool\'s '
                           'to move'))
                continue
            home = (part.x, part.y, part.rot)
            if op.get('rot') is not None:
                self.st.apply_move(ref, part.x, part.y,
                                   float(op['rot']) % 360.0)
            # Evenly distributed along the edge, the way stage 1 does it
            # (seeder.py:439); _seat_edge then slides outward from there
            # until the seat is pad/hole-conflict free.
            frac = (k + 1) / (n + 1)
            tx, ty = seeder._edge_pose(self.st.parts[ref], self.st.board,
                                       op['edge'], frac, overhang)
            ok = seeder._seat_edge(self.st, ref, entry, set(),
                                   self.res.notes, target=(tx, ty))
            if ok:
                self.pending.discard(ref)
                p = self.st.parts[ref]
                self.res.seats.append(Seat(
                    ref=ref, step=step, action='place_edge', target=(tx, ty),
                    pose=(p.x, p.y, p.rot), clearance=self.st.clearance,
                    moved_mm=math.hypot(p.x - tx, p.y - ty),
                    rot_requested=op.get('rot')))
            else:
                self.st.apply_move(ref, *home)
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_edge', target=(tx, ty),
                    reason=f"no conflict-free seat on the {op['edge']} edge "
                           f"band at overhang {overhang:g}mm"))

    def op_place_lock(self, op, step):
        for ref in self.refs(op['refs']):
            if ref not in self.res.lock_refs:
                self.res.lock_refs.append(ref)
        self.res.lock_refs.sort()

    # -- helpers ---------------------------------------------------------
    def refs(self, value, where=None, order=None) -> List[str]:
        return select_refs(value, self.pcb, self.res.indexes, where=where,
                           order=order, groups=self.groups())

    def groups(self) -> Dict[str, List[str]]:
        if self._groups is None:
            from placement.groups import AUTO_SOURCES, derive_groups
            try:
                self._groups = derive_groups(self.pcb, AUTO_SOURCES)
            except Exception:            # a group source is advisory here
                self._groups = {}
        return self._groups

    def _index_of(self, value) -> Optional[Dict]:
        try:
            kind, arg = parse_ref_selector(value)
        except PlanError:
            return None
        return self.res.indexes.get(arg) if kind == 'index' else None


def resolve(pcb_data, pcb_file: str, ops: Sequence[Dict], *,
            clearance: float = 0.25, board_edge_clearance: float = 0.55,
            grid_step: float = 0.1, state=None, deadline=None,
            progress=None) -> ResolveResult:
    """Run a validated placement plan against a board.

    The plan must already have passed `plan_ops.parse_placement_plan`; this
    raises `PlanError` rather than re-validating, because an op that reaches
    here malformed is a caller bug, not an authoring mistake.
    """
    import pose_score
    if state is None:
        state = pose_score.make_state(
            pcb_data, pcb_file, clearance=clearance,
            board_edge_clearance=board_edge_clearance, grid_step=grid_step)
    r = _Resolver(pcb_data, pcb_file, state, deadline=deadline,
                  progress=progress)
    for i, op in enumerate(ops):
        action = op.get('action')
        if action not in RESOLVED_ACTIONS:
            raise PlanError(
                f"step {i + 1}: {action!r} is a valid op that this resolver "
                f"does not execute yet, so nothing was placed. Implemented: "
                f"{', '.join(RESOLVED_ACTIONS)}")
        if progress is not None:
            progress(i + 1, len(ops), action)
        if deadline is not None and deadline.expired():
            r.res.complete = False
            r.res.notes.append(
                f"deadline expired before step {i + 1} ({action}) -- the "
                f"remaining {len(ops) - i} op(s) did not run")
            break
        getattr(r, 'op_' + action)(op, i + 1)
    return r.res
