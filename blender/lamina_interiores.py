"""Lámina de revisión de la etapa 3: cortes sin cubierta + vistas desde adentro (no necesita Blender)."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def F(sz, b=False):
    try:
        return ImageFont.truetype(FB if b else FR, sz)
    except Exception:
        return ImageFont.load_default()


CORTES = [('axo_casa_pb', 'Casa amarilla · planta baja sin techo'), ('axo_casa_pa', 'Casa amarilla · planta alta (torre)'),
          ('axo_gris_pb', 'Edificio gris · planta baja sin techo'), ('axo_gris_pa', 'Edificio gris · planta alta y terraza con verjas')]
VISTAS = [('int_casa_recepcion', 'Casa · desde la recepción hacia el comedor'),
          ('int_casa_escalera', 'Casa · escalera desde el pasillo'),
          ('int_casa_gerencia', 'Casa · oficina del gerente hacia el balcón'),
          ('int_gris_escalera', 'Gris · estar y escalera, planta baja'),
          ('int_gris_hosp', 'Gris · hospitalización, planta alta'),
          ('int_gris_terraza', 'Gris · terraza cerrada con verjas')]


def celda(nombre, titulo, w):
    p = os.path.join(OUT, nombre + '.png')
    im = Image.open(p).convert('RGB')
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    c = Image.new('RGB', (w, im.height + 40), (250, 249, 246))
    d = ImageDraw.Draw(c)
    d.text((4, 10), titulo, font=F(18, True), fill=(34, 40, 46))
    c.paste(im, (0, 40))
    return c


def fila(items, w, gap=16):
    cs = [celda(n, t, w) for n, t in items if os.path.exists(os.path.join(OUT, n + '.png'))]
    if not cs:
        return None
    H = max(c.height for c in cs)
    f = Image.new('RGB', (len(cs) * w + (len(cs) - 1) * gap, H), (250, 249, 246))
    x = 0
    for c in cs:
        f.paste(c, (x, 0)); x += w + gap
    return f


if __name__ == '__main__':
    W = 1800
    filas = [fila(CORTES[:2], (W - 16) // 2), fila(CORTES[2:], (W - 16) // 2),
             fila(VISTAS[:3], (W - 32) // 3), fila(VISTAS[3:], (W - 32) // 3)]
    filas = [f for f in filas if f]
    H = 130 + sum(f.height + 24 for f in filas) + 60
    L = Image.new('RGB', (W + 60, H), (250, 249, 246))
    d = ImageDraw.Draw(L)
    d.text((30, 26), 'Etapa 3 · Interiores en bloqueo (materiales neutros)', font=F(34, True), fill=(34, 40, 46))
    d.text((30, 78), 'Muros con huecos reales de puertas y ventanas, escaleras caminables y mobiliario de referencia '
                     '(bloques para leer uso y escala).', font=F(17), fill=(110, 118, 126))
    y = 130
    for f in filas:
        L.paste(f, (30, y)); y += f.height + 24
    d.text((30, y + 10), 'Distribución interpretada de los croquis y fotos; medidas proporcionales, no un levantamiento.',
           font=F(16), fill=(110, 118, 126))
    L.save(os.path.join(OUT, 'interiores_etapa3.jpg'), quality=86)
    print('interiores_etapa3.jpg', L.size)
