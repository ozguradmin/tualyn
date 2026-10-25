"""helpers for recovery experiments: model variants + open-loop keyframe sequences (concept 'rc' structure)."""
import sys, os, re, json, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import tarcin as T, recover as R
RANGES = {"F": ((-20, 160), (-140, 25)), "H": ((-50, 130), (-25, 140))}
FINAL = dict(dF=[20, -44], dH=[-20, 44], uF=[20, -44], uH=[-20, 44], pan=0.0, tail=0.0, T=0.4)
def make_xml(variant, mu=0.6, meshdir=None):
    if meshdir: T.MESHDIR=meshdir; os.makedirs(meshdir,exist_ok=True)
    opts=variant.split('+') if variant!='base' else []
    pan=0.07
    if 'pan2' in opts: pan=0.2
    T.TAU_PAN=pan
    x=T.build(mu=mu, ears='soft' if 'soft' in opts else 'rigid')
    if 'tail8' in opts: x=x.replace('mesh="tail" mass="0.01410"','mesh="tail" mass="0.00810"')
    return x
def run_seq(xml, seq, roll, pitch, settle=1.0, model_cache={}):
    s = T.Sim(xml, record=False)
    q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015
    s.hold(R.stand(), settle)
    x, y, z = s.up(); down = 1 if x[2] < 0 else -1
    for kf in seq:
        s.hold(R.kf_target(kf, down), kf["T"])
    s.hold(R.stand(), 0.8); s.hold(R.stand(), 0.4)
    return float(s.up()[2][2])
def rand_kf(rng):
    kf = {}
    for role in ("dF", "dH", "uF", "uH"):
        (a0, a1), (k0, k1) = RANGES[role[1]]
        kf[role] = [float(rng.uniform(a0, a1)), float(rng.uniform(k0, k1))]
    kf["pan"] = float(rng.uniform(-40, 40)); kf["tail"] = float(rng.uniform(-85, 85)); kf["T"] = float(rng.uniform(0.25, 0.9))
    return kf
