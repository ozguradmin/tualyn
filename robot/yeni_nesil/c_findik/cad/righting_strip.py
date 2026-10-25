#!/usr/bin/env python3
"""3-frame self-righting strip from the verified quasi-static states (righting.json); rotations map the
rest direction (pitch, roll) to world-down (Euler XYZ, deg):
side rest (pitch 8, roll 84, stand legs) -> lower-side legs swung f80/r120, rolled to (14, 38) -> standing."""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont
R = "/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/render/render.js"
frames = [("r1", "stl", "sad", (-0.8, 84.1)), ("r2", "stl_tuck", "neutral", (-11.0, 38.9)), ("r3", "stl", "happy_noblush", (0, 0))]
os.makedirs("wip/strip", exist_ok=True)
for name, d, emo, (rx, ry) in frames:
    e = "happy" if emo.startswith("happy") else emo
    subprocess.run(["python3", "scene.py", d, e, "scene_strip.json", f"{name}:0:24:0.92", "640", "560"], check=True, capture_output=True)
    sc = json.load(open("scene_strip.json"))
    for p in sc["parts"]:
        p["rotation"] = [rx, ry, 0]
    json.dump(sc, open("scene_strip.json", "w"))
    subprocess.run(["node", R, "scene_strip.json", "wip/strip"], check=True, capture_output=True)
W, H = 640 * 3, 560 + 90
img = Image.new("RGB", (W, H), (237, 232, 225))
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
caps = ["1  falls on its side: rests at roll 84 deg",
        "2  lower-side legs swing (front 80, rear 120):\n    the egg rolls itself to 38 deg",
        "3  legs sweep down: stands up (0, 0)"]
for i, (name, *_ ) in enumerate(frames):
    img.paste(Image.open(f"wip/strip/{name}.png"), (i * 640, 0))
    ImageDraw.Draw(img).multiline_text((i * 640 + 24, 560 + 10), caps[i], fill=(50, 42, 36), font=f, spacing=4)
img.save("final/righting_strip.png")
print("wrote final/righting_strip.png")
