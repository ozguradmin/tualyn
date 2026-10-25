#!/usr/bin/env python3
"""Hold-out check of recover2 (closed loop): 24 NEW random drop orientations (seed 11) + 8 pushes from standing
(angular-velocity kick about the long axis / pitch axis, i.e. a finger flick). usage: validate_rc.py mu [mass_scale]"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, recover as R, recover2 as R2
mu = float(sys.argv[1]); ms = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
xml = T.build(mu=mu)
import mujoco
def mk():
    s = T.Sim(xml, record=False)
    if ms != 1.0: s.m.body_mass[:] *= ms
    return s
rng = np.random.default_rng(11)
res = []
for k in range(24):
    roll, pitch = float(rng.uniform(-180, 180)), float(rng.uniform(-40, 40))
    s = mk(); q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015; s.hold(R.stand(), 1.2)
    st = R2.classify(s)[0]; ok, att = R2.recover(s)
    res.append(dict(kind='drop', roll=round(roll, 1), pitch=round(pitch, 1), settled=st, ok=ok, attempts=att if ok else -1, t=round(s.d.time, 2), **R2.pan_log(s))); print(res[-1], flush=True)
for wy, wx in [(9, 0), (-9, 0), (13, 3), (-13, -3), (11, 0), (-11, 4), (0, 22), (0, -22)]:
    s = mk(); s.set_pose(R.stand()); s.drop_to_floor(); s.hold(R.stand(), 0.4)
    s.d.qvel[3:6] = s.d.xmat[s.bid].reshape(3, 3) @ np.array([wx, wy, 0.0])
    s.hold(R.stand(), 1.4)
    st = R2.classify(s)[0]; ok, att = R2.recover(s)
    res.append(dict(kind='push', w_body=[wx, wy], settled=st, ok=ok, attempts=att if ok else -1, t=round(s.d.time, 2), **R2.pan_log(s))); print(res[-1], flush=True)
n = sum(r['ok'] for r in res); fell = [r for r in res if r['settled'] != 'up']
out = dict(mu=mu, mass_scale=ms, success=f"{n}/{len(res)}", fallen=len(fell), success_of_fallen=f"{sum(r['ok'] for r in fell)}/{len(fell)}",
           first_try_of_fallen=f"{sum(r['ok'] and r['attempts'] == 1 for r in fell)}/{len(fell)}", per_state=R2.per_state(fell),
           servo_model=R2.SERVO_MODEL(), pan_gear_peak_Nm=max(r['pan_gear_peak_Nm'] for r in res),
           pan_overshoot_max_deg=max(r['pan_overshoot_deg'] for r in res), cases=res)
print('RESULT', {k: v for k, v in out.items() if k != 'cases'}, flush=True)
json.dump(out, open(os.path.join(HERE, 'out', f'rec2_validate_mu{mu}_m{ms}.json'), 'w'), indent=1)
