# gpm board 18: uecg

**Task:** `/plan-pcb-placement full` on `wk/gpm/18_uecg/uecg.kicad_pcb` with `intent.json`. Every part starts in the
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
| AE1 | not claimed | U.FL_Hirose_U.FL-R-SMT-1_Vertical | edge_receptacle: nearest edge north is 5.52 mm away (> 0.5) |
| E+1 | mechanical.fixed | PinHeader_1x01_P2.54mm_Vertical | fa10-decl-v1: locked in the human board |
| E-1 | mechanical.fixed | PinHeader_1x01_P2.54mm_Vertical | fa10-decl-v1: locked in the human board |
| J2 | brief.edge=north | conn_usb_B_micro_smd_our | edge_receptacle, seat -0.10 mm from the edge |
| SW1 | not claimed | BTN_HY_1185 | edge_actuator: nearest edge north is 1.08 mm away (> 0.5) |
| SW2 | brief.edge=north | SW_SPDT_PCM12 | edge_actuator, seat -1.20 mm from the edge |

Notes:
- The source was a KiCad 6 file; it was opened and saved once by KiCad 10.0.7 (pcbnew) before staging, which is what opening it in KiCad 10 does.
- E+1 and E-1 (the electrode pins) were locked in the source; their poses are declared.

Parts keep the side (F.Cu / B.Cu) they had in the source (1 of 75 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `intent.json` | `b42188a066b79ac26d3521a8a0ed57065a6c2f6f3e8dd96f313e1ed1d7028547` |
| `mechanical.json` | `59f2542e37a5906f4b717e4461873a34d7a42cba5887e5fab96067ffd8d3b3df` |
| `uecg.design-brief.json` | `1fec5c03781f922a34abe8a2309b2fc958b326fec16903d29d467168f5629157` |
| `uecg.kicad_pcb` | `43972f64e4eb89dfae13dc499d8ad36635fab8278452f17e862aa9c88e65a6ed` |
| `uecg.kicad_pro` | `8fac24d5e0ecfec9852a6b27d98766bbb295e6a2588300d7f310a47438d741b1` |

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
