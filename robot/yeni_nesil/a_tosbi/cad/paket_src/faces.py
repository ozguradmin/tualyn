#!/usr/bin/env python3
"""Tosbi face frames at the GC9A01's native 240x240.

How the real firmware draws them: LVGL 9 / TFT_eSPI sprite, anti-aliased primitives (rounded rects,
arcs, ellipses), a vertical gradient fill, a soft "shadow" glow (lv_obj shadow, ~8 px, 30 % opa),
then pushed to the panel as RGB565. To match that we draw at 4x, downsample (= AA edge quality of
LVGL), add the small glow, and quantise to RGB565 (5-6-5 bits), so gradient banding is real.
Pure black background; the panel is round, so anything outside r = 120 px is never seen.

Geometry is taken from concept_A/eyes.py (mm on the visor) converted with 240 px / 32.4 mm = 7.41 px/mm.
usage: python3 -I faces.py <package_dir>
"""
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

PKG = sys.argv[1]
OUT = os.path.join(PKG, "faces"); os.makedirs(OUT, exist_ok=True)
N, SS = 240, 4
S = N * SS
PX = 240 / 32.4 * SS          # supersampled px per mm
C = S / 2
GLOW = (124, 244, 255)        # #7CF4FF
CORE = (222, 253, 255)
BLUSH = (255, 110, 135)

def mm(v): return v * PX

def L():
    im = Image.new("L", (S, S), 0); return im, ImageDraw.Draw(im)

def rr(d, cx, cy, w, h, r, fill=255):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=fill)

def compose(mask, hi=None, blush=0, extra=None, extra_col=GLOW):
    """mask: L image (SS scale) of the eye shapes. Returns 240x240 RGB565-quantised frame."""
    img = Image.new("RGB", (S, S), (0, 0, 0))
    # soft glow (LVGL shadow): drawn at native scale like the firmware would
    glow = mask.resize((N, N), Image.LANCZOS).filter(ImageFilter.GaussianBlur(4.0)).point(lambda v: int(v * 0.42))
    img = Image.composite(Image.new("RGB", (S, S), GLOW), img, glow.resize((S, S), Image.BILINEAR))
    # vertical gradient fill (LVGL lv_grad, 2 stops), top = white-cyan core, bottom = cyan
    grad = Image.new("RGB", (1, S))
    top, bot = C - mm(9), C + mm(9)
    for y in range(S):
        t = min(1.0, max(0.0, (y - top) / (bot - top)))
        grad.putpixel((0, y), tuple(int(CORE[k] * (1 - t) + GLOW[k] * t) for k in range(3)))
    grad = grad.resize((S, S))
    img = Image.composite(grad, img, mask)
    if extra is not None:
        img = Image.composite(Image.new("RGB", (S, S), extra_col), img, extra)
    if blush:
        bl, bd = L()
        for sx in (-1, 1):
            cx, cy = C + sx * mm(9.6), C + mm(7.6)
            bd.ellipse([cx - mm(3.0), cy - mm(1.4), cx + mm(3.0), cy + mm(1.4)], fill=blush)
        bl = bl.filter(ImageFilter.GaussianBlur(SS * 3))
        bl = ImageChops.subtract(bl, mask)            # blush is behind the eye
        img = Image.composite(Image.new("RGB", (S, S), BLUSH), img, bl)
    if hi is not None:
        img = Image.composite(Image.new("RGB", (S, S), (255, 255, 255)), img, hi)
    img = img.resize((N, N), Image.BOX)                 # AA, native resolution
    # round panel: outside the circle is never lit
    cm = Image.new("L", (N, N), 0); ImageDraw.Draw(cm).ellipse([0, 0, N - 1, N - 1], fill=255)
    img = Image.composite(img, Image.new("RGB", (N, N)), cm)
    # RGB565 quantisation
    px = img.load()
    for y in range(N):
        for x in range(N):
            r, g, b = px[x, y]
            r5, g6, b5 = r >> 3, g >> 2, b >> 3
            px[x, y] = ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))
    return img

EW, EH, GAP, DY = mm(9.8), mm(13.8), mm(4.8), mm(1.3)
def centers(w=EW, gap=GAP):
    return [C + sx * (gap / 2 + w / 2) for sx in (-1, 1)]

def highlights(d, cx, cy, w, h):
    x0, y0 = cx - w * 0.30, cy - h * 0.36
    d.ellipse([x0, y0, x0 + mm(2.3), y0 + mm(2.3)], fill=240)
    x1, y1 = cx + w * 0.10, cy - h * 0.10
    d.ellipse([x1, y1, x1 + mm(1.0), y1 + mm(1.0)], fill=190)

def neutral(h=EH, look=0.0, mouth=None):
    m, d = L(); hi, hd = L()
    for cx in centers():
        cx += mm(look)
        rr(d, cx, C + DY, EW, h, EW * 0.48)
        highlights(hd, cx, C + DY, EW, h)
    ex = None
    if mouth:
        ex, ed = L()
        mw, mh = mouth
        my = C + mm(10.6)
        rr(ed, C, my, mm(mw), mm(mh), min(mm(mw), mm(mh)) * 0.5)
        if mh > 1.5:   # open mouth: darker inside, light rim (reads as an open mouth on a 240 px panel)
            rr(ed, C, my + mm(0.25), mm(mw) - mm(1.3), mm(mh) - mm(1.3), (min(mw, mh) - 1.3) * PX * 0.5, fill=0)
    hi = hi.filter(ImageFilter.GaussianBlur(SS * 0.4))
    return compose(m, hi, blush=110, extra=ex, extra_col=(255, 140, 150))

def blink():
    m, d = L()
    for cx in centers():
        rr(d, cx, C + DY + mm(3.2), EW + mm(0.6), mm(1.7), mm(0.85))
    return compose(m, None, blush=110)

def happy():
    m, d = L()
    w, gap, dy, th = EW, mm(4.4), mm(1.8), mm(3.0)
    for cx in centers(w, gap):
        bb = [cx - w / 2, C + dy - w * 0.42, cx + w / 2, C + dy + w * 0.58]
        d.arc(bb, start=200, end=340, fill=255, width=int(th))
        for ang in (200, 340):
            a = math.radians(ang)
            rx, ry = (bb[2] - bb[0]) / 2 - th / 2, (bb[3] - bb[1]) / 2 - th / 2
            px_, py_ = (bb[0] + bb[2]) / 2 + rx * math.cos(a), (bb[1] + bb[3]) / 2 + ry * math.sin(a)
            d.ellipse([px_ - th / 2, py_ - th / 2, px_ + th / 2, py_ + th / 2], fill=255)
    return compose(m, None, blush=170)

def surprised():
    m, d = L(); hi, hd = L()
    r, gap, dy = mm(5.4), mm(4.0), mm(0.6)
    for sx in (-1, 1):
        cx = C + sx * (gap / 2 + r)
        d.ellipse([cx - r, C + dy - r * 1.1, cx + r, C + dy + r * 1.1], fill=255)
        x0, y0 = cx - r * 0.58, C + dy - r * 0.8
        hd.ellipse([x0, y0, x0 + mm(2.6), y0 + mm(2.6)], fill=245)
    ex, ed = L()
    ed.ellipse([C - mm(1.6), C + mm(9.6), C + mm(1.6), C + mm(12.6)], fill=255)
    ed.ellipse([C - mm(0.9), C + mm(10.3), C + mm(0.9), C + mm(11.9)], fill=0)
    return compose(m, hi.filter(ImageFilter.GaussianBlur(SS * 0.4)), blush=0, extra=ex, extra_col=(255, 140, 150))

def lidded(inner, outer, h=EH, dy=DY, w=EW, blush=0, hl=False):
    """Eyes with a straight upper lid: inner/outer = fraction of eye height cut at the inner/outer corner."""
    m, d = L(); hi, hd = L()
    for sx, cx in zip((-1, 1), centers(w)):
        rr(d, cx, C + dy, w, h, w * 0.48)
        top = C + dy - h / 2
        x_in, x_out = cx - sx * w / 2, cx + sx * w / 2
        d.polygon([(x_in - sx * 4, top - 8), (x_out + sx * 4, top - 8), (x_out + sx * 4, top + outer * h),
                   (x_in - sx * 4, top + inner * h)], fill=0)
        if hl:
            hd.ellipse([cx - w * 0.25, top + max(inner, outer) * h + mm(1.2), cx - w * 0.25 + mm(1.8), top + max(inner, outer) * h + mm(3.0)], fill=200)
    return compose(m, hi.filter(ImageFilter.GaussianBlur(SS * 0.4)), blush=blush)

FACES = {
    "neutral": lambda: neutral(),
    "blink": blink,
    "happy": happy,
    "talk_a": lambda: neutral(h=EH * 0.94, mouth=(4.2, 3.0)),
    "talk_b": lambda: neutral(h=EH, mouth=(3.4, 1.0)),
    "surprised": surprised,
    "sleepy": lambda: lidded(0.55, 0.62, h=EH * 0.95, dy=DY + mm(1.0), blush=90),
    "sad": lambda: lidded(0.12, 0.42, h=EH * 0.9, dy=DY + mm(1.4), hl=True),
    "determined": lambda: lidded(0.42, 0.10, h=mm(9.0), dy=mm(2.6), w=mm(10.2)),
}

if __name__ == "__main__":
    tiles = []
    for name, fn in FACES.items():
        im = fn(); im.save(os.path.join(OUT, f"{name}.png")); tiles.append((name, im))
        # upside-down state: the firmware rotates the whole frame 180 deg (GC9A01 MADCTL) when the IMU sees gravity flip
        im.rotate(180).save(os.path.join(OUT, f"{name}_inv.png"))
    sh = Image.new("RGB", (len(tiles) * 250 + 10, 260), (40, 40, 44))
    for i, (n, im) in enumerate(tiles):
        sh.paste(im, (10 + i * 250, 10))
    sh.save(os.path.join(PKG, "src", "faces_sheet.png"))
    print("faces:", [n for n, _ in tiles])
