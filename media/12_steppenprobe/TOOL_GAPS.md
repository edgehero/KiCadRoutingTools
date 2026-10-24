# TOOL_GAPS -- gpm board 12 (steppenprobe)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gpm`) with `export PATH="$HOME/.venvs/krt/bin:$PATH:/Applications/KiCad/KiCad.app/Contents/MacOS"`;
the boards they need are in `wk/gpm/12_steppenprobe/repro/`.

## 1. `fill_for_delivery.py` turns a DONE board into a blocking one (via-in-paste), so the best board could not be shipped

- **Tool / command:** `python3 -X utf8 py_tools/fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` (skill §3.9 step 2).
- **What it claimed:** `Filled: ... unconnected (no --refill-zones): 54 -> 0`, exit 0 -- a filled copy of the same board.
- **What was true:** the board went in as KiCad 6 format (`version 20211014`) and came out as KiCad 10 (`version 20260206`)
  with an explicit `(capping no) (covering ...) (plugging ...) (filling no)` written into every one of its 109 vias
  (0 before, 110 `(capping no)` tokens after). The route step had recorded the board's 4 +3V3 vias in 0603/ferrite pads
  as `unstampable` (old format, cannot declare Type VII) and `check_drc` accepted them as `undeclarable-via-in-paste`.
  After the fill the same 4 vias are graded `via-in-paste ... not filled+capped (capping no, filling no)`:
  `board_score` blocking 0 -> **4** (`drc_via_in_paste=4`), `check_complete` DONE -> **INCOMPLETE**. The repo's own stamp
  (`fab_notes.ship_via_protection_file`) then refuses to declare Type VII on them, because the tokens pcbnew wrote read as
  an author's decision ("own spec kept"). Cost: the via-cost-300 board (109 vias) was abandoned at delivery (~25 min; the board finally
  shipped has 123 vias).
- **Reproduce:**
  ```
  P=wk/gpm/12_steppenprobe/repro
  python3 -X utf8 py_tools/board_score.py $P/v300_labelled.kicad_pcb --baseline $P/pile.kicad_pcb --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3 --json /tmp/a.json -q   # BLOCKING=0
  python3 -X utf8 py_tools/fill_for_delivery.py $P/v300_labelled.kicad_pcb -o $P/v300_refill.kicad_pcb
  python3 -X utf8 py_tools/board_score.py $P/v300_refill.kicad_pcb --baseline $P/pile.kicad_pcb --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3 --json /tmp/b.json -q   # BLOCKING=4 drc_via_in_paste=4
  grep -c '(capping no)' $P/v300_refill.kicad_pcb    # 110 (0 in the input)
  ```
- **Existing issues:** none covers it. Related: #1335 (CLOSED, the skills never ran the delivery fill), #992/#962/#1171
  (CLOSED, Type VII stamping), #1232 (OPEN, via rings inside mask openings).

## 2. The skills disagree on whether a net-class track width is a spec, and the default chain cannot meet it

- **Tool / command:** plan-pcb-placement §1 ("DONE is measured with every spec the board declares", `--net-min-widths`)
  and `references/verifier.md` step 5 ("power widths" a declared class) against plan-pcb-routing Step 4
  ("track_width ... not DRC floors -- they are just defaults"); the default route chain.
- **What it claimed:** the routed board graded DONE (`board_score` blocking 0, `check_complete` DONE) with
  `net_widths` UNEXAMINED, following the routing skill's reading.
- **What was true:** the verifier read the board's `Power` net class (track_width 0.3 on 8 nets) as a declared power
  width, graded it, and failed the board: GND 19.06 mm, VBUS 3.05, +3V3 1.84, +1V8 1.65 mm of copper at 0.15-0.175 mm
  (`net_widths` blocking 4). The skill names no way to deliver a class width: `route.py`'s tap neck-down and its
  plane finalize draw at the call's `--track-width` (0.15), and `--force-reroute` skips the poured nets ("planes belong
  to route_planes"). What worked was a split chain of my own -- rails routed first and the two pours finalised last,
  each at `--track-width 0.3`, signals between them at 0.15 -- which met 0.3 everywhere AND cut vias 136 -> 123.
  Cost: one verifier call and ~20 min.
- **Reproduce:** `python3 -X utf8 py_tools/board_score.py wk/gpm/12_steppenprobe/repro/s11_L30_routed.kicad_pcb --baseline wk/gpm/12_steppenprobe/repro/pile.kicad_pcb --net-min-widths wk/gpm/12_steppenprobe/repro/net_min_widths.json --json /tmp/w.json -q` -> `net_widths=4`; the chain that meets it is `helpers/full_chain_w.sh`.
- **Existing issues:** #1318 (CLOSED, 0.15 mm necks on 0.3 mm power nets at LQFP pins) is the same symptom; none on the
  skill conflict.

## 3. `route_diff` lowers the board's authored `min_hole_clearance` and `check_complete --authored-from` does not say so

- **What was true:** the input project declares `min_hole_clearance 0.25`; after `route_diff.py ... --clearance-ceiling
  0.15` the project says 0.15, and it ships so. `check_drc` still grades copper-to-NPTH at 0.25 (clean), but KiCad's DRC
  of the delivered board now enforces 0.15, and `check_complete --authored-from <input>` lists no lowered floor
  (the verifier found it by reading the two projects).
- **Reproduce:** `python3 -X utf8 py_router/route_diff.py wk/gpm/12_steppenprobe/repro/s11_step1_pour.kicad_pcb wk/gpm/12_steppenprobe/repro/s11_diff_check.kicad_pcb --nets '/USB_D*' --track-width 0.15 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3`, then compare `min_hole_clearance` in `s11_step1_pour.kicad_pro` (0.25) and `s11_diff_check.kicad_pro` (0.15).
- **Existing issues:** none found ("min_hole_clearance writeback").

## 4. Nothing grades the USB pair: KiCad does not see `/USB_DP` + `/USB_DM` as a pair, and route_diff's own intra-pair status is "not-measured"

- **What was true:** `list_nets --diff-pairs` and `route_diff` treat the nets as a pair and the project records them as
  `protected_nets` "diff-pair", but `board_score`'s diff_pairs component reports `pairs {}` (KiCad pairs nets by a
  `P`/`N` or `+`/`-` suffix; `DM` is neither) and is UNGRADED. The first delivered board had 4.52 mm P/N skew; with
  `--diff-pair-intra-match` route_diff reports `status: unmatched, reason: not-measured, matcher_delta_mm 0.0014`,
  while the shipped copper measures 0.632 mm (`helpers/usb_pair.py`, which calls `net_queries.diff_pair_copper`).
  The verifier failed call 1 partly on this. Helper written because no CLI reports the pair.
- **Reproduce:** `python3 -X utf8 wk/gpm/12_steppenprobe/helpers/usb_pair.py wk/gpm/12_steppenprobe/repro/s11_L30_routed.kicad_pcb` (skew 4.5 mm) and `grep -o '"intra_pair_matching": [^]]*' wk/gpm/12_steppenprobe/final_route/plan_run.log`.
- **Existing issues:** none found.

## 5. `route.py --same-net-pad-clearance > 0` still ships +3V3 vias inside same-net SMD pads

- **Tool / command:** `route.py ... --same-net-pad-clearance 0.3` (help: "> 0 keeps vias off same-net SMD pads AND off the
  net's solder-paste openings (escape vias, via-in-pad rescue, tap vias)").
- **What it claimed:** vias kept off same-net pads; then its own `FAB NOTE: 4 via(s) in a pad or paste opening
  [C16.1, C22.1, FB2.2, FB3.2] ... 4 shipped WITHOUT Type VII`.
- **What was true:** with the flag at 0.1 or 0.3 on every route step, the default via cost gave 0-2 such vias, but every
  run at `--via-cost` 90-400 put 1-8 +3V3 vias in 0603 cap / ferrite pads (measured by `helpers/via_in_pad.py`: 3, 6, 1,
  1, 3, 4, 4, 5, 8, 4 over ten runs). The main loop's trace (`KICAD_ROUTE_TRACE`) has no `add_v` for them, so they come
  from the in-run plane finalize / pour repair, which does not honour the pad clearance. Cost: together with gap 1 it
  is why the 109-via result could not ship.
- **Reproduce:**
  ```
  P=wk/gpm/12_steppenprobe/repro
  python3 -X utf8 py_router/route.py $P/s11_step2a_diff.kicad_pcb $P/s11_v300_route.kicad_pcb --nets '*' --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --power-nets GND +3V3 VBUS +5V +1V8 /VPHY /VPLL Vdrive --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 0.3 --layer-costs 1.0 3.0 --escalation board --same-net-pad-clearance 0.3 --via-cost 300
  python3 -X utf8 wk/gpm/12_steppenprobe/helpers/via_in_pad.py $P/s11_v300_route.kicad_pcb   # 4 same-net via-in-pad: C16.1 FB3.2 FB2.2 C22.1
  ```
- **Existing issues:** #1232 (OPEN, "route.py puts via rings inside pad solder-mask openings, and nothing reports it") is
  adjacent; none names the finalize ignoring `--same-net-pad-clearance`.

## 6. Default chain settings put 77 of 155 vias inside SMD pads (LQFP pins included) and nothing gates it on a KiCad 6 board

- **Tool / command:** the skill's route step with defaults (`route.py --nets '*' ...`, via-in-pad allowed by default, #1025).
- **What it claimed:** `board_score` blocking 0, `check_complete` DONE, `check_drc` clean; KiCad DRC compare:
  `VIA-IN-PASTE ... undeclarable=76 (KiCad has no such check)`.
- **What was true:** 77 vias overlap a same-net SMD pad (`helpers/via_in_pad.py`), including LQFP-64 pins U1.16, U1.17,
  U1.32 (0.3 mm wide, 0.5 mm pitch) and 0603 passives. On this file format none can be declared Type VII, so a fab would
  build 77 unfilled vias under solder. Only `--same-net-pad-clearance 0.1` brought it to 0-2 (and, here, fewer vias too).
  The skill mentions the flag only in the Advanced Routing Parameters table; nothing in the DONE path surfaces the count.
- **Reproduce:** `python3 -X utf8 wk/gpm/12_steppenprobe/helpers/via_in_pad.py wk/gpm/12_steppenprobe/final_route_old1/step2d_iter2.kicad_pcb` (77 of 155).
- **Existing issues:** #1232 (OPEN) is related; #962/#992 (CLOSED) built the stamping that this format cannot use.
- **Helper written:** `helpers/via_in_pad.py` -- no repo tool reports via-in-pad as a count on a pre-KiCad-10 board
  (check_drc folds them into `undeclarable` and passes).

## 7. The fast judge kept the wrong seed

- **Tool / command:** `judge_seeds.py judge.json --chain judge_chain.txt --intent intent_run.json --seeds 11,8` (§3.7).
- **What it claimed:** `best seed 8` (fast blocking 0, joins 0, vias 115) over seed 11 (fast blocking 1, joins 1, vias 98).
- **What was true:** full-routed with one chain, seed 11 is DONE with 133-136 vias / ~1100 mm while seed 8 is DONE with
  143-155 vias / 1465-1580 mm. The one open join of seed 11's `--quick 2` route closed in the full route. Cost: a full
  routing cycle (A/B of 10 chains) spent on seed 8 before the switch (~15 min).
- **Reproduce:** `zsh wk/gpm/12_steppenprobe/helpers/full_chain.sh wk/gpm/12_steppenprobe/repro/s11.kicad_pcb /tmp/s11 1.0 3.0` and the same for `repro/s8.kicad_pcb`, then `zsh wk/gpm/12_steppenprobe/helpers/grade_quick.sh /tmp/s11/a5.kicad_pcb` (and s8).
- **Existing issues:** #1296 (CLOSED, judge and floorplan errors) and #1327 (CLOSED, judging chain tool) are about the
  judge, not about a 1-join quick route outranking a better full route.

## 8. Skill contradiction: Step 1 says keep a designer's thermal pour with `--thermal-relief`; R07 refuses the plan

- **Tool / command:** `plan-pcb-routing` Step 1 ("If it should be replaced but keep thermal relief, add `--thermal-relief`")
  vs `route_plan_check.py` R07 / Important Notes ("do not set `--thermal-relief`").
- **What was true:** the board's own pours are thermal (`connect_pads` default, 0.15 spokes). The thermal chain was the
  cleanest first DONE (158 vias, no undersized via), the solid one escalated a 0.3/0.2 GND tap via below the board's
  0.6 mm via floor until `--escalation board` was added. The plan checker refuses the first, so the shipped plan pours
  solid. Cost ~10 min of A/B.
- **Reproduce:** `python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py wk/gpm/12_steppenprobe/repro/plan_thermal.sh --board wk/gpm/12_steppenprobe/repro/s11.kicad_pcb` -> `FAIL R07 no teardrops, no thermal relief ... REFUSED`.
- **Existing issues:** #1329 (CLOSED, route_planes replaces a designer's zone thermal -> solid) introduced the Step 1 text; no issue on the R07 conflict.

## 9. `analyze_power_paths.get_power_net_recommendations` multiplies a part's current by its number of power pins

- **Tool / command:** the `/analyze-power-nets` recipe (`classify_component` then `get_power_net_recommendations`).
- **What it claimed:** GND 2.0 mm, +3V3 1.0 mm, VBUS 1.0 mm, /VPHY 0.7 mm for a ~230 mA board.
- **What was true:** the loop adds `current_rating_ma` once per power PIN: J1 classified 500 mA puts 2000 mA on GND (4
  GND pads), U1 at 70 mA puts 630 mA on GND (9 pins), 350 mA on +3V3 (5 pins), 280 mA on +1V8. Per part, the board draws
  about 230 mA, so the tool's own table gives 0.7 mm; that is what was used, and the report says so.
- **Reproduce:** `python3 -X utf8 wk/gpm/12_steppenprobe/helpers/power_analysis.py wk/gpm/12_steppenprobe/repro/pile.kicad_pcb | tail -6`
- **Existing issues:** none found ("analyze_power_paths per pin current", "power net width GND pins").

## 10. Default `--escalation fab` routes below the board's own DRC-enforced floors and lowers them in the project

- **Tool / command:** `route.py` with the default `--fab-tier auto --escalation fab`.
- **What was true:** on a board declaring `min_via_diameter 0.6`, plane taps were escalated to 0.3/0.2 and 0.25/0.15 vias
  and a clearance of 0.1442 mm, and the writeback set the project's `min_via_diameter` to 0.3 / 0.25 -- so the board then
  grades itself against the lowered floor. It is disclosed (`Design rules [...]`), but a DONE at the board's own rules
  needed `--escalation board`, which the skill does not suggest for this case. Cost ~5 min.
- **Reproduce:** `python3 -X utf8 py_router/route.py wk/gpm/12_steppenprobe/repro/s11_step2a_diff.kicad_pcb wk/gpm/12_steppenprobe/repro/esc_default.kicad_pcb --nets '*' --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --power-nets GND +3V3 --power-nets-widths 0.7 0.7 --layer-costs 1.0 1.5 | grep 'Design rules \['`
  -> `29 feature(s) on 9 net(s) delivered below the requested size (smallest clearance 0.1442 mm, smallest track width 0.1423 mm, smallest via diameter 0.3 mm); 21 fab-tier escalation(s)`, and `esc_default.kicad_pro` now says `min_via_diameter 0.45` (the input says 0.6).
- **Existing issues:** #1287 and #1170 (CLOSED) are about escalation floors; nothing open.

## 11. No PDF renderer for the datasheet steps (poppler absent, Read refuses PDFs)

- **Tool / command:** skill §3.5 step 2 (`pdftotext` / `pdftoppm`) and the Read tool on a PDF.
- **What was true:** neither binary exists on this Mac, and Read answers "pdftoppm is not installed". `qlmanage` renders
  page 1 only. Wrote `helpers/pdfpage.swift` (PDFKit) to render pages. Cost ~5 min.
- **Reproduce:** `which pdftoppm pdftotext` (not found).
- **Existing issues:** none found.

## 12. An edge connector's body overhang is "unmeasured" on any rounded-corner outline, so the band falls to the courtyard

- **Tool / command:** `check_floorplan.py ... --intent` with `edge_connectors[J1].overhang_mm`.
- **What was true:** `connector_geometry` measures the drawn body only against a plain rectangle; this board's outline has
  3 mm corner arcs, so the GCT USB4085's 2.51 mm (datasheet edge line to shell front) had to be written as 3.0-3.1 mm
  on the courtyard (`legacy_occupancy@margin=0`). Cost ~5 min.
- **Reproduce:** `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/12_steppenprobe/repro/s11.kicad_pcb --intent wk/gpm/12_steppenprobe/repro/intent_run.json | grep 'J1 north'`
- **Existing issues:** #1301 (CLOSED) moved the band to zero margin; nothing on rounded outlines.

## 13. Dangling stubs survive the chain's two `'*'` iterations

- **Tool / command:** `route.py --nets '*'` iterations (Step 2d), graded by `check_complete` (weird_copper).
- **What was true:** a 3.36 mm +1V8 dead-end on F.Cu (seed 8, layer costs 1.0 1.2) and a 0.1 mm +3V3 stub (1.0 1.5)
  stayed through both iterations; a scoped `--rip-existing-nets +1V8` was a documented no-op; only `--nets +1V8
  --force-reroute` cleared it. Several other parameter variants failed DONE on weird copper alone. Cost ~5 min.
- **Reproduce:** `python3 -X utf8 py_router/check_weird.py wk/gpm/12_steppenprobe/repro/s8_N_a5.kicad_pcb` (dangling-end +1V8 3.359 mm).
- **Existing issues:** #1166, #1291, #1332 (CLOSED) are other dangling producers.

## 14. `place_pose` reports `legal: false` for an in-place 180 deg turn on a rounded-corner outline

- **What was true:** `place_pose ... set R25 116.6053 75.8011 --rot 180` (route_review's own suggestion) prints
  `"legal": false, "no_worse": true`; the only cause is `pad_edge_after.complete: false` with 306 pads "outline uses
  sampled perimeter check". `check_assembly` says buildable. Cost: a minute of doubt.
- **Reproduce:** `python3 -X utf8 py_placer/place_pose.py wk/gpm/12_steppenprobe/repro/s11.kicad_pcb /tmp/r.kicad_pcb set R25 116.6053 75.8011 --rot 180 | grep -o '"legal": [a-z]*'`
- **Existing issues:** #1326 (CLOSED) is a different `legal` false.

## 15. Small papercuts

- `converge.py record` prints the whole score payload (~1000 lines) to stdout on every call, and a `quick_score` payload
  carries no `board_sha` ("the ledger cannot verify it grades THIS board"). Repro: any `converge.py record --score-file wk/gpm/12_steppenprobe/s11_fast.score.json ...`.
- Power widths: route.py shipped two 2.0 mm +3V3 stubs at J4 pin 1 though 0.7 mm was asked, and 1.65-19 mm of power
  copper at 0.15 mm under the Power class's 0.3 mm (disclosed in `power_widths`; #1318 is about the same necking).
  Repro: the J4.1 stubs are in `wk/gpm/12_steppenprobe/repro/s11_L30_routed.kicad_pcb` (+3V3, width 2.0, near (115.5, 67.2)).

## 16. `beautify_labels` shrinks references below the board's minimum text height, and the skill's silk count does not see it

- **Tool / command:** skill §3.9 step 1, `beautify_labels.py <board> labelled.kicad_pcb`, graded with the skill's one-liner
  that counts only violation types starting with `silk`.
- **What it claimed:** silk 108 -> 18 (silk_edge_clearance 4 -> 2, silk_over_copper 50 -> 3, silk_overlap 54 -> 13),
  so the labelled board was kept.
- **What was true:** the same KiCad run reports `text_height` 0 -> **5**: U12, U9 and R8 shrunk to 0.75 mm, R7 and R25 to
  0.7 mm, under the board's 0.8 mm minimum (`"shrunk": 3, "shrunk_rotated": 5` in its JSON_SUMMARY). The skill's
  comparison command filters those out, so the trade is invisible (the verifier found it). Net still better (108 -> 23
  KiCad warnings), so the tidy was kept and this is disclosed.
- **Reproduce:** `python3 -X utf8 py_placer/beautify_labels.py wk/gpm/12_steppenprobe/repro/routed_final.kicad_pcb /tmp/lab.kicad_pcb`, then `kicad-cli pcb drc` on both (copies) and count `text_height` (0 before, 5 after).
- **Existing issues:** none found ("beautify_labels text_height").

## Helpers written (each is a gap above, or this one)

| helper | why the repo's tools were not enough |
|---|---|
| `helpers/pdfpage.swift` | gap 11: no PDF renderer on this machine |
| `helpers/via_in_pad.py` | gap 6: no tool counts vias in SMD pads on a pre-KiCad-10 board |
| `helpers/usb_pair.py` | gap 4: no CLI reports the pair KiCad does not recognise (wraps `net_queries.diff_pair_copper`) |
| `helpers/stamp_type_vii.py` | gap 1: tried to re-apply route.py's own Type VII rule after the fill; the repo function refused ("own spec kept"), so it was not used on the shipped board |
| `helpers/power_analysis.py` | the /analyze-power-nets recipe is a Python snippet by design; this file is that snippet with this board's classifications (gap 9) |
| `helpers/full_chain.sh`, `helpers/full_chain_w.sh`, `helpers/grade_quick.sh` | `judge_seeds.py` always adds `--quick 2`, and no tool runs a full routing chain over several placements or parameter sets and grades them alike; these run the §3.8 chain (the second the width-respecting form of gap 2) and grade with board_score + check_complete |
