# Run 37: StickHub again, with the #1094-#1099 fixes

Run 37 used the same input and route recipe as run 36: KiCad 10's StickHub demo, stripped, with every part piled off the board. J1, H1 and J2-J8 were locked at their human poses. The tools were PR #1097 at 3d55a329.

**Not a pure tool result.** The seeder still leaves the USB port capacitors C14-C20 unseated, and neither `--repair` nor `--reseat` could seat them (#1101). So the 20 port-column parts (D1-D14, C15-C20) were placed **by hand** at the human's poses. Everything else was placed by `place_seed` (seed 1 of 4), `--repair` / `--repair-decaps` and `place_pose --snap`.

| | human placement | run 36 | run 37 |
|---|---:|---:|---:|
| airwire crossings (placed board) | 186 | 365 | 309 |
| hpwl, mm (placed board) | 478.1 | 689.8 | 599.8 |
| U1/U2 decaps C1-C13 to a same-net pin, min / median / max mm | 1.39 / 1.52 / 2.84 | 2.11 / 5.07 / 9.84 | 1.50 / 2.86 / 12.12 |
| parts on J1's USB tongue | 0 | **8** | **0** |
| parts at 45° | 39 | 0 | 0 |
| board_score blocking | 1 | 24 | **15** |
| broken / unrouted nets | – | 24 / 0 | 12 / 3 |
| vias | 87 | 201 | 169 |
| copper, mm | 742.7 | 886.0 | 995.2 |

- **Crossings and hpwl** are `render_placement` metrics with no ignored nets.
- **Run 36's tongue count** is today's checker applied to run 36's placed board. Run 36 itself called that placement buildable.

## What the fixes did in this run

- **#1098:** 0 parts landed on the tongue. `check_assembly` now reports run 36's board as NOT BUILDABLE with the 8 parts named.
- **#1099(c):** every seed's exit line named the unseated parts ("7 part(s) UNSEATED ... C14 ..."), and `oob_pad_copper_gating_refs` listed the same parts.
- **#1099(a):** `--decaps-from` the human board armed a 2.18 mm decap limit. The median fell from 5.07 to 2.86 mm. Four caps are still 8.9-12.1 mm from a same-net pin without a `decap_distance` error, because the rule measures to the chip's pad box, not the pin (#1102).
- **#1099(b):** `--diagonal-rotations` placed nothing at 45° on any seed. It stays opt-in.

## The final board

`final.kicad_pcb`, sha256 `16c80c6bf30bad1e3995f5ef1e0b0c6fb17059986fecf78d644624fb77122b08`.

| check | result |
|---|---|
| board_score | blocking 15: 12 broken, 3 unrouted |
| check_drc `--baseline --clearance-margin 0.1` | 0 violations |
| check_assembly | buildable; 0 parts on the tongue; 0 pad copper off the outline |
| check_floorplan `--intent` | 0 errors |

## Found on the way (filed)

- **#1100:** `place_pose` accepted a new pad short because the conflict COUNT tied (C18 on D11). `check_assembly` caught it.
- **#1101:** the seeder never seats the port capacitors C14-C20.
- **#1102:** `decap_distance` measures to the chip's pad bbox, so a cap 12 mm from its pin passes a 2.2 mm limit.
- **#1103:** `--emit-intent` on a pile inferred 87 "edge connectors" from staging poses.

## Assets

- `stickhub_run37_stage3d.mp4`: 751 frames, 1400×788.
- `stickhub37_preview.gif`
- `stickhub37_frame_*.png`
- `compare_run37_F.png` / `compare_run37_B.png`: the placed board.
