# Board-floor binding: what it costs, measured

`--board-floors` binds a board's own declared fab floors so the router cannot
emit copper beneath them and the writeback cannot rewrite the declaration to
match. It ships **defaulting to `off`**. This document is the evidence for and
against that -- including a flip that was made, measured, and REVERTED.

---

## Phase A — authority, all 33 corpus boards (no routing)

```
bind something under `authored` : 14 of 33
bind nothing                    : 19  (18 have no .kicad_pro; 1 is pure stock)
key count by source             : fab_floor_origin 30, board rules 7,
                                  board provenance 3
```

The distribution is the argument for the authority rule. **30 of 40 bound keys
come from `fab_floor_origin`, not from the project's current rules block** —
because those projects are outputs of this toolchain, and their rules block is
the relaxed writeback. `fanout_output1.kicad_pro` currently declares via 0.3 /
drill 0.2 while its own origin records 0.45 / 0.25; binding the rules block
would bind a number the router itself wrote.

### The honest residue

`qfn_fanned_out` and `routed_output` bind from `board rules` with **no origin
key**: non-stock values that cannot be shown to be authored rather than
ratcheted by an older toolchain. Two boards. Nothing in the tree distinguishes
them, and the flip decision should account for them rather than smooth them
over.

---

## Phase B — routing delta, ALL THREE clean subjects

Only **3 of the 14** binding boards are copper-free and therefore clean routing
subjects: `tigard`, `watchy`, `interf_u_plane`. The other 11 are intermediate
tool outputs that already carry copper, so re-routing them measures the copper
already there rather than the flag. "14 boards" would overstate the evidence
base by 4x; the honest Phase B is 3 routing subjects plus a writeback check on
the rest.

| board | arm | rules lowered below declaration | routed | failed |
|---|---|---|---|---|
| watchy | off | 2 | 52 | 0 |
| watchy | **authored** | **none** | **52** | **0** |
| interf_u_plane | off | 1 | 109 | 0 |
| interf_u_plane | **authored** | **none** | **109** | **0** |
| tigard | off | 4 | 85 | 0 |
| tigard | **authored** | **none** | 81 | 1 |

**3 of 3 stop lowering their declaration. 2 of 3 cost nothing at all.**

### The detail on tigard

Subject: `wk/run22/tigard/frozen.kicad_pcb` — run 22's own frozen placement,
which declares (with `floor_provenance`) min_track_width 0.15 /
min_via_diameter 0.5 / min_via_drill 0.25 / min_clearance 0.15. Both arms
identical apart from the flag; fresh output paths.

```
route.py <in> <out> --nets '*' --clearance 0.15 --board-floors {off|authored} --deadline 600
```

### What binding fixes

| | `off` (today) | `authored` |
|---|---|---|
| output `.kicad_pro` rules lowered below the declaration | **all four** | **none** |
| smallest track emitted | 0.0889 | **0.15** |
| smallest via / drill emitted | 0.25 / 0.15 | **0.5 / 0.25** |
| `FAB FLOOR RELAXED` banner | fires (18 of 197 objects below the original 0.5 via) | silent |
| `GRADING FLOOR RELAXED` banner | fires (clearance 0.15 → 0.1) | silent |

The `off` arm reproduces run 22's defect exactly: sub-declaration copper, and a
project rewritten so every checker grades it clean. The `authored` arm emits
**zero objects below the declared floors**.

### What binding costs

| | `off` | `authored` |
|---|---|---|
| `routed_single` | 85 | **81** |
| `failed_single` | 0 | **1** (`/BD7`) |

Routed in `off` but not in `authored`: **`/BD5`, `/BD7`, `/CLK`, `GND`.**

Four nets whose terminal-escalation ladder the floor emptied (net ids 7, 11,
22, 85 — each at `track_width 0.15, floor 0.15, via_size 0.5`, i.e. already at
the declaration with nowhere left to march).

That is the real trade: **4 of 85 nets on this board**, in exchange for not
shipping copper the fab cannot make while every instrument calls it clean.

---

## The flip, and why it was reverted

On the evidence above the default WAS flipped to `authored`. The argument was
asymmetry of failure modes: `off` ships a board the fab cannot make while every
instrument calls it clean, while `authored` fails a few nets loudly and by
name -- and this repo prefers loud incompleteness to silent wrongness.

**The full suite refuted it.** Three tests went red, and two of them are the
very boards that bind:

```
test_tigard_usb_diff            [underpad-scoped] coupled route is DRC-clean   FAIL
                                [underpad-scoped] final board is DRC-clean     FAIL
test_watchy_diff_hybrid_escape  hybrid-escaped USB_D has DRC violations        FAIL
test_obstacle_map_balance       (also red under the flip)
```

Note what the tigard failure says: the `[bare]` arm still passes, and only the
`[underpad-scoped]` arm fails. **Underpad and hybrid escapes legitimately need
sub-declaration vias.** Forcing tigard's declared 0.5 via into an underpad
region does not make the net fail honestly -- it puts a bigger barrel where a
smaller one fitted and produces DRC VIOLATIONS.

That is not loud incompleteness. It is shipping violations, which is the thing
the asymmetry argument was supposed to avoid. The argument was not wrong about
asymmetry; it was wrong because it rested on PLAIN ROUTING measurements and
never exercised the fanout paths.

Default reverted to `off`. Both tests pass again.

### The escape-via question -- DECIDED: not exempt

The open question was whether fanout escape vias are a different process
question from ordinary routing, so that the clamp should skip them. **They are
not, and it should not.** Measured rather than argued:

The `[underpad-scoped]` failure is **one VIA-VIA pair**, and the arithmetic is
the whole story. tigard's U3 escape puts two vias 0.6 mm apart -- the QFN's pad
pitch, a property of the PART, not a routing choice:

| via size | edge-to-edge gap | vs the 0.15 clearance |
|---|---|---|
| 0.45 (requested) | 0.15 | exactly meets it |
| 0.5 (declared, pinned up to) | 0.10 | short by **0.050** |

`check_drc` reports `Overlap: 0.050mm` at `(43.80,59.60)` / `(43.80,60.20)`.
Nothing else on the board fails; `[bare]` and `[stub-nonscoped]` stay clean.

**Not exempt**, for three reasons:

1. An escape via is drilled and plated by the same process as any other via.
   Via-in-pad differs in **finishing** -- filled and capped, IPC-4761 Type VII
   -- which this repo already models separately (`via.tenting_attrs`,
   `fab_notes.print_via_in_pad_note`). Finishing is not drill capability, and
   the "via-in-pad IS a finer capability" line above was an assumption, never a
   measurement.
2. Exempting would let `authored` emit sub-declaration copper on exactly the
   path that produced run 22's defect, which is the thing the flag exists to
   prevent.
3. The failure is the flag WORKING. tigard cannot escape U3 underpad at its own
   declared 0.5 via. That is a real fab constraint being discovered, and
   discovering it is the point.

So binding is incompatible with an underpad escape on a board whose declared
via is coarser than the part's pitch allows, and **the flag's help now says
so**. Route such an escape with `--board-floors off`, or correct the
declaration.

### The instrumentation defect this uncovered

The pin-up warning said the floor came from *"the selected `--fab-tier`"* and
advised *"Pass `--fab-overrides` to declare a smaller fab capability"*. Under a
board binding both halves are wrong, and the advice is **provably useless** --
the board clamp is applied on top of the tier and its overrides:

```
no board floor, override 0.35 : 0.35
board floor 0.5, SAME override: 0.5
```

Sending the user to a flag that cannot work is the same class of lie as an
accepted-but-ignored flag. The message now names the board and its provenance
and offers `--board-floors off`; the unbound path keeps the original wording,
because there the tier really is the source. Pinned by
`tests/test_run22_board_floor_binding.py`.

### Where the flip stands

Still `off`, and this decision does not by itself change that. What it removes
is the *unknown*: the escape interaction is now measured and documented rather
than blocking. A future flip must still re-run `test_tigard_usb_diff`,
`test_watchy_diff_hybrid_escape` and `test_obstacle_map_balance` under
`authored` and accept -- explicitly -- that the underpad arm reports a real
constraint rather than passing. `off` remains the honest default: the
protection is available to any run that asks for it, and the disclosure banners
fire either way.

## What is still unmeasured, and should be said out loud

- **The fanout/underpad interaction, above.** This is now the blocker for any
  future flip, and it was invisible to three boards' worth of plain-routing
  measurement.
- **`--board-floors all` was never routed.** It binds stock values and the
  netclass, and it clamps clearance -- which collapses the rescue clearance
  ladder. Nobody should propose it as a default without routing it first.
- **Two boards bind on ambiguous authority.** `qfn_fanned_out` and
  `routed_output` declare non-stock rules with no `fab_floor_origin`, so they
  cannot be shown to be authored rather than ratcheted by an older toolchain.
  Both already carry copper, so the binding affects only future routes on them.
- **11 of the 14 binding boards were never routed** because they are not clean
  subjects. Their writeback behaviour is checked; their routing behaviour is
  not.

---

## An instrumentation defect this measurement caught

The first run reported `escalations_prevented: 5454` — a number describing how
often `fab_floor_ladder` was *called*, not what the floor did. `fab_floor_ladder`
runs on every rescue attempt and every tap. Deduped by (from, to) it is **2**.

Worth recording because it is the same failure the disclosure exists to
prevent: a number nobody can read is not a disclosure, and it would have gone
straight into a flip commit as evidence.
