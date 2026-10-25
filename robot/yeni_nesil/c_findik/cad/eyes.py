#!/usr/bin/env python3
"""Procedural eye frames for Findik's two round GC9A01 screens (240x240 each), drawn with PIL.

Style: "findik gozlu" (hazel-eyed). A big hazel iris with a large pupil and two sparkle highlights,
on a pure-black background so the round screen disappears into the glossy black socket.
Each frame is drawn from parameters (gaze, lid, squash), the same way the firmware will draw it
with TFT_eSPI/LVGL sprites, so blink/squash/emotion are tweens of these numbers, not bitmaps.

Writes  tex/eye_<emotion>_<l|r>.png  (rendered at 4x then downsampled = what an anti-aliased
240x240 sprite looks like) and tex/eyes_sheet.png (all emotions, both eyes).
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "tex"
os.makedirs(OUT, exist_ok=True)
N = 240          # panel resolution
S = 4            # supersampling
W = N * S

HAZEL_IN = (232, 170, 78)     # golden ring around the pupil
HAZEL_MID = (176, 112, 50)
HAZEL_OUT = (92, 52, 24)      # dark limbal ring
PUPIL = (12, 8, 6)
WARM = (255, 214, 150)        # glow colour for happy arcs


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def iris_layer(cx, cy, r, pupil_frac, gaze_tilt=0.0):
    """RGBA layer with the iris disc (radial gradient + streaks), pupil and limbal ring."""
    lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    px = lay.load()
    rp = r * pupil_frac
    x0, x1 = int(cx - r - 2), int(cx + r + 2)
    y0, y1 = int(cy - r - 2), int(cy + r + 2)
    for y in range(max(0, y0), min(W, y1)):
        for x in range(max(0, x0), min(W, x1)):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            t = d / r
            if d < rp:
                c = PUPIL
            else:
                u = (d - rp) / (r - rp)
                if u < 0.45:
                    c = lerp(HAZEL_IN, HAZEL_MID, u / 0.45)
                else:
                    c = lerp(HAZEL_MID, HAZEL_OUT, min(1, (u - 0.45) / 0.55) ** 0.8)
                a = math.atan2(dy, dx)
                streak = 0.10 * math.sin(a * 23 + 1.3) + 0.06 * math.sin(a * 41 + 0.4)
                c = tuple(max(0, min(255, int(v * (1 + streak * (1 - u))))) for v in c)
                # soft shading: darker at the top (upper lid shadow), warmer at the bottom
                sh = 0.78 + 0.30 * ((dy / r + 1) / 2)
                c = tuple(max(0, min(255, int(v * sh))) for v in c)
            # anti-aliased edge
            alpha = 255 if d < r - 1.5 * S else int(255 * max(0, (r - d) / (1.5 * S)))
            px[x, y] = c + (alpha,)
    return lay


def sparkle(draw, cx, cy, r, scale=1.0, star=False):
    # big soft highlight upper-left + small one lower-right
    hx, hy = cx - 0.36 * r, cy - 0.40 * r
    a, b = 0.24 * r * scale, 0.20 * r * scale
    draw.ellipse([hx - a, hy - b, hx + a, hy + b], fill=(255, 255, 255, 245))
    sx, sy = cx + 0.30 * r, cy + 0.34 * r
    q = 0.085 * r * scale
    draw.ellipse([sx - q, sy - q, sx + q, sy + q], fill=(255, 255, 255, 230))
    if star:
        tx, ty = cx + 0.42 * r, cy - 0.30 * r
        L = 0.15 * r
        draw.polygon([(tx, ty - L), (tx + L * 0.22, ty - L * 0.22), (tx + L, ty), (tx + L * 0.22, ty + L * 0.22),
                      (tx, ty + L), (tx - L * 0.22, ty + L * 0.22), (tx - L, ty), (tx - L * 0.22, ty - L * 0.22)],
                     fill=(255, 255, 255, 235))


def eye_open(gx=0.0, gy=0.0, squash=1.0, pupil=0.64, lid_top=0.0, lid_angle=0.0, side=1, star=False, ox=0.0,
             rx=0.345, ry=0.385):
    """Kawaii oval eye floating on black.  gx, gy in [-1,1] gaze; side=+1 robot-left eye (image right is
    outward), -1 right eye; ox = static outward offset (fraction of panel) so the two drawn eyes sit
    ~0.85 eye-widths apart although the panels are close; lid_top 0..1 closes from the top;
    lid_angle (deg) tilts the lid edge (+ = outer corner lower -> sad)."""
    img = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    R = ry * W
    cx = W / 2 + (side * ox + gx * 0.06) * W
    cy = W / 2 + gy * 0.06 * W
    iris = iris_layer(cx, cy, R, pupil)
    # squash to an oval (rx/ry) and optional blink squash, about the eye centre
    sxf, syf = rx / ry, squash
    big = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    bw, bh = max(1, int(W * sxf)), max(1, int(W * syf))
    iris = iris.resize((bw, bh), Image.LANCZOS)
    big.paste(iris, (int(cx - cx * sxf), int(cy - cy * syf)))
    # soft amber halo so the eye reads as lit on the black visor
    halo = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([cx - rx * W - 3 * S, cy - R * syf - 3 * S, cx + rx * W + 3 * S, cy + R * syf + 3 * S],
                                 fill=(255, 170, 90, 70))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(5 * S)))
    img.alpha_composite(big)
    d = ImageDraw.Draw(img)
    if squash > 0.5:
        r_eff = R
        hx, hy = cx - 0.42 * rx * W, cy - 0.45 * R
        a, b = 0.30 * rx * W, 0.22 * R
        d.ellipse([hx - a, hy - b, hx + a, hy + b], fill=(255, 255, 255, 250))
        sx_, sy_ = cx + 0.38 * rx * W, cy + 0.36 * R
        q = 0.10 * rx * W
        d.ellipse([sx_ - q, sy_ - q, sx_ + q, sy_ + q], fill=(255, 255, 255, 235))
        if star:
            tx, ty = cx + 0.55 * rx * W, cy - 0.50 * R
            L = 0.16 * R
            d.polygon([(tx, ty - L), (tx + L * 0.22, ty - L * 0.22), (tx + L, ty), (tx + L * 0.22, ty + L * 0.22),
                       (tx, ty + L), (tx - L * 0.22, ty + L * 0.22), (tx - L, ty), (tx - L * 0.22, ty - L * 0.22)],
                      fill=(255, 255, 255, 240))
    if lid_top > 0:
        lid = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lid)
        yl = cy - R + 2 * R * lid_top
        t = math.tan(math.radians(lid_angle)) * side      # outer side = +side direction
        ld.polygon([(0, 0), (W, 0), (W, yl + t * W / 2), (0, yl - t * W / 2)], fill=(0, 0, 0, 255))
        img.alpha_composite(lid)
    return img


def eye_happy(side=1, lift=0.0):
    """Closed happy eye: thick glowing upside-down U ('^') arc."""
    img = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = W / 2, W / 2 + 0.09 * W - lift * W
    rx, ry = 0.30 * W, 0.27 * W
    th = int(0.095 * W)
    box = [cx - rx, cy - ry, cx + rx, cy + ry]
    g.arc(box, 200, 340, fill=WARM + (255,), width=th)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(5 * S)))
    img.alpha_composite(glow)
    # rounded caps
    d = ImageDraw.Draw(img)
    for a in (200, 340):
        ar = math.radians(a)
        ex = cx + (rx - th / 2) * math.cos(ar)
        ey = cy + (ry - th / 2) * math.sin(ar)
        d.ellipse([ex - th / 2, ey - th / 2, ex + th / 2, ey + th / 2], fill=WARM + (255,))
    # tiny sparkle above the arc
    sx, sy = cx + 0.30 * W * side, cy - 0.33 * W
    L = 0.045 * W
    d.polygon([(sx, sy - L), (sx + L * 0.25, sy - L * 0.25), (sx + L, sy), (sx + L * 0.25, sy + L * 0.25),
               (sx, sy + L), (sx - L * 0.25, sy + L * 0.25), (sx - L, sy), (sx - L * 0.25, sy - L * 0.25)],
              fill=(255, 240, 210, 220))
    return img


def circle_mask(img):
    m = Image.new("L", (W, W), 0)
    ImageDraw.Draw(m).ellipse([0, 0, W - 1, W - 1], fill=255)
    bg = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    return Image.composite(img, bg, m)


def save(img, name, size=N * 2):
    img = circle_mask(img).convert("RGB").resize((size, size), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    return img


EMO = {
    # name: (left-eye image fn, right-eye image fn)   left/right = robot's own left/right
    "neutral": (lambda: eye_open(gx=-0.25, gy=-0.35, side=1), lambda: eye_open(gx=0.25, gy=-0.35, side=-1)),
    "happy": (lambda: eye_happy(1), lambda: eye_happy(-1)),
    "curious": (lambda: eye_open(gx=0.5, gy=-0.4, pupil=0.66, side=1, star=True, ry=0.40, rx=0.345),
                lambda: eye_open(gx=0.5, gy=-0.4, pupil=0.56, lid_top=0.22, lid_angle=-10, side=-1)),
    "sleepy": (lambda: eye_open(gy=0.15, lid_top=0.52, lid_angle=0, side=1),
               lambda: eye_open(gy=0.15, lid_top=0.52, lid_angle=0, side=-1)),
    "sad": (lambda: eye_open(gy=0.25, pupil=0.6, lid_top=0.30, lid_angle=16, side=1),
            lambda: eye_open(gy=0.25, pupil=0.6, lid_top=0.30, lid_angle=16, side=-1)),
    "blink": (lambda: eye_open(gy=-0.1, squash=0.14, side=1), lambda: eye_open(gy=-0.1, squash=0.14, side=-1)),
}

if __name__ == "__main__":
    sheet = Image.new("RGB", (len(EMO) * 2 * 250 + 20, 290), (24, 22, 20))
    for i, (name, (fl, fr)) in enumerate(EMO.items()):
        # files: _l = robot's left eye (appears on the viewer's right)
        il = save(fl(), f"eye_{name}_l.png")
        ir = save(fr(), f"eye_{name}_r.png")
        sheet.paste(ir.resize((240, 240)), (10 + i * 500, 10))
        sheet.paste(il.resize((240, 240)), (10 + i * 500 + 250, 10))
        ImageDraw.Draw(sheet).text((10 + i * 500 + 200, 262), name, fill=(230, 220, 200))
    sheet.save(os.path.join(OUT, "eyes_sheet.png"))
    print("ok")
