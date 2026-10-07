# TOOL_GAPS -- fa10 03_complex_hierarchy

Run: `/pcb-free-agent full` on the complex_hierarchy pile, worktree `krt-fa10` at
upstream main `04a2c68d`, 2026-10-07. Result: DONE, 7 vias, verifier PASS.

Ranked by what each gap cost this run. Every command runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) after `export MSYS2_ARG_CONV_EXCL='*'`,
with `R=wk/fa10/03_complex_hierarchy/repro` (inputs copied with `copy_board.py`, so
each `.kicad_pro` travels with its board). Routing is deterministic, and each
routing repro below was re-run from `$R` and matched the numbers quoted.

The issue searches were read-only (`gh issue list --repo drandyhaas/KiCadRoutingTools
--state all --search ...`).

---

## 1. Power-net copper from the plane finalize / KiCad-oracle reconnect ships at 0.4 mm, below `--power-nets-widths 0.6`

**Cost: the biggest one in this run.** It REJECTED 9 of the 20 routed candidates,
including every attempt to move to the better placement (s2) at moderate via
cost. About 25 min of the optimisation phase went to candidates this killed.

- **Tool / command:** `py_router/route.py ... --nets '*' --power-nets '*VAA' '/12Vext' GND HT VCC --power-nets-widths 0.6 0.6 0.6 0.6 0.6`
  on a board with a B.Cu GND pour.
- **What it claimed:** the run's `Power widths:` line and
  `design_rules.narrowed[site="power copper shipped under width"]` disclose it, so
  nothing here is silent. The claim that is not true is closed **#1047**: it says
  the finalize and oracle power copper are now widened by `power_widen.widen_power_copper`
  / `ExactWideCheck`. Measured, neither name exists in this tree:
  `git grep -n "widen_power_copper\|ExactWideCheck\|power_widen" -- '*.py'` returns nothing.
- **What was true:** the oracle's exact-fill tier straps the fragmented GND pour
  with long B.Cu links at 0.4 mm. Its width ladder (`kicad_oracle.py:2644`,
  `for w in sorted({0.2, 0.4, 0.8, round(_net_w, 4)})`) stops at the first width
  that does not fit, so 0.6 is tried once and abandoned. Nothing widens the link
  afterwards where 0.6 fits. Measured GND shortfalls under 0.6, in mm of length:

  | board | mm under |
  |---|---|
  | r6 | 121.9 |
  | r8a | 74.0 of 92.9 |
  | r9 vc1000/vc1200 | 78.9 of 105.4 |
  | r11d | 53.5 of 86.2 |
  | r11c / r7a | 20.4 |
  | r3 | 13.4 (escalation off) |
  | r4a | 1 segment |
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $R/gap4/s2_pour.kicad_pcb $R/out/g4.kicad_pcb --nets '*' --power-nets '*VAA' '/12Vext' 'GND' 'HT' 'VCC' --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --layer-costs 1.0 1.0 --via-cost 800 --json-out $R/out/g4.json
  ```
  The log shows `GND: (152.94,81.12)<->(187.32,131.57)  OK 19 seg(s), 1 via(s), w=0.40mm`
  and `Power widths: GND 74.0/92.9 mm under the requested 0.6 (min 0.4)`.
  `board_score --net-min-widths` with `{"GND": 0.6}` then reads `net_widths` 1.
- **Issues:** #1047 (CLOSED, "widen power copper laid by the plane finalize and oracle
  too") covers exactly this and is closed, yet the pass it names is not in the tree.
  #1033 (CLOSED) covers the bulk-route half.
- **Workaround used:** none that fixed it. I routed other configurations until one
  happened not to need an oracle strap.

## 2. route.py necks a terminal segment by 0.2 um (0.4 -> 0.3998) when its edge sits EXACTLY at clearance

**Cost:** every one of the 20 routed candidates carried 1-9 of these necks. The
first fully routed board was blocking 8, all from them. It took about 9 min, an
`--escalation off` detour that made things worse (gap 5), and a helper
(`helpers/unneck.py`) run on every candidate afterwards.

- **Tool / command:** `route.py` (any run). The code is `single_ended_routing.py:972`,
  `allowed_half = d - own_l - 1e-4  # 1e-4: stay just inside the rule`. The neck fires
  when `allowed_half < width/2`. A terminal whose copper edge is exactly 0.300 mm
  from a foreign pad (legal in KiCad, and common when 0.1 mm-lattice placement
  meets a 0.1 mm routing grid) is necked to `2*(d - 0.3 - 1e-4)` = 0.3998.
- **What it claimed:** `Design rules [...]: 12 feature(s) on 8 net(s) delivered below the requested size (smallest track width 0.3998 mm)`,
  site `terminal neck`. That is disclosed, and true.
- **What was true:** the necks buy no clearance KiCad requires. Widening all of
  them back to 0.4 mm left `check_drc --clearance-margin 0` at 0 violations on
  every board. Measured as `(width 0.3998)` counts before and after: r2 9->0,
  r4a 6->0, r4b 9->0, r4c 8->0, r5a 5->0, r5b 6->0, r7a 6->0, r7b 4->0, r8a 3->0,
  r11c 6->0, r11d 4->0, and 1->0 on six more. The helper reverted none. The one
  leftover, r9_s2_vc1200 1->1, is the run where my helper crashed on a Windows file
  lock before widening anything. Under a per-net width spec equal to the class
  width (0.4), every neck is a `net_widths` blocker.
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $R/gap2/r1_pour.kicad_pcb $R/out/g2.kicad_pcb --nets '*' --power-nets '*VAA' '/12Vext' 'GND' 'HT' 'VCC' --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --json-out $R/out/g2.json
  python3 -X utf8 py_tools/board_score.py $R/out/g2.kicad_pcb --net-min-widths $R/gap2/spec_widths.json --quiet
  ```
  This gives `BLOCKING=8 (... net_widths=8) vias=63 copper_mm=1652.37`, and every
  `design_rules.narrowed` entry is `(0.3998, 'terminal neck')`.
  Then `python3 -X utf8 wk/fa10/03_complex_hierarchy/helpers/unneck.py $R/out/g2.kicad_pcb $R/out/g2u.kicad_pcb --spec $R/gap2/spec_widths.json`
  widens all of them with DRC still 0.
- **Helper written:** `helpers/unneck.py`. It widens segments within 1 um of their
  spec width back to the spec. It keeps a widening only if `check_drc
  --clearance-margin 0` stays at the input's violation count, and otherwise falls
  back to trying the segments one at a time.
- **Issues:** none found for the 1e-4 trigger. Searches: "terminal neck", "neck
  0.3998", "terminal neck clearance margin". The neighbours are #276 and #157
  (CLOSED, terminal grazes; that is where the neck came from) and #173 (CLOSED,
  sub-cell grazes).

## 3. The default `--escalation fab` ratchets the project, and the NEXT step silently routes at the ratcheted clearance

**Cost:** my best raw board (r10: 6 vias, 1535 mm) was unusable, and recovering
from it took a whole round (round 5, about 15 min) re-run with pinned floors.

- **Tool / command:** `route.py` on the s2 placement with `--layer-costs 1 1 --via-cost 1600`
  (default `--escalation fab`). One net rescue routed `Net-(D204-K)` at clearance
  0.2567 and track 0.127, and the writeback then lowered the whole board's floors.
- **What it claimed:** this is disclosed, in `FAB FLOOR RELAXED` and
  `PROJECT_WRITES_JSON: ["rules.min_track_width: 0.2032 -> 0.127 mm", "net_class[Default].clearance: 0.3 -> 0.2567 mm"]`.
- **What was true:** a single net's rescue re-specified every net. The next step,
  a scoped `--nets 'Net-(D204-K)' --force-reroute --escalation off` on that board,
  reported `"min_clearance_used": 0.2567` (r10 log): `--escalation off` did not stop
  it routing below the board's authored 0.3. `board_score` and `check_drc` then grade
  all descendants at 0.2567, unless you pass `--clearance 0.3`.
  `check_complete --authored-from` flags it only while sub-floor COPPER exists
  (UNSOUND on r8b). Once that copper was re-routed it said nothing about a project
  still declaring Default 0.2567 and min_track 0.127 (r10).
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $R/gap4/s2_pour.kicad_pcb $R/out/g5.kicad_pcb --nets '*' --power-nets '*VAA' '/12Vext' 'GND' 'HT' 'VCC' --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --layer-costs 1.0 1.0 --via-cost 1600 --json-out $R/out/g5.json
  ```
  It prints the PROJECT_WRITES above and `"min_clearance_used": 0.2567`. Then a
  scoped route on `$R/out/g5.kicad_pcb` with `--escalation off` reports 0.2567 again.
- **Lever that worked:** `--fab-overrides fab_floors.txt` (the board's own floors:
  via 0.889/0.508, track 0.2032, clearance 0.3, hole 0.25, edge 0.2) plus
  `--no-fix-drc-settings` on every route. With those, `min_clearance_used` stayed
  0.3 and the project kept its authored classes. This is the run-22 recipe from
  memory, and the skill does not mention it.
- **Issues:** #530 (CLOSED; the defaults are a design decision, "completion first,
  disclosed"), #857 (CLOSED). No open issue covers "the next step inherits the
  ratcheted class even under `--escalation off`", nor the skill not naming the
  pinned-floor lever.

## 4. check_weird's `narrow-pad-joint` floor is the board's narrowest track, so unrelated copper hides or reveals a joint

**Cost:** about 10 min of diagnosis, plus one extra whole-board route pass (r13).

- **Tool / command:** `py_router/check_weird.py` (and `check_complete`, which gates
  on it). At `check_weird.py:789`, `min_track_w = min(_widths)` over ALL segments
  on the board is the floor for every net's terminal-web test.
- **What it claimed:** r11a_u read `NO WEIRD THINGS FOUND`. r12, made from it by
  re-routing only `Net-(D204-K)`, read `narrow-pad-joint: 2`, at Q304.2
  (`Net-(Q304-B)`, F.Cu) and C304.2 (GND, B.Cu).
- **What was true:** the copper of `Net-(Q304-B)` and GND is IDENTICAL on the two
  boards (segment-by-segment diff: no difference), and so are their projects. The
  only change is that the board's narrowest track went from 0.2032 (D204-K's rescue)
  to 0.4. A rescue on one net therefore masked a real joint defect on two others.
  A whole-board `route.py --nets '*'` pass then bridged both ("Bridged 2 same-net
  soft joint(s)"). Note that the scoped `--nets` run cannot repair them, by scope.
- **Repro:**
  ```
  python3 -X utf8 py_router/check_weird.py $R/gap6/r11a_u.kicad_pcb    # NO WEIRD THINGS FOUND
  python3 -X utf8 py_router/check_weird.py $R/gap6/r12.kicad_pcb       # narrow-pad-joint: 2
  ```
- **Issues:** #416 (CLOSED) introduced the check. Nothing covers the floor being
  board-global.

## 5. With `--escalation off`, the plane finalize still puts standard-tier 0.45/0.2 vias on GND, and the design-rules disclosure omits them

**Cost:** two rejected candidates (r3, r4a), about 5 min. It also discredited the
"use `--escalation off` for exact sizes" route out of gap 2.

- **Tool / command:** `route.py ... --escalation off` (r3), and the default
  `--escalation fab` (r4a).
- **What it claimed:** `Design rules [--escalation off, --fab-tier auto]: 1 feature(s) on 1 net(s) delivered below the requested size (smallest track width 0.4 mm)`.
  The JSON has `fab_tier_escalations: 0` and `min_delivered: {track_width: 0.4}`.
- **What was true:** the output carries 2 GND vias at **0.45/0.2 mm**, below the
  board's own `min_via_diameter` 0.889 / `min_through_hole_diameter` 0.508 and the
  class via 1.651/0.6. They are not mentioned anywhere in `design_rules`.
  `check_drc --min-via-diameter 0.889 --min-via-drill 0.508` reports
  `VIA-SIZE violations (2): Via:GND diameter too small for fab`. The log calls them
  "Added 8 tap segments, 2 tap vias".
- **Repro:**
  ```
  python3 -X utf8 py_router/route.py $R/gap2/r1_pour.kicad_pcb $R/out/g7.kicad_pcb --nets '*' --power-nets '*VAA' '/12Vext' 'GND' 'HT' 'VCC' --power-nets-widths 0.6 0.6 0.6 0.6 0.6 --escalation off --json-out $R/out/g7.json
  python3 -X utf8 py_router/check_drc.py $R/out/g7.kicad_pcb --min-via-diameter 0.889 --min-via-drill 0.508
  ```
  This gives 2 GND vias (0.45, 0.2). `g7.json` `design_rules.fab_tier_escalations` = 0.
- **Issues:** #857 (CLOSED, "--fab-tier standard escalates below the selected floor
  silently") is the closest. #842 (CLOSED) made `--escalation off` exact for
  widths. Nothing covers the finalize's tap via under `off`.

## 6. place_seed (and rank_rotations) refuse a pile as "already PLACED" once the one fixed part is placed

**Cost:** about 3 min (one refused seed, one refused 4-arm ranking, both re-run
with `--force`).

- **Tool / command:** the skill's own order (§3/§4: lock the fixed parts with
  `place_pose`, then `place_seed`). `place_pose ... set Q304 129.794 96.52 --rot 0 lock Q304`,
  then `place_seed p01_q304.kicad_pcb out --intent intent.json`.
- **What it claimed:** `place_seed: this board already looks PLACED ... --force to re-seed anyway.`
  (exit 3). `rank_rotations` then refused all arms (`refused: board_placed`).
- **What was true:** 67 of 68 parts were still in the staging pile.
  `board_brief` on the same board says `"pile": true, "unplaced": false` (99% of
  footprints outside the outline). `place_seed.py:1070` tests only
  `st.unplaced` / `st.partially_unplaced`, not the pile predicate #1109 added to
  board_brief. `--force` does the right thing: the locked part is kept.
- **Repro:**
  ```
  python3 -X utf8 py_placer/place_seed.py $R/gap1/p01_q304.kicad_pcb $R/out/g1.kicad_pcb --intent $R/gap1/intent.json   # exit 3
  python3 -X utf8 py_tools/board_brief.py $R/gap1/p01_q304.kicad_pcb --json $R/out/g1_brief.json             # pile true, unplaced false
  ```
- **Issues:** #1109 (CLOSED) fixed board_brief's side and asked for "one pile
  predicate, shared by both". place_seed still uses the other one.

## 7. measure.py cannot find the transcript of a session that runs from a different checkout (or as a subagent)

**Cost:** about 3 min.

- **Tool / command:** the skill's §6.4 command,
  `python3 -X utf8 .claude/skills/pcb-free-agent/scripts/measure.py --root .`
  run from the worktree.
- **What it claimed:** `refuse: no transcript under C:\Users\rob\.claude\projects\C--Users-rob-Documents-prive-git-krt-fa10` (exit 1).
- **What was true:** this session's cwd is the primary checkout, and it is a
  subagent, so its transcript is
  `...\C--Users-rob-Documents-prive-git-KiCadRoutingTools\<parent>\subagents\agent-<id>.jsonl`.
  Passing that path positionally works.
- **Repro:** the command above, from the worktree, in any subagent session.
- **Issues:** none found (search "measure.py transcript subagent").

## 8. `check_complete --authored-from` is INCOMPLETE on every board solely because the input declares a 0.0 copper-to-hole floor

**Cost:** about 2 min (and it makes `grade.py`'s `check_complete_authored` read
INCOMPLETE on a clean board).

- **Tool / command:** `check_complete.py <board> --intent <i> --authored-from <input>`.
- **What it claimed:** `VERDICT: INCOMPLETE -- declared fab floor(s) NOT measured by this check ... copper-to-hole clearance (declared 0.0)` (exit 4).
- **What was true:** a 0.0 floor is honoured by any board. `check_drc` grades
  copper-to-hole at the 0.3 class clearance and found 0 violations (verifier and
  me). It is the only item listed, on every board.
- **Repro:**
  ```
  python3 -X utf8 check_complete.py $R/gap3/r2u_unneck.kicad_pcb --intent $R/gap3/intent.json --authored-from $R/gap3/input.kicad_pcb   # exit 4
  ```
- **Issues:** none found (search "authored-from hole clearance", "copper-to-hole
  clearance declared 0"). #1038 (CLOSED) is about the NPTH clearance itself.

## 9. make_film plays the ledger in record order, so two parallel placement lineages render as the whole board flying back and forth

**Cost:** none to the board; it costs the film's readability.

- **Tool / command:** `python3 -X utf8 py_tools/make_film.py --from-ledger wk/fa10/03_complex_hierarchy/ledger.jsonl --theme light --aspect 4:3 -o ...`
- **What it claimed:** the caption at row i11 reads `moving 67 part(s)`.
- **What was true:** no part moved in that step. Row i11 (a route of placement
  s1) was recorded right after row i10 (placement s2, a parallel lineage). Every
  row carries the right `--parent` (`parent_sha`), but the film interpolates
  between consecutive rows regardless. `--accepted-only` does not help, because
  the accepted rows of the two lineages also interleave (i10 s2 placement, i11/i12
  s1 routes, i25 s2 route).
- **Repro:** the command above. Then
  `ffmpeg -ss 30 -i wk/fa10/03_complex_hierarchy/03_complex_hierarchy_film.mp4 -frames:v 1 f30.png`
  shows the i11 caption `moving 67 part(s)`.
- **Issues:** #1034 (CLOSED) fixed `parent_sha` for parallel lineages in the
  LEDGER; nothing covers the film following it (search "make_film parent lineage").
