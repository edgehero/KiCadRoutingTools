# gpm board 12: steppenprobe

**Task:** `/plan-pcb-placement full` on `wk/gpm/12_steppenprobe/steppenprobe.kicad_pcb` with `intent.json`. Every part starts in the
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
| H1 | mechanical.fixed | MountingHole_3.2mm_M3 | fa10-decl-v1: MountingHole footprint |
| H2 | mechanical.fixed | MountingHole_3.2mm_M3 | fa10-decl-v1: MountingHole footprint |
| H3 | mechanical.fixed | MountingHole_3.2mm_M3 | fa10-decl-v1: MountingHole footprint |
| H4 | mechanical.fixed | MountingHole_3.2mm_M3 | fa10-decl-v1: MountingHole footprint |
| J1 | brief.edge=north | USB_C_Receptacle_GCT_USB4085 | edge_receptacle, seat -0.61 mm from the edge |
| SW1 | brief.edge=west | SW_SPDT_PCM12 | edge_actuator, seat -0.90 mm from the edge |
| SW2 | not claimed | SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG | edge_actuator: nearest edge east is 3.45 mm away (> 0.5) |

Notes:
- none

Parts keep the side (F.Cu / B.Cu) they had in the source (0 of 84 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `a2238d2102796550af651d35290a7d0b3627c5f4a39abccddfd6c9a593bc13e5` |
| `mechanical.json` | `f013f40a387a8b59204c4561250c9c37d672aa631f30691cf3affe1b7739ea29` |
| `steppenprobe.design-brief.json` | `db1bdc2df23b842d7658e181daf90ae1ee50e5653b59dc0317f3a0e6b6e7dc3c` |
| `steppenprobe.kicad_pcb` | `172fbe0b00a248f102cbdf7ae6a3771298061233884caa36bbb2fa35176ed7bf` |
| `steppenprobe.kicad_pro` | `f556c8e309bbb66a6724055e21af4ea9a98b3a4c694190d2726cd690e297def0` |

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
