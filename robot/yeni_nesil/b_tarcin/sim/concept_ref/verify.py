#!/usr/bin/env python3
"""Robustness check of a recovery keyframe sequence ('rc_tarcin'): random drop orientations, friction and mass
variations, OpenCat-style retries (mirrored on alternate attempts).
Usage: verify.py <seq.json> [--tail-scale=x]"""
import sys, math, os, json
import numpy as np, mujoco

SEQ = sys.argv[1]
sys.argv = [sys.argv[0], 'stl'] + sys.argv[2:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import righting as R

R.VMAX = math.radians(600)
R.build_xml()
base = open(os.path.join(R.OUT, 'tarcin.xml')).read()
seq = json.load(open(SEQ))['seq']
LEGS = R.LEGS


def spec_from(kf, down):
    sp = {}
    for leg in LEGS:
        sx = 1 if leg[1] == 'R' else -1
        role = ('d' if sx == down else 'u') + leg[0]
        a, k = kf[role]
        sp[leg] = (a, a + k)
    return sp


def run(m, roll, pitch, tries=4):
    r = R.Runner(m)
    r.set_orientation(roll, pitch)
    r.step_to(r.target, 1.2)
    peak = 0.0
    for att in range(tries):
        x, y, z = r.axes()
        if z[2] > 0.85:
            return True, att, peak
        down = 1 if x[2] < 0 else -1
        if att % 2 == 1:
            down = -down              # OpenCat-style: mirror the move on the next attempt
        for kf in seq:
            tg = R.pose_targets(spec_from(kf, down))
            tg['pan'] = math.radians(kf['pan'] * down)
            tg['tail'] = math.radians(kf.get('tail', 0) * down)
            r.step_to(tg, kf['T'])
            peak = max(peak, float(np.abs(r.d.actuator_force).max()))
        st = R.pose_targets(R.stand_spec()); st['pan'] = 0; st['tail'] = 0
        r.step_to(st, 0.8)
        r.step_to(st, 0.5)
    x, y, z = r.axes()
    return bool(z[2] > 0.85), tries, peak


if __name__ == '__main__':
    rng = np.random.default_rng(7)
    orients = [(90, 0), (-90, 0), (180, 0), (135, 0), (-135, 0), (90, 20), (-90, -20), (180, -15), (180, 15)] + \
              [(float(rng.uniform(-180, 180)), float(rng.uniform(-35, 35))) for _ in range(15)]
    variants = [('nominal mu=0.6', 0.6, 1.0), ('slippery mu=0.4', 0.4, 1.0), ('grippy mu=0.9', 0.9, 1.0), ('+10% mass', 0.6, 1.1)]
    only = [a.split('=')[1] for a in sys.argv if a.startswith('--only=')]
    res = {}
    for name, mu, ms in variants:
        if only and not name.startswith(only[0]):
            continue
        xml = base.replace('friction="0.6 0.005 0.0001"', f'friction="{mu} 0.005 0.0001"')
        m = mujoco.MjModel.from_xml_string(xml)
        m.body_mass[:] *= ms
        ok, tries, peaks = 0, [], []
        for ro, pi in orients:
            s, t, pk = run(m, ro, pi)
            ok += s
            tries.append(t if s else -1)
            peaks.append(round(pk, 3))
        res[name] = dict(success=f"{ok}/{len(orients)}", attempts=tries, peak_torque_Nm=max(peaks))
        print(name, res[name], flush=True)
    tag = os.path.basename(SEQ).replace('.json', '')
    json.dump(dict(seq=SEQ, tail_scale=R.TAIL_SCALE, orientations=orients, results=res),
              open(os.path.join(R.OUT, f'verify_{tag}_tail{R.TAIL_SCALE}.json'), 'w'), indent=1)
