"""Genera texturas RGBA de follaje (cluster de hojas y fronda de palma)."""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'textures', 'gen')
os.makedirs(OUT, exist_ok=True)
random.seed(3)
N = 1024


def leaf(draw, cx, cy, L, ang, color):
    # hoja elíptica con punta
    pts = []
    for t in np.linspace(0, 2 * math.pi, 18):
        r = L * (0.5 if abs(math.cos(t)) < 0.98 else 0.5)
        x = math.cos(t) * L * 0.5
        y = math.sin(t) * L * 0.18 * (1 - 0.3 * abs(math.cos(t)))
        xr = x * math.cos(ang) - y * math.sin(ang); yr = x * math.sin(ang) + y * math.cos(ang)
        pts.append((cx + xr, cy + yr))
    draw.polygon(pts, fill=color)


# ---- cluster de hojas (árbol)
im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
for i in range(900):
    cx = N / 2 + random.gauss(0, N * 0.2); cy = N / 2 + random.gauss(0, N * 0.2)
    if math.hypot(cx - N / 2, cy - N / 2) > N * 0.46:
        continue
    g = random.randint(70, 150); r = int(g * random.uniform(0.35, 0.6)); b = int(g * random.uniform(0.2, 0.4))
    leaf(d, cx, cy, random.uniform(50, 110), random.uniform(0, math.pi), (r, g, b, 255))
im.save(f'{OUT}/leaf_cluster.png')

# ---- fronda de palma (vertical, nace arriba, leaflets a los lados)
im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.line([(N / 2, 10), (N / 2, N - 10)], fill=(130, 120, 70, 255), width=12)
for i in range(110):
    f = i / 110
    y = 30 + f * (N - 60)
    L = (N * 0.46) * (0.35 + 0.65 * math.sin(math.pi * min(1, f * 1.15))) + 30
    for side in (-1, 1):
        a = math.radians(28 + 30 * f)
        x1 = N / 2 + side * math.cos(a) * L; y1 = y + math.sin(a) * L
        g = random.randint(95, 150)
        d.line([(N / 2, y), (x1, y1)], fill=(int(g * 0.42), g, int(g * 0.28), 255), width=13)
im = im.filter(ImageFilter.SMOOTH)
im.save(f'{OUT}/palm_frond.png')

# ---- césped alto / arbusto
im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
for i in range(1500):
    cx = N / 2 + random.gauss(0, N * 0.22); cy = N / 2 + random.gauss(0, N * 0.22)
    if math.hypot(cx - N / 2, cy - N / 2) > N * 0.46:
        continue
    g = random.randint(90, 170); r = int(g * 0.45); b = int(g * 0.3)
    leaf(d, cx, cy, random.uniform(20, 45), random.uniform(0, math.pi), (r, g, b, 255))
im.save(f'{OUT}/bush_cluster.png')
print('ok hojas')
