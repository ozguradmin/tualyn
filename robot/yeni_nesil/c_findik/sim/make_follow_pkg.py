#!/usr/bin/env python3
"""Build a throw-away view package for the walk follow-cam strip: same model.glb/faces, but walk.json's base is
wrapped back by whole 30 cm steps (a pure ground-plane shift, a multiple of the 1 cm grid) so the robot always stays
over the 60 cm posecheck grid and inside the shadow frustum.  Joint angles, height and attitude are untouched.
usage: python3 -I make_follow_pkg.py <outdir>      then: node render/posecheck.js <outdir> sim/strip_follow.json sim/strips
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
out = os.path.abspath(sys.argv[1]); os.makedirs(os.path.join(out, "anim"), exist_ok=True)
for f in ("model.glb", "faces"):
    dst = os.path.join(out, f)
    if not os.path.exists(dst):
        os.symlink(os.path.join(PKG, f), dst)
m = json.load(open(os.path.join(PKG, "manifest.json")))
a = json.load(open(os.path.join(PKG, "anim", "walk.json")))
WRAP = 300.0
for b in a["base"]:
    k = round(b[1] / WRAP)
    b[1] -= k * WRAP
m["animations"] = {"walk": "anim/walk.json"}
json.dump(a, open(os.path.join(out, "anim", "walk.json"), "w"), separators=(",", ":"))
json.dump(m, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False)
print("follow package", out)
