# TOOL_GAPS -- gpm board 11 (daplink)

Ranked by what each cost this run. Every repro runs from the worktree root
(`cd ~/Documents/git/krt-gpm && export PATH="$HOME/.venvs/krt/bin:$PATH";`)
against the boards copied into `wk/gpm/11_daplink/repro/`. No helper script was
written (`helpers/` is empty).

## 1. route.py's via-in-pad unblock (#535) leaves dangling vias that the end-of-run sweep (#1166) cannot remove -> `check_complete` INCOMPLETE

- **Tool / command:** `py_router/route.py` (any chain step on this board), e.g.
  `route.py IN OUT --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0`
- **What it claimed:** the run reports clean (`failed 0`, `open_single []`,
  `JSON_SUMMARY_MIN` with nothing wrong), prints no `Dangling vias (#1166, end of run): removed ...`
  line, and the #1166 docstring promises that every via check_weird calls dangling is removed.
- **What was true:** the output carries 4 vias that check_weird and KiCad call
  `via_dangling` (/OSCIN at U2.5, /OSCOUT at U2.6, /PA0 at U2.10, /TGT_SWDIO at
  U2.27, all 0.3/0.2 vias dropped by "Via-in-pad unblock: dropped 1 fab-floor
  via(s) to reach a boxed endpoint (1 off-pad escape stub(s), #535)"). Each sits
  on F.Cu between two F.Cu segments whose ends are 0.07 mm apart inside the
  barrel -- the via is the only thing joining them -- so `sweep_dangling_via_branches`
  removes the via alone, finds two new dangling ends, and its gate refuses
  (measured: before = 1 dangling via / 0 dangling ends; after = 0 / 2 ends at
  (124.85,113.25) and (124.80,113.20)). `check_complete` then reads
  `INCOMPLETE -- weird_copper: not clean`, so a board with blocking 0 is not DONE.
  `--same-net-pad-clearance 0.1` only moves the dropped via 0.1 mm off the pad:
  the same 4 dangling vias came back (arm C, 40 vias). The fix that worked every time was
  re-routing the named nets with `--nets <nets> GND --force-reroute`
  (pass 1: 34 -> 30 vias; pass 2: 21 -> 20). The sweep could merge the two
  segment ends (or re-draw the stub) instead of refusing.
- **Cost:** about 12 min: arms B and C, the gate investigation, and a force-reroute
  lap on every routed candidate.
- **Repro:**
  `python3 -X utf8 py_router/route.py wk/gpm/11_daplink/repro/gap1_s1_diff.kicad_pcb wk/gpm/11_daplink/repro/gap1_out.kicad_pcb --nets '*' '!GND' --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 && python3 -X utf8 py_router/check_weird.py wk/gpm/11_daplink/repro/gap1_out.kicad_pcb`
  -> `FOUND 4 WEIRD THINGS`, 4 x `dangling via` (verified at 16:55Z).
- **Issues:** `gh issue list --state all --search "dangling via"` and
  `"1166 dangling"`: #1166 (CLOSED, "route.py never removes a dangling via, or the
  dead branch it ends") is the parent; #1179 (CLOSED, a plane-finalize via joining
  one layer) is a sibling. Neither covers a via that is the only join of two
  same-layer segments; this case is new.

## 2. At the board's own floors route.py cannot route /OSCOUT, a pad check_reachability calls PASSABLE

- **Tool / command:** `py_router/route.py ... --escalation board --fab-tier standard --same-net-pad-clearance 0.1`
  (arm B of the full route, then its `Hint:` rip set, then `--force-reroute` of the four nets round the pad).
- **What it claimed:** `Boxed in at this geometry after 5025 iteration(s) (grid 0.1, clearance 0.2, track 0.127 mm)`,
  `no rippable blockers found`, and a Hint to rip `/PA0 /IF_RST /PA12 +3.3V /OSCIN`.
- **What was true:** `check_reachability --pad U2.6` on the failed board:
  `VERDICT PASSABLE at track 0.127mm (margin +173.3 um)`, throat 0.700 mm between U2.5 and U2.7,
  "ROUTED COPPER cages this pad, the placement does not: a ROUTING finding". Taking the hint
  (`--rip-existing-nets` with all five) and force-rerouting /OSCOUT /OSCIN /IF_RST /PA0 together
  both left /OSCOUT open (1 broken). The only DONE board therefore relies on the
  default `--escalation fab`, which went below the board's authored floors
  (vias 0.5 -> 0.3/0.2 drill, annular 0.1 -> 0.05, Default clearance 0.2 -> 0.1452) and
  put 10 of its 20 vias in pads (IPC-4761 Type VII). `check_complete --authored-from`
  reads UNSOUND for exactly that.
- **Cost:** about 5 min (3 laps), and a board that does not keep its authored floors.
- **Repro:**
  `python3 -X utf8 py_router/route.py wk/gpm/11_daplink/repro/gap3_boardfloors.kicad_pcb wk/gpm/11_daplink/repro/gap3_out.kicad_pcb --nets '/OSCOUT' '/OSCIN' '/IF_RST' '/PA0' GND --force-reroute --track-width 0.127 --clearance-ceiling 0.2 --via-size 0.5 --via-drill 0.3 --power-nets '+5V' '+3.3V' GND --power-nets-widths 0.7 0.7 0.7 --layer-costs 1.0 1.0 --escalation board --fab-tier standard --same-net-pad-clearance 0.1`
  -> `failed_single: ["/OSCOUT"]`; then
  `python3 -X utf8 py_tools/check_reachability.py wk/gpm/11_daplink/repro/gap3_out.kicad_pcb --pad U2.6 --clearance 0.2 --track 0.127`
  -> `PASSABLE`, "with the routing in place: CAGED" (verified 16:56Z).
- **Issues:** `--search "boxed in PASSABLE reachability"`: only #1031 (CLOSED, rule-area
  keepouts) and #1348 (CLOSED, route_bus caging a ball) -- neither is this.

## 3. analyze_power_paths sizes a net by the part's current once PER POWER PIN (GND 2.0 mm, +3.3V 1.0 mm for a ~300 mA board)

- **Tool / command:** `/analyze-power-nets` Step 5,
  `get_power_net_recommendations(pcb_data, components, paths)` in `py_tools/analyze_power_paths.py`.
- **What it claimed:** `+3.3V 1.00`, `GND 2.00`, `+5V 0.70` (the skill says these are the
  widths the route step carries).
- **What was true:** the loop over a CURRENT_SINK / POWER_SOURCE's pins adds
  `comp.current_rating_ma` for every power pin, so the STM32 (50 mA, 5 VDD + 4 VSS pins) puts
  250 mA on +3.3V and 200 mA on GND, and P1 (classified 500 mA, 8 GND/shield pads) puts 4 A
  on GND -- hence 2.0 mm. The board's real budget is about 300 mA (LDO estimate), which the
  same IPC table maps to 0.7 mm. I used 0.7 / 0.7 / 0.7 and said so in REPORT.md.
- **Cost:** about 3 min reading the code and re-deriving the widths.
- **Repro:**
  `python3 -X utf8 -c "import sys;sys.path[:0]=['py_tools','py_router'];from analyze_power_paths import *;c,p=analyze_pcb('wk/gpm/11_daplink/repro/gap2_pile.kicad_pcb');classify_component(c,'P1',ComponentRole.POWER_SOURCE,current_rating_ma=500);classify_component(c,'U1',ComponentRole.POWER_SOURCE,current_rating_ma=300);classify_component(c,'U2',ComponentRole.CURRENT_SINK,current_rating_ma=50);print(get_power_net_recommendations(p,c,trace_power_paths(p,c)))"`
  -> GND 2.0, +3.3V 1.0 for 850 mA of declared sources and 50 mA of sinks.
- **Issues:** `--search "analyze_power_paths current per pin"`, `"power net recommendations GND width overcount"`,
  `"get_power_net_recommendations"`: none covers it (#124 CLOSED is the opposite complaint).

## 4. The routing skill's parameter table says "--via-cost ... Higher = fewer vias"; on this board it was the reverse

- **Tool / command:** plan-pcb-routing SKILL.md, "Advanced Routing Parameters":
  `--via-cost 75 | 75 | Higher = fewer vias, longer paths`.
- **What was true:** the same chain on the same pass-1 placement: via cost 75 -> 34 vias
  (30 after the gap-1 fix), 150 -> 43 vias / 481 mm, 300 -> 49 vias / 594 mm (all blocking 0).
  One board, so not a default argument -- but the table states the direction as a fact.
- **Cost:** one lap (~2 min).
- **Repro:** `bash wk/gpm/11_daplink/exp_via150/plan.sh && bash wk/gpm/11_daplink/exp_via300/plan.sh`
  (each the shipped chain with `--via-cost N` added to its route steps; their `in.kicad_pcb` is the
  pass-1 placement, also kept as `repro/gap5_final_pass1.kicad_pcb`), then
  `python3 -X utf8 py_tools/board_score.py wk/gpm/11_daplink/exp_via150/s6_iter2.kicad_pcb --quiet` (and via300).
- **Issues:** `--search "via-cost more vias"`: none.

## 5. converge.py verdict says "only one of them carries a score" when every row in the window carries one

- **Tool / command:** `py_placer/converge.py verdict --ledger wk/gpm/11_daplink/ledger.jsonl --score wk/gpm/11_daplink/final_route/s7_force.score.json`
- **What it claimed:** routing `no-comparison` ... "no two of the last 5 can be COMPARED -- only one of
  them carries a score ... Score those laps the same way as the rest and re-record them".
- **What was true:** all five rows (iterations 24, 25, 32, 33, 34) were recorded with
  `--score-file` and carry a full board_score payload; four are `--rejected`, so only ONE is
  ACCEPTED, and the code (`blocked: single-lap`) excludes rejected rows from the sequence. The
  advice to re-score them is wrong; the real remedy is another accepted lap or `--exhausted routing`.
- **Cost:** ~2 min.
- **Repro:** the command above on the shipped ledger.
- **Issues:** `--search "no-comparison converge"`: #1323, #1071, #1075 (all CLOSED, different
  defects); none covers the message.

## 6. manifest_to_plan.py reads the plain redirect the routing skill prescribes as tool arguments, and calls a command that ran "REJECTED"

- **Tool / command:** `python3 -X utf8 tests/stress/manifest_to_plan.py wk/gpm/11_daplink/final_route/final_plan.sh -o final_plan.json`
  (plan-pcb-routing Step 9). The skill says "In the plan file use a plain redirect, `> /tmp/step.txt 2>&1`, or nothing at all".
- **What it claimed:** `command 3: route_planes.py refuses its arguments after parsing: number of net arguments (2) must match number of plane layers (5)` -- "the CLI ran nothing for them" -- and it dropped the route_diff and first route.py steps as "upstream of a rejected command" (4 of 7 steps written).
- **What was true:** route_planes ran and poured (s3_pour.kicad_pcb, its log, and the recorded manifest all exist); the converter tokenized `> .../s3_pour.log 2>&1` into `--plane-layers`, making 5 layers. Converting the recorded `redo_commands.sh` (no redirects) instead wrote all 7 steps.
- **Cost:** ~2 min.
- **Repro:** `python3 -X utf8 tests/stress/manifest_to_plan.py wk/gpm/11_daplink/repro/gap6_final_plan.sh -o wk/gpm/11_daplink/repro/gap6_plan.json` -> the REJECTED warning above.
- **Issues:** `--search "manifest_to_plan redirect"`, `"plan.sh redirect tokenized"`: none; `"manifest_to_plan route_planes plane layers"`: #361 (CLOSED, param gaps), not this.
