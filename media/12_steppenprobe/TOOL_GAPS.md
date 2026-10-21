# TOOL_GAPS -- gp14 board 12 (steppenprobe)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`, venv python 3.13); every input it needs
is in `wk/gp14/12_steppenprobe/repro/`.

---

## 1. Placement writer never turns a pad that carries the KiCad-6 `locked` token -- and the given pile already carries that damage

**Tool:** `py_placer/placement/writer.py::_rotate_pad_angles` (used by
`place_simple.py`, `place_pose.py`, and evidently by whatever wrote the pile).

**What it claimed:** `place_simple --round` reported all 12 round-1 seeds legal
(exit 0, `illegal: []`); `check_assembly` read them buildable; the judge picked
r1/s8 with a clean fast route.

**What was true:** every pad on this board is written
`(pad "1" smd roundrect locked (at x y a) ...)`. The writer's regex is
`\(pad\s+"[^"]*"\s+\S+\s+\S+\s*\n?\s*\(at ...` -- it allows exactly two
tokens (type, shape) before `(at`, so a pad with `locked` never matches and its
ABSOLUTE angle is left behind whenever its footprint turns.
- The given pile has every footprint at angle 0 but its pads at their old
  absolute angles: 38 of 84 parts have pads turned 90 deg against their own
  bodies. pcbnew agrees: U1's pad 1 (west row) reads bbox 0.30 x 1.55 mm at
  footprint angle 0 / pad angle 270; `check_pads` reports 126 overlapping
  different-net pad pairs on U1 in the pile.
- Round 1 placed on that geometry: in every seed with U1 at 0 deg (s9, s11,
  s1) `qfn_fanout` escaped 0/31 pads ("dropped 31 stub(s) grazing a foreign
  pad") and the judge route left 35-46 nets open; with U1 at 90/270 it escaped
  31/31. The judge was ranking seeds by U1's angle, not by placement quality.
  The "winning" r1/s8 had 37 parts with turned pads (SC-70s, SOT-23s, Y1, ...).
- Cost: round 1 voided (12 placements + 6 judge routes), ~15 min of
  diagnosis, and a helper.

**Workaround:** `helpers/normalize_pile.py` -- per footprint, set the footprint
angle to its pads' common angle (pad-local angle 0 again = library geometry)
and drop the per-pad `locked` token so the writer's regex matches; after it,
`check_pads` is clean on the pile and all 12 round-2 seeds have 0 turned-pad
parts, and `place_pose rotate U1 90` writes pad angle 90.

**Reproduce:**
```bash
python3 -X utf8 py_placer/place_pose.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb \
    wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb rotate U4 90 --force
python3 -c "t=open('wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb').read(); i=t.find('(fp_text reference \"U4\"'); s=t.rfind('(footprint ',0,i); b=t[s:s+60000]; import re; print(re.search(r'\(at [^)]*\)',b).group(0), re.search(r'\(pad \"1\"[^\n]*',b).group(0)[:60])"
#   -> (at 125.690300 123.359000 90) (pad "1" smd rect locked (at -2.7 -1.905) ...   footprint turned, pad angle still 0
python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/pile_rot.kicad_pcb --component U4   # overlapping pads
python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb --component U1       # 126 overlaps in the GIVEN pile
```

**Issues:** `gh issue list --search "pad angle locked rotate"`, `"_rotate_pad_angles"`,
`"pad locked writer"`, `"pile pad rotation"`: none covers it. Nearest:
#1163 (make_unplaced keeps text-to-part angles; closed), #1214 (writer leaves
a footprint's own keep-out zone behind; closed).

---

## 2. A declared net-class width is graded nowhere unless a widths file is hand-written, and no reader names the class's members

**Tools:** `py_router/list_nets.py --design-rules`, `py_tools/board_context.py`,
`py_tools/board_score.py` / `check_complete.py`, `route.py` (`--track-width`).

**What it claimed:** `list_nets --design-rules` printed
`[Power] clearance=0.15 track_width=0.3 ...` with no member nets (an
unassigned class reads exactly the same); board_context never mentions it;
`board_score` and `check_complete` said `UNGRADED (not scored, not passed):
... net_widths` and DONE.

**What was true:** the input is a KiCad-6 project whose `Power` class lists
its members inside `net_settings.classes[].nets` (+1V8, +3V3, +5V, /VPHY,
/VPLL, GND, VBUS, Vdrive). The routing skill's chain passes an explicit
`--track-width 0.15`, which overrides every class width, so the shipped v4
board had 6 of the 8 nets under 0.3 mm (about 124 mm of copper; +1V8 and
Vdrive at 0.25 everywhere, /VPHY and /VPLL at 0.15). Only the independent
verifier read the class and FAILED the board. Cost: a verifier call, the
re-route rounds P1b-P5b, and the run ends without DONE (gap 3). (My own miss
too: I looked for netclass patterns/assignments, the KiCad 7+ fields.)

**Reproduce:**
```bash
python3 -X utf8 py_router/list_nets.py wk/gp14/12_steppenprobe/repro/pile.kicad_pcb --design-rules | grep Power   # no members
python3 -c "import json; print([(c['name'],c.get('nets')) for c in json.load(open('wk/gp14/12_steppenprobe/repro/pile.kicad_pro'))['net_settings']['classes']])"
python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/final.kicad_pcb --quiet   # net_widths UNGRADED
python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/final.kicad_pcb --net-min-widths wk/gp14/12_steppenprobe/widths.json --quiet   # net_widths 6
```

**Issues:** `"netclass track width net_widths"`: none; `"Power netclass width"`,
`"net-min-widths netclass"`: #1237 (OPEN, design for an audit judging a board
against a spec) is the nearest; #530 (closed) is clearance-only.

---

## 3. route.py necks power nets to 0.15 mm at every 0.5 mm-pitch pin, and no flag stops it without breaking the net

**Tool:** `py_router/route.py` (power widths, pad-entry neck-down, `#72` tap neck-down).

**What it claimed:** routing all 8 Power-class nets at `--power-nets-widths 0.3`
(variant P1b), `Design rules [...]` reported the narrowed sites, and the run
finished with 0 failed nets.

**What was true:** every remaining under-width segment is a 0.15 mm neck-down of
up to ~2.5 mm at U1's LQFP pins (VCORE 12/37/49, VPHY 4, VPLL 9, GND 1/5/13/15/25/35/47/51,
one +3V3), although a straight 0.3 mm exit along a 0.3 mm pad clears the
neighbouring pads by 0.2 mm (> 0.15). `--escalation off` (P2b) still necks
("a wide power net may still neck for at most 2 mm of path at a pad entry")
and adds an undersized item; adding `--no-power-tap-neckdown` (P3b) breaks +1V8;
`--grid-step 0.05` (P4b: still 5 nets, 27 mm under, 116 vias) and
`--neckdown-length 0.5` (P5b: still 5 nets, 20 mm under) do not remove it. So
`--net-min-widths` at the declared 0.3 cannot reach 0 on this board with the
repo's tools. The independent verifier (verdict_2.txt) measured the shipped board:
29.01 mm under 0.3 on 59 segments, all at U1; 20.59 mm of it would widen to
0.3 in place at 0.15 clearance, and a 0.3 track fits every U1 pad (0.192-0.204 mm
to the neighbours) -- the necks are the router's choice, not geometry. No repo
tool widens existing copper, and the routing skill forbids hand-placed copper. Cost: five extra chains and the run ends NOT DONE (blocking 5 = net_widths 5).

**Reproduce:**
```bash
bash wk/gp14/12_steppenprobe/expP1b/plan.sh   # writes into expP1b/ (fresh copy first: copy_board s0_fix.kicad_pcb expP1b/placed.kicad_pcb)
python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/expP1b/step4b.kicad_pcb --net-min-widths wk/gp14/12_steppenprobe/widths.json --quiet
```

**Issues:** `"power width neck pad fine pitch"`, `"neckdown power net width"`,
`"power-tap-neckdown"`: #72 (closed) introduced the tap neck-down; #593 (OPEN,
width-aware corridor reservation for power nets) is related; none covers
necking at a pin a full-width track can reach.

---

## 4. No placement grade sees a footprint whose OWN pads overlap each other

**Tools:** `place_simple.py` legality, `py_tools/check_assembly.py`.

**What it claimed:** r1/s9 legal (place_simple) and `VERDICT: buildable
(blocking 0)` (check_assembly with `--baseline` and `--intent`).

**What was true:** U1 in r1/s9 has 129+ overlapping different-net pad pairs
(its rows are turned, gap 1), confirmed by pcbnew's pad bboxes and by
`py_router/check_pads.py` ("Likely a pad-rotation modelling error"). Only
`check_pads` -- which no step of either skill runs -- and `qfn_fanout`'s
warning ("U1 has 158 overlapping different-net pad pair(s)") noticed. Cost:
it let gap 1 run a full placement round and judge before anything refused.

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_assembly.py wk/gp14/12_steppenprobe/repro/r1_s9.kicad_pcb   # buildable
python3 -X utf8 py_router/check_pads.py wk/gp14/12_steppenprobe/repro/r1_s9.kicad_pcb       # 129+ overlapping pad pairs on U1
```

**Issues:** searched `"check_assembly pad overlap same footprint"`,
`"check_pads overlapping pads check_assembly"`: none (nearest #1106/#1204,
both about other parts).

---

## 5. Following plan-pcb-routing as written ships copper below the board's own declared minimums, and the writeback hides it

**Tools / skill:** `route.py`, `route_diff.py`, `qfn_fanout.py` defaults
(`--escalation fab`, `--fab-tier auto`); `.claude/skills/plan-pcb-routing/SKILL.md`
(its chain never passes `--escalation` / `--fab-tier`).

**What it claimed:** the v1 chain (`final_route_old1/plan_v1.sh`, the skill's
chain with the board's sizes 0.15/0.15, via 0.6/0.3) finished with
`failed: 0`; `board_score` without spec flags: blocking 0; `check_drc`: clean.

**What was true:** the board's Board Setup declares min_via_diameter 0.6,
min_through_hole 0.3, min_track_width 0.15 and a 0.15 Default clearance. The
route escalated 11 plane taps to the ADVANCED fab tier (0.3/0.15 mm vias:
"plane tap U1.12: escalated standard->advanced"), descended clearance to 0.127
and one track to 0.1496, then wrote the project down to match
(min_via_diameter 0.6 -> 0.45, min_through_hole 0.3 -> 0.2, Default clearance
0.15 -> 0.127), so every later checker graded the sub-floor copper clean.
`board_score --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3`
(the spec flags plan-pcb-placement section 1 requires) showed `undersized=3`. It is
disclosed (`Design rules [...]` line), but the routing recipe gives no step to
hold the board's floors; `--escalation board --fab-tier standard` did (v2+:
0 undersized, min clearance used 0.15). Cost: one full re-route plus the
+1V8 corridor fight that the honest floors then exposed (v2, v3).

**Reproduce:**
```bash
python3 -X utf8 py_router/route.py wk/gp14/12_steppenprobe/repro/v1_step2a.kicad_pcb wk/gp14/12_steppenprobe/repro/v1_out.kicad_pcb \
    --nets '*' --power-nets GND +3V3 +5V VBUS +1V8 Vdrive --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.25 \
    --track-width 0.15 --clearance-ceiling 0.15 --via-size 0.6 --via-drill 0.3 --layer-costs 1.0 1.5
#  -> "Design rules [--escalation fab, --fab-tier auto]: ... below the requested size", WARNING plane tap ... escalated standard->advanced
python3 -X utf8 py_tools/board_score.py wk/gp14/12_steppenprobe/repro/v1_out.kicad_pcb --min-track-width 0.15 --min-via-diameter 0.6 --min-via-drill 0.3
```

**Issues:** `"escalation fab below board minimums"`, `"fab-tier auto via
escalation plane tap"`: #857 (closed, `--fab-tier standard` escalated silently),
#1262 (open, `--escalation board` clearance misreport), #1160 (closed). None
says the routing skill's chain should hold declared floors.

---

## 6. qfn_fanout lays a stub across a same-net cap pad and past it; nothing downstream removes the tail, and check_complete refuses DONE

**Tool:** `py_router/qfn_fanout.py` (stub escape), then `route.py` cleanup.

**What it claimed:** fanout `escaped 31/31`, `drc_grazes total 0`; `route.py`
"Dead-end sweep / Dangle trim" ran; `check_connected`: all connected.

**What was true:** U1 pin 64's +1V8 stub runs from (118.054, 77.993) to
(116.300, 79.800): across C11's +1V8 pad 1 (117.01, 79.92, 0.875 x 0.95) and
0.27 mm past its edge, ending between C11's two pads. After routing it stayed as
`check_weird` dangling-end (1.203 mm) + kicad-dangling + `check_orphan_stubs`
orphan, so `check_complete` said INCOMPLETE. Two cleanup laps did not remove it;
`--rip-existing-nets +1V8` alone is a no-op on a connected net
(`--force-reroute` needed). Final fix: keep +1V8 out of the U1 fanout.
Cost: two laps and a chain variant.

**Reproduce:**
```bash
python3 -X utf8 py_router/qfn_fanout.py wk/gp14/12_steppenprobe/repro/v3_step1.kicad_pcb --component U1 \
    --nets '*' '!GND' '!+3V3' --output wk/gp14/12_steppenprobe/repro/v3_step1b_out.kicad_pcb \
    --clearance 0.15 --track-width 0.15 --escalation board --fab-tier standard
# +1V8 segment (118.0538, 77.9925) -> (116.3, 79.8); C11 pad 1 spans x 116.57..117.45
```

**Issues:** `"dangling tail fanout stub"`, `"qfn_fanout stub through pad"`:
nearest #601 / #84 (closed, orphan stubs from route.py), not the fanout.

---

## 7. route.py writes stacked same-net duplicate segments it has already detected

**Tool:** `py_router/route.py` (v3 chain); `check_weird` / `check_complete`.

**What it claimed:** "WARNING: 18 stacked-copper finding(s) on the write model
(same-net duplicates KiCad will not flag)" -- and wrote them.

**What was true:** v3's board carried 23 exact same-net duplicate segments
(GND / +3V3 on F.Cu); `check_weird` stacked-copper 8 groups;
`check_complete`: "weird_copper: not clean", so no DONE. No repo tool removes
them. Workaround: `helpers/dedupe_segments.py` (drops a segment only when
another of the same net/layer has the same endpoints; connectivity and DRC
re-checked clean). The shipped v4 chain happened to write none.

**Reproduce:**
```bash
python3 -X utf8 py_router/check_weird.py wk/gp14/12_steppenprobe/repro/v3_step4b.kicad_pcb   # stacked-copper: 8
```
(the producing step is `final_route_old3/redo_commands.sh`, route.py from step2ff.)

**Issues:** `"stacked duplicate segments"`: #162 (OPEN, same-net redundant
copper -- find the producers, remove delete-only), #606 (closed, trim pass),
#1063 (closed).

---

## 8. Placement rounds stop at a clean fast route even though every judged seed fails the verifier's floorplan gate (skill gap)

**Skill:** `.claude/skills/plan-pcb-placement/SKILL.md` section 3.6 / verifier.md.

`place_simple` grades decap limits at error, yet all 6 judged r2 seeds broke
1-4 of them (`check_floorplan --intent`: s0 C12 3.00 mm and C6 3.79 mm from U1,
limit 2.92; s7 four caps). The stop rule ends the rounds at the first clean fast
route, and the verifier requires 0 floorplan errors; the skill gives no step for
that gap. Fixed by hand with `place_pose set` on C12/C6 (in CHOSEN.json
`after`). Cost: small (two moves), but a reader following the text would
ship a verifier FAIL.

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/12_steppenprobe/repro/r2_s0.kicad_pcb --intent wk/gp14/12_steppenprobe/intent.json
```

**Issues:** `"decap limit broken place_simple"`: none.

---

## 9. qfn_fanout defaults its clearance to the fab floor and lowers the project's classes; `--clearance-ceiling` does not stop it

**Tool:** `py_router/qfn_fanout.py`.

Without `--clearance`, qfn_fanout used 0.1 (not the board's 0.15 Default class,
which route.py would use) and wrote `net_class[Default].clearance: 0.15 -> 0.1`
and `min_hole_clearance 0.25 -> 0.1`; the chain spelling the routing skill asks
for, `--clearance-ceiling 0.15`, printed "no cap applied -- --clearance 0.1 is
already at or below it". Cost: one judge run redone with `--clearance 0.15`.

**Reproduce:**
```bash
python3 -X utf8 py_router/qfn_fanout.py wk/gp14/12_steppenprobe/repro/r2_s0.kicad_pcb --component U1 \
    --nets '*' '!GND' '!+3V3' --output wk/gp14/12_steppenprobe/repro/r2_s0_fan_default.kicad_pcb \
    --clearance-ceiling 0.15 --track-width 0.15
```

**Issues:** `"qfn_fanout default clearance"`: #1195 (closed; qfn_fanout lowers
via/hole floors on a run placing no via) is the same family.

---

## 10. A bare pour lowers the project's copper-to-hole floor

**Tool:** `py_router/route_planes.py` (Step 1 bare pour, no vias, no tracks).

Writes `rules.min_hole_clearance: 0.25 -> 0.15` into the output project and
prints "FAB FLOOR RELAXED"; every later step carries it. Disclosed, harmless
here (0.6/0.3 vias at 0.15 clearance keep 0.30 mm hole-to-copper), but it is a
floor change on a step that laid nothing near a hole. Cost: report noise only.

**Reproduce:**
```bash
python3 -X utf8 py_router/route_planes.py wk/gp14/12_steppenprobe/repro/r2_s0.kicad_pcb wk/gp14/12_steppenprobe/repro/r2_s0_pour.kicad_pcb \
    --nets GND +3V3 --plane-layers B.Cu F.Cu
```

**Issues:** #1195 (closed, same pattern on qfn_fanout).

---

## 11. manifest_to_plan drops the cap pass: "cannot load intent ... No such file" for a path that exists

**Tool:** `tests/stress/manifest_to_plan.py` (routing skill Step 9).

`manifest_to_plan.py wk/gp14/12_steppenprobe/steppenprobe_plan.sh -o ...`:
"command 4: place_fanout_clearance.py refuses its arguments after parsing:
cannot load intent wk/gp14/12_steppenprobe/intent.json: [Errno 2] No such file",
"6 step(s) written ... (1 command(s) skipped)". The file exists relative to the
repo root (the plan's own first line is `cd` there). The GUI plan therefore lacks
Step 1c. Cost: small.

**Reproduce:**
```bash
python3 -X utf8 tests/stress/manifest_to_plan.py wk/gp14/12_steppenprobe/steppenprobe_plan.sh -o wk/gp14/12_steppenprobe/repro/plan.json
```

**Issues:** `"manifest_to_plan place_fanout_clearance"`: none (#1067 is a
different place_fanout_clearance defect).

---

## 12. Environment: no PDF reader, so the connector drawing could not be read

`WebFetch` saved the GCT USB4085 datasheet PDF, but the host has no
`pdftoppm` and the venv no `pypdf`/`fitz`, so section 3.4's "how far the receptacle
reaches past the edge" could not be taken from the drawing; J1 was left at the
intent's flush seat. Not a repo tool. Cost: none measured.
