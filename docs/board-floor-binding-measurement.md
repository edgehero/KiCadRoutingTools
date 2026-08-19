# Board-floor binding: what it costs, measured

`--board-floors` binds a board's own declared fab floors so the router cannot
emit copper beneath them and the writeback cannot rewrite the declaration to
match. It defaults to **`authored`** as of the flip commit. This is the evidence that
decided that.

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

## Why the default flipped

The two failure modes are not symmetric, and that is the whole argument:

- `off` ships a board the fab cannot make while **every instrument calls it
  clean**. That is silent wrongness, and it is what run 22 did.
- `authored` fails four nets **loudly and by name**, on one of three boards.

This repo's doctrine prefers loud incompleteness to silent wrongness
everywhere else; the default now matches it. And the flip is one flag to
reverse (`--board-floors off`), whereas a board shipped under the ratchet is
discovered at the fab.

Binding is inert on **19 of 33** boards (18 declare nothing, 1 is pure stock),
so the change reaches only boards whose author said something.

## What is still unmeasured, and should be said out loud

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
