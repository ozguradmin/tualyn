#!/usr/bin/env python3
"""Write scene.json for a pose folder and call the shared renderer.
usage: python3 -I render.py <pose_dir> <eye_png> <views-preset> [colourway] [outdir]"""
import json, os, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "renderer", "render.js")

COLOURWAYS = {
    # shell (domes), skin (head/limbs/rim), accent (bezel, toe caps)
    "nane":   {"shell": "#5DBB97", "skin": "#E8DDCB", "accent": "#FF6A5C", "leg": "#5DBB97", "bg": "#E9E4DC"},
    "nane_dark": {"shell": "#5DBB97", "skin": "#E8DDCB", "accent": "#FF6A5C", "bg": "#E9E4DC"},
    "nane_mint": {"shell": "#5DBB97", "skin": "#E8DDCB", "accent": "#FF6A5C", "leg": "#5DBB97", "bg": "#E9E4DC"},
    "nane_cream": {"shell": "#5DBB97", "skin": "#E8DDCB", "accent": "#FF6A5C", "leg": "#E8DDCB", "bg": "#E9E4DC"},
    "nane_sage": {"shell": "#5DBB97", "skin": "#E8DDCB", "accent": "#FF6A5C", "leg": "#3F6F62", "bg": "#E9E4DC"},
    "mandalina": {"shell": "#F2955A", "skin": "#EEE6DA", "accent": "#36456B", "leg": "#F2955A", "bg": "#EDE7E0"},
    "gece":   {"shell": "#3C4478", "skin": "#EEE7DA", "accent": "#FFC94A", "leg": "#3C4478", "bg": "#E6E4EC"},
}

def scene(pose_dir, eye_png, preset, cw="nane", xray=False):
    c = COLOURWAYS[cw]
    shell_alpha = 0.18 if xray else 1.0
    parts = [
        {"file": "shell.stl", "color": c["shell"], "roughness": 0.52, "clearcoat": 0.12, "sheen": 0.3,
         "opacity": shell_alpha},
        {"file": "skin.stl", "color": c["skin"], "roughness": 0.55, "clearcoat": 0.1, "sheen": 0.25,
         "opacity": 0.22 if xray else 1.0},
        {"file": "leg.stl", "color": c.get("leg", "#2E3238"), "roughness": 0.62, "sheen": 0.2,
         "opacity": 0.3 if xray else 1.0},
        {"file": "accent.stl", "color": c["accent"], "roughness": 0.6, "sheen": 0.4},
        {"file": "tpu.stl", "color": c["accent"], "roughness": 0.75, "sheen": 0.5},
        {"file": "dark.stl", "color": "#16181c", "roughness": 0.35},
        {"file": "metal.stl", "color": "#9aa0a6", "roughness": 0.3, "metalness": 0.8},
        {"file": "visor.stl", "image": eye_png, "uvAxes": ["x", "z"], "imageEmissive": 1.35,
         "roughness": 0.3, "clearcoat": 0.25, "clearcoatRoughness": 0.25, "envMapIntensity": 0.18, "specularIntensity": 0.45, "crease": 80},
    ]
    if xray:
        parts += [
            {"file": "servo.stl", "color": "#2b3f7a", "roughness": 0.5},
            {"file": "pcb.stl", "color": "#1f7a4a", "roughness": 0.5},
            {"file": "chip.stl", "color": "#222222", "roughness": 0.4},
            {"file": "cell.stl", "color": "#d6402b", "roughness": 0.4},
            {"file": "speaker.stl", "color": "#555a60", "roughness": 0.4, "metalness": 0.4},
        ]
    views = {
        "main": [
            {"name": "hero", "azimuth": -30, "elevation": 14, "distance": 0.70, "fov": 26},
            {"name": "front", "azimuth": 0, "elevation": 6, "distance": 0.80, "fov": 26},
            {"name": "side", "azimuth": -90, "elevation": 4, "distance": 0.80, "fov": 26},
            {"name": "top", "azimuth": 0, "elevation": 89, "distance": 0.80, "fov": 26},
            {"name": "back", "azimuth": 150, "elevation": 22, "distance": 0.80, "fov": 26},
        ],
        "one": [{"name": "hero", "azimuth": -30, "elevation": 14, "distance": 0.70, "fov": 26}],
        "action": [{"name": "action", "azimuth": -24, "elevation": 12, "distance": 0.80, "fov": 26}],
        "xray": [{"name": "xray", "azimuth": -40, "elevation": 34, "distance": 0.78, "fov": 26}],
        "flip": [{"name": "flip", "azimuth": -34, "elevation": 18, "distance": 0.80, "fov": 26}],
        "seq": [{"name": "seq", "azimuth": -55, "elevation": 16, "distance": 0.86, "fov": 26}],
    }[preset]
    return {"width": 1600, "height": 1200, "background": c["bg"], "exposure": 0.86, "envIntensity": 0.8,
            "keyIntensity": 2.0, "shadowOpacity": 0.25, "parts": parts, "views": views}

if __name__ == "__main__":
    pose_dir, eye, preset = sys.argv[1], sys.argv[2], sys.argv[3]
    cw = sys.argv[4] if len(sys.argv) > 4 else "nane"
    outdir = sys.argv[5] if len(sys.argv) > 5 else pose_dir
    shutil.copy(eye, os.path.join(pose_dir, os.path.basename(eye)))
    sc = scene(pose_dir, os.path.basename(eye), preset, cw, xray=(preset == "xray"))
    fn = os.path.join(pose_dir, f"scene_{preset}_{cw}.json")
    json.dump(sc, open(fn, "w"), indent=1)
    subprocess.run(["node", RENDER, fn, outdir], check=True)
