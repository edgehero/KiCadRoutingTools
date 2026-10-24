# gpm board 03: complex_hierarchy

**Task:** `/plan-pcb-placement full` on `wk/gpm/03_complex_hierarchy/complex_hierarchy.kicad_pcb` with `intent.json`. Every part starts in the
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
| `intent.json` | `d471731c5cc27ae426c8fc455ce138b9cbf01f5c65c6470ea6cec95a7f57a026` |
| `mechanical.json` | `601b142cc5b1cebc319a3876a66ec0a9e396f8d6933de16ad25dc8cbef1dc710` |

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
