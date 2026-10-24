# STATE 01_ecc83-pp_v2

FIRST_CMD: 2026-10-23T15:28:37Z

## Milestones
- 15:3x setup: fixed.kicad_pcb (copy_board of input), intent_run.json (= intent.json, waive_locked_overlaps: 0 pairs), groups.json (5 groups, check_groups 0 err/0 warn), no templates, no EMC rows (emc_roles empty)
- pass 1 placing: place_simple 12 seeds --jobs 4, log wk/gpm/01_ecc83-pp_v2/place_pass1.log
- 15:33 pass1 placed: 12 legal seeds, judge.json names 4,5,6,1,9,3; all buildable, floorplan 0. Ledger: s0 first legal placement.
- judging: judge_seeds --jobs 3, log wk/gpm/01_ecc83-pp_v2/judge_pass1.log (KICAD_ROUTE_TRACE=1)
- 15:34 judged: s4 best (quick: blocking 0, joins 0, vias 1, copper 125.74, seg 69). Kept -> final.kicad_pcb sha256 57cd564d68f689b2ecda1129ece0fcce051882b8fdc5b81f354fe80e4db8c52f. CHOSEN.json, placed_from/ written. Ledger rows 0-7.
- next: §3.8 full route by plan-pcb-routing (by hand) in final_route/, two arms (defaults vs --layer-costs 1.0 1.0 --via-cost 600)
- 15:36 FIRST DONE: arm A (defaults) final_route_old1/s4_iter2 vias 3 copper 125.79 seg 30; arm B (--layer-costs 1.0 1.0 --via-cost 600) final_route/s4_iter2.kicad_pcb DONE vias 0 copper 121.6 seg 25 (best). Ledger rows 8,9.
- next: post-DONE copper check: arm-B chain on the other judged seeds (expt/), then silk, fill, verifier
- 15:38 post-DONE approach 1 (arm-B chain on all 12 pass-1 seeds, expt/) rejected: best alt s9 130.94 > 121.6. approach 2: pass 2 place_simple --moves 27500 (5x); pass-1 files moved to old/pass1/. Best board still final_route/s4_iter2.kicad_pcb (from old/pass1/s4).
- 15:40 approach 2 (pass 2, --moves 27500) IMPROVED: s8 arm B full route vias 0 copper 116.37 seg 23 (expt/p2_s8_armB). Pass-2 files in old/pass2/. Trying approach 3: pass 3 --moves 110000. If not better, restore old/pass2 to folder and ship pass-2 s8.
- 15:43 approach 3 (pass 3 --moves 110000) IMPROVED: s1 arm B full copper 105.52 vias 0 (expt/p3_s1_armB); judge re-run with arm-B chain (judge_pass3b.log) also picks s1. Pass-3 files -> old/pass3/. Approach 4: pass 4 --moves 440000 (log place_pass4.log).
- 15:46 approach 4 (pass 4 --moves 440000) REJECTED: best s9 115.64 (old/pass4). approach 5 (grid 0.05 route of p3 s1) REJECTED 105.81. pass 3 restored then re-moved to old/pass3 for approach 6: pass 5 --moves 110000 --crossing-weight 4.
- 15:48 approach 6 (pass 5 crossing-weight 4) REJECTED (best 116.78). 3 consecutive failures -> stop optimising. Kept placement: pass 3 s1 -> final.kicad_pcb sha 865d5cb2ade374605c8e6703a11fb1da1f920533eefee574045a468b239aec1c. final_route (pass-1 arm B) -> final_route_old2. Running shipping chain plan_armB.sh in final_route/.
- 15:49 routed.kicad_pcb (final_route/s4_iter2 copy) sha 4e7d1e9d950fd961c0d7d7a1a3ba229dc187bbd34f7b9339f043a46dc7bdc05b: board_score blocking 0, vias 0, copper 105.52, seg 26; check_complete DONE; check_connected/check_drc/kicad_drc_compare clean. Next: §3.9 labels + silk, fill_for_delivery, verifier.
- 15:49 delivered.kicad_pcb sha 0729dc6c5618cf8659e017b9140d27f468b09760986554278e5906b44f9d6533 (labelled silk 10->0, filled). board_score blocking 0 vias 0 copper 105.52 seg 26. Verifier call 1 launched (verdict_1.txt).
- 15:54 verifier call 1 PASS (verdict_1*.txt). grade.py done=true (grade_output.txt). DONE marker written. Ledger closed (--final, stop 1, 73 rows). measure.py -> measure_output.txt. REPORT.md write REFUSED by harness -> content goes in final reply, no REPORT_DONE. TOOL_GAPS.md written (5 entries).
