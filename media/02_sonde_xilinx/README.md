# fa10 board 02: sonde_xilinx

**Task:** `/pcb-free-agent full` on `wk/fa10/02_sonde_xilinx/sonde_xilinx.kicad_pcb` with `intent.json`. Every part starts in the
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

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `379594269348c2f95bade6e31dc9d4009822da44a710747dbfc6c8ecd3415254` |
| `sonde_xilinx.design-brief.json` | `2ebbd2a37de1ef41da0f51976e7ea9a762d0503fa0b0b2b574f97c9526921976` |
| `sonde_xilinx.kicad_pcb` | `cb7d030d0305ee191cb923f3bed0301d0eb03fdd07fff0974b30e3d1b300b39a` |
| `sonde_xilinx.kicad_pro` | `b924e0198678ae421e1c00a0ec7240dec28c157b49b187423be336e3a24f3027` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
