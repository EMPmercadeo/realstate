"""
Texturas de follaje para las copas de árboles, hechas con las mismas hojas 3D de vegetacion.py:
se arma una rama con hojas de mango (o de hoja fina), se renderiza desde arriba con fondo transparente
y se guarda como PNG con alfa. Resultado más creíble que las texturas dibujadas a mano.
Uso: python3 blender/gen_tarjetas.py   ->  assets/textures/gen/copa_mango.png, copa_fina.png
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector, Matrix
import vegetacion as V

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEN = os.path.join(ROOT, 'assets', 'textures', 'gen')

TIPOS = {
    # nombre: (largo y ancho de hoja, hojas, verde oscuro, verde claro)
    'copa_mango': ((0.24, 0.06), 900, (0.025, 0.06, 0.012), (0.12, 0.20, 0.035)),
    'copa_fina': ((0.10, 0.035), 1600, (0.035, 0.08, 0.015), (0.16, 0.25, 0.05)),
}


def rama(col, hoja, n, c0, c1, seed):
    rnd = random.Random(seed)
    M = V.Malla()
    mh = M.mat(V.mat_hoja('hoja_tarjeta', c0, c1, transl=0.25, rough=0.35))
    mt = M.mat(V.mat_tronco('rama_t', (0.14, 0.11, 0.08), (0.25, 0.2, 0.14)))
    lv, lc = V._hoja(*hoja, curva=0.25)
    # 5-7 manojos irregulares (sin ramas a la vista): el contorno de la tarjeta queda dentado, no circular
    manojos = []
    for k in range(rnd.randint(5, 7)):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.15, 0.55)
        manojos.append((Vector((math.cos(a) * r, math.sin(a) * r, 0)), rnd.uniform(0.22, 0.4)))
    for _ in range(n):
        c, rr = manojos[rnd.randrange(len(manojos))]
        r = math.sqrt(rnd.random()) * rr
        a = rnd.uniform(0, 2 * math.pi)
        p = c + Vector((math.cos(a) * r, math.sin(a) * r, rnd.uniform(-0.06, 0.12) * (1 - r / rr)))
        d = Vector((math.cos(a + rnd.uniform(-1.0, 1.0)), math.sin(a + rnd.uniform(-1.0, 1.0)), rnd.uniform(-0.5, 0.4))).normalized()
        t, s, nn = V._base(d)
        rot = Matrix.Rotation(rnd.uniform(-0.8, 0.8), 3, t) @ Matrix((t, s, nn)).transposed()
        e = rnd.uniform(0.7, 1.15)
        M.add([p + rot @ (v * e) for v in lv], lc, rnd.random() * 0.6 + 0.4 * (p.z + 0.1) / 0.25, mh)
    return M.objeto('rama', col)


for nombre, (hoja, n, c0, c1) in TIPOS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    V._M.clear()
    rama(sc.collection, hoja, n, c0, c1, seed=len(nombre))
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.85, 0.95, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    sol = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN')); sc.collection.objects.link(sol)
    sol.data.energy = 1.6; sol.rotation_euler = (math.radians(25), math.radians(10), 0)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0; cam.location = (0, 0, 3); sc.camera = cam
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = os.path.join(GEN, nombre + '.png')
    bpy.ops.render.render(write_still=True)
    print('tarjeta', nombre, flush=True)
