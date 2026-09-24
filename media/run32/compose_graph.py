"""run32 movie + progress graph (disclosed helper; reads the ledger and frames, writes media only).

Chart: every ledger row's open connections (board_score unrouted + broken) against run time,
log y, coloured by kind/outcome, with the best accepted routed value as a step line.
A marker tracks each movie frame's run time: routing frames carry krt:t_epoch in their PNG
metadata; placement-film frames have none and are interpolated between their boards' mtimes.
"""
import glob
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import imageio.v2 as iio  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W = 'wk/run32'
M = W + '/movie'
T0 = 1790114214.425            # run start (cmd_timing.jsonl first row), = frame 0's krt:run_started
HOURS = lambda t: (t - T0) / 3600.0  # noqa: E731

rows = [json.loads(l) for l in open(W + '/ledger.jsonl', encoding='utf-8')]
pts = []
for r in rows:
    b = (r.get('score') or {}).get('blocking_by') or {}
    if not b:
        continue
    y = (b.get('unrouted') or 0) + (b.get('broken') or 0)
    inval = 'INVALID LAP' in (r.get('lever') or '')
    pts.append((HOURS(r['t']), max(y, 1), r['kind'], bool(r.get('accepted')), inval))

FW = 1200
fig = plt.figure(figsize=(FW / 100, 2.9), dpi=100, facecolor='#0e0f12')
ax = fig.add_axes([0.06, 0.2, 0.92, 0.66], facecolor='#15171c')
for sp in ax.spines.values():
    sp.set_color('#555')
ax.tick_params(colors='#bbb', labelsize=9)


def sc(sel, **kw):
    s = [p for p in pts if sel(p)]
    if s:
        ax.scatter([p[0] for p in s], [p[1] for p in s], **kw)


sc(lambda p: p[2] == 'completion' and not p[3] and not p[4], s=9, c='#6b6f78', label='routing lap, rejected')
sc(lambda p: p[4], s=14, c='#d9534f', marker='x', label='INVALID lap (broken test)')
sc(lambda p: p[2] == 'placement', s=26, c='#5aa9e6', marker='s', label='placement lap (no copper yet)')
sc(lambda p: p[2] == 'completion' and p[3], s=22, c='#4cd07d', label='routing lap, accepted')
# best accepted routed value ON THE CURRENT PLACEMENT: reset at every placement-shaped classification
resets = sorted(HOURS(r['t']) for r in rows if r['kind'] == 'classification' and r.get('shape') == 'placement')
segs, best, cur = [], None, []
for p in sorted(pts):
    while resets and p[0] >= resets[0]:
        if cur:
            segs.append(cur)
        cur, best = [], None
        resets.pop(0)
    if p[2] == 'completion' and p[3] and p[1] < 120:
        best = p[1] if best is None else min(best, p[1])
    if best is not None:
        cur.append((p[0], best))
if cur:
    segs.append(cur)
for i, sg in enumerate(segs):
    ax.step([q[0] for q in sg], [q[1] for q in sg], where='post', color='#f0c24b', lw=2,
            label='best routed board on the current placement' if i == 0 else None)
for r in rows:
    if r['kind'] == 'classification':
        ax.axvline(HOURS(r['t']), color='#b07cf0', lw=1, ls='--', alpha=.8)
ax.set_yscale('log')
ax.set_ylim(8, 700)
ax.set_yticks([10, 19, 30, 50, 100, 250, 500])
ax.set_yticklabels(['10', '19', '30', '50', '100', '250', '500'])
xmax = HOURS(rows[-1]['t']) + 0.3
ax.set_xlim(0, xmax)
ax.set_xlabel('run time (h)   |   dashed violet = a failure classified (placement re-entry)', color='#bbb', fontsize=9)
ax.set_title('open connections (unrouted + broken, board_score) per ledger row -- 223 rows', color='#eee', fontsize=11, loc='left')
ax.legend(loc='upper right', fontsize=8, facecolor='#15171c', edgecolor='#444', labelcolor='#ddd', ncol=3)
ax.grid(color='#2a2d34', lw=.6)
fig.canvas.draw()
base = Image.frombytes('RGBA', fig.canvas.get_width_height(), bytes(fig.canvas.buffer_rgba())).convert('RGB')
# data -> pixel for x
(x0, _), (x1, _) = ax.transData.transform([(0, 10), (xmax, 10)])
bb = ax.get_window_extent()
Hfig = base.height
ytop, ybot = Hfig - bb.y1, Hfig - bb.y0
plt.close(fig)


def strip(t_epoch):
    im = base.copy()
    d = ImageDraw.Draw(im)
    x = x0 + (x1 - x0) * (HOURS(t_epoch) / xmax)
    d.line([(x, ytop), (x, ybot)], fill=(255, 255, 255), width=2)
    d.polygon([(x - 6, ytop - 9), (x + 6, ytop - 9), (x, ytop)], fill=(255, 255, 255))
    return im


# placement film: 7 beats, interpolate time between the beat boards' mtimes
beats = ['glasgow_unplaced', 'pipe/s1_a', 'pipe/s1_b', 'pipe/s1_c', 'placed', 'placed_v2', 'placed_v3']
bt = [T0] + [os.path.getmtime(f'{W}/{b}.kicad_pcb') for b in beats[1:]]
P = sorted(glob.glob(M + '/pframes/frame_*.png'))
R = sorted(glob.glob(M + '/frames/frame_*.png'))
FWr, FHr = Image.open(R[0]).size


def pad(im):
    c = Image.new('RGB', (FWr, FHr), (14, 15, 18))
    im = im.convert('RGB')
    c.paste(im, ((FWr - im.width) // 2, (FHr - im.height) // 2))
    return c


frames = []
n = len(P)
for i, f in enumerate(P):
    u = i / max(n - 1, 1) * (len(bt) - 1)
    k = min(int(u), len(bt) - 2)
    t = bt[k] + (bt[k + 1] - bt[k]) * (u - k)
    frames.append((pad(Image.open(f)), t))
for f in R:
    im = Image.open(f)
    t = float(im.info.get('krt:t_epoch', bt[-1]))
    t = max(t, bt[-1])   # frame 0's clock basis is run-start; the routing chain begins after placed_v3
    frames.append((im.convert('RGB'), t))
frames += [frames[-1]] * 30

out = []
for im, t in frames:
    s = strip(t)
    c = Image.new('RGB', (FWr, FHr + s.height), (14, 15, 18))
    c.paste(im, (0, 0))
    c.paste(s.resize((FWr, s.height)), (0, FHr))
    out.append(c)

w = iio.get_writer(M + '/run32_graph.mp4', fps=10, codec='libx264', quality=8, macro_block_size=8)
for c in out:
    w.append_data(np.asarray(c))
w.close()
g = [c.resize((560, int(c.height * 560 / c.width)), Image.LANCZOS).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
     for c in out[::2]]
g[0].save(M + '/run32_graph.gif', save_all=True, append_images=g[1:], duration=200, loop=0, optimize=True)
out[len(P) + 150].save(M + '/run32_graph_still.png')
print(len(out), out[0].size)
