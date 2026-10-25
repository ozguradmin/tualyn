#!/usr/bin/env python3
"""Tarcin eye frames at the GC9A01's NATIVE resolution (240x240, round), drawn the way the ESP32 firmware
draws them (TFT_eSPI smooth/anti-aliased primitives into a 16-bit sprite):
  * flat shapes with anti-aliased edges (4x supersampling = TFT_eSPI 'smooth' AA), no photographic blur
  * a 2-step outline 'glow' (two larger dim copies of the same shape) instead of a Gaussian halo
  * simple vertical 2-colour gradient, a 2-dot sparkle
  * colours quantised to RGB565, pure black background, round panel (outside the circle = black)
L = robot's left eye = +x side (nose toward image left), R = -x side (nose toward image right).
Writes ../faces/<expr>_L.png and _R.png.
"""
import math, os
from PIL import Image, ImageDraw, ImageChops

N = 240
SS = 4
S = N * SS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faces")
os.makedirs(OUT, exist_ok=True)

CYAN = (0, 200, 255)
CORE = (120, 236, 255)
PINK = (255, 120, 160)
PINK_CORE = (255, 214, 228)
SAD = (110, 200, 255)


def rr(d, cx, cy, w, h, r, fill=255):
    r = min(r, w / 2, h / 2)
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=fill)


def new():
    return Image.new("L", (S, S), 0)


def lid(m, cx, y_inner, y_outer, nose_dir, w, below=False):
    """cut away everything above (or below) a straight lid line running from the inner (nose) corner
    to the outer corner"""
    d = ImageDraw.Draw(m)
    xi, xo = cx + nose_dir * w * 0.62, cx - nose_dir * w * 0.62
    # extend line far out
    k = (y_outer - y_inner) / (xo - xi)
    xa, xb = -S, 2 * S
    ya, yb = y_inner + k * (xa - xi), y_inner + k * (xb - xi)
    if not below:
        d.polygon([(xa, ya), (xb, yb), (xb, -S), (xa, -S)], fill=0)
    else:
        d.polygon([(xa, ya), (xb, yb), (xb, 2 * S), (xa, 2 * S)], fill=0)
    return m


def pill(cx, cy, w, h, r=None):
    m = new()
    rr(ImageDraw.Draw(m), cx, cy, w, h, r if r is not None else min(w, h) * 0.47)
    return m


def arc_eye(cx, cy, w, h, thick, up=True):
    """happy '^' arc (up=True) or closed sleeping arc (up=False), with round caps"""
    m = new()
    d = ImageDraw.Draw(m)
    if up:
        box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2 + h * 0.6]
        a0, a1 = 200, 340
    else:
        box = [cx - w / 2, cy - h * 1.1, cx + w / 2, cy + h * 0.5]
        a0, a1 = 25, 155
    d.arc(box, start=a0, end=a1, fill=255, width=int(thick))
    bx0, by0, bx1, by1 = box
    rx, ry = (bx1 - bx0) / 2 - thick / 2, (by1 - by0) / 2 - thick / 2
    ccx, ccy = (bx0 + bx1) / 2, (by0 + by1) / 2
    for ang in (a0, a1):
        a = math.radians(ang)
        px, py = ccx + rx * math.cos(a), ccy + ry * math.sin(a)
        d.ellipse([px - thick / 2, py - thick / 2, px + thick / 2, py + thick / 2], fill=255)
    return m


def heart(cx, cy, s):
    m = new()
    d = ImageDraw.Draw(m)
    r = 0.52 * s
    d.ellipse([cx - 2 * r + 0.12 * s, cy - 0.55 * s - r, cx + 0.12 * s, cy - 0.55 * s + r], fill=255)
    d.ellipse([cx - 0.12 * s, cy - 0.55 * s - r, cx + 2 * r - 0.12 * s, cy - 0.55 * s + r], fill=255)
    d.polygon([(cx - 2 * r + 0.16 * s, cy - 0.38 * s), (cx + 2 * r - 0.16 * s, cy - 0.38 * s), (cx, cy + 0.95 * s)], fill=255)
    return m


def grow(mask, px):
    """outline copy grown by px (firmware: same primitive drawn larger)"""
    from PIL import ImageFilter
    k = int(px) * 2 + 1
    return mask.filter(ImageFilter.MaxFilter(k if k % 2 else k + 1))


def compose(mask, color=CYAN, core=CORE, sparkle=None, dim=1.0, glow=True):
    img = Image.new("RGB", (S, S), (0, 0, 0))
    if glow:
        # two dim outline steps (drawn as larger copies) - what the firmware can afford at 60 fps
        g2 = grow(mask, 7 * SS)
        g1 = grow(mask, 3 * SS)
        img.paste(tuple(int(c * 0.16 * dim) for c in color), (0, 0), g2)
        img.paste(tuple(int(c * 0.38 * dim) for c in color), (0, 0), g1)
    # 2-colour vertical gradient (core colour at the top -> eye colour at the bottom)
    bb = mask.getbbox()
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    y0, y1 = (bb[1], bb[3]) if bb else (0, S)
    for y in range(S):
        t = min(1.0, max(0.0, (y - y0) / max(1, (y1 - y0))))
        t = t * 0.85
        c = tuple(int((core[i] * (1 - t) + color[i] * t) * dim) for i in range(3))
        gd.line([(0, y), (S, y)], fill=c)
    img.paste(grad, (0, 0), mask)
    if sparkle:
        sx, sy, sr = sparkle
        sp = new()
        sd = ImageDraw.Draw(sp)
        sd.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=255)
        r2 = sr * 0.42
        sd.ellipse([sx + sr * 1.15 - r2, sy + sr * 1.45 - r2, sx + sr * 1.15 + r2, sy + sr * 1.45 + r2], fill=255)
        sp = ImageChops.multiply(sp, mask)
        img.paste((255, 255, 255), (0, 0), sp)
    return img


def finish(img):
    """downsample (AA), quantise to RGB565, mask to the round panel"""
    small = img.resize((N, N), Image.BOX)
    px = small.load()
    for y in range(N):
        for x in range(N):
            r, g, b = px[x, y]
            r = (r >> 3) << 3; g = (g >> 2) << 2; b = (b >> 3) << 3
            r |= r >> 5; g |= g >> 6; b |= b >> 5
            px[x, y] = (r, g, b)
    circ = Image.new("L", (N, N), 0)
    ImageDraw.Draw(circ).ellipse([0, 0, N - 1, N - 1], fill=255)
    out = Image.new("RGB", (N, N), (0, 0, 0))
    out.paste(small, (0, 0), circ)
    return out


def eye(expr, side):
    """side +1 = L (+x, nose toward image left), -1 = R"""
    nose = -side                       # image x direction of the nose
    u = SS
    cx = S / 2 + nose * 20 * u         # pill drawn offset toward the nose (concept: visual gap ~ 1 eye width)
    cy = S / 2 + 4 * u
    W, H = 116 * u, 150 * u
    spark = (cx - 26 * u, cy - 44 * u, 12 * u)   # light from the upper left on both eyes
    if expr == "neutral":
        return compose(pill(cx, cy, W, H), sparkle=spark)
    if expr == "blink":
        m = arc_eye(cx, cy + 22 * u, W * 0.95, 34 * u, 16 * u, up=False)
        return compose(m, glow=True)
    if expr == "happy":
        return compose(arc_eye(cx, cy - 4 * u, 128 * u, 100 * u, 34 * u, up=True))
    if expr == "talk_a":               # speaking pulse: a touch taller and lifted
        return compose(pill(cx, cy - 4 * u, W * 1.03, H * 1.05), sparkle=(spark[0], spark[1] - 6 * u, spark[2]))
    if expr == "talk_b":               # ... then squashed, lower lid pushing up
        m = pill(cx, cy + 6 * u, W * 1.06, H * 0.84)
        lid(m, cx, cy + 50 * u, cy + 44 * u, nose, W, below=True)
        return compose(m, sparkle=(spark[0], spark[1] + 10 * u, spark[2]))
    if expr == "surprised":
        m = pill(cx, cy - 6 * u, 136 * u, 166 * u, r=66 * u)
        return compose(m, sparkle=(cx - 32 * u, cy - 52 * u, 14 * u))
    if expr == "sleepy":
        m = pill(cx, cy + 10 * u, W, H * 0.9)
        lid(m, cx, cy + 4 * u, cy + 14 * u, nose, W)
        return compose(m, dim=0.7, glow=False)
    if expr == "sleep":
        m = arc_eye(cx, cy + 30 * u, W * 0.9, 30 * u, 12 * u, up=False)
        return compose(m, dim=0.45, glow=False)
    if expr == "sad":
        m = pill(cx, cy + 10 * u, W * 0.96, H * 0.92)
        lid(m, cx, cy - 46 * u, cy - 6 * u, nose, W)         # inner corner high, outer corner low
        return compose(m, color=SAD, core=(200, 236, 255), sparkle=(cx - 22 * u, cy - 4 * u, 9 * u), dim=0.9)
    if expr == "determined":
        m = pill(cx, cy + 6 * u, W * 1.02, H * 0.9)
        lid(m, cx, cy - 10 * u, cy - 50 * u, nose, W)        # inner corner low = focused / 'let's go'
        lid(m, cx, cy + 60 * u, cy + 60 * u, nose, W, below=True)
        return compose(m, sparkle=(cx - 18 * u, cy - 14 * u, 9 * u))
    if expr == "curious":
        if side > 0:
            return compose(pill(cx, cy - 6 * u, 126 * u, 160 * u), sparkle=(cx - 28 * u, cy - 50 * u, 13 * u))
        m = pill(cx, cy + 6 * u, 108 * u, 132 * u)
        lid(m, cx, cy - 34 * u, cy - 26 * u, nose, 108 * u)
        return compose(m, sparkle=(cx - 22 * u, cy - 22 * u, 10 * u))
    if expr == "love":
        return compose(heart(cx, cy - 6 * u, 64 * u), color=PINK, core=PINK_CORE, sparkle=(cx - 30 * u, cy - 50 * u, 8 * u))
    raise ValueError(expr)


EXPRS = ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "sleep", "sad", "determined", "curious", "love"]

if __name__ == "__main__":
    cols = 4
    rows = (len(EXPRS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 500 + 20, rows * 250 + 10), (30, 30, 30))
    for i, e in enumerate(EXPRS):
        for j, (side, tag) in enumerate(((-1, "R"), (1, "L"))):     # sheet: robot's right eye on the left, as seen from the front
            im = finish(eye(e, side))
            im.save(os.path.join(OUT, f"{e}_{tag}.png"))
            sheet.paste(im, ((i % cols) * 500 + j * 244 + 10, (i // cols) * 250 + 5))
    sheet.save(os.path.join(OUT, "..", "build", "faces_sheet.png"))
    print("ok", len(EXPRS))
