"""Coupled/uncoupled length and P/N skew of the USB pair, read off the copper with the repo's own
net_queries.diff_pair_copper (board_score's diff_pairs component cannot see this pair: KiCad does not
recognise /USB_DP + /USB_DM as a diff pair by name, so it reports pairs {}).
usage: python3 helpers/usb_pair.py <board.kicad_pcb>"""
import sys
sys.path.insert(0, 'py_router')
from kicad_parser import parse_kicad_pcb
from net_queries import diff_pair_copper
pcb = parse_kicad_pcb(sys.argv[1])
ids = {n.name: n.net_id for n in pcb.nets.values()}
rec = diff_pair_copper(pcb, ids['/USB_DP'], ids['/USB_DM'])
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in dict(rec).items()} if hasattr(rec, 'keys') else rec)
