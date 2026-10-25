#!/usr/bin/env python3
"""Procedural eye frames for the two GC9A01 (240x240 round) screens, drawn the way the firmware would:
pure black background, one pupil-less glowing pill per screen, soft halo, small sparkle.
Writes tex/eye_<emotion>_<L|R>.png (L = robot's left = +x side, R = -x side)."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 480                      # draw at 2x, store at 2x for crisp texture
GLOW = (124, 244, 255)       # #7CF4FF
CORE = (214, 253, 255)

def pill_mask(w, h, cx, cy, r, lid_top=0.0, lid_angle=0.0, smile=0.0):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=255)
    if lid_top > 0 or lid_angle:
        # top lid: polygon covering from above a tilted line
        y0 = cy - h / 2 + lid_top * h
        dy = math.tan(math.radians(lid_angle)) * w / 2
        d.polygon([(cx - w, y0 - dy - 400), (cx + w, y0 + dy - 400), (cx + w, y0 + dy), (cx - w, y0 - dy)], fill=0)
    if smile > 0:
        # cheek push-up from below (happy squint): big ellipse removing the lower part
        d.ellipse([cx - w * 0.95, cy + h / 2 - smile * h, cx + w * 0.95, cy + h / 2 - smile * h + h * 1.3], fill=0)
    return m

def arc_mask(cx, cy, w, h, thick):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.arc([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2 + h * 0.6], start=200, end=340, fill=255, width=int(thick))
    # round caps
    for ang in (200, 340):
        a = math.radians(ang)
        rx, ry = w / 2 - thick / 2, (h * 1.6) / 2 - thick / 2
        px, py = cx + rx * math.cos(a), cy + h * 0.3 + ry * math.sin(a)
        d.ellipse([px - thick / 2, py - thick / 2, px + thick / 2, py + thick / 2], fill=255)
    return m

def compose(mask, sparkle=None, color=GLOW, core=CORE):
    img = Image.new("RGB", (S, S), (0, 0, 0))
    # halo
    halo = mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
    img.paste(Image.new("RGB", (S, S), color), (0, 0), halo)
    # body with vertical gradient
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        c = tuple(int(core[i] * (1 - t) * 0.55 + color[i] * (0.45 + t * 0.55)) for i in range(3))
        gd.line([(0, y), (S, y)], fill=c)
    soft = mask.filter(ImageFilter.GaussianBlur(1.6))
    img.paste(grad, (0, 0), soft)
    # inner bright core
    core_m = mask.filter(ImageFilter.GaussianBlur(26)).point(lambda v: max(0, int((v - 150) * 2.2)))
    img.paste(Image.new("RGB", (S, S), core), (0, 0), core_m)
    if sparkle:
        sx, sy, sr = sparkle
        sp = Image.new("L", (S, S), 0)
        ImageDraw.Draw(sp).ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=255)
        ImageDraw.Draw(sp).ellipse([sx + sr * 1.3, sy + sr * 1.5, sx + sr * 1.9, sy + sr * 2.1], fill=255)
        sp = ImageChops.multiply(sp.filter(ImageFilter.GaussianBlur(1.2)), mask)
        img.paste(Image.new("RGB", (S, S), (255, 255, 255)), (0, 0), sp)
    # round panel: outside the 240 px circle is not part of the screen
    circ = Image.new("L", (S, S), 0)
    ImageDraw.Draw(circ).ellipse([4, 4, S - 4, S - 4], fill=255)
    out = Image.new("RGB", (S, S), (0, 0, 0))
    out.paste(img, (0, 0), circ)
    return out

def eye(emotion, side):
    # side: +1 = eye on +x (image: nose is toward -x = left of image), -1 = eye on -x
    nose_dir = -side
    cx = S / 2 + nose_dir * 40
    cy = S / 2 + 8
    if emotion == "neutral":
        m = pill_mask(232, 300, cx, cy, 108)
        return compose(m, sparkle=(cx - 50, cy - 86, 24))
    if emotion == "happy":
        m = arc_mask(cx, cy - 10, 270, 210, 72)
        return compose(m)
    if emotion == "curious":
        # one eye bigger (the +x one), slight lid on the other
        if side > 0:
            m = pill_mask(252, 320, cx, cy - 6, 118)
            return compose(m, sparkle=(cx - 54, cy - 92, 26))
        m = pill_mask(218, 262, cx, cy + 10, 100, lid_top=0.22, lid_angle=-12 * side)
        return compose(m, sparkle=(cx - 44, cy - 50, 20))
    if emotion == "love":
        m = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(m)
        r = 62
        d.ellipse([cx - 2 * r + 8, cy - 70 - r, cx + 8, cy - 70 + r], fill=255)
        d.ellipse([cx - 8, cy - 70 - r, cx + 2 * r - 8, cy - 70 + r], fill=255)
        d.polygon([(cx - 2 * r + 12, cy - 50), (cx + 2 * r - 12, cy - 50), (cx, cy + 110)], fill=255)
        return compose(m, sparkle=(cx - 60, cy - 100, 16), color=(255, 120, 150), core=(255, 220, 230))
    raise ValueError(emotion)

if __name__ == "__main__":
    os.makedirs("tex", exist_ok=True)
    for emo in (sys.argv[1:] or ["neutral", "happy", "curious", "love"]):
        for side, tag in ((1, "L"), (-1, "R")):
            eye(emo, side).save(f"tex/eye_{emo}_{tag}.png")
    # orientation test texture
    t = Image.new("RGB", (256, 256), (0, 0, 0)); d = ImageDraw.Draw(t)
    d.rectangle([0, 0, 128, 40], fill=(255, 0, 0)); d.rectangle([0, 0, 40, 128], fill=(0, 255, 0))
    t.save("tex/orient.png")
    print("ok")
