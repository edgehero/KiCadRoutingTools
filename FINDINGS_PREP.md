# gpm candidate findings from prep (pin bda59fa0). Each stays unverified until a separate verifier re-runs it.

1. **The placement writer crashes on a KiCad 6/7 text `(at x y unlocked)`** (medium; gp14 hit it and never filed it).
   - **Where:** `py_placer/placement/writer.py:296` (`rotated`) reads the token after x y as an angle, giving
     `ValueError: could not convert string to float: 'unlocked'`.
   - **Hit:** daplink's original KiCad 7 file (`wk/gpm/_src/daplink/orig/daplink.kicad_pcb`, 4 `unlocked` tokens).
     The file is piled through `make_unplaced.py`. place_simple and place_pose write through the same writer.
   - **Repro (from krt-gpm):**
     `strip_copper_only.py wk/gpm/_src/daplink/orig/daplink.kicad_pcb /tmp/s.kicad_pcb && make_unplaced.py /tmp/s.kicad_pcb /tmp/p.kicad_pcb`.
   - **Campaign workaround (as in gp14):** the source was re-saved through pcbnew 10.0.7 (`_src/daplink/daplink.kicad_pcb`).
   - **Upstream:** no issue (gh searches "unlocked _TEXT_AT", "unlocked angle writer": 0).
2. **build_router.py decides "this checkout differs from main" against `origin/main`** (low).
   - **Effect:** on a fork clone, `origin` is the fork and its main is stale, so a clean upstream-main worktree
     always builds from source and never downloads the release binary.
   - **Where:** `build_router.py:405` (`('origin/main', 'main')`).
   - **Hit:** here (origin = edgehero, 1209 commits behind). The from-source build is correct, only slower, and it
     needs a Rust toolchain.
3. **make_unplaced cannot unlock a KiCad 6 footprint lock** (medium).
   - **What happens:** KiCad 6 writes a lock as `(footprint "X" locked (layer ...))`. `_unlock`
     (`.claude/skills/plan-pcb-placement/scripts/make_unplaced.py:181-188`) only removes the KiCad 7+ `(locked yes)`
     child. So it prints `FAIL: meant to unlock ['U4'], unlocked [], still locked ['U4']` and exits 1, after having
     WRITTEN the pile with the part still locked and moved.
   - **Hit:** esp_rust_board (U4, the board's own `Rust_Board` footprint) and uecg (E+1, E-1). Both are KiCad 6
     (20211014) corpus boards, staged from `wk/gpm/_src/<stem>/orig/`.
   - **Workaround:** a pcbnew 10.0.7 re-save converts the locks to `(locked yes)`.
   - **To check:** whether `place_pose unlock` and the parser's lock reading have the same gap. The parser DOES
     read the lock, because the FAIL line names the part.
4. **A part that carries a milled window cannot leave the board outline** (medium/high for piles).
   - **The board:** tfgps01's D3-D7 (`Mlab_D:LED_1206_mill`) each draw a closed Edge.Cuts window. The parser calls
     them carried (`owns_board_outline False`), as #829 intends.
   - **The failure:** `writer.write_placed_output`'s tripwire (`py_placer/placement/writer.py:1343-1356`)
     fingerprints the outline through `kicad_parser.structural_outline_fingerprint`. That re-runs
     `footprint_outline_owners` on the AFTER text. A window moved outside the outline no longer "lies inside the
     outline the board draws without it", so it is reclassified as STRUCTURAL, unmasked, and the fingerprint
     changes: `OutlineOwnerMove: this write would have CHANGED THE BOARD OUTLINE`.
   - **The consequence:** make_unplaced cannot pile the board. A pile made by any other means would trip the same
     check in place_simple when the part moves back in, because the BEFORE text then has the window outside.
   - **Repro:** `strip_copper_only.py wk/gpm/_src/tfgps01/TFGPS01.kicad_pcb /tmp/s.kicad_pcb && make_unplaced.py /tmp/s.kicad_pcb /tmp/p.kicad_pcb`.
   - **Campaign:** tfgps01 was replaced by environment_sensor (Rob, 2026-10-23).
5. Not a bug, noted: twonkie's J1 draws the board boundary, and make_unplaced refuses it (`refuse: 1 footprint(s)
   draw the board boundary (J1)`). That is #829's design.
6. **route.py tracebacks on a missing input board** (low, UX). It prints the full #441 "NO .kicad_pro" banner first,
   and then the parser raises `FileNotFoundError`, a raw traceback, EXIT=1. There is no clean "input board not found"
   refusal. Seen in `14_imx6ulz_4l/final_route_old1/s6_route.log`: the teammate's chain pointed at a diff-step output
   that was never written.
   Second instance: 09_StickHub/final_route_old1/.log. A zsh-joined path 's3_pour s4_route s4.kicad_pcb' reaches route.py as a single name and fails the same way.
7. **fill_for_delivery's stored fill differs from KiCad's own refill on hatched zones** (low/medium, from the lead's
   compare of 20_sam9g25).
   - **The board:** `kicad-cli pcb drc` on `delivered.kicad_pcb` (stored fills) gives 8 `track_dangling`: 7 GND stubs
     on F/B.Cu (0.2-2.7 mm, e.g. (122.5, 67.3), (119.7, 77.2)) and the VBUS T-joint.
   - **With --refill-zones:** 1 (VBUS only). 0 unconnected either way.
   - **So** the delivered file's hatched GND fill leaves 7 stub ends in hatch gaps where KiCad's own refill reaches
     them. A user who opens the delivered board and runs DRC sees 7 dangling tracks the teammate's checks (refill)
     never showed.
   - **Repro:** copy `20_sam9g25/delivered.*` to a temp dir; `kicad-cli pcb drc delivered.kicad_pcb --severity-all`,
     with and without `--refill-zones`. check_weird and check_orphan_stubs report clean.
   Third instance (same UX family): 07_One-Air-Max/try4_route/run_clean.log. A --power-nets / --power-nets-widths length mismatch (1 vs 27, a shell-joined argument) raises a raw ValueError traceback from batch_route (route.py:2962) instead of an argparse error.
8. **Tracked docs quote a corpus board's source layout values** (low, test hygiene, found by the daplink teammate).
   `docs/floorplan-intent.md:671-676` cites daplink's J2/J3 `{7.0, 7.4}` and P1 band values from an earlier
   hand-written intent. Any agent placing daplink from scratch can read the source's mechanical answers in the repo's
   own docs. The teammate disclosed it, and says its values came from the GCT drawing and the footprint before it
   reached that paragraph. Campaign: disclose it, and suggest that board-specific examples in docs use a fixture
   board, or that the campaign fence lists docs that name the board.
- CORRECTION (2026-10-23, after the audit): #8's numbers (J2/J3 6.46, P1 0.50) are gp14's AI-placed daplink bands, not the human board's (human: J2/J3 9.17, P1 0.025, graded with the same rows). See AUDIT.md.
