# TOOL_GAPS -- gpm board 01 ecc83-pp_v2

Ranked by what each cost this run. None of them blocked DONE; the board was DONE
on its first full route (about 25 min after FIRST_CMD). The costs below are the
post-DONE optimisation laps and the hand-work around each gap. All commands run
from WT (`~/Documents/git/krt-gpm`) after
`export PATH="$HOME/.venvs/krt/bin:$PATH"`.

## 1. The seed judge runs ONE chain, but plan-pcb-routing tells a 2-layer THT board to route TWO arms and keep the better -- the judge then picks by the wrong arm's vias (skill instruction gap)

- **Tool / step:** `py_placer/judge_seeds.py` as SKILL.md §3.7 tells you to use it, with
  the "board's routing chain" in `judge_chain.txt`; plan-pcb-routing Step 8 ("A 2-layer
  through-hole board WITHOUT the buses") says to route `--layer-costs 1.0 3.0` (defaults)
  AND `--layer-costs 1.0 1.0 --via-cost 600` as arms and keep the better.
- **What it claimed:** pass 3 (`place_simple --moves 110000`), judged with the
  default-cost chain (`old/pass3_judge_armA/judge_pass3.log`): "best seed 9" -- quick
  vias 0, copper 126.84 mm, ahead of seed 1 (quick vias 0, copper 127.39) and of seed 7
  (vias 1, copper 109.82).
- **What was true:** the arm the run ships (arm B, 0 vias on every seed) ranks the seeds
  differently. Full arm-B routes of all six judged seeds (`expt/p3_s*_armB/r.score.json`):
  seed 1 **105.52 mm**, seed 6 108.89, seed 7 117.39, seed 5 120.03, **seed 9 122.01**,
  seed 2 147.43 -- all 0 vias. Re-judging the same seeds with the arm-B chain
  (`judge_pass3b.log`) names seed 1 (quick 107.27 mm). Keeping the judge's first answer
  would have shipped 16.5 mm (16%) more copper. The skill gives no rule for which arm the
  judge chain carries when the routing recipe prescribes two.
- **Reproduce:**
  ```bash
  R=wk/gpm/01_ecc83-pp_v2   # repro/judge3 and repro/judge3b hold copies of the six pass-3 seeds
  KICAD_ROUTE_TRACE=1 python3 -X utf8 py_placer/judge_seeds.py $R/repro/judge3/judge.json \
      --chain $R/repro/judge3/chain_armA.txt --intent $R/intent_run.json --jobs 3    # "best seed 9"
  KICAD_ROUTE_TRACE=1 python3 -X utf8 py_placer/judge_seeds.py $R/repro/judge3b/judge.json \
      --chain $R/repro/judge3b/chain_armB.txt --intent $R/intent_run.json --jobs 3   # "best seed 1"
  ```
  (re-run 2026-10-23: the two calls print `best seed 9` and `best seed 1`.)
- **Cost:** one extra judge run and six full routes per pass to find it (minutes).
- **gh issue search:** `judge chain arm`, `judge_seeds chain` -- no issue covers it.

## 2. `analyze_power_paths` silently drops the 300 mA heater nets: a sink's current reaches a net only through a `power_in` pintype (silently wrong)

- **Tool / command:** `py_tools/analyze_power_paths.py` as `/analyze-power-nets` Steps 3-5
  use it: `classify_component(...)`, `trace_power_paths(...)`,
  `get_power_net_recommendations(...)`.
- **What it claimed:** after classifying P4 as `POWER_SOURCE` 300 mA (heater header), U1
  (ECC83) as `CURRENT_SINK` 300 mA and P3 as `POWER_SOURCE` 5 mA, exactly as the skill's
  Step 3d says: `paths = []`, recommendations `{'GND': 0.7}` -- "Routing Configuration
  --power-nets GND --power-nets-widths 0.7".
- **What was true:** the ECC83 heater (pins 4+5 tied, pin 9; 6.3 V parallel) draws
  300 mA through `Net-(P4-P1)` and `Net-(P4-PM)`, which by the tool's own table (under
  500 mA -> 0.7 mm) need 0.7 mm. Neither is named. Cause, read in the code:
  `trace_power_paths` builds its sink nets only from pads whose pintype is `power_in`
  (and sources only from `power_out` / OUT-named pins); U1's heater pins are `input` and
  P4's are `passive`, so the classification the skill asks for never reaches a net. The
  report prints the 300 mA sink under "Current Sinks" and then traces nothing, with no
  warning. I sized the heater nets by hand (0.7 mm IPC minimum, routed at the 0.8636 mm
  net class) and graded them with `--net-min-widths`.
- **Reproduce:**
  `python3 -X utf8 wk/gpm/01_ecc83-pp_v2/repro/analyze_power_heater.py`
  (prints `recommendations: {'GND': 0.7}` and `heater nets missing from the
  recommendations: ['Net-(P4-P1)', 'Net-(P4-PM)']`; input `repro/pile.kicad_pcb`).
- **Cost:** about 5 minutes (reading the tracer, sizing by hand). On a board whose
  current-carrying nets are not on `power_in` pins (valves, relays, motors, LED strings
  fed from headers) the route step would silently draw them at signal width.
- **gh issue search:** `analyze_power_paths power_in`, `analyze-power-nets heater`,
  `power net recommendations pintype`, `trace_power_paths`, `analyze_power` -- no issue
  covers it (#187 is unrelated dead-code cleanup).

## 3. `place_simple`'s default anneal (500 moves per part) leaves about 13% copper on the table on this small board (weak default, measured on one board)

- **Tool / command:** `py_placer/place_simple.py` at its default `--moves` (11 movable
  parts -> 5500 moves, 0.4 s a seed), as SKILL.md §3.6 runs it.
- **What it claimed:** pass 1's best seed (s4) objective cost 184.1; it routed DONE at
  0 vias / 121.6 mm (arm B), and nothing in the output says the anneal had stopped short.
- **What was true:** the same inputs at `--moves 27500` (pass 2) gave a best cost of 147.2
  and 116.37 mm; at `--moves 110000` (pass 3) a best cost of 144.8 and **105.52 mm**
  (0 vias, 26 segments vs 25); at `--moves 440000` (pass 4) a best cost of 146.2 and
  115.64 mm (no further gain; seed spread dominates). Each pass is 12 seeds, the same
  groups and intent. Pass 3 costs 7 s a seed against 0.4 s -- still under 30 s for the
  whole pass on this board. One board only, so this is a measurement, not a proposal to
  change the default.
- **Reproduce:**
  ```bash
  R=wk/gpm/01_ecc83-pp_v2; mkdir -p $R/repro/moves
  python3 -X utf8 py_placer/place_simple.py $R/fixed.kicad_pcb "$R/repro/moves/d{seed}.kicad_pcb" \
      --groups $R/groups.json --intent $R/intent_run.json --jobs 4 --json "$R/repro/moves/d{seed}.json"
  python3 -X utf8 py_placer/place_simple.py $R/fixed.kicad_pcb "$R/repro/moves/m{seed}.kicad_pcb" \
      --groups $R/groups.json --intent $R/intent_run.json --jobs 4 --moves 110000 --json "$R/repro/moves/m{seed}.json"
  ```
  (compare the `cost` lines; route seed 4 of the first and seed 1 of the second with
  `plan_armB.sh`'s route.py line to see 121.6 vs 105.52 mm.)
- **Cost:** three extra placement passes (2-6) and their judging/routing, about 15 minutes.
- **gh issue search:** `place_simple moves anneal`, `anneal budget moves` -- no issue.

## 4. `converge.py record` warns on every judged-seed row the skill tells you to record (noise)

- **Tool / command:** `python3 -X utf8 py_placer/converge.py record --ledger ... --board
  s<S>.kicad_pcb --kind placement --score-file s<S>_fast.score.json [--rejected]`, as
  the TASK and SKILL.md §5 rule 6 ask for EVERY judged seed.
- **What it claimed:** on every such row: `score payload carries no board_sha (pre-B4
  board_score, or hand-built JSON) -- the ledger cannot verify it grades THIS board`, and
  `INCOMMENSURABLE with iteration 0, the last accepted placement lap ...`.
- **What was true:** the payload is `judge_seeds`' own `quick_score` output for that
  seed; the tool that the skill prescribes writes no `board_sha`, so the ledger's
  identity check can never pass for the rows the skill requires, and the
  incommensurability warning fires on every judged seed by construction (quick 2 vs
  board_score). The rows are still written (exit 0, row count checked).
- **Reproduce:**
  ```bash
  R=wk/gpm/01_ecc83-pp_v2
  python3 -X utf8 py_placer/converge.py record --ledger $R/repro/ledger_try.jsonl \
      --board $R/s1.kicad_pcb --kind placement --parent $R/fixed.kicad_pcb \
      --lever "repro" --score-file $R/s1_fast.score.json
  ```
- **Cost:** none beyond reading the warnings.
- **gh issue search:** `converge record INCOMMENSURABLE` -> #1323 (closed: "converge
  record refuses the first board_score row after a quick_score row") is the same
  payload mismatch in its refusing form; `quick_score board_sha` -- no issue for the
  missing `board_sha`.

## 5. SKILL.md §3.9 calls bare `kicad-cli`, which is not on PATH on macOS, while the repo's own tools find KiCad (skill instruction gap)

- **Tool / step:** SKILL.md §3.9 step 1, `kicad-cli pcb drc <board> --severity-all ...`,
  and its fallback "Without `kicad-cli`, keep the board as it was and say the silk is
  ungraded."
- **What it claimed:** `which kicad-cli` -> `kicad-cli not found` in the prescribed shell.
- **What was true:** KiCad 10.0.7 is installed at
  `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`;
  `tests/stress/kicad_drc_compare.py` and `py_tools/fill_for_delivery.py` find it (and
  KiCad's python) by themselves through `py_router/kicad_locate.py` and ran fine with the
  same PATH. Followed literally, the skill would have shipped "silk ungraded" and kept 10
  KiCad silk violations (8 `silk_overlap`, 2 `silk_over_copper`) that the tidy removed.
  I added the app's MacOS dir to PATH.
- **Reproduce:** `which kicad-cli; python3 -X utf8 -c "import sys; sys.path.insert(0,'py_router'); import kicad_locate as k; print(k.describe_search())"`
  (prints `kicad-cli not found`, then `found: /Applications/KiCad/KiCad.app`).
- **Cost:** about 2 minutes.
- **gh issue search:** `kicad-cli PATH macOS` -- no issue covers it.
