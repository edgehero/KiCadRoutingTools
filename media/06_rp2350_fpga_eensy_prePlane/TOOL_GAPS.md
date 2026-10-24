# TOOL_GAPS -- gpm 06 rp2350_fpga_eensy_prePlane

Ranked by what each cost this run. Every command runs from WT (`~/Documents/git/krt-gpm`) with
`export PATH="$HOME/.venvs/krt/bin:$PATH"`; `D=wk/gpm/06_rp2350_fpga_eensy_prePlane`. Inputs the repros need are
copied into `$D/repro/`.

## 1. place_simple: all 12 seeds leave a decap_distance error, so the skill's §3.6 path judges ONE seed

- **Tool / command:** `python3 -X utf8 py_placer/place_simple.py $D/fixed.kicad_pcb '$D/s{seed}.kicad_pcb' --groups $D/groups.json --intent $D/intent_run.json --jobs 4 --json '$D/s{seed}.json'` (the skill's default pass), then SKILL.md §3.6 "When no seed can be judged".
- **What it claimed:** `place_simple` prices the intent's decap limits (`decap limits priced: 46 term(s)`), and the skill says a seed with a floorplan error "cannot be DONE as placed"; when every judged seed carries one with a different part in each, it says to hand-repair the FIRST seed judge.json names and "judge it on its own".
- **What was true:** 12 of 12 seeds carried 1-7 `decap_distance` errors, a different cap in each (s9 C17 1.51 mm, s6 C11 2.00, s2 C18 1.3103 against a 1.3073 limit, s3 C5 4.92, s7 C23 1.89 + C7 1.40, s4 C10 1.31 + C23 1.32, against `decaps.max_distance_mm` 1.3073). Followed literally, the 6-seed judge collapses to one seed, which throws away the selection the skill's own measurements credit the judge with. I repaired five more by hand to judge them (s7, s6, s2, s4; s3 could not be repaired): 7 `place_pose` calls, of which 2 were refused (s3 C5: every candidate within 2 mm stacks with C7; s4 C10) and 2 produced a COURTYARD-BLOCKING pair (s2 C18/U2 0.52 mm2, s4 C23/U2 0.30 mm2) that I then had to undo and redo as 0.05-0.07 mm nudges. Outcome: s9 still ranked first, so the extra judging changed nothing here, but the skill gives no way to know that without doing it. No tool repairs a `decap_distance` finding (the `--repair-decaps` of #1188 is gone); each repair is a hand-computed `place_pose set ... --near`.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py $D/repro/seeds/fixed.kicad_pcb "$D/repro/seeds/s{seed}.kicad_pcb" --groups $D/repro/seeds/groups.json --intent $D/repro/seeds/intent_run.json --jobs 4 --json "$D/repro/seeds/s{seed}.json"` -> every seed line ends `N floorplan error(s) (decap_distance)`, N >= 1, and judge.json's WARNINGs say each judged seed "cannot be DONE as placed".
- **Issues:** `gh issue list --search "judged with floorplan errors every seed"` -> #1296 (closed, title only read: the judge used to rank seeds with floorplan errors; judge.json now names clean seeds first). Nothing covers "no seed is clean" or a decap-repair tool.

## 2. route.py: a net boxed in at grid 0.1 that a 6-second grid-0.05 lap routes; the in-run rescue never tries the finer grid

- **Tool / command:** `py_router/route.py ... --nets '*' --track-width 0.0762 --clearance-ceiling 0.09 --via-size 0.25 --via-drill 0.15 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 1.0 1.0 --no-bga-zones --max-ripup 5 --power-nets ...` (the chain's route step; the full command is line 6 of `$D/final_route_old1/redo_commands.sh`).
- **What it claimed:** `/RP2354A/FPGA.~{STATUS}` failed: `Boxed in at this geometry after 5019 iteration(s) (grid 0.1, clearance 0.09, track 0.0762 mm)`, `no rippable blockers found`; the hint offered `--grid-step 0.05 --clearance 0.15 --track-width 0.15` (a WIDER clearance and track than the run's own 0.09/0.0762). Its final reconciliation retried with rip authority over `/T8F49I2X/PIN.4` and failed again; the two iteration passes were reverted by the improvement gate, unchanged.
- **What was true:** `py_tools/check_reachability.py ... --pad U2.A4` -> `PASSABLE at track 0.0762mm (margin +3987.9 um)`; with the routing in place `CAGED (margin -75.6 um) ... ROUTED COPPER cages this pad ... a ROUTING finding`. A scoped lap at `--grid-step 0.05` (same flags, `--nets '/RP2354A/FPGA.~{STATUS}' GND +3V3`) routed it in about 6 s with no other change: blocking 1 -> 0. A rip lap of the hinted blocker at grid 0.1 failed and broke a second net (`/RP2354A/FPGA.MOSI`, reverted). The same signature recurred on another placement (`/T8F49I2X/PIN.6`, arms/v4_qfn: grid-0.05 lap closed it). The engine has the lever and the measurement but never pairs them.
- **Repro:** `python3 -X utf8 py_router/route.py $D/repro/status_s4_diff.kicad_pcb $D/repro/status_out.kicad_pcb --nets '*' --track-width 0.0762 --clearance-ceiling 0.09 --via-size 0.25 --via-drill 0.15 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 1.0 1.0 --no-bga-zones --max-ripup 5 --power-nets GND +3V3 'Net-(D2-K)' /VIN 'Net-(D2-A)' 'Net-(U7-SW)' +1V1 /RP2354A/1V1 'Net-(U6-VREG_LX)' 'Net-(U6-VREG_AVDD)' --power-nets-widths 0.7 0.7 0.7 0.7 0.7 0.7 0.5 0.5 0.5 0.3` -> `failed_single: ["/RP2354A/FPGA.~{STATUS}"]`; then the same command on `status_out.kicad_pcb` with `--nets '/RP2354A/FPGA.~{STATUS}' GND +3V3 --grid-step 0.05` -> `failed: 0`.
- **Issues:** `gh issue list --search "boxed in finer grid rescue"` -> nothing relevant (#811, #424 unrelated).

## 3. analyze_power_paths: a sink's current is charged once per power PIN, and a source's rating is added on top of the sinks it feeds

- **Tool / command:** `/analyze-power-nets` Step 5, `get_power_net_recommendations(pcb_data, components, paths)` (`py_tools/analyze_power_paths.py` lines 418-439).
- **What it claimed:** with the board's parts classified at datasheet maxima: GND 3.0 mm, +3V3 1.2 mm, Net-(D2-K) 1.2 mm, +1V1 1.0 mm; with every source rated at the LOAD it actually serves: GND 2.0, +3V3 1.2 (the 1-2 A row), and `Net-(U6-VREG_AVDD)` 0.7 mm.
- **What was true:** the sinks sum to about 330 mA (U6 150, U2 60, U1 30, J3 50, D1 15, Y2 5, estimates). The loop adds `current` for EVERY power pad of a sink on a net, so U6's ten +3V3 supply pins alone charge 1.5 A to +3V3, and its VREG_AVDD pin (about 200 uA by the RP2350 guide) gets U6's whole 150 mA (-> 0.7 mm). The POWER_SOURCE branch then adds the regulator's own rating to the same net, counting the current twice. On a 17.8 mm wide board with 0.4 mm-pitch parts the recommendation is unusable; I set the widths by hand from the IPC-2221 table the skill quotes applied to per-net estimates (0.7/0.5/0.3 mm).
- **Repro:** `python3 -X utf8 $D/repro/power_widths_repro.py` -> `{'+1V1': 0.7, 'GND': 2.0, '+3V3': 1.2, '/RP2354A/1V1': 0.7, 'Net-(U6-VREG_AVDD)': 0.7, ...}` with only U7 (280 mA source) and U6/U2/U1 (150/60/30 mA sinks) classified.
- **Issues:** `gh issue list --search "analyze_power_paths current"` / `"power net width per pin"` -> nothing relevant (#937, #40, #1237 are other topics).

## 4. No PDF renderer: the skill's §3.5 datasheet steps assume poppler; helper written

- **Tool / command:** SKILL.md §3.5 step 2 (`pdftotext -layout`, `pdftoppm -r 300`, `pdfimages -j`, "where poppler is installed") and the Read tool on a PDF.
- **What it claimed:** the skill offers poppler as the way to find and read the layout pages; it names no fallback.
- **What was true:** this machine has none of the three, and the Read tool refuses PDFs (`pdftoppm is not installed`). WebFetch mangles PDFs (the skill says so). I wrote `helpers/pdftool.swift` (PDFKit: `text`, `find`, `png`, `crop`) and used it for the TPS62162 (SLVSAM2E Figure 42), the RP2350 hardware design guide (Figure 4) and the HRO TYPE-C-31-M-12 drawing (that one via `qlmanage -t`).
- **Repro:** `python3 -c "import shutil; print(shutil.which('pdftotext'), shutil.which('pdftoppm'), shutil.which('pdfimages'))"` -> `None None None`.
- **Issues:** `gh issue list --search "poppler pdftotext datasheet"` -> none.

## 5. place_pose writes, and check_assembly passes, a courtyard overlap that KiCad's DRC grades as an error

- **Tool / command:** `python3 -X utf8 py_placer/place_pose.py $D/s9.kicad_pcb $D/s9.kicad_pcb set C17 --near 153.4 112.7 --rot 0 --intent $D/intent_run.json` (the §3.6 hand repair), then `check_assembly --baseline`, `board_score`, `check_complete`, `tests/stress/kicad_drc_compare.py`.
- **What it claimed:** place_pose: pad legality clean, exit 0; check_assembly: `buildable (blocking 0)`, the pairs `C17 <-> Y2` (0.151 mm2) and `C17 <-> U2` (0.095 mm2) `advisory` (0.060 / 0.064 mm2 after the routing chain's cap pass); board_score and check_complete DONE on the routed board.
- **What was true:** KiCad's own DRC grades both pairs `courtyards_overlap` at severity error (`kicad_drc_compare`: `COURTYARD kicad=2 krt_blocking=0 advisory=2 ... C17<->U2 krt=advisory sev=error`). Every grader on the DONE path passes a board that KiCad opens with two red courtyard errors. I moved C17 again (to 153.95,112.4, advisory 0) and re-routed, which cost three more routing arms (the chain is chaotic: the same 0.05 mm C17 move swung the routed vias 178 / 184 / 174).
- **Repro:** `python3 -X utf8 py_placer/place_pose.py $D/repro/s9_as_placed.kicad_pcb $D/repro/s9_c17.kicad_pcb set C17 --near 153.4 112.7 --rot 0` then `python3 -X utf8 py_tools/check_assembly.py $D/repro/s9_c17.kicad_pcb --baseline $D/repro/fixed.kicad_pcb` -> `advisory 2 ... buildable`; `kicad-cli pcb drc $D/repro/s9_c17.kicad_pcb --format json -o /dev/stdout` lists two `courtyards_overlap` errors on C17.
- **Issues:** `gh issue list --search "courtyard advisory kicad error"` -> #1095 (closed: check_assembly ignored the project's courtyards_overlap severity); this board's project keeps the severity at error and the pairs still grade advisory.

## 6. manifest_to_plan rejects plan.sh lines that use the plain redirect the skill prescribes

- **Tool / command:** `python3 tests/stress/manifest_to_plan.py $D/final_route/board_plan.sh -o $D/final_route/board_plan.json` (plan-pcb-routing Step 9).
- **What it claimed:** plan-pcb-routing ("After Routing Completes" and Step 10 rule 5) says "In the plan file use a plain redirect, `> /tmp/step.txt 2>&1`, or nothing at all"; `route_plan_check.py` R02 passes the file.
- **What was true:** the converter treats `> log 2>&1` as arguments: `5 recorded command(s) were REJECTED by their tool's own argument parser` (route_planes: "number of net arguments (2) must match number of plane layers (5)"; bga_fanout, qfn_fanout, place_fanout_clearance: "unrecognized arguments: > ..."; route_diff: "--layer-costs: invalid float value: '>'"), so only the three route.py steps reached the JSON. Workaround: converted the recorded `redo_commands.sh` instead (8 of 8 steps).
- **Repro:** `python3 -X utf8 tests/stress/manifest_to_plan.py $D/final_route/board_plan.sh -o $D/repro/plan_from_sh.json`.
- **Issues:** `gh issue list --search "manifest_to_plan redirect"` / `"manifest_to_plan pipe tokenizes"` -> none.

## 7. check_floorplan names a different "IC it decouples" than place_simple's decap term

- **Tool / command:** `check_floorplan.py <seed> --intent $D/intent_run.json` against the seed logs of `place_simple`.
- **What it claimed:** `[ERROR] decap_distance: C7 is 1.40mm from Y2, the IC it decouples` (s7), `C23 ... from U1` (s4), `C11 is 3.06mm from U1` (s8); place_simple's log for the same pass says `NOTE: decap C7 on +3V3 serves U6`.
- **What was true:** C7 is one of U6's IOVDD caps (groups.json puts it with U6, and place_simple tethers it there); U1 is the PSRAM on the OTHER face. The grade attributes a +3V3 cap to whichever rail chip is nearest, so the message points the repair at the wrong chip (repairing toward Y2 or U1 would be wrong). The distance is still a valid failure (nearest <= U6), only the attribution misleads.
- **Repro:** `python3 -X utf8 py_tools/check_floorplan.py $D/old/s7_as_placed.kicad_pcb --intent $D/intent_run.json` (pre-repair s7) -> the C7/Y2 line; `grep "decap C7" $D/s7.log` -> `serves U6`.
- **Issues:** `gh issue list --search "check_floorplan decap the IC it decouples nearest"` -> #1249, #794 (closed; other decap-attribution cases, not this one).

## 8. route_diff says "far-apart terminal pads peeled" when it routed the pair single-ended for being short

- **Tool / command:** `py_router/route_diff.py ... --nets '/Power Supply and USB/D*' '/RP2354A/USB_D*' --track-width 0.1 --diff-pair-gap 0.1 ...`
- **What it claimed:** `4 net(s) have far-apart terminal pads peeled from the coupled chain - route them single-ended next`.
- **What was true:** the lines just above give the real reason, `Electrically short (3.0mm coupled floor) - routing single-ended instead of coupled`, for both pairs; nothing was peeled for being far apart. Harmless here (route.py finished them), misleading when read alone.
- **Repro:** rerun line 5 of `$D/final_route/redo_commands.sh` to a scratch output and `grep -E "Electrically short|far-apart"` its log.
- **Issues:** `gh issue list --search "route_diff electrically short peeled far-apart"` -> none.

## 9. quick_score JSON carries no board_sha, so every judged-seed ledger row warns

- **Tool / command:** `converge.py record --score-file $D/s9_fast.score.json` (the judged seeds' quick_score payloads).
- **What it claimed / what was true:** `record WARNING: score payload carries no board_sha (pre-B4 board_score, or hand-built JSON) -- the ledger cannot verify it grades THIS board.` The payload is quick_score's current output, not a pre-B4 or hand-built one.
- **Repro:** `python3 -X utf8 py_placer/converge.py record --ledger $D/repro/ledger_test.jsonl --board $D/s9_fast.kicad_pcb --kind placement --lever test --score-file $D/s9_fast.score.json`.
- **Issues:** `gh issue list --search "quick_score board_sha"` -> none.

## 10. SKILL.md §3.9 calls a bare `kicad-cli`, which is not on PATH on macOS

- **Tool / command:** the §3.9 silk commands `kicad-cli pcb drc ...`.
- **What was true:** `which kicad-cli` -> not found; the binary is `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` (the repo's own tools locate it themselves). I added that directory to PATH.
- **Repro:** `which kicad-cli`.
- **Issues:** `gh issue list --search "kicad-cli PATH macOS"` -> nothing relevant.

## Helpers written (each is an entry above)

- `helpers/pdftool.swift` (+ compiled `helpers/pdftool`): entry 4.
