# gpm audit: did every board start cleared, and did any run use the human design? (2026-10-23)

Asked by Rob after all 20 boards had run. Three independent checks, written fresh (not the stage gate),
each with a positive control that must fire on the human board. Scripts and full outputs: `wk/gpm/_audit/`.

## A. The start state (`audit_start.py`, census in `sexp_census.py`: raw-text, paren-balanced, no repo parser)

For all 20 boards, on the exact files each teammate was given:
- **Given inputs unchanged:** every staged file still hashes to `_truth/<stem>/stage.json`.
- **The pile:** 0 segments, 0 arcs, 0 vias, 0 zone fills, 0 board text, 0 drawings off Edge.Cuts,
  0 images, 0 locked footprints, and 0 parts with a pad inside the outline's bounding box (stricter than
  inside the outline). Positive control: every human board shows copper (54-5484 items), every part on the
  board, and its locks (up to 68 on icebreaker).
- **What place_simple read** (`placed_from/fixed.kicad_pcb`, kept pass and every old pass): 0 copper, and
  0 parts moved from their pile pose. Declared fixed poses are seated by place_simple itself.
- **Where the shipped route started** (`final_route/in.kicad_pcb`): 0 copper on all 20.

**Two exceptions:**
- **12 steppenprobe: 312 pad-level `locked` tokens.** KiCad 6 locks pads one by one,
  `(pad "1" smd rect locked (at ...))`. `make_unplaced` unlocks every footprint but leaves these, and the
  stage gate did not count them. The repo's parser ignores pad locks when deciding whether a part is locked
  (`kicad_parser.py:4546`), so all 84 parts were free to move. But the pile was not fully unlocked.
  **Redone** from a pile with the 312 tokens stripped (`_staging/strip_pad_locks.py`, stage step 3a). The
  gate now counts pad locks too.
- **15 am32_esc: MOTOR_MOUNT1 stays where it is.** It has no pads, no nets and no copper. It is the
  footprint that draws the motor's mounting holes into the board outline (5 Edge.Cuts items). Moving it
  would change the outline, which no step may do. This is correct, and disclosed.

Zone outlines (unfilled pour definitions) are kept on the boards that have them, as in gp14. They are
design declarations, not routing.

## B. Did any shipped board carry the human placement or copper? (`audit_copy.py`)

On each `delivered.kicad_pcb`, compared with the human board:
- **Parts at their human pose** (0.005 mm, 0.05°, same side): only the declared fixed poses (from
  `mechanical.json`) on all 20 boards. The one exception is am32's MOTOR_MOUNT1 above.
- **Segments identical to a human segment** (both ends within 1 µm, same layer): **0 on 18 boards.**
  imx6ulz has 24 (of 2361) and 34 vias at a human via (of 377). All 24 segments and 33 of the vias sit on
  the ball or ball-quad sites of U1 and U2, two BGAs whose poses are declared at their human position. The
  0.566 mm (0.4·√2) dog-bone to the centre of four balls is where both the designer and `bga_fanout` put
  the via. The last via there, and one on uecg, are chance coincidences on the 0.1 mm grid: different net
  and different drill in each case.
- Reference rate: main's router on the human placement itself (the control) matches 0-8 human segments
  per board. So even the human placement routed by our router does not reproduce the human copper.

## C. Downloads and forbidden reads (`audit_transcripts.py`: every tool call of the 20 teammates and their 29 verifiers)

- **Network:** every URL is a part datasheet or a distributor's part page, on 38 vendor and distributor
  hosts (ti.com, lcsc, diodes, gct.co, nordicsemi, ...). There is no GitHub, no project site and no corpus
  host. Every WebSearch query names a part. One library install: PyMuPDF on sam9g25, to read PDFs.
- **Not touched by any agent:**
  - `_truth`, `_src`, `_control`, `_cmp`, `_staging`;
  - `wk/gp14`, `krt-gp14`, `gp14-assets`, `krt-film`, `krt-gpm-oi`;
  - `kicad_files/`, `tests/fixtures/`, the corpus manifests;
  - the KiCad demo DMG (`kicad_dmg`, `/Volumes/KiCad`) and `~/Downloads`;
  - another board's folder;
  - discussion #118, and the bodies of #1296-#1360.
  No board history was read: every git call was `git status` or `git log --oneline`, a list of commit titles.
  The only `tests/stress` scripts run were `kicad_drc_compare` and `manifest_to_plan`, which fetch nothing.
- **Minor, disclosed:**
  - Five teammates read the memory note `mac-setup.md` (venv and KiCad paths).
  - One uecg verifier grepped skill text in the main checkout's `.claude/skills`.
  - Board 12 listed the names in `/tmp/claude-501/`.
  - Each board folder's `.fence-manifest.json` (written by `fence_audit create`) names the human board's
    path. Several teammates printed it, and none opened that path.
- **One exposure, smaller than it first looked: 11 daplink.** `docs/floorplan-intent.md:671-678` quotes daplink band values: J2/J3 about 6.46 mm and P1 0.50 mm. The same numbers are in a docstring at `py_placer/placement/connector_geometry.py:467`.
  - **They are not the human design's.** Graded with the same edge rows, the human board reads J2/J3 9.17 mm and P1 0.025 mm. The quoted numbers come from gp14's AI-placed daplink: the bands its teammate wrote by hand, which became #1301's worked example. My prep note #8 and the first-run teammate both called them "source" bands; that was wrong.
  - **First run:** it read that doc section (call #41, 16:21:49) before writing its J2/J3 bands (#45, 16:22:42), although its report says the opposite order. It derived 6.505 / 0.505 from the footprint geometry and the GCT drawing, and shipped J2/J3 at 6.63-6.73 mm and P1 at 0.505 mm. The human board has 9.17 and 0.025.
  - **Re-run anyway,** with the doc paragraph hidden for the run (`_staging/hide_doc_daplink.py`, restored afterwards). It wrote its bands at 20:15 and 20:53 UTC. It first met the same gp14 numbers in the connector_geometry docstring at 20:58 UTC, after both, while it fixed P1 after verifier call 1. It shipped J2/J3 at 6.01 / 6.49 mm and P1 at 0.505 mm.
  - main's docs, code and tests name daplink on 28 lines in 17 files (#1301, #1319, #1325 and others), and `tests/stress/manifest_set5.json` holds its GitHub URL. None of them gives a human pose.

Other tracked docs and skills name campaign boards as tool-behaviour examples: RP2350 and CM5 chip
classes, steppenprobe's #1318 necks, imx6ulz's DQS0 layers, glasgow's scattered-start result. None gives a
pose, an edge or a band.

## Redone

| board | why | first run (kept in `_superseded/`) |
|---|---|---|
| 11 daplink | read gp14's daplink band values in tracked docs before writing its own (not the human design's, it turned out) | DONE, verifier PASS, 20 vias |
| 12 steppenprobe | pile carried 312 KiCad-6 pad locks | DONE, verifier PASS, 140 vias |
