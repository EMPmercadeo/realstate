"""
Vistas de la MUESTRA (casa amarilla: frente, acceso y recepción) para comparar antes/después.
Renderiza desde cualquier .blend sin modificarlo.

Uso:
  python3 blender/muestra_vistas.py -- --blend build/bloqueo/bloqueo.blend --sufijo antes --ancho 960 --muestras 24
  blender -b -P blender/muestra_vistas.py -- --blend build/muestra/muestra.blend --sufijo despues --ancho 1920 --muestras 256 --gpu
Salida: build/muestra/<vista>_<sufijo>.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio
import bloqueo_vistas as BV
from vistas_interiores import INTERIORES

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BLEND = os.path.join(ROOT, arg('--blend', 'build/bloqueo/bloqueo.blend'))
SUFIJO = arg('--sufijo', 'antes')
ANCHO = int(arg('--ancho', '960'))
MUESTRAS = int(arg('--muestras', '24'))
OUT = os.path.join(ROOT, 'build', 'muestra')
os.makedirs(OUT, exist_ok=True)

# vista -> (edificio, pos local xyz, mira local xyz, lente mm, exposición)
VISTAS = {
    # cámara ajustada a la foto real de la fachada (más cerca del portón que la de la etapa 2)
    'm_frente': (sitio.CASA, (4.6, -15.2, 1.5), (6.0, -2.0, 4.3), 16, None),
    # ya dentro del portón, caminando hacia la entrada principal (ojos a 1,60 m)
    'm_acceso': (sitio.CASA, (5.6, -6.3, 1.6), (9.4, 0.0, 1.5), 18, None),
    # recepción (misma cámara de la etapa 4)
    'm_recepcion': INTERIORES['int_casa_recepcion'][:4] + (float(arg('--expo-int', '-1.0')),),
}
# resto del lote: las cámaras de las fotos (bloqueo_vistas) y una vista aérea de dron
for k in ('casa_patio', 'gris_galeria', 'gris_acceso'):
    v = BV.VISTAS[k]
    VISTAS['v_' + k] = (sitio.CASA if v['edif'] == 'casa' else sitio.GRIS, v['pos'], v['mira'], v['lens'], None)
VISTAS['v_aerea'] = (sitio.CASA, (62.0, -8.0, 72.0), (4.0, 25.0, 0.0), 26, None)
pedidas = arg('--vistas', 'todas')
pedidas = ['m_frente', 'm_acceso', 'm_recepcion'] if pedidas == 'todas' else list(VISTAS) if pedidas == 'lote' else pedidas.split(',')

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
EXPO_ESCENA = sc.view_settings.exposure          # exteriores: la exposición guardada en el .blend
for o in bpy.data.objects:
    if o.name.startswith('satelite'):
        o.hide_render = True
    elif o.type == 'LIGHT':
        o.hide_render = False

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
                print('GPU:', tipo, flush=True)
                break
        except Exception:
            pass
cy.samples = MUESTRAS
cy.use_denoising = True
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.02
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 3; cy.transmission_bounces = 6
cy.transparent_max_bounces = 48
cy.caustics_reflective = False; cy.caustics_refractive = False; cy.blur_glossy = 1.0
sc.render.resolution_x = ANCHO
sc.render.resolution_y = int(ANCHO * 9 / 16)
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'
if not sc.view_settings.look or sc.view_settings.look == 'None':
    sc.view_settings.look = 'AgX - Medium High Contrast'

for k in pedidas:
    E, p, q, lens, expo = VISTAS[k]
    X, Y = sitio.local_a_m(E, p[0], p[1])
    TX, TY = sitio.local_a_m(E, q[0], q[1])
    cam = bpy.data.cameras.new(k)
    cam.lens = lens; cam.sensor_width = 36; cam.clip_start = 0.05; cam.clip_end = 6000
    co = bpy.data.objects.new('cam_' + k, cam)
    sc.collection.objects.link(co)
    co.location = (X, Y, p[2])
    co.rotation_euler = (Vector((TX, TY, q[2])) - Vector((X, Y, p[2]))).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.view_settings.exposure = EXPO_ESCENA if expo is None else expo
    sc.render.filepath = os.path.join(OUT, f'{k}_{SUFIJO}.png')
    bpy.ops.render.render(write_still=True)
    print('render', k, SUFIJO, flush=True)
