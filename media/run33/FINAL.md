# run33 FINAL

**Board:** `wk/run33/best.kicad_pcb` (+ `best.kicad_pro`)
**sha256:** `20fb3bfc570ffc14636600553060da078662d3c74f12e5f0b3e88e287ff25443`

| blocking | unrouted | broken | vias | copper_mm | segments | check_complete |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 6 | 321.34 | 180 | DONE |

Other checks: check_connected all nets connected; check_drc 0 violations (with the
unplaced board as `--baseline`, clearance margin 0.1); check_assembly buildable; no pad or
graphic copper off the outline. check_complete does not grade impedance, length or
net_widths, because no targets for them were given.

## Verifier verdicts

1. `verdict_1.txt`: **VERDICT=PASS**. The sha matched, and every check in `VERIFIER.md`
   passed. This was the only verifier call.

## What I tried

I placed the three connectors by hand first. USB1 sits on the west edge at rot 180, with
the mouth outward and 0.6 mm overhang. CON2 runs along the north edge at rot 180, so VBUS
(pin 7) is at its west end. CON1 stands vertically on the east edge with pin 1 north, so
the CON1–CON2 connections nest without crossing. U1 is at rot 0, so D+/D- enter between
its pin rows without crossing. The crystal sits under U1's pins 9/10.

The seeder alone failed its own intent gate on all 5 seeds (crystal and LDO proximity),
so I placed all 18 parts myself. The first `route.py` run already routed everything:
blocking 0 and 28 vias. check_complete still said INCOMPLETE because of 26 redundant
segments that the route's own cleanup leaves behind. `wk/run33/prune_weird.py` removes
them one at a time. It keeps a removal only when `check_weird` findings for that net go
down, none increase, and the net stays fully connected. It also deletes orphaned vias
this way. That gave the first DONE board: 26 vias, 319 mm.

Router settings helped a little. Track width 0.2 mm with `--via-cost 500` gave 20 vias.
`inside_out` or `original` ordering, a finer grid, zero turn cost, 0.18 mm tracks and
equal layer costs were all neutral or worse.

The big gain came from `wk/run33/search.py`, a hill-climb over part poses: move, rotate
or swap one part at a time. Each candidate had to be legal in `place_pose`, have 0
intent ERRORs, and have no render pad conflict, off-board part or body overlap. It was
then routed, pruned and scored on (open nets, vias, copper, segments). Across 4 rounds of
6 parallel workers it went 20 → 13 → 8 → 6 vias, then plateaued at 6 with copper
321–324 mm.

Two gates were added mid-search after they let defects through:
- a render pad-clearance check, after U1 ended up 0.04 mm too close to USB1;
- a body-overlap check, after one round-3 winner stacked C1 on U2 and C4 on Y1, which
  check_assembly graded NOT BUILDABLE.

Neither of those boards was shipped.

The 6 remaining vias are TXD, RXD, DCOM and three on 3V3. With U1 at rot 0, pins 3, 4
and 5 (RXD, TXD and 3V3) sit in a pocket enclosed by the D+/D- tracks and the crystal
loop, so they have to change layer to reach the east connectors. I tested the structural
alternative: U1 at rot 180, so the pocket holds GND and the crystal instead, with the
crystal moved above U1. Two search rounds on it plateaued at 8 vias, worse than 6.
Re-routing the final placement with 8 router settings also found nothing below 6.

The shipped board beats run 30 (39 vias, 375.86 mm, 290 segments) on all three
tie-breakers.
