# fa10 board 07: One-Air-Max

**Task:** `/pcb-free-agent full` on `wk/fa10/07_One-Air-Max/One-Air-Max.kicad_pcb` with `intent.json`. Every part starts in the
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
| BAT1 | mechanical.fixed | BAT-SMD_BH-18650-B5BA016 | fa10-decl-v1: locked in the human board |
| I2C1 | mechanical.fixed | HDR-TH_4P-P2.54-V-F | fa10-decl-v1: locked in the human board |
| I2C2 | mechanical.fixed | HDR-TH_4P-P2.54-V-F | fa10-decl-v1: locked in the human board |
| LED2 | mechanical.fixed | LED-TH_BD3.8-P2.54-FD_BLUE | fa10-decl-v1: locked in the human board |
| SW1 | mechanical.fixed | KEY-TH_TS-1096-A1B2-D2 | fa10-decl-v1: locked in the human board |
| USB1 | mechanical.fixed | USB-C-SMD_G-SWITCH_GT-USB-7010ASV | fa10-decl-v1: locked in the human board |

Notes:
- Six parts locked in the source (USB1, SW1, BAT1, I2C1, I2C2, LED2) have declared poses.
- 192 parts start on the bottom side, as in the source.
- Zone definitions (pours) are kept; only their fills were removed. Two length-tuning patterns were removed.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `One-Air-Max.design-brief.json` | `9562bd2c5faf21fd6cbb2d0355f136848e3701704dbd370a9bab0ecc366e2657` |
| `One-Air-Max.kicad_pcb` | `df3d48a4a252061fff2dbf60dc33953257fd094bee35422c3c81d9ae1db7b203` |
| `One-Air-Max.kicad_pro` | `636011135f97641895be1098523db254eb00b90db61132da86e58789ca95d6bb` |
| `intent.json` | `4a0eb84a2cf7d58016295cc57766e3f6750f78644d1e9ef50008471919e364a2` |
| `mechanical.json` | `e4a7e7528dd67345e1bccf2422cda7d58377619aff3b208848d7c7665c173e3a` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
