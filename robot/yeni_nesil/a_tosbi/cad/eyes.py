#!/usr/bin/env python3
"""Procedural eye frames for Tosbi.

Hardware: one round GC9A01 (240x240, active dia 33.4 mm) behind an oval glossy-black visor
(52.6 x 36.6 mm). The PNG covers the visor bounding box; everything outside the round active
area stays black (that is the black-painted mask around the screen), so the screen edge is invisible.
Firmware draws the same parametric shapes (eye w/h, corner radius, lid angles, offsets) into a
240x240 sprite at 30-60 fps; screen240_*.png are the exact 240x240 frames the panel would show.
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
VA, VB = 26.3, 18.3            # visor semi-axes (mm)
S = 1500                       # texture width (px)
SH = int(round(S * VB / VA))   # texture height (px)
MM = S / (2 * VA)              # px per mm
R_ACT = 33.4 / 2 * MM          # active screen radius (px)
C, CY = S / 2, SH / 2
GLOW = (124, 244, 255)         # #7CF4FF
CORE = (222, 253, 255)
BLUSH = (255, 120, 140)

def new(mode="L", col=0):
    return Image.new(mode, (S, SH), col)

def rr(draw, cx, cy, w, h, r, fill):
    draw.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=fill)

def finish(mask_core, highlight=None, blush=0):
    img = new("RGB", (0, 0, 0))
    glow = new("RGB", GLOW)
    img = Image.composite(glow, img, mask_core.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.5)))
    img = Image.composite(glow, img, mask_core.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.8)))
    grad = new("RGB")
    gd = ImageDraw.Draw(grad)
    for y in range(SH):
        t = min(1.0, max(0.0, (y - CY + R_ACT) / (2 * R_ACT)))
        gd.line([(0, y), (S, y)], fill=tuple(int(CORE[k] * (1 - t) + GLOW[k] * t) for k in range(3)))
    img = Image.composite(grad, img, mask_core.filter(ImageFilter.GaussianBlur(1.3)))
    if blush:
        bl = new()
        bd = ImageDraw.Draw(bl)
        for sx in (-1, 1):
            cx, cy = C + sx * 9.6 * MM, CY + 7.6 * MM
            bd.ellipse([cx - 3.0 * MM, cy - 1.5 * MM, cx + 3.0 * MM, cy + 1.5 * MM], fill=blush)
        img = Image.composite(new("RGB", BLUSH), img, bl.filter(ImageFilter.GaussianBlur(16)))
    if highlight is not None:
        img = Image.composite(new("RGB", (255, 255, 255)), img, highlight.filter(ImageFilter.GaussianBlur(1.6)))
    clip = new()
    ImageDraw.Draw(clip).ellipse([C - R_ACT, CY - R_ACT, C + R_ACT, CY + R_ACT], fill=255)
    return Image.composite(img, new("RGB", (0, 0, 0)), clip.filter(ImageFilter.GaussianBlur(2)))

def neutral(look=0.0):
    m, hi = new(), new()
    d, hd = ImageDraw.Draw(m), ImageDraw.Draw(hi)
    w, h, gap, dy = 9.8 * MM, 13.8 * MM, 4.8 * MM, 1.3 * MM      # eye line ~45 % of the face height
    for sx in (-1, 1):
        cx = C + sx * (gap / 2 + w / 2) + look * MM
        rr(d, cx, CY + dy, w, h, w * 0.48, 255)
        x0, y0 = cx - w * 0.30, CY + dy - h * 0.36
        hd.ellipse([x0, y0, x0 + 2.3 * MM, y0 + 2.3 * MM], fill=240)
        x1, y1 = cx + w * 0.10, CY + dy - h * 0.10
        hd.ellipse([x1, y1, x1 + 1.0 * MM, y1 + 1.0 * MM], fill=190)
    return finish(m, hi, blush=110)

def happy():
    m = new(); d = ImageDraw.Draw(m)
    w, gap, dy, th = 9.8 * MM, 4.4 * MM, 1.8 * MM, 3.0 * MM
    for sx in (-1, 1):
        cx = C + sx * (gap / 2 + w / 2)
        bb = [cx - w / 2, CY + dy - w * 0.42, cx + w / 2, CY + dy + w * 0.58]
        d.arc(bb, start=200, end=340, fill=255, width=int(th))
        for ang in (200, 340):
            a = math.radians(ang)
            rx, ry = (bb[2] - bb[0]) / 2 - th / 2, (bb[3] - bb[1]) / 2 - th / 2
            px, py = (bb[0] + bb[2]) / 2 + rx * math.cos(a), (bb[1] + bb[3]) / 2 + ry * math.sin(a)
            d.ellipse([px - th / 2, py - th / 2, px + th / 2, py + th / 2], fill=255)
    return finish(m, None, blush=170)

def wow():
    m, hi = new(), new()
    d, hd = ImageDraw.Draw(m), ImageDraw.Draw(hi)
    r, gap, dy = 5.4 * MM, 4.0 * MM, 0.6 * MM
    for sx in (-1, 1):
        cx = C + sx * (gap / 2 + r)
        d.ellipse([cx - r, CY + dy - r * 1.1, cx + r, CY + dy + r * 1.1], fill=255)
        x0, y0 = cx - r * 0.58, CY + dy - r * 0.8
        hd.ellipse([x0, y0, x0 + 2.6 * MM, y0 + 2.6 * MM], fill=245)
    return finish(m, hi, blush=0)

def determined():
    """'Ters döndüm ama sorun yok' - flat-topped eyes (upper lids lowered), used after a flip."""
    m = new(); d = ImageDraw.Draw(m)
    w, h, gap, dy = 10.2 * MM, 9.0 * MM, 4.4 * MM, 2.6 * MM
    for sx in (-1, 1):
        cx = C + sx * (gap / 2 + w / 2)
        rr(d, cx, CY + dy, w, h, w * 0.45, 255)
        x_in, x_out = cx - sx * w / 2, cx + sx * w / 2
        top = CY + dy - h / 2
        d.polygon([(x_in, top - 2), (x_out, top - 2), (x_out, top + 0.10 * h), (x_in, top + 0.42 * h)], fill=0)
    return finish(m, None, blush=0)

if __name__ == "__main__":
    frames = (("neutral", neutral), ("happy", happy), ("wow", wow), ("determined", determined))
    for name, fn in frames:
        im = fn()
        im.save(os.path.join(HERE, f"eyes_{name}.png"))
        a = R_ACT
        im.crop((int(C - a), int(CY - a), int(C + a), int(CY + a))).resize((240, 240), Image.LANCZOS) \
          .save(os.path.join(HERE, f"screen240_{name}.png"))
    tw, th = 480, int(480 * SH / S)
    sheet = Image.new("RGB", (len(frames) * (tw + 20) + 20, th + 40), (233, 228, 220))
    for i, (name, _) in enumerate(frames):
        sheet.paste(Image.open(os.path.join(HERE, f"eyes_{name}.png")).resize((tw, th), Image.LANCZOS), (20 + i * (tw + 20), 20))
    sheet.save(os.path.join(HERE, "eyes_sheet.png"))
    print("ok", S, SH)
