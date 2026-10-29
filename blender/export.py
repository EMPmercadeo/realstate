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

# vecinos y entorno van a un grupo simple
kwargs = dict(
    filepath=os.path.join(out_dir, 'escena.glb'),
    export_format='GLB',
    export_apply=True,
    export_extras=True,
    export_yup=True,
    export_image_format='JPEG',
    export_jpeg_quality=82,
    export_texture_dir='',
    export_materials='EXPORT',
    export_normals=True,
    export_tangents=False,
    export_cameras=False,
    export_lights=False,
    export_animations=False,
)
try:
    bpy.ops.export_scene.gltf(**kwargs, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    print('exportado con draco')
except Exception as e:
    print('draco no disponible:', e)
    bpy.ops.export_scene.gltf(**kwargs)
    print('exportado sin draco')
print(os.path.getsize(os.path.join(out_dir, 'escena.glb')) / 1e6, 'MB')
