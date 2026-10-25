"""Tosbi gaits (Sesame-style 2-DOF legs: hip yaw + knee). Trot: diagonal pairs (fl+rr, fr+rl) alternate.
Everything is in the body frame; `sign` = +1 standing on face A, -1 standing on face B (knees and neck mirrored)."""
import math
from tosbi import LEGS, smooth

PHASE = {"fl": 0.0, "rr": 0.0, "fr": 0.5, "rl": 0.5}
LEFT = {"fl", "rl"}                  # robot's left = +x
HIPMAX = {"fl": 14, "fr": 14, "rl": 20, "rr": 20}

DEFAULT = dict(T=0.5, sw=0.5, Af=14, Ab=14, lift=30, bias=0.0, knee=80, rbias=0.0, push=0.0)


def gait_targets(t, p, sign=1, fwd=1.0, turn=0.0, amp=1.0, neck=15):
    """fwd: +1 forward, -1 backward; turn: +1 = turn left (CCW seen from above), mixes with fwd.
    amp: 0..1 ramp of hip amplitude and lift."""
    turn = turn * sign                 # on face B the world yaw sense is mirrored; firmware flips it
    out = {}
    for l in LEGS:
        side = 1.0 if l in LEFT else -1.0
        dirn = fwd - turn * side * (1.0 if fwd == 0 else 0.6)  # turn left: left legs stroke backward
        dirn = max(-1.0, min(1.0, dirn))
        ph = ((t / p["T"]) + PHASE[l]) % 1.0
        front, back = p["Af"], -p["Ab"]
        if dirn < 0: front, back = back, front      # stroke reversed: swing goes front->back
        sc = abs(dirn) * amp
        bias = p["bias"] + (p["rbias"] if l in ("rl", "rr") else 0.0)
        if ph < p["sw"]:
            s = ph / p["sw"]
            hip = (back + (front - back) * smooth(s)) * sc
            knee = p["knee"] - p["lift"] * amp * math.sin(math.pi * s)
        else:
            s = (ph - p["sw"]) / (1 - p["sw"])
            hip = (front + (back - front) * s) * sc
            knee = p["knee"] + p["push"] * amp * math.sin(math.pi * s)
        hip = max(-20, min(HIPMAX[l], hip + bias))
        out[f"hip_{l}"] = hip
        out[f"knee_{l}"] = sign * min(90, knee)
    out["neck"] = sign * neck
    return out
