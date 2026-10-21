# REPORT -- gp14 board 04 multichannel_mixer (`/plan-pcb-placement full`)

## 1. Result: DONE

- **Board:** `wk/gp14/04_multichannel_mixer/final.kicad_pcb` (+ `final.kicad_pro`), sha256 `e7b6c7936ad83fa514240c29e998ad38610d28ea5314e8ce3bc8e00cbeeb1ca9`.
- **Placement:** round 1 seed 2 (scattered start), then 4 moves to clear body overlaps and 2 relative 180° turns (`CHOSEN.json`).
- **Routing:** the chain in `final_route/`.

| DONE condition (full mode) | measured |
|---|---|
| `board_score` blocking, with the spec flags | **0** |
| unrouted | **0** |
| broken | **0** |
| `check_complete`, with the spec flags | **DONE**; impedance, length and net_widths are UNEXAMINED because the board declares none |
| `check_complete --authored-from <input>` | DONE, no floor listed |
| `check_connected` | all nets connected; KiCad refill cross-check agrees |
| `check_drc --baseline --clearance-margin 0.1` (graded at 0.3) | 0 violations; 0 unfiltered as well |
| `check_weird` / `check_orphan_stubs` | none / none |
| `check_assembly --baseline --intent` | buildable, blocking 0 |
| `check_floorplan --intent --allow-routed` | 0 errors, 0 warnings. It exits 4 because the given intent withholds `oob_count` and `overlap_area` for a pile (#1103) |
| Mechanical facts (22 poses in `mechanical.json`) | all met; worst deviation 0.000 mm, 0° |
| Pad, graphic or keep-out copper off the outline | none |

- **`blocking_by`:** every graded component is 0.
- **Quality:** **70 vias, 1964.22 mm copper, 497 segments**. The first DONE board had 99 / 1960.58 / 485.
- **Spec flags** (the board's own Board Setup minimums): `--min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3`.
- **`grade.py`** (`grade/grade_final.json`): `{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 70, "copper_mm": 1964.22, "segments": 497, "check_complete": "DONE", "check_complete_authored": "DONE", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`.

## 2. The board, the groups and the judgement calls

**The board.** 114 parts, 81 nets, 2 layers, 110 × 111 mm, a four-channel audio mixer.
- **Channel strips /CH1/../CH4/,** one TL072 each (IC2–IC5):
  - half A is an inverting preamp fed from the input jack through a 2.2 µF can and 10 k;
  - half B is a Bass/Mid/Treble tone stack;
  - a Volume pot wired as a rheostat feeds a 2.2 µF can onto the sum bus `/CH1/OUT`.
- **Master section,** IC1:
  - half A sums `/CH1/OUT` (R3 feedback) and drives C4 into the output jack J6;
  - half B buffers the R1/R2 divider (filtered by C1) into `vbias`, with C2 on vbias;
  - J5 is the +12 V DC jack.
- **Sides:** 81 SMD 1206 parts are on B.Cu; the pots, jacks and electrolytics are through-hole on F.Cu.
- **Datasheets:** not needed. Every role is plain from the nets and values.

**Fixed parts.** The 16 pots and 6 jacks are seated by the intent's `fixed_poses[]`, so they get no lock and no edge entry.

**Groups** (`groups.json`, five groups; `check_groups` reported 0 errors and 0 warnings):
- `ch1`..`ch4`: each channel strip is one group (jack, 4 pots, op-amp, 9 caps, 11 resistors), anchored on its op-amp. The channel is the functional unit: one signal chain from one jack to one pot column.
- Each op-amp's +12 V decap (C12, C21, C30, C39) stays in its channel group with its IC.
- `master`: IC1, R1–R3, C1–C4, J6 and J5, with `near: ch3`. The bias buffer and the summer share one TL072, so they stay together. J5 has no conditioning parts, so there is no separate power group.
- No `edge` or `side` hints: every connector is seated, and parts keep the face they came on.

**Repeated channels.** I did not use the "arrange one, then replicate" pattern. A dry run of `place_pose replicate --from CH1 --to CH2 --to CH3 --to CH4 --anchor RV1` was refused because the copies landed off the west edge. Every seed's channel spans 21–27 mm around its pot column, wider than the 22 mm column pitch, and confining channels to their columns would be an input change, which the stop rule forbids after a clean round.

**EMC and keep-away.** No EMC rows were given, since the user was unavailable, and I invented no limits. `board_context` finds no converter, crystal, oscillator or ESD array. There is no keep-away rule because the board is all-analog audio with no aggressor.

**Intent.** I used the given `intent.json` unchanged.

## 3. Rounds and what the routes showed

**Round 1** (`r1/`): `place_simple --round --jobs 4` took about 35 s for 12 seeds. All 12 were legal according to `place_simple`, and the judge chose seeds 10, 0, 3, 2, 6 and 4.

**Every judged seed was NOT BUILDABLE** in `check_assembly`, with 3–7 body overlaps each. All involved the 11 through-hole electrolytics or J5, which draw no courtyard (TOOL_GAPS #1). I cleared the overlaps with `helpers/fix_body_overlaps.py`, which moves the electrolytics with `place_pose`.

The first pass of that helper graded clearance at the 0.2 netclass and left two pad gaps of 0.24–0.25 mm. The first full route exposed them as 2 pad-pad DRC violations at the board's 0.3 (TOOL_GAPS #2). I reran the helper on all six seeds at `--clearance 0.3`.

**Judging routes.** The same chain for every seed: keep the board's GND pour, then `route.py --quick 2` at the board's floors. Results (blocking / vias / copper_mm / segments):

| seed | blocking | vias | copper_mm | segments |
|---|---|---|---|---|
| s3 | **0** | 64 | 1971.88 | 1337 |
| s0 | 1 | 61 | 1922.57 | 1239 |
| s2 | 1 | 59 | 1978.75 | 1310 |
| s4 | 1 | 67 | 1984.42 | 1336 |
| s10 | 2 | 55 | 1918.47 | 1391 |
| s6 | 4 | 60 | 1877.61 | 1303 |

Seed 3's fast route was clean, so placement rounds stopped there: no review and no round 2.

**First DONE at 23:47Z** came from the full route of seed 3: 99 vias, DONE.

**After DONE: vias first, then copper, then segments.** This work is in `opt/`. Every board was scored with `board_score` and the spec flags, and every rejected board is in the ledger.
- **Routing arms on the DONE placement** (layer costs, via cost 150 and 300, the 2-layer through-hole recipe): vias fell to 62–102, but every arm left the GND pour in pieces. `route.py`'s summary still said `failed 0` (TOOL_GAPS #5, #9).
- **Full routes of the other judged seeds:** s2 gave 92 vias, s4 97, s0 104, s10 106, and s6 still had 2 blocking. The fast-route judge does not predict full-route vias (TOOL_GAPS #10).
- **`route_review`'s turned two-pad parts.**
  - My first attempt used `rotate R39 180`, which is absolute (TOOL_GAPS #3). It routed to 75 vias and passed verifier call 1, but KiCad reported an R39–R42 courtyard error.
  - Redone with `--relative` (C8 180→0, R39 270→90).
- **Via-cost sweeps** across 75–200 on several placements:
  - Most arms below about 85 vias left GND broken.
  - Most clean arms left copper that `check_complete` refuses but `board_score` does not see: a dangling 3.7 mm `/CH1/OUT` stub, a stacked GND duplicate, and a vbias copper web below the 0.3 track floor (TOOL_GAPS #4).
  - A `--force-reroute` of exactly the nets `check_weird` named cleaned them.
- **Shipped:** seed 2 with the corrected turns, at via cost 135, plus that cleanup step: 70 vias, 1964.22 mm, 497 segments, DONE.
- **Plateau:** the other s2t arms gave 92, 80 (broken), 78 (broken), 80 (broken) and 77 vias. The last batch on other seeds and the earlier misrotated placement gave 76–86 vias or a broken GND.

**Routing chain** (`final_route/multichannel_mixer_plan.sh`; `route_plan_check` passed 17/17; replay manifest `final_route/redo_commands.sh`; a route trace beside each step):
1. `copy_board` copies the kept placement to `input.kicad_pcb`.
2. `route_planes --nets GND GND --plane-layers F.Cu B.Cu --skip-existing-zones`, with sizes given. This keeps the board's own dual-layer GND pour.
3. `route.py --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 135` (27 s).
4. The same command twice more, as the Step 2d iterations (6 s each).
5. `route.py --nets '/CH1/OUT' 'Net-(IC4B-IN-)' vbias GND --force-reroute`, with the same flags (7 s).

**Why this plan:**
- The board is 2-layer and STANDARD tier.
- It needs no fanout and has no diff pairs.
- No impedance step: the stackup is KiCad's default and no net needs it.
- No GND via or stitching tail, because this is low-speed audio.
- Layer costs are 1.0 / 1.0 because all SMD parts sit on B.Cu under a pour on both layers.
- For Step 5b, the route step takes `'*'` with GND in `--power-nets`.

## 4. Stop rule and remaining items

**Stop condition 1, DONE.** The post-DONE via optimisation ended on a plateau. No blocking item remains. Impedance, length and per-net widths are ungraded because the board declares none of them.

A second placement round (channel zones or a replicated channel) might cut vias further. I did not run one, because the skill stops placement at the first clean fast route.

**Disclosures from the verifier, not gating:**
- 42 vias sit in B-side paste openings. The file format cannot declare capping or filling for them, so the fab drawing needs a Type VII note.
- The GND zone is stored unfilled, as it was in the input. Refill it before plotting.
- KiCad 10 non-copper items:
  - starved_thermal ×2 (IC1 pad 4 and IC2 pad 4);
  - connection_width ×11 under the board's `min_connection` 0.3:
    - 10 GND pour necks down to 0.244 mm. The input zone's own `min_thickness` is 0.25.
    - 1 `/CH1/OUT` joint at a via, 0.148 mm. The router made this one.
  - track_dangling ×1 (a connected T-joint);
  - silkscreen warnings.

## 5. Floors

The run routed at the board's declared Board Setup minimums, which are above the Default netclass (0.2 / 0.2 / 0.6): clearance 0.3, track 0.3, via 1.5 / 0.3, with `--escalation board`.
- **`design_rules.count`:** 0 on the shipped steps, with no fab-tier escalation.
- **`check_complete --authored-from`:** DONE, with no floor listed.
- **Project writes:** only `min_via_drill: None → 0.3`, which is the board's own minimum through-hole diameter.
- **Power widths:** 2.0 mm of GND was routed at 0.3 instead of the requested 0.4. That is still within the board's floor.
- **Placement:** also graded at 0.3, using `--clearance 0.3` on `place_pose` and `check_assembly`.

## 6. Timeline and where the time went

| UTC | event |
|---|---|
| 23:19:53 | FIRST_CMD |
| 23:23:49 | Round 1 placed |
| 23:24–23:36 | All judged seeds found NOT BUILDABLE; helper written; fixes applied; judging routes run |
| 23:38–23:45 | First full route has 2 pad-pad DRC errors; fixes rerun at 0.3; seeds re-judged |
| 23:47 | **First DONE** (99 vias) |
| 23:48–00:20 | Via optimisation: 33 graded routes |
| 00:27 | Verifier call 1 PASS on the 75-via board; KiCad courtyard error traced to the absolute rotate |
| 00:33 | Rotations redone, swept, re-routed: 70 vias, shipped |
| 00:34 | Verifier call 2 PASS; ledger closed |

**Where the time went:**
- Placement legality repair: about 20 min, all due to gaps 1 and 2.
- Via optimisation: about 32 min, mostly lost to GND-island failures.
- Verification and write-up: the rest.

Raw costs are small: placing all 12 seeds took about 35 s, a judging route about 4 s, and a full route about 45 s. `measure.py`: wall clock 1:16:37, of which 604.8 s waiting on jobs, 2384.4 s other tools and 1608.1 s model; 219 tool calls (`measure_output.txt`, `measure.json`).

## 7. Tool gaps

`TOOL_GAPS.md` has 10 entries, each with repro commands against `repro/`:
1. `place_simple` ignores the body of courtyard-less parts that `check_assembly` gates.
2. `check_assembly` and `place_pose` check clearance at the 0.2 netclass instead of the board's 0.3 `min_clearance`.
3. `place_pose rotate` is absolute, while `route_review` and the skill imply a relative turn.
4. `board_score` and `check_orphan_stubs` pass weird copper that `check_complete` refuses.
5. `route.py` reports `failed 0` while KiCad's refill shows the GND pour in pieces (21 of 33 routes).
6. `check_assembly` calls a courtyard overlap "advisory" that KiCad grades as an error; no repo tool grades KiCad's connection_width or starved_thermal.
7. The skill's advice to pass `--clearance-ceiling` routes below `min_clearance` on this board.
8. `route_planes` duplicates a dual-layer zone and lowers floors it never used.
9. The router's GND-island hint is a no-op.
10. The skill has no step for "every seed NOT BUILDABLE", and judge vias do not predict full-route vias.

**Tools that said "fine" about something that was not:**
- `place_simple`: `illegal: []` on unbuildable seeds.
- `place_pose` and `check_assembly`: legal and buildable at 0.24 mm pad gaps.
- `route.py`: `failed 0` with GND in pieces.
- `board_score` and `check_orphan_stubs`: clean on a dangling segment.
- `check_assembly`: "advisory" on a courtyard overlap KiCad grades as an error.

## 8. Verifier

- **Call 1** (75-via board, sha `4a970cf9…`): **VERDICT=PASS**, all three lenses PASS. Its KiCad cross-check reported an R39–R42 courtyards_overlap error, which I traced to my absolute rotation and fixed.
- **Call 2** (shipped board, sha `e7b6c793…`): **VERDICT=PASS**, all three lenses PASS:
  - sha match; `check_assembly` buildable;
  - `check_floorplan` 0 errors; 22 of 22 mechanical poses exact;
  - `board_score` blocking 0; `check_complete` DONE;
  - all nets connected; DRC 0; sizes meet the spec;
  - KiCad courtyard overlap 0, plus the disclosures in §4.

The verdict files are `verdict_1*.txt` and `verdict_2*.txt`.

## 9. Files

All paths are under `wk/gp14/04_multichannel_mixer/`:
- `final.kicad_pcb`, `final.kicad_pro`, `FINAL.sha256`, `DONE`
- `groups.json`, `intent.json` (unchanged), `CHOSEN.json`
- `final_route/`, plus superseded chains `final_route_old1/` to `final_route_old4/`
- `ledger.jsonl` (82 rows, closed with `--final --stop-condition 1`)
- `r1/` (`fixed.kicad_pcb` with its `.kicad_pro`, `groups.json`, `intent.json`, `s<S>.*`, `judge.json`)
- `TOOL_GAPS.md`, `helpers/fix_body_overlaps.py`, `repro/`
- `grade/`, `measure_output.txt`, `measure.json`, `STATE.md`

The five input files' sha256 still match the values in the README.
