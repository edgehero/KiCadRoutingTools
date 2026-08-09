#!/usr/bin/env python3
"""Surgical convergence: rank a move before paying for it, and step back cheaply.

A convergence run is expensive in exactly one way -- routing -- and a loop that
re-runs a full chain for every candidate spends its whole budget discovering
things a millisecond of arithmetic already knew. Measured on one board: eleven
full-chain iterations bought about eight useful moves, and the run stopped with
five nets carrying no copper.

So: a ladder, cheapest evidence first, stopping as soon as a tier discriminates.

    tier 1  legality            QuenchState.candidate_valid      ms
    tier 2  placement cost      QuenchState.total_cost           ms
    tier 3  scoped route        route.py --nets <affected>       seconds
    tier 4  full chain          the caller's own                 minutes

Tiers 1 and 2 live in pose_score.py. This module adds tier 3 -- routing only the
nets a move can affect -- and the bookkeeping that makes a step back a checkout
rather than a reconstruction.

VERBS

    converge.py poses BOARD --ref U3 [--route] [--affected NET ...]
        Rank the part's candidate poses. With --route, also run tier 3 on the
        top few and report what actually happened to the copper.

    converge.py where BOARD --nets NET ...
        What is unconnected, where the gap is, and which foreign copper is
        walling it in -- via net_forensics, which already answers this and which
        nothing in the usual chain calls.

    converge.py record --ledger L --board B --kind completion --argv ...
        Store a board by content and record what produced it.

    converge.py step-back --ledger L [--to SHA|--iteration N] --out BOARD
        Check out an earlier board. Exact, because it is addressed by content.

    converge.py replay --ledger L --iteration N
        Re-run that iteration's lever verbatim. An entry that recorded only
        prose refuses, loudly.

    converge.py status --ledger L
        Iterations spent, split completion vs systemic. A budget going to the
        instrument rather than the board is the failure this makes visible.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
_ROUTE_PY = os.path.join(ROOT, 'route.py')


# --------------------------------------------------------------------- tier 3

def scoped_route(board, nets, out=None, extra_args=(), timeout=None):
    """Route ONLY `nets`, and return the merged summary. Seconds, not minutes.

    This is the tier that actually discriminates: placement cost says a pose
    looks better, and only a route says the copper agrees. Scoping it to the
    affected nets is what makes it affordable enough to run per candidate.
    """
    tmp = tempfile.mkdtemp(prefix='converge_t3_')
    out = out or os.path.join(tmp, 'routed.kicad_pcb')
    js = os.path.join(tmp, 'route.json')
    argv = [sys.executable, '-X', 'utf8', _ROUTE_PY, board, out,
            '--nets'] + list(nets) + ['--json-out', js] + list(extra_args)
    r = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=timeout, cwd=ROOT)
    summary = {}
    if os.path.isfile(js):
        with open(js, encoding='utf-8') as f:
            summary = json.load(f)
    return {'argv': argv, 'returncode': r.returncode, 'board': out,
            'json': js, 'summary': summary, 'stdout_tail': r.stdout[-1500:]}


def route_verdict(summary):
    """(failures, note) from a route summary -- the tier-3 comparison key."""
    if not summary:
        return None, 'no summary'
    failed = list(summary.get('failed_single') or [])
    # Routed-but-OPEN nets (kept result, disconnected pads). Before this key a
    # non-multipoint open net weighed ZERO here -- probes read failures=0 on
    # boards shipping open copper. Multipoint nets are excluded from the key by
    # the emitter, so adding it to the pad deficit cannot double-count.
    opened = list(summary.get('open_single') or [])
    fm = [d.get('net_name') if isinstance(d, dict) else d
          for d in (summary.get('failed_multipoint') or [])]
    deficit = (summary.get('multipoint_pads_total', 0)
               - summary.get('multipoint_pads_connected', 0))
    n = len(failed) + len(opened) + max(0, deficit)
    parts = []
    if failed or fm:
        parts.append('failed: ' + ', '.join(sorted(set(failed + fm))[:6]))
    if deficit:
        parts.append(f'{deficit} pad(s) short')
    prot = summary.get('protected_skipped')
    if prot:
        # Surfaced because a caller following the router's own retry hint would
        # otherwise loop: 'locked' has no override, ever.
        flat = {k: v for ctx in prot.values() for k, v in ctx.items()}
        parts.append('refused rips: ' + ', '.join(
            f'{k}({v})' for k, v in sorted(flat.items())[:4]))
    return n, '; '.join(parts) or 'clean'


# ------------------------------------------------------------- rip invariants

def check_rip_invariants(nets, rip_set, power_nets=(), impedance_nets=()):
    """Complaints about a proposed rip. Empty list means it is safe to run.

    Four rules, each of which cost a wasted iteration to learn:

    1. A ripped net is re-routed at the CALLING command's parameters, not the
       ones it was originally routed with. Ripping a width-bearing net without
       carrying its width brings it back at the signal default and silently
       destroys a spec geometry.
    2. One net per call. Two together let the second rip the first, reported as
       "1/2 routed" twice running with a DIFFERENT net each time.
    3. A glob never substitutes for an exact name on a protected net: the glob
       is silently skipped while the router keeps asking for that exact rip.
    4. A rip set that names the net being routed is a no-op that needs
       --force-reroute instead.
    """
    out = []
    if len(nets) > 1:
        out.append(f"routing {len(nets)} nets in one call: the second can rip "
                   f"the first and the tally will not say so -- one net per call")
    widthy = set(power_nets) | set(impedance_nets)
    unguarded = sorted(widthy & set(rip_set))
    if unguarded:
        out.append(f"rip set contains width-bearing net(s) {', '.join(unguarded)} "
                   f"-- carry --power-nets/--impedance in the SAME call or they "
                   f"come back at the signal default")
    globs = sorted(p for p in rip_set if any(c in p for c in '*?['))
    if globs:
        out.append(f"rip pattern(s) {', '.join(globs)} are globs: a protected or "
                   f"locked net matching them is skipped silently -- name it "
                   f"exactly to override, and note 'locked' has no override")
    both = sorted(set(nets) & set(rip_set))
    if both:
        out.append(f"{', '.join(both)} is in BOTH --nets and the rip set: that is "
                   f"a no-op unless you also pass --force-reroute")
    return out


# ------------------------------------------------------------------ the verbs

class _StdoutToStderr:
    """`poses` emits JSON on stdout, so nothing else may.

    Parsing the board and building the placement state print diagnostics --
    quench warns about footprints with no courtyard, for instance -- straight to
    stdout, which lands in the middle of the document a caller is piping into
    `json.load`. The diagnostics are worth keeping; they just belong on stderr.
    """

    def __enter__(self):
        self._real = sys.stdout
        sys.stdout = sys.stderr
        return self

    def __exit__(self, *exc):
        sys.stdout = self._real
        return False


def _pose_knobs(board, clearance, board_edge_clearance):
    """Resolve unset pose knobs from the BOARD (run-7 S4).

    The old fixed argparse defaults (0.25/0.55) silently vetoed legal
    rotations on any board routed to a tighter floor (0.15/0.3): the grader
    was stricter than the board's own spec, and `poses` reported "no legal
    pose" for poses the router would happily route. Resolution order (shared
    with check_floorplan via list_nets.board_floor_knobs): explicit CLI
    value > the board's own Default netclass / board constraint > the fixed
    default.
    """
    from list_nets import board_floor_knobs
    return board_floor_knobs(board, clearance, board_edge_clearance)


def cmd_poses(a):
    from kicad_parser import parse_kicad_pcb
    import pose_score
    clearance, board_edge_clearance, knobs = _pose_knobs(
        a.board, a.clearance, a.board_edge_clearance)
    with _StdoutToStderr():
        pcb = parse_kicad_pcb(a.board)
        st = pose_score.make_state(pcb, a.board, clearance=clearance,
                                   board_edge_clearance=board_edge_clearance)
    diag = {}
    with _StdoutToStderr():
        # Armed INSIDE the guard: this verb's stdout is a JSON document, and
        # krt_deadline's DEADLINE:/PROGRESS: lines would land in the middle of
        # it. The guard sends them to stderr, where they belong.
        import krt_deadline
        _dl = krt_deadline.arm(a.deadline, tool='converge poses')
        poses = pose_score.rank_poses(pcb, a.board, a.ref, radius=a.radius,
                                      step=a.step, limit=a.limit, state=st,
                                      diagnostics=diag,
                                      cancel_check=(_dl.cancel_check('sweep')
                                                    if _dl else None))
    if not poses:
        # The dropped-pose census is the difference between "this part has
        # nowhere to go" and "your knobs veto even staying put" (run-7 S4:
        # flip-in-place WAS enumerated, then silently dropped).
        _cut = bool(diag.get('stopped_early'))
        print(json.dumps({'ref': a.ref, 'poses': [], 'knobs': knobs,
                          'dropped_total': diag.get('dropped_total', 0),
                          'dropped_in_place': diag.get('dropped_in_place', []),
                          'stopped_early': _cut,
                          # "no legal pose" is a VERDICT about the part. A cut
                          # sweep has not earned it: with --deadline 0 the
                          # check fires before even the identity offset, so the
                          # old text diagnosed a part whose poses were never
                          # enumerated.
                          'note': ('the sweep was cut by --deadline before it '
                                   'finished -- this is NOT a verdict about '
                                   'the part' if _cut else
                                   'no legal pose, including staying put')},
                         indent=1))
        return 2 if _cut else 1

    if a.route:
        if not a.affected:
            print("--route needs --affected NET ... : only the caller knows "
                  "which nets a move can affect", file=sys.stderr)
            return 2
        from placement.writer import write_placed_output
        tmp = tempfile.mkdtemp(prefix='converge_poses_')
        with _StdoutToStderr():     # the writer and the router both narrate
            for p in poses[:a.route_top]:
                cand = os.path.join(
                    tmp, f"p_{p['x']}_{p['y']}_{int(p['rot'])}.kicad_pcb")
                write_placed_output(a.board, cand, [{'reference': a.ref,
                                                     'new_x': p['x'],
                                                     'new_y': p['y'],
                                                     'new_rotation': p['rot']}])
                res = scoped_route(cand, a.affected, extra_args=a.route_args or [])
                n, note = route_verdict(res['summary'])
                p['route'] = {'failures': n, 'note': note,
                              'iterations': res['summary'].get('total_iterations'),
                              'vias': res['summary'].get('total_vias')}
    # A cut sweep returns a DIFFERENT best pose with a byte-identical document
    # shape -- measured, r=3/s=0.25: full ran 176s and chose rot 0; the same
    # call with --deadline 4 ran 7s and chose rot 90, with no key marking it
    # partial. A ranking nobody can tell is partial is worse than a slow one.
    print(json.dumps({'ref': a.ref, 'stopped_early': bool(diag.get('stopped_early')),
                      'base_cost': poses[0]['cost'] - poses[0]['delta'],
                      'knobs': knobs,
                      'dropped_total': diag.get('dropped_total', 0),
                      'dropped_in_place': diag.get('dropped_in_place', []),
                      'poses': poses}, indent=1))
    return 0


def cmd_where(a):
    """net_forensics already answers 'where is the gap and what is walling it
    in', per layer, nearest-first. Nothing in the usual chain calls it.

    --oracle prepends KiCad's OWN join list (kicad-cli DRC after a real zone
    refill, parsed to endpoint pairs): each remaining join printed as an
    exact net + pad<->copper pair spec, THEN the per-net forensics. Run-5's
    endgame worked joins one at a time from --items prose; this makes the
    work list machine-shaped and scopes forensics to the nets that still
    need work."""
    nets = list(a.nets or [])
    if getattr(a, 'oracle', False):
        from kicad_unconnected import kicad_unconnected, parse_pairs
        n, items, err = kicad_unconnected(a.board)
        if n is None:
            print(f"ORACLE: ERR {err}")
            return 3
        pairs = parse_pairs(items)
        print(f"ORACLE: {len(pairs)} join(s) remain (kicad-cli DRC, zones refilled)")
        for p in pairs:
            pa, pb = p['a'], p['b']
            print(f"  {p['net']}: {pa['kind']}@({pa['x']:.3f},{pa['y']:.3f},"
                  f"{pa['layer'] or 'all'}) <-> {pb['kind']}@({pb['x']:.3f},"
                  f"{pb['y']:.3f},{pb['layer'] or 'all'})")
        oracle_nets = sorted({p['net'] for p in pairs})
        if not nets:
            nets = oracle_nets
        if not nets:
            return 0
    if not nets:
        print("where: no nets given (pass --nets, or --oracle to derive them)")
        return 2
    argv = [sys.executable, '-X', 'utf8',
            os.path.join(ROOT, 'net_forensics.py'), a.board,
            '--nets'] + nets + ['--radius', str(a.radius)]
    return subprocess.run(argv, cwd=ROOT).returncode


def cmd_record(a):
    from board_store import BoardStore, Ledger
    # --score-file: the payload as a PATH, not as argv.
    #
    # `--score` is JSON text, and every caller passes `--score "$(cat ...)"`.
    # board_score payloads run 24-49 kB (they repeat every net name in both
    # `unrouted.nets` and `connectivity_nets`, and carry the whole assembly
    # `pairs` array), so past roughly 32 kB of total argv the SHELL fails with
    # `Argument list too long` and exits 126 -- before `record` ever execs.
    # Nothing is written, and because the 126 belongs to the shell rather than
    # to this tool, a caller who does not re-count the ledger rows sees no
    # error at all. Run 9 lost a lap that way and found it only by chance.
    #
    # `verdict --score` was already a path (it is open()ed), so this makes the
    # two subcommands agree rather than inventing a convention.
    if getattr(a, 'score_file', None):
        if a.score:
            print("record: pass --score OR --score-file, not both.",
                  file=sys.stderr)
            return 2
        try:
            with open(a.score_file, encoding='utf-8') as _sf:
                a.score = _sf.read()
        except OSError as _e:
            print(f"record: --score-file unreadable: {_e}", file=sys.stderr)
            return 2
    # Refuse an --argv that can never replay (run-7 F4: entries recorded with
    # placeholder script names made replay a reconstruction, which is exactly
    # what the ledger exists to prevent). Nothing is written on refusal.
    if a.argv:
        import shutil
        exe = a.argv[0]
        if not (os.path.isfile(exe) or shutil.which(exe)):
            print(f"record: --argv starts with '{exe}', which is neither an "
                  f"existing file nor an executable on PATH -- this entry "
                  f"could never replay. Record the REAL command (the one that "
                  f"produced the board), or omit --argv for a prose-only "
                  f"entry. Nothing was written.", file=sys.stderr)
            return 2
    # Lens verdicts are stored RAW, so the grammar stays owned by
    # verifier-prompts.md and a malformed line stays visible instead of being
    # normalised into something that reads like a pass. Refuse the shape at
    # write time -- same posture as --argv above -- so the ledger never holds a
    # row that cannot be read back.
    _LENS_RE = r'^VERDICT=(PASS|FAIL):lens=[A-Za-z0-9_-]+'
    if a.lens:
        import re as _re
        _badl = [v for v in a.lens if not _re.match(_LENS_RE, v.strip())]
        if _badl:
            print("record: --lens takes the verifier's VERDICT= line verbatim, "
                  "e.g. 'VERDICT=PASS:lens=connectivity' or "
                  "'VERDICT=FAIL:lens=drc;finding=...;evidence=...'. "
                  f"Not: {_badl[0]!r}. Nothing was written.", file=sys.stderr)
            return 2
    if a.final and not a.stop_condition:
        print("record: --final requires --stop-condition (which of the run's "
              "stop conditions ended it). Nothing was written.",
              file=sys.stderr)
        return 2
    # A run-closing record must carry the routed-board lenses. `blocking == 0`
    # and "every lens passes" are two different claims and the second had no
    # mechanism at all -- verifier-prompts.md states the conjunct and nothing
    # computed it, so a close-out could be written with no lens ever dispatched.
    if a.final and a.kind == 'completion':
        _seen = set()
        for v in (a.lens or []):
            _m = __import__('re').match(r'^VERDICT=(PASS|FAIL):lens=([A-Za-z0-9_-]+)',
                                        v.strip())
            if _m:
                _seen.add(_m.group(2))
        _need = {'connectivity', 'drc', 'spec'}
        _miss = sorted(_need - _seen)
        if _miss:
            print(f"record: --final needs the routed-board lenses and is "
                  f"missing {', '.join(_miss)}. Dispatch them "
                  f"(routing_driver --stage V5 fans them out) and pass each "
                  f"VERDICT= line as --lens. `blocking == 0` is not `every "
                  f"lens passes`. Nothing was written.", file=sys.stderr)
            return 2
        _failed = [v for v in (a.lens or []) if v.strip().startswith('VERDICT=FAIL')]
        if _failed and (a.stop_condition or '').strip() not in ('2', '4'):
            print(f"record: {len(_failed)} lens FAILED, so this run did not "
                  f"finish clean -- --stop-condition must be 2 (budget spent) "
                  f"or 4 (measured-unfixable and said so), not "
                  f"{a.stop_condition!r}. A FAIL means `blocking` was not "
                  f"really zero. Nothing was written.", file=sys.stderr)
            return 2
    store = BoardStore(a.store or os.path.join(os.path.dirname(a.ledger), 'boards'))
    sha = store.put(a.board)
    # Run-3 B4: three ledger entries shipped carrying a PRIOR board's score
    # because --score is free JSON with no binding to --board. board_score
    # now embeds board_sha; warn LOUDLY when it is absent or names a
    # different board than the one being recorded. A warning rather than a
    # refusal: baseline rows legitimately attach a parent score to a
    # rejected candidate -- but never silently.
    if a.score:
        try:
            _payload_sha = json.loads(a.score).get('board_sha')
        except Exception:
            _payload_sha = None
        if _payload_sha is None:
            print("record WARNING: score payload carries no board_sha "
                  "(pre-B4 board_score, or hand-built JSON) -- the ledger "
                  "cannot verify it grades THIS board.", file=sys.stderr)
        elif _payload_sha != sha:
            print(f"record WARNING: score payload grades a DIFFERENT board "
                  f"(payload board_sha {_payload_sha[:12]}... != recorded "
                  f"board {sha[:12]}...). Run-3 shipped three stale-payload "
                  f"entries exactly this way; if this attachment is "
                  f"deliberate (baseline row on a rejected candidate), say "
                  f"so in --lever.", file=sys.stderr)
    lg = Ledger(a.ledger)
    # Three run-7 ledger defects, each caught only by a human re-reading the
    # file afterwards. None is a refusal: every one has a legitimate shape, and
    # a ledger that refuses entries is a ledger people stop writing.
    #
    # (1) The accept flag and the prose disagreeing. Run-7 recorded a rung whose
    #     --lever text says REJECTED while the entry carried accepted=true, so a
    #     reader counting accepted iterations counted a rejection.
    _lever_txt = (a.lever or '').lower()
    _says_reject = any(w in _lever_txt for w in ('reject', 'rolled back',
                                                 'rolled-back', 'reverted'))
    if _says_reject and not a.rejected:
        print("record WARNING: --lever reads as a REJECTION but the entry is "
              "recorded accepted (no --rejected). A reader counting accepted "
              "iterations will count this one. Pass --rejected, or say in the "
              "lever why an entry describing a rejection is the accepted "
              "state.", file=sys.stderr)
    elif a.rejected and _lever_txt and not _says_reject:
        print("record WARNING: entry is --rejected but the lever text never "
              "says so -- a later reader has only the flag. Name the rejection "
              "and the gate that refused it in --lever.", file=sys.stderr)
    # (2) The lever naming a CHECKER instead of the transform. A checker does
    #     not change a board, so an entry whose argv is a checker records no
    #     lever at all -- the board moved for a reason the ledger did not keep.
    if a.argv:
        # Skip past the interpreter to the SCRIPT. This guard inspected
        # argv[0], which is `python3` for every invocation the doctrine
        # teaches (`python3 -X utf8 <script> ...`) -- so it had never fired
        # once, on any entry, in any run. The same blindness applies to the
        # replay guard above, which was validating that an interpreter exists
        # rather than that a command can replay.
        _toks = [str(t) for t in a.argv]
        _script = ''
        for _t in _toks:
            _base = os.path.basename(_t).lower()
            if _base.endswith('.py'):
                _script = _base
                break
            if _base.startswith('python') or _t.startswith('-') or \
                    _base in ('utf8', 'timeout', 'env', 'nice'):
                continue
            _script = _base
            break
        _exe = _script or os.path.basename(_toks[0]).lower()
        if _exe.endswith('.py'):
            _exe = _exe[:-3]
        _stem = _exe.split()[0]
        if _stem.startswith('check_') or _stem in ('board_score', 'list_nets',
                                                   'kicad_drc_compare'):
            print(f"record WARNING: --argv names '{_stem}', which measures a "
                  f"board rather than changing one. The ledger's lever is meant "
                  f"to be the TRANSFORM that produced this board; record that "
                  f"command and put the measurement in --score.",
                  file=sys.stderr)
    # (3) Back-fill. An entry timestamped before the one it follows means the
    #     record was written after the fact, so its ordering is a reconstruction.
    _prior = lg.entries()
    if _prior:
        _last_t = _prior[-1].get('t')
        if isinstance(_last_t, (int, float)) and time.time() < _last_t - 1.0:
            print(f"record WARNING: this entry's clock is BEHIND the previous "
                  f"entry's (t {time.time():.0f} < {_last_t:.0f}). The ledger's "
                  f"order is meant to be the order things happened; a "
                  f"back-filled entry cannot support that claim.",
                  file=sys.stderr)
    prev = lg.last_accepted()
    entry = {'iteration': len(lg.entries()), 'kind': a.kind,
             'parent_sha': (prev or {}).get('result_sha'),
             'result_sha': sha, 'lever': a.lever,
             'lever_argv': list(a.argv) if a.argv else None,
             'score': json.loads(a.score) if a.score else None,
             'renders': list(a.render_json) if a.render_json else None,
             'lenses': list(a.lens) if a.lens else None,
             'accepted': not a.rejected}
    # A placement lap moved parts. The skill mandates the move be LOOKED AT,
    # and run 9 skipped that for an entire campaign without anything noticing
    # -- including afterwards, because the record kept no trace either way. A
    # warning, not a refusal: a rejected lap or a no-move gate row legitimately
    # has nothing to show. But silence must stop being indistinguishable from
    # compliance.
    if a.kind == 'placement' and not a.render_json and not a.rejected:
        print("record NOTE: this placement lap records no --render-json. The "
              "read mandates are only auditable through the ledger; without "
              "one, a skipped read and an absent trigger look identical later. "
              "Attach the render you read, or say in --lever why there was "
              "no trigger.", file=sys.stderr)
    if a.final:
        entry['final'] = True
        entry['stop_condition'] = a.stop_condition
    e = lg.append(entry)
    print(json.dumps(e, indent=1, sort_keys=True))
    # Failing-net NAMES belong in the record (run-7 S10/F5): a score that
    # carries only a count forces every later read to re-derive which nets,
    # and a truncated re-derivation shipped a wrong close-out.
    sc = e.get('score') or {}
    fails = sc.get('failures')
    names = sc.get('failed_nets') or sc.get('failed') or []
    if fails:
        if names:
            print("failing nets: " + ", ".join(str(n) for n in names[:12]),
                  file=sys.stderr)
        else:
            print(f"NOTE: score records failures={fails} but names no nets -- "
                  f"add 'failed_nets' to the score JSON so the ledger stays "
                  f"readable without re-deriving the open set.",
                  file=sys.stderr)
    return 0


def cmd_step_back(a):
    from board_store import BoardStore, Ledger
    lg = Ledger(a.ledger)
    store = BoardStore(a.store or os.path.join(os.path.dirname(a.ledger), 'boards'))
    if a.to:
        sha = a.to
    elif a.iteration is not None:
        m = [e for e in lg.entries() if e.get('iteration') == a.iteration]
        if not m:
            print(f"no iteration {a.iteration} in {a.ledger}", file=sys.stderr)
            return 2
        sha = m[-1]['result_sha']
    else:
        last = lg.last_accepted()
        if not last:
            print("no accepted iteration to step back to", file=sys.stderr)
            return 2
        sha = last['result_sha']
    store.get(sha, a.out)
    print(f"checked out {sha[:12]} -> {a.out}")
    return 0


def cmd_replay(a):
    from board_store import Ledger, replay_command
    lg = Ledger(a.ledger)
    m = [e for e in lg.entries() if e.get('iteration') == a.iteration]
    if not m:
        print(f"no iteration {a.iteration}", file=sys.stderr)
        return 2
    try:
        argv = replay_command(m[-1])
    except ValueError as e:
        # A message, not a traceback: "this iteration is not replayable" is an
        # ordinary answer about the ledger, not a crash.
        print(str(e), file=sys.stderr)
        print("Record lever_argv when you write an entry and this becomes a "
              "one-liner instead of a reconstruction.", file=sys.stderr)
        return 4
    print('replaying: ' + ' '.join(argv))
    return subprocess.run(argv, cwd=ROOT).returncode


CONTINUE, DONE, STUCK, BUDGET = 4, 0, 5, 6

#: Which half of the loop a ledger row belongs to. `systemic` is neither -- it
#: changes how the chain measures itself, not the board -- so it can never make
#: a half look like it is still improving.
_HALF = {'placement': 'placement', 'completion': 'routing'}


def _score_key(score):
    """(blocking, quality) as a comparable tuple, or None if not gradeable.

    Lexicographic, never a weighted sum: a weighted sum lets a router buy off a
    disconnected net with a lower via count. `blocking == None` is NOT zero --
    it means a component that was asked for could not answer -- so it sorts
    worse than any real number rather than reading as a perfect board.
    """
    if not isinstance(score, dict):
        return None
    b = score.get('blocking')
    q = score.get('quality') or {}
    # A quality tuple carrying None (board_score.quality returns {'error': ...}
    # when the board will not parse) makes min() raise TypeError the moment two
    # rows tie on `blocking`. Untested until now because the self-tests use a
    # uniform empty quality. Sort unknowns LAST rather than crashing.
    quality = tuple(v if isinstance(v, (int, float)) else float('inf')
                    for v in (q.get('vias'), q.get('copper_mm'),
                              q.get('segments')))
    if b is None:
        # NOT `inf`. A row whose score never measured `blocking` used to rank
        # as the worst possible board, and `inf >= inf` then made the plateau
        # test TRUE -- so an unmeasured lap read as a plateaued one, which is
        # the opposite of what it is. Returning None drops it from the window
        # entirely (the callers already filter None), so a half is judged on
        # laps that actually measured something.
        return None
    return (b, quality)


def _half_is_flat(rows, half, flat):
    """Has this half failed to improve in its last `flat` accepted laps?

    Only ACCEPTED rows count. A rejected lap is data -- it is what makes a
    plateau detectable at all -- but it is not evidence that the half can still
    move, or every rejection would reset the counter and the loop would never
    stop.

    Returns (is_flat, n_laps, reason). The REASON matters because `False` has
    two completely different causes and the caller could not tell them apart:
    "this half improved recently" and "this half has not run `flat` laps, so
    the question is not answerable yet". They call for opposite actions -- keep
    pulling levers, versus recognise a half that finished early -- and the
    verdict sentence fused them into "it improved ... or has not run that many
    yet", which is two diagnoses in one breath.

    Measured (neo6502, run 15): the placement half satisfied its OWN close-out
    in 4 accepted laps -- every gate clean, residue named -- against a --flat of
    5. It could never plateau, so L5 returned CONTINUE forever while reporting
    the half as "still improving", which it was not. A half that does its job
    efficiently should not be indistinguishable from one that stalled.
    """
    keys = [_score_key(r.get('score')) for r in rows
            if r.get('accepted') and _HALF.get(r.get('kind')) == half]
    keys = [k for k in keys if k is not None]
    if len(keys) <= flat:
        # NOT the same as "still improving" -- say which.
        return False, len(keys), 'too-few-laps'
    # Did this half improve ACROSS ITS OWN last `flat` laps?
    #
    # `best_before = min(keys[:-flat])` asked a different question: has the
    # window beaten the best lap EVER seen before it. One large early
    # improvement then pins the bar for the rest of the run. Measured on run 9:
    # the pour took the routing half to 297 on its first lap, and the series
    # [297, 371, 365, 340, 330, 320] -- a necessary rise at the fanout, then
    # five laps of strict improvement -- reported flat:true, because 320 never
    # beat 297. A half that is demonstrably still moving read as plateaued,
    # which is exactly the DONE-vs-STUCK confusion this function exists to
    # prevent.
    #
    # (Replacing it with `keys[-flat-1]` does NOT fix that case -- on a
    # 6-lap ledger that IS the 297. The baseline has to be the window's own
    # first lap.)
    window = keys[-flat:]
    _flat = min(window) >= window[0]
    return _flat, len(keys), ('plateau' if _flat else 'improving')


def cmd_verdict(a):
    """Continue, or stop -- and say WHICH kind of stop it was.

    Every stop RULE in this toolchain is written down (a 5-lap placement cap,
    four routing stop conditions, a budget of 100, "5 consecutive flat") and
    not one of them had a MECHANISM: no counter, no budget check, no read of
    the ledger that gated continuation. `final` and `stop_condition` were
    written and never read back. So a run that stopped because it was finished
    and a run that stopped because it was stuck produced the same artifact.

    Reaching `blocking == 0` is the FLOOR, not the finish. The score is
    lexicographic (blocking, quality) and quality orders the boards that
    already got there, so the loop keeps pulling levers on the second key and
    stops only when NEITHER half can improve EITHER key -- which is what
    "fully blocked in both placement and routing" means, measured.
    """
    from board_store import Ledger
    rows = Ledger(a.ledger).entries()
    score, err = None, None
    if a.score:
        try:
            with open(a.score, encoding='utf-8') as fh:
                score = json.load(fh)
        except Exception as exc:                            # noqa: BLE001
            err = f'{type(exc).__name__}: {exc}'
    if score is None:
        print(json.dumps({'verdict': 'NO-SCORE', 'reason': (
            err or '--score is required: the verdict is about a board, and '
            'without its score there is nothing to be blocked or done ABOUT.'
        )}, indent=1, sort_keys=True))
        return 2

    scored = [r for r in rows if _score_key(r.get('score')) is not None]
    key = _score_key(score)
    blocking = key[0]
    flat_p, laps_p, why_p = _half_is_flat(rows, 'placement', a.flat)
    flat_r, laps_r, why_r = _half_is_flat(rows, 'routing', a.flat)

    doc = {'ledger_rows': len(rows), 'scored_rows': len(scored),
           'budget': a.budget, 'flat': a.flat,
           'blocking': None if blocking == float('inf') else blocking,
           'quality': score.get('quality'),
           'ungraded': sorted(score.get('ungraded') or []),
           'unknown': sorted(score.get('unknown') or []),
           'placement': {'accepted_laps': laps_p, 'flat': flat_p,
                         'why': why_p},
           'routing': {'accepted_laps': laps_r, 'flat': flat_r,
                       'why': why_r}}

    if len(rows) >= a.budget:
        doc.update(verdict='BUDGET', reason=(
            f'{len(rows)} ledger entries written, budget {a.budget}. Report '
            f'the best-scoring board AND every remaining blocker, itemised '
            f'with its measurement.'))
        code = BUDGET
    elif not (flat_p and flat_r):
        still = [h for h, f in (('placement', flat_p), ('routing', flat_r))
                 if not f]
        # Say WHICH of the two causes applies, per half. They call for opposite
        # actions and the old sentence offered both at once.
        _laps = {'placement': laps_p, 'routing': laps_r}
        _why = {'placement': why_p, 'routing': why_r}
        _parts = []
        for h in still:
            if _why[h] == 'too-few-laps':
                _parts.append(
                    f'{h} has run {_laps[h]} accepted lap(s), fewer than the '
                    f'{a.flat} this test needs, so whether it plateaued is NOT '
                    f'YET ANSWERABLE -- which is not the same as "it is still '
                    f'improving". If it stopped because its own close-out was '
                    f'satisfied, that is a half that finished early, and the '
                    f'lever is to give it something further to optimise (or to '
                    f'say on the record that there is nothing), never to lower '
                    f'--flat until the gate agrees')
            else:
                _parts.append(
                    f'{h} improved within its last {a.flat} accepted laps, so '
                    f'it has more to give')
        doc.update(verdict='CONTINUE', improving=still,
                   why={h: _why[h] for h in still}, reason=(
            '; '.join(_parts) + '. Reaching blocking == 0 is the floor, not '
            'the finish -- keep pulling levers on quality until neither half '
            'can improve either key.'))
        code = CONTINUE
    elif blocking == 0:
        doc.update(verdict='DONE-EXHAUSTED', reason=(
            'blocking == 0 and neither half improved in its last '
            f'{a.flat} accepted laps. This is the best board these levers '
            f'found.'))
        code = DONE
    else:
        doc.update(verdict='STUCK', reason=(
            f'blocking == {doc["blocking"]} and neither half improved in its '
            f'last {a.flat} accepted laps. Stopping here is legitimate; '
            f'calling the board finished is not. Itemise every remaining '
            f'blocker with the measurement that proves it.'))
        code = STUCK

    if doc['ungraded']:
        # Not fatal: a board with no spec files has nothing to grade those
        # components against, and making it fatal would put every corpus board
        # permanently in STUCK. But it is never silent -- a component nothing
        # examined is UNEXAMINED, and DONE must say so out loud.
        doc['reason'] += (' UNEXAMINED, and not passed: '
                          + ', '.join(doc['ungraded']) + '.')
    if doc['unknown']:
        doc['reason'] += (' A component RAN and could not answer: '
                          + ', '.join(doc['unknown'])
                          + ' -- fix the instrument before trusting any '
                            'verdict here.')
    print(json.dumps(doc, indent=1, sort_keys=True))
    return code


def cmd_status(a):
    from board_store import Ledger
    lg = Ledger(a.ledger)
    c = lg.counts()
    print(json.dumps(c, indent=1, sort_keys=True))
    if c['total'] and c['systemic'] * 2 >= c['total']:
        print("NOTE: at least half of this budget went to SYSTEMIC iterations -- "
              "changes to how the chain measures or grades itself, not to the "
              "copper. Check what is still unrouted before spending more.",
              file=sys.stderr)
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='verb', required=True)

    q = sub.add_parser('poses', help='rank a part\'s candidate poses')
    q.add_argument('board')
    q.add_argument('--ref', required=True)
    q.add_argument('--radius', type=float, default=2.0)
    q.add_argument('--step', type=float, default=0.5)
    q.add_argument('--limit', type=int, default=12,
                   help='how many ranked poses to RETURN. It does not bound '
                        'the sweep: every candidate is still evaluated. Use '
                        '--deadline for that.')
    q.add_argument('--deadline', type=float, default=None, metavar='SECONDS',
                   help='wall-clock budget for the candidate sweep. The sweep '
                        'is radius/step rings x rotations and each candidate '
                        'pays a full cost evaluation; --limit only truncates '
                        'the result. Env: KRT_DEADLINE_S')
    q.add_argument('--clearance', type=float, default=None,
                   help='pose-legality clearance (default: the board\'s own '
                        'Default netclass, else 0.25; run-7 S4 -- a fixed '
                        'default tighter than the board floor silently '
                        'vetoes legal poses)')
    q.add_argument('--board-edge-clearance', type=float, default=None,
                   help='pose-legality edge clearance (default: the board\'s '
                        'own min_copper_edge_clearance, else 0.55)')
    q.add_argument('--route', action='store_true',
                   help='also run tier 3 (a scoped route) on the top poses')
    q.add_argument('--route-top', type=int, default=2,
                   help='how many ranked poses to actually route (default 2)')
    q.add_argument('--affected', nargs='+', default=None,
                   help='nets a move of this part can affect; required by --route')
    q.add_argument('--route-args', nargs='+', default=None)
    q.set_defaults(fn=cmd_poses)

    w = sub.add_parser('where', help='islands, gaps and the copper walling them in')
    w.add_argument('board')
    w.add_argument('--nets', nargs='+', default=None,
                   help='nets to run forensics on (optional with --oracle, '
                        'which derives them from the remaining joins)')
    w.add_argument('--radius', type=float, default=1.0)
    w.add_argument('--oracle', action='store_true',
                   help="prepend KiCad's own join list (kicad-cli DRC after a "
                        "zone refill) as exact endpoint-pair specs, and scope "
                        "forensics to those nets when --nets is omitted")
    w.set_defaults(fn=cmd_where)

    r = sub.add_parser('record', help='store a board and record what produced it')
    r.add_argument('--ledger', required=True)
    r.add_argument('--board', required=True)
    r.add_argument('--store', default=None)
    r.add_argument('--kind', choices=('completion', 'placement', 'systemic'),
                   default='completion')
    r.add_argument('--lever', default=None)
    r.add_argument('--score', default=None, help='JSON')
    r.add_argument('--score-file', default=None, metavar='PATH',
                   help='the score payload as a FILE. Prefer this: '
                        '--score "$(cat ...)" exceeds the OS argv limit at '
                        '~32kB and the shell then exits 126 BEFORE record '
                        'runs, so the lap is lost with no error. Mutually '
                        'exclusive with --score.')
    r.add_argument('--render-json', action='append', default=None,
                   metavar='PATH',
                   help='render_placement --json-out document(s) that were '
                        'READ for this lap; repeatable. Stored as '
                        'entry["renders"]. The [read: ...] convention lived in '
                        'free-text --lever, so an audit could not tell a '
                        'skipped mandate from an absent trigger.')
    r.add_argument('--lens', action='append', default=None, metavar='VERDICT',
                   help='a verifier lens verdict, VERBATIM: '
                        '"VERDICT=PASS:lens=connectivity" or '
                        '"VERDICT=FAIL:lens=drc;finding=...;evidence=...". '
                        'Repeatable; stored raw as entry["lenses"]. Same '
                        'reason as --render-json: a verdict that lives in '
                        'free-text --lever cannot be told from a lens nobody '
                        'ran. --final requires the three routed-board lenses.')
    r.add_argument('--rejected', action='store_true')
    r.add_argument('--final', action='store_true',
                   help='mark the run-closing record; requires --stop-condition')
    r.add_argument('--stop-condition', default=None,
                   help='which stop condition ended the run (with --final)')
    r.add_argument('--argv', nargs=argparse.REMAINDER, default=None,
                   help='the command that produced it -- what makes replay '
                        'possible. Refused (exit 2) when its first token is '
                        'neither an existing file nor on PATH.')
    r.set_defaults(fn=cmd_record)

    s = sub.add_parser('step-back', help='check out an earlier board, exactly')
    s.add_argument('--ledger', required=True)
    s.add_argument('--store', default=None)
    s.add_argument('--to', default=None, help='a board sha')
    s.add_argument('--iteration', type=int, default=None)
    s.add_argument('--out', required=True)
    s.set_defaults(fn=cmd_step_back)

    y = sub.add_parser('replay', help="re-run an iteration's lever verbatim")
    y.add_argument('--ledger', required=True)
    y.add_argument('--iteration', type=int, required=True)
    y.set_defaults(fn=cmd_replay)

    t = sub.add_parser('status', help='budget spent, completion vs systemic')
    t.add_argument('--ledger', required=True)
    t.set_defaults(fn=cmd_status)

    v = sub.add_parser('verdict',
                       help='continue, or stop -- and which kind of stop')
    v.add_argument('--ledger', required=True)
    v.add_argument('--score', required=True,
                   help="the current board's score JSON (board_score --json)")
    v.add_argument('--budget', type=int, default=100,
                   help='ledger entries this run may write (default 100, the '
                        'figure convergence.md already states)')
    v.add_argument('--flat', type=int, default=5,
                   help='accepted laps a half may go without improving before '
                        'it counts as blocked (default 5, ditto)')
    v.set_defaults(fn=cmd_verdict)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == '__main__':
    # NO cli_banner here (deliberate): converge's stdout is a JSON API --
    # `record` and `status` print documents that callers json.loads() whole
    # (tests/test_converge.py does). The other instruments' stdout is a log.
    sys.exit(main())
