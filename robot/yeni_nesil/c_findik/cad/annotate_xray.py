#!/usr/bin/env python3
"""Add labelled callouts to the x-ray render.  Re-implements the renderer's camera (render/page.html):
model (x,y,z) mm -> world (x, z, -y) * 0.01; target = bbox centre; dist = d * radius / sin(fov/2) * 1.05.
usage: python3 annotate_xray.py scene_xray.json final/xray.png stl/info.json final/xray_annotated.png"""
import json, math, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

scene_p, img_p, info_p, out_p = sys.argv[1:5]
scene = json.load(open(scene_p))
info = json.load(open(info_p))
base = os.path.dirname(os.path.abspath(scene_p))
GZ = info["ground_offset_GZ"]


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return arr["v"].reshape(-1, 3).astype(float)

pts = np.vstack([read_stl(os.path.join(base, p["file"])) for p in scene["parts"]])
world = np.stack([pts[:, 0], pts[:, 2], -pts[:, 1]], 1) * 0.01
lo, hi = world.min(0), world.max(0)
center = (lo + hi) / 2
radius = np.linalg.norm(hi - lo) / 2
W, H = scene["width"], scene["height"]
v = scene["views"][0]
fov = math.radians(v.get("fov", 28))
az, el = math.radians(v["azimuth"]), math.radians(v["elevation"])
dist = v["distance"] * radius / math.sin(fov / 2) * 1.05
cam = center + dist * np.array([math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az)])
fwd = center - cam; fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
up = np.cross(right, fwd)


def proj(p_body):
    x, y, z = p_body
    z = z + GZ
    w = np.array([x, z, -y]) * 0.01 - cam
    xc, yc, zc = w @ right, w @ up, w @ fwd
    f = 1 / math.tan(fov / 2)
    ndc_x = f * xc / zc / (W / H)
    ndc_y = f * yc / zc
    return ((ndc_x + 1) / 2 * W, (1 - ndc_y) / 2 * H)

S = info["legs_deg"]["rl"]
ax_r = (13.0, 21.5 + 34 * math.sin(math.radians(S)), 32 - 34 * math.cos(math.radians(S)))
labels = [  # (text, anchor in body frame mm, side)
    ("2 x GC9A01 1.28in round IPS eyes", (21.5, -31.0, 50.0), "L"),
    ("ESP32-S3 N16R8 devkit (Wi-Fi -> Claude)", (-20.0, 10.0, 63.5), "L"),
    ("deck: bucks, DRV8833, IMU, amp", (-18.0, -4.0, 57.5), "L"),
    ("cliff IR x2 (TCRT5000) in the chin", (12.0, -21.0, 18.0), "L"),
    ("2S 14500 pack, lowest point", (-10.0, 3.5, 18.6), "L"),
    ("INMP441 mic under the cap", (0.0, 0.0, 88.0), "R"),
    ("32 mm speaker, back grille", (0.0, 37.0, 66.0), "R"),
    ("4 x MG90S hip servos (1 per leg)", (14.0, 21.5, 40.0), "R"),
    ("2 x N20 6V 100rpm in the rear paws", ax_r, "R"),
    ("free-rolling front paws (M3 axle)", (37.8, -15.5 - 34 * math.sin(math.radians(S)), 32 - 34 * math.cos(math.radians(S))), "R"),
]
img = Image.open(img_p).convert("RGB")
d = ImageDraw.Draw(img)
fp = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(fp, 21)
tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
d.text((40, 30), "Findik - x-ray: everything fits (0 mm3 interference in the CAD check)", fill=(60, 52, 44), font=tfont)
labels = [(t, a, "L" if proj(a)[0] < W / 2 else "R") for t, a, _ in labels]
left = [l for l in labels if l[2] == "L"]
rightl = [l for l in labels if l[2] == "R"]
for group, xtext in ((left, 40), (rightl, W - 40)):
    group = sorted(group, key=lambda l: proj(l[1])[1])
    n = len(group)
    for i, (t, a, side) in enumerate(group):
        px, py = proj(a)
        ty = 130 + i * (H - 220) / max(1, n - 1) if n > 1 else py - 12
        tw = d.textlength(t, font=font)
        tx = xtext if side == "L" else xtext - tw
        ex = tx + tw + 10 if side == "L" else tx - 10
        d.line([(ex, ty + 12), (px, py)], fill=(70, 60, 50), width=2)
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(214, 120, 40), outline=(255, 255, 255), width=2)
        d.text((tx, ty), t, fill=(40, 34, 30), font=font)
img.save(out_p)
print("wrote", out_p)
