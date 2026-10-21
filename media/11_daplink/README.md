# gp14 board 11: daplink

**Task:** `/plan-pcb-placement full` on `wk/gp14/11_daplink/daplink.kicad_pcb` with `intent.json`. Every part starts in the
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
| P1 | brief.edge=west | USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal | edge_receptacle, seat 0.48 mm from the edge |
| RST1 | brief.edge=north | SW_Push_SPST_NO_Alps_SKRK | edge_actuator, seat 0.41 mm from the edge |

Notes:
- The source was a KiCad 7 file; it was opened and saved once by KiCad 10.0.7 (pcbnew) before staging, which is what opening it in KiCad 10 does.

Parts keep the side (F.Cu / B.Cu) they had in the source (1 of 35 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `daplink.design-brief.json` | `7d8f52c5543efcf874b7583cc518918b0a75854089a3449153248b3f6e65fd84` |
| `daplink.kicad_pcb` | `297e7c6965eeb0f10c7d03a255789e3c47fe2a2c956810a09e170b9450c11dff` |
| `daplink.kicad_pro` | `dc832abe16d69f17e0d0e8c5e3b47267e9e08bc98ffe31ae1da2bc0b47d17f26` |
| `intent.json` | `cd65976c8446eb56970dbae937d1d6406742658a4afc4a8cc48224a1f7964d40` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
