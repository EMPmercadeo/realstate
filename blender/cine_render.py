"""Renderiza el sobrevuelo cinematográfico con Cycles (GPU) siguiendo la misma ruta de cámara
que la portada web (web/src/data/cine.ts). Produce fotogramas en build/cine/ y, si hay ffmpeg,
el video web/public/clips/sobrevuelo.mp4 que la portada reproduce controlado por el scroll.

Uso (desde la carpeta realstate, con Blender instalado):
  blender -b -P blender/cine_render.py -- --preview                 # 360p, 16 muestras, 60 cuadros
  blender -b -P blender/cine_render.py -- --solo 0,12,24 --w 1280   # solo esos cuadros (de --frames)
  blender -b -P blender/cine_render.py -- --w 1920 --samples 128    # 1080p final, 720 cuadros
  blender -b -P blender/cine_render.py -- --start 100 --end 200     # rango (para reanudar)
  blender -b -P blender/cine_render.py -- --video                   # solo arma el video con los PNG
Opciones de look: --hdri <nombre en assets/hdri>  --exposure -0.4  --sun-elev 14  --sun-az 246  --crf 20
Si existen assets/pbr/<Set>/ (ambientCG) se usan esas texturas; si no, las generadas.
"""
import os, sys, math, re, glob, argparse, subprocess, shutil, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument('--preview', action='store_true')
ap.add_argument('--w', type=int, default=1280)
ap.add_argument('--samples', type=int, default=96)
ap.add_argument('--frames', type=int, default=720)
ap.add_argument('--fps', type=int, default=24)
ap.add_argument('--start', type=int, default=0)
ap.add_argument('--end', type=int, default=-1)
ap.add_argument('--solo', type=str, default='', help='cuadros concretos, p.ej. 0,12,24')
ap.add_argument('--out', type=str, default='', help='carpeta de salida (por defecto build/cine)')
ap.add_argument('--cpu', action='store_true')
ap.add_argument('--hdri', type=str, default='', help='archivo .hdr en assets/hdri (sin extensión) o "none"')
ap.add_argument('--sun-elev', type=float, default=14.0)
ap.add_argument('--sun-az', type=float, default=66.0, help='sun_rotation del cielo Nishita (66 = sol al este-sureste, mañana)')
ap.add_argument('--exposure', type=float, default=0.55)
ap.add_argument('--crf', type=int, default=26)
ap.add_argument('--gop', type=int, default=16, help='cuadros entre keyframes (menor = scrub más rápido, archivo más grande)')
ap.add_argument('--video', action='store_true', help='no renderiza: solo arma el video con los cuadros existentes')
ap.add_argument('--solo-escena', action='store_true', help='solo prepara la escena y la guarda (build/cine.blend)')
args = ap.parse_args(argv)
if args.preview:
    args.w, args.samples, args.frames = 640, 16, 60

OUT = os.path.abspath(args.out) if args.out else os.path.join(ROOT, 'build', 'cine'); os.makedirs(OUT, exist_ok=True)
PBR = os.path.join(ROOT, 'assets', 'pbr')
HDRI_DIR = os.path.join(ROOT, 'assets', 'hdri')


def ffmpeg_bin():
    f = shutil.which('ffmpeg')
    if f: return f
    for pat in (os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe'), r'C:\ffmpeg\bin\ffmpeg.exe'):
        for c in glob.glob(pat):
            if os.path.exists(c): return c
    return None


def armar_video(fps):
    ff = ffmpeg_bin()
    if not ff:
        print('sin ffmpeg: no se arma el video'); return
    clips = os.path.join(ROOT, 'web', 'public', 'clips'); os.makedirs(clips, exist_ok=True)
    salida = os.path.join(clips, 'sobrevuelo.mp4')
    # escritorio 16:9 (1080p máx.) — GOP corto para que el scrub por scroll sea instantáneo
    subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(OUT, 'f%04d.png'),
                    '-vf', 'scale=min(1920\\,iw):-2', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                    '-crf', str(args.crf), '-g', str(args.gop), '-keyint_min', str(args.gop), '-sc_threshold', '0', '-movflags', '+faststart', '-an', salida], check=False)
    # móvil 9:16: recorte central y 720 px de ancho
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', salida, '-vf', 'crop=ih*9/16:ih,scale=720:-2', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow',
                    '-pix_fmt', 'yuv420p', '-crf', str(args.crf + 1), '-g', str(args.gop), '-keyint_min', str(args.gop), '-sc_threshold', '0', '-movflags', '+faststart', '-an',
                    os.path.join(clips, 'sobrevuelo-m.mp4')], check=False)
    # póster (primer cuadro) para que la portada muestre algo antes de que cargue el video
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', os.path.join(OUT, 'f0000.png'), '-vf', 'scale=1600:-2', '-q:v', '4', os.path.join(clips, 'poster.jpg')], check=False)
    for n in ('sobrevuelo.mp4', 'sobrevuelo-m.mp4', 'poster.jpg'):
        p = os.path.join(clips, n)
        if os.path.exists(p): print(f'{n}: {os.path.getsize(p) / 1e6:.1f} MB')


if args.video:
    armar_video(args.fps); sys.exit(0)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'build', 'escena.blend'))
scene = bpy.context.scene

# ---------------- ruta de cámara: leída de web/src/data/cine.ts ----------------
src = open(os.path.join(ROOT, 'web', 'src', 'data', 'cine.ts'), encoding='utf-8').read()
bloque = src.split('export const RUTA')[1].split('];')[0]
puntos = [(list(map(float, p.split(','))), list(map(float, t.split(','))))
          for p, t in re.findall(r'pos:\s*\[([^\]]+)\],\s*target:\s*\[([^\]]+)\]', bloque)]
# three.js (x, y, z) -> Blender (x, -z, y)
POS = [Vector((p[0], -p[2], p[1])) for p, _ in puntos]
TGT = [Vector((t[0], -t[2], t[1])) for _, t in puntos]


def catmull(points, t):
    """Igual que THREE.CatmullRomCurve3 (abierta, centripetal, getPoint)."""
    n = len(points); p = (n - 1) * t; i = int(math.floor(p)); w = p - i
    if w == 0 and i == n - 1: i = n - 2; w = 1
    p0 = points[i - 1] if i > 0 else points[0] - (points[1] - points[0])
    p1, p2 = points[i], points[i + 1]
    p3 = points[i + 2] if i + 2 < n else points[n - 1] - (points[n - 2] - points[n - 1])
    dt0 = math.pow((p0 - p1).length_squared, 0.25)
    dt1 = math.pow((p1 - p2).length_squared, 0.25)
    dt2 = math.pow((p2 - p3).length_squared, 0.25)
    if dt1 < 1e-4: dt1 = 1.0
    if dt0 < 1e-4: dt0 = dt1
    if dt2 < 1e-4: dt2 = dt1
    out = []
    for k in range(3):
        x0, x1, x2, x3 = p0[k], p1[k], p2[k], p3[k]
        t1 = (x1 - x0) / dt0 - (x2 - x0) / (dt0 + dt1) + (x2 - x1) / dt1
        t2 = (x2 - x1) / dt1 - (x3 - x1) / (dt1 + dt2) + (x3 - x2) / dt2
        t1 *= dt1; t2 *= dt1
        c0, c1, c2, c3 = x1, t1, -3 * x1 + 3 * x2 - 2 * t1 - t2, 2 * x1 - 2 * x2 + t1 + t2
        out.append(c0 + c1 * w + c2 * w * w + c3 * w * w * w)
    return Vector(out)


# ---------------- entorno: colinas, Volcán Barú, bosque lejano (como mundo.ts) ----------------
def hash2(x, y):
    s = math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - math.floor(s)
def vnoise(x, y):
    ix, iy = math.floor(x), math.floor(y); fx, fy = x - ix, y - iy
    u, v = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = hash2(ix, iy), hash2(ix + 1, iy), hash2(ix, iy + 1), hash2(ix + 1, iy + 1)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v
def fbm(x, y, o=4):
    s, a, f = 0, 0.5, 1
    for _ in range(o): s += a * vnoise(x * f, y * f); a *= 0.5; f *= 2
    return s
def smooth(x, a, b):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def altura(x, y):
    """x, y en coordenadas del sitio (Blender). Plano en el lote y alrededores."""
    z3 = -y
    dx = max(0, -22 - x, x - 62); dz = max(0, -112 - z3, z3 - 30)
    k = smooth(math.hypot(dx, dz), 10, 90)
    if k <= 0: return 0.0
    h = (fbm(x * 0.012 + 3, z3 * 0.012 + 9, 4) - 0.45) * 26
    r = math.hypot(x - 20, z3 + 40)
    h += smooth(r, 420, 1300) * 180 * (0.55 + 0.45 * fbm(x * 0.004, z3 * 0.004, 3))
    dv = math.hypot((x - 200) / 1.6, z3 + 2900)
    h += max(0, 1 - dv / 1500) ** 1.6 * 1250
    return h * k


# ---------------- materiales PBR reales (ambientCG) ----------------
def pbr_set(nombre):
    """Devuelve dict con rutas Color/NormalGL/Roughness/Displacement si existe assets/pbr/<nombre>."""
    d = os.path.join(PBR, nombre)
    if not os.path.isdir(d): return None
    out = {}
    for k in ('Color', 'NormalGL', 'Roughness', 'Displacement', 'Metalness', 'AmbientOcclusion'):
        m = glob.glob(os.path.join(d, f'*_{k}.jpg')) + glob.glob(os.path.join(d, f'*_{k}.png'))
        if m: out[k] = m[0]
    return out if 'Color' in out else None


_imgs = {}
def _img(path, noncolor=False):
    if path not in _imgs:
        im = bpy.data.images.load(path, check_existing=True)
        if noncolor: im.colorspace_settings.name = 'Non-Color'
        _imgs[path] = im
    return _imgs[path]


def _tex(nt, mapping, path, noncolor=False):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = _img(path, noncolor); t.projection = 'BOX'; t.projection_blend = 0.25
    t.interpolation = 'Linear'; nt.links.new(mapping.outputs['Vector'], t.inputs['Vector']); return t


def rehacer_pbr(nombre_mat, set_name, tile=2.0, tint=None, color=None, rough=None, metal=0.0, bump=0.35, mezcla=None, variacion=None):
    """Reconstruye el material <nombre_mat> con texturas reales proyectadas en caja por posición mundial.
    tint: multiplica el color de la textura. color: color plano en lugar de la textura de color (usa normal/rough del set).
    mezcla: (set2, tile2, escala_ruido) mezcla un segundo set por ruido (parches de tierra en el césped).
    variacion: (escala, fuerza) variación grande de tono/brillo por ruido."""
    m = bpy.data.materials.get(nombre_mat)
    S = pbr_set(set_name)
    if not m or not S:
        return False
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / tile, 1 / tile, 1 / tile)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    if color is None:
        c = _tex(nt, mp, S['Color']); col_out = c.outputs['Color']
    else:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (*color[:3], 1); col_out = rgb.outputs[0]
    if tint:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
        mix.inputs[7].default_value = (*tint[:3], 1); nt.links.new(col_out, mix.inputs[6]); col_out = mix.outputs[2]
    rough_out = None
    if rough is None and 'Roughness' in S:
        r = _tex(nt, mp, S['Roughness'], True); rough_out = r.outputs['Color']
    if mezcla:
        S2 = pbr_set(mezcla[0])
        if S2:
            mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (1 / mezcla[1],) * 3
            nt.links.new(geo.outputs['Position'], mp2.inputs['Vector'])
            c2 = _tex(nt, mp2, S2['Color'])
            nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = mezcla[2]; nz.inputs['Detail'].default_value = 3.0; nz.inputs['Roughness'].default_value = 0.55
            nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
            ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.63; ramp.color_ramp.elements[1].position = 0.72
            nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(ramp.outputs['Color'], mx.inputs['Factor'])
            nt.links.new(col_out, mx.inputs[6]); nt.links.new(c2.outputs['Color'], mx.inputs[7]); col_out = mx.outputs[2]
            if rough_out is not None and 'Roughness' in S2:
                r2 = _tex(nt, mp2, S2['Roughness'], True)
                mr = nt.nodes.new('ShaderNodeMix'); mr.data_type = 'RGBA'; nt.links.new(ramp.outputs['Color'], mr.inputs['Factor'])
                nt.links.new(rough_out, mr.inputs[6]); nt.links.new(r2.outputs['Color'], mr.inputs[7]); rough_out = mr.outputs[2]
    if variacion:
        esc, fz = variacion
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = esc; nz.inputs['Detail'].default_value = 4.0
        nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
        hs = nt.nodes.new('ShaderNodeHueSaturation')
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7
        mr.inputs['To Min'].default_value = 1 - fz; mr.inputs['To Max'].default_value = 1 + fz
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], hs.inputs['Value'])
        mh = nt.nodes.new('ShaderNodeMapRange'); mh.inputs['From Min'].default_value = 0.3; mh.inputs['From Max'].default_value = 0.7
        mh.inputs['To Min'].default_value = 0.5 - fz * 0.12; mh.inputs['To Max'].default_value = 0.5 + fz * 0.12
        nt.links.new(nz.outputs['Fac'], mh.inputs['Value']); nt.links.new(mh.outputs['Result'], hs.inputs['Hue'])
        hs.inputs['Saturation'].default_value = 1.1
        nt.links.new(col_out, hs.inputs['Color']); col_out = hs.outputs['Color']
    nt.links.new(col_out, bsdf.inputs['Base Color'])
    if rough_out is not None: nt.links.new(rough_out, bsdf.inputs['Roughness'])
    else: bsdf.inputs['Roughness'].default_value = 0.6 if rough is None else rough
    bsdf.inputs['Metallic'].default_value = metal
    if bump and 'Displacement' in S:
        h = _tex(nt, mp, S['Displacement'], True)
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.03
        nt.links.new(h.outputs['Color'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    elif 'NormalGL' in S:
        n = _tex(nt, mp, S['NormalGL'], True); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.8
        nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return True


def mejorar_hojas():
    """Follaje: translucidez (luz a través de las hojas) y variación de tono por árbol."""
    for nombre in ('follaje', 'fronda', 'arbusto'):
        m = bpy.data.materials.get(nombre)
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not (bsdf and tex and out): continue
        # variación por objeto
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        hs = nt.nodes.new('ShaderNodeHueSaturation')
        mh = nt.nodes.new('ShaderNodeMapRange'); mh.inputs['To Min'].default_value = 0.47; mh.inputs['To Max'].default_value = 0.535
        mv = nt.nodes.new('ShaderNodeMapRange'); mv.inputs['To Min'].default_value = 0.75; mv.inputs['To Max'].default_value = 1.2
        ms = nt.nodes.new('ShaderNodeMapRange'); ms.inputs['To Min'].default_value = 0.85; ms.inputs['To Max'].default_value = 1.15
        for n in (mh, mv, ms): nt.links.new(oi.outputs['Random'], n.inputs['Value'])
        nt.links.new(mh.outputs['Result'], hs.inputs['Hue']); nt.links.new(mv.outputs['Result'], hs.inputs['Value']); nt.links.new(ms.outputs['Result'], hs.inputs['Saturation'])
        nt.links.new(tex.outputs['Color'], hs.inputs['Color'])
        nt.links.new(hs.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.55
        try: bsdf.inputs['Specular IOR Level'].default_value = 0.35
        except Exception: pass
        # translucidez
        tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
        mult = nt.nodes.new('ShaderNodeMix'); mult.data_type = 'RGBA'; mult.blend_type = 'MULTIPLY'; mult.inputs['Factor'].default_value = 1.0
        mult.inputs[7].default_value = (0.75, 0.9, 0.45, 1)
        nt.links.new(hs.outputs['Color'], mult.inputs[6]); nt.links.new(mult.outputs[2], tr.inputs['Color'])
        mixs = nt.nodes.new('ShaderNodeMixShader'); mixs.inputs['Fac'].default_value = 0.32
        nt.links.new(bsdf.outputs['BSDF'], mixs.inputs[1]); nt.links.new(tr.outputs['BSDF'], mixs.inputs[2])
        # alpha: transparente donde la textura es transparente
        tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mixa = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(tex.outputs['Alpha'], mixa.inputs['Fac']); nt.links.new(tp.outputs['BSDF'], mixa.inputs[1]); nt.links.new(mixs.outputs['Shader'], mixa.inputs[2])
        for l in list(out.inputs['Surface'].links): nt.links.remove(l)
        nt.links.new(mixa.outputs['Shader'], out.inputs['Surface'])
        try: m.surface_render_method = 'DITHERED'
        except Exception: pass


def materiales_render():
    ok = []
    # suelo: césped real con parches de tierra y variación grande de tono
    for nm in ('cesped', 'cesped_ext'):
        if rehacer_pbr(nm, 'Grass004', 2.4, tint=(0.66, 1.0, 0.52), mezcla=('Ground037', 3.0, 0.035), variacion=(0.012, 0.15), bump=0.25): ok.append(nm)
    if rehacer_pbr('asfalto', 'Asphalt012', 4.0, tint=(0.75, 0.75, 0.76), variacion=(0.05, 0.12)): ok.append('asfalto')
    if rehacer_pbr('concreto', 'Concrete034', 2.0): ok.append('concreto')
    if rehacer_pbr('gris_claro', 'Concrete034', 2.2, tint=(1.18, 1.2, 1.24), bump=0.2): ok.append('gris_claro')
    if rehacer_pbr('acera', 'Concrete034', 1.6, tint=(1.1, 1.1, 1.06), bump=0.2): ok.append('acera')
    pl = 'PaintedPlaster016' if pbr_set('PaintedPlaster016') else 'PaintedPlaster017'
    if rehacer_pbr('amarillo', 'Plaster001', 2.0, tint=(1.0, 0.74, 0.34), bump=0.15): ok.append('amarillo')
    if rehacer_pbr('blanco', 'Plaster001', 2.0, tint=(0.95, 0.95, 0.93), bump=0.2): ok.append('blanco')
    if rehacer_pbr('grava', 'Gravel022', 1.6): ok.append('grava')
    # 'ceramica' conserva la textura generada (Tiles074 es un damero)
    cs = next((s for s in ('CorrugatedSteel005', 'CorrugatedSteel004', 'CorrugatedSteel002') if pbr_set(s)), None)
    if cs:
        if rehacer_pbr('lamina', cs, 1.0, color=(0.74, 0.75, 0.77), rough=0.42, metal=0.55, bump=0.5): ok.append('lamina')
        if rehacer_pbr('lamina_roja', cs, 1.0, color=(0.42, 0.055, 0.035), rough=0.48, metal=0.35, bump=0.5): ok.append('lamina_roja')
    mejorar_hojas()
    # agua de la piscina: un poco más clara y con ondas
    ag = bpy.data.materials.get('agua')
    if ag and ag.use_nodes:
        b = next((n for n in ag.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b:
            b.inputs['Base Color'].default_value = (0.45, 0.78, 0.88, 1); b.inputs['Roughness'].default_value = 0.03
            nz = ag.node_tree.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 6
            bp = ag.node_tree.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08; bp.inputs['Distance'].default_value = 0.01
            ag.node_tree.links.new(nz.outputs['Fac'], bp.inputs['Height']); ag.node_tree.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    print('PBR aplicado a:', ok)


def preparar_entorno():
    ent = bpy.data.objects.get('entorno')
    if ent: ent.hide_render = True
    # terreno
    import bmesh
    TS, SEG = 6400, 200
    bm = bmesh.new()
    verts = []
    for j in range(SEG + 1):
        for i in range(SEG + 1):
            x = -TS / 2 + TS * i / SEG + 20; y = -TS / 2 + TS * j / SEG + 40
            verts.append(bm.verts.new((x, y, altura(x, y) - 0.05)))
    bm.verts.ensure_lookup_table()
    for j in range(SEG):
        for i in range(SEG):
            a = j * (SEG + 1) + i
            bm.faces.new((verts[a], verts[a + 1], verts[a + SEG + 2], verts[a + SEG + 1]))
    me = bpy.data.meshes.new('terreno'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('terreno', me); scene.collection.objects.link(ob)
    mat = bpy.data.materials.get('cesped_ext') or bpy.data.materials.get('cesped')
    if mat: ob.data.materials.append(mat)
    me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uv[li].uv = (v.x / 6.0, v.y / 6.0)
    for p in me.polygons: p.use_smooth = True
    # bosque lejano: copias de los árboles existentes (instancias ligeras)
    base = [o for o in bpy.data.objects if o.name.startswith('arbol_') and not o.name.startswith('vecino')]
    palmas = [o for o in bpy.data.objects if o.name.startswith('palma_')]
    random.seed(5)
    col = bpy.data.collections.new('BosqueLejano'); scene.collection.children.link(col)
    n = 1500
    for k in range(n):
        a = random.random() * 6.2832; r = 75 + random.random() ** 1.4 * 900
        x = 20 + math.cos(a) * r; y = 40 + math.sin(a) * r
        if -16 < x < 62 and -42 < y < 122: continue
        if abs(x - 36.5) < 8: continue   # la calle sigue
        if fbm(x * 0.01, y * 0.01, 2) < 0.4 and r > 220: continue
        src = random.choice(palmas if random.random() < 0.22 else base)
        if not src: continue
        inst = bpy.data.objects.new(f'bl_{k}', src.data); inst.location = (x, y, altura(x, y) - 0.1)
        s = 0.7 + random.random() * 0.9; inst.scale = (s, s, s); inst.rotation_euler = (0, 0, random.random() * 6.28)
        col.objects.link(inst)
    # casas vecinas lejanas (cajas con techo)
    for k in range(60):
        x = -220 + random.random() * 480; y = -320 + random.random() * 460
        if -16 < x < 62 and -42 < y < 122: continue
        if abs(x - 36.5) < 9: continue
        w, d, h = 9 + random.random() * 6, 8 + random.random() * 5, 3.2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + w / 2, y + d / 2, altura(x, y) + h / 2))
        c = bpy.context.active_object; c.scale = (w, d, h); c.name = f'vec_{k}'
        c.data.materials.append(bpy.data.materials.get('blanco') or bpy.data.materials[0])
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(w, d) * 0.78, depth=2.4, location=(x + w / 2, y + d / 2, altura(x, y) + h + 1.2), rotation=(0, 0, math.radians(45)))
        t = bpy.context.active_object; t.scale = (w / max(w, d), d / max(w, d), 1); t.name = f'vec_t_{k}'
        t.data.materials.append(bpy.data.materials.get('lamina_roja' if k % 2 else 'lamina') or bpy.data.materials[0])
    # calle continua
    calle = bpy.data.objects.get('calle')
    if calle: calle.hide_render = True
    bpy.ops.mesh.primitive_plane_add(size=1, location=(36.5, 50, 0.02)); c = bpy.context.active_object; c.scale = (9, 560, 1); c.name = 'calle_larga'
    c.data.materials.append(bpy.data.materials.get('asfalto') or bpy.data.materials[0])
    # línea central discontinua
    lm = bpy.data.materials.new('linea'); lm.use_nodes = True
    lm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.85, 0.6, 1)
    for i in range(-40, 50):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(36.5, i * 6, 0.03)); l = bpy.context.active_object; l.scale = (0.12, 3, 1); l.name = f'linea_{i}'
        l.data.materials.append(lm)
    # los vecinos construidos se quedan (dan vida al barrio); su arboleda también


# ---------------- mundo / luz ----------------
def hdri_elegido():
    if args.hdri.lower() == 'none': return None
    if args.hdri:
        p = os.path.join(HDRI_DIR, args.hdri if args.hdri.endswith('.hdr') else args.hdri + '.hdr')
        return p if os.path.exists(p) else None
    return None   # por defecto cielo procedural (sol controlable); --hdri <nombre> para usar uno


def preparar_mundo():
    w = scene.world; nt = w.node_tree
    bg = nt.nodes.get('Background')
    hd = hdri_elegido()
    if hd:
        import numpy as np
        for n in [n for n in nt.nodes if n.type == 'TEX_SKY']: nt.nodes.remove(n)
        im = bpy.data.images.load(hd)
        W, H = im.size; px = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
        lum = px[..., :3].sum(-1); yy, xx = np.unravel_index(lum.argmax(), lum.shape)
        az_img = xx / W * 360.0          # longitud del sol en la imagen (0 = borde izquierdo)
        # en Blender el centro de la imagen equirectangular (u=0.5) mira a -Y; u crece hacia -X.
        # queremos el sol en el acimut deseado (medido como sun_rotation Nishita): dir = (cos(az+90), sin(az+90))
        az_deseado = math.radians(args.sun_az + 90)
        lon_deseada = math.degrees(math.atan2(math.sin(az_deseado), math.cos(az_deseado)))   # ángulo mundo
        # longitud mundo de un píxel u: ang = 180 + (u*360) ... se calibra por rotación Z simple:
        rotz = math.radians((az_img - 90) - lon_deseada)
        env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = im
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Rotation'].default_value = (0, 0, rotz)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
        nt.links.new(env.outputs['Color'], bg.inputs['Color'])
        bg.inputs['Strength'].default_value = 1.0
        # sol propio a la elevación deseada (el del HDRI suele estar casi en el horizonte)
        sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(0.9); sun.color = (1.0, 0.82, 0.62)
        so = bpy.data.objects.new('sol', sun); scene.collection.objects.link(so)
        el = math.radians(args.sun_elev); azr = math.radians(args.sun_az + 90)
        d = Vector((math.cos(el) * math.cos(azr), math.cos(el) * math.sin(azr), math.sin(el)))
        so.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        print(f'HDRI {os.path.basename(hd)} sol imagen az={az_img:.0f}° rotZ={math.degrees(rotz):.0f}°')
    else:
        sky = next((n for n in nt.nodes if n.type == 'TEX_SKY'), None)
        if not sky:
            sky = nt.nodes.new('ShaderNodeTexSky'); nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
        sky.sky_type = 'MULTIPLE_SCATTERING'
        sky.sun_disc = True; sky.sun_size = math.radians(1.1)
        sky.sun_elevation = math.radians(args.sun_elev); sky.sun_rotation = math.radians(args.sun_az)
        sky.sun_intensity = 1.5; sky.altitude = 60
        sky.air_density = 1.0; sky.aerosol_density = 1.2; sky.ozone_density = 1.8; sky.ground_albedo = 0.25
        bg.inputs['Strength'].default_value = 0.065
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = args.exposure
    # niebla/bruma de distancia (pase Mist → compositor)
    w.mist_settings.use_mist = True; w.mist_settings.start = 120; w.mist_settings.depth = 1800; w.mist_settings.falloff = 'LINEAR'
    scene.view_layers[0].use_pass_mist = True


def preparar_compositor():
    try:
        nt = bpy.data.node_groups.new('cine_comp', 'CompositorNodeTree')
        try: nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        except Exception: pass
        rl = nt.nodes.new('CompositorNodeRLayers'); rl.scene = scene
        outp = nt.nodes.new('NodeGroupOutput')
        # bruma: mezcla con color cálido según el pase Mist
        haze = nt.nodes.new('CompositorNodeRGB'); haze.outputs[0].default_value = (0.86, 0.80, 0.68, 1)
        ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'LINEAR'
        cr.elements[0].position = 0.0; cr.elements[0].color = (0, 0, 0, 1)
        cr.elements[1].position = 0.9; cr.elements[1].color = (0.6, 0.6, 0.6, 1)
        e2 = cr.elements.new(0.985); e2.color = (0.55, 0.55, 0.55, 1)
        e3 = cr.elements.new(1.0); e3.color = (0.22, 0.22, 0.22, 1)
        nt.links.new(rl.outputs['Mist'], ramp.inputs['Fac'])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        nt.links.new(ramp.outputs['Color'], mix.inputs['Factor']); nt.links.new(rl.outputs['Image'], mix.inputs[6]); nt.links.new(haze.outputs[0], mix.inputs[7])
        # resplandor suave en las altas luces
        gl = nt.nodes.new('CompositorNodeGlare')
        try: gl.inputs['Type'].default_value = 'BLOOM'
        except Exception:
            try: gl.glare_type = 'BLOOM'
            except Exception: pass
        for k, v in (('Threshold', 1.6), ('Strength', 0.12), ('Size', 0.6), ('Smoothness', 0.2), ('Quality', 'MEDIUM')):
            try: gl.inputs[k].default_value = v
            except Exception: pass
        nt.links.new(mix.outputs[2], gl.inputs['Image'])
        nt.links.new(gl.outputs['Image'], outp.inputs[0])
        scene.compositing_node_group = nt
        scene.render.use_compositing = True
        print('compositor: bruma + bloom')
    except Exception as e:
        print('compositor no disponible:', e)
        scene.render.use_compositing = False


def preparar_camara():
    cam = bpy.data.cameras.new('cine'); cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(45); cam.clip_end = 9000; cam.clip_start = 0.2
    cam.dof.use_dof = False
    co = bpy.data.objects.new('cine', cam); scene.collection.objects.link(co); scene.camera = co
    return co


def colocar(co, u):
    p = catmull(POS, u); t = catmull(TGT, u)
    co.location = p
    co.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()


def render_settings():
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons.get('cycles')
    if not args.cpu and prefs:
        cp = prefs.preferences
        for tipo in ('OPTIX', 'CUDA', 'HIP', 'METAL'):
            try:
                cp.compute_device_type = tipo
                cp.get_devices()
                ok = False
                for d in cp.devices:
                    d.use = d.type != 'CPU'
                    ok = ok or d.use
                if ok:
                    scene.cycles.device = 'GPU'; print('GPU:', tipo, [d.name for d in cp.devices if d.use]); break
            except Exception:
                continue
        else:
            scene.cycles.device = 'CPU'; print('sin GPU compatible, CPU')
    else:
        scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    try: scene.cycles.denoiser = 'OPTIX' if scene.cycles.device == 'GPU' else 'OPENIMAGEDENOISE'
    except Exception: pass
    try: scene.cycles.denoising_use_gpu = True
    except Exception: pass
    scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.02
    scene.cycles.max_bounces = 6; scene.cycles.diffuse_bounces = 3; scene.cycles.glossy_bounces = 3; scene.cycles.transparent_max_bounces = 12
    scene.cycles.sample_clamp_indirect = 8.0
    scene.cycles.blur_glossy = 1.0
    scene.render.resolution_x = args.w; scene.render.resolution_y = int(args.w * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_depth = '8'
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    scene.render.use_persistent_data = True


preparar_entorno()
materiales_render()
preparar_mundo()
preparar_compositor()
co = preparar_camara()
render_settings()
if args.solo_escena:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'build', 'cine.blend')); print('build/cine.blend'); sys.exit(0)

N = args.frames
end = args.end if args.end >= 0 else N - 1
cuadros = [int(x) for x in args.solo.split(',') if x.strip()] if args.solo else list(range(args.start, end + 1))
import time
t0 = time.time(); hechos = 0
for f in cuadros:
    u = f / (N - 1)
    colocar(co, u)
    scene.render.filepath = os.path.join(OUT, f'f{f:04d}.png')
    if not args.solo and os.path.exists(scene.render.filepath) and os.path.getsize(scene.render.filepath) > 1000:
        continue   # reanudar: no repetir cuadros ya hechos
    bpy.ops.render.render(write_still=True)
    hechos += 1
    print(f'cuadro {f}/{N - 1} u={u:.3f}  ({(time.time() - t0) / hechos:.1f} s/cuadro)', flush=True)

# video (si están todos los cuadros)
if not args.solo and args.start == 0 and end == N - 1:
    faltan = [f for f in range(N) if not os.path.exists(os.path.join(OUT, f'f{f:04d}.png'))]
    if faltan: print('faltan cuadros:', faltan[:10], '...')
    else: armar_video(args.fps)
