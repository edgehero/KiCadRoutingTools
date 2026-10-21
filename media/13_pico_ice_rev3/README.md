# gp14 board 13: pico_ice_rev3

**Task:** `/plan-pcb-placement full` on `wk/gp14/13_pico_ice_rev3/pico_ice_rev3.kicad_pcb` with `intent.json`. Every part starts in the
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
| H1 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: locked in the human board |
| H2 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: locked in the human board |
| H3 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: locked in the human board |
| H4 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: locked in the human board |
| J1 | brief.edge=south | USB_C_Receptacle_HRO_TYPE-C-31-M-12 | edge_receptacle, seat 0.03 mm from the edge |
| SW1 | not claimed | PTS820J25KSMTRLFS | edge_actuator: nearest edge west is 4.47 mm away (> 0.5) |
| SW2 | brief.edge=north | PTS820J25KSMTRLFS | edge_actuator, seat -0.11 mm from the edge |

Notes:
- Raspberry Pi Pico form factor; H1-H4 are its mounting holes (declared).

Parts keep the side (F.Cu / B.Cu) they had in the source (30 of 97 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `0d6730f9cc2e2e9676439a02a99eb888ffc176b9d77860609dd89135508c200c` |
| `mechanical.json` | `6ec39b23ee325382a0a8ffb50c93de2001c01bc5da120369fcb8b48141488c0d` |
| `pico_ice_rev3.design-brief.json` | `bfacbb4f75c32009317dd39aef4921105609b628fa33db54351b0d6906589d1c` |
| `pico_ice_rev3.kicad_pcb` | `17dfda8b04b0d9fbcb3a2743dd4d684b3c0fc0110dcf8f329909fb347219823d` |
| `pico_ice_rev3.kicad_pro` | `50a46ec12c370b5a59aee388229ebe326afee25a7f0554489ec6668134571e3f` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
