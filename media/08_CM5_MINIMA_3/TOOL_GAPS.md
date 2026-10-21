# TOOL_GAPS -- gp14 board 08 (CM5_MINIMA_3)

Ranked by what each cost this run. Every command is run from the worktree root
(`~/Documents/git/krt-gp14`) with `export PATH="$HOME/.venvs/krt/bin:$PATH"`.
Inputs needed by the repro commands are copied into `wk/gp14/08_CM5_MINIMA_3/repro/`.

---

## 1. route_planes cannot replace the input's multi-layer GND zone -- it stacks a second GND zone on every layer, and check_impedance then reads the overlap as plane "splits"

- **Tool / command:** `py_router/route_planes.py <placed board> <out> --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu`
  (the board keeps the designer's ONE GND zone spanning F/In1/In2/In4/B, and a +5V zone on In3).
- **What it claimed:** for each GND layer: *"it is ONE multi-layer zone that also covers ... so it cannot be replaced for F.Cu alone ... To replace it outright, run those layers together or delete the pour in KiCad."* I had run those five layers together in that very call.
- **What was true:** the output carries 11 zones: the original GND zone (5 layer entries, priority 0) PLUS five new GND zones at priority 1 -- two overlapping same-net zones on each of F, In1, In2, In4, B. `+5V` (single-layer) was replaced in place correctly.
  Downstream, `check_impedance` keys reference copper by `(zone index, fill component)`, so wherever the two overlapping GND fills differ a trace "moves" between zones and is counted a reference-plane **split**. Measured on the first full route (`final_route_old1/f6_route.kicad_pcb`): `board_score` impedance = **28 nets** crossing (114 crossings). The same chain with the stale zone removed (helper below) and nothing else changed: 22 -> 8 -> 0 nets as I then also fixed the layer use; experiment G vs H isolates it (G kept the original zone, 25 nets all "split" crossings with 0.000 mm over void).
  The other way round, `--skip-existing-zones` keeps the designer's zone (min_thickness 0.15, islands > 5 mm2 kept) and the route step's oracle then left **GND broken 2** (an island at the NW ear, 2 unroutable forced links) -- experiments D/G.
- **Workaround:** `helpers/drop_zone.py` deletes the input's GND zone block before the pour, so route_planes creates one fresh GND zone per layer (same net, same five layers -- the design's pour map is unchanged). Recorded in `final_route/redo_commands.sh` as a commented non-repo step.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route_planes.py wk/gp14/08_CM5_MINIMA_3/repro/gap_pour_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/pour.kicad_pcb --nets GND GND GND GND GND +5V --plane-layers F.Cu In1.Cu In2.Cu In4.Cu B.Cu In3.Cu
  python3 -X utf8 -c "import sys,collections; sys.path.insert(0,'py_router'); from kicad_parser import parse_kicad_pcb; p=parse_kicad_pcb('wk/gp14/08_CM5_MINIMA_3/repro/out/pour.kicad_pcb'); print(collections.Counter((z.layer,p.nets[z.net_id].name) for z in p.zones))"
  # -> 2 GND zones on each of F/B/In1/In2/In4
  ```
- **Cost:** the largest: ~25 min and 9 routed experiments (A-I) to find why a connected, DRC-clean board scored impedance 28, plus a diagnosis helper (`helpers/plane_components.py`, because no repo tool shows which fill components check_impedance moved between).
- **Existing issues:** `gh issue list --search "route_planes multi-layer zone"` -> #1131, #662, #598, #657, #488 (none is this); `"check_impedance split zone"` -> #487 (not this). **Not covered.**

## 2. place_simple's declared-pose check refuses the four corner mounting holes and the CM5 connector pair, so EVERY seed is "illegal" and the round judges nothing

- **Tool / command:** `py_placer/place_simple.py <fixed> 'r1/s{seed}.kicad_pcb' --groups ... --intent ... --round --jobs 4` with the given intent's `fixed_poses[]` (from mechanical.json).
- **What it claimed:** `WARNING: H102's declared pose is not legal: ... pad copper 2.177mm past the outline` (H103 2.185, H104 2.155, H105 2.164), and `Module301's declared pose is not legal: courtyard overlaps Module302 by 0.00x22.80mm (14.580mm2)`; then `no legal pose for ... H102, H103, H104, H105, Module301, Module302` in all 12 seeds, `judge.json` `"judge": []`, exit 4.
- **What was true:** each hole's round 5.4 mm pad sits **0.4 mm inside** the outline's ear arc (arc radius 3.10 mm about the hole centre, measured from the Edge.Cuts arc points). `check_assembly` on the same board says these pads are *"on the outline by design, not gated ... a round pad whose bounding box, not its copper, crosses"*. Module301/Module302 are the CM5's two connectors sharing one origin by design (mechanical.json); their B.CrtYd rectangles do not overlap (x 125.86-129.56 vs 91.86-95.64) -- the "0.00 x 22.80" overlap comes from rects that include the shared NPTH holes. A part the seed cannot move (declared pose) is also counted as that seed's illegal part, so one bad declared pose disqualifies every seed.
- **Workaround:** drop those six refs from `fixed_poses[]` (in `intent_cm5.json`) and seat them at exactly their mechanical.json poses with `place_pose set ... lock` (KiCad locks are not re-checked); add `overlap_waivers` for Module301/Module302 and H102/J1 so `check_assembly --baseline <input>` does not gate them.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s0.kicad_pcb --groups wk/gp14/08_CM5_MINIMA_3/repro/gap1_groups.json --intent wk/gp14/08_CM5_MINIMA_3/repro/gap1_intent.json --seed 0
  # -> WARNING ... H102..H105 "pad copper ~2.17mm past the outline", Module301/302 courtyard overlap; no legal pose for ...; exit 4
  python3 -X utf8 py_tools/check_assembly.py wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s0.kicad_pcb --baseline wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb | grep "by design"
  ```
- **Cost:** one whole placement round (`r1_aborted/`, 12 seeds) and ~20 min of diagnosis.
- **Existing issues:** `"declared pose"` -> #1060 (courtyard waiver; closed, not this), #1152 (pad-less fixed pose; closed); `"fixed pose mounting hole outline"` -> none. **Not covered.**

## 3. route.py ships same-net duplicate segments and redundant micro-segments; check_complete then refuses the board, and no repo tool removes them

- **Tool / command:** `py_router/route.py ... --nets '*' ...` (every variant of the chain on this board).
- **What it claimed:** `WARNING: 56 stacked-copper finding(s) on the write model (same-net duplicates KiCad will not flag)` -- disclosed, shipped. JSON_SUMMARY `failed 0`.
- **What was true:** `check_complete` -> `INCOMPLETE -- orphan_stubs ... weird_copper: not clean`. `check_weird` on the first DONE-candidate: 50 stacked-copper (duplicate GND segments), 2 dangling-end (ETH TRD2 P/N half-segment tails 0.424 mm past their via anchor under J1's F.Cu pads); on later variants 1-2 `kicad-dangling` micro-segments (0.03-0.05 mm, wholly covered by other same-net track) as well. 60-87 duplicates per run.
- **Workaround:** `helpers/clean_copper.py` -- delete-only: removes exact duplicates (check_weird's own 1 um key, keeps the widest), trims named tails back to their anchor, drops named redundant micro-segments. Every result re-verified with check_weird, check_connected, check_drc, board_score and check_complete. Final board: 85 duplicates + 2 micro-segments removed, nothing added.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/check_weird.py wk/gp14/08_CM5_MINIMA_3/repro/gap_weird.kicad_pcb    # 52 weird things
  python3 -X utf8 check_complete.py wk/gp14/08_CM5_MINIMA_3/repro/gap_weird.kicad_pcb            # INCOMPLETE (weird_copper, orphan_stubs)
  ```
- **Cost:** ~15 min plus a helper and its re-verification on every candidate.
- **Existing issues:** `"stacked-copper duplicate segments"` -> **#162 OPEN** ("Same-net redundant copper ... find the producers, remove delete-only") covers it; #606 (trim pass, closed) did not stop it here; #1063 (closed) is the same "no route.py output reaches check_complete DONE" shape.

## 4. route_diff's GND return vias break the board's hole-to-hole floor, even with `--hole-to-hole-clearance 0.25` given

- **Tool / command:** `py_router/route_diff.py <board> <out> --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 --layers ... --layer-costs 1.0 -1 1.0 -1 -1 1.0 [--hole-to-hole-clearance 0.25]`
- **What it claimed:** all pairs routed, exit 0.
- **What was true:** it placed two GND return vias beside the DPHY0 clock vias at (96.80, 52.47) and (97.00, 52.16): `check_drc` VIA-DRILL-HOLE, overlap 0.038 mm against the board's `min_hole_to_hole` 0.25 -- in three separate chains (final_route_old1, expI, and with the explicit flag). With `--via-size 0.25` the vias land elsewhere and DRC is clean (that is what the final chain uses). Seed 9 shows the same defect at (96.65, 53.69)/(96.85, 53.36), overlap 0.016 mm, which is why seed 9 (204 vias) could not be shipped.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/route_diff.py wk/gp14/08_CM5_MINIMA_3/repro/gap_diffvia_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/d100.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.3 --via-drill 0.15 --hole-to-hole-clearance 0.25 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0
  python3 -X utf8 py_router/check_drc.py wk/gp14/08_CM5_MINIMA_3/repro/out/d100.kicad_pcb | grep -A5 VIA-DRILL
  ```
- **Cost:** ~8 min, and it disqualified the fewest-via seed.
- **Existing issues:** `"route_diff gnd via hole-to-hole"` -> #221 (coupled pair vias, closed), #308 (route.py, closed); none for the GND return vias. **Not covered.**

## 5. route_diff silently falls back to single-ended on a declared 100-ohm pair, and nothing in the DONE grade notices

- **Tool / command:** the 100-ohm `route_diff.py` call above with `--via-size 0.25 --via-drill 0.15 --via-cost 250` on seed 3.
- **What it claimed:** exit 0, `failed_diff_pairs: []`; `board_score` blocking 0 and `check_complete` DONE on the routed board (193 vias -- the fewest of the run).
- **What was true:** JSON_SUMMARY `single_ended_diff_pairs: ["/CM5/DPHY0_P.D0"]` -- one MIPI CSI lane routed as two uncoupled single-ended traces. The impedance component grades only reference-plane crossings, so the board read DONE. I rejected that board (and the 210-via one with the same fallback) and shipped 217 vias with every pair coupled.
- **Repro:**
  ```bash
  KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0' python3 -X utf8 py_router/route_diff.py wk/gp14/08_CM5_MINIMA_3/repro/gap_single_ended_in.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/se.kicad_pcb --nets '/CM5/ETH_PI.TRD*' '/CM5/HDMI_PI.D*' '/CM5/HDMI_PI.CK_*' '/CM5/DPHY0_P.*' --impedance 100 --track-width 0.1 --diff-pair-gap 0.13 --clearance-ceiling 0.13 --via-size 0.25 --via-drill 0.15 --layers F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu --layer-costs 1.0 -1 1.0 -1 -1 1.0 --via-cost 250 | grep -o '"single_ended_diff_pairs[^]]*\]'
  ```
- **Cost:** small (caught by reading the JSON), but it is a "tool said fine about something that was not": a DONE board with an uncoupled lane.
- **Existing issues:** `"single_ended_diff_pairs fallback"` -> #226, #221 (fallback via clearance; closed) -- not this. **Not covered.**

## 6. qfn_fanout escapes single-pad (no-connect) nets

- **Tool / command:** `py_router/qfn_fanout.py <poured> --output <out> --component Module302 --nets '*' '!GND' '!+5V' --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1` (the routing skill's prescription for CM4/CM5 connectors).
- **What it claimed:** `"requested": 70, "escaped": 70, "failed": 0`.
- **What was true:** 33 of the 70 via-in-pads are on nets with ONE pad (the unused DPHY1/HDMI1/USB3/SD module pins) -- dangling vias that only block routing. Module301 likewise "failed 5" on five single-pad SD_*/SYNC_OUT nets.
- **Workaround:** computed the multi-pad non-plane net list per module (`work/fan_Module30x.lst`, 37 and 36 nets) and passed it as `--nets`.
- **Repro:**
  ```bash
  python3 -X utf8 py_router/qfn_fanout.py wk/gp14/08_CM5_MINIMA_3/repro/gap_fanout_in.kicad_pcb --output wk/gp14/08_CM5_MINIMA_3/repro/out/fan.kicad_pcb --component Module302 --nets '*' '!GND' '!+5V' --escape-method underpad --allow-via-in-pad --via-size 0.25 --via-drill 0.15 --width 0.1
  # -> requested 70 escaped 70; 33 of the 70 new vias are on single-pad nets
  ```
- **Cost:** ~5 min.
- **Existing issues:** `"qfn_fanout single-pad unconnected nets"` -> #110, #669 (not this). **Not covered.**

## 7. Edge seating: a declared `class` is ignored, two big connectors are not recognised as connectors, and one straight 44 mm edge has "no room"

- **Tool / command:** `place_simple ... --round` with `edge_connectors[]` entries for J501 (HDMI, declared `"class": "edge_receptacle"`, edge south) and SW501 (edge east, `mating_face +x`); `check_floorplan --emit-intent --declare-classes`.
- **What it claimed:** `NOTE: J501 is declared on the south edge but is not an edge part (no part class): placed as any other part` (the seed then put the HDMI mouth facing INTO the board); `WARNING: SW501 is declared on an edge but has no seat there (no room along the east edge)`. `--declare-classes` wrote no entry at all for J1 (Kycon RJ45 MagJack) or J501 (full-size HDMI) -- only for J101/USB701/CN1/J50x/J802.
- **What was true:** the east edge is a straight Edge.Cuts line x = 132.90, y 30.04-74.64 (44.6 mm) with nothing on F.Cu near it; SW501 is 3.7 x 4.6 mm. Hand-placed at (130.5, 68.0, 0) with `place_pose` it is legal (`no_worse true`, check_assembly buildable). Cause not established; `edge_seat._seat_coord` / `seats` take the edge line and its span from `board_info.board_bounds` (the bounding box, which here is the corner ears at x 136.25), which is my unverified suspicion.
- **Workaround:** placed and locked J501, J802 and SW501 by hand (`place_pose set ... lock`), as SKILL 3.1 allows.
- **Repro:**
  ```bash
  python3 -X utf8 py_placer/place_simple.py wk/gp14/08_CM5_MINIMA_3/repro/gap1_fixed.kicad_pcb wk/gp14/08_CM5_MINIMA_3/repro/out/gap1_s7.kicad_pcb --groups wk/gp14/08_CM5_MINIMA_3/repro/gap1_groups.json --intent wk/gp14/08_CM5_MINIMA_3/repro/gap1_intent.json --seed 7 | grep -E "J501|SW501"
  ```
- **Cost:** ~10 min.
- **Existing issues:** `"edge seat part class declared"` -> #1242, #1155, #706 (closed; not this). **Not covered.**

## 8. The redo recorder drops environment knobs

- **Tool:** `py_router/redo_record.py` (via `REDO_MANIFEST`), for `route_diff.py` / `route.py` run with `KICAD_PLANE_FRAGILITY_LAYERS='GND@F.Cu=0,GND@B.Cu=0'` (the routing skill's DENSE-tier rule 1, which says such env prefixes "ride the redo-manifest form of the plan").
- **What was true:** `final_route/redo_commands.sh` records argv only; the env knob is absent (`grep -c KICAD_PLANE_FRAGILITY final_route_old1/redo_commands.sh` -> 0), so a replay routes without it. I annotated the manifest by hand.
- **Repro:** `grep -c KICAD_PLANE_FRAGILITY wk/gp14/08_CM5_MINIMA_3/final_route_old1/redo_commands.sh` (0) vs the `env_knobs` in `final_route/f6_route.json`.
- **Cost:** ~3 min.
- **Existing issues:** `"redo manifest env knobs"` -> #670 OPEN ("Promote the tuned-recipe env knobs to first-class params") is the nearest; it is about GUI plans, not the recorder. **Partly covered.**

## 9. Skill instructions that did not work as written

- **SKILL 3.1 / 3.5:** "A pose the intent declares in `fixed_poses[]` needs no lock" -- here it made every seed illegal (gap 2), and the skill has no step for a declared pose its own placer refuses.
- **SKILL 3.6 step 1:** the judging chain has no runner; each seed is a 9-command chain run by hand. I wrote `helpers/judge_chain.sh` (repo CLIs only) so the six seeds ran the SAME chain; `helpers/final_chain.sh` / `exp_chain.sh` do the same for the full-route trials.
- **plan-pcb-routing Step 3 ("CM4/CM5 ... DO benefit -- use qfn_fanout --escape-method underpad --allow-via-in-pad") + DENSE map:** the measured layer map that made the impedance grade pass was NOT the skill's DENSE price vector (GND 6.0 / rails 2.5 / highway 1.0): any routed copper on a GND/+5V reference layer fragments it and the declared-impedance grade fails (experiments B-F: 8-28 nets). Forbidding In1/In3/In4 (`--layer-costs 1.0 -1 1.0 -1 -1 1.0`) took it to 0 with no loss of completion. The skill never says that `--impedance-nets` grades reference-plane continuity, which is what decided the layer map here.
- **SKILL 1 "DONE is measured with every spec the board declares":** DONE says nothing about power widths or the buck switch node. The final board is DONE with the buck's switch node `/PCIe-M2/M2_LX` routed 36.4 mm long, 29.5 mm of it at 0.1 mm (requested 0.6), `M2_3V3` (the M.2 SSD rail) necked to 0.1 mm for 4.4 mm, and L701 31 mm from U702's LX pin (no EMC row was given, by campaign rule, so nothing held the stage together). route.py's `power_trace_ampacity` puts both nets at 0.45 A. These are reported in REPORT.md; no gating tool flagged them.

## 10. board_brief on a pile names "mechanical facts" from staging poses and points at ops that do not exist

- **Tool / command:** `py_tools/board_brief.py wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb --json ...`
- **What it claimed:** `mechanical: 12 part(s) whose position is a mechanical fact ['H101', ..., 'J101']... sit alone at their coordinate, so 'at' is assertable with place_fixed`, and "State mechanical poses with place_fixed and the rest with place_at/place_pack".
- **What was true:** the board is a pile (its own summary says `pile: true`), so J101's coordinate is a staging pose, not a fact; and there are no `place_fixed` / `place_at` / `place_pack` tools in `py_placer/` (the names only appear in board_brief's own text).
- **Repro:** `python3 -X utf8 py_tools/board_brief.py wk/gp14/08_CM5_MINIMA_3/CM5_MINIMA_3.kicad_pcb | grep -E "mechanical:|place_fixed"; ls py_placer | grep -E "place_(fixed|at|pack)"`
- **Cost:** ~2 min (read and discarded).
- **Existing issues:** `"board_brief place_fixed"` -> #711 (closed, not this). **Not covered.**

## Helpers written (each is a gap above)

| helper | why |
|---|---|
| `helpers/judge_chain.sh` | gap 9: no judging-chain runner |
| `helpers/exp_chain.sh`, `helpers/final_chain.sh` | gap 9: same, for full-route trials |
| `helpers/plane_components.py` | gap 1: no tool shows the fill components check_impedance compares |
| `helpers/imp_summary.py` | gap 1: groups check_impedance's per-crossing JSON by kind / layer / place (its text report lists nets, not where the crossings cluster) |
| `helpers/drop_zone.py` | gap 1: route_planes cannot replace the multi-layer GND zone |
| `helpers/clean_copper.py` | gap 3: no tool removes route.py's duplicate / redundant copper |
