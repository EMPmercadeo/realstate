"""
Exteriores de las dos construcciones existentes, reconstruidos por volúmenes a partir de las fotos
(web/public/fotos-reales, IMAGENES REALES FACHADA) y de los contornos del satélite (sitio.py).

Medidas proporcionales y aproximadas: ninguna cota de aquí es un levantamiento.
Cada edificio se arma en su marco local y cuelga de un Empty con la posición/giro de sitio.py.

Casa amarilla (marco local):
    x a lo largo de la fachada principal, de izquierda a derecha vista desde la calle de tierra
    (izquierda = lado de la calle C.A), y hacia el fondo, z arriba.
    Cochera adelantada (arco + medallón) a la izquierda; torre de dos niveles con balcón al centro;
    ala baja a la derecha; garaje y portal con columnas sobre el costado de la C.A.
Edificio gris (marco local):
    x de norte a sur a lo largo de la fachada de acceso (hacia la calle de tierra), y hacia el este.
    Ala de la galería cerrada con listones al norte, adelantada; el resto retrocede en dos escalones
    con su propio remate alto de lámina. Galería abierta (terraza) en todo el lado este, con escalera
    metálica exterior al sur.
"""
import math
import bpy
from mathutils import Vector
from lib import box, cylinder, mesh_obj, cut, join, set_parent, empty, coll


# ------------------------------------------------------------------ utilidades
class Kit:
    def __init__(self, M, c, pfx):
        self.M, self.c, self.pfx, self.objs, self.n = M, c, pfx, [], 0
        self.aberturas = []      # (cara, plano, a0, a1, z0, z1): huecos reales para los muros (interiores.py)

    def nm(self, t):
        self.n += 1
        return f'{self.pfx}_{t}_{self.n}'

    def B(self, t, x0, y0, z0, x1, y1, z1, m, keep=True):
        o = box(self.nm(t), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), (min(x0, x1), min(y0, y1), min(z0, z1)), self.M[m] if m else None, self.c, 1.0)
        if keep:
            self.objs.append(o)
        return o

    def cyl(self, t, x, y, z, r, h, m, segs=16, r2=None, keep=True):
        o = cylinder(self.nm(t), r, h, (x, y, z), self.M[m] if m else None, self.c, segs, r2)
        if keep:
            self.objs.append(o)
        return o

    def poly(self, t, verts, faces, m):
        o = mesh_obj(self.nm(t), verts, faces, self.M[m], self.c, 1.0)
        self.objs.append(o)
        return o


def hip(K, t, x0, y0, x1, y1, z, pitch, ov, m, chamfer=0.0, chamfer_side='y0', fascia=0.18, soffit='alero', excluir=None):
    """Techo a cuatro aguas sobre el rectángulo de muros, con alero `ov`, pendiente `pitch` (grados),
    canto (fascia) y cielo de alero. `chamfer` recorta las dos esquinas del lado indicado."""
    ex0, ey0, ex1, ey1 = x0 - ov, y0 - ov, x1 + ov, y1 + ov
    w, d = ex1 - ex0, ey1 - ey0
    h = math.tan(math.radians(pitch)) * min(w, d) / 2
    cx, cy = (ex0 + ex1) / 2, (ey0 + ey1) / 2
    if d >= w:
        R0, R1 = (cx, ey0 + w / 2, z + h), (cx, ey1 - w / 2, z + h)
        key = lambda p: 0 if p[1] < cy else 1
    else:
        R0, R1 = (ex0 + d / 2, cy, z + h), (ex1 - d / 2, cy, z + h)
        key = lambda p: 0 if p[0] < cx else 1
    c = chamfer
    if c and chamfer_side == 'y0':
        P = [(ex0 + c, ey0), (ex1 - c, ey0), (ex1, ey0 + c), (ex1, ey1), (ex0, ey1), (ex0, ey0 + c)]
    elif c and chamfer_side == 'y1':
        P = [(ex0, ey0), (ex1, ey0), (ex1, ey1 - c), (ex1 - c, ey1), (ex0 + c, ey1), (ex0, ey1 - c)]
    else:
        P = [(ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]
    n = len(P)
    verts = [(p[0], p[1], z) for p in P] + [R0, R1] + [(p[0], p[1], z - fascia) for p in P]
    iR = {0: n, 1: n + 1}
    faces = []
    for i in range(n):
        j = (i + 1) % n
        a, b = P[i], P[j]
        ka, kb = key(a), key(b)
        if ka == kb:
            faces.append((i, j, iR[ka]))
        else:
            faces.append((i, j, iR[kb], iR[ka]))
        faces.append((n + 2 + j, n + 2 + i, i, j)[::-1])      # fascia
    roof = K.poly(t, verts, faces, m)
    roof['techo'] = 1
    # cielo del alero: solo el anillo del vuelo (no tapa los cuartos: debajo van el cielo raso y las luces)
    if excluir and not c:
        # alero recortado: no entra en la planta de la casa (debajo van cielos rasos y luces)
        from shapely.geometry import box as _bx
        from shapely.ops import unary_union as _uu
        import interiores as _I
        anillo = _bx(ex0, ey0, ex1, ey1).difference(_bx(x0, y0, x1, y1)).difference(_uu([_bx(*r) for r in excluir]))
        vs, fs = [], []
        for (a_, b_, c_, d_) in _I.celdas(anillo):
            k = len(vs)
            vs += [(a_, b_, z - fascia), (c_, b_, z - fascia), (c_, d_, z - fascia), (a_, d_, z - fascia)]
            fs.append((k + 3, k + 2, k + 1, k))
        if vs:
            so = K.poly(t + '_alero', vs, fs, soffit)
            so['techo'] = 1
        return roof
    I_ = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    sv = [(p[0], p[1], z - fascia) for p in P] + [(p[0], p[1], z - fascia) for p in I_]
    o = lambda i: i
    ii = lambda i: n + i
    if n == 4:
        caras = [(o(i), o((i + 1) % 4), ii((i + 1) % 4), ii(i)) for i in range(4)]
    elif chamfer_side == 'y0':
        caras = [(o(0), o(1), ii(1), ii(0)), (o(1), o(2), ii(1)), (o(2), o(3), ii(2), ii(1)), (o(3), o(4), ii(3), ii(2)),
                 (o(4), o(5), ii(0), ii(3)), (o(5), o(0), ii(0))]
    else:
        caras = [(o(0), o(1), ii(1), ii(0)), (o(1), o(2), ii(2), ii(1)), (o(2), o(3), ii(2)), (o(3), o(4), ii(3), ii(2)),
                 (o(4), o(5), ii(3)), (o(5), o(0), ii(0), ii(3))]
    so = K.poly(t + '_alero', sv, [tuple(f[::-1]) for f in caras], soffit)
    so['techo'] = 1
    return roof


def arco_muro(K, t, x0, x1, y, t_wall, z0, z1, ancho, z_arranque, m, eje='x', centro=None):
    """Muro con un vano en arco de medio punto. eje='x': el muro corre en x a la altura y."""
    cx = centro if centro is not None else (x0 + x1) / 2
    r = ancho / 2
    if eje == 'x':
        w = K.B(t, x0, y - t_wall / 2, z0, x1, y + t_wall / 2, z1, m, keep=False)
        c1 = K.B('cut', cx - r, y - 1, z0 - 0.1, cx + r, y + 1, z_arranque, None, keep=False)
        c2 = K.cyl('cutc', cx, y - 1, z_arranque, r, 2.0, None, segs=32, keep=False)
        c2.rotation_euler = (math.pi / 2, 0, 0); c2.location = (cx, y + 1, z_arranque)
    else:
        w = K.B(t, y - t_wall / 2, x0, z0, y + t_wall / 2, x1, z1, m, keep=False)
        c1 = K.B('cut', y - 1, cx - r, z0 - 0.1, y + 1, cx + r, z_arranque, None, keep=False)
        c2 = K.cyl('cutc', y - 1, cx, z_arranque, r, 2.0, None, segs=32, keep=False)
        c2.rotation_euler = (0, math.pi / 2, 0); c2.location = (y - 1, cx, z_arranque)
    bpy.context.view_layer.update()
    cut(w, [c1, c2])
    K.objs.append(w)
    return w


def ventana(K, cara, a0, a1, z0, z1, plano, sale, rejas=True, arco=False, marco='marco', vidrio='vidrio'):
    """Ventana en la fachada. cara 'x': muro en el plano y=plano (normal hacia afuera = sale);
    cara 'y': muro en el plano x=plano. a0..a1 = tramo horizontal. Registra el hueco para que el muro
    real (interiores.py) quede abierto; el vidrio va dentro del vano."""
    s = sale
    zt = z1 + ((a1 - a0) / 2 if arco else 0.0)
    K.aberturas.append((cara, plano, a0, a1, z0, zt))

    def bx(t, u0, u1, zz0, zz1, d0, d1, m):
        if cara == 'x':
            return K.B(t, u0, plano + s * d0, zz0, u1, plano + s * d1, zz1, m)
        return K.B(t, plano + s * d0, u0, zz0, plano + s * d1, u1, zz1, m)
    f = 0.07
    bx('marco', a0 - f, a0, z0 - f, z1, 0.0, 0.05, marco)
    bx('marco', a1, a1 + f, z0 - f, z1, 0.0, 0.05, marco)
    bx('marco', a0 - f, a1 + f, z0 - f, z0, 0.0, 0.05, marco)
    if not arco:
        bx('marco', a0 - f, a1 + f, z1, z1 + f, 0.0, 0.05, marco)
    bx('vidrio', a0, a1, z0, z1, -0.10, -0.08, vidrio)
    bx('alfeizar', a0 - 0.12, a1 + 0.12, z0 - 0.12, z0 - 0.04, 0.0, 0.12, marco)
    if arco:
        r = (a1 - a0) / 2
        cu = (a0 + a1) / 2
        for rr, mm, d0, d1 in ((r + f, marco, 0.0, 0.05), (r, vidrio, -0.10, -0.08)):
            o = K.cyl('arco', 0, 0, 0, rr, d1 - d0, mm, segs=24)
            mid = plano + s * (d0 + d1) / 2
            if cara == 'x':
                o.rotation_euler = (math.pi / 2, 0, 0); o.location = (cu, mid + (d1 - d0) / 2, z1)
            else:
                o.rotation_euler = (0, math.pi / 2, 0); o.location = (mid - (d1 - d0) / 2, cu, z1)
            cu_box = (K.B('cut', cu - rr - 0.1, plano - 1, z1 - rr - 0.2, cu + rr + 0.1, plano + 1, z1, None, keep=False) if cara == 'x'
                      else K.B('cut', plano - 1, cu - rr - 0.1, z1 - rr - 0.2, plano + 1, cu + rr + 0.1, z1, None, keep=False))
            bpy.context.view_layer.update()
            cut(o, [cu_box])
        # aro: vaciar el disco del marco dejando el borde
        # (el disco de marco queda como arco macizo de 7 cm por fuera del vidrio)
    if rejas:
        u = a0 + 0.11
        while u < a1 - 0.05:
            bx('reja', u - 0.012, u + 0.012, z0, z1, 0.07, 0.1, 'hierro')
            u += 0.13
        bx('rejah', a0, a1, (z0 + z1) / 2 - 0.012, (z0 + z1) / 2 + 0.012, 0.07, 0.1, 'hierro')


def puerta(K, cara, a0, a1, z0, z1, plano, sale, m='puerta', bisagra='a0'):
    """Puerta exterior: registra el hueco, pone el marco y deja la hoja abierta hacia adentro."""
    s = sale
    K.aberturas.append((cara, plano, a0, a1, z0, z1))
    f = 0.08
    W = a1 - a0
    h0 = a0 if bisagra == 'a0' else a1 - 0.045
    if cara == 'x':
        K.B('pmarco', a0 - f, plano, z0, a0, plano + s * 0.05, z1 + f, 'marco')
        K.B('pmarco', a1, plano, z0, a1 + f, plano + s * 0.05, z1 + f, 'marco')
        K.B('pmarco', a0, plano, z1, a1, plano + s * 0.05, z1 + f, 'marco')
        K.B('puerta', h0, plano - s * 0.12, z0 + 0.02, h0 + 0.045, plano - s * (0.12 + W), z1, m)
    else:
        K.B('pmarco', plano, a0 - f, z0, plano + s * 0.05, a0, z1 + f, 'marco')
        K.B('pmarco', plano, a1, z0, plano + s * 0.05, a1 + f, z1 + f, 'marco')
        K.B('pmarco', plano, a0, z1, plano + s * 0.05, a1, z1 + f, 'marco')
        K.B('puerta', plano - s * 0.12, h0, z0 + 0.02, plano - s * (0.12 + W), h0 + 0.045, z1, m)


def obox(nm, size, off, org, ang, m, c):
    """Caja con su esquina en `off` medido en el marco de un tramo que arranca en `org` con giro `ang`."""
    x = org[0] + math.cos(ang) * off[0] - math.sin(ang) * off[1]
    y = org[1] + math.sin(ang) * off[0] + math.cos(ang) * off[1]
    return box(nm, size, (x, y, org[2] + off[2]), m, c, rot=ang)


def baranda(K, x0, y0, x1, y1, z, h=1.0, paso=0.12, m='hierro', tipo='barrotes'):
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    org = (x0, y0, z)
    M = K.M[m]
    parts = [obox(K.nm('bar_top'), (L, 0.05, 0.05), (0, -0.025, h - 0.05), org, ang, M, K.c),
             obox(K.nm('bar_bot'), (L, 0.04, 0.04), (0, -0.02, 0.08), org, ang, M, K.c)]
    if tipo == 'barrotes':
        k = paso / 2
        while k < L:
            parts.append(obox(K.nm('bar'), (0.02, 0.02, h - 0.1), (k - 0.01, -0.01, 0.08), org, ang, M, K.c))
            k += paso
    else:   # cruces (balcón de la torre)
        from mathutils import Matrix
        T = Matrix.Translation((x0, y0, z)) @ Matrix.Rotation(ang, 4, 'Z')
        nb = max(1, round(L / 1.2))
        for i in range(nb):
            u0 = i * L / nb; u1 = (i + 1) * L / nb
            for (a, bb) in ((u0, u1), (u1, u0)):
                dl = math.hypot(u1 - u0, h - 0.15)
                cr = box(K.nm('bar_x'), (dl, 0.025, 0.025), (0, -0.0125, 0), M, K.c, rot=0)
                cr.rotation_euler = (0, -math.atan2(h - 0.15, bb - a), 0)
                cr.location = (a, 0, 0.08)
                bpy.context.view_layer.update()
                cr.matrix_world = T @ cr.matrix_world.copy()
                parts.append(cr)
            parts.append(obox(K.nm('bar_p'), (0.05, 0.05, h), (u0 - 0.025, -0.025, 0), org, ang, M, K.c))
        parts.append(obox(K.nm('bar_p'), (0.05, 0.05, h), (L - 0.025, -0.025, 0), org, ang, M, K.c))
    o = join(parts, K.nm('baranda'))
    K.objs.append(o)
    return o


def porton(K, x0, x1, y, alto=1.9, arco=0.3, paso=0.12):
    """Portón de barrotes con remate en arco y celosía baja (vista de las fotos del frente)."""
    parts = []
    L = x1 - x0
    k = paso / 2
    while k < L:
        t = k / L
        h = alto + arco * math.sin(math.pi * t)
        parts.append(box(K.nm('pb'), (0.022, 0.022, h), (x0 + k - 0.011, y - 0.011, 0.05), K.M['hierro'], K.c))
        k += paso
    parts.append(box(K.nm('pr'), (L, 0.05, 0.06), (x0, y - 0.025, 0.05), K.M['hierro'], K.c))
    parts.append(box(K.nm('pr'), (L, 0.05, 0.05), (x0, y - 0.025, 0.55), K.M['hierro'], K.c))
    parts.append(box(K.nm('pr'), (L, 0.05, 0.05), (x0, y - 0.025, alto - 0.1), K.M['hierro'], K.c))
    # celosía baja (rombos)
    n = max(2, int(L / 0.25))
    for i in range(n):
        for sgn in (1, -1):
            d = box(K.nm('pc'), (0.36, 0.02, 0.02), (-0.18, -0.01, -0.01), K.M['hierro'], K.c)
            d.location = (x0 + (i + 0.5) * L / n, y, 0.3)
            d.rotation_euler = (0, sgn * math.radians(55), 0)
            parts.append(d)
    o = join(parts, K.nm('porton'))
    K.objs.append(o)
    return o


def colocar(K, root):
    for o in K.objs:
        if o and o.name in bpy.data.objects and o.parent is None:
            set_parent(o, root)


# ================================================================== CASA AMARILLA
def casa_amarilla(M, c, origen, ang):
    """Frente hacia la C.A (y negativa). De izquierda a derecha vista desde la calle:
    cochera adelantada con arco y medallón, torre de dos niveles con balcón, ala baja; garaje de
    piedra aparte, a la derecha, con su reja hacia la calle de tierra."""
    K = Kit(M, c, 'ca')
    root = empty('casa_root', (origen[0], origen[1], 0), ang, c)
    H = 3.0      # alero de las alas bajas
    Y = 'amarillo'
    W, D = 12.6, 13.8

    # ---- cuerpo bajo: tres alas con cubiertas distintas
    tx0, tx1 = 4.4, 10.0                                    # torre
    # (muros, pisos, losas y escalera: interiores.CASA, al final)
    K.B('zocalo', tx1, 0.86, 0, W, 0.9, 0.45, 'piedra')
    PLANTA = [(0, 0, 4.4, 13.8), (4.4, 0, 10.0, 13.8), (10.0, 0.9, 12.6, 13.8), (5.3, -0.6, 9.1, 0)]   # planta baja
    hip(K, 'techo_izq', 0.0, 0.0, tx0, D, H, 20, 0.8, 'teja', excluir=PLANTA)
    hip(K, 'techo_der', tx1, 0.9, W, D, H, 20, 0.8, 'teja', excluir=PLANTA)

    # ---- cochera adelantada: arco al frente, medallón, arcos laterales (pasa el carro)
    cx0, cx1, cy0, cy1 = -1.0, 3.9, -5.6, 0.0
    HC = 4.0
    arco_muro(K, 'coch_frente', cx0, cx1, cy0 + 0.15, 0.3, 0, HC, 3.6, 2.5, Y, eje='x')
    for xx, nom in ((cx0 + 0.15, 'izq'), (cx1 - 0.15, 'der')):
        arco_muro(K, 'coch_lado_' + nom, cy0 + 0.3, cy1, xx, 0.3, 0, HC, 3.4, 2.2, Y, eje='y', centro=cy0 + 0.3 + 2.3)
    for xx in (cx0 - 0.05, cx1 - 0.45):                     # columnas blancas al frente
        K.B('coch_col', xx, cy0 - 0.12, 0, xx + 0.5, cy0 + 0.38, 2.7, 'blanco')
        K.B('coch_cap', xx - 0.06, cy0 - 0.18, 2.7, xx + 0.56, cy0 + 0.44, 2.85, 'blanco')
    med = K.cyl('medallon', 0, 0, 0, 0.5, 0.1, 'blanco', segs=32)
    med.rotation_euler = (math.pi / 2, 0, 0); med.location = ((cx0 + cx1) / 2, cy0 - 0.05, 3.45)
    K.B('coch_piso', cx0, cy0, 0, cx1, cy1, 0.04, 'ceramica')
    hip(K, 'coch_techo', cx0, cy0, cx1, cy1, HC, 24, 0.6, 'teja', excluir=PLANTA)
    # porche entre la cochera y la torre (el arco lateral que se ve a la derecha de la cochera)
    K.B('porche_losa', cx1, -2.4, H - 0.25, tx0, 0.0, H, 'blanco')
    K.B('porche_col', tx0 - 0.4, -2.4, 0, tx0, -2.0, H - 0.25, 'blanco')

    # ---- torre de dos niveles con balcón frontal
    ventana(K, 'x', 5.9, 8.5, 0.9, 2.3, -0.6, -1, rejas=True)          # saliente con ventanal
    ventana(K, 'x', 4.6, 5.1, 1.0, 2.3, 0.0, -1, rejas=False)
    puerta(K, 'x', 9.2, 9.95, 0.0, 2.2, 0.0, -1)                        # entrada principal (recepción)
    K.B('balcon_losa', tx0, -0.7, H - 0.1, tx1, 0.0, H + 0.15, 'blanco')
    K.B('balcon_losa', tx0, 0.0, H + 0.002, tx1, 1.4, H + 0.15, 'blanco')      # sobre los cuartos: no baja del cielo raso
    K.B('balcon_canto', tx0, -0.75, H - 0.3, tx1, -0.6, H + 0.15, 'blanco')
    baranda(K, tx0 + 0.05, -0.65, tx1 - 0.05, -0.65, H + 0.15, h=1.05, tipo='cruces')
    baranda(K, tx0 + 0.05, -0.65, tx0 + 0.05, 1.4, H + 0.15, h=1.05, tipo='cruces')
    baranda(K, tx1 - 0.05, -0.65, tx1 - 0.05, 1.4, H + 0.15, h=1.05, tipo='cruces')
    for xx in (5.95, 8.45):                                             # dos columnas redondas al alero
        K.cyl('col_balcon', xx, -0.45, H + 0.15, 0.16, 6.2 - H - 0.15, 'blanco')
    puerta(K, 'x', 6.5, 7.9, H + 0.15, H + 2.45, 1.4, -1, m='blanco')
    ventana(K, 'x', 5.3, 6.0, H + 0.85, H + 2.0, 1.4, -1, rejas=False, arco=True)
    ventana(K, 'x', 8.4, 9.1, H + 0.85, H + 2.0, 1.4, -1, rejas=False, arco=True)
    # alero ancho con esquinas frontales ochavadas (como en la foto; no se supone octágono)
    hip(K, 'torre_techo', tx0 + 0.3, -0.45, tx1 - 0.3, D, 6.15, 22, 1.25, 'teja', chamfer=1.3)
    # planta alta hacia el patio: tres ventanas y balconcito en la esquina (foto del patio de grava)
    ventana(K, 'x', 7.4, 9.2, H + 1.0, H + 2.2, D, 1, rejas=False)
    ventana(K, 'x', 6.1, 6.7, H + 1.0, H + 2.2, D, 1, rejas=False)
    ventana(K, 'x', 5.0, 5.6, H + 1.0, H + 2.2, D, 1, rejas=False)
    ventana(K, 'y', 9.6, 10.4, H + 1.4, H + 2.2, tx0 + 0.3, -1, rejas=False)   # baño de la recámara alta
    K.B('balcon_tras', tx1 - 0.3, D - 2.2, H - 0.1, tx1 + 1.1, D, H + 0.12, 'blanco')
    baranda(K, tx1 + 1.1, D - 2.2, tx1 + 1.1, D, H + 0.12, h=1.0)
    baranda(K, tx1 - 0.3, D, tx1 + 1.1, D, H + 0.12, h=1.0)

    # ventanas de las alas
    ventana(K, 'x', 10.6, 12.0, 0.9, 2.3, 0.9, -1)
    ventana(K, 'x', 0.5, 1.9, 0.9, 2.3, 0.0, -1)
    for yy in (2.0, 5.5, 9.0):
        ventana(K, 'y', yy, yy + 1.4, 0.9, 2.3, W, 1)
        ventana(K, 'y', yy + 0.3, yy + 1.5, 0.9, 2.3, 0.0, -1)

    # ---- fondo (patio de grava): porche con dos columnas y balaustrada; porche en arco al sureste
    px0, px1 = 8.9, 12.0
    K.B('porche_tras_piso', px0, D, 0, px1, D + 1.8, 0.25, 'blanco')
    for xx in (px0 + 0.15, px1 - 0.43):
        K.B('porche_tras_col', xx, D + 1.4, 0.25, xx + 0.28, D + 1.68, H - 0.2, 'blanco')
    baranda(K, px0 + 0.5, D + 1.55, px1 - 0.45, D + 1.55, 0.25, h=0.85, paso=0.18, m='blanco')
    hip(K, 'porche_tras_techo', px0, D, px1, D + 1.7, H - 0.2, 18, 0.4, 'teja', excluir=PLANTA)
    puerta(K, 'x', 10.0, 11.0, 0.25, 2.35, D, 1)
    arco_muro(K, 'arco_tras', 1.2, 4.4, D + 1.6, 0.3, 0, H, 2.4, 1.9, Y, eje='x')
    K.B('arco_tras_l', 1.2, D, 0, 1.5, D + 1.6, H, Y)
    K.B('arco_tras_r', 4.1, D, 0, 4.4, D + 1.6, H, Y)
    hip(K, 'arco_tras_techo', 1.2, D, 4.4, D + 1.75, H, 18, 0.4, 'teja', excluir=PLANTA)
    ventana(K, 'x', 5.9, 7.1, 0.9, 2.3, D, 1)
    ventana(K, 'x', 3.2, 4.4, 0.9, 2.3, D, 1)
    ventana(K, 'x', 0.6, 1.8, 0.9, 2.3, D, 1)

    # ---- garaje aparte (techo rosado del satélite junto a la bifurcación), muro de piedra y reja
    gx0, gx1, gy0, gy1 = 15.9, 21.0, -1.6, 3.0
    K.B('garaje', gx0, gy0, 0, gx1, gy1, 2.8, Y)
    K.B('garaje_piedra', gx1, gy0, 0, gx1 + 0.05, gy1, 2.8, 'piedra')
    hip(K, 'garaje_techo', gx0, gy0, gx1, gy1, 2.8, 22, 0.55, 'teja')
    K.B('garaje_vano', gx1 + 0.05, gy0 + 0.5, 0.05, gx1 + 0.08, gy1 - 0.5, 2.4, 'vidrio_osc')
    k = gy0 + 0.6
    while k < gy1 - 0.5:
        K.B('garaje_reja', gx1 + 0.08, k, 0.05, gx1 + 0.11, k + 0.03, 2.4, 'hierro'); k += 0.16
    # pisos de baldosa: frente y entrada del garaje
    K.B('piso_frente', -1.6, -12.5, 0, 12.6, -0.6, 0.03, 'ceramica')
    K.B('piso_garaje', 12.6, -2.0, 0, 24.0, 3.5, 0.03, 'ceramica')
    # cerca del frente, retirada de la calle (afuera queda la rampa de baldosa), con dos portones
    YF = -7.4
    portones = [(-0.6, 2.0), (2.6, 9.4)]
    pilares = [-5.0, -2.6, -0.9, 2.3, 9.7, 12.2, 14.6]
    for a, b in zip(pilares[:-1], pilares[1:]):
        if any(abs((a + b) / 2 - (p0 + p1) / 2) < 1.0 for p0, p1 in portones):
            continue
        K.B('cerca_frente', a, YF - 0.1, 0, b, YF + 0.1, 1.5, Y)
    for xr in (-5.0, 14.6):
        K.B('cerca_retorno', xr - 0.1, YF - 4.6, 0, xr + 0.1, YF, 1.5, Y)
    for xx in pilares:
        K.B('pilar', xx - 0.22, YF - 0.22, 0, xx + 0.22, YF + 0.22, 1.95, Y)
        K.B('pilar_cap', xx - 0.28, YF - 0.28, 1.95, xx + 0.28, YF + 0.28, 2.05, 'blanco')
        K.cyl('pilar_bola', xx, YF, 2.05, 0.17, 0.32, 'blanco', segs=12, r2=0.06)
    for (p0, p1) in portones:
        porton(K, p0 + 0.05, p1 - 0.05, YF, alto=1.85, arco=0.35 if p1 - p0 > 4 else 0.2)

    import interiores
    K.interior = interiores.construir(K, interiores.CASA, Y, mat_int='pintura_casa', mat_piso='piso_casa')
    import muebles3d
    K.camas = muebles3d.amueblar(K, interiores.CASA, 'casa')
    K.root = root
    colocar(K, root)
    return K


# ================================================================== EDIFICIO GRIS
def edificio_gris(M, c, origen, ang):
    """x de norte a sur, y de oeste (calle) a este (jardín). Fachada oeste escalonada según el
    satélite: el tramo sur sobresale; el norte es el más retirado. Galería cerrada con listones en el
    lado norte; galería abierta en el lado este; escalera metálica exterior al sur."""
    K = Kit(M, c, 'gr')
    root = empty('gris_root', (origen[0], origen[1], 0), ang, c)
    G = 'gris_claro'
    Z1, Z2, ZT = 3.2, 6.35, 7.9          # entrepiso, techo, remate
    ov = 0.5
    XL, YE = 14.4, 13.5                   # borde sur y borde este del techo
    tramos = [(0.0, 4.6, 4.3), (4.6, 6.7, 1.9), (6.7, XL, 0.0)]   # (x0, x1, borde oeste del techo)
    GN = 2.0                              # fondo de la galería cerrada del norte
    GE = 2.0                              # fondo de la galería abierta del este
    YN = 10.2                             # el tramo norte se retira al este: porche cubierto en ambos niveles

    # ---- muros, pisos, losa de entrepiso y escalera interior: interiores.GRIS (al final)
    for (a0, a1, r) in tramos:
        K.B('losa_techo', a0, r, Z2 - 0.2, a1, YE, Z2, 'concreto')
        K.B('cubierta', a0, r, Z2, a1, YE, Z2 + 0.55, 'lamina_techo')
    # ---- remates altos de lámina en todo el perímetro (cajas escalonadas de las fotos)
    for (a0, a1, r) in tramos:
        K.B('remate_o', a0, r - 0.05, Z2 - 0.2, a1, r + 0.1, ZT, 'lamina')
    K.B('remate_e', 0.0, YE - 0.1, Z2 - 0.2, XL, YE + 0.05, ZT, 'lamina')
    K.B('remate_n', -0.05, tramos[0][2], Z2 - 0.2, 0.1, YE, ZT + 0.2, 'lamina')
    K.B('remate_s', XL - 0.1, 0.0, Z2 - 0.2, XL + 0.05, YE, ZT, 'lamina')
    for (xa, r0, r1) in ((4.6, 1.9, 4.3), (6.7, 0.0, 1.9)):         # retornos de cada escalón
        K.B('remate_ret', xa - 0.07, r0, Z2 - 0.2, xa + 0.07, r1 + 0.1, ZT, 'lamina')

    # ---- galería norte cerrada: losa, listones verticales, paneles decorativos
    y0n, y1n = tramos[0][2] + ov, YE - ov
    K.B('gal_n_piso', 0.15, y0n, Z1 - 0.25, ov + GN, y1n, Z1, 'concreto')
    y = y0n + 0.1
    while y < y1n - 0.05:
        K.B('liston', 0.2, y, Z1, 0.27, y + 0.05, Z2 - 0.2, 'metal_gris'); y += 0.15
    for yy in (y0n + 0.9, y0n + 3.6, y0n + 6.3):
        K.B('panel_deco', 0.17, yy, Z1 + 0.9, 0.2, yy + 0.9, Z2 - 0.9, 'hierro')
    K.B('gal_n_pasam', 0.15, y0n, Z1 + 1.0, 0.3, y1n, Z1 + 1.1, 'metal_gris')
    for yy in (y0n, (y0n + y1n) / 2, y1n - 0.15):
        K.B('gal_n_poste', 0.12, yy, Z1, 0.32, yy + 0.15, Z2 - 0.2, 'metal_gris')
    # planta baja norte: puerta y dos ventanas bajo la galería
    xpb = ov + 0.6
    puerta(K, 'y', 5.4, 6.4, 0, 2.2, xpb, -1, m='puerta_roja')
    ventana(K, 'y', 8.2, 9.4, 0.9, 2.3, xpb, -1)
    # planta alta norte: puerta de la biblioteca a la galería y ventana de la escalera
    puerta(K, 'y', 5.6, 6.5, Z1, Z1 + 2.2, ov + GN, -1)
    ventana(K, 'y', 8.3, 9.3, Z1 + 0.9, Z1 + 2.1, ov + GN, -1, rejas=False)

    # ---- fachada oeste: ventanitas de bloque de vidrio, aire acondicionado, puerta
    bloques = [(2.85, 4.8, 1.3), (5.65, 2.4, 1.3), (8.6, 0.5, 1.3), (10.3, 0.5, 1.3), (12.7, 0.5, 1.3),
               (3.55, 4.8, Z1 + 1.3), (5.65, 2.4, Z1 + 1.3), (7.55, 0.5, Z1 + 1.3), (11.15, 0.5, Z1 + 1.3)]
    for (mid, yw, zz) in bloques:
        ventana(K, 'x', mid - 0.35, mid + 0.35, zz, zz + 0.7, yw, -1, rejas=False, vidrio='bloque')
    K.B('ac', 5.2, 1.9 + ov - 0.35, Z1 + 1.6, 6.0, 1.9 + ov, Z1 + 2.15, 'blanco')
    puerta(K, 'x', 6.9, 7.9, 0, 2.2, ov, -1, m='puerta_roja')
    # estacionamientos con pintura (frente al acceso)
    for i, xx in enumerate((1.0, 3.8)):
        K.B('parqueo', xx, -1.8, 0, xx + 2.5, 3.6, 0.02, 'pintura_azul')

    # ---- galería este (terraza): postes delgados y losa volada. Según el propietario (30-10-2026) hoy
    # está cerrada con verjas de piso a techo; la foto edificio-gris.jpg es anterior y la muestra abierta.
    yE = YE - ov - GE
    K.B('gal_e_piso', 4.6, yE, Z1 - 0.25, XL - ov, YE - 0.1, Z1, 'concreto')
    for xx in (4.6, 7.7, 10.8, XL - ov - 0.15):
        K.B('gal_e_poste', xx, YE - 0.35, Z1, xx + 0.12, YE - 0.23, Z2 - 0.2, 'metal_gris')
    baranda(K, 4.6, YE - 0.3, XL - ov, YE - 0.3, Z1, h=Z2 - 0.2 - Z1, paso=0.13, m='metal_gris')
    baranda(K, 4.6, YE - 0.3, 4.6, yE, Z1, h=Z2 - 0.2 - Z1, paso=0.13, m='metal_gris')
    baranda(K, XL - ov, YE - 0.3, XL - ov, yE + 1.2, Z1, h=Z2 - 0.2 - Z1, paso=0.13, m='metal_gris')
    K.B('gal_e_travesano', 4.6, YE - 0.33, Z1 + 1.0, XL - ov, YE - 0.27, Z1 + 1.06, 'metal_gris')
    for xx in (ov + 0.05, 4.45):                                     # porche cubierto del tramo norte
        K.B('porche_n_poste', xx, YE - 0.4, 0, xx + 0.15, YE - 0.25, Z2 - 0.2, 'metal_gris')
    K.B('ac_e', 2.2, YN, Z1 + 1.4, 3.0, YN + 0.35, Z1 + 1.95, 'blanco')
    puerta(K, 'x', 7.0, 8.0, Z1, Z1 + 2.2, yE, 1)
    puerta(K, 'x', 10.5, 11.5, Z1, Z1 + 2.2, yE, 1, bisagra='a1')     # hoja hacia el pasillo central
    for xx in (9.0, 12.2):
        ventana(K, 'x', xx, xx + 1.2, Z1 + 0.9, Z1 + 2.3, yE, 1, rejas=False)
    for (a, b, zz) in ((2.0, 3.2, 0.9), (8.0, 9.2, 0.9), (10.4, 11.6, 0.9),
                       (1.6, 2.8, Z1 + 0.9), (6.0, 7.2, Z1 + 0.9), (8.6, 9.8, Z1 + 0.9)):
        ventana(K, 'y', a, b, zz, zz + 1.4, XL - ov, 1)
    for xx in (5.4, 7.4, 9.4, 11.6):
        ventana(K, 'x', xx, xx + 1.2, 0.8, 2.4, YE - ov - 0.3, 1)
    ventana(K, 'x', 1.6, 2.8, 0.8, 2.4, YN, 1)
    # ---- escalera metálica exterior al sur, sube a la galería este
    n = 17
    y_ini = 5.4
    for i in range(n):
        yy = y_ini + i * (yE + 0.6 - y_ini) / n
        K.B('esc_huella', XL + 0.05, yy, (i + 1) * Z1 / n - 0.05, XL + 1.15, yy + 0.3, (i + 1) * Z1 / n, 'hierro')
    Lz = math.hypot(yE + 0.6 - y_ini, Z1)
    for xx in (XL + 0.05, XL + 1.1):
        z = K.B('esc_zanca', xx, 0, -0.12, xx + 0.05, Lz, 0.12, 'hierro')
        z.rotation_euler = (math.atan2(Z1, yE + 0.6 - y_ini), 0, 0); z.location = (xx, y_ini, 0)
    K.B('esc_descanso', XL, yE + 0.6, Z1 - 0.12, XL + 1.2, YE - 0.1, Z1, 'hierro')
    baranda(K, XL + 1.15, y_ini + 1.5, XL + 1.15, YE - 0.1, Z1, h=1.0)

    import interiores
    K.interior = interiores.construir(K, interiores.GRIS, G, mat_int='pintura_gris', mat_piso='piso_gris')
    import muebles3d
    K.camas = muebles3d.amueblar(K, interiores.GRIS, 'gris')
    K.root = root
    colocar(K, root)
    return K
