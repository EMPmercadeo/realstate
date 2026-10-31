"""
Plantas del frente y puntos de vista para la prueba web horneada (complemento de hornear_web.py).
No hornea nada: exporta arbustos, palmas, faroles y adornos con su color en los vértices, y un JSON con el sol
y las vistas. Sin hierba (pesa demasiado para un celular; en la web va como textura del suelo).
Uso: python3 blender/plantas_web.py -- --zona frente
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'web_horneado')
os.makedirs(OUT, exist_ok=True)
ZONA = arg('--zona', 'frente')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'muestra', 'realismo.blend'))
sc = bpy.context.scene


# ------------------------------------------------------------------ plantas del frente (sin hornear)
# Las plantas se mueven con el viento en la web y no caben en un atlas: van aparte, con su color en los
# vértices (el mismo degradado de sus materiales) y se iluminan en vivo con el mismo sol.
PLANTAS = ('alamanda', 'ixora', 'verde', 'palma', 'areca', 'mata_maceta', 'maceta', 'farol', 'ca_porton_adorno')
def color_por_cara(o):
    me = o.data
    cols = []
    for poly in me.polygons:
        m = me.materials[poly.material_index] if me.materials else None
        c0 = c1 = (0.3, 0.3, 0.3, 1)
        usa_tinte = False
        if m and m.use_nodes:
            for nd in m.node_tree.nodes:
                if nd.bl_idname == 'ShaderNodeValToRGB':
                    c0, c1 = tuple(nd.color_ramp.elements[0].color), tuple(nd.color_ramp.elements[-1].color)
                elif nd.bl_idname == 'ShaderNodeAttribute' and nd.attribute_name == 'tinte':
                    usa_tinte = True
                elif nd.bl_idname == 'ShaderNodeBsdfPrincipled' and not nd.inputs['Base Color'].is_linked:
                    c0 = c1 = tuple(nd.inputs['Base Color'].default_value)
        cols.append((c0, c1, usa_tinte))
    return cols

def aclarar(o, conservar=0.3, crecer=1.7, seed=7):
    """Para el celular: cada hoja, pinna o flor es una isla de pocas caras. Se conserva una fracción de las
    islas chicas y se agrandan sobre su propio centro, así la planta conserva su volumen con muchos menos
    triángulos. Las islas grandes (troncos, ramas, capitel) quedan intactas. Decimar no sirve aquí: deforma
    las hojas sueltas."""
    import bmesh, random
    rnd = random.Random(seed)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    vistas, borrar = set(), []
    for f in bm.faces:
        if f.index in vistas:
            continue
        isla, pila = [], [f]
        vistas.add(f.index)
        while pila:
            g = pila.pop(); isla.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistas:
                        vistas.add(h.index); pila.append(h)
        if len(isla) > 12:                              # tronco, rama o capitel
            continue
        if rnd.random() > conservar:
            borrar.extend(isla)
            continue
        vs = {v for g in isla for v in g.verts}
        c = sum((v.co for v in vs), Vector()) / len(vs)
        for v in vs:
            v.co = c + (v.co - c) * crecer
    bmesh.ops.delete(bm, geom=borrar, context='FACES')
    bm.to_mesh(o.data); bm.free()


plantas = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PLANTAS)
           and o.users_collection and o.users_collection[0].name == 'Vegetacion']
copias = []
for o in plantas:
    c = o.copy(); c.data = o.data.copy(); sc.collection.objects.link(c)
    me = c.data
    t = me.color_attributes.get('tinte')
    vals = [0.5] * (len(me.loops) * 4)
    if t:
        t.data.foreach_get('color', vals)
    info = color_por_cara(c)
    out = []
    for poly, (c0, c1, ut) in zip(me.polygons, info):
        for li in poly.loop_indices:
            k = vals[li * 4] if ut else 0.5
            out.extend([c0[i] + (c1[i] - c0[i]) * k for i in range(3)] + [1.0])
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    col.data.foreach_set('color', out)
    if t:
        me.color_attributes.remove(me.color_attributes['tinte'])
    me.color_attributes.active_color = me.color_attributes['Col']
    me.materials.clear()
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    if len(me.polygons) > 2500:                       # menos hojas pero más grandes: misma silueta, mucho menos peso
        if c.name.startswith(('palma', 'areca')):
            aclarar(c, conservar=0.3, crecer=1.45)
            d = c.modifiers.new('dec', 'DECIMATE'); d.ratio = 0.5    # raquis y tronco: tubos con menos anillos
        else:
            aclarar(c, conservar=0.14, crecer=2.1)
    copias.append(c)
for o in bpy.context.view_layer.objects:
    o.select_set(o in copias)
ruta_p = os.path.join(OUT, f'{ZONA}_plantas.glb')
bpy.ops.export_scene.gltf(filepath=ruta_p, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_materials='NONE', export_vertex_color='ACTIVE', export_cameras=False, export_lights=False,
                          export_animations=False)       # sin Draco: el visor de prueba no puede bajar el decodificador
print('plantas', ruta_p, round(os.path.getsize(ruta_p) / 1e6, 2), 'MB',
      sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in copias), 'triángulos', flush=True)


# datos para la página: sol y puntos de vista (coordenadas de three.js: x, z, -y)
sol = bpy.data.objects['sol']
d = sol.matrix_world.to_3x3() @ Vector((0, 0, 1))          # hacia el sol
def T(x, y, z):
    return [round(x, 3), round(z, 3), round(-y, 3)]
def L(x, y, z):
    X, Y = sitio.local_a_m(sitio.CASA, x, y)
    return T(X, Y, z)
datos = dict(sol=T(d.x, d.y, d.z), exposicion=sc.view_settings.exposure,
             vistas=[dict(nombre='Calle', pos=L(5.0, -16.5, 1.6), mira=L(6.0, -2.0, 3.6)),
                     dict(nombre='Portón', pos=L(5.8, -8.6, 1.6), mira=L(7.0, 0.0, 2.2)),
                     dict(nombre='Entrada', pos=L(6.6, -4.0, 1.6), mira=L(9.6, 0.0, 1.5)),
                     dict(nombre='Cochera', pos=L(1.4, -6.5, 1.6), mira=L(1.6, 2.0, 1.8))])
json.dump(datos, open(os.path.join(OUT, f'{ZONA}.json'), 'w'), indent=1)
print('datos', os.path.join(OUT, f'{ZONA}.json'), flush=True)

# el edificio horneado se dibuja sin luces: no necesita normales (sin ellas los vértices se comparten y pesa menos)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, f'{ZONA}.glb'))
for o in bpy.context.view_layer.objects:
    o.select_set(o.type == 'MESH')
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{ZONA}_sn.gltf'), export_format='GLTF_SEPARATE', use_selection=True,
                          export_yup=True, export_normals=False, export_materials='EXPORT', export_image_format='JPEG',
                          export_cameras=False, export_lights=False, export_animations=False)
print('casa sin normales', os.path.join(OUT, f'{ZONA}_sn.gltf'), flush=True)
