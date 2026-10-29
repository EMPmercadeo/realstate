"""
Construye la escena completa del proyecto (terreno + dos edificios + exteriores + mobiliario).
Uso:  python3 -c "import runpy; runpy.run_path('blender/build.py')"  (con bpy instalado)
Produce: build/escena.blend y build/escena.glb
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
from lib import *
from programa import GRIS, AMARILLA, LOTE, ELEMENTOS, ARBOLES, PALMAS

random.seed(4)
OUT = os.path.join(ROOT, 'build')
os.makedirs(OUT, exist_ok=True)

# ---------------- escena limpia ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

ALTO = 3.0      # altura libre
LOSA = 0.25     # espesor losa
NIVEL = ALTO + LOSA
EXT = 0.25      # muro exterior
INT = 0.12      # muro interior

# ---------------- materiales ----------------
M = dict(
    concreto=mat('concreto', 'concrete', scale=0.33, normal_strength=0.6),
    gris_claro=mat('gris_claro', 'concrete', scale=0.33, normal_strength=0.4, tint=(1.12, 1.12, 1.12, 1)),
    amarillo=mat('amarillo', 'plaster_yellow', scale=0.4, normal_strength=0.5),
    blanco=mat('blanco', 'plaster_white', scale=0.4, normal_strength=0.3),
    ceramica=mat('ceramica', 'ceramic_beige', scale=0.4166, normal_strength=0.8),   # 6 baldosas de 40cm = 2.5m
    ceramica_g=mat('ceramica_g', 'ceramic_grey', scale=0.4166, normal_strength=0.8),
    teja=mat('teja', 'roof_tile', scale=0.5, normal_strength=1.0),
    lamina=mat('lamina', 'metal_roof', scale=0.5, normal_strength=0.8, metal=0.6),
    lamina_roja=mat('lamina_roja', 'metal_roof', scale=0.5, normal_strength=0.8, metal=0.4, rough=0.5, tint=(0.62, 0.1, 0.07, 1)),
    ladrillo=mat('ladrillo', color=(0.28, 0.11, 0.07, 1), rough=0.9),
    ac_blanco=mat('ac_blanco', color=(0.9, 0.9, 0.88, 1), rough=0.5),
    ac_rejilla=mat('ac_rejilla', color=(0.25, 0.26, 0.27, 1), rough=0.6, metal=0.3),
    grava=mat('grava', 'gravel', scale=0.5, normal_strength=1.0),
    tierra=mat('tierra', 'soil', scale=0.5),
    granito=mat('granito', 'granite', scale=0.5),
    madera=mat('madera', 'wood_dark', scale=0.5),
    cesped=mat('cesped', 'grass', scale=0.25, normal_strength=0.6),
    cesped_ext=mat('cesped_ext', 'grass', scale=0.25, normal_strength=0.6, tint=(0.8, 0.85, 0.75, 1)),
    asfalto=mat('asfalto', 'concrete', scale=0.5, tint=(0.45, 0.45, 0.46, 1), rough=0.95),
    acera=mat('acera', 'concrete', scale=0.5, tint=(0.95, 0.95, 0.93, 1)),
    vidrio=mat('vidrio', color=(0.75, 0.85, 0.9, 1), rough=0.05, transmission=1.0, alpha=0.25, ior=1.5),
    marco=mat('marco', color=(0.92, 0.92, 0.9, 1), rough=0.4, metal=0.3),
    hierro=mat('hierro', color=(0.08, 0.08, 0.09, 1), rough=0.5, metal=0.8),
    baranda_b=mat('baranda_b', color=(0.95, 0.95, 0.95, 1), rough=0.35, metal=0.4),
    azul=mat('azul', color=(0.12, 0.3, 0.7, 1), rough=0.6),
    azul_p=mat('azul_p', color=(0.1, 0.32, 0.75, 1), rough=0.9),
    tronco=mat('tronco', 'wood_dark', scale=0.8, tint=(0.75, 0.7, 0.65, 1), rough=0.95),
    hoja=mat('hoja', color=(0.07, 0.22, 0.06, 1), rough=0.85),
    hoja2=mat('hoja2', color=(0.1, 0.3, 0.08, 1), rough=0.85),
    palma=mat('palma', color=(0.09, 0.3, 0.08, 1), rough=0.75),
    agua=mat('agua', color=(0.35, 0.7, 0.85, 1), rough=0.05, transmission=0.8, alpha=0.7, ior=1.33),
    colchon=mat('colchon', color=(0.9, 0.9, 0.88, 1), rough=0.9),
    cobija=mat('cobija', color=(0.36, 0.45, 0.6, 1), rough=1.0),
    mesita_top=mat('mesita_top', color=(0.92, 0.9, 0.86, 1), rough=0.4),
    cortina=mat('cortina', color=(0.93, 0.9, 0.84, 1), rough=0.95),
    zocalo=mat('zocalo', color=(0.35, 0.33, 0.3, 1), rough=0.6),
    flor_r=mat('flor_r', color=(0.8, 0.12, 0.15, 1), rough=0.8),
    flor_a=mat('flor_a', color=(0.9, 0.55, 0.1, 1), rough=0.8),
    banca=mat('banca', 'wood_dark', scale=0.5, tint=(1.4, 1.3, 1.2, 1)),
    sabana=mat('sabana', color=(0.25, 0.5, 0.7, 1), rough=0.95),
    almohada=mat('almohada', color=(1, 1, 1, 1), rough=1.0),
    cama_metal=mat('cama_metal', color=(0.45, 0.47, 0.5, 1), rough=0.35, metal=0.85),
    cama_cabecera=mat('cama_cabecera', color=(0.62, 0.7, 0.76, 1), rough=0.5),
    mesita=mat('mesita', 'wood_dark', scale=0.5, tint=(1.3, 1.25, 1.2, 1)),
    led=mat('led', color=(1, 0.97, 0.9, 1), emission=((1, 0.96, 0.85, 1), 6.0)),
    led_panel=mat('led_panel', color=(1, 1, 1, 1), emission=((1, 0.98, 0.94, 1), 28.0)),
    tela_rojo=mat('tela_rojo', color=(0.55, 0.12, 0.12, 1), rough=0.9),
    tela_gris=mat('tela_gris', color=(0.45, 0.45, 0.47, 1), rough=0.9),
    mantel=mat('mantel', color=(0.97, 0.97, 0.95, 1), rough=0.95),
    ceramica_banio=mat('ceramica_banio', color=(0.95, 0.95, 0.95, 1), rough=0.2),
    rojo_tile=mat('rojo_tile', color=(0.72, 0.2, 0.12, 1), rough=0.25),
    porcelana=mat('porcelana', color=(0.98, 0.98, 0.98, 1), rough=0.1),
    estacion=mat('estacion', color=(0.93, 0.93, 0.9, 1), rough=0.5),
    cielo_raso=mat('cielo_raso', color=(0.96, 0.96, 0.95, 1), rough=0.9),
    puerta=mat('puerta', 'wood_dark', scale=0.4),
    puerta_roja=mat('puerta_roja', color=(0.5, 0.1, 0.08, 1), rough=0.4),
)

C_TERRENO = coll('Terreno')
C_VEG = coll('Vegetacion')
C_EXT = coll('Exteriores')


# =====================================================================
#  TERRENO
# =====================================================================
def build_terreno():
    # césped del entorno
    g = box('entorno', (260, 260, 0.1), (-110, -90, -0.15), M['cesped_ext'], C_TERRENO, 4.0)
    # lote
    pts = LOTE['poligono']
    verts = [(x, y, 0.0) for x, y in pts] + [(x, y, -0.3) for x, y in pts]
    n = len(pts)
    faces = [tuple(range(n))[::-1]] + [tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    lote = mesh_obj('lote', verts, faces, M['cesped'], C_TERRENO, 4.0)
    # calle (lado este)
    cx, cy, cw, cl, ang = LOTE['calle']
    box('calle', (cw, cl, 0.1), (-cw / 2, -cl / 2, -0.12), M['asfalto'], C_TERRENO, 2.0, rot=ang).location = (cx, cy, -0.12)
    box('acera', (cx - cw / 2 - 29.9, cl, 0.14), (29.9 - cx, -cl / 2, -0.12), M['acera'], C_TERRENO, 1.0, rot=ang).location = (cx, cy, -0.12)
    box('acera2', (1.8, cl, 0.12), (cw / 2, -cl / 2, -0.12), M['acera'], C_TERRENO, 1.0, rot=ang).location = (cx, cy, -0.12)
    # cerca perimetral: murete + barrotes en el lado de la calle
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0); a = math.atan2(y1 - y0, x1 - x0)
        if LOTE['cerca_calle'][i]:
            # murete 0.6 + barrotes
            mur = box(f'murete_{i}', (L, 0.2, 0.6), (0, -0.1, 0), M['amarillo'], C_EXT, 0.5, rot=a); mur.location = (x0, y0, 0)
            rail = box(f'rail_{i}', (L, 0.04, 0.04), (0, -0.02, 1.9), M['hierro'], C_EXT, rot=a); rail.location = (x0, y0, 0)
            rail2 = box(f'rail2_{i}', (L, 0.04, 0.04), (0, -0.02, 0.7), M['hierro'], C_EXT, rot=a); rail2.location = (x0, y0, 0)
            bars = []
            k = 0.0
            while k < L:
                b = box(f'bar_{i}_{k:.1f}', (0.025, 0.025, 1.4), (k, -0.012, 0.6), M['hierro'], C_EXT, rot=a); b.location = (x0, y0, 0)
                bars.append(b); k += 0.14
            pil = []
            k = 0.0
            while k <= L + 0.01:
                p = box(f'pilar_{i}_{k:.1f}', (0.4, 0.4, 2.2), (k - 0.2, -0.2, 0), M['amarillo'], C_EXT, 0.5, rot=a); p.location = (x0, y0, 0)
                pil.append(p)
                cap = box(f'pilarcap_{i}_{k:.1f}', (0.5, 0.5, 0.08), (k - 0.25, -0.25, 2.2), M['acera'], C_EXT, 0.5, rot=a); cap.location = (x0, y0, 0); pil.append(cap)
                pil.append(sphere(f'pilarbola_{i}_{k:.1f}', 0.14, (x0 + math.cos(a) * k, y0 + math.sin(a) * k, 2.46), M['ladrillo'], C_EXT, 2))
                k += 4.0
            join(bars + pil + [rail, rail2], f'reja_{i}')
        else:
            # cerca de malla sencilla (poste + alambre) para el resto
            k = 0.0
            posts = []
            while k <= L + 0.01:
                p = box(f'poste_{i}_{k:.1f}', (0.08, 0.08, 2.0), (k, -0.04, 0), M['hierro'], C_EXT, rot=a); p.location = (x0, y0, 0)
                posts.append(p); k += 3.0
            w = box(f'malla_{i}', (L, 0.01, 1.9), (0, 0, 0.1), mat('malla', color=(0.5, 0.5, 0.5, 1), alpha=0.25, metal=0.6), C_EXT, rot=a); w.location = (x0, y0, 0)
            join(posts + [w], f'cerca_{i}')
    # portón eléctrico (en la entrada)
    gx, gy, gw, ga = LOTE['porton']
    g1 = box('porton', (gw, 0.06, 0.4), (0, -0.03, 0.1), M['hierro'], C_EXT, rot=ga); g1.location = (gx, gy, 0)
    g2 = box('porton_top', (gw, 0.06, 0.08), (0, -0.03, 2.0), M['hierro'], C_EXT, rot=ga); g2.location = (gx, gy, 0); bars0 = [g2]
    bars = []
    k = 0.15
    while k < gw:
        b = box(f'pbar_{k:.1f}', (0.03, 0.09, 1.9), (k, -0.045, 0.15), M['hierro'], C_EXT, rot=ga); b.location = (gx, gy, 0); bars.append(b); k += 0.15
    join([g1] + bars0 + bars, 'porton_electrico')


# =====================================================================
#  EDIFICIO (muros + aberturas + pisos + mobiliario)
# =====================================================================
def segs_from_rooms(rooms, pu, pv, pw, pd):
    """Segmentos de muro únicos: une intervalos colineales para que no haya muros superpuestos."""
    lines = {}
    def add(axis, coord, a, b):
        lines.setdefault((axis, round(coord, 3)), []).append((round(min(a, b), 3), round(max(a, b), 3)))
    for r in rooms:
        u, v, w, d = r['rect']
        if r.get('abierto'):
            continue
        add('y', v, u, u + w); add('y', v + d, u, u + w); add('x', u, v, v + d); add('x', u + w, v, v + d)
    out = []
    for (axis, coord), ivs in lines.items():
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1] + 1e-6:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for a, b in merged:
            if axis == 'y':
                A, B = (a, coord), (b, coord)
                ext = coord in (pv, pv + pd)
            else:
                A, B = (coord, a), (coord, b)
                ext = coord in (pu, pu + pw)
            out.append((A, B, ext))
    return out


def lbox(name, size, loff, wall_loc, ang, m, pc, rot_extra=0.0):
    """Caja en coordenadas locales de un muro (loff = offset local; ang = rotación del muro)."""
    x = wall_loc[0] + math.cos(ang) * loff[0] - math.sin(ang) * loff[1]
    y = wall_loc[1] + math.sin(ang) * loff[0] + math.cos(ang) * loff[1]
    return box(name, size, (x, y, loff[2]), m, pc, 1.0, rot=ang + rot_extra)


def ventana(pfx, wall_loc, ang, cpos, ww, t, z0, pc, objs, rejas=True, dentro=1):
    """Ventana (marco + vidrio + rejas) en coordenadas locales del muro; devuelve el cortador."""
    cu = lbox(pfx + '_vcut', (ww, t + 0.6, 1.3), (cpos - ww / 2, -t / 2 - 0.3, z0 + 1.0), wall_loc, ang, None, pc)
    fr = lbox(pfx + '_vmarco', (ww + 0.06, t * 0.6, 1.36), (cpos - ww / 2 - 0.03, -t * 0.3, z0 + 0.97), wall_loc, ang, M['marco'], pc)
    fr2 = lbox(pfx + '_vmcut', (ww - 0.08, t + 0.5, 1.22), (cpos - ww / 2 + 0.04, -t / 2 - 0.25, z0 + 1.04), wall_loc, ang, None, pc)
    fr = cut(fr, [fr2])
    gl = lbox(pfx + '_vidrio', (ww - 0.06, 0.012, 1.24), (cpos - ww / 2 + 0.03, -0.006, z0 + 1.03), wall_loc, ang, M['vidrio'], pc)
    objs += [fr, gl]
    for k in (-1, 1):
        ct = lbox(pfx + '_cortina', (0.35, 0.08, 2.3), (cpos + k * (ww / 2 + 0.12) - 0.175, dentro * (t / 2 + 0.03) - (0.08 if dentro < 0 else 0), z0 + 0.25), wall_loc, ang, M['cortina'], pc)
        smooth(ct, 30); objs.append(ct)
    if rejas:
        rb = []
        k = 0.12
        while k < ww - 0.06:
            rb.append(lbox(pfx + '_reja', (0.015, 0.015, 1.3), (cpos - ww / 2 + k, -dentro * (t / 2 + 0.05), z0 + 1.0), wall_loc, ang, M['hierro'], pc))
            k += 0.14
        h1 = lbox(pfx + '_rejah', (ww - 0.06, 0.015, 0.015), (cpos - ww / 2 + 0.03, -dentro * (t / 2 + 0.05), z0 + 1.6), wall_loc, ang, M['hierro'], pc)
        objs.append(join(rb + [h1], pfx + '_rejas'))
    return cu


def build_edificio(E):
    """E: dict del programa (ver programa.py). Construye en un Empty padre con posición/rotación."""
    name = E['id']
    C = coll(f'Edificio_{name}')
    root = empty(f'{name}_root', (E['pos'][0], E['pos'][1], 0), E['rot'], C)
    W, D = E['huella']
    muro_ext = M[E['material_ext']]
    muro_int = M['blanco']
    objs = []
    nivel_max = 0
    for fi, piso in enumerate(E['pisos']):
        z0 = fi * NIVEL
        nivel_max = z0
        pc = coll(f'{name}_p{fi + 1}', C)
        pw, pd = piso.get('huella', (W, D))
        pu, pv = piso.get('offset', (0, 0))
        # losa de piso
        losa = box(f'{name}_p{fi + 1}_losa', (pw + 0.3, pd + 0.3, LOSA), (pu - 0.15, pv - 0.15, z0 - LOSA), M['concreto'], pc, 1.0)
        objs.append(losa)
        # piso de cada sala (textura) y cielo raso
        for r in piso['rooms']:
            u, v, w, d = r['rect']
            fm = M[r.get('piso', E['piso_default'])]
            fl = box(f'{name}_{r["id"]}_piso', (w, d, 0.02), (u, v, z0), fm, pc, 1.0)
            objs.append(fl)
            if not r.get('abierto'):
                cr = box(f'{name}_{r["id"]}_cielo', (w, d, 0.02), (u, v, z0 + ALTO - 0.02), M['cielo_raso'], pc, 1.0)
                cr['cielo'] = 1
                objs.append(cr)
                # paneles LED en el cielo raso
                npan = 1 if w * d < 14 else (2 if w * d < 40 else 4)
                for k in range(npan):
                    if npan <= 2:
                        px, py = u + w * (k + 0.5) / npan, v + d / 2
                    else:
                        px, py = u + w * ((k % 2) + 0.5) / 2, v + d * ((k // 2) + 0.5) / 2
                    lp = box(f'{name}_{r["id"]}_led{k}', (1.2, 0.6, 0.03), (px - 0.6, py - 0.3, z0 + ALTO - 0.06), M['led_panel'], pc, 1.0)
                    lp['cielo'] = 1
                    objs.append(lp)
        # zócalo oscuro al pie de los muros de cada sala (interior)
        for r in piso['rooms']:
            if r.get('abierto'):
                continue
            u, v, w, d = r['rect']
            zs = [box(f'{name}_zoc', (w, 0.02, 0.1), (u, v + INT / 2, z0), M['zocalo'], pc), box(f'{name}_zoc', (w, 0.02, 0.1), (u, v + d - INT / 2 - 0.02, z0), M['zocalo'], pc),
                  box(f'{name}_zoc', (0.02, d, 0.1), (u + INT / 2, v, z0), M['zocalo'], pc), box(f'{name}_zoc', (0.02, d, 0.1), (u + w - INT / 2 - 0.02, v, z0), M['zocalo'], pc)]
            objs.append(join(zs, f'{name}_{r["id"]}_zocalo'))
        # muros centrados en la línea del segmento
        segs = segs_from_rooms(piso['rooms'], pu, pv, pw, pd)
        walls = []   # (wall, a, ang, L, ext, cutters)
        for (a, b, ext) in segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            t = EXT if ext else INT
            wall = box(f'{name}_muro', (L + t, t, ALTO), (-t / 2, -t / 2, z0), muro_ext if ext else muro_int, pc, 1.0, rot=ang)
            wall.location = (a[0], a[1], z0)
            bpy.context.view_layer.update()
            wall['uv_scale'] = 1.0
            cutters = []
            if ext and L >= 2.4:
                # lado interior: hacia el centro de la planta
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                nrm = (-math.sin(ang), math.cos(ang))  # +y local
                dentro = 1 if (nrm[0] * (pu + pw / 2 - mid[0]) + nrm[1] * (pv + pd / 2 - mid[1])) > 0 else -1
                nwin = max(1, int(L // 3.4))
                for k in range(nwin):
                    cpos = (k + 0.5) * L / nwin
                    ww = min(1.6, L / nwin - 1.0)
                    cutters.append(ventana(f'{name}_v', (wall.location.x, wall.location.y), ang, cpos, ww, t, z0, pc, objs, rejas=True, dentro=dentro))
            walls.append([wall, a, ang, L, ext, cutters, t])
        # puertas definidas por sala: (lado, pos_relativa, ancho)
        for r in piso['rooms']:
            if r.get('abierto'):
                continue
            u, v, w, d = r['rect']
            for (lado, rel, ancho) in r.get('puertas', []):
                if lado == 's':   a = (u + rel, v); ang = 0
                elif lado == 'n': a = (u + rel, v + d); ang = 0
                elif lado == 'w': a = (u, v + rel); ang = math.pi / 2
                else:             a = (u + w, v + rel); ang = math.pi / 2
                best = None; bd = 1e9
                for wrec in walls:
                    wall, wa, wang, wL, wext, cs, t = wrec
                    dirv = Vector((math.cos(wang), math.sin(wang), 0))
                    rel_ = Vector((a[0] - wa[0], a[1] - wa[1], 0))
                    along = rel_.dot(dirv); perp = (rel_ - dirv * along).length
                    if perp < 0.2 and -0.05 <= along <= wL + 0.05 and perp < bd:
                        bd = perp; best = wrec
                if not best:
                    continue
                wall, wa, wang, wL, wext, cs, t = best
                dirv = Vector((math.cos(wang), math.sin(wang), 0))
                along = (Vector((a[0] - wa[0], a[1] - wa[1], 0))).dot(dirv)
                wl = (wall.location.x, wall.location.y)
                cu = lbox(f'{name}_pcut', (ancho, t + 0.6, 2.1), (along, -t / 2 - 0.3, z0), wl, wang, None, pc)
                cs.append(cu)
                pm = M['puerta_roja'] if E['id'] == 'gris' else M['puerta']
                mk = lbox(f'{name}_pmarco', (ancho + 0.12, t + 0.04, 2.16), (along - 0.06, -t / 2 - 0.02, z0 - 0.01), wl, wang, M['marco'], pc)
                mk2 = lbox(f'{name}_pmcut', (ancho - 0.08, t + 0.5, 2.06), (along + 0.04, -t / 2 - 0.25, z0 - 0.01), wl, wang, None, pc)
                objs.append(cut(mk, [mk2]))
                if r.get('puerta_abierta', True):
                    hoja = lbox(f'{name}_puerta', (ancho - 0.06, 0.045, 2.05), (along + 0.03, -0.02, z0 + 0.02), wl, wang, pm, pc, rot_extra=math.radians(25))
                    objs.append(hoja)
        for wrec in walls:
            wall, wa, wang, wL, wext, cs, t = wrec
            if cs:
                cut(wall, cs)
            objs.append(wall)
        # mobiliario
        for r in piso['rooms']:
            objs += build_mobiliario(name, r, z0, pc)
        # porches: columnas y techo
        for r in piso['rooms']:
            if r.get('tipo') == 'porche':
                u, v, w, d = r['rect']
                roof = box(f'{name}_{r["id"]}_techo', (w + 0.4, d + 0.4, 0.2), (u - 0.2, v - 0.2, z0 + ALTO - 0.2), M['blanco'], pc, 1.0); roof['techo'] = 1
                teja = box(f'{name}_{r["id"]}_teja', (w + 0.6, d + 0.6, 0.12), (u - 0.3, v - 0.3, z0 + ALTO), M['lamina_roja'], pc, 1.0); teja['techo'] = 1
                objs += [roof, teja]
                # columnas en el borde exterior (lado este) y esquinas
                xs = [u + w - 0.25]
                for yy in [v + 0.25 + k * (d - 0.5) / max(1, round(d / 3)) for k in range(round(d / 3) + 1)]:
                    col = box(f'{name}_{r["id"]}_col', (0.35, 0.35, ALTO), (u + w - 0.4, yy - 0.175, z0), M['blanco'], pc, 1.0)
                    objs.append(col)
                    # arco: viga con vano semicircular
                    arc = box(f'{name}_{r["id"]}_arco', (0.3, (d - 0.5) / max(1, round(d / 3)), 0.9), (u + w - 0.38, yy, z0 + ALTO - 1.0), M['blanco'], pc, 1.0)
                    cy = yy + (d - 0.5) / max(1, round(d / 3)) / 2
                    cu = cylinder(f'{name}_arccut', (d - 0.5) / max(1, round(d / 3)) / 2 - 0.2, 1.0, (u + w - 0.23, cy, z0 + ALTO - 1.0 - 0.5), None, pc, 24)
                    cu.rotation_euler = (0, math.pi / 2, 0); cu.location = (u + w - 0.23, cy, z0 + ALTO - 1.0)
                    bpy.context.view_layer.update()
                    objs.append(cut(arc, [cu]))
        # elementos de piso: terrazas con baranda, escalera
        for r in piso['rooms']:
            u, v, w, d = r['rect']
            if r.get('baranda'):
                for lado in r['baranda']:
                    if lado == 'n': a, L, ang = (u, v + d), w, 0
                    elif lado == 's': a, L, ang = (u, v), w, 0
                    elif lado == 'w': a, L, ang = (u, v), d, math.pi / 2
                    else: a, L, ang = (u + w, v), d, math.pi / 2
                    objs.append(baranda(f'{name}_baranda', a, L, ang, z0, pc, azul=(E['id'] == 'gris')))
            if r.get('escalera'):
                objs += escalera(name, r, z0, pc)
    # techo
    build_techo(E, (nivel_max + NIVEL) if E['techo'] != 'cuatro_aguas' else NIVEL, C, objs)
    if E['techo'] == 'cuatro_aguas' and len(E['pisos']) > 1:
        p2 = E['pisos'][1]; pw, pd = p2['huella']; pu, pv = p2.get('offset', (0, 0))
        build_techo(dict(E, huella=(pw, pd), id=E['id'] + '_p2'), 2 * NIVEL, C, objs, offset=(pu, pv))
    for o in objs:
        if o and o.parent is None:
            set_parent(o, root)
    for o in C.all_objects:
        if o.parent is None and o is not root:
            set_parent(o, root)
    return root


def canaleta(name, x0, y0, W, D, z, c, objs, bajantes=True, lados='nsew'):
    """Canaleta perimetral (perfil blanco) y bajantes en las esquinas."""
    g = 0.13
    if 's' in lados: objs.append(box(name + '_s', (W + 2 * g, g, g), (x0 - g, y0 - g, z), M['baranda_b'], c))
    if 'n' in lados: objs.append(box(name + '_n', (W + 2 * g, g, g), (x0 - g, y0 + D, z), M['baranda_b'], c))
    if 'w' in lados: objs.append(box(name + '_w', (g, D, g), (x0 - g, y0, z), M['baranda_b'], c))
    if 'e' in lados: objs.append(box(name + '_e', (g, D, g), (x0 + W, y0, z), M['baranda_b'], c))
    if bajantes:
        for (bx, by) in ((x0 - g, y0 - g), (x0 + W, y0 - g), (x0 - g, y0 + D), (x0 + W, y0 + D)):
            objs.append(box(name + '_baj', (0.09, 0.09, z - 0.1), (bx + 0.02, by + 0.02, 0.1), M['baranda_b'], c))


def aire_acondicionado(name, x, y, z, ang, c):
    """Unidad condensadora en la fachada; (x, y) es el punto en el muro, ang la normal exterior."""
    parts = []
    b = box(name, (0.82, 0.32, 0.56), (-0.41, 0.04, 0), M['ac_blanco'], c, rot=ang); b.location = (x, y, z); parts.append(b)
    r = box(name + '_r', (0.6, 0.02, 0.44), (-0.3, 0.355, 0.06), M['ac_rejilla'], c, rot=ang); r.location = (x, y, z); parts.append(r)
    for k in (-0.3, 0.3):
        s = box(name + '_s', (0.05, 0.4, 0.03), (k - 0.025, -0.02, -0.03), M['hierro'], c, rot=ang); s.location = (x, y, z); parts.append(s)
        t = box(name + '_t', (0.05, 0.03, 0.3), (k - 0.025, -0.02, -0.33), M['hierro'], c, rot=ang); t.location = (x, y, z); parts.append(t)
    return join(parts, name)


def baranda(name, a, L, ang, z0, c, azul=False):
    parts = []
    top = box(name, (L, 0.06, 0.06), (0, -0.03, z0 + 1.05), M['baranda_b'], c, rot=ang); top.location = (a[0], a[1], z0 + 0.0); top.location.z = z0
    parts.append(top)
    mid = box(name + '_m', (L, 0.04, 0.04), (0, -0.02, z0 + 0.55), M['baranda_b'], c, rot=ang); mid.location = (a[0], a[1], 0); mid.location.z = z0
    parts.append(mid)
    k = 0.0
    while k <= L + 0.01:
        p = box(name + '_p', (0.05, 0.05, 1.08), (k - 0.025, -0.025, z0), M['azul'] if azul else M['baranda_b'], c, rot=ang); p.location = (a[0], a[1], 0); p.location.z = z0
        parts.append(p); k += 1.5
    # zócalo azul (como en las fotos de la terraza)
    if azul:
        zo = box(name + '_z', (L, 0.12, 0.12), (0, -0.12, z0), M['azul_p'], c, rot=ang); zo.location = (a[0], a[1], 0); zo.location.z = z0
        parts.append(zo)
    return join(parts, name)


def escalera(name, r, z0, c):
    u, v, w, d = r['rect']
    n = 16
    objs = []
    rise = NIVEL / n
    run = (d - 1.0) / n
    for i in range(n):
        s = box(f'{name}_esc', (w - 0.3, run + 0.02, rise), (u + 0.15, v + 0.5 + i * run, z0 + i * rise), M['ceramica_g'], c, 1.0)
        objs.append(s)
    st = join(objs, f'{name}_escalera')
    rail = box(f'{name}_esc_rail', (0.05, d - 1.0, 0.05), (u + 0.15, v + 0.5, z0 + 0.9), M['hierro'], c)
    rail.rotation_euler = (math.atan2(NIVEL, d - 1.0), 0, 0)
    return [st, rail]


def build_techo(E, ztop, C, objs, offset=(0, 0)):
    W, D = E['huella']
    if E['techo'] != 'cuatro_aguas':
        W = max([W] + [p.get('huella', (W, D))[0] for p in E['pisos']]); D = max([D] + [p.get('huella', (W, D))[1] for p in E['pisos']])
    name = E['id']
    tc = coll(f'{name}_techo', C)
    ox, oy = offset
    if E['techo'] == 'cuatro_aguas':
        # techo de tejas a cuatro aguas con alero
        al = 0.9; h = 2.6
        v = [(ox - al, oy - al, ztop), (ox + W + al, oy - al, ztop), (ox + W + al, oy + D + al, ztop), (ox - al, oy + D + al, ztop),
             (ox + W * 0.3, oy + D * 0.5, ztop + h), (ox + W * 0.7, oy + D * 0.5, ztop + h)]
        f = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
        t = mesh_obj(f'{name}_techo', v, f, M['lamina_roja'], tc, 1.0)
        t['techo'] = 1
        canaleta(f'{name}_canal', ox - al, oy - al, W + 2 * al, D + 2 * al, ztop - 0.1, tc, objs, bajantes=True)
        # cielo del alero
        s = box(f'{name}_alero', (W + 2 * al, D + 2 * al, 0.15), (ox - al, oy - al, ztop - 0.15), M['blanco'], tc, 1.0); s['techo'] = 1
        objs += [t, s]
    else:
        # losa + parapeto + techo de lámina a dos aguas de baja pendiente
        losa = box(f'{name}_losa_techo', (W + 0.3, D + 0.3, LOSA), (-0.15, -0.15, ztop - LOSA), M['concreto'], tc, 1.0); losa['techo'] = 1
        objs.append(losa)
        h = 1.6; al = 0.6
        v = [(-al, -al, ztop + 0.2), (W + al, -al, ztop + 0.2), (W + al, D + al, ztop + 0.2), (-al, D + al, ztop + 0.2),
             (-al, D / 2, ztop + 0.2 + h), (W + al, D / 2, ztop + 0.2 + h)]
        f = [(0, 1, 5, 4), (3, 2, 5, 4), (0, 4, 3), (1, 2, 5)]
        t = mesh_obj(f'{name}_techo', v, f, M['lamina'], tc, 1.0); t['techo'] = 1
        objs.append(t)
        canaleta(f'{name}_canal', -al, -al, W + 2 * al, D + 2 * al, ztop + 0.1, tc, objs, bajantes=True, lados='ns')
        # estructura: pequeñas columnas en el frente
        for x in (0.5, W - 0.5):
            for y in (0.5, D - 0.5):
                cpost = box(f'{name}_tpost', (0.2, 0.2, 0.4), (x - 0.1, y - 0.1, ztop), M['concreto'], tc); cpost['techo'] = 1
                objs.append(cpost)


# =====================================================================
#  MOBILIARIO
# =====================================================================
def cama_hospital(pfx, u, v, z0, rot, c):
    """Cama hospitalaria: base, colchón redondeado, sábana, cobija, almohada, cabecera, rieles tubulares, mesita y luz."""
    parts = []
    def B(nm, size, center, m):
        o = cbox(nm, size, (0, 0, 0), m, c); o.location = (center[0], center[1], z0 + center[2]); return o
    def T(nm, r, h, center, m, rot=(0, 0, 0)):
        o = cylinder(nm, r, h, (0, 0, 0), m, c, 10); o.location = (center[0], center[1], z0 + center[2]); o.rotation_euler = rot; return o
    parts.append(B(f'{pfx}_base', (0.9, 2.0, 0.12), (0, 0, 0.42), M['cama_metal']))
    parts.append(B(f'{pfx}_chasis', (0.6, 1.4, 0.16), (0, 0, 0.26), M['cama_metal']))
    for sx in (-0.38, 0.38):
        for sy in (-0.8, 0.8):
            parts.append(T(f'{pfx}_rueda', 0.06, 0.05, (sx, sy, 0.06), M['hierro'], (math.pi / 2, 0, 0)))
            parts.append(B(f'{pfx}_pata', (0.04, 0.04, 0.3), (sx, sy, 0.22), M['cama_metal']))
    col = B(f'{pfx}_colchon', (0.88, 1.98, 0.2), (0, 0, 0.58), M['colchon']); smooth(col, 30); col.modifiers['bevel'].width = 0.05; parts.append(col)
    sab = B(f'{pfx}_sabana', (0.94, 1.25, 0.1), (0, 0.38, 0.7), M['sabana']); smooth(sab, 30); sab.modifiers['bevel'].width = 0.04; parts.append(sab)
    cob = B(f'{pfx}_cobija', (0.96, 0.5, 0.12), (0, 0.72, 0.73), M['cobija']); smooth(cob, 30); cob.modifiers['bevel'].width = 0.05; parts.append(cob)
    alm = B(f'{pfx}_almohada', (0.6, 0.42, 0.14), (0, -0.74, 0.76), M['almohada']); smooth(alm, 30); alm.modifiers['bevel'].width = 0.05; parts.append(alm)
    cab = B(f'{pfx}_cabecera', (0.96, 0.05, 0.75), (0, -1.03, 0.78), M['cama_cabecera']); smooth(cab, 30); parts.append(cab)
    pie = B(f'{pfx}_piecera', (0.96, 0.05, 0.5), (0, 1.03, 0.62), M['cama_cabecera']); smooth(pie, 30); parts.append(pie)
    for sx in (-0.47, 0.47):
        parts.append(T(f'{pfx}_rail', 0.015, 1.05, (sx, 0.05, 0.98), M['cama_metal'], (math.pi / 2, 0, 0)))
        parts.append(T(f'{pfx}_rail2', 0.015, 1.05, (sx, 0.05, 0.86), M['cama_metal'], (math.pi / 2, 0, 0)))
        for k in (-0.45, -0.15, 0.15, 0.45):
            parts.append(T(f'{pfx}_railp', 0.012, 0.32, (sx, 0.05 + k, 0.82), M['cama_metal']))
    # mesita de noche con cajón
    mes = B(f'{pfx}_mesita', (0.45, 0.45, 0.68), (0.76, -0.72, 0.34), M['mesita']); smooth(mes, 30); parts.append(mes)
    parts.append(B(f'{pfx}_mesita_top', (0.48, 0.48, 0.03), (0.76, -0.72, 0.695), M['mesita_top']))
    parts.append(B(f'{pfx}_tirador', (0.12, 0.02, 0.02), (0.76, -0.49, 0.5), M['cama_metal']))
    # luz LED sobre la cabecera
    parts.append(B(f'{pfx}_led', (0.7, 0.05, 0.05), (0, -1.1, 2.0), M['led']))
    ob = join(parts, pfx)
    ob.rotation_euler = (0, 0, rot); ob.location = (u, v, 0)
    return ob


def cama_simple(pfx, u, v, z0, rot, c):
    parts = []
    def B(nm, size, center, m):
        o = cbox(nm, size, (0, 0, 0), m, c); o.location = (center[0], center[1], z0 + center[2]); return o
    parts.append(B(f'{pfx}_base', (1.5, 2.0, 0.35), (0, 0, 0.2), M['madera']))
    parts.append(B(f'{pfx}_colchon', (1.45, 1.95, 0.2), (0, 0, 0.47), M['colchon']))
    parts.append(B(f'{pfx}_sabana', (1.47, 1.3, 0.05), (0, 0.3, 0.6), mat('sabana_b', color=(0.8, 0.72, 0.6, 1), rough=0.95)))
    parts.append(B(f'{pfx}_alm1', (0.6, 0.4, 0.12), (-0.38, -0.7, 0.62), M['almohada']))
    parts.append(B(f'{pfx}_alm2', (0.6, 0.4, 0.12), (0.38, -0.7, 0.62), M['almohada']))
    parts.append(B(f'{pfx}_cab', (1.55, 0.06, 1.1), (0, -1.02, 0.6), M['madera']))
    parts.append(B(f'{pfx}_mesita', (0.45, 0.45, 0.55), (1.0, -0.75, 0.28), M['mesita']))
    ob = join(parts, pfx); ob.rotation_euler = (0, 0, rot); ob.location = (u, v, 0)
    return ob


def silla(pfx, u, v, z0, rot, c, m=None):
    m = m or M['tela_rojo']
    parts = []
    def B(nm, size, center, mm):
        o = cbox(nm, size, (0, 0, 0), mm, c); o.location = (center[0], center[1], z0 + center[2]); return o
    a = B(f'{pfx}_as', (0.46, 0.46, 0.08), (0, 0, 0.46), m); smooth(a, 30); a.modifiers['bevel'].width = 0.03; parts.append(a)
    r = B(f'{pfx}_re', (0.46, 0.06, 0.44), (0, 0.2, 0.72), m); smooth(r, 30); r.modifiers['bevel'].width = 0.025; parts.append(r)
    parts.append(B(f'{pfx}_marco', (0.44, 0.44, 0.03), (0, 0, 0.41), M['madera']))
    for sx in (-0.19, 0.19):
        for sy in (-0.19, 0.19):
            parts.append(B(f'{pfx}_p', (0.035, 0.035, 0.42), (sx, sy, 0.21), M['madera']))
    ob = join(parts, pfx); ob.rotation_euler = (0, 0, rot); ob.location = (u, v, 0)
    return ob


def mesa(pfx, u, v, z0, w, d, c, m=None, h=0.75):
    m = m or M['madera']
    parts = []
    t = cbox(f'{pfx}_t', (w, d, 0.04), (0, 0, 0), m, c); t.location = (0, 0, z0 + h - 0.02); parts.append(t)
    for sx in (-w / 2 + 0.06, w / 2 - 0.06):
        for sy in (-d / 2 + 0.06, d / 2 - 0.06):
            p = cbox(f'{pfx}_p', (0.06, 0.06, h - 0.04), (0, 0, 0), M['madera'], c); p.location = (sx, sy, z0 + (h - 0.04) / 2); parts.append(p)
    ob = join(parts, pfx); ob.location = (u, v, 0)
    return ob


def build_mobiliario(name, r, z0, c):
    u, v, w, d = r['rect']
    out = []
    pf = f'{name}_{r["id"]}'
    tipo = r.get('tipo')
    if tipo == 'hospital':
        n = r['camas']
        por_fila = math.ceil(n / 2)
        margen = 3.0 if r.get('estacion') else 0.7
        paso = (w - margen - 0.7) / por_fila
        for i in range(n):
            fila = 0 if i < por_fila else 1
            col = i if fila == 0 else i - por_fila
            cx = u + 0.7 + paso * (col + 0.5)
            if fila == 0:
                out.append(cama_hospital(f'{pf}_cama{i}', cx, v + 1.12, z0, 0, c))
            else:
                out.append(cama_hospital(f'{pf}_cama{i}', cx, v + d - 1.12, z0, math.pi, c))
        if r.get('estacion'):
            ex = u + w - 1.6
            out.append(mesa(f'{pf}_est', ex, v + d / 2, z0, 2.2, 0.8, c, M['estacion'], 1.05))
            out.append(mesa(f'{pf}_est2', ex, v + d / 2, z0, 2.0, 0.7, c, M['estacion'], 0.75))
            out.append(silla(f'{pf}_sillaE', ex + 0.6, v + d / 2, z0, math.pi / 2, c, M['tela_gris']))
    elif tipo == 'habitacion':
        out.append(cama_simple(f'{pf}_cama', u + w / 2, v + 1.1, z0, 0, c))
        ar = cbox(f'{pf}_closet', (0.6, 1.6, 2.1), (0, 0, 0), M['madera'], c); ar.location = (u + 0.3, v + d - 0.9, z0 + 1.05); out.append(ar)
    elif tipo == 'comedor':
        out.append(arbusto(f'{pf}_planta', u + 0.6, v + d - 0.6, 0.45, c))
        nm = max(1, int((w * d) // 9))
        k = 0
        for i in range(nm):
            cx = u + w / 2; cy = v + (i + 0.5) * d / nm
            out.append(mesa(f'{pf}_mesa{i}', cx, cy, z0, 1.6, 0.9, c, M['mantel']))
            for sx, rot in ((-1.05, math.pi / 2), (1.05, -math.pi / 2)):
                for sy in (-0.35, 0.35):
                    out.append(silla(f'{pf}_s{k}', cx + sx, cy + sy, z0, rot, c)); k += 1
    elif tipo == 'conferencia':
        pass
    elif tipo == 'oficina':
        out.append(mesa(f'{pf}_esc', u + w / 2, v + 1.0, z0, 1.5, 0.7, c, M['madera']))
        out.append(silla(f'{pf}_s', u + w / 2, v + 1.7, z0, math.pi, c, M['tela_gris']))
        out.append(silla(f'{pf}_s2', u + w / 2 - 0.4, v + 0.3, z0, 0, c, M['tela_gris']))
        out.append(silla(f'{pf}_s3', u + w / 2 + 0.4, v + 0.3, z0, 0, c, M['tela_gris']))
    elif tipo == 'cocina':
        cnt = cbox(f'{pf}_meson', (w - 0.4, 0.6, 0.9), (0, 0, 0), M['madera'], c); cnt.location = (u + w / 2, v + d - 0.3, z0 + 0.45); out.append(cnt)
        top = cbox(f'{pf}_granito', (w - 0.36, 0.64, 0.04), (0, 0, 0), M['granito'], c); top.location = (u + w / 2, v + d - 0.3, z0 + 0.92); out.append(top)
        alto = cbox(f'{pf}_alacena', (w - 0.6, 0.35, 0.7), (0, 0, 0), M['madera'], c); alto.location = (u + w / 2, v + d - 0.18, z0 + 1.9); out.append(alto)
        est = cbox(f'{pf}_estufa', (0.6, 0.6, 0.02), (0, 0, 0), M['hierro'], c); est.location = (u + 1.0, v + d - 0.3, z0 + 0.95); out.append(est)
        out.append(mesa(f'{pf}_mesa', u + w / 2, v + 1.2, z0, 1.2, 0.8, c, M['mantel']))
    elif tipo == 'bano':
        wc = cbox(f'{pf}_wc', (0.4, 0.6, 0.4), (0, 0, 0), M['porcelana'], c); wc.location = (u + 0.4, v + d - 0.4, z0 + 0.2); out.append(wc)
        tk = cbox(f'{pf}_tanque', (0.4, 0.18, 0.4), (0, 0, 0), M['porcelana'], c); tk.location = (u + 0.4, v + d - 0.12, z0 + 0.6); out.append(tk)
        lv = cbox(f'{pf}_lav', (0.5, 0.4, 0.15), (0, 0, 0), M['porcelana'], c); lv.location = (u + w - 0.5, v + d - 0.25, z0 + 0.82); out.append(lv)
        if r.get('regadera'):
            rg = cbox(f'{pf}_regadera', (0.03, 0.03, 2.0), (0, 0, 0), M['cama_metal'], c); rg.location = (u + w - 0.3, v + 0.3, z0 + 1.0); out.append(rg)
        # azulejo rojo (como en las fotos)
        az = box(f'{pf}_azulejo', (w - 0.02, 0.02, 1.6), (u + 0.01, v + d - 0.14, z0), M['rojo_tile'], c); out.append(az)
    elif tipo == 'sala':
        for i, (sx, sy, rot) in enumerate(((0, -1.0, 0), (-1.3, 0.3, math.pi / 2), (1.3, 0.3, -math.pi / 2))):
            so = cbox(f'{pf}_sofa{i}', (1.8 if rot == 0 else 0.8, 0.8 if rot == 0 else 1.8, 0.45), (0, 0, 0), M['tela_rojo'], c)
            so.location = (u + w / 2 + sx, v + d / 2 + sy, z0 + 0.22); out.append(so)
            re = cbox(f'{pf}_resp{i}', (1.8 if rot == 0 else 0.25, 0.25 if rot == 0 else 1.8, 0.45), (0, 0, 0), M['tela_rojo'], c)
            re.location = (u + w / 2 + sx + (0 if rot == 0 else (-0.28 if sx < 0 else 0.28)), v + d / 2 + sy + (-0.28 if rot == 0 else 0), z0 + 0.65); out.append(re)
        out.append(mesa(f'{pf}_centro', u + w / 2, v + d / 2 + 0.3, z0, 1.0, 0.6, c, M['madera'], 0.45))
    elif tipo == 'taller':
        out.append(mesa(f'{pf}_mesa', u + w / 2, v + d / 2, z0, min(3.0, w - 1.4), 1.1, c, M['mantel']))
        for i, sx in enumerate((-1.0, 0, 1.0)):
            out.append(silla(f'{pf}_s{i}', u + w / 2 + sx, v + d / 2 - 0.85, z0, 0, c, M['tela_gris']))
            out.append(silla(f'{pf}_t{i}', u + w / 2 + sx, v + d / 2 + 0.85, z0, math.pi, c, M['tela_gris']))
    elif tipo == 'terapia':
        for i in range(2):
            out.append(cama_hospital(f'{pf}_cam{i}', u + 1.2 + i * 2.2, v + 1.2, z0, 0, c))
        out.append(mesa(f'{pf}_mesa', u + w - 1.5, v + d - 1.0, z0, 1.4, 0.7, c, M['madera']))
    elif tipo == 'recepcion':
        out.append(arbusto(f'{pf}_planta', u + w - 0.6, v + d - 0.6, 0.45, c))
        out.append(mesa(f'{pf}_mostrador', u + w / 2, v + 1.0, z0, min(2.2, w - 1), 0.7, c, M['madera'], 1.0))
        out.append(silla(f'{pf}_s', u + w / 2, v + 1.7, z0, math.pi, c, M['tela_gris']))
    elif tipo == 'deposito':
        for i in range(max(1, int(w // 1.2))):
            sh = cbox(f'{pf}_est{i}', (1.0, 0.4, 2.0), (0, 0, 0), M['hierro'], c); sh.location = (u + 0.6 + i * 1.2, v + d - 0.25, z0 + 1.0); out.append(sh)
    elif tipo == 'lavanderia':
        for i in range(2):
            lw = cbox(f'{pf}_lav{i}', (0.6, 0.6, 0.85), (0, 0, 0), M['porcelana'], c); lw.location = (u + 0.5 + i * 0.7, v + d - 0.35, z0 + 0.43); out.append(lw)
    return out


# =====================================================================
#  EXTERIORES
# =====================================================================
LEAF = None
FROND = None
BUSH = None


def _leafmats():
    global LEAF, FROND, BUSH
    if LEAF is None:
        LEAF = leaf_mat('follaje', f'{TEX}/leaf_cluster.png')
        FROND = leaf_mat('fronda', f'{TEX}/palm_frond.png')
        BUSH = leaf_mat('arbusto', f'{TEX}/leaf_cluster.png')


def arbol(name, x, y, h=8.0, c=None):
    _leafmats()
    c = c or C_VEG
    parts = []
    tr = cylinder(f'{name}_tronco', 0.22 * h / 8, h * 0.5, (0, 0, 0), M['tronco'], c, 10, r2=0.12 * h / 8)
    parts.append(tr)
    for i in range(4):
        a = i * 1.7 + random.random()
        br = cylinder(f'{name}_rama{i}', 0.07, h * 0.32, (0, 0, 0), M['tronco'], c, 6, r2=0.03)
        br.rotation_euler = (math.radians(40), 0, a)
        br.location = (0, 0, h * 0.45)
        parts.append(br)
    rc = h * 0.4
    cz = h * 0.68
    # masa interior oscura
    for i in range(3):
        s = sphere(f'{name}_masa{i}', rc * 0.38, ((random.random() - 0.5) * rc * 0.6, (random.random() - 0.5) * rc * 0.6, cz + (random.random() - 0.5) * rc * 0.4), M['hoja'], c, 2)
        parts.append(s)
    # cartas de follaje
    n = 34
    for i in range(n):
        u = random.random() * 2 * math.pi; v = math.acos(2 * random.random() - 1)
        rad = rc * (0.55 + 0.45 * random.random())
        px = math.cos(u) * math.sin(v) * rad; py = math.sin(u) * math.sin(v) * rad; pz = cz + math.cos(v) * rad * 0.75
        size = rc * (0.9 + 0.5 * random.random())
        cd = card(f'{name}_hoja{i}', size, size, LEAF, c, 'center')
        cd.location = (px, py, pz)
        cd.rotation_euler = (random.random() * math.pi, random.random() * math.pi, random.random() * math.pi)
        parts.append(cd)
    ob = join(parts, name); ob.location = (x, y, 0)
    ob.rotation_euler = (0, 0, random.random() * 6.28)
    return ob


def palma(name, x, y, h=7.0, c=None):
    _leafmats()
    c = c or C_VEG
    parts = []
    lean = math.radians(3 + random.random() * 5)
    tr = cylinder(f'{name}_tronco', 0.22, h, (0, 0, 0), M['tronco'], c, 10, r2=0.15)
    tr.rotation_euler = (lean, 0, 0)
    parts.append(tr)
    top = Vector((0, -math.sin(lean) * h, math.cos(lean) * h))
    nf = 13
    for i in range(nf):
        a = i * (2 * math.pi / nf) + random.random() * 0.3
        fr = card(f'{name}_fronda{i}', 1.3, 3.6, FROND, c, 'bottom')
        # la fronda nace en la copa y cae hacia afuera: rotación X negativa (apunta hacia -Z) y giro en Z
        fr.rotation_euler = (math.radians(-(62 + 30 * random.random())), 0, a)
        fr.location = (top.x, top.y, top.z - 0.1)
        parts.append(fr)
    # cocos / corona
    parts.append(sphere(f'{name}_corona', 0.35, (top.x, top.y, top.z - 0.1), M['tronco'], c, 1))
    ob = join(parts, name); ob.location = (x, y, 0)
    return ob


def arbusto(name, x, y, r=0.8, c=None):
    _leafmats()
    c = c or C_VEG
    parts = [sphere(f'{name}_m', r * 0.7, (0, 0, r * 0.6), M['hoja'], c, 1)]
    for i in range(6):
        a = i * 1.05
        cd = card(f'{name}_c{i}', r * 2.0, r * 2.0, BUSH, c, 'center')
        cd.location = (math.cos(a) * r * 0.3, math.sin(a) * r * 0.3, r * 0.8)
        cd.rotation_euler = (random.random() * 1.2, 0, a)
        parts.append(cd)
    ob = join(parts, name); ob.location = (x, y, 0)
    return ob


def build_exteriores():
    for el in ELEMENTOS:
        t = el['tipo']; x, y = el.get('pos', (0, 0))
        if t == 'gazebo':
            r = el['r']
            cylinder('gazebo_piso', r, 0.3, (x, y, 0), M['acera'], C_EXT, 8)
            for i in range(8):
                a = i * math.pi / 4 + math.pi / 8
                cylinder(f'gazebo_col{i}', 0.12, 2.8, (x + math.cos(a) * (r - 0.3), y + math.sin(a) * (r - 0.3), 0.3), M['madera'], C_EXT, 8)
            tp = cylinder('gazebo_techo', r + 0.5, 1.6, (x, y, 3.1), M['teja'], C_EXT, 8, r2=0.05)
            cylinder('gazebo_anillo', r + 0.5, 0.15, (x, y, 3.0), M['madera'], C_EXT, 8)
            for i, (dx, dy) in enumerate(((-1.3, 0), (1.3, 0), (0, -1.3), (0, 1.3))):
                mesa(f'gazebo_mesa{i}', x + dx, y + dy, 0.3, 0.8, 0.8, C_EXT, M['mantel'])
                silla(f'gazebo_s{i}a', x + dx + 0.6, y + dy, 0.3, -math.pi / 2, C_EXT, M['tela_gris'])
                silla(f'gazebo_s{i}b', x + dx - 0.6, y + dy, 0.3, math.pi / 2, C_EXT, M['tela_gris'])
        elif t == 'piscina':
            r = el['r']
            cylinder('hidro_borde', r + 0.7, 0.45, (x, y, 0), M['acera'], C_EXT, 32)
            cylinder('hidro_agua', r, 0.05, (x, y, 0.42), M['agua'], C_EXT, 32)
            for i in range(4):
                a = i * math.pi / 2 + math.pi / 4
                cylinder(f'hidro_col{i}', 0.12, 2.6, (x + math.cos(a) * (r + 0.4), y + math.sin(a) * (r + 0.4), 0.45), M['madera'], C_EXT, 8)
            # pérgola
            for i in range(7):
                k = -r - 0.5 + i * (2 * r + 1) / 6
                box(f'hidro_perg{i}', (2 * r + 1.4, 0.12, 0.08), (x - r - 0.7, y + k, 3.0), M['madera'], C_EXT)
            box('hidro_perg_a', (0.12, 2 * r + 1.0, 0.12), (x - r - 0.5, y - r - 0.5, 2.95), M['madera'], C_EXT)
            box('hidro_perg_b', (0.12, 2 * r + 1.0, 0.12), (x + r + 0.4, y - r - 0.5, 2.95), M['madera'], C_EXT)
        elif t == 'huerto':
            w, d = el['tam']
            box('huerto_tierra', (w, d, 0.1), (x, y, -0.05), M['tierra'], C_EXT, 1.0)
            for i in range(4):
                sy = y + 0.6 + i * (d - 1.2) / 3
                box(f'huerto_surco{i}', (w - 1.0, 0.5, 0.25), (x + 0.5, sy - 0.25, 0.0), M['tierra'], C_EXT, 1.0)
                for k in range(int((w - 1.0) // 0.6)):
                    arbusto(f'huerto_pl{i}_{k}', x + 0.8 + k * 0.6, sy, 0.22 + 0.08 * random.random(), C_EXT)
            # cerca baja de madera
            for (ax, ay, L, ang) in ((x, y, w, 0), (x, y + d, w, 0), (x, y, d, math.pi / 2), (x + w, y, d, math.pi / 2)):
                k = 0
                while k <= L + 0.01:
                    p = box(f'huerto_post', (0.08, 0.08, 1.1), (k, -0.04, 0), M['madera'], C_EXT, rot=ang); p.location = (ax, ay, 0); k += 1.5
                r1 = box('huerto_rail', (L, 0.04, 0.08), (0, -0.02, 0.95), M['madera'], C_EXT, rot=ang); r1.location = (ax, ay, 0)
                r2 = box('huerto_rail2', (L, 0.04, 0.08), (0, -0.02, 0.5), M['madera'], C_EXT, rot=ang); r2.location = (ax, ay, 0)
        elif t == 'estacionamiento':
            w, d = el['tam']
            box('estac_grava', (w, d, 0.06), (x, y, -0.04), M['grava'], C_EXT, 1.0)
            for i in range(2):
                box(f'estac_azul{i}', (2.6, 5.0, 0.01), (x + 0.6 + i * 3.0, y + d - 5.2, 0.021), M['azul_p'], C_EXT)
                box(f'estac_linea{i}', (0.1, 5.0, 0.012), (x + 0.6 + i * 3.0, y + d - 5.2, 0.022), M['porcelana'], C_EXT)
        elif t == 'camino':
            # camino de losas
            (x1, y1), (x2, y2) = el['de'], el['a']
            L = math.hypot(x2 - x1, y2 - y1); a = math.atan2(y2 - y1, x2 - x1)
            k = 0
            while k < L:
                s = box('camino_losa', (0.9, 1.2, 0.05), (k, -0.6, 0.0), M['acera'], C_EXT, rot=a); s.location = (x1, y1, 0); k += 1.1
        elif t == 'rampa':
            w, L, ang = el['w'], el['L'], el['ang']
            r = box('rampa', (L, w, 0.1), (0, -w / 2, 0.0), M['acera'], C_EXT, rot=ang); r.location = (x, y, 0)
            r.rotation_euler = (0, math.radians(-4), ang)
            for sy in (-w / 2, w / 2):
                rl = box('rampa_rail', (L, 0.04, 0.04), (0, sy - 0.02, 0.9), M['hierro'], C_EXT, rot=ang); rl.location = (x, y, 0); rl.rotation_euler = (0, math.radians(-4), ang)
                k = 0
                while k <= L:
                    p = box('rampa_post', (0.04, 0.04, 0.9), (k, sy - 0.02, 0.0), M['hierro'], C_EXT, rot=ang); p.location = (x, y, 0); p.rotation_euler = (0, math.radians(-4), ang); k += 1.5
        elif t == 'garage':
            # entrada circular de adoquín frente a la casa amarilla
            x, y, r = el['pos'][0], el['pos'][1], el['r']
            cylinder('garage_circ', r, 0.06, (x, y, -0.04), M['ceramica'], C_EXT, 40)
            cylinder('garage_centro', r * 0.35, 0.3, (x, y, 0.0), M['cesped'], C_EXT, 24)
            arbusto('garage_arb', x, y, 0.8)
            palma('garage_palma', x + 0.3, y - 0.3, 4.5)
    # bancas y faroles junto a los caminos
    for i, (x, y, a) in enumerate(((24, 52, 0.3), (18, 42, 1.2), (28, 38, 0.0), (12, 40, -0.3))):
        b1 = box(f'banca{i}_as', (1.6, 0.45, 0.06), (-0.8, -0.22, 0.42), M['banca'], C_EXT, rot=a); b1.location = (x, y, 0)
        b2 = box(f'banca{i}_re', (1.6, 0.06, 0.4), (-0.8, 0.2, 0.48), M['banca'], C_EXT, rot=a); b2.location = (x, y, 0)
        p1 = box(f'banca{i}_p1', (0.06, 0.45, 0.42), (-0.75, -0.22, 0), M['hierro'], C_EXT, rot=a); p1.location = (x, y, 0)
        p2 = box(f'banca{i}_p2', (0.06, 0.45, 0.42), (0.7, -0.22, 0), M['hierro'], C_EXT, rot=a); p2.location = (x, y, 0)
        join([b1, b2, p1, p2], f'banca{i}')
    for i, (x, y) in enumerate(((26, 58), (23, 46), (21, 34), (28, 24), (8, 44), (14, 50))):
        cylinder(f'farol{i}_poste', 0.04, 2.6, (x, y, 0), M['hierro'], C_EXT, 8)
        box(f'farol{i}_luz', (0.3, 0.3, 0.35), (x - 0.15, y - 0.15, 2.6), mat('farol_vidrio', color=(1, 0.95, 0.8, 1), rough=0.2, alpha=0.6), C_EXT)
    # jardineras con flores al pie de la casa amarilla y del edificio gris
    random.seed(21)
    for (x0, y0, L, ang) in ((AMARILLA['pos'][0] + 16 + 3.2, AMARILLA['pos'][1] + 0.5, 8, math.pi / 2), (GRIS['pos'][0] + 26.3, GRIS['pos'][1] + 0.5, 11, math.pi / 2), (AMARILLA['pos'][0] - 0.8, AMARILLA['pos'][1] + 1, 12, math.pi / 2)):
        jb = box('jardinera', (L, 0.6, 0.3), (0, -0.3, 0), M['acera'], C_EXT, rot=ang); jb.location = (x0, y0, 0)
        for k in range(int(L / 0.5)):
            px = x0 + math.cos(ang) * (k * 0.5 + 0.25); py = y0 + math.sin(ang) * (k * 0.5 + 0.25)
            arbusto(f'jflor_{x0}_{k}', px, py, 0.28, C_EXT)
            for j in range(3):
                sphere(f'flor_{x0}_{k}_{j}', 0.05, (px + random.uniform(-0.2, 0.2), py + random.uniform(-0.2, 0.2), 0.5 + random.uniform(0, 0.15)), M['flor_r'] if (k + j) % 2 else M['flor_a'], C_EXT, 1)
    for i, (x, y, h) in enumerate(ARBOLES):
        arbol(f'arbol_{i}', x, y, h)
    for i, (x, y, h) in enumerate(PALMAS):
        palma(f'palma_{i}', x, y, h)
    # setos junto a la cerca de la calle
    for i in range(14):
        arbusto(f'seto_{i}', LOTE['setos'][0] + (LOTE['setos'][2] - LOTE['setos'][0]) * i / 13, LOTE['setos'][1] + (LOTE['setos'][3] - LOTE['setos'][1]) * i / 13, 0.7)


# =====================================================================
#  LUZ, CÁMARA, RENDER
# =====================================================================
def build_vecinos():
    vc = coll('Vecinos')
    random.seed(11)
    casas = [(-14, 6), (-15, 24), (-13, 44), (-14, 66), (-12, 86), (46, 2), (47, 22), (48, 70), (49, 90), (4, 96), (22, 97), (4, -14), (22, -15)]
    for i, (x, y) in enumerate(casas):
        w = 9 + random.random() * 5; d = 8 + random.random() * 4; h = 3.0
        mt = M['blanco'] if i % 3 else M['amarillo']
        box(f'vecino_{i}', (w, d, h), (x, y, 0), mt, vc, 1.0)
        v = [(x - 0.6, y - 0.6, h), (x + w + 0.6, y - 0.6, h), (x + w + 0.6, y + d + 0.6, h), (x - 0.6, y + d + 0.6, h), (x + w * 0.5, y + d * 0.5, h + 2.0)]
        f = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
        r = mesh_obj(f'vecino_techo_{i}', v, f, M['lamina_roja'] if i % 2 else M['lamina'], vc, 1.0)
        vd = mat('vidrio_osc', color=(0.04, 0.06, 0.07, 1), rough=0.12)
        for (lado, L) in (('s', w), ('n', w), ('e', d), ('w', d)):
            nv = max(1, int(L // 4))
            for k in range(nv):
                c0 = (k + 0.5) * L / nv
                if lado == 's': loc, ang = (x + c0, y - 0.03), 0
                elif lado == 'n': loc, ang = (x + c0, y + d + 0.03), 0
                elif lado == 'e': loc, ang = (x + w + 0.03, y + c0), math.pi / 2
                else: loc, ang = (x - 0.03, y + c0), math.pi / 2
                fr = box(f'vecino_vm_{i}', (1.4, 0.06, 1.3), (-0.7, -0.03, 1.0), M['marco'], vc, rot=ang); fr.location = (loc[0], loc[1], 0)
                gl = box(f'vecino_vv_{i}', (1.28, 0.08, 1.18), (-0.64, -0.04, 1.06), vd, vc, rot=ang); gl.location = (loc[0], loc[1], 0)
        pd = box(f'vecino_puerta_{i}', (0.95, 0.06, 2.1), (-0.475, -0.03, 0), M['puerta'], vc, rot=0); pd.location = (x + 1.2, y - 0.03, 0)
        for k in range(2):
            arbol(f'vecino_arbol_{i}_{k}', x + random.random() * w, y - 3 + random.random() * (d + 6), 5 + random.random() * 4, vc)


def build_mundo():
    w = bpy.data.worlds.new('Mundo'); scene.world = w; w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(52)
    sky.sun_rotation = math.radians(215)
    sky.sun_intensity = 0.22
    sky.sun_size = math.radians(0.8)
    sky.altitude = 30
    sky.air_density = 1.0; sky.aerosol_density = 1.5; sky.ozone_density = 1.2
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.22
    scene.view_settings.exposure = 0.0
    return None


def camara(name, loc, target, lens=28):
    cam = bpy.data.cameras.new(name); cam.lens = lens
    co = bpy.data.objects.new(name, cam); scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return co


def render_setup(samples=96, w=1600, h=900):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.render.resolution_x = w; scene.render.resolution_y = h
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.image_settings.file_format = 'PNG'


def balcon_gris():
    """Balcón corrido del segundo nivel del edificio gris, sobre la fachada norte (hacia el jardín),
    como en las fotos reales: losa volada, baranda, columnas delgadas y alero de lámina."""
    c = coll('Balcon', C_EXT)
    x0, y0 = GRIS['pos']; w = 18.0; y1 = y0 + 16.0; prof = 2.0; z = NIVEL
    losa = box('balcon_losa', (w + 0.3, prof + EXT, 0.22), (x0 - 0.15, y1 - 0.05, z - 0.22), M['gris_claro'], c, 0.5)
    losa['edificio'] = 'gris'; losa['piso'] = 2
    piso = box('balcon_piso', (w + 0.3, prof, 0.03), (x0 - 0.15, y1 + EXT - 0.05, z), M['concreto'] if 'concreto' in M else M['acera'], c, 0.5)
    piso['edificio'] = 'gris'; piso['piso'] = 2
    # baranda metálica (frente y laterales)
    b1 = baranda('balcon_bar_n', (x0 - 0.1, y1 + prof + EXT - 0.1), w + 0.2, 0.0, z, c, azul=True)
    b2 = baranda('balcon_bar_w', (x0 - 0.1, y1 + EXT - 0.05), prof, math.pi / 2, z, c, azul=True)
    b3 = baranda('balcon_bar_e', (x0 + w + 0.1, y1 + EXT - 0.05), prof, math.pi / 2, z, c, azul=True)
    for b in (b1, b2, b3): b['edificio'] = 'gris'; b['piso'] = 2
    # columnas delgadas y alero
    k = 0.0
    while k <= w + 0.01:
        col = box(f'balcon_col_{k:.0f}', (0.12, 0.12, ALTO), (x0 - 0.1 + k - 0.06, y1 + prof + EXT - 0.2, z), M['baranda_b'], c)
        col['edificio'] = 'gris'; col['piso'] = 2
        k += 4.5
    al = box('balcon_alero', (w + 0.6, prof + 0.8, 0.06), (x0 - 0.3, y1, z + ALTO), M['lamina'], c, 0.5)
    al.rotation_euler = (math.radians(6), 0, 0)
    al['edificio'] = 'gris'; al['piso'] = 99; al['techo'] = 1
    # acceso en planta baja bajo el balcón: puerta doble y rampa corta
    rampa = box('balcon_rampa', (3.0, prof + 1.5, 0.12), (x0 + w / 2 - 1.5, y1 + EXT, 0), M['acera'], c, 1.0)
    rampa['edificio'] = 'gris'; rampa['piso'] = 1


# =====================================================================
if __name__ == '__main__' or True:
    build_terreno()
    build_exteriores()
    build_vecinos()
    for E in (GRIS, AMARILLA):
        build_edificio(E)
    balcon_gris()
    gx, gy = GRIS['pos']
    for i, (yy, zz) in enumerate(((gy + 10.5, 2.2), (gy + 14.0, 2.2))):
        aire_acondicionado(f'ac_gris_{i}', gx + 26 + EXT / 2, yy, zz, -math.pi / 2, C_EXT)
    for i, xx in enumerate((gx + 7.5, gx + 15.5)):
        aire_acondicionado(f'ac_gris_s{i}', xx, gy - EXT / 2, NIVEL + 2.2, math.pi, C_EXT)
    ax, ay = AMARILLA['pos']
    for i, (xx, zz) in enumerate(((ax + 7.0, 2.1), (ax + 12.5, 2.1))):
        aire_acondicionado(f'ac_casa_{i}', xx, ay - EXT / 2, zz, math.pi, C_EXT)
    build_mundo()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'escena.blend'))
    print('escena guardada; objetos:', len(bpy.data.objects))
