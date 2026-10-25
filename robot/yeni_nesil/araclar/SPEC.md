# Robot package spec (for the interactive viewer)

The user wants a browser page (index.html) where they can see all 4 concepts:
- at true relative scale next to a phone, from any angle
- moving: walking, talking, getting up after a fall, happy, sleeping
- **looking the way a real build would look**: FDM-printed plastic with layer lines and part seams, real filament colours, and real screens with their actual resolution behind real bezels or acrylic. Not idealised CG.

They will choose one based on this page, so honesty matters more than glamour.

Every concept is delivered as a **package folder** `/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/paket/<KEY>/`.

## Shared tooling (do not modify)

All of it lives in `/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/render/`.

- `realism.js`: materials.
  - `printMaterial`: matte FDM with layer lines and per-layer tint.
  - `tpuMaterial`, `glossyPetgMaterial`.
  - `acrylicMaterial`: smoked acrylic.
  - `screenMaterial`: native-res LCD with a pixel grid when zoomed, IPS black glow and a round mask.
  - `FILAMENTS`: names and hexes of filament colours sold in Turkey.
- `rig.js`: loads a package (see conventions below). The viewer uses exactly this code.
- `posecheck.js`: renders your package through rig.js exactly as the viewer will show it.
  - Usage: `node /…/render/posecheck.js <packageDir> <shots.json> <outDir>`. See the header of posecheck.js for the shots.json format.
  - It prints the joints, screens and anims it found. **Use it to check every step.** Look at the PNGs with the Read tool.
- `render.js`: the older STL-scene renderer. It also supports `"material":"print"|"tpu"|"petg"|"acrylic"|"screen"` per part.
- Test package for reference: `/…/render/testpkg/`. Its `model.glb` was built with trimesh; see how its nodes are named.

## Package contents

```
paket/<KEY>/
  manifest.json
  model.glb          # all links + meshes, mm, Z up, robot faces -Y, root node = body link
  faces/*.png        # one PNG per screen per expression, at the screen's NATIVE resolution
  anim/*.json        # animations sampled at 30 fps
  stills/*.png       # realistic stills rendered with posecheck (hero, front, side, macro, xray, action)
  sim/               # MuJoCo model + scripts + results (for reproducibility)
  bom.json           # verified BOM (see below)
  NOTES.md           # what was simplified and what is uncertain
```

### model.glb conventions (rig.js depends on these)

- **Units and orientation:** millimetres, Z up, the robot faces **-Y**. In the rest pose the feet touch Z = 0.
- **Node hierarchy:**
  - The root scene node is the **body link**. Name it `body`, and make it the GLB's only top-level node.
  - Each movable link is a node, e.g. `head`, `thigh_fl`, `shin_fl`, `tail`, `wheel_rl`. The node's origin sits **on the joint axis**, and its rest rotation is identity relative to its parent.
  - Joints chain naturally: `body → thigh_fl → shin_fl`.
- **Mesh node names:** `<link>__<matKey>`, e.g. `head__shell`, `head__visor`, `head__screen_eyeL`, `thigh_fl__shell`, `body__internal_battery`.
  - Each `<matKey>` must exist in `manifest.materials`.
  - With trimesh: create link frames with `scene.graph.update(frame_from=parent, frame_to=link, matrix=T)`, then add meshes with `scene.add_geometry(mesh, node_name='link__mat', geom_name='…', parent_node_name=link)`. Export with `scene.export('model.glb')`.
  - Mesh vertices are expressed in the link's local frame (joint at origin).
- **Internals:** servos, ESP32 board, battery, BMS/bucks, speaker, sensors and screens' PCBs are real-size boxes or meshes with matKeys `internal_*` and `"type":"internal"`. They are hidden normally and shown in x-ray mode.
- **Polygon budget:** about 150-300k triangles total per robot. Use `tolerance=0.05, angular_tolerance=0.15` on smooth parts and decimate where needed. The page must stay fast.
- **Seams:** print-split lines that would really exist (shell halves, caps) should be visible as 0.4-0.8 mm reveal grooves in the geometry.

### manifest.json

```json
{
 "key": "B", "name": "Tarçın", "subtitle_tr": "Cep kırmızı pandası", "tagline_tr": "...", "accent": "#e0692b",
 "glb": "model.glb",
 "joints": {"hip_fl": {"node":"thigh_fl","axis":[1,0,0],"min":-20,"max":160,"zero":0,"servo":"MG90S"},
            "wheel_rl": {"node":"wheel_rl","axis":[1,0,0],"continuous":true,"motor":"N20 100rpm"}},
 "materials": {
   "shell":  {"type":"print","color":"#e0692b","filament":"Elas PLA Turuncu","layer":0.16,"layerAxis":[0,0,1]},
   "visor":  {"type":"petg","color":"#141518","filament":"PETG Siyah (parlak, ütülenmiş)"},
   "paw":    {"type":"tpu","color":"#202124","filament":"TPU 95A Siyah"},
   "glass":  {"type":"acrylic","color":"#0b0c0e","opacity":0.6,"note":"2 mm füme akrilik"},
   "screen_eyeL": {"type":"screen","screen":"eyeL"},
   "blush":  {"type":"led","color":"#ff9aa8","intensity":0.8},
   "internal_servo": {"type":"internal","color":"#3b82f6"}
 },
 "screens": {"eyeL": {"res":[240,240],"round":true,"uvAxes":["x","z"],"panel":"GC9A01 1.28in IPS","active_diam_mm":32.4}},
 "faces": {"neutral":{"eyeL":"faces/neutral_L.png","eyeR":"faces/neutral_R.png"}, "blink":{...}, "happy":{...},
           "talk_a":{...}, "talk_b":{...}, "surprised":{...}, "sleepy":{...}, "sad":{...}, "determined":{...}},
 "animations": {"idle":"anim/idle.json","walk":"anim/walk.json","turn":"anim/turn.json","talk":"anim/talk.json",
                "happy":"anim/happy.json","fall_recover":"anim/fall_recover.json","sleep":"anim/sleep.json"},
 "pose_rest": {"hip_fl": 20, "...": 0},
 "specs": {"dims_mm":[120,144,150], "mass_g":368, "servos":10, "motors":0, "brain":"ESP32-S3 ...",
           "battery":"2S 14500 900 mAh", "runtime_walk_min":30, "runtime_idle_h":2.2,
           "walk_speed_cm_s": 0, "self_righting":"...", "sensors":["..."], "voice":"..."},
 "sim_summary": {"walk_speed_cm_s":0, "recovery":"24/24 orientations ...", "notes":"..."},
 "realism_notes_tr": ["Gerçekte katman çizgileri görünür...", "Gözler 240x240, yakından piksel görünür...", "..."]
}
```

- **Joint angle convention:** `node.quaternion = rest * axisAngle(axis, angle - zero)`. The axis is in the node's local frame. Angles are in degrees.
- **pose_rest** is the standing pose used whenever no animation is playing.
- **Faces:**
  - Draw them at **native screen resolution** (e.g. 240×240) with PIL. Use the style a real ESP32 would render (LVGL/TFT_eSPI-like), not a 4K drawing scaled down.
  - The background is pure black.
  - **Required:** neutral, blink, happy, talk_a, talk_b.
  - **Recommended:** surprised, sleepy, sad, determined.
- **colour + filament:** pick real, commonly available filament colours (see `realism.js` `FILAMENTS`, or name a real product line) and keep each hex close to what that filament looks like.

### anim/*.json

```json
{"fps":30, "loop":true, "frames":120,
 "joints":{"hip_fl":[...degrees per frame...], ...},
 "base":[[x_mm,y_mm,z_mm,qw,qx,qy,qz], ...],
 "face":[[0,"neutral"],[45,"blink"],[48,"neutral"]],
 "source":"MuJoCo 3.17, MG90S 0.20 N·m / 600°/s position servos, μ=0.6, mass 368 g",
 "metrics":{"speed_cm_s":3.1}}
```

- **base** is the world pose of the body link at each frame (the same frame as the GLB root node). It is optional for in-place clips.
- **face** is a step list of `[frameIndex, expression]`.

Required clips, all **physically simulated in MuJoCo** where there is physics:

| Clip | Duration | Content |
|---|---|---|
| `idle` | 4-6 s, loop | Breathing or sway plus blinks; may be kinematic but must stay statically stable. |
| `walk` | 6-8 s | Forward walking (wheels or legs). Report the real speed. |
| `turn` | 4-6 s | Turn in place or turn while walking. |
| `talk` | 4-6 s, loop | Head and body gestures plus `talk_a`/`talk_b` face alternation every ~0.15-0.25 s. Kinematic is fine. |
| `happy` | 3-5 s | Its signature happy move (wave, wag, wiggle). |
| `fall_recover` | 5-10 s | Start standing, get knocked or tipped over (apply an impulse or tilt), land, then run the concept's real recovery strategy until standing again, or "ask for help" if the concept cannot recover from that fall. **This must be the MuJoCo result, not hand-animated.** If recovery fails in sim, show the failure honestly and report it. |
| `sleep` | 4 s | Settle down and sleep face. |

**MuJoCo modelling rules:**
- Collision geometry: convex hulls of each link's real meshes, split into a few hulls if concave.
- Masses come from CAD volumes × PLA density (1.24 g/cm³ × infill factor) plus real component masses:
  - MG90S 13.4 g
  - ESP32-S3 devkit about 10 g
  - GC9A01 about 6 g
  - 14500 cell about 20 g
  - N20 about 10 g
- Servos: position actuators with kp tuned so that torque is clamped to **±0.20 N·m** (MG90S at about 5.5 V; SG90 ±0.15). Limit velocity to about 600°/s with joint damping and armature. Joint ranges as in the manifest.
- Contact: floor friction 0.6, plus a second run at 0.4. Wheels as cylinders. TPU feet friction about 0.9.
- Timestep ≤ 2 ms. Record at 30 fps.
- Put the MJCF and scripts in `sim/`. Report success rates.

### bom.json

```json
{"items":[{"part":"MG90S servo","qty":9,"unit_tl":125.80,"line_tl":1132.2,"shop":"Robotistan","url":"https://...","stock":"in stock (qty 520)","checked":"2026-10-25","verified_on_page":true}],
 "print":{"grams":140,"hours":14,"materials":["PLA ...","PETG ...","TPU ..."],"tl_min":600,"tl_max":950,"basis":"..."},
 "shipping_tl":[150,300],
 "tools_tl_if_needed":[0,1000],
 "total_tl":[4500,4900],
 "lean_variant":{"what":"...","total_tl":[4000,4300]}}
```

## Realism checklist (the user explicitly asked for this)

- **Layer lines** must be visible up close.
  - Set `layerAxis` to the real print orientation of each part. For example, a dome printed dome-up has Z layers; a leg printed flat has layers along its thickness.
- **Seams** between printed parts must be visible.
- **Screws:**
  - Show screw heads where they would really be seen.
  - Hidden screws are fine only if the design really hides them.
- **Screens:**
  - Show the real panel at native resolution and the real active area.
  - On a round GC9A01 module the glass is about 35.5 mm with a 32.4 mm active circle; show the dark ring.
  - If the design hides the edge behind acrylic or PETG, show the real darkening and reflection.
- **Glossy parts:**
  - Glossy black on an FDM part only happens with ironing or post-processing; say which.
  - Otherwise use the matte print material.
- **Colours** must be achievable with off-the-shelf filament. Multi-colour prints need either separate parts or an AMS-type printer; note which in `NOTES.md`.
- **Wires:** any wires that would really be visible at joints (e.g. a service loop through the neck) must be modelled.

Never write into the git repo `/home/user/tualyn`. Work only inside your package folder; you may read anything.
