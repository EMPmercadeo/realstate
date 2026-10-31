"""
Etapa 3 · interiores: cuartos, muros con huecos reales, losas con hueco de escalera y escaleras en U.

La distribución sale de los croquis originales (docs/croquis-*.jpg), de los esquemas de relaciones de
Codex y de las fotos interiores (carpeta drive-download-20261028…). Es INTERPRETATIVA: los rectángulos
fijan relaciones y proporciones aproximadas, no muros medidos. Los puntos dudosos están en SUPUESTOS.

Coordenadas en el marco local de cada edificio (ver fachadas.py / sitio.py), metros.
La geometría (qué muros, dónde van las puertas) se calcula aquí sin Blender para que los planos 2D
y el modelo 3D salgan de la misma fuente.
"""
import math
from shapely.geometry import box as sbox, LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, linemerge

T_EXT = 0.20      # muro exterior (hacia adentro desde la cara de fachada)
T_INT = 0.12      # tabique interior (centrado en la línea)
PUERTA_ALTO = 2.10


# ===================================================================== DATOS
# tipo: 'cerrado' (lleva muros) o 'abierto' (circulación: no levanta muros contra otros abiertos)
# conecta: ids con los que se abre una puerta interior en el muro compartido más largo
def R(*r):
    return tuple(r)


CASA = dict(
    nombre='Casa amarilla',
    niveles=[
        dict(id='pb', nombre='Planta baja', z0=0.0, z1=3.0,
             masas=[R(0, 0, 4.4, 13.8), R(4.4, 0, 10.0, 13.8), R(10.0, 0.9, 12.6, 13.8), R(5.3, -0.6, 9.1, 0)],
             cuartos=[
                 dict(id='consultorio', nombre='Consultorio de salud', rects=[R(0, 0, 3.4, 3.6)], conecta=['comedor']),
                 dict(id='cocina', nombre='Cocina', rects=[R(0, 3.6, 3.4, 7.0)], conecta=['comedor', 'pasillo']),
                 dict(id='comedor', nombre='Comedor y sala de familiares', tipo='abierto',
                      rects=[R(3.4, 0, 6.6, 7.0), R(5.3, -0.6, 6.6, 0)]),
                 dict(id='recepcion', nombre='Recepción', tipo='abierto',
                      rects=[R(6.6, -0.6, 9.1, 0), R(6.6, 0, 10.0, 0.9), R(6.6, 0.9, 9.4, 3.6)]),
                 dict(id='cuarto3', nombre='Cuarto 3', rects=[R(6.6, 3.6, 9.4, 7.0)], conecta=['pasillo']),
                 dict(id='terapia', nombre='Sala de terapia', rects=[R(9.4, 0.9, 12.6, 4.2)], conecta=['recepcion']),
                 dict(id='talleres', nombre='Talleres', rects=[R(9.4, 4.2, 12.6, 7.0)], conecta=['pasillo']),
                 dict(id='pasillo', nombre='Pasillo', tipo='abierto', rects=[R(0, 7.0, 12.6, 8.4)]),
                 dict(id='lavanderia', nombre='Lavandería', rects=[R(0, 8.4, 2.4, 13.8)], conecta=['pasillo']),
                 dict(id='cuarto1', nombre='Cuarto privado 1', rects=[R(2.4, 8.4, 5.4, 13.8)], conecta=['pasillo']),
                 dict(id='bano1', nombre='Baño', rects=[R(5.4, 8.4, 7.5, 13.8)], conecta=['pasillo']),
                 dict(id='escalera', nombre='Escalera', tipo='abierto', escalera=True, rects=[R(7.5, 8.4, 9.5, 12.0)]),
                 dict(id='bano2', nombre='Baño compartido', rects=[R(7.5, 12.0, 9.5, 13.8)], conecta=['recamara2']),
                 dict(id='recamara2', nombre='Recámara 2', rects=[R(9.5, 8.4, 12.6, 13.8)], conecta=['pasillo']),
             ]),
        dict(id='pa', nombre='Planta alta (torre)', z0=3.15, z1=6.1, losa=(3.0, 3.15),
             losa_rects=[R(4.4, 1.4, 10.0, 13.8)],
             masas=[R(4.7, 1.4, 9.7, 13.8)],
             cuartos=[
                 dict(id='gerencia', nombre='Oficina del gerente', rects=[R(4.7, 1.4, 9.7, 7.0)], conecta=['hall']),
                 dict(id='hall', nombre='Vestíbulo', tipo='abierto', rects=[R(4.7, 7.0, 9.7, 8.4)]),
                 dict(id='escalera', nombre='Escalera', tipo='abierto', escalera=True, rects=[R(7.5, 8.4, 9.5, 12.0)]),
                 dict(id='pasillo_alto', nombre='Pasillo', tipo='abierto', rects=[R(6.4, 8.4, 7.5, 12.0)]),
                 dict(id='bano_ger', nombre='Baño', rects=[R(4.7, 8.4, 6.4, 12.0)], conecta=['pasillo_alto']),
                 dict(id='sala_alta', nombre='Recámara alta (uso por definir)', rects=[R(4.7, 12.0, 9.7, 13.8)],
                      conecta=['pasillo_alto']),
             ]),
    ],
    escaleras=[dict(caja=R(7.5, 8.4, 9.5, 12.0), eje='y', inicio='min', mitad1='hi', descanso=1.0,
                    z0=0.0, z1=3.15, barandas_sup=[((8.5, 8.4), (9.5, 8.4)), ((7.5, 8.4), (7.5, 12.0))])],
    luces_extra=[],
)

GRIS = dict(
    nombre='Edificio gris',
    niveles=[
        dict(id='pb', nombre='Planta baja', z0=0.0, z1=2.95,
             masas=[R(1.1, 4.8, 4.6, 10.2), R(4.6, 2.4, 6.7, 12.7), R(6.7, 0.5, 13.9, 12.7)],
             cuartos=[
                 dict(id='recepcion', nombre='Acceso y recepción', tipo='abierto', rects=[R(6.7, 0.5, 9.1, 4.8)]),
                 dict(id='bano_acc', nombre='Baño accesible', rects=[R(4.6, 2.4, 6.7, 4.8)], conecta=['pasillo']),
                 dict(id='oficina1', nombre='Oficina 1 · administración', rects=[R(9.1, 0.5, 11.5, 4.8)], conecta=['pasillo']),
                 dict(id='oficina2', nombre='Oficina 2 · supervisor', rects=[R(11.5, 0.5, 13.9, 4.8)], conecta=['pasillo']),
                 dict(id='pasillo', nombre='Pasillo', tipo='abierto', rects=[R(1.1, 4.8, 9.1, 7.4), R(9.1, 4.8, 13.9, 6.2)]),
                 dict(id='escalera', nombre='Escalera', tipo='abierto', escalera=True, rects=[R(2.7, 7.4, 6.7, 9.8)]),
                 dict(id='estar', nombre='Estar y espera', tipo='abierto', rects=[R(6.7, 7.4, 9.1, 9.8)]),
                 dict(id='salonA', nombre='Salón A · 4 camas', rects=[R(4.6, 9.8, 9.1, 12.7)], conecta=['estar']),
                 dict(id='salonB', nombre='Salón B · 6 camas', rects=[R(9.1, 6.2, 13.9, 12.7)], conecta=['pasillo']),
                 dict(id='deposito', nombre='Depósito', rects=[R(1.1, 7.4, 2.7, 10.2), R(2.7, 9.8, 4.6, 10.2)], conecta=['pasillo']),
             ]),
        dict(id='pa', nombre='Planta alta', z0=3.2, z1=6.15, losa=(2.95, 3.2),
             # la losa cubre la planta alta; las franjas de planta baja fuera de ella quedan bajo las
             # losas de las galerías (fachadas.py), sin caras coplanares
             losa_rects=[R(2.5, 4.8, 4.6, 10.2), R(4.6, 2.4, 6.7, 11.0), R(6.7, 0.5, 13.9, 11.0)],
             masas=[R(2.5, 4.8, 4.6, 10.2), R(4.6, 2.4, 6.7, 11.0), R(6.7, 0.5, 13.9, 11.0)],
             cuartos=[
                 dict(id='pasillo', nombre='Pasillo y estar', tipo='abierto', rects=[R(6.7, 0.5, 8.4, 11.0)]),
                 dict(id='bano', nombre='Baño con regadera', rects=[R(4.6, 2.4, 6.7, 4.8)], conecta=['pasillo']),
                 dict(id='cocina', nombre='Cocina', rects=[R(4.6, 4.8, 6.7, 7.4)], conecta=['pasillo']),
                 dict(id='biblioteca', nombre='Biblioteca → insumos', rects=[R(2.5, 4.8, 4.6, 7.4)], conecta=['cocina']),
                 dict(id='escalera', nombre='Escalera', tipo='abierto', escalera=True, rects=[R(2.7, 7.4, 6.7, 9.8)]),
                 dict(id='closet', nombre='Clóset', rects=[R(4.6, 9.8, 6.7, 11.0)], conecta=['pasillo']),
                 dict(id='salon2', nombre='Salón 2 · 4 camas', rects=[R(8.4, 0.5, 13.9, 4.2)], conecta=['pasillo']),
                 dict(id='hosp', nombre='Hospitalización · 10 camas + estación', rects=[R(8.4, 4.2, 13.9, 11.0)],
                      conecta=['pasillo']),
             ]),
    ],
    escaleras=[dict(caja=R(2.7, 7.4, 6.7, 9.8), eje='x', inicio='max', mitad1='lo', descanso=1.2,
                    z0=0.0, z1=3.2, barandas_sup=[((6.7, 7.4), (6.7, 8.6))])],
)

SUPUESTOS = [
    'Distribución interpretada de los croquis manuscritos; no es un levantamiento ni fija muros reales.',
    'Casa amarilla: el croquis se leyó con el frente (cochera) abajo y el jardín arriba, sin espejar.',
    'Casa amarilla: recepción y comedor quedaron abiertos entre sí; la puerta principal entra por la torre.',
    'Casa amarilla: la escalera interior (en U, como en la foto de paredes verdes) se ubicó en la torre, '
    'junto al pasillo; su posición exacta no aparece en el croquis.',
    'Casa amarilla: el croquis pone la terraza atrás a la derecha; la foto del patio muestra el porche en '
    'arco atrás a la izquierda. Se dejó el porche como en la foto.',
    'Casa amarilla, planta alta: oficina del gerente al frente (balcón), baño y una recámara alta atrás.',
    'Edificio gris: escalera interior en U al norte, junto a la salida; la escalera metálica exterior sigue al sur.',
    'Edificio gris: se respetó la terraza al este (hoy cerrada con verjas). Salones y hospitalización quedan '
    'hacia el jardín; baños, cocina y oficinas hacia la calle (ventanas de bloque de vidrio).',
    'Capacidad: Salón A 4 + Salón B 6 + Salón 2 4 + Hospitalización 10 = 24 camas en el gris; la casa '
    'suma 3–4 cuartos. Pendiente de confirmar (28 vs 26). Al colocar camas de 0,95 × 2,0 m con paso libre en '
    'puertas y un pasillo de ~0,9 m entre camas enfrentadas, con estas medidas estimadas caben: Salón A 2 de 4, '
    'Salón B 4 de 6, Salón 2 3 de 4 y Hospitalización 7 de 10 (16 de 24). Hay que medir en sitio antes de '
    'ofrecer una capacidad.',
    'Biblioteca: se dejó como insumos (croquis), con puerta a la cocina y a la galería norte; el uso como '
    'lectura queda pendiente.',
    'Edificio gris, planta alta: un eje de circulación de la calle a la terraza reparte cocina, baño, '
    'Salón 2 y Hospitalización; la escalera llega a ese eje.',
    'No hay ascensor ni rampa entre niveles: la conexión accesible para encamados sigue sin definir.',
]


# ===================================================================== GEOMETRÍA (sin Blender)
def poly_cuarto(c):
    return unary_union([sbox(*r) for r in c['rects']])


def exterior(nivel):
    return orient(unary_union([sbox(*r) for r in nivel['masas']]).simplify(0.001), 1.0)


def _segmentos(geom):
    """LineString(s) -> lista de segmentos ((x0,y0),(x1,y1)) ortogonales."""
    out = []
    if geom.is_empty:
        return out
    if geom.geom_type in ('MultiLineString', 'GeometryCollection'):
        parts = [g for g in geom.geoms if g.geom_type in ('LineString', 'MultiLineString')]
        geom = linemerge(unary_union(parts)) if parts else None
        if geom is None or geom.is_empty:
            return out
    lines = geom.geoms if geom.geom_type == 'MultiLineString' else [geom]
    for ln in lines:
        cs = list(ln.coords)
        for a, b in zip(cs[:-1], cs[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.05:
                out.append((a, b))
    return out


def muros_exteriores(nivel, aberturas):
    """Cada arista del contorno -> muro hacia adentro con sus huecos (ventanas/puertas registradas)."""
    ext = exterior(nivel)
    cs = list(ext.exterior.coords)[:-1]
    n = len(cs)
    out = []
    for i in range(n):
        a, b = cs[i], cs[(i + 1) % n]
        prev, nxt = cs[i - 1], cs[(i + 2) % n]
        d = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*d)
        if L < 0.05:
            continue
        horizontal = abs(d[1]) < 1e-6
        if not horizontal and abs(d[0]) > 1e-6:
            continue                     # solo aristas ortogonales
        nrm = (-d[1] / L, d[0] / L)       # izquierda = adentro (anillo antihorario)
        # vértices reflejos: prolongar el muro para cerrar la esquina
        def giro(p, q, r):
            return (q[0] - p[0]) * (r[1] - q[1]) - (q[1] - p[1]) * (r[0] - q[0])
        ext0 = T_EXT if giro(prev, a, b) < 0 else 0.0
        ext1 = T_EXT if giro(a, b, nxt) < 0 else 0.0
        if horizontal:
            u0, u1 = sorted((a[0], b[0]))
            if a[0] < b[0]:
                u0 -= ext0; u1 += ext1
            else:
                u0 -= ext1; u1 += ext0
            plano = a[1]
            huecos = [(h[2], h[3], h[4], h[5]) for h in aberturas if h[0] == 'x' and abs(h[1] - plano) < 0.04
                      and h[3] > u0 and h[2] < u1 and h[5] > nivel['z0'] + 0.05 and h[4] < nivel['z1'] - 0.05]
            out.append(dict(eje='x', c0=plano, c1=plano + nrm[1] * T_EXT, u0=u0, u1=u1, huecos=huecos, ext=True))
        else:
            u0, u1 = sorted((a[1], b[1]))
            if a[1] < b[1]:
                u0 -= ext0; u1 += ext1
            else:
                u0 -= ext1; u1 += ext0
            plano = a[0]
            huecos = [(h[2], h[3], h[4], h[5]) for h in aberturas if h[0] == 'y' and abs(h[1] - plano) < 0.04
                      and h[3] > u0 and h[2] < u1 and h[5] > nivel['z0'] + 0.05 and h[4] < nivel['z1'] - 0.05]
            out.append(dict(eje='y', c0=plano, c1=plano + nrm[0] * T_EXT, u0=u0, u1=u1, huecos=huecos, ext=True))
    return out


def muros_interiores(nivel):
    """Muros entre cuartos (no entre dos abiertos) y puertas en el muro compartido más largo."""
    cuartos = nivel['cuartos']
    polys = {c['id']: poly_cuarto(c) for c in cuartos}
    tipos = {c['id']: c.get('tipo', 'cerrado') for c in cuartos}
    enlaces = set()
    for c in cuartos:
        for o in c.get('conecta', []):
            enlaces.add(frozenset((c['id'], o)))
    out, puertas = [], []
    ids = [c['id'] for c in cuartos]
    for i, A in enumerate(ids):
        for B in ids[i + 1:]:
            if tipos[A] == 'abierto' and tipos[B] == 'abierto':
                continue
            comp = polys[A].boundary.intersection(polys[B].boundary)
            segs = _segmentos(comp)
            if not segs:
                continue
            huecos_por_seg = {k: [] for k in range(len(segs))}
            if frozenset((A, B)) in enlaces:
                k = max(range(len(segs)), key=lambda j: math.hypot(segs[j][1][0] - segs[j][0][0], segs[j][1][1] - segs[j][0][1]))
                (a, b) = segs[k]
                horiz = abs(a[1] - b[1]) < 1e-6
                lo, hi = (sorted((a[0], b[0])) if horiz else sorted((a[1], b[1])))
                ancho = 1.2 if any(t in (A + B) for t in ('salon', 'hosp', 'comedor', 'recepcion', 'terapia')) else 0.9
                ancho = min(ancho, hi - lo - 0.3)
                if ancho > 0.6:
                    m = (lo + hi) / 2
                    huecos_por_seg[k].append((m - ancho / 2, m + ancho / 2, nivel['z0'], nivel['z0'] + PUERTA_ALTO))
                    puertas.append(dict(eje='x' if horiz else 'y', c=a[1] if horiz else a[0], u0=m - ancho / 2,
                                        u1=m + ancho / 2, entre=(A, B)))
            for k, (a, b) in enumerate(segs):
                horiz = abs(a[1] - b[1]) < 1e-6
                if horiz:
                    u0, u1 = sorted((a[0], b[0])); c = a[1]
                    out.append(dict(eje='x', c0=c - T_INT / 2, c1=c + T_INT / 2, u0=u0, u1=u1, huecos=huecos_por_seg[k], ext=False))
                else:
                    u0, u1 = sorted((a[1], b[1])); c = a[0]
                    out.append(dict(eje='y', c0=c - T_INT / 2, c1=c + T_INT / 2, u0=u0, u1=u1, huecos=huecos_por_seg[k], ext=False))
    return out, puertas


def piezas_muro(m, z0, z1):
    """Muro con huecos -> lista de cajas (u0,u1,za,zb) en coordenadas del muro."""
    hs = sorted((max(h[0], m['u0']), min(h[1], m['u1']), max(h[2], z0), min(h[3], z1)) for h in m['huecos'])
    out = []
    cur = m['u0']
    for (a, b, za, zb) in hs:
        if b - a < 0.05:
            continue
        if a > cur + 0.01:
            out.append((cur, a, z0, z1))
        if za > z0 + 0.01:
            out.append((a, b, z0, za))
        if zb < z1 - 0.01:
            out.append((a, b, zb, z1))
        cur = max(cur, b)
    if m['u1'] > cur + 0.01:
        out.append((cur, m['u1'], z0, z1))
    return out


def celdas(poly):
    """Descompone un polígono ortogonal (con huecos) en rectángulos por franjas."""
    if poly.is_empty:
        return []
    xs, ys = set(), set()
    geoms = poly.geoms if poly.geom_type == 'MultiPolygon' else [poly]
    for g in geoms:
        for ring in [g.exterior] + list(g.interiors):
            for x, y in ring.coords:
                xs.add(round(x, 4)); ys.add(round(y, 4))
    xs, ys = sorted(xs), sorted(ys)
    out = []
    for j in range(len(ys) - 1):
        run = None
        for i in range(len(xs) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if poly.contains(Point(cx, cy)):
                if run is None:
                    run = [xs[i], ys[j], xs[i + 1], ys[j + 1]]
                else:
                    run[2] = xs[i + 1]
            elif run is not None:
                out.append(tuple(run)); run = None
        if run is not None:
            out.append(tuple(run))
    return out


def piso(nivel, E):
    """Piso terminado del nivel: contorno menos el hueco de la escalera que llega a este nivel."""
    p = exterior(nivel)
    for esc in E['escaleras']:
        if abs(esc['z1'] - nivel['z0']) < 0.06:
            p = p.difference(sbox(*esc['caja']))
    return celdas(p)


def losa(nivel, E):
    rects = nivel.get('losa_rects')
    if not rects:
        return []
    p = unary_union([sbox(*r) for r in rects])
    for esc in E['escaleras']:
        if abs(esc['z1'] - nivel['z0']) < 0.06:
            p = p.difference(sbox(*esc['caja']))
    return celdas(p)


def tramos_escalera(esc):
    """Escalones macizos, descanso y datos de barandas de una escalera en U."""
    x0, y0, x1, y1 = esc['caja']
    eje = esc['eje']
    Hn = esc['z1'] - esc['z0']
    n = max(2, round(Hn / 0.175 / 2))     # contrahuellas por tramo
    sube = Hn / (2 * n)
    if eje == 'y':
        a0, a1, b0, b1 = y0, y1, x0, x1
    else:
        a0, a1, b0, b1 = x0, x1, y0, y1
    gap = 0.1
    bm = (b0 + b1) / 2
    lo, hi = (b0, bm - gap / 2), (bm + gap / 2, b1)
    m1, m2 = (hi, lo) if esc['mitad1'] == 'hi' else (lo, hi)
    D = esc['descanso']
    if esc['inicio'] == 'min':
        f_ini, f_fin, d_lo, d_hi = a0 + 0.05, a1 - D, a1 - D, a1
    else:
        f_ini, f_fin, d_lo, d_hi = a1 - 0.05, a0 + D, a0, a0 + D
    run = (f_fin - f_ini) / (n - 1)
    cajas = []
    # tramo 1: de f_ini hacia el descanso
    for i in range(n - 1):
        u0, u1 = sorted((f_ini + i * run, f_ini + (i + 1) * run))
        cajas.append((u0, u1, m1[0], m1[1], esc['z0'], esc['z0'] + (i + 1) * sube))
    zd = esc['z0'] + n * sube
    cajas.append((d_lo, d_hi, b0, b1, esc['z0'], zd))
    # tramo 2: del descanso de vuelta hacia f_ini
    borde = a0 if esc['inicio'] == 'min' else a1
    for i in range(n - 1):
        ua, ub = f_fin - i * run, f_fin - (i + 1) * run
        if i == n - 2:
            ub = borde                     # el último escalón llega al borde de la losa (sin rendija)
        u0, u1 = sorted((ua, ub))
        cajas.append((u0, u1, m2[0], m2[1], esc['z0'], zd + (i + 1) * sube))
    # barandas inclinadas sobre el borde interior de cada tramo
    bi1 = m1[0] if m1[0] > b0 + 0.01 else m1[1]
    bi2 = m2[0] if m2[0] > b0 + 0.01 else m2[1]
    barandas = [((f_ini, bi1, esc['z0']), (f_fin, bi1, zd)), ((f_fin, bi2, zd), (f_ini, bi2, esc['z1']))]

    def xy(u, v):
        return (v, u) if eje == 'y' else (u, v)
    cajas_xy = []
    for (u0, u1, v0, v1, za, zb) in cajas:
        (X0, Y0), (X1, Y1) = xy(u0, v0), xy(u1, v1)
        cajas_xy.append((min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1), za, zb))
    bar_xy = [(xy(p[0], p[1]) + (p[2],), xy(q[0], q[1]) + (q[2],)) for p, q in barandas]
    # eje de la línea de marcha (para la prueba de recorrido)
    c1, c2 = (m1[0] + m1[1]) / 2, (m2[0] + m2[1]) / 2
    dm = (d_lo + d_hi) / 2
    marcha = [xy(f_ini - (0.6 if esc['inicio'] == 'min' else -0.6), c1), xy(f_ini, c1), xy(f_fin, c1), xy(dm, c1), xy(dm, c2),
              xy(f_fin, c2), xy(f_ini, c2), xy(f_ini + (-0.6 if esc['inicio'] == 'min' else 0.6), c2)]
    return dict(cajas=cajas_xy, barandas=bar_xy, n=n, sube=sube, huella=abs(run), marcha=marcha)


# ===================================================================== CONSTRUCCIÓN (Blender)
def construir(K, E, mat_ext, mat_int='muro_int', mat_piso='piso_int', mat_losa='concreto'):
    """Levanta muros, pisos, losas, escaleras, barandas y luces de un edificio dentro del Kit K."""
    import bpy
    from fachadas import baranda
    res = dict(muros=[], puertas=[])
    for nv in E['niveles']:
        z0, z1 = nv['z0'], nv['z1']
        # piso terminado sobre el contorno del nivel
        for (a, b, c, d) in piso(nv, E):
            K.B(f'piso_{nv["id"]}', a, b, z0, c, d, z0 + 0.02, mat_piso)
        for (a, b, c, d) in losa(nv, E):
            K.B(f'losa_{nv["id"]}', a, b, nv['losa'][0], c, d, nv['losa'][1], mat_losa)
        mext = muros_exteriores(nv, K.aberturas)
        mint, puertas = muros_interiores(nv)
        for m in mext + mint:
            mm = mat_ext if m['ext'] else mat_int
            for (u0, u1, za, zb) in piezas_muro(m, z0, z1 - 0.004):     # sin tocar la losa (caras coplanares)
                c0, c1 = sorted((m['c0'], m['c1']))
                if m['eje'] == 'x':
                    K.B('muro', u0, c0, za, u1, c1, zb, mm)
                else:
                    K.B('muro', c0, u0, za, c1, u1, zb, mm)
        for p in puertas:   # marcos de puertas interiores
            c0, c1 = p['c'] - T_INT / 2 - 0.02, p['c'] + T_INT / 2 + 0.02
            # el marco entra 3-4 cm en el vano para no compartir caras con el muro (evita manchas negras)
            for (u0, u1, za, zb) in ((p['u0'] - 0.03, p['u0'] + 0.03, z0 + 0.021, z0 + PUERTA_ALTO - 0.01),
                                     (p['u1'] - 0.03, p['u1'] + 0.03, z0 + 0.021, z0 + PUERTA_ALTO - 0.01),
                                     (p['u0'] - 0.03, p['u1'] + 0.03, z0 + PUERTA_ALTO - 0.04, z0 + PUERTA_ALTO - 0.01)):
                if p['eje'] == 'x':
                    K.B('pmarco_int', u0, c0, za, u1, c1, zb, 'marco')
                else:
                    K.B('pmarco_int', c0, u0, za, c1, u1, zb, 'marco')
        res['muros'].append(dict(nivel=nv['id'], ext=mext, int=mint, puertas=puertas))
    # escaleras
    for esc in E['escaleras']:
        t = tramos_escalera(esc)
        for (a, b, c, d, za, zb) in t['cajas']:
            K.B('escalon', a, b, za, c, d, zb, 'escalon')
        for (p, q) in t['barandas']:
            baranda_inclinada(K, p, q)
        for (p, q) in esc.get('barandas_sup', []):
            baranda(K, p[0], p[1], q[0], q[1], esc['z1'], h=1.0, paso=0.12)
        res['escalera'] = t
    return res


def baranda_inclinada(K, p, q, h=0.95, paso=0.3):
    """Pasamanos inclinado con balaustres (escaleras)."""
    import bpy
    from lib import box
    L2 = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(2, int(L2 / paso))
    for i in range(n + 1):
        t = i / n
        x, y, z = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] + (q[2] - p[2]) * t
        K.B('balaustre', x - 0.012, y - 0.012, z, x + 0.012, y + 0.012, z + h, 'hierro')
    L3 = math.dist(p, q)
    o = box(K.nm('pasamanos'), (L3, 0.04, 0.04), (0, -0.02, -0.02), K.M['hierro'], K.c)
    ang_z = math.atan2(q[1] - p[1], q[0] - p[0])
    ang_y = -math.atan2(q[2] - p[2], L2)
    o.rotation_euler = (0, ang_y, ang_z)
    o.location = (p[0], p[1], p[2] + h)
    K.objs.append(o)


def luces(K, E, coleccion, potencia_m2=18.0):
    """Una luz de área por cuarto cerrado o abierto, pegada al cielo raso (solo para vistas interiores)."""
    import bpy
    out = []
    for nv in E['niveles']:
        for c in nv['cuartos']:
            p = poly_cuarto(c)
            a, b, cc, d = p.bounds
            area = p.area
            ld = bpy.data.lights.new(f'{K.pfx}_luz_{nv["id"]}_{c["id"]}', 'AREA')
            ld.shape = 'RECTANGLE'
            ld.size = max(0.3, (cc - a) * 0.6); ld.size_y = max(0.3, (d - b) * 0.6)
            ld.energy = potencia_m2 * area
            ld.color = (1.0, 0.95, 0.88)
            o = bpy.data.objects.new(ld.name, ld)
            coleccion.objects.link(o)
            o.location = ((a + cc) / 2, (b + d) / 2, nv['z1'] - 0.25)
            out.append(o)
    return out


# ===================================================================== MOBILIARIO DE REFERENCIA
# Bloques neutros para dar escala y leer el uso de cada cuarto. No es el amueblado final.
def _puertas_de(cid, puertas_nivel, exteriores, rect, z0=0.0):
    """Tramos (eje, c, u0, u1) de puertas que tocan el cuarto (interiores y exteriores)."""
    out = []
    for p in puertas_nivel:
        if cid in p['entre']:
            out.append((p['eje'], p['c'], p['u0'], p['u1']))
    x0, y0, x1, y1 = rect
    for (cara, plano, a0, a1, za, zb) in exteriores:
        if not (abs(za - z0) < 0.35 and zb > z0 + 1.6):     # solo puertas de este nivel (no ventanas)
            continue
        if cara == 'x' and (abs(plano - y0) < 0.05 or abs(plano - y1) < 0.05) and a1 > x0 and a0 < x1:
            out.append(('x', plano, a0, a1))
        if cara == 'y' and (abs(plano - x0) < 0.05 or abs(plano - x1) < 0.05) and a1 > y0 and a0 < y1:
            out.append(('y', plano, a0, a1))
    return out


def _libre(caja, puertas, margen=0.9):
    """True si la caja (x0,y0,x1,y1) no invade la zona de barrido de ninguna puerta."""
    x0, y0, x1, y1 = caja
    for (eje, c, u0, u1) in puertas:
        if eje == 'x':
            z = (u0 - 0.15, c - margen, u1 + 0.15, c + margen)
        else:
            z = (c - margen, u0 - 0.15, c + margen, u1 + 0.15)
        if x0 < z[2] and x1 > z[0] and y0 < z[3] and y1 > z[1]:
            return False
    return True


def muebles(K, E):
    """Camas, mesas, escritorios y mostradores según el nombre de cada cuarto."""
    import re
    cuenta = {}
    K.muebles = []
    for nv, mu in zip(E['niveles'], K.interior['muros']):
        z = nv['z0'] + 0.02
        K._nivel = nv['id']
        for c in nv['cuartos']:
            if c.get('escalera'):
                continue
            r = max(c['rects'], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = r[0] + 0.15, r[1] + 0.15, r[2] - 0.15, r[3] - 0.15
            pu = _puertas_de(c['id'], mu['puertas'], K.aberturas, r, nv['z0'])
            cid = c['id']
            m = re.search(r'(\d+)\s*camas', c['nombre'])
            puestas = 0
            if m:                                   # sala de camas: cabecera contra los muros largos
                n = int(m.group(1))
                largo_x = (x1 - x0) >= (y1 - y0)
                L0, L1 = (x0, x1) if largo_x else (y0, y1)
                lados = [(y0, 1), (y1, -1)] if largo_x else [(x0, 1), (x1, -1)]
                paso = 1.25
                ocupado = []
                def choca(cj, mg=0.45):
                    # pasillo de ~0,9 m entre pies de camas enfrentadas; de lado basta con no tocarse
                    mx, my = (0.02, mg) if largo_x else (mg, 0.02)
                    return any(cj[0] < o[2] + mx and cj[2] > o[0] - mx and cj[1] < o[3] + my and cj[3] > o[1] - my
                               for o in ocupado)
                for (borde, sgn) in lados:
                    u = L0 + 0.2
                    while u + 0.95 <= L1 and puestas < n:
                        if largo_x:
                            caja = (u, min(borde, borde + sgn * 2.05), u + 0.95, max(borde, borde + sgn * 2.05))
                        else:
                            caja = (min(borde, borde + sgn * 2.05), u, max(borde, borde + sgn * 2.05), u + 0.95)
                        if _libre(caja, pu) and not choca(caja):
                            cama(K, caja, z, largo_x, sgn)
                            ocupado.append(caja)
                            puestas += 1
                        u += paso
                if 'estación' in c['nombre'] or 'estacion' in c['nombre']:
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    est = (cx - 0.35, cy - 1.0, cx + 0.35, cy + 1.0) if not largo_x else (cx - 1.0, cy - 0.35, cx + 1.0, cy + 0.35)
                    if not choca(est, 0.6):
                        K.B('estacion', est[0], est[1], z, est[2], est[3], z + 1.0, 'mueble')
                        K.muebles.append((nv['id'], 'estacion') + tuple(est))
                cuenta[c['nombre']] = (n, puestas)
            elif cid.startswith(('cuarto', 'recamara', 'sala_alta')):
                w, l = 1.4, 2.0
                for cand in ((x0, y1 - l, x0 + w, y1), (x1 - w, y1 - l, x1, y1), (x0, y0, x0 + w, y0 + l), (x1 - w, y0, x1, y0 + l)):
                    if _libre(cand, pu):
                        cama(K, cand, z, False, -1 if cand[3] == y1 else 1, ancho=w)
                        break
            elif cid in ('comedor',):
                cx, cy = (x0 + x1) / 2 - 0.2, (y0 + y1) / 2 + 0.6
                mesa(K, cx - 0.5, cy - 1.2, cx + 0.5, cy + 1.2, z, sillas=8)
            elif cid in ('gerencia', 'oficina1', 'oficina2', 'consultorio'):
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                for dx, dy in ((0, 0), (0, 0.8), (0, -0.8), (0.8, 0), (-0.8, 0)):
                    caja = (cx + dx - 0.8, cy + dy - 0.35, cx + dx + 0.8, cy + dy + 0.35)
                    if _libre(caja, pu, 1.0):
                        mesa(K, *caja, z, sillas=2)
                        break
            elif cid == 'recepcion':
                cx = (x0 + x1) / 2
                caja = (cx - 1.0, y0 + 0.6, cx + 1.0, y0 + 1.2) if E is GRIS else (x0 + 0.4, y1 - 1.0, x0 + 2.2, y1 - 0.4)
                if _libre(caja, pu, 1.0):
                    K.B('mostrador', *caja[:2], z, *caja[2:], z + 1.05, 'mueble')
            elif cid in ('terapia', 'talleres', 'biblioteca'):
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                mesa(K, cx - 0.9, cy - 0.45, cx + 0.9, cy + 0.45, z, sillas=4 if cid != 'biblioteca' else 2)
            elif cid == 'cocina':
                for caja in ((x0, y0, x1, y0 + 0.6), (x0, y0, x0 + 0.6, y1)):
                    if _libre(caja, pu, 1.0):
                        K.B('mueble_cocina', *caja[:2], z, *caja[2:], z + 0.9, 'mueble')
                        break
            elif cid.startswith('bano'):
                for caja in ((x0, y1 - 0.7, x0 + 0.45, y1), (x1 - 0.45, y1 - 0.7, x1, y1), (x0, y0, x0 + 0.45, y0 + 0.7)):
                    if _libre(caja, pu, 0.8):
                        K.B('inodoro', *caja[:2], z, *caja[2:], z + 0.42, 'loza')
                        break
    return cuenta


def cama(K, caja, z, largo_x, sgn, ancho=0.95):
    x0, y0, x1, y1 = caja
    K.muebles.append((getattr(K, '_nivel', ''), 'cama', x0, y0, x1, y1))
    K.B('cama_base', x0, y0, z, x1, y1, z + 0.45, 'mueble')
    K.B('colchon', x0 + 0.03, y0 + 0.03, z + 0.45, x1 - 0.03, y1 - 0.03, z + 0.6, 'colchon')
    # cabecera contra el muro (lado del borde)
    if largo_x:
        yb = y0 if sgn > 0 else y1 - 0.06
        K.B('cabecera', x0, yb, z, x1, yb + 0.06, z + 1.0, 'mueble')
    else:
        if abs(x1 - x0) < abs(y1 - y0):            # cama orientada en y (cuartos)
            yb = y0 if sgn > 0 else y1 - 0.06
            K.B('cabecera', x0, yb, z, x1, yb + 0.06, z + 1.0, 'mueble')
        else:
            xb = x0 if sgn > 0 else x1 - 0.06
            K.B('cabecera', xb, y0, z, xb + 0.06, y1, z + 1.0, 'mueble')


def mesa(K, x0, y0, x1, y1, z, sillas=0):
    K.muebles.append((getattr(K, '_nivel', ''), 'mesa', x0, y0, x1, y1))
    K.B('mesa', x0, y0, z + 0.72, x1, y1, z + 0.76, 'mueble')
    for (px, py) in ((x0 + 0.05, y0 + 0.05), (x1 - 0.1, y0 + 0.05), (x0 + 0.05, y1 - 0.1), (x1 - 0.1, y1 - 0.1)):
        K.B('pata', px, py, z, px + 0.05, py + 0.05, z + 0.72, 'mueble')
    larga_x = (x1 - x0) >= (y1 - y0)
    n = sillas // 2
    for i in range(n):
        t = (i + 0.5) / n
        if larga_x:
            u = x0 + (x1 - x0) * t
            for yy in (y0 - 0.55, y1 + 0.1):
                K.B('silla', u - 0.22, yy, z, u + 0.22, yy + 0.45, z + 0.46, 'mueble2')
        else:
            u = y0 + (y1 - y0) * t
            for xx in (x0 - 0.55, x1 + 0.1):
                K.B('silla', xx, u - 0.22, z, xx + 0.45, u + 0.22, z + 0.46, 'mueble2')
