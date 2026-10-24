# gpm findings, clustered (all 20 boards; interf_u folded in at the end)

**gpm findings: cross-board defect clusters (19 of 20 boards; 05_interf_u still running, it has no TOOL_GAPS.md yet)**

Sources: 19 TOOL_GAPS.md files, the "said fine" lists in the REPORT.md files, FINDINGS_PREP.md (#1-#8), GRADE_NOTES.md, and OLD_ISSUES.md / B1-B8. Every repro was checked to exist on disk. Nothing was re-run. The only extra check was a grep confirming the named code locations (for example board_score.py:1357, check_complete.py:583, analyze_power_paths.py:303 and 418-439, edge_seat.py:482).

**Common setup for every repro:**
```
cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH"; B=wk/gpm; T=$(mktemp -d)
KC=/Applications/KiCad/KiCad.app/Contents/MacOS   # prepend to PATH wherever kicad-cli or kicad_drc_compare is used
```
"verbatim NN §k" means: copy the command from that board's TOOL_GAPS entry k.

## Cluster table

| ID | Title | Kind | Boards | Sev | Upstream |
|---|---|---|---|---|---|
| G01 | fill_for_delivery's KiCad 10 re-save turns accepted via-in-pad into blocking violations | false-OK | 04,07,10,13,14,15,17,19 | high | new (#1335, #992, #749 related) |
| G02 | route.py ships dead-end stubs, dangling vias and loops that check_weird flags; no CLI removes them | bug / missing-tool | 07,08,10,11,12,13,14,15,19,20 | high | #1166, #84, #1063 (closed); #1234 (open); #162 (state disputed) |
| G03 | analyze_power_paths adds a part's current once per power pin, and a source's rating on top | bug (silently wrong) | 06,08,09,11,12,13,17 | high | new |
| G04 | Default fab escalation goes below Board Setup minimums, rewrites them, and bare graders then say DONE | false-OK | 04,11,16 (+10 boards authored UNSOUND) | high | new (#857, #1287, #1170, #1160; #502 open) |
| G05 | place_simple leaves error-graded decap near-misses in every seed; no repair tool | bug | 06,09,10,12,13 | high | new (#1296, #1320, #1267 related) |
| G06 | route.py cages pads with its own copper; the rescue never tries the levers that work; hints misdirect | bug | 04,06,11,13,20 | high | new (#1348 same shape, route_bus) |
| G07 | analyze_power_paths ignores the classification and traces only pintyped pins | bug (silently wrong) | 01,07,09,15,19,20 | high | new |
| G08 | Named diff pairs are measured, not graded, so DONE ships an uncoupled DDR strobe | false-OK | 08,12,14 | high | related #1303 (PARTLY), #1134 |
| G09 | Quick judge mis-ranks seeds against full routes; judge chain carries one arm where the skill prescribes two | bug / skill-text | 01,03,04,12 (+07) | med-high | new |
| G10 | Bodies drawn only on silk never gate (parts inside a battery holder, under modules) | false-OK | 07,08 | high | new (#1250, #896, #916, #1300) |
| G11 | An outline split into separate regions (mouse bites, snap-offs) is invisible to placement and check_reachability | false-OK | 15,19 | high | new (#628 related) |
| G12 | Overhang band is read as a sum over crossed sides/corners; the footprint's "PCB Edge" marker is unread | false-OK | 02,12 | high | new (#1155, #1301, #987, #961) |
| G13 | Requested power widths not delivered (pad necks, bulk at signal width) | bug | 06,09,12,18 | high | same as #1318 (re-verified PARTLY); #1033 |
| G14 | Requested power widths reach no DONE grader; the skills disagree | skill-text / false-OK | 09,12,18 | med-high | new |
| G15 | Impedance declarations never held to Z0 and not auto-read; route.py ships half the solved width | false-OK | 18,20 | high | new (#964 class) |
| G16 | Courtyard-conditioned .kicad_dru rules invisible to router, check_drc and kicad_drc_compare | false-OK | 20 | high | new (#447 unrelated) |
| G17 | Classless edge_connectors row: dropped by the seat, graded ERROR by check_floorplan | bug | 08,09,16 | med-high | new (#1331 fixed the declared-class half) |
| G18 | Exact-name --rip-existing-nets override honoured in the main pass only, not in the plane finalize | bug | 13 | high | new (#677, #521) |
| G19 | Writeback lowers project floors when no copper needs it | bug | 10,12,14,17 | med-high | regression-of #1319 (uncovered paths); #1285, #1198, #900 |
| G20 | Edge exemptions (#408, pad-edge off by default) hide KiCad copper_edge_clearance errors on moved copper | false-OK | 08,17 | med-high | #408, #438 |
| G21 | Router cannot aim at a .kicad_dru length window; the match target and report are wrong | missing-tool / bug | 14 | high | #1363 (open, bus half); #1313 (PARTLY) |
| G22 | B-side parts in a BGA escape field, so fanout vias land in their pads (contact) | bug | 14 | high | same as #1343 (re-verified STILL BROKEN) |
| G23 | check_weird misreads overlap-only joints (soft joint reads "dangling"; a 0.04 mm edge overlap reads "connected") | bug / false-OK | 07,08,09,13,16 | med-high | new (#722, #695, #984) |
| G24 | DENSE layer prices let signals onto GND reference planes | skill-text | 08,10,20 | med-high | same as #1359 (re-verified PARTLY) |
| G25 | route.py's end-of-run verdict disagrees with authoritative connectivity (GND credited; oracle "confirmed" an island) | false-OK | 09,12 | med-high | regression-of #1339 |
| G26 | route.py writes a different-net crossing short and reports failed 0 | bug | 20 | high | new (#169, #673, #1260; #1310 is a different producer) |
| G27 | --escalation board writes vias whose diameter is below their drill; check_drc clean | false-OK | 07 | med-high | same as #1349 (re-verified PARTLY) |
| G28 | check_complete --authored-from omits lowered clearances and min_hole_clearance | false-OK | 10,12 | medium | new (#1198, #900) |
| G29 | Courtyard overlaps KiCad grades error are advisory; place_pose --near snaps into courtyards | false-OK | 06,14 | medium | #1095 (closed) |
| G30 | KiCad track_dangling on delivered boards that check_weird / check_orphan_stubs call clean | false-OK | 10,20 (lead prep #7) | medium | new (#1291, #1217) |
| G31 | Redundant loops invisible to DONE (check_complete does not run check_cycles) | false-OK | 04,16,17 | medium | new (#162, #444) |
| G32 | place_simple parks parts inside a fixed part's pad copper that reaches past its courtyard | bug | 18 | med-high | new |
| G33 | analyze_power_paths keeps one sink per rail (sink_nets dict) | bug | 02,16 | medium | new |
| G34 | analyze_power_paths traces backward through regulators and sums overlapping paths | bug | 08,10,13,14,17 | medium | new |
| G35 | design_rules disclosure does not match the shipped copper | false-OK | 15,16,18 | medium | new (#1160, #857) |
| G36 | Edge facing abstains silently, so a side-push switch facing along its edge passes | false-OK | 20 | med-high | new |
| G37 | "fanout-dropped ball, re-run the fanout" hint after route.py itself stripped the escape | bug | 08,20 | medium | same as #1311 (re-verified PARTLY) |
| G38 | Routed diff pairs wall in later nets and plane balls | bug | 13,14 | med-high | #677 (open) |
| G39 | REDO manifest misses kicad-cli upgrade, check_join and hand removals | bug | 04,14,19 | medium | new |
| G40 | Judge key ignores template members left 6-24 mm off | bug / skill-text | 08,18 | medium | new |
| G41 | Same-number MP tabs: KiCad says unconnected, the repo says connected | false-OK | 17 | medium | new |
| G42 | route.py not run-to-run deterministic (Step 2c env stack; plane finalize) | bug | 17,20 | medium | new (#490) |
| G43 | One-cap supply pin's decap limit priced flat | bug | 14 | medium | same as #1320 (re-verified STILL BROKEN) |
| G44 | board_score / check_complete keep only the last --impedance-nets | false-OK | 18 | medium | new |
| G45 | route_diff cannot re-route a connected pair; skill Step 2d names a flag route_diff lacks | missing-tool / skill-text | 08,14 | medium | #515 (route.py only), #677 |
| E01-E05 | Environment (see the env section at the end) | env | — | — | — |

## Sections

### G01 fill_for_delivery's KiCad 10 re-save (false-OK)
- **Claim.** pcbnew re-saves a pre-10 routed board as version 20260206 and writes an explicit `(capping no) (covering …) (plugging …) (filling no)` on every via. Vias that check_drc accepted as "undeclarable in this file format" become "unprotected (violations)". The tool exits 0 and says nothing.
- **The repo's own stamper cannot undo it.** `fab_notes.via_protection_stamps` keeps any spec that names capping/filling: 19 measured ship_via_protection_file stamping 0 of 88. `kicad-cli pcb upgrade` writes the same tokens (19).
- **Blocking 0 → N per board:**
  - 04: 20
  - 07: 4
  - 10: 356 (KiCad 8 input)
  - 13: 113 (all 368 vias tokened; blocking 3 → 116)
  - 14: 212, and 194 again on DONE #2
  - 15: 52 (verifier call 1 FAIL)
  - 17: 68
  - 19: 69 (256 vias)
- **Workarounds used.**
  - Upgrade-first chain (04, 10, 15, 17, 19). This changes routing: 19 went from 256 vias DONE to 249 with /P1A7 broken; 04 went from 47 to 42 vias.
  - A post-fill restamp helper (07, 13, 14).
- **Side finding (10).** board_score without `--baseline` does not arm the via-in-paste grade at all.
- **Repro:**
  ```
  R=$B/04_multichannel_mixer
  python3 -X utf8 py_tools/board_score.py $R/repro/gap1_routed_v9.kicad_pcb --baseline $R/multichannel_mixer.kicad_pcb --quiet   # BLOCKING=0
  python3 -X utf8 py_tools/fill_for_delivery.py $R/repro/gap1_routed_v9.kicad_pcb -o $T/g01.kicad_pcb; head -c 40 $T/g01.kicad_pcb
  python3 -X utf8 py_tools/board_score.py $T/g01.kicad_pcb --baseline $R/multichannel_mixer.kicad_pcb --quiet   # BLOCKING=20 drc_via_in_paste=20
  ```
- **Code.** `py_tools/fill_for_delivery.py` (SaveBoard); `fab_notes.via_protection_stamps` / `ship_via_protection_file`; route.py counts these vias `unstampable` on pre-10 files.
- **Fix.**
  - Strip pcbnew's setup-equal protection tokens back to inherit, as 13's and 14's helpers did, or keep the input's format.
  - Then run `ship_via_protection_file` with the input's via snapshot.
  - Print the version change, and gate: board_score on the filled copy must equal board_score on its input.
  - Say all of this in SKILL §3.9 and plan-pcb-routing 4d.

### G02 route.py ships dead or redundant copper that nothing removes
- **Claim.** The end-of-run cleanup (strict collapse, #1166 sweep, dead-end prune, prune_redundant_cycles) leaves stubs, dangling vias and loops that check_weird flags, so check_complete says INCOMPLETE on blocking-0 boards.
  - `--rip-existing-nets` is a no-op on a connected net.
  - `--force-reroute` skips zone-owning nets, and can recreate the defect.
  - No CLI deletes copper. Six teammates wrote a drop/prune helper (07, 08, 14, 15, 19, 20).
- **Per board:**
  - 07: USB_D+ dead-end spur in both tries. 3 loops plus a 2.1 mm free end, removed only by a second identical route.py, so the cleanup does not reach a fixpoint.
  - 08: a 0.25 mm In2 tail on protected DPHY0_P.D2_P survives every pass.
  - 10: /VCCPLL0 1.15 mm stub; only `--force-reroute` cleared it.
  - 11: 4 dangling vias from the #535 via-in-pad unblock. Each via is the only join of two F.Cu ends 0.07 mm apart inside its barrel; the sweep removes the via, sees 2 new dangling ends, and its gate refuses.
  - 12: a +1V8 loop on 4 of 5 recipe variants.
  - 13: 11 findings shipped.
  - 14: 1.27 mm +3V3 stub, 4.96 mm VMEM tail, 7 pad-internal stubs, a dangling DQ1 via.
  - 15: 7 of 12 arms INCOMPLETE; force-reroute recreated the 5v loop 0.25 mm away.
  - 19: 4 dangling +3V3 branches (16 segments) on a poured net.
  - 20: GND stubs in the 1 mm gap between hatched zones; the fill model credits the zone edge.
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $B/11_daplink/repro/gap1_s1_diff.kicad_pcb $T/g02.kicad_pcb --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0
  python3 -X utf8 py_router/check_weird.py $T/g02.kicad_pcb   # 4 x dangling via
  ```
- **Code.** `sweep_dangling_via_branches` gate (11); force-reroute's zone-owner skip (15, 19, 20); `py_router/cleanup_pipeline.py` has no CLI.
- **Fix.**
  - Iterate the cleanup to a fixpoint.
  - When removing a via exposes two ends that met inside its barrel, join them instead of refusing.
  - Prune poured-net stubs against the exact fill.
  - Ship a recorded CLI that deletes named or flagged copper and re-verifies connectivity.

### G03 analyze_power_paths: once per pin, plus the source on top
- **Claim.** `get_power_net_recommendations` (analyze_power_paths.py:418-439) adds `current_rating_ma` for every power pad of a part, then adds each source's rating on top of the sinks it feeds.
- **Per board:**
  - 06: U6's ten +3V3 pins give 1.5 A; VREG_AVDD (~200 µA) gets 150 mA and 0.7 mm; GND 3.0 mm.
  - 08: Module301's +1V8 / GPIO_VREF / +3V3_PI pins inherit 3 A, giving 2.0-3.0 mm.
  - 09: 7 VCC33 pins × 167 mA = 1169 mA on a 100 mA rail, giving 1.2 mm.
  - 11: STM32 50 mA × 5 pins; P1 500 mA × 8 GND/shield pads = 4 A, so GND 2.0 mm on a ~300 mA board.
  - 12: FT2232HL 70 mA × 19 pins = 1330 mA.
  - 13: one sink counted once per path (5 / 5 / 15 paths).
  - 17: GND 2.0, +3V3 1.0 on ~187 mA.
- **Repro:**
  ```
  python3 -X utf8 -c "import sys;sys.path[:0]=['py_tools','py_router'];from analyze_power_paths import *;c,p=analyze_pcb('$B/11_daplink/repro/gap2_pile.kicad_pcb');classify_component(c,'P1',ComponentRole.POWER_SOURCE,current_rating_ma=500);classify_component(c,'U1',ComponentRole.POWER_SOURCE,current_rating_ma=300);classify_component(c,'U2',ComponentRole.CURRENT_SINK,current_rating_ma=50);print(get_power_net_recommendations(p,c,trace_power_paths(p,c)))"   # GND 2.0, +3.3V 1.0
  ```
- **Fix.** Charge each part once per net; ground return = the sum of sinks, once; never add a source's rating to the sinks it feeds. Add a multi-pin IC test.

### G04 Fab escalation below Board Setup minimums, graded DONE (false-OK)
- **Claim.** The defaults `--fab-tier auto --escalation fab` descend below the board's Board Setup minimums, and the writeback lowers those minimums. Bare board_score / check_complete then read the rewritten project and say DONE; only `--authored-from` (report-only) says UNSOUND.
- **Skill gap.** SKILL §1 says to grade "with every spec the board declares", but never says that Board Setup minimums are that declaration.
- **Per board:**
  - 04: 9 GND oracle vias at 0.45/0.2 on a min_via_diameter 1.5 board. Writeback 1.5 → 0.45, annular 0.3 → 0.125, hole 0.3 → 0.2. At the declared floors: blocking 18. One false DONE ledger row.
  - 16: two IO0 vias at 0.25/0.15 against a 0.4/0.2 minimum (undersized 4). `--fab-tier standard` routed blocking 0 with 83 vias, so the escalation was not needed.
  - 11: the only DONE board relies on it (vias 0.5 → 0.3/0.2, clearance 0.2 → 0.1452).
  - Grade notes: authored UNSOUND also on 06, 07, 09, 10, 13, 15, 17, 18, 19, 20.
- **Repro:**
  ```
  R=$B/16_esp_rust_board/repro
  python3 -X utf8 py_router/route.py $R/s8_diff.kicad_pcb $T/g04.kicad_pcb --nets '*' --track-width 0.127 --clearance-ceiling 0.127 --via-size 0.45 --via-drill 0.2 --power-nets +3V3 /Buck_Coil +5V VBUS 'Net-(D6-Pad2)' +BATT GND 'Net-(J1-PadS1)' --power-nets-widths 1.0 1.0 1.0 0.7 1.2 0.7 0.5 0.5 --layer-costs 1.0 1.0 --via-cost 150
  python3 -X utf8 py_tools/board_score.py $T/g04.kicad_pcb --quiet                                                  # clean
  python3 -X utf8 py_tools/board_score.py $T/g04.kicad_pcb --min-via-diameter 0.4 --min-via-drill 0.2 --min-track-width 0.127 --quiet   # undersized=4
  ```
- **Fix.**
  - Graders default to the authored floors (`fab_floor_origin` or the baseline project).
  - The router tries the board's own tier before escalating.
  - The skill says Board Setup minimums are the spec flags.

### G05 Decap near-misses in every seed
- **Claim.** place_simple prints "decap limits priced: N terms", but every seed ends with error-graded decap findings, mostly 0.01-0.4 mm past the limit. No tool repairs them (#1188's `--repair-decaps` is gone), and §3.6 case 2 collapses the judge to one hand-repaired seed.
- **Per board:**
  - 06: 12/12 seeds, 1-7 errors each (C18 1.3103 against 1.3073). 7 hand moves: 2 refused, 2 created COURTYARD-BLOCKING pairs.
  - 09: 24/24 seeds, at default weight and at `--decap-limit-weight 40` (1.81 against 1.77; 4.36-4.91 against 4.31). Only adding `--near-weight 10` gave 2 clean seeds.
  - 10: 12/12 seeds, 3-14 errors; at weight 50 still 1-6 (C92 4.86 against 4.79).
  - 13: 12/12 seeds, 3-19 errors. The judge then ranks by error count, so the anneal's cheapest seed (s4) was never judged.
  - 12: 3 of 6 judged seeds (grade notes).
- **Code (named by 10).** The final legalisation (overlap lambda ramped to 10^4) pushes caps past the limits that were priced.
- **Repro:**
  ```
  R=$B/10_glasgow_revC/repro; python3 -X utf8 py_placer/place_simple.py $R/fixed.kicad_pcb $T/s5.kicad_pcb --groups $R/groups.json --intent $R/intent_run.json --decap-limit-weight 50 --seed 5 --json $T/s5.json   # "1 floorplan error(s) (decap_distance)"
  ```
- **Fix.** A constrained post-legalisation repair: move each broken cap to the nearest legal pose inside its limit, or hold the limits hard in the last stage. Show residual decap errors in the seed summary.

### G06 route.py cages pads with its own copper
- **Claim.** Nets fail "Boxed in / no rippable blockers" where check_reachability says PASSABLE on the placement and CAGED only with the routing in place. The in-run rescue never tries the levers that actually work.
- **Per board:**
  - 04: each TL072's GND pin 4 sits between two vbias pins. PASSABLE (bottleneck 6.0 mm), then CAGED by the run's own vbias via and IC2A-OUT track. 7 strict arms left 1-4 GND joins; `--rip-existing-nets` restored the original copper; only `--force-reroute` of the cage nets closed it, on some seeds. About 25 route runs and 2 changes of the kept seed.
  - 06: STATUS boxed at grid 0.1. A scoped grid-0.05 lap routed it in about 6 s. The hint suggested a WIDER clearance and track than the run's own.
  - 11: /OSCOUT at board floors (margin +173 µm) stays open even after the hint's rips and a force-reroute of 4 neighbours.
  - 13: 3 nets ship open, each PASSABLE then CAGED. The board is NOT DONE.
  - 20: U1.C13 is CAGED after the first route step ripped ddr-d11.
- **Repro.** Verbatim 06 §2 (two route.py runs on `$B/06_rp2350_fpga_eensy_prePlane/repro/status_s4_diff.kicad_pcb`): the first leaves `failed_single ["/RP2354A/FPGA.~{STATUS}"]`; the `--grid-step 0.05` lap gives `failed 0`.
- **Fix.** For a CAGED-by-routing failure: rip and re-route the cage nets, and retry the scoped net at a finer grid at the run's own clearance. The hint should name the cage nets and never suggest a wider clearance.

### G07 analyze_power_paths: classification ignored, only pintypes traced
- **Claim.** `trace_power_paths` builds sinks only from `power_in` pins and sources only from `power_out` / OUT-named pins; `is_power_pin` drops `passive`. The classified roles never reach a net, and there is no warning.
- **Per board:**
  - 01: the ECC83 heater (300 mA on Net-(P4-P1) / Net-(P4-PM)) is missing; the only recommendation is {GND 0.7}.
  - 07: easyeda pins, 0 paths; only GND and PGND at 3.0 mm.
  - 09: passive JST VBUS pins add nothing; J1 → JP1 → U2 not traced.
  - 15: the 30 A J1 → R11 → BAT+ → shunt → VDD → FETs → phases path is not traced (VDD 0.7, phases none).
  - 19: 0 paths; the isolated /ET_GND and /EB_GND sized 1.0 mm from the board's 609 mA total.
  - 20: 0 paths; VIN and VBUS absent.
- **Repro.** `python3 -X utf8 $B/01_ecc83-pp_v2/repro/analyze_power_heater.py`
- **Fix.** A classified part's supply-net pads become sink/source pins whatever their pintype; trace through PASS_THROUGH parts; warn when a classified part contributes no path.

### G08 Named diff pairs measured, not graded (false-OK)
- **Claim.** board_score's diff_pairs component grades only `.kicad_dru` skew / uncoupled rules ("measured, not graded"), and check_complete lists it UNEXAMINED. Verifier rule 5 FAILs any declared class left ungraded, and neither skill says to write a rule.
- **Per board:**
  - 14: DONE #1 had DQS1 coupled 0.00 of 25.10 mm with 15.467 mm skew, and CLK0 3.13 of 42.19 mm with 4.242 mm skew. The board's one pair rule names a netclass the project lacks. Verifier FAIL; about 40 min.
  - 08: 100/90 Ω classes and no `.kicad_dru`. Verifier FAIL (13 of 18 pairs over 0.5 mm skew, worst 5.213 mm). A hand-written 0.15 mm rule plus `--diff-pair-intra-match` left every pair unmatched ("No suitable straight run").
  - 12: the USB pair shipped uncoupled and ungraded.
- **Repro:**
  ```
  R=$B/14_imx6ulz_4l; python3 -X utf8 py_tools/board_score.py $R/repro/done1_delivered.kicad_pcb --intent $R/intent_run.json --baseline $R/repro/pile.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25 --quiet
  python3 -X utf8 check_complete.py $R/repro/done1_delivered.kicad_pcb --min-track-width 0.1 --min-via-diameter 0.45 --min-via-drill 0.25   # DONE
  ```
- **Fix.** Grade a minimum coupled share and P/N skew for every pair the board names (a diff netclass, or a route_diff-protected pair), or have the skills write the rule. verifier.md and board_score must agree on what is graded.

### G09 Quick judge mis-ranks seeds against full routes
- **Claim.** The `--quick 2` judge_key ranks noise when every seed is DONE-class. It is blind to the plane finalize and to spec floors. And plan-pcb-routing Step 8 prescribes two arms for 2-layer THT while §3.7 says to judge with "the board's routing chain".
- **Per board:**
  - 01: judged with arm A, best s9. In full arm-B routes s1 is 105.52 mm and s9 is 122.01 mm (+16.5 mm). Re-judging with arm B names s1.
  - 03: pass 1, s1 783.78 vs s9 740.56 mm; pass 2, s23 755.13 vs s18 715.41 mm. Quick-vs-full copper moves −2% to +8% per seed, more than the spread between the top seeds.
  - 04: the judge's best (s11) never closed GND at the board's floors; s10 reached DONE at 42 vias.
  - 12: the judge's best was s1; in full routes s2 was 142 vias DONE, s1 147, s3 blocking 1.
  - 07: the run kept s8 over the judge's s4 (grade notes; no reason given).
- **Repro:**
  ```
  R=$B/01_ecc83-pp_v2
  KICAD_ROUTE_TRACE=1 python3 -X utf8 py_placer/judge_seeds.py $R/repro/judge3/judge.json --chain $R/repro/judge3/chain_armA.txt --intent $R/intent_run.json --jobs 3   # best seed 9
  KICAD_ROUTE_TRACE=1 python3 -X utf8 py_placer/judge_seeds.py $R/repro/judge3b/judge.json --chain $R/repro/judge3b/chain_armB.txt --intent $R/intent_run.json --jobs 3 # best seed 1
  ```
- **Fix.**
  - Judge with the shipped arm, or with each prescribed arm.
  - When the top quick scores are within the quick/full spread, full-route the top k.
  - The judging chain counts poured joins and runs at the declared floors.

### G10 Silk-drawn bodies never gate (false-OK)
- **Claim.** Courtyard-less parts drawn only on silk/fab are `gate_exempt: silk_drawn`, so even 100% containment is advisory.
- **07.** 197 of 204 footprints have no courtyard. Solarpower1 sat 100% inside BAT1's 77.6 × 56.8 mm holder; PWR_SW1's actuator and NTC1 were under it; DC1 sat over I2C2 (4.83 mm², `waived:edge_class`); U3, R5 and R63 were 0.5-0.76 mm under the ESP32 module. Verifier FAIL; 14 parts hand-repaired and a full re-route.
- **08.** CN1 sat under the CM5 module (`pads_under_body … advisory`).
- **Repro:**
  ```
  R=$B/07_One-Air-Max; python3 -X utf8 py_tools/check_assembly.py $R/repro/silk_body_inside.kicad_pcb --intent $R/repro/silk_body_inside.intent.json --baseline $R/fixed.kicad_pcb
  python3 -X utf8 $R/helpers/body_overlaps.py $R/repro/silk_body_inside.kicad_pcb
  ```
- **Fix.** Estimate a body from the largest closed silk/fab outline (as #1300 does for fab bodies) and gate another part's pads inside it.

### G11 Electrically separate outline regions (false-OK)
- **Claim.** Placement legality, check_assembly, check_floorplan, board_brief and check_reachability do not model mouse-bite rows or snap-off tabs.
- **15.** The mouse-bite webs (0.2-0.4 mm) are under twice the 0.2 mm edge clearance, so no copper can cross. With R26 placed on the island: place_pose no_worse, buildable, 0 floorplan errors, check_reachability "PASSABLE, bottleneck ≥ 69.21 mm"; route.py then fails CAN_SILENT.
- **19.** The outline is 4 regions. Pass-1 seeds put 10-51 parts per seed in regions their nets cannot reach; every seed graded buildable with 0 errors. 4 passes, about 40 min.
- **Repro:**
  ```
  R=$B/15_am32_esc/repro; python3 -X utf8 py_tools/check_reachability.py $R/s8_island_north.kicad_pcb --pad R26.2
  python3 -X utf8 py_router/route.py $R/s8_island_north.kicad_pcb $T/g11.kicad_pcb --nets CAN_SILENT   # ROUTE FAILED
  ```
- **Fix.** Derive copper-connectable regions from Edge.Cuts plus NPTH rows at the hole/edge clearances; check_reachability honours Edge.Cuts; placement keeps groups in their nets' region; add a skill step for panelised outlines.

### G12 Overhang band reading (false-OK)
- **Claim.** The band is read as the courtyard's outside amount summed over every side and corner it crosses (`legacy_occupancy` / `rect_outside_amount`), not as the distance past the mating edge. The footprint's "PCB Edge" marker is never read, and SKILL §3.4's "an overhang of x reads x" is false.
- **02.**
  - J2 was seated with its pad copper 5.30 mm inside the outline: pass.
  - J1's correct seat reads 25.12 = 14.20 + 10.92.
  - Following the skill literally (min 14.2) seats J1's pads 2.51 mm inside: pass.
- **12.** On the rounded outline J1 reads 2.5149 = 3 × 0.838: pass. The body was actually 0.338 mm past the edge, 2.2 mm too deep. At the drawing's pose it reads 9.15 and fails. Verifier FAIL, every route redone.
- **Repro:**
  ```
  R=$B/12_steppenprobe/repro; python3 -X utf8 py_tools/check_floorplan.py $R/seed2_placed.kicad_pcb --intent $R/intent_run_J1band.json | grep "J1 north: overhang"   # 2.5149 pass
  python3 -X utf8 py_tools/check_floorplan.py $R/seed2_J1moved.kicad_pcb --intent $R/intent_run_J1band.json | grep "J1 north: overhang"  # 9.15 fail
  ```
- **Fix.** One signed distance past the nearest edge along the mating normal; read the marker when present; fix the §3.4 text.

### G13 Power widths not delivered (same as #1318, re-verified PARTLY; plus #1033)
- **New boards:**
  - 12: every `--escalation board` route necks power to the 0.15 floor at pads and finalize straps (4-6 nets fail). `--escalation off` left GND taps at U1.15/25/35/51 unconnected, while check_join grades a 1.2 mm stub plus via CLEAN: the tap search failed, not the geometry. It took 14 arms.
  - 18: Net-(F1-Pad1) is 31.34 of 42.11 mm under 0.7 mm (74% at 0.127), which is #1033's bulk-route symptom.
  - 06: 8 rails necked to 0.0762-0.35 mm (REPORT).
  - 09: VBUS about 30 mm at 0.1 mm (grade notes).
- **Repro.** Verbatim 12 §3, first command ("Pads still unconnected: U1.15 … U1.51"), then its check_join command (CLEAN).
- **Fix.** The #1318 draft; the bulk route honours `--power-nets-widths`; the tap search tries the stub-plus-via join that check_join accepts.

### G14 Requested power widths reach no grader
- **Claim.** `net_widths` is UNGRADED unless a `--net-min-widths` file is passed. SKILL §1 passes it only when "the board declares" one, plan-pcb-routing Step 4 calls net-class widths "not DRC floors", yet the verifier FAILs an ungraded power class.
- **Per board:** 12 (verifier FAIL D3); 18 (verifier FAIL, 7 nets under width; the spec was re-declared from IPC-2221); 09 (grade notes).
- **Repro.** `python3 -X utf8 py_tools/board_score.py $B/18_uecg/repro/delivered_copy.kicad_pcb --net-min-widths $B/18_uecg/power_widths.json --quiet` gives net_widths=7; without the flag it is ungraded.
- **Fix.** route.py records the requested widths in the .kicad_pro (as it does net_impedance); graders auto-read them with a pad-neck allowance; reconcile the two skills.

### G15 Impedance never held (false-OK)
- **Claim.** board_score `--impedance-nets` and check_complete grade reference-plane continuity only, never Z0. check_complete ignores the project's net_impedance ("UNEXAMINED … no spec was given").
- **18.** route.py solved 0.920 mm and logged "routed short edge at 0.4601"; check_impedance measures 64.4 / 80.5 Ω; board_score impedance 0, DONE. Verifier FAIL; the declaration was dropped.
- **20.** route_diff `--impedance` wrote 11 declarations; check_complete said DONE; graded, there are 8 blocking (42 reference-plane crossings). Verifier FAIL.
- **Repro:**
  ```
  R=$B/18_uecg/repro; python3 -X utf8 py_tools/board_score.py $R/final_route_old2_iter2.kicad_pcb --impedance-nets 'Net-([CA][1E][0-9]-Pad1)' --quiet   # impedance=0
  python3 -X utf8 py_tools/check_impedance.py $R/final_route_old2_iter2.kicad_pcb --coplanar-gap 0.25 --nets 'Net-(C10-Pad1)' 'Net-(AE1-Pad1)'   # 64.4/80.5 ohm
  ```
- **Fix.** Auto-read net_impedance in both graders and grade Z0 through check_impedance's solver; route.py reports an impedance net shipped below its solved width as a failure.

### G16 Courtyard-conditioned .kicad_dru rules (false-OK)
- **Claim.** check_drc skips `A.insideCourtyard('U1')`-type rules as "non-layer scope"; the router's escalation ignores them; kicad_drc_compare counts copper classes only, so it reads CONSISTENT.
- **20.** The rules require track_width ≥ 0.1016 inside the U1, U200 and J6 courtyards; route.py narrowed to 0.0889, and kicad-cli reports 20 `track_width` errors (26 on v4). Verifier FAIL; fixed with `--fab-overrides`.
- **Repro.** Verbatim 20 §2 (check_drc, kicad_drc_compare and kicad-cli on `$B/20_sam9g25/repro/dru_delivered_v3.kicad_pcb`).
- **Fix.** Evaluate courtyard/area conditions in kicad_dru for track_width and clearance; kicad_drc_compare reports any unclassified KiCad error type instead of dropping it.

### G17 Classless edge_connectors row
- **Claim.** A row whose part is not in `SEATED_CLASSES` is skipped by the seat, with one NOTE per seed log (`edge_seat.py:482-485`). check_floorplan grades the same row ERROR, and the run summary is silent.
- **Per board:** 08 J501 (4 of 12 seeds); 09 C38 (9 of 12, pass discarded); 16 U3 antenna module (12 of 12, pass discarded).
- **Repro:**
  ```
  R=$B/09_StickHub/repro; python3 -X utf8 py_placer/place_simple.py $R/fixed.kicad_pcb $T/g17.kicad_pcb --seed 3 --groups $R/groups.json --intent $R/intent_classless_c38.json 2>&1 | grep -E "C38|floorplan"
  python3 -X utf8 py_tools/check_floorplan.py $T/g17.kicad_pcb --intent $R/intent_classless_c38.json | grep C38
  ```
- **Fix.** Seat a classless row as `connector_affinity`, or refuse it at intent load in both tools; document `class` for non-connectors.

### G18 Rip override stops at the main pass
- **Claim.** An exact name in `--rip-existing-nets` lifts #521 protection in the main pass only. 13's lap2.log shows it:
  - line 32: the main pass makes the net eligible;
  - line 336: the plane finalize "4 PROTECTED excluded";
  - line 387: the nested sub-run "name a net exactly to override".
- **The decisive failure** was a plane tap blocked by /USB_P "(protected, cannot rip)". Hints keep saying "NEVER rip". The board ships NOT DONE on 3 nets after about 45 min of laps.
- **Repro.** `bash $B/13_pico_ice_rev3/explore_E/lap2.sh > $T/lap2.log 2>&1; grep -n "PROTECTED\|eligible for rip-up" $T/lap2.log` (about 3 min).
- **Fix.** Forward the override set into the finalize and nested reconciliation sub-runs, the way the dru map is forwarded; hints read the effective protected set.

### G19 Writeback lowers floors no copper needed (regression-of #1319)
- **Per board:**
  - 10: route_planes `--skip-existing-zones` skipped both zones and drew nothing, yet wrote Default clearance 0.1499 → 0.12.
  - 17: the same flag "tightened" zone clearance to 0.119 for U6's "via lattice". U6 is an LGA-8 with no vias. Default and min_clearance went 0.15 → 0.119.
  - 12: route_diff `--escalation board` wrote min_hole_clearance 0.25 → 0.15, though no track needed it. The fill was then poured 0.1505 mm from 12 NPTH hole/layer pairs, which check_drc does not grade. Verifier FAIL D2.
  - 14: U2's footprint `(clearance 0.08)` became rules.min_clearance 0.08, and `--escalation board` then rescued U1 balls at 0.09, "bounded at the board's own minimums".
- **Repro.** `python3 -X utf8 py_router/route_planes.py $B/17_environment_sensor/repro/placed.kicad_pcb $T/g19.kicad_pcb --nets GND GND GND +3V3 --plane-layers F.Cu In1.Cu B.Cu In2.Cu --skip-existing-zones 2>&1 | grep -E "tightened|keeping it|net_class\[Default\]"`
- **Fix.** Extend #1319's "only the floors of copper it drew" to net-class clearance, min_clearance and min_hole_clearance (route_planes skip path, route_diff); check the lattice exists; a pad override is never a board floor.

### G20 Edge exemptions hide KiCad errors (false-OK)
- **Claim.** Pad-to-edge checking is off by default, tracks near pads count as covered by an "edge-exempt pad", and kicad_drc_compare drops KiCad's items as "#408 intentional". All of this assumes pre-existing edge connectors; on a board placed from a pile, the copper is the run's own.
- **08.** J1's shield tabs are 0.201 / 0.206 mm from the notch against 0.372: 2 KiCad errors, and check_drc finds them only with `--check-pad-edge`. Verifier FAIL. The geometry cannot do better.
- **17.** 5 tracks 0.1976-0.1978 mm from the slot arcs against 0.2; kicad_drc_compare reports "[#408: -5/-5] CONSISTENT". Fixed with `--board-edge-clearance 0.22`.
- **Repro.** `python3 -X utf8 py_router/check_drc.py $B/08_CM5_MINIMA_3/repro/routed.kicad_pcb --check-pad-edge --clearance-margin 0.1` (2 PAD-BOARD-EDGE) against the same command without the flag (0).
- **Fix.** With `--baseline`, exempt only edge copper that already exists at the same place on the baseline.

### G21 No routing to a length window
- **Claim.**
  - Every step prints "length is not routed to"; `--length-match-group` targets the longest member.
  - Protected members silently drop out of later groups' targets.
  - A member with "No straight run with clearance found" ships unmatched while the group reports matched.
  - Rip victims are re-matched short.
- **14.** Arm A had 6 of 8 DQ nets outside 11.5-14.5 mm (DQ6 9.04, DQ7 21.54). A one-call match targets 14.76 mm and fails by construction. 25 orderings (helper) found one that lands all 8; about 1 h.
- **Repro.** Verbatim 14 §1 route.py on `$B/14_imx6ulz_4l/repro/dq_poured.kicad_pcb`, then `check_drc.py` (length rows).
- **Fix.** Clamp the target into the dru window (meander short members up to min); report per-member status; protected members still count toward the target.

### G22 BGA escape field (same as #1343, re-verified STILL BROKEN)
- **14 (new).** 4 decaps and 8 boot-config 0402s sat on B.Cu under U1's ball field. place_fanout_clearance left "12 unresolved"; routed, there were 4 PAD-VIA violations in CONTACT (shorts) and 6 grazes. 19 hand moves and 4 re-routes (blocking 17 → 15 → 8 → 6), about 40 min.
- **Repro.** `python3 -X utf8 py_router/check_drc.py $B/14_imx6ulz_4l/repro/armA_routed.kicad_pcb --clearance-margin 0.1`
- **Fix.** Per the #1343 draft; at minimum, the cap pass names the parts it cannot clear as placement findings.

### G23 check_weird misreads overlap joints
- **Claim.** A segment end inside same-net copper is called "dangling-end" (soft-joint reads 0), which makes check_complete INCOMPLETE. At the same time, a connection made only by a 0.04 mm edge overlap passes every checker. route.py ships both shapes.
- **Per board:**
  - 09: +3.3V end 0.33 mm from the next end, with half-widths summing to 0.375 mm, so the copper overlaps; hand joins needed.
  - 13: VBUS end 0.283 mm from a 0.7 mm track's end. Deleting the 11 reported segments split VBUS (blocking 3 → 5); shipped with 11 findings.
  - 07: power ends 0.5-0.7 mm short of a track they overlap; closing them exposed 11-21 hidden stubs.
  - 08: a 0.046 mm soft joint under the tail of G02.
  - 16: USB_D- joined only by a 0.0415 mm overlap with D5 pad 1. A CLEAN check_join then produced 5 "removable" segments.
- **Repro.** `python3 -X utf8 py_router/check_weird.py $B/09_StickHub/repro/soft_joint.kicad_pcb | grep -E "dangling-end:|soft-joint:|kicad-dangling"`
- **Fix.** One overlap rule shared by check_weird, check_connected and route.py's cleanup; route.py welds soft joints and flags any joint below a minimum contact width.

### G24 Reference planes (same as #1359, re-verified PARTLY)
- **New boards:**
  - 08: 9 nets blocked on the first route, 16 on the stub chain. Forbidding In1/In3/In4 took impedance to 0 (blocking 23 → 10).
  - 10: the USB pair runs about 80% on the In1 GND layer (68.7% / 80.5% over a void), skew 10.58 mm, and is ungraded.
  - 20: 8 USB nets, 42 crossings at prices 1.0 6.0 2.5 1.0.
- **Repro.** Verbatim 08 §2 `check_impedance.py $B/08_CM5_MINIMA_3/repro/trialB_route.kicad_pcb --nets …`
- **Fix.** Forbid (−1) the reference layers for impedance and diff nets in the recipe; mention the continuity grade in plan-pcb-routing.

### G25 route.py verdict vs connectivity (regression-of #1339)
- **09.** JSON_ORACLE says "remaining 1 … GND", but pad_pairs_open lists only +5V and /LED3, and JSON_REGRADE puts GND under routed_single. board_score finds GND broken with 5 joins (blocking 7, not 2).
- **12.** (b) "confirmed connected by the oracle" while check_connected and KiCad find U1.20 on a +3V3 island. (a) The opposite direction: a false `failed 1`.
- **Repro.** `grep -E "JSON_ORACLE|JSON_SUMMARY_MIN" $B/09_StickHub/repro/gnd_verdict_route.log | cut -c1-300; python3 -X utf8 py_tools/board_score.py $B/09_StickHub/repro/gnd_verdict.kicad_pcb --quiet --json $T/g25.json | grep BLOCKING`
- **Fix.** The final re-grade uses the exact fill for every poured net, including links the oracle left open; the oracle's "confirmed" is checked against the exact-fill island it lands on.

### G26 Different-net crossing short
- **20.** RMII-TX0 ↔ VDD-IO SEGMENT-CROSSING at (141.15, 91.85), 5 check_drc violations, with `failed: 0`. In the trace, a VDD-IO poured-net reconnect (377 segments of 0.05 mm) runs through RMII-TX0's earlier track. Reproduced 3 times.
- **Repro.** Verbatim 20 §4 (route.py on `$B/20_sam9g25/repro/short_s6.kicad_pcb`, then check_drc).
- **Fix.** The reconnect routes against in-run copper; add a same-layer crossing audit before write that rips or refuses.

### G27 Via diameter below drill (same as #1349, re-verified PARTLY)
- **07 (new mechanism).** `--escalation board` clamps the via diameter to the board's 0.3 min_via_diameter, giving 0.45, but keeps the 0.508 min_through_hole drill. Every escalation-board route wrote 1-14 such vias (5 in the shipped chain). check_drc is clean; KiCad reports hole_clearance GND/PGND. Each was a hand fix.
- **Repro.** `python3 -X utf8 py_router/check_drc.py $B/07_One-Air-Max/repro/malformed_via.kicad_pcb --clearance-margin 0.1` (clean) against `PATH=$KC:$PATH python3 -X utf8 tests/stress/kicad_drc_compare.py $B/07_One-Air-Max/repro/malformed_via.kicad_pcb`.
- **Fix.** Pin diameter ≥ drill + 2 × annular; check_drc grades annular ring as KiCad does.

### G28 --authored-from omits clearances (false-OK)
- **10.** UNSOUND lists track, via and hole, but not Default/Power clearance 0.1499 → 0.09 or min_hole_clearance 0.25 → 0.09. At 0.1499 the copper has 2540 violations.
- **12.** DONE over min_hole_clearance 0.25 → 0.15.
- **Repro.** `python3 -X utf8 check_complete.py $B/10_glasgow_revC/repro/delivered.kicad_pcb --authored-from $B/10_glasgow_revC/repro/fixed.kicad_pcb`, then compare `net_settings.classes[].clearance` between `repro/fixed.kicad_pro` and `repro/delivered.kicad_pro`.
- **Fix.** Diff every floor in both projects and list each one lowered.

### G29 Courtyard overlaps (false-OK)
- **06.** C17 ↔ U2 (0.095 mm²) and C17 ↔ Y2 (0.151 mm²) are advisory and buildable, while the project severity is error; kicad_drc_compare shows "COURTYARD kicad=2 krt_blocking=0". Three extra arms.
- **14.** 17 KiCad courtyards_overlap errors shipped as advisory, after 19 `place_pose --near` moves, all reported legal.
- **Repro.** `R=$B/06_rp2350_fpga_eensy_prePlane/repro; python3 -X utf8 py_placer/place_pose.py $R/s9_as_placed.kicad_pcb $T/g29.kicad_pcb set C17 --near 153.4 112.7 --rot 0; python3 -X utf8 py_tools/check_assembly.py $T/g29.kicad_pcb --baseline $R/fixed.kicad_pcb`
- **Fix.** Gate overlaps the project grades error (what #1095 intended); `place_pose --near` searches courtyard-clean poses or reports the overlap.

### G30 KiCad track_dangling missed (false-OK)
- **10.** 3 track_dangling (+3V3 0.354 mm, QA6 0.875 mm, Z0_N 0.600 mm) where check_weird and check_orphan_stubs say clean.
- **20 (lead prep #7).** On the stored hatched fill, 8 track_dangling (7 GND stubs in hatch gaps plus VBUS); with `--refill-zones`, 1. check_weird calls the VBUS T-junction connected.
- **Repro.** `python3 -X utf8 py_router/copy_board.py $B/20_sam9g25/delivered.kicad_pcb $T/d.kicad_pcb; $KC/kicad-cli pcb drc $T/d.kicad_pcb --severity-all --format json -o $T/a.json`, and again with `--refill-zones`; count `track_dangling`.
- **Fix.** Match KiCad's dangling rule (including stored fill); surface track_dangling in kicad_drc_compare; fill_for_delivery prunes or names stubs in hatch gaps.

### G31 Loops invisible to DONE (false-OK)
- **Claim.** check_complete does not run check_cycles, and check_weird misses loops through pad-local back-tracks and wide copper.
- **Per board:** 04 has 2 loops; 16 has 19 (+3V3 14, USB_D+ 3, VBUS 2); 17 has 11 on the USB impedance pair. All DONE, with check_weird clean.
- **Repro.** `python3 -X utf8 py_tools/check_cycles.py $B/16_esp_rust_board/routed.kicad_pcb`
- **Fix.** Add check_cycles to check_complete; make `prune_redundant_cycles` use the same definition.

### G32 Fixed part's pad copper past its courtyard
- **18.** E+1 and E-1 have 12 mm pads inside 3.6 mm courtyards. The anneal prices the courtyard; check_assembly's `occupancy_shape` (#1094) is courtyard ∪ pad copper. 12 of 12 pass-1 seeds were NOT BUILDABLE (one short of 0.18 mm²; one overlap of 6.25 mm², 4.03 mm deep), and the judge named 6 of them. Fixed by keep-out circles of r 6.05.
- **Repro.** Verbatim 18 §1 (place_simple `--seeds 1` with `intent_pass1_like.json`, then check_assembly).
- **Fix.** Price `occupancy_shape` in the anneal; pre-flight warns when pad copper exceeds the courtyard.

### G33 One sink per rail
- **Claim.** `sink_nets: Dict[int, str]` (analyze_power_paths.py:303, 312) keeps one sink per net id; later sinks overwrite earlier ones.
- **02.** 1 path traced for two 22 mA ICs.
- **16.** U3 (350 mA) is overwritten by a 60 mA LED; the shell net comes out at 2.0 mm.
- **Repro.** Verbatim 16 §5 one-liner (prints one path, U5 → D9).
- **Fix.** Use `Dict[int, List[str]]`.

### G34 Backward and overlapping paths
- **Claim.** Paths run from regulator outputs back into inputs and through switch nodes, and every path is summed.
- **Per board:**
  - 08: invents U702 → Module301 over +5V.
  - 10: U14 → U30 through +1V2 → +5V; a 1.0 mm track on a 3-pad PLL ground.
  - 13: credits the 1.2 V LDO as the 3.3 V PSRAM's source.
  - 14: 3.0 mm on BGA rails; DRAM_VREF 1.2 mm.
  - 17: GND → GNDREF through FB1.
- **Repro.** `python3 -X utf8 $B/10_glasgow_revC/repro/power_paths_repro.py`
- **Fix.** A directed source → output-net → sink graph that stops at regulators; one path per sink.

### G35 Disclosure does not match the copper (false-OK)
- **15.** The Default class went 0.13 → 0.1075, attributed to 2 nets; at 0.13 there are 7 items on other nets (down to 0.005 mm).
- **16.** The IO0 0.25/0.15 vias are not named. route_diff shipped a 0.25/0.15 via under `--via-size 0.45` with no design_rules record at all.
- **18.** JSON_SHIPPED_RULES lists via narrowings on a net that has 0 vias; signal pins are called "plane tap".
- **Repro.** Verbatim 16 §4 (route_diff on `$B/16_esp_rust_board/repro/s11_pour.kicad_pcb`, grep, via census).
- **Fix.** Build the record from a census of the written copper against the authored floors; give route_diff the same record.

### G36 Facing abstains silently (false-OK)
- **20.** The SW1 and SW2 actuators (EVQP7C) face along their edges, and check_floorplan prints `pass` with no facing word at all; declaring `mating_face +y` makes both FAIL. Verifier FAIL, a hand repair and 2 more chains.
- **Repro.** `python3 -X utf8 py_tools/check_floorplan.py $B/20_sam9g25/repro/facing_final_v1.kicad_pcb --intent $B/20_sam9g25/repro/intent_run.json`
- **Fix.** Print "facing abstained (reason)"; warn for edge_actuator; infer facing from the F.Fab protrusion.

### G37 Fanout blamed for ripped escapes (same as #1311, re-verified PARTLY)
- **New evidence that the hint half also persists:**
  - 08: "Module302.133 … Re-run the fanout", though qfn_fanout escaped 38 of 38.
  - 20: "U1.C13 … Re-run the fanout", though the fanout escaped 133 of 133; the first route step ripped the escape (terminal_restores_broken). A whole extra chain.
- **Repro.** Verbatim 20 §7 (route.py on `$B/20_sam9g25/repro/hint_s7.kicad_pcb`).
- **Fix.** Per the #1311 draft; the hint checks the input's escape copper before blaming the fanout.

### G38 Pairs wall in later nets (#677)
- **13.** The hints for its 3 open nets name the USB copper as the wall.
- **14.** Pairs routed early took the only VMEM drop site, so VMEM broke. Six re-orderings each lost a pair or broke 1-4 nets; only hand vias placed before the pair step fixed it.
- **Repro.** Verbatim 14 §3 board_score on `$B/14_imx6ulz_4l/repro/a9_routed.kicad_pcb` (BLOCKING=1, VMEM).
- **Fix.** Reserve plane-drop and escape sites for poured-net balls when pairs route early.

### G39 REDO manifest gaps
- **04.** The upgrade and 3 joins had to be appended by hand.
- **14.** No check_join is recorded; the replay dies at step 7.
- **19.** The upgrade is absent, so a replay routes the KiCad 8 copy (249 vias, broken).
- **Repro.** Verbatim 14 §8 (a check_join with REDO_RUNDIR set writes no manifest).
- **Fix.** check_join records itself; add a recorded upgrade step; the G02 delete CLI records itself.

### G40 Judge ignores template drift
- **08.** The best seed had C709 24.27 mm off its template (ground return 25.9 mm); another best had L701 19 mm off.
- **18.** The best seed had L2 5.94 mm off. Restoring it gave 139 vias / 929.6 mm against 141 / 1007.5.
- **Repro.** `python3 -X utf8 py_tools/check_floorplan.py $B/08_CM5_MINIMA_3/old/pass4/s10.kicad_pcb --intent $B/08_CM5_MINIMA_3/repro/intent_pass4.json | grep template`
- **Fix.** judge_key penalises template drift; §3.7 says to restore template members before routing.

### G41 Same-number MP tabs (false-OK)
- **17.** J2 and J3 each have two `MP` pads on one net. The repo treats it as a one-pad net and says connected and DONE; KiCad reports 2 unconnected. Fixed with 2 check_join tracks.
- **Repro.** Verbatim 17 §3 (check_connected against kicad-cli on `$B/17_environment_sensor/repro/mptabs_routed.kicad_pcb`).
- **Fix.** Treat same-number pads on one net as multipoint in the router and the graders.

### G42 Nondeterminism
- **17.** Same input, flags and Step 2c env: 1183 or 1188 copper items (917.32 or 923.97 mm), alternating between runs.
- **20.** The plane finalize printed "Zone SPLIT 3 islands" in 1 of 4 identical runs (368 vs 373 vias).
- **Repro.** Verbatim 17 §4 loop; compare md5s.
- **Fix.** Find the unordered iteration or timing source in the global-plan path and the finalize; add a determinism test.

### G43 One-cap pin (same as #1320, re-verified STILL BROKEN)
- **14.** U1.P12 broke its limit in 11 of 12 seeds in both passes (21-32 mm against 8.455); `decap_limits` is a flat 5.0. Fixed only by an error-graded proximity row.
- **Repro.** Verbatim 14 §9.

### G44 Last --impedance-nets wins (false-OK)
- **Claim.** `nargs='+'` without `action='extend'` (board_score.py:1357, check_complete.py:583); grade.py's `--spec` emits repeated flags.
- **18.** Order AE1, C10 gives impedance 0 and BLOCKING 0; order C10, AE1 gives impedance 1 and BLOCKING 1.
- **Repro.** Verbatim 18 §4 (two board_score calls on `final_route_old1_iter2`).
- **Fix.** Use `action='extend'` and audit the other `nargs='+'` spec flags.

### G45 route_diff cannot re-route a connected pair
- **14.** "Skipping 6 already-routed … nothing to route", exit 0. The teammate wrote strip_nets.py.
- **08.** `--force-reroute` unrecognized by route_diff. Step 2d prescribes it, and route.py re-routes pairs single-ended.
- **Repro.** `python3 -X utf8 py_router/route_diff.py --help | grep -c -E 'rip-existing|force-reroute'` prints 0.
- **Fix.** Add `--force-reroute` to route_diff (rip both members, route as a pair); fix the Step 2d text.

## Minor (beyond the top 45, one line each)
- Narrow pad webs below the min-track floor (a 1.5 mm via in a 0.6 mm pad; terminal caps): 04, 14, 15. `check_weird $B/04_multichannel_mixer/repro/gap7_s2_lc1.kicad_pcb`. Related #1063, #1161, #1187.
- Same-net vias with overlapping drills, unreported by route.py (+3V3 0.22 mm apart; GND 0.071 mm apart): 08, 10. `check_drc $B/10_glasgow_revC/repro/vdh_7_iter2.kicad_pcb`.
- Regression-of #1315 (candidate): `bga_fanout --check-for-previous` puts dog-bone vias on DQ7's lane, 6 violations, "failed 0": 14 §10.
- Same as #1316 (STILL BROKEN): route_bus output has no .kicad_dru; DQ lanes out of window, locked, untunable (#1363): 14 §13.
- `--no-fix-drc-settings` also drops protected_nets, so the pair is re-routed single-ended (35 of 103 segments survive): 12 §4.
- Notched edge: the seat puts U1 6.43 mm inside the real edge, antenna under BAT1, WARN only: 07 §3.
- Regression-of #1325 (candidate): DC1's south seat refused in every seed (145 of 188 "against BAT1") though the anneal seats it legally; floorplan ERROR in 5 of 12 seeds: 07 §9.
- A group `edge` hint is met when any one member touches the side (`placement/simple.py _hint_full`): long headers mid-board (12, 20).
- Zone shape feasibility: "no legal pose" with no reason; the plan check measures area only: 19 §5 (about 30 min).
- Lead prep #1: the writer crashes on KiCad 6/7 `(at x y unlocked)` (`writer.py:296`): daplink source (11).
- Lead prep #3: make_unplaced cannot remove a KiCad 6 `(footprint … locked …)` lock (`make_unplaced.py:181-188`), and writes the pile anyway: 16, 18 sources.
- Lead prep #4: a part carrying a milled window trips the writer's `OutlineOwnerMove` (`writer.py:1343-1356`): tfgps01.
- fit_template seats C9 5.76 mm against a 4.2375 limit, with only a NOTE: 20 §9.
- The cap pass breaks C78's decap limit and strands the fanout stub: 10 §3.
- Mouse-bite drills: (a) regression-of #1297 (uncovered case), 16 declared drill poses refused in every seed, exit 4; (b) drills classed mount_hole gate like screw-head keep-outs, and SKILL §3.1 implies a waiver that does not exist: 19 §6, §9.
- Plan-file tokenising: manifest_to_plan reads the skill's own `> log 2>&1` as tool arguments (06, 11); route_plan_check R02 reads a `|` inside a quoted net name as a pipe (19).
- Skill text: "--min-thickness 0.1" replaces the designer's 0.15 mm pours, leaving 12 connection_width webs no DONE grader sees: 12 §7.
- Skill text: Step 8's pour-last recipe is REVERTED by the improvement gate (blocking 40 against 8 pour-first): 09 §3.
- Skill text: "--rip-existing-nets <exact names>" is a no-op on a connected net; the flag needed is `--force-reroute` (09, 19; also 10, 12, 15). #515.
- Skill text: the stop rule says nothing about arms in flight (13), and counts unusable placement passes before any route (19).
- Same as #1326 (PARTLY): place_pose `legal: false` on every pose on an outline with arcs (12, 15, 17).
- check_floorplan exits 4 / pass false with 0 errors on a pile-emitted intent (03, 04; also noted on 11, 16).
- converge: "no board_sha" warning on every quick_score row and a mis-read `--rejected` lever (01, 04, 06); a wrong "only one carries a score" verdict (11).
- Decap grading: an error/warn cliff between the limit and the 5 mm radius (10); a cap attributed to the nearest IC rather than the one it serves (06); `decap_pin_uncovered` on a buck LX switch node (08, 16).
- route_diff has no `--json-out` though §3.7's chain example uses one (07, 14).
- render_placement reports BODY STACK on a round pad's bounding box (18); check_assembly says "off-board" for pads 0.245 mm inside (02).
- kicad_drc_compare subtracts pre-existing items by position, so moved solder-jumper copper reads DIVERGED (19).
- route_diff: a pair demoted to "partial" by a test pad 3 mm away (19); a wrong "far-apart peeled" message (06); GND return vias left dangling on a 2-layer board (12).
- Classification: AK300 screw terminals classify None; CAP+/CAP- detected as a diff pair (03). The `-VAA` (dash-letter) net name is rejected by argparse; #597 fixed dash-digit only (03).
- `achievability_note` is silent on KiCad's default stackup (10); check_reachability defaults to netclass sizes (04); route_plan_check R17 calls a split layer a "solid plane" (14).
- CLI validation (lead prep #6, plus #7's third instance): raw FileNotFoundError on a missing input board (09, 14); raw ValueError on a `--power-nets` length mismatch (07); a whole flag string inside `--nets` is routed at exit 0 (12).
- A negative `overhang_mm.min` is accepted and never reads; `max_setback_mm` is never named (08).
- The default `--moves` stops about 13% copper short on a small board (one board: 01).
- Missing tools: a rotation/escape ranker (09, 13; #1191's `rank_rotations` does not ship), a hand-join via-site finder (13), a one-lever arm runner (15).
- Skill text: the CM4/CM5 underpad recipe escapes 18 of 38 at a 0.45 mm via floor where stub escapes 38 of 38 (08). One-board measurements: the iteration passes added vias (04); "--via-cost higher = fewer vias" ran the other way (11).
- judge chains cannot carry an env knob (08); `board_score --quiet` still prints a 10 kB line (#1194 residual, 19); §3.6's check_assembly call omits `--intent` (10).
- starved_thermal errors on DONE boards (04: 3; 19: 1). #1334 is report-only by owner decision.
- KiCad 6 file: 79-82 vias in pads by default; `--same-net-pad-clearance 0.1` cuts this to 2 (12; #1025).
- U1 reads "6.08 mm from the edge" while its drawn body is flush (07).
- Lead prep #8: docs/floorplan-intent.md:671-676 quotes daplink's source band values (11).

## Environment (not code defects)
- **E01 No PDF reader.**
  - Boards: 02, 03, 04, 06, 07, 08, 09, 13, 14, 15, 16, 17, 18, 20.
  - What failed: the Read tool needs pdftoppm; there is no poppler, fitz or pypdf; WebFetch returns FlateDecode bytes; §3.5 names no fallback.
  - What teammates did: wrote PDFKit Swift helpers (9 boards), a stream inflater (09), and pip-installed PyMuPDF, 249 MB (20). Cost 4-10 min each.
  - Repro: `which pdftotext pdftoppm; python3 -c "import fitz"; python3 -c "import pypdf"`.
  - Fix candidate: ship a PDF page/text helper, or add pypdf, and name the fallback in §3.5.
- **E02 kicad-cli not on PATH (macOS).**
  - Boards: 01, 06, 08, 12, 15, 17 (04 and 20 set PATH up front).
  - SKILL §3.9 and plan-pcb-routing 4c call it bare, and §3.9's fallback would ship "silk ungraded". The repo's own tools find KiCad through `py_router/kicad_locate.py`.
  - Fix: a kicad_locate shim.
- **E03 Datasheet hosts refuse automation.** ST (HTTP/2 error), LCSC (HTML bot check), Nordic (Cloudflare), Microchip (Access Denied): 02, 13, 15, 18, 20. The skill could say to check `file` after each download.
- **E04 REPORT.md write refused by the harness for a subagent:** 03.
- **E05 build_router.py compares against `origin/main` (`build_router.py:405`)** (lead prep #2): a fork clone always builds from source.

Pending: 05_interf_u. Send its TOOL_GAPS.md when it exists and I will fold it in.


---

# Delta: board 05 interf_u folded in (G46, G47 new)

I folded in 05_interf_u's 7 gaps. Gap 1 stands alone as a new cluster (G46), and gap 4 promotes the starved-thermal minor line to a cluster (G47). Gaps 2, 3 and 5 extend G04, G03 and G09; gaps 6 and 7 are minor lines.

## Existing clusters that gain board 05

- **G04 (default fab escalation goes below the authored floors; bare graders say DONE). Boards become 04,05,11,16.**
  - **05 measurements.** These are route.py's defaults with `--clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5` on a 2-layer through-hole board.
    - Arm B wrote Default and Power class clearance 0.254 → 0.1588, and `min_track_width` 0.2 → 0.127.
    - Arm A wrote `min_track_width` 0.2 → 0.175, `min_via_diameter` 0.9 → 0.45 and `min_through_hole_diameter` 0.5 → 0.2. This came from a GND net rescue that escalated to the advanced tier.
    - The first DONE board (`final_route_old1/lap2.kicad_pcb`) passed the bare `check_complete` and `board_score`. It reads UNSOUND under `--authored-from`, so it was discarded (about 15 min).
    - With `--escalation board`, every later arm held 0.254 / 0.2 / 0.9-0.5, and the shipped board is DONE under `--authored-from`.
  - **New in it.**
    - `--clearance-ceiling 0.254` reads to a user as "never tighter than 0.254", yet the class went to 0.1588.
    - plan-pcb-routing never names `--escalation board`; the teammate found it in `--help`.
  - **Fix addition.** Steps 2c/4 of the routing skill should say that `--escalation board` keeps the run at the authored floors.
  - **Repro.** Verbatim 05 §2: `copy_board` of `$B/05_interf_u/repro/placed_seed1.kicad_pcb`, then route.py, then `grep PROJECT_WRITES_JSON`.

- **G03 (analyze_power_paths counts once per power pin). Boards become 05,06,08,09,11,12,13,17.**
  - **05 measurements.**
    - U9 (XC4003A: 8 VCC pins, 3 mode pins tied to VCC, 9 GND) contributes about 9× its current.
    - BUS1's two +5V fingers count its rating twice.
    - Result: GND 2.0 mm and VCC 1.2 mm for about 0.46 A, where the skill's own table gives 0.7 mm.
    - It also sizes the one-pad net `unconnected-(BUS1-GND-Pad10)` at 0.5-0.7 mm.
  - **Repro.** `python3 -X utf8 $B/05_interf_u/repro/power_double_count.py`

- **G09 (the quick judge mis-ranks seeds against full routes). Boards become 01,03,04,05,12 (+07).**
  - **05 measurements.** Re-judged with the chain the run later shipped (Step 8's through-hole recipe, via cost 300), `judge_seeds` named seed 11. The quick routes were s11 blocking 2 / 71 vias and s1 blocking 3 / 67 vias. The full routes with 2 iterations were s1 DONE at 93 vias and s11 blocking 1 at 99 vias.
  - **Why it matters.** The judge was running the same chain that was shipped, so the inversion here is not only the "wrong arm" cause.
  - **Skill gap.** There is no step for when §3.8 finds a much better recipe (here 162 → 93 vias): whether to re-judge, and whether the judge or the full route wins.
  - **Repro.** Verbatim 05 §5: a loop over `placed_seed1` and `placed_seed11`, then `grep JSON_SUMMARY_MIN`.

- **Minor line "board_score --quiet still prints SCORE_JSON" (#1194 residual). Boards become 05,19.**
  - 05 measured 21,454 bytes on stdout for the 24-part pile and 4,290 bytes on the routed board, on every call.

- **Checked against 05, not hit.**
  - G01: the fill ran, but this through-hole board has no vias in paste, and it delivered DONE.
  - G05: only seeds 6 and 9 of 12 carried decap errors (the board has bulk caps only). This does not fit the every-seed pattern.

## New clusters

### G46 Blocker analysis blames a net on the other layer; the real same-layer wall is never named (bug)
- **Boards:** 05. **Severity:** medium-high. **Upstream:** new (#510 closed and #592 open are related, neither covers it).
- **Answer to your question.** This stands alone rather than going into G06.
  - It shares G06's symptom: a pad caged by the run's own copper, and a rescue that fails.
  - The root cause is different. The blocker attribution is blind to layers: it credits a cross-layer finger that only forbids a via. G06 is about the rescue lacking the right levers.
- **The claim.** Phase 3 reports `VCC blocked_by /PC-DB6 (blocked_count 1)` for every `--ripup-blocker-select` (count, near-target, bidir, mincut). It then rips /PC-DB6, fails, restores it, and prints "No additional rippable blockers from retry analysis". VCC ships open at BUS1 pad 3.
- **What was true.**
  - BUS1.3 is the +5V finger on **B.Cu** (1.778 × 7.62 mm at 164.47, 138.43).
  - /PC-DB6 is pad 34, the **F.Cu** finger on the other side of the card. It only forbids a via in the finger.
  - The wall is /PC-RST's B.Cu track (162.4,134.2)-(165.6,134.2)-(167.0,135.6). It runs 0.42 mm above the finger and spans its whole width.
  - The backward search explores 1785 cells (the finger itself) and stops. /PC-RST is never named, so no selector can rip it.
  - Naming it by hand does not help either. `--nets VCC /PC-RST GND --rip-existing-nets /PC-RST --force-reroute`, with or without `--ordering original`, re-lays /PC-RST along the same line, because its phase-1 edge is routed before VCC's phase-3 tap.
  - A failed-first split (VCC and GND first, then `'*'`) opened 4 other nets.
- **Cost.**
  - This one open set the floor on vias: it is the only open at via cost 375, 450 and 600, and on arm B. That is 72 vias with it open against the 88 shipped.
  - It took about 10 laps, about 35 min.
- **Repro:**
  ```
  python3 -X utf8 -u py_router/route.py $B/05_interf_u/repro/vcc_finger_walled.kicad_pcb $T/out_vcc.kicad_pcb --nets VCC GND --no-bga-zones U9 --clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5 --power-nets GND VCC --power-nets-widths 0.7 0.7 --layer-costs 1.0 1.0 --direction-preference-cost 4000 --turn-cost 2000 --via-cost 600 --escalation board > $T/out_vcc.log 2>&1
  grep -E "Ripping|was blocking|No additional rippable" $T/out_vcc.log
  python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as p;b=p('$B/05_interf_u/repro/vcc_finger_walled.kicad_pcb');[print(s.layer,(s.start_x,s.start_y),(s.end_x,s.end_y)) for s in b.segments if b.nets[s.net_id].name=='/PC-RST' and min(s.start_y,s.end_y)>130]"   # the 2 B.Cu wall segments
  ```
- **What a fix needs.**
  - Attribute blockers per layer, on the frontier cells of the failed search. When a pad cannot take a via, count only copper on the pad's own layer.
  - When a terminal's frontier is closed by one net's track, name that net.
  - A forced re-route of the named wall should be ordered after (or priced around) the tap it walls in.

### G47 starved_thermal errors at project severity ship on DONE boards; the routing skill contradicts its own R07 on --thermal-relief (false-OK / skill-text)
- **Boards:** 04, 05, 19. **Severity:** medium. **Upstream:** #1334 (closed; fixed as reporting only, by owner decision); #1329 (closed). The skill contradiction is new.
- **What this cluster changes.** It promotes the minor line "starved_thermal errors on DONE boards (04, 19)" from my first reply to a cluster, because 05 adds a third board and the skill-text contradiction behind it.
- **The contradiction.**
  - plan-pcb-routing SKILL.md:1468 says "it should be replaced but keep thermal relief, add `--thermal-relief`".
  - SKILL.md:1411 says "do not set `--thermal-relief`", and `route_plan_check.py` R07 (lines 267-272 and 597) refuses the flag.
  - So the agent cannot re-pour a designer's thermal-relief pour and keep the reliefs.
- **Measurements.**
  - **05:** the designer's B.Cu GND pour was kept as drawn (thermal relief, 0.5 mm clearance), with no route_planes step. KiCad `--refill-zones` then reports 5 `starved_thermal` errors at project severity: U2.10, U8.12, U9.G2, U9.K3 and U9.L7 (3 on the via-300 board). Every pad is still connected through tracks.
  - **On the same 05 board, every DONE gate is clean:** board_score blocking 0, check_complete DONE, check_drc 0, and kicad_drc_compare CONSISTENT (it prints `thermal=5` outside its verdict).
  - **04:** 3 starved thermals (IC1.4, C12.1, IC4.4), cleared by 3 hand GND stub joins after force-reroutes only moved them around.
  - **19:** U1.2.
- **Repro.** `PATH=$KC:$PATH python3 -X utf8 tests/stress/kicad_drc_compare.py $B/05_interf_u/routed.kicad_pcb --baseline $B/05_interf_u/final_route/in.kicad_pcb` gives `thermal=5` with the verdict CONSISTENT. For the contradiction: `grep -n "thermal-relief" .claude/skills/plan-pcb-routing/SKILL.md`.
- **What a fix needs.**
  - Make Step 1 agree with R07, or let R07 allow `--thermal-relief` when the plan replaces a designer's relief pour.
  - Count `starved_thermal` errors at the project's error severity in check_complete, or at least in the verifier brief. That reverses #1334's owner decision, so it is the owner's call.
  - route.py's plane finalize should add a spoke or stub when a thermal is starved.

## New minor line
- kicad_drc_compare labels every starved thermal as pad `?` at the zone outline's corner (193.675, 133.35). `_THERMAL_PAD_RE` (`tests/stress/kicad_drc_compare.py:147`) matches only a capitalised `Pad`, while KiCad 10.0.7 writes lower-case `PTH pad 10 [GND] of U2`. Found on 05, and independently by its verifier. The fix is `re.IGNORECASE`.

Totals with 05 folded in: 47 clusters (G01-G47), E01-E05, and the minor list, which loses the starved-thermal line and gains the regex line. The other clusters are unchanged.
