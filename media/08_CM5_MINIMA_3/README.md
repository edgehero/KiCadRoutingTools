# gp14 board 08: CM5_MINIMA_3

**Task:** `/plan-pcb-placement full` on `wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb` with `intent.json`. Every part starts in the
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
| H101 | mechanical.fixed | MountingHole_2.2mm_M2_DIN965_Pad_TopBottom | fa10-decl-v1: MountingHole footprint |
| H102 | mechanical.fixed | MountingHole_2.7mm_Pad | fa10-decl-v1: MountingHole footprint |
| H103 | mechanical.fixed | MountingHole_2.7mm_Pad | fa10-decl-v1: MountingHole footprint |
| H104 | mechanical.fixed | MountingHole_2.7mm_Pad | fa10-decl-v1: MountingHole footprint |
| H105 | mechanical.fixed | MountingHole_2.7mm_Pad | fa10-decl-v1: MountingHole footprint |
| J101 | not claimed | USB-C-SMD_TYPEC-305-ACP16H458 | edge_receptacle: nearest edge west is 1.05 mm away (> 0.5) |
| J701 | mechanical.fixed | M.2 M Key socket_2230_2242 | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| M701 | mechanical.fixed | MountingHole_3mm_Pad | fa10-decl-v1: MountingHole footprint |
| M702 | mechanical.fixed | MountingHole_3mm_Pad | fa10-decl-v1: MountingHole footprint |
| Module301 | mechanical.fixed | Raspberry-Pi-5-Compute-Module_GPIO | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| Module302 | mechanical.fixed | Raspberry-Pi-5-Compute-Module_HSS | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| SW101 | not claimed | SW-SMD_MK-11C04-G013 | edge_actuator: nearest edge east is 5.06 mm away (> 0.5) |
| SW501 | not claimed | SW-SMD_TS-1010A-B | edge_actuator: nearest edge east is 4.08 mm away (> 0.5) |
| USB701 | not claimed | USB-C-SMD_TYPEC-305-ACP16H458 | edge_receptacle: nearest edge west is 1.05 mm away (> 0.5) |

Notes:
- JUDGMENT: the two CM5 module connectors (Module301/302, bottom side, one shared origin) and the M.2 socket J701 (card length from the M701/M702 standoffs) have declared poses.
- The project has 100 ohm and 50 ohm net classes: impedance-controlled pairs.
- 15 length-tuning patterns were removed; the project's DRC exclusions were cleared.

Parts keep the side (F.Cu / B.Cu) they had in the source (15 of 84 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `CM5_MINIMA_3.design-brief.json` | `99e78927d3db6beb7e96793c44f3a84ffd61898474c2fd9c21e0528fe4439036` |
| `CM5_MINIMA_3.kicad_pcb` | `86acde2b36beb8fa70a25f599701a2c5f7d6d40ddc5d3ce346cc9e620654cbe9` |
| `CM5_MINIMA_3.kicad_pro` | `796e93e4df6ba3b2178760f42a63e65e9b07526e1cc23e22d72f77ba2b9d7843` |
| `intent.json` | `30d9ed84e5b0281e5ea3028b3f6de0c75c4a11f796f6e50e9dc0cf4e15a98a78` |
| `mechanical.json` | `1af778464fbcad208b6f8b4f61acf2d178c626eb46bcf28a5f60d2e1ace0a4fd` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
