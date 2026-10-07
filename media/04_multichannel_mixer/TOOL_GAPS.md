# TOOL_GAPS -- fa10 / 04_multichannel_mixer

Ranked by what each cost this run. Every repro runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) in Git Bash with
`export MSYS2_ARG_CONV_EXCL='*'`; `R=wk/fa10/04_multichannel_mixer/repro`.
Issue searches were read-only `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`.

---

## 1. route.py's plane finalize ships 0.45 mm vias on a 1.5 mm-via board, then rewrites the project so every checker reads them clean

**Tool / command.** `py_router/route.py <board> <out> --nets '*' --track-width 0.3 --clearance 0.3 --via-size 1.5 --via-drill 0.6 --escalation board [--fab-overrides fab_board_floor.txt]` on a board whose Board Setup says `min_via_diameter 1.5`.

**What it claimed.** `JSON_SUMMARY_MIN: {"escalations": 0, ...}`; `--escalation board` is documented as "down to the board's own declared floors (Board Setup rules.min_*)"; `--fab-overrides` "PINS the floor".

**What was true (measured).** Every pour-carrying route of this board shipped GND vias at 0.45/0.20: k2_r1 10 of 209, m3_r1 14 of 214, m3_C (with `--fab-overrides via_diameter=1.5`) the same 14 of 214, w3_C 23 of 232, p4_R6 25 of 210, p5_B_t2 18 of 221. The source is `py_router/kicad_oracle.py` (lines ~2322 and ~2600): the oracle reconnect's via ladder is `((config.via_size, config.via_drill), (0.45, 0.2))`, a hard-coded rung that neither `--escalation` nor `--fab-overrides` reaches. route.py then writes `rules.min_via_diameter: 1.5 -> 0.45`, `min_via_annular_width 0.3 -> 0.125`, `min_through_hole_diameter 0.3 -> 0.2` into the output `.kicad_pro` and prints "Every checker (check_drc, board_score, KiCad's own DRC) grades against the NEW value, so this copper will read clean". It also writes `rules.min_via_drill`, a key the input project never had (the verifier flagged it as non-KiCad). Only `board_score --min-via-diameter 1.5` saw them (`undersized` 20-50). They are load-bearing: deleting the 10 from r3_B split GND into 10 KiCad-fill clusters.

**Cost.** The largest of the run: ~2 h of route arms and four helpers (`helpers/zone_strip.py`, `helpers/drop_small_vias.py`, `helpers/gnd_previas.py`, `helpers/gnd_stitch.py`). The working recipe: pre-anchor every B-side SMD GND pad with a locked 1.5 mm via before routing; leave GND out of `--nets` on every targeted retry (so the finalize never runs on the pour); finally drop any sub-floor via and re-join GND with board-floor vias placed inside KiCad's own exact fill.

**Repro.**
```
python3 -X utf8 py_router/route.py $R/m3.kicad_pcb $R/m3_out.kicad_pcb --nets '*' --track-width 0.3 --clearance 0.3 --via-size 1.5 --via-drill 0.6 --escalation board --fab-overrides $R/fab_board_floor.txt --layer-costs 1.0 1.0
grep "via diameter" -A0 <the log>     # "via diameter: 1.5 -> 0.45 mm; N of M object(s) ... below the ORIGINAL 1.5mm"
```
(~20 min.)

**Existing issue.** #1170 OPEN "Oracle reconnect drops to hardcoded 0.45/0.2 vias under --escalation off, outside escalation_rungs and design_rules" -- same root cause; this run adds that `--escalation board` and `--fab-overrides` are bypassed too, and that the project rewrite hides it from KiCad's DRC.

---

## 2. Targeted route.py retries rip nets outside `--nets`, and plateau by returning the input unchanged

**Tool / command.** `route.py <best> <out> --nets <the 3-7 broken nets> ...` (with or without `--rip-existing-nets <the hint's list>`).

**What it claimed.** A scoped retry routes the named nets; `--rip-existing-nets` is the documented way to free named blockers.

**What was true.** r3_B_t1: scoped to 8 nets, it ripped IC2A-IN-, IC2A-OUT, IC3A-IN- and R14-Pad1 (none in `--nets`) and left 7 open (log: "Ripping Net-(C19-Pad1) ... to retry tap route"). p5_s1 broke IC2B-OUT and IC3B-OUT the same way. Then p5_s2, p5_s3 (with the hint's rip list) and p5b_s1 each returned a board byte-identical in copper and via count to their input (3756.8 mm / 203 vias; 3478.43 mm / 199 vias) -- the remaining 6-7 nets never moved.

**Cost.** ~40 min of retries; the plateau is why the run had to diversify whole-board routes instead.

**Repro.** `python3 -X utf8 py_router/route.py $R/p5_s1g.kicad_pcb /tmp/x.kicad_pcb --nets 'Net-(IC2B-OUT)' 'Net-(IC3B-OUT)' 'Net-(IC5B-OUT)' --rip-existing-nets 'Net-(R14-Pad1)' 'Net-(C7-Pad2)' 'Net-(IC3A-IN-)' 'Net-(C9-Pad1)' --track-width 0.3 --clearance 0.3 --via-size 1.5 --via-drill 0.6 --escalation board --layer-costs 1.0 1.0 --max-ripup 6` then `board_score` -> unchanged blocking 6.

**Existing issue.** #1156 OPEN "route.py rips out-of-scope routed nets without --rip-existing-nets ..." covers the collateral rips; the no-op plateau has no issue.

---

## 3. The seeder's decap pin stage can never serve an `IC`-prefixed chip, and the fallbacks it points to do nothing

**Tool / command.** `py_placer/place_seed.py ... --intent <i> [--decap-claim-after-ics]`, then `place_seed --repair --repair-decaps`.

**What it claimed.** The skill: "re-seed with `--decap-claim-after-ics`" / "`--repair-decaps` to seat charged caps at their IC's pin".

**What was true.** With the given intent (only `decaps.max_pin_distance_mm`) the stage is unarmed ("decaps.max_distance_mm is not declared") so `--decap-claim-after-ics` is silently inert (z0 and z0d byte-identical). Arming `max_distance_mm` (intent_zd_probe.json) gives `claimed 0, pins 0`: "owners must be U-prefixed unless decap_owner_chips" -- `seed_from_intent(decap_owner_chips=False)` and no CLI exposes it, so IC1..IC5 are never owners. Stage 3.5 is also pre-empted on a zoned intent ("every scoped cap was claimed or put back before the centroid stage"). `--repair --repair-decaps` on z0: `no_legal_pose_within_limit` for C12, C21, C30 (4 IC errors left, 13-15 mm). My first hand placement (cap beside pin 8, in-row) then boxed in pin 7/pin 6 and the router failed exactly those pins (m3_r1).

**Cost.** ~35 min and `helpers/decap_escape_pose.py` (seats each decap within the pin limit, outside every other pin's escape row and outside courtyards, using the grader's own `_pin_gap` metric).

**Repro.** `python3 -X utf8 py_placer/place_seed.py $R/p0_fixed.kicad_pcb /tmp/s.kicad_pcb --intent $R/intent_zd_probe.json --clearance 0.3 --seed 0 --force --decap-claim-after-ics` -> `decap_stage.claimed 0`, reason "... owners must be U-prefixed unless decap_owner_chips".

**Existing issue.** #1105 OPEN "Per-supply-pin decap stage claims 0 caps on a pile" is related (no owner seated yet); the U-prefix owner rule and the `max_distance_mm` prerequisite are not filed.

---

## 4. Courtyard-less radial electrolytics are seated as pad boxes; check_assembly calls the body collision "advisory" and the board buildable

**Tool / command.** `place_seed` (any seed), then `py_tools/check_assembly.py <seed> --intent <i>`.

**What it claimed.** `VERDICT: buildable (blocking 0)`.

**What was true.** 11 CAPPRB254-500X840 (5 mm radial, no F.CrtYd) were packed with intersecting bodies: k2 `C22 <-> C5 fab 5.5638mm2 advisory`, `C2 <-> J5 fab 2.9341mm2`, `C13 <-> C5 fab 1.01mm2`. `placement/parser.py warn_missing_courtyards` confirms the placer falls back to the pad bbox with no fab fallback. `fside_body_fix` could find no clear pose for C5/C22 once the B-side parts were seeded.

**Cost.** ~25 min and `helpers/fside_body_fix.py`; worked around by seating the 11 caps by hand first (p2_caps) and seeding the rest around them.

**Repro.** `python3 -X utf8 py_tools/check_assembly.py $R/k2.kicad_pcb --intent $R/intent_zoned.json` -> fab overlaps listed `advisory`, `buildable`.

**Existing issue.** #1182 OPEN "On a courtyard-less library the seeder, --repair and --reseat work on pad boxes while check_assembly --baseline gates fab bodies" -- covers it (without `--baseline` the fab overlap is advisory).

---

## 5. place_seed refuses the board the skill tells you to build ("already looks PLACED")

**Tool / command.** `place_pose set+lock` the 22 declared front-panel poses (skill: "lock the fixed parts with place_pose first, then place_seed"), then `place_seed p0_fixed.kicad_pcb ... --intent intent.json`.

**What it claimed.** exit 3, "this board already looks PLACED ... use place_portfolio.py ... or --force".

**What was true.** 92 of 114 parts were still in the pile south of the outline; the pile is spread, not stacked, so `partially_unplaced` stays False. `--force` does the right thing (re-seeds only unlocked parts; all 22 locked poses held).

**Cost.** ~3 min.

**Repro.** `python3 -X utf8 py_placer/place_seed.py $R/p0_fixed.kicad_pcb /tmp/s.kicad_pcb --intent $R/intent.json --clearance 0.3` -> exit 3.

**Existing issue.** #1165 OPEN "place_seed refuses a pile as 'already PLACED' once the fixed parts are placed and locked, the order the skill prescribes" -- covers it.

---

## 6. Every placement and DRC grader defaults to the Default class (0.2), not the Board Setup min_clearance (0.3)

**Tool / command.** `place_pose`, `check_floorplan`, `check_assembly` ("Assembly audit ... (clearance 0.2)"), `check_join` ("grading at clearance 0.2"), `check_drc` ("Grading at clearance 0.2 mm (from ... Default net class)") with no `--clearance`.

**What was true.** This board declares `min_clearance 0.3` in Board Setup above a 0.2 Default class; KiCad's DRC floors clearance at the board minimum, so a 0.2-graded "clean" is not KiCad-clean. I passed `--clearance 0.3` to every grader that takes it (check_assembly and check_join do not have the same knob for this).

**Cost.** Low (caught at the start), but the verifier brief runs `check_drc` without `--clearance`, so its DRC lens grades at 0.2 on this board. It bit once: after shifting the decaps off the IC courtyards (route/p5_fin, since discarded) `board_score` reported `drc=0` while `check_drc --clearance 0.3` found **4 PAD-SEGMENT violations** (+12V pads of C12/C21/C30/C39 0.067 mm into a diagonal track) -- board_score's DRC lens grades at the 0.2 class too. The verifier confirmed the default-0.2 grading on check_drc, check_assembly, check_floorplan, render_placement and board_score.

**Repro.** `python3 -X utf8 py_router/check_drc.py $R/m3.kicad_pcb | head -3` -> "Grading at clearance 0.2 mm".

**Existing issue.** None found ("min_clearance Board Setup netclass floor grade" -> only #530, closed).

---

## 6b. check_assembly lists IC/decap courtyard overlaps as "advisory"; KiCad's DRC rejects them as errors

**Tool / command.** `py_tools/check_assembly.py route/p5_s1g.kicad_pcb --intent intent_zoned.json` vs `kicad-cli pcb drc --severity-error --refill-zones route/p5_s1g.kicad_pcb`.

**What it claimed.** `C12 <-> IC2 courtyard 0.279mm2 ... advisory` (x5, one per op-amp), `courtyard_blocking 0`, `VERDICT: buildable`; board_score `assembly 0`, `drc 0`.

**What was true.** KiCad 10's DRC on the same board: **5 `courtyards_overlap` errors** (IC1/C3, IC2/C12, IC3/C21, IC4/C30, IC5/C39; each a 0.2 x 1.395 mm sliver) at the project's own severity. The advisory floor (area >= 0.5 mm2 or 25 % AND depth >= 0.3 mm) is the tool's, not KiCad's. I fixed them before freezing (decaps 0.22 mm west + 0.12 mm south, C3 0.25 mm east); KiCad then reported 0 violations.

**Cost.** ~10 min (and it would have shipped had I not run kicad-cli myself).

**Repro.** `python3 -X utf8 py_tools/check_assembly.py $R/p5_s1g.kicad_pcb --intent $R/intent_zoned.json | grep courtyard` then `"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --format json --severity-error --refill-zones -o /tmp/d.json $R/p5_s1g.kicad_pcb`.

**Existing issue.** None covering this (#1095 closed is about check_assembly ignoring the project's courtyards_overlap severity when it is set to ignore; here the severity is error and the tool still says advisory).

---

## 7. No tool replicates a known-good channel arrangement onto identical sibling sheets

**What was missing.** The four channel sheets are exact translational copies (22 mm pitch; R+11 / C+9 / IC+1 per sheet). In every r3 route the c11f channel routed with 0-1 joins while kicad/0e62 carried 3-6. No placement tool copies a block's relative arrangement onto its siblings (arrays #1051 are rows of identical parts).

**Cost.** ~10 min and `helpers/replicate_channel.py` (refs mapped by verified net topology, pad by pad). Result p4_rep: crossings 366 -> 327, hpwl 3004 -> 2887, all checks clean.

**Repro.** `python3 -X utf8 wk/fa10/04_multichannel_mixer/helpers/replicate_channel.py $R/r3.kicad_pcb --src c11f`

**Existing issue.** None found.

---

## 8. check_floorplan --health does not measure escape lanes for a SOIC that has no inter-pin channel at this board's rules

**What it claimed.** `escape_lanes not measured: no fine-pitch parts on this board`.

**What was true.** SOIC-8, 1.27 mm pitch, 0.6 mm pads: 0.67 mm between pads, while a 0.3 track at 0.3 clearance needs 0.9 mm and a 1.5 mm via cannot sit between pins at all. Most unrouted ends in p4/p5 were op-amp pins (IC3.2, IC4.3/5/7, IC2.5, IC3.5). The pitch threshold ignores the board's own track/clearance/via.

**Cost.** Low (an escape-lane keep-out experiment, intent_esc.json, measured worse: e2 broken 11, e3 broken 14).

**Repro.** `python3 -X utf8 py_tools/check_floorplan.py $R/p4_rep.kicad_pcb --intent $R/intent_zoned.json --health --clearance 0.3`

**Existing issue.** None found.
