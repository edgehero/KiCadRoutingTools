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
    'place_index', 'place_at', 'place_array', 'place_slots',
    'place_relative', 'place_edge', 'place_lock',
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
        x, y = (float(v) for v in op['at'])
        mirror = op.get('mirror')
        if mirror:
            # The other half's coordinate, without the author doing the
            # subtraction: arrange.py:189-202 carries thirteen hand-mirrored
            # constants, each one a place the axis could have been mistyped.
            if mirror['axis'] == 'board:xmid':
                x = self._mirror_sum(mirror['axis']) - x
            else:
                y = self._mirror_sum(mirror['axis']) - y
        self.seat(op['ref'], round(x, 4), round(y, 4), step, 'place_at',
                  within=op.get('within'), rot=op.get('rot'),
                  rot_prefer=op.get('rot_prefer'))

    # -- lattices --------------------------------------------------------
    def _mirror_sum(self, axis: str) -> float:
        """`mirror(v) = sum - v`, i.e. reflection about the board's midpoint.

        arrange.py:28 had this as a hand-transcribed constant --
        `MIRROR_X = 17.599913 + 239.1983`, the sum of the board's own x
        bounds, read off the file and typed back in. Read it instead.
        """
        x0, y0, x1, y1 = self.st.board
        return (x0 + x1) if axis == 'board:xmid' else (y0 + y1)

    def _probe_axis(self, spec: Dict, axis: str, fixed: float,
                    members: Sequence[Tuple[str, int]], pitch: float,
                    rot: Optional[float]) -> Optional[float]:
        """Smallest origin at which EVERY member of this lattice line, and
        every declared `also` rect, is fully on the board.

        This is the construct the intent schema could never hold. The
        per-column stagger arrange.py used ({34.0, 28.5, 25.5, 30.0, 39.5},
        arrange.py:85-103) is not a design parameter -- it is a measurement of
        that outline's arcs, and a zone rect can only be authored. Solving it
        here means the plan states the intent ("a column of three, as high as
        this outline allows") and the board supplies the number.

        Rects are taken at the array's declared rotation, or at 0 when it
        declares none: an unplaced pile's rotation is a generator default and
        not a decision (seeder.py:90-96), so probing at it would measure a
        bounding box the lattice never intends to use.
        """
        u = self.st.usable
        lo = u[1] if axis == 'y' else u[0]
        hi = u[3] if axis == 'y' else u[2]
        start = spec.get('from')
        start = lo if start is None else float(start)
        step = float(spec.get('step')
                     or max(0.1, getattr(self.st, 'grid_step', 0.1) or 0.1))
        limit = spec.get('limit')
        limit = int(limit) if limit is not None \
            else max(1, int((hi - lo) / step))
        down = spec.get('direction') == 'down'
        also = spec.get('also') or []
        gate = self.st.edge_gate

        for k in range(limit + 1):
            origin = start - step * k if down else start + step * k
            ok = True
            for ref, n in members:
                part = self.st.parts.get(ref)
                if part is None:
                    continue
                v = origin + pitch * n
                cx, cy = (fixed, v) if axis == 'y' else (v, fixed)
                r = part.rot if rot is None else float(rot) % 360.0
                if gate.rect_outside_amount(part.rect(cx, cy, r)) > 1e-9:
                    ok = False
                    break
                for a in also:
                    ox, oy = a['offset']
                    w, h = a['extent']
                    rect = (cx + ox - w / 2.0, cy + oy - h / 2.0,
                            cx + ox + w / 2.0, cy + oy + h / 2.0)
                    if gate.rect_outside_amount(rect) > 1e-9:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return round(origin, 4)
        return None

    @staticmethod
    def _is_solve(v) -> bool:
        return isinstance(v, str) or isinstance(v, dict)

    @staticmethod
    def _solve_spec(v) -> Dict:
        return {} if isinstance(v, str) else {k: val for k, val in v.items()
                                              if k != 'solve'}

    def _lattice_members(self, op, step, idx, action):
        """(ref, col, row, mirrored) for every member that carries the index
        fields the lattice needs. A member that does not is PARKED with the
        field named -- a lattice cannot position a part it has no index for,
        and quietly defaulting it to 0 stacks the whole board at one seat."""
        ix, iy = op.get('index_x'), op.get('index_y')
        mirror = op.get('mirror')
        out = []
        for ref in self.refs(op['refs'], op.get('where'), op.get('order')):
            row = (idx['members'].get(ref, {}) if idx else {})
            vals = {}
            missing = None
            for name, key in (('index_x', ix), ('index_y', iy)):
                if key is None:
                    vals[name] = 0
                    continue
                v = row.get(key)
                if v is None:
                    missing = key
                    break
                vals[name] = v
            if missing is not None:
                self.res.parks.append(Park(
                    ref=ref, step=step, action=action,
                    reason=f"the index gives it no {missing!r}, so this "
                           f"lattice has no position for it"))
                continue
            mirrored = bool(mirror and _passes(row, mirror.get('when'))) \
                if mirror else False
            out.append((ref, vals['index_x'], vals['index_y'], mirrored))
        return out

    def op_place_array(self, op, step):
        idx = self._index_of(op['refs'])
        members = self._lattice_members(op, step, idx, 'place_array')
        if not members:
            return
        px, py = (float(v) for v in op['pitch'])
        origin = op['origin']
        rot = op.get('rot')
        mirror = op.get('mirror')
        msum = self._mirror_sum(mirror['axis']) if mirror else 0.0

        ox_spec, oy_spec = origin.get('x'), origin.get('y')
        if self._is_solve(ox_spec) and self._is_solve(oy_spec):
            raise PlanError(
                f"step {step} (place_array): both origin axes ask to be "
                f"solved, which is not a lattice -- solve one against the "
                f"outline and state the other")

        # A solved axis is solved PER LINE of the other index, which is what
        # makes it a stagger rather than one number: arrange.py probed a y0
        # for each column separately, against that column's own x.
        solved: Dict[Any, Optional[float]] = {}
        for ref, col, row, mirrored in members:
            if self._is_solve(oy_spec):
                x = float(ox_spec) + px * col
                if mirrored:
                    x = msum - x
                key = (mirrored, col)
                if key not in solved:
                    line = [(r2, rw2) for r2, c2, rw2, m2 in members
                            if c2 == col and m2 == mirrored]
                    solved[key] = self._probe_axis(
                        self._solve_spec(oy_spec), 'y', x, line, py, rot)
            elif self._is_solve(ox_spec):
                y = float(oy_spec) + py * row
                key = (mirrored, row)
                if key not in solved:
                    line = [(r2, c2) for r2, c2, rw2, m2 in members
                            if rw2 == row and m2 == mirrored]
                    solved[key] = self._probe_axis(
                        self._solve_spec(ox_spec), 'x', y, line, px, rot)

        for ref, col, row, mirrored in members:
            if self._is_solve(oy_spec):
                x = float(ox_spec) + px * col
                if mirrored:
                    x = msum - x
                base = solved.get((mirrored, col))
                if base is None:
                    self.res.parks.append(Park(
                        ref=ref, step=step, action='place_array',
                        reason=f"no origin on this outline puts every member "
                               f"of {'mirrored ' if mirrored else ''}line "
                               f"{col} fully on the board"))
                    continue
                y = base + py * row
            elif self._is_solve(ox_spec):
                y = float(oy_spec) + py * row
                base = solved.get((mirrored, row))
                if base is None:
                    self.res.parks.append(Park(
                        ref=ref, step=step, action='place_array',
                        reason=f"no origin on this outline puts every member "
                               f"of {'mirrored ' if mirrored else ''}line "
                               f"{row} fully on the board"))
                    continue
                x = base + px * col
                if mirrored:
                    x = msum - x
            else:
                x = float(ox_spec) + px * col
                y = float(oy_spec) + py * row
                if mirrored:
                    x = msum - x
            self.seat(ref, round(x, 4), round(y, 4), step, 'place_array',
                      within=op.get('within'), rot=rot,
                      rot_prefer=op.get('rot_prefer'))

    def op_place_slots(self, op, step):
        """Named irregular pockets, handed out by a stated rule.

        arrange.py:121-132 is the shape: two thumb coordinates, and the rule
        "per half, the thumb on the HIGHER column takes the inner slot". The
        slots are a fact about the outline; the assignment is a decision, and
        both belong in the plan rather than in a zip() nobody can review.
        """
        idx = self._index_of(op['refs'])
        refs = self.refs(op['refs'], op.get('where'), op.get('order'))
        slots = [(float(a), float(b)) for a, b in op['slots']]
        mirror = op.get('mirror')
        msum = self._mirror_sum(mirror['axis']) if mirror else 0.0
        group_by = op.get('group_by')

        buckets: Dict[Any, List[str]] = {}
        for ref in refs:
            row = (idx['members'].get(ref, {}) if idx else {})
            key = tuple(row.get(g[1:] if g.startswith('-') else g)
                        for g in (group_by or ()))
            buckets.setdefault(key, []).append(ref)

        for key in sorted(buckets, key=lambda k: tuple(
                (v is None, str(v)) for v in k)):
            group = buckets[key]
            if len(group) > len(slots):
                for ref in group[len(slots):]:
                    self.res.parks.append(Park(
                        ref=ref, step=step, action='place_slots',
                        reason=f"only {len(slots)} slot(s) declared for "
                               f"{len(group)} member(s) in this group"))
            for ref, (sx, sy) in zip(group, slots):
                row = (idx['members'].get(ref, {}) if idx else {})
                mirrored = bool(mirror
                                and _passes(row, mirror.get('when'))) \
                    if mirror else False
                x = msum - sx if mirrored else sx
                self.seat(ref, round(x, 4), round(sy, 4), step, 'place_slots',
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
