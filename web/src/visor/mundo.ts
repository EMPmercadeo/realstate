/*
  Mundo: todo lo que rodea a los edificios y les da vida.
  Terreno ondulado con césped, colinas y el Volcán Barú al norte, bosque lejano,
  árboles y palmeras estilizadas con viento, nubes, pájaros, agua con reflejos,
  bruma de hora dorada. Todo procedural (sin descargas) e instanciado.
*/
import * as THREE from 'three';
import { Water } from 'three/examples/jsm/objects/Water.js';

// ---------- ruido ----------
function hash(x: number, y: number) { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); }
function vnoise(x: number, y: number) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy), b = hash(ix + 1, iy), c = hash(ix, iy + 1), d = hash(ix + 1, iy + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function fbm(x: number, y: number, oct = 4) { let s = 0, a = 0.5, f = 1; for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f); a *= 0.5; f *= 2; } return s; }
let seed = 7;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };

export interface Mundo { update: (t: number, dt: number, cam: THREE.Camera) => void; agua: Water[]; escenaNubes: THREE.Scene; }

// Zona plana del lote (coordenadas three.js: x = x sitio, z = -y sitio)
let LOTE = { x0: -22, x1: 62, z0: -112, z1: 30 };

// Sitio del modelo amueblado (residencia.glb): lote real, calles del satélite y vegetación del lote.
// Sin configuración se usa la maqueta anterior (portada cinematográfica).
export interface ConfigMundo {
  lote: { x0: number; x1: number; z0: number; z1: number };
  calles: { ancho: number; puntos: number[][] }[];
  arboles: number[][]; palmas: number[][];
  centro: number[];
}
function alturaTerreno(x: number, z: number) {
  // plano dentro del lote y los vecinos, ondulado afuera, colinas lejos, montaña al norte (z negativo)
  const dx = Math.max(0, LOTE.x0 - x, x - LOTE.x1), dz = Math.max(0, LOTE.z0 - z, z - LOTE.z1);
  const d = Math.hypot(dx, dz);
  const k = THREE.MathUtils.smoothstep(d, 10, 90);
  if (k <= 0) return 0;
  let h = (fbm(x * 0.012 + 3, z * 0.012 + 9, 4) - 0.45) * 26;
  const r = Math.hypot(x - 20, z + 40);
  h += THREE.MathUtils.smoothstep(r, 420, 1300) * 180 * (0.55 + 0.45 * fbm(x * 0.004, z * 0.004, 3));
  // Volcán Barú al norte
  const dv = Math.hypot((x - 60) / 1.5, z + 1750);
  h += Math.max(0, 1 - dv / 1000) ** 1.5 * 1500;
  return h * k;
}

function windShader(mat: THREE.Material, fuerza: number, uTime: { value: number }) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = uTime; sh.uniforms.uWind = { value: fuerza };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uTime; uniform float uWind;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        #ifdef USE_INSTANCING
          vec4 wp = instanceMatrix * vec4(position, 1.0);
        #else
          vec4 wp = vec4(position, 1.0);
        #endif
        float k = clamp(position.y / 6.0, 0.0, 1.0); k = k * k;
        float ph = uTime * 1.3 + wp.x * 0.15 + wp.z * 0.11;
        transformed.x += (sin(ph) * 0.35 + sin(ph * 2.7) * 0.12) * uWind * k;
        transformed.z += (cos(ph * 0.8) * 0.25) * uWind * k;`);
  };
}

export function crearMundo(scene: THREE.Scene, renderer: THREE.WebGLRenderer, movil: boolean, sunDir: THREE.Vector3, evitar: number[][] = [], cfg?: ConfigMundo): Mundo {
  const uTime = { value: 0 };
  if (cfg) LOTE = cfg.lote;
  // desplazamiento del vecindario respecto al centro de la maqueta anterior (16, -40)
  const DX = cfg ? cfg.centro[0] - 16 : 0, DZ = cfg ? cfg.centro[1] + 40 : 0;
  // distancia de un punto a las calles (para no poner casas ni árboles encima)
  const segs: [number, number, number, number, number][] = [];
  if (cfg) for (const c of cfg.calles) {
    const p = prolongar(c.puntos, 260);
    for (let i = 0; i < p.length - 1; i++) segs.push([p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], c.ancho]);
  }
  const cercaCalle = (x: number, z: number, m: number) => segs.some(([x0, z0, x1, z1, w]) => distSeg(x, z, x0, z0, x1, z1) < w / 2 + m);
  const enZonaLote = (x: number, z: number, m = 0) => x > LOTE.x0 - m && x < LOTE.x1 + m && z > LOTE.z0 - m && z < LOTE.z1 + m;
  const grupo = new THREE.Group(); grupo.name = 'mundo'; scene.add(grupo);

  // ---------- terreno ----------
  const TS = 3200, SEG = movil ? 160 : 260;
  const tg = new THREE.PlaneGeometry(TS, TS, SEG, SEG); tg.rotateX(-Math.PI / 2);
  const pos = tg.attributes.position as THREE.BufferAttribute;
  const col = new Float32Array(pos.count * 3);
  const cA = new THREE.Color('#4f8a3a'), cB = new THREE.Color('#8fae4a'), cC = new THREE.Color('#6b7a46'), cR = new THREE.Color('#5a6e4e');
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) + 20, z = pos.getZ(i) - 40;
    const h = alturaTerreno(x, z);
    pos.setX(i, x); pos.setZ(i, z); pos.setY(i, h - 0.05);
    const n = fbm(x * 0.05, z * 0.05, 3);
    const c = new THREE.Color().copy(cA).lerp(cB, n);
    if (h > 60) c.lerp(cC, THREE.MathUtils.smoothstep(h, 60, 300));
    if (h > 500) c.lerp(cR, THREE.MathUtils.smoothstep(h, 500, 1200));
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
  }
  tg.setAttribute('color', new THREE.BufferAttribute(col, 3));
  tg.computeVertexNormals();
  const texCesped = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d')!;
    const img = g.createImageData(256, 256);
    for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
      const i = (y * 256 + x) * 4; const n = 0.78 + 0.22 * fbm(x / 9, y / 9, 3) + (hash(x, y) - 0.5) * 0.16;
      img.data[i] = 255 * n; img.data[i + 1] = 255 * n; img.data[i + 2] = 255 * n; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(220, 220); t.anisotropy = 4; return t;
  })();
  const terreno = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ vertexColors: true, map: texCesped, roughness: 1, metalness: 0 }));
  tg.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(Array.from({ length: pos.count }, (_, i) => [pos.getX(i) / TS, pos.getZ(i) / TS]).flat()), 2));
  terreno.receiveShadow = true; terreno.name = 'terreno'; grupo.add(terreno);

  // ---------- calles y vecindario ----------
  const matAsfalto = new THREE.MeshStandardMaterial({ color: '#5c5e5c', roughness: 0.95 });
  const calle = (x0: number, z0: number, x1: number, z1: number, w: number) => {
    const L = Math.hypot(x1 - x0, z1 - z0); const g = new THREE.PlaneGeometry(w, L); g.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(g, matAsfalto); m.position.set((x0 + x1) / 2, 0.02, (z0 + z1) / 2); m.rotation.y = -Math.atan2(z1 - z0, x1 - x0) + Math.PI / 2;
    m.receiveShadow = true; grupo.add(m); return m;
  };
  if (cfg) {
    // calles reales (C.A y calle de tierra), prolongadas fuera del recorte del satélite
    const matTierra = new THREE.MeshStandardMaterial({ color: '#8a7a62', roughness: 1 });
    cfg.calles.forEach((c, k) => {
      const p = prolongar(c.puntos, 260);
      for (let i = 0; i < p.length - 1; i++) {
        const m = calle(p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], c.ancho);
        if (k === 1) m.material = matTierra;
        m.position.y = 0.01 + k * 0.004;
        // junta suave entre tramos
        const j = new THREE.Mesh(new THREE.CircleGeometry(c.ancho / 2, 20).rotateX(-Math.PI / 2), k === 1 ? matTierra : matAsfalto);
        j.position.set(p[i + 1][0], 0.01 + k * 0.004, p[i + 1][1]); j.receiveShadow = true; grupo.add(j);
      }
    });
  } else {
    // la calle del lote sigue hacia el norte y el sur; una transversal al sur
    calle(36.5, 230, 36.5, -330, 9); calle(-180, 30, 230, 30, 7); calle(-180, -112, 230, -112, 7);
    // acera entre la cerca del lote y la calle, y línea central
    const acera = new THREE.Mesh(new THREE.PlaneGeometry(2, 100).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#b9b4a8', roughness: 1 }));
    acera.position.set(31, 0.03, -42); acera.receiveShadow = true; grupo.add(acera);
    const linea = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 560).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: '#e8e2c8' }));
    linea.position.set(36.5, 0.04, -50); grupo.add(linea);
  }
  const casas: THREE.Matrix4[] = []; const techos: THREE.Matrix4[] = []; const colores: THREE.Color[] = [];
  const paleta = ['#f3e6c8', '#e9d7a6', '#f2efe6', '#d9c9a8', '#efe1d2', '#e2ccb4'];
  const o = new THREE.Object3D();
  const lotes: [number, number][] = [];
  for (let i = 0; i < 46; i++) {
    const x = -170 + rnd() * 390 + DX, z = -300 + rnd() * 420 + DZ;
    if (cfg) {
      if (enZonaLote(x, z, 6) || cercaCalle(x, z, 9)) continue;
    } else {
      if (x > -14 && x < 60 && z > -118 && z < 36) continue;              // lote y calle
      if (Math.abs(x - 36.5) < 9 || Math.abs(z - 30) < 8 || Math.abs(z + 112) < 8) continue;
    }
    if (lotes.some(([a, b]) => Math.hypot(a - x, b - z) < 22)) continue;
    lotes.push([x, z]);
    const w = 9 + rnd() * 6, d = 8 + rnd() * 5, h = 3 + rnd() * 0.8;
    o.position.set(x, alturaTerreno(x, z), z); o.rotation.set(0, Math.round(rnd() * 2) * Math.PI / 2 + (rnd() - 0.5) * 0.2, 0); o.scale.set(w, h, d); o.updateMatrix();
    casas.push(o.matrix.clone()); colores.push(new THREE.Color(paleta[i % paleta.length]));
    o.scale.set(w + 1.2, 2.2 + rnd(), d + 1.2); o.position.y += h; o.updateMatrix(); techos.push(o.matrix.clone());
  }
  const gCasa = new THREE.BoxGeometry(1, 1, 1); gCasa.translate(0, 0.5, 0);
  const mCasas = new THREE.InstancedMesh(gCasa, new THREE.MeshStandardMaterial({ roughness: 0.9 }), casas.length);
  casas.forEach((m, i) => { mCasas.setMatrixAt(i, m); mCasas.setColorAt(i, colores[i]); });
  const gTecho = new THREE.ConeGeometry(0.72, 1, 4); gTecho.rotateY(Math.PI / 4); gTecho.translate(0, 0.5, 0);
  const mTechos = new THREE.InstancedMesh(gTecho, new THREE.MeshStandardMaterial({ roughness: 0.9 }), techos.length);
  const paletaTecho = ['#b5513a', '#9c4a36', '#b8b8b2', '#a85a3c', '#8f8f8a'];
  techos.forEach((m, i) => { mTechos.setMatrixAt(i, m); mTechos.setColorAt(i, new THREE.Color(paletaTecho[i % paletaTecho.length])); });
  mCasas.castShadow = mCasas.receiveShadow = true; mTechos.castShadow = true;
  grupo.add(mCasas, mTechos);

  // ---------- vegetación estilizada ----------
  const matHoja = new THREE.MeshStandardMaterial({ color: '#3f8a3c', roughness: 0.9, flatShading: true, vertexColors: true });
  const matHoja2 = new THREE.MeshStandardMaterial({ color: '#7fb04a', roughness: 0.9, flatShading: true, vertexColors: true });
  const matTronco = new THREE.MeshStandardMaterial({ color: '#6b4a2e', roughness: 1, flatShading: true });
  const matFronda = new THREE.MeshStandardMaterial({ color: '#4f9a3c', roughness: 0.85, side: THREE.DoubleSide, flatShading: true, vertexColors: true });
  windShader(matHoja, 1, uTime); windShader(matHoja2, 1, uTime); windShader(matFronda, 1.6, uTime);

  function tintar(g: THREE.BufferGeometry, base: THREE.Color, var_ = 0.12) {
    const p = g.attributes.position; const c = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) {
      const k = 0.85 + (p.getY(i) / 10) * 0.6 + (rnd() - 0.5) * var_;
      c[i * 3] = base.r * k; c[i * 3 + 1] = base.g * k; c[i * 3 + 2] = base.b * k;
    }
    g.setAttribute('color', new THREE.BufferAttribute(c, 3)); return g;
  }
  // copa de árbol: varias masas facetadas
  function geoCopa(h: number) {
    const gs: THREE.BufferGeometry[] = [];
    const n = 6;
    for (let i = 0; i < n; i++) {
      const r = h * (0.22 + rnd() * 0.14);
      const g = new THREE.IcosahedronGeometry(r, 1);
      const a = (i / n) * Math.PI * 2 + rnd();
      const d = i === 0 ? 0 : h * 0.22;
      g.translate(Math.cos(a) * d, h * 0.72 + (rnd() - 0.5) * h * 0.18 + (i === 0 ? h * 0.08 : 0), Math.sin(a) * d);
      gs.push(g);
    }
    return tintar(mergeGeos(gs), new THREE.Color('#4a9440'), 0.25);
  }
  function geoTronco(h: number, r = 0.22) {
    const g = new THREE.CylinderGeometry(r * 0.55, r, h * 0.62, 7); g.translate(0, h * 0.31, 0);
    const ramas: THREE.BufferGeometry[] = [g];
    for (let i = 0; i < 3; i++) {
      const b = new THREE.CylinderGeometry(0.04, r * 0.5, h * 0.3, 5); b.translate(0, h * 0.15, 0);
      b.rotateZ(0.6).rotateY((i / 3) * Math.PI * 2); b.translate(0, h * 0.5, 0); ramas.push(b);
    }
    return mergeGeos(ramas);
  }
  // palmera: tronco curvo + frondas geométricas
  function geoPalmaTronco(h: number) {
    const pts: THREE.Vector3[] = []; const lean = 0.18 + rnd() * 0.2;
    for (let i = 0; i <= 8; i++) { const t = i / 8; pts.push(new THREE.Vector3(Math.sin(t * 1.3) * lean * h, t * h, 0)); }
    const g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 10, 0.2, 7, false);
    g.scale(1, 1, 1); return g;
  }
  function geoFrondas(h: number) {
    const gs: THREE.BufferGeometry[] = []; const lean = 0.18;
    const top = new THREE.Vector3(Math.sin(1.3) * lean * h, h, 0);
    const nf = 11;
    for (let i = 0; i < nf; i++) {
      const L = 3.4 + rnd() * 0.8, W = 0.9;
      const g = new THREE.PlaneGeometry(W, L, 2, 8);
      const p = g.attributes.position as THREE.BufferAttribute;
      for (let k = 0; k < p.count; k++) {
        const y = p.getY(k) + L / 2; const x = p.getX(k); const t = y / L;
        p.setZ(k, -t * t * 2.2 + Math.abs(x) * 0.35 * (1 - t));
        p.setX(k, x * (1 - t * 0.8));
      }
      g.rotateX(-Math.PI / 2 + 0.25 + rnd() * 0.3);
      g.rotateY((i / nf) * Math.PI * 2 + rnd() * 0.3);
      g.translate(top.x, top.y - 0.05, top.z);
      gs.push(g);
    }
    return tintar(mergeGeos(gs), new THREE.Color('#4f9a3c'), 0.2);
  }

  const posArboles: [number, number, number][] = [];   // x, z, h
  const posPalmas: [number, number, number][] = [];
  // dentro del lote: posiciones del programa (sitio x,y → three x, -y)
  const ARB = [[3, 36, 9], [4, 48, 8], [26, 50, 7], [3, 76, 9], [12, 77, 8], [26, 78, 6], [3, 4, 8], [22, 2, 7]];
  const PAL = [[27, 72, 7], [27, 50, 6.5], [16, 75, 7], [4, 72, 6], [27, 40, 5.5], [15, 47, 6], [28, 34, 6], [1, 42, 6], [1, 54, 7], [2, 64, 6.5], [26.8, 60.2, 3.4]];
  const libre = (x: number, z: number) => !evitar.some(([ex, ez]) => Math.hypot(ex - x, ez - z) < 9);
  if (cfg) {
    for (const [x, z, h] of cfg.arboles) if (libre(x, z)) posArboles.push([x, z, h * 0.85]);
    for (const [x, z, h] of cfg.palmas) if (libre(x, z)) posPalmas.push([x, z, h * 0.9]);
  } else {
    for (const [x, y, h] of ARB) if (libre(x, -y)) posArboles.push([x, -y, h * 0.72]);
    for (const [x, y, h] of PAL) if (libre(x, -y)) posPalmas.push([x, -y, h * 0.85]);
  }
  // vecindario y campo: árboles sueltos (sin invadir el lote ni la calle)
  const enLote = (x: number, z: number) => cfg ? enZonaLote(x, z) : x > -3 && x < 34 && z > -88 && z < 4;
  const enCalle = (x: number, z: number) => cfg ? cercaCalle(x, z, 2) : x > 31 && x < 42;
  const nVec = movil ? 140 : 320;
  for (let i = 0; i < nVec; i++) {
    const x = -200 + rnd() * 440 + DX, z = -260 + rnd() * 380 + DZ;
    if (enLote(x, z) || enCalle(x, z)) continue;
    if (!cfg && (Math.abs(z - 30) < 6 || Math.abs(z + 112) < 6)) continue;
    if (lotes.some(([a, b]) => Math.abs(a - x) < 9 && Math.abs(b - z) < 8)) continue;
    if (evitar.some(([ex, ez]) => Math.hypot(ex - x, ez - z) < 9)) continue;
    (rnd() < 0.28 ? posPalmas : posArboles).push([x, z, 5 + rnd() * 6]);
  }
  // bosque lejano, denso y barato
  const nBosque = movil ? 900 : 2600;
  const posBosque: [number, number, number][] = [];
  for (let i = 0; i < nBosque; i++) {
    const a = rnd() * Math.PI * 2, r = 200 + rnd() * 900;
    const x = 20 + DX + Math.cos(a) * r, z = -40 + DZ + Math.sin(a) * r;
    if (fbm(x * 0.01, z * 0.01, 2) < 0.42) continue;
    posBosque.push([x, z, 7 + rnd() * 9]);
  }

  function matrices(lista: [number, number, number][], hRef: number) {
    const o = new THREE.Object3D();
    return lista.map(([x, z, h]) => {
      const y = enLote(x, z) ? 0 : alturaTerreno(x, z);
      o.position.set(x, y - 0.1, z); o.rotation.set(0, rnd() * Math.PI * 2, 0); const s = h / hRef; o.scale.set(s * (0.9 + rnd() * 0.2), s, s * (0.9 + rnd() * 0.2));
      o.updateMatrix(); return o.matrix.clone();
    });
  }
  function instanciar(geo: THREE.BufferGeometry, mat: THREE.Material, ms: THREE.Matrix4[], sombra: boolean) {
    const m = new THREE.InstancedMesh(geo, mat, ms.length);
    ms.forEach((mx, i) => m.setMatrixAt(i, mx));
    m.castShadow = sombra; m.receiveShadow = sombra; m.frustumCulled = false; grupo.add(m); return m;
  }
  const mA = matrices(posArboles, 8), mP = matrices(posPalmas, 7), mB = matrices(posBosque, 9);
  instanciar(geoTronco(8), matTronco, mA, true);
  instanciar(geoCopa(8), matHoja, mA, true);
  instanciar(geoPalmaTronco(7), matTronco, mP, true);
  instanciar(geoFrondas(7), matFronda, mP, true);
  const gb = new THREE.ConeGeometry(3.2, 9, 6); gb.translate(0, 5.5, 0);
  const gb2 = new THREE.IcosahedronGeometry(3.4, 0); gb2.translate(0, 6.5, 0);
  instanciar(tintar(mergeGeos([gb, gb2]), new THREE.Color('#3f7f36'), 0.3), matHoja2, mB, false);

  // ---------- nubes ----------
  // las nubes van en una escena aparte (se dibujan después del post-proceso: el AO las ennegrecía)
  const escenaNubes = new THREE.Scene(); escenaNubes.fog = scene.fog;
  const nubes = new THREE.Group(); escenaNubes.add(nubes);
  const texNube = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d')!;
    for (let i = 0; i < 14; i++) {
      const x = 60 + Math.random() * 136, y = 100 + Math.random() * 70, r = 30 + Math.random() * 50;
      const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
    }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const nubeDatos: { s: THREE.Sprite; v: number }[] = [];
  for (let i = 0; i < (movil ? 10 : 18); i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: texNube, transparent: true, opacity: 0.85, depthWrite: false, color: '#fff2e2' }));
    const w = 120 + rnd() * 220;
    s.scale.set(w, w * 0.45, 1);
    s.position.set(-700 + rnd() * 1400, 140 + rnd() * 120, -900 + rnd() * 1100);
    nubes.add(s); nubeDatos.push({ s, v: 0.6 + rnd() * 0.9 });
  }

  // ---------- pájaros ----------
  const nP = movil ? 10 : 18;
  const gAve = new THREE.BufferGeometry();
  const av = new Float32Array([-1.2, 0, 0.2, 0, 0, 0, 0, 0, -0.5, 1.2, 0, 0.2, 0, 0, 0, 0, 0, -0.5]);
  gAve.setAttribute('position', new THREE.BufferAttribute(av, 3));
  const mAve = new THREE.MeshBasicMaterial({ color: '#2b2622', side: THREE.DoubleSide });
  const aves = new THREE.InstancedMesh(gAve, mAve, nP); aves.frustumCulled = false; grupo.add(aves);
  const aveDatos = Array.from({ length: nP }, (_, i) => ({ ph: i * 0.7, r: 95 + rnd() * 70, h: 48 + rnd() * 30, off: rnd() * 6.28, s: 0.8 + rnd() * 0.5 }));

  // ---------- agua ----------
  const agua: Water[] = [];
  function crearAgua(mesh: THREE.Mesh) {
    mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox!.clone().applyMatrix4(mesh.matrixWorld);
    const w = bb.max.x - bb.min.x, d = bb.max.z - bb.min.z;
    const geo = (mesh.geometry as any).parameters?.radiusTop !== undefined
      ? new THREE.CircleGeometry(Math.max(w, d) / 2, 48)
      : new THREE.PlaneGeometry(w, d);
    const water = new Water(geo, {
      textureWidth: movil ? 256 : 512, textureHeight: movil ? 256 : 512,
      waterNormals: texturaNormalesAgua(),
      sunDirection: sunDir.clone(), sunColor: 0xfff1d6, waterColor: 0x2a7f9a, distortionScale: 0.5, fog: true,
    });
    water.rotation.x = -Math.PI / 2;
    water.position.set((bb.min.x + bb.max.x) / 2, bb.max.y + 0.02, (bb.min.z + bb.max.z) / 2);
    (water.material as THREE.ShaderMaterial).uniforms.size.value = 10;
    (water.material as THREE.ShaderMaterial).uniforms.alpha.value = 0.95;
    grupo.add(water); agua.push(water); mesh.visible = false;
  }

  function update(t: number, dt: number, cam: THREE.Camera) {
    uTime.value = t;
    for (const n of nubeDatos) { n.s.position.x += n.v * dt * 2; if (n.s.position.x > 800) n.s.position.x = -800; }
    const o = new THREE.Object3D();
    aveDatos.forEach((a, i) => {
      const ang = t * 0.12 * a.s + a.off;
      o.position.set(16 + DX + Math.cos(ang) * a.r + Math.sin(t * 0.5 + a.ph) * 6, a.h + Math.sin(t * 0.7 + a.ph) * 3, -40 + DZ + Math.sin(ang) * a.r * 0.8);
      o.rotation.set(0, -ang + Math.PI / 2, Math.sin(t * 9 + a.ph) * 0.55);
      o.scale.setScalar(0.7); o.updateMatrix(); aves.setMatrixAt(i, o.matrix);
    });
    aves.instanceMatrix.needsUpdate = true;
    for (const w of agua) (w.material as THREE.ShaderMaterial).uniforms.time.value = t * 0.6;
  }

  return { update, agua, crearAgua, escenaNubes } as Mundo & { crearAgua: typeof crearAgua };
}

// alarga una polilínea por sus dos extremos (las calles siguen más allá del recorte del satélite)
function prolongar(p: number[][], L: number) {
  if (p.length < 2) return p;
  const ext = (a: number[], b: number[]) => { const dx = a[0] - b[0], dz = a[1] - b[1], d = Math.hypot(dx, dz) || 1; return [a[0] + (dx / d) * L, a[1] + (dz / d) * L]; };
  return [ext(p[0], p[1]), ...p, ext(p[p.length - 1], p[p.length - 2])];
}
function distSeg(x: number, z: number, x0: number, z0: number, x1: number, z1: number) {
  const dx = x1 - x0, dz = z1 - z0, L2 = dx * dx + dz * dz || 1;
  const t = Math.max(0, Math.min(1, ((x - x0) * dx + (z - z0) * dz) / L2));
  return Math.hypot(x - (x0 + t * dx), z - (z0 + t * dz));
}

function texturaNormalesAgua() {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d')!;
  const img = g.createImageData(256, 256);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
    const i = (y * 256 + x) * 4;
    const nx = fbm(x / 23, y / 23, 3) - fbm((x + 1) / 23, y / 23, 3);
    const ny = fbm(x / 23, y / 23, 3) - fbm(x / 23, (y + 1) / 23, 3);
    img.data[i] = 128 + nx * 900; img.data[i + 1] = 128 + ny * 900; img.data[i + 2] = 255; img.data[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}

function mergeGeos(gs: THREE.BufferGeometry[]) {
  // fusión simple (sin índices) para geometrías con position (+ normal opcional)
  const out: number[] = [];
  for (const g of gs) {
    const ng = g.index ? g.toNonIndexed() : g;
    const p = ng.attributes.position; for (let i = 0; i < p.count; i++) out.push(p.getX(i), p.getY(i), p.getZ(i));
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(out, 3));
  geo.computeVertexNormals();
  return geo;
}
