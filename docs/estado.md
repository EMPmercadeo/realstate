# Estado del proyecto (29-10-2026, madrugada)

## Dirección actual
Ernesto descartó la maqueta 3D "plana" como protagonista. La portada (`/`) es ahora un **sobrevuelo 3D
cinematográfico** estilo demos "Gemini 4 Argon builders": mundo low-poly con hora dorada, bruma, colinas y
Volcán Barú, bosque, árboles y palmeras con viento, vecindario, nubes, pájaros y agua con reflejos; la cámara
vuela por una ruta (`web/src/data/cine.ts`) movida por el scroll, con paradas de texto y foto "así quedará".

## Rutas del sitio
- `/` — sobrevuelo 3D (Cine.astro + visor.ts modo cine + mundo.ts) y luego datos, comparadores, espacios, inversionistas.
- `/fotos` — recorrido en fotos tipo scroll-world (fotos reales → "después"; usa clips de video si existen en `/clips`).
- `/recorrido` — maqueta 3D libre (orbitar, caminar, pisos, etiquetas) con el mismo mundo mejorado.

## Hecho en esta sesión
- Fotos reales de fachada (26) revisadas; 15 seleccionadas a 2400 px en `web/public/fotos-reales/`.
- Skill `scroll-world` instalada en `.agents/skills/` y `.claude/skills/` (motor, prompts, método de costuras).
- Motor de scroll de fotos (`web/src/recorrido/motor.ts`, Lenis) y página `/fotos`.
- Mundo procedural (`web/src/visor/mundo.ts`) + luz dorada, niebla, bloom, viñeta/grado (`visor.ts`).
- Modo cine con ruta de cámara y `?u=` para depurar; `web/scripts/captura.mjs` para capturas sin cabeza.
- `docs/ORQUESTACION.md` con el prompt-goal para Claude Code en PowerShell.
- Tareas 13–16 de Antigravity (fachada, edificio gris, jardín central, porche).

## Siguiente fase (PC con RTX 3080) — ver docs/PLAN-GPU.md
- Render fotorrealista del sobrevuelo con Cycles GPU (`blender/cine_render.py`) → `web/public/clips/sobrevuelo.mp4`; la portada lo reproduce por scroll (ya implementado; `/?3d` fuerza el 3D en vivo).
- Texturas PBR reales + HDRI (descarga de Ernesto) y, opcional, horneado de luz para el 3D en vivo.
- `exterior.glb` (3,7 MB) para la portada 3D; `escena.glb` (8,9 MB) para /recorrido.

## Pendiente inmediato
- Afinar cada parada del sobrevuelo (encuadres, árboles que tapan, agua de la piscina, cielo visible).
- Capturar móvil y verificar rendimiento (reducir sombras/AO en móvil ya está; medir).
- Imágenes Antigravity 8, 9, 11, 12, 13, 14, 15, 16 → `web/public/fotos-despues/`.
- Push a GitHub (Ernesto) → Vercel; desactivar "Vercel Authentication" en el proyecto.
- Blog: no tocar hasta recibir prompt y buyer persona.

## Cómo regenerar
```
cd web && npm run build && npx astro preview          # sitio
node scripts/captura.mjs "http://localhost:4321/?frames=8&u=0.4" cap.jpg 1400 800
python3 publicar.py                                   # carpeta publish/ para el artefacto
python3 -c "import runpy; runpy.run_path('blender/build.py')" && python3 blender/export.py   # solo si cambia el modelo
```
