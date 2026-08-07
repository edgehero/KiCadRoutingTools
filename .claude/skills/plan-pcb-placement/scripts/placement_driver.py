#!/usr/bin/env python3
"""The placement workflow, one stage at a time.

A skill document is read all at once, which is how a 4,900-line one produced
executors that skimmed the gate and improvised the ladder. This script is the
tape head instead: you ask for one stage, it prints that stage's instructions
and nothing else, and it REFUSES to print a later stage until you hand it the
evidence the earlier one was supposed to produce.

The refusal is the point. A gate written in prose is a sentence someone skims;
a gate that withholds the next instructions cannot be skimmed past.

    python3 -X utf8 <this> --stage P0 --board b.kicad_pcb
    python3 -X utf8 <this> --stage P3 --board b.kicad_pcb --drc-json wk/drc0.json
    python3 -X utf8 <this> --list
    python3 -X utf8 <this> --dump-all          # every stage, all branches
    python3 -X utf8 <this> --self-test

Output carries exactly three tags:

    <stage_instructions>  act on these yourself
    <subagent_prompt>     copy VERBATIM into a subagent; do NOT follow it
    <error>               you skipped evidence; go produce it

Exit: 0 emitted, 2 usage, 4 a guard refused.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REFS = os.path.join(os.path.dirname(SKILL_DIR), 'plan-pcb-routing', 'references')


# --------------------------------------------------------------------------
# evidence loading -- a guard reads the real artifact, never a pasted claim
# --------------------------------------------------------------------------

def _load(path, what):
    """(data, error_text). A guard that cannot read its evidence refuses."""
    if not path:
        return None, (f'{what} not provided. Produce it first, then re-run '
                      f'this stage with the flag that names it.')
    if not os.path.isfile(path):
        return None, f'{what}: no such file: {path}'
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh), None
    except Exception as exc:                                # noqa: BLE001
        return None, f'{what}: unreadable ({type(exc).__name__}: {exc})'


def err(text):
    return f'<error>\n{text}\n</error>'


# --------------------------------------------------------------------------
# the stages
# --------------------------------------------------------------------------

def p0(a):
    """Decide whether to touch the placement at all."""
    return f'''<stage_instructions stage="P0" name="gate" of="7">
MEASURE this board's placement, then decide. Do not decide first.

The measurement is two commands and it is never optional. Skipping it is how a
board with two parts stacked on each other reaches routing -- every other
instrument in the chain looks at copper, and there is no copper yet.

Run BOTH, on the board with its copper removed. Neither alone is enough: the
first cannot see two parts stacked on the same net, the second is the channel
that can.

  python3 -X utf8 check_drc.py {a.board} --clearance <the board's own floor>
  echo "EXIT=$?"
  python3 -X utf8 check_assembly.py {a.board} --json wk/assembly0.json
  echo "EXIT=$?"

Read the floor off the board (its .kicad_pro netclass or .kicad_dru), never a
round number you chose.

Every violation a COPPER-FREE board returns is a placement defect that no
router can remove.

Then classify by what you MEASURED, and say which row you are in:

  both clean                  -> the placement is fit. Do not run a pass over
                                 it: an optimizer on a placement that already
                                 passes makes it worse (measured -- the default
                                 weights caused two new routing failures). Hand
                                 the board to /plan-pcb-routing and stop here.
                                 This is a verdict you reached, not a default
                                 you assumed.
  board carries copper        -> STOP. Placement moves footprints, not tracks;
                                 the tools exit 3. Re-run from the unrouted board.
  unplaced                    -> P1
  violations, or a mechanically-fixed part where mechanics forbid  -> P2
  rough/imported, all legal   -> P5 (a slate), or P4 for local violations only

Next: python3 -X utf8 {sys.argv[0]} --stage <P1|P2|P4|P5> --board {a.board} \\
          --drc-json wk/drc0.json --assembly-json wk/assembly0.json
</stage_instructions>'''


def p1(a):
    return f'''<stage_instructions stage="P1" name="unplaced" of="7">
The board has no placement to repair. Do not test this with an exit code -- one
placement tool exits 0 and gives advice on a board with every part at its
generator default. Test positively:

  python3 -X utf8 -c "
from kicad_parser import parse_kicad_pcb
p = parse_kicad_pcb('{a.board}')
print('no outline:', p.board_info.board_bounds is None)
print('stacked at defaults:', len({{(round(f.x,3), round(f.y,3))
      for f in p.footprints.values()}}) < len(p.footprints) / 2)"

Walk the ladder in order and say which rung applies:

1. The repo has its own seeder -> run it, then treat the output as a rough
   placement (P4/P5).
2. No seeder, but an intent exists or the spec states placement facts ->
   author the intent (P6), then seed from it:
       python3 -X utf8 place_seed.py {a.board} seed.kicad_pcb --intent fp.json
   The seeder grades its own output against the same intent; exit 4 means the
   seed does not satisfy the intent it was built from, and says which rule broke.
3. Neither -> say so and STOP. This toolchain does not invent a placement, and
   inventing mechanical geometry is what every rule here forbids.

Next: --stage P4 (legalize the seed) or --stage P6 (declare the intent first).
</stage_instructions>'''


def p2(a):
    ok, why = _guard_damage(a)
    if not ok:
        return err(why)
    return f'''<stage_instructions stage="P2" name="mechanical facts" of="7">
Before any search runs, separate the parts whose position is NOT a netlist
question. Each is placed by a determinant you can name, and an optimizer that
moves them is destroying information.

  class                          determined by            detect on any board
  mounting holes / NPTH          the enclosure pattern    pad_type np_thru_hole,
                                                          or 0 connected pins
  edge connectors, castellations the mating standard      courtyard intersects
                                                          (castellated: centred
                                                          on) the outline
  enclosure-referenced parts     an aperture in the spec  SPEC ONLY -- not
  (USB, barrel, RF, buttons)                              board-derivable
  fiducials, test points         a fab or fixture rule    usually spec

Run the lock advisor and act on it:

  python3 -X utf8 place_optimize.py {a.board} --suggest-locks \\
      --suggest-locks-json wk/locks.json

The gate for leaving this stage is `unlocked_high == 0`, or every remaining
finding dispositioned IN WRITING with the reason.

On a DAMAGED board that gate is usually unreachable by locking, and reaching
for it is the trap: a displaced part can carry a high-confidence finding, and
locking it records the damaged pose as a decision every later stage then treats
as ground truth. Disposition instead, per ref, against a measurement. The
advisor demotes a part lying WHOLLY off the board for this reason; a part
hanging PARTLY off an edge it cannot distinguish from a real edge-mounted one,
so that one is yours to judge -- compare its excursion with the other
edge-mounted parts on this board.

A part the FILE marks (locked yes) is never yours to move, whatever any intent
says. Place a part, verify it, then lock it -- never inherit a lock you have
not checked.

Next: python3 -X utf8 {sys.argv[0]} --stage P3 --board {a.board} \\
          --drc-json {a.drc_json or 'wk/drc0.json'} --locks-json wk/locks.json
</stage_instructions>'''


def p3(a):
    ok, why = _guard_damage(a)
    if not ok:
        return err(why)
    locks, lerr = _load(a.locks_json, 'The lock advisor output (--locks-json)')
    if lerr:
        return err(lerr + '\n\nP2 produces it:\n  python3 -X utf8 '
                          f'place_optimize.py {a.board} --suggest-locks '
                          '--json wk/locks.json')
    high = _dig(locks, 'unlocked_high')
    if isinstance(high, int) and high > 0:
        # --waive was used ONLY for its truthiness: the strings were never
        # parsed, the count was never compared to `unlocked_high` (so one
        # `--waive X:y` unblocked a report of 300), and they were never written
        # anywhere. P3 hard-refuses without them, so a resumed run could not
        # re-enter this stage -- run 9's six waivers survive only because the
        # teammate happened to re-type them into a handover message.
        parsed, malformed = {}, []
        for w in (a.waive or []):
            ref, sep, reason = str(w).partition(':')
            if not sep or not ref.strip() or not reason.strip():
                malformed.append(w)
            else:
                parsed[ref.strip()] = reason.strip()
        if malformed:
            return err(
                f'--waive takes REF:reason, and these do not parse: '
                f'{", ".join(repr(m) for m in malformed)}.\n\nThe reason is the '
                f'point -- a waiver without one is a flag that makes the gate '
                f'go away, which is what this stage exists to prevent.')
        if len(parsed) < high:
            return err(
                f'The lock advisor reports unlocked_high = {high}. Those are '
                f'parts whose position looks load-bearing and which nothing is '
                f'holding, so a search is free to move them.\n\nYou waived '
                f'{len(parsed)} of {high}'
                f'{" (" + ", ".join(sorted(parsed)) + ")" if parsed else ""}. '
                f'Lock them, or re-run with --waive REF:reason for EACH one. '
                f'The count used to go unchecked, so a single waiver cleared '
                f'any number of findings.')
        _wp = os.path.join(os.path.dirname(os.path.abspath(a.locks_json)),
                           'waivers.json')
        try:
            with open(_wp, 'w', encoding='utf-8') as _wf:
                json.dump({'board': os.path.abspath(a.board),
                           'unlocked_high': high, 'waivers': parsed},
                          _wf, indent=1, sort_keys=True)
        except OSError:
            _wp = None
    return f'''<stage_instructions stage="P3" name="reconstruct" of="7">
The board is placed WRONG, not merely rough, so the quench is the wrong tool:
it is a local search on a continuous lattice, and what you have is a structural
error. Escalate, do not compose. Each rung has an applicability test; run the
test, and when it fails say so and fall through.

R1  Which parts did P2 establish? Their positions are arithmetic now.
R2  Does the BOARD determine a position? A family whose pattern is
    over-determined by its surviving members predicts the rest. The fit
    PROPOSES; the copper-free measurement DECIDES. Apply a proposal only when
      - the fit is over-determined (>= 2 survivors for a translation,
        >= 3 with rotation or scale), AND
      - the residual collapses to a grid step within a TOLERANCE, not to
        equality, AND
      - applying it improves the copper-free violation count AND does not
        increase the off-board amount.
    Both conjuncts, always: the count alone is gameable by evacuation -- a
    conflict removed by pushing a part off the board reads as an improvement.
    If it does not improve, REVERT: the determinant was not on the board.
R3  Apply with the repair tools, never the from-scratch seeder:
      python3 -X utf8 place_seed.py {a.board} r.kicad_pcb --intent fp.json --repair
      python3 -X utf8 place_reconstruct.py {a.board} r.kicad_pcb [--intent fp.json]
    Both take --dry-run and report what they WOULD do.
R4  Test for a rigid displacement. Offsets of +v and -v are AGREEMENT, not
    disagreement -- an exchange displaces its two groups by opposite vectors,
    and that pair is the swap's signature. Offsets disagreeing in MAGNITUDE
    mean there is no single rigid displacement: stop, go to P5.
R5  Anchor the large parts, then size the gap between two anchors from the
    SMALL PARTS that live in the corridor, not from the routing that crosses
    it (measured: small-part extent correlates with the gap a human left on
    8 of 8 boards; the routing cut does not correlate at all).

After ANY anchor move, re-run the escape ledger for every neighbouring
fine-pitch part -- a widened corridor can eat another part's escape face.

LOOK AT WHAT YOU MOVED. This stage moves parts, and the next one will not open
without a render of the result -- so produce it here, and READ it. --pair diffs
the findings BY NAME across the two boards, which is what says whether the move
fixed anything or just swapped one conflict for another (a level count hides a
swap):

  python3 -X utf8 render_placement.py r.kicad_pcb --before {a.board} --pair \\
      --clearance <the board's own floor> --ignore-nets <the poured nets> \\
      --expect-moved <the count this stage reported> \\
      --json-out wk/render_p3.json -o wk/render_p3.png

It prints WHAT THIS PANEL SHOWS (every finding in words), THE WORST N (one crop
command each) and DECLUTTER (the flags that clear the noise). Run one of the
crops it hands you; that is the whole point of it handing them to you.

Next: python3 -X utf8 {sys.argv[0]} --stage P4 --board r.kicad_pcb \\
          --before {a.board} --drc-json wk/drc1.json \\
          --render-json wk/render_p3.json
</stage_instructions>'''


def p4(a):
    if not a.before:
        return err('P4 compares a result against what it came from, so it '
                   'needs --before <the board this one was derived from>. '
                   'Without it none of the gates below can be a DELTA, and an '
                   'absolute threshold is what made two of them unusable.')
    if not os.path.isfile(a.before):
        return err(f'--before: no such file: {a.before}')
    _ok, _why = _guard_render(a)
    if not _ok:
        return err(_why)
    return f'''<stage_instructions stage="P4" name="fix loop" of="7">
One lap = measure, ONE targeted change, verify. Cap: 5 laps. Anything still
broken at the cap is NAMED with its measurement, not carried silently.

MEASURE (all four, every lap, on the copper-free board):

  python3 -X utf8 check_drc.py {a.board} --clearance <floor> --clearance-margin 0
  python3 -X utf8 check_assembly.py {a.board} --baseline {a.before}
  python3 -X utf8 check_channels.py {a.board} --baseline {a.before} --gate
  python3 -X utf8 check_rigid_consistency.py {a.before} {a.board}

The last three are DELTAS against the board you started from, deliberately.
Each has an absolute form that was measured and refused: a starved escape face,
a courtyard overlap and a contact pair are all routinely properties of the
DESIGN, so the absolute count fires on healthy and human-placed boards alike.
The delta cancels the design term because both boards carry it.

What each one refuses to let pass:
  check_assembly     a blocking pair (two parts on the same copper -- not
                     buildable whatever the nets), or copper on a LOCKED part
  check_channels     a face that now carries demand with no lane left, and did
                     not before
  check_rigid_...    a new contact between two parts moved by DIFFERENT
                     vectors -- impossible in a rigid restore, so the result is
                     a search that happened to fit, not the damage undone

FIX: one change, aimed at a named finding. The eaten_by refs in the channel
ledger are the move targets; the pair members in the assembly report are the
candidates. Do not batch fixes -- a lap that changes three things cannot tell
you which one worked.

VERIFY: re-run all four. A lap is ACCEPTED only if the finding it aimed at is
gone and nothing above it got worse.

Then record it, before starting the next lap:
  python3 -X utf8 converge.py record --ledger wk/ledger.jsonl \\
      --board {a.board} --kind placement --lever "<what you changed and why>" \\
      --argv <the real command that produced this board, as BARE TOKENS>

--argv takes the rest of the line, unquoted, and it must REPLAY: converge
refuses (exit 2) any first token that is not a real file or on PATH, and a
placeholder like "<all but R12>" inside a quoted string makes the whole thing
one unrunnable token. Expand the arguments you actually used.

A lap that did NOT clear its finding is recorded too, with --rejected, and then
stepped back. Keeping it is what makes "two flat laps" detectable -- a loop that
discards its failures cannot tell a plateau from a fresh start -- and the step
back is a checkout of the parent board, siblings included, not a reconstruction:

  python3 -X utf8 converge.py step-back --ledger wk/ledger.jsonl \\
      --out <where to put the restored board>

Two flat laps in a row means the residue is floorplan-shaped, not repairable
here: stop and go to P5.

EVERY LAP THAT MOVES A PART OWES A RENDER, and P6/P-close will not open without
one of the board they are handed. Re-render after each accepted lap, against the
board that lap came from:

  python3 -X utf8 render_placement.py <this lap> --before <the lap before it> \\
      --pair --clearance <floor> --ignore-nets <poured nets> \\
      --expect-moved <what the lever said it moved> \\
      --json-out wk/render_lapN.json -o wk/render_lapN.png

Read WHAT THE MOVE DID: `N fixed, M NEW` is the lap's verdict. A lap that
introduces findings it did not resolve is a lap to revert, and the count alone
will not tell you -- 46 -> 46 can be nine fixed and nine new somewhere else.

Record it: converge.py record ... --render-json wk/render_lapN.json

Next: --stage P5 (a slate) or --stage P6 (declare and grade), then P-close.
</stage_instructions>'''


def p5(a):
    return f'''<stage_instructions stage="P5" name="options" of="7">
Use this when the question is "which arrangement", not "is this one legal".

  python3 -X utf8 place_portfolio.py {a.board} --out-dir wk/slate \\
      --candidates <K> --keep <N> [--full-probe]

Rank rules, in this order:
  1. HARD gates first: legality and the declared intent. A candidate that fails
     either is not in the running, however good it looks.
  2. Prefer a ranking that ROUTED something over one that only measured the
     placement. A placement metric cannot see the thing you are choosing for.
  3. hpwl and crossings ANNOTATE the slate; they do not rank it. Both correlate
     positively with distance-to-truth on damaged boards.

Adopt one deliberately, say why in writing, and re-run P4 on the adopted board.
Adoption is a decision, not a step -- it is not replayable, so it belongs in
the record.

Next: --stage P4 --board <adopted> --before {a.board}
</stage_instructions>'''


def p6(a):
    # Mandate 1: you cannot declare zones for a board you have not looked at.
    # An intent authored off coordinates alone is a guess with a schema.
    _ok, _why = _guard_render(a)
    if not _ok:
        return err(_why)
    return f'''<stage_instructions stage="P6" name="declare the intent" of="7">
An intent turns "it looks right" into something gradable.

  python3 -X utf8 check_floorplan.py {a.board} --emit-intent wk/intent.json
  # then EDIT it down: the emit describes the board as it is, including its
  # damage. Keep what the SPEC requires; delete what is merely observed.

  python3 -X utf8 check_floorplan.py {a.board} --intent wk/intent.json --health

Two traps, both measured:
  - An emitted intent records the board's own geometry as a requirement. On a
    damaged board that bakes the damage in as the target. Entries derived from
    observation are marked suspect for exactly this reason; treat them as
    hypotheses, never as the spec.
  - must_lock is a REQUIREMENT ("these refs must end up locked"), not a
    licence. The file's own (locked yes) stamps are the authority on what may
    move, and they are recorded separately, under context.

A zone that cannot contain a part's courtyard at any rotation is graded on the
part's anchor point instead, and the tool says so.

Next: --stage P4 --board {a.board} --before <the board before any change>
</stage_instructions>'''


def p_close(a):
    if not a.before:
        return err('The close-out compares against the board this run started '
                   'from: pass --before <original>.')
    if not os.path.isfile(a.before):
        return err(f'--before: no such file: {a.before}')
    # The last chance to have looked at what is being handed on. Run 9's
    # placement half closed out having read no image at all, and the omission
    # was invisible afterwards because nothing recorded reads.
    _ok, _why = _guard_render(a)
    if not _ok:
        return err(_why)
    return f'''<stage_instructions stage="P-close" name="close out" of="7">
Prove the placement, then hand it on.

1. RE-MEASURE, exactly as P4 does, and put the numbers in the report. A verdict
   with no numbers beside it is an opinion.
2. Dispatch an INDEPENDENT verifier. Its prompt is a reference file, quoted
   whole -- do not paraphrase it, and do not read it as your own instructions:

<subagent_prompt agent="verifier" description="verify the placement">
Read {os.path.join(REFS, 'verifier-prompts.md')} and apply its placement
lenses to this board. Your inputs are:
    result   {a.board}
    before   {a.before}
    ledger   wk/ledger.jsonl
Re-derive every number yourself from the boards; do not trust the report.
Answer with a line beginning VERDICT= and nothing above it.
</subagent_prompt>

3. The report states, for each item: what was damaged, what changed, the
   measurement that says so, and what remains with WHY it is unfixable here.
4. Placement invalidates every downstream routed board. Say so, and hand the
   board to /plan-pcb-routing -- or to /plan-pcb-placement-and-routing if this
   run also routes.
5. Render the run. Every other artifact is a snapshot; this is the only one
   that shows WHICH lap moved what, and it comes straight off the ledger:

       python3 -X utf8 make_film.py --from-ledger wk/ledger.jsonl -o wk/place.mp4

   Rejected laps are in it too, badged -- seeing where the search went is the
   point. If it comes out one or two beats long, the laps were not recorded and
   the ledger is the thing to fix, not the film.

STOP conditions, name the one that applies:
  - every gate clean;
  - the residue named, measured, and shown unfixable at this stage;
  - two consecutive laps with no change (floorplan-shaped: needs a different
    arrangement, not another repair);
  - the 5-lap cap.
</stage_instructions>'''


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------

def _dig(doc, key):
    """First occurrence of `key` anywhere in a nested JSON document."""
    if isinstance(doc, dict):
        if key in doc:
            return doc[key]
        for v in doc.values():
            got = _dig(v, key)
            if got is not None:
                return got
    elif isinstance(doc, list):
        for v in doc:
            got = _dig(v, key)
            if got is not None:
                return got
    return None


def _guard_damage(a):
    """P2/P3 exist to repair damage; refuse to run them blind, or on a clean board."""
    drc, derr = _load(a.drc_json, 'The copper-free DRC result (--drc-json)')
    if derr:
        return False, (derr + '\n\nP0 produces it:\n  python3 -X utf8 '
                              f'check_drc.py {a.board} --clearance <floor> '
                              '--json wk/drc0.json')
    count = _dig(drc, 'violations')
    if count is None:
        count = _dig(drc, 'total_violations')
    if isinstance(count, list):
        count = len(count)
    if count is None:
        return False, (
            'That JSON carries no violation count, so it does not say whether '
            'this board has placement damage. A file that parses is not '
            'evidence -- an empty or unrelated JSON passes a file-exists check '
            'and answers nothing.\n\nProduce the real measurement:\n'
            f'  python3 -X utf8 check_drc.py {a.board} --clearance <floor> '
            '--json wk/drc0.json')
    if isinstance(count, int) and count == 0:
        asm, _ = _load(a.assembly_json, 'assembly')
        blocking = _dig(asm, 'blocking') if asm else None
        if not blocking:
            return False, (
                'The copper-free board reports 0 violations and no blocking '
                'assembly pair. There is no damage for this stage to repair, '
                'and running a placement search on a legal board makes it '
                'worse (measured).\n\nIf you want a different ARRANGEMENT '
                'rather than a repair, that is --stage P5. If you were '
                'expecting damage, your clearance floor is probably wrong: '
                'read it off the board, not from a round number.')
    return True, ''


def _guard_render(a):
    """A stage that FOLLOWS a move refuses until the move was looked at.

    Run 9 produced ZERO render_placement reads across an entire placement
    campaign and nothing noticed -- not the driver, not the ledger, not the
    operator. The skill mandates a read in eight cases; this file enforced none
    of them, so the mandate was carried entirely by prose that an executor
    skims. That is the same failure mode this whole driver exists to fix: "a
    gate written in prose is a sentence someone skims; a gate that withholds
    the next instructions cannot be skimmed past."

    What it checks, and why each one:
      * the document loads -- a claim is not evidence;
      * `instrument.board` is THIS board -- render_placement records the board
        it rendered, and without this check an earlier lap's render satisfies a
        later stage (the same board-binding hole loop_driver.l2 has);
      * a `checklist` block exists -- a bare `--json` render answers none of
        mandate 8's four questions;
      * `checklist.d_moved.match` is not False -- if the caller declared
        --expect-moved, the render must agree with it.
    """
    doc, derr = _load(a.render_json, 'The placement render (--render-json)')
    if derr:
        return False, (
            derr + '\n\nEvery stage that FOLLOWS a move needs one. Produce it '
                   'against the board this one came from:\n'
                   f'  python3 -X utf8 render_placement.py {a.board} \\\n'
                   f'      --before <the board it was derived from> \\\n'
                   '      --clearance <the board\'s own floor> '
                   '--ignore-nets <the poured nets> \\\n'
                   '      --expect-moved <how many the stage said it moved> \\\n'
                   '      --json-out wk/render.json -o wk/render.png\n\n'
                   'Then READ it -- the JSON is the re-measurement channel, the '
                   'picture is what catches what no metric models.')
    inst = doc.get('instrument') or {}
    shown = inst.get('board')
    if not shown:
        return False, (
            'That render carries no `instrument.board`, so it cannot say WHICH '
            'board it looked at. A render that parses is not evidence that this '
            'board was looked at. Re-render with --json-out (not bare --json).')
    if os.path.normcase(os.path.abspath(shown)) != \
            os.path.normcase(os.path.abspath(a.board)):
        return False, (
            f'That render is of a DIFFERENT board:\n'
            f'      rendered: {shown}\n'
            f'      staging : {os.path.abspath(a.board)}\n\n'
            f'An earlier lap\'s render does not prove this one was looked at.')
    chk = doc.get('checklist')
    if not isinstance(chk, dict):
        return False, (
            'That render has no `checklist` block, so it answers none of the '
            'four questions the read exists to ask: is any part off the '
            'outline, is any part on any other part, is any part on a hole or a '
            'locked part, and did more parts move than the step claimed.\n\n'
            'Re-render with --json-out.')
    d = chk.get('d_moved') or {}
    if d.get('match') is False:
        return False, (
            f'The render disagrees with the move count you declared: it '
            f'measured {d.get("moved")} moved part(s), you passed '
            f'--expect-moved {d.get("expected")}.\n\nOne of the two is wrong, '
            f'and "more parts moved than the step claimed" is exactly what '
            f'mandate 8(d) exists to catch. Resolve it before continuing.')
    return True, ''


STAGES = {
    'P0': p0, 'P1': p1, 'P2': p2, 'P3': p3, 'P4': p4, 'P5': p5, 'P6': p6,
    'P-close': p_close,
}
TITLES = {
    'P0': 'gate -- should the placement be touched at all',
    'P1': 'unplaced ladder',
    'P2': 'the parts whose position is a mechanical fact',
    'P3': 'reconstruct a damaged placement',
    'P4': 'the fix loop (measure, one change, verify)',
    'P5': 'a slate of arrangements',
    'P6': 'declare the floorplan intent',
    'P-close': 'close out and hand on',
}


def _args(argv=None):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stage', choices=sorted(STAGES))
    ap.add_argument('--board', default='board.kicad_pcb')
    ap.add_argument('--before', default=None,
                    help='the board this one was derived from (the delta gates '
                         'need it)')
    ap.add_argument('--drc-json', default=None)
    ap.add_argument('--assembly-json', default=None)
    ap.add_argument('--locks-json', default=None)
    ap.add_argument('--render-json', default=None, metavar='PATH',
                    help='render_placement --json-out document for THIS board. '
                         'Required by every stage that follows a move (P4, P6, '
                         'P-close): the read mandates were prose-only, and a '
                         'whole campaign once ran with zero reads and nothing '
                         'noticed.')
    ap.add_argument('--waive', action='append', default=[], metavar='REF:reason')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--dump-all', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    return ap.parse_args(argv)


def main(argv=None):
    a = _args(argv)
    if a.list:
        for key in ('P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P-close'):
            print(f'  {key:8s} {TITLES[key]}')
        return 0
    if a.dump_all:
        return _dump_all()
    if a.self_test:
        return _self_test()
    if not a.stage:
        print('placement_driver: --stage is required (see --list)',
              file=sys.stderr)
        return 2
    out = STAGES[a.stage](a)
    print(out)
    return 4 if out.startswith('<error>') else 0


def _fake_render(board):
    """The minimum render document `_guard_render` accepts, for the fixtures.

    Deliberately the REAL shape render_placement emits (`instrument.board` +
    a `checklist` with mandate 8's keys), not a stub that happens to pass:
    a fixture that satisfies a guard by a shape the real tool never produces
    would let the guard drift away from its instrument unnoticed.
    """
    return {
        'instrument': {'board': os.path.abspath(board)},
        'checklist': {
            'a_off_outline': {'pad_copper': [], 'courtyard': []},
            'b_pad_clearance_pairs': [], 'b_body_overlap_pairs': [],
            'c_hole_conflicts': [], 'c_locked_refs': [],
            'd_moved': {'moved': 3, 'expected': None, 'match': None},
        },
    }


def _dump_all():
    """Every stage's REAL body, guards satisfied.

    This used to pass filenames that do not exist, so P2, P3 and P4 dumped
    their REFUSALS -- three of eight stages, including the two that carry the
    most commands. Anything auditing the driver through --dump-all (a flag
    checker, a reviewer, a person) was reading error text and seeing no
    commands to be wrong. Guard evidence is cheap to fabricate HERE, where the
    point is to show the instructions rather than to act on them.
    """
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        def wrote(name, doc):
            p = os.path.join(tmp, name)
            with open(p, 'w', encoding='utf-8') as fh:
                _json.dump(doc, fh)
            return p

        board = os.path.join(tmp, 'b.kicad_pcb')
        before = os.path.join(tmp, 'a.kicad_pcb')
        for p in (board, before):
            open(p, 'w', encoding='utf-8').close()
        loose = _args([
            '--board', board, '--before', before,
            '--drc-json', wrote('d.json', {'violations': 3}),
            '--locks-json', wrote('l.json', {'findings': [],
                                             'lock_patterns': []}),
            '--assembly-json', wrote('as.json', {'blocking': 1}),
            '--render-json', wrote('r.json', _fake_render(board)),
            '--waive', 'X:checked'])
        refused = []
        for key in sorted(STAGES):
            body = STAGES[key](loose)
            print(f'===== {key} =====')
            print(body)
            if body.startswith('<error>'):
                refused.append(key)
    if refused:
        # Loud, because a silently-refusing dump is what hid this for a while.
        print(f'\n!! {len(refused)} stage(s) dumped a REFUSAL, not their '
              f'instructions: {", ".join(refused)}')
        return 1
    return 0


def _self_test():
    """Every stage emits; every guard refuses without its evidence."""
    import tempfile
    bad = []

    def want(cond, label):
        print(f'  {"PASS" if cond else "FAIL"}  {label}')
        if not cond:
            bad.append(label)

    for key in sorted(STAGES):
        out = STAGES[key](_args(['--board', 'b.kicad_pcb', '--before',
                                 'a.kicad_pcb']))
        want(out.startswith(('<stage_instructions', '<error>')),
             f'{key} emits a tagged block')
        # Every stage either hands the reader onward or is the terminal one.
        # A stage that ends without saying where to go is where an executor
        # starts improvising, which is the failure this driver exists to stop.
        want(key == 'P-close' or 'Next:' in out or out.startswith('<error>'),
             f'{key} says what comes next')
        # Instructions must fit in a reading, not a scroll.
        want(len(out.splitlines()) <= 80, f'{key} stays under 80 lines')

    # Guards refuse without evidence.
    want(STAGES['P3'](_args(['--board', 'b'])).startswith('<error>'),
         'P3 refuses without the copper-free DRC result')
    want(STAGES['P4'](_args(['--board', 'b'])).startswith('<error>'),
         'P4 refuses without --before (its gates are deltas)')

    with tempfile.TemporaryDirectory() as tmp:
        clean = os.path.join(tmp, 'clean.json')
        json.dump({'violations': 0}, open(clean, 'w', encoding='utf-8'))
        out = STAGES['P3'](_args(['--board', 'b', '--drc-json', clean]))
        want(out.startswith('<error>') and 'no damage' in out,
             'P3 refuses on a board with nothing to repair')

        dmg = os.path.join(tmp, 'dmg.json')
        json.dump({'violations': 12}, open(dmg, 'w', encoding='utf-8'))
        locks = os.path.join(tmp, 'locks.json')
        json.dump({'JSON_SUMMARY': {'unlocked_high': 3}},
                  open(locks, 'w', encoding='utf-8'))
        out = STAGES['P3'](_args(['--board', 'b', '--drc-json', dmg,
                                  '--locks-json', locks]))
        want(out.startswith('<error>') and 'unlocked_high' in out,
             'P3 refuses while load-bearing parts are unlocked')
        # This used to pass ONE waiver against unlocked_high = 3 and assert the
        # stage proceeded -- so the test's own label ("each finding") described
        # a rule the code did not implement and the test did not check.
        out = STAGES['P3'](_args(['--board', 'b', '--drc-json', dmg,
                                  '--locks-json', locks, '--waive', 'U1:checked']))
        want(out.startswith('<error>') and '1 of 3' in out,
             'P3 refuses when the waivers do not cover every finding')
        out = STAGES['P3'](_args(['--board', 'b', '--drc-json', dmg,
                                  '--locks-json', locks,
                                  '--waive', 'U1:checked', '--waive', 'U2:edge',
                                  '--waive', 'U3:standoff']))
        want(out.startswith('<stage_instructions'),
             'P3 proceeds once each finding is waived in writing')
        out = STAGES['P3'](_args(['--board', 'b', '--drc-json', dmg,
                                  '--locks-json', locks, '--waive', 'U1',
                                  '--waive', 'U2:e', '--waive', 'U3:s']))
        want(out.startswith('<error>') and 'do not parse' in out,
             'P3 refuses a waiver with no reason (REF, not REF:reason)')

    # Banned shapes: hedging, and a subagent prompt the model might obey itself.
    # The evidence must be REAL files: this used to pass bare names ('b', 'a',
    # 'd'), so every stage with an existence check dumped its refusal instead of
    # its body and the banned-shape scan ran over error text. It went unnoticed
    # because the only assertion that depended on a body -- the subagent-prompt
    # one -- happened to be satisfied by the one stage that had no such check.
    with tempfile.TemporaryDirectory() as tmp2:
        _b = os.path.join(tmp2, 'b.kicad_pcb')
        _a = os.path.join(tmp2, 'a.kicad_pcb')
        for _p in (_b, _a):
            open(_p, 'w', encoding='utf-8').close()

        def _w(name, doc):
            p = os.path.join(tmp2, name)
            json.dump(doc, open(p, 'w', encoding='utf-8'))
            return p

        _ev = _args(['--board', _b, '--before', _a,
                     '--drc-json', _w('d.json', {'violations': 3}),
                     '--locks-json', _w('l.json', {'findings': []}),
                     '--assembly-json', _w('as.json', {'blocking': 1}),
                     '--render-json', _w('r.json', _fake_render(_b)),
                     '--waive', 'X:y'])
        bodies = {k: STAGES[k](_ev) for k in sorted(STAGES)}
        everything = '\n'.join(bodies.values())
    _refused = [k for k, v in bodies.items() if v.startswith('<error>')]
    want(not _refused,
         f'every stage emits its body under complete evidence '
         f'(refused: {", ".join(_refused) or "none"})')
    for phrase in ('you may want to', 'if you are not sure', 'consider running'):
        want(phrase not in everything.lower(), f'no hedging: {phrase!r}')
    want(everything.count('<subagent_prompt') >= 1,
         'at least one stage dispatches an independent verifier')

    print('OK' if not bad else f'FAIL: {len(bad)}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
