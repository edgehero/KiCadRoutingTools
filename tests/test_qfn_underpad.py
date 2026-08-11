#!/usr/bin/env python3
"""Issue #164: qfn_fanout --escape-method underpad drops a clearing via per pad.

Escapes a fine-pitch QFN diff pair (tigard U3, QFN-64 0.5mm, /USB_DP+/USB_DN)
by dropping a staggered through-via just past each pad instead of the surface
45-degree fan. Asserts both halves escape and the two different-net vias clear.

Uses kicad_files/tigard.kicad_pcb; skips cleanly if absent.
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from kicad_parser import parse_kicad_pcb
from qfn_fanout import generate_qfn_fanout

BOARD = os.path.join(ROOT, "kicad_files", "tigard.kicad_pcb")

VIA_SIZE, CLEARANCE = 0.45, 0.1


def main():
    if not os.path.exists(BOARD):
        print(f"SKIP: corpus board not found ({BOARD})")
        return 0

    pcb = parse_kicad_pcb(BOARD)
    u3 = pcb.footprints["U3"]
    tracks, vias, dropped = generate_qfn_fanout(
        u3, pcb, net_filter=["/USB_DP", "/USB_DN"], layer="F.Cu",
        track_width=0.1, clearance=CLEARANCE, grid_step=0.05,
        escape_method="underpad", via_size=VIA_SIZE, via_drill=0.25)

    fails = []
    if dropped:
        fails.append(f"dropped (should escape): {dropped}")
    if len(vias) != 2:
        fails.append(f"expected 2 escape vias, got {len(vias)}")
    # every via is a through-hole on the net, with a stub feeding it
    net_ids = {v["net_id"] for v in vias}
    for v in vias:
        if v["layers"] != ["F.Cu", "B.Cu"]:
            fails.append(f"via not through-hole: {v['layers']}")
    if len(net_ids) != 2:
        fails.append(f"expected both pair halves to escape, got nets {net_ids}")
    if not any(t["net_id"] in net_ids for t in tracks):
        fails.append("no stub feeding the escape vias")
    # the two different-net vias must clear (centre-to-centre >= via + clearance)
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            if vias[i]["net_id"] == vias[j]["net_id"]:
                continue
            d = math.hypot(vias[i]["x"] - vias[j]["x"], vias[i]["y"] - vias[j]["y"])
            if d < VIA_SIZE + CLEARANCE - 1e-6:
                fails.append(f"vias too close: {d:.3f} < {VIA_SIZE + CLEARANCE}")

    fails += _d10_self_blindness()

    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    print(f"PASS: pair escaped as {len(vias)} staggered through-vias, "
          f"min different-net spacing OK")
    return 0


# --- D10: the candidate test must see the run's OWN emitted copper ----------
#
# `via_clears` tested a candidate against the board it was handed -- a snapshot
# taken before anything was placed -- and against the via CENTRES emitted so
# far. It never saw the STUBS the same run emitted, so it approved vias sitting
# on copper it had just laid, and those escapes came back DRC CONTACTS.
#
# Measured: U2 (QFN56) reported 39 of 46 escapes under `--escape-method underpad
# --allow-via-in-pad` and the gate rejected every one as a contact -- while a
# hostile verifier established the geometry was fine (1.4mm moat admitting a
# 0.7mm via at all 56 pads, pad_via == 0, a real 0.700mm via placeable DRC-clean
# in U2.43, true capacity 11 of 14 lanes per side).

KN = dict(via_size=0.7, via_drill=0.4, clearance=0.2, track_width=0.15,
          hole_to_hole=0.2)


def _d10_self_blindness():
    from qfn_fanout import run_output_conflict as conflict
    bad = []

    def check(name, cond):
        print(("PASS: " if cond else "FAIL: ") + name)
        if not cond:
            bad.append(name)

    # Net 1: pad at (0,0), via at (0,2) -- so a 2mm stub runs up x=0.
    stub = [(0.0, 2.0, 1, 0.0, 0.0)]

    # A net-2 via at (0,1) sits ON that stub, yet is 1.0mm from the via centre
    # -- comfortably past the 0.9mm different-net via floor (0.7+0.2). So the
    # via-to-via test PASSES it, and ONLY the stub test can reject it. This is
    # exactly the shape that shipped contacts.
    check('a via sitting on this run\'s own stub is rejected',
          conflict(0.0, 1.0, 2, stub, **KN))
    check('...and it clears every via CENTRE, so nothing else would catch it',
          math.hypot(0.0 - 0.0, 1.0 - 2.0) >= KN['via_size'] + KN['clearance'])

    # Same net: its own stub is not an obstacle.
    check('a SAME-net via on the same stub is allowed',
          not conflict(0.0, 1.0, 1, stub, **KN))

    # Clear of everything.
    check('a via clear of both the stub and the via is allowed',
          not conflict(3.0, 1.0, 2, stub, **KN))

    # The candidate's OWN stub must be tested too -- here the via lands clear
    # but its stub from (0.6,1.0) sweeps across the placed via at (0,2)... use
    # a pad whose stub passes the foreign via.
    check('a candidate whose own STUB crosses a placed via is rejected',
          conflict(-2.0, 2.0, 2, stub, px=2.0, py=2.0, **KN))

    # Stub-vs-stub, ISOLATED. A parallel-stubs case would be tautological: two
    # stubs close enough to graze also put their vias inside the 0.9mm
    # different-net via floor, so the via-to-via test alone would reject it and
    # the assertion would pass with the stub logic deleted. Cross them instead,
    # with a long placed stub, so every other pair is far above its floor:
    #   cand via <-> placed via  2.50mm (floor 0.90)
    #   cand via <-> placed stub 2.00mm (floor 0.625)
    #   placed via <-> cand stub 1.50mm (floor 0.625)
    # Only the stub-vs-stub distance (0) can fire.
    long_stub = [(0.0, 3.0, 1, 0.0, 0.0)]
    check('a candidate whose STUB crosses an emitted stub is rejected',
          conflict(2.0, 1.5, 2, long_stub, px=-2.0, py=1.5, **KN))
    check('...and the same crossing on its OWN net is allowed',
          not conflict(2.0, 1.5, 1, long_stub, px=-2.0, py=1.5, **KN))

    # A via-in-pad entry has a zero-length stub and must not be read as one.
    inpad = [(5.0, 5.0, 1, 5.0, 5.0)]
    check('a zero-length (via-in-pad) stub is not treated as copper',
          not conflict(5.0, 6.0, 2, inpad, **KN))
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
