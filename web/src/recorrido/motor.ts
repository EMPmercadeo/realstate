/*
  Motor del recorrido cinematográfico por scroll.
  Adaptado del scrub-engine de scroll-world (MIT, cyw 2026) a TypeScript y al
  esquema "hoy → así quedará" de este proyecto.

  Modo foto (por defecto): cada parada muestra la foto real; al avanzar el scroll la
  cámara se acerca (push-in) y la imagen "después" se revela sobre la real.
  Modo clip: si existe /clips/<id>.mp4 el video se carga como Blob y se recorre
  con currentTime según el scroll (como las páginas de producto de Apple).
*/
import type { Parada } from '../data/recorrido';

interface Seg extends Parada {
  idx: number;
  start: number; end: number; w: number;
  el: HTMLDivElement; imgA: HTMLImageElement; imgD: HTMLImageElement | null; pill: HTMLSpanElement;
  video: HTMLVideoElement | null; cargando: boolean; listo: boolean; conClip: boolean;
  cur: number; target: number; visible: boolean; tieneDespues: boolean; cargada: boolean;
}

export interface Opciones {
  base?: string;             // prefijo de rutas ('/' en el sitio, './' en el artefacto)
  diveScroll?: number;       // alturas de pantalla por parada
  crossfade?: number;        // ancho del fundido entre paradas (en vh)
  onParada?: (i: number) => void;
  existe?: (ruta: string) => boolean;   // manifiesto de archivos opcionales (evita sondear con 404)
}

const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => { x = clamp(x); return x * x * (3 - 2 * x); };

export function montarRecorrido(root: HTMLElement, paradas: Parada[], op: Opciones = {}) {
  const base = (op.base ?? '/').replace(/\/$/, '');
  const R = (p: string) => base + p;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = matchMedia('(hover: none) and (pointer: coarse)').matches;
  const smallMQ = matchMedia('(max-width: 860px)');
  const esMovil = () => coarse || smallMQ.matches;
  const DIVE = op.diveScroll ?? 1.35;
  const FADE = op.crossfade ?? 0.12;
  const N = paradas.length;

  const stage = root.querySelector<HTMLDivElement>('.rc-stage')!;
  const escenas = root.querySelector<HTMLDivElement>('.rc-escenas')!;
  const copias = Array.from(root.querySelectorAll<HTMLElement>('.rc-copy'));
  const puntos = Array.from(root.querySelectorAll<HTMLButtonElement>('.rc-ruta button'));
  const navItems = Array.from(root.querySelectorAll<HTMLButtonElement>('.rc-nav button'));
  const barra = root.querySelector<HTMLElement>('.rc-barra span')!;
  const hint = root.querySelector<HTMLElement>('.rc-hint')!;

  // ---- escenas ----
  const SEGS: Seg[] = paradas.map((p, i) => {
    const el = document.createElement('div'); el.className = 'rc-escena';
    el.style.setProperty('--acento', p.acento || '#c99a3c');
    const imgA = document.createElement('img'); imgA.className = 'rc-antes'; imgA.alt = ''; imgA.decoding = 'async';
    const imgD = p.despues ? document.createElement('img') : null;
    if (imgD) { imgD.className = 'rc-despues'; imgD.alt = ''; imgD.decoding = 'async'; }
    if (p.posicion) { imgA.style.objectPosition = p.posicion; if (imgD) imgD.style.objectPosition = p.posicion; }
    const pill = document.createElement('span'); pill.className = 'rc-pill'; pill.textContent = 'Hoy';
    el.append(imgA); if (imgD) el.append(imgD); el.append(pill); escenas.append(el);
    return { ...p, idx: i, start: 0, end: 0, w: p.scroll || DIVE, el, imgA, imgD, pill, video: null,
      cargando: false, listo: false, conClip: false, cur: 0, target: 0, visible: false, tieneDespues: false, cargada: false };
  });

  function cargarImagenes(s: Seg) {
    if (s.cargada) return; s.cargada = true;
    s.imgA.src = R(s.antes);
    if (s.imgD && s.despues && op.existe && !op.existe(s.despues)) { s.imgD.remove(); s.imgD = null; }
    else if (s.imgD && s.despues) {
      const probe = new Image();
      probe.onload = () => { s.imgD!.src = probe.src; s.tieneDespues = true; s.el.classList.add('con-despues'); };
      probe.onerror = () => { s.imgD!.remove(); s.imgD = null; };
      probe.src = R(s.despues);
    }
  }

  function cargarClip(s: Seg) {
    if (reduce || s.cargando) return;
    s.cargando = true;
    const ruta = `/clips/${s.id}${esMovil() ? '-m' : ''}.mp4`;
    if (op.existe && !op.existe(ruta)) return;
    const url = R(ruta);
    fetch(url, { headers: { Range: 'bytes=0-0' } }).then(r => {
      const tipo = r.headers.get('content-type') || '';
      if (!r.ok || !tipo.startsWith('video')) throw new Error('sin clip');
      return fetch(R(`/clips/${s.id}${esMovil() ? '-m' : ''}.mp4`)).then(r2 => r2.blob());
    }).then(blob => {
      const v = document.createElement('video');
      v.className = 'rc-video'; v.muted = true; v.playsInline = true; v.preload = 'auto';
      v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
      v.src = URL.createObjectURL(blob);
      v.addEventListener('loadedmetadata', () => { s.listo = true; leer(); });
      v.addEventListener('seeked', () => s.el.classList.add('con-clip'), { once: true });
      v.addEventListener('loadeddata', () => { try { v.pause(); } catch {} if (userReady) prime(v); });
      s.el.append(v); s.video = v; s.conClip = true;
    }).catch(() => { /* sin clip: modo foto */ });
  }

  // ---- geometría ----
  let vh = innerHeight, totalW = 0, activo = -1, ticking = false, anchoLayout = innerWidth, top0 = 0;
  function layout() {
    vh = innerHeight; anchoLayout = innerWidth;
    let off = 0;
    SEGS.forEach(s => { s.start = off * vh; off += s.w; s.end = off * vh; });
    totalW = off;
    root.style.height = `${(totalW + 1) * 100}vh`;
    top0 = root.getBoundingClientRect().top + scrollY;
    leer();
  }

  function irA(i: number) {
    const s = SEGS[i];
    const y = top0 + s.start + (s.end - s.start) * 0.55;
    const lenis = (window as any).__lenis;
    if (lenis) lenis.scrollTo(y, { duration: reduce ? 0 : 1.6 });
    else scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
  }
  puntos.forEach((b, i) => b.addEventListener('click', () => irA(i)));
  navItems.forEach((b, i) => b.addEventListener('click', () => irA(i)));

  function leer() {
    const y = scrollY - top0;
    const fade = FADE * vh;
    let ci = 0;
    for (let i = 0; i < N; i++) if (y >= SEGS[i].start) ci = i;
    const fin = y > totalW * vh + vh * 0.5;
    stage.classList.toggle('rc-fin', fin);

    for (let i = 0; i < N; i++) {
      const s = SEGS[i];
      if (y > s.start - 2.2 * vh && y < s.end + 2.2 * vh) { cargarImagenes(s); cargarClip(s); }
      const local = clamp((y - s.start) / (s.end - s.start));
      s.target = local;
      let fuera = 0;
      if (y < s.start) fuera = s.start - y; else if (y > s.end) fuera = y - s.end;
      const op = smooth(1 - fuera / fade);
      s.el.style.opacity = String(op); s.visible = op > 0.001;
      s.el.style.zIndex = i === ci ? '20' : String(10 + Math.round(op * 5));
      if (!s.conClip || !s.listo) {
        const sc = reduce ? 1 : 1.04 + local * 0.15;
        const tr = `scale(${sc.toFixed(4)}) translateY(${((0.5 - local) * 1.5).toFixed(2)}%)`;
        s.imgA.style.transform = tr;
        if (s.imgD) {
          s.imgD.style.transform = tr;
          const rev = smooth((local - 0.3) / 0.32);
          s.imgD.style.opacity = String(s.tieneDespues ? rev : 0);
          const despues = s.tieneDespues && rev > 0.5;
          s.pill.textContent = despues ? 'Así quedará' : 'Hoy';
          s.pill.classList.toggle('es-despues', despues);
        }
      }
    }

    for (let i = 0; i < N; i++) {
      const s = SEGS[i];
      const pr = clamp((y - s.start) / (s.end - s.start));
      const antes = y < s.start, despues = y > s.end;
      let cop: number;
      if (i === 0) cop = despues ? 0 : smooth(1 - pr / 0.62);
      else if (i === N - 1) cop = antes ? 0 : (fin ? 0 : smooth(pr / 0.4));
      else cop = antes || despues ? 0 : smooth(1 - Math.abs(pr - 0.5) / 0.5);
      const c = copias[i];
      c.style.opacity = String(cop);
      c.style.transform = reduce ? 'none' : `translateY(${((0.5 - pr) * 4).toFixed(2)}vh)`;
      c.style.pointerEvents = cop > 0.5 ? 'auto' : 'none';
    }

    if (ci !== activo) {
      activo = ci;
      puntos.forEach((d, k) => d.classList.toggle('activo', k === ci));
      navItems.forEach((d, k) => d.classList.toggle('activo', k === ci));
      root.style.setProperty('--acento', SEGS[ci].acento || '#c99a3c');
      op.onParada?.(ci);
    }
    barra.style.transform = `scaleX(${clamp(y / (totalW * vh))})`;
    hint.style.opacity = String(clamp(1 - y / (0.5 * vh)));
    ticking = false;
  }

  function raf() {
    const eps = esMovil() ? 0.02 : 0.008;
    for (const s of SEGS) {
      if (!s.conClip || !s.listo || !s.video) continue;
      if (s.video.seeking) continue;
      if (!s.visible && Math.abs(s.cur - s.target) < 0.002) continue;
      s.cur += (s.target - s.cur) * (reduce ? 1 : 0.18);
      const t = clamp(s.cur, 0, 0.999) * (s.video.duration || 1);
      if (Math.abs(s.video.currentTime - t) > eps) { try { s.video.currentTime = t; } catch {} }
    }
    requestAnimationFrame(raf);
  }

  let userReady = false;
  function prime(v: HTMLVideoElement | null) {
    if (!esMovil() || !v) return;
    try { const p = v.play(); if (p && p.then) p.then(() => { try { v.pause(); } catch {} }).catch(() => {}); } catch {}
  }
  const primerGesto = () => { if (userReady) return; userReady = true; SEGS.forEach(s => prime(s.video)); };
  addEventListener('pointerdown', primerGesto, { once: true, passive: true });
  addEventListener('touchstart', primerGesto, { once: true, passive: true });

  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(leer); } }, { passive: true });
  addEventListener('resize', () => { if (coarse && innerWidth === anchoLayout) return; layout(); });
  addEventListener('orientationchange', layout);
  addEventListener('load', layout);
  layout();
  requestAnimationFrame(raf);

  return { irA, layout };
}
