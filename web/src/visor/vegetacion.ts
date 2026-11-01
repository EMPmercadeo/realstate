/*
  Vegetación con follaje de tarjetas (texturas con alfa de blender/texturas_web.py): árboles frondosos de
  tres formas, palmas (coco, navidad y fénix en macolla), cipreses columnares y pinos. Cada especie es
  una geometría a escala de referencia que luego se instancia (InstancedMesh) con su altura real.
  Las normales del follaje apuntan hacia afuera de la copa: así la luz la modela como un volumen.
*/
import * as THREE from 'three';
import { materialFollaje, type Texturas } from './realismo';

let seed = 11;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

class Acum {
  p: number[] = []; n: number[] = []; uv: number[] = []; c: number[] = [];
  tri(a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3, na: THREE.Vector3, nb: THREE.Vector3, nc: THREE.Vector3,
      ua: number[], ub: number[], uc: number[], ca: number, cb: number, cc: number) {
    this.p.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
    this.n.push(na.x, na.y, na.z, nb.x, nb.y, nb.z, nc.x, nc.y, nc.z);
    this.uv.push(...ua, ...ub, ...uc);
    this.c.push(ca, ca, ca, cb, cb, cb, cc, cc, cc);
  }
  quad(a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3, d: THREE.Vector3, n: THREE.Vector3[], uv: number[][], col: number[]) {
    this.tri(a, b, c, n[0], n[1], n[2], uv[0], uv[1], uv[2], col[0], col[1], col[2]);
    this.tri(a, c, d, n[0], n[2], n[3], uv[0], uv[2], uv[3], col[0], col[2], col[3]);
  }
  geo() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.computeBoundingSphere();
    return g;
  }
}

function dirAzar() {
  const u = rnd() * 2 - 1, a = rnd() * Math.PI * 2, s = Math.sqrt(1 - u * u);
  return V(Math.cos(a) * s, u, Math.sin(a) * s);
}

/** tarjetas de follaje dentro de un elipsoide (centro, radios) */
function copa(A: Acum, c: THREE.Vector3, r: THREE.Vector3, n: number, tam: [number, number], sombraBase = 0.45) {
  for (let i = 0; i < n; i++) {
    const d = dirAzar();
    if (d.y < -0.55) d.y *= 0.5;
    const k = 0.5 + 0.5 * Math.sqrt(rnd());
    const p = V(c.x + d.x * r.x * k, c.y + d.y * r.y * k, c.z + d.z * r.z * k);
    const s = tam[0] + rnd() * (tam[1] - tam[0]);
    // orientación: mezcla entre mirar hacia afuera y al azar
    const f = d.clone().lerp(dirAzar(), 0.6).normalize();
    const a = Math.abs(f.y) > 0.9 ? V(1, 0, 0) : V(0, 1, 0);
    const e1 = a.clone().cross(f).normalize(); const e2 = f.clone().cross(e1).normalize();
    const rot = rnd() * Math.PI * 2;
    const u = e1.clone().multiplyScalar(Math.cos(rot)).addScaledVector(e2, Math.sin(rot)).multiplyScalar(s / 2);
    const v = e2.clone().multiplyScalar(Math.cos(rot)).addScaledVector(e1, -Math.sin(rot)).multiplyScalar(s / 2);
    const q = [p.clone().sub(u).sub(v), p.clone().add(u).sub(v), p.clone().add(u).add(v), p.clone().sub(u).add(v)];
    const nrm = q.map((x) => V((x.x - c.x) / r.x, (x.y - c.y) / r.y + 0.35, (x.z - c.z) / r.z).normalize());
    // sombra interna: más oscuro abajo y hacia el centro
    const col = q.map((x) => {
      const h = THREE.MathUtils.clamp(((x.y - c.y) / r.y + 1) / 2, 0, 1);
      const o = THREE.MathUtils.clamp(Math.hypot((x.x - c.x) / r.x, (x.y - c.y) / r.y, (x.z - c.z) / r.z), 0, 1.2);
      return THREE.MathUtils.clamp(sombraBase + (1 - sombraBase) * (0.55 * h + 0.45 * o), 0.25, 1.05);
    });
    A.quad(q[0], q[1], q[2], q[3], nrm, [[0, 0], [1, 0], [1, 1], [0, 1]], col);
  }
}

/** cilindro (tronco o rama) de p0 a p1 con UV de corteza en metros */
function rama(A: Acum, p0: THREE.Vector3, p1: THREE.Vector3, r0: number, r1: number, seg = 7) {
  const d = p1.clone().sub(p0); const L = d.length(); d.normalize();
  const a = Math.abs(d.y) > 0.9 ? V(1, 0, 0) : V(0, 1, 0);
  const e1 = a.clone().cross(d).normalize(); const e2 = d.clone().cross(e1).normalize();
  for (let i = 0; i < seg; i++) {
    const t0 = (i / seg) * Math.PI * 2, t1 = ((i + 1) / seg) * Math.PI * 2;
    const n0 = e1.clone().multiplyScalar(Math.cos(t0)).addScaledVector(e2, Math.sin(t0));
    const n1 = e1.clone().multiplyScalar(Math.cos(t1)).addScaledVector(e2, Math.sin(t1));
    const a0 = p0.clone().addScaledVector(n0, r0), b0 = p0.clone().addScaledVector(n1, r0);
    const a1 = p1.clone().addScaledVector(n0, r1), b1 = p1.clone().addScaledVector(n1, r1);
    const u0 = i / seg * 2, u1 = (i + 1) / seg * 2, v1 = L / 1.4;
    A.quad(a0, b0, b1, a1, [n0, n1, n1, n0], [[u0, 0], [u1, 0], [u1, v1], [u0, v1]], [0.8, 0.8, 1, 1]);
  }
}

export type Especie = 'mango' | 'abierto' | 'joven' | 'lejano' | 'mata' | 'coco' | 'navidad' | 'fenix' | 'cipres' | 'pino';
export const ALTO_REF: Record<Especie, number> = { mango: 8, abierto: 8, joven: 6, lejano: 9, mata: 1.6, coco: 9, navidad: 6, fenix: 4.2, cipres: 4.5, pino: 8 };

interface Partes { tronco?: THREE.BufferGeometry; follaje?: THREE.BufferGeometry; fronda?: THREE.BufferGeometry; tex: 'hojas' | 'cipres' }

function frondoso(e: Especie): Partes {
  const T = new Acum(), F = new Acum();
  const h = ALTO_REF[e];
  const cfg = {
    mango: { c: V(0, 5.1, 0), r: V(3.5, 2.7, 3.4), n: 96, tam: [1.5, 2.5] as [number, number], tr: 3.0, ramas: 5 },
    abierto: { c: V(0, 5.6, 0), r: V(4.3, 1.9, 4.0), n: 80, tam: [1.6, 2.6] as [number, number], tr: 4.0, ramas: 6 },
    joven: { c: V(0, 3.9, 0), r: V(2.1, 2.0, 2.1), n: 60, tam: [1.1, 1.8] as [number, number], tr: 2.2, ramas: 3 },
    lejano: { c: V(0, 5.8, 0), r: V(3.6, 3.0, 3.6), n: 24, tam: [3.0, 4.1] as [number, number], tr: 3.0, ramas: 0 },
    mata: { c: V(0, 0.8, 0), r: V(0.9, 0.75, 0.9), n: 16, tam: [0.6, 1.0] as [number, number], tr: 0, ramas: 0 },
  }[e as 'mango']!;
  if (cfg.tr > 0) {
    const top = V((rnd() - 0.5) * 0.3, cfg.tr, (rnd() - 0.5) * 0.3);
    rama(T, V(0, -0.2, 0), top, h * 0.035, h * 0.025, 8);
    for (let i = 0; i < cfg.ramas; i++) {
      const a = (i / cfg.ramas) * Math.PI * 2 + rnd() * 0.6;
      const p1 = V(Math.cos(a) * cfg.r.x * 0.6, cfg.c.y + (rnd() - 0.2) * cfg.r.y * 0.6, Math.sin(a) * cfg.r.z * 0.6);
      rama(T, top, p1, h * 0.02, h * 0.008, 5);
    }
  }
  copa(F, cfg.c, cfg.r, cfg.n, cfg.tam, e === 'lejano' ? 0.62 : 0.52);
  // un segundo lóbulo para que no sea una esfera perfecta
  if (e === 'mango' || e === 'abierto') copa(F, V(cfg.r.x * 0.45, cfg.c.y + 0.6, -cfg.r.z * 0.3), cfg.r.clone().multiplyScalar(0.55), Math.round(cfg.n * 0.28), cfg.tam);
  return { tronco: cfg.tr > 0 ? T.geo() : undefined, follaje: F.geo(), tex: 'hojas' };
}

function conifera(e: 'cipres' | 'pino'): Partes {
  const T = new Acum(), F = new Acum();
  const h = ALTO_REF[e];
  rama(T, V(0, -0.2, 0), V(0, h * 0.85, 0), e === 'pino' ? 0.22 : 0.12, 0.05, 7);
  const capas = e === 'pino' ? 9 : 12;
  for (let i = 0; i < capas; i++) {
    const t = i / (capas - 1);
    const y = e === 'pino' ? h * (0.3 + 0.68 * t) : h * (0.08 + 0.88 * t);
    const R = e === 'pino' ? (1 - t) * 2.6 + 0.35 : (Math.sin(Math.PI * (0.15 + 0.85 * t)) ** 0.6) * 0.95 * (1 - 0.55 * t) + 0.12;
    copa(F, V(0, y, 0), V(R, e === 'pino' ? 0.5 : h * 0.07, R), e === 'pino' ? 16 : 11, e === 'pino' ? [0.9, 1.5] : [0.55, 0.85], 0.5);
  }
  return { tronco: T.geo(), follaje: F.geo(), tex: 'cipres' };
}

/** frondas de palma: tiras con la textura de fronda, dobladas en V y arqueadas */
function frondas(A: Acum, top: THREE.Vector3, n: number, L: [number, number], W: number, sube: [number, number], cae: number, seca = 0.1) {
  for (let i = 0; i < n; i++) {
    const az = (i / n) * Math.PI * 2 + rnd() * 0.5;
    const dir = V(Math.cos(az), 0, Math.sin(az)); const lado = V(-dir.z, 0, dir.x);
    const Lf = L[0] + rnd() * (L[1] - L[0]);
    const el = sube[0] + rnd() * (sube[1] - sube[0]);
    const S = 6; let prev: THREE.Vector3[] | null = null; let pv = 0;
    const c = rnd() < seca ? 0.55 : 1;
    for (let k = 0; k <= S; k++) {
      const t = k / S;
      // arco: sale con elevación `el` y cae con la gravedad
      const x = Lf * t * Math.cos(el * (1 - t * 0.5)), y = Lf * t * Math.sin(el) - cae * Lf * t * t;
      const cen = top.clone().addScaledVector(dir, x).add(V(0, y, 0));
      const w = W * (0.35 + 0.65 * Math.sin(Math.PI * Math.min(1, 0.15 + t)));
      const pliegue = 0.18 * w;
      const fila = [cen.clone().addScaledVector(lado, -w / 2).add(V(0, pliegue, 0)), cen.clone(), cen.clone().addScaledVector(lado, w / 2).add(V(0, pliegue, 0))];
      if (prev) {
        const nu = V(0, 1, 0).addScaledVector(dir, 0.25).normalize();
        const col = c * (0.7 + 0.3 * t);
        A.quad(prev[0], prev[1], fila[1], fila[0], [nu, nu, nu, nu], [[0, pv], [0.5, pv], [0.5, t], [0, t]], [col, col, col, col]);
        A.quad(prev[1], prev[2], fila[2], fila[1], [nu, nu, nu, nu], [[0.5, pv], [1, pv], [1, t], [0.5, t]], [col, col, col, col]);
      }
      prev = fila; pv = t;
    }
  }
}

function palma(e: 'coco' | 'navidad' | 'fenix'): Partes {
  const T = new Acum(), R = new Acum();
  const h = ALTO_REF[e];
  if (e === 'fenix') {
    const nt = 4;
    for (let i = 0; i < nt; i++) {
      const a = (i / nt) * Math.PI * 2 + rnd() * 0.5; const ht = h * (0.65 + rnd() * 0.35);
      const top = V(Math.cos(a) * 0.5, ht, Math.sin(a) * 0.5);
      rama(T, V(0, -0.2, 0), top, 0.17, 0.14, 7);
      frondas(R, top, 24, [2.0, 2.8], 1.1, [0.35, 1.0], 0.45, 0.08);
    }
  } else {
    const lean = e === 'coco' ? 0.12 + rnd() * 0.1 : 0.03;
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 6; i++) { const t = i / 6; pts.push(V(Math.sin(t * 1.4) * lean * h, t * h, 0)); }
    for (let i = 0; i < 6; i++) rama(T, pts[i], pts[i + 1], (e === 'coco' ? 0.2 : 0.11) * (1 - i * 0.05), (e === 'coco' ? 0.2 : 0.11) * (1 - (i + 1) * 0.05), 8);
    const top = pts[6];
    if (e === 'navidad') {
      rama(T, top.clone().add(V(0, -0.9, 0)), top.clone().add(V(0, 0.1, 0)), 0.14, 0.1, 8);       // capitel verde
      frondas(R, top.clone().add(V(0, 0.05, 0)), 13, [1.8, 2.4], 1.3, [0.7, 1.15], 0.45, 0.05);
    } else {
      frondas(R, top, 15, [3.4, 4.4], 2.1, [0.25, 0.95], 0.55, 0.12);
    }
  }
  return { tronco: T.geo(), fronda: R.geo(), tex: 'hojas' };
}

export interface Vegetal { especie: Especie; x: number; y: number; z: number; alto: number; giro?: number; tinte?: THREE.Color }

/** crea las mallas instanciadas para una lista de plantas y las agrega al grupo */
export function plantar(grupo: THREE.Group, lista: Vegetal[], tex: Texturas, uTime: { value: number }, sombras: boolean) {
  const matTronco = new THREE.MeshStandardMaterial({ map: tex.corteza, color: '#b3a594', roughness: 0.95, vertexColors: true });
  const matPalma = new THREE.MeshStandardMaterial({ map: tex.corteza, color: '#c4b8a6', roughness: 0.9, vertexColors: true });
  const matHojas = materialFollaje(tex.hojas, '#ffffff', { uTime, fuerza: 0.6 });
  const matCipres = materialFollaje(tex.hojasCipres, '#f2f6ea', { uTime, fuerza: 0.25 });
  const matFronda = materialFollaje(tex.fronda, '#ffffff', { uTime, fuerza: 1.0 });
  const especies = [...new Set(lista.map((v) => v.especie))];
  const o = new THREE.Object3D();
  for (const e of especies) {
    const L = lista.filter((v) => v.especie === e);
    const partes: Partes = e === 'coco' || e === 'navidad' || e === 'fenix' ? palma(e) : e === 'cipres' || e === 'pino' ? conifera(e) : frondoso(e);
    const ms = L.map((v) => {
      const s = v.alto / ALTO_REF[e];
      o.position.set(v.x, v.y - 0.05, v.z); o.rotation.set(0, v.giro ?? rnd() * Math.PI * 2, 0);
      o.scale.set(s * (0.9 + rnd() * 0.2), s, s * (0.9 + rnd() * 0.2)); o.updateMatrix();
      return o.matrix.clone();
    });
    const lejano = e === 'lejano';
    const poner = (g: THREE.BufferGeometry | undefined, m: THREE.Material, tinte: boolean) => {
      if (!g) return;
      const im = new THREE.InstancedMesh(g, m, ms.length);
      ms.forEach((mx, i) => {
        im.setMatrixAt(i, mx);
        if (tinte) {
          const t = L[i].tinte ?? new THREE.Color().setHSL(0.2 + (rnd() - 0.5) * 0.1, 0.3 + rnd() * 0.3, 0.86 + rnd() * 0.1);
          im.setColorAt(i, t);
        }
      });
      im.castShadow = sombras && !lejano; im.receiveShadow = !lejano; im.frustumCulled = false;
      grupo.add(im);
    };
    const esPalma = e === 'coco' || e === 'navidad' || e === 'fenix';
    poner(partes.tronco, esPalma ? matPalma : matTronco, false);
    poner(partes.follaje, partes.tex === 'cipres' ? matCipres : matHojas, true);
    poner(partes.fronda, matFronda, true);
  }
}
