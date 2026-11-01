"""
Panorámicas 360° (equirectangulares) con Cycles desde build/bloqueo/bloqueo.blend, para el visor 360 de la web.

Cada panorámica es una foto esférica renderizada rayo por rayo: en la web pesa ~1-3 MB y se ve como una foto
real que el visitante gira con el dedo o el mouse (web/src/visor/pano360.ts).

Uso:
  python3 blender/panoramas.py -- --ids hosp@gris,galeria@gris --ancho 2048 --muestras 24          (CPU, prueba)
  blender -b -P blender/panoramas.py -- --ids todas --ancho 6144 --muestras 256 --gpu            (RTX: final)
Salida: build/pano/<id>.png → web/public/pano/<id>.jpg (+ miniatura _m.jpg) y web/src/data/panoramas.json.
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'pano'); os.makedirs(OUT, exist_ok=True)
WEB = os.path.join(ROOT, 'web', 'public', 'pano'); os.makedirs(WEB, exist_ok=True)
MAN = os.path.join(ROOT, 'web', 'src', 'data', 'panoramas.json')

G, C = sitio.GRIS, sitio.CASA
PA_G, PA_C = 3.2, 3.15            # z0 de las plantas altas
# id (el mismo del recorrido: cuarto@edificio), nombre, edificio, (x, y) en unidades de diseño, z de los ojos,
# punto al que mira la vista inicial (x, y), exposición
PANOS = [
    ('hosp@gris', 'Personas encamadas', G, (11.23, 3.40), PA_G + 1.55, (11.23, 7.2), -0.9),
    ('salon2@gris', 'Salón amarillo', G, (7.80, 9.50), PA_G + 1.55, (13.0, 8.3), -0.7),
    ('galeria@gris', 'Área recreativa y de coffee break', G, (1.55, 8.90), PA_G + 1.55, (1.4, 12.5), -0.8),
    ('salonA@gris', 'Salón grande 1', G, (11.30, 3.80), 1.55, (11.0, 0.8), -0.7),
    ('acceso@gris', 'Entrada del edificio gris', G, (2.70, 5.75), 1.55, (8.0, 5.7), -0.7),
    ('recepcion@amarilla', 'Recepción 24 h', C, (8.90, 0.75), 1.55, (7.3, 3.2), -0.7),
    ('comedor@amarilla', 'Comedor y TV', C, (5.00, 3.60), 1.55, (4.6, 6.4), -0.7),
    ('terapia@amarilla', 'Terapia con familiares', C, (10.70, 3.00), 1.55, (12.0, 1.5), -0.7),
    ('suite@amarilla', 'Suite', C, (10.40, 10.20), 1.55, (12.2, 11.0), -0.7),
    ('jardin', 'Jardín interno', G, (-11.6, 7.8), 1.60, (0.0, 8.0), -0.6),
]

sel = arg('--ids', 'todas')
ids = [p[0] for p in PANOS] if sel == 'todas' else sel.split(',')
ANCHO = int(arg('--ancho', '2048'))
MUESTRAS = int(arg('--muestras', '24'))

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'bloqueo', 'bloqueo.blend'))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        o.hide_render = False
    elif o.name.startswith('satelite'):
        o.hide_render = True
cy = sc.cycles
sc.render.engine = 'CYCLES'
cy.device = 'CPU'
if '--gpu' in argv:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = tipo
            prefs.get_devices()
            if any(d.type == tipo for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == tipo
                cy.device = 'GPU'
                print('GPU:', tipo)
                break
        except Exception:
            pass
cy.samples = MUESTRAS
cy.use_denoising = True
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 3; cy.transmission_bounces = 6
cy.caustics_reflective = False; cy.caustics_refractive = False; cy.blur_glossy = 1.0
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
sc.render.resolution_x = ANCHO; sc.render.resolution_y = ANCHO // 2
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'

try:
    man = json.load(open(MAN))
except Exception:
    man = []
por_id = {m['id']: m for m in man}

for (pid, nombre, E, (x, y), z, (mx, my), expo) in PANOS:
    if pid not in ids:
        continue
    X, Y = sitio.local_a_m(E, x, y); MX, MY = sitio.local_a_m(E, mx, my)
    cam = bpy.data.cameras.new('pano_' + pid)
    cam.type = 'PANO'
    try:
        cam.panorama_type = 'EQUIRECTANGULAR'
    except Exception:
        cam.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam.clip_start = 0.03; cam.clip_end = 2000
    co = bpy.data.objects.new('cam_pano', cam); sc.collection.objects.link(co)
    co.location = (X, Y, z)
    # mira en horizontal: el centro de la imagen es la vista inicial del visor
    co.rotation_euler = Vector((MX - X, MY - Y, 0.0)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.view_settings.exposure = expo
    archivo = pid.replace('@', '-')
    sc.render.filepath = os.path.join(OUT, archivo + '.png')
    bpy.ops.render.render(write_still=True)
    try:
        from PIL import Image
        im = Image.open(sc.render.filepath).convert('RGB')
        im.save(os.path.join(WEB, archivo + '.jpg'), quality=86, optimize=True, progressive=True)
        t = im.resize((960, 480), Image.LANCZOS)
        t.crop((180, 60, 780, 400)).save(os.path.join(WEB, archivo + '_m.jpg'), quality=82, optimize=True)
    except ImportError:
        print('falta PIL: convertir a mano', sc.render.filepath)
    por_id[pid] = dict(id=pid, nombre=nombre, archivo=f'/pano/{archivo}.jpg', mini=f'/pano/{archivo}_m.jpg',
                       ancho=ANCHO, muestras=MUESTRAS)
    bpy.data.objects.remove(co, do_unlink=True)
    orden = [p[0] for p in PANOS]
    json.dump(sorted(por_id.values(), key=lambda m: orden.index(m['id']) if m['id'] in orden else 99),
              open(MAN, 'w'), ensure_ascii=False, indent=1)
    print('pano', pid, flush=True)
