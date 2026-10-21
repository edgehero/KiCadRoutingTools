# gp14 grade notes (my independent re-grades vs the teammate's claim)

## 10 glasgow_revC (teammate: NOT DONE, blocking 7)
- My compare grade (staged intent.json, baseline = pile): blocking 8 = broken 6 + drc 1 + assembly 1; vias 869, copper 6115.67, segs 5831. Same copper numbers as the teammate.
- The +1 is check_assembly courtyard_blocking_gating on J5 <-> MK2 (4.0669 mm2). Both are DECLARED poses (mechanical.json),
  and the human board carries the same overlap (check_assembly on _truth/human_stripped: same pair, same 4.0669 mm2, buildable
  only because no --baseline arms moved-vs-baseline gating). The teammate waived the pair in intent_v3 -> buildable.
- Report as: blocking 7 (6 broken + 1 short C76 pad 2 / +3V3 via); the J5/MK2 gate is inherited from the declaration. -> FINDINGS_PREP #7.
- films: all rendered; place_movie and movie3d 0 of 264 differ; movie3d 214/264 models, 11 boxes; iso stills 213/224.
- GIFs over 3 MB: film.gif 6400 KB, film_andy.gif 4352 KB -> need a stronger fallback at asset build.
- measure: wall 2:43:32. fence CLEAN.

## 13 pico_ice_rev3 (teammate: NOT DONE, blocking 8)
- My compare grade agrees exactly: blocking 8 = broken 8; drc 0; vias 303, copper 2670.69, segs 2874; assembly buildable; floorplan 0.
- check_drc exit 0, check_connected exit 1 (8 pads). measure wall 1:20:23. fence CLEAN. iso 75/82 models.
- Teammate ran 6 placement rounds (r4-r6 after a PLACEMENT classification of the full route; skill silent on whether they count toward --rounds 3).
- First film pass: place_movie/movie3d differed in 78/97 because r5 used place_simple --decap-limit-weight 100, which films.sh did not pass.
  films.sh now takes CHOSEN.json "place_args" or FILM_PLACE_ARGS; re-filmed into _cmp/pico_ice_rev3/refilm/.
  teammate_prompt.md now asks for "place_args" (for boards launched after 00:10); the 4 running teammates were messaged the same ask.

## 14 imx6ulz_4l (teammate: NOT DONE by verifier; every machine gate DONE)
- teammate: blocking 0, check_complete DONE, kicad-cli DRC 0, DRAM_LDQ window met; vias 349, copper 3145.14, segs 2711.
- verifier FAIL on the spec lens: DDR3 pairs DQS0 skew 4.60 mm (0.57/21.08 mm coupled), CLK0 2.97 mm, DQS1 1.24 mm.
- My compare grade agrees exactly: done true, blocking 0, vias 349, copper 3145.14, segs 2711; check_complete DONE; check_connected 0; check_drc 0; iso 153/153; measure wall 3:03:01; fence CLEAN.
- first films pass died on a syntax error because I edited films.sh while bash was reading it; films re-run separately.
- So imx6ulz is the campaign's only machine-DONE so far among the hard boards; NOT DONE only by the verifier's DDR3 pair lens (no tool grades routed pairs).
- re-film OK: place_movie and movie3d 0/97 differ; refilm copied over, first pass kept in stale_first_pass/
- films re-run OK: place_movie and movie3d 0/159 differ. movie3d drew 130/159 from models, 25 boxes (U1, U2 BGAs + 23 resistors) while kicad_iso_render drew 153/153 -> evidence for FINDINGS_PREP #6. film.gif 4.8 MB (over 3 MB).

## 09 StickHub (teammate: NOT DONE, blocking 1)
- My compare grade agrees exactly: blocking 1 = broken 1 (/U7D- at U1.37); drc 0; vias 132, copper 773.42, segs 1147; buildable; floorplan 0.
- films all OK: place_movie and movie3d 0/90 differ (CHOSEN has place_args []); movie3d 70/90 models, 17 boxes (USB-A J2-J9, LEDs, U2, Y1) vs iso 93/93.
- measure wall 0:58:36. fence CLEAN.
- Notable: route.py GND plane repair ripped the routed +3.3V rail (17 pads, no copper) 3x; pad_pairs_open omits it; board_score blocking ties it with 1 stranded pad.

## 05 interf_u (teammate: DONE, verifier PASS)
- My compare grade agrees exactly: done true, blocking 0, vias 157, copper 4630.48, segs 1017; check_complete DONE AND --authored-from DONE (no floor relaxed); buildable; floorplan 0; check_connected 0; check_drc 0.
- control (human placement, one route.py pass) was blocking 2 -> the grouped flow beat the control here.
- films OK, 0/24 differ; movie3d boxes BUS1, P1, U9 (iso 21/23). measure wall 1:08:35. fence CLEAN.

## 07 One-Air-Max (teammate: DONE, verifier PASS -- graded on its own intent_gp.json)
- My compare grade on the GIVEN intent.json: done FALSE, blocking 1 = assembly 1 (NOT BUILDABLE): BAT1<->DC1 courtyard 38.71 mm2 and
  BAT1<->PWR_SW1 16.58 mm2, both COURTYARD-BLOCKING, gating because DC1/PWR_SW1 moved vs the pile. check_complete INCOMPLETE follows from it.
  Copper identical: vias 225, copper 2824.74, segs 1563; broken 0, drc 0; check_connected 0; check_drc 0.
- On the teammate's intent_gp.json (adds overlap_waivers BAT1/DC1, BAT1/PWR_SW1): buildable -> DONE.
- Unlike glasgow, the waived poses are the TEAMMATE's choice (DC1 and PWR_SW1 fixed_poses basis derived_default, not mechanical.json).
  BAT1 draws no courtyard; its occupancy falls back to marking+pads. Human board: BAT1<->DC1 only a silk-body ADVISORY (11.6 mm2), no courtyard gate.
  -> table: "DONE on own waivers; NOT BUILDABLE on the given intent (2 BAT1 overlaps)". Disclose both.
- Workarounds to disclose: placed on fixed_nohole (BAT1 peg hole stripped by helpers/bat1_hole.py, restored after); helpers/dedupe_segments.py
  removed 54 stacked GND segments and is NOT in redo_commands.sh (a manifest replay does not reproduce final).
- films: place_movie and movie3d 0/204 differ. 3D: iso 1/198 models, movie3d 0/204: 193 models point at ${EASYEDA2KICAD}, 4 at C:\ paths
  (source project's private libs, not shipped) -> the 3D stills/film are boxes. Check what fa10 showed.
- measure wall 1:15:22. fence CLEAN.

## 06 rp2350_fpga_eensy_prePlane (teammate: DONE, verifier PASS)
- My compare grade agrees exactly: done true, blocking 0, vias 152, copper 995.18, segs 1059; check_complete DONE (authored UNSOUND:
  annular 0.1->0.05, min_hole_clearance 0.25->0.09); buildable; floorplan 0; check_connected 0; check_drc 0. fa10: done, 185 / 986.11.
- Placed with the teammate's helpers/place_simple_frame_fix.py (anneal overlap term skips container U8): stock place_simple marked
  all 12 r1 seeds illegal (U8 castellated half-holes "past the outline" + U8 frame rect counted as overlap). Disclose.
- First film pass: place_movie/movie3d 60/61 differ (stock placer). Re-filming with _staging/with_placer_patch.py applying the same patch.
- iso 51/60 models; movie3d 48/61, 12 boxes. measure wall 0:54:13. fence CLEAN.
- re-film with the teammate's placer patch: place_movie and movie3d 0/61 differ; copied over, first pass in stale_first_pass/. (Films of this board use the patched placer: disclose.)

## 08 CM5_MINIMA_3 (teammate: DONE, verifier PASS -- graded on its own intent_cm5.json + --impedance-nets)
- My compare grade on the GIVEN intent: done false, blocking 1 = assembly 1: Module301<->Module302 courtyard 14.58 mm2 (both DECLARED, one module
  drawn as two footprints sharing an origin) and H102<->J1 4.62 mm2 (H102 declared; J1 in the outline's NW notch). The human board has BOTH pairs
  (14.58 and 4.64 mm2), buildable only without a baseline. Same mechanism as glasgow -> FINDINGS_PREP #7 (2nd board).
  On intent_cm5.json (overlap_waivers for both): buildable. Copper identical: vias 217, copper 2962.33, segs 1794; broken 0, drc 0.
- Chain contains helpers/drop_zone.py and helpers/clean_copper.py (both recorded in redo_commands.sh) + env KICAD_PLANE_FRAGILITY_LAYERS.
- Not graded by DONE but measured: M.2 buck L701 31 mm from U702 SW pin, LX 0.1 mm wide for 29.5 mm; HDMI CK 21.5 mm / ETH TRD1 21.9 mm intra-pair skew.
- films OK: 0/84 differ. iso 63/77 models; movie3d 52/84, 20 boxes. measure wall 1:27:58. fence CLEAN. fa10: NOT, blocking 1, 232 vias.

## 04 multichannel_mixer (teammate: DONE, verifier PASS x2)
- My compare grade agrees exactly: done true, blocking 0, vias 70, copper 1964.22, segs 497; check_complete DONE and --authored-from DONE; buildable;
  floorplan 0; check_connected 0; check_drc 0. fa10: NOT, blocking 6, 198 / 3756.8. human 29 / 1959.3.
- Placement repair helper helpers/fix_body_overlaps.py (place_pose moves of courtyard-less electrolytics) -- recorded as CHOSEN "after" moves.
- 3D: 0/21 models -- the board names only 21 models (16 Alps RK09K pots, 5 Neutrik jacks) and KiCad 10's mac library has neither; the 81 SMD parts
  name none. Stills/3D film are boxes. films OK, 0/114 differ. measure wall 1:17:50. fence CLEAN.

## 12 steppenprobe (in progress)
- Candidate final at 20:43Z: board_score blocking 0, check_complete DONE, 110 vias / 967.86 mm / 696 segs; verifier_1 FAIL: declared Power netclass
  (0.3 mm) not met on 6 of 8 nets (+1V8, Vdrive routed at 0.25; /VPHY /VPLL at 0.15; GND/+3V3 necks).
- STALL: its 20:46Z Bash call never ran (no widths.json / expP1 created) for ~2 h; stopped + resumed 00:44Z. Subtract the stall when reporting wall time.
- FINISHED: NOT DONE, blocking 5 (net_widths only: Power class 0.3 mm, 5 of 8 nets neck to 0.15 at U1, 29.0 mm; 20.6 mm widenable in place).
  110 vias, 962.4 mm, 693 segs; broken 0, drc 0. verifier_1 and verifier_2 FAIL (widths only). Active time ~1 h 03 m (+ ~4 h stall incl. the 2 h before resume... measure wall 4:59).
- STAGING DEFECT (ours, via the writer bug FINDINGS_PREP #8): the staged pile had 54 footprints with pads turned against their bodies. Only this board.
- My compare grade (campaign standard, same flags as every board: no --net-min-widths): done TRUE, blocking 0, 110 / 962.4 / 693,
  check_complete DONE, --authored-from DONE, buildable. The teammate's NOT DONE comes from grading the project's Power netclass widths
  (--net-min-widths widths.json, 0.3 mm), which the standard grade does not do on ANY board. Table: "DONE on the standard grade; blocking 5 with
  the declared Power-class widths". TODO phase 3: grade every board's declared netclass widths the same way (one extra column).
- films OK: 0/84 differ (r2/fixed is the normalized pile). iso 75/75; movie3d 75/84 (3 FID boxes). measure wall 5:00:47 (other_tool 15711 s = the stall).

## Declared non-Default net-class widths (supplementary; KiCad DRC does not enforce them) -- _staging/class_widths.py
    complex_hierarchy  final  nets under: 0 mm under: 0 narrowest: -
    complex_hierarchy  human  nets under: 0 mm under: 0 narrowest: -
    interf_u           final  nets under: 1 mm under: 59.7 narrowest: 0.2
    interf_u           human  nets under: 2 mm under: 34.9 narrowest: 0.381
    glasgow_revC       final  nets under: 7 mm under: 213.3 narrowest: 0.0998
    glasgow_revC       human  nets under: 6 mm under: 45.4 narrowest: 0.15
    steppenprobe       final  nets under: 5 mm under: 29.0 narrowest: 0.15
    steppenprobe       human  nets under: 7 mm under: 102.6 narrowest: 0.15
    -> the human boards miss their own declared Power-class widths too (steppenprobe human: 7 of 8 nets, 102.6 mm under). steppenprobe's verifier FAIL on widths is stricter than the human design.
