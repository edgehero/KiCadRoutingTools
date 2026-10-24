"""trim_spur.py -- remove the dead-end /USB_D+ F.Cu spur route.py shipped on
final_route/s4_route.kicad_pcb (check_weird `kicad-dangling` at (139.75, 116.062),
which fails check_complete's weird_copper gate). No repo tool removes it: route.py's
#1217 split pass ran and left it, and check_join only ADDS copper.

Edits, by uuid (each asserted to hold the coordinates check_weird named):
  * a27f8f19...: (138.0,114.3)-(139.8,116.1) w0.0889 -> end at (139.35,115.662132),
    the T-joint where the R63-side 0.15 mm chain ends on it;
  * 4ad7c124...: (139.8,116.1)-(139.75,116.1) deleted;
  * 9ff67522...: (139.75,116.062132)-(139.75,116.1) deleted.
Usage: python3 trim_spur.py IN.kicad_pcb OUT.kicad_pcb  (OUT must already exist as a
copy_board copy of IN, so its siblings are in place; it is rewritten in place).
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()


def block(uuid):
    m = re.search(r'\n\t\(segment\n(?:(?!\n\t\)).)*?\(uuid "' + uuid + r'"\)\n\t\)', t, re.S)
    assert m, uuid
    return m


edits = {
    'a27f8f19-e313-4259-bc69-2800ef328c53': ('(end 139.800000 116.100000)', '(end 139.350000 115.662132)'),
    '4ad7c124-7234-464a-a4e6-69d5e8f458fa': ('(start 139.800000 116.100000)', None),
    '9ff67522-4386-4af2-b3ae-36a9d1abf151': ('(start 139.750000 116.062132)', None),
}
for uuid, (must, new) in edits.items():
    m = block(uuid)
    b = m.group(0)
    assert must in b and '(net 25)' in b and '(layer "F.Cu")' in b, (uuid, b)
    nb = '' if new is None else b.replace(must, new)
    t = t[:m.start()] + nb + t[m.end():]
    print(('trimmed ' if new else 'deleted ') + uuid)
open(dst, 'w', encoding='utf-8').write(t)
