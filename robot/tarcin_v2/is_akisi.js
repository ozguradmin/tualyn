export const meta = {
  name: 'tarcin-v2-build-package',
  description: 'Tarçın v2: single-board electronics + LiPo, keyboard-ready legs, print-ready CAD, re-simulation, Turkish cart and beginner build guide, reviewed',
  phases: [
    { title: 'Design', detail: 'electronics/power + leg track/paw choice' },
    { title: 'CAD', detail: 'print-ready parts, slicing' },
    { title: 'Validate', detail: 'MuJoCo re-check, cart, guide' },
    { title: 'Review', detail: 'hardware review + beginner read-through' },
    { title: 'Fix', detail: 'apply review fixes' },
  ],
}

const SP = '/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad'
const OUT = `${SP}/tarcin_v2`
const B = `${SP}/yeni/paket/B`
const REPO = '/home/user/tualyn'

const BG = `
PROJECT: "Tarçın v2", the build version of the Tarçın red-panda desk robot for a family in Turkey. The family approved Tarçın's look;
they are TOTAL BEGINNERS (no tools, no experience; they will buy a cheap soldering kit and learn from YouTube + our guide), they have NO
3D printer (a print studio prints the parts), and they CANNOT get a Li-ion pack spot-welded. Every part comes from shops in Turkey
(Robotistan, Direnc, Motorobit, Robolink, Robo90, Robot Sepeti, Amazon.com.tr shipped from Turkey). Language for anything the family
reads: Turkish (plain, friendly, no jargon without explanation).

Decisions already made (do not reopen):
 1. Battery: a ready RC-style 2S LiPo pack, Tinylab 7.4 V 2S 1300/850 mAh family — PICK: Tinylab 2S 850 mAh 40C, 59x31x17 mm, 52 g,
    Robotistan 847.30 TL (https://www.robotistan.com/tinylab-74v-2s-lipo-batarya-850mah-40c). Charged OUTSIDE the robot with an
    iMAX B3 PRO balance charger through its balance plug (Robot Sepeti 731.84). A LiPo low-voltage alarm (Motorobit 115.14) and a
    firmware cutoff via a voltage divider replace the BMS. The pack must be removable without tools (a hatch) and its main plug must
    mate with a pigtail inside the robot. No spot welding anywhere.
 2. Electronics simplified to ONE ESP32-S3 (with PSRAM) instead of two boards; the 10 servos driven by a PCA9685 servo board (servos
    plug in). The family WILL solder (header pins, a few wires to pads), but minimise and simplify joints.
 3. Keep the look: red-panda head with two GC9A01 round eyes behind the smoked mask, ears, ringed tail, sagittal 2-servo leg pods.
 4. Legs: make it better on keyboards. The keyboard study found "wide track (+25 mm per side) + ski paws (two 5 mm-radius capsules,
    21 mm long, 19 mm wide) + spread trot with 8 mm lift" lifts K2-diagonal success from 14/36 to 30/36 (flat desk 20/20 at 5.5 cm/s
    vs 7.2-7.7) — but +25 mm per side changes the look; choose the track carefully (see the legs task).

Sources (read what you need; copy, never modify these):
 - Package: ${B}/ (manifest.json specs, bom.json verified Turkish BOM with URLs and the print basis, NOTES.md, model.glb, sim/ MuJoCo
   model tarcin.py + gait/recovery tools + out/, build/geom.py + pack.py = how the package GLB was made from the CAD).
 - Concept CAD (build123d, parametric): ${SP}/yeni/concept_B/model.py (+ concept.md, calc.py). It is a concept model: shells,
   pods, servos placed, clearance checks; NOT yet split into printable parts with bosses, hatches and tolerances.
 - Keyboard study: ${OUT}/girdi/sim_tarcin-keyboard.json (results), ${SP}/klavye/tarcin/kb/ (kbsim.py has VARIANT track_add/ski,
   kbd.py the keyboards K1/K2, batch.py/flatcheck.py/torques.py), ${SP}/klavye/tarcin/out/ (spec_*.json gaits incl. spec_MECH.json).
 - Turkish solder-free/power parts research with verified URLs: ${OUT}/girdi/research_solder-free-parts.json.
 - A stopped earlier attempt at a single-board layout (partial, may help): ${SP}/klavye/tasarim/ (fit/, sim/currents.py, bom.py).
 - Power/brownout and mechanics research: ${SP}/yeni/research/mech.md; looks: ${SP}/yeni/research/appeal.md.
 - Style references for the family docs: ${REPO}/robot/docs/BASKI.md (print-studio message), ${REPO}/robot/docs/MONTAJ.md
   (assembly guide), ${REPO}/robot/docs/baglanti_ciz.py (wiring diagram generator).
 - Renderer for previews: ${SP}/render/ (rig.js, realism.js, render.js+page.html for STL scenes; headless Chromium + SwiftShader:
   slow, long timeouts). PrusaSlicer is installed (/usr/bin/prusa-slicer); build123d, trimesh, manifold3d, MuJoCo 3.17 available.
Rules: write only under ${OUT}/<your folder>/. Never pkill/pgrep -f with a pattern matching your own command line. Verify any shop
price you rely on by opening the page today (25 Oct 2026), KDV incl. Be honest about what is verified, estimated or untested.`

const STR = { type: 'string' }
const ARR = { type: 'array', items: STR }
const NUM = { type: 'number' }
const FILES = { type: 'array', items: STR }

phase('Design')
const [elec, legs] = await parallel([
  () => agent(`${BG}

YOUR TASK (folder ${OUT}/elec/): the complete electronics and power design of Tarçın v2.
 - Board: pick ONE ESP32-S3 with PSRAM that fits (compare the tiny S3 Super Mini / S3-Zero class vs an N16R8 devkit; size, pins, header
   state, USB-C access for flashing). Decide where it sits (head or body) and how the eye SPI, I2C, power and servo leads cross the neck.
 - Servo driver: PCA9685 (Robotistan 245.54, pre-soldered per research) for 8 leg servos + tail + head pan; channel map.
 - Power from the 2S LiPo: main lead -> latching switch -> servo rails (enough for the ~4.8-5.8 A self-righting peak: e.g. two
   MP1584 at 5.5 V on two servo banks, or UBECs; justify with the package's current numbers) + logic 5 V/3.3 V rail with hold-up,
   voltage divider to an ADC pin for the cutoff, the LiPo alarm on the balance lead, fuse or polyfuse if sensible. Connector choice for
   the pack's main lead (check the Tinylab pack's actual plug on the product page and pick the matching pigtail; JST-RCY is ~3 A —
   if marginal, choose XT30 or similar and say exactly what to buy in Turkey).
 - Sensors/IO: 2x GC9A01 (SPI, shared bus, 2 CS), IMU (MPU6050/6500/BMI160), VL53L0X desk-edge, TTP223 head touch, speaker amp
   (PAM8403 or I2S), optional mic; a full PIN MAP for the chosen board with no conflicts (strapping pins, USB pins, PSRAM pins).
 - Joint count: list every solder joint the family makes (header pins per module, wires to pads), and minimise it (e.g. modules that
   come pre-soldered, servo extension leads, lever connectors for power). Mark "kolay" (header pins) vs "dikkat" (wire to pad).
 - Deliver: elec.json (parts with verified URLs/prices/sizes, pin map, PCA9685 channel map, power tree with currents, joint list),
   a wiring diagram SVG with Turkish labels (adapt baglanti_ciz.py's style), and a short firmware-facing note (pins, I2C addresses,
   PCA9685 frequency, cutoff thresholds).`, { label: 'design:electronics', phase: 'Design', schema: {
    type: 'object',
    properties: { summary: STR, board: STR, power_tree: STR, pin_map: STR, solder_joints: STR, parts_table: STR, module_sizes_for_cad: STR, files: FILES, open_risks: ARR },
    required: ['summary', 'board', 'power_tree', 'pin_map', 'solder_joints', 'parts_table', 'module_sizes_for_cad', 'files', 'open_risks'],
  } }),
  () => agent(`${BG}

YOUR TASK (folder ${OUT}/legs/): choose the leg track width and paw shape for Tarçın v2 with simulation AND looks in mind.
Using the keyboard study's tools (copy ${SP}/klavye/tarcin/kb and its model setup), run the MECH variant family at track_add =
0, 8, 12, 16, 20, 25 mm per side, each with and without ski paws, using the spread trot (8 mm lift) and the package trot: flat desk,
K1 laptop keyboard (rows + diagonal), K2 mechanical keyboard diagonal (and rows for completeness), at friction 0.3/0.4/0.6, plus a
quick self-righting check (side fall and back fall with the package's recovery sequences) and servo peak/p95 torques. Add the expected
LiPo mass/position change (pack 52 g vs the old 2x14500 pack; assume the bay stays near the old one unless told otherwise) to the model.
Render a quick same-camera front/3-quarter look comparison of 0 / 12 / 25 mm (a simple STL render of the concept with the leg pods moved
is enough) and judge the look honestly (does it still read as a cute red panda or as a crab?). Recommend ONE track_add + paw choice with
the trade-off stated (keyboard success, flat speed, self-righting, look), plus the exact geometry changes the CAD must make (hip spacer
length, pod offsets, paw shape dimensions). Output legs.json + images.`, { label: 'design:legs', phase: 'Design', schema: {
    type: 'object',
    properties: { recommendation: STR, results_table: STR, look_judgement: STR, cad_changes: STR, gait_to_use: STR, files: FILES },
    required: ['recommendation', 'results_table', 'look_judgement', 'cad_changes', 'gait_to_use', 'files'],
  } }),
])

phase('CAD')
const cad = await agent(`${BG}

YOUR TASK (folder ${OUT}/cad/): turn the concept into PRINT-READY parts for Tarçın v2. Start from ${SP}/yeni/concept_B/model.py
(copy it) and implement, in build123d:
 - the leg changes from the legs task, the electronics layout from the electronics task (board, PCA9685, bucks, amp, sensors, speaker,
   switch, voltage divider board) with real mounts (screw bosses for M2 self-tapping or snap clips, standoffs), and the LiPo bay for the
   59x31x17 mm pack + its lead with a tool-free hatch (latch or magnet) so the pack can be removed for charging; keep the centre of mass
   low and near the old pack position where possible;
 - split every shell into printable parts (one colour per part, no AMS needed: the original colours are orange/cream/black + TPU paws),
   with walls >= 1.6 mm, hidden or deliberate seam lines (reveal grooves), alignment features, clearance 0.2-0.3 mm on sliding fits,
   servo pockets for real MG90S (22.8x12.2x28.5 mm body, 32.2 mm tab span) and the 4 g micro servo, horn interfaces, wire channels and
   pass-throughs for the neck and hips with enough slack, USB-C access to the board for flashing, the switch hole, speaker grille,
   the VL53L0X window, touch pad area;
 - print orientation per part to minimise supports and put the best face up; export every part as STL (and a 3MF per colour) into
   ${OUT}/cad/stl/; check each is watertight/manifold (trimesh) and that the assembled parts do not intersect (except intended press
   fits) at rest and over the joint ranges the package uses;
 - slice every part with PrusaSlicer (PLA 0.2 mm, 4 perimeters / 15 % infill as the package basis; TPU for paws) to get grams and hours,
   and render preview images of the assembled robot (same look as before) and an exploded view.
Write cad.json: part list (name, colour, material, grams, hours, supports yes/no, orientation note), assembly order, screws/inserts
list (type, length, count — buyable in Turkey), mass/CoM of the new assembly for the simulator, and every known compromise.

ELECTRONICS RESULT (JSON): ${JSON.stringify(elec)}
LEGS RESULT (JSON): ${JSON.stringify(legs)}`, { label: 'cad:print-ready', phase: 'CAD', schema: {
  type: 'object',
  properties: { summary: STR, parts: STR, screws: STR, mass_com: STR, print_totals: STR, assembly_order: STR, compromises: ARR, files: FILES },
  required: ['summary', 'parts', 'screws', 'mass_com', 'print_totals', 'assembly_order', 'compromises', 'files'],
} })

phase('Validate')
const [sim, cart] = await parallel([
  () => agent(`${BG}

YOUR TASK (folder ${OUT}/sim/): re-validate Tarçın v2 in MuJoCo with the NEW CAD (masses, CoM, leg geometry, paws) — build the model
from ${OUT}/cad/ outputs, reusing the package's tarcin.py approach (torque-speed limited MG90S, 0.20 N·m; also a sagging case 0.16).
Run: flat-desk walk with the chosen gait, turn, K1 keyboard (rows + diagonal), K2 diagonal, the full self-righting suite of the package
(side/back/front falls, friction 0.4/0.6), servo peak/p95 torques per joint, and the supply-current peaks per servo bank (compare with
the chosen regulators and the LiPo). Report regressions vs the package honestly and propose gait/sequence retunes if something fails
(apply them if they are parameter-level). Also regenerate the viewer package (model.glb + manifest + anim clips) for Tarçın v2 in
${OUT}/sim/pkg/ following the package conventions, so the 3D viewer can show it.

CAD RESULT (JSON): ${JSON.stringify(cad)}
LEGS RESULT (JSON): ${JSON.stringify(legs)}
ELECTRONICS RESULT (JSON): ${JSON.stringify(elec)}`, { label: 'validate:sim', phase: 'Validate', schema: {
    type: 'object',
    properties: { summary: STR, results_table: STR, currents: STR, regressions: ARR, retunes: STR, viewer_pkg: STR, files: FILES },
    required: ['summary', 'results_table', 'currents', 'regressions', 'retunes', 'files'],
  } }),
  () => agent(`${BG}

YOUR TASK (folder ${OUT}/sepet/): the final shopping list and cost of Tarçın v2, plus the tool kit. Re-verify TODAY every line's price
and stock on its shop page. Group the cart by shop and optimise for each shop's free-shipping threshold (Robotistan/Direnc/Robolink/
Robo90 1,500 TL, Motorobit/Robot Sepeti 2,500 TL) without paying more overall; include spares (2 MG90S), screws/inserts from the CAD
list, wires/heat-shrink/servo extensions, the LiPo + balance charger + alarm + pigtail, and the beginner tool kit (60 W adjustable pen
iron, stand, DT-830D multimeter, side cutter, 60/40 1 mm solder, flux, desoldering wick, practice perfboard + header strip; optional
helping hands / safety glasses / LiPo safe bag if found in Turkish stock). Compute the real cost with the package method (parts +
services + print-studio estimate from the CAD's slicer grams/hours + shipping) and show: robot only, tools, Claude API credit estimate.
Write sepet.json and a Turkish sepet.md (table per shop with links, quantities, prices, subtotals, free-shipping notes, totals).

ELECTRONICS RESULT (JSON): ${JSON.stringify(elec)}
CAD RESULT (JSON): ${JSON.stringify(cad)}`, { label: 'validate:cart', phase: 'Validate', schema: {
    type: 'object',
    properties: { summary: STR, totals: STR, by_shop: STR, changes_vs_package: STR, files: FILES },
    required: ['summary', 'totals', 'by_shop', 'changes_vs_package', 'files'],
  } }),
])

const guide = await agent(`${BG}

YOUR TASK (folder ${OUT}/kilavuz/): write the family's Turkish build guide for Tarçın v2 as Markdown files with images/diagrams:
 1. KILAVUZ.md — the whole journey in order: what to buy (link to sepet.md), sending the parts to a print studio (a ready message like
    BASKI.md, with the STL list, colours, materials, settings), tool setup, SAFETY (lead solder hygiene, iron, LiPo rules: balance
    charger only, never unattended, storage, puffy pack = stop), a soldering LESSON for a total beginner (what a good joint looks like,
    practice plan on perfboard: 50-100 joints, common mistakes and how to fix them with wick; suggest YouTube search terms in Turkish
    and the Adafruit Guide to Excellent Soldering), then module-by-module soldering with "kolay"/"dikkat" marks and a photo checkpoint
    ("send a close-up photo to Claude before continuing"), setting the bucks with the multimeter BEFORE connecting anything, the first
    power-on checklist, mechanical assembly in the CAD's order (servo centring before fitting horns!), cable routing through neck and
    hips, closing the shell, charging the pack, and troubleshooting (resets/brownouts, a servo buzzing, a blank eye).
 2. A clear wiring diagram (reuse the electronics SVG; add a simple per-module pin table).
 Use plain words; explain every term once (pin, header, pad, flux, buck, PCA9685...). Number steps; one action per step; say how long
 each stage takes. Note that the firmware will be provided later as a browser flasher (ESP Web Tools) and keep a placeholder section.

ELECTRONICS: ${JSON.stringify(elec)}
CAD: ${JSON.stringify(cad)}
SIM: ${JSON.stringify(sim)}
CART: ${JSON.stringify(cart)}`, { label: 'validate:guide', phase: 'Validate', schema: {
  type: 'object', properties: { summary: STR, files: FILES, stage_times: STR }, required: ['summary', 'files', 'stage_times'],
} })

phase('Review')
const ALL = JSON.stringify({ elec, legs, cad, sim, cart, guide })
const REVIEW = {
  type: 'object',
  properties: { problems: { type: 'array', items: { type: 'object', properties: { severity: STR, where: STR, problem: STR, fix: STR }, required: ['severity', 'where', 'problem', 'fix'] } }, verdict: STR },
  required: ['problems', 'verdict'],
}
const [hwReview, beginnerReview] = await parallel([
  () => agent(`${BG}

YOU ARE A SKEPTICAL HARDWARE REVIEWER (folder ${OUT}/inceleme_donanim/). Try to break Tarçın v2: open the STLs (manifold, wall
thickness, overhangs, unsupported bridges, tolerances, part fits, screw boss sizes for M2 self-tappers, can the pack hatch really open
and hold, can servos/horns/wires actually be assembled in the stated order, does the board's USB-C remain reachable), re-slice a few
parts, check the electronics (pin map conflicts, current paths and wire gauges, connector ratings, LiPo cutoff/alarm, buck settings,
brownout), check that the cart contains everything the CAD and wiring need (screws, wires, connectors) at the stated prices, and that
the simulation claims hold (re-run a couple of cases). List every real problem with a concrete fix; severity blocker/major/minor.

ALL RESULTS (JSON): ${ALL}`, { label: 'review:hardware', phase: 'Review', schema: REVIEW }),
  () => agent(`${BG}

YOU ARE A TOTAL BEGINNER READING THE GUIDE (folder ${OUT}/inceleme_acemi/). You have never held a soldering iron, you have no tools,
you read Turkish. Read ${OUT}/kilavuz/ and the cart (${OUT}/sepet/sepet.md) start to finish as this person. Flag every step that is
unclear, assumes knowledge, uses an unexplained term, skips a needed action, has a wrong order, is unsafe, or would make you give up;
say exactly what is missing and suggest the fixed wording. Also check the print-studio message is something you could just send.

GUIDE/CART RESULTS (JSON): ${JSON.stringify({ guide, cart })}`, { label: 'review:beginner', phase: 'Review', schema: REVIEW }),
])

phase('Fix')
const fix = await agent(`${BG}

YOUR TASK: apply the reviews' fixes to Tarçın v2 (CAD in ${OUT}/cad/, electronics ${OUT}/elec/, cart ${OUT}/sepet/, guide
${OUT}/kilavuz/, sim ${OUT}/sim/). Fix every blocker and major, and every minor that is cheap; re-export/re-slice changed parts, re-verify
changed prices, update the guide text and cart totals so all documents agree. Do not fix by hiding problems: if something cannot be
fixed, say so in the guide's "bilinen sınırlar" section. Return what you changed and what remains.

HARDWARE REVIEW: ${JSON.stringify(hwReview)}
BEGINNER REVIEW: ${JSON.stringify(beginnerReview)}
ALL RESULTS: ${ALL}`, { label: 'fix:apply', phase: 'Fix', schema: {
  type: 'object', properties: { changed: ARR, remaining: ARR, final_cost: STR, final_files: FILES, summary_tr: STR }, required: ['changed', 'remaining', 'final_cost', 'final_files', 'summary_tr'],
} })

return { elec, legs, cad, sim, cart, guide, hwReview, beginnerReview, fix }
