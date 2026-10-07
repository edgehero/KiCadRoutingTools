# TOOL_GAPS -- fa10 board 02 (sonde_xilinx)

Ranked by what each cost this run. Every command runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) after `export MSYS2_ARG_CONV_EXCL='*'`.
Repro inputs are in `wk/fa10/02_sonde_xilinx/repro/` (abbreviated `R=wk/fa10/02_sonde_xilinx/repro` below).
Issue searches are read-only `gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search "..."`.

---

## 1. A reversed edge-mount receptacle passes every placement instrument (J2 shell placed ON the board)

**Cost: highest -- ~25 min and an invalid first DONE.** Everything from 03:53 to 04:15 (seed, 6 routes,
a 10-seed compare that I killed, a rotation ranking) was built on a board whose DB9 shell lay over the
board, and the first "DONE" (04:07, `route/s0_rbd.kicad_pcb`) was physically unbuildable.

**Tools and commands.** `place_pose.py ... set J2 181.71 88.9 --rot 90`, then `check_floorplan.py --intent`,
`board_context.py`, `check_assembly.py`, `place_seed.py`, `board_score.py`, `check_complete.py`.

**What they claimed.** place_pose: `no_worse true`, `mating_keepout_count_after 0`. check_floorplan:
`J2 east: overhang 0.5140mm [legacy_occupancy@margin=0.254] pass`, 0 errors. board_context:
`Mating face **E**, 0.0mm from that edge, overhanging it by 0.26mm`. check_assembly: `buildable (blocking 0)`.
board_score blocking 0 and check_complete DONE on the routed board.

**What was true.** J2 is a B-side `DSUB-9_Male_EdgeMount` whose file-local frame is Y-mirrored relative to
the F-side J1 (PCB-edge line at local y = -1.99, B.CrtYd shell out to local y = -16.19). At rot 90 the shell
points WEST, into the board: its courtyard spans x 165.52..183.96 on a board whose east edge is x 183.7, i.e.
the connector body sits over 14 mm of the board and the mating face points inward. The same part at rot 270
(the correct pose, used from 04:15 on) measures courtyard x 179.46..197.9, and the same tools then report
`overhang 14.4540mm` / `overhanging it by 14.2mm`. Both poses PASS: no instrument distinguishes a shell
over the board from a shell off it, because the edge rule reads the pad edge and a minimum-free overhang.
The B-side render (`seeds/s0_placement_B.png`) is the only place it shows -- a 31 x 18 mm J2 box inside the outline.
The source's own seat (`-13.60 mm from the edge`, README) was the only hint that ~14 mm of overhang was expected.

**Reproduce.**
```
python3 -X utf8 py_tools/check_floorplan.py $R/p0_connectors_locked.kicad_pcb --intent $R/intent.json   # J2 east: overhang 0.5140mm ... pass, 0 error(s)
python3 -X utf8 py_tools/board_context.py $R/p0_connectors_locked.kicad_pcb --md | grep -A4 "### J2"      # Mating face E ... overhanging it by 0.26mm
python3 -X utf8 py_tools/check_assembly.py $R/p0_connectors_locked.kicad_pcb --intent $R/intent.json      # no J2 finding
```
(`p0_connectors_locked` = input board + `place_pose set J1 105.29 88.9 --rot 270 set J2 181.71 88.9 --rot 90 lock J1 J2`.)

**Existing issues.** None found: searched "edge receptacle overhang mating" (only #891, the context sheet,
closed) and "edge connector reversed body" (no results).

---

## 2. route.py's in-run plane finalize ships stacked duplicate copper silently, so check_complete refuses the board

**Cost: ~10 min plus a helper (`helpers/dedup_stacked.py`) that every routed board in this run then needed.**
Without it no board reached check_complete DONE (it removed 42, 10, 10, 6 duplicate GND segments on four of the
routed boards).

**Tool and command.** `py_router/route.py <seed> <out> --nets '*' --escalation off --layer-costs 1.0 1.0 --via-cost 150`.

**What it claimed.** `Single-ended: 26/26 routed`, `Multi-point: 66/66 pads connected`, no stacked-copper
line anywhere in the log or `--json-out` (CLAUDE.md: whatever still stacks "is named in the summary rather than
shipped silently"). A second `route.py --nets '*'` pass over the output also left all of it in place.

**What was true.** `check_weird`: `stacked-copper: 36` (40 exact duplicate keys, some tripled), all GND F.Cu at
J2's F.Cu GND pads, where the finalize's pad repair re-traced the same tap path for J2.6..J2.9 to a shared via
("Pad J2.6 (F.Cu)... reused via at (182.40, 96.50), 35 trace segment(s)"). check_complete:
`VERDICT: INCOMPLETE -- weird_copper: not clean (exit 1)` while board_score said blocking 0.

**Reproduce.**
```
python3 -X utf8 py_router/check_weird.py $R/s0_rb_stacked.kicad_pcb                      # stacked-copper: 36
python3 -X utf8 py_router/route.py $R/s0_seed.kicad_pcb $R/_s0_rb.kicad_pcb --nets '*' --escalation off --layer-costs 1.0 1.0 --via-cost 150
python3 -X utf8 py_router/check_weird.py $R/_s0_rb.kicad_pcb                             # stacked-copper: 36 again (deterministic)
```

**Existing issues.** #162 (OPEN, "Same-net redundant copper ... find the producers, remove delete-only") covers
the class; #606 (closed) added the trim pass that does not reach this producer. This run adds a measured producer:
the plane finalize's pad repair.

---

## 3. check_complete (via check_orphan_stubs) refuses a near-miss joint that check_weird, check_connected and KiCad all accept

**Cost: ~8 min and one routing round** (the first 0-via board, `sweep2/s9_r`, could not be called DONE).

**Tools.** route.py wrote the joint; `py_tools/check_orphan_stubs.py --layer B.Cu` (run by `check_complete.py`)
flags it; `py_router/check_weird.py`, `py_router/check_connected.py`, `py_tools/kicad_unconnected.py` pass it.

**What they claimed.** check_complete: `INCOMPLETE -- orphan_stubs: 1 layer(s) carry orphan stubs`
(`VCC on B.Cu: 1 orphans (137.65, 91.85)`). check_weird: `NO WEIRD THINGS FOUND!` (its soft-joint rule did not
fire). check_connected: `ALL NETS FULLY CONNECTED!`. KiCad oracle: `KICAD_UNCONNECTED: 0`. board_score blocking 0.

**What was true.** The VCC B.Cu branch (137.655, 91.855)->(141.5, 95.7) ends 0.547 mm from the trunk's endpoint
(138.2, 91.9); both are 0.635 mm tracks, so the round caps overlap by 0.088 mm but neither anchor lies inside the
other track. KiCad counts the overlap as connected. The off-grid endpoint looks like a smoothing artifact.
Two repo instruments give opposite verdicts on the same joint, and check_complete sides with the stricter one, so
a board KiCad calls complete is reported INCOMPLETE. Whichever answer is right, the router should not write it
and the two checkers should agree. (I avoided it by re-routing with `--layer-costs 1.0 2.0`, which happened not
to produce one.)

**Reproduce.**
```
python3 -X utf8 py_tools/check_orphan_stubs.py $R/p2s9_orphan_vcc.kicad_pcb --layer B.Cu   # 1 orphan (137.65, 91.85)
python3 -X utf8 py_router/check_weird.py $R/p2s9_orphan_vcc.kicad_pcb                      # NO WEIRD THINGS FOUND!
python3 -X utf8 py_tools/kicad_unconnected.py $R/p2s9_orphan_vcc.kicad_pcb                 # KICAD_UNCONNECTED: 0
python3 -X utf8 check_complete.py $R/p2s9_orphan_vcc.kicad_pcb --intent $R/intent.json     # INCOMPLETE -- orphan_stubs
```

**Existing issues.** #601 (closed) is the inverse case (check_connected passing a real gap that only
check_orphan_stubs caught). Nothing found for this direction ("orphan stub soft joint endpoint", "check_orphan_stubs").

---

## 4. route.py's plane finalize ships a GND soft joint and an edge-clearance graze (2 real DRC)

**Cost: ~5 min, one routing round** (`cand/u180s0_r1000`, 4 vias, rejected).

**Tool and command.** `route.py cand/u180s0.kicad_pcb ... --nets '*' --escalation off --layer-costs 1.0 1.0 --via-cost 1000`.

**What it claimed.** `Single-ended: 26/26 routed`, `KiCad-oracle recheck: KiCad reports all processed nets complete`.

**What was true.** check_drc: `SEGMENT-ENDPOINT-GAP` on GND B.Cu, gap 1.100 mm with cap overlap 0.018 mm at
(138.0, 74.5)-(136.9, 74.5), and `SEGMENT-BOARD-EDGE` GND B.Cu 0.028 mm inside the 0.2 mm edge clearance at
(130.2, 67.9). board_score `drc=2`, check_complete INCOMPLETE. Both are GND copper added by the in-run plane finalize
(the 0.2 mm edge floor is one route_planes/route.py itself wrote into the project: `rules.min_copper_edge_clearance:
0.01 -> 0.2 mm (fab-edge pin)`).

**Reproduce.**
```
python3 -X utf8 py_router/route.py $R/u180s0_placed.kicad_pcb $R/_u180s0_r1000.kicad_pcb --nets '*' --escalation off --layer-costs 1.0 1.0 --via-cost 1000
python3 -X utf8 py_router/check_drc.py $R/_u180s0_r1000.kicad_pcb --baseline wk/fa10/02_sonde_xilinx/sonde_xilinx.kicad_pcb   # 2 violations
```

**Existing issues.** Nothing specific found ("plane finalize soft joint board edge" -> #658, unrelated).

---

## 5. place_seed refuses a pile as "already PLACED" once the connectors are seated, the order the skill prescribes

**Cost: ~3 min, and `--force` / `--seed-args='--force'` on every later seed, compare_seeds and rank_rotations call.**

**Tool and command.** `place_seed.py <p0> <out> --intent intent.json` where p0 = input pile + J1/J2 seated and locked
(skill section 4: "Place and lock the connectors and mechanically fixed parts first ... Then zone the rest and seed").

**What it claimed.** `place_seed: this board already looks PLACED. Seeding would discard that placement; use
place_portfolio.py ... or --force`, exit 3.

**What was true.** 23 of 25 parts were still in the staging pile; board_brief on the same board says
`state: PILE`, `pile: true`. `placement_state` decides `unplaced = s1 or (s2 and s3) or ...`: seating J1 at
x 105 and J2 at x 182 widened the footprint spread past the s2 threshold, the pile is a grid (no coincident
stack, so s1 false and no `partially_unplaced` suspects), so the pile read as placed. place_seed gates on
`unplaced`/`partially_unplaced`, not on board_brief's `pile` (the #1109 split, now at the seeder's own gate).
`--force` did the right thing (locked J1/J2 were kept).

**Reproduce.**
```
python3 -X utf8 py_placer/place_seed.py $R/p0_connectors_locked.kicad_pcb $R/_refused.kicad_pcb --intent $R/intent.json   # exit 3
python3 -X utf8 py_tools/board_brief.py $R/p0_connectors_locked.kicad_pcb --json $R/_brief.json                      # pile: true
```

**Existing issues.** None found ("place_seed already looks PLACED", "partially unplaced pile connectors").

---

## 6. route.py leaves dangling GND vias (and stacked copper) at J1 that check_weird flags

**Cost: ~4 min** (one board rejected, plus a re-run to prove my dedup helper did not cause it).

**Tool and command.** `route.py repro/s0_seed.kicad_pcb ... --nets '*' --escalation off --layer-costs 1.0 1.0 --via-cost 400`.

**What it claimed.** Clean completion; nothing about dangling vias.

**What was true.** check_weird on the raw output: `dangling-via: 2` -- GND vias at (108.2, 91.1) and (108.2, 104.0)
that "spans 2 layer(s) but joins none (KiCad via_dangling)", next to J1's B.Cu GND pads -- plus `stacked-copper: 2`.

**Reproduce.**
```
python3 -X utf8 py_router/check_weird.py $R/s0_vc400b_routed.kicad_pcb    # dangling-via: 2, stacked-copper: 2
```

**Existing issues.** None found for the dangling vias ("dangling via route" -> #1058/#695, different mechanisms).

---

## 7. compare_seeds / rank_rotations rank by crossings when every probe routes, and crossings did not predict vias

**Cost: ~5 min** -- I wrote my own seed sweep (inline shell loop: seed, route with my recipe, dedup, score) because
neither tool reports the probe's via count or copper.

**What they claimed.** rank_rotations: `probe: 0 failure(s)` for every arm, then ranked by crossings/hpwl.

**What was true.** My 10-seed sweep at the same intent (U1@180): polish crossings vs routed vias were
seed 4: 28 -> 12 vias, seed 0: 29 -> 3, seed 7: 45 -> 1, seed 9: 46 -> 10. The fewest-crossing seed was among the
worst for vias; the via-minimal seed had above-median crossings. On a board where every seed completes, the
rankers have no way to order by the post-DONE objective (vias, then copper).

**Reproduce.** `cat wk/fa10/02_sonde_xilinx/sweep/summary.txt` (seed crossings from `sweep/sN.seed.log` vs routed vias).

**Existing issues.** None found ("compare_seeds via count probe", "rank_rotations crossings vias").

---

## 8. check_assembly labels pads 0.25 mm INSIDE the outline as "pad copper off-board"

**Cost: ~2 min.**

**What it claimed.** `2 part(s) with pad copper off-board: J1 (0.004mm), J2 (0.004mm)` (still `buildable`).

**What was true.** J1/J2 pad copper sits 0.25 mm inside the outline (pad edge x 103.55 vs edge 103.3; 183.45 vs 183.7).
The 0.004 mm is the pad AABB vs the outline inflated by the 0.254 mm pad clearance, i.e. a clearance shortfall,
not copper off the board. render_placement's `checklist.a_off_outline.pad_copper` is empty for the same board.

**Reproduce.** `python3 -X utf8 py_tools/check_assembly.py $R/u180s0_placed.kicad_pcb --intent $R/intent.json | grep "off-board"`

**Existing issues.** None found ("check_assembly pad copper off-board edge clearance").

---

## 9. measure.py cannot find a teammate's transcript, and the one it can find is the wrong session

**Cost: ~3 min.**

**What it claimed.** `measure.py --root .` -> `refuse: no transcript under ...C--Users-rob-Documents-prive-git-krt-fa10`.
Pointed at the session file beside the primary checkout's project dir it printed a confident
`wall_clock = 2 days, 7:06:20`, 24 agent spawns -- the orchestrator's session, not this run.

**What was true.** This run's transcript is `.../<parent-session>/subagents/agent-<id>.jsonl`; measured there it is
1:13 wall clock at hand-back time, 1 agent spawn. measure.py does not check that the transcript it reads is the run it
is asked about.

**Reproduce.** `python3 -X utf8 .claude/skills/pcb-free-agent/scripts/measure.py --root .`

**Existing issues.** Not searched separately (skill-script issue, low cost).

---

## Helper written

- `helpers/dedup_stacked.py` -- removes exact same-net duplicate `(segment ...)` blocks (same net, layer, width and
  unordered endpoints; keeps the first). Needed because of gap 2: no repo tool removes stacked copper, and
  check_complete refuses a board that carries it. Used on every routed board; on the final board it removed 0.
