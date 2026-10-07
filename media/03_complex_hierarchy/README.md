# fa10 board 03: complex_hierarchy

**Task:** `/pcb-free-agent full` on `wk/fa10/03_complex_hierarchy/complex_hierarchy.kicad_pcb` with `intent.json`. Every part starts in the
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
| Q304 | mechanical.fixed | TO-92_HandSolder | fa10-decl-v1: locked in the human board |

Notes:
- 165 teardrop zones were removed with the routing (KiCad generates them from the tracks).
- Three repeated sheets: the circuit repeats, so does nothing in the intent.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `complex_hierarchy.design-brief.json` | `8bec22fb047b2b84e8b5e4a5c69edb452a323899c2a9e37d65443f695892817c` |
| `complex_hierarchy.kicad_pcb` | `706e9d2b705fb10568467c1f65d39c8ee049ef27f98a6ff3f9c2799793ebd924` |
| `complex_hierarchy.kicad_pro` | `5aa341695e4b294273cacaa7ff6788c6b260563112dccd0d83e5349b000badee` |
| `intent.json` | `58cc68ca336e4f1c613d6ecdcc7cab4636bfdb94a4833640fa91339ba4156047` |
| `mechanical.json` | `20f428ba4f3e0108ed30f9c598b3295d64c0548509f20da83649c5b85e3ba9f0` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
