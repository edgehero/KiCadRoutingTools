#!/usr/bin/env python3
"""gp14 staging (ported from fa10): write wk/gp14/NN_<stem>/README.md for every staged board.

    python3 -X utf8 wk/gp14/_staging/write_readme.py
"""
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
FA = os.path.join(ROOT, 'wk', 'gp14')

NOTES = {
    'ecc83-pp_v2': [],
    'sonde_xilinx': ['J1 (DSUB-25) and J2 (DSUB-9) are edge-mount; J2 sits on the bottom side.'],
    'complex_hierarchy': ['165 teardrop zones were removed with the routing (KiCad generates them from the tracks).',
                          'Three repeated sheets: the circuit repeats, so does nothing in the intent.'],
    'multichannel_mixer': ['JUDGMENT: the 16 pots and 6 jacks are front-panel parts; their poses are declared.',
                           'The board keeps 4 groups from the source.',
                           "Board Setup's min_clearance 0.3 / min via 1.5 are above the Default class (0.2 / 0.6)."],
    'interf_u': ['BUS1 (ISA edge fingers) and P1 (DSUB-25) were locked in the source; their poses are declared.'],
    'rp2350_fpga_eensy_prePlane': [
        'JUDGMENT: the source had no .kicad_pro. KiCad wrote one; its floors were then set from the source copper: '
        'Default class 0.09 clearance / 0.09 track / 0.45-0.2 via; Board Setup minimums 0.075 track, 0.25-0.15 via, '
        '0.2 edge clearance.',
        'The source is a pre-plane snapshot: its routing was unfinished, so it is a placement benchmark, not a copper one.',
        'U8 (the Teensy 4.0 frame) was locked in the source; its pose is declared.'],
    'One-Air-Max': ['Six parts locked in the source (USB1, SW1, BAT1, I2C1, I2C2, LED2) have declared poses.',
                    'Board-wide pour definitions are kept; only their fills were removed. Two length-tuning patterns were removed.'],
    'CM5_MINIMA_3': ['JUDGMENT: the two CM5 module connectors (Module301/302, bottom side, one shared origin) and the '
                     'M.2 socket J701 (card length from the M701/M702 standoffs) have declared poses.',
                     'The project has 100 ohm and 50 ohm net classes: impedance-controlled pairs.',
                     "15 length-tuning patterns were removed; the project's DRC exclusions were cleared."],
    'StickHub': ['JUDGMENT: J1, H1 and J2-J8 have declared poses -- the set earlier StickHub runs (36-39) staged as '
                 'locked mechanical parts.',
                 'StickHub is CC BY-NC-SA.'],
    'glasgow_revC': ['Derived by the same rule as every other board, from the human board (GlasgowEmbedded/glasgow '
                     'at d884af4b): its 17 locked parts and MK1-MK4 have declared poses.',
                     'JUDGMENT: MK1-MK4 are 3.5 mm mounting holes, each 4.0 mm in from a board corner (stated for run 34).'],
    'daplink': ['The source was a KiCad 7 file; it was opened and saved once by KiCad 10.0.7 (pcbnew) before '
                'staging, which is what opening it in KiCad 10 does.'],
    'steppenprobe': [],
    'pico_ice_rev3': ['Raspberry Pi Pico form factor; H1-H4 are its mounting holes (declared).'],
    'imx6ulz_4l': ['U1 and U2 (the two BGAs) and J4 were locked in the source; their poses are declared.',
                   'The board ships a .kicad_dru with its own rules; every routing step reads it.'],
}

FORBIDDEN = """- Reading: `wk/gp14/_truth/`, `wk/gp14/_src/`, `wk/gp14/_staging/`, `wk/gp14/_cmp/`, `wk/gp14/_control/`, `wk/gp14/_watch/`,
  `wk/gp14/_phase0/`, `wk/gp14/_old_a22397f9/`, any other `wk/gp14/NN_*` folder, the KiCad demos (`<tmp>),
  `~/Downloads`, any other worktree or checkout (`../krt-film`, `../KiCadRoutingTools`), any copy of a design under
  `kicad_files/` or `tests/fixtures/`, git history of board files, and this board's project on the web.
- Writing anywhere outside this folder; editing the design brief, `mechanical.json` or `intent.json` (their
  sha256 are below and are re-checked).
- Any `gh` write, any subagent except the single verifier the skill specifies."""


def main():
    for d in sorted(glob.glob(os.path.join(FA, '[0-9][0-9]_*'))):
        nn, stem = os.path.basename(d).split('_', 1)
        if os.path.exists(os.path.join(d, 'STATE.md')):
            print('skip', os.path.basename(d), '(a teammate has started it)')
            continue
        T = os.path.join(FA, '_truth', stem)
        stage = json.load(open(os.path.join(T, 'stage.json')))
        log = open(os.path.join(T, 'stage.log'), encoding='utf8', errors='replace').read()
        rows = [l for l in log.splitlines() if re.match(r'^\| [A-Za-z#]', l) and not l.startswith('| ref')]
        decl = '\n'.join(['| ref | channel | footprint | why |', '|---|---|---|---|'] + rows) if rows else \
            '(nothing declared: no locked part, mounting hole or edge connector)'
        ins = '\n'.join(f'| `{n}` | `{h}` |' for n, h in stage['inputs'].items() if n != 'README.md')
        notes = '\n'.join(f'- {n}' for n in NOTES.get(stem, [])) or '- none'
        intent = 'intent.json'
        import sys
        sys.path[:0] = [os.path.join(ROOT, 'py_router')]
        from kicad_parser import parse_kicad_pcb
        pcb = parse_kicad_pcb(os.path.join(d, stem + '.kicad_pcb'))
        padded = [f for f in pcb.footprints.values() if f.pads]
        np, nb = len(padded), sum(1 for f in padded if f.layer == 'B.Cu')
        text = f"""# gp14 board {nn}: {stem}

**Task:** `/plan-pcb-placement full` on `wk/gp14/{nn}_{stem}/{stem}.kicad_pcb` with `{intent}`. Every part starts in the
pile south of the board outline and there is no routing. Place and route the board until it is DONE or a stop rule
fires.

**DONE** (the skill's own definition): `board_score` blocking 0 (unrouted 0, broken 0) and `check_complete` DONE.
After DONE, optimise vias, then copper, then segments, under the skill's stop rules.

## What you are given (rule fa10-decl-v1)

Read off the source board before it was piled, by one rule: parts the source LOCKED and `MountingHole` footprints
get a declared pose in `mechanical.json` (the part still starts in the pile -- the pose is a target); edge
connectors get an EDGE only (`along_edge` unknown) in the design brief, and only when the source seats them within
0.5 mm of that edge. Anything marked JUDGMENT was decided by the campaign organiser and is listed in the notes.
`intent.json` also carries a decap budget derived from the source (which caps belong to which IC, and how far).

{decl}

Notes:
{notes}

Parts keep the side (F.Cu / B.Cu) they had in the source ({nb} of {np} start on the bottom); the pile does not flip
anything. Every lock was removed. Board-wide pours are kept (which net pours where is design intent); local pours
and rule areas smaller than a quarter of the board were removed with the routing. Board-level text, dimensions,
drawings off Edge.Cuts and padless artwork (logos, labels) were removed, and footprint text angles were reset to 0.

## Inputs (sha256, re-checked at the end)

| file | sha256 |
|---|---|
{ins}

## Not allowed

{FORBIDDEN}
"""
        with open(os.path.join(d, 'README.md'), 'w', encoding='utf8') as f:
            f.write(text)
        print('wrote', os.path.join(os.path.basename(d), 'README.md'), len(rows), 'declared row(s)')


if __name__ == '__main__':
    main()
