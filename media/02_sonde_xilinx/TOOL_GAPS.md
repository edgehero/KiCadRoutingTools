# TOOL_GAPS -- gpm board 02 (sonde_xilinx)

Ranked by what each cost this run. No helper scripts were written (`helpers/` is empty).
Every repro command runs from WT (`~/Documents/git/krt-gpm`) with the venv on PATH
(`export PATH="$HOME/.venvs/krt/bin:$PATH"`); its inputs are in `wk/gpm/02_sonde_xilinx/repro/`.

---

## 1. Edge-mount DSUB depth: the footprint's own "PCB edge" marker is read by nothing, a wrong depth grades `pass`, and SKILL §3.4's "an overhang of x reads x" is false for a part longer than its edge

**Cost:** about 15 min: measuring the right seat by hand, writing `overhang_mm` bands into `intent_run.json`, and two scratch placements to prove what happens without them.

**Tool / command:** `place_simple.py` edge seat (`placement/edge_seat.py`) and `check_floorplan.py`'s `edge_connector` rule, on the intent compiled from the design brief (`edge` only, no `overhang_mm`).

**What it claimed:**
- *J2 (DSUB-9 edge mount, east edge, bottom side):* `NOTE: edge connector J2 on the east edge, facing it`. Then check_floorplan reads `J2 east: overhang 4.1645mm ... pass; pad copper 5.3022mm vs 0.2mm pass; facing east ... pass`, and check_assembly says buildable.
- *J1 (DSUB-25, west edge):* `WARNING: J1 ... has no seat there (... its courtyard is 54.10mm along a 43.18mm edge; declare overhang_mm.min at the reading where its mating face meets the edge); placed as any other part`. That warning is correct and useful. The seed then carries 2 `edge_connector` errors.
- *SKILL.md §3.4:* "write that distance [how far the part reaches past the edge] as `overhang_mm.min` ... an overhang of x reads x".

**What was true (measured):**
- Both footprints draw their mating geometry: a `Dwgs.User` line labelled "PCB edge" at local y = +1.99 mm (J1; -1.99 mm in J2's stored back-side block). The pads end at |y| = 1.74 mm. So an edge-mount DSUB is built with that line ON the board edge: its two pin rows straddle the PCB, with the pad copper 0.25 mm inside it.
- Without a band, J2 is seated with its pad copper **5.30 mm** inside the outline and its shell 4.16 mm past the edge. Such a connector cannot be fitted to the board, and every grader passes it.
- The band is read as the courtyard's overhang **summed over every side it crosses**. J1's courtyard (54.10 mm) is longer than the west edge (43.18 mm), so the reading at the correct seat is 14.20 (past the west edge) + 10.92 (past north and south) = **25.12 mm**.
- Following the skill literally (`overhang_mm.min` = 14.2, the real reach) seats J1 with its pad copper **2.51 mm** inside the edge instead of 0.245. check_floorplan grades that `pass` too.
- The seat that is right needed bands written by hand at the reading measured at the marker pose: J1 [25.12, 25.17] and J2 [14.20, 14.25]. With those, all 12 seeds seated both connectors at pad copper 0.245 mm, facing out.

**Reproduce (from WT):**
```bash
P=wk/gpm/02_sonde_xilinx/repro
# given intent: J1 unseated, J2 seated 5.30 mm deep and graded pass
python3 -X utf8 py_placer/place_simple.py $P/sonde_xilinx.kicad_pcb $P/out_given.kicad_pcb --groups $P/groups.json --intent $P/intent.json --seed 0
python3 -X utf8 py_tools/check_floorplan.py $P/out_given.kicad_pcb --intent $P/intent.json | grep -E "J1|J2"
# the skill's literal reading (min = real reach 14.2): J1 pads 2.51 mm inside, graded pass
python3 -X utf8 py_placer/place_simple.py $P/sonde_xilinx.kicad_pcb $P/out_literal.kicad_pcb --groups $P/groups.json --intent $P/intent_literal.json --seed 0
python3 -X utf8 py_tools/check_floorplan.py $P/out_literal.kicad_pcb --intent $P/intent_literal.json | grep -E "J1 west: overhang"
```

**Existing issues** (`gh issue list --repo drandyhaas/KiCadRoutingTools --state all --search ...`, keywords "edge mount overhang", "overhang band emitter 0", "DSUB edge", "edge connector seat depth", "edge mount straddle"):
- #1155 (closed) "A reversed edge-mount connector (shell lying over the board) passes edge_connector, check_assembly and board_score". Related, but a different defect: here the facing is right and the DEPTH is wrong.
- #1176 and #1242 (closed): DSUB classification and reseat facing. Not this.

No issue covers reading a footprint's "PCB edge" marker, or the corner-summed band for a part longer than its edge.

---

## 2. `analyze_power_paths.trace_power_paths` traces one sink per rail, so a pass-through part's current is under-counted

**Cost:** about 5 min (noticed in the report, then read the code). The widths did not change on this board.

**Tool / command:** `py_tools/analyze_power_paths.py`, `trace_power_paths()` (the `/analyze-power-nets` skill's Step 5).

**What it claimed:** `Path 1: J2 -> U1  Current: 22mA  Nets: VCC -> /PWR_3,3-5V  Via: D2`. That is the only traced path, with U1 and U2 both classified `CURRENT_SINK` at 22 mA.

**What was true:** U1 and U2 both take power from VCC, which is fed through D2 from /PWR_3,3-5V. So D2 and the input net carry at least 44 mA, as two paths. The cause is `sink_nets: Dict[int, str]`, keyed `net_id -> sink_ref`: the second sink on a net overwrites the first, so each rail is traced from one sink only. On this board the error stays under the 50 mA threshold, so no width moved. On a board whose rail feeds several ICs through a fuse, diode or ferrite, the input path is undersized by a factor of the sink count, silently.

**Reproduce (from WT):**
```bash
python3 -X utf8 -c "
import sys; sys.path[:0]=['py_tools','py_router']
from analyze_power_paths import *
c,p=analyze_pcb('wk/gpm/02_sonde_xilinx/repro/final.kicad_pcb')
classify_component(c,'J2',ComponentRole.POWER_SOURCE,current_rating_ma=100)
classify_component(c,'D2',ComponentRole.PASS_THROUGH,current_rating_ma=150)
classify_component(c,'U1',ComponentRole.CURRENT_SINK,current_rating_ma=22)
classify_component(c,'U2',ComponentRole.CURRENT_SINK,current_rating_ma=22)
paths=trace_power_paths(p,c); print(len(paths),[(x.sink_component,x.estimated_current_ma) for x in paths])"
# prints 1 path (one of U1/U2), expected 2
```

**Existing issues** (keywords "analyze_power_paths", "power paths sink", "power net width current sink"): none covers it.

---

## 3. `check_assembly` echo says "pad copper off-board" for pads 0.245 mm INSIDE the outline

**Cost:** about 3 min to resolve the contradiction with check_floorplan before trusting the board.

**Tool / command:** `python3 -X utf8 py_tools/check_assembly.py <board> --intent <intent> --baseline <input>`.

**What it claimed:** `pad/hole/oob echo: 0 pad pair(s), 0 hole conflict(s), 2 part(s) with pad copper off-board: J1 (0.009mm), J2 (0.009mm)`, with JSON `oob_pad_count 2`, `oob_pad_refs [["J1", 0.009], ["J2", 0.009]]`.

**What was true:** measured from the parsed pads, J1's pad copper spans x 103.545-107.025 against the west edge at 103.300, so it is **0.245 mm inside**. J2 spans 179.975-183.455 against the east edge at 183.700, also 0.245 mm inside. check_floorplan reads the same copper as `pad copper 0.2450mm vs 0.2mm pass`. The 0.009 mm is 0.254 (the netclass clearance) minus 0.245: the echo measures pad AABBs against the outline inflated by the grading clearance. `oob_pad_basis` says so, but the printed line says "off-board". It is not gating (`oob_pad_copper_gating_refs` is empty, verdict buildable). Two tools read the same pad against two different margins (0.254 here, 0.2 in check_floorplan), and one of them reports the result as off-board copper.

**Reproduce (from WT):**
```bash
P=wk/gpm/02_sonde_xilinx/repro
python3 -X utf8 py_tools/check_assembly.py $P/delivered.kicad_pcb --intent $P/intent_run.json --baseline $P/sonde_xilinx.kicad_pcb | grep off-board
python3 -X utf8 py_tools/check_floorplan.py $P/delivered.kicad_pcb --intent $P/intent_run.json --allow-routed | grep "pad copper"
```

**Existing issues** (keywords "oob_pad_refs", "check_assembly pad copper off-board", "pad copper off-board clearance"): #1193 (closed), "place_seed --repair charges a locked part on its pads' bounding box ... no pad is off the board". It has the same shape (a bounding-box reading reported as off-board) but sits in another tool. None covers this line.

---

## 4. No way to read a datasheet PDF on this machine; the maker's site refused the download

**Cost:** about 4 min here, because this board needed no §3.5 template, only two currents for analyze-power-nets. On a board with a switching stage it would block §3.5.

**Tool / command:** SKILL.md §3.5 step 2 (download the PDF and read it with the Read tool's `pages`; `pdftotext` / `pdftoppm` / `pdfimages` "where poppler is installed").

**What it claimed:** the skill's path is: WebFetch mangles a PDF, so `curl` it and open it with Read and `pages`.

**What was true:**
- `Read` on the downloaded TI PDF (`datasheets/sn74ls125a/sn74ls125a.pdf`, 1.5 MB) failed: "pdftoppm is not installed".
- `pdftotext` is absent, and neither `pypdf` nor `fitz` is in the venv.
- WebFetch on the PDF returned "a raw, compressed PDF file (FlateDecode streams) with no readable text".
- ST's `bat46.pdf` failed both ways: curl gave `HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR`, and WebFetch timed out at 60 s.
- The values used (74LS125 supply current max 22 mA, IOL 24 mA; BAT46 IF 150 mA) came from TI's HTML product page and from search results quoting ST-era datasheet copies, not from a datasheet page read directly.

**Reproduce (from WT):**
```bash
which pdftotext pdftoppm; python3 -c "import pypdf" ; python3 -c "import fitz"
curl -sSL -m 60 -A "Mozilla/5.0" -o /dev/null https://www.st.com/resource/en/datasheet/bat46.pdf; echo $?
```

**Existing issues** (keywords "pdftotext poppler", "datasheet pdf"): none.
