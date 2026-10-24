# gpm board 19: icebreaker_v10e

**Task:** `/plan-pcb-placement full` on `wk/gpm/19_icebreaker_v10e/icebreaker_v10e.kicad_pcb` with `intent.json`. Every part starts in the
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
| J20 | mechanical.fixed | Pin_Header_Straight_1x07 | fa10-decl-v1: locked in the human board |
| J21 | mechanical.fixed | Socket_Strip_Angled_2x06 | fa10-decl-v1: locked in the human board |
| J22 | mechanical.fixed | Socket_Strip_Angled_2x06 | fa10-decl-v1: locked in the human board |
| J23 | mechanical.fixed | Socket_Strip_Straight_2x06 | fa10-decl-v1: locked in the human board |
| J24 | mechanical.fixed | Pin_Header_Straight_2x06 | fa10-decl-v1: locked in the human board |
| J25 | mechanical.fixed | Pin_Header_Straight_2x04 | fa10-decl-v1: locked in the human board |
| J26 | mechanical.fixed | Pin_Header_Straight_2x01 | fa10-decl-v1: locked in the human board |
| J27 | mechanical.fixed | Pin_Header_Straight_2x01 | fa10-decl-v1: locked in the human board |
| P1 | mechanical.fixed | Connector_USB_Micro_B_SMD | fa10-decl-v1: locked in the human board |
| REF** | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~10 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~11 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~12 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~13 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~14 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~15 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~16 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~17 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~18 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~19 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~2 | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~20 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~21 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~22 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~23 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~24 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~25 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~26 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~27 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~28 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~29 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~3 | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~30 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~31 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~32 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~33 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~34 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~35 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~36 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~37 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~38 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~39 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~4 | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~40 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~41 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~42 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~43 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~44 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~45 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~46 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~47 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~48 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~49 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~5 | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~50 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~51 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~52 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~53 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~54 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~55 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~56 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~57 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~58 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~6 | mechanical.fixed | MountingHole_3-5mm | fa10-decl-v1: locked in the human board |
| REF**~7 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~8 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| REF**~9 | mechanical.fixed | Drill_0.5mm | fa10-decl-v1: locked in the human board |
| SW1 | brief.edge=west | SW_SPST_3x4x2.5 | edge_actuator, seat 0.05 mm from the edge |
| SW2 | not claimed | SW_SPST_3x4x2.5 | edge_actuator: nearest edge east is 0.55 mm away (> 0.5) |
| SW3 | not claimed | SW_SPST_3x4x2.5 | edge_actuator: nearest edge east is 0.55 mm away (> 0.5) |
| SW4 | not claimed | SW_SPST_3x4x2.5 | edge_actuator: nearest edge east is 0.55 mm away (> 0.5) |

Notes:
- 67 parts were locked in the source (the PMOD headers and sockets, the USB connector, the mounting holes and drill markers); their poses are declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (27 of 191 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `icebreaker_v10e.design-brief.json` | `f5e0852fbdfd5af87c60010bb6002f0306193ceabaf4d5832f1298b3db96bcc9` |
| `icebreaker_v10e.kicad_pcb` | `240b0f425247313592c99f703e3a2c8817c9e1f4b8b2ebde8b34f647935bc146` |
| `icebreaker_v10e.kicad_pro` | `d732c67427c88e475cba72ccaef9a26f07190f734fbb4b57114bbb6825a88f14` |
| `intent.json` | `baab6e39e887d5549229e77b2701a51ac5cd501befad8cd3aaadb6359baa2d38` |
| `mechanical.json` | `c275b5352df05caa74c5c508e00aaf249aaa86bbe942dfbd03816c6740ee86d4` |

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
