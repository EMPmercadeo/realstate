"""Genera texturas RGBA de follaje (cluster de hojas, fronda de palma y arbusto) con sombreado
por hoja (gradiente, nervadura, variación de tono) y antialias por supermuestreo."""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'textures', 'gen')
os.makedirs(OUT, exist_ok=True)
random.seed(3)
N = 1024
SS = 2                      # supermuestreo
M = N * SS


def hoja(draw, cx, cy, L, ang, col, anch=0.2, nerv=True):
    """Hoja lanceolada con gradiente (más clara hacia la punta) y nervadura central."""
    pts = []
    for t in np.linspace(0, 2 * math.pi, 26):
        x = math.cos(t) * L * 0.5
        y = math.sin(t) * L * anch * (1 - 0.35 * max(0, math.cos(t)))
        xr = x * math.cos(ang) - y * math.sin(ang); yr = x * math.sin(ang) + y * math.cos(ang)
        pts.append((cx + xr, cy + yr))
    r, g, b = col
    draw.polygon(pts, fill=(r, g, b, 255))
    # mitad iluminada (lado +y local) un poco más clara
    half = [p for i, p in enumerate(pts) if i >= 13] + [pts[0]]
    draw.polygon(half, fill=(min(255, int(r * 1.12)), min(255, int(g * 1.12)), min(255, int(b * 1.1)), 255))
    if nerv:
        x0, y0 = cx - math.cos(ang) * L * 0.48, cy - math.sin(ang) * L * 0.48
        x1, y1 = cx + math.cos(ang) * L * 0.44, cy + math.sin(ang) * L * 0.44
        draw.line([(x0, y0), (x1, y1)], fill=(int(r * 0.72), int(g * 0.72), int(b * 0.7), 255), width=max(2, int(L * 0.025)))


def verde():
    """Paleta de verdes tropicales: oliva, verde medio, verde profundo, con toques amarillentos."""
    k = random.random()
    if k < 0.15: base = (118, 142, 52)     # amarillento
    elif k < 0.55: base = (72, 122, 46)    # verde medio
    elif k < 0.85: base = (44, 92, 38)     # profundo
    else: base = (96, 128, 60)             # claro
    j = random.uniform(0.82, 1.18)
    return tuple(int(min(255, c * j)) for c in base)


def guardar(im, nombre):
    im = im.resize((N, N), Image.LANCZOS)
    # borde alfa más limpio
    a = np.asarray(im).astype(np.float32)
    alpha = a[..., 3]
    a[..., 3] = np.clip((alpha - 40) * 1.4, 0, 255)
    Image.fromarray(a.astype(np.uint8)).save(f'{OUT}/{nombre}.png')
    print('ok', nombre)


# ---- cluster de hojas (árbol): hojas grandes al frente, pequeñas y oscuras detrás
im = Image.new('RGBA', (M, M), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for i in range(520):
    cx = M / 2 + random.gauss(0, M * 0.19); cy = M / 2 + random.gauss(0, M * 0.19)
    if math.hypot(cx - M / 2, cy - M / 2) > M * 0.45: continue
    f = i / 520
    col = verde()
    if f < 0.4: col = tuple(int(c * 0.6) for c in col)       # fondo en sombra
    L = random.uniform(70, 150) * SS * (0.75 + 0.5 * f)
    hoja(d, cx, cy, L, random.uniform(0, math.pi), col, anch=random.uniform(0.16, 0.26))
guardar(im, 'leaf_cluster')

# ---- fronda de palma (vertical, nace arriba, foliolos a los lados)
im = Image.new('RGBA', (M, M), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.line([(M / 2, 10), (M / 2, M - 10)], fill=(126, 112, 62, 255), width=14 * SS)
for i in range(130):
    f = i / 130
    y = 30 * SS + f * (M - 60 * SS)
    L = (M * 0.46) * (0.3 + 0.7 * math.sin(math.pi * min(1, f * 1.12))) + 30 * SS
    for side in (-1, 1):
        a = math.radians(26 + 34 * f) + random.uniform(-0.05, 0.05)
        g = random.randint(100, 150); col = (int(g * 0.46), g, int(g * 0.3))
        x1 = M / 2 + side * math.cos(a) * L; y1 = y + math.sin(a) * L
        d.line([(M / 2, y), (x1, y1)], fill=(*col, 255), width=11 * SS)
        d.line([(M / 2, y), (x1, y1)], fill=(min(255, int(col[0] * 1.15)), min(255, int(col[1] * 1.12)), int(col[2] * 1.1), 255), width=5 * SS)
guardar(im, 'palm_frond')

# ---- arbusto
im = Image.new('RGBA', (M, M), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for i in range(1400):
    cx = M / 2 + random.gauss(0, M * 0.21); cy = M / 2 + random.gauss(0, M * 0.21)
    if math.hypot(cx - M / 2, cy - M / 2) > M * 0.45: continue
    col = verde()
    if i < 500: col = tuple(int(c * 0.6) for c in col)
    hoja(d, cx, cy, random.uniform(28, 60) * SS, random.uniform(0, math.pi), col, anch=random.uniform(0.22, 0.34), nerv=False)
guardar(im, 'bush_cluster')
print('ok hojas')
