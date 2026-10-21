# gp14 board 14: imx6ulz_4l

**Task:** `/plan-pcb-placement full` on `wk/gp14/14_imx6ulz_4l/imx6ulz_4l.kicad_pcb` with `intent.json`. Every part starts in the
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
| H1 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: MountingHole footprint |
| H2 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: MountingHole footprint |
| H3 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: MountingHole footprint |
| H4 | mechanical.fixed | MountingHole_2.7mm_M2.5 | fa10-decl-v1: MountingHole footprint |
| J4 | mechanical.fixed | microSD_HC_Hirose_DM3AT-SF-PEJM5 | fa10-decl-v1: locked in the human board |
| SW1 | not claimed | SW_DIP_SPSTx02_Slide_Copal_CHS-02B_W7.62mm_P1.27mm | edge_actuator: nearest edge south is 0.90 mm away (> 0.5) |
| SW2 | not claimed | SW_DIP_SPSTx04_Slide_Copal_CHS-04B_W7.62mm_P1.27mm | edge_actuator: nearest edge east is 1.27 mm away (> 0.5) |
| SW3 | not claimed | SW_Push_1P1T_NO_CK_KMR2 | edge_actuator: nearest edge west is 2.74 mm away (> 0.5) |
| U1 | mechanical.fixed | BGA289C80P17X17_1400X1400X132 | fa10-decl-v1: locked in the human board |
| U2 | mechanical.fixed | BGA96C80P6X16_800X1400X120 | fa10-decl-v1: locked in the human board |

Notes:
- U1 and U2 (the two BGAs) and J4 were locked in the source; their poses are declared.
- The board ships a .kicad_dru with its own rules; every routing step reads it.

Parts keep the side (F.Cu / B.Cu) they had in the source (97 of 159 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `imx6ulz_4l.design-brief.json` | `a8dc0f0d2c6e43eaaa5d8b65c0785ebca9f49842497d23431a5384285c6ac3df` |
| `imx6ulz_4l.kicad_dru` | `a3f5cf245c60eba7050b18d78d2351563c0b80922da3aab2fcec0ff4ea778533` |
| `imx6ulz_4l.kicad_pcb` | `fee6fc05e8d14aa2aaa77e59c33b6ee9bd52713b1066a9867f3e17a9172af8ce` |
| `imx6ulz_4l.kicad_pro` | `341822ca23742316f0fd0c4bd74788edf8ddae9ea255d5744cc191a44a2f4939` |
| `intent.json` | `4642d550af61dce75f9cc90c1655b8fb6adcbb0f779977f065ef7f21f515aa02` |
| `mechanical.json` | `d9574404ba2cf47c2c3123f3755d128f0d4f3a435724333cd0be4ed5bc2adb4e` |

## Not allowed

- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies.
