# Robot appeal research: what makes a small desk robot look adorable, premium and alive

Scope: design rules for a 10-15 cm, ≤350 g, FDM-printed (PLA/PETG) legged desk robot with an ESP32-S3 and a screen face.
This file covers research only; no modeling.
Numbers marked (src) come from the sources listed at the end. Numbers marked (est.) are my estimates from photos or general practice.

---

## 1. Benchmarks in our size class

| Robot | Size / mass | Face | Actuators | Why it reads as cute or premium | Weak spot |
|---|---|---|---|---|---|
| **Eilik** (Energize Lab) | 108×105×133 mm, ~230 g (src) | 1.54" 128×64 OLED (src) | 4 servos: head nod, body twist, 2 arms (src) | Very close to our target size. The head is about 55% of the height. One soft, pebble-like shell, two colours (white plus one pastel), no visible fasteners. Touch sensors on the head, belly and back trigger reactions. | Monochrome OLED. Does not walk. |
| **LivingAI EMO** | 95×67×118 mm, ~248 g (src) | Small LCD behind a black glossy front (src says LCD) | Head pan/tilt plus two stubby legs that shuffle | The head is about 70% of the height and the legs are tiny "toddler stumps". The whole front is a black glass mask, so screen edges vanish. Plain eyes (two glowing rounded squares) carry all the emotion. | Grey plastic can read as "gadget". |
| **Anki Cozmo** | ~ palm size | 128×64 OLED | Head tilt, lift, 2 treads | Eyes animated by Pixar animator Carlos Baena (src). Pupils were removed because they made Cozmo "feel too human" (src). The eyes squash into happy slits. Anki built custom Maya tools so animators could animate the actual robot (src). | Exposed forklift mechanics, but they are styled. |
| **Anki Vector** | ~ palm size | Wide colour IPS (reported 184×96), ~1.9:1 | Head, lift, treads | Eyes are always moving: blinking, narrowing when thinking, worried at table edges (src). The black face window makes the screen look like part of the body. | — |
| **Sesame** (dorianborian) | Body ~79×68 mm; leg parts ~58 mm long (measured from the repo STLs) | 128×64 OLED on the body front (src) | 8× MG90 (src) | Moves well and the face syncs with motion. It is clean for a DIY build and has hat/ear variants. | No head; the face is a small window in a box. The legs are thin and splay sideways, which reads as crab or spider, not pet. The face is about 25-30% of the front width, so the eyes are tiny. |
| **Petoi Bittle / Nybble** | ~20 cm | None (Bittle), or wooden cat (Nybble) | 9-12 servos | Strong dynamic gaits; can get up after falling. | Exposed servos and PCB read as a "kit", not a "pet". |
| **Petoi Quaddle** (2026) | Desk size | Optional AI core | 4 servos with linkage legs ("MiniDoF") (src) | Very few actuators for omnidirectional walking. Printable shells over moulded joints (src). | — |
| **M5Stack Stack-chan** | ~8 cm | 2" IPS showing a pure black-on-white face: 2 dots and a mouth line | 2 servos (pan/tilt) | The extreme simplicity is charming. With look-at plus a dot-eye face, 2 servos feel alive. | The face is a box with a visible bezel. |
| **Keepon** | Two yellow tennis balls (src) | 2 cameras as eyes, no mouth (src) | 4 DOF: pan, nod, side-tilt, squash/bob | The simplest form that can still interact (src). All emotion comes from squash and lean. It shows that timing beats detail. | — |
| **Mira** (Alonso Martinez, Pixar TD) | Egg/sphere, flat bottom (src) | Single LED "eye" | Shell rotation on a slight axis plus bounce | Simplicity built from small design cues (src). Peek-a-boo: it bounces with excitement when you hide your face (src). | — |
| **Disney BDX** | 0.66 m, 15.4 kg; head+neck 2.4 kg (src) | LED-array eyes with variable colour and radius (src) | 5 DOF per leg, **4 DOF neck/head** (src) | Design is "driven by creative intent and simplicity rather than functional requirements" (src). Show functions: actuated antennas, illuminated eyes, head lamp, speakers (src). Antennas duck back and the eyes narrow at top speed to show effort (src). Idle blinking and antenna motion (src). Backward-bending knees, rounded foam soles. | — |
| **Microduck** (Pollen / Hugging Face, 2026) | ~25 cm, $399 (src) | Duck face, no screen | 15+ motors (src) | One iconic animal silhouette (yellow duck) instantly reads as a character. RL-trained waddle, self-righting (src). | — |
| **Loona** | Larger, on wheels | IPS face | Wheel-legs, 2 ears | Big expressive ears as emotion amplifiers. | Size. |
| **Sony aibo ERS-1000** | Dog size | **Two OLED eyes**, one per eye socket | 22 axes | The eyes are separate displays sunk in sockets, so they read as eyes, not a screen. Slow, weighted, dog-like idles. | Price. |
| **Pleo** | Dinosaur | — | ~14 motors | Soft rubber skin; slow breathing idle; reacts to touch. | — |
| **Furby** | — | Mechanical eyelids (old); LCD eyes (2012) | Ears, eyelids, beak | Big eyes with eyelids, ears that perk up, and a babble voice. | Uncanny when it fails. |
| **WALL-E / EVE** | — | WALL-E: binocular "eyes" on a neck. EVE: an egg with eyes drawn on a black glossy visor | — | EVE is the reference for "premium plus cute": a white glossy egg with a black glass face band and blue glowing pill eyes. WALL-E: the head on a neck leads every emotion. | — |
| **Tamagotchi / pixel faces** | — | Low-res pixels | — | Charm from honest low resolution plus very readable silhouettes: 2-3 pixel eyes, a 1-pixel mouth, big pixels on purpose. | Looks cheap if pixels are small, jagged and anti-aliased badly. |

Key takeaways from the table:
- The products closest to our target (Eilik 108×105×133 mm, ~230 g; EMO 95×67×118 mm, ~248 g) are a **big head on a small body**, use **one soft shell**, have **two colours**, and **hide all mechanics**.
- Sesame's look problem is structural, not cosmetic: no head, a tiny face, splayed thin legs, and a boxy body.

---

## 2. Proportions (baby schema, "Kindchenschema")

Lorenz's baby schema, as confirmed by Glocker et al. (2009), lists the cues that read as cute:
- a large head relative to the body
- a high, rounded forehead
- large eyes placed **low** on the face
- a small nose and mouth (or none)
- round cheeks
- short, thick limbs
- a rounded, compact body
- clumsy, toddler-like motion

Concrete targets for a 10-15 cm walker:
- **Head : total height = 0.45-0.60.** Our size-class benchmarks run 55-70%. If the head is a separate part, its width should be ≥ body width (×1.0-1.15). A head narrower than the body reads as an adult animal or a bug.
- **Visible leg length ≤ 0.35-0.45 of total height,** and legs at least 14-18 mm thick (est.). Thick, short, slightly tapered "stumps" with round feet read as toddler. Long, thin legs with knees out read as spider or crab.
  - Keep the feet **inside or just outside the body footprint** in the standing pose, like BDX and Microduck.
  - Feet slightly oversized and rounded, with soft TPU soles if possible (BDX uses foam soles).
- **Eye line at 40-48% of head height,** measured from the bottom of the face. Low eyes give a big forehead, which reads as baby. Eyes in the upper third read as adult or predator.
- **Eye size: each eye's height ≈ 20-30% of face height,** and the width of each eye ≈ 22-28% of face width.
- **Eye spacing:** the gap between the eyes is 0.6-1.0× one eye width.
  - Wide-set reads as baby or prey animal.
  - Close-set reads as angry or predator.
  - Over 1.3× reads as derpy, which is fun as a temporary expression.
- **Mouth:** none, or a tiny element (a 2-4 px line or "w") shown only during speech or joy. A big or realistic mouth is uncanny.
- **Mass distribution:** visually bottom-heavy (round belly, low centre). A top-heavy look makes people nervous. Keep the head visually large but physically light: hollow shell, screen near the front.
- **Overall bounding shape:** close to a cube or a squat egg (H:W:D roughly 1.2 : 1 : 0.9). Long horizontal bodies read as "dog robot / kit", while compact, tall-ish bodies read as "companion".

## 3. Silhouette and form language

- **One continuous soft shell.** Every product that reads as premium (Eilik, EMO, EVE, Vector, Mira, Keepon) reads as one or two smooth volumes.
  - Mechanics are either fully hidden or deliberately styled. Cozmo's lift arm is designed as part of the character; its mechanism is not just left visible.
  - Exposed generic servos are the number-one "kit" signal (Bittle, Sesame legs).
- **Fillet sizes for a 100-150 mm object:**
  - Main volumes: radius ≥ 8-15 mm. They should look like pebbles or soap bars.
  - Secondary edges: ≥ 3-5 mm.
  - No sharp 90° external edges anywhere a viewer looks.
  - Use variable or continuous-curvature blends (loft or spline) on the head silhouette rather than a box with uniform fillets. A filleted box still reads as a box.
- **Readable silhouette:** if you black-fill the robot, you should still read the character (head, ears or antennas, stubby legs). Give it 1-2 signature shapes that are visible in silhouette:
  - ears
  - antennas
  - a tail
  - a duck bill (Microduck)
  - a visor band (EVE)
- **Part lines as design lines.** Put the colour change exactly at the split between parts, and make the seam an intentional **reveal groove** (0.6-1.0 mm wide, ~0.8 mm deep). FDM tolerance gaps then look designed instead of sloppy. Uneven gaps are a strong "cheap" signal.
- **Hide fasteners:** screws go from the underside or behind removable "cheek" plates. Use magnets (6×2 mm) for lids and hats; Sesame does this for its hats, which is a good idea. Use snap fits where PLA allows.
- **No greebles.** Surface detail (vents, ribs, fake bolts) makes small robots look busy and cheap. One or two crisp details (an ear notch, a status light dot, a belly button / touch pad) are enough.
- **FDM-specific form tips:**
  - Large convex domes printed face-up show contour "stair steps" at the top. Use 0.12 mm or variable layer height on domes.
  - Better still, split the shell so the dominant curve lies in the XY plane, for example splitting the head into front and back halves printed lying down.
  - Place the Z-seam at the back or on a sharp inner corner.
  - Matte PLA hides layer lines far better than silk or glossy filament. Light matte colours hide them better than dark glossy ones.
  - Avoid visible support scars on the face or top. Design overhangs ≤ 45°, or make the underside a hidden surface.
  - Thin light-coloured PLA (≤1.2 mm) glows when an LED is behind it: an ESP32 power LED or a charge LED shows through. Use ≥ 1.6 mm walls or a black inner paint or film in the head, or cover the board LEDs with a dab of black paint.

## 4. Colour and finish (PLA reality)

- **Two-colour rule:**
  - Main body: a warm off-white or soft pastel, 70-80% of the surface.
  - Accent: one saturated colour on the ears, legs or feet, visor frame or belly.
  - **Dark visor:** near-black for the face.
  - The eye glow (cyan, white or warm yellow) is the only "light" colour.
- Avoid pure white #FFFFFF. It reads as cheap and clinical, and it yellows and shows dirt. Warm ivory or cream reads as premium (Eilik and EVE-like).
- Avoid more than 2 plastic colours plus black. Avoid rainbow, silk, glitter and translucent filaments. Translucent filament shows the internals and the infill pattern.
- Pastel matte PLA (sakura pink, mint, lemon, latte, ash grey, sky blue) is widely available from most brands, including Turkish brands like Elas, Porima, Filameon and Microzey. Matte finishes look like injection-moulded ABS with a soft-touch coat.
- Feet or soles in TPU (black or the accent colour) give grip, less clatter on the desk, and a premium "soft part" contrast.
- Optional premium touch: one glossy element. The visor (acrylic) or a clear-coated nose or button contrasts with the matte body. Matte plus one gloss reads as designed.

## 5. The face

### Hardware options (prices from GUIDE)
| Option | Active area | Look | Verdict |
|---|---|---|---|
| 0.96" SSD1306 OLED (Sesame) | ~22×11 mm, 128×64 1-bit | True black and crisp, but **tiny** on a 10-15 cm robot; the eyes become specks | Too small for the hero face. Fine as a secondary display. |
| 1.3" 240×240 ST7789 IPS | ~23×23 mm | Colour, square | OK. The square shape does not fit two horizontal eyes as well as a wide screen. |
| **1.47" 172×320 IPS (Waveshare ESP32-S3 board, includes IMU)** | ~17×33 mm, used **landscape 320×172 ≈ 1.86:1** | Almost the same aspect as Vector's face (~1.9:1). Two eyes side by side fill it naturally. MCU and IMU on the same board. | **Best "Vector/EMO" face** behind a dark visor. |
| **GC9A01 1.28" round 240×240** | Ø ~32 mm | Round "porthole" face (Stack-chan / BMO-ish), or **2 round screens = 2 real eyes (aibo-like)** | One round screen in a round bezel looks very integrated and premium. Two of them (2×351 TL) give the most "alive" eyes possible, at ~70 mm minimum face width. |

### How to make a cheap screen look built-in
1. **Background pure black (0,0,0), and only the eyes lit.** The screen then disappears into the visor and the eyes look like they float in the face. This is the single biggest trick (Vector, EMO, EVE).
2. **Dark tinted front "glass":**
   - Laser-cut **smoked (füme) acrylic, 2 mm**, ~30-50% transmission, cut to the face outline (cheap at local laser shops).
   - Or a glossy black printed bezel with the screen flush.
   - The visor should be **larger than the screen**, a whole face band or face mask, so the screen edge sits behind tinted material and is invisible.
   - IPS black glows grey in dim rooms, and the tint fixes that.
   - Lower the backlight with PWM, to ~40-70% indoors.
3. **Never let the screen frame, white PCB, flex cable or mounting holes show.** The screen sits behind the visor in a black-painted pocket. Keep drawn content ≥ 6-8 px from the active-area edge.
4. The **visor shape follows the head shape:** a rounded rectangle or an EVE-style band with ≥ 30% corner radius, curving with the head where possible. Acrylic can't curve easily, so keep it flat but inset into a softly filleted recess, ~1 mm proud or flush.
5. Add a thin **accent ring or bezel** (1.5-3 mm) around the visor in the accent colour. It reads as a deliberate frame.

### Eye design and animation (procedural, not bitmaps)
- **Shape:**
  - Rounded rectangles or "pills" (Cozmo, Vector, EMO, EVE). On a 320×172 panel, each eye is about 70-85 px wide × 90-110 px tall, with a corner radius ~35-45% of width, and a gap of ~50-70 px between the eyes.
  - Pupil-less reads as friendly robot (Anki removed pupils for this reason).
  - Optional anime "sparkle": a 6-10 px white highlight in the upper corner. Use it for love or excited expressions only.
- **Glow:** draw a soft halo (2-4 px, 20-30% alpha) around each eye. Colour eyes cyan-white (#6FF3FF / #BFFBFF) on black, or warm white. Change colour only for strong emotions.
- **Draw from parameters, not frames:**
  - Parameters per eye: width, height, x/y offset, corner radius, top-lid angle and height, bottom-lid "smile" curve.
  - Tween every parameter with easing at ≥ 30 fps, using a TFT_eSPI or LVGL sprite with DMA.
  - Swapping static bitmap faces (Sesame style) is a major "cheap" signal.
- **Blink:**
  - Random interval of 2-6 s; 10-20% of blinks are double blinks.
  - Close in ~60-80 ms, hold ~20-40 ms, open in ~100-150 ms. Opening is slower than closing.
  - **Squash on blink:** while closing, eye height drops to ~10% and width grows by ~10-15%.
  - Blink on every big head turn and gaze shift. Animals do this, and it sells "alive" instantly.
- **Saccades:**
  - The gaze jumps (in 1-3 frames, ~30-50 ms) to a new target every 0.4-3 s, with small 2-5 px micro-saccades in between.
  - **The eyes lead, the head follows** 100-250 ms later, then the body follows. This lag between eyes, head and body is the core principle of character animation.
  - When looking sideways, the far eye shrinks ~10-15% and both eyes shift. This fakes perspective, so the face feels 3D.
- **Emotion poses through lids and shape:**
  - happy: bottom-up arcs or "^^" slits (Cozmo)
  - sad: outer top lids drop and the eyes shift down
  - angry: inner top lids drop
  - sleepy: half-closed with slow blinks
  - curious: one eye bigger, plus a head tilt
  - surprised: eyes grow ~120% with a quick overshoot
  - love: hearts or sparkle
  - effort: eyes narrow (BDX does this when walking fast)
- **Pixel-art fallback:** if a pixel style is used (Tamagotchi), use **big pixels on purpose** (each "pixel" = 8-12 real px) with zero anti-aliasing. Never mix pixel art with smooth vectors.

## 6. Expressive DOF: personality per servo

Ranking, for a legged desk robot that already has body pitch, roll and height from its legs:

1. **Head roll / tilt (side tilt):** the curious dog tilt. It is the single most "aww" motion per servo. Keepon and BDX both have it.
2. **Head pitch (nod / look up at you):**
   - Looking up at the user, about 15-25° above horizontal, triggers the baby schema strongly.
   - Drooping down reads as sad or sleepy.
3. **Head yaw (look-at):** following the user (Stack-chan, Mira). It can be partly faked by body yaw from the legs plus eye gaze on the screen.
4. **Ears or antennas (1 servo each, or 1 servo for both via linkage):** emotion amplifiers (Loona, Furby, BDX antennas).
   - Perked up = alert or happy; back = scared or effort; asymmetric = curious.
   - Cheap SG90 class servo, light load.
5. **Tail wag (1 SG90):** unmistakable joy that is also readable from behind. Very high payoff for a quadruped.
6. **Free from legs:**
   - Crouch and stretch (squash and stretch), body roll for tilt, a "bow" (play invitation), shiver, bounce, sit.
   - Sesame and Keepon show that body posture alone carries most emotions, so script these before adding servos.
7. **Passive secondary motion (0 servos):**
   - Spring-wire or TPU antennas or ears that wobble after each step give follow-through and overlapping action for free.
   - A bobble on a thin TPU stalk is very cheap and very alive.

Recommended budget for our robot: walking legs (8 servos) plus **1-2 expressive servos**. Options are a 2-axis neck (tilt + nod) or a 1-axis neck plus an ear or tail servo. Add passive wobble antennas or ears on top. Eilik gets a lot of personality from just 4 servos, and Stack-chan from just 2.

## 7. Motion appeal (Disney's 12 principles applied to servos)

- **Never move linearly at full servo speed.** Default servo moves (instant target, max speed) are the most robotic thing possible.
  - Update targets at 50-100 Hz with easing curves: ease-in-out for poses, ease-out-back for snappy reactions.
  - Cozmo and Vector were animated in Maya by animators, not with raw servo jumps (src).
- **Anticipation:** before a jump, walk start, turn or "surprise", move 5-10% the opposite way, for example a 3-6 mm crouch or a head pull-back lasting 120-250 ms.
- **Overshoot and settle:** snappy moves overshoot by ~5-12% and settle with 1-2 damped oscillations over 150-300 ms. Head and ears especially.
- **Overlapping action / follow-through:** eyes, then head, then body, with 50-150 ms offsets. Ears and antennas lag the head.
- **Idle "breathing":**
  - Body height varies ±1-1.5 mm (sine, 3-5 s period).
  - Plus slow eye drift and blinks, plus an occasional weight shift or look-around every 8-20 s.
  - It never freezes completely. BDX runs perpetual idle blinking and antenna motion (src).
- **Timing gives character:** small and fast reads as excited puppy; slow and heavy reads as sleepy. Pick a default "tempo" for the character and keep it consistent.
- **Toddler gait:** a slightly bouncy body and a little side-to-side roll while walking (a "waddle") read cute. Perfectly level mechanical trotting reads as machine. Microduck's waddle is its whole charm.
- **Falling and getting up:**
  - Make a fall a performance: a surprised face, a pause, a little shake-off after getting up.
  - A clumsy fall followed by a proud recovery is appealing. Flailing is not.
- **Contingent reactions** (response within ~200-300 ms):
  - Touch triggers squash, a giggle sound and happy eyes.
  - A face or sound triggers a look. Mira's peek-a-boo is a good example.
  - Responsiveness reads as "alive" more than any amount of detail.
- **Servo hygiene:**
  - Avoid holding torque at jittery positions (MG90S hum and jitter).
  - Use small deadbands, filtered targets, and detach expressive servos at rest when the load allows.
  - Buzz and twitch at rest are strong "cheap" signals.

### Sound
- Use non-verbal chirps and beeps (R2-D2 / WALL-E / Cozmo style) for emotions. They come across as cute and never uncanny.
  - Rising pitch means a question or curiosity, falling means sad, quick trills mean happy.
- Generate them procedurally: short tones of 40-200 ms with pitch glides, played through the MAX98357A and a small speaker.
- Keep TTS for actual sentences only. Pitch it slightly up and keep it short.
- Sync sound to motion: the sound starts with, or ~30-50 ms before, the motion peak. Sound also masks servo noise.
- Give the speaker a small sealed back volume and grille holes on the underside or back, not on the face.

---

## 8. Anti-patterns: why DIY robots look cheap

1. Exposed servos, horns, wires, zip ties, PCB edges, USB cables or battery tape.
2. A rectangular OLED in a rectangular hole: a visible screen border, a white flex cable or PCB showing, or the screen sitting proud or at an angle.
3. Tiny eyes: a 0.96" OLED on a 10 cm face. Eyes set high or close together.
4. Static bitmap faces that swap instead of animating, small jagged 1-bit art, text on the face.
5. Uniform thin legs splayed sideways (crab/spider stance), many visible joints, feet outside the footprint.
6. Boxy volumes with small uniform fillets ("filleted box"), hard edges, flat slabs.
7. Too many colours, silk or rainbow filament, translucent PLA showing infill, pure #FFFFFF white.
8. Visible layer stair-stepping on the head dome, support scars on the face, a seam line across the front, elephant foot, stringing.
9. Uneven gaps between parts, visible screw heads, misaligned shells.
10. Busy surface greebles, vents, logos and stickers.
11. Board LEDs glowing through thin white walls.
12. Linear constant-speed servo motion, twitching, buzzing at rest, jerky starts and stops, a frozen idle.
13. A realistic human mouth or teeth, or a TTS voice used for emotions (uncanny).
14. No reaction to touch or gaze: a robot that "performs at" you instead of responding.
15. A face on the body front with no head, so "looking" is impossible.

---

## 9. Twelve concrete rules for our 10-15 cm desk walker

1. **Big head:** the head (face volume) is **≥ 50% of standing height** and at least as wide as the body. Target overall ~110-140 mm tall.
2. **Short, thick legs** tucked under the body. Visible leg ≤ 40% of height, leg cross-section ≥ 14 mm, feet rounded with TPU soles, feet within or near the body footprint. No sideways splay.
3. **One soft shell plus a dark visor.** Main fillets ≥ 8 mm, secondary ≥ 3 mm, no visible screws (fasten from below, use magnets for the top or hats).
4. **Face = landscape colour IPS (or round GC9A01) behind a 2 mm smoked acrylic visor** that is larger than the screen, with a pure-black UI background and an accent bezel ring. No visible screen edges.
5. **Eyes low and wide:** the eye line at 40-48% of face height, each eye 22-28% of face width, a gap of 0.6-1.0 eye widths. Pupil-less rounded pills with a soft glow.
6. **Procedural eyes at ≥ 30 fps:**
   - random blinks every 2-6 s, with squash
   - saccades every 0.4-3 s
   - the far eye shrinks when looking sideways
   - lids and shape carry emotion
7. **Eyes lead, the head follows (100-250 ms), the body follows.** Add at least one head DOF, with tilt the priority.
8. **One or two expressive extras:** a tilt+nod neck, or a neck plus an ear or tail servo. Add **passive wobble antennas or ears** for free follow-through.
9. **Never linear motion:** easing at 50-100 Hz, anticipation before every big move, 5-12% overshoot plus settle, a breathing idle (±1-1.5 mm, 3-5 s), and no total freeze.
10. **Two colours plus black, matte PLA:** a warm off-white or pastel body, one saturated accent on the ears, feet or bezel, and a glossy black visor. Put the colour splits on reveal grooves.
11. **Print for looks:**
    - 0.12 mm or variable layers on domes, Z-seam at the back, no supports on visible faces.
    - Walls ≥ 1.6 mm, with black paint or film inside the head so no LEDs show through.
    - Uniform 0.3-0.5 mm part gaps.
12. **React within 300 ms with sound:**
    - Touch triggers a squash, a chirp and happy eyes.
    - A detected face or sound triggers a look-at.
    - Falls become a performance (oops face, then a proud shake-off).

## 10. Three colourways (matte PLA plus black visor)

| Name | Body (≈75%) | Accent (ears, feet, bezel) | Visor / dark | Eye glow | Notes |
|---|---|---|---|---|---|
| **"Süt & Mandalina" (Milk & Tangerine)** | `#F3EEE4` warm ivory | `#FF8A3D` tangerine | `#121417` | `#7CF4FF` cyan | The safest premium look: EVE/Eilik warmth with a playful accent. Orange reads well in photos. |
| **"Nane Şekeri" (Mint Candy)** | `#CFE9DD` soft mint | `#FF8FA3` coral pink | `#14181B` | `#FFFFFF` warm white (`#FFF6E8`) | The most "adorable/kawaii". Mint + coral is a classic toy palette. White eyes keep it gentle. |
| **"Galaktik Gece" (Galactic Night)** | `#2E3352` deep indigo | `#FFC94A` sunflower yellow | `#0D0F1A` | `#8AF7FF` ice cyan (or `#FFD36A`) | Bold "space buddy" look. The dark body hides layer lines less well, so print matte at 0.12 mm. Yellow ears or antennas pop. |

Alternative accent swaps within the same system: lemon `#FFE066`, sky `#8CC8FF`, latte `#C9A27E`.

---

## Sources
- Sesame Robot repo: https://github.com/dorianborian/sesame-robot/ (local copy; STL sizes measured from it)
- Hackster, Sesame: https://www.hackster.io/news/build-your-own-quadruped-robot-for-under-60-99a2b1db20dd
- Eilik specs: https://store.energizelab.com/es/products/eilik , https://theindexproject.org/award/nominees/8185
- EMO size and display: https://keyirobot.com/blogs/buying-guide/emo-cute-robot-pet-review-is-livingais-emotional-robot-worth-it
- Cozmo animation and eyes: https://www.therobotreport.com/cozmo-ai-robot-brings-wall-e-to-life/ , https://www.engadget.com/2016-10-14-anki-cozmo-robot.html , https://www.designboom.com/technology/anki-cozmo-07-07-2016/
- Vector eyes: https://www.macrumors.com/review/anki-vector-robot/
- Disney BDX paper (Grandia et al., RSS 2024): https://arxiv.org/html/2501.05204v1 ; Disney: https://thewaltdisneycompany.com/news/behind-the-bdx-droids/
- Microduck: https://techcrunch.com/2026/08/27/hugging-face-is-selling-a-cute-399-open-source-duck-robot-microduck/
- Petoi Quaddle: https://makezine.com/article/technology/petoi-quaddle-a-robotic-pet-for-everyone/ , https://www.petoi.com/pages/quaddle
- Keepon: https://www.yalescientific.org/?p=1095 , https://www.ei.tohoku.ac.jp/xkozima/carebots/robot-ponhist-eng.html
- Mira: https://www.raspberrypi.com/news/mira-robot-alonso-martinez/ , https://techcrunch.com/2015/07/10/this-pixar-artists-homemade-robot-is-adorable-and-i-want-one
- Procedural Cozmo-style eyes on ESP32: https://github.com/liunix61/esp32-eyes
- Baby schema: Glocker et al., "Baby schema in infant faces induces cuteness perception and motivation for caretaking in adults", Ethology 2009 (from memory, not fetched)
