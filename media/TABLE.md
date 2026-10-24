| # | board | result (verifier) | gp14 | fa10 | vias ours / gp14 / human / control | copper mm ours / gp14 / human / control | crossings ours / human | wall ours / gp14 | agent / tools / waiting |
|---|---|---|---|---|---|---|---|---|---|
| 01 | ecc83-pp_v2 | DONE (PASS) | DONE (PASS) | DONE | 0 / 0 / 0 / 1 | 105.52 / 131.72 / 219.1 / 163.75 | 4 / 8 | 27 min / 1.0 h | 16 min / 10 min / 1 min |
| 02 | sonde_xilinx | DONE (PASS) | DONE (PASS) | DONE | 0 / 0 / 3 / 18 | 556.16 / 516.67 / 637.8 / 556.18 | 37 / 39 | 23 min / 30 min | 18 min / 5 min / 0 min |
| 03 | complex_hierarchy | DONE (PASS) | DONE (PASS) | DONE | 0 / 0 / 0 / 14 | 710.64 / 740.61 / 1265.7 / 1185.01 | 34 / 64 | 30 min / 30 min | 21 min / 8 min / 1 min |
| 04 | multichannel_mixer | DONE (PASS) | DONE (PASS) | blocking 6 | 42 / 70 / 29 / 140 | 1840.3 / 1964.22 / 1959.3 / 1869.88 | 104 / 105 | 1.2 h / 1.3 h | 35 min / 24 min / 12 min |
| 05 | interf_u | DONE (PASS) | DONE (PASS) | blocking 9 | 88 / 157 / 84 / 240 (ctl blocking 1) | 3834.05 / 4630.48 / 5101.5 / 5319.42 | 421 / 457 | 2.0 h / 1.1 h | 30 min / 54 min / 34 min |
| 06 | rp2350_fpga_eensy_prePlane | DONE (PASS) | DONE (PASS) | DONE | 173 / 152 / 70 / 131 (ctl blocking 9) | 929.26 / 995.18 / 846.7 / 1039.18 | 404 / 516 | 42 min / 54 min | 31 min / 9 min / 1 min |
| 07 | One-Air-Max | DONE (PASS) | blocking 1 (PASS) | blocking 6 | 169 / 225 / 410 / 255 | 2647.59 / 2824.74 / 3740.7 / 3482.34 | 367 / 673 | 2.9 h / 1.3 h | 1.1 h / 26 min / 1.3 h |
| 08 | CM5_MINIMA_3 | blocking 1 (FAIL) | blocking 1 (PASS) | blocking 1 | 201 / 217 / 444 / 267 (ctl blocking 3) | 2527.06 / 2962.33 / 2785.8 / 2826.71 | 558 / 755 | 2.5 h / 1.5 h | 1.0 h / 40 min / 51 min |
| 09 | StickHub | DONE (PASS) | blocking 1 (FAIL) | DONE | 133 / 132 / 87 / 86 | 907.16 / 773.42 / 742.7 / 628.1 | 175 / 186 | 1.2 h / 59 min | 44 min / 13 min / 15 min |
| 10 | glasgow_revC | DONE (PASS) | blocking 8 (FAIL) | blocking 6 | 763 / 869 / 416 / 544 (ctl blocking 13) | 4956.46 / 6115.67 / 4437.0 / 4466.33 | 1759 / 1352 | 1.9 h / 2.7 h | 41 min / 17 min / 53 min |
| 11 | daplink | DONE (PASS) | DONE (PASS) | - | 22 / 56 / 27 / 57 | 411.74 / 598.78 / 654.5 / 562.28 | 47 / 85 | 58 min / 27 min | 32 min / 18 min / 8 min |
| 12 | steppenprobe | DONE (PASS) | DONE (FAIL) | - | 123 / 110 / 79 / 126 | 1066.84 / 962.4 / 1233.3 / 1191.39 | 189 / 255 | 1.5 h / 5.0 h | 44 min / 40 min / 4 min |
| 13 | pico_ice_rev3 | blocking 3 (FAIL) | blocking 8 (FAIL) | - | 368 / 303 / 189 / 320 (ctl blocking 8) | 2606.79 / 2670.69 / 2300.4 / 2861.32 | 1268 / 1160 | 4.9 h / 1.3 h | 1.0 h / 18 min / 3.6 h |
| 14 | imx6ulz_4l | DONE (PASS) | DONE (FAIL) | - | 377 / 349 / 315 / 354 (ctl blocking 9) | 2496.77 / 3145.14 / 2579.1 / 2773.17 | 680 / 807 | 4.6 h / 3.1 h | 1.2 h / 2.9 h / 28 min |
| 15 | am32_esc | DONE (PASS) | - | - | 104 / - / 292 / 133 | 954.42 / - / 1036.6 / 1012.23 | 190 / 252 | 1.9 h / - | 40 min / 13 min / 1.0 h |
| 16 | esp_rust_board | DONE (PASS) | - | - | 81 / - / 216 / 104 (ctl blocking 2) | 985.55 / - / 878.6 / 1085.75 | 134 / 156 | 53 min / - | 29 min / 7 min / 17 min |
| 17 | environment_sensor | DONE (PASS) | - | - | 147 / - / 144 / 118 (ctl blocking 1) | 847.36 / - / 1000.4 / 929.37 | 205 / 279 | 59 min / - | 32 min / 21 min / 5 min |
| 18 | uecg | DONE (PASS) | - | - | 139 / - / 147 / 150 (ctl blocking 3) | 928.45 / - / 914.1 / 1149.24 | 133 / 167 | 1.2 h / - | 36 min / 23 min / 15 min |
| 19 | icebreaker_v10e | DONE (PASS) | - | - | 266 / - / 157 / 238 | 2688.88 / - / 2024.3 / 2061.18 | 602 / 680 | 2.1 h / - | 51 min / 20 min / 57 min |
| 20 | sam9g25 | DONE (PASS) | - | - | 355 / - / 440 / 589 (ctl blocking 22) | 4076.04 / - / 5845.9 / 5458.08 | 1291 / 1826 | 2.6 h / - | 49 min / 43 min / 1.1 h |
