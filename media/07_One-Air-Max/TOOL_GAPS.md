# TOOL_GAPS -- fa10 board 07 (One-Air-Max)

Ranked by what each cost this run. Every command runs from the worktree root
(`C:/Users/rob/Documents/prive/git/krt-fa10`) after
`export MSYS2_ARG_CONV_EXCL='*'`; repro inputs live in `wk/fa10/07_One-Air-Max/repro/`.
`D=wk/fa10/07_One-Air-Max` below.

---

## 1. check_connected grades the no-net pseudo-net (net 0), so `board_score` can never reach blocking 0 on this board

**Cost:** the run's DONE. Every routed board scores `blocking 6` with all real nets connected, so
`check_complete` says INCOMPLETE and the verifier must FAIL. No routing or placement can clear it.

**Tool and command:** `py_router/check_connected.py` (read by `py_tools/board_score.py` -> `components.broken`,
and by `check_complete.py`).

**What it claimed:** on the routed board r02f, `board_score`: `blocking 6`, `blocking_by.broken 6`,
`components.broken.nets {}` (no names); `check_complete`: `VERDICT: INCOMPLETE -- blocking = 6`.

**What was true:** the only finding is `(net 0): Segments: 9, Vias: 0, Pads: 7, Disconnected components: 7`.
Net 0 is "no net". Its 7 pads are no-net pads (plated holes of USB1 x2, DC1 x2 and BAT1, plus the no-net exposed
pad 9 of Q1 and of Q2, as verifier 2 measured), and its 9 "segments" are footprint copper the parser models as net-0
graphic segments since #908 (JP2 x4 and
JP3 x4 solder-jumper bridges, F2 x1 PCB-trace fuse). `check_connected`'s no-component path excludes net 0 only
implicitly ("net 0 has no segments/vias", comment near line 1892), so once footprint copper exists net 0 qualifies
and 7 components score 7 - 1 = 6 broken. KiCad's own oracle on the same board: `KICAD_UNCONNECTED: 0`.
route.py's regrade: `pad_pairs_open 0`. The untouched INPUT board already shows the same `(net 0)` block
(6 components), so it predates anything this run did. `components.broken.nets` is `{}` because board_score's
name regex needs a non-empty net name.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_connected.py wk/fa10/07_One-Air-Max/One-Air-Max.kicad_pcb | grep -A4 "(net 0)"
python3 -X utf8 py_tools/kicad_unconnected.py wk/fa10/07_One-Air-Max/repro/r02f.kicad_pcb        # KICAD_UNCONNECTED: 0
python3 -X utf8 py_tools/board_score.py wk/fa10/07_One-Air-Max/repro/r02f.kicad_pcb --json wk/fa10/07_One-Air-Max/repro/s.json --quiet >/dev/null  # blocking 6
```

**Existing issues:** `gh issue list --search "no-net pseudo-net"` -> #497 (CLOSED, "pcb_data.nets disagrees three
ways about net 0 ... it should be in none of them"): this is a regression path around that fix, opened by #908's
net-0 graphic segments. `--search "net 0 check_connected"`: nothing that covers it (#1157, #984 are different).

---

## 1b. The router and every repo checker treat a FILLED board graphic as its outline, so route.py put a +3V3 via inside USB1's exposed shield copper and nothing but KiCad noticed

**Cost:** a verifier call (FAIL), about 25 minutes to fix (remove the via, two rule areas, a finalize pass, a prune),
and a real short that check_drc, check_connected and board_score all passed.

**Tool and command:** `py_router/route.py` (r07: `--via-cost 300`), graded by `py_router/check_drc.py --baseline
... --clearance-margin 0.1` (`NO DRC VIOLATIONS FOUND!`), `check_connected` and `board_score` (`drc 0`).

**What was true:** the input draws USB1's shield as two filled, mask-exposed F.Cu `gr_rect`s on Net-(C1-Pad2)
((129.06,115.97)-(130.36,122.27) and (138.26,115.97)-(139.56,122.27), the 8 "NET-TAGGED copper graphic segments" every
tool warns about). The parser keeps only their 4 perimeter segments, so the interior is free space for the router.
r07 put a 0.6 mm +3V3 via at (129.70,118.80), 0.26 mm inside the left rectangle. KiCad 10's own DRC (read through
`kicad_unconnected.py --json`) reports `shorting_items` +3V3 <-> Net-(C1-Pad2) plus 6 `solder_mask_bridge`; error
items 31 vs the 24 footprint-intrinsic ones on r06f/r14p. The independent verifier found it.
Fix that held: removed the via and its 3 stub segments, added two vias-only rule areas over the rectangles
(`helpers/add_rule_area.py ... --allow-tracks --allow-pour`; the perimeter already keeps tracks out), re-ran the
finalize, pruned 17 dead stub segments: KiCad DRC back to 24.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_drc.py wk/fa10/07_One-Air-Max/repro/r07f.kicad_pcb --baseline wk/fa10/07_One-Air-Max/One-Air-Max.kicad_pcb --clearance-margin 0.1 | tail -3   # NO DRC VIOLATIONS
python3 -X utf8 py_tools/kicad_unconnected.py wk/fa10/07_One-Air-Max/repro/r07f.kicad_pcb --json wk/fa10/07_One-Air-Max/repro/kdrc_r07f.json
python3 -X utf8 -c "import json;print([v['type'] for v in json.load(open('wk/fa10/07_One-Air-Max/repro/kdrc_r07f.json'))['violations'] if 'Net-(C1-Pad2)' in str(v) and '+3V3' in str(v)])"
```

**Existing issues:** `--search "filled graphic copper"` / `"gr_rect fill copper obstacle"` -> #908 (CLOSED, "footprint
fp_poly copper is invisible to the router and check_drc"), whose fix models such copper by its PERIMETER only, never the
interior fill (stated in CLAUDE.md): this short is that choice's failure mode, for a board-level filled `gr_rect`.
#513 (CLOSED roll-up) and #337 cover net-tagged board graphics as obstacles. No issue covers a via landing inside one.

---

## 2. Placement engines see a courtyard-less part as its PAD box; check_assembly grades its FAB body, so every seed is NOT BUILDABLE and no repair tool can see why

**Cost:** about 50 minutes (04:05-04:55Z): 8 seeds, a repair, a reseat and hand nudges before I found the cause, plus a
helper (`helpers/add_fab_courtyards.py`).

**Tools and commands:** `py_placer/place_seed.py` (seat search and polish), `place_seed --repair`, `place_seed --reseat`,
`py_placer/place_pose.py`, versus `py_tools/check_assembly.py --baseline`.

**What they claimed:** place_seed exit 0 / "0 grade errors" on seeds 1-3. `place_seed --repair --dry-run` on s180_0p:
`Repair census: 0 conflict pair(s) ... Repair: 0 violator(s)`. `place_seed --reseat C27 D6 JP3 U8`: `GATE REFUSED`,
`overlap 0.4323->0.4323` (its overlap basis reads 0.43 mm2). place_seed prints `WARNING [quench]: 197 footprint(s)
have no courtyard (F/B.CrtYd) and fall back to their pad bounding box`.

**What was true:** `check_assembly --baseline One-Air-Max.kicad_pcb` grades the same boards' courtyard channel from each
part's FAB body (`BODY COVERAGE: 204 of 210 ... (197 fab, 7 silk)`). Bodies larger than their pads get packed into
neighbours by every seed: seed0 6 courtyard-blocking pairs, seed1 5, seed2 6, seed3 8, the decap-claim seed 9, all
`VERDICT: NOT BUILDABLE`. On s180_0q the four gating pairs total 12.5 mm2 (C27<->L1 6.40, U5<->U8 3.45, D6<->D7 1.61,
JP3<->U12 1.02) where the reseat gate measured 0.43. U8's body extends 1.16 mm past its pads, L1's 1.58 mm. No tool
moves parts to clear `courtyard_blocking` (grep: no mover in py_placer consumes it). After writing a courtyard from
each part's own fab outline (+0.1 mm), the very next seed had 0 back-side gating pairs and 0 advisory pairs.

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_assembly.py $D/repro/s180_0q.kicad_pcb --intent $D/repro/intent_v2_u5r180.json --baseline $D/One-Air-Max.kicad_pcb   # NOT BUILDABLE, 4 COURTYARD-BLOCKING
python3 -X utf8 py_placer/place_seed.py $D/repro/s180_0q.kicad_pcb wk/fa10/07_One-Air-Max/repro/x.kicad_pcb --intent $D/repro/intent_v2_u5r180.json --repair --dry-run  # 0 violator(s)
python3 -X utf8 py_placer/place_seed.py $D/repro/s180_0q.kicad_pcb wk/fa10/07_One-Air-Max/repro/x.kicad_pcb --intent $D/repro/intent_v2_u5r180.json --reseat C27 D6 JP3 U8  # GATE REFUSED, overlap 0.4323
```

**Existing issues:** `--search "courtyard pad bounding box fab body"` -> #896 (CLOSED, "one body model for
courtyard-less libraries", whose proposal included "legality/seeder"), #1106 (CLOSED, parts with no courtyard AND no
fab body). The seeder half of #896 is not in effect on this board (its own warning says it falls back to pad boxes).
`--search "courtyard_blocking repair"`: none.

---

## 3. board_score and the verifier's check_assembly call cannot see what check_assembly --baseline gates

**Cost:** low in time; high in risk -- a fudged "buildable" was one command away.

**What they claimed:** `board_score --baseline` on s180_0q: `assembly 0`, `buildable True`,
`conjuncts.courtyard_blocking_gating: None` (unmeasured). `check_assembly --intent intent.json` (no `--baseline`,
the exact form in `references/verifier.md`) on repro/seed_given_intent.kicad_pcb: `VERDICT: buildable (blocking 0)`
with 22 courtyard-blocking pairs listed as REPORT-ONLY.

**What was true:** that seed (the GIVEN intent, no keep-outs) put DC1 (78.2 mm2), PWR_SW1 (53.7 mm2), Solarpower1, C10,
C13 and Battery1's leads inside the 18650 holder, and U1 over SW1 (38.7 mm2) and USB1 (22.4 mm2).
`check_assembly --baseline One-Air-Max.kicad_pcb` on the same file: `22 of 22 GATE`, `VERDICT: NOT BUILDABLE`.
BAT1 is classed a "container" (pad box >= 50% of the board, `legality.CONTAINER_RATIO`), so `BAT1<->Battery1` is
`waived:container_class` -- an 18650 holder is a body, not a frame.

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_assembly.py $D/repro/seed_given_intent.kicad_pcb --intent $D/intent.json            # buildable
python3 -X utf8 py_tools/check_assembly.py $D/repro/seed_given_intent.kicad_pcb --intent $D/intent.json --baseline $D/One-Air-Max.kicad_pcb  # NOT BUILDABLE
```

**Existing issues:** `--search "board_score courtyard_blocking_gating"` -> #964 (CLOSED, a different channel);
`--search "check_assembly baseline buildable courtyard"` -> #918 (CLOSED, "blocking == 0 is not buildable"), related
but this conjunct is still unmeasured. `--search "container courtyard battery"`: none.

---

## 4. route.py's plane finalize joins +3V3 pour islands with up to 2.0 mm tracks ON THE GND PLANE LAYER, and the only lever to stop it costs completion

**Cost:** one 45-minute re-route (r03) that came out worse, plus the quality of the shipped board.

**Tool and command:** `py_router/route.py --nets '*' --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 1.5 3.0 1.0`
(the plan-pcb-routing recipe: 3.0 on the solid-plane layer). In2.Cu is the board's solid GND layer, In1.Cu carries the
+3V3 pour.

**What it claimed:** r01 `JSON_SUMMARY_MIN`: routed 120, failed 0, `pad_pairs_open 0` -- a clean run.

**What was true:** on r02 the +3V3 net has 228 segments on In2.Cu, many 1.6-2.0 mm wide (e.g. a 2.0 mm run
(176.5,64.1)-(183.6,59.5) and a 1.6 mm run (119.0,108.0)-(146.1,112.6)), plus a dead +3V3 branch on In2 (item 6).
The log shows the finalize joining regions with a width ladder: `Joining 40 regions incrementally ... OK width=2.00mm`.
Signals routed on In1 cut the +3V3 pour into islands; the joins then cross the GND plane. Forbidding In2
(`--layer-costs 1.0 3.0 -1 1.0`, r03) stopped it but routed worse: 4 failed nets, 2 open pad pairs, blocking 10,
481 vias vs 471.

**Reproduce:** count +3V3 segments per layer and width on `wk/fa10/07_One-Air-Max/repro/r02.kicad_pcb` with
`kicad_parser.parse_kicad_pcb` (228 on In2.Cu, widths {0.3, 0.4, 0.8, 1.6, 2.0}); and
`grep -n "OK width=2.00mm" wk/fa10/07_One-Air-Max/repro/r01.log`.

**Existing issues:** `--search "region join In2 plane width"` -> nothing specific (#162 is about duplicates; #662/#544
are older pour work).

---

## 5. route.py leaves same-net duplicate segments (240), check_complete then fails weird_copper, and a duplicate hides a dangling end

**Cost:** about 15 minutes and a helper (`helpers/dedupe_segments.py`).

**What it claimed:** route.py r01 prints `WARNING: 84 stacked-copper finding(s) on the write model` mid-run and ships
`stacked_copper` with 240 entries in `--json-out` -- disclosed, never removed. `check_complete`: `weird_copper: not clean`.

**What was true:** 245 exact duplicates (same net, layer, both endpoints) on GND and +3V3 across all four layers.
Dropping them changed no copper and check_drc stayed clean. After the drop, check_weird reported a +3V3 In1.Cu dangling
end at (160.4,77.7) that it had NOT reported on r01: the duplicate gave the free end a second segment end, so the
dangling-end census missed it.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_weird.py wk/fa10/07_One-Air-Max/repro/r01.kicad_pcb | grep -E "stacked-copper:|dangling-end:"   # 222 / 1
python3 -X utf8 wk/fa10/07_One-Air-Max/helpers/dedupe_segments.py wk/fa10/07_One-Air-Max/repro/r01.kicad_pcb wk/fa10/07_One-Air-Max/repro/r01d_check.kicad_pcb
python3 -X utf8 py_router/check_weird.py wk/fa10/07_One-Air-Max/repro/r01d_check.kicad_pcb | grep -E "stacked-copper:|dangling-end:"   # 0 / 2
```

**Existing issues:** #162 (OPEN, "Same-net redundant copper (self-crossings + stacked duplicates): find the producers,
remove delete-only") covers the duplicates; #606 (CLOSED, "add a trim pass") did not prevent these. The masked
dangling end is not covered by any issue I found.

---

## 6. A dead +3V3 branch survives route.py's own finalize, and no CLI removes a named piece of copper

**Cost:** about 15 minutes, one scoped route pass (r02) and a helper (`helpers/remove_copper.py`).

**What it claimed:** `route.py --nets +3V3` on the deduped board (finalize only, "nothing to route") pruned the two
+3V3 stubs and exited 0.

**What was true:** check_weird on r02 still reports `dangling via: same-net copper reaches it on In2.Cu only, so it
spans 4 layer(s) but joins none (KiCad via_dangling)` at (162.6, 86.4): a through via feeding only two parallel 0.8 mm
In2.Cu runs back to IO1.3's via. Removing that via and its 8 In2 segments left check_weird, check_orphan_stubs,
kicad_unconnected (0) and check_drc all clean.

It recurs on every full route: r06 had 1 such via (+3V3, In2 branch back to IO1.3 again), r07 had 3 (2 GND in the
pour-free NE corner, 1 +3V3); a `route.py --nets +3V3 GND` finalize pass on r07 (r11) fixed a soft joint but left
all 3. Removing each exposes the next: the far via of a dead join chain then dangles too (r07: 3 removed, then 2
more). Helpers: `helpers/remove_copper.py` (named copper), then `helpers/prune_dangling_vias.py` (iterates
check_weird's `dangling-via` findings, removes the via plus the degree-2 chain to the next via/junction, never a
pad). After it, r07f: check_weird clean, kicad_unconnected 0, check_drc clean, vias 391 -> 386.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_weird.py wk/fa10/07_One-Air-Max/repro/r02.kicad_pcb | grep -A1 "dangling-via"
python3 -X utf8 py_router/check_weird.py wk/fa10/07_One-Air-Max/repro/r11.kicad_pcb | grep -A3 "dangling-via"   # 3, after a finalize pass
```

**Existing issues:** `--search "dangling via finalize"` -> only #162 (adjacent, not this).

---

## 6b. check_weird reports a live mid-span T-junction as a `dangling-end` "free end"; acting on it disconnects the net

**Cost:** about 15 minutes and one broken intermediate board (caught by kicad_unconnected).

**What it claimed:** on r15q, `dangling-end: net /SCL (F.Cu) at (138.400, 110.700): free end, dangling segment 1.500mm
(rooted at (138.400, 109.200))`, with `soft-joint: 0`.

**What was true:** the "free end" lands MID-SPAN on another /SCL F.Cu segment, (112.8,110.7)-(138.6,110.7) -- a
T-junction onto the middle of a segment, which check_weird's endpoint graph does not see (verifier 2 measured this;
my first reading, a 0.2 mm cap overlap with the segment's end at (138.6,110.7), was wrong). KiCad counts it as
connected (`KICAD_UNCONNECTED: 0` on r15q). Removing only the "dangling"
1.5 mm segment gave `KICAD_UNCONNECTED: 1` (`Spoor [/SCL] op F.Cu ... @(138.40,109.20) <-> Spoor [/SCL] ... @(138.60,110.70)`)
and a new 13.3 mm dangling end. What made check_weird quiet was the opposite: a 0.2 mm locked segment
(138.4,110.7)-(138.6,110.7), graded `CLEAN` by `check_join.py`. It lies on top of the existing segment (redundant
same-net copper, harmless), and only gives the T-junction an endpoint check_weird can see. The same blind spot made my first
dangling-end pruner unsafe (r15p: 2 KiCad unconnected); the shipped helper runs `--vias-only`.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_weird.py wk/fa10/07_One-Air-Max/repro/r15q.kicad_pcb | grep -A2 "dangling-end"       # calls it a free end
python3 -X utf8 py_tools/kicad_unconnected.py wk/fa10/07_One-Air-Max/repro/r15q.kicad_pcb                              # 0 -- it is connected
python3 -X utf8 py_tools/kicad_unconnected.py wk/fa10/07_One-Air-Max/repro/r15r.kicad_pcb --items                      # 1 after removing that segment
```

Minor, same episode: `check_join.py --keep-staged` writes the staged board with CRLF line endings (a whole-file diff
against its LF input) and does not stamp the join `(locked yes)`, which the skill asks for; I re-wrote the join locked.

**Existing issues:** `--search "check_weird free end overlap"` -> #1167 (OPEN, "check_orphan_stubs does not credit a
stub's own half-width against tracks") is the same blind spot in the sibling checker; #984 (OPEN, soft joints vs the
oracle leg) and #722 (CLOSED, soft-joint anchor test) are adjacent. None covers check_weird's dangling-end on a cap overlap.

---

## 7. place_seed refuses the skill's own recipe: "this board already looks PLACED" with 198 of 204 parts still piled

**Cost:** about 3 minutes (rank_rotations died 20 s in with `refused: board_placed`).

**What it claimed:** after `place_pose ... set` + `lock` of the 6 mechanical parts (skill section 4, "Place and lock the
connectors and mechanically fixed parts first ... Then zone the rest and seed"), `place_seed p01_fixed.kicad_pcb ...`
prints `this board already looks PLACED. Seeding would discard that placement` and exits 3.

**What was true:** 198 of 204 pad-bearing parts were still in the staging pile; only BAT1 (an 82 x 44 mm pad box,
half the board) and five small edge parts were on the board. `--force` works, and locked parts are kept.

**Reproduce:**
```bash
python3 -X utf8 py_placer/place_seed.py wk/fa10/07_One-Air-Max/repro/p01_fixed.kicad_pcb wk/fa10/07_One-Air-Max/repro/x.kicad_pcb --intent wk/fa10/07_One-Air-Max/intent.json   # exit 3
```

**Existing issues:** `--search "looks placed place_seed"` -> #892, #704 (CLOSED, unrelated).

---

## 8. An ESP32 module with no courtyard and no fab outline, and no CLI that creates a copper rule area

**Cost:** about 20 minutes of reading footprints, plus `helpers/add_rule_area.py`.

**What happened:** U1 (ESP32-C6-WROOM-1) draws its 25.6 mm body only on silk; placement sees the 17.4 mm pad box, so
the 6 mm antenna is invisible (`body from SILK (never gates)`). In the no-keep-out seed (item 3) U1 landed over SW1
and USB1. The README says the input's small rule areas were removed with the routing; nothing in py_router/py_tools
creates one (`route_planes` makes net pours; `route.py --keepout` only READS User-layer polygons). The parser and
router already honour `(zone ... (keepout ...))`, so I wrote one (ANT_KEEPOUT, tracks/vias/pour not allowed, all
four layers) with a helper.

**Reproduce:** `grep -c "(keepout" wk/fa10/07_One-Air-Max/repro/p03_place.kicad_pcb` (0 rule areas before the helper).

**Existing issues:** `--search "rule area keepout antenna create"` -> #487 (CLOSED, a broad feature audit).

---

## 9. 188 vias land in pads / paste openings by default, unprotected (KiCad 9 file)

**Cost:** quality, not time.

**What it claimed:** `FAB NOTE (route): 188 via(s) in a pad or paste opening [BAT1.1 F.Paste (pad), BAT1.3 F.Paste
(pad), C10.2 F.Paste (pad), ...] -- 0 stamped (capping yes) (filling yes)`. check_drc accepts them as undeclarable
on a pre-KiCad-10 file.

**What was true:** the default `--same-net-pad-clearance` resolves to -1 (via-in-pad allowed) on a reflow board whose
file format cannot declare filling/capping, so the vias ship as plain via-in-pad (solder wicking risk), including
inside the 18650 holder's solder pads. `--same-net-pad-clearance 0.1` is the lever, and it is expensive here:
same flags and `--via-cost 150`, r04 (default, via-in-pad allowed) failed 2 nets with 0 open pad pairs (174 vias in
pads), r05 (`--same-net-pad-clearance 0.1`) failed 9 nets, 4 open pad pairs, multipoint deficit 27 (board_score
blocking 15 vs 8). The r01/r04/r06 lineage ships 174-188 unprotected vias in pads.

**Existing issues:** `--search "via in pad same-net-pad-clearance default"` -> nothing covering the default.

---

## 10. route.py spends ~98% of a step after routing

**Cost:** waiting. r01: 33 min wall, `main_loop_time_s 41.6`. r03: 45 min wall, `main_loop_time_s 63.29`. The rest is
cleanup, the plane finalize (tap/join with long traces, e.g. C72.1 tapped through 98 segments to LED2's GND barrel)
and GND reconciliation sub-runs. Not a defect by itself; it decides how many experiments fit in 10 hours.

**Existing issues:** #658 (CLOSED, via/copper economy) and the known "post-route cleanup dominates wall" finding.

---

## 11. Minor

- `board_score --quiet` still prints the full `SCORE_JSON=` line (~580 KB) on stdout
  (`python3 -X utf8 py_tools/board_score.py wk/fa10/07_One-Air-Max/p01_fixed.kicad_pcb --quiet | wc -c`). No issue found.
- `place_pose --strict-legal` grades the whole board, so on a pile it refuses every pose
  (`pad_conflicts 2562, oob_pad_count 196`); a single part's pose cannot be checked strictly there. Documented, minor.

---

## Helper index (every helper written, and the gap that forced it)

All in `wk/fa10/07_One-Air-Max/helpers/`; none edits a tracked repo file.

| helper | gap | what it does |
|---|---|---|
| `add_fab_courtyards.py` | 2 | writes a courtyard = bbox(own fab body + pads) + 0.1 mm on the 196 courtyard-less footprints, so the seeder sees the bodies check_assembly grades |
| `courtyard_nudge.py` | 2 | proposes place_pose moves from check_assembly's overlap rects (superseded by the courtyards; its NTC1 proposal was wrong for a contained part) |
| `add_rule_area.py` | 8, 1b | inserts a KiCad keep-out rule area: ANT_KEEPOUT (all kinds) over U1's antenna; USB_SHIELD_NOVIA_L/R (vias only) over the filled shield rectangles |
| `dedupe_segments.py` | 5 | drops exact same-net duplicate segments (keeps the widest) |
| `remove_copper.py` | 6, 6b | removes named copper (segments by net/layer/endpoints, vias by position) |
| `prune_dangling_vias.py` | 6, 6b | iterates check_weird `dangling-via` findings and removes the via plus the dead chain to the next via/junction; its dangling-END mode broke /SCL once (gap 6b), so it ships `--vias-only` |
| `clean_and_check.sh` | 5, 6, 1b | workflow wrapper: dedupe, vias-only prune, then board_score, check_weird, check_orphan_stubs, kicad_unconnected (+ KiCad DRC json), check_drc, check_complete, check_connected on every candidate |
