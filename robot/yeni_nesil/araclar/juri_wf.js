export const meta = {
  name: 'kipir-juri',
  description: 'Independent 3-lens jury (appeal, engineering/sim, cost/build) over the 4 finished robot packages, then a chair writes the final Turkish verdict with the honest real cost of each',
  phases: [
    { title: 'Jury', detail: 'appeal, engineering, cost/build, each scoring all 4 packages independently' },
    { title: 'Chair', detail: 'synthesis into the final Turkish jury JSON for the viewer' },
  ],
}

const PK = args.paket, OUT = args.out, SPEC = args.spec
const CTX = `Four desk-robot concepts were packaged for a family in Turkey who will pick ONE to build.
The family's budget is 5-10k TL max (ideally ≤5k). They want it cute, well made, walking well, and able to call the Claude API over Wi-Fi; getting up after falls is a bonus.
The packages are in ${PK}/A (Tosbi), ${PK}/B (Tarçın), ${PK}/C (Fındık) and ${PK}/D (Yumurcak). Each has manifest.json, bom.json, NOTES.md, stills/*.png (realistic renders: FDM layer lines, real screens), sim/ (MuJoCo models and results) and anim/*.json.
Read ${SPEC} for what everything means.
Judge only on evidence in the packages: open the stills with the Read tool, read the sim results and the bom.json lines. Ignore marketing language.`

const SCORE = { type: 'object', properties: { scores: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, score: { type: 'number' }, evidence: { type: 'string' }, strengths: { type: 'array', items: { type: 'string' } }, weaknesses: { type: 'array', items: { type: 'string' } } }, required: ['key', 'score', 'evidence', 'strengths', 'weaknesses'] } }, ranking: { type: 'array', items: { type: 'string' } }, note: { type: 'string' } }, required: ['scores', 'ranking', 'note'] }

const LENSES = [
  { key: 'gorunus', name: 'Görünüş', p: 'APPEAL: You are a consumer toy/robot product designer. Look at every still, especially the hero, face, macro and action shots. Score cuteness, charm and premium feel AS IT WILL REALLY LOOK when FDM-printed, with the real screens. Score whether a non-technical person would love it on their desk. Penalise anything that will look worse in reality than in the render.' },
  { key: 'muhendislik', name: 'Yürüyüş ve kalkma', p: 'ENGINEERING: You are a legged-robotics engineer. Use the sim results (walk speed, stability, fall_recover success rates at μ 0.6 and 0.4), torque margins, power/battery fit, and the MJCF fidelity vs the CAD. Score how well it will REALLY move and recover. Penalise results that are only quasi-static or hand-animated.' },
  { key: 'maliyet', name: 'Maliyet ve yapım', p: 'COST & BUILD: You are a maker-workshop instructor in Turkey. Check every bom.json line against the shop URL (curl or WebFetch a few of the most expensive ones), recompute the total, and add any forgotten items. Judge the build difficulty for a beginner family with a soldering iron, the sourcing risk (stock), and the print difficulty (supports, multi-colour, TPU, visor). Report your own honest real-cost range for each.' },
]

phase('Jury')
const jur = await parallel(LENSES.map(l => () => agent(`${CTX}\n\n${l.p}\nScore each of A, B, C and D from 1 to 10 under YOUR lens only. Cite evidence (file names, numbers) and rank them.`,
  { label: `jury:${l.key}`, phase: 'Jury', schema: SCORE, effort: 'high' })))

phase('Chair')
const FINAL = { type: 'object', properties: {
  summary_tr: { type: 'string' }, recommendation_tr: { type: 'string' },
  ranking: { type: 'array', items: { type: 'object', properties: {
    key: { type: 'string' }, rank: { type: 'number' }, score_total: { type: 'number' },
    scores: { type: 'object', properties: { 'Görünüş': { type: 'number' }, 'Yürüyüş ve kalkma': { type: 'number' }, 'Maliyet ve yapım': { type: 'number' } }, required: ['Görünüş', 'Yürüyüş ve kalkma', 'Maliyet ve yapım'] },
    verdict_tr: { type: 'string' }, pros: { type: 'array', items: { type: 'string' } }, cons: { type: 'array', items: { type: 'string' } },
    real_cost_tl: { type: 'array', items: { type: 'number' } }, real_cost_note_tr: { type: 'string' } },
    required: ['key', 'rank', 'score_total', 'scores', 'verdict_tr', 'pros', 'cons', 'real_cost_tl', 'real_cost_note_tr'] } } },
  required: ['summary_tr', 'recommendation_tr', 'ranking'] }
const final = await agent(`${CTX}\n\nYou chair the jury. These are the three independent lens reports: ${JSON.stringify(jur.map((j, i) => j && ({ lens: LENSES[i].name, ...j })))}
Write the final verdict in natural, plain Turkish (the user reads Turkish), for the interactive viewer.
- **Weights:** score_total = 0.35 × Görünüş + 0.40 × Yürüyüş ve kalkma + 0.25 × Maliyet ve yapım, rounded to 1 decimal.
- **real_cost_tl:** [min, max] in TL, all-in (parts + print + shipping). Use the cost juror's numbers and bom.json; do not include tools.
- **Per robot:** 3-5 short pros and 3-5 short cons, and a 2-3 sentence verdict_tr.
- **recommendation_tr:** 3-5 sentences. Say which one to build and why, and which is the best cheaper alternative if one exists.
- **summary_tr:** 2-3 sentences about the overall comparison.
- **Tone:** be honest about what is uncertain (e.g. untested on hardware, sim simplifications).
Write the JSON also to ${OUT} (python json.dump with ensure_ascii=False, indent=1).`,
  { label: 'chair', phase: 'Chair', schema: FINAL, effort: 'high' })
return { jur, final }
