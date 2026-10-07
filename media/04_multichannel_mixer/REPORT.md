<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT: fa10 / 04_multichannel_mixer (`/pcb-free-agent full`)

## Result: NOT DONE

Final board: `wk/fa10/04_multichannel_mixer/final.kicad_pcb` (+ `final.kicad_pro`, + `final.design-brief.json` copied from the input brief)
sha256 `0cd0dbd019b3a901554e063618af3e95b88fae3fca34b237e53ac07c856ff870`

Graded with every spec the board declares (Board Setup: min track 0.3, min via 1.5, min drill 0.3):
`board_score --intent intent.json --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --baseline multichannel_mixer.kicad_pcb`

| DONE condition (`full`) | measured | met |
|---|---|---|
| board_score `blocking` 0 | **6** | no |
| unrouted 0 | 0 | yes |
| broken 0 | **6** (GND 2, Net-(IC2B-OUT) 2, Net-(IC3B-OUT) 1, Net-(IC5B-OUT) 1) | no |
| check_complete DONE | INCOMPLETE (blocking = 6) | no |
| drc (board_score) | 0 | yes |
| check_drc at the declared 0.3 clearance + spec sizes | NO DRC VIOLATIONS | yes |
| KiCad 10 DRC (`kicad-cli pcb drc --severity-error --refill-zones`) | 0 violations, 6 unconnected items (the same 6) | -- |
| undersized (via < 1.5, track < 0.3) | 0 (all 198 vias 1.5/0.6, all 1064 segments 0.3) | yes |
| assembly (check_assembly --intent intent.json) | buildable, blocking 0, advisory 0, courtyard_blocking 0 | yes |
| floorplan (check_floorplan --intent intent.json) | 0 errors; decap_pin_distance graded on all 5 supply pins | yes |
| check_weird | NO WEIRD THINGS FOUND | yes |
| pad, graphic, keep-out or courtyard copper off the outline | none | yes |
| mechanical facts (22 declared poses) | 22/22 exact (verifier) | yes |

- **`blocking_by`:** unrouted 0, broken 6, drc 0, undersized 0, floorplan 0, assembly 0.
- **Ungraded (nothing declared):** impedance, length, net_widths.
- **Quality:** 198 vias, 3756.8 mm copper, 1064 segments.
- **Independent `grade.py`** (`--spec min-track-width=0.3 --spec min-via-diameter=1.5 --spec min-via-drill=0.3`): done false, blocking 6, unrouted 0, broken 6, drc 0, vias 198, copper_mm 3756.8, segments 1064, check_complete INCOMPLETE, check_complete_authored INCOMPLETE, assembly buildable, floorplan_errors 0.

## Stop rule that fired

"If DONE will not come: after three consecutive DIFFERENT approaches that each fail to lower unrouted + broken, stop." It is closed as `STUCK`, the ledger's name for that plateau.

The best unrouted + broken was 6, reached by route/p5_s1g at 15:15Z. After it, each measured with identical spec flags:
1. **Re-placing the GND anchor vias** that walled the neighbouring channel (p5b): best 7 (p5b_R6g).
2. **Targeted retries ripping the router's own named blockers** (`--rip-existing-nets`): the board came back unchanged (p5_s3, p5b_s1: same copper and via count).
3. **Six whole-board parameter variants on p5b:** ordering inside_out 12, ordering original 12, direction backward 8, grid 0.05 9, max-ripup 10 8, heuristic 1.5 with 400k iterations 7.
4. **Pre-routed, locked under-body vbias links** on every op-amp (p6l): vbias fully joined, but 8, and 7 after the finishing recipe.

### Every remaining blocker on final.kicad_pcb (from board_score, check_connected and KiCad DRC)

| net | joins | stranded pads (B.Cu) | measurement |
|---|---|---|---|
| GND | 2 | IC3.4 (125.97,104.10) and C12.1 (137.66,99.81), each on its own fill island | The verifier found these islands with pcbnew. Each anchor via lands in an F.Cu pour island walled in by signal tracks. No 1.5 mm via fits inside both an island and the main fill on the other layer, and every strap or bridge candidate (8-13 per cluster) failed check_join. The in-house copper grade passed GND; only KiCad's refill sees the islands. |
| Net-(IC2B-OUT) | 2 | R10 (136.60,106.18), IC2.7 (142.57,101.56), R9 (153.37,99.95) | The router's hint names pre-existing blockers R14-Pad1, C7-Pad2, IC3A-IN-, C9-Pad1, +12V, R47-Pad1, C10-Pad1. Ripping them left the board unchanged. |
| Net-(IC3B-OUT) | 1 | R20 (131.37,99.95) | The same R9-equivalent pad, one strip west. |
| Net-(IC5B-OUT) | 1 | R42 (109.37,99.95) | The same R9-equivalent pad, two strips west. |

The three *B-OUT failures are the same relative pad (R9/R20/R42 at strip x + 16.6 mm, y 99.95) in three of the four identical channels. Only the rightmost channel, whose neighbour is the nearly empty master section, routes. That points at the replicated arrangement's right-hand escape, so it is placement-shaped. I did not re-enter placement because the stop rule had already fired.

## Floors

- **Routing floors:** every route ran exactly at the board's Board Setup floors: track 0.3, clearance 0.3, via 1.5/0.6, `--escalation board`, `--fab-overrides fab_board_floor.txt`. route.py printed no `Design rules [...]` narrowing line in the final chain (`escalations: 0`, `min_clearance_used: 0.3`, `finalize_excluded_nets: ["GND"]` on the retry).
- **Project file:** `final.kicad_pro` still declares min_clearance 0.3, min_track_width 0.3, min_via_diameter 1.5, min_via_annular 0.3, min_through_hole 0.3. route.py also added `rules.min_via_drill 0.6`, a key the input did not have.
- **Earlier arms:** their projects were rewritten to 0.45 mm vias by route.py (TOOL_GAPS 1). None of that copper or project is in the final chain.
- **`check_complete --authored-from multichannel_mixer.kicad_pcb`:** INCOMPLETE (blocking 6). It lists no floor gone below and notes that copper-to-hole clearance (declared 0.25) is not measured by it; check_drc measured it clean.
- **Via-in-pad, disclosed:** 71 vias sit in SMD pad or paste openings (the router's default). The file is KiCad 9 format, so check_drc accepts them as undeclarable via-in-paste. A no-via-in-pad arm (`--same-net-pad-clearance 0.1`, m3_D) measured worse: 7 nets open, 2 unrouted.
- **Remaining KiCad warnings:** 25 connection_width, 1 track_dangling, plus silk and library warnings.

## Intent files I wrote (the given intent.json is unchanged)

- **`intent_zoned.json`:** intent.json plus one zone per channel sheet (the 22 mm strip under its jack and pot column) and a `master` block (IC1, R1-R3, C1-C4) east of x 177.9. Why: the unzoned seed (s0) put all five op-amps in one cluster east of centre, far from their channels' pots, with 5 decap errors. With zones, each channel's parts stay in their strip.
- **`intent_zd_probe.json`:** a probe that armed `decaps.max_distance_mm` to measure the seeder's decap stage (TOOL_GAPS 3). Not used for the board.
- **`intent_esc.json`:** B-side escape-lane keep-outs beside every SOIC pin column. It measured worse (e2 11, e3 14) and was not used.
- All grading (ledger, verifier, grade.py) used the given `intent.json`.

## Timeline (UTC, from FIRST_CMD 12:07:02)

| time | elapsed | event |
|---|---|---|
| 12:07 | 0:00 | FIRST_CMD; read the README, the skill and the verifier brief |
| 12:11 | 0:04 | 22 declared front-panel poses set and locked (p0_fixed) |
| 12:28 | 0:21 | first legal placement (seeds/k2: blocking 78, all of it unrouted) |
| 12:37 | 0:30 | placement m3 kept (radial caps hand-seated, no body overlaps) |
| 12:51 | 0:44 | first routed board (probe k2_r1: 11 nets open, 10 sub-floor GND vias) |
| 13:20 | 1:13 | `--layer-costs 1 1` found (m3_B, 155 vias) |
| 14:07 | 2:00 | r3 (decaps off the pin rows) routes to broken 9 |
| 14:28 | 2:21 | channel replication (p4_rep: crossings 327, hpwl 2887) |
| 14:51 | 2:44 | GND anchors: p5_B reaches blocking 9 with zero sub-floor vias |
| 15:15 | 3:08 | best board p5_s1g: blocking 6 (signal-only retry + GND stitch) |
| 15:20-16:24 | 3:13-4:17 | four approaches fail to beat 6; stop rule fires |
| 16:28 | 4:21 | final frozen: decaps moved 0.22 mm off the IC courtyards, R45 nudged 0.1 mm inside the outline, 5 dangling vias removed |
| 16:31 | 4:24 | verifier call 1 |
| 16:48 | 4:41 | ledger closed, film written |
| -- | -- | first DONE: never |

## Where the time went

`measure.py` on this session's transcript, at 4:25:41 wall:
- **1h32m waiting on background jobs:** route.py runs of about 15-25 min each, up to 7 in parallel on 8 cores.
- **2h05m in foreground tools:** seeds at about 40 s each, board_score at 30-60 s each, the exact-fill GND stitcher at 20 s to 3 min per board, check_join chains.
- **49 min of model time.**
- 353 tool calls (312 Bash) and roughly 45 whole-board or chain route runs.

## What worked (measured)

- **Seating the fixed and awkward parts by hand before seeding** (22 front-panel poses, 5 op-amps with their decaps, 11 radial electrolytics). Every later seed had 0 grade errors, 0 unseated parts and 0 courtyard-blocking pairs.
- **One strip zone per channel sheet** kept each channel's parts in its strip (s0 to z0).
- **`--layer-costs 1.0 1.0`** instead of the default F 1 / B 3: on m3, vias fell from 214 to 155. Making B cheaper (2/1) was worse on r3 (broken 15 against 9).
- **Moving the decaps off the pin rows** (helper decap_escape_pose): broken went from 19 (m3_B) to 9 (r3_B).
- **Replicating the channel that routes** (c11f onto the other three strips): crossings 366 to 327, hpwl 3004 to 2887.
- **Locked 1.5 mm GND anchor vias placed before routing** gave the first pour route with zero sub-floor vias (p5_B, blocking 9).
- **Signal-only retries (GND left out of `--nets`) plus GND stitching with board-floor vias inside KiCad's exact fill:** 9, then 8, then 6.
- **`--max-ripup 6`** helped on r3 (9 to 8) but tended to add sub-floor vias.

## What did not work (measured)

- **`--fab-overrides` with the board floors:** identical to the baseline, still 14 vias at 0.45 mm (m3_C).
- **Spreading the seed** (`place_seed --clearance 1.0`): w3 no better (7 open, 232 vias).
- **No via-in-pad** (`--same-net-pad-clearance 0.1`): worse (m3_D).
- **Routing without the pour** (GND as tracks): broken 21 (r3nz_B).
- **Buses first** (+12V, vbias, /CH1/OUT): 20-25 broken; the buses walled off the channels.
- **Escape-lane keep-outs:** e2 11, e3 14.
- **`--ripup-blocker-select mincut`:** byte-identical to running without it.
- **Six parameter variants** (ordering, direction, grid 0.05, max-ripup 10, heuristic 1.5): 7 to 12.
- **Targeted retries:** collateral rips (#1156), then no-ops.
- **Unlocked pre-routed vbias links** were ripped (vbias 10 joins). Locked ones fixed vbias but moved the failures to other nets.

## Tool gaps

Full entries with repro commands and issue searches are in `TOOL_GAPS.md` (9 entries). Top three:
1. **0.45 mm vias from the plane finalize.** `kicad_oracle.py` hard-codes a 0.45/0.2 via rung that ignores `--escalation board` and `--fab-overrides`. route.py then rewrites the project's minimum via from 1.5 to 0.45, so check_drc and KiCad read the copper clean. Related open issue #1170.
2. **Targeted retries.** They rip nets outside `--nets` (#1156 open), then stall and return the input unchanged.
3. **Seeder decap stage.** It never serves `IC`-prefixed chips (`decap_owner_chips` is not exposed) and needs `decaps.max_distance_mm`. `--decap-claim-after-ics` and `--repair-decaps` did nothing here; #1105 is related.

Also measured:
- check_assembly calls body collisions of courtyard-less radial caps "advisory" (#1182).
- place_seed refuses the board built in the skill's own lock-first order (#1165).
- Every grader defaults to the 0.2 Default class instead of the board's 0.3 floor. board_score reported drc 0 on a board with 4 pad-to-track violations at 0.3.
- check_assembly called five IC/decap courtyard overlaps advisory while KiCad's DRC reported them as errors; I fixed them before freezing.
- No tool replicates a known-good channel arrangement onto identical sheets.
- A SOIC with no room between its pins at this board's rules is not escape-graded.

Helpers I wrote (each is a TOOL_GAPS entry): `helpers/fside_body_fix.py`, `decap_escape_pose.py`, `replicate_channel.py`, `zone_strip.py`, `drop_small_vias.py`, `gnd_previas.py`, `gnd_stitch.py`, `underbody_links.py`.

## Verifier verdicts

**Call 1 (the only call): VERDICT=FAIL**, which agrees with the NOT DONE claim.
- **Identity:** sha256 matches; the board was not modified.
- **Rules:** read from `final.kicad_pro`. Copper: 1064 segments all 0.3 mm, 198 vias all 1.5/0.6, so the size floors are met.
- **check_assembly:** buildable at 0.2 and at 0.3 with `--baseline`; no gating refs; no part left in the pile.
- **check_floorplan:** 0 errors, 0 warnings. It exits 4 "not fully graded" because budgets were abstained and rules are owed dispositions; oob_count 0.
- **render_placement:** nothing off the outline; the verifier looked at the PNGs.
- **Mechanical facts:** 22/22 at the exact declared x, y and rotation 90, all KiCad-locked.
- **board_score:** blocking 6 = broken 6. check_complete INCOMPLETE. check_connected: 4 nets, 6 joins (as itemised above); GND has 3 clusters after KiCad's refill, while the in-house copper grade passed it.
- **check_drc:** 0 violations at the default 0.2 and at 0.3. KiCad DRC: 0 violations, 6 unconnected items.
- **Declared classes:** none.
- **Lens files:**
  - `VERDICT=FAIL:lens=connectivity;finding=4 nets broken, 6 joins needed ...;evidence=6`
  - `VERDICT=PASS:lens=drc`
  - `VERDICT=FAIL:lens=spec;finding=check_complete INCOMPLETE blocking 6 (all broken nets); mechanical facts 22/22 exact;evidence=6`

Ledger: 58 rows, closed with `--final --stop-condition STUCK` and the three lens files. Film: `04_multichannel_mixer_film.mp4`, 871 frames, 3D board box.
