// Load the artifact build under a CSP like the Artifact viewer's (fetch only to own files; data:/blob: only for images/media)
// inside a sandboxed iframe, and exercise every robot, view and motion.
// Usage: node qa/csp_check.js <dir> [--mobile] [--quick]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const CSP = ["default-src 'self'", "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://cdn.tailwindcss.com https://code.jquery.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", "font-src 'self' https://fonts.gstatic.com data:", "img-src 'self' data: blob:",
  "media-src 'self' data: blob:", "connect-src 'self'", "worker-src 'self' blob:", "frame-src 'none'", "object-src 'none'"].join('; ');
const SKEL_HEAD = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>';
(async () => {
  const dir = path.resolve(process.argv[2]); const mobile = process.argv.includes('--mobile'), quick = process.argv.includes('--quick');
  const out = path.join(__dirname, 'csp_' + (mobile ? 'phone' : 'desk')); fs.mkdirSync(out, { recursive: true });
  const types = { '.json': 'application/json', '.png': 'image/png', '.txt': 'text/plain; charset=utf-8', '.html': 'text/html; charset=utf-8' };
  const srv = http.createServer((q, s) => {
    const u = decodeURIComponent(q.url.split('?')[0]);
    if (u === '/') { s.setHeader('Content-Type', 'text/html; charset=utf-8'); s.end(`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>html,body,iframe{margin:0;border:0;width:100%;height:100%;display:block}</style><iframe sandbox="allow-scripts allow-same-origin allow-forms allow-popups" src="/a/"></iframe>`); return; }
    const rel = u.startsWith('/a/') ? u.slice(3) : null;
    if (rel === null) { s.statusCode = 404; s.end(); return; }
    s.setHeader('Content-Security-Policy', CSP);
    if (rel === '') { s.setHeader('Content-Type', 'text/html; charset=utf-8'); s.end(SKEL_HEAD + fs.readFileSync(path.join(dir, 'artifact.html'), 'utf8') + '</body></html>'); return; }
    const f = path.join(dir, rel);
    if (!fs.existsSync(f) || !f.startsWith(dir)) { s.statusCode = 404; s.end(); return; }
    s.setHeader('Content-Type', types[path.extname(f)] || 'application/octet-stream'); s.end(fs.readFileSync(f));
  }).listen(0);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: mobile ? { width: 400, height: 860 } : { width: 1400, height: 860 }, deviceScaleFactor: 1, hasTouch: mobile, isMobile: mobile });
  p.setDefaultTimeout(180000);
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message)); p.on('console', m => { if (['error', 'warning'].includes(m.type())) errs.push(m.type() + ': ' + m.text().slice(0, 300)); });
  p.on('requestfailed', r => errs.push('requestfailed: ' + r.url().slice(0, 120) + ' ' + (r.failure()?.errorText || '')));
  await p.goto(`http://localhost:${srv.address().port}/`);
  const fr = await (await p.waitForSelector('iframe')).contentFrame();
  const t0 = Date.now();
  await fr.waitForFunction(() => document.querySelector('#loading')?.hidden === true || /Yüklenemedi/.test(document.querySelector('#loading')?.textContent || ''), null, { timeout: 300000 });
  const status = await fr.$eval('#loading', e => (e.hidden ? 'OK' : 'FAIL') + ' ' + e.textContent.slice(0, 300));
  console.log('load:', status, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  await p.waitForTimeout(2000); await p.screenshot({ path: path.join(out, '0_overview.png') });
  if (status.startsWith('OK') && !quick) {
    const keys = await fr.evaluate(() => window.__kipir.robots.map(r => r.key));
    const anims = ['idle', 'walk', 'turn', 'talk', 'happy', 'fall_recover', 'sleep'];
    for (const k of keys) {
      await fr.click('#chip-' + k, { force: true }); await p.waitForTimeout(1500);
      for (const a of anims) {
        const el = await fr.$('#anim-' + a); if (!el || await el.evaluate(e => e.disabled)) continue;
        await el.click({ force: true }); await p.waitForTimeout(700);
      }
      for (const v of ['#vface', '#vmacro', '#xray', '#xray']) { const el = await fr.$(v); if (el) { await el.click({ force: true }); await p.waitForTimeout(500); } }
      for (const t of ['ozellik', 'maliyet', 'gercek', 'juri']) { const el = await fr.$('#tab-' + t); if (el) { await el.click({ force: true }); await p.waitForTimeout(150); } }
      await p.screenshot({ path: path.join(out, `1_${k}.png`) });
    }
    await fr.click('#chip-all', { force: true }); await p.waitForTimeout(1000);
    await fr.click('#anim-walk', { force: true }); await p.waitForTimeout(2500);
    await p.screenshot({ path: path.join(out, '2_all_walk.png') });
  }
  fs.writeFileSync(path.join(out, 'errors.txt'), errs.join('\n'));
  console.log('errors/warnings:', errs.length ? '\n' + [...new Set(errs)].slice(0, 25).join('\n') : 'none');
  await b.close(); srv.close();
})();
