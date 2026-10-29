# Estado del proyecto (28-10-2026, noche)

## Hecho
- Modelo 3D procedural en Blender (`blender/`): terreno 30×84 m, calle, cerca, portón, casa amarilla (2 niveles, porche de arcos, teja), edificio gris (2 niveles, lámina, terraza con baranda azul/blanca), gazebo, terapia acuática, huerto, estacionamiento, rampas, caminos, bancas, faroles, jardineras, palmas y árboles. Interiores amueblados según el programa (camas hospitalarias con rieles, mesitas y luz LED; estación de enfermería; comedor; cocina; baños; cuartos; recepción; consultorio; terapia).
- Visor web (`web/src/visor/visor.ts`): cielo físico, sol con sombras, oclusión ambiental, recorrido guiado con subtítulos, modo maqueta (orbitar, cortar por piso) y modo caminar (teclado o joystick), etiquetas sobre cada espacio, comparador "hoy / así quedará" por sala, pantalla de carga, enlaces profundos (`/recorrido#hospitalizacion@gris`).
- Fotos "así quedará" generadas con Nano Banana (7 de 12): hospitalización, salón #2, refrigerios, cocina, terraza, baño accesible, recepción. Pendientes por cuota: comedor, terapia, cuarto VIP, gazebo, terapia acuática (tareas 7, 8, 9, 11, 12 de `docs/tareas-antigravity.md`). El visor detecta automáticamente las nuevas en `web/public/fotos-despues/`.
- Portada (`web/src/pages/index.astro`): hero, datos, comparadores, galería, llamada al recorrido, bloque inversionistas.
- Renders fijos en `build/renders/`.

## Pendiente
- Planos o medidas reales → actualizar `blender/programa.py` y reconstruir (`build.py` → `export.py`).
- Datos de la clienta: nombre comercial, contacto, precio o "solicitar expediente", dominio.
- Repositorio GitHub + Vercel (root directory `web`).
- Blog multipaís: estructura lista en `web/src/content/blog/`; el prompt y buyer persona los da Ernesto aparte.

## Cómo regenerar
```
python3 -c "import runpy; runpy.run_path('blender/build.py')"   # escena
python3 blender/export.py                                         # GLB -> web/public/modelo
cd web && npm run build                                           # sitio
python3 publicar.py                                               # carpeta publish/ para el artefacto
```
