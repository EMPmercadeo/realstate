"""Lámina de comparación de la muestra: foto real | antes | después (sin Blender, solo Pillow).
Uso: python3 blender/lamina_muestra.py m_frente r1 [antes]  -> build/muestra/cmp_m_frente_r1.jpg"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
D = os.path.join(ROOT, 'build', 'muestra')
# la foto 'recepcion.jpg' NO es la recepción real (es un cuarto con cama, según la propietaria): no se compara
FOTOS = {'m_frente': 'web/public/fotos-reales/fachada-frontal.jpg',
         'v_casa_patio': 'web/public/fotos-reales/casa-amarilla-patio.jpg', 'v_gris_galeria': 'web/public/fotos-reales/edificio-gris.jpg',
         'v_gris_acceso': 'web/public/fotos-reales/edificio-gris-noche.jpg'}
vista, despues = sys.argv[1], sys.argv[2]
antes = sys.argv[3] if len(sys.argv) > 3 else 'antes'
H = 450
def fit(im):
    w = int(H * 16 / 9); r = max(w / im.width, H / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2; y = (im.height - H) // 2
    return im.crop((x, y, x + w, y + H))
try:
    font = ImageFont.truetype('DejaVuSans-Bold.ttf', 20)
except Exception:
    font = ImageFont.load_default()
paneles = []
if vista in FOTOS:
    paneles.append(('FOTO REAL', Image.open(os.path.join(ROOT, FOTOS[vista])).convert('RGB')))
paneles.append(('ANTES', Image.open(os.path.join(D, f'{vista}_{antes}.png')).convert('RGB')))
paneles.append(('DESPUÉS', Image.open(os.path.join(D, f'{vista}_{despues}.png')).convert('RGB')))
w = int(H * 16 / 9)
S = Image.new('RGB', (w * len(paneles) + 10 * (len(paneles) - 1), H), 'white')
for i, (t, im) in enumerate(paneles):
    S.paste(fit(im), (i * (w + 10), 0))
    d = ImageDraw.Draw(S)
    tw = d.textlength(t, font=font)
    d.rectangle([i * (w + 10) + 8, 8, i * (w + 10) + 20 + tw, 38], fill=(20, 20, 20))
    d.text((i * (w + 10) + 14, 11), t, fill='white', font=font)
out = os.path.join(D, f'cmp_{vista}_{despues}.jpg')
S.save(out, quality=88)
print(out)
