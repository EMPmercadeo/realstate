"""
Arma las láminas de revisión de la etapa de bloqueo (no necesita Blender):
  build/bloqueo/cenital.jpg         satélite + modelo alineados, lote, vías, escala provisional
  build/bloqueo/par_<id>.jpg        foto real | modelo desde una cámara equivalente
  build/bloqueo/revision_etapa2.jpg las cuatro comparaciones juntas
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import sitio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not os.path.exists(FB):
    FB = FR = None


def font(sz, bold=False):
    try:
        return ImageFont.truetype(FB if bold else FR, sz)
    except Exception:
        return ImageFont.load_default()


def etiqueta(d, xy, txt, sz=22, fg=(255, 255, 255), bg=(20, 24, 28), bold=True, pad=6):
    f = font(sz, bold)
    x, y = xy
    bb = d.textbbox((x, y), txt, font=f)
    d.rectangle((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad), fill=bg)
    d.text((x, y), txt, font=f, fill=fg)


def cenital():
    k = 2
    sat = Image.open(os.path.join(ROOT, 'docs', 'lote-satelite.png')).convert('RGB').resize((sitio.IMG_W * k, sitio.IMG_H * k), Image.LANCZOS)
    mod = Image.open(os.path.join(OUT, 'cenital_modelo.png')).convert('RGBA')
    a = mod.split()[3].point(lambda v: int(v * 0.82))
    mod.putalpha(a)
    izq = sat.copy().convert('RGBA')
    izq.alpha_composite(mod)
    d = ImageDraw.Draw(izq)
    g = sitio.geometria_px()
    def P(poly):
        return [(x * k, y * k) for x, y in list(poly.exterior.coords)]
    d.line(P(g['rojo']), fill=(230, 40, 40), width=3)
    for via in (g['ca'], g['oeste']):
        for p in ([via] if via.geom_type == 'Polygon' else via.geoms):
            d.line(P(p), fill=(255, 160, 40), width=3)
    d.line(P(g['lote']), fill=(80, 255, 120), width=5)
    s = sitio.s()
    etiqueta(d, (360 * k, 70 * k), 'C.A', 26)
    etiqueta(d, (140 * k, 235 * k), 'calle de tierra', 22)
    etiqueta(d, (430 * k, 455 * k), 'Casa amarilla', 24, bg=(120, 90, 20))
    etiqueta(d, (215 * k, 755 * k), 'Edificio gris', 24, bg=(60, 70, 80))
    etiqueta(d, (300 * k, 525 * k), 'franja intermedia', 20, bg=(40, 70, 40))
    # barra de escala de 10 m
    L = 10 / s * k
    x0, y0 = 40 * k, 960 * k
    d.rectangle((x0 - 10, y0 - 46, x0 + L + 160, y0 + 22), fill=(20, 24, 28))
    d.rectangle((x0, y0, x0 + L, y0 + 10), fill=(255, 255, 255))
    d.rectangle((x0 + L / 2, y0, x0 + L, y0 + 10), fill=(60, 60, 60))
    d.text((x0, y0 - 38), '10 m (escala provisional)', font=font(22, True), fill=(255, 255, 255))
    # leyenda
    ley = [((230, 40, 40), 'trazo del usuario (referencia, no lindero)'),
           ((255, 160, 40), 'vías incluidas en el trazo (se restan)'),
           ((80, 255, 120), f'lote usado: {2500:,} m² aprox.'.replace(',', '.')),
           ((255, 255, 255), f'escala uniforme {s:.3f} m por píxel'.replace('.', ','))]
    yy = 20
    d.rectangle((14, 10, 860, 20 + 40 * len(ley)), fill=(20, 24, 28))
    for col, txt in ley:
        d.rectangle((26, yy + 8, 60, yy + 22), fill=col)
        d.text((72, yy), txt, font=font(24), fill=(255, 255, 255)); yy += 40
    der = Image.open(os.path.join(OUT, 'cenital_completo.png')).convert('RGB')
    dd = ImageDraw.Draw(der)
    etiqueta(dd, (20, 20), 'Modelo de bloqueo (materiales neutros)', 30)
    etiqueta(dd, (20, 70), 'norte de imagen, no geográfico', 22, bold=False)
    W = izq.width + der.width + 30
    hoja = Image.new('RGB', (W, izq.height + 110), (245, 244, 240))
    hd = ImageDraw.Draw(hoja)
    hd.text((20, 25), 'Vista cenital alineada con el satélite · Altos de San Cristóbal', font=font(44, True), fill=(30, 40, 46))
    hoja.paste(izq.convert('RGB'), (0, 110)); hoja.paste(der, (izq.width + 30, 110))
    hoja = hoja.resize((hoja.width // 2, hoja.height // 2), Image.LANCZOS)
    hoja.save(os.path.join(OUT, 'cenital.jpg'), quality=88)
    print('cenital.jpg')


PARES = [
    ('casa_frontal', 'Casa amarilla · frente (cochera, torre, ala baja)'),
    ('casa_patio', 'Casa amarilla · fondo desde el patio de grava'),
    ('gris_acceso', 'Edificio gris · acceso (galería cerrada y remates)'),
    ('gris_galeria', 'Edificio gris · galería del lado jardín (hoy cerrada con verjas; la foto es anterior)'),
]


def par(vid, titulo, foto, H=720):
    f = Image.open(os.path.join(ROOT, foto)).convert('RGB')
    r = Image.open(os.path.join(OUT, f'cam_{vid}.png')).convert('RGB')
    f = f.resize((int(f.width * H / f.height), H), Image.LANCZOS)
    r = r.resize((int(r.width * H / r.height), H), Image.LANCZOS)
    W = f.width + r.width + 20
    hoja = Image.new('RGB', (W, H + 70), (245, 244, 240))
    d = ImageDraw.Draw(hoja)
    d.text((12, 18), titulo, font=font(30, True), fill=(30, 40, 46))
    hoja.paste(f, (0, 70)); hoja.paste(r, (f.width + 20, 70))
    etiqueta(d, (14, 84), 'FOTO REAL', 22)
    etiqueta(d, (f.width + 34, 84), 'MODELO · bloqueo', 22, bg=(30, 90, 70))
    hoja.save(os.path.join(OUT, f'par_{vid}.jpg'), quality=88)
    return hoja


def todo():
    import bloqueo_vistas
    hojas = []
    for vid, tit in PARES:
        p = os.path.join(OUT, f'cam_{vid}.png')
        if os.path.exists(p):
            hojas.append(par(vid, tit, bloqueo_vistas.FOTOS[vid]))
    if hojas:
        W = max(h.width for h in hojas)
        Ht = sum(h.height for h in hojas) + 20 * len(hojas)
        L = Image.new('RGB', (W, Ht), (245, 244, 240))
        y = 0
        for h in hojas:
            L.paste(h, (0, y)); y += h.height + 20
        L = L.resize((L.width * 2 // 3, L.height * 2 // 3), Image.LANCZOS)
        L.save(os.path.join(OUT, 'revision_etapa2.jpg'), quality=86)
        print('revision_etapa2.jpg')


if __name__ == '__main__':
    if os.path.exists(os.path.join(OUT, 'cenital_modelo.png')):
        cenital()
    todo()
