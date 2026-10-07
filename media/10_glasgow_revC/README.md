# fa10 board 10: glasgow_revC

**Task:** `/pcb-free-agent full` on `wk/fa10/10_glasgow_revC/glasgow_revC.kicad_pcb` with `intent.json`. Every part starts in the
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
| MK1 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK2 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK3 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |
| MK4 | mechanical.fixed | MountingHole_3.5mm_Pad_Via_CrtYd | fa10-decl-v1 JUDGMENT: run 34's PROMPT.md: 3.5 mm mounting holes 4.0 mm in from each corner |

Notes:
- Run 34's starting inputs: its pile (all 264 parts off the board, locks removed), its design brief and its intent, NOT re-derived by rule fa10-decl-v1. They carry more than the rule gives the other boards: the brief has mount mode, cable entry and role per connector; the intent has edges for FID1-6 and SW1, one block zone and an oob budget, all read off the human board for run 34.
- The pile's outline is the corpus copy's (square corners); the human reference has 4 mm rounded corners.
- MK1-MK4 are declared in mechanical.json, which run 34 stated in its prompt: 3.5 mm mounting holes, each 4.0 mm in from a board corner.
- Run 34 reached blocking 15 with 1370 vias in 7h56m; this run is the comparison.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `glasgow_revC.design-brief.json` | `c6e5c66d30af6811e3820fc3dae18e4f0d81cc639691dd86ddceeee38515f4c4` |
| `glasgow_revC.kicad_pcb` | `aa4281222c44ea711540aa82d407a6ce26acc9cfb5caac14c09cdf2ad2acf20e` |
| `glasgow_revC.kicad_pro` | `840c1a01f55d230f17d4bf57af1d9c356af1322df2b9f92cbf3c75dcaea7c6aa` |
| `intent.json` | `6cd87360ff52217330830751cafd23baf109abfe96906fd78d16efbf5cbc5dc5` |
| `mechanical.json` | `383ad042c5d2ae611c7df630932e06375a5efd1dcff468fbd91da7bf392e0332` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
