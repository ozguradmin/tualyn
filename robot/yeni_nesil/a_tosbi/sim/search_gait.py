"""Grid search of trot parameters for forward speed with stability (both mu). Writes out/gait_search.json."""
import itertools, json, math, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tosbi import Sim, REST, stand_pose, yaw_of
from gait import gait_targets, DEFAULT

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"); os.makedirs(OUT, exist_ok=True)


def body_floor_contact(s):
    m, d = s.m, s.d
    for i in range(d.ncon):
        c = d.contact[i]
        names = (m.geom(c.geom1).name, m.geom(c.geom2).name)
        if "floor" in names and not any("toe" in n or "boot" in n for n in names):
            return True
    return False


def evaluate(p, mu=0.6, dur=6.0, fwd=1.0, turn=0.0, sign=1):
    s = Sim(mu); s.set_pose(stand_pose(sign));
    if sign < 0:
        s.d.qpos[3:7] = [0, 0, 1, 0]   # flipped about body y: face B up
    s.drop_to_floor(0.2); s.run(0.4, record=False)
    t0 = s.t; ramp = p["T"]
    pol = lambda sim, t: gait_targets(t - t0, p, sign=sign, fwd=fwd, turn=turn, amp=min(1.0, (t - t0) / ramp))
    s.run(ramp, pol, record=False)
    b0 = s.base(); y0 = yaw_of(b0[3:]); R0 = s.R().copy()
    tilt = 0.0; drag = 0; tmax = 0.0; n = 0; zs = []; yaw_acc = 0.0; yprev = y0
    t_end = s.t + dur
    while s.t < t_end:
        s.run(0.02, pol, record=False)
        R = s.R(); tilt = max(tilt, math.degrees(math.acos(min(1, abs(R[2, 2])))))
        drag += body_floor_contact(s); n += 1
        tmax = max(tmax, s.max_actuator_torque()); zs.append(s.base()[2])
        yc = yaw_of(s.base()[3:]); yaw_acc += (yc - yprev + math.pi) % (2 * math.pi) - math.pi; yprev = yc
    b1 = s.base()
    dp = np.array(b1[:3]) - np.array(b0[:3])
    fwd_dir = R0 @ np.array([0, -1.0, 0]); fwd_dir[2] = 0; fwd_dir /= np.linalg.norm(fwd_dir)
    lat_dir = np.array([-fwd_dir[1], fwd_dir[0], 0])
    dyaw = math.degrees(yaw_acc)                      # unwrapped, accumulated every 20 ms
    return {"speed_cm_s": float(dp @ fwd_dir) / 10 / dur, "lat_cm": float(dp @ lat_dir) / 10, "yaw_deg": dyaw,
            "yaw_rate_deg_s": dyaw / dur, "max_tilt_deg": tilt, "body_drag_frac": drag / max(1, n), "max_torque": tmax,
            "z_range_mm": float(np.ptp(zs)), "upright": bool(s.up() * sign > 0.8)}


if __name__ == "__main__":
    res = []
    grid = dict(T=[0.36, 0.5, 0.7], sw=[0.5], lift=[25, 40], bias=[0.0, 3.0], Ab=[14, 20], push=[0.0, 6.0])
    keys = list(grid)
    t0 = time.time()
    for vals in itertools.product(*grid.values()):
        p = dict(DEFAULT); p.update(dict(zip(keys, vals)))
        r6 = evaluate(p, 0.6); r4 = evaluate(p, 0.4)
        res.append({"p": p, "mu0.6": r6, "mu0.4": r4})
        print(json.dumps({k: p[k] for k in keys}), "| 0.6: v %.2f lat %.1f yaw %.0f tilt %.0f drag %.2f tq %.3f | 0.4: v %.2f lat %.1f yaw %.0f" % (
            r6["speed_cm_s"], r6["lat_cm"], r6["yaw_deg"], r6["max_tilt_deg"], r6["body_drag_frac"], r6["max_torque"],
            r4["speed_cm_s"], r4["lat_cm"], r4["yaw_deg"]), flush=True)
    json.dump(res, open(os.path.join(OUT, "gait_search.json"), "w"), indent=1)
    print("time", time.time() - t0)
