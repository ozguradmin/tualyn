#!/usr/bin/env python3
"""Compose posecheck frames (strips/<clip>_NN.png) into ../stills/anim_<clip>.png with t / frame / face labels."""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
times = json.load(open(os.path.join(HERE, "strip_times.json")))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    fbig = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except Exception:
    font = fbig = ImageFont.load_default()
ALIAS = {"walk_follow": "walk"}
for clip, ts in times.items():
    a = json.load(open(os.path.join(PKG, "anim", ALIAS.get(clip, clip) + ".json")))
    tiles = []
    for i, t in enumerate(ts):
        p = os.path.join(HERE, "strips", f"{clip}_{i:02d}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        fr = min(int(t * 30), a["frames"] - 1)
        face = None
        for fi, ex in a["face"]:
            if fi <= fr:
                face = ex
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 34], fill=(20, 20, 22))
        d.text((10, 6), f"t={t:.2f}s  f{fr}  face: {face}", fill=(240, 240, 240), font=font)
        tiles.append(im)
    if not tiles:
        continue
    cols = min(5, len(tiles)) if len(tiles) != 6 else 3
    if len(tiles) in (8, 12):
        cols = 4
    rows = (len(tiles) + cols - 1) // cols
    W, H = tiles[0].size
    sc = 0.6
    w, h = int(W * sc), int(H * sc)
    sheet = Image.new("RGB", (cols * w, rows * h + 40), (30, 30, 32))
    dd = ImageDraw.Draw(sheet)
    title = f"{clip}  ({a['frames']} frames @30 fps, {a['source'][:150]})"
    if clip == "walk_follow":
        title = f"walk_follow  ({a['frames']} frames @30 fps; base wrapped back every 30 cm = pure ground shift, so the grid stays under the robot)"
    dd.text((10, 8), title, fill=(255, 255, 255), font=fbig)
    for k, im in enumerate(tiles):
        sheet.paste(im.resize((w, h), Image.LANCZOS), ((k % cols) * w, 40 + (k // cols) * h))
    out = os.path.join(PKG, "stills", f"anim_{clip}.png")
    sheet.save(out)
    print("wrote", out, sheet.size)
