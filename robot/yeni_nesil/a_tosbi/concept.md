# Konsept A: "Tosbi", the two-faced turtle

**Tagline:** *Ters dönse de yürür.* A Sesame-lineage 8-servo spider walker restyled as a chibi turtle. Its two shell faces are identical, so it never has to get back up: when it lands upside down it simply walks on the other face.

Renders (all in this folder):
- `render_hero.png`, `render_front.png`, `render_side.png`, `render_back.png`, `render_top.png`
- `render_action_wave.png`: happy face, head up 26°, one paw raised
- `render_flip_sequence.png`: the three steps of recovering from landing upside down
- `render_xray.png`: the fit of every internal part
- `render_colourways.png`: Nane Şekeri, Galaktik Gece, Mandalina
- `eyes_sheet.png`: the four expressions; `screen240_*.png` are the exact 240×240 panel frames

## Karakter

Tosbi is a curious toddler turtle that is a little clumsy and proud of itself.
- **Its signature joke:** a turtle on its back is helpless, but Tosbi on its back just shrugs and keeps walking. The eyes switch to "determined" and the image rotates 180°.
- **Face:** an oval, glossy black face visor with two big pill-shaped eyes that glow cyan, a soft blush, and a coral pin-stripe around the edge.
- **Head:** a round "mochi" head that looks up at you at a 15° pitch.
- **Touch spots:** a coral hexagon "pat me" plate on the middle shell segment of each dome, with a copper touch pad behind it, and a second pad inside the top of the head.

## Ölçüler ve kütle

**Size**
- Standing: **154 W × 156 L × 72 H mm** (bbox from the model). The robot is about 3% over the 150 mm guideline in length and width.
- Body pebble: 82 × 84 × 48 mm.
- Head: 66 W × 58 H × 40 D mm, which is 81% of the standing height.
- Mid-plane height: 42.5 mm. Body ground clearance: 18.5 mm.

**Mass estimate (`calc.py`): about 380 g ±25 g**
- Bought parts: 225 g.
- Printed parts: 155 g, assuming 1.2 mm walls on the legs, 1.4 mm on the head and 1.8 mm on the domes.
- This is about 30 g over the 350 g target. Ways to save weight:
  - SG90 for the neck: −4 g.
  - 1.0 mm boot walls: −6 g.
  - Drop the spare chassis ribs: −5 g.
  - Together these reach roughly 365 g.

**Centre of mass**
- Located at y = −9 mm (toward the head) and 38.8 mm above the ground.

## Mekanizma ve serbestlik dereceleri (9 DOF)

**Legs: 8 × MG90S, Sesame kinematics**
- Each leg has a hip yaw servo plus a knee.
- Hip axes sit on the corner arcs at ±35°, 6 mm inside the shell edge.
- Leg geometry:
  - Coxa (hip to knee axis): 33 mm
  - Foot (knee to toe axis): 36 mm
  - Stance: 80° below the flipper plane
  - Toe: a TPU capsule, R7 × 24 mm, lying along the knee axis
- Gait yaw range:
  - Rear legs: ±20°.
  - Front legs: +14° forward and −20° back. The forward limit comes from head clearance and is collision-checked.
- Hip servos sit fixed in the body.
  - Their bodies point inward at 120°/60°.
  - The outer tab is trimmed and the inner tab is screwed to the chassis.
- Each hip drives a mint **hub egg** (a superellipsoid of revolution).
  - The egg sits in a matching socket in the shell with a constant 0.8 mm reveal.
  - The horn is on top of the egg and an M2 shoulder-screw bearing pin is below it.
  - A C-window on the inside of the egg lets the fixed servo body pass through. It cannot be seen in any yaw position.
- Each **knee servo** lies inside the arm.
  - It turns a **knee barrel** (R11.4 × 40.6 mm). Its middle belongs to the arm and its two end caps belong to the foot.
  - The joint therefore looks like a seamless barrel at every knee angle, and no horns or brackets show.
  - The foot boot starts outside the arc the arm sweeps.

**Neck: 1 × MG90S, head pitch −40…+40°**
- The servo is **fixed on a short stalk inside the head**. The head and its electronics pitch around it, about the head's own centre.
- Benefits of this layout:
  - The head's outline barely changes as it pitches.
  - The gap to the body stays at 5 mm.
  - Only a Ø15 stalk crosses that gap.
  - The front legs and the neck stop fighting for space at the front of the body. A neck servo in the body front collided with the front hips in iterations 1–4.

**Expression**
- The face is drawn procedurally on a 240×240 sprite at ≥30 fps: blinks, eye jumps and lids.
- Head pitch gives nodding and looking up.
- The legs give the body roll, pitch, yaw, bounce and "breathing", which covers the curious head tilt.
- Chirps play through a 29 mm speaker behind the tail grille.

## Kendi kendine doğrulma (dürüst değerlendirme)

The robot is built to be the same either way up:
- The two domes are the **same printed part, flipped**.
- Knee axes, hub eggs and the neck pivot all sit on the mid-plane.

When the BMI160 sees gravity reverse, the firmware:
- mirrors the knee angles (β → −β)
- mirrors the neck angle (θ → −θ)
- rotates the display 180°.

The recovery sequence for "on its back" (`render_flip_sequence.png`):
1. The robot lies on its back with its feet up.
2. The knees swing about 160° through the flipper plane. The horizontal-foot position is collision-checked (`out/flat`).
3. The feet touch down at about 28° and push up with all four legs. That takes 39% of stall (below).

No active roll-over is needed. Research showed that roll-over cannot be done with spider legs anyway (17–38° achievable vs 53–65° needed).

Cases not yet proven:
- **Side landing:** the robot rests on one side's legs, a shell edge and the head side. The lower knees should kick it onto either face, since both faces count as "up".
- **Nose-down landing:** the head plus the front legs should rock it back.

Neither case has been simulated. The next step is MuJoCo with these exact joint limits.

## Elektronik

| Block | Part | Location |
|---|---|---|
| Brain | ESP32-S3 SuperMini (Wi-Fi to the Claude API) | head top, horizontal, outside the servo sweep |
| Face | GC9A01 1.28" round IPS behind a printed glossy-black PETG oval visor (52.6 × 36.6 mm); black-painted mask; smoked acrylic window | head front |
| Cliff / edge | VL53L0X, looking out of the chin slot (it reads as a tiny mouth) at 35° down. Inverted, the neck mirrors so it still looks at the desk | chin |
| Servo driver | PCA9685 (I2C), 9 of 16 channels | body, centre deck |
| IMU | BMI160 | body |
| Audio | PAM8403 (fed by ESP32 PWM/ΣΔ) + 29 mm speaker | body rear |
| Touch | ESP32-S3 native touch pins, with copper tape behind the coral hex plates and inside the head top | — |

- **Neck flex:** 6 wires (5 V, GND, SDA, SCL, audio, body touch) cross the stalk with a ±40° service loop.
- **GPIO:** the SuperMini has enough pins only because the servos go through I2C.

## Güç ve batarya yerleşimi

- **Pack:** 2S 14500 Li-ion, two cells lying lengthwise in the belly column (x = ±7.3 mm, z = −13 mm), with a 2S BMS and a 2S USB-C charger. The USB-C port is in the "tail" nub.
- **Rails:** two MP1584 at 5.5 V, one per servo bank, and one MP1584 at 5.0 V for logic (sent up the neck).
- **Protection:** an SS14 diode and 470 µF on the logic rail as hold-up, and 1000 µF per servo bank.
- **Firmware power rules:** staged servo attach, a slew-rate limit, and pausing Wi-Fi during push-ups.
- **Runtime:** about 6 Wh gives roughly 30–40 minutes of walking and 2–3 hours of idle or talking.
- **Fit:** the pack fits, as the x-ray and `check.py` confirm.

## Tork kontrolü (`calc.py`; 380 g; MG90S ≈ 0.20 N·m at 5.5 V; static × 2 for dynamics)

| Joint / case | Lever | ×2 torque | % stall |
|---|---|---|---|
| Knee, trot, front leg (60% of weight on the front pair) | 6.3 mm | 0.028 N·m | **14%** |
| Knee, crouched trot (foot at 55°) | 20.6 mm | 0.092 | **46%** |
| Knee, push-up from the back/belly, 4 legs (+15% uneven) | 36 mm | 0.077 | **39%** |
| Knee, push-up with only 2 legs touching | 36 mm | 0.134 | 67%: firmware must push with 4 |
| Hip yaw scrub, μ 0.5 / μ 0.8 (TPU) | 39 mm | 0.073 / 0.117 | **37% / 59%** |
| Neck (pivot at the head's centre of mass) | ≈4 mm | 0.003 | 2% |

The worst normal case is the crouched trot at 46%, which is under the 60% rule.

**Crawl-gait stability:** the centre of mass is 7.4 mm outside the support triangle when a *front* leg lifts. The gait must shift the body back about 12 mm, as Sesame does, or use a trot.

## Parçalar (Türkiye stoğu, TL, KDV dahil, `bom.py`)

| Item | Price |
|---|---|
| 10× MG90S (incl. 1 spare) | 1,258.00 |
| ESP32-S3 SuperMini | 472.68 |
| GC9A01 round display | 351.50 |
| PCA9685 | 245.54 |
| BMI160 | 127.86 |
| VL53L0X | 423.35 |
| 2× 14500 cells | 210.96 |
| 2S BMS | 45.24 |
| 2S USB-C charger | 78.00 |
| 3× MP1584 | 159.66 |
| PAM8403 | 26.78 |
| 29 mm speaker | 70.76 |
| USB-C breakout, capacitors, wiring, copper tape, screws, bearing pins (est.) | 230.00 |

- **Parts:** about 3,700 TL.
- **Print:** 650–950 TL at a studio, using mint PLA, cream PLA, coral PLA, black PETG for the visor and coral TPU for the toes.
- **Shipping:** about 150 TL.
- **Total: about 4,500–4,800 TL.** A lean build without the VL53L0X and the spare servo comes to about 3,950–4,250 TL.

## Basılabilirlik

- Six materials, each exported as its own STL in `out/stand/`:
  - `shell.stl`: mint domes plus hub eggs
  - `leg.stl`: mint arms and boots
  - `skin.stl`: cream head, stalk and tail
  - `accent.stl`: coral bezel and hex plates
  - `tpu.stl`: coral toes
  - `visor.stl`: black PETG
  - The internals are separate, for the x-ray.
- **Domes:** one STL printed twice, dome-up, at 0.12 mm layers, with the seam at the back.
- **Hub eggs:** split at the equator.
- **Arms:** split top and bottom, and they clamp the knee servo.
- **Boots:** printed standing.
- **Head:** split front and back.
- Walls are ≥1.2 mm on the legs, 1.4 mm on the head and 1.8 mm on the domes. Overhangs are under 45°, except the egg poles, which print pole-down.

## Neden yeni / Sesame'den farkı

1. **The symmetric "two-faced" body solves self-righting without an extra mechanism.** A head is usually what breaks that symmetry; here the head and the neck pivot also sit on the mid-plane.
2. **The neck servo is fixed inside a head that pivots about its own centre**, so a big head can coexist with Sesame-style front legs.
3. **Every joint reads as a designed form:** egg-in-socket hips with a constant reveal, and knee barrels whose end caps rotate with the foot. No servo boxes, horns or brackets are visible.
4. **The face is a single round screen inside an oval visor.** This keeps the EMO/EVE-style face at a 351 TL display cost.

## Riskler

See the structured summary. In short:
- weight is about 30 g over target
- footprint is about 4 mm over 150 mm
- side landings are unsimulated
- the crawl gait needs a body shift
- tabs must be trimmed on 8 servos
- 14500 high-drain cells and BMS current rating are not yet verified.

## Dosyalar

- `model.py`: build123d model. Poses: stand, wave, flip, fallen, transit, yawfwd, yawback, pitchup, pitchdown, flat.
- `check.py`: manifold3d collision and fit check across all poses. The only contacts are the intended horn splines.
- `calc.py` → `calc.json`: mass, centre of mass, support margins and torque.
- `bom.py` → `bom.json`
- `eyes.py`: eye frames.
- `render.py` and `renderer/`: a local copy of the guide renderer, extended with `envMapIntensity` and `specularIntensity`.
