#!/usr/bin/env python3
"""gp14: side-by-side placement image, human (left) vs ours (right), per side.

    python3 -X utf8 wk/gp14/_staging/compose_compare.py STEM

Reads _cmp/STEM/place_{human,ours}_{F,B}.png (render_placement --per-side) and
writes _cmp/STEM/compare_{F,B}.png, each panel captioned with its own metrics.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FA = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def font(sz):
    for f in ('arialbd.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def main(stem):
    C = os.path.join(FA, '_cmp', stem)
    summ = json.load(open(os.path.join(C, 'summary.json'), encoding='utf-8'))
    for side in ('F', 'B'):
        paths = [os.path.join(C, f'place_{w}_{side}.png') for w in ('human', 'ours')]
        if not all(os.path.exists(p) for p in paths):
            continue
        ims = [Image.open(p).convert('RGB') for p in paths]
        h = max(i.height for i in ims)
        ims = [i.resize((int(i.width * h / i.height), h)) if i.height != h else i for i in ims]
        bar = 70
        out = Image.new('RGB', (sum(i.width for i in ims) + 20, h + bar), 'white')
        d = ImageDraw.Draw(out)
        x = 0
        for who, im in zip(('human', 'ours'), ims):
            out.paste(im, (x, bar))
            m = summ['placement_' + who]
            label = (f"{'HUMAN' if who == 'human' else 'gp14 (AI, grouped-placement)'}  side {side}   crossings {m.get('crossings')}"
                     f"   hpwl {round(m['hpwl']) if m.get('hpwl') else '-'} mm")
            d.text((x + 12, 18), label, fill="black", font=font(24))
            x += im.width + 20
        # keep the file a sensible size for a GitHub comment
        if out.width > 2400:
            out = out.resize((2400, int(out.height * 2400 / out.width)))
        out.save(os.path.join(C, f'compare_{side}.png'), optimize=True)
        print('wrote', f'compare_{side}.png', out.size)


if __name__ == '__main__':
    main(sys.argv[1])
