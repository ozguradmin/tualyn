// realism.js: shared "what it will really look like" materials for Kıpır concept renders and the web viewer.
// Three.js r170, ES module. All geometry is in millimetres (object space), so layer heights are in mm.
//
//   import { printMaterial, screenMaterial, acrylicMaterial, tpuMaterial } from './realism.js';
//   mesh.material = printMaterial(THREE, { color: '#d9692f', layer: 0.16, axis: [0,0,1] });
//
// printMaterial: matte FDM plastic with layer lines.
//   The lines are a normal perturbation, sin(2π·(p·axis)/layer), plus a ±1.5% per-layer tint wobble.
//   They are faded out by screen-space derivatives (fwidth), so distant views don't moiré.
//   Top and bottom skins perpendicular to the layer axis show no lines, as on a real print.
// screenMaterial: an IPS LCD driven by a <canvas> at native resolution.
//   Uses NEAREST magnification, a visible pixel grid when you zoom in, IPS black glow, round mask and a backlight level.
// acrylicMaterial: smoked acrylic / glossy PETG visor in front of the screens.
//   It darkens what is behind it and adds reflections.
// tpuMaterial: soft, slightly sheeny TPU for feet, paws and ears.

export const FILAMENTS = {
  // Approximate colours of common PLA lines sold in Turkey (Elas, Porima, eSun, Bambu Lab).
  // Hexes are photo-matched approximations.
  'PLA Beyaz': '#eeeae2', 'PLA Krem / Fildişi': '#efe4cc', 'PLA Turuncu': '#e0692b', 'PLA Tarçın / Bakır': '#c9693b',
  'PLA Mint': '#9fd8c3', 'PLA Pastel Yeşil': '#a8d5b0', 'PLA Mercan / Somon': '#f2846b', 'PLA Pembe': '#f3a6b5',
  'PLA Sarı': '#f6c544', 'PLA Pastel Sarı': '#f4d77e', 'PLA Bal': '#e9a73c', 'PLA Siyah': '#26272b',
  'PLA Antrasit': '#3a3c41', 'PLA Gri': '#8e9196', 'PLA Lacivert': '#2b3a67', 'PLA Kahve': '#6b4630',
  'PETG Siyah (parlak)': '#141518', 'TPU Siyah': '#202124', 'TPU Beyaz': '#ece9e3', 'TPU Kırmızı': '#d64a3a',
};

function axisVec(THREE, axis) {
  if (Array.isArray(axis)) return new THREE.Vector3(...axis).normalize();
  return new THREE.Vector3(axis === 'x' ? 1 : 0, axis === 'y' ? 1 : 0, axis === 'z' || !axis ? 1 : 0);
}

export function printMaterial(THREE, o = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color: o.color || '#cccccc', roughness: o.roughness ?? 0.62, metalness: 0,
    clearcoat: o.clearcoat ?? 0.0, clearcoatRoughness: 0.6, sheen: o.sheen ?? 0.08, sheenRoughness: 0.8,
    sheenColor: new THREE.Color(o.color || '#cccccc').multiplyScalar(0.4),
  });
  const layer = o.layer ?? 0.16, strength = o.layerStrength ?? 0.55, ax = axisVec(THREE, o.axis);
  m.userData.print = { layer, strength, axis: ax };
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uLayer = { value: layer };
    sh.uniforms.uLayerStrength = { value: strength };
    sh.uniforms.uLayerAxis = { value: ax };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vObjPos;\nvarying vec3 vAxisView;\nuniform vec3 uLayerAxis;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvObjPos = position;\nvAxisView = normalize((modelViewMatrix * vec4(uLayerAxis, 0.0)).xyz);');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vObjPos; varying vec3 vAxisView; uniform float uLayer; uniform float uLayerStrength; uniform vec3 uLayerAxis;
float kHash(float n){ return fract(sin(n*127.1)*43758.5453); }`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  float h = dot(vObjPos, uLayerAxis) / uLayer;          // layer coordinate
  float ph = h * 6.2831853;
  float fw = fwidth(ph);                                   // radians per pixel
  float fade = clamp(1.0 - (fw - 1.2) / 2.6, 0.0, 1.0);    // full below ~5 px/layer, gone at ~1.6 px/layer (no moire)
  float side = 1.0 - abs(dot(normal, vAxisView));          // lines only on walls
  // FDM bead profile ~ rounded: use a sharpened cosine for the slope
  float slope = sin(ph) * (0.6 + 0.4 * abs(sin(ph)));
  normal = normalize(normal - vAxisView * slope * uLayerStrength * side * fade);
}`)
      .replace('#include <color_fragment>', `#include <color_fragment>
{
  float li = floor(dot(vObjPos, uLayerAxis) / uLayer);
  diffuseColor.rgb *= 1.0 + 0.03 * (kHash(li) - 0.5);
}`);
  };
  // layer/strength/axis are uniforms (set per material in onBeforeCompile), so every print material can share one program
  m.customProgramCacheKey = () => 'print';
  return m;
}

export function tpuMaterial(THREE, o = {}) {
  return printMaterial(THREE, { roughness: 0.82, sheen: 0.35, layer: o.layer ?? 0.2, layerStrength: 0.4, ...o });
}

export function acrylicMaterial(THREE, o = {}) {
  // Smoked acrylic: a dark tinted, glossy, partially see-through sheet.
  // opacity ~ 1 - transmittance: typical 'füme' acrylic transmits 25-50 %.
  return new THREE.MeshPhysicalMaterial({
    color: o.color || '#0b0c0e', roughness: o.roughness ?? 0.06, metalness: 0, clearcoat: 1.0, clearcoatRoughness: 0.04,
    transparent: true, opacity: o.opacity ?? 0.62, depthWrite: false, ior: 1.49, specularIntensity: 1.0,
  });
}

export function glossyPetgMaterial(THREE, o = {}) {
  return printMaterial(THREE, { color: o.color || '#141518', roughness: 0.28, clearcoat: 0.35, layer: o.layer ?? 0.16, layerStrength: 0.3, ...o });
}

// Screen: emissive canvas texture at native resolution. canvas is drawn by the caller; call tex.needsUpdate = true per frame.
export function screenMaterial(THREE, canvas, o = {}) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.LinearMipmapLinearFilter; tex.anisotropy = 4;
  const res = o.res || [canvas.width, canvas.height];
  const m = new THREE.MeshPhysicalMaterial({
    color: '#000000', roughness: 0.18, metalness: 0, clearcoat: 0.6, clearcoatRoughness: 0.08,
    emissive: '#ffffff', emissiveMap: tex, emissiveIntensity: o.brightness ?? 1.25,
  });
  m.userData.texture = tex;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uRes = { value: new THREE.Vector2(res[0], res[1]) };
    sh.uniforms.uRound = { value: o.round ? 1.0 : 0.0 };
    sh.uniforms.uBlackGlow = { value: o.blackGlow ?? 0.018 };
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec2 uRes; uniform float uRound; uniform float uBlackGlow;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  vec2 uvp = vEmissiveMapUv * uRes;
  vec2 f = fract(uvp);
  float fw = max(fwidth(uvp.x), fwidth(uvp.y));
  float gridVis = clamp(1.0 - fw * 2.5, 0.0, 1.0);          // visible only when a pixel spans > ~2.5 screen px
  float gx = smoothstep(0.0, 0.12, f.x) * smoothstep(1.0, 0.88, f.x);
  float gy = smoothstep(0.0, 0.12, f.y) * smoothstep(1.0, 0.88, f.y);
  totalEmissiveRadiance *= mix(1.0, 0.55 + 0.45 * gx * gy, gridVis);
  // IPS black is never black: faint bluish glow, a bit stronger at the edges (backlight bleed)
  vec2 c = vEmissiveMapUv - 0.5;
  float edge = smoothstep(0.30, 0.5, length(c));
  totalEmissiveRadiance += vec3(0.55, 0.62, 0.75) * uBlackGlow * (1.0 + 1.5 * edge);
  if (uRound > 0.5 && length(c) > 0.5) totalEmissiveRadiance = vec3(0.0);
}`);
  };
  m.customProgramCacheKey = () => 'screen' + (o.round ? 'r' : 's');   // uRes etc. are uniforms
  return m;
}
