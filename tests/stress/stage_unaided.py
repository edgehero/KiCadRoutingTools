#!/usr/bin/env python3
"""Stage a board for an UNAIDED placement run: netlist in, nothing else.

    python3 -X utf8 tests/stress/stage_unaided.py SRC.kicad_pcb WORKDIR TRUTHDIR

`--kind pile` was the closest thing to this and it is not close enough. Its
own docstring says "this kind exists to produce the place-from-scratch task"
(`placement/perturb.py:368-382`) and it hands over:

  * EVERY free part's original rotation (`:389-391` writes
    `'new_rotation': state.parts[r].rot`). Measured on splitflap_driver:
    65 of 65 preserved, 32 of them non-zero.
  * every pad-less and every `(locked yes)` ref at its true x, y AND rotation,
    because `portfolio.free_refs` skips those and `_all_at_current` then
    writes them where they were.

And `fence_audit` cannot see any of it: `pose_match` counts a ref only when
position AND rotation are inside tolerance, so on a pile the positions are all
wrong, `match_frac` is 0.0000, and the verdict is CLEAN. Run 19's fence exited
CLEAN, 0 on exactly this.

So this stager does three things the pile kind does not:

  1. **Rotation 0 for every non-exempt part.** An angle is a design decision
     as much as a position; handing it over is handing over the answer.
  2. **Exemptions are DECLARED, per ref, with a reason**, in a
     `mechanical.json` the run may read. Some inheritance is legitimate -- a
     mounting hole's position is a mechanical fact, not a placement choice --
     but the difference between a benchmark input and a leak is whether it is
     written down. Silent inheritance is what `--kind pile` does.
  3. **The source is recorded by HASH, not by path.** `stage_blind.py:204`
     writes `'source': src` into the truth dir, naming a file whose original
     placement is one `Read` away. The mapping lives in the truth dir instead.

Truth goes to a SIBLING directory, never a child of the work dir -- the fence
audit recurses, and `perturb()`'s own default writes the control beside the
damaged board, which is how a run gets fenced on paper and open in fact.

Exit codes: 0 staged, 2 usage/IO, 3 the board cannot be staged (no outline).
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
for _p in (ROOT, os.path.join(ROOT, 'py_router'),
           os.path.join(ROOT, 'py_tools'), os.path.join(ROOT, 'py_placer')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = 1


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def classify_exempt(pcb_data, pcb_file=None):
    """{ref: (x, y, rot)} plus {ref: reason} for the parts a real new board
    would genuinely know the position of.

    A PROJECTION of `placement.part_class.mechanical_parts`, not a second
    taxonomy. It used to be the implementation, which meant the only thing in
    the tree that could name a board's mechanical parts lived in a stress
    harness -- so `board_brief` could not answer "where do the fixed parts
    go?" and an unaided author had to read `mechanical.json`, an artifact no
    product path emits. Same classifier, two readers.
    """
    from placement.part_class import mechanical_parts
    found = mechanical_parts(pcb_data)
    refs = {r: tuple(v['at']) for r, v in found.items()}
    reasons = {r: v['reason'] for r, v in found.items()}
    return refs, reasons


def read_mechanical(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def stage(src, out_board, truth_dir=None, mechanical_out=None):
    """Write the unaided board; return the mechanical declaration.

    Everything free lands on ONE coordinate at ROTATION 0. The single
    coordinate is what `placement_state.assess_placement` needs to call the
    board unplaced (`duplicate_fraction >= 0.5` AND `distinct_positions <=
    max(3, 0.1n)`), which is what makes the placement tools accept it as a
    from-scratch task rather than refusing it as a damaged placement.
    """
    from kicad_parser import parse_kicad_pcb
    from placement.writer import write_placed_output
    from placement.portfolio import copy_siblings

    pcb = parse_kicad_pcb(src)
    bi = pcb.board_info
    if bi.board_bounds is None:
        raise ValueError("the board has no Edge.Cuts outline, so there is "
                         "nothing to stage a placement against")
    x0, y0, x1, y1 = bi.board_bounds
    cx, cy = round((x0 + x1) / 2.0, 6), round((y0 + y1) / 2.0, 6)

    exempt, reasons = classify_exempt(pcb, src)
    placements = []
    for ref, fp in sorted(pcb.footprints.items()):
        if ref in exempt:
            ex, ey, erot = exempt[ref]
            placements.append({'reference': ref, 'new_x': ex, 'new_y': ey,
                               'new_rotation': erot})
        else:
            placements.append({'reference': ref, 'new_x': cx, 'new_y': cy,
                               'new_rotation': 0.0})
    write_placed_output(src, out_board, placements)
    copy_siblings(src, out_board)

    doc = {'schema': SCHEMA, 'kind': 'mechanical-declaration',
           'refs': exempt, 'reasons': reasons,
           'note': 'the ONLY poses carried over from the source. Everything '
                   'else is at the board centre at rotation 0. A run may read '
                   'this; it is an input, not a leak, BECAUSE it is written '
                   'down.'}
    mech = mechanical_out or os.path.join(os.path.dirname(out_board),
                                          'mechanical.json')
    with open(mech, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=True)

    if truth_dir:
        os.makedirs(truth_dir, exist_ok=True)
        control = os.path.join(truth_dir, 'control.kicad_pcb')
        shutil.copyfile(src, control)
        copy_siblings(src, control)
        with open(os.path.join(truth_dir, 'stage.json'), 'w',
                  encoding='utf-8') as f:
            # The source by HASH. stage_blind records `'source': <path>`,
            # which names a file whose original placement the run can simply
            # open; the mapping belongs on this side of the fence.
            json.dump({'schema': SCHEMA, 'kind': 'unaided-stage',
                       'source_sha256': sha256_file(src),
                       'source_basename': os.path.basename(src),
                       'staged_sha256': sha256_file(out_board),
                       'exempt_refs': sorted(exempt),
                       'piled_at': [cx, cy],
                       'note': 'source recorded by hash, not by path'},
                      f, indent=1, sort_keys=True)
    return doc


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Stage a board for an unaided placement run.")
    p.add_argument("src")
    p.add_argument("workdir")
    p.add_argument("truthdir", nargs='?')
    a = p.parse_args(argv)

    if a.truthdir and os.path.abspath(a.truthdir).startswith(
            os.path.abspath(a.workdir) + os.sep):
        p.error("TRUTHDIR must be a SIBLING of WORKDIR, never a child -- the "
                "fence audit recurses into the work dir, so truth inside it "
                "is inside the fence")
    os.makedirs(a.workdir, exist_ok=True)
    out = os.path.join(a.workdir, 'board.kicad_pcb')
    try:
        doc = stage(a.src, out, truth_dir=a.truthdir)
    except ValueError as e:
        print(f"stage_unaided: {e}", file=sys.stderr)
        return 3
    except OSError as e:
        print(f"stage_unaided: {e}", file=sys.stderr)
        return 2

    # Disclosure discipline, from stage_blind: say the SHAPE of the board and
    # nothing about what was staged away.
    print(f"Staged {out}")
    print(f"  {len(doc['refs'])} ref(s) declared mechanical and carried at "
          f"their source pose; everything else at the board centre, "
          f"rotation 0")
    for ref in sorted(doc['refs'])[:8]:
        print(f"    {ref}: {doc['reasons'][ref]}")
    if a.truthdir:
        print(f"  truth in {a.truthdir} (a sibling; nothing in the work dir "
              f"names the source)")
    print("JSON_SUMMARY: " + json.dumps(
        {'board': out, 'exempt': len(doc['refs']),
         'mechanical': os.path.join(a.workdir, 'mechanical.json')},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    # In LEVER_REGISTRY, so it must DECLARE -- an entry that writes
    # poses without declaring makes an armed regime refuse the engine
    # itself, which is the failure the registry exists to prevent.
    from placement.provenance import declare_lever
    with declare_lever('stage_unaided.py', sys.argv):
        sys.exit(main())
