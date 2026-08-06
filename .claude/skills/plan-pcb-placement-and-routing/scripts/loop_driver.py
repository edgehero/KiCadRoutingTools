#!/usr/bin/env python3
"""The loop BETWEEN placement and routing, one stage at a time.

The two halves each have a driver, and each keeps its own rules in front of the
executor one stage at a time. Their accept rules genuinely conflict -- placement
accepts a lap when the named finding it aimed at is gone, routing accepts an
iteration when `blocking` strictly decreased -- so an executor holding both
skills at once has two contradictory definitions of "better" live in the same
context. That is the confusion this driver removes: it never emits both.

What it adds beyond sequencing is the part nothing else owns:

  * the hand-off REFUSES without a placement close-out, so routing cannot start
    on a board whose placement was never proved;
  * a retry REFUSES without a stated classification, because the three failure
    shapes re-enter at three different points and cost is asymmetric -- a wrong
    parameter guess wastes iterations, a wrong placement guess wastes the whole
    routed board;
  * a placement-shaped re-entry MARKS every routed board stale, by name, so the
    next pass cannot quietly reuse one.

State crosses the boundary on DISK (the converge ledger), never in a head.
Delegation is a choice about context volume, not about correctness -- see
--delegate.

    python3 -X utf8 <this> --stage L1 --board b.kicad_pcb
    python3 -X utf8 <this> --list
    python3 -X utf8 <this> --dump-all
    python3 -X utf8 <this> --self-test

Tags: <stage_instructions> act on these; <subagent_prompt> copy verbatim into a
teammate; <error> you skipped evidence.

Exit: 0 emitted, 2 usage, 4 a guard refused.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

SHAPES = ('parameter', 'placement', 'floorplan')


def err(text):
    return f'<error>\n{text}\n</error>'


def _load(path, what):
    if not path:
        return None, f'{what} not provided.'
    if not os.path.isfile(path):
        return None, f'{what}: no such file: {path}'
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh), None
    except Exception as exc:                                # noqa: BLE001
        return None, f'{what}: unreadable ({type(exc).__name__}: {exc})'


def _recorded(board, ledger):
    """Is THIS board in the ledger, by content?

    Not "did the executor say it recorded" -- the same sha256 the board store
    keys on. A run of the combined skill recorded two placement laps and zero
    routing ones, and nothing noticed: the film came out two frames long, the
    staleness list printed "none recorded" at the one moment it mattered, and
    step-back had nothing to step back to. Recording is the spine of all three,
    so the stage that depends on them checks it rather than trusting it.

    None when the question cannot be answered (no ledger yet, unreadable
    board): the caller must not turn "I could not check" into a refusal.
    """
    if not os.path.isfile(board) or not os.path.isfile(ledger):
        return None
    try:
        sys.path.insert(0, ROOT)
        from board_store import sha256_file
        sha = sha256_file(board)
    except Exception:                                       # noqa: BLE001
        return None
    return any(r.get('result_sha') == sha for r in _ledger_rows(ledger))


def _ledger_rows(path):
    if not path or not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------

def l1(a):
    """Place. Delegated or inline -- correctness is the same either way."""
    if a.delegate:
        return f'''<stage_instructions stage="L1" name="place" of="5">
Delegate the placement half to a TEAMMATE, not a plain subagent: the placement
skill spawns its own verification subagents at its close-out, and a subagent
cannot spawn one. Give it the prompt below verbatim.

<subagent_prompt agent="claude" description="place {os.path.basename(a.board)}">
Drive the placement half of this board to its close-out, and do not route.

  board:  {a.board}
  ledger: {a.ledger}

Use /plan-pcb-placement. Ask its driver for one stage at a time:
  python3 -X utf8 .claude/skills/plan-pcb-placement/scripts/placement_driver.py \\
      --stage P0 --board {a.board}
and follow the stage it prints, including its refusals -- an <error> means a
gate is holding, so produce what it asks for rather than working around it.

Record every accepted lap with converge.py into the ledger above.

Return, and return ONLY:
  1. the path of the placed board;
  2. the four close-out measurements with their numbers;
  3. what remains unfixed, each with the measurement that says it is unfixable
     at this stage;
  4. the refs you locked and why.
Do not summarise the process. The next stage needs the board and the numbers.
</subagent_prompt>

When it returns, continue here with --stage L2 and the board it produced.

Next: python3 -X utf8 {sys.argv[0]} --stage L2 --board <placed board> \\
          --ledger {a.ledger} --placement-report <its close-out json>
</stage_instructions>'''
    return f'''<stage_instructions stage="L1" name="place" of="5">
Place this board yourself, driven. Do not read the placement skill end to end:
ask its driver for one stage at a time, so only one loop's rules are ever in
front of you.

  python3 -X utf8 .claude/skills/plan-pcb-placement/scripts/placement_driver.py \\
      --stage P0 --board {a.board}

Follow it to P-close, including its refusals. Record every accepted lap into
{a.ledger} with converge.py.

Delegate this stage instead (--delegate) when the placement run's own output
would crowd out the routing half -- a few hundred parts, long repair sweeps,
many renders. That is a context decision, not a correctness one: the guards
below are identical either way.

Next: python3 -X utf8 {sys.argv[0]} --stage L2 --board <placed board> \\
          --ledger {a.ledger} --placement-report <its close-out json>
</stage_instructions>'''


def l2(a):
    """Freeze what placement decided, then route."""
    rep, e = _load(a.placement_report, 'The placement close-out (--placement-report)')
    if e:
        return err(
            e + '\n\nRouting may not start on a board whose placement was '
                'never proved. L1 ends with a close-out carrying the four '
                'measurements; produce it, then come back.\n\nIf the board '
                'arrived already placed by someone else, run the placement '
                'gate alone and use ITS output:\n'
                '  python3 -X utf8 check_drc.py <board> --clearance <floor> '
                '--json wk/drc0.json\n'
                '  python3 -X utf8 check_assembly.py <board> --json '
                'wk/assembly0.json')
    blocking = rep.get('blocking')
    if blocking is None:
        return err(
            'The placement close-out carries no `blocking` count, so it does '
            'not say whether the placement is assembly-clean -- and a missing '
            'measurement is not a passing one. Produce the close-out from the '
            'instrument that measures it:\n'
            '  python3 -X utf8 check_assembly.py <board> --json '
            'wk/assembly_close.json\n\nAn EMPTY or unrelated JSON satisfies a '
            'file-exists check and tells you nothing; that is the failure this '
            'refusal exists to stop.')
    if isinstance(blocking, int) and blocking > 0 and not a.accept_residue:
        return err(
            f'The placement close-out reports blocking = {blocking}. A board '
            f'that reaches routing with a blocking assembly pair will fail '
            f'routing for a reason routing cannot fix, and the retries spent '
            f'there are wasted.\n\nGo back to the placement half, or re-run '
            f'this stage with --accept-residue if that residue is measured '
            f'unfixable and NAMED in the close-out -- which is a decision you '
            f'are recording, not a flag that makes it go away.')
    # blocking == 0 is not the same as routable. A part whose pads lie off the
    # board carries nets no router can reach, and it produces NO blocking pair
    # -- there is nothing for it to collide with out there. Measured on a
    # damaged board that passed this gate at blocking 0 with three parts
    # sitting wholly off the outline; every net on them would have failed, and
    # the loop would have spent a routing pass to discover it.
    oob = rep.get('oob_pad_count')
    if isinstance(oob, int) and oob > 0 and not a.accept_residue:
        return err(
            f'The placement close-out reports blocking = 0, but '
            f'oob_pad_count = {oob}: {oob} part(s) carry pad copper OFF the '
            f'board. Those parts are assembly-clean precisely because nothing '
            f'is out there to collide with, and their nets cannot be routed at '
            f'all.\n\nThis is placement-shaped damage, and it is cheaper to '
            f'fix now than to discover it as a routing failure and re-enter. '
            f'Go back to the placement half.\n\nIf the overhang is BY DESIGN '
            f'-- a card edge, a switch actuator, a castellated module -- '
            f'declare it in the floorplan intent (edge_connectors), which '
            f'exempts it and makes the exemption reviewable, and then re-run '
            f'with --accept-residue.')
    return f'''<stage_instructions stage="L2" name="freeze, then route" of="5">
FREEZE first. Lock the refs whose poses are decisions -- mechanically fixed
parts, anything a spec pins, anything the placement half moved deliberately. A
later step that moves them silently undoes the placement work, and nothing
downstream will report it.

Then route, driven, so the routing loop's rules are the only ones in front of
you:

  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/routing_driver.py \\
      --plan --board {a.board}
  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/routing_driver.py \\
      --stage A1 --board {a.board}

Its Step 0 gate will pass: you just did that work, and the close-out is the
evidence.

Two rules that are only true HERE, where the halves meet:
  - copper is not evidence about placement. A route that completed does not
    ratify the placement it ran on, and one that failed does not condemn it.
  - every routed board produced from THIS placement is valid only while this
    placement stands.

Next, on success: --stage L5. On a failure: --stage L3 --score <score json>
</stage_instructions>'''


def l3(a):
    """Classify. The whole loop turns on this."""
    score, e = _load(a.score, 'The routing score (--score)')
    if e:
        return err(e + '\n\nA retry without a classification is a guess, and '
                       'the three shapes re-enter at three different points. '
                       'Produce the score first:\n  python3 -X utf8 '
                       '.claude/skills/plan-pcb-routing/scripts/board_score.py '
                       '<board> --json wk/score.json')
    blocking = score.get('blocking')
    if blocking is None:
        return err(
            'The score carries no `blocking` count. `blocking == null` is not '
            'zero -- it means something was not graded, and a component '
            'nothing examined is reported UNEXAMINED, never clean. Re-score '
            'the board and read why the count is missing before classifying '
            'anything:\n  python3 -X utf8 '
            '.claude/skills/plan-pcb-routing/scripts/board_score.py <board> '
            '--json wk/score.json')
    if _recorded(a.board, a.ledger) is False:
        return err(
            f'This routed board is not in the ledger.\n\n  board:  {a.board}\n'
            f'  ledger: {a.ledger}\n\nRecord it before classifying. Everything '
            f'that happens after this point reads the ledger and not the '
            f'board: L4 names the routed boards a placement change makes '
            f'stale, L5 decides whether the loop is over from the score '
            f'history, step-back restores from the board store, and the film '
            f'is the ledger read out loud. A run that skipped this recorded '
            f'two placement laps and no routing ones -- the staleness list '
            f'then printed "none recorded" at the one moment it mattered.\n\n'
            f'  python3 -X utf8 converge.py record --ledger {a.ledger} \\\n'
            f'      --board {a.board} --kind completion \\\n'
            f'      --lever "<what you changed and why>" \\\n'
            f'      --score "$(cat {a.score})" \\\n'
            f'      --argv <the real command, as bare tokens>')
    if blocking == 0:
        return f'''<stage_instructions stage="L3" name="classify" note="nothing to classify">
blocking == 0. There is no failure to classify -- and that is not the same as
being finished.

`blocking` is only the first key of a lexicographic score; `quality`
(vias, copper_mm, segments) orders the boards that already reached 0. So the
question now is not "is it done" but "can either half still improve it", and
L5 answers that from the ledger rather than from an impression.

Confirm nothing is merely UNGRADED first -- a component nothing examined is
reported unexamined, never clean.

Next: --stage L5 --board {a.board} --score {a.score} --ledger {a.ledger}
</stage_instructions>'''
    return f'''<stage_instructions stage="L3" name="classify the failure" of="5">
blocking = {blocking}. Name the SHAPE before choosing anything.

All three shapes look identical from inside the router -- nets that did not
route. What separates them is a measurement, and the cost of guessing is
asymmetric.

  parameter-shaped   grid, rip-up depth, layer costs, width. The router had a
                     path and did not take it.
                     Evidence: the failing nets have lane supply at their
                     escape faces, and the diagnosis names a knob.

  placement-shaped   a starved escape face, a part its net cannot reach. No
                     router setting adds a lane.
                     Evidence: check_channels shows the face carrying demand
                     with zero supply; check_reachability says CAGED.

  floorplan-shaped   a clause no arrangement at this placement satisfies.
                     Evidence: the constraint survives every parameter and
                     every local move.

Measure it, do not infer it from how the failure feels:

  python3 -X utf8 check_channels.py {a.board} --baseline <the pre-route board>
  python3 -X utf8 check_reachability.py {a.board} --pad <REF.PAD> --json

check_reachability answers about ONE pad per run -- give it a pad on a failing
net (or --net <id> --at <x,y>). Run it for each failing net you are
classifying; a single CAGED verdict is enough to make the shape placement.

Then re-run this stage with the shape you measured:
  --stage L4 --shape <parameter|placement|floorplan> --board {a.board} \\
      --score {a.score} --ledger {a.ledger}
</stage_instructions>'''


def l4(a):
    """Re-enter, at the point the classification names."""
    if a.shape not in SHAPES:
        return err(
            'A re-entry needs a measured shape: --shape parameter | placement '
            '| floorplan.\n\nThis is the guard that matters most in this '
            'driver. Retrying a placement-shaped failure with router '
            'parameters spends iterations on a board no parameter can fix; '
            'sending a parameter-shaped failure back to placement throws away '
            'a routed board for nothing. L3 tells you how to measure it.')
    if a.shape == 'parameter':
        return f'''<stage_instructions stage="L4" name="re-enter: parameter" of="5">
Re-enter the FAILING ROUTING STEP with the parameter changed. Nothing before it
is invalidated, and the routed board stands.

  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/routing_driver.py \\
      --stage <the step that failed> --board {a.board}

Change ONE parameter. An iteration that changes three cannot tell you which one
worked, and the ledger entry it writes is unusable as evidence for the next.

Write to a FRESH output path -- board_R5_i2, not board_R5 again. The routing
steps write a sibling .kicad_pro carrying the DRC floor, and re-running to the
same path reads that floor back in, so the second run is not the first run with
one parameter changed: it starts from a different floor. The comparison the
whole iteration exists to make is then between two things that differ in two
ways. It also keeps the ledger's recorded sha pointing at a file that still
holds what was recorded.

Record it, then go back to L3 with the new score. If two parameter iterations
in a row do not move `blocking`, the shape was probably not parameter --
re-measure rather than trying a third.

Next: --stage L3 --board {a.board} --score <new score>
</stage_instructions>'''
    if a.shape == 'floorplan':
        return f'''<stage_instructions stage="L4" name="re-enter: floorplan" of="5">
No arrangement at this placement satisfies the clause, so neither a router
parameter nor a local repair will reach it. Go for a different ARRANGEMENT:

  python3 -X utf8 .claude/skills/plan-pcb-placement/scripts/placement_driver.py \\
      --stage P5 --board <the pre-route placed board>

State the clause as intent first, so the slate can be graded against it rather
than eyeballed.

Every routed board from the old placement is stale. Say so in the ledger before
you start, and start the chain again at L1.

Next: --stage L1 --board <the adopted arrangement> --ledger {a.ledger}
</stage_instructions>'''
    # placement-shaped: the expensive one
    rows = _ledger_rows(a.ledger)
    routed = [r for r in rows if (r.get('kind') or '') in ('completion', 'routing')]
    if routed:
        stale = '\n'.join(f'    - iteration {r.get("iteration")}: '
                          f'{(r.get("result_sha") or "")[:12]}'
                          for r in routed[-8:])
    else:
        # An empty list here is not reassurance. Reaching L4 means a route ran
        # and failed, so a ledger with no routed row means the routing was
        # never recorded -- and this stage's whole job is naming the boards
        # that must not be reused. Say that, rather than printing a blank that
        # reads as "nothing to invalidate".
        stale = (
            '    NONE RECORDED -- and that is a problem, not a clean bill.\n'
            '    You are here because a route failed, so a routed board\n'
            '    exists somewhere. It is not in this ledger, so nothing can\n'
            '    tell the next pass which files are now stale. Find every\n'
            '    board produced from this placement and treat ALL of them as\n'
            '    stale, then record the routing result before the next\n'
            '    iteration so this list works next time:\n'
            '      python3 -X utf8 converge.py record --ledger '
            f'{a.ledger} \\\n'
            '          --board <the routed board> --kind completion \\\n'
            '          --score "$(cat <the score json>)" --argv <the command>')
    return f'''<stage_instructions stage="L4" name="re-enter: placement" of="5">
This is the expensive one, and the cost is the point: no router setting adds a
lane, so every routed board produced from this placement is now stale.

Routed boards this ledger recorded, which must not be reused:
{stale}

1. Record the classification in the ledger BEFORE moving, with the measurement
   that produced it -- otherwise the next pass cannot tell why the placement
   changed and will re-derive it wrongly.
2. Re-enter the placement half at the rung the damage calls for:
       P2  a part whose position is a mechanical fact is wrong
       P3  the structure is wrong (a swap, a drag, a bad import)
       P4  local violations only
   python3 -X utf8 .claude/skills/plan-pcb-placement/scripts/placement_driver.py \\
       --stage <P2|P3|P4> --board <the placed board> --before <its input>
3. Then restart the chain at L1. Do not resume routing from a stale board, and
   do not carry a routed net list across: the nets are the same, the corridors
   are not.

Next: --stage L1 --board <the re-placed board> --ledger {a.ledger}
</stage_instructions>'''


def _verdict(a):
    """Ask converge for the stop verdict. Returns (name, doc, exit) or None."""
    if not a.score or not os.path.isfile(a.score):
        return None
    import subprocess
    p = subprocess.run(
        [sys.executable, '-X', 'utf8', os.path.join(ROOT, 'converge.py'),
         'verdict', '--ledger', a.ledger, '--score', a.score,
         '--budget', str(a.budget), '--flat', str(a.flat)],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=ROOT)
    try:
        doc = json.loads(p.stdout)
    except Exception:                                       # noqa: BLE001
        return None
    return doc.get('verdict'), doc, p.returncode


def l5(a):
    """Close out -- but only if the loop is actually finished.

    This stage used to print a checklist and end, which made it the place a run
    stopped rather than the place a run was MEASURED to be over. Reaching
    `blocking == 0` is the floor: the score is lexicographic and `quality`
    orders the boards that already got there, so a solved board whose quality
    is still improving has to go round again. And a run that stopped because it
    was finished must not look like one that stopped because it was stuck.
    """
    got = _verdict(a)
    if got is None:
        return err(
            'L5 decides whether the loop is OVER, and that is a measurement, '
            'not a judgement call. Score the board and come back:\n'
            '  python3 -X utf8 '
            '.claude/skills/plan-pcb-routing/scripts/board_score.py '
            f'{a.board} --json wk/score_final.json\n'
            f'  python3 -X utf8 {sys.argv[0]} --stage L5 --board {a.board} \\\n'
            f'      --ledger {a.ledger} --score wk/score_final.json\n\n'
            'Every stop RULE in this toolchain was already written down and '
            'none of them had a mechanism, so "done" and "stuck" came out '
            'looking identical. This is that mechanism.')
    name, doc, _code = got
    why = doc.get('reason', '')

    if name == 'CONTINUE':
        halves = ', '.join(doc.get('improving') or ['a half'])
        return f'''<stage_instructions stage="L5" name="not done yet" of="5">
The loop is NOT over: {halves} is still improving.

{why}

Go round again. A board that merely routes is the floor -- keep pulling levers
until neither half can improve either key.

  placement still improving -> --stage L1 --board {a.board} --ledger {a.ledger}
  routing still improving   -> --stage L3 --board {a.board} \\
                                   --score {a.score} --ledger {a.ledger}

Record the lap you are about to run, accepted or rejected. A rejected lap is
data: it is what makes the plateau detectable, and without it this stage cannot
tell a finished run from a stalled one.
</stage_instructions>'''

    verdicts = {
        'DONE-EXHAUSTED': 'the board is done, and measured to be done',
        'STUCK': 'stopping is legitimate; calling this finished is not',
        'BUDGET': 'the budget ended this run, not the board',
        'NO-SCORE': 'the score could not be read',
    }
    return f'''<stage_instructions stage="L5" name="close out: {name}" of="5">
{verdicts.get(name, name)}.

{why}

Confirm with the instruments, and put the numbers in the report beside the
names of the instruments that produced them:

  python3 -X utf8 check_complete.py {a.board} --clearance <floor> \\
      --authored-from <the board this chain STARTED from>
  python3 -X utf8 check_drc.py {a.board} --clearance <floor> --clearance-margin 0.1
  python3 -X utf8 check_connected.py {a.board}
  python3 -X utf8 check_assembly.py {a.board}

check_complete is the one that fails CLOSED: board_score exits 0 with four of
nine components ungraded, and it has no component at all for orphan stubs,
weird copper or pad overlaps. --authored-from is what lets it see whether this
board grades itself against floors it rewrote -- the writeback only ever
loosens, so without the original project there is nothing left to compare to.

Connectivity is orthogonal to DRC: a DRC-clean board can be entirely
disconnected, because isolated copper has no clearance conflicts.

Close the ledger with the stop condition NAMED -- converge refuses --final
without it, deliberately:

  python3 -X utf8 converge.py record --ledger {a.ledger} --board {a.board} \\
      --kind completion --final --stop-condition "{name}" \\
      --score "$(cat {a.score})" --argv <the command that produced this board>

Then render the run. It is the only artifact that shows HOW the board got here,
and because both halves recorded into one ledger it is ONE film, not two:

  python3 -X utf8 make_film.py --from-ledger {a.ledger} -o wk/run.mp4

Report, per half, the number and the instrument beside it; say how many times
the loop turned and why each turn happened; and name anything UNEXAMINED rather
than reporting it clean. A chain that re-entered placement twice is not a
failure -- an unexplained one is.

<subagent_prompt agent="claude" description="verify the finished board">
Verify this board end to end, independently.

  board:  {a.board}
  ledger: {a.ledger}

Read .claude/skills/plan-pcb-routing/references/verifier-prompts.md and apply
its routed-board lenses, then check the PLACEMENT half too: the copper-free
gate cannot be re-run on a routed board, so verify it from the ledger's
recorded placement close-out and confirm the poses still match the board.

Re-derive every number yourself. Do not trust the report.
Answer with a line beginning VERDICT= and nothing above it.
</subagent_prompt>
</stage_instructions>'''


STAGES = {'L1': l1, 'L2': l2, 'L3': l3, 'L4': l4, 'L5': l5}
TITLES = {'L1': 'place (inline or delegated)',
          'L2': 'freeze what placement decided, then route',
          'L3': 'classify the failure -- the whole loop turns on this',
          'L4': 're-enter at the point the classification names',
          'L5': 'close out, both halves, measured'}


def _args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stage', choices=sorted(STAGES))
    ap.add_argument('--board', default='board.kicad_pcb')
    ap.add_argument('--ledger', default='wk/ledger.jsonl')
    ap.add_argument('--placement-report', default=None)
    ap.add_argument('--score', default=None)
    ap.add_argument('--shape', default=None, choices=SHAPES)
    ap.add_argument('--budget', type=int, default=100,
                    help='ledger entries this run may write before L5 calls '
                         'it (default 100, the figure convergence.md states)')
    ap.add_argument('--flat', type=int, default=5,
                    help='accepted laps a half may go without improving '
                         'before it counts as blocked (default 5, ditto)')
    ap.add_argument('--delegate', action='store_true',
                    help='hand a half to a TEAMMATE (not a plain subagent -- '
                         'each half spawns its own verifiers). A context '
                         'decision, not a correctness one')
    ap.add_argument('--accept-residue', action='store_true',
                    help='proceed to routing with a NAMED, measured-unfixable '
                         'placement residue')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--dump-all', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    return ap.parse_args(argv)


def main(argv=None):
    a = _args(argv)
    if a.list:
        for k in ('L1', 'L2', 'L3', 'L4', 'L5'):
            print(f'  {k}  {TITLES[k]}')
        return 0
    if a.self_test:
        return _self_test()
    if a.dump_all:
        # The guards must be SATISFIED here. Dumping with files that do not
        # exist prints three refusals and no instructions, which is the
        # opposite of what a dump is for.
        import tempfile
        refused = []
        with tempfile.TemporaryDirectory() as tmp:
            def wrote(name, doc):
                p = os.path.join(tmp, name)
                with open(p, 'w', encoding='utf-8') as fh:
                    json.dump(doc, fh)
                return p
            loose = _args(['--board', 'b.kicad_pcb',
                           '--score', wrote('s.json', {'blocking': 2}),
                           '--placement-report', wrote('p.json',
                                                       {'blocking': 0}),
                           '--shape', 'placement'])
            for k in sorted(STAGES):
                print(f'===== {k} =====')
                body = STAGES[k](loose)
                print(body)
                if body.startswith('<error>'):
                    refused.append(k)
            print('===== L1 (delegated) =====')
            loose.delegate = True
            print(STAGES['L1'](loose))

            # L5 has FOUR outcomes and the dump above shows one of them. The
            # other three carry the commands that close a run out -- the
            # --final record and the film -- so dumping only CONTINUE leaves
            # them unscanned by anything that reads this output. Drive the
            # real verdict with real ledgers rather than faking the branch.
            flat = ([{'kind': 'placement', 'accepted': True,
                      'score': {'blocking': 0, 'quality': {}}}] * 6
                    + [{'kind': 'completion', 'accepted': True,
                        'score': {'blocking': 0, 'quality': {}}}] * 6)
            stuck = [dict(r, score={'blocking': 4, 'quality': {}})
                     for r in flat]
            for label, rows, sc, budget in (
                    ('DONE-EXHAUSTED', flat, {'blocking': 0}, 100),
                    ('STUCK', stuck, {'blocking': 4}, 100),
                    ('BUDGET', stuck, {'blocking': 4}, 1)):
                lp = os.path.join(tmp, f'l_{label}.jsonl')
                with open(lp, 'w', encoding='utf-8') as fh:
                    for i, r in enumerate(rows):
                        fh.write(json.dumps(dict(r, iteration=i)) + '\n')
                v = _args(['--board', 'b.kicad_pcb', '--ledger', lp,
                           '--budget', str(budget),
                           '--score', wrote(f's_{label}.json', sc)])
                print(f'===== L5 ({label}) =====')
                body = STAGES['L5'](v)
                print(body)
                if body.startswith('<error>'):
                    refused.append(f'L5/{label}')
        if refused:
            print(f'\n!! {len(refused)} stage(s) dumped a REFUSAL, not their '
                  f'instructions: {", ".join(refused)}')
            return 1
        return 0
    if not a.stage:
        print('loop_driver: --stage is required (see --list)', file=sys.stderr)
        return 2
    out = STAGES[a.stage](a)
    print(out)
    return 4 if out.startswith('<error>') else 0


def _self_test():
    import tempfile
    bad = []

    def want(cond, label):
        print(f'  {"PASS" if cond else "FAIL"}  {label}')
        if not cond:
            bad.append(label)

    base = ['--board', 'b.kicad_pcb']
    for key in sorted(STAGES):
        out = STAGES[key](_args(base + ['--score', 'x.json',
                                        '--placement-report', 'p.json',
                                        '--shape', 'placement']))
        want(out.startswith(('<stage_instructions', '<error>')),
             f'{key} emits a tagged block')
        want(len(out.splitlines()) <= 70, f'{key} stays under 70 lines')

    want(STAGES['L2'](_args(base)).startswith('<error>'),
         'routing refuses to start without a placement close-out')
    want(STAGES['L3'](_args(base)).startswith('<error>'),
         'classification refuses without a score')
    want(STAGES['L4'](_args(base)).startswith('<error>'),
         'a re-entry refuses without a measured shape')

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'p.json')
        json.dump({'blocking': 3}, open(p, 'w', encoding='utf-8'))
        out = STAGES['L2'](_args(base + ['--placement-report', p]))
        want(out.startswith('<error>') and 'blocking = 3' in out,
             'routing refuses a placement that still has blocking pairs')
        out = STAGES['L2'](_args(base + ['--placement-report', p,
                                         '--accept-residue']))
        want(out.startswith('<stage_instructions'),
             '...and proceeds when the residue is explicitly accepted')

        # blocking == 0 with parts off the board: assembly-clean because
        # nothing is out there to collide with, and unroutable for the same
        # reason. Caught by running the real loop on a damaged board.
        oob = os.path.join(tmp, 'oob.json')
        json.dump({'blocking': 0, 'oob_pad_count': 4},
                  open(oob, 'w', encoding='utf-8'))
        out = STAGES['L2'](_args(base + ['--placement-report', oob]))
        want(out.startswith('<error>') and 'oob_pad_count = 4' in out,
             'routing refuses a blocking-0 placement with pads off the board')
        want('edge_connectors' in out,
             '...and names how a BY-DESIGN overhang is declared instead')
        out = STAGES['L2'](_args(base + ['--placement-report', oob,
                                         '--accept-residue']))
        want(out.startswith('<stage_instructions'),
             '...and still proceeds when that is explicitly accepted')

        # A report that answers neither question is not a close-out.
        empty = os.path.join(tmp, 'empty.json')
        json.dump({}, open(empty, 'w', encoding='utf-8'))
        want(STAGES['L2'](_args(base + ['--placement-report', empty]))
             .startswith('<error>'),
             'an empty JSON does not satisfy the hand-off guard')
        want(STAGES['L3'](_args(base + ['--score', empty]))
             .startswith('<error>'),
             'an empty JSON does not satisfy the classification guard')

        s = os.path.join(tmp, 's.json')
        json.dump({'blocking': 0}, open(s, 'w', encoding='utf-8'))
        out = STAGES['L3'](_args(base + ['--score', s]))
        want('nothing to classify' in out,
             'a clean score has no failure to classify')

    for shape, needle in (('parameter', 'the routed board stands'),
                          ('floorplan', 'different ARRANGEMENT'),
                          ('placement', 'stale')):
        out = STAGES['L4'](_args(base + ['--shape', shape]))
        want(needle in out, f'{shape}-shaped re-entry says what it costs')

    inline = STAGES['L1'](_args(base))
    deleg = STAGES['L1'](_args(base + ['--delegate']))
    want('<subagent_prompt' in deleg and '<subagent_prompt' not in inline,
         'delegation is a choice, and only the delegated form dispatches')
    want('TEAMMATE' in deleg and 'cannot spawn' in deleg,
         'delegation says a teammate is required, and why')

    # Assemble the emitted text from stages whose guards are SATISFIED --
    # otherwise this scans refusals and reports the instructions are missing
    # content the refusals were never going to carry.
    with tempfile.TemporaryDirectory() as tmp:
        ok_rep = os.path.join(tmp, 'p.json')
        json.dump({'blocking': 0}, open(ok_rep, 'w', encoding='utf-8'))
        ok_score = os.path.join(tmp, 's.json')
        json.dump({'blocking': 4}, open(ok_score, 'w', encoding='utf-8'))
        full = base + ['--score', ok_score, '--placement-report', ok_rep,
                       '--shape', 'placement']
        everything = '\n'.join(STAGES[k](_args(full)) for k in sorted(STAGES))
        for k in sorted(STAGES):
            want(not STAGES[k](_args(full)).startswith('<error>'),
                 f'{k} emits instructions once its evidence exists')
    for phrase in ('you may want to', 'if you are not sure', 'usually skip'):
        want(phrase not in everything.lower(), f'no hedging: {phrase!r}')
    want('copper is not evidence about placement' in everything,
         'the rule that only exists here is stated')

    # L5 is a MEASUREMENT now, not a checklist. Its whole point is that a run
    # which stopped because it was finished and one that stopped because it was
    # stuck no longer produce the same artifact.
    with tempfile.TemporaryDirectory() as tmp:
        want(STAGES['L5'](_args(base)).startswith('<error>'),
             'close-out refuses without a score to decide on')

        def ledger_of(rows, name):
            p = os.path.join(tmp, name)
            with open(p, 'w', encoding='utf-8') as fh:
                for i, r in enumerate(rows):
                    fh.write(json.dumps(dict(r, iteration=i)) + '\n')
            return p

        def scored(doc, name):
            p = os.path.join(tmp, name)
            json.dump(doc, open(p, 'w', encoding='utf-8'))
            return p

        flat = ([{'kind': 'placement', 'accepted': True,
                  'score': {'blocking': 0, 'quality': {}}}] * 6
                + [{'kind': 'completion', 'accepted': True,
                    'score': {'blocking': 0, 'quality': {}}}] * 6)
        out = STAGES['L5'](_args(base + [
            '--ledger', ledger_of([], 'fresh.jsonl'),
            '--score', scored({'blocking': 0}, 'zero.json')]))
        want('not done yet' in out,
             'blocking == 0 with the halves still moving does NOT close out')
        out = STAGES['L5'](_args(base + [
            '--ledger', ledger_of(flat, 'flat.jsonl'),
            '--score', scored({'blocking': 0}, 'z2.json')]))
        want('DONE-EXHAUSTED' in out and 'make_film' in out,
             'a plateaued solved board closes out, with the film')
        out = STAGES['L5'](_args(base + [
            '--ledger', ledger_of(
                [dict(r, score={'blocking': 4, 'quality': {}}) for r in flat],
                'stuck.jsonl'),
            '--score', scored({'blocking': 4}, 'four.json')]))
        want('STUCK' in out and 'calling this finished is not' in out,
             'a plateaued UNSOLVED board says stuck, not done')

        # The staleness list, the film and step-back all read the ledger, so
        # the stage that feeds them checks the board is in it.
        board = os.path.join(tmp, 'b.kicad_pcb')
        open(board, 'w', encoding='utf-8').write('(kicad_pcb)')
        out = STAGES['L3'](_args(
            ['--board', board, '--ledger', ledger_of(flat, 'l3.jsonl'),
             '--score', scored({'blocking': 3}, 'b3.json')]))
        want(out.startswith('<error>') and 'not in the ledger' in out,
             'classification refuses a routed board nobody recorded')

    print('OK' if not bad else f'FAIL: {len(bad)}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
