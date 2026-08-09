#!/usr/bin/env python3
"""The routing chain, one stage at a time, with only the stages this board needs.

Two things a document cannot do, and this can.

FIRST, it emits one stage. A skill file is read whole, so every reader of the
routing half pays for the BGA escape arithmetic, the impedance ladder and the
plane-repair doctrine even on a two-layer board with none of them.

SECOND, it computes the chain from the BOARD. The stage list is not a fixed
recipe with "skip if not applicable" notes -- the notes are what get misread. A
board with no fine-pitch parts is never told about fanout; a board with no
plane nets is never told about pours or plane repair. What you are shown is
what you run.

    python3 -X utf8 <this> --stage A1 --board b.kicad_pcb
    python3 -X utf8 <this> --plan --board b.kicad_pcb     # the chain, computed
    python3 -X utf8 <this> --list
    python3 -X utf8 <this> --dump-all
    python3 -X utf8 <this> --self-test

Tags: <stage_instructions> act on these; <subagent_prompt> copy verbatim into a
subagent; <error> you skipped evidence.

Exit: 0 emitted, 2 usage, 4 a guard refused.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REFS = os.path.join(SKILL_DIR, 'references')


def err(text):
    return f'<error>\n{text}\n</error>'


def _load(path, what):
    if not path:
        return None, (f'{what} not provided.')
    if not os.path.isfile(path):
        return None, f'{what}: no such file: {path}'
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh), None
    except Exception as exc:                                # noqa: BLE001
        return None, f'{what}: unreadable ({type(exc).__name__}: {exc})'


# --------------------------------------------------------------------------
# board facts -- what decides which stages exist
# --------------------------------------------------------------------------

def board_facts(board):
    """(facts, error). Read from the board; never guessed, never asked for."""
    # repo root = .../<repo>/.claude/skills/<skill>/scripts -> up four
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(HERE))))
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from kicad_parser import parse_kicad_pcb, detect_package_type
    except Exception as exc:                                # noqa: BLE001
        return None, f'cannot import the parser ({exc})'
    if not os.path.isfile(board):
        return None, f'no such board: {board}'
    try:
        pcb = parse_kicad_pcb(board)
    except Exception as exc:                                # noqa: BLE001
        return None, f'cannot parse {board}: {exc}'

    layers = list(getattr(pcb.board_info, 'copper_layers', []) or [])
    fine = []
    for ref, fp in sorted((pcb.footprints or {}).items()):
        try:
            if detect_package_type(fp) in ('QFN', 'QFP', 'BGA', 'PGA', 'LGA'):
                fine.append(ref)
        except Exception:
            pass
    names = [n.name for n in (pcb.nets or {}).values() if n.name]
    powerish = [n for n in names
                if n.upper().lstrip('/+').startswith(
                    ('GND', 'VCC', 'VDD', 'VSS', '3V3', '5V', '1V8', 'AGND'))]
    # A diff pair, conservatively: two net names differing only in a P/N or
    # +/- suffix. Names alone under-count (that is why a separate skill exists
    # to find them by pin function) -- so this only decides whether to SHOW the
    # stage, and the stage itself says to confirm.
    stems = {}
    for n in names:
        for a, b in (('_P', '_N'), ('+', '-'), ('_p', '_n')):
            if n.endswith(a):
                stems.setdefault(n[:-len(a)], set()).add('P')
            elif n.endswith(b):
                stems.setdefault(n[:-len(b)], set()).add('N')
    pairs = sorted(s for s, v in stems.items() if v == {'P', 'N'})
    return {
        'board': board,
        'layers': len(layers) or 2,
        'layer_names': layers,
        'nets': len(names),
        'fine_pitch': fine,
        'plane_candidates': sorted(set(powerish)),
        'diff_pair_stems': pairs,
        'has_copper': bool(pcb.segments or pcb.vias),
    }, None


def chain_for(f):
    """The stages this board actually needs, in order."""
    steps = [('A1', 'read the board and state what it is'),
             ('A2', 'layers and stackup')]
    if f['fine_pitch']:
        steps.append(('A3', 'which parts need a fanout, and would benefit'))
    steps.append(('A4', 'diff pairs, power nets, and the design rules'))
    if f['plane_candidates']:
        steps.append(('A5', 'which nets become planes, on which layers'))
    steps.append(('A6', 'the net-coverage partition (a gate for every R stage)'))
    if f['plane_candidates']:
        steps.append(('R1', 'pour the planes, bare, on the empty board'))
    if f['fine_pitch']:
        steps.append(('R2', 'fanout the fine-pitch parts'))
        steps.append(('R3', 'clear decap/fanout-via collisions'))
    if f['diff_pair_stems']:
        steps.append(('R4', 'differential pairs and impedance nets'))
    steps.append(('R5', 'the bulk signal route'))
    if f['plane_candidates']:
        steps.append(('R6', 'finalize the planes (stitching, return vias)'))
        steps.append(('R7', 'repair disconnected plane regions'))
        steps.append(('R8', 'reconnect what the repair ripped'))
    steps.append(('R9', 'verify: DRC, connectivity, orphan stubs, coverage'))
    steps.append(('V1', 'score it, and audit the score'))
    steps.append(('V2', 'classify the blocker and pick the cheapest lever'))
    steps.append(('V3', 'apply, accept or revert, and record'))
    steps.append(('V5', 'stop conditions and close-out'))
    return steps


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------

def _facts_or_err(a):
    f, e = board_facts(a.board)
    if e:
        return None, err(f'{e}\n\nEvery stage in this driver is computed from '
                         f'the board, so it cannot run without one. Pass '
                         f'--board <file>.')
    # R1 only. R2 was in this tuple and could never be reached: R1's own
    # `Next:` hands R2 the board R1 just poured, and R2's first line says
    # "escape the fine-pitch parts ON THE POURED BOARD". Both were written in
    # the same commit (255af97), so this is choosing between two co-authored
    # intents rather than restoring a lost one -- and R2's text is the one that
    # describes the chain the rest of the file computes.
    #
    # It was not a latent edge case. `has_copper` is segments-or-vias, and
    # `route_planes` places real copper: one 266-part board came out of R1 with
    # 241 vias and 1915 traces, so R2 refused on the FIRST hop of the normal
    # chain and the run had to work around its own driver.
    if f['has_copper'] and a.stage == 'R1':
        return None, err(
            'This board already carries copper, and the pour assumes an empty '
            'board -- a fanout\'s escape stubs are signal copper, and pouring '
            'over them seals the channels they need. Re-run the chain from the '
            'unrouted board, or pick the stage you actually mean to re-enter '
            'at.')
    return f, None


def a1(a, f):
    return f'''<stage_instructions stage="A1" name="read the board">
State what this board IS before planning anything for it. Read, do not assume:

  python3 -X utf8 list_nets.py {a.board} --design-rules
  python3 -X utf8 check_drc.py {a.board} --clearance <the board's own floor>

Read from THIS board, measured just now:
  copper layers      {f['layers']}  ({', '.join(f['layer_names']) or 'unnamed'})
  nets               {f['nets']}
  fine-pitch parts   {len(f['fine_pitch'])}{': ' + ', '.join(f['fine_pitch'][:8]) if f['fine_pitch'] else ' -- no fanout stage in this chain'}
  plane candidates   {len(f['plane_candidates'])}{': ' + ', '.join(f['plane_candidates'][:8]) if f['plane_candidates'] else ' -- no pour or plane stages in this chain'}
  diff-pair stems    {len(f['diff_pair_stems'])}{': ' + ', '.join(f['diff_pair_stems'][:6]) if f['diff_pair_stems'] else ' -- no diff-pair stage in this chain'}
  carries copper     {f['has_copper']}

The clearance floor comes off the board (its .kicad_pro netclass, its
.kicad_dru rules), never from a round number. Grading at a floor the board was
not routed to manufactures violations that are not there.

Before any of this is worth doing, the placement must have been MEASURED fit
(the copper-free check_drc + check_assembly pair). If that has not happened on
this board, stop and do it: no routing parameter recovers a placement defect,
and every instrument from here on looks at copper.

Next: --stage A2 --board {a.board}   (or --plan for the whole computed chain)
</stage_instructions>'''


def a2(a, f):
    tail = ('' if f['layers'] > 2 else '''
This is a TWO-LAYER board. Everything about inner-layer plane costs and
4+-layer pour strategy is absent from this chain on purpose -- it does not
apply. What does: on a dense two-layer board the layer-cost balance is the
lever, and the default is often too steep. Rebalance toward 1.0/1.5, then
1.0/1.0, and compare via counts.''')
    return f'''<stage_instructions stage="A2" name="layers and stackup">
{f['layers']} copper layer(s): {', '.join(f['layer_names']) or 'unnamed'}.

  python3 -X utf8 -c "
from kicad_parser import parse_kicad_pcb
b = parse_kicad_pcb('{a.board}').board_info
print('stackup layers:', len(b.stackup))
for l in b.stackup[:12]: print(' ', l.name, l.layer_type, l.thickness, l.epsilon_r)"

An empty or default stackup means impedance targets cannot be computed and
must not be claimed. Say so rather than routing to a number nobody derived.{tail}

Next: --stage {'A3' if f['fine_pitch'] else 'A4'} --board {a.board}
</stage_instructions>'''


def a3(a, f):
    return f'''<stage_instructions stage="A3" name="fanout">
Fine-pitch parts on this board: {', '.join(f['fine_pitch'])}

Needing a fanout and BENEFITING from one are different questions. Ask all four
per part, and answer them from the board:
  1. Are there interior pads that no edge lane can reach? (they need a via,
     not a lane -- that is the actual fanout signal)
  2. Does the escape budget close? via + track + 2*clearance + margin must fit
     within the pad pitch.
  3. Do the parts' own escape faces have lanes left?
       python3 -X utf8 check_channels.py {a.board}
  4. Are the plane balls excluded, so they get plane-drop vias instead of
     escape routes?

Decide per part, from those four answers, not from a prior. When 1 and 2 both
pass with room to spare, the case for a fanout is weak -- an escape stub is
committed copper that later steps must route around -- but that is a
CONCLUSION the four measurements support or refuse, part by part. Name the
answer that decided each one.

Next: --stage A4 --board {a.board}
</stage_instructions>'''


def a4(a, f):
    dp = (f'''Diff-pair stems found BY NAME: {', '.join(f['diff_pair_stems'][:10])}
Name matching under-counts -- pairs whose names do not follow P/N convention
are invisible to it. Confirm by pin function before routing them:
  /identify-diff-pairs   (a separate skill; it reads datasheets)'''
          if f['diff_pair_stems'] else
          'No P/N-suffixed net names on this board, so no diff-pair stage is in\n'
          'this chain. If the board HAS pairs under other names, find them now:\n'
          '  /identify-diff-pairs')
    return f'''<stage_instructions stage="A4" name="pairs, power, rules">
{dp}

The board's own rules outrank any default you would otherwise pass:
  python3 -X utf8 list_nets.py {a.board} --design-rules

And a requirements document, if one exists, outranks the board's rules. Read it
before choosing a width, a clearance, or an impedance -- a spec clause is the
one input none of these tools can derive.

Power nets: {', '.join(f['plane_candidates'][:10]) or '(none by name)'}
Width is a REQUEST, not a result. Whatever you set, measure the emitted copper
afterwards; the router does not complain when it cannot honour a width.

Next: --stage {'A5' if f['plane_candidates'] else 'A6'} --board {a.board}
</stage_instructions>'''


def a5(a, f):
    return f'''<stage_instructions stage="A5" name="plane mapping">
Plane candidates by name: {', '.join(f['plane_candidates'])}

Decide which become planes and on which layers. The signal-integrity reasoning
(GND adjacency for return paths, GND/VCC pairing for interplane capacitance,
split layers for multiple rails) has its own skill:
  /recommend-plane-mappings

The output you need here is a net -> layer map, because two later gates consume
it: the coverage partition (A6) and the layer costs the bulk route uses.

Next: --stage A6 --board {a.board}
</stage_instructions>'''


def a6(a, f):
    return f'''<stage_instructions stage="A6" name="coverage partition">
Every net is routed by exactly one stage. Write that partition down NOW, as
JSON, because every R stage below refuses to run without it:

  wk/coverage.json
  {{"planes": ["GND", "VCC"], "diff_pairs": ["USB_*"], "impedance": [],
    "signals": ["*"], "signals_exclude": ["GND", "VCC", "USB_*"]}}

A catch-all "signals": ["*"] claims the plane nets too, so the exclude list is
not optional bookkeeping -- it is the half that makes this a partition.

Then assert it against THIS BOARD's net list, before any command runs:

  python3 -X utf8 -c "
import fnmatch, json
from kicad_parser import parse_kicad_pcb
c = json.load(open('wk/coverage.json'))
nets = sorted({{n.name for n in parse_kicad_pcb('{a.board}').nets.values()
               if n.name}})
buckets = [k for k in c if not k.endswith('_exclude')]
own = {{}}
for name in nets:
    own[name] = [k for k in buckets
                 if any(fnmatch.fnmatch(name, p) for p in c[k])
                 and not any(fnmatch.fnmatch(name, p)
                             for p in c.get(k + '_exclude', []))]
twice = {{n: v for n, v in own.items() if len(v) > 1}}
never = [n for n, v in own.items() if not v]
print(f'{{len(nets)}} nets: {{len(twice)}} claimed twice, '
      f'{{len(never)}} claimed by nobody')
assert not twice and not never, \\
    f'partition leak\\n  twice: {{twice}}\\n  never: {{never[:20]}}'
print('partition OK')"

Expand the globs against the real nets, as above. Comparing the bucket lists to
each other proves nothing: the earlier form of this check asserted
`planes == c.get('signals_exclude', planes)`, whose default makes it a
comparison of a value with itself. It printed "partition OK" for a coverage
file with no exclude list at all -- the exact leak it was written to catch.

The failure this prevents: a net that belongs to the pour also appearing in the
bulk route's net list, so the router lays copper for a net the pour already
owns -- or the reverse, a net nobody routes and nobody notices until the
connectivity check at the end.

Next: --stage {'R1' if f['plane_candidates'] else 'R5'} --board {a.board} \\
          --coverage wk/coverage.json
</stage_instructions>'''


def _needs_coverage(a):
    cov, cerr = _load(a.coverage, 'The net-coverage partition (--coverage)')
    if cerr:
        return err(cerr + '\n\nA6 produces it. Every routing stage refuses '
                          'without it, because a net routed by two stages (or '
                          'by none) is the failure that is hardest to see '
                          'afterwards.')
    # A partition with no parts is not a partition. Checking only that the file
    # parses lets `{}` satisfy the gate every R stage claims to be protected
    # by -- the file-exists check wearing a partition's name.
    missing = [k for k in ('planes', 'signals') if not isinstance(
        (cov or {}).get(k), list)]
    if missing:
        return err(
            f'The coverage file carries no {" and no ".join(missing)} list, so '
            f'it does not partition anything. Every net on this board belongs '
            f'to exactly one stage, and this file is where that is written '
            f'down.\n\nA6 says how to build it. An empty JSON parses and '
            f'answers nothing, which is why this refuses rather than '
            f'proceeding.')
    return None


def r1(a, f):
    return f'''<stage_instructions stage="R1" name="pour the planes FIRST">
Pour on the EMPTY board, before the fanout. Nets and layers only:

  python3 -X utf8 route_planes.py {a.board} board_R1.kicad_pcb \\
      --nets {' '.join(f['plane_candidates']) or 'GND'} \\
      --plane-layers <one BARE layer name per net, in the same order>

--plane-layers is REQUIRED and is not --layers: --layers is the routing layer
set. Its format is BARE LAYER NAMES positionally matched to --nets, NOT
net:layer pairs -- A5 gives you a net -> layer MAP, and you pass only its
right-hand column, in --nets order:

  --nets GND GNDA --plane-layers B.Cu B.Cu

Passing `GND:B.Cu` writes a zone on a layer that does not exist. KiCad then
refuses the whole board ("Failed to load board") while every in-repo checker
still reads it as fine -- run 11 lost two full routing laps to exactly this.
route_planes now refuses it against the board's own copper layers, but the
mistake is easier not to make.

The net list above is every plane candidate this board has; confirm each
one belongs on a plane before pouring it, and drop the ones that do not. A
two-pad filter net whose name merely starts with GND or VCC is not a plane.

NO --add-gnd-vias, NO --stitch-vias, NO --rip-blocker-nets at this stage: each
adapts to signals that do not exist yet.

The ordering is mechanical, not stylistic. A fanout's escape stubs ARE signal
copper, and the pour step refuses (exit 3) to pour over a partially-routed
board carrying bare pads. Fanout first and this stage cannot run.

Next: --stage {'R2' if f['fine_pitch'] else 'R5'} --board board_R1.kicad_pcb \\
          --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r2(a, f):
    return f'''<stage_instructions stage="R2" name="fanout">
Escape the fine-pitch parts on the poured board: {', '.join(f['fine_pitch'])}

Exclude the plane nets -- the exclusion is exactly what marks their balls for
plane-drop vias, which the intact pour picks up at fill:

  python3 -X utf8 bga_fanout.py board_R1.kicad_pcb board_R2.kicad_pcb \\
      --nets "*" {' '.join('"!' + n + '"' for n in f['plane_candidates'])}

GATE before moving on: failed == 0 and no drc_grazes class. A fanout that left
escapes unrouted has committed copper that every later stage must route around,
and retrying it later is more expensive than fixing it now.

Next: --stage R3 --board board_R2.kicad_pcb --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r3(a, f):
    return f'''<stage_instructions stage="R3" name="decap clearance">
Fanout vias and decoupling caps compete for the same space under a fine-pitch
part. Clear the collisions before signal routing, not after:

  python3 -X utf8 place_fanout_clearance.py board_R2.kicad_pcb board_R3.kicad_pcb

This moves PARTS, so everything it touches is a placement change: re-check the
placement gates if it moves anything load-bearing.

Next: --stage {'R4' if f['diff_pair_stems'] else 'R5'} --board board_R3.kicad_pcb \\
          --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r4(a, f):
    return f'''<stage_instructions stage="R4" name="pairs and impedance">
The most constrained routes claim their channels before anything else can block
them. Stems seen by name: {', '.join(f['diff_pair_stems'][:8])}

  python3 -X utf8 route_diff.py <in> --output board_R4.kicad_pcb \\
      --nets <confirmed pair stems> --clearance <floor>

Both members of a pair route together or the pair is not routed. A "partial"
pair is a single-ended net with a misleading name.

If the pairs carry an IMPEDANCE spec, add --impedance <ohms> and DROP
--clearance: it is a ceiling over every net class, so passing it clamps the
impedance classes down to the floor and the writeback then rewrites them. The
one case where omitting a clearance is correct is this one.

After this stage those nets are EXCLUDED from every later net list -- they are
already routed, and re-routing them silently is how a matched pair becomes
unmatched.

Next: --stage R5 --board board_R4.kicad_pcb --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r5(a, f):
    lc = ('\n--layer-costs is MANDATORY here: a solid pour exists, and without\n'
          'the cost the router will cut through it wherever that is shortest.\n'
          'Derive it from the plane map (~3x on plane layers).\n\n'
          'Its format is BARE FLOATS positionally matched to --layers, not\n'
          'layer:cost pairs -- argparse rejects those as an invalid float:\n\n'
          '  --layers F.Cu B.Cu --layer-costs 1.0 3.0\n\n'
          'A negative cost FORBIDS a layer: its copper still blocks and vias\n'
          'may span it, but no track is placed on it. Pass --layers whenever\n'
          'you pass costs, so the pairing is visible instead of implied.'
          if f['plane_candidates'] else
          '\nNo planes on this board, so no layer costs to derive.')
    return f'''<stage_instructions stage="R5" name="the bulk signal route">
Everything the partition assigns to signals, excluding what earlier stages
already routed:

  python3 -X utf8 route.py <in> board_R5.kicad_pcb \\
      --nets "*" <exclusions from the partition> \\
      --clearance <floor> --track-width <from A4> \\
      [--layer-costs ...] 2>&1 | tee wk/route.log
{lc}

EVERY step below that searches takes `--deadline`, and the value must be BELOW
THE SMALLEST CAP IN THE STACK -- including your harness's. A 2400s deadline
inside a 600s window can never fire: the harness sends SIGTERM, the tool's own
shutdown never runs, and you get exit 143 with no partial board, no
`complete:false` and no summary. 143 and 124 are the SHELL's codes, not a
tool's. Run anything long detached rather than raising the number.

Do NOT pass --max-iterations: the router self-budgets. Rip-up depth 3-5;
deeper measured WORSE, because a ripped victim whose corridor is taken cannot
be restored.

Read the JSON summary, not the console tail: min_clearance_used tells you what
the router actually honoured, which is frequently not what you asked for.

Next: --stage {'R6' if f['plane_candidates'] else 'R9'} --board board_R5.kicad_pcb \\
          --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r6(a, f):
    return f'''<stage_instructions stage="R6" name="finalize the planes">
Now the signals exist, so stitching and return vias can adapt to them:

  python3 -X utf8 route_planes.py board_R5.kicad_pcb board_R6.kicad_pcb \\
      --nets {' '.join(f['plane_candidates'])} \\
      --plane-layers <the same BARE layer names as R1> --add-gnd-vias --stitch-vias

Pour the SAME nets on the same layers as R1. A net poured at R1 and missing
here keeps R1's copper and gets no stitching. Same format rule as R1: bare
layer names positionally matched to --nets, never net:layer pairs.

Prefer the no-rip form first. --rip-blocker-nets leaves nets unrouted for a
later stage to reconnect, and a rip whose restore fails ships an open net.

Next: --stage R7 --board board_R6.kicad_pcb --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r7(a, f):
    return f'''<stage_instructions stage="R7" name="repair plane regions">
  python3 -X utf8 route_disconnected_planes.py board_R6.kicad_pcb board_R7.kicad_pcb \\
      --nets {' '.join(f['plane_candidates'])} --clearance <floor>

This step's reconnect runs at THIS step's parameters, so restate every per-net
constraint that matters (widths, layers, power-net widths) -- none of them
persists from an earlier command.

Read ripped_still_open in its JSON summary and its exit code: nets it ripped
and could neither reconnect nor restore ship OPEN, and the run exits nonzero
when they do.

Next: --stage R8 --board board_R7.kicad_pcb --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r8(a, f):
    return f'''<stage_instructions stage="R8" name="reconnect what was ripped">
Reconnect the casualties, mirroring every constrained pass in the SAME order
they ran originally, and sweeping the remainder last. A net reconnected under
default parameters has silently lost whatever width or layer constraint it
carried.

Next: --stage R9 --board board_R8.kicad_pcb --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def r9(a, f):
    return f'''<stage_instructions stage="R9" name="verify">
Four instruments, none of which replaces another. Do NOT pipe a gate -- a
truncated read is how a failing board reads as passing:

  python3 -X utf8 check_drc.py <board> --clearance <floor> --clearance-margin 0.1
  python3 -X utf8 check_connected.py <board>
  python3 -X utf8 check_orphan_stubs.py <board>
  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/board_score.py <board> \\
      --json wk/score.json

--clearance-margin 0.1 on a ROUTED board: the margin is a fraction of the
clearance, and at 0 the grid quantization of the copper itself (~8 um) is
reported as violations. Grade a COPPER-FREE board at 0 -- there is no routed
geometry to quantize, and a real pad overlap must not be filtered.

Connectivity is orthogonal to DRC: a DRC-clean board can be entirely
disconnected, because isolated copper has no clearance conflicts.

Also read the fab-floor line the DRC writeback prints. If it relaxed a track or
via minimum, this board grades clean against a rule it just rewrote -- confirm
the fab supports the new number before calling it done.

Next: --stage V1 --board <board> --coverage {a.coverage or 'wk/coverage.json'}
</stage_instructions>'''


def v1(a, f):
    return f'''<stage_instructions stage="V1" name="score and audit the score">
  python3 -X utf8 .claude/skills/plan-pcb-routing/scripts/board_score.py \\
      <board> --json wk/score.json <every clause-carrying flag this board has>

Then audit it before believing it:
  - a component reported `ungraded` was NOT examined. Report it as unexamined,
    never as clean.
  - `blocking == null` is not `blocking == 0`.
  - quality (vias, copper, segments) is a tie-break ONLY at blocking == 0.
    Comparing it earlier lets a router trade a disconnected net for a via.

Read {os.path.join(REFS, 'evidence-map.md')} before quoting any
number from any instrument: it says which key answers which question.

Next: --stage V2 --board <board> --score wk/score.json
</stage_instructions>'''


def v2(a, f):
    score, serr = _load(a.score, 'The board score (--score)')
    if serr:
        return err(serr + '\n\nV1 produces it. Choosing a lever without the '
                          'score is how a run spends its budget on the wrong '
                          'component.')
    blocking = score.get('blocking') if isinstance(score, dict) else None
    if blocking is None:
        return err('The score carries no `blocking` value, or it is null. That '
                   'is not zero -- it means something was not graded. Fix the '
                   'instrument first: a systemic iteration, not a routing one.')
    if blocking == 0:
        return f'''<stage_instructions stage="V2" name="classify" note="blocking is 0">
blocking == 0. There is no lever to choose: this board is deliverable on the
gates measured so far.

Confirm nothing is merely UNGRADED (V1's audit), then go to close-out.

Next: --stage V5 --board {a.board} --score {a.score}
</stage_instructions>'''
    return f'''<stage_instructions stage="V2" name="classify the blocker">
blocking = {blocking}. Classify BEFORE retrying; the classification decides
which of three very different levers applies.

Choose by the connectivity-first ladder, in this order -- NOT by which
blocking_by entry is largest. "The biggest entry names the lever" is wrong and
it wrecked a run:

  1. unrouted   nets with no copper at all
  2. broken     nets whose copper does not connect their pads
  3. widths     copper narrower than its clause requires
  4. floorplan  a clause no arrangement at this placement can satisfy
  5. drc        clearance violations

Then classify the SHAPE of the failure:

  parameter-shaped   grid, rip-up depth, layer costs, width -> re-enter at the
                     failing ROUTING stage with the parameter changed
  placement-shaped   a starved escape face, a part its net cannot reach ->
                     STOP. No router setting adds a lane.
  floorplan-shaped   the arrangement cannot satisfy the clause -> a different
                     arrangement, not another retry

THE SHAPE ALSO DECIDES WHO ACTS ON IT, and that depends on how you were
started. If a parent loop dispatched you -- you were handed a ledger and told
the placement is frozen -- then you own `parameter` and nothing else:

  parameter    yours. Re-enter your failing R stage, record the lap, carry on.
  placement    NOT yours. Report the shape and STOP.
  floorplan    NOT yours. Report the shape and STOP.

Both of those mean changing halves, which invalidates every routed board
including the one you just made, and that decision belongs to the loop that can
see both halves. A half that re-places locally is doing the outer loop's job
invisibly: measured on run 14, the outer L3 and L4 never fired once because
this stage's own conclusion never left this stage.

If nobody dispatched you -- you are driving this skill directly -- then all
three are yours, and a placement-shaped failure means going to
/plan-pcb-placement and restarting the chain from its output.

Next: --stage V3 --board {a.board} --score {a.score}
</stage_instructions>'''


def v3(a, f):
    return f'''<stage_instructions stage="V3" name="apply, accept, record">
Apply ONE lever. Re-score with the same flags, and write to a FRESH output
path: the routing steps write a sibling .kicad_pro carrying the DRC floor, so
re-running to the same path reads that floor back and the iteration differs
from its predecessor in two ways rather than one. Number the outputs.

ACCEPT only if blocking strictly decreased, or it is level and quality
improved. Two exceptions, both real:
  - connectivity outranks everything: an iteration that connects a net and
    raises drc is progress;
  - blocking may RISE because more of the board became measurable. Compare
    what each score LOOKED AT before comparing the scores.

Record before the next iteration starts:
  python3 -X utf8 converge.py record --ledger wk/ledger.jsonl --board <board> \\
      --kind completion --lever "<what and why>" --score-file wk/score.json \\
      --argv <the real command, as BARE TOKENS -- it takes the rest of the line>

--argv must REPLAY: converge refuses (exit 2) a first token that is not a real
file or on PATH, so expand every argument instead of writing a placeholder
inside quotes -- quoted, the whole command becomes one unrunnable token.

Failing nets go in by NAME. A count forces every later reader to re-derive the
set, and a truncated re-derivation shipped a wrong close-out.

ON A REJECT: record it ANYWAY, with --rejected, and then step back. Both halves
of that matter. A rejected iteration is data -- it is what makes "five
consecutive with no change" detectable at all, and a run that simply discards
its failures cannot tell a plateau from a fresh start. And stepping back is a
CHECKOUT, not a reconstruction: the board store has the parent byte-for-byte,
siblings included.

  python3 -X utf8 converge.py record --ledger wk/ledger.jsonl --board <board> \\
      --kind completion --rejected --lever "<what and why it did not work>" \\
      --score-file wk/score.json --argv <the real command>
  python3 -X utf8 converge.py step-back --ledger wk/ledger.jsonl \\
      --out <where to put the restored board>

With no --to/--iteration it returns to the last ACCEPTED board, which is what
you want after a failed lever.

Next: --stage V2 (another lever) or --stage V5 (close out)
</stage_instructions>'''


#: The routed-board lenses, and the slice each one is handed.
#: verifier-prompts.md says "fan these out in one response, each handed only
#: its slice" and "never hand a verifier the raw .kicad_pcb" -- V5 used to
#: dispatch ONE agent, for all three lenses, with the board itself as the
#: input, in violation of the file it was quoting.
ROUTED_LENSES = (
    ('connectivity', 'conn.txt (check_connected), wk/score.json, and the '
                     '--nets list every routing step was given',
     'reconcile score.json#/components/unrouted/count and /broken/count '
     'against conn.txt. A net left unrouted because it was excluded from '
     'every step and never poured is a FAIL, not an absence'),
    ('drc', 'drc.txt (check_drc --max-print 0), wk/score.json, and the '
            'clearance the copper was ACTUALLY routed to',
     'score.json#/components/drc/graded_at must equal the routed floor. If '
     'the spec states sizes and board_score was called without them, FAIL on '
     'that alone'),
    ('spec', 'wk/score.json, the requirements document, and intent.json',
     'walk every numeric requirement to a measurement. Entries in '
     'score.json#/ungraded are findings: ungraded is not passed'),
)


def v5(a, f):
    # Same guard as V2, for the same reason: the close-out is where the run
    # ships, and it had NO guard at all -- a chain could be "closed out" with
    # no score, no ledger and no verifier ever dispatched.
    _score, _serr = _load(a.score, 'The board score (--score)')
    if _serr:
        return err(_serr + '\n\nV1 produces it. A close-out without the score '
                           'is a claim, not a measurement.')
    lenses = list(getattr(a, 'lens', None) or [])
    seen = set()
    for v in lenses:
        m = re.match(r'^VERDICT=(PASS|FAIL):lens=([A-Za-z0-9_-]+)', v.strip())
        if m:
            seen.add(m.group(2))
    missing = [n for n, _, _ in ROUTED_LENSES if n not in seen]

    if lenses and missing:
        return err(
            f'The close-out is missing {len(missing)} routed-board lens '
            f'verdict(s): {", ".join(missing)}.\n\n"blocking == 0" and "every '
            f'lens passes" are two different claims, and only the first has a '
            f'number. Dispatch the missing lens(es) and pass each VERDICT= '
            f'line back as --lens.')

    if not lenses:
        blocks = '\n\n'.join(
            f'''<subagent_prompt agent="verifier" description="lens {name}">
Read {os.path.join(REFS, 'verifier-prompts.md')} and apply lens `{name}` to
this board, and ONLY that lens. Your inputs are:
    {inputs}
{rule}.
Re-derive every number yourself; do not trust the report. Answer with one line
beginning VERDICT= and nothing above it.
</subagent_prompt>''' for name, inputs, rule in ROUTED_LENSES)
        return f'''<stage_instructions stage="V5" name="close out: verify">
Three routed-board lenses, fanned out IN ONE RESPONSE, each handed only its
slice. Never hand a verifier the raw .kicad_pcb: it is the thing they are
supposed to be independent of.

{blocks}

Then come back with every verdict line, verbatim:

  python3 -X utf8 {sys.argv[0]} --stage V5 --board {a.board} \\
      --score {a.score or 'wk/score.json'} \\
      --lens "VERDICT=..." --lens "VERDICT=..." --lens "VERDICT=..."
</stage_instructions>'''

    failed = [v for v in lenses if v.strip().startswith('VERDICT=FAIL')]
    return f'''<stage_instructions stage="V5" name="close out">
{len(lenses)} lens verdict(s) in hand, {len(failed)} FAILED.

Stop on one of these, and NAME which:
  1. blocking == 0 and every lens passes;
  2. the budget is spent;
  3. five consecutive iterations with no change;
  4. the remaining work is measured-unfixable at this stage, and said so.

"It looks done" and "the router says routed" are not stop conditions. A
router's own tally can come from a local proxy while pads stay disconnected.
{"A FAILED lens means `blocking` was not really zero, so condition 1 is not "
 "available: spend an iteration on it, or stop on 2 or 4 and report it as an "
 "outstanding blocker." if failed else ""}
Produce the close-out document -- it is what the loop's L5 gate reads, and it
fails CLOSED where board_score does not:

  python3 -X utf8 check_complete.py {a.board} \\
      --authored-from <the board this chain STARTED from> \\
      --json wk/routing_close.json

--authored-from is not bookkeeping: without it the fab-floor check cannot run
at all and UNSOUND becomes unreachable. The writeback only ever loosens, so the
original project is the only thing left to compare against.

Then close the ledger with the verdicts attached:

  python3 -X utf8 converge.py record --ledger wk/ledger.jsonl \\
      --board {a.board} --kind completion --final --stop-condition <1-4> \\
      --score-file {a.score or 'wk/score.json'} \\
      {" ".join(f'--lens "{v}"' for v in lenses[:3])} \\
      --argv <the command that produced this board>

The report states, per component: the number, the instrument that produced it,
and for anything unresolved WHY it is unfixable here.
</stage_instructions>'''


STAGES = {'A1': a1, 'A2': a2, 'A3': a3, 'A4': a4, 'A5': a5, 'A6': a6,
          'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4, 'R5': r5, 'R6': r6,
          'R7': r7, 'R8': r8, 'R9': r9,
          'V1': v1, 'V2': v2, 'V3': v3, 'V5': v5}
COVERAGE_GATED = {'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9'}


def _args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stage', choices=sorted(STAGES))
    ap.add_argument('--board', default='board.kicad_pcb')
    ap.add_argument('--coverage', default=None)
    ap.add_argument('--score', default=None)
    ap.add_argument('--lens', action='append', default=None, metavar='VERDICT',
                    help="a routed-board lens verdict, verbatim from the "
                         "verifier: 'VERDICT=PASS:lens=connectivity'. "
                         "Repeatable. V5 fans the lenses out when none are "
                         "given and closes out when all three are in hand.")
    ap.add_argument('--plan', action='store_true',
                    help='the chain this board needs, computed from the board')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--dump-all', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    return ap.parse_args(argv)


def main(argv=None):
    a = _args(argv)
    if a.list:
        for k in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'R1', 'R2', 'R3', 'R4',
                  'R5', 'R6', 'R7', 'R8', 'R9', 'V1', 'V2', 'V3', 'V5'):
            print(f'  {k}')
        return 0
    if a.self_test:
        return _self_test()
    if a.dump_all:
        # Guard evidence must EXIST here, or the stages behind a guard dump
        # their refusal instead of their instructions and anything auditing
        # this output reads error text where the commands should be.
        import json as _json
        import tempfile
        fake = {'board': 'b.kicad_pcb', 'layers': 4,
                'layer_names': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
                'nets': 120, 'fine_pitch': ['U1'],
                'plane_candidates': ['GND', '+3V3'],
                'diff_pair_stems': ['USB'], 'has_copper': False}
        refused = []
        with tempfile.TemporaryDirectory() as tmp:
            def wrote(name, doc):
                p = os.path.join(tmp, name)
                with open(p, 'w', encoding='utf-8') as fh:
                    _json.dump(doc, fh)
                return p
            loose = _args([
                '--board', 'b.kicad_pcb',
                '--coverage', wrote('c.json', {'planes': ['GND'],
                                               'signals': ['*'],
                                               'signals_exclude': ['GND']}),
                '--score', wrote('s.json', {'blocking': 2, 'unrouted': 1,
                                            'drc': 0, 'open': 1})])
            for k in sorted(STAGES):
                print(f'===== {k} =====')
                loose.stage = k
                body = STAGES[k](loose, fake)
                print(body)
                if body.startswith('<error>'):
                    refused.append(k)
        if refused:
            print(f'\n!! {len(refused)} stage(s) dumped a REFUSAL, not their '
                  f'instructions: {", ".join(refused)}')
            return 1
        return 0
    if a.plan:
        f, e = board_facts(a.board)
        if e:
            print(err(e))
            return 4
        print(f'<stage_instructions stage="plan" name="the chain this board '
              f'needs">')
        print(f'Computed from {a.board}: {f["layers"]} layer(s), '
              f'{len(f["fine_pitch"])} fine-pitch part(s), '
              f'{len(f["plane_candidates"])} plane candidate(s), '
              f'{len(f["diff_pair_stems"])} diff-pair stem(s).\n')
        for key, title in chain_for(f):
            print(f'  {key:3s}  {title}')
        skipped = sorted(set(STAGES) - {k for k, _ in chain_for(f)})
        if skipped:
            print(f'\nNot in this chain (this board has no such work): '
                  f'{", ".join(skipped)}')
        print('\nRun them in order, one at a time:\n'
              f'  python3 -X utf8 {sys.argv[0]} --stage A1 --board {a.board}')
        print('</stage_instructions>')
        return 0
    if not a.stage:
        print('routing_driver: --stage is required (see --list, --plan)',
              file=sys.stderr)
        return 2
    f, e = _facts_or_err(a)
    if e:
        print(e)
        return 4
    if a.stage in COVERAGE_GATED:
        refusal = _needs_coverage(a)
        if refusal:
            print(refusal)
            return 4
    out = STAGES[a.stage](a, f)
    print(out)
    return 4 if out.startswith('<error>') else 0


def _self_test():
    bad = []

    def want(cond, label):
        print(f'  {"PASS" if cond else "FAIL"}  {label}')
        if not cond:
            bad.append(label)

    two_layer = {'board': 'b.kicad_pcb', 'layers': 2,
                 'layer_names': ['F.Cu', 'B.Cu'], 'nets': 40,
                 'fine_pitch': [], 'plane_candidates': [],
                 'diff_pair_stems': [], 'has_copper': False}
    dense = {'board': 'b.kicad_pcb', 'layers': 4,
             'layer_names': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'], 'nets': 300,
             'fine_pitch': ['U1'], 'plane_candidates': ['GND', '+3V3'],
             'diff_pair_stems': ['USB'], 'has_copper': False}

    simple = {k for k, _ in chain_for(two_layer)}
    full = {k for k, _ in chain_for(dense)}
    want('R2' not in simple, 'a board with no fine-pitch part gets no fanout stage')
    want('R1' not in simple, 'a board with no plane nets gets no pour stage')
    want('R4' not in simple, 'a board with no pairs gets no diff-pair stage')
    want('R5' in simple and 'R9' in simple, 'every board still routes and verifies')
    want(full > simple, 'a dense board gets strictly more stages')
    want({'R1', 'R2', 'R4', 'R7'} <= full, 'a dense board gets all of them')

    a = _args(['--board', 'b.kicad_pcb', '--coverage', 'c.json',
               '--score', 's.json'])
    for key, fn in sorted(STAGES.items()):
        a.stage = key
        out = fn(a, dense)
        want(out.startswith(('<stage_instructions', '<error>')),
             f'{key} emits a tagged block')
        want(len(out.splitlines()) <= 60, f'{key} stays under 60 lines')

    a2_ = _args(['--board', 'b.kicad_pcb'])
    want('TWO-LAYER' in STAGES['A2'](a2_, two_layer),
         'a two-layer board is told the two-layer lever')
    want('TWO-LAYER' not in STAGES['A2'](a2_, dense),
         '...and a 4-layer board is not')
    want('MANDATORY' in STAGES['R5'](_args(['--board', 'b', '--coverage', 'c']), dense),
         'layer costs are mandatory when a pour exists')
    want('No planes' in STAGES['R5'](_args(['--board', 'b', '--coverage', 'c']),
                                     two_layer),
         '...and explicitly absent when none does')

    want(_needs_coverage(_args(['--board', 'b'])) is not None,
         'an R stage refuses without the coverage partition')

    # Assembled from SATISFIED args. `a` above names files that do not exist,
    # which was fine while no stage validated them -- V5 now does, so a
    # refusal would silently empty the sweep below and the subagent-prompt
    # assertion would pass on a stage that no longer emits one. (loop_driver's
    # self-test had to learn the same thing.)
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _sp = os.path.join(_td, 's.json')
        with open(_sp, 'w', encoding='utf-8') as _fh:
            json.dump({'blocking': 3, 'blocking_by': {}}, _fh)
        _sat = _args(['--board', 'b.kicad_pcb', '--coverage', 'c.json',
                      '--score', _sp])
        everything = '\n'.join(fn(_sat, dense) for fn in STAGES.values())
        want('<error>' not in everything,
             'every stage emits instructions when its guards are satisfied')

        # V5 has two branches and the sweep above only sees the first. With
        # the verdicts in hand it must stop fanning out and start closing out.
        _closing = STAGES['V5'](_args(
            ['--board', 'b.kicad_pcb', '--coverage', 'c.json', '--score', _sp,
             '--lens', 'VERDICT=PASS:lens=connectivity',
             '--lens', 'VERDICT=PASS:lens=drc',
             '--lens', 'VERDICT=PASS:lens=spec']), dense)
        want('check_complete.py' in _closing and '--authored-from' in _closing,
             'V5 with every lens in hand names the close-out document')
        want('--lens' in _closing and 'converge.py record' in _closing,
             '...and carries the verdicts into the ledger record')
        _partial = STAGES['V5'](_args(
            ['--board', 'b.kicad_pcb', '--coverage', 'c.json', '--score', _sp,
             '--lens', 'VERDICT=PASS:lens=connectivity']), dense)
        want(_partial.startswith('<error>') and 'drc' in _partial
             and 'spec' in _partial,
             'V5 refuses a partial lens set and names what is missing')
        want(STAGES['V5'](_args(['--board', 'b.kicad_pcb',
                                 '--coverage', 'c.json']),
                          dense).startswith('<error>'),
             'V5 refuses without a score, as V2 does')
        want(everything.count('<subagent_prompt') >= 3,
             'the close-out fans out one verifier PER LENS, not one for all '
             'three')

    for phrase in ('you may want to', 'if you are not sure', 'perhaps'):
        want(phrase not in everything.lower(), f'no hedging: {phrase!r}')
    # The forbidden flag may be NAMED (to forbid it) but never offered. The
    # distinction is whether it appears inside a command line.
    offered = [ln for ln in everything.splitlines()
               if '--max-iterations' in ln
               and ('python3' in ln or ln.lstrip().startswith(('--', 'route')))]
    want(not offered, 'the forbidden flag is named to forbid it, never offered')
    want(everything.count('<subagent_prompt') >= 1,
         'the close-out dispatches an independent verifier')

    # ---- the copper guard, which had NO coverage in either direction -------
    # Every fixture above pins `has_copper: False` and calls the stage
    # functions directly, bypassing _facts_or_err entirely -- so the guard that
    # decides which stages may see copper was never executed by a test. R2 sat
    # in that guard while R1's own `Next:` handed it a poured board, and the
    # contradiction survived because nothing ran it.
    import types as _types
    _real = globals()['board_facts']
    try:
        for _copper in (True, False):
            globals()['board_facts'] = (
                lambda _b, _c=_copper: (dict(dense, has_copper=_c), None))
            for _stage in ('R1', 'R2'):
                _a = _types.SimpleNamespace(board='b.kicad_pcb', stage=_stage)
                _f, _e = _facts_or_err(_a)
                _refused = _e is not None
                if _copper and _stage == 'R1':
                    want(_refused, 'R1 refuses a board that already has copper')
                elif _copper and _stage == 'R2':
                    want(not _refused,
                         'R2 does NOT refuse a poured board -- it is the stage '
                         'that runs ON one')
                else:
                    want(not _refused,
                         f'{_stage} opens on an empty board')
    finally:
        globals()['board_facts'] = _real

    print('OK' if not bad else f'FAIL: {len(bad)}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
