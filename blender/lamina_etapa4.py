"""Láminas de la etapa 4 (no necesita Blender): vistas interiores amuebladas y comparación con Antigravity."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
REF = os.path.join(ROOT, 'web', 'public', 'fotos-despues')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONDO, TXT, SUAVE = (250, 249, 246), (34, 40, 46), (110, 118, 126)


def F(sz, b=False):
    try:
        return ImageFont.truetype(FB if b else FR, sz)
    except Exception:
        return ImageFont.load_default()


GRIS = [('int_gris_hosp', 'Personas encamadas · 10 camas, estación de enfermería al fondo'),
        ('int_gris_hosp2', 'Personas encamadas · desde la puerta del pasillo'),
        ('int_gris_salon2', 'Salón amarillo · 4 camas, personas con movilidad reducida'),
        ('int_gris_salonB', 'Salón grande 2 · 6 camas, personas que deambulan'),
        ('int_gris_salonA', 'Salón grande 1 · 2 camas, personas que deambulan'),
        ('int_gris_refrigerios', 'Terraza de arriba · área de coffee break'),
        ('int_gris_bano_acc', 'Baño accesible para usuarios (planta baja)'),
        ('int_gris_deposito', 'Depósito y ropería (antes biblioteca)'),
        ('int_gris_cocina', 'Cocineta del área de coffee break'),
        ('int_gris_acceso', 'Acceso, pasillo y escalera')]
CASA = [('int_casa_recepcion', 'Recepción 24 h'),
        ('int_casa_comedor', 'Comedor y TV (a la izquierda, puertas de vidrio del semiprivado 2)'),
        ('int_casa_vip', 'Cuarto semiprivado 2 (el de puertas de vidrio)'),
        ('int_casa_suite', 'Suite'),
        ('int_casa_semipriv', 'Cuarto semiprivado 1'),
        ('int_casa_terapia', 'Terapia con familiares'),
        ('int_casa_talleres', 'Talleres: pintura, acuarela, costura'),
        ('int_casa_consultorio', 'Consultorio de salud'),
        ('int_casa_cocina', 'Cocina de acero inoxidable'),
        ('int_casa_bano', 'Baño compartido de los semiprivados'),
        ('int_casa_recamara', 'Recámara alta · 4.º cuarto privado')]
PARES = [('hospitalizacion', 'int_gris_hosp', 'Personas encamadas'), ('salon-2', 'int_gris_salon2', 'Salón amarillo'),
         ('refrigerios', 'int_gris_refrigerios', 'Área de coffee break'), ('bano-accesible', 'int_gris_bano_acc', 'Baño accesible'),
         ('comedor', 'int_casa_comedor', 'Comedor'), ('cuarto-vip', 'int_casa_vip', 'Cuarto privado'),
         ('terapia', 'int_casa_terapia', 'Terapia'), ('cocina', 'int_casa_cocina', 'Cocina')]


def celda(path, titulo, w, h=None):
    im = Image.open(path).convert('RGB')
    if h:
        r = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        x0, y0 = (im.width - w) // 2, (im.height - h) // 2
        im = im.crop((x0, y0, x0 + w, y0 + h))
    else:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    c = Image.new('RGB', (w, im.height + 38), FONDO)
    ImageDraw.Draw(c).text((2, 9), titulo, font=F(18, True), fill=TXT)
    c.paste(im, (0, 38))
    return c


def lamina(items, titulo, sub, nombre, cols=2, W=2200):
    w = (W - (cols - 1) * 18) // cols
    cs = [celda(os.path.join(OUT, n + '.png'), t, w) for n, t in items if os.path.exists(os.path.join(OUT, n + '.png'))]
    filas = [cs[i:i + cols] for i in range(0, len(cs), cols)]
    H = 130 + sum(max(c.height for c in f) + 22 for f in filas) + 50
    L = Image.new('RGB', (W + 60, H), FONDO)
    d = ImageDraw.Draw(L)
    d.text((30, 26), titulo, font=F(36, True), fill=TXT)
    d.text((30, 80), sub, font=F(18), fill=SUAVE)
    y = 130
    for f in filas:
        x = 30
        for c in f:
            L.paste(c, (x, y)); x += c.width + 18
        y += max(c.height for c in f) + 22
    d.text((30, y + 4), 'Muebles y acabados: modelos de referencia hechos en Blender sobre las medidas estimadas del modelo; '
                         'no son productos cotizados.', font=F(16), fill=SUAVE)
    L.save(os.path.join(OUT, nombre), quality=88)
    print(nombre, L.size)


def comparacion(nombre='comparacion_antigravity.jpg', W=2200):
    w = (W - 18) // 2
    h = int(w * 9 / 16)
    filas = []
    for ref, vista, t in PARES:
        a, b = os.path.join(REF, ref + '.jpg'), os.path.join(OUT, vista + '.png')
        if os.path.exists(a) and os.path.exists(b):
            filas.append((celda(a, f'{t} · imagen de Antigravity (idea)', w, h), celda(b, f'{t} · modelo 3D (medidas del modelo)', w, h)))
    H = 150 + len(filas) * (h + 38 + 22) + 40
    L = Image.new('RGB', (W + 60, H), FONDO)
    d = ImageDraw.Draw(L)
    d.text((30, 26), 'Lo que propuso Antigravity y cómo queda en el modelo 3D', font=F(36, True), fill=TXT)
    d.text((30, 80), 'A la izquierda, la imagen generada sobre la foto real; a la derecha, el mismo uso amueblado dentro del '
                     'modelo, con las camas y el paso que de verdad caben.', font=F(18), fill=SUAVE)
    y = 150
    for a, b in filas:
        L.paste(a, (30, y)); L.paste(b, (30 + w + 18, y))
        y += a.height + 22
    L.save(os.path.join(OUT, nombre), quality=86)
    print(nombre, L.size)


if __name__ == '__main__':
    lamina(GRIS, 'Etapa 4 · Edificio gris amueblado', 'Encamados, salones, refrigerios y servicios según el programa de la '
           'propietaria (26 camas en total: 22 en el gris, 4 en la casa).', 'interiores_gris_etapa4.jpg')
    lamina(CASA, 'Etapa 4 · Casa amarilla amueblada', 'Recepción 24 h, áreas comunes, consultorio y los 4 cuartos privados '
           '(2 semiprivados, suite y recámara alta).', 'interiores_casa_etapa4.jpg')
    comparacion()
