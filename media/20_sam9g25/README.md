# gpm board 20: sam9g25

**Task:** `/plan-pcb-placement full` on `wk/gpm/20_sam9g25/sam9g25.kicad_pcb` with `intent.json`. Every part starts in the
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
| H1 | mechanical.fixed | MountingHole_2.7mm | fa10-decl-v1: MountingHole footprint |
| H2 | mechanical.fixed | MountingHole_2.7mm | fa10-decl-v1: MountingHole footprint |
| H4 | mechanical.fixed | MountingHole_2.7mm | fa10-decl-v1: MountingHole footprint |
| J2 | brief.edge=west | USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal | edge_receptacle, seat -0.67 mm from the edge |
| SW1 | brief.edge=west | SW_SPST_EVQP7C | edge_actuator, seat -0.65 mm from the edge |
| SW2 | brief.edge=south | SW_SPST_EVQP7C | edge_actuator, seat -0.75 mm from the edge |

Notes:
- The board ships a .kicad_dru with its own rules (some scoped to a part's courtyard); every routing step reads it.
- H1, H2 and H4 are its mounting holes (declared).

Parts keep the side (F.Cu / B.Cu) they had in the source (39 of 111 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `f345dc18e21169d415df421610107b0e351060aaca075280a03315cecc1b4783` |
| `mechanical.json` | `992884716c4f0b8bfece530dd5bd7f4dc06e061e8a334ecc15c120338798b07c` |
| `sam9g25.design-brief.json` | `e86e70f98928ee6af9e28be80351aeca6c667d2e56e85650ef597239bd0826f0` |
| `sam9g25.kicad_dru` | `84aff755eff89f6e2276a973a7bf8cac112bd97a4264ae914d8e485e509c525c` |
| `sam9g25.kicad_pcb` | `08ee03cb7df1631b4c37110eec504634676af1e978ed5d76ba5e424d85829d99` |
| `sam9g25.kicad_pro` | `fb4e1d4b62cf63d5be2d4b35bc25da9bfc3976947ebccbfdb77ea739b549fbc3` |

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
