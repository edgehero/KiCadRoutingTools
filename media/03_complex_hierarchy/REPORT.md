# REPORT — board 03 complex_hierarchy (`/plan-pcb-placement full`)

**DONE.** Delivered `wk/gpm/03_complex_hierarchy/delivered.kicad_pcb` (sha256 `d061e4dfd3e272aae820afa7a4644ebaad29fa3edf558feccdb9fcabc8daaff0`, with its `.kicad_pro`). The independent verifier passed it on its first call. Stop rule: **1, DONE**.

## 1. Result

| DONE condition (full mode) | measured on delivered.kicad_pcb |
|---|---|
| `board_score` blocking | **0** |
| unrouted | 0 |
| broken | 0 |
| `check_complete` | **DONE**; UNEXAMINED: diff_pairs, impedance, length (the board declares none of them) |
| `check_complete --authored-from <input>` | DONE, no floor listed |
| `check_assembly --baseline` | buildable (blocking 0) |
| `check_floorplan --intent` | 0 errors, 1 warning (template_ground_return, see §4) |
| `check_connected` | all nets fully connected |
| `check_drc --baseline --clearance-margin 0.1` | 0 violations |
| KiCad DRC (`tests/stress/kicad_drc_compare.py`, kicad-cli 10.0.7) | 0, CONSISTENT; connwidth 0, thermal 0 |

`blocking_by`: unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly 0, net_widths 0, drc_via_in_paste 0. diff_pairs, impedance and length are ungraded because no spec declares them.

| quality | value |
|---|---|
| vias | **0** |
| copper_mm | **710.64** |
| segments | **178** |

**Spec flag** used everywhere (board_score, check_complete, grade, verifier): `--net-min-widths net_min_widths.json`. It holds the board's own `power` net class track width, 0.6 mm, for that class's nets (-VAA, /12Vext, GND, HT, VCC).

Delivered widths:
- -VAA, /12Vext, HT and +12V at 0.6 mm; VCC at 0.7 mm.
- Signals at 0.4 mm (the Default class).
- GND has no track: all 26 GND pads are through-hole and sit in the B.Cu pour.

**Independent grade**: `scripts/grade.py delivered.kicad_pcb --baseline complex_hierarchy.kicad_pcb --intent intent_run.json --mode full --spec net-min-widths=net_min_widths.json` (output in `grade/grade_output.txt`):
`{"done": true, "blocking": 0, "unrouted": 0, "broken": 0, "drc": 0, "vias": 0, "copper_mm": 710.64, "segments": 178, "check_complete": "DONE", "check_complete_authored": "DONE", "assembly_verdict": "buildable (blocking 0)", "floorplan_errors": 0}`

**Timing**: `scripts/measure.py --self --evidence wk/gpm/03_complex_hierarchy` (output in `measure_output.txt`, exit 0).
- Wall clock at the moment of the call: 0:26:32. Model 1099 s, tools 448 s, waiting on jobs 45 s; 145 tool calls.
- It did not count the verifier subagent (`subagents` is `{}`). The verifier ran 158 s.

## 2. What was given, and what I added

- **Board:** 68 parts, all through-hole; 52 nets; 2 layers; a 100.7 x 80.0 mm rectangle. The parts start as a pile south of the outline. The designer's GND pour on B.Cu (thermal relief, clearance 0.508 mm) was kept.
- **mechanical.json:** Q304 at (129.794, 96.52), rot 0, which the intent carries in `fixed_poses[]`. It is delivered exactly there, on F.Cu.
- **Design brief:** no interfaces, no edges, no keep-outs.
- **EMC rows: none were given.** `board_context`'s `emc_roles` found no converter, crystal, oscillator or ESD part, so there is no `proximity` or `keep_away` row.
- **intent.json is untouched** (sha re-checked at the end). `intent_run.json` is `intent.json` plus one row:
  - `templates[U102]`, written by `fit_template.py --write-intent`: the ICL7660 charge pump (§4).
  - `waive_locked_overlaps.py` found 0 pairs (nothing is locked) and wrote nothing.
- **Skills followed BY HAND** (none can be invoked here):
  - `/plan-pcb-placement`: SKILL.md, verifier.md, part-roles.md, placement-lessons.md.
  - `/plan-pcb-routing` (§3.8): Step 0, Step 8's 2-layer through-hole arms, Step 9's plan and `route_plan_check.py`.
  - `/analyze-power-nets`, as plan-pcb-routing Step 4 asks.
  - The inline parts of `/find-high-speed-nets` and `/recommend-plane-mappings` that the routing skill delegates. A name and part scan found no high-speed, impedance or RF nets on this audio-band piezo driver. GND stays the one plane, on B.Cu, as the designer poured it.

## 3. The groups and every judgement call

`groups.json` has 6 groups. `check_groups`: 0 errors, 0 warnings, 11 bridges; its one template HINT (U102) is named as a candidate.

| group | parts | why |
|---|---|---|
| power_entry (edge N) | P101 C101 P102 D101 | both supply terminals: the HT entry with its 47uF/63V bulk cap, and the 12 V entry with its 1N4007 reverse-polarity diode |
| supplies | C104 U101 C102 U102 C105 C103 | +12V bulk cap at the 78L05; the 78L05 makes VCC (C102); the ICL7660 charge pump (flying cap C105, reservoir C103) makes -VAA |
| ch2_in (edge E) | P201 R201 C202 R202 C201 R203 C203 U201 RV201 R213 | input RC, Sallen-Key low-pass round U201B, error amp U201A, gain pot RV201 with R213 |
| ch2_out (edge E) | Q201-Q204 D201-D204 R204-R212 C204 P202 | HV push-pull output stage, compensation R211/C204, emitter resistors to PIEZO_OUT, R209/R210 feedback |
| ch3_in (edge W) | P301 … R313 | the same circuit, sheet ampli_ht_horizontal |
| ch3_out (edge W) | Q301-Q304 D301-D304 R304-R312 C304 P302 | the same; Q304 (declared pose) anchors it |

Judgement calls:
- **Each channel is split in two:** the op-amp and filter stage, and the HV output stage, rather than one 29-part group.
  - R209 and R210 go with the output stage, so both emitter nets stay inside the group and only S_OUT+ crosses.
  - R212 goes with Q204.
- **The power entry is a group of its own, separate from the regulators.** Both terminals are together on `edge N`. The regulators are `near` it with no edge, because placement-lessons says power conditioners sit by their entry, not on an edge.
- **The edges for the terminal groups (N, E, W) are my choice, not the user's.**
  - The brief declares no edge, and the terminal blocks do not classify as edge parts (TOOL_GAPS #4), so a group `edge` hint was the only lever.
  - Channel 3 got the west half because Q304 is declared at x 129.8, left of centre.
  - The hint prices only the group's nearest courtyard. On the shipped board P301 (W) and P202 (E) are at their edges and P201 is near the south-east edge, but P101, P102 and P302 sit mid-board.
- **Net-(U102-CAP+)/Net-(U102-CAP-) is not a differential pair**, although list_nets and board_context match it by name. These are the ICL7660's flying-cap pins, U102 to C105 on each net. They are routed single-ended, with no route_diff step (TOOL_GAPS #5).
- **No §4 `replicate`:**
  - In the best layout, channel 2's Q204 sits at 270°. Copying ch2 onto ch3 with Q304 as the anchor would turn the declared Q304 off its rot 0.
  - Copying ch3 onto ch2 would lengthen the board: in every seed measured, ch3 routes longer than ch2. Own copper per channel was s9 194 vs 316 mm, s1 226 vs 239 mm, s8 210 vs 256 mm.
- **The kept seed was chosen by its FULL route, over the judge's quick pick, twice** (TOOL_GAPS #1). Every judged seed was at blocking 0, so the choice came down to copper, and there the quick route ranked them wrongly.
- **Two half turns** that route_review named on the full route (two-pad parts turned against their wiring):
  - R302 on seed 9: -11.96 mm.
  - R307 on seed 18: -4.77 mm. This is the one shipped (`CHOSEN.json` `after`).

## 4. Datasheet template (§3.5)

- **U102, an ICL7660 charge-pump inverter.** It is a switching stage by the skill's list ("a charge pump").
- **Datasheet:** Renesas (Intersil) ICL7660/ICL7660A, **FN3072 Rev.7.00, Oct 5 2010**.
  - Sources used: Figure 13A "Simple negative converter" (the configuration) and Do's and Don'ts item 4 (polarity).
  - It has **no layout figure** and no distance guideline. Figure 13A names each cap's pins, so this is a template "from text" with no `side`s (§3.5 step 1).
- **Matched by net:**
  - C1 (10 µF pump cap) is **C105**: + on CAP+ (pin 2), - on CAP- (pin 4).
  - C2 (10 µF reservoir) is **C103**: across VOUT (pin 5) and GND (pin 3), + to GND.
  - The flying cap is listed first.
- **Fitted legs:**
  - C105: 3.77 + 3.77 mm.
  - C103: 5.08 + 5.59 mm. Listed first, C103's shortest is 5.46 + 2.73 mm: 2.5 mm more in sum, not "several mm past", so I kept the template.
- **Drift on the delivered board: 0.00 mm** for both members.
- **WARN `template_ground_return`:** C103 returns its ground 5.08 mm from U102's GND pin. C103 is a 17.5 mm axial electrolytic (15.00 mm pin pitch), and pin 4 sits between its pad and pin 3, so no pose of that body does better.
- **C102 is not a member.** It is the 47 µF VCC cap: the 78L05's output cap and the ICL7660's V+ bypass. Figure 13 draws no input cap.

## 5. Placement passes

| pass | inputs | seeds judged | result |
|---|---|---|---|
| 1 | default seeds 0-11 (6 scattered, 6 clustered); judging chain = arm A | 9 1 10 11 8 5, all quick blocking 0 | the judge kept s1 (2 vias); on full arm-B routes s9 was best, 740.56 mm |
| 2 | `--seeds 12-23 --clustered-seeds 18-23`; judging chain = arm B (the final chain) | 16 22 19 18 23 12, all quick blocking 0, 0 vias | the judge picked s23 (quick 701.45 mm, full 755.13 mm); on full routes **s18 was best, 715.41 mm** |

- All 24 seeds were legal, buildable and floorplan-clean.
- Pass 1's files are in `old/pass1/`. Pass 2's seeds, `judge.json`, `judge_chain.txt` and `placed_from/` (fixed.kicad_pcb with its .kicad_pro, groups.json, intent_run.json) are in the folder.
- `CHOSEN.json`: seed 18, clustered, pass 2, intent `intent_run.json`, place_args `["--seeds","12-23","--clustered-seeds","18-23"]`, after `place_pose final set R307 147.1849 81.0037 --rot 180`.
- The full routes of pass 2's six judged seeds ran in `explore/pass2/`, from the same inputs. Its s18 has the same sha as the main-folder run.

## 6. Routing (§3.8, /plan-pcb-routing by hand)

- **Step 0** on `final_route/in.kicad_pcb`: check_assembly buildable; the board_score baseline was 49 unrouted nets (87 joins).
- **What the board needs:** 2 layers and all through-hole, so no fanout. No diff pairs (§3). No impedance control (default stackup, and nothing to control). No high-speed nets, so **no GND return-via or stitch tail** (Step 10 rule 10).
- **Design rules:** Default class 0.3 mm clearance and 0.4 mm track; `power` class 0.6 mm track. Vias 0.889/0.508 mm, the board's min_via_diameter rather than the class's 1.651/0.6.
- **`/analyze-power-nets`:**
  - Classification (estimates are marked):
    - Sources: P101 (HT, estimate 50 mA), P102 (12 V, estimate 60 mA), the 78L05 (100 mA), the ICL7660 (20 mA).
    - Pass-through: D101; Q202/Q302 on HT (estimate 25 mA).
    - Sinks: the LM358s (5 mA); the piezo outputs (estimate 25 mA).
    - MPSA42/92 ratings (300 V, 0.5 A) are from distributor listings.
  - Its recommendation: GND 0.7 mm, VCC 0.7 mm; everything else is under 50 mA.
  - Widths used: GND 0.7, VCC 0.7; HT, -VAA, /12Vext and +12V 0.6 (the board's power class). +12V is not in that class, but it carries /12Vext's current; that is my judgement.
  - `-VAA` is passed as the glob `'?VAA'` (TOOL_GAPS #3).
- **Step 8 arms, on pass 1's kept seed:**
  - Arm A, the defaults (layer costs 1.0/3.0, via cost 75): 4 vias, 805.0 mm, 187 segments.
  - Arm B, `--layer-costs 1.0 1.0 --via-cost 600`: 0 vias, 783.78 mm, 171 segments.
  - Arm B became the chain. Both arms reached DONE.
- **The shipped chain** is `final_route/final_plan.sh` (`route_plan_check.py`: all 17 rules ok). It replays from `final_route/redo_commands.sh`; the GUI form is `final_route/final_plan.json`.
  1. `route_planes.py in s1_pour --nets GND --plane-layers B.Cu --skip-existing-zones` keeps the designer's thermal-relief pour.
  2. `route.py s1_pour s2_route --nets '*' --clearance-ceiling 0.3 --via-size 0.889 --via-drill 0.508 --power-nets GND VCC HT '?VAA' /12Vext +12V --power-nets-widths 0.7 0.7 0.6 0.6 0.6 0.6 --layer-costs 1.0 1.0 --via-cost 600`
- **Route results:** JSON_SUMMARY_MIN shows routed 49, failed 0, open_single [], multipoint_deficit 0, vias 0. JSON_ORACLE: KiCad reports all nets complete (0 rounds). check_orphan_stubs, check_weird and check_cycles are clean.
- **Earlier chains are kept:**
  - `final_route_old1/`: arm A on pass 1's seed 1 (the first routed board and the first DONE).
  - `final_route_armB/`: arm B on the same seed.
  - `final_route_old2/`: staged for pass 1's seed 1, never routed.

## 7. Stop rule and remaining blockers

**Stop rule 1, DONE:** blocking 0, check_complete DONE, verifier PASS. No blocker remains.

The first DONE came at 17:04 (4 vias, 805.0 mm). After it, four levers each improved the board:

| lever | result |
|---|---|
| arm B | 0 vias, 783.78 mm |
| keeping the seed by its full route | 740.56 mm |
| a half turn (R302) | 728.6 mm |
| pass 2 plus a half turn (R307) | 710.64 mm |

With vias at 0, only copper was left to optimise, and I stopped there.

## 8. Floors

None crossed.
- route.py's design_rules: count 0, escalations 0, fab tier escalations 0.
- Minimum clearance used: 0.3 mm (the board's Default class). Tracks 0.4/0.6/0.7 mm; no vias.
- `check_complete --authored-from <input>`: DONE, no floor listed.
- route_planes wrote `rules.min_copper_edge_clearance 0.01 -> 0.2` into the output project. That is the fab edge floor and a raise, not a descent.

## 9. Silkscreen (§3.9 step 1)

KiCad's silk classes, `routed.kicad_pcb` to `labelled.kicad_pcb` (beautify_labels placed all 68 labels):

| class | before | after |
|---|---|---|
| silk_overlap | 56 | 5 |
| silk_over_copper | 32 | 1 |
| silk_edge_clearance | 1 | 0 |
| **total** | **89** | **6** |

I kept `labelled.kicad_pcb`. The verifier lists the 6 that remain: the P201/RV201 refs, C201/R201, D303's K text on R311, D201's K text on R205, and D203's K text on R204.

## 10. Fill (§3.9 step 2)

`fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` ran (exit 0). It wrote 1 filled_polygon block and kept both net classes; KiCad's unconnected count without refill went from 25 to 0. The delivered board carries its fill.

## 11. Timeline (UTC) and where the time went

| time | step |
|---|---|
| 16:51:27 | FIRST_CMD |
| 16:52-16:58 | read the board (board_brief, board_context), wrote the groups, got the ICL7660 datasheet (download + PDF helper) |
| 16:59 | template fitted into intent_run.json |
| 17:00 | pass 1 placed (12 seeds, ~5 s each) |
| 17:02 | pass 1 judged (6 seeds, ~5 s each) |
| 17:04 | first routed board = **first DONE** (arm A, final_route_old1) |
| 17:05 | arm B: 0 vias |
| 17:06-17:07 | full routes of the other judged seeds; s9 + R302 turn |
| 17:09 | scratch pass 2 placed and full-routed; s18 + R307 turn |
| 17:11 | pass 2 placed and judged in the folder |
| 17:12 | final.kicad_pcb and the final_route chain |
| 17:13 | labels, fill, delivered.kicad_pcb |
| 17:15-17:18 | grade.py, the verifier (158 s), measure.py |

Most of the time went to reading the skills and the board: model time was 1099 s of 1592 s. Every tool is fast on this board (a placement seed ~5 s, a full route ~10 s with the KiCad oracle). The datasheet step cost about 5 minutes because this machine has no PDF tooling.

## 12. Tool gaps (detail in TOOL_GAPS.md)

1. `judge_seeds`' quick ranking was the inverse of the full route's on copper, in both passes. Behind it is a skill gap: the judging chain must be written before plan-pcb-routing's two-arm comparison exists.
2. No PDF reader for §3.5 (no poppler, PyMuPDF or pypdf). I wrote `helpers/pdfpages.swift`.
3. `-VAA` (a dash-then-letter net name) breaks route.py's argument parsing; #597 fixed only dash-then-digit names.
4. The Altech AK300 screw terminal blocks are unclassified, so nothing can hold them to an edge.
5. A charge pump's CAP+/CAP- nets are detected as a differential pair.
6. check_floorplan exits 4 on a 0-error placement when the given intent withholds budgets.
7. The harness refused the REPORT.md write.

Helpers written (`helpers/`):
- `pdfpages.swift` (gap 2).
- `full_route_armB.sh` (gap 1): no repo tool runs the full chain over a list of placements.

No tool said "fine" about a defect on this board. The judge's "best seed" was the only claim that did not hold up.

## 13. Verifier verdicts

**verdict_1.txt: `VERDICT=PASS`.** Lenses: connectivity PASS, drc PASS, spec PASS. One verifier call of the three allowed was used.

It measured:
- sha256 matching the claim.
- buildable.
- 0 floorplan errors (its exit 4 means "not fully graded", as in TOOL_GAPS #6).
- no off-outline copper.
- Q304 exactly at its declared pose.
- blocking 0 and DONE.
- all nets connected.
- 0 DRC violations, also with `--check-pad-edge`. A kicad-cli refill DRC found 0 copper violations and 0 unconnected items.
- power widths of at least 0.6 mm.
- diff_pairs, impedance and length UNEXAMINED, and not declared by the board.

## 14. Ledger

`ledger.jsonl` has 33 rows:
- the first legal placement;
- all 12 judged seeds from the two passes;
- every further fully routed board (`--kind completion`, rejected ones marked);
- the kept placement;
- the first DONE;
- the delivered board;
- the closing `--final --stop-condition 1` row, with the three lens files.

The datasheet folder was moved to `old/datasheets/`; I ran no `rm -r`, so the orchestrator deletes it.

---

## The teammate's final summary (saved with the report by the orchestrator)

**DONE.** The board is placed, routed and filled, and the independent verifier passed it on its first call. REPORT.md could not be written: the harness refused the write ("Subagents should return findings as text"). So, as TASK.md says, I did not create REPORT_DONE, and the full REPORT.md is below for the orchestrator to save.

- **Delivered board:** `wk/gpm/03_complex_hierarchy/delivered.kicad_pcb`, sha256 `d061e4dfd3e272aae820afa7a4644ebaad29fa3edf558feccdb9fcabc8daaff0` (also in `DELIVERED.sha256` and `DONE`).
- **Score:** blocking 0, joins_needed 0, vias 0, copper_mm 710.64, segments 178.
- **Stop rule:** 1, DONE.
- **Wall time from FIRST_CMD:** 0:28:18 (16:51:27Z to 17:19:45Z).
- **TOOL_GAPS.md:** 7 entries. The top three:
  1. `judge_seeds`' quick route ranked the seeds the wrong way round on copper in both passes. I kept the seed whose full route used least copper; the judge's pick would have shipped 44–73 mm more.
  2. This machine has no PDF tools (poppler, PyMuPDF, pypdf), so the Read tool cannot open datasheets. I wrote `helpers/pdfpages.swift` to read the ICL7660 datasheet.
  3. The net name `-VAA` breaks `route.py`'s argument parsing. Issue #597 fixed only names like `-3V3`; I passed it as the glob `'?VAA'`.
