"""
Etapa 4a · modelos procedurales de muebles y equipo (Blender, bmesh).

Cada constructor arma el mueble en su marco local (origen al centro de la huella, en el piso;
ancho en x, fondo en y, respaldo hacia -y) dentro de una Malla con varios materiales; amueblar()
lo ubica según amueblado.DIST y lo cuelga del Kit del edificio. Nada se compra ni se descarga:
todo sale de cajas, cilindros, esferas y toros con biseles.
"""
import math, random
from contextlib import contextmanager
import bpy, bmesh
from mathutils import Matrix, Vector
import amueblado as A
from lib import box_uv

R = math.radians


class Malla:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.M = Matrix.Identity(4)
        self.luces = []          # (co local, potencia W, radio, color)

    def mi(self, nombre):
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    @contextmanager
    def at(self, x=0, y=0, z=0, g=0, rx=0, ry=0, esc=None):
        viejo = self.M
        T = Matrix.Translation((x, y, z)) @ Matrix.Rotation(R(g), 4, 'Z') @ Matrix.Rotation(R(ry), 4, 'Y') @ Matrix.Rotation(R(rx), 4, 'X')
        if esc:
            T = T @ Matrix.Diagonal((esc[0], esc[1], esc[2], 1))
        self.M = viejo @ T
        try:
            yield
        finally:
            self.M = viejo

    def _fin(self, vs, mat, suave=False, suave_lados=False):
        for v in vs:
            v.co = self.M @ v.co
        fs = {f for v in vs for f in v.link_faces}
        k = self.mi(mat)
        for f in fs:
            f.material_index = k
            f.smooth = suave or (suave_lados and len(f.verts) == 4)
        return fs

    def caja(self, x0, y0, z0, x1, y1, z1, mat, bev=0.0, seg=2, suave=False):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = r['verts']
        sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
        for v in vs:
            v.co = Vector((min(x0, x1) + (v.co.x + 0.5) * sx, min(y0, y1) + (v.co.y + 0.5) * sy, min(z0, z1) + (v.co.z + 0.5) * sz))
        fs = self._fin(vs, mat, suave)
        b = min(bev, 0.45 * min(sx, sy, sz)) if bev else 0
        if b > 0.0005:
            es = list({e for v in vs for e in v.link_edges})
            res = bmesh.ops.bevel(self.bm, geom=es + list(vs), offset=b, segments=seg, profile=0.5, affect='EDGES',
                                  clamp_overlap=True)
            k = self.mi(mat)
            for f in res['faces']:
                f.material_index = k
                f.smooth = True
        return fs

    def cc(self, cx, cy, cz, sx, sy, sz, mat, **kw):
        """Caja por centro (z = base)."""
        return self.caja(cx - sx / 2, cy - sy / 2, cz, cx + sx / 2, cy + sy / 2, cz + sz, mat, **kw)

    def cil(self, x, y, z0, z1, r, mat, segs=16, r2=None, eje='z'):
        h = abs(z1 - z0)
        r_ = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                                   radius2=r if r2 is None else r2, depth=h)
        vs = r_['verts']
        if eje == 'z':
            T = Matrix.Translation((x, y, (z0 + z1) / 2))
        elif eje == 'x':     # (x,y,z0..z1) se lee como: centro (y, z) = (x, y), tramo en x de z0 a z1
            T = Matrix.Translation(((z0 + z1) / 2, x, y)) @ Matrix.Rotation(R(90), 4, 'Y')
        else:                # eje y: centro (x, z) = (x, y), tramo en y de z0 a z1
            T = Matrix.Translation((x, (z0 + z1) / 2, y)) @ Matrix.Rotation(R(-90), 4, 'X')
        for v in vs:
            v.co = T @ v.co
        return self._fin(vs, mat, suave_lados=True)

    def tubo(self, p, q, r, mat, segs=10):
        p, q = Vector(p), Vector(q)
        d = q - p
        L = d.length
        if L < 1e-5:
            return
        r_ = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=L)
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        T = Matrix.Translation((p + q) / 2) @ rot
        for v in r_['verts']:
            v.co = T @ v.co
        return self._fin(r_['verts'], mat, suave_lados=True)

    def esfera(self, x, y, z, r, mat, seg=12, esc=(1, 1, 1)):
        r_ = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r)
        T = Matrix.Translation((x, y, z)) @ Matrix.Diagonal((esc[0], esc[1], esc[2], 1))
        for v in r_['verts']:
            v.co = T @ v.co
        return self._fin(r_['verts'], mat, suave=True)

    def toro(self, x, y, z, Rm, r, mat, eje='z', seg=24, seg2=8):
        """Toro (ruedas, aros). eje = eje de giro."""
        vs = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            for j in range(seg2):
                b = 2 * math.pi * j / seg2
                rr = Rm + r * math.cos(b)
                vs.append(self.bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        for i in range(seg):
            for j in range(seg2):
                a = vs[i * seg2 + j]; b = vs[((i + 1) % seg) * seg2 + j]
                c = vs[((i + 1) % seg) * seg2 + (j + 1) % seg2]; d = vs[i * seg2 + (j + 1) % seg2]
                self.bm.faces.new((a, b, c, d))
        if eje == 'z':
            T = Matrix.Translation((x, y, z))
        elif eje == 'x':
            T = Matrix.Translation((x, y, z)) @ Matrix.Rotation(R(90), 4, 'Y')
        else:
            T = Matrix.Translation((x, y, z)) @ Matrix.Rotation(R(90), 4, 'X')
        for v in vs:
            v.co = T @ v.co
        return self._fin(vs, mat, suave=True)

    def hoja(self, base, direc, largo, ancho, mat, curva=0.25, giro=0.0):
        """Hoja ancha (higuera, palma): superficie 6×3 con perfil de hoja, arqueada hacia abajo."""
        base = Vector(base); direc = Vector(direc).normalized()
        lado = direc.cross(Vector((0, 0, 1)))
        if lado.length < 1e-3:
            lado = Vector((1, 0, 0))
        lado.normalize()
        lado = Matrix.Rotation(giro, 3, direc) @ lado
        arriba = lado.cross(direc).normalized()
        n = 6
        filas = []
        for i in range(n + 1):
            t = i / n
            w = ancho * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.8 * (1 - 0.15 * t)
            c = base + direc * (largo * t) - Vector((0, 0, 1)) * (curva * largo * t * t)
            fila = [self.bm.verts.new(c + lado * (s * w / 2) + arriba * (abs(s) * -0.012)) for s in (-1, 0, 1)]
            filas.append(fila)
        vs = [v for f in filas for v in f]
        for i in range(n):
            for j in range(2):
                self.bm.faces.new((filas[i][j], filas[i][j + 1], filas[i + 1][j + 1], filas[i + 1][j]))
        return self._fin(vs, mat, suave=True)

    def luz(self, x, y, z, w, radio=0.05, color=(1.0, 0.82, 0.6)):
        self.luces.append((self.M @ Vector((x, y, z)), w, radio, color))

    def objeto(self, nombre, M, coleccion):
        me = bpy.data.meshes.new(nombre)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(M[n])
        ob = bpy.data.objects.new(nombre, me)
        coleccion.objects.link(ob)
        return ob


# ===================================================================== piezas compartidas
def patas(m, x0, y0, x1, y1, z, r, mat, cuadradas=False, cono=None):
    for (x, y) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        if cuadradas:
            m.cc(x, y, 0, 2 * r, 2 * r, z, mat, bev=0.004)
        else:
            m.cil(x, y, 0, z, r, mat, segs=10, r2=cono)


def silla_comedor(m, tela='tela_beige', madera='madera_clara', brazos=True):
    """Silla tapizada (respaldo hacia -y), 0,50 × 0,52."""
    patas(m, -0.20, -0.20, 0.20, 0.20, 0.44, 0.018, madera, cuadradas=True)
    m.caja(-0.24, -0.24, 0.42, 0.24, 0.25, 0.50, tela, bev=0.03, seg=3)
    with m.at(0, -0.22, 0.48, rx=-8):
        m.caja(-0.23, -0.04, 0, 0.23, 0.04, 0.48, tela, bev=0.03, seg=3)
    if brazos:
        for s in (-1, 1):
            m.caja(s * 0.25 - 0.03, -0.22, 0.50, s * 0.25 + 0.03, 0.16, 0.66, tela, bev=0.025, seg=2)


def silla_simple(m, tela='tela_beige', madera='madera_clara'):
    patas(m, -0.19, -0.19, 0.19, 0.19, 0.44, 0.015, madera, cuadradas=True)
    m.caja(-0.22, -0.22, 0.42, 0.22, 0.22, 0.48, tela, bev=0.025)
    m.caja(-0.21, -0.23, 0.48, 0.21, -0.20, 0.86, madera, bev=0.01)
    m.caja(-0.20, -0.20, 0.62, 0.20, -0.17, 0.82, tela, bev=0.012)


def silla_oficina(m, tela='tela_gris'):
    for i in range(5):
        a = 2 * math.pi * i / 5
        p = (0.27 * math.cos(a), 0.27 * math.sin(a))
        m.tubo((0, 0, 0.09), (p[0], p[1], 0.07), 0.018, 'plastico_negro', 6)
        m.esfera(p[0], p[1], 0.03, 0.03, 'plastico_negro', 8)
    m.cil(0, 0, 0.08, 0.40, 0.025, 'cromo', 12)
    m.caja(-0.24, -0.22, 0.40, 0.24, 0.24, 0.48, tela, bev=0.03, seg=3)
    m.caja(-0.03, -0.27, 0.42, 0.03, -0.22, 0.60, 'plastico_negro')
    with m.at(0, -0.26, 0.56, rx=-6):
        m.caja(-0.22, -0.03, 0, 0.22, 0.04, 0.50, tela, bev=0.035, seg=3)
    for s in (-1, 1):
        m.caja(s * 0.25 - 0.02, -0.12, 0.48, s * 0.25 + 0.02, 0.0, 0.62, 'plastico_negro')
        m.caja(s * 0.25 - 0.035, -0.18, 0.62, s * 0.25 + 0.035, 0.10, 0.65, 'plastico_negro', bev=0.01)


def libros(m, x0, x1, y0, y1, z, alto=(0.18, 0.27), rnd=None, inclina=True):
    rnd = rnd or random.Random(1)
    x = x0
    while x < x1 - 0.02:
        g = rnd.uniform(0.018, 0.045)
        if x + g > x1:
            break
        h = rnd.uniform(*alto)
        mat = f'color_{rnd.randrange(6)}'
        if inclina and rnd.random() < 0.06 and x + 0.15 < x1:
            with m.at(x + 0.02, (y0 + y1) / 2, z, ry=18):
                m.caja(0, y0 - (y0 + y1) / 2, 0, g, y1 - (y0 + y1) / 2, h, mat, bev=0.002)
            x += 0.12
            continue
        m.caja(x, y0 + rnd.uniform(0, 0.03), z, x + g, y1, z + h, mat, bev=0.002)
        x += g + 0.002
        if rnd.random() < 0.08:
            x += rnd.uniform(0.05, 0.15)


def lampara_mesa(m, x, y, z, alto=0.45, r=0.13):
    m.cil(x, y, z, z + 0.02, 0.07, 'metal_negro', 16)
    m.cil(x, y, z + 0.02, z + alto * 0.55, 0.055, 'porcelana', 16, r2=0.035)
    m.cil(x, y, z + alto * 0.55, z + alto * 0.6, 0.01, 'cromo', 8)
    m.cil(x, y, z + alto * 0.55, z + alto, r, 'pantalla_lampara', 20, r2=r * 0.8)
    m.esfera(x, y, z + alto * 0.68, 0.03, 'luz_calida', 8)
    m.luz(x, y, z + alto * 0.7, 12, 0.04)


def planta_hojas(m, x, y, z, alto, rnd, maceta='maceta_blanca', r_mac=0.20, n=40, tipo='ficus'):
    """Planta en maceta: higuera de hoja ancha ('ficus'), palma areca ('palma') o lengua de suegra ('sansevieria')."""
    hm = r_mac * 1.7
    m.cil(x, y, z, z + hm, r_mac, maceta, 24, r2=r_mac * 0.82)
    m.cil(x, y, z + hm - 0.03, z + hm - 0.015, r_mac * 0.95, 'tierra', 20)
    if tipo == 'sansevieria':
        for i in range(14):
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0, r_mac * 0.6)
            b = Vector((x + rr * math.cos(a), y + rr * math.sin(a), z + hm - 0.02))
            d = Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, 1.0))
            m.hoja(b, d, alto * rnd.uniform(0.6, 1.0), 0.07, 'hoja' if i % 3 else 'hoja_clara', curva=0.02, giro=rnd.uniform(0, 3))
        return
    if tipo == 'palma':
        for i in range(9):
            a = 2 * math.pi * i / 9 + rnd.uniform(-0.2, 0.2)
            b = Vector((x, y, z + hm))
            top = b + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, alto * rnd.uniform(0.55, 0.8)))
            m.tubo(b, top, 0.008, 'tronco', 5)
            for k in range(7):
                t = 0.3 + 0.1 * k
                p = b + (top - b) * t
                for s in (-1, 1):
                    d = Vector((math.cos(a + s * 1.3), math.sin(a + s * 1.3), -0.2))
                    m.hoja(p, d, 0.28 * (1.2 - t * 0.6), 0.035, 'hoja_clara', curva=0.3, giro=0.4)
        return
    # higuera de hoja de violín: tronco y hojas grandes en espiral
    tope = Vector((x + rnd.uniform(-0.04, 0.04), y + rnd.uniform(-0.04, 0.04), z + alto))
    m.tubo((x, y, z + hm - 0.02), tope, 0.018, 'tronco', 8)
    for i in range(n):
        t = 0.35 + 0.65 * i / n
        p = Vector((x, y, z + hm)) + (tope - Vector((x, y, z + hm))) * t
        a = i * 2.4
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.2, 0.9)))
        m.hoja(p, d, rnd.uniform(0.18, 0.28) * (1.25 - 0.4 * t), rnd.uniform(0.12, 0.17), 'hoja' if i % 4 else 'hoja_clara',
               curva=0.3, giro=rnd.uniform(-0.4, 0.4))


def cojin(m, x, y, z, w, d, h, mat, g=0, rx=0):
    with m.at(x, y, z, g=g, rx=rx):
        m.caja(-w / 2, -d / 2, 0, w / 2, d / 2, h, mat, bev=min(w, d, h) * 0.45, seg=3)


# ===================================================================== constructores
def b_cama_hosp(m, w, d, h, o, rnd):
    hw = w / 2
    # chasis con ruedas y elevador
    for (x, y) in ((-hw + 0.06, -d / 2 + 0.12), (hw - 0.06, -d / 2 + 0.12), (-hw + 0.06, d / 2 - 0.12), (hw - 0.06, d / 2 - 0.12)):
        m.cil(y, 0.055, x - 0.014, x + 0.014, 0.02, 'plastico_gris', 10, eje='x')
        m.toro(x, y, 0.055, 0.045, 0.012, 'goma', eje='x', seg=16, seg2=6)
        m.caja(x - 0.02, y - 0.03, 0.06, x + 0.02, y + 0.03, 0.16, 'metal_gris', bev=0.005)
    m.caja(-hw + 0.04, -d / 2 + 0.08, 0.15, hw - 0.04, d / 2 - 0.08, 0.20, 'metal_blanco', bev=0.01)
    m.caja(-0.22, -0.55, 0.20, 0.22, 0.55, 0.36, 'plastico_gris', bev=0.02)
    m.caja(-hw + 0.03, -d / 2 + 0.07, 0.36, hw - 0.03, d / 2 - 0.07, 0.42, 'metal_blanco', bev=0.012)
    # colchón con respaldo levantado
    Y0, Y1, quiebre = -d / 2 + 0.08, d / 2 - 0.08, -d / 2 + 0.78
    m.caja(-hw + 0.04, quiebre, 0.42, hw - 0.04, Y1, 0.57, 'sabana_celeste', bev=0.045, seg=3)
    with m.at(0, quiebre, 0.42, rx=-14):
        m.caja(-hw + 0.04, Y0 - quiebre, 0, hw - 0.04, 0.02, 0.15, 'sabana_celeste', bev=0.045, seg=3)
        cojin(m, 0, (Y0 - quiebre) + 0.24, 0.13, 0.58, 0.36, 0.13, 'sabana_blanca', rx=8)
    # sábana blanca doblada y manta a los pies
    m.caja(-hw + 0.02, quiebre - 0.05, 0.47, hw - 0.02, Y1 + 0.01, 0.595, 'sabana_blanca', bev=0.03, seg=3)
    m.caja(-hw + 0.01, quiebre - 0.08, 0.55, hw - 0.01, quiebre + 0.10, 0.615, 'sabana_blanca', bev=0.03, seg=3)
    m.caja(-hw + 0.05, Y1 - 0.40, 0.595, hw - 0.05, Y1 - 0.08, 0.64, 'manta_gris' if o.get('manta') == 'gris' else 'manta_arena',
           bev=0.02, seg=2)
    # cabecera y piecera de laminado con marco blanco
    for (ya, yb, z1) in ((-d / 2, -d / 2 + 0.035, 0.98), (d / 2 - 0.035, d / 2, 0.86)):
        m.caja(-hw + 0.03, ya, 0.40, hw - 0.03, yb, z1, 'laminado_madera', bev=0.012)
        for s in (-1, 1):
            m.cil(s * (hw - 0.02), (ya + yb) / 2, 0.36, z1 + 0.02, 0.018, 'metal_blanco', 10)
        m.tubo((-hw + 0.02, (ya + yb) / 2, z1 + 0.02), (hw - 0.02, (ya + yb) / 2, z1 + 0.02), 0.016, 'metal_blanco')
    # barandales partidos (lado cabeza levantado, lado pies abatido)
    for s in (-1, 1):
        x = s * (hw - 0.005)
        for (a, b, zz) in ((Y0 + 0.12, quiebre - 0.05, (0.66, 0.76)), (quiebre + 0.2, Y1 - 0.25, (0.50, 0.60))):
            for z in zz:
                m.tubo((x, a, z), (x, b, z), 0.011, 'aluminio', 8)
            for yy in (a + 0.04, (a + b) / 2, b - 0.04):
                m.tubo((x, yy, 0.42), (x, yy, zz[1]), 0.009, 'aluminio', 6)
    # control de mano colgando
    m.caja(hw - 0.01, -0.35, 0.50, hw + 0.025, -0.28, 0.62, 'plastico_blanco', bev=0.008)


def b_cama(m, w, d, h, o, rnd):
    hw = w / 2
    estilo = o.get('estilo', 'tapizada')
    Y0, Y1 = -d / 2 + 0.06, d / 2
    patas(m, -hw + 0.06, Y0 + 0.08, hw - 0.06, Y1 - 0.06, 0.12, 0.022, 'madera_oscura', cuadradas=True)
    m.caja(-hw + 0.02, Y0, 0.12, hw - 0.02, Y1 - 0.02, 0.36, 'tela_lino' if estilo == 'tapizada' else 'madera_media', bev=0.015)
    m.caja(-hw + 0.035, Y0 + 0.02, 0.36, hw - 0.035, Y1 - 0.04, 0.56, 'sabana_blanca', bev=0.05, seg=3)
    # edredón que cubre y cae a los lados; doblez arriba
    m.caja(-hw - 0.005, Y0 + 0.50, 0.33, hw + 0.005, Y1, 0.60, o.get('edredon', 'sabana_blanca'), bev=0.06, seg=3)
    m.caja(-hw - 0.01, Y0 + 0.44, 0.53, hw + 0.01, Y0 + 0.66, 0.625, o.get('edredon', 'sabana_blanca'), bev=0.04, seg=3)
    # manta tejida a los pies
    m.caja(-hw - 0.012, Y1 - 0.62, 0.40, hw + 0.012, Y1 - 0.14, 0.635, o.get('manta', 'manta_arena'), bev=0.03, seg=2)
    # almohadas
    n_alm = 2 if w > 1.2 else 1
    for i in range(n_alm):
        cx = 0 if n_alm == 1 else (-0.33 + 0.66 * i)
        cojin(m, cx, Y0 + 0.24, 0.53, 0.62 if n_alm == 1 else 0.6, 0.38, 0.16, 'sabana_blanca', rx=12)
        if n_alm == 2 or w >= 1.0:
            cojin(m, cx + 0.05, Y0 + 0.42, 0.55, 0.42, 0.14, 0.26, o.get('cojin', 'tela_lino'), rx=-15)
    # cabecera
    if estilo == 'tapizada':
        m.caja(-hw - 0.02, -d / 2, 0.20, hw + 0.02, -d / 2 + 0.07, 1.10, o.get('cabecera', 'tela_lino'), bev=0.035, seg=3)
        nb = max(3, int(w / 0.22))
        for i in range(nb):
            x = -hw + (i + 0.5) * w / nb
            m.caja(x - 0.004, -d / 2 + 0.065, 0.62, x + 0.004, -d / 2 + 0.072, 1.06, 'tela_gris')
    else:
        m.caja(-hw - 0.01, -d / 2, 0.10, hw + 0.01, -d / 2 + 0.05, 1.0, 'madera_media', bev=0.012)
        m.caja(-hw + 0.04, -d / 2 + 0.05, 0.6, hw - 0.04, -d / 2 + 0.06, 0.92, 'madera_clara', bev=0.005)
        m.caja(-hw - 0.01, Y1 - 0.05, 0.10, hw + 0.01, Y1, 0.62, 'madera_media', bev=0.012)


def b_cama_suite(m, w, d, h, o, rnd):
    b_cama(m, w, d, h, dict(o, cabecera='tela_lino', manta='manta_arena'), rnd)


def b_mesita(m, w, d, h, o, rnd):
    mat = o.get('mat', 'madera_clara')
    patas(m, -w / 2 + 0.04, -d / 2 + 0.04, w / 2 - 0.04, d / 2 - 0.04, 0.10, 0.015, 'madera_oscura', cuadradas=True)
    m.caja(-w / 2, -d / 2, 0.10, w / 2, d / 2, h, mat, bev=0.01)
    m.caja(-w / 2 + 0.03, d / 2, 0.36, w / 2 - 0.03, d / 2 + 0.008, h - 0.04, mat, bev=0.004)
    m.caja(-0.06, d / 2 + 0.008, h - 0.12, 0.06, d / 2 + 0.02, h - 0.105, 'cromo', bev=0.003)
    if o.get('lampara', True):
        lampara_mesa(m, -0.06, -0.03, h, 0.46, 0.13)
        m.caja(0.06, 0.02, h, 0.19, 0.17, h + 0.035, 'color_1', bev=0.003)


def b_mesita_hosp(m, w, d, h, o, rnd):
    for (x, y) in ((-w / 2 + 0.04, -d / 2 + 0.05), (w / 2 - 0.04, -d / 2 + 0.05), (-w / 2 + 0.04, d / 2 - 0.05), (w / 2 - 0.04, d / 2 - 0.05)):
        m.esfera(x, y, 0.025, 0.025, 'plastico_gris', 8)
    m.caja(-w / 2, -d / 2, 0.05, w / 2, d / 2, h - 0.03, 'laminado_madera', bev=0.01)
    m.caja(-w / 2 - 0.01, -d / 2 - 0.01, h - 0.03, w / 2 + 0.01, d / 2 + 0.01, h, 'laminado_blanco', bev=0.008)
    m.caja(-w / 2 + 0.03, d / 2 - 0.02, 0.42, w / 2 - 0.03, d / 2 + 0.002, h - 0.2, 'plastico_negro')       # nicho
    m.caja(-w / 2 + 0.03, d / 2, h - 0.17, w / 2 - 0.03, d / 2 + 0.01, h - 0.06, 'laminado_blanco', bev=0.004)
    m.caja(-0.05, d / 2 + 0.01, h - 0.12, 0.05, d / 2 + 0.02, h - 0.11, 'aluminio')
    # vaso con agua y pañuelos
    m.cil(0.08, -0.05, h, h + 0.11, 0.035, 'vidrio_int', 12, r2=0.04)
    m.caja(-0.13, -0.12, h, -0.01, 0.0, h + 0.07, 'papel', bev=0.006)


def b_mesa_puente(m, w, d, h, o, rnd):
    # base en C: columna al costado de la cama (-x), tablero sobre la cama
    m.caja(-0.52, -0.25, 0.02, -0.46, 0.25, 0.06, 'metal_gris', bev=0.005)
    for y in (-0.22, 0.22):
        m.esfera(-0.49, y, 0.02, 0.02, 'plastico_gris', 6)
    m.caja(-0.51, -0.03, 0.06, -0.47, 0.03, 0.86, 'metal_blanco', bev=0.005)
    m.caja(-0.53, -0.20, 0.86, 0.32, 0.20, 0.89, 'laminado_madera', bev=0.008)
    m.cil(0.10, 0.05, 0.89, 0.99, 0.04, 'plastico_blanco', 12, r2=0.045)


def b_estacion(m, w, d, h, o, rnd):
    """Estación de enfermería: la auxiliar se sienta de espaldas al muro y mira las camas (+y)."""
    y0, y1 = -d / 2 + 0.42, d / 2
    m.caja(-w / 2, y0, 0.73, w / 2, y1, 0.76, 'laminado_blanco', bev=0.008)
    for s in (-1, 1):
        m.caja(s * w / 2 - 0.025, y0, 0, s * w / 2 + 0.025, y1, 0.73, 'laminado_madera', bev=0.006)
    m.caja(-w / 2, y1 - 0.06, 0, w / 2, y1, 1.05, 'laminado_blanco', bev=0.01)                       # frente
    m.caja(-w / 2 - 0.02, y1 - 0.20, 1.05, w / 2 + 0.02, y1 + 0.03, 1.08, 'laminado_madera', bev=0.008)  # repisa alta
    m.caja(w / 2 - 0.42, y0 + 0.02, 0.02, w / 2 - 0.04, y0 + 0.50, 0.70, 'laminado_madera', bev=0.006)  # cajonera
    for k in range(3):
        z = 0.08 + k * 0.21
        m.caja(w / 2 - 0.40, y0 + 0.015, z, w / 2 - 0.06, y0 + 0.02, z + 0.18, 'laminado_blanco', bev=0.003)
        m.caja(w / 2 - 0.27, y0 + 0.005, z + 0.14, w / 2 - 0.19, y0 + 0.015, z + 0.15, 'aluminio')
    # monitor, teclado, papeles, teléfono
    m.caja(-0.30, y0 + 0.28, 0.76, -0.10, y0 + 0.40, 0.775, 'plastico_negro', bev=0.004)
    m.caja(-0.215, y0 + 0.34, 0.775, -0.185, y0 + 0.36, 0.95, 'plastico_negro')
    m.caja(-0.47, y0 + 0.33, 0.90, 0.07, y0 + 0.36, 1.22, 'plastico_negro', bev=0.006)
    m.caja(-0.455, y0 + 0.328, 0.915, 0.055, y0 + 0.331, 1.205, 'pantalla')
    m.caja(-0.40, y0 + 0.08, 0.76, 0.0, y0 + 0.24, 0.775, 'plastico_negro', bev=0.004)
    m.caja(0.08, y0 + 0.10, 0.76, 0.30, y0 + 0.40, 0.79, 'papel', bev=0.002)
    m.caja(0.30, y0 + 0.30, 1.08, 0.42, y0 + 0.36, 1.18, 'plastico_negro', bev=0.004)
    # silla de la auxiliar
    with m.at(-0.12, -d / 2 + 0.25, 0, g=0):
        silla_oficina(m, 'tela_azul')


def b_ropero(m, w, d, h, o, rnd):
    mat = o.get('mat', 'madera_clara')
    m.caja(-w / 2 + 0.02, -d / 2 + 0.02, 0, w / 2 - 0.02, d / 2 - 0.04, 0.08, 'madera_oscura')
    m.caja(-w / 2, -d / 2, 0.08, w / 2, d / 2 - 0.02, h, mat, bev=0.006)
    n = 2 if w < 1.2 else 3
    for i in range(n):
        x0 = -w / 2 + 0.005 + i * (w - 0.01) / n
        x1 = x0 + (w - 0.01) / n - 0.006
        m.caja(x0, d / 2 - 0.02, 0.09, x1, d / 2, h - 0.01, mat, bev=0.004)
        hx = x1 - 0.04 if i % 2 == 0 else x0 + 0.04
        m.caja(hx - 0.008, d / 2, 1.0, hx + 0.008, d / 2 + 0.03, 1.22, 'aluminio', bev=0.004)


def b_butaca(m, w, d, h, o, rnd, tela=None, patas_mat='madera_oscura'):
    tela = tela or o.get('tela', 'tela_beige')
    hw, hd = w / 2, d / 2
    patas(m, -hw + 0.07, -hd + 0.08, hw - 0.07, hd - 0.08, 0.12, 0.02, patas_mat, cono=0.014)
    m.caja(-hw, -hd, 0.12, hw, hd, 0.36, tela, bev=0.04, seg=3)
    cojin(m, 0, 0.05, 0.36, w - 0.24, d - 0.22, 0.12, tela)
    with m.at(0, -hd + 0.05, 0.34, rx=-12):
        m.caja(-hw + 0.04, -0.06, 0, hw - 0.04, 0.12, h - 0.34, tela, bev=0.06, seg=3)
    for s in (-1, 1):
        m.caja(s * hw - (0.13 if s > 0 else 0), -hd + 0.02, 0.30, s * hw + (0.13 if s < 0 else 0), hd, 0.62, tela, bev=0.05, seg=3)
    if o.get('cojin'):
        cojin(m, 0.12, -hd + 0.26, 0.46, 0.40, 0.14, 0.32, o['cojin'], rx=-20)


def b_butaca_cuero(m, w, d, h, o, rnd):
    b_butaca(m, w, d, h, o, rnd, tela=o.get('tela', 'cuero_camel'), patas_mat='madera_media')


def b_reclinable(m, w, d, h, o, rnd):
    t = 'tela_gris'
    hw, hd = w / 2, d / 2
    m.caja(-hw + 0.05, -hd + 0.05, 0, hw - 0.05, hd - 0.05, 0.10, 'plastico_negro')
    m.caja(-hw + 0.13, -hd + 0.1, 0.10, hw - 0.13, hd, 0.44, t, bev=0.05, seg=3)
    with m.at(0, -hd + 0.08, 0.38, rx=-15):
        m.caja(-hw + 0.13, -0.08, 0, hw - 0.13, 0.16, 0.66, t, bev=0.07, seg=3)
        cojin(m, 0, 0.12, 0.42, 0.46, 0.12, 0.20, t)
    for s in (-1, 1):
        m.caja(s * hw - (0.15 if s > 0 else 0), -hd, 0.05, s * hw + (0.15 if s < 0 else 0), hd - 0.03, 0.66, t, bev=0.06, seg=3)


def b_silla_ruedas(m, w, d, h, o, rnd):
    hw = 0.28
    for s in (-1, 1):
        x = s * hw
        m.toro(x, -0.12, 0.30, 0.29, 0.018, 'goma', eje='x', seg=32, seg2=8)
        m.toro(x + s * 0.03, -0.12, 0.30, 0.26, 0.007, 'cromo', eje='x', seg=28, seg2=6)
        m.cil(-0.12, 0.30, x - 0.03, x + 0.03, 0.03, 'cromo', 10, eje='x')
        for k in range(8):
            a = math.pi * k / 4
            m.tubo((x, -0.12, 0.30), (x, -0.12 + 0.28 * math.cos(a), 0.30 + 0.28 * math.sin(a)), 0.003, 'cromo', 4)
        # ruedita delantera
        m.toro(x * 0.85, 0.36, 0.08, 0.07, 0.015, 'goma', eje='x', seg=16, seg2=6)
        m.tubo((x * 0.85, 0.36, 0.08), (x * 0.85, 0.33, 0.30), 0.01, 'cromo', 6)
        # marco
        m.tubo((x * 0.88, -0.30, 0.48), (x * 0.88, 0.30, 0.48), 0.012, 'cromo', 8)
        m.tubo((x * 0.88, -0.30, 0.25), (x * 0.88, -0.30, 0.95), 0.012, 'cromo', 8)
        m.tubo((x * 0.88, -0.30, 0.95), (x * 0.88, -0.42, 0.95), 0.013, 'plastico_negro', 8)
        m.tubo((x * 0.88, 0.30, 0.48), (x * 0.88, 0.40, 0.12), 0.011, 'cromo', 8)
        m.caja(x * 0.88 - 0.06, 0.36, 0.10, x * 0.88 + 0.06, 0.48, 0.115, 'plastico_negro')
        m.caja(x * 0.88 - 0.02, -0.28, 0.62, x * 0.88 + 0.02, 0.18, 0.66, 'plastico_negro', bev=0.01)
        m.tubo((x * 0.88, 0.16, 0.48), (x * 0.88, 0.16, 0.64), 0.01, 'cromo', 6)
    m.caja(-hw * 0.88, -0.28, 0.46, hw * 0.88, 0.22, 0.50, 'vinil_gris', bev=0.01)
    m.caja(-hw * 0.88, -0.31, 0.52, hw * 0.88, -0.29, 0.92, 'vinil_gris', bev=0.006)


def b_sofa(m, w, d, h, o, rnd):
    t = o.get('tela', 'tela_gris')
    hw, hd = w / 2, d / 2
    patas(m, -hw + 0.08, -hd + 0.08, hw - 0.08, hd - 0.08, 0.10, 0.02, 'madera_oscura', cono=0.014)
    m.caja(-hw, -hd, 0.10, hw, hd, 0.38, t, bev=0.04, seg=3)
    n = 3 if w > 1.7 else 2
    ws = (w - 0.32) / n
    for i in range(n):
        x = -hw + 0.16 + ws * (i + 0.5)
        cojin(m, x, 0.06, 0.37, ws - 0.01, d - 0.24, 0.12, t)
        with m.at(x, -hd + 0.07, 0.36, rx=-12):
            m.caja(-ws / 2 + 0.005, -0.05, 0, ws / 2 - 0.005, 0.14, 0.44, t, bev=0.06, seg=3)
    m.caja(-hw + 0.02, -hd, 0.36, hw - 0.02, -hd + 0.14, 0.78, t, bev=0.04, seg=3)
    for s in (-1, 1):
        m.caja(s * hw - (0.15 if s > 0 else 0), -hd, 0.30, s * hw + (0.15 if s < 0 else 0), hd, 0.62, t, bev=0.05, seg=3)
    cojin(m, -hw + 0.32, -hd + 0.28, 0.48, 0.42, 0.13, 0.36, o.get('cojin', 'tela_salvia'), rx=-20, g=10)
    cojin(m, hw - 0.32, -hd + 0.28, 0.48, 0.42, 0.13, 0.36, o.get('cojin', 'tela_crema'), rx=-20, g=-10)


def b_mesa_centro(m, w, d, h, o, rnd):
    patas(m, -w / 2 + 0.05, -d / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.05, h - 0.04, 0.02, 'madera_media', cuadradas=True)
    m.caja(-w / 2, -d / 2, h - 0.04, w / 2, d / 2, h, 'madera_media', bev=0.008)
    m.caja(-w / 2 + 0.06, -d / 2 + 0.06, 0.10, w / 2 - 0.06, d / 2 - 0.06, 0.12, 'madera_media')
    m.caja(-0.15, -0.10, h, 0.12, 0.10, h + 0.02, 'color_3', bev=0.003)
    m.cil(0.25 if w > 0.7 else 0.0, 0.0, h, h + 0.10, 0.06, 'porcelana', 16, r2=0.08)


def b_mesa_centro_red(m, w, d, h, o, rnd):
    r = min(w, d) / 2
    m.cil(0, 0, h - 0.04, h, r, 'madera_media', 32)
    m.cil(0, 0, h - 0.06, h - 0.04, r * 0.92, 'madera_media', 32)
    for i in range(3):
        a = 2 * math.pi * i / 3
        m.tubo((r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), 0), (r * 0.3 * math.cos(a), r * 0.3 * math.sin(a), h - 0.05), 0.018, 'madera_oscura', 8)
    if r > 0.26:
        m.cil(0.05, 0.0, h, h + 0.12, 0.05, 'porcelana', 16, r2=0.07)


def b_mueble_tv(m, w, d, h, o, rnd):
    patas(m, -w / 2 + 0.06, -d / 2 + 0.05, w / 2 - 0.06, d / 2 - 0.05, 0.12, 0.015, 'metal_negro', cuadradas=True)
    m.caja(-w / 2, -d / 2, 0.12, w / 2, d / 2, h, 'madera_clara', bev=0.008)
    for i in range(3):
        x0 = -w / 2 + 0.01 + i * (w - 0.02) / 3
        m.caja(x0 + 0.004, d / 2, 0.14, x0 + (w - 0.02) / 3 - 0.004, d / 2 + 0.006, h - 0.02, 'madera_clara', bev=0.003)
    # televisor de 55"
    m.caja(-0.18, -0.10, h, 0.18, 0.06, h + 0.015, 'plastico_negro', bev=0.005)
    m.caja(-0.03, -0.06, h, 0.03, -0.03, h + 0.12, 'plastico_negro')
    m.caja(-0.62, -0.07, h + 0.08, 0.62, -0.035, h + 0.80, 'plastico_negro', bev=0.006)
    m.caja(-0.605, -0.035, h + 0.095, 0.605, -0.033, h + 0.785, 'pantalla')
    m.caja(0.30, -0.05, h, 0.48, 0.12, h + 0.06, 'color_4', bev=0.004)
    planta_hojas(m, -0.55, 0.0, h, 0.35, rnd, 'maceta_blanca', 0.06, tipo='sansevieria')


def b_comedor(m, w, d, h, o, rnd):
    L, A_ = w - 0.6, 0.90
    m.caja(-L / 2, -A_ / 2, 0.73, L / 2, A_ / 2, 0.765, 'madera_clara', bev=0.008)
    m.caja(-L / 2 + 0.06, -A_ / 2 + 0.06, 0.66, L / 2 - 0.06, A_ / 2 - 0.06, 0.73, 'madera_clara')
    patas(m, -L / 2 + 0.07, -A_ / 2 + 0.07, L / 2 - 0.07, A_ / 2 - 0.07, 0.73, 0.03, 'madera_clara', cuadradas=True)
    n = o.get('sillas', 6)
    lado = 2 if n <= 5 else 3
    for s in (-1, 1):
        for i in range(lado):
            x = -L / 2 + L * (i + 0.5) / lado
            with m.at(x, s * (A_ / 2 + 0.10), 0, g=0 if s < 0 else 180):
                silla_comedor(m)
    if n % 2 == 1:
        with m.at(-L / 2 - 0.12, 0, 0, g=270):
            silla_comedor(m)
    # centro de mesa: frutero y florero
    m.cil(0.25, 0, 0.765, 0.80, 0.14, 'cesta', 20, r2=0.10)
    for k in range(6):
        a = k * 1.1
        m.esfera(0.25 + 0.06 * math.cos(a), 0.06 * math.sin(a), 0.82, 0.04, ['fruta_roja', 'fruta_amarilla', 'fruta_naranja'][k % 3], 10)
    m.cil(-0.30, 0, 0.765, 0.95, 0.045, 'vidrio_int', 14, r2=0.03)
    for k in range(5):
        a = k * 1.3
        m.esfera(-0.30 + 0.05 * math.cos(a), 0.05 * math.sin(a), 1.02 + 0.03 * (k % 2), 0.035, 'fruta_roja' if k % 2 else 'color_4', 8)
    for s in (-1, 1):
        for i in range(lado):
            x = -L / 2 + L * (i + 0.5) / lado
            m.cil(x, s * (A_ / 2 - 0.16), 0.765, 0.775, 0.12, 'porcelana', 24)


def b_mostrador(m, w, d, h, o, rnd):
    """Recepción con frente de listones de madera clara (imagen de Antigravity)."""
    yf = d / 2
    m.caja(-w / 2, yf - 0.62, 0.72, w / 2, yf - 0.08, 0.75, 'laminado_blanco', bev=0.006)
    for s in (-1, 1):
        m.caja(s * w / 2 - 0.03, yf - 0.62, 0, s * w / 2 + 0.03, yf - 0.02, 1.08, 'madera_clara', bev=0.008)
    m.caja(-w / 2, yf - 0.10, 0.0, w / 2, yf - 0.06, 1.05, 'madera_clara')
    x = -w / 2 + 0.04
    while x < w / 2 - 0.05:
        m.caja(x, yf - 0.06, 0.03, x + 0.035, yf - 0.02, 1.05, 'madera_clara', bev=0.006)
        x += 0.055
    m.caja(-w / 2 - 0.02, yf - 0.30, 1.05, w / 2 + 0.02, yf + 0.02, 1.09, 'madera_clara', bev=0.01)
    m.caja(-w / 2, -d / 2 + 0.75, 0.0, w / 2, yf - 0.62, 0.05, 'madera_oscura')
    # monitor, teléfono, libreta, plantita
    m.caja(-0.36, yf - 0.50, 0.75, -0.16, yf - 0.38, 0.765, 'plastico_negro', bev=0.004)
    m.caja(-0.275, yf - 0.46, 0.765, -0.245, yf - 0.44, 0.92, 'plastico_negro')
    m.caja(-0.52, yf - 0.47, 0.88, 0.0, yf - 0.44, 1.18, 'plastico_negro', bev=0.005)
    m.caja(-0.51, yf - 0.471, 0.89, -0.01, yf - 0.469, 1.17, 'pantalla')
    m.caja(0.20, yf - 0.48, 0.75, 0.34, yf - 0.32, 0.79, 'plastico_negro', bev=0.006)
    m.caja(0.40, yf - 0.24, 1.09, 0.62, yf - 0.06, 1.10, 'papel')
    planta_hojas(m, w / 2 - 0.18, yf - 0.16, 1.09, 0.25, rnd, 'maceta_blanca', 0.05, tipo='sansevieria')
    with m.at(-0.15, -d / 2 + 0.32, 0, g=0):
        silla_oficina(m, 'tela_gris')


def b_escritorio(m, w, d, h, o, rnd):
    """Escritorio con silla detrás (hacia el muro) y dos sillas de visita al frente."""
    yd0, yd1 = -d / 2 + 0.60, -d / 2 + 1.30
    mat = o.get('mat', 'madera_media')
    m.caja(-w / 2, yd0, 0.72, w / 2, yd1, 0.755, mat, bev=0.008)
    for s in (-1, 1):
        m.caja(s * w / 2 - 0.025, yd0, 0, s * w / 2 + 0.025, yd1, 0.72, mat, bev=0.005)
    m.caja(-w / 2, yd1 - 0.03, 0.25, w / 2, yd1 - 0.01, 0.72, mat)
    m.caja(w / 2 - 0.45, yd0 + 0.02, 0, w / 2 - 0.03, yd1 - 0.05, 0.70, mat, bev=0.005)
    for k in range(3):
        z = 0.06 + k * 0.21
        m.caja(w / 2 - 0.44, yd0 + 0.012, z, w / 2 - 0.04, yd0 + 0.02, z + 0.19, mat, bev=0.003)
        m.caja(w / 2 - 0.28, yd0 + 0.0, z + 0.15, w / 2 - 0.20, yd0 + 0.012, z + 0.16, 'aluminio')
    m.caja(-0.20, yd0 + 0.40, 0.755, 0.18, yd0 + 0.60, 0.77, 'plastico_negro', bev=0.004)
    m.caja(-0.30, yd0 + 0.47, 0.77, 0.28, yd0 + 0.50, 1.10, 'plastico_negro', bev=0.006)
    m.caja(-0.29, yd0 + 0.469, 0.78, 0.27, yd0 + 0.471, 1.09, 'pantalla')
    m.caja(-0.22, yd0 + 0.12, 0.755, 0.20, yd0 + 0.28, 0.77, 'plastico_negro', bev=0.004)
    m.caja(0.30, yd0 + 0.10, 0.755, 0.52, yd0 + 0.40, 0.785, 'papel', bev=0.002)
    m.cil(-0.50, yd0 + 0.25, 0.755, 0.86, 0.035, 'metal_negro', 12)
    lampara_mesa(m, -0.55, yd0 + 0.52, 0.755, 0.40, 0.10)
    with m.at(0, -d / 2 + 0.30, 0, g=0):
        silla_oficina(m, 'cuero_negro' if mat != 'laminado_blanco' else 'tela_gris')
    for x in (-0.33, 0.33):
        with m.at(x, d / 2 - 0.25, 0, g=180):
            silla_simple(m, 'tela_azul', 'metal_negro')


def b_escritorio_simple(m, w, d, h, o, rnd):
    yd0, yd1 = -d / 2, -d / 2 + 0.55
    m.caja(-w / 2, yd0, 0.72, w / 2, yd1, 0.75, 'madera_media', bev=0.008)
    patas(m, -w / 2 + 0.03, yd0 + 0.03, w / 2 - 0.03, yd1 - 0.03, 0.72, 0.015, 'metal_negro', cuadradas=True)
    m.caja(-0.18, yd0 + 0.10, 0.75, 0.18, yd0 + 0.36, 0.765, 'plastico_gris', bev=0.004)
    m.caja(-0.17, yd0 + 0.10, 0.765, 0.17, yd0 + 0.12, 0.98, 'plastico_gris', bev=0.004)
    m.caja(0.25, yd0 + 0.15, 0.75, 0.45, yd0 + 0.40, 0.77, 'papel')
    lampara_mesa(m, -0.40, yd0 + 0.20, 0.75, 0.36, 0.09)
    with m.at(0, d / 2 - 0.25, 0, g=180):
        silla_oficina(m, 'tela_gris')


def b_archivador(m, w, d, h, o, rnd):
    m.caja(-w / 2, -d / 2, 0, w / 2, d / 2 - 0.01, h, 'metal_gris', bev=0.006)
    for k in range(4):
        z = 0.03 + k * (h - 0.05) / 4
        m.caja(-w / 2 + 0.015, d / 2 - 0.01, z, w / 2 - 0.015, d / 2, z + (h - 0.05) / 4 - 0.01, 'metal_gris', bev=0.003)
        m.caja(-0.07, d / 2, z + 0.20, 0.07, d / 2 + 0.02, z + 0.22, 'cromo')
        m.caja(-0.04, d / 2, z + 0.25, 0.04, d / 2 + 0.002, z + 0.28, 'papel')


def b_librero(m, w, d, h, o, rnd):
    mat = o.get('mat', 'madera_media')
    m.caja(-w / 2, -d / 2, 0, w / 2, -d / 2 + 0.015, h, mat)
    for s in (-1, 1):
        m.caja(s * w / 2 - 0.02, -d / 2, 0, s * w / 2 + 0.02, d / 2, h, mat, bev=0.004)
    n = 5
    for k in range(n + 1):
        z = 0.06 + k * (h - 0.09) / n
        m.caja(-w / 2 + 0.02, -d / 2, z, w / 2 - 0.02, d / 2, z + 0.022, mat, bev=0.003)
        if k < n:
            libros(m, -w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.03, z + 0.022, (0.18, min(0.3, (h - 0.09) / n - 0.05)), rnd)


def b_estante(m, w, d, h, o, rnd):
    """Estantería metálica negra (como la de la biblioteca) con su contenido."""
    cont = o.get('cont', 'ropa')
    for (x, y) in ((-w / 2 + 0.015, -d / 2 + 0.015), (w / 2 - 0.015, -d / 2 + 0.015), (-w / 2 + 0.015, d / 2 - 0.015), (w / 2 - 0.015, d / 2 - 0.015)):
        m.caja(x - 0.015, y - 0.015, 0, x + 0.015, y + 0.015, h, 'metal_negro')
    n = 5
    for k in range(n):
        z = 0.08 + k * (h - 0.12) / (n - 1)
        m.caja(-w / 2, -d / 2, z, w / 2, d / 2, z + 0.02, 'metal_negro')
        if k == n - 1:
            break
        hz = (h - 0.12) / (n - 1) - 0.06
        if cont == 'ropa':
            x = -w / 2 + 0.05
            while x < w / 2 - 0.25:
                mat = ['sabana_blanca', 'sabana_celeste', 'sabana_blanca', 'manta_arena', 'tela_crema'][rnd.randrange(5)]
                hh = rnd.uniform(0.12, min(0.30, hz))
                m.caja(x, -d / 2 + 0.05, z + 0.02, x + 0.24, d / 2 - 0.06, z + 0.02 + hh, mat, bev=0.02, seg=2)
                x += 0.27
        elif cont == 'libros':
            libros(m, -w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.05, d / 2 - 0.05, z + 0.02, (0.17, 0.25), rnd)
        else:
            x = -w / 2 + 0.04
            while x < w / 2 - 0.2:
                ww = rnd.uniform(0.18, 0.32)
                if x + ww > w / 2 - 0.03:
                    break
                mat = rnd.choice(['color_3', 'papel', 'plastico_blanco', 'color_2', 'tela_beige'])
                m.caja(x, -d / 2 + 0.04, z + 0.02, x + ww, d / 2 - 0.05, z + 0.02 + rnd.uniform(0.10, min(0.28, hz)), mat, bev=0.006)
                x += ww + 0.04


def b_camilla_med(m, w, d, h, o, rnd):
    hw, hd = w / 2, d / 2
    patas(m, -hw + 0.06, -hd + 0.06, hw - 0.06, hd - 0.06, 0.62, 0.018, 'metal_blanco', cuadradas=True)
    m.caja(-hw + 0.04, -hd + 0.04, 0.20, hw - 0.04, hd - 0.04, 0.23, 'metal_blanco')
    m.caja(-hw + 0.02, -hd + 0.02, 0.60, hw - 0.02, hd - 0.02, 0.64, 'metal_blanco', bev=0.008)
    m.caja(-hw + 0.55, -hd + 0.03, 0.64, hw - 0.03, hd - 0.03, 0.72, 'vinil_gris', bev=0.03, seg=3)
    with m.at(-hw + 0.55, 0, 0.64, ry=25):
        m.caja(-0.52, -hd + 0.03, 0, 0.0, hd - 0.03, 0.08, 'vinil_gris', bev=0.03, seg=3)
        m.caja(-0.50, -0.22, 0.08, 0.10, 0.22, 0.085, 'papel')
    m.caja(-hw + 0.55, -0.24, 0.72, hw - 0.1, 0.24, 0.723, 'papel')
    # escalón
    m.caja(hw - 0.42, hd - 0.02, 0, hw - 0.02, hd + 0.0, 0.0, 'metal_blanco')


def b_camilla_ter(m, w, d, h, o, rnd):
    hw, hd = w / 2, d / 2
    for s in (-1, 1):
        m.caja(s * (hw - 0.25) - 0.03, -hd + 0.06, 0.02, s * (hw - 0.25) + 0.03, hd - 0.06, 0.06, 'metal_blanco', bev=0.008)
        for t in (-1, 1):
            m.esfera(s * (hw - 0.25), t * (hd - 0.08), 0.02, 0.025, 'plastico_gris', 8)
    m.caja(-0.30, -0.08, 0.06, 0.30, 0.08, 0.10, 'metal_blanco', bev=0.01)
    m.tubo((-0.25, 0, 0.08), (0.25, 0, 0.52), 0.025, 'metal_blanco')
    m.tubo((0.25, 0, 0.08), (-0.25, 0, 0.52), 0.025, 'metal_blanco')
    m.caja(-hw + 0.08, -hd + 0.08, 0.52, hw - 0.08, hd - 0.08, 0.57, 'metal_blanco', bev=0.01)
    m.caja(-hw, -hd, 0.57, hw - 0.62, hd, 0.70, 'vinil_azul', bev=0.035, seg=3)
    m.caja(hw - 0.60, -hd, 0.57, hw, hd, 0.70, 'vinil_azul', bev=0.035, seg=3)
    m.caja(-hw + 0.08, -0.06, 0.62, -hw + 0.20, 0.06, 0.705, 'plastico_negro')


def b_paralelas(m, w, d, h, o, rnd):
    hw, hd = w / 2, d / 2
    m.caja(-hw, -hd, 0, hw, hd, 0.04, 'vinil_gris', bev=0.01)
    for s in (-1, 1):
        y = s * (hd - 0.08)
        for x in (-hw + 0.12, 0, hw - 0.12):
            m.cil(x, y, 0.04, 0.92, 0.022, 'cromo', 12)
            m.cil(x, y, 0.04, 0.06, 0.05, 'cromo', 12)
        m.cil(y, 0.95, -hw + 0.06, hw - 0.06, 0.025, 'madera_clara', 14, eje='x')


def b_bici(m, w, d, h, o, rnd):
    for y in (-0.42, 0.40):
        m.cil(y, 0.035, -0.27, 0.27, 0.03, 'metal_gris', 10, eje='x')
    m.tubo((0, -0.42, 0.05), (0, 0.40, 0.05), 0.03, 'metal_blanco')
    m.tubo((0, -0.20, 0.05), (0, -0.10, 0.80), 0.035, 'metal_blanco')
    m.tubo((0, 0.25, 0.05), (0, 0.30, 1.10), 0.035, 'metal_blanco')
    m.cil(0.15, 0.40, -0.035, 0.035, 0.24, 'plastico_gris', 28, eje='x')   # volante
    m.cil(0.15, 0.40, -0.05, 0.05, 0.08, 'plastico_negro', 16, eje='x')
    for s in (-1, 1):
        m.tubo((s * 0.05, 0.15, 0.40), (s * 0.08, 0.15 + s * 0.12, 0.40 - s * 0.10), 0.012, 'cromo')
        m.caja(s * 0.08 + s * 0.0 - 0.05, 0.15 + s * 0.12 - 0.05, 0.40 - s * 0.10 - 0.01, s * 0.08 + 0.05 * s + 0.05,
               0.15 + s * 0.12 + 0.05, 0.40 - s * 0.10 + 0.01, 'plastico_negro')
    with m.at(0, -0.10, 0.82):
        m.caja(-0.10, -0.12, 0, 0.10, 0.12, 0.06, 'cuero_negro', bev=0.025, seg=3)
    m.tubo((-0.22, 0.32, 1.12), (0.22, 0.32, 1.12), 0.016, 'plastico_negro')
    m.caja(-0.10, 0.27, 1.12, 0.10, 0.34, 1.22, 'plastico_negro', bev=0.01)


def b_estante_ter(m, w, d, h, o, rnd):
    for x in (-w / 2 + 0.02, w / 2 - 0.02):
        m.caja(x - 0.02, -d / 2, 0, x + 0.02, d / 2, h, 'metal_blanco', bev=0.004)
    for z in (0.08, 0.55, 1.0, h - 0.02):
        m.caja(-w / 2, -d / 2, z, w / 2, d / 2, z + 0.02, 'metal_blanco')
    cols = ['pelota_roja', 'fruta_amarilla', 'pelota_verde', 'pelota_azul', 'color_5', 'color_0']
    for i, c in enumerate(cols):                      # bandas elásticas colgando
        x = -w / 2 + 0.10 + i * (w - 0.2) / 5
        m.caja(x - 0.03, d / 2 - 0.02, 1.02 - 0.45, x + 0.03, d / 2 - 0.01, 1.02, c)
    for i in range(6):                                # pesas
        x = -w / 2 + 0.1 + i * 0.14
        c = cols[i % 4]
        m.cil(0.0, 0.57 + 0.035, x - 0.05, x + 0.05, 0.018, 'cromo', 8, eje='x')
        for xx in (x - 0.05, x + 0.05):
            m.cil(0.0, 0.57 + 0.035, xx - 0.02, xx + 0.02, 0.035, c, 10, eje='x')
    m.esfera(-0.22, 0.0, 0.10 + 0.17, 0.17, 'pelota_verde', 16)
    m.esfera(0.20, 0.0, 0.10 + 0.13, 0.13, 'pelota_azul', 16)
    m.esfera(0.0, 0.0, h + 0.30, 0.28, 'pelota_roja', 18)
    for i in range(3):                                # colchonetas enrolladas
        m.cil(0.0, 1.02 + 0.07 + i * 0.0, -w / 2 + 0.1 + i * 0.27, -w / 2 + 0.33 + i * 0.27, 0.07, ['pelota_azul', 'color_2', 'color_3'][i], 14, eje='x')


def b_silla_fam(m, w, d, h, o, rnd):
    silla_simple(m, 'tela_beige', 'madera_clara')


def b_mesa_taller(m, w, d, h, o, rnd):
    yt0, yt1 = -d / 2, -d / 2 + 0.80
    m.caja(-w / 2, yt0, 0.72, w / 2, yt1, 0.76, 'madera_clara', bev=0.008)
    patas(m, -w / 2 + 0.05, yt0 + 0.05, w / 2 - 0.05, yt1 - 0.05, 0.72, 0.028, 'madera_clara', cuadradas=True)
    for i, x in enumerate((-0.52, 0.0, 0.52)):
        with m.at(x, yt1 + 0.12, 0, g=180):
            silla_simple(m, ['tela_salvia', 'tela_beige', 'tela_azul'][i], 'madera_clara')
    # materiales: hojas, acuarelas, frascos de pinceles, lana, tela
    m.caja(-0.65, yt0 + 0.25, 0.76, -0.25, yt0 + 0.55, 0.765, 'papel')
    m.caja(-0.20, yt0 + 0.30, 0.76, 0.05, yt0 + 0.42, 0.775, 'plastico_blanco', bev=0.004)
    for i in range(6):
        m.cil(-0.18 + i * 0.04, yt0 + 0.36, 0.775, 0.78, 0.014, f'color_{i}', 8)
    m.cil(0.15, yt0 + 0.20, 0.76, 0.88, 0.04, 'vidrio_int', 12)
    for i in range(4):
        m.tubo((0.15, yt0 + 0.20, 0.78), (0.13 + 0.015 * i, yt0 + 0.18 + 0.01 * i, 0.98), 0.004, 'madera_oscura', 4)
    for i, c in enumerate(('pelota_roja', 'color_3', 'pelota_azul')):
        m.esfera(0.45 + i * 0.09, yt0 + 0.55, 0.80, 0.045, c, 10)
    m.caja(0.30, yt0 + 0.12, 0.76, 0.70, yt0 + 0.40, 0.768, 'color_5', bev=0.003)


def b_caballete(m, w, d, h, o, rnd):
    for (a, b) in (((-0.25, 0.15, 0), (-0.04, -0.02, 1.62)), ((0.25, 0.15, 0), (0.04, -0.02, 1.62)), ((0, -0.30, 0), (0, -0.02, 1.45))):
        m.tubo(a, b, 0.018, 'madera_clara', 6)
    m.caja(-0.32, 0.06, 0.72, 0.32, 0.12, 0.75, 'madera_clara')
    with m.at(0, 0.10, 0.75, rx=-8):
        m.caja(-0.30, -0.015, 0, 0.30, 0.0, 0.62, 'madera_clara')
        m.caja(-0.29, 0.0, 0.01, 0.29, 0.004, 0.61, 'lienzo_2')


def b_maquina_coser(m, w, d, h, o, rnd):
    y0, y1 = -d / 2, -d / 2 + 0.50
    m.caja(-w / 2, y0, 0.72, w / 2, y1, 0.75, 'madera_media', bev=0.006)
    for s in (-1, 1):
        m.caja(s * w / 2 - 0.03, y0, 0, s * w / 2 + 0.03, y1, 0.72, 'madera_media', bev=0.004)
    # máquina de coser
    m.caja(-0.22, y0 + 0.15, 0.75, 0.22, y0 + 0.35, 0.80, 'plastico_blanco', bev=0.015)
    m.caja(0.10, y0 + 0.17, 0.80, 0.21, y0 + 0.33, 1.06, 'plastico_blanco', bev=0.02)
    m.caja(-0.18, y0 + 0.18, 0.98, 0.21, y0 + 0.32, 1.08, 'plastico_blanco', bev=0.03, seg=3)
    m.caja(-0.18, y0 + 0.21, 0.86, -0.13, y0 + 0.29, 0.98, 'plastico_blanco', bev=0.01)
    m.cil(-0.155, y0 + 0.25, 0.80, 0.86, 0.006, 'cromo', 6)
    m.cil(0.0, y0 + 0.25, 1.08, 1.12, 0.018, 'color_0', 10)
    m.caja(-0.48, y0 + 0.08, 0.75, -0.26, y0 + 0.40, 0.76, 'color_1', bev=0.003)
    with m.at(0, d / 2 - 0.25, 0, g=180):
        silla_simple(m, 'tela_beige', 'madera_clara')


def b_mesa_reunion(m, w, d, h, o, rnd):
    m.cil(0, 0, 0.72, 0.755, 0.52, 'madera_media', 40)
    m.cil(0, 0, 0.05, 0.72, 0.06, 'metal_negro', 16)
    m.cil(0, 0, 0, 0.05, 0.30, 'metal_negro', 24, r2=0.28)
    for i in range(4):
        a = 2 * math.pi * i / 4 + math.pi / 4
        with m.at(0.60 * math.cos(a), 0.60 * math.sin(a), 0, g=math.degrees(a) + 90):
            silla_simple(m, 'cuero_negro', 'metal_negro')
    m.caja(-0.15, -0.12, 0.755, 0.12, 0.08, 0.77, 'papel')


def _gabinete(m, w, d, h, mat_cuerpo, mat_top, top_h=0.04, puertas=2, z_zocalo=0.10):
    m.caja(-w / 2 + 0.03, -d / 2, 0, w / 2 - 0.03, d / 2 - 0.06, z_zocalo, 'plastico_negro')
    m.caja(-w / 2, -d / 2, z_zocalo, w / 2, d / 2 - 0.02, h - top_h, mat_cuerpo, bev=0.004)
    for i in range(puertas):
        x0 = -w / 2 + 0.005 + i * (w - 0.01) / puertas
        x1 = x0 + (w - 0.01) / puertas - 0.005
        m.caja(x0, d / 2 - 0.02, z_zocalo + 0.01, x1, d / 2, h - top_h - 0.01, mat_cuerpo, bev=0.003)
        hx = x1 - 0.05 if i % 2 == 0 else x0 + 0.05
        m.caja(hx - 0.006, d / 2, h - top_h - 0.20, hx + 0.006, d / 2 + 0.025, h - top_h - 0.06, 'cromo', bev=0.003)
    m.caja(-w / 2 - 0.01, -d / 2, h - top_h, w / 2 + 0.01, d / 2 + 0.02, h, mat_top, bev=0.005)


def _fregadero(m, cx, cy, ztop, bw, bd, prof, mat='inox'):
    """Pila empotrada: borde + fondo + paredes (sin booleanos)."""
    m.caja(cx - bw / 2, cy - bd / 2, ztop - prof, cx + bw / 2, cy + bd / 2, ztop - prof + 0.01, mat)
    for s in (-1, 1):
        m.caja(cx - bw / 2, cy + s * bd / 2 - (0.01 if s > 0 else 0), ztop - prof, cx + bw / 2, cy + s * bd / 2 + (0.0 if s > 0 else 0.01), ztop + 0.001, mat)
        m.caja(cx + s * bw / 2 - (0.01 if s > 0 else 0), cy - bd / 2, ztop - prof, cx + s * bw / 2 + (0.0 if s > 0 else 0.01), cy + bd / 2, ztop + 0.001, mat)
    m.cil(cx, cy, ztop - prof + 0.01, ztop - prof + 0.013, 0.035, 'cromo', 12)


def _grifo(m, x, y, z, alto=0.30, alcance=0.20):
    m.cil(x, y, z, z + 0.03, 0.03, 'cromo', 12)
    m.tubo((x, y, z), (x, y, z + alto), 0.014, 'cromo')
    m.tubo((x, y, z + alto), (x, y + alcance, z + alto), 0.014, 'cromo')
    m.tubo((x, y + alcance, z + alto), (x, y + alcance, z + alto - 0.06), 0.012, 'cromo')
    m.tubo((x, y, z + 0.08), (x + 0.07, y - 0.02, z + 0.12), 0.007, 'cromo')


def b_inox_fregadero(m, w, d, h, o, rnd):
    _gabinete(m, w, d, h, 'inox', 'inox', 0.03)
    for i, x in enumerate((-w / 4, w / 4)):
        _fregadero(m, x, 0.05, h, w / 2 - 0.12, d - 0.25, 0.22)
    _grifo(m, 0, -d / 2 + 0.06, h, 0.38, 0.22)
    m.caja(-w / 2, -d / 2 - 0.0, h, w / 2, -d / 2 + 0.02, h + 0.20, 'inox')
    m.caja(w / 4 - 0.12, -0.05, h - 0.12, w / 4 + 0.12, 0.10, h - 0.11, 'color_2')


def b_inox_plano(m, w, d, h, o, rnd):
    _gabinete(m, w, d, h, 'inox', 'inox', 0.03, puertas=1 if w < 0.6 else 2)
    m.caja(-w / 2, -d / 2, h, w / 2, -d / 2 + 0.02, h + 0.20, 'inox')
    if w > 0.8:
        m.caja(-0.25, -0.05, h, 0.15, 0.20, h + 0.025, 'laminado_blanco', bev=0.004)
        for i in range(3):
            m.cil(0.32 + 0.0, -0.15 + i * 0.12, h, h + 0.16 + 0.04 * i, 0.06, 'inox', 16)


def b_estufa(m, w, d, h, o, rnd):
    """Cocina industrial de 6 hornillas, horno y campana de acero inoxidable."""
    m.caja(-w / 2, -d / 2, 0.08, w / 2, d / 2, h - 0.04, 'inox', bev=0.006)
    for x in (-w / 2 + 0.04, w / 2 - 0.04):
        for y in (-d / 2 + 0.04, d / 2 - 0.04):
            m.cil(x, y, 0, 0.08, 0.02, 'inox', 10)
    m.caja(-w / 2 + 0.04, d / 2, 0.14, w / 2 - 0.04, d / 2 + 0.015, 0.58, 'inox', bev=0.005)
    m.caja(-w / 2 + 0.12, d / 2 + 0.014, 0.28, w / 2 - 0.12, d / 2 + 0.016, 0.50, 'pantalla')
    m.tubo((-w / 2 + 0.1, d / 2 + 0.05, 0.62), (w / 2 - 0.1, d / 2 + 0.05, 0.62), 0.012, 'cromo')
    for i in range(6):
        m.cil(-w / 2 + 0.1 + i * (w - 0.2) / 5, 0.71, d / 2, d / 2 + 0.035, 0.022, 'plastico_negro', 12, eje='y')
    m.caja(-w / 2, -d / 2, h - 0.04, w / 2, d / 2, h, 'inox')
    for i in range(3):
        for j in range(2):
            x = -w / 2 + w * (i + 0.5) / 3; y = -d / 2 + 0.12 + j * (d - 0.30)
            m.cil(x, y, h, h + 0.02, 0.06, 'metal_negro', 16)
            m.cil(x, y, h + 0.02, h + 0.035, 0.035, 'metal_negro', 12)
    for x in (-w / 2 + 0.01, 0, w / 2 - 0.01):
        m.caja(x - 0.008, -d / 2 + 0.02, h + 0.035, x + 0.008, d / 2 - 0.08, h + 0.05, 'metal_negro')
    for y in (-d / 2 + 0.02, 0.02, d / 2 - 0.12):
        m.caja(-w / 2 + 0.01, y - 0.008, h + 0.035, w / 2 - 0.01, y + 0.008, h + 0.05, 'metal_negro')
    m.cil(0.18, 0.10, h + 0.05, h + 0.22, 0.13, 'inox', 20)
    m.cil(-0.20, -0.15, h + 0.05, h + 0.15, 0.11, 'inox', 20)
    # campana
    m.caja(-w / 2 - 0.10, -d / 2, 1.75, w / 2 + 0.10, d / 2 + 0.05, 1.85, 'inox', bev=0.005)
    m.caja(-w / 2 - 0.05, -d / 2, 1.85, w / 2 + 0.05, d / 2 - 0.10, 2.10, 'inox', bev=0.005)
    m.caja(-0.18, -d / 2, 2.10, 0.18, -d / 2 + 0.30, 2.85, 'inox', bev=0.004)
    m.caja(-w / 2 - 0.08, -d / 2 + 0.02, 1.749, w / 2 + 0.08, d / 2 + 0.03, 1.75, 'metal_gris')
    m.luz(0, 0, 1.70, 8, 0.1, (1, 0.95, 0.9))


def b_refri(m, w, d, h, o, rnd):
    m.caja(-w / 2, -d / 2, 0.02, w / 2, d / 2 - 0.05, h, 'inox', bev=0.012)
    for (z0, z1) in ((0.04, h * 0.66), (h * 0.66 + 0.01, h - 0.01)):
        m.caja(-w / 2 + 0.005, d / 2 - 0.05, z0, w / 2 - 0.005, d / 2, z1, 'inox', bev=0.008)
    m.tubo((w / 2 - 0.07, d / 2 + 0.035, h * 0.30), (w / 2 - 0.07, d / 2 + 0.035, h * 0.62), 0.011, 'cromo')
    m.tubo((w / 2 - 0.07, d / 2 + 0.035, h * 0.70), (w / 2 - 0.07, d / 2 + 0.035, h * 0.88), 0.011, 'cromo')
    for z in (h * 0.30, h * 0.62, h * 0.70, h * 0.88):
        m.tubo((w / 2 - 0.07, d / 2, z), (w / 2 - 0.07, d / 2 + 0.035, z), 0.008, 'cromo')
    m.caja(-0.10, d / 2, h * 0.45, 0.08, d / 2 + 0.002, h * 0.55, 'papel')


def b_mesa_inox(m, w, d, h, o, rnd):
    m.caja(-w / 2, -d / 2, h - 0.04, w / 2, d / 2, h, 'inox', bev=0.006)
    m.caja(-w / 2 + 0.03, -d / 2 + 0.03, 0.18, w / 2 - 0.03, d / 2 - 0.03, 0.20, 'inox')
    patas(m, -w / 2 + 0.03, -d / 2 + 0.03, w / 2 - 0.03, d / 2 - 0.03, h - 0.04, 0.02, 'inox')
    for i in range(3):
        m.cil(0, -0.35 + i * 0.35, 0.20, 0.34 - 0.04 * i, 0.12 - 0.015 * i, 'inox', 20)
    m.caja(-0.18, -0.30, h, 0.18, 0.05, h + 0.025, 'madera_clara', bev=0.004)
    for i in range(3):
        m.esfera(-0.05 + i * 0.07, 0.25, h + 0.04, 0.04, ['fruta_roja', 'pelota_verde', 'fruta_naranja'][i], 10)


def b_granito_fregadero(m, w, d, h, o, rnd, sink=True):
    # base de bloque repellado (foto de la cocina del edificio gris) con meseta de granito
    m.caja(-w / 2, -d / 2, 0, -w / 2 + 0.08, d / 2, h - 0.04, 'pintura_gris')
    m.caja(w / 2 - 0.08, -d / 2, 0, w / 2, d / 2, h - 0.04, 'pintura_gris')
    m.caja(-w / 2, -d / 2, 0, w / 2, -d / 2 + 0.05, h - 0.04, 'pintura_gris')
    m.caja(-w / 2 + 0.08, -d / 2, 0.30, w / 2 - 0.08, d / 2 - 0.05, 0.34, 'pintura_gris')
    m.caja(-w / 2 - 0.01, -d / 2, h - 0.04, w / 2 + 0.01, d / 2 + 0.03, h, 'granito', bev=0.006)
    if sink:
        _fregadero(m, -w / 4, 0.03, h, 0.40, 0.36, 0.18)
        _grifo(m, -w / 4, -d / 2 + 0.06, h, 0.30, 0.18)
        m.caja(w / 4 - 0.25, -0.15, h, w / 4 + 0.25, 0.20, h + 0.006, 'metal_negro')
        for x in (w / 4 - 0.12, w / 4 + 0.12):
            m.cil(x, 0.02, h + 0.006, h + 0.02, 0.06, 'metal_negro', 14)
    # cilindro de gas y ollas en el hueco
    m.cil(0.0, 0.0, 0.0, 0.30, 0.13, 'color_2', 16)
    m.cil(-w / 4, 0.0, 0.34, 0.46, 0.12, 'inox', 16)


def b_granito_plano(m, w, d, h, o, rnd):
    b_granito_fregadero(m, w, d, h, o, rnd, sink=False)
    if w > 0.5:
        m.caja(-0.22, -d / 2 + 0.04, h, 0.22, d / 2 - 0.18, h + 0.27, 'plastico_negro', bev=0.01)
        m.caja(-0.20, d / 2 - 0.181, h + 0.03, 0.10, d / 2 - 0.179, h + 0.24, 'pantalla')
    else:
        m.cil(0, 0, h, h + 0.20, 0.06, 'cromo', 14)


def b_refri_chico(m, w, d, h, o, rnd):
    m.caja(-w / 2, -d / 2, 0.02, w / 2, d / 2, h, 'plastico_negro', bev=0.01)
    m.caja(w / 2 - 0.05, d / 2, h - 0.35, w / 2 - 0.03, d / 2 + 0.03, h - 0.1, 'cromo')
    m.caja(-0.12, -0.10, h, 0.14, 0.15, h + 0.24, 'plastico_negro', bev=0.012)       # cafetera
    m.cil(0.0, 0.08, h, h + 0.14, 0.06, 'vidrio_int', 14)


def b_lavadora(m, w, d, h, o, rnd, secadora=False):
    m.caja(-w / 2, -d / 2, 0.02, w / 2, d / 2, h, 'plastico_blanco', bev=0.015)
    m.caja(-w / 2 + 0.02, d / 2 - 0.01, h - 0.12, w / 2 - 0.02, d / 2 + 0.003, h - 0.02, 'plastico_gris', bev=0.004)
    m.cil(w / 2 - 0.12, h - 0.07, d / 2, d / 2 + 0.03, 0.025, 'cromo', 14, eje='y')
    m.toro(0, d / 2 + 0.01, 0.44, 0.17, 0.025, 'plastico_gris', eje='y', seg=28, seg2=8)
    m.cil(0, 0.44, d / 2 - 0.02, d / 2 + 0.02, 0.15, 'pantalla' if not secadora else 'vidrio_int', 24, eje='y')
    if not secadora:
        m.caja(-0.18, -0.15, h, 0.10, 0.12, h + 0.12, 'color_1', bev=0.02, seg=2)


def b_secadora(m, w, d, h, o, rnd):
    b_lavadora(m, w, d, h, o, rnd, secadora=True)


def b_batea(m, w, d, h, o, rnd):
    patas(m, -w / 2 + 0.04, -d / 2 + 0.04, w / 2 - 0.04, d / 2 - 0.04, 0.60, 0.02, 'plastico_blanco', cuadradas=True)
    m.caja(-w / 2, -d / 2, 0.60, w / 2, d / 2, 0.62, 'plastico_blanco')
    _fregadero(m, 0, 0.03, h, w - 0.06, d - 0.10, 0.28, 'plastico_blanco')
    for s in (-1, 1):
        m.caja(s * w / 2 - (0.03 if s > 0 else 0), -d / 2, 0.62, s * w / 2 + (0.03 if s < 0 else 0), d / 2, h, 'plastico_blanco')
    m.caja(-w / 2, d / 2 - 0.03, 0.62, w / 2, d / 2, h, 'plastico_blanco')
    _grifo(m, 0, -d / 2 + 0.03, h, 0.25, 0.18)


def b_inodoro(m, w, d, h, o, rnd):
    m.caja(-0.19, -d / 2, 0.42, 0.19, -d / 2 + 0.18, 0.76, 'porcelana', bev=0.03, seg=3)
    m.caja(-0.20, -d / 2 - 0.005, 0.76, 0.20, -d / 2 + 0.19, 0.79, 'porcelana', bev=0.012)
    m.cil(0.0, -d / 2 + 0.10, 0.79, 0.80, 0.02, 'cromo', 12)
    with m.at(0, 0.03, 0):
        m.cil(0, 0, 0, 0.22, 0.11, 'porcelana', 24, r2=0.15)
        with m.at(0, 0, 0, esc=(1, 1.3, 1)):
            m.cil(0, 0, 0.22, 0.40, 0.15, 'porcelana', 28, r2=0.18)
            m.cil(0, 0, 0.40, 0.42, 0.185, 'plastico_blanco', 28)
            m.cil(0, 0, 0.42, 0.44, 0.18, 'plastico_blanco', 28, r2=0.17)
    m.caja(-0.08, -d / 2 + 0.17, 0.40, 0.08, -d / 2 + 0.20, 0.45, 'cromo')


def b_lavamanos(m, w, d, h, o, rnd):
    with m.at(0, 0.0, 0):
        m.caja(-w / 2, -d / 2, h - 0.16, w / 2, d / 2, h, 'porcelana', bev=0.04, seg=3)
    _fregadero(m, 0, 0.04, h, w - 0.14, d - 0.16, 0.10, 'porcelana')
    m.cil(0, -0.05, 0.25, h - 0.15, 0.03, 'cromo', 12)
    _grifo(m, 0, -d / 2 + 0.06, h, 0.16, 0.12)
    # espejo y repisa sobre el lavamanos
    m.caja(-w / 2 + 0.02, -d / 2, h + 0.25, w / 2 - 0.02, -d / 2 + 0.02, h + 0.95, 'metal_gris', bev=0.004)
    m.caja(-w / 2 + 0.04, -d / 2 + 0.02, h + 0.27, w / 2 - 0.04, -d / 2 + 0.022, h + 0.93, 'espejo')
    m.caja(-0.12, -d / 2, h + 0.08, 0.0, -d / 2 + 0.10, h + 0.23, 'plastico_blanco', bev=0.01)   # jabón
    m.caja(w / 2 + 0.05, -d / 2, h - 0.20, w / 2 + 0.28, -d / 2 + 0.10, h + 0.15, 'plastico_blanco', bev=0.012)  # papel toalla


def b_tocador(m, w, d, h, o, rnd):
    _gabinete(m, w, d, h, 'madera_media', 'granito', 0.03, puertas=3 if w > 1.2 else 2, z_zocalo=0.12)
    n = 2 if w > 1.2 else 1
    for i in range(n):
        x = -w / 2 + w * (i + 0.5) / n
        _fregadero(m, x, 0.03, h, 0.40, 0.30, 0.13, 'porcelana')
        _grifo(m, x, -d / 2 + 0.06, h, 0.20, 0.15)
    m.caja(-w / 2, -d / 2, h, w / 2, -d / 2 + 0.015, h + 0.10, 'granito')
    m.caja(-w / 2 + 0.05, -d / 2, h + 0.20, w / 2 - 0.05, -d / 2 + 0.015, h + 1.05, 'espejo', bev=0.004)
    m.caja(-w / 2 + 0.03, -d / 2, h + 1.08, w / 2 - 0.03, -d / 2 + 0.10, h + 1.12, 'metal_gris')
    m.luz(0, 0.0, h + 1.05, 10, 0.2, (1, 0.93, 0.85))
    m.caja(0.05, 0.0, h, 0.20, 0.12, h + 0.12, 'color_4', bev=0.01)


def b_ducha(m, w, d, h, o, rnd):
    """Ducha a ras de piso: rejilla, columna de ducha, barras de apoyo, asiento abatible y cortina."""
    hw, hd = w / 2, d / 2
    m.caja(-hw + 0.01, -hd + 0.01, 0, hw - 0.01, hd - 0.01, 0.006, 'vinil_gris')
    m.caja(-0.30, -0.03, 0.006, 0.30, 0.03, 0.009, 'cromo')
    # columna
    m.cil(0.0, -hd + 0.06, 0.95, 2.05, 0.012, 'cromo', 10)
    m.tubo((0.0, -hd + 0.06, 2.05), (0.0, -hd + 0.30, 2.05), 0.012, 'cromo')
    m.cil(0.0, -hd + 0.30, 2.00, 2.03, 0.11, 'cromo', 24)
    m.caja(-0.10, -hd + 0.0, 1.00, 0.10, -hd + 0.07, 1.12, 'cromo', bev=0.01)
    m.tubo((0.12, -hd + 0.04, 1.05), (0.12, -hd + 0.06, 1.55), 0.015, 'cromo')
    # barras de apoyo
    m.tubo((-hw + 0.06, -hd + 0.05, 0.85), (hw - 0.06 - 0.25, -hd + 0.05, 0.85), 0.017, 'cromo')
    m.tubo((-hw + 0.05, -hd + 0.3, 0.85), (-hw + 0.05, -hd + 0.3, 1.50), 0.017, 'cromo')
    # asiento abatible de listones
    if o.get('asiento', True):
        for i in range(5):
            y = -hd + 0.06 + i * 0.085
            m.caja(-hw + 0.05, y, 0.46, -hw + 0.50, y + 0.07, 0.48, 'madera_clara', bev=0.005)
        for x in (-hw + 0.08, -hw + 0.46):
            m.tubo((x, -hd + 0.02, 0.30), (x, -hd + 0.42, 0.46), 0.012, 'cromo')
    if o.get('vidrio'):
        m.caja(-hw + 0.0, hd - 0.02, 0.0, hw - 0.30, hd - 0.008, 2.0, 'vidrio_int')
        m.caja(-hw + 0.0, hd - 0.025, 0.0, -hw + 0.03, hd - 0.003, 2.0, 'cromo')
    else:
        m.tubo((-hw + 0.02, hd - 0.03, 2.02), (hw - 0.02, hd - 0.03, 2.02), 0.012, 'cromo')
        # cortina recogida a un lado, con pliegues
        x0, x1 = hw - 0.45, hw - 0.04
        n = 9
        for i in range(n):
            x = x0 + (x1 - x0) * i / (n - 1)
            dy = 0.04 * math.sin(i * 1.7)
            m.caja(x - 0.03, hd - 0.05 + dy, 0.18, x + 0.03, hd - 0.01 + dy, 2.0, 'cortina_blanca', bev=0.012)
    m.caja(hw - 0.08, -hd, 1.15, hw - 0.01, -hd + 0.10, 1.32, 'plastico_blanco', bev=0.01)


def b_barra_buffet(m, w, d, h, o, rnd):
    patas(m, -w / 2 + 0.05, -d / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.05, h - 0.05, 0.022, 'madera_clara', cuadradas=True)
    m.caja(-w / 2, -d / 2, h - 0.05, w / 2, d / 2, h, 'madera_clara', bev=0.008)
    m.caja(-w / 2 + 0.06, -d / 2 + 0.06, 0.22, w / 2 - 0.06, d / 2 - 0.06, 0.24, 'madera_clara')
    # dos termos de café, canasta de frutas, vitrina de pan, tazas
    for x in (-0.72, -0.48):
        m.cil(x, 0.0, h, h + 0.04, 0.09, 'metal_negro', 18)
        m.cil(x, 0.0, h + 0.04, h + 0.40, 0.085, 'inox', 20)
        m.cil(x, 0.0, h + 0.40, h + 0.44, 0.06, 'metal_negro', 16)
        m.tubo((x, 0.085, h + 0.10), (x, 0.13, h + 0.10), 0.01, 'metal_negro')
    m.cil(-0.12, 0.0, h, h + 0.12, 0.16, 'cesta', 20, r2=0.19)
    for k in range(9):
        a = k * 0.7
        m.esfera(-0.12 + 0.09 * math.cos(a), 0.09 * math.sin(a), h + 0.15 + 0.03 * (k % 3), 0.045,
                 ['fruta_roja', 'fruta_amarilla', 'fruta_naranja', 'pelota_verde'][k % 4], 10)
    m.cil(0.30, 0.0, h, h + 0.02, 0.17, 'madera_media', 24)
    m.cil(0.30, 0.0, h + 0.02, h + 0.20, 0.15, 'vidrio_int', 24)
    m.esfera(0.30, 0.0, h + 0.20, 0.15, 'vidrio_int', 16, esc=(1, 1, 0.5))
    for k in range(5):
        m.esfera(0.26 + 0.05 * (k % 3), -0.04 + 0.04 * (k // 3), h + 0.05, 0.035, 'color_3', 8, esc=(1.3, 1, 0.6))
    for i in range(6):
        m.cil(0.55 + 0.09 * (i % 3), -0.06 + 0.11 * (i // 3), h, h + 0.08, 0.035, 'porcelana', 12, r2=0.04)
    m.caja(0.78, -0.12, h, 0.88, 0.12, h + 0.03, 'papel')


def b_mesa_redonda(m, w, d, h, o, rnd):
    m.cil(0, 0, 0.72, 0.75, 0.38, 'madera_clara', 36)
    patas(m, -0.24, -0.24, 0.24, 0.24, 0.72, 0.022, 'madera_clara', cono=0.016)
    m.caja(-0.24, -0.24, 0.62, 0.24, 0.24, 0.66, 'madera_clara')
    n = o.get('sillas', 4)
    for i in range(n):
        a = 2 * math.pi * i / n + 0.4
        with m.at(0.52 * math.cos(a), 0.52 * math.sin(a), 0, g=math.degrees(a) - 90):
            with m.at(0, 0, 0, g=180):
                silla_comedor(m, o.get('tela', 'tela_salvia'), 'madera_clara', brazos=False)
    m.cil(0.0, 0.0, 0.75, 0.87, 0.04, 'vidrio_int', 12)
    m.esfera(0.0, 0.0, 0.92, 0.05, 'fruta_roja', 10)


def b_dispensador(m, w, d, h, o, rnd):
    m.caja(-w / 2, -d / 2, 0, w / 2, d / 2, 0.82, 'plastico_blanco', bev=0.02)
    m.caja(-0.10, d / 2, 0.55, 0.10, d / 2 + 0.06, 0.70, 'plastico_gris', bev=0.01)
    for x in (-0.05, 0.05):
        m.caja(x - 0.015, d / 2 + 0.03, 0.62, x + 0.015, d / 2 + 0.07, 0.66, 'pelota_azul' if x > 0 else 'pelota_roja')
    m.cil(0, 0, 0.82, 1.12, 0.13, 'agua_azul', 24)
    m.cil(0, 0, 1.12, 1.17, 0.06, 'agua_azul', 16, r2=0.03)


def b_portagarrafon(m, w, d, h, o, rnd):
    for (x, y) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
        m.caja(x - 0.012, y - 0.012, 0, x + 0.012, y + 0.012, 0.62, 'metal_negro')
    m.caja(-0.19, -0.19, 0.60, 0.19, 0.19, 0.63, 'granito')
    m.caja(-0.19, -0.19, 0.12, 0.19, 0.19, 0.135, 'metal_negro')
    m.toro(0, 0, 0.30, 0.17, 0.008, 'metal_negro', seg=20, seg2=6)
    m.cil(0, 0, 0.63, 1.00, 0.14, 'agua_azul', 24)
    m.cil(0, 0, 1.00, 1.08, 0.13, 'agua_azul', 24, r2=0.05)
    m.cil(0, 0, 1.08, 1.12, 0.04, 'pelota_azul', 12)


def b_pizarra(m, w, d, h, o, rnd):
    for s in (-1, 1):
        m.tubo((s * 0.28, -0.20, 0), (s * 0.28, 0.0, 1.38), 0.016, 'madera_media', 6)
        m.tubo((s * 0.28, 0.22, 0), (s * 0.28, 0.0, 1.38), 0.016, 'madera_media', 6)
    with m.at(0, -0.10, 0.45, rx=8):
        m.caja(-0.30, -0.02, 0, 0.30, 0.0, 0.88, 'madera_media', bev=0.006)
        m.caja(-0.27, 0.0, 0.03, 0.27, 0.003, 0.85, 'pizarra')
        for i in range(6):
            m.caja(-0.20, 0.003, 0.70 - i * 0.10, -0.20 + 0.12 + 0.25 * ((i * 7) % 3) / 3, 0.004, 0.71 - i * 0.10, 'papel')


def b_planta(m, w, d, h, o, rnd):
    tipo = o.get('tipo', 'ficus')
    planta_hojas(m, 0, 0, 0, h, rnd, o.get('maceta', 'maceta_blanca' if tipo != 'palma' else 'cesta'), min(w, d) * 0.40, n=46, tipo=tipo)


def b_planta_med(m, w, d, h, o, rnd):
    planta_hojas(m, 0, 0, 0, h, rnd, o.get('maceta', 'maceta_gris'), min(w, d) * 0.40, n=22,
                 tipo=o.get('tipo', 'sansevieria' if rnd.random() < 0.5 else 'palma'))


def b_banca(m, w, d, h, o, rnd):
    for s in (-1, 1):
        m.caja(s * (w / 2 - 0.08) - 0.025, -d / 2 + 0.03, 0, s * (w / 2 - 0.08) + 0.025, d / 2 - 0.03, h - 0.05, 'metal_negro')
    for i in range(4):
        y = -d / 2 + 0.02 + i * (d - 0.04) / 4
        m.caja(-w / 2, y + 0.005, h - 0.05, w / 2, y + (d - 0.04) / 4 - 0.005, h, 'madera_clara', bev=0.005)


def b_lampara_pie(m, w, d, h, o, rnd):
    m.cil(0, 0, 0, 0.03, 0.15, 'metal_negro', 20)
    m.cil(0, 0, 0.03, h - 0.30, 0.012, 'metal_negro', 8)
    m.cil(0, 0, h - 0.32, h, 0.18, 'pantalla_lampara', 24, r2=0.15)
    m.esfera(0, 0, h - 0.18, 0.04, 'luz_calida', 8)
    m.luz(0, 0, h - 0.16, 25, 0.05)


BUILD = {k[2:]: v for k, v in globals().items() if k.startswith('b_')}


# ===================================================================== ubicación
def amueblar(K, E, clave, coleccion=None):
    """Construye y coloca todos los muebles de un edificio; devuelve la cuenta de camas por cuarto."""
    col = coleccion or K.c
    luces = []
    cuenta = {}
    for nv in E['niveles']:
        listas = dict(A.DIST.get((clave, nv['id']), {}))
        listas.update(A.EXTRA.get((clave, nv['id']), {}))
        z0 = nv['z0'] + 0.02
        for cid, lista in listas.items():
            for i, it in enumerate(lista):
                t = it['t']
                w, d, h = A.CAT[t]
                w, d = it.get('w', w), it.get('d', d)
                rnd = random.Random(hash((clave, nv['id'], cid, i)) & 0xffff)
                m = Malla()
                BUILD[t](m, w, d, h, it, rnd)
                ob = m.objeto(f'{K.pfx}_mueble_{cid}_{t}_{i}', K.M, col)
                box_uv(ob, 1.0)
                zb = z0 + (0.0 if cid != 'galeria' else 0.0)
                ob.location = (it['x'], it['y'], zb)
                ob.rotation_euler = (0, 0, R(it['g']))
                K.objs.append(ob)
                for (co, pw, rad, colr) in m.luces:
                    luces.append((ob, co, pw, rad, colr))
                if t.startswith('cama'):
                    cuenta[cid] = cuenta.get(cid, 0) + 1
    K.luces_muebles = luces
    return cuenta


def luces_de_muebles(K, coleccion):
    """Luces puntuales de lámparas de mesa/pie y campana (hijas del mueble)."""
    out = []
    for (ob, co, pw, rad, colr) in getattr(K, 'luces_muebles', []):
        ld = bpy.data.lights.new(ob.name + '_luz', 'POINT')
        ld.energy = pw; ld.shadow_soft_size = rad; ld.color = colr
        lo = bpy.data.objects.new(ld.name, ld)
        coleccion.objects.link(lo)
        lo.parent = ob
        lo.location = co
        out.append(lo)
    return out


def b_ropero_doble(m, w, d, h, o, rnd):
    b_ropero(m, w, d, h, o, rnd)


def b_sofa2(m, w, d, h, o, rnd):
    b_sofa(m, w, d, h, o, rnd)


def b_aparador(m, w, d, h, o, rnd):
    _gabinete(m, w, d, 0.85, 'madera_clara', 'madera_clara', 0.03)
    m.caja(-w / 2, -d / 2, 0.85, w / 2, d / 2 - 0.05, h, 'madera_clara', bev=0.006)
    m.caja(-w / 2 + 0.03, d / 2 - 0.06, 0.88, w / 2 - 0.03, d / 2 - 0.05, h - 0.03, 'vidrio_int')
    for z in (1.10, 1.35):
        m.caja(-w / 2 + 0.03, -d / 2 + 0.02, z, w / 2 - 0.03, d / 2 - 0.07, z + 0.015, 'vidrio_int')
        for k in range(4):
            m.cil(-w / 2 + 0.15 + k * 0.25, 0.0, z + 0.015, z + 0.035, 0.1, 'porcelana', 20)


BUILD = {k[2:]: v for k, v in globals().items() if k.startswith('b_')}
