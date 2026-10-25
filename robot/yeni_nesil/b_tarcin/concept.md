# Konsept B — "Tarçın": cep boyu kızıl panda robot

**Tagline:** a pocket red-panda pup with a mask-visor face, glowing round eyes, and a long ringed tail. The tail wags when it is happy and doubles as the lever it uses to get back up.

Renders are in `renders/`:
- `B_hero.png`, `B_front.png`, `B_side.png`, `B_rear34.png`
- `B_happy_wave.png`
- `B_xray.png`
- `B_selfrighting.png`
- `B_colorways.png`

CAD is in `model.py`. Its output STLs, one per colour or material, are in `stl/`.

## Karakter
- **Character:** an original red-panda / raccoon pup.
  - Big round head: 88 mm wide, about 59 % of the standing height.
  - Dark "mask" visor with two round glowing eyes.
  - Cream muzzle, a glossy black nose, and a tiny "ω" mouth.
  - Rounded cat ears in TPU, with cream inner ears.
  - Chubby cinnamon thighs with charcoal "socks" and paws.
  - A tall bushy tail with charcoal rings.
- **Personality cues:**
  - The eyes are drawn procedurally and lead every gesture. The head pans after them, then the body follows.
  - Two WS2812B LEDs behind thin cream cheek windows glow pink when it is happy.
  - The tail wags sideways.
- **Colours:** two colours plus black, in matte PLA.
  - **Tarçın:** `#DF6E35` cinnamon, `#F3EEE4` cream, `#2A2C31` charcoal.
  - **Alternates (`B_colorways.png`):** "Süt & Mandalina" and "Galaktik Gece".

## Boyutlar ve kütle
| | |
|---|---|
| Size (W × L × H) | 120 × 144 × 150 mm. Head 88 wide; ears and the tail tip set the height. Hip axis is 69 mm off the desk. |
| Mass (CAD budget, `stl/checks.json`) | **≈ 368 g**: printed parts 137 g, 10 servos 125 g, battery 39 g, electronics 47 g, wiring and screws 20 g. That is about 5 % over the guide's ~350 g. The torque margins below still hold. |

## Mekanizma ve DOF (10)
- **Legs: 8 DOF, sagittal (OpenCat/Bittle kinematics).**
  - Each leg has a hip pitch and a knee.
  - L1 = 40 mm, L2 = 34 mm.
  - Stand pose: thigh 20°, shin 24°. Each paw sits under its hip, and the knees point inward.
- **Leg pods: the key packaging idea.**
  - Each thigh is a self-contained module holding two MG90S servos: the hip servo near the top and the knee servo near the bottom. Their mounting tabs are trimmed and the pod clamps the cases.
  - The hip servo's horn bolts to a Ø18 hub post on the body, and a Ø22 collar acts as a coaxial bearing.
  - The shin runs in the plane between the body and the pod, so the paws land under the body. That gives a cute, tidy stance with no visible servos.
  - The body therefore contains no servos and is only 39 mm wide.
- **Head:** 1 DOF pan, ±40°, from a 4 g digital micro servo inside the head that drives a neck post. The body has a smooth saucer-shaped neck nook for clearance. CAD clearance is ≥ 1.9 mm to the body and ≥ 2.5 mm to the front pods over the full pan range.
- **Tail:** 1 DOF, an MG90S in the rump with its shaft along +Y.
  - It sweeps sideways like a windscreen wiper (±85°) to wag.
  - It is also the self-righting lever.
- **Joint windows (180° servos):**
  - Front hips −20…+160°; hind hips −50…+130°. Both swing "backward" over the back, so front and hind legs never cross.
  - Knees ±140° fold.

## Yürüme
- Trot, walk, crawl and turn use the OpenCat gait tables, re-zeroed for these windows.
- The stance is narrow and paw-under-hip. That gives almost zero hip torque and a short knee lever.
- Tiny TPU paws grip the desk. The legs can also lean, bow, sit and wave a paw (`B_happy_wave.png`).

## Kendini doğrultma (verified in MuJoCo)
**Method:** an OpenCat-`rc`-style keyframe recovery, adapted to this body.
- **Trigger:** the IMU (BMI160) sees roll above 85° or gravity reversed.
- **Retries** mirror the move left/right on alternate attempts, as OpenCat does.
- **Sequence** (`sim/out/best_seq_13.json`, 5 keyframes, about 3 s):
  1. The legs throw the body onto its back.
  2. The tail swings −35° and then +46° as a lever while the legs kick.
  3. The body flips onto its feet and stands.

**Model used:** `sim/righting.py`. It is built from the CAD STLs as convex hulls.
- Real masses.
- MG90S limits: 0.20 N·m and 600°/s.
- TPU ears are soft and non-colliding.
- Knee fold limited to ±140°.

**Results** (`sim/verify.py`, 24 drop orientations each: sides, back, 135°, pitched, random):

| Condition | Recovered within 4 tries |
|---|---|
| μ = 0.6 (desk) | **24/24**, most on the first try (also 24/24 with ±140° knee limit) |
| μ = 0.9 (TPU / mat) | **24/24** |
| +10 % mass | **24/24** |
| μ = 0.4 (glossy) | 20/24 |
| Same body with a short tail (scale 1.0) | only 4/24 |

The design changes that came out of this simulation:
- The domed crown (`head_ev_top = 1.8`) means it can never rest on its head.
- The long tail is the lever.
- An earlier flat-top head with a short tail failed every roll case.

`B_selfrighting.png` shows CAD poses taken from the simulation.

## Yüz ve ifade
- **Eyes:** 2 × GC9A01 1.28" round IPS screens (240 × 240) sit behind a flat 2 mm smoked-acrylic visor in a mask outline. The visor is set flush into a flat face plane with a 0.5 mm reveal groove.
  - The modules sit with their glass 0.3 mm behind the acrylic and their headers pointing up into the forehead.
  - CAD check: the visor and modules stay fully inside the head (0 mm³ protrusion).
- **Eye layout:** eye centres ±19.6 mm. The pupil-less pills are drawn offset toward the nose, so the visual gap is about 1× the eye width. The eye line is at 45 % of head height.
- **UI:** a pure black background, so the screen edges vanish behind the smoked acrylic.
- **Eye frames:** `eyes.py` draws neutral, happy, curious and love frames with PIL. Firmware draws the same shapes procedurally (blink squash, saccades, eyes leading the head).
- **Other face elements:** WS2812B cheek blush, a TTP223 head-pat sensor, and a 32 mm speaker with a PAM8403 for chirps.

## Elektronik
**Two ESP32-S3 Super Minis**, linked by UART (5 V, GND, TX, RX) through the neck:
- **Head MCU:**
  - SPI to both eyes (shared SCK/MOSI/DC, two CS lines) plus backlight PWM.
  - Pan servo, touch, PWM audio, WS2812.
  - Wi-Fi and the Claude API over HTTPS.
  - 12 of about 15 GPIO used.
- **Body MCU:**
  - 9 servo PWMs: 8 LEDC channels plus 1 MCPWM.
  - I²C to the BMI160 and VL53L0X.
  - Battery ADC.
  - 14 of about 15 GPIO used.

**Sensors:**
- **VL53L0X:** sits in the nose, looking down and forward. It detects the desk edge about 25 mm ahead of the front paws.
- **BMI160:** sits on the spine near the centre of mass.

## Güç ve batarya yerleşimi
- **Battery:** 2S 14500 Li-ion (7.4 V, about 6 Wh), stacked on the centre line low in the belly (CAD-checked fit).
  - It runs from y −33 to +17 mm, between the neck and the tail servo, which keeps the CoM low and central.
  - Cells must be high-drain (IMR, 4 A or more). Charging is through a 2S BMS rated 5 A or more and a 2S USB-C 4 A charger, with the port on the right flank.
- **Rails:**
  - 2 × MP1584 at 5.5 V, one per servo bank.
  - 1 × MP1584 at 5.0 V for logic, behind an SS14 Schottky with 470 µF hold-up.
  - 1000 µF per bank, star ground.
  - Servos attach one at a time, slew is limited, and Wi-Fi/audio pause during recovery.
- **Estimated run time:** walking about 1.5 A average (about 11.5 W) gives about 30 minutes; idle or talking about 2.2 h. The peak during recovery is about 5.8 A for under 0.5 s.

## Tork kontrolü (`calc.py`, m = 0.368 kg, MG90S at 5.5 V = 0.20 N·m, peak = static × 2)

| Case | Knee lever | Peak % of stall |
|---|---|---|
| Stand, 4 legs | 13.8 mm | 12.5 % |
| Trot / crawl / paw-wave | 13.8 mm | 25 % |
| End of stride, foot 20 mm ahead | knee 21.9 mm, hip 18.4 mm | knee 39.5 %, hip 33 % |
| **Worst: deep-crouch trot (thigh 40°)** | 25.7 mm | **46 %** (below the 60 % rule) |
| Stand up from belly | — | 20 % |

- **Head pan:** needs 0.003 N·m, about 4 % of the micro servo.
- **Tail lever:** 2.7 N at the tip, against a 3.6 N robot. The simulation shows recovery briefly saturates the servos (stall for under 0.5 s per attempt).

## Basılabilirlik
All parts are FDM PLA, with TPU 95A for the paws and ears. Walls are at least 1.6 mm everywhere.
- **Body:** two domes split at the reveal groove: a cinnamon top and a cream belly. Both print dome-up with no supports.
- **Head:** a cinnamon crown shell (dome-up, 0.12 mm layers) plus a cream muzzle part. The visor is laser-cut acrylic.
- **Pods:** a shell plus an inner cover plate carrying the hub collars, and a separate charcoal "sock" cap joined at a groove.
- **Small parts:** the shin is a flat plate; the paws and ears are TPU; the tail is printed hollow in 3 ring sections.
- **Fasteners:** screws go in from the underside only, and magnets hold the ears.

## Maliyet (`calc.json`, prices in TL with KDV, from Turkish shops in stock)
| Item | TL |
|---|---|
| MG90S ×10 (8 legs, tail, 1 spare) | 1258 |
| 4 g micro servo | 303 |
| GC9A01 ×2 | 703 |
| ESP32-S3 Super Mini ×2 | 945 |
| BMI160 | 128 |
| VL53L0X | 423 |
| Touch, audio, LEDs | 108 |
| 14500 ×2, BMS, charger | 343 |
| MP1584 ×3 | 160 |
| Misc (est.) | 220 |
| Acrylic (est.) | 60 |
| **Parts total** | **≈ 4,650** |
| **All-in, with print 450–900 and shipping 150** | **≈ 5.25–5.7k** |

**Lean version, ≈ 4.2k parts and ≈ 4.8–5.2k all-in:**
- Drop the spare servo.
- Use one ESP32-S3 N16R8 devkit in the head (with a 12-wire neck loom) instead of two Super Minis.

## Yenilik
1. **Two-servo leg pods.** The body holds no servos; the legs are modular, swappable and identical.
2. **Mask visor with two round eyes.** It makes the two screens read as a natural red-panda marking rather than a gadget.
3. **A tail that is both emotion and function.** It wags for joy and is the self-righting lever.
4. **Recovery verified before CAD sign-off.** The self-righting was checked in MuJoCo on the actual CAD geometry under friction and mass variations.

## Riskler
- **Mass:** ≈ 368 g, about 5 % over the guide. The legs carry 46 % of the mass, which means more swing inertia.
- **Recovery stresses the servos.** It saturates them briefly, so retries need a cap, the robot should cool down between attempts, and the tail servo needs metal gears. It is weaker on glossy desks (20/24 at μ = 0.4).
- **Simulation fidelity.** The model uses convex hulls, an idealised servo model and soft ears. The real tuning should be redone on hardware.
- **Board GPIO.** Super Mini GPIO count varies by vendor (the shop lists 11; my budget assumes 15). The fallback is an ESP32-S3-Zero-class board for the head.
- **Parts and supply:**
  - GC9A01 module outlines differ by vendor (Ø38 PCB assumed); Robotistan has only 19 in stock.
  - The 14500 cells' discharge rating and the 2S BMS current rating must be verified.
  - Trimming servo tabs and clamping the cases needs accurate print tolerances.
- **Over budget:** cost is above the ideal 3.5k for parts.
- **Size:** height is 150.3 mm, right at the limit.
