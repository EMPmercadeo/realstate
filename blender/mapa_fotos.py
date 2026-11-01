"""
Mapa de la fase 1 (docs/mapa/mapa-fase1.jpg): satélite de Esri con el lindero del modelo, los techos del
modelo (leídos de build/bloqueo/bloqueo.blend), los exteriores y dónde se tomó cada foto o video del
31-10-2026. Registro entre imágenes en docs/mapa/registro-satelites.json.
Uso: python3 blender/mapa_fotos.py      (necesita el módulo bpy para leer los techos)
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sitio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
D = os.path.join(ROOT, 'docs', 'mapa')
REG = json.load(open(os.path.join(D, 'registro-satelites.json')))
Ag = np.array(REG['google_a_esri'])
K = 3
FB = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
FR = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
G, C = sitio.GRIS, sitio.CASA


def techos():
    import bpy
    from shapely.geometry import MultiPoint
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'bloqueo', 'bloqueo.blend'))
    out = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(('ca_', 'gr_')) and any(t in o.name for t in ('techo', 'cubierta', 'remate', 'toldo')):
            mw = o.matrix_world
            pts = [sitio.m_a_px(*(mw @ v.co).to_2d()[:]) for v in o.data.vertices]
            if len(pts) >= 3:
                out.append(list(MultiPoint(pts).convex_hull.exterior.coords))
    return out


def g2e(gx, gy):
    x, y = Ag @ np.array([gx, gy, 1.0])
    return (x * K, y * K)


def L(E, x, y):
    return g2e(*sitio.m_a_px(*sitio.local_a_m(E, x, y)))


FOT = [('1', '113649 · 113640 (videos)', G, (0.5, -3.2), (5, 6)), ('2', '114153 · 114207', G, (-5, -8), (5, 5)),
       ('3', '114245 · 114259 (puerta, mano a 1,80 m)', G, (1.8, 3.2), (1.8, 4.8)), ('4', '114358', G, (6.2, 1.0), (0, -2.5)),
       ('5', '114532 · 114557 (desde el pilar)', G, (-19.6, -0.6), (-29, 8)), ('6', '114626 (portón del patio de grava)', G, (-23.5, -10.5), (-30, 6)),
       ('7', '114732 (porche y garaje de atrás)', G, (-27.5, 0.5), (-31, 4)), ('8', '114821 (frente a la C.A)', C, (14.5, -10), (4, -7)),
       ('9', '114847 (jardín del frente)', C, (13.0, -4.5), (17, -2)), ('10', '113759 · 113809 · 113820 · 113831', G, (-4.3, 3.0), (-19.6, 3.0)),
       ('11', '113841 (quiosco y muro)', G, (-13, 1.6), (-8.6, -0.4)), ('12', '113851 (rampa hacia el gris)', G, (-11, 6.2), (-3, 6)),
       ('13', '114024 (cara norte del gris)', G, (-9.5, 7), (0, 7)), ('14', '114032 · 113942 (oficinita)', G, (-10.8, 6.4), (-12.8, 16)),
       ('15', '113911 (bananal)', G, (-6, 8.3), (-6, 18)), ('16', '114051 · 114101 (jardín)', G, (-16.5, 8.5), (-22, 9)),
       ('17', '114759 (palma, tanque)', G, (-24.5, -2), (-24, 10))]


# panorámicas de Street View usadas en la ronda 2 (posición de la cámara)
SV = [(G, (1.36, -4.8), 'SV1'), (C, (9.36, -11.37), 'SV2')]


def main():
    hulls = techos()
    im = Image.open(os.path.join(D, 'satelite-esri-z19.jpg')).convert('RGB').resize((800 * K, 600 * K), Image.LANCZOS)
    d = ImageDraw.Draw(im, 'RGBA')
    g_old = sitio.geometria_px(cortar=False); g_new = sitio.geometria_px()
    pts = [g2e(*p) for p in g_old['lote'].exterior.coords]
    for i in range(0, len(pts) - 1, 2):
        d.line([pts[i], pts[i + 1]], fill=(255, 80, 220, 255), width=4)
    d.line([g2e(*p) for p in g_new['lote'].exterior.coords], fill=(60, 255, 90, 255), width=6)
    for h in hulls:
        d.line([g2e(*p) for p in h], fill=(255, 255, 255, 230), width=3)
    d.line([L(G, -4.2, 3.0), L(G, -19.2, 3.0)], fill=(200, 120, 60, 255), width=10)
    for (a, b) in (((-4.6, 5.25), (-10, 5.25)), ((-11.5, 7.0), (-17.2, 7.0))):
        d.line([L(G, *a), L(G, *b)], fill=(90, 140, 255, 255), width=10)

    def caja(x0, y0, x1, y1, fill):
        d.polygon([L(G, x0, y0), L(G, x1, y0), L(G, x1, y1), L(G, x0, y1)], fill=fill, outline=(0, 0, 0, 255))
    caja(-14.04, 14.7, -11.56, 17.7, (255, 255, 255, 230))
    caja(-10.0, -0.9, -7.2, 0.65, (240, 200, 40, 230))
    caja(-10.6, 10.6, -4.8, 17.6, (120, 80, 40, 140))
    for (x, y, r, col) in ((-16.2, 13.2, 2.15, (255, 120, 40, 255)), (-12.2, 0.75, 1.4, (40, 220, 255, 255))):
        cx, cy = L(G, x, y); rr = r / 0.1969 * K
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col, width=5)
    for n, t, E, p, q in FOT:
        a = L(E, *p); b = L(E, *q); v = np.array(b) - np.array(a); v = v / np.linalg.norm(v) * 60
        tip = (a[0] + v[0], a[1] + v[1]); ang = math.atan2(v[1], v[0])
        d.line([a, tip], fill=(255, 230, 0, 255), width=6)
        for s in (2.6, -2.6):
            d.line([tip, (tip[0] - 22 * math.cos(ang + s * 0.35), tip[1] - 22 * math.sin(ang + s * 0.35))], fill=(255, 230, 0, 255), width=6)
        d.ellipse([a[0] - 24, a[1] - 24, a[0] + 24, a[1] + 24], fill=(20, 20, 20, 235), outline=(255, 230, 0, 255), width=4)
        tw = d.textlength(n, font=FB(26)); d.text((a[0] - tw / 2, a[1] - 15), n, font=FB(26), fill=(255, 230, 0))
    # eje de la calle de tierra (corregido con Street View) y cámaras de Street View
    eje = [g2e(*q) for q in sitio.OESTE]
    for i in range(len(eje) - 1):
        a, b = np.array(eje[i]), np.array(eje[i + 1]); n_ = max(1, int(np.linalg.norm(b - a) / 28))
        for j in range(0, n_, 2):
            d.line([tuple(a + (b - a) * j / n_), tuple(a + (b - a) * (j + 1) / n_)], fill=(255, 255, 255, 220), width=4)
    for E, p, txt in SV:
        cx, cy = L(E, *p)
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 255, 255, 240), outline=(30, 90, 220, 255), width=6)
        tw = d.textlength(txt, font=FB(24)); d.text((cx - tw / 2, cy - 14), txt, font=FB(24), fill=(30, 90, 220))
    px10 = 10 / 0.1969 * K; x0, y0 = 60, 600 * K - 70
    d.rectangle([x0 - 12, y0 - 48, x0 + px10 + 120, y0 + 34], fill=(0, 0, 0, 170))
    d.rectangle([x0, y0, x0 + px10, y0 + 14], fill=(255, 255, 255, 255)); d.rectangle([x0 + px10 / 2, y0, x0 + px10, y0 + 14], fill=(90, 90, 90, 255))
    d.text((x0, y0 - 40), '0          5          10 m', font=FB(26), fill='white')
    nx, ny = 800 * K - 80, 90
    d.polygon([(nx, ny - 55), (nx - 22, ny + 15), (nx, ny), (nx + 22, ny + 15)], fill=(255, 255, 255, 255))
    d.text((nx - 12, ny + 20), 'N', font=FB(34), fill='white')
    leg = [((60, 255, 90), 'Lindero del modelo (corregido con las fotos)'), ((255, 80, 220), 'Trazo anterior menos calles (punteado)'),
           ((255, 255, 255), 'Techos del modelo (casa y gris)'), ((200, 120, 60), 'Camino de baldosa'), ((90, 140, 255), 'Rampas con baranda'),
           ((255, 255, 255), 'Oficinita blanca (existe; satélite y video)'), ((240, 200, 40), 'Quiosco amarillo (existe)'),
           ((120, 80, 40), 'Huerto (propuesta)'), ((255, 120, 40), 'Gazebo (propuesta)'), ((40, 220, 255), 'Tina de hidroterapia (propuesta)'),
           ((255, 230, 0), 'Foto o video: posición aproximada y dirección'),
           ((235, 235, 235), 'Eje de la calle de tierra (punteado; ronda 2)'),
           ((30, 90, 220), 'SV1 / SV2: cámaras de Street View (calle de tierra / C.A)')]
    LW = 1150; lg = Image.new('RGB', (LW, im.height), (246, 245, 240)); dl = ImageDraw.Draw(lg)
    dl.text((40, 40), 'Mapa revisado (rondas 1 y 2)', font=FB(56), fill=(25, 30, 35))
    dl.text((40, 120), 'Satélite de Esri (Web Mercator, 0,197 m por píxel de la captura).', font=FR(30), fill=(70, 75, 80))
    dl.text((40, 160), 'Escala medida: 0,1415 m/px en la imagen de Google (antes 0,117).', font=FR(30), fill=(70, 75, 80))
    y = 240
    for col, t in leg:
        dl.rectangle([40, y + 6, 90, y + 36], fill=col, outline=(0, 0, 0)); dl.text((110, y), t, font=FR(32), fill=(30, 30, 30)); y += 56
    y += 20; dl.text((40, y), 'Fotos y videos (31-10-2026)', font=FB(36), fill=(25, 30, 35)); y += 56
    for n, t, *_ in FOT:
        dl.text((40, y), f'{n:>2}  {t}', font=FR(28), fill=(30, 30, 30)); y += 42
    out = Image.new('RGB', (im.width + LW, im.height), (246, 245, 240)); out.paste(im, (0, 0)); out.paste(lg, (im.width, 0))
    out = out.resize((out.width * 2 // 3, out.height * 2 // 3), Image.LANCZOS)
    out.save(os.path.join(D, 'mapa-fase1.jpg'), quality=86)
    print('mapa', out.size)


if __name__ == '__main__':
    main()
