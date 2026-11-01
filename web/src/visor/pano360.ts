// Visor de panorámicas 360° (equirectangulares renderizadas con Cycles: blender/panoramas.py).
// Se abre a pantalla completa sobre la página: arrastrar para mirar, rueda o pellizco para acercar,
// flechas del teclado, Esc para cerrar. Gira solo y despacio hasta que el visitante toca.
import * as THREE from 'three';

export interface Pano { id: string; nombre: string; archivo: string; mini?: string }

let abierto: (() => void) | null = null;

export function abrir360(p: Pano, lista: Pano[] = [], base = '/') {
  if (abierto) abierto();
  const url = (s: string) => base.replace(/\/$/, '') + s;
  const raiz = document.createElement('div');
  raiz.className = 'p360';
  raiz.setAttribute('role', 'dialog');
  raiz.setAttribute('aria-label', `Vista 360°: ${p.nombre}`);
  raiz.innerHTML = `
    <div class="p360-cab">
      <div><span class="p360-sup">Vista 360° · render del proyecto</span><strong class="p360-tit"></strong></div>
      <button class="p360-cerrar" aria-label="Cerrar">×</button>
    </div>
    <div class="p360-carga"><span></span>Cargando la vista…</div>
    <p class="p360-ayuda">Arrastra para mirar alrededor · rueda o pellizco para acercar</p>
    <nav class="p360-lista" aria-label="Otras vistas 360°"></nav>`;
  document.body.appendChild(raiz);
  document.documentElement.classList.add('p360-on');
  const tit = raiz.querySelector('.p360-tit') as HTMLElement;
  const carga = raiz.querySelector('.p360-carga') as HTMLElement;
  const ayuda = raiz.querySelector('.p360-ayuda') as HTMLElement;
  const nav = raiz.querySelector('.p360-lista') as HTMLElement;

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  raiz.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 100);
  const geo = new THREE.SphereGeometry(50, 96, 64);
  geo.scale(-1, 1, 1);                       // se ve por dentro
  const mat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const esfera = new THREE.Mesh(geo, mat);
  // la vista inicial (centro de la imagen) queda hacia -z
  esfera.rotation.y = -Math.PI / 2;
  scene.add(esfera);

  let lon = 0, lat = 0, fov = innerWidth < innerHeight ? 85 : 72;
  let auto = true, arrastrando = false;
  let px = 0, py = 0, plon = 0, plat = 0, distPinza = 0, fovPinza = fov;
  const loader = new THREE.TextureLoader();

  function cargar(q: Pano) {
    tit.textContent = q.nombre;
    carga.classList.add('on');
    loader.load(url(q.archivo), (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = renderer.capabilities.getMaxAnisotropy();
      t.minFilter = THREE.LinearMipmapLinearFilter;
      const vieja = mat.map; mat.map = t; mat.needsUpdate = true; vieja?.dispose();
      carga.classList.remove('on');
      lon = 0; lat = 0; auto = true;
    }, undefined, () => { carga.innerHTML = 'No se pudo cargar la vista.'; });
    nav.querySelectorAll('button').forEach((b) => b.classList.toggle('on', (b as HTMLElement).dataset.id === q.id));
  }
  if (lista.length > 1) {
    nav.innerHTML = lista.map((q) => `<button data-id="${q.id}" style="${q.mini ? `background-image:url('${url(q.mini)}')` : ''}"><span>${q.nombre}</span></button>`).join('');
    nav.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
      const q = lista.find((x) => x.id === (b as HTMLElement).dataset.id); if (q) cargar(q);
    }));
  }
  cargar(p);

  function tamano() {
    renderer.setSize(innerWidth, innerHeight);
    camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  }
  tamano();
  addEventListener('resize', tamano);

  const el = renderer.domElement;
  el.style.touchAction = 'none';
  const tocar = () => { auto = false; ayuda.classList.add('fuera'); };
  el.addEventListener('pointerdown', (e) => {
    arrastrando = true; tocar(); px = e.clientX; py = e.clientY; plon = lon; plat = lat; el.setPointerCapture(e.pointerId);
  });
  el.addEventListener('pointermove', (e) => {
    if (!arrastrando) return;
    const k = fov / innerHeight;             // grados por pixel según el acercamiento
    lon = plon - (e.clientX - px) * k; lat = plat + (e.clientY - py) * k;
  });
  const soltar = () => { arrastrando = false; };
  el.addEventListener('pointerup', soltar); el.addEventListener('pointercancel', soltar);
  el.addEventListener('wheel', (e) => { e.preventDefault(); tocar(); fov = THREE.MathUtils.clamp(fov + e.deltaY * 0.04, 30, 95); }, { passive: false });
  el.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) { arrastrando = false; distPinza = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY); fovPinza = fov; }
  }, { passive: true });
  el.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2 && distPinza) {
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      fov = THREE.MathUtils.clamp(fovPinza * distPinza / d, 30, 95);
    }
  }, { passive: true });
  const teclas = (e: KeyboardEvent) => {
    if (e.key === 'Escape') cerrar();
    else if (e.key === 'ArrowLeft') { tocar(); lon -= 6; }
    else if (e.key === 'ArrowRight') { tocar(); lon += 6; }
    else if (e.key === 'ArrowUp') { tocar(); lat += 4; }
    else if (e.key === 'ArrowDown') { tocar(); lat -= 4; }
  };
  addEventListener('keydown', teclas);

  let vivo = true; let t0 = performance.now();
  const v = new THREE.Vector3();
  function cuadro(t: number) {
    if (!vivo) return;
    const dt = Math.min(0.05, (t - t0) / 1000); t0 = t;
    if (auto) lon += dt * 2.2;
    lat = THREE.MathUtils.clamp(lat, -80, 80);
    camera.fov += (fov - camera.fov) * 0.2; camera.updateProjectionMatrix();
    const phi = THREE.MathUtils.degToRad(90 - lat), th = THREE.MathUtils.degToRad(lon);
    v.set(Math.sin(phi) * Math.sin(th), Math.cos(phi), -Math.sin(phi) * Math.cos(th));
    camera.lookAt(v);
    renderer.render(scene, camera);
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);

  function cerrar() {
    vivo = false;
    removeEventListener('resize', tamano); removeEventListener('keydown', teclas);
    mat.map?.dispose(); mat.dispose(); geo.dispose(); renderer.dispose();
    raiz.remove(); document.documentElement.classList.remove('p360-on');
    abierto = null;
  }
  (raiz.querySelector('.p360-cerrar') as HTMLElement).addEventListener('click', cerrar);
  abierto = cerrar;
}
