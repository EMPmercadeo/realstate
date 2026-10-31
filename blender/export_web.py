"""Exporta el modelo amueblado (build/bloqueo/bloqueo.blend) al recorrido 3D de la web.

Salida:
  web/public/modelo/residencia.glb   modelo ligero (Draco) para three.js
  web/src/data/residencia.json       cuartos, cámaras, niveles, vistas y vegetación del lote para el visor

Antes hay que correr blender/web_muestras.py (colores y texturas de los materiales procedurales).
Uso:  blender -b -P blender/export_web.py
"""
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector, Matrix
import sitio
from vistas_interiores import INTERIORES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(ROOT, 'build', 'web')
MUESTRAS = json.load(open(os.path.join(WEB, 'muestras.json')))
INT = json.load(open(os.path.join(ROOT, 'build', 'bloqueo', 'interiores.json')))
OUT_GLB = os.path.join(ROOT, 'web', 'public', 'modelo', 'residencia.glb')
OUT_JSON = os.path.join(ROOT, 'web', 'src', 'data', 'residencia.json')

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'bloqueo', 'bloqueo.blend'))
from shapely.geometry import Polygon, MultiPoint, Point, box
from shapely.ops import unary_union


def T(X, Y, Z):
    """metros del modelo (z arriba) → three.js (y arriba, z = -Y)."""
    return [round(X, 3), round(Z, 3), round(-Y, 3)]


def wbb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(w[i] for w in ws) for i in range(3)], [max(w[i] for w in ws) for i in range(3)]


# ---------------------------------------------------------------- limpieza
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA') or o.name in ('satelite', 'entorno') or o.name.startswith('lote'):
        bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects:
    o.hide_viewport = False; o.hide_set(False); o.hide_render = False

EDIF = {'gr_': ('gris', sitio.GRIS, INT['gris']), 'ca_': ('amarilla', sitio.CASA, INT['casa'])}
NIV = {}
for pref, (ed, E, d) in EDIF.items():
    pa = d['niveles'][1]
    NIV[ed] = dict(pa0=pa['z0'], pa1=pa['z1'], pb1=d['niveles'][0]['z1'])

# ---------------------------------------------------------------- huellas y zonas (antes de unir)
pts = {'gris': [], 'amarilla': []}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for pref, (ed, E, d) in EDIF.items():
        if o.name.startswith(pref):
            mw = o.matrix_world
            pts[ed] += [(mw @ v.co).to_2d()[:] for v in list(o.data.vertices)[::7]]
huella = {ed: MultiPoint(p).convex_hull for ed, p in pts.items()}


def bbox_de(prefijos):
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(prefijos)]
    a = [wbb(o) for o in obs]
    return [min(x[0][i] for x in a) for i in range(3)], [max(x[1][i] for x in a) for i in range(3)]


zonas = {
    'galeria': bbox_de(('gr_gal_e_piso', 'gr_piso_galeria')),
    'terraza_n': bbox_de(('gr_gal_n_piso',)),
    'parqueo': bbox_de(('gr_parqueo',)),
    'garaje': bbox_de(('ca_piso_garaje',)),
    'porton_casa': bbox_de(('ca_porton_612',)),
    'balcon': bbox_de(('ca_balcon_losa',)),
}
vias = [MultiPoint([(o.matrix_world @ v.co).to_2d()[:] for v in o.data.vertices]).convex_hull
        for o in bpy.data.objects if o.name.startswith('via')]
# las calles las dibuja el visor (se prolongan fuera del recorte del satélite)
for o in [o for o in bpy.data.objects if o.name.startswith('via')]:
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- materiales para glTF
RENOMBRE = {'n_vidrio_claro': 'vidrio_claro', 'n_vidrio': 'vidrio_oscuro', 'luz_panel': 'led_panel',
            'luz_calida': 'led_calida', 'vidrio_int': 'vidrio_int', 'agua_azul': 'botellon_azul', 'pantalla_lampara': 'tela_pantalla'}
JPG = os.path.join(WEB, 'tex_jpg'); os.makedirs(JPG, exist_ok=True)
WEBM = {}


def material_web(m):
    if m.name in WEBM:
        return WEBM[m.name]
    nombre = 'w_' + RENOMBRE.get(m.name, m.name)
    if RENOMBRE.get(m.name, '').startswith(('vidrio', 'led')):
        nombre = RENOMBRE[m.name]
    w = bpy.data.materials.new(nombre)
    w.use_nodes = True
    nt = w.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ob = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
    rough, metal, alpha, trans, emi, col = 0.6, 0.0, 1.0, 0.0, 0.0, (0.8, 0.8, 0.8)
    emi_col = (1, 1, 1)
    if ob:
        g = lambda k, d: (ob.inputs[k].default_value if k in ob.inputs and not ob.inputs[k].is_linked else d)
        rough = g('Roughness', 0.6); metal = g('Metallic', 0.0); alpha = g('Alpha', 1.0)
        trans = g('Transmission Weight', 0.0); emi = g('Emission Strength', 0.0)
        col = tuple(ob.inputs['Base Color'].default_value[:3])
        emi_col = tuple(ob.inputs['Emission Color'].default_value[:3])
    mu = MUESTRAS.get(m.name)
    if mu:
        col = tuple(mu['color'])
    b.inputs['Base Color'].default_value = col + (1,)
    b.inputs['Roughness'].default_value = max(0.05, min(1.0, rough))
    b.inputs['Metallic'].default_value = metal
    if mu and mu.get('textura'):
        src = os.path.join(WEB, 'tex', mu['textura'])
        dst = os.path.join(JPG, m.name + '.jpg')
        tmp = bpy.data.images.load(src)
        tmp.scale(512, 512)
        tmp.filepath_raw = dst; tmp.file_format = 'JPEG'
        tmp.save()
        bpy.data.images.remove(tmp)
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping'); mp.vector_type = 'POINT'
        px, py = mu['periodo']
        mp.inputs['Scale'].default_value = (1 / px, 1 / py, 1)
        im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(dst); im.extension = 'REPEAT'
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], im.inputs['Vector'])
        nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
    if trans > 0.5:
        alpha = 0.25
    if alpha < 0.99:
        b.inputs['Alpha'].default_value = alpha
        for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            try:
                setattr(w, attr, val)
            except Exception:
                pass
    if emi > 0:
        b.inputs['Emission Color'].default_value = emi_col + (1,) if any(emi_col) else col + (1,)
        b.inputs['Emission Strength'].default_value = 1.0
    WEBM[m.name] = w
    return w


for o in bpy.data.objects:
    if o.type == 'MESH':
        for s in o.material_slots:
            if s.material:
                s.material = material_web(s.material)

# ---------------------------------------------------------------- aligerar muebles muy detallados
def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


for o in list(bpy.data.objects):
    if o.type == 'MESH' and tris(o) > 4500:
        md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = max(0.3, 2600 / tris(o))
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier='dec')

# ---------------------------------------------------------------- separar cielos rasos de los acabados
CIELOS = ('w_cielo', 'w_cielo_reticula')


def separar_cielos(o):
    idx = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name in CIELOS]
    if not idx:
        return None
    c = o.copy(); c.data = o.data.copy(); c.name = o.name + '_cielo'
    for col in o.users_collection:
        col.objects.link(c)
    for ob, borrar_cielo in ((o, True), (c, False)):
        bm = bmesh.new(); bm.from_mesh(ob.data)
        fuera = [f for f in bm.faces if (f.material_index in idx) == borrar_cielo]
        bmesh.ops.delete(bm, geom=fuera, context='FACES')
        bm.to_mesh(ob.data); bm.free()
    return c


for o in list(bpy.data.objects):
    if o.type == 'MESH' and '_acabados' in o.name:
        separar_cielos(o)

# ---------------------------------------------------------------- clasificar y unir
def clase(o):
    n = o.name
    if n.startswith(('cerca_', 'pilar_', 'porton_')):
        return None, None, 'muro'
    if n.startswith(('bola_', 'via')):
        return None, None, 'obj'
    for pref, (ed, E, d) in EDIF.items():
        if not n.startswith(pref):
            continue
        z0, z1 = wbb(o)[0][2], wbb(o)[1][2]
        nv = NIV[ed]
        piso = 99 if z0 >= nv['pa1'] - 0.35 else (2 if z0 >= nv['pa0'] - 0.35 else 1)
        if piso == 99:
            return ed, 99, 'techo'
        base = 0.0 if piso == 1 else nv['pa0']
        if n.endswith('_cielo') or z0 > base + 2.2:
            return ed, piso, 'cielo'
        if '_muro' in n or '_acabados' in n or n.startswith(('ca_cerca', 'ca_porton')) or \
                (n.startswith('ca_garaje_') and not any(k in n for k in ('techo', 'reja', 'vano'))):
            return ed, piso, 'muro'
        return ed, piso, 'obj'
    return None, None, 'obj'


# piezas que solo se ven por dentro: no van en el modelo de la portada (sobrevuelo exterior)
INTERIOR = ('_mueble_', 'lampara', 'abanico', 'cuadro', 'lienzo', 'cortina')


def agrupar(excluir=()):
    g = {}
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.data.polygons or o.get('_web'):
            continue
        if excluir and any(k in o.name for k in excluir):
            continue
        ed, piso, fl = clase(o)
        g.setdefault(f'{ed}_p{piso}_{fl}' if ed else f'sitio_{fl}', []).append(o)
    return g


dg = bpy.context.evaluated_depsgraph_get()


def unir(grupos, coleccion):
    col = bpy.data.collections.new(coleccion); bpy.context.scene.collection.children.link(col)
    res = []
    for nombre, obs in sorted(grupos.items()):
        me = bpy.data.meshes.new(nombre)
        bm = bmesh.new()
        mats = []
        for o in obs:
            tmp = o.evaluated_get(dg).to_mesh().copy()
            tmp.transform(o.matrix_world)
            if o.matrix_world.determinant() < 0:
                tmp.flip_normals()
            remap = []
            for s in o.material_slots:
                mm = s.material
                if mm not in mats:
                    mats.append(mm)
                remap.append(mats.index(mm))
            for p in tmp.polygons:
                if remap:
                    p.material_index = remap[min(p.material_index, len(remap) - 1)]
            if not tmp.uv_layers:
                tmp.uv_layers.new(name='UVMap')
            else:
                tmp.uv_layers[0].name = 'UVMap'
                while len(tmp.uv_layers) > 1:
                    tmp.uv_layers.remove(tmp.uv_layers[-1])
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        bm.to_mesh(me); bm.free()
        for mm in mats:
            me.materials.append(mm)
        nuevo = bpy.data.objects.new(nombre, me)
        nuevo['_web'] = 1
        col.objects.link(nuevo)
        partes = nombre.split('_')
        if partes[0] in ('gris', 'amarilla'):
            nuevo['edificio'] = partes[0]
            nuevo['piso'] = int(partes[1][1:])
            if partes[2] == 'cielo':
                nuevo['cielo'] = 1
            if partes[2] == 'techo':
                nuevo['techo'] = 1
        res.append(nuevo)
        print(coleccion, nombre, len(obs), 'objetos', sum(len(p.vertices) - 2 for p in me.polygons), 'tri', len(mats), 'mat', flush=True)
    return res


completo = unir(agrupar(), 'web')
exterior = unir(agrupar(INTERIOR), 'web_exterior')

# solo quedan los modelos unidos
for o in list(bpy.data.objects):
    if not o.get('_web'):
        bpy.data.objects.remove(o, do_unlink=True)
for o in completo + exterior:
    del o['_web']


def exportar(objs, ruta):
    for o in bpy.data.objects:
        o.select_set(o in objs)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    kw = dict(filepath=ruta, export_format='GLB', export_apply=True, export_extras=True, export_yup=True,
              export_image_format='AUTO', export_materials='EXPORT', export_normals=True, export_tangents=False,
              export_cameras=False, export_lights=False, export_animations=False, use_selection=True)
    try:
        bpy.ops.export_scene.gltf(**kw, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    except Exception as e:
        print('sin draco:', e)
        bpy.ops.export_scene.gltf(**kw)
    print('GLB', ruta, round(os.path.getsize(ruta) / 1e6, 2), 'MB', flush=True)


exportar(completo, OUT_GLB)
exportar(exterior, OUT_GLB.replace('residencia.glb', 'residencia-exterior.glb'))

# ---------------------------------------------------------------- datos del visor
def L(E, x, y, z):
    X, Y = sitio.local_a_m(E, x, y)
    return T(X, Y, z)


VISTA_DE = {}   # (edificio, cuarto) → vista interior
for k, v in INTERIORES.items():
    _, ed, *resto = k.split('_')
    VISTA_DE[('gris' if ed == 'gris' else 'amarilla', '_'.join(resto))] = v
ALIAS = {('gris', 'refrigerios'): 'galeria'}
for (ed, cu), v in list(VISTA_DE.items()):
    if (ed, cu) in ALIAS:
        VISTA_DE[(ed, ALIAS[(ed, cu)])] = v
VISTA_DE[('amarilla', 'bano1')] = VISTA_DE.pop(('amarilla', 'bano'))

CIRC = {'pasillo', 'escalera', 'hall', 'pasillo_alto', 'closet'}
TIPO = {'hosp': 'hospital', 'salon2': 'hospital', 'salonA': 'hospital', 'salonB': 'hospital'}


def cuarto(ed, E, nivel, c, camas):
    poly = unary_union([box(*r) for r in c['rects']])
    cx, cy = poly.centroid.x, poly.centroid.y
    z0 = nivel['z0']
    centro = L(E, cx, cy, z0 + 1.2)
    v = VISTA_DE.get((ed, c['id']))
    if v:
        _, p, t, *_ = v
        cam = L(E, p[0], p[1], p[2] + 0.35); mira = L(E, t[0], t[1], t[2])
    else:
        x0, y0, x1, y1 = max((r for r in c['rects']), key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
        cam = L(E, x0 + 0.45, y0 + 0.45, z0 + 2.1); mira = L(E, cx, cy, z0 + 0.6)
    nombre = c['nombre'].replace(' (por confirmar)', ' · por confirmar')
    return dict(id=c['id'], nombre=nombre, tipo='circulacion' if c['id'] in CIRC else TIPO.get(c['id'], 'cuarto'),
                camas=camas.get(c['id'], 0), centro=centro, cam=cam, mira=mira)


def zona_cuarto(id_, nombre, tipo, bb, z0, cam=None, mira=None):
    (x0, y0, _), (x1, y1, _) = bb
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return dict(id=id_, nombre=nombre, tipo=tipo, camas=0, centro=T(cx, cy, z0 + 1.2),
                cam=cam or T(x0 + 0.3, y0 + 0.3, z0 + 2.6), mira=mira or T(cx, cy, z0 + 0.5))


edificios = []
for pref, ed, nom in (('gr_', 'gris', 'Edificio gris'), ('ca_', 'amarilla', 'Casa amarilla')):
    _, E, d = EDIF[pref]
    camas = INT['camas']['gris' if ed == 'gris' else 'casa']
    pisos = []
    for n, nivel in enumerate(d['niveles'], 1):
        rooms = [cuarto(ed, E, nivel, c, camas) for c in nivel['cuartos']]
        if ed == 'gris' and n == 2:
            v = VISTA_DE[('gris', 'galeria')]
            rooms.append(zona_cuarto('galeria', 'Área de coffee break', 'terraza', zonas['galeria'], nivel['z0'],
                                     cam=L(E, v[1][0], v[1][1], v[1][2] + 0.35), mira=L(E, *v[2])))
            rooms.append(zona_cuarto('terraza', 'Terraza', 'terraza', zonas['terraza_n'], nivel['z0']))
        if ed == 'amarilla' and n == 2:
            rooms.append(zona_cuarto('balcon', 'Balcón', 'terraza', zonas['balcon'], nivel['z0']))
        usados = {r['id'] for p in pisos for r in p['rooms']}
        for r in rooms:
            if r['id'] in usados:
                r['id'] += '_pa'
        nombre_n = 'Planta baja' if n == 1 else 'Planta alta'
        pisos.append(dict(n=n, nombre=nombre_n, z0=nivel['z0'], rooms=rooms))
    edificios.append(dict(id=ed, nombre=nom, nivel2=d['niveles'][1]['z0'], pisos=pisos))

# exteriores
def centro_bb(bb, z=0.0):
    (x0, y0, _), (x1, y1, _) = bb
    return (x0 + x1) / 2, (y0 + y1) / 2


px_, py_ = centro_bb(zonas['parqueo']); gx, gy = centro_bb(zonas['garaje']); tx, ty = centro_bb(zonas['porton_casa'])
exteriores = [
    dict(id='estacionamiento', nombre='Estacionamiento', centro=T(px_, py_, 0.6), cam=T(px_ - 9, py_ + 6, 3.5)),
    dict(id='garaje', nombre='Garaje', centro=T(gx, gy, 1.0), cam=T(gx + 8, gy + 7, 3.0)),
]

# lote y vistas generales
lote = Polygon(sitio.poly_m(sitio.geometria_px()['lote']))
lx0, ly0, lx1, ly1 = lote.bounds
c3 = T(lote.centroid.x, lote.centroid.y, 0)
# punto medio entre los dos edificios (centro de la vista general)
_cg, _ca = huella['gris'].centroid, huella['amarilla'].centroid
cm = T((_cg.x + _ca.x) / 2, (_cg.y + _ca.y) / 2, 0)
presets = {
    'sitio': dict(pos=[cm[0] + 58, 58, cm[2] - 46], target=[cm[0], 2, cm[2]]),
    'calle': dict(pos=L(sitio.CASA, 6.3, -15.0, 1.8), target=L(sitio.CASA, 6.3, 3.0, 2.8)),
    'gris-ext': dict(pos=L(sitio.GRIS, 7.0, -13.0, 2.0), target=L(sitio.GRIS, 7.0, 5.0, 3.2)),
}
etiqueta_calle = T(tx, ty, 0.3)

# vegetación del lote: cerca de los bordes, lejos de edificios, vías y parqueo
rnd = random.Random(7)
# corredores de las vistas desde la calle: sin árboles entre la cámara y la fachada
def corredor(pr):
    from shapely.geometry import LineString
    return LineString([(pr['pos'][0], -pr['pos'][2]), (pr['target'][0], -pr['target'][2])]).buffer(5)


prohibido = unary_union([huella['gris'].buffer(5.5), huella['amarilla'].buffer(5.5),
                         corredor(presets['calle']), corredor(presets['gris-ext'])] +
                        [v.buffer(1.0) for v in vias] + [box(zonas['parqueo'][0][0], zonas['parqueo'][0][1],
                                                              zonas['parqueo'][1][0], zonas['parqueo'][1][1]).buffer(2)])
dentro = lote.buffer(-1.6)
borde = lote.exterior
arboles, palmas, puestos = [], [], []
for _ in range(4000):
    p = Point(rnd.uniform(lx0, lx1), rnd.uniform(ly0, ly1))
    if not dentro.contains(p) or prohibido.contains(p) or borde.distance(p) > 7:
        continue
    if any(p.distance(q) < 7.5 for q in puestos):
        continue
    puestos.append(p)
    x, _, z = T(p.x, p.y, 0)
    (arboles if len(puestos) % 2 else palmas).append([x, z, round(rnd.uniform(5.5, 8.5), 1)])
    if len(puestos) >= 18:
        break

limites = [round(lx0 - 6, 1), round(lx1 + 6, 1), round(-ly1 - 6, 1), round(-ly0 + 6, 1)]   # x0 x1 z0 z1 (three)
datos = dict(
    edificios=edificios, exteriores=exteriores, presets=presets, etiquetaCalle=etiqueta_calle,
    centro=[c3[0], 0, c3[2]], limites=limites,
    lote=[[round(x, 2), round(-y, 2)] for x, y in lote.exterior.coords[:-1]],
    mundo=dict(lote=dict(x0=limites[0] - 10, x1=limites[1] + 10, z0=limites[2] - 10, z1=limites[3] + 10),
               calles=[dict(ancho=round(ancho * sitio.s(), 2), puntos=[[round(x, 2), round(-y, 2)] for x, y in (sitio.m(*q) for q in pl)])
                       for pl, ancho in ((sitio.CA, sitio.CA_ANCHO * 0.8), (sitio.OESTE, sitio.OESTE_ANCHO * 0.8))],
               arboles=arboles, palmas=palmas, centro=[c3[0], c3[2]]),
)
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(datos, f, ensure_ascii=False, indent=1)
print('JSON', OUT_JSON, len(arboles), 'árboles', len(palmas), 'palmas', flush=True)
os._exit(0)
