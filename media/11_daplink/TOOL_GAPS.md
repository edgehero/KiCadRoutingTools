# TOOL_GAPS -- gp14 board 11 (daplink)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`) after
`export PATH="$HOME/.venvs/krt/bin:$PATH"`; every input it needs is under
`wk/gp14/11_daplink/repro/` (copied with `copy_board.py`, so each board carries its
`.kicad_pro`).

---

## 1. place_simple's edge seat refuses a right-angle header: "no room along the east edge" (silk-only pads counted as pad copper)

**Cost:** about 25 minutes (two exploratory placements, reading `edge_seat.py`, a debug
probe), plus a workaround that takes the part out of the anneal (J2/J3 placed and
locked by hand at the east-edge centre with `place_pose`, so they can no longer slide
along the edge).

**Tool and command:** `py_placer/place_simple.py` (its edge seat,
`py_placer/placement/edge_seat.py`):

```bash
python3 -X utf8 py_placer/place_simple.py wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb /tmp/rep1.kicad_pcb \
    --groups wk/gp14/11_daplink/repro/groups.json --intent wk/gp14/11_daplink/repro/intent_edges.json --seed 1
```

**What it claimed:**
`WARNING: J3 is declared on an edge but has no seat there (no room along the east edge); placed as any other part`
(the same for J2), and it then placed both headers in the board interior. Without an
`overhang_mm` band it does seat them, but flush, with their 6 mm mating pins lying on
the board (exploratory seed `explore/e1`).

**What was true, measured:** the footprint `Connector_Harwin:Harwin_M20-89005xx_1x05_P2.54mm_Horizontal`
draws each pin as a `pad "" smd rect (size 6 0.76) (layers "F.SilkS")`, a silkscreen-only
"pad" with no copper, at local x 0.895..6.895. `edge_seat._pad_box` keeps every pad that
is not `np_thru_hole`, so the seat holds those silk "pads" the 0.55 mm edge clearance
inside the board and cannot push the part out by the declared band. The debug probe
(`helpers/seat_probe.py`, entry 8) prints `padbox (-6.775, -5.58, 6.895, 5.58)`: the real
copper pads end at x -4.275, and the seat coordinate comes out at origin x 142.554,
band 0.38 against the declared min 7.0. The pose the seat said does not exist is legal:
`place_pose set J3 149.18 110 --rot 0` wrote it (`no_worse` true), `check_assembly`
reads buildable, and `check_floorplan` grades the band at 7.006 mm, pass, with 0 errors
(`r1/s3`, `final.kicad_pcb`). `connector_geometry`'s own pad-copper test
(`copper_clear`) answers True at every slide position: only the seat's `_pad_box` is
wrong.

**Reproduce the measurement:**
```bash
python3 -X utf8 wk/gp14/11_daplink/helpers/seat_probe.py wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb \
    wk/gp14/11_daplink/repro/groups.json wk/gp14/11_daplink/repro/intent_edges.json J3
```

**Existing issues:** `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "seat"`
lists #1257 (CLOSED, "The seat search checks only the courtyard, so a part whose pad lies
outside its courtyard is seated ... with pad copper past the outline"), whose pad-box
check is presumably where the silk-only pad entered. No issue covers non-copper pads in
the seat's pad box. Searches "edge seat no room silk pad", "right-angle header overhang
edge seat", "_pad_box", "silkscreen pad": nothing else relevant.

---

## 2. An edge connector's overhang band changes currency when routing writes the board's edge clearance: the same pose fails the grade after routing

**Cost:** about 15 minutes, a rejected full route (arm A, `final_route_old1/`), and a
forced routing choice (`--board-edge-clearance 0.55` on every routing step, so the
grade reads the same margin before and after routing).

**Tool and command:** `py_tools/check_floorplan.py` (`floorplan.rule_edge_connector`,
via `connector_geometry.band_amount`):

```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/11_daplink/repro/placed_s3.kicad_pcb  --intent wk/gp14/11_daplink/repro/intent_edges.json
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/11_daplink/repro/armA_routed.kicad_pcb --intent wk/gp14/11_daplink/repro/intent_edges.json --allow-routed
```

**What it claimed:** on the routed board, 3 ERRORs:
`J2 overhangs the outline by 6.66mm, under the declared minimum 7.00mm (legacy_occupancy@margin=0.2)`,
the same for J3, and `P1 overhangs the outline by 0.70mm, under the declared minimum 1.05mm`.
On the placed board those three parts, at the same poses, grade 7.006 / 7.006 / 1.050, pass,
0 errors.

**What was true:** no part moved between the two boards. The outline has rounded
corners, so no drawn body can be measured ("a non-rectangular outline") and every band
is graded in the courtyard currency at the board's edge margin. The placed board's
project declares `min_copper_edge_clearance` 0, so the margin is the fixed default 0.55
(`"edge_clearance_used": {"source": "fixed default", "value": 0.55}`). The routing chain's
DRC writeback stores 0.2 there (`route_planes`: `rules.min_copper_edge_clearance: 0.0 ->
0.2 mm (fab-edge pin)`), so after routing the margin is 0.2 (`"source": "board
constraint"`) and every courtyard overhang reads 0.35 mm less. A band written so the seat
puts a body exactly at the edge (which the band's currency forces: it must be written in
courtyard + margin) then fails on the routed board. `board_score` counts the 3 as
floorplan blocking, `check_complete` reads INCOMPLETE.

**Existing issues:** searches "overhang band legacy_occupancy margin", "rounded outline
body overhang", "min_copper_edge_clearance writeback": #987 (CLOSED, the seat accepted
within 0.02 mm of its band and the grade flags it) and #1174 are the nearest; neither
covers the margin moving under a declared band.

---

## 3. The routing chain the skills spell lowers the board's authored floors on a board that routes at them

**Cost:** about 10 minutes and one rejected full route (arm A).

**Tool and command:** `route.py` / `route_planes.py` with the skill's chain spelling
(`--clearance-ceiling 0.2`, default `--fab-tier auto --escalation fab`). The arm A
chain is `wk/gp14/11_daplink/final_route_old1/daplink_plan.sh`; its routed board is
`repro/armA_routed.kicad_pcb`:

```bash
python3 -c "import json;r=json.load(open('wk/gp14/11_daplink/repro/armA_routed.kicad_pro'))['board']['design_settings']['rules'];print(r['min_via_diameter'],r['min_through_hole_diameter'],r['min_hole_clearance'])"
```

**What it claimed:** `Design rules [--escalation fab, --fab-tier auto]: 19 feature(s) on
6 net(s) delivered below the requested size (smallest clearance 0.1818 mm, ... smallest
via diameter 0.25 mm); 14 fab-tier escalation(s) to advanced` -- disclosed, and every
checker then reads the board clean, because the writeback lowered the project to match
(Default class 0.2 -> 0.1818, `min_via_diameter` 0.5 -> 0.25,
`min_through_hole_diameter` 0.3 -> 0.15, `min_hole_clearance` 0.25 -> 0.1818).

**What was true:** the same placement routes complete at the authored floors. Arm C
(`final_route/`: no clearance flag, `--fab-tier standard --escalation board
--same-net-pad-clearance 0.1`) ships 0 escalations, every via 0.5/0.3, Default class
0.2, and fewer vias (56 against 61). So the escalations bought nothing here: they came
from plane taps and layer-switch vias the router squeezed beside 0.5 mm-pitch pins
(`plane tap U2.35/U2.47/U2.26`, `layer-switch pad via (net 20/21)`) where a via one step
further out was free. Nothing is false in the disclosure; the gap is that the skills'
recipe (plan-pcb-routing Step 4 "on the routing steps of a chain, spell it
`--clearance-ceiling`", defaults left alone) never tells you to try the authored floors
first, and the floors it spends read clean everywhere afterwards.

**Existing issues:** #1262 (OPEN, "--escalation board commits 0.025 mm clearance
violations ...") and #1287 (CLOSED) concern the escalation policies; none covers the
default chain spending floors a board did not need.

---

## 4. route_planes' DRC writeback ignores `--board-edge-clearance` and lowers `min_hole_clearance` unasked

**Cost:** about 5 minutes (found while chasing entry 2); the shipped project still
declares copper-to-hole 0.2 where the board authored 0.25.

**Tool and command:** `py_router/route_planes.py`:

```bash
python3 -X utf8 py_router/route_planes.py wk/gp14/11_daplink/repro/placed_s3.kicad_pcb /tmp/rp.kicad_pcb \
    --nets GND --plane-layers B.Cu --board-edge-clearance 0.55
```

**What it claimed:** `DRC settings: wrote ... rules.min_hole_clearance: 0.25 -> 0.2 mm`,
`rules.min_copper_edge_clearance: 0.0 -> 0.2 mm (fab-edge pin)`, `rules.min_via_drill: None
-> 0.4 mm`, then `FAB FLOOR RELAXED ... copper-to-hole clearance: 0.25 -> 0.2 mm`.

**What was true:** the call asked for a 0.55 mm edge clearance and passed no clearance
flag at all. The edge value written is 0.2, not 0.55 (`qfn_fanout` and
`place_fanout_clearance` keep 0.2; `route_diff` then writes 0.55, so the project's edge
rule flips 0 -> 0.2 -> 0.55 down the chain). The hole clearance it lowered to 0.2 does
not even license the only sub-0.25 copper on the board: KiCad flags P1's own GND/VBUS
pads at 0.1751 / 0.2099 mm from P1's own NPTH pegs (footprint geometry, present on the
unrouted placement too), 4 of which are below 0.2 as well. `min_via_drill` 0.4 is above
the 0.3 drill the chain routes with (route.py rewrites it to 0.3 later).

**Existing issues:** #1290 (OPEN, "Some passes ignore --board-edge-clearance and
net-class clearance (v0.23.1)") is the nearest; it names passes, not this writeback.
Search "min_hole_clearance relaxed route_planes": nothing.

---

## 5. The emitted overhang band (0) seats a USB-C receptacle 1.055 mm inside the board on a rounded-corner outline

**Cost:** about 10 minutes (reading the band currency), and a hand-written band.

**Tool and command:** `check_floorplan.py --emit-intent` / the given intent's
`edge_connectors[P1]` (no `overhang_mm`), read by `place_simple`'s seat:

```bash
python3 -X utf8 py_tools/check_assembly.py wk/gp14/11_daplink/repro/placed_p1_band0.kicad_pcb --baseline wk/gp14/11_daplink/repro/daplink_pile.kicad_pcb
```
(`repro/placed_p1_band0` is the exploratory seed `explore/e1`, placed with the band unset; it prints `in the band but belonging at the
edge ... P1 1.055mm [edge_receptacle]`.)

**What it claimed:** the skill (§3.4) says the seat puts a receptacle flush with the low
end of its `overhang_mm` band, which the emitter writes as 0, and to raise `min` only where
the datasheet puts the board edge inside the body.

**What was true:** GCT USB4105's own "PCB Edge" line (Dwgs.User, local y +3.675) is the
Fab body front: the mouth belongs flush with the edge, i.e. the skill's default case. But
on this board's rounded outline the band is graded in courtyard currency at the 0.55
margin, so 0 puts the courtyard 0.55 mm inside the edge and the body front 1.055 mm
inside. To seat it flush the band has to be written as 1.05 (`intent_edges.json`), a
number nothing in the skill derives. Combined with entry 2, that number is also wrong
after routing (0.70).

**Existing issues:** search "rounded outline body overhang": #1174 (CLOSED) is about
emitted zones and overhang on the emitting board, not this currency. None found.

---

## 6. route.py ships a KiCad `track_dangling` micro-segment that its cleanup keeps, and the scoped retry for it is a no-op

**Cost:** about 5 minutes; arm B rejected (`final_route_old2/`).

**Tool and command:** `route.py` (arm B chain, `final_route_old2/daplink_plan.sh`), graded by

```bash
python3 -X utf8 py_router/check_weird.py wk/gp14/11_daplink/repro/armB_routed.kicad_pcb
```

**What it claimed:** the route step reported a clean board (`failed 0, open_single [],
multipoint_deficit 0`; `board_score` blocking 0).

**What was true:** `check_weird` finds `kicad-dangling: net +3.3V (F.Cu) segment
(143.650, 106.500)-(143.700, 106.450) w0.300` (a 0.07 mm segment lying on other +3.3V
track), and KiCad's own DRC reports it as `track_dangling` (measured with kicad-cli), so
`check_complete` reads INCOMPLETE (`weird_copper: not clean`). A follow-up
`route.py --nets '+3.3V' GND --rip-existing-nets '+3.3V'` changed nothing: the net is
connected, so it is skipped (`--force-reroute` would be needed). Arm C's different via
rule happened not to produce it.

**Existing issues:** #1217 (CLOSED) taught `check_weird` to report this shape; #162
(OPEN, "Same-net redundant copper ... find the producers, remove delete-only") is the
producer side.

---

## 7. Default routing puts vias in SMD pads (IPC-4761 Type VII) on a plain 2-layer board, and the routing skill never mentions the flag that stops it

**Cost:** about 5 minutes (a third full-route arm).

**Tool and command:** `route.py` defaults (arm B, `final_route_old2/plan_run.log`):
`FAB NOTE (route): 15 via(s) in a pad or paste opening [C4.1, C5.2, C6.1, C6.2, C7.2,
C9.2, D3.1, J2.1, J2.5, R10.1, R4.1, R9.2, U1.3, U2.12, Y1.2] ... 15 already
filled+capped`.

**What it claimed:** nothing false: it discloses and stamps Type VII on each.

**What was true:** several are signal pads (C6.1 /OSCOUT, U2.12 /TGT_RX, C4.1 /IF_RST),
on a cheap 2-layer debug probe where filled-and-capped vias are a real cost adder. With
`--same-net-pad-clearance 0.1` on every routing step the same placement routes complete
with 0 via-in-pad and 56 vias (against 55). plan-pcb-routing names the flag only under
`route_planes.py` options; nothing tells a 2-layer chain to set it.

**Existing issues:** search "via-in-pad 2-layer same-net-pad-clearance": none on point.

---

## 8. Helper `helpers/seat_probe.py` (debug probe for entry 1)

No tool says WHY an edge seat found "no room": `place_simple` prints only the
conclusion. The probe rebuilds `place_simple.build`'s state and prints, for one ref, the
seat's turns, its courtyard and pad box, the seat coordinate and, along the edge, each
conjunct (`band`, `copper_clear`, nearest edge, declared-pose check). Command in entry 1.
Search "seat no room explain": nothing.

## 9. Helper `helpers/judge_chain.sh` (the judging chain over judge.json's seeds)

The skill (§3.6 step 1) has the agent run the board's routing chain on each seed
`r<N>/judge.json` names, identically, then copy out and `quick_score` each; no repo
tool runs a chain over a seed list. The script only sequences repo CLIs with fixed
arguments (pour GND on B.Cu, `qfn_fanout` U2, `place_fanout_clearance`, `route_diff
--quick 2`, `route.py --quick 2`, `copy_board`, `quick_score`). Cost: minutes; it ran each
seed in about 4 s. Usage: `bash wk/gp14/11_daplink/helpers/judge_chain.sh wk/gp14/11_daplink/r1 3`.

---

## 10. manifest_to_plan drops the pour and the fanout from a plan.sh, and counts the loss as "1 command skipped"

**Cost:** about 5 minutes (noticed because the plan JSON had 4 steps for a 7-step chain);
the plan JSON shipped is converted from `final_route/redo_commands.sh` instead.

**Tool and command:** `tests/stress/manifest_to_plan.py` (plan-pcb-routing Step 9's
`<board>_plan.json`), on the plan file the skill tells you to write:

```bash
python3 -X utf8 tests/stress/manifest_to_plan.py wk/gp14/11_daplink/repro/m2p/daplink_plan.sh -o /tmp/m2p_from_plan.json
```

**What it claimed:** `command 8: place_fanout_clearance.py refuses its arguments after
parsing: cannot load intent wk/gp14/11_daplink/intent_edges.json: [Errno 2] No such file`,
then `4 step(s) written ... (1 command(s) skipped ...)`.

**What was true:** the intent path is valid from the worktree root, where the plan's own
first line `cd`s and where the converter was run; the converter resolves it elsewhere (the
same plan converted from a copy in another folder fails the same way). Rejecting that one
command breaks the file-dependency chain, and the pruner then silently drops the two steps
upstream of it as well: the JSON has `route_diff, route, route, route` -- no `route_planes`
and no `fanout` -- while the summary says one command was skipped. The recorded manifest
(absolute paths) converts to all 7 steps: `route_planes, fanout, optimize_caps, route_diff,
route, route, route`.

**Existing issues:** searches "manifest_to_plan dropped steps relative intent",
"manifest_to_plan prune": nothing.
