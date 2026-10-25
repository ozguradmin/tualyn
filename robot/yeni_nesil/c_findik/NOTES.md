# Package C: Fındık (wheel-pawed roly-poly hamster)

## Review fixes (2026-10-25)

- **Self-righting headline** now uses the recommended **hybrid** firmware: 18/18 at the sim CoM, 17/18 at the concept's own CoM (+1.6 mm), 17/18 at +3.5 mm.
  The concept's own 60°/0.3 s rule is reported next to it: 16/18 at the sim CoM, but only **9/17 at the concept CoM** and 4/18 at +3.5 mm.
  `fall.py` now runs a CoM sweep (0/1/1.6/2.5/3.5 mm) for both firmwares. `fall_recover` is re-simulated with the hybrid firmware.
- **Joint limits** come from a new arm-vs-shell sweep (`sim/check_arm_shell.py`, a winding-number point-in-mesh test of the shell skin against the posed arm, boot and N20 sleeve):
  front **5…82°** (clear from 4°), rear **5…118°** (clear 3…119°). The old −5/−12/122° limits went 1.6-4 mm into the shell.
  The happy lean was redesigned and re-simulated: FR 40°, RL 8°, RR 65°.
  The tuck uses rear 118° instead of 120°.
- **Battery:** a printed 53.6 mm bay with contacts salvaged from the 2×AA holder (the holder itself does not fit). The cells were raised 1.4 mm and centred between the hip servos.
- **Wires:** the rear N20 pair now enters the body on the hip axis through the horn-boss hole, so it only orbits and twists there; no arc slot is needed.
- **BOM:** print materials match the manifest; magnets are Ø6×1.5 everywhere; the front axle is an M3×12 screw plus a printed PETG sleeve.
- **Colour:** the caramel render albedo was lowered so lit areas land near the real swatch.
- **Checks:** `verify_replay.py` now parses the MJCF and asserts it matches the GLB, and checks every clip frame against the arm-vs-shell table.
- **Strip:** the follow-cam walk strip keeps the grid and shadow under the robot.

## Rig (model.glb, manifest.json, faces/)

**Rebuild.** All of it is reproducible from `src/`:
- `src/model_base.py` is derived from `concept_C2/model.py` lines 1-320 (the shell, the two-tone split, the visor, the screens and the ears). Only the material keys were renamed, plus the two changes below.
- `python3 -I src/build_rig.py` builds the legs per link and the internals and visible extras, then writes `model.glb` and `src/rig_info.json`. It takes about 1 min.
- `python3 -I src/faces.py` writes `faces/*.png` and `stills/faces_sheet.png`.
- `python3 -I src/make_manifest.py` writes `manifest.json` and the placeholder `anim/idle.json`. It keeps any `animations`, `specs` and `sim_summary` that a later phase has already written.
- `node render/posecheck.js paket/C src/shots_final.json paket/C/stills` re-renders the stills.

**Links and joints:**
- `body` is the root and only top-level node. Its origin is on the floor under the egg centre, so the egg bottom sits at Z = 14.52 at rest.
- `leg_fl`, `leg_fr`, `leg_rl` and `leg_rr` each hang on one MG90S hip-pitch joint. The origin is on the spline axis at x = ±31, y = −15.5 (front) or +21.5 (rear), z = 46.52. Each link carries the arm, the boot, the horn screw and the horn; the rear links also carry the N20 and its wires.
- `wheel_*` are children of the legs, with the origin on the axle (34 mm below the hip, x = ±37.8).
- Joint angle 0 means the arm points straight down. A positive angle moves the wheel away from the body centre, so the front axis is [−1,0,0] and the rear axis is [1,0,0]. `pose_rest` is 22° on all four hips, which matches the concept's stand pose; in it the tyres touch Z = 0.
- **Limits: front 5…82°, rear 5…118°.** They come from `sim/check_arm_shell.py` (→ `sim/results/arm_shell_sweep.json`), not from the concept.
  - The concept's limits (front −5…82°, rear −12…122°) are not reachable.
    - Front below 4°: the arm enters the cream shell (0.6 mm at 0°, 1.6 mm at −5°).
    - Rear below 3°: the inboard N20 boot sleeve enters the belly (0.7 mm at 0°, 2.2 mm at −5°, 4.0 mm at −12°).
    - Rear above 119°: the arm grazes the cap (0.1 mm at 120°, 0.7 mm at 122°).
  - The new limits keep a 1-2° margin.
  - Inside them, the front and rear tyres cannot touch, so the old coupled-limit rule is gone. `stills/check_limit_min_coupled.png` shows all four hips at 5°.
  - The socket reliefs in the CAD are still cut for the concept sweep (`LEG_RANGE` in `model_base.py`), which is larger than needed and harmless.
- Wheels are continuous joints about [1,0,0], where + rolls forward. The front wheels roll freely; the rear wheels are driven by the N20s.

**Size.** About 194k triangles (189k visible); the GLB is 5.1 MB.
- Only the egg skins (`cream`, `cap`, `visor`) carry normals. Their outer surface uses exact analytic egg normals, so the glossy visor shows no facet shimmer.
- All other meshes have no normals, and rig.js computes 40° crease normals for them.

## Changes and additions compared with the concept CAD (realism)

- **Chin cliff-sensor slots** are widened from 6.6×4 to 11.2×6.2 mm. A TCRT5000 lens pair is 10.2 mm wide, so the concept window could not show it. The black TCRT body is now visible in each slot, with its blue-tinted emitter and black detector lenses.
- **USB-C:** the concept's black printed insert, which had a 6.8×1.4 slot that no plug would fit, is replaced by a real 8.94×3.26 receptacle (metal shell plus tongue). It sits 0.4 mm behind the 9.4×3.6 opening.
- **Screws that would really be seen:**
  - one M2 pan-head horn screw per hip, in a Ø4.7 counterbore on the arm's outer face (the horn is embedded in the arm, so the screw has to go in from outside)
  - two M2 countersunk screws under the belly, into the battery-tray bosses
  - The cap is held by magnets and the front axle screws are under the hubcaps, so those stay hidden.
- **Rear N20 wires:**
  - A red and black 28 AWG pair runs in a groove on the inner face of each rear arm, up to 4.6 mm from the hip axis.
  - There it turns inward through the Ø12.6 horn-boss hole of the socket cup. Because the wires cross into the body on the hip axis, a 113° sweep only makes them orbit 4.6 mm around the axis inside the hole and twist. No arc slot is needed.
  - A ~4 cm service loop inside the body is assumed and is not modelled.
  - The concept never routed these wires; this route is an addition.
- **Grille:** black speaker cloth is visible behind the grille holes.
- **Internals (x-ray only):**
  - 4 MG90S, horns, 2 N20, axles
  - 2×14500 cells (Ø14.5×50.5) in a printed bay, 53.6 mm inside, with spring and plate contacts taken from the BOM's 2×AA holder.
    - The holder itself (~57 mm) does not fit the belly.
    - The cells were raised 1.4 mm and moved to y = 3.0, between the hip servos.
    - Clearance to the inner shell: 0.44 mm (cells) and 0.93 mm (9×9 contacts). Clearance to the MG90S case bottoms: 0.8 mm. `build_rig.py` prints this check.
    - No tabbed 14500 cells or ready 2S 14500 pack were found in stock at Direnc or Robotistan.
  - ESP32-S3 devkit (PCB, module can and USB-C)
  - GC9A01 PCBs and LCD stacks, speaker, bucks, BMS, amp, mic, IMU, DRV8833, charger, TCRT boards
  - WS2812B cheek LEDs, cap magnets (4 pairs of Ø6×1.5), inner chassis

## Materials and print orientation (layerAxis)

| Part | Filament | Layer axis | Why |
|---|---|---|---|
| Lower body | matte ivory/cream PLA, 0.12 mm | split-plane normal (0, 0.386, 0.922) | printed split face down, so the layers run parallel to the 23° tilted seam |
| Cap | Bambu Lab PLA Matte Caramel | same | same |
| Ears | caramel shell + cream insert | ear normal (0, 0.985, −0.174) | printed flat |
| Visor, nose | black PETG | Y | outer face up; gloss needs sanding plus 2K clear |
| Front-axle sleeves | PETG, any colour | sleeve axis | Ø3.2/Ø5.0×6.6 mm bushing. The M3×12 screw clamps it to the boot and the hub turns on it, not on the thread |
| Arms (with boots), hubs, hubcaps, toe-beans | PLA, 0.16 mm | X | flat on the hub face |
| Tyres | TPU 95A black | X | printed flat |

- **Caramel colour.**
  - #AE835B is the Bambu catalogue swatch, stored as `swatch` in the manifest.
  - The render `color` is a darker albedo, **#745034**. The viewer's ACES tone mapping plus the key light and environment lifted #AE835B to about RGB(232,209,177) on lit areas, a light golden beige.
  - With #745034, hero lit areas sample at about (199-206, 157-169, 121-137) and shaded areas at about (112-140, 74-101, 50-77). The swatch (174,131,91) falls between the two.
  - A real print is browner and more "latte" than the golden #CF8A46 in the concept renders.
  - **Availability in Turkey is not verified.** Bambu PLA Matte Caramel was not found at Robotistan or Direnc on 2026-10-25. If the studio substitutes a local light-brown PLA, the tone will differ.
- Two colours plus black: every part is a single colour, so no AMS is needed. The toe-beans are separate cream inserts, or embossed only if printed in one colour.

## Screens and faces

- Each GC9A01 runs 240×240 at RGB565.
  - The faces are drawn at native resolution with 1-px anti-aliased edges, the way LovyanGFX `fillSmoothCircle` draws them, and quantised to 5-6-5.
  - Expressions: neutral, blink, happy, talk_a, talk_b, surprised, sleepy, sad, determined, plus the concept's curious.
- Fındık has **no mouth**. Talking is shown as eye pulses: talk_a has wider pupils and a lifted lower lid; talk_b is squashed by 0.86 with a higher lower lid.
- The cheek LEDs would pulse while it talks or is happy. The rig cannot switch LEDs on and off per face, so the LEDs are internal only. They appear only in x-ray.
- Face files: `<expr>_L.png` is the robot's LEFT eye (+X), which appears on the viewer's right.
- The screen sits about 4.4 mm deep in the visor bore.
  - In a lit room the black panel reads as a dark-grey disc, lighter than the glossy visor. The concept's claim that the panel "disappears" is optimistic.

## Placeholder and uncertain

- The `check_*` stills are rig checks: joint axes, directions and limits, rendered without re-solving the base. In some of them the robot floats or sinks. **They are not physical poses.**
- `specs.runtime_*` are still the concept's calculated power-table values (not simulated).
- GC9A01 module shape: the model assumes the round Ø38.6 PCB with the header removed (see concept §12).

## Motion (MuJoCo, `sim/`)

**Rebuild.** `python3 -I sim/build_mjcf.py` (meshes + `findik_base.xml`), `python3 -I sim/fall.py` (fall matrix with the CoM sweep, 14 configurations, ~5 min on 4 processes),
`python3 -I sim/clips.py` (all `anim/*.json`), `python3 -I sim/update_manifest.py`, then
`python3 sim/make_strip_shots.py`, `node render/posecheck.js paket/C sim/strip_shots.json sim/strips` and
`python3 sim/compose_strips.py` for `stills/anim_*.png`. (`build_mjcf.py` needs `PYTHONPATH=scratchpad/pylib_c` only for the optional decimation.)

**Model.** The MJCF mirrors the GLB exactly: `body` has a free joint and the GLB root frame; each `leg_*` sits at its GLB node position
with the manifest axis and zero (arm straight down); each `wheel_*` sits on its axle with axis +X. The recorded joint angles and base poses
therefore replay 1:1 in rig.js.
- Collision: convex hulls of the real meshes (egg shell incl. visor, 2 ears, 4 arm+boot hulls), tyres as cylinders (r 15, w 6.8).
  Body vs legs/wheels contact is excluded, because a convex hull would fill the sculpted shoulder sockets. MuJoCo therefore cannot see arm-vs-shell interference. The joint limits come from `check_arm_shell.py` instead, and `verify_replay.py` checks every frame against it.
- Mass 300.9 g from the concept mass table: printed shell as a thin shell, internals as solids at their x-ray positions, legs from CAD volume.
  Resulting CoM: (0.2, 4.5, 46.3) mm, 1.6 mm lower than the concept's 47.9 mm (the concept lumps 22 g of wiring at the deck; here 14 g).
  Because recovery is sensitive to this, `fall.py` sweeps the CoM height (+0, 1, 1.6 = concept, 2.5, 3.5 mm).
- MG90S: torque-speed line 0.20 N·m / 600°/s, kp 2.9 N·m/rad (full torque at about 4° error), armature 5e-5. N20: 0.10 N·m stall, 100 rpm at the 80 % PWM cap.
- Friction: PLA shell = desk μ (0.6, and 0.4); TPU tyres 0.9 on the 0.6 desk and 0.4 on the 0.4 desk (worst case). The tyre contact is softened to stand in
  for TPU compression; without that, one rear wheel lifts off whenever its motor torque deflects the compliant hip servo.

**All clips are simulated**, including idle/talk/happy/sleep (joint targets go to the simulated servos; the base is whatever the sim did).
Checks per clip are in `sim/results/clips_report.json`.
- No frame is without floor contact, except the falls and one frame of the turn sit-down (gap 0.08 mm).
- The worst contact penetration is 1.3 mm (TPU tyre during the sit-down and the wave).
- Every hip angle stays inside the shell-clear range.

| Clip | Result |
|---|---|
| walk (7 s) | Rolls on the rear N20s: **13.8 cm/s** (same at μ 0.4), 72 cm in the clip, stops within 3 mm when braked. It does not walk; the legs only hold the stance. |
| turn (5 s) | **Belly-pivot spin**: it sits on the round belly (front 82°, rear 50°) and paddles the rear wheels in opposite directions: **49°/s** (63°/s at μ 0.4), 155° in the clip. |
| happy (4 s) | Leans right/back (FR 40°, RL 8°, RR 65°), waves the front-left paw on 3 wheels (CoM 14.4 mm inside the support triangle throughout the wave, in sim), then bounce + wheel wiggle. |
| idle / talk (5 s loops) | Breathing ±3° and sway; talk nods/tilts with talk_a/talk_b every 0.17-0.20 s. Loop drift ≤ 1.6 mm, spread over the loop. |
| sleep (4 s) | Legs to 75°/72°, the egg settles on its belly, sleepy → closed eyes. |
| fall_recover (5.6 s) | Finger push at the head toward its left side → **hybrid** trigger tucks at 50° while still falling → rolls back → standing again 1.0 s after the tuck. |
| fall_back_help (5.6 s, extra) | Hard shove backward (held to 75°): the paw-catch reflex is not enough, it lands on its back and rocks its paws asking for help. **This is the honest failure case.** |

**Turning is the big finding.** The concept says it "spins in place, leaning back to unload the front paws". In the sim that does not work with
TPU tyres on the free front wheels: the front tyres resist sliding sideways, and on 4 wheels it turns only 7-9°/s while drifting 11-12 cm/s
(a wide arc; one-wheel arcs are no better, ~6°/s). Hence the belly-pivot turn in the clip. Its rate is uncertain: the rear tyres carry only ~10 %
of the weight there and chatter (in contact 15-30 % of the time). **Fix:** hard PLA/PETG front rims (μ ≈ 0.35) → a 62°/s lean-back spin on 4 wheels in the sim (see below).
The result is also sensitive to servo stiffness (kp 1.5 → 12°/s, kp 20 → 43°/s for the lean-back spin), because the N20 torque reacts on the
compliant hip servo and unloads the wheel ("drive-torque jacking").
- **With the new rear limit (+5° instead of −5°) the hard-rim lean-back spin drops to 62°/s** (6.8 cm/s drift), not 120°/s. Hard front rims are still the preferred fix.
- **Belly wear:** the belly pivot slides the cream PLA belly on the desk at μ 0.6. The two M2 countersunk belly screws (x = ±18) sit about 3-5 mm above the lowest belly point, beside the contact patch.
  - On a real desk this scuffs the shell and may drag the screw heads.
  - Recommended: a felt or PTFE dot (or a printed PETG wear skid) at the pivot, or move the screws further out.

**Self-righting** (`sim/results/fall_matrix.json`).
- Test cases: 12 push directions × 2 tilt speeds (30 and 90°/s, released at 40°), plus 6 side drops (±15° pitch) and back/face/upside-down drops.
- "CoM +x" raises the body CoM by x mm. **+1.6 mm is the concept's own CoM estimate** (47.9 mm).

| Firmware | μ | CoM | pushes that fell → recovered | caught by paw reflex | side drops | back/face/upside-down |
|---|---|---|---|---|---|---|
| **hybrid (tuck at 50° side tilt while still falling) = headline** | 0.6 | sim (46.3 mm) | **18/18** | 6/24 | 6/6 | 0/3 (asks for help) |
| hybrid | 0.6 | +1.0 mm | 16/18 | 6/24 | 6/6 | 0/3 |
| hybrid | 0.6 | **+1.6 mm (concept CoM)** | **17/18** | 6/24 | 6/6 | 0/3 |
| hybrid | 0.6 | +2.5 mm | 17/18 | 6/24 | 6/6 | 0/3 |
| hybrid | 0.6 | +3.5 mm | 17/18 | 6/24 | 6/6 | 0/3 |
| hybrid | 0.4 | sim / +1.6 mm | 16/17 / 17/17 | 7/24 | 6/6 | 0/3 |
| concept (60° for 0.3 s, + catch reflex) | 0.6 | sim | 16/18 | 6/24 | 6/6 | 0/3 |
| concept | 0.6 | +1.0 mm | 12/17 | 7/24 | 6/6 | 0/3 |
| concept | 0.6 | **+1.6 mm (concept CoM)** | **9/17** | 7/24 | 6/6 | 0/3 |
| concept | 0.6 | +2.5 mm | 10/18 | 6/24 | 6/6 | 0/3 |
| concept | 0.6 | +3.5 mm | 4/18 | 6/24 | 6/6 | 0/3 |
| concept | 0.4 | sim | 14/16 | 8/24 | 6/6 | 0/3 |
| concept, no catch reflex | 0.6 | sim | 16/24 (backward pushes end on the back) | 0 | 6/6 | 0/3 |

- CoM curve at μ 0.6, recovered/fell for CoM +0/1/1.6/2.5/3.5 mm:
  - concept: 16/18, 12/17, 9/17, 10/18, 4/18
  - hybrid: 18/18, 16/18, 17/18, 17/18, 17/18
- The hybrid failures are single cases toward 270° (a forward push that ends face-down after the paw catch), not side falls.
- The previous package version headlined "17/17 with the concept firmware". That held only at the MJCF CoM, which is 1.6 mm lower than the concept's own estimate.
- The concept's rule alone cannot be relied on. The hybrid trigger is a firmware-only change and is what the viewer shows.
- In a dynamic side fall the egg does **not** stop on its side (the quasi-static rest at roll 84°). It rolls on to ~100-105°, partly onto the back.
  The concept's rule only works because its 0.3 s timer fires while the egg is still rolling. A firmware that waits until the robot is at rest
  fails almost always (it ends on its back).
- The concept rule is **brittle against the CoM height**: 1.6 mm higher (the concept's own estimate) drops it to 9/17, and 3.5 mm higher drops it to 4/18.
  A few mm is well inside build tolerance (wires, glue, a heavier board).
- Back, face and upside-down landings are never recovered (as the concept says). The paw-catch reflex prevents most back tips from a moderate push.
- Hip torque during righting reaches 0.16 N·m (80 % of stall) briefly. Hip servos touch the 0.20 N·m stall only for milliseconds in any clip.
- The pushing finger is not shown in the viewer; the robot simply starts to tip.

**Playback verification.** `python3 -I sim/check_arm_shell.py` (slow, ~20 min, → `sim/results/arm_shell_sweep.json`), then `python3 -I sim/verify_replay.py` (→ `sim/results/replay_check.json`).
- **MJCF vs GLB:** `verify_replay.py` parses `findik_base.xml` and asserts the following.
  - Every leg and wheel body position equals the GLB node translation (0.0 mm error).
  - Every hinge axis equals the manifest axis, and every range equals the manifest min/max.
  - The inertial masses sum to 300.9 g.
- **Replay:** it then replays every `anim/*.json` through the GLB's own node frames with the rig.js convention (no MuJoCo). Results:
  - The lowest visible point over all frames is −1.27 mm (fall impact, soft TPU contact); the highest gap is +0.61 mm. Nothing floats or sinks visibly.
  - Tyre and hub vertices never enter the egg's convex hull (0.0 mm). Front/rear tyre clearance is at least 22.3 mm (happy wave).
  - **Arm/boot/N20 sleeve never enters the shell skin (0.00 mm in every frame).** Each frame's hip angle is looked up in the winding-number sweep table.
    MuJoCo cannot catch this, because body-leg contact is excluded there; the sweep table and the joint limits are the guard.
- **Posecheck strips** (fixed camera per clip, 6-12 t values, face label per tile): `stills/anim_{idle,talk,happy,walk,walk_follow,turn,sleep,fall_recover,fall_back_help}.png`.
  - `anim_walk` uses a fixed world camera; the robot travels 72 cm, so it is small.
  - `anim_walk_follow` is a close follow camera rendered from a throw-away package (`sim/make_follow_pkg.py`). In it the walk base is wrapped back every 30 cm (a pure ground-plane shift, a multiple of the 1 cm grid), so the grid and shadow stay under the robot. Joint angles, height and attitude are unchanged.
  - Rebuild: `python3 sim/make_strip_shots.py`, `node render/posecheck.js paket/C sim/strip_shots.json sim/strips`, `python3 -I sim/make_follow_pkg.py <tmp>`, `node render/posecheck.js <tmp> sim/strip_follow.json sim/strips`, `python3 sim/compose_strips.py`.
- Faces checked in the strips: blinks in idle, talk_a/talk_b alternation in talk, surprised → determined → happy in fall_recover (the hybrid tucks before it lands), sad while asking for help, sleepy → closed eyes in sleep.
