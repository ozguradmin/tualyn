# New Kıpır robot: design guide for agents

## Goal (from the user, in Turkish originally)
"Design something Sesame-style, or totally different, maybe never done before, that is cuter, better looking and more advanced, without raising the price much. Quality, useful, moves well. Do your absolute best, like a benchmark. The look matters a lot: I don't want to reject good work just because it looks bad."

The previous plan, "Kıpır Mini 4", was a stock Sesame clone at about 3.5-5k TL. The user found my crude concept render ugly; the real Sesame looks better than that render. The new design must look **premium and adorable** in renders and as a real FDM print.

## Hard constraints
- **Size:** desk-top or phone-sized. Largest dimension ≤ ~150 mm standing. Mass ≤ ~350 g (lighter is better for small servos).
- **Cost:** all parts from Turkish shops in stock now; importing is not viable (~5.7k TL fixed customs fees per parcel).
  - Target total ≤ 5,000 TL including 3D print at a studio (~350-900 TL) and shipping.
  - Parts ideally ≤ ~3,500 TL. The user's absolute max is 10k TL.
  - Verified prices: see `/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/mini/brief.md` and the designs `.../scratchpad/mini/sesame4.json`, `.../scratchpad/mini/otto2.json`.
  - Quick price table (TL, KDV incl.):
    - MG90S 125.80 (Robotistan; inner gears plastic, 180°)
    - SG90 82.25
    - ES08MA II metal 424.20
    - ESP32-S3 N16R8 devkit 610.23 (size ~63-69 x 25.5 mm)
    - Waveshare ESP32-S3 1.47" LCD board with IMU 1,636.20
    - Waveshare ESP32-S3 1.3" 240x240 board with IMU 1,818
    - GC9A01 1.28" round LCD 351.50
    - 1.3" 240x240 ST7789 module 315.12
    - 0.96" OLED 162.73
    - MPU6050 193.53 (Robotistan)
    - INMP441 145.29
    - MAX98357A 309
    - 1 W speaker 51-79
    - 14500 cell 105.48
    - 18650 cell 153.43
    - 1S LiPo 1000 mAh 215.30
    - TP4056 21.77
    - 2S BMS 45.24
    - MP1584 buck 53.22
    - PCA9685 245.54
- **Must:**
  - walks on legs well on a desk (forward/back/turn), with an expressive face
  - an ESP32-S3 with Wi-Fi so it can call the Claude API over HTTPS
  - FDM-printable in PLA/PETG with minimal supports
  - servos, wires and screws hidden or tidy
- **Strongly desired:**
  - gets up by itself after falling over (self-righting)
  - a head that moves, for character
  - two-colour look
  - edge/cliff awareness on a desk
  - touch reaction
  - optional voice: Claude does not do audio, so voice goes via the phone or a PC server
- **Electronics:** only parts that exist in Turkish stock. Prefer few servos (≤ 10). The battery and BMS must physically fit (a previous design failed exactly here).

## Coordinates and units for models
- mm, Z up, robot faces **-Y**, origin at the ground under the body centre.
- The model must sit on the ground (min Z = 0) in its standing pose.

## Tools (verified working in this container)
- **CAD: build123d** (`python3 -I model.py`). OCCT B-rep with fillets, chamfers, shells, lofts.
  - Export each colour/material as a separate STL: `export_stl(part, "name.stl", tolerance=0.03, angular_tolerance=0.08)`.
  - OpenSCAD is also available.
  - Use real fillets and soft, rounded forms; avoid boxy hard edges unless intentional.
- **Renderer:** `node /tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/render/render.js scene.json outdir`
  - It uses Three.js PBR, environment lighting and soft shadows.
  - scene.json format (files relative to the scene.json folder):
    ```json
    {"width":1600,"height":1200,"background":"#efece6","exposure":1.0,
     "parts":[{"file":"shell.stl","color":"#f3eee4","roughness":0.38,"clearcoat":0.35},
              {"file":"legs.stl","color":"#ff8a4c","roughness":0.5},
              {"file":"eye_l.stl","image":"eye.png","uvAxes":["x","-z"],"imageEmissive":0.9,"roughness":0.15,"clearcoat":1}],
     "views":[{"name":"hero","azimuth":30,"elevation":15,"distance":1.0,"fov":28},
              {"name":"front","azimuth":0,"elevation":5}]}
    ```
  - Views:
    - azimuth 0 = from the front, positive = from the robot's right side; elevation in degrees.
    - distance 1.0 frames the whole model; smaller zooms in.
    - Optional "target":[x,y,z] in model mm.
  - Parts:
    - `image` maps a PNG planar onto the part, using bbox-normalised axes from `uvAxes`.
    - Use flat discs or plates for screens with PNG faces drawn by PIL.
    - `imageEmissive` makes the screen glow.
    - Other fields: `opacity`, `transmission`, `metalness`, `sheen`, `crease` (normal smoothing angle, default 40).
  - Render at least: hero (az ~30, el ~15), front (az 0), side (az 90), plus one "in action" pose if relevant.
  - Look at the PNGs yourself (the Read tool shows images) and iterate until it looks genuinely good.
- **Physics:** MuJoCo 3.17 (`import mujoco`) is installed for later gait and self-righting simulation.
- **Read-only references** in `/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/repos/`:
  - sesame-robot (STLs, firmware)
  - OpenCatEsp32 (Petoi self-righting logic)
  - xiaozhi-esp32
  - kame32
  - freenove dog
- **Do not write anything in the git repo `/home/user/tualyn`.** Work only in your own folder under `/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/`.
