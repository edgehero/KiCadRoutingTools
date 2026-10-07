# fa10 board 06: rp2350_fpga_eensy_prePlane

**Task:** `/pcb-free-agent full` on `wk/fa10/06_rp2350_fpga_eensy_prePlane/rp2350_fpga_eensy_prePlane.kicad_pcb` with `intent.json`. Every part starts in the
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
| J1 | brief.edge=north | USB_C_Receptacle_HRO_TYPE-C-31-M-12-Edge_Silkscreen_Removed | edge_receptacle, seat -1.43 mm from the edge |
| SW1 | not claimed | SW_Push_1P1T_NO_Vertical_Wuerth_434133025816 | edge_actuator: nearest edge south is 2.31 mm away (> 0.5) |
| U8 | mechanical.fixed | Teensy40 | fa10-decl-v1: locked in the human board |

Notes:
- JUDGMENT: the source had no .kicad_pro. KiCad wrote one; its floors were then set from the source copper: Default class 0.09 clearance / 0.09 track / 0.45-0.2 via; Board Setup minimums 0.075 track, 0.25-0.15 via, 0.2 edge clearance.
- The source is a pre-plane snapshot: its routing was unfinished, so it is a placement benchmark, not a copper one.
- U8 (the Teensy 4.0 frame) was locked in the source; its pose is declared.

Parts keep the side (F.Cu / B.Cu) they had in the source; the pile does not flip anything. Board-wide pours are
kept (which net pours where is design intent); local pours and rule areas smaller than a quarter of the board were
removed with the routing, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `5ed827ee83ab1e1cef597af44bdedf3e48399d5e4979327e1aadc23f392b81cb` |
| `mechanical.json` | `84c82ace3b15c17025d5b16d14811e31f352ad824e5cf23d8c7234175d780878` |
| `rp2350_fpga_eensy_prePlane.design-brief.json` | `9fa93fe03db911f1fd49588ba55b303aad0ea58c63faeedc55890daedab651d7` |
| `rp2350_fpga_eensy_prePlane.kicad_pcb` | `19fe93de2c6b97233b490827ee17c0e29b54f3fecc0a5033cbee8ec38431b184` |
| `rp2350_fpga_eensy_prePlane.kicad_pro` | `09bcf62aa0feff66bcbbcd7f43820d5dea72d60308d54bcc644b8c0526cd2336` |

## Not allowed

- Reading: `wk/fa10/_truth/`, `wk/fa10/_src/`, `wk/fa10/_staging/`, `wk/fa10/_cmp/`, `wk/fa10/_issues/`, `wk/fa10/_control/`, `wk/fa10/_watch/`,
  any other `wk/fa10/NN_*` folder, `C:/Program Files/KiCad/*/share/kicad/demos/`,
  `C:/Users/rob/Documents/kicad_stress_test/`, any other worktree (`../krt-*`), any copy of this design under
  `kicad_files/` or `tests/fixtures/`, and git history of board files.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- `loop_driver.py`, `placement_driver.py`, the primary checkout, any `gh` write, any subagent except the single
  verifier the skill specifies.
