#!/usr/bin/env node
// Screenshot the built viewer in headless Chromium and run scripted interactions.
// Usage: node shoot.js [outDir] [--offline] [--mobile]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
(async () => {
  const out = path.resolve(process.argv[2] || 'shots'); fs.mkdirSync(out, { recursive: true });
  const offline = process.argv.includes('--offline'), mobile = process.argv.includes('--mobile');
  const dist = path.join(__dirname, 'dist');
  const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.glb': 'model/gltf-binary' };
  const srv = http.createServer((q, s) => {
    const u = decodeURIComponent(q.url.split('?')[0]); const f = path.join(dist, u === '/' ? (offline ? 'kipir_tek_dosya.html' : 'index.html') : u);
    if (!fs.existsSync(f)) { s.statusCode = 404; s.end(); return; }
    s.setHeader('Content-Type', types[path.extname(f)] || 'application/octet-stream'); s.end(fs.readFileSync(f));
  }).listen(0);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const vp = mobile ? { width: 400, height: 860 } : { width: 1500, height: 900 };
  const p = await b.newPage({ viewport: vp, deviceScaleFactor: 1 });
  p.setDefaultTimeout(180000);
  const errs = []; p.on('pageerror', e => errs.push('pageerror: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.goto(`http://localhost:${srv.address().port}/`);
  await p.waitForFunction(() => document.querySelector('#loading')?.hidden === true || /Yüklenemedi/.test(document.querySelector('#loading')?.textContent || ''), { timeout: 300000 });
  const wait = (ms) => p.waitForTimeout(ms);
  await wait(1500); await p.screenshot({ path: path.join(out, '01_lineup.png') });
  const keys = await p.evaluate(() => window.__kipir.robots.map(r => r.key));
  for (const k of keys) {
    await p.click("#chip-" + k); await wait(3000); await p.screenshot({ path: path.join(out, `02_${k}_34.png`) });
    await p.click("#vface"); await wait(3000); await p.screenshot({ path: path.join(out, `03_${k}_face.png`) });
    await p.click("#vmacro"); await wait(3000); await p.screenshot({ path: path.join(out, `04_${k}_macro.png`) });
    for (const a of ['walk', 'fall_recover']) {
      const dis = await p.$eval('#anim-' + a, el => el.disabled);
      if (dis) continue;
      await p.click("#v34"); await wait(2500); await p.click('#anim-' + a);
      for (const t of [1, 3]) { await wait(t === 1 ? 1000 : 2000); await p.screenshot({ path: path.join(out, `05_${k}_${a}_${t}s.png`) }); }
    }
    await p.click('#xray'); await wait(700); await p.screenshot({ path: path.join(out, `06_${k}_xray.png`) }); await p.click('#xray');
    await p.click('#tab-maliyet'); await wait(300); await p.screenshot({ path: path.join(out, `07_${k}_cost.png`) });
  }
  await p.click('#chip-all'); await wait(1200); await p.click('#anim-walk'); await wait(2500); await p.screenshot({ path: path.join(out, '08_all_walk.png') });
  fs.writeFileSync(path.join(out, 'errors.txt'), errs.join('\n'));
  console.log('errors:', errs.length ? errs.slice(0, 20).join('\n') : 'none');
  await b.close(); srv.close();
})();
