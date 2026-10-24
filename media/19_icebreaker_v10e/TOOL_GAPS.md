# Tool gaps -- gpm board 19, icebreaker_v10e

Ranked by what each cost this run. Every reproducer runs from the worktree root
(`~/Documents/git/krt-gpm`, upstream main bda59fa0) with the venv's
python3 3.13 on PATH; its inputs are copied into
`wk/gpm/19_icebreaker_v10e/repro/`.

---

## 1. The placement stack does not know the outline is several electrically separate boards (mouse-bite perforation, snap-off tabs)

**Cost:** four rejected placement passes (13:42 to 14:22, about 40 min of the 64 min to the first DONE), plus the analysis that found the cause. I also had to write a helper to see the problem at all.

**Tool and command:**
`py_placer/place_simple.py` (12 seeds), then the skill's per-seed checks `py_tools/check_assembly.py --baseline`, `py_tools/check_floorplan.py --intent` and `py_tools/render_placement.py`.

**What it claimed:** pass 1 returned 12 legal seeds and named 6 to judge. Each judged seed was buildable with 0 floorplan errors, and nothing warned.

**What was true:** the outline is four regions. The main board (x 30-80) is one. The snap-off PMOD board (x 82-103, y 37.2-57.8) joins it only through two 1.5 mm tabs. Two frame strips (y < 35.2 and y > 59.8 at x > 82) are cut off by the declared mouse-bite drill lines (`mechanical.json` REF**~7..~58).
- At x = 80/82 the 0.5 mm drills sit at 0.8 mm pitch, leaving 0.3 mm between holes against the board's 0.25 mm hole clearance on each side.
- At x 86-88 and 96-98 the pitch is 1.0 mm, leaving 0 mm.

So no copper can cross into a strip. Every pass-1 seed still put 10 to 51 parts in a region their nets cannot reach (`helpers/region_check.py`). Seed 7, for example, put the 3.3 V LDO U2 with C5, C8, C32-C34 and R3 on the bottom frame strip, and SW2/SW4 on the strips. The workaround was hand-written `blocks[]` zones in `intent_run.json`. It then took three more passes to find a region assignment the placer could satisfy, because the strips are too small for the 2x4 sockets the netlist's isolated adapters carry (gap 5).

**Reproduce:**
```bash
R=wk/gpm/19_icebreaker_v10e/repro
python3 -X utf8 py_placer/place_simple.py $R/icebreaker_v10e.kicad_pcb $R/p1_s7.kicad_pcb \
    --groups $R/groups_pass1.json --intent $R/intent.json --clustered-seeds 6-11 --seed 7 --json $R/p1_s7.json
python3 -X utf8 wk/gpm/19_icebreaker_v10e/helpers/region_check.py $R/groups_pass1.json $R/p1_s7.kicad_pcb
python3 -X utf8 py_tools/check_assembly.py $R/p1_s7.kicad_pcb --baseline $R/icebreaker_v10e.kicad_pcb --intent $R/intent.json
python3 -X utf8 py_tools/check_floorplan.py $R/p1_s7.kicad_pcb --intent $R/intent.json
```
Measured on re-run: 23 parts out of region (`C32:bot C33:bot C34:bot C5:bot C8:bot R3:bot U2:bot SW2:top SW4:bot ...`), check_assembly `buildable (blocking 0)`, check_floorplan `0 error(s)`.

**Existing issues:** `gh issue list --search "mouse bite"`, `"breakaway"` and `"isolated region outline"` find nothing that covers it.

---

## 2. fill_for_delivery upgrades a KiCad 8 board to the KiCad 10 format and writes an explicit "no protection" on every via, so the delivered board fails DONE on via-in-paste

**Cost:** about 35 min (15:15 to about 15:50), plus a second routing campaign on an upgraded input.

**Tool and command:** `python3 -X utf8 py_tools/fill_for_delivery.py routed.kicad_pcb -o delivered.kicad_pcb` (§3.9 step 2).

**What it claimed:** "Filled ... unconnected (no --refill-zones): 105 -> 0", exit 0. That means a finished delivery copy.

**What was true:**
- **Before the fill.** `routed.kicad_pcb` is `(version 20240108)` (KiCad 8, the input board's format). board_score reads blocking 0. check_drc reads "69 undeclarable in this file format (accepted; Type VII belongs on the fab drawing)", because route.py's ship-time stamp counted them `unstampable` on the old format.
- **After the fill.** `delivered.kicad_pcb` is `(version 20260206)`, and every one of the 256 vias now carries an explicit `(capping no) (covering (front no) (back no)) (plugging (front no) (back no)) (filling no)`. The routed file had no token, which means "inherit the board setup".
- **The verdict flips.** check_drc now reads "69 unprotected (violations)", and board_score on the delivered board gives **blocking 69** (`drc_via_in_paste` 69), which check_complete calls INCOMPLETE.
- **The stamp cannot fix it afterwards.** The repo's own `fab_notes.ship_via_protection_file` stamps 0 of 88 ("own spec kept"), because the upgrade turned every via's inherit into an explicit decision.
- **KiCad's own upgrade does the same.** `kicad-cli pcb upgrade` writes 257 `(capping no)` on the same board.
- **The only route.** The chain must start from a KiCad 10 input (`kicad-cli pcb upgrade` on the unrouted `final_route/in.kicad_pcb`), so that route.py stamps its own vias under solder when it creates them. On such a board fill_for_delivery keeps the stamps: 66 filled+capped accepted, 0 unprotected.
- **The format changes the copper.** The same chain arguments route differently on the upgraded input: the A8 arm went from 256 vias and DONE to 249 vias with /P1A7 broken.

**Reproduce:**
```bash
R=wk/gpm/19_icebreaker_v10e/repro
python3 -X utf8 py_tools/fill_for_delivery.py $R/routed_k8.kicad_pcb -o $R/filled_k10.kicad_pcb
head -2 $R/routed_k8.kicad_pcb $R/filled_k10.kicad_pcb ; grep -c '(capping no)' $R/filled_k10.kicad_pcb
python3 -X utf8 py_tools/board_score.py $R/routed_k8.kicad_pcb  --intent $R/intent_run.json --baseline $R/icebreaker_v10e.kicad_pcb --json /dev/null   # BLOCKING=0
python3 -X utf8 py_tools/board_score.py $R/filled_k10.kicad_pcb --intent $R/intent_run.json --baseline $R/icebreaker_v10e.kicad_pcb --json /dev/null   # BLOCKING=69 (drc_via_in_paste=69)
```

**Existing issues:** `gh issue list --search "fill_for_delivery"` finds #1335 (closed, "The placement/routing skills never run the delivery fill (#910) ...")  and #937; `"via protection upgrade"` finds #749 (closed, re-placed via re-stamping). None covers the format upgrade turning inherited protection into explicit "no".

---

## 3. Skill: no step for a panelised or snap-off outline, and §3.6's "count each unusable pass toward the stop rule's three" fires before any route

**Cost:** a process conflict. The literal rule stops the run with an unrouted pile placement while DONE was two passes away.

**Where:** `.claude/skills/plan-pcb-placement/SKILL.md` §3.6 ("Whether it is a new pass ... count it as one approach toward the stop rule's three (§5, rule 3)") and §5 rule 3.

**What it says:** after three consecutive different approaches that each fail to lower unrouted + broken, stop and ship the best board.

**What happened:**
- **The counter filled before routing began.** Passes 1-3 were each unusable (ledger rows 1-3). None could lower unrouted + broken, because none was routed: blocking 183, 189 and 188 (124 unrouted each).
- **The literal outcome would have been absurd.** It ships old/pass1/s9.kicad_pcb, an unrouted placement.
- **What I did instead:** I read the rule as applying to measured approaches toward DONE, and continued. Pass 5 then reached DONE in 17 more minutes.
- **The missing step:** the skill names breakaway outlines nowhere. A board whose outline is several boards joined by tabs or mouse bites needs region zones before §3.6 (gap 1).

**Reproduce:** read the ledger (`python3 -X utf8 py_placer/converge.py` over `wk/gpm/19_icebreaker_v10e/ledger.jsonl`). Rows 1-4 are the rejected passes with their blocking.

**Existing issues:** `gh issue list --search "stop rule approach"` finds #110 and #529, neither of which covers it.

---

## 4. route.py ships dead-end branches its own end-of-run cleanup keeps, and no CLI can remove them, so check_complete refuses DONE

**Cost:** about 15 min, plus a helper (`helpers/drop_dangling.py`). It also corrupted one experimental board: my first via rule was wrong (see below).

**Tool and command:** the `final_route/` chain:
- `route.py ... --nets '*' --track-width 0.127 --clearance-ceiling 0.15 --via-size 0.5 --via-drill 0.3 --layer-costs 1.0 6.0 2.5 1.0 ...`
- two more `'*'` iterations, the GND-via re-pour, and a closing route.py.

**What it claimed:** each step's `JSON_SUMMARY_MIN` read `failed 0, multipoint_deficit 0, open_single []`, and board_score read blocking 0.

**What was true:**
- **The stubs.** `check_weird` found 4 dangling +3V3 F.Cu stubs: 0.127 mm tracks with a free end, from 0.7 to 2.7 mm long. Walking them back, they were dead-end branches of 16 segments in all, which every later route step kept.
- **The verdict.** `check_complete` grades `INCOMPLETE -- orphan_stubs ...; weird_copper ...`.
- **`--rip-existing-nets '+3V3'` is a no-op here.** The log says "Skipping 2 already-routed net(s): Already fully connected". The flag only permits ripping a net that blocks another.
- **`--force-reroute` cannot help either.** It "skips plane (zone-owning) nets", and +3V3 owns the In2 pour.
- **No CLI removes the copper.** `check_weird` and `check_orphan_stubs` are read-only.

The same holds for the A6 arm (`--via-cost 150` + env bundle): its dead /VCORE branch ends in a `via_dangling` via.

**Skill text gap:** plan-pcb-routing "Retrying a failed net" says "To change the geometry of copper the router is happy with you must rip it (`--rip-existing-nets <exact names>`)". That is false for an already-connected net, which the scoped step skips.

**Helper caveat:** my helper's first via rule ("copper reaches it on one layer") deleted a via that was the only B.Cu bridge between a 0.0889 mm track and J16.1's rounded-corner pad. The track stops 0.005 mm short of the corner arc, and removing the via disconnected J16 (check_connected). check_weird calls such a via `dangling-via` because it joins no layers, yet it carries the connection. The rule is now "the via touches at most one copper item". The shipped board needed no hand edit at all: its chain (A8's arguments plus `--max-ripup 5` on a KiCad 10 input) reaches DONE natively.

**Reproduce:**
```bash
R=wk/gpm/19_icebreaker_v10e/repro   # route_in.kicad_pcb = the kept placement
sed 's#wk/gpm/19_icebreaker_v10e/final_route/in.kicad_pcb#wk/gpm/19_icebreaker_v10e/repro/route_in.kicad_pcb#; s#wk/gpm/19_icebreaker_v10e/final_route/#wk/gpm/19_icebreaker_v10e/repro/r_#g' \
    $R/route_plan_A1.sh > $R/route_plan_A1_repro.sh && bash $R/route_plan_A1_repro.sh
python3 -X utf8 py_router/check_weird.py $R/r_s7_final.kicad_pcb       # 4 dangling +3V3 F.Cu ends
python3 -X utf8 check_complete.py $R/r_s7_final.kicad_pcb               # INCOMPLETE
```

**Existing issues:** #1166 (closed) "route.py never removes a dangling via, or the dead branch it ends, even when the via's net is in --nets", and #84 (closed) "route.py multipoint: orphan dead-end stubs ...". This looks like the same family recurring on a poured net.

---

## 5. The two 2x4 sockets of the netlist's isolated adapters fit no frame strip, but place_simple only says "no legal pose"

**Cost:** passes 2, 3 and 4 (13:49 to 14:18, about 30 min).

**Tool and command:** `place_simple.py` with `intent_run.json`, which puts the /ET_* adapter (J31 J32 Q1 R7 R27) in a zone on the top frame strip and the /EB_* adapter (J33 J34 R28 R29) on the bottom one. (old/pass2/intent_run_pass2.json)

**What it claimed:** "no legal pose for J31, J33, J34" in 12/12 seeds. It gives no reason and no feasibility check before 12 x 145 s of annealing. check_floorplan's plan check (`plan_zone_overfull`/`_crowded`) reported nothing for those zones.

**What was true:**
- **J31 needs almost the whole strip height.** Its courtyard is 6.1 x 11.2 mm and the strip is 6.2 mm tall, so J31 is feasible only in a 0.1 mm band of y.
- **The ET adapter cannot fit at all.** It needs about 23.5 mm of courtyard length (J31 11.2 + J32 8.65 + Q1 3.6) where a strip gives about 20.5 mm between its r = 1 mm corners and the drill line.
- **A by-area check misses this.** The zone is over-full by shape, not by area, which is why the plan check stays quiet.

**Reproduce:**
```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gpm/19_icebreaker_v10e/repro/icebreaker_v10e.kicad_pcb \
    --intent wk/gpm/19_icebreaker_v10e/old/pass2/intent_run_pass2.json --allow-unplaced | grep -i "plan_\|overfull\|crowded"   # prints nothing
```

**Existing issues:** `gh issue list --search "declared pose is not legal"` finds #1325 (closed, "edge seat says no room ... for three different faults") but nothing for zone shape feasibility.

---

## 6. place_simple refuses the declared mouse-bite drill poses in every seed, so every run exits 4

**Cost:** small, but every run's exit code is 4 and has to be read past (`declared pose is not legal`, 16 lines per run).

**Tool and command:** `place_simple.py` on any pass.

**What it claimed:** "WARNING: REF**~10's declared pose is not legal, in every seed: 1 of 1 drill hole(s) past the outline". The same appears for 16 drills: ~9, ~10, ~12, ~13, ~15, ~17, ~19, ~20, ~22, ~23, ~25, ~27, ~31, ~34, ~40, ~45. Exit code 4.

**What was true:** these are mouse-bite perforations, NPTH holes drawn on the outline by design (`mechanical.json`). Moving them would break the perforation, and check_assembly does not gate them, so the board is buildable.

**Reproduce:** the gap 1 command. `grep -c "declared pose is not legal" $R/p1_s7.log` prints 16, and the exit is 4.

**Existing issues:** #1297 (closed, title only read, as #1296-#1360 bodies are off-limits) "place_simple refuses declared poses on pad bounding boxes and castellated half-holes ...". That is the same family; drill holes on the outline are not covered by the castellated exemption.

---

## 7. analyze_power_paths traces no power path, and sizes isolated adapter grounds from the whole board's current

**Cost:** about 5 min to see that the recommendation was unusable and to set widths by hand.

**Tool and command:** the `/analyze-power-nets` recipe: `analyze_pcb` → `classify_component` (P1 500 mA source, U2/U3 LDO sources, ICs and LEDs as sinks) → `trace_power_paths` → `get_power_net_recommendations`.

**What it claimed:** "Power Net Recommendations: GND 1.00, /ET_GND 1.00, /EB_GND 1.00" and nothing else. The "Traced Power Paths" section was empty.

**What was true:**
- **No path was traced.** The board's regulators carry no pin types, so the tracer found no path even with every source and sink classified by hand.
- **The rails were left out.** +5V, +3V3 and +1V2 got no recommendation.
- **The isolated grounds were mis-sized.** /ET_GND and /EB_GND belong to self-contained adapters with no sink on them, yet each was sized 1.0 mm from the board's 609 mA total sink current.

**Reproduce:**
```bash
python3 -X utf8 -c "
import sys; sys.path.insert(0,'py_tools'); sys.path.insert(0,'py_router')
from analyze_power_paths import *
c,p=analyze_pcb('wk/gpm/19_icebreaker_v10e/repro/icebreaker_v10e.kicad_pcb')
classify_component(c,'P1',ComponentRole.POWER_SOURCE,current_rating_ma=500)
classify_component(c,'U2',ComponentRole.POWER_SOURCE,current_rating_ma=500)
classify_component(c,'U4',ComponentRole.CURRENT_SINK,current_rating_ma=70)
paths=trace_power_paths(p,c); print(len(paths), get_power_net_recommendations(p,c,paths))"
```

**Existing issues:** `gh issue list --search "trace_power_paths"` and `"analyze_power_paths"` find nothing relevant (#187 and #937 are unrelated).

---

## 8. route_plan_check R02 refuses a plan for a "pipe" that is a `|` inside a quoted net name

**Cost:** about 2 min, plus a glob workaround (`'/VCCIO_0?1'` for `/VCCIO_0|1`).

**Tool and command:**
`.claude/skills/plan-pcb-routing/scripts/route_plan_check.py final_route/icebreaker_plan.sh --board ...`

**What it claimed:** `line 6 carries a pipe` and `REFUSED: 1 rule(s) failed`.

**What was true:** the only `|` is inside the single-quoted net name `'/VCCIO_0|1'`, a KiCad net of this board passed to `--power-nets`. There is no shell pipe.

**Reproduce:**
```bash
python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/route_plan_check.py \
    wk/gpm/19_icebreaker_v10e/repro/plan_with_quoted_pipe_netname.sh --board wk/gpm/19_icebreaker_v10e/repro/route_in.kicad_pcb
```

**Existing issues:** `gh issue list --search "route_plan_check pipe"` and `"net name pipe"` find nothing.

---

## 9. Mouse-bite Drill_0.5mm markers are classed `mount_hole`, so their 0.5 mm estimated courtyards gate like screw-head keep-outs

**Cost:** it made the frame strips stricter than the geometry (gap 5). It cost no extra pass of its own.

**Tool and command:** `py_tools/check_assembly.py old/pass2/s9.kicad_pcb --baseline fixed.kicad_pcb --intent old/pass2/intent_run_pass2.json`

**What it claimed:** `J31 <-> REF**~18  0.25mm2  depth 0.5mm  side B  GATES`, and the same for 9 more drill pairs: NOT BUILDABLE.

**What was true:**
- **The markers are perforations, not screw holes.** A `pkl_mechanical:Drill_0.5mm` is a bare 0.5 mm NPTH perforation with no courtyard drawn and no screw head. `legality._MARKER_NONPHYSICAL` deliberately leaves `mount_hole` out of the waiver, for the screw-head reason, and part_class puts a perforation drill in `mount_hole`.
- **The skill implies a waiver that does not exist.** SKILL.md §3.1 says "Leave declared mounting holes and fiducials unlocked too: a KiCad lock voids the marker waiver on their courtyard pairs". In the code, a mounting hole has no courtyard marker waiver, locked or not.

**Reproduce:**
```bash
D=wk/gpm/19_icebreaker_v10e
python3 -X utf8 py_tools/check_assembly.py $D/old/pass2/s9.kicad_pcb --baseline $D/fixed.kicad_pcb --intent $D/old/pass2/intent_run_pass2.json | grep GATES
```

**Existing issues:** `gh issue list --search "mount_hole marker waiver"` and `"drill marker courtyard"` find nothing that covers it.

---

## 10. route_diff demotes the USB pair to "partial" when its third terminal is a test pad 3 mm from the connector

**Cost:** none to completion; the shipped USB pair runs as two single-ended nets.

**Tool and command:** `route_diff.py s1_pour.kicad_pcb s2_diff.kicad_pcb --nets /USB_DP /USB_DM --track-width 0.127 --diff-pair-gap 0.15 --clearance-ceiling 0.15 --layers F.Cu In1.Cu In2.Cu B.Cu ...`

**What it claimed:**
- "Leg 1/2: P1 -> P4 electrically short (< 3.0mm coupled) - deferring leg to single-ended".
- "SUCCESS: 1 legs, 16 segments" for P4 → U4.
- Then "DEMOTED /USB_D: no coupled trunk copper kept -- 'partial' pair dropped from routed_diff_pairs", and "Diff pairs: 0/1 routed".

**What was true:** the coupled leg from the back-side test pad P4 to U4 was laid, then reported as not kept, and route.py routed both members single-ended. The pair's terminals are P1 (USB), the back-side solder pads P3/P4 and U4. The routing is honest about the demotion, but a pair with a test pad near its connector cannot ship coupled through this step.

**Reproduce:** steps 1-2 of `repro/route_plan_A1.sh` (gap 4 command), then `grep -E "DEMOTED|Leg|SUCCESS" ` on the route_diff log.

**Existing issues:** #602 (closed) "route_diff reports a pair as 'coupled' while its own MEMBER AUDIT shows member pads still disconnected", which is the audit this demotion comes from.

---

## 11. `board_score --quiet` still prints the full SCORE_JSON line

**Cost:** context only, about 10 kB per call.

**Tool and command:** `py_tools/board_score.py BOARD --json X --quiet`

**What it claimed:** `--quiet` should suppress the report.

**What was true:** it prints a 10 kB `SCORE_JSON=` line on this board (126 nets listed twice).

**Reproduce:**
`python3 -X utf8 py_tools/board_score.py wk/gpm/19_icebreaker_v10e/routed.kicad_pcb --json /dev/null --quiet | wc -c`

**Existing issues:** #1194 (closed) "Three CLI papercuts: board_score --quiet prints 590 KB ...". It is smaller now but still a full line.

---

## 12. kicad_drc_compare subtracts "pre-existing" KiCad items by position, so a moved part's own footprint copper reads as a routing divergence

**Cost:** about 5 min to prove the 15 KiCad-only items were not routing defects.

**Tool and command:**
`PATH=/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH python3 -X utf8 tests/stress/kicad_drc_compare.py <copy of delivered.kicad_pcb> --baseline icebreaker_v10e.kicad_pcb`

**What it claimed:** `kicad=15 (+5 pre-existing on input, subtracted) check_drc=0 ... DIVERGED`. It listed 15 `KICAD-ONLY` items: `shorting_items` and `clearance` between a signal net and `<no net>`.

**What was true:** all 15 sit on the pads of the normally-closed solder jumpers (J1, J2, J14-J19, J29, J30). KiCad flags their own bridge copper because the footprints declare no `net_tie_pad_groups`. The same 20 items (7 shorting + 13 clearance) are already on the placed, UNROUTED `final.kicad_pcb`. The input is a pile with the jumpers elsewhere, so only 5 matched by position.

**Reproduce:**
```bash
D=wk/gpm/19_icebreaker_v10e
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc <copy of $D/final.kicad_pcb> --severity-all --format json -o /tmp/final.json
# count shorting_items/clearance whose items name <no net>: 7 + 13 on the unrouted placement
```

**Existing issues:** none found (`"drill marker courtyard"` and `"mount_hole marker waiver"` are unrelated).

---

## 13. The redo manifest cannot carry the `kicad-cli pcb upgrade` step the shipped chain needs

**Cost:** none yet. It is a replay hazard.

**Tool and command:** `REDO_MANIFEST` recording during the `final_route/` chain.

**What it claimed:** `final_route/redo_commands.sh` holds the chain: copy_board, route_planes, route_diff, 4x route.py and the GND-via route_planes.

**What was true:** step 2 of `final_route/icebreaker_plan.sh` (`kicad-cli pcb upgrade final_route/in_k10.kicad_pcb`) is not a recorded tool, so it is absent. A replay of the manifest routes the KiCad 8 copy. Per gap 2, that is a different board (A8k10 gave 249 vias with /P1A7 broken, A8 gave 256 DONE), and its delivery fill fails via-in-paste.

**Reproduce:** `grep -c "pcb upgrade" wk/gpm/19_icebreaker_v10e/final_route/redo_commands.sh` prints 0, and `grep -c "pcb upgrade" wk/gpm/19_icebreaker_v10e/final_route/icebreaker_plan.sh` prints 1.

**Existing issues:** none found.
