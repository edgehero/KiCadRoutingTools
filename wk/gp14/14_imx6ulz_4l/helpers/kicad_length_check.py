#!/usr/bin/env python3
"""Grade a board's .kicad_dru LENGTH rules (min/max window) with KiCad's own DRC.

No repo tool grades an absolute length window: route.py prints "length has no
consumer in this tool yet" for the .kicad_dru rule, board_score --length-groups
grades only a spread (tolerance), and check_drc has no length check. This runs
kicad-cli pcb drc on a temp copy (board + .kicad_pro + .kicad_dru) and lists
every length_out_of_range item, plus the other copper-error classes KiCad sees.

usage: python3 helpers/kicad_length_check.py BOARD.kicad_pcb [--json OUT]
"""
import collections, json, os, re, shutil, subprocess, sys, tempfile

KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def main():
    board = sys.argv[1]
    out = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    stem = board[:-len('.kicad_pcb')]
    tmp = tempfile.mkdtemp(prefix='klen_')
    for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
        if os.path.isfile(stem + ext):
            shutil.copy(stem + ext, os.path.join(tmp, 't' + ext))
    if not os.path.isfile(os.path.join(tmp, 't.kicad_dru')):
        print('NO .kicad_dru beside the board: nothing declares a length rule')
    rep = os.path.join(tmp, 'drc.json')
    r = subprocess.run([KICAD_CLI, 'pcb', 'drc', '--format', 'json', '--severity-all',
                        '--refill-zones', '-o', rep, os.path.join(tmp, 't.kicad_pcb')],
                       capture_output=True, text=True)
    if not os.path.isfile(rep):
        print('kicad-cli wrote no report:', r.stdout[-500:], r.stderr[-500:])
        sys.exit(2)
    d = json.load(open(rep))
    viol = d.get('violations', [])
    lens = []
    for v in viol:
        if v['type'] == 'length_out_of_range':
            nets = sorted({m.group(1) for i in v['items']
                           for m in [re.search(r'\[(/[^\]]+)\]', i.get('description', ''))] if m})
            lens.append({'nets': nets, 'description': v['description']})
    counts = collections.Counter(v['type'] for v in viol)
    copper = {k: n for k, n in counts.items()
              if k in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance',
                       'copper_edge_clearance', 'hole_to_hole', 'courtyards_overlap',
                       'length_out_of_range', 'track_width', 'via_diameter', 'annular_width',
                       'drill_out_of_range', 'unconnected_items', 'skew_out_of_range')}
    res = {'board': board, 'length_out_of_range': len(lens), 'length_items': lens,
           'unconnected_items': len(d.get('unconnected_items', [])),
           'copper_classes': copper, 'all_classes': dict(counts)}
    print(f"length_out_of_range {len(lens)}  unconnected {res['unconnected_items']}  copper {copper}")
    for it in lens:
        print('  ', it['nets'], it['description'])
    for v in viol:
        if v['type'] in ('shorting_items', 'tracks_crossing', 'clearance', 'hole_clearance', 'copper_edge_clearance'):
            print('   ', v['type'], v['description'][:90], '|', ' / '.join(i.get('description', '')[:60] for i in v['items'][:2]),
                  '@', ' '.join(f"({i['pos']['x']:.2f},{i['pos']['y']:.2f})" for i in v['items'][:1]))
    if out:
        json.dump(res, open(out, 'w'), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
