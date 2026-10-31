import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { SMAAPass } from 'three/examples/jsm/postprocessing/SMAAPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { crearMundo, type ConfigMundo } from './mundo';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import vistasMaqueta from '../data/vistas.json';
import residencia from '../data/residencia.json';
import fotos from '../data/fotos.json';

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
  'galeria@gris': { ...F['refrigerios@gris'], nombre: 'Área de coffee break' },
  'cocina@gris': { ...F['cocina@gris'], nombre: 'Cocineta del área de coffee break' },
  'terraza@gris': { ...F['terraza@gris'], nombre: 'Terraza' },
  'bano_acc@gris': { ...F['bano_acc@gris'], nombre: 'Baño accesible para usuarios' },
  'comedor@amarilla': { ...F['comedor@amarilla'], nombre: 'Comedor y TV' },
  'terapia@amarilla': { ...F['terapia@amarilla'], nombre: 'Terapia con familiares' },
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
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.72;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  labels.setSize(container.clientWidth, container.clientHeight);
  labels.domElement.className = 'etiquetas';
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 5000);
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
  u.turbidity.value = 2.8; u.rayleigh.value = 1.1; u.mieCoefficient.value = 0.005; u.mieDirectionalG.value = 0.85;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene(); skyScene.add(sky.clone());
  scene.environment = pmrem.fromScene(skyScene as any, 0.02).texture;
  scene.environmentIntensity = 0.45;
  scene.fog = new THREE.FogExp2(new THREE.Color('#d8d0c2'), MOVIL ? 0.0011 : 0.00075);
  const mundo = crearMundo(scene, renderer, MOVIL, sunDir, (opts.ruta || []).map((r) => [r.pos[0], r.pos[2]]), RES ? (residencia as any).mundo as ConfigMundo : undefined);

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
  scene.add(new THREE.HemisphereLight(0xdcc8ff, 0x6a5a3a, 0.5));
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
  const bloom = new UnrealBloomPass(new THREE.Vector2(container.clientWidth, container.clientHeight), MOVIL ? 0.1 : 0.16, 0.6, 0.9);
  composer.addPass(bloom);
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
          if (m.name.startsWith('vidrio')) { m.transparent = true; m.opacity = 0.28; m.roughness = 0.05; m.metalness = 0.1; m.depthWrite = false; o.castShadow = false; }
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
    scene.add(gltf.scene);
    gltf.scene.updateMatrixWorld(true);
    for (const a of aguas) (mundo as any).crearAgua(a);
    estado.cargado = true;
    if (!CINE) crearEtiquetas();
    aplicarVista();
    opts.onCargado?.();
    if (CINE) return;
    pct.textContent = '100 %';
    $('#btn-entrar').removeAttribute('disabled');
    $('#btn-entrar').textContent = 'Entrar al recorrido';
    const h = decodeURIComponent(location.hash.slice(1));
    const camQ = new URLSearchParams(location.search).get('cam');
    if (camQ) {
      // depuración: ?cam=x,y,z,tx,ty,tz[,edificio:piso]
      const v = camQ.split(',');
      camera.position.set(+v[0], +v[1], +v[2]); orbit.target.set(+v[3], +v[4], +v[5]);
      if (v[6]) { const [ed, pi] = v[6].split(':'); setVista({ edificio: ed === 'sitio' ? null : ed, piso: +pi }); }
    } else if (h && presets[h]) { setTimeout(() => irA(h), 300); }
  }, (e) => {
    if (e.total) { const p = Math.round((e.loaded / e.total) * 100); barra.style.width = `${p}%`; pct.textContent = `${p} %`; }
  }, (err) => { console.error(err); pct.textContent = 'No se pudo cargar el modelo. Recarga la página.'; });
  $('#btn-entrar').addEventListener('click', () => { pantalla.classList.add('oculta'); if (!location.hash) iniciarTour(); });

  // ---------- controles ----------
  const orbit = new OrbitControls(camera, renderer.domElement);
  orbit.target.copy(centro).setY(2);
  if (RES) camera.position.set(...(presets['sitio'].pos as [number, number, number]));
  orbit.enableDamping = true; orbit.dampingFactor = 0.06;
  orbit.maxPolarAngle = Math.PI / 2.02; orbit.minDistance = RES ? 0.8 : 2.5; orbit.maxDistance = 240;
  orbit.addEventListener('start', () => { if (estado.tour) detenerTour(); });

  const plc = new PointerLockControls(camera, renderer.domElement);
  const keys: Record<string, boolean> = {};
  window.addEventListener('keydown', (e) => { keys[e.code] = true; if (estado.tour && e.code !== 'Escape') detenerTour(); });
  window.addEventListener('keyup', (e) => (keys[e.code] = false));
  const vel = new THREE.Vector3();
  const alturaOjos = 1.65;
  const ray = new THREE.Raycaster();
  let joyVec = { x: 0, y: 0 };
  const joy = $('#joy');
  if (joy) {
    joy.addEventListener('touchmove', (e) => {
      const t = e.touches[0]; const r = joy.getBoundingClientRect();
      joyVec = { x: THREE.MathUtils.clamp((t.clientX - r.left - r.width / 2) / (r.width / 2), -1, 1), y: THREE.MathUtils.clamp((t.clientY - r.top - r.height / 2) / (r.height / 2), -1, 1) };
      e.preventDefault();
    }, { passive: false });
    joy.addEventListener('touchend', () => (joyVec = { x: 0, y: 0 }));
  }
  // mirar con el dedo en modo caminar (móvil)
  let lastTouch: { x: number; y: number } | null = null;
  renderer.domElement.addEventListener('touchstart', (e) => { if (estado.modo === 'recorrido') lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY }; }, { passive: true });
  renderer.domElement.addEventListener('touchmove', (e) => {
    if (estado.modo !== 'recorrido' || !lastTouch) return;
    const dx = e.touches[0].clientX - lastTouch.x, dy = e.touches[0].clientY - lastTouch.y;
    lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    const eu = new THREE.Euler(0, 0, 0, 'YXZ').setFromQuaternion(camera.quaternion);
    eu.y -= dx * 0.004; eu.x = THREE.MathUtils.clamp(eu.x - dy * 0.004, -1.3, 1.3);
    camera.quaternion.setFromEuler(eu);
  }, { passive: true });

  // ---------- etiquetas en la escena ----------
  const etiquetaObjs: { obj: CSS2DObject; ed: string | null; piso: number; id: string }[] = [];
  function crearEtiquetas() {
    const mk = (id: string, texto: string, pos: number[], ed: string | null, piso: number, foto: boolean) => {
      const el = document.createElement('button');
      el.className = 'etq' + (foto ? ' foto' : '');
      el.innerHTML = `<span>${texto}</span>`;
      el.addEventListener('click', (e) => { e.stopPropagation(); irA(id); });
      const o = new CSS2DObject(el);
      o.position.set(pos[0], pos[1] + 1.2, pos[2]);
      scene.add(o);
      etiquetaObjs.push({ obj: o, ed, piso, id });
    };
    for (const ex of (vistas as any).exteriores) mk(ex.id, ex.nombre, ex.centro, null, 99, !!FOTOS[ex.id]);
    for (const ed of (vistas as any).edificios) for (const p of ed.pisos) for (const r of p.rooms) {
      if (r.tipo === 'circulacion' && !r.id.startsWith('acceso')) continue;
      mk(r.id + '@' + ed.id, r.nombre, r.centro, ed.id, p.n, !!FOTOS[r.id + '@' + ed.id]);
    }
    mk('calle', 'Entrada principal', RES ? (residencia as any).etiquetaCalle : [30, 1, -60], null, 99, false);
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
    document.querySelectorAll('[data-vista]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.vista === `${v.edificio ?? 'sitio'}:${v.piso}`));
  }
  function setModo(m: Modo) {
    if (estado.tour) detenerTour();
    estado.modo = m;
    orbit.enabled = m === 'orbita';
    container.classList.toggle('caminando', m === 'recorrido');
    if (m === 'recorrido') {
      const t = orbit.target.clone();
      const dir = camera.position.clone().sub(t).setY(0).normalize();
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? nivelDe(estado.vista.edificio) : 0;
      camera.position.copy(t).addScaledVector(dir, 2.2).setY(nivel + alturaOjos);
      camera.lookAt(t.x, nivel + 1.4, t.z);
      $('#hint').textContent = MOVIL ? 'Arrastra para mirar · joystick para caminar' : 'Clic en la escena para mirar con el mouse · WASD o flechas para caminar · Shift corre · Esc suelta el mouse';
    } else {
      plc.unlock();
      $('#hint').textContent = 'Arrastra para girar · rueda para acercar · toca una etiqueta o elige un espacio en el panel';
    }
    aplicarVista();
    document.querySelectorAll('[data-modo]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.modo === m));
  }
  renderer.domElement.addEventListener('click', () => { if (estado.modo === 'recorrido' && !plc.isLocked && !MOVIL) plc.lock(); });

  // ---------- volar / ir a ----------
  let tween: { t: number; dur: number; p0: THREE.Vector3; p1: THREE.Vector3; t0: THREE.Vector3; t1: THREE.Vector3; fin?: () => void } | null = null;
  function volar(pos: number[], target: number[], dur = 1.6, fin?: () => void) {
    if (estado.modo === 'recorrido') {
      camera.position.set(pos[0], pos[1], pos[2]); camera.lookAt(target[0], target[1], target[2]); fin?.(); return;
    }
    tween = { t: 0, dur, p0: camera.position.clone(), p1: new THREE.Vector3(...pos), t0: orbit.target.clone(), t1: new THREE.Vector3(...target), fin };
  }
  function irA(id: string, desdeTour = false) {
    const pr = presets[id]; if (!pr) return;
    if (!desdeTour && estado.tour) detenerTour();
    setVista({ edificio: pr.ed, piso: pr.piso });
    volar(pr.pos, pr.target, desdeTour ? 3.2 : 1.6);
    panel.querySelectorAll('li').forEach((x) => x.classList.toggle('on', (x as HTMLElement).dataset.id === id));
    mostrarFoto(id);
    history.replaceState(null, '', `#${id}`);
  }

  // ---------- comparador antes / después ----------
  const comp = $('#comparador');
  function mostrarFoto(id: string) {
    const f = FOTOS[id];
    if (!f) { comp.classList.remove('on'); return; }
    const antes = `${base}fotos-antes/${f.antes}.jpg`;
    const nombreD = f.despues || f.antes;
    const despues = `${base}fotos-despues/${nombreD}.jpg`;
    const soloAntes = () => {
      comp.innerHTML = `<div class="comp-cab"><strong>${f.nombre}</strong><span>Foto actual</span><button class="cerrar" aria-label="Cerrar">×</button></div><div class="comp-img"><img src="${antes}" alt="${f.nombre}, hoy"></div>`;
      comp.classList.add('on');
      comp.querySelector('.cerrar')!.addEventListener('click', () => comp.classList.remove('on'));
    };
    const conDespues = () => {
      comp.innerHTML = `<div class="comp-cab"><strong>${f.nombre}</strong><span>Hoy → así quedará</span><button class="cerrar" aria-label="Cerrar">×</button></div>
         <div class="comp-img"><img src="${despues}" alt="${f.nombre}, así quedará"><div class="comp-antes" style="clip-path:inset(0 50% 0 0)"><img src="${antes}" alt="${f.nombre}, hoy"></div><span class="comp-linea" style="left:50%"></span><input type="range" min="0" max="100" value="50" aria-label="Comparar"><span class="comp-l">Hoy</span><span class="comp-r">Así quedará</span></div>`;
      comp.classList.add('on');
      comp.querySelector('.cerrar')!.addEventListener('click', () => comp.classList.remove('on'));
      const r = comp.querySelector('input'); const a = comp.querySelector('.comp-antes') as HTMLElement | null; const ln = comp.querySelector('.comp-linea') as HTMLElement | null;
      if (r && a) r.addEventListener('input', () => { a.style.clipPath = `inset(0 ${100 - +r.value}% 0 0)`; if (ln) ln.style.left = `${r.value}%`; });
    };
    // detecta en tiempo de ejecución si ya existe la foto "así quedará"
    const probe = new Image();
    probe.onload = conDespues; probe.onerror = soloAntes; probe.src = despues;
  }

  // ---------- panel ----------
  const panel = $('#panel-lista');
  function li(id: string, nombre: string, detalle?: string) {
    const f = FOTOS[id];
    const tag = f ? `<i class="tag">${f.despues ? 'foto' : 'foto actual'}</i>` : '';
    return `<li data-id="${id}"><span>${nombre}${tag}</span>${detalle ? `<em>${detalle}</em>` : ''}</li>`;
  }
  let html = `<h3>Terreno</h3><ul>${li('sitio', 'Vista general', '2.500 m²')}${li('calle', 'Desde la calle', 'Entrada')}${li('gris-ext', RES ? 'Edificio gris' : 'Edificio de hospitalización', 'Exterior')}`;
  for (const ex of (vistas as any).exteriores) html += li(ex.id, ex.nombre);
  html += `</ul>`;
  for (const ed of (vistas as any).edificios) for (const p of ed.pisos) {
    html += `<h3>${ed.nombre} · ${p.nombre}</h3><ul>${li(`${ed.id}-p${p.n}`, 'Ver la planta', 'sin techo')}`;
    for (const r of p.rooms) html += li(r.id + '@' + ed.id, r.nombre, r.camas ? `${r.camas} ${r.camas === 1 ? 'cama' : 'camas'}` : (r.tipo === 'terraza' ? 'al aire libre' : ''));
    html += `</ul>`;
  }
  panel.innerHTML = html;
  panel.addEventListener('click', (e) => { const el = (e.target as HTMLElement).closest('li'); if (el) irA((el as HTMLElement).dataset.id!); });
  document.querySelectorAll('[data-modo]').forEach((b) => b.addEventListener('click', () => setModo((b as HTMLElement).dataset.modo as Modo)));
  document.querySelectorAll('[data-vista]').forEach((b) => b.addEventListener('click', () => {
    const [ed, p] = (b as HTMLElement).dataset.vista!.split(':');
    if (estado.tour) detenerTour();
    setVista({ edificio: ed === 'sitio' ? null : ed, piso: parseInt(p) });
  }));
  $('#btn-etiquetas').addEventListener('click', () => { estado.etiquetas = !estado.etiquetas; $('#btn-etiquetas').classList.toggle('on', estado.etiquetas); actualizarEtiquetas(); });
  $('#btn-panel').addEventListener('click', () => $('#panel').classList.toggle('abierto'));

  // ---------- recorrido guiado ----------
  const TOUR_RES: { id: string; texto: string; espera: number }[] = [
    { id: 'sitio', texto: 'Un terreno de 2.500 m² en Altos de San Cristóbal, David: la casa amarilla al frente y el edificio gris atrás.', espera: 4 },
    { id: 'calle', texto: 'La casa amarilla da a la C.A. La propiedad ya tiene cerca perimetral y portones eléctricos.', espera: 4 },
    { id: 'recepcion@amarilla', texto: 'Recepción 24 h en la entrada principal de la casa amarilla.', espera: 4 },
    { id: 'comedor@amarilla', texto: 'Comedor y TV: el área social de la casa amarilla.', espera: 4 },
    { id: 'terapia@amarilla', texto: 'Terapia con familiares y, detrás, los talleres de pintura, acuarela y costura.', espera: 4 },
    { id: 'suite@amarilla', texto: 'Cuatro cuartos privados, un huésped en cada uno. La suite tiene baño y clóset propios.', espera: 4 },
    { id: 'gris-ext', texto: 'El edificio gris es la parte asistencial: 22 camas en dos niveles.', espera: 4 },
    { id: 'hosp@gris', texto: 'Personas encamadas: 10 camas de hospital con barandales, luz sobre cada cama y estación de enfermería.', espera: 6 },
    { id: 'salon2@gris', texto: 'Salón amarillo: 4 camas para personas con movilidad reducida.', espera: 4 },
    { id: 'galeria@gris', texto: 'Área de coffee break en la terraza con verjas del piso alto.', espera: 5 },
    { id: 'salonB@gris', texto: 'Abajo, los salones de las personas que deambulan: 6 camas en este y 2 en el otro.', espera: 4 },
    { id: 'sitio', texto: 'Una residencia lista para operar. Solicita el expediente completo para inversionistas.', espera: 5 },
  ];
  const TOUR_MAQUETA: { id: string; texto: string; espera: number }[] = [
    { id: 'sitio', texto: 'Un terreno de 2.500 m² en Altos de San Cristóbal, David, con dos edificios, jardines y arboleda.', espera: 4 },
    { id: 'calle', texto: 'Cerca perimetral, portón eléctrico y entrada circular. Todo el campus ya cuenta con seguridad certificada.', espera: 4 },
    { id: 'recepcion@amarilla', texto: 'La casa principal recibe a residentes y familias: recepción, consultorio de salud, comedor y sala de terapia.', espera: 5 },
    { id: 'comedor@amarilla', texto: 'Comedor y sala de familiares, el corazón social de la residencia.', espera: 4 },
    { id: 'cto1@amarilla', texto: 'Tres cuartos privados para residentes independientes, con clóset y baño.', espera: 4 },
    { id: 'gris-ext', texto: 'El edificio de hospitalización: dos niveles, 24 camas y terraza.', espera: 4 },
    { id: 'hospitalizacion@gris', texto: 'Sala de hospitalización con 10 camas eléctricas, luz individual y estación de enfermería.', espera: 6 },
    { id: 'salon_2@gris', texto: 'Salón para residentes con movilidad reducida, con acceso directo a la terraza.', espera: 4 },
    { id: 'terraza@gris', texto: 'Terraza del piso alto: área recreativa al aire libre con vista a la arboleda.', espera: 5 },
    { id: 'refrigerios@gris', texto: 'Área de refrigerios y cocina de preparación de alimentos.', espera: 4 },
    { id: 'gazebo', texto: 'En el jardín central, gazebo para juegos de mesa y terapia acuática con agua tibia.', espera: 5 },
    { id: 'huerto', texto: 'Huerto cercado para siembra de hortalizas y flores, con su oficina de herramientas.', espera: 4 },
    { id: 'sitio', texto: 'Una residencia lista para abrir. Solicita el expediente completo para inversionistas.', espera: 5 },
  ];
  const TOUR = RES ? TOUR_RES : TOUR_MAQUETA;
  let tourIdx = 0; let tourTimer: number | null = null;
  const subt = $('#subtitulo');
  function pasoTour() {
    if (!estado.tour) return;
    const paso = TOUR[tourIdx % TOUR.length];
    irA(paso.id, true);
    subt.textContent = paso.texto; subt.classList.add('on');
    tourIdx++;
    tourTimer = window.setTimeout(pasoTour, (paso.espera + 3.2) * 1000);
  }
  function iniciarTour() {
    if (estado.modo !== 'orbita') setModo('orbita');
    estado.tour = true; tourIdx = 0;
    $('#btn-tour').classList.add('on'); $('#btn-tour').textContent = 'Detener';
    comp.classList.remove('on');
    actualizarEtiquetas();
    pasoTour();
  }
  function detenerTour() {
    estado.tour = false;
    if (tourTimer) clearTimeout(tourTimer);
    subt.classList.remove('on');
    $('#btn-tour').classList.remove('on'); $('#btn-tour').textContent = 'Recorrido guiado';
    actualizarEtiquetas();
  }
  $('#btn-tour').addEventListener('click', () => (estado.tour ? detenerTour() : iniciarTour()));

  // ---------- loop ----------
  const clock = new THREE.Clock();
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const maxFrames = parseInt(new URLSearchParams(location.search).get('frames') || '0');
  let nFrames = 0;
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
      camera.position.lerpVectors(tween.p0, tween.p1, k);
      orbit.target.lerpVectors(tween.t0, tween.t1, k);
      if (tween.t >= 1) { const f = tween.fin; tween = null; f?.(); }
    }
    if (estado.modo === 'orbita') {
      if (estado.tour && !tween) { orbit.target.y += 0; camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0); }
      orbit.update();
    } else if (estado.modo === 'recorrido') {
      const fwd = new THREE.Vector3(); camera.getWorldDirection(fwd); fwd.y = 0; fwd.normalize();
      const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0));
      const dir = new THREE.Vector3();
      if (keys.KeyW || keys.ArrowUp) dir.add(fwd);
      if (keys.KeyS || keys.ArrowDown) dir.sub(fwd);
      if (keys.KeyD || keys.ArrowRight) dir.add(right);
      if (keys.KeyA || keys.ArrowLeft) dir.sub(right);
      dir.addScaledVector(fwd, -joyVec.y).addScaledVector(right, joyVec.x);
      const speed = keys.ShiftLeft ? 4.5 : 2.0;
      vel.lerp(dir.lengthSq() > 0 ? dir.normalize().multiplyScalar(speed) : new THREE.Vector3(), 0.18);
      if (vel.lengthSq() > 0.0001) {
        ray.set(camera.position.clone().setY(camera.position.y - 0.4), vel.clone().normalize()); ray.far = 0.6;
        if (ray.intersectObjects(muros, false).length === 0) camera.position.addScaledVector(vel, dt);
      }
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? nivelDe(estado.vista.edificio) : 0;
      camera.position.y += (nivel + alturaOjos - camera.position.y) * 0.2;
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
    requestAnimationFrame(frame);
  }
  frame();

  window.addEventListener('resize', () => {
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h); composer.setSize(w, h); labels.setSize(w, h); gtao?.setSize(w, h); bloom.setSize(w, h);
  });

  if (CINE) { estado.modo = 'cine'; estado.etiquetas = false; orbit.enabled = false; container.classList.add('cine'); }
  else setModo('orbita');
  (window as any).__setProgreso = setProgreso;
  (window as any).__snap = () => { composer.render(); renderer.autoClear = false; renderer.render(mundo.escenaNubes, camera); renderer.autoClear = true; return renderer.domElement.toDataURL('image/jpeg', 0.85); };
  return { setModo, setVista, irA, setProgreso };
}
