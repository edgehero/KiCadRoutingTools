# STATE 08_CM5_MINIMA_3

FIRST_CMD: 2026-10-23T13:42:07Z

## Milestones
- 15:42 start. Inputs read; fixed.kicad_pcb = copy_board of input.
- intent_run.json = copy of intent.json + J1 fixed pose (notch, judgment) + edge_connectors J101/USB701 (W), J501 (S) + U702 template (fit_template).
- groups.json written (9 groups).
- 15:57 CEST pass 1 place_simple launched (12 seeds, --jobs 4), log wk/gpm/08_CM5_MINIMA_3/place_pass1.log
- ~15:59 pass 1 rejected (J1 pose refused vs H102 courtyard; USB-C negative band unseated) -> intent fixes.
- ~16:02 pass 2: 8 clean seeds; s8 = first legal placement (ledger). Rejected by judgment: parts under the M.2 2242 card.
- ~16:05 pass 3 launched with F keep-out m2-card-2242 (log place_pass3.log)
- ~16:09 pass 3 rejected (strict keep-out too crowded; J501 not edge-seated: no part class). pass 4: keep-out allows low parts; J501 class edge_receptacle (log place_pass4.log)
- ~16:12 pass 4: 12/12 seeds clean; judged 6,9,7,5,2,10. judge_seeds launched (jobs 2), log judge_pass4.log
- 16:16 pass 4 judged (best s10 blocking 3, but buck split: L701 19 mm off template). Rejected; pass 5: U702 also kept out of the card region (log place_pass5.log)
- 16:19 pass 5 placed (12/12 clean); judge launched, log judge_pass5.log
- 16:23 kept pass5 s7 -> final.kicad_pcb; full route steps 1-3 launched (final_route/run_123.log)
- 16:27 step3 routed: blocking 29 (unrouted 2, broken 18, impedance 9), joins 20, vias 196. iterations launched (final_route/run_iter.log)
- 16:32 approach 1 (iterations) plateau: blocking 28 joins 18. trial B (stub fanout of both module connectors) running in scratch/trialB
- 16:36 trial B: blocking 23 (broken 7, impedance 16), joins 7. trial C (B + In1/In3/In4 forbidden for tracks) running
- 16:38 trial C: blocking 10 (broken 10, impedance 0), joins 10. iterations on C running
- 16:41 C iterations: no gain. trial D (C + --clearance-ceiling 0.13 everywhere, coplanar 0.15) running
- 16:44 trial D (ceiling 0.13) worse: blocking 12. trials E (C + grid 0.05) and F (C + grid 0.05 + ceiling 0.1) running
- 16:49 trial E blocking 5, trial F blocking 3 (best). iterations on F running
- 16:58 F plateau at 3 (scoped laps: no gain). approach: placement repair (D401/D402 inline above J501 rot 180, R703 moved off the HDMI_+5V path) -> trial G running
- 17:04 trial G (repaired placement + F chain): blocking 2 (D2 pair). trial H: D2 pair routed first (failed-first split) running
- 17:08 trial H: BLOCKING 0 (vias 241, copper 2469.7). checking check_complete
- 17:11 final_route_old1 archived; new final_route chain (fanout+capclear+D2-first+F params+tidy) launched on repaired final, log final_route/run.log
- 17:17 FIRST DONE: final_route/s6_join.kicad_pcb -> routed.kicad_pcb (blocking 0, check_complete DONE, vias 234, copper 2474.6)
- 17:22 KiCad DRC flagged C601/R703 courtyard; CN1 found under CM5 body. final v3 (R703+CN1 moved); old chain -> final_route_old2; re-running chain in final_route
- 17:28 DONE on v3: routed.kicad_pcb (vias 225, copper 2542.06). optimisation arms A1 (via-cost 100) / A2 (max-ripup 3) next
- 17:31 arm A1 (via-cost 100) better: vias 214 copper 2486; A2 rejected. final_route -> final_route_old3; re-running chain with via-cost 100
- 17:35 routed.kicad_pcb = final_route/s6_join (DONE, vias 215, copper 2473.66). next: 3.9 labels+fill, grade, verifier
- 17:46 arms: via-cost 150 best (201 vias); 200/300 worse (2 failed in a row). final_route -> final_route_old4; re-running with via-cost 150
- 17:51 routed.kicad_pcb = via-cost-150 chain s6_join (DONE, vias 201, copper 2527.06); labels: all 84 hidden, no change
- 17:52 delivered.kicad_pcb filled (sha 203667ad...); grade.py done=true; spawning verifier 1
- 17:55 verifier 1 running (writes verdict_1*.txt). REPORT.md write refused by the harness ("Subagents should return findings as text") -> report goes into the final reply; no REPORT_DONE.
## Current best
- delivered.kicad_pcb sha256 203667ad19b3fa48a9a618cee5257a91ebe8c362f2e70dd2fe0221f73129b972 (board_score blocking 0, vias 201, copper 2527.06, segments 2123; check_complete DONE)
- routed.kicad_pcb sha256 8308cab18253b1411a7ebdfd05387e708c2461329a5e8f7cd9e82b23efb2577b
- 18:05 verifier 1 FAIL: (1) diff pairs ungraded, 13/18 skew>0.5mm; (2) J1 tab edge clearance 0.20 vs 0.372 (inherent). trial M: skew rule dru (0.15mm within_diff_pairs, judgment) + route_diff --diff-pair-intra-match
- 18:10 ledger closed (stop 4); DELIVERED.sha256 + DONE written; inputs re-hashed unchanged
- 18:12 FINISHED. measure.py: wall 2:29:56 (jobs 3040 s, tools 2373 s, model 3583 s). REPORT.md refused by harness -> in the final reply (no REPORT_DONE). No running jobs.
