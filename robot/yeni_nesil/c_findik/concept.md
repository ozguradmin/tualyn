# Concept C2 — "Fındık": a wheel-pawed roly-poly hamster

**Tagline:** a palm-sized hamster that zooms around your desk on four wheel-paws, waves, kneels, and when it falls on its side it rolls itself back up like a *hacıyatmaz*.

*Fındık* means "hazelnut", a classic Turkish pet name, and *fındık gözlü* means "hazel-eyed". That is literally its face.

![hero](final/hero.png)

| | |
|---|---|
| Size (standing) | 96 W × 92.5 L × 117 H mm. Body egg 96 × 86 × 98 mm. Belly clearance 14.5 mm. |
| Mass (model estimate) | **301 g**. CoM is 33 mm above the lowest point of the belly. |
| Actuators | **6 in total**: 4 × MG90S hip-pitch servos (one per leg) and 2 × N20 6 V 100 rpm gearmotors in the rear paws. The front paws roll freely. |
| Expressive DOF | Body height, nod, head-tilt (roll) and squash come from the legs; pan comes from the wheels. That is Keepon's 4 DOF without a neck. Plus 2 round eye screens and 2 cheek LEDs. |
| Speed | 0.16 m/s at 6 V (100 rpm, Ø30 wheels), about 0.19 m/s at 7.4 V |
| Self-righting | Side falls are handled by "tuck & roll", checked with a 3D quasi-static analysis. Falls onto the face or back (and upside-down drops, which end on the back) are only *prevented*, not recovered. See §4. |
| Cost | Parts **3,873 TL**, print about 750 TL, shipping about 300 TL. **Total ≈ 4,923 TL.** Without audio ≈ 4,417 TL. |

---

## 1. Character and look

- **Who it is:** a round, curious, slightly clumsy desk hamster. Its default tempo is "busy little animal": quick rolls, then a pause and a look at you. It is proud after it gets up.
- **Silhouette:** one egg-shaped body that *is* the head. The proportions follow the baby schema:
  - The head is 84 % of the height and the legs are short stubs.
  - Two round ears and four chunky paws sit inside the body's footprint.
  - The silhouette reads as a hamster even when filled in black.
- **Two-tone shell (matte PLA):**
  - Caramel `#CF8A46` cap and ears, split from the body along a tilted plane (76 mm high at the front, 40 mm at the back) with a 0.9 mm reveal groove. It reads like a hamster's golden coat over a cream face and belly.
  - The body is warm cream `#EFE3CF`.
  - Black covers only the visor, the nose and the tyres.
- **Face:**
  - A glossy black "peanut" visor (two lobes and a pinched bridge) holds two round 1.28" IPS screens.
  - Below the visor: a tiny glossy nose and two pink blush cheeks (WS2812B behind 0.8 mm cream windows).
  - Eye line at 47 % of the body height (low = baby-like). The drawn eyes are 22 × 25 mm with a gap of about 0.9 eye-widths.
- **Paws:** each leg is a rounded caramel limb ending in a chunky boot with a Ø30 wheel. The wheel has a cream hub, a dark TPU tyre, and a caramel hubcap with embossed toe-beans.

## 2. Mechanism and motion

**Leg layout.** Four 1-DOF legs, hip-pitch only.
- Hip axes sit at 32 mm height: front at y = −15.5 mm, rear at y = +21.5 mm.
- Each MG90S stands vertically inside the lower body with its output spline facing outward. The horn is embedded in the arm.
- Leg dimensions:
  - hip→axle 34 mm
  - arm 4.4 mm thick with 2 mm round edges
  - boot r 11.6 mm
  - wheel Ø30 × 6.8 mm
- Stance is 22° (an "A" stance). Wheelbase 62 mm, track 76 mm.
- Usable sweep is −5…82° for the front legs and −12…122° for the rear legs. Each shoulder has a **sculpted socket**: a swept relief, so the arm never rubs the round flank. The CAD check shows 0 mm³ interference standing and 0.4 mm³ in the righting pose.

**Drive.**
- The rear wheels are driven by N20s (differential drive). Each motor sits inboard in its boot sleeve, bolted to the arm, and the D-shaft runs through the arm to the wheel.
- The front wheels free-wheel on M3 shoulder-screw axles.
- When the leg angles change, the front wheels roll and the body simply shifts. No wheel/leg coordination is needed.

**What it can do with 6 actuators:**

| Motion | How |
|---|---|
| Roll, spin in place | Differential rear drive. For tight spins it leans back to unload the front paws. |
| Squash / bounce / breathe | All legs together (±10 mm height range) |
| Nod / look up at you | Front vs rear legs |
| Curious head-tilt | Left vs right legs. The body is the head, so this is a real head tilt. |
| Bow / kneel | Front legs swing forward-up and the round chin settles on the desk |
| Wave a paw | Lifts the front-left leg on 3 wheels. Static margin is 3.1 mm; the firmware leans right/back first. See `wave_happy.png`. |
| Wiggle / dance | Alternating leg pumps plus wheel jiggles |
| Paw over a cable, paw onto a 15 mm book | Front paw lifts up to 27 mm (22° → 82°) |
| Catch reflex | When the IMU sees a fore/aft tip starting, the paws swing out. This raises the tip angle from 35°/31° to 56°/54°. |

![wave](final/wave_happy.png)

## 3. Torque check (worst cases; `calc.py`, `calc.json`)

Assumptions:
- Mass 0.301 kg.
- MG90S on a 5.6 V rail: stall ≈ 0.20 N·m.
- N20 6 V 100 rpm: stall ≈ 0.10 N·m (conservative).
- "dyn" = static × 2 (or × 1.5 for slow moves).

| Case | Static | Dynamic | % stall (dyn) |
|---|---|---|---|
| Stand, 4 wheels, legs 22° (lever 12.7 mm) | 9.4 mN·m | 18.8 | 9 % |
| Paw wave on 3 wheels (one leg takes W/2) | 18.8 | 37.6 | 19 % |
| Stand up from the belly, wheel touchdown at 60°, 4 legs share | 21.7 | 32.6 | 16 % |
| Same, only 2 legs share (worst) | 43.5 | 65.2 | **33 %** |
| Leg sweep while lying on its side (μ 0.5, half weight on the leg) | 25.1 | 37.6 | 19 % |
| Step-up: front paw on a 15 mm book, rear pushes | 28.8 | 57.6 | 29 % |
| N20: accelerate 1 m/s² | 2.3 | — | 2 % |
| N20: 15° ramp | 5.7 | — | 6 % |
| N20: spin in place, front paws skidding (μ 0.8) | 13.7 | — | 14 % (7 % leaning back) |

- Every case stays within the research rule (dynamic ≤ 60 % of stall).
- The rear wheels have enough traction for the skid spin: 0.39 N needed against 0.66 N available per wheel.

## 4. Self-righting (`verify_righting.py` → `righting.json`, `selfright.py` → `selfright.json`)

The body is a hacıyatmaz egg: round lower half (R 48 in front view) and the battery at the very bottom. Method:
- A rigid-body support-function analysis on the real geometry.
- The CoM height over every "down" direction is computed, and the robot is followed downhill while the legs move slowly (2° grid, quasi-static).

**Side falls** (the common case for a wide wheeled robot that is bumped or turning):
- In its standing pose a side fall comes to rest at **pitch 8°, roll 84°**: on its side, propped up by the lower wheels.
- Firmware sequence: |roll| > 60° for 0.3 s → swing **only the lower-side legs** (front 80°, rear 120°) out of the round outline → the egg rolls itself to **(14°, 38°)** on its round belly → all legs sweep back down → **stands at (0°, 0°)**.
- This was checked for both sides and for landings pitched −15°/+15°.
- **Margin:** front 75° / rear 120° and front 80° / rear 115° still work. Front 70° and rear 110° do not. That leaves about 5° per joint in hand.
- Torque is 19–33 % of stall (table above). Total sequence time is about 1.5 s.

![righting](final/righting_strip.png)

**Fore/aft and upside-down:**
- *Prevented* by:
  - a 22° stance (tip angles 34.7° forward, 31.4° back, 38.3° sideways)
  - the paw-catch reflex (56°/54°)
  - the chin cliff sensors (it never drives off an edge)
- Upside down it cannot rest: the CoM is far below the round top. However, the analysis shows it then tips onto its **back** (settles at pitch 98°), so it lands in the unrecovered case below.
- **Not guaranteed:** a face-down, back-down or upside-down landing, e.g. when it is dropped. A bottom-mounted 1-DOF leg cannot reach over a round back. The search over all symmetric leg paths shows a reach of about 165° would be needed. In that case it rocks ±40°, shows sad eyes and chirps for a hand.
- A candidate fix, not analysed yet, is a fifth servo: a short "tail lever" at the upper back (about +126 TL).

## 5. Face and expression

- **Screens:** 2 × GC9A01 1.28" round IPS (240×240, Ø32.4 active).
  - Each sits in a counterbored seat in the visor, axis about 21° outward, so the glass rim is hidden under the visor edge.
  - The background is pure black, so the panel disappears into the black visor and only the eyes glow.
- **Procedural eyes** (`eyes.py`, `tex/`). Each eye is drawn from parameters every frame (LovyanGFX sprites with DMA, about 40 fps with partial updates):
  - gaze x/y
  - oval size
  - pupil size
  - lid height and lid angle
  - squash
  - sparkle

  The parts of the eye:
  - **Iris:** hazel ("fındık gözlü"), golden near the pupil, darker toward the rim.
  - **Pupil:** large.
  - **Sparkles:** two white highlights.
  - **Halo:** a soft amber glow so the eye reads on the black visor.
- **Emotions** in the sheet: neutral (looking up at you), happy (^^ glowing arcs and sparkles), curious (asymmetric lids plus a star sparkle), sleepy, sad (outer lids drop), blink (squash). Body language amplifies each one:
  - happy = bounce and wiggle
  - curious = head-tilt plus a slow approach
  - sleepy = a slow breathing sink onto the belly
  - sad = nose down
- **Cheeks:** blush LEDs glow on happy or touch.
- **Sound:** 32 mm speaker behind the back grille for chirps and TTS.
- **Touch:** TTP223 pads on the head (inside the cap) and the back.

![eyes](final/eyes_sheet.png)

## 6. Electronics (all Turkish stock; see the BOM)

- **ESP32-S3 N16R8 devkit** (8 MB PSRAM holds two 240×240 frame buffers), lying flat at 62 mm height. It is reached by lifting the magnet-held caramel cap; OTA updates over Wi-Fi.
- **Claude:**
  - The ESP32 calls the Messages API over HTTPS with tool calls (`move`, `emote`, `say`) through a small phone/PC proxy that holds the key.
  - Voice goes through the phone, or through the INMP441 + MAX98357A with a xiaozhi-style server.
- **Sensors:**
  - BMI160 IMU at the body centre
  - 2 × TCRT5000 cliff sensors in the chin, looking 45° down and ahead (about 17 mm in front of the front paws)
  - 2 × TTP223B touch modules
- **Pin plan (ESP32-S3; GPIO 35–37 are left free for the octal PSRAM):**
  - servos FL/FR/RL/RR → GPIO 4/5/6/7 (LEDC, 50 Hz)
  - DRV8833 AIN1/AIN2/BIN1/BIN2 → GPIO 15/16/17/18 (MCPWM); nSLEEP → GPIO 8
  - SPI SCK 12, MOSI 11, DC 13, RST 14, CS-L 10, CS-R 9; backlight PWM 21
  - I2C SDA 47, SCL 0 (pulled up)
  - I2S BCLK 39, WS 40, amp DIN 41, mic DOUT 42
  - TCRT digital outputs → GPIO 45/46 (low at boot is fine)
  - touch → GPIO 1/2; VBAT ADC → GPIO 3 (100k/33k divider); WS2812B → GPIO 38
- **Fit:** the CAD check finds 0 mm³ interference between the internals and the shells or legs in the standing pose. See the annotated x-ray.

![xray](final/xray_annotated.png)

## 7. Power

- **Pack:** 2S Li-ion, 2 × Orion 14500 900 mAh 3C (7.4 V, 6.7 Wh, 42 g).
  - It lies flat at the lowest point under the servo cases. It is the hacıyatmaz ballast.
  - Protected by a 2S 4.5 A BMS.
- **Charging:** 2S USB-C charger with the port in the lower back. *Set its current to ≤ 0.9 A (1C)*; the stock module is rated up to 4 A.
- **Rails:**
  - MP1584 #1 → 5.6 V for the servos, with 1000 µF.
  - MP1584 #2 → 5.0 V for logic and audio, behind an SS14 diode and 470 µF hold-up, so servo dips never brown out the ESP32.
  - The N20s run from the pack through the DRV8833 (PWM ≤ 80 %).
- **Peak pack current:** 2.0 A for the stand-up, 1.8 A for spinning. Both are within the 2.7 A (3C) cell rating. The all-stalled fault case (4.3 A) trips the BMS.
- **Runtime:** about 1 h of active play, about 4.6 h standing idle, about 6.6 h sitting idle (servos detached, belly on the desk).

## 8. Mass breakdown (model, g)

| Item | g |
|---|---|
| Shell (cream body + caramel cap + ears) | 52.0 |
| Visor and nose | 3.5 |
| Legs (arms, boots, hubs, tyres; arms at 50 % infill) | 47.0 |
| 4 × MG90S | 53.6 |
| 2 × N20 | 19.0 |
| 2 × 14500 | 42.0 |
| ESP32 devkit, 2 × GC9A01 | 22.0 |
| Speaker, amp, mic, IMU, DRV8833, 2 × MP1584, BMS, charger, 2 × TCRT | 31.0 |
| Inner chassis | 8.7 |
| Wires, screws, inserts, magnets, caps, LEDs, horns | 24.0 |
| **Total** | **≈ 301** |

## 9. Printability (FDM, PLA/PETG/TPU, walls ≥ 1.6 mm, shell 1.8 mm)

| Part | Material | Orientation / support |
|---|---|---|
| Body (cream: face ring, belly, sockets) | matte PLA, 0.12 mm layers on domes | Split face down, dome up. Tree supports only inside the four socket cups (hidden). |
| Cap (caramel) | matte PLA | Split face down, dome up. No supports. |
| Ears (caramel shell + cream insert) ×2 | PLA | Flat. Glued and pinned into the cap. |
| Visor | black PETG | Outer face up, ironed or lightly sanded with 2K clear. A studio resin print is an option (+~150 TL). |
| Arms with boots ×4 | caramel PLA, 50 % gyroid | Flat on the hub face (boot axis vertical). No supports. |
| Hubs ×4, hubcaps ×4 | cream / caramel PLA | Flat. The toe-beans are 4 tiny cream inserts, or embossed in one colour. |
| Tyres ×4 | black TPU 95A | Flat |
| Inner chassis (servo cradles, battery tray, deck) | any PLA/PETG | Flat. Screws hold the servos' upper ears; the lower ears are trimmed. |

- Fasteners are hidden: the body screws to the chassis from inside the sockets and from under the belly, and the cap is held by 4 × 6×2 mm magnets.
- Board LEDs are blacked out (1.8 mm walls).

## 10. BOM (TL, KDV incl.; shop stock checked in the research scrape)

| Part | Qty | Unit | Line | Shop |
|---|---|---|---|---|
| MG90S 180° metal-gear (4 + 1 spare) | 5 | 125.80 | 629.00 | Robotistan |
| N20 6 V 100 rpm gearmotor | 2 | 178.56 | 357.12 | Robo90 (q=28) |
| DRV8833 2-ch driver | 1 | 75.75 | 75.75 | Motorobit |
| ESP32-S3 N16R8 devkit | 1 | 610.23 | 610.23 | Direnc |
| GC9A01 1.28" round IPS | 2 | 351.50 | 703.00 | Robotistan (q=19) |
| BMI160 IMU | 1 | 127.86 | 127.86 | Direnc |
| TCRT5000 module | 2 | 52.31 | 104.62 | Direnc |
| TTP223B touch | 2 | 17.86 | 35.72 | Robo90 |
| WS2812B LED | 2 | 6.00 | 12.00 | Robolink |
| INMP441 mic | 1 | 145.29 | 145.29 | Direnc |
| MAX98357A amp (brief price, not re-verified; Adafruit fallback 740.38) | 1 | 309.00 | 309.00 | Amazon.com.tr |
| Speaker 8 Ω 1 W 32 mm | 1 | 51.51 | 51.51 | Motorobit |
| Orion 14500 900 mAh 3C | 2 | 105.48 | 210.96 | Direnc |
| 2S 4.5 A BMS | 1 | 66.66 | 66.66 | Motorobit |
| 2S Type-C charger | 1 | 78.00 | 78.00 | Robolink |
| MP1584 3 A buck | 2 | 53.22 | 106.44 | Robotistan |
| Misc (switch, caps, SS14, wire/JST, screws, inserts, magnets, axles) | — | — | ~250 | est. |
| **Parts** | | | **3,873** | |
| 3D print at a studio (~200 g PLA, PETG visor, TPU tyres) | | | ~750 | est. |
| Shipping (5 shops) | | | ~300 | est. |
| **Total** | | | **≈ 4,923 TL** | |

Cost-downs:
- Drop the spare servo: 4,797 TL.
- Leave out the on-robot audio and use voice through the phone: 4,417 TL.

## 11. What is new here

1. **A wheel-leg robot that is also a hacıyatmaz.** The round egg with its battery ballast does most of the self-righting. The legs only have to get out of the way (lower-side legs swing fore/aft) and then stand up. This was verified quasi-statically, not just claimed.
2. **The body is the head.** Four 1-DOF wheel-legs give nod, tilt, squash/stretch and (through the wheels) pan. That is Keepon's expressive set without a neck servo, so the build needs only 6 actuators, fewer than Sesame's 8 servos, yet it rolls at 16 cm/s, waves and gets up from side falls.
3. **Twin round "fındık gözlü" eyes floating in a peanut visor.** Two cheap GC9A01s read as real animal eyes, not as a screen in a box.
4. **Only the rear paws are driven.** The front paws are free, so posture moves need no wheel/leg coordination and cost 2 fewer motors.

## 12. Risks and next steps

- **Back/face/upside-down landings are not recovered** (see §4). Mitigation: the catch reflex and cliff sensors; a fifth "tail lever" servo is a possible fix (not analysed yet).
- **The righting margin is quasi-static** (about 5° per joint). Next step: simulate the "tuck & roll" in MuJoCo with tyre and shell friction, then test the hardware with a stopwatch.
- **Packaging is tight:**
  - the eye PCB rim sits about 1–2 mm from the front servo cases
  - the lower MG90S ears must be trimmed
  - the hip spline carries the leg's side load, so add a printed bearing ring in the socket cup, in the spirit of the research's "second support" rule.
- **GC9A01 module shape varies.** The model assumes a Ø38.6 round PCB with the header pins removed (wires soldered to the pads). If the Robotistan module has a large tab, use the Motorobit round-PCB version (545.40 TL each, +388 TL).
- **3-wheel wave margin is only 3.1 mm.** The firmware must lean before lifting.
- **Charger current** must be set to ≤ 1C. **MAX98357A** price not re-verified (fallback 740 TL).
- **Glossy visor finish** needs post-processing to look premium.
- **Narrow drive base:** with free front paws, spins skid the front tyres. That is fine on a desk, but it gets worse on rubber mats.

## 13. Files (`/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_C2/`)

**Scripts:**
- `model.py`: build123d parametric model. Poses: stand, tuck, wave, xray. Writes STLs per material, `info.json` (mass, CoM, interference check).
- `eyes.py`: procedural eye frames (`tex/`)
- `scene.py`, `render_final.sh`: renders
- `annotate_xray.py`: x-ray callouts
- `righting_strip.py`: the 3-frame righting strip
- `explore.py`, `verify_righting.py`, `selfright.py`: self-righting analysis (`righting.json`, `selfright.json`)
- `calc.py`: torques, power, BOM (`calc.json`)

**Model outputs** (STL per colour/material, plus `int_*` internals):
- `stl/`: standing pose
- `stl_tuck/`: righting pose
- `stl_wave/`: happy wave pose

**Renders** (`final/`):
- `hero.png`, `front.png`, `side.png`
- `wave_happy.png`
- `xray.png`, `xray_annotated.png`
- `righting_strip.png`
- `eyes_sheet.png`
