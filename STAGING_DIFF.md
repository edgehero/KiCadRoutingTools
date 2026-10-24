# gpm staging vs gp14 (pin 8328f157 -> bda59fa0)

Staged inputs of the 14 boards, by sha256 against gp14's `_truth/<stem>/stage.json`.

| board | same | differs | only gp14 | only gpm |
|---|---|---|---|---|
| CM5_MINIMA_3 | 4 | intent.json | - | - |
| One-Air-Max | 3 | One-Air-Max.design-brief.json, intent.json | - | - |
| StickHub | 4 | intent.json | - | - |
| complex_hierarchy | 4 | intent.json | - | - |
| daplink | 3 | intent.json | - | - |
| ecc83-pp_v2 | 4 | intent.json | - | - |
| glasgow_revC | 4 | intent.json | - | - |
| imx6ulz_4l | 5 | intent.json | - | - |
| interf_u | 4 | intent.json | - | - |
| multichannel_mixer | 4 | intent.json | - | - |
| pico_ice_rev3 | 4 | intent.json | - | - |
| rp2350_fpga_eensy_prePlane | 4 | intent.json | - | - |
| sonde_xilinx | 3 | intent.json | - | - |
| steppenprobe | 3 | intent.json, steppenprobe.kicad_pcb | - | - |

**`intent.json` differs on every board, as expected.** It is re-emitted at main, and check_floorplan's
edge-clearance fallback moved from 0.55 to 0.2 at main.

The two other differences:
- **steppenprobe.kicad_pcb: 249 lines, every one a pad `(at x y a)`.** gp14's pile had pads turned against their
  body: the writer skipped pads carrying KiCad 6's `locked` token (gp14 #8, fixed by #1305). At main they now
  keep their angle relative to the footprint, so `pads_turned` is 0 and this pile is the correct one. gp14's
  teammate started from the damaged pile.
- **One-Air-Max.design-brief.json: one new edge claim, DC1 (the DC jack) at the south edge.** The rule is unchanged
  (fa10-decl-v1). Main's `part_class` now classifies DC1 as an `edge_receptacle` seated within tolerance of the
  south edge, where gp14's did not. The claim is kept, because the rule runs on the tools at the pin, and it is
  disclosed in the post.

**Board 17.** Board 17 was to be tfgps01. It cannot be piled at main (prep finding #4), so on Rob's call
environment_sensor takes its place.

**Re-saves.** esp_rust_board and uecg (KiCad 6) were opened and saved once by pcbnew 10.0.7 before staging
(prep finding #3), as daplink was in gp14.
