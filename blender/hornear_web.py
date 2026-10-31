"""
Luz horneada para la web (como se decidió el 30-10: Three.js con la luz de Cycles pintada en las texturas).

Une las piezas de una zona en una sola malla, le hace un UV de luz, hornea con Cycles la imagen final de cada
superficie (color + sol + cielo + rebotes, sin reflejos que dependan de la vista), le aplica la misma
exposición y AgX que los renders, y exporta un GLB donde todo usa esa textura. En el navegador se dibuja
sin luces (MeshBasicMaterial): se ve igual que Blender y corre en cualquier celular.

Uso:
  python3 blender/hornear_web.py -- --zona frente --atlas 2048 --muestras 16          (prueba, CPU)
  & $b -b -P blender\\hornear_web.py -- --zona frente --atlas 8192 --muestras 256 --gpu  (PC con RTX)
Salida: build/web_horneado/<zona>.glb (+ <zona>_luz.jpg)
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector
import sitio

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'web_horneado')
os.makedirs(OUT, exist_ok=True)
ZONA = arg('--zona', 'frente')
ATLAS = int(arg('--atlas', '2048'))
MUESTRAS = int(arg('--muestras', '16'))

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'muestra', 'realismo.blend'))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name.startswith('satelite'):
        o.hide_render = True

# ------------------------------------------------------------------ qué se hornea
NO = ('_mueble_', 'lampara', 'abanico', 'cuadro', 'lienzo', 'cortina', 'vidrio', 'espejo')   # muebles e interiores finos
from shapely.geometry import box as rect, Point
from shapely.ops import unary_union
PLANTA = unary_union([rect(*r) for r in [(0, 0, 4.4, 13.8), (4.4, 0, 10.0, 13.8), (10.0, 0.9, 12.6, 13.8), (5.3, -0.6, 9.1, 0)]]).buffer(-0.4)


def en_zona(o):
    """Zona 'frente': exterior de la casa amarilla (lo que toca la fachada), cercas, piso y jardineras.
    Lo que queda entero dentro de la planta (muros y muebles interiores) no se hornea en esta prueba."""
    if o.type != 'MESH' or not o.data.polygons or any(k in o.name for k in NO) or o.hide_render:
        return False
    if o.name.startswith('satelite'):
        return False
    if o.users_collection and o.users_collection[0].name in ('Vegetacion', 'Entorno'):
        return o.name.startswith('jardinera') or o.name.startswith('patio_grava')
    if o.name.startswith(('lote', 'via', 'entorno')):
        return False
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(w.x for w in ws) / 8; cy = sum(w.y for w in ws) / 8
    lx, ly = sitio.m_a_local(sitio.CASA, cx, cy)
    if not (-8 < lx < 25 and -14 < ly < 27):
        return False
    if o.name.startswith('ca_'):
        esquinas = [sitio.m_a_local(sitio.CASA, w.x, w.y) for w in ws]
        if all(PLANTA.contains(Point(q)) for q in esquinas) and max(w.z for w in ws) < 6.0:
            return False
    return True


objs = [o for o in bpy.data.objects if en_zona(o)]
print('piezas', len(objs), flush=True)

# ------------------------------------------------------------------ unir (con modificadores aplicados)
dg = bpy.context.evaluated_depsgraph_get()
bm = bmesh.new()
mats = []
for o in objs:
    tmp = o.evaluated_get(dg).to_mesh().copy()
    tmp.transform(o.matrix_world)
    if o.matrix_world.determinant() < 0:
        tmp.flip_normals()
    remap = []
    for s in o.material_slots:
        if s.material not in mats:
            mats.append(s.material)
        remap.append(mats.index(s.material))
    for p in tmp.polygons:
        p.material_index = remap[min(p.material_index, len(remap) - 1)] if remap else 0
    while tmp.uv_layers:
        tmp.uv_layers.remove(tmp.uv_layers[0])
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
me = bpy.data.meshes.new(f'horneado_{ZONA}')
bm.to_mesh(me); bm.free()
for m in mats:
    me.materials.append(m)
H = bpy.data.objects.new(f'horneado_{ZONA}', me)
sc.collection.objects.link(H)
for o in objs:
    o.hide_render = True                      # la malla unida los reemplaza (sombras y rebotes incluidos)
print('triángulos', sum(len(p.vertices) - 2 for p in me.polygons), 'materiales', len(mats), flush=True)

# ------------------------------------------------------------------ UV de luz
me.uv_layers.new(name='luz')
bpy.context.view_layer.objects.active = H
for o in bpy.context.view_layer.objects:
    o.select_set(o == H)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0015, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.average_islands_scale()                  # misma densidad de texel en todas las piezas
bpy.ops.uv.pack_islands(margin=0.0015, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------------ hornear
img = bpy.data.images.new(f'luz_{ZONA}', ATLAS, ATLAS, alpha=False, float_buffer=True)
for m in mats:
    if not m or not m.use_nodes:
        continue
    nt = m.node_tree
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.name = '_horneo'
    nt.nodes.active = tx
cy = sc.cycles
sc.render.engine = 'CYCLES'
cy.device = 'CPU'
if '--gpu' in argv:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = tipo; prefs.get_devices()
            if any(d.type == tipo for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == tipo
                cy.device = 'GPU'; print('GPU:', tipo, flush=True); break
        except Exception:
            pass
cy.samples = MUESTRAS
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.transparent_max_bounces = 32
bk = sc.render.bake
bk.use_pass_direct = True; bk.use_pass_indirect = True
bk.use_pass_diffuse = True; bk.use_pass_glossy = False; bk.use_pass_transmission = True; bk.use_pass_emit = True
bk.margin = 6; bk.target = 'IMAGE_TEXTURES'
print('horneando', ATLAS, 'px,', MUESTRAS, 'muestras…', flush=True)
bpy.ops.object.bake(type='COMBINED', uv_layer='luz')

# misma exposición y AgX que los renders: la textura queda lista para mostrarse tal cual
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
ruta_luz = os.path.join(OUT, f'{ZONA}_luz.jpg')
img.save_render(ruta_luz, scene=sc)
print('textura', ruta_luz, flush=True)

# ------------------------------------------------------------------ material único y GLB
tex = bpy.data.images.load(ruta_luz)
mw = bpy.data.materials.new(f'web_{ZONA}')
mw.use_nodes = True
nt = mw.node_tree
pb = nt.nodes['Principled BSDF']
t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex
nt.links.new(t.outputs['Color'], pb.inputs['Base Color'])
pb.inputs['Roughness'].default_value = 1.0
me.materials.clear(); me.materials.append(mw)
me.uv_layers.active = me.uv_layers['luz']
for o in bpy.context.view_layer.objects:
    o.select_set(o == H)
ruta = os.path.join(OUT, f'{ZONA}.glb')
bpy.ops.export_scene.gltf(filepath=ruta, export_format='GLB', use_selection=True, export_apply=True,
                          export_yup=True, export_materials='EXPORT', export_image_format='JPEG',
                          export_cameras=False, export_lights=False, export_animations=False)
print('glb', ruta, round(os.path.getsize(ruta) / 1e6, 2), 'MB', flush=True)


# las plantas y los puntos de vista de la página van en blender/plantas_web.py
