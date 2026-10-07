# fa10 board 05: interf_u

**Task:** `/pcb-free-agent full` on `wk/fa10/05_interf_u/interf_u.kicad_pcb` with `intent.json`. Every part starts in the
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
| BUS1 | mechanical.fixed | BUS_PC | fa10-decl-v1: locked in the human board |
| P1 | mechanical.fixed | DSUB-25_Female_Horizontal_P2.77x2.84mm_EdgePinOffset9.90mm_Housed_MountingHolesOffset11.32mm | fa10-decl-v1: locked in the human board |

Notes:
- BUS1 (ISA edge fingers) and P1 (DSUB-25) were locked in the source; their poses are declared.
- The project declares no edge clearance, so tools use the 0.55 mm fixed default.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `98fe3279aff2384d20f348485cbbf80fe31dca16812f86604ad0422149cd58ce` |
| `interf_u.design-brief.json` | `d6be103cf936cf29b7577e04074866ee07a526beb266d47421bec3cdf44d9432` |
| `interf_u.kicad_pcb` | `7255bb081bd7f26a7d502e97b7d63e5a985fb1233100f285cbd54313f9a8abdb` |
| `interf_u.kicad_pro` | `d16074d956eccc7543fc18bc6dffbc16b1978652fa80f4b0608705d80521cd9f` |
| `mechanical.json` | `f9fae96de4880457f10b8a42da25622e77c29149218df06c779d147bc0357cd6` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
