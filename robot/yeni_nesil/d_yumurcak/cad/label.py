#!/usr/bin/env python3
"""Callout labels on a render: replicates render/page.html camera math to project model points.
usage: label.py scene.json view_name in.png out.png labels.json
labels.json: [{"text": "...", "p": [x,y,z] (model mm, world/ground frame), "side": "L"|"R", "dy": px}]"""
import json, math, os, sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

scene_p, view_name, inp, outp, lab_p = sys.argv[1:6]
sc = json.load(open(scene_p))
base = os.path.dirname(os.path.abspath(scene_p))
W, H = sc["width"], sc["height"]
pts = []
for p in sc["parts"]:
    m = trimesh.load(os.path.join(base, p["file"]))
    v = m.bounds  # 2x3 model mm
    pts.append(v)
pts = np.vstack(pts)
def to_world(q):
    q = np.asarray(q, float)
    return np.array([q[0], q[2], -q[1]]) * 0.01
corners = np.array([[x, y, z] for x in pts[:, 0][[pts[:, 0].argmin(), pts[:, 0].argmax()]]
                    for y in pts[:, 1][[pts[:, 1].argmin(), pts[:, 1].argmax()]]
                    for z in pts[:, 2][[pts[:, 2].argmin(), pts[:, 2].argmax()]]])
wc = np.array([to_world(c) for c in corners])
bmin, bmax = wc.min(0), wc.max(0)
center = (bmin + bmax) / 2
radius = np.linalg.norm(bmax - bmin) / 2
v = [vv for vv in sc["views"] if vv["name"] == view_name][0]
fov = math.radians(v.get("fov", 28))
az, el = math.radians(v.get("azimuth", 35)), math.radians(v.get("elevation", 18))
dist = v.get("distance", 1.0) * radius / math.sin(fov / 2) * 1.05
tgt = center
cam = tgt + dist * np.array([math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az)])
fwd = (tgt - cam) / np.linalg.norm(tgt - cam)
right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
up = np.cross(right, fwd)
f = 1 / math.tan(fov / 2)
def proj(q):
    w = to_world(q) - cam
    x, y, z = w @ right, w @ up, w @ fwd
    return (W / 2 + (x / z) * f * H / 2, H / 2 - (y / z) * f * H / 2)

img = Image.open(inp).convert("RGB")
d = ImageDraw.Draw(img)
S = W / 1400
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", int(22 * S))
small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", int(17 * S))
title = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", int(30 * S))
labs = json.load(open(lab_p))
INK = (38, 40, 46)
ACC = (226, 120, 10)
used = {"L": [], "R": []}
for L in labs:
    px, py = proj(L["p"])
    side = L.get("side") or ("L" if px < W / 2 else "R")
    tx = int(60 * S) if side == "L" else int(W - 60 * S)
    ty = int(L["ty"] * S) if "ty" in L else int(py + L.get("dy", 0) * S)
    lines = L["text"].split("\n")
    tw = max(d.textlength(t, font=font if i == 0 else small) for i, t in enumerate(lines))
    ex = tx + tw + 14 * S if side == "L" else tx - tw - 14 * S
    d.line([(px, py), (ex, ty)], fill=INK, width=max(1, int(2 * S)))
    r = 5 * S
    d.ellipse([px - r, py - r, px + r, py + r], fill=ACC, outline=(255, 255, 255), width=max(1, int(2 * S)))
    for i, t in enumerate(lines):
        fnt = font if i == 0 else small
        w_ = d.textlength(t, font=fnt)
        x0 = tx if side == "L" else tx - w_
        d.text((x0, ty - 14 * S + i * 25 * S), t, font=fnt, fill=INK if i == 0 else (90, 92, 98))
if len(sys.argv) > 6:
    d.text((int(60 * S), int(40 * S)), sys.argv[6], font=title, fill=INK)
if len(sys.argv) > 7:
    d.text((int(60 * S), int(82 * S)), sys.argv[7], font=small, fill=(90, 92, 98))
img.save(outp)
print("ok", outp)
