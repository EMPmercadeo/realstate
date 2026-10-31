"""
Etapa 4a · materiales realistas para los interiores (Cycles).

Procedurales salvo pisos y pintura (texturas de assets/). Pisos, muros y cielos usan las UV en metros
de lib.box_uv; los muebles usan coordenadas de objeto, así no necesitan UV.
Referencias de color: fotos reales (sala de conferencias, baños rojos, galería, biblioteca) y las
imágenes "así quedará" de Antigravity.
"""
import os
import bpy
from lib import ROOT, img

PBR = os.path.join(ROOT, 'assets', 'pbr')
TEX = os.path.join(ROOT, 'assets', 'textures', 'gen')
_cache = {}


class N:
    """Ayudante para armar árboles de nodos con pocas líneas."""
    def __init__(self, nombre):
        self.m = bpy.data.materials.new(nombre)
        self.m.use_nodes = True
        self.nt = self.m.node_tree
        self.b = self.nt.nodes['Principled BSDF']
        self.out = self.nt.nodes['Material Output']

    def n(self, tipo, **props):
        nd = self.nt.nodes.new(tipo)
        for k, v in props.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
            else:
                nd.inputs[k].default_value = v
        return nd

    def l(self, a, b):
        self.nt.links.new(a, b)

    def coord(self, tipo='Object', escala=(1, 1, 1), rot=(0, 0, 0)):
        tc = self.n('ShaderNodeTexCoord')
        mp = self.n('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = escala
        mp.inputs['Rotation'].default_value = rot
        self.l(tc.outputs[tipo], mp.inputs['Vector'])
        return mp.outputs['Vector']

    def rampa(self, fac, c0, c1, p0=0.0, p1=1.0):
        r = self.n('ShaderNodeValToRGB')
        e = r.color_ramp.elements
        e[0].position, e[0].color = p0, tuple(c0) + (1,) if len(c0) == 3 else c0
        e[1].position, e[1].color = p1, tuple(c1) + (1,) if len(c1) == 3 else c1
        self.l(fac, r.inputs['Fac'])
        return r.outputs['Color']

    def mezcla(self, fac, a, b):
        mx = self.n('ShaderNodeMix', data_type='RGBA')
        mx.inputs['Factor'].default_value = 0.5
        if isinstance(fac, float):
            mx.inputs['Factor'].default_value = fac
        else:
            self.l(fac, mx.inputs['Factor'])
        for i, v in ((6, a), (7, b)):
            if isinstance(v, tuple):
                mx.inputs[i].default_value = v + (1,) if len(v) == 3 else v
            else:
                self.l(v, mx.inputs[i])
        return mx.outputs[2]

    def relieve(self, alto, fuerza=0.2, dist=0.01, normal=None):
        bp = self.n('ShaderNodeBump')
        bp.inputs['Strength'].default_value = fuerza
        bp.inputs['Distance'].default_value = dist
        self.l(alto, bp.inputs['Height'])
        if normal is not None:
            self.l(normal, bp.inputs['Normal'])
        self.l(bp.outputs['Normal'], self.b.inputs['Normal'])
        return bp.outputs['Normal']

    def set(self, **kw):
        nombres = {'color': 'Base Color', 'rough': 'Roughness', 'metal': 'Metallic', 'coat': 'Coat Weight',
                   'sheen': 'Sheen Weight', 'ior': 'IOR', 'trans': 'Transmission Weight', 'alpha': 'Alpha',
                   'sss': 'Subsurface Weight', 'emis_col': 'Emission Color', 'emis': 'Emission Strength',
                   'spec': 'Specular IOR Level'}
        for k, v in kw.items():
            inp = self.b.inputs[nombres[k]]
            if isinstance(v, (tuple, list)):
                inp.default_value = tuple(v) + ((1,) if len(v) == 3 else ())
            elif isinstance(v, (int, float)):
                inp.default_value = v
            else:
                self.l(v, inp)
        return self


def liso(nombre, color, rough=0.5, metal=0.0, **kw):
    if nombre in _cache:
        return _cache[nombre]
    n = N(nombre).set(color=color, rough=rough, metal=metal, **kw)
    _cache[nombre] = n.m
    return n.m


# ------------------------------------------------------------------ superficies de obra (UV en metros)
def baldosa(nombre, c1, c2, junta, tam=(0.45, 0.45), rough=0.12, junta_ancho=0.003, desfase=0.0, var=0.04):
    n = N(nombre)
    v = n.coord('UV')
    br = n.n('ShaderNodeTexBrick', offset=desfase, offset_frequency=2, squash=1.0, squash_frequency=2)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = tam[0]
    br.inputs['Row Height'].default_value = tam[1]
    br.inputs['Mortar Size'].default_value = junta_ancho
    br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = c1 + (1,)
    br.inputs['Color2'].default_value = c2 + (1,)
    br.inputs['Mortar'].default_value = junta + (1,)
    n.l(v, br.inputs['Vector'])
    # nube suave dentro de cada pieza (vetas leves)
    nz = n.n('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 6.0
    n.l(v, nz.inputs['Vector'])
    col = n.mezcla(var, br.outputs['Color'], nz.outputs['Color'])
    mr = n.n('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = rough
    mr.inputs['To Max'].default_value = 0.7
    n.l(br.outputs['Fac'], mr.inputs['Value'])
    n.set(color=col, rough=mr.outputs['Result'])
    inv = n.n('ShaderNodeMath', operation='SUBTRACT')
    inv.inputs[0].default_value = 1.0
    n.l(br.outputs['Fac'], inv.inputs[1])
    n.relieve(inv.outputs[0], 0.35, 0.002)
    return n.m


def pintura(nombre, color, rough=0.85):
    """Pintura mate sobre repello (relieve de PaintedPlaster017)."""
    n = N(nombre)
    v = n.coord('UV', (0.5, 0.5, 0.5))
    p = os.path.join(PBR, 'PaintedPlaster017', 'PaintedPlaster017_2K-JPG_NormalGL.jpg')
    if os.path.exists(p):
        t = n.n('ShaderNodeTexImage'); t.image = img(p); t.image.colorspace_settings.name = 'Non-Color'
        n.l(v, t.inputs['Vector'])
        nm = n.n('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.25
        n.l(t.outputs['Color'], nm.inputs['Color']); n.l(nm.outputs['Normal'], n.b.inputs['Normal'])
    nz = n.n('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.5; nz.inputs['Detail'].default_value = 3
    n.l(v, nz.inputs['Vector'])
    oscuro = tuple(c * 0.93 for c in color)
    n.set(color=n.rampa(nz.outputs['Fac'], oscuro, color, 0.3, 0.7), rough=rough)
    return n.m


def reticula(nombre):
    """Cielo raso de losetas acústicas 60×60 con perfilería (fotos de la sala de conferencias)."""
    n = N(nombre)
    v = n.coord('UV')
    br = n.n('ShaderNodeTexBrick', offset=0.0)
    for k, val in (('Scale', 1.0), ('Brick Width', 0.61), ('Row Height', 0.61), ('Mortar Size', 0.012),
                   ('Mortar Smooth', 0.0), ('Bias', 0.0)):
        br.inputs[k].default_value = val
    br.inputs['Color1'].default_value = (0.86, 0.86, 0.84, 1)
    br.inputs['Color2'].default_value = (0.84, 0.84, 0.82, 1)
    br.inputs['Mortar'].default_value = (0.93, 0.93, 0.92, 1)
    n.l(v, br.inputs['Vector'])
    fis = n.n('ShaderNodeTexNoise'); fis.inputs['Scale'].default_value = 90; fis.inputs['Detail'].default_value = 10
    fis.inputs['Roughness'].default_value = 0.7
    n.l(v, fis.inputs['Vector'])
    pore = n.n('ShaderNodeMath', operation='MULTIPLY'); pore.inputs[1].default_value = 0.6
    n.l(fis.outputs['Fac'], pore.inputs[0])
    sum_ = n.n('ShaderNodeMath', operation='ADD'); n.l(pore.outputs[0], sum_.inputs[0]); n.l(br.outputs['Fac'], sum_.inputs[1])
    n.set(color=br.outputs['Color'], rough=0.95)
    n.relieve(sum_.outputs[0], 0.25, 0.004)
    return n.m


# ------------------------------------------------------------------ muebles (coordenadas de objeto)
def madera(nombre, c_claro, c_oscuro, escala=1.0, rough=0.42, eje='x'):
    """Veta fina y recta (ruido estirado a lo largo de la veta) con variación suave de tono."""
    n = N(nombre)
    v = n.coord('Object', (3.0 * escala, 3.0 * escala, 60.0 * escala))          # veta vertical por defecto
    ns = n.n('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 2.5; ns.inputs['Detail'].default_value = 10
    ns.inputs['Distortion'].default_value = 0.4; ns.inputs['Roughness'].default_value = 0.65
    n.l(v, ns.inputs['Vector'])
    v2 = n.coord('Object', (60.0 * escala, 3.0 * escala, 3.0 * escala))         # y otra a lo largo de x
    ns2 = n.n('ShaderNodeTexNoise'); ns2.inputs['Scale'].default_value = 2.5; ns2.inputs['Detail'].default_value = 10
    ns2.inputs['Distortion'].default_value = 0.4
    n.l(v2, ns2.inputs['Vector'])
    f = n.mezcla(0.5, ns.outputs['Color'], ns2.outputs['Color'])
    bw = n.n('ShaderNodeRGBToBW'); n.l(f, bw.inputs['Color'])
    medio = tuple((a * 0.6 + b * 0.4) for a, b in zip(c_claro, c_oscuro))
    col = n.rampa(bw.outputs['Val'], medio, c_claro, 0.38, 0.62)
    big = n.n('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 1.2
    n.l(n.coord('Object'), big.inputs['Vector'])
    col2 = n.mezcla(0.25, col, n.rampa(big.outputs['Fac'], c_oscuro, c_claro, 0.3, 0.7))
    n.set(color=col2, rough=rough, coat=0.15)
    n.relieve(bw.outputs['Val'], 0.03, 0.002)
    return n.m


def tela(nombre, color, rough=0.9, escala=320.0, bump=0.18, sheen=0.6):
    n = N(nombre)
    v = n.coord('Object', (escala, escala, escala))
    nz = n.n('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 2
    n.l(v, nz.inputs['Vector'])
    big = n.n('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 0.02 * escala / 32
    n.l(n.coord('Object', (6, 6, 6)), big.inputs['Vector'])
    oscuro = tuple(c * 0.85 for c in color)
    n.set(color=n.rampa(big.outputs['Fac'], oscuro, color, 0.3, 0.7), rough=rough, sheen=sheen)
    n.relieve(nz.outputs['Fac'], bump, 0.002)
    return n.m


def tejido(nombre, color):
    """Manta tejida (ondas de punto)."""
    n = N(nombre)
    v = n.coord('Object', (1, 1, 1))
    wv = n.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X')
    wv.inputs['Scale'].default_value = 55; wv.inputs['Distortion'].default_value = 1.5
    n.l(v, wv.inputs['Vector'])
    wv2 = n.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y')
    wv2.inputs['Scale'].default_value = 140
    n.l(v, wv2.inputs['Vector'])
    mul = n.n('ShaderNodeMath', operation='MULTIPLY'); n.l(wv.outputs['Fac'], mul.inputs[0]); n.l(wv2.outputs['Fac'], mul.inputs[1])
    oscuro = tuple(c * 0.75 for c in color)
    n.set(color=n.rampa(mul.outputs[0], oscuro, color), rough=0.95, sheen=0.8)
    n.relieve(mul.outputs[0], 0.6, 0.004)
    return n.m


def cuero(nombre, color, rough=0.42):
    n = N(nombre)
    v = n.coord('Object', (90, 90, 90))
    vo = n.n('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 1.0
    n.l(v, vo.inputs['Vector'])
    big = n.n('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 3
    n.l(n.coord('Object'), big.inputs['Vector'])
    oscuro = tuple(c * 0.72 for c in color)
    n.set(color=n.rampa(big.outputs['Fac'], oscuro, color, 0.35, 0.7), rough=rough, coat=0.2)
    n.relieve(vo.outputs['Distance'], 0.12, 0.002)
    return n.m


def inox(nombre, rough=0.28):
    n = N(nombre)
    v = n.coord('Object', (2, 2, 400))
    nz = n.n('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 4
    n.l(v, nz.inputs['Vector'])
    mr = n.n('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough - 0.08; mr.inputs['To Max'].default_value = rough + 0.08
    n.l(nz.outputs['Fac'], mr.inputs['Value'])
    n.set(color=(0.78, 0.78, 0.78), metal=1.0, rough=mr.outputs['Result'])
    return n.m


def granito(nombre, base=(0.62, 0.62, 0.61)):
    """Granito sal y pimienta (meseta de las fotos de cocina y baño)."""
    n = N(nombre)
    v = n.coord('Object', (1, 1, 1))
    vo = n.n('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 70
    n.l(v, vo.inputs['Vector'])
    vo2 = n.n('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = 45; vo2.inputs['Randomness'].default_value = 1
    n.l(v, vo2.inputs['Vector'])
    nz = n.n('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 30; nz.inputs['Detail'].default_value = 6
    n.l(v, nz.inputs['Vector'])
    c = n.rampa(nz.outputs['Fac'], tuple(x * 0.75 for x in base), (0.86, 0.85, 0.83), 0.4, 0.62)
    negro = n.rampa(vo.outputs['Distance'], (0.03, 0.03, 0.03), (1, 1, 1), 0.10, 0.13)
    m1 = n.n('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); m1.inputs['Factor'].default_value = 1.0
    n.l(c, m1.inputs[6]); n.l(negro, m1.inputs[7])
    blanco = n.rampa(vo2.outputs['Distance'], (0.95, 0.94, 0.92), (0, 0, 0), 0.06, 0.08)
    m2 = n.n('ShaderNodeMix', data_type='RGBA', blend_type='LIGHTEN'); m2.inputs['Factor'].default_value = 1.0
    n.l(m1.outputs[2], m2.inputs[6]); n.l(blanco, m2.inputs[7])
    n.set(color=m2.outputs[2], rough=0.12, coat=0.4)
    return n.m


def cuadro(nombre, semilla, cielo=(0.45, 0.62, 0.82), monte=(0.36, 0.44, 0.52), campo=(0.30, 0.42, 0.16)):
    """Paisaje pintado (montañas de Chiriquí) a partir de coordenadas generadas del lienzo."""
    n = N(nombre)
    tc = n.n('ShaderNodeTexCoord')
    sep = n.n('ShaderNodeSeparateXYZ'); n.l(tc.outputs['Generated'], sep.inputs['Vector'])
    # dimensión horizontal del lienzo: x o y según cómo quedó el objeto; se usan las dos
    hx = n.n('ShaderNodeMath', operation='ADD'); n.l(sep.outputs['X'], hx.inputs[0]); n.l(sep.outputs['Y'], hx.inputs[1])

    def ruido1d(esc, sem):
        cb = n.n('ShaderNodeCombineXYZ'); m = n.n('ShaderNodeMath', operation='MULTIPLY'); m.inputs[1].default_value = esc
        n.l(hx.outputs[0], m.inputs[0]); n.l(m.outputs[0], cb.inputs['X']); cb.inputs['Y'].default_value = sem
        nz = n.n('ShaderNodeTexNoise'); nz.inputs['Detail'].default_value = 4; n.l(cb.outputs['Vector'], nz.inputs['Vector'])
        return nz.outputs['Fac']

    def linea(base, amp, fac):
        m = n.n('ShaderNodeMath', operation='MULTIPLY_ADD'); m.inputs[1].default_value = amp; m.inputs[2].default_value = base - amp / 2
        n.l(fac, m.inputs[0])
        g = n.n('ShaderNodeMath', operation='GREATER_THAN'); n.l(sep.outputs['Z'], g.inputs[0]); n.l(m.outputs[0], g.inputs[1])
        return g.outputs[0]
    sobre_campo = linea(0.42, 0.18, ruido1d(2.5, semilla))
    sobre_monte = linea(0.62, 0.34, ruido1d(1.3, semilla + 3.1))
    grad = n.rampa(sep.outputs['Z'], (0.86, 0.88, 0.86), cielo, 0.45, 1.0)
    pincel = n.n('ShaderNodeTexNoise'); pincel.inputs['Scale'].default_value = 25; pincel.inputs['Detail'].default_value = 6
    n.l(tc.outputs['Generated'], pincel.inputs['Vector'])
    campo_c = n.rampa(pincel.outputs['Fac'], tuple(c * 0.6 for c in campo), tuple(min(1, c * 1.5) for c in campo), 0.35, 0.65)
    monte_c = n.rampa(pincel.outputs['Fac'], tuple(c * 0.8 for c in monte), tuple(min(1, c * 1.2) for c in monte), 0.3, 0.7)
    a = n.mezcla(sobre_monte, monte_c, grad)
    b = n.mezcla(sobre_campo, campo_c, a)
    n.set(color=b, rough=0.6)
    n.relieve(pincel.outputs['Fac'], 0.15, 0.002)
    return n.m


def cortina(nombre, color, opacidad=0.65):
    n = N(nombre)
    n.set(color=color, rough=0.9, sheen=0.7)
    tr = n.n('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = color + (1,)
    mx = n.n('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.45
    n.l(n.b.outputs['BSDF'], mx.inputs[1]); n.l(tr.outputs['BSDF'], mx.inputs[2])
    tp = n.n('ShaderNodeBsdfTransparent')
    mx2 = n.n('ShaderNodeMixShader'); mx2.inputs['Fac'].default_value = opacidad
    n.l(tp.outputs['BSDF'], mx2.inputs[1]); n.l(mx.outputs['Shader'], mx2.inputs[2])
    n.l(mx2.outputs['Shader'], n.out.inputs['Surface'])
    return n.m


def hoja(nombre, color):
    n = N(nombre)
    v = n.coord('Object', (12, 12, 12))
    nz = n.n('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1; n.l(v, nz.inputs['Vector'])
    oscuro = tuple(c * 0.7 for c in color)
    n.set(color=n.rampa(nz.outputs['Fac'], oscuro, color, 0.3, 0.7), rough=0.45, sss=0.0, coat=0.3)
    tr = n.n('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = tuple(min(1, c * 1.4) for c in color) + (1,)
    mx = n.n('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.25
    n.l(n.b.outputs['BSDF'], mx.inputs[1]); n.l(tr.outputs['BSDF'], mx.inputs[2])
    n.l(mx.outputs['Shader'], n.out.inputs['Surface'])
    return n.m


def bloque_vidrio(nombre):
    """Bloques de vidrio 19×19 de las fachadas del edificio gris."""
    n = N(nombre)
    v = n.coord('UV')
    br = n.n('ShaderNodeTexBrick', offset=0.0)
    for k, val in (('Scale', 1.0), ('Brick Width', 0.175), ('Row Height', 0.175), ('Mortar Size', 0.012), ('Bias', 0)):
        br.inputs[k].default_value = val
    br.inputs['Color1'].default_value = (0.80, 0.86, 0.88, 1); br.inputs['Color2'].default_value = (0.78, 0.84, 0.86, 1)
    br.inputs['Mortar'].default_value = (0.75, 0.74, 0.72, 1)
    n.l(v, br.inputs['Vector'])
    wv = n.n('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 3
    n.l(v, wv.inputs['Vector'])
    n.set(color=br.outputs['Color'], rough=0.08, trans=0.0)
    tr = n.n('ShaderNodeMath', operation='SUBTRACT'); tr.inputs[0].default_value = 0.85; n.l(br.outputs['Fac'], tr.inputs[1])
    n.set(trans=tr.outputs[0])
    n.relieve(wv.outputs['Fac'], 0.4, 0.004)
    return n.m


def emisor(nombre, color, fuerza):
    n = N(nombre)
    n.set(color=color, rough=0.5, emis_col=color, emis=fuerza)
    return n.m


# ------------------------------------------------------------------ catálogo
def crear():
    """Devuelve el diccionario de materiales de interior (se suma al de bloqueo)."""
    M = {}
    # obra
    M['piso_casa'] = baldosa('piso_casa', (0.80, 0.74, 0.63), (0.76, 0.70, 0.59), (0.60, 0.56, 0.50), (0.45, 0.45), 0.10)
    M['piso_gris'] = baldosa('piso_gris', (0.83, 0.83, 0.81), (0.79, 0.79, 0.78), (0.64, 0.64, 0.63), (0.60, 0.60), 0.09)
    M['piso_bano'] = baldosa('piso_bano', (0.60, 0.61, 0.62), (0.56, 0.57, 0.58), (0.80, 0.80, 0.79), (0.30, 0.30), 0.35)
    M['piso_terraza'] = baldosa('piso_terraza', (0.86, 0.85, 0.82), (0.82, 0.81, 0.78), (0.66, 0.65, 0.62), (0.45, 0.45), 0.10)
    M['pintura_casa'] = pintura('pintura_casa', (0.88, 0.82, 0.68))
    M['pintura_gris'] = pintura('pintura_gris', (0.85, 0.86, 0.85))
    M['pintura_amarilla'] = pintura('pintura_amarilla', (0.90, 0.78, 0.47))
    M['pintura_celeste'] = pintura('pintura_celeste', (0.70, 0.80, 0.87))
    M['pintura_salvia'] = pintura('pintura_salvia', (0.74, 0.79, 0.70))
    M['azulejo_rojo'] = baldosa('azulejo_rojo', (0.70, 0.07, 0.04), (0.64, 0.06, 0.04), (0.88, 0.87, 0.85), (0.20, 0.30), 0.08)
    M['azulejo_blanco'] = baldosa('azulejo_blanco', (0.90, 0.90, 0.89), (0.87, 0.87, 0.86), (0.78, 0.78, 0.77), (0.30, 0.60), 0.08)
    M['azulejo_beige'] = baldosa('azulejo_beige', (0.84, 0.78, 0.67), (0.80, 0.74, 0.63), (0.92, 0.90, 0.86), (0.30, 0.30), 0.08)
    M['azulejo_metro'] = baldosa('azulejo_metro', (0.92, 0.92, 0.91), (0.89, 0.89, 0.88), (0.72, 0.72, 0.71), (0.20, 0.10), 0.06, desfase=0.5)
    M['cielo'] = liso('cielo', (0.89, 0.89, 0.88), 0.92)
    M['cielo_reticula'] = reticula('cielo_reticula')
    M['bloque_vidrio'] = bloque_vidrio('bloque_vidrio')
    # maderas, laminados
    M['madera_clara'] = madera('madera_clara', (0.74, 0.56, 0.36), (0.58, 0.40, 0.23))
    M['madera_media'] = madera('madera_media', (0.50, 0.32, 0.18), (0.32, 0.19, 0.10))
    M['madera_oscura'] = madera('madera_oscura', (0.26, 0.14, 0.08), (0.13, 0.07, 0.04), rough=0.35)
    M['madera_rojiza'] = madera('madera_rojiza', (0.42, 0.13, 0.07), (0.26, 0.07, 0.04), rough=0.3)
    M['laminado_blanco'] = liso('laminado_blanco', (0.88, 0.88, 0.86), 0.32)
    M['laminado_gris'] = liso('laminado_gris', (0.55, 0.56, 0.57), 0.4)
    M['laminado_madera'] = madera('laminado_madera', (0.70, 0.52, 0.33), (0.60, 0.43, 0.27), escala=0.6, rough=0.3)
    # telas y cueros
    M['tela_beige'] = tela('tela_beige', (0.72, 0.65, 0.54))
    M['tela_crema'] = tela('tela_crema', (0.86, 0.81, 0.72))
    M['tela_olivo'] = tela('tela_olivo', (0.38, 0.40, 0.19))
    M['tela_gris'] = tela('tela_gris', (0.44, 0.45, 0.47))
    M['tela_lino'] = tela('tela_lino', (0.62, 0.60, 0.56))
    M['tela_azul'] = tela('tela_azul', (0.16, 0.24, 0.40))
    M['tela_salvia'] = tela('tela_salvia', (0.55, 0.60, 0.50))
    M['sabana_blanca'] = tela('sabana_blanca', (0.91, 0.91, 0.90), escala=500, bump=0.08, sheen=0.3)
    M['sabana_celeste'] = tela('sabana_celeste', (0.52, 0.70, 0.87), escala=500, bump=0.08, sheen=0.3)
    M['manta_arena'] = tejido('manta_arena', (0.74, 0.63, 0.47))
    M['manta_gris'] = tejido('manta_gris', (0.62, 0.62, 0.60))
    M['cuero_camel'] = cuero('cuero_camel', (0.55, 0.30, 0.12))
    M['cuero_negro'] = cuero('cuero_negro', (0.035, 0.035, 0.035), 0.35)
    M['vinil_azul'] = cuero('vinil_azul', (0.04, 0.14, 0.55), 0.3)
    M['vinil_gris'] = cuero('vinil_gris', (0.35, 0.36, 0.38), 0.35)
    # metales, plásticos, loza, vidrio
    M['cromo'] = liso('cromo', (0.92, 0.92, 0.92), 0.06, 1.0)
    M['inox'] = inox('inox')
    M['aluminio'] = liso('aluminio', (0.80, 0.81, 0.83), 0.32, 1.0)
    M['metal_blanco'] = liso('metal_blanco', (0.88, 0.88, 0.87), 0.28, 0.0, coat=0.3)
    M['metal_negro'] = liso('metal_negro', (0.025, 0.025, 0.025), 0.38, 0.4)
    M['metal_gris'] = liso('metal_gris_int', (0.34, 0.35, 0.36), 0.4, 0.5)
    M['metal_cafe'] = liso('metal_cafe', (0.14, 0.08, 0.05), 0.3, 0.2, coat=0.4)
    M['plastico_blanco'] = liso('plastico_blanco', (0.86, 0.86, 0.84), 0.32)
    M['plastico_gris'] = liso('plastico_gris', (0.30, 0.31, 0.32), 0.4)
    M['plastico_negro'] = liso('plastico_negro', (0.03, 0.03, 0.03), 0.45)
    M['goma'] = liso('goma', (0.02, 0.02, 0.02), 0.8)
    M['porcelana'] = liso('porcelana', (0.93, 0.93, 0.92), 0.05, coat=0.5)
    M['granito'] = granito('granito')
    M['vidrio_int'] = liso('vidrio_int', (0.95, 0.97, 0.97), 0.02, trans=1.0, ior=1.5)
    M['espejo'] = liso('espejo', (0.95, 0.95, 0.95), 0.02, 1.0)
    M['pantalla'] = liso('pantalla', (0.005, 0.005, 0.006), 0.06, coat=1.0)
    M['agua_azul'] = liso('agua_azul', (0.45, 0.70, 0.90), 0.05, trans=0.9, ior=1.33)
    M['papel'] = liso('papel', (0.93, 0.93, 0.91), 0.8)
    M['pizarra'] = liso('pizarra', (0.06, 0.07, 0.06), 0.85)
    # luces
    M['luz_panel'] = emisor('luz_panel', (1.0, 0.95, 0.86), 6.0)
    M['luz_calida'] = emisor('luz_calida', (1.0, 0.80, 0.55), 5.0)
    M['pantalla_lampara'] = cortina('pantalla_lampara', (0.95, 0.90, 0.80), 0.9)
    # textiles de ventana
    M['cortina_blanca'] = cortina('cortina_blanca', (0.93, 0.92, 0.89), 0.55)
    M['cortina_beige'] = cortina('cortina_beige', (0.80, 0.70, 0.52), 0.85)
    # plantas, macetas, objetos
    M['hoja'] = hoja('hoja', (0.06, 0.20, 0.05))
    M['hoja_clara'] = hoja('hoja_clara', (0.13, 0.32, 0.07))
    M['tronco'] = liso('tronco', (0.20, 0.13, 0.08), 0.8)
    M['tierra'] = liso('tierra', (0.08, 0.05, 0.03), 0.95)
    M['maceta_blanca'] = liso('maceta_blanca', (0.88, 0.87, 0.84), 0.3)
    M['maceta_barro'] = liso('maceta_barro', (0.55, 0.26, 0.14), 0.7)
    M['maceta_gris'] = liso('maceta_gris', (0.40, 0.40, 0.39), 0.75)
    M['cesta'] = tela('cesta', (0.48, 0.33, 0.17), escala=60, bump=0.6, sheen=0.0)
    for i, c in enumerate([(0.55, 0.08, 0.06), (0.08, 0.20, 0.45), (0.12, 0.35, 0.18), (0.80, 0.62, 0.20),
                           (0.85, 0.85, 0.82), (0.30, 0.10, 0.25)]):
        M[f'color_{i}'] = liso(f'color_{i}', c, 0.45)
    M['pelota_roja'] = liso('pelota_roja', (0.75, 0.05, 0.04), 0.35)
    M['pelota_verde'] = liso('pelota_verde', (0.15, 0.55, 0.10), 0.35)
    M['pelota_azul'] = liso('pelota_azul', (0.05, 0.25, 0.70), 0.35)
    M['fruta_roja'] = liso('fruta_roja', (0.60, 0.05, 0.03), 0.3)
    M['fruta_amarilla'] = liso('fruta_amarilla', (0.85, 0.65, 0.08), 0.35)
    M['fruta_naranja'] = liso('fruta_naranja', (0.85, 0.35, 0.03), 0.4)
    for i, (ci, mo, ca) in enumerate([((0.45, 0.62, 0.82), (0.36, 0.44, 0.52), (0.30, 0.42, 0.16)),
                                      ((0.80, 0.62, 0.45), (0.45, 0.38, 0.40), (0.42, 0.40, 0.15)),
                                      ((0.55, 0.70, 0.80), (0.30, 0.38, 0.30), (0.20, 0.36, 0.12))]):
        M[f'lienzo_{i}'] = cuadro(f'lienzo_{i}', 1.7 * i + 0.3, ci, mo, ca)
    return M
