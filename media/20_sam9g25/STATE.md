# STATE 20_sam9g25

FIRST_CMD: 2026-10-23T10:58:16Z

## Milestones
- 11:00Z fixed.kicad_pcb = copy_board of input; intent_run.json = copy of intent.json (+ U2 template row from fit_template)
- groups.json written (11 groups), check_groups 0 errors 0 warnings
- U2 MCP16501 template (16 members, text/schematic based: DS20006388B has no layout figure)
- 11:09Z pass 1 place_simple launched: 12 seeds, --jobs 4, log wk/gpm/20_sam9g25/place_pass1.log

## Next
- judge seeds (judge_seeds --jobs 2) with judge_chain.txt
- 11:13Z pass 1 done (12 seeds, judge 5,10,4,2,8,7); NOT judged: input fixes found -> archived to old/pass1/
  (U2 template v1 stranded C9 4.9mm off U2 -> decap_ungraded in 7 seeds; J6/J3 edge hints ignored, J6 mid-board in 6 seeds)
- intent_run.json now: U2 template v3 (COUTs beside each other at the chip), + edge_connectors J6 east (+x), J3 north (+x)
- 11:15Z pass 2 place_simple launched, log place_pass2.log
- 11:20Z pass 2 done: judged seeds 11,7,1,3,0,5 (all buildable+floorplan-clean); judge_seeds launched --jobs 2, log judge_pass2.log

## Tool gaps noted (running list)
1. Read tool cannot render PDFs (poppler missing); helpers/pdftool.py + pip --target helpers/pylib pymupdf
2. analyze_power_paths: no power paths traced; GND 3.0 / VDD-IO 2.0 / VDD_DDR 2.0 mm widths; VIN, VBUS (the real input path) omitted
3. fit_template (no-figure template): greedy seat put C9 4.9mm off U2 -> decap_ungraded ERROR in 7/12 seeds; fit_template does not check the intent's decap limits
4. group `edge` hint did not lay J6 (2x22 THT header) on an edge: mid-board in 6/12 pass-1 seeds; needed edge_connectors rows
- 11:25Z kept seed 11 -> final.kicad_pcb; full route plan final_route/final_plan.sh (route_plan_check OK) launched, logs final_route/s*.log
- 11:31Z first routed board final_route/s9_iter2 blocking 1 (ddr-d11, U1.C13 CAGED by routed copper, PASSABLE on placement); scoped laps s10 (rip BTN_USR), s11 (rip ddr-ck-) no change; arms rA (ripped-route-avoidance 3 + track-proximity 2) and rB (max-ripup 3) from s6 running in arms/
- 11:39Z arm rA (route step with --ripped-route-avoidance-cost 3 --track-proximity-cost 2, then force-reroute RMII-TX0+LCD-D10 [crossing short fix] and ddr-ck pair [dangling vias]) -> blocking 0, check_complete DONE (arms/rA/s12). Old chain moved to final_route_old1/; re-running winning chain in final_route/ (final_plan.sh v2). arm rC (route_bus) running in arms/rC
- 11:44Z DONE: final_route/s11_lap_ck -> routed.kicad_pcb (blocking 0, check_complete DONE, vias 527 copper 3881.78 seg 2646). Next: optimisation arms (rC route_bus running), then 3.9 labels+fill, verifier
- 11:57Z arm rE (via-cost 150) -> arms/rE/s13_drop.kicad_pcb DONE vias 473 copper 4017.78 (better than routed.kicad_pcb's 527); needs helper drop_segment (GND stub). rD (auto escape) rejected 540 vias. rF (via-cost 300) running; rC (route_bus) still in fanout round 1 (started 11:36Z)
- plan: winner gets re-run in final_route/ (move current to final_route_old2/)
5. route.py shipped a RMII-TX0 x VDD-IO crossing short (arm rA s7) with failed 0; repro repro/short_s6.kicad_pcb
6. route.py v1: hint "U1.C13 is a fanout-dropped ball" -- the route step itself ripped it (terminal_restores_broken)
7. GND dead-end stub (0.2mm, F.Cu) survives every route.py pass incl. '*' and pours-only; no tool removes it -> helpers/drop_segment.py
- 12:26Z v3 final_route (via-cost 1200) DONE vias 373 copper 4059.89 -> routed.kicad_pcb; rerun of rH not reproducible (368 in arm). rC route_bus still running (fanout round 2).
- 12:51Z post-DONE plateau: rI (via 2400) 371, rJ (auto+1200) 402+DRC, rC2 (route_bus+1200) 370 -- none beats rH 368 (run-to-run spread 5 vias). Shipping v3 final_route (373). 3.9 done: labelled (silk 128->30), delivered.kicad_pcb filled. Next: verifier.
- 12:54Z verifier call 1 running on delivered.kicad_pcb (sha de85413c...). grade.py done:true. REPORT.md Write refused by harness -> report goes in final reply (no REPORT_DONE).
- 13:03Z verifier 1 FAIL (SW1/SW2 facing; impedance decl 11 blocking; 20 kicad track_width in dru courtyards). Fix: SW1/SW2 mating_face +y + hand turn -> final.kicad_pcb (old in old/final_v1); next v4 route: no --impedance (USB 0.171 / ck 0.139 geometry), ck glob fixed, kicad-cli track_width check + laps
- 13:22Z v5 final_route DONE (s12_drop2: vias 355 copper 4076.04, kicad-cli: 0 track_width, 3 solder_mask_bridge AE1 lib, 1 VBUS track_dangling warn) -> routed.kicad_pcb; old routed/delivered in old/*_v3. Next: 3.9 + verifier call 2
- 13:32Z verifier call 2 PASS on delivered.kicad_pcb sha c854a3ea650000edb6b5311f8b438a1f55cdb4166ea6fe357e5196d0c049b70c (vias 355, copper 4076.04, segments 2491)
- 13:33Z DONE marker written; ledger closed (--final --stop-condition 1, 32 rows); grade_out/ and measure.txt written; REPORT.md refused by harness -> in final reply, no REPORT_DONE
## FINAL: DONE. best board = delivered.kicad_pcb (sha above). No running jobs.
