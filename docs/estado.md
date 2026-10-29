# Estado del proyecto (29-10-2026, mañana)

## Dirección actual
La portada (`/`) es un **sobrevuelo cinematográfico renderizado con Cycles (GPU)** que la web reproduce
controlado por el scroll: fluido en cualquier celular porque es video, no 3D en vivo. El 3D en vivo queda
como respaldo (`/?3d`) y para `/recorrido`. La ruta de cámara y las 7 paradas viven en `web/src/data/cine.ts`
y las comparten el render (Blender) y la web.

## Rutas del sitio
- `/` — video `clips/sobrevuelo.mp4` (escritorio) o `sobrevuelo-m.mp4` (9:16 móvil) por scroll + póster `clips/poster.jpg`; luego datos, comparadores, espacios, inversionistas.
- `/fotos` — recorrido en fotos tipo scroll-world (fotos reales → "después"; usa clips de video si existen en `/clips/<id>.mp4`).
- `/recorrido` — maqueta 3D libre (orbitar, caminar, pisos, etiquetas).

## Hecho en esta sesión (Claude Code, PC con RTX 3080)
- **Pipeline de render** `blender/cine_render.py` (Blender 5.2, OptiX): luz de hora dorada (cielo Nishita, sol al
  este-sureste a 14°), texturas PBR reales de ambientCG (`assets/pbr/`, proyección en caja por posición mundial),
  follaje translúcido con variación de tono por árbol, bruma por pase Mist + bloom en el compositor de Blender 5,
  `--solo` para cuadros sueltos, `--video` para rearmar el mp4 sin re-renderizar, reanudación automática.
- **Modelo** (`blender/build.py`): techo de lámina roja en la casa amarilla (como en las fotos), canaletas y bajantes,
  aires acondicionados, rejas en todas las ventanas, remates en los pilares de la cerca, ventanas y puertas en las
  casas vecinas, techo del edificio gris cubriendo la terraza, entrada de baldosa. Hojas regeneradas con sombreado
  (`blender/gen_leaves.py`). Árboles y palmas reubicados fuera de la ruta de cámara (`blender/programa.py`).
- **Ruta de cámara** afinada tras revisar los 60 cuadros de preview: llegada centrada, paso sobre la cerca (no por el
  portón, que tiene pilares con remate), porche en 3/4, jardín sin palmas tapando, terraza desde la calle.
- **Web**: póster inmediato mientras baja el video; manifiesto de archivos opcionales generado en build
  (`web/src/data/existentes.ts`) para que `/fotos` y `/` no sondeen archivos inexistentes (cero 404 en consola).
- **Verificación** (Playwright + Lighthouse, con `astro preview`): portada en 1400×800 y 390×844 reproduce el video por
  scroll, las 7 paradas muestran su texto, las 5 fotos cargan, el seek coincide con `u` en todas; `/fotos` y
  `/recorrido` sin errores de consola; Lighthouse móvil performance 97 (FCP 1,6 s, TBT 0 ms, CLS 0).
- **GLB** reexportados: `escena.glb` 4,0 MB, `exterior.glb` 2,1 MB.
- **Deploy**: push a `EMPmercadeo/realstate` → Vercel `residencia-altos` despliega solo (Ready en ~10 s).
  `https://residencia-altos.vercel.app` responde 200 sin muro de "Vercel Authentication".

## Render final
- Comando: `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P blender\cine_render.py -- --w 1920 --samples 128 --frames 720`
  (≈ 7,6 s/cuadro en la 3080 → ≈ 1 h 30 min). Cuadros en `build/cine/`, log en `build/render_final.log`.
- Salida: `web/public/clips/sobrevuelo.mp4` (1080p, x264 crf 20, GOP 6 para scrub instantáneo), `sobrevuelo-m.mp4`
  (recorte central 9:16 a 720 px), `poster.jpg`. Pesos: ver sección "Resultado" al final.

## Pendiente
- Imágenes Antigravity que faltan: 13 fachada, 14 edificio-gris, 15 jardin-central, 16 porche → `web/public/fotos-despues/`
  (8 terapia, 9 cuarto-vip, 11 gazebo y 12 terapia-acuatica ya llegaron).
- Opcional: HDRI con nubes (`assets/hdri/` ya tiene tres de Poly Haven; `--hdri kloppenheim_06_puresky` los usa con
  un sol propio) si se quiere cielo con nubes en vez del procedural.
- Opcional: subir la calidad del follaje (más cartas por árbol o modelos de árbol reales) y añadir la torre/balcón
  octogonal del segundo piso de la casa amarilla tal como en `fotos-reales/fachada-frontal.jpg`.
- Dominio y contacto de la clienta; `site` en `web/astro.config.mjs` sigue siendo de ejemplo.
- Blog: no tocar hasta recibir prompt y buyer persona.

## Cómo regenerar
```
# 1. modelo (solo si cambia build.py / programa.py)
& $b -b -P blender\build.py
# 2. prueba rápida de 6 cuadros a 1280 px
& $b -b -P blender\cine_render.py -- --solo 0,12,24,36,48,59 --frames 60 --w 1280 --samples 48 --out build\cine_t
# 3. render final (reanudable) y video
& $b -b -P blender\cine_render.py -- --w 1920 --samples 128 --frames 720
& $b -b -P blender\cine_render.py -- --video --crf 22      # solo rearmar el mp4 (p. ej. si pesa > 25 MB)
# 4. web
cd web; npm run build; npx astro preview
# 5. 3D ligero para /recorrido y el respaldo de la portada
& $b -b -P blender\export.py
```
`$b = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`. ffmpeg: `winget install Gyan.FFmpeg`.

## Resultado (29-10-2026 06:10)
- Render final: 720 cuadros 1920×1080, 128 muestras, OptiX + denoise, 8,4 s/cuadro → 1 h 41 min en la RTX 3080.
- `sobrevuelo.mp4` 23,3 MB (x264 crf 26, GOP 16, 30 s a 24 fps) · `sobrevuelo-m.mp4` 7,4 MB (720×1278) · `poster.jpg` 0,3 MB.
  Detección de cortes de ffmpeg (`select=gt(scene,0.25)`): 0 saltos en ambos.
- Verificación local con `astro preview` (Playwright): escritorio 1400×800 y móvil 390×844 cargan el video (30 s),
  7/7 paradas con texto, 5/5 fotos, 7/7 seeks exactos, 0 errores de consola en `/`, `/fotos` y `/recorrido`.
  Lighthouse móvil: performance 97 (FCP 1,6 s · LCP 1,6 s · TBT 0 ms · CLS 0 · SI 4,2 s).
- Deploy: ver commit siguiente (verificación en producción).
