"""Self-righting success rate. 26 landing orientations (which body direction points at the floor: 6 faces,
12 edges, 8 corners of the body box) x random yaw, dropped from 15 mm with the stand pose held, plus
8 shove tests (standing robot hit by a 0.15 s push at mid-plane height from 8 directions + a lift on one side).
Each at mu 0.6 and 0.4. Writes out/recovery.json."""
import itertools, json, math, os, sys, time
import numpy as np, mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tosbi import Sim, stand_pose, LEGS
from recover import Recover

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"); os.makedirs(OUT, exist_ok=True)


def quat_from_to(a, b):
    a = np.asarray(a, float) / np.linalg.norm(a); b = np.asarray(b, float) / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b)
    if c < -0.999999:
        ax = np.cross(a, [1, 0, 0]);
        if np.linalg.norm(ax) < 1e-6: ax = np.cross(a, [0, 1, 0])
        ax /= np.linalg.norm(ax); return np.array([0, *ax])
    q = np.array([1 + c, *v]); return q / np.linalg.norm(q)


def qmul(a, b):
    r = np.zeros(4); mujoco.mju_mulQuat(r, np.asarray(a, float), np.asarray(b, float)); return r


def standing_ok(s, sign):
    m, d = s.m, s.d
    toes = set(); body_on_floor = False
    for i in range(d.ncon):
        c = d.contact[i]; n1, n2 = m.geom(c.geom1).name, m.geom(c.geom2).name
        if "floor" not in (n1, n2): continue
        other = n2 if n1 == "floor" else n1
        if "toe" in other or "boot" in other: toes.add(other.split("_")[1])
        else: body_on_floor = True
    return len(toes) >= 3 and not body_on_floor and s.up() * sign > 0.94


def run_case(mu, down=None, yaw=0.0, push=None, seed=0, T=12.0, record=False, height=15.0, tumble=1.0, tau=0.20, quat=None, t_ctrl=0.9):
    rng = np.random.default_rng(seed)
    s = Sim(mu); s.set_pose(stand_pose(1))
    s.m.actuator_forcerange[:] = [-tau, tau]
    if down is not None:
        q = quat_from_to(down, [0, 0, -1])                    # body vector `down` -> world -z
        qz = np.array([math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)])
        s.d.qpos[3:7] = qmul(qz, q) if quat is None else quat
        s.drop_to_floor(height)
        s.d.qvel[3:6] = rng.normal(0, tumble, 3)              # tumble, rad/s
    else:
        s.drop_to_floor(0.0)
    ctrl = Recover()
    pushfn = None
    if push is not None:
        ang, F, kind = push
        def pushfn(sim, t):
            if 0.5 <= t < 0.65:
                b = sim.bid
                f = np.array([math.cos(ang), math.sin(ang), 0.0]) * F
                if kind == "lift":  # a hand lifting one side of the shell (upward force at the shell edge)
                    p = sim.d.xpos[b] + sim.R() @ np.array([41 * math.cos(ang), 41 * math.sin(ang), 42.45]) / 1000
                    f = np.array([0, 0, F])
                else:
                    p = sim.d.xpos[b] + sim.R() @ np.array([0, 0, 0.06])
                # xfrc_applied acts at the body CoM: convert the force at p into force + torque about the CoM
                com = sim.d.xipos[b]
                sim.d.xfrc_applied[b, :3] = f; sim.d.xfrc_applied[b, 3:] = np.cross(p - com, f)
    t_start_ctrl = t_ctrl if down is not None else 0.0
    tq = {"max": 0.0}
    def pol(sim, t):
        if t < t_start_ctrl: return None
        return ctrl(sim, t)
    ok_since = None; t_rec = None
    def pol2(sim, t):
        r = pol(sim, t)
        if t >= t_start_ctrl: tq["max"] = max(tq["max"], sim.max_actuator_torque())
        return r
    while s.t < T:
        s.run(0.1, pol2, record=record, push=pushfn)
        if ctrl.done_t is not None and standing_ok(s, ctrl.sign):
            ok_since = ok_since or s.t
            if s.t - ok_since > 1.0: t_rec = ok_since; break
        else:
            ok_since = None
    fell = any(m_ in ("flip_through", "edge_kick") for _, m_ in ctrl.log)
    return {"ok": t_rec is not None, "t_recovered": None if t_rec is None else round(t_rec, 2), "final_face": "A" if ctrl.sign > 0 else "B",
            "fell_over": fell or down is not None, "modes": ctrl.log, "up_end": round(float(s.up()), 3), "max_torque_Nm": round(tq["max"], 3)}, s, ctrl


DOWNS = {}
for v in itertools.product([-1, 0, 1], repeat=3):
    if v == (0, 0, 0): continue
    n = sum(abs(x) for x in v)
    DOWNS[{1: "face", 2: "edge", 3: "corner"}[n] + str(v).replace(" ", "")] = v

def rand_quat(rng):
    q = rng.normal(size=4); return q / np.linalg.norm(q)


def summary(rs):
    return f"{sum(r['ok'] for r in rs)}/{len(rs)}"


if __name__ == "__main__":
    res = {"systematic_drop_15mm": {}, "random_tumble_40mm": {}, "placed_still": {}, "pushes": {}, "weak_servo_4V8_random": {}}
    t0 = time.time()
    PLACED = {"left side": (1, 0, 0), "right side": (-1, 0, 0), "nose down": (0, -1, 0), "tail down": (0, 1, 0), "on back": (0, 0, 1),
              "back-left edge": (1, 0, 1)}
    for mu in (0.6, 0.4):
        for i, (name, v) in enumerate(DOWNS.items()):
            r, s, c = run_case(mu, down=v, yaw=(i * 2.399) % (2 * math.pi), seed=i)
            res["systematic_drop_15mm"][f"{name}@{mu}"] = r
        for i in range(30):
            rng = np.random.default_rng(100 + i)
            r, s, c = run_case(mu, down=(0, 0, 1), quat=rand_quat(rng), seed=100 + i, height=40.0, tumble=3.0)
            res["random_tumble_40mm"][f"r{i}@{mu}"] = r
        for name, v in PLACED.items():
            r, s, c = run_case(mu, down=v, yaw=0.0, height=1.0, tumble=0.0, t_ctrl=1.5)
            res["placed_still"][f"{name}@{mu}"] = r
            print(f"placed mu {mu} {name:15s} {r['ok']} t {r['t_recovered']} face {r['final_face']} modes {r['modes'][:8]}", flush=True)
        for k in range(8):
            ang = k * math.pi / 4
            for kind, F in (("shove", 10.0), ("lift", 6.0)):
                r, s, c = run_case(mu, push=(ang, F, kind))
                res["pushes"][f"{kind}{k*45}@{mu}"] = r
    for i in range(30):
        rng = np.random.default_rng(100 + i)
        r, s, c = run_case(0.6, down=(0, 0, 1), quat=rand_quat(rng), seed=100 + i, height=40.0, tumble=3.0, tau=0.177)
        res["weak_servo_4V8_random"][f"r{i}@0.6"] = r
    out = {}
    for cat, d in res.items():
        for mu in (0.6, 0.4):
            rs = [v for k, v in d.items() if k.endswith(f"@{mu}")]
            if not rs: continue
            fails = [k for k, v in d.items() if k.endswith(f"@{mu}") and not v["ok"]]
            fell = sum(1 for v in rs if any(m in ("flip_through", "edge_kick") for _, m in v["modes"]))
            ts = [v["t_recovered"] for v in rs if v["ok"]]
            out[f"{cat}@{mu}"] = {"success": summary(rs), "needed_righting": fell, "fails": fails,
                                  "t_median_s": float(np.median(ts)) if ts else None, "t_max_s": max(ts) if ts else None,
                                  "max_torque_Nm": max(v["max_torque_Nm"] for v in rs),
                                  "ended_face_B": sum(1 for v in rs if v["final_face"] == "B")}
            print(cat, mu, out[f"{cat}@{mu}"], flush=True)
    res["summary"] = out
    json.dump(res, open(os.path.join(OUT, "recovery.json"), "w"), indent=1)
    print("time", round(time.time() - t0, 1))
