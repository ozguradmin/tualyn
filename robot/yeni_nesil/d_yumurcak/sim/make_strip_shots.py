#!/usr/bin/env python3
"""Fixed-camera posecheck shots for every clip (camera target + distance fixed in world mm; the 'distance'
argument of posecheck is divided by the per-frame Box3 radius from verify_anims.py so the camera does not zoom).
-> <out>/strip_shots.json ; compose_strips.py tiles the renders into ../stills/anim_<clip>.png"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
V = json.load(open(os.path.join(HERE, "out", "verify_anims.json")))
SIN = math.sin(math.radians(14.0))
CAM = {  # clip: (azimuth, elevation, target mm, camera distance m, times s)
    "idle": (30, 12, [0, 0, 68], 0.50, [0, 0.8, 1.3, 2.5, 3.4, 4.6]),
    "walk": (90, 10, [0, -130, 62], 0.78, [0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.95]),
    "turn": (25, 35, [0, 0, 60], 0.52, [0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.95]),
    "talk": (20, 8, [0, 0, 74], 0.46, [0.1, 0.45, 1.0, 1.95, 3.0, 3.75, 4.3, 4.95]),
    "happy": (-30, 10, [0, 0, 70], 0.50, [0, 0.6, 1.0, 1.3, 1.6, 2.2, 3.35, 3.95]),
    "sleep": (30, 12, [0, 0, 58], 0.50, [0, 0.8, 1.6, 2.3, 2.9, 3.95]),
    "fall_recover": (0, 18, [-55, 0, 55], 0.62, [0, 0.7, 0.9, 1.2, 1.6, 2.4, 3.0, 3.4, 3.9, 4.5, 5.2, 6.7]),
    "fall_recover_back": (90, 18, [25, 70, 55], 0.70, [0, 0.8, 1.0, 1.6, 2.6, 4.2, 5.6, 7.0, 8.6, 10.4, 11.4, 13.4]),
}
shots = []
for clip, (az, el, tgt, dist, ts) in CAM.items():
    rads = V[clip]["rad_m"]
    for t in ts:
        i = min(len(rads) - 1, int(round(t * 30)))
        d = dist * SIN / (1.05 * rads[i])
        shots.append({"name": f"{clip}_{int(round(t * 1000)):05d}", "anim": clip, "t": t, "azimuth": az, "elevation": el,
                      "target": tgt, "distance": round(d, 5)})
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
json.dump({"width": 800, "height": 600, "shots": shots}, open(os.path.join(out, "strip_shots.json"), "w"), indent=0)
json.dump(CAM, open(os.path.join(out, "strip_cams.json"), "w"))
print(len(shots), "shots")
