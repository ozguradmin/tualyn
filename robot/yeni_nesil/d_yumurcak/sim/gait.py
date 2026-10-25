"""Open-loop Sesame/Kame-style gaits for Yumurcak, written the way the ESP32 firmware would run them.

Leg geometry (rig convention): yaw + swings the knee knuckle OUTWARD. For the FRONT legs that moves the
paw backwards (+Y), for the BACK legs it moves the paw forwards (-Y). So in stance (paw pushing backwards)
front yaws increase and back yaws decrease. Inward yaw is limited to -20 deg (knuckle meets the egg), so the
sweep is centred on `c` with c - A >= -20.
"""
import math
import numpy as np

SGN = {"fl": 1, "fr": 1, "bl": -1, "br": -1}          # stance sweep direction for forward walking
PAIR = {"fl": 0.0, "br": 0.0, "fr": 0.5, "bl": 0.5}     # diagonal trot pairs
# for turning in place (robot turns to its LEFT = CCW seen from above): every paw sweeps CW about the egg
# centre during stance. CW about +Z for FL/BR (axis +Z) is yaw -, for FR/BL (axis -Z) is yaw +.
TURN = {"fl": -1, "br": -1, "fr": 1, "bl": 1}


def leg_cycle(ph, duty):
    """ph in [0,1): returns (s in [-1,1] stance sweep position, lift in [0,1])"""
    if ph < duty:                       # stance: sweep -1 -> +1 linearly
        return -1 + 2 * ph / duty, 0.0
    u = (ph - duty) / (1 - duty)        # swing: +1 -> -1 with a smooth cosine, lift = sin
    return math.cos(math.pi * u), math.sin(math.pi * u)


def trot_pose(t, p, mode="walk", ramp=1.0):
    """p: dict(f, A, c, K0, dK, duty, [lean]) -> joint targets (deg). ramp scales amplitude (start/stop)."""
    f, A, c, K0, dK, duty = p["f"], p["A"], p["c"], p["K0"], p["dK"], p["duty"]
    out = {}
    for k in ("fl", "fr", "bl", "br"):
        ph = (t * f + PAIR[k]) % 1.0
        s, lift = leg_cycle(ph, duty)
        sg = SGN[k] if mode == "walk" else TURN[k]
        front = k[0] == "f"
        kb = K0 + (p.get("lean", 0.0) * (1 if front else -1))
        out["yaw_" + k] = c + sg * A * ramp * s
        out["knee_" + k] = kb + dK * ramp * lift
    return out
