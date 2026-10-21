#!/usr/bin/env python3
"""Make board_score's length component able to MEASURE via-in-pad joins.

Why this exists (TOOL_GAPS): net_queries.pin_pair_path_length (board_score
--length-groups, both modes) links a pad and a via only through a TRACK node
inside both discs. A via-in-pad whose tracks leave on another layer (no track
on the pad's own layer) is never linked to its pad, so a fully connected net
reads "pads not joined by track copper" and the whole length group goes
UNGRADED -- while check_connected and KiCad both see it connected and KiCad
measures its length. Measured: exp_l10/s2_it3, DQ0-DQ3 of DRAM_LDQ unjoined.

For each listed net that net_match_length cannot measure, this finds every pad
with a same-net via inside its copper and no same-layer track end at it, and
stages a 0.05 mm track on the pad's layer from the pad centre toward the via
(inside both the pad and the via copper: electrically nothing new) with
py_tools/check_join.py, which verifies it against ALL board copper and writes
the staged board. Prints the measured lengths before and after.

usage: python3 helpers/vip_joins.py IN.kicad_pcb OUT.kicad_pcb NET [NET ...]
"""
import math, os, shutil, subprocess, sys

sys.path.insert(0, 'py_router')


def lengths(board, nets):
    from kicad_parser import parse_kicad_pcb
    from net_queries import net_match_length
    pcb = parse_kicad_pcb(board)
    by = {n.name: i for i, n in pcb.nets.items()}
    return pcb, by, {n: net_match_length(pcb, by[n], mode='pin_pair') for n in nets}


def main():
    src, dst, nets = sys.argv[1], sys.argv[2], sys.argv[3:]
    subprocess.run([sys.executable, '-X', 'utf8', 'py_router/copy_board.py', src, dst], check=True,
                   stdout=subprocess.DEVNULL)
    pcb, by, before = lengths(dst, nets)
    print('before', {n.split('/')[-1]: (round(v, 2) if v else None) for n, v in before.items()})
    joins = []
    for n in nets:
        if before[n] is not None:
            continue
        nid = by[n]
        segs = [s for s in pcb.segments if s.net_id == nid]
        for p in pcb.pads_by_net.get(nid, []):
            r = max(p.size_x, p.size_y) / 2
            for v in pcb.vias:
                if v.net_id != nid or math.hypot(v.x - p.global_x, v.y - p.global_y) > r:
                    continue
                cu = [l for l in p.layers if l.endswith('.Cu')]
                if any(s.layer in cu and min(math.hypot(s.start_x - p.global_x, s.start_y - p.global_y),
                                             math.hypot(s.end_x - p.global_x, s.end_y - p.global_y)) <= r
                       for s in segs):
                    continue
                d = math.hypot(v.x - p.global_x, v.y - p.global_y)
                if d >= 0.02:
                    ex, ey = v.x, v.y
                else:
                    ex, ey = p.global_x + 0.05, p.global_y
                joins.append((n, cu[0], p.global_x, p.global_y, ex, ey))
    tmp = dst + '.staged.kicad_pcb'
    for (n, layer, x1, y1, x2, y2) in joins:
        r = subprocess.run([sys.executable, '-X', 'utf8', 'py_tools/check_join.py', dst, n,
                            f'{x1:.4f},{y1:.4f},{layer}', f'{x2:.4f},{y2:.4f},{layer}',
                            '--width', '0.1', '--keep-staged', tmp, '-q'], capture_output=True, text=True)
        verdict = (r.stdout.strip().splitlines() or [''])[-1]
        print(f'  join {n} {layer} ({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f}): {verdict}')
        if 'CLEAN' in verdict and os.path.isfile(tmp):
            shutil.move(tmp, dst)
        else:
            print('    NOT applied')
    for ext in ('.kicad_pro', '.kicad_dru', '.design-brief.json'):
        if os.path.isfile(tmp[:-len('.kicad_pcb')] + ext):
            os.remove(tmp[:-len('.kicad_pcb')] + ext)
    _, _, after = lengths(dst, nets)
    print('after ', {n.split('/')[-1]: (round(v, 2) if v else None) for n, v in after.items()})


if __name__ == '__main__':
    main()
