# fa10: 10-board /pcb-free-agent campaign

- Worktree: `C:/Users/rob/Documents/prive/git/krt-fa10`, upstream main **04a2c68d**, router 0.22.0, stage3d node_modules installed.
- Started 2026-10-06. Plan: `~/.claude/plans/create-a-worktree-from-twinkly-raven.md`.
- Two teammates at once (one board each); every timing is measured under that load, plus the control routes early on.

| # | board | layers | parts | status | result | vias ours / human / control | copper mm ours / human / control | wall | stop rule |
|---|---|---|---|---|---|---|---|---|---|
| 01 | ecc83-pp_v2 | 2 | 15 | finished (smoke test) | **DONE** (re-graded) | 0 / 0 / 1 | 195.6 / 219.1 / 164.18 | 48 min to final (59 min total) | 3 (plateau) |
| 02 | sonde_xilinx | 2 | 25 | finished | **DONE** (re-graded) | 0 / 3 / 18 | 713.57 / 637.8 / 556.2 | 1h18m | plateau |
| 03 | complex_hierarchy | 2 | 68 | finished | **DONE** (re-graded) | 7 / 0 / 14 | 1562.25 / 1265.7 / 1189.94 | 57.5 min to final | plateau (+1 round past it, disclosed) |
| 04 | multichannel_mixer | 2 | 114 | finished | NOT DONE, blocking 6 (GND islands 2 + same pad in 3 of 4 channels) | 198 / 29 / 145 (control blocking 0) | 3756.8 / 1959.3 / 1895.0 | 4h41m | STUCK (4 approaches failed) |
| 05 | interf_u | 2 | 24 | finished | NOT DONE, blocking 9 (10 with the Power-class GND width spec) | 435 / 84 / 213 (control blocking 5) | 6744.6 / 5101.5 / 4982.3 | 8h58m | BUDGET (10 h) |
| 06 | rp2350_fpga_eensy_prePlane | 6 | 61 | finished | **DONE** (copper-to-hole below the authored 0.25: disclosed) | 185 / 70 / see _cmp | 986.1 / see _cmp / see _cmp | 1h40m | plateau after DONE |
| 07 | One-Air-Max | 4 | 204 | finished | NOT DONE, blocking 6 = all net 0 (grader defect; KiCad 0 unconnected) | 357 / 410 / 252 (control blocking 11) | 4825.9 / 3740.7 / 3548.4 | 6h46m | 4 (net-0, unfixable by board change) |
| 08 | CM5_MINIMA_3 | 6 | 84 | finished | NOT DONE: blocking 1 (shared module origin) without the impedance spec, 42 with it (own-via antipad); connected, DRC clean | 232 / 444 / 261 (control blocking 5) | 2348.8 / 2785.8 / 2772.9 | 5h13m | 4 (measured floor) |
| 09 | StickHub | 2 | 90 | finished | **DONE** (re-graded) | 166 / 87 / 85 (control blocking 1) | 829.96 / 742.7 / 627.55 | 4h15m | plateau after DONE (verifier PASS on call 2) |
| 10 | glasgow_revC | 4 | 264 | finished (run-34 inputs) | NOT DONE, blocking 6 (re-graded); run 34: 15 | 1476 / 416 / 543 (control blocking 27) | 8955.6 / 4437.0 / 4385.4 | 6h48m | 3 (five approaches failed) |

## Staging findings (issue candidates)

- `strip_copper_only.py` keeps teardrop zones (complex_hierarchy 165) and length-tuning patterns (One-Air-Max 2, CM5 15) -- routing output that encodes the human copper.
- `check_floorplan --emit-intent` on a human board writes a sheet zone its own grade then rejects: CM5 `intent_zone_outside_envelope` (irregular outline), rp2350 `zone_containment`.
- `--decaps-from` withholds the decap limit on a human board it calls "not placed" because two footprints share an origin by design (CM5 Module301/302; rp2350).
- The edge-claim rule reads bounding-box bounds, so on an irregular outline (CM5, 287 vertices) a USB-C at a notch reads 15 mm from the edge.
- rp2350's human copper reports different-net contacts even at 0.05 mm clearance (pre-plane snapshot).
- `part_class` reads `DSUB...MountingHoles` footprints as mounting holes (design-agent finding, to confirm).

## Notes per board

- 01 ecc83: staged BEFORE the pile sanitiser existed, so its pile kept text angles that encode the human rotations
  (it had no local zones). Its final rotations match the human on 1 of 11 free parts (C1), and fence_audit is CLEAN,
  so the result stands, disclosed. REPORT.md was saved by the orchestrator from the teammate's reply (the harness
  refused the teammate's own write).
- Boards 02-10 were re-staged after the staging verifier's findings: local pours and rule areas under 25% of the
  board dropped, text angles reset, source paths redacted from intent.json.

## Queue

slot A: glasgow -> then the next board by the rule "never two hard boards at once".
Remaining: complex_hierarchy (easy), One-Air-Max (hard), sonde_xilinx (easy), CM5_MINIMA_3 (hard), interf_u (medium),
multichannel_mixer (medium), rp2350 (hard).
