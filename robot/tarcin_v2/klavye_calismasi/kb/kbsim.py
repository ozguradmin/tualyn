#!/usr/bin/env python3
"""Tarcin on keyboards: model = the package's tarcin.py model (same GLB hulls, masses, MG90S servo model with droop,
coupled hip limit) + keyboard geoms from kbd.py. Runs a gait controller from a start pose already standing on the keys
and scores it.

Failure rules (any of them ends the run):
  fell      body up-vector z < 0.7 (tilt > 45 deg) or body origin > 20 mm below its start height (slid off)
  stuck     a paw moved < 3 mm (world xy) during a 3 s window while the gait was stepping, or the body made < 10 mm of
            progress along the heading in a 3 s window
  off       any paw down on the desk (stepped off the keyboard)
  timeout   target distance not reached in t_max
success = progress along the start heading >= target (25 cm, or less where the keyboard is shorter)."""
import sys, os, math, json, time
import numpy as np
import mujoco
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(os.path.dirname(HERE), "pkg", "sim")
sys.path.insert(0, SIM); sys.path.insert(0, HERE)
import tarcin as T, gait as G
import kbd

LEG_J = {"hip": [f"hip_{l}" for l in T.LEGS], "knee": [f"knee_{l}" for l in T.LEGS]}
_XML0 = {}


def base_xml(mu_desk=0.6):
    if mu_desk not in _XML0:
        _XML0[mu_desk] = T.build(mu=mu_desk)
    return _XML0[mu_desk]


# mechanical variants (defaults = the package as built)
VARIANT = dict(paw_mu=None, shin_ext=0.0, pod_scale_y=1.0, track_add=0.0, ski=0.0)


def apply_variant():
    """patch the IK foot points for a longer shin (shin_ext m along the knee->sole direction)"""
    import math as _m
    T._foot()
    if not hasattr(T, "_FOOT0"):
        T._FOOT0 = {k: np.array(v) for k, v in T.FOOT.items()}
    for leg, p in T._FOOT0.items():
        u = np.array([0.0, p[1], p[2]]); u /= np.linalg.norm(u)
        T.FOOT[leg] = p + VARIANT["shin_ext"] * u


def build_xml(kb, mu_desk=0.6, multiccd=True):
    xml = base_xml(mu_desk)
    apply_variant()
    if VARIANT["paw_mu"]:
        for leg in T.LEGS:
            xml = xml.replace(f'mesh="shin_{leg}_paw" ', f'mesh="shin_{leg}_paw" priority="3" friction="{VARIANT["paw_mu"]} 0.005 0.0001" ', 1)
    if VARIANT["shin_ext"]:
        for leg in T.LEGS:
            p = T._FOOT0[leg]; u = np.array([0.0, p[1], p[2]]); u /= np.linalg.norm(u)
            off = VARIANT["shin_ext"] * u
            a = p - np.array([p[0], 0, 0]) * 0 + np.array([0, 0, 0.004]) * 0
            frm = (p[0], p[1] - u[1] * 0.014, p[2] - u[2] * 0.014)                     # inside the old paw/shin
            to = (p[0], p[1] + off[1] - u[1] * 0.009, p[2] + off[2] - u[2] * 0.009)   # inside the moved paw
            strut = (f'          <geom name="shin_{leg}_strut" type="capsule" size="0.004" fromto="{frm[0]:.5f} {frm[1]:.5f} {frm[2]:.5f} '
                     f'{to[0]:.5f} {to[1]:.5f} {to[2]:.5f}" mass="0.001"/>\n')
            xml = xml.replace(f'mesh="shin_{leg}_paw" ', f'mesh="shin_{leg}_paw" pos="0 {off[1]:.5f} {off[2]:.5f}" ', 1)
            xml = xml.replace(f'          <geom name="shin_{leg}_paw"', strut + f'          <geom name="shin_{leg}_paw"', 1)
    if VARIANT["ski"]:
        # paw shape variant: the flat puck (vertical toe face) replaced by two side-by-side capsules ('skis'),
        # radius VARIANT['ski'] (m), 21 mm long, 19 mm wide: same footprint, rounded toe and heel.
        import math as _m
        r = VARIANT["ski"]
        for leg in T.LEGS:
            p = T.FOOT[leg]
            b = _m.radians(T.MAN["pose_rest"]["hip_" + leg] + T.MAN["pose_rest"]["knee_" + leg])
            ax = np.array([0.0, _m.cos(b), -_m.sin(b)]); upv = np.array([0.0, _m.sin(b), _m.cos(b)])
            g = ""
            for dx in (-0.0045, 0.0045):
                c = np.array(p) + r * upv + np.array([dx, 0, 0])
                a0, a1 = c - (0.0105 - r) * ax, c + (0.0105 - r) * ax
                g += (f'          <geom name="shin_{leg}_ski{0 if dx < 0 else 1}" type="capsule" size="{r:.4f}" fromto="{a0[0]:.5f} {a0[1]:.5f} {a0[2]:.5f} '
                      f'{a1[0]:.5f} {a1[1]:.5f} {a1[2]:.5f}" mass="0.0001" contype="2" conaffinity="2" '
                      f'priority="{3 if VARIANT["paw_mu"] else 1}" friction="{VARIANT["paw_mu"] or 0.9} 0.005 0.0001"/>\n')
            import re
            xml = re.sub(f'(<geom name="shin_{leg}_paw"[^>]*?)contype="2" conaffinity="2"', r'\1contype="0" conaffinity="0"', xml, count=1)
            xml = xml.replace(f'          <geom name="shin_{leg}_paw"', g + f'          <geom name="shin_{leg}_paw"', 1)
            import re
            xml = re.sub(f'    <pair geom1="floor" geom2="shin_{leg}_paw"[^>]*/>\n', '', xml)
    if VARIANT["track_add"]:
        import re
        for leg in T.LEGS:
            m = re.search(f'<body name="shin_{leg}" pos="([^"]+)"', xml)
            v = [float(x) for x in m.group(1).split()]
            v[0] += VARIANT["track_add"] * (1 if leg[1] == "l" else -1)
            xml = xml.replace(m.group(0), f'<body name="shin_{leg}" pos="{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}"', 1)
    if VARIANT["pod_scale_y"] != 1.0:
        for leg in T.LEGS:
            xml = xml.replace(f'<mesh name="thigh_{leg}" file="thigh_{leg}.stl"/>',
                              f'<mesh name="thigh_{leg}" file="thigh_{leg}.stl" scale="1 {VARIANT["pod_scale_y"]} 1"/>', 1)
    a, w = kb.mjcf() if kb is not None else ("", "")
    xml = xml.replace("  </asset>\n", a + "  </asset>\n", 1)
    xml = xml.replace('    <body name="body"', w + '    <body name="body"', 1)
    if multiccd:
        xml = xml.replace('integrator="implicitfast" gravity="0 0 -9.81"/>',
                          'integrator="implicitfast" gravity="0 0 -9.81"><flag multiccd="enable"/></option>', 1)
    xml = xml.replace('<size memory="20M"/>', '<size memory="64M"/>')
    return xml


def yaw_quat(psi):
    return (math.cos(psi / 2), 0.0, 0.0, math.sin(psi / 2))


class Run:
    def __init__(self, kb, heading_deg, x0_mm, y0_mm, yaw_jitter_deg=0.0, mu_desk=0.6, target_mm=250.0, record=False):
        self.kb = kb
        self.s = T.Sim(build_xml(kb, mu_desk), record=record)
        self.phi = math.radians(heading_deg)
        psi = self.phi + math.pi / 2 + math.radians(yaw_jitter_deg)
        self.psi0 = psi
        self.hd = np.array([math.cos(self.phi), math.sin(self.phi)])
        self.target = target_mm / 1000.0
        s = self.s
        s.set_pose(T.rest_pose(), base=(x0_mm / 1000, y0_mm / 1000, 0.3) + yaw_quat(psi))
        self.paw_gid = [mujoco.mj_name2id(s.m, mujoco.mjtObj.mjOBJ_GEOM, f"shin_{l}_paw") for l in T.LEGS]
        self.shin_bid = [mujoco.mj_name2id(s.m, mujoco.mjtObj.mjOBJ_BODY, f"shin_{l}") for l in T.LEGS]
        fp = T._foot()
        self.fp = [np.array(fp[l]) for l in T.LEGS]
        self._place()
        self.hip_ids = [s.aid[n] for n in LEG_J["hip"]]
        self.knee_ids = [s.aid[n] for n in LEG_J["knee"]]

    # --------------------------------------------------------------- placement on the terrain
    def paw_world(self, gi):
        s = self.s
        mid = s.m.geom_dataid[gi]
        va, nv = s.m.mesh_vertadr[mid], s.m.mesh_vertnum[mid]
        V = s.m.mesh_vert[va:va + nv]
        return V @ s.d.geom_xmat[gi].reshape(3, 3).T + s.d.geom_xpos[gi]

    def _place(self):
        s = self.s
        mujoco.mj_forward(s.m, s.d)
        lift = -1e9
        for gi in self.paw_gid:
            W = self.paw_world(gi)
            sole = W[W[:, 2] < W[:, 2].min() + 0.0015]
            zt = max((self.kb.surface_z(x * 1000, y * 1000) if self.kb else 0.0) for x, y, _ in sole[::3]) / 1000.0
            lift = max(lift, zt - W[:, 2].min())
        # every other geom must also be above the terrain: check the body/pod hull lowest points vs local terrain
        s.d.qpos[2] += lift + 0.0015
        mujoco.mj_forward(s.m, s.d)
        s.hold(T.rest_pose(), 0.6)
        self.z0 = float(s.d.qpos[2])
        self.h0 = float(s.d.qpos[2] - self.paws()[:, 2].mean())
        self.p0 = s.d.qpos[0:2].copy()

    # --------------------------------------------------------------- run
    def paws(self):
        """sole centres in world (4x3, m)"""
        d = self.s.d
        return np.array([d.xpos[b] + d.xmat[b].reshape(3, 3) @ p for b, p in zip(self.shin_bid, self.fp)])

    def progress(self):
        return float((self.s.d.qpos[0:2] - self.p0) @ self.hd)

    def yaw(self):
        R = self.s.d.xmat[self.s.bid].reshape(3, 3)
        return math.atan2(R[1, 0], R[0, 0])

    def go(self, ctrl, t_max=30.0, warm=0.6, stuck_win=3.0, log_every=0.0):
        s = self.s
        dt = T.DT
        n = int(t_max / dt)
        t0 = s.d.time
        hist = []        # (t, progress, paw xy (4x2))
        win = int(round(0.05 / dt))
        tq_h, tq_k = [], []
        result = None
        minup = 1.0
        maxtilt = 0.0
        lat = []
        trace = []
        for i in range(n):
            t = s.d.time - t0
            tg = ctrl(t, s, self)
            s.step(tg)
            up = s.d.xmat[s.bid][8]
            minup = min(minup, up)
            if t > warm:
                maxtilt = max(maxtilt, math.degrees(math.acos(min(1.0, up))))
                f = s.d.actuator_force
                tq_h.append(np.abs(f[self.hip_ids])); tq_k.append(np.abs(f[self.knee_ids]))
            if i % win == 0:
                PW = self.paws(); pw = PW[:, :2]
                pr = self.progress()
                hist.append((t, pr, pw))
                lat.append(float((s.d.qpos[0:2] - self.p0) @ np.array([-self.hd[1], self.hd[0]])))
                if log_every and (i % int(log_every / dt) == 0):
                    trace.append(dict(t=round(t, 2), prog_mm=round(pr * 1000, 1), lat_mm=round(lat[-1] * 1000, 1),
                                      z_mm=round(float(s.d.qpos[2]) * 1000, 1), up=round(float(up), 3)))
                if up < 0.7 or (s.d.qpos[2] - PW[:, 2].mean()) < self.h0 - 0.025:
                    result = "fell"; break
                if pr >= self.target:
                    result = "success"; break
                if t > warm + stuck_win:
                    k = int(stuck_win / 0.05)
                    old = hist[-k - 1]
                    if pr - old[1] < 0.010:
                        result = "stuck_body"; break
                    seg = np.array([h[2] for h in hist[-k - 1:]])      # (k+1, 4, 2)
                    rngs = np.ptp(seg, axis=0).max(axis=1)             # per paw max xy range
                    if rngs.min() < 0.003:
                        result = "stuck_paw"; break
                # walked off (K1: off the deck onto the desk; K2: paws on the desk)
                if self.kb is not None and t > warm:
                    if PW[:, 2].min() < 0.004:      # any paw down on the desk = walked off the keyboard
                        result = "off"; break
        if result is None: result = "timeout"
        T_ = s.d.time - t0
        th = np.array(tq_h) if tq_h else np.zeros((1, 4)); tk = np.array(tq_k) if tq_k else np.zeros((1, 4))
        out = dict(result=result, t=round(T_, 2), progress_mm=round(self.progress() * 1000, 1),
                   speed_cm_s=round(self.progress() * 100 / max(1e-6, T_ - warm), 2),
                   lat_mm=round(lat[-1] * 1000, 1) if lat else 0.0, lat_max_mm=round(max(abs(v) for v in lat) * 1000, 1) if lat else 0.0,
                   yaw_err_deg=round(math.degrees(_wrap(self.yaw() - self.psi0)), 1),
                   minup=round(float(minup), 3), maxtilt_deg=round(maxtilt, 1),
                   end_xy_mm=[round(float(v) * 1000, 1) for v in s.d.qpos[0:2]],
                   hip=dict(peak=round(float(th.max()), 3), p95=round(float(np.percentile(th, 95)), 3), p99=round(float(np.percentile(th, 99)), 3),
                            sat=round(float((th > 0.195).mean()), 3)),
                   knee=dict(peak=round(float(tk.max()), 3), p95=round(float(np.percentile(tk, 95)), 3), p99=round(float(np.percentile(tk, 99)), 3),
                             sat=round(float((tk > 0.195).mean()), 3)))
        if trace: out["trace"] = trace
        return out


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi
