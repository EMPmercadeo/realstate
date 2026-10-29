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
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import vistas from '../data/vistas.json';
import fotos from '../data/fotos.json';

type Modo = 'orbita' | 'recorrido';
type Vista = { edificio: string | null; piso: number };
type Preset = { pos: number[]; target: number[]; ed: string | null; piso: number; nombre: string; detalle?: string };

const $ = (sel: string) => document.querySelector(sel) as HTMLElement;
const FOTOS = fotos as Record<string, { nombre: string; antes: string; despues: string | null }>;
const MOVIL = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || window.innerWidth < 820;
const NIVEL = 3.25;

export function iniciarVisor(container: HTMLElement) {
  const base = document.body.dataset.base || '/';

  // ---------- renderer ----------
  const renderer = new THREE.WebGLRenderer({ antialias: MOVIL, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, MOVIL ? 1.5 : 1.75));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.8;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  labels.setSize(container.clientWidth, container.clientHeight);
  labels.domElement.className = 'etiquetas';
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 900);
  camera.position.set(110, 70, 30);

  // ---------- cielo + sol ----------
  const sky = new Sky();
  sky.scale.setScalar(2000);
  scene.add(sky);
  const sunDir = new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - 52), THREE.MathUtils.degToRad(215));
  const u = sky.material.uniforms;
  u.sunPosition.value.copy(sunDir);
  u.turbidity.value = 4; u.rayleigh.value = 1.6; u.mieCoefficient.value = 0.006; u.mieDirectionalG.value = 0.8;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene(); skyScene.add(sky.clone());
  scene.environment = pmrem.fromScene(skyScene as any, 0.02).texture;
  scene.environmentIntensity = 0.5;

  const centro = new THREE.Vector3(15, 0, -42);
  const sun = new THREE.DirectionalLight(0xfff3df, 2.3);
  sun.position.copy(sunDir).multiplyScalar(140).add(centro);
  sun.target.position.copy(centro);
  sun.castShadow = true;
  const sm = MOVIL ? 2048 : 4096;
  sun.shadow.mapSize.set(sm, sm);
  sun.shadow.camera.left = -70; sun.shadow.camera.right = 70; sun.shadow.camera.top = 70; sun.shadow.camera.bottom = -70;
  sun.shadow.camera.near = 20; sun.shadow.camera.far = 320;
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x5a6b45, 0.4));
  // luz de relleno que acompaña a la cámara dentro de los edificios
  const relleno = new THREE.PointLight(0xfff4e0, 0, 14, 1.6);
  scene.add(relleno);

  // ---------- post ----------
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  let gtao: GTAOPass | null = null;
  if (!MOVIL) {
    gtao = new GTAOPass(scene, camera, container.clientWidth, container.clientHeight);
    gtao.output = GTAOPass.OUTPUT.Default;
    (gtao as any).updateGtaoMaterial({ radius: 0.6, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
    composer.addPass(gtao);
  }
  composer.addPass(new OutputPass());
  if (!MOVIL) composer.addPass(new SMAAPass());

  // ---------- estado ----------
  const objetos: THREE.Object3D[] = [];
  const muros: THREE.Mesh[] = [];
  const estado = { modo: 'orbita' as Modo, vista: { edificio: null as string | null, piso: 99 }, cargado: false, etiquetas: true, tour: false };

  // ---------- presets de cámara ----------
  const presets: Record<string, Preset> = {};
  presets['sitio'] = { pos: [110, 70, 30], target: [15, 2, -42], ed: null, piso: 99, nombre: 'Vista general', detalle: 'Terreno de 2.500 m² con dos edificios' };
  presets['calle'] = { pos: [44, 1.9, -44], target: [14, 3, -61], ed: null, piso: 99, nombre: 'Desde la calle', detalle: 'Cerca perimetral, portón eléctrico y entrada circular' };
  presets['gris-ext'] = { pos: [42, 2.2, -2], target: [12, 4, -18], ed: null, piso: 99, nombre: 'Edificio de hospitalización', detalle: 'Dos niveles, terraza y acceso accesible' };
  for (const ex of (vistas as any).exteriores) presets[ex.id] = { pos: ex.cam, target: ex.centro, ed: null, piso: 99, nombre: ex.nombre };
  for (const ed of (vistas as any).edificios) {
    for (const p of ed.pisos) {
      const c = p.rooms.reduce((a: number[], r: any) => [a[0] + r.centro[0], a[1] + r.centro[1], a[2] + r.centro[2]], [0, 0, 0]).map((v: number) => v / p.rooms.length);
      presets[`${ed.id}-p${p.n}`] = { pos: [c[0] + 14, c[1] + 22, c[2] + 18], target: c, ed: ed.id, piso: p.n, nombre: `${ed.nombre} · ${p.nombre}`, detalle: 'Vista de planta sin techo' };
      for (const r of p.rooms) presets[r.id + '@' + ed.id] = { pos: r.cam, target: r.centro, ed: ed.id, piso: p.n, nombre: r.nombre, detalle: r.camas ? `${r.camas} ${r.camas === 1 ? 'cama' : 'camas'}` : undefined };
    }
  }

  // ---------- carga ----------
  const loader = new GLTFLoader();
  const draco = new DRACOLoader(); draco.setDecoderPath(`${base}draco/`);
  loader.setDRACOLoader(draco);
  const pantalla = $('#pantalla-carga');
  const barra = $('#carga');
  const pct = $('#carga-pct');
  loader.load(`${base}modelo/escena.glb`, (gltf) => {
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
      }
      objetos.push(o);
    });
    scene.add(gltf.scene);
    estado.cargado = true;
    crearEtiquetas();
    aplicarVista();
    pct.textContent = '100 %';
    $('#btn-entrar').removeAttribute('disabled');
    $('#btn-entrar').textContent = 'Entrar al recorrido';
    const h = decodeURIComponent(location.hash.slice(1));
    if (h && presets[h]) { setTimeout(() => irA(h), 300); }
  }, (e) => {
    if (e.total) { const p = Math.round((e.loaded / e.total) * 100); barra.style.width = `${p}%`; pct.textContent = `${p} %`; }
  }, (err) => { console.error(err); pct.textContent = 'No se pudo cargar el modelo. Recarga la página.'; });
  $('#btn-entrar').addEventListener('click', () => { pantalla.classList.add('oculta'); if (!location.hash) iniciarTour(); });

  // ---------- controles ----------
  const orbit = new OrbitControls(camera, renderer.domElement);
  orbit.target.copy(centro).setY(2);
  orbit.enableDamping = true; orbit.dampingFactor = 0.06;
  orbit.maxPolarAngle = Math.PI / 2.02; orbit.minDistance = 2.5; orbit.maxDistance = 240;
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
    mk('calle', 'Entrada principal', [30, 1, -60], null, 99, false);
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
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? NIVEL : 0;
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
  let html = `<h3>Terreno</h3><ul>${li('sitio', 'Vista general', '2.500 m²')}${li('calle', 'Desde la calle', 'Entrada')}${li('gris-ext', 'Edificio de hospitalización', 'Exterior')}`;
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
  const TOUR: { id: string; texto: string; espera: number }[] = [
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
  const maxFrames = parseInt(new URLSearchParams(location.search).get('frames') || '0');
  let nFrames = 0;
  function frame() {
    nFrames++;
    if (maxFrames && nFrames > maxFrames) { (window as any).__done = true; return; }
    const dt = Math.min(clock.getDelta(), 0.05);
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
    } else {
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
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? NIVEL : 0;
      camera.position.y += (nivel + alturaOjos - camera.position.y) * 0.2;
      camera.position.x = THREE.MathUtils.clamp(camera.position.x, -6, 36);
      camera.position.z = THREE.MathUtils.clamp(camera.position.z, -92, 8);
    }
    // relleno interior: solo dentro de un edificio
    const dentro = !!estado.vista.edificio && (estado.modo === 'recorrido' || camera.position.y < 7);
    relleno.intensity += ((dentro ? 6 : 0) - relleno.intensity) * 0.1;
    relleno.position.copy(camera.position).y += 0.6;
    composer.render();
    labels.render(scene, camera);
    requestAnimationFrame(frame);
  }
  frame();

  window.addEventListener('resize', () => {
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h); composer.setSize(w, h); labels.setSize(w, h); gtao?.setSize(w, h);
  });

  setModo('orbita');
  (window as any).__snap = () => { composer.render(); return renderer.domElement.toDataURL('image/jpeg', 0.85); };
  return { setModo, setVista, irA };
}
