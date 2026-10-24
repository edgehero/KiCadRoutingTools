import sys, re, os, math
sys.path[:0] = ['py_router', 'wk/gpm/_audit']
from kicad_parser import parse_kicad_pcb
from sexp_census import top_items
D = sys.argv[1]
CASES = {'job_storage_exp': ('J3', 'H2'), 'reterminal_em': ('J2', 'J3'), 'jetson_nano_bb': ('J8', None), 'cm4_baseboard': ('J501', None), 'f3_nvme_backplane': ('J2', None)}
for name, (sref, nref) in CASES.items():
    p = os.path.join(D, name + '.kicad_pcb'); pcb = parse_kicad_pcb(p); t = open(p, errors='replace').read()
    s = pcb.footprints[sref]
    cx = sum(q.global_x for q in s.pads) / len(s.pads); cy = sum(q.global_y for q in s.pads) / len(s.pads)
    # card direction: from the pad row toward the part's courtyard far side = toward the standoff if known, else the
    # board axis on which the socket's origin sits farther from its pads
    if nref:
        n = pcb.footprints[nref]; dx, dy = n.x - cx, n.y - cy; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    else:
        cands = []
        for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            near = [ff for rr, ff in pcb.footprints.items() if re.search(r'Spacer|standoff|SMSI|9774|MountingHole', ff.footprint_name, re.I)
                    and abs(-(ff.x - cx) * uy + (ff.y - cy) * ux) < 4 and 18 < (ff.x - cx) * ux + (ff.y - cy) * uy < 85]
            cands.append((len(near), ux, uy, near))
        k, ux, uy, near = max(cands, key=lambda c: c[0])
        L = min(((ff.x - cx) * ux + (ff.y - cy) * uy) for ff in near) if near else 80.0
        nref = near[0].reference if near else None
    side = s.layer
    under = []
    for rr, ff in pcb.footprints.items():
        if rr in (sref, nref) or ff.layer != side: continue
        a = (ff.x - cx) * ux + (ff.y - cy) * uy; b = -(ff.x - cx) * uy + (ff.y - cy) * ux
        if 2 < a < L - 1 and abs(b) < 11: under.append(rr)
    keeps = 0; kinfo = []
    for h, blk in top_items(t):
        if h == 'zone' and re.search(r'\(keepout|\(rule_area', blk):
            pts = [(float(x), float(y)) for x, y in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', blk)]
            if any(2 < (x - cx) * ux + (y - cy) * uy < L and abs(-(x - cx) * uy + (y - cy) * ux) < 11 for x, y in pts):
                keeps += 1
                lay = re.search(r'\(layers? ([^)]*)\)', blk); rules = re.findall(r'\((tracks|vias|pads|copperpour|footprints) not_allowed\)', blk)
                kinfo.append(((lay.group(1)[:30] if lay else '?'), rules))
    print(f'{name}: socket {sref} on {side}; standoff {nref or "none on the card axis"} at {L:.1f} mm; '
          f'{len(under)} parts under the card on {side} {under[:8]}; keep-out rule areas over the card: {keeps} {kinfo[:3]}')
