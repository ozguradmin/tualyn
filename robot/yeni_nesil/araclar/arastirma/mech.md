# Mechanism research: desk walker (10-15 cm, 200-350 g) that walks well and gets back up

Date: 2026-10-24. Numbers come from the scripts in `research/calc/`:
- `mech_calc.py`: joint torques, the roll-over geometry, power
- `roll_stability.py`: passive roll stability of a cross-section
- `cost_and_checks.py`: costs, mass, and the checks for the picked designs

Prices are the verified guide prices (TL, KDV included). "est." marks an unverified price.

## 0. Ground rules used in every calculation

| Servo | Stall torque 4.8 V / 6 V | Stall current | Mass | TL |
|---|---|---|---|---|
| SG90 | 0.176 / ~0.176 N·m | ~0.65 A | 9 g | 82.25 |
| MG90S (180°, plastic inner gear stage per guide) | 0.177 / 0.216 N·m | ~0.75 A (≈1 A at 6 V) | 13.4 g | 125.80 |
| ES08MA II | ~0.157 / ~0.196 N·m | ~0.75 A | 12 g | 424.20 |

- **Design rule.** Static holding should stay at or below 30 % of stall. Peaks, computed as static × 2 to cover acceleration and impact, should stay at or below 60 %. Above that the servo buzzes, heats up and loses position.
- **Servo rail voltage.** Run the servos at about 5.5 V, not 4.8 V. That gives about 0.20 N·m on an MG90S, or 10-20 % more margin for free.
- **Torque formula.** Worst-case torque = (m·g / number of supporting legs) × horizontal lever from the joint axis to the foot contact.
- **Load cases.** A trot or diagonal-pair gait puts m·g/2 on each stance leg. A 4-leg stand puts m·g/4 on each.
- **Shaft bending.** Every hobby servo shaft that carries a leg needs a second, coaxial support (a printed pin or M2 screw on the opposite side of the bracket). Sesame and Bittle both do this. Without it the plastic case cracks before the gears do.

## 1. Sesame-style spider legs (hip yaw + knee, 8 servos)

**Geometry.** Sesame STLs measured with trimesh:
- Thigh bracket (R1/L1): 49.5 × 30.5 × 20.3 mm
- Foot (R3/L3): 58.4 mm
- Internal frame: 79 × 68 × 16 mm
- Top cover: 38 mm tall

That gives a coxa of about 35 mm (hip axis to knee axis) and a foot of about 52 mm (knee axis to tip). The firmware stand pose puts the knees at 0/180 (servo end stops) and rest at 90. So **the 180° knee already sweeps from foot-down to foot-up**.

**Torque.** Knee lever = foot length × cos(foot angle below horizontal):

| Case (m = 0.30 kg) | Knee lever | Static | ×2 dynamic | % of MG90S at 6 V |
|---|---|---|---|---|
| 4-leg stand, foot 60° below horizontal | 26 mm | 0.019 N·m | 0.038 | 18 % |
| trot, foot 60° | 26 mm | 0.038 | 0.077 | 35 % |
| trot, foot 45° (crouched) | 37 mm | 0.054 | 0.108 | 50 % |
| belly-flat, foot horizontal (stand-up, trot) | 52 mm | 0.077 | 0.153 | 71 % (87 % on SG90) |

- At 0.35 kg the belly-flat case reaches 83 % of an MG90S and 101 % of an SG90. **Use MG90S at the knees**, keep the stance at 50° or more, and stand up from the belly on all 4 legs (0.077 N·m, 35 %).
- Hip yaw carries no gravity load. Its worst case is foot scrub, μ·F·r = 0.5 × 1.47 N × 0.06 m = 0.044 N·m (×2 = 41 %).

**Walking quality on a desk.** Good and very stable. The stance is wide (about 150 mm foot span) and the CoM is low. The crawl gait is proven by Sesame and Kame32. The body can lean, bounce and yaw as a whole, so the body itself acts as the "head". Walking is slow (a creep). Hip-yaw kinematics scrub the feet a little.

**Self-righting.**
- **Rolling over: NO.** The roll-over model (`spider_roll`) gives:
  - Pushing with one side's knees from an inverted body reaches only 17-38° of roll.
  - Tipping past the far edge needs 53-65°.
  - This held for every geometry tested, from W68/T40/foot 52 to W40/T30/foot 70.
  - The pushing foot can't reach far enough, because the coxa spreads the leg sideways instead of over the back.
- **An inverted, symmetric body solves it: YES.** The knee already sweeps from -90 to +90°, so a body whose two faces are identical can simply walk upside down. Requirements:
  - Knee axis on the body mid-plane.
  - Foot length × sin(stance angle) ≥ T/2 + clearance. With T = 40-42 mm and a 55-58 mm foot at 60°, clearance is 28-29 mm.
  - No tall top cover. Stock Sesame fails here only because of the 38 mm top cover with ears.
  - The IMU sees gravity flip, so firmware swaps the gait sign and rotates the face image 180°.
  - A rounded lens edge means it never rests on its side: on edge the CoM is about 36 mm high on a round edge, so it is unstable and drops onto a face.
- **Costs of the symmetric approach:**
  - No head or ears on top.
  - The face must sit on the front edge, so its height is limited to about 30-38 mm.
  - Cliff sensors are needed on both faces, or one forward-down sensor at the front edge.

**Parts and build.**
- DOF 8.
- Servos 8 × MG90S + 2 spare = 1,258 TL. About 3.2k TL in parts without audio, 3.7k with audio.
- Prints well: mostly flat parts, and Sesame prints without supports.
- Build complexity: low, using the proven Sesame layout.

## 2. Bittle / OpenCat sagittal legs (hip pitch + knee, 8 servos)

### How `rc` (recover) works in OpenCatEsp32

The code is in `repos/PetoiCamp_OpenCatEsp32/src`.

**1. Detection: `imu.h:getImuException()`, around line 840.**
- `IMU_EXCEPTION_FLIPPED` is raised when |roll| (`ypr[2]`) > 85° and gravity along body Z points the wrong way:
  - `xyzReal[2] < 1` for the MPU6050
  - `< -1` for the ICM42670
- Pitch outside -50 to 75° is handled differently, as "lifted" or "dropped" (`IMU_EXCEPTION_LIFTED`). **Only roll falls trigger `rc`.** Nose or tail falls are expected to settle onto the back or side first.

**2. Reaction: `reaction.h:dealWithExceptions()`, line 57.**
- It runs only while `gyroBalanceQ` is true (toggled with the `g` token).
- It plays `soundFallOver()`, sets `token='k'` and `newCmd="rc"`, and sets `manualHeadQ=false`.

**3. Skill loading: `skill.h`, around line 510.**
- Behaviours are **mirrored left↔right on alternate attempts**: `coinFace` toggles, plus a random chance.
- So if a recovery fails against a wall or object, the next try rolls the other way (comment at `skill.h:221`).

**4. The skill: `InstinctBittleESP.h:2387`.**
- Header `-5,0,0,2` means a 5-frame behaviour with **angles stored ÷2** (angleDataRatio 2), because the angles exceed 128.
- Row layout: 16 joint angles, then speed, delay, trigger axis, trigger angle.
- Joint order: 0 head pan, 1 head tilt, 2 tail, 4-7 shoulder roll (unused), 8-11 shoulder pitch (LF, RF, RH, LH), 12-15 knees.

| Frame | Shoulders LF/RF/RH/LH (×2) | Knees (×2) | Meaning |
|---|---|---|---|
| 1 (speed 32, fast) | -176 / -86 / 134 / 200 | 84 / -70 / 84 / 84 | Left legs swing about 180° to point **over the back** and press the desk; right legs stay sideways. The asymmetric push lifts the left edge and the body rolls onto its right side. |
| 2 (fast) | -166 / -176 / 200 / 120 | 84 / 84 / 84 / 100 | All legs go dorsal. On its side, this moves leg mass and keeps the body tipping. |
| 3-4 (speed 16 then 8) | 36 / 36 / 44 / 44 | -28 / -28 / -26 / -26 | All legs snap under the belly into a crouch. The fast swing shifts the CoM, the legs catch the ground and the body falls onto its feet. |
| 5 | 30 for all | 30 for all | `up` (stand). |

- The Nybble version (`InstinctNybbleESP.h:1365`) also uses the head and tail as levers. Frame 1 has head pan +30 and tail +120.

### What geometry and range `rc` needs

- **Shoulder range.** Bittle's `angleLimit` allows shoulders -200..+80 (front) and -80..+200 (hind), about 280° of travel on 270° Petoi P1S servos. The legs must reach **about 140-180° from "straight down"**, pointing over the back.
- **Leg length and body section.** Leg length beyond the back surface must be large compared with body width. Model `sag_roll`:
  - The pushing foot extends L·cos(180° - q_max) - T/2 beyond the back.
  - Achievable roll = atan(reach / pivot distance).
  - Needed roll = atan((W/2 - R_edge) / (T/2)).

| Body W × T, leg L1+L2 = 85, back-edge fillet R | q_max | Reach beyond back | Roll possible / needed |
|---|---|---|---|
| 55 × 40, boxy (R0), Bittle-like with 180° servo window | 180° | 65 mm | 50° / 54° → **NO** (Bittle succeeds dynamically and with 280° travel) |
| 52 × 48, R0 | 140° | 41 mm | 38° / 47° → **NO** |
| **52 × 48, R15** | **140°** | **41 mm** | **48° / 25° → OK** |
| 50 × 50, R18 | 140° | 40 mm | 51° / 16° → OK |
| 56 × 44, R10 | 140° | 43 mm | 43° / 39° → marginal |

**Takeaway:** with 180° hobby servos, self-righting works if:
1. The back edges are rounded (fillet of 15 mm or more), and the section is not boxy.
2. The body is no wider than it is tall.
3. The hip servo's 180° window is offset, so it does not span the usual ±90° around straight down:
   - **front hips -40° … +140°** (forward and up over the head)
   - **hind hips -140° … +40°** (backward and up over the tail)
   - This is an X-config.
   - Walking uses about ±35°, folding uses ±90°, and the dorsal push uses ±140°.
4. Knee window -10 … +170° (one-sided bending).

**Torques for the push.**
- Pivot torque is m·g·(W/2 - R) = 0.031 N·m for the R15 body. That is about 0.5 N per foot, which is trivial.
- From the side to the belly, swinging 4 legs of about 30 g by 35-45 mm moves the CoM 14-18 mm. That is enough when the belly edges are also filleted and the battery sits in the belly, so the CoM is low.

**Torques for walking** (L1 40 / L2 45, hip height 60-70 mm, ×2 dynamic, MG90S at 6 V):

| Mass | Knee | Hip |
|---|---|---|
| 0.25 kg | 7-25 % | 17-28 % |
| 0.30 kg | 8-30 % | 20-34 % |
| 0.35 kg | 9-35 % | 24-40 % |

- From belly to standing: 0.033-0.039 N·m (15-18 %).
- **These are the best margins of any 8-servo layout.** The foot sits under the hip, so the hip carries almost no gravity torque.

**Assessment.**
- DOF 8, plus an optional head-pan servo (9).
- Walking: the best on a desk of all options. Trot, crawl, sit, stretch, paw-wave, and every other OpenCat skill is reusable.
- Self-right: YES, actively, with an adapted `rc` and a rounded body.
- Cost:
  - Parts: 1,258 TL in servos, about 3.2k TL without audio, about 3.7k with audio.
  - All-in: about 3.7-4.7k TL including print and shipping.
- Build complexity: medium. Each leg is a bracket plus a knee-servo thigh plus a shin with a support pin.
- Printability: good. The shell is two halves printed dome-up, and the legs are flat.

## 3. Four-servo designs

**Petoi Quaddle** (Kickstarter Sept 2026; source code and CAD not yet public):
- 1 servo per leg (about 2.5 kg·cm). A passive four-bar plus springs turns hip rotation into a knee-lift step. Each foot tip is a **free rolling wheel**.
- It walks, strafes and spins by phasing the four legs. Self-righting is not mentioned anywhere.
- The URDF on Hugging Face lists 16 revolute joints (4 actuated), 8 continuous (rollers) and 2 springs per leg.
- Sources: [petoi/quaddle](https://huggingface.co/petoi/quaddle), [CircuitDigest](https://circuitdigest.com/news/quaddle-is-an-open-source-desk-robot-that-can-move-omnidirectionally-with-just-4-servos), [Petoi](https://www.petoi.com/pages/quaddle).

**ESP-Hi** (`xiaozhi-esp32/main/boards/espressif/esp-hi`): a 4-servo dog with FL/FR/BL/BR pins and 1-DOF straight legs. It walks by shuffling and scooting.

**Otto** (OttoDIYLib): 4 × SG90, with 2 hip-yaw and 2 ankle-roll servos. It moves by lean-and-twist shuffling.

**Torque.**
- A 1-DOF leg in a trot at 0.30 kg with an effective lever of 10-30 mm: 0.015-0.044 N·m. ×2 that is 14-41 % of an MG90S, or 17-50 % of an SG90.
- Otto's ankle lean (0.25 kg, 22 mm half-foot): 0.054 N·m. That is 31 % of an SG90 at 4.8 V, and about 41 % when run directly from 1S at 3.7 V.

**What 4-servo designs can and cannot do.**

| Can | Cannot |
|---|---|
| Cheap, at 411-755 TL in servos | Place a foot precisely or lift a foot high, so it trips on cables and desk edges |
| Light, about 200-250 g | Make expressive single-leg gestures (only crude ones) |
| Long battery life | Do a static crawl gait, so it hops, scoots and drifts on smooth desks |
| Very robust | Self-right with legs: a 1-DOF leg can't reach over the back, and Otto is a tall biped that always ends up on its face |

- Quaddle-grade walking needs a well-tuned four-bar and springs. That is R&D for us, because the CAD isn't public.
- Self-righting is possible only through **body shape**: a round, roly-poly shell (§5).

## 4. Wheel-leg hybrids

**(a) Driven wheels at the feet.** N20 gear motors cost about 150-250 TL each (est.), plus a DRV8833 at about 80 TL (est.).
- Drive mode is fast, smooth and quiet on a desk, with in-place turns.
- A high-ratio N20 (100:1 or more) is barely back-drivable. With rubber O-ring tyres, a stopped wheel acts as a foot, so the legs can still walk.
- Costs:
  - About 10-12 g per wheel module at the foot tip, which adds knee inertia and torque: +0.005-0.01 N·m.
  - +500-900 TL.
  - Wiring through moving legs.
- Variant: 4 hip servos plus 2 driven rear wheels plus 2 passive front skids. That is about 1.1k TL in actuators, and it drives well but "walks" only as a show.
- Self-righting: only if the hip window reaches over the back (as in §2).

**(b) Passive rollers at the feet (Quaddle).** These let a 1-DOF leg "skate". On a desk they are a **cliff risk**: a push rolls the robot. Use rollers with a ratchet or high friction.

**Verdict.** The user asked for "walks on legs well", so wheels are a secondary mode. Not recommended as the main architecture: it adds cost, mass and a desk-edge risk.

## 5. Self-righting without legs

### 5a. Roly-poly (hacıyatmaz) round-bottom shell

**Spherical bottom of radius R.** The body always rights itself if the CoM is below the sphere centre (h_CoM < R).
- Mass budget for a 280 g egg with the battery and 4 servos low: CoM ≈ 26 mm above the lowest point.

| R | CoM below centre | Righting torque at 90° | At 150° |
|---|---|---|---|
| 40 mm | 14 mm | 0.039 N·m | 0.019 |
| 45 mm | 19 mm | 0.053 N·m | 0.026 |
| 50 mm | 24 mm | 0.066 N·m | 0.033 |

- A perfect sphere with CoM offset e at 0.3 kg: 0.029 N·m at 90°, but **only 0.005 N·m at 170°**. A near-inverted ball can stall on friction or desk texture. Give the top a smaller radius (a pointed egg or a head knob) so "on top" is never a rest.

**Rules for the shell:**
1. Legs must fold flush into recesses so the outline stays round.
2. No flat facet the CoM can rest on. A display needs a domed clear window, or the perpendicular from the CoM must fall outside the facet.
3. The battery goes at the very bottom.

**Print:** two hemispheres, each printed dome-up, so no supports are needed.

### 5b. Rolling about the long axis: cross-section shape matters

`roll_stability.py` counts the stable rest angles of a convex section with the CoM offset e below centre.
- **Boxy sections (superellipse p ≥ 2.5) are ALWAYS stable on their back.** This is the turtle problem; e had no effect in any case tested.
- **True ellipse or round sections (p = 2) become monostable**, meaning only the upright rest survives:
  - 50 × 50 mm with e ≥ 4 mm
  - 45 × 50 mm with e ≥ 8 mm
  - 45 × 55 or 50 × 60 mm with e ≥ 12 mm. With e = 8 these sections still settle at about ±34° from upright, and the legs can finish from there.
- A wide, flat 55 × 40 ellipse stays stable on its back whatever the e.
- **Design rule:** a frontal section that is round or slightly taller than wide, a true ellipse rather than a rounded box, and battery-low CoM (e ≥ 0.3 × half-width). Then the body itself rolls toward upright, and the legs only finish the job.

### 5c. Head or tail lever

A head (or tail) servo swings into the desk. Required servo torque:

| Body | CoM to pivot | Lever | Servo torque | % of MG90S |
|---|---|---|---|---|
| 0.3 kg | 25 mm | 40 mm | 0.060 N·m | 28 % |
| 0.3 kg | 30 mm | 50 mm | 0.074 N·m | 34 % |
| 0.3 kg | 40 mm | 50 mm | 0.084 N·m | 39 % |

- Feasible with one MG90S. A head-pan servo that can swing ±90° sideways doubles as a roll lever, as Nybble's `rc` does. The cost is an exposed neck that takes impacts: use metal gears or a printed slip clutch.

### 5d. Beetle-style wing covers (elytra)

On its back, a domed shell rocks with an energy barrier of only m·g·e (about 44 mJ at e = 15 mm). The push needed is at most 0.044 N·m, but the shell must be pushed past 90° plus atan(e/R) before it falls onto its feet. One servo opening two wing flaps works, and the flaps double as a "happy" gesture. It is a novel look, but it is one more mechanism.

## 6. Other low-servo-count ideas

**6-servo quad with coupled knees.**
- 4 hip servos plus 2 knee servos, each driving one diagonal pair (LF+RH, RF+LH) through a rod or cable across the body.
- Trot and turning work, but there is no crawl, no single-paw gesture and only a weak `rc`.
- Saves 2 servos (about 250 TL, 27 g), but adds a long linkage with backlash.
- **Not worth it.**

**3-servo hexapod walker.** A centre servo rocks the middle legs to lift alternate tripods; 2 servos swing the front and back legs.
- Classic and reliable, with an insect shuffle. Centre-servo torque is about 0.05 N·m (fine on an SG90).
- About 2.4-2.9k TL in parts.
- No self-righting and no gestures. Cute only as a bug.

**5-bar legs with all 8 servos inside the body** (Minitaur/Doggo-style, non-coaxial pairs):
- Legs become thin linkages that fold flat, so a round roly-poly body and full 2-DOF legs are both possible.
- Also the best mass distribution, with a low CoM.
- It is R&D work: joint pins, backlash, and servo pairs spaced 15-20 mm.
- Keep it as a stretch variant of pick #1.

## 7. Power, battery fit and brownout

**Current.**
- 8 × MG90S: walking average about 1.4-2.4 A. Get-up or `rc` peak, with half the servos near stall, is about 4.2 A at 5.5 V (about 23 W). The theoretical all-stall is 6 A.
- 9 servos: about 4.7 A peak.
- 4-5 servos: about 2-2.5 A peak.
- ESP32-S3 Wi-Fi TX bursts: about 0.35-0.5 A at 3.3 V. LCD backlight: about 30-60 mA. MAX98357A peaks: up to about 0.5 A at 5 V.

**Battery options that fit:**

| Option | Size / mass | Energy | Verdict |
|---|---|---|---|
| **2S 14500 Li-ion** (2 × 105.48 TL) + 2S BMS 45.24 + 2S USB-C charger 78 | 2 × Ø14.2 × 50 mm, about 42 g; flat pack 29 × 14.5 × 50 | 5.9-7.4 Wh → about 40-50 min walking, about 2-2.5 h idle or talking | **Recommended.** Same as Sesame's pack. Fits a 48-52 mm wide belly or a 40 mm lens body. The cells must be high-drain (IMR, about 4 A or more): **verify the shop's cell rating**, because cheap "1200 mAh" 14500 cells are 1C. The BMS must be rated ≥ 5 A continuous. |
| 2S 18650 (2 × 153.43, 15C) | 2 × Ø18.5 × 65 mm, about 90 g | 14.8 Wh | Electrically the best, but +50 g pushes servo margins (0.35 kg rows above) and needs a body at least 70 mm long. Only for pick #1 if length allows. |
| 1S 18650 15C + 5 V boost | 45 g | 7.4 Wh | The cell is fine, but a 5 A 5 V boost is not in the verified list (XL6009 ≈ 1.5-2 A max). **One sagging 1S rail for servos and ESP32 is the classic brownout trap.** |
| 1S LiPo 1000 mAh (215.30) | flat | 3.7 Wh | Too weak for 8 servos (1-2C). Fine for logic only. |

**Keeping the ESP32 from browning out.**
1. **Separate rails.** Use 2 × MP1584 at 5.5 V for the servos, one per 4-servo bank (3 A peak each), or one XL4015 5 A (98.80 TL). Use a third MP1584 at 5.0 V into the devkit 5V pin, so the on-board LDO makes 3.3 V. Three MP1584 cost 159.66 TL and are each 22 × 17 mm. MP1584 needs Vin ≥ Vout + about 1 V, so set the low-battery cutoff at 6.6 V under load.
2. **Hold-up on the logic rail.** Put an SS14 Schottky in series into the logic buck, with 220-470 µF after it, so battery dips during servo inrush never reach the ESP32. Add 100 µF plus 100 nF at the devkit.
3. **Servo bulk capacitance.** 1000 µF / 10 V low-ESR per bank, as in Sesame's BOM, plus 100 nF at the headers.
4. **Star ground.** Servo return current must not flow through the ESP32 ground.
5. **Firmware:**
   - Attach servos one by one, 60-100 ms apart, at boot.
   - Limit slew rate to about 300°/s.
   - Never command 8 large moves in the same tick: stagger by about 5 ms.
   - Stop PWM (detach) on idle servos while lying or charging.
   - Pause audio and Wi-Fi bursts during `rc` and stand-up.
   - Read battery voltage on an ADC through a divider.
   - Leave the brownout detector enabled; design so that it never trips.
6. **PWM channels.** The ESP32-S3 has only **8 LEDC channels**. With 9 servos plus backlight, drive the servos from **MCPWM** (2 units, 12 outputs), or add a PCA9685 (245.54 TL). Sesame's 8 servos on LEDC leave no channel for backlight PWM.

## 8. Comparison

| Architecture | Servos | Walk on desk | Self-right | Torque margin, worst ×2 (0.3 kg, MG90S) | Parts TL (no audio / with) | Build | Print |
|---|---|---|---|---|---|---|---|
| Spider, stock Sesame | 8 | good, slow | no | 50-71 % (knee crouched or flat) | 3.2k / 3.7k | easy | easy |
| **Spider, ambidextrous lens body** | 8 | good, slow | **not needed** (walks either side up) | 35-50 % | 3.2k / 3.7k (+0.5k with Waveshare 1.47" board) | easy | easy |
| **Sagittal (Bittle-type), rounded body** | 8 (+1 head) | **best** | **yes**, active `rc` plus shape | 30-40 % | 3.2k / 3.7k | medium | medium |
| Quaddle-like 1-DOF + rollers | 4 | fair (skate or scoot) | only with roly-poly shell | 14-41 % | 2.5k / 3.0k (5 servos with head: 2.65k / 3.16k) | four-bar R&D | easy |
| Otto biped | 4 (SG90) | poor (shuffle) | no | 31-41 % (ankle) | 2.3k / 2.8k | easy | easy |
| Wheel-leg (4 hips + 2 N20) | 4 + 2 motors | drives great, walks weakly | partial | about 30 % | 3.0k / 3.5k (est.) | medium | medium |
| 6-servo coupled knees | 6 | fair (trot only) | weak | about 35 % | 2.8k / 3.3k | linkage pain | medium |
| 3-servo hexapod | 3 | fair (insect) | no | about 30 % | 2.4k / 2.9k | easy | easy |
| **Roly-poly egg, 4 legs + head** | 5 | fair | **yes, passive in all directions** | 14-41 % | 2.65k / 3.16k | medium | easy (dome-up halves) |

- Core electronics in every row (1,899 TL): ESP32-S3 N16R8 610.23, GC9A01 351.50, MPU6050 193.53, 2 × 14500 210.96, 2S BMS 45.24, 2S charger 78, 3 × MP1584 159.66, cliff IR × 2 (about 50, est.), misc (about 200, est.).
- Audio adds 506 TL: INMP441, MAX98357A, speaker.
- Touch costs about 0 TL: ESP32-S3 native touch pins with copper foil inside the shell.
- Printing adds 350-900 TL and shipping about 150 TL.

## 9. Recommendation: top 3

### #1: "Bean" sagittal quadruped (OpenCat lineage) with a rounded, roll-friendly body and a head pan

**Why it ranks first:**
- It walks best: trot, crawl, sit, stretch, wave.
- It has the largest servo margins: 30-40 % worst case at 0.30-0.35 kg.
- Self-righting is proven in firmware (`rc`). We port the frames with new angle windows, and keep the mirror-on-retry logic.
- A dog or cat pose language gives it character.
- The head-pan servo doubles as a roll lever.

**Key dimensions:**
- **Body:** about 96 × 52 × 48 mm (L × W × T).
- **Frontal section:** ellipse or round (not a rounded box), back and belly edge fillets ≥ 15 mm.
- **CoM:** at or below 0.3 × half-width under the section centre. The 2 × 14500 pack goes lengthwise in the belly.
- **Hip axes:** at mid-height, ±35 mm fore and aft (70 mm spacing).
- **Legs:**
  - L1 (hip to knee) 40 mm, L2 (knee to foot) 45 mm, plus a 3 mm TPU or rubber toe.
  - Hip height 62-68 mm when standing.
  - Front hip window -40…+140°, hind hip window -140…+40°, knee window -10…+170°.
  - X-config knees.
- **Head:** about 40 mm, carrying the round 1.28" GC9A01 face, on 1 pan servo (SG90 is enough).
- **Overall:** about 140 L × 70 W (including leg pods) × 105-115 H mm. Mass about 320 g.

**Cost:** 9 servos + 1 spare (1,258 TL). About 3.2k TL in parts without audio, 3.7k with audio, 3.7-4.7k all-in.

**Validate next:** run the roll-righting in MuJoCo with these exact windows before CAD sign-off.

### #2: "Two-faced" ambidextrous spider (Sesame lineage) with a symmetric lens body

**Why it ranks second:**
- Simplest mechanics and the most stable walk, with the widest stance.
- It never needs to self-right, because it walks either side up. The IMU flips the gait and the face.
- Sesame's knee range already allows it; the stock top cover is the only obstacle.
- It is the most robust and lowest-risk build.

**Key dimensions:**
- **Body:** a lens about 80 × 72 × 40-42 mm, mirror-symmetric top and bottom, with a round edge so it can't rest on its side.
- **Hip yaw servos:** vertical, at the corners.
- **Coxa:** 32-35 mm. Knee axis exactly on the mid-plane.
- **Foot:** 55-58 mm. The 180° knee centre is the horizontal.
- **Stance:** foot 55-65° below horizontal, giving 28-30 mm body clearance on either face.
- **Footprint:** about 150 mm span.
- **Face:** on the front edge. Options:
  - 0.96" OLED (27 mm)
  - Waveshare ESP32-S3 1.47" 172×320 board in landscape (about 22 mm tall) as a visor. It includes the S3 and a QMI8658 IMU, so the MPU6050 and the separate devkit go away: +about 480 TL net.
- **Cliff sensing:** one IR sensor per face, chosen by the IMU.
- **Mass:** about 300 g.

**Cost:** 8 servos + 2 spare (1,258 TL). About 3.2k TL in parts without audio, 3.7k with audio.

**Trade-off:** no moving head. The whole body leans, bounces and yaws as the expression instead.

### #3: "Hacıyatmaz" roly-poly egg, 4 legs + 1 head servo

**Why it ranks third:**
- Passive self-righting in **every** direction (roll and pitch) with zero code, which makes it the most robust.
- It is the cheapest and lightest.
- As far as I know it has not been done as a hobby walker, and the Turkish hacıyatmaz toy makes it instantly readable and cute.

**Key dimensions:**
- **Bottom:** spherical, R = 45 mm, so the egg is about 90 mm in diameter and about 105-110 mm tall.
- **CoM:** about 26 mm above the lowest point, which is 19 mm below the sphere centre. The battery sits at the bottom pole and the 4 hip servos in the lower hemisphere.
- **Righting torque:** 0.053 N·m at 90°.
- **Top:** the head dome, with a smaller radius so "upside down" is never a rest. It rotates on 1 servo, and the face sits behind a domed clear window.
- **Legs:** 4 × 1-DOF legs of about 45-50 mm, folding flush into recesses (Quaddle-style four-bar foot lift if time allows, straight legs otherwise).

**Cost:** about 2.65k TL in parts without audio, 3.16k with audio, 3.2-4.2k all-in. Mass about 250 g.

**Trade-off:** walking is only "fair": scoot or creep, with no precise steps. Upgrade path: the 5-bar, all-servos-inside variant (§6) gives 2-DOF legs in the same round shell, but that is R&D.

**Hybrid worth testing.** #1 with an elliptical frontal section and the knee servos recessed into side pockets gets #3's passive roll bias plus `rc` as backup. That would be the strongest single answer to "walks best and always gets up".
