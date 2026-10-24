# gpm board 17: environment_sensor

**Task:** `/plan-pcb-placement full` on `wk/gpm/17_environment_sensor/environment_sensor.kicad_pcb` with `intent.json`. Every part starts in the
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
| J1 | brief.edge=west | USB-C_Receptacle_GCT_USB4105-GF-A | edge_receptacle, seat -1.20 mm from the edge |
| MP1 | mechanical.fixed | MP_Pad5.4mm_Drill2.7mm | fa10-decl-v1: mounting part by drill (every pad drilled >= 2.0 mm, no signal net) |
| MP2 | mechanical.fixed | MP_Pad5.4mm_Drill2.7mm | fa10-decl-v1: mounting part by drill (every pad drilled >= 2.0 mm, no signal net) |
| MP3 | mechanical.fixed | MP_Pad5.4mm_Drill2.7mm | fa10-decl-v1: mounting part by drill (every pad drilled >= 2.0 mm, no signal net) |
| TP1 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |
| TP2 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |
| TP3 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |
| TP4 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |
| TP5 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |
| TP6 | mechanical.fixed | TP_SMD_1.5mm | fa10-decl-v1: locked in the human board |

Notes:
- TP1-TP6 were locked in the source; their poses are declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (2 of 107 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `environment_sensor.design-brief.json` | `c7f5224fe4592fefd610fabd486abbc3fd8e77491158a466d01936e4b3bd4b82` |
| `environment_sensor.kicad_pcb` | `911653c24108c47013457b7f814ee1b55b834b2b77b7def923f638b0d12c9d62` |
| `environment_sensor.kicad_pro` | `11e3a3f6505744df6dd1829b6088cf77ea15b4b648e54cef37914ad42dee6440` |
| `intent.json` | `67f0dff3561b0a791ddfa9fba02fb08631fa0de0d814938bd4e0a3b39e0d7a7f` |
| `mechanical.json` | `fd2430fb716718a8d4f8684eaa219c32343fd8967834b024e9738adabc48a569` |

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
