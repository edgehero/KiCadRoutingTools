# fa10 board 08: CM5_MINIMA_3

**Task:** `/pcb-free-agent full` on `wk/fa10/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb` with `intent.json`. Every part starts in the
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
| J101 | not claimed | USB-C-SMD_TYPEC-305-ACP16H458 | edge_receptacle: nearest edge west is 15.02 mm away (> 0.5) |
| J701 | mechanical.fixed | M.2 M Key socket_2230_2242 | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| M701 | mechanical.fixed | MountingHole_3mm_Pad | fa10-decl-v1: MountingHole footprint |
| M702 | mechanical.fixed | MountingHole_3mm_Pad | fa10-decl-v1: MountingHole footprint |
| Module301 | mechanical.fixed | Raspberry-Pi-5-Compute-Module_GPIO | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| Module302 | mechanical.fixed | Raspberry-Pi-5-Compute-Module_HSS | fa10-decl-v1 JUDGMENT: form factor: the CM5 module connectors share the module's origin and hole pattern, and the M.2 socket J701 sits at card length from the M701/M702 standoffs |
| SW101 | not claimed | SW-SMD_MK-11C04-G013 | edge_actuator: nearest edge east is 5.06 mm away (> 0.5) |
| SW501 | not claimed | SW-SMD_TS-1010A-B | edge_actuator: nearest edge east is 4.08 mm away (> 0.5) |
| USB701 | not claimed | USB-C-SMD_TYPEC-305-ACP16H458 | edge_receptacle: nearest edge west is 15.02 mm away (> 0.5) |

Notes:
- JUDGMENT: the two CM5 module connectors (Module301/302, bottom side, one shared origin) and the M.2 socket J701 (card length from the M701/M702 standoffs) have declared poses.
- The project has 100 ohm and 50 ohm net classes: impedance-controlled pairs.
- 15 length-tuning patterns were removed; the project's DRC exclusions were cleared.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `CM5_MINIMA_3.design-brief.json` | `f1358ef7032a8d56531045b9497bdae6d9f9967a6a2ecee333947ee4c08d6d82` |
| `CM5_MINIMA_3.kicad_pcb` | `e4b0253c3cd55a400b02576c0677a8540b22e93597acea85e0dfc0bd99ee4cc5` |
| `CM5_MINIMA_3.kicad_pro` | `cb230108d949f13a5302d3c5a2a74783015b99ce273b0cf4bf1f52cd9222f586` |
| `intent.json` | `7c70b35eedb6cebb2735ac43fcbaa965cdcc4dcc67e4b266b85785e24d7859b6` |
| `mechanical.json` | `d9d4ecac2a60bdea7b140ad0bf4a6ca86dc972694dc8ad2b3ada11e8e5f8a1bc` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
