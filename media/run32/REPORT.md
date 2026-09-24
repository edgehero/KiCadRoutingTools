# Run 32: glasgow_revC placed and routed from an off-board pile (router arm: built from source)

## Result, led by `blocking`

**The board is not finished. It is the best this run could make: 0 unrouted, 19 broken joins across 17 nets, 0 DRC at the routed clearance, and buildable.** Stop token **BUDGET**: 223 ledger rows against a budget of 100. The last 64 valid laps accepted one improvement.

| measurement (shipped board) | value | instrument |
|---|---:|---|
| board | `wk/run32/routed_c3.kicad_pcb` sha256 `90e24fc25d1f19878f4d361d4516b969f72ff0f301f8bbfb527ff4425cf25700` | produced by lap `K3_R9_it` (`route.py --nets '*'` + GND `repair_planes`, argv in `logs/K3_R9_it_argv.json`) |
| KiCad oracle, unconnected joins | **19**, over 17 nets | `kicad_unconnected.py --pairs-json pairs_final.json` (exit 4) |
| `blocking` | **30** = broken 19 + floorplan 11; unrouted 0, drc 0, undersized 0, assembly 0 | `board_score --intent` → `score_c3.json` |
| DRC at the routed 0.1 mm | NO VIOLATIONS (with `--baseline` the input; 307 vias in paste, all filled+capped) | `check_drc --clearance 0.1 --clearance-margin 0.1 --baseline` |
| assembly | buildable (blocking 0) | `check_assembly --clearance 0.2` |
| quality | 1271 vias, 9175 mm copper, 9065 segments | `board_score` |
| check_complete | **UNSOUND** (exit 5): BGA-escape copper below the board's ORIGINAL declared floors (track 0.2→0.0889, via 0.5→0.25, ring 0.1→0.05, hole 0.3→0.15) | `check_complete --authored-from frozen.kicad_pcb --intent` |

Open joins, BY NAME: +3V3 ×3, /D2, /~{ALERT}, /PKTEND, /xVBUS, Net-(U3-A1), Net-(U30A-IOT_172), /IO_Banks/QA1, QA5, QB2, QB3, QB5, DA3, DB7, Z4_P, Z5_P, Z7_N.

### Independent verification (fresh agent, never a fork; `verdict_*_c5.txt`)

| lens | verdict | what it found |
|---|---|---|
| connectivity | **FAIL** | the 19 joins above, re-derived |
| drc | **FAIL** | 2 track-to-NPTH-hole at J5's hole against the declared 0.25 mm copper-to-hole (Z1_P B.Cu short 0.049, QA6 In2 short 0.038). No route.py flag routes to this dimension |
| spec | **FAIL** | **net_widths: all 5 declared power nets run below their requested `--power-nets-widths` over 49.6–82.4 % of their length** (GND 49.9 %, +3V3 49.6 %, +1V2 82.4 %). The endgame laps re-neck power copper. floorplan 11 real. impedance/length UNGRADED (no target) |
| record (boundary) | PASS | ledger timestamps monotone; poses byte-identical placed_v3 → frozen_c3 → routed_c3 |

## The run, in one paragraph

Placement matched run31 by content hash, as intended: the same zone plan and seed 1. The loop then turned **three placement-shaped re-entries**, each triggered by a measurement:
1. U30's BGA escape vias landed in the pads of six back-side passives (13 pad-via, 8 in contact).
2. 17 signal pads sat in the board's F/B no-copper keepout band, which **no placement instrument models**.
3. The +3V3-plane map needed C79/C14/C33 re-seated.

Routing ran four bulk lineages and ~190 scoped laps. The lever that finally moved the board was **ripping the one rail or protected pair each net's router Hint names as the blocker, in its own lap** (27 → 21), then one more `'*'` pass (21 → 19). Two attempts at a better placement were measured and **refused**: local rearrangement (≤ −2.3 % hpwl, breaks gates) and four fresh seeds without the zone plan (all worse: hpwl 5952–6563 vs 5743).

## Against the human original

`glasgow_ref.kicad_pcb` ships with **no copper** (0 segments, 0 vias). `compare_to_original.py` says so itself ("REFERENCE-EMPTY"), so there is **no human routing bar** and no via/length comparison. The placement comparison, same instrument (`render_placement --json-out`), is:

| | human as-built | this run |
|---|---:|---:|
| airwire crossings | **1352** | 3750 |
| hpwl mm | **3640.9** | 5742.9 |
| courtyard overlap mm² | 70.05 | **23.69** (= the locked-part budget) |
| pad-conflict pairs | 10 | **6** |
| off-outline courtyards | 6 | 6 (the same locked parts) |
| U1↔U30 bus pin-order inversions | 96 | 142 |

The human wins decisively where it matters for routability: 2.8× fewer crossings, 37 % shorter wire. This run wins only on interpenetration. That gap is this run's main finding: the placement engine's arrangement, not the router, is what holds the board at 19. Every stranded pad tested PASSABLE on the copper-free board, yet four bulk lineages failed ~30 *different* nets each.

## Against prior runs of the same board

run31 (same input, published v0.22.1 router asset) ended its endgame at oracle ~25 (its journal §28). Its numbers were not re-graded with today's graders here, so treat that as a pointer, not a comparison. The two arms differ only as binaries, and this run's routing diverged mostly through **process**: bus-first ordering, the keepout re-seat and rail-blocker rips, not through the router build.

## Findings (tool and skill)

1. **Rule-area keepouts are invisible to placement.** check_assembly, place_pose legality, the render checklist, check_reachability, place_optimize and place_portfolio all ignore `board_info.keepouts`. 17 signal pads sat in the band with every gate green. It cost a whole routing cycle.
2. **Scoped laps without GND in `--nets` are judged on damage they may not heal.** The in-run finalize skips GND by plan, but the improvement gate counts the GND pads the lap cut. Every scoped signal lap before batch 5 was penalised this way.
3. **Power-net width is not durable across endgame laps** (verifier). 50–82 % of the power copper is below the requested width.
4. **The ledger's `parent_sha` is wrong under parallel lineages.** `record` takes the last accepted row as the parent, so interleaved lineages chain across each other. The movie's lineage was rebuilt from the chain scripts instead (`movie_chain.txt`).
5. **A lap script silently shifted arguments** (bash `read` collapses empty tab fields). 24 laps ran with the grid value as the rip set, and all 24 were recorded INVALID. `assert_cmd.py` now re-reads each lap's CMD line before judging it.
6. The placement half's forks report they **cannot dispatch subagents**, so every placement close-out was verified single-agent.
7. **The movie's 3D panel is gated on the wrong resolver.** `movie_panels.py:575` calls `resolve_models(board)` without `model_dirs(cli, board)`. On Windows the KiCad 10 library is found through the install, so the gate read 0/224 models and switched the panel off, while the render path (line 644) resolves 213/224. `--iso-allow-bare` works around it. Separately, `kir.model_dirs(resolve_cli(), b)` raises TypeError, because `resolve_cli` returns a tuple.
8. **`make_movie` holds every frame in RAM.** Per-segment route traces made about 6100 frames at 1400 px; the render reached 29.5 GB and was stopped at 0.9 GB free. The shipped movie reveals each step in chunks instead (trace-free copies of the chain). It also **skips copper-free boards**, so placement is absent from a make_movie chain; the placement stage was rendered with `make_film --camera auto` and joined in front.

## Waivers spent

| token | command | reason |
|---|---|---|
| place_seed seed-override (`--force`) | every `place_seed` pass (cycles 1 and 6) | `assess_placement` reads the pile as placed because 21 pinned parts span the outline |
| `--waive congestion:` | placement P-close (cycle 1) | hpwl of an unplaced pile is not a repair baseline |
| `--accept-unclosed ungraded` | `loop_driver --stage L5` | impedance/length/net_widths have no spec file on this board (default stackup, no length groups). The verifier then graded net_widths from the route argv and FAILED it |
| `--accept-unclosed fab_floors` | `loop_driver --stage L5` | a 0.8 mm-pitch BGA escape cannot be made at the declared 0.2/0.5/0.3 floors. Disclosed as UNSOUND above; the fab must confirm 0.0889/0.25/0.15 |

No `--accept-residue`, `--accept-congestion`, `--accept-unclassified` or `--accept-incommensurable` was spent.

## Audits at DONE (run_watch cheats)

* **fence**: quoted verbatim from `watch/cheats_shell.log`: "FENCE no control board found, so blindness was NOT verified -- that is not a pass". The watcher printed no exit code for it: it did not run a fence audit, because there is no control board. This is not a blind or perturbed subject. (This line was sharpened after REPORT_DONE, because the report audit flagged the earlier paraphrase.)
* **provenance**: exit 5, UNPROVEN. The work dir was not staged by a stager, so there is no manifest to check.
* The watcher's SCOPE/FLOOR lines are the sanctioned endgame levers (single-net `--nets`, `--rip-existing-nets`) and the final DRC at the routed 0.1 mm. One SCOPE line is **my error**: the `--final` row's `lever_argv` has `--nets *` shell-globbed into repo filenames, so it is not replayable. The true argv is `logs/K3_R9_it_argv.json`.

## The ledger, by kind

223 rows: **198 completion, 16 placement, 6 systemic, 3 classification**. 40 accepted, 183 rejected, of which 24 were INVALID (the broken batch 5).

## Cost

| agent | subagent_tokens | tool uses |
|---|---:|---:|
| placement half (fork) | 277,958 | 57 |
| routing half (fork, 16 resumptions; last reported) | 580,534 | 262 |
| P4 six-part re-seat | 241,120 | 30 |
| P4b keepout re-seat | 350,962 | 61 |
| P5 local re-arrangement (refused) | 335,359 | 18 |
| P6 fresh seeds (refused) | 358,204 | 20 |
| P4c C79/C14/C33 re-seat | 384,074 | 45 |
| end-to-end verifier (sonnet) | 248,840 | 75 |

`cmd_timing.jsonl` (`cmd_timing_report.md`): 1475 wrapped commands, **tool time 39:30:27** summed and **31:38:53 wall**; the lineages ran in parallel. The three longest steps are the bulk routes: K3A 2:25, D5 1:58, K3B 1:38. Most of the rest is ~5–20 min scoped laps (route plus GND repair plus oracle).

## Artifacts

`routed_c3.kicad_pcb` (+ `.kicad_pro`), `movie/run32_full.mp4` / `movie/run32.gif` (placement glide, then routing step by step with the 3D panel; lineage in `movie_chain.txt`), `movie/run32.mp4` (the first, 17-minute per-segment cut, without the 3D panel), `movie/iso_final.png` / `iso_start.png` / `iso_ref.png`, `run_pair.png`, `close_sheet.png`, `verdict_*_c5.txt`, `ledger.jsonl` (final row 222), `DONE`, `journal.md`.
