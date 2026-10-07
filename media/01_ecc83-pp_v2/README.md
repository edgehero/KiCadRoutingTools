# fa10 board 01: ecc83-pp_v2

**Task:** `/pcb-free-agent full` on `wk/fa10/01_ecc83-pp_v2/ecc83-pp_v2.kicad_pcb` with `intent.json`. Every part starts in the
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

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `ecc83-pp_v2.design-brief.json` | `477632c32030c5236f5f1e891ac935c1a171d5634d92368cf94467040db392d7` |
| `ecc83-pp_v2.kicad_pcb` | `3b61094e1fe55b4bdd764d55de1b711893c3af5f80e92769f18ec0fcf324b980` |
| `ecc83-pp_v2.kicad_pro` | `25b56d169885c90305e4ed0f5ca7206115d3eccbeeaca798dafe9dd4948155cf` |
| `intent.json` | `8ca0246fb1e728b9d9577762c6ed9af0a913574d90856790f3a2d1ffc334cafb` |
| `mechanical.json` | `0d09510a5e6fb151e1d60b01c84d415957721e8c2c3e6fd399950bd379391232` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
