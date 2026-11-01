# Plan GPU (RTX 3080): realismo + rapidez en cualquier web

La idea: el navegador **no** dibuja el 3D en vivo. Blender renderiza el sobrevuelo completo con Cycles
(fotorrealista, GPU OptiX) y la portada reproduce ese video controlado por el scroll. Corre fluido en
cualquier celular porque es video. El 3D en vivo queda como respaldo (`/?3d`) y para `/recorrido`.

## 1. Instalar en tu PC (una vez)

1. **Blender** (gratis): https://www.blender.org/download/ → instala la versión actual (4.x o 5.x).
   Luego en PowerShell comprueba: `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -v`
   (ajusta la ruta a tu versión).
2. **ffmpeg** (para armar el video): `winget install Gyan.FFmpeg` y reabre PowerShell. Comprueba `ffmpeg -version`.
3. **Node** ya lo tienes (`npm`). Claude Code ya lo tienes.
4. (Opcional, mejora grande de realismo) Descarga a `realstate\assets\pbr\` estas texturas 2K de
   https://ambientcg.com (gratis, sin registro): `Grass004`, `Ground037`, `Gravel022`, `Asphalt012`,
   `Concrete034`, `PaintedPlaster017`, `RoofingTiles012`, `MetalPlates006`, `Plaster001`.
   Y a `realstate\assets\hdri\` un cielo de https://polyhaven.com/hdris (2K .hdr): `kloofendal_48d_partly_cloudy_puresky`
   o `belfast_sunset_puresky`. Claude Code los conecta (ver tareas abajo).

## 2. Probar el render (5 minutos)

En PowerShell, dentro de `realstate`:

```
$b = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"   # tu ruta
& $b -b -P blender\cine_render.py -- --preview
```

Debe imprimir `GPU: OPTIX [...]`, renderizar 60 cuadros de 640 px en `build\cine\` y crear
`web\public\clips\sobrevuelo.mp4` + `sobrevuelo-m.mp4`. Si imprime `sin GPU compatible, CPU`, dímelo.

Luego `cd web; npm run dev` y abre http://localhost:4321 → la portada ya reproduce el video por scroll
(si quieres ver el 3D en vivo: http://localhost:4321/?3d).

## 3. Render final (≈ 1 h en la 3080)

```
& $b -b -P blender\cine_render.py -- --w 1920 --samples 128 --frames 720
```

720 cuadros = 30 s a 24 fps. Se puede interrumpir y reanudar (no repite cuadros hechos). Para 1080p
final usa `--w 1920`; para pruebas `--w 1280 --samples 64`.

## 4. Prompt-goal para Claude Code (pegar en PowerShell dentro de `realstate`)

```
Lee docs/PLAN-GPU.md, docs/ORQUESTACION.md y docs/estado.md. Tengo una RTX 3080, Blender instalado en
<RUTA> y ffmpeg. Objetivo: portada (/) con sobrevuelo fotorrealista por scroll, fluida en cualquier
celular. Pasos, en bucle hasta que quede bien:
1. Corre blender/cine_render.py --preview y revisa 6 cuadros repartidos (abre los PNG). Corrige en
   blender/cine_render.py o blender/build.py lo que se vea mal (encuadres de web/src/data/cine.ts,
   luz, materiales, entorno). Repite.
2. Si existen assets/pbr y assets/hdri: en blender/build.py reemplaza las texturas generadas por las
   PBR reales (color/normal/roughness) para césped, concreto, repello, teja, zinc, asfalto, grava; y en
   build_mundo usa el HDRI como cielo (nodo Environment Texture) con el sol como luz principal.
   Reconstruye (& $b -b -P blender\build.py) y vuelve al paso 1.
3. Render final 1080p (--w 1920 --samples 128). Verifica el video en el navegador (npm run dev) en
   escritorio y en móvil (DevTools). Comprueba peso de sobrevuelo.mp4 (< 25 MB; si pesa más, sube crf
   a 23 en cine_render.py).
4. Commit y push. No toques el blog.
```

## 5. Qué hace cada archivo

- `blender/build.py` → construye la escena (edificios por código desde croquis/fotos) → `build/escena.blend`.
- `blender/cine_render.py` → añade entorno (colinas, Barú, bosque, vecinos, calle), cámara por la ruta de
  `web/src/data/cine.ts`, render Cycles GPU, video con ffmpeg.
- Todos los scripts de `blender/` se corren con `& $b -b -P blender\<script>.py -- <args>` en tu PC
  (aquí en la nube corren con `python3` porque Blender está instalado como módulo).
- `blender/export.py` → GLB para el 3D en vivo (`escena.glb` completo, `exterior.glb` ligero para la portada).
- `web/src/components/Cine.astro` → portada: usa `clips/sobrevuelo.mp4` si existe; si no, 3D en vivo.

## 6. Vistas 360° en calidad de foto (01-11-2026)

Lo hiperrealista en la web sale de renders hechos antes, no del 3D en vivo. Las vistas 360° son fotos
esféricas renderizadas con Cycles desde el modelo amueblado (`build/bloqueo/bloqueo.blend`, el mismo del
recorrido). La web las muestra en `/360` y con el botón "Ver en 360°" de cada espacio en `/recorrido`
(visor: `web/src/visor/pano360.ts`). Pesan ~1–3 MB cada una.

En la nube se renderizan a 2048 px con pocas muestras (CPU, ~10 min cada una). En la 3080, calidad final:

```
& $b -b -P blender\bloqueo.py -- --solo ninguno                                  # modelo amueblado (si cambió)
& $b -b -P blender\panoramas.py -- --ids todas --ancho 6144 --muestras 256 --gpu  # ≈ 1–2 min por vista
cd web; npm run build
```

Las vistas, sus puntos de cámara y su exposición están en `PANOS` dentro de `blender/panoramas.py`; el
manifiesto `web/src/data/panoramas.json` se reescribe solo. Para agregar una vista, se suma una línea a
`PANOS` con el id del espacio (el mismo de `/recorrido`, p. ej. `salonB@gris`).

Pendiente para la portada: el sobrevuelo v2 (`clips/sobrevuelo-v2.mp4`) con el modelo amueblado. Hoy
`cine_render.py` abre `build/escena.blend` (la maqueta anterior); hay que apuntarlo a `bloqueo.blend`.
