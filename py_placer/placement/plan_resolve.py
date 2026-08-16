"""Execute a placement plan: statements in, seated poses out.

Almost every op resolves to `seeder._try_place` calls, which is what makes
this cheap: the target a plan states is a HINT, and `_try_place` returns the
nearest FULLY-CONTAINED legal pose to it, trying the requested rotation in
full before the rest of the 90-degree lattice, and relaxing courtyard
clearance in three steps before giving up. So legality, the rotation
fallback, the clearance ladder and the pile-exclusion rule all behave exactly
as they do for `seed_from_intent`.

That is NOT the same as "a plan cannot author an illegal board", which this
docstring claimed until it was measured and found false. `_try_place` only
avoids what it is given as an obstacle, and the pile-exclusion rule used to
hide every unlocked part, so `place_at R1` at U1's exact coordinate seated at
0.0mm and reported `complete: true` on a board `check_assembly` graded NOT
BUILDABLE. Unnamed parts at a distinct pose are obstacles now (see
`_Resolver.__init__`), but two holes remain, both real: `place_edge` bypasses
`_try_place` entirely (below), and a PARKED part keeps its incoming pose,
which on a pile is the middle of the board. Grade the output; do not trust
`complete: true` to mean legal.

`place_edge` is THE EXCEPTION, and it has to be: an edge connector overhangs
the outline by design, and `_try_place` demands full containment, so it would
refuse every legal edge seat. It uses `seeder._seat_edge` instead -- the same
helper stage 1 of `seed_from_intent` uses. It takes the SAME exclude set every
other seat uses (`self.pending - {ref}`), so an unplaced pile cannot veto an
honest edge pose -- it used to take none, and the pile pushed connectors along
the edge until one was "free", which is how one ended up 26mm away and off the
board. Its seat is checked by `seeder.edge_seat_ok` (the declared band, and a
bound of half the part's own depth so a wrong band cannot buy an off-board
pose) rather than by `pose_ok`, and it runs no clearance ladder, so an edge
Seat reports `clearance: None` rather than a number nothing measured.

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
from placement.plan_ops import (PLACEMENT_ACTIONS, UNIMPLEMENTED_ACTIONS,
                                PlanError, parse_ref_selector)

# Implemented so far. An op outside this set refuses by name rather than
# being skipped -- see the module docstring.
# Derived, never hand-listed: a second list would drift from the validator's,
# and then the authoring contract would advertise an op that refuses.
RESOLVED_ACTIONS = tuple(a for a in PLACEMENT_ACTIONS
                         if a not in UNIMPLEMENTED_ACTIONS)

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
    # None when the op did not run a clearance ladder (place_edge). Reporting
    # the state's nominal clearance there would be a number nothing measured,
    # and `summary()['relaxed']` would never be able to see an edge seat.
    clearance: Optional[float]
    moved_mm: float
    rot_requested: Optional[float] = None
    rot_changed: bool = False

    def to_dict(self) -> Dict:
        return {'ref': self.ref, 'step': self.step, 'action': self.action,
                'target': [round(v, 4) for v in self.target],
                'pose': [round(v, 4) for v in self.pose],
                'clearance': (None if self.clearance is None
                              else round(self.clearance, 4)),
                'moved_mm': round(self.moved_mm, 4),
                'rot_requested': self.rot_requested,
                'rot_changed': self.rot_changed}


@dataclass
class Park:
    """One part the plan named and could not seat.

    `blockers` is `{ref: poses_available_with_that_ref_lifted}` (issue #629's
    shape), censused at the seat that failed -- not only by `place_lift`,
    which used to be the sole source and left every ordinary park a dead end
    with `blockers: {}`. `censused` is separate because an empty `blockers`
    has two meanings: "nothing movable is near" (censused) and "nothing was
    measured" (not). Non-geometric parks -- not a movable part, file-locked,
    no target on record -- are never censused, and correctly report False."""
    ref: str
    step: int
    action: str
    reason: str
    target: Optional[Tuple[float, float]] = None
    within: Optional[float] = None
    blockers: Dict[str, int] = field(default_factory=dict)
    censused: bool = False
    # Poses available with NOTHING lifted. `blockers` values are ABSOLUTE
    # counts with that one blocker lifted, not deltas, so without this a
    # reader cannot tell "46" from an improvement -- the seeder's own
    # no_pose_blockers has the same shape and keeps its baseline in a
    # different structure entirely (`evictions[].poses_before`).
    baseline_poses: Optional[int] = None
    #: The lattice `baseline_poses` and `blockers` were counted on. A census
    #: is commensurate WITHIN itself (one window for the baseline and every
    #: blocker) and NOT across budgets: a coarser lattice counts fewer poses
    #: over more ground. Reported so a reader compares the right things --
    #: 253 at 0.1mm and 113 at 0.25mm are not a decrease.
    census_step_mm: Optional[float] = None
    #: How far the census actually looked. SMALLER than `within` means the
    #: sweep was capped and the counts describe the NEAR FIELD only -- a
    #: bounded census with its bound stated, rather than an unbounded one
    #: (`within: 500` built a 1,002,001-offset disc, ~72MB, before probing a
    #: single pose) or a silent truncation.
    census_radius_mm: Optional[float] = None
    #: The zone this seat had to satisfy, if any, and its tolerance. Carried
    #: for two reasons. It makes the counts READABLE -- a count under a
    #: constraint is not comparable to an unconstrained one, so the zone
    #: belongs beside `census_step_mm`. And it makes them RECOVERABLE:
    #: `place_lift` retries a part an earlier op parked, and with no zone on
    #: the record it retried unconstrained and wrote the part outside the
    #: zone its own plan had confined it to, then reported a seat.
    constraint: Optional[Tuple[float, float, float, float]] = None
    tol: Optional[float] = None

    def to_dict(self) -> Dict:
        return {'ref': self.ref, 'step': self.step, 'action': self.action,
                'reason': self.reason,
                'target': None if self.target is None
                else [round(v, 4) for v in self.target],
                'within': self.within,
                'blockers': dict(self.blockers), 'censused': self.censused,
                'baseline_poses': self.baseline_poses,
                'census_step_mm': self.census_step_mm,
                'census_radius_mm': self.census_radius_mm,
                'constraint': (None if self.constraint is None
                               else [round(v, 4) for v in self.constraint]),
                'tol': self.tol}


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
                'unmeasured_clearance': sum(1 for s in self.seats
                                            if s.clearance is None),
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
        # An index field is not type-homogeneous by construction: `map`
        # values are unconstrained and `partner.inherit` can overwrite one
        # member's field with a differently-typed partner value. Sorting a
        # mixed column used to raise straight out of resolve(); numbers sort
        # before strings, and neither raises.
        if missing:
            key.append((2, 0.0, ''))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            num = float(v)
            key.append((0, -num if desc else num, ''))
        else:
            t = str(v)
            key.append((1, 0.0, _Neg(t) if desc else t))
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
                 progress=None, plan_refs=None, census_parks=True,
                 fixed_refs=None):
        self.pcb = pcb_data
        self.pcb_file = pcb_file
        self.st = state
        self.deadline = deadline
        self.progress = progress
        self.census_parks = census_parks
        self.res = ResolveResult()
        # The pile: parts THIS PLAN will seat and has not seated yet. They are
        # passed as `exclude` so their meaningless input coordinates cannot
        # veto a real pose -- seed_from_intent's own rule (seeder.py:78-79).
        #
        # `plan_refs` is what makes that rule safe here, and omitting it was a
        # correctness bug: seed_from_intent owns the WHOLE board, so "every
        # unlocked part" and "every part I am about to place" are the same
        # set. A plan does not own the whole board -- it also repairs an
        # existing placement -- and there every part it does NOT name sits at
        # an authoritative pose. Excluding those made them invisible, so
        # `place_at R1` at U1's exact coordinate seated at 0.0mm and reported
        # `complete: true` while check_assembly graded the board NOT BUILDABLE
        # (COINCIDENT ORIGINS). A part this plan will never move is an
        # obstacle, whatever its pose means.
        #
        # Which unnamed parts are authoritative is decided PER PART, not by a
        # whole-board placed/unplaced verdict. A part sharing an exact origin
        # with another is piled -- its coordinate is an artifact of staging,
        # and check_assembly grades exact coincidence NOT BUILDABLE, so it is
        # never a real placement. A part alone at its origin is where someone
        # put it. This keeps a genuine pile behaving exactly as before (every
        # part stacked at one point stays excluded) while a placed board's
        # untouched parts become the obstacles they are.
        #
        # A part locked in the FILE is authoritatively placed and never here.
        movable = {r for r, p in state.parts.items() if not p.locked}
        if plan_refs is None:
            self.pending: Set[str] = movable
        else:
            seen: Dict[Tuple[float, float], int] = {}
            for p in state.parts.values():
                key = (round(p.x, 4), round(p.y, 4))
                seen[key] = seen.get(key, 0) + 1
            piled = {r for r, p in state.parts.items()
                     if seen.get((round(p.x, 4), round(p.y, 4)), 0) > 1}
            # A place_fixed ref is NEVER in the pile set, even when it shares
            # the pile's coordinate. On a pile every part is `piled`, so the
            # plan_target_refs skip was inert exactly where this op matters:
            # an op running BEFORE the place_fixed saw it as invisible and
            # could seat on top of it, producing the COINCIDENT ORIGINS /
            # NOT BUILDABLE shape this module's docstring says was fixed.
            self.pending = (movable & (set(plan_refs) | piled)) - set(
                fixed_refs or ())
        self._groups: Optional[Dict[str, List[str]]] = None
        # Declared by place_keepout, honoured by every seat AFTER it.
        self.keepouts: List[Tuple] = []
        # Asserted by place_fixed. These are mechanical facts, so nothing --
        # including place_lift, which otherwise moves anything movable -- may
        # relocate them. Without this, lifting a fixed part wrote it 4mm away
        # and reported `complete: true` with no note.
        self.fixed_refs: Set[str] = set(fixed_refs or ())
        # Refs place_fixed has actually asserted SO FAR. Distinct from
        # `fixed_refs`, which is pre-populated from the whole plan so a fixed
        # part is an obstacle before its own step -- using that as the
        # "already asserted" test made the FIRST assertion refuse itself.
        self.asserted_refs: Set[str] = set()

    # -- seating ---------------------------------------------------------
    def seat(self, ref: str, tx: float, ty: float, step: int, action: str,
             *, within: Optional[float] = None, rot=None, rot_prefer=None,
             constraint=None, tol: float = 0.5, census: bool = True) -> bool:
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
        if ref in self.asserted_refs:
            # place_fixed's contract is "never moves that part", and this is
            # where that has to be enforced: `seat()` checked `part.locked`
            # and nothing else, so place_at / place_array / place_slots /
            # place_edge / a second place_fixed all moved an asserted pose,
            # emitted a SECOND Seat for the same ref, and reported
            # `complete: true` with no note. `placements` is in seating order,
            # so the writer applied the later pose -- the assertion silently
            # lost to a later op. Only place_lift refused, because it was the
            # only one given a check.
            self.res.parks.append(Park(
                ref=ref, step=step, action=action,
                reason='was asserted by place_fixed as a mechanical fact, so '
                       'no later op may move it -- drop the place_fixed if '
                       'the pose is really negotiable'))
            return False

        home = (part.x, part.y, part.rot)
        # `_try_place` tries the part's CURRENT rotation in full before the
        # rest of its lattice, so a requested angle is applied first and is
        # therefore what gets searched first. That is the whole mechanism for
        # `rot`, and it is why the intent schema -- which has no rotation --
        # could never express one (seeder.py:26-32).
        angles: List[Optional[float]] = list(rot_prefer) if rot_prefer \
            else [rot]
        # A part's legality geometry exists only at the angles in
        # `bounds_by_rot` (its 90-degree lattice plus its own base angle).
        # `_Part.rect` silently falls back to the 0-degree box for anything
        # else, so a plan asking for 45 degrees was checked against the wrong
        # courtyard and written off the board at exit 0. Refuse the angle
        # instead, and name the ones that exist.
        have = getattr(part, 'bounds_by_rot', None) or {}
        bad = [a for a in angles
               if a is not None and float(a) % 360.0 not in have]
        if bad and have:
            self.res.parks.append(Park(
                ref=ref, step=step, action=action, target=(tx, ty),
                within=within,
                constraint=(tuple(constraint) if constraint is not None
                            else None),
                tol=(tol if constraint is not None else None),
                reason=f"rotation(s) {sorted(set(bad))} are not in this "
                       f"part's legality lattice {sorted(have)}, so no "
                       f"courtyard exists to check them against"))
            return False
        info: Dict = {}
        for angle in angles:
            if angle is not None:
                self.st.apply_move(ref, part.x, part.y, float(angle) % 360.0)
            info = {}
            clr = seeder._try_place(self.st, ref, tx, ty, self.pending - {ref},
                                    constraint=constraint, tol=tol,
                                    max_disp=within, info=info,
                                    deadline=self.deadline,
                                    forbid=self.keepouts)
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
                constraint=(tuple(constraint) if constraint is not None
                            else None),
                tol=(tol if constraint is not None else None),
                reason='the deadline expired during this search -- nothing '
                       'was measured'))
            return False
        budget = f"within {within:g}mm of " if within is not None else "near "
        park = Park(
            ref=ref, step=step, action=action, target=(tx, ty), within=within,
            reason=f"no legal pose {budget}({tx:.1f}, {ty:.1f})",
            constraint=(tuple(constraint) if constraint is not None else None),
            tol=(tol if constraint is not None else None))
        # `census=False` is for a caller that has ALREADY censused this seat
        # and will fill the Park itself. Censusing again here would measure a
        # different board: `_census` derives its candidates and its baseline
        # from `self.pending`, which `place_lift` has just added the lifted
        # blockers to. That produced a Park whose `blockers` came from before
        # the lift and whose `baseline_poses` and reason sentence came from
        # after it -- two board states, two resolutions, one record.
        if census:
            self._census(park, ref, tx, ty, within, constraint, tol)
        self.res.parks.append(park)
        return False

    def _census(self, park, ref, tx, ty, within, constraint=None, tol=0.5):
        """Which movable neighbours are in this part's way, and what lifting
        each would free.

        Without this a park is a dead end: `place_lift` -- the op whose whole
        job is evicting a blocker -- required the author to GUESS which part
        to lift, and a wrong guess returns the honest but useless "lifting
        C22, C35 frees no pose either, so they are not what is in the way".
        The machinery already existed for the seeder's stage 3c (issue #629);
        this is the plan path using it.

        Bounded on purpose. `count_legal_poses` sweeps 4356 poses per call at
        the default radius, measured at 1.10s when the cap fires and 2.64s
        when the count is 0 -- and a genuinely blocked part has baseline 0, so
        it is the slow case that always applies. `max_disp` prunes by the
        op's own budget (`seeder.py:212` skips offsets beyond it with a bare
        hypot), which is what makes this affordable; `place_lift` already
        does the same. `censused` stays False when nothing was measured, so
        an empty `blockers` never reads as "nothing is in the way".
        """
        if not self.census_parks:
            return
        if self.deadline is not None and self.deadline.expired():
            return
        try:
            base = self.pending - {ref}
            cands = seeder._evict_candidates(
                self.st, ref, tx, ty,
                {r for r in self.st.parts if r not in self.pending},
                set(self.res.lock_refs), constraint=constraint, tol=tol)
            if not cands:
                park.censused = True          # measured: nothing movable near
                return
            # SAMPLE THE BUDGET ON A LATTICE THE SEAT SEARCH ACTUALLY VISITS.
            # `census_window` owns both halves of that (see its docstring);
            # what matters here is that ONE window is used for the baseline
            # and every blocker, so the numbers below are commensurate with
            # each other whatever budget the op carried.
            radius, step = seeder.census_window(
                within, getattr(self.st, 'grid_step', 0.1))
            kw = dict(max_disp=within, radius=radius, step=step,
                      forbid=self.keepouts, constraint=constraint, tol=tol)
            if constraint is not None:
                # The zone supersedes the disc, so report the window the
                # census really used rather than the one it did not --
                # including how far it actually got, which is NOT `within`
                # when the zone is far or the location cap bites.
                step, _offs, radius = seeder.zone_census_offsets(
                    self.st.parts[ref], constraint, tol, tx, ty,
                    getattr(self.st, 'grid_step', 0.1), within)
            baseline = seeder.count_legal_poses(
                self.st, ref, tx, ty, base, **kw)
            freed = {}
            for b in cands:
                freed[b] = seeder.count_legal_poses(
                    self.st, ref, tx, ty, base | {b}, **kw)
            park.blockers = dict(freed)
            park.baseline_poses = baseline
            park.census_step_mm = step
            park.census_radius_mm = radius
            park.censused = True
            if constraint is not None:
                # Say the counts are zone-scoped, or a reader compares them
                # with an unconstrained park's and concludes the board got
                # fuller. This is also the sentence that separates "the board
                # is full" from "your zone is full" -- the capacity note the
                # pack op emits answers the second, and these counts must not
                # look like an answer to the first.
                park.reason += (
                    f"; counted INSIDE the zone "
                    f"[{constraint[0]:g}, {constraint[1]:g}, "
                    f"{constraint[2]:g}, {constraint[3]:g}] (tol {tol:g}) -- "
                    f"poses outside it were never candidates")
                if not radius:
                    # The one actionable fact when the sweep never left the
                    # target: the budget cannot reach the zone from here, so
                    # an all-zero census says nothing about the zone at all.
                    park.reason += (
                        "; and the sweep never left the target -- this "
                        "budget cannot reach that zone from this target, so "
                        "the zero says nothing about what is in the way")
                elif within is not None and radius < within - 1e-9:
                    park.reason += (
                        f"; the sweep reached {radius:g}mm of the "
                        f"{within:g}mm budget, so these are near-field counts")
            elif within is not None and radius is not None \
                    and radius < within - 1e-9:
                park.reason += (
                    f"; the census looked {radius:g}mm out, not the full "
                    f"{within:g}mm -- these counts are the near field")
            useful = sorted(((n, b) for b, n in freed.items() if n > baseline),
                            reverse=True)
            if useful:
                park.reason += (
                    f"; lifting {useful[0][1]} would free {useful[0][0]} pose(s) "
                    f"(none are free now)" if baseline == 0 else
                    f"; lifting {useful[0][1]} would take it from {baseline} to "
                    f"{useful[0][0]} pose(s)")
        except Exception as e:                           # noqa: BLE001
            # A census is a diagnostic. It must never turn a park into a crash.
            self.res.notes.append(
                f"{ref}: the blocker census did not run "
                f"({type(e).__name__}: {e})")

    # -- ops -------------------------------------------------------------
    def op_place_index(self, op, step):
        self.res.indexes[op['name']] = _build_index(
            self.pcb, op, self.res.indexes, self.res.notes)

    def op_place_fixed(self, op, step):
        """Assert a pose as a mechanical fact. Set it; never search.

        On a PILE, a mounting hole or an edge receptacle has no meaningful
        pose, and there was no way to tell the plan where it belongs:
        `place_at H1` at its own coordinate is refused at `within: 0`
        ("must be > 0mm"), parks at 0.1, and at 3.0 MOVES THE HOLE 1.4mm --
        a hole is not a request. `place_lock` pins a part where it already
        is, which on a pile is the centre of the board.

        So this is the one op that does not go through a seat gate at all.
        It is a declaration of something the board's mechanical drawing
        already fixed, and the plan is not entitled to move it. It is
        reported as a Seat with `clearance: None` -- nothing measured one --
        and it is excluded from the plan's movable set, so every later op
        sees it as an obstacle (`plan_target_refs` skips it exactly as it
        skips `place_lock`; without that a fixed part is INVISIBLE, which is
        the defect `tests/test_plan_obstacles.py` pins).

        Ordering matters and the schema says so: put these first. Until this
        op runs the part sits at its incoming pose, which on a pile is the
        middle of the board -- an obstacle in the wrong place.
        """
        ref = op['ref']
        if ref not in self.st.parts:
            self.res.parks.append(Park(
                ref=ref, step=step, action='place_fixed',
                reason='not a movable part on this board'))
            return
        x, y = (float(v) for v in op['at'])
        part = self.st.parts[ref]
        rot = float(op['rot']) % 360.0 if op.get('rot') is not None else part.rot
        home = (part.x, part.y)

        # A second assertion of the same ref is a contradiction, not an
        # update: this op does not go through `seat()`, so without this a
        # later place_fixed moved an earlier one and wrote the ref twice.
        # NOTE `asserted_refs`, not `fixed_refs`. The latter is pre-populated
        # from the whole plan so a fixed part is an obstacle before its own
        # step; testing it here made the FIRST assertion refuse itself, and
        # the op then produced neither a seat nor a park -- silently nothing.
        if ref in self.asserted_refs:
            if abs(part.x - x) > 1e-6 or abs(part.y - y) > 1e-6 \
                    or abs(((part.rot - rot) + 180.0) % 360.0 - 180.0) > 1e-6:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_fixed', target=(x, y),
                    reason=f"was already asserted at ({part.x:g}, {part.y:g}) "
                           f"rot {part.rot:g}; a mechanical fact cannot be "
                           f"restated differently in the same plan"))
            return

        # A rotation outside the part's legality lattice has NO courtyard to
        # check, so `part.rect` silently returns the 0-degree box. `seat()`
        # guards this ("a plan asking for 45 degrees was checked against the
        # wrong courtyard and written off the board at exit 0") and this op
        # skipped the guard: rot 45 seated silently, the legality note below
        # graded a shape the part does not have, and every later op then
        # treated it as an obstacle with that wrong shape. 45 degrees is the
        # edge-receptacle case this op exists for.
        have = getattr(part, 'bounds_by_rot', None) or {}
        if have and rot % 360.0 not in have:
            self.res.parks.append(Park(
                ref=ref, step=step, action='place_fixed', target=(x, y),
                reason=f"rotation {rot:g} is not in this part's legality "
                       f"lattice {sorted(have)}, so no courtyard exists to "
                       f"check it -- a fixed pose is asserted, not searched, "
                       f"so an unverifiable one is refused rather than "
                       f"written"))
            return

        # A KiCad-locked part is not this tool's to move, and place_fixed is
        # not an exemption -- `place_at` and `place_lift` both refuse one. But
        # ASSERTING the pose it already has is a legitimate no-op: it is how a
        # plan states the mechanical fact explicitly.
        if getattr(part, 'locked', False):
            if abs(part.x - x) > 1e-3 or abs(part.y - y) > 1e-3 \
                    or abs(((part.rot - rot) + 180.0) % 360.0 - 180.0) > 1e-3:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_fixed', target=(x, y),
                    reason=f"is (locked yes) in the file at "
                           f"({part.x:g}, {part.y:g}) rot {part.rot:g} -- not "
                           f"this tool's to move, and place_fixed is not an "
                           f"exemption. Assert its EXISTING pose, or unlock it "
                           f"in KiCad"))
                return
            self.res.notes.append(
                f"{ref}: is (locked yes) and already at the asserted pose; "
                f"place_fixed recorded it and moved nothing")
        self.st.apply_move(ref, round(x, 4), round(y, 4), rot)
        self.pending.discard(ref)
        self.fixed_refs.add(ref)
        self.asserted_refs.add(ref)
        p = self.st.parts[ref]
        self.res.seats.append(Seat(
            ref=ref, step=step, action='place_fixed', target=(x, y),
            pose=(p.x, p.y, p.rot), clearance=None,
            moved_mm=math.hypot(p.x - home[0], p.y - home[1]),
            rot_requested=op.get('rot')))
        # A fixed pose can still be illegal -- it is asserted, not checked --
        # so say when it is, rather than letting the board carry a silent
        # overlap that every later op then routes around.
        if not seeder.pose_ok(self.st, ref, p.x, p.y, p.rot,
                              self.pending - {ref}, forbid=self.keepouts):
            # Name WHAT it collides with. "not a legal pose" alone leaves the
            # author to find the other part by eye, and the commonest cause is
            # a part this same plan already seated there.
            hits = []
            mine = p.rect(p.x, p.y, p.rot)
            for other, op_part in self.st.parts.items():
                if other == ref or other in self.pending:
                    continue
                r2 = op_part.rect(op_part.x, op_part.y, op_part.rot)
                if (min(mine[2], r2[2]) - max(mine[0], r2[0]) > 0
                        and min(mine[3], r2[3]) - max(mine[1], r2[1]) > 0):
                    hits.append(other)
            where = (f" It overlaps {', '.join(sorted(hits)[:4])}."
                     if hits else
                     " Nothing overlaps it, so the outline or a keepout is "
                     "what refuses it.")
            self.res.notes.append(
                f"{ref}: fixed at ({p.x:g}, {p.y:g}) rot {p.rot:g}, which is "
                f"not a legal pose on this board -- asserted anyway, because a "
                f"mechanical fact outranks the seat gate.{where} Grade the "
                f"output.")

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
    @staticmethod
    def _mirror_xy(axis: str, x: float, y: float, msum: float):
        """Reflect the coordinate the axis actually names.

        `board:ymid` used to reflect X in the lattice ops (only `place_at`
        branched correctly), so a y-mirror mixed the board's y-bounds sum into
        an x coordinate.
        """
        if axis == 'board:xmid':
            return msum - x, y
        return x, msum - y

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
                    rot: Optional[float],
                    mirror_sum: Optional[float] = None) -> Optional[float]:
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
                # A mirrored line must be PROBED on the side it will land on.
                # Solving on the unmirrored side and reflecting the answer
                # afterwards validates against the wrong geometry the moment
                # the outline is not symmetric.
                if mirror_sum is not None:
                    v = mirror_sum - v
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
                    x, _ = self._mirror_xy(mirror['axis'], x, 0.0, msum)
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
                        self._solve_spec(ox_spec), 'x', y, line, px, rot,
                        mirror_sum=msum if mirrored else None)

        for ref, col, row, mirrored in members:
            if self._is_solve(oy_spec):
                x = float(ox_spec) + px * col
                if mirrored:
                    x, _ = self._mirror_xy(mirror['axis'], x, 0.0, msum)
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
                # `_probe_axis` was given `mirror_sum`, so it TESTED the
                # mirrored side while returning the origin in unmirrored
                # space -- the reflection therefore still happens here, once.
                x = base + px * col
                if mirrored:
                    x, _ = self._mirror_xy(mirror['axis'], x, 0.0, msum)
            else:
                x = float(ox_spec) + px * col
                y = float(oy_spec) + py * row
                if mirrored:
                    x, y = self._mirror_xy(mirror['axis'], x, y, msum)
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
                x, y = ((sx, sy) if not mirrored
                        else self._mirror_xy(mirror['axis'], sx, sy, msum))
                self.seat(ref, round(x, 4), round(y, 4), step, 'place_slots',
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
            if ref in self.asserted_refs:
                # place_edge does not go through `seat()`, so it needs the
                # same guard: without it, an edge op moved an asserted
                # mechanical fact 42mm and wrote the ref twice.
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_edge',
                    reason='was asserted by place_fixed as a mechanical fact, '
                           'so no later op may move it'))
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
            # Pass the SAME exclude set every other seat uses. The `set()`
            # that used to sit here landed in the `must_lock` slot, which
            # _seat_edge ignores -- so the pile was a full obstacle set and
            # vetoed the honest edge poses, sliding the part along the edge.
            ok = seeder._seat_edge(self.st, ref, entry, set(),
                                   self.res.notes, target=(tx, ty),
                                   exclude=self.pending - {ref})
            if ok:
                self.pending.discard(ref)
                p = self.st.parts[ref]
                self.res.seats.append(Seat(
                    ref=ref, step=step, action='place_edge', target=(tx, ty),
                    pose=(p.x, p.y, p.rot), clearance=None,
                    moved_mm=math.hypot(p.x - tx, p.y - ty),
                    rot_requested=op.get('rot')))
            else:
                self.st.apply_move(ref, *home)
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_edge', target=(tx, ty),
                    reason=f"no conflict-free seat on the {op['edge']} edge "
                           f"band at overhang {overhang:g}mm"))

    def op_place_lift(self, op, step):
        """Evict named blockers, seat what they were blocking, put them back.

        THE ORDERING IS THE WHOLE OP. `reseat_scope` already lifts a set and
        re-seats it, and run 19 called it three times on exactly this case and
        got a null every time -- because its queue re-seated the blockers
        first, at their net centroids, which is back into the very pockets
        they block, and the blocked switches then swept against a re-blocked
        board. `apply_c2_seats.py:1-12` records that measurement. So here the
        blocked part is seated FIRST, against a board the blockers are lifted
        out of, and the blockers are re-seated afterwards with it as an
        obstacle.

        Each retry is censused before anything moves (issue #629): how many
        poses the blocked part has now, and how many with each blocker lifted
        on its own. That is what turns "no legal pose" into "D14 is why".
        """
        blockers = self.refs(op['refs'])
        blocked = self.refs(op['for']) if op.get('for') is not None else []
        within = op.get('within')
        restore = op.get('restore', True)

        both = sorted(set(blockers) & set(blocked))
        if both:
            # Lifting a part to make room for itself is not a trade, and the
            # census would compare it against its own absence.
            for ref in both:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_lift',
                    reason='named as both a blocker (refs) and a blocked part '
                           '(for) -- it cannot make room for itself'))
            return

        movable = []
        for b in blockers:
            part = self.st.parts.get(b)
            if part is None:
                self.res.parks.append(Park(
                    ref=b, step=step, action='place_lift',
                    reason='not a movable part on this board'))
                continue
            if part.locked:
                # Naming the source matters: a ref locked by the FILE and one
                # locked by this run are different problems for the reader.
                self.res.parks.append(Park(
                    ref=b, step=step, action='place_lift',
                    reason="(locked yes) in the file -- not this tool's to "
                           "move, so it cannot be lifted either"))
                continue
            if b in self.fixed_refs:
                # A place_fixed pose is a mechanical fact. Lifting one wrote
                # it 4.000mm from where it was asserted, emitted TWO
                # placements for the same ref (the writer applies the last),
                # and reported `complete: true` with no note -- the plan's own
                # declaration silently overridden by a later op. The
                # still-in-the-pile guard below could not catch it, because
                # op_place_fixed removes the ref from `pending`.
                self.res.parks.append(Park(
                    ref=b, step=step, action='place_lift',
                    reason='was asserted by place_fixed as a mechanical fact, '
                           'so it cannot be lifted -- state a different '
                           'blocker, or drop the place_fixed if the pose is '
                           'really negotiable'))
                continue
            if b in self.pending:
                # It is still in the pile, so it is not in anyone's way and
                # there is nothing to lift. Censusing it would also be
                # tautological: the count with it excluded is the count it
                # already had, so "lifting it frees no pose" could not have
                # come out any other way. Restoring it would additionally
                # SEAT a part this plan never asked to place.
                self.res.parks.append(Park(
                    ref=b, step=step, action='place_lift',
                    reason='not seated by this plan, so it is not an '
                           'obstacle and lifting it would measure nothing'))
                continue
            movable.append(b)
        if not movable:
            return

        # Retry targets come from the earlier op that parked them: the plan
        # says WHICH parts are blocked, and where they were meant to go is
        # already on the record.
        #
        # THE ZONE IS PART OF "WHERE IT WAS MEANT TO GO". Carrying only
        # (target, within) meant the retry re-seated without the constraint
        # the original op imposed, so a part `place_pack` had confined to a
        # zone was written OUTSIDE it and reported as a seat -- measured on
        # splitflap_driver, R1 landed 3.86mm clear of its zone with a note
        # crediting a lift that had freed nothing (64 poses before, 64
        # after). That is a wrong board, not a wrong number.
        # FIRST-WINS, EXCEPT A CONSTRAINT UPGRADES. First-wins was pure
        # bookkeeping while the tuple was (target, within); with a zone on it
        # it became a correctness choice, and the wrong one -- a `place_at`
        # that parked the ref earlier with no zone silently outranked the
        # `place_pack` that later demanded one, so the retry ran
        # unconstrained and seated the part 4.5mm outside the zone with no
        # record that a zone was ever asked for. A later park that carries a
        # constraint is a more specific statement of where the part must go,
        # so it replaces an unconstrained incumbent.
        parked_at = {}
        for p in self.res.parks:
            if p.target is None:
                continue
            prev = parked_at.get(p.ref)
            if prev is not None and not (prev[2] is None
                                         and p.constraint is not None):
                continue
            parked_at[p.ref] = (p.target, p.within, p.constraint,
                                p.tol if p.tol is not None else 0.5)

        # Census BEFORE anything moves, so the numbers describe the board the
        # plan actually met.
        #
        # Deliberately NOT gated on `self.census_parks`, which `_census`
        # honours. That flag turns off the AUTOMATIC census on ordinary
        # parks; `place_lift` is an author explicitly asking which of these
        # named parts is in the way, and answering "measurement disabled" to
        # a request to measure would make the op useless. The cost is
        # bounded the same way -- `census_window` caps the sweep.
        census: Dict[str, Dict[str, int]] = {}
        baseline: Dict[str, int] = {}
        census_step: Dict[str, float] = {}
        census_radius: Dict[str, float] = {}
        for ref in blocked:
            if ref not in self.st.parts or ref not in parked_at:
                continue
            (tx, ty), budget, zone, ztol = parked_at[ref]
            cap = budget if budget is not None else within
            base = set(self.pending) - {ref}
            # Same window helper `_census` uses, and for the same reason:
            # these two calls ran at the default CENSUS_STEP_MM of 1.0mm, so
            # for any retry budget under a millimetre the only offset to
            # survive the `max_disp` prune was (0, 0) -- one location at four
            # rotations, every count in {0..4}. The step fix landed in
            # `_census` alone and this, the op the census exists FOR, kept
            # answering at 1.0mm.
            radius, step_mm = seeder.census_window(
                cap, getattr(self.st, 'grid_step', 0.1))
            kw = dict(max_disp=cap, radius=radius, step=step_mm,
                      forbid=self.keepouts, constraint=zone, tol=ztol)
            if zone is not None:
                step_mm, _o, radius = seeder.zone_census_offsets(
                    self.st.parts[ref], zone, ztol, tx, ty,
                    getattr(self.st, 'grid_step', 0.1), cap)
            census_step[ref] = step_mm
            census_radius[ref] = radius
            baseline[ref] = seeder.count_legal_poses(
                self.st, ref, tx, ty, base, **kw)
            census[ref] = {}
            for b in movable:
                census[ref][b] = seeder.count_legal_poses(
                    self.st, ref, tx, ty, base | {b}, **kw)

        # Lift: the blockers rejoin the pile, so they stop being obstacles.
        home = {b: (self.st.parts[b].x, self.st.parts[b].y,
                    self.st.parts[b].rot) for b in movable}

        # A trade is ALL OR NOTHING. Everything from here is undone together
        # if any part of it cannot be completed legally -- the house standard
        # (`reseat_scope`'s three-conjunct gate reverts the whole pass;
        # `seed_from_intent`'s anchor rounds snapshot and restore). Without
        # this, a blocker that cannot get back out of the way used to be put
        # back at its old pose ANYWAY, which is now occupied by the part it
        # was blocking: two coincident courtyards, written, with a note
        # reading as success.
        snap = {'poses': {r: (self.st.parts[r].x, self.st.parts[r].y,
                              self.st.parts[r].rot)
                          for r in set(movable) | set(blocked)
                          if r in self.st.parts},
                'pending': set(self.pending),
                'seats': list(self.res.seats),
                'parks': list(self.res.parks)}

        def stamp(park, ref):
            """Write this op's ONE pre-lift measurement onto a park, whole.

            All four fields together, and only onto a park that carries no
            census of its own. Two halves of that matter:

            It never DOWNGRADES. The old form ended `p.censused = ref in
            census`, which wrote False over a True whenever `ref` was skipped
            above -- leaving a park claiming nothing was measured beside a
            populated `baseline_poses` and a reason naming a blocker.

            It never overwrites an existing census. On the rollback path the
            restored parks are the EARLIER op's, already censused by
            `_census` at their own window; replacing their numbers and
            leaving their reason sentence is how a park came to read
            `blockers={'C10': 0}` beside "would free 34".
            """
            if ref not in census or park.censused:
                return
            park.blockers = dict(census[ref])
            park.baseline_poses = baseline.get(ref)
            park.census_step_mm = census_step.get(ref)
            park.census_radius_mm = census_radius.get(ref)
            park.censused = True
            top = sorted(((n, b) for b, n in census[ref].items()),
                         reverse=True)
            if top and top[0][0] > (baseline.get(ref) or 0):
                park.reason += (
                    f"; lifting {top[0][1]} would take it from "
                    f"{baseline.get(ref)} to {top[0][0]} pose(s) "
                    f"(measured at {census_step.get(ref)}mm, before the lift)")
            elif top:
                # "no ADDITIONAL pose", not "no pose". With a non-zero
                # baseline this used to say the lift frees nothing while the
                # blockers dict beside it held non-zero counts.
                park.reason += (
                    f" -- and lifting {', '.join(movable)} frees no "
                    f"additional pose (still {baseline.get(ref)} at "
                    f"{census_step.get(ref)}mm), so they are not what is in "
                    f"the way")

        def rollback(why: str):
            for r, pose in snap['poses'].items():
                self.st.apply_move(r, *pose)
            self.pending = set(snap['pending'])
            self.res.seats = list(snap['seats'])
            self.res.parks = list(snap['parks'])
            self.res.notes.append(why)
            for ref in blocked:
                for p in self.res.parks:
                    if p.ref == ref:
                        stamp(p, ref)

        self.pending |= set(movable)
        seated_now = []
        for ref in blocked:
            if ref not in parked_at:
                self.res.parks.append(Park(
                    ref=ref, step=step, action='place_lift',
                    reason='nothing earlier in this plan parked it, so there '
                           'is no target to retry it at'))
                continue
            (tx, ty), budget, zone, ztol = parked_at[ref]
            # census=False: this op censused the SAME seat above, before the
            # lift. Letting seat() census again measures a board where the
            # blockers are already out of the way -- a different question,
            # answered into the same four fields.
            #
            # `constraint=zone`: the retry must satisfy the SAME constraint
            # the op that parked it did. Without this the lift "succeeded" by
            # dropping the requirement -- R1 seated 3.86mm outside the zone
            # place_pack gave it, and the run reported a seat.
            ok = self.seat(ref, tx, ty, step, 'place_lift',
                           within=budget if budget is not None else within,
                           rot=op.get('rot'), census=False,
                           constraint=zone, tol=ztol)
            # Either way the earlier park is SUPERSEDED: this op answered the
            # question it asked. Carrying both would report one part as
            # seated-and-parked on success, and on failure would leave the
            # bare verdict beside the censused one -- with the bare one first,
            # which is the reading a caller would take.
            self.res.parks = [p for p in self.res.parks
                              if not (p.ref == ref and p.step != step)]
            if ok:
                seated_now.append(ref)
            else:
                for p in self.res.parks:
                    if p.ref == ref and p.step == step:
                        stamp(p, ref)

        # Put the blockers back, now that what they blocked is in place. Their
        # old seat may well be taken now -- that is the point -- so each one
        # searches from where it was, within the op's budget.
        if restore:
            for b in movable:
                bx, by, brot = home[b]
                if not self.seat(b, bx, by, step, 'place_lift',
                                 within=within, rot=brot):
                    rollback(
                        f"place_lift (step {step}) REVERTED: {b} was lifted "
                        f"but has no legal pose to return to within "
                        f"{within if within is not None else 'any distance'}"
                        f"mm of where it was, so the trade cannot be "
                        f"completed. Nothing was moved. Raise `within`, name "
                        f"a different blocker, or seat {b} deliberately "
                        f"somewhere else first.")
                    return
        else:
            # `restore: false` hands the blockers to a later op. They are
            # UNSEATED, and must be reported as such: leaving their earlier
            # Seat in place would write the very pose this op lifted them out
            # of, on top of whatever now occupies it.
            for b in movable:
                self.res.seats = [s for s in self.res.seats if s.ref != b]
                self.res.parks.append(Park(
                    ref=b, step=step, action='place_lift',
                    reason='lifted with restore=false, so it is deliberately '
                           'left unseated for a later op to place'))

        for ref in seated_now:
            freed = census.get(ref) or {}
            top = sorted(freed.items(), key=lambda kv: (-kv[1], kv[0]))
            if top:
                self.res.notes.append(
                    f"{ref}: seated after lifting "
                    f"{', '.join(b for b, _ in top)} "
                    f"(poses at its target, counted at "
                    f"{census_step.get(ref)}mm: {baseline.get(ref, 0)} "
                    f"before, "
                    + ', '.join(f"{n} with {b} lifted" for b, n in top) + ")")

    def op_place_keepout(self, op, step):
        """Reserve a rect for the REST of the plan.

        The intent schema has carried a `keepouts` rule since #549 and it is
        GRADED and honoured by nothing -- `keepout` appears in floorplan.py's
        rule and in no seeding module -- so a reserved strip could only ever
        be reported after the fact. `arrange.py:27` is the scar: its
        `X0 = 46.0` exists to keep the lattice clear of U1's vertical strip,
        and the reservation lives in a COMMENT because nothing could hold it.

        Declared here, honoured by every op after it, ignored by every op
        before it -- ops run in order, and a keepout that retroactively
        invalidated earlier seats would be a different tool.
        """
        rect = tuple(float(v) for v in op['rect'])
        # Carried in the intent's own shape: `sides` limits the reservation
        # to one face, `allow` names the refs it does not apply to.
        self.keepouts.append((rect, tuple(op.get('sides') or ()) or None,
                              tuple(op.get('allow') or ())))
        self.res.notes.append(
            f"keepout {list(rect)} reserved"
            + (f" -- {op['reason']}" if op.get('reason') else '')
            + f" ({len(self.res.seats)} part(s) already seated are NOT "
              f"re-checked against it)")

    def op_place_pack(self, op, step):
        """A set into a zone, by a stated policy.

        `radial` is what the seeder's zone stage does today (members ordered
        by descending pin count, packed outward from the zone centre) and is
        named so a plan can ask for the CURRENT behaviour explicitly rather
        than getting it by default. It is also the policy that measurably
        failed run 19: 34 six-pad diodes seated before 34 fifteen-millimetre
        switches, and the smalls took the centre. `rows`/`grid` lay members
        out in reading order at their own extents, which is what a human
        means by "pack these into that area"; `ring` places them around the
        zone's edge, for parts that want the perimeter.
        """
        idx = self._index_of(op['refs'])
        refs = self.refs(op['refs'], op.get('where'), op.get('order'))
        if not refs:
            return
        zone = tuple(float(v) for v in op['zone'])
        policy = op.get('policy', 'radial')
        tol = float(op.get('tolerance') or 0.5)
        cx, cy = (zone[0] + zone[2]) / 2.0, (zone[1] + zone[3]) / 2.0
        before = len(self.res.parks)

        if policy == 'radial':
            # Ordered by descending pin count, like the zone stage, so
            # "policy: radial" really is the behaviour it names.
            refs = sorted(refs, key=lambda r: (
                -getattr(self.st.parts.get(r), 'pin_count', 0), r))
            for ref in refs:
                self.seat(ref, cx, cy, step, 'place_pack',
                          within=op.get('within'), rot=op.get('rot'),
                          constraint=zone, tol=tol)
            self._zone_capacity(op, step, refs, zone, before)
            return

        targets = self._pack_targets(refs, zone, policy)
        for ref, (tx, ty) in zip(refs, targets):
            self.seat(ref, round(tx, 4), round(ty, 4), step, 'place_pack',
                      within=op.get('within'), rot=op.get('rot'),
                      constraint=zone, tol=tol)
        self._zone_capacity(op, step, refs, zone, before)

    def _zone_capacity(self, op, step, refs, zone, before):
        """When a pack overflows for a CAPACITY reason, say by how much.

        An overfull zone used to produce N identical refusals at one
        coordinate -- five refs, one target, and no answer to the only
        question the author has, which is how much bigger the zone must be.
        `options.grow_board` answers that for a whole board; this is the same
        per-part charge scoped to a zone.

        Three things this must NOT do, each of which it did:

        * **Blame capacity for a park that is not about capacity.** It counted
          every park the op produced, so an illegal `rot`, a `(locked yes)`
          member, or a DEADLINE became "did not fit" -- and the deadline case
          reported an unfinished search as a measured failure, contradicting
          the park reason printed beside it.
        * **Treat the zone rect as usable area.** The rect is never clipped to
          the outline. A zone hanging off the board east edge measured 2400mm2
          of rect against ~127mm2 of board, then told the author the parts
          were "blocked by shape ... not by total area" -- ruling out the true
          cause by name.
        * **Charge both sides against one rect.** A part on B.Cu does not
          compete with one on F.Cu for the same area; `grow_board` splits per
          side for exactly this reason.
        """
        # Only parks that are a capacity question. A park whose reason is a
        # lock, a rotation lattice, a missing ref or an expired deadline is a
        # different fact and must not be re-labelled as one.
        NON_CAPACITY = ('locked yes', 'legality lattice', 'not a movable part',
                        'deadline expired', 'mechanical fact')
        parked = [p for p in self.res.parks[before:]
                  if not any(k in p.reason for k in NON_CAPACITY)]
        if not parked:
            return

        # The zone as the board actually offers it: clipped to the outline and
        # inset by the edge clearance, the way grow_board computes `usable`.
        bounds = getattr(self.st, 'board', None)
        zx0, zy0 = min(zone[0], zone[2]), min(zone[1], zone[3])
        zx1, zy1 = max(zone[0], zone[2]), max(zone[1], zone[3])
        clipped = False
        if bounds:
            edge = getattr(self.st, 'board_edge_clearance', 0.0) or 0.0
            bx0, by0, bx1, by1 = bounds
            ux0, uy0 = max(zx0, bx0 + edge), max(zy0, by0 + edge)
            ux1, uy1 = min(zx1, bx1 - edge), min(zy1, by1 - edge)
            clipped = (abs(ux0 - zx0) > 1e-6 or abs(uy0 - zy0) > 1e-6
                       or abs(ux1 - zx1) > 1e-6 or abs(uy1 - zy1) > 1e-6)
            zx0, zy0, zx1, zy1 = ux0, uy0, ux1, uy1
        zone_area = max(0.0, zx1 - zx0) * max(0.0, zy1 - zy0)

        clr = getattr(self.st, 'clearance', 0.0) or 0.0
        per_side = {}
        for ref in refs:
            part = self.st.parts.get(ref)
            if part is None:
                continue
            r = part.rect(0.0, 0.0, part.rot)
            a = (r[2] - r[0] + clr) * (r[3] - r[1] + clr)
            side = (getattr(part, 'side', None) or 'F')
            per_side[side] = per_side.get(side, 0.0) + a
        need = max(per_side.values()) if per_side else 0.0
        sides = (f" (busiest of {len(per_side)} sides)"
                 if len(per_side) > 1 else "")
        where = " (clipped to the board)" if clipped else ""

        head = (f"place_pack step {step}: {len(parked)} of {len(refs)} part(s) "
                f"did not fit")
        if zone_area <= 0:
            self.res.notes.append(
                f"{head} -- the zone lies entirely off the usable board area, "
                f"so none of it is available. Move the zone onto the board.")
            return
        if need > zone_area:
            self.res.notes.append(
                f"{head} -- the usable zone is {zone_area:.1f} mm2{where} and "
                f"these parts need AT LEAST {need:.1f} mm2{sides}, so it is "
                f"short by at least {need - zone_area:.1f} mm2 "
                f"({need / zone_area:.2f}x). Area is a necessary condition, "
                f"not a sufficient one -- packing overhead means the zone that "
                f"actually seats them is larger again. Widen the zone, move "
                f"parts out of it, or split the pack.")
        else:
            self.res.notes.append(
                f"{head}, and total area is not the reason: the usable zone is "
                f"{zone_area:.1f} mm2{where} for {need:.1f} mm2 of parts"
                f"{sides} ({need / zone_area:.2f}x). Packing overhead, part "
                f"shape, or parts already sitting in the zone accounts for it "
                f"-- widening a little may still not be enough.")

    def _pack_targets(self, refs, zone, policy):
        """Where each member of a pack should aim, before legality.

        Sized from the members' OWN extents rather than a fixed pitch: a pack
        of mixed parts laid out on the largest one's stride wastes the zone,
        and one laid out on the smallest overlaps every larger member onto
        its neighbour's target (they would still seat legally -- `_try_place`
        sees to that -- but every one of them would land far from where the
        plan said, and `moved_mm` would be the only trace).
        """
        w = zone[2] - zone[0]
        h = zone[3] - zone[1]
        ext = []
        for r in refs:
            part = self.st.parts.get(r)
            if part is None:
                ext.append((1.0, 1.0))
                continue
            rr = part.rect(0.0, 0.0, part.rot)
            ext.append((max(0.1, rr[2] - rr[0]), max(0.1, rr[3] - rr[1])))
        step_x = max(e[0] for e in ext) + self.st.clearance
        step_y = max(e[1] for e in ext) + self.st.clearance

        if policy == 'ring':
            n = len(refs)
            rx = max(0.0, w / 2.0 - step_x / 2.0)
            ry = max(0.0, h / 2.0 - step_y / 2.0)
            cx, cy = (zone[0] + zone[2]) / 2.0, (zone[1] + zone[3]) / 2.0
            return [(cx + rx * math.cos(2 * math.pi * i / n),
                     cy + ry * math.sin(2 * math.pi * i / n))
                    for i in range(n)]

        fits = max(1, int(w // step_x))
        if policy == 'grid':
            # Square-ish, which is what distinguishes a grid from rows: fill
            # to the zone's width and you have written `rows` under a second
            # name, and two names for one layout is worse than one name.
            cols = max(1, min(fits, int(math.ceil(math.sqrt(len(refs))))))
        else:                                    # 'rows'
            cols = fits                          # across, then wrap
        out = []
        for i in range(len(refs)):
            r, c = divmod(i, cols)
            out.append((zone[0] + step_x * (c + 0.5),
                        zone[1] + step_y * (r + 0.5)))
        return out

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


def compile_intent(res: ResolveResult, state, pcb_data, ops: Sequence[Dict],
                   *, tolerance_mm: float = 0.5) -> Dict:
    """The plan, as a floorplan intent `check_floorplan` can grade.

    A plan STATES intent, so an intent falls out of it -- unlike
    `floorplan.emit_intent`, which reads one off a board and therefore grades
    clean by construction. This one is built from what the plan MEANT: each
    lattice or slot op becomes a block whose zone is the bounding box of its
    members' courtyards AT THEIR TARGETS, padded by the budget the op itself
    declared acceptable (`within`).

    That is the structural check `moved_mm` cannot give. `moved_mm` is local --
    it says one part landed 8mm from its target. Zone containment says the
    block stopped being a block. A plan whose parts all seated "successfully"
    but scattered fails this and passes that.

    Emitted for the ops that describe a SET with a shape (`place_array`,
    `place_slots`, `place_pack`) plus `place_edge` bands and `place_lock`
    refs. `place_at` and `place_relative` are deliberately not blocks: a
    single part at a coordinate is a zone of one, which grades nothing that
    `moved_mm` has not already reported, and a relative child's home is its
    parent's pose rather than a rectangle.
    """
    bi = pcb_data.board_info
    intent: Dict[str, Any] = {
        'schema': 1, 'kind': 'floorplan-intent', 'units': 'mm',
        'board': getattr(pcb_data, 'source_path', '') or '',
        # `context` is the intent schema's read-only slot; an unknown
        # top-level key is refused at load, deliberately, so provenance goes
        # here rather than inventing a field.
        'context': {
            'compiled_by': 'plan_resolve.compile_intent',
            'meaning': 'the zones are what the PLAN MEANT (built from each '
                       'op target padded by that op own `within`), not what '
                       'the board turned out to be -- an intent read off the '
                       'result would grade clean by construction',
        },
    }
    if bi.board_bounds is not None:
        intent['envelope'] = {'rect': [round(v, 4) for v in bi.board_bounds],
                              'tolerance_mm': tolerance_mm}

    by_step: Dict[int, List[Seat]] = {}
    for s in res.seats:
        by_step.setdefault(s.step, []).append(s)

    blocks: List[Dict] = []
    edges: List[Dict] = []
    locks: List[str] = []
    for i, op in enumerate(ops, start=1):
        action = op.get('action')
        if action == 'place_lock':
            locks.extend(op.get('refs') if isinstance(op.get('refs'), list)
                         else [op.get('refs')])
            continue
        seats = by_step.get(i) or []
        if action == 'place_edge':
            oh = op.get('overhang')
            oh = DEFAULT_EDGE_OVERHANG_MM if oh is None else float(oh)
            for s in seats:
                edges.append({'ref': s.ref, 'edge': op['edge'],
                              'overhang_mm': {'min': 0.0,
                                              'max': round(oh * 2.0, 4)}})
            continue
        if action not in ('place_array', 'place_slots', 'place_pack'):
            continue
        if not seats:
            continue
        pad = float(op.get('within') or 0.0) + tolerance_mm
        x0 = y0 = float('inf')
        x1 = y1 = float('-inf')
        for s in seats:
            part = state.parts.get(s.ref)
            if part is None:
                continue
            # The courtyard AT THE TARGET, not at the seat: the zone has to
            # describe the intent, or a part that drifted defines the box it
            # is then graded against.
            r = part.rect(s.target[0], s.target[1], s.pose[2])
            x0, y0 = min(x0, r[0]), min(y0, r[1])
            x1, y1 = max(x1, r[2]), max(y1, r[3])
        if x0 > x1:
            continue
        if bi.board_bounds is not None:
            # Clamped to the envelope, as emit_intent does: a zone poking
            # outside the board is refused by intent_zone_outside_envelope,
            # and a block whose members legitimately sit at the edge would
            # otherwise make the intent contradict itself.
            bx0, by0, bx1, by1 = bi.board_bounds
            x0, y0 = max(x0 - pad, bx0), max(y0 - pad, by0)
            x1, y1 = min(x1 + pad, bx1), min(y1 + pad, by1)
        else:
            x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        blocks.append({
            'name': op.get('note') or f"{action}-{i}",
            'refs': sorted(s.ref for s in seats),
            'zone': [round(x0, 4), round(y0, 4),
                     round(x1, 4), round(y1, 4)],
            'tolerance_mm': tolerance_mm,
        })
    if blocks:
        intent['blocks'] = blocks
    if edges:
        intent['edge_connectors'] = edges
    if locks:
        intent['must_lock'] = sorted(set(locks))
    return intent


def plan_target_refs(pcb_data, pcb_file, state, ops) -> Tuple[Set[str], List[str]]:
    """Every ref this plan may seat, resolved WITHOUT seating anything.

    Returns (refs, unresolved_notes). Anything not in `refs` keeps its pose
    for the whole run, so it is an obstacle -- see `_Resolver.__init__`.

    Index ops are replayed here because a selector like `index:switch` cannot
    be resolved without them; `op_place_index` only builds a dict, so running
    it twice is free and side-effect-free. A selector this pass cannot resolve
    is reported, and its op's refs are treated as TARGETS (the old, permissive
    behaviour) rather than silently becoming obstacles -- guessing wrong in
    that direction parks a part the author asked for, which is louder than
    stacking one, and the note says which step was involved.
    """
    probe = _Resolver(pcb_data, pcb_file, state)
    targets: Set[str] = set()
    unresolved: List[str] = []
    for i, op in enumerate(ops):
        action = op.get('action')
        if action == 'place_index':
            try:
                probe.op_place_index(op, i + 1)
            except Exception as e:                       # noqa: BLE001
                unresolved.append(f"step {i + 1} ({action}): {e}")
            continue
        # place_lock PINS a part and place_fixed ASSERTS one; neither seats.
        # Collecting their refs as targets would exclude them from the
        # obstacle set -- so locking or fixing a part made it INVISIBLE and
        # the next op could seat on top of it, which is precisely backwards.
        # place_keepout names no parts at all.
        if action in ('place_keepout', 'place_lock', 'place_fixed'):
            continue
        for key in ('ref', 'refs', 'of', 'for'):
            value = op.get(key)
            if value is None:
                continue
            if key == 'ref' and isinstance(value, str):
                targets.add(value)
                continue
            try:
                targets.update(probe.refs(value))
            except Exception as e:                       # noqa: BLE001
                unresolved.append(
                    f"step {i + 1} ({action}) {key}={value!r}: {e}")
                # Permissive fallback: cannot tell what it names, so do not
                # let it become an obstacle by accident.
                targets.update(r for r, p in state.parts.items()
                               if not p.locked)
    return targets, unresolved


def resolve(pcb_data, pcb_file: str, ops: Sequence[Dict], *,
            clearance: float = 0.25, board_edge_clearance: float = 0.55,
            grid_step: float = 0.1, state=None, deadline=None,
            progress=None, census_parks: bool = True) -> ResolveResult:
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
    plan_refs, unresolved = plan_target_refs(pcb_data, pcb_file, state, ops)
    fixed_refs = {op['ref'] for op in ops
                  if op.get('action') == 'place_fixed' and op.get('ref')}
    r = _Resolver(pcb_data, pcb_file, state, deadline=deadline,
                  progress=progress, plan_refs=plan_refs,
                  census_parks=census_parks, fixed_refs=fixed_refs)
    for note in unresolved:
        r.res.notes.append(
            f"could not pre-resolve a selection, so nothing it names was "
            f"treated as an obstacle: {note}")
    held = sum(1 for ref, p in state.parts.items()
               if not p.locked and ref not in r.pending)
    if held:
        r.res.notes.append(
            f"{held} part(s) this plan never names sit at a distinct pose and "
            f"are held there as obstacles; {len(r.pending)} part(s) are the "
            f"plan's to move (or are piled, so their pose means nothing)")
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
