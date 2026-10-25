#!/usr/bin/env python3
"""Writes the scene JSONs for the final renders of concept B 'Tarcin' and runs the guide's renderer.
Usage: python3 -I render_all.py [main|happy|xray|colors|rc|all]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "..", "..", "render", "render.js")
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)

PALETTES = {
    "tarcin": dict(main="#DF6E35", cream="#F3EEE4", dark="#2A2C31", accent="#DF6E35", hub="#C9602E", belly="#F3EEE4",
                   sock="#2A2C31", tail_b="#2A2C31", ear_in="#F3EEE4", face="#F3EEE4", paw="#2A2C31", eye="neutral"),
    "sut_mandalina": dict(main="#F3EEE4", cream="#F3EEE4", dark="#2A2C31", accent="#FF8A3D", hub="#E9E2D6", belly="#F3EEE4",
                          sock="#FF8A3D", tail_b="#FF8A3D", ear_in="#FF8A3D", face="#F3EEE4", paw="#2A2C31", eye="neutral"),
    "galaktik_gece": dict(main="#2E3352", cream="#FFC94A", dark="#1A1D2E", accent="#FFC94A", hub="#262A45", belly="#FFC94A",
                          sock="#1A1D2E", tail_b="#FFC94A", ear_in="#FFC94A", face="#FFC94A", paw="#1A1D2E", eye="neutral"),
}


def parts(d, pal, eye="neutral", cheeks_on=False, xray=False):
    P = PALETTES[pal]
    sh = dict(roughness=0.55, clearcoat=0.1)
    L = [
        dict(file=f"{d}/head_main.stl", color=P["main"], **sh),
        dict(file=f"{d}/head_face.stl", color=P["face"], **sh),
        dict(file=f"{d}/cheeks.stl", color=P["face"], roughness=0.55),
        dict(file=f"{d}/mouth.stl", color=P["dark"], roughness=0.6),
        dict(file=f"{d}/mask.stl", color="#0b0c0e", roughness=0.12, clearcoat=1.0, clearcoatRoughness=0.04),
        dict(file=f"{d}/eye_L.stl", image=f"tex/eye_{eye}_L.png", uvAxes=["x", "z"], imageEmissive=0.75, roughness=0.12, clearcoat=1.0, clearcoatRoughness=0.04),
        dict(file=f"{d}/eye_R.stl", image=f"tex/eye_{eye}_R.png", uvAxes=["x", "z"], imageEmissive=0.75, roughness=0.12, clearcoat=1.0, clearcoatRoughness=0.04),
        dict(file=f"{d}/nose.stl", color="#121417", roughness=0.2, clearcoat=1),
        dict(file=f"{d}/ear_outer.stl", color=P["main"], roughness=0.55),
        dict(file=f"{d}/ear_inner.stl", color=P["ear_in"], roughness=0.6),
        dict(file=f"{d}/body_top.stl", color=P["main"], **sh),
        dict(file=f"{d}/body_belly.stl", color=P["belly"], roughness=0.55),
        dict(file=f"{d}/hub.stl", color=P["hub"], roughness=0.6),
        dict(file=f"{d}/neck.stl", color=P["dark"], roughness=0.6),
        dict(file=f"{d}/pod.stl", color=P["main"], **sh),
        dict(file=f"{d}/pod_low.stl", color=P["sock"], roughness=0.6),
        dict(file=f"{d}/shin.stl", color=P["dark"], roughness=0.6),
        dict(file=f"{d}/paw.stl", color=P["paw"], roughness=0.85),
        dict(file=f"{d}/tail_a.stl", color=P["main"], roughness=0.6),
        dict(file=f"{d}/tail_b.stl", color=P["tail_b"], roughness=0.6),
    ]
    if cheeks_on:
        L[2].update(color="#FF9AAE", emissive="#FF6F8E", emissiveIntensity=0.6)
    if xray:
        for p in L:
            if "image" not in p and "mask" not in p["file"]:
                p.update(opacity=0.16, castShadow=False, clearcoat=0.0)
            if "mask" in p["file"]:
                p.update(opacity=0.35, castShadow=False)
        C = dict(int_servo="#2F6FEB", int_horn="#F5F5F5", int_neck="#2F6FEB", int_tail_servo="#2F6FEB",
                 int_battery="#43A047", int_mcu="#1B5E20", int_power="#FB8C00", int_sensors="#8E24AA",
                 int_eyes="#00ACC1", int_head="#546E7A")
        for k, c in C.items():
            L.append(dict(file=f"{d}/{k}.stl", color=c, roughness=0.45, metalness=0.05))
    return L


def scene(name, d, views, pal="tarcin", eye="neutral", cheeks_on=False, xray=False, w=1600, h=1200, bg="#ECE8E1"):
    sc = dict(width=w, height=h, background=bg, exposure=1.0, parts=parts(d, pal, eye, cheeks_on, xray), views=views)
    fn = os.path.join(HERE, f"scene_{name}.json")
    json.dump(sc, open(fn, "w"), indent=1)
    subprocess.run(["node", RENDER, fn, OUT], check=True, capture_output=True)
    return [os.path.join(OUT, v["name"] + ".png") for v in views]


def label(img_path, text, sub=None):
    im = Image.open(img_path).convert("RGB")
    dr = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(im.height * 0.04))
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(im.height * 0.028))
    except Exception:
        f1 = f2 = ImageFont.load_default()
    dr.text((int(im.width * 0.04), int(im.height * 0.04)), text, fill="#2A2C31", font=f1)
    if sub:
        dr.text((int(im.width * 0.04), int(im.height * 0.04 + im.height * 0.055)), sub, fill="#5A5C61", font=f2)
    return im


def main(which):
    if which in ("main", "all"):
        scene("final", "stl", [
            dict(name="B_hero", azimuth=-34, elevation=13, distance=0.92, fov=28),
            dict(name="B_front", azimuth=0, elevation=4, distance=0.95),
            dict(name="B_side", azimuth=-90, elevation=3, distance=0.95),
            dict(name="B_rear34", azimuth=-145, elevation=16, distance=0.95),
        ])
    if which in ("happy", "all"):
        scene("happy", "stl_happy", [dict(name="B_happy_wave", azimuth=-28, elevation=12, distance=0.92, fov=28)],
              eye="happy", cheeks_on=True)
    if which in ("xray", "all"):
        scene("xray", "stl", [dict(name="B_xray", azimuth=-38, elevation=22, distance=0.92, fov=28)], xray=True, bg="#F2F0EC")
    if which in ("colors", "all"):
        ims = []
        names = [("tarcin", "Tarçın", "cinnamon / cream / charcoal"),
                 ("sut_mandalina", "Süt & Mandalina", "ivory / tangerine"),
                 ("galaktik_gece", "Galaktik Gece", "indigo / sunflower")]
        for pal, t, sub in names:
            p = scene("col_" + pal, "stl", [dict(name="col_" + pal, azimuth=-34, elevation=13, distance=0.92, fov=28)],
                      pal=pal, w=1000, h=1000)[0]
            ims.append(label(p, t, sub))
        W = sum(i.width for i in ims)
        sheet = Image.new("RGB", (W, ims[0].height), "#ECE8E1")
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0)); x += i.width
        sheet.save(os.path.join(OUT, "B_colorways.png"))
    if which in ("rc", "all"):
        ims = []
        caps = [("1  falls on its side", "IMU: roll > 85 deg"), ("2  rolls onto its back", "legs swing, tail -35 deg"),
                ("3  tail lever + leg kick", "tail +46 deg, flips over"), ("4  standing  (t = 5.4 s)", "MuJoCo, MG90S 0.2 N m limit")]
        for i in range(1, 5):
            p = scene(f"rc{i}", f"stl_rc{i}", [dict(name=f"rc{i}", azimuth=-60, elevation=18, distance=1.0, fov=28)], w=900, h=800)[0]
            ims.append(label(p, *caps[i - 1]))
        W = sum(i.width for i in ims)
        sheet = Image.new("RGB", (W, ims[0].height), "#ECE8E1")
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0)); x += i.width
        sheet.save(os.path.join(OUT, "B_selfrighting.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
