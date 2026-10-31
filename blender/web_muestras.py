"""Muestrea los materiales procedurales de bloqueo.blend para la web.

glTF no entiende los nodos procedurales (ladrillo, ruido, rampas): este script renderiza cada material
sobre un parche plano (solo su color base, como emisión) y guarda:
  - el color medio de cada material (para muebles, telas, maderas…)
  - una textura repetible para pisos, azulejos, cielo de losetas y bloques de vidrio (UV en metros)
Salida: build/web/muestras.json y build/web/tex/<material>.png
Uso:  blender -b -P blender/web_muestras.py      (o python con el módulo bpy)
"""
import os, sys, json, math
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'web')
TEX = os.path.join(OUT, 'tex')
os.makedirs(TEX, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'bloqueo', 'bloqueo.blend'))
sc = bpy.context.scene
# escena vacía: se sacan todas las colecciones (los datos siguen en el archivo)
for c in list(sc.collection.children):
    sc.collection.children.unlink(c)
for o in list(sc.collection.objects):
    sc.collection.objects.unlink(o)
sc.world = None

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 6
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 0
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0
sc.view_settings.gamma = 1
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.resolution_percentage = 100
sc.render.filter_size = 0.8

# parche con UV en metros (como lib.box_uv para caras horizontales)
me = bpy.data.meshes.new('parche')
me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new(name='UVMap')
plano = bpy.data.objects.new('parche', me)
sc.collection.objects.link(plano)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam


def preparar(px, py):
    for i, (x, y) in enumerate([(0, 0), (px, 0), (px, py), (0, py)]):
        me.vertices[i].co = (x, y, 0)
    for li, vi in enumerate(me.polygons[0].vertices):
        uv.data[li].uv = (me.vertices[vi].co.x, me.vertices[vi].co.y)
    me.update()
    cam.location = (px / 2, py / 2, 5)
    cam.rotation_euler = (0, 0, 0)
    cam_d.ortho_scale = max(px, py)


TEXTURAS = ('piso_', 'azulejo_', 'cielo_reticula', 'bloque_vidrio')


def periodo(m):
    br = next((n for n in m.node_tree.nodes if n.type == 'TEX_BRICK'), None)
    if not br:
        return 1.0, 1.0
    s = br.inputs['Scale'].default_value
    w = br.inputs['Brick Width'].default_value / s
    h = br.inputs['Row Height'].default_value / s
    ph = 2 * h if abs(br.offset) > 1e-6 else h
    kx = max(1, round(1.2 / w)); ky = max(1, round(1.2 / ph))
    return w * kx, ph * ky


def srgb_a_lineal(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


usados = set()
for o in bpy.data.objects:
    if o.type == 'MESH':
        for s in o.material_slots:
            if s.material:
                usados.add(s.material.name)

res = {}
for m in bpy.data.materials:
    if m.name not in usados or not m.node_tree:
        continue
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf or not bsdf.inputs['Base Color'].is_linked:
        continue
    textura = m.name.startswith(TEXTURAS)
    px, py = periodo(m) if textura else (1.0, 1.0)
    preparar(px, py)
    base = 512 if textura else 48
    sc.render.resolution_x = base if px >= py else max(8, round(base * px / py))
    sc.render.resolution_y = base if py >= px else max(8, round(base * py / px))
    mc = m.copy()
    nt = mc.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = b.inputs['Base Color'].links[0].from_socket
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
    nt.links.new(src, em.inputs['Color'])
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    for l in list(out.inputs['Surface'].links):
        nt.links.remove(l)
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    if out.inputs.get('Displacement') is not None:
        for l in list(out.inputs['Displacement'].links):
            nt.links.remove(l)
    me.materials.clear(); me.materials.append(mc)
    ruta = os.path.join(TEX, m.name + '.png')
    sc.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(ruta)
    px_ = list(img.pixels)
    n = len(px_) // 4
    media = [sum(px_[i::4][:n]) / n for i in range(3)]   # pixels de PNG cargado: sRGB 0..1
    lin = [srgb_a_lineal(c) for c in media]
    res[m.name] = dict(color=[round(c, 4) for c in lin], textura=(m.name + '.png') if textura else None,
                       periodo=[round(px, 4), round(py, 4)] if textura else None)
    bpy.data.images.remove(img)
    if not textura:
        os.remove(ruta)
    print('muestra', m.name, res[m.name], flush=True)

with open(os.path.join(OUT, 'muestras.json'), 'w') as f:
    json.dump(res, f, indent=1)
print('listo', len(res), flush=True)
os._exit(0)
