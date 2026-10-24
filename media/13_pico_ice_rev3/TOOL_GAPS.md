# TOOL_GAPS -- board 13 pico_ice_rev3 (`/plan-pcb-placement full`), ranked by what each cost this run

All repro commands run from WT (`~/Documents/git/krt-gpm`) with the venv python (`python3 -X utf8`).
Their inputs are under `wk/gpm/13_pico_ice_rev3/repro/` or in this folder.

## 1. The routed USB pairs wall in the last nets, and naming one EXACTLY in --rip-existing-nets unprotects it in the main pass only

- **Tool / command:** `py_router/route.py ... --nets '/~{ICE_RST}' '+3V3' 'GND' --rip-existing-nets '/USB_N' '/USB_P' '/LED_R' ... <arm-E flags>` (explore_E/lap2.sh). This is the override the router's own Hint prescribes: "override deliberately by naming the net EXACTLY (no glob) in --rip-existing-nets". The routing skill's #521 text says the same.
- **Claimed:** the exact name lifts #521 protection for that net in this run.
- **True (explore_E/lap2.log):**
  - Line 32, main pass: `10 pre-existing net(s) eligible for rip-up: /QSPI_SD3, /USB_P, ... /USB_N`.
  - Line 336, the in-run plane finalize: `4 PROTECTED net(s) excluded from blocker rip-up (/USB_D+, /USB_D-, /USB_N, /USB_P)`.
  - Line 387, its nested sub-run: `3 PROTECTED net(s) excluded from pre-existing rip candidacy (diff-pair: /USB_D+, /USB_P, /USB_N) -- name a net exactly (no glob) to override`, although they had been named exactly.
  - The decisive failure was a plane tap (lap1.log line 320: `Pad C12.1 ... blocked by /USB_P (protected, cannot rip)`), which is exactly the stage that ignores the override.
  - Every failure Hint keeps printing "PROTECTED net(s) '/USB_P' ... The router will NEVER rip these", even for nets the run had made eligible.
  - `--rip-existing-nets` alone never rips a CONNECTED net (lap1.log line 20, #515); `--force-reroute` does, and lap 3 used it.
  - The three nets the shipped board still has open (+3V3 at C12.1, /LED_R at U6.41, /~{ICE_RST} at U3.39) are all PASSABLE on the placement and CAGED only with the routing in place. Their hints name the USB pair copper (/USB_D-, /USB_P, /USB_N) as the wall. Five scoped laps moved none of them.
- **Repro:** `bash wk/gpm/13_pico_ice_rev3/explore_E/lap2.sh > /tmp/lap2.log 2>&1; grep -n "PROTECTED\|eligible for rip-up" /tmp/lap2.log` (reads explore_E/6_lap1.kicad_pcb; ~3 min; it writes explore_E/7_lap2.kicad_pcb again, deterministically).
- **Existing issues:** #677 (OPEN, "A diff pair from an earlier step can wall in later signal nets") is the phenomenon. No issue names the half-honoured override (searches "rip-existing-nets protected override", "PROTECTED excluded blocker rip-up finalize", "521 override plane finalize", "protected diff pair plane tap").
- **Cost:** the board ships NOT DONE on these 3 nets; ~45 min of laps and arms (laps 1-5, v2/v2E, FF).

## 2. fill_for_delivery's KiCad 10 re-save turns 113 accepted vias-in-paste into 113 DRC violations, and blocks the repo's own Type VII stamper (helper written)

- **Tool / command:** `python3 -X utf8 py_tools/fill_for_delivery.py labelled.kicad_pcb -o delivered.kicad_pcb` (SKILL §3.9 step 2).
- **Claimed:** "Filled ... net classes preserved: 1, unconnected (no --refill-zones): 84 -> 3", exit 0. Nothing about vias.
- **True (measured):**
  - The input is KiCad 8 format (`version 20240108`), whose vias carry no protection token (they inherit the board setup). The output is re-saved by KiCad 10's pcbnew as `version 20260206`, with `(capping no) (covering (front no) (back no)) (plugging (front no) (back no)) (filling no)` written on all 368 vias. Those values equal the board setup, so nothing changed physically.
  - check_drc on the input: `Vias in a solder-paste opening: 0 unprotected (violations) ... 113 undeclarable in this file format (accepted; Type VII belongs on the fab drawing)`.
  - On the output: `113 unprotected (violations)`, `FOUND 113 DRC VIOLATIONS: VIA-IN-PASTE`. board_score blocking went 3 -> 116 (`drc_via_in_paste` 113), on copper and fill that are identical.
  - The repo's own fix cannot apply either. `fab_notes.via_protection_stamps` treats a spec naming capping/filling as "Someone DECIDED ... kept, never overridden", and every via now names both.
  - `helpers/restamp_after_fill.py` removes only the setup-equal token groups (368 of 368) and calls `fab_notes.ship_via_protection_file` with the input's (empty) via snapshot. That is the function route.py runs at ship time. It stamped Type VII on 119 vias. check_drc then reads `0 unprotected, 113 filled+capped (accepted)`, `NO DRC VIOLATIONS`, board_score blocking 3, with fill blocks and segments identical.
  - The underlying fact, that the router put 119 vias in pads or paste openings, is a fab cost of its own: IPC-4761 Type VII.
- **Repro (from WT):** `python3 -X utf8 py_tools/fill_for_delivery.py wk/gpm/13_pico_ice_rev3/repro/labelled_v8.kicad_pcb -o /tmp/filled.kicad_pcb && head -c 60 /tmp/filled.kicad_pcb && python3 -X utf8 py_router/check_drc.py /tmp/filled.kicad_pcb --baseline wk/gpm/13_pico_ice_rev3/pico_ice_rev3.kicad_pcb --clearance-margin 0.1 | grep "Vias in a solder"` (compare the same check_drc line on `repro/labelled_v8.kicad_pcb`).
- **Existing issues:** related, not the same: #992 (closed, Type VII stamping on tool-added vias), #1232 (OPEN, via rings inside pad solder-mask openings), #910 / #1335 (closed, the delivery fill). Searches: "fill_for_delivery via-in-paste", "fill_for_delivery capping filling", "KiCad 10 resave via protection tokens", "via protection explicit no after save", "via-in-paste".
- **Cost:** ~15 min; without catching it the delivered board would have carried 113 DRC violations the routed board did not.

## 3. place_simple leaves ERROR-graded decap findings on 12 of 12 seeds; judge.json then ranks seeds by error COUNT

- **Tool / command:** `py_placer/place_simple.py fixed.kicad_pcb 's{seed}.kicad_pcb' --groups groups.json --intent intent_run.json --jobs 4 --json 's{seed}.json'` (skill defaults, 12 seeds).
- **Claimed:** it prices the intent's decap limits, which check_floorplan grades at error (`--decap-limit-weight` 10 per mm past the limit). judge.json names "the legal seeds of lowest cost, buildable and floorplan-clean first".
- **True (measured):**
  - All 12 seeds carry 3-19 floorplan errors, every one `decap_distance` / `decap_pin_distance` / `decap_ungraded`: s1 3, s8 4, s2 7, s9 7, s3 8, s5 8, s10 8, s0 9, s4 9, s6 10, s11 11, s7 19.
  - Each was a plain hand fix: s1 took 5 `place_pose set ... --near` moves, s4 took 7, and every move landed exactly where asked.
  - In s1, five of the core group's +3V3 decaps (C10, C16, C17, C19, C21) sat at y 80.7-87.1 beside U8/U6, 20-27 mm from their own IC U3 (y 107.6).
  - With no clean seed, judge.json ranked by error count. The anneal's cheapest seed (s4: cost 5341 vs s1's 6836, 955 crossings vs 1233, hpwl 1804 vs 1995 mm) was not among the 6 judged.
  - Hand-repaired and full-routed, s4 did route worse than s1 (blocking 18 vs 12 on one chain), so the miss cost a seed, not a placement.
- **Repro:** `python3 -X utf8 py_placer/place_simple.py wk/gpm/13_pico_ice_rev3/repro/pile.kicad_pcb 'wk/gpm/13_pico_ice_rev3/repro/p{seed}.kicad_pcb' --groups wk/gpm/13_pico_ice_rev3/repro/groups.json --intent wk/gpm/13_pico_ice_rev3/repro/intent_run.json --seeds 1,4 --jobs 2 --json 'wk/gpm/13_pico_ice_rev3/repro/p{seed}.json'` gives seed 1 cost 6835.7 with 3 errors and seed 4 cost 5341.5 with 9 (re-run at the end of this run: identical). Then `python3 -X utf8 py_tools/check_floorplan.py wk/gpm/13_pico_ice_rev3/repro/p1.kicad_pcb --intent wk/gpm/13_pico_ice_rev3/repro/intent_run.json | grep ERROR`.
- **Existing issues:** related, not the same: #1296 (closed, "Seed judge ranks and stops on placements with error-graded floorplan findings") and #1320 (closed, a decap limit wider than the tether radius). Searches: "place_simple decap limit", "decap_pin_distance seeds", "decap limit weight anneal", "every seed floorplan error".
- **Cost:** ~30 min (two hand repairs, one extra full-route arm).

## 4. check_weird calls a track end that sits inside a wide same-net track "free end, dangling"; deleting it split VBUS (helper written, result rejected)

- **Tool / command:** `python3 -X utf8 py_router/check_weird.py routed.kicad_pcb`, which check_complete reads as `weird_copper: not clean (exit 1)` and the verifier reported as a defect ("dangling/orphan copper on +3V3, VBUS, /USB_N").
- **Claimed:** `dangling-end: 9`, including `net VBUS (B.Cu) at (72.900, 124.525): free end, dangling segment 1.131mm (rooted at (73.700, 125.325))`, plus `kicad-dangling: 2`. `soft-joint: 0`.
- **True (measured):**
  - The "free end" (72.9, 124.525) lies 0.283 mm from the end (72.7, 124.725) of a 0.7 mm-wide VBUS track on the same layer, so inside that track's copper (half-width 0.35). That is a copper-overlap joint, which is either a soft joint or nothing, never a dangling end.
  - Deleting exactly the 11 reported segments (`helpers/delete_weird_segments.py`, one exact endpoint match per finding) split VBUS at PTC1: board_score blocking went 3 -> 5 (broken 3 -> 4, DRC 0 -> 1), and check_weird then reported 3 new dangling ends.
  - The deletion was rejected. The shipped board keeps all 11 pieces, some of which are therefore false findings.
  - Separately, route.py's own cleanup leaves the genuine stubs. A scoped re-run over `+3V3 GND VBUS /USB_N` (explore_E/clean.log) left all 11, and no repo tool removes dead copper. A first helper that walked the graph itself (`old/abandoned_helpers/prune_dangling.py`) chose 1327 segments and was abandoned unused.
- **Repro (from WT):** `python3 -X utf8 py_router/check_weird.py wk/gpm/13_pico_ice_rev3/routed.kicad_pcb | grep "VBUS (B.Cu) at (72.900"`, then `python3 -X utf8 py_router/check_connected.py wk/gpm/13_pico_ice_rev3/old/abandoned_helpers/7_pruned.kicad_pcb | grep -A3 VBUS` (the board with that segment removed: PTC1 disconnected).
- **Existing issues:** related, closed: #695 and #722 (check_weird crediting pads/vias by centre vs radius), #1063 (in-pad wiggles), #1166 (route.py never removes a dead branch). None covers a track end inside a wide same-net track. Searches: "check_weird dangling-end false", "dangling segment overlap wide track", "check_weird soft joint dangling", "orphan stub false positive".
- **Cost:** ~20 min, and the delivered board carries 11 weird-copper findings that check_complete counts.

## 5. SKILL §5 rule 3 ("three consecutive DIFFERENT approaches") read strictly would have shipped blocking 11; an arm already in flight reached 3

- **Step:** the stop rule, with parallel routing arms (allowed: up to 3 routing processes).
- **What happened:** after arm C (blocking 11), three arms in a row failed to lower it (s4 18, v2 14, D 11 tie). The rule fired when D finished at 11:02Z. Arm E (JLC-standard via 0.45/0.20, track 0.0889, grid 0.025) had been started at 10:54 and finished its first pass at 11:31 with blocking 7, then 3 after one iteration. The rule says nothing about arms in flight when it fires. I let them finish and report the reset openly.
- **Repro:** the ledger (`ledger.jsonl` rows 7-14) and STATE.md timestamps.
- **Existing issue:** none found ("stop rule consecutive approaches parallel").
- **Cost:** none in the end; it would have been 8 blocking nets.

## 6. analyze_power_paths overcounts current through regulators (2.0 mm for +3V3 and GND)

- **Tool / command:** `py_tools/analyze_power_paths.py` (`trace_power_paths`, `get_power_net_recommendations`), as `/analyze-power-nets` runs it.
- **Claimed:** `+3V3` 2.0 mm, `GND` 2.0 mm, `VBUS` 1.2 mm, `+1V2` 1.0 mm (IPC bands "under 5 A" / "under 2 A").
- **True:**
  - The board's whole input is one 350 mA polyfuse (PTC1, MF-FSMF035X) feeding two 300 mA LDOs, and the sinks sum to ~260 mA.
  - The tracer enumerates every sink-to-source path, including paths run BACKWARDS through a regulator, and sums them. `U1 -> U5 via /+3V3_STDBY -> +3V3 -> VBUS -> +1V2 (D4, U4, U1)` credits the 1.2 V LDO as the 3.3 V PSRAM's source.
  - One sink is counted once per path: 5 paths for U5, 5 for U2, 15 for U6.
- **Repro:** `python3 -X utf8 wk/gpm/13_pico_ice_rev3/repro/power_paths_repro.py` (prints every path and the recommendation dict).
- **Existing issue:** none found ("analyze_power_paths current", "trace_power_paths", "power nets width overcount", "analyze-power-nets").
- **Cost:** ~10 min; widths re-derived by hand from the IPC table.

## 7. No tool proposes a hand join; check_join only verifies one (helper written)

- **Tool:** `py_tools/check_join.py` (SKILL §4 "Hand-written copper").
- **What was needed:** where a via could stand beside a stranded pad.
  - check_join verifies a polyline the caller already chose (1.3 s a call). My first guess for +3V3 at C12 hit /ICE_9, /ICE_23 and /ICE_11 on three layers.
  - `helpers/free_via_sites.py` lists via sites that clear every foreign track, via and pad on all layers. It found 0 within 2.5 mm of C12.1, even for a 0.25 via, and 4524 in an empty patch (the sanity check).
  - So hand joins were ruled out by measurement.
- **Repro:** `python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/free_via_sites.py wk/gpm/13_pico_ice_rev3/explore_E/9_lap4.kicad_pcb '+3V3' 73.43 99.74 --radius 2.5`.
- **Existing issue:** none found ("check_join propose", "hand join via site").
- **Cost:** ~15 min.

## 8. No tool ranks a chip's quarter turns by escape facing (helper written)

- **Tool:** none at the placement door (`krt_registry.py --door placement`). `board_context`'s pin-order rows read CROSSED for 158 of 345 rows (rail pairs included) without saying which rotation would help.
- **What was needed:** whether a quarter turn of U3 or U6 would free the stranded pads on their rows.
  - `helpers/rot_probe.py` counts, per rotation, the signal pins whose nearest partner lies behind their own side.
  - U3 rot 0 had 21 (best), U6 rot 90 had 12 (best). So the anneal's turns were already the best, and the lever was elsewhere.
  - Its transform was checked against the parser's pad positions on both faces (error 0.000).
- **Repro:** `python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/rot_probe.py wk/gpm/13_pico_ice_rev3/final.kicad_pcb U3 U6`.
- **Existing issue:** #1191 (closed) names a `rank_rotations` tool that does not ship in this checkout.
- **Cost:** ~10 min.

## 9. Skill/environment: the datasheet PDF could not be opened the way the skill says

- **Step:** SKILL §3.5 "download it ... open it with the Read tool and pages", and "Where poppler is installed: pdftotext / pdftoppm".
- **True:**
  - No poppler on this machine, so the Read tool refuses every PDF ("pdftoppm is not installed").
  - LCSC's datasheet URLs return an HTML bot check to curl.
  - I got the HRO TYPE-C-31-M-12 drawing from JLCPCB's signed OSS link and rendered it with macOS `qlmanage -t` (`sips` clipped the rotated page). The skill names no fallback.
- **Repro:** `curl -sSL -o /tmp/x.pdf https://www.lcsc.com/datasheet/C165948.pdf; file /tmp/x.pdf` (HTML, not PDF).
- **Existing issue:** none found ("pdftoppm poppler datasheet").
- **Cost:** ~10 min.
