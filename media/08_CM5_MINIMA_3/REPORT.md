<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT.md content — fa10 board 08, CM5_MINIMA_3, `/pcb-free-agent full`

## 1. Result

Final board `final.kicad_pcb` + `final.kicad_pro`, sha256 `e7c7f02d262cdcd8a852083ded84d10ef1bea5554b0d126c2a4640c0d7927cfb`.

Graded with every spec the board declares:
- the intent `intent_cm5.json` (see section 3 for why it differs from the given one);
- `--impedance-nets` set to the project's 90/100-ohm netclass patterns: `/*USB_*` `/*PCIE*` `/*USB2*` `/*ETH_PI*` `/*HDMI_P*.D*` `/*DPHY0*` `/*HDMI_P*.CK*`;
- `--min-via-diameter 0.45 --min-via-drill 0.3`, the board's own via floor;
- `--baseline CM5_MINIMA_3.kicad_pcb`.

| DONE condition | required | measured | met |
|---|---|---|---|
| board_score blocking | 0 | **42** | no |
| unrouted | 0 | 0 | yes |
| broken | 0 | 0 | yes |
| check_complete (spec flags) | DONE | INCOMPLETE, blocking 42 | no |
| check_connected | all connected | ALL NETS FULLY CONNECTED (95 nets) | yes |
| check_drc at the authored rules | 0 | NO DRC VIOLATIONS | yes |
| check_floorplan | 0 errors | 0 errors, 3 warnings (decaps outside the 5 mm search radius, not graded) | yes |
| check_assembly | buildable | NOT BUILDABLE; the only failing check is `coincident_origins` = 1 | no |
| check_complete's extra instruments | clean | orphan stubs 0, pad overlaps clean, weird copper clean | yes |

**blocking_by:** unrouted 0, broken 0, drc 0, undersized 0, floorplan 0, assembly **1**, impedance **41**. `length` and `net_widths` are ungraded because the project declares no length groups and no power-width spec.

**Quality:** vias 232, copper 2348.77 mm, 2005 segments. `grade.py` (`grade/grade_final.json`) independently gives the same numbers on the same sha.

**Against the given `intent.json`:** check_floorplan finds 0 errors. check_assembly adds 8 courtyard overlaps; each is waived in `intent_cm5.json` with its measurement (section 3).

## 2. Stop rule, and every remaining blocker

**Rule that fired:** "If DONE will not come". The best board was r4d at 14:19Z (blocking 42). After it, three consecutive different approaches failed to lower blocking:
- **r5**, a re-placement (U405 nudge) plus a 0.25 mm DPHY pair gap: blocking 45, broken 3.
- **r6**, a scoped lap on the 23 impedance nets with inner-plane crossings: no change, because route.py skips nets that are already connected.
- **r6b**, a `--force-reroute` of those 23 nets on F/B only: 5 failed, 6 nets broken, rejected by route.py's improvement gate.

Both remaining blockers are also unreachable by construction:

1. **Assembly 1: Module301 and Module302 share an origin at (127.25, 77.6).**
   - `mechanical.json` declares both CM5 connector footprints at that exact pose. They share the module origin by library design; their pads are 34 mm apart.
   - `check_assembly` fails any two non-marker parts at one origin, and that check reads no waiver of any kind (G1).
   - So every board that honours the declaration is NOT BUILDABLE.
2. **Impedance 41: every impedance net's own via counts as a reference-plane void.**
   - 42 nets match the declared patterns. 41 carry a via, and every one must change layers: the CM5 pads are on B.Cu and all their partner connectors are on F.Cu.
   - All 41 have a crossing at their own via. A 0.45 mm via at the 0.2 mm class clearance has a 0.425 mm antipad; a P/N pair's two antipads merge. check_impedance ignores only voids shorter than a fixed 0.30 mm and never exempts the trace's own via (G6).
   - No net has only non-own crossings, so the count equals the number of via-bearing nets for any routing. Verifier 2's decomposition agrees: 237 of 296 void crossings sit at the net's own via.
   - One of the 41, `/PCIe-M2/M2_LX` (the buck's switch node), only matches `/*PCIE*` because net patterns are case-insensitive on Windows (G10). On Linux/macOS the count would be 40.
   - The 41 nets: DPHY0 C/D0-D3 (10), ETH TRD0-3 (8), HDMI CK/D0-D2 (8), PCIe CLK/RX/TX (6), PCIe PWR_EN, nCLKREQ, nRST, nWAKE, USB2P.D_N/P, USB_C.D_N/P, and /PCIe-M2/M2_LX.

## 3. Intent used, and why

`intent_cm5.json` is the given `intent.json` (unchanged; its sha256 was re-checked) with four additions.

**Overlap waivers (8 pairs), each with its measurement:**
- Module301/Module302: the declared shared origin.
- H102/J1, 2.87 mm². J1 (the RJ45) can only sit in the outline's notch, and its courtyard corner then overlaps the corner mounting hole's courtyard. Their copper is 3.4 mm apart.
- J503, L701 and J601, each against Module301 and Module302 (six pairs). These are phantom overlaps: `check_assembly` gives each B-side connector an F-side "courtyard" equal to the bounding box of its two NPTH mount holes, 48 mm apart (G2).

**Keep-outs:**
- The drawn bodies of four parts that have no courtyard: USB701, J101 (its silk outline), SW501 and SW101.
- `m2-card`: under the M.2 2230/2242 card, only low-profile parts are allowed (passives except the 2.1 mm tantalum C702, diodes/LEDs, small ICs, test points).
- Three F-side via corridors over the CM5 pin columns. I added these after r1 showed F-side parts sitting on top of the columns and boxing in the escape vias.

**A decap limit:** `decaps.max_distance_mm` 3.8. This is the source decap census the given intent already carries (19 tethers, max 3.79 mm). The intent generator withheld it only because it read the declared module pair as a pile (G5).

## 4. Floors

- **No authored floor is relaxed.**
  - `check_complete --authored-from` lists nothing as relaxed. The one floor it can't measure, copper-to-hole 0.2, is the one check_drc graded at 0.2 and found clean.
  - The pour step had written `min_hole_clearance` down to 0.13 in the project; I restored 0.2 in `final.kicad_pro`.
  - All netclasses are identical to the authored ones, and all 232 vias measure 0.45/0.3.
- **Clearance was held at 0.13 by a fab-overrides file** (`fab_overrides_board.txt`). In r1, a single GND rescue at 0.1 mm had silently lowered the Default class to 0.1 for the whole board (G8, issue #1160).
- **Track widths:** signals were requested at 0.1 mm; netclass widths are drawing defaults, not DRC floors.
  - route.py's `Design rules` lines for the final chain:
    - r3: `80 feature(s) on 34 net(s) delivered below the requested size (smallest track width 0.0889 mm)`.
    - r4b lap: `15 feature(s) on 8 net(s)`, smallest 0.1 mm.
    - r4d lap: `6 feature(s) on 3 net(s)`, smallest 0.1 mm.
  - 0.0889 mm is the 6-layer standard-tier floor; the board's own minimum is 0.
- **Power widths are requests, and some copper shipped under them** (r3): GND 21.0 of 21.0 mm of tap traces under 0.3; HDMI_+5V 9.1 of 24.6 mm under 0.25; +3V3_PI 7.9 of 105.9 under 0.25; +5V 4.4 of 34.4 under 0.4; VBUS_USB2.0 1.4 of 30.7 under 0.4; M2_3V3 7.4 of 44.2 under 0.3. No power-width spec is declared.
- **Edge clearance at the RJ45 tabs:** J1.15 and J1.16 sit 0.204 mm from the notch's edges, against the 0.372 mm floor. This is forced: the notch is 15.79 mm wide and the tabs' inner gap is 16.2 mm. KiCad's DRC reports both; the default check_drc does not (G14).
- **Zones are stored unfilled** and must be refilled before fab output (noted by verifier 2).

## 5. Timeline (UTC)

| time | event |
|---|---|
| 10:02 | FIRST_CMD; board_brief: a pile of 112 parts, 221 nets, 6 layers |
| 10:16 | Fixed parts and first connector frame placed, against the outline's bounding box (G3) |
| 10:30 | Real outline found (RJ45 notch, corner ears); connector frame redone |
| 11:06 | **First legal placement**, b04_seedA: 0 grade errors, 0 unseated |
| 11:40 | **First fully routed board**, r1: blocking 107 |
| 12:04 | Re-placement with via corridors and in-line ESD parts |
| 12:24 | r2t: blocking 46 |
| 12:52 | r3: blocking 46, broken 1 |
| 12:53-13:53 | A pair of board_score runs took 61 min (G12) |
| 14:19 | **Best board**, r4d: blocking 42, every non-structural term at 0 |
| 14:22-14:40 | r5, r6 and r6b fail to lower it; stop rule fires |
| 14:47 | Final v1 frozen; DONE never reached |
| 14:48-14:58 | Verifier call 1: FAIL. KiCad flags a C709/C710 courtyard graze that my own decap nudge created |
| 15:06 | Final v2 frozen with C709 moved 0.1 mm |
| 15:02-15:12 | Verifier call 2: FAIL on the spec lens only |
| 15:14 | Ledger closed (stop condition 4) |
| 15:15 | Film made |

## 6. Where the time went

`measure.py` on this agent's transcript: 5h13m of wall clock.
- 2h28m waiting on background jobs.
- 1h40m other (foreground) tool time, which includes the 61-minute board_score stall.
- 1h06m model time.

That came to 336 tool calls and 2 verifier spawns, with `forbidden_uses: []`.

## 7. What worked and what did not

**Worked:**
- Placing the edge parts by hand on the real outline, then `place_seed --force`: 69 parts seated with 0 grade errors in about 8 minutes.
- F-side via corridors over the CM5 pin columns, plus HDMI ESD parts (D401/D402) placed in line between J501 and J101 so their pin order matches J501's: blocking 107 to 46-48.
- `route_diff --no-gnd-vias`: drc 63 to 2. 61 of those errors were route_diff's own GND return vias (G7).
- The 0.13 mm clearance floor file: no more class rewrite.
- The routing skill's tuned environment settings: on identical input, blocking 46 against 48 and 228 vias against 241.
- Hand-placed GND links for the ESD parts' centre GND pads (checked with `check_join`, then locked): D402's GND went from broken to connected.
- One hand-placed GND via inside Module302's pin column, plus deleting a 4-segment GND tap that walled in the PCIe clock pair: broken 1 to 0. Three rip-and-reroute laps before that had only traded CLK_P and CLK_N between broken and connected (G11).
- Ending two DPHY0 D1_N segments on their via centre: drc 2 to 0.
- Moving C709 by 0.1 mm: cleared the KiCad courtyard error that verifier 1 found.

**Did not work:**
- Diff pairs on F/B only (r3fb): impedance stayed at 41, copper went up 300 mm, GND broke.
- Forced F/B re-route of the 23 nets (r6b): rejected by route.py's gate.
- r5: blocking 45.
- `--decap-claim-after-ics`: 9 extra caps claimed, but 2 decap errors either way.
- `place_seed --repair-decaps`: declined both small overruns as "disproportionate".

## 8. Tool gaps

`TOOL_GAPS.md` has 14 entries ranked by what each cost this run, each with a reproduction command and an issue search:

| rank | gap | issue |
|---|---|---|
| 1 | G6 check_impedance counts each net's own via antipad as a void | — |
| 2 | G1 unwaivable coincident-origin check | — |
| 3 | G12 61-minute board_score with no timing | — |
| 4 | G11 rip laps trade one diff-pair leg for the other | — |
| 5 | G3 board_brief/render_placement show the outline's bounding box | — |
| 6 | G2 phantom NPTH-strip courtyard | — |
| 7 | G7 route_diff GND vias inside the pair's class clearance | — |
| 8 | G8 silent clearance ratchet | #1160 |
| 9 | G14 default check_drc skips pad-to-edge on routed boards | — |
| 10 | G10 Windows-only case-insensitive net patterns | — |
| 11 | G9 snap advice that repeats a refused pose | — |
| 12 | G4 place_seed refuses once fixed parts are locked | #1165 family |
| 13 | G5 decap budget withheld | — |
| 14 | G13 floorplan exit 4 on 0 errors | — |

Helper scripts I had to write are listed in `TOOL_GAPS.md` with why each was needed: `fp_geom`, `seedsum`, the chain/lap scripts, `lock_copper` and `edit_copper`.

## 9. Verifier verdicts

- **`verdict_1.txt`: FAIL.**
  - Blocking 42, and check_complete INCOMPLETE.
  - The coincident origin.
  - The forced J1.15/J1.16 edge clearance (seen with `--check-pad-edge` and in KiCad's DRC).
  - KiCad courtyard errors H102/J1 (forced) and C709/C710. C709/C710 was my defect, and it is fixed in v2.
  - Lens files: connectivity PASS, drc FAIL (J1 edge), spec FAIL.
- **`verdict_2.txt`: FAIL** on the spec lens only (evidence 42).
  - Connectivity PASS and drc PASS; mechanical poses 10/10 exact; no gating copper off the outline.
  - Informational findings: 92 of 104 impedance-net vias have no GND return via within 2 mm; P/N copper skew up to 14.5 mm on ETH TRD2; zones stored unfilled.
