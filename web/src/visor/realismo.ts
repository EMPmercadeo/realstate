/*
  Realismo (ronda 3): texturas repetibles generadas por blender/texturas_web.py, aplicadas en espacio de
  mundo (triplanar) para no depender de las UV del modelo, relieve por derivadas de pantalla, mugre en la
  base de los muros, láminas onduladas procedurales y el césped del terreno con dos escalas y manchas secas.
*/
import * as THREE from 'three';

export interface Texturas {
  cesped: THREE.Texture; seco: THREE.Texture; tierra: THREE.Texture; asfalto: THREE.Texture;
  relieve: THREE.Texture; hojas: THREE.Texture; hojasCipres: THREE.Texture; fronda: THREE.Texture; corteza: THREE.Texture; banano: THREE.Texture;
}

let _tex: Texturas | null = null;
export function texturas(base: string, renderer: THREE.WebGLRenderer): Texturas {
  if (_tex) return _tex;
  const L = new THREE.TextureLoader();
  const an = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const t = (f: string, color = true, rep = true) => {
    const x = L.load(`${base}tex/${f}`);
    if (color) x.colorSpace = THREE.SRGBColorSpace;
    if (rep) x.wrapS = x.wrapT = THREE.RepeatWrapping;
    x.anisotropy = an;
    return x;
  };
  _tex = {
    cesped: t('cesped.jpg'), seco: t('cesped_seco.jpg'), tierra: t('tierra.jpg'), asfalto: t('asfalto.jpg'),
    relieve: t('relieve.png', false), hojas: t('hojas.png', true, false), hojasCipres: t('hojas_cipres.png', true, false),
    fronda: t('fronda.png', true, false), corteza: t('corteza.jpg'), banano: t('hoja_banano.png', true, false),
  };
  return _tex;
}

// ---------------------------------------------------------------- piezas de shader comunes
const VERT_DECL = `
varying vec3 vRWPos; varying vec3 vRWNrm;`;
const VERT_CALC = `
  {
    vec4 rwp = vec4(transformed, 1.0);
    vec3 rwn = objectNormal;
    #ifdef USE_INSTANCING
      rwp = instanceMatrix * rwp; rwn = mat3(instanceMatrix) * rwn;
    #endif
    rwp = modelMatrix * rwp;
    vRWPos = rwp.xyz; vRWNrm = normalize(mat3(modelMatrix) * rwn);
  }`;
const FRAG_DECL = `
varying vec3 vRWPos; varying vec3 vRWNrm;
vec3 rPerturb(vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDir) {
  vec3 vSigmaX = normalize(dFdx(surf_pos)); vec3 vSigmaY = normalize(dFdy(surf_pos));
  vec3 R1 = cross(vSigmaY, surf_norm); vec3 R2 = cross(surf_norm, vSigmaX);
  float fDet = dot(vSigmaX, R1) * faceDir;
  vec3 vGrad = sign(fDet) * (dHdxy.x * R1 + dHdxy.y * R2);
  return normalize(abs(fDet) * surf_norm - vGrad);
}
vec4 rTri(sampler2D t, vec3 p, vec3 w) { return texture2D(t, p.zy) * w.x + texture2D(t, p.xz) * w.y + texture2D(t, p.xy) * w.z; }`;

function parchear(mat: THREE.Material, clave: string, fn: (sh: THREE.WebGLProgramParametersWithUniforms) => void) {
  const previo = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    previo?.call(mat, sh, r);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>' + VERT_DECL)
      .replace('#include <project_vertex>', '#include <project_vertex>' + VERT_CALC);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>' + FRAG_DECL);
    fn(sh);
  };
  const k0 = mat.customProgramCacheKey?.bind(mat);
  mat.customProgramCacheKey = () => (k0 ? k0() : '') + '|' + clave;
  mat.needsUpdate = true;
}

// ---------------------------------------------------------------- muros, concreto, láminas
export interface Detalle {
  canal: [number, number, number, number];   // pesos de relieve.png: R estuco, G concreto, B mancha, A poros
  escala: number;          // repeticiones por metro
  color: number;           // amplitud de la variación de color del relieve
  mancha: number;          // manchas grandes (humedad, sol)
  relieve: number;         // fuerza del relieve
  lejos?: number;          // distancia a la que se apaga el relieve
  sucio?: number;          // oscurecer la base de los muros (0 = no)
  onda?: { paso: number; eje: [number, number, number]; teja?: number };   // lámina ondulada / teja
  ventanas?: boolean;      // casas vecinas (InstancedMesh de una caja 1×1×1 apoyada en y = 0): ventanas y puerta
}

export function detallar(mat: THREE.MeshStandardMaterial, tex: Texturas, d: Detalle) {
  const u = {
    uRel: { value: tex.relieve }, uCanal: { value: new THREE.Vector4(...d.canal) }, uEsc: { value: d.escala },
    uColAmp: { value: d.color }, uMan: { value: d.mancha }, uBump: { value: d.relieve }, uLejos: { value: d.lejos ?? 40 },
    uSucio: { value: d.sucio ?? 0 }, uPaso: { value: d.onda?.paso ?? 0.2 }, uEje: { value: new THREE.Vector3(...(d.onda?.eje ?? [1, 0, 0])) },
    uTeja: { value: d.onda?.teja ?? 0 },
  };
  const onda = !!d.onda, ven = !!d.ventanas;
  parchear(mat, `det${onda ? 'O' : ''}${ven ? 'V' : ''}`, (sh) => {
    Object.assign(sh.uniforms, u);
    if (ven) {
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vLoc; varying vec3 vLocN; varying vec3 vEsc;')
        .replace('#include <project_vertex>', `#include <project_vertex>
  #ifdef USE_INSTANCING
    vEsc = vec3(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz), length(instanceMatrix[2].xyz));
  #else
    vEsc = vec3(1.0);
  #endif
  vLoc = position * vEsc; vLocN = normal;`);
    }
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D uRel; uniform vec4 uCanal; uniform float uEsc, uColAmp, uMan, uBump, uLejos, uSucio, uPaso, uTeja; uniform vec3 uEje;
float rAlto; float rVidrio = 0.0;${ven ? '\nvarying vec3 vLoc; varying vec3 vLocN; varying vec3 vEsc;' : ''}`)
      .replace('#include <map_fragment>', `#include <map_fragment>
  {
    vec3 bw = pow(abs(vRWNrm), vec3(4.0)); bw /= (bw.x + bw.y + bw.z);
    vec4 r = rTri(uRel, vRWPos * uEsc, bw);
    float h = dot(r, uCanal) / max(1e-3, uCanal.x + uCanal.y + uCanal.z + uCanal.w);
    float m = rTri(uRel, vRWPos * 0.09, bw).b;
    ${onda ? `
    vec3 n = normalize(vRWNrm);
    vec3 tg = cross(vec3(0.0, 1.0, 0.0), n);
    tg = length(tg) < 0.25 ? uEje : normalize(tg);
    float s = dot(vRWPos, tg) / uPaso;
    float hc = 0.5 + 0.5 * cos(6.2832 * s);
    if (uTeja > 0.0) {
      vec3 dn = normalize(cross(n, tg));
      float v = fract(dot(vRWPos, dn) / uTeja);
      hc = hc * (0.55 + 0.45 * smoothstep(0.0, 0.85, v)) - 0.35 * smoothstep(0.85, 1.0, v);
    }
    h = mix(h, hc, 0.85);` : ''}
    rAlto = h;
    diffuseColor.rgb *= 1.0 + (h - 0.5) * uColAmp + (m - 0.5) * uMan;
    float vert = 1.0 - bw.y;
    diffuseColor.rgb *= mix(1.0, mix(1.0 - uSucio, 1.0, smoothstep(0.02, 0.55, vRWPos.y)), vert);
    ${ven ? `
    if (abs(vLocN.y) < 0.5) {
      bool frente = vLocN.z > 0.5;
      float along = abs(vLocN.x) > 0.5 ? vLoc.z : vLoc.x;
      float medio = (abs(vLocN.x) > 0.5 ? vEsc.z : vEsc.x) * 0.5;
      float cel = 2.9; float piso = floor(vLoc.y / 2.9);
      float y = vLoc.y - piso * 2.9;
      if (piso >= floor(vEsc.y / 2.9)) y = -1.0;
      float f = fract(along / cel + 0.5);
      if (frente && piso < 0.5 && abs(along) < 0.5 && y < 2.12) {
        diffuseColor.rgb = vec3(0.30, 0.20, 0.13) * (0.9 + 0.2 * h);
      } else if (f > 0.3 && f < 0.7 && y > 0.95 && y < 2.12 && abs(along) < medio - 0.6 && !(frente && piso < 0.5 && abs(along) < 1.4)) {
        float fx = min(f - 0.3, 0.7 - f) * cel, fy = min(y - 0.95, 2.12 - y);
        if (min(fx, fy) < 0.06) diffuseColor.rgb = vec3(0.82, 0.82, 0.80);
        else {
          float rj = max(step(0.9, fract(along / 0.13)), step(0.88, fract(y / 0.17)));
          diffuseColor.rgb = mix(vec3(0.05, 0.06, 0.07), vec3(0.015), rj);
          rVidrio = 1.0 - rj;
        }
      }
    }` : ''}
  }`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
  roughnessFactor = mix(roughnessFactor, 0.12, rVidrio);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  {
    float f = uBump * (1.0 - smoothstep(uLejos * 0.4, uLejos, length(vViewPosition)));
    if (f > 0.0) normal = rPerturb(-vViewPosition, normal, vec2(dFdx(rAlto), dFdy(rAlto)) * f, faceDirection);
  }`);
  });
}

// Clasificación de los materiales del modelo exportado por Blender (w_n_*, w_pintura_*, …)
export const ESTUCO: Detalle = { canal: [1, 0, 0, 0.35], escala: 1.1, color: 0.10, mancha: 0.10, relieve: 0.9, sucio: 0.22, lejos: 30 };
const CONCRETO: Detalle = { canal: [0, 1, 0, 0.6], escala: 0.7, color: 0.22, mancha: 0.18, relieve: 0.8, sucio: 0.12, lejos: 30 };
const PIEDRA: Detalle = { canal: [0.3, 1, 0, 0.3], escala: 1.6, color: 0.35, mancha: 0.12, relieve: 1.6, lejos: 25 };
export const LAMINA: Detalle = { canal: [0, 0.4, 0, 0.6], escala: 0.6, color: 0.10, mancha: 0.16, relieve: 1.4, lejos: 45, onda: { paso: 0.19, eje: [1, 0, 0] } };
export const TEJA: Detalle = { canal: [0, 0.5, 0, 0.5], escala: 0.8, color: 0.14, mancha: 0.20, relieve: 1.6, lejos: 45, onda: { paso: 0.24, eje: [1, 0, 0], teja: 0.36 } };
const TELA: Detalle = { canal: [0, 0, 0, 1], escala: 3.0, color: 0.06, mancha: 0.08, relieve: 0.4, lejos: 12 };

export function clasificar(nombre: string): Detalle | null {
  const n = nombre.toLowerCase();
  if (/vidrio|led|espejo|agua|cromo|inox|pantalla|aluminio|acero|metal_|plastico|porcelana|lienzo|color_|pelota|fruta|piso_|azulejo|cielo_ret|bloque_vidrio|granito|laminado/.test(n)) return null;
  if (/cubierta_casa/.test(n)) return TEJA;
  if (/cubierta|remate_lamina/.test(n)) return LAMINA;
  if (/toldo/.test(n)) return TELA;
  if (/piedra/.test(n)) return PIEDRA;
  if (/concreto|murete|rampa|grava|baldosa|banda|bloque/.test(n)) return CONCRETO;
  if (/muro|pintura|blanco|amarill|pilar|cielo|alero|rojo_interior|azul_accesible|verde_borde/.test(n)) return ESTUCO;
  return null;
}

export function aplicarAlModelo(raiz: THREE.Object3D, tex: Texturas) {
  const hechos = new Set<THREE.Material>();
  raiz.traverse((o: any) => {
    if (!o.isMesh) return;
    const mats: THREE.Material[] = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (hechos.has(m) || !(m as any).isMeshStandardMaterial) continue;
      hechos.add(m);
      const d = clasificar(m.name || '');
      if (d) detallar(m as THREE.MeshStandardMaterial, tex, d);
    }
  });
}

// ---------------------------------------------------------------- terreno con césped
export function materialCesped(tex: Texturas) {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, metalness: 0 });
  parchear(mat, 'cesped', (sh) => {
    sh.uniforms.tCes = { value: tex.cesped }; sh.uniforms.tSeco = { value: tex.seco }; sh.uniforms.tTierra = { value: tex.tierra };
    sh.uniforms.uRel = { value: tex.relieve };
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D tCes, tSeco, tTierra, uRel; float rAlto;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
  {
    vec2 p = vRWPos.xz;
    vec3 g1 = texture2D(tCes, p / 2.4).rgb;
    vec3 g2 = texture2D(tCes, mat2(0.8, -0.6, 0.6, 0.8) * p / 6.1).rgb;
    vec3 s1 = texture2D(tSeco, mat2(0.6, 0.8, -0.8, 0.6) * p / 3.3).rgb;
    // tres escalas giradas y sin múltiplos comunes para que de lejos no se vean franjas repetidas
    float mg = texture2D(uRel, mat2(0.92, -0.39, 0.39, 0.92) * p / 377.0).b * 0.45
             + texture2D(uRel, mat2(0.6, 0.8, -0.8, 0.6) * p / 113.0).b * 0.35
             + texture2D(uRel, p / 31.0).b * 0.2;
    float seco = smoothstep(0.48, 0.78, mg);
    vec3 g = mix(mix(g1, g2, 0.45), s1, seco * 0.75);
    float tierra = smoothstep(0.80, 0.93, texture2D(uRel, mat2(0.8, 0.6, -0.6, 0.8) * p / 61.0 + 0.37).b) * smoothstep(0.35, 0.6, mg) * 0.6;
    g = mix(g, texture2D(tTierra, p / 3.0).rgb * 0.8, tierra);
    rAlto = dot(g, vec3(0.3, 0.6, 0.1));
    diffuseColor.rgb = g * diffuseColor.rgb * 1.05;
  }`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
  {
    float f = 1.2 * (1.0 - smoothstep(6.0, 22.0, length(vViewPosition)));
    if (f > 0.0) normal = rPerturb(-vViewPosition, normal, vec2(dFdx(rAlto), dFdy(rAlto)) * f, faceDirection);
  }`);
  });
  return mat;
}

// ---------------------------------------------------------------- calles (UV en metros)
export function materialCalle(tex: Texturas, tipo: 'asfalto' | 'tierra') {
  const t = (tipo === 'asfalto' ? tex.asfalto : tex.tierra);
  const mat = new THREE.MeshStandardMaterial({ map: t, vertexColors: true, roughness: tipo === 'asfalto' ? 0.9 : 1, metalness: 0 });
  parchear(mat, 'calle' + tipo, (sh) => {
    sh.uniforms.uRel = { value: tex.relieve };
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D uRel;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
  { float m = texture2D(uRel, vRWPos.xz / 23.0).b; diffuseColor.rgb *= 0.86 + 0.28 * m; }`);
  });
  return mat;
}

// ---------------------------------------------------------------- follaje: normales de copa también por detrás
export function materialFollaje(map: THREE.Texture, color = '#ffffff', viento?: { uTime: { value: number }; fuerza: number }) {
  const mat = new THREE.MeshStandardMaterial({ map, color, alphaTest: 0.5, side: THREE.DoubleSide, roughness: 0.82, metalness: 0, vertexColors: true });
  mat.onBeforeCompile = (sh) => {
    if (viento) {
      sh.uniforms.uTime = viento.uTime; sh.uniforms.uWind = { value: viento.fuerza };
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nuniform float uTime; uniform float uWind;')
        .replace('#include <begin_vertex>', `#include <begin_vertex>
        {
          #ifdef USE_INSTANCING
            vec4 wp = instanceMatrix * vec4(position, 1.0);
          #else
            vec4 wp = vec4(position, 1.0);
          #endif
          float k = clamp(position.y / 7.0, 0.0, 1.0); k *= k;
          float ph = uTime * 1.2 + wp.x * 0.17 + wp.z * 0.13;
          float r = sin(uTime * 3.1 + position.x * 2.3 + position.z * 1.7) * 0.04;
          transformed.x += (sin(ph) * 0.22 + sin(ph * 2.7) * 0.07) * uWind * k + r * uWind;
          transformed.z += cos(ph * 0.8) * 0.16 * uWind * k;
        }`);
    }
    // alfa escalado por nivel de mip (si no, las hojas finas desaparecen de lejos con alphaTest)
    sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
      {
        vec2 tx = vMapUv * vec2(textureSize(map, 0));
        vec2 ddx = dFdx(tx), ddy = dFdy(tx);
        float lod = max(0.0, 0.5 * log2(max(dot(ddx, ddx), dot(ddy, ddy))));
        diffuseColor.a *= 1.0 + lod * 0.28;
      }`);
    // la cara de atrás de una tarjeta conserva la normal de la copa (si se invierte queda negra)
    sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>', `
      float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
      vec3 normal = normalize( vNormal );
      vec3 nonPerturbedNormal = normal;`);
  };
  mat.customProgramCacheKey = () => 'follaje' + (viento ? 'v' : '');
  return mat;
}
