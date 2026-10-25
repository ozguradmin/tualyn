import sys, os, json; sys.path.insert(0, '.')
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import kbd, report
OUT = '../out'
INK, INK2, MUTED, GRID, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df', '#fcfcfb'
STOCK, MOD = '#2a78d6', '#eb6834'
plt.rcParams.update({'font.size': 9, 'text.color': INK, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.edgecolor': GRID, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'font.family': 'DejaVu Sans'})
fig = plt.figure(figsize=(11, 8.2))
gs = fig.add_gridspec(2, 4, height_ratios=[1.25, 1], hspace=0.5, wspace=0.12)
ax = fig.add_subplot(gs[0, :])
kb = kbd.Keyboard('K2', 'real', seed=0)
cx0, cx1, cy0, cy1 = kb.base
ax.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fc='#f1f0ec', ec=GRID, lw=1))
for (x, y, w, d, zt) in kb.keys:
    ax.add_patch(Rectangle((x - w / 2, y - d / 2), w, d, fc='#dddcd6', ec='none'))
tr = json.load(open(f'{OUT}/tracks_K2.json'))
for x in tr:
    T = np.array(x['track'])
    col = STOCK if x['name'] == 'BASE' else MOD
    ax.plot(T[:, 8], T[:, 9], color=col, lw=2, solid_capstyle='round')
    ax.plot(T[0, 8], T[0, 9], 'o', ms=6, color=col, mec=SURF, mew=1.5)
    if x['result'] in ('fell', 'off'):
        ax.plot(T[-1, 8], T[-1, 9], 'x', ms=9, mew=2.2, color=col)
ax.text(300, 129, 'nav-cluster holes', ha='center', va='bottom', color=INK2, fontsize=8)
ax.annotate('front edge (user side): 4-6° tilt runs downhill toward here', xy=(215, cy0), xytext=(215, -40), ha='center', color=INK2, fontsize=8,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8))
ax.plot([], [], color=STOCK, lw=2, label='package trot, stock Tarçın')
ax.plot([], [], color=MOD, lw=2, label='wide track + ski paws + spread trot')
ax.plot([], [], 'o', color=MUTED, label='start'); ax.plot([], [], 'x', mew=2, color=MUTED, label='fell / stepped off')
ax.legend(loc='upper left', bbox_to_anchor=(0, 1.13), ncol=4, frameon=False, fontsize=8.5)
ax.set_xlim(-25, 455); ax.set_ylim(-55, 150); ax.set_aspect('equal')
ax.set_xlabel('mm along the rows'); ax.set_yticks([0, 50, 100]); ax.set_ylabel('mm')
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
ax.set_title('Body path on the full-size mechanical keyboard (K2), along the rows, same 4 starts, μ 0.4', loc='left', fontsize=10, color=INK, pad=24)
cfg = [('BASE', 'Package trot (5 mm lift)', STOCK), ('RT', 'Rough trot: spread stance + heading hold', STOCK),
       ('WALK', 'Walk, one leg at a time (12 mm lift)', STOCK), ('MECH', 'Wide track + ski paws + spread trot (8 mm)', MOD)]
cases = [('K1', 'rows', 'K1 laptop, along rows'), ('K1', 'diag', 'K1 laptop, diagonal'), ('K2', 'rows', 'K2 mechanical, along rows'), ('K2', 'diag', 'K2 mechanical, diagonal')]
data = {}
for tag, _, _ in cfg:
    _, rows = report.table(tag)
    for r in rows:
        k = (r['kind'], r['mode']); a = data.setdefault((tag,) + k, [0, 0]); a[0] += r['ok']; a[1] += r['n']
for i, (kind, mode, title) in enumerate(cases):
    a = fig.add_subplot(gs[1, i])
    ys = np.arange(len(cfg))[::-1]
    for y, (tag, lab, col) in zip(ys, cfg):
        ok, n = data[(tag, kind, mode)]
        a.barh(y, 100 * ok / n, height=0.62, color=col)
        a.text(min(100 * ok / n, 100) + 2 if ok / n < 0.8 else 100 * ok / n - 2, y, f'{ok}/{n}', va='center', ha='left' if ok / n < 0.8 else 'right',
               color=INK if ok / n < 0.8 else SURF, fontsize=8.5, fontweight='bold')
    a.set_xlim(0, 100); a.set_xticks([0, 50, 100]); a.set_xticklabels(['0', '50', '100%'])
    a.xaxis.grid(True, color=GRID, lw=0.8); a.set_axisbelow(True)
    a.set_yticks(ys); a.set_yticklabels([c[1] for c in cfg] if i == 0 else [], fontsize=8)
    for sp in ('top', 'right', 'left'): a.spines[sp].set_visible(False)
    a.set_title(title, fontsize=9, loc='left', color=INK)
fig.text(0.125, 0.425, 'Success = 25 cm without falling, a foot stuck > 3 s, or any paw stepping down onto the desk; 12 random starts x keycap friction 0.3 / 0.4 / 0.6 = 36 runs per cell.\n'
         'Blue = stock Tarçın, orange = modified legs (paws 25 mm further out, rounded "ski" soles). Diagonal runs use a key field three keyboards deep so 25 cm fits.',
         fontsize=8, color=INK2, linespacing=1.5)
fig.savefig(f'{OUT}/tarcin_keyboard_results.png', dpi=150, bbox_inches='tight')
print('ok')
