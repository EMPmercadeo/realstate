"""Renderiza vistas de build/escena.blend.  Uso: python3 blender/render.py <vista> [samples] [ancho]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'renders'); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'escena.blend'))
scene = bpy.context.scene

from programa import GRIS, AMARILLA

def _pos(E, u, v, z):
    return (E['pos'][0] + u, E['pos'][1] + v, z)

G, A = GRIS, AMARILLA
VISTAS = {
    'hospital':   (_pos(G, 8.0, 8.8, 4.75), _pos(G, 13.0, 13.5, 4.3), 20, True),
    'salon_b':    (_pos(G, 1.0, 8.8, 1.5), _pos(G, 6.0, 13.0, 1.2), 20, True),
    'comedor':    (_pos(A, 9.5, 6.0, 1.5), _pos(A, 5.0, 9.0, 1.1), 22, True),
    'recepcion':  (_pos(A, 15.6, 7.0, 1.6), _pos(A, 11.0, 7.0, 1.2), 24, True),
    'terapia':    (_pos(A, 15.6, 9.6, 1.6), _pos(A, 11.0, 13.0, 1.2), 22, True),
    'cto1':       (_pos(A, 3.8, 4.0, 1.5), _pos(A, 0.8, 6.5, 1.0), 22, True),
    'terraza':    (_pos(G, 25.5, 1.0, 4.9), _pos(G, 19.5, 8.0, 4.0), 24, False),
    'planta_gris_p2': (_pos(G, 12, 8, 42), _pos(G, 12, 8.01, 3), 40, True),
    'planta_amarilla': (_pos(A, 8, 7, 40), _pos(A, 8, 7.01, 0), 40, True),
    # nombre: (posición cámara, objetivo, lente mm, ocultar techos?)
    'aerea':      ((78, -30, 48), (16, 40, 2), 32, False),
    'aerea_sur':  ((60, -40, 40), (14, 22, 3), 35, False),
    'calle':      ((42, 44, 1.8), (14, 61, 3), 28, False),
    'casa':       ((36, 68, 1.7), (12, 61, 3), 30, False),
    'gris':       ((40, 2, 1.7), (12, 16, 3), 28, False),
    'gazebo':     ((30, 38, 1.6), (16, 44, 1.5), 28, False),
}


def camara(loc, target, lens):
    cam = bpy.data.cameras.new('cam'); cam.lens = lens; cam.clip_end = 600
    co = bpy.data.objects.new('cam', cam); scene.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    return co


def render(vista, samples=64, w=1600):
    loc, tgt, lens, sin_techo = VISTAS[vista]
    camara(loc, tgt, lens)
    if sin_techo:
        planta = vista.startswith('planta')
        for o in bpy.data.objects:
            if o.get('techo') or (planta and o.get('cielo')):
                o.hide_render = True
        # ocultar piso 2 del gris si la vista es interior del piso 2? no: ocultar todo lo que esté por encima de la cámara + 1 m
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith(('gris_', 'amarilla_')) and not o.get('techo') and not (o.get('cielo') and not planta):
                zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
                if zmin > loc[2] + 1.2:
                    o.hide_render = True
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.use_adaptive_sampling = True
    scene.render.resolution_x = w; scene.render.resolution_y = int(w * 9 / 16)
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.image_settings.file_format = 'JPEG'; scene.render.image_settings.quality = 92
    scene.render.filepath = os.path.join(OUT, f'{vista}.jpg')
    bpy.ops.render.render(write_still=True)
    print('render ->', scene.render.filepath)


if __name__ == '__main__':
    v = sys.argv[1] if len(sys.argv) > 1 else 'aerea'
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 64
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
    render(v, s, w)
