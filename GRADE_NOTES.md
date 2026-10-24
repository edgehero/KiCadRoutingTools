# gpm grade notes (my independent re-grades vs the teammate's claims)

## running observations
- 10 glasgow (11:4x): pass 1 rejected; pass 2 changed SW1's edge west->south in its run intent. (Resolved below: the given intent declares NO edge for SW1; the teammate added the claim.)
- 12 steppenprobe: experiment arm M used --no-fix-drc-settings (route_planes/route_diff/route). At grading, check that the shipped final_route/redo_commands.sh does not carry it (no fab_floor_origin means the floor integrity check cannot run).
- 14 imx6ulz: 3 placement passes (U1 P12 decap error in 11/12 seeds for passes 1-2; pass 3 added a run-intent proximity U8.2->U1.P12 of 7 mm). 13 pico: all 12 seeds with decap errors; s1 hand-repaired (5 moves). 12 steppenprobe: 3 of 6 judged seeds carry decap errors. A likely cross-board finding: place_simple does not meet the decap limits it grades.
- 10 glasgow: its verifier ran check_drc with --clearance-margin (verify_scratch/check_drc.txt). My compare runs check_drc with no margin; compare the two counts.
- 20 sam9g25: the teammate pip-installed PyMuPDF (+onnxruntime etc., 249 MB) into helpers/pylib to read datasheet PDFs for §3.5 templates (helpers/pdftool.py). The skill asks for datasheet figures; the repo has no PDF reader. Exclude helpers/pylib from assets.

## 10 glasgow_revC (teammate: DONE, verifier PASS) -- gp14: NOT DONE, blocking 7; control on main: blocking 13
- **My compare grade agrees exactly.** On the GIVEN intent and on intent_run.json: done true, blocking 0 (joins 0), 763 vias,
  4956.46 mm of copper, 4837 segments. check_complete DONE; check_complete_authored UNSOUND, which is the floors
  disclosure. buildable, floorplan 0, check_connected 0, check_drc 0 with no margin (the verifier used
  --clearance-margin 0.1, and it makes no difference here).
- **SW1's edge.** The given brief and intent declare no edge for SW1; derive_decl did not claim it. The teammate ADDED
  `edge_connectors` SW1 south, band 0.27-0.30, in intent_run.json, its own §3.4 judgment: the board's edge keep-out is
  notched only at J1 and at x 71.7-77.6 on the south edge. Its first draft said west. Nothing declared was overridden.
- **Floors:** routed at 0.09 clearance, 0.0889 track and 0.25/0.15 vias (JLC advanced), against the board's own
  0.1499 / 0.15 / 0.4. 356 vias are Type VII via-in-pad. At the board's own 0.1499 the copper has 2540 violations.
  This is the headline caveat.
- iso 213/224. measure wall 1:51:14, model 41 min, tools 17 min, waiting 53 min. fence CLEAN. Repo untouched.
- **film_seed:** 1 of 264 differs, C92 (0.35 mm). That is the hand repair in CHOSEN "after", so the film reproduces
  place_simple exactly.
- **film_flow:** first pass SKIPPED, because the run judged only s5 (skill §3.6 case 2) and film_work expected 6
  judged seeds. film_work now auto-judges the seeds the run fast-routed. Re-run OK with --judge 1: 1125 frames,
  best = kept = s5, full route = final_route/7_final. The GIFs (film_seed 3.3 MB, film_flow 4.3 MB) are over 3 MB and
  need a stronger pass at asset build.
- **TOOL_GAPS:** 12. The top 3 are fill_for_delivery's KiCad 10 re-save (356 via-in-paste), place_simple decap
  near-misses in every seed, and the cap pass breaking C78 and stranding a stub.

## 12 steppenprobe (teammate: DONE, verifier PASS on call 2) -- gp14: DONE by the machine, verifier FAIL (Power widths); control on main: blocking 0, INCOMPLETE
- **My compare grade agrees exactly:** done true, blocking 0, 140 vias, 1323.85 mm, 877 segments. check_complete DONE AND
  authored DONE (no floor relaxed: the shipped chain runs --no-fix-drc-settings to keep min_hole_clearance 0.25, its
  TOOL_GAPS #2). buildable, floorplan 0, connected, check_drc 0.
- **The Power class (0.3 mm) is met.** All 411 power segments are >= 0.3 mm, graded through the teammate's own
  power_min_widths.json; gp14 shipped necks. The cost is 140 vias / 1324 mm, against gp14's 110 / 962 and the human's
  79 / 1233.
- **The pile was correct this time** (#1305); gp14 started from a damaged one.
- **USB pair:** coupled by route_diff, then re-routed single-ended by later steps. It is ungraded because no diff
  class is declared (TOOL_GAPS #4).
- **film_seed:** 0 of 84 parts differ. **film_flow:** SKIPPED, correctly. The run kept s2 although the quick judge
  ranked s1 first: the teammate full-routed all three judged seeds and s2 routed best (142 vias against 147, s3
  blocking 1; TOOL_GAPS #11). A flow film would label s1 as the best.
- iso 75/75. measure wall 2:06:30, model 56 min, tools 32 min, waiting 39 min. fence CLEAN.

## 06 rp2350_fpga_eensy_prePlane (teammate: DONE, verifier PASS) -- gp14: DONE, verifier PASS, but with a teammate-patched placer; control on main: blocking 9
- **My compare grade agrees exactly:** done true, blocking 0, 173 vias, 929.26 mm, 1068 segments. check_complete DONE;
  authored UNSOUND (the annular ring 0.1 -> 0.05 with the board's own 0.25/0.15 via; min_hole_clearance 0.25 -> 0.09
  from the FPGA fanout's writeback). Buildable, floorplan 0, connected, check_drc 0. 116 vias in pads, Type VII.
- **Stock main, no placer patch** (gp14 needed helpers/place_simple_frame_fix.py). Every seed carried a decap_distance
  error; s9 was repaired by hand (C17, three moves), the rest per §3.6 case 2.
- **Templates for U7 (TPS62162) and U6 (RP2354A regulator)**, with drift 0.60 / 0.00 mm. A PDF helper
  (helpers/pdftool.swift) was needed, because the machine has no poppler.
- iso 51/60. measure wall 0:41:39. fence CLEAN.
- **Films.** film_seed: 1 of 61 differs (C17, hand). film_flow: first pass skipped, because the run routed
  9,6,2,7,4 (s3 could not be repaired). film_work now films the covering prefix with s3 noted as skipped. Re-run OK: judge 6, best = kept = s9, 779 frames, both GIFs 2.3 MB.

## 09 StickHub (teammate: DONE, verifier PASS) -- gp14: NOT DONE, blocking 1; control on main: blocking 0, INCOMPLETE
- **My compare grade agrees exactly:** done true, blocking 0, 133 vias, 907.16 mm, 1234 segments. check_complete DONE;
  authored UNSOUND (track 0.15 -> 0.1, via 0.5 -> 0.25, hole 0.25 -> 0.15, clearance 0.15 -> 0.1: JLC advanced).
  Buildable, floorplan 0, connected, check_drc 0. 60 Type VII vias.
- **Placement took 3 passes.** Pass 1: a classless edge row (C38) ignored by place_simple but graded ERROR by
  check_floorplan. Pass 2: decap errors on a different pin in every seed. Pass 3 used --decap-limit-weight 40
  --near-weight 10 (CHOSEN place_args). One hand join, through check_join.
- **Caveat: power widths are not declared and shipped thin** (the upstream VBUS path is about 30 mm at 0.1 mm).
- iso 93/93. measure wall 1:12:28. fence CLEAN.
- **Films:** film_seed 0 of 90 differ; film_flow OK (judge 2: s10 + s3, best = kept = s10, 1069 frames).
- 20 sam9g25: experiment arm rM passes --fab-overrides (a fab-floor file). At grading, check whether the shipped chain carries it, and what floor it declares.

## 20 sam9g25 (teammate: DONE, verifier PASS on call 2) -- gp14: not run; control on main: blocking 22
- **My compare grade agrees exactly:** done true, blocking 0, 355 vias, 4076.04 mm, 2491 segments. check_complete DONE;
  authored UNSOUND (via 0.4 -> 0.25, annular 0.075 -> 0.05, hole 0.3 -> 0.15, Default clearance 0.195 -> 0.0987; the
  track 0.1016 is held). Buildable, floorplan 0, connected, check_drc 0. 101 Type VII vias.
- **The shipped chain passes --fab-overrides helpers/fab_track_floor.txt** (track 0.1016, via 0.25/0.15, clearance
  0.09). It holds the board's courtyard-scoped .kicad_dru track rule, which the repo tools do not read (its TOOL_GAPS
  #2). **Independent check:** kicad-cli DRC on a copy gives 0 track_width and 0 clearance errors, and 0 unconnected.
- **kicad-cli on the stored fills:** 8 track_dangling (7 GND stubs + VBUS); with --refill-zones, 1 (VBUS). Prep
  finding #7.
- **Verifier call 1 FAILED** it: SW1/SW2 actuators along their edges, ungraded impedance declarations, courtyard
  track_width. All were fixed; call 2 PASS. Template for U2 (MCP16501), drift 0.0.
- iso 100/103. measure wall 2:36:30. fence CLEAN.
- **Films:** film_seed 0 of 111 differ; film_flow OK (judge 6, best = kept = s11, 876 frames).

## 14 imx6ulz_4l (teammate: DONE, verifier PASS on call 2) -- gp14: machine DONE, verifier FAIL (DDR3 pairs); control on main: blocking 9
- **My compare grade agrees exactly:** done true, blocking 0, 377 vias, 2496.77 mm, 2361 segments. check_complete DONE AND
  authored DONE. Buildable (17 KiCad courtyards_overlap errors that check_assembly grades advisory, disclosed),
  floorplan 0, connected, check_drc 0 (8 length-rule nets in range). 193-194 Type VII vias.
- **DDR3:** DQ0-7 all inside the .kicad_dru 11.5-14.5 mm window (a 25-order search, helpers/dq_sequence_search.py).
  DQS0/DQS1/CLK0 coupled, skew 0.42/0.31/0.02 mm. In gp14 they were barely coupled with 4.6 mm skew. Verifier call 1
  FAILED DQS1 as uncoupled (0 of 25 mm) on the first DONE; nothing in the repo graded it (its TOOL_GAPS #2).
- **The wall includes the ~1 h orchestrator stall (11:45-12:46 local),** so the effective time is about 3.5 h.
- **fill_for_delivery's KiCad 10 re-save** wrote explicit all-"no" via protection on 377 vias, which would grade
  blocking. helpers/stamp_type_vii.py removed it and re-stamped 194. This is the same cluster as glasgow TOOL_GAPS #1.
- iso 153/153. measure wall 4:34:49. fence CLEAN.
- **Films:**
  - film_seed: 0 of 159 differ against s6. The 19 hand moves were made on final.kicad_pcb (CHOSEN after), so the film
    shows the anneal, and those 19 parts sit at their seed poses in it.
  - film_flow: OK (judge 6, best = kept = s6, 874 frames). It ends on final_route/s8_iter2, the manifest's last board.
    The shipped routed.kicad_pcb adds the hygiene steps (check_join + remove_segments, not in the manifest; 2747 vs
    2744 copper lines).
- 08 CM5: place_pose --force used in scratch/ (decl -> decl2). At grading, check whether a forced pose reached the shipped placement (CHOSEN after / ledger).
- 13 pico: the cheats watcher flagged that the saved REPORT.md names no delivered digest. The sha c457c559... was in the teammate's summary above '# REPORT' (save_report keeps only from the header). DONE and DELIVERED.sha256 carry it.

## 13 pico_ice_rev3 (teammate: NOT DONE, blocking 3; verifier FAIL) -- gp14: NOT DONE, blocking 8; control on main: blocking 8
- **My compare grade agrees exactly:** blocking 3 = broken 3 (+3V3 at C12.1, /LED_R at U6.41, /~{ICE_RST} at U3.39),
  368 vias, 2606.79 mm, 3294 segments. check_complete INCOMPLETE (blocking 3, orphan stubs, weird copper 11); authored
  UNSOUND. Buildable, floorplan 0, check_drc 0.
- **The blockers:** each is PASSABLE on the placement and CAGED only by routed copper. The protected USB pairs wall in
  the last nets, and naming them exactly in --rip-existing-nets is honoured by the main pass only, not by the plane
  finalize (its TOOL_GAPS #1). Free-via search: no site within 2.5 mm of C12.1.
- **The stop rule fired twice** (plateau). 74% of the 4:55 wall was waiting on routes (grid 0.025 passes about 40 min).
- **fill_for_delivery's KiCad 10 re-save** set explicit no-protection on 368 vias (113 via-in-paste), restamped by
  helpers/restamp_after_fill.py. That is the 3rd board in this cluster (glasgow, imx6ulz, pico).
- iso 75/82. measure wall 4:54:52. fence CLEAN.
- **Films:** film_seed 5 differ (C17, C2, C21, C29, C8, all hand repairs in CHOSEN after); film_flow OK (judge 1,
  best = kept = s1, 823 frames).
- 17 environment_sensor: probe arms E1-E3 pass --board-edge-clearance to route_diff. At grading, check the shipped chain's edge clearance against the board's own.

## 15 am32_esc (teammate: DONE, verifier PASS on call 2) -- new board; control on main: DONE (133 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 104 vias, 954.42 mm, 756 segments (human 293 vias / control
  133). check_complete DONE; authored UNSOUND (Default clearance 0.13 -> 0.1075 at fine-pitch plane taps). Buildable,
  floorplan 0, connected, check_drc 0. 53 Type VII vias.
- **Verifier call 1 FAILED** it on blocking 52 (drc_via_in_paste) after fill_for_delivery's KiCad 10 re-save. That is
  the 4th board in this cluster. The shipped chain upgrades the placement copy to KiCad 10 first (kicad-cli pcb
  upgrade), so the route steps can stamp Type VII.
- **Hand steps:** helpers/drop_segment.py removed a redundant 5v loop edge that route.py ships (its TOOL_GAPS #1). It
  added an intent keep-out over the mouse-bite-isolated motor-mount section, a property of the outline (TOOL_GAPS #3).
  Template for U2 (FD6288Q, text-only), drift 0.0.
- **Disclosed:** SW1 hard against the bottom-right mounting hole (courtyard enters the hole 0.156 mm). No hole keep-out
  is declared.
- iso 75/83. measure wall 1:54:08. fence CLEAN.
- **Films:** film_seed 0 of 93 differ; film_flow OK (judge 2: s5 + s8, best = kept = s5, 688 frames).

## 17 environment_sensor (teammate: DONE, verifier PASS on call 1) -- new board (it replaced tfgps01); control on main: blocking 1
- **My compare grade agrees exactly:** done true, blocking 0, 101 vias, 933.23 mm, 881 segments (control 118 vias).
  check_complete DONE (with --impedance-nets '/USB_D_*', the 90 ohm class declared by the routing); authored UNSOUND
  (track 0.0889 at the USB pads, via 0.28/0.15, clearance 0.1187). Buildable, floorplan 0, connected, check_drc 0.
- **Edge clearance:** the board declares 0.0. The teammate routed every step at 0.22. Its TOOL_GAPS #2: at 0.2, 5
  tracks were 2 um inside at the slot arcs, which check_drc and kicad_drc_compare hide as "#408".
- **KiCad requires J2/J3's MP tabs joined;** the repo's connectivity tools miss it. Two hand check_joins.
- **Same fill_for_delivery KiCad 10 cluster** (68 via-in-paste): 5th board. The fix was an upgrade-first chain.
- **iso:** first pass 0/93 models. Every model sits under ${ANT3DMDL}, Antmicro's library, which is not installed.
  iso_render.py now falls back to KiCad's own model of the same file name: 69/93.
- measure wall 1:26:25. fence CLEAN.
- **Films:** film_seed 0 of 107 differ (D1/D2 were moved on final.kicad_pcb); film_flow OK (judge 4, best = kept = s4,
  714 frames).

## 19 icebreaker_v10e (teammate: DONE, verifier PASS on call 1) -- new board; control on main: DONE (238 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 266 vias, 2688.88 mm, 1964 segments (human 159 vias /
  control 238). check_complete DONE; authored UNSOUND (track 0.0889, clearance 0.1, 31 advanced-tier vias). Buildable,
  floorplan 0, connected, check_drc 0. 78 Type VII vias.
- **The outline is 4 electrically separate regions** (the main board, the snap-off PMOD, and 2 frame strips cut off
  by mouse-bite drill rows). The placer cannot see this (its TOOL_GAPS #1): pass 1 put 10-51 parts per seed on
  unreachable regions, and the checks said buildable. The fix was 2 intent `blocks[]` regions.
- **Disclosed compromise:** the /ET_ and /EB_ adapter circuits sit on the main board, not on the frame strips they
  were drawn for. On the strips they have no legal pose (6.1 mm courtyards in 6.2 mm strips). So the board is no
  longer separable there.
- **5 placement passes, about 40 min.** The §3.6 "unusable pass counts toward stop rule 3" reading would have
  stopped the run before any route (TOOL_GAPS #3). The teammate continued, and says so.
- **fill_for_delivery KiCad 10 cluster:** 6th board (69 via-in-paste); the fix was an upgrade-first chain.
- **KiCad starved_thermal at U1.2** (the designer's thermal pour), a real KiCad error at project severity; advisory.
- iso 104/111. measure wall 2:07:42. fence CLEAN.
- **Films:** film_seed 0 of 191 differ; both films exit 4 (place_simple's exit for the 16 refused mouse-bite
  drills, every run) but render. film_flow judge 5, best = kept = s3, 858 frames.

## 01 ecc83-pp_v2 (teammate: DONE, verifier PASS on call 1) -- gp14: DONE (131.72 mm); control on main: DONE (1 via, 163.75 mm)
- **My compare grade agrees exactly:** done true, blocking 0, 0 vias, 105.52 mm, 26 segments (gp14 131.72, human 219.1,
  control 163.75). check_complete DONE AND authored DONE (routed at the board's own class, no narrowing). Buildable,
  floorplan 0, connected, check_drc 0.
- **Kept pass 3** (place_args --moves 110000, i.e. 20x the default anneal), after the variant-B re-judge. The teammate
  measured the default anneal stopping early on this board (121.6 vs 105.52 mm; TOOL_GAPS #3, one board, a
  measurement only). TOOL_GAPS #1: the judge runs one chain, while the routing skill prescribes two variants for this
  board class.
- iso 11/11. measure wall 0:27:09. fence CLEAN.
- **Films:** film_seed 0 of 15 differ; film_flow OK (judge 6, best = kept = s1, 410 frames).

## 08 CM5_MINIMA_3 (teammate: machine DONE; verifier FAIL) -- gp14: DONE on own waivers; control on main: blocking 3
- **My compare grade.**
  - On intent_run.json: done true, blocking 0, 201 vias, 2527.06 mm, 2123 segments, check_complete DONE, authored DONE.
  - On the GIVEN intent: blocking 1 = assembly 1, NOT BUILDABLE. The one gating pair is H102 <-> J1 courtyard
    (4.60 mm2). Only the teammate's own row waives it: J1 is a judgment fixed pose (the Kycon mid-mount RJ45 in the
    outline notch) with accept_courtyard_overlap H102. The human board has the same overlap.
  - **Module301 <-> Module302 is now waived by the GIVEN intent** (fixed_pose_accepted): #1298's fix works at main.
  - **So CM5 is "DONE on its own waiver".**
- **Verifier FAIL:**
  - J1's shield tabs are 0.20 mm from the notch edge against 0.372. This is geometric: a 16.2 mm tab span in a
    15.79 mm notch. check_drc skips pad-to-edge by default (KiCad flags 2).
  - The diff pairs are declared but no skew rule exists; 13 of 18 are over 0.5 mm skew.
  - The ledger closes with stop 4.
- **Placement took 5 passes.** Nothing models the M.2 card or the CM5 module body covering parts (its TOOL_GAPS #1).
  The fix was a keep-out under the 2242 card. CN1 was moved out from under the module.
- **The prescribed CM4/CM5 underpad fanout drops pads** at the 0.45 via floor; the stub fanout escapes 38/38. The
  DENSE layer-price recipe lets tracks onto reference planes (#1359 closed, still hit).
- iso 63/77. measure wall 2:31:28. fence CLEAN.
- **Films:** film_seed 0 of 84 differ. film_flow SKIPPED, correctly: the judge's best was s0, but the teammate kept s7
  because s0's buck caps sat up to 24 mm off the template.
- 04 mixer: its judging chain passes a bare --clearance (CLAUDE.md prefers --clearance-ceiling in chains). At grading, check the shipped chain's clearance against Default 0.2 / Board Setup min 0.3, and against what the .kicad_pro writeback declares.

## 18 uecg (teammate: DONE, verifier PASS on call 3, resting on 2 spec decisions) -- new board; control on main: blocking 3
- **My compare grade agrees exactly:** done true, blocking 0, 139 vias, 928.45 mm, 898 segments (human 148 vias / control
  150). check_complete DONE; authored UNSOUND (track 0.19 -> 0.127, 13 advanced-tier vias, clearance 0.15 -> 0.127).
  Buildable, floorplan 0, connected, check_drc 0. 54 Type VII vias.
- **The verifier pass rests on two spec re-declarations made after FAILs. Disclose them prominently:**
  1. **Power widths.** The requested 0.4-0.7 mm shipped thin (the battery path is 74% at 0.127). The teammate
     re-declared the spec as IPC-2221 minimums for the estimated currents (<= 122 mA), so every minimum is 0.127.
  2. **RF feed.** The declared 50 ohm measured 64/80 ohm. The teammate dropped the declaration as electrically short
     and inside the Nordic match. It ships at 70/89 ohm.
- **TOOL_GAPS:**
  - #2: requested power widths reach no grader.
  - #3: board_score's --impedance-nets checks only the reference plane, not Z0.
  - #1: electrode pads (12 mm) inside 3.6 mm courtyards are invisible to the anneal (all 12 pass-1 seeds NOT
    BUILDABLE).
- **One rule slip** (rm -f of a 9-byte junk download), disclosed by the teammate.
- iso 70/74. measure wall 1:13:58. fence CLEAN.
- **Films:** film_seed 0 of 75 differ (the L2/L3 template restore went to a separate file); film_flow OK (judge 6,
  best = kept = s8, 1287 frames).
- 11 daplink: the final chain passes an explicit --fab-tier (advanced, a hard tier) to route_planes / route_diff / route.py. Disclose, with the floors from check_complete --authored-from.

## 16 esp_rust_board (teammate: DONE, verifier PASS on calls 1 + 2) -- new board; control on main: blocking 2
- **My compare grade agrees exactly:** done true, blocking 0, 81 vias, 985.55 mm, 598 segments (human 217 vias / control
  104). check_complete DONE AND authored DONE: the shipped chain used --fab-tier standard, with no via under the board's
  0.4 minimum. Buildable, floorplan 0, connected, check_drc 0. 33-34 Type VII vias.
- **TOOL_GAPS:**
  - #2: the default --fab-tier auto ships 0.25/0.15 vias below the board's own 0.4 minimum on IO0, and its
    disclosure names only the GND rescue.
  - #3: a 0.042 mm pad-edge overlap "connection" on USB_D-, which the checkers disagree on.
  - #1: a classless edge_connectors row is graded but never seated (the U3 antenna module), which cost pass 1. That
    is the same cluster as StickHub's C38.
- **The antenna keep-out** was added by the teammate with add_rule_area (skill §4 trap #1200); the verifier found no
  copper in it.
- **2 verifier subagents for 2 calls** (the second call was a fresh spawn), disclosed by the teammate.
- iso 48/56. measure wall 0:52:55. fence CLEAN.
- **Films:** film_seed 0 of 55 differ; film_flow OK (judge 6, best = kept = s8, 592 frames).

## 11 daplink (teammate: DONE, verifier PASS on call 1) -- gp14: DONE (56 vias); control on main: blocking 0, INCOMPLETE (57 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 20 vias, 375.71 mm, 225 segments (gp14 56 / human 27 /
  control 57). check_complete DONE; authored UNSOUND (3 vias 0.3/0.2 on the advanced tier, annular 0.05, clearance
  0.2 -> 0.1452). An arm holding the board's own floors left /OSCOUT boxed (PASSABLE per check_reachability; TOOL_GAPS
  #2). 10 Type VII vias.
- **Pass 2 with --crossing-weight 4** took vias from 30 to 20.
- **Dangling vias from the #535 via-in-pad unblock** survive the #1166 sweep (TOOL_GAPS #1, a variant of closed #1166);
  fixed by --force-reroute.
- **FENCE / LEAK DISCLOSED:** docs/floorplan-intent.md:671-676 quotes daplink's source J2/J3 / P1 bands. The teammate
  read it after deriving its own bands, which agree (prep finding #8).
- iso 33/35. measure wall 0:33:11. fence CLEAN.
- **Films:** film_seed 0 of 35 differ; film_flow OK (judge 6, best = kept = s11, 522 frames).

## 02 sonde_xilinx (teammate: DONE, verifier PASS on call 1) -- gp14: DONE (516.67 mm, 0 vias); control on main: DONE (18 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 0 vias, 556.16 mm, 116 segments (gp14 0 / 516.67, human
  3 / 637.8). check_complete DONE AND authored DONE. Buildable, floorplan 0, connected, check_drc 0. The designer's B.Cu
  GND pour was kept (no route_planes step).
- **Edge-mount DSUBs:** the teammate added overhang bands J1 {25.12, 25.17} and J2 {14.20, 14.25}. Without them J2
  seats with its pads 5.30 mm inside the board, and every grader says pass (TOOL_GAPS #1). Nothing reads the
  footprint's "PCB edge" marker. gp14's board had the same footprints.
- **Copper is 556 against gp14's 517:** the bands seat the DSUBs further out, as built. A fair difference.
- iso 23/25. measure wall 0:23:24. fence CLEAN.
- **Films:** film_seed 0 of 25 differ; film_flow OK (judge 6, best = kept = s4, 459 frames).

## 03 complex_hierarchy (teammate: DONE, verifier PASS on call 1) -- gp14: DONE (740.61 mm, 0 vias); control on main: DONE (14 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 0 vias, 710.64 mm, 178 segments (gp14 740.61, human 1265.7,
  control 1185). check_complete DONE AND authored DONE. Buildable, floorplan 0, connected, check_drc 0.
- **Template for U102** (ICL7660 charge pump, text-only), drift 0.0.
- **Pass 2 used --seeds 12-23 --clustered-seeds 18-23** (a second set of 12). The kept seed was s18, chosen by FULL
  route over the judge's quick pick s23. The quick ranking was inverted on copper in both passes (TOOL_GAPS #1).
- iso 68/68. measure wall 0:29:32. fence CLEAN.
- **Films.**
  - film_seed first failed (exit 2): films.sh passed the run's --seeds 12-23 with --seed 18. films.sh now drops the
    pass's seed-selection args. Re-filmed: 0 of 68 differ.
  - film_flow SKIPPED, correctly: the judge's best was s23, the run kept s18.

## 04 multichannel_mixer (teammate: DONE, verifier PASS on call 1) -- gp14: DONE (70 vias); control on main: DONE (140 vias)
- **My compare grade agrees exactly:** done true, blocking 0, 42 vias, 1840.3 mm, 516 segments (gp14 70 / 1964, human
  29 / 1959, control 140). check_complete DONE AND authored DONE: routed at the board's own floors (clearance 0.3,
  track 0.3, via 1.5/0.3, --escalation board). Buildable, floorplan 0, connected, check_drc 0. 20 Type VII vias.
- **The given intent was used unchanged** (no intent_run).
- **The kept seed is s10, not the judge's s11:** s11 never closed GND at the 1.5 mm via floor; route.py boxes in the
  TL072 GND pins with its own copper (TOOL_GAPS #1). Three check_join GND stubs fixed KiCad starved_thermal errors
  route.py left.
- **TOOL_GAPS #2** (the default escalation lays vias below the board's 1.5 mm minimum and lowers the minimum) gave one
  false DONE ledger row, which the teammate corrected. TOOL_GAPS #3: the fill_for_delivery KiCad 10 cluster (the 7th
  board).
- **iso 0/21:** the 16 pots and 5 jacks reference Potentiometer_THT / Connector_Audio models absent from this Mac's
  KiCad 10 library (gp14: the same 0/21). find_models candidate at asset build.
- measure wall 1:10:36. fence CLEAN.
- **Films:** film_seed 0 of 114 differ. film_flow SKIPPED, correctly: the judge's best was s11, the run kept s10.

## 07 One-Air-Max (teammate: DONE, verifier PASS on call 2) -- gp14: DONE only on its own waivers (BAT1/DC1/PWR_SW1); control on main: blocking 0, INCOMPLETE
- **My compare grade agrees exactly:** done true, blocking 0, 169 vias, 2647.59 mm, 1909 segments (gp14 225, human 410,
  control 255). check_complete DONE; authored UNSOUND (5 small vias on MODE/SYS/REGN, 0.25-0.45 with 0.15-0.2 drills).
  Buildable, floorplan 0, connected, check_drc 0. No overlap waiver was needed this time.
- **Verifier call 1 FAILED it on bodies drawn only on silk**, which no grader gates (its TOOL_GAPS #1, HIGH):
  - Solarpower1, PWR_SW1 and NTC1 sat inside the BAT1 holder outline;
  - DC1 sat over I2C2, with its mouth facing west;
  - U3, R5 and R63 sat under the ESP32 module.
  check_assembly said buildable. All were hand-repaired; call 2 PASS.
- **TOOL_GAPS #2:** route.py --escalation board writes vias with drill > diameter (0.45/0.508); check_drc is clean while
  KiCad flags hole_clearance. That is the same cluster as old issue #1349 PARTLY. Fixed by hand with helpers/fix_copper.py.
- **TOOL_GAPS #3:** on a notched edge, the edge seat put U1 at the notch depth, 6.4 mm inside the real edge with its
  antenna under the battery, graded only as a warning. One placement pass was lost.
- **fill_for_delivery KiCad 10 cluster:** the 8th board (5 vias hand-stamped Type VII).
- **iso 1/198:** EasyEDA-converted models (${EASYEDA2KICAD}), not installed. This is the board to try find_models on.
- measure wall 2:53:37. fence CLEAN.
- **Films:** film_seed 0 of 204 differ. film_flow SKIPPED, correctly: the judge's best was s4, the run kept s8.

## 05 interf_u (teammate: DONE, verifier PASS on call 2) -- gp14: DONE (157 vias); control on main: blocking 1
- **My compare grade agrees exactly:** done true, blocking 0, 88 vias, 3834.05 mm, 856 segments (gp14 157 / 4630, human
  84 / 5102, control 240). check_complete DONE AND authored DONE (--escalation board; routed at the board's own
  floors). Buildable, floorplan 0, connected, check_drc 0.
- **The given intent was used unchanged.** Kept seed s1 (the first judge's pick). The re-judge with the shipped chain
  named s11, but s11 full-routes worse (blocking 1, 99 vias).
- **KiCad DRC shows 5 starved_thermal errors** on the designer's relief GND pour, which was kept as drawn (not gated,
  #1334). TOOL_GAPS #4: the routing skill says add --thermal-relief, while plan rule R07 refuses it.
- **TOOL_GAPS #1:** route.py's rip-up blames /PC-DB6 (the F.Cu finger opposite) for VCC's open at BUS1.3; the wall is
  /PC-RST on B.Cu. TOOL_GAPS #2: the skill never mentions --escalation board (the default went below the floors).
- **2 verifier spawns for 2 calls** (disclosed). iso 21/23. measure wall 1:57:54. fence CLEAN.
- **Films:** film_seed 0 of 24 differ. film_flow SKIPPED, correctly: the judge's best was s11, the run kept s1.

## 11 daplink, RE-RUN (teammate: DONE, verifier PASS on call 2) -- first run (now _superseded/): DONE, PASS, 20 vias, authored UNSOUND
- **Why re-run:** the start-state audit found the first run had read docs/floorplan-intent.md's daplink band values before writing its own. Measured afterwards: those values are gp14's AI-placed bands, not the human board's (human J2/J3 9.17 mm, P1 0.025 mm). See AUDIT.md. The re-run had that paragraph hidden; it met the same numbers in connector_geometry.py's docstring at 20:58 UTC, after writing all its bands (20:15, 20:53).
- **My compare grade agrees exactly:** done true, blocking 0, 22 vias, 411.74 mm, 257 segments. check_complete DONE and authored DONE: routed at the board's own 0.2 clearance and 0.5/0.3 vias (`--escalation board`), where the first run lowered the vias to 0.3 and the clearance to 0.145. Buildable, floorplan 0, connected, check_drc 0, kicad_drc_compare CONSISTENT.
- **Verifier call 1 caught a real seat fault:** P1's shell sat 0.5 mm inside its own drawn PCB-Edge line while the floorplan grade said pass (rounded outline -> courtyard reading; G12's family). Fixed by a 0.505 mm place_pose move, recorded in CHOSEN "after".
- **Films:** film_seed 0 of 35 differ. film_flow SKIPPED correctly: the quick judge's best was s1, the run kept s10 on full routes (22 vs 27 vias), G09 again.
- iso 33/35. measure wall 0:57:37, model 32 min, tools 18 min, waiting 8 min. fence CLEAN. Repo untouched (the docs edit was mine and is restored).

## 12 steppenprobe, RE-RUN (teammate: DONE, verifier PASS on call 2) -- first run (now _superseded/): DONE, PASS on call 2, 140 vias
- **Why re-run:** the first pile carried 312 KiCad-6 pad-level `locked` tokens (make_unplaced leaves them; the parser ignores them, so no part was pinned). Re-staged with stage step 3a, strip_pad_locks.py; the pile is byte-identical to the first one minus those tokens.
- **My compare grade agrees exactly:** done true, blocking 0, 123 vias, 1066.84 mm, 966 segments. check_complete DONE, authored DONE. Buildable, floorplan 0, connected, check_drc 0. Power class 0.3 mm met (the verifier graded it with --net-min-widths: 0); USB skew 0.632 mm.
- **Verifier call 1 FAIL:** Power class widths ungraded (GND/VBUS/+3V3/+1V8 at 0.15 mm for 1.65-19 mm) and the USB pair ungraded at 4.52 mm skew. The fix chain: rails first and pours last at 0.3, then --diff-pair-intra-match.
- route_diff's writeback lowered min_hole_clearance 0.25 -> 0.15 (G19); the copper meets 0.25 (check_drc at 0.25, and KiCad at 0.25 restored).
- KiCad: 28 solder_mask_bridge, all between J1's own PTH pins (library geometry).
- **Two verifier subagents for two calls** (the teammate spawned a fresh one for call 2), within the 3-call cap; disclosed.
- **Films:** film_seed 0 of 84 differ. film_flow SKIPPED correctly: the judge's quick best s8, kept s11 on full routes (133-136 vs 143-155 vias), G09.
- iso 75/75. measure wall 1:28:17. fence CLEAN. Repo untouched.
