# Board-floor binding: what it costs, measured

`--board-floors` binds a board's own declared fab floors so the router cannot
emit copper beneath them and the writeback cannot rewrite the declaration to
match. It ships **defaulting to `off`**. This is the evidence for and against
flipping that default.

**Nothing here justifies a flip yet.** One board is measured, not the corpus.

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

## Phase B — routing delta, ONE board

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

## Why the default is still `off`

- **One board is not the corpus.** 14 boards bind something; this measured one
  of them. Flipping a floor for every board on one board's evidence is the
  "change a floor and hope" this work exists to remove.
- **~5% completion loss is not nothing.** It may be entirely correct — those
  nets were only routable by going under the declaration — but whether it is
  acceptable is the board owner's call, and it should be made with the corpus
  distribution in hand, not one sample.
- **The two ambiguous boards** (Phase A residue) would bind values nobody can
  prove were authored.

### What the flip commit needs

1. Phase B across all 14 binding boards, `off` vs `authored`, same seeds.
2. Per board: routed/failed **by name**, objects below each bound floor
   (expect > 0 → 0), banner counts (expect > 0 → 0), `nets_blocked`, runtime.
3. A third arm at `--board-floors all`, to price the hard-clearance option so
   nobody proposes it on vibes.
4. Boards that could not be swept: must be 0, or the flip does not land.

---

## An instrumentation defect this measurement caught

The first run reported `escalations_prevented: 5454` — a number describing how
often `fab_floor_ladder` was *called*, not what the floor did. `fab_floor_ladder`
runs on every rescue attempt and every tap. Deduped by (from, to) it is **2**.

Worth recording because it is the same failure the disclosure exists to
prevent: a number nobody can read is not a disclosure, and it would have gone
straight into a flip commit as evidence.
