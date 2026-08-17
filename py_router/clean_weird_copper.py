#!/usr/bin/env python3
"""Remove the copper `check_weird` proves is redundant. The missing half.

`check_weird.py` is read-only by design and says so in its own help. That was
fine while nothing gated on it -- and `check_complete` does, through its
`weird_copper` component, which lands in the INCOMPLETE reasons and so in L5's
converge-vs-close-out cross-check. Measured on a board `route.py` had just
routed 83/83 with DRC 0 and connectivity 0:

    removable-segment: 89
    dangling-via:      1
    -> check_complete: INCOMPLETE -- weird_copper: not clean (exit 1)
    -> loop_driver L5: TWO INSTRUMENTS DISAGREE ... refuses to close

So a correct board could not be closed out, the finding named no tool that
could act on it, and the only exit was `--accept-unclosed agreement`, which
blanket-waives the very cross-check L5 exists to run. This is that tool.

WHAT IT REMOVES, and nothing else:

  removable-segment  a track whose exclusion leaves (num_components,
                     disconnected-pad count) UNCHANGED. `check_weird` proves
                     that on a width-CLAMPED graph on purpose, so a one-grid
                     jog whose neighbours only meet through their end caps is
                     NOT called removable -- that fragile cap-overlap joint is
                     the class `close_soft_joints` exists to bridge (#322).
  dangling-via       a via spanning >1 layer that same-net copper reaches on
                     one only, so it joins nothing. KiCad's own `via_dangling`.

Deliberately NOT removed: `unsupported-via` (floating -- it may be a
deliberate stitching via a later plane step will use), `stacked-copper`,
`soft-joint`, `dangling-end`, `cycle`, `orphan-island`. Every one of those is
either a real defect needing a decision or copper another pass owns; this tool
only deletes what has a proof attached.

THE SAFETY GATE IS NOT OPTIONAL. Removability is proven per-segment against the
UNMODIFIED board, so removing a SET is not automatically safe -- two segments
can each be individually redundant and jointly load-bearing (a parallel pair).
So the removal is verified after the fact: connectivity is re-analysed on the
result and any net whose component count or disconnected-pad count got worse
causes the whole pass to ABORT without writing. `--iterate` re-proves and
re-removes until a pass is clean, which is what actually converges a parallel
pair rather than guessing at one.

    python3 -X utf8 clean_weird_copper.py routed.kicad_pcb out.kicad_pcb
    python3 -X utf8 clean_weird_copper.py routed.kicad_pcb --in-place --iterate
    python3 -X utf8 clean_weird_copper.py routed.kicad_pcb --dry-run

Exit codes: 0 wrote (or nothing to do), 2 usage/parse, 3 the safety gate
tripped and nothing was written.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#: The finding categories this tool is willing to delete. Everything else
#: `check_weird` reports is left alone -- see the module docstring.
REMOVABLE_CATEGORIES = ('removable-segment', 'dangling-via')


def _conn_key(pcb_data):
    """{net_id: (num_components, disconnected_pads)} for every multi-pad net.

    The quantity the removal must not worsen, measured the same way
    `check_weird._check_removable` measures it so the two cannot drift.
    """
    from collections import defaultdict
    from check_connected import check_net_connectivity, analyze_conn_excluding
    segs, vias, zones = (defaultdict(list), defaultdict(list),
                         defaultdict(list))
    for s in pcb_data.segments:
        segs[s.net_id].append(s)
    for v in pcb_data.vias:
        vias[v.net_id].append(v)
    for z in (pcb_data.zones or []):
        zones[z.net_id].append(z)
    out = {}
    for net_id, pads in (pcb_data.pads_by_net or {}).items():
        if not net_id or len(pads or []) < 2:
            continue
        try:
            # The SAME call `_check_removable` makes, so the gate and the proof
            # cannot drift -- but on the UNCLAMPED copper, because this is
            # asking "is the board still connected", not "is this jog
            # load-bearing".
            r = check_net_connectivity(net_id, segs.get(net_id, []),
                                       vias.get(net_id, []), pads or [],
                                       zones.get(net_id, []),
                                       return_graph=True)
            g = r.get('graph')
            if not g:
                continue
            a = analyze_conn_excluding(g, ())
            out[net_id] = (a['num_components'], len(a['disconnected_pads']))
        except Exception:                                   # noqa: BLE001
            continue
    return out


def collect_removable(pcb_data, tolerance=0.1, thorough=False):
    """(segments, vias, findings, refused) -- what to delete, and what not.

    `refused` is the findings whose removal WOULD break the net, with the
    connectivity key it would have produced. They are reported rather than
    dropped: a finding that cannot be acted on is exactly the shape of the
    problem this tool exists to solve, and hiding it would recreate it.

    GREEDY AND RE-PROVED, not "everything check_weird listed". Each finding is
    proven against the UNMODIFIED board, so the set is not safe just because
    its members are: measured on splitflap_driver, removing all 89 at once
    broke GND and /MOTOR_E_PHASE_B, because two individually-redundant
    segments were jointly load-bearing (a parallel pair -- drop either and the
    other carries; drop both and the net splits).

    So candidates are accepted ONE AT A TIME against the copper as it stands
    after the accepted ones, per net. The first of a parallel pair is taken and
    the second is then no longer redundant, so it is refused -- which is the
    correct answer rather than a guess at which to keep. The post-write gate in
    `clean_once` stays as a backstop, but it should now never fire.
    """
    from collections import defaultdict
    from check_weird import check_weird
    from check_connected import check_net_connectivity, analyze_conn_excluding

    findings, _skipped = check_weird(pcb_data, thorough=thorough, quiet=True,
                                     tolerance=tolerance)
    by_net = defaultdict(list)
    vias, keep = [], []
    for f in findings:
        if f.get('category') not in REMOVABLE_CATEGORIES:
            continue
        obj = f.get('obj')
        if obj is None:
            continue                    # nothing to act on; leave it reported
        # BOTH kinds are re-proved. "A dangling via joins no LAYERS, so it
        # cannot be load-bearing" is false and cost a broken GND to learn: the
        # via still has copper on the layer copper DOES reach it on, and two
        # tracks meeting at that point can be relying on its pad to bridge
        # them. Spanning nothing vertically says nothing about horizontally.
        by_net[obj.net_id].append((f, obj))

    all_segs = defaultdict(list)
    all_vias = defaultdict(list)
    all_zones = defaultdict(list)
    for sg in pcb_data.segments:
        all_segs[sg.net_id].append(sg)
    for v in pcb_data.vias:
        all_vias[v.net_id].append(v)
    for z in (pcb_data.zones or []):
        all_zones[z.net_id].append(z)

    def _key(net_id, segs, vias_now):
        r = check_net_connectivity(net_id, segs, vias_now,
                                   pcb_data.pads_by_net.get(net_id, []),
                                   all_zones.get(net_id, []), return_graph=True)
        g = r.get('graph')
        if not g:
            return None
        a = analyze_conn_excluding(g, ())
        return (a['num_components'], len(a['disconnected_pads']))

    segs_out, refused = [], []
    for net_id, cands in by_net.items():
        live_s = list(all_segs.get(net_id, []))
        live_v = list(all_vias.get(net_id, []))
        base = _key(net_id, live_s, live_v)
        if base is None:
            continue
        for f, obj in cands:
            is_via = f['category'] == 'dangling-via'
            if is_via:
                trial_v = [x for x in live_v if x is not obj]
                trial_s = live_s
                if len(trial_v) == len(live_v):
                    continue
            else:
                trial_s = [x for x in live_s if x is not obj]
                trial_v = live_v
                if len(trial_s) == len(live_s):
                    continue
            if _key(net_id, trial_s, trial_v) == base:
                live_s, live_v = trial_s, trial_v
                (vias if is_via else segs_out).append(obj)
                keep.append(f)
            else:
                refused.append((f, _key(net_id, trial_s, trial_v), base))
    return segs_out, vias, keep, refused


def clean_once(board_in, board_out, tolerance=0.1, thorough=False,
               dry_run=False, verbose=True):
    """One prove-then-remove pass. Returns (n_segs, n_vias, aborted)."""
    from kicad_parser import parse_kicad_pcb
    from kicad_writer import (remove_segments_from_content,
                              remove_vias_from_content)
    pcb = parse_kicad_pcb(board_in)
    before = _conn_key(pcb)
    segs, vias, findings, refused = collect_removable(pcb, tolerance, thorough)
    if verbose and refused:
        print(f"  REFUSED {len(refused)} finding(s): removal would BREAK the "
              f"net, so they are not redundant however they are labelled.")
        for f, would, base in refused[:6]:
            print(f"    {f['category']} net {f['net']} at "
                  f"({f['x']:.3f}, {f['y']:.3f}): {base} -> {would} "
                  f"(components, disconnected pads)")
        print(f"    These need a JOIN-then-delete repair (close the joint the "
              f"object is bridging, THEN remove it), which no tool here does "
              f"yet. Deleting them alone ships a broken net.")
    if not segs and not vias:
        if verbose:
            print("  nothing safe to remove")
        return 0, 0, False
    if verbose:
        print(f"  removable: {len(segs)} segment(s), {len(vias)} via(s)")
        for f in findings[:8]:
            print(f"    {f['category']} net {f['net']} ({f['layer']}) "
                  f"at ({f['x']:.3f}, {f['y']:.3f})")
        if len(findings) > 8:
            print(f"    ... and {len(findings) - 8} more")
    if dry_run:
        return len(segs), len(vias), False

    with open(board_in, encoding='utf-8') as fh:
        content = fh.read()
    n_s = n_v = 0
    if segs:
        content, n_s = remove_segments_from_content(
            content, segs, getattr(pcb, 'net_id_to_name', None) or None)
    if vias:
        content, n_v = remove_vias_from_content(
            content, vias, getattr(pcb, 'net_id_to_name', None) or None)

    tmp = board_out + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(content)

    # THE GATE. Removability was proven per-segment against the ORIGINAL board;
    # a SET is a different question. Re-analyse the result and refuse to keep it
    # if any net got worse.
    after = _conn_key(parse_kicad_pcb(tmp))
    worse = [nid for nid, key in before.items()
             if after.get(nid, key) > key]
    if worse:
        names = [(pcb.nets[n].name if n in pcb.nets else str(n))
                 for n in worse[:6]]
        print(f"  ABORTED: removing that set made {len(worse)} net(s) WORSE "
              f"({', '.join(names)}). Nothing written. Each segment is "
              f"individually redundant; jointly they were not -- re-run with "
              f"--iterate, which removes one proven set at a time and "
              f"re-proves.", file=sys.stderr)
        os.unlink(tmp)
        return 0, 0, True
    os.replace(tmp, board_out)
    if verbose:
        print(f"  removed {n_s} segment(s) and {n_v} via(s); connectivity "
              f"unchanged on all {len(before)} multi-pad net(s)")
    return n_s, n_v, False


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board')
    ap.add_argument('output', nargs='?',
                    help='output board (default: --in-place required)')
    ap.add_argument('--in-place', action='store_true',
                    help='rewrite the input board (a .bak is kept)')
    ap.add_argument('--dry-run', action='store_true',
                    help='report what would go, write nothing')
    ap.add_argument('--iterate', action='store_true',
                    help='repeat until a pass finds nothing. Removability is '
                         'proven against the board as it IS, so one pass can '
                         'expose the next (removing one of a parallel pair '
                         'makes the other load-bearing, and vice versa)')
    ap.add_argument('--max-passes', type=int, default=8)
    ap.add_argument('--tolerance', type=float, default=0.1,
                    help='drop findings smaller than this (mm). Default 0.1 to '
                         'MATCH check_weird.py, which is what check_complete '
                         'runs -- so a default clean clears exactly what the '
                         'gate flags. `--tolerance 0` also sweeps the sub-0.1mm '
                         'slivers (197 vs 89 on the measured board); they are '
                         'proven redundant too, just not what anything gates on')
    ap.add_argument('--thorough', action='store_true',
                    help='also scan nets with >500 segments (slow)')
    a = ap.parse_args(argv)

    if not os.path.isfile(a.board):
        print(f"no such board: {a.board}", file=sys.stderr)
        return 2
    if not a.dry_run and not a.output and not a.in_place:
        print("give an output path, or --in-place, or --dry-run",
              file=sys.stderr)
        return 2

    out = a.output
    if a.in_place and not a.dry_run:
        shutil.copy2(a.board, a.board + '.bak')
        out = a.board
    elif a.dry_run:
        out = None

    print(f"Cleaning weird copper in {a.board}:")
    total_s = total_v = 0
    src = a.board
    for lap in range(1, (a.max_passes if a.iterate else 1) + 1):
        if a.iterate:
            print(f"  pass {lap}:")
        n_s, n_v, aborted = clean_once(
            src, out or src, tolerance=a.tolerance, thorough=a.thorough,
            dry_run=a.dry_run)
        if aborted:
            return 3
        total_s += n_s
        total_v += n_v
        if a.dry_run or not a.iterate or (n_s == 0 and n_v == 0):
            break
        src = out                        # the next pass proves against the result
    if a.dry_run:
        print(f"DRY RUN: would remove {total_s} segment(s), {total_v} via(s)")
    else:
        print(f"removed {total_s} segment(s) and {total_v} via(s) -> {out}")
    return 0


if __name__ == '__main__':
    import cli_banner
    cli_banner.install()
    sys.exit(main())
