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
import vistas from '../data/vistas.json';

type Modo = 'orbita' | 'recorrido';
type Vista = { edificio: string | null; piso: number };

const $ = (sel: string) => document.querySelector(sel) as HTMLElement;

export function iniciarVisor(container: HTMLElement) {
  // ---------- renderer ----------
  const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.78;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 800);
  camera.position.set(95, 55, 20);

  // ---------- cielo + sol ----------
  const sky = new Sky();
  sky.scale.setScalar(2000);
  scene.add(sky);
  const sunDir = new THREE.Vector3();
  const elev = 52, azim = 215;
  const phi = THREE.MathUtils.degToRad(90 - elev);
  const theta = THREE.MathUtils.degToRad(azim);
  sunDir.setFromSphericalCoords(1, phi, theta);
  const u = sky.material.uniforms;
  u.sunPosition.value.copy(sunDir);
  u.turbidity.value = 4; u.rayleigh.value = 1.6; u.mieCoefficient.value = 0.006; u.mieDirectionalG.value = 0.8;

  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene(); skyScene.add(sky.clone());
  scene.environment = pmrem.fromScene(skyScene as any, 0.02).texture;
  scene.environmentIntensity = 0.55;

  const sun = new THREE.DirectionalLight(0xfff3df, 2.3);
  sun.position.copy(sunDir).multiplyScalar(140).add(new THREE.Vector3(15, 0, -42));
  sun.target.position.set(15, 0, -42);
  sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  sun.shadow.camera.left = -70; sun.shadow.camera.right = 70;
  sun.shadow.camera.top = 70; sun.shadow.camera.bottom = -70;
  sun.shadow.camera.near = 20; sun.shadow.camera.far = 320;
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x5a6b45, 0.35));

  // ---------- post ----------
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const gtao = new GTAOPass(scene, camera, container.clientWidth, container.clientHeight);
  gtao.output = GTAOPass.OUTPUT.Default;
  (gtao as any).updateGtaoMaterial({ radius: 0.6, distanceExponent: 1, thickness: 1, scale: 1, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
  composer.addPass(gtao);
  composer.addPass(new OutputPass());
  composer.addPass(new SMAAPass());

  // ---------- modelo ----------
  const loader = new GLTFLoader();
  const draco = new DRACOLoader(); draco.setDecoderPath('/draco/');
  loader.setDRACOLoader(draco);
  const objetos: THREE.Object3D[] = [];
  const muros: THREE.Mesh[] = [];
  const estado: { modo: Modo; vista: Vista; cargado: boolean } = { modo: 'orbita', vista: { edificio: null, piso: 99 }, cargado: false };

  const barra = $('#carga');
  loader.load('/modelo/escena.glb', (gltf) => {
    gltf.scene.traverse((o: any) => {
      if (o.isMesh) {
        o.castShadow = true; o.receiveShadow = true;
        const m = o.material as THREE.MeshStandardMaterial;
        if (m) {
          m.envMapIntensity = 0.6;
          if (m.transparent && m.opacity < 1) { m.depthWrite = false; }
          if (m.alphaTest === 0 && m.map && (m.name.includes('follaje') || m.name.includes('fronda') || m.name.includes('arbusto'))) {
            m.alphaTest = 0.4; m.transparent = false; m.side = THREE.DoubleSide;
          }
          if (m.name.startsWith('vidrio')) { m.transparent = true; m.opacity = 0.3; m.roughness = 0.05; m.metalness = 0.1; m.depthWrite = false; }
        }
        if (o.name.includes('_muro')) muros.push(o);
      }
      objetos.push(o);
    });
    scene.add(gltf.scene);
    estado.cargado = true;
    barra.style.display = 'none';
    aplicarVista();
    const h = decodeURIComponent(location.hash.slice(1));
    if (h && presets[h]) { const pr = presets[h]; volar(pr.pos, pr.target, pr.ed, pr.piso); panel.querySelector(`li[data-id="${h}"]`)?.classList.add('on'); }
  }, (e) => {
    if (e.total) barra.style.width = `${Math.round((e.loaded / e.total) * 100)}%`;
  }, (err) => { console.error(err); barra.textContent = 'No se pudo cargar el modelo'; });

  // ---------- controles ----------
  const orbit = new OrbitControls(camera, renderer.domElement);
  orbit.target.set(15, 2, -42);
  orbit.enableDamping = true; orbit.dampingFactor = 0.06;
  orbit.maxPolarAngle = Math.PI / 2.02; orbit.minDistance = 4; orbit.maxDistance = 220;

  const plc = new PointerLockControls(camera, renderer.domElement);
  const keys: Record<string, boolean> = {};
  window.addEventListener('keydown', (e) => (keys[e.code] = true));
  window.addEventListener('keyup', (e) => (keys[e.code] = false));
  const vel = new THREE.Vector3();
  let alturaOjos = 1.65;
  const ray = new THREE.Raycaster();

  // joystick táctil simple
  const joy = $('#joy'); let joyVec = { x: 0, y: 0 };
  if (joy) {
    const base = joy.getBoundingClientRect();
    joy.addEventListener('touchmove', (e) => {
      const t = e.touches[0]; const r = joy.getBoundingClientRect();
      joyVec = { x: THREE.MathUtils.clamp((t.clientX - r.left - r.width / 2) / (r.width / 2), -1, 1), y: THREE.MathUtils.clamp((t.clientY - r.top - r.height / 2) / (r.height / 2), -1, 1) };
      e.preventDefault();
    }, { passive: false });
    joy.addEventListener('touchend', () => (joyVec = { x: 0, y: 0 }));
    void base;
  }

  // ---------- vista (edificio / piso) ----------
  function aplicarVista() {
    const { edificio, piso } = estado.vista;
    for (const o of objetos) {
      const ud = (o as any).userData || {};
      if (!ud.edificio) continue;
      if (edificio && ud.edificio === edificio) {
        const p = ud.piso ?? 1;
        const visible = p <= piso || (p === 99 && piso >= 99);
        // en recorrido, mantener cielo del piso actual pero quitar el superior
        o.visible = estado.modo === 'recorrido' ? (p <= piso || (ud.cielo && p === piso)) : visible;
        if (estado.modo === 'orbita' && ud.cielo && p === piso && piso < 99) o.visible = false;
      } else {
        o.visible = true;
      }
    }
  }

  function setVista(v: Vista) {
    estado.vista = v;
    aplicarVista();
    document.querySelectorAll('[data-vista]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.vista === `${v.edificio ?? 'sitio'}:${v.piso}`));
  }

  function setModo(m: Modo) {
    estado.modo = m;
    orbit.enabled = m === 'orbita';
    if (m === 'recorrido') {
      // posicionar a nivel de ojos cerca del objetivo actual
      const t = orbit.target.clone();
      const dir = camera.position.clone().sub(t).setY(0).normalize();
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? 3.25 : 0;
      camera.position.copy(t).addScaledVector(dir, 2.5).setY(nivel + alturaOjos);
      camera.lookAt(t.x, nivel + 1.4, t.z);
      $('#hint').textContent = 'Toca o haz clic para mirar con el mouse · WASD / flechas para caminar · Shift corre · Esc suelta el mouse';
    } else {
      plc.unlock();
      $('#hint').textContent = 'Arrastra para girar · rueda para acercar · elige un espacio en el panel';
    }
    aplicarVista();
    document.querySelectorAll('[data-modo]').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.modo === m));
  }

  renderer.domElement.addEventListener('click', () => { if (estado.modo === 'recorrido' && !plc.isLocked) plc.lock(); });

  // ---------- volar a un punto ----------
  let tween: { t: number; p0: THREE.Vector3; p1: THREE.Vector3; t0: THREE.Vector3; t1: THREE.Vector3 } | null = null;
  function volar(pos: number[], target: number[], ed: string | null, piso: number) {
    setVista({ edificio: ed, piso });
    if (estado.modo === 'recorrido') {
      camera.position.set(pos[0], pos[1], pos[2]);
      camera.lookAt(target[0], target[1], target[2]);
      return;
    }
    tween = { t: 0, p0: camera.position.clone(), p1: new THREE.Vector3(...pos), t0: orbit.target.clone(), t1: new THREE.Vector3(...target) };
  }

  // ---------- panel ----------
  const panel = $('#panel-lista');
  function liHtml(id: string, nombre: string, detalle: string) {
    return `<li data-id="${id}"><span>${nombre}</span>${detalle ? `<em>${detalle}</em>` : ''}</li>`;
  }
  const presets: Record<string, { pos: number[]; target: number[]; ed: string | null; piso: number }> = {};
  let html = '';
  html += `<h3>Terreno</h3><ul>`;
  presets['sitio'] = { pos: [95, 55, 20], target: [15, 2, -42], ed: null, piso: 99 };
  html += liHtml('sitio', 'Vista general', '2.500 m²');
  presets['calle'] = { pos: [44, 1.9, -44], target: [14, 3, -61], ed: null, piso: 99 };
  html += liHtml('calle', 'Desde la calle', 'Entrada principal');
  for (const ex of (vistas as any).exteriores) {
    presets[ex.id] = { pos: ex.cam, target: ex.centro, ed: null, piso: 99 };
    html += liHtml(ex.id, ex.nombre, '');
  }
  html += `</ul>`;
  for (const ed of (vistas as any).edificios) {
    for (const p of ed.pisos) {
      html += `<h3>${ed.nombre} · ${p.nombre}</h3><ul>`;
      // vista de planta
      const key = `${ed.id}-p${p.n}`;
      const c = p.rooms.reduce((a: number[], r: any) => [a[0] + r.centro[0], a[1] + r.centro[1], a[2] + r.centro[2]], [0, 0, 0]).map((v: number) => v / p.rooms.length);
      presets[key] = { pos: [c[0] + 14, c[1] + 22, c[2] + 18], target: c, ed: ed.id, piso: p.n };
      html += liHtml(key, 'Ver la planta', 'sin techo');
      for (const r of p.rooms) {
        presets[r.id + '@' + ed.id] = { pos: r.cam, target: r.centro, ed: ed.id, piso: p.n };
        html += liHtml(r.id + '@' + ed.id, r.nombre, r.camas ? `${r.camas} ${r.camas === 1 ? 'cama' : 'camas'}` : (r.tipo === 'terraza' ? 'al aire libre' : ''));
      }
      html += `</ul>`;
    }
  }
  panel.innerHTML = html;
  panel.addEventListener('click', (e) => {
    const li = (e.target as HTMLElement).closest('li'); if (!li) return;
    const pr = presets[li.dataset.id!]; if (!pr) return;
    panel.querySelectorAll('li').forEach((x) => x.classList.remove('on')); li.classList.add('on');
    if (pr.ed) {
      // entrar a una sala: cámara dentro a altura de ojos en órbita cercana
      volar(pr.pos, pr.target, pr.ed, pr.piso);
    } else {
      volar(pr.pos, pr.target, null, 99);
    }
  });

  document.querySelectorAll('[data-modo]').forEach((b) => b.addEventListener('click', () => setModo((b as HTMLElement).dataset.modo as Modo)));
  document.querySelectorAll('[data-vista]').forEach((b) => b.addEventListener('click', () => {
    const [ed, p] = (b as HTMLElement).dataset.vista!.split(':');
    setVista({ edificio: ed === 'sitio' ? null : ed, piso: parseInt(p) });
  }));

  // ---------- loop ----------
  const clock = new THREE.Clock();
  const maxFrames = parseInt(new URLSearchParams(location.search).get('frames') || '0');
  let nFrames = 0;
  function frame() {
    nFrames++;
    if (maxFrames && nFrames > maxFrames) { (window as any).__done = true; return; }
    const dt = Math.min(clock.getDelta(), 0.05);
    if (tween) {
      tween.t = Math.min(1, tween.t + dt / 1.4);
      const k = tween.t < 0.5 ? 2 * tween.t * tween.t : -1 + (4 - 2 * tween.t) * tween.t;
      camera.position.lerpVectors(tween.p0, tween.p1, k);
      orbit.target.lerpVectors(tween.t0, tween.t1, k);
      if (tween.t >= 1) tween = null;
    }
    if (estado.modo === 'orbita') {
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
      vel.lerp(dir.normalize().multiplyScalar(dir.lengthSq() > 0 ? speed : 0), 0.18);
      // colisión sencilla contra muros
      if (vel.lengthSq() > 0.0001) {
        ray.set(camera.position.clone().setY(camera.position.y - 0.4), vel.clone().normalize());
        ray.far = 0.6;
        const hit = ray.intersectObjects(muros, false);
        if (hit.length === 0) camera.position.addScaledVector(vel, dt);
      }
      // nivel del piso
      const nivel = estado.vista.edificio && estado.vista.piso === 2 ? 3.25 : 0;
      camera.position.y += (nivel + alturaOjos - camera.position.y) * 0.2;
      camera.position.x = THREE.MathUtils.clamp(camera.position.x, -6, 36);
      camera.position.z = THREE.MathUtils.clamp(camera.position.z, -92, 8);
    }
    composer.render();
    requestAnimationFrame(frame);
  }
  frame();

  window.addEventListener('resize', () => {
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h); composer.setSize(w, h); gtao.setSize(w, h);
  });

  setModo('orbita');
  (window as any).__snap = () => { composer.render(); return renderer.domElement.toDataURL('image/jpeg', 0.85); };
  return { setModo, setVista, volar };
}
