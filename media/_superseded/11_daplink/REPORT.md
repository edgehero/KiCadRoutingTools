# gpm board 11 -- daplink: REPORT

`/plan-pcb-placement full wk/gpm/11_daplink/daplink.kicad_pcb wk/gpm/11_daplink/intent.json`, followed by hand from `.claude/skills/plan-pcb-placement/SKILL.md` on upstream main bda59fa0. **`/plan-pcb-routing` (§3.8) and `/analyze-power-nets` were followed by hand from their SKILL.md files.** So were the methods those name (`/find-high-speed-nets`, `/identify-diff-pairs`, `/recommend-plane-mappings`), as quick inline scans described below.

## Result: DONE

| DONE condition (full mode) | measured on `delivered.kicad_pcb` |
|---|---|
| `board_score` blocking | **0** |
| unrouted / broken | **0 / 0** |
| joins_needed | 0 |
| `check_complete` | **DONE** (exit 0). diff_pairs, impedance, length and net_widths are UNEXAMINED: the board declares no spec for them |
| `check_assembly --baseline` | buildable (blocking 0) |
| `check_floorplan --intent intent_run.json` | 0 errors, 0 warnings |
| `check_connected` | all nets connected |
| `check_drc --baseline --clearance-margin 0.1` | 0 violations (also 0 at margin 0) |
| KiCad DRC (`kicad_drc_compare`, and `kicad-cli` on the filled board) | 0 copper items, 0 unconnected, CONSISTENT |
| verifier | **verdict_1: PASS** (all three lenses PASS) |

`blocking_by`: unrouted 0, broken 0, drc 0, drc_via_in_paste 0, undersized 0, floorplan 0, assembly 0. diff_pairs, impedance, length and net_widths were not graded because none is declared.

**Quality: 20 vias, 375.71 mm copper, 225 segments.**

- Delivered board: `delivered.kicad_pcb` (+ `.kicad_pro`), sha256 `0619d6fcca99d8aa4ba40e4be2f7402ba7770a77690c8f8d9523d7dbed6433d2` (in `DELIVERED.sha256` and `DONE`).
- Chain: `final.kicad_pcb` (pass 2, seed 11) → `final_route/` → `routed.kicad_pcb` → `labelled.kicad_pcb` → `delivered.kicad_pcb`.
  - Manifest: `final_route/redo_commands.sh`
  - Plan: `final_route/final_plan.sh`
  - GUI form: `final_route/final_plan.json`

`grade.py --mode full` (`grade.txt`, `grade_delivered.json`):
`{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 20, "copper_mm": 375.71, "segments": 225, "check_complete": "DONE", "check_complete_authored": "UNSOUND", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`. No `--spec` was passed: the board declares none.

## The board

- 2 copper layers, 50.0 x 20.0 mm, 35 parts (34 on F, J2 on B), 50 nets.
- No stackup, no `.kicad_dru`, no `mechanical.json`.
- Default net class only: clearance 0.2, track 0.25, via 0.8/0.4. The board's `min_via_diameter` is 0.5.

It is a USB-C CMSIS-DAP probe:
- STM32F103CBT6 (LQFP-48, 0.5 mm pitch) with an 8 MHz crystal;
- AMS1117-3.3 LDO;
- USB-C receptacle P1 (brief: west edge) and reset button RST1 (brief: north edge);
- J1, a 1x04 vertical SWD header that programs the STM32;
- J3 (F, target SWD/RST) and J2 (B, target UART), two right-angle SMT 1x05 headers;
- three LEDs.

## Groups and judgement calls

`groups.json` has 7 groups. `check_groups` gave 0 errors, 1 WARN and no template hints.

| group | refs | anchor | why |
|---|---|---|---|
| usb_in | P1 R1 R14 R12 R13 | P1 | USB-C with its CC1/CC2 5k1 pull-downs and the 33R D-/D+ series pair, which bridges to core |
| power | U1 C1 C2 C3 | U1 | AMS1117 with C1/C2 on the +5V input and C3 (10 µF) on VO. C3 is the LDO's required output cap and the only 3.3 V bulk cap |
| core | U2 Y1 C5 C6 C4 R2 R3 R4 R9 R10 C7 C9 R15 R5 | U2 | STM32 with: its crystal and load caps (crystal claims come from the intent), the NRST RC, the BOOT0/PC13 pull-downs, the PA0 strap divider, the USB-side 18 pF caps, the 1k5 D+ pull-up, and R5 |
| debug | J1 | J1 | vertical SWD header for the STM32 itself; no edge rule for a short vertical header |
| target | J3 J2 | J3 | target headers, both declared on the east edge (below) |
| reset | RST1 R11 C8 | RST1 | target reset button with its 10k pull-up and 10 nF cap beside it |
| leds | D1 D2 D3 R6 R7 R8 | D1 | three status LEDs with their series resistors |

Judgements:
- **R5 (100R, PB12 → TGT_SWDIO) in core, not target.** `check_groups` warned it had 2 links to core and 1 to target. PB12 is the SWDIO driver, and placement-lessons puts a series resistor at its driver.
- **C3 with the LDO (power), not the MCU.** It is the AMS1117's stability cap on VO; `check_groups` raised no decap conflict.
- **J2's WARN accepted.** J2's signals all go to U2 (TGT_RX/TX), but it is an edge connector, so it belongs where the target headers are.
- **No `edge` hint on the LEDs.** On a 20 mm board every part is within 10 mm of an edge, so the soft term would only cost wire. The power group gets no edge either, as the skill requires.
- **No templates (§3.5).** The board has no switching stage and no RF front end:
  - U1 is an LDO, which is never a template;
  - the STM32F103 has no built-in DC-DC;
  - there is no inductor, transformer, flying cap or RF part;
  - `check_groups` printed no template hint.

### Rows added to `intent_run.json` (a copy of the read-only `intent.json`)

1. **`edge_connectors[]` J3:** edge east, `overhang_mm` {6.5, 6.8}.
2. **`edge_connectors[]` J2:** edge east, `overhang_mm` {6.5, 6.8}.
   - Reason (§3.4, my judgement; the brief does not declare them): J2/J3 are Harwin M20-890 right-angle SMT male headers whose 6 mm pins point +x out of the body. In the footprint, the F.Fab body runs x −1.725 to 0.775, the pins 0.775 to 6.775, and the courtyard to 7.28.
   - In the board interior the courtyard would take 14.6 x 13.7 mm of a 50 x 20 mm board. At the edge opposite the USB they form the dongle's target end.
   - The band is read on the courtyard, because the outline is not a rectangle so no body reading is made. With the body front at the edge, the courtyard reaches 6.505 mm past it.
   - J2 is on the back, so the two stack on opposite faces. place_simple seated both, with no `oversubscribed`.
   - The Harwin PDF could not be fetched (cdn.harwin.com served HTML), so the band rests on the footprint's own Fab drawing.
3. **`edge_connectors[]` P1:** `overhang_mm` {0.5, 1.0}, added to the brief's west-edge entry.
   - Reason (§3.4): the GCT USB4105 drawing (www.gct.co, Rev B4, "Recommended PCB Layout") puts the PCB edge at the receptacle's front face. That face is the footprint's F.Fab front and its Dwgs.User "PCB Edge" line.
   - On the courtyard basis that face is 0.505 mm inside the courtyard edge.
   - Verified on the delivered board: P1's PCB-Edge line is on the outline (x=100.000).

No `overlap_waivers[]`, `proximity[]` or template rows were added. `waive_locked_overlaps.py` was not needed: nothing is locked and there are no `fixed_poses[]`.

### EMC rows

None were given. `emc_roles` found only the crystal Y1: no converter, no ESD, and `keep_away` is empty. Per the task, I invented no limits and declared no `keep_away`.

The intent's own crystal claims are warning-graded, and all pass on the delivered board (0 warnings):
- Y1 within 8.1 mm of U2.5/6;
- C5/C6 within 2.2 mm of Y1.

### Disclosure

While reading `docs/floorplan-intent.md` for the `overhang_mm` keys, I came across a paragraph that cites "daplink"'s J2/J3 and P1 band values from an earlier hand-written intent (J2/J3 ~6.46 mm, P1 0.50 mm at zero margin). It is tracked repo documentation, not one of the forbidden sources, but it describes this board's source.

My P1 band came from the GCT drawing and my J2/J3 bands from the footprint geometry, both before I reached that paragraph; the values agree. The orchestrator may want that paragraph out of reach in future campaigns.

## Placement passes

**Pass 1** (skill defaults, 12 seeds). All were legal; the 6 judged (11, 8, 0, 4, 2, 1) were buildable and floorplan-clean. Fast routes with the judging chain (`old/pass1/judge_chain.txt`):

| seed | blocking | vias |
|---|---|---|
| s8 (kept) | 0 | 33 |
| s4 | 0 | 38 |
| s0 | 0 | 41 |
| s11 | 1 | 41 |
| s2 | 1 | 43 |
| s1 | 1 | 50 |

s8 routed to DONE at 30 vias / 421.83 mm (`final_route_old4/`).

**Pass 2** (`--crossing-weight 4`; the lever is that crossings cost vias on a 2-layer board). Judged 1, 11, 0, 8, 2, 6:

| seed | blocking | vias |
|---|---|---|
| s11 (kept, clustered) | 0 | 23 |
| s1 | 0 | 27 |
| s2 | 0 | 36 |
| s0 | 0 | 41 |
| s8 | 1 | 30 |
| s6 | 1 | 61 |

s11's full route gave 20 vias / 375.71 mm.

**Pass 3** (`--crossing-weight 8`): best fast route 38 vias, rejected. Pass 2 was restored; pass 3 is in `old/pass3/`.

`CHOSEN.json`: `{"seed": 11, "start": "clustered", "pass": 2, "intent": "intent_run.json", "place_args": ["--crossing-weight", "4"], "after": []}`. `route_review` on the routed board listed 0 turned parts, so no `place_pose` change was made.

## Routing (`/plan-pcb-routing`, followed by hand)

**Step 0 gate:** `check_assembly` buildable; `board_score` baseline unrouted 29, broken 0.

**Analysis:**
- 2 copper layers, so STANDARD tier (the dense tier needs 6+ layers).
- No fanout: the LQFP-48 is a perimeter part (a candidate only) and routed without it.
- One name-detected pair, /D+ /D- (USB 2.0 FS).
- No stackup, so no impedance pass (Step 10 rule 1). `achievability_note`: 90 Ω would need a 1.19 mm leg against the 0.2 mm pin gap (12.9x), which is not achievable on this 2-layer board.
- High-speed scan (inline): USB FS 12 Mbit/s, SWD ≤ ~10 MHz, 8 MHz crystal. All below the high tier, so no GND return vias or stitching (Step 10 rule 10).
- Keep-away: none (purely digital, no switch node).
- Plane map (inline recommend-plane-mappings, Step 8 2-layer flow): GND flooded on both faces and poured last (dense 2-layer: 3.5 parts/cm²); rails as tracks.

**`/analyze-power-nets`, by hand.** Classifications:
- P1 POWER_SOURCE 500 mA (USB 2.0 default with a 5k1 Rd sink);
- U1 POWER_SOURCE 300 mA, an **estimate** (the AMS1117 is rated 1 A);
- U2 CURRENT_SINK 50 mA (STM32F103 IDD max at 72 MHz with all peripherals, DS5319, via a web search);
- J3 CURRENT_SINK 200 mA (target supply, an **estimate**);
- D1-D3 2-3 mA;
- J1, J2, RST1 and Y1 SHUNT.

The tool recommended +3.3V 1.0, GND 2.0 and +5V 0.7 mm. It sums each part's current once per power pin (TOOL_GAPS #3), so I carried **0.7 / 0.7 / 0.7 mm**: the same IPC table at the real ~300 mA budget. `power_analysis.txt` has the tool's report.

**Chain** (`final_route/final_plan.sh`; `route_plan_check`: 17 rules OK; manifest `final_route/redo_commands.sh`):
1. route_diff on /D+ /D- (0.2/0.2, clearance-ceiling 0.2). It deferred the pair as electrically short, and route.py finished it.
2. route.py `'*' '!GND'`: track 0.127, clearance-ceiling 0.2, via 0.5/0.3, power widths 0.7, layer costs 1.0 1.0.
3. route_planes: GND on F.Cu and B.Cu.
4. route.py `'*'`.
5. Two iterations.
6. **Retry: `--nets '/TGT_RST' GND --force-reroute`** to remove a dangling via (TOOL_GAPS #1).

The Step 5b ledger reconciles: GND is excluded in the signal step, claimed by the closing step, and listed in `--power-nets`.

**Arms that did not win.** All were fully routed and each is recorded `--rejected` in the ledger.

| arm | result |
|---|---|
| board floors held (`--escalation board --fab-tier standard --same-net-pad-clearance 0.1`) | /OSCOUT boxed: 1 broken, even after the rip hint and a force-reroute of its neighbours (TOOL_GAPS #2) |
| no via-in-pad only | dangling vias again, 40 vias |
| via cost 150 / 300 | 43 / 49 vias (TOOL_GAPS #4) |
| layer costs 1.0 1.5 | 30 vias / 427 mm on pass 1; 29 vias on pass 2 |
| GND poured first | 36 vias |
| seeds 4 and 0 of pass 1 | 37 / 40 vias |
| max-ripup 5 (pass 2) | identical copper |
| soft costs (ripped-route avoidance 3 + track proximity 2) | 35 vias |

## Stop rule

**Stop condition 1, DONE.** It was reached at 16:32Z on pass 1 (30 vias) and again at 16:39Z on pass 2 (20 vias).

After DONE I optimised vias, then copper. The last improvement was pass 2. Pass 3, three routing arms on pass 2 and seven on pass 1 did not beat 20 vias, so I stopped on that plateau. `converge.py verdict` reports placement as `plateau`. For routing it reports `no-comparison`, because only one routing lap in its window was accepted (see TOOL_GAPS #5).

**No blocker remains.**

## Floors

The default `--escalation fab` / `--fab-tier auto` went below the board's authored floors. route.py's `Design rules [...]` lines disclose it, and `check_complete --authored-from daplink.kicad_pcb` reports **UNSOUND** (exit 5; reported, not gating):

- **Vias:** diameter 0.5 → 0.3 on 3 of the 20 vias, all on the JLC "advanced" tier: /IF_SWDIO (125.7, 106.95), /TGT_SWCLK (129.7, 105.15), /PB5 (124.2, 109.45). Annular ring 0.1 → 0.05, hole 0.3 → 0.2.
- **Clearance:** Default class 0.2 → **0.1452**, an automatic descent on /IF_SWDIO, /PB5, /PB6, /TGT_RST, /TGT_SWCLK and Net-(U2-BOOT0). At the authored 0.2 the verifier counts 16 grazes, all on /TGT_SWCLK, closest ~0.146 mm.
- **Copper-to-NPTH-hole 0.25:** this board reaches 0.1751 in 9 places; the reference itself reaches 0.0 in 12.
- **Tracks:** signals at 0.127 mm (the board's `min_track_width` is unset). Power tracks requested at 0.7 neck to 0.127 at the LQFP pins:
  - +3.3V: 31.6 of 101.6 mm under 0.7;
  - +5V: 7.0 of 23.4 mm;
  - GND: 0.1 of 3.4 mm.
  The ampacity bottleneck on +3.3V is 0.54 A by IPC-2152, above the ~0.3 A estimate.
- **10 of the 20 vias are in pads or paste openings:** D1.1, J3.1, P1.A4, R6.1, R7.1, RST1.2, U2.12, U2.13, U2.26, U2.36. They are stamped `(capping yes) (filling yes)`, so IPC-4761 Type VII must be on the fab drawing.

The arm that kept every authored floor and forbade via-in-pad left /OSCOUT open (TOOL_GAPS #2). The shipped board therefore needs a fab that accepts 0.1452 mm clearance and 0.3/0.2 vias with a 0.05 mm ring.

## Silkscreen

`beautify_labels` turned `routed.kicad_pcb` into `labelled.kicad_pcb`: 30 labels placed, 1 rotated, 2 shrunk, R6 left as it was. KiCad's silk classes:

| | silk_edge_clearance | silk_overlap | silk_over_copper | total |
|---|---|---|---|---|
| before | 7 | 17 | 23 | **47** |
| after | 4 | 4 | 1 | **9** |

**The labelled board was kept.** `lib_footprint_mismatch` (34) is the same on both boards and comes from the input's footprints.

## Fill

`fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` ran with exit 0. It used KiCad's zone filler, wrote 6 filled polygon blocks, kept the net class, and took `unconnected (no --refill-zones)` from 31 to 0. The delivered board is filled, and nothing was routed after it.

## Timeline (UTC) and where the time went

| time | step |
|---|---|
| 16:17:43 | FIRST_CMD; read TASK, README, both skills and their references |
| 16:19-16:22 | board_brief / board_context, USB4105 datasheet, J2/J3 decision, groups, intent_run.json |
| 16:23 | place_simple pass 1 (13 s) |
| 16:24-16:26 | judge pass 1 (6 seeds, ~2 min with checks) |
| 16:26-16:28 | analyze-power-nets, routing analysis, plan + route_plan_check, arm A (~15 s of routing) |
| 16:28-16:32 | dangling-via diagnosis, arms B and C, force-reroute → first DONE |
| 16:33-16:36 | six post-DONE arms on pass 1, three in parallel |
| 16:37-16:39 | pass 2 place + judge + full route → DONE at 20 vias |
| 16:40-16:41 | pass 3 (rejected); three routing arms on pass 2 (rejected) |
| 16:42 | labels, silk grade, fill, delivered checks |
| 16:44-16:48 | verifier (one subagent, 1 call, ~4 min); grade.py, measure.py, TOOL_GAPS |

`measure.py --self --evidence wk/gpm/11_daplink` (`measure.txt`, taken at 16:48):
- wall clock 0:30:18: model 1271 s, tools 526 s, waiting on jobs 21 s;
- 174 tool calls, 143 of them Bash;
- most-used repo scripts: board_score 24, converge 20, route.py 19, check_weird 18;
- the verifier's transcript is not counted.

Placing and routing were cheap on this board (seconds per step). Most of the time went to reading, deciding and grading. About a third of the post-placement time went to the dangling-via defect.

## Tool gaps

Six entries in `TOOL_GAPS.md`, ranked by cost:
1. route.py's via-in-pad unblock (#535) leaves dangling vias that the #1166 sweep refuses to remove, so a blocking-0 board reads INCOMPLETE. The parent issue #1166 is closed; this variant is new.
2. At the board's own floors, route.py cannot route /OSCOUT, which check_reachability calls PASSABLE (caged only by routed copper). This held even after the rip hint and a force-reroute of its neighbours.
3. analyze_power_paths counts a part's current once per power pin, giving GND 2.0 mm on a ~300 mA board.
4. The routing skill's table says a higher `--via-cost` gives fewer vias. On this board via cost 75 / 150 / 300 gave 34 / 43 / 49 vias.
5. `converge.py verdict` says "only one of them carries a score" when every row carries one; in fact only one was accepted.
6. manifest_to_plan.py reads the plain redirects the skill prescribes as `--plane-layers` values, and reports a command that ran as "REJECTED".

Tools that said "fine" about something that was not:
- route.py's run summaries (`failed 0`, no dangling-via line) on boards that check_weird and KiCad flag for dangling vias (gap 1).
- `check_floorplan` prints `"pass": false` with 0 errors and 0 warnings, because the given intent leaves four rules owed. This is documented, not a defect.

## Verifier verdicts

One verifier, one call: **`verdict_1.txt` VERDICT=PASS**. `verdict_1_connectivity.txt`, `verdict_1_drc.txt` and `verdict_1_spec.txt` are all PASS.

It confirmed:
- the sha;
- buildable, floorplan 0 errors, no off-outline copper;
- P1 on the west edge facing out (its PCB-Edge line is on the outline), RST1 on the north edge;
- blocking 0, DONE, connected, DRC 0.

It also reported the UNSOUND floors above. For information only, it noted that the /D+ /D- pair runs 2.5 mm over a void in the plane below, with 2.30 mm skew; this is not graded because nothing declares a target.

## Files

All in `wk/gpm/11_daplink/`:

- **Boards:**
  - `delivered.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`, brief), `routed.kicad_pcb`, `labelled.kicad_pcb`;
  - `final.kicad_pcb` (kept placement, pass 2 s11), `fixed.kicad_pcb`;
  - the pass-1 placement in `old/pass1/final_pass1.kicad_pcb`.
- **Placement inputs and seeds:**
  - `groups.json`, `intent.json` (unchanged), `intent_run.json`, `CHOSEN.json`, `placed_from/`;
  - pass 2's seeds (`s<S>.*`, `s<S>_route/`, `s<S>_fast.*`), `judge.json`, `judge_chain.txt`.
- **Routing:**
  - the shipped chain: `final_route/`;
  - older routes: `final_route_old2/` (board-floors arm), `final_route_old3/` (no via-in-pad arm), `final_route_old4/` (pass-1 DONE chain);
  - experiment arms in `exp_*/` and `exp2_*/`.
- **Records:**
  - `ledger.jsonl` (37 rows, closed with `--final --stop-condition 1`);
  - `verdict_1*.txt`, `grade.txt`, `measure.txt`;
  - `TOOL_GAPS.md`, `repro/`, `STATE.md`.
- The datasheet folder was moved to `old/datasheets/`.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE.** The board passed the verifier.

- **Delivered board:** `wk/gpm/11_daplink/delivered.kicad_pcb`
- **sha256:** `0619d6fcca99d8aa4ba40e4be2f7402ba7770a77690c8f8d9523d7dbed6433d2`
- **Score:** blocking 0, joins_needed 0, 20 vias, 375.71 mm copper, 225 segments. `check_complete` says DONE and `verdict_1.txt` says PASS, with all three lenses PASS.
- **Catch: the board only grades clean at rules the run lowered itself.** The router's default escalation went below the board's own floors: vias 0.5 → 0.3 mm, annular ring 0.1 → 0.05 mm, clearance 0.2 → 0.1452 mm. `check_complete --authored-from` therefore reads UNSOUND (reported, not gating). Also, 10 of the 20 vias sit in pads and must be filled and capped (IPC-4761 Type VII). The arm that kept the board's own floors left /OSCOUT open.
- **Stop rule:** condition 1, DONE. After DONE I kept cutting vias until they plateaued: three placement passes (pass 2, `--crossing-weight 4`, took vias from 30 to 20) and about 13 routing arms. Nothing beat 20 vias.
- **Wall time:** 0:30:18 from FIRST_CMD (16:17:43Z) to 16:48Z, per `measure.py`.
- **TOOL_GAPS:** 6 entries. The top three:
  1. route.py's via-in-pad unblock (#535) leaves dangling vias that the #1166 end-of-run sweep refuses to remove, so a blocking-0 board reads INCOMPLETE. The fix every time was `--force-reroute` of the named nets. This is a new variant of closed #1166.
  2. At the board's own floors, route.py cannot route /OSCOUT, although `check_reachability` calls it PASSABLE (only routed copper cages it). The router's rip hint and a force-reroute of the neighbouring nets did not help.
  3. `analyze_power_paths` counts a part's current once per power pin, so it recommended GND 2.0 mm and +3.3V 1.0 mm on a board drawing about 300 mA. I used 0.7 mm for all three rails.

The harness refused to let me write REPORT.md ("Subagents should return findings as text"). So REPORT_DONE was not created, and the full REPORT.md content follows. One more thing the orchestrator should know: `docs/floorplan-intent.md` quotes this board's source edge bands. That is a leak of the source into tracked docs; it is under Disclosure in the report.
