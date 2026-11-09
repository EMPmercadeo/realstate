import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { SMAAPass } from 'three/examples/jsm/postprocessing/SMAAPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { crearMundo, type ConfigMundo } from './mundo';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { texturas, aplicarAlModelo } from './realismo';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import vistasMaqueta from '../data/vistas.json';
import residencia from '../data/residencia.json';
import fotos from '../data/fotos.json';
import panoramas from '../data/panoramas.json';
import { abrir360, type Pano } from './pano360';
import { PARADAS_3D, VISTAS_EXTRA, RENDER_CUARTO, PLANOS_VISOR } from '../data/paradas';
import { GRIS as AV_GRIS, CASA as AV_CASA } from '../data/avances';
import { enlaceContacto } from '../data/sitio';

type Modo = 'orbita' | 'recorrido' | 'cine';
type Vista = { edificio: string | null; piso: number };
type Preset = { pos: number[]; target: number[]; ed: string | null; piso: number; nombre: string; detalle?: string };

const fantasma = document.createElement('div');
const $ = (sel: string) => (document.querySelector(sel) as HTMLElement) || fantasma;
type Foto = { nombre: string; antes: string; despues: string | null };
const F = fotos as Record<string, Foto>;
// fotos reales ("hoy → así quedará") ligadas a los cuartos del modelo amueblado
const FOTOS_RES: Record<string, Foto> = {
  'hosp@gris': { ...F['hospitalizacion@gris'], nombre: 'Personas encamadas' },
  'salon2@gris': { ...F['salon_2@gris'], nombre: 'Salón amarillo' },
  'galeria@gris': { ...F['refrigerios@gris'], nombre: 'Área recreativa y de coffee break' },
  'cocina@gris': { ...F['cocina@gris'], nombre: 'Cocineta del área de coffee break' },
  'terraza@gris': { ...F['terraza@gris'], nombre: 'Terraza al aire libre' },
  'bano_acc@gris': { ...F['bano_acc@gris'], nombre: 'Baño accesible para huéspedes o usuarios' },
  'comedor@amarilla': { ...F['comedor@amarilla'], nombre: 'Comedor y TV', despues: 'comedor' },
  'terapia@amarilla': { ...F['terapia@amarilla'], nombre: 'Terapia con familiares', despues: 'terapia' },
  'parqueo_casa': { nombre: 'Parqueo de grava de la casa', antes: 'parqueo-casa', despues: null },
};
const MOVIL = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || window.innerWidth < 820;
const RAPIDO = new URLSearchParams(location.search).has('rapido');   // capturas rápidas de depuración
const NIVEL = 3.25;

export interface OpcionesVisor { cine?: boolean; ruta?: { pos: number[]; target: number[] }[]; onCargado?: () => void; maqueta?: boolean; }

export function iniciarVisor(container: HTMLElement, opts: OpcionesVisor = {}) {
  const base = document.body.dataset.base || '/';
  const CINE = !!opts.cine;
  // Recorrido y portada usan el modelo amueblado (residencia.glb / residencia-exterior.glb);
  // { maqueta: true } vuelve a la maqueta anterior (escena.glb / exterior.glb).
  const RES = !opts.maqueta;
  const vistas: any = RES ? residencia : vistasMaqueta;
  const FOTOS: Record<string, Foto> = RES ? FOTOS_RES : F;
  const nivelDe = (ed: string | null) => (RES ? (vistas.edificios.find((e: any) => e.id === ed)?.nivel2 ?? 3.2) : NIVEL);
  const LIM = RES ? (residencia as any).limites as number[] : [-6, 36, -92, 8];
  // ruta de cámara para el modo cine (curvas suaves por los puntos dados)
  const rutaPos = new THREE.CatmullRomCurve3((opts.ruta || []).map((p) => new THREE.Vector3(...p.pos)), false, 'centripetal', 0.5);
  const rutaTgt = new THREE.CatmullRomCurve3((opts.ruta || []).map((p) => new THREE.Vector3(...p.target)), false, 'centripetal', 0.5);
  let uObjetivo = 0, uSuave = 0;
  const setProgreso = (u: number, instante = false) => { uObjetivo = THREE.MathUtils.clamp(u, 0, 1); if (instante) uSuave = uObjetivo; };

  // ---------- renderer ----------
  const renderer = new THREE.WebGLRenderer({ antialias: MOVIL, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, MOVIL ? 1.25 : 1.5));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = MOVIL ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
  // tono: ?tono=aces|agx|neutral para comparar (por defecto ACES)
  const TONO = new URLSearchParams(location.search).get('tono') || 'aces';
  renderer.toneMapping = TONO === 'aces' ? THREE.ACESFilmicToneMapping : TONO === 'neutral' ? THREE.NeutralToneMapping : THREE.AgXToneMapping;
  renderer.toneMappingExposure = TONO === 'aces' ? 0.76 : TONO === 'neutral' ? 0.62 : 0.95;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  labels.setSize(container.clientWidth, container.clientHeight);
  labels.domElement.className = 'etiquetas';
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
  // Celular vertical: con 45° de campo vertical solo se ven ~20° de ancho y los edificios quedaban cortados.
  // Se abre el lente según lo angosta que sea la pantalla (68° en un teléfono, 45° en pantallas horizontales).
  function ajustarLente() {
    const a = container.clientWidth / Math.max(1, container.clientHeight);
    camera.aspect = a;
    camera.fov = CINE || a >= 1 ? 45 : THREE.MathUtils.lerp(68, 45, THREE.MathUtils.clamp((a - 0.45) / 0.55, 0, 1));
    camera.updateProjectionMatrix();
  }
  ajustarLente();
  camera.position.set(110, 70, 30);

  // ---------- cielo + sol ----------
  const sky = new Sky();
  sky.scale.setScalar(2000);
  scene.add(sky);
  // hora dorada: sol bajo desde el este-sureste (ilumina las fachadas que dan a la calle)
  // en el modelo amueblado la fachada principal de la casa mira al noreste: sol de la mañana desde el este
  const sunDir = new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - (RES ? 30 : 26)), THREE.MathUtils.degToRad(RES ? 72 : 14));
  const u = sky.material.uniforms;
  u.sunPosition.value.copy(sunDir);
  u.turbidity.value = RES ? 2.2 : 2.8; u.rayleigh.value = RES ? 2.0 : 1.1; u.mieCoefficient.value = 0.004; u.mieDirectionalG.value = 0.85;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene(); skyScene.add(sky.clone());
  scene.environment = pmrem.fromScene(skyScene as any, 0.02).texture;
  scene.environmentIntensity = 0.45;
  // luz ambiente de una foto HDR real (Rooitou Park, Poly Haven, CC0) sin el sol: cielo arriba, césped abajo
  new RGBELoader().load(`${base}tex/entorno_parque.hdr`, (hdr) => {
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = pmrem.fromEquirectangular(hdr).texture;
    scene.environmentIntensity = 1.35;
    scene.environmentRotation.set(0, Math.PI * 0.6, 0);
    hdr.dispose();
  });
  scene.fog = new THREE.FogExp2(new THREE.Color(RES ? '#cdd6de' : '#d8d0c2'), MOVIL ? 0.0009 : 0.0006);
  // puntos que la vegetación y las casas no deben tapar: la ruta de la portada (densificada, solo donde va baja)
  // y las vistas fijas
  const evitar: number[][] = [];
  const R = opts.ruta || [];
  for (let i = 0; i < R.length; i++) {
    const a = R[i].pos, b = R[Math.min(R.length - 1, i + 1)].pos;
    const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[2] - a[2]) / 3));
    for (let k = 0; k < n; k++) {
      const f = k / n, y = a[1] + (b[1] - a[1]) * f;
      if (y < 18) evitar.push([a[0] + (b[0] - a[0]) * f, a[2] + (b[2] - a[2]) * f]);
    }
  }
  if (RES) for (const p of Object.values((residencia as any).presets) as any[]) evitar.push([p.pos[0], p.pos[2]]);
  const mundo = crearMundo(scene, renderer, MOVIL, sunDir, evitar,
    RES ? { ...(residencia as any).mundo, poligono: (residencia as any).lote } as ConfigMundo : undefined, base);

  const centro = RES ? new THREE.Vector3(...(residencia as any).centro as [number, number, number]) : new THREE.Vector3(15, 0, -42);
  const sun = new THREE.DirectionalLight(0xffd6a0, 3.2);
  sun.position.copy(sunDir).multiplyScalar(140).add(centro);
  sun.target.position.copy(centro);
  sun.castShadow = true;
  const sm = RAPIDO ? 1024 : MOVIL ? 2048 : 4096;
  sun.shadow.mapSize.set(sm, sm);
  sun.shadow.camera.left = -70; sun.shadow.camera.right = 70; sun.shadow.camera.top = 70; sun.shadow.camera.bottom = -70;
  sun.shadow.camera.near = 20; sun.shadow.camera.far = 320;
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xdfe6ff, 0x8a7a52, 0.28));
  // luz de relleno que acompaña a la cámara dentro de los edificios
  const relleno = new THREE.PointLight(0xfff4e0, 0, 14, 1.6);
  scene.add(relleno);

  // ---------- post ----------
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  let gtao: GTAOPass | null = null;
  if (!MOVIL && !RAPIDO) {
    gtao = new GTAOPass(scene, camera, container.clientWidth, container.clientHeight);
    gtao.output = GTAOPass.OUTPUT.Default;
    (gtao as any).updateGtaoMaterial({ radius: 0.6, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
    composer.addPass(gtao);
  }
  const bloom = MOVIL ? null : new UnrealBloomPass(new THREE.Vector2(container.clientWidth, container.clientHeight), 0.16, 0.6, 0.9);
  if (bloom) composer.addPass(bloom);
  composer.addPass(new OutputPass());
  // viñeta + grado cálido de película
  const grado = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uVig: { value: 0.42 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uVig; varying vec2 vUv;
      void main(){ vec4 c = texture2D(tDiffuse, vUv);
        vec2 d = vUv - 0.5; float v = 1.0 - smoothstep(0.35, 1.05, length(d) * 1.35) * uVig;
        c.rgb *= v;
        // sombras ligeramente frías, altas luces cálidas
        float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
        c.rgb = mix(c.rgb * vec3(0.96, 0.98, 1.05), c.rgb * vec3(1.04, 1.0, 0.94), smoothstep(0.2, 0.8, l));
        gl_FragColor = c; }`,
  });
  composer.addPass(grado);
  if (!MOVIL && !RAPIDO) composer.addPass(new SMAAPass());

  // ---------- estado ----------
  const objetos: THREE.Object3D[] = [];
  const muros: THREE.Mesh[] = [];
  const aguas: THREE.Mesh[] = [];
  const estado = { modo: 'orbita' as Modo, vista: { edificio: null as string | null, piso: 99 }, cargado: false, etiquetas: true, tour: false };
  // misma condición que el CSS del diseño para celular
  const esMovil = () => matchMedia('(max-width: 820px), (pointer: coarse) and (max-height: 500px)').matches;

  // ---------- presets de cámara ----------
  const presets: Record<string, Preset> = {};
  if (RES) {
    const P = (residencia as any).presets;
    presets['sitio'] = { ...P.sitio, ed: null, piso: 99, nombre: 'Vista general', detalle: 'Terreno de 2.500 m² con dos edificios' };
    presets['calle'] = { ...P.calle, ed: null, piso: 99, nombre: 'Desde la calle', detalle: 'Casa amarilla, frente a la C.A' };
    presets['gris-ext'] = { ...P['gris-ext'], ed: null, piso: 99, nombre: 'Edificio gris', detalle: 'Fachada hacia la calle de tierra' };
  } else {
    presets['sitio'] = { pos: [110, 70, 30], target: [15, 2, -42], ed: null, piso: 99, nombre: 'Vista general', detalle: 'Terreno de 2.500 m² con dos edificios' };
    presets['calle'] = { pos: [44, 1.9, -44], target: [14, 3, -61], ed: null, piso: 99, nombre: 'Desde la calle', detalle: 'Cerca perimetral, portón eléctrico y entrada circular' };
    presets['gris-ext'] = { pos: [42, 2.2, -2], target: [12, 4, -18], ed: null, piso: 99, nombre: 'Edificio de hospitalización', detalle: 'Dos niveles, terraza y acceso accesible' };
  }
  if (RES) for (const [id, v] of Object.entries(VISTAS_EXTRA)) presets[id] = { pos: v.pos, target: v.target, ed: null, piso: 99, nombre: v.nombre, detalle: v.detalle };
  for (const ex of (vistas as any).exteriores) presets[ex.id] = { pos: ex.cam, target: ex.centro, ed: null, piso: 99, nombre: ex.nombre };
  for (const ed of (vistas as any).edificios) {
    for (const p of ed.pisos) {
      const c = p.rooms.reduce((a: number[], r: any) => [a[0] + r.centro[0], a[1] + r.centro[1], a[2] + r.centro[2]], [0, 0, 0]).map((v: number) => v / p.rooms.length);
      presets[`${ed.id}-p${p.n}`] = { pos: [c[0] + 14, c[1] + 22, c[2] + 18], target: c, ed: ed.id, piso: p.n, nombre: `${ed.nombre} · ${p.nombre}`, detalle: 'Vista de planta sin techo' };
      for (const r of p.rooms) presets[r.id + '@' + ed.id] = { pos: r.cam, target: r.mira || r.centro, ed: ed.id, piso: p.n, nombre: r.nombre, detalle: r.camas ? `${r.camas} ${r.camas === 1 ? 'cama' : 'camas'}` : undefined };
    }
  }

  // ---------- carga ----------
  const loader = new GLTFLoader();
  const draco = new DRACOLoader(); draco.setDecoderPath(`${base}draco/`);
  loader.setDRACOLoader(draco);
  const pantalla = $('#pantalla-carga');
  const barra = $('#carga');
  const pct = $('#carga-pct');
  const archivo = RES ? (CINE ? 'residencia-exterior' : 'residencia') : (CINE ? 'exterior' : 'escena');
  loader.load(`${base}modelo/${archivo}.glb`, (gltf) => {
    gltf.scene.traverse((o: any) => {
      if (o.isMesh) {
        o.castShadow = true; o.receiveShadow = true;
        const m = o.material as THREE.MeshStandardMaterial;
        if (m) {
          m.envMapIntensity = 0.55;
          if (m.map && (m.name.includes('follaje') || m.name.includes('fronda') || m.name.includes('arbusto'))) {
            m.alphaTest = 0.45; m.transparent = false; m.side = THREE.DoubleSide; o.castShadow = true;
          } else if (m.transparent && m.opacity < 1) {
            m.depthWrite = false;
          }
          if (m.name.startsWith('vidrio')) { m.transparent = true; m.opacity = 0.5; m.roughness = 0.04; m.metalness = 0.1; m.envMapIntensity = 1.8; m.depthWrite = false; o.castShadow = false; }
          if (m.name.startsWith('led')) { m.emissiveIntensity = 1.6; }
          if (m.name.startsWith('agua')) { m.transparent = true; m.opacity = 0.75; m.roughness = 0.05; }
        }
        if (o.name.includes('_muro')) muros.push(o);
        if (m && m.name.startsWith('agua')) aguas.push(o);
      }
      // el entorno (césped infinito, vecinos y arboleda de la maqueta) lo reemplaza el mundo procedural
      if (/^(entorno|vecino_|arbol_|palma_|garage_palma|calle$|acera$|acera2$)/.test(o.name)) o.visible = false;
      objetos.push(o);
    });
    aplicarAlModelo(gltf.scene, texturas(base, renderer));
    scene.add(gltf.scene);
    gltf.scene.updateMatrixWorld(true);
    for (const a of aguas) (mundo as any).crearAgua(a);
    estado.cargado = true;
    if (!CINE) crearEtiquetas();
    aplicarVista();
    opts.onCargado?.();
    if (CINE) return;
    pct.textContent = 'Listo';
    barra.style.width = '100%';
    $('#btn-entrar').removeAttribute('disabled');
    $('#btn-libre').removeAttribute('disabled');
    (window as any).__listo = true;
    const h = decodeURIComponent(location.hash.slice(1));
    const camQ = new URLSearchParams(location.search).get('cam');
    if (camQ) {
      // depuración: ?cam=x,y,z,tx,ty,tz[,edificio:piso]
      const v = camQ.split(',');
      camera.position.set(+v[0], +v[1], +v[2]); orbit.target.set(+v[3], +v[4], +v[5]);
      if (v[6]) { const [ed, pi] = v[6].split(':'); setVista({ edificio: ed === 'sitio' ? null : ed, piso: +pi }); }
    } else if (h && presets[h]) { pantalla.classList.add('oculta'); setTimeout(() => irA(h), 300); }
  }, (e) => {
    if (e.total) { const p = Math.round((e.loaded / e.total) * 100); barra.style.width = `${p}%`; pct.textContent = `Cargando el modelo · ${p} %`; }
  }, (err) => { console.error(err); pct.textContent = 'No se pudo cargar el modelo. Recarga la página.'; });

  // ---------- controles ----------
  const orbit = new OrbitControls(camera, renderer.domElement);
  orbit.target.copy(centro).setY(2);
  if (RES) camera.position.set(...(presets['sitio'].pos as [number, number, number]));
  orbit.enableDamping = true; orbit.dampingFactor = 0.06;
  orbit.maxPolarAngle = Math.PI / 2.02; orbit.minDistance = RES ? 0.8 : 2.5; orbit.maxDistance = 240;
  orbit.addEventListener('start', () => { if (estado.tour) detenerTour(); ocultarAyuda(); });

  const keys: Record<string, boolean> = {};
  const enCampo = (e: KeyboardEvent) => (e.target as HTMLElement)?.closest?.('input, textarea, select');
  window.addEventListener('keydown', (e) => {
    if (enCampo(e)) return;
    keys[e.code] = true;
    if (estado.tour && /^(Key[WASD]|Arrow)/.test(e.code)) detenerTour();
  });
  window.addEventListener('keyup', (e) => (keys[e.code] = false));
  const vel = new THREE.Vector3();
  const alturaOjos = 1.65;
  const ray = new THREE.Raycaster();
  const nivelActual = () => (estado.vista.edificio && estado.vista.piso === 2 ? nivelDe(estado.vista.edificio) : 0);

  // ---------- caminar: arrastrar para mirar, tocar el piso para avanzar (como en los recorridos virtuales) ----------
  const anillo = new THREE.Mesh(
    new THREE.RingGeometry(0.2, 0.3, 40),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, depthWrite: false, side: THREE.DoubleSide }),
  );
  anillo.rotation.x = -Math.PI / 2; anillo.visible = false; anillo.renderOrder = 10;
  const anilloCentro = new THREE.Mesh(new THREE.CircleGeometry(0.2, 40), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide }));
  anillo.add(anilloCentro);
  scene.add(anillo);
  const visibleCadena = (o: THREE.Object3D | null) => { for (; o; o = o.parent) if (!o.visible) return false; return true; };
  const _n = new THREE.Vector3();
  const _ndc = new THREE.Vector2();
  function pisoBajo(x: number, y: number): THREE.Vector3 | null {
    const r = renderer.domElement.getBoundingClientRect();
    _ndc.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(_ndc, camera); ray.far = 40;
    const hits = ray.intersectObjects(objetos.filter((o) => (o as any).isMesh), false);
    for (const h of hits) {
      if (!visibleCadena(h.object) || h.object === anillo || !h.face) continue;
      _n.copy(h.face.normal).transformDirection(h.object.matrixWorld);
      if (_n.y < 0.6) return null;                       // pegó en un muro o mueble: ahí no se camina
      if (Math.abs(h.point.y - nivelActual()) > 1.3) return null;
      return h.point.clone();
    }
    return null;
  }
  let glide: { t: number; dur: number; p0: THREE.Vector3; p1: THREE.Vector3 } | null = null;
  function caminarA(p: THREE.Vector3) {
    const desde = camera.position.clone();
    const plano = new THREE.Vector3(p.x - desde.x, 0, p.z - desde.z);
    let d = plano.length(); if (d < 0.3) return;
    plano.normalize();
    // no atravesar muros: se detiene antes del primero que haya en el camino
    ray.set(desde.clone().setY(desde.y - 0.4), plano); ray.far = d;
    const muro = ray.intersectObjects(muros, false).find((h) => visibleCadena(h.object));
    if (muro) d = Math.max(0, muro.distance - 0.45);
    const destino = desde.clone().addScaledVector(plano, Math.min(d, 14));
    glide = { t: 0, dur: THREE.MathUtils.clamp(d / 3.2, 0.45, 1.6), p0: desde, p1: destino };
  }
  let pd: { x: number; y: number; t: number; mov: number; id: number } | null = null;
  let ultimoHover = 0;
  const lienzo = renderer.domElement;
  lienzo.addEventListener('pointerdown', (e) => {
    ocultarAyuda();
    if (esMovil() && !estado.tour) container.classList.add('reel-plegada');
    if (estado.modo !== 'recorrido') return;
    pd = { x: e.clientX, y: e.clientY, t: performance.now(), mov: 0, id: e.pointerId };
    try { lienzo.setPointerCapture(e.pointerId); } catch { /* evento sintético */ }
  });
  lienzo.addEventListener('pointermove', (e) => {
    if (estado.modo !== 'recorrido') return;
    if (pd && pd.id === e.pointerId) {
      const dx = e.movementX || 0, dy = e.movementY || 0;
      pd.mov += Math.abs(dx) + Math.abs(dy);
      const eu = new THREE.Euler(0, 0, 0, 'YXZ').setFromQuaternion(camera.quaternion);
      const k = e.pointerType === 'touch' ? 0.0045 : 0.0032;
      eu.y += dx * k; eu.x = THREE.MathUtils.clamp(eu.x + dy * k, -1.25, 1.25);   // arrastrar la imagen, como en las fotos 360°
      camera.quaternion.setFromEuler(eu);
      anillo.visible = false;
    } else if (e.pointerType === 'mouse' && performance.now() - ultimoHover > 40) {
      ultimoHover = performance.now();
      const p = pisoBajo(e.clientX, e.clientY);
      anillo.visible = !!p;
      if (p) anillo.position.set(p.x, p.y + 0.03, p.z);
      lienzo.style.cursor = p ? 'pointer' : 'grab';
    }
  });
  const soltar = (e: PointerEvent) => {
    if (!pd || pd.id !== e.pointerId) return;
    const toque = pd.mov < 8 && performance.now() - pd.t < 450;
    pd = null;
    if (!toque || estado.modo !== 'recorrido') return;
    const p = pisoBajo(e.clientX, e.clientY);
    if (p) {
      anillo.position.set(p.x, p.y + 0.03, p.z); anillo.visible = true;
      caminarA(p);
      if (e.pointerType !== 'mouse') setTimeout(() => (anillo.visible = false), 900);
    }
  };
  lienzo.addEventListener('pointerup', soltar);
  lienzo.addEventListener('pointercancel', () => (pd = null));
  lienzo.addEventListener('pointerleave', () => { if (!pd) anillo.visible = false; });

  // ---------- etiquetas en la escena ----------
  const etiquetaObjs: { obj: CSS2DObject; ed: string | null; piso: number; id: string }[] = [];
  function crearEtiquetas() {
    const mk = (id: string, texto: string, pos: number[], ed: string | null, piso: number) => {
      const el = document.createElement('button');
      const conFoto = !!FOTOS[id] || !!RENDER_CUARTO[id];
      el.className = 'etq' + (conFoto ? ' foto' : '') + (pano(id) ? ' p360' : '');
      el.innerHTML = `<i aria-hidden="true"></i><span>${texto}</span>${pano(id) ? '<b>360°</b>' : ''}`;
      el.addEventListener('click', (e) => { e.stopPropagation(); irA(id); });
      const o = new CSS2DObject(el);
      o.position.set(pos[0], pos[1] + 1.2, pos[2]);
      scene.add(o);
      etiquetaObjs.push({ obj: o, ed, piso, id });
    };
    for (const ex of (vistas as any).exteriores) mk(ex.id, ex.nombre, ex.centro, null, 99);
    if (RES) mk('jardin', 'Jardín interno', VISTAS_EXTRA.jardin.target, null, 99);
    for (const ed of (vistas as any).edificios) for (const p of ed.pisos) for (const r of p.rooms) {
      if (r.tipo === 'circulacion' && !r.id.startsWith('acceso')) continue;
      mk(r.id + '@' + ed.id, r.nombre.split(' · ')[0], r.centro, ed.id, p.n);
    }
    mk('calle', 'Entrada principal', RES ? (residencia as any).etiquetaCalle : [30, 1, -60], null, 99);
  }
  // Cada 3 cuadros: se ubican en pantalla, se ordenan (las que tienen foto primero, luego las más cercanas) y se
  // esconden las que chocan con otra, se salen del borde o caen debajo de los controles. En celular, máximo 7.
  const _p = new THREE.Vector3();
  const tamEtq = new WeakMap<HTMLElement, [number, number]>();
  let cuentaDespeje = 0;
  const ZONAS_UI = '.vt-marca, .vt-der, .vt-lugar, .vb, .niveles, .ficha:not(.oculta), .panel.abierto, .ayuda.on';
  function despejarEtiquetas() {
    if (++cuentaDespeje % 3) return;
    const W = container.clientWidth, H = container.clientHeight;
    const cr = container.getBoundingClientRect();
    const ocupado: number[][] = [];
    container.querySelectorAll(ZONAS_UI).forEach((z) => {
      const r = z.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) ocupado.push([r.left - cr.left, r.top - cr.top, r.right - cr.left, r.bottom - cr.top]);
    });
    const cands: { el: HTMLElement; r: number[]; prio: number }[] = [];
    for (const e of etiquetaObjs) {
      const el = e.obj.element as HTMLElement;
      if (!e.obj.visible || el.style.display === 'none') { el.classList.remove('tapada'); continue; }
      _p.setFromMatrixPosition(e.obj.matrixWorld).project(camera);
      if (_p.z > 1) continue;
      let t = tamEtq.get(el);
      if (!t) { t = [el.offsetWidth, el.offsetHeight]; if (t[0]) tamEtq.set(el, t); }
      const x = (_p.x * 0.5 + 0.5) * W, y = (-_p.y * 0.5 + 0.5) * H;
      cands.push({ el, r: [x - t[0] / 2 - 4, y - t[1] / 2 - 4, x + t[0] / 2 + 4, y + t[1] / 2 + 4], prio: (el.classList.contains('foto') ? 0 : 1) + _p.z });
    }
    cands.sort((a, b) => a.prio - b.prio);
    const max = W < 820 ? 7 : 22;
    let puestas = 0;
    for (const c of cands) {
      const [x0, y0, x1, y1] = c.r;
      const fuera = x0 < 4 || x1 > W - 4 || y0 < 4 || y1 > H - 4;
      const choca = puestas >= max || ocupado.some((o) => x0 < o[2] && x1 > o[0] && y0 < o[3] && y1 > o[1]);
      const ocultar = fuera || choca;
      c.el.classList.toggle('tapada', ocultar);
      if (!ocultar) { ocupado.push(c.r); puestas++; }
    }
  }
  function actualizarEtiquetas() {
    const { edificio, piso } = estado.vista;
    for (const e of etiquetaObjs) {
      let v = estado.etiquetas && estado.modo === 'orbita' && !estado.tour;
      if (e.ed) v = v && edificio === e.ed && e.piso === piso;
      else v = v && (edificio === null);
      e.obj.visible = v;
    }
  }

  // ---------- vista (edificio / piso) ----------
  const NOM_ED: Record<string, string> = { amarilla: 'Casa amarilla', gris: 'Edificio gris' };
  const nomPiso = (n: number) => (n === 2 ? 'planta alta' : 'planta baja');
  function aplicarVista() {
    const { edificio, piso } = estado.vista;
    for (const o of objetos) {
      const ud = (o as any).userData || {};
      if (!ud.edificio) continue;
      if (edificio && ud.edificio === edificio) {
        const p = ud.piso ?? 1;
        if (estado.modo === 'recorrido') o.visible = p <= piso || (ud.cielo && p === piso);
        else o.visible = (p <= piso && !(ud.cielo && p === piso && piso < 99)) || (p === 99 && piso >= 99);
      } else {
        o.visible = true;
      }
    }
    actualizarEtiquetas();
  }
  function setVista(v: Vista) {
    estado.vista = v;
    aplicarVista();
    const clave = `${v.edificio ?? 'sitio'}:${v.piso}`;
    document.querySelectorAll('[data-vista]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.vista === clave));
    $('#niv-actual').textContent = v.edificio ? `${v.edificio === 'gris' ? 'Gris' : 'Casa'} · ${v.piso === 2 ? 'PA' : 'PB'}` : 'Todo';
  }
  function setModo(m: Modo) {
    if (estado.tour) detenerTour();
    estado.modo = m;
    tween = null;
    orbit.enabled = m === 'orbita';
    container.classList.toggle('caminando', m === 'recorrido');
    anillo.visible = false; glide = null;
    lienzo.style.cursor = m === 'recorrido' ? 'grab' : '';
    if (m === 'recorrido') {
      ficha.classList.remove('abierta');             // en el celular la ficha abierta tapaba la vista
      // si se está viendo un cuarto desde adentro se camina desde ahí; si no, desde el punto que se mira
      const pr = presets[idActual];
      const nivel = nivelActual();
      if (pr && pr.ed && pr.pos[1] - nivel < 3) {
        camera.position.set(pr.pos[0], nivel + alturaOjos, pr.pos[2]);
        camera.lookAt(pr.target[0], nivel + 1.4, pr.target[2]);
      } else if (!estado.vista.edificio) {
        // desde la vista aérea: se baja a la entrada principal
        const c = presets['calle'];
        camera.position.set(c.pos[0], alturaOjos, c.pos[2]); camera.lookAt(c.target[0], 1.6, c.target[2]);
      } else {
        const t = orbit.target.clone();
        const dir = camera.position.clone().sub(t).setY(0).normalize();
        camera.position.copy(t).addScaledVector(dir, 2.2).setY(nivel + alturaOjos);
        camera.lookAt(t.x, nivel + 1.4, t.z);
      }
      mostrarAyuda(MOVIL || matchMedia('(pointer: coarse)').matches
        ? 'Arrastra para mirar · toca el piso para avanzar'
        : 'Arrastra para mirar · clic en el piso para avanzar · W A S D también caminan');
    } else {
      // al volver a la maqueta, el pivote queda delante de la cámara
      const f = new THREE.Vector3(); camera.getWorldDirection(f);
      orbit.target.copy(camera.position).addScaledVector(f, 3);
      ocultarAyuda();
    }
    aplicarVista();
    document.querySelectorAll('[data-modo]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.modo === m));
    if (estado.cargado && !CINE) mostrarFicha(idActual);
  }

  // ---------- volar / ir a ----------
  let tween: { t: number; dur: number; p0: THREE.Vector3; p1: THREE.Vector3; c: THREE.Vector3 | null; t0: THREE.Vector3; t1: THREE.Vector3; fin?: () => void } | null = null;
  function volar(pos: number[], target: number[], dur = 1.6, fin?: () => void) {
    if (estado.modo === 'recorrido') {
      glide = null;
      camera.position.set(pos[0], pos[1], pos[2]); camera.lookAt(target[0], target[1], target[2]); fin?.(); return;
    }
    const p0 = camera.position.clone(), p1 = new THREE.Vector3(...pos);
    // entre adentro y afuera (o de un cuarto a otro) la cámara sube y entra por arriba, con el techo abierto,
    // en vez de atravesar muros en línea recta
    const d = p0.distanceTo(p1);
    let c: THREE.Vector3 | null = null;
    if (d > 6 && Math.min(p0.y, p1.y) < 9) {
      c = p0.clone().add(p1).multiplyScalar(0.5);
      c.y = Math.max(p0.y, p1.y) + Math.min(28, d * 0.35 + 6);
    }
    tween = { t: 0, dur, p0, p1, c, t0: orbit.target.clone(), t1: new THREE.Vector3(...target), fin };
  }
  let idActual = 'sitio';
  const VUELO = 2.8;                  // segundos de vuelo entre paradas del recorrido guiado
  function irA(id: string, desdeTour = false) {
    const pr = presets[id]; if (!pr) return;
    if (!desdeTour && estado.tour) detenerTour();
    // caminando, las vistas aéreas vuelven a la maqueta (si no, quedaría parado en medio del césped)
    if (estado.modo === 'recorrido') {
      const nivel = pr.ed && pr.piso === 2 ? nivelDe(pr.ed) : 0;
      if (!pr.ed || pr.pos[1] - nivel > 3) setModo('orbita');
    }
    idActual = id;
    setVista({ edificio: pr.ed, piso: pr.piso });
    let pos = pr.pos;
    // vistas generales y plantas sin techo: en pantalla vertical la cámara se aleja un poco para que quepa todo
    if (camera.aspect < 1 && (id === 'sitio' || /-p\d$/.test(id))) {
      const k = THREE.MathUtils.lerp(1.35, 1, THREE.MathUtils.clamp((camera.aspect - 0.45) / 0.55, 0, 1));
      pos = pr.pos.map((v, i) => pr.target[i] + (v - pr.target[i]) * k);
    }
    volar(pos, pr.target, desdeTour ? VUELO : 1.6);
    if (estado.modo === 'recorrido') camera.position.y = (pr.piso === 2 && pr.ed ? nivelDe(pr.ed) : 0) + alturaOjos;
    panel.querySelectorAll('li').forEach((x) => x.classList.toggle('on', (x as HTMLElement).dataset.id === id));
    marcarReel(id);
    mostrarFicha(id);
    history.replaceState(null, '', `#${id}`);
  }

  // ---------- modal (fotos, renders, planos) ----------
  const modal = $('#vmodal');
  const B = base.replace(/\/$/, '');
  function abrirModal(titulo: string, cuerpo: string, extra = '') {
    modal.innerHTML = `<div class="vm-caja"><div class="vm-cab"><strong>${titulo}</strong>${extra}<button class="vm-cerrar" aria-label="Cerrar"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12 M18 6L6 18" /></svg></button></div><div class="vm-cuerpo">${cuerpo}</div></div>`;
    modal.hidden = false;
    modal.setAttribute('aria-label', titulo);
    modal.querySelector('.vm-cerrar')!.addEventListener('click', cerrarModal);
    (modal.querySelector('.vm-cerrar') as HTMLElement).focus();
    if (estado.tour) detenerTour();
  }
  function cerrarModal() { modal.hidden = true; modal.innerHTML = ''; }
  modal.addEventListener('click', (e) => { if (e.target === modal) cerrarModal(); });
  window.addEventListener('keydown', (e) => { if (e.code === 'Escape' && !modal.hidden) cerrarModal(); });

  function comparador(antes: string, despues: string, nombre: string) {
    return `<div class="vm-comp"><img src="${despues}" alt="${nombre}, así quedará"><div class="vm-antes" style="clip-path:inset(0 50% 0 0)"><img src="${antes}" alt="${nombre}, hoy"></div><span class="vm-linea" style="left:50%"><i></i></span><input type="range" min="0" max="100" value="50" aria-label="Comparar hoy y así quedará"><span class="vm-l">Hoy</span><span class="vm-r">Así quedará</span></div>`;
  }
  function activarComparador() {
    const r = modal.querySelector('input') as HTMLInputElement | null; const a = modal.querySelector('.vm-antes') as HTMLElement | null; const ln = modal.querySelector('.vm-linea') as HTMLElement | null;
    if (r && a) r.addEventListener('input', () => { a.style.clipPath = `inset(0 ${100 - +r.value}% 0 0)`; if (ln) ln.style.left = `${r.value}%`; });
  }
  function abrirFotos(id: string) {
    const f = FOTOS[id]; if (!f) return;
    const antes = `${B}/fotos-antes/${f.antes}.jpg`;
    const despues = `${B}/fotos-despues/${f.despues || f.antes}.jpg`;
    const probe = new Image();
    probe.onload = () => { abrirModal(f.nombre, comparador(antes, despues, f.nombre), '<span>Arrastra para comparar</span>'); activarComparador(); };
    probe.onerror = () => abrirModal(f.nombre, `<img class="vm-img" src="${antes}" alt="${f.nombre}, foto actual">`, '<span>Foto actual</span>');
    probe.src = despues;
  }
  function abrirRender(id: string) {
    const r = RENDER_CUARTO[id]; if (!r) return;
    const d = DESC[r];
    abrirModal(d?.t || presets[id]?.nombre || '', `<img class="vm-img" src="${B}/avances/${r}.jpg" alt="${d?.t || ''}">${d ? `<p class="vm-pie">${d.d}</p>` : ''}`, '<span>Render del proyecto</span>');
  }
  function abrirPlanos(inicial?: string) {
    const ini = PLANOS_VISOR.find((p) => p.id === inicial) || PLANOS_VISOR.find((p) => p.ed === 'gris' && p.piso === 2)!;
    const tabs = PLANOS_VISOR.map((p) => `<button data-plano="${p.id}" class="${p.id === ini.id ? 'on' : ''}">${p.t}</button>`).join('');
    abrirModal('Planos', `<div class="vm-tabs" role="tablist">${tabs}</div><a class="vm-plano" href="${B}${ini.f}" target="_blank" rel="noopener" title="Abrir el plano en grande"><img src="${B}${ini.f}" alt="${ini.t}"></a><p class="vm-pie">Medidas aproximadas, tomadas del satélite y de las fotos. La línea roja es la ruta del recorrido desde la escalera. Toca el plano para abrirlo en grande.</p>`);
    const centrarTab = () => (modal.querySelector('[data-plano].on') as HTMLElement | null)?.scrollIntoView({ inline: 'center', block: 'nearest' });
    centrarTab();
    modal.querySelectorAll<HTMLButtonElement>('[data-plano]').forEach((b) => b.addEventListener('click', () => {
      const p = PLANOS_VISOR.find((x) => x.id === b.dataset.plano)!;
      const img = modal.querySelector('.vm-plano img') as HTMLImageElement; img.src = `${B}${p.f}`; img.alt = p.t;
      (modal.querySelector('.vm-plano') as HTMLAnchorElement).href = `${B}${p.f}`;
      modal.querySelectorAll('[data-plano]').forEach((x) => x.classList.toggle('on', x === b));
      centrarTab();
    }));
  }
  $('#btn-planos').addEventListener('click', () => {
    const v = estado.vista;
    abrirPlanos(v.edificio ? `${v.edificio}:${v.piso === 2 ? 2 : 1}` : undefined);
  });

  // ---------- ficha del lugar ----------
  const PANOS = (RES ? panoramas : []) as Pano[];
  function pano(id: string) { return PANOS.find((p) => p.id === id); }
  const DESC: Record<string, { t: string; d: string }> = {};
  for (const v of [...AV_GRIS, ...AV_CASA]) DESC[v.f] = { t: v.t, d: v.d };
  const ficha = $('#ficha');
  function lugarDe(pr: Preset) {
    if (!pr.ed) return 'Terreno';
    return `${NOM_ED[pr.ed] || pr.ed} · ${nomPiso(pr.piso)}`;
  }
  function mostrarFicha(id: string, textoTour?: string) {
    const pr = presets[id]; if (!pr) return;
    const par = PARADAS_3D.find((p) => p.id === id);
    const r = RENDER_CUARTO[id];
    const d = r ? DESC[r] : undefined;
    const titulo = par?.nombre || pr.nombre.split(' · ')[0];
    const lugar = par?.lugar || lugarDe(pr);
    let texto = textoTour || par?.texto || d?.d || '';
    if (!texto && /-p\d$/.test(id)) texto = 'Vista de la planta sin techo. Toca un nombre para entrar a ese espacio.';
    const datos = par?.datos || (pr.detalle && /cama/.test(pr.detalle) ? [pr.detalle] : []);
    $('#ficha-titulo').textContent = titulo;
    $('#ficha-lugar').textContent = lugar;
    $('#ficha-texto').textContent = texto;
    $('#vt-lugar').textContent = id === 'sitio' ? 'Vista general' : `${titulo} · ${lugar}`;
    $('#ficha-datos').innerHTML = datos.map((x) => `<li>${x}</li>`).join('');
    const img = $('#ficha-img') as HTMLButtonElement;
    if (r) { (img.querySelector('img') as HTMLImageElement).src = `${B}/mini/${r}.jpg`; img.hidden = false; img.onclick = () => abrirRender(id); }
    else if (id === 'terraza@gris' && FOTOS[id]) { (img.querySelector('img') as HTMLImageElement).src = `${B}/mini/terraza.jpg`; img.hidden = false; img.onclick = () => abrirFotos(id); }
    else { img.hidden = true; img.onclick = null; }
    const acc: string[] = [];
    if (pano(id)) acc.push(`<button class="fa fa-p" data-acc="360"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 4 0 1 0 18 0a9 4 0 1 0 -18 0 M12 3v18" /></svg>Vista 360°</button>`);
    if (FOTOS[id]) acc.push(`<button class="fa" data-acc="fotos"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h3l2-2h6l2 2h3v12H4z M12 10a3 3 0 1 0 .01 0" /></svg>${FOTOS[id].despues ? 'Hoy y así quedará' : 'Foto real'}</button>`);
    if (pr.ed && estado.modo === 'orbita') acc.push(`<button class="fa" data-acc="caminar"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 4.5a1.6 1.6 0 1 0 .01 0 M10 21l2-6-2.5-2.5 1.5-5 3 3 3 1 M12 15l3 6" /></svg>Caminar aquí</button>`);
    $('#ficha-acciones').innerHTML = acc.join('');
    $('#ficha-acciones').querySelectorAll<HTMLButtonElement>('[data-acc]').forEach((b) => b.addEventListener('click', () => {
      const a = b.dataset.acc;
      if (a === '360') { if (estado.tour) detenerTour(); abrir360(pano(id)!, PANOS, base); }
      else if (a === 'fotos') abrirFotos(id);
      else if (a === 'render') abrirRender(id);
      else if (a === 'caminar') setModo('recorrido');
    }));
    ficha.classList.remove('oculta');
    ficha.classList.toggle('sin-img', img.hidden);
  }
  $('#ficha-cerrar').addEventListener('click', () => ficha.classList.add('oculta'));
  // en el celular la ficha se abre o se pliega tocándola
  ficha.addEventListener('click', (e) => {
    if ((e.target as HTMLElement).closest('button, a')) return;
    ficha.classList.toggle('abierta');
  });

  // ---------- índice de espacios ----------
  const panel = $('#panel-lista');
  const MINI_EXT: Record<string, string> = { sitio: 'sitio', calle: 'calle', jardin: 'jardin', 'gris-ext': 'gris-ext', parqueo_casa: 'parqueo-casa', 'terraza@gris': 'terraza' };
  function li(id: string, nombre: string, detalle?: string) {
    const r = RENDER_CUARTO[id];
    const ext = MINI_EXT[id];
    const marcas = (pano(id) ? '<i class="tag">360°</i>' : '') + (FOTOS[id] ? '<i class="tag">fotos</i>' : '');
    const planta = /-p\d$/.test(id);
    const mini = r || ext ? `<img src="${B}/mini/${r || ext}.jpg" alt="" loading="lazy">`
      : `<span class="li-sin" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="${planta ? 'M4 4h16v16H4z M4 12h7 M11 4v16 M15 12h5' : 'M12 21s-6-5.6-6-10a6 6 0 1 1 12 0c0 4.4-6 10-6 10z M12 11h.01'}" /></svg></span>`;
    return `<li data-id="${id}" tabindex="0" role="button">${mini}<span class="li-t">${nombre}<small>${[detalle, marcas].filter(Boolean).join(' ')}</small></span></li>`;
  }
  let html = `<h3>Terreno</h3><ul>${li('sitio', 'Vista general', '2.500 m²')}${li('calle', 'Entrada principal')}${RES ? li('jardin', 'Jardín interno', 'propuesta') : ''}${li('gris-ext', RES ? 'Edificio gris por fuera' : 'Edificio de hospitalización')}`;
  for (const ex of (vistas as any).exteriores) html += li(ex.id, ex.nombre);
  html += `</ul>`;
  const orden = [...(vistas as any).edificios].sort((a: any) => (a.id === 'amarilla' ? -1 : 1));
  for (const ed of orden) for (const p of ed.pisos) {
    html += `<h3>${ed.nombre} · ${p.nombre.toLowerCase()}</h3><ul>${li(`${ed.id}-p${p.n}`, 'Ver la planta completa', 'sin techo')}`;
    for (const r of p.rooms) {
      if (r.tipo === 'circulacion' && !r.id.startsWith('acceso')) continue;
      html += li(r.id + '@' + ed.id, r.nombre, r.camas ? `${r.camas} ${r.camas === 1 ? 'cama' : 'camas'}` : (r.tipo === 'terraza' ? 'al aire libre' : ''));
    }
    html += `</ul>`;
  }
  panel.innerHTML = html;
  const panelEl = $('#panel');
  function abrirPanel(abrir: boolean) {
    panelEl.classList.toggle('abierto', abrir);
    panelEl.setAttribute('aria-hidden', String(!abrir));
    for (const b of ['#btn-panel', '#btn-panel-d']) { $(b).setAttribute('aria-expanded', String(abrir)); $(b).classList.toggle('on', abrir); }
    if (abrir && estado.tour) detenerTour();
  }
  const elegir = (el: HTMLElement | null) => {
    if (!el) return;
    irA(el.dataset.id!);
    if (esMovil()) abrirPanel(false);              // en el celular la hoja tapa el modelo: se cierra al elegir
  };
  panel.addEventListener('click', (e) => elegir((e.target as HTMLElement).closest('li')));
  panel.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); elegir((e.target as HTMLElement).closest('li')); } });
  $('#btn-panel').addEventListener('click', () => abrirPanel(!panelEl.classList.contains('abierto')));
  $('#btn-panel-d').addEventListener('click', () => abrirPanel(!panelEl.classList.contains('abierto')));
  $('#panel-cerrar').addEventListener('click', () => abrirPanel(false));
  window.addEventListener('keydown', (e) => { if (e.code === 'Escape' && panelEl.classList.contains('abierto')) abrirPanel(false); });

  // ---------- modos, niveles, nombres, pantalla completa ----------
  document.querySelectorAll('[data-modo]').forEach((b) => b.addEventListener('click', () => setModo((b as HTMLElement).dataset.modo as Modo)));
  const niveles = $('#niveles');
  $('#btn-niveles').addEventListener('click', () => {
    const ab = !niveles.classList.contains('abierto');
    niveles.classList.toggle('abierto', ab); $('#btn-niveles').setAttribute('aria-expanded', String(ab));
  });
  document.querySelectorAll('[data-vista]').forEach((b) => b.addEventListener('click', () => {
    const [ed, p] = (b as HTMLElement).dataset.vista!.split(':');
    if (estado.tour) detenerTour();
    niveles.classList.remove('abierto'); $('#btn-niveles').setAttribute('aria-expanded', 'false');
    // elegir un nivel lleva a verlo desde arriba sin techo; caminando, solo cambia lo que se ve
    const id = ed === 'sitio' ? 'sitio' : `${ed}-p${p}`;
    if (estado.modo === 'recorrido' && ed !== 'sitio') setModo('orbita');
    if (presets[id]) irA(id);
    else setVista({ edificio: ed === 'sitio' ? null : ed, piso: parseInt(p) });
  }));
  $('#btn-etiquetas').addEventListener('click', () => {
    estado.etiquetas = !estado.etiquetas;
    $('#btn-etiquetas').classList.toggle('on', estado.etiquetas);
    $('#btn-etiquetas').setAttribute('aria-pressed', String(estado.etiquetas));
    actualizarEtiquetas();
  });
  const btnPantalla = $('#btn-pantalla') as HTMLButtonElement;
  if (document.fullscreenEnabled) {
    btnPantalla.hidden = false;
    btnPantalla.addEventListener('click', () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {}));
  }

  // ---------- ayuda de gestos (una vez, se va sola) ----------
  const ayuda = $('#ayuda');
  let ayudaTimer: number | null = null;
  function mostrarAyuda(t: string) {
    ayuda.textContent = t; ayuda.classList.add('on');
    if (ayudaTimer) clearTimeout(ayudaTimer);
    ayudaTimer = window.setTimeout(ocultarAyuda, 6000);
  }
  function ocultarAyuda() { ayuda.classList.remove('on'); }

  // ---------- tira de paradas y recorrido guiado ----------
  const reel = $('#reel');
  function marcarReel(id: string) {
    reel.querySelectorAll<HTMLButtonElement>('button').forEach((b) => {
      const on = b.dataset.id === id;
      b.classList.toggle('on', on);
      b.setAttribute('aria-current', on ? 'true' : 'false');
      if (on) {
        const li = b.parentElement!; const lista = reel as HTMLElement;
        lista.scrollTo({ left: li.offsetLeft - (lista.clientWidth - li.clientWidth) / 2, behavior: reduceMotion ? 'auto' : 'smooth' });
      }
    });
  }
  reel.querySelectorAll<HTMLButtonElement>('button').forEach((b) => b.addEventListener('click', () => irA(b.dataset.id!)));
  let tourIdx = 0; let tourTimer: number | null = null;
  function pasoTour() {
    if (!estado.tour) return;
    if (tourIdx >= PARADAS_3D.length) {
      detenerTour();
      irA('sitio');
      mostrarFicha('sitio', 'Una residencia lista para operar, con pasadía y estadías temporales. Solicita el expediente completo para inversionistas.');
      $('#ficha-acciones').insertAdjacentHTML('afterbegin', `<a class="fa fa-p" href="${enlaceContacto()}">Solicitar información</a>`);
      return;
    }
    const paso = PARADAS_3D[tourIdx];
    irA(paso.id, true);
    ficha.classList.add('abierta');
    const dur = (paso.espera ?? 4) + VUELO;
    const btn = reel.querySelector<HTMLElement>(`button[data-i="${tourIdx}"]`);
    reel.querySelectorAll('.corre').forEach((x) => x.classList.remove('corre'));
    if (btn) { btn.style.setProperty('--dur', `${dur}s`); void btn.offsetWidth; btn.classList.add('corre'); }
    tourIdx++;
    tourTimer = window.setTimeout(pasoTour, dur * 1000);
  }
  function iniciarTour(desde = -1) {
    if (estado.modo !== 'orbita') setModo('orbita');
    abrirPanel(false); cerrarModal(); ocultarAyuda();
    estado.tour = true;
    const k = PARADAS_3D.findIndex((p) => p.id === idActual);
    tourIdx = desde >= 0 ? desde : (k > 0 && k < PARADAS_3D.length - 1 ? k : 0);
    container.classList.add('en-tour'); container.classList.remove('reel-plegada');
    $('#btn-tour').setAttribute('aria-label', 'Pausar el recorrido guiado');
    actualizarEtiquetas();
    pasoTour();
  }
  function detenerTour() {
    estado.tour = false;
    if (tourTimer) clearTimeout(tourTimer);
    container.classList.remove('en-tour');
    reel.querySelectorAll('.corre').forEach((x) => x.classList.remove('corre'));
    $('#btn-tour').setAttribute('aria-label', 'Reproducir el recorrido guiado');
    ficha.classList.remove('abierta');
    actualizarEtiquetas();
  }
  $('#btn-tour').addEventListener('click', () => (estado.tour ? detenerTour() : iniciarTour()));
  $('#btn-reel').addEventListener('click', () => container.classList.remove('reel-plegada'));
  // la ficha se apoya sobre la barra de abajo, que cambia de alto según la pantalla
  const vb = container.querySelector('.vb') as HTMLElement | null;
  if (vb && 'ResizeObserver' in window) new ResizeObserver(() => container.style.setProperty('--vb-h', `${vb.offsetHeight}px`)).observe(vb);
  $('#btn-entrar').addEventListener('click', () => { pantalla.classList.add('oculta'); iniciarTour(0); });
  $('#btn-libre').addEventListener('click', () => {
    pantalla.classList.add('oculta');
    irA('sitio');
    mostrarAyuda(MOVIL || matchMedia('(pointer: coarse)').matches
      ? 'Arrastra para girar · pellizca para acercar · toca un nombre para entrar'
      : 'Arrastra para girar · rueda para acercar · clic en un nombre para entrar');
  });

  // ---------- loop ----------
  const clock = new THREE.Clock();
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const maxFrames = parseInt(new URLSearchParams(location.search).get('frames') || '0');
  let nFrames = 0;
  const _f = new THREE.Vector3(), _r = new THREE.Vector3(), _d = new THREE.Vector3(), _cero = new THREE.Vector3(), _arriba = new THREE.Vector3(0, 1, 0);
  function frame() {
    if (estado.cargado) nFrames++;
    if (maxFrames && nFrames > maxFrames) { (window as any).__done = true; return; }
    const dt = Math.min(clock.getDelta(), 0.05);
    if (estado.modo === 'cine' && opts.ruta && opts.ruta.length > 1) {
      uSuave += (uObjetivo - uSuave) * (reduceMotion ? 1 : 0.06);
      const p = rutaPos.getPoint(uSuave), t = rutaTgt.getPoint(uSuave);
      const el = clock.elapsedTime;
      p.y += Math.sin(el * 0.7) * 0.12; t.x += Math.sin(el * 0.5) * 0.25; t.y += Math.cos(el * 0.6) * 0.15;
      camera.position.copy(p); camera.lookAt(t); orbit.target.copy(t);
    }
    if (tween) {
      tween.t = Math.min(1, tween.t + dt / tween.dur);
      const k = tween.t < 0.5 ? 2 * tween.t * tween.t : -1 + (4 - 2 * tween.t) * tween.t;
      if (tween.c) {
        const a = 1 - k;
        camera.position.set(0, 0, 0).addScaledVector(tween.p0, a * a).addScaledVector(tween.c, 2 * a * k).addScaledVector(tween.p1, k * k);
      } else camera.position.lerpVectors(tween.p0, tween.p1, k);
      orbit.target.lerpVectors(tween.t0, tween.t1, k);
      if (tween.t >= 1) { const f = tween.fin; tween = null; f?.(); }
    }
    if (estado.modo === 'orbita') {
      orbit.update();
    } else if (estado.modo === 'recorrido') {
      camera.getWorldDirection(_f); _f.y = 0; _f.normalize();
      _r.crossVectors(_f, _arriba);
      _d.set(0, 0, 0);
      if (keys.KeyW || keys.ArrowUp) _d.add(_f);
      if (keys.KeyS || keys.ArrowDown) _d.sub(_f);
      if (keys.KeyD || keys.ArrowRight) _d.add(_r);
      if (keys.KeyA || keys.ArrowLeft) _d.sub(_r);
      if (_d.lengthSq() > 0) glide = null;
      const speed = keys.ShiftLeft || keys.ShiftRight ? 4.5 : 2.0;
      vel.lerp(_d.lengthSq() > 0 ? _d.normalize().multiplyScalar(speed) : _cero, 0.18);
      if (vel.lengthSq() > 0.0001) {
        ray.set(camera.position.clone().setY(camera.position.y - 0.4), vel.clone().normalize()); ray.far = 0.6;
        if (ray.intersectObjects(muros, false).filter((h) => visibleCadena(h.object)).length === 0) camera.position.addScaledVector(vel, dt);
      }
      if (glide) {
        glide.t = Math.min(1, glide.t + dt / glide.dur);
        const k = 1 - Math.pow(1 - glide.t, 3);
        camera.position.x = glide.p0.x + (glide.p1.x - glide.p0.x) * k;
        camera.position.z = glide.p0.z + (glide.p1.z - glide.p0.z) * k;
        if (glide.t >= 1) { glide = null; if (!matchMedia('(hover: hover)').matches) anillo.visible = false; }
      }
      camera.position.y += (nivelActual() + alturaOjos - camera.position.y) * 0.2;
      camera.position.x = THREE.MathUtils.clamp(camera.position.x, LIM[0], LIM[1]);
      camera.position.z = THREE.MathUtils.clamp(camera.position.z, LIM[2], LIM[3]);
    }
    // relleno interior: solo dentro de un edificio
    const dentro = !CINE && !!estado.vista.edificio && (estado.modo === 'recorrido' || camera.position.y < 7);
    relleno.intensity += ((dentro ? 6 : 0) - relleno.intensity) * 0.1;
    relleno.position.copy(camera.position).y += 0.6;
    mundo.update(clock.elapsedTime, dt, camera);
    composer.render();
    renderer.autoClear = false; renderer.render(mundo.escenaNubes, camera); renderer.autoClear = true;
    labels.render(scene, camera);
    if (!CINE) despejarEtiquetas();
    requestAnimationFrame(frame);
  }
  frame();

  window.addEventListener('resize', () => {
    const w = container.clientWidth, h = container.clientHeight;
    ajustarLente();
    renderer.setSize(w, h); composer.setSize(w, h); labels.setSize(w, h); gtao?.setSize(w, h); bloom?.setSize(w, h);
  });

  if (CINE) { estado.modo = 'cine'; estado.etiquetas = false; orbit.enabled = false; container.classList.add('cine'); }
  else { setModo('orbita'); mostrarFicha('sitio'); marcarReel('sitio'); }
  const api = { setModo, setVista, irA, setProgreso, iniciarTour, detenerTour, abrirPlanos };
  (window as any).__visor = api;
  (window as any).__setProgreso = setProgreso;
  (window as any).__info = () => ({ ...renderer.info.render, geometrias: renderer.info.memory.geometries, texturas: renderer.info.memory.textures });
  (window as any).__snap = () => { composer.render(); renderer.autoClear = false; renderer.render(mundo.escenaNubes, camera); renderer.autoClear = true; return renderer.domElement.toDataURL('image/jpeg', 0.85); };
  return api;
}
