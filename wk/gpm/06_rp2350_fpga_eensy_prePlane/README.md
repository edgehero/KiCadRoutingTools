# gpm board 06: rp2350_fpga_eensy_prePlane

**Task:** `/plan-pcb-placement full` on `wk/gpm/06_rp2350_fpga_eensy_prePlane/rp2350_fpga_eensy_prePlane.kicad_pcb` with `intent.json`. Every part starts in the
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
| J1 | brief.edge=north | USB_C_Receptacle_HRO_TYPE-C-31-M-12-Edge_Silkscreen_Removed | edge_receptacle, seat -1.43 mm from the edge |
| SW1 | not claimed | SW_Push_1P1T_NO_Vertical_Wuerth_434133025816 | edge_actuator: nearest edge south is 2.31 mm away (> 0.5) |
| U8 | mechanical.fixed | Teensy40 | fa10-decl-v1: locked in the human board |

Notes:
- JUDGMENT: the source had no .kicad_pro. KiCad wrote one; its floors were then set from the source copper: Default class 0.09 clearance / 0.09 track / 0.45-0.2 via; Board Setup minimums 0.075 track, 0.25-0.15 via, 0.2 edge clearance.
- The source is a pre-plane snapshot: its routing was unfinished, so it is a placement benchmark, not a copper one.
- U8 (the Teensy 4.0 frame) was locked in the source; its pose is declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (4 of 61 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `5ba1b29fc95207174365dff6080590de77b03627fe19d4c2181c6cf4d152a91d` |
| `mechanical.json` | `ecf38b6dadf37b48bf683319c00ad0f56fdd846d9e3847847003d8ad19aa5d4a` |
| `rp2350_fpga_eensy_prePlane.design-brief.json` | `4752b15eb103f24396326d0ccc17e70799449a1dc548f02a9b3b097056e830a1` |
| `rp2350_fpga_eensy_prePlane.kicad_pcb` | `6371a88a6d10f3b80402c4daf70c4bfe5ea99918c91b71463420d65dee889083` |
| `rp2350_fpga_eensy_prePlane.kicad_pro` | `c4bbfd0c1da8080c9e83ca618eb8c5896c94a7032e0e8ed88868b2eb3ad7cd37` |

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
