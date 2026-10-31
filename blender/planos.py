"""
Planos esquemáticos de la etapa 3 (no necesita Blender).
Lee build/bloqueo/interiores.json y recorrido.json (los escribe bloqueo.py) y dibuja:
  build/bloqueo/plano_<edificio>_<nivel>.png   y   build/bloqueo/planos_etapa3.jpg (lámina completa)
Mismos datos que el modelo 3D: si cambia interiores.py, se regenera todo junto.
"""
import os, json, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
S = 46          # píxeles por metro
MG = 70         # margen
CORTE = 1.2     # altura del corte del plano

C_FONDO = (250, 249, 246)
C_CERR = (246, 238, 222)
C_ABIER = (236, 239, 240)
C_ESC = (226, 232, 238)
C_MURO = (38, 42, 46)
C_VENT = (90, 150, 205)
C_TXT = (34, 40, 46)
C_SUAVE = (120, 128, 136)
C_RUTA = (214, 60, 48)


def F(sz, b=False):
    try:
        return ImageFont.truetype(FB if b else FR, sz)
    except Exception:
        return ImageFont.load_default()


EXTRAS = {   # elementos exteriores de referencia (marco local), solo contorno punteado + rótulo
    ('casa', 'pb'): [((-1.0, -5.6, 3.9, 0.0), 'Cochera'), ((8.9, 13.8, 12.0, 15.6), 'Porche'),
                     ((1.2, 13.8, 4.4, 15.4), 'Porche en arco')],
    ('casa', 'pa'): [((4.4, -0.7, 10.0, 1.4), 'Balcón')],
    ('gris', 'pb'): [((14.45, 5.4, 15.55, 11.6), 'Esc. metálica'), ((1.0, -1.8, 6.3, 3.6), 'Estacionamientos')],
    ('gris', 'pa'): [((0.15, 4.8, 2.5, 13.0), 'Galería cerrada'), ((4.6, 11.0, 13.9, 13.4), 'Terraza · cerrada con verjas'),
                     ((14.45, 5.4, 15.55, 11.6), 'Esc. metálica')],
}
ORIENT = {
    'casa': dict(abajo='Frente · calle C.A', arriba='Fondo · patio de grava y jardín', izq='', der='Garaje'),
    'gris': dict(abajo='Calle de tierra (oeste)', arriba='Jardín (este)', izq='Norte · hacia la casa amarilla', der='Sur'),
}


def dibujar(clave, ed, nv, rutas):
    pts = [tuple(p) for p in nv['contorno']]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    extra = EXTRAS.get((clave, nv['id']), [])
    for (a, b, c, d), _ in extra:
        xs += [a, c]; ys += [b, d]
    x0, x1, y0, y1 = min(xs) - 0.6, max(xs) + 0.6, min(ys) - 0.6, max(ys) + 0.6
    W = int((x1 - x0) * S) + 2 * MG
    H = int((y1 - y0) * S) + 2 * MG + 90
    im = Image.new('RGB', (W, H), C_FONDO)
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (MG + (x - x0) * S, MG + 90 + (y1 - y) * S)

    def R(a, b, c, e):
        (X0, Y0), (X1, Y1) = P(a, b), P(c, e)
        return (min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1))

    z0 = nv['z0']; zc = z0 + CORTE
    # elementos exteriores de referencia
    for (a, b, c, e), nombre in extra:
        r = R(a, b, c, e)
        for k in range(int(r[0]), int(r[2]), 12):
            d.line([(k, r[1]), (min(k + 6, r[2]), r[1])], fill=C_SUAVE, width=1)
            d.line([(k, r[3]), (min(k + 6, r[2]), r[3])], fill=C_SUAVE, width=1)
        for k in range(int(r[1]), int(r[3]), 12):
            d.line([(r[0], k), (r[0], min(k + 6, r[3]))], fill=C_SUAVE, width=1)
            d.line([(r[2], k), (r[2], min(k + 6, r[3]))], fill=C_SUAVE, width=1)
        f = F(13)
        tw = d.textlength(nombre, font=f)
        if tw < r[2] - r[0] - 4:
            d.text(((r[0] + r[2]) / 2 - tw / 2, (r[1] + r[3]) / 2 - 7), nombre, font=f, fill=C_SUAVE)
        else:
            d.text((r[0] + 2, r[1] - 16), nombre, font=f, fill=C_SUAVE)
    # cuartos
    for c in nv['cuartos']:
        col = C_ESC if c['escalera'] else (C_ABIER if c['tipo'] == 'abierto' else C_CERR)
        for rr in c['rects']:
            d.rectangle(R(*rr), fill=col)
    # mobiliario de referencia (camas, mesas, estación)
    for (niv, tipo, a, b, c, e) in ed.get('muebles', []):
        if niv != nv['id']:
            continue
        col = {'cama': (255, 255, 255), 'mesa': (225, 214, 196), 'estacion': (205, 196, 182)}.get(tipo, (230, 230, 230))
        d.rectangle(R(a, b, c, e), fill=col, outline=(160, 150, 138), width=1)
    # escaleras: huellas
    for esc in ed['escaleras']:
        if not (esc['z0'] - 0.1 <= z0 <= esc['z1'] + 0.1):
            continue
        for (a, b, c, e, za, zb) in esc['cajas']:
            if nv['id'] == 'pa' and zb < zc - 0.01 and False:
                continue
            d.rectangle(R(a, b, c, e), outline=(150, 160, 170), width=1)
        mp = esc['marcha']
        tramo = mp[1:4] if nv['id'] == 'pb' else mp[4:7]
        d.line([P(*p) for p in tramo], fill=(70, 90, 110), width=2)
        ex, ey = P(*tramo[-1]); px, py = P(*tramo[-2])
        ang = math.atan2(ey - py, ex - px)
        for s in (-1, 1):
            d.line([(ex, ey), (ex - 12 * math.cos(ang + s * 0.45), ey - 12 * math.sin(ang + s * 0.45))], fill=(70, 90, 110), width=2)
        sx, sy = P(*tramo[0])
        d.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=(70, 90, 110))
        d.text((sx + 6, sy - 18), 'sube' if nv['id'] == 'pb' else 'llega', font=F(12, True), fill=(70, 90, 110))
    # muros cortados a 1,2 m; huecos de ventanas y puertas
    for m in nv['muros']:
        c0, c1 = sorted((m['c0'], m['c1']))
        piezas = []
        cur = m['u0']
        hs = sorted(m['huecos'])
        for (a, b, za, zb) in hs:
            if za <= zc <= zb:      # el hueco corta el plano
                if a > cur:
                    piezas.append((cur, a))
                cur = max(cur, b)
                es_puerta = za <= z0 + 0.3
                if m['eje'] == 'x':
                    r = R(a, c0, b, c1)
                else:
                    r = R(c0, a, c1, b)
                if es_puerta:
                    # arco de giro
                    rad = (b - a) * S
                    if m['eje'] == 'x':
                        hx, hy = P(a, (c0 + c1) / 2)
                        d.arc((hx - rad, hy - rad, hx + rad, hy + rad), 270, 360, fill=(150, 120, 90), width=1)
                        d.line([(hx, hy), (hx, hy - rad)], fill=(150, 120, 90), width=2)
                    else:
                        hx, hy = P((c0 + c1) / 2, a)
                        d.arc((hx - rad, hy - rad, hx + rad, hy + rad), 0, 90, fill=(150, 120, 90), width=1)
                        d.line([(hx, hy), (hx + rad, hy)], fill=(150, 120, 90), width=2)
                else:
                    d.rectangle(r, fill=(255, 255, 255))
                    if m['eje'] == 'x':
                        for cc in (c0 + (c1 - c0) * 0.35, c0 + (c1 - c0) * 0.65):
                            d.line([P(a, cc), P(b, cc)], fill=C_VENT, width=2)
                    else:
                        for cc in (c0 + (c1 - c0) * 0.35, c0 + (c1 - c0) * 0.65):
                            d.line([P(cc, a), P(cc, b)], fill=C_VENT, width=2)
        if m['u1'] > cur:
            piezas.append((cur, m['u1']))
        for (a, b) in piezas:
            d.rectangle(R(a, c0, b, c1) if m['eje'] == 'x' else R(c0, a, c1, b), fill=C_MURO)
    # recorrido de prueba sobre este nivel
    for ruta in rutas:
        seg = [P(p['x'], p['y']) for p in ruta['puntos'] if z0 - 0.3 <= p['z'] <= nv['z1'] - 0.3 or
               (nv['id'] == 'pb' and p['z'] < 1.7) or (nv['id'] == 'pa' and p['z'] >= 1.7)]
        for a, b in zip(seg[:-1], seg[1:]):
            if math.dist(a, b) < S * 0.6:
                d.line([a, b], fill=C_RUTA, width=3)
    # rótulos
    for c in nv['cuartos']:
        big = max(c['rects'], key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
        cx, cy = P((big[0] + big[2]) / 2, (big[1] + big[3]) / 2)
        wpx = (big[2] - big[0]) * S - 8
        hpx = (big[3] - big[1]) * S
        nombre = c['nombre']
        for sz in (15, 13, 11, 10):
            f = F(sz, True)
            palabras = nombre.split(' ')
            lineas, cur = [], ''
            for w in palabras:
                t = (cur + ' ' + w).strip()
                if d.textlength(t, font=f) <= wpx or not cur:
                    cur = t
                else:
                    lineas.append(cur); cur = w
            lineas.append(cur)
            if max(d.textlength(l, font=f) for l in lineas) <= max(wpx, 30) and len(lineas) * (sz + 3) + 16 <= max(hpx, 24):
                break
        alto = len(lineas) * (sz + 3)
        yy = cy - alto / 2 - 7
        for l in lineas:
            tw = d.textlength(l, font=f)
            d.text((cx - tw / 2, yy), l, font=f, fill=C_TXT); yy += sz + 3
        if not c['escalera'] and c['area'] >= 3:
            t = f"{c['area']:.1f} m²".replace('.', ',')
            ff = F(max(10, sz - 3))
            d.text((cx - d.textlength(t, font=ff) / 2, yy + 1), t, font=ff, fill=C_SUAVE)
    # orientación
    o = ORIENT[clave]
    f = F(14, True)
    if o['abajo']:
        t = '▼ ' + o['abajo']; d.text((W / 2 - d.textlength(t, font=f) / 2, H - MG / 2 - 8), t, font=f, fill=C_SUAVE)
    if o['arriba']:
        t = '▲ ' + o['arriba']; d.text((W / 2 - d.textlength(t, font=f) / 2, 90 + MG / 2 - 14), t, font=f, fill=C_SUAVE)
    if o['izq']:
        t = '◀ ' + o['izq']
        tmp = Image.new('RGBA', (int(d.textlength(t, font=f)) + 4, 20), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((2, 0), t, font=f, fill=C_SUAVE)
        tmp = tmp.rotate(90, expand=True)
        im.paste(tmp, (8, int(H / 2 - tmp.height / 2)), tmp)
    if o['der']:
        t = o['der'] + ' ▶'
        tmp = Image.new('RGBA', (int(d.textlength(t, font=f)) + 4, 20), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((2, 0), t, font=f, fill=C_SUAVE)
        tmp = tmp.rotate(-90, expand=True)
        im.paste(tmp, (W - 8 - tmp.width, int(H / 2 - tmp.height / 2)), tmp)
    # título y escala
    tit = f"{ed['nombre']} · {nv['nombre']}"
    sz = 24
    while sz > 14 and d.textlength(tit, font=F(sz, True)) > W - (MG - 30) - 12:
        sz -= 1
    d.text((MG - 30, 16), tit, font=F(sz, True), fill=C_TXT)
    bx, by = MG - 30, 54
    d.rectangle((bx, by, bx + 5 * S, by + 7), fill=C_TXT)
    d.rectangle((bx + 2.5 * S, by, bx + 5 * S, by + 7), fill=(200, 200, 200))
    d.text((bx, by + 10), '0       2,5       5 m', font=F(12), fill=C_SUAVE)
    return im


def leyenda(w):
    im = Image.new('RGB', (w, 120), C_FONDO)
    d = ImageDraw.Draw(im)
    items = [(C_CERR, 'Cuarto (cerrado)'), (C_ABIER, 'Circulación abierta'), (C_ESC, 'Escalera'),
             (C_MURO, 'Muro cortado a 1,2 m'), (C_VENT, 'Ventana'), ((150, 120, 90), 'Puerta'),
             ((255, 255, 255), 'Cama 0,95 × 2,0 m (las que caben)'), (C_RUTA, 'Recorrido de prueba')]
    x = 20
    for col, t in items:
        d.rectangle((x, 30, x + 26, 48), fill=col)
        d.text((x + 34, 30), t, font=F(15), fill=C_TXT)
        x += 46 + d.textlength(t, font=F(15))
    d.text((20, 70), 'Distribución interpretada de los croquis y fotos. Medidas proporcionales, no un levantamiento.',
           font=F(15), fill=C_SUAVE)
    return im


def supuestos(w, lista, rutas):
    lineas = []
    f = F(15)
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    for i, s in enumerate(lista, 1):
        palabras = f'{i}. {s}'.split(' ')
        cur = ''
        for p in palabras:
            t = (cur + ' ' + p).strip()
            if d0.textlength(t, font=f) < w - 60:
                cur = t
            else:
                lineas.append(cur); cur = '    ' + p
        lineas.append(cur)
    res = []
    for r in rutas:
        pts = r['puntos']
        res.append(f"• {r['nombre']}: {pts[-1]['d']:.0f} m recorridos, de {pts[0]['z']:.2f} a {pts[-1]['z']:.2f} m de altura; "
                   f"escalón máx. {max(abs(p['paso']) for p in pts):.2f} m · altura libre mín. {min(p['libre'] for p in pts):.2f} m · "
                   f"choques con muros: {sum(p['choque'] for p in pts)}.".replace('.', ',', 0))
    H = 90 + 22 * len(lineas) + 60 + 44 * len(res)
    im = Image.new('RGB', (w, H), C_FONDO)
    d = ImageDraw.Draw(im)
    d.text((20, 20), 'Supuestos y pendientes', font=F(22, True), fill=C_TXT)
    y = 60
    for l in lineas:
        d.text((20, y), l, font=f, fill=C_TXT); y += 22
    y += 20
    d.text((20, y), 'Prueba de subida (rayos sobre el modelo 3D)', font=F(22, True), fill=C_TXT); y += 36
    for t in res:
        cur = ''
        for p in t.split(' '):
            tt = (cur + ' ' + p).strip()
            if d.textlength(tt, font=f) < w - 60:
                cur = tt
            else:
                d.text((20, y), cur, font=f, fill=C_TXT); y += 22; cur = '   ' + p
        d.text((20, y), cur, font=f, fill=C_TXT); y += 26
    return im


if __name__ == '__main__':
    data = json.load(open(os.path.join(OUT, 'interiores.json')))
    rec = json.load(open(os.path.join(OUT, 'recorrido.json')))
    rutas = {'casa': [r for r in rec if r['nombre'].startswith('Casa')], 'gris': [r for r in rec if r['nombre'].startswith('Edificio')]}
    hojas = {}
    for clave in ('casa', 'gris'):
        ed = data[clave]
        for nv in ed['niveles']:
            im = dibujar(clave, ed, nv, rutas[clave])
            im.save(os.path.join(OUT, f'plano_{clave}_{nv["id"]}.png'))
            hojas[(clave, nv['id'])] = im
            print('plano', clave, nv['id'], im.size)
    # lámina: casa PB + PA arriba, gris PB + PA abajo
    fila1 = [hojas[('casa', 'pb')], hojas[('casa', 'pa')]]
    fila2 = [hojas[('gris', 'pb')], hojas[('gris', 'pa')]]
    W = max(sum(i.width for i in fila1), sum(i.width for i in fila2)) + 80
    ley = leyenda(W)
    import sys; sys.path.insert(0, os.path.dirname(__file__))
    import interiores
    sup = supuestos(W, interiores.SUPUESTOS, rec)
    Ht = 90 + ley.height + max(i.height for i in fila1) + max(i.height for i in fila2) + sup.height + 40
    L = Image.new('RGB', (W, Ht), C_FONDO)
    d = ImageDraw.Draw(L)
    d.text((24, 24), 'Etapa 3 · Distribución interior y conexión vertical · Altos de San Cristóbal', font=F(34, True), fill=C_TXT)
    y = 90
    L.paste(ley, (0, y)); y += ley.height
    x = 20
    for i in fila1:
        L.paste(i, (x, y)); x += i.width + 40
    y += max(i.height for i in fila1)
    x = 20
    for i in fila2:
        L.paste(i, (x, y)); x += i.width + 40
    y += max(i.height for i in fila2) + 20
    L.paste(sup, (0, y))
    L.save(os.path.join(OUT, 'planos_etapa3.jpg'), quality=90)
    print('planos_etapa3.jpg', L.size)
