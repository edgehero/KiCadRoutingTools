#!/usr/bin/env python3
"""Stage a BLIND perturbed subject: damaged board here, truth over there.

    python3 -X utf8 tests/stress/stage_blind.py SRC.kicad_pcb WORKDIR TRUTHDIR

The run may open WORKDIR/board.kicad_pcb and nothing else. TRUTHDIR gets the
control, the perturbation record and the draw, and is not read until the board
is frozen. Pair it with `fence_audit.py --mode create` immediately afterwards.

Disclosure discipline, tightened against the leaks earlier runs found:

  * The writer's own "Modified N footprint positions" line is a dose/block
    tell, so every call runs with stdout captured and discarded.
  * Run 10 disclosed `PERTURBED BLOCK N` because its report's `home /N`
    denominator needed it, and a watcher correctly called that a leak: a
    `swap` draw unions two disjoint blocks and so reports a distinctly larger
    N than the other kinds. This script discloses NOTHING about the block. The
    denominator is read from the record at AUDIT time, when the fence is
    already down; the run itself is scored on the routed outcome, which needs
    no truth at all.
  * There is deliberately NO redraw gate. Run 10 used `home_frac <= 0.20`,
    an asymmetric filter that bites mainly on `scatter` and is therefore
    itself informative about the kind.

THE DOSE IS SCALED TO THE BOARD, and this file used to only claim that.
The previous version called `placement.perturb.max_feasible_dose(pcb)` with one
positional argument against a signature of `(state, members, u, *, grid_step,
dose_cap, ...)`. Binding failed on ARITY, before any board data was touched --
so the `except` was not a guard, it was the ONLY path, and a hard-coded 30.0 mm
was the scale for every board on earth. The docstring's "a band of the board's
own max feasible dose" was not unverifiable; it was always false.

It cannot be fixed by correcting the arity either: `max_feasible_dose` answers
"how far can THIS block travel along THIS direction, up to dose_cap" -- it is
bounded by the cap you pass, so it cannot be used to DERIVE a dose, and it
needs a block and a direction that do not exist until after the draw. There is
no board-maximum mode to call.

So the scale comes from a real board property instead: the outline's smaller
span, which is what actually bounds how far a part can move and still be on
the board. `perturb()` independently clips whatever is asked for
(`on_overflow='clip'`), and the APPLIED dose is recorded in the record as
`max_feasible_dose_mm` / `clipped` -- so the truth dir holds what landed, not
what was requested.
"""
import contextlib
import io
import json
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from kicad_parser import parse_kicad_pcb  # noqa: E402
import placement.perturb as P  # noqa: E402

#: Fraction of the board's smaller span a single draw may ask for. The low end
#: has to be material (a 1 mm nudge on an 80 mm board is not a recovery test)
#: and the high end has to leave the board recognisable.
DOSE_BAND = (0.06, 0.22)


def board_scale_mm(pcb):
    """The board's smaller outline span, or None when it declares no outline.

    This is a REAL board property, unlike the constant it replaces. It is the
    dimension that actually bounds a displacement: a part pushed further than
    this along the short axis is off the board whatever the dose says.
    """
    b = getattr(pcb.board_info, 'board_bounds', None)
    if not b:
        return None
    w, h = abs(b[2] - b[0]), abs(b[3] - b[1])
    return min(w, h) if w > 0 and h > 0 else None


def main(src, workdir, truthdir):
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(truthdir, exist_ok=True)

    rng = random.Random(int.from_bytes(os.urandom(16), 'big'))
    kind = rng.choice(P.KINDS)
    seed = int.from_bytes(os.urandom(4), 'big')

    # The AUDIT reference: a plain copy of the source. The perturbation writes
    # its own dose-0 control below, straight into the truth dir -- it must
    # never be derived from `out`, which is what put the human placement inside
    # the work dir in the first place (run-12 Tier 0).
    control = os.path.join(truthdir, 'control.kicad_pcb')
    shutil.copyfile(src, control)
    for ext in ('.kicad_pro', '.kicad_prl'):
        sib = os.path.splitext(src)[0] + ext
        if os.path.exists(sib):
            shutil.copyfile(sib, os.path.join(truthdir, 'control' + ext))

    out = os.path.join(workdir, 'board.kicad_pcb')

    # Computed under capture -- the scale is itself a size tell.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        pcb = parse_kicad_pcb(src)
        scale = board_scale_mm(pcb)
        if scale is None:
            raise SystemExit(
                'stage_blind: this board declares no usable outline, so a '
                'dose cannot be scaled to it. Refusing rather than falling '
                'back to a constant -- a silent constant is what this script '
                'shipped for three runs.')
        dose = max(3.0, scale * rng.uniform(*DOSE_BAND))
        # control_out FENCES BOTH HALVES OF TRUTH IN ONE CALL. Without it the
        # tool writes `board.control.kicad_pcb` -- the human placement, pose
        # for pose -- and `board.perturb.json` (it embeds `original_poses`)
        # beside the damaged board, INSIDE the work dir the run then reads.
        rec = P.perturb(src, out, kind=kind, dose_mm=dose, seed=seed,
                        write_record=True,
                        control_out=os.path.join(truthdir,
                                                 'perturbed.control.kicad_pcb'))

    with open(os.path.join(truthdir, 'draw.json'), 'w', encoding='utf-8') as f:
        json.dump({'kind': kind, 'dose_mm': dose, 'seed': seed,
                   'board_scale_mm': scale, 'dose_band': list(DOSE_BAND),
                   'source': src}, f, indent=1)
    written = os.path.join(truthdir, 'board.perturb.json')
    want = os.path.join(truthdir, 'perturbed.perturb.json')
    if os.path.exists(written):
        shutil.move(written, want)
    for cand in (os.path.splitext(out)[0] + '.perturb.json',):
        if os.path.exists(cand):
            shutil.move(cand, want)
    if not os.path.exists(want):
        with open(want, 'w', encoding='utf-8') as f:
            json.dump(rec, f, indent=1)

    # The ONLY disclosure: board shape, which is visible on the board anyway.
    # NOT the scale, the band, the dose, the kind, the seed or the block.
    p = parse_kicad_pcb(out)
    b = p.board_info.board_bounds
    print(f"parts {len(p.footprints)} | nets "
          f"{len([n for n in p.nets.values() if n.name])} | copper layers "
          f"{len(p.board_info.copper_layers)} "
          f"({', '.join(p.board_info.copper_layers)}) | bbox "
          f"{b[2]-b[0]:.1f} x {b[3]-b[1]:.1f}")
    print(f"segments {len(p.segments)} | vias {len(p.vias)}")
    print("damage applied; kind/dose/seed/block written to the truth dir "
          "and disclosed nowhere")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__.strip().splitlines()[2].strip())
    main(sys.argv[1], sys.argv[2], sys.argv[3])
