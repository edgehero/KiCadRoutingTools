# The 65 issues gp14 filed (#1296-#1360): re-checked on main bda59fa0

Each batch report (B1.md-B8.md) has the command, the measurement gp14 -> main, the fix commit and the test.

**Tally: 65 checked: FIXED 52, PARTLY 7, STILL BROKEN 6**

| batch | finding | issue | verdict | title |
|---|---|---|---|---|
| B1 | H02 | #1296 | FIXED | Seed judge ranks and stops on placements with error-graded floorplan findings: judge.json filters only `illega |
| B1 | H04 | #1297 | FIXED | place_simple refuses declared poses on pad bounding boxes and castellated half-holes, so every seed is "illega |
| B1 | H05 | #1298 | FIXED | Declared fixed poses that overlap each other grade NOT BUILDABLE, and neither --emit-intent nor fixed_poses[]. |
| B1 | H07 | #1300 | FIXED | place_simple seats courtyard-less parts on pad boxes while check_assembly gates their fab bodies, and the bran |
| B1 | H15 | #1307 | FIXED | place_simple's anneal prices a pin-frame container's whole-board rect in its overlap term, so no state is ever |
| B1 | H16 | #1308 | FIXED | place_simple's anneal prices a drilled part's whole courtyard on the far face: one locating-peg hole blocks th |
| B1 | M02 | #1320 | STILL BROKEN | place_simple prices a supply-pin decap limit wider than the 5 mm tether radius at a flat 5 mm past the limit,  |
| B1 | M03 | #1321 | FIXED | plan-pcb-placement: no step when place_simple names no judgeable seed (empty judge.json) or every judged seed  |
| B2 | H13 | #1305 | FIXED | Placement writer never rotates a pad written `(pad "N" type shape locked (at ...))` (KiCad 6), so every rotate |
| B2 | H14 | #1306 | FIXED | check_assembly, place_pose and check_drc skip pad overlaps inside one footprint, so a board KiCad grades with  |
| B2 | M08 | #1325 | FIXED | place_simple's edge seat says "no room along the <edge> edge" for three different faults, two of them seats th |
| B2 | M09 | #1326 | PARTLY | place_pose grades a castellated module's half-holes against the edge-clearance floor (the #1096 exemption stop |
| B2 | M15 | #1330 | FIXED | place_simple's `apart` hint is a constant when the two groups touch anywhere: no gradient, identical placement |
| B2 | M16 | #1331 | FIXED | place_simple's edge seat ignores an intent `edge_connectors[].class`; DC jacks, slide switches and part-number |
| B2 | M29 | #1343 | STILL BROKEN | place_simple prices no far-face escape field under a BGA: back-face parts fill the ball field's outer escape r |
| B2 | M31 | #1345 | STILL BROKEN | place_simple prices a `proximity` claim without `pads` as every shared-net pad's reach, while check_floorplan  |
| B3 | H17 | #1309 | FIXED | Plane repair: a failed tap restores a re-ripped net into pcb_data but not into the write list, so the net ship |
| B3 | H18 | #1310 | FIXED | route.py ships new shorts (0 -> 17 DRC) and its improvement gate accepts them: /RD's input copper reaches the  |
| B3 | H19 | #1311 | PARTLY | route.py's terminal restore of a ripped BGA escape is erased by the end-of-run stale-input strip, and the hint |
| B3 | H20 | #1312 | FIXED | route.py's end-of-run strict collapse (#1063) prints "removed N" but strips nothing on a pre-KiCad-10 board wh |
| B3 | H25 | #1317 | FIXED | Routed copper lands 1-5 µm inside a footprint's local clearance override; KiCad flags it, but check_drc's defa |
| B3 | H26 | #1318 | PARTLY | route.py ships 0.15 mm necks on 0.3 mm power nets at 0.5 mm-pitch LQFP pins where a 0.3 track fits (fine-pitch |
| B3 | M25 | #1339 | FIXED | route.py's end-of-run re-grade reports GND "recovered" (failed 0) after its own oracle left 5 exact-fill links |
| B3 | M07 | #1324 | FIXED | The #103 pre-existing-blocker hint for a plane-finalize oracle strap names a net far from the failure (it anch |
| B4 | H06 | #1299 | FIXED | route_planes keeps a multi-layer same-net zone even when every layer it covers is poured in the same call; che |
| B4 | M01 | #1319 | FIXED | route_planes (bare pour, 0 vias/0 tracks) writes via/track floors and lowers min_hole_clearance; route.py then |
| B4 | M14 | #1329 | FIXED | route_planes replaces a designer's same-net zone (thermal → solid, clearance, min_thickness, outline) and repo |
| B4 | M19 | #1334 | FIXED | A DONE board ships KiCad starved_thermal errors and sub-min_connection via/pour webs that no repo grader repor |
| B4 | M20 | #1335 | FIXED | The placement/routing skills never run the delivery fill (#910), so a DONE board opens with plane "opens" unti |
| B4 | H08 | #1301 | FIXED | An edge connector's overhang_mm band, graded on the courtyard, changes value when a routing step rewrites the  |
| B4 | M24 | #1338 | FIXED | check_assembly and place_pose grade pad clearance at the Default net class below Board Setup min_clearance (th |
| B5 | H10 | #1303 | PARTLY | route_diff reports a pair "coupled" and "matched" that the written copper is not: the seam re-ask replaces the |
| B5 | H23 | #1315 | FIXED | bga_fanout under-pad/dogbone: an existing track whose start point lies outside the escape window is not stampe |
| B5 | M12 | #1328 | FIXED | qfn_fanout defaults --clearance to 0.1 instead of the board's Default class; with the chain's --clearance-ceil |
| B5 | M17 | #1332 | FIXED | qfn_fanout's stub escape crosses a same-net pad and ends past it; the tail ships as dangling copper that route |
| B5 | M27 | #1341 | FIXED | route_diff GND return vias land below min_hole_to_hole of another pair's GND via (checked on the floored grid  |
| B5 | M28 | #1342 | FIXED | qfn_fanout escapes single-pad (no-connect) nets that bga_fanout skips (#122), leaving useless vias that block  |
| B5 | M34 | #1348 | STILL BROKEN | route_bus (joint) cages a non-bus ball of its array: U2.F1 (VMEM) PASSABLE before the step, CAGED for any widt |
| B5 | H24 | #1316 | STILL BROKEN | route_bus writes OUT with .kicad_pro only: whole_route's best-round copy and flow_frame.SIBLINGS drop .kicad_d |
| B6 | H21 | #1313 | PARTLY | A `.kicad_dru` length window (min/max) is graded by nothing: check_drc and board_score read clean while KiCad  |
| B6 | H22 | #1314 | FIXED | net_queries track graph never joins a via-in-pad to its pad, so board_score length reads connected nets as "no |
| B6 | M18 | #1333 | FIXED | kicad_drc_compare --baseline prints the baseline board's full check_drc listing, unlabelled, as the head of th |
| B6 | M33 | #1347 | FIXED | check_reachability reports routed copper as geometry: CAGED on a routed board, PASSABLE on the same placement  |
| B6 | M35 | #1349 | PARTLY | list_nets --design-rules suggests a via whose drill exceeds its diameter (--via-size 0.45 --via-drill 0.508) |
| B6 | M06 | #1323 | FIXED | converge record refuses the first board_score row after a quick_score row ("graded FEWER components"): quick_s |
| B6 | L06 | #1354 | FIXED | render_placement tells the user to "Override with --allow-unplaced", a flag it rejects (exit 2), and renders a |
| B6 | L03 | #1352 | FIXED | place_pose on a pile prints ~300 KB: pad_edge findings uncapped in JSON_SUMMARY and in the text report |
| B7 | H09 | #1302 | FIXED | redo_record drops KICAD_* env knobs, so redo_commands.sh replays a different board (and redo_stress_test canno |
| B7 | H12 | #1304 | FIXED | KiCad-6 netclass membership (`net_settings.classes[].nets`) is read by no netclass reader: member nets route a |
| B7 | M11 | #1327 | FIXED | No tool runs the placement skill's judging chain over judge.json's seeds; each run hand-writes one |
| B7 | M23 | #1337 | FIXED | manifest_to_plan ignores the plan.sh's `cd <repo>` line, falsely rejects a relative path, and silently prunes  |
| B7 | M26 | #1340 | FIXED | plan-pcb-placement ranks boards with open nets by vias/copper, so a board missing a whole 17-pad rail beats on |
| B7 | M21 | #1336 | FIXED | plan-pcb-routing: route.py's --same-net-pad-clearance is documented only under route_planes, and the through-h |
| B7 | M32 | #1346 | FIXED | Routing skill: Step 5b's prose invariant and its asserts (route_plan_check R14) disagree on a net excluded in  |
| B7 | L11 | #1358 | FIXED | plan-pcb-routing: the fanout benefit check says a <=0.65 mm perimeter part "genuinely" benefits; on one LQFP-4 |
| B8 | M05 | #1322 | FIXED | route_review's "turn 180" is a pad swap that `place_pose rotate` cannot perform; a no-op rotate prints "Modifi |
| B8 | M30 | #1344 | FIXED | Discrete ESD/TVS diodes get no emc_roles row, so nothing places or grades them at their connector |
| B8 | L01 | #1350 | FIXED | movie3d draws DNP parts as boxes and reports them as "fell back to a box" though their models resolve |
| B8 | L02 | #1351 | FIXED | Decap owner election makes resistor arrays and LEDs "the IC it decouples" (no role check on ≥4-pad owners) |
| B8 | L04 | #1353 | FIXED | board_brief and board_context make pose claims off a pile's staging poses; board_brief recommends ops that do  |
| B8 | L08 | #1355 | STILL BROKEN | ortools is an undeclared dependency of awx/route_bus.py (skill Step 1a); without it the bus step lays nothing  |
| B8 | L09 | #1356 | FIXED | No skill step grades or tidies silkscreen: a verified-DONE board carries 4 KiCad silk errors that beautify_lab |
| B8 | L10 | #1357 | FIXED | Intent rows spell their free-text reason three ways (why / note / reason); proximity refuses `why`, fixed_pose |
| B8 | L13 | #1359 | PARTLY | plan-pcb-routing: the DENSE layer-price recipe lets signals onto impedance reference planes, which the declare |
| B8 | L14 | #1360 | FIXED | Skill says to stamp hand-written joins `(locked yes)`, but no tool commits or locks a segment |
