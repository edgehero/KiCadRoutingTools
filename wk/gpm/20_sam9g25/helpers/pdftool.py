"""Helper: PDF text / page render (poppler is not installed; Read cannot render PDFs).
usage: pdftool.py text PDF [first last]   |  pdftool.py render PDF page outprefix [dpi] [clip x0 y0 x1 y1 (fractions)]
       pdftool.py find PDF regex"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pylib'))
import fitz
cmd, pdf = sys.argv[1], sys.argv[2]
doc = fitz.open(pdf)
if cmd == 'text':
    a = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    b = int(sys.argv[4]) if len(sys.argv) > 4 else doc.page_count
    for i in range(a-1, b):
        print(f'===== page {i+1} =====')
        print(doc[i].get_text())
elif cmd == 'find':
    rx = re.compile(sys.argv[3], re.I)
    for i, p in enumerate(doc):
        for line in p.get_text().splitlines():
            if rx.search(line): print(i+1, line.strip())
elif cmd == 'render':
    pg = int(sys.argv[3]); out = sys.argv[4]
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 150
    page = doc[pg-1]
    clip = None
    if len(sys.argv) > 9:
        r = page.rect; f = [float(x) for x in sys.argv[6:10]]
        clip = fitz.Rect(r.x0 + f[0]*r.width, r.y0 + f[1]*r.height, r.x0 + f[2]*r.width, r.y0 + f[3]*r.height)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    pix.save(out); print('wrote', out, pix.width, pix.height)
