# REPORT: gp14 board 03, complex_hierarchy (`/plan-pcb-placement full`)

**DONE.** `final.kicad_pcb`, sha256 `0c4d3fa4e9e52ff6121dced6ea11131858648c7390e69f60a74331aab8b3ed7a`, with `final.kicad_pro`, `FINAL.sha256` and `DONE`. Verifier call 1: **PASS**.

## 1. Result

| DONE condition (full mode) | Measured | Tool |
|---|---|---|
| board_score blocking | **0** | `py_tools/board_score.py`, every spec flag |
| unrouted / broken | **0 / 0** | board_score; `check_connected` says ALL NETS FULLY CONNECTED, and the KiCad refill cross-check agrees |
| check_complete | **DONE**; impedance and length are UNEXAMINED because nothing declares them | `check_complete.py`, every spec flag |
| check_assembly | buildable (blocking 0); no pad, graphic or keep-out copper off the outline | `check_assembly --intent --baseline` |
| check_floorplan --intent | 0 errors, 0 violations; exits 4 because the given intent leaves 3 rules undeclared (§4) | `check_floorplan --allow-routed` |
| check_drc | 0 violations, with and without `--clearance-margin 0.1` | `check_drc.py --baseline` |
| weird copper / orphan stubs / loops | clean / none / 0 | `check_weird`, `check_orphan_stubs`, `check_cycles` |
| KiCad 10.0.7 DRC (`kicad-cli pcb drc --refill-zones`) | 0 copper violations, 0 unconnected; 8 silkscreen errors; 68 lib_footprint warnings (libraries not installed) | run by me and by the verifier |
| Mechanical fact: Q304 at (129.794, 96.52), rot 0 | exact | verifier, measured from the board |
| Independent grade | `{"done": true, "blocking": 0, "vias": 0, "copper_mm": 740.61, "segments": 158, "check_complete": "DONE", "check_complete_authored": "DONE"}` | `scripts/grade.py`, output in `grade/grade_output.txt` |

`blocking_by`: unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, net_widths 0, drc_via_in_paste 0. Impedance and length are ungraded because the board declares neither.

**Quality: 0 vias, 740.61 mm of copper, 158 segments.** That is 631.9 mm on F.Cu and 108.7 mm on B.Cu, with 134 segments at 0.4 mm and 24 at 0.6 mm. The first DONE board had 9 vias, 857.28 mm and 213 segments.

Spec flags used everywhere:
- `--min-track-width 0.2032 --min-via-diameter 0.889 --min-via-drill 0.508`: the board's own Board Constraints.
- `--net-min-widths net_min_widths.json`: my own reading of the board's `power` net class, which sets 0.6 mm tracks on -VAA, /12Vext, GND, HT and VCC.
  - KiCad does not enforce a class width as a DRC minimum, but it is the only width the design states, so I graded it rather than leave net widths unexamined.
  - Every routed segment of those nets is 0.6 mm. GND has no tracks; the pour serves it.

## 2. The board, the groups and each judgement call

The board has 68 through-hole parts, 53 nets and 2 layers, measures 100.7 x 80.0 mm, and every part started in the pile. It has one board-wide GND zone on B.Cu, which I kept. The circuit is:
- two identical high-voltage piezo amplifier channels (sheets 2xx and 3xx);
- a 12 V supply;
- an HT (high-voltage) entry.

I identified the parts from their values and nets:
- **U101**, a 78L05, makes VCC from +12V.
- **U102**, an ICL7660, inverts VCC to -VAA, with C105 as its flying cap on CAP+/CAP-.
- **U201 and U301** are LM358 op-amps.
- **The output transistors** are MPSA92 (Q201, Q203, Q301, Q303) and MPSA42 (Q202, Q204, Q302, Q304).
- **D101**, a 1N4007, is reverse-polarity protection on the 12 V input.
- **RV201 and RV301** are Bourns 3266W trimmers.
- **P101, P102, P201, P202, P301 and P302** are Altech AK300 terminal blocks.

No datasheet lookups were needed, so no datasheet folder was created.

`groups.json` passed `check_groups` with 0 errors and 0 warnings:

| Group | Refs | Anchor | Hints | Why |
|---|---|---|---|---|
| power | P102 D101 C104 U101 C102 U102 C105 C103 | U102 | near ch2_in, ch3_in | The 12 V entry, the reverse diode and the +12V bulk cap; the 78L05 and its VCC bulk cap; the ICL7660 with its flying cap and -VAA reservoir. +12V and -VAA feed both LM358s. |
| ht_in | P101 C101 | P101 | near ch2_out, ch3_out | The HT terminal and its 47uF/63V bulk cap. HT feeds only the output stages. |
| ch2_in | P201 R201 C202 R202 C201 R203 C203 U201 RV201 R213 | U201 | near ch2_out, power | The input terminal, the R/C filter into U201B, and U201A with its feedback trimmer RV201 and R213. |
| ch2_out | R212 Q201-Q204 D201-D204 R204-R211 C204 P202 | Q202 | near ch2_in, ht_in | The discrete HV output stage: bias diode string, emitter resistors to the PIEZO_OUT terminal, feedback divider R209/R210. |
| ch3_in / ch3_out | the same circuit with 3xx refs | U301 / Q304 | as for channel 2 | Q304 is the one declared mechanical pose, so it anchors ch3_out. |

Judgement calls:
- **Splitting each channel** into its op-amp stage and its HV output stage gave 6 groups of 2 to 19 parts, inside the skill's 5 to 8. R212 (U201A output to Q204's emitter) went with the output stage; RV201 and R213 went with the op-amp.
- **CAP+/CAP- is not a differential pair**, although `list_nets --diff-pairs` lists it. It is the ICL7660's flying capacitor, so it was routed single-ended with everything else and there is no `route_diff` step.
- **No connector edges.** The design brief declares no interfaces, and `check_floorplan` classifies none of the terminal blocks as an edge receptacle. I did not invent edges or write a second intent. The terminal blocks sit inboard, which is buildable because the wires enter at 45° from above.
- **Q304 was not locked.** The intent's `fixed_poses[]` seats it, as the skill says.
- **EMC rows:** none were given, because the user was unavailable. `board_context` names no switching converter, crystal, oscillator or ESD array. I added no proximity or keep-away rows.
- **The given intent was used unchanged**: decap budget 72.9 mm, Q304's fixed pose. There is no `intent_<name>.json`.

## 3. Placement rounds and the work after DONE

**Round 1** (`r1/`) placed 12 seeds in 18 s. It judged seeds 11, 6, 9, 10, 4 and 5, the six with the lowest `final.cost`. Every fast route (`route.py --quick 2`, at the class widths) had **blocking 0**:

| Seed | Start | Fast-route vias | Fast-route copper_mm | Segments |
|---|---|---|---|---|
| 5 | scattered | **4** | 818.17 | 603 |
| 9 | clustered | 6 | 814.09 | 552 |
| 11 | clustered | 7 | 721.95 | 522 |
| 6 | clustered | 9 | 785.64 | 574 |
| 10 | clustered | 10 | 772.01 | 538 |
| 4 | scattered | 10 | 833.14 | 657 |

Round 1 was clean, so placement stopped there (skill §3.6) and the judge kept **seed 5**. The placement loop had no review round.

**After DONE: lowering vias, then copper, then segments.** Every candidate was fully routed and graded with board_score and the spec flags. All of them are in `opt/` and in the ledger.

1. **Chain parameters on seed 5** (first DONE: 9 vias, 857.28 mm).
   - `--layer-costs 1.0 1.5` gave 13 vias, `1.0 1.0` gave 14, and the 2-layer through-hole bus flags gave 9.
   - `--via-cost` 150 gave 7 vias, 300 gave 3, and **600 gave 0 vias** (865.76 mm). 1000 and 2000 were identical to 600.
   - With via cost 600, `--layer-costs 1.0 1.0` gave 834.61 mm (kept), `1.0 1.5` gave 834.73, and `1.0 2.0` gave 865.64.
2. **Re-judging the six seeds by full route** under that chain. Seed 6 was best (0 vias, 809.75 mm) and was kept:

   | Seed | Vias | Copper (mm) |
   |---|---|---|
   | 6 | 0 | 809.75 |
   | 10 | 0 | 851.2 |
   | 4 | 0 | 863.48 |
   | 5 | 0 | 834.61 |
   | 9 | 1 | — |
   | 11 | 2 | 744.5 |

   The fast-route ranking did not hold up here: seed 5's 4 fast-route vias became 9 on its first full route.
3. **route_review on seed 6** said R207 was turned against its wiring and would save 9 mm.
   - I applied it as `place_pose set R207 152.2729 107.6242 --rot 270`, which swaps its pads in place. TOOL_GAPS entry 2 explains why `rotate` could not do this.
   - Copper went from 809.75 to **781.94 mm**; the board stayed buildable with 0 floorplan errors.
   - route_review then listed no turned part.
4. **`--direction-preference-cost 0`** took copper from 781.94 to **758.1 mm** and 184 segments. The default of 250 prefers horizontal on F.Cu and vertical on B.Cu, which forced detours on this board. Grid 0.05 on its own gave 781.66.
5. **Plateau.** None of the following beat 758.1, so the optimisation stopped:
   - direction preference 0 with layer costs 1.0/1.5 (797.3 mm), 1.0/3.0 (829.2 mm) or grid 0.05 (779.1 mm);
   - the six seeds again under the direction-preference-0 chain: the best 0-via board was seed 6 without the R207 swap (787.7 mm); seed 11 reached 733 mm but with 2 vias;
   - seed 11 with layer costs 1.0/1.5 (still 2 vias);
   - seed 11 with via cost 2000 (4 vias). Its rescue also narrowed Net-(U301B-+) to 0.127 mm, below the 0.2032 mm board minimum, giving 3 undersized tracks.
6. **Iteration passes and the dangling stub.**
   - The final chain's two iteration passes smoothed copper from 758.1 to 740.64 mm and 159 segments.
   - They left a 0.038 mm off-grid stub on /ampli_ht_horizontal/S_OUT+, which `check_weird` and KiCad both call dangling, so `check_complete` said INCOMPLETE.
   - Forcing a re-route of that one net on the 0.05 grid removed it: **740.61 mm, 158 segments** (TOOL_GAPS entry 1).
7. **`beautify_labels.py`** on the kept placement (reference text only) cut KiCad's silkscreen errors from 92 to 8. The copper is identical.

`CHOSEN.json`: round 1, seed 6 (clustered); `after` lists the R207 pad swap and the label tidy.

## 4. Stop rule and remaining blockers

**Stop condition 1 (DONE).** board_score blocking is 0, `check_complete` says DONE, and the verifier passed. The optimisation after DONE then stopped on a plateau: after the last gain, three different approaches lowered neither vias nor copper:
- chain variants;
- re-judging the seeds under the final chain;
- removing seed 11's vias.

The ledger is closed with `--final --stop-condition 1` and the three verifier lens files; it has 58 rows.

**Remaining blockers: none.** These items do not gate:
- **KiCad silkscreen errors (8):**
  - R312's reference text overlaps U301's outline three times.
  - D204's reference text overlaps D203's "K" text.
  - The "K" text of D202, D301, D302 and D304 sits on pads of R205, R304, Q301 and R305.

  They are cosmetic and not in any gate.
- **`check_floorplan --intent` exits 4 with 0 errors.** The given intent leaves three rules (`zone_containment`, `decap_distance`, `legality`) undeclared, and withholds three budget values because the input was a pile. These are gaps in the intent, which I was not allowed to edit.
- **Report-only body-to-edge band** (JLCPCB's 2.5 mm assembly rule): Q203 0.571 mm, R211 1.25, D204 1.35, P102 1.875, C105 2.207.

## 5. Floors

- `route.py` printed no `Design rules [...]` line in the final chain. There were 0 escalations, and nothing was delivered below the requested sizes; `min_clearance_used` was 0.3, the clearance of both net classes.
- The board was routed at 0.3 mm clearance with 0.4 mm tracks (Default class) and 0.6 mm tracks (power class), and has no vias.
- **DRC writeback:**
  - It raised `min_copper_edge_clearance` from 0.01 to 0.2 mm, the fab edge floor, which is stricter.
  - It added `min_via_drill` 0.508.
  - It lowered no floor.
- **`check_complete --authored-from <input>`:** DONE, with no floor relaxed and none kept. Three floors are vacuous:
  - `min_via_diameter` 0.889 and `min_via_annular_width` 0.05, because the board has no via;
  - `min_hole_clearance`, which is declared 0.

## 6. Timeline and where the time went (UTC, 2026-10-20)

| Time | Event |
|---|---|
| 20:02:53 | FIRST_CMD written to STATE.md |
| 20:02–20:05 | Read the board (board_brief, board_context, list_nets); wrote groups.json; ran check_groups and check_floorplan |
| 20:05:28–20:05:46 | Round 1 placement, 12 seeds in 18 s |
| 20:06–20:08 | Fast routes of the 6 judged seeds (about 2 s each), quick_score, ledger; seed 5 kept |
| 20:08–20:10 | Full route of seed 5 plus 2 iterations, then verification: **first DONE** (9 vias, 857.28 mm) |
| 20:10–20:19 | Optimisation after DONE: about 35 full routes of 5–12 s each |
| 20:20–20:23 | Final chain; found the dangling stub and fixed it with a scoped re-route |
| 20:24–20:25 | Label tidy, fresh `final_route/`, `final.kicad_pcb` |
| 20:25–20:31 | grade.py, KiCad DRC, verifier (one call, about 3 min, PASS), TOOL_GAPS.md, ledger closed |

The board was frozen about 22 minutes after FIRST_CMD (20:25), and the run closed about 28 minutes after it (20:31).

`measure.py --self --evidence` (in `measure_output.txt` and `measure.json`) measured 0:27:10 of wall time when it ran:
- 978.6 s of model time, 629.2 s of tool time, 22 s waiting on background jobs;
- 142 tool calls, including 33 `route.py` and 31 `board_score`.

Machine time was small: placement took 18 s and every route took under 16 s. The time went to reading, checking, and the optimisation loop after DONE.

## 7. Tool gaps (full detail and repro commands in TOOL_GAPS.md)

1. **`route.py` ships an off-grid T-junction stub** that `check_weird` and KiCad call dangling while `board_score` reports blocking 0. The cause is the truncation bug in #1291, which was closed today; its fix is not on this branch (line 4707). The related issue #1234 is still open.
2. **route_review's "turn 180" is not what `place_pose rotate` does** for an axial part.
   - `rotate` sets the angle absolutely by default, so `rotate R207 180` made a quarter turn and was refused for a pad stack.
   - With `--relative` it pivots on pad 1, which landed R207 on two neighbours (NOT BUILDABLE).
   - What swaps the pads is a `set` to the other pad's position at the angle plus 180°. SKILL.md §3.6 tells you to use `rotate`.
3. **`kicad_drc_compare --baseline`** opens its report with the input pile's 729 violations, as if they belonged to the board being graded.
4. **`place_pose` reports `legal: false` on every pose on this board.** One outline corner is 16 µm off square, so the pad-to-edge check falls back to sampling and leaves all 165 pads unmeasured.

The fast-route judge's ranking did not hold up on this board: it kept seed 5 (4 vias), whose full route had 9 vias, and the full-route re-judge chose seed 6. This is not a tool fault.

## 8. Verifier verdict

- **verdict_1.txt: VERDICT=PASS.**
  - The sha matches.
  - `check_assembly` says buildable, with no gating copper and no part left in the pile.
  - Floorplan has 0 errors, and Q304's pose is exact.
  - board_score blocking is 0 (0 vias, 740.61 mm, 158 segments).
  - `check_complete` says DONE, `check_connected` finds every net connected, and `check_drc` is clean.
  - The verifier's own `kicad-cli` run found 0 copper violations and 0 unconnected items, plus the 8 non-gating silkscreen errors.
  - The connectivity, drc and spec lens files all say PASS.
- One of the three allowed verifier calls was used.

## Files

Everything is in `wk/gp14/03_complex_hierarchy/`:
- **The board:** `final.kicad_pcb` with `.kicad_pro`, `FINAL.sha256`, `DONE`.
- **Inputs I placed with:** `groups.json`, `intent.json` (given, unchanged), `net_min_widths.json`, `CHOSEN.json`.
- **Routing:** `final_route/` holds `redo_commands.sh`, the plan as `.sh` and `.json`, and every step's board, JSON and route trace.
- **Record:** `ledger.jsonl`.
- **Placement:** `r1/` holds the fixed board, groups, intent, 12 seeds, `judge.json` and the fast routes.
- **Optimisation:** `opt/` holds every route tried after DONE.
- **Earlier chains:**
  - `final_route_old1/` is the first DONE chain.
  - `final_route_old2/` is the chain before the label tidy, with the same copper.
- **Grading:** `verdict_1*.txt`, `grade/`, `measure_output.txt`.
- **Tool problems:** `TOOL_GAPS.md` and `repro/`.

I wrote no helper scripts, so the empty `helpers/` folder was removed.
