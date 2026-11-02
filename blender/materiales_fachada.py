"""
Materiales procedurales de fachada y sitio (repello con desgaste, teja metálica, lámina, baldosa, piedra,
hierro, asfalto, calle de tierra, césped del lote) para el modelo amueblado (build/bloqueo/bloqueo.blend).

Sin efectos al importar: `aplicar()` reescribe los materiales n_* del modelo abierto. Lo usan realismo.py
(muestra de la casa) y cine_render.py --modelo bloqueo (sobrevuelo v2).
"""
import os, math
import bpy
import sitio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEN = os.path.join(ROOT, 'assets', 'textures', 'gen')


class Mat:
    """Reescribe el árbol de nodos de un material existente (mismo nombre, mismos objetos)."""
    def __init__(self, nombre):
        m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
        m.use_nodes = True
        self.m = m; self.nt = m.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.out = self.nt.nodes.new('ShaderNodeOutputMaterial')
        self.pb = self.nt.nodes.new('ShaderNodeBsdfPrincipled')
        self.l(self.pb.outputs[0], self.out.inputs['Surface'])

    def n(self, tipo, **kw):
        nd = self.nt.nodes.new(tipo)
        for k, v in kw.items():
            if hasattr(nd, k) and not isinstance(getattr(nd, k), bpy.types.bpy_prop_collection):
                setattr(nd, k, v)
            else:
                nd.inputs[k].default_value = v
        return nd

    def l(self, a, b):
        self.nt.links.new(a, b)

    def pos(self, tipo='world'):
        """Coordenadas: 'world' (posición global, continua entre piezas) u 'object'."""
        if tipo == 'world':
            return self.n('ShaderNodeNewGeometry').outputs['Position']
        return self.n('ShaderNodeTexCoord').outputs['Object']

    def ruido(self, vec, escala, detalle=6, rough=0.55, estirar=None):
        if estirar:
            mp = self.n('ShaderNodeMapping'); mp.inputs['Scale'].default_value = estirar
            self.l(vec, mp.inputs['Vector']); vec = mp.outputs['Vector']
        nz = self.n('ShaderNodeTexNoise', Scale=escala, Detail=detalle, Roughness=rough)
        self.l(vec, nz.inputs['Vector'])
        return nz.outputs['Fac']

    def rampa(self, fac, pares):
        r = self.n('ShaderNodeValToRGB')
        el = r.color_ramp.elements
        while len(el) < len(pares):
            el.new(0.5)
        for e, (p, c) in zip(el, pares):
            e.position = p
            e.color = (*c, 1) if len(c) == 3 else c
        self.l(fac, r.inputs['Fac'])
        return r.outputs['Color']

    def mezcla(self, fac, a, b, modo='MIX'):
        mx = self.n('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = modo
        if isinstance(fac, (int, float)):
            mx.inputs['Factor'].default_value = fac
        else:
            self.l(fac, mx.inputs['Factor'])
        for k, v in (('A', a), ('B', b)):
            if isinstance(v, tuple):
                mx.inputs[k].default_value = (*v, 1) if len(v) == 3 else v
            else:
                self.l(v, mx.inputs[k])
        return mx.outputs['Result']

    def mate(self, op, a, b=None, clamp=False):
        m = self.n('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.l(v, m.inputs[i])
        return m.outputs[0]

    def rango(self, val, a, b, c=0.0, d=1.0, suave=True):
        mr = self.n('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP' if suave else 'LINEAR'
        mr.inputs['From Min'].default_value = a; mr.inputs['From Max'].default_value = b
        mr.inputs['To Min'].default_value = c; mr.inputs['To Max'].default_value = d
        self.l(val, mr.inputs['Value'])
        return mr.outputs['Result']

    def z(self):
        sep = self.n('ShaderNodeSeparateXYZ'); self.l(self.pos('world'), sep.inputs['Vector'])
        return sep.outputs['Z']

    def bump(self, alto, fuerza, dist=0.02, normal=None):
        b = self.n('ShaderNodeBump'); b.inputs['Strength'].default_value = fuerza
        b.inputs['Distance'].default_value = dist
        self.l(alto, b.inputs['Height'])
        if normal is not None:
            self.l(normal, b.inputs['Normal'])
        return b.outputs['Normal']

    def img(self, archivo, vec, no_color=False):
        tx = self.n('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(os.path.join(GEN, archivo), check_existing=True)
        if no_color:
            tx.image.colorspace_settings.name = 'Non-Color'
        self.l(vec, tx.inputs['Vector'])
        return tx

    def base(self, color, rough=None, normal=None, metal=None, spec=None):
        if isinstance(color, tuple):
            self.pb.inputs['Base Color'].default_value = (*color, 1)
        else:
            self.l(color, self.pb.inputs['Base Color'])
        if rough is not None:
            if isinstance(rough, (int, float)):
                self.pb.inputs['Roughness'].default_value = rough
            else:
                self.l(rough, self.pb.inputs['Roughness'])
        if normal is not None:
            self.l(normal, self.pb.inputs['Normal'])
        if metal is not None:
            self.pb.inputs['Metallic'].default_value = metal
        if spec is not None:
            self.pb.inputs['Specular IOR Level'].default_value = spec


SUCIO = (0.20, 0.18, 0.14)


def estuco(nombre, color, sucio=0.7, manchas=0.35, rough=0.9):
    """Repello pintado: variación de tono, manchas de humedad, suciedad que sube del suelo y
    chorreado vertical; relieve fino del repello."""
    M = Mat(nombre)
    w = M.pos('world')
    var = M.ruido(w, 0.45, 4)
    c = M.mezcla(M.rango(var, 0.35, 0.65), tuple(x * 0.9 for x in color), tuple(min(1, x * 1.06) for x in color))
    # manchas grandes de humedad / pintura gastada
    mancha = M.rango(M.ruido(w, 1.6, 8, 0.6), 0.55, 0.72, 0, manchas)
    c = M.mezcla(mancha, c, M.mezcla(0.55, c, SUCIO, 'MULTIPLY'))
    # suciedad que sube del suelo (salpicadura de lluvia) con borde irregular
    z = M.z()
    zr = M.mate('ADD', z, M.mate('MULTIPLY', M.ruido(w, 3.0, 6), 0.5))
    pie = M.rango(zr, 0.95, 0.15, 0, sucio)
    c = M.mezcla(pie, c, SUCIO)
    # chorreado vertical
    chorro = M.rango(M.ruido(w, 2.0, 4, 0.5, estirar=(6, 6, 0.35)), 0.6, 0.8, 0, 0.18 * sucio)
    c = M.mezcla(chorro, c, SUCIO)
    fino = M.ruido(w, 70, 10, 0.7)
    medio = M.ruido(w, 9, 6)
    nor = M.bump(fino, 0.25, 0.004, M.bump(medio, 0.12, 0.01))
    M.base(c, M.rango(var, 0, 1, rough - 0.05, rough), nor, spec=0.3)
    M.m.diffuse_color = (*color, 1)
    return M.m


def teja_metalica(nombre, color):
    """Lámina con perfil de teja (escalón cada ~35 cm a lo largo de la pendiente: bandas en z),
    nervios verticales cada 20 cm, pintura algo decolorada por el sol y suciedad en los escalones."""
    M = Mat(nombre)
    w = M.pos('world')
    wv = M.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', wave_profile='SAW')
    wv.inputs['Scale'].default_value = 0.314 / 0.115
    wv.inputs['Distortion'].default_value = 0.0
    M.l(w, wv.inputs['Vector'])
    paso = wv.outputs['Fac']
    var = M.ruido(w, 0.8, 5)
    c = M.mezcla(M.rango(var, 0.3, 0.7), tuple(x * 0.82 for x in color), tuple(min(1, x * 1.18) for x in color))
    c = M.mezcla(M.rango(paso, 0.85, 1.0, 0, 0.35), c, (0.12, 0.05, 0.035))      # sombra/suciedad del escalón
    c = M.mezcla(M.rango(M.ruido(w, 3.5, 8), 0.6, 0.75, 0, 0.3), c, (0.55, 0.42, 0.38))   # decolorado
    nor = M.bump(paso, 0.55, 0.02, M.bump(M.ruido(w, 40, 6), 0.08, 0.003))
    M.base(c, M.rango(var, 0, 1, 0.38, 0.55), nor, spec=0.5)
    M.m.diffuse_color = (*color, 1)
    return M.m


def baldosa(nombre, c1, c2, junta, lado=0.33, coords='object'):
    """Baldosa cerámica cuadrada con junta, variación por pieza, desgaste y brillo."""
    M = Mat(nombre)
    v = M.pos(coords)
    br = M.n('ShaderNodeTexBrick', offset=0.0, squash=1.0)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.008
    br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Brick Width'].default_value = lado
    br.inputs['Row Height'].default_value = lado
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1)
    br.inputs['Mortar'].default_value = (*junta, 1)
    M.l(v, br.inputs['Vector'])
    c = br.outputs['Color']
    gasto = M.rango(M.ruido(v, 0.7, 6), 0.45, 0.75, 0, 0.45)
    c = M.mezcla(gasto, c, M.mezcla(0.5, c, (0.30, 0.24, 0.18), 'MULTIPLY'))
    c = M.mezcla(M.rango(M.ruido(v, 12, 8), 0.62, 0.8, 0, 0.25), c, (0.18, 0.15, 0.12))
    junta_f = br.outputs['Fac']
    rough = M.mate('ADD', M.mate('MULTIPLY', junta_f, 0.4), M.rango(M.ruido(v, 2.5, 4), 0, 1, 0.35, 0.6))
    nor = M.bump(M.mate('SUBTRACT', 1.0, junta_f), 0.6, 0.004, M.bump(M.ruido(v, 50, 8), 0.06, 0.002))
    M.base(c, rough, nor, spec=0.5)
    M.m.diffuse_color = (*c1, 1)
    return M.m


def piedra(nombre):
    """Enchape de piedra irregular (garaje y zócalo de la casa)."""
    M = Mat(nombre)
    w = M.pos('world')
    vo = M.n('ShaderNodeTexVoronoi', feature='F1'); vo.inputs['Scale'].default_value = 5.5
    vo.inputs['Randomness'].default_value = 1.0
    M.l(w, vo.inputs['Vector'])
    ed = M.n('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE'); ed.inputs['Scale'].default_value = 5.5
    M.l(w, ed.inputs['Vector'])
    cel = M.rampa(vo.outputs['Color'], [(0.0, (0.16, 0.15, 0.13)), (0.5, (0.30, 0.28, 0.25)), (1.0, (0.42, 0.38, 0.32))])
    sep = M.n('ShaderNodeSeparateColor'); M.l(cel, sep.inputs[0])
    junta = M.rango(ed.outputs['Distance'], 0.0, 0.06, 1, 0)
    c = M.mezcla(junta, cel, (0.30, 0.29, 0.27))
    c = M.mezcla(M.rango(M.ruido(w, 18, 8), 0.4, 0.8, 0, 0.5), c, (0.12, 0.11, 0.10))
    alto = M.mate('ADD', M.mate('MULTIPLY', M.mate('SUBTRACT', 1, junta), 0.8), M.mate('MULTIPLY', M.ruido(w, 25, 8), 0.2))
    M.base(c, 0.85, M.bump(alto, 0.8, 0.02), spec=0.3)
    return M.m


def metal_pintado(nombre, color, rough=0.45, oxido=0.12):
    M = Mat(nombre)
    w = M.pos('world')
    c = M.mezcla(M.rango(M.ruido(w, 6, 8), 0.62, 0.78, 0, oxido), color, (0.22, 0.09, 0.04))
    M.base(c, M.rango(M.ruido(w, 3, 4), 0, 1, rough - 0.1, rough + 0.15), M.bump(M.ruido(w, 60, 6), 0.05, 0.002), metal=0.0, spec=0.5)
    M.m.diffuse_color = (*color, 1)
    return M.m


def asfalto(nombre):
    M = Mat(nombre)
    w = M.pos('world')
    c = M.mezcla(M.rango(M.ruido(w, 0.5, 4), 0.3, 0.7), (0.035, 0.035, 0.035), (0.075, 0.072, 0.068))
    c = M.mezcla(M.rango(M.ruido(w, 90, 4), 0.62, 0.7, 0, 0.6), c, (0.20, 0.19, 0.18))
    c = M.mezcla(M.rango(M.ruido(w, 2.2, 8, 0.6, estirar=(1, 8, 1)), 0.68, 0.74, 0, 0.5), c, (0.015, 0.015, 0.015))
    M.base(c, 0.88, M.bump(M.ruido(w, 120, 6), 0.35, 0.003), spec=0.3)
    return M.m


def suelo_jardin(nombre, pasto=0.6):
    """Tierra con pasto ralo (lote): mezcla de tierra rojiza y césped de la textura generada."""
    M = Mat(nombre)
    w = M.pos('world')
    mp = M.n('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.45, 0.45, 0.45)
    M.l(w, mp.inputs['Vector'])
    tx = M.img('grass_color.jpg', mp.outputs['Vector'])
    verde = M.mezcla(0.9, tx.outputs['Color'], (0.34, 0.32, 0.20), 'MULTIPLY')
    seco = M.mezcla(0.8, tx.outputs['Color'], (0.62, 0.48, 0.20), 'MULTIPLY')            # pasto quemado por el sol
    verde = M.mezcla(M.rango(M.ruido(w, 0.9, 6), 0.45, 0.7), verde, seco)
    tierra = M.mezcla(M.rango(M.ruido(w, 6, 8), 0.3, 0.7), (0.10, 0.075, 0.05), (0.19, 0.14, 0.09))     # tierra parda, no rosada
    mask = M.rango(M.ruido(w, 0.35, 6, 0.6), 0.5 - pasto * 0.3, 0.6 - pasto * 0.3)
    c = M.mezcla(mask, tierra, verde)
    M.base(c, 0.92, M.bump(M.ruido(w, 30, 8), 0.4, 0.01), spec=0.25)
    return M.m


def vidrio(nombre):
    M = Mat(nombre)
    M.pb.inputs['Base Color'].default_value = (0.80, 0.86, 0.88, 1)
    M.pb.inputs['Roughness'].default_value = 0.02
    M.pb.inputs['Transmission Weight'].default_value = 1.0
    M.pb.inputs['IOR'].default_value = 1.52
    M.m.diffuse_color = (0.3, 0.35, 0.38, 0.4)
    return M.m


OCRE = (0.58, 0.36, 0.10)


def lamina_ondulada(nombre, color, paso=0.076):
    """Lámina acanalada de los remates del edificio gris: nervios verticales cada `paso` m (en el marco
    del edificio, así sirven en las cuatro fachadas), brillo metálico gastado y chorreado de óxido."""
    M = Mat(nombre)
    w = M.pos('world')
    gx, gy, ga = sitio.marco(sitio.GRIS)
    mp = M.n('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, -ga)
    M.l(w, mp.inputs['Vector'])
    sep = M.n('ShaderNodeSeparateXYZ'); M.l(mp.outputs['Vector'], sep.inputs['Vector'])
    k = 2 * math.pi / paso
    sx = M.mate('SINE', M.mate('MULTIPLY', sep.outputs['X'], k))
    sy = M.mate('SINE', M.mate('MULTIPLY', sep.outputs['Y'], k))
    onda = M.mate('ADD', sx, sy)
    c = M.mezcla(M.rango(M.ruido(w, 1.2, 5), 0.3, 0.7), tuple(x * 0.85 for x in color), color)
    oxido = M.rango(M.ruido(w, 2.5, 6, 0.5, estirar=(5, 5, 0.4)), 0.62, 0.78, 0, 0.35)
    c = M.mezcla(oxido, c, (0.24, 0.13, 0.07))
    M.base(c, M.rango(M.ruido(w, 4, 4), 0, 1, 0.3, 0.5), M.bump(onda, 0.5, 0.012), metal=0.6, spec=0.5)
    M.m.diffuse_color = (*color, 1)
    return M.m


def tierra_camino(nombre):
    """Calle de tierra (foto calle-frente): tierra rojiza con grava suelta y huellas de llanta."""
    M = Mat(nombre)
    w = M.pos('world')
    c = M.mezcla(M.rango(M.ruido(w, 0.6, 5), 0.3, 0.7), (0.20, 0.12, 0.07), (0.33, 0.22, 0.14))
    vo = M.n('ShaderNodeTexVoronoi', feature='F1'); vo.inputs['Scale'].default_value = 22; M.l(w, vo.inputs['Vector'])
    piedras = M.rango(vo.outputs['Distance'], 0.0, 0.25, 1, 0)
    c = M.mezcla(M.mate('MULTIPLY', piedras, M.rango(M.ruido(w, 3, 4), 0.4, 0.6)), c, (0.42, 0.40, 0.37))
    c = M.mezcla(M.rango(M.ruido(w, 1.2, 6, 0.6), 0.6, 0.75, 0, 0.5), c, (0.16, 0.20, 0.07))     # matas de pasto
    M.base(c, 0.95, M.bump(M.mate('ADD', piedras, M.ruido(w, 8, 8)), 0.6, 0.03), spec=0.25)
    return M.m


def aplicar(suelo=True):
    """Reescribe los materiales de fachada y sitio del modelo abierto. suelo=False deja el césped del lote y del
    entorno como esté (el sobrevuelo v2 pone el suyo)."""
    estuco('n_muro_casa', OCRE, sucio=0.75, manchas=0.4)
    estuco('n_blanco', (0.74, 0.72, 0.66), sucio=0.55, manchas=0.2, rough=0.8)
    estuco('n_cielo_alero', (0.66, 0.62, 0.54), sucio=0.0, manchas=0.1)
    estuco('n_muro_gris', (0.40, 0.42, 0.44), sucio=0.7, manchas=0.35)
    estuco('n_concreto', (0.42, 0.41, 0.39), sucio=0.5, manchas=0.4)
    teja_metalica('n_cubierta_casa', (0.36, 0.085, 0.05))
    teja_metalica('n_cubierta_gris', (0.40, 0.41, 0.42))
    lamina_ondulada('n_remate_lamina', (0.55, 0.56, 0.57))
    baldosa('n_piso_ceramica', (0.60, 0.33, 0.17), (0.50, 0.27, 0.14), (0.26, 0.20, 0.15))
    piedra('n_piedra')
    asfalto('n_via')
    camino = tierra_camino('calle_tierra')
    for o in bpy.data.objects:
        if o.name.startswith('via_oeste'):
            o.data.materials.clear(); o.data.materials.append(camino)
    if suelo:
        suelo_jardin('n_lote', pasto=0.45)
        suelo_jardin('n_entorno', pasto=0.6)
    vidrio('n_vidrio_claro')
    for nombre in ('metal_negro',):
        if bpy.data.materials.get(nombre):
            metal_pintado(nombre, (0.018, 0.018, 0.018), rough=0.42, oxido=0.1)
    terracota = estuco('remate_terracota', (0.42, 0.17, 0.09), sucio=0.3, manchas=0.3, rough=0.75)
    for o in bpy.data.objects:
        if o.name.startswith('ca_pilar_bola'):
            o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(terracota)
