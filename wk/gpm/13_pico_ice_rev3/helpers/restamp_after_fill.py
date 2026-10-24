"""restamp_after_fill.py -- undo the per-via protection overrides a KiCad 10 fill round-trip invents,
then let the repo's own #962 policy declare Type VII where the route step would have.

    python3 -X utf8 wk/gpm/13_pico_ice_rev3/helpers/restamp_after_fill.py FILLED.kicad_pcb INPUT.kicad_pcb OUT.kicad_pcb

Why (TOOL_GAPS "fill_for_delivery"): `fill_for_delivery.py` fills through KiCad 10's pcbnew, which
re-saves a KiCad 8 board (version 20240108) as version 20260206 and writes
`(capping no) (covering (front no) (back no)) (plugging (front no) (back no)) (filling no)` on EVERY
via, equal to the board setup. On the KiCad 8 file the same vias carried no token (they inherit
the setup), so check_drc accepted the vias in paste openings as "undeclarable in this file format".
On the filled file they read as 113 VIA-IN-PASTE violations. `fab_notes.via_protection_stamps` also
treats any spec that names capping/filling as a decision, so it can no longer stamp them.

What it does, and nothing else:
  1. for each `(via ...)` block whose protection tokens are EXACTLY the board setup's values, removes
     those tokens (the via then inherits the same setup -- the effective protection is unchanged);
     a via whose tokens differ from the setup is left alone and reported;
  2. calls `fab_notes.ship_via_protection_file(OUT, via_snapshot(input vias))`, the function the
     CLI route step runs at ship time, which inserts Type VII only on vias in a pad or paste
     opening that this run created (the input board has no vias).
Copper, zones and fills are untouched.
"""
import re
import shutil
import sys

sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb  # noqa: E402
import fab_notes  # noqa: E402

TOKEN_RE = re.compile(r'\n\t\t\((?:capping|filling) (?:yes|no)\)'
                      r'|\n\t\t\((?:covering|plugging)\n\t\t\t\(front (?:yes|no)\)\n\t\t\t\(back (?:yes|no)\)\n\t\t\)')


def setup_tokens(text):
    i = text.find('(setup')
    j = text.find('(pcbplotparams', i)
    blk = text[i:j]
    out = {}
    for name in ('capping', 'filling'):
        m = re.search(r'\(%s (yes|no)\)' % name, blk)
        out[name] = m.group(1) if m else None
    for name in ('covering', 'plugging'):
        m = re.search(r'\(%s\s*\(front (yes|no)\)\s*\(back (yes|no)\)\s*\)' % name, blk)
        out[name] = (m.group(1), m.group(2)) if m else None
    return out


def via_tokens(block):
    out = {}
    for name in ('capping', 'filling'):
        m = re.search(r'\(%s (yes|no)\)' % name, block)
        if m:
            out[name] = m.group(1)
    for name in ('covering', 'plugging'):
        m = re.search(r'\(%s\s*\(front (yes|no)\)\s*\(back (yes|no)\)\s*\)' % name, block)
        if m:
            out[name] = (m.group(1), m.group(2))
    return out


def main():
    filled, input_board, out = sys.argv[1:4]
    text = open(filled, encoding='utf-8').read()
    setup = setup_tokens(text)
    n_strip = n_keep = 0

    def fix(m):
        nonlocal n_strip, n_keep
        block = m.group(0)
        toks = via_tokens(block)
        if toks and all(setup.get(k) == v for k, v in toks.items()):
            n_strip += 1
            return TOKEN_RE.sub('', block)
        if toks:
            n_keep += 1
        return block

    new = re.sub(r'\n\t\(via\n.*?\n\t\)', fix, text, flags=re.S)
    shutil.copyfile(filled, out)  # siblings are the caller's (copy_board)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(new)
    print(f'board setup: {setup}')
    print(f'vias whose tokens equalled the setup, tokens removed: {n_strip}; vias with their own spec kept: {n_keep}')
    inp = parse_kicad_pcb(input_board)
    snap = fab_notes.via_snapshot(inp.vias, inp)
    rec = fab_notes.ship_via_protection_file(out, snap, context='restamp_after_fill')
    print('record:', {k: rec[k] for k in ('count', 'stamped', 'restored', 'protected', 'unstampable')} if rec else None)


if __name__ == '__main__':
    main()
