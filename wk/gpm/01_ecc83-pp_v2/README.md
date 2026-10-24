# gpm board 01: ecc83-pp_v2

**Task:** `/plan-pcb-placement full` on `wk/gpm/01_ecc83-pp_v2/ecc83-pp_v2.kicad_pcb` with `intent.json`. Every part starts in the
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
| `intent.json` | `eec2684044aa64909458fb9731fa476ae44202c5b219e3812f3b5d8002913c95` |
| `mechanical.json` | `20b1db36700f0c19395c451efc71ef24f363b1893f4e8e8af2eed9bbec2b9c8b` |

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
