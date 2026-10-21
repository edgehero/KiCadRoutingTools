#!/usr/bin/env python3
"""Apply route.py's own end-of-run strict collapse (#1063) to a finished board.

Why this exists (TOOL_GAPS): route.py's `_late_strict_collapse1063` prints
"Strict collapse (#1063, end of run): removed N redundant segment(s)" but, on a
board whose file is not KiCad-10 format, calls `remove_segments_from_content`
WITHOUT the net-name map. This chain's boards are mixed-dialect (name-ref
`(net "/X")` segments beside numeric `(net 13)` ones), so every name-ref target
matches 0 blocks; the returned count is ignored and the claim is printed anyway.
Measured on exp_l10/s2_it3: 293 strict-removable segments, 0 removed from the
file, and the next run "removes" the same ~291 again. check_weird then reports
them as removable-segment and check_complete refuses the board (weird_copper).

This calls route.py's OWN pass, pcb_modification.collapse_strict_redundant, on the
parsed board exactly as _late_strict_collapse1063 does (every segment owned, no
vias owned, scope = every net), takes the segments it actually removed, and
strips them with the SAME writer function -- passing the net-name map. (A first
version removed check_weird's whole removable set at once and disconnected +5V
at U6: the set is graded per segment, not jointly; the real pass sequences.)

Then a hygiene pass for the three check_weird classes check_complete gates on and
no repo tool removes (zoned nets are exempt from the strict model): exact
same-net duplicate segments (stacked-copper: one copy kept), KiCad-dangling
slivers (a segment whose both ends lie on other same-net tracks), redundant-cycle
loop edges (removal leaves connectivity identical, per check_weird), and dangling
vias (barrel reached on one layer only). Each is copper that joins nothing new.

usage: python3 helpers/strict_collapse.py IN.kicad_pcb OUT.kicad_pcb
(OUT's siblings are copied with py_router/copy_board.py first.)
"""
import collections, os, subprocess, sys

sys.path.insert(0, 'py_router')


def collapse(pcb):
    """route.py's own pass; returns the segments it removed from pcb."""
    from pcb_modification import collapse_strict_redundant
    before = list(pcb.segments)
    scope = {nid for nid in pcb.nets if nid}
    stats = {}
    collapse_strict_redundant([{'new_segments': list(pcb.segments), 'new_vias': []}], pcb,
                              scope, keep_input_copper=False, stats=stats)
    kept = {id(x) for x in pcb.segments}
    return [x for x in before if id(x) not in kept], stats


def main():
    src, dst = sys.argv[1], sys.argv[2]
    subprocess.run([sys.executable, '-X', 'utf8', 'py_router/copy_board.py', src, dst], check=True,
                   stdout=subprocess.DEVNULL)
    from kicad_parser import parse_kicad_pcb
    from kicad_writer import remove_segments_from_content
    total = 0
    for rnd in range(10):
        pcb = parse_kicad_pcb(dst)
        rem, st = collapse(pcb)
        if not rem:
            break
        content = open(dst, encoding='utf-8').read()
        name_of = {i: n.name for i, n in pcb.nets.items()}
        content, n = remove_segments_from_content(content, rem, net_id_to_name=name_of)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'round {rnd + 1}: {len(rem)} strict-removable segment(s), {n} removed from the file')
        total += n
        if n == 0:
            print('  nothing matched in the file: stopping')
            break
    print(f'strict_collapse: removed {total} segment(s) in all -> {dst}')
    hygiene(dst)


def hygiene(dst):
    import re
    import check_weird as cw
    from kicad_parser import parse_kicad_pcb
    from kicad_writer import remove_segments_from_content, remove_vias_from_content
    pcb = parse_kicad_pcb(dst)
    name_of = {i: n.name for i, n in pcb.nets.items()}
    groups = collections.defaultdict(list)
    for sg in pcb.segments:
        a = (round(sg.start_x, 3), round(sg.start_y, 3))
        b = (round(sg.end_x, 3), round(sg.end_y, 3))
        groups[(sg.net_id, sg.layer, frozenset((a, b)))].append(sg)
    dups = [x for g in groups.values() if len(g) > 1 for x in g[1:]]
    findings, _ = cw.check_weird(pcb, tolerance=0)
    slivers, vias = [], []
    for f in findings:
        if f['category'] in ('kicad-dangling', 'redundant-cycle'):
            m = re.search(r'(?:segment|loop edge) \(([-\d.]+), ([-\d.]+)\)-\(([-\d.]+), ([-\d.]+)\)', f['detail'])
            if m:
                p1 = (float(m.group(1)), float(m.group(2))); p2 = (float(m.group(3)), float(m.group(4)))
                for sg in pcb.segments:
                    if name_of.get(sg.net_id) == f['net'] and sg.layer == f['layer'] and {
                            (round(sg.start_x, 3), round(sg.start_y, 3)),
                            (round(sg.end_x, 3), round(sg.end_y, 3))} == {p1, p2}:
                        slivers.append(sg)
                        break
        elif f['category'] == 'dangling-via':
            for v in pcb.vias:
                if name_of.get(v.net_id) == f['net'] and abs(v.x - f['x']) < 0.002 and abs(v.y - f['y']) < 0.002:
                    vias.append(v)
                    break
    content = open(dst, encoding='utf-8').read()
    content, n1 = remove_segments_from_content(content, dups + slivers, net_id_to_name=name_of)
    content, n2 = remove_vias_from_content(content, vias, net_id_to_name=name_of)
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'hygiene: {len(dups)} stacked duplicate(s) + {len(slivers)} KiCad-dangling sliver(s) -> '
          f'{n1} segment(s) removed; {len(vias)} dangling via(s) -> {n2} removed')


if __name__ == '__main__':
    main()
