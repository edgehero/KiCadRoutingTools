# gpm board 07: One-Air-Max

**Task:** `/plan-pcb-placement full` on `wk/gpm/07_One-Air-Max/One-Air-Max.kicad_pcb` with `intent.json`. Every part starts in the
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
| BAT1 | mechanical.fixed | BAT-SMD_BH-18650-B5BA016 | fa10-decl-v1: locked in the human board |
| DC1 | brief.edge=south | DC-IN-SMD_DC-045A-13A | edge_receptacle, seat 0.15 mm from the edge |
| I2C1 | mechanical.fixed | HDR-TH_4P-P2.54-V-F | fa10-decl-v1: locked in the human board |
| I2C2 | mechanical.fixed | HDR-TH_4P-P2.54-V-F | fa10-decl-v1: locked in the human board |
| LED2 | mechanical.fixed | LED-TH_BD3.8-P2.54-FD_BLUE | fa10-decl-v1: locked in the human board |
| PWR_SW1 | not claimed | SW-TH_TK-6580A8-1 | edge_actuator: nearest edge south is 4.04 mm away (> 0.5) |
| SW1 | mechanical.fixed | KEY-TH_TS-1096-A1B2-D2 | fa10-decl-v1: locked in the human board |
| USB1 | mechanical.fixed | USB-C-SMD_G-SWITCH_GT-USB-7010ASV | fa10-decl-v1: locked in the human board |

Notes:
- Six parts locked in the source (USB1, SW1, BAT1, I2C1, I2C2, LED2) have declared poses.
- Board-wide pour definitions are kept; only their fills were removed. Two length-tuning patterns were removed.

Parts keep the side (F.Cu / B.Cu) they had in the source (192 of 204 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `One-Air-Max.design-brief.json` | `720eb0d6b4b21fb6572781743ab161cf8329166fa60036a693037c968bbb3dc0` |
| `One-Air-Max.kicad_pcb` | `ff27591c8009140cf9d3a7801a799971346da984b92f6a2e9f417a0fb91113a6` |
| `One-Air-Max.kicad_pro` | `081a6662863a98811239b91b7d367889e8b9dddc32fb6b759a9238506bd29717` |
| `intent.json` | `deb408be39ae3c6d2567ef7eae717431821469e03d7241c0682c7f8b471f7b6d` |
| `mechanical.json` | `9e27e8f158f38e45daacf8b012736ed114ca8ea127ad84ad518458a42e7b6c0c` |

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
