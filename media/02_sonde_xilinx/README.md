# gp14 board 02: sonde_xilinx

**Task:** `/plan-pcb-placement full` on `wk/gp14/02_sonde_xilinx/sonde_xilinx.kicad_pcb` with `intent.json`. Every part starts in the
pile south of the board outline and there is no routing. Place and route the board until it is DONE or a stop rule
fires.

**DONE** (the skill's own definition): `board_score` blocking 0 (unrouted 0, broken 0) and `check_complete` DONE.
After DONE, optimise vias, then copper, then segments, under the skill's stop rules.

## What you are given (rule fa10-decl-v1)

Read off the source board before it was piled, by one rule: parts the source LOCKED and `MountingHole` footprints
get a declared pose in `mechanical.json` (the part still starts in the pile -- the pose is a target); edge
connectors get an EDGE only (`along_edge` unknown) in the design brief, and only when the source seats them within
0.5 mm of that edge. Anything marked JUDGMENT was decided by the campaign organiser and is listed in the notes.
`intent.json` also carries a decap budget derived from the source (which caps belong to which IC, and how far).

| ref | channel | footprint | why |
|---|---|---|---|
| J1 | brief.edge=west | DSUB-25_Male_EdgeMount_P2.77mm | edge_receptacle, seat -13.48 mm from the edge |
| J2 | brief.edge=east | DSUB-9_Male_EdgeMount_P2.77mm | edge_receptacle, seat -13.60 mm from the edge |

Notes:
- J1 (DSUB-25) and J2 (DSUB-9) are edge-mount; J2 sits on the bottom side.

Parts keep the side (F.Cu / B.Cu) they had in the source (1 of 25 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `5305b9bff3c280838327e8bd0f33b7e6b3fe7d75da3fc0d9fc47e89cf3049d4d` |
| `sonde_xilinx.design-brief.json` | `0e4c5f1794cc103d5d067eba2d67696c464c3c213547802e851b7246d6a2d9af` |
| `sonde_xilinx.kicad_pcb` | `b425129da7eca83cc448d8a1ceeb68d9c9ffef01fd9bad3c8b7bb8ef0fcaa9d6` |
| `sonde_xilinx.kicad_pro` | `10881e940a11ef7d06d451f9ca979feb9ee4131da44b5b34137c5021a8c2e5e5` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
