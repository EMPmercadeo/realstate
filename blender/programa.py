"""
Programa arquitectónico en coordenadas del sitio (metros).
Marco: x hacia el este (calle), y hacia el norte. La calle corre paralela al eje y por el lado este.
Medidas estimadas de la vista satelital; se corrigen con planos.
"""
import math

# ---------------- LOTE ----------------
LOTE = dict(
    poligono=[(0, 0), (30, 0), (30, 84), (0, 84)],
    cerca_calle=[False, True, False, False],     # qué lados llevan murete + reja (lado de la calle)
    calle=(36.5, 42, 9, 120, 0.0),               # cx, cy, ancho, largo, ángulo
    porton=(30, 60, 4.5, math.pi / 2),           # x, y, ancho, ángulo (sobre el lado este)
    setos=(29.0, 2, 29.0, 52),                   # línea de setos (x0,y0,x1,y1)
)

# ---------------- EDIFICIO GRIS ----------------
GRIS = dict(
    id='gris', nombre='Edificio gris', pos=(3, 8), rot=0.0,
    huella=(18, 16), material_ext='gris_claro', piso_default='ceramica_g', techo='lamina',
    pisos=[
        dict(huella=(26, 16), rooms=[
            dict(id='salon_b', nombre='Salón B', rect=[0, 8, 10, 8], tipo='hospital', camas=6, puertas=[('s', 4.4, 1.2)]),
            dict(id='salon_a', nombre='Salón A', rect=[10, 8, 8, 8], tipo='hospital', camas=4, puertas=[('s', 3.4, 1.2)]),
            dict(id='pasillo', nombre='Pasillo', rect=[0, 5.5, 18, 2.5], tipo='circulacion'),
            dict(id='supervisor', nombre='Oficina del supervisor', rect=[0, 0, 4.5, 5.5], tipo='oficina', puertas=[('n', 1.6, 0.9)]),
            dict(id='admin', nombre='Administración', rect=[4.5, 0, 4.5, 5.5], tipo='oficina', puertas=[('n', 1.6, 0.9)]),
            dict(id='deposito', nombre='Depósito', rect=[9, 0, 3, 5.5], tipo='deposito', puertas=[('n', 1.0, 0.9)]),
            dict(id='escalera', nombre='Escalera', rect=[12, 0, 3, 5.5], tipo='circulacion', escalera=True, puertas=[('n', 0.9, 1.2)]),
            dict(id='bano_acc', nombre='Baño accesible', rect=[15, 0, 3, 5.5], tipo='bano', regadera=True, puertas=[('n', 1.0, 0.9)]),
            dict(id='acceso', nombre='Acceso y recepción', rect=[18, 0, 8, 8], tipo='recepcion', piso='ceramica', puertas=[('e', 3.0, 1.6), ('w', 5.6, 1.4)]),
            dict(id='lavanderia', nombre='Lavandería y servicio', rect=[18, 8, 8, 4], tipo='lavanderia', puertas=[('s', 1.0, 0.9)]),
        ]),
        dict(huella=(26, 16), rooms=[
            dict(id='salon_2', nombre='Salón #2 · movilidad reducida', rect=[0, 8, 6, 8], tipo='hospital', camas=4, puertas=[('s', 2.4, 1.2)]),
            dict(id='hospitalizacion', nombre='Sala de hospitalización', rect=[6, 8, 12, 8], tipo='hospital', camas=10, estacion=True, puertas=[('s', 5.3, 1.4)]),
            dict(id='pasillo2', nombre='Pasillo', rect=[0, 5.5, 18, 2.5], tipo='circulacion', puertas=[('e', 0.5, 1.4)]),
            dict(id='cocina', nombre='Cocina', rect=[0, 0, 5, 5.5], tipo='cocina', puertas=[('n', 2.0, 0.9)]),
            dict(id='refrigerios', nombre='Área de refrigerios', rect=[5, 0, 5, 5.5], tipo='comedor', puertas=[('n', 1.9, 1.2)]),
            dict(id='insumos', nombre='Depósito de insumos', rect=[10, 0, 2, 5.5], tipo='deposito', puertas=[('n', 0.5, 0.9)]),
            dict(id='escalera2', nombre='Escalera', rect=[12, 0, 3, 5.5], tipo='circulacion', puertas=[('n', 0.9, 1.2)]),
            dict(id='bano2', nombre='Baño con regadera', rect=[15, 0, 3, 5.5], tipo='bano', regadera=True, puertas=[('n', 1.0, 0.9)]),
            dict(id='terraza', nombre='Terraza', rect=[18, 0, 8, 12], tipo='terraza', abierto=True, baranda=['e', 'n', 's'], piso='concreto'),
        ]),
    ],
)

# ---------------- CASA AMARILLA ----------------
AMARILLA = dict(
    id='amarilla', nombre='Casa amarilla', pos=(4, 54), rot=0.0,
    huella=(16, 14), material_ext='amarillo', piso_default='ceramica', techo='cuatro_aguas',
    pisos=[
        dict(huella=(16, 14), rooms=[
            dict(id='lavanderia', nombre='Lavandería', rect=[0, 0, 4, 3.5], tipo='lavanderia', puertas=[('e', 1.2, 0.9)]),
            dict(id='cto1', nombre='Cuarto privado #1', rect=[0, 3.5, 4, 4], tipo='habitacion', puertas=[('e', 2.6, 0.9)]),
            dict(id='bano1', nombre='Baño', rect=[0, 7.5, 4, 1.5], tipo='bano', puertas=[('e', 0.3, 0.8)]),
            dict(id='bano2', nombre='Baño', rect=[0, 9, 4, 1.5], tipo='bano', puertas=[('e', 0.3, 0.8)]),
            dict(id='recamara2', nombre='Recámara #2', rect=[0, 10.5, 4, 3.5], tipo='habitacion', puertas=[('e', 1.2, 0.9)]),
            dict(id='cocina', nombre='Cocina', rect=[4, 0, 6, 5], tipo='cocina', puertas=[('n', 2.4, 1.0)]),
            dict(id='comedor', nombre='Comedor y sala de familiares', rect=[4, 5, 6, 6], tipo='comedor'),
            dict(id='pasillo2', nombre='Pasillo', rect=[4, 11, 2, 3], tipo='circulacion', puertas=[('s', 0.3, 1.4)]),
            dict(id='cto3', nombre='Cuarto #3', rect=[6, 11, 4, 3], tipo='habitacion', puertas=[('w', 1.0, 0.9)]),
            dict(id='consultorio', nombre='Consultorio de salud', rect=[10, 0, 6, 5], tipo='oficina', puertas=[('n', 2.4, 0.9)]),
            dict(id='recepcion', nombre='Recepción', rect=[10, 5, 6, 4], tipo='recepcion', puertas=[('e', 1.2, 1.6), ('w', 1.2, 1.6)]),
            dict(id='terapia', nombre='Sala de terapia', rect=[10, 9, 6, 5], tipo='terapia', puertas=[('w', 0.6, 1.2)]),
            dict(id='terraza', nombre='Terraza', rect=[0, 14, 16, 3], tipo='terraza', abierto=True, piso='ceramica'),
            dict(id='porche', nombre='Porche', rect=[16, 0, 3, 9], tipo='porche', abierto=True, piso='ceramica'),
            dict(id='carport', nombre='Estacionamiento bajo techo', rect=[16, 9, 5, 5], tipo='porche', abierto=True, piso='ceramica'),
        ]),
        dict(huella=(7, 7), offset=(4, 4), rooms=[
            dict(id='gerencia', nombre='Oficina del gerente', rect=[4, 4, 5, 7], tipo='oficina', puertas=[('e', 0.4, 0.9)]),
            dict(id='bano_ger', nombre='Baño', rect=[9, 4, 2, 3], tipo='bano', puertas=[('n', 0.5, 0.8)]),
            dict(id='balcon', nombre='Balcón', rect=[9, 7, 2, 4], tipo='terraza', abierto=True, baranda=['e', 'n'], piso='ceramica'),
        ]),
    ],
)

# ---------------- EXTERIORES ----------------
ELEMENTOS = [
    dict(tipo='estacionamiento', pos=(21, 28), tam=(8, 12)),
    dict(tipo='garage', pos=(26.5, 60.5), r=3.4),
    dict(tipo='gazebo', pos=(22, 44), r=3.2),
    dict(tipo='piscina', pos=(10, 42), r=2.3),
    dict(tipo='huerto', pos=(4, 1.5), tam=(12, 5)),
    dict(tipo='rampa', pos=(29, 28), w=1.6, L=10, ang=math.pi / 2),
    dict(tipo='camino', de=(24, 56), a=(22, 48)),
    dict(tipo='camino', de=(22, 40), a=(26, 30)),
    dict(tipo='camino', de=(19, 44), a=(13, 42)),
    dict(tipo='camino', de=(30, 32), a=(29.5, 27)),
]

# (x, y, altura)
ARBOLES = [(3, 36, 9), (14, 36, 7), (4, 48, 8), (3, 76, 9), (12, 77, 8), (26, 78, 6), (3, 4, 8), (21, 82, 8), (22, 2, 7), (14, 82, 7)]
PALMAS = [(27, 72, 7), (23, 76, 6.5), (16, 75, 7), (4, 72, 6), (27, 25.5, 5.5), (7, 50, 6), (1.5, 26, 6), (1, 42, 6), (1, 54, 7), (2, 64, 6.5)]
