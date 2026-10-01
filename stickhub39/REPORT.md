# Run 39: StickHub, `/pcb-free-agent full`, from the pile, no hand placement

Tools: PR #1110 branch `fix/run38-placement-route` at `18221cc8`, worktree `krt-run39`.
The board is CC BY-NC-SA, so nothing here is committed.

## Result: NOT DONE by the letter. Every real condition is met; check_complete fails on a checker phantom

| DONE condition (full mode) | measured on `final.kicad_pcb` | pass |
|---|---|---|
| board_score blocking 0 | **0** | yes |
| unrouted 0 | **0** | yes |
| broken 0 | **0** | yes |
| check_complete DONE | **INCOMPLETE** (exit 4), from `pad_overlaps` only | **no** (see below) |
| check_connected | ALL NETS FULLY CONNECTED; the verifier's KiCad refill cross-check agrees | yes |
| DRC (`check_drc --baseline p01_pile --clearance-margin 0.1`, at the project's 0.1) | 0 violations; 76 vias in paste, all filled and capped | yes |
| check_weird | NO WEIRD THINGS FOUND | yes |
| check_assembly | buildable (blocking 0) | yes |
| check_floorplan --intent intent270.json | 0 errors (4 warnings) | yes |
| mechanical: J1, H1, J2-J8 locked poses; Edge.Cuts | identical to the input (20 Edge.Cuts items, same hash) | yes |

- `blocking_by`: unrouted 0, broken 0, drc 0, assembly 0, floorplan 0, undersized 0.
- impedance, length and net_widths are **ungraded (UNEXAMINED)**. The project declares none of them: it has only the Default netclass, and the verifier judged that net names alone do not declare the USB pairs.
- Quality: **175 vias, 726.15 mm copper, 935 segments.**
- `final.kicad_pcb` sha256 `3e92aa55ac9dcb0cf8f7c632380c7a59adec50751196b812f43d80c67f7c87ad` (= `O5.kicad_pcb`).

**Why check_complete fails (tool defect, not the board).**
- Its `pad_overlaps` component runs `check_pads.py --cross-footprint`, which reports JP1.1 (Net-(J1-Pin_1)) against JP1.2 (VIN), "overlap 0.150 mm".
- JP1 is a `JP-2_1.5x1.5` solder jumper: two `connect custom` pads made of interleaved triangles.
- `check_pads._pad_outline_polygon` models each pad as its 2.1 x 1.5 bounding box, and the pad centres are 1.95 mm apart.
- On the true primitives (`pad.polygons`, shapely) the intersection area is 0.0 and the minimum gap is 0.150 mm. check_drc agrees.
- The same finding appears on the input pile and on the human reference. No placement or routing can clear it, so check_complete cannot say DONE on this design.
- The verifier confirmed all of this independently.

**Comparison:**
- **Run 38:** blocking 15 (3 unrouted, 12 broken), 195 vias, 851 mm, 1395 segments, after hand-locking U1/U2, a hand rotation sweep, 4 hand cap poses and an intent keep-out.
- **Run 39:** blocking 0, 175 vias (-10 %), 726 mm (-15 %), 935 segments (-33 %), with no hand coordinates.
- **The human placement routed by our router** reached 4. This run beats it on blocking.

## Stop rules

- **First reach DONE.** Blocking 0 was first reached at 15:15 (M2) and first reached clean at 15:31 (K4; M2 carried 3 stacked GND duplicates).
- **Optimise after DONE.** Round 1 cut vias 181 -> 177 (-2.2 %) and round 2 cut 177 -> 175 (-1.1 %). Two consecutive rounds were under 5 %, so the optimisation stop fired.
- **Ledger.** It is closed with `--final --stop-condition STUCK`. The reason: DONE's check_complete term cannot be satisfied because of the check_pads phantom above. It carries the three lens files.

## Manual interventions

None:
- no hand-chosen coordinates;
- no locks beyond the file's own (J1, H1, J2-J8);
- no hand-written or hand-deleted copper.

**One intent edit** (`intent_changes.diff`; `intent270.json` = `intent_emitted.json` + one block):

    "blocks": [{"name": "hub_rotation", "refs": ["U1"], "rotation": 270,
                "note": "U1 rotation is a pin-order decision (#893); swept 0/90/180/270/225 and chosen by measurement"}]

Why the edit was needed:
- The seeder keeps a part's input rotation when it fits. The pile has U1 at 0 deg.
- At 0 deg, U1's U5D/U6D pins (left-column ports J6/J7) face east and its U4D pins (right-column J5) face west. board_context shows 5 CROSSED U1 interfaces.
- `converge.py poses --ref U1` cannot rank rotations on a seeded board: it dropped all 323 candidates, including 90/180/270 in place.
- The seeder documents `blocks[].rotation` (#893) as the channel for a rotation that is a pin-order decision.

How 270 deg was chosen: from all 5 candidates, by the seeder's own numbers, with seeds 0 and 1 for each:

| U1 rot | crossings (s0 / s1) | hpwl (s0 / s1) |
|---|---|---|
| 0 | 262 / 222 | 543 / 527 |
| 90 | 376 / 328 | 614 / 571 |
| 180 | 285 / 257 | 550 / 531 |
| **270** | 264 / **182** | 523 / **466** |
| 225 (the human's angle) | 266 / 262 | 564 / 566 |

The seeder places every part, including U1's position. The intent was emitted from the pile with `--decaps-from stickhub_ref.kicad_pcb`, which armed decap 2.18 mm / pin 1.77 mm, as the skill requires. The reference was used for nothing else.

## Floors (below the authored Board Setup)

`check_complete --authored-from p01_pile` returns **UNSOUND** (reported, not gating):
- track width 0.15 -> 0.1
- via diameter 0.5 -> 0.25
- via annular ring 0.1 -> 0.05
- hole diameter 0.25 -> 0.15

The project's Default class now reads clearance 0.1, and DRC was graded there. The finishing passes requested track/clearance 0.0889; route.py delivered 0.1 (the floor it reports). Via 0.25/0.15 requires the fab's advanced tier.

route.py's line on the main routing step (V5): `Design rules [--escalation fab, --fab-tier auto]: 5 feature(s) on 5 net(s) delivered below the requested size (smallest via diameter 0.25 mm); 22 fab-tier escalation(s) to advanced.`

## The chain that produced the final board

1. `place_seed p01_pile --intent intent270.json --seed 2 --rotate-by-facing --diagonal-rotations --force --decap-owners-first` -> `sr270_2` (crossings 148, hpwl 455).
2. `place_seed --repair --repair-decaps` -> `rp270_2` (floorplan 0, buildable, copper-free DRC clean). This is the kept placement.
3. `route.py` over all 44 non-GND nets at `--track-width 0.1 --clearance 0.1 --via-size 0.3 --via-drill 0.15 --grid-step 0.05`. No qfn_fanout, no route_diff. -> `V5_route`.
4. `route_planes --nets GND GND --plane-layers F.Cu B.Cu` -> `V5_pl`.
5. `repair_planes` with GND on both layers at fine geometry (`--track-width 0.1 --min-track-width 0.1 --clearance 0.1 --via-size 0.3 --via-drill 0.15 --grid-step 0.05`) -> `V5_rq3`: blocking 1 (/U4D+ at U1.12) and no stacked copper.
6. `route.py --nets /U4D+ /U4D- /U3D- /U3D+ --force-reroute`, with `--rip-existing-nets` set to the 7 blockers route.py itself named. Run at 0.0889/0.25/0.15, grid 0.05, improvement gate on. -> `J4`: blocking 0.
7. `route.py --force-reroute` on the 4 nets check_weird named removable (/LED1, /U1D+, /U5D+, Net-(U1-TEST1#)), gate on -> `K4`: check_weird clean.
8. Via rounds: force-reroute /U7D+- at `--via-cost 200` (-> O2, 177 vias), then /LC at `--via-cost 200` (-> O5, 175 vias). O5 is the final board.

## Timeline (2026-10-01, start 13:11:44)

| time | event |
|---|---|
| 13:15-13:16 | 8 seeds: 4 without and 4 with `--decap-owners-first` |
| 13:17:40 | first legal placement `rpB_0` (floorplan 0, buildable, DRC clean) |
| 13:29-13:30 | first routed boards at U1 0 deg, run-38 chain: blocking 31-37 |
| 13:35 | U1 rotation sweep (intent blocks) picks 270 deg |
| 13:38:59 | `rp270_2` legal; this is the kept placement |
| 13:49:45 | 270 deg placements, run-38 chain: blocking 16 / 16 / 19 |
| 14:10 | scoped rounds (`--rip-existing-nets '*'`): 12 -> 9, then a plateau |
| 14:28:39 | single fine-geometry route.py pass (R0): **5** |
| 14:50 | parameter sweep: `--max-ripup 12` -> 4, `--grid-step 0.05` -> 4 |
| 15:00 | repair_planes at fine geometry: **2** |
| 15:08 | narrow pass at 0.0889/0.25: **1** |
| 15:15 | M2: **first blocking 0** (with 3 stacked GND duplicates) |
| 15:29-15:31 | J4 -> K4: blocking 0, check_weird clean |
| 15:36-15:40 | via rounds 1-2 -> O5 / final (175 vias) |
| 15:43-15:47 | verifier call 1: FAIL on spec (pad_overlaps phantom only) |
| 15:47-16:00 | grade, film, report |

Wall time to the final board: **2h28m**. Total including verification, film and report: about 2h50m. That is well under the 8 h cap.

## Where the time went

`steps.jsonl` has 254 tool steps summing to 427 min of CPU time, run 3-8 at a time:

| tool | steps | minutes |
|---|---|---|
| route.py | 68 | 196 |
| repair_planes | 62 | 141 |
| place_seed | 36 | 61 |
| place_route_loop | 1 | 21 |

My own time (reading logs, deciding) was about 40 min of the 2h28m; the rest was waiting on parallel jobs. `measure.py --root .` refused ("no transcript under ...krt-run39"), because this session ran as a subagent from another project directory.

## What worked and what didn't (measured)

**Worked:**
1. **`--decap-owners-first` (#1105)**, A vs B arm, same seeds 0-3:
   - decap stage claimed 0 -> 16 caps;
   - seed floorplan errors 12/18/14/13 -> 1/1/5/5;
   - crossings mixed (best 236 -> 222).
   - Kept for every later seed.
2. **U1 at 270 deg via an intent rotation block:**
   - seeder crossings 222 -> 182 (and 148 on seed 2);
   - first full route 31-37 -> 16-19 on the same chain;
   - the scoped rounds at 0 deg did not improve at all (S1: 31 -> 31).
3. **One fine-geometry route.py pass instead of qfn_fanout + route_diff + default-width route:** on the same placement, blocking 16 -> 5 after planes and repair (Y2 vs R0). Found from place_route_loop's own round-0 probe log, which showed only 3 failed pad pairs.
4. **route.py parameters:** `--grid-step 0.05` or `--max-ripup 12` took 5 -> 4 (V5, V4). Ordering inside_out/original and backward direction were worse (14-42).
5. **repair_planes at the routed geometry** (track 0.1, via 0.3/0.15) instead of its defaults (min track 0.2, board via 0.5): 4 -> 2 on V5 and GND fully connected. At grid 0.05: 4 -> 1 with no stacked copper.
6. **Narrow, gated force-reroutes naming the exact blockers route.py's hint lists:** 1 -> 0. Making the collateral nets (/U3D+-) targets was what passed the gate: J4 passed, while J1/J3/J5/J6 were rejected or failed.
7. **Via rounds:** force-reroute single nets at `--via-cost 200`: 181 -> 175.

**Didn't work:**
- **Scoped rounds with GND in `--nets`:**
  - With the improvement gate on, they were rejected because GND read 1 -> 23 before repair_planes could reweld (Y2s1).
  - With the gate off: 16 -> 12 -> 9, then a plateau (Y2b 17, Y2d 10, Y2e 14).
  - On R0 they made 5 worse (7, 23, 26).
- **Rip blocker selection** `mincut` / `near-target` / `bidir`: 9 -> 9 / 9 / 10.
- **place_route_loop:** 4 rounds, probe failures 3 -> 2, 41 parts nudged. Its board then routed to 3-4 with the best recipe (P4, P5), against 2-4 on rp270_2.
- **Other 270 deg seeds** with the fine recipe: rp270_5 -> 13, rp270_6 -> 23, rp270_9 -> 22. rp270_2 was clearly the best placement.
- **`--reseat C8`:** correctly refused; it landed the cap 4.47 mm off.
- **repair_planes `--rip-blocker-nets`:** worse (5-14).

## Which PR #1110 fixes visibly helped

| fix | visible here |
|---|---|
| #1105 `--decap-owners-first` | **Yes, large:** claimed 0 -> 16, seed errors 12-18 -> 1-5, and every kept placement used it. |
| #1104 repair/reseat honour `courtyards_overlap=ignore` | **Yes:** `--repair --repair-decaps` took rpB_0, rp270_2, rp270_5, rp270_6 and rp270_9 to floorplan 0. Rung results: 8 seated, 8 reverted, 3 disproportionate, **0** reverted for `legality.overlap_area` (run 38 had 6). There were 0 hand cap poses (run 38 had 4). |
| #1106 body-less parts not seated under U1 | **Yes:** J9 and JP1 were outside U1's body in all 22 seeds, and no keep-out intent edit was needed (run 38 needed one). |
| #1107 broken diff-pair members not protected | **Yes, it fired:** 166 "Protection lifted" lines across the route steps (e.g. /U1D+, /U4D+-, /D-). The final fixes still named the protected nets explicitly. |
| #1108 route_planes non-zero exit when no board | Not exercised: every route_planes call wrote a board. |
| #1109 board_brief `pile` / make_film 3D | **Yes:** `pile: true`, and make_film's last line says `board box: 3D (...)`. Its human text still prints `state: placed` beside `pile: true`. |

## Tool gaps (issue candidates)

1. **`check_pads` models custom pads by their bounding box, so check_complete can never be DONE on StickHub.**
   - Location: `py_router/check_pads.py:_pad_outline_polygon` / `_overlaps_in`. The docstring claims "TRUE copper shape (... custom-polygon model)".
   - `check_pads final.kicad_pcb`: "JP1.1 (Net-(J1-Pin_1)) <-> JP1.2 (VIN) overlap 0.150 mm". The same result on `p01_pile` and `stickhub_ref`.
   - The true primitives have intersection area 0.0 and a gap of 0.150 mm.
   - Related to closed #232 (the parser's bbox fallback for gr_circle/line/rect), but this is gr_poly in check_pads.
2. **repair_planes emits stacked duplicate same-net segments, and no tool can remove them.**
   - check_weird `stacked-copper`: V5_pl 0 -> V5_rq1 3, N4 route 3 -> N4_rep 18, and K2 0-stack -> K3 15 when repair re-ran on a finished board.
   - `route.py --force-reroute` skips plane nets, so the only remedy was redoing the repair at another grid (V5_rq3).
   - New evidence for open #162 (repair_planes as a producer).
3. **repair_planes defaults ignore the geometry the chain routed at.**
   - It defaults to the board class via 0.5 and `--min-track-width 0.2`, while the signals were routed at 0.1/0.3.
   - V5: default repair 4 (GND C4.2/C34.2 stranded, though PASSABLE) vs fine repair 2 with GND fully connected. V4: 4 -> 6, so the effect is not monotone, but it decided this run.
4. **No tool chooses a large IC's rotation by connectivity on a pile.**
   - place_seed keeps the input rotation (U1 0 deg from the pile). `--rotate-by-facing` only scores edge facing.
   - `converge.py poses --ref U1` on a seeded board drops all 323 candidates, including 90/180/270 in place, so it cannot rank them.
   - The only route was an intent rotation block plus a seed sweep. 270 deg improved crossings 222 -> 182 and the first route 31 -> 16.
5. **route.py's improvement gate judges GND before the chain's plane repair.**
   - Y2s1 connected 6 nets and was reverted for "GND 1->23". With the gate off and repair_planes after it, the same round went 16 -> 12.
   - Related to closed #1032 / #1039; the trap still exists in the scoped-round recipe.
6. **Smaller gaps:**
   - The skill text says `board_brief.py <board> --json`, but `--json` requires a PATH (argparse error).
   - The first-route recipe in run 38's chain (qfn_fanout + route_diff + default-width route) is 3x worse here than one fine pass. The routing skill could say to probe both.
   - The decap rung leaves 0.2 mm misses as "disproportionate" or "reverted" (rp270_1: C8 1.98 vs 1.77 mm; rp270_0: C10/C12 2.20 mm). This was harmless here because other seeds were clean.

## Verifier verdicts

Call 1 (15:47): **VERDICT=FAIL** (`verdict_1.txt`).
- connectivity: **PASS**
- drc: **PASS**
- spec: **FAIL** on `check_complete INCOMPLETE: pad_overlaps (check_pads --cross-footprint) JP1.1<->JP1.2 bbox overlap at (148.59,106.84), true copper gap 0.150 mm, same on input and reference; mechanical facts all match`.

The verifier independently called it a checker artifact, and it is not fixable on the board, so there was no second call.

## Files

- **Final board:** `final.kicad_pcb` / `final.kicad_pro` (= `O5`), with `final.score.json`.
- **Independent grade:** `grade_final.json` from grade.py: done false (check_complete INCOMPLETE), blocking 0, unrouted 0, broken 0, drc 0, vias 175.
- **Ledgers:**
  - `ledger.jsonl`: 16 rows, closed with `--final --stop-condition STUCK` and the three lens files.
  - `steps.jsonl`: every tool step with command, exit, wall seconds, and blocking/unrouted/broken/drc/floorplan/vias after it.
- **Intent:** `intent270.json` (graded), `intent_emitted.json`, `intent_changes.diff`, and `intent_r{90,180,225,270}.json` (the sweep).
- **Film:** `run39_film.mp4` (stage3d, from the ledger).
- **Helper scripts** (none edits a board): `step.sh`, `chain.sh`, `scoped.sh`, `zfull.sh`, `plain.sh`, `plain_fine.sh`, `planes.sh`, `planes_fine.sh`, `poses.py`, `st.py`.
