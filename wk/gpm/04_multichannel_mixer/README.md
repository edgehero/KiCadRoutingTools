# gpm board 04: multichannel_mixer

**Task:** `/plan-pcb-placement full` on `wk/gpm/04_multichannel_mixer/multichannel_mixer.kicad_pcb` with `intent.json`. Every part starts in the
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
- The board keeps 4 groups from the source.
- Board Setup's min_clearance 0.3 / min via 1.5 are above the Default class (0.2 / 0.6).

Parts keep the side (F.Cu / B.Cu) they had in the source (81 of 114 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `e0021a1576d911baf9df37451bd4dc5e23334d4dea7470bf8e4f535a6fdbb8d0` |
| `mechanical.json` | `fc7002089833bfb9b4767d1d18c3fe06f061bede33c4d18ecdfd23244075110a` |
| `multichannel_mixer.design-brief.json` | `fc6ed57531948d67924ae50c4a08bc8f0c980ecebdf638a962baec09326128ef` |
| `multichannel_mixer.kicad_pcb` | `c09cd6a4d7e8ed53b32a02da0abe94b1fa6992e557af9c3442e9859189393c50` |
| `multichannel_mixer.kicad_pro` | `ab71c3abe506d86d1e3c9a99af5531de743caef555270dd6f3fd3141c05e696d` |

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
