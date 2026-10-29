"""
Genera texturas PBR tileables (color, roughness, normal) con numpy/PIL.
Salida: assets/textures/gen/<nombre>_{color,rough,normal}.jpg
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'textures', 'gen')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
N = 1024


def fbm(n, octaves=6, persistence=0.5, seed=0):
    """Fractal noise tileable (suma de ruidos interpolados con wrap)."""
    r = np.random.default_rng(seed)
    out = np.zeros((n, n), dtype=np.float32)
    amp = 1.0
    freq = 4
    for _ in range(octaves):
        g = r.random((freq, freq)).astype(np.float32)
        # upsample bilinear tileable
        im = Image.fromarray((g * 255).astype(np.uint8))
        im = im.resize((n, n), Image.BICUBIC)
        a = np.asarray(im).astype(np.float32) / 255.0
        out += a * amp
        amp *= persistence
        freq *= 2
    out -= out.min(); out /= (out.max() + 1e-6)
    return out


def tileable(a):
    """Mezcla bordes para asegurar tileado."""
    n = a.shape[0]
    b = np.roll(np.roll(a, n // 2, 0), n // 2, 1)
    w = np.linspace(0, 1, n, dtype=np.float32)
    wx = np.minimum(w, 1 - w) * 2
    mask = np.minimum.outer(wx, wx)
    mask = np.clip(mask * 1.6, 0, 1)
    return a * mask + b * (1 - mask)


def normal_from_height(h, strength=2.0):
    h = h.astype(np.float32)
    dx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
    dy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    nx = -dx * strength; ny = -dy * strength; nz = np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def save(name, color, rough, height, nstrength=2.0, q=88):
    rough = np.broadcast_to(np.asarray(rough, np.float32), height.shape)
    Image.fromarray(np.clip(color, 0, 255).astype(np.uint8)).save(f'{OUT}/{name}_color.jpg', quality=q)
    Image.fromarray(np.clip(rough * 255, 0, 255).astype(np.uint8)).save(f'{OUT}/{name}_rough.jpg', quality=q)
    Image.fromarray(normal_from_height(height, nstrength)).save(f'{OUT}/{name}_normal.jpg', quality=q)
    print('ok', name)


def colorize(h, c0, c1):
    c0 = np.array(c0, np.float32); c1 = np.array(c1, np.float32)
    return c0[None, None] * (1 - h[..., None]) + c1[None, None] * h[..., None]


# ---- concreto gris (edificio gris)
h = tileable(fbm(N, 7, 0.55, 1))
fine = tileable(fbm(N, 8, 0.7, 2))
col = colorize(h * 0.7 + fine * 0.3, (168, 170, 172), (206, 208, 210))
save('concrete', col, 0.75 + 0.2 * fine, h * 0.5 + fine * 0.5, 1.2)

# ---- repello pintado amarillo (casa amarilla)
h = tileable(fbm(N, 8, 0.6, 3))
col = colorize(h, (222, 190, 110), (240, 214, 140))
save('plaster_yellow', col, 0.85 + 0.1 * h, h, 0.8)

# ---- repello blanco interior
h = tileable(fbm(N, 8, 0.6, 4))
col = colorize(h, (236, 234, 228), (248, 247, 243))
save('plaster_white', col, 0.9 - 0.1 * h, h, 0.5)

# ---- cerámica beige 40x40 con fuga (pisos de las fotos)
tiles = 6
yy, xx = np.mgrid[0:N, 0:N]
gx = (xx * tiles / N) % 1.0; gy = (yy * tiles / N) % 1.0
grout = ((gx < 0.025) | (gx > 0.975) | (gy < 0.025) | (gy > 0.975)).astype(np.float32)
tile_id = (np.floor(xx * tiles / N) + np.floor(yy * tiles / N) * tiles)
var = (np.sin(tile_id * 12.9898) * 43758.5453) % 1.0
spec = tileable(fbm(N, 8, 0.75, 5))
base = colorize(spec * 0.6 + var * 0.4, (214, 206, 190), (236, 230, 216))
col = base * (1 - grout[..., None]) + np.array((150, 146, 138), np.float32)[None, None] * grout[..., None]
rough = 0.22 + 0.1 * spec + 0.6 * grout
height = (1 - grout) * (0.9 + 0.1 * spec)
save('ceramic_beige', col, rough, height, 3.0)

# ---- cerámica gris oscuro (edificio gris, pisos del salón)
base = colorize(spec * 0.6 + var * 0.4, (196, 198, 200), (226, 228, 230))
col = base * (1 - grout[..., None]) + np.array((140, 140, 142), np.float32)[None, None] * grout[..., None]
save('ceramic_grey', col, 0.25 + 0.1 * spec + 0.6 * grout, height, 3.0)

# ---- tejas terracota (techo casa amarilla)
rows = 10
ry = (yy * rows / N) % 1.0
cx = ((xx * rows * 1.0 / N) + 0.5 * np.floor(yy * rows / N)) % 1.0
curve = np.sin(cx * np.pi) ** 1.5
edge = np.clip(ry * 6, 0, 1) * np.clip((1 - ry) * 1.2, 0, 1)
hh = curve * edge
n = tileable(fbm(N, 7, 0.6, 6))
col = colorize(hh * 0.6 + n * 0.4, (142, 66, 48), (196, 104, 74))
save('roof_tile', col, 0.7 + 0.2 * n, hh, 4.0)

# ---- lámina metálica (techo gris)
waves = (np.sin(xx * 2 * np.pi * 24 / N) * 0.5 + 0.5)
n = tileable(fbm(N, 7, 0.6, 7))
col = colorize(n * 0.3 + waves * 0.1, (170, 174, 178), (205, 208, 212))
save('metal_roof', col, 0.35 + 0.2 * n, waves * 0.8 + n * 0.2, 3.0)

# ---- grava
g = tileable(fbm(N, 9, 0.8, 8))
spots = (rng.random((N, N)) > 0.985).astype(np.float32)
spots = np.asarray(Image.fromarray((spots * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))) / 255.0
col = colorize(g * 0.7 + spots * 0.3, (150, 142, 128), (205, 198, 184))
save('gravel', col, 0.9, g * 0.6 + spots * 0.4, 3.5)

# ---- tierra (huerto)
g = tileable(fbm(N, 8, 0.7, 9))
col = colorize(g, (92, 64, 42), (134, 98, 66))
save('soil', col, 0.95, g, 1.5)

# ---- granito (cocina)
g = tileable(fbm(N, 9, 0.85, 10))
fl = (rng.random((N, N)) > 0.97).astype(np.float32)
col = colorize(g * 0.7 + fl * 0.3, (70, 68, 70), (150, 146, 142))
save('granite', col, 0.15 + 0.05 * g, g * 0.1, 0.4)

# ---- madera oscura (puertas, muebles)
wy = (yy / N * 1.0 + np.sin(xx / N * 2 * np.pi * 2) * 0.05)
rings = (np.sin(wy * 2 * np.pi * 18) * 0.5 + 0.5)
n = tileable(fbm(N, 7, 0.6, 11))
col = colorize(rings * 0.5 + n * 0.5, (84, 48, 30), (140, 88, 54))
save('wood_dark', col, 0.45 + 0.2 * n, rings * 0.3 + n * 0.2, 1.0)

# ---- césped (desde foto real si existe, si no procedural)
src = os.path.join(OUT, '..', 'grass.jpg')
if os.path.exists(src) and os.path.getsize(src) > 1000:
    im = Image.open(src).convert('RGB').resize((N, N))
    a = np.asarray(im).astype(np.float32)
    # un poco más verde tropical
    a[..., 1] = np.clip(a[..., 1] * 1.05, 0, 255)
    hgt = tileable(fbm(N, 8, 0.7, 12))
    save('grass', a, 0.95, hgt, 1.5)
else:
    g = tileable(fbm(N, 9, 0.8, 12))
    save('grass', colorize(g, (62, 96, 40), (112, 150, 70)), 0.95, g, 1.5)

# ---- pintura azul (barandas / estacionamiento)
print('done')
