# TOOL_GAPS -- gp14 board 02 sonde_xilinx

Ranked by what each cost this run. Every repro command runs from the WT root
(`~/Documents/git/krt-gp14`) with the venv python first on PATH, and reads
only files under `wk/gp14/02_sonde_xilinx/repro/` (copies made with `copy_board.py`).
No helper scripts were written (`helpers/` is empty): every step used a repo tool.

## 1. place_simple: an edge-mount DSUB on its declared edge is "placed as any other part", exit 0, with a false reason

**Tool / command.** `py_placer/place_simple.py` with the campaign's given `intent.json`
(J1 declared `edge: west`, no `overhang_mm`).

**What it claimed.**
`WARNING: J1 is declared on an edge but has no seat there (no room along the west edge); placed as any other part`,
then `JSON_SUMMARY ... "illegal": []` and exit 0. The placement is reported legal and the run succeeds.

**What was true (measured).**
- There IS room along the west edge: J1's pad row spans 35.1 mm (33.24 mm pitch span + one 1.85 mm pad)
  on a 43.18 mm edge, and with an overhang band the same command seats it there (below).
- The real cause is the overhang target. With no `overhang_mm` the seat aims at 0 (flush), graded in
  `legacy_occupancy@margin=0.254` (the courtyard), and J1's 54.1 mm DB25 flange courtyard is wider than
  the 43.18 mm edge, so the band reads >= 11.43 mm (flange past N and S) at EVERY pose. `_seat_coord`'s
  bisection never leaves the board centre and `_free_stretches` finds no stretch, which the message
  reports as "no room".
- The output board violates the intent it was given: `check_floorplan --intent intent.json` on it gives
  2 ERRORs (`J1 sits nearest the north edge but is declared on the west edge`; `its mating face points north`).
  place_simple's own summary says nothing is wrong (`illegal: []`, exit 0).
- Fix used in this run (skill §3.4): `intent_seat.json` = the given intent plus
  `overhang_mm {min 25.88, max 26.2}` for J1 and `{min 14.45, max 14.8}` for J2, measured by posing each
  part with its pad row 1.99 mm inside the edge (the footprint's own Dwgs.User PCB-edge marker line).
  With it every one of the 12 seeds seated J1 west / J2 east, facing out, pads 0.25 mm inside.
- Cost: about 15-20 min (probe, read edge_seat.py, measure the band, write the derived intent).

**Repro.**
```bash
python3 -X utf8 py_placer/place_simple.py wk/gp14/02_sonde_xilinx/repro/sonde_xilinx.kicad_pcb \
    wk/gp14/02_sonde_xilinx/repro/out/gap1_s0.kicad_pcb --groups wk/gp14/02_sonde_xilinx/repro/groups.json \
    --intent wk/gp14/02_sonde_xilinx/repro/intent_given.json --seed 0      # WARNING ... no room; exit 0
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/02_sonde_xilinx/repro/out/gap1_s0.kicad_pcb \
    --intent wk/gp14/02_sonde_xilinx/repro/intent_given.json               # 2 x [ERROR] edge_connector J1
# control: the same with --intent wk/gp14/02_sonde_xilinx/repro/intent_seat.json seats J1 west, 0 errors
```

**Existing issues** (`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`):
"no room along edge seat", "has no seat there", "courtyard longer than edge", "edge-mount DSUB" --
nothing covers it. Nearest: #987 (seat accepted within 0.02 mm of its band), #1155 (reversed
edge-mount connector passes), #1240/#1242 (re-seat paths) -- all closed, all different.

## 2. A routing step's project writeback turns a passing placement into a floorplan ERROR with no part moved

**Tool / command.** `route.py` (clearance descent + Default-class writeback) and `route_planes.py`
(fab-edge pin of `min_copper_edge_clearance`), then `check_floorplan` / `board_score` on the routed board.

**What it claimed.** On judged seed 7 (and seed 1) routed with the chain's recipe, `board_score` reports
`BLOCKING=2 (floorplan=2)` -- two `edge_connector` ERRORs -- on a board that is fully connected and
DRC-clean, and whose J1/J2 poses `check_floorplan` passed before routing.

**What was true (measured).**
- Before routing, `check_floorplan r1/s7 --intent intent_seat.json`: J1 overhang 25.8800 mm
  `[legacy_occupancy@margin=0.254] pass`, pad copper 0.0150 mm vs 0.01 mm pass; 0 errors.
- route.py's escalation descent routed `/CTRL-D3` and `/TD0-PROG-D4` at 0.2223 mm and the writeback stored
  it as the Default class (`DEFAULT CLASS CLEARANCE LOWERED BY A DESCENT -- 0.254 -> 0.2223 mm`).
  route_planes had already pinned `rules.min_copper_edge_clearance: 0.01 -> 0.2 mm (fab-edge pin)`.
- After routing, with no footprint moved: J1 overhang 25.7849 mm `[legacy_occupancy@margin=0.2223] fail`
  (under the declared 25.88), J2 14.4183 mm fail, and J1 pad copper 0.0150 mm vs 0.2 mm fail -> 2 errors.
  The band's currency (courtyard at the netclass-clearance margin) moves with a value the router rewrites,
  and place_simple seats pad copper at the board's declared 0.01 mm edge rule, which the first routing tool
  replaces with 0.2 mm.
- The shipped board (seed 11) was not affected (no descent; J1 pads 0.252 mm inside), but two of the six
  judged seeds became ineligible after a full route. Cost about 10-15 min to find.

**Repro.**
```bash
R=wk/gp14/02_sonde_xilinx/repro
python3 -X utf8 py_tools/check_floorplan.py $R/s7.kicad_pcb --intent $R/intent_seat.json          # 0 errors
python3 -X utf8 py_router/route_planes.py $R/s7.kicad_pcb $R/out/gap2_planes.kicad_pcb --nets GND --plane-layers B.Cu
python3 -X utf8 py_router/route.py $R/out/gap2_planes.kicad_pcb $R/out/gap2_routed.kicad_pcb --nets '*' \
    --power-nets GND VCC '/PWR_3,3-5V' --power-nets-widths 0.635 0.635 0.635 --track-width 0.254 \
    --via-size 0.889 --via-drill 0.508 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 600
python3 -X utf8 py_tools/check_floorplan.py $R/out/gap2_routed.kicad_pcb --intent $R/intent_seat.json --allow-routed   # 2 errors
```
(zsh: set `R` on its own line, or inline the path.)

**Existing issues.** #1160 (CLOSED) "One net's rescue lowers the Default class clearance in the project,
and the next step routes every net there" -- the same writeback, a different consequence (that issue is
about later routing steps, not about a placement grade flipping). Searches "legacy_occupancy margin",
"clearance descent writeback floorplan", "fab-edge pin edge clearance": nothing on the placement side.

## 3. Skill gap: the routing recipe for a light 2-layer through-hole board ships 16 vias where 0 are free

**Tool / command.** `.claude/skills/plan-pcb-routing/SKILL.md` followed as written (plane first on a light
2-layer board, `route.py --nets '*'` at the 2-layer default `--layer-costs 1.0 3.0`, default via cost 75),
compared with the `--quick 2` judging route of the same placement.

**What it claimed.** The judging route of seed 11 (same flags, `--quick 2`) scored 3 vias; the full
route of the same placement with the same flags gave 16 vias (VCC 6, Net-(U1B-E) 5, from Phase-3 tap
routing), DONE. Nothing in the recipe points at via cost for a board that has no failures: via cost
appears only in the "2-Layer Through-Hole Bus Boards" section (150), which this board is not.

**What was true (measured, 25 arms on the same placement, all DONE):**
| arm | vias | copper_mm | segments |
|---|---|---|---|
| recipe as written (1.0 3.0, via 75) | 16 | 539.07 | 144 |
| `--layer-costs 1.0 1.0` | 8 | 527.21 | 133 |
| `--via-cost 300` | 2 | 589.05 | 137 |
| `--layer-costs 1.0 1.0 --via-cost 600` | 0 | 535.08 | 124 |
| + `--grid-step 0.05 --direction-preference-cost 0 --turn-cost 2000` (shipped) | 0 | 516.67 | 119 |
On a through-hole board every pad is already a layer change, so a high via cost costs almost no copper.
Cost: about 10 min of arms (each 5-20 s). Also: the `--quick 2` judge's 3 vias did not predict the full
route's 16 under identical flags.

**Repro.**
```bash
P=wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb; O=wk/gp14/02_sonde_xilinx/repro/out
python3 -X utf8 py_router/route_planes.py $P $O/g3_planes.kicad_pcb --nets GND --plane-layers B.Cu
python3 -X utf8 py_router/route.py $O/g3_planes.kicad_pcb $O/g3_default.kicad_pcb --nets '*' --power-nets GND VCC '/PWR_3,3-5V' \
    --power-nets-widths 0.635 0.635 0.635 --track-width 0.254 --via-size 0.889 --via-drill 0.508 --layers F.Cu B.Cu --layer-costs 1.0 3.0   # 16 vias
python3 -X utf8 py_router/route.py $O/g3_planes.kicad_pcb $O/g3_via600.kicad_pcb --nets '*' --power-nets GND VCC '/PWR_3,3-5V' \
    --power-nets-widths 0.635 0.635 0.635 --track-width 0.254 --via-size 0.889 --via-drill 0.508 --layers F.Cu B.Cu --layer-costs 1.0 1.0 --via-cost 600   # 0 vias
```

**Existing issues.** #658 (CLOSED) "Via/copper economy gap vs human routing: ~3x the vias on equal nets";
#153 (OPEN) tune mode. Searches "via cost 2-layer vias", "fast route vias full route", "quick 2 vias": no
issue names the default 2-layer via cost on through-hole boards or the quick-vs-full via gap.

## 4. route_planes invents a `min_via_drill` floor, and route.py then warns the user about "the original number"

**Tool / command.** `py_router/route_planes.py` then `py_router/route.py` on a board whose project
declares no `min_via_drill`.

**What it claimed.** route_planes: `rules.min_via_drill: None -> 0.635 mm`. route.py next:
`rules.min_via_drill: 0.635 -> 0.508 mm ... Confirm your fab supports it; if the original number was a
real process limit, re-route at that floor rather than shipping this project.`

**What was true.** The board never declared a via-drill floor (its `min_through_hole_diameter` is 0.508);
0.635 is the Default class's via DRILL size copied in by route_planes one step earlier. The "original
number" the warning asks the user to respect was written by the toolchain, not by the author. Harmless to
the copper; cost about 5 min to rule out a real floor breach.

**Repro.**
```bash
python3 -X utf8 py_router/route_planes.py wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb \
    wk/gp14/02_sonde_xilinx/repro/out/g4_planes.kicad_pcb --nets GND --plane-layers B.Cu    # PROJECT_WRITES: min_via_drill None -> 0.635
```
then the route.py line of entry 3 (its log prints the 0.635 -> 0.508 warning).

**Existing issues.** "min_via_drill": #1195 (qfn_fanout lowers via/hole floors on a run that places no via),
#1170 -- related writeback family, neither covers route_planes writing an undeclared floor.

## 5. check_floorplan exits 4 on a clean final board, forever, because the INPUT was a pile

**Tool / command.** `py_tools/check_floorplan.py final.kicad_pcb --intent intent_seat.json --allow-routed`.

**What it claimed.** `0 error(s), 1 warning(s)` and exit 4 (`NOT FULLY GRADED: 3 budget_abstained ...`,
`"pass": false`).

**What was true.** The three abstained budgets (`decaps.max_distance_mm`, `oob_count`, `overlap_area`) were
withheld by the emitter because the source was staged as a pile (#1103), so no placement of this board can
ever make them gradable and the exit code can never be 0. The skill and the verifier read "0 errors", so it
cost nothing here beyond reading the tail; a script gating on the exit code would fail every board of this
campaign. Cost about 2 min.

**Repro.**
```bash
python3 -X utf8 py_tools/check_floorplan.py wk/gp14/02_sonde_xilinx/repro/final.kicad_pcb \
    --intent wk/gp14/02_sonde_xilinx/repro/intent_seat.json --allow-routed ; echo $?     # 0 errors, exit 4
```

**Existing issues.** None found for "NOT FULLY GRADED exit 4 pile budgets"; #1103 is the withholding itself.

## 6. route_planes replaces the designer's own GND pour with its defaults (solid pads, 0.1 mm min thickness), and the skill's Step 1 sends you there

**Tool / command.** `py_router/route_planes.py <board> <out> --nets GND --plane-layers B.Cu` on a board that
already carries a board-wide GND pour on B.Cu (the README calls board-wide pours design intent), as the
routing skill's Step 1 prescribes ("a bare pour", "do not set --thermal-relief").

**What it claimed.** `Note: Replacing existing zone on B.Cu for net 'GND' with new parameters` -- the
parameters are not listed.

**What was true (measured, input zone -> shipped zone).** clearance 0.508 -> 0.254; pad connection thermal
reliefs 0.508/0.508 -> solid (`connect_pads yes`), reliefs 0.2; `min_thickness` 0.254 -> 0.1; polygon
x 105.41..182.88 -> 103.5..183.5. On a hand-soldered through-hole board the solid connection is a real
change. The 0.1 mm min thickness is what lets the refilled pour form the two 0.1654 / 0.1111 mm necks the
verifier and `kicad_drc_compare` (staged min_connection 0.2032) found. Routing the same recipe WITHOUT
route_planes (designer zone kept) is also DONE with 0 vias, but at 539.94 mm vs 516.67 mm, so the shipped
board keeps the rewritten pour; the verifier also showed the shipped copper connects fully with the
input's zone settings restored. Cost: about 5 min (the verifier spent more).

**Repro.**
```bash
python3 -X utf8 py_router/route_planes.py wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb \
    wk/gp14/02_sonde_xilinx/repro/out/g6_planes.kicad_pcb --nets GND --plane-layers B.Cu    # "Replacing existing zone ... with new parameters"
grep -A12 '(zone$' wk/gp14/02_sonde_xilinx/repro/placed_s11.kicad_pcb | head -14          # input: clearance 0.508, min_thickness 0.254, thermal 0.508
grep -A12 '(zone$' wk/gp14/02_sonde_xilinx/repro/out/g6_planes.kicad_pcb | head -14        # output: connect_pads yes, clearance 0.254, min_thickness 0.1
```

**Existing issues.** "route_planes replacing existing zone", "thermal relief replaced zone",
"zone min_thickness connection_width": only #487 / #531 (closed, general) -- nothing on replacing a
designer's zone settings.

## Not a gap, noted for the record

- The shipped `final.kicad_pcb` carries zone OUTLINES with no `filled_polygon` (the repo's documented
  default, #910). `kicad-cli pcb drc` without `--refill-zones` reports 18 phantom GND opens; with a refill,
  0. `py_tools/fill_for_delivery.py` exists for an opt-in delivery fill; neither skill mentions it, and it
  was not run (the board must be refilled in KiCad before plotting).
