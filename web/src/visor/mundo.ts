/*
  Mundo: lo que rodea a los edificios.
  Ronda 3 (realismo, 01-11-2026): las calles del barrio salen de OpenStreetMap (web/src/data/vecindario.json,
  © colaboradores de OpenStreetMap, ODbL) y las del lote de sitio.py; las casas vecinas se levantan a lo
  largo de esas calles (las que OSM tiene mapeadas van en su lugar real); el terreno lleva césped con
  textura; árboles y palmas con follaje de tarjetas; Volcán Barú al norte, nubes, pájaros y agua.
*/
import * as THREE from 'three';
import { Water } from 'three/examples/jsm/objects/Water.js';
import vecindario from '../data/vecindario.json';
import { texturas, materialCesped, materialCalle, detallar, ESTUCO, LAMINA, type Texturas } from './realismo';
import { plantar, type Vegetal, type Especie } from './vegetacion';

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

export interface ConfigMundo {
  lote: { x0: number; x1: number; z0: number; z1: number };
  calles: { ancho: number; puntos: number[][] }[];
  arboles: number[][]; palmas: number[][];
  vegetacion?: (string | number)[][];
  poligono?: number[][];
  centro: number[];
}
function alturaTerreno(x: number, z: number) {
  // plano en todo el barrio (David es llano), lomas lejos y el Volcán Barú al norte (z negativo)
  const dx = Math.max(0, LOTE.x0 - x, x - LOTE.x1), dz = Math.max(0, LOTE.z0 - z, z - LOTE.z1);
  const d = Math.hypot(dx, dz);
  const k = THREE.MathUtils.smoothstep(d, 380, 720);
  if (k <= 0) return 0;
  // llanura de David: ondulaciones suaves y lomas bajas al norte; el Barú es una silueta lejana aparte
  let h = (fbm(x * 0.008 + 3, z * 0.008 + 9, 4) - 0.45) * 14;
  h += THREE.MathUtils.smoothstep(-z, 600, 1500) * 45 * (0.5 + 0.5 * fbm(x * 0.004, z * 0.004, 3));
  return Math.max(-2, h) * k;
}

type Seg = [number, number, number, number, number];     // x0 z0 x1 z1 ancho
function distSeg(x: number, z: number, x0: number, z0: number, x1: number, z1: number) {
  const dx = x1 - x0, dz = z1 - z0, L2 = dx * dx + dz * dz || 1;
  const t = Math.max(0, Math.min(1, ((x - x0) * dx + (z - z0) * dz) / L2));
  return Math.hypot(x - (x0 + t * dx), z - (z0 + t * dz));
}
function dentroPoligono(x: number, z: number, P: number[][]) {
  let s = false;
  for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
    const [xi, zi] = P[i], [xj, zj] = P[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) s = !s;
  }
  return s;
}
function distPoligono(x: number, z: number, P: number[][]) {
  let d = Infinity;
  for (let i = 0, j = P.length - 1; i < P.length; j = i++) d = Math.min(d, distSeg(x, z, P[j][0], P[j][1], P[i][0], P[i][1]));
  return dentroPoligono(x, z, P) ? -d : d;
}
// alarga una polilínea por sus dos extremos
function prolongar(p: number[][], L: number) {
  if (p.length < 2) return p;
  const ext = (a: number[], b: number[]) => { const dx = a[0] - b[0], dz = a[1] - b[1], d = Math.hypot(dx, dz) || 1; return [a[0] + (dx / d) * L, a[1] + (dz / d) * L]; };
  return [ext(p[0], p[1]), ...p, ext(p[p.length - 1], p[p.length - 2])];
}
// quita de una polilínea lo que cae dentro de un círculo (las calles del lote ya están medidas en sitio.py)
function recortarCirculo(p: number[][], c: number[], R: number): number[][][] {
  const fuera = (q: number[]) => Math.hypot(q[0] - c[0], q[1] - c[1]) >= R;
  const corte = (a: number[], b: number[]) => {
    let lo = 0, hi = 1; const fa = fuera(a);
    for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; const q = [a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m]; if (fuera(q) === fa) lo = m; else hi = m; }
    const m = (lo + hi) / 2; return [a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m];
  };
  const out: number[][][] = []; let cur: number[][] = [];
  for (let i = 0; i < p.length; i++) {
    const q = p[i];
    if (fuera(q)) {
      if (i > 0 && !fuera(p[i - 1])) cur.push(corte(p[i - 1], q));
      cur.push(q);
    } else if (i > 0 && fuera(p[i - 1])) { cur.push(corte(p[i - 1], q)); if (cur.length > 1) out.push(cur); cur = []; }
  }
  if (cur.length > 1) out.push(cur);
  return out;
}
/** cinta de calle: 3 vértices por punto (orilla, eje, orilla), UV en baldosas de `tile` metros */
function cinta(p: number[][], ancho: number, tile: number, y: number) {
  const pos: number[] = [], uv: number[] = [], col: number[] = [], idx: number[] = [];
  let largo = 0;
  for (let i = 0; i < p.length; i++) {
    const a = p[Math.max(0, i - 1)], b = p[Math.min(p.length - 1, i + 1)];
    let dx = b[0] - a[0], dz = b[1] - a[1]; const L = Math.hypot(dx, dz) || 1; dx /= L; dz /= L;
    let k = 1;
    if (i > 0 && i < p.length - 1) {      // inglete limitado
      const d1x = p[i][0] - p[i - 1][0], d1z = p[i][1] - p[i - 1][1], l1 = Math.hypot(d1x, d1z) || 1;
      const cosm = (d1x / l1) * dx + (d1z / l1) * dz; k = 1 / Math.max(0.6, Math.sqrt((1 + cosm) / 2));
    }
    if (i > 0) largo += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
    const nx = -dz * k, nz = dx * k;
    for (const s of [-1, 0, 1]) {
      pos.push(p[i][0] + nx * s * ancho / 2, y, p[i][1] + nz * s * ancho / 2);
      uv.push((s * ancho / 2) / tile, largo / tile);
      const c = s === 0 ? 1 : 0.72; col.push(c, c, c);
    }
    if (i > 0) { const o = (i - 1) * 3; idx.push(o, o + 1, o + 3, o + 1, o + 4, o + 3, o + 1, o + 2, o + 4, o + 2, o + 5, o + 4); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}
/** techo a cuatro aguas o a dos aguas, huella 1×1 centrada, alto 1 */
function geoTecho(cuatroAguas: boolean) {
  const r = cuatroAguas ? 0.22 : 0.5;
  const v = [[-0.5, 0, -0.5], [0.5, 0, -0.5], [0.5, 0, 0.5], [-0.5, 0, 0.5], [-r, 1, 0], [r, 1, 0]];
  const f = cuatroAguas ? [[0, 5, 1], [0, 4, 5], [2, 5, 4], [2, 4, 3], [1, 5, 2], [3, 4, 0]] : [[0, 5, 1], [0, 4, 5], [2, 5, 4], [2, 4, 3], [1, 5, 2], [3, 4, 0]];
  const pos: number[] = [];
  for (const t of f) for (const i of t) pos.push(...v[i]);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
  return g;
}

export function crearMundo(scene: THREE.Scene, renderer: THREE.WebGLRenderer, movil: boolean, sunDir: THREE.Vector3, evitar: number[][] = [], cfg?: ConfigMundo, base = '/'): Mundo {
  const uTime = { value: 0 };
  const tex: Texturas = texturas(base, renderer);
  if (cfg) LOTE = cfg.lote;
  const C = cfg ? cfg.centro : [16, -40];
  const poli = cfg?.poligono ?? [[LOTE.x0, LOTE.z0], [LOTE.x1, LOTE.z0], [LOTE.x1, LOTE.z1], [LOTE.x0, LOTE.z1]];
  const grupo = new THREE.Group(); grupo.name = 'mundo'; scene.add(grupo);

  // ---------- terreno ----------
  const TS = 3200, SEG = movil ? 160 : 260;
  const tg = new THREE.PlaneGeometry(TS, TS, SEG, SEG); tg.rotateX(-Math.PI / 2);
  const pos = tg.attributes.position as THREE.BufferAttribute;
  const col = new Float32Array(pos.count * 3);
  const cBosque = new THREE.Color(0.62, 0.72, 0.58), cRoca = new THREE.Color(0.62, 0.64, 0.6);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) + C[0], z = pos.getZ(i) + C[1];
    const h = alturaTerreno(x, z);
    pos.setX(i, x); pos.setZ(i, z); pos.setY(i, h - 0.05);
    const n = fbm(x * 0.02, z * 0.02, 3);
    const c = new THREE.Color(0.92 + 0.16 * n, 0.95 + 0.1 * n, 0.88 + 0.14 * n);
    if (h > 40) c.lerp(cBosque, THREE.MathUtils.smoothstep(h, 40, 260));
    if (h > 500) c.lerp(cRoca, THREE.MathUtils.smoothstep(h, 500, 1200));
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
  }
  tg.setAttribute('color', new THREE.BufferAttribute(col, 3));
  tg.computeVertexNormals();
  const terreno = new THREE.Mesh(tg, materialCesped(tex));
  terreno.receiveShadow = true; terreno.name = 'terreno'; grupo.add(terreno);

  // ---------- Volcán Barú y cordillera de Talamanca: silueta azulada al norte-noroeste ----------
  {
    const g = new THREE.BufferGeometry(); const pts: number[] = []; const col: number[] = [];
    const R = 4300, N = 220;
    const perfil = (a: number) => {            // a: ángulo desde el norte (rad), negativo = oeste
      const barú = 520 * Math.exp(-(((a + 0.42) / 0.16) ** 2));
      const cord = 170 + 90 * fbm(a * 6 + 3, 1.7, 3) + 60 * Math.exp(-(((a + 0.1) / 0.5) ** 2));
      return Math.max(barú, cord) * THREE.MathUtils.smoothstep(Math.abs(a), 1.9, 1.1);
    };
    for (let i = 0; i < N; i++) {
      const a0 = -2 + (4 * i) / N, a1 = -2 + (4 * (i + 1)) / N;
      const p = (a: number, y: number) => [C[0] + Math.sin(a) * R, y, C[1] - Math.cos(a) * R];
      const q = [p(a0, -20), p(a1, -20), p(a1, perfil(a1)), p(a0, perfil(a0))];
      for (const k of [0, 1, 2, 0, 2, 3]) { pts.push(...q[k]); const t = q[k][1] / 520; col.push(0.55 + 0.1 * t, 0.62 + 0.1 * t, 0.72 + 0.08 * t); }
    }
    g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    const sierra = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, fog: false, side: THREE.DoubleSide, transparent: true, opacity: 0.85, depthWrite: false }));
    sierra.renderOrder = -1; grupo.add(sierra);
  }

  // ---------- calles ----------
  const segs: Seg[] = [];
  const RCORTE = 50;
  const matAsf = materialCalle(tex, 'asfalto'), matTie = materialCalle(tex, 'tierra');
  matAsf.polygonOffset = matTie.polygonOffset = true; matAsf.polygonOffsetFactor = matTie.polygonOffsetFactor = -1;
  let nCalle = 0;
  const calle = (p: number[][], ancho: number, tipo: 'asfalto' | 'tierra') => {
    const m = new THREE.Mesh(cinta(p, ancho, tipo === 'asfalto' ? 4 : 3, 0.012 + (nCalle++ % 7) * 0.003), tipo === 'asfalto' ? matAsf : matTie);
    m.receiveShadow = true; grupo.add(m);
    for (let i = 0; i < p.length - 1; i++) segs.push([p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], ancho]);
  };
  if (cfg) {
    // las dos calles del lote (medidas): C.A con asfalto y la calle de tierra
    cfg.calles.forEach((c, k) => calle(prolongar(c.puntos, RCORTE * 0.6), c.ancho, k === 1 ? 'tierra' : 'asfalto'));
    // el resto del barrio, de OpenStreetMap, sin lo que cae cerca del lote
    for (const c of (vecindario as any).calles as { tipo: 'asfalto' | 'tierra'; ancho: number; puntos: number[][] }[])
      for (const tramo of recortarCirculo(c.puntos, C, RCORTE)) calle(tramo, c.ancho, c.tipo);
  }
  const cercaCalle = (x: number, z: number, m: number) => segs.some(([x0, z0, x1, z1, w]) => distSeg(x, z, x0, z0, x1, z1) < w / 2 + m);
  const enLote = (x: number, z: number, m = 0) => distPoligono(x, z, poli) < m;
  const cercaEvitar = (x: number, z: number, r: number) => evitar.some(([ex, ez]) => Math.hypot(ex - x, ez - z) < r);

  // ---------- casas vecinas ----------
  type Casa = { x: number; z: number; w: number; d: number; h: number; rot: number; techo: number };
  const casas: Casa[] = [];
  const libreCasa = (x: number, z: number, w: number, d: number) => {
    const r = Math.max(w, d) * 0.5;
    if (Math.hypot(x - C[0], z - C[1]) > 330) return false;
    if (enLote(x, z, r + 4) || cercaEvitar(x, z, r + 5)) return false;
    if (segs.some(([x0, z0, x1, z1, a]) => distSeg(x, z, x0, z0, x1, z1) < a / 2 + r * 0.85 + 0.8)) return false;
    return !casas.some((c) => Math.hypot(c.x - x, c.z - z) < (Math.max(c.w, c.d) + Math.max(w, d)) * 0.5 + 1.5);
  };
  // edificios mapeados en OSM: rectángulo de área mínima
  const tanques: number[][] = [];
  for (const P of (vecindario as any).edificios as number[][][]) {
    const pts = P.slice(0, -1);
    const cx = pts.reduce((s, q) => s + q[0], 0) / pts.length, cz = pts.reduce((s, q) => s + q[1], 0) / pts.length;
    if (pts.length > 12) { tanques.push([cx, cz, pts.reduce((s, q) => s + Math.hypot(q[0] - cx, q[1] - cz), 0) / pts.length]); continue; }
    let best = { a: Infinity, rot: 0, w: 0, d: 0, ox: 0, oz: 0 };
    for (let i = 0; i < pts.length; i++) {
      const q = pts[(i + 1) % pts.length], p0 = pts[i]; const ang = Math.atan2(q[1] - p0[1], q[0] - p0[0]);
      const ca = Math.cos(-ang), sa = Math.sin(-ang);
      const xs = pts.map((t) => (t[0] - cx) * ca - (t[1] - cz) * sa), zs = pts.map((t) => (t[0] - cx) * sa + (t[1] - cz) * ca);
      const w = Math.max(...xs) - Math.min(...xs), d = Math.max(...zs) - Math.min(...zs);
      if (w * d < best.a) best = { a: w * d, rot: ang, w, d, ox: (Math.max(...xs) + Math.min(...xs)) / 2, oz: (Math.max(...zs) + Math.min(...zs)) / 2 };
    }
    const x = cx + best.ox * Math.cos(best.rot) - best.oz * Math.sin(best.rot), z = cz + best.ox * Math.sin(best.rot) + best.oz * Math.cos(best.rot);
    casas.push({ x, z, w: best.w, d: best.d, h: best.w * best.d > 300 ? 4.6 : 3.0 + rnd() * 0.6, rot: -best.rot, techo: rnd() < 0.5 ? 0 : 1 });
  }
  // casas a lo largo de las calles, mirando a la calle
  if (cfg) for (const [x0, z0, x1, z1, a] of segs.slice()) {
    const L = Math.hypot(x1 - x0, z1 - z0); if (L < 6) continue;
    const ux = (x1 - x0) / L, uz = (z1 - z0) / L;
    for (const lado of [-1, 1]) {
      let t = rnd() * 6;
      while (t < L - 4) {
        const w = 8 + rnd() * 5, d = 7 + rnd() * 4, ret = 3 + rnd() * 4;
        const off = a / 2 + ret + d / 2;
        const x = x0 + ux * (t + w / 2) - uz * off * lado, z = z0 + uz * (t + w / 2) + ux * off * lado;
        if (rnd() < 0.7 && libreCasa(x, z, w, d)) {
          casas.push({ x, z, w, d, h: rnd() < 0.14 ? 5.9 + rnd() * 0.3 : 2.95 + rnd() * 0.4, rot: angFrente(ux, uz, lado), techo: rnd() < 0.55 ? 0 : 1 });   // +z local mira a la calle
        }
        t += w + 4 + rnd() * 9;
      }
    }
  }
  function angFrente(ux: number, uz: number, lado: number) {
    // vector hacia la calle (en el plano xz) = -lado * normal izquierda; rotation.y = θ hace que +z local apunte a (sin θ, cos θ)
    const nx = uz * lado, nz = -ux * lado;
    return Math.atan2(nx, nz);
  }
  {
    const n = casas.length;
    const gMuro = new THREE.BoxGeometry(1, 1, 1); gMuro.translate(0, 0.5, 0);
    const matMuro = new THREE.MeshStandardMaterial({ roughness: 0.92 });
    detallar(matMuro, tex, { ...ESTUCO, ventanas: true, sucio: 0.28 });
    const mMuros = new THREE.InstancedMesh(gMuro, matMuro, n);
    const techos = [new THREE.InstancedMesh(geoTecho(true), new THREE.MeshStandardMaterial({ roughness: 0.62, metalness: 0.3 }), n),
      new THREE.InstancedMesh(geoTecho(false), new THREE.MeshStandardMaterial({ roughness: 0.62, metalness: 0.3, side: THREE.DoubleSide }), n)];
    techos.forEach((t) => detallar(t.material as THREE.MeshStandardMaterial, tex, LAMINA));
    const cuenta = [0, 0];
    const paleta = ['#f1e7cf', '#e9d6a4', '#f4f1ea', '#d9c7a3', '#eedcd0', '#cfe0d6', '#e4d0b5', '#f0d8a8', '#d6dde6'];
    const pTecho = ['#8d4a33', '#9a5236', '#a6a7a2', '#8e9091', '#7a4433', '#b2b3ad', '#5f7363', '#a0543a'];
    const o = new THREE.Object3D();
    const cercas: THREE.Matrix4[] = []; const cColores: THREE.Color[] = [];
    casas.forEach((c, i) => {
      o.position.set(c.x, 0, c.z); o.rotation.set(0, c.rot, 0); o.scale.set(c.w, c.h, c.d); o.updateMatrix();
      mMuros.setMatrixAt(i, o.matrix); mMuros.setColorAt(i, new THREE.Color(paleta[Math.floor(rnd() * paleta.length)]));
      const k = c.techo; const j = cuenta[k]++;
      o.position.y = c.h; o.scale.set(c.w + 1.1, 1.1 + rnd() * 0.5, c.d + 1.1); o.updateMatrix();
      techos[k].setMatrixAt(j, o.matrix); techos[k].setColorAt(j, new THREE.Color(pTecho[Math.floor(rnd() * pTecho.length)]));
      // muro de cerca al frente (bloque con reja) en muchas casas
      if (rnd() < 0.6 && c.w * c.d < 260) {
        const dist = c.d / 2 + 2.2;
        o.position.set(c.x + Math.sin(c.rot) * dist, 0, c.z + Math.cos(c.rot) * dist); o.rotation.set(0, c.rot, 0);
        o.scale.set(c.w + 3 + rnd() * 3, 1.1 + rnd() * 0.7, 0.18); o.updateMatrix(); cercas.push(o.matrix.clone());
        cColores.push(new THREE.Color(paleta[Math.floor(rnd() * paleta.length)]));
      }
    });
    techos.forEach((t, k) => { t.count = cuenta[k]; t.castShadow = true; t.receiveShadow = true; grupo.add(t); });
    mMuros.castShadow = mMuros.receiveShadow = true; grupo.add(mMuros);
    if (cercas.length) {
      const matCerca = new THREE.MeshStandardMaterial({ roughness: 0.92 }); detallar(matCerca, tex, ESTUCO);
      const mc = new THREE.InstancedMesh(gMuro, matCerca, cercas.length);
      cercas.forEach((m, i) => { mc.setMatrixAt(i, m); mc.setColorAt(i, cColores[i]); });
      mc.castShadow = mc.receiveShadow = true; grupo.add(mc);
    }
    if (tanques.length) {
      const g = new THREE.CylinderGeometry(1, 1, 1, 40); g.translate(0, 0.5, 0);
      const mt = new THREE.MeshStandardMaterial({ color: '#b9bcb8', roughness: 0.6, metalness: 0.4 }); detallar(mt, tex, { ...LAMINA, onda: { paso: 0.6, eje: [0, 1, 0] } });
      const it = new THREE.InstancedMesh(g, mt, tanques.length);
      tanques.forEach(([x, z, r], i) => { o.position.set(x, 0, z); o.rotation.set(0, 0, 0); o.scale.set(r, 9, r); o.updateMatrix(); it.setMatrixAt(i, o.matrix); });
      it.castShadow = it.receiveShadow = true; grupo.add(it);
    }
  }
  const cercaCasa = (x: number, z: number, m: number) => casas.some((c) => Math.hypot(c.x - x, c.z - z) < Math.max(c.w, c.d) * 0.6 + m);

  // ---------- vegetación ----------
  const plantas: Vegetal[] = [];
  const add = (especie: Especie, x: number, z: number, alto: number) => plantas.push({ especie, x, y: enLote(x, z, 2) ? 0 : alturaTerreno(x, z), z, alto });
  const frondosa = (h: number): Especie => (h < 5.2 ? 'joven' : rnd() < 0.55 ? 'mango' : 'abierto');
  if (cfg) {
    // los del lote puestos al azar se quitan si tapan la ruta de la portada o una vista fija; los de las fotos se quedan
    for (const [x, z, h] of cfg.arboles) if (!cercaEvitar(x, z, 9)) add(frondosa(h), x, z, h);
    for (const [x, z, h] of cfg.palmas) if (!cercaEvitar(x, z, 9)) add('coco', x, z, h * 1.05);
    for (const v of cfg.vegetacion ?? []) add(v[0] as Especie, v[1] as number, v[2] as number, v[3] as number);
  }
  // patios: árboles y palmas detrás y al lado de las casas, matas al frente
  for (const c of casas) {
    if (Math.hypot(c.x - C[0], c.z - C[1]) > 300) continue;
    const s = Math.sin(c.rot), co = Math.cos(c.rot);
    const n = rnd() < 0.75 ? 1 + Math.floor(rnd() * 2.2) : 0;
    for (let k = 0; k < n; k++) {
      const atras = -(c.d / 2 + 2.5 + rnd() * 4), lat = (rnd() - 0.5) * (c.w + 4);
      const x = c.x + s * atras + co * lat, z = c.z + co * atras - s * lat;
      if (cercaCalle(x, z, 2) || enLote(x, z, 3) || cercaEvitar(x, z, 8)) continue;
      const r = rnd();
      add(r < 0.3 ? 'coco' : r < 0.4 ? 'joven' : frondosa(6 + rnd() * 4), x, z, r < 0.3 ? 7 + rnd() * 5 : 5 + rnd() * 4);
    }
    if (rnd() < 0.5) {
      const ad = c.d / 2 + 1.2, lat = (rnd() - 0.5) * c.w;
      const x = c.x + s * ad + co * lat, z = c.z + co * ad - s * lat;
      if (!cercaCalle(x, z, 0.8)) add('mata', x, z, 1.2 + rnd() * 0.8);
    }
  }
  // arboleda: densa donde no hay calles ni casas (el sur del lote es monte en el satélite), con claros
  // cerca (< 150 m) con especies completas; más lejos, árboles de tarjetas grandes (menos geometría)
  const nArb = movil ? 3500 : 9500;
  for (let i = 0; i < nArb; i++) {
    const a = rnd() * Math.PI * 2, r = 12 + Math.sqrt(rnd()) * 330;
    const x = C[0] + Math.cos(a) * r, z = C[1] + Math.sin(a) * r;
    const dens = fbm(x * 0.013 + 5, z * 0.013 - 2, 3);
    if (rnd() > (dens > 0.42 ? 0.95 : 0.35)) continue;
    if (enLote(x, z, 3) || cercaCalle(x, z, 3.5) || cercaCasa(x, z, 2.5) || cercaEvitar(x, z, 10)) continue;
    const t = rnd();
    if (r > 150 && t >= 0.14) { add('lejano', x, z, 7 + rnd() * 7); continue; }
    add(t < 0.14 ? 'coco' : t < 0.24 ? 'joven' : frondosa(7 + rnd() * 5), x, z, t < 0.14 ? 8 + rnd() * 6 : 6 + rnd() * 6);
  }
  // árboles a lo largo de la quebrada
  for (const A of (vecindario as any).agua as number[][][]) for (let i = 0; i < A.length - 1; i++) {
    const L = Math.hypot(A[i + 1][0] - A[i][0], A[i + 1][1] - A[i][1]);
    for (let t = 0; t < L; t += 7) {
      const f = t / L, x = A[i][0] + (A[i + 1][0] - A[i][0]) * f + (rnd() - 0.5) * 14, z = A[i][1] + (A[i + 1][1] - A[i][1]) * f + (rnd() - 0.5) * 14;
      if (!cercaCalle(x, z, 3) && !cercaCasa(x, z, 2)) add(frondosa(9), x, z, 8 + rnd() * 6);
    }
  }
  // bosque lejano: tarjetas grandes, sin sombra
  const nLej = movil ? 900 : 2400;
  for (let i = 0; i < nLej; i++) {
    const a = rnd() * Math.PI * 2, r = 340 + rnd() * 900;
    const x = C[0] + Math.cos(a) * r, z = C[1] + Math.sin(a) * r;
    if (fbm(x * 0.01, z * 0.01, 2) < 0.42) continue;
    add('lejano', x, z, 8 + rnd() * 9);
  }
  plantar(grupo, plantas, tex, uTime, !movil);

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
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: texNube, transparent: true, opacity: 0.85, depthWrite: false, color: '#fff6ee' }));
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

  function update(t: number, dt: number) {
    uTime.value = t;
    for (const n of nubeDatos) { n.s.position.x += n.v * dt * 2; if (n.s.position.x > 800) n.s.position.x = -800; }
    const o = new THREE.Object3D();
    aveDatos.forEach((a, i) => {
      const ang = t * 0.12 * a.s + a.off;
      o.position.set(C[0] + Math.cos(ang) * a.r + Math.sin(t * 0.5 + a.ph) * 6, a.h + Math.sin(t * 0.7 + a.ph) * 3, C[1] + Math.sin(ang) * a.r * 0.8);
      o.rotation.set(0, -ang + Math.PI / 2, Math.sin(t * 9 + a.ph) * 0.55);
      o.scale.setScalar(0.7); o.updateMatrix(); aves.setMatrixAt(i, o.matrix);
    });
    aves.instanceMatrix.needsUpdate = true;
    for (const w of agua) (w.material as THREE.ShaderMaterial).uniforms.time.value = t * 0.6;
  }

  return { update, agua, crearAgua, escenaNubes } as Mundo & { crearAgua: typeof crearAgua };
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
