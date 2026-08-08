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

#: When a half runs in a teammate instead of here. ONE rule per half, on ONE
#: number each, because "when the output would crowd the other half" is a thing
#: nobody can evaluate at the moment they have to decide.
#:
#: The two halves are sized by different things, which is why there are two
#: numbers rather than one:
#:
#:   PLACEMENT output scales with PARTS -- the repair sweep visits violators,
#:   the legalize ladder visits them again, and every render draws all of them.
#:   ROUTING output scales with NETS -- the route log is per-net, and the score
#:   and connectivity reports enumerate them.
#:
#: Both are proxies for context volume and both are JUDGEMENTS, not
#: calibrations. What is measured is only the two ends: a 65-part / 83-net
#: 2-layer board ran both halves inline comfortably, and a 216-part / 266-net
#: 4-layer board produces a per-net route log plus a fanout stage per
#: fine-pitch part. The thresholds sit between those, and both are flags
#: because the right value depends on what else is already in the context.
#:
#: What would calibrate them: record, per run, the half that forced a
#: compaction and the board's parts/nets. Nothing measures that today, so
#: these stay judgements and say so here rather than in the emission.
DELEGATE_ABOVE_PARTS = 200
DELEGATE_ABOVE_NETS = 300


def _board_size(board):
    """(parts, nets) with pads/names, or (None, None) if it cannot be read.

    None matters: "I could not count" must not silently become "small enough
    to run inline", so the caller keeps whatever the flags said instead of
    inventing a decision out of a failed read.
    """
    if not board or not os.path.isfile(board):
        return None, None
    try:
        sys.path.insert(0, ROOT)
        from kicad_parser import parse_kicad_pcb
        pcb = parse_kicad_pcb(board)
        return (sum(1 for f in (pcb.footprints or {}).values() if f.pads),
                sum(1 for n in (pcb.nets or {}).values() if n.name))
    except Exception:                                       # noqa: BLE001
        return None, None


def _part_count(board):
    return _board_size(board)[0]


def _delegation(a, half='placement'):
    """(delegate?, why) -- flags first, then the one number for THIS half.

    Delegation is a CONTEXT decision, never a correctness one: the guards are
    identical either way and both halves record into the same ledger. But
    leaving it to judgement means it gets judged on the board where judging it
    was already too late, so the number is read off the board and the default
    decides. Either flag overrides, and the reason is ALWAYS printed with the
    value, the threshold and the flag that changes it -- a run that silently
    spawned a teammate would be worse than one that never did.
    """
    if getattr(a, 'no_delegate', False):
        return False, '--no-delegate was passed, so this half runs here'
    parts, nets = _board_size(a.board)
    if getattr(a, 'delegate', False):
        return True, '--delegate was passed, so this half goes to a teammate'
    if parts is None:
        return False, (f'{a.board} could not be read to size it. A failed read '
                       f'is not evidence the board is small, so this half runs '
                       f'here rather than guessing -- pass --delegate if it is '
                       f'in fact large')
    if half == 'routing':
        val, lim, unit, flag = nets, a.delegate_above_nets, 'nets', \
            '--delegate-above-nets'
        other = f'{parts} parts'
    else:
        val, lim, unit, flag = parts, a.delegate_above_parts, 'parts', \
            '--delegate-above-parts'
        other = f'{nets} nets'
    if val is not None and val > lim:
        return True, (f'{val} {unit} > {lim} ({flag}), so this half goes to a '
                      f'teammate. {other.capitalize()} for context')

    # THE TWO THRESHOLDS MUST NOT SPLIT THE DECISION. They are independent
    # proxies for the same thing, so a board can land over one and under the
    # other -- and that split is what run 13 was: 264 parts (delegate) and 251
    # nets (inline). Placement went to a teammate and followed its driver rung
    # by rung; routing stayed with the orchestrator, which by then was also
    # holding the outer loop, two watchers, the journal and the report -- and
    # never entered routing's own V1-V5 convergence loop at all.
    #
    # So: if the board was big enough to need a teammate for PLACEMENT, it is
    # big enough for one for ROUTING. The orchestrator has been coordinating
    # rather than executing, and handing it a loop to drive directly at that
    # point is the transition that failed. Costs no new state to ask.
    if half == 'routing' and _delegation(a, half='placement')[0]:
        return True, (f'{val} {unit} <= {lim} ({flag}), but PLACEMENT was '
                      f'delegated, so routing goes to a teammate too rather '
                      f'than splitting the decision. The two thresholds are '
                      f'independent proxies for one thing; the half that '
                      f'skipped its own convergence loop was the inline half '
                      f'of exactly such a split. --no-delegate overrides')
    return False, (f'{val} {unit} <= {lim} ({flag}), so this half runs here. '
                   f'{other.capitalize()} for context')


def l1(a):
    """Place. Delegated or inline -- correctness is the same either way."""
    delegate, why = _delegation(a)
    if delegate:
        return f'''<stage_instructions stage="L1" name="place (delegated)" of="5">
DELEGATING: {why}.

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
INLINE: {why}.

Place this board yourself, driven. Do not read the placement skill end to end:
ask its driver for one stage at a time, so only one loop's rules are ever in
front of you.

  python3 -X utf8 .claude/skills/plan-pcb-placement/scripts/placement_driver.py \\
      --stage P0 --board {a.board}

Follow it to P-close, including its refusals. Record every accepted lap into
{a.ledger} with converge.py.

--delegate forces a teammate for this half whatever the size, and
--no-delegate forces it inline. That is a context decision, not a correctness
one: the guards below are identical either way.

Next: python3 -X utf8 {sys.argv[0]} --stage L2 --board <placed board> \\
          --ledger {a.ledger} --placement-report <its close-out json>
</stage_instructions>'''


def l2(a):
    """Freeze what placement decided, then route."""
    _res = getattr(a, 'accept_residue', None)
    if _res is not None:
        _bad = [n for n in _res if n not in L2_CHECKS]
        if not _res or _bad:
            return err(
                f'--accept-residue now names WHICH check you are accepting. '
                f'Valid: {" ".join(L2_CHECKS)}.'
                + (f' Unknown: {" ".join(_bad)}.' if _bad else
                   ' A bare --accept-residue waived all of them at once, which '
                   'is how a spurious `blocking` refusal also waived the '
                   '`oob_pad_count` gate (run 10, 21 parts with pad copper off '
                   'the board).'))
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
    # Bind the close-out to the board it is unlocking. check_assembly writes the
    # graded board's path into the payload and this gate never compared it, so
    # an EARLIER lap's close-out (or another board's entirely) unlocked routing
    # on a board nobody graded. Cheap, and it closes a hole that is invisible
    # afterwards because the ledger records only that the stage passed.
    _graded = rep.get('board')
    if _graded and a.board:
        if os.path.normcase(os.path.abspath(_graded)) != \
                os.path.normcase(os.path.abspath(a.board)):
            return err(
                f'The placement close-out grades a DIFFERENT board than the one '
                f'being handed to routing:\n\n  close-out graded : {_graded}\n'
                f'  handing to route: {os.path.abspath(a.board)}\n\n'
                f'A stale close-out is not evidence about this board. Re-grade '
                f'the board you are actually routing:\n'
                f'  python3 -X utf8 check_assembly.py {a.board} --json '
                f'wk/assembly_close.json')

    # SHAPE, BEFORE CONTENT. `blocking` exists in BOTH check_assembly's report
    # and board_score's, with completely different meanings -- a
    # pad-intersection-PAIR count vs a six-component TOTAL over unrouted +
    # broken + drc + undersized + floorplan + assembly -- while
    # buildable/verdict/locked_contacts/oob_pad_count exist only in
    # check_assembly's. Measured on run 10: handing board_score's JSON here
    # silently disabled three of the four checks below (their keys are simply
    # absent, and `None is False` is False) and fired the fourth with
    # `blocking = 57` -- 100% unrouted, 0% assembly -- under a message blaming
    # "a blocking assembly pair". Nothing about that JSON looks malformed,
    # which is why a key-presence check is the only thing that catches it.
    #
    # NOT waivable by --accept-residue: a residue is a measured defect somebody
    # accepted, and this is the wrong instrument's output. There is nothing to
    # accept.
    _missing = [k for k in L2_CHECKS if k not in rep]
    if _missing:
        _hint = ''
        if rep.get('kind') == 'board-score' or 'blocking_by' in rep:
            _hint = (
                "\n\nThis looks like `board_score.py`'s JSON, not "
                "`check_assembly.py`'s. They share the field name `blocking` "
                "and mean different things by it: board_score's is a total "
                "over unrouted + broken + drc + undersized + floorplan + "
                "assembly, check_assembly's is a count of pad-intersection "
                "PAIRS. board_score grades the ROUTE; this gate grades the "
                "PLACEMENT.")
        return err(
            f'The placement close-out is not shaped like a `check_assembly.py` '
            f'report: it is missing {", ".join(_missing)}.\n\nThis gate reads '
            f'exactly four measurements -- {", ".join(L2_CHECKS)} -- and a '
            f'document missing any of them cannot answer the questions the '
            f'gate asks. A missing key is not a passing one; the checks that '
            f'read it would simply not run.{_hint}\n\nProduce the right '
            f'document:\n  python3 -X utf8 check_assembly.py '
            f'{a.board or "<board>"} --json wk/assembly_close.json')

    def _count(key):
        """(value, refusal). Anything that is not a finite, non-negative real
        is UNMEASURED, never clean.

        The guards were `isinstance(x, int) and x > 0`, which passes a
        string "7" (fails the isinstance, so the refusal never fires), a float
        3.0 (not an int), a NaN (`nan > 0` is False, and json round-trips a
        bare NaN) and a negative. Every one of those reads as a clean board.
        """
        v = rep.get(key)
        if v is None:
            return None, None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None, (
                f'The close-out reports `{key}` as {type(v).__name__} {v!r}, '
                f'not a number. A count that is not a number has not been '
                f'measured, and an unmeasured count is not a passing one -- '
                f'the old guard here accepted exactly this shape as clean. '
                f'Re-produce the close-out with check_assembly --json.')
        if v != v or v in (float('inf'), float('-inf')):
            return None, (
                f'The close-out reports `{key}` = {v!r}. NaN and infinity both '
                f'compare False against `> 0`, so they used to read as a clean '
                f'board. Re-produce the close-out.')
        if v < 0:
            return None, (
                f'The close-out reports `{key}` = {v}, which is negative and '
                f'therefore not a count. Re-produce the close-out.')
        return v, None

    # check_assembly always writes `buildable` and `locked_contacts`; this gate
    # read NEITHER, so a board it calls NOT BUILDABLE passed. SKILL.md's
    # non-negotiable 3 names all three -- a blocking pair, a locked-part
    # contact, a rigid inconsistency -- and the driver enforced two.
    _buildable = rep.get('buildable')
    _verdict = rep.get('verdict')
    if (_buildable is False or (isinstance(_verdict, str)
                                and 'NOT BUILDABLE' in _verdict.upper())) \
            and not _accept(a, 'buildable'):
        return err(
            f'The placement close-out says the board is NOT BUILDABLE '
            f'(buildable={_buildable!r}, verdict={_verdict!r}).\n\nThis gate '
            f'used to read only `blocking` and `oob_pad_count`, so a board its '
            f'own instrument calls unbuildable walked through. Go back to the '
            f'placement half, or re-run with --accept-residue buildable if this is a '
            f'measured, named, accepted residue.')
    _lc, _lcerr = _count('locked_contacts')
    if _lcerr:
        return err(_lcerr)
    if _lc and _lc > 0 and not _accept(a, 'locked_contacts'):
        return err(
            f'The placement close-out reports locked_contacts = {_lc}: copper '
            f'or a part is in contact with a KiCad-LOCKED part.\n\nA locked '
            f'pose is a decision somebody made -- an enclosure standoff, a '
            f'panel cut-out -- so a placement search may not settle this by '
            f'moving the other part somewhere it likes better, and routing '
            f'cannot settle it at all. Fix it in the placement half.')

    blocking, _berr = _count('blocking')
    if _berr:
        return err(_berr)
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
    if blocking > 0 and not _accept(a, 'blocking'):
        return err(
            f'The placement close-out reports blocking = {blocking}. A board '
            f'that reaches routing with a blocking assembly pair will fail '
            f'routing for a reason routing cannot fix, and the retries spent '
            f'there are wasted.\n\nGo back to the placement half, or re-run '
            f'this stage with --accept-residue blocking if that residue is measured '
            f'unfixable and NAMED in the close-out -- which is a decision you '
            f'are recording, not a flag that makes it go away.')
    # blocking == 0 is not the same as routable. A part whose pads lie off the
    # board carries nets no router can reach, and it produces NO blocking pair
    # -- there is nothing for it to collide with out there. Measured on a
    # damaged board that passed this gate at blocking 0 with three parts
    # sitting wholly off the outline; every net on them would have failed, and
    # the loop would have spent a routing pass to discover it.
    oob, _ooberr = _count('oob_pad_count')
    if _ooberr:
        return err(_ooberr)
    if oob and oob > 0 and not _accept(a, 'oob_pad_count'):
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
            f'with --accept-residue oob_pad_count.')
    delegate, why = _delegation(a, half='routing')
    freeze = '''FREEZE first. Lock the refs whose poses are decisions -- mechanically fixed
parts, anything a spec pins, anything the placement half moved deliberately. A
later step that moves them silently undoes the placement work, and nothing
downstream will report it.'''
    if delegate:
        return f'''<stage_instructions stage="L2" name="freeze, then route (delegated)" of="5">
DELEGATING: {why}.

{freeze}

Freeze BEFORE you hand it over -- the locks are a decision from the placement
half, and a teammate that receives an unfrozen board cannot know which poses
were deliberate.

Then delegate the routing half to a TEAMMATE, for the same reason L1 does: the
routing skill spawns its own verification subagents at close-out, and a
subagent cannot spawn one. This half is the one that produces the most output
of anything in the loop -- a route log on a board this size runs to thousands
of lines -- so it is the half most worth keeping out of this context.

<subagent_prompt agent="claude" description="route {os.path.basename(a.board)}">
Route this board to its close-out. The placement is FROZEN: do not move a
footprint, and if you conclude one must move, stop and say so rather than
moving it.

  board:  {a.board}
  ledger: {a.ledger}

Use /plan-pcb-routing. Ask its driver for the chain and then one stage at a
time:
  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/routing_driver.py \\
      --plan --board {a.board}
  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/routing_driver.py \\
      --stage A1 --board {a.board}
and follow it, including its refusals -- an <error> means a gate is holding,
so produce what it asks for rather than working around it.

Record EVERY accepted iteration into the ledger above with converge.py, and
every rejected one with --rejected before stepping back. The stage after this
one refuses a board that is not in the ledger, by content hash.

Return, and return ONLY:
  1. the path of the routed board;
  2. its score JSON path, and `blocking` with its `blocking_by` breakdown;
  3. the failing nets BY NAME, not counted;
  4. anything left UNGRADED, named as unexamined rather than clean.
Do not summarise the process. The next stage classifies from those numbers.
</subagent_prompt>

When it returns, continue here with the board and score it produced.

Two rules that are only true HERE, where the halves meet:
  - copper is not evidence about placement. A route that completed does not
    ratify the placement it ran on, and one that failed does not condemn it.
  - every routed board produced from THIS placement is valid only while this
    placement stands.

TAKE THE HAND-OFF PICTURE before the first route. This is the last moment the
board is copper-free, so it is the only render that shows the placement ALONE --
afterwards every panel is placement plus whatever the router did, and the two
become hard to separate by eye:

  python3 -X utf8 render_placement.py {a.board} \\
      --clearance <the board's own floor> --ignore-nets <the poured nets> \\
      --json-out wk/handoff.json -o wk/handoff.png

Its WHAT THIS PANEL SHOWS block is what routing is being given. Anything it
names as off the outline, stacked, or hole-conflicting will still be there after
the route, and no router setting removes it -- so if that list is not empty,
read this stage's refusals again before spending a routing pass on it.

Next, on success: --stage L5. On a failure: --stage L3 --score <score json>
         --render-json <a --focus render; L3 will not open without one>
</stage_instructions>'''
    return f'''<stage_instructions stage="L2" name="freeze, then route" of="5">
INLINE: {why}.

{freeze}

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

TAKE THE HAND-OFF PICTURE before the first route. This is the last moment the
board is copper-free, so it is the only render that shows the placement ALONE --
afterwards every panel is placement plus whatever the router did, and the two
become hard to separate by eye:

  python3 -X utf8 render_placement.py {a.board} \\
      --clearance <the board's own floor> --ignore-nets <the poured nets> \\
      --json-out wk/handoff.json -o wk/handoff.png

Its WHAT THIS PANEL SHOWS block is what routing is being given. Anything it
names as off the outline, stacked, or hole-conflicting will still be there after
the route, and no router setting removes it -- so if that list is not empty,
read this stage's refusals again before spending a routing pass on it.

Next, on success: --stage L5. On a failure: --stage L3 --score <score json>
         --render-json <a --focus render; L3 will not open without one>
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
            f'      --score-file {a.score} \\\n'
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
    if not a.render_json:
        return err(
            f'blocking = {blocking}, so there IS a failure to classify -- and '
            f'the classification is the decision this whole loop turns on. Do '
            f'it with the picture, not from the score.\n\n'
            f'"Do the failures share one pocket, or scatter?" is the question '
            f'that separates placement-shaped from parameter-shaped, and it is '
            f'ONE look. A run that skipped it spent eleven iterations on '
            f'clearance grading while five nets sat with no copper at all; the '
            f'panels would have shown that in seconds.\n\n'
            f'  python3 -X utf8 render_placement.py {a.board} \\\n'
            f'      --summary-json <the route log JSON_SUMMARY> --focus \\\n'
            f'      --clearance <the board\'s own floor> '
            f'--ignore-nets <the poured nets> \\\n'
            f'      --json-out wk/focus.json -o wk/focus/\n\n'
            f'  (no route summary to hand it? --focus now clusters the '
            f'LEGALITY findings instead, which is the only form of the '
            f'question a copper-free board can answer.)\n\n'
            f'READ the panels, then re-run this stage with '
            f'--render-json wk/focus.json.\n\n'
            f'The render prints WHAT THIS PANEL SHOWS and THE WORST N with a '
            f'crop command each; one pocket means a local fix, scattered means '
            f'systemic, and that is the classification below.')
    return f'''<stage_instructions stage="L3" name="classify the failure" of="5">
blocking = {blocking}. Name the SHAPE before choosing anything.

You have the focus panels ({a.render_json}). Say in one line what they showed --
one pocket or scattered -- and let that lead the evidence below, rather than
being reverse-engineered to agree with it.

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
            '          --score-file <the score json> --argv <the command>')
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

Before you restart, SEE what the re-entry changed. Otherwise the next lap begins
on a board nobody looked at, and "the loop turned" becomes the only record that
anything happened:

  python3 -X utf8 render_placement.py <the re-placed board> \\
      --before <the board it came from> --pair \\
      --clearance <the board's own floor> --ignore-nets <the poured nets> \\
      --json-out wk/reenter.json -o wk/reenter.png

Read WHAT THE MOVE DID. A re-entry that resolves nothing and introduces findings
is a lap to revert, and `N fixed, M NEW` says which -- a level count does not.
Attach it: converge.py record ... --render-json wk/reenter.json

Next: --stage L1 --board <the re-placed board> --ledger {a.ledger}
</stage_instructions>'''


def _verdict(a):
    """Ask converge for the stop verdict. Returns (name, doc, exit) or None."""
    if not a.score or not os.path.isfile(a.score):
        return None
    # L5 interpolated `a.board` into every command it emits and NEVER checked
    # it. A typo, or a stale path a later lap overwrote, produced a
    # `DONE-EXHAUSTED` close-out naming a board nobody graded -- and the
    # close-out is the run's terminal artifact. board_score already writes a
    # `board_sha` with the same digest board_store uses, so binding them is
    # free.
    if a.board and not os.path.isfile(a.board):
        return ('NO-BOARD', {'board': a.board}, 3)
    try:
        with open(a.score, encoding='utf-8') as _sf:
            _payload = json.load(_sf)
    except Exception:                                           # noqa: BLE001
        _payload = None
    if isinstance(_payload, dict) and a.board and os.path.isfile(a.board):
        _psha = _payload.get('board_sha')
        if _psha:
            try:
                sys.path.insert(0, ROOT)
                from board_store import sha256_file
                if sha256_file(a.board) != _psha:
                    return ('SCORE-MISMATCH',
                            {'board': a.board, 'payload_sha': _psha}, 3)
            except Exception:                                   # noqa: BLE001
                pass
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
    if got and got[0] == 'NO-BOARD':
        return err(
            f'L5 was asked to close out a board that does not exist:\n\n'
            f'  {os.path.abspath(got[1]["board"])}\n\n'
            f'This stage names the board in every command it emits and used to '
            f'validate none of them, so a typo or a path a later lap overwrote '
            f'produced a DONE close-out for a file nobody graded -- in the '
            f'run\'s terminal artifact. Point --board at the board you are '
            f'closing out.')
    if got and got[0] == 'SCORE-MISMATCH':
        return err(
            f'The score was taken on a DIFFERENT board than --board names.\n\n'
            f'  --board       : {os.path.abspath(got[1]["board"])}\n'
            f'  score board_sha: {str(got[1]["payload_sha"])[:16]}...\n\n'
            f'board_score embeds the sha of the board it graded precisely so '
            f'this cannot go unnoticed. Re-score the board you are closing '
            f'out, then come back.')
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

    # The terminal branches are where the run SHIPS, so this is where the
    # routing half has to have closed out. Not CONTINUE: that is the go-round-
    # again branch, and gating it would put the most expensive instrument in
    # the repo into the loop that runs most often, to say nothing the score has
    # not already said.
    _refusal = _close_out(a, name)
    if _refusal:
        return _refusal

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
      --score-file {a.score} --argv <the command that produced this board>

Then render the run. It is the only artifact that shows HOW the board got here,
and because both halves recorded into one ledger it is ONE film, not two:

  python3 -X utf8 make_film.py --from-ledger {a.ledger} -o wk/run.mp4

And take the ONE still that shows whether the run made progress: the board this
run started from against the board it is ending with, at identical instrument
settings, diffed BY NAME.

  python3 -X utf8 render_placement.py {a.board} \\
      --before <the board this RUN started from> --pair \\
      --clearance <the board's own floor> --ignore-nets <the poured nets> \\
      --json-out wk/run_pair.json -o wk/run_pair.png

Its WHAT THE MOVE DID block is the run's verdict in one place -- `N fixed, M
NEW` per finding class, plus crossings/hpwl/overlap before and after. Put those
numbers in the report. Two reasons they are not optional:

  * a level count hides a swap. "46 body stacks then 46 body stacks" can be
    nine resolved and nine created somewhere else, and only the by-name diff
    shows it -- the same reason the ledger records failing nets by name.
  * the discrete findings and the aggregate can disagree. On one run every
    finding class improved while `overlap_area` got WORSE (237.50 -> 239.02);
    a single scalar picks one and hides the other, and a report built on the
    flattering one is the failure this stage exists to prevent.

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


#: The four measurements L2 reads out of the placement close-out. It is also
#: the SHAPE TEST -- these four exist in `check_assembly.py`'s JSON and in no
#: other report this chain produces -- and the vocabulary of --accept-residue.
L2_CHECKS = ('buildable', 'verdict', 'locked_contacts', 'blocking',
             'oob_pad_count')


def _accept(a, check: str) -> bool:
    """Is THIS check's residue accepted?

    One blanket flag used to waive all four at once, so clearing a SPURIOUS
    `blocking` refusal -- one raised by the wrong document being handed in --
    silently also waived the `oob_pad_count` gate, which on that board was the
    only load-bearing check of the four (21 parts with pad copper off the
    board). A bare --accept-residue is refused upstream; only named checks
    waive anything."""
    names = getattr(a, 'accept_residue', None)
    return bool(names) and check in names


#: The routing close-out, produced by `check_complete.py --json`.
#: `verdict` alone is not a shape test -- check_assembly's report carries a
#: `verdict` too -- so the value vocabulary is tested as well. That option was
#: not available to L2 (its `blocking` collided with no vocabulary at all),
#: which is why that gate has to lean on key presence.
CLOSE_KEYS = ('board', 'score', 'components', 'fab_floors', 'verdict',
              'reason', 'ungraded')
CLOSE_VERDICTS = ('DONE', 'INCOMPLETE', 'UNSOUND')

#: The vocabulary of --accept-unclosed. Deliberately NOT --accept-residue's:
#: `_accept` reads one namespace attribute, so sharing it would mean an
#: `--accept-residue blocking` passed for the PLACEMENT gate silently waived a
#: ROUTING check -- the run-10 compounding hazard rebuilt across gates instead
#: of within one. `shape` and `binding` are absent on purpose: a malformed or
#: mis-bound document is the wrong document, and there is nothing to accept.
CLOSE_CHECKS = ('instruments', 'fab_floors', 'ungraded', 'agreement')


def _accept_close(a, check: str) -> bool:
    """Is THIS close-out check accepted? (L5's routing gate.)"""
    names = getattr(a, 'accept_unclosed', None)
    return bool(names) and check in names


def _close_out(a, name):
    """Refusal string, or None when the close-out clears L5.

    The asymmetry this exists to remove: L2 refuses to START routing without a
    placement close-out, while nothing ever refused to FINISH. A run reached
    the terminal artifact having never invoked the routing half's own V1-V5 at
    all, and shipped a board carrying a power-rail-to-signal short.

    The gate is NOT "produce a document" -- a well-shaped empty one would
    satisfy that. It is that TWO INDEPENDENT INSTRUMENTS MUST NOT CONTRADICT
    EACH OTHER. converge reaches DONE-EXHAUSTED from `blocking == 0` plus a
    plateau, and `blocking == 0` is exactly the number check_complete exists to
    distrust: it has no component at all for orphan stubs, weird copper or
    cross-footprint pad overlaps, so a short can live in the gap between them.
    The contradiction is the refusal.
    """
    _res = getattr(a, 'accept_unclosed', None)
    if _res is not None:
        _bad = [n for n in _res if n not in CLOSE_CHECKS]
        if not _res or _bad:
            return err(
                f'--accept-unclosed names WHICH close-out check you are '
                f'accepting. Valid: {" ".join(CLOSE_CHECKS)}.'
                + (f' Unknown: {" ".join(_bad)}.' if _bad else
                   ' A bare flag would waive all of them at once, which is how '
                   'a spurious refusal also waives the one check that was '
                   'load-bearing.'))

    doc, e = _load(getattr(a, 'routing_close', None),
                   'The routing close-out (--routing-close)')
    if e:
        return err(
            e + f'\n\nL5 is where the run ships, so it is where the routing '
                f'half has to have closed out. Produce it:\n\n'
                f'  python3 -X utf8 check_complete.py {a.board} \\\n'
                f'      --authored-from <the board this chain STARTED from> \\\n'
                f'      --json wk/routing_close.json\n\n'
                f'--authored-from is not optional bookkeeping: without it the '
                f'floor check cannot run at all, and UNSOUND becomes '
                f'unreachable. The chain rewrites the floors in place, so the '
                f'original project is the only thing left to compare against.')

    _missing = [k for k in CLOSE_KEYS if k not in doc]
    if _missing or doc.get('verdict') not in CLOSE_VERDICTS:
        _hint = ''
        if doc.get('kind') == 'board-score' or 'blocking_by' in doc:
            _hint = ("\n\nThis looks like `board_score.py`'s JSON. That is the "
                     "document check_complete WRAPS and distrusts -- it exits 0 "
                     "with four of nine components ungraded and has no "
                     "component for orphan stubs, weird copper or pad overlaps.")
        elif 'ledger_rows' in doc:
            _hint = ("\n\nThis looks like `converge.py verdict`'s JSON. That is "
                     "the OTHER half of this gate: it never opens the board, so "
                     "it cannot see the things this check is for.")
        return err(
            f'The routing close-out is not shaped like a `check_complete.py` '
            f'report'
            + (f': it is missing {", ".join(_missing)}.' if _missing else
               f': `verdict` is {doc.get("verdict")!r}, not one of '
               f'{" / ".join(CLOSE_VERDICTS)}.')
            + f' A missing key is not a passing one.{_hint}\n\nProduce the '
              f'right document:\n  python3 -X utf8 check_complete.py {a.board} '
              f'--authored-from <original> --json wk/routing_close.json')

    # Bind by CONTENT. A path comparison accepts a close-out for a board that
    # has since been rewritten, and the close-out is the terminal artifact.
    _dsha = doc.get('board_sha')
    if _dsha and a.board and os.path.isfile(a.board):
        try:
            sys.path.insert(0, ROOT)
            from board_store import sha256_file
            if sha256_file(a.board) != _dsha:
                return err(
                    f'The close-out grades a DIFFERENT board than the one being '
                    f'closed out:\n\n  --board          : '
                    f'{os.path.abspath(a.board)}\n'
                    f'  close-out board_sha: {str(_dsha)[:16]}...\n\n'
                    f'Re-run check_complete on the board you are shipping.')
        except Exception:                                       # noqa: BLE001
            pass
    elif doc.get('board') and a.board:
        if os.path.normcase(os.path.abspath(doc['board'])) != \
                os.path.normcase(os.path.abspath(a.board)):
            return err(
                f'The close-out names a different board:\n\n'
                f'  close-out : {doc["board"]}\n'
                f'  --board   : {os.path.abspath(a.board)}')

    # `--skip-slow` empties `components`, leaving a document that passes every
    # shape check while carrying LESS than the score already in hand -- the
    # added instruments are the only reason to prefer it.
    if doc.get('components') == {} and not _accept_close(a, 'instruments'):
        return err(
            'The close-out ran with --skip-slow: `components` is empty, so '
            'orphan stubs, weird copper and cross-footprint pad overlaps were '
            'NOT examined. Those are the instruments board_score has no '
            'component for, and they are the reason this document gates '
            'anything.\n\nRe-run without --skip-slow, or '
            '--accept-unclosed instruments to ship with them unexamined.')

    _ff = doc.get('fab_floors') or {}
    if _ff.get('ran') is False and not _accept_close(a, 'fab_floors'):
        return err(
            f'The close-out could not check the fab floors: '
            f'{_ff.get("reason", "no reason given")}.\n\nWithout it UNSOUND is '
            f'unreachable by construction, so a DONE from this document cannot '
            f'distinguish "the copper is right" from "the rule moved". Pass '
            f'--authored-from <the board this chain STARTED from>, or '
            f'--accept-unclosed fab_floors.')

    _ung = doc.get('ungraded') or []
    if _ung and not _accept_close(a, 'ungraded'):
        return err(
            f'{len(_ung)} component(s) were never examined: '
            f'{", ".join(_ung)}.\n\nNothing was asked to grade them, so they '
            f'are UNKNOWN rather than clean, and they contributed nothing to '
            f'`blocking`. Pass the spec flags check_complete needs, or '
            f'--accept-unclosed ungraded to ship with them unexamined.')

    # THE AGREEMENT CHECK. Only fires where the two instruments disagree:
    # STUCK/BUDGET alongside INCOMPLETE is a CONSISTENT pair and passes.
    if name == 'DONE-EXHAUSTED' and doc['verdict'] != 'DONE' \
            and not _accept_close(a, 'agreement'):
        return err(
            f'TWO INSTRUMENTS DISAGREE, and this is the one place that must '
            f'not be waved through.\n\n'
            f'  converge verdict : DONE-EXHAUSTED  (blocking == 0, and a '
            f'plateau)\n'
            f'  check_complete   : {doc["verdict"]}\n\n'
            f'  {doc.get("reason", "")}\n\n'
            f'converge reaches DONE-EXHAUSTED from `blocking == 0`, and that is '
            f'exactly the number check_complete exists to distrust -- it has no '
            f'component for orphan stubs, weird copper or cross-footprint pad '
            f'overlaps, so a defect can sit in the gap between them and every '
            f'published number still reads clean.\n\n'
            f'Fix what the close-out names and re-score, or --accept-unclosed '
            f'agreement and say in the report which instrument you are '
            f'overriding and why.')
    return None


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
    ap.add_argument('--render-json', default=None, metavar='PATH',
                    help='render_placement --json-out document. L3 requires '
                         'one when there is a failure to classify: "one pocket '
                         'or scattered" is the question that separates '
                         'placement-shaped from parameter-shaped, and it is a '
                         'look, not an inference from the score.')
    ap.add_argument('--shape', default=None, choices=SHAPES)
    ap.add_argument('--budget', type=int, default=100,
                    help='ledger entries this run may write before L5 calls '
                         'it (default 100, the figure convergence.md states)')
    ap.add_argument('--flat', type=int, default=5,
                    help='accepted laps a half may go without improving '
                         'before it counts as blocked (default 5, ditto)')
    ap.add_argument('--delegate-above-parts', type=int,
                    default=DELEGATE_ABOVE_PARTS, metavar='N',
                    help=f'parts above which the PLACEMENT half goes to a '
                         f'teammate (default {DELEGATE_ABOVE_PARTS}): its '
                         f'output scales with parts')
    ap.add_argument('--delegate-above-nets', type=int,
                    default=DELEGATE_ABOVE_NETS, metavar='N',
                    help=f'nets above which the ROUTING half goes to a '
                         f'teammate (default {DELEGATE_ABOVE_NETS}): its '
                         f'output scales with nets')
    ap.add_argument('--no-delegate', action='store_true',
                    help='force both halves inline whatever the board size')
    ap.add_argument('--delegate', action='store_true',
                    help='hand a half to a TEAMMATE (not a plain subagent -- '
                         'each half spawns its own verifiers). A context '
                         'decision, not a correctness one')
    ap.add_argument('--accept-residue', nargs='*', metavar='CHECK',
                    default=None,
                    help='proceed to routing with a NAMED, measured-unfixable '
                         'placement residue -- naming WHICH check you are '
                         'accepting: ' + ' '.join(L2_CHECKS) + '. One blanket '
                         'flag used to waive all of them at once, so clearing '
                         'a spurious `blocking` refusal silently also waived '
                         'the `oob_pad_count` gate that was the load-bearing '
                         'one (run 10). A bare --accept-residue is refused.')
    ap.add_argument('--routing-close', default=None, metavar='PATH',
                    help='the ROUTING close-out, from `check_complete.py '
                         '--json`. L5 refuses without it: L2 refuses to START '
                         'routing without a placement close-out and nothing '
                         'ever refused to FINISH, so a run reached the '
                         'terminal artifact having never entered the routing '
                         "half's own V1-V5 loop at all.")
    ap.add_argument('--accept-unclosed', nargs='*', metavar='CHECK',
                    default=None,
                    help='ship with a NAMED close-out check unsatisfied: '
                         + ' '.join(CLOSE_CHECKS) + '. Deliberately separate '
                         'from --accept-residue, which is the placement gate: '
                         'one shared flag would let a waiver granted for '
                         'placement silently waive a routing check. A bare '
                         '--accept-unclosed is refused.')
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
            # A REAL board file, and a close-out carrying every key the L2 gate
            # reads. Both were bare/partial before: the board did not exist (L5
            # now validates it) and the close-out omitted `buildable` /
            # `locked_contacts` / `board` (L2 now reads them). A dump whose
            # fixture cannot satisfy the guards prints refusals, which is the
            # opposite of what a dump is for.
            _bd = os.path.join(tmp, 'b.kicad_pcb')
            open(_bd, 'w', encoding='utf-8').close()
            loose = _args(['--board', _bd,
                           '--score', wrote('s.json', {'blocking': 2}),
                           '--placement-report', wrote(
                               'p.json', {'blocking': 0, 'oob_pad_count': 0,
                                          'buildable': True,
                                          'verdict': 'buildable (blocking 0)',
                                          'locked_contacts': 0,
                                          'board': _bd}),
                           '--render-json', wrote('rj.json', {
                               'instrument': {'board': _bd},
                               'checklist': {'d_moved': {'match': None}}}),
                           '--shape', 'placement'])
            for k in sorted(STAGES):
                print(f'===== {k} =====')
                body = STAGES[k](loose)
                print(body)
                if body.startswith('<error>'):
                    refused.append(k)
            # Both halves can delegate, and the teammate prompts are where the
            # commands a delegated run will actually execute live -- dumping
            # only the inline forms leaves them unscanned.
            loose.delegate = True
            for k in ('L1', 'L2'):
                print(f'===== {k} (delegated) =====')
                body = STAGES[k](loose)
                print(body)
                if body.startswith('<error>'):
                    refused.append(f'{k}/delegated')
            loose.delegate = False

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
            def close_doc(verdict):
                return {'schema': 1, 'kind': 'board-complete', 'board': _bd,
                        'score': {'blocking': 0},
                        'components': {'orphan_stubs': {'ran': True}},
                        'fab_floors': {'ran': True, 'relaxed': []},
                        'verdict': verdict, 'reason': 'fixture',
                        'ungraded': []}

            # Each terminal branch needs its own close-out, and they are NOT
            # all DONE: pairing DONE-EXHAUSTED with DONE and the other two with
            # INCOMPLETE is what makes this dump show the agreement rule is
            # ONE-DIRECTIONAL. A fixture set that is DONE throughout would
            # print identically whether or not the rule existed.
            for label, rows, sc, budget, cv in (
                    ('DONE-EXHAUSTED', flat, {'blocking': 0}, 100, 'DONE'),
                    ('STUCK', stuck, {'blocking': 4}, 100, 'INCOMPLETE'),
                    ('BUDGET', stuck, {'blocking': 4}, 1, 'INCOMPLETE')):
                lp = os.path.join(tmp, f'l_{label}.jsonl')
                with open(lp, 'w', encoding='utf-8') as fh:
                    for i, r in enumerate(rows):
                        fh.write(json.dumps(dict(r, iteration=i)) + '\n')
                v = _args(['--board', _bd, '--ledger', lp,
                           '--budget', str(budget),
                           '--routing-close', wrote(f'c_{label}.json',
                                                    close_doc(cv)),
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
        # Every L2 fixture now carries the FOUR keys the gate reads, because a
        # document missing any of them is refused on SHAPE before any of its
        # content is looked at (see L2_CHECKS). That refusal is the change
        # detector: run 10 fed this gate `board_score`'s JSON, which shares the
        # field name `blocking` and means a six-component total by it, and
        # three of the four checks silently did not run.
        _asm = {'buildable': True, 'verdict': 'buildable (blocking 0)',
                'locked_contacts': 0, 'oob_pad_count': 0}
        p = os.path.join(tmp, 'p.json')
        json.dump({**_asm, 'blocking': 3}, open(p, 'w', encoding='utf-8'))
        out = STAGES['L2'](_args(base + ['--placement-report', p]))
        want(out.startswith('<error>') and 'blocking = 3' in out,
             'routing refuses a placement that still has blocking pairs')
        out = STAGES['L2'](_args(base + ['--placement-report', p,
                                         '--accept-residue', 'blocking']))
        want(out.startswith('<stage_instructions'),
             '...and proceeds when the residue is explicitly accepted')

        # blocking == 0 with parts off the board: assembly-clean because
        # nothing is out there to collide with, and unroutable for the same
        # reason. Caught by running the real loop on a damaged board.
        oob = os.path.join(tmp, 'oob.json')
        json.dump({**_asm, 'blocking': 0, 'oob_pad_count': 4},
                  open(oob, 'w', encoding='utf-8'))
        out = STAGES['L2'](_args(base + ['--placement-report', oob]))
        want(out.startswith('<error>') and 'oob_pad_count = 4' in out,
             'routing refuses a blocking-0 placement with pads off the board')
        want('edge_connectors' in out,
             '...and names how a BY-DESIGN overhang is declared instead')
        out = STAGES['L2'](_args(base + ['--placement-report', oob,
                                         '--accept-residue', 'oob_pad_count']))
        want(out.startswith('<stage_instructions'),
             '...and still proceeds when that is explicitly accepted')

        # THE COMPOUNDING HAZARD the per-check flag exists to remove: accepting
        # one check must not waive another. This exact pair is what happened --
        # a `blocking` refusal was cleared with a blanket flag, and the
        # oob_pad_count gate went with it.
        out = STAGES['L2'](_args(base + ['--placement-report', oob,
                                         '--accept-residue', 'blocking']))
        want(out.startswith('<error>') and 'oob_pad_count = 4' in out,
             'accepting `blocking` does NOT waive the oob_pad_count gate')
        out = STAGES['L2'](_args(base + ['--placement-report', oob,
                                         '--accept-residue']))
        want(out.startswith('<error>') and 'names WHICH check' in out,
             'a BARE --accept-residue is refused, not a blanket waiver')
        out = STAGES['L2'](_args(base + ['--placement-report', oob,
                                         '--accept-residue', 'nonsense']))
        want(out.startswith('<error>') and 'Unknown: nonsense' in out,
             'an unknown check name is refused by name')

        # SHAPE: board_score's JSON is not check_assembly's, and sharing the
        # field name `blocking` is precisely why this must be a key-presence
        # test rather than a value test.
        bs = os.path.join(tmp, 'bs.json')
        json.dump({'kind': 'board-score', 'blocking': 57,
                   'blocking_by': {'unrouted': 57}, 'advisory': {}},
                  open(bs, 'w', encoding='utf-8'))
        out = STAGES['L2'](_args(base + ['--placement-report', bs]))
        want(out.startswith('<error>') and 'board_score' in out,
             'L2 refuses board_score\'s JSON BY SHAPE and names it')
        want('blocking = 57' not in out,
             '...without firing the blocking check on the wrong number')
        out = STAGES['L2'](_args(base + ['--placement-report', bs,
                                         '--accept-residue', 'blocking']))
        want(out.startswith('<error>') and 'board_score' in out,
             '...and the shape refusal is NOT waivable by --accept-residue')

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

    inline = STAGES['L1'](_args(base + ['--no-delegate']))
    deleg = STAGES['L1'](_args(base + ['--delegate']))
    want('<subagent_prompt' in deleg and '<subagent_prompt' not in inline,
         'delegation is a choice, and only the delegated form dispatches')
    want('TEAMMATE' in deleg and 'cannot spawn' in deleg,
         'delegation says a teammate is required, and why')

    # The size decides by default, so that it is not left to be remembered on
    # the board where remembering it was already too late. Both halves, because
    # routing is the one that produces the most output and used to have no
    # escape hatch at all.
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _t:
        rep = os.path.join(_t, 'p.json')
        # All four L2_CHECKS keys: this fixture has to get PAST the shape gate
        # to reach the delegation decision it is actually testing.
        json.dump({'blocking': 0, 'oob_pad_count': 0, 'locked_contacts': 0,
                   'buildable': True, 'verdict': 'buildable (blocking 0)'},
                  open(rep, 'w', encoding='utf-8'))
        # ANY board in the corpus: this asserts the RULE, not a board, and
        # naming one would pin a skill to a specific project.
        import glob as _g
        small = next(iter(sorted(
            _g.glob(os.path.join(ROOT, 'kicad_files', '*.kicad_pcb')))), None)
        if small and os.path.isfile(small):
            n = _part_count(small)
            want(isinstance(n, int) and n > 0,
                 'the board can be sized at all')
            auto = ['--board', small, '--placement-report', rep]
            for k in ('L1', 'L2'):
                out = STAGES[k](_args(auto))
                want('INLINE:' in out and '<subagent_prompt' not in out,
                     f'{k} runs a small board inline, and says why')
                out = STAGES[k](_args(auto + ['--delegate-above-parts', '1',
                                              '--delegate-above-nets', '1']))
                want('DELEGATING:' in out and '<subagent_prompt' in out,
                     f'{k} delegates once the board is over the threshold')
                want(str(n) in out,
                     f'{k} names the count it decided on, not just the verdict')
                out = STAGES[k](_args(auto + ['--delegate-above-parts', '1',
                                              '--delegate-above-nets', '1',
                                              '--no-delegate']))
                want('<subagent_prompt' not in out,
                     f'{k}: --no-delegate overrides the size')
        # A board that cannot be read is not evidence that it is small.
        out = STAGES['L1'](_args(['--board', os.path.join(_t, 'nope.kicad_pcb'),
                                  '--delegate-above-parts', '1',
                                              '--delegate-above-nets', '1']))
        want('could not be read' in out and '<subagent_prompt' not in out,
             'an unreadable board does not auto-delegate, and says so')

    # Assemble the emitted text from stages whose guards are SATISFIED --
    # otherwise this scans refusals and reports the instructions are missing
    # content the refusals were never going to carry.
    with tempfile.TemporaryDirectory() as tmp:
        # A REAL board: L5 now validates the path it interpolates into its
        # close-out commands, and the close-out is the run's terminal artifact.
        _bf = os.path.join(tmp, 'b.kicad_pcb')
        open(_bf, 'w', encoding='utf-8').close()
        ok_rep = os.path.join(tmp, 'p.json')
        # The close-out must also carry the keys the L2 gate now reads --
        # `buildable`, `locked_contacts` and the board it graded -- because a
        # payload that omits them is exactly what used to walk an unbuildable
        # board into routing.
        json.dump({'blocking': 0, 'oob_pad_count': 0, 'buildable': True,
                   'verdict': 'buildable (blocking 0)', 'locked_contacts': 0,
                   'board': _bf}, open(ok_rep, 'w', encoding='utf-8'))
        ok_score = os.path.join(tmp, 's.json')
        json.dump({'blocking': 4}, open(ok_score, 'w', encoding='utf-8'))
        ok_rj = os.path.join(tmp, 'rj.json')
        json.dump({'instrument': {'board': _bf},
                   'checklist': {'d_moved': {'match': None}}},
                  open(ok_rj, 'w', encoding='utf-8'))
        full = ['--board', _bf,
                '--score', ok_score, '--placement-report', ok_rep,
                '--render-json', ok_rj, '--shape', 'placement']
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
        # The board must EXIST for these. It used to be the bare name
        # 'b.kicad_pcb', which is exactly the hole L5 now closes: this stage
        # names the board in every command it emits and validated none of them,
        # so a DONE close-out could be produced for a file nobody graded. The
        # fixtures were relying on that.
        _b5 = os.path.join(tmp, 'b.kicad_pcb')
        open(_b5, 'w', encoding='utf-8').close()
        base = ['--board', _b5]

        want(STAGES['L5'](_args(base)).startswith('<error>'),
             'close-out refuses without a score to decide on')
        want('does not exist' in STAGES['L5'](_args(
                 ['--board', os.path.join(tmp, 'ghost.kicad_pcb'),
                  '--ledger', os.path.join(tmp, 'x.jsonl'),
                  '--score', (lambda p: (json.dump({'blocking': 0},
                                                   open(p, 'w', encoding='utf-8')),
                                         p)[1])(os.path.join(tmp, 'g.json'))])),
             'close-out refuses a board that does not exist')

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

        def closed(name, **over):
            """A check_complete.py close-out, DONE unless told otherwise."""
            d = {'schema': 1, 'kind': 'board-complete', 'board': _b5,
                 'score': {'blocking': 0}, 'components': {'orphan_stubs': {}},
                 'fab_floors': {'ran': True, 'relaxed': []},
                 'verdict': 'DONE', 'reason': 'clean', 'ungraded': []}
            d.update(over)
            return scored(d, name)

        flat = ([{'kind': 'placement', 'accepted': True,
                  'score': {'blocking': 0, 'quality': {}}}] * 6
                + [{'kind': 'completion', 'accepted': True,
                    'score': {'blocking': 0, 'quality': {}}}] * 6)
        out = STAGES['L5'](_args(base + [
            '--ledger', ledger_of([], 'fresh.jsonl'),
            '--score', scored({'blocking': 0}, 'zero.json')]))
        want('not done yet' in out,
             'blocking == 0 with the halves still moving does NOT close out')
        # CONTINUE must NOT be gated: it is the go-round-again branch, and
        # gating it would run the most expensive instrument every lap.
        want('routing close-out' not in out,
             'the CONTINUE branch is not gated on a close-out')

        _fl = ledger_of(flat, 'flat.jsonl')
        _z2 = scored({'blocking': 0}, 'z2.json')
        done_args = base + ['--ledger', _fl, '--score', _z2]
        out = STAGES['L5'](_args(done_args))
        want(out.startswith('<error>') and 'routing close-out' in out,
             'close-out refuses to SHIP without a routing close-out')
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_done.json')]))
        want('DONE-EXHAUSTED' in out and 'make_film' in out,
             'a plateaued solved board closes out, with the film')

        # THE AGREEMENT CHECK, both directions. Asserting only the refusal
        # would pass for a gate that refused everything.
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_unsound.json', verdict='UNSOUND',
                                      reason='floors moved')]))
        want(out.startswith('<error>') and 'TWO INSTRUMENTS DISAGREE' in out,
             'DONE-EXHAUSTED + UNSOUND is refused')
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_inc.json', verdict='INCOMPLETE',
                                      reason='orphan stubs')]))
        want(out.startswith('<error>') and 'TWO INSTRUMENTS DISAGREE' in out,
             'DONE-EXHAUSTED + INCOMPLETE is refused')
        want('DONE-EXHAUSTED' in STAGES['L5'](_args(
                 done_args + ['--routing-close', closed('c_ok2.json'),
                              '--accept-unclosed', 'agreement'])),
             '...and --accept-unclosed agreement ships it, named')

        _stuck = ledger_of(
            [dict(r, score={'blocking': 4, 'quality': {}}) for r in flat],
            'stuck.jsonl')
        _f4 = scored({'blocking': 4}, 'four.json')
        out = STAGES['L5'](_args(base + [
            '--ledger', _stuck, '--score', _f4,
            '--routing-close', closed('c_inc2.json', verdict='INCOMPLETE',
                                      reason='blocking = 4')]))
        want('STUCK' in out and 'calling this finished is not' in out,
             'a plateaued UNSOLVED board says stuck, not done')
        want(not out.startswith('<error>'),
             'STUCK + INCOMPLETE is a CONSISTENT pair and is NOT refused')

        # The document must be the right one, and about the right board.
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', scored(
                {'kind': 'board-score', 'blocking': 0, 'blocking_by': {},
                 'quality': {}}, 'c_bs.json')]))
        want(out.startswith('<error>') and 'board_score' in out,
             'a board_score JSON is refused BY SHAPE and named')
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_skip.json', components={})]))
        want(out.startswith('<error>') and '--skip-slow' in out,
             'a --skip-slow document is refused, and --skip-slow is named')
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_noff.json',
                                      fab_floors={'ran': False,
                                                  'reason': 'no --authored-from'})]))
        want(out.startswith('<error>') and 'UNSOUND is unreachable' in out,
             'a close-out that could not check the floors is refused')
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_ung.json',
                                      ungraded=['impedance', 'length'])]))
        want(out.startswith('<error>') and 'never examined' in out,
             'unexamined components are refused, and named')
        # ...and each waiver waives ONLY its own check.
        out = STAGES['L5'](_args(done_args + [
            '--routing-close', closed('c_two.json', components={},
                                      ungraded=['impedance']),
            '--accept-unclosed', 'ungraded']))
        want(out.startswith('<error>') and '--skip-slow' in out,
             'accepting `ungraded` does NOT waive `instruments`')
        want(STAGES['L5'](_args(done_args + [
                 '--routing-close', closed('c_bare.json'),
                 '--accept-unclosed'])).startswith('<error>'),
             'a bare --accept-unclosed is refused')
        want('Unknown: nonsense' in STAGES['L5'](_args(done_args + [
                 '--routing-close', closed('c_unk.json'),
                 '--accept-unclosed', 'nonsense'])),
             'an unknown --accept-unclosed name is refused BY NAME')

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
