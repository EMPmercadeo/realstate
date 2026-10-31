"""
Renderiza vistas interiores desde build/bloqueo/bloqueo.blend (lo genera bloqueo.py) sin reconstruir el modelo.
Uso:
  python3 blender/render_interiores.py -- --vistas int_gris_hosp,int_casa_vip --muestras 20 --ancho 1280 [--gpu]
  blender -b -P blender/render_interiores.py -- --vistas todas --muestras 128 --ancho 1920 --gpu   (PC con RTX)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio
from vistas_interiores import INTERIORES

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'bloqueo')
vistas = arg('--vistas', 'todas')
vistas = list(INTERIORES) if vistas == 'todas' else vistas.split(',')
MUESTRAS = int(arg('--muestras', '20'))
ANCHO = int(arg('--ancho', '1280'))

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'bloqueo.blend'))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        o.hide_render = False          # luces de techo, lámparas y sol
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
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 2; cy.transmission_bounces = 4
cy.caustics_reflective = False; cy.caustics_refractive = False; cy.blur_glossy = 1.0
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03
sc.render.resolution_x = ANCHO; sc.render.resolution_y = int(ANCHO * 9 / 16)
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
for k in vistas:
    E, p, q, lens, expo = INTERIORES[k]
    X, Y = sitio.local_a_m(E, p[0], p[1]); TX, TY = sitio.local_a_m(E, q[0], q[1])
    cam = bpy.data.cameras.new(k); cam.lens = lens; cam.sensor_width = 36; cam.clip_start = 0.05
    co = bpy.data.objects.new('cam_' + k, cam); sc.collection.objects.link(co)
    co.location = (X, Y, p[2])
    co.rotation_euler = (Vector((TX, TY, q[2])) - Vector((X, Y, p[2]))).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.view_settings.exposure = expo
    sc.render.filepath = os.path.join(OUT, k + '.png')
    bpy.ops.render.render(write_still=True)
    print('render', k, flush=True)
