#!/usr/bin/env node
// posecheck: render a robot PACKAGE (manifest.json + model.glb ...) exactly the way the web viewer will show it.
// Usage: node posecheck.js <packageDir> <shots.json> [outDir]
// shots.json: {"width":1400,"height":1050,"shots":[
//   {"name":"rest_hero","azimuth":30,"elevation":15},
//   {"name":"walk_0","anim":"walk","t":0.0}, {"name":"walk_1","anim":"walk","t":0.4,"azimuth":90},
//   {"name":"xray","xray":true}, {"name":"happy","face":"happy","pose":{"tail":40}} ]}
// Prints the package's joints/screens/anims so you can check that the GLB node names match the manifest.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
(async () => {
  const pkg = path.resolve(process.argv[2]); const shotsPath = path.resolve(process.argv[3]);
  const out = path.resolve(process.argv[4] || path.join(pkg, 'check'));
  fs.mkdirSync(out, { recursive: true });
  const cfg = JSON.parse(fs.readFileSync(shotsPath, 'utf8'));
  const lib = __dirname;
  const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.glb': 'model/gltf-binary' };
  const srv = http.createServer((q, s) => {
    const u = decodeURIComponent(q.url.split('?')[0]);
    let f = u === '/' ? path.join(lib, 'pose.html') : u === '/cfg.json' ? shotsPath : u.startsWith('/pkg/') ? path.join(pkg, u.slice(5)) : path.join(lib, u);
    if (!fs.existsSync(f)) { s.statusCode = 404; s.end(); return; }
    s.setHeader('Content-Type', types[path.extname(f)] || 'application/octet-stream'); s.end(fs.readFileSync(f));
  }).listen(0);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const W = cfg.width || 1400, H = cfg.height || 1050;
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (['error', 'warning'].includes(m.type())) errs.push(m.text()); });
  await p.goto(`http://localhost:${srv.address().port}/`);
  try { await p.waitForFunction('window.READY === true', { timeout: 240000 }); }
  catch (e) { console.error('LOAD FAILED:\n' + errs.join('\n')); await b.close(); srv.close(); process.exit(1); }
  console.log('package:', JSON.stringify(await p.evaluate(() => window.state)));
  for (const s of cfg.shots) {
    const res = await p.evaluate(s => window.renderShot(s), s);
    if (res !== 'ok') { console.error(s.name, res); continue; }
    const f = path.join(out, s.name + '.png'); await p.locator('canvas').screenshot({ path: f }); console.log('wrote', f);
  }
  if (errs.length) console.error('page messages:\n' + errs.join('\n'));
  await b.close(); srv.close();
})();
