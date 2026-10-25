#!/usr/bin/env python3
"""Procedural keyboard terrains for the Tarcin MuJoCo model (all static geoms in the world body).

Keyboard frame (= world frame): x along the rows (left -> right as the user sees it), y toward the back of the
keyboard (away from the user), z up, origin = front-left corner of the key area, on the desk (z = 0).

K1  laptop / chiclet (15.6" with numpad): deck (laptop base) 8-12 mm above the desk, 15-16 mm square cap tops on a
    19.05 mm pitch (3-4 mm gaps), caps 1.5-2.0 mm proud of the deck, half-height F row, open lid behind the deck.
K2  full-size ANSI mechanical: case/plate 19-22 mm above the desk at the front edge, 4-6 deg tilt (back higher, so
    the back of the plate is ~29-34 mm up), sculpted caps (tapered frusta) on a 19.05 mm pitch, 1u tops 13-14 mm
    (5-6 mm gaps at the top), tops 7-10 mm above the plate, 0-2 mm row-to-row steps, 6.25u space bar, nav-cluster and
    F-row blanks, 0.25u group gaps.
'real'  = one keyboard of the real size.
'field' = the same row pattern repeated 3x front-to-back on one continuous deck/plate (no lid), so a 25 cm path at
          30-45 deg to the rows fits on keys. On K2 the tilt continues (the back of the field is ~3x higher).
"""
import math
import numpy as np

U = 19.05  # mm


def _rng(seed):
    return np.random.default_rng(seed)


# ------------------------------------------------------------------ layouts (width in u; 'g' = blank) ------------
# each row: list of (w_u, kind) with kind 'k' key, 'g' blank (no key, plate/deck visible), 't' = tall key (2 rows,
# the lower half is drawn in the next row as 'c' continuation -> no key there)
K2_ROWS = [  # front (bottom row) to back
    [(1.25, 'k'), (1.25, 'k'), (1.25, 'k'), (6.25, 'k'), (1.25, 'k'), (1.25, 'k'), (1.25, 'k'), (1.25, 'k'),
     (0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (0.25, 'g'), (2, 'k'), (1, 'k'), (1, 'c')],
    [(2.25, 'k')] + [(1, 'k')] * 10 + [(2.75, 'k'), (0.25, 'g'), (1, 'g'), (1, 'k'), (1, 'g'), (0.25, 'g'),
     (1, 'k'), (1, 'k'), (1, 'k'), (1, 't')],
    [(1.75, 'k')] + [(1, 'k')] * 11 + [(2.25, 'k'), (0.25, 'g'), (3, 'g'), (0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (1, 'c')],
    [(1.5, 'k')] + [(1, 'k')] * 12 + [(1.5, 'k'), (0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (0.25, 'g'),
     (1, 'k'), (1, 'k'), (1, 'k'), (1, 't')],
    [(1, 'k')] * 13 + [(2, 'k'), (0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (1, 'k')],
    # F row sits 0.5u behind the number row
    [(1, 'k'), (1, 'g')] + [(1, 'k')] * 4 + [(0.5, 'g')] + [(1, 'k')] * 4 + [(0.5, 'g')] + [(1, 'k')] * 4 +
    [(0.25, 'g'), (1, 'k'), (1, 'k'), (1, 'k'), (0.25, 'g'), (4, 'g')],
]
K2_ROW_Y = [0, 1, 2, 3, 4, 5.5]      # row front edge in u
K2_DEPTH_U = 6.5

K1_ROWS = [  # 15.6" laptop with numpad, 19u wide
    [(1.25, 'k'), (1, 'k'), (1, 'k'), (1.25, 'k'), (5.5, 'k'), (1, 'k'), (1, 'k'), (1, 'k'), (1, 'k'), (1, 'k'),
     (2, 'k'), (1, 'k'), (1, 'c')],
    [(2.25, 'k')] + [(1, 'k')] * 10 + [(1.75, 'k'), (1, 'k')] + [(1, 'k'), (1, 'k'), (1, 'k'), (1, 't')],
    [(1.75, 'k')] + [(1, 'k')] * 11 + [(2.25, 'k')] + [(1, 'k')] * 4,
    [(1.5, 'k')] + [(1, 'k')] * 12 + [(1.5, 'k')] + [(1, 'k')] * 4,
    [(1, 'k')] * 13 + [(2, 'k')] + [(1, 'k')] * 4,
    [(1, 'h')] * 19,                         # half-height F row
]
K1_ROW_Y = [0, 1, 2, 3, 4, 5]
K1_ROW_D = [1, 1, 1, 1, 1, 0.6]          # row pitch in u
K1_DEPTH_U = 5.6


class Keyboard:
    """geoms: list of dicts (type box|mesh, pos (m), quat, size / mesh verts, name)"""

    def __init__(self, kind="K2", variant="real", seed=0, tilt=None, mu=0.4):
        self.kind, self.variant, self.seed, self.mu = kind, variant, seed, mu
        r = _rng(1000 + seed)
        self.geoms = []
        self.meshes = {}
        self.keys = []            # (cx, cy, w, d, ztop) in mm for metrics / placement
        if kind == "K1":
            self._k1(r)
        else:
            self._k2(r, tilt)

    # ---------------------------------------------------------------- K1
    def _k1(self, r):
        self.h_deck = float(r.uniform(8, 12))
        self.proud = float(r.uniform(1.5, 2.0))
        self.gap = float(r.uniform(3.0, 4.0))
        reps = 1 if self.variant == "real" else 3
        W = 19 * U
        D = K1_DEPTH_U * U * reps
        self.key_x = (0.0, W); self.key_y = (0.0, D)
        # laptop base: 8 mm side margins, palm rest 100 mm in front, 14 mm behind the keys to the hinge
        bx0, bx1 = -9.0, W + 9.0
        by0, by1 = -100.0, D + 14.0
        self.base = (bx0, bx1, by0, by1)
        self._box("deck", ((bx0 + bx1) / 2, (by0 + by1) / 2, self.h_deck / 2), ((bx1 - bx0) / 2, (by1 - by0) / 2, self.h_deck / 2))
        top = self.h_deck + self.proud
        for rep in range(reps):
            y_off = rep * K1_DEPTH_U * U
            for ri, row in enumerate(K1_ROWS):
                x = 0.0
                y0 = y_off + K1_ROW_Y[ri] * U
                d = K1_ROW_D[ri] * U
                for w, k in row:
                    wm = w * U
                    if k in ('k', 'h', 't'):
                        dd = d * (2 if k == 't' else 1)
                        yy0 = y0 - (d if k == 't' else 0)
                        cx, cy = x + wm / 2, yy0 + dd / 2
                        sx, sy = wm - self.gap, dd - self.gap
                        zc = (self.h_deck - 1.0 + top) / 2
                        self._box(f"k{rep}_{ri}_{len(self.keys)}", (cx, cy, zc), (sx / 2, sy / 2, (top - self.h_deck + 1.0) / 2))
                        self.keys.append((cx, cy, sx, sy, top))
                    x += wm
        if self.variant == "real":
            # open lid: 6 mm thick panel, hinge at the back of the deck, leaning back 20 deg from vertical
            th = math.radians(20)
            L = 230.0
            hy, hz = by1 + 3.0, self.h_deck + 2.0
            cy = hy + math.sin(th) * L / 2 + 3.0 * math.cos(th)
            cz = hz + math.cos(th) * L / 2
            q = _quat_x(-th)   # rotate the panel about x: top goes to +y
            self._box("lid", (W / 2, cy, cz), ((bx1 - bx0) / 2, 3.0, L / 2), quat=q)
        self.tilt = 0.0
        self.z_top_front = top

    # ---------------------------------------------------------------- K2
    def _k2(self, r, tilt):
        self.tilt = math.radians(tilt if tilt is not None else float(r.uniform(4, 6)))
        self.h0 = float(r.uniform(19, 22))           # plate height at the front edge of the key area
        self.gap = float(r.uniform(5.0, 6.0))        # gap between cap tops
        reps = 1 if self.variant == "real" else 3
        W = 22.5 * U
        D = (K2_DEPTH_U * reps) * U
        self.key_x = (0.0, W); self.key_y = (0.0, D)
        # sculpted profile (OEM-like, randomised): cap height above the plate per row, 7-10 mm, row-to-row
        # sculpt steps 0-2 mm (bottom/Z rows R4, home row R3 lowest, Q row R2, number + F rows R1 tallest).
        # The 4-6 deg plate tilt adds 1.3-2.0 mm per row on top of this.
        nrow = 6 * reps
        hc = []
        for rep in range(reps):
            b = float(r.uniform(8.0, 8.5))
            z = b + float(r.uniform(-0.3, 0.3))
            a = z - float(r.uniform(0.3, 1.0))
            q = a + float(r.uniform(0.3, 1.0))
            n = q + float(r.uniform(1.2, 2.0))
            f = n + float(r.uniform(-0.3, 0.5))
            hc += [min(10.0, max(7.0, v)) for v in (b, z, a, q, n, f)]
        self.row_h = hc
        tn = math.tan(self.tilt)
        # case: wedge, rim 12 mm at the sides/front, 20 mm at the back; top surface = plate plane
        cx0, cx1, cy0, cy1 = -12.0, W + 12.0, -12.0, D + 20.0
        self.base = (cx0, cx1, cy0, cy1)
        zf = self.h0 + cy0 * tn; zb = self.h0 + cy1 * tn
        V = [(cx0, cy0, 0), (cx1, cy0, 0), (cx0, cy1, 0), (cx1, cy1, 0), (cx0, cy0, zf), (cx1, cy0, zf), (cx0, cy1, zb), (cx1, cy1, zb)]
        self._mesh("case", V)
        ct, st_ = math.cos(self.tilt), math.sin(self.tilt)
        q = _quat_x(self.tilt)
        for rep in range(reps):
            for ri, row in enumerate(K2_ROWS):
                gi = rep * 6 + ri
                x = 0.0
                y0 = (rep * K2_DEPTH_U + K2_ROW_Y[ri]) * U
                hcap = hc[gi]
                for w, k in row:
                    wm = w * U
                    if k in ('k', 't'):
                        d = U * (2 if k == 't' else 1)
                        yy0 = y0 - (U if k == 't' else 0)
                        cx, cy = x + wm / 2, yy0 + d / 2
                        bw, bd = wm - 1.0, d - 1.0
                        tw, td = wm - self.gap, d - self.gap
                        # frustum in the plate frame (z along the plate normal), local origin at the plate surface
                        name = f"cap_{w}_{k}_{round(hcap, 2)}_{round(self.gap, 2)}"
                        if name not in self.meshes:
                            self.meshes[name] = [(sx * bw / 2, sy * bd / 2, -0.5) for sx in (-1, 1) for sy in (-1, 1)] + \
                                                [(sx * tw / 2, sy * td / 2, hcap) for sx in (-1, 1) for sy in (-1, 1)]
                        # plate point (cx, cy) on the tilted plate: plate plane passes (y=0, z=h0)
                        pz = self.h0 + cy * tn
                        self.geoms.append(dict(type="mesh", mesh=name, pos=(cx, cy, pz), quat=q, name=f"key{len(self.keys)}"))
                        # top centre in world (approx): shift by the plate normal
                        self.keys.append((cx - 0, cy - hcap * st_, tw, td, pz + hcap * ct))
                    x += wm
        self.z_top_front = self.h0 + hc[0]

    # ---------------------------------------------------------------- helpers
    def _box(self, name, c, h, quat=(1, 0, 0, 0)):
        self.geoms.append(dict(type="box", pos=c, size=h, quat=quat, name=name))

    def _mesh(self, name, V):
        self.meshes[name] = V
        self.geoms.append(dict(type="mesh", mesh=name, pos=(0, 0, 0), quat=(1, 0, 0, 0), name=name))

    def mjcf(self):
        """(asset xml, worldbody xml); all lengths converted mm -> m"""
        a = ""
        for n, V in self.meshes.items():
            vs = " ".join(f"{x / 1000:.6f} {y / 1000:.6f} {z / 1000:.6f}" for x, y, z in V)
            a += f'    <mesh name="kb_{n}" vertex="{vs}"/>\n'
        w = ""
        mu = self.mu
        for g in self.geoms:
            p = " ".join(f"{v / 1000:.6f}" for v in g["pos"])
            q = " ".join(f"{v:.7f}" for v in g["quat"])
            common = (f'friction="{mu} 0.005 0.0001" priority="2" contype="1" conaffinity="3" '
                      f'rgba="{_col(g["name"])}"')
            if g["type"] == "box":
                s = " ".join(f"{v / 1000:.6f}" for v in g["size"])
                w += f'    <geom name="kb_{g["name"]}" type="box" pos="{p}" quat="{q}" size="{s}" {common}/>\n'
            else:
                w += f'    <geom name="kb_{g["name"]}" type="mesh" mesh="kb_{g["mesh"]}" pos="{p}" quat="{q}" {common}/>\n'
        return a, w

    def surface_z(self, x, y):
        """approx terrain top (mm) at (x, y): max of cap tops covering the point, else deck/plate, else desk"""
        z = 0.0
        bx0, bx1, by0, by1 = self.base
        if bx0 <= x <= bx1 and by0 <= y <= by1:
            z = self.h_deck if self.kind == "K1" else self.h0 + y * math.tan(self.tilt)
        for cx, cy, w, d, zt in self.keys:
            if abs(x - cx) <= w / 2 and abs(y - cy) <= d / 2:
                z = max(z, zt)
        return z

    def on_key(self, x, y, margin=2.0):
        """True if (x, y) mm lies on a key top (at least 'margin' inside its edge)"""
        for cx, cy, w, d, zt in self.keys:
            if abs(x - cx) <= w / 2 - margin and abs(y - cy) <= d / 2 - margin:
                return True
        return False

    def info(self):
        d = dict(kind=self.kind, variant=self.variant, seed=self.seed, mu=self.mu, gap_mm=round(self.gap, 2),
                 n_keys=len(self.keys), key_area_mm=[round(self.key_x[1], 1), round(self.key_y[1], 1)])
        if self.kind == "K1":
            d.update(deck_mm=round(self.h_deck, 2), proud_mm=round(self.proud, 2))
        else:
            d.update(tilt_deg=round(math.degrees(self.tilt), 2), plate_front_mm=round(self.h0, 2),
                     cap_h_mm=[round(v, 2) for v in self.row_h[:6]])
        return d


def _quat_x(a):
    return (math.cos(a / 2), math.sin(a / 2), 0.0, 0.0)


def _col(name):
    if name in ("deck", "case"): return "0.25 0.26 0.28 1"
    if name == "lid": return "0.2 0.2 0.22 0.5"
    return "0.12 0.12 0.13 1" if name.startswith("k") else "0.5 0.5 0.5 1"


class Slope(Keyboard):
    """plain tilted plate (no keys), for separating the effect of the K2 tilt from the keys"""
    def __init__(self, tilt_deg=5.0, mu=0.4, h0=20.0):
        self.kind, self.variant, self.seed, self.mu = "slope", "plain", 0, mu
        self.geoms, self.meshes, self.keys = [], {}, []
        self.tilt = math.radians(tilt_deg); self.h0 = h0; self.gap = 0.0
        W, D = 600.0, 400.0
        self.key_x = (0.0, W); self.key_y = (0.0, D); self.base = (-10, W + 10, -10, D + 10)
        tn = math.tan(self.tilt)
        cx0, cx1, cy0, cy1 = self.base
        zf = h0 + cy0 * tn; zb = h0 + cy1 * tn
        V = [(cx0, cy0, 0), (cx1, cy0, 0), (cx0, cy1, 0), (cx1, cy1, 0), (cx0, cy0, zf), (cx1, cy0, zf), (cx0, cy1, zb), (cx1, cy1, zb)]
        self._mesh("case", V)

    def surface_z(self, x, y):
        return self.h0 + y * math.tan(self.tilt)

    def info(self):
        return dict(kind="slope", tilt_deg=round(math.degrees(self.tilt), 2), mu=self.mu)
