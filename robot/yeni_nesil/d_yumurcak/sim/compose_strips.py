#!/usr/bin/env python3
"""Tile the fixed-camera posecheck renders into ../stills/anim_<clip>.png (label: t, frame, face, base z, tilt)."""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
W = sys.argv[1]
CAM = json.load(open(os.path.join(W, "strip_cams.json")))
V = json.load(open(os.path.join(HERE, "out", "verify_anims.json")))
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except OSError:
    F = FB = ImageFont.load_default()
TW, TH, COLS = 600, 450, 4
for clip, (az, el, tgt, dist, ts) in CAM.items():
    a = json.load(open(os.path.join(PKG, "anim", clip + ".json")))
    n = len(ts); rows = math.ceil(n / COLS)
    img = Image.new("RGB", (TW * min(n, COLS), TH * rows + 50), "#ffffff")
    d = ImageDraw.Draw(img)
    d.text((12, 10), f"{clip}  ({a['frames']} frames @30 fps, fixed camera az {az} el {el}, {dist} m)   {a['source'][:120]}", fill="#111", font=F)
    for i, t in enumerate(ts):
        im = Image.open(os.path.join(W, "raw", f"{clip}_{int(round(t * 1000)):05d}.png")).convert("RGB").resize((TW, TH), Image.LANCZOS)
        x, y = (i % COLS) * TW, 50 + (i // COLS) * TH
        img.paste(im, (x, y))
        fi = min(a["frames"] - 1, int(t * 30))
        face = None
        for k, e in a["face"]:
            if k <= fi: face = e
        zm = V[clip]["zmin"][fi]
        q = a["base"][fi][3:]
        tilt = math.degrees(math.acos(max(-1, min(1, 1 - 2 * (q[1] ** 2 + q[2] ** 2)))))
        d.rectangle([x, y, x + TW - 1, y + TH - 1], outline="#bbb")
        d.text((x + 10, y + 8), f"t={t:.2f}s  f{fi}  {face}", fill="#000", font=FB)
        d.text((x + 10, y + TH - 32), f"min z {zm:+.2f} mm   tilt {tilt:.0f}°", fill="#333", font=F)
    f = os.path.join(PKG, "stills", f"anim_{clip}.png")
    img.save(f, optimize=True)
    print("wrote", f, img.size)
