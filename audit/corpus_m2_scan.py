import sys, re, glob, os, math
sys.path[:0] = ['py_router', 'wk/gpm/_audit']
from sexp_census import top_items
from kicad_parser import parse_kicad_pcb
SOCK = re.compile(r'M\.?2[ _-]|NGFF|MDT\d|2199230|KEY[_ -]?[MEB]\b|M2[_ -]?(SOCKET|CONN)|NVME', re.I)
NUT = re.compile(r'standoff|spacer|nut|PEM|9774|SMTSO|MountingHole|M2[_ ]?Screw|screw', re.I)
for p in sorted(glob.glob(sys.argv[1] + '/*.kicad_pcb')):
    name = os.path.basename(p)[:-10]
    t = open(p, encoding='utf-8', errors='replace').read()
    keep = []
    for h, blk in top_items(t):
        if h == 'zone' and re.search(r'\(keepout|\(rule_area', blk):
            pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', blk)]
            if pts:
                xs, ys = zip(*pts)
                nm = re.search(r'\(name "([^"]*)"\)', blk)
                keep.append(((min(xs), min(ys), max(xs), max(ys)), nm.group(1) if nm else ''))
    pcb = parse_kicad_pcb(p)
    socks = [(r, f) for r, f in pcb.footprints.items() if SOCK.search(f.footprint_name) and len(f.pads) > 30]
    nuts = [(r, f) for r, f in pcb.footprints.items() if NUT.search(f.footprint_name) and len(f.pads) <= 4]
    print(f'== {name}: {len(pcb.footprints)} parts, {len(socks)} M.2-like sockets, {len(nuts)} standoff/hole parts, {len(keep)} keep-out rule areas')
    for r, f in socks:
        near = sorted((math.hypot(n.x - f.x, n.y - f.y), nr, n.footprint_name.split(':')[-1][:40]) for nr, n in nuts)[:3]
        print(f'   socket {r} {f.footprint_name.split(":")[-1][:45]} at ({f.x:.1f},{f.y:.1f}) rot {f.rotation:.0f} {f.layer}')
        for dist, nr, nn in near:
            print(f'      standoff/hole {nr} {nn}: {dist:.2f} mm from the socket origin')
        # keep-out areas whose bbox touches the socket-to-nearest-standoff span
        if near:
            n = pcb.footprints[near[0][1]]
            x0, x1 = sorted((f.x, n.x)); y0, y1 = sorted((f.y, n.y))
            x0 -= 12; x1 += 12; y0 -= 12; y1 += 12
            hit = [nm or 'unnamed' for (a, b, c, d), nm in keep if a < x1 and c > x0 and b < y1 and d > y0]
            under = [rr for rr, ff in pcb.footprints.items() if x0 + 10 < ff.x < x1 - 10 and y0 + 10 < ff.y < y1 - 10 and rr not in (r, near[0][1])]
            print(f'      keep-out areas over the card span: {hit[:6]}; parts inside the span: {len(under)} {under[:10]}')
