"""
Emplazamiento proporcional sobre docs/lote-satelite.png (770 x 996 px).

Todo lo de este archivo es una LECTURA A OJO de la imagen aérea, no una medición:
- El trazo rojo del usuario se copió como referencia y NO se trata como lindero legal.
- Las dos vías que el trazo incluye (C.A al noreste y la calle de tierra al oeste) se restan.
- La escala sale de pedir que el polígono restante mida 2.500 m² (escala uniforme, provisional):
      s = sqrt(2500 / area_px)  ->  ~0,117 m por píxel
- Marco del modelo: X a la derecha de la imagen, Y hacia arriba de la imagen ("norte de imagen").
  No se afirma norte geográfico.
"""
import math

IMG_W, IMG_H = 770, 996
OX, OY = 300.0, 450.0          # píxel que cae en el origen del modelo

# ---- trazo rojo del usuario (px) ----
ROJO = [(297, 83), (345, 100), (400, 140), (450, 172), (500, 190), (550, 213), (590, 238), (600, 280), (600, 320),
        (580, 355), (545, 395), (500, 420), (465, 440), (420, 470), (400, 500), (380, 530), (362, 556), (358, 580),
        (362, 600), (375, 612), (390, 615), (378, 630), (350, 690), (310, 750), (255, 822), (200, 806), (150, 793),
        (100, 776), (75, 744), (55, 722), (35, 716), (12, 709), (37, 712), (40, 680), (45, 625), (50, 600), (80, 550),
        (110, 505), (132, 450), (145, 400), (155, 360), (175, 320), (200, 285), (230, 225), (250, 150), (270, 115)]

# ---- ejes aproximados de las vías que el trazo incluye (px) ----
CA = [(250, 45), (300, 85), (330, 112), (420, 155), (500, 195), (565, 232), (608, 278), (632, 335), (660, 420)]
CA_ANCHO = 44          # px (incluye cunetas/orillas)
OESTE = [(300, 92), (266, 145), (238, 215), (207, 290), (178, 360), (150, 430), (121, 498), (92, 556), (70, 616),
         (57, 690), (20, 726), (-10, 735)]
OESTE_ANCHO = 32

AREA_OBJETIVO = 2500.0


def _shapely():
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
    return Polygon, LineString, unary_union


def geometria_px():
    Polygon, LineString, unary_union = _shapely()
    rojo = Polygon(ROJO).buffer(0)
    ca = LineString(CA).buffer(CA_ANCHO / 2, cap_style=2)
    oe = LineString(OESTE).buffer(OESTE_ANCHO / 2, cap_style=2)
    lote = rojo.difference(unary_union([ca, oe]))
    if lote.geom_type != 'Polygon':
        lote = max(lote.geoms, key=lambda g: g.area)
    lote = lote.simplify(1.5)
    return dict(rojo=rojo, ca=ca, oeste=oe, lote=lote)


def escala():
    return math.sqrt(AREA_OBJETIVO / geometria_px()['lote'].area)


S = None


def s():
    global S
    if S is None:
        S = escala()
    return S


def m(px, py):
    """píxel de la imagen -> metros del modelo"""
    k = s()
    return (k * (px - OX), -k * (py - OY))


def poly_m(poly):
    return [m(x, y) for x, y in list(poly.exterior.coords)[:-1]]


# ---- edificios: marco local leído del satélite ----
# Orientaciones confirmadas con las brújulas de las capturas de Street View (la imagen aérea de
# Google se asume con el norte arriba solo para relacionar esas capturas; no se afirma norte del modelo).
# Casa amarilla: fachada principal (cochera con arco, torre con balcón, ala baja) hacia la C.A, lado
# noreste del techo grande. x local corre a lo largo de esa fachada de izquierda a derecha vista desde
# la C.A (del extremo sureste al noroeste, donde está el garaje de piedra junto a la bifurcación);
# y local entra hacia el fondo (patio de grava, suroeste).
CASA = dict(
    origen_px=(472.3, 344.5),               # esquina frontal izquierda de muros (techo menos alero)
    x_img=(-0.672, -0.738),                 # dirección local x en la imagen
)
# Edificio gris: x de norte a sur a lo largo de la fachada escalonada que da a la calle de tierra,
# y hacia el este (galería abierta). La galería cerrada con listones está en el lado norte.
GRIS = dict(
    origen_px=(174.6, 582.7),               # esquina noroeste de la envolvente del techo
    x_img=(-0.4305, 0.9026),
)


def marco(E):
    """(x, y, ángulo) del marco local en metros del modelo."""
    ox, oy = m(*E['origen_px'])
    ux, uy = E['x_img']
    ang = math.atan2(-uy, ux)       # y de imagen invertida
    return ox, oy, ang


def local_a_m(E, x, y):
    ox, oy, a = marco(E)
    return (ox + x * math.cos(a) - y * math.sin(a), oy + x * math.sin(a) + y * math.cos(a))


def m_a_local(E, X, Y):
    ox, oy, a = marco(E)
    dx, dy = X - ox, Y - oy
    return (dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a))


def m_a_px(X, Y):
    k = s()
    return (X / k + OX, -Y / k + OY)


if __name__ == '__main__':
    g = geometria_px()
    k = s()
    print('escala m/px', round(k, 4))
    print('lote m2', round(g['lote'].area * k * k), ' trazo rojo completo m2', round(g['rojo'].area * k * k))
    for n, E in (('casa', CASA), ('gris', GRIS)):
        print(n, [round(v, 2) for v in marco(E)[:2]], round(math.degrees(marco(E)[2]), 1))
