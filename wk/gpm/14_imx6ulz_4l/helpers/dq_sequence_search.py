"""Search route.py step orders that land DRAM_DQ0-7 inside the board's .kicad_dru
length window (11.5-14.5 mm, rule 'byte0 delay matching').

Why a helper (TOOL_GAPS): route.py's --length-match-group matches every member to
the LONGEST member (routed this run or already on the board); it has no target or
window, so one net that routes long sets a target past the window's max, and a
net boxed in mid-bus gets "No straight run with clearance found for meanders".
The only lever left is the ORDER in which the lane's nets are routed, in
separate route.py calls. This script runs candidate orders from one board and
grades each with check_drc's own length measure (net_queries.net_match_length).

usage (from WT): python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/dq_sequence_search.py BASE.kicad_pcb OUTDIR SEQ [SEQ ...]
  SEQ like "57|3m|01246m": steps split by '|', digits = DQ numbers, trailing m = length-matched step
"""
import os
import subprocess
import sys

sys.path.insert(0, 'py_router')
COMMON = ['--layers', 'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu', '--layer-costs', '1.0', '-1', '2.5', '1.0',
          '--track-width', '0.1', '--clearance-ceiling', '0.1', '--via-size', '0.45', '--via-drill', '0.25',
          '--no-bga-zones', '--max-ripup', '5', '--escalation', 'board']
MATCH = ['--length-match-group', '/DRAM/DRAM_DQ[0-7]', '--length-match-tolerance',
         os.environ.get('DQ_TOL', '0.6'), '--meander-amplitude', os.environ.get('DQ_AMP', '0.6')]


def lengths(board):
    from kicad_parser import parse_kicad_pcb
    from net_queries import net_match_length
    pcb = parse_kicad_pcb(board)
    out = {}
    for nid, n in pcb.nets.items():
        if n.name in ['/DRAM/DRAM_DQ%d' % i for i in range(8)]:
            v = net_match_length(pcb, nid, 'total')
            out[int(n.name[-1])] = round(v, 2) if v is not None else None
    return out


def run(base, outdir, seq):
    tag = seq.replace('|', '_')
    cur = base
    for i, step in enumerate(seq.split('|')):
        m = step.endswith('m')
        digits = step.rstrip('m')
        out = os.path.join(outdir, f'{tag}_{i}.kicad_pcb')
        cmd = [sys.executable, '-X', 'utf8', 'py_router/route.py', cur, out, '--nets'] + \
              [f'/DRAM/DRAM_DQ{d}' for d in digits] + COMMON + (MATCH if m else [])
        with open(out.replace('.kicad_pcb', '.log'), 'w') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        if not os.path.exists(out):
            return seq, None, 'step %d wrote nothing' % i
        cur = out
    ls = lengths(cur)
    bad = sum(1 for v in ls.values() if v is None or v < 11.5 or v > 14.5)
    return seq, cur, f'out_of_window={bad} ' + ' '.join(f'DQ{k}={ls[k]}' for k in sorted(ls))


if __name__ == '__main__':
    base, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for seq in sys.argv[3:]:
        s, board, res = run(base, outdir, seq)
        print(s, '->', res, board, flush=True)
