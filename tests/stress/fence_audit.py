#!/usr/bin/env python3
"""Audit a perturbed-corpus work dir for GROUND-TRUTH LEAKS, by content.

A recovery experiment measures how close a repaired placement lands to the
original. That number is only meaningful if the tools never saw the original.
The protocol fences the obvious carriers by NAME -- the control board, the
perturbation record, the human reference -- and a run-7 watcher found the hole
that naming leaves open:

    the STRIPPED board (the human placement with its copper removed) sat in
    every work dir. It is the perturbation's INPUT, so nobody thought of it as
    truth. Its footprint poses ARE the human placement, exactly.

Naming cannot close that hole, because the next carrier will have a different
name (a `.bak`, a `board_orig.kicad_pcb`, a candidate copied out of an archive).
So this audit ignores names and asks the only question that matters:

    does any FILE in this work dir carry the control's poses?

Boards, and pose RECORDS: a perturbation record embeds `original_poses`
verbatim, so it is ground truth in JSON clothing and gets no name exemption
either. This matters on the default path, not a contrived one --
`perturb(..., control_out=None)` writes that record BESIDE the output board,
i.e. inside the fence. Stage with `control_out=<a dir outside the work dir>`
and the record never enters.

Two modes, because the same content means opposite things before and after a run:

  --mode create   Run at work-dir creation, BEFORE any tool touches the board.
                  Every board here is an INPUT. Any board whose poses match the
                  control (other than the explicitly allowed carriers) is a
                  leak -> exit 4. Writes `.fence-manifest.json` recording the
                  files present and their hashes.

  --mode audit    Run at watcher time, AFTER the run. A board matching the
                  control now has two possible causes, and the manifest tells
                  them apart:
                    * present at creation  -> LEAK (it was an input)
                    * created by the run   -> RECOVERED, which is the experiment
                      succeeding, not a breach (a perfect reconstruction lands
                      exactly on truth -- one run-7 board did, at d1 = 0.000000)
                  Exit 4 only for the first kind.

Match is on the pose set, not on file bytes: copper, UUIDs, netclasses and
zone fills all differ between a stripped board and its control while the
placement is identical.

Usage:
    python3 -X utf8 tests/stress/fence_audit.py --control C.kicad_pcb \\
        --workdir wk/run8/<board>/ --mode create
    python3 -X utf8 tests/stress/fence_audit.py --control C.kicad_pcb \\
        --workdir wk/run8/<board>/ --mode audit [--json]

Exit codes: 0 clean, 2 usage/IO problem, 4 leak found.
"""
import argparse
import fnmatch
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from kicad_parser import parse_kicad_pcb  # noqa: E402
from placement import recovery  # noqa: E402

MANIFEST_NAME = '.fence-manifest.json'

# Carriers the protocol declares as truth ON PURPOSE, excluded from the leak
# report by name.
#
# `*.control.kicad_pcb` USED TO BE HERE AND IS GONE (run-12 Tier 0). It made
# the same bytes a LEAK or CLEAN depending only on the filename: a copy of the
# control under any other name was reported, the control itself was not --
# while `perturb()` wrote it into the output directory by default, so the most
# likely carrier of all was the one carrier this audit ignored. That
# contradicts the docstring above ("Naming cannot close that hole ... So this
# audit ignores names"), and a name-based exemption for the single most likely
# carrier is exactly the hole the module exists to close. A control INSIDE the
# work dir is now a LEAK, which is what this module says it believes.
#
# The legitimate cases are still covered: `control_real` (below) never reports
# the audit's OWN reference, and `--allow` remains for a caller that genuinely
# means it.
#
# DEFAULT_ALLOW IS EMPTY, AND THAT IS THE POINT.
#
# It used to hold `*.perturb.json`. That was harmless only while it was a lie:
# `scan()` walked `.kicad_pcb` alone, so the entry exempted a file the module
# could not open anyway. Teaching the scan to read `.json` turned an inert
# declaration into a working blind spot -- and not a hypothetical one.
# `placement.perturb.perturb(...)` with `control_out` unset writes the record
# BESIDE THE OUTPUT BOARD (perturb.py:596-602), i.e. inside the work dir, and
# that record embeds `original_poses` verbatim. So the default perturbation
# path drops complete ground truth into the fence, and this tuple told the
# audit to walk past it.
#
# The module's thesis is that a leak is CONTENT, not a filename; it already
# applies that to the control ("A control INSIDE the work dir is now a LEAK",
# above). A record is the same truth in JSON clothing, so it gets the same
# answer. The declared record lives in `_truth/`, OUTSIDE the work dir, which
# is what `control_out` is for and what the staging recipe does -- a record
# inside the fence is a staging mistake, and this is the tool that says so.
#
# `--allow` remains for a caller who genuinely means it.
DEFAULT_ALLOW = ()

# A board counts as truth-carrying when this fraction of its shared refs sit
# within POSE_TOL of the control. Not 1.0: a leak is still a leak when one
# footprint was nudged, and a repaired board that genuinely reaches truth is
# separated by the manifest (see --mode audit), not by this threshold.
MATCH_FRAC = 0.98
POSE_TOL_MM = 1e-6
POSE_TOL_DEG = 1e-3


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pose_match(poses_a, poses_b):
    """(match_frac, shared_ref_count, worst_mm) between two pose maps."""
    shared = sorted(set(poses_a) & set(poses_b))
    if not shared:
        return 0.0, 0, None
    hits = 0
    worst = 0.0
    for ref in shared:
        ax, ay, arot = poses_a[ref][0], poses_a[ref][1], poses_a[ref][2]
        bx, by, brot = poses_b[ref][0], poses_b[ref][1], poses_b[ref][2]
        d = math.hypot(ax - bx, ay - by)
        worst = max(worst, d)
        drot = abs((arot - brot) % 360.0)
        drot = min(drot, 360.0 - drot)
        if d <= POSE_TOL_MM and drot <= POSE_TOL_DEG:
            hits += 1
    return hits / len(shared), len(shared), worst


def _json_poses(path):
    """{ref: (x, y, rot)} out of a perturbation RECORD, or None.

    The record embeds `original_poses` verbatim -- it is ground truth in JSON
    clothing, and the scan filtered on the extension before opening anything,
    so this module named a carrier it structurally could not see.

    Read BYTES and let `json.loads` sniff the encoding. Opening as utf-8 text
    made the audit defeatable by re-saving the record as UTF-16 -- same keys,
    same truth, `UnicodeDecodeError` into the bare `except`, waved through as
    "ordinary JSON". `json.loads` applies RFC-4627 BOM detection and accepts
    utf-8, utf-8-sig, utf-16 and utf-32 alike (verified), so the content test
    stops depending on how the file was saved.
    """
    try:
        with open(path, 'rb') as fh:
            doc = json.loads(fh.read())
    except Exception:                                   # noqa: BLE001
        return None
    if not isinstance(doc, dict):
        return None
    # `original_poses` ONLY. A `poses` alias was tried and dropped: across 561
    # real driver-output JSONs in this repo it matched nothing (no writer emits
    # a top-level ref->[x,y,rot] dict under that name), so it bought no
    # coverage -- while the `kind == 'record'` branch in main() is
    # unconditional, meaning anything this function claims can NEVER be classed
    # as recovery. A future tool writing its RESULT as {"poses": {...}} would
    # therefore have had a perfect reconstruction -- the case the module
    # docstring insists must not be a breach ("one run-7 board did, at
    # d1 = 0.000000") -- reported as a LEAK. Speculative coverage is not worth
    # a mechanism that misclassifies the experiment succeeding.
    for key in ('original_poses',):
        raw = doc.get(key)
        if isinstance(raw, dict) and raw:
            out = {}
            for ref, v in raw.items():
                if isinstance(v, (list, tuple)) and len(v) >= 3:
                    try:
                        out[ref] = (float(v[0]), float(v[1]),
                                    float(v[2]) % 360.0)
                    except (TypeError, ValueError):
                        continue
            if out:
                return out
    return None


#: Extensions the scan opens. This module's thesis -- "the next carrier will
#: have a different name" -- applies to EXTENSIONS exactly as it does to stems,
#: and the scan used to stop at `.kicad_pcb`.
SCANNED_EXT = ('.kicad_pcb', '.json')


def scan(workdir, control_poses, allow):
    """Every scannable file in workdir, scored against the control's poses."""
    rows = []
    for root, _dirs, files in os.walk(workdir):
        for name in sorted(files):
            if not name.endswith(SCANNED_EXT):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, workdir).replace('\\', '/')
            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat)
                   for pat in allow):
                continue
            try:
                if name.endswith('.json'):
                    poses = _json_poses(path)
                    if poses is None:
                        continue        # ordinary JSON, not a pose carrier
                else:
                    poses = recovery.board_poses(parse_kicad_pcb(path))
            except Exception as exc:                    # unparseable is not a leak
                rows.append({'file': rel, 'error': str(exc)[:120]})
                continue
            frac, shared, worst = pose_match(poses, control_poses)
            _kind = 'record' if name.endswith('.json') else 'board'
            rows.append({
                'file': rel,
                'kind': _kind,
                'match_frac': round(frac, 6),
                'refs_shared': shared,
                'worst_mm': None if worst is None else round(worst, 6),
                'carries_truth': frac >= MATCH_FRAC and shared > 0,
                'sha256': _sha256(path),
                'mtime': os.path.getmtime(path),
            })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--control', required=True,
                    help='the ground-truth board (the perturbation control)')
    ap.add_argument('--workdir', required=True, help='work dir to audit')
    ap.add_argument('--mode', choices=('create', 'audit'), default='audit')
    ap.add_argument('--allow', action='append', default=[],
                    help='extra glob of a DECLARED truth carrier (repeatable)')
    ap.add_argument('--json', action='store_true', help='machine-readable report')
    args = ap.parse_args(argv)

    if not os.path.isfile(args.control):
        print(f'fence_audit: control not found: {args.control}', file=sys.stderr)
        return 2
    if not os.path.isdir(args.workdir):
        print(f'fence_audit: workdir not found: {args.workdir}', file=sys.stderr)
        return 2

    allow = list(DEFAULT_ALLOW) + list(args.allow)
    control_poses = recovery.board_poses(parse_kicad_pcb(args.control))
    # The control may itself live inside the work dir under any name; never
    # report the audit's own reference as a leak.
    control_real = os.path.realpath(args.control)

    rows = [r for r in scan(args.workdir, control_poses, allow)
            if os.path.realpath(os.path.join(args.workdir, r['file'])) != control_real]

    manifest_path = os.path.join(args.workdir, MANIFEST_NAME)
    manifest = None
    if args.mode == 'audit' and os.path.isfile(manifest_path):
        try:
            manifest = json.load(open(manifest_path, encoding='utf-8'))
        except Exception as exc:
            print(f'fence_audit: manifest unreadable ({exc}); every '
                  f'truth-carrying board is reported as a LEAK', file=sys.stderr)

    if args.mode == 'audit' and manifest is None:
        # SAY it. The unreadable-manifest path above warns; the ABSENT one said
        # nothing, so audit silently became strict where create had been silent
        # -- and a reader could not tell "no board carried truth" from "there
        # was no record to check against".
        print('fence_audit: no creation manifest in this work dir, so no board '
              'has provenance. Every truth-carrying board will be reported as '
              'a LEAK. Run --mode create BEFORE the run to record one.',
              file=sys.stderr)

    at_creation = set((manifest or {}).get('files', []))
    at_creation_shas = (manifest or {}).get('shas') or {}
    control_sha = (manifest or {}).get('control_sha256')
    leaks, recovered, errors = [], [], []
    for row in rows:
        if 'error' in row:
            errors.append(row)
        elif not row['carries_truth']:
            continue
        elif args.mode == 'create':
            leaks.append(row)
        elif row.get('kind') == 'record':
            # FIRST among the audit branches, because it is the one reason that
            # holds no matter what the manifest says. Ordered after them it was
            # unreachable in the commonest case -- no manifest -- and the row
            # came back "provenance unknown", which invites someone to fix it
            # by running --mode create. That would record the record and make
            # it permanently exempt. A pose RECORD carries `original_poses`
            # verbatim and no placement run reconstructs one, so provenance is
            # not the question.
            row['reason'] = ('a pose RECORD inside the fence -- records are '
                             'never reconstructed, so this is truth arriving, '
                             'not recovery')
            leaks.append(row)
        elif manifest is None:
            row['reason'] = 'no creation manifest -- provenance unknown'
            leaks.append(row)
        elif row['file'] in at_creation \
                and at_creation_shas.get(row['file']) == row.get('sha256'):
            # UNCHANGED since creation, so it is an input that already carried
            # truth. The sha is what makes that testable: this branch used to
            # key on the PATH alone, which meant a board the run REWROTE in
            # place -- a recovery landing on the control's poses -- was
            # reported as "present at work-dir creation". The better the run
            # did, the more certainly it fired. `shas` was recorded here for
            # exactly this and was never read.
            row['reason'] = 'present at work-dir creation, unchanged since'
            leaks.append(row)
        elif control_sha and row.get('sha256') == control_sha:
            # A BYTE COPY OF THE CONTROL is not a reconstruction. A real
            # recovery differs in copper, UUIDs and netclasses even when every
            # pose matches; identical bytes mean the file was copied, not
            # rebuilt. Without this, `cp control.kicad_pcb r4_final.kicad_pcb`
            # was classed "produced by the run" and exited 0.
            row['reason'] = ('byte-identical to the control -- copied, not '
                             'reconstructed')
            leaks.append(row)
        else:
            row['reason'] = 'produced by the run (recovery reaching truth)'
            recovered.append(row)

    if args.mode == 'create':
        with open(manifest_path, 'w', encoding='utf-8') as fh:
            json.dump({
                'control': os.path.relpath(args.control, args.workdir
                                           ).replace('\\', '/'),
                'control_sha256': _sha256(args.control),
                'allow': allow,
                'files': [r['file'] for r in rows],
                'shas': {r['file']: r.get('sha256') for r in rows},
            }, fh, indent=1, sort_keys=True)

    report = {
        'mode': args.mode,
        'workdir': args.workdir.replace('\\', '/'),
        'control': args.control.replace('\\', '/'),
        # `files_scanned`, not `boards_scanned`: the scan reads pose RECORDS as
        # well as boards, and a count that says "boards" while including
        # records is the same category error the name exemption was.
        'files_scanned': len(rows),
        'leaks': leaks,
        'recovered_to_truth': recovered,
        'unparseable': errors,
        'verdict': 'LEAK' if leaks else 'CLEAN',
    }
    if args.json:
        if args.mode == 'create':
            # CREATE runs with the fence UP. `worst_mm` IS the applied dose and
            # `match_frac` is the block size -- the two things the staging
            # script captures stdout to conceal. A leak verdict needs neither.
            _strip = ('match_frac', 'worst_mm', 'refs_shared', 'mtime')
            for _b in ('leaks', 'recovered_to_truth'):
                report[_b] = [{k: v for k, v in r.items() if k not in _strip}
                              for r in report[_b]]
            report['note'] = ('create mode: per-board metrics withheld -- they '
                              'disclose the perturbation dose and block size '
                              'while the fence is still up')
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        print(f'fence_audit [{args.mode}] {args.workdir}: '
              f'{len(rows)} file(s) scanned against {args.control}')
        for row in errors:
            print(f'  UNPARSEABLE {row["file"]}: {row["error"]}')
        for row in recovered:
            print(f'  ok  {row["file"]}: matches the control '
                  f'({row["match_frac"]:.3f}) -- {row["reason"]}')
        for row in leaks:
            print(f'  LEAK {row["file"]}: carries the control\'s placement '
                  f'({row["match_frac"]:.3f} of {row["refs_shared"]} refs '
                  f'within {POSE_TOL_MM}mm)'
                  + (f' -- {row["reason"]}' if row.get('reason') else ''))
        if leaks:
            _nb = sum(1 for r in leaks if r.get('kind') != 'record')
            _nr = len(leaks) - _nb
            _what = ' + '.join(([f'{_nb} board(s)'] if _nb else [])
                               + ([f'{_nr} pose record(s)'] if _nr else []))
            print(f'  VERDICT: LEAK -- {_what} carry ground truth inside the '
                  f'work dir. Move them outside the fence before the run -- '
                  f'that is what perturb(control_out=...) is for -- or declare '
                  f'them with --allow.')
        else:
            print('  VERDICT: CLEAN (no undeclared board OR pose record '
                  'carries the control\'s placement)')
    return 4 if leaks else 0


if __name__ == '__main__':
    sys.exit(main())
