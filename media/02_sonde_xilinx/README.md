# gpm board 02: sonde_xilinx

**Task:** `/plan-pcb-placement full` on `wk/gpm/02_sonde_xilinx/sonde_xilinx.kicad_pcb` with `intent.json`. Every part starts in the
pile south of the board outline and there is no routing. Place and route the board until it is DONE or a stop rule
fires.

**DONE** (the skill's own definition): `board_score` blocking 0 (unrouted 0, broken 0) and `check_complete` DONE.
Below DONE, fewer `joins_needed` is better; after DONE, optimise vias, then copper, then segments, under the skill's
stop rules. The board you hand back is the §3.9 `delivered.kicad_pcb`.

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
| `intent.json` | `5692e78892a5de78c904564ed444f55cdd81a80d38d1db8c4c0c856a2c64431b` |
| `sonde_xilinx.design-brief.json` | `0e4c5f1794cc103d5d067eba2d67696c464c3c213547802e851b7246d6a2d9af` |
| `sonde_xilinx.kicad_pcb` | `b425129da7eca83cc448d8a1ceeb68d9c9ffef01fd9bad3c8b7bb8ef0fcaa9d6` |
| `sonde_xilinx.kicad_pro` | `10881e940a11ef7d06d451f9ca979feb9ee4131da44b5b34137c5021a8c2e5e5` |

## Not allowed

- Reading: `wk/gpm/_truth/`, `wk/gpm/_src/`, `wk/gpm/_staging/`, `wk/gpm/_cmp/`, `wk/gpm/_control/`, `wk/gpm/_watch/`,
  `wk/gpm/_phase0/`, `wk/gpm/_oldissues/`, `wk/gpm/_verify/`, `wk/gp14/` (an earlier campaign's files), any other
  `wk/gpm/NN_*` folder, the KiCad demos (`<tmp>`), `~/Downloads`, any other worktree or
  checkout (`../krt-gp14`, `../gp14-assets`, `../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/` or a stress-corpus folder, git history of board files, this board's project on
  the web, and GitHub discussion #118 (it holds an earlier campaign's results for these boards).
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
