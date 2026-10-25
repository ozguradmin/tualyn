#!/usr/bin/env node
// Photoreal-ish renderer for robot concept models (Three.js + headless Chromium).
// Usage: node render.js path/to/scene.json [outdir]
// scene.json: {
//   "width":1600, "height":1200, "background":"#efece6", "exposure":1.0,
//   "parts":[{"file":"body.stl","color":"#f4efe6","roughness":0.4,"clearcoat":0.3,
//             "image":"eyes.png","uvAxes":["x","z"],"imageEmissive":1.2,"position":[0,0,0],"rotation":[0,0,0]}],
//   "views":[{"name":"hero","azimuth":35,"elevation":18,"distance":1.0,"fov":28}]
// }
// Model units: mm, Z up, robot faces -Y. Files in "parts" are relative to the scene.json folder.
// azimuth 0 = straight from the front; +az = from the robot's right side; elevation in degrees.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

(async () => {
  const scenePath = path.resolve(process.argv[2]);
  const sceneDir = path.dirname(scenePath);
  const outDir = path.resolve(process.argv[3] || sceneDir);
  fs.mkdirSync(outDir, { recursive: true });
  const spec = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
  const libDir = __dirname;
  const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.stl': 'application/octet-stream', '.glb': 'model/gltf-binary' };
  const srv = http.createServer((q, s) => {
    let u = decodeURIComponent(q.url.split('?')[0]);
    let f;
    if (u === '/' ) f = path.join(libDir, 'page.html');
    else if (u === '/scene.json') f = scenePath;
    else if (fs.existsSync(path.join(libDir, u)) && /\.(js|html)$/.test(u)) f = path.join(libDir, u);
    else f = path.join(sceneDir, u);
    if (!fs.existsSync(f)) { s.statusCode = 404; s.end('nf ' + u); return; }
    s.setHeader('Content-Type', types[path.extname(f)] || 'application/octet-stream');
    s.end(fs.readFileSync(f));
  }).listen(0);
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const W = spec.width || 1600, H = spec.height || 1200;
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(`http://localhost:${port}/`);
  try { await p.waitForFunction('window.READY === true', { timeout: 180000 }); }
  catch (e) { console.error('render failed:', errs.join('\n')); await b.close(); srv.close(); process.exit(1); }
  const views = spec.views || [{ name: 'hero' }];
  for (const v of views) {
    await p.evaluate(v => window.renderView(v), v);
    const out = path.join(outDir, (v.name || 'view') + '.png');
    await p.locator('canvas').screenshot({ path: out });
    console.log('wrote', out);
  }
  if (errs.length) console.error('page warnings:', errs.join('\n'));
  await b.close(); srv.close();
})();
