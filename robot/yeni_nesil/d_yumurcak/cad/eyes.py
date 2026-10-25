#!/usr/bin/env python3
"""Procedural eye frames for Yumurcak's two round GC9A01 eyes (240x240, active ~32.4 mm).

Each eye is drawn as the firmware would draw it: parametric pill + lids on pure black,
soft glow, small catch-light. Images are 512 px (supersampled render of the 240 px panel)
and are mapped planar onto the round screen parts.
  side 'L' = screen at model -X (viewer's left in the front view); its nose side is +u.
Output: tex/eye_<state>_<side>.png  and tex/eyes_sheet.png (preview).
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 512            # output px
SS = 3             # supersample
MM = S / 32.4      # px per mm on the panel
CORE = (196, 252, 255)
GLOW = (64, 214, 255)
OUT = "tex"
os.makedirs(OUT, exist_ok=True)


def canvas():
    return Image.new("L", (S * SS, S * SS), 0)


def pill(d, cx, cy, w, h, r):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=255)


def compose(mask, sparkle=None, tint=CORE):
    m = mask.resize((S, S), Image.LANCZOS)
    glow = m.filter(ImageFilter.GaussianBlur(14))
    glow2 = m.filter(ImageFilter.GaussianBlur(4))
    img = Image.new("RGB", (S, S), (0, 0, 0))
    g = Image.new("RGB", (S, S), GLOW)
    img = Image.composite(g, img, glow.point(lambda v: int(v * 0.55)))
    img = Image.composite(Image.new("RGB", (S, S), (120, 236, 255)), img, glow2.point(lambda v: int(v * 0.8)))
    # inner gradient: brighter top
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for yy in range(S):
        t = yy / S
        c = tuple(int(tint[i] * (1.0 - 0.18 * t) + 255 * 0.0) for i in range(3))
        gd.line([(0, yy), (S, yy)], fill=c)
    img = Image.composite(grad, img, m)
    if sparkle:
        sp = Image.new("L", (S, S), 0)
        sd = ImageDraw.Draw(sp)
        for (x, y, r) in sparkle:
            sd.ellipse([x - r, y - r, x + r, y + r], fill=255)
        sp = sp.filter(ImageFilter.GaussianBlur(1.2))
        img = Image.composite(Image.new("RGB", (S, S), (255, 255, 255)), img, ImageChops.multiply(sp, m))
    # round panel edge: outside active area stays black
    edge = Image.new("L", (S, S), 0)
    ImageDraw.Draw(edge).ellipse([2, 2, S - 3, S - 3], fill=255)
    return Image.composite(img, Image.new("RGB", (S, S), (0, 0, 0)), edge)


def eye(state, side):
    sgn = 1 if side == "L" else -1          # +1: nose is +u (right) on the L screen
    c = canvas()
    d = ImageDraw.Draw(c)
    k = SS * MM
    cx = S * SS / 2 + sgn * 3.2 * k
    cy = S * SS / 2 + 0.6 * k
    w, h = 16.0 * k, 21.0 * k
    spark = None
    if state == "neutral":
        pill(d, cx, cy, w, h, 7.6 * k)
        spark = [((cx - sgn * 3.6 * k) / SS, (cy - 5.6 * k) / SS, 2.3 * MM), ((cx - sgn * 1.2 * k) / SS, (cy - 2.4 * k) / SS, 1.0 * MM)]
    elif state == "happy":
        # ^ ^ : thick upward arc with round caps (Cozmo-style happy squint), slightly raised
        r, wd = 8.4 * k, 4.6 * k
        cy2 = cy + 3.0 * k
        bb = [cx - r, cy2 - r, cx + r, cy2 + r]
        a0, a1 = 198, 342
        d.arc(bb, a0, a1, fill=255, width=int(wd))
        for aa in (a0, a1):
            rr = r - wd / 2
            ex, ey = cx + rr * math.cos(math.radians(aa)), cy2 + rr * math.sin(math.radians(aa))
            d.ellipse([ex - wd / 2, ey - wd / 2, ex + wd / 2, ey + wd / 2], fill=255)
        # small blush dots under the eye (cheeks)
        spark = None
    elif state == "curious":
        # nose-side eye bigger + lifted inner brow lid on the other
        big = 1.12 if side == "R" else 0.92
        pill(d, cx, cy - (1.2 * k if side == "R" else -0.6 * k), w * big, h * big, 7.6 * k * big)
        if side == "L":
            d.polygon([(cx - w, cy - h * 0.62), (cx + w, cy - h * 0.62), (cx + w, cy - h * 0.28), (cx - w, cy - h * 0.44)], fill=0)
        spark = [((cx - sgn * 3.6 * k) / SS, (cy - 6.0 * k) / SS, 2.3 * MM)]
    elif state == "sleepy":
        # closed: gentle downward smile line (resting egg)
        bb = [cx - 8.0 * k, cy - 6.0 * k, cx + 8.0 * k, cy + 4.0 * k]
        d.arc(bb, 20, 160, fill=255, width=int(2.4 * k))
    return compose(c, sparkle=spark)


if __name__ == "__main__":
    states = ["neutral", "happy", "curious", "sleepy"]
    sheet = Image.new("RGB", (S * 2 * len(states) // 2 + 40, S + 20), (20, 20, 22))
    sheet = Image.new("RGB", (len(states) * (2 * S // 2 + 20), S // 2 + 20), (24, 24, 26))
    for i, st in enumerate(states):
        for j, sd in enumerate(("L", "R")):
            im = eye(st, sd)
            im.save(os.path.join(OUT, f"eye_{st}_{sd}.png"))
            sheet.paste(im.resize((S // 2, S // 2)), (i * (S + 20) + j * (S // 2), 10))
    sheet.save(os.path.join(OUT, "eyes_sheet.png"))
    print("ok")
