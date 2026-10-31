"""
Etapas 2 y 3 del encargo de mejora: BLOQUEO con materiales neutros.
  - terreno proporcional sobre el satélite (sitio.py), vías fuera del lote
  - casa amarilla y edificio gris por volúmenes con su identidad de fachada (fachadas.py)
  - cercas sobre los bordes que dan a las vías
Salidas (build/bloqueo/):
  bloqueo.blend, cenital.png (render ortográfico alineado con docs/lote-satelite.png),
  cam_<id>.png para las cuatro comparaciones foto/modelo,
  axo_<edificio>_<nivel>.png (cortes sin cubierta), int_<id>.png (vistas interiores),
  interiores.json (cuartos, muros, huecos y escaleras para planos.py) y recorrido.json (prueba de subida).
Uso:
  python3 blender/bloqueo.py                 (bpy como módulo)
  blender -b -P blender/bloqueo.py           (Blender instalado)
  argumentos opcionales después de `--`:  --solo cenital,casa_frontal  --muestras 32  --ancho 1280
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
from lib import ROOT, box, mesh_obj, cylinder, sphere, coll, join, mat
import sitio
from fachadas import casa_amarilla, edificio_gris, obox

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d
SOLO = arg('--solo', '')
MUESTRAS = int(arg('--muestras', '32'))
ANCHO = int(arg('--ancho', '1280'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.cycles.max_bounces = 4

# ---------------- materiales neutros (bloqueo) ----------------
def neutro(nombre, gris, rough=0.8, metal=0.0):
    c = gris if isinstance(gris, tuple) else (gris, gris, gris)
    return mat('n_' + nombre, color=(c[0], c[1], c[2], 1), rough=rough, metal=metal)

M = dict(
    amarillo=neutro('muro_casa', (0.76, 0.53, 0.19)),          # amarillo ocre de las fotos de la fachada
    gris_claro=neutro('muro_gris', (0.56, 0.58, 0.61)),
    blanco=neutro('blanco', 0.80, 0.6),
    marco=neutro('marco', 0.82, 0.5),
    teja=neutro('cubierta_casa', (0.43, 0.10, 0.05), 0.7),     # teja terracota de las fotos
    lamina=neutro('remate_lamina', (0.70, 0.71, 0.72), 0.45, 0.3),
    lamina_techo=neutro('cubierta_gris', (0.50, 0.51, 0.52), 0.5),
    concreto=neutro('concreto', 0.66),
    hierro=neutro('hierro', 0.04, 0.5, 0.5),
    metal_gris=neutro('metal_gris', 0.22, 0.5, 0.4),
    vidrio_osc=neutro('vidrio', (0.05, 0.06, 0.07), 0.15),
    bloque=neutro('bloque_vidrio', (0.42, 0.45, 0.50), 0.3),
    puerta=neutro('puerta', (0.26, 0.23, 0.21), 0.6),
    puerta_roja=neutro('puerta_gris', (0.24, 0.20, 0.18), 0.6),
    piedra=neutro('piedra', (0.32, 0.31, 0.29), 0.9),
    ceramica=neutro('piso_ceramica', (0.55, 0.50, 0.45), 0.7),
    alero=neutro('cielo_alero', 0.72, 0.8),
    lote=neutro('lote', (0.45, 0.48, 0.42), 0.95),
    via=neutro('via', (0.34, 0.33, 0.31), 0.95),
    entorno=neutro('entorno', (0.40, 0.42, 0.38), 0.95),
    seto=neutro('seto', (0.28, 0.33, 0.26), 0.9),
    pintura_azul=neutro('pintura_parqueo', (0.28, 0.31, 0.38), 0.8),
    vidrio=mat('n_vidrio_claro', color=(0.78, 0.84, 0.88, 1), rough=0.05, alpha=0.12),
    muro_int=neutro('muro_interior', (0.80, 0.79, 0.76), 0.85),
    piso_int=neutro('piso_interior', (0.42, 0.40, 0.37), 0.45),
    escalon=neutro('escalon', (0.50, 0.49, 0.47), 0.6),
    mueble=neutro('mueble', (0.30, 0.27, 0.24), 0.6),
    mueble2=neutro('mueble_claro', (0.45, 0.43, 0.40), 0.7),
    colchon=neutro('colchon', (0.86, 0.86, 0.84), 0.9),
    loza=neutro('loza', 0.92, 0.3),
)

# ---------------- etapa 4a: materiales realistas de interior (los neutros de fachada se conservan)
import materiales
MR = materiales.crear()
M.update(MR)
M.update(puerta=MR['madera_media'], puerta_roja=MR['madera_rojiza'], marco=MR['metal_blanco'],
         escalon=MR['piso_terraza'], bloque=MR['bloque_vidrio'], hierro=MR['metal_negro'],
         muro_int=MR['pintura_gris'], piso_int=MR['piso_gris'])

C_SITIO = coll('Sitio')
C_CASA = coll('Casa_amarilla')
C_GRIS = coll('Edificio_gris')
C_CERCA = coll('Cercas')
C_REF = coll('Referencia_satelite')


def losa_poligono(nombre, pts, z0, z1, m, c):
    n = len(pts)
    verts = [(x, y, z1) for x, y in pts] + [(x, y, z0) for x, y in pts]
    faces = [tuple(range(n))] + [tuple(range(n, 2 * n))[::-1]]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))
    o = mesh_obj(nombre, verts, faces, m, c, 1.0)
    # orientar normales hacia afuera
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)
    return o


def geom_a_pts(g):
    if g.geom_type == 'Polygon':
        return [sitio.poly_m(g)]
    return [sitio.poly_m(p) for p in g.geoms]


# ---------------- sitio ----------------
def construir_sitio():
    g = sitio.geometria_px()
    s = sitio.s()
    box('entorno', (200, 220, 0.1), (-100, -110, -0.16), M['entorno'], C_SITIO, 4.0)
    for i, pts in enumerate(geom_a_pts(g['lote'])):
        losa_poligono(f'lote_{i}', pts, -0.1, 0.0, M['lote'], C_SITIO)
    from shapely.geometry import Polygon, LineString
    caja = Polygon([(-60, -60), (830, -60), (830, 1060), (-60, 1060)])
    for nombre, b in (('via_CA', g['ca']), ('via_oeste', g['oeste'])):
        for i, pts in enumerate(geom_a_pts(b.intersection(caja))):
            losa_poligono(f'{nombre}_{i}', pts, -0.12, -0.03, M['via'], C_SITIO)
    return g


def construir_referencia():
    """Plano con la imagen satelital en su escala (solo para la vista cenital)."""
    img = bpy.data.images.load(os.path.join(ROOT, 'docs', 'lote-satelite.png'))
    m = bpy.data.materials.new('satelite'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(t.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs[0], o.inputs[0])
    x0, y0 = sitio.m(0, 0); x1, y1 = sitio.m(sitio.IMG_W, sitio.IMG_H)
    me = bpy.data.meshes.new('satelite')
    me.from_pydata([(x0, y1, -0.3), (x1, y1, -0.3), (x1, y0, -0.3), (x0, y0, -0.3)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    ob = bpy.data.objects.new('satelite', me); C_REF.objects.link(ob); me.materials.append(m)
    return ob


# ---------------- cercas ----------------
def cercas(g):
    """Murete amarillo con pilares y remates en bola sobre los bordes del lote que dan a una vía.
    Portones en los puntos de acceso conocidos por las fotos."""
    from shapely.geometry import Point
    s = sitio.s()
    lote = g['lote']
    ca, oe = g['ca'], g['oeste']
    portones = [sitio.local_a_m(sitio.CASA, 23.5, 0.5),
                sitio.local_a_m(sitio.GRIS, 1.5, -8.0)]
    pts = list(lote.exterior.coords)
    pil, panel, rejas = [], [], []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if min(mid.distance(ca), mid.distance(oe)) > 4:
            continue
        A, Bm = sitio.m(*a), sitio.m(*b)
        L = math.hypot(Bm[0] - A[0], Bm[1] - A[1])
        if L < 0.5:
            continue
        ang = math.atan2(Bm[1] - A[1], Bm[0] - A[0])
        npan = max(1, round(L / 3.0))
        for k in range(npan):
            u0 = k * L / npan; u1 = (k + 1) * L / npan
            cx = A[0] + math.cos(ang) * (u0 + u1) / 2; cy = A[1] + math.sin(ang) * (u0 + u1) / 2
            lx, ly = sitio.m_a_local(sitio.CASA, cx, cy)
            if -6.0 < lx < 15.6 and -16.0 < ly < -6.0:
                continue
            en_porton = any(math.hypot(cx - px, cy - py) < 2.6 for px, py in portones)
            org = (A[0], A[1], 0)
            o = obox(f'cerca_{i}_{k}', (u1 - u0, 0.2, 0.95 if en_porton else 1.55), (u0, -0.1, 0), org, ang, M['amarillo'], C_CERCA)
            if en_porton:
                o.scale.z = 0.02
                bars = []
                kk = u0 + 0.06
                while kk < u1:
                    bars.append(obox(f'pb_{i}_{k}', (0.022, 0.022, 1.9), (kk, -0.011, 0.05), org, ang, M['hierro'], C_CERCA))
                    kk += 0.12
                for zz in (0.05, 1.85):
                    bars.append(obox(f'pr_{i}_{k}', (u1 - u0, 0.05, 0.06), (u0, -0.025, zz), org, ang, M['hierro'], C_CERCA))
                join(bars, f'porton_{i}_{k}')
            panel.append(o)
            px, py = A[0] + math.cos(ang) * u0, A[1] + math.sin(ang) * u0
            pil.append(box(f'pilar_{i}_{k}', (0.42, 0.42, 1.95), (px - 0.21, py - 0.21, 0), M['amarillo'], C_CERCA))
            pil.append(sphere(f'bola_{i}_{k}', 0.16, (px, py, 2.12), M['blanco'], C_CERCA, 2))


# ---------------- luz y cámaras ----------------
def mundo():
    w = bpy.data.worlds.new('Mundo'); scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(48); sky.sun_rotation = math.radians(-35)
    sky.sun_intensity = 0.25; sky.altitude = 30
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.25
    sun = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN'))
    scene.collection.objects.link(sun)
    sun.data.energy = 2.6; sun.data.angle = math.radians(1.0)
    # sol desde el sureste de la imagen (sombras hacia el noroeste, como en el satélite)
    d = Vector((-0.55, 0.65, -0.75)).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = -0.9


def camara(nombre, loc, target, lens=24.0, sensor=36.0):
    cam = bpy.data.cameras.new(nombre); cam.lens = lens; cam.sensor_width = sensor; cam.sensor_fit = 'HORIZONTAL'
    cam.clip_start = 0.1; cam.clip_end = 600
    co = bpy.data.objects.new(nombre, cam); scene.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


def L(E, x, y, z):
    X, Y = sitio.local_a_m(E, x, y)
    return (X, Y, z)


import bloqueo_vistas as BV
EDIF = {'casa': sitio.CASA, 'gris': sitio.GRIS}


def render(nombre, cam, w, h, muestras, ortho=False, transparente=False):
    scene.camera = cam
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = muestras
    scene.cycles.use_denoising = True
    scene.render.resolution_x = w; scene.render.resolution_y = h
    scene.render.film_transparent = transparente
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA' if transparente else 'RGB'
    scene.render.filepath = os.path.join(OUT, nombre + '.png')
    bpy.ops.render.render(write_still=True)
    print('render', nombre)


def visibles(sitio_on=True, ref_on=False):
    for o in C_SITIO.all_objects:
        o.hide_render = not sitio_on
    for o in C_REF.all_objects:
        o.hide_render = not ref_on


# =====================================================================
g = construir_sitio()
construir_referencia()
cercas(g)
ox, oy, a = sitio.marco(sitio.CASA)
K_CASA = casa_amarilla(M, C_CASA, (ox, oy), a)
ox, oy, a = sitio.marco(sitio.GRIS)
K_GRIS = edificio_gris(M, C_GRIS, (ox, oy), a)
mundo()

import json
import interiores as INT
import amueblado as A
import acabados, muebles3d
from fachadas import colocar
from lib import set_parent
C_LUZ = coll('Luces_interior')
for K, E, clave in ((K_CASA, INT.CASA, 'casa'), (K_GRIS, INT.GRIS, 'gris')):
    acabados.construir(K, E, clave, C_LUZ)
    colocar(K, K.root)
    for o in K.luces_techo:
        set_parent(o, K.root)
    K.luces_muebles = getattr(K, 'luces_muebles', []) + getattr(K, 'luces_acabados', [])
    muebles3d.luces_de_muebles(K, C_LUZ)
for o in C_LUZ.all_objects:
    o.hide_render = True
bpy.context.view_layer.update()
print('objetos en escena:', len(bpy.data.objects))

# --- datos para los planos 2D (misma fuente que el modelo)
def _datos(K, E, clave):
    muebles = []
    for nv in E['niveles']:
        for cid, m, h in A.huellas_nivel(clave, nv['id']):
            muebles.append(dict(nivel=nv['id'], cuarto=cid, t=m['t'], pts=[[round(a, 3), round(b, 3)] for a, b in h.exterior.coords]))
    out = dict(nombre=E['nombre'], aberturas=K.aberturas, niveles=[], escaleras=[], muebles=muebles)
    for nv, mu in zip(E['niveles'], K.interior['muros']):
        ext = INT.exterior(nv)
        out['niveles'].append(dict(id=nv['id'], nombre=nv['nombre'], z0=nv['z0'], z1=nv['z1'],
                                   contorno=list(ext.exterior.coords),
                                   cuartos=[dict(id=c['id'], nombre=c['nombre'], tipo=c.get('tipo', 'cerrado'),
                                                 rects=c['rects'], area=round(INT.poly_cuarto(c).area, 1),
                                                 escalera=c.get('escalera', False)) for c in nv['cuartos']],
                                   muros=mu['ext'] + mu['int'], puertas=mu['puertas']))
    for esc in E['escaleras']:
        t = INT.tramos_escalera(esc)
        out['escaleras'].append(dict(caja=esc['caja'], cajas=t['cajas'], n=t['n'], sube=t['sube'],
                                     huella=t['huella'], marcha=t['marcha'], z0=esc['z0'], z1=esc['z1']))
    return out
print('camas por cuarto:', K_CASA.camas, K_GRIS.camas)
json.dump(dict(casa=_datos(K_CASA, INT.CASA, 'casa'), gris=_datos(K_GRIS, INT.GRIS, 'gris'), supuestos=INT.SUPUESTOS,
               camas=dict(casa=K_CASA.camas, gris=K_GRIS.camas)),
          open(os.path.join(OUT, 'interiores.json'), 'w'), ensure_ascii=False, indent=1)

# --- prueba de recorrido: piso continuo, escalones, altura libre y muros (rayos en la escena)
def _densificar(pts, paso=0.1):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.dist(a, b)
        n = max(1, int(L / paso))
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    out.append(pts[-1])
    return out


def prueba(nombre, E, pts):
    dg = bpy.context.evaluated_depsgraph_get()
    muestras = _densificar(pts)
    z = None
    res = []
    d = 0.0
    prev = None
    for (x, y) in muestras:
        X, Y = sitio.local_a_m(E, x, y)
        zs = 3.5 if z is None else z + 1.2
        hit, loc, *_ = scene.ray_cast(dg, Vector((X, Y, zs)), Vector((0, 0, -1)), distance=6.0)
        zf = loc.z if hit else -9
        paso = 0.0 if z is None else zf - z
        hu, lu, *_ = scene.ray_cast(dg, Vector((X, Y, zf + 0.05)), Vector((0, 0, 1)), distance=6.0)
        libre = (lu.z - zf) if hu else 9.9
        choque = False
        if prev is not None:
            PX, PY, pz = prev
            v = Vector((X - PX, Y - PY, 0)); Ls = v.length
            if Ls > 1e-6:
                for hz in (0.45, 1.5):
                    h2, l2, *_ = scene.ray_cast(dg, Vector((PX, PY, pz + hz)), v.normalized(), distance=Ls)
                    if h2:
                        choque = True
            d += Ls
        res.append(dict(d=round(d, 2), x=round(x, 2), y=round(y, 2), z=round(zf, 3), paso=round(paso, 3),
                        libre=round(libre, 2), choque=choque))
        prev = (X, Y, zf)
        z = zf
    malos = [r for r in res if abs(r['paso']) > 0.21 or r['libre'] < 2.0 or r['choque']]
    print(f'recorrido {nombre}: {len(res)} puntos, z final {res[-1]["z"]}, problemas {len(malos)}')
    return dict(nombre=nombre, puntos=res, problemas=malos)

t_c = INT.tramos_escalera(INT.CASA['escaleras'][0])['marcha']
t_g = INT.tramos_escalera(INT.GRIS['escaleras'][0])['marcha']
RUTAS = {
    'casa': (sitio.CASA, 'Casa amarilla: calle → recepción → comedor → escalera → recámara alta → balcón',
             [(9.575, -1.5), (9.575, 0.6), (8.6, 1.55), (6.4, 2.1), (6.38, 7.7), (t_c[0][0], 7.7)] + t_c +
             [(6.0, 7.7), (6.0, 6.4), (7.1, 5.6), (7.1, 2.4), (7.2, 0.0)]),
    'gris': (sitio.GRIS, 'Edificio gris: calle → acceso → escalera → personas encamadas → área de coffee break',
             [(7.4, -1.0), (7.4, 1.5), (7.4, 6.0), (t_g[0][0], 6.6)] + t_g +
             [(7.6, t_g[-1][1]), (7.6, 6.95), (9.9, 6.95), (11.1, 6.95), (11.1, 9.0), (11.1, 6.95), (7.6, 6.95),
              (7.6, 10.5), (7.5, 12.2)]),
}
REC = [prueba(nombre, E, pts) for (E, nombre, pts) in RUTAS.values()]
json.dump(REC, open(os.path.join(OUT, 'recorrido.json'), 'w'), ensure_ascii=False, indent=1)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'bloqueo.blend'))

def quiere(n):
    return not SOLO or n in SOLO.split(',')

if quiere('cenital'):
    # cámara ortográfica que cubre la imagen satelital completa, píxel a píxel (x2)
    s = sitio.s()
    cx, cy = sitio.m(sitio.IMG_W / 2, sitio.IMG_H / 2)
    cam = camara('cam_cenital', (cx, cy, 120), (cx, cy, 0))
    cam.rotation_euler = (0, 0, 0)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = sitio.IMG_H * s; cam.data.sensor_fit = 'VERTICAL'
    visibles(sitio_on=False, ref_on=False)
    suelo = [o for o in bpy.data.objects if any(t in o.name for t in ('_piso_', 'parqueo', 'coch_piso'))]
    for o in suelo:
        o.hide_render = True
    render('cenital_modelo', cam, sitio.IMG_W * 2, sitio.IMG_H * 2, max(16, MUESTRAS // 2), transparente=True)
    for o in suelo:
        o.hide_render = False
    visibles(sitio_on=True, ref_on=False)
    render('cenital_completo', cam, sitio.IMG_W * 2, sitio.IMG_H * 2, max(16, MUESTRAS // 2))

for k, v in BV.VISTAS.items():
    if not quiere(k) or (SOLO == '' and False):
        continue
    visibles(sitio_on=True, ref_on=False)
    E = EDIF[v['edif']]
    cam = camara('cam_' + k, L(E, *v['pos']), L(E, *v['mira']), v['lens'])
    rw, rh = v['res']
    w = ANCHO if rw >= rh else int(ANCHO * 0.75)
    render('cam_' + k, cam, w, int(w * rh / rw), MUESTRAS)


# --- etapa 3: cortes sin cubierta y vistas interiores
def ocultar(zmax):
    ocultos = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
        if zmin > zmax or any(t in o.name for t in ('techo', 'alero')):
            o.hide_render = True; ocultos.append(o)
    return ocultos


def axo(nombre, E, centro, zcorte, escala):
    cx, cy = sitio.local_a_m(E, *centro)
    ox_, oy_, ang = sitio.marco(E)
    d = Vector((math.cos(ang + math.radians(-125)), math.sin(ang + math.radians(-125)), 0))
    loc = Vector((cx, cy, 0)) + d * 60 + Vector((0, 0, 70))
    cam = camara('cam_' + nombre, tuple(loc), (cx, cy, zcorte - 2.0))
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = escala
    ocultos = ocultar(zcorte)
    for o in C_LUZ.all_objects:
        o.hide_render = True
    render(nombre, cam, ANCHO, int(ANCHO * 0.75), max(16, MUESTRAS // 2))
    for o in ocultos:
        o.hide_render = False


AXOS = {
    'axo_casa_pb': (sitio.CASA, (6.3, 6.9), 2.95, 27),
    'axo_casa_pa': (sitio.CASA, (7.2, 7.6), 6.05, 18),
    'axo_gris_pb': (sitio.GRIS, (7.5, 6.6), 2.9, 24),
    'axo_gris_pa': (sitio.GRIS, (7.5, 6.6), 6.1, 24),
}
for k, (E, c, z, esc) in AXOS.items():
    if SOLO and k in SOLO.split(','):
        axo(k, E, c, z, esc)

from vistas_interiores import INTERIORES
pedidos = [k for k in INTERIORES if SOLO and (k in SOLO.split(',') or 'interiores' in SOLO.split(','))]
if pedidos:
    for o in C_LUZ.all_objects:
        o.hide_render = False
    visibles(sitio_on=True, ref_on=False)
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3; scene.cycles.glossy_bounces = 2; scene.cycles.transmission_bounces = 4
    scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False; scene.cycles.blur_glossy = 1.0
    scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.03
    expo0 = scene.view_settings.exposure
    for k in pedidos:
        E, p, q, lens, expo = INTERIORES[k]
        cam = camara('cam_' + k, L(E, *p), L(E, *q), lens)
        scene.view_settings.exposure = expo
        render(k, cam, ANCHO, int(ANCHO * 9 / 16), MUESTRAS)
    scene.view_settings.exposure = expo0
    for o in C_LUZ.all_objects:
        o.hide_render = True
print('listo')
