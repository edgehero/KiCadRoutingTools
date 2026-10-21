# gp14 launch log (pin 8328f157); 4 at once, at most 2 hard
| NN | board | hard | launched (local) | agent |
|---|---|---|---|---|
| 10 | glasgow_revC | H | 2026-10-20 21:00 | a3045c05f4d141de9 |
| 01 | ecc83-pp_v2 | | 2026-10-20 21:00 | a231a9921635d555b |
| 14 | imx6ulz_4l | H | 2026-10-20 21:00 | a570e663927e65439 |
| 11 | daplink | | 2026-10-20 21:00 | a2892b4a387164fdd |

Queue (next free slot takes the first that keeps <=2 hard): 05 interf_u H, 02 sonde_xilinx, 07 One-Air-Max H,
12 steppenprobe, 08 CM5_MINIMA_3 H, 03 complex_hierarchy, 04 multichannel_mixer H, 13 pico_ice_rev3, 09 StickHub,
06 rp2350_fpga_eensy_prePlane
| 02 | sonde_xilinx | | 2026-10-20 21:28 | a96bb2be8a0fd3b84 |
11 daplink finished 2026-10-20 21:28 (DONE)
02 sonde_xilinx finished 2026-10-20 21:59 (DONE)
| 12 | steppenprobe | | 2026-10-20 21:59 | ac582ab05a06ea53a |
01 ecc83-pp_v2 finished 2026-10-20 22:02 (DONE)
| 03 | complex_hierarchy | | 2026-10-20 22:02 | a39e8be646b4f0f46 |
03 complex_hierarchy finished 2026-10-20 22:32 (DONE)
| 13 | pico_ice_rev3 | | 2026-10-20 22:32 | a6982e5ce2845968b |
10 glasgow_revC finished 2026-10-20 23:44 (NOT DONE, blocking 7)
| 05 | interf_u | H | 2026-10-20 23:44 | a4ec6d6da2cc210c3 |
13 pico_ice_rev3 finished 2026-10-20 23:53 (NOT DONE, blocking 8)
| 09 | StickHub | | 2026-10-20 23:53 | a753b787548742901 |
14 imx6ulz_4l finished 2026-10-21 00:03 (machine gates DONE blocking 0; verifier FAIL: DDR3 pair skew)
| 07 | One-Air-Max | H | 2026-10-21 00:04 | adab3f1b77bd8630a |
09 StickHub finished 2026-10-21 00:51 (NOT DONE, blocking 1)
| 06 | rp2350_fpga_eensy_prePlane | | 2026-10-21 00:52 | a7e2d474e2a43f058 |
Queue now: 08 CM5_MINIMA_3 H, 04 multichannel_mixer H (both wait for a hard slot: interf_u or One-Air-Max)
05 interf_u finished 2026-10-21 00:53 (DONE, verifier PASS)
| 08 | CM5_MINIMA_3 | H | 2026-10-21 00:53 | a53e4f71b650e6868 |
07 One-Air-Max finished 2026-10-21 01:19 (DONE, verifier PASS)
| 04 | multichannel_mixer | H | 2026-10-21 01:19 | a68b24cacf8fe9d28 |
Queue empty: all 14 launched.
06 rp2350_fpga_eensy_prePlane finished 2026-10-21 01:46 (DONE, verifier PASS; placed with helpers/place_simple_frame_fix.py)
08 CM5_MINIMA_3 finished 2026-10-21 02:21 (DONE, verifier PASS)
04 multichannel_mixer finished 2026-10-21 02:37 (DONE, verifier PASS x2)
12 steppenprobe STALLED 20:46Z-00:44Z (~2 h): a Bash call (with rm -rf) never executed (likely an unanswered permission prompt); stopped and resumed 2026-10-21 02:43 with a note. Disclose: ~2 h of its wall time is the stall.
12 steppenprobe finished 2026-10-21 03:00 (NOT DONE, blocking 5 net_widths; ~2 h stall)
