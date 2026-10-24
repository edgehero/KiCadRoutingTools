# gpm board 16: esp_rust_board

**Task:** `/plan-pcb-placement full` on `wk/gpm/16_esp_rust_board/esp_rust_board.kicad_pcb` with `intent.json`. Every part starts in the
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
| J1 | brief.edge=south | GCT_USB4105-GF-A | edge_receptacle, seat -0.06 mm from the edge |
| SW1 | not claimed | SW_SPST_PTS810 | edge_actuator: nearest edge west is 4.09 mm away (> 0.5) |
| SW2 | not claimed | SW_SPST_PTS810 | edge_actuator: nearest edge east is 3.99 mm away (> 0.5) |
| U4 | mechanical.fixed | Rust_Board | fa10-decl-v1: locked in the human board |

Notes:
- The source was a KiCad 6 file; it was opened and saved once by KiCad 10.0.7 (pcbnew) before staging, which is what opening it in KiCad 10 does.
- U4 (the board's own Rust_Board footprint) was locked in the source; its pose is declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (1 of 55 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `esp_rust_board.design-brief.json` | `3fc9edd4821b3f92b1f0a228a13fa70fc36176a1da4529d27db56d634cdf2cfc` |
| `esp_rust_board.kicad_pcb` | `ba40fbd675ea0430eab76de4666c850022e103ac6a706eb2e8229763d3a07738` |
| `esp_rust_board.kicad_pro` | `4fe58a3fce27a0fd872f186d9f92cb4f01d6ede7fcf4f49f14385bc69be80dfc` |
| `intent.json` | `bd50431fd65224b522d78982f3fefe176987532a3145f15e564830188c9fadab` |
| `mechanical.json` | `633eb655db561c92f19b32f3a4340f17dd94a9b97346785fc68f94a607350c32` |

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
