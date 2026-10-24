# STATE 09_StickHub

FIRST_CMD: 2026-10-23T11:55:39Z

## Milestones (UTC)
- ~12:05 read skill/verifier/routing skill; board = 2-layer 16.5x40 USB hub (XR22417 LQFP-48 on B, 7 JST-SH + USB-A PCB plug at declared poses)
- groups.json (13 groups); intent_run.json = intent.json + edge_connectors C38 north (judgment: Board_Edge electrolytic can)
- ~12:08 pass 1 (defaults): all 12 seeds floorplan errors; C38 classless edge row ignored by place_simple -> REJECTED, files in old/pass1/
- ~12:12 pass 2 (C38 row class connector_affinity + mating_face +y; --decap-limit-weight 40): all seeds 1-7 decap misses (differ per seed)
- s7 hand-repaired (C11 0.087 mm) -> 0 floorplan errors, buildable; judged alone: quick blocking 39 (rails broken only)
- final.kicad_pcb = s7 (sha dd8a585d2c96dd3f2be06a92fb37effd83b77b4487950262fb761972e1947349); placed_from/, CHOSEN.json
- ~12:18 full route chain final_route/StickHub_plan.sh (route_plan_check 17/17 ok)
  - s1 route_diff: 5/8 pairs coupled, 3 single-ended followup
  - s2 signal route ('*' '!GND'): 6 open (+1V8, /LC, /LED2, /LED7, Net-(D15-1), VBUS_SENSE), 96 vias
- ~12:21 running s3 bare pour + s4 route '*' + s5 iteration (logs final_route/s3_pour.log, s4_route.log, s5_iter.log)

## Best board
- placement: final.kicad_pcb; routed: none yet

## Next
- after s5: GND-via/stitch tail (s6) + closing route (s7), then board_score/check_complete
- 12:23 chain A (pour-last) final_route: closing route REVERTED by improvement gate; first routed board = final_route/s3_pour (blocking 40: 6 signal + GND 34)
- arms (wk/gpm/09_StickHub/arms/): B pour-first GND in main route -> blocking 8 (BEST so far, arms/B/s2.kicad_pcb); C grid .05+ripup5 14; D soft-cost 14; F ripup5 16; G failed-first 13
- approaches since B: #1 routing params (C/D/F) failed, #2 ordering (G) failed. classified: placement (failures at U1 escape faces; power group far north of plug J1, Net-(J1-Pin_1) runs the board length)
- 12:40 pass 3 (approach #3): place args --decap-limit-weight 40 --near-weight 10 (power near host); judge chain = arm B chain. pass 2 files in old/pass2/
- 12:45 pass 3: seeds 10, 3 floorplan-clean; judged both: s10 quick blocking 7 (KEPT), s3 51. final.kicad_pcb = s10 (sha b8b8c6c2bafd5eaa9ee1cd5037a4c349cbb0411771c3921463639b788b3699a1); old final in old/final_pass2_s7.*; CHOSEN.json pass 3
- final_route (pass-3 board, pour-first plan B): s0 bare pour (keep zones) -> s1 diff -> s2 route '*' -> s3 iter; running (logs final_route/s*_*.log). old chains: final_route_old1 (pass2 A, outline replaced), final_route_old2 (pass2 A)
- 12:44 final_route s2_route (pass-3 board): blocking 7; s4/s5 GND-via+stitch tail -> 6; s6 scoped lap (/LED3 /LED2 GND, rip /LED2) -> 3 (+5V J6.1, /LED3 R9, GND 1) = BEST: final_route/s6_led3.kicad_pcb
- laps s7 (grid .05), s7b (rip set), s8 ('*' pass) all >= 3 -> scoped-lap approach plateaued (approach #1 since best)
- +5V J6.1 hand join: check_join refuses every straight/under-body path (+3.3V F track at y=102.3, J6 pins 2/3, /U5D+)
- 12:55 arms H (power widths 0.3/0.5) + I (Step 2c strict small features) on pass-3 s1_diff, running
- 12:53 FINAL CHAIN (final_route, plan with Step 2c strict small features): s5_final blocking 0; check_weird soft joint -> check_join hand join -> final_route/s6_join.kicad_pcb = FIRST DONE (board_score 0, check_complete DONE, DRC clean). vias 151 copper 864.9
- next: short via-optimisation arms, then 3.9 (labels, fill), verifier, report
- 12:57 via arms: O3 (via-cost 150, stitch-only tail) 133 vias DONE after a +3.3V soft-joint check_join; O1/O2/O4/O5/O6 worse (plateau)
- 13:00 final_route = O3 chain re-run (deterministic, 133 vias) + join -> s6_join -> routed.kicad_pcb. next: 3.9 labels+fill -> delivered, verifier, report
- 13:01 delivered.kicad_pcb (labels kept: silk 4 -> 0; fill 38 -> 0 unconnected) sha dea19c19e394fd2ff104cae5299adb94086d7875860fc37ac5b35d940fe430cc
- 13:05 verifier verdict_1: PASS (connectivity, drc, spec). DONE marker written; ledger closed (--final, stop condition 1). grade.txt, measure.txt written. datasheets -> old/datasheets
- REPORT.md: the harness refused the write ("Subagents should return findings as text") -> full content returned in the final reply; REPORT_DONE NOT created (per TASK)

## Best board (FINAL)
- delivered.kicad_pcb sha256 dea19c19e394fd2ff104cae5299adb94086d7875860fc37ac5b35d940fe430cc: blocking 0, joins 0, vias 133, copper 907.16 mm, segments 1234
- no running jobs
