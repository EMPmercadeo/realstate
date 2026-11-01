"""
Exteriores del lote según las fotos y videos del 31-10-2026 (carpeta "VIDEOS REFERENCIA MAS REAL") y el
satélite (Google, Esri y Bing). Ver docs/fase-mapa.md.

Lo que EXISTE hoy (fotos):
  - Camino de baldosa de abanico con franjas antideslizantes, paralelo al muro de la calle de tierra,
    desde la plazoleta del norte del gris hasta el muro con portón del patio de grava de la casa.
  - Rampas de concreto con muretes grises y barandas negras de tubo, descansos azules con el símbolo de
    accesibilidad (al lado este del camino).
  - Oficinita blanca con puerta corrediza de vidrio y techo de lámina (al noreste del gris; el satélite
    la muestra), con el bananal al lado ("donde están los tallos", probablemente).
  - Quiosco amarillo de dos vanos, muro amarillo, pilares color arena con bola blanca y portones negros
    en la calle de tierra; palmas fénix junto a la galería norte del gris; patio de grava atrás de la casa.
Lo PROPUESTO (contexto del proyecto, no existe hoy): gazebo de juegos con letrero, tina de hidroterapia
donde estaba el mango (tocón en el césped al oeste del camino) y huerto de 4 surcos con cerca al lado
de la oficinita.

Todo se define en el marco del edificio gris (x de norte a sur, y de oeste a este) en UNIDADES DE DISEÑO
(sitio.kp() las pasa a metros), pero las piezas se construyen con su tamaño real en metros. El terreno
del modelo es plano: el desnivel real entre la casa y el gris (que explica las rampas) falta medirlo.
"""
import math, random
import bpy
from mathutils import Vector
import sitio
from muebles3d import Malla

R = math.radians


class Marco:
    """Malla en el marco del gris: coordenadas de entrada en unidades de diseño, piezas en metros."""
    def __init__(self):
        self.ox, self.oy, self.ang = sitio.marco(sitio.GRIS)
        self.k = sitio.kp()

    def P(self, x, y):
        return (x * self.k, y * self.k)

    def malla(self):
        m = Malla()
        m._ctx = m.at(self.ox, self.oy, 0, g=math.degrees(self.ang))
        m._ctx.__enter__()
        return m


def cerrar(m, nombre, M, C):
    m._ctx.__exit__(None, None, None)
    ob = m.objeto(nombre, M, C)
    from lib import box_uv
    box_uv(ob, 1.0)
    return ob


# ------------------------------------------------------------------ piezas (metros, en el marco del gris)
def tramo(m, p, q, ancho, z0, z1, mat, off=0.0):
    """Caja a lo largo del segmento p→q (puntos en metros del marco) con ancho y desplazamiento lateral."""
    p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
    d = q - p
    L = d.length
    g = math.degrees(math.atan2(d.y, d.x))
    with m.at(p.x, p.y, 0, g=g):
        m.caja(0, off - ancho / 2, z0, L, off + ancho / 2, z1, mat)


def baranda_tubo(m, p, q, alto=0.92, paso=1.6, mat='metal_negro', base=True, z0=0.0):
    """Baranda de tubo cuadrado: postes (con dado de concreto si base) y dos pasamanos (0,45 m y arriba),
    apoyada a la altura z0 (p. ej. sobre un murete)."""
    p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
    d = q - p
    L = d.length
    g = math.degrees(math.atan2(d.y, d.x))
    n = max(1, round(L / paso))
    with m.at(p.x, p.y, z0, g=g):
        for i in range(n + 1):
            u = L * i / n
            m.caja(u - 0.025, -0.025, 0.0, u + 0.025, 0.025, alto, mat)
            if base:
                m.cil(u, 0, 0.0, 0.10, 0.075, 'concreto_claro', segs=10)
        for z in (min(0.45, alto * 0.5), alto - 0.04):
            m.caja(0, -0.025, z, L, 0.025, z + 0.045, mat)


def camino_baldosa(m, p, q, ancho=1.25, paso_franja=0.62):
    """Camino de baldosa de abanico con franjas negras antideslizantes (fotos 113820 y 113831)."""
    tramo(m, p, q, ancho, 0.0, 0.045, 'baldosa_abanico')
    p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
    d = q - p
    L = d.length
    g = math.degrees(math.atan2(d.y, d.x))
    with m.at(p.x, p.y, 0, g=g):
        u = 0.4
        while u < L - 0.2:
            m.caja(u - 0.025, -0.16, 0.045, u + 0.025, 0.16, 0.05, 'banda_negra')
            u += paso_franja


def rampa(m, p, q, ancho=1.3, muro=0.42):
    """Rampa de concreto con murete gris a cada lado y baranda negra encima del murete."""
    tramo(m, p, q, ancho, 0.0, 0.06, 'concreto_rampa')
    for s in (-1, 1):
        off = s * (ancho / 2 + 0.075)
        tramo(m, p, q, 0.15, 0.0, muro, 'murete_gris', off=off)
        pp = Vector((p[0], p[1], 0)); qq = Vector((q[0], q[1], 0))
        d = (qq - pp).normalized(); n = Vector((-d.y, d.x, 0)) * (off + s * 0.12)
        baranda_tubo(m, pp + n, qq + n)


def descanso(m, x0, y0, x1, y1, simbolo=True):
    """Descanso pintado de azul (símbolo de accesibilidad en blanco)."""
    m.caja(x0, y0, 0.0, x1, y1, 0.065, 'azul_accesible')
    if simbolo:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        m.toro(cx + 0.05, cy - 0.05, 0.066, 0.28, 0.025, 'blanco', seg=20, seg2=4)
        m.cil(cx - 0.12, cy + 0.28, 0.065, 0.07, 0.07, 'blanco', segs=10)
        m.caja(cx - 0.15, cy - 0.05, 0.065, cx - 0.09, cy + 0.2, 0.07, 'blanco')
        m.caja(cx - 0.15, cy - 0.05, 0.065, cx + 0.18, cy + 0.01, 0.07, 'blanco')


def muro(m, p, q, alto=1.55, grueso=0.18, mat='amarillo_muro', pilares=3.0, mat_pilar=None, bola=True):
    """Muro con pilares cada `pilares` m y bola blanca (como los del lote)."""
    tramo(m, p, q, grueso, 0.0, alto, mat)
    pp = Vector((p[0], p[1], 0)); qq = Vector((q[0], q[1], 0))
    L = (qq - pp).length
    n = max(1, round(L / pilares))
    for i in range(n + 1):
        c = pp + (qq - pp) * (i / n)
        m.cc(c.x, c.y, 0.0, 0.40, 0.40, alto + 0.35, mat_pilar or mat)
        m.cc(c.x, c.y, alto + 0.35, 0.48, 0.48, 0.07, 'blanco')
        if bola:
            m.esfera(c.x, c.y, alto + 0.58, 0.15, 'blanco', seg=10)


def porton_negro(m, p, q, alto=1.8, arco=0.0, celosia=False, paso=0.12):
    """Portón de barrotes negros (opcional: remate en arco y celosía baja), en el segmento p→q."""
    pp = Vector((p[0], p[1], 0)); qq = Vector((q[0], q[1], 0))
    d = qq - pp
    L = d.length
    g = math.degrees(math.atan2(d.y, d.x))
    with m.at(pp.x, pp.y, 0, g=g):
        u = paso / 2
        while u < L:
            h = alto + arco * math.sin(math.pi * u / L)
            m.caja(u - 0.012, -0.012, 0.05, u + 0.012, 0.012, h, 'metal_negro')
            u += paso
        for z in (0.05, alto * 0.5, alto - 0.05):
            m.caja(0, -0.025, z, L, 0.025, z + 0.05, 'metal_negro')
        if arco:
            nn = 12
            for i in range(nn):
                a0, a1 = i / nn, (i + 1) / nn
                m.tubo((a0 * L, 0, alto + arco * math.sin(math.pi * a0) + 0.05),
                       (a1 * L, 0, alto + arco * math.sin(math.pi * a1) + 0.05), 0.022, 'metal_negro', segs=6)
        if celosia:
            nd = max(2, int(L / 0.22))
            for i in range(nd):
                for s in (1, -1):
                    with m.at(L * (i + 0.5) / nd, 0, 0.32, ry=s * 55):
                        m.caja(-0.2, -0.01, -0.01, 0.2, 0.01, 0.01, 'metal_negro')


# ------------------------------------------------------------------ construcciones pequeñas
def oficinita(m, cx, cy, g=0.0):
    """Oficinita blanca (iba a ser de fotocopias → oficina del huerto y bodega): 3,6 × 3,0 m, techo de
    lámina a un agua, frente con puerta corrediza de vidrio de piso a techo (video 113942)."""
    W, D, H = 3.6, 3.0, 2.55
    with m.at(cx, cy, 0, g=g):
        m.caja(-W / 2 - 0.5, -D / 2 - 0.9, 0.0, W / 2 + 0.5, D / 2 + 0.3, 0.12, 'concreto_claro')   # base y acera
        m.caja(-W / 2, -D / 2 + 0.15, 0.12, -W / 2 + 0.18, D / 2, H, 'blanco_muro')
        m.caja(W / 2 - 0.18, -D / 2 + 0.15, 0.12, W / 2, D / 2, H, 'blanco_muro')
        m.caja(-W / 2, D / 2 - 0.18, 0.12, W / 2, D / 2, H, 'blanco_muro')
        m.caja(-W / 2, -D / 2 + 0.15, 0.12, -0.2, -D / 2 + 0.33, H, 'blanco_muro')               # muro frontal ciego (izq.)
        m.caja(-0.2, -D / 2 + 0.2, 0.12, W / 2 - 0.18, -D / 2 + 0.24, H - 0.12, 'vidrio_osc')    # vidrio corredizo
        for u in (-0.2, 0.75, W / 2 - 0.2):
            m.caja(u - 0.03, -D / 2 + 0.17, 0.12, u + 0.03, -D / 2 + 0.27, H - 0.1, 'aluminio')
        m.caja(-0.2, -D / 2 + 0.17, H - 0.16, W / 2 - 0.18, -D / 2 + 0.27, H - 0.08, 'aluminio')
        m.caja(-W / 2 + 0.2, D / 2 - 0.22, 0.12, W / 2 - 0.2, D / 2 - 0.18, H - 0.1, 'rojo_interior')   # muro rojo de adentro
        m.caja(-W / 2 + 0.18, -D / 2 + 0.33, 0.12, W / 2 - 0.18, D / 2 - 0.18, 0.14, 'piso_gris')
        with m.at(0, 0, H, rx=-7):                                                               # techo a un agua
            m.caja(-W / 2 - 0.35, -D / 2 - 0.45, 0.0, W / 2 + 0.35, D / 2 + 0.3, 0.05, 'lamina_techo')
            m.caja(-W / 2 - 0.35, -D / 2 - 0.47, -0.12, W / 2 + 0.35, -D / 2 - 0.43, 0.05, 'blanco')
        m.caja(-W / 2 - 0.05, -D / 2 - 0.85, 0.12, W / 2 + 0.05, -D / 2 - 0.55, 0.32, 'concreto_claro')  # jardinera baja


def quiosco(m, cx, cy, g=0.0):
    """Quiosco amarillo de dos vanos abiertos con losa plana (foto 113841)."""
    W, D, H = 3.4, 1.7, 2.15
    with m.at(cx, cy, 0, g=g):
        m.caja(-W / 2, -D / 2, 0.0, W / 2, D / 2, 0.08, 'concreto_claro')
        m.caja(-W / 2, D / 2 - 0.15, 0.08, W / 2, D / 2, H, 'amarillo_muro')
        for u in (-W / 2, -0.075, W / 2 - 0.15):
            m.caja(u, -D / 2, 0.08, u + 0.15, D / 2, H, 'amarillo_muro')
        m.caja(-W / 2 - 0.12, -D / 2 - 0.12, H, W / 2 + 0.12, D / 2 + 0.12, H + 0.12, 'concreto_claro')
        m.caja(-W / 2 - 0.13, -D / 2 - 0.13, H + 0.12, W / 2 + 0.13, D / 2 + 0.13, H + 0.16, 'lamina')
        m.caja(-W / 2 - 0.13, -D / 2 - 0.13, H - 0.1, W / 2 + 0.13, -D / 2 - 0.1, H + 0.12, 'verde_borde')


def gazebo(m, cx, cy, r=2.1):
    """PROPUESTA: gazebo octogonal de juegos de mesa con letrero "Área recreativa / juegos sociales"."""
    with m.at(cx, cy, 0):
        verts8 = [(r * math.cos(R(22.5 + 45 * i)), r * math.sin(R(22.5 + 45 * i))) for i in range(8)]
        m.cil(0, 0, 0.0, 0.15, r + 0.25, 'piso_terraza', segs=8)
        for (x, y) in verts8:
            m.cil(x * 0.93, y * 0.93, 0.15, 2.55, 0.08, 'madera_clara', segs=8)
        m.cil(0, 0, 2.55, 2.75, r + 0.1, 'madera_clara', segs=8)
        m.cil(0, 0, 2.75, 3.75, r + 0.55, 'teja', segs=8, r2=0.12)
        m.cil(0, 0, 0.15, 0.85, 0.08, 'madera_oscura', segs=8)
        m.cil(0, 0, 0.85, 0.9, 0.55, 'madera_clara', segs=16)                    # mesa de dominó
        for i in range(4):
            a = R(45 + 90 * i)
            m.cil(math.cos(a) * 0.95, math.sin(a) * 0.95, 0.15, 0.6, 0.2, 'madera_oscura', segs=10)
        for i in range(8):                                                      # baranda baja entre postes
            (x0, y0), (x1, y1) = verts8[i], verts8[(i + 1) % 8]
            if i == 6:
                continue                                                        # entrada
            m.tubo((x0 * 0.93, y0 * 0.93, 0.85), (x1 * 0.93, y1 * 0.93, 0.85), 0.03, 'madera_clara', segs=6)
        x0, y0 = verts8[6][0] * 0.93, verts8[6][1] * 0.93
        x1, y1 = verts8[7][0] * 0.93, verts8[7][1] * 0.93
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        g = math.degrees(math.atan2(y1 - y0, x1 - x0))
        with m.at(mx, my, 2.3, g=g):
            m.caja(-0.75, -0.04, 0.0, 0.75, 0.0, 0.36, 'letrero_verde')
            m.caja(-0.7, -0.045, 0.06, 0.7, -0.04, 0.3, 'blanco')


def tina(m, cx, cy):
    """PROPUESTA: tina de hidroterapia (agua tibia en movimiento) sobre deck de madera con escalón y
    pasamanos, donde estaba el palo de mango."""
    with m.at(cx, cy, 0):
        m.caja(-1.6, -1.6, 0.0, 1.6, 1.6, 0.45, 'madera_deck')
        m.cil(0, 0, 0.0, 0.47, 1.12, 'piedra_clara', segs=32)
        m.cil(0, 0, 0.05, 0.42, 0.98, 'agua', segs=32)
        m.toro(0, 0, 0.47, 1.05, 0.06, 'piedra_clara', seg=32, seg2=6)
        m.caja(-0.7, -2.05, 0.0, 0.7, -1.6, 0.22, 'madera_deck')
        for s in (-1, 1):
            m.tubo((s * 0.45, -2.0, 0.22), (s * 0.45, -2.0, 1.1), 0.025, 'acero', segs=8)
            m.tubo((s * 0.45, -2.0, 1.1), (s * 0.45, -1.4, 1.35), 0.025, 'acero', segs=8)
            m.tubo((s * 0.45, -1.4, 1.35), (s * 0.45, -1.15, 0.47), 0.025, 'acero', segs=8)
        for (x, y) in ((-1.35, 1.35), (1.35, 1.35)):
            m.cil(x, y, 0.45, 0.85, 0.22, 'maceta_terracota', segs=12)


def huerto(m, x0, y0, x1, y1, n=4):
    """PROPUESTA: huerto de `n` surcos con cerca de malla y postes (de la oficinita a la esquina)."""
    L = x1 - x0
    sep = (y1 - y0) / n
    rnd = random.Random(11)
    for i in range(n):
        yc = y0 + sep * (i + 0.5)
        m.caja(x0 + 0.6, yc - 0.35, 0.0, x1 - 0.6, yc + 0.35, 0.22, 'tierra_surco')
        u = x0 + 0.9
        while u < x1 - 0.8:
            h = 0.25 + rnd.random() * 0.25
            m.esfera(u, yc + rnd.uniform(-0.12, 0.12), 0.22 + h / 2, h * 0.55, 'hoja_hortaliza', seg=8, esc=(1, 1, 0.8))
            u += 0.45
    for (p, q) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0 + 1.6))):
        pp, qq = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
        Ls = (qq - pp).length
        k = max(1, round(Ls / 2.0))
        for j in range(k + 1):
            c = pp + (qq - pp) * (j / k)
            m.cil(c.x, c.y, 0.0, 1.25, 0.045, 'madera_oscura', segs=6)
        tramo(m, (pp.x, pp.y), (qq.x, qq.y), 0.01, 0.1, 1.15, 'malla_cerca')


# ------------------------------------------------------------------ vegetación con geometría (para la web)
def banano(m, x, y, h, rnd):
    """Mata de banano: pseudotallo y 7-9 hojas grandes arqueadas, algunas secas (video 113911)."""
    m.cil(x, y, 0.0, h * 0.62, 0.11, 'tallo_banano', segs=8, r2=0.08)
    nh = rnd.randint(7, 9)
    for i in range(nh):
        a = 2 * math.pi * i / nh + rnd.uniform(-0.3, 0.3)
        sube = rnd.uniform(0.35, 0.9)
        d = Vector((math.cos(a), math.sin(a), sube))
        seca = rnd.random() < 0.25
        m.hoja((x, y, h * 0.6 + rnd.uniform(-0.1, 0.15)), d, rnd.uniform(1.5, 2.1), rnd.uniform(0.75, 0.95),
               'hoja_seca' if seca else 'hoja_banano', curva=0.55 if seca else 0.3, giro=rnd.uniform(-0.3, 0.3))
    if rnd.random() < 0.4:                                                        # racimo
        m.cil(x + 0.15, y, h * 0.35, h * 0.55, 0.12, 'racimo', segs=8, r2=0.05)


def palma_fenix(m, x, y, h, rnd, troncos=4):
    """Palma fénix en macolla (varios troncos con frondas finas y raíces colgantes) junto al gris."""
    for t in range(troncos):
        a = 2 * math.pi * t / troncos + rnd.uniform(0, 0.6)
        lean = rnd.uniform(0.15, 0.45)
        ht = h * rnd.uniform(0.7, 1.0)
        top = (x + math.cos(a) * lean * ht * 0.3, y + math.sin(a) * lean * ht * 0.3, ht)
        m.tubo((x + math.cos(a) * 0.2, y + math.sin(a) * 0.2, 0), top, 0.13, 'tronco_palma', segs=7)
        m.cil(top[0], top[1], ht - 0.9, ht - 0.05, 0.17, 'fronda_seca', segs=8, r2=0.13)   # barba seca
        nf = 22
        for i in range(nf):
            b = 2 * math.pi * i / nf + rnd.uniform(-0.15, 0.15)
            d = Vector((math.cos(b), math.sin(b), rnd.uniform(-0.25, 0.7)))
            m.hoja(top, d, rnd.uniform(1.7, 2.3), 0.26, 'fronda', curva=0.4, giro=R(90))


def palma_navidad(m, x, y, h, rnd):
    """Palma de navidad (Adonidia) de un tronco, como las del portón del gris (Street View y video 113649)."""
    lean = rnd.uniform(-0.25, 0.25)
    top = (x + lean, y + rnd.uniform(-0.2, 0.2), h)
    m.tubo((x, y, 0), top, 0.11, 'tronco_gris', segs=8)
    m.cil(top[0], top[1], h - 0.9, h + 0.05, 0.13, 'tallo_banano', segs=8, r2=0.10)      # capitel verde
    for i in range(11):
        b = 2 * math.pi * i / 11 + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(b), math.sin(b), rnd.uniform(0.0, 0.9)))
        m.hoja((top[0], top[1], h + 0.02), d, rnd.uniform(1.6, 2.1), 0.5, 'fronda', curva=0.45, giro=R(90))


def cipres(m, x, y, h, rnd):
    """Árbol columnar oscuro (tuya o ciprés) de la hilera de la calle de tierra (Street View)."""
    m.cil(x, y, 0.0, 0.5, 0.12, 'tronco_palma', segs=6)
    r = rnd.uniform(0.75, 1.0)
    for k, (z, rr) in enumerate(((0.35, 1.0), (0.55, 0.9), (0.75, 0.7), (0.9, 0.45))):
        m.esfera(x + rnd.uniform(-0.08, 0.08), y + rnd.uniform(-0.08, 0.08), h * z, r * rr, 'cipres', seg=8,
                 esc=(1, 1, h * 0.22 / max(0.3, r * rr)))


def croton(m, x, y, h, rnd):
    for i in range(10):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0, 0.35)
        m.esfera(x + math.cos(a) * r, y + math.sin(a) * r, rnd.uniform(0.35, 0.8) * h, rnd.uniform(0.22, 0.32),
                 rnd.choice(('croton_amarillo', 'croton_rojo', 'croton_verde')), seg=7, esc=(1, 1, 0.8))


# ------------------------------------------------------------------ armado
def construir(M, C):
    F = Marco()
    P = F.P
    rnd = random.Random(31)
    objs = []

    # ---- plazoleta al norte del gris (donde se estaciona junto a la galería) y descanso al pie de la rampa
    m = F.malla()
    x0, y0 = P(-4.2, 1.6); x1, y1 = P(0.2, 13.0)
    m.caja(x0, y0, 0.0, x1, y1, 0.04, 'concreto_claro')
    descanso(m, *P(-4.6, 4.5), *P(-3.0, 6.0))
    # ---- camino de baldosa paralelo al muro de la calle de tierra, hasta el portón del patio de grava
    camino_baldosa(m, P(-4.2, 3.0), P(-19.2, 3.0))
    camino_baldosa(m, P(-12.8, 7.7), P(-12.8, 14.3), ancho=1.1)                    # a la oficinita
    # ---- rampas con murete y baranda; descansos azules
    rampa(m, P(-4.6, 5.25), P(-10.0, 5.25))
    descanso(m, *P(-11.5, 4.5), *P(-10.0, 7.7))
    rampa(m, P(-11.5, 7.0), P(-17.2, 7.0))
    descanso(m, *P(-18.8, 3.6), *P(-17.2, 7.7))
    # ---- muro amarillo con portón negro entre el jardín y el patio de grava de la casa (foto 113831)
    muro(m, P(-19.6, -0.6), P(-19.6, 2.3), alto=1.5)
    muro(m, P(-19.6, 3.8), P(-19.6, 9.5), alto=1.5)
    porton_negro(m, P(-19.6, 2.3), P(-19.6, 3.8), alto=1.55)
    # ---- patio de grava detrás de la casa (foto casa-amarilla-patio y video 114626)
    gx0, gy0 = P(-27.0, -7.6); gx1, gy1 = P(-19.8, 11.5)
    m.caja(gx0, gy0, 0.0, gx1, gy1, 0.035, 'grava')
    objs.append(cerrar(m, 'ext_caminos_rampas', M, C))

    # ---- construcciones pequeñas existentes
    m = F.malla()
    oficinita(m, *P(-12.8, 16.2), g=90.0)            # frente (vidrio) hacia el camino, al oeste
    quiosco(m, *P(-8.6, -0.12), g=180.0)             # contra el muro de la calle de tierra
    objs.append(cerrar(m, 'ext_oficinita_quiosco', M, C))

    # ---- propuesta (contexto del proyecto): gazebo, tina de hidroterapia y huerto
    m = F.malla()
    gazebo(m, *P(-16.2, 13.2))                        # jardín del noreste, entre la oficinita y el patio
    tina(m, *P(-12.2, 0.75))                          # donde estaba el mango (tocón al oeste del camino)
    hx0, hy0 = P(-10.6, 10.6); hx1, hy1 = P(-4.8, 17.6)
    huerto(m, hx0, hy0, hx1, hy1, n=4)
    objs.append(cerrar(m, 'ext_propuesta_gazebo_tina_huerto', M, C))

    # ---- vegetación de las fotos: bananal, palmas fénix, crotos, tocón del mango
    m = F.malla()
    for i in range(16):
        x = rnd.uniform(-11.5, -3.0); y = rnd.uniform(17.9, 21.5) if i < 10 else rnd.uniform(9.0, 10.3)
        if i >= 10:
            x = rnd.uniform(-10.5, -4.5)
        banano(m, *P(x, y), rnd.uniform(3.0, 4.2), rnd)
    for (x, y) in ((-17.0, 1.2), (-15.2, 0.2), (-19.0, 8.8), (-8.2, 8.4), (-5.5, 8.6)):
        croton(m, *P(x, y), rnd.uniform(1.0, 1.5), rnd)
    tx, ty = P(-14.4, 0.6)
    m.cil(tx, ty, 0.0, 0.55, 0.16, 'tronco_palma', segs=9, r2=0.12)               # tocón (foto 113831)
    objs.append(cerrar(m, 'ext_vegetacion', M, C))
    # palmas y árboles columnares: objeto aparte; la web no los exporta y dibuja los suyos (follaje con
    # textura) en las mismas posiciones, guardadas en la propiedad 'arboles_web' (tipo, x, y, alto), con x, y en
    # metros del marco del gris (las que devuelve Marco.P)
    m = F.malla()
    web = []
    for (x, y, h) in ((-1.7, 10.4, 4.6), (-1.9, 12.6, 4.0), (-5.0, 1.2, 4.2), (-3.4, 0.0, 3.6)):
        n = rnd.randint(3, 5)
        palma_fenix(m, *P(x, y), h, rnd, troncos=n)
        web.append(('fenix', *P(x, y), h))
    # hilera de árboles columnares en la orilla de la calle de tierra y palmas de navidad frente al gris
    # (Street View en la calle de tierra, panorama de 8,41245 N 82,44374 O)
    for k, x in enumerate((-4.4, -6.5, -8.1, -10.6, -12.9, -15.8, -17.6)):
        q = P(x + rnd.uniform(-0.3, 0.3), -2.0 + rnd.uniform(-0.25, 0.25)); h = rnd.uniform(3.6, 5.2)
        cipres(m, *q, h, rnd)
        web.append(('cipres', *q, h))
    for x in (9.4, 11.3, 13.2):
        h = rnd.uniform(5.5, 7.0)
        palma_navidad(m, *P(x, -1.6), h, rnd)
        web.append(('navidad', *P(x, -1.6), h))
    ob = cerrar(m, 'ext_arboles', M, C)
    import json
    ob['arboles_web'] = json.dumps([(t, round(a, 2), round(b, 2), round(h, 2)) for t, a, b, h in web])
    objs.append(ob)
    for o in objs:
        o['exterior_fotos'] = 1
    return objs


def materiales(mat, neutro):
    """Materiales nuevos (colores medidos a ojo en las fotos del 31-10-2026)."""
    return dict(
        baldosa_abanico=mat('ex_baldosa_abanico', color=(0.36, 0.25, 0.17, 1), rough=0.75),
        banda_negra=neutro('banda_negra', 0.03, 0.8),
        concreto_rampa=neutro('concreto_rampa', (0.47, 0.47, 0.45), 0.9),
        concreto_claro=neutro('concreto_claro', (0.55, 0.55, 0.53), 0.9),
        murete_gris=neutro('murete_gris', (0.50, 0.52, 0.53), 0.85),
        azul_accesible=neutro('azul_accesible', (0.02, 0.11, 0.55), 0.6),
        amarillo_muro=neutro('amarillo_muro', (0.70, 0.52, 0.07), 0.85),
        arena=neutro('pilar_arena', (0.43, 0.29, 0.16), 0.85),
        blanco_muro=neutro('blanco_muro', 0.80, 0.85),
        rojo_interior=neutro('rojo_interior', (0.33, 0.04, 0.04), 0.8),
        verde_borde=neutro('verde_borde', (0.10, 0.30, 0.10), 0.7),
        grava=neutro('grava', (0.40, 0.39, 0.37), 0.95),
        madera_deck=neutro('madera_deck', (0.30, 0.17, 0.08), 0.7),
        piedra_clara=neutro('piedra_clara', (0.62, 0.60, 0.55), 0.7),
        agua=mat('ex_agua', color=(0.06, 0.32, 0.40, 1), rough=0.12),
        acero=neutro('acero', 0.7, 0.25, 1.0),
        maceta_terracota=neutro('maceta_terracota', (0.45, 0.18, 0.08), 0.8),
        letrero_verde=neutro('letrero_verde', (0.05, 0.25, 0.12), 0.6),
        tierra_surco=neutro('tierra_surco', (0.20, 0.12, 0.07), 1.0),
        hoja_hortaliza=neutro('hoja_hortaliza', (0.12, 0.35, 0.07), 0.8),
        malla_cerca=mat('ex_malla_cerca', color=(0.25, 0.27, 0.25, 1), rough=0.6, alpha=0.35),
        tallo_banano=neutro('tallo_banano', (0.22, 0.25, 0.10), 0.8),
        hoja_banano=neutro('hoja_banano', (0.10, 0.30, 0.06), 0.7),
        hoja_seca=neutro('hoja_seca', (0.33, 0.25, 0.13), 0.9),
        racimo=neutro('racimo', (0.22, 0.38, 0.06), 0.7),
        tronco_palma=neutro('tronco_palma', (0.24, 0.18, 0.12), 0.95),
        fronda=neutro('fronda', (0.09, 0.24, 0.05), 0.75),
        fronda_seca=neutro('fronda_seca', (0.30, 0.24, 0.14), 0.95),
        croton_amarillo=neutro('croton_amarillo', (0.55, 0.40, 0.03), 0.7),
        croton_rojo=neutro('croton_rojo', (0.40, 0.08, 0.03), 0.7),
        croton_verde=neutro('croton_verde', (0.12, 0.28, 0.05), 0.7),
        toldo_rojo=neutro('toldo_rojo', (0.42, 0.04, 0.05), 0.75),
        cipres=neutro('cipres', (0.13, 0.24, 0.04), 0.85),          # tuya verde amarillento (Street View)
        tronco_gris=neutro('tronco_gris', (0.40, 0.38, 0.34), 0.9),
    )
