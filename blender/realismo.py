"""
Capa de REALISMO sobre el modelo (fase "como Astra"): materiales de fachada con desgaste, teja metálica,
baldosa, piedra, hierro, asfalto, cielo y sol, jardineras, hierba, arbustos con flor, palmas y árboles.
No toca los scripts del modelo: abre build/bloqueo/bloqueo.blend y guarda build/muestra/realismo.blend.

Uso:
  python3 blender/realismo.py                      (bpy como módulo)
  blender -b -P blender/realismo.py                (Blender instalado)
Luego:  muestra_vistas.py -- --blend build/muestra/realismo.blend --sufijo despues
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio
import vegetacion as V

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEN = os.path.join(ROOT, 'assets', 'textures', 'gen')
OUT = os.path.join(ROOT, 'build', 'muestra')
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'bloqueo', 'bloqueo.blend'))
sc = bpy.context.scene


# materiales de fachada y sitio: materiales_fachada.py (también los usa el sobrevuelo v2)
from materiales_fachada import *  # noqa: F401,F403
aplicar()
terracota = bpy.data.materials['remate_terracota']


# ================================================================== cielo y sol
def cielo():
    w = sc.world; nt = w.node_tree
    sky = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexSky')
    # sol de media mañana desde el frente izquierdo de la casa (como en la foto de la fachada)
    ox, oy, a = sitio.marco(sitio.CASA)
    frente = Vector((math.sin(a), -math.cos(a), 0))          # dirección local -y en el mundo
    izq = Vector((-math.cos(a), -math.sin(a), 0))            # dirección local -x
    hacia_sol = (frente * 0.78 + izq * 0.62).normalized()
    elev = math.radians(58)
    d = Vector((hacia_sol.x * math.cos(elev), hacia_sol.y * math.cos(elev), math.sin(elev)))
    sky.sun_elevation = elev
    sky.sun_rotation = math.atan2(d.x, d.y)                 # Blender: rotación medida desde +y
    if hasattr(sky, 'sun_disc'):
        sky.sun_disc = False                                  # el disco lo pone la lámpara
    for k, v in (('air_density', 1.0), ('aerosol_density', 0.5), ('ozone_density', 1.4)):
        if hasattr(sky, k):
            setattr(sky, k, v)
    sky.altitude = 120
    sky.sun_intensity = 1.0
    # Escala de luz medida (cal_sol): con el cielo a fuerza 1, el sol físico equivale a una lámpara de 135.
    # Se conserva el nivel de cielo del modelo anterior (0,0625) para que los interiores no cambien,
    # y el sol pasa a su valor físico (8,4 en vez de 2,6): más contraste y sombras definidas.
    CIELO = 0.0625
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = CIELO
    sol = bpy.data.objects['sol']
    sol.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sol.data.energy = 135 * CIELO
    sol.data.angle = math.radians(0.6)
    sol.data.color = (1.0, 0.97, 0.92)
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.35


cielo()


# ================================================================== jardín del frente
col = bpy.data.collections.new('Vegetacion'); sc.collection.children.link(col)
ox, oy, A = sitio.marco(sitio.CASA)


def W(x, y, z=0.0):
    X, Y = sitio.local_a_m(sitio.CASA, x, y)
    return (X, Y, z)


def poner(o, x, y, z=0.0, giro=0.0, esc=1.0):
    o.location = W(x, y, z); o.rotation_euler = (0, 0, A + giro); o.scale = (esc,) * 3
    return o


def jardinera(nombre, x0, y0, x1, y1, alto=0.10):
    """Cama de tierra sobre la baldosa con borde de bloque pintado."""
    me = bpy.data.meshes.new(nombre)
    v = [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, alto), (x1, y0, alto), (x1, y1, alto), (x0, y1, alto)]
    f = [(4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.materials.append(tierra)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    o.location = W(0, 0); o.rotation_euler = (0, 0, A)
    return o


tierra = suelo_jardin('tierra_jardinera', pasto=0.25)
YF = -7.4
camas = [(-5.0, -12.0, 2.25, YF - 0.25), (9.95, -12.0, 14.6, YF - 0.25),        # afuera, a los lados de la rampa
         (-0.9, YF + 0.25, -0.55, -5.7), (9.75, YF + 0.25, 12.4, -1.0)]          # adentro, junto a la cerca
for i, (x0, y0, x1, y1) in enumerate(camas):
    jardinera(f'jardinera_{i}', x0, y0, x1, y1)
    h = V.hierba(f'hierba_{i}', col, (x0, y0, x1, y1), densidad=150 if i < 2 else 110, seed=10 + i, z=0.10, maleza=0.25,
                verde=((0.05, 0.11, 0.015), (0.30, 0.31, 0.07)))
    h.location = W(0, 0); h.rotation_euler = (0, 0, A)
# hierbita en las juntas al pie de la cerca, del lado de adentro
h = V.hierba('maleza_cerca', col, (-5.0, YF + 0.12, 14.6, YF + 0.5), densidad=70, seed=31, alto=(0.06, 0.2), maleza=0.1)
h.location = W(0, 0); h.rotation_euler = (0, 0, A)

HOJA = os.path.join(GEN, 'copa_mango.png')          # gen_tarjetas.py: hojas 3D renderizadas
HOJA_FINA = os.path.join(GEN, 'copa_fina.png')
# palma real a la derecha del portón grande (la de la foto) y la que asoma al fondo
poner(V.palma('palma_portón', col, alto=9.6, frondas=14, seed=3, inclin=0.08), 12.4, -9.9)
poner(V.palma('palma_fondo_1', col, alto=12.5, frondas=13, seed=7), -3.5, 15.5, giro=1.0)
poner(V.palma('palma_fondo_2', col, alto=10.5, frondas=12, seed=9), 13.5, 17.0, giro=2.0)
for i, (x, y) in enumerate([(15.6, -6.0), (16.4, -5.2), (15.2, -4.6)]):           # areca en macolla, junto al garaje
    poner(V.palma(f'areca_{i}', col, alto=4.2 + i * 0.8, frondas=9, seed=20 + i, tipo='areca', inclin=0.3), x, y, giro=i)
# árboles de copa (mango y vecinos) detrás de la casa y a la derecha
poner(V.arbol('mango_izq', col, alto=9.5, copa=4.6, seed=4, imagen=HOJA), -7.5, 5.0)
poner(V.arbol('arbol_fondo', col, alto=12.0, copa=5.0, seed=5, imagen=HOJA), 6.0, 24.0, giro=0.7)
poner(V.arbol('arbol_der', col, alto=10.0, copa=3.4, seed=6, imagen=HOJA_FINA, verde=(0.85, 0.9, 0.8)), 17.8, -9.6)
poner(V.arbol('arbol_der_2', col, alto=11.0, copa=4.2, seed=8, imagen=HOJA), 22.0, 6.0)
# arbustos con flor de la foto: alamanda amarilla a la izquierda, ixora roja a la derecha del portón
poner(V.arbusto('alamanda_1', col, radio=1.3, alto=1.5, hojas=4200, flores=420, color_flor=(0.95, 0.70, 0.03), seed=2), 0.5, -9.7)
poner(V.arbusto('alamanda_2', col, radio=0.9, alto=1.1, hojas=2200, flores=180, color_flor=(0.95, 0.70, 0.03), seed=12), -2.0, -9.1)
poner(V.arbusto('ixora_1', col, radio=0.95, alto=1.7, hojas=3600, flores=90, color_flor=(0.80, 0.08, 0.12), hoja=(0.11, 0.045), seed=5, forma='racimo'), 11.0, -8.55)
poner(V.arbusto('verde_1', col, radio=0.9, alto=1.2, hojas=2600, seed=14, verde=((0.04, 0.10, 0.02), (0.15, 0.24, 0.04))), 13.9, -10.8)
poner(V.arbusto('verde_2', col, radio=0.6, alto=0.9, hojas=1400, seed=15), -4.3, -8.4)
poner(V.arbusto('verde_adentro_1', col, radio=0.55, alto=1.0, hojas=1300, seed=16), 11.2, -5.5)
poner(V.arbusto('verde_adentro_2', col, radio=0.45, alto=0.8, hojas=1000, flores=25, color_flor=(0.80, 0.08, 0.12), seed=17, forma='racimo'), 10.4, -2.0)

# ================================================================== detalles de arquitectura
# 1) Cantos biselados: los bordes rectos perfectos delatan el 3D; un bisel de 1-2 cm atrapa la luz.
BISEL = ('muro', 'cerca', 'pilar', 'col', 'coch', 'losa', 'balcon', 'garaje', 'torre', 'alfeizar', 'marco',
         'pmarco', 'zocalo', 'escalon', 'arco', 'porche', 'remate', 'cap', 'canto', 'gal', 'parqueo')
nb = 0
for c in ('Casa_amarilla', 'Edificio_gris', 'Cercas'):
    for o in bpy.data.collections[c].all_objects:
        if o.type != 'MESH' or len(o.data.polygons) > 400:
            continue
        partes = o.name.split('_')
        if not any(p in partes for p in BISEL) or 'mueble' in partes:
            continue
        b = o.modifiers.new('bisel', 'BEVEL')
        b.width = 0.012; b.segments = 2; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40)
        b.harden_normals = False
        nb += 1
print('biseles', nb, flush=True)

# 2) Medallón de la cochera: roseta en relieve como en la foto (aro, 12 pétalos y botón central)
med = next(o for o in bpy.data.objects if o.name.startswith('ca_medallon'))
blanco = bpy.data.materials['n_blanco']
def pieza(nombre, me, loc, rot=(0, 0, 0), esc=(1, 1, 1)):
    o = bpy.data.objects.new(nombre, me); med.users_collection[0].objects.link(o)
    o.parent = med; o.location = loc; o.rotation_euler = rot; o.scale = esc
    me.materials.append(blanco)
    for pol in me.polygons:
        pol.use_smooth = True
    return o
import bmesh
def malla_bm(nombre, f):
    bm = bmesh.new(); f(bm); me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free(); return me
aro = malla_bm('medallon_aro', lambda bm: bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.44, radius2=0.40, depth=0.05))
pieza('ca_medallon_aro', aro, (0, 0, 0.125))
for k in range(12):
    a = 2 * math.pi * k / 12
    pet = malla_bm(f'petalo_{k}', lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0))
    pieza(f'ca_medallon_petalo_{k}', pet, (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.11), (0, 0, a), (0.15, 0.055, 0.035))
pieza('ca_medallon_boton', malla_bm('boton', lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.075)), (0, 0, 0.12))

# 2b) Fascia blanca en el borde de los techos de la casa (en la foto el canto del alero es blanco)
fascia = estuco('fascia_blanca', (0.76, 0.75, 0.70), sucio=0.0, manchas=0.15, rough=0.6)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('ca_') and o.data.materials and o.data.materials[0] and o.data.materials[0].name == 'n_cubierta_casa':
        o.data.materials.append(fascia)
        k = len(o.data.materials) - 1
        for pol in o.data.polygons:
            if abs(pol.normal.z) < 0.25:
                pol.material_index = k
# el canto de los techos bajos que queda DENTRO de la casa (donde se juntan con la torre) se veía como
# una viga diagonal en el cielo de la recepción: se borran esas caras
import bmesh
PLANTA = [(0, 0, 4.4, 13.8), (4.4, 0, 10.0, 13.8), (10.0, 0.9, 12.6, 13.8), (5.3, -0.6, 9.1, 0)]
borradas = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('ca_') and 'techo' in o.name and 'alero' not in o.name:
        bm = bmesh.new(); bm.from_mesh(o.data)
        mw = o.matrix_world
        fuera = []
        for f in bm.faces:
            if abs(f.normal.z) > 0.25:
                continue
            c = mw @ f.calc_center_median()
            lx, ly = sitio.m_a_local(sitio.CASA, c.x, c.y)
            if any(x0 + 0.25 < lx < x1 - 0.25 and y0 + 0.25 < ly < y1 - 0.25 for x0, y0, x1, y1 in PLANTA):
                fuera.append(f)
        if fuera:
            bmesh.ops.delete(bm, geom=fuera, context='FACES'); borradas += len(fuera)
            bm.to_mesh(o.data)
        bm.free()
print('cantos interiores borrados', borradas, flush=True)

# 2c) Portón: pasamanos curvo siguiendo el arco y anillos decorativos entre dos curvas (como en la foto)
hierro = bpy.data.materials.get('metal_negro')
for (p0, p1) in [(-0.6, 2.0), (2.6, 9.4)]:
    x0, x1 = p0 + 0.05, p1 - 0.05
    arco = 0.35 if p1 - p0 > 4 else 0.2
    M = V.Malla(); mi = M.mat(hierro)
    for dz in (0.0, -0.28):
        pts = [(x0 + (x1 - x0) * i / 24, -7.4, 1.85 + arco * math.sin(math.pi * i / 24) - 0.03 + dz) for i in range(25)]
        V.tubo(M, pts, [0.018] * 25, 6, mi, tapa=False)
    n = int((x1 - x0) / 0.24)
    for i in range(n):
        t = (i + 0.5) / n
        cx = x0 + (x1 - x0) * t; cz = 1.85 + arco * math.sin(math.pi * t) - 0.17
        ring = [(cx + 0.1 * math.cos(2 * math.pi * k / 16), -7.4, cz + 0.1 * math.sin(2 * math.pi * k / 16)) for k in range(17)]
        V.tubo(M, ring, [0.008] * 17, 5, mi, tapa=False)
    o = M.objeto(f'ca_porton_adorno_{p0}', col)
    o.location = W(0, 0); o.rotation_euler = (0, 0, A)

# 2d) Interiores de la casa: piso cerámico beige más cálido y brillante (como el de las fotos de adentro)
pc = bpy.data.materials.get('piso_casa')
if pc:
    for nd in pc.node_tree.nodes:
        if nd.bl_idname == 'ShaderNodeTexBrick':
            nd.inputs['Color1'].default_value = (0.66, 0.56, 0.42, 1)
            nd.inputs['Color2'].default_value = (0.62, 0.53, 0.40, 1)
            nd.inputs['Mortar'].default_value = (0.50, 0.44, 0.36, 1)
        elif nd.bl_idname == 'ShaderNodeMapRange':
            nd.inputs['To Min'].default_value = 0.06

# 3) Faroles de pared en los pilares del portón (lado de la calle), como en la foto
negro = bpy.data.materials.get('metal_negro') or bpy.data.materials['n_vidrio']
vid = bpy.data.materials['n_vidrio_claro']
def farol(nombre, x, y, z):
    M = V.Malla(); mn = M.mat(negro); mv = M.mat(vid)
    def caja(x0, y0, z0, x1, y1, z1, mi):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        M.add([Vector(p) for p in v], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], 0.5, mi)
    caja(-0.03, 0.0, -0.03, 0.03, 0.18, 0.03, mn)                    # brazo desde el pilar
    caja(-0.09, 0.14, -0.20, 0.09, 0.32, -0.18, mn)                  # base
    caja(-0.075, 0.155, -0.18, 0.075, 0.305, 0.06, mv)               # vidrio
    for dx in (-0.08, 0.08):
        for dy in (0.15, 0.31):
            caja(dx - 0.008, dy - 0.008, -0.18, dx + 0.008, dy + 0.008, 0.06, mn)
    caja(-0.11, 0.12, 0.06, 0.11, 0.34, 0.09, mn)                    # tapa
    caja(-0.04, 0.19, 0.09, 0.04, 0.27, 0.16, mn)
    o = M.objeto(nombre, col, suave=False)
    o.location = W(x, y, z); o.rotation_euler = (0, 0, A + math.pi)   # el brazo sale hacia la calle (-y local)
    return o
for xx in (2.3, 9.7):
    farol(f'farol_{xx}', xx, YF - 0.22, 1.62)

# 4) Poste de luz de concreto con lámpara en la acera de la C.A (en la foto asoma detrás de la casa)
gris_c = estuco('concreto_poste', (0.45, 0.44, 0.42), sucio=0.4, manchas=0.3)
def poste(nombre, x, y):
    M = V.Malla(); mc = M.mat(gris_c); mn = M.mat(hierro)
    V.tubo(M, [(0, 0, 0), (0, 0, 9.0)], [0.16, 0.10], 10, mc)
    V.tubo(M, [(0, 0, 8.2), (0.6, 0, 8.6), (1.6, 0, 8.7)], [0.035, 0.03, 0.03], 6, mn, tapa=False)
    V.tubo(M, [(1.45, 0, 8.68), (1.75, 0, 8.66)], [0.09, 0.07], 8, mn)
    V.tubo(M, [(-0.7, 0, 8.8), (0.7, 0, 8.8)], [0.04, 0.04], 6, mn)       # cruceta de los cables
    o = M.objeto(nombre, col); o.location = W(x, y); o.rotation_euler = (0, 0, A + math.pi / 2)
    return o
poste('poste_ca_1', 15.5, -13.2)
poste('poste_ca_2', -14.0, -13.2)
# cables entre postes (catenaria simple)
M = V.Malla(); mc = M.mat(hierro)
for dz in (8.8, 8.55):
    a, b = Vector(W(15.5, -13.2 + 0.0, dz)), Vector(W(-14.0, -13.2, dz))
    pts = [tuple(a.lerp(b, i / 30) - Vector((0, 0, 0.6 * math.sin(math.pi * i / 30)))) for i in range(31)]
    V.tubo(M, pts, [0.008] * 31, 4, mc, tapa=False)
M.objeto('cables_ca', col)
# matas en macetas junto a la entrada principal y en la cochera (fotos del porche)
maceta = bpy.data.materials.get('maceta_gris') or terracota
for i, (x, y) in enumerate([(9.0, -0.5), (10.2, -0.5), (3.6, -2.2), (-0.6, -0.4)]):
    M = V.Malla(); mm = M.mat(maceta)
    V.tubo(M, [(0, 0, 0), (0, 0, 0.42)], [0.17, 0.23], 14, mm)
    o = M.objeto(f'maceta_{i}', col); o.location = W(x, y)
    poner(V.arbusto(f'mata_maceta_{i}', col, radio=0.35, alto=0.75, hojas=700, hoja=(0.16, 0.05), seed=40 + i,
                    verde=((0.03, 0.09, 0.015), (0.12, 0.22, 0.04))), x, y, z=0.4)

# ---- entorno: árboles donde el satélite muestra copa (lote, franja intermedia, bosque del sur)
import random
import arboles_satelite as AS
from shapely.geometry import Point, Polygon
rnd = random.Random(77)
col_ent = bpy.data.collections.new('Entorno'); sc.collection.children.link(col_ent)
bases = []
for k in range(6):
    img = HOJA if k % 3 else HOJA_FINA
    bases.append(V.arbol(f'arbol_base_{k}', col_ent, alto=rnd.uniform(7, 11.5), copa=rnd.uniform(3.0, 5.0), seed=100 + k,
                         imagen=img, verde=(0.82 + 0.05 * k, 0.92, 0.8)))
bases += [V.palma(f'palma_base_{k}', col_ent, alto=rnd.uniform(9, 13), frondas=12, seed=200 + k) for k in range(2)]
for b in bases:
    b.location = (0, 0, -500)                          # las bases quedan escondidas bajo el terreno
g = sitio.geometria_px()
calles = [g['ca'].buffer(3), g['oeste'].buffer(2)]
huellas = []
for cn in ('Casa_amarilla', 'Edificio_gris'):
    xs, ys = [], []
    for o in bpy.data.collections[cn].all_objects:
        if o.type == 'MESH':
            for v in o.bound_box:
                wv = o.matrix_world @ Vector(v); xs.append(wv.x); ys.append(wv.y)
    huellas.append((min(xs) - 1.5, min(ys) - 1.5, max(xs) + 1.5, max(ys) + 1.5))
def excluir(X, Y):
    if any(x0 < X < x1 and y0 < Y < y1 for x0, y0, x1, y1 in huellas):
        return True
    lx, ly = sitio.m_a_local(sitio.CASA, X, Y)
    if -7 < lx < 24 and -17 < ly < -0.5:              # jardín del frente: plantas puestas a mano
        return True
    if -3 < lx < 17 and 14 < ly < 27:                  # patio de grava detrás de la casa (foto del patio)
        return True
    pxy = sitio.m_a_px(X, Y)
    return any(c.contains(Point(pxy)) for c in calles)
CAMARAS = [(5.0, -15.2), (5.6, -6.3), (9.6, 20.0)]                         # casa (frente, acceso, patio)
CAMARAS_G = [(7.0, 22.0), (-4.6, -0.6)]                                     # gris (galería, acceso)
camw = [W(*c)[:2] for c in CAMARAS] + [sitio.local_a_m(sitio.GRIS, *c) for c in CAMARAS_G]
def excluir2(X, Y):
    return excluir(X, Y) or any(math.hypot(X - cx, Y - cy) < 5 for cx, cy in camw)
n_sat = AS.colocar(col_ent, bases, excluir2, paso=3.6, fuera_de=g['lote'].buffer(8))

# ---- dentro del lote, a mano (fotos): hilera de palmas en la orilla de la calle de tierra, árboles en la
# franja intermedia y junto a la galería del gris (papayos y un árbol grande en la foto del jardín)
from shapely.geometry import LineString
oeste_m = LineString([sitio.m(*p) for p in sitio.OESTE])
lote_m = Polygon([sitio.m(*p) for p in g['lote'].exterior.coords])
borde = lote_m.exterior
i = 0; d = 2.0
while d < borde.length:
    p = borde.interpolate(d)
    if oeste_m.distance(p) < 6:
        q = lote_m.buffer(-2.2).exterior.interpolate(lote_m.buffer(-2.2).exterior.project(p))
        if not excluir2(q.x, q.y):
            V.instancia(bases[6 + i % 2], f'palma_orilla_{i}', col_ent, (q.x, q.y, 0), rnd.uniform(0, 6.28), rnd.uniform(0.75, 1.0))
            i += 1
    d += rnd.uniform(3.8, 5.0)
GX = lambda x, y: sitio.local_a_m(sitio.GRIS, x, y)
papayo = V.arbol('papayo', col_ent, alto=4.5, copa=1.6, tarjetas=260, seed=301, imagen=HOJA_FINA, verde=(1.0, 1.05, 0.85))
papayo.location = (*GX(3.5, 19.5), 0)
V.instancia(papayo, 'papayo_2', col_ent, (*GX(1.0, 21.0), 0), 1.0, 0.9)
V.instancia(bases[1], 'arbol_jardin_gris', col_ent, (*GX(13.5, 25.5), 0), 0.4, 0.85)
for k, (x, y) in enumerate([(8.0, 30.0), (16.0, 32.0), (0.0, 34.0)]):                 # franja intermedia (casa local)
    V.instancia(bases[k % 6], f'arbol_franja_{k}', col_ent, W(x, y), rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.0))
# casas vecinas donde el satélite muestra techos (fuera del lote)
mats_techo = {'rojo': teja_metalica('techo_vecino_rojo', (0.34, 0.07, 0.045)),
              'terracota': teja_metalica('techo_vecino_terracota', (0.42, 0.16, 0.08)),
              'lamina': lamina_ondulada('techo_vecino_lamina', (0.52, 0.53, 0.54)),
              'oxido': teja_metalica('techo_vecino_oxido', (0.25, 0.12, 0.07))}
muros_v = [estuco(f'muro_vecino_{i}', c, sucio=0.6, manchas=0.4) for i, c in
           enumerate([(0.70, 0.68, 0.62), (0.60, 0.45, 0.30), (0.55, 0.58, 0.60), (0.62, 0.52, 0.25)])]
nv = 0
for rect, ctecho in AS.techos_satelite(g['lote'].buffer(4), [g['ca'], g['oeste']]):
    AS.casa_vecina(f'vecino_{nv}', col_ent, rect, ctecho, muros_v[nv % 4], mats_techo); nv += 1
print('casas vecinas', nv, flush=True)

# más allá de la imagen satelital: anillo para que el horizonte no quede vacío
k = sitio.s()
X0, Y1 = sitio.m(0, 0); X1, Y0 = sitio.m(sitio.IMG_W, sitio.IMG_H)
n = 0
while n < 160:
    ang = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(40, 170)
    x, y = 10 + math.cos(ang) * r, -5 + math.sin(ang) * r
    if X0 < x < X1 and Y0 < y < Y1:
        continue
    V.instancia(rnd.choice(bases), f'lejos_{n}', col_ent, (x, y, -0.15), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.4))
    n += 1
print('árboles por satélite', n_sat, '+ horizonte', n, flush=True)

# ---- suelo hasta el horizonte y colinas lejanas (antes, mirando desde arriba, se veía el vacío bajo el horizonte)
import bmesh
def colinas(nombre, r0, r1, alto, seed):
    rnd2 = random.Random(seed)
    bm = bmesh.new()
    na, nr = 96, 10
    fases = [rnd2.uniform(0, 6.28) for _ in range(4)]
    vs = []
    for i in range(nr + 1):
        r = r0 + (r1 - r0) * i / nr
        fila = []
        for j in range(na):
            a = 2 * math.pi * j / na
            h = alto * math.sin(math.pi * i / nr) * (0.55 + 0.25 * math.sin(3 * a + fases[0]) + 0.2 * math.sin(7 * a + fases[1]))
            fila.append(bm.verts.new((10 + r * math.cos(a), -5 + r * math.sin(a), h - 0.3)))
        vs.append(fila)
    for i in range(nr):
        for j in range(na):
            bm.faces.new((vs[i][j], vs[i][(j + 1) % na], vs[i + 1][(j + 1) % na], vs[i + 1][j]))
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials['n_entorno'])
    for pol in me.polygons:
        pol.use_smooth = True
    o = bpy.data.objects.new(nombre, me); col_ent.objects.link(o)
    return o
colinas('llano', 95, 900, 6, 1)
colinas('colinas_lejos', 900, 2600, 260, 2)

# ---- patio de grava detrás de la casa (foto casa-amarilla-patio)
grava = Mat('grava_patio')
w_ = grava.pos('world')
vo = grava.n('ShaderNodeTexVoronoi', feature='F1'); vo.inputs['Scale'].default_value = 28; grava.l(w_, vo.inputs['Vector'])
ed = grava.n('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE'); ed.inputs['Scale'].default_value = 28; grava.l(w_, ed.inputs['Vector'])
cg = grava.rampa(vo.outputs['Color'], [(0.0, (0.20, 0.20, 0.19)), (0.5, (0.36, 0.36, 0.34)), (1.0, (0.55, 0.54, 0.51))])
cg = grava.mezcla(grava.rango(ed.outputs['Distance'], 0.0, 0.08, 1, 0), cg, (0.08, 0.075, 0.07))
grava.base(cg, 0.85, grava.bump(grava.rango(ed.outputs['Distance'], 0.0, 0.15), 0.9, 0.02), spec=0.35)
me = bpy.data.meshes.new('patio_grava')
pts = [(-1.0, 15.7), (15.5, 15.7), (16.5, 25.5), (-2.5, 25.5)]
me.from_pydata([(x, y, 0.02) for x, y in pts], [], [(0, 1, 2, 3)]); me.materials.append(grava.m)
o = bpy.data.objects.new('patio_grava', me); col.objects.link(o); o.location = W(0, 0); o.rotation_euler = (0, 0, A)

for o in bpy.data.objects:
    if o.name.startswith('satelite'):
        o.hide_render = True
    elif o.type == 'LIGHT':
        o.hide_render = False             # lámparas interiores encendidas (se ven por las ventanas y al entrar)

ruta = os.path.join(OUT, 'realismo.blend')
bpy.ops.wm.save_as_mainfile(filepath=ruta, relative_remap=True, compress=True)
print('guardado', ruta, len(bpy.data.objects), 'objetos', flush=True)
