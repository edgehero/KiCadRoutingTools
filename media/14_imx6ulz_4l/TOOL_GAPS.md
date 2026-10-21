# TOOL_GAPS — gp14 board 14 (imx6ulz_4l)

Ranked by what each cost this run. Every command runs from the worktree root
(`~/Documents/git/krt-gp14`) with `export PATH="$HOME/.venvs/krt/bin:$PATH"`;
`W=wk/gp14/14_imx6ulz_4l`, `R=$W/repro`. Repro inputs were copied with
`py_router/copy_board.py` (board + `.kicad_pro` + `.kicad_dru` + brief).

---

## 1. Nothing in the chain grades or honours the board's `.kicad_dru` LENGTH window; the bus step and the default chain both break it  (cost: ~1 h 30 min, most of the run)

**Tools:** `route.py`, `route_diff.py`, `awx/route_bus.py`, `board_score.py --length-groups`, `check_drc.py`, the plan-pcb-routing skill.

**What they claim.** The board's `.kicad_dru` declares
`(rule "byte0 delay matching" (condition "A.NetClass == 'DRAM_LDQ'") (constraint length (min 11.5mm) (opt 13mm) (max 14.5mm)))`
(DRAM_LDQ = `/DRAM/DRAM_DQ0..7`). Every routing step prints
`.kicad_dru rule 'byte0 delay matching': parsed, but length has no consumer in this tool yet`
and goes on; `check_drc` has no length check; `board_score --length-groups` grades only a
SPREAD (`tolerance_mm`), not a min/max window; `route_bus` (Step 1a, "use it on every such bus")
plans the DDR bus with no length term. So every repo grader reads the board as clean while KiCad's
own DRC reports `length_out_of_range`.

**What is true (measured with KiCad's DRC, `helpers/kicad_length_check.py`):**

| chain | lane-0 nets outside 11.5–14.5 mm (KiCad) |
|---|---|
| default chain (dogbone fanouts, `route.py '*'` + `--length-match-group DQ0-7 --length-match-tolerance 1.0`), `exp_d1/r2` | 8 of 8 (9.2–20.9 mm) |
| `route_bus` joint on r1/s2 (`exp_bus/rest1`) | 3 (DQ2 10.2, DQ5 17.3, DQ7 21.3) |
| `route_bus` joint on the kept placement (`final_route_old2/s1a_bus`) | 4 (DQ2 10.2, DQ4 18.0, DQ5 21.3, DQ7 21.0) |
| `route_bus` escape mode (`exp_bus2`) | 6 (DQ5 52.6 mm) |
| shipped chain (lane 0 routed FIRST, before any fanout of its balls, in three protected length-matched steps) | 0 (12.5–14.1 mm) |

`--length-match-group` only extends nets toward the group's LONGEST, so it cannot repair a
window whose max is broken; it also skips already-connected nets ("Skipping 8 already-routed
net(s)"), so the bus's lanes cannot be matched afterwards, and `route_bus` locks them.
I wrote `helpers/kicad_length_check.py` (kicad-cli DRC on a temp copy, lists length items)
because no repo instrument reports the window.

**Repro:**
```bash
python3 -X utf8 py_tools/board_score.py $R/viainpad_len.kicad_pcb --length-groups $R/length_groups.json --quiet   # length: spread only
python3 -X utf8 py_router/check_drc.py $R/viainpad_len.kicad_pcb --clearance-margin 0.1                        # no length check at all
python3 -X utf8 $W/helpers/kicad_length_check.py $R/viainpad_len.kicad_pcb                                   # KiCad: 8 length_out_of_range
```
**Existing issues:** `gh issue list --search "length window kicad_dru min max"` → none;
`"length has no consumer"` → none on point (#1246/#1248 are about spread measurement, closed).

---

## 2. `route_diff` reports a pair "coupled" / "matched" that the verifier measures as uncoupled and skewed  (cost: ~40 min: the verifier FAIL and three fix attempts)

**Tool:** `py_router/route_diff.py` (pair_reports, `--diff-pair-intra-match`).

**Claim (shipped chain, `final_route/s2a_diff.log`):** `"routed_diff_pairs": ["/DRAM/DRAM_CLK0", "/DRAM/DRAM_DQS0"]`,
DQS0 `"outcome": "coupled"` (with a "Hybrid escape ... terminals NOT coupled" note). With
`--diff-pair-intra-match` (exp_p2): CLK0 `"status": "matched", "delta_mm": 0.0003`.

**True (verifier, and `helpers/pair_check.py`):** DQS0 P runs In2.Cu 19.95 mm + F 1.13, N runs
B.Cu 15.92 + F 0.57 — only 0.57 of 21.08 mm coupled, skew 4.60 mm pad to pad; in exp_p2 it got worse
(5.29 mm). CLK0 "matched" measures 2.97 mm U2->U1 skew (16.80 vs 19.77 mm). The coupled-middle and
the matching cover only route_diff's own middle span; the uncoupled terminal legs (35.8 mm of them
on DQS0, "best plan still ships 35.8mm uncoupled leg copper") are not in either number. No repo
instrument grades a routed pair (board_score / check_complete have no diff-pair component), so
nothing in the stack sees it; I wrote `helpers/pair_check.py` (coupled length, layers, skew per pair).

**Repro:** `grep -o '"pair": "/DRAM/DRAM_DQS0"[^}]*}' $W/repro/pairs_route_diff.log`, then
`python3 -X utf8 $W/helpers/pair_check.py $W/repro/pairs_final.kicad_pcb /DRAM/DRAM_DQS0 /DRAM/DRAM_DQS1 /DRAM/DRAM_CLK0`
(DQS0 coupled 0.00/21.08 mm, skew 4.60).
**Existing issues:** `gh issue list --search "route_diff hybrid escape coupled skew"` → none on point
(#677 open is about pairs walling in later nets).

---

## 3. `route.py`'s end-of-run strict collapse (#1063) claims removals it never writes  (cost: ~25 min + a helper)

**Tool:** `py_router/route.py` (`_late_strict_collapse1063`), and through it `check_complete.py`.

**Claim:** `Strict collapse (#1063, end of run): removed 291 redundant segment(s) on 100 net(s)`.

**True:** nothing is removed. On a non-KiCad-10 file (`(version 20240108)`) the CLI path calls
`remove_segments_from_content(content, removed, net_id_to_name=None)`; this chain's boards are
mixed-dialect (2785 segments carry `(net "/name")`, 440 carry `(net 13)`), so every name-ref
target matches 0 blocks and the returned count is discarded. Measured on the repro: segments
3014 in → 3014 out, `check_weird` removable-segment 144 → 144; on the shipped chain every one of
the 4 route passes "removed" ~291 again. The leftover copper then fails `check_complete`
(`weird_copper: not clean`). Calling the same function with the name map matches 293/293.

Workaround: `helpers/strict_collapse.py` runs route.py's OWN `collapse_strict_redundant` on the
parsed board and strips what it removed WITH the name map (291 segments), then a hygiene pass for
the classes `check_complete` gates on and nothing removes on zoned nets (63 exact same-net
duplicates on +3V3/GND, KiCad-dangling slivers, `redundant-cycle` loop edges, 2 dangling GND vias).
A first version that removed check_weird's whole removable SET at once disconnected +5V at U6 —
the set is graded per segment, not jointly.

**Repro:**
```bash
L="F.Cu In1.Cu In2.Cu B.Cu"
python3 -X utf8 py_router/check_weird.py $R/collapse_noop.kicad_pcb | grep removable-segment        # 144
python3 -X utf8 py_router/route.py $R/collapse_noop.kicad_pcb $R/out_cn.kicad_pcb --nets '*' --track-width 0.1 \
  --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.25 --layers $L --layer-costs 1.0 6.0 1.5 1.0 \
  --no-bga-zones --max-ripup 5 --via-cost 250 --power-nets GND +3V3 --power-nets-widths 0.2 0.2 | grep "Strict collapse"
python3 -X utf8 py_router/check_weird.py $R/out_cn.kicad_pcb | grep removable-segment                    # still 144
```
**Existing issues:** `"1063 strict collapse"` → #1063 (closed; the collapse itself), `"late_strict_collapse"` → none;
#162 (open) covers same-net stacked duplicates in general.

---

## 4. `board_score`'s length component cannot see a via-in-pad join, so a connected group goes UNGRADED  (cost: ~20 min + a helper)

**Tool:** `py_tools/board_score.py --length-groups` (via `net_queries.pin_pair_path_length` / `net_pads_joined`).

**Claim:** `DRAM_LDQ: 4 of 8 member(s) have pads not joined by track copper (unrouted, stub-only, broken or plane-only)` → length UNGRADED.

**True:** all 8 nets are connected (`check_connected`: ALL NETS FULLY CONNECTED; KiCad measures
each length). The track graph links a pad disc and a via disc only through a TRACK node inside
both; a via in the pad whose tracks leave on another layer is never linked to the pad. Through
check_complete this turns a declared spec into "UNEXAMINED", which the verifier brief rules a FAIL.

Workaround: `helpers/vip_joins.py` stages a 0.05 mm track from the pad centre toward the via on
the pad's layer with `py_tools/check_join.py` (CLEAN each time) — electrically nothing new — after
which all 8 measure (12.50–14.11 mm, spread 1.61). These joins must go on LAST: route.py's own
strict-collapse model (applied by helper 2) removes them as in-pad wiggles.

**Repro:**
```bash
python3 -X utf8 py_tools/board_score.py $R/viainpad_len.kicad_pcb --length-groups $R/length_groups.json --json $R/out_l.json --quiet
python3 -c "import json;print(json.load(open('$R/out_l.json'))['components']['length'])"   # DQ3, DQ7 'unjoined'
python3 -X utf8 py_router/check_connected.py $R/viainpad_len.kicad_pcb --nets /DRAM/DRAM_DQ3 /DRAM/DRAM_DQ7  # connected
```
**Existing issues:** `"net_match_length via in pad"` / `"pin_pair_path_length"` → none on point (#1246, #1248 closed, different).

---

## 5. `bga_fanout --check-for-previous` lays escapes over existing foreign-net tracks  (cost: ~20 min, one shipped-candidate short)

**Tool:** `py_router/bga_fanout.py`.

**Claim:** `"requested": 41, "escaped": 41, "failed": 0`.

**True:** with lane 0 already routed through U2's ball field, the U2 fanout added 34 new
`check_drc` violations (64 → 98), 20 of them `/DRAM/DRAM_DQ5 <-> VMEM`; in exp_l6 one survived the
whole chain as a KiCad `shorting_items` (DQS0_N fanout via on DQ5's track at (69.20, 109.00)) plus a
`tracks_crossing`. Its exit planning only treats earlier FANOUT copper as occupied
(`find_existing_fanouts`), not routed tracks. The shipped chain avoids it by fanning out U2's VMEM
balls before lane 0 and the rest after, where nothing crossed.

**Repro:**
```bash
L="F.Cu In1.Cu In2.Cu B.Cu"
python3 -X utf8 py_router/check_drc.py $R/fanout_over_tracks.kicad_pcb --clearance-margin 0.1 | grep FOUND   # 64
python3 -X utf8 py_router/bga_fanout.py $R/fanout_over_tracks.kicad_pcb --component U2 --nets '*' '!GND' '!+3V3' \
  --check-for-previous --layers $L --layer-costs 1.0 -1 1.5 1.0 --escape-method dogbone --via-size 0.45 --via-drill 0.25 \
  --track-width 0.1 --clearance 0.1 --diff-pairs '/DRAM/DRAM_DQS0_*' '/DRAM/DRAM_DQS1_*' '/DRAM/DRAM_CLK0_*' \
  --diff-pair-gap 0.1 --output $R/out_fo.kicad_pcb | grep JSON_SUMMARY            # failed 0
python3 -X utf8 py_router/check_drc.py $R/out_fo.kicad_pcb --clearance-margin 0.1 | grep FOUND                    # 98
```
**Existing issues:** `"bga_fanout check-for-previous existing copper"` → #1189 (closed: under-pad exit cell vs foreign via; related, not this).

---

## 6. place_simple leaves a one-cap rail's pin limit broken in 33 of 36 seeds, and the judge never sees it  (cost: ~15 min, three hand moves)

**Tools:** `py_placer/place_simple.py` (decap-limit term), `py_tools/quick_score.py`, the skill's judge.

**Claim:** each seed's report `"decap_broken": 1, "decap_limits": 5.0`; `judge.json` names it legal;
its fast route scores blocking 8 (quick_score has no floorplan term).

**True:** the broken limit is `decap_pin_distance: U1 pin P12 (/SOC Power/VDD_SNVS_IN) is 22.34mm from
C20 ... (limit 8.46mm)` — 13.9 mm past it, priced at 5.0. `set_limits` caps a pin limit wider than
the 5 mm tether radius at "the radius past the limit" on the reasoning "any cap on the rail meets it";
VDD_SNVS_IN has exactly ONE cap (C20, the MCP1700's output cap), so nothing else can. The first full
route then failed DONE on floorplan 1. Fixed after placement with three `place_pose set` moves
(U8, C19, C20 to U1's west face; CHOSEN.json `after`). Note also: check_groups did not warn —
C20 sits in the power group with U8, an IC on the same rail.

**Repro:**
```bash
python3 -X utf8 py_placer/place_simple.py $R/r1_fixed.kicad_pcb $R/out_s2.kicad_pcb --groups $R/r1_groups.json \
  --intent $R/r1_intent.json --seed 2 --json $R/out_s2.json | tail -1          # decap_broken 1, decap_limits 5.0
python3 -X utf8 py_tools/check_floorplan.py $R/out_s2.kicad_pcb --intent $R/r1_intent.json | grep ERROR    # P12 22.34 mm from C20
```
**Existing issues:** `"decap pin distance radius"` → #1249 (closed: a 3-pad regulator can never own a cap — the root of C20 being graded against U1), #1150 (closed).

---

## 7. B-face parts pile under an F-face BGA; `apart` cannot stop it  (cost: ~15 min, one placement round)

**Tool:** `place_simple` (halo / apart terms).

**Claim:** r1 seeds legal and buildable; r2 with `straps` `apart: ["core"]` still legal.

**True:** the halo only prices parts on the BGA's own face, so B-side 0402 strap resistors (44 of
them, wired only to U1) sit under U1's ball field where its dog-bone vias must go: 36–43 B parts
under U1 in r1 (16 straps on the kept seed), and their nets were the recurring open nets at U1
(BOOT_CFG1_x/2_x/4_x). `apart` is one group-gap term (5 per mm, ≤3 mm), so r2 still had 10–15
straps under U1. Only an intent keep-out with an `allow` list of the core group (r3, `intent_r3.json`
`u1_back`) cleared them.

**Repro:**
```bash
python3 -X utf8 py_placer/place_simple.py $R/r1_fixed.kicad_pcb $R/out_s.kicad_pcb --groups $R/r1_groups.json --intent $R/r1_intent.json --seed 2
python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as p;b=p('$R/out_s.kicad_pcb');print(sum(1 for r,f in b.footprints.items() if f.layer=='B.Cu' and 79.8<=f.x<=93.8 and 103.2<=f.y<=117.2))"
```
**Existing issues:** `"halo back side"` → #456 (closed, clearance model ignores side; different).

---

## 8. `route_bus` writes OUT without the board's `.kicad_dru` and design-brief siblings  (cost: ~10 min)

**Tool:** `awx/route_bus.py`.

**True:** `final_route_old2/` holds `s1a_bus.kicad_pcb` and `.kicad_pro` only; the input had
`.kicad_dru` and `.design-brief.json`. Every later step read no dru, and KiCad graded the bus board
with no length rule (my first check printed `length_out_of_range 0` — false; with the dru restored
by hand it was 4). The skill's "never cp a board without its siblings" rule is broken by the tool.

**Repro:** `ls $W/final_route_old2/ | grep s1a_bus` (no `.kicad_dru`); to regenerate,
`python3 -X utf8 awx/route_bus.py $R/bus_in.kicad_pcb $R/out_bus.kicad_pcb --rounds 2 --inproc --bus U1:U2:joint:F.Cu,B.Cu,In1.Cu,In2.Cu --clearance-ceiling 0.1 --track-width 0.1 --fanout-track-width 0.1 --via-size 0.45 --via-drill 0.25; ls $R/out_bus.*` (~35 min).
**Existing issues:** `"route_bus kicad_dru"`, `"route_bus sibling"` → none.

---

## 9. `route_bus` hands on a board with a caged ball and lane copper on the GND plane layer  (cost: ~10 min)

**Tool:** `awx/route_bus.py` (joint mode, all four layers named as the skill says).

**Claim:** `BUS U1->U2 ... connected=1 drc=1 (bus 0, board 0 vs 0 in)`; joint fanout "every ball served".

**True:** after the rest of the chain, VMEM stays open at U2.F1 (73.60, 105.40):
`check_reachability --pad U2.F1` → `VERDICT CAGED for any track width`, walled by locked bus lanes
(which no later step may rip). The bus board also carries VMEM tails on In1.Cu (the solid GND plane
layer), e.g. a 4.4 mm dangling VMEM segment at (88.40, 103.38).

**Repro:**
```bash
python3 -X utf8 py_tools/check_reachability.py $R/bus_vmem_caged.kicad_pcb --pad U2.F1 | tail -2
python3 -X utf8 py_router/check_weird.py $R/bus_vmem_caged.kicad_pcb | grep "VMEM (In1.Cu)"
```
**Existing issues:** `"VMEM caged route_bus"` → none.

---

## 10. `check_drc`'s default margin passes copper KiCad rejects at a footprint's own clearance  (cost: ~10 min)

**Tool:** `py_router/check_drc.py` (and `board_score`'s drc component).

**Claim:** board_score `drc 0`; check_drc at the default 5 % margin: clean.

**True:** U1's footprint declares a local clearance of 0.12 mm; the router lays tracks at
0.115–0.1186 mm. `check_drc --clearance-margin 0` finds 15 PAD-SEGMENT violations ("Required
clearance: 0.1200mm (local/netclass override)"), KiCad's DRC reports them as errors
(`kicad_drc_compare`: kicad=6 check_drc=0, DIVERGED). Shipped board: 0 either way (fixed by a
fine-grid force-reroute of the one net, BOOT_CFG1_3, that grazed).

**Repro:**
```bash
python3 -X utf8 py_router/check_drc.py $R/u1_local_clearance.kicad_pcb | grep FOUND                       # default margin
python3 -X utf8 py_router/check_drc.py $R/u1_local_clearance.kicad_pcb --clearance-margin 0 | grep FOUND   # 15
python3 -X utf8 tests/stress/kicad_drc_compare.py $R/u1_local_clearance.kicad_pcb --baseline $R/r1_fixed.kicad_pcb | tail -3
```
**Existing issues:** `"footprint local clearance 0.12 margin"` → none on point.

---

## 11. `converge.py record` refuses the first board_score row after the skill's quick_score rows  (cost: ~10 min)

**Tool:** `py_placer/converge.py record` with the skill's own score files.

**Claim:** `this lap looks like an IMPROVEMENT only because it graded FEWER components ... Nothing was written.`

**True:** the previous accepted completion row is a judged seed's `quick_score` file, which has no
`ungraded` list; every real `board_score` row (impedance and net_widths ungraded on a board that
declares neither) reads as "fewer components". The skill tells you to record fast routes with
quick_score and full routes with board_score in one ledger, so the first full route (and the
first DONE) cannot be recorded as accepted. I recorded the first full route `--rejected` and the
DONE / optimisation rows with a quick_score-shaped file of the same board (route tally + quality;
the board_score files sit beside them).

**Repro:** `python3 -X utf8 py_placer/converge.py record --ledger $R/out_l.jsonl ...` after copying
`$W/ledger.jsonl` rows 1–13 to $R/out_l.jsonl, with `--score-file $W/final.score.json --kind completion`.
**Existing issues:** `"converge record quick_score commensurab"` → none.

---

## 12. `check_assembly` passes a courtyard overlap KiCad reports as an error  (cost: ~5 min)

**Tools:** `place_pose.py`, `check_assembly.py`.

**True:** after `place_pose set C20 75.55 112.4 --rot 90` (legal, no_worse), check_assembly said
`buildable` with no courtyard pair; KiCad's DRC reported `courtyards_overlap FB2/C20` (error).
The overlap is under check_assembly's floors (area ≥ 0.5 mm² or 25 %, depth ≥ 0.3 mm) — a documented
policy, but one that ships a board KiCad marks as failing. Moved C20 to x 75.1.

**Repro:** `python3 -X utf8 py_tools/check_assembly.py $R/courtyard_c20_fb2.kicad_pcb | grep -E "VERDICT|COURTYARD"`;
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc --format json --severity-all -o $R/out_c.json $R/courtyard_c20_fb2.kicad_pcb; grep -c courtyards_overlap $R/out_c.json`.
**Existing issues:** none found for "courtyard overlap floors KiCad courtyards_overlap".

---

## 13. No tool runs the skill's seed judge or a post-DONE lap  (cost: ~10 min; two helpers)

**Skill steps:** plan-pcb-placement §3.6 step 1 ("fast-route the seeds judge.json names with the
board's routing chain ... copy its last board ... score each") and §1 "better, once DONE".
Nothing runs a chain over the named seeds; I wrote `helpers/judge_chain.sh` (one seed: pour, two
fanouts, cap pass, route_diff, `route.py --quick 2`, copy, quick_score) and `helpers/opt_lap.sh`
(re-run the main route from a fixed pre-route board with flag variants, then the cleanup helpers,
then grade). Repro: `bash $W/helpers/judge_chain.sh $W 1 2`.
**Existing issues:** none found ("judge runner").

---

## 14. Skill text gaps

- **plan-pcb-routing Step 1a** says to use `route_bus` "on every bus between two ball arrays";
  on this board it is the reason the declared length window fails (item 1), and the skill has no
  step for a `.kicad_dru` length rule at all (Step 5a-tuned-iii covers netclass NAME hints only).
  What worked: route the windowed byte lane FIRST, before any fanout of its balls, with
  `--direction-preference-cost 0 --turn-cost 0 --heuristic-weight 1 --grid-step 0.05 --via-cost 25`,
  in protected `--length-match-group` steps ordered so the longest lanes are laid first.
- **"Hand-written copper: stage each join with check_join.py and stamp it (locked yes)"** —
  check_join stages but no tool stamps a lock on a segment; the four 0.05 mm joins ship unlocked.
- **Verifier brief vs the graders:** verifier.md says a declared class (diff pairs among them) whose
  component is ungraded is a FAIL, and board_score has no diff-pair component at all, so a board with
  DDR pairs cannot get a clean verdict from the stack; the verifier graded them by hand with
  review-routed-board Step 4 and itself called the FAIL a judgement call ("read your way, the spec
  lens would be PASS").
- **§3.6 judge vs DONE:** the judge ranks by quick_score (no floorplan); a seed with an
  error-graded floorplan violation (item 5) can win and only fails at the full route.
