"""Render rápido de una vista desde un .blend (Cycles CPU), para comparar con fotos.
Uso: python3 blender/vista_rapida.py -- --blend build/bloqueo/bloqueo.blend --edif gris --pos 4,-9,1.6
     --mira 4,4,3.5 --lens 27 --ancho 960 --alto 540 --muestras 16 --out salida.png [--expo -0.9]
pos/mira en unidades de diseño del edificio (sitio.local_a_m) salvo --mundo (metros del modelo)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d
bpy.ops.wm.open_mainfile(filepath=arg('--blend', 'build/bloqueo/bloqueo.blend'))
import sitio
E = {'casa': sitio.CASA, 'gris': sitio.GRIS}.get(arg('--edif', 'gris'))
def P(s):
    x, y, z = [float(v) for v in s.split(',')]
    if '--mundo' in argv:
        return Vector((x, y, z))
    X, Y = sitio.local_a_m(E, x, y)
    return Vector((X, Y, z))
sc = bpy.context.scene
pos, mira = P(arg('--pos')), P(arg('--mira'))
cam = bpy.data.cameras.new('cam_rapida'); cam.lens = float(arg('--lens', '27')); cam.sensor_width = 36
cam.clip_start = 0.05; cam.clip_end = 3000
co = bpy.data.objects.new('cam_rapida', cam); sc.collection.objects.link(co)
co.location = pos; co.rotation_euler = (mira - pos).to_track_quat('-Z', 'Y').to_euler()
sc.camera = co
for o in bpy.data.objects:
    if o.name == 'satelite':
        o.hide_render = True
    if o.type == 'LIGHT' and o.data.type in ('POINT', 'AREA', 'SPOT'):
        o.hide_render = '--luces' not in argv          # --luces: enciende las luces interiores
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(arg('--muestras', '16'))
sc.cycles.use_denoising = True
if '--luces' in argv:      # mismos ajustes que las vistas interiores de bloqueo.py
    sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x = int(arg('--ancho', '960')); sc.render.resolution_y = int(arg('--alto', '540'))
sc.render.resolution_percentage = 100
if arg('--expo'):
    sc.view_settings.exposure = float(arg('--expo'))
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.abspath(arg('--out', 'vista.png'))
bpy.ops.render.render(write_still=True)
print('ok', sc.render.filepath)
