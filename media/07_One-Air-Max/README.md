# gp14 board 07: One-Air-Max

**Task:** `/plan-pcb-placement full` on `wk/gp14/07_One-Air-Max/One-Air-Max.kicad_pcb` with `intent.json`. Every part starts in the
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
- Board-wide pour definitions are kept; only their fills were removed. Two length-tuning patterns were removed.

Parts keep the side (F.Cu / B.Cu) they had in the source (192 of 204 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `One-Air-Max.design-brief.json` | `596742844fcb123747105e3669cf42b1d9d5d951898359b493a8e6446a977705` |
| `One-Air-Max.kicad_pcb` | `ff27591c8009140cf9d3a7801a799971346da984b92f6a2e9f417a0fb91113a6` |
| `One-Air-Max.kicad_pro` | `081a6662863a98811239b91b7d367889e8b9dddc32fb6b759a9238506bd29717` |
| `intent.json` | `04a851bcb5698f7475dbfdaa8b7aeef08997d545532b00ea82402a616dc851d4` |
| `mechanical.json` | `9e27e8f158f38e45daacf8b012736ed114ca8ea127ad84ad518458a42e7b6c0c` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
