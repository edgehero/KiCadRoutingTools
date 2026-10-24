import sys, re, glob, os, math
sys.path[:0] = ['py_router']
from kicad_parser import parse_kicad_pcb
LEN = (22, 30, 42, 60, 80)
for p in sorted(glob.glob(sys.argv[1] + '/*.kicad_pcb')):
    name = os.path.basename(p)[:-10]
    pcb = parse_kicad_pcb(p)
    for r, f in pcb.footprints.items():
        if not (re.search(r'M\.?2|NGFF|MDT\d|2199230', f.footprint_name, re.I) and len(f.pads) > 60):
            continue
        # card axis: the socket's pads sit on one side; the card leaves along the direction from pad centroid to origin...
        # take both directions along each board axis and keep the one with hits
        cx = sum(pp.global_x for pp in f.pads) / len(f.pads); cy = sum(pp.global_y for pp in f.pads) / len(f.pads)
        best = []
        for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            hits = []
            for rr, ff in pcb.footprints.items():
                if rr == r: continue
                dx, dy = ff.x - cx, ff.y - cy
                along, side = dx * ax + dy * ay, abs(-dx * ay + dy * ax)
                L = next((L for L in LEN if abs(along - L) <= 2.5), None)
                if L and side <= 4:
                    hits.append((L, round(along, 2), rr, ff.footprint_name.split(':')[-1][:45], len(ff.pads)))
            if len(hits) > len(best): best = hits
        print(f'{name}: socket {r} ({f.footprint_name.split(":")[-1][:40]}) on {f.layer}; parts on its card axis at card lengths: {sorted(best)[:6]}')
