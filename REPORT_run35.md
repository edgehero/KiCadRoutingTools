# run 35: esp_prog, /pcb-free-agent full, from a pile

**Result: DONE, verifier PASS on the first call.** Final board
`wk/run35/final.kicad_pcb`, sha256
`1558fcc61c148d28ed9fa2b9b931d0f15f0e6fd1ce67d62d9a2a0e5efe4ac72f`.

| DONE condition | measured |
|---|---|
| board_score blocking | 0 (unrouted 0, broken 0, drc 0, floorplan 0, assembly 0, undersized 0) |
| check_complete | DONE (impedance, length, net_widths UNEXAMINED: the board declares none) |
| check_connected | all nets connected |
| check_drc --baseline input --clearance-margin 0.1 | 0 violations |
| check_floorplan --intent | 0 errors, 1 warning |
| check_assembly | buildable |
| quality | 36 vias, 339.41 mm copper, 250 segments |

Input: `esp_prog_unplaced.kicad_pcb` (run 30's), all 18 pad-bearing parts piled
off the outline, 0 tracks, 0 vias. Intent rebuilt with the current tree from
the design brief (`build_intent.py`).

## Stop rule

After DONE, two bounded rounds of re-routes. Round 1 (3 variants) improved
nothing; round 2's best (grid 0.05 plus a scoped /EN re-route) cut vias 37 -> 36
(2.7 %). Two consecutive rounds under 5 %: stop.

## Floors

route.py: `Design rules [--escalation fab, --fab-tier auto]: 15 feature(s) on
5 net(s) delivered below the requested size (smallest track width 0.127 mm,
smallest via diameter 0.25 mm)`. The verifier counts 12 shipped features below
the project's recorded original floors (track 0.3, via 0.5, drill 0.3): 2
tracks at 0.127, 6 vias at 0.25/0.15 (filled and capped, in pads), 1 via at
0.325/0.225, 3 vias at 0.45/0.2. `check_complete --authored-from` lists none of
them.

## Timeline (wall clock)

- 04:53 staged; placement: connectors + fiducials placed and locked,
  `place_seed` x4 seeds, then hand poses for the proximity claims
- 04:58 legal placement, 0 intent errors
- 05:00 first routed board (blocking 1: GND at C3/CON1)
- 05:03 first DONE (repair_planes + delete-only prune)
- 05:09 final board (36 vias)
- 05:12 verifier PASS

## What worked, what didn't

- `place_seed` does not search the proximity claims (known); five hand
  `place_pose --snap` rounds satisfied all six.
- `place_pose --snap` applies to ONE pose op per call; a multi-op call
  silently skips snap and then refuses.
- `repair_planes` left 3 same-coordinate duplicate GND segments (one at a
  different width) and route.py a dangling via; `check_complete` refuses
  them as weird copper, and no tool removes them. `wk/run35/prune.py` did
  (delete-only, gated by check_weird).
- Re-route variants: via-cost 500/1000/200, layer-costs, grid 0.05: all
  blocking > 0 on their own; grid 0.05 + a scoped /EN re-route was the win.

## Tool gaps (for the film, fixed in PR #1091)

- the stage3d camera fitted the whole film at once, so the board filled a
  third of its box;
- band record labels printed under the caption;
- U2's footprint-owned tab copper flashed red as a rip at the pile.
