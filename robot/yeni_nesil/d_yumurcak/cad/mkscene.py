import json, sys, os
# usage: mkscene.py stl_dir out.json state W H views_json [xray]
d, out, state, W, H, views = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
xray = len(sys.argv) > 7 and sys.argv[7] == "xray"
CREAM, ACC, DARK = os.environ.get("CREAMC", "#EFE6D6"), os.environ.get("ACCC", "#FF9F1C"), "#111316"
BEZ = os.environ.get("BEZ", CREAM)
rel = os.path.relpath(d, os.path.dirname(os.path.abspath(out)))
tex = os.path.relpath("tex", os.path.dirname(os.path.abspath(out)))
P = []
def add(f, **k):
    k["file"] = f"{rel}/{f}.stl"; P.append(k)
op = 0.13 if xray else 1.0
add("body_shell", color=CREAM, roughness=0.46, clearcoat=0.25, clearcoatRoughness=0.35, opacity=op, castShadow=not xray, crease=25)
add("head_shell", color=CREAM, roughness=0.46, clearcoat=0.25, clearcoatRoughness=0.35, opacity=op, castShadow=not xray, crease=25)
add("visor", color=DARK, roughness=0.18, clearcoat=1.0, clearcoatRoughness=0.06, opacity=(0.28 if xray else 1.0), crease=15)
if os.path.exists(os.path.join(d, "bezel.stl")) and False:
    add("bezel", color=BEZ, roughness=0.46, clearcoat=0.25, clearcoatRoughness=0.35)
add("lens", color="#15171a", roughness=0.2, clearcoat=1.0)
if os.environ.get("QUIFF","0")=="1":
    add("quiff", color=ACC, roughness=0.5, clearcoat=0.2)
if os.path.exists(os.path.join(d,"cap.stl")) and os.environ.get("CAP","1")=="1":
    add("cap", color=os.environ.get("CAPC", "#FBF6EC"), roughness=0.42, clearcoat=0.3, clearcoatRoughness=0.25, opacity=(0.45 if xray else 1.0), crease=25)
add("haunch", color=ACC, roughness=0.5, clearcoat=0.2, opacity=(0.22 if xray else 1.0), castShadow=not xray)
add("foot", color=ACC, roughness=0.5, clearcoat=0.2)
add("sole", color="#4a4744", roughness=0.85)
for s in (() if xray else ("L", "R")):
    add(f"screen_{s}", image=f"{tex}/eye_{state}_{s}.png", uvAxes=["x", "z"], imageEmissive=1.15, roughness=0.18, clearcoat=1.0, clearcoatRoughness=0.06)
if xray:
    add("int_servo", color="#2b5fb8", roughness=0.5)
    add("int_horn", color="#f5f5f5", roughness=0.5)
    add("int_hservo", color="#2b5fb8", roughness=0.5)
    add("int_cells", color="#3fae5a", roughness=0.4, metalness=0.2)
    add("int_frame", color="#9a9a9a", roughness=0.6)
    add("int_elec", color="#1f7a4a", roughness=0.5)
    add("int_disp", color="#333a44", roughness=0.4)
rot = os.environ.get("ROT")
if rot:
    r = [float(v) for v in rot.split(",")]
    for p in P:
        p["rotation"] = r
sc = {"width": W, "height": H, "background": "#ece8e1", "exposure": 1.0, "shadowOpacity": 0.2, "parts": P, "views": json.loads(views)}
json.dump(sc, open(out, "w"), indent=1)
