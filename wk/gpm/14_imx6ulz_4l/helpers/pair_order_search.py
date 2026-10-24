"""Try orders of early route_diff calls for the DDR3 pairs (CLK0, DQS0, DQS1) and report, per order, each pair's
coupled length / P-N skew and the copper left within a via's reach of U2.C1 (the VMEM ball arm A9 walled in).
Helper for TOOL_GAPS 3 (no tool orders pair routing or reserves a plane ball's drop site).
usage (from WT): python3 -X utf8 wk/gpm/14_imx6ulz_4l/helpers/pair_order_search.py BASE.kicad_pcb OUTDIR ORDER [ORDER ...]
  ORDER like "1@2.5|0@6|C@2.5": steps split by '|', 0/1 = DQS0/DQS1, C = CLK0, @cost = In2.Cu layer cost"""
import math, os, subprocess, sys
sys.path.insert(0, 'py_router'); sys.path.insert(0, 'py_tools')
NETS = {'0': "/DRAM/DRAM_DQS0_*", '1': "/DRAM/DRAM_DQS1_*", 'C': "/DRAM/DRAM_CLK0_*"}
def run(base, outdir, order):
    cur = base; tag = order.replace('|', '_').replace('@', 'a').replace('.', 'p')
    for i, st in enumerate(order.split('|')):
        names, cost = st.split('@')
        out = os.path.join(outdir, f'{tag}_{i}.kicad_pcb')
        cmd = [sys.executable, '-X', 'utf8', 'py_router/route_diff.py', cur, out, '--nets'] + [NETS[c] for c in names] + [
            '--track-width', '0.1', '--diff-pair-gap', '0.1', '--clearance-ceiling', '0.1', '--layers', 'F.Cu', 'In1.Cu',
            'In2.Cu', 'B.Cu', '--layer-costs', '1.0', '-1', cost, '1.0', '--via-size', '0.45', '--via-drill', '0.25',
            '--escalation', 'board', '--diff-pair-intra-match']
        with open(out.replace('.kicad_pcb', '.log'), 'w') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        cur = out
    from kicad_parser import parse_kicad_pcb
    from net_queries import diff_pair_copper, net_match_length
    pcb = parse_kicad_pcb(cur)
    nid = {n.name: k for k, n in pcb.nets.items()}
    res = []
    for p in ('CLK0', 'DQS0', 'DQS1'):
        P, N = nid['/DRAM/DRAM_%s_P' % p], nid['/DRAM/DRAM_%s_N' % p]
        r = diff_pair_copper(pcb, P, N, 0.08, 0.15)
        lp, ln = net_match_length(pcb, P, 'total'), net_match_length(pcb, N, 'total')
        res.append(f"{p}: coupled {r.get('coupled_mm', 0):.2f} skew {abs((lp or 0) - (ln or 0)):.2f}")
    def dseg(px, py, s):
        ax, ay, bx, by = s.start_x, s.start_y, s.end_x, s.end_y
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    near = sorted({(s.layer, pcb.nets[s.net_id].name.split('/')[-1]) for s in pcb.segments
                   if pcb.nets[s.net_id].name != 'VMEM' and dseg(73.6, 107.8, s) < 0.375 + s.width / 2})
    return order, cur, '; '.join(res) + f' | near U2.C1: {near}'
if __name__ == '__main__':
    base, outdir = sys.argv[1], sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    for o in sys.argv[3:]:
        print(*run(base, outdir, o), flush=True)
