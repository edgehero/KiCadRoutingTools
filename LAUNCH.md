# gpm launch log (pin bda59fa0); 4 at once, at most 2 hard
| NN | board | hard | launched (local) | agent |
|---|---|---|---|---|
| 10 | glasgow_revC | H | 2026-10-23 11:07 | a964bcfb6275726ca |
| 14 | imx6ulz_4l | H | 2026-10-23 11:07 | a4f1da6f7635c30f3 |
| 13 | pico_ice_rev3 | | 2026-10-23 11:07 | ac91cc3b10f4f0ba6 |
| 12 | steppenprobe | | 2026-10-23 11:07 | a2ee3ab6ec865ea1d |

Queue (hard, longest first; at most 2 hard at once): 20 sam9g25, 19 icebreaker_v10e, 08 CM5_MINIMA_3, 07 One-Air-Max, 04 multichannel_mixer, 05 interf_u
Queue (easy/medium): 06 rp2350_fpga_eensy_prePlane, 09 StickHub, 15 am32_esc, 17 environment_sensor, 18 uecg, 01 ecc83-pp_v2, 16 esp_rust_board, 11 daplink, 02 sonde_xilinx, 03 complex_hierarchy
| 20 | sam9g25 | H | 2026-10-23 12:59 | a23c9fc0cd0c7fd43 |
| 06 | rp2350_fpga_eensy_prePlane | | 2026-10-23 13:14 | aa6ac7142aa097355 |
| 09 | StickHub | | 2026-10-23 13:56 | a81485256fdf5f1d0 |
| 15 | am32_esc | | 2026-10-23 15:09 | a966390cf95bea094 |
| 19 | icebreaker_v10e | H | 2026-10-23 15:35 | afc81249b52ec823a |
| 08 | CM5_MINIMA_3 | H | 2026-10-23 15:42 | a5fc8fbe747a2f6cd |
| 17 | environment_sensor | | 2026-10-23 16:02 | a67127cdf1bb03e35 |
| 18 | uecg | | 2026-10-23 17:03 | a1f88672ba5c80ed2 |
| 01 | ecc83-pp_v2 | | 2026-10-23 17:29 | a24e9932cf593aa5e |
| 07 | One-Air-Max | H | 2026-10-23 17:43 | a90b8045c6fafda90 |
| 16 | esp_rust_board | | 2026-10-23 17:56 | aa42c7fcd5ce8a31f |
| 04 | multichannel_mixer | H | 2026-10-23 18:14 | a817abdbc7a4bfb1a |
| 11 | daplink | | 2026-10-23 18:18 | a11ec6893f363f851 |
| 02 | sonde_xilinx | | 2026-10-23 18:50 | ad7e349275602493d |
| 03 | complex_hierarchy | | 2026-10-23 18:52 | ac484bf1c7fd9c158 |
| 05 | interf_u | H | 2026-10-23 19:25 | a8149862327d482a7 |
Controls were still running (sequential, background) at launch.
14 imx6ulz_4l STALLED 11:45-12:46 (~1 h, no transcript or file activity, no process running; a queued nudge was never picked up). Stopped and resumed from its own transcript 12:46 with a continue note. Disclose: ~1 h of its wall time is the stall.
10 glasgow_revC finished 2026-10-23 12:58 (DONE, verifier PASS; REPORT.md saved from the final reply; wall 1:49:42 per measure.py)
12 steppenprobe finished 2026-10-23 13:12 (DONE, verifier PASS on call 2; REPORT.md saved from the final reply; wall 2:05:07)
06 rp2350_fpga_eensy_prePlane finished 2026-10-23 13:55 (DONE, verifier PASS; REPORT.md saved from the final reply; wall 0:40:20)
09 StickHub finished 2026-10-23 15:07 (DONE, verifier PASS; REPORT.md saved from the final reply; wall 1:11:20)
20 sam9g25 finished 2026-10-23 15:34 (DONE, verifier PASS on call 2; REPORT.md saved from the final reply; wall 2:35:04; shipped chain uses --fab-overrides helpers/fab_track_floor.txt: track 0.1016, via 0.25/0.15, clearance 0.09)
14 imx6ulz_4l finished 2026-10-23 15:40 (DONE, verifier PASS on call 2; REPORT.md saved from the final reply; wall 4:34 incl. the ~1 h stall)
13 pico_ice_rev3 finished 2026-10-23 16:01 (NOT DONE, blocking 3 broken; verifier FAIL; REPORT.md saved from the final reply; wall 4:53)
15 am32_esc finished 2026-10-23 17:01 (DONE, verifier PASS on call 2; REPORT.md saved; wall 1:52:30)
17 environment_sensor finished 2026-10-23 17:27 (DONE, verifier PASS on call 1; REPORT.md saved; wall about 1:25)
19 icebreaker_v10e finished 2026-10-23 17:42 (DONE, verifier PASS on call 1; REPORT.md saved; wall about 2:07; the adapters were placed on the main board, a disclosed compromise)
01 ecc83-pp_v2 finished 2026-10-23 17:55 (DONE, verifier PASS on call 1; REPORT.md saved; wall about 0:27)
08 CM5_MINIMA_3 finished 2026-10-23 18:12 (machine DONE: blocking 0, check_complete DONE; verifier FAIL on J1 edge clearance (geometric) and ungraded diff-pair skew; REPORT.md saved; wall 2:31)
18 uecg finished 2026-10-23 18:17 (DONE, verifier PASS on call 3, resting on two spec re-declarations: IPC-minimum power widths, and the RF 50 ohm declaration dropped; REPORT.md saved; wall 1:12:46; one rm -f rule slip, disclosed)
16 esp_rust_board finished 2026-10-23 18:49 (DONE, verifier PASS on calls 1 and 2; REPORT.md saved; wall 0:51:33; 2 verifier spawns for 2 calls, disclosed)
11 daplink finished 2026-10-23 18:50 (DONE, verifier PASS on call 1; REPORT.md saved; wall 0:30:18; disclosed: docs/floorplan-intent.md:671-676 quotes daplink's source edge bands, a fence leak in tracked docs)
02 sonde_xilinx finished 2026-10-23 19:11 (DONE, verifier PASS on call 1; REPORT.md saved; wall 0:20:58)
03 complex_hierarchy finished 2026-10-23 19:20 (DONE, verifier PASS on call 1; REPORT.md saved; wall 0:28:18)
04 multichannel_mixer finished 2026-10-23 19:23 (DONE, verifier PASS on call 1; REPORT.md saved; wall about 1:10; routed at the board's own floors, authored DONE)
Queue empty: all 20 launched (19:25).
07 One-Air-Max finished 2026-10-23 20:37 (DONE, verifier PASS on call 2; REPORT.md saved; wall 2:52:16; verifier 1 FAILED it on silk-only bodies overlapping, which check_assembly did not gate)
05 interf_u finished 2026-10-23 21:21 (DONE, verifier PASS on call 2; REPORT.md saved; wall about 1:55; authored DONE). ALL 20 FINISHED.

## Re-runs after the start-state and cheating audit (AUDIT.md)
| 11 | daplink (redo: docs/floorplan-intent.md's quoting sentences hidden for the run) | | 2026-10-23 22:12 | acaa8bd59aaf8d539 |
| 12 | steppenprobe (redo: pile without its 312 KiCad-6 pad locks) | | 2026-10-23 22:12 | a9ad3d1477880e719 |
First runs kept in _superseded/ (both DONE, verifier PASS). Prompts byte-identical to the first runs'. docs/floorplan-intent.md is locally modified (hide_doc_daplink.py) until daplink finishes.
11 daplink (redo) finished 23:09 (DONE, verifier PASS on call 2; 22 vias, 411.74 mm; authored DONE; wall 0:56; REPORT.md saved). docs/floorplan-intent.md restored (git checkout) at 23:09.
12 steppenprobe (redo) finished 23:40 (DONE, verifier PASS on call 2; 123 vias, 1066.84 mm; Power class 0.3 met; USB skew 0.63; authored DONE; wall 1:27; REPORT.md saved; two verifier subagents for two calls, disclosed).
| 17 | environment_sensor (redo: MP1-MP3 now declared by the drill rule in derive_decl.py, after the 2026-10-24 hole audit) | | 2026-10-24 08:36 | a8c382543f032fe9a |
First run kept in _superseded/17_environment_sensor (DONE, verifier PASS, 101 vias; MP1-MP3 placed by the teammate's own judgment, 0.4-0.7 mm off the designer's holes).
17 environment_sensor (redo) finished 09:35 (DONE, verifier PASS on call 1; 147 vias, 847.36 mm; MP1-MP3 at the declared poses; wall 0:57; REPORT.md saved).
