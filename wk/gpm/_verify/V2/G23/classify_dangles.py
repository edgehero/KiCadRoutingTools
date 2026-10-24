"""For every check_weird dangling-end finding, report whether the free end's
copper (a disc of half its track width) overlaps OTHER same-net copper on its
layer: another segment's capsule (excluding segments sharing a vertex with the
finding's own segment), a pad on that layer, or a via. Read-only."""
import sys, math, json
sys.path[:0] = ['py_router', '.']
from kicad_parser import parse_kicad_pcb
from check_weird import check_weird

def pseg(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-ax-t*dx, py-ay-t*dy), t

def main(path, kdrc=None):
    pcb = parse_kicad_pcb(path)
    f, _ = check_weird(pcb, tolerance=0.1)
    dang = [x for x in f if x['category'] == 'dangling-end']
    kd = []
    if kdrc:
        d = json.load(open(kdrc))
        for v in d['violations']:
            if v['type'] == 'track_dangling':
                kd.append((v['items'][0]['pos']['x'], v['items'][0]['pos']['y'], v['items'][0]['description']))
    out = []
    for x in dang:
        nid = [n for n, v in pcb.nets.items() if v.name == x['net']][0]
        P = (x['x'], x['y']); L = x['layer']
        own = None
        for s in pcb.segments:
            if s.net_id == nid and s.layer == L and any(abs(a-P[0]) < 1e-3 and abs(b-P[1]) < 1e-3 for a, b in ((s.start_x, s.start_y), (s.end_x, s.end_y))):
                own = s; break
        r = own.width/2 if own else 0
        verts = {(round(own.start_x, 3), round(own.start_y, 3)), (round(own.end_x, 3), round(own.end_y, 3))} if own else set()
        best = None
        for s in pcb.segments:
            if s is own or s.net_id != nid or s.layer != L: continue
            if {(round(s.start_x, 3), round(s.start_y, 3)), (round(s.end_x, 3), round(s.end_y, 3))} & verts: continue
            d, t = pseg(P[0], P[1], s.start_x, s.start_y, s.end_x, s.end_y)
            ov = r + s.width/2 - d
            if best is None or ov > best[0]:
                best = (ov, d, s.width, 'end' if t in (0, 1) else 'interior')
        kic = [k for k in kd if math.hypot(k[0]-P[0], k[1]-P[1]) < 0.02]
        out.append(dict(net=x['net'], layer=L, at=P, own_w=own.width if own else None,
                        overlap_mm=round(best[0], 4) if best else None,
                        partner_w=best[2] if best else None, where=best[3] if best else None,
                        kicad_track_dangling_here=bool(kic), detail=x['detail'][:60]))
    for o in out: print(json.dumps(o))
    ov = [o for o in out if o['overlap_mm'] and o['overlap_mm'] > 0]
    print(f"SUMMARY {path}: dangling-end {len(out)}; free end overlaps same-net copper {len(ov)} "
          f"(of which KiCad flags track_dangling there: {sum(o['kicad_track_dangling_here'] for o in ov)}); "
          f"KiCad track_dangling total {len(kd) if kdrc else 'n/a'}")

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
