#!/usr/bin/env python3
"""Compose the 3-frame self-righting storyboard (wip/seq1..3.png -> final/self_righting.png)."""
from PIL import Image, ImageDraw, ImageFont
fr = [Image.open(f'wip/seq{i}.png') for i in (1, 2, 3)]
w, h = fr[0].size
top, bot = 150, 40
W = Image.new('RGB', (w * 3, h + top + bot), (236, 232, 225))
for i, f in enumerate(fr):
    W.paste(f, (i * w, top))
d = ImageDraw.Draw(W)
T = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 34)
F = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 24)
S = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 19)
INK, G, ACC = (38, 40, 46), (95, 97, 104), (226, 120, 10)
d.text((40, 28), "Self-righting in three moves", font=T, fill=INK)
d.text((40, 76), "Quasi-static convex-hull model (righting.py): 7 of 7 fall directions recover; "
       "worst knee load 0.066 N·m = 33 % of MG90S stall", font=S, fill=G)
caps = [("1  Falls over", "rests on one haunch ball + the egg's flank (85° tilt)"),
        ("2  Down-side knees sweep the paws head-ward", "paw tips lift the flank: 85° → 57° while the knees hold 0.066 N·m"),
        ("3  Tips past the haunch and drops on its feet", "then stands, shakes off, happy eyes")]
for i, (a, b) in enumerate(caps):
    x = i * w + 30
    d.ellipse([x, h + top - 70, x + 12, h + top - 58], fill=ACC)
    d.text((x + 22, h + top - 82), a, font=F, fill=INK)
    d.text((x + 22, h + top - 50), b, font=S, fill=G)
for i in (1, 2):
    d.line([(i * w, top + 30), (i * w, h + top - 100)], fill=(214, 209, 200), width=2)
W.save('final/self_righting.png')
print(W.size)
