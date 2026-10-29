"""Exporta build/escena.blend a web/public/modelo/escena.glb (con extras: techo, cielo, piso)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'escena.blend'))
out_dir = os.path.join(ROOT, 'web', 'public', 'modelo')
os.makedirs(out_dir, exist_ok=True)

# marcar piso y edificio en extras para el visor
for o in bpy.data.objects:
    n = o.name
    for ed in ('gris', 'amarilla'):
        if n.startswith(ed + '_'):
            o['edificio'] = ed
            # piso: por colección
            for c in o.users_collection:
                if c.name.startswith(ed + '_p'):
                    o['piso'] = int(c.name.split('_p')[1][0])
            if o.get('techo'):
                o['piso'] = 99

# texturas más ligeras para la web (máx. 512 px; el césped a 768)
for im in bpy.data.images:
    if im.size[0] > 0:
        mx = 768 if 'grass' in im.name else 512
        if im.size[0] > mx:
            im.scale(mx, int(im.size[1] * mx / im.size[0]))

kwargs = dict(
    filepath=os.path.join(out_dir, 'escena.glb'),
    export_format='GLB',
    export_apply=True,
    export_extras=True,
    export_yup=True,
    export_image_format='JPEG',
    export_jpeg_quality=74,
    export_texture_dir='',
    export_materials='EXPORT',
    export_normals=True,
    export_tangents=False,
    export_cameras=False,
    export_lights=False,
    export_animations=False,
)
import re
def exportar(nombre, excluir=None):
    kwargs['filepath'] = os.path.join(out_dir, nombre)
    if excluir:
        for o in bpy.data.objects:
            o.hide_viewport = False
            o.select_set(bool(excluir.search(o.name)) is False)
        kwargs['use_selection'] = True
    try:
        bpy.ops.export_scene.gltf(**kwargs, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    except Exception as e:
        print('draco no disponible:', e)
        bpy.ops.export_scene.gltf(**kwargs)
    print(nombre, round(os.path.getsize(kwargs['filepath']) / 1e6, 2), 'MB')

# completo (maqueta libre, /recorrido)
exportar('escena.glb')
# solo exterior (portada): sin mobiliario, cielos rasos, vecinos ni arboleda (el mundo procedural los pone)
EXCLUIR = re.compile(r'(^(entorno|vecino_|arbol_|palma_|garage_palma|calle$|acera$|acera2$)|_(cama|silla|mesa|mesita|estacion|closet|estufa|alacena|meson|granito|lav|wc|tanque|ger|cielo|led|cortina|sofa|tv|escritorio|camilla|cobija|almohada|s\d*|esc|planta|zoc)(\d|\.|_|$))')
exportar('exterior.glb', EXCLUIR)
