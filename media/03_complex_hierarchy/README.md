# gp14 board 03: complex_hierarchy

**Task:** `/plan-pcb-placement full` on `wk/gp14/03_complex_hierarchy/complex_hierarchy.kicad_pcb` with `intent.json`. Every part starts in the
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

Parts keep the side (F.Cu / B.Cu) they had in the source (0 of 68 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `complex_hierarchy.design-brief.json` | `6cd8a829fecbb7a90e64ecd4e58607880d6706d7e31f6416f15988cb19b83f6e` |
| `complex_hierarchy.kicad_pcb` | `b00ae3a7a8299300ea7c156cd2b481a435f6317998836a126f21da1ef069f1e7` |
| `complex_hierarchy.kicad_pro` | `448ecd389f5d51b9bc6af38c9cc353de99ba502b45ce5a137b5a54882fb9f19f` |
| `intent.json` | `3742c7572d357dd22a1d266a0bc1364bdfbfd93a05dc1f2c05cf2dd642ed7c34` |
| `mechanical.json` | `601b142cc5b1cebc319a3876a66ec0a9e396f8d6933de16ad25dc8cbef1dc710` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
