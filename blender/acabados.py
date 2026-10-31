"""
Etapa 4a · acabados interiores: revestimientos y zócalos, guardacamillas, cielos rasos, lámparas y
abanicos de techo, aires acondicionados, cuadros, cortinas y hojas de puertas interiores.

La geometría de cada cuarto (cara interior de los muros, huecos de puertas y ventanas) sale de
interiores.py; así los acabados siguen a los muros si cambia la distribución.
"""
import math, random
from shapely.geometry import box as sbox, Point, LineString
from shapely.ops import unary_union
import interiores as I
from muebles3d import Malla, R

# ------------------------------------------------------------------ configuración por edificio y cuarto
EDIF = {
    'casa': dict(piso='piso_casa', cielo='cielo', zocalo='piso_casa', cielo_h=None, lampara='plafon',
                 puerta='madera_media', marco='madera_media'),
    'gris': dict(piso='piso_gris', cielo='cielo_reticula', zocalo='piso_gris', cielo_h=2.75, lampara='domo',
                 puerta='metal_cafe', marco='metal_cafe'),
}
REVEST = {   # bandas sobre la cara interior de los muros: (material, z desde, z hasta | None = hasta el cielo)
    ('casa', 'pb', 'bano1'): [('azulejo_beige', 0.0, 2.10)],
    ('casa', 'pb', 'bano2'): [('azulejo_beige', 0.0, 2.10)],
    ('casa', 'pa', 'bano_rec'): [('azulejo_beige', 0.0, 2.10)],
    ('casa', 'pb', 'cocina'): [('azulejo_metro', 0.0, 1.60)],
    ('casa', 'pb', 'lavanderia'): [('azulejo_blanco', 0.0, 1.30)],
    ('gris', 'pb', 'bano_acc'): [('azulejo_rojo', 0.0, 1.60), ('pintura_celeste', 1.60, None)],
    ('gris', 'pa', 'bano'): [('azulejo_rojo', 0.0, 1.60), ('pintura_celeste', 1.60, None)],
    ('gris', 'pa', 'cocina'): [('azulejo_blanco', 0.0, 1.50)],
    ('gris', 'pa', 'salon2'): [('pintura_amarilla', 0.0, None)],
    ('gris', 'pb', 'salonA'): [('pintura_salvia', 0.0, 0.85)],
    ('gris', 'pb', 'salonB'): [('pintura_salvia', 0.0, 0.85)],
    ('casa', 'pb', 'terapia'): [('pintura_salvia', 0.0, None)],
}
PISO_ESP = {('casa', 'pb', 'bano1'), ('casa', 'pb', 'bano2'), ('casa', 'pa', 'bano_rec'), ('gris', 'pb', 'bano_acc'),
            ('gris', 'pa', 'bano'), ('casa', 'pb', 'lavanderia')}
GUARDA = {('gris', 'pa', 'hosp'), ('gris', 'pa', 'salon2'), ('gris', 'pb', 'salonA'), ('gris', 'pb', 'salonB'),
          ('gris', 'pa', 'pasillo'), ('gris', 'pb', 'pasillo')}
CORTINAS = {   # cuartos con cortinas en sus ventanas: material
    'casa': {'vip': 'cortina_blanca', 'suite': 'cortina_blanca', 'semipriv': 'cortina_blanca', 'comedor': 'cortina_blanca',
             'recepcion': 'cortina_blanca', 'consultorio': 'cortina_blanca', 'psicologia': 'cortina_blanca',
             'recamara': 'cortina_blanca', 'talleres': 'cortina_blanca', 'terapia': 'cortina_blanca'},
    'gris': {'hosp': 'cortina_beige', 'salon2': 'cortina_beige', 'salonA': 'cortina_blanca', 'salonB': 'cortina_blanca',
             'oficina1': 'cortina_blanca', 'oficina2': 'cortina_blanca'},
}
# abanicos de techo (con luz): (cuarto, x, y)
ABANICOS = {
    ('casa', 'pb'): [('comedor', 5.0, 2.4), ('terapia', 10.9, 2.6), ('talleres', 10.9, 5.6), ('suite', 11.0, 11.0)],
    ('casa', 'pa'): [('recamara', 7.2, 4.2)],
    ('gris', 'pb'): [('salonA', 6.85, 11.2), ('salonB', 11.4, 7.8), ('salonB', 11.4, 10.9)],
    ('gris', 'pa'): [('hosp', 11.1, 5.9), ('hosp', 11.1, 9.2), ('salon2', 11.1, 2.4)],
}
ABANICOS_GALERIA = [(6.2, 12.2), (9.4, 12.2), (12.5, 12.2)]
# aires acondicionados (split): (cuarto, lado del muro, cara, posición a lo largo)
AIRES = {
    ('casa', 'pb'): [('vip', '+y', 6.94, 7.9), ('suite', '-x', 9.56, 10.9), ('semipriv', '-x', 2.46, 12.3),
                     ('consultorio', '-y', 0.20, 2.8), ('recepcion', '+y', 3.54, 7.6)],
    ('casa', 'pa'): [('recamara', '-x', 4.90, 4.3)],
    ('gris', 'pb'): [('salonA', '-x', 4.80, 11.2), ('salonB', '-x', 9.16, 11.4), ('oficina1', '-y', 0.70, 9.7),
                     ('oficina2', '-y', 0.70, 11.9)],
    ('gris', 'pa'): [('hosp', '-y', 4.26, 8.9), ('hosp', '-y', 4.26, 12.6), ('salon2', '-y', 0.70, 9.7)],
}
# cuadros: (cuarto, lado, cara, u, z centro, ancho, alto)
CUADROS = {
    ('casa', 'pb'): [('comedor', '-x', 3.46, 5.95, 1.55, 0.9, 0.6), ('recepcion', '-x', 6.60, 0.5, 1.6, 0.5, 0.4),
                     ('recepcion', '+y', 3.54, 8.85, 1.65, 0.6, 0.45), ('vip', '+x', 9.34, 5.15, 1.55, 0.55, 0.7),
                     ('suite', '+x', 12.40, 11.0, 1.6, 0.9, 0.6), ('semipriv', '+x', 5.34, 12.3, 1.6, 0.6, 0.45),
                     ('pasillo', '-y', 7.06, 9.0, 1.55, 0.8, 0.55), ('pasillo', '+y', 8.34, 3.3, 1.55, 0.7, 0.5),
                     ('consultorio', '-x', 0.20, 1.2, 1.65, 0.45, 0.6), ('talleres', '-x', 9.46, 6.0, 1.55, 0.6, 0.45),
                     ('psicologia', '-x', 0.20, 12.9, 1.6, 0.5, 0.4)],
    ('casa', 'pa'): [('recamara', '+x', 9.50, 4.30, 1.75, 0.9, 0.6), ('hall', '-y', 7.06, 7.5, 1.6, 0.8, 0.55)],
    ('gris', 'pb'): [('salonA', '-y', 9.86, 5.8, 1.6, 0.7, 0.5), ('salonB', '+x', 13.70, 7.4, 1.6, 0.6, 0.45),
                     ('salonB', '+x', 13.70, 11.4, 1.6, 0.6, 0.45), ('estar', '+x', 9.04, 8.15, 1.6, 0.9, 0.55),
                     ('pasillo', '+y', 7.34, 4.6, 1.6, 0.8, 0.55), ('acceso', '-x', 6.76, 2.2, 1.6, 0.6, 0.8)],
    ('gris', 'pa'): [('hosp', '+x', 13.70, 7.4, 1.75, 0.55, 0.40), ('hosp', '-x', 8.46, 9.75, 1.75, 0.5, 0.40),
                     ('salon2', '-y', 0.70, 9.0, 1.7, 0.7, 0.5), ('salon2', '+x', 13.70, 2.4, 1.6, 0.6, 0.45),
                     ('pasillo', '+x', 8.34, 9.3, 1.6, 0.7, 0.5), ('pasillo', '-x', 6.70, 8.6, 1.6, 0.6, 0.8)],
}
ESPEJOS = {('casa', 'pb'): [('terapia', '+y', 4.14, 9.85, 1.2, 0.6, 1.5)]}


# ------------------------------------------------------------------ geometría de caras de muro por cuarto
def _muros_union(nv):
    ws = []
    for m in I.muros_exteriores(nv, []) + I.muros_interiores(nv)[0]:
        c0, c1 = sorted((m['c0'], m['c1']))
        ws.append(sbox(m['u0'], c0, m['u1'], c1) if m['eje'] == 'x' else sbox(c0, m['u0'], c1, m['u1']))
    return unary_union(ws)


def caras(nv, cid):
    """Segmentos de cara interior de muro de un cuarto: (eje, coord, u0, u1, normal hacia el cuarto)."""
    cu = {c['id']: c for c in nv['cuartos']}[cid]
    W = _muros_union(nv)
    libre = I.poly_cuarto(cu).difference(W)
    if libre.geom_type == 'MultiPolygon':
        libre = max(libre.geoms, key=lambda g: g.area)
    toca = libre.boundary.intersection(W.buffer(0.01))
    out = []
    for (a, b) in I._segmentos(toca):
        if abs(a[1] - b[1]) < 1e-6:
            c = a[1]; u0, u1 = sorted((a[0], b[0])); eje = 'x'
            n = 1 if libre.contains(Point((u0 + u1) / 2, c + 0.03)) else -1
        elif abs(a[0] - b[0]) < 1e-6:
            c = a[0]; u0, u1 = sorted((a[1], b[1])); eje = 'y'
            n = 1 if libre.contains(Point(c + 0.03, (u0 + u1) / 2)) else -1
        else:
            continue
        if u1 - u0 > 0.03:
            out.append((eje, c, u0, u1, n))
    return out, libre


def huecos_en(eje, c, n, puertas, aberturas, z0):
    """Vanos (u0, u1, za, zb) sobre una cara de muro."""
    hs = []
    for p in puertas:
        if p['eje'] == eje and abs(abs(p['c'] - c) - I.T_INT / 2) < 0.03:
            hs.append((p['u0'], p['u1'], z0, z0 + I.PUERTA_ALTO))
    for (cara, plano, a0, a1, za, zb) in aberturas:
        if cara == eje and abs(abs(plano - c) - I.T_EXT) < 0.03:
            hs.append((a0, a1, za, zb))
    return hs


def piezas(u0, u1, za, zb, hs):
    hs = [h for h in hs if h[3] > za + 0.005 and h[2] < zb - 0.005]      # solo vanos que cruzan la banda
    m = dict(u0=u0, u1=u1, huecos=hs)
    return [p for p in I.piezas_muro(m, za, zb) if p[1] - p[0] > 0.02 and p[3] - p[2] > 0.005]


def banda(fin, eje, c, n, u0, u1, za, zb, hs, mat, esp=0.008, sep=0.002, nombre='revest'):
    for (a, b, z0, z1) in piezas(u0, u1, za, zb, hs):
        if eje == 'x':
            y0, y1 = sorted((c + n * sep, c + n * (sep + esp)))
            fin.caja(a, y0, z0, b, y1, z1, mat)
        else:
            x0, x1 = sorted((c + n * sep, c + n * (sep + esp)))
            fin.caja(x0, a, z0, x1, b, z1, mat)


def pared_xy(lado, c, u, sep):
    """Punto contra un muro y giro del objeto (respaldo hacia el muro)."""
    if lado == '-y':
        return (u, c + sep), 0
    if lado == '+y':
        return (u, c - sep), 180
    if lado == '+x':
        return (c - sep, u), 90
    return (c + sep, u), 270


# ------------------------------------------------------------------ piezas de techo y pared
def plafon(m, r=0.17):
    m.cil(0, 0, -0.03, 0, r, 'metal_blanco', 24)
    m.cil(0, 0, -0.065, -0.03, r * 0.92, 'luz_panel', 24, r2=r * 0.98)


def domo(m, r=0.21):
    m.cil(0, 0, -0.02, 0, r + 0.02, 'metal_blanco', 28)
    m.esfera(0, 0, -0.02, r, 'luz_panel', 20, esc=(1, 1, 0.35))


def abanico(m, caida=0.35):
    m.cil(0, 0, -0.05, 0, 0.07, 'metal_blanco', 16)
    m.cil(0, 0, -caida, -0.05, 0.012, 'metal_blanco', 8)
    m.cil(0, 0, -caida - 0.14, -caida, 0.11, 'metal_blanco', 24, r2=0.09)
    for i in range(3):
        with m.at(0, 0, -caida - 0.10, g=120 * i):
            m.caja(0.10, -0.012, -0.006, 0.20, 0.012, 0.006, 'metal_gris')
            with m.at(0, 0, 0, rx=8):
                m.caja(0.18, -0.07, -0.004, 0.72, 0.07, 0.004, 'plastico_blanco', bev=0.003)
    m.esfera(0, 0, -caida - 0.17, 0.10, 'luz_panel', 16, esc=(1, 1, 0.6))


def aire(m):
    m.caja(-0.42, 0.0, -0.15, 0.42, 0.22, 0.15, 'plastico_blanco', bev=0.03, seg=3)
    m.caja(-0.36, 0.20, -0.13, 0.36, 0.222, -0.10, 'plastico_gris')
    m.caja(0.25, 0.221, 0.05, 0.32, 0.223, 0.07, 'luz_panel')


def cuadro_marco(m, w, h, mat_marco='madera_oscura'):
    m.caja(-w / 2 - 0.04, 0.0, -h / 2 - 0.04, w / 2 + 0.04, 0.03, h / 2 + 0.04, mat_marco, bev=0.008)
    m.caja(-w / 2 - 0.005, 0.03, -h / 2 - 0.005, w / 2 + 0.005, 0.033, h / 2 + 0.005, 'papel')


def lampara_cama(m):
    """Luminaria sobre la cabecera (encamados: 'luz sobre cada cama')."""
    m.caja(-0.32, 0.0, -0.04, 0.32, 0.09, 0.04, 'metal_blanco', bev=0.01)
    m.caja(-0.30, 0.09, -0.03, 0.30, 0.092, 0.03, 'luz_panel')
    m.caja(-0.42, 0.0, -0.30, 0.42, 0.06, -0.18, 'metal_blanco', bev=0.008)       # riel de gases y tomas
    for x in (-0.3, -0.1, 0.15, 0.32):
        m.cil(x, 0.06, -0.26, -0.22, 0.012, 'cromo', 8)


# ------------------------------------------------------------------ construcción
def construir(K, E, clave, C_LUZ):
    import bpy
    from shapely.geometry import box as _b
    cfg = EDIF[clave]
    luces = []

    def poner(nombre, m, x, y, z, g=0):
        ob = m.objeto(f'{K.pfx}_{nombre}_{len(K.objs)}', K.M, K.c)
        ob.location = (x, y, z); ob.rotation_euler = (0, 0, R(g))
        K.objs.append(ob)
        for (co, pw, rad, colr) in m.luces:
            luces.append((ob, co, pw, rad, colr))
        return ob

    def area_luz(x, y, z, pot, tam=0.35, color=(1.0, 0.92, 0.82)):
        ld = bpy.data.lights.new(f'{K.pfx}_luz_techo', 'AREA')
        ld.shape = 'DISK'; ld.size = tam; ld.energy = pot; ld.color = color
        o = bpy.data.objects.new(ld.name, ld); C_LUZ.objects.link(o)
        o.location = (x, y, z)
        K.luces_techo.append(o)
        return o
    K.luces_techo = []

    from lib import box_uv
    for nv, mu in zip(E['niveles'], K.interior['muros']):
        fin = Malla()
        z0 = nv['z0'] + 0.02
        zc = (nv['z0'] + cfg['cielo_h']) if cfg['cielo_h'] else (nv['z1'] - 0.01)
        abanicos = ABANICOS.get((clave, nv['id']), [])
        for cu in nv['cuartos']:
            cid = cu['id']
            segs, libre = caras(nv, cid)
            # zócalo cerámico
            for (eje, c, u0, u1, n) in segs:
                hs = huecos_en(eje, c, n, mu['puertas'], K.aberturas, nv['z0'])
                banda(fin, eje, c, n, u0, u1, z0, z0 + 0.08, hs, cfg['zocalo'], esp=0.012, nombre='zocalo')
                for (mat, za, zb) in REVEST.get((clave, nv['id'], cid), []):
                    banda(fin, eje, c, n, u0, u1, max(z0 + 0.08, nv['z0'] + za) if za == 0 else nv['z0'] + za,
                          (zc - 0.005) if zb is None else nv['z0'] + zb, hs, mat, esp=0.006, sep=0.003)
                if (clave, nv['id'], cid) in GUARDA:
                    banda(fin, eje, c, n, u0, u1, nv['z0'] + 0.82, nv['z0'] + 0.92, hs, 'madera_media', esp=0.025, sep=0.004,
                          nombre='guardacamilla')
            # piso especial (baños)
            if (clave, nv['id'], cid) in PISO_ESP:
                for (a, b, c, d) in I.celdas(libre):
                    fin.caja(a, b, z0, c, d, z0 + 0.004, 'piso_bano')
            # cielo raso (no sobre el hueco de la escalera de planta baja)
            if not (cu.get('escalera') and nv['id'] == 'pb'):
                for (a, b, c, d) in I.celdas(libre):
                    fin.caja(a, b, zc - 0.02, c, d, zc, cfg['cielo'])
            # lámparas de techo con su luz
            if cu.get('escalera') and nv['id'] == 'pb':
                continue
            x0, y0, x1, y1 = libre.bounds
            area = libre.area
            nfan = [f for f in abanicos if f[0] == cid]
            n = max(1, round(area / 9.0)) - len(nfan)
            pts = []
            if n > 0:
                largo_x = (x1 - x0) >= (y1 - y0)
                L = (x1 - x0) if largo_x else (y1 - y0)
                for i in range(n):
                    t = (i + 0.5) / n
                    p = (x0 + L * t, (y0 + y1) / 2) if largo_x else ((x0 + x1) / 2, y0 + L * t)
                    if not libre.contains(Point(p)):
                        p = libre.representative_point().coords[0]
                    pts.append(p)
            pot = 9.0 * area / max(1, n + len(nfan))
            for (x, y) in pts:
                m = Malla()
                (plafon if cfg['lampara'] == 'plafon' else domo)(m)
                poner('lampara', m, x, y, zc)
                area_luz(x, y, zc - 0.09, pot)
            for (_, x, y) in nfan:
                m = Malla(); abanico(m, 0.30 if cfg['cielo_h'] else 0.40)
                poner('abanico', m, x, y, zc)
                area_luz(x, y, zc - (0.30 if cfg['cielo_h'] else 0.40) - 0.25, pot, 0.3)
        ob = fin.objeto(f'{K.pfx}_acabados_{nv["id"]}', K.M, K.c)
        box_uv(ob, 1.0)
        K.objs.append(ob)
        # aires, cuadros, espejos
        for (cid, lado, c, u) in AIRES.get((clave, nv['id']), []):
            (x, y), g = pared_xy(lado, c, u, 0.0)
            m = Malla(); aire(m)
            poner('aire', m, x, y, zc - 0.32, g)
        for (cid, lado, c, u, zz, w, h) in CUADROS.get((clave, nv['id']), []):
            (x, y), g = pared_xy(lado, c, u, 0.004)
            m = Malla(); cuadro_marco(m, w, h)
            poner('cuadro', m, x, y, nv['z0'] + zz, g)
            # lienzo aparte (coordenadas generadas propias)
            m2 = Malla()
            m2.caja(-w / 2, 0.033, -h / 2, w / 2, 0.036, h / 2, f'lienzo_{hash((cid, u)) % 3}')
            poner('lienzo', m2, x, y, nv['z0'] + zz, g)
        for (cid, lado, c, u, zz, w, h) in ESPEJOS.get((clave, nv['id']), []):
            (x, y), g = pared_xy(lado, c, u, 0.004)
            m = Malla()
            m.caja(-w / 2 - 0.03, 0, -h / 2 - 0.03, w / 2 + 0.03, 0.02, h / 2 + 0.03, 'madera_clara', bev=0.005)
            m.caja(-w / 2, 0.02, -h / 2, w / 2, 0.022, h / 2, 'espejo')
            poner('espejo', m, x, y, nv['z0'] + zz, g)
        # luminaria sobre la cabecera de cada cama de encamados y del salón amarillo
        if clave == 'gris' and nv['id'] == 'pa':
            import amueblado as A
            for cid in ('hosp', 'salon2'):
                for it in A.DIST[('gris', 'pa')][cid]:
                    if it['t'] != 'cama_hosp':
                        continue
                    g = it['g']
                    bx = math.sin(R(g)); by = -math.cos(R(g))
                    d = A.CAT['cama_hosp'][1]
                    x = it['x'] + bx * d / 2; y = it['y'] + by * d / 2
                    m = Malla(); lampara_cama(m)
                    poner('lampara_cama', m, x, y, nv['z0'] + 1.65, g)
                    ld = bpy.data.lights.new(f'{K.pfx}_luz_cama', 'AREA'); ld.shape = 'RECTANGLE'
                    ld.size = 0.6; ld.size_y = 0.08; ld.energy = 14; ld.color = (1.0, 0.93, 0.85)
                    o = bpy.data.objects.new(ld.name, ld); C_LUZ.objects.link(o)
                    o.location = (x - bx * 0.2, y - by * 0.2, nv['z0'] + 1.62)
                    o.rotation_euler = (0, 0, 0)
                    K.luces_techo.append(o)
        # cortinas en las ventanas de los cuartos indicados
        curt = CORTINAS.get(clave, {})
        for (cara, plano, a0, a1, za, zb) in K.aberturas:
            if za < nv['z0'] + 0.3 or za > nv['z1'] - 0.3 or zb - za < 0.6:
                continue
            for cu in nv['cuartos']:
                if cu['id'] not in curt:
                    continue
                pol = I.poly_cuarto(cu)
                mid = (a0 + a1) / 2
                for s in (1, -1):
                    p = (mid, plano + s * 0.35) if cara == 'x' else (plano + s * 0.35, mid)
                    if pol.contains(Point(p)):
                        cortina(K, poner, cara, plano + s * (I.T_EXT + 0.06), s, a0, a1, za, min(zb + 0.25, zc - 0.04),
                                curt[cu['id']])
                        break
        # hojas de puertas interiores
        for p in mu['puertas']:
            hoja_puerta(K, poner, p, nv['z0'], cfg, clave)
    # galería este del gris: piso de baldosa, abanicos
    if clave == 'gris':
        K.B('piso_galeria', 4.62, 11.02, 3.2, 13.88, 13.18, 3.208, 'piso_terraza')
        for (x, y) in ABANICOS_GALERIA:
            m = Malla(); abanico(m, 0.35)
            poner('abanico_gal', m, x, y, 6.15)
            area_luz(x, y, 6.15 - 0.62, 30, 0.3)
    K.luces_acabados = luces
    return luces


def cortina(K, poner, cara, c, s, a0, a1, za, zb, mat):
    """Dos paños plisados recogidos a los lados de la ventana y su barra."""
    m = Malla()
    L = a1 - a0
    ancho = min(0.45, 0.25 + L * 0.12)
    for (u0, u1) in ((a0 - 0.15, a0 - 0.15 + ancho), (a1 + 0.15 - ancho, a1 + 0.15)):
        nplieg = max(4, int((u1 - u0) / 0.06))
        for i in range(nplieg):
            u = u0 + (u1 - u0) * (i + 0.5) / nplieg
            dv = 0.03 * math.sin(i * 2.1)
            m.caja(u - (u1 - u0) / nplieg * 0.75, -0.025 + dv, za - 0.25, u + (u1 - u0) / nplieg * 0.75, 0.02 + dv, zb - 0.02, mat,
                   bev=0.01, seg=2, suave=True)
    m.tubo((a0 - 0.25, 0.0, zb + 0.01), (a1 + 0.25, 0.0, zb + 0.01), 0.012, 'metal_negro')
    # el marco local de la Malla corre en x; se gira para muros en y
    if cara == 'x':
        poner('cortina', m, 0.0, c + s * 0.0, 0.0, 0)
    else:
        # u corre en y: girar 90° (x local → y) y espejar el lado
        poner('cortina', m, c, 0.0, 0.0, 90)


def hoja_puerta(K, poner, p, z0, cfg, clave):
    a = p['u1'] - p['u0']
    m = Malla()
    if p.get('tipo') == 'corrediza':
        # dos paños de vidrio con marco de madera y arcos decorativos (puertas de la foto del cuarto VIP)
        for i, off in enumerate((0.0, a / 2 - 0.08)):
            x0 = -a / 2 + off + 0.02
            x1 = x0 + a / 2
            yy = -0.03 if i == 0 else 0.03
            m.caja(x0, yy - 0.02, 0.02, x1, yy + 0.02, 2.06, 'madera_oscura', bev=0.004)
            m.caja(x0 + 0.06, yy - 0.006, 0.12, x1 - 0.06, yy + 0.006, 1.98, 'vidrio_int')
            # arco decorativo de madera en la parte alta del paño
            cx = (x0 + x1) / 2
            for k in range(12):
                t0 = math.pi * k / 12; t1 = math.pi * (k + 1) / 12
                r = (x1 - x0) / 2 - 0.07
                m.tubo((cx + r * math.cos(t0), yy + 0.012, 1.40 + r * math.sin(t0) * 0.9),
                       (cx + r * math.cos(t1), yy + 0.012, 1.40 + r * math.sin(t1) * 0.9), 0.012, 'madera_oscura', 6)
            m.caja(x0 + 0.06, yy + 0.008, 1.38, x1 - 0.06, yy + 0.02, 1.42, 'madera_oscura')
            m.caja(x1 - 0.12, yy + 0.02, 0.95, x1 - 0.10, yy + 0.05, 1.15, 'cromo')
        m.caja(-a / 2, -0.06, 2.06, a / 2, 0.06, 2.10, 'madera_oscura')
        if p['eje'] == 'x':
            poner('puerta_corrediza', m, (p['u0'] + p['u1']) / 2, p['c'], z0, 0)
        else:
            poner('puerta_corrediza', m, p['c'], (p['u0'] + p['u1']) / 2, z0, 90)
        return
    # hoja batiente abierta a 90°, contra el lado de la bisagra
    mat = cfg['puerta']
    oficina = clave == 'gris' and any(x.startswith('oficina') for x in p['entre'])
    if oficina:
        mat = 'madera_rojiza'
    L = a - 0.04
    m.caja(0, -0.02, 0.02, L, 0.02, 2.06, mat, bev=0.004)
    for (zz0, zz1) in ((0.15, 0.95), (1.08, 1.95)):
        for s in (-1, 1):
            m.caja(0.10, s * 0.02 - (0.004 if s < 0 else 0), zz0, L - 0.10, s * 0.02 + (0.004 if s > 0 else 0), zz1, mat, bev=0.006)
    if oficina:
        for s in (-1, 1):
            m.esfera(L / 2, s * 0.024, 1.45, 0.17, 'vidrio_int', 16, esc=(0.75, 0.05, 1.3))
    for s in (-1, 1):
        m.caja(L - 0.09, s * 0.02, 0.98, L - 0.07, s * 0.06, 1.0, 'cromo')
        m.caja(L - 0.21, s * 0.055, 0.98, L - 0.07, s * 0.065, 1.0, 'cromo')
    lado = p['lado']
    if p['eje'] == 'x':
        u = p['u0'] + 0.03 if p['bisagra'] == 'lo' else p['u1'] - 0.03
        # la hoja corre en +y o -y desde la bisagra
        g = 90 if lado > 0 else 270
        poner('hoja_puerta', m, u, p['c'] + lado * (I.T_INT / 2 + 0.02), z0, g)
    else:
        u = p['u0'] + 0.03 if p['bisagra'] == 'lo' else p['u1'] - 0.03
        g = 0 if lado > 0 else 180
        poner('hoja_puerta', m, p['c'] + lado * (I.T_INT / 2 + 0.02), u, z0, g)
