# gpm board 09: StickHub

**Task:** `/plan-pcb-placement full` on `wk/gpm/09_StickHub/StickHub.kicad_pcb` with `intent.json`. Every part starts in the
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
- JUDGMENT: J1, H1 and J2-J8 have declared poses -- the set earlier StickHub runs (36-39) staged as locked mechanical parts.
- StickHub is CC BY-NC-SA.

Parts keep the side (F.Cu / B.Cu) they had in the source (53 of 90 start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
| `StickHub.design-brief.json` | `bfa6ca5ba134ceaa6f42b98dba5c7e282537545ddb0003740dd5caa941a065cf` |
| `StickHub.kicad_pcb` | `b48aca35f0321c90638f274288c34279df5c51c807576c2a6b133fed4a4443c6` |
| `StickHub.kicad_pro` | `14cfde8a9056a35c4968d6ca389ed015b3d180ee869251359c837313e6839073` |
| `intent.json` | `215f14d9a79a20af8ee10677b36ea821d5b6dc82056b47451cf3f21e18da6edf` |
| `mechanical.json` | `43aef1f890e5299ff7d2df1c287e7a61b43c27c11f2ddabbf6731499c96ed081` |

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
