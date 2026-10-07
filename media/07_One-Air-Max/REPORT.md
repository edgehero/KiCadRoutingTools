<!-- Saved by the fa10 orchestrator, verbatim from the teammate's final message: the harness refused the
     teammate's own write ("Subagents should return findings as text, not write report files"). -->
# REPORT: fa10 board 07, One-Air-Max (`/pcb-free-agent full`)

## 1. Result

**NOT DONE.** `board_score` reports blocking 6 and `check_complete` reports INCOMPLETE. All 6 come from `check_connected` scoring the no-net group "(net 0)". Every real check is clean.

| DONE condition (full mode) | required | measured on `final.kicad_pcb` |
|---|---|---|
| `board_score` blocking | 0 | **6** |
| unrouted | 0 | 0 |
| broken | 0 | **6**: all net 0, 7 pieces; no named net open |
| `check_complete` | DONE | **INCOMPLETE** (only reason: blocking = 6) |
| KiCad's own unconnected check (`kicad_unconnected.py`) | none | 0 unconnected |
| `check_drc --baseline --clearance-margin 0.1` | 0 | 0 |
| KiCad DRC (error severity) | none new | 24, all inside single footprints and present in the input (Q1/Q2 pad 9 vs drain pads, F2 fuse copper, U6 invalid padstacks); 0 introduced |
| `check_assembly` (with and without `--baseline`) | buildable | buildable, blocking 0, courtyard_blocking 0 |
| `check_floorplan --intent` (my intent and the given one) | 0 errors | 0 errors, 35 warnings (all `decap_ungraded`) |
| pad, graphic or keep-out copper off the outline | none | none |
| mechanical.json facts | 6/6 | 6/6, zero offset |
| `check_weird` / `check_orphan_stubs` | clean | clean |

- **blocking_by:** assembly 0, broken 6, drc 0, floorplan 0, undersized 0, unrouted 0.
- **Not graded:** impedance, length and net_widths. The board declares none of them, so they are unexamined rather than passed.
- **Quality:** 357 vias, 4825.88 mm copper, 3259 segments.
- **Independent grade (`grade.py`):** done false, blocking 6, unrouted 0, broken 6, drc 0, vias 357, buildable, floorplan errors 0.

## 2. Stop rule and remaining blockers

The ledger is closed with `--stop-condition 4`. A classification row records the measurement first; the final row carries verifier 2's three verdict files.

Both of the skill's stop paths fired, and both are measured:
- **DONE will not come.** Every routed board since r01 (05:38Z) scores broken 6, all from net 0. The same group exists on the untouched input board (6 pieces there), so routing and placement cannot change it.
- **The via optimisation ran out.** After the first board that was clean on every real check (r02f, 471 vias), each round re-routed the board at a different setting:

  | round | change | result |
  |---|---|---|
  | R1 | In2 (the solid GND layer) forbidden | worse: 481 vias, 4 nets failed |
  | R2 | `--via-cost 150` | 402 vias (-14.6%) |
  | R3 | `--via-cost 300` | 386, then 385 after a fix (-4.2%) |
  | R4 | `--via-cost 600` | 357 (-7.3%) |
  | R5 | `--via-cost 1200` | 366 before finishing: no cut |
  | R6 | `--via-cost 600`, In1 as cheap as F/B | 353 with /SCL open; the finishing pass was reverted by route.py's own improvement check |

  R5 and R6 both cut less than 5%, so optimisation stopped.

**The remaining blocker, by name:** net 0, 7 pieces:
- No-net plated holes: BAT1 (109.81, 59.97), USB1 (131.43, 117.74) and (137.22, 117.74), DC1 (193.35, 118.45) and (189.35, 118.45).
- No-net exposed pads: Q1 pad 9 (142.44, 79.90) and Q2 pad 9 (136.64, 84.13).
- Net-0 footprint copper: JP2 (4 segments), JP3 (4), F2 (1).

Measured with `check_connected` on both the final and the input board, and confirmed by verifier 2.

## 3. Floors

**What I asked the router for:** Default track 0.25 mm, clearance 0.1 mm (the board's class), vias 0.6/0.3 mm, power widths 0.3–0.5 mm. Fab tier auto, escalation fab.

**route.py's `Design rules` lines for the final board's chain:**
- r12: `230 feature(s) on 42 net(s) delivered below the requested size (smallest track width 0.1963 mm, smallest via diameter 0.25 mm); 128 fab-tier escalation(s) to advanced`
- r15: `11 feature(s) on 4 net(s) ... (smallest track width 0.2 mm, smallest via diameter 0.25 mm); 5 fab-tier escalation(s) to advanced`

**`check_complete --authored-from` input board: UNSOUND, report only.** Floors lowered:
- Via diameter 0.3 → 0.25 mm: 9 vias at 0.25/0.15 and 3 at 0.3/0.15.
- Hole diameter 0.508 → 0.15 mm: every via drill is below 0.508. The board's own Default class via (0.8/0.4) already broke that floor.
- The project's minimum hole clearance went 0.127 → 0.1.

**Fab advisory:** 163–166 vias sit in same-net pad or paste openings and are not protected. The KiCad 9 file format cannot declare filled-and-capped vias, so the fab drawing must call for them (IPC-4761 Type VII).

## 4. Design decisions and board edits (disclosed)

**`intent_v2_u5r180.json`** is the given `intent.json` plus:
- **U1** (the ESP32-C6 module) fixed at (179.5, 66.75), rot 180, back side: antenna on the north edge, inside the pour-free north-east area, which is exactly module-sized.
- **DC1** (barrel jack) at (189.6, 118.2), rot 180, front: opening faces the east edge.
- **PWR_SW1** (slide switch) at (178.0, 116.8), rot 0, front: actuator at the south edge.
- Three keep-outs:
  - the 18650 holder's drawn body on the front side;
  - BAT1's pad box on the front side;
  - U1's module body on the back side.
- U5 rotation 180.

**Why:**
- BAT1 counts as a "container", so its courtyard is ignored. With the given intent alone, the seeder put DC1, PWR_SW1, Solarpower1, C10 and C13 inside the battery holder, and placed U1 over SW1 and USB1.
- U1 has no courtyard and no fab outline, so its 6 mm antenna was invisible to placement.

**Edits to the board file** (none touch the outline, a pad or a footprint's copper):
- Courtyards added to 196 footprints, each drawn from its own fab body plus pads, +0.1 mm.
- Rule areas: ANT_KEEPOUT over the antenna (tracks, vias and pour; all 4 layers), and USB_SHIELD_NOVIA_L and _R (vias only) over USB1's filled shield copper.
- One locked 0.2 mm /SCL segment. It turned out to lie on top of an existing segment: redundant and harmless.

**Decap rule:** the organiser's intent already armed it (53 tethers, limit 4.55 mm). The final board has 0 decap errors. The 35 `decap_ungraded` warnings are caps beyond the rule's 5 mm search radius (the charger's caps sit 8–15 mm from U5), so they were never measured.

## 5. Timeline (UTC; FIRST_CMD 03:14:20)

- 03:18 – six mechanical parts placed and locked.
- 03:26–04:47 – rotation ranking of U5: four seeds plus two full-board probe routes. The probes gave 0° 2 failures, 180° 3, from one seed each.
- 04:00–04:55 – finding why every seed had overlapping bodies: 8 seeds, all NOT BUILDABLE under `--baseline`.
- **04:58** – first legal placement (`p03_place`), 1 h 44 min in.
- **05:38** – first fully routed board (r01), 2 h 24 min in: route.py's tally 120/120, KiCad 0 unconnected.
- **06:08** – first board clean on every real check (r02f, 471 vias), 2 h 54 min in.
- 07:19 – r06f, 402 vias.
- 08:03 – r07f, 386 vias.
- 08:05–08:19 – **verifier 1: FAIL** (the net-0 count plus a real short).
- 08:35 – short fixed (r14p, 385 vias).
- **08:49** – best board r15u, 357 vias.
- 09:24–09:37 – rounds 5 and 6, no cut; stop rule fired.
- 09:38 – final board frozen (FINAL.sha256, DONE marker).
- 09:39–09:54 – **verifier 2: FAIL** (the net-0 count only; DRC check passed).
- 09:58 – film rendered; about 10:00 close-out.
- Formal DONE: never reached.

## 6. Where the time went

From `measure.py` on this session's own transcript at 09:44Z (6 h 30 min):

| category | time |
|---|---|
| waiting on background jobs | 2 h 50 min |
| foreground tools | 2 h 47 min |
| model time | 53 min |

- **Background jobs** were mostly route.py passes of 30–45 minutes each, of which the routing loop itself was 35–63 s. Cleanup, the plane finalize and reconciliation take the rest. The two probe routes took about 25 minutes each.
- **Foreground tools** include 31 `board_score` runs and many checker runs; `measure.py` also counted 14 `place_seed` runs.

## 7. What worked and what didn't

**What worked:**
- **Courtyards drawn from each part's fab body:** seeds went from 4–9 body-overlap pairs (NOT BUILDABLE) to 0 on the back side.
- **Via cost as the via lever**, each run finished and cleaned up:

  | `--via-cost` | vias |
  |---|---|
  | 75 (default) | 471 |
  | 150 | 402 |
  | 300 | 386 |
  | 600 | 357 |
  | 1200 | no gain (366, unfinished) |
- **Short finishing passes on just the failing nets, with GND and +3V3 included:** they closed 2–5 nets in 2–5 minutes. Leaving the pours out once cut +3V3 into 3 pieces (r08).
- **KiCad's own DRC as a standing check** after verifier 1 found the short. A clean board has exactly the 24 errors that sit inside single footprints.

**What didn't:**
- **Forbidding In2, the GND layer (r03):** 4 failed nets, 481 vias.
- **Keeping vias out of pads (`--same-net-pad-clearance 0.1`):** r05 failed 9 nets against 2 at the same via cost. Five finishing passes got it down to one open net, /Solar_module/SYS, boxed in at U5 even with route.py's suggested rip set. I abandoned that line.
- **U5 rotation ranking:** inconclusive, one seed per angle. I kept 180 (652 vs 656 crossings).
- **`--decap-claim-after-ics`:** it claimed 41 caps, but the seed had 9 body-overlap pairs, so I didn't keep it.
- **`place_seed --repair` and `--reseat` for body overlaps:** "0 violators" and "GATE REFUSED".
- **My dangling-end pruning:** it broke /SCL once. `check_weird` reported a live mid-segment T-junction as a free end. I reverted to pruning dangling vias only.

## 8. Tool gaps (detail and repro commands in TOOL_GAPS.md)

| # | gap |
|---|---|
| 1 | `check_connected` counts net 0 once footprint copper exists → `board_score` can never reach blocking 0 (also on the input). Related: #497, #908. |
| 1b | Filled board graphics are modelled by their outline only → route.py put a +3V3 via inside USB1's exposed shield copper; `check_drc`, `check_connected` and `board_score` all said clean, only KiCad DRC and the verifier caught it. Related: #908. |
| 2 | Placement tools use the pad box for parts without a courtyard; `check_assembly` grades the drawn body → every seed NOT BUILDABLE, and repair/reseat can't see it. Related: #896. |
| 3 | `board_score` and the verifier's `check_assembly` call (without `--baseline`) can't see body-overlap pairs that `--baseline` gates; BAT1 is waived as a "container". |
| 4 | route.py's plane finalize joins +3V3 islands with up to 2.0 mm tracks on the In2 GND plane (228 +3V3 segments there); the only lever against it costs completion. |
| 5 | route.py leaves duplicate same-net segments (240), which fail `check_complete`; one duplicate hid a dangling end. Related: #162. |
| 6 | Dead +3V3 branches survive route.py's finalize; no command-line tool removes named copper. |
| 6b | `check_weird` calls a live mid-segment T-junction a "free end" (removing it disconnected /SCL). Related: #1167. |
| 7 | `place_seed` refuses with "looks PLACED" right after the skill's own recipe of placing the fixed parts first. |
| 8 | The ESP32 module has no courtyard or fab outline, and nothing in the repo creates a copper rule area. |
| 9 | Via-in-pad is the default (165+ vias in pads, unprotected); keeping vias out of pads cost 7 nets here. |
| 10 | route.py spends about 98% of each step after routing. |
| 11 | Minor: `board_score --quiet` still prints about 580 KB to stdout; `place_pose --strict-legal` grades the whole board, so it refuses every pose on a pile. |

Helpers, each one explained in TOOL_GAPS.md: `add_fab_courtyards.py`, `courtyard_nudge.py`, `add_rule_area.py`, `dedupe_segments.py`, `remove_copper.py`, `prune_dangling_vias.py`, `clean_and_check.sh`.

## 9. Verifier verdicts (2 of 3 calls used)

- **`verdict_1.txt` (r07f): FAIL.** Blocking 6 from net 0, plus a **real short**: a +3V3 via at (129.70, 118.80) inside USB1's filled shield copper on Net-(C1-Pad2). KiCad reported it as a short and 6 solder-mask bridges. Verdict files: connectivity FAIL, drc FAIL, spec FAIL. **Fixed** in r14p and in every later board.
- **`verdict_2.txt` (final board): FAIL** on the literal rule only: blocking 6, entirely from net 0, no named net open, KiCad 0 unconnected.
  - Verdict files: connectivity FAIL (evidence 6), drc PASS, spec FAIL (`check_complete` INCOMPLETE; mechanical 6/6).
  - It verified all four of my claims: net-0 attribution, no vias in the shield rule areas, nothing in the antenna keep-out, and the locked /SCL segment.
  - Advisories: 163 vias in paste openings without protection; the 196 added courtyards.
