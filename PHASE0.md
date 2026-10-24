# gpm Phase 0 (2026-10-23, pin bda59fa0): does everything work on this Mac?

| check | result |
|---|---|
| worktree | `krt-gpm` detached at bda59fa09496 (upstream main, v0.23.7 + #1363) |
| router | grid_router 0.23.7, built from source (build_router compares against origin/main = edgehero's stale fork: prep finding #2) |
| environment | see env.txt: python 3.13.16 venv, numpy/scipy/shapely/Pillow/ortools, KiCad 10.0.7 (pcbnew + wx + kicad-cli), node 26, ffmpeg 9, movie3d npm ci, headless shell 1169, **Google Chrome 156 installed**, so movie3d renders on Metal (ANGLE Metal, M5 Pro, about 50 ms a frame) |
| suite | `tests/run_all.py --jobs 8`: **894 passed, 0 failed, 0 skipped**, 457 s |
| staging | all 20 boards PASS the cleared gate. The 14 are byte-identical to gp14 except the intents, steppenprobe (correct now) and One-Air-Max's brief (STAGING_DIFF.md) |
| dry run (tigard, `e2e_tigard/`) | place_simple 12 seeds 59 s, judge_seeds 6 seeds 74 s with traces, final_route (planes + route) with redo manifest, beautify_labels, silk counts, fill_for_delivery, grade.py --mode full: all work. The board has no .kicad_pro, so its quick routes block 52; its full route reaches blocking 0 |
| films | film_seed (kept seed, pose_diff 0/89 differ) and film_flow (whole run via film_work.py, best = kept): both render, 116 s for both |
| compare | compare_board.sh ran end to end on the dry run. iso stills need the board in boards.tsv; they were tested on ecc83 (11/11 models) |
| controls | the human placement routed once by route.py on main, for all 20: DONE on ecc83, sonde, complex_hierarchy, mixer, am32_esc, icebreaker. Blocking: glasgow 13 (gp14 control 21), pico 8 (24), CM5 3 (6), interf_u 1 (2), rp2350 9 (8), imx6ulz 9 (4 of them DRC), sam9g25 22, uecg 3, esp_rust 2, environment_sensor 1. The rest are blocking 0 but check_complete INCOMPLETE |
