# gpm board 10: glasgow_revC

**Task:** `/plan-pcb-placement full` on `wk/gpm/10_glasgow_revC/glasgow_revC.kicad_pcb` with `intent.json`. Every part starts in the
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
| C1 | mechanical.fixed | C_0603_1608Metric | fa10-decl-v1: locked in the human board |
| C15 | mechanical.fixed | C_0402_1005Metric | fa10-decl-v1: locked in the human board |
| C17 | mechanical.fixed | C_0402_1005Metric | fa10-decl-v1: locked in the human board |
| FID1 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID2 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID3 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID4 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID5 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID6 | mechanical.fixed | Fiducial_0.75mm_Mask1.5mm | fa10-decl-v1: locked in the human board |
| FID8 | mechanical.fixed | Fiducial_0.5mm_Dia_1mm_Outer | fa10-decl-v1: locked in the human board |
| J1 | mechanical.fixed | USB_C_Receptacle_HRO_TYPE-C-31-M-12 | fa10-decl-v1: locked in the human board |
| J2 | mechanical.fixed | IDC-Header_2x10_P2.54mm_Vertical | fa10-decl-v1: locked in the human board |
| J3 | mechanical.fixed | IDC-Header_2x10_P2.54mm_Vertical | fa10-decl-v1: locked in the human board |
| J4 | mechanical.fixed | Molex_KK-254_1x02_P2.54mm_Horizontal | fa10-decl-v1: locked in the human board |
| J5 | mechanical.fixed | PinHeader_2x22_P1.27mm_Vertical__SMD | fa10-decl-v1: locked in the human board |
| MK1 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK2 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK3 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK4 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| SW1 | not claimed | SW_Tactile_SPST_Angled_TC-1109DE | edge_actuator: nearest edge south is 0.52 mm away (> 0.5) |
| U2 | mechanical.fixed | TSSOP-8_4.4x3mm_P0.65mm | fa10-decl-v1: locked in the human board |
| U3 | mechanical.fixed | TSSOP-8_4.4x3mm_P0.65mm | fa10-decl-v1: locked in the human board |

Notes:
- Derived by the same rule as every other board, from the human board (GlasgowEmbedded/glasgow at d884af4b): its 17 locked parts and MK1-MK4 have declared poses.
- JUDGMENT: MK1-MK4 are 3.5 mm mounting holes, each 4.0 mm in from a board corner (stated for run 34).

Parts keep the side (F.Cu / B.Cu) they had in the source (92 of 264 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `glasgow_revC.design-brief.json` | `3c16dd0d70e74775ec9c3dfc4c61597c59b02dcccdcd26006c7c31090cb1e7d6` |
| `glasgow_revC.kicad_pcb` | `22d15bf23328d1e0b47281e9ac35623bee1171f757ccbaa5f7a91984e712b81d` |
| `glasgow_revC.kicad_pro` | `fb9cbd818b42c662317b5d62b7cf4cd22605d172626e0fc082faa803bd335871` |
| `intent.json` | `95aceee7684bc1e4e71f3fcf4088bf49db1c640c55e6917a043e51db6994b6bd` |
| `mechanical.json` | `89c8e7fc55f36f0b394e0ebc931f033b220a56010d03d78411932ade42f52e22` |

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
