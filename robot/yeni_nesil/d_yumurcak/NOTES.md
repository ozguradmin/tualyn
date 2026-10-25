# D · Yumurcak: notes, simplifications and uncertainties

## Colours and printing (no AMS needed)
Every colour is a separate printed part, so a single-colour printer with filament swaps between jobs is enough. An AMS-type printer is not needed.

| Part | Filament | Print orientation (layer axis) |
|---|---|---|
| Body bowl, head shell | Elas PLA Krem / Fildişi, matte, #efe6d4, 0.12 mm | Oblique 12° seam face on the bed, so layers are rings normal to the tilted head axis |
| Eggshell cap, 8 haunch hemispheres, 4 paws | eSUN PLA+ Orange, #f2881c | Cap and hemispheres dome up; paws on their side (layers along the knee axis) |
| Eye pocket behind the visor | Matte black PLA | — |
| Soles | TPU 95A black, glued on with CA | — |
| Visor | 1 mm smoked PETG sheet, vacuum-formed | — |

- **Visor gloss.** The gloss comes from the vacuum-formed PETG sheet. It is not a printed surface. If no vacuum former is available, the fallback is a 0.8 mm translucent-black PETG print. That version is matte and layered, and the eyes glow through it more softly. The lean BOM variant uses this fallback.
- **Orange on screen vs in reality.** The viewer's shared lighting and ACES tone mapping wash eSUN orange (#f2881c) out to a pale apricot (#f5ba56–#fddb92 on lit faces). A real print is much more saturated. The eyes are also brighter in reality than the grey-cyan they show behind the visor. The hex is kept as the filament's real colour. This has been reported as a global viewer issue.

## Joint limits vs the concept
- **Knee 0…164° (concept: 178° "egg mode").** `src/check_limits.py` shows that knee 165°+ hits the egg flank at yaw 0. The concept's fallen pose at 178° penetrates the shell by 4.2 mm. The recorded animations are clamped to 164 in `sim/rec.py` (`clamp_to_manifest`). The sim overshot to 165 on impact.
- **Yaw −20…85° (concept: ±85°).** Below −22° the knee knuckle drives into the egg, so inward yaw is limited to −20°.
- **Coupled knee/yaw limit** (`sim/limits_coupled.json`, enforced by the firmware model and every clip):

| yaw ° | −20 | −12 | −4 | 0…40 | 44 | 48 | 52 | 56 | 60 | 64 | 68 | 72 | 85 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| knee max ° | 160 | 162 | 164 | 164 | 160 | 156 | 150 | 142 | 136 | 128 | 122 | 114 | 70 |

- **Servo travel.** The knee needs the full 0–164° span. Many MG90S units only reach about 160–170°, so calibrate each knee servo's end points before assembly.

## Self-righting needs a firmware change
- **Concept manoeuvre alone** (fold the paws, then sweep the two down-side paws 164→0): 13/20 at μ 0.6 and 13/20 at μ 0.4. On back and face-down falls, the folded paw tips hold the egg at about 131°, and the −20° inward yaw limit stops the paw from pushing forwards or backwards.
- **"Flank tuck" retry** (`sim/fall.py`, STRATEGY=hybrid): after a failed sweep, fold the paws along the flanks (knee 150°, yaw 40°), then retry. This gives 20/20 at μ 0.6, 0.5 and 0.4. Results are in `sim/out/fall_hybrid_mu{0.6,0.5,0.4}.json`.
- **Recovered on the first try:** 13/20 at μ 0.6, 15/20 at μ 0.5, 13/20 at μ 0.4, each in about 4–5 s. The rest need attempt 3 and take about 11–12.6 s:
  - μ 0.6: shove back-left, nudge backwards, nudge/shove face-down, dropped upside down, placed on back, placed face down.
  - μ 0.5: shove left, nudge backwards, and the three placed/dropped cases.
  - μ 0.4: nudge/shove backwards, the two front-diagonal shoves, and the three placed/dropped cases.
- The flank tuck is **not in the concept**. The ESP32 firmware has to implement it.

## Servo load (build risk)
- **Walking.** The simulated walk peaks at 0.157 N·m on the leg servos. That is 78% of the 0.20 N·m MG90S clamp, above the concept's own ≤60% dynamic rule (the concept estimated 0.07). Expect warm servos and higher current than the concept assumes.
- **Hard recoveries.** These reach the 0.20 N·m clamp for short periods (≤0.05 s on impact, longer while pushing the egg over).

## Substitutions vs concept.md (see bom.json `changes_vs_concept`)
- **Battery.** 2 × Orion 14500 900 mAh Li-ion from Robotistan. These are **not IMR** cells: they are rated about 3C (2.7 A). The concept needs about 4 A on the battery side during a get-up. Servos must be staggered, and voltage sag or an ESP32 brown-out is possible. No high-drain 14500 is stocked in these Turkish shops.
- **Runtime.** 25 min walking and 3.5 h idle are the concept's estimates (11.8 W average while walking). They were not measured.
- **IMU.** BMI160 → MPU6050 (GY-521), to avoid a fourth paid parcel. The GY-521 board is 21 × 16 mm, and the x-ray still shows the concept's smaller IMU box.
- **Charger.** The concept's "2S 4 A" module (whose page actually says 2 A) → Motorobit 2S module charging at 0.55 A, about 2 h for a full charge. The USB-C port is at the back and reachable in the nest pose.
- **Power switch.** The model shows a slide-switch slot at the back, under the USB-C port. The first BOM bought a KCD1 rocker "under the belly", but a 19 × 13 mm rocker does not fit there: the haunch balls, the vertical cells and the BMS fill the belly.
  - The BOM now buys the IC205 slide switch (SS12D00 class, Robotistan 6.23 TL).
  - Because that switch is rated about 0.5 A, it only drives the gate of an IRF4905 P-MOSFET high-side switch (55.64 TL, 100 k pull-up). No battery current flows through it.
  - The MOSFET is not modelled; it lies flat on the perfboard.
- **Dimensions.** concept.md says 146 mm tall. The rest pose (knees 30°, soles at Z=0) measures 107 × 122 × 137 mm, which matches the concept's own stand STLs.

## Modelling simplifications
- Internals (servos, cells, PCBs, bucks, BMS, IMU, ToF, frame) are real-size boxes or meshes and are only visible in x-ray. Wiring inside the shell is not modelled because none of it is visible from outside. The head ribbon runs through the hollow centre post, and the knee leads run through the top pocket of each ball.
- Collision geometry in MuJoCo is made of convex hulls of the link meshes. The contact model lets the shell sink up to about 3 mm into the floor on hard impacts.
- The idle, talk, happy and sleep clips are scripted servo targets played back in the same sim; they do not tip over. The walk, turn, fall_recover and fall_recover_back clips are free physics results.
- The big printed shells (body, head, cap, haunch balls) carry explicit 35° crease normals in the GLB, computed in `src/build_rig.py` with trimesh `smooth_shade`. This removes a hairline shading artefact from sliver triangles along the head shell.

## Reproduce
- `python3 -I src/build_rig.py` builds `model.glb`, with `body` as the only root node.
- `python3 -I src/review_fixes.py` and `python3 -I src/bom_fix.py` apply the round-2 spec, BOM and notes fixes on top of the generated manifest and BOM.
- `cd sim && STRATEGY=hybrid NPROC=2 python3 fall.py 0.6 0.5 0.4` re-runs the fall study, and `python3 clips.py` re-records the clips.
