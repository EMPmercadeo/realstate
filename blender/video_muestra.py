"""
Video de la muestra: caminata a la altura de los ojos (1,60 m) desde la calle, por el portón, hasta la
recepción. Cámara de 24 mm como en el recorrido de Astra; velocidad de paso (~1,1 m/s); la exposición pasa
de exterior a interior al cruzar la puerta.

Uso (PC con RTX 3080, PowerShell dentro de realstate):
  & $b -b -P blender\\video_muestra.py -- --gpu --ancho 1920 --muestras 128
Prueba rápida (aquí, CPU):
  python3 blender/video_muestra.py -- --ancho 480 --muestras 8 --fps 12
Salida: build/video_muestra/f_####.png y build/video_muestra/recorrido_muestra.mp4
Se puede cortar y reanudar: no repite cuadros que ya existen.
"""
import os, sys, math, glob, shutil, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import sitio

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index(k) + 1] if k in argv else d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build', 'video_muestra')
os.makedirs(OUT, exist_ok=True)
ANCHO = int(arg('--ancho', '1920'))
MUESTRAS = int(arg('--muestras', '128'))
FPS = int(arg('--fps', '24'))
VEL = 1.1                                     # m/s

# recorrido en coordenadas locales de la casa (x a lo largo del frente, y hacia el fondo), z = ojos
# la puerta principal está en x 9,2–9,95 (y = 0) y la recepción se angosta a x ≤ 9,4 pasando y = 0,9
RUTA = [(5.0, -17.0), (5.3, -12.0), (5.8, -8.0), (6.6, -4.6), (8.2, -2.0), (9.4, -0.8), (9.57, -0.1), (9.45, 0.45),
        (8.9, 0.6), (8.3, 0.7)]
# hacia dónde mira en cada punto
MIRA = [(6.0, -2.0, 3.2), (6.2, -2.0, 2.8), (7.0, 0.0, 2.0), (9.0, 0.0, 1.7), (9.6, 1.0, 1.6), (9.6, 1.5, 1.6),
        (8.0, 2.2, 1.5), (7.0, 2.6, 1.4), (6.4, 3.2, 1.3), (6.0, 3.4, 1.2)]
PUERTA = 0.0                                   # y local de la puerta: aquí cambia la exposición
OJOS = 1.60


def catmull(p, t):
    n = len(p) - 1
    t = min(max(t, 0.0), 1.0) * n
    i = min(int(t), n - 1); u = t - i
    p0, p1, p2, p3 = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, n)]
    return tuple(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


# largo de la ruta para la velocidad constante
muestras_t = [i / 400 for i in range(401)]
pts = [catmull(RUTA, t) for t in muestras_t]
acum = [0.0]
for a, b in zip(pts, pts[1:]):
    acum.append(acum[-1] + math.dist(a, b))
L = acum[-1]
N = int(L / VEL * FPS)


def t_de_s(s):
    for i in range(1, len(acum)):
        if acum[i] >= s:
            f = (s - acum[i - 1]) / max(1e-9, acum[i] - acum[i - 1])
            return muestras_t[i - 1] + f * (muestras_t[i] - muestras_t[i - 1])
    return 1.0


bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'muestra', 'realismo.blend'))
sc = bpy.context.scene
cy = sc.cycles
sc.render.engine = 'CYCLES'
cy.device = 'CPU'
if '--gpu' in argv:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = tipo; prefs.get_devices()
            if any(d.type == tipo for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == tipo
                cy.device = 'GPU'; print('GPU:', tipo, flush=True); break
        except Exception:
            pass
cy.samples = MUESTRAS; cy.use_denoising = True; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 3; cy.transmission_bounces = 6
cy.transparent_max_bounces = 48; cy.caustics_reflective = False; cy.caustics_refractive = False
cy.seed = 0; cy.use_animated_seed = False        # ruido quieto entre cuadros (el denoiser lo limpia)
sc.render.resolution_x = ANCHO; sc.render.resolution_y = int(ANCHO * 9 / 16); sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
for o in bpy.data.objects:
    if o.name.startswith('satelite'):
        o.hide_render = True
# el portón grande se abre para el recorrido: se corre detrás de la cerca de la derecha
_ox, _oy, _a = sitio.marco(sitio.CASA)
_dx = Vector((math.cos(_a), math.sin(_a), 0)) * 6.8 + Vector((-math.sin(_a), math.cos(_a), 0)) * 0.3
for o in bpy.data.objects:
    if o.name.startswith('ca_porton'):
        c = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
        lx, ly = sitio.m_a_local(sitio.CASA, c.x, c.y)
        if 2.4 < lx < 9.6:
            o.matrix_world.translation += _dx
EXP_EXT = sc.view_settings.exposure
EXP_INT = -0.8

cam = bpy.data.cameras.new('cam_video'); cam.lens = 24; cam.sensor_width = 36; cam.clip_start = 0.05; cam.clip_end = 6000
co = bpy.data.objects.new('cam_video', cam); sc.collection.objects.link(co); sc.camera = co
print(f'ruta {L:.1f} m · {N} cuadros a {FPS} fps · {N / FPS:.1f} s', flush=True)
# cámara y exposición con fotogramas clave, y render de animación con datos persistentes: Cycles no vuelve a
# preparar la escena en cada cuadro (mucho más rápido que un render suelto por cuadro)
for f in range(N):
    t = t_de_s(f / max(1, N - 1) * L)
    x, y = catmull(RUTA, t)
    mx, my, mz = catmull(MIRA, t)
    paso = 0.012 * math.sin(2 * math.pi * f / FPS * 1.8)         # vaivén leve del caminar
    X, Y = sitio.local_a_m(sitio.CASA, x, y); TX, TY = sitio.local_a_m(sitio.CASA, mx, my)
    co.location = (X, Y, OJOS + paso)
    co.rotation_euler = (Vector((TX, TY, mz)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    co.keyframe_insert('location', frame=f + 1); co.keyframe_insert('rotation_euler', frame=f + 1)
    k = min(1.0, max(0.0, (y - (PUERTA - 1.4)) / 1.9))            # mezcla de exposición alrededor de la puerta
    sc.view_settings.exposure = EXP_EXT + (EXP_INT - EXP_EXT) * k
    sc.view_settings.keyframe_insert('exposure', frame=f + 1)
sc.frame_start = 1; sc.frame_end = N
sc.render.fps = FPS
sc.render.use_persistent_data = True
sc.render.use_overwrite = False                  # reanudar: no repite cuadros que ya existen
sc.render.use_placeholder = True
sc.render.filepath = os.path.join(OUT, 'f_')
bpy.ops.render.render(animation=True)


def ffmpeg_bin():
    f = shutil.which('ffmpeg')
    if f:
        return f
    for pat in (os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe'), r'C:\ffmpeg\bin\ffmpeg.exe'):
        for c in glob.glob(pat):
            if os.path.exists(c):
                return c
    return None


ff = ffmpeg_bin()
if ff:
    mp4 = os.path.join(OUT, 'recorrido_muestra.mp4')
    subprocess.run([ff, '-y', '-framerate', str(FPS), '-start_number', '1', '-i', os.path.join(OUT, 'f_%04d.png'), '-c:v', 'libx264',
                    '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    print('video', mp4, flush=True)
else:
    print('sin ffmpeg: quedan los cuadros PNG (instalar con: winget install Gyan.FFmpeg)', flush=True)
