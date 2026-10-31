"""
Etapa 4a · amueblado de los interiores.

Una sola fuente para el modelo 3D (constructores en muebles3d.py) y los planos 2D (planos.py):
cada mueble es (tipo, centro x, centro y, giro en grados, opciones) en el marco local del edificio.

Convención de cada mueble: ancho w en x local, fondo d en y local; el respaldo (lo que va contra el
muro: cabecera de la cama, espalda del ropero, tanque del inodoro) está en -y local. Con giro g, el
respaldo mira hacia (sin g, -cos g): 0 → -y, 180 → +y, 90 → +x, 270 → -x.

Usos por cuarto según docs/contexto-proyecto.md (29-10-2026). Medidas estimadas (no levantamiento).
"""
import math
from shapely.geometry import Polygon, box as sbox, LineString
from shapely.ops import unary_union
import interiores as I

# tipo: (w, d, h) — medidas exteriores en metros
CAT = {
    'cama_hosp': (0.92, 2.10, 0.95), 'cama': (1.00, 2.05, 1.10), 'cama_suite': (1.45, 2.10, 1.15),
    'mesita': (0.45, 0.40, 0.58), 'mesita_hosp': (0.38, 0.45, 0.80), 'mesa_puente': (0.80, 0.42, 0.95),
    'estacion': (1.05, 0.95, 1.05),
    'ropero': (0.90, 0.58, 2.00), 'ropero_doble': (1.60, 0.60, 2.05),
    'butaca': (0.78, 0.80, 0.88), 'butaca_cuero': (0.80, 0.82, 0.86), 'reclinable': (0.86, 0.95, 1.02),
    'silla_ruedas': (0.64, 1.05, 0.92), 'sofa': (2.00, 0.90, 0.85), 'sofa2': (1.45, 0.86, 0.85),
    'mesa_centro': (1.00, 0.55, 0.42), 'mesa_centro_red': (0.65, 0.65, 0.48), 'mueble_tv': (1.50, 0.42, 0.55),
    'comedor': (2.10, 1.60, 0.76), 'aparador': (1.10, 0.45, 1.60),
    'mostrador': (1.80, 1.30, 1.10), 'escritorio': (1.40, 2.05, 0.76), 'escritorio_simple': (1.10, 1.05, 0.76),
    'archivador': (0.47, 0.62, 1.32), 'librero': (0.90, 0.35, 1.95), 'estante': (0.90, 0.45, 1.85),
    'camilla_med': (1.90, 0.66, 0.78), 'camilla_ter': (1.95, 0.72, 0.72), 'paralelas': (2.00, 0.80, 1.00),
    'bici': (0.55, 1.05, 1.25), 'estante_ter': (1.00, 0.40, 1.60), 
    'mesa_taller': (1.60, 1.35, 0.76), 'caballete': (0.62, 0.62, 1.65), 'maquina_coser': (1.00, 1.00, 0.76),
    'mesa_reunion': (1.50, 1.50, 0.75),
    'inox_fregadero': (1.20, 0.65, 0.90), 'inox_plano': (1.00, 0.65, 0.90), 'estufa': (0.90, 0.75, 0.90),
    'refri': (0.80, 0.75, 1.85), 'mesa_inox': (0.60, 1.20, 0.90),
    'granito_fregadero': (1.20, 0.60, 0.90), 'granito_plano': (0.70, 0.60, 0.90), 'refri_chico': (0.55, 0.58, 0.85),
    'lavadora': (0.65, 0.65, 0.90), 'secadora': (0.65, 0.65, 0.90), 'batea': (0.60, 0.55, 0.90),
    'inodoro': (0.40, 0.70, 0.80), 'lavamanos': (0.55, 0.46, 0.86), 'tocador': (1.40, 0.55, 0.88),
    'ducha': (1.00, 1.00, 2.10),
    'barra_buffet': (1.80, 0.55, 0.92), 'mesa_redonda': (1.45, 1.45, 0.75), 'dispensador': (0.34, 0.34, 1.10),
    'pizarra': (0.62, 0.50, 1.40),
    'planta': (0.55, 0.55, 1.70), 'planta_med': (0.42, 0.42, 1.05), 'banca': (1.20, 0.45, 0.46),
    'lampara_pie': (0.36, 0.36, 1.60), 'portagarrafon': (0.40, 0.40, 1.15),
}
# muebles altos que no deben tapar ventanas: (para el validador; solo aviso)
ALTOS = {'ropero', 'ropero_doble', 'librero', 'estante', 'refri', 'aparador', 'archivador', 'estante_ter'}
# pueden tocarse entre sí (mesita contra cama, mesa puente sobre la cama, etc.)
PEGADOS = {'mesita', 'mesita_hosp', 'mesa_puente'}
SOBRE = {'mesa_puente'}          # va sobre la cama: no cuenta como choque


def P(t, x, y, g=0, **kw):
    return dict(t=t, x=x, y=y, g=g, **kw)


def W(t, lado, c, u, sep=0.0, **kw):
    """Mueble con el respaldo contra un muro. lado: '-x' '+x' '-y' '+y' (el muro está en esa dirección),
    c = cara interior del muro, u = posición del centro a lo largo del muro."""
    w, d, h = CAT[t]
    w, d = kw.get('w', w), kw.get('d', d)
    if lado == '-y':
        return P(t, u, c + sep + d / 2, 0, **kw)
    if lado == '+y':
        return P(t, u, c - sep - d / 2, 180, **kw)
    if lado == '+x':
        return P(t, c - sep - d / 2, u, 90, **kw)
    return P(t, c + sep + d / 2, u, 270, **kw)


def fila(t, lado, c, u0, n, hueco, mesa=None, sep=0.0, **kw):
    """n muebles iguales contra un muro desde u0 (borde), con `mesa` (tipo) entre cada par si se da."""
    w = CAT[t][0]
    out, u = [], u0
    for i in range(n):
        out.append(W(t, lado, c, u + w / 2, sep, **kw))
        u += w
        if i < n - 1:
            if mesa:
                wm = CAT[mesa][0]
                out.append(W(mesa, lado, c, u + hueco / 2, sep))
            u += hueco
    return out


def huella(m):
    """Polígono de la planta del mueble."""
    w, d, h = CAT[m['t']]
    w, d = m.get('w', w), m.get('d', d)
    g = math.radians(m['g'])
    cs, sn = math.cos(g), math.sin(g)
    pts = []
    for (a, b) in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        pts.append((m['x'] + a * cs - b * sn, m['y'] + a * sn + b * cs))
    return Polygon(pts)


# ===================================================================== DISTRIBUCIÓN POR CUARTO
# Casa amarilla, planta baja ----------------------------------------------------------------
CASA_PB = {
    'consultorio': [W('escritorio', '-y', 0.20, 1.20, sep=0.05), W('camilla_med', '+x', 3.34, 1.15),
                    W('archivador', '+y', 3.54, 0.55), W('estante', '+y', 3.54, 1.35, d=0.40),
                    W('lavamanos', '+y', 3.54, 2.10)],
    'cocina': [W('refri', '-x', 0.20, 4.08), W('estufa', '-x', 0.20, 4.95), W('inox_plano', '-x', 0.20, 5.55, w=0.30),
               W('inox_fregadero', '-x', 0.20, 6.32), W('inox_plano', '-y', 3.66, 1.65, w=1.30),
               P('mesa_inox', 1.95, 5.30, 0)],
    'comedor': [P('comedor', 4.70, 5.95, 90, sillas=5), W('sofa', '-x', 3.46, 1.35),
                P('mesa_centro', 4.85, 1.35, 90), P('mueble_tv', 5.95, 1.25, 90),
                P('butaca', 4.85, 2.70, 180), W('planta', '-y', -0.40, 5.82, sep=0.02)],
    'recepcion': [W('mostrador', '+y', 3.54, 7.55), W('butaca_cuero', '-y', -0.40, 7.62, sep=0.06),
                  W('butaca_cuero', '-y', -0.40, 8.48, sep=0.06), P('mesa_centro_red', 8.05, 0.98, 0),
                  W('planta', '-y', -0.40, 6.92, sep=0.02)],
    'vip': [W('cama', '+x', 9.34, 5.15), W('mesita', '+x', 9.34, 4.35), W('mesita', '+x', 9.34, 5.95),
            W('ropero_doble', '-y', 3.66, 7.85), W('butaca', '+y', 6.94, 7.85, sep=0.03),
            W('planta_med', '+y', 6.94, 8.95)],
    'terapia': [W('camilla_ter', '-y', 1.10, 10.55, sep=0.05), W('paralelas', '+x', 12.40, 2.30, sep=0.05),
                P('bici', 10.18, 3.80, 90), W('estante_ter', '+y', 4.14, 11.05, w=0.70),
                P('silla_fam', 10.95, 2.30, 0), P('silla_fam', 10.95, 2.90, 0)],
    'talleres': [W('mesa_taller', '+y', 6.94, 10.35), W('maquina_coser', '-y', 4.26, 10.00),
                 P('caballete', 10.95, 4.95, 200)],
    'pasillo': [W('banca', '+y', 8.34, 3.30), W('planta_med', '-y', 7.06, 0.55),
                W('planta_med', '+y', 8.34, 12.10)],
    'lavanderia': [W('batea', '-x', 0.20, 8.80), W('lavadora', '-x', 0.20, 9.50), W('secadora', '-x', 0.20, 10.18),
                   W('estante', '+y', 10.94, 0.75, d=0.35, w=0.90)],
    'psicologia': [W('escritorio_simple', '-x', 0.20, 11.70), W('butaca', '+y', 13.60, 0.70, sep=0.05),
                   W('butaca', '+x', 2.34, 13.00, sep=0.05)],
    'semipriv': [W('cama', '+y', 13.60, 3.90), W('mesita', '+y', 13.60, 2.95), W('mesita', '+y', 13.60, 4.85),
                 W('escritorio_simple', '+x', 5.34, 11.05, w=1.0),
                 W('ropero', '-x', 2.46, 9.05), W('ropero', '-x', 2.46, 9.97), W('butaca', '+x', 5.34, 9.95, sep=0.05)],
    'bano1': [W('tocador', '+x', 7.44, 10.10), W('inodoro', '-x', 5.46, 10.55), W('ducha', '+y', 13.60, 6.45, w=1.98, d=1.30)],
    'suite': [W('cama_suite', '+x', 12.40, 11.00), W('mesita', '+x', 12.40, 9.95), W('mesita', '+x', 12.40, 12.05),
              W('ropero_doble', '-y', 8.46, 11.55), P('butaca', 11.65, 13.05, 135), W('lampara_pie', '+y', 13.60, 12.15)],
    'bano2': [W('ducha', '+y', 13.60, 8.03, w=0.95, d=0.82), W('inodoro', '-y', 12.06, 7.85),
              W('lavamanos', '-y', 12.06, 8.85, d=0.38)],
}
CASA_PA = {
    'recamara': [W('cama_suite', '+x', 9.50, 4.30), W('mesita', '+x', 9.50, 3.10), W('mesita', '+x', 9.50, 5.50),
                 W('ropero_doble', '+y', 6.94, 8.40), W('sofa2', '-x', 4.90, 5.00), P('mesa_centro_red', 6.30, 5.00, 0, w=0.55, d=0.55),
                 W('escritorio_simple', '-x', 4.90, 2.90), W('planta', '+y', 6.94, 7.20), W('planta_med', '-y', 1.60, 5.15)],
    'hall': [W('banca', '-x', 4.90, 7.70, sep=0.02), P('planta_med', 9.20, 7.32, 0)],
    'bano_rec': [W('ducha', '-y', 8.46, 5.62, w=1.44, d=0.95), W('inodoro', '-x', 4.90, 10.05),
                 W('lavamanos', '-x', 4.90, 11.40)],
    'oficina_ger': [W('archivador', '-y', 12.06, 5.20), W('archivador', '-y', 12.06, 5.70), W('librero', '-y', 12.06, 6.25, d=0.32, w=0.55),
                    W('escritorio_simple', '+y', 13.60, 8.30), W('librero', '+x', 9.50, 12.80, d=0.32)],
}
# Edificio gris, planta baja ---------------------------------------------------------------
GRIS_PB = {
    'acceso': [W('banca', '+x', 9.04, 2.10), W('planta', '+x', 9.04, 0.98), W('dispensador', '+x', 9.04, 3.10)],
    'bano_acc': [W('ducha', '-y', 2.60, 5.33, w=1.06, d=1.10), W('inodoro', '+x', 6.64, 3.05), W('lavamanos', '-x', 4.80, 4.20)],
    'oficina1': [W('escritorio', '-y', 0.70, 10.30), W('archivador', '+x', 11.44, 3.30), W('archivador', '+x', 11.44, 3.80),
                 W('librero', '-x', 9.16, 3.30, d=0.32)],
    'oficina2': [W('escritorio', '-y', 0.70, 12.60), W('archivador', '-x', 11.56, 3.10), W('estante', '+x', 13.70, 3.75, d=0.40)],
    'pasillo': [W('butaca_cuero', '-y', 5.00, 2.35, sep=0.05), W('butaca_cuero', '-y', 5.00, 3.75, sep=0.05),
                W('portagarrafon', '-y', 5.00, 3.05, sep=0.05), W('planta', '+y', 7.34, 1.62), W('banca', '+y', 6.14, 11.70)],
    'estar': [W('sofa2', '+x', 9.04, 8.15), P('butaca', 7.30, 9.30, 180), P('mesa_centro', 7.92, 8.25, 90, w=0.80, d=0.46)],
    'salonA': fila('cama', '+y', 12.50, 5.05, 2, 0.55, mesa='mesita') +
              [W('ropero_doble', '+x', 9.04, 11.70), W('mesita', '+y', 12.50, 7.82)],
    'salonB': fila('cama', '+y', 12.50, 9.40, 3, 0.45, mesa='mesita') +
              fila('cama', '-y', 6.26, 10.55, 2, 0.45, mesa='mesita') +
              [W('cama', '+x', 13.70, 9.38), W('mesita', '-y', 6.26, 13.30),
               W('ropero', '-x', 9.16, 7.95), W('ropero', '-x', 9.16, 8.87), W('ropero', '-x', 9.16, 9.79),
               P('butaca', 10.45, 9.35, 300)],
    'huerto': [W('escritorio_simple', '-x', 1.30, 8.85, w=0.95), W('estante', '+y', 10.00, 1.95, d=0.40, w=1.20)],
}
GRIS_PA = {
    'pasillo': [W('planta', '-y', 0.70, 7.75), W('banca', '-x', 6.90, 1.75)],
    'bano': [W('ducha', '-y', 2.60, 5.30, w=1.00, d=1.00), W('inodoro', '+y', 4.74, 5.20), W('lavamanos', '+y', 4.74, 6.12)],
    'cocina': [W('granito_fregadero', '-y', 4.87, 5.37), W('granito_plano', '-y', 4.87, 6.30, w=0.66),
               W('refri_chico', '+y', 7.34, 4.98), W('granito_plano', '+y', 7.34, 5.45, w=0.38)],
    'deposito': [W('estante', '+y', 7.34, 3.20), W('estante', '+y', 7.34, 4.10), W('estante', '-y', 5.00, 3.20)],
    'closet': [W('estante', '+y', 10.80, 5.20, d=0.40, w=0.70)],
    'salon2': fila('cama_hosp', '+y', 4.14, 8.54, 4, 0.44, mesa='mesita_hosp') +
              [W('reclinable', '-y', 0.70, 13.05, sep=0.05), W('silla_ruedas', '-y', 0.70, 11.10, sep=0.05)],
    # 10 encamados: cabecera contra los muros largos y pasillo central de ~1 m. La puerta del pasillo
    # queda entre la 2.ª y la 3.ª cama del lado norte; la estación de enfermería, a la cabeza del pasillo
    # central (donde estaba el podio), mira a las 10 camas. Del lado norte no cabe mesita entre camas:
    # llevan mesa puente.
    'hosp': fila('cama_hosp', '+x', 13.70, 4.32, 5, 0.40, mesa='mesita_hosp') +
            [W('cama_hosp', '-x', 8.46, yc) for yc in (4.76, 5.93, 7.96, 9.13, 10.30)] +
            [P('mesa_puente', 9.55, yc, 90) for yc in (5.93, 9.13)] +
            [W('estacion', '-y', 4.26, 11.09, sep=0.02, w=1.0)],
}
# galería este de la planta alta (terraza cerrada con verjas): refrigerios + estar
GALERIA = [W('barra_buffet', '-y', 11.00, 5.68, sep=0.02), W('dispensador', '-y', 11.00, 6.78, sep=0.02),
           P('pizarra', 4.95, 11.85, 60),
           P('mesa_redonda', 6.15, 12.40, 0), P('mesa_redonda', 9.20, 12.40, 0),
           W('butaca', '+y', 13.15, 12.25, sep=0.02), W('butaca', '+y', 13.15, 13.20, sep=0.02),
           P('mesa_centro_red', 12.72, 12.05, 0, w=0.55, d=0.55),
           W('planta', '+y', 13.15, 4.95), W('planta', '+y', 13.15, 10.75), W('planta_med', '-y', 11.00, 13.55)]

DIST = {('casa', 'pb'): CASA_PB, ('casa', 'pa'): CASA_PA, ('gris', 'pb'): GRIS_PB, ('gris', 'pa'): GRIS_PA}
EXTRA = {('gris', 'pa'): {'galeria': GALERIA}}
CAT['silla_fam'] = (0.50, 0.52, 0.85)


def camas():
    """Cuenta de camas por cuarto (para la lámina y la verificación del programa)."""
    out = {}
    for (ed, nv), d in DIST.items():
        for cid, lista in d.items():
            n = sum(1 for m in lista if m['t'].startswith('cama'))
            if n:
                out[(ed, nv, cid)] = n
    return out


# ===================================================================== VALIDACIÓN 2D
def _muros(nivel):
    ws = []
    mext = I.muros_exteriores(nivel, [])
    mint, pu = I.muros_interiores(nivel)
    for m in mext + mint:
        c0, c1 = sorted((m['c0'], m['c1']))
        ws.append(sbox(m['u0'], c0, m['u1'], c1) if m['eje'] == 'x' else sbox(c0, m['u0'], c1, m['u1']))
    return unary_union(ws), pu


def barrido(p, prof=None):
    """Zona de barrido de la hoja (cuadrado del ancho de la puerta del lado hacia el que abre)."""
    a = p['u1'] - p['u0']
    prof = a if prof is None else prof
    if p.get('tipo') == 'corrediza':
        prof = 0.6                       # paso libre delante de la corrediza
        lados = (1, -1)
    else:
        lados = (p['lado'],)
    zs = []
    for s in lados:
        if p['eje'] == 'x':
            zs.append(sbox(p['u0'], min(p['c'], p['c'] + s * prof), p['u1'], max(p['c'], p['c'] + s * prof)))
        else:
            zs.append(sbox(min(p['c'], p['c'] + s * prof), p['u0'], max(p['c'], p['c'] + s * prof), p['u1']))
    return unary_union(zs)


def validar(E, clave):
    """Lista de problemas: fuera del cuarto, choques entre muebles, barrido de puertas."""
    probs = []
    for nv in E['niveles']:
        d = DIST.get((clave, nv['id']), {})
        muros, pu = _muros(nv)
        cuartos = {c['id']: c for c in nv['cuartos']}
        zonas = [(p, barrido(p)) for p in pu]
        for cid, lista in d.items():
            libre = I.poly_cuarto(cuartos[cid]).difference(muros).buffer(0.005)
            hs = [(m, huella(m)) for m in lista]
            for i, (m, h) in enumerate(hs):
                if not libre.contains(h):
                    fuera = h.difference(libre).area
                    if fuera > 0.004:
                        probs.append(f'{clave}/{nv["id"]}/{cid}: {m["t"]} sale del cuarto ({fuera:.2f} m²)')
                for (p, z) in zonas:
                    if cid in p['entre'] and h.intersection(z).area > 0.01 and m['t'] not in SOBRE:
                        probs.append(f'{clave}/{nv["id"]}/{cid}: {m["t"]} invade la puerta {p["entre"]}')
                for (m2, h2) in hs[i + 1:]:
                    if m['t'] in SOBRE or m2['t'] in SOBRE:
                        continue
                    a = h.intersection(h2).area
                    if a > 0.003:
                        probs.append(f'{clave}/{nv["id"]}/{cid}: {m["t"]} choca con {m2["t"]} ({a:.2f} m²)')
    return probs


def huellas_nivel(clave, nivel_id):
    out = []
    for cid, lista in DIST.get((clave, nivel_id), {}).items():
        for m in lista:
            out.append((cid, m, huella(m)))
    for cid, lista in EXTRA.get((clave, nivel_id), {}).items():
        for m in lista:
            out.append((cid, m, huella(m)))
    return out


def choques_ruta(clave, nivel_id, pts, holgura=0.25):
    """Muebles que tocan una ruta (lista de puntos x,y) con media holgura de paso."""
    ln = LineString(pts).buffer(holgura)
    return [(cid, m['t']) for cid, m, h in huellas_nivel(clave, nivel_id)
            if m['t'] not in SOBRE and h.intersection(ln).area > 0.002]


if __name__ == '__main__':
    tot = 0
    for k, n in camas().items():
        print('camas', k, n); tot += n
    print('total camas', tot)
    for E, clave in ((I.CASA, 'casa'), (I.GRIS, 'gris')):
        for p in validar(E, clave):
            print('  !', p)
