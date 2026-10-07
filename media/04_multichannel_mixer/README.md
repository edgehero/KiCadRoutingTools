# fa10 board 04: multichannel_mixer

**Task:** `/pcb-free-agent full` on `wk/fa10/04_multichannel_mixer/multichannel_mixer.kicad_pcb` with `intent.json`. Every part starts in the
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
| J1 | mechanical.fixed | Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| J5 | mechanical.fixed | CLIFF_FC68148(DC-10A) | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| J6 | mechanical.fixed | Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| J7 | mechanical.fixed | Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| J8 | mechanical.fixed | Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| J9 | mechanical.fixed | Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV1 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV10 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV11 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV12 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV13 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV14 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV15 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV16 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV2 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV3 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV4 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV5 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV6 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV7 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV8 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |
| RV9 | mechanical.fixed | Potentiometer_Alps_RK09K_Single_Vertical | fa10-decl-v1 JUDGMENT: front-panel parts: the panel drilling fixes every pot shaft and jack |

Notes:
- JUDGMENT: the 16 pots and 6 jacks are front-panel parts; their poses are declared.
- 81 parts start on the bottom side, as in the source.
- The board keeps 4 enabled rule areas named `auto-placement-area-/CHn/` and 4 groups from the source.
- Board Setup's min_clearance 0.3 / min via 1.5 are above the Default class (0.2 / 0.6).

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `b1a80b98827210ab7626f48dbb6fe2f0ced04be10a1bbe7ccb6ef1dd1e09904b` |
| `mechanical.json` | `da7cc144ed557c47c7c4862ba42cab91c7a7b5db6bcd5d678995571df571f5d7` |
| `multichannel_mixer.design-brief.json` | `228592418b5043e80bc244741641bdb2e0fdf228f9b4f5b978a4b3b60a681829` |
| `multichannel_mixer.kicad_pcb` | `80a419e98df2f85c17730747f3f767ef9f4e78dcfdf132100d6b44f0116642cf` |
| `multichannel_mixer.kicad_pro` | `3dbbfdcaeb1168536d2c5fc941b195c7c34180e57c8aaba6b3ad46c5d5c98fb8` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
