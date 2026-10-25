#!/usr/bin/env python3
"""Findik's eye frames for the two GC9A01 1.28" round IPS panels, drawn at NATIVE 240x240.

Drawn the way the ESP32-S3 firmware would draw them (LovyanGFX sprites): analytic shapes with 1-px
smooth edges (like fillSmoothCircle / fillEllipse with AA), a per-pixel radial iris gradient that the
firmware precomputes once into a PSRAM sprite, black lids drawn over it, then quantised to RGB565
(16-bit, 5-6-5) because that is what the panel receives over SPI.  Background pure black.

Files: faces/<expr>_L.png (robot's LEFT eye = +X = appears on the viewer's RIGHT) and <expr>_R.png.
In image space +x is the viewer's right, so the OUTER corner of eyeL is image-right, of eyeR image-left.
usage: python3 -I faces.py  -> ../faces/*.png and ../faces/_sheet.png
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "faces")
os.makedirs(OUT, exist_ok=True)
N = 240
SS = 3                                   # edge AA samples per axis (= 1-px smooth edges, not detail)
HAZEL_IN = np.array([232, 170, 78.])
HAZEL_MID = np.array([176, 112, 50.])
HAZEL_OUT = np.array([88, 50, 22.])
PUPIL = np.array([10, 7, 5.])
WARM = np.array([255, 208, 140.])
WHITE = np.array([255, 255, 255.])

_o = (np.arange(SS) + 0.5) / SS
yy, xx = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
X = (xx[..., None, None] + _o[None, None, None, :]).astype(np.float32)      # (N,N,1,SS)
Y = (yy[..., None, None] + _o[None, None, :, None]).astype(np.float32)      # (N,N,SS,1)


def cov(mask):
    """sub-sample coverage -> alpha (N,N)"""
    return np.broadcast_to(mask, (N, N, SS, SS)).mean(axis=(2, 3))


def comp(img, col, a):
    a = np.clip(a, 0, 1)[..., None]
    return img * (1 - a) + np.asarray(col, float) * a


def eye(side, gx=0.0, gy=0.0, rx=80, ry=90, squash=1.0, pupil=0.62, lid=0.0, lid_ang=0.0,
        low_lid=0.0, star=False, glints=True, halo=0.22, scale=1.0, dy=0.0, tear=False):
    """side=+1 robot-left eye (outer = image +x), -1 robot-right eye.
    lid: 0..1 upper lid closing; lid_ang deg, + = OUTER corner lower (sad), - = inner corner lower (determined)
    low_lid: 0..1 lower lid rising (smiling / squinting eyes)."""
    img = np.zeros((N, N, 3))
    cx = N / 2 + gx * 16
    cy = N / 2 + gy * 14 + dy
    rx, ry = rx * scale, ry * scale * squash
    # normalised ellipse coordinates (sub-sampled)
    ex, ey = (X - cx) / rx, (Y - cy) / ry
    rr = np.sqrt(ex ** 2 + ey ** 2)
    inside = rr <= 1.0
    # soft amber halo (firmware: 3 alpha-blended concentric ellipses, here a smooth falloff)
    rr_c = rr.mean(axis=(2, 3))
    out_px = np.clip(rr_c - 1.0, 0, None) * min(rx, ry)
    img = comp(img, [255, 160, 80], halo * np.exp(-(out_px / 7.0) ** 2) * (rr_c > 0.98))
    # iris: radial gradient + streaks, shaded darker on top (upper lid shadow)
    rc = rr.mean(axis=(2, 3))
    ang = np.arctan2(((Y - cy) / ry).mean(axis=(2, 3)), ((X - cx) / rx).mean(axis=(2, 3)))
    u = np.clip((rc - pupil) / (1 - pupil), 0, 1)
    c1 = HAZEL_IN + (HAZEL_MID - HAZEL_IN) * np.clip(u / 0.45, 0, 1)[..., None]
    c2 = HAZEL_MID + (HAZEL_OUT - HAZEL_MID) * (np.clip((u - 0.45) / 0.55, 0, 1) ** 0.8)[..., None]
    col = np.where((u < 0.45)[..., None], c1, c2)
    streak = 0.10 * np.sin(ang * 23 + 1.3) + 0.06 * np.sin(ang * 41 + 0.4)
    col = col * (1 + streak * (1 - u))[..., None]
    ey_c = ((Y - cy) / ry).mean(axis=(2, 3))
    col = col * (0.80 + 0.28 * (ey_c + 1) / 2)[..., None]
    a_iris = cov(inside)
    img = comp(img, np.clip(col, 0, 255), a_iris)
    img = comp(img, PUPIL, cov(rr <= pupil))
    if glints and squash > 0.45:
        hx, hy = cx - 0.40 * rx, cy - 0.44 * ry
        a, b = 0.29 * rx, 0.21 * ry
        img = comp(img, WHITE, 0.97 * cov(((X - hx) / a) ** 2 + ((Y - hy) / b) ** 2 <= 1))
        sx_, sy_ = cx + 0.36 * rx, cy + 0.36 * ry
        q = 0.10 * rx
        img = comp(img, WHITE, 0.92 * cov((X - sx_) ** 2 + (Y - sy_) ** 2 <= q * q))
        if star:
            tx, ty, L = cx + 0.55 * rx, cy - 0.52 * ry, 0.17 * ry
            d = np.abs(X - tx) ** 0.5 + np.abs(Y - ty) ** 0.5
            img = comp(img, WHITE, 0.95 * cov(d <= L ** 0.5))
    if tear:
        tx, ty = cx + side * 0.55 * rx, cy + 0.80 * ry
        img = comp(img, [150, 200, 255], 0.9 * cov(((X - tx) / 7) ** 2 + ((Y - ty) / 10) ** 2 <= 1))
        img = comp(img, WHITE, 0.9 * cov((X - tx + 2) ** 2 + (Y - ty + 3) ** 2 <= 4))
    # upper lid: black over everything above a tilted line (outer side = +side direction)
    if lid > 0:
        yl = cy - ry + 2 * ry * lid
        t = math.tan(math.radians(lid_ang)) * side
        img = comp(img, [0, 0, 0], cov(Y < yl + t * (X - cx)))
    if low_lid > 0:
        # lower lid as an upward-bulging curve (cheeks pushing up = smiling eyes)
        yb = cy + ry - 2 * ry * low_lid
        curve = yb + 0.35 * ry * ((X - cx) / rx) ** 2
        img = comp(img, [0, 0, 0], cov(Y > curve))
    return img


def happy(side, lift=0.0):
    img = np.zeros((N, N, 3))
    cx, cy = N / 2, N / 2 + 26 - lift
    rx, ry, th = 70.0, 64.0, 21.0
    ex, ey = (X - cx), (Y - cy)
    rr = np.sqrt((ex / rx) ** 2 + (ey / ry) ** 2)
    dist = (rr - 1) * (rx + ry) / 2
    ang = np.degrees(np.arctan2(ey, ex))
    band = (np.abs(dist) <= th / 2) & (ang >= -160) & (ang <= -20)
    caps = np.zeros_like(band)
    for a in (-160, -20):
        ar = math.radians(a)
        px, py = cx + rx * math.cos(ar), cy + ry * math.sin(ar)
        caps |= (X - px) ** 2 + (Y - py) ** 2 <= (th / 2) ** 2
    shape = band | caps
    a = cov(shape)
    # soft glow (blurred copy)
    from PIL import ImageFilter
    g = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    img = comp(img, [255, 160, 80], 0.45 * np.asarray(g) / 255.0)
    img = comp(img, WARM, a)
    # tiny sparkle above the arc, outer side
    tx, ty, L = cx + side * 58, cy - 82, 11.0
    d = np.abs(X - tx) ** 0.5 + np.abs(Y - ty) ** 0.5
    img = comp(img, [255, 240, 210], 0.9 * cov(d <= L ** 0.5))
    return img


def to_rgb565(img):
    a = np.clip(np.round(img), 0, 255).astype(np.uint16)
    r, g, b = a[..., 0] >> 3, a[..., 1] >> 2, a[..., 2] >> 3
    out = np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.uint8)
    return out


def round_mask(img):
    m = cov((X - N / 2) ** 2 + (Y - N / 2) ** 2 <= (N / 2) ** 2)
    return img * m[..., None]


# expression -> per-side kwargs  (L = +1, R = -1)
G_UP = dict(gx=0.0, gy=-0.30)
EXPR = {
    "neutral":    lambda s: eye(s, **G_UP),
    "blink":      lambda s: eye(s, gy=-0.1, squash=0.11, halo=0.18),
    "happy":      lambda s: happy(s),
    "talk_a":     lambda s: eye(s, gx=0.0, gy=-0.25, pupil=0.66, low_lid=0.16, dy=-2),
    "talk_b":     lambda s: eye(s, gx=0.0, gy=-0.25, pupil=0.62, squash=0.86, low_lid=0.22, dy=2),
    "surprised":  lambda s: eye(s, gy=-0.4, rx=86, ry=96, pupil=0.50, halo=0.3),
    "sleepy":     lambda s: eye(s, gy=0.2, lid=0.56, lid_ang=4, pupil=0.62, halo=0.12, glints=True),
    "sad":        lambda s: eye(s, gy=0.35, pupil=0.62, lid=0.30, lid_ang=17, tear=(s == 1)),
    "determined": lambda s: eye(s, gy=0.0, ry=84, pupil=0.56, lid=0.30, lid_ang=-20, low_lid=0.10),
    "curious":    lambda s: (eye(s, gx=0.5, gy=-0.4, pupil=0.66, ry=94, star=True) if s == 1
                             else eye(s, gx=0.5, gy=-0.4, pupil=0.58, lid=0.22, lid_ang=-10)),
}

if __name__ == "__main__":
    names = list(EXPR)
    sheet = Image.new("RGB", (len(names) * 500 + 20, 290), (24, 22, 20))
    for i, nm in enumerate(names):
        imgs = {}
        for side, tag in ((1, "L"), (-1, "R")):
            im = Image.fromarray(to_rgb565(round_mask(EXPR[nm](side))))
            im.save(os.path.join(OUT, f"{nm}_{tag}.png"))
            imgs[tag] = im
        # sheet as seen from the front: robot's right eye (R) on the viewer's left
        sheet.paste(imgs["R"], (10 + i * 500, 10))
        sheet.paste(imgs["L"], (10 + i * 500 + 250, 10))
        ImageDraw.Draw(sheet).text((10 + i * 500 + 210, 262), nm, fill=(230, 220, 200))
    sheet.save(os.path.join(os.path.dirname(HERE), "stills", "faces_sheet.png"))
    print("faces:", names)
