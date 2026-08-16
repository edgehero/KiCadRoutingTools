#!/usr/bin/env python3
"""Two watchers for a long run: what went wrong, and how long it took.

Both are written for the Monitor contract -- ONE STDOUT LINE PER EVENT, exit
ends the watch -- so they can be armed once and left alone while the run
works.

WHY A SCRIPT AND NOT A GREP. A watcher that matches only the happy path is
silent through a crash, and silence is indistinguishable from "still
running". That is the failure this file exists to avoid, so `bugs` matches
the signatures you would ACT on -- tracebacks, refusals, leaks, rejected
laps, a `blocking` that went UP -- and `timer` emits on every terminal state
it can reach, including the ones nobody wants: stalled and timed out. If it
cannot tell you the run finished, it tells you it stopped being able to
tell.

    # every new problem, as it appears (many events, until you stop it)
    python3 -X utf8 tests/stress/run_watch.py bugs --workdir wk/run20

    # one event at the start, one when it ends (however it ends)
    python3 -X utf8 tests/stress/run_watch.py timer --workdir wk/run20 \
        --done wk/run20/DONE

Exit codes: 0 normal, 2 usage. `bugs` never exits on its own.
"""
import argparse
import json
import os
import re
import sys
import time

#: Substrings that mean something went wrong, in any text the run leaves
#: behind. Deliberately broad: a false positive costs one line, a missed
#: crash costs the whole run's credibility. Ordered roughly by severity so
#: the emitted label is the most specific one that matched.
SIGNATURES = (
    ('TRACEBACK', 'Traceback (most recent call last)'),
    ('LEAK', 'VERDICT: LEAK'),
    ('UNAIDED-VIOLATION', 'UnaidedViolation'),
    ('PROVENANCE', 'UNAIDED VIOLATION'),
    ('NOT-BUILDABLE', 'NOT BUILDABLE'),
    ('REFUSED', 'refusing'),
    ('REFUSED', 'REFUSED'),
    ('ERROR', 'Error:'),
    ('ERROR', 'ERROR'),
    ('FAILED', 'FAILED'),
    ('ASSERT', 'AssertionError'),
    ('DID-NOT-RUN', 'did not run'),
    ('UNAVAILABLE', 'unavailable'),
)

#: Files worth reading for those signatures. The run tees its own output to
#: `*.log`; the tools write `*.json` reports whose `skipped` blocks say what
#: could not be measured.
WATCHED_EXT = ('.log', '.txt', '.json', '.jsonl')

POLL_SEC = 5.0


def _walk(workdir):
    for root, dirs, files in os.walk(workdir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in sorted(files):
            if name.endswith(WATCHED_EXT):
                yield os.path.join(root, name)


def _scan_text(path, seen, rel):
    """Emit one line per NEW signature hit in this file."""
    out = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except OSError:
        return out
    for i, line in enumerate(lines):
        for label, needle in SIGNATURES:
            if needle in line:
                key = (rel, label, line.strip()[:160])
                if key in seen:
                    break
                seen.add(key)
                out.append(f'{label} {rel}:{i + 1}: {line.strip()[:200]}')
                break
    return out


def _scan_ledger(path, seen, rel):
    """A rejected lap, or a `blocking` that went UP, is a finding too.

    The ledger is the run's own record of what it decided, so a regression
    here is more trustworthy than any log line -- it is what the loop acted
    on, not what a tool printed.
    """
    out, prev = [], None
    try:
        with open(path, encoding='utf-8') as f:
            rows = [json.loads(x) for x in f if x.strip()]
    except (OSError, ValueError):
        return out
    for r in rows:
        if not isinstance(r, dict):
            continue
        it = r.get('iteration')
        if r.get('accepted') is False:
            key = (rel, 'rejected', it)
            if key not in seen:
                seen.add(key)
                out.append(f'REJECTED-LAP {rel}: iteration {it} '
                           f'lever={r.get("lever")} was not accepted')
        sc = r.get('score') if isinstance(r.get('score'), dict) else {}
        blk = sc.get('blocking')
        if isinstance(blk, (int, float)):
            if prev is not None and blk > prev:
                key = (rel, 'regress', it)
                if key not in seen:
                    seen.add(key)
                    out.append(f'BLOCKING-UP {rel}: iteration {it} '
                               f'blocking {prev} -> {blk}')
            prev = blk
        elif 'blocking' in sc:
            key = (rel, 'blocking-none', it)
            if key not in seen:
                seen.add(key)
                out.append(f'BLOCKING-NULL {rel}: iteration {it} reports '
                           f'blocking=None -- "0 violations" and "0 rules '
                           f'ran" are different answers')
    return out


def watch_bugs(workdir, poll):
    seen = set()
    print(f'WATCHING {os.path.abspath(workdir)} for problems '
          f'({len(SIGNATURES)} signatures + the ledger)', flush=True)
    while True:
        if os.path.isdir(workdir):
            for path in _walk(workdir):
                rel = os.path.relpath(path, workdir).replace('\\', '/')
                if path.endswith('.jsonl'):
                    for line in _scan_ledger(path, seen, rel):
                        print(line, flush=True)
                else:
                    for line in _scan_text(path, seen, rel):
                        print(line, flush=True)
        time.sleep(poll)


def _fmt(sec):
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f'{h:d}h{m:02d}m{s:02d}s' if h else f'{m:d}m{s:02d}s'


def watch_timer(workdir, done_path, poll, stall_min, max_min):
    """START now; ONE further event when the run reaches any terminal state.

    Three terminal states, not one. A timer that only knows how to say
    "finished" reports nothing at all when the run dies or wanders off, and
    an absent notification reads exactly like work still in progress.
    """
    t0 = time.time()
    stamp = os.path.join(workdir, '.run_watch_started')
    os.makedirs(workdir, exist_ok=True)
    if os.path.isfile(stamp):
        try:
            with open(stamp, encoding='utf-8') as f:
                t0 = float(json.load(f)['started'])
        except Exception:                              # noqa: BLE001
            pass
    else:
        with open(stamp, 'w', encoding='utf-8') as f:
            json.dump({'started': t0,
                       'started_iso': time.strftime('%Y-%m-%dT%H:%M:%S')}, f)
    print(f'TIMER START {time.strftime("%H:%M:%S")} -- watching '
          f'{os.path.abspath(workdir)}, done marker '
          f'{os.path.relpath(done_path, workdir)}', flush=True)

    last_change, last_sig = time.time(), None
    while True:
        if os.path.exists(done_path):
            print(f'TIMER STOP after {_fmt(time.time() - t0)} -- done marker '
                  f'appeared', flush=True)
            return 0
        sig = []
        if os.path.isdir(workdir):
            for p in _walk(workdir):
                try:
                    sig.append((p, os.path.getmtime(p), os.path.getsize(p)))
                except OSError:
                    pass
        sig = tuple(sorted(sig))
        if sig != last_sig:
            last_sig, last_change = sig, time.time()
        idle = time.time() - last_change
        if stall_min and idle > stall_min * 60:
            print(f'TIMER STALLED after {_fmt(time.time() - t0)} -- nothing '
                  f'in the work dir changed for {_fmt(idle)}. The run may '
                  f'have died, or it is thinking; check before assuming '
                  f'either', flush=True)
            return 0
        if max_min and (time.time() - t0) > max_min * 60:
            print(f'TIMER TIMEOUT at {_fmt(time.time() - t0)} -- the deadline '
                  f'passed with no done marker', flush=True)
            return 0
        time.sleep(poll)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='mode', required=True)

    b = sub.add_parser('bugs', help='one event per new problem, forever')
    b.add_argument('--workdir', required=True)
    b.add_argument('--poll', type=float, default=POLL_SEC)

    t = sub.add_parser('timer', help='one event at start, one at the end')
    t.add_argument('--workdir', required=True)
    t.add_argument('--done', help='path whose existence means finished '
                                  '(default: WORKDIR/DONE)')
    t.add_argument('--poll', type=float, default=POLL_SEC)
    t.add_argument('--stall-min', type=float, default=20.0,
                   help='emit STALLED after this many idle minutes (0 = off)')
    t.add_argument('--max-min', type=float, default=0.0,
                   help='emit TIMEOUT after this many minutes (0 = off)')

    a = p.parse_args(argv)
    # An empty WORKDIR is what an unset shell variable looks like, and it used
    # to reach os.makedirs('') and traceback -- which in a watcher reads as
    # "the thing I am watching crashed", not "you passed nothing".
    if not (a.workdir or '').strip():
        p.error('--workdir is empty (an unset shell variable?), so there is '
                'nothing to watch')
    if a.mode == 'bugs':
        try:
            watch_bugs(a.workdir, a.poll)
        except KeyboardInterrupt:
            return 0
        return 0
    done = a.done or os.path.join(a.workdir, 'DONE')
    try:
        return watch_timer(a.workdir, done, a.poll, a.stall_min, a.max_min)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    sys.exit(main())
