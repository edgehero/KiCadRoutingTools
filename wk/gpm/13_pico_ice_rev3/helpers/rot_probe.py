"""rot_probe.py -- rank the four quarter turns of a chip by how its signal pins face their partners.

    python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/rot_probe.py BOARD REF [REF ...]

For each REF and each absolute rotation 0/90/180/270 (about the footprint origin, the
way place_pose `rotate` turns it), every pad on a signal net (not GND, not a rail
reaching more than 25% of the parts) is moved with the turn; for that pad we take the
nearest pad of ANOTHER part on its net and report
  * dist  : sum over pads of the straight distance to that partner pad,
  * behind: pads whose partner lies BEHIND the pad's own side of the chip (the pad's
            outward normal points away from the partner: dot < 0) -- each such net has
            to run round the chip or drop a via under it,
  * pads  : the pads counted.
Written because no repo tool ranks a chip's rotations by its escape facing
(TOOL_GAPS: "no rotation ranker"); it reads geometry only and writes nothing.
"""
import math
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402


def main():
    board, refs = sys.argv[1], sys.argv[2:]
    pcb = parse_kicad_pcb(board)
    n_parts = len(pcb.footprints)
    owners = {}
    for ref, fp in pcb.footprints.items():
        for p in fp.pads:
            if p.net_id:
                owners.setdefault(p.net_id, set()).add(ref)
    rails = {nid for nid, s in owners.items()
             if len(s) > 0.25 * n_parts or 'GND' in (pcb.nets[nid].name or '').upper()}
    for ref in refs:
        fp = pcb.footprints[ref]
        cur = fp.rotation % 360
        print(f'== {ref} at ({fp.x:.2f}, {fp.y:.2f}) rot {cur:.0f} {fp.layer}')
        xs = [p.local_x for p in fp.pads]
        ys = [p.local_y for p in fp.pads]
        hx, hy = (max(xs) - min(xs)) / 2 or 1, (max(ys) - min(ys)) / 2 or 1
        for rot in (0, 90, 180, 270):
            th = math.radians(rot)
            dist = behind = n = 0
            for p in fp.pads:
                if not p.net_id or p.net_id in rails:
                    continue
                others = [q for r2, f2 in pcb.footprints.items() if r2 != ref
                          for q in f2.pads if q.net_id == p.net_id]
                if not others:
                    continue
                # the parser's local frame is already mirrored for a B-side part:
                # this transform reproduces global_x/y exactly on both faces
                lx, ly = p.local_x, p.local_y
                # KiCad: positive angle turns counter-clockwise on screen (y down)
                gx = fp.x + lx * math.cos(th) + ly * math.sin(th)
                gy = fp.y - lx * math.sin(th) + ly * math.cos(th)
                # outward normal of the pad's side, in local frame, then turned
                nxl, nyl = (lx / hx, 0.0) if abs(lx / hx) >= abs(ly / hy) else (0.0, ly / hy)
                nx = nxl * math.cos(th) + nyl * math.sin(th)
                ny = -nxl * math.sin(th) + nyl * math.cos(th)
                q = min(others, key=lambda q: math.hypot(q.global_x - gx, q.global_y - gy))
                dx, dy = q.global_x - gx, q.global_y - gy
                d = math.hypot(dx, dy)
                dist += d
                n += 1
                if d > 0.5 and (nx * dx + ny * dy) < 0:
                    behind += 1
            mark = '  <- current' if abs(rot - cur) < 1 else ''
            print(f'   rot {rot:3d}: pads {n:3d}  dist {dist:8.1f} mm  behind {behind:3d}{mark}')


if __name__ == '__main__':
    main()
