<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT.md: fa10 board 05, interf_u (`/pcb-free-agent full`)

## Result: NOT DONE

| DONE condition | required | measured on final.kicad_pcb |
|---|---|---|
| board_score blocking | 0 | **10** |
| unrouted | 0 | **2**: Net-(U3-Y2), Net-(U3-Y3) |
| broken | 0 | **7 joins on 6 nets** |
| DRC (graded at the authored 0.254 mm) | 0 | 0 (verifier: also 0 with `--clearance 0.254`) |
| undersized (track 0.2 / via 0.9 / drill 0.5) | 0 | 0 |
| power widths (GND/VCC at least 0.5 mm, Power class) | 0 | **1**: GND has 147.4 of 235.8 mm under 0.5 (narrowest 0.2); VCC is all 0.5 |
| floorplan (given `intent.json`) | 0 errors | 0 errors, 0 warnings (exit 4 only because the given intent withholds 3 budgets) |
| check_assembly | buildable | buildable (one advisory: C6/G1 courtyard overlap of 1.0 mm²) |
| check_complete | DONE | **INCOMPLETE** (blocking 10, plus one dangling /CS1- via) |

- **Blocking breakdown:** unrouted 2, broken 7, power widths 1, DRC 0, undersized 0, floorplan 0, assembly 0.
- **Quality:** 435 vias, 6744.55 mm copper, 4053 segments.

## Stop rule that fired: BUDGET (10 h hard cap)

At 12:03 the remaining 67 min could not hold another full routing pass (measured at 35-81 min each) plus cleanup and re-checking. The three attempts made after the best board did not improve it:
- the iteration pass with rip authority fell into a cascade;
- the iteration pass without it was still stuck in its tap phase when stopped;
- a scoped 7-net lap was rolled back by route.py's own improvement check, because disconnected pads went from 9 to 12.

**Remaining blockers:**
- **Net-(U3-Y2):** U3.16 (113.19, 107.40) to U8.5 (159.78, 108.64). Zero copper.
- **Net-(U3-Y3):** U3.15 (113.19, 109.94) to U8.6 (162.32, 108.64). Zero copper.
- **/MD7:** U9.B8 (152.54, 65.30) is cut off.
- **/PC-RD:** U3.13 (113.19, 115.02) is cut off.
- **/REF7:** U2.14 (123.81, 111.92) is cut off.
- **/REF8:** U2.5 (116.19, 106.84) is cut off.
- **GND:** U3 pads at (105.57, 97.24) and (113.19, 99.78); 3 pieces, 2 joins needed.
- **Net-(C3-Pad1):** X1.2 (98.92, 83.74) is cut off.
- **GND width:** 187 of 269 segments are under the Power class's 0.5 mm (the GND connections the router added into the pour).
- **check_complete's weird-copper finding:** the /CS1- via at (129.5, 36.2). It bridges two F.Cu track ends 0.2 mm apart; removing it leaves a fragile 0.084 mm overlap, so I kept it.

**Classification of the two zero-copper nets: placement.** My zone layout put U3 (over the address fingers, left) and U8 (data side, right) at opposite ends, but they share 7 nets, so these two nets have to cross 46 mm through the most crowded strip.

## Floors

- **Track:** I asked for 0.3 mm (the Default class says 0.4). The router narrowed to 0.2 mm only at pad necks, which is the board's own minimum.
- **Vias:**
  - Signals use 1.0/0.5 mm (the class says 1.4/0.6), still at or above the Board Setup minimums of 0.9 mm via and 0.5 mm hole.
  - VCC's 2 vias are 1.4 mm.
- **Clearance:** held at the class 0.254 mm with `fab_floor_board.txt` (`clearance = 0.254`). The verifier confirmed no class clearance was lowered.
- **route.py's own `Design rules [...]` lines:**
  - d4_all: "47 feature(s) on 42 net(s) delivered below the requested size (smallest track width 0.2 mm, smallest via diameter 0.9 mm)"
  - d4_i2: "14 feature(s) on 7 net(s) …"
  - cleanup pass: "1 feature(s) on 1 net(s) … (smallest track width 0.2 mm)"
- **Project rules changed:** `min_copper_edge_clearance` 0.0 → 0.2 and `min_via_drill` added at 0.5.
- **check_complete `--authored-from`:** lists no relaxed floor. It lists one floor as not measured: copper-to-hole clearance (declared 0.0).
- **Not shipped:** r/d3_all had its clearance escalated to 0.127 mm (see G6).

## Intents used

- DONE is graded against the given `intent.json`.
- Placement was steered with three derived files beside it:
  - `intent_rot180.json`: U9 at 180°, from rank_rotations.
  - `intent_band.json`: adds a keep-out band at [90.8, 122, 172.1, 133.4] above BUS1, so the 62 fingers have room to fan out.
  - `intent_band2.json`: adds zones for the address parts (U2, U3, JP1, RR1), the data parts (U1, U8) and the memory (U5).
- No `--decaps-from` was used, because no placed reference was allowed. The given 34.08 mm decap limit holds on the final board (0 errors).

## Timeline (UTC)

| time | event |
|---|---|
| 03:10:37 | first command |
| 03:13 | BUS1 and P1 placed at their declared poses and locked |
| 03:17 | first legal placement (seed 0, buildable) |
| 03:36 | U9 turned to 180° (seed crossings 1844 → 1020) |
| 04:52 | U9 pinned at (150, 82) beside P1 (crossings 923) |
| 06:02 | fanout band above BUS1 (crossings 789) |
| 06:27 | final placement: zones plus decap fix (crossings 748, floorplan clean) |
| 06:45 | escape stubs on the BUS1 fingers |
| 07:05 | VCC routed alone at 0.5 mm (23/23 pads) |
| 09:30 | first fully routed board, d3_all; not shippable because its clearance was escalated |
| 10:30 | first routed board at the authored rules, d4 (blocking 13) |
| 11:05 | d4_i2 (blocking 11) |
| 11:31 | after cleanup (blocking 10) |
| 11:36 | final board frozen |
| 11:38-11:50 | verifier call 1: FAIL |
| 12:01 | scoped lap rolled back |
| 12:05 | ledger closed, film made |
| — | first DONE: never reached |

## Where the time went

From `measure.py` on my transcript, at 11:40:
- 8h30m wall clock in total;
- 5h57m (70%) waiting on long jobs;
- 1h54m in other tool calls;
- 39 min of model time;
- 377 tool calls.

The big cost was routing:
- runs I stopped without a usable board: a0, a1, b0_r1, b0_t3, b0_t3m0, c0_r1, c0_env, d0_a, d0_b, d1_b, i3a, i3b;
- d2_all was killed by the 2 h background cap during its final passes;
- completed runs: d3 (81 min), d4 (59 min), d5 (53 min), i1 and i2 (36 min each).

Placement took under 30 min of compute in total.

## What worked, with measurements

- **Turning U9 to 180°:** seed crossings 1844/1722 → 1020/1021.
- **Pinning U9 beside P1:** 1020 → 923.
- **The fanout band above BUS1:** 923 → 789, and that placement's first routing pass had 0 failures.
- **Zones plus moving C6 and C1:** 748 crossings, 3 decap errors → 0.
- **0.3 mm instead of 0.4 mm track:** first-pass failures 6 → 2 on the same placement.
- **Escape stubs on the BUS1 fingers:** the fingers disappear from the open-pad lists.
- **VCC first at strict 0.5 mm:** 23/23 pads, 340 mm all at 0.5 mm, 2 vias, in 166 s.
- **1.0/0.5 mm vias:** the rescue pass took 304 s instead of 2113 s.
- **Pinning the clearance at 0.254:** DRC 0 at the authored rules, at the cost of about 3 more open nets.
- **Iteration with rip authority:** blocking 13 → 11; the scoped cleanup pass then took it to 10.

## What did not work, with measurements

- **No rip-up at all (`--max-ripup 0`):** 16 first-pass failures.
- **`--max-ripup 3`:** blocking 23.
- **The routing skill's tuned setting bundle without the stubs:** the BUS1 fingers stayed sealed in.
- **The scoped 7-net lap:** rolled back by the router.
- **The rank_rotations route probe:** killed, since it routes 4 times in sequence with default settings.

## Tool gaps

Seven entries in TOOL_GAPS.md, ranked by cost, each with a repro command:
1. **G4:** rip-up cascade, long runtime, and no board left when a run is stopped.
2. **G5:** no edge-finger escape tool; helpers `add_finger_stubs.py` and `trim_stub_tails.py`.
3. **G6:** clearance rewritten to 0.127 mm while the graders read clean (#1160).
4. **G2:** nothing checks whether the class track width fits between 2.54 mm-pitch through-hole pins, and check_channels says a through-hole PGA's inner pins need vias.
5. **G7:** `--keep-input-copper` iteration passes stack duplicate GND copper (3 → 17 findings); helper `dedupe_stacked.py` (#162).
6. **G1:** place_seed calls a grid pile "already PLACED" once the fixed parts are seated.
7. **G3:** qfn_fanout writes no copper for the finger row and still lowers the project's via and hole minimums.

## Verifier verdict (1 of 3 calls used)

`verdict_1.txt` reads `VERDICT=FAIL`.
- Identity matches; no class clearance was lowered.
- Buildable, with no copper off the board.
- BUS1, P1 and the outline match the declaration.
- board_score blocking 10; check_complete INCOMPLETE.
- DRC: 0 violations, including at 0.254 mm.

Lens files:
- connectivity: FAIL (evidence 9)
- DRC: PASS
- spec: FAIL (evidence 10)

## Independent grade (`grade/grade_final.json`)

grade.py reports:
- done: false
- blocking 10 (unrouted 2, broken 7, DRC 0)
- 435 vias, 6744.55 mm copper, 4053 segments
- crossings 842, HPWL 5065.5 mm
- buildable
- check_complete INCOMPLETE
