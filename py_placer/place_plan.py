#!/usr/bin/env python3
"""place_plan: run a placement plan against a board.

The plan is what an AI writes instead of a per-board python script. It states
the arrangement -- a pitch, a mirror axis, an origin solved against the
outline, a satellite's offset from its parent -- and every statement is seated
through `seeder._try_place`, so the board that comes out is legal by the same
gate `place_seed` uses and by no other.

    python3 place_plan.py board.kicad_pcb plan.json -o seeded.kicad_pcb
    python3 place_plan.py board.kicad_pcb plan.json --dry-run --json r.json
    python3 place_plan.py --print-schema        # the authoring contract

Exit codes, following the placement family:
    0   every named part seated
    2   bad arguments, or a plan this tool cannot execute as written
    3   the board is not in a state this tool can work on
    4   the plan ran and parked at least one part

4 rather than 1 because a caller has to tell "the plan did not fit this board"
from "the tool is broken", and 3 is already the family's board-state code.

A parked part is reported with its target, its budget and the reason, and the
board is still written -- the same contract `place_seed` has for `unseated`:
a partial result you can look at beats a refusal you cannot.
"""
import argparse
import json
import os
import sys

import _path  # noqa: F401  (py_placer -> py_router/py_tools on sys.path)

from kicad_parser import parse_kicad_pcb
from placement import seeder
from placement.cli_gates import add_board_state_args
from placement.placement_state import UNPLACED_EXIT, gate_or_exit
from placement.plan_ops import (PLACEMENT_PLAN_SCHEMA, PlanError,
                                format_errors, parse_placement_plan)
from placement.plan_resolve import resolve
from placement.portfolio import copy_siblings
from placement.writer import write_placed_output

VIOLATIONS_EXIT = 4


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Run a placement plan against a board.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
Examples:
  python place_plan.py board.kicad_pcb plan.json -o seeded.kicad_pcb
  python place_plan.py board.kicad_pcb plan.json --dry-run
""")
    p.add_argument("input_file", nargs='?',
                   help="Input KiCad PCB (an unplaced pile, or a placement "
                        "the plan repairs)")
    p.add_argument("plan", nargs='?', help="Placement plan JSON")
    p.add_argument("-o", "--output", metavar="PCB",
                   help="Output board (required unless --dry-run)")
    p.add_argument("--json", metavar="PATH",
                   help="Write the full seat/park report here")
    p.add_argument("--dry-run", action="store_true",
                   help="Resolve and report; write nothing")
    p.add_argument("--print-schema", action="store_true",
                   help="Print the plan authoring contract and exit")
    p.add_argument("--clearance", type=float, default=None)
    p.add_argument("--board-edge-clearance", type=float, default=None)
    p.add_argument("--grid-step", type=float, default=0.1)
    p.add_argument("--deadline", type=float, default=None, metavar="SECONDS")
    add_board_state_args(p)
    a = p.parse_args(argv)

    if a.print_schema:
        print(PLACEMENT_PLAN_SCHEMA)
        return 0
    if not a.input_file or not a.plan:
        p.error("input_file and plan are required (or --print-schema)")
    if not a.dry_run and not a.output:
        p.error("-o/--output is required unless --dry-run")

    try:
        with open(a.plan, encoding='utf-8') as f:
            raw = f.read()
    except OSError as e:
        print(f"place_plan: cannot read the plan: {e}", file=sys.stderr)
        return 2
    ops, errors = parse_placement_plan(raw)
    if ops is None:
        print(format_errors(errors), file=sys.stderr)
        return 2

    pcb = parse_kicad_pcb(a.input_file)
    if pcb.board_info.board_bounds is None:
        print("place_plan: this board has no Edge.Cuts outline. The outline "
              "is spec-owned -- draw it before placing against it.",
              file=sys.stderr)
        return UNPLACED_EXIT
    # A plan is explicit about every part it touches, so an unplaced pile is
    # the NORMAL input here rather than a refusal -- that is the whole point.
    # Copper is still a refusal: placement moves footprints, not tracks.
    gate_or_exit(pcb, a.input_file, 'place_plan', allow_unplaced=True,
                 allow_routed=a.allow_routed)

    floors = {}
    try:
        from list_nets import board_floor_knobs
        floors = board_floor_knobs(
            a.input_file, clearance=a.clearance,
            board_edge_clearance=a.board_edge_clearance) or {}
    except Exception:
        floors = {}

    def _floor(name, fallback):
        v = floors.get(name)
        if isinstance(v, dict):
            v = v.get('value')
        return fallback if v is None else float(v)

    clearance = a.clearance if a.clearance is not None \
        else _floor('clearance', 0.25)
    edge = a.board_edge_clearance if a.board_edge_clearance is not None \
        else _floor('board_edge_clearance', 0.55)

    dl = None
    if a.deadline:
        from krt_deadline import arm
        dl = arm(a.deadline, tool='place_plan')

    try:
        res = resolve(pcb, a.input_file, ops, clearance=clearance,
                      board_edge_clearance=edge, grid_step=a.grid_step,
                      deadline=dl)
    except PlanError as e:
        print(f"place_plan: {e}", file=sys.stderr)
        return 2

    for n in res.notes:
        print(f"  NOTE: {n}")
    for park in res.parks:
        print(f"  PARK {park.ref}: {park.reason}")
    s = res.summary()
    print(f"Seated {s['seated']} part(s); {s['parked']} parked; "
          f"{s['locked']} to lock; worst move {s['worst_move_mm']}mm")

    if not a.dry_run:
        write_placed_output(a.input_file, a.output, res.placements)
        copy_siblings(a.input_file, a.output)
        if res.lock_refs:
            n = seeder.stamp_locked(a.output, res.lock_refs)
            print(f"Locked {n} footprint(s) in the output")
        print(f"Wrote {a.output}")

    report = {'schema': 1, 'kind': 'placement-plan-run',
              'board': os.path.abspath(a.input_file),
              'output': os.path.abspath(a.output) if a.output else None,
              'clearance': clearance, 'board_edge_clearance': edge,
              'seats': [x.to_dict() for x in res.seats],
              'parks': [x.to_dict() for x in res.parks],
              'notes': res.notes, 'lock_refs': res.lock_refs,
              'indexes': {k: v['members'] for k, v in res.indexes.items()},
              **s}
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=1, sort_keys=True)
    summary = dict(s, output=a.output, board=a.input_file)
    print("JSON_SUMMARY: " + json.dumps(summary, sort_keys=True))

    if not res.complete:
        from krt_deadline import DEADLINE_EXIT
        return DEADLINE_EXIT
    return VIOLATIONS_EXIT if res.parks else 0


if __name__ == "__main__":
    sys.exit(main())
