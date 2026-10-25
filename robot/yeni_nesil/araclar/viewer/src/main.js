// Kıpır desk-robot viewer: 4 concepts at true scale, realistic print/screen materials, MuJoCo-recorded motions.
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { loadRobot } from './rig.js';

// ---------- assets: published files (artifact / http server) or embedded base64 (offline single file) ----------
const EMB = window.__KIPIR_ASSETS__ || null;
const blobCache = {};
const MIME = { glb: 'model/gltf-binary', png: 'image/png', json: 'application/json', jpg: 'image/jpeg' };
function R(path) {
  if (!EMB || !EMB[path]) return path;
  if (blobCache[path]) return blobCache[path];
  const bin = atob(EMB[path]); const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return (blobCache[path] = URL.createObjectURL(new Blob([u8], { type: MIME[path.split('.').pop()] || 'application/octet-stream' })));
}
async function getJSON(path) { return (await fetch(R(path))).json(); }

// ---------- DOM ----------
const $ = (s) => document.querySelector(s);
const canvas = $('#c'), stage = $('#stage');
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const rmq = matchMedia('(prefers-reduced-motion: reduce)');
let reduceMotion = rmq.matches;
const coarse = matchMedia('(pointer: coarse)').matches;   // phones/tablets: lighter shadows, lower pixel ratio
const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } } };

// ---------- three ----------
const renderer = (() => {
  try { return new THREE.WebGLRenderer({ canvas, antialias: !coarse || devicePixelRatio < 2, preserveDrawingBuffer: false }); }
  catch (e) { $('#loading').textContent = 'Bu tarayıcıda 3B görünüm (WebGL) açılamadı. Donanım hızlandırmayı açıp sayfayı yenile.'; throw e; }
})();
renderer.setPixelRatio(Math.min(devicePixelRatio, coarse ? 1.5 : 2));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = coarse ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.85;
const camera = new THREE.PerspectiveCamera(30, 1, 0.005, 30);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = !reduceMotion; controls.dampingFactor = 0.08; controls.minDistance = 0.04; controls.maxDistance = 3.5;
controls.maxPolarAngle = Math.PI * 0.495;
rmq.addEventListener?.('change', (e) => { reduceMotion = e.matches; controls.enableDamping = !reduceMotion; });

// lights
const key = new THREE.DirectionalLight('#fff6ea', 2.1); key.position.set(0.5, 1.0, 0.7); key.castShadow = true;
const smap = coarse ? 1024 : 2048;
key.shadow.mapSize.set(smap, smap); key.shadow.radius = 5; key.shadow.bias = -0.0003; key.shadow.normalBias = 0.002;
Object.assign(key.shadow.camera, { left: -0.6, right: 0.6, top: 0.6, bottom: -0.6, near: 0.05, far: 3 });
scene.add(key, key.target);
const rim = new THREE.DirectionalLight('#dce8ff', 0.7); rim.position.set(-0.8, 0.6, -0.8); scene.add(rim);
scene.add(new THREE.HemisphereLight('#ffffff', '#cfc6b8', 0.25));

// desk (subtle laminate noise so the floor does not look like CG void)
function deskTexture() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 512; const g = cv.getContext('2d');
  g.fillStyle = '#808080'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 9000; i++) { const v = 118 + Math.random() * 20; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(Math.random() * 512, Math.random() * 512, 1 + Math.random() * 3, 1); }
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(12, 12); return t;
}
const deskMat = new THREE.MeshStandardMaterial({ color: '#d9d2c6', roughness: 0.82, roughnessMap: deskTexture() });
const desk = new THREE.Mesh(new THREE.PlaneGeometry(4, 4), deskMat);
desk.rotation.x = -Math.PI / 2; desk.receiveShadow = true; scene.add(desk);
const grid = new THREE.GridHelper(1.2, 120, 0xa79f92, 0xc7c0b4); grid.position.y = 0.0003;
grid.material.transparent = true; grid.material.opacity = 0.55; grid.material.vertexColors = false; scene.add(grid);
scene.fog = new THREE.Fog('#e9e5de', 2.2, 4.5);   // softens the far desk edge into the background

// theme: scene background, desk, grid and fog follow the page tokens (light/dark, OS or data-theme)
function applyTheme() {
  const bg = new THREE.Color(css('--scene-bg') || '#e9e5de');
  scene.background = bg; scene.fog.color.copy(bg);
  deskMat.color.set(css('--scene-floor') || '#e2ddd4');
  const dark = css('color-scheme') === 'dark' || document.documentElement.dataset.theme === 'dark';
  grid.material.color.set(dark ? '#4a4f57' : '#b3ab9e'); grid.material.needsUpdate = true;
}
applyTheme();
matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', applyTheme);
new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

// scale references: 30 cm ruler, phone (75 x 160 x 8 mm), 1 TL coin (Ø26.15 mm)
function rulerTexture() {
  const cv = document.createElement('canvas'); cv.width = 3000; cv.height = 300; const g = cv.getContext('2d');
  g.fillStyle = '#f4f1ea'; g.fillRect(0, 0, 3000, 300); g.fillStyle = '#2b2b2b'; g.font = 'bold 54px sans-serif'; g.textAlign = 'center';
  for (let mm = 0; mm <= 300; mm++) {
    const x = 10 * mm; const h = mm % 10 === 0 ? 120 : mm % 5 === 0 ? 80 : 45;
    g.fillRect(Math.min(x, 2996), 0, 4, h);
    if (mm % 10 === 0 && mm > 0 && mm < 300) g.fillText(String(mm / 10), x, 190);
  }
  g.font = '600 40px sans-serif'; g.textAlign = 'left'; g.fillText('cm', 2880, 270);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
const ruler = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.0015, 0.03),
  [0, 0, 1, 0, 0, 0].map((m) => m ? new THREE.MeshStandardMaterial({ map: rulerTexture(), roughness: 0.5 }) : new THREE.MeshStandardMaterial({ color: '#e8e4dc', roughness: 0.5 })));
ruler.receiveShadow = true; ruler.castShadow = true; scene.add(ruler);

const phone = new THREE.Group();
{
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.075, 0.16, 0.008), new THREE.MeshPhysicalMaterial({ color: '#2a2d33', roughness: 0.35, metalness: 0.3 }));
  const cv = document.createElement('canvas'); cv.width = 300; cv.height = 640; const g = cv.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 300, 640); grd.addColorStop(0, '#24324f'); grd.addColorStop(1, '#5a3d6b'); g.fillStyle = grd; g.fillRect(0, 0, 300, 640);
  g.fillStyle = '#ffffffd0'; g.font = '600 64px sans-serif'; g.textAlign = 'center'; g.fillText('09:41', 150, 150); g.font = '500 20px sans-serif'; g.fillText('telefon · 16 cm', 150, 600);
  const st = new THREE.CanvasTexture(cv); st.colorSpace = THREE.SRGBColorSpace;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.069, 0.152), new THREE.MeshPhysicalMaterial({ color: '#000', emissive: '#fff', emissiveMap: st, emissiveIntensity: 0.55, roughness: 0.08, clearcoat: 1 }));
  screen.position.z = 0.0041; body.add(screen); body.castShadow = true;
  phone.add(body); body.position.y = 0.08; body.rotation.x = -0.12; // leaning slightly back on a stand
  const stand = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.012, 0.03), new THREE.MeshStandardMaterial({ color: '#9aa0a8', roughness: 0.5 }));
  stand.position.set(0, 0.006, -0.012); stand.castShadow = true; phone.add(stand);
}
scene.add(phone);
const coin = new THREE.Group();
{
  // 1 TL (2009 series): yellow nickel-brass ring, white cupronickel core
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.013075, 0.013075, 0.0019, 64), new THREE.MeshPhysicalMaterial({ color: '#c8a85a', metalness: 1, roughness: 0.3 }));
  const core = new THREE.Mesh(new THREE.CylinderGeometry(0.0085, 0.0085, 0.00195, 64), new THREE.MeshPhysicalMaterial({ color: '#c9ccd1', metalness: 1, roughness: 0.32 }));
  coin.add(ring, core); coin.position.y = 0.00095; ring.castShadow = true;
}
scene.add(coin);

// ---------- state ----------
const robots = [];        // {key, rig, man, bom, x, box, size, half, offLocal, walkZ, anim:{name,t,playing,hold}, label}
let catalog = null, selected = null, tab = 'genel', xray = false, speed = 1, playing = true;
let compact = false;      // portrait phone: robots in a 2 x 2 grid instead of one row
const clock = new THREE.Clock();
const ANIMS = [
  ['idle', 'Bekle'], ['walk', 'Yürü'], ['turn', 'Dön'], ['talk', 'Konuş'], ['happy', 'Sevin'], ['fall_recover', 'Düş ve kalk'], ['sleep', 'Uyu'],
  ['fall_recover_back', 'Sırtüstü düş, kalk'], ['fall_back_help', 'Sırtüstü düş (yardım ister)'],
];
const EXTRA = new Set(['fall_recover_back', 'fall_back_help']);                  // only some robots have these
const SOLO = new Set(['fall_recover', 'fall_recover_back', 'fall_back_help']);   // drift sideways up to ~22 cm: one robot at a time
const MOVES = new Set(['walk', 'turn', ...SOLO]);                                // the body leaves its spot: neighbours are hidden
const animName = (k) => (ANIMS.find((x) => x[0] === k) || [0, k])[1];

// ---------- Turkish formatting ----------
const fmt = (n, d = 1) => Number(n).toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtN = (n) => fmt(n, Number(n) % 1 ? 1 : 0);
// small parts (capacitors, resistors) cost under 10 TL: keep the kuruş so a 0,34 TL line does not read "0 TL"
const fmtTL = (n) => n == null ? '–' : (n > 0 && n < 10 ? fmt(n, 2) : Math.round(n).toLocaleString('tr-TR')) + ' TL';
const fmtRange = (v) => Array.isArray(v) ? `${fmtN(v[0])}–${fmtN(v[1])}` : fmtN(v);
const dimsTxt = (d, sep = ' × ') => (d || []).map(fmtN).join(sep);
// package prose (already Turkish) still uses '.' decimals: 0.6 → 0,6 (keeps 1.500-style thousands and "MuJoCo 3.17")
const trn = (t) => String(t ?? '').replace(/(?<!MuJoCo |\d\.)(\d)\.(\d{1,2})(?![\d.])/g, '$1,$2').replace(/\b0\.(\d{3,})\b/g, '0,$1');
// drop simulation file references ("Sonuçlar: sim/out/x.json", "(sim/foo.py)") from prose meant for a family
const noPaths = (t) => String(t ?? '').replace(/\s*\([^()]*\b(?:sim|stills|anim)\/[^()]*\)/g, '').replace(/\s*(?:Sonuçlar|Kaynaklar|Ayrıntı|Komut)\s*:[^.]*?(?:\/|\.json|\.py)[^]*?(?=\.\s|$)\.?/g, '').trim();

// ---------- load ----------
async function boot() {
  catalog = await getJSON('pkg/catalog.json');
  // load every robot at once; one at a time costs ~130 sequential round trips on a phone
  const mans = await Promise.all(catalog.robots.map((e) => getJSON(`pkg/${e.key}/manifest.json`)));
  // the models are ~90 % of the data: show their download as a percentage (glb_bytes is set by the Artifact build)
  const total = mans.reduce((s, m) => s + (m.glb_bytes || 0), 0);
  let got = 0;
  const onBytes = total ? (n) => { got += n; $('#loading').textContent = `Robotlar yükleniyor… %${Math.min(99, Math.floor((got / total) * 100))}`; } : null;
  const loaded = await Promise.all(catalog.robots.map((entry, i) => {
    const base = `pkg/${entry.key}/`;
    return Promise.all([getJSON(base + 'bom.json').catch(() => null), loadRobot(THREE, GLTFLoader, base, mans[i], { resolve: (p) => R(base + p), onBytes })]);
  }));
  for (const [i, entry] of catalog.robots.entries()) {
    const man = mans[i], [bom, rig] = loaded[i];
    // shadows only where they read: shells cast, shells and desk receive (screens, visors and internals skip both)
    rig.meshes.forEach((m) => {
      const t = m.material.userData.def?.type, shell = ['print', 'tpu', 'petg', 'plastic', 'rubber'].includes(t);
      m.castShadow = shell && m.visible; m.receiveShadow = shell && t !== 'rubber';
      if (coarse && m.material.isMeshPhysicalMaterial && m.material.userData.print) { m.material.sheen = 0; m.material.clearcoat = 0; }
    });
    scene.add(rig.object);
    robots.push({ key: entry.key, rig, man, bom, anim: { name: 'idle', t: Math.random() * 3, playing: true }, blinkAt: 2 + Math.random() * 3 });
  }
  robots.forEach((r) => { samplePoints(r); sweepOf(r); });
  resize();
  layout();
  buildUI();
  frameAll(true);
  if (reduceMotion) setPlaying(false);          // start still; motions run when a button is pressed
  $('#loading').hidden = true;
  initVoices();
  new ResizeObserver(onResize).observe(canvas);
  new ResizeObserver(() => resize()).observe($('#dock'));
  // pause rendering while the stage is scrolled off-screen (phones)
  let looping = false;
  const loop = (on) => { if (on === looping) return; looping = on; if (on) clock.getDelta(); renderer.setAnimationLoop(on ? tick : null); };
  loop(true);
  if ('IntersectionObserver' in window) new IntersectionObserver(([e]) => loop(e.isIntersecting)).observe(canvas);
}

function meshBox(r) {
  // precise world box of the visible meshes (Box3.setFromObject without `precise` inflates rotated parts)
  const b = new THREE.Box3();
  r.rig.object.updateMatrixWorld(true);
  r.rig.meshes.forEach((m) => { if (m.visible) b.expandByObject(m, true); });
  return b;
}
// a few hundred vertices per mesh part (every n-th vertex plus each part's extremes): the CURRENT box of a moving robot
// (labels, group camera, clip sweeps) without walking 100k+ vertices every frame
function samplePoints(r) {
  r.pts = [];
  for (const m of r.rig.meshes) {
    if (!m.visible || r.rig.internal.includes(m)) continue;
    const pos = m.geometry.attributes.position; if (!pos) continue;
    const n = pos.count, step = Math.max(1, Math.floor(n / 48)), ext = new Array(6).fill(0), lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < n; i++) {
      for (let a = 0; a < 3; a++) { const v = pos.getComponent(i, a); if (v < lo[a]) { lo[a] = v; ext[2 * a] = i; } if (v > hi[a]) { hi[a] = v; ext[2 * a + 1] = i; } }
    }
    const idx = new Set(ext); for (let i = 0; i < n; i += step) idx.add(i);
    const arr = new Float32Array(idx.size * 3); let j = 0;
    for (const i of idx) { arr[j++] = pos.getX(i); arr[j++] = pos.getY(i); arr[j++] = pos.getZ(i); }
    r.pts.push({ m, arr });
  }
}
const _sp = new THREE.Vector3();
function curBox(r, out = new THREE.Box3()) {
  // world box from the sampled vertices; matrices must be current (scene.updateMatrixWorld / after render)
  out.makeEmpty();
  for (const { m, arr } of r.pts) {
    if (!m.visible) continue;
    const e = m.matrixWorld.elements;
    for (let i = 0; i < arr.length; i += 3) {
      const x = arr[i], y = arr[i + 1], z = arr[i + 2];
      _sp.set(e[0] * x + e[4] * y + e[8] * z + e[12], e[1] * x + e[5] * y + e[9] * z + e[13], e[2] * x + e[6] * y + e[10] * z + e[14]);
      out.expandByPoint(_sp);
    }
  }
  return out;
}
function sweepOf(r) {
  // everything the body covers in any of its clips, relative to its spot (rig.object at the origin); the phone and
  // the coin are placed outside these so nobody walks or falls through them
  // kept per sampled frame (not one union box): a fall that drifts back-left leaves the front-left free
  r.rig.object.position.set(0, 0, 0);
  const sw = new THREE.Box3(), b = new THREE.Box3(), rects = [];
  const add = () => { r.rig.object.updateMatrixWorld(true); curBox(r, b); sw.union(b); rects.push({ x0: b.min.x, x1: b.max.x, z0: b.min.z, z1: b.max.z }); };
  for (const a of Object.values(r.rig.anims)) {
    const n = a.frames || (a.joints ? Object.values(a.joints)[0].length : (a.base?.length || 1)), fps = a.fps || 30;
    const step = Math.max(1, Math.round(n / 60));   // ≤ ~4 mm of travel between samples at these speeds; rects get a margin
    for (let i = 0; i < n; i += step) { r.rig.applyFrame(a, i / fps); add(); }
    r.rig.applyFrame(a, (n - 1) / fps); add();
  }
  r.rig.setBase(null); r.rig.setPose(r.man.pose_rest || {}); add();
  if (r.man.faces?.neutral) r.rig.setFace('neutral');
  r.sweepLocal = sw; r.sweepRects = rects;
}
function restBox(r) {
  r.rig.setBase(null); r.rig.setPose(r.man.pose_rest || {});
  return meshBox(r);
}
function layout() {
  compact = camera.aspect < 0.8;
  // measure at the origin; `sweep` = how far the footprint grows sideways while turning in place
  robots.forEach((r) => {
    r.rig.object.position.set(0, 0, 0); const b = restBox(r);
    r.size = b.getSize(new THREE.Vector3()); r.half = r.size.clone().multiplyScalar(0.5);
    r.cx = (b.min.x + b.max.x) / 2; r.cz = (b.min.z + b.max.z) / 2;
    r.sweep = r.rig.anims.turn ? Math.max(0, Math.hypot(r.size.x, r.size.z) / 2 - r.size.x / 2) : 0;
    const w = r.rig.anims.walk; r.walkZ = w?.base ? Math.max(0, ...w.base.map((f) => -f[1] / 1000)) : 0;   // GLB -Y = world +z
  });
  const gapAfter = (i, list) => Math.max(0.03, list[i].sweep + (list[i + 1]?.sweep || 0) + 0.012);
  const place = (r, x, z) => { r.x = x - r.cx; r.rig.object.position.set(r.x, 0, z - r.cz); };
  if (!compact) {
    const total = robots.reduce((a, r, i) => a + r.size.x + (i < robots.length - 1 ? gapAfter(i, robots) : 0), 0);
    let x = -total / 2;
    robots.forEach((r, i) => { place(r, x + r.size.x / 2, 0); x += r.size.x + (i < robots.length - 1 ? gapAfter(i, robots) : 0); });
  } else {
    // portrait phone: 2 x 2, the two tallest at the back; the back row sits half a slot to the side so each back robot
    // stands in a gap of the front row instead of behind a front robot, and the camera looks down more steeply
    const tall = new Set([...robots].sort((a, b) => b.size.y - a.size.y).slice(0, 2));
    const back = robots.filter((r) => tall.has(r)), front = robots.filter((r) => !tall.has(r));
    const fx = [0], bx = [0];
    for (let i = 1; i < front.length; i++) fx.push(fx[i - 1] + front[i - 1].half.x + front[i].half.x + Math.max(0.045, gapAfter(i - 1, front)));
    const slot = front.length > 1 ? fx[1] - fx[0] : 0.15;
    for (let i = 1; i < back.length; i++) bx.push(bx[i - 1] + Math.max(slot, back[i - 1].half.x + back[i].half.x + gapAfter(i - 1, back)));
    const shift = slot * KS.shift;
    const all = [...front.map((r, i) => [r, fx[i]]), ...back.map((r, i) => [r, bx[i] + shift])];
    const lo = Math.min(...all.map(([r, x]) => x - r.half.x)), hi = Math.max(...all.map(([r, x]) => x + r.half.x));
    const mid = (lo + hi) / 2;
    const depthF = Math.max(...front.map((r) => r.size.z)), depthB = Math.max(...back.map((r) => r.size.z));
    const zF = (depthF + depthB) / 4 + KS.gap, zB = -zF;
    front.forEach((r, i) => place(r, fx[i] - mid, zF));
    back.forEach((r, i) => place(r, bx[i] + shift - mid, zB));
  }
  for (const r of robots) {
    r.box = restBox(r);
    // body centre in the root link's frame, so labels and the follow camera track the moving body without a per-frame box
    r.offLocal = r.rig.root.worldToLocal(r.box.getCenter(new THREE.Vector3()));
  }
  placeReferences();
}

// phone and coin: next to the robots for scale, but never inside the area any clip sweeps (walks, turns, falls), the phone
// never in front of a robot (it is 16 cm tall), and placed where the overview camera can stay closest
function placeReferences() {
  const U = new THREE.Box3(); robots.forEach((r) => U.union(r.box));
  const M = 0.02;   // clearance; the sampled frames and vertices can under-read a sweep by a few mm
  const rects = robots.flatMap((r) => { const o = r.rig.object.position; return r.sweepRects.map((q) => ({ x0: q.x0 + o.x - M, x1: q.x1 + o.x + M, z0: q.z0 + o.z - M, z1: q.z1 + o.z + M })); });
  const hits = (x0, x1, z0, z1, list) => { for (const q of list) if (x0 < q.x1 && x1 > q.x0 && z0 < q.z1 && z1 > q.z0) return true; return false; };
  const PH = { x: 0.04, z0: -0.032, z1: 0.008, h: 0.162 }, CR = 0.0135;   // phone footprint (leaning back on its stand), coin radius
  const dir = overviewDir(), cost = (B) => fitDist(corners(B), B.getCenter(new THREE.Vector3()), dir, 1);
  const tmp = new THREE.Box3(), lo = new THREE.Vector3(), hi = new THREE.Vector3();
  let best = null;
  for (let x = U.min.x - 0.35; x <= U.max.x + 0.35; x += 0.005) for (let z = U.min.z - 0.3; z <= U.max.z + 0.1; z += 0.005) {
    const x0 = x - PH.x, x1 = x + PH.x, z0 = z + PH.z0, z1 = z + PH.z1;
    // in front of a robot it would hide it: only allowed beside or behind the robots
    if (x1 > U.min.x && x0 < U.max.x && z1 > U.min.z + 0.02) continue;
    if (hits(x0, x1, z0, z1, rects)) continue;
    tmp.copy(U).union(new THREE.Box3(lo.set(x0, 0, z0), hi.set(x1, PH.h, z1)));
    const sc = cost(tmp) + (x > (U.min.x + U.max.x) / 2 ? 0.003 : 0);   // tie-break: the left side, as before
    if (!best || sc < best.sc) best = { sc, x, z };
  }
  if (best) phone.position.set(best.x, 0, best.z);
  const P = { x0: phone.position.x - PH.x - 0.006, x1: phone.position.x + PH.x + 0.006, z0: phone.position.z + PH.z0 - 0.006, z1: phone.position.z + PH.z1 + 0.006 };
  const U2 = U.clone().union(new THREE.Box3(lo.set(P.x0, 0, P.z0), hi.set(P.x1, PH.h, P.z1)));
  rects.push(P); best = null;
  for (let x = U2.min.x - 0.12; x <= U2.max.x + 0.12; x += 0.004) for (let z = U.min.z + 0.6 * (U.max.z - U.min.z); z <= U.max.z + 0.15; z += 0.004) {
    // the coin lies toward the front (not hidden behind a robot or under a label), off every path
    if (hits(x - CR, x + CR, z - CR, z + CR, rects)) continue;
    tmp.copy(U2).union(new THREE.Box3(lo.set(x - CR, 0, z - CR), hi.set(x + CR, 0.002, z + CR)));
    const near = Math.min(...robots.map((r) => Math.hypot(Math.max(0, r.box.min.x - x, x - r.box.max.x), Math.max(0, r.box.min.z - z, z - r.box.max.z))));
    const sc = cost(tmp) + 0.15 * near;   // stay beside a robot so the size comparison reads
    if (!best || sc < best.sc) best = { sc, x, z };
  }
  if (best) coin.position.set(best.x, 0.00095, best.z);
  ruler.position.set(0, 0.00075, U.max.z + 0.03);
}
function robotCenter(r, out = new THREE.Vector3()) { return r.rig.root.localToWorld(out.copy(r.offLocal)); }

// ---------- UI ----------
function el(tag, attrs = {}, html = '') { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (html) e.innerHTML = html; return e; }
const short = (t, n) => { t = String(t ?? ''); if (t.length <= n) return t; const cut = t.slice(0, n); const i = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('; ')); return (i > 40 ? cut.slice(0, i + 1) : cut.replace(/\s+\S*$/, '') + '…'); };
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ICON_PAUSE = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><rect x="3" y="2" width="3.6" height="12" rx="1" fill="currentColor"/><rect x="9.4" y="2" width="3.6" height="12" rx="1" fill="currentColor"/></svg>';
const ICON_PLAY = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4 2.2v11.6c0 .6.6.9 1.1.6l9-5.8c.5-.3.5-.9 0-1.2l-9-5.8C4.6 1.3 4 1.6 4 2.2z" fill="currentColor"/></svg>';
function setPlaying(p) { playing = p; const b = $('#playBtn'); b.innerHTML = p ? ICON_PAUSE : ICON_PLAY; b.setAttribute('aria-label', p ? 'Duraklat' : 'Oynat'); }
const announce = (msg) => { $('#sr').textContent = msg; };
let noteTimer = 0;
function note(msg, ms = 5000) { const n = $('#note'); n.textContent = msg; n.hidden = !msg; clearTimeout(noteTimer); if (msg) noteTimer = setTimeout(() => { n.hidden = true; }, ms); }

let voiceOn = store.get('kipir.voice') !== '0';
function buildUI() {
  const chips = $('#robotChips');
  const all = el('button', { class: 'chip', 'aria-pressed': 'true', id: 'chip-all' }, 'Hepsi');
  all.onclick = () => select(null); chips.append(all);
  for (const r of robots) {
    const b = el('button', { class: 'chip', 'aria-pressed': 'false', id: 'chip-' + r.key }, `<span class="dot" style="background:${esc(r.man.accent || '#888')}"></span>${esc(r.man.name)}`);
    b.onclick = () => select(r.key); chips.append(b);
    const s = r.man.specs?.dims_mm;
    const lab = el('div', { class: 'label' }, `<span class="nm"><span class="dot" style="background:${esc(r.man.accent || '#888')}"></span>${esc(r.man.name)}</span><br><span class="dm num">${s ? dimsTxt(s, '×') + ' mm' : ''}</span>`);
    lab.onclick = () => select(r.key); $('#labels').append(lab); r.label = lab;
  }
  const ar = $('#animRow');
  for (const [k, t] of ANIMS) {
    const b = el('button', { class: 'btn', 'data-anim': k, id: 'anim-' + k }, t);
    b.onclick = () => playAnim(k); ar.append(b);
  }
  const vb = el('button', { class: 'btn', id: 'voice', 'aria-pressed': String(voiceOn), title: 'Konuş hareketinde robot Türkçe konuşsun mu?' }, 'Sesli');
  vb.onclick = () => { voiceOn = !voiceOn; vb.setAttribute('aria-pressed', voiceOn); store.set('kipir.voice', voiceOn ? '1' : '0'); if (!voiceOn) stopSpeech(); };
  ar.append(vb);
  const vr = $('#viewRow');
  const views = [['3/4', 'v34'], ['Ön', 'vfront'], ['Yan', 'vside'], ['Üst', 'vtop'], ['Yüz yakın', 'vface'], ['Baskı yüzeyi', 'vmacro']];
  for (const [t, id] of views) { const b = el('button', { class: 'btn', id }, t); b.onclick = () => viewPreset(id); vr.append(b); }
  const xb = el('button', { class: 'btn', id: 'xray', 'aria-pressed': 'false' }, 'Röntgen'); xb.onclick = () => { xray = !xray; xb.setAttribute('aria-pressed', xray); robots.forEach((r) => r.rig.setXray(xray)); }; vr.append(xb);
  const gb = el('button', { class: 'btn', id: 'gridbtn', 'aria-pressed': 'true' }, '1 cm ızgara'); gb.onclick = () => { grid.visible = !grid.visible; gb.setAttribute('aria-pressed', grid.visible); }; vr.append(gb);
  $('#playBtn').onclick = () => setPlaying(!playing);
  $('#speed').onchange = (e) => { speed = parseFloat(e.target.value); };
  $('#scrub').oninput = (e) => {
    // every robot scrubs through its own clip length
    for (const r of activeRobots()) { const a = r.rig.anims[r.anim.name]; if (!a) continue; r.anim.t = (e.target.value / 1000) * clipDur(a); r.anim.hold = null; }
    setPlaying(false);
  };
  controls.addEventListener('start', () => { followCam = false; wideWalk = false; userMoved = true; fly = null; });
  renderPanel();
  updateAnimButtons();
}

let toastT = 0;
function toast(msg) {
  let t = document.getElementById('toast');
  if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); document.getElementById('stage').append(t); }
  t.style.top = $('#top').offsetHeight + 8 + 'px';   // under the top bar, never over the chips it points to
  t.textContent = msg; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { t.hidden = true; }, 3200);
  announce(msg);
}
function activeRobots() { return selected ? robots.filter((r) => r.key === selected) : robots; }
function toIdle(r) { r.rig.setBase(null); r.rig.setPose(r.man.pose_rest || {}); r.anim = { name: 'idle', t: 0, playing: true }; }
function updateVisibility() {
  // while the selected robot walks, turns or falls, its neighbours step out of the way (falls drift into them), and in every
  // preset but 3/4: the side camera sits behind the robots on the right, and on a portrait phone the front row hides the back row
  const s = selected && robots.find((x) => x.key === selected);
  const solo = s && (MOVES.has(s.anim.name) || lastView !== 'v34');
  robots.forEach((o) => { o.rig.object.visible = !solo || o === s; });
  phone.visible = coin.visible = !selected;   // scale references belong to the side-by-side view
}

function select(k) {
  stopSpeech(); followCam = false; wideWalk = false;
  for (const r of robots) if (MOVES.has(r.anim.name)) toIdle(r);
  selected = k;
  document.querySelectorAll('#robotChips .chip').forEach((c) => c.setAttribute('aria-pressed', 'false'));
  $(k ? '#chip-' + k : '#chip-all').setAttribute('aria-pressed', 'true');
  if (!k) { tab = 'genel'; frameAll(); } else { tab = 'ozellik'; viewPreset('v34'); }
  renderPanel(); updateAnimButtons(); updateVisibility();
  const r = k && robots.find((x) => x.key === k);
  announce(r ? `${r.man.name} seçildi` : 'Dört robot birlikte gösteriliyor');
}

function soloOnly(k) { return !selected && (SOLO.has(k) || (k === 'walk' && compact)); }
function updateAnimButtons() {
  const rs = activeRobots();
  for (const [k] of ANIMS) {
    const b = $('#anim-' + k); if (!b) continue;
    const has = rs.some((r) => r.rig.anims[k]);
    b.hidden = EXTRA.has(k) && (!has || !selected);
    const solo = soloOnly(k);
    b.disabled = !has; b.classList.toggle('soft', solo); b.setAttribute('aria-disabled', String(solo));
    b.title = solo ? 'Bu hareket için önce bir robot seç (robotlar yana kayar)' : '';
    b.setAttribute('aria-pressed', String(rs.length > 0 && rs.every((r) => r.anim.name === k)));
  }
}

// ---------- talk (optional Turkish TTS) ----------
let speaking = null, trVoice = null;
function initVoices() {
  if (!('speechSynthesis' in window)) return;
  const pick = () => { try { trVoice = speechSynthesis.getVoices().find((v) => v.lang && v.lang.toLowerCase().replace('_', '-').startsWith('tr')) || null; } catch (e) { trVoice = null; } };
  pick(); speechSynthesis.addEventListener?.('voiceschanged', pick);
}
function stopSpeech() { if (speaking) { try { speechSynthesis.cancel(); } catch (e) { /* ignore */ } speaking = null; } }
function speak(r) {
  if (!voiceOn) return;
  try {
    if (!('speechSynthesis' in window) || !trVoice) { note('Bu tarayıcıda Türkçe ses yok; robot sessiz konuşuyor.'); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(`Merhaba! Ben ${r.man.name}. ${r.man.subtitle_tr || ''}. ${r.man.say_tr || 'Masanda seninle yaşamaya hazırım.'}`);
    u.lang = 'tr-TR'; u.voice = trVoice; u.rate = 1.05; u.pitch = 1.5;
    u.onend = () => { if (speaking === r) { speaking = null; if (r.anim.name === 'talk') playAnim('idle', [r]); } };
    speaking = r; speechSynthesis.speak(u);
  } catch (e) { /* speech is optional */ }
}

function playAnim(k, which) {
  if (!which && soloOnly(k)) { toast('Bu hareket için önce bir robot seç: robotlar yana kayar, birbirine girer.'); return; }
  if (k !== 'talk') stopSpeech();
  const rs = which || activeRobots();
  const sel = !which && selected ? robots.find((x) => x.key === selected) : null;
  const before = sel ? robotCenter(sel, new THREE.Vector3()) : null;
  for (const r of rs) {
    if (!r.rig.anims[k]) continue;
    r.rig.setBase(null); r.rig.setPose(r.man.pose_rest || {});
    r.anim = { name: k, t: 0, playing: true, hold: null };
  }
  if (k === 'talk' && rs.length === 1) speak(rs[0]);
  setPlaying(true);
  updateAnimButtons(); updateVisibility();
  if (which) return;
  // the robot snapped back to its rest spot: re-frame the current view there instead of leaving the camera behind
  if (sel) sel.rig.object.updateMatrixWorld(true);
  if (sel && before && robotCenter(sel, new THREE.Vector3()).distanceTo(before) > 0.005) viewPreset(lastView);
  else if (sel && MOVES.has(k)) startFollow(sel); else followCam = false;
  // all four walking: the camera follows the group's centroid and fits its current spread (see groupFrame)
  if (!selected && k === 'walk') { wideWalk = true; userMoved = false; }   // let a pending overview fly finish: groupFrame keeps the camera's direction
  else if (!selected && wideWalk) { wideWalk = false; frameAll(); }
  announce(`${animName(k)} oynatılıyor`);
}

// ---------- camera ----------
let freeV = 1, fly = null, followCam = false, wideWalk = false, userMoved = false, lastView = 'v34';
const UP = new THREE.Vector3(0, 1, 0);
function flyTo(pos, tgt, dur = 0.8, instant = false) {
  if (reduceMotion || instant) { fly = null; camera.position.copy(pos); controls.target.copy(tgt); return; }
  fly = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: tgt, start: performance.now(), dur };
}
const fovs = () => { const v = (camera.fov * Math.PI) / 180; return { v, h: 2 * Math.atan(Math.tan(v / 2) * camera.aspect) }; };
// overview direction (target → camera); portrait phones look down more steeply so the back row shows over the front one
const KS = { shift: 0.25, gap: 0.075, dir: [0.06, 0.79, 1.0] };   // portrait 2 x 2: back-row side shift (x slot), extra row gap (m), camera direction (~38°)
const overviewDir = () => (compact ? new THREE.Vector3(...KS.dir) : new THREE.Vector3(0.18, 0.42, 0.9)).normalize();
const _fr = new THREE.Vector3(), _fu = new THREE.Vector3(), _fp = new THREE.Vector3();
function fitDist(pts, c, dir, margin = 1.1) {
  // smallest distance along `dir` from target `c` at which every point is inside the free part of the view
  // (the view offset centres the image between the top bar and an overlaid dock; freeV is that part's height share)
  const f = fovs(), tH = Math.tan(f.h / 2) / margin, tV = (Math.tan(f.v / 2) * freeV) / margin;
  _fr.crossVectors(UP, dir).normalize(); _fu.crossVectors(dir, _fr);
  let d = 0.05;
  for (const p of pts) {
    _fp.subVectors(p, c); const x = _fp.dot(_fr), y = _fp.dot(_fu), z = _fp.dot(dir);
    d = Math.max(d, z + Math.abs(x) / tH, z + Math.abs(y) / tV);
  }
  return d;
}
function corners(b, out = []) { for (let i = 0; i < 8; i++) out.push(new THREE.Vector3(i & 1 ? b.max.x : b.min.x, i & 2 ? b.max.y : b.min.y, i & 4 ? b.max.z : b.min.z)); return out; }
function frameAll(instant) {
  followCam = false; userMoved = false;
  const b = new THREE.Box3(); robots.forEach((r) => b.union(r.box)); b.expandByObject(phone); b.expandByObject(coin);
  b.max.y += 0.03;   // room for the name labels above the tallest robot
  const c = b.getCenter(new THREE.Vector3()), dir = overviewDir();
  const d = fitDist(corners(b), c, dir, 1.06);
  flyTo(c.clone().addScaledVector(dir, d), c, 0.8, instant);
}
// all four walking: aim at the centroid of the robots and fit their current spread, smoothly. A robot that walks far ahead
// may leave the frame: the distance is capped at 1.3 x the fit without the robot farthest from the centroid
const _gc = new THREE.Vector3(), _gd = new THREE.Vector3();
function groupFrame(dt, boxes) {
  const vis = robots.filter((r) => r.rig.object.visible);
  if (!vis.length) return;
  const cs = vis.map((r) => boxes.get(r).getCenter(new THREE.Vector3()));
  _gc.set(0, 0, 0); cs.forEach((c) => _gc.add(c)); _gc.multiplyScalar(1 / cs.length);
  const dir = _gd.subVectors(camera.position, controls.target).normalize();
  const all = []; vis.forEach((r) => corners(boxes.get(r), all));
  let d = fitDist(all, _gc, dir, 1.08);
  if (vis.length > 2) {
    let far = 0; cs.forEach((c, i) => { if (c.distanceTo(_gc) > cs[far].distanceTo(_gc)) far = i; });
    const core = []; vis.forEach((r, i) => { if (i !== far) corners(boxes.get(r), core); });
    d = Math.min(d, fitDist(core, _gc, dir, 1.08) * 1.3);
  }
  const k = reduceMotion ? 1 : 1 - Math.exp(-2.5 * dt);
  const cur = camera.position.distanceTo(controls.target);
  controls.target.lerp(_gc, k);
  camera.position.copy(controls.target).addScaledVector(dir, cur + (d - cur) * k);
}
// rigid follow: every frame the robot's displacement is added to both the camera and the target, so whatever framing is
// on screen (a preset picked mid-walk, or the user's own zoom) stays locked to the moving robot
let followR = null; const followPrev = new THREE.Vector3();
function startFollow(r) {
  if (!r) { followCam = false; return; }
  r.rig.object.updateMatrixWorld(true); followR = r; robotCenter(r, followPrev); followCam = true;
}
function facing(r) {
  // robots face GLB -Y; returns world forward/right of the body link (follows turns)
  r.rig.object.updateMatrixWorld(true);
  const fwd = new THREE.Vector3(0, -1, 0).transformDirection(r.rig.root.matrixWorld); fwd.y = 0;
  if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, 1); fwd.normalize();
  return { fwd, right: UP.clone().cross(fwd).normalize() };
}
const SKIN = new Set(['print', 'tpu', 'petg', 'plastic']);
function viewPreset(id, instant = false) {
  followCam = false; userMoved = false; lastView = id; updateVisibility();
  const r = selected ? robots.find((x) => x.key === selected) : null;
  if (!r) { frameAll(instant); return; }
  presetFor(r, id, instant);
  // mid-walk/turn/fall: the preset was framed on the current pose; keep it locked to the robot until the clip ends,
  // then the tick re-frames the same preset at the rest spot
  if (MOVES.has(r.anim.name)) startFollow(r);
}
function presetFor(r, id, instant) {
  const b = meshBox(r); const c = b.getCenter(new THREE.Vector3()); const s = b.getSize(new THREE.Vector3());
  const f = fovs();
  const rad = s.length() / 2; const d = rad / Math.sin(Math.min(f.v, f.h) / 2) * 1.05;
  const dirs = { v34: [0.55, 0.35, 0.76], vfront: [0, 0.12, 1], vside: [1, 0.12, 0], vtop: [0.001, 1, 0.12] };
  if (dirs[id]) { const v = new THREE.Vector3(...dirs[id]).normalize(); flyTo(c.clone().addScaledVector(v, d), c, 0.8, instant); return; }
  const { fwd, right } = facing(r);
  if (id === 'vface') {
    // frame the eye screens (and visor); come in a little from above-right so the visor reflection misses the lens
    const fb = new THREE.Box3();
    r.rig.meshes.forEach((m) => { const t = m.material.userData.def?.type; if (m.visible && (t === 'screen' || t === 'acrylic')) fb.expandByObject(m, true); });
    const tgt = fb.isEmpty() ? new THREE.Vector3(c.x, b.min.y + s.y * 0.66, b.max.z - s.z * 0.18) : fb.getCenter(new THREE.Vector3());
    const fs = fb.isEmpty() ? s.clone().multiplyScalar(0.5) : fb.getSize(new THREE.Vector3());
    const fw = Math.abs(fs.x * fwd.z) + Math.abs(fs.z * fwd.x);   // face width across the view
    const dd = Math.max((fw / 0.55 / 2) / Math.tan(f.h / 2), (fs.y / 0.4 / 2) / Math.tan(f.v / 2), 0.09);
    const dir = fwd.clone().addScaledVector(UP, 0.35).addScaledVector(right, 0.25).normalize();
    flyTo(tgt.clone().addScaledVector(dir, dd), tgt, 0.8, instant); return;
  }
  if (id === 'vmacro') {
    // close-up of a printed body wall: cast rays at the upper flank of the body shell (not a leg) and look at the hit from
    // ~45 mm, grazing from above-outside (layer lines read best at a low angle and the shell's curve and silhouette stay in
    // frame); skip spots where a limb would sit between the camera and the wall
    const jointNodes = new Set(Object.values(r.rig.joints).map((j) => j.node));
    const onBody = (m) => { for (let o = m; o && o !== r.rig.root; o = o.parent) if (jointNodes.has(o)) return false; return true; };
    const skin = r.rig.meshes.filter((m) => m.visible && SKIN.has(m.material.userData.def?.type));
    const body = skin.filter(onBody);
    const aim = c.clone().setY(b.min.y + s.y * 0.72);
    const cands = [[-0.85, 0.45], [0.85, 0.45], [-1, 0], [1, 0], [0.7, -0.7], [-0.7, -0.7], [0.3, 1], [-0.3, 1]];
    const all = r.rig.meshes.filter((m) => m.visible);
    const lum = (m) => { const c = m.material.color; return c ? 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b : 0; };
    // what the close-up would show: a 7 x 5 grid of rays over the view. A good wall view is mostly the printed shell the
    // centre ray hits, with at most a strip of a dark part (a seam with a chassis band is welcome, a black switch or
    // visor filling the frame is not) and little empty background
    const shows = (pos, tgt, main) => {
      const fw = tgt.clone().sub(pos).normalize(), rt = fw.clone().cross(UP).normalize(), up = rt.clone().cross(fw);
      const tv = Math.tan(f.v / 2) * freeV * 0.85, th = Math.tan(f.h / 2) * 0.85, rc = new THREE.Raycaster();
      let n = 0, same = 0, dark = 0, miss = 0;
      for (let i = 0; i < 7; i++) for (let j = 0; j < 5; j++) {
        const d = fw.clone().addScaledVector(rt, (i / 3 - 1) * th).addScaledVector(up, (j / 2 - 1) * tv).normalize();
        rc.set(pos, d); rc.far = 0.25; const h = rc.intersectObjects(all, false)[0]; n++;
        if (!h) { miss++; continue; }
        const t = h.object.material.userData.def?.type;
        if (h.object.material === main) same++;
        else if (!SKIN.has(t) || lum(h.object) < 0.1) dark++;
      }
      return { same: same / n, dark: dark / n, miss: miss / n };
    };
    // a low, wide shell (Tosbi's two domes on a dark chassis band): the up-sloping candidates below end on the dome's top;
    // look instead at a dome's side wall just above the dome/chassis seam, down along the wall at a grazing angle
    if (s.y < 0.6 * Math.max(s.x, s.z)) {
      const vol = (m) => { const q = new THREE.Box3().setFromObject(m).getSize(new THREE.Vector3()); return q.x * q.y * q.z; };
      const main = body.reduce((a, m) => (vol(m) > vol(a) ? m : a), body[0]);
      const mb = new THREE.Box3().setFromObject(main, true), mc = mb.getCenter(new THREE.Vector3());
      const rc = new THREE.Raycaster();
      for (const side of [right.clone(), right.clone().negate(), fwd.clone().negate()]) {
        const cast = (y) => { rc.set(mc.clone().setY(y).addScaledVector(side, 0.5), side.clone().negate()); rc.far = 1; return rc.intersectObjects(all, false)[0]; };
        let seenMain = false, seamY = null;
        for (let y = mb.max.y - 0.002; y > mb.min.y; y -= 0.001) {
          const h = cast(y); const isMain = h && h.object === main;
          if (isMain) seenMain = true; else if (seenMain && h) { seamY = y; break; }
        }
        if (seamY == null) continue;
        const hit = cast(seamY + 0.006);   // 6 mm above the seam
        if (!hit || hit.object !== main) continue;
        const K = [0.02, 0.028, 0.02];   // camera: out from the wall, up, along it (an oblique look makes the lines converge)
        const along = UP.clone().cross(side).normalize();
        const pos = hit.point.clone().addScaledVector(side, K[0]).addScaledVector(UP, K[1]).addScaledVector(along, K[2]);
        const to = hit.point.clone().sub(pos), dist = to.length();
        if (new THREE.Raycaster(pos, to.normalize(), 0, dist - 0.002).intersectObjects(all, false)[0]) continue;
        const q = shows(pos, hit.point, main.material);
        if (q.same < 0.4 || q.dark > 0.25) continue;
        flyTo(pos, hit.point.clone(), 0.8, instant); return;
      }
    }
    for (const [kr, kf] of cands) {
      const dir = right.clone().multiplyScalar(kr).addScaledVector(fwd, kf).addScaledVector(UP, 0.15).normalize();
      const hit = new THREE.Raycaster(aim.clone().addScaledVector(dir, 1), dir.clone().negate(), 0, 2).intersectObjects(body.length ? body : skin, false)[0];
      if (!hit) continue;
      const n = hit.face.normal.clone().transformDirection(hit.object.matrixWorld); if (n.dot(dir) < 0) n.negate();
      const tg = UP.clone().addScaledVector(n, -n.dot(UP)); if (tg.lengthSq() < 1e-4) tg.copy(fwd); tg.normalize();
      const pos = hit.point.clone().addScaledVector(n, 0.03).addScaledVector(tg, 0.032).addScaledVector(fwd, 0.008);
      const to = hit.point.clone().sub(pos), dist = to.length();
      const block = new THREE.Raycaster(pos, to.normalize(), 0, dist - 0.002).intersectObjects(skin, false)[0];
      if (block) continue;
      const q = shows(pos, hit.point, hit.object.material);
      if (q.same < 0.5 || q.dark > 0.25 || q.miss > 0.3) continue;
      flyTo(pos, hit.point.clone(), 0.8, instant); return;
    }
    const tgt = new THREE.Vector3(b.max.x - s.x * 0.2, b.min.y + s.y * 0.55, c.z);
    const dd = Math.max(s.x, s.y) * 0.32;
    flyTo(tgt.clone().add(new THREE.Vector3(dd * 0.9, dd * 0.25, dd * 0.55)), tgt, 0.8, instant);
  }
}

// canvas size + keeping the subject clear of the overlaid top bar and dock (view offset shifts the image, not the camera)
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return false;
  renderer.setSize(w, h, false); camera.aspect = w / h;
  const dock = $('#dock'), top = $('#top');
  const over = getComputedStyle(dock).position === 'absolute' ? dock.offsetHeight + 14 : 0;
  const shift = Math.round((over - top.offsetHeight) / 2);
  freeV = Math.max(0.4, (h - over - top.offsetHeight) / h);
  if (shift) camera.setViewOffset(w, h, 0, shift, w, h); else camera.clearViewOffset();
  camera.updateProjectionMatrix();
  return true;
}
function onResize() {
  const was = compact;
  if (!resize() || !robots.length) return;
  if ((camera.aspect < 0.8) !== was) { layout(); updateAnimButtons(); }
  if (!userMoved && !fly && !followCam && !wideWalk) { if (selected) viewPreset(lastView, true); else frameAll(true); }
}

// ---------- panel ----------
const TABS_SEL = [['ozellik', 'Özellikler'], ['maliyet', 'Maliyet'], ['gercek', 'Gerçekte nasıl?'], ['juri', 'Jüri']];
const TABS_ALL = [['genel', 'Karşılaştır'], ['juri', 'Jüri'], ['nasil', 'Nasıl yapıldı?']];
let tabsFor;
function renderPanel() {
  const r = selected ? robots.find((x) => x.key === selected) : null;
  const list = r ? TABS_SEL : TABS_ALL;
  if (!list.some(([k]) => k === tab)) tab = list[0][0];
  $('#ptitle').textContent = r ? r.man.name : 'Dört konsept yan yana';
  $('#psub').textContent = r ? (r.man.subtitle_tr || '') + (r.man.tagline_tr ? ' · ' + r.man.tagline_tr : '') : 'Gerçek boyutlarıyla, telefon ve 1 TL ile karşılaştır. Bir robota tıklayınca ayrıntıları açılır.';
  const tabs = $('#tabs');
  // rebuild the tab buttons only when the robot changes, so keyboard focus stays on the tab
  if (tabsFor !== (r ? r.key : '*')) {
    tabsFor = r ? r.key : '*'; tabs.innerHTML = '';
    list.forEach(([k, t], i) => {
      const b = el('button', { class: 'tab', role: 'tab', id: 'tab-' + k, 'aria-controls': 'pbody' }, t);
      b.onclick = () => { tab = k; renderPanel(); };
      b.onkeydown = (e) => {
        const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : e.key === 'Home' ? -i : e.key === 'End' ? list.length - 1 - i : 0;
        if (!d) return; e.preventDefault(); tab = list[(i + d + list.length) % list.length][0]; renderPanel(); $('#tab-' + tab).focus();
      };
      tabs.append(b);
    });
  }
  tabs.querySelectorAll('.tab').forEach((b) => { const on = b.id === 'tab-' + tab; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; });
  const body = $('#pbody'); body.setAttribute('aria-labelledby', 'tab-' + tab);
  body.innerHTML = r ? robotTab(r) : overviewTab(); body.scrollTop = 0;
  body.querySelectorAll('.card[data-key]').forEach((c) => {
    c.onclick = () => focusCard(c.dataset.key);
    c.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); focusCard(c.dataset.key); } };
  });
}

// tools_tl_if_needed starts at 0 for a family that already owns them; when buying, the floor is an iron + multimeter
// (cheapest verified pair: Motorobit 60 W iron 242.40 + Direnc DT830D 191.79 TL)
const MIN_TOOL_KIT_TL = 434;
function toolsRange(b) {
  const t = b?.tools_tl_if_needed; if (!Array.isArray(t)) return null;
  return [t[0] > 0 ? t[0] : (b.tools_min_kit_tl ?? MIN_TOOL_KIT_TL), t[1]];
}
// phones: the 3D view is above the panel, so bring it back into view after picking a card
function focusCard(key) {
  select(key);
  if (matchMedia('(max-width: 900px)').matches) stage.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
}
function costOf(r) { const t = r.bom?.total_tl || r.man.specs?.total_tl; return Array.isArray(t) ? t : null; }
function juryFor(k) { return catalog.jury?.ranking?.find((x) => x.key === k); }
// Jury's estimate adds the risk of current discounts ending on top of the parts-list total.
function realCost(r) { const t = juryFor(r.key)?.real_cost_tl; return Array.isArray(t) ? t : costOf(r); }
const TR = (r) => catalog.tr?.[r.key] || {};
const speedOf = (r) => r.man.sim_summary?.walk_speed_cm_s ?? r.man.specs?.walk_speed_cm_s;
const wheeled = (r) => (r.man.specs?.motors || 0) > 0;

function overviewTab() {
  if (tab === 'juri') return juryAll();
  if (tab === 'nasil') return howMade();
  let h = '';
  if (catalog.jury?.recommendation_tr) h += `<div class="total" style="display:block"><span class="muted">Jürinin önerisi</span><p style="margin:6px 0 0">${esc(catalog.jury.recommendation_tr)}</p></div>`;
  for (const r of robots) {
    const s = r.man.specs || {}, sim = r.man.sim_summary || {}, c = realCost(r), j = juryFor(r.key);
    const v = speedOf(r);
    h += `<div class="card" data-key="${esc(r.key)}" role="button" tabindex="0" aria-label="${esc(r.man.name)} robotuna odaklan"><div class="ch"><span class="dot" style="background:${esc(r.man.accent || '#888')}"></span><b>${esc(r.man.name)}</b><span class="muted">${esc(r.man.subtitle_tr || '')}</span>${j?.rank ? `<span class="pill good" style="margin-left:auto">${j.rank}. sıra · ${fmt(j.score_total)}/10</span>` : ''}</div>
    <dl class="kv sm"><dt>Boyut</dt><dd class="num">${dimsTxt(s.dims_mm)} mm · ${s.mass_g ?? '–'} g</dd>
    <dt>Hareket</dt><dd>${s.servos ?? '–'} servo${s.motors ? ' + ' + s.motors + ' motor' : ''}${v ? ` · <span class="num">${fmt(v)} cm/s</span>${wheeled(r) ? ' (tekerlekle)' : ''}` : ''}</dd>
    <dt>Düşerse</dt><dd>${esc(TR(r).recovery_tr || short(trn(noPaths(sim.recovery_short || s.self_righting_short || s.self_righting || '–')), 110))}</dd>
    <dt>Gerçek maliyet</dt><dd><b class="num">${c ? fmtTL(c[0]) + ' – ' + fmtTL(c[1]) : '–'}</b></dd></dl></div>`;
  }
  const tools = robots.map((r) => toolsRange(r.bom)).filter(Boolean);
  const tl = tools.length ? `Havya ve multimetre yoksa robota göre ${fmtTL(Math.min(...tools.map((t) => t[0])))}–${fmtTL(Math.max(...tools.map((t) => t[1])))} ekle. ` : '';
  h += `<p class="muted">Maliyetler: Türkiye'de stokta parçalar, KDV dahil, ${esc(catalog.prices_checked || 'Ekim 2026')} fiyatları; 3D baskı ve kargo dahil. ${tl}Bir karta tıkla: o robota odaklanır.</p>`;
  return h;
}

function robotTab(r) {
  const s = r.man.specs || {}, sim = r.man.sim_summary || {}, T = TR(r);
  if (tab === 'ozellik') {
    let h = '<dl class="kv">';
    const v = speedOf(r);
    const kv = [['Boyut', dimsTxt(s.dims_mm) + ' mm'], ['Ağırlık', s.mass_g ? s.mass_g + ' g' : null], ['Servo / motor', `${s.servos ?? '–'} servo${s.motors ? ' + ' + s.motors + ' motor' : ''}`],
      ['Beyin', trn(s.brain)], ['Pil', trn(s.battery)], ['Çalışma süresi', s.runtime_walk_min ? `yürürken ~${s.runtime_walk_min} dk · beklerken ~${fmtN(s.runtime_idle_h)} sa` : null],
      [wheeled(r) ? 'Hız (simülasyon, tekerlekle)' : 'Yürüme hızı (simülasyon)', v ? fmt(v) + ' cm/s' : null],
      ['Hız notu', wheeled(r) && s.walk_speed_note ? trn(noPaths(s.walk_speed_note)) : null],
      ['Düşünce kendi kalkar mı?', TR(r).recovery_tr ? TR(r).recovery_tr + ' ' + trn(noPaths(s.self_righting || '')) : trn(noPaths(s.self_righting || ''))], ['Sensörler', trn((s.sensors || []).join(', '))], ['Ses', trn(s.voice)]];
    let more = false;
    for (const [k, val] of kv) if (val) { const t = String(val); if (t.length > 170) more = true; h += `<dt>${k}</dt><dd>${esc(short(t, 170))}</dd>`; }
    h += '</dl>';
    if (more) h += `<details><summary class="muted">Tüm teknik ayrıntılar</summary><dl class="kv sm">${kv.filter(([, val]) => val).map(([k, val]) => `<dt>${k}</dt><dd>${esc(val)}</dd>`).join('')}</dl></details>`;
    const rec = trn(noPaths(T.recovery_tr || sim.recovery || ''));
    const notes = (T.notes_tr || (Array.isArray(sim.notes) ? sim.notes : sim.notes ? [sim.notes] : [])).map((n) => trn(noPaths(n))).filter((n) => n && !/^(Kaynaklar|Sources)\b/i.test(n) && n.length > 12);
    if (rec || notes.length) h += `<h3>Fizik simülasyonu (MuJoCo)</h3><p>${esc(short(rec, 420))}</p>${rec.length > 420 || notes.length ? `<details><summary class="muted">Simülasyonun tüm ayrıntıları</summary>${rec.length > 420 ? `<p class="muted">${esc(rec)}</p>` : ''}${notes.length ? `<ul class="notes muted">${notes.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>` : ''}</details>` : ''}`;
    const c = realCost(r); if (c) h += `<div class="total"><span>Gerçek maliyet</span><b class="num">${fmtTL(c[0])} – ${fmtTL(c[1])}</b></div>`;
    return h;
  }
  if (tab === 'maliyet') {
    const b = r.bom; if (!b) return '<p>Parça listesi henüz yok.</p>';
    const shops = catalog.tr?.shops || {}, parts = T.items || {};
    const rc = juryFor(r.key)?.real_cost_tl;
    let h = rc ? `<div class="total"><span>Gerçek maliyet (indirimler biterse diye pay dahil)</span><b class="num">${fmtTL(rc[0])} – ${fmtTL(rc[1])}</b></div>` : '';
    h += `<div class="total"><span>Parça listesi toplamı (baskı + kargo dahil)</span><b class="num">${fmtTL(b.total_tl?.[0])} – ${fmtTL(b.total_tl?.[1])}</b></div>`;
    h += '<div class="tblwrap"><table><thead><tr><th>Parça</th><th class="r">Adet</th><th class="r">Tutar</th><th>Mağaza</th></tr></thead><tbody>';
    for (const it of b.items || []) {
      const shop = shops[it.shop] ?? it.shop;
      h += `<tr><td>${esc(it.part_tr ?? parts[it.part] ?? it.part)}${it.verified_on_page === false ? ' <span class="pill warn">doğrulanmadı</span>' : ''}${/stok yok|tükendi|out of stock|OOS/i.test(it.stock || '') ? ' <span class="pill bad">stok yok</span>' : ''}</td><td class="r num">${it.qty}</td><td class="r num">${fmtTL(it.line_tl ?? it.unit_tl * it.qty)}</td><td>${it.url ? `<a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(shop)}</a>` : esc(shop)}</td></tr>`;
    }
    h += '</tbody></table></div>';
    if (b.print) {
      const hrs = b.print.hours_range || b.print.hours;
      h += `<h3>3D baskı</h3><p class="num">${fmtRange(b.print.grams)} g · ~${fmtRange(hrs)} saat · ${fmtTL(b.print.tl_min)} – ${fmtTL(b.print.tl_max)}</p>`;
      if (T.print_tr) h += `<p class="muted">${esc(T.print_tr)}</p>`;   // the package's own materials/basis text is English
    }
    if (b.shipping_tl) h += `<p>Kargo: <span class="num">${fmtTL(b.shipping_tl[0])} – ${fmtTL(b.shipping_tl[1])}</span></p>`;
    if (b.lean_variant) h += `<h3>Sade sürüm</h3><p class="num">${fmtTL(b.lean_variant.total_tl?.[0])} – ${fmtTL(b.lean_variant.total_tl?.[1])}</p>${T.lean_tr || b.lean_variant.what_tr ? `<p>${esc(T.lean_tr || b.lean_variant.what_tr)}</p>` : ''}`;
    const tr = toolsRange(b); if (tr) h += `<p class="muted">Havya ve multimetre yoksa: ${fmtTL(tr[0])} – ${fmtTL(tr[1])}</p>`;
    return h;
  }
  if (tab === 'gercek') {
    let h = '<p>Bu sahnedeki malzemeler gerçek baskıya göre ayarlı: mat PLA, 0,12–0,16 mm katman çizgileri, parça birleşim yerleri ve ekranların gerçek çözünürlüğü. "Baskı yüzeyi" ve "Yüz yakın" görünümleriyle yakından bak.</p>';
    h += '<ul class="notes">' + (r.man.realism_notes_tr || []).map((n) => `<li>${esc(trn(noPaths(n)))}</li>`).join('') + '</ul>';
    const fil = new Map(); Object.values(r.man.materials || {}).forEach((m) => { if (m.filament && !fil.has(m.filament)) fil.set(m.filament, m.color); });
    if (fil.size) { h += '<h3>Filamentler</h3><ul class="notes">'; for (const [f, col] of fil) h += `<li><span class="dot" style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${esc(col)};margin-right:6px"></span>${esc(trn(f))}</li>`; h += '</ul>'; }
    const scr = Object.values(r.man.screens || {}); if (scr.length) h += `<h3>Ekranlar</h3><ul class="notes">${scr.map((x) => `<li>${esc(trn(x.panel || 'LCD'))} · ${x.res.join('×')} piksel${x.active_diam_mm ? ' · aktif alan Ø' + fmtN(x.active_diam_mm) + ' mm' : ''}</li>`).join('')}</ul>`;
    return h;
  }
  if (tab === 'juri') { const j = juryFor(r.key); return j ? juryCard(j) : '<p>Jüri değerlendirmesi hazırlanıyor.</p>'; }
  return '';
}

function juryCard(j) {
  let h = '';
  if (j.rank) h += `<p><span class="pill good">${j.rank}. sıra</span> <b class="num">${fmt(j.score_total ?? 0)}</b>/10</p>`;
  for (const [k, v] of Object.entries(j.scores || {})) h += `<div class="score"><span>${esc(k)}</span><span class="bar"><i style="width:${Math.max(0, Math.min(10, v)) * 10}%"></i></span><span class="num">${fmtN(v)}</span></div>`;
  if (j.verdict_tr) h += `<p>${esc(j.verdict_tr)}</p>`;
  if (j.pros?.length) h += `<h3>Güçlü yanları</h3><ul class="notes">${j.pros.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
  if (j.cons?.length) h += `<h3>Zayıf yanları</h3><ul class="notes">${j.cons.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
  if (j.real_cost_tl) {
    const r = robots.find((x) => x.key === j.key), c = r && costOf(r);
    h += `<div class="total" style="flex-wrap:wrap;gap:4px 12px"><span>Jüri tahmini (yedek payı dahil)</span><b class="num">${fmtTL(j.real_cost_tl[0])} – ${fmtTL(j.real_cost_tl[1])}</b>${c ? `<span class="muted" style="flex-basis:100%">Parça listesi: <span class="num">${fmtTL(c[0])} – ${fmtTL(c[1])}</span></span>` : ''}</div>`;
    if (j.real_cost_note_tr) h += `<p class="muted">${esc(j.real_cost_note_tr.replace(/\bbom\.json toplamı/g, 'Parça listesi toplamı'))}</p>`;
  }
  return h;
}
function juryAll() {
  const J = catalog.jury; if (!J) return '<p>Jüri değerlendirmesi hazırlanıyor.</p>';
  let h = J.summary_tr ? `<p>${esc(J.summary_tr)}</p>` : '';
  for (const j of [...(J.ranking || [])].sort((a, b) => (a.rank || 9) - (b.rank || 9))) {
    const r = robots.find((x) => x.key === j.key);
    h += `<h3>${j.rank ? j.rank + '. ' : ''}${esc(r?.man.name || j.key)}</h3>` + juryCard(j);
  }
  return h;
}
function howMade() {
  return `<ul class="notes">
  <li><b>Gövdeler</b> build123d ile gerçek CAD olarak çizildi: içindeki servolar, kart, pil ve ekranlar gerçek ölçüleriyle yerleştirildi (Röntgen ile görebilirsin).</li>
  <li><b>Hareketler</b> MuJoCo fizik motorundan kaydedildi. Servolar MG90S'in gerçek torkuyla (0,2 N·m) sınırlandı, masa sürtünmesi 0,6. Yürüme hızı ve düşüp kalkma sonuçları simülasyon ölçümleri.</li>
  <li><b>Görünüm</b> gerçek baskıya göre: mat PLA, katman çizgileri, parça birleşim yerleri, Türkiye'de satılan filament renkleri; gözler 240×240 piksel ekranlar, yakından pikseller görünür.</li>
  <li><b>Maliyetler</b> Türk mağazalarının ürün sayfalarından tek tek kontrol edildi (KDV dahil).</li>
  <li>Simülasyon gerçeğe yakındır ama birebir değildir: gerçek baskıda yürüyüş ayarı ve kalkma hareketleri ince ayar ister.</li></ul>`;
}

// ---------- loop ----------
// clip length as rig.applyFrame plays it: the last frame is reached at (n-1)/fps (loops wrap there)
function clipDur(a) { const n = a.frames || (a.joints ? Object.values(a.joints)[0].length : (a.base?.length || 1)); return Math.max(1, n - 1) / (a.fps || 30); }
const _v = new THREE.Vector3(), _c = new THREE.Vector3(), _d = new THREE.Vector3(), _k = new THREE.Vector3(0.5, 1.0, 0.7);
let tlText = '';
function tick() {
  const dt = Math.min(clock.getDelta(), 0.25);   // larger cap: slow devices still play in real time; guards tab-switch jumps
  if (canvas.width !== Math.floor(canvas.clientWidth * renderer.getPixelRatio()) || canvas.height !== Math.floor(canvas.clientHeight * renderer.getPixelRatio())) resize();
  const w = canvas.clientWidth, h = canvas.clientHeight;
  for (const r of robots) {
    const a = r.rig.anims[r.anim.name];
    if (!a) continue;
    if (playing && r.anim.playing) r.anim.t += dt * speed;
    const res = r.rig.applyFrame(a, r.anim.t);
    if (res.done) {
      r.anim.hold = (r.anim.hold ?? 0) + (playing ? dt : 0);   // a paused/scrubbed end frame stays put
      if (r.anim.hold > 1.6 && r.anim.name !== 'sleep') {
        const wasMove = MOVES.has(r.anim.name);
        toIdle(r); updateAnimButtons(); updateVisibility();
        // the body snaps back to its spot: bring the camera back too (unless the user took over)
        if (wasMove && followCam && selected === r.key) viewPreset(lastView);
        if (wideWalk && robots.every((o) => o.anim.name !== 'walk')) { wideWalk = false; frameAll(); }
      }
    }
    // procedural blink while idling, if the idle clip has no face track
    if (r.anim.name === 'idle' && !(a.face && a.face.length > 1) && r.man.faces?.blink) {
      r.blinkAt -= dt;
      if (r.blinkAt < 0) { r.rig.setFace('blink'); if (r.blinkAt < -0.12) { r.rig.setFace('neutral'); r.blinkAt = 2.5 + Math.random() * 3.5; } }
    }
  }
  // timeline
  const rs = activeRobots();
  if (rs.length) {
    const r = rs[0], a = r.rig.anims[r.anim.name];
    if (a) {
      const dur = clipDur(a); const tt = a.loop ? r.anim.t % dur : Math.min(r.anim.t, dur);
      if (document.activeElement !== $('#scrub')) $('#scrub').value = Math.round((tt / dur) * 1000);
      const src = a.source ? (/mujoco/i.test(a.source) ? ' · MuJoCo' : ' · kinematik') : '';
      const t = `${animName(r.anim.name)} · ${fmt(tt)} / ${fmt(dur)} sn${src}`;
      if (t !== tlText) { tlText = t; $('#tl-label').textContent = t; }
    }
  }
  // current boxes of every robot (sampled vertices): group framing and labels follow the moving bodies
  scene.updateMatrixWorld();
  const boxes = new Map(robots.map((r) => [r, curBox(r, r.cur || (r.cur = new THREE.Box3()))]));
  // camera: rigid follow of the selected robot (also shifts a fly in progress), group framing, fly
  if (followCam && selected && followR && followR.key === selected) {
    robotCenter(followR, _c); _d.subVectors(_c, followPrev); followPrev.copy(_c);
    camera.position.add(_d); controls.target.add(_d);
    if (fly) { fly.p0.add(_d); fly.t0.add(_d); fly.p1.add(_d); fly.t1.add(_d); }
  } else if (wideWalk && !selected && !fly) groupFrame(dt, boxes);
  if (fly) {
    fly.t = (performance.now() - fly.start) / 1000 / fly.dur; const e = fly.t >= 1 ? 1 : 1 - Math.pow(1 - fly.t, 3);
    camera.position.lerpVectors(fly.p0, fly.p1, e); controls.target.lerpVectors(fly.t0, fly.t1, e);
    if (fly.t >= 1) fly = null;
  }
  controls.update();
  // shadows follow the view target
  key.target.position.copy(controls.target); key.position.copy(controls.target).add(_k);
  renderer.render(scene, camera);
  // labels: above each body, nearest first; a label that would overlap a nearer one is hidden
  const topView = selected && (_v.subVectors(camera.position, controls.target).normalize().y > 0.93 || camera.position.distanceTo(controls.target) < 0.12);   // top view or a close-up: the name is redundant and would pin to an edge
  const tight = !selected && (camera.aspect < 0.8 || h < 420), topBar = $('#top').offsetHeight;
  const placed = [], items = [];
  for (const r of robots) {
    const bx = boxes.get(r); bx.getCenter(_c); const depth = _c.distanceTo(camera.position);
    _v.set(_c.x, bx.max.y + 0.01, _c.z).project(camera);   // above the CURRENT top of the body (falls, walks)
    const vis = _v.z < 1 && r.rig.object.visible && (!selected || selected === r.key) && !topView;
    if (!vis) { r.label.hidden = true; continue; }
    r.label.hidden = false; r.label.classList.toggle('nodm', tight);
    items.push({ r, x: ((_v.x + 1) / 2) * w, y: ((1 - _v.y) / 2) * h, depth });
  }
  items.sort((a, b) => a.depth - b.depth);
  for (const it of items) { it.lw = it.r.label.offsetWidth; it.lh = it.r.label.offsetHeight; }   // all reads before any write: one layout
  for (const it of items) {
    const lw = it.lw, lh = it.lh;
    const x = Math.min(Math.max(it.x, lw / 2 + 4), w - lw / 2 - 4), y = Math.min(Math.max(it.y, topBar + lh), h - 4);
    const rect = { l: x - lw / 2, r: x + lw / 2, t: y - lh, b: y };
    if (placed.some((p) => rect.l < p.r && rect.r > p.l && rect.t < p.b && rect.b > p.t)) { it.r.label.hidden = true; continue; }
    placed.push(rect);
    it.r.label.style.left = x + 'px'; it.r.label.style.top = y + 'px';
  }
}

addEventListener('keydown', (e) => { if (e.key === 'Escape') select(null); });
window.__kipir = { KS, relayout: () => { layout(); frameAll(true); }, THREE, phone, coin, ruler, robots, select, playAnim, viewPreset, scene, camera, renderer, controls, setXray: (on) => { xray = on; robots.forEach((r) => r.rig.setXray(on)); } };
boot().catch((e) => { $('#loading').textContent = 'Yüklenemedi: ' + e.message; console.error(e); });
