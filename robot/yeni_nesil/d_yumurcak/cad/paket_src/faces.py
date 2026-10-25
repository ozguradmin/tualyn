#!/usr/bin/env python3
"""Eye frames for Yumurcak's two GC9A01 round IPS panels, at NATIVE resolution 240 x 240.

Drawn the way the ESP32 firmware would draw them (LVGL / TFT_eSPI sprite style): flat cyan-white
parametric pill per eye on pure black, a 2-step pre-rendered glow halo, 1-2 white catch-lights,
and black "lid" polygons for moods. Anti-aliasing = 4x supersampling of the 240 px frame
(LVGL draws anti-aliased shapes the same way), never a hi-res picture scaled down.

Same parameters as concept_D2/eyes.py: pill 16 x 21 mm, shifted 3.2 mm toward the nose.
Screen u axis = +X world (viewer's right, seen from the front). eyeL = robot's LEFT eye (+X),
so its nose side is -u; eyeR (at -X) has its nose at +u.
usage: python3 -I faces.py   -> ../faces/<expr>_<L|R>.png, faces_sheet.png
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "faces")
os.makedirs(OUT, exist_ok=True)
N = 240                    # native panel resolution
SS = 4                     # anti-alias supersampling of the 240 px frame
MM = N / 32.4              # px per mm on the 32.4 mm active circle
CORE_TOP, CORE_BOT = (172, 242, 255), (112, 212, 236)
GLOW = (40, 190, 255)


class Eye:
    def __init__(self):
        self.m = Image.new("L", (N * SS, N * SS), 0)
        self.d = ImageDraw.Draw(self.m)
        self.spark = []

    def k(self, mm):
        return mm * MM * SS

    def pill(self, cx, cy, w, h, r=None):
        k = self.k
        r = min(w, h) / 2 * 0.95 if r is None else r
        self.d.rounded_rectangle([k(cx - w / 2), k(cy - h / 2), k(cx + w / 2), k(cy + h / 2)], radius=k(r), fill=255)

    def lid(self, pts):            # black polygon (mm coords) cut from the eye
        self.d.polygon([(self.k(x), self.k(y)) for x, y in pts], fill=0)

    def arc(self, cx, cy, r, a0, a1, width):
        k = self.k
        self.d.arc([k(cx - r), k(cy - r), k(cx + r), k(cy + r)], a0, a1, fill=255, width=int(k(width)))
        rr = r - width / 2
        for a in (a0, a1):
            ex, ey = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
            self.d.ellipse([k(ex - width / 2), k(ey - width / 2), k(ex + width / 2), k(ey + width / 2)], fill=255)

    def render(self):
        m = self.m.resize((N, N), Image.BOX)                      # 4x4 box filter = AA coverage
        glow = m.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.55))
        halo = m.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.75))
        img = Image.new("RGB", (N, N), (0, 0, 0))
        img = Image.composite(Image.new("RGB", (N, N), GLOW), img, glow)
        img = Image.composite(Image.new("RGB", (N, N), (110, 230, 255)), img, halo)
        grad = Image.new("RGB", (N, N))
        gd = ImageDraw.Draw(grad)
        for y in range(N):
            t = y / (N - 1)
            gd.line([(0, y), (N, y)], fill=tuple(int(CORE_TOP[i] * (1 - t) + CORE_BOT[i] * t) for i in range(3)))
        img = Image.composite(grad, img, m)
        if self.spark:
            sp = Image.new("L", (N * SS, N * SS), 0)
            sd = ImageDraw.Draw(sp)
            for (x, y, r) in self.spark:
                sd.ellipse([self.k(x - r), self.k(y - r), self.k(x + r), self.k(y + r)], fill=255)
            sp = sp.resize((N, N), Image.BOX)
            img = Image.composite(Image.new("RGB", (N, N), (255, 255, 255)), img, ImageChops.multiply(sp, m))
        edge = Image.new("L", (N * SS, N * SS), 0)
        ImageDraw.Draw(edge).ellipse([0, 0, N * SS - 1, N * SS - 1], fill=255)
        return Image.composite(img, Image.new("RGB", (N, N), (0, 0, 0)), edge.resize((N, N), Image.BOX))


C = 16.2      # panel centre in mm


def draw(expr, side):
    s = -1 if side == "L" else 1        # +1: nose toward +u (right half of the image)
    e = Eye()
    cx, cy = C + s * 3.2, C + 0.6
    w, h = 16.0, 21.0
    sparks = lambda dy=0.0, big=2.3: [(cx - s * 3.6, cy - 5.6 + dy, big), (cx - s * 1.2, cy - 2.4 + dy, 1.0)]
    if expr == "neutral":
        e.pill(cx, cy, w, h); e.spark = sparks()
    elif expr == "blink":
        e.pill(cx, cy + 3.0, w + 1.0, 2.6)
    elif expr == "talk_a":                      # no mouth: talking = eyes bounce (squash)
        e.pill(cx, cy - 0.6, w + 1.0, h - 3.0); e.spark = sparks(-0.6 + 1.5)
    elif expr == "talk_b":                      # stretch
        e.pill(cx, cy - 1.2, w - 0.6, h + 1.2); e.spark = sparks(-1.8)
    elif expr == "happy":
        e.arc(cx, cy + 3.0, 8.4, 198, 342, 4.6)
    elif expr == "surprised":
        e.pill(cx, cy - 0.6, w + 3.0, h + 3.0); e.spark = [(cx - s * 4.2, cy - 6.8, 2.8), (cx - s * 1.0, cy - 3.0, 1.2)]
    elif expr == "sleepy":                      # heavy flat lids over the top half
        e.pill(cx, cy, w, h)
        e.lid([(cx - 12, cy - 14), (cx + 12, cy - 14), (cx + 12, cy + 0.8), (cx - 12, cy + 0.8)])
        e.spark = [(cx - s * 3.6, cy + 3.2, 1.3)]
    elif expr == "asleep":                      # closed, resting
        e.arc(cx, cy - 5.5, 8.0, 25, 155, 2.4)
    elif expr == "sad":                         # lid drops toward the OUTER corner, eye a bit lower
        e.pill(cx, cy + 1.0, w - 0.6, h - 1.0)
        yi, yo = cy - 9.5, cy - 1.0             # inner (nose) / outer lid heights
        xi, xo = cx + s * 9, cx - s * 9
        e.lid([(xi, yi), (xo, yo), (xo, cy - 16), (xi, cy - 16)])
        e.spark = [(cx + s * 2.0, cy + 2.5, 1.6)]
    elif expr == "determined":                  # lid drops toward the NOSE (frown), slightly narrowed
        e.pill(cx, cy + 0.5, w, h - 1.0)
        yi, yo = cy - 1.8, cy - 8.0
        xi, xo = cx + s * 9, cx - s * 9
        e.lid([(xi, yi), (xo, yo), (xo, cy - 16), (xi, cy - 16)])
        e.spark = [(cx - s * 3.4, cy + 1.0, 1.8)]
    elif expr == "curious":                     # concept frame: one eye big, the other half-lidded
        big = 1.12 if side == "R" else 0.92
        e.pill(cx, cy - (1.2 if side == "R" else -0.6), w * big, h * big)
        if side == "L":
            e.lid([(cx - w, cy - h * 0.62), (cx + w, cy - h * 0.62), (cx + w, cy - h * 0.44 if s < 0 else cy - h * 0.28),
                   (cx - w, cy - h * 0.28 if s < 0 else cy - h * 0.44)])
        e.spark = [(cx - s * 3.6, cy - 6.0, 2.3)]
    return e.render()


EXPR = ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "asleep", "sad", "determined", "curious"]
if __name__ == "__main__":
    sheet = Image.new("RGB", (len(EXPR) * 2 * (N // 2) + len(EXPR) * 8, N // 2 + 8), (30, 30, 34))
    for i, ex in enumerate(EXPR):
        for j, sd in enumerate(("R", "L")):     # sheet shows eyes as seen from the front: robot-right eye on the left
            im = draw(ex, sd)
            im.save(os.path.join(OUT, f"{ex}_{sd}.png"))
            sheet.paste(im.resize((N // 2, N // 2), Image.NEAREST), (i * (N + 8) + j * (N // 2), 4))
    sheet.save(os.path.join(HERE, "faces_sheet.png"))
    print("ok", len(EXPR))
