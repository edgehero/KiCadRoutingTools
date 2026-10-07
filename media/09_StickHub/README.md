# fa10 board 09: StickHub

**Task:** `/pcb-free-agent full` on `wk/fa10/09_StickHub/StickHub.kicad_pcb` with `intent.json`. Every part starts in the
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
| H1 | mechanical.fixed | Plain_Hole_3mm | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J1 | mechanical.fixed | USB_A_PCB_traces_small | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J2 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J3 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J4 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J5 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J6 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J7 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |
| J8 | mechanical.fixed | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal | fa10-decl-v1 JUDGMENT: the earlier StickHub runs (36-39) staged these as locked mechanical parts; declared so run 39 is a fair comparison |

Notes:
- JUDGMENT: J1, H1 and J2-J8 have declared poses -- the set earlier StickHub runs (36-39) staged as locked, so run 39 (blocking 0, 175 vias) is a fair comparison. Run 39 started with those parts in place; here they start in the pile.
- StickHub is CC BY-NC-SA.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `StickHub.design-brief.json` | `8a317528d06363cbc501ebad03e7c3ef437dc338b34b227d18d6ce6cbe5f27ba` |
| `StickHub.kicad_pcb` | `807d357640ef180855b0c1f411ca587bb409339834033cf51a6f27e9ee3b5c09` |
| `StickHub.kicad_pro` | `df0ac7b3f93c2b25290849c31a926e6a2b23714db4c1a1683feb7913bff1590d` |
| `intent.json` | `da0ae23ee0f30ee33f4703082a2a0272b9814f5eebb2556de5baea9783a8a4f2` |
| `mechanical.json` | `477dd8671a7b166502f626be7bbf53846f79b46d3a0b62032abb1f5eab69c016` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
