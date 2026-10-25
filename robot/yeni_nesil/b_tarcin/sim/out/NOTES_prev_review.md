# Tarçın (B): package notes

## Rig (model.glb, manifest.json, faces, anim/idle.json)

Rebuild: `cd build && python3 -I -B geom.py && python3 -I faces.py && python3 -I pack.py`.
- `geom.py` imports the concept CAD (`concept_B/model.py`, read-only) and tessellates each link in its own frame.
- `pack.py` mirrors the -x legs and writes `model.glb`, `manifest.json` and `anim/idle.json`.

### Frames (needed by the motion stage)
- **Units and orientation:** mm, Z up, robot faces -Y.
- **Root node `body`:**
  - The transform is identity. The origin is on the desk under the body centre.
  - The hip axes are at z = 69.05.
  - The anim `base` is the world pose of this node, so the rest pose is `[0,0,0,1,0,0,0]`.
  - Conversion from a MuJoCo torso placed at hip height: `base = torso_pose * T(0,0,-69.05)`.
- **Link origins** (relative to `body`, all rest rotations identity):

| Link | Origin | Joint (axis) | Range (deg) | Rest |
|---|---|---|---|---|
| head | (0,-32,69.05) | neck_pan (+Z) | -40..40 | 0 |
| tail | (0,48,64.05) | tail (+Y) | -85..85 | 0 |
| thigh_fl / thigh_fr | (0,-32,69.05) | hip (+X) | -20..160 | 20 |
| thigh_hl / thigh_hr | (0,+32,69.05) | hip (+X) | -50..130 | -20 |
| shin_f* | (0,0,-40) in thigh | knee (+X) | -140..25 | -44 |
| shin_h* | (0,0,-40) in thigh | knee (+X) | -25..140 | 44 |

- **Hip and knee angles:** hip = thigh angle a, measured from -Z toward +Y. knee = b - a, where b is the absolute shin angle. This is the same convention as `concept_B/model.py` and `concept_B/sim`.
- **Sides are anatomical:** `l` = +x = the robot's LEFT. The concept and its sim call +x "R".
  - sim `hip_FR` = `hip_fl`
  - sim `hip_FL` = `hip_fr`
  - sim `hip_HR` = `hip_hl`
  - sim `hip_HL` = `hip_hr` (and the same for the knees)
- **The -x legs are mirror copies.** They use the same +X axis and the same angle signs.
- **Positive angles:**
  - +neck_pan turns the face toward +x.
  - +tail swings the tip toward +x.

### What was added to the concept CAD for realism
- **Seams (0.5-0.8 mm reveals):**
  - body top / belly (concept)
  - head crown / chin cap (new: z = head centre - 17; the cap carries the neck opening)
  - muzzle part (concept)
  - visor pocket (concept)
  - pod inner half / outer cap (new: vertical split at x = 41)
  - pod / black sock (concept)
  - tail bands (concept)
- **Screws (M2 pan-head, counterbored):**
  - 4 under the belly
  - 2 under the head's chin cap
  - 1 per pod on the body-facing side
  - 3 per shin: knee horn centre screw plus 2 horn screws
  - 1 on the back of the tail root, along the servo axis
- **Eyes:**
  - The concept's mask outline is one 2 mm smoked-acrylic plate with no holes.
  - Behind it sits a black PLA backer with Ø36 openings.
  - Each GC9A01 has 35.5 mm glass with a black ring around the 32.4 mm active circle (the 240×240 screen surface). The PCB (Ø38) and header are modelled as internals.
- **Speaker:** a 20 mm speaker sits directly behind a 19-hole grille on the back of the head.
- **VL53L0X:** a small black IR window in the lower chest. The sensor looks down and forward.
- **USB-C charge port: moved to the front of the belly.**
  - concept.md puts it on the right flank, but the hip hub post occupies that spot.
  - The charger board is moved to match.
- **Hip service loops:** 2 flat 3-wire servo leads per hip (brown/red/orange), running from the pod into the body flank.
  - The loop is rigidly attached to the thigh, so at extreme hip angles the body end slides along the flank surface.
  - A real loop flexes instead.

### Materials and print orientation
- **Filaments:** Elas PLA Turuncu `#e0692b`, Elas PLA Krem `#efe4cc`, Elas PLA Siyah `#26272b`, TPU 95A Siyah paws, PETG Siyah nose.
  - The concept's `#DF6E35` / `#F3EEE4` / `#2A2C31` were snapped to real filament colours.
  - Cream PLA is yellower than the concept render.
- **Ears: matte PLA with magnets.** The concept said TPU, but orange TPU is not a common stock colour.
  - Rigid PLA ears will collide in falls, while the concept sim treats the ears as soft.
  - The magnets let the ears pop off on impact.
- **Colours need no AMS:** every colour is a separate part. The only exception is the ω mouth inlay: use an AMS-type printer, or print it as a separate part and glue it in.
- **layerAxis per part:**
  - Z: body top, belly, head crown, chin cap, tail, socks, neck
  - X: pod halves (split face on the bed), hub posts, shins
  - Y: muzzle (face on the bed), cheeks, backer, mouth
  - Tilted to the sole plane: paws
  - Approximately Y: ears
- **Pod and sock layerStrength is 0.38.** At full strength the shared shader showed moiré blotches at viewer distance. The lines are still visible in macro shots.
- **Visor: light-smoke 2 mm acrylic, about 65-70 % transmission** (`opacity` 0.32), with screen brightness 1.5.
  - Darker smoke turned the eyes grey once the ACES tone-mapped screen was blended under the acrylic.
  - The glossy acrylic still lays a grey room reflection over the eyes. That is honest for a bright room.

### Faces
- **Format:** native 240×240, RGB565-quantized, drawn TFT_eSPI-style.
  - Anti-aliased flat shapes, a 2-colour gradient, a 2-step dim outline instead of a blur glow, and a 2-dot sparkle.
- **Expressions:** neutral, blink, happy, talk_a, talk_b, surprised, sleepy, sleep, sad, determined, curious, love.
  - `talk_a` / `talk_b` are an eye pulse. The ω mouth is printed and static.
- **Sheet:** `stills/rig_faces_sheet_native240.png`.

### Checks done (posecheck stills in `stills/rig_*.png`)
- **Rest bounding box:** 120 × 144 × 150.3 mm, the same as the concept. Lowest point z = 0 (paws).
- **Triangles:** about 228k.
- **Clearances** (vertex distance, approximate):
  - head to body ≥ 2.0 mm over ±40° pan
  - head to front pods ≥ 3 mm
  - tail at +85° to hind pod: 2.3 mm (0.8 mm if that hind hip is at +30°)
- **Joint-limit poses:** `rig_lim_*`.
- **Idle placeholder:** a kinematic 2 s loop that keeps the paws under the hips (`rig_idle_*`).

### Uncertain or simplified
- Internals are envelope boxes and cylinders.
- Hip collars and hub posts follow the concept geometry. Horn screws inside the hub are hidden.
- Wire loops are rigid meshes.
- The cheek LEDs are shown off (cream).

## Motion (anim/*.json, sim/)

All clips are 30 fps and replay in rig.js with the GLB frames. The `base` of each frame is the world pose of the `body` node.

### MuJoCo model (`sim/tarcin.py`, exported to `sim/tarcin_mu0.6.xml` / `tarcin_mu0.4.xml`)
- **Built from `model.glb` itself.** Link frames, joint origins, axes, ranges and zeros are identical to the rig: the `body` freejoint origin is on the desk, and the hips are at z = 69.05.
- **Collision:** convex hulls of each link's visible meshes.
  - The rigid PLA ears are separate hulls and do collide.
  - The paws are separate TPU hulls.
- **Mass:** 368 g, from the CAD mass budget. Servos, cells, screens and boards are placed as boxes at their GLB positions.
- **Servos:**
  - MG90S position actuator: kp 3, ±0.20 N·m clamp, 600°/s command slew, damping 0.012, armature 0.0004.
  - Head pan: 4 g micro servo (E-Sky 002279) at ±0.07 N·m.
- **Contact:**
  - Desk μ 0.6, plus a second run at 0.4.
  - Paws μ 0.9 on the 0.6 desk and 0.6 on the 0.4 desk.
  - dt 0.5 ms.

### Results
| Clip | How | Result |
|---|---|---|
| walk (7.3 s) | MuJoCo. Trot (period 0.52 s, stride 20 mm, lift 5 mm) from IK foot paths, plus an IMU levelling loop (PI on roll/pitch → per-leg foot height) | **5.6 cm/s** in the clip at μ 0.6. Steady state ≈ 6.2 cm/s (μ 0.6) and ≈ 6.6 cm/s (μ 0.4). Servos sit at the 0.20 N·m limit about 3 % of the time. |
| turn (5.4 s) | MuJoCo. Trot in place with ±11 mm differential stride, open loop | 199° in 4.4 s = **45°/s**, centre drift 5 mm. At μ 0.4 ≈ 40°/s. Drift is 5-40 mm depending on the run. |
| fall_recover (7.0 s) | MuJoCo. Finger flick at t = 0.9 s (9 rad/s roll), lands on its side, closed-loop recovery | Recovers on the first attempt and is standing at t ≈ 5 s. |
| happy (4.3 s) | MuJoCo. Play bow, bounces, tail wag (2 Hz, ±45° command; the servo slew limits the real amplitude) | min up 0.984. Statically stable. |
| sleep (4.0 s) | MuJoCo. Crouches with IK, folds onto the belly, tail curls to the side | Body ends 18.5 mm lower, lying on the belly and socks. |
| idle / talk (5 s loops) | Kinematic. Feet are fixed by IK and the body sways sagittally only. Replayed in MuJoCo as a check. | Base deviation ≤ 0.6 mm and ≤ 0.9°, no drift, peak torque 0.08 N·m. talk_a/talk_b alternate every 0.17-0.23 s, with 2 pauses. |

**Self-righting** (`sim/recover2.py`; results in `sim/out/rec2_*.json`):
- **The controller follows the concept's strategy:** tail lever plus leg kicks, OpenCat-'rc' style, closed loop on the IMU gravity vector.
  - On its **back**, it plays the concept's `best_seq_13` unchanged and mirrors it on every second try.
  - On a **side**, it plays a side sequence re-tuned on this model (`sim/rc_side.json`). The down-side legs swing up and back so the pods stop propping the body, the tail slams toward the floor, then the robot tucks and stands. It is never mirrored on a side: the IMU says which side is down, and mirroring only rolled it the wrong way.
  - It retries up to 4 times, with 1.3 s in the stand pose between attempts.

| Set | μ 0.6 | μ 0.4 |
|---|---|---|
| Concept's 24 drop orientations (`recover.orients()`, 23 actually fall) | 23/23 (19 first try) | 23/23 (22 first try) |
| Hold-out: 24 new random orientations + 8 pushes (30 fall) | 30/30 (25 first try) | 30/30 (27 first try) |
| Hold-out at +10 % mass | 30/30 (27 first try) | — |

- Each attempt takes about 2.5 s. The worst case, 4 attempts, took 16.5 s.
- Every recovery saturates servos at 0.20 N·m (stall) for short moments. That is the battery peak noted in the BOM.

**Honest failures and caveats:**
- **The concept's single sequence does not transfer.** Replayed open-loop on this package model, with OpenCat mirroring, it recovered only **8/24** at μ 0.6 (`sim/out/recovery_mu0.6_rigid.json`). It failed almost every side fall.
  - Ablations (`sim/ablate*.py`) show this is sensitivity to small model changes, not one design flaw. The relevant changes are rigid ears, a 14 g tail instead of 8 g, and a 0.07 N·m head servo instead of 0.2.
  - With all of the concept's assumptions put back, the concept sequence still recovered only 3 of 8 test cases on a single try.
  - A random search on this model found working side sequences within about 12 trials. The final side sequence was then refined by ES on randomised side drops.
- **The side sequence was tuned in this same simulator.** The hold-out orientations differ, but the model is the same.
  - Outcomes are chaotic: changing a drop angle by 0.03° can change the number of attempts.
  - Read the rates as "almost always gets up within 4 tries in sim". They are not a guarantee for a real build.
  - Convex hulls, ideal servos and rigid parts are the main fidelity limits. Expect to re-tune the keyframes on hardware.
- **The open-loop trot is bistable.** Undisturbed it does 7.8 cm/s. After a small nudge, or from the tail sway alone, it settles into a 6° lean and a ≈ 2 cm/s shuffle.
  - The walk clip therefore uses IMU levelling, which costs some speed.
  - Levelling made in-place turning worse (−40 % yaw rate), so turn is open loop.
- **Kinematic clips do not prove torque or contact.** idle and talk are kinematic. They were checked for static stability in MuJoCo only.
- **Rig-side limitation:** the hip service-loop wire meshes are rigid, so in the fall clip they slide along the flank instead of flexing.

### Playback check
- **`sim/playcheck.py`** uses the same FK as rig.js over every frame.
  - Lowest visible vertex: −1.0 … +1.2 mm in all clips. The only floating frames are a 2-frame bounce in the fall.
  - Link-to-link interpenetration is ≤ 0.26 mm.
- **Strips:** `stills/anim_*.png` come from posecheck with a fixed camera. `sim/fixcam.py` cancels pose.html's bounding-box-dependent zoom.

Reproduce, from `sim/`:
- Clips: `python3 clips.py`
- Recovery stats: `python3 recover2.py 0.6 rc_side.json` and `python3 validate_rc.py 0.6`
- Strips: `python3 strips.py walk turn ...`
- Playback check: `python3 playcheck.py`
