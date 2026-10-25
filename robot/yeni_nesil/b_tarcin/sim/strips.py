#!/usr/bin/env python3
"""Playback check: render each anim through posecheck (rig.js, exactly as the viewer) from a FIXED camera at several
t values and compose stills/anim_<clip>.png strips. usage: strips.py clip [clip...]"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixcam as F
PKG = F.PKG
RENDER = '/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/render'
TMP = os.path.join(HERE, 'out', 'strip_frames')
W, H = 1000, 750


def cams(clip, a):
    n = a['frames']; dur = (n - 1) / 30
    bs = np.array(a['base']) if a.get('base') else np.zeros((1, 7))
    c = bs[:, :3].mean(0) if a.get('base') else np.zeros(3)
    span = np.ptp(bs[:, :2], axis=0).max() if a.get('base') else 0
    views = []
    if clip == 'walk':
        ts = list(np.linspace(0, dur, 8))
        views.append(('side', 90, 6, [c[0], c[1], 60], max(520, 2.6 * (span + 160)), ts))
        views.append(('front', -25, 18, [c[0], c[1], 70], max(520, 2.6 * (span + 160)), ts))
    elif clip == 'turn':
        ts = list(np.linspace(0, dur, 8))
        views.append(('top', 20, 55, [c[0], c[1], 50], 620, ts))
    elif clip == 'fall_recover':
        ts = list(np.linspace(0, dur, 12))
        views.append(('front', 0, 12, [c[0], c[1], 60], 640, ts))
        views.append(('side', 90, 12, [c[0], c[1], 60], 640, ts))
    elif clip == 'fall_recover_back':
        ts = list(np.linspace(0, dur, 18))
        views.append(('front', 20, 14, [c[0], c[1], 60], 660, ts))
    else:
        ts = list(np.linspace(0, dur, 8))
        views.append(('hero', 30, 14, [c[0], c[1], 72], 560, ts))
        if clip in ('talk', 'happy', 'sleep', 'idle'):
            views.append(('face', 0, 8, [c[0], c[1] - 50, 105], 300, ts))
    return views


def face_at(a, t):
    i = int(math.floor(min(t * 30, a['frames'] - 1))) if not a.get('loop') else int(math.floor((t * 30) % (a['frames'] - 1)))
    e = None
    for fi, ex in a.get('face', []):
        if fi <= i: e = ex
        else: break
    return e


def main(clips):
    os.makedirs(TMP, exist_ok=True)
    shots, plan = [], []
    for clip in clips:
        a = json.load(open(os.path.join(PKG, 'anim', clip + '.json')))
        for vname, az, el, tgt, D, ts in cams(clip, a):
            row = []
            for k, t in enumerate(ts):
                j, b = F.frame(a, t)
                d, lo, hi = F.dist_param(D, j, b)
                nm = f'{clip}_{vname}_{k:02d}'
                shots.append(dict(name=nm, anim=clip, t=float(t), azimuth=az, elevation=el, target=[float(x) for x in tgt], distance=float(d)))
                row.append((nm, t, float(lo[2]), face_at(a, t)))
            plan.append((clip, vname, row))
    cfg = os.path.join(TMP, 'shots.json')
    json.dump(dict(width=W, height=H, shots=shots), open(cfg, 'w'))
    r = subprocess.run(['node', os.path.join(RENDER, 'posecheck.js'), PKG, cfg, TMP], capture_output=True, text=True)
    print(r.stdout.splitlines()[0][:400] if r.stdout else '', r.stderr[-2000:])
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
    except Exception: font = ImageFont.load_default()
    for clip in clips:
        rows = [(v, row) for c, v, row in plan if c == clip]
        cols = max(len(r) for _, r in rows)
        tw, th = W // 2, H // 2
        ncol = min(cols, 6) if cols > 8 else (4 if cols == 8 else cols)
        nrow_per = math.ceil(cols / ncol)
        sheet = Image.new('RGB', (ncol * tw, nrow_per * len(rows) * th), 'white')
        dr = ImageDraw.Draw(sheet)
        for ri, (v, row) in enumerate(rows):
            for k, (nm, t, zlo, fc) in enumerate(row):
                f = os.path.join(TMP, nm + '.png')
                if not os.path.exists(f): continue
                im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
                x = (k % ncol) * tw; y = (ri * nrow_per + k // ncol) * th
                sheet.paste(im, (x, y))
                dr.text((x + 10, y + 8), f'{v} t={t:.2f}s' + (f' [{fc}]' if fc else ''), fill=(20, 20, 20), font=font)
        out = os.path.join(PKG, 'stills', f'anim_{clip}.png')
        sheet.save(out); print('wrote', out, sheet.size)


if __name__ == '__main__':
    main(sys.argv[1:])
