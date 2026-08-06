#!/usr/bin/env python3
"""The recovery table, measured — not assembled by hand.

    python3 -X utf8 tests/stress/arm_report.py <workdir> --result <board> \
        [--human <the original routed board>] [--out REPORT.md]

Emits one table, one row per version of the board:

    | run | recovery | home /N | vias | copper mm | buildable |

Every number comes from the instrument that owns it. That is the whole point:
the last run's table was written by hand and three of its numbers were wrong in
the flattering direction — pad CENTRES quoted as pad copper (so every excursion
was understated and the fourth off-board part vanished from a list the same
paragraph counted as four), three of six unrepairable parts quoted, and a stop
condition claimed with two of five laps used.

TRUTH OPENS AT ONE POINT, and it is marked below. Everything before it reads
only the boards in the work dir. The control's poses arrive inside the perturb
record (`original_poses`), which is why the fence forbids that file to the run
itself and allows it here.

Two rules inherited from `placement/recovery.py`, both of which the previous
arm broke:

  * displacement is measured in PAD space, not between footprint origins. A
    part rotated in place moves its origin 0.00 mm and its pads up to 49 mm,
    so an origin-distance "home" count reports a rotated part as home. The
    correct value is already computed by `displacement_to_original`.
  * `N` is the FROZEN perturbed member list, never re-derived from the board.
    Re-deriving it scores a different set of parts at every dose.

Exit: 0 wrote the report, 2 usage/missing inputs.
"""
import argparse
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ.setdefault('KRT_NO_BANNER', '1')

SKILL_SCRIPTS = os.path.join(ROOT, '.claude', 'skills', 'plan-pcb-routing',
                             'scripts')
PY = [sys.executable, '-X', 'utf8']


def _run(args, timeout=1800):
    p = subprocess.run(PY + args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', cwd=ROOT,
                       timeout=timeout)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def quality(board):
    """vias / copper_mm / segments, from board_score's own helper."""
    sys.path.insert(0, SKILL_SCRIPTS)
    try:
        import board_score
        return board_score.quality(board)
    except Exception as exc:                                # noqa: BLE001
        return {'error': f'{type(exc).__name__}: {exc}'}


def buildable(board, clearance, tmp):
    """check_assembly's own verdict, read from its JSON rather than its text."""
    jp = os.path.join(tmp, os.path.basename(board) + '.assembly.json')
    code, out = _run(['check_assembly.py', board, '--clearance',
                      str(clearance), '--json', jp])
    if not os.path.isfile(jp):
        return {'error': f'check_assembly exit {code}', 'log': out[-300:]}
    with open(jp, encoding='utf-8') as fh:
        doc = json.load(fh)
    # `buildable`/`verdict` are keys now; recompute only for an older JSON, and
    # say so rather than silently disagreeing with the tool.
    if 'buildable' not in doc:
        doc['buildable'] = not (doc.get('blocking')
                                or doc.get('locked_contact_pairs'))
        doc['verdict'] = 'derived (tool predates the verdict key)'
    return doc


def _fmt(v, nd=2):
    if v is None:
        return '—'
    if isinstance(v, float):
        return f'{v:.{nd}f}'
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('workdir')
    ap.add_argument('--result', required=True,
                    help='the board this run produced')
    ap.add_argument('--control', default=None,
                    help='the control board (default <workdir>/'
                         'perturbed.control.kicad_pcb) -- used for the fence '
                         'audit only; the poses come from the perturb record')
    ap.add_argument('--record', default=None,
                    help='the perturb record (default <workdir>/'
                         'perturbed.perturb.json)')
    ap.add_argument('--damaged', default=None,
                    help='the damaged input (default <workdir>/'
                         'perturbed.kicad_pcb)')
    ap.add_argument('--human', default=None,
                    help='the original ROUTED board, for the reference row')
    ap.add_argument('--clearance', type=float, default=None,
                    help="default: the board's own Default netclass")
    ap.add_argument('--out', default=None,
                    help='default <workdir>/REPORT.md')
    a = ap.parse_args(argv)

    wd = a.workdir
    if not os.path.isdir(wd):
        print(f'no such work dir: {wd}', file=sys.stderr)
        return 2
    damaged = a.damaged or os.path.join(wd, 'perturbed.kicad_pcb')
    control = a.control or os.path.join(wd, 'perturbed.control.kicad_pcb')
    record_p = a.record or os.path.join(wd, 'perturbed.perturb.json')
    for p in (damaged, a.result, record_p):
        if not os.path.isfile(p):
            print(f'missing input: {p}', file=sys.stderr)
            return 2

    clearance = a.clearance
    if clearance is None:
        from list_nets import board_default_netclass_clearance
        clearance = board_default_netclass_clearance(damaged) or 0.25

    tmp = os.path.join(wd, '_report')
    os.makedirs(tmp, exist_ok=True)

    # ---- board-only measurements ------------------------------------------
    rows = []
    for label, board in (('damaged input', damaged), ('this run', a.result)):
        rows.append({'run': label, 'board': board, 'quality': quality(board),
                     'assembly': buildable(board, clearance, tmp)})

    human = None
    if a.human and os.path.isfile(a.human):
        from tests.stress.compare_to_original import (profile,
                                                      original_degeneracy)
        prof = profile(a.human)
        # A "human original" with no copper cannot be a reference, and 7 of 75
        # wave references had none. Say which, rather than printing zeros as
        # though they were a comparison.
        human = {'run': 'human original', 'board': a.human, 'profile': prof,
                 'degeneracy': original_degeneracy(prof),
                 'quality': quality(a.human),
                 'assembly': buildable(a.human, clearance, tmp)}

    # ---- truth opens HERE, and only here ----------------------------------
    from placement import recovery as R
    from kicad_parser import parse_kicad_pcb
    with open(record_p, encoding='utf-8') as fh:
        record = json.load(fh)
    orig = {r: tuple(v) for r, v in (record.get('original_poses') or {}).items()}
    members = list((record.get('block') or {}).get('members') or [])
    n = len(members)

    def displacement(board):
        pcb = parse_kicad_pcb(board)
        return R.displacement_to_original(R.board_poses(pcb), orig,
                                          pcb.footprints, subset=members)

    d_dmg = displacement(damaged)
    d_res = displacement(a.result)
    d0, d1 = d_dmg['perturbed_pad_rms'], d_res['perturbed_pad_rms']

    def home_count(d):
        frac = d.get('parts_home_frac')
        return None if frac is None else int(round(frac * n))

    rows[0].update(recovery=None, home=home_count(d_dmg), rms=d0,
                   displacement=d_dmg)
    rows[1].update(recovery=R.recovery_fraction(d0, d1),
                   home=home_count(d_res), rms=d1, displacement=d_res)
    if human:
        human.update(recovery=None, home=n, rms=0.0)

    code, fence = _run(['tests/stress/fence_audit.py', '--control', control,
                        '--workdir', wd, '--mode', 'audit'])
    fence_verdict = next((ln.strip() for ln in fence.splitlines()
                          if 'VERDICT:' in ln), f'fence_audit exit {code}')

    # ---- the table ---------------------------------------------------------
    all_rows = rows + ([human] if human else [])
    out = [f'# Recovery report — {os.path.basename(wd)}', '',
           f'Clearance floor {clearance} mm, read off the board. '
           f'N = {n} (the frozen perturbed member list, '
           f'{d_res.get("members_scored")} scored).', '',
           '| run | recovery | home /' + str(n)
           + ' | vias | copper mm | buildable |',
           '|---|---|---|---|---|---|']
    for r in all_rows:
        q, asm = r.get('quality') or {}, r.get('assembly') or {}
        out.append('| {} | {} | {} | {} | {} | {} |'.format(
            r['run'],
            '—' if r.get('recovery') is None else f'{r["recovery"]:+.4f}',
            _fmt(r.get('home')), _fmt(q.get('vias')),
            _fmt(q.get('copper_mm'), 1),
            'yes' if asm.get('buildable') else 'NO'))
    out += ['',
            f'- fence: {fence_verdict}',
            f'- distance to truth (pad RMS): damaged {d0:.4f} → '
            f'result {d1:.4f}',
            '- `home` is pad-space, at '
            f'`recovery.HOME_TOLERANCE_MM` = {R.HOME_TOLERANCE_MM} mm — a part '
            'rotated in place moves its origin 0.00 mm and its pads much '
            'further, so an origin-distance count would call it home.']
    if d_res.get('rot_mismatch_total'):
        out.append(f'- rotation mismatches: {d_res["rot_mismatch_total"]} '
                   f'({", ".join(d_res.get("rot_mismatch") or [])})')
    if human and human['degeneracy']:
        out.append(f'- **the human reference is {human["degeneracy"]}** — its '
                   f'copper cannot serve as a comparison, so read that row as '
                   f'a placement reference only.')
    for r in all_rows:
        asm = r.get('assembly') or {}
        if asm.get('error'):
            out.append(f'- {r["run"]}: assembly UNMEASURED ({asm["error"]})')
        elif not asm.get('buildable'):
            out.append(f'- {r["run"]}: {asm.get("verdict")} — blocking '
                       f'{asm.get("blocking")}, locked contacts '
                       f'{asm.get("locked_contacts")}, '
                       f'{asm.get("oob_pad_count")} part(s) with pad copper '
                       f'off-board')

    text = '\n'.join(out) + '\n'
    dest = a.out or os.path.join(wd, 'REPORT.md')
    with open(dest, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print(text)
    print(f'REPORT -> {dest}')
    jp = os.path.splitext(dest)[0] + '.json'
    with open(jp, 'w', encoding='utf-8') as fh:
        json.dump({'workdir': wd, 'clearance': clearance, 'N': n,
                   'fence': fence_verdict, 'rows': all_rows}, fh, indent=1,
                  sort_keys=True, default=str)
    print(f'JSON   -> {jp}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
