# Tarçın (B): package notes

## Review update (2026-10-25): what changed

| Finding | What was done |
|---|---|
| Front hip runs into the head above ~130° | Swept hip_f × neck_pan × knee with the real visible meshes (`sim/hipsweep.py`). The joint max is now **128°** (was 160). The firmware/sim **coupled limit** is a table over neck_pan (`build/limits.json`, also in `manifest.joints.hip_f*.coupled_limit`). The old "head to front pods ≥ 3 mm" claim held only at rest; it is replaced below. `rig_lim_hips_max` is re-rendered at 128°, and `rig_lim_hip_pan_coupled` is new. |
| Hip service loop had no buildable route | Lead route redesigned: a straight thigh-fixed stub through a 2 mm **arc slot** in the body, concentric with the hip, plus a body-fixed slack loop inside. Details below. |
| fall_recover showed only the easy case | New MuJoCo clip **`fall_recover_back`** (on its back, 3 attempts). First-try rates are now reported per landing state. A torque/speed sensitivity run was added (`sim/sensitivity.py`). |
| Servo model had no torque-speed droop | Added back-EMF droop to `sim/tarcin.py`. **All** physical clips and every recovery statistic were re-run with it. Power risk is stated in the user-facing text. |
| Super Mini GPIO budget unverified | Checked against Motorobit's own pinout image: 15 edge GPIO. Body needs 14, head 12. Pin map below. No PCA9685 needed. |
| Contradictions (IMU, speaker, ears, nose, ToF) | One choice each, propagated to the GLB, manifest, BOM and these notes: **MPU6500**; **32 mm speaker**, modelled and fitted; **rigid PLA ears, glued** (no magnets, no pop-off); **black PLA nose + clear varnish**; **ToF in the lower chest**. |
| Minors | Pan-servo load is logged and listed as a risk. playcheck now checks parent-child pairs with the real meshes and runs every clip in one go. Lean-variant total is recomputed with its formula. An orange-colour note was added. A cheek-LED still was added. |

## Rig (model.glb, manifest.json, faces)

Rebuild:
```
cd build
python3 -I -B geom.py
python3 -I faces.py
python3 -I pack.py
python3 -I bom_patch.py
python3 -I manifest_patch.py
```
- `geom.py` imports the concept CAD (`concept_B/model.py`, read-only) and tessellates each link in its own frame. It reads the hip windows from `build/limits.json`.
- `pack.py` mirrors the -x legs and now writes **only** `model.glb` and `pack_info.json`. Pass `--manifest-skeleton` to regenerate the stage-1 manifest and the placeholder idle; that would overwrite the motion-stage content.
- `manifest_patch.py` and `bom_patch.py` apply the review changes. Both are idempotent. The manifest numbers are read from `sim/out`.

### Frames
- mm, Z up, the robot faces -Y.
- Root node `body` has the identity transform, with its origin on the desk under the body centre. The hip axes are at z = 69.05.
- anim `base` is the world pose of `body`. Rest is `[0,0,0,1,0,0,0]`.
- From a MuJoCo torso at hip height: `base = torso_pose * T(0,0,-69.05)`.

| Link | Origin | Joint (axis) | Range (deg) | Rest |
|---|---|---|---|---|
| head | (0,-32,69.05) | neck_pan (+Z) | -40..40 | 0 |
| tail | (0,48,64.05) | tail (+Y) | -85..85 | 0 |
| thigh_fl / thigh_fr | (0,-32,69.05) | hip (+X) | **-20..128**, coupled with neck_pan (below) | 20 |
| thigh_hl / thigh_hr | (0,+32,69.05) | hip (+X) | -50..130 | -20 |
| shin_f* | (0,0,-40) in thigh | knee (+X) | -140..25 | -44 |
| shin_h* | (0,0,-40) in thigh | knee (+X) | -25..140 | 44 |

- Hip angle = thigh angle a, measured from -Z toward +Y. Knee = b - a.
- `l` = +x = the robot's LEFT. The concept/sim "R" is +x, so sim `hip_FR` = `hip_fl`, and so on. The -x legs are mirror copies with the same axis and the same angle signs.
- +neck_pan turns the face toward +x. +tail swings the tip toward +x.

### Front hip vs head: coupled limit (review fix)
`sim/hipsweep.py` sweeps hip_fl over 90..160° in 2° steps, neck_pan over -40..40° in 5° steps, and knee over 12 values from -140 to 25°.

**Method:**
- For each pose, it finds the smallest distance from the leg's visible surface (pod, sock, lead stub, shin and paw; ~20k points, 0.7 mm spacing) to the head's visible surface.
- A leg point inside the head's crown/chin-cap hull or an ear hull counts as negative.
- Raw data: `sim/out/hipsweep.json`.

**Result:** the largest hip angle with ≥ 1 mm clearance for every knee angle. The knee does not matter: the pod or the lead stub always hits first.

| neck_pan (+ = face toward this leg) | -40 | -30 | -20 | -10 | 0 | +10 | +20 | +30 | +40 |
|---|---|---|---|---|---|---|---|---|---|
| hip_fl max | 150 | 146 | 138 | 132 | **128** | 124 | 122 | 118 | **114** |

- hip_fr uses the same table with the pan sign flipped.
- The joint range in the manifest is capped at 128° (the pan-0 value), so the viewer can never show more than 128°. With the head turned toward a leg raised to 128°, the viewer would still show a collision (rig.js cannot couple joints). The note on the joint says so, and `stills/rig_lim_hip_pan_coupled.png` shows the legal pose: 114° at pan +40.
- **The firmware and the sim** (`tarcin.Sim.step`) clamp the hip_f command to `min(table(pan_measured), table(pan_commanded))`.
  - Both recovery sequences command 135-148° on the front hips. These commands are now cut to 114-128°.
  - In the recorded clips the front hips never actually pass 60°, because floor and body contact stop the legs first. So the clamp rarely changes the motion; the drop in first-try rates (below) comes mainly from the droop model.
- At pan 0, the lead stub sets the limit at 128°; without it the pod alone would allow ~134°. At |pan| ≥ 20° the pod itself limits.

### Hip leads: route (review fix)
Each hip carries 6 wires: the hip and knee servo leads, 2 × brown/red/orange, laid side by side as a 6.6 × 1.1 mm flat ribbon.

**Pod side:**
- The lead leaves the pod's inner face (x = 28.6) through a 7.6 × 2 mm slot.
- The exit is at r = 13.6 mm from the hip axis, just outside the r 11 hip collar.
- It sits at 25° from the thigh axis toward the body centre.

**Crossing:**
- It runs straight along -x across the gap, so it is **fixed to the thigh** and turns with it.
- It enters the body through a **2 mm arc slot concentric with the hip axis**. The slot is cut through the body top and belly shells.
- The slot spans the whole joint window plus the ribbon width: front -12°..170°, hind -92°..122° in body angle.
- The stub ends 1.5 mm inside the shell at its deepest point (front x = 11.5, hind x = 8.4; `build/meshes/wire_*.json`).

**Inside the body:**
- A body-fixed slack loop takes up the length change (`body__internal_wire`, x-ray only).
- The entry point travels up to 2 × 13.6 mm relative to the board end. The loop holds ~30 mm in a pocket between the shell and the boards, which are 4 mm apart there.

**What you see:**
- At the shell, the arc slot shows on the belly and flank from below and the front.
- The ribbon shows in the ~8-17 mm gap between pod and body (`stills/rig_macro_hipslot*.png`).
- The wire is no longer a rigid prop sliding through the shell.

**Wire-fatigue risk:**
- The ribbon flexes at the slot lip and in the slack loop on every hip move.
- Self-righting swings the hind hips through up to ~145° (-24 to 121° recorded) and the front hips through ~80° in a fraction of a second, several times per recovery.
- Stock PVC servo leads (28 AWG) can crack after a few thousand such cycles.
- Mitigations:
  - Break the slot lip (0.5 mm chamfer).
  - Keep the bend radius ≥ 3 mm in the slack pocket.
  - Better: re-lead the 8 leg servos with 28 AWG silicone wire.
  - Treat the leads as a wear part. This is in the BOM risks.

### Head interior (review fix: 32 mm speaker)
- **Speaker:** the BOM's Motorobit 8 Ω 1 W 32 × 5 mm speaker is now modelled at that size.
  - It sits on the back wall, centred 2.25 mm below the head centre, behind a 37-hole grille.
  - The front rim is 0.4 mm inside the 1.6 mm wall (analytic check against the head superellipsoid).
  - The back face (y = -24.05) is 3.95 mm behind the head MCU board (y = -28).
  - The old 20 mm cone and the old internal envelope (to y = -15.4) are gone (`build/meshes/speaker_fit.json`).
- **Pan servo:** to make room, the 4 g pan servo body now points **forward** from the pan axis (y -47.5..-27.5).
  - It is 0.5 mm above the neck post, 4 mm below the MCU board, and clear of the eye PCBs (y ≤ -55.8).
  - Before, it pointed back and filled the lower back of the head, where a 32 mm speaker cannot fit.

### What was added to the concept CAD for realism
- **Seams (0.5-0.8 mm reveals):**
  - body top / belly
  - head crown / chin cap
  - muzzle
  - visor pocket
  - pod inner half / outer cap (x = 41)
  - pod / sock
  - tail bands
- **Screws (M2 pan-head, counterbored):**
  - 4 under the belly
  - 2 under the chin cap
  - 1 per pod (body side)
  - 3 per shin
  - 1 on the tail root
- **Eyes:**
  - One 2 mm smoked-acrylic mask plate over a black PLA backer with Ø36 openings.
  - GC9A01: 35.5 mm glass with a black ring around the 32.4 mm active circle. PCB and header are internals.
- **VL53L0X:** a small black IR window in the **lower chest**. The sensor looks down and forward. The BOM line now says the same; concept.md said "nose".
- **USB-C charge port:** moved to the front of the belly, because the hip hub post sits where concept.md put it.
- **Hip arc slots and lead stubs:** see above.

### Materials and print orientation
- **Filaments:** Elas PLA Turuncu `#e0692b`, Elas PLA Krem `#efe4cc`, Elas PLA Siyah `#26272b`, TPU 95A Siyah paws.
- **Nose:** black PLA + 2 coats of clear gloss varnish (`print` material with clearcoat).
  - There is no PETG in this build any more.
  - Ironing is impossible on the curved nose.
- **Ears: rigid orange PLA on a pin, glued with CA.** They do not pop off.
  - The concept's TPU ears and the magnets were dropped, and the magnets are out of the BOM.
  - This matches the sim, which treats the ears as rigid colliders.
  - A hard fall can crack an ear: print with 4 walls.
- **Colours need no AMS:** every colour is a separate part. The ω mouth inlay is the only exception: use AMS, or print it separately and glue it.
- **layerAxis per part:**
  - Z: body top, belly, crown, chin cap, tail, socks, neck
  - X: pods, hubs, shins
  - Y: muzzle, cheeks, backer, mouth
  - Paws: tilted to the sole
  - Ears: approximately Y
- **Pods/socks** use layerStrength 0.38, to avoid moiré at viewer distance.
- **Visor:** light-smoke 2 mm acrylic, opacity 0.32, with screen brightness 1.5.
- **Colour on screen vs the real spool:**
  - Under the shared renderer, Elas PLA Turuncu `#e0692b` renders as a light apricot (`#ee9758`-`#f5a159` on lit faces).
  - The real print is a deeper, more saturated orange. `realism_notes_tr` says so.
  - The eyes look muted grey-teal through the acrylic, which is honest.
- **Cheek LEDs:**
  - Shown lit only in `stills/rig_face_happy_blush.png`, rendered from a temporary manifest copy with `cheek` as an `led` material.
  - rig.js has no per-clip material switch, so the clips show the cheeks off (cream).

### Faces
- Native 240×240, RGB565-quantized, TFT_eSPI style.
- 12 expressions.
- `talk_a` / `talk_b` are an eye pulse; the ω mouth is printed and static.
- Sheet: `stills/rig_faces_sheet_native240.png`.

### Checks (posecheck stills in `stills/rig_*.png`, all re-rendered for this update)
- **Rest bounding box:** 120 × 144 × 150.3 mm. Lowest point z = 0.
- **Triangles:** 236.6k.
- **Clearances:**
  - head to body ≥ 2.0 mm over ±40° pan
  - front pods to head: 4.7 mm at rest. Over the joint range, the real clearance is the coupled table above. There is no fixed number.
  - tail at +85° to the hind pod: 2.3 mm
- **Parent-child pairs** with the real meshes over each full joint range: see "Playback check".

## Electronics: pin budget (review fix)
- **Board:** Motorobit's ESP32-S3 Super Mini (ESP32S3FH4R2).
  - Source: the shop's own pinout image, `dosya.motorobit.com/resim/esp32-s3-super-mini-pinout.jpg`, fetched 2026-10-25.
  - The edge headers carry **GPIO1-13 plus TX (43) and RX (44) = 15 usable pins**.
  - GPIO48 is the on-board RGB LED. More GPIO sit on bottom pads.
  - The "11 GPIO" in the page text undercounts.
  - USB is native (19/20), so UART0 on 43/44 is free. It prints boot messages at reset, so the link protocol needs framing and a checksum.

| Body board (14 of 15) | GPIO |
|---|---|
| Battery ADC (100k/33k divider) | 1 (ADC1) |
| 9 servo PWM (8 leg + tail; LEDC 8 ch + 1 MCPWM) | 2-10 (GPIO3 is a strapping pin, which is fine for an output) |
| I2C SDA/SCL (MPU6500 + VL53L0X) | 11, 12 |
| UART to the head | 43, 44 |
| spare (VL53L0X XSHUT / IMU INT) | 13 |

| Head board (12 of 15) | GPIO |
|---|---|
| GC9A01 ×2: SCK, MOSI, DC, RST shared; CS_L, CS_R; BL (PWM) | 4, 5, 6, 7, 8, 9, 10 |
| Pan servo PWM | 1 |
| PAM8403 input (LEDC PWM + RC filter) | 2 |
| TTP223 | 3 |
| WS2812B cheeks | 11 |
| UART to the body | 43, 44 |
| spare | 12, 13 |

- If a board revision breaks out fewer pins, a PCA9685 (Robotistan 245.54 TL, not counted) frees 9 pins. It is 62 × 25 mm and would need a body layout change.

## Power (review fix)
- The recovery sim assumes every servo gives its full 0.20 N·m on stiff 5.5 V rails.
- **The pack:**
  - Robotistan's only 14500 is the Orion 900 mAh. It has no rating on the page; Direnc lists the same cell as 3C (~2.7 A).
  - The recovery peak is ~4.8 A on the battery side.
  - Each MP1584 bank peaks near its 3 A rating.
- **No stronger pack fits:**
  - The smallest in-stock 2S LiPo ≥ 20C at Robotistan is the Tinylab 850 mAh 40C (847.30 TL, qty 30). It is 59 × 31 × 17 mm and 52 g, against the 50.5 × 14.2 × 28.6 mm bay.
  - JSumo 450 mAh 25C (qty 4) has no listed size.
  - The pack stays, and the risk is in the user-facing text (`specs.battery`, `sim_summary.power_assumption`, `realism_notes_tr`) and in the BOM risks.
- **Failure mode:** a sag or a 5 A BMS trip mid-flip resets the MCU. The robot then lies still until it reboots and retries.
- **Mitigations:**
  - Firmware staggers the kicks: at most 4 servos at full torque at once.
  - 2 × 1000 µF on the servo banks.
  - Brown-out-safe recovery that resumes after a reset.
- **Sensitivity** (see below): at 0.16 N·m the recovery mostly fails. Power is the weakest point of this concept.

## Motion (anim/*.json, sim/)
All clips are 30 fps and replay in rig.js with the GLB frames. `base` is the world pose of `body`.

### MuJoCo model (`sim/tarcin.py`; exported `sim/tarcin_mu0.6.xml` / `tarcin_mu0.4.xml`)
- **Built from `model.glb`:** frames, joint origins, axes, ranges (hip_f now -20..128) and zeros are identical to the rig.
- **Collision:** convex hulls of each link's visible meshes. The lead stubs are excluded. Ears and paws are separate hulls.
- **Mass:** 368 g. Internals are boxes at their GLB positions; the pan servo box moved forward with the GLB change.
- **Servo model (review fix):**
  - MG90S position actuator: kp 3, drive clamped to ±0.20 N·m, command slew 600°/s.
  - **Back-EMF droop:** joint damping = τmax/ω0 + 0.001 = 0.2/11 + 0.001 = 0.0192 N·m·s/rad. So when moving at ω the servo can push only τmax·(1-ω/ω0); it can brake with up to τmax·(1+ω/ω0). No-load speed comes out at ~600°/s.
  - Before the review, damping 0.012 alone gave ~955°/s no-load.
  - Head pan: 4 g micro servo, ±0.07 N·m, ω0 14 rad/s.
  - Firmware coupled hip_f limit, as above.
- **Contact:** desk μ 0.6 (plus a second run at 0.4). Paws μ 0.9 / 0.6. dt 0.5 ms.
- **Pan-gear load logging:** actuator torque + the joint-limit reaction (the limit stop is the servo's own gear train), the external contact torque about the pan axis, and the overshoot beyond ±40°.

### Results (all re-run with the new servo model)
| Clip | How | Result |
|---|---|---|
| walk (7.3 s) | MuJoCo. Trot (0.52 s period, 20 mm stride, 5 mm lift) + IMU levelling | **7.0 cm/s** (was 5.6 with the old servo model). The stronger back-EMF damping calms the leg ringing. Expect ±30 % on hardware. |
| turn (5.4 s) | MuJoCo. In-place trot, ±11 mm differential stride, open loop | 204° in 4.4 s = **46°/s**, 17 mm centre drift |
| fall_recover (7.0 s) | MuJoCo. Finger flick (9 rad/s roll) → side landing → closed-loop recovery | First attempt; standing at t ≈ 5 s. This is the easy case. |
| **fall_recover_back (14.2 s, new)** | MuJoCo. Released upside down 15 mm above the desk (as if a hand turned it over; the roll-180 drop-test start) → closed-loop recovery | Lands on its **back**. Attempt 1 (back sequence) leaves it on its side, attempt 2 (side sequence) rolls it onto its back again, attempt 3 (mirrored back sequence) stands it up at t ≈ 13 s. |
| happy (4.3 s) | MuJoCo. Play bow, bounces, 2 Hz tail wag | min up 0.982 |
| sleep (4.0 s) | MuJoCo. Crouch, fold onto the belly, tail curls | body 18.5 mm lower |
| idle / talk (5 s loops) | Kinematic, feet fixed by IK. Replayed in MuJoCo. | Deviation ≤ 0.5 mm / 0.8°. Peak torque 0.04 / 0.07 N·m. |

- How a flick lands: a flick from standing about the long axis always lands Tarçın on its side (the pods prop it). Tested at 9-24 rad/s and with an external roll torque.
- A pitch flick tips it onto its nose or tail.
- Only a hand turning it over puts it on its back.

### Self-righting (`sim/recover2.py`, `sim/validate_rc.py`; results in `sim/out/rec2_*.json`)
- **The controller follows the concept's strategy:** tail lever plus leg kicks, OpenCat-'rc' style, closed loop on the IMU gravity vector.
  - On its back: the concept's `best_seq_13`, mirrored on every second try.
  - On a side: the side sequence re-tuned on this model (`rc_side.json`), never mirrored.
  - Up to 4 tries, with 1.3 s in the stand pose between them.

| Set (only falls that really fell) | μ 0.6 recovered | μ 0.6 first try | μ 0.4 recovered | μ 0.4 first try |
|---|---|---|---|---|
| Concept's 24 orientations (23 fall) | 23/23 | 13/23 | 23/23 | 15/23 |
| Hold-out: 24 random + 8 pushes (30 fall) | 30/30 | 21/30 | **29/30** | 19/30 |
| Hold-out at +10 % mass | 30/30 | 17/30 | – | – |

**First try by landing state** (both sets together):

| | μ 0.6 | μ 0.4 |
|---|---|---|
| **Side** | **30/39** first try, 39/39 recovered | 30/38 first try, 37/38 recovered |
| **Back** | **4/14** first try, 14/14 recovered | 4/15 first try, 15/15 recovered |

- Back landings usually need 2-3 attempts at ~3.8 s each.
- Worst successful case: 4 attempts, ~17.6 s (μ 0.4, or +10 % mass).
- The failure: μ 0.4 hold-out, drop roll -95.3°/pitch 24.2°, a side landing. Not up after 4 tries, so the firmware gives up and asks for help (sad eyes + chirp).

**Torque and speed sensitivity** (`sim/sensitivity.py`; concept's 23 falls, μ 0.6, up to 4 tries; `sim/out/sens_*.json`):

| Servo | Recovered | First try | Side first / ok | Back first / ok |
|---|---|---|---|---|
| 0.20 N·m, 600°/s (nominal) | 23/23 | 13/23 | 11/15 · 15/15 | 2/8 · 8/8 |
| **0.16 N·m** (sagging pack; ω0 scales with the voltage, back-EMF damping kept) | **15/23** | 1/23 | 0/15 · 9/15 | 1/8 · 6/8 |
| **450°/s** servos (slew and ω0 × 0.75) | 22/23 | 1/23 | 0/15 · 14/15 | 1/8 · 8/8 |

- **What this means:** the keyframes have almost no torque or speed margin.
  - The side sequence's first try depends on the full 0.20 N·m at 600°/s.
  - With a sagging pack, a third of the falls are not recovered within 4 tries.
  - The reviewer's run on the old servo model (23/23 at 0.16 N·m) did not include droop or the hip-head limit; both cut the margin.
  - Re-tuning the sequences for 0.16 N·m / 450°/s is listed under "What remains".
- **Head-pan load:**
  - Falls back-drive the 76 g head into the 4 g servo's end stop.
  - Peak gear load is **≈0.47 N·m**, against the servo's 0.07 N·m.
  - neck_pan overshoots ±40° by up to **4.6°**. rig.js clamps the display at 40°.
  - Gear stripping is likely after repeated falls. Keep spare servos, or add an O-ring slip coupling at the horn (BOM risks).
  - An MG90S does not fit next to the 32 mm speaker and the eye PCBs.
  - Per-case values: `pan_gear_peak_Nm` / `pan_overshoot_deg` in `sim/out/rec2_*.json`.

**Honest failures and caveats:**
- The recovery sequences were tuned before the droop model and the coupled hip limit. With both (mostly the droop), first-try rates fell (concept set at μ 0.6: 19 → 13 of 23), and one μ 0.4 case now fails.
- The concept's own single sequence recovered only 8/24 on this model (old servo model, `sim/out/recovery_mu0.6_rigid.json`). That is why the side sequence was re-tuned.
- The sequences were tuned in this same simulator. Outcomes are chaotic: a 0.03° change in drop angle can change the attempt count.
- Convex hulls, ideal rails, and rigid ears and leads limit fidelity. Expect to re-tune on hardware.
- Idle and talk are kinematic. They were checked for static stability only.

### Playback check (`sim/playcheck.py`, all clips in one run → `sim/out/playcheck.json`)
- **Desk contact:** the lowest visible vertex is -1.1 … +1.3 mm in every clip. The exceptions are a 1-frame bounce in fall_recover, and the 15 mm release at frame 0 of fall_recover_back (9.8 mm, by design).
- **Sibling links** (MuJoCo hulls): ≤ 0.44 mm interpenetration.
- **Parent-child pairs with the real meshes** (new). The minimum clearance over each full joint range is:

| Pair | Clearance |
|---|---|
| head-body (pan) | 0.95 mm |
| thigh-body (hip; the hub post in its collar is excluded) | 0.23 mm, the lead stub in its 2 mm slot |
| shin-thigh (knee) | 0.20 mm, the shin plate beside the knee collar |
| tail-body | 0.03 mm |

  - These are constant running gaps, not angle-dependent collisions. The tail root rides against the rump almost touching: a real print needs ~0.3 mm there.
  - The check is unsigned: a crossing would read ~0.
- **Head vs front legs (real meshes):** no clip lifts a front hip above 90°, because floor and body contact limit the legs during recovery. The coupled table therefore only matters for commanded poses and the viewer.
- **neck_pan overshoot:** fall_recover reaches 44° and fall_recover_back reaches -43/44°, against the ±40° range. rig.js clamps the display, and playcheck uses the clamped values. The overshoot is reported in each clip's metrics.

Reproduce, from `sim/`:
- Clips: `python3 clips.py idle talk walk turn happy sleep fall_recover fall_recover_back`
- Recovery: `python3 recover2.py 0.6 rc_side.json`, `python3 validate_rc.py 0.6` (plus 0.4, and `0.6 1.1`)
- Sensitivity: `python3 sensitivity.py tau0.16 v450`
- Hip-head sweep: `python3 hipsweep.py [pans...]`
- Playback check: `python3 playcheck.py`
- Strips: `python3 strips.py <clips>`

## What remains uncertain or simplified
- **Internals** are envelope boxes and cylinders. The slack loop is one representative rest shape and does not deform with the hip.
- **Hip-head coupling:** the viewer cannot couple joints. A viewer user can pose hip 128° with pan +40° and see a collision that firmware would forbid.
- **Recovery margin:** the sequences need re-tuning for weaker servos, ideally as a robust search over 0.16-0.20 N·m and 450-600°/s. The weak 14500 pack makes this the main hardware risk.
- **Walk speed** rose to 7.0 cm/s with the droop model. The gait was not re-tuned. The open-loop bistability noted before (lean into a ~2 cm/s shuffle) was seen with the old model and was not re-checked.
- **Cheek LEDs** are shown lit in one still only.
