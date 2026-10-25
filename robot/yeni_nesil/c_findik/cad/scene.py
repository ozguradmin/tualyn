#!/usr/bin/env python3
"""Write a renderer scene.json for one STL set.
usage: python3 scene.py <stl_dir> <emotion> <out_scene.json> <views> [w h] [xray]
views: comma list of name:az:el:dist[:fov[:tx:ty:tz]]"""
import json, os, sys

stl_dir, emo, out, views = sys.argv[1:5]
W = int(sys.argv[5]) if len(sys.argv) > 5 else 1400
H = int(sys.argv[6]) if len(sys.argv) > 6 else 1050
XRAY = len(sys.argv) > 7 and sys.argv[7] == "xray"
base = os.path.dirname(os.path.abspath(out))
rel = lambda p: os.path.relpath(os.path.abspath(p), base)

CREAM, CARAMEL = "#EFE3CF", "#CF8A46"
mats = {
    "cream":   dict(color=CREAM, roughness=0.55, clearcoat=0.12, clearcoatRoughness=0.5, sheen=0.25),
    "cream2":  dict(color=CREAM, roughness=0.55, clearcoat=0.12),
    "caramel": dict(color=CARAMEL, roughness=0.5, clearcoat=0.15, clearcoatRoughness=0.5, sheen=0.2),
    "dark":    dict(color="#15110E", roughness=0.16, clearcoat=1.0, clearcoatRoughness=0.06),
    "glass":   dict(color="#050505", roughness=0.08, clearcoat=1.0, clearcoatRoughness=0.02),
    "tyre":    dict(color="#2A2623", roughness=0.85),
    "legcaramel": dict(color=CARAMEL, roughness=0.5, clearcoat=0.15, clearcoatRoughness=0.5, sheen=0.2),
    "legcream": dict(color=CREAM, roughness=0.55, clearcoat=0.12),
    "lens":    dict(color="#0A0A0C", roughness=0.03, clearcoat=1.0, clearcoatRoughness=0.02, opacity=0.2),
    "blush":   dict(color="#FF8C8C", roughness=0.6, emissive="#FF6F7A", emissiveIntensity=0.55, opacity=0.75),
}
xray_int = {
    "int_servo": "#2F57C8", "int_motor": "#C9CED6", "int_battery": "#2E9E62", "int_pcb": "#1E6B3A",
    "int_pcb_blue": "#1F4FA0", "int_lcdglass": "#111111", "int_speaker": "#555555", "int_chassis": "#B9B4AC",
}
parts = []
files = set(os.listdir(stl_dir))
for m, mt in mats.items():
    f = m + ".stl"
    if f in files:
        p = dict(file=rel(os.path.join(stl_dir, f)), **mt)
        if XRAY and m in ("cream", "caramel", "cream2"):
            p.update(opacity=0.16, roughness=0.3, clearcoat=0.0, sheen=0.0)
            p["castShadow"] = False
        if XRAY and m in ("dark", "lens"):
            p.update(opacity=0.35)
            p["castShadow"] = False
        parts.append(p)
for side in ("l", "r"):
    f = "eye_%s.stl" % side
    if f in files:
        parts.append(dict(file=rel(os.path.join(stl_dir, f)), image=rel("tex/eye_%s_%s.png" % (emo, side)),
                          uvAxes=["x", "z"], imageEmissive=1.05, roughness=0.22, clearcoat=0.55,
                          clearcoatRoughness=0.03, crease=80))
if XRAY:
    for f in sorted(files):
        if f.startswith("int_") and f.endswith(".stl"):
            k = f[:-4]
            parts.append(dict(file=rel(os.path.join(stl_dir, f)), color=xray_int.get(k, "#888888"),
                              roughness=0.45, metalness=0.3 if k == "int_motor" else 0.0))
vs = []
for v in views.split(","):
    a = v.split(":")
    d = dict(name=a[0], azimuth=float(a[1]), elevation=float(a[2]), distance=float(a[3]))
    if len(a) > 4:
        d["fov"] = float(a[4])
    if len(a) > 7:
        d["target"] = [float(a[5]), float(a[6]), float(a[7])]
    vs.append(d)
scene = dict(width=W, height=H, background="#EDE8E1", exposure=1.0, envIntensity=0.85, keyIntensity=2.0,
             rimIntensity=0.9, shadowOpacity=0.2, shadowSoftness=8, parts=parts, views=vs)
json.dump(scene, open(out, "w"), indent=1)
print("scene", out, len(parts), "parts")
