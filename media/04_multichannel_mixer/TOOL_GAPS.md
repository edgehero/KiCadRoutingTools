# TOOL_GAPS -- gp14 board 04 multichannel_mixer

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`) after
`export PATH="$HOME/.venvs/krt/bin:$PATH"`; the input boards are copied into
`wk/gp14/04_multichannel_mixer/repro/` (R=`wk/gp14/04_multichannel_mixer`, P=`$R/repro`).

---

## 1. place_simple packs courtyard-less footprints by their pad box; check_assembly grades their .Fab body -> every judged seed NOT BUILDABLE (helper written)

**Tool / command:** `py_placer/place_simple.py ... --round` (then `py_tools/check_assembly.py <seed> --baseline <fixed> --intent <intent>`).

**What it claimed:** all 12 seeds legal (`illegal: []`, exit 0); `judge.json` named 6 seeds to judge.

**What was true:** check_assembly called all 6 judged seeds **NOT BUILDABLE**: 3-7 `COURTYARD-BLOCKING` pairs each (seed 10: 7 pairs, 35.1 mm2; seed 3: 6 pairs). Every pair involves a THT electrolytic (`CAPPRB254-500X840`: C1, C2, C4, C5, C13, C14, C22, C23, C31, C32, C40) or J5 -- the 12 footprints `board_brief` warns "have no courtyard and fall back to their pad bounding box". The anneal's overlap term (`simple_anneal._grown_at` -> `placement_state` courtyard, else pad bbox) sees a 2.54 mm-pitch pad pair (~4.3 x 1.6 mm); check_assembly sees the drawn 5 mm can (`b_body_sources: fab`). Cans were packed onto each other and onto the jacks' courtyards (C2<->C4 depth 2.55 mm, C23<->J8 1.51 mm, C5<->J1 1.42 mm). No repo tool legalises a body overlap (place_pose snaps to PAD legality only; there is no quench/legalise CLI at the placement door), so I wrote `helpers/fix_body_overlaps.py`: it walks the movable member of each gating pair away from the overlap with `place_pose set REF --near X Y` and keeps a move only when check_assembly's gating count/area drops. 4-24 moves per seed, ~6 min per seed (6 in parallel), all six then buildable.

**Cost:** the largest of the run: writing the helper plus two fixer passes (the first at the wrong clearance, gap 2) -- about 20 of the 28 minutes to the first DONE -- and every shipped placement carries 4-13 extra place_pose moves (CHOSEN.json `after`).

**Repro:**
```bash
python3 -X utf8 py_placer/place_simple.py $P/pile.kicad_pcb $P/s3.kicad_pcb --groups $P/groups.json --intent $P/intent.json --seed 3 --json $P/s3.json
python3 -X utf8 py_tools/check_assembly.py $P/s3.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json
# -> place_simple JSON_SUMMARY illegal [] ; check_assembly: 6 COURTYARD-BLOCKING pairs (C13<->RV4, C13<->C22, C14<->J7, C32<->J9, C5<->J1, C5<->J7), VERDICT: NOT BUILDABLE
```

**Existing issues** (`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "no courtyard pad bounding box"`): #1182 CLOSED "On a courtyard-less library the seeder, --repair and --reseat work on pad boxes while check_assembly --baseline gates fab bodies, so every seed is NOT BUILDABLE" -- the same defect, fixed for the retired seeder; `place_simple`'s anneal (the new path) still uses pad boxes. Also #896 CLOSED (one body model for courtyard-less libraries), #1106 CLOSED. No open issue covers place_simple.

---

## 2. check_assembly and place_pose grade pad clearance at the Default net class (0.2), below the board's Board Setup min_clearance (0.3) that check_drc / board_score / KiCad grade; check_assembly calls 0.3 "STRICTER than the board asks for"

**Tool / command:** `py_tools/check_assembly.py` (default clearance) and `py_placer/place_pose.py set REF --near X Y` (default clearance).

**What it claimed:** `grading at clearance 0.2mm [board netclass]`; my fixer's place_pose moves were `legal: true`, the boards `buildable`. Asked for `--clearance 0.3`, check_assembly prints: "NOTE: --clearance 0.3mm overrides this board's own Default net-class clearance of 0.2mm, so this grade is STRICTER than the board asks for."

**What was true:** the board asks for 0.3: `.kicad_pro` `rules.min_clearance 0.3`, which KiCad's DRC enforces and which `check_drc` and `board_score` grade at (`graded_at: 0.3`). Two pads the fixer had moved sat 0.24-0.25 mm from foreign pads (C39.2 <-> C32.1 overlap 0.062 mm, C5.2 <-> C6.1 overlap 0.048 mm at 0.3). They passed place_pose and check_assembly and surfaced only after a full route, as `board_score drc=2` (`pad-pad`). The fix was `--clearance 0.3` on every place_pose / check_assembly call.

**Cost:** one wasted full route (final_route_old1), a second fixer pass on all six seeds and a re-judge (~8 min).

**Repro:**
```bash
python3 -X utf8 py_tools/check_assembly.py $P/s3_fix_at02.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json   # buildable (blocking 0), "grading at clearance 0.2mm [board netclass]"
python3 -X utf8 py_router/check_drc.py $P/s3_fix_at02.kicad_pcb                                                            # FOUND 2: PAD-PAD C39.2<->C32.1, C5.2<->C6.1
python3 -X utf8 py_tools/check_assembly.py $P/s3_fix_at02.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json --clearance 0.3   # prints the false "STRICTER than the board asks for" note
```

**Existing issues** (`--search "min_clearance"`): #1210 CLOSED "check_drc and board_score grade copper clearance at the Default net class and ignore Board Setup min_clearance, which KiCad's DRC enforces above it" -- fixed for check_drc/board_score only; check_assembly and place_pose (placement door) still read the Default class. No issue found for the placement side (`--search "check_assembly clearance netclass"`, `--search "place_pose clearance min_clearance"`: none).

---

## 3. place_pose `rotate REF 180` is an ABSOLUTE angle; route_review says "turn 180" and the skill says "place_pose ... rotate" -- applied as written it turned R39 by 90 degrees and C8 not at all, and shipped a KiCad courtyard error

**Tool / command:** `py_tools/route_review.py` ("== two-pad parts turned against their wiring (turn 180)": `C8 at (141.86, 99.9) rot 180`, `R39 at (93.0, 120.01) rot 270`) followed by the skill's instruction (§3.6 step 4 "a turned two-pad part: ... `place_pose ... rotate` after the last placement", and the place-mode paragraph "turn each two-pad part it lists ... with `place_pose ... rotate`") -> `place_pose.py IN OUT rotate C8 180 rotate R39 180`.

**What it claimed:** exit 0, `legal: true`, no_worse; check_assembly afterwards `buildable`.

**What was true:** `rotate REF DEG` SETS the angle (`--relative` adds); the help says so on one line, but neither route_review's "turn 180" nor the skill mentions `--relative`. C8 was already at 180 (not turned); R39 went 270 -> 180, a 90-degree turn that pushed its courtyard into R42's (0.082 mm2, depth 0.217 mm). That board routed to 75 vias, passed board_score, check_complete and the verifier's call 1 -- and KiCad's own DRC (the verifier's cross-check, and `tests/stress/kicad_drc_compare.py`: `R39<->R42 krt=advisory sev=error`) reported a courtyards_overlap ERROR (gap 6 for why check_assembly did not). Redone with `rotate C8 180 --relative rotate R39 180 --relative` (C8 180->0, R39 270->90), which also routed better (70 vias).

**Cost:** one shipped-then-superseded final chain (final_route_old4), a second verifier call, ~20 min.

**Repro:**
```bash
python3 -X utf8 py_placer/place_pose.py $P/s2_fixc.kicad_pcb $P/rot_abs.kicad_pcb --clearance 0.3 rotate R39 180
python3 -c "import sys; sys.path.insert(0,'py_router'); from kicad_parser import parse_kicad_pcb; print(parse_kicad_pcb('$P/rot_abs.kicad_pcb').footprints['R39'].rotation)"   # 180.0 (was 270.0)
```

**Existing issues** (`--search "place_pose rotate relative"`): none (only #1255, unrelated).

---

## 4. board_score says blocking 0 and check_orphan_stubs says "NO ORPHAN STUBS" on a board check_complete refuses for weird copper (dangling end, stacked duplicate); route.py's own cleanup and two extra all-nets passes leave it

**Tool / command:** `py_tools/board_score.py`, `py_tools/check_orphan_stubs.py` vs `check_complete.py` / `py_router/check_weird.py`, on the via-cost-125 final chain (final_route_old3).

**What it claimed:** board_score `BLOCKING=0 ... vias=80`; check_orphan_stubs "NO ORPHAN STUBS FOUND!"; route.py iterations "routed 0" (nothing to do).

**What was true:** check_complete `VERDICT: INCOMPLETE -- weird_copper: not clean`; check_weird: a 3.677 mm dangling `/CH1/OUT` segment on F.Cu (free end at 131.4,142.9) and two stacked GND segments (0.8 and 0.4 mm wide, same endpoints, inside a via). The dangling end appeared on every route of that placement at via cost 75-135; the two `--nets '*'` iterations the routing skill bakes in did not remove it. A `--force-reroute` of exactly the nets check_weird names (with GND in `--nets`) cleared it, and that step is the last step of the shipped chain.

**Cost:** one more final chain (~2 min) plus the cleanup step; the skill's §5.6 ledger example scores with board_score only, so a run that stopped at board_score would have called this DONE.

**Repro:**
```bash
python3 -X utf8 py_tools/board_score.py $P/s2r_v125_step4.kicad_pcb --intent $P/intent.json --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --baseline $P/pile.kicad_pcb --quiet   # BLOCKING=0
python3 -X utf8 py_tools/check_orphan_stubs.py $P/s2r_v125_step4.kicad_pcb    # NO ORPHAN STUBS FOUND!
python3 -X utf8 py_router/check_weird.py $P/s2r_v125_step4.kicad_pcb          # dangling-end 3.677 mm + stacked-copper
python3 -X utf8 check_complete.py $P/s2r_v125_step4.kicad_pcb --intent $P/intent.json --min-track-width 0.3 --min-via-diameter 1.5 --min-via-drill 0.3 --baseline $P/pile.kicad_pcb   # INCOMPLETE -- weird_copper
```

**Existing issues** (`--search "check_orphan_stubs dangling check_weird"`, `--search "weird_copper check_complete board_score"`): #1186 CLOSED (check_weird free-end false positive on T-junctions -- the opposite direction); nothing covers board_score / check_orphan_stubs missing weird copper.

---

## 5. route.py reports a clean run while KiCad's refill shows the GND pour in 5 pieces (false success)

**Tool / command:** `py_router/route.py ... --via-cost 150` (a post-DONE routing arm).

**What it claimed:** end of run, "re-graded on the written board": `Multi-point: 177/177 pads connected`, "Recovered after a summary reported them failing: 2", `JSON_SUMMARY_MIN failed 0, multipoint_deficit 0` -- although the same run's plane finalize had logged `GND: exact-fill verdict OPEN` and the reconciliation's oracle links on GND FAILED.

**What was true:** `check_connected`: "1 net(s) UNCONNECTED per KiCad refill though copper grading passed them: GND", 5 disconnected components; `board_score broken=1` (GND, 4 joins). The final re-grade credits the fill model, not the exact fill the finalize had just measured. Of the 33 post-DONE routes I graded (opt/A*, opt/sweep/*, opt/seeds/*), 23 shipped GND in pieces and 21 of those 23 printed `JSON_SUMMARY_MIN failed 0`; only board_score / check_connected caught them.

**Cost:** low (board_score caught every one), but anyone trusting `JSON_SUMMARY_MIN` would ship a broken ground.

**Repro:**
```bash
python3 -X utf8 py_router/route.py $P/pour_s3.kicad_pcb $P/A3_out.kicad_pcb --nets '*' --clearance 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 150 --json-out $P/A3_out.json
python3 -X utf8 py_router/check_connected.py $P/A3_out.kicad_pcb     # GND UNCONNECTED per KiCad refill, 5 components
```

**Existing issues** (`--search "JSON_SUMMARY_MIN failed 0 oracle"`, `--search "regrade copper grading KiCad refill unconnected"`, `--search "rip-existing-nets already fully connected hint"`): #572 CLOSED "ghoul GND open: oracle-punted link false-cleared by model credit" is the same pattern (model credit clearing an oracle-open link), closed; nothing open.

---

## 6. check_assembly calls a courtyard overlap "advisory" that the project grades as an ERROR and KiCad's DRC reports; KiCad-only findings no repo checker grades (connection_width, starved_thermal)

**Tool / command:** `py_tools/check_assembly.py <board> --baseline <input> --intent <intent>` on final_route_old4's board.

**What it claimed:** `R39 <-> R42  courtyard  0.0823mm2 side B  advisory`, `VERDICT: buildable`; its own JSON says `courtyard_severity "error"`, basis `project`.

**What was true:** KiCad's DRC (verifier call 1, and `kicad_drc_compare`: `COURTYARD kicad=1 ... R39<->R42 krt=advisory sev=error`) reports it as a courtyards_overlap error. check_assembly gates a pair only past its floors (area >= 0.5 mm2 or 25 %, AND depth >= 0.3 mm), so a small overlap the board's own severity calls an error is advisory here, and neither board_score nor check_complete sees it. The same KiCad cross-check reports, on every routed board of this run, `connection_width` items under the board's `min_connection` 0.3 (10-12 per board: GND pour necks down to 0.244 mm -- the input's own zone has `min_thickness 0.25`, below its own 0.3 rule -- and one router-made `/CH1/OUT` T-joint at a via, 0.148 mm) and 2 `starved_thermal` GND pads (IC1.4, IC2.4: 1 spoke of 2). `kicad_drc_compare` prints the connwidth count but still says CONSISTENT; no repo grade counts any of them.

**Cost:** found only by the verifier's KiCad cross-check, after a board had been called DONE.

**Repro:**
```bash
python3 -X utf8 py_tools/check_assembly.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb --intent $P/intent.json   # R39 <-> R42 advisory, buildable
python3 -X utf8 tests/stress/kicad_drc_compare.py $P/old4_final.kicad_pcb --baseline $P/pile.kicad_pcb               # COURTYARD kicad=1 ... R39<->R42 krt=advisory sev=error ; connwidth=10@<0.3mm
```

**Existing issues** (`--search "courtyard advisory KiCad error severity"`, `--search "connection_width starved_thermal"`): #1095 CLOSED "check_assembly ignores the project's courtyards_overlap severity" (it now reads the severity, but its floors still downgrade a small overlap); nothing on connection_width or starved_thermal.

---

## 7. Skill: "in a chain pass --clearance-ceiling <floor>" routes BELOW the board's own min_clearance when Board Setup min_clearance > the Default class

**Where:** CLAUDE.md "In a CHAIN, pass `--clearance-ceiling <floor>`, not `--clearance`" and plan-pcb-routing Step 4 ("on the routing steps of a chain, spell it `--clearance-ceiling <value>`").

**What it claims:** the ceiling is the safe chain spelling.

**What was true:** here the Default class is 0.2 and Board Setup min_clearance is 0.3. `--clearance-ceiling 0.3` caps every class at min(class, 0.3) = 0.2: the run routes at 0.2 (`min_clearance_used: 0.2`) and lowers the output project `rules.min_clearance: 0.3 -> 0.2`. Honouring the board's declared floor needed a bare `--clearance 0.3` on every step (what the shipped chain does; route_plan_check accepted it).

**Cost:** small (caught by reading the help before the first route); measured afterwards for this entry.

**Repro:**
```bash
python3 -X utf8 py_router/route.py $P/pour_s3.kicad_pcb $P/ceiling_out.kicad_pcb --nets '*' --clearance-ceiling 0.3 --track-width 0.3 --via-size 1.5 --via-drill 0.3 --escalation board --power-nets GND +12V --power-nets-widths 0.4 0.4 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --quick 2 --json-out $P/ceiling_out.json
# -> "rules.min_clearance: 0.3 -> 0.2 mm", JSON_SUMMARY_MIN min_clearance_used 0.2
```

**Existing issues** (`--search "min_clearance"`): #1160 CLOSED, #1210 CLOSED, #1287 CLOSED touch the floor writeback; none covers the ceiling spelling going under Board Setup min_clearance.

---

## 8. route_planes: does not recognise a multi-layer (F.Cu + B.Cu) same-net zone as existing, adds two more GND zones on top; and a pour step that lays no copper lowers the board's floors

**Tool / command:** `py_router/route_planes.py <board> <out> --nets GND GND --plane-layers F.Cu B.Cu --clearance 0.3` (the skill's "pour first" step) on this board, whose kept board-wide GND pour is ONE zone with `(layers "F.Cu" "B.Cu")`.

**What it claimed:** help: "an existing same-net zone is REPLACED in place (CLI default)"; summary `status ok`, `plane_zones` F.Cu and B.Cu.

**What was true:** the output has 3 GND zones (the original dual-layer one kept, two new single-layer zones at priority 2 over it). With `--skip-existing-zones` it does detect the zone on both layers ("already exists on F.Cu - keeping it"), so the shipped chain uses that. Separately, with `--track-width` / `--via-size` omitted the pour step writes `rules.min_track_width 0.3 -> 0.2`, `min_connection 0.3 -> 0.2` and `min_via_diameter 1.5 -> 0.6` into the output project ("FAB FLOOR RELAXED") although it laid no track and no via.

**Cost:** ~3 min (inspect, rerun with --skip-existing-zones and explicit sizes).

**Repro:**
```bash
python3 -X utf8 py_router/route_planes.py $P/pile.kicad_pcb $P/pour_dup.kicad_pcb --nets GND GND --plane-layers F.Cu B.Cu --clearance 0.3
grep -c '^	(zone' $P/pile.kicad_pcb $P/pour_dup.kicad_pcb     # 1 -> 3 ; log: rules.min_track_width 0.3 -> 0.2, min_via_diameter 1.5 -> 0.6
```

**Existing issues** (`--search "skip-existing-zones multi-layer zone"`, `--search "route_planes duplicate zone"`, `--search "route_planes min_track_width relax"`): none covers either (#598, #483, #488 are other plane defects, all closed).

---

## 9. The router's Hint for a GND island ("Retry with --rip-existing-nets 'Net-(IC5A-IN-)'") is a no-op, and following it to --force-reroute does not join the island either

**Tool / command:** route.py plane finalize on a post-DONE arm (opt/sweep/s2_v200): `GND: (152.05,114.91)<->(151.15,114.93) FAILED (exact-fill strap unroutable)` ... `Hint: ... Retry with --rip-existing-nets 'Net-(IC5A-IN-)'`.

**What it claimed:** that ripping the named net is the retry.

**What was true:** `--nets GND 'Net-(IC5A-IN-)' --rip-existing-nets 'Net-(IC5A-IN-)'` routed 0 nets (WARNING: the net is already connected, `--rip-existing-nets` only rips blockers, pass `--force-reroute`); with `--force-reroute` the net was re-routed, 71 vias, and GND still had 2 components. Narrower GND straps (`--power-nets-widths 0.3 0.4`) did not help either. I abandoned the low-via (v150-v300) arms for this reason.

**Cost:** ~5 min.

**Repro:** route `$P/pour_s3.kicad_pcb` as in gap 5 with `--via-cost 200` (or replay `$R/opt/sweep/s2_v200/` from `r1/s2_fixc.kicad_pcb`), then the two retries above.

**Existing issues** (`--search "rip-existing-nets already fully connected hint"`, `--search "exact-fill strap unroutable"`): #677 OPEN (a diff pair walling later nets) is a different case; nothing matches.

---

## 10. Skill: no step for "every judged seed is NOT BUILDABLE", and the fast-route judge did not rank by the full route's vias

- §3.5 says to read check_assembly's `buildable` after placing, but neither the workflow nor the round stop rule says what to do when place_simple calls every seed legal and check_assembly calls every one unbuildable (gap 1). I fixed the judged seeds before judging them, and recorded the fixes as `after` moves.
- The judge's quick routes put seed 3 first (0 open, 64 vias) and seed 2 at 1 open / 59 vias; full routes of the same placements gave seed 3 **99** vias and seed 2 **92** (92 again with route_review's two turns applied correctly). The full route adds 30-40 vias over the `--quick 2` route on every seed (63->99, 59->92, 65->97, 55->106, 61->104), so the judge's via ranking says little about the shipped board. Not a defect in a tool -- a property worth knowing when optimising vias after DONE.

**Cost:** ~15 min of post-DONE full routes to find the better seed.

**Existing issues:** none searched (skill text, not a tool).
