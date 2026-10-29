# Orquestación del proyecto (para Claude Code en PowerShell o para seguir aquí)

Proyecto: sitio web de venta de la propiedad de Altos de San Cristóbal (David, Chiriquí) como
residencia de retiro llave en mano. Carpeta: `C:\Users\ermom\.gemini\antigravity\scratch\realstate`.
Repositorio: `EMPmercadeo/realstate` (GitHub) → Vercel `residencia-altos` (root `web`).

## Qué hay

| Carpeta | Qué es |
|---|---|
| `web/` | Sitio Astro 7. `npm run dev` para verlo. Tres rutas: `/` (sobrevuelo 3D cinematográfico), `/fotos` (recorrido en fotos tipo scroll-world), `/recorrido` (maqueta 3D libre). |
| `web/src/visor/visor.ts` | Visor Three.js: carga `public/modelo/escena.glb`, cielo, sol, post-proceso (AO, bloom, viñeta), modo cine (cámara por ruta), orbitar, caminar. |
| `web/src/visor/mundo.ts` | Mundo procedural: terreno, colinas, Volcán Barú, bosque, árboles/palmeras low-poly con viento, calles, vecindario, nubes, pájaros, agua con reflejos. |
| `web/src/data/cine.ts` | **Ruta de la cámara y paradas** del sobrevuelo. Editar aquí para cambiar el recorrido. |
| `web/src/data/recorrido.ts` | Paradas del recorrido en fotos (`/fotos`). |
| `web/src/components/Cine.astro` | Portada: escenario 3D fijo + scroll (Lenis) + textos y fotos por parada. |
| `web/src/components/Recorrido.astro` + `web/src/recorrido/motor.ts` | Scroll-world de fotos (hoy → así quedará; usa `/clips/<id>.mp4` si existen). |
| `web/public/fotos-reales/` | Fotos reales de fachada (2400 px). |
| `web/public/fotos-antes/`, `fotos-despues/` | Fotos actuales y renders "así quedará" (Nano Banana). El sitio detecta solo las que existen. |
| `blender/` | Modelo procedural (`build.py` → `build/escena.blend`; `export.py` → GLB). Solo si cambian medidas. |
| `docs/tareas-antigravity.md` | Tareas de imágenes para Antigravity (prompt + foto fuente). |
| `.agents/skills/scroll-world/` y `.claude/skills/scroll-world/` | Skill de referencia (motor scrub, prompts, método de costuras de video). |
| `web/scripts/captura.mjs` | Captura sin cabeza del visor: `node scripts/captura.mjs "http://localhost:4321/?frames=8&u=0.4" salida.jpg 1400 800`. En `/recorrido` también `?cam=x,y,z,tx,ty,tz`. |

## Cómo iterar el sobrevuelo 3D (bucle)

1. `cd web && npm run dev` (o `npm run build && npx astro preview`).
2. Capturar paradas: `u` de 0 a 1 (`?u=0.3` fija la cámara en ese punto de la ruta sin animar).
3. Mirar la captura, ajustar `src/data/cine.ts` (ruta/paradas), `src/visor/mundo.ts` (entorno) o `visor.ts` (luz/post).
4. Repetir hasta que cada parada se vea como una toma de película. Criterios: sujeto centrado,
   nada tapando la cámara, horizonte visible en tomas bajas, sombras largas, bruma al fondo.
5. `git add -A && git commit -m "..." && git push` → Vercel despliega solo.

## Prompt-goal para Claude Code (pegar en PowerShell dentro de `realstate`)

```
Lee docs/ORQUESTACION.md y docs/estado.md. Objetivo: que la portada (/) sea un sobrevuelo 3D
cinematográfico al nivel de los demos "Gemini 4 Argon builders" (hidroavión, pagoda): luz dorada,
bruma, agua con reflejos, vegetación con viento, cámara de película que recorre la propiedad por
scroll, paradas con texto y foto "así quedará". Itera en bucle: build → captura cada parada con
web/scripts/captura.mjs → corrige → repite. No toques el blog. Cuando una parada quede bien,
commit. Al final actualiza docs/estado.md.
```

## Imágenes con Antigravity (Nano Banana)

Las tareas están en `docs/tareas-antigravity.md`. Pendientes: 7 comedor ✔ (ya está), 8 terapia,
9 cuarto-vip, 11 gazebo, 12 terapia-acuatica, 13 fachada, 14 edificio-gris, 15 jardin-central,
16 porche (porche de arcos adecuado: rampa, pasamanos, jardineras; fuente `web/public/fotos-reales/porche-arcos.jpg`).
Guardar cada resultado como `web/public/fotos-despues/<nombre>.jpg` (1600 px de ancho). El sitio las toma solo.

## Clips de video (opcional, fase 2)

Para `/fotos`: con Higgsfield/Kling/Veo "primer y último fotograma", generar por parada un clip de
5–8 s desde la foto real hacia la imagen "después" (cámara avanzando lento) y guardarlo como
`web/public/clips/<id>.mp4` (16:9, sin audio, `-g 8 +faststart`) y `<id>-m.mp4` (9:16). El motor los
usa automáticamente.

## Pendiente de la clienta
Planos o medidas reales, nombre comercial, contacto, precio o "solicitar expediente", dominio.
