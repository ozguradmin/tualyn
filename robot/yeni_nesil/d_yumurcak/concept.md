# Concept D2: "Yumurcak", the egg that hatched legs

**Tagline:** *It wobbles, it falls, it gets back up, and then it looks proud of itself.*

**Character.** In Turkish *yumurcak* means "little rascal", and the word comes from *yumurta*, egg.
- Yumurcak is a hatchling that has only just broken out of its shell.
- It still wears the top of its eggshell as a cap, tilted at a jaunty angle.
- It is curious, a bit clumsy, and cheeky.
- It looks at you with two big round eyes floating in a dark glass visor.
- When it is happy it lifts one chubby paw to wave.

**Proportions.** The look is an upright egg with stubby limbs, like EVE crossed with a baby chick:
- warm-ivory egg
- yolk-orange cap, haunches and paws
- black glass face

## Renders (final/)

| File | What it shows |
|---|---|
| `hero.png` | Standing, 3/4 view, neutral eyes |
| `front.png`, `side.png` | Orthographic-like front and side views |
| `happy_wave.png` | The emotion: happy squint eyes, head turned 30° on the oblique joint, front-left paw raised to wave |
| `xray.png` | Back x-ray with callouts showing how every real part fits |
| `self_righting.png` | Storyboard of the three-move self-righting manoeuvre, taken from the simulation |
| `eyes_sheet.png` | Eye frames: neutral, happy, curious, sleepy |

There were nine work-in-progress render rounds, kept in `wip/`. Main changes between them:
- capsule haunches → ball haunches, because the capsules read as boxy wedges
- socketed goggle eyes → floating eyes
- a quiff on top → the eggshell cap
- lemon accent → yolk-orange accent
- knee moved up and paws lengthened to 48 mm, because the self-righting simulation failed with 33 mm paws
- visor normal-smoothing artefacts fixed

## 1. What is new (the wildcard)

1. **A walking egg on "turret haunches".** The proven Sesame leg topology (hip-yaw + knee, 8 × MG90S) is repackaged so that no generic servo, bracket or horn is visible.
   - Each hip is a 41 mm ball that turns in place about its own vertical axis. A sphere spinning on its own axis never changes its outline, so the gap around it stays a constant 0.7 mm circle while it walks.
   - The knee servo sits inside the ball, and the paw comes out of a round joint plate on its flank.
   - Sesame-class gait quality, with none of the "kit" look.
2. **A one-servo oblique head (the Jibo trick, applied to a walker).**
   - The head is the upper egg above a seam tilted 12°. The seam is a circle on the spherical zone of the egg, so the head turns without a gap ever opening.
   - One SG90 turning the head ±60° about that tilted axis produces yaw 58°, a curious head tilt of 10.4° and a look-up of 5.8° all at once (computed).
   - The tilted cap swings with the head and makes the tilt read even more strongly.
   - The result is three apparent degrees of freedom from one servo, with no neck, no exposed joint and a continuous egg silhouette.
3. **Self-righting tuned to the egg's shape, verified in a model rather than hoped for.** The research finding (§5b of the research) was applied: a round section and a low CoM roll the body toward upright, and the legs finish the job.
   - All batteries and servos are low. The CoM is 14.7 mm below the centre of the egg's bottom sphere.
   - When the robot tucks its paws, the side-rest energy barrier drops from 23 mm to 8 mm of CoM lift.
   - The paws are shaped, toe-in and long enough to push from above the CoM. Short 33 mm paws provably fail.
   - The convex-hull rolling model recovers from **7 of 7 fall directions**, including the upside-down landing.
4. **"Hatchling" behaviour that is built into the hardware.**
   - It sits in a nest pose on its four haunch balls to charge (USB-C at the back).
   - It shows sleepy eyes at rest.
   - It treats every fall as a little show: oops eyes, push, tip over, shake off, happy eyes.

## 2. Dimensions, mass and stance

| | Value |
|---|---|
| Egg body | Ø96 × 106 mm, plus a 2 mm cap. The bottom is a sphere of R 48; the top is a prolate tip (R≈22 at z+50) so it can never rest on its head. |
| Overall standing size | **107 W × 122 D × 146 H mm** (paw to paw, including the cap) |
| Footprint (sole centres) | 89 × 97 mm. Stance angle 30°. Lateral static tip-over angle 35°. |
| Mass (`check.json`, itemised) | **346 g** |
| CoM | 62.6 mm above the desk; 14.7 mm below the egg's sphere centre |
| Head share of height | Head (above the seam) ≈ 51 % of height |
| Legs below the egg | ≈ 20 % of height (toddler stumps) |
| Eye line | ≈ 39 % up the head front, which reads as a big forehead and a baby face |

**Mass breakdown (g):**

| Part | Mass (g) |
|---|---|
| Shells (body 19.2, head 21.4, visor 6.2, cap 4.9) | 52 |
| Haunch balls | 36 |
| Paws | 28 |
| 8 × MG90S | 107 |
| SG90 | 9 |
| Horns and screws | 10 |
| 2 × 14500 cells | 41 |
| Deck, collars and sled | 9 |
| 2 × GC9A01 displays | 12 |
| Boards and power modules | 18 |
| Wiring and capacitors | 16 |
| Hardware | 8 |

## 3. Mechanism and DOF: 9 servos (8 × MG90S legs + 1 × SG90 head)

**Leg (×4), at the egg's lower diagonals (±24, ±24):**
- **Hip-yaw (MG90S):** vertical, shaft down, clamped in a printed deck. Its horn sits in a pocket in the top of the ball.
  - Second support: a PTFE-lined printed collar grips the ball's top boss, so leg bending loads bypass the servo, as research §0 requires.
  - The ball turns ±30° to walk and up to ±85° to aim a push.
- **Knee (MG90S):** inside the ball, with tabs trimmed and the case clamped.
  - The shaft runs along ±Y at the top of the case, at z = −30.5 (5.5 mm above the ball centre). This higher pivot is what lets the paw push head-ward.
- **Paw:** a 48 mm bean leg (knee axis to sole) with the toe turned in and a TPU sole.

**Gait (Sesame/Kame32 firmware family):**
- Yaw moves the foot tangentially (radius 31.8 mm); the knee lifts it outward.
- Stride: ±25° yaw → 27 mm per step. Foot lift: knee 30° → 55° raises the sole 14 mm.
- Trot at 1.5 Hz gives ≈ 4 cm/s. A crawl uses the 89 × 97 mm support polygon.
- Turn in place: yaws in phase.
- Body lean and nod come for free from differential knees.
- Every leg can aim its paw in any horizontal direction (yaw ±85°), which the righting manoeuvre uses.

**Head:**
- An SG90 rides in the head with its horn fixed to a central core post. The 12° oblique axis passes through the seam centre.
- The head rests on a PTFE-taped lip at the seam, so the servo only provides torque.
- A 10-wire ribbon passes through the hollow post (±60° twist).
- The whole head sweep (displays and head servo, −60…+60°) was checked against every fixed part: interference 0.05 mm³, which is numerical noise.

**Fit check** (`check.py`, OCC booleans): 0 mm³ interference for every pair checked, including:
- servos vs servos, shell, cells, deck and haunch walls
- electronics vs shell and servos
- paws vs shell
- displays vs visor

## 4. Self-righting: numbers (`righting.py`, `righting.json`)

**Method.** A convex-hull rolling model. Potential energy is m·g·h(d), where h is the support function of the full exterior hull about the CoM, sampled over 14,000 directions.
- Stable rests are the local minima.
- Barriers to upright come from a merge tree.
- The manoeuvre is quasi-static: after each 5° knee step the body rolls by steepest descent to its new rest.

**Rests.**
- Standing: side rests at 95–111° tilt, barrier 22–26 mm (≈ 75–89 mJ). Legs splayed would prop it on its side.
- Paws folded up (egg mode): the barrier falls to **8.1 mm (27 mJ)** at the 85° side rest. This is the egg shape at work.
- The tip of the egg can never be a rest.

**Manoeuvre:**
1. Fall detected by the IMU.
2. All paws fold up.
3. The two down-side legs yaw so their paw plane contains the fall direction.
4. Their knees sweep the paws from 178° toward the head, and the paw tips lift the flank: 85° → 72° → 59° → 44°.
5. The CoM passes over the haunch-ball pivot and the robot drops onto its feet. Then it stands.

**Results:**
- Right side, left side, face-down, on its back, both diagonals and upside-down: **all 7 recover**.
- Worst knee load 0.066 N·m, which is 33 % of MG90S stall at 5.5 V.

**Margin and sensitivity:**
- With the CoM raised 3 mm: still 7/7.
- With 44 mm paws: 7/7, but only after the toe-in fix. With 41 mm paws: 2/7.
- With 33 mm paws and a low knee: 0/7. The bottom-mounted push rolls it the wrong way. This is why the knee sits high and the paws are 48 mm.

## 5. Torque check (`calc.py` → `calc.json`)

Basis: 0.346 kg (3.39 N); MG90S ≈ 0.20 N·m and SG90 ≈ 0.19 N·m at 5.5 V. The rule is static ≤ 30 % and ×2 dynamic ≤ 60 %.

| Case | Static N·m | ×2 N·m | % stall static / dyn |
|---|---|---|---|
| Knee, 4-leg stand (30°) | 0.017 | 0.035 | 9 / 17 |
| Knee, trot on 2 legs (30°) | 0.035 | 0.070 | 17 / 35 |
| Knee, crouched trot (45°) | 0.053 | 0.105 | 26 / 53 |
| Knee, rise from the nest on 4 legs | 0.041 | 0.081 | 20 / 41 |
| Knee, rise from the nest on 2 legs | 0.081 | 0.163 | 41 / 81 → **forbidden in firmware**: always rise on 4 |
| Hip yaw, foot scrub μ 0.5 / 0.8 (TPU) | 0.026 / 0.042 | 0.052 / 0.084 | 13 / 26 and 21 / 42 |
| Knee, self-righting push (worst fall) | 0.066 | 0.132 | 33 / 66 |
| Head SG90 (gravity, 60° in 0.15 s, ring friction) | 0.016 | – | 8 |

The righting push is executed slowly (≤ 60°/s, quasi-static, dynamic factor ≈ 1.3, so about 43 %). The model also assumes half the robot's weight on each paw, which is conservative.

## 6. Face and expression

**Hardware.**
- **2 × GC9A01 1.28" round 240×240 IPS** (Robotistan, 351.50 TL each), on one SPI bus with two CS lines. Centres 39.2 mm apart, the PCB minimum.
- They sit about 3 mm behind a dark visor band. The visor is an EVE-like rounded band, 74 × 35 mm, wrapping the egg.
  - Build: vacuum-formed 1 mm smoked PETG over a printed buck.
  - Fallback: 0.8 mm printed translucent-black PETG, where the eyes glow through softly.

**Pure-black UI.** The panel edges vanish, so the eyes float.

**Eyes** (`eyes.py`; drawn the way the firmware would draw them, on black):
- Parametric pills, 16 × 21 mm, each shifted 3.2 mm toward the nose. That gives a gap of 0.94 eye-widths, which reads as baby, not derpy.
- Cyan-white with a soft glow and two catch-lights.
- Emotions: happy "^ ^" arcs, curious (asymmetric with a lid), sleepy closed arcs.
- Blinks, saccades and "eyes lead, head follows" are implemented as easing on parameters.

**Body language from the 9 servos:**
- oblique-head look and tilt
- body lean, bounce and nod from the knees
- paw wave
- a "waddle" from the yaws

**Other inputs and outputs:**
- Touch: copper-tape pads inside the cap (head pat) and belly, on ESP32-S3 native touch pins.
- Cliff: VL53L0X looking forward and down through a 6.8 mm "belly-button" window.

## 7. Electronics and power

**Controller:** ESP32-S3 Mini/Zero class board (23.5 × 18 mm, 4 MB flash, 2 MB PSRAM, Robot Sepeti 632.44 TL). It has Wi-Fi for HTTPS calls to the Claude API and voice through the phone or a PC.
- **PWM:** all 9 servos on MCPWM (12 outputs). LEDC handles the display backlight.
- **I²C:** BMI160 IMU and VL53L0X.
- **ADC:** battery divider.

**Power path:** 2S 14500 IMR (2 × 105.48 TL; confirm a rating of 4 A or more) → 2S BMS (5 A or more) → switch → three MP1584 bucks:

| Rail | Voltage | Loads |
|---|---|---|
| A | 5.5 V | 4 knees + head |
| B | 5.5 V | 4 yaws |
| C | 5.0 V | Logic, via SS14 + 470 µF hold-up, so the ESP32 never browns out |

- Bulk capacitance: 1000 µF on each servo bank. Star ground.
- Peak ≈ 4.7 A during a get-up, which is 3 A or less per bank.
- Charging: 2S USB-C 4 A charger. The port is at the back, about 57 mm above the desk when standing, so it charges while sitting in the nest pose.

**Placement.** Both cells stand vertically on the floor of the egg at the very centre (z −43…+7). They are the ballast. The MP1584s, charger and ESP32 sit on a sled at the back of the core. The BMS and IMU sit near the centre.

**Runtime** (5.8 Wh): about 25 min of continuous walking; about 3.5 h idle or talking with servos detached.

**Firmware rules** (research §7):
- staggered servo attach
- slew limit 300°/s
- detach when idle
- pause Wi-Fi during a get-up
- low-battery cutoff at 6.6 V

## 8. BOM and cost (TL, KDV incl., Turkish stock; `calc.json`)

| Item | TL |
|---|---|
| MG90S × 8 + 1 spare (Robotistan) | 1,132.20 |
| SG90 (head) | 82.25 |
| ESP32-S3 Mini/Zero board | 632.44 |
| GC9A01 1.28" round × 2 | 703.00 |
| BMI160 IMU (Direnc) | 127.86 |
| VL53L0X ToF cliff sensor (Robotistan) | 423.35 |
| 14500 IMR × 2 | 210.96 |
| 2S BMS + 2S USB-C 4 A charger | 123.24 |
| MP1584 × 3 | 159.66 |
| Capacitors, diode, switch (est.) | 55.00 |
| Copper tape (est.) | 30.00 |
| Wire, JST, M2 screws, inserts, PTFE, magnets (est.) | 150.00 |
| Smoked PETG sheet for the visor (est.) | 100.00 |
| **Parts** | **3,929.96** |
| Studio print: PLA cream + orange, PETG, TPU soles (est.) | 650.00 |
| Shipping from about 4 shops (est.) | 250.00 |
| **Total** | **≈ 4,830 TL (≤ 5,000 ✓)** |

Optional on-board voice: INMP441 + MAX98357A + speaker adds 506 TL, for about 5,336 TL. Swapping the VL53L0X for 2 × TCRT5000 IR sensors (≈ 25 TL each, price not verified) brings that back to **about 4,962 TL**. Otherwise voice goes through the phone.

## 9. Printability (FDM, walls ≥ 1.6 mm)

- **Body bowl and head:** each part has a planar oblique seam face. Print it on that face, dome up, with no supports.
  - The top edge of the visor window gets a 0.4 mm sacrificial membrane that is cut out after printing.
  - Layer height 0.12 mm on the domes. Z-seam at the back.
- **Haunch balls:** two hemispheres each, split at the equator and printed dome-up. The joint plates and the horn pocket are flat or vertical, so no supports are needed.
- **Eggshell cap:** orange PLA, dome-up. Held with 2 magnets so it is swappable (hats).
- **Paws:** printed on their side, then the TPU soles are glued on. Small parts — the deck, collars, sled and core post — are flat prints.
- **Colours:** matte warm ivory `#F1E9DA` and yolk orange `#F68A0E`, plus a black or smoked visor. All fasteners are hidden under the cap, inside the balls and under the belly.

## 10. Risks and mitigations

1. **Self-righting is modelled quasi-statically, not dynamically.** It has margin: CoM +3 mm still gives 7/7.
   - *Next:* a MuJoCo run with friction and servo limits.
   - The firmware retries in the mirrored direction (OpenCat `rc` style). On a soft rug the paw tips may sink.
2. **The 48 mm paws look a little leggier** than a pure toddler would. They are the price of righting.
   - A 44 mm paw with the toe-in works in the model too (7/7) but has no margin.
3. **Knee torque on a 2-leg rise is 81 % dynamic.** The firmware forbids it.
   - The righting push is 66 % ×2, so it is done slowly.
   - Metal-gear MG90S, plus a spare in the BOM.
4. **The visor is the hardest part to make well.** Vacuum-forming needs a small DIY former; the fallback is a printed translucent-black visor.
   - The two round displays need a black-painted inner pocket so no PCB edge shows.
5. **Yaw servos clamped without tabs.** This needs good printed cradles. The ball's PTFE collar takes the bending loads.
6. **Cable loops:** each knee servo cable passes through the ball's top pocket (loop sized for ±90° yaw). The head ribbon passes through the hollow post (±60°).
7. **The 2 MB PSRAM** on the mini board is enough for two 240×240 eye sprites and TLS. The N16R8 devkit (63 × 25 mm) does not fit the core sled.

## Files

**Scripts:**
- `model.py`: build123d model. Poses `stand`, `curious`, `push`, `fallen`, `egg`. Exports one STL per colour or material, plus internal envelopes.
- `check.py`: interference checks, head-sweep check, mass and CoM.
- `righting.py`: self-righting model.
- `calc.py`: torque, power and cost.
- `eyes.py`: eye textures.

**Rendering:**
- `mkscene.py`, `render_final.sh`, `label.py`, `compose_seq.py`.

**STLs and data** (exterior STL groups in `stl_stand/`):

| STL | Material |
|---|---|
| `body_shell`, `head_shell` | Cream PLA |
| `cap`, `haunch`, `foot` | Orange PLA |
| `sole` | TPU |
| `visor` | Smoked PETG |
| `screen_L`, `screen_R` | Displays |
| `lens` | ToF window |
| `int_*` | Real envelopes of servos, cells, boards and displays |

`check.json`, `righting.json` and `calc.json` hold the numbers.
