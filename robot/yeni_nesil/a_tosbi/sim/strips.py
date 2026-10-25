#!/usr/bin/env python3
"""Render every clip through posecheck.js (= rig.js, exactly what the viewer shows) at several t from a FIXED camera
(target fixed in world mm; a few marked 'follow' tiles are close-ups for the face / leg lift) and compose
stills/anim_<clip>.png contact sheets. Usage: python3 -I strips.py <scratch_dir>"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
SCR = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "frames")); os.makedirs(SCR, exist_ok=True)
POSECHECK = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(PKG))), "render", "posecheck.js")
A = {k: json.load(open(os.path.join(PKG, "anim", k + ".json"))) for k in ("idle", "walk", "turn", "talk", "happy", "sleep", "fall_recover")}

def mid(clip):
    B = np.array(A[clip]["base"])[:, :3]; return [float(v) for v in (B.min(0) + B.max(0)) / 2]

def face_at(clip, t):
    a = A[clip]; n = a["frames"]; x = t * 30
    x = x % (n - 1) if a["loop"] else min(x, n - 1); i = int(x); e = None
    for fi, ex in a["face"]:
        if fi <= i: e = ex
    return e

PLAN = {
 "idle": dict(cam=dict(azimuth=-35, elevation=12, distance=0.8, target=[0, -15, 35]), ts=[0, 0.6, 1.25, 2.5, 3.55, 4.4]),
 "talk": dict(cam=dict(azimuth=-20, elevation=10, distance=0.55, target=[0, -70, 45]), ts=[0.05, 0.25, 1.0, 2.7, 3.3, 4.2]),
 "happy": dict(cam=dict(azimuth=-30, elevation=12, distance=0.85, target=[0, -15, 35]), ts=[0.2, 0.7, 1.0, 1.25, 1.45, 2.0, 3.0, 3.5]),
 "sleep": dict(cam=dict(azimuth=-55, elevation=10, distance=0.85, target=[0, -15, 30]), ts=[0, 0.5, 1.2, 1.4, 2.2, 3.9]),
 "turn": dict(cam=dict(azimuth=0, elevation=50, distance=0.95, target=[0, 0, 35]), ts=[0, 1, 2, 3, 4, 5]),
 "walk": dict(cam=dict(azimuth=-70, elevation=18, distance=1.5, target=None), ts=[0, 1.4, 2.8, 4.2, 5.6, 7.0],
              follow=dict(cam=dict(azimuth=-60, elevation=8, distance=0.8), ts=[3.0, 3.35])),
 "fall_recover": dict(cam=dict(azimuth=-25, elevation=28, distance=1.45, target=None),
                      ts=[0.5, 1.4, 1.9, 2.1, 2.4, 2.8, 3.05, 3.3, 3.6, 4.5, 5.5, 6.6],
                      follow=dict(cam=dict(azimuth=-10, elevation=15, distance=0.6), ts=[2.2, 3.1, 3.5])),
}

ONLY = [a for a in sys.argv[2:] if not a.startswith("--")]
if ONLY: PLAN = {k: v for k, v in PLAN.items() if k in ONLY}
shots, tiles = [], {}
for clip, p in PLAN.items():
    cam = dict(p["cam"])
    if cam.get("target") is None:
        m = mid(clip); cam["target"] = [m[0], m[1], 40.0]
    tiles[clip] = []
    for t in p["ts"]:
        nm = f"{clip}_{t:.2f}"; shots.append({"name": nm, "anim": clip, "t": t, **cam}); tiles[clip].append((nm, t, "fixed cam"))
    if "follow" in p:
        for t in p["follow"]["ts"]:
            nm = f"{clip}_f{t:.2f}"; shots.append({"name": nm, "anim": clip, "t": t, **p["follow"]["cam"]}); tiles[clip].append((nm, t, "close-up"))
cfg = os.path.join(SCR, "anim_shots.json")
json.dump({"width": 1400, "height": 1050, "shots": shots}, open(cfg, "w"), indent=0)
if "--compose-only" not in sys.argv:
    subprocess.run(["node", POSECHECK, PKG, cfg, SCR], check=True)

try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
except Exception: font = ImageFont.load_default()
for clip, tl in tiles.items():
    cols = 4 if len(tl) in (8, 12, 15, 16) else 3
    if len(tl) == 15: cols = 5
    rows = -(-len(tl) // cols); W, H = 560, 420
    sheet = Image.new("RGB", (cols * W, rows * H + 40), "#f4f1ec"); d = ImageDraw.Draw(sheet)
    d.text((12, 8), f"{clip}  –  MuJoCo clip played through rig.js (posecheck); fixed camera unless marked close-up", fill="#222", font=font)
    for k, (nm, t, kind) in enumerate(tl):
        im = Image.open(os.path.join(SCR, nm + ".png")).convert("RGB").resize((W, H), Image.LANCZOS)
        x, y = (k % cols) * W, 40 + (k // cols) * H
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + W - 1, y + 30], fill="#ffffffcc")
        ev = [e for f_, e in A[clip].get("events", []) if f_ <= t * 30]
        d.text((x + 8, y + 4), f"t={t:.2f}s  face={face_at(clip, t)}  {kind}", fill="#111", font=font)
        if ev:
            d.rectangle([x, y + H - 32, x + W - 1, y + H - 1], fill="#ffffffcc")
            d.text((x + 8, y + H - 29), ev[-1][:48], fill="#7a2e12", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17) if hasattr(font, "path") else font)
    out = os.path.join(PKG, "stills", f"anim_{clip}.png"); sheet.save(out, optimize=True); print("wrote", out)
