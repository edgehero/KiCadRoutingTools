# gp14 campaign assets

The gp14 campaign ran KiCadRoutingTools' `grouped-placement` branch, pinned at
**8328f15756d3f8d943adc81663ef93dbd45caeea**, on 14 boards. These were fa10's ten
plus daplink, steppenprobe, pico_ice_rev3 and imx6ulz_4l. Each board was run by one
Claude teammate following `/plan-pcb-placement full`, starting with every part in a
pile off the board. The write-up is in discussion #118.

## Layout
- `media/NN_STEM/` holds one folder per board:
  - **Films:**
    - `film_andy.gif` / `.mp4`: `place_movie` of the chosen seed, followed by `route_movie` of the final route.
    - `film_3d.gif` / `.mp4`: `movie3d` of the chosen seed.
    - `film.gif` / `.mp4`: fa10's `make_film` from the converge ledger.
  - **Images:**
    - the 3D views `iso_start.png` (the pile), `iso_final.png` (ours) and `iso_ref.png` (human);
    - `compare_F.png` / `compare_B.png` (human vs ours, per side);
    - `place_*_{F,B}.png`.
  - **Reports:** the teammate's `REPORT.md` and `TOOL_GAPS.md`, `README.md` (what the teammate was given) and `CHOSEN.json`.
  - **Grades:** my independent grade (`grade_ours.json`, `summary.json`), `measure.json`, and `class_widths_final.json` where the board declares a net class wider than Default.
- `media/TABLE.md` and `media/metrics.json` hold the campaign table.
- `media/FINDINGS.md` has every finding as re-run by a verifier at the pin, with verdicts, causes and issue drafts. `media/FINDINGS_CLUSTERED.md` has the candidates as clustered from the teammates' TOOL_GAPS.
- `wk/gp14/...` holds the **repro inputs** that the issues cite, at the same paths. Copy `wk/` into a KiCadRoutingTools checkout at the pin and run the issue's command from the checkout root.
- `staging/` holds the campaign scripts: staging, the teammate prompt, the compare/grade/film scripts and the asset build. `staging/truth/` has each board's staging hashes and declarations.
- `GRADE_NOTES.md` is the lead's per-board re-grade notes. `LAUNCH.md` is the launch log. `PIN` records the pinned commit.

## Boards
The KiCad demo boards ship with KiCad. The corpus boards come from their public
open-hardware projects; StickHub is CC BY-NC-SA. `staging/boards.tsv` lists each
board's source file.
