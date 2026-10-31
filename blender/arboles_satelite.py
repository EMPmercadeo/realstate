"""
Árboles colocados donde el satélite muestra copa FUERA del lote (bosque del sur y vecinos). Dentro del lote
el color no distingue bien césped de copa, así que allí se ponen a mano según las fotos.
Antes: árboles colocados donde el satélite muestra copa (docs/lote-satelite.png): dentro del lote, en la franja
intermedia, alrededor del edificio gris y en el bosque del sur. Así el entorno se parece al real en vez de
un anillo al azar. Se lee la imagen con bpy (sin Pillow) para que corra también dentro de Blender.
"""
import os, math, random
import bpy
import numpy as np
import sitio
import vegetacion as V
from shapely.geometry import Point

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def mascara_copas():
    im = bpy.data.images.load(os.path.join(ROOT, 'docs', 'lote-satelite.png'), check_existing=True)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]      # fila 0 = arriba de la imagen
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    return ((g > r) & (g > b * 0.92) & (lum < 0.45)) | ((lum < 0.13) & (g >= r * 0.95))


def colocar(col, bases, excluir, paso=3.2, umbral=0.5, seed=5, fuera_de=None):
    """Recorre la imagen en celdas de `paso` metros; donde la fracción de copa supera `umbral` pone una
    instancia de alguna base. `excluir(X, Y)` (metros del modelo) descarta zonas (edificios, calles, jardín)."""
    mask = mascara_copas()
    H, W = mask.shape
    k = sitio.s()
    c = max(4, int(round(paso / k)))
    rnd = random.Random(seed)
    n = 0
    for py in range(c // 2, H - c // 2, c):
        for px in range(c // 2, W - c // 2, c):
            f = mask[py - c // 2: py + c // 2, px - c // 2: px + c // 2].mean()
            if f < umbral:
                continue
            qx, qy = px + rnd.uniform(-c * 0.4, c * 0.4), py + rnd.uniform(-c * 0.4, c * 0.4)
            if fuera_de is not None and fuera_de.contains(Point(qx, qy)):
                continue
            X, Y = sitio.m(qx, qy)
            if excluir(X, Y):
                continue
            base = rnd.choice(bases)
            esc = rnd.uniform(0.8, 1.25) * (1.15 if f > 0.85 else 1.0)
            V.instancia(base, f'sat_{n}', col, (X, Y, -0.05), rnd.uniform(0, 2 * math.pi), esc)
            n += 1
    return n


# ------------------------------------------------------------------ casas vecinas
def techos_satelite(fuera_de, calles, celda=4, area_min=35.0):
    """Manchas de techo en el satélite (rojo/terracota o lámina gris clara), fuera del lote y de las calles.
    Devuelve [(rectángulo shapely en metros, color medio rgb)]."""
    from shapely.geometry import MultiPoint
    im = bpy.data.images.load(os.path.join(ROOT, 'docs', 'lote-satelite.png'), check_existing=True)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    techo = ((r > g * 1.12) & (r > 0.35)) | ((lum > 0.55) & (abs(r - b) < 0.12))
    H, W = h // celda, w // celda
    m = techo[:H * celda, :W * celda].reshape(H, celda, W, celda).mean(axis=(1, 3)) > 0.6
    for i in range(H):                      # fuera las celdas del lote y de las calles (antes de agrupar)
        for j in range(W):
            if m[i, j]:
                q = Point((j + 0.5) * celda, (i + 0.5) * celda)
                if fuera_de.contains(q) or any(cl.buffer(6).contains(q) for cl in calles):
                    m[i, j] = False
    vis = np.zeros_like(m)
    k = sitio.s()
    out = []
    for i in range(H):
        for j in range(W):
            if not m[i, j] or vis[i, j]:
                continue
            pila = [(i, j)]; vis[i, j] = True; celdas = []
            while pila:
                a, c = pila.pop(); celdas.append((a, c))
                for da, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    aa, cc = a + da, c + dc
                    if 0 <= aa < H and 0 <= cc < W and m[aa, cc] and not vis[aa, cc]:
                        vis[aa, cc] = True; pila.append((aa, cc))
            area = len(celdas) * (celda * k) ** 2
            if area < area_min or area > 260:
                continue
            pts = [((c + 0.5) * celda, (a + 0.5) * celda) for a, c in celdas]
            cen = MultiPoint(pts).centroid
            if fuera_de.contains(cen) or any(cl.contains(cen) for cl in calles):
                continue
            rect = MultiPoint([sitio.m(x, y) for x, y in pts]).minimum_rotated_rectangle
            if area / max(rect.area, 1e-6) < 0.55:          # mancha muy irregular: no es un techo
                continue
            sel = np.array([px[int(y), int(x)] for x, y in pts])
            out.append((rect, tuple(float(v) for v in sel.mean(axis=0))))
    return out


def casa_vecina(nombre, col, rect, color_techo, mat_muro, mats_techo, alto=2.8, ov=0.45):
    """Casa de una planta con techo a cuatro aguas sobre el rectángulo del satélite (el rectángulo es el
    techo, así que los muros quedan retirados el alero)."""
    from mathutils import Vector
    c = list(rect.exterior.coords)[:4]
    p0, p1, p3 = Vector(c[0]), Vector(c[1]), Vector(c[3])
    ux, uy = (p1 - p0), (p3 - p0)
    wl, dl = ux.length, uy.length
    if wl < dl:
        ux, uy, wl, dl = uy, ux, dl, wl
        p0 = Vector(c[0]) if (Vector(c[3]) - Vector(c[0])).length > (Vector(c[1]) - Vector(c[0])).length else Vector(c[0])
    ux.normalize(); uy.normalize()
    cen = Vector(rect.centroid.coords[0])
    def P(x, y, z):
        q = cen + ux * x + uy * y
        return (q.x, q.y, z)
    hw, hd = wl / 2, dl / 2
    mw_, md_ = hw - ov, hd - ov
    v = [P(-mw_, -md_, 0), P(mw_, -md_, 0), P(mw_, md_, 0), P(-mw_, md_, 0),
         P(-mw_, -md_, alto), P(mw_, -md_, alto), P(mw_, md_, alto), P(-mw_, md_, alto)]
    caras_m = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    hr = math.tan(math.radians(20)) * hd
    rx = max(0.0, hw - hd)
    v += [P(-hw, -hd, alto - 0.1), P(hw, -hd, alto - 0.1), P(hw, hd, alto - 0.1), P(-hw, hd, alto - 0.1),
          P(-rx, 0, alto - 0.1 + hr), P(rx, 0, alto - 0.1 + hr)]
    caras_t = [(8, 9, 13, 12), (10, 11, 12, 13), (9, 10, 13), (11, 8, 12)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(v, [], caras_m + caras_t)
    # techo más cercano en color a la muestra del satélite
    paleta = {'rojo': (0.55, 0.25, 0.20), 'terracota': (0.62, 0.40, 0.32), 'lamina': (0.70, 0.70, 0.70), 'oxido': (0.45, 0.30, 0.22)}
    clave = min(paleta, key=lambda kk: sum((a - b) ** 2 for a, b in zip(paleta[kk], color_techo)))
    me.materials.append(mat_muro); me.materials.append(mats_techo[clave])
    me.polygons.foreach_set('material_index', [0] * 4 + [1] * 4)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    return o
