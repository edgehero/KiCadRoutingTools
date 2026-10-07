<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT: fa10 board 10, glasgow_revC (`/pcb-free-agent full`)

**Result: NOT DONE.** The best board is `wk/fa10/10_glasgow_revC/final.kicad_pcb` (sha256 `3ef237a3ebef5ed9196215f53c7cdb6b1afb25100a9972530b3dc6cd8ba9080e`, with `final.kicad_pro`). It scores **blocking 6**: 1 unrouted net, 5 broken nets, DRC 0, floorplan 0, buildable. Stop condition 3 fired: five measured approaches after the best board each failed to lower unrouted + broken. Run 34 started from the same pile, brief and intent and reached blocking 15 with 1370 vias in 7h56m. This run reached 6 at 5h48m and finished at 6h48m.

## 1. Result

No spec flags apply: the board declares only a Default net class and no impedance, length or width spec files.

| condition | required | measured |
|---|---|---|
| board_score blocking | 0 | **6** |
| unrouted | 0 | **1** (/IO_Banks/U5) |
| broken | 0 | **5** (+1V2, /IO_Banks/DA0, /IO_Banks/Z12_P, /IO_Banks/Z8_N, /VCCPLL1) |
| board_score DRC / check_drc (margin 0.1) | 0 | 0 / 0 (after the via stamp, see §9) |
| floorplan errors | 0 | 0 (19 warnings) |
| check_assembly | buildable | buildable (blocking 0) |
| check_complete | DONE | **INCOMPLETE**: blocking 6, orphan stubs on F.Cu (/D7, /IO_Banks/DA0), 27 weird-copper items (21 stacked +3V3/GND, 3 dangling vias, 2 dangling ends, 1 narrow pad joint) |
| ungraded | named | impedance, length, net_widths are UNEXAMINED (nothing declared) |

`blocking_by`: unrouted 1, broken 5, drc 0, undersized 0, floorplan 0, assembly 0.

**Quality:** 1476 vias, 8955.59 mm of copper, 7110 segments. grade.py reproduces all of these numbers.

## 2. Stop rule and the remaining blockers

The best board, d, scored 6 at 02:09Z. Five laps after it were all reverted by route.py's own improvement gate:
- **c**, from a (8): ripped +1V2.
- **e1**, from df (7): plain scoped lap.
- **e2**, from df: ripped the 16 nets the hints named most.
- **f1**, from df: grid 0.05.
- **f2**, from df: whole-board `'*'` pass.

There is one confound: e1–f2 started from df, which is d plus a re-fanout of U30.E8. That re-fanout added a DRC, so df scored 7 (gap 7).

Each remaining blocker was measured on the final board with `check_reachability --pad <pad> --track 0.0762 --clearance 0.09 --via 0.25`:

| net | stranded pads | verdict |
|---|---|---|
| /IO_Banks/U5 (unrouted) | U30.E8, R23.1 | **CAGED** (-38 µm), walled in by routed copper. It was routed in r1, then ripped out of scope and lost its escape stub (gap 2). |
| +1V2 | U30.D8, U30.H8, C18.1 | PASSABLE (+273 / +253 / +184 µm) |
| /IO_Banks/DA0 | U4.5 | PASSABLE (+811 µm) |
| /IO_Banks/Z12_P | J5.8 | PASSABLE (+476 µm) |
| /IO_Banks/Z8_N | J5.17 | COARSE; not re-measured at step 0.01 |
| /VCCPLL1 | R32.1 | PASSABLE (+124 µm) |

Five of the six are router findings: a route exists at the shipped track width. None is claimed unfixable.

## 3. Floors

The 0.8 mm-pitch BGA-121 cannot escape at the authored 0.2/0.2 floors, so the chain ran below them.

- **Chain rules:** track 0.0762, clearance 0.0889 (the project writes 0.09), via 0.25 with 0.15 drill. Hole-to-hole 0.25 and edge 0.5 are the board's own values.
- **route.py:** `Design rules [--escalation fab, --fab-tier auto]: 3 feature(s) on 3 net(s) delivered below the requested size (smallest track width 0.0762 mm)`. The three are power widths requested at 0.2 and delivered at 0.0762: +3V3 over 40.49 mm, GND over 43.39 mm, +1V2 over 13.68 mm. No fab-tier escalation happened.
- **`check_complete --authored-from glasgow_revC.kicad_pcb`:** **UNSOUND**. Track width 0.2 → 0.0762, via diameter 0.5 → 0.25, annular ring 0.1 → 0.05, hole diameter 0.3 → 0.15. 5221 of the 7110 segments are at 0.0762 mm. The Default class clearance went 0.2 → 0.09 and `min_hole_clearance` went 0.25 → 0.09.

## 4. Timeline (UTC; FIRST_CMD 2026-10-06T20:21:31Z)

| time | elapsed | event |
|---|---|---|
| 20:29 | 0:08 | MK1–4 placed at the mechanical.json poses and locked |
| 20:48 | 0:27 | connector layout v1 placed by hand |
| 21:12–21:57 | | six rotation arms run in parallel: U30@0 and U1@90 win |
| 21:57–22:50 | | v1 seeds, repairs and 9 hand decap moves bring decap errors to 0 |
| 22:03–23:01 | | route rehearsal on the unrepaired control seed: blocking 48 (broken 7, DRC 7, floorplan 34) |
| 23:08 | 2:47 | v1 found infeasible (J2 clips MK3's bounding square, gap 1); switch to layout v2 |
| 23:12–00:00 | | v2 seeds; my helper misread logo overlaps (gap 3); switch to v3 with J5 vertical |
| 00:06–00:45 | | v3 seeds (r90 kept), repair, 5 decap nudges |
| **≈00:45** | **4:24** | **first legal placement** `place1`: floorplan 0, buildable, copper-free DRC clean |
| 00:46–01:29 | | pour, bga_fanout 98/98, place_fanout_clearance (11 caps), route.py (41 min) |
| **01:29** | **5:08** | **first routed board** `r1`: blocking 11, 1442 vias |
| 01:41 | 5:20 | lap a: blocking 8 |
| **02:09** | **5:48** | lap d (rip +1V2): **blocking 6** |
| 02:09–02:49 | | laps c, e1, e2, f1, f2 all reverted; stop condition 3 |
| ≈02:52 | 6:31 | board frozen; verifier call 1 |
| ≈03:00 | | one via stamped (§9); verifier call 2 |
| 03:09 | 6:48 | ledger closed and film made; DONE never reached |

## 5. Where the time went

measure.py on this session's own transcript: 6h48m wall in total.

| category | time |
|---|---|
| waiting on my own jobs | 3h47m |
| other tool time | 2h13m |
| model time | 48 min |

308 tool calls; no forbidden entry points.

The main costs:
- **place_seed:** 21–40 min per seed on the shared machine, over three seeding rounds, about 1h45m of wall time.
- **route.py:** a full pass took 41 min; scoped laps took 7–16 min.
- **Layout rework:** gaps 1 and 3 together cost about 2h15m.

## 6. What worked and what didn't

**Worked:**
- **Hand-placing connectors and mechanical parts first.** The seeder alone overlapped J2 and J3 by 88.7 mm² and put J1 7.3 mm off its edge.
- **Running rotation arms in parallel.**
  - On v1: U1@90 cut render crossings from 3134 to 2972, and U30@0 won.
  - On v3: U30@90 won (4598 vs 4664–5227).
- **`--decap-claim-after-ics`:** seed grade errors fell from 34 to 13, or 7 after repair, with mixed effect on crossings.
- **`place_fanout_clearance --intent`:** cleared 7 of 7 cap grazes with decap errors staying at 0. The rehearsal without it had 7 pad-via DRC errors.
- **Run 34's routing recipe** (0.0762/0.0889, 0.25/0.15 vias, layer costs 1/4/2.5/1): first full pass blocking 11 with DRC 0.
- **Scoped laps:** 11 → 8. Ripping +1V2, the blocker named most often in route.py's hints, took it to 6.

**Did not work:**
- `--rip-existing-nets '*'`
- grid 0.05
- a whole-board `'*'` pass
- re-fanning a ball after a rip (it added a DRC error)
- `place_seed --reseat` of decaps (its gate refused them)

**Not done:**
- Power widths were delivered at 0.0762 (see §3).
- USB runs about 50 mm from J1 to U1.
- No diff-pair or impedance routing was declared, so none was done.

## 7. Intents and declarations

- Grading used the given intent.json throughout. All five input sha256 values were re-checked and match.
- Seeding-only intents (the given intent plus rotation blocks): `intent_fa.json`, `intent_fa2.json`, `intent_u30_90.json`, `intent_u30_270.json`. They exist because rank_rotations' arms were run by hand in parallel.
- The decap rule was **not** armed via `--decaps-from`: no placed reference of this design exists. The given intent already carries the 2.5/2.5 decap limits.
- The two KiCad-locked logos were left untouched.

## 8. Tool gaps

`TOOL_GAPS.md` has 13 entries. Each has a repro under `repro/` and a GitHub issue search. Top three:
1. The overlap budget grades the circular MK1–4 courtyards as squares; the exact-shape tools say clean.
2. route.py ripped out-of-scope routed nets without the flag, and U5 lost its escape stub.
3. check_floorplan's overlap error names no pair, and my helper over-counted logos.

The other ten:
4. Decap pin errors are charged to the IC, which `--repair-decaps` cannot fix (issue #1150 covers part of this).
5. rank_rotations runs its arms sequentially.
6. The seeder seats IDC headers perpendicular to the edge and overlapping.
7. A re-fanout adds a DRC error.
8. Decap election counts a shared GND net.
9. Several `--near` ops in one place_pose call do not snap.
10. place_seed refuses a pile once the MK parts are locked.
11. Routing outputs drop the design-brief sibling file.
12. One via under solder was left unstamped; board_score calls it advisory while check_drc fails it.
13. The stop-condition `3` vs `STUCK` wording.

Helpers written: `decap_audit.py`, `overlap_pairs.py`, `stamp_via_type7.py`.

## 9. Verifier verdicts

- **Call 1** (sha c9c16b21…): **VERDICT=FAIL**.
  - It confirmed blocking 6, the six nets, floorplan 0, buildable, MK1–4 exact and 1476 vias.
  - It refuted my "DRC 0": check_drc found 1 VIA-IN-PASTE, a +1V2 via at (117.00, 92.60) with its barrel 0.006 mm into U36.2's paste opening and no protection.
  - Lenses: connectivity FAIL, drc FAIL, spec FAIL.
- **Fix:** I added IPC-4761 Type VII (capping + filling) to that one via. check_drc went to 0 and blocking stayed 6.
- **Call 2** (sha 3ef237a3…): **VERDICT=FAIL**.
  - The diff is confirmed as exactly the two added tokens.
  - check_drc is clean; connectivity (6 nets) and check_complete INCOMPLETE are unchanged.
  - Lenses: connectivity FAIL, drc PASS, spec FAIL.
  - It also corrected its own stacked-copper count from 22 to 21.
