"""
Vegetación procedural en 3D (sin descargas): palmas reales (tronco anillado, capitel verde y frondas
con pinnas), arbustos de hoja con flores, árboles de copa grande y matas de hierba.
Cada función devuelve un objeto con su malla; para repetirlos se usan duplicados enlazados
(misma malla), así la escena pesa poco y la web puede instanciarlos.
"""
import os, math, random
import bpy
import numpy as np
from mathutils import Vector, Matrix

# ------------------------------------------------------------------ materiales de vegetación
_M = {}


def _nodos(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def mat_hoja(nombre, c0, c1, transl=0.35, rough=0.42):
    """Hoja con tono por cara (atributo 'tinte') entre c0 y c1, brillo de cutícula y translucidez."""
    if nombre in _M:
        return _M[nombre]
    m, nt, out = _nodos(nombre)
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'tinte'
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].color = (*c0, 1); rp.color_ramp.elements[1].color = (*c1, 1)
    nt.links.new(at.outputs['Fac'], rp.inputs['Fac'])
    pb = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(rp.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = rough
    pb.inputs['Specular IOR Level'].default_value = 0.45
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    hsv.inputs['Saturation'].default_value = 1.25; hsv.inputs['Value'].default_value = 1.15
    nt.links.new(rp.outputs['Color'], hsv.inputs['Color'])
    nt.links.new(hsv.outputs['Color'], tr.inputs['Color'])
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = transl
    nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (*[(a + b) / 2 for a, b in zip(c0, c1)], 1)
    _M[nombre] = m
    return m


def mat_tronco(nombre, c0, c1, anillos=0.0, rough=0.85):
    """Corteza: color con ruido y, si anillos > 0, bandas horizontales cada `anillos` m (palma real)."""
    if nombre in _M:
        return _M[nombre]
    m, nt, out = _nodos(nombre)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].color = (*c0, 1); rp.color_ramp.elements[1].color = (*c1, 1)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
    pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); pb.inputs['Roughness'].default_value = rough
    nt.links.new(rp.outputs['Color'], pb.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6
    if anillos > 0:
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = 0.314 / anillos   # periodo de la onda: 0,314 / escala; wv.inputs['Distortion'].default_value = 0.6
        wv.inputs['Detail'].default_value = 2
        nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'ADD'
        nt.links.new(wv.outputs['Fac'], mx.inputs[0]); nt.links.new(nz.outputs['Fac'], mx.inputs[1])
        nt.links.new(mx.outputs[0], bump.inputs['Height'])
    else:
        nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 40; nz2.inputs['Detail'].default_value = 10
        nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
        nt.links.new(nz2.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], pb.inputs['Normal'])
    nt.links.new(pb.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (*c0, 1)
    _M[nombre] = m
    return m


def mat_tarjeta(nombre, imagen, tinte=(1, 1, 1), transl=0.3):
    """Tarjeta de follaje con alfa (copa de árboles lejanos)."""
    nombre = f'{nombre}_{os.path.splitext(os.path.basename(imagen))[0]}_{"%.2f%.2f" % tinte[:2]}'
    if nombre in _M:
        return _M[nombre]
    m, nt, out = _nodos(nombre)
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(imagen, check_existing=True)
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'tinte'
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].color = (tinte[0] * 0.75, tinte[1] * 0.8, tinte[2] * 0.7, 1)
    rp.color_ramp.elements[1].color = (tinte[0] * 1.15, tinte[1] * 1.1, tinte[2] * 0.95, 1)
    nt.links.new(at.outputs['Fac'], rp.inputs['Fac'])
    nt.links.new(tx.outputs['Color'], mix.inputs['A']); nt.links.new(rp.outputs['Color'], mix.inputs['B'])
    pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); pb.inputs['Roughness'].default_value = 0.5
    nt.links.new(mix.outputs['Result'], pb.inputs['Base Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); nt.links.new(mix.outputs['Result'], tr.inputs['Color'])
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = transl
    nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    tp = nt.nodes.new('ShaderNodeBsdfTransparent')
    ma = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tx.outputs['Alpha'], ma.inputs['Fac'])
    nt.links.new(tp.outputs[0], ma.inputs[1]); nt.links.new(mx.outputs[0], ma.inputs[2])
    nt.links.new(ma.outputs[0], out.inputs['Surface'])
    m.blend_method = 'HASHED' if hasattr(m, 'blend_method') else None
    m.diffuse_color = (0.12, 0.2, 0.08, 1)
    _M[nombre] = m
    return m


# ------------------------------------------------------------------ armado de mallas
class Malla:
    """Acumula vértices, caras, tinte por cara y material por cara; crea un objeto al final."""
    def __init__(self):
        self.v = []; self.f = []; self.t = []; self.mi = []; self.uv = []
        self.mats = []

    def mat(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, verts, caras, tinte, mi, uvs=None):
        b = len(self.v)
        self.v.extend(verts)
        for c in caras:
            self.f.append([b + i for i in c]); self.t.append(tinte); self.mi.append(mi)
            if uvs is not None:
                self.uv.append([uvs[i] for i in c])
            else:
                self.uv.append([(0, 0)] * len(c))

    def objeto(self, nombre, col, suave=True):
        me = bpy.data.meshes.new(nombre)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mi)
        if suave:
            me.polygons.foreach_set('use_smooth', [True] * len(self.f))
        at = me.color_attributes.new('tinte', 'FLOAT_COLOR', 'CORNER')
        vals = []
        for p, t in zip(me.polygons, self.t):
            vals.extend([t, t, t, 1.0] * p.loop_total)
        at.data.foreach_set('color', vals)
        uvl = me.uv_layers.new(name='UVMap')
        flat = [c for poly in self.uv for uv in poly for c in uv]
        uvl.data.foreach_set('uv', flat)
        me.update()
        o = bpy.data.objects.new(nombre, me)
        col.objects.link(o)
        return o


def _base(d):
    """Base ortonormal (t, s, n) con t = d."""
    t = Vector(d).normalized()
    up = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
    s = t.cross(up).normalized()
    n = s.cross(t).normalized()
    return t, s, n


def tubo(M, puntos, radios, segs, mi, tinte=0.5, tapa=True):
    """Tubo por una polilínea con radio variable (troncos y ramas)."""
    verts, caras = [], []
    n = len(puntos)
    for i, (p, r) in enumerate(zip(puntos, radios)):
        d = (Vector(puntos[min(i + 1, n - 1)]) - Vector(puntos[max(i - 1, 0)]))
        t, s, nn = _base(d)
        for k in range(segs):
            a = 2 * math.pi * k / segs
            verts.append(Vector(p) + (s * math.cos(a) + nn * math.sin(a)) * r)
    for i in range(n - 1):
        for k in range(segs):
            a, b = i * segs + k, i * segs + (k + 1) % segs
            caras.append((a, b, b + segs, a + segs))
    if tapa:
        verts.append(Vector(puntos[-1]))
        c = len(verts) - 1
        for k in range(segs):
            caras.append(((n - 1) * segs + k, (n - 1) * segs + (k + 1) % segs, c))
    uvs = [(k / segs, i / max(1, n - 1)) for i in range(n) for k in range(segs)] + ([(0.5, 1)] if tapa else [])
    M.add(verts, caras, tinte, mi, uvs)


# ------------------------------------------------------------------ palma
def palma(nombre, col, alto=10.0, frondas=13, seed=1, inclin=0.04, tipo='real'):
    """Palma de tronco gris anillado. tipo 'real' (Roystonea: capitel verde liso y frondas arqueadas)
    o 'areca' (más baja, frondas más rectas y amarillentas)."""
    rnd = random.Random(seed)
    M = Malla()
    m_tr = M.mat(mat_tronco('palma_tronco', (0.20, 0.19, 0.17), (0.36, 0.34, 0.30), anillos=0.09))
    m_cap = M.mat(mat_tronco('palma_capitel', (0.20, 0.32, 0.09), (0.30, 0.42, 0.14), anillos=0.0, rough=0.5))
    if tipo == 'real':
        m_hoja = M.mat(mat_hoja('palma_hoja', (0.08, 0.17, 0.03), (0.22, 0.33, 0.06), transl=0.4))
    else:
        m_hoja = M.mat(mat_hoja('areca_hoja', (0.20, 0.30, 0.05), (0.42, 0.48, 0.10), transl=0.45))
    cap = 1.4 if tipo == 'real' else 0.4
    ht = alto - cap
    ax, ay = rnd.uniform(-1, 1) * inclin, rnd.uniform(-1, 1) * inclin
    pts, rad = [], []
    nseg = 24
    for i in range(nseg + 1):
        z = ht * i / nseg
        u = z / ht
        pts.append((ax * z * z / ht, ay * z * z / ht, z))
        if tipo == 'real':
            r = 0.25 - 0.06 * u + 0.05 * math.exp(-((u - 0.55) / 0.2) ** 2)    # abultado típico de la palma real
        else:
            r = 0.10 - 0.02 * u
        rad.append(r)
    tubo(M, pts, rad, 16, m_tr, tapa=False)
    top = Vector(pts[-1])
    cpts = [top + Vector((0, 0, cap * i / 6)) for i in range(7)]
    crad = [rad[-1] * (1.02 if tipo == 'real' else 1.0) * (1 - 0.15 * (i / 6) ** 2) for i in range(7)]
    tubo(M, [tuple(p) for p in cpts], crad, 14, m_cap)
    cima = cpts[-1]
    for f in range(frondas):
        az = 2 * math.pi * f / frondas + rnd.uniform(-0.25, 0.25)
        edad = f / frondas                                   # 0: joven (arriba), 1: vieja (colgando)
        elev = math.radians(rnd.uniform(55, 75) - 95 * edad) if tipo == 'real' else math.radians(rnd.uniform(60, 75) - 55 * edad)
        largo = rnd.uniform(3.0, 3.8) if tipo == 'real' else rnd.uniform(1.6, 2.2)
        _fronda(M, cima - Vector((0, 0, 0.15 * edad)), az, elev, largo, m_hoja, rnd, tipo)
    o = M.objeto(nombre, col)
    return o


def _fronda(M, base, az, elev, largo, mi, rnd, tipo):
    n = 26
    d = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), math.sin(elev)))
    p = Vector(base)
    ras = [p.copy()]
    tans = [d.copy()]
    caida = (0.9 if tipo == 'real' else 0.5) / n
    for i in range(n):
        p = p + d * (largo / n)
        d = (d + Vector((0, 0, -caida * (1 + i / n)))).normalized()
        ras.append(p.copy()); tans.append(d.copy())
    tubo(M, [tuple(q) for q in ras], [0.03 * (1 - i / (n + 1)) + 0.006 for i in range(n + 1)], 5, mi, tinte=0.25, tapa=False)
    lmax = 0.85 if tipo == 'real' else 0.55
    for i in range(2, n):
        u = i / n
        t = tans[i]
        lado = t.cross(Vector((0, 0, 1)))
        if lado.length < 1e-4:
            lado = Vector((1, 0, 0))
        lado.normalize()
        up = lado.cross(t).normalized()
        L = lmax * math.sin(math.pi * (0.08 + 0.88 * u)) * rnd.uniform(0.85, 1.05)
        for sgn in (-1, 1):
            for k in range(2 if tipo == 'real' else 1):          # dos filas de pinnas en V (palma real)
                ang_v = math.radians(35 if k == 0 else -10)
                dirp = (lado * sgn * math.cos(ang_v) + up * math.sin(ang_v) + t * 0.35).normalized()
                _pinna(M, ras[i] + t * (k * 0.04), dirp, t, L, 0.035 if tipo == 'real' else 0.03, mi, rnd)


def _pinna(M, base, dirp, t, L, w, mi, rnd):
    """Pinna: tira de 4 tramos que se dobla hacia abajo, más angosta en la punta."""
    verts, caras = [], []
    seg = 4
    caida = rnd.uniform(0.25, 0.55)
    lat = dirp.cross(Vector((0, 0, 1)))
    if lat.length < 1e-4:
        lat = t.copy()
    lat = (t * 0.7 + lat.normalized() * 0.3).normalized()
    p = Vector(base)
    d = dirp.copy()
    for i in range(seg + 1):
        u = i / seg
        ww = w * (1 - u ** 1.5) + 0.002
        verts.append(p - lat * ww * 0.5)
        verts.append(p + lat * ww * 0.5 + Vector((0, 0, ww * 0.25)))
        p = p + d * (L / seg)
        d = (d + Vector((0, 0, -caida / seg))).normalized()
    for i in range(seg):
        a = 2 * i
        caras.append((a, a + 2, a + 3, a + 1))
    M.add(verts, caras, rnd.random(), mi)


# ------------------------------------------------------------------ arbusto con hojas y flores
def _hoja(L, W, curva=0.15):
    """Contorno de hoja ovada en el plano xy (x a lo largo), con un poco de curvatura en z."""
    pts = [(0, 0, 0)]
    for k in range(1, 5):
        u = k / 5
        w = W * 0.5 * math.sin(math.pi * u) ** 0.8
        z = curva * L * (u - 0.5) ** 2
        pts.append((L * u, w, z)); pts.append((L * u, -w, z))
    pts.append((L, 0, curva * L * 0.25))
    # índices: 0 base, impares lado izquierdo, pares lado derecho, 9 punta
    tri = []
    izq = [1, 3, 5, 7]; der = [2, 4, 6, 8]
    tri.append((0, 2, 1))
    for i in range(3):
        tri.append((izq[i], der[i], der[i + 1], izq[i + 1]))
    tri.append((izq[3], der[3], 9))
    return [Vector(p) for p in pts], tri


def arbusto(nombre, col, radio=0.9, alto=1.3, hojas=1800, flores=0, color_flor=(0.9, 0.7, 0.05),
            hoja=(0.10, 0.06), verde=((0.05, 0.13, 0.02), (0.18, 0.30, 0.05)), seed=1, forma='flor5'):
    """Arbusto denso: hojas en la superficie de un elipsoide irregular, ramitas y racimos de flores."""
    rnd = random.Random(seed)
    M = Malla()
    m_h = M.mat(mat_hoja(f'hoja_arbusto_{seed % 3}', verde[0], verde[1], transl=0.3, rough=0.38))
    m_t = M.mat(mat_tronco('rama', (0.16, 0.12, 0.08), (0.28, 0.22, 0.15)))
    m_f = M.mat(mat_hoja('flor_%02x%02x%02x' % tuple(int(c * 255) for c in color_flor), tuple(c * 0.75 for c in color_flor), color_flor, transl=0.5, rough=0.35)) if flores else None
    lv, lc = _hoja(*hoja)
    # lóbulos del arbusto
    lob = [(Vector((rnd.uniform(-0.35, 0.35) * radio, rnd.uniform(-0.35, 0.35) * radio, alto * rnd.uniform(0.45, 0.65))),
            radio * rnd.uniform(0.55, 0.8)) for _ in range(5)]
    for c, r in lob:                          # ramitas del centro a cada lóbulo
        tubo(M, [(0, 0, 0), tuple(c * 0.5), tuple(c)], [0.025, 0.018, 0.01], 5, m_t, tapa=False)
    for _ in range(hojas):
        c, r = lob[rnd.randrange(len(lob))]
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1) * 0.8 + 0.2)).normalized()
        p = c + d * r * rnd.uniform(0.7, 1.0)
        if p.z < 0.05:
            continue
        out = (p - c).normalized()
        t = (out + Vector((rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), rnd.uniform(0.0, .7)))).normalized()
        tt, ss, nn = _base(t)
        rot = Matrix((tt, ss, nn)).transposed()
        rot = Matrix.Rotation(rnd.uniform(-1.2, 1.2), 3, tt) @ rot
        esc = rnd.uniform(0.75, 1.2)
        M.add([p + rot @ (v * esc) for v in lv], lc, min(1.0, max(0.0, rnd.gauss(0.5, 0.22) + 0.2 * (p.z / alto))), m_h)
    for _ in range(flores):
        c, r = lob[rnd.randrange(len(lob))]
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), abs(rnd.gauss(0, 1)) + 0.4)).normalized()
        p = c + d * r * rnd.uniform(0.9, 1.05)
        if forma == 'racimo':                 # ixora: racimo redondo de florecitas
            for _k in range(16):
                q = p + Vector((rnd.gauss(0, 0.045), rnd.gauss(0, 0.045), rnd.gauss(0, 0.03)))
                _flor(M, q, d, 0.014, 4, m_f, rnd)
        else:                                 # alamanda: flor de trompeta amarilla de 5 pétalos
            _flor(M, p, d, 0.045, 5, m_f, rnd)
    return M.objeto(nombre, col)


def _flor(M, p, d, r, petalos, mi, rnd):
    tt, ss, nn = _base(d)
    verts = [p]
    for k in range(petalos * 2):
        a = 2 * math.pi * k / (petalos * 2)
        rr = r if k % 2 == 0 else r * 0.45
        verts.append(p + (ss * math.cos(a) + nn * math.sin(a)) * rr + tt * (0.25 * rr))
    caras = [(0, 1 + k, 1 + (k + 1) % (petalos * 2)) for k in range(petalos * 2)]
    M.add(verts, caras, rnd.uniform(0.6, 1.0), mi)


# ------------------------------------------------------------------ árbol de copa grande (mango)
def arbol(nombre, col, alto=9.0, copa=4.0, tarjetas=1500, seed=1, imagen=None,
          verde=(1.0, 1.0, 1.0)):
    rnd = random.Random(seed)
    M = Malla()
    m_t = M.mat(mat_tronco('corteza', (0.17, 0.14, 0.11), (0.33, 0.29, 0.24)))
    m_c = M.mat(mat_tarjeta('copa_tarjeta', imagen, verde))
    fuste = alto * 0.32
    tubo(M, [(0, 0, 0), (0.05, 0.02, fuste * 0.5), (0, 0, fuste)], [0.32 * copa / 4, 0.27 * copa / 4, 0.24 * copa / 4], 10, m_t, tapa=False)
    centro = Vector((0, 0, alto - copa * 0.75))
    blobs = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.3, 0.3)
        rr = copa * rnd.uniform(0.35, 0.6)
        c = centro + Vector((math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(-0.2, 0.5) * copa * 0.5))
        blobs.append((c, copa * rnd.uniform(0.45, 0.62)))
        tubo(M, [(0, 0, fuste * 0.9), tuple(Vector((0, 0, fuste)) + (c - Vector((0, 0, fuste))) * 0.5), tuple(c)],
             [0.14 * copa / 4, 0.09 * copa / 4, 0.04], 6, m_t, tapa=False)
    blobs.append((centro + Vector((0, 0, copa * 0.35)), copa * 0.6))
    s = 0.6                                   # tarjetas chicas y muchas: la copa no se ve hecha de "rosetas"
    quad = [Vector((-s, 0, -s)), Vector((s, 0, -s)), Vector((s, 0, s)), Vector((-s, 0, s))]
    uvq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for _ in range(tarjetas):
        c, r = blobs[rnd.randrange(len(blobs))]
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        p = c + d * r * rnd.uniform(0.55, 1.0)
        eje = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        rot = Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 3, eje)
        esc = rnd.uniform(0.7, 1.25) * copa / 4
        luz = 0.3 + 0.7 * max(0.0, min(1.0, (p.z - centro.z + copa * 0.6) / (copa * 1.4)))
        M.add([p + rot @ (v * esc) for v in quad], [(0, 1, 2, 3)], luz * rnd.uniform(0.75, 1.0), m_c, uvq)
    return M.objeto(nombre, col)


# ------------------------------------------------------------------ hierba
def hierba(nombre, col, area, densidad=60, alto=(0.12, 0.30), seed=1, verde=((0.05, 0.12, 0.015), (0.22, 0.30, 0.05)),
           excluir=None, z=0.0, maleza=0.15):
    """Una sola malla con miles de briznas sobre un rectángulo (x0, y0, x1, y1) en coordenadas del objeto
    padre. `excluir(x, y)` devuelve True donde no debe crecer. `maleza` = fracción de briznas altas."""
    rnd = random.Random(seed)
    M = Malla()
    m = M.mat(mat_hoja('hierba', verde[0], verde[1], transl=0.35, rough=0.5))
    x0, y0, x1, y1 = area
    n = int((x1 - x0) * (y1 - y0) * densidad)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if excluir and excluir(x, y):
            continue
        alta = rnd.random() < maleza
        h = rnd.uniform(*alto) * (2.3 if alta else 1.0)
        az = rnd.uniform(0, 2 * math.pi)
        inc = rnd.uniform(0.1, 0.6)
        w = rnd.uniform(0.004, 0.008)
        d = Vector((math.cos(az) * inc, math.sin(az) * inc, 1)).normalized()
        lat = Vector((-math.sin(az), math.cos(az), 0))
        verts = []
        p = Vector((x, y, z))
        for k in range(4):
            u = k / 3
            ww = w * (1 - u)
            verts.append(p - lat * ww); verts.append(p + lat * ww)
            p = p + d * (h / 3)
            d = (d + Vector((math.cos(az), math.sin(az), 0)) * 0.25 * inc).normalized()
        caras = [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 7, 6)]
        M.add(verts, caras, min(1, max(0, rnd.gauss(0.45, 0.25) + (0.25 if alta else 0))), m)
    return M.objeto(nombre, col)


def instancia(base, nombre, col, loc, rot=0.0, esc=1.0):
    o = bpy.data.objects.new(nombre, base.data)
    col.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, rot); o.scale = (esc, esc, esc)
    return o
