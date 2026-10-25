// rig.js: loads one robot package (manifest.json + model.glb + faces + animations) into Three.js,
// applies realistic materials (realism.js), and exposes joint/base/face control plus animation playback.
// The web viewer and the posecheck harness both use it, so a package that renders right in posecheck
// renders right in the viewer.
//
// Package conventions (see SPEC.md):
//  - model.glb: millimetres, Z up, robot faces -Y. The root node is the body ("base") link.
//  - Every movable link is a named node whose origin sits on its joint axis, with an identity rest rotation
//    relative to its parent wherever possible.
//  - Mesh nodes are named "<link>__<matKey>", e.g. "thigh_fl__shell", "head__visor", "eyeL__screen_eyeL".
//    The <matKey> after "__" selects manifest.materials[matKey]; a trailing ".001"-style suffix is ignored.
//  - Joint angle θ (deg) is applied as node.quaternion = restQuat * axisAngle(axis, θ - zero).
//    The axis is expressed in the node's local frame.
import * as RL from './realism.js';
import { toCreasedNormals } from './BufferGeometryUtils.js';

export async function loadRobot(THREE, GLTFLoader, baseUrl, manifest, opts = {}) {
  const url = opts.resolve ? (p) => opts.resolve(p) : (p) => baseUrl.replace(/\/?$/, '/') + p;
  const gltf = await new GLTFLoader().loadAsync(url(manifest.glb));
  const root = gltf.scene;                                   // mm, Z up
  const zup = new THREE.Group(); zup.add(root);
  const object = new THREE.Group(); object.add(zup);         // Y up, metres
  zup.rotation.x = -Math.PI / 2; zup.scale.setScalar(0.001);

  // ---------- screens ----------
  const screens = {};
  for (const [name, s] of Object.entries(manifest.screens || {})) {
    const cv = document.createElement('canvas'); cv.width = s.res[0]; cv.height = s.res[1];
    const ctx = cv.getContext('2d'); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, cv.width, cv.height);
    const material = RL.screenMaterial(THREE, cv, { round: !!s.round, res: s.res, brightness: s.brightness ?? 1.25 });
    screens[name] = { canvas: cv, ctx, material, spec: s };
  }

  // ---------- materials ----------
  const matCache = {};
  const internal = [];
  function materialFor(key) {
    if (matCache[key]) return matCache[key];
    const m = (manifest.materials || {})[key] || { type: 'print', color: '#bbbbbb' };
    let mat;
    switch (m.type) {
      case 'print': mat = RL.printMaterial(THREE, { color: m.color, roughness: m.roughness, layer: m.layer, axis: m.layerAxis, layerStrength: m.layerStrength, clearcoat: m.clearcoat }); break;
      case 'tpu': mat = RL.tpuMaterial(THREE, { color: m.color, axis: m.layerAxis }); break;
      case 'petg': mat = RL.glossyPetgMaterial(THREE, { color: m.color, axis: m.layerAxis }); break;
      case 'acrylic': mat = RL.acrylicMaterial(THREE, { color: m.color, opacity: m.opacity }); break;
      case 'screen': mat = screens[m.screen]?.material || new THREE.MeshStandardMaterial({ color: '#000' }); break;
      case 'led': mat = new THREE.MeshStandardMaterial({ color: m.color, emissive: m.color, emissiveIntensity: m.intensity ?? 1.5, roughness: 0.4 }); break;
      case 'metal': mat = new THREE.MeshPhysicalMaterial({ color: m.color || '#b8bcc2', metalness: 1, roughness: m.roughness ?? 0.35 }); break;
      case 'rubber': mat = new THREE.MeshPhysicalMaterial({ color: m.color || '#1d1e20', roughness: 0.9, sheen: 0.3 }); break;
      case 'internal': mat = new THREE.MeshStandardMaterial({ color: m.color || '#3b82f6', roughness: 0.5, metalness: 0.1 }); break;
      default: mat = new THREE.MeshPhysicalMaterial({ color: m.color || '#bbbbbb', roughness: m.roughness ?? 0.5 });
    }
    mat.userData.matKey = key; mat.userData.def = m;
    return (matCache[key] = mat);
  }
  const meshes = [];
  root.traverse((o) => {
    if (!o.isMesh) return;
    let nm = o.name || o.parent?.name || '';
    if (!nm.includes('__') && o.parent?.name?.includes('__')) nm = o.parent.name;
    const key = (nm.split('__')[1] || 'default').replace(/[._]\d{3}$/, '');
    // GLBs exported from trimesh often carry no normals/UVs: give them crease-angle normals,
    // and planar UVs for screens (uvAxes from manifest.screens, default x→u, z→v as seen from the front).
    if (!o.geometry.attributes.normal) o.geometry = toCreasedNormals(o.geometry, THREE.MathUtils.degToRad(manifest.creaseDeg ?? 40));
    const mdef = (manifest.materials || {})[key] || {};
    if (mdef.type === 'screen' && !o.geometry.attributes.uv) {
      const ax = (manifest.screens?.[mdef.screen]?.uvAxes) || ['x', 'z'];
      const g = o.geometry; g.computeBoundingBox(); const bb = g.boundingBox, pos = g.attributes.position;
      const uv = new Float32Array(pos.count * 2), idx = (a) => 'xyz'.indexOf(a.replace('-', ''));
      const mn = [bb.min.x, bb.min.y, bb.min.z], mx = [bb.max.x, bb.max.y, bb.max.z];
      for (let i = 0; i < pos.count; i++) {
        const P = [pos.getX(i), pos.getY(i), pos.getZ(i)];
        let u = (P[idx(ax[0])] - mn[idx(ax[0])]) / ((mx[idx(ax[0])] - mn[idx(ax[0])]) || 1);
        let v = (P[idx(ax[1])] - mn[idx(ax[1])]) / ((mx[idx(ax[1])] - mn[idx(ax[1])]) || 1);
        if (ax[0].startsWith('-')) u = 1 - u; if (ax[1].startsWith('-')) v = 1 - v;
        uv[2 * i] = u; uv[2 * i + 1] = v;
      }
      g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    }
    o.material = materialFor(key);
    o.castShadow = true; o.receiveShadow = true;
    const def = (manifest.materials || {})[key] || {};
    if (def.type === 'internal' || def.internal) { internal.push(o); o.visible = false; }
    if (def.type === 'acrylic') { o.castShadow = false; o.renderOrder = 2; }
    // Crease-angle normals for STL-derived meshes without good normals
    if (opts.recomputeNormals && o.geometry) o.geometry.computeVertexNormals();
    meshes.push(o);
  });

  // ---------- joints ----------
  const joints = {};
  for (const [jn, j] of Object.entries(manifest.joints || {})) {
    const node = root.getObjectByName(j.node);
    if (!node) { console.warn('joint node missing', jn, j.node); continue; }
    joints[jn] = { node, axis: new THREE.Vector3(...j.axis).normalize(), rest: node.quaternion.clone(), zero: j.zero ?? 0, min: j.min ?? -180, max: j.max ?? 180, continuous: !!j.continuous, value: j.zero ?? 0 };
  }
  const _q = new THREE.Quaternion();
  function setJoint(name, deg) {
    const j = joints[name]; if (!j) return;
    if (!j.continuous) deg = Math.max(j.min, Math.min(j.max, deg));
    j.value = deg;
    _q.setFromAxisAngle(j.axis, THREE.MathUtils.degToRad(deg - j.zero));
    j.node.quaternion.copy(j.rest).multiply(_q);
  }
  function setPose(p) { for (const [k, v] of Object.entries(p || {})) setJoint(k, v); }

  // base pose: [x, y, z, qw, qx, qy, qz] in mm, Z up world, applied to the GLB root node
  const restRootPos = root.position.clone(), restRootQuat = root.quaternion.clone();
  function setBase(b) {
    if (!b) { root.position.copy(restRootPos); root.quaternion.copy(restRootQuat); return; }
    root.position.set(b[0], b[1], b[2]);
    root.quaternion.set(b[4], b[5], b[6], b[3]);
  }

  // ---------- faces ----------
  const faceImgs = {};
  async function loadFace(expr) {
    if (faceImgs[expr]) return faceImgs[expr];
    const def = (manifest.faces || {})[expr]; if (!def) return null;
    const out = {};
    for (const [scr, file] of Object.entries(def)) {
      const im = new Image(); im.src = url(file); await im.decode(); out[scr] = im;
    }
    return (faceImgs[expr] = out);
  }
  for (const k of Object.keys(manifest.faces || {})) await loadFace(k);
  let currentFace = null;
  function setFace(expr) {
    const f = faceImgs[expr]; if (!f || expr === currentFace) return;
    currentFace = expr;
    for (const [scr, im] of Object.entries(f)) {
      const s = screens[scr]; if (!s) continue;
      s.ctx.fillStyle = '#000'; s.ctx.fillRect(0, 0, s.canvas.width, s.canvas.height);
      s.ctx.drawImage(im, 0, 0, s.canvas.width, s.canvas.height);
      s.material.userData.texture.needsUpdate = true;
    }
  }

  // ---------- animations ----------
  const anims = {};
  for (const [k, f] of Object.entries(manifest.animations || {})) {
    try { anims[k] = await (await fetch(url(f))).json(); } catch (e) { console.warn('anim load failed', k, e); }
  }
  function applyFrame(a, t) {
    // t in seconds; linear interpolation of joints and base, step for faces
    const fps = a.fps || 30, n = a.frames || (a.joints ? Object.values(a.joints)[0].length : (a.base?.length || 1));
    let x = t * fps; if (a.loop) x = x % (n - 1); else x = Math.min(x, n - 1);
    const i = Math.floor(x), f = x - i, i2 = Math.min(i + 1, n - 1);
    for (const [jn, arr] of Object.entries(a.joints || {})) {
      const j = joints[jn];
      if (j && j.continuous) setJoint(jn, arr[i] + (arr[i2] - arr[i]) * f);
      else setJoint(jn, arr[i] + (arr[i2] - arr[i]) * f);
    }
    if (a.base) {
      const b0 = a.base[i], b1 = a.base[i2];
      const p = [0, 1, 2].map((k) => b0[k] + (b1[k] - b0[k]) * f);
      const q0 = new THREE.Quaternion(b0[4], b0[5], b0[6], b0[3]), q1 = new THREE.Quaternion(b1[4], b1[5], b1[6], b1[3]);
      q0.slerp(q1, f);
      setBase([...p, q0.w, q0.x, q0.y, q0.z]);
    }
    if (a.face) {
      let e = null; for (const [fi, ex] of a.face) { if (fi <= i) e = ex; else break; }
      if (e) setFace(e);
    }
    return { done: !a.loop && x >= n - 1, frame: i };
  }

  function setXray(on) {
    for (const o of meshes) {
      const def = o.material.userData.def || {};
      if (internal.includes(o)) { o.visible = on; continue; }
      if (on) {
        if (!o.userData.xmat) { o.userData.xmat = o.material.clone(); o.userData.xmat.transparent = true; o.userData.xmat.opacity = 0.18; o.userData.xmat.depthWrite = false; }
        if (def.type !== 'screen') o.material = o.userData.xmat;
      } else if (o.userData.xmat) o.material = matCache[def && o.userData.xmat.userData.matKey] || o.material;
    }
    if (!on) for (const o of meshes) { const key = o.userData.xmat?.userData?.matKey; if (key && matCache[key]) o.material = matCache[key]; }
  }

  setPose(manifest.pose_rest || {});
  if (manifest.faces?.neutral) setFace('neutral');
  return { object, root, joints, setJoint, setPose, setBase, screens, setFace, loadFace, anims, applyFrame, setXray, manifest, meshes, internal };
}
