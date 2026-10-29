# Residencia Altos de San Cristóbal — sitio web + recorrido 3D

Proyecto de comercialización de la propiedad (antiguo campus ISPE, David, Chiriquí) como residencia de retiro llave en mano.

## Estructura

```
blender/      modelo 3D procedural (bpy). programa.py = programa arquitectónico; build.py = construye la escena;
              render.py = renders fijos; export.py = exporta a glTF para la web; gen_textures.py / gen_leaves.py = texturas.
assets/       texturas PBR generadas y HDRIs.
build/        escena.blend y renders (se regenera).
web/          sitio Astro + visor Three.js (src/visor/visor.ts). Se despliega en Vercel tal cual.
docs/         programa de espacios, transcripción de la nota de voz, referencias.
```

## Comandos

```bash
# 3D (requiere Python 3.11+ y `pip install bpy numpy pillow`)
python3 blender/gen_textures.py && python3 blender/gen_leaves.py
python3 -c "import runpy; runpy.run_path('blender/build.py')"
python3 blender/render.py casa 64 1920          # vista, muestras, ancho
python3 blender/export.py                        # -> web/public/modelo/escena.glb

# Web
cd web && npm install && npm run dev             # http://localhost:4321
npm run build                                    # -> web/dist (Vercel: framework Astro, root = web)
```

## Estado

- Medidas de los edificios estimadas por satélite: corregir `blender/programa.py` cuando haya planos y reconstruir.
- Pendiente: imágenes fotorrealistas por espacio (prompts en docs/), textos definitivos, dominio y contacto de la clienta, blog multipaís (estructura lista en `web/src/content/blog`).
