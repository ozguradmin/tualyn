export const meta = {
  name: 'kipir-paket',
  description: 'Turn one robot concept into a realistic, articulated, physically simulated package for the interactive viewer (rig + faces + MuJoCo clips + verified BOM), then review and fix it',
  phases: [
    { title: 'Rig & Cost', detail: 'articulated GLB with realistic materials and faces; live-verified BOM' },
    { title: 'Motion', detail: 'MuJoCo-simulated clips: walk, turn, fall_recover, plus idle/talk/happy/sleep' },
    { title: 'Review', detail: 'adversarial realism/physics/cost review' },
    { title: 'Fix', detail: 'apply review findings, re-render stills' },
  ],
}

const K = args.key, SRC = args.src, PKG = args.pkg, SPEC = args.spec, GUIDE = args.guide, RENDER = args.render
const CTX = `You are packaging robot concept ${K} (${args.title}) for an interactive browser viewer that the user will use to choose which robot to build.
Read ${SPEC} completely and follow it exactly. Also read ${GUIDE}.
Concept source folder (read-only for you): ${SRC} (concept.md, model.py, STLs, eye drawings, calc files, renders, any sim/).
Package folder (yours to write): ${PKG}. Shared tools: ${RENDER} (realism.js, rig.js, posecheck.js, render.js, testpkg/).
Never write into /home/user/tualyn. CPU is shared by several workers (4 cores), so avoid needless re-renders; 1400x1050 is enough.`

const RIG_SCHEMA = { type: 'object', properties: { joints: { type: 'array', items: { type: 'string' } }, links: { type: 'array', items: { type: 'string' } }, triangles: { type: 'number' }, faces: { type: 'array', items: { type: 'string' } }, stills: { type: 'array', items: { type: 'string' } }, realism_notes: { type: 'string' }, issues: { type: 'string' } }, required: ['joints', 'links', 'triangles', 'faces', 'stills', 'realism_notes', 'issues'] }
const MOTION_SCHEMA = { type: 'object', properties: { clips: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, seconds: { type: 'number' }, simulated: { type: 'boolean' }, result: { type: 'string' } }, required: ['name', 'seconds', 'simulated', 'result'] } }, walk_speed_cm_s: { type: 'number' }, recovery_summary: { type: 'string' }, strips: { type: 'array', items: { type: 'string' } }, honesty_notes: { type: 'string' } }, required: ['clips', 'walk_speed_cm_s', 'recovery_summary', 'strips', 'honesty_notes'] }
const COST_SCHEMA = { type: 'object', properties: { total_tl_min: { type: 'number' }, total_tl_max: { type: 'number' }, parts_tl: { type: 'number' }, print_tl: { type: 'string' }, unverified: { type: 'array', items: { type: 'string' } }, out_of_stock: { type: 'array', items: { type: 'string' } }, changes_vs_concept: { type: 'string' } }, required: ['total_tl_min', 'total_tl_max', 'parts_tl', 'print_tl', 'unverified', 'out_of_stock', 'changes_vs_concept'] }
const REVIEW_SCHEMA = { type: 'object', properties: { verdict: { type: 'string', enum: ['ship', 'fix', 'broken'] }, findings: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, area: { type: 'string' }, issue: { type: 'string' }, fix: { type: 'string' } }, required: ['severity', 'area', 'issue', 'fix'] } } }, required: ['verdict', 'findings'] }

phase('Rig & Cost')
const [rig, cost] = await parallel([
  () => agent(`${CTX}

TASK: build the RIG part of the package.
1. Create the articulated model.glb from the concept's model.py: links, joint origins and axes as in the concept's mechanism. Include realistic internals (internal_*), visible seams, and screw heads where real.
2. Write manifest.json: materials with real filament names and colours, plus layerAxis per part according to its print orientation; screens; joints with real limits; pose_rest; specs; realism_notes_tr written in Turkish.
3. Draw the faces at native screen resolution: neutral, blink, happy, talk_a, talk_b, plus surprised, sleepy, sad and determined when they make sense for this character.
4. Write a placeholder anim/idle.json (a 2 s breathing loop) so posecheck can test animation playback.
5. Verify with posecheck:
   - rest hero, front, side, back, top
   - macro of the face showing the screen pixels and bezel
   - macro of a printed surface showing layer lines and seams
   - xray
   - a few joint-limit poses, to check that axes and directions are right and that nothing intersects badly
6. Iterate until the posecheck renders look like the real printed robot and match the concept renders in form. Save the final stills in ${PKG}/stills/.`,
    { label: `rig:${K}`, phase: 'Rig & Cost', schema: RIG_SCHEMA, effort: 'high' }),
  () => agent(`${CTX}

TASK: write the verified BOM (bom.json) for this concept.
1. Start from the concept's BOM in concept.md, calc files, or the concept summary.
2. Re-check EVERY line's price and stock live on the Turkish shop pages (curl/WebFetch the product URL; KDV-included TL). Fix wrong URLs. Find in-stock alternatives for out-of-stock lines.
3. Add the forgotten items: wires, connectors, screws, magnets, solder, heat-shrink, glue, a USB cable for flashing, a charger.
4. Estimate the 3D print cost from grams and hours. The concept STLs give the volumes; use typical Turkish studio rates (search for current rates if possible), and add multi-material/TPU/PETG surcharges.
5. Estimate shipping per shop using their free-shipping thresholds.
6. Give the honest real total range, a lean variant, and the tools cost if the family has none (soldering iron, multimeter).
Write ${PKG}/bom.json per SPEC and return the summary.`,
    { label: `cost:${K}`, phase: 'Rig & Cost', schema: COST_SCHEMA, effort: 'high' }),
])

phase('Motion')
const motion = await agent(`${CTX}

The rig is done. Summary: ${JSON.stringify(rig)}
TASK: produce the animation clips per SPEC with MuJoCo (python3 -c "import mujoco" works, v3.17):
- walk, turn and fall_recover must be physically simulated, using the real masses, MG90S torque limits and contact.
- idle, talk, happy and sleep may be kinematic, but they must stay statically stable. Check them in the sim too if cheap.
- Build an MJCF that mirrors the GLB link frames exactly, so that recorded joint angles and base poses replay correctly in rig.js: same joint origins, axes and zero.
- If the concept already has a sim (look in ${SRC}/sim or similar), reuse and extend it.
- Tune the gait for real, stable progress and report the measured speed.
- For fall_recover, tip or push the robot over (side and/or back as appropriate) and run the concept's real recovery strategy. Report the success rate over several fall orientations and at μ 0.6 and 0.4.
- Show failures honestly in the notes.
Write anim/*.json and update manifest.animations, specs and sim_summary. Then verify playback with posecheck strips (several t values per clip, from a fixed camera) and save them to ${PKG}/stills/anim_*.png. Look at them: no floating, no ground penetration, no limbs passing through the body, and the face timing works.`,
  { label: `motion:${K}`, phase: 'Motion', schema: MOTION_SCHEMA, effort: 'high' })

phase('Review')
const review = await agent(`${CTX}

You are an ADVERSARIAL reviewer. The user will pick a robot to BUILD based on this package, so anything that looks better than reality, or any motion that cannot really happen, is a defect.
Rig summary: ${JSON.stringify(rig)}
Motion summary: ${JSON.stringify(motion)}
Cost summary: ${JSON.stringify(cost)}
Check everything:
- Run posecheck yourself and look at the renders, including the anim strips.
- Do the joints match the mechanism?
- Are the realism items from the SPEC realism checklist present? Layer lines, seams, real screen resolution and active area, real filament colours, visible screws and wires.
- Do the MJCF masses, torques and frames match the GLB, and do the replayed clips match the sim?
- Does fall_recover really come from the sim?
- Are the BOM prices plausible, and do the totals add up?
- Is manifest.json complete per SPEC?
List the findings with concrete fixes.`,
  { label: `review:${K}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })

phase('Fix')
const fix = review && review.findings && review.findings.length ? await agent(`${CTX}

Apply these review findings to the package (all blockers and majors, and any minors that are cheap to fix): ${JSON.stringify(review.findings)}
Re-run posecheck and re-render the stills and anim strips that changed. Return a short report of what was fixed and what remains.`,
  { label: `fix:${K}`, phase: 'Fix', effort: 'high' }) : 'no findings'

return { key: K, rig, cost, motion, review, fix }
