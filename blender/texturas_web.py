"""
Texturas procedurales repetibles para el visor web (ronda 3, realismo). Sin descargas: todo sale de ruido
y trazos dibujados aquí, así que no hay licencias que cuidar.

Salida en web/public/tex/:
  cesped.jpg        césped (color), 1024 px ≈ 2,5 m
  cesped_seco.jpg   césped seco / tierra con pasto, para variar el terreno
  tierra.jpg        calle de tierra con piedritas
  asfalto.jpg       asfalto con agregado
  relieve.png       4 canales de relieve en escala de grises (R estuco, G concreto, B mancha suave, A poros)
  hojas.png         racimo de hojas con alfa (tarjetas de las copas)
  hojas_ciprés.png  follaje escamoso con alfa (cipreses y tuyas)
  fronda.png        fronda de palma con alfa
  corteza.jpg       corteza
Uso: python3 blender/texturas_web.py
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

OUT = os.path.join(os.path.dirname(__file__), '..', 'web', 'public', 'tex')
rng = np.random.default_rng(31)


def ruido(n, celdas, orden=3):
    """ruido de valor periódico (se repite sin costura) de n x n con `celdas` celdas por lado"""
    g = rng.random((celdas, celdas))
    return ndimage.zoom(g, n / celdas, order=orden, mode='grid-wrap', grid_mode=True)[:n, :n]


def fbm(n, base=4, oct=5, pers=0.5):
    s, a, t = np.zeros((n, n)), 1.0, 0.0
    for i in range(oct):
        c = base * 2 ** i
        if c > n // 2:
            break
        s += a * ruido(n, c); t += a; a *= pers
    return s / t


def norm01(a):
    return (a - a.min()) / (a.max() - a.min() + 1e-9)


def guardar(a, nombre, q=82):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    p = os.path.join(OUT, nombre)
    if nombre.endswith('.jpg'):
        im.convert('RGB').save(p, quality=q, optimize=True)
    else:
        im.save(p, optimize=True)
    print(nombre, im.size, os.path.getsize(p) // 1024, 'KB')


def trazos(img, n, gen, W):
    """dibuja trazos con envoltura (la imagen se repite sin costura)"""
    d = ImageDraw.Draw(img, 'RGBA')
    for _ in range(n):
        pts, col, ancho = gen()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for ox in (0, -W, W):
            if min(xs) + ox > W or max(xs) + ox < 0:
                continue
            for oy in (0, -W, W):
                if min(ys) + oy > W or max(ys) + oy < 0:
                    continue
                d.line([(x + ox, y + oy) for x, y in pts], fill=col, width=ancho)


def cesped(nombre, seco=0.0, n=1024):
    base = fbm(n, 4, 6)
    suelo = np.stack([0.20 + 0.10 * base, 0.22 + 0.08 * base, 0.10 + 0.04 * base], -1)
    suelo = suelo * (1 - seco) + np.stack([0.36 + 0.1 * base, 0.30 + 0.08 * base, 0.18 + 0.05 * base], -1) * seco
    img = Image.fromarray((suelo * 255).astype(np.uint8)).convert('RGBA')

    def hoja():
        x, y = rng.random() * n, rng.random() * n
        L = 10 + rng.random() * 26
        a = -math.pi / 2 + (rng.random() - 0.5) * 1.6
        curva = (rng.random() - 0.5) * 0.6
        pts = [(x, y)]
        for k in range(1, 4):
            t = k / 3
            pts.append((x + math.cos(a + curva * t) * L * t, y + math.sin(a + curva * t) * L * t))
        r = rng.random()
        if r < seco * 0.8 or r < 0.05:          # hoja seca
            h = (0.55 + rng.random() * 0.2, 0.48 + rng.random() * 0.15, 0.25 + rng.random() * 0.1)
        else:
            v = 0.32 + rng.random() * 0.42
            h = (v * (0.58 + rng.random() * 0.22), v * 0.96, v * (0.30 + rng.random() * 0.14))
        return pts, tuple(int(c * 255) for c in h) + (int(150 + rng.random() * 105),), 1 + int(rng.random() < 0.35)
    trazos(img, 52000, hoja, n)
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    # variación media para que no se note el mosaico
    m = fbm(n, 2, 3)
    a *= (0.88 + 0.24 * m)[..., None]
    guardar(a, nombre)


def tierra(n=1024):
    b = fbm(n, 4, 7)
    c = np.stack([0.50 + 0.14 * b, 0.42 + 0.12 * b, 0.32 + 0.10 * b], -1)
    img = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    for _ in range(9000):                    # piedritas
        x, y, r = rng.random() * n, rng.random() * n, 0.8 + rng.random() ** 3 * 5
        v = 0.38 + rng.random() * 0.45
        col = (int(255 * v), int(255 * v * 0.94), int(255 * v * 0.86), int(160 + rng.random() * 95))
        for ox in (0, -n, n):
            for oy in (0, -n, n):
                d.ellipse([x + ox - r, y + oy - r * 0.8, x + ox + r, y + oy + r * 0.8], fill=col)
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    a *= (0.85 + 0.3 * fbm(n, 3, 3))[..., None]
    guardar(a, 'tierra.jpg')


def asfalto(n=1024):
    b = fbm(n, 8, 6)
    g = 0.30 + 0.08 * b + (rng.random((n, n)) - 0.5) * 0.10
    p = rng.random((n, n)) ** 30 * 0.35            # agregado claro
    g = g + p
    g *= 0.9 + 0.2 * fbm(n, 2, 3)
    a = np.stack([g, g * 0.99, g * 0.97], -1)
    guardar(np.clip(a, 0, 1), 'asfalto.jpg')


def grava(n=1024):
    img = Image.new('RGB', (n, n), (92, 86, 78))
    d = ImageDraw.Draw(img)
    for _ in range(26000):
        x, y, r = rng.random() * n, rng.random() * n, 2 + rng.random() * 6
        v = 0.40 + rng.random() * 0.45
        t = rng.random()
        col = (int(255 * v), int(255 * v * (0.95 - 0.08 * t)), int(255 * v * (0.88 - 0.12 * t)))
        for ox in (0, -n, n):
            for oy in (0, -n, n):
                d.ellipse([x + ox - r, y + oy - r * 0.75, x + ox + r, y + oy + r * 0.75], fill=col, outline=(60, 56, 50))
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    guardar(a, 'grava.jpg')


def relieve(n=512):
    est = norm01(fbm(n, 16, 5, 0.55) + (rng.random((n, n)) - 0.5) * 0.25)          # estuco: grano fino
    est = ndimage.gaussian_filter(est, 0.7, mode='wrap')
    con = norm01(fbm(n, 8, 6, 0.6))                                                   # concreto
    poros = (rng.random((n, n)) ** 40)
    poros = ndimage.gaussian_filter(poros, 0.8, mode='wrap')
    con = norm01(con - poros * 4)
    man = norm01(fbm(n, 2, 4, 0.6))                                                   # mancha suave
    tal = norm01(ndimage.gaussian_filter(rng.random((n, n)), 1.2, mode='wrap'))       # poros finos
    a = np.stack([est, con, man, tal], -1)
    im = Image.fromarray((a * 255).astype(np.uint8), 'RGBA')
    im.save(os.path.join(OUT, 'relieve.png'), optimize=True)
    print('relieve.png', os.path.getsize(os.path.join(OUT, 'relieve.png')) // 1024, 'KB')


def hojas(nombre, n=512, nh=420, largo=(14, 30), ancho=0.38, tono=(0.16, 0.36, 0.10), escamas=False):
    """racimo de hojas con alfa; el centro más denso; sombreado por posición (abajo y adentro más oscuro)"""
    img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    # ramitas
    for k in range(9):
        a = rng.random() * math.tau; L = n * (0.25 + rng.random() * 0.2)
        d.line([(c, c), (c + math.cos(a) * L, c + math.sin(a) * L)], fill=(70, 55, 40, 255), width=3)
    orden = []
    for _ in range(nh):
        r = (rng.random() ** 0.7) * n * 0.44
        a = rng.random() * math.tau
        x, y = c + math.cos(a) * r, c + math.sin(a) * r
        orden.append((y, x, a))
    orden.sort()
    for y, x, a in orden:
        L = largo[0] + rng.random() * (largo[1] - largo[0])
        W = L * ancho
        ang = a + (rng.random() - 0.5) * 1.4
        # tono: más claro arriba y afuera, más oscuro abajo/centro
        luz = 0.55 + 0.45 * (1 - y / n) * 0.8 + 0.25 * (math.hypot(x - c, y - c) / (n * 0.44))
        v = (0.75 + rng.random() * 0.5) * luz
        col = [min(1, t * v * (0.9 + rng.random() * 0.2)) for t in tono]
        if rng.random() < 0.07:
            col = [min(1, col[0] * 1.6 + 0.08), min(1, col[1] * 1.25 + 0.05), col[2]]
        ca, sa = math.cos(ang), math.sin(ang)
        if escamas:
            pts = [(x + ca * L * t - sa * W * 0.5 * math.sin(math.pi * t) * s, y + sa * L * t + ca * W * 0.5 * math.sin(math.pi * t) * s)
                   for s in (1, -1) for t in ((0, .25, .5, .75, 1) if s == 1 else (1, .75, .5, .25, 0))]
        else:
            pts = [(x + ca * L * t - sa * W * math.sin(math.pi * t) ** 0.8 * s, y + sa * L * t + ca * W * math.sin(math.pi * t) ** 0.8 * s)
                   for s in (1, -1) for t in ((0, .15, .35, .55, .75, .9, 1) if s == 1 else (1, .9, .75, .55, .35, .15, 0))]
        d.polygon(pts, fill=tuple(int(t * 255) for t in col) + (255,))
        # nervadura
        d.line([(x, y), (x + ca * L * 0.85, y + sa * L * 0.85)], fill=tuple(int(min(255, t * 255 * 1.25)) for t in col) + (255,), width=1)
    img = img.filter(ImageFilter.GaussianBlur(0.35))
    a = np.asarray(img).astype(np.float32)
    # alfa duro para alphaTest y color sangrado en los bordes (evita halos negros con mipmaps)
    al = a[..., 3] / 255
    rgb = a[..., :3]
    m = al > 0.05
    lleno = rgb.copy()
    idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
    lleno = rgb[idx[0], idx[1]]
    out = np.dstack([lleno, (al > 0.45) * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, nombre), optimize=True)
    print(nombre, os.path.getsize(os.path.join(OUT, nombre)) // 1024, 'KB')


def fronda(n_w=256, n_h=1024):
    img = Image.new('RGBA', (n_w, n_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = n_w / 2
    # raquis de abajo (base, v=0) a arriba (punta, v=1) -> en la imagen, base abajo
    for i in range(120):
        t = i / 120
        y = n_h * (1 - t) - 8
        L = (n_w * 0.5 - 6) * (math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.7) * (1 - 0.25 * t)
        for s in (1, -1):
            ang = math.radians(58 + rng.random() * 10)
            x1 = cx + s * L * math.sin(ang); y1 = y - L * math.cos(ang)
            W = 6.0 + 5 * (1 - t)
            v = 0.7 + rng.random() * 0.45
            seca = rng.random() < 0.06
            col = (0.42 * v, 0.40 * v, 0.16 * v) if seca else (0.20 * v, 0.40 * v, 0.12 * v)
            # folíolo: polígono angosto
            px, py = -(y1 - y), (x1 - cx)
            nn = math.hypot(px, py) or 1
            px, py = px / nn * W / 2, py / nn * W / 2
            d.polygon([(cx, y), (cx + (x1 - cx) * 0.5 + px, y + (y1 - y) * 0.5 + py), (x1, y1), (cx + (x1 - cx) * 0.5 - px, y + (y1 - y) * 0.5 - py)],
                      fill=tuple(int(255 * c) for c in col) + (255,))
    d.line([(cx, n_h - 2), (cx, 6)], fill=(120, 110, 60, 255), width=5)
    a = np.asarray(img).astype(np.float32)
    al = a[..., 3] / 255
    idx = ndimage.distance_transform_edt(~(al > 0.05), return_distances=False, return_indices=True)
    rgb = a[..., :3][idx[0], idx[1]]
    out = np.dstack([rgb, (al > 0.45) * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'fronda.png'), optimize=True)
    print('fronda.png', os.path.getsize(os.path.join(OUT, 'fronda.png')) // 1024, 'KB')


def corteza(n=512):
    x = fbm(n, 4, 5)
    vet = ruido(n, 64, 3)
    vet = ndimage.zoom(rng.random((8, 96)), (n / 8, n / 96), order=3, mode='grid-wrap', grid_mode=True)[:n, :n]
    g = norm01(0.6 * vet + 0.4 * x)
    c = np.stack([0.30 + 0.25 * g, 0.25 + 0.20 * g, 0.19 + 0.15 * g], -1)
    guardar(c, 'corteza.jpg')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    cesped('cesped.jpg', 0.0)
    cesped('cesped_seco.jpg', 0.55)
    tierra(); asfalto(); relieve(); corteza()
    hojas('hojas.png', nh=700, largo=(16, 34))
    hojas('hojas_cipres.png', nh=1500, largo=(6, 11), ancho=0.6, tono=(0.12, 0.30, 0.10), escamas=True)
    fronda()
