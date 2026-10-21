# gp14 board 01: ecc83-pp_v2

**Task:** `/plan-pcb-placement full` on `wk/gp14/01_ecc83-pp_v2/ecc83-pp_v2.kicad_pcb` with `intent.json`. Every part starts in the
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
| P5 | mechanical.fixed | MountingHole_3.2mm_M3_DIN965_Pad | fa10-decl-v1: MountingHole footprint |
| P6 | mechanical.fixed | MountingHole_3.2mm_M3_DIN965_Pad | fa10-decl-v1: MountingHole footprint |
| P7 | mechanical.fixed | MountingHole_3.2mm_M3_DIN965_Pad | fa10-decl-v1: MountingHole footprint |
| P8 | mechanical.fixed | MountingHole_3.2mm_M3_DIN965_Pad | fa10-decl-v1: MountingHole footprint |

Notes:
- none

Parts keep the side (F.Cu / B.Cu) they had in the source (0 of 15 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `ecc83-pp_v2.design-brief.json` | `85cdf2e60b835d66eed28c563d9158f5f746c52d7cad5f7175aa7b587b1bf437` |
| `ecc83-pp_v2.kicad_pcb` | `ddf1063105b589401280947b538ec1afa06fb3ff20d8b673d08d4873c66e1ae8` |
| `ecc83-pp_v2.kicad_pro` | `34a89cfc8cc2780cc3acf331f7d8de59fbb78d0445b4af498772118786ee5f8b` |
| `intent.json` | `9938ae6d1c70b7d7e903d01b2742c085232b94c967afa2eafa55960abb4a3c3b` |
| `mechanical.json` | `20b1db36700f0c19395c451efc71ef24f363b1893f4e8e8af2eed9bbec2b9c8b` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
