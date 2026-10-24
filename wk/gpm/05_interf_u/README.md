# gpm board 05: interf_u

**Task:** `/plan-pcb-placement full` on `wk/gpm/05_interf_u/interf_u.kicad_pcb` with `intent.json`. Every part starts in the
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
| BUS1 | mechanical.fixed | BUS_PC | fa10-decl-v1: locked in the human board |
| P1 | mechanical.fixed | DSUB-25_Female_Horizontal_P2.77x2.84mm_EdgePinOffset9.90mm_Housed_MountingHolesOffset11.32mm | fa10-decl-v1: locked in the human board |

Notes:
- BUS1 (ISA edge fingers) and P1 (DSUB-25) were locked in the source; their poses are declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (0 of 24 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `172ff8d091fc65c331e1d1ac34b96abf953633859f65d4e61bd5219d4681b800` |
| `interf_u.design-brief.json` | `d88a16454e4e1636c7a0b4248a5f7430689d9c5bd4ae7e4442d8246af8b9a4a5` |
| `interf_u.kicad_pcb` | `a3025ad15a8042aa0dbd6e69fd8ba5636e2b52f4d43d511bd300873c3f489387` |
| `interf_u.kicad_pro` | `00f226459d899968de188eb29f65c3b1d4792451d5eac1b5cf0c1a5b84951da0` |
| `mechanical.json` | `f7b32b1ff00c47d54a037cc55a4954f7bdc3c6eeb1621920fe7d5952e5f5fa8d` |

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
