# TOOL_GAPS -- gpm board 05 interf_u

Ranked by what each one cost this run. Every repro command runs from the WT root
(`~/Documents/git/krt-gpm`, with the krt venv's `python3`); its input board is a
`copy_board.py` copy under `wk/gpm/05_interf_u/repro/` (see `repro/README.txt`). No helper
script was needed in `helpers/`.

## 1. route.py's rip-up blames the wrong net when a B.Cu edge finger's only exit is walled (cost: ~10 laps, ~35 min)

**Tool / command.** `py_router/route.py`, multipoint phase 3 + rip-up ladder (every
`--ripup-blocker-select`: count, near-target, bidir, mincut), e.g.

```bash
python3 -X utf8 -u py_router/route.py wk/gpm/05_interf_u/repro/vcc_finger_walled.kicad_pcb \
    wk/gpm/05_interf_u/repro/out_vcc.kicad_pcb --nets VCC GND --no-bga-zones U9 \
    --clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5 \
    --power-nets GND VCC --power-nets-widths 0.7 0.7 --layer-costs 1.0 1.0 \
    --direction-preference-cost 4000 --turn-cost 2000 --via-cost 600 --escalation board \
    > wk/gpm/05_interf_u/repro/out_vcc.log 2>&1
grep -E "Ripping|was blocking|No additional rippable" wk/gpm/05_interf_u/repro/out_vcc.log
```

**What it claimed.** `blockers: [{"net": "VCC", "stage": "phase3", "blocked_by": [{"net": "/PC-DB6",
"blocked_count": 1, ...}]}]`; it rips `/PC-DB6`, fails, restores it, and prints
`No additional rippable blockers from retry analysis`. VCC ships open at BUS1 pad 3.

**What was true.** BUS1 pad 3 is the +5V finger on **B.Cu** (164.47, 138.43, 1.778 x 7.62 mm).
`/PC-DB6` is the **F.Cu** finger on the other side of the card (pad 34) and its F.Cu track -- it
only forbids a via in the finger. The wall is `/PC-RST`'s **B.Cu** track
`(162.4,134.2)-(165.6,134.2)-(167.0,135.6)`, 0.42 mm above the finger's top end, spanning its whole
width: the finger has no B.Cu exit at all (the backward search explores 1785 cells -- the finger
itself -- and stops). Listing the copper:
`python3 -c "import sys;sys.path.insert(0,'py_router');from kicad_parser import parse_kicad_pcb as p;b=p('wk/gpm/05_interf_u/repro/vcc_finger_walled.kicad_pcb');[print(s.layer,(s.start_x,s.start_y),(s.end_x,s.end_y)) for s in b.segments if b.nets[s.net_id].name=='/PC-RST' and min(s.start_y,s.end_y)>130]"`
prints exactly those two B.Cu segments. `/PC-RST` is never named, so no selector can rip it.
The two workarounds also fail: `--nets VCC /PC-RST GND --rip-existing-nets /PC-RST --force-reroute`
(with or without `--ordering original`) re-lays `/PC-RST` along the same line, because its
phase-1 edge is routed before VCC's phase-3 tap to the finger; and a failed-first split (VCC+GND
first, then `'*'`) opened four other nets. This one wall is the only open on every arm at via
cost >= 375 (375, 450, 600) and on arm B (layer costs 1:1, via cost 600), i.e. it is what bounded
the via count from below (72 vias at via cost 600 with this single open, 88 shipped).

**gh search** `"blocker misattributed rip-up wrong net"`, `"rippable blockers edge finger"`,
`"edge finger via rip"`: no issue covers it (closest: #510, partial leg-level rip-up, closed;
#592, connector-row escape combing, open -- neither is the attribution).

## 2. plan-pcb-routing never says how to keep the board's authored floors; the default `--escalation fab` silently crossed them (cost: one DONE board discarded as UNSOUND, ~15 min)

**Tool / command.** `py_router/route.py` at its defaults (`--fab-tier auto --escalation fab`) with
`--clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5`, and the skill text
(`plan-pcb-routing` Steps 4/2c, which pass `--clearance-ceiling` as "the floor the whole chain
routes to"). Repro:

```bash
python3 -X utf8 py_router/copy_board.py wk/gpm/05_interf_u/repro/placed_seed1.kicad_pcb wk/gpm/05_interf_u/repro/esc_in.kicad_pcb
python3 -X utf8 -u py_router/route.py wk/gpm/05_interf_u/repro/esc_in.kicad_pcb wk/gpm/05_interf_u/repro/esc_out.kicad_pcb \
    --nets '*' --no-bga-zones U9 --clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5 \
    --power-nets GND VCC --power-nets-widths 0.7 0.7 --layer-costs 1.0 1.0 --via-cost 600 \
    > wk/gpm/05_interf_u/repro/esc_out.log 2>&1
grep PROJECT_WRITES_JSON wk/gpm/05_interf_u/repro/esc_out.log
```

**What it claimed.** The chain's own `check_complete` (and `board_score`) graded the result
DONE / clean; `--clearance-ceiling 0.254` reads as "route no tighter than 0.254".

**What was true.** Measured on this board: arm B wrote
`net_class[Default].clearance: 0.254 -> 0.1588`, `net_class[Power].clearance: 0.254 -> 0.1588`,
`rules.min_track_width: 0.2 -> 0.127`; arm A wrote `min_track_width 0.2 -> 0.175`,
`min_via_diameter 0.9 -> 0.45`, `min_through_hole_diameter 0.5 -> 0.2` (a GND net rescue
escalated to the advanced fab tier on a 2-layer through-hole board). The first DONE board
(`final_route_old1/lap2.kicad_pcb`) reads `check_complete --authored-from`: **UNSOUND -- copper below
floors its project once declared**. Everything is disclosed in the `Design rules [...]` line, as
designed (CLAUDE.md: "Completion first, DISCLOSED"), but the routing skill never tells the agent
that `--escalation board` is the switch that keeps the descent inside the authored floors; I found
it in `route.py --help`. With `--escalation board` every later arm stayed at 0.254 / 0.2 / 0.9-0.5,
and the shipped board grades DONE under `--authored-from`.

**gh search** `"escalation board authored floor clearance relaxed"`: #1160 (closed; a rescue lowers
the Default class for the NEXT step) is related but not this; no issue asks the skill to name
`--escalation board`.

## 3. analyze_power_paths counts a sink's current once per power PIN (cost: ~10 min, would have shipped 2.0 mm GND / 1.2 mm VCC)

**Tool / command.** `py_tools/analyze_power_paths.get_power_net_recommendations` (the
`/analyze-power-nets` skill's Step 5). Repro:
`python3 -X utf8 wk/gpm/05_interf_u/repro/power_double_count.py`

**What it claimed.** With every IC classified at 10 mA (6 ICs = 60 mA) and BUS1 as a 100 mA
source, it recommends `GND 0.7`, `VCC 0.7` (the 100-500 mA band). With this run's real
estimates (~455 mA total, BUS1 at 460 mA) it recommended **GND 2.0 mm, VCC 1.2 mm** (>= 2 A and
1-2 A), and `unconnected-(BUS1-GND-Pad10)` 0.5-0.7 mm (a one-pad net).

**What was true.** The loop at `py_tools/analyze_power_paths.py:418-439` adds
`comp.current_rating_ma` for EVERY pad whose pin is a power pin, so U9 (XC4003A, 8 VCC + 3 mode
pins tied to VCC, 9 GND) contributes ~9x its current, and a source with two +5V fingers counts
twice. The real load is ~0.46 A -> 0.7 mm by the skill's own table. I used 0.7 mm for both and
said so in REPORT.md.

**gh search** `"power net width per pin double count"`, `"power_paths current pin"`,
`"analyze power nets current"`: no issue covers it (#124, power widths not widened, closed
wontfix, is the opposite direction).

## 4. The routing skill contradicts its own plan checker on thermal relief; keeping the reliefs left 5 KiCad `starved_thermal` errors no DONE gate counts (cost: ~5 min; the outcome ships)

**Tool / command.** `.claude/skills/plan-pcb-routing/SKILL.md` Step 1 ("If it should be replaced
but keep thermal relief, add `--thermal-relief`") against
`.claude/skills/plan-pcb-routing/scripts/route_plan_check.py` rule R07 ("no teardrops, no thermal
relief") and Step 6 ("do not set `--thermal-relief`"). Repro of the outcome:

```bash
python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/05_interf_u/routed.kicad_pcb --baseline wk/gpm/05_interf_u/final_route/in.kicad_pcb
```

**What it claimed.** `board_score` blocking 0, `check_complete` DONE, `check_drc` 0, and
`kicad_drc_compare` CONSISTENT.

**What was true.** This is a hand-soldered through-hole board whose designer poured GND on B.Cu
with thermal relief and 0.5 mm clearance. A re-pour would come back solid (R07 forbids the flag
that keeps the reliefs), so I kept the designer's pour as drawn (no `route_planes` step). At 0.5 mm
the pour cannot enter a 2.54 mm PGA/DIP pin field, and KiCad's own DRC (`kicad-cli pcb drc
--refill-zones`) reports **5 `starved_thermal` errors** at the project's severity on the delivered
board (U2.10, U8.12, U9.G2, U9.K3, U9.L7; 3 on the via-300 board) -- each pad still connected
through tracks (`unconnected 0`). `kicad_drc_compare` prints them as `thermal=5`, outside its
verdict; no DONE gate (`board_score`, `check_complete`, the verifier brief) reads them.

**gh search** `"starved thermal"`: #1334 (closed: "A DONE board ships KiCad starved_thermal errors
... that no repo grader reports" -- fixed by reporting them, not by gating); `"skip-existing-zones
thermal"`: #1329 (closed: route_planes replaces a designer's zone, thermal -> solid). Neither covers
the Step 1 / R07 contradiction.

## 5. The quick judge and the full route disagree once the routing recipe changes, and the skill has no step for it (cost: ~15 min)

**Tool / command.** `py_placer/judge_seeds.py` (`--quick 2`) vs the same chain routed in full;
skill §3.7/§3.8. Repro (quick vs full on the two seeds, C300 chain):

```bash
for s in 1 11; do python3 -X utf8 -u py_router/route.py wk/gpm/05_interf_u/repro/placed_seed$s.kicad_pcb wk/gpm/05_interf_u/repro/full_s$s.kicad_pcb \
  --nets '*' --no-bga-zones U9 --clearance-ceiling 0.254 --track-width 0.2 --via-size 0.9 --via-drill 0.5 \
  --power-nets GND VCC --power-nets-widths 0.7 0.7 --layer-costs 1.0 1.0 --direction-preference-cost 4000 \
  --turn-cost 2000 --via-cost 300 --escalation board > wk/gpm/05_interf_u/repro/full_s$s.log 2>&1; done
grep JSON_SUMMARY_MIN wk/gpm/05_interf_u/repro/full_s*.log
```

**What it claimed.** Re-judging pass 1 with the board's better chain (Step 8's through-hole recipe,
via cost 300), `judge_seeds` printed `best seed 11: keep its placement s11.kicad_pcb` (quick:
seed 11 blocking 2 / 71 vias, seed 1 blocking 3 / 67 vias).

**What was true.** Full routes of the same chain (+2 iterations): seed 1 **DONE, 93 vias**; seed 11
**blocking 1, 99 vias**. The first judging (router defaults chain) had picked seed 1. The skill
says the judging chain is "a starting point" for §3.8 but not what to do when §3.8 finds a much
better recipe (here 162 -> 93 vias): re-judge or not, and which verdict wins. I kept seed 1 on the
full-route evidence and recorded seed 11's full route as rejected.

**gh search** `"judge_seeds quick route ranking full route"`, `"re-judge seeds routing chain"`:
no issue covers it.

## 6. kicad_drc_compare names a starved thermal as pad `?` at the zone's corner (cost: ~5 min, a hand kicad-cli run to find the pads)

**Tool / command.**
`python3 -X utf8 tests/stress/kicad_drc_compare.py wk/gpm/05_interf_u/routed.kicad_pcb --baseline wk/gpm/05_interf_u/final_route/in.kicad_pcb`

**What it claimed.** Five identical lines
`STARVED-THERMAL ?  ['GND'] @ (193.675, 133.35)  Thermal relief connection to zone incomplete`.

**What was true.** (193.675, 133.35) is a corner of the GND zone's outline, not a pad. KiCad 10.0.7's
own report names the pads (`PTH pad 10 [GND] of U2`, `PTH pad 12 [GND] of U8`, `PTH pad G2/K3/L7
[GND] of U9`); `_THERMAL_PAD_RE = re.compile(r"Pad\s+(\S+)\s+\[[^\]]*\]\s+of\s+(\S+)")`
(`tests/stress/kicad_drc_compare.py:147`) is case-sensitive and never matches KiCad's lower-case
`pad`, so every row falls back to `?` and the first item's (the zone's) position. Found by me and
independently by the verifier.

**gh search** `"kicad_drc_compare thermal pad regex PTH"`: no issue; #1334 (closed) added the
`thermal=` channel this mis-labels.

## 7. `board_score --quiet` still prints the whole SCORE_JSON line (cost: minor, context)

**Tool / command.** `python3 -X utf8 py_tools/board_score.py wk/gpm/05_interf_u/repro/interf_u_pile.kicad_pcb --intent wk/gpm/05_interf_u/intent.json --baseline wk/gpm/05_interf_u/repro/interf_u_pile.kicad_pcb --json wk/gpm/05_interf_u/repro/q.json --quiet 2>/dev/null | wc -c`

**What it claimed.** `--quiet`.

**What was true.** Measured: 21,454 bytes on stdout for the 24-part pile (one `SCORE_JSON=` line carrying all 109
unrouted net names three times, before the `BLOCKING=` line) and 4,290 bytes on the routed board,
on every call; I redirected it to /dev/null thereafter.

**gh search** `"board_score quiet SCORE_JSON"`: #1194 (closed, "board_score --quiet prints 590 KB")
-- the size fell, the line is still there.
