"""
Emplazamiento proporcional sobre docs/lote-satelite.png (770 x 996 px).

Todo lo de este archivo es una LECTURA A OJO de la imagen aérea, no una medición:
- El trazo rojo del usuario se copió como referencia y NO se trata como lindero legal.
- Las dos vías que el trazo incluye (C.A al noreste y la calle de tierra al oeste) se restan.
- ESCALA MEDIDA (01-11-2026): 0,1415 m por píxel de docs/lote-satelite.png. Sale de tres fuentes que
  coinciden: la barra de escala de Google Maps en la misma imagen (5 m = 66 px css -> 0,144 m/px),
  y las imágenes de Esri y Bing a escala Web Mercator conocida (distancia casa-gris y techo del gris
  -> 0,139-0,140 m/px). Antes se usaba s = sqrt(2500 / area_px) = 0,117 m/px (suponer que el trazo
  medía 2.500 m²): eso dejaba todo un ~21 % más chico en planta. Con la escala medida el trazo (sin
  las vías) mide ~3.670 m²; si el lote escriturado es de 2.500 m², el lindero real es más chico que
  el trazo (pendiente: plano catastral). Ver docs/fase-mapa.md.
- Los edificios se dibujaron en "unidades de diseño" (las medidas de las etapas 2-4, hechas con la
  escala vieja). KP pasa esas unidades a metros en planta (x, y); las alturas no cambian (se midieron
  con fotos y con la puerta del gris: mano a 1,80 m -> marco a ~2,22 m, hoja de 2,10 m).
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
# eje de la calle de tierra; desde y≈420 px sigue el trazo sobre el satélite de Esri (01-11-2026), que la
# muestra 3-4 m más al este que la lectura anterior, pegada al gris. Junto al gris se acercó ~2 m más con
# Street View: desde la cámara de la panorámica de la calle (que circula por el eje), el gris y el portón se
# ven del mismo tamaño que en el modelo solo si el eje pasa a ~5,8 m de la fachada (ver docs/fase-mapa.md)
OESTE = [(300, 92), (266, 145), (238, 215), (207, 290), (185, 360), (181, 428), (164, 501), (140, 560), (108, 629),
         (79, 693), (47, 733), (-10, 740)]
OESTE_ANCHO = 32

AREA_OBJETIVO = 2500.0          # área que dijo la propietaria (no se usa para la escala)
S_MEDIDA = 0.1415               # m por píxel de lote-satelite.png (ver arriba)


def _shapely():
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
    return Polygon, LineString, unary_union


# Lindero oeste entre el patio de grava de la casa y el gris (fotos y video del 31-10-2026): el muro de la
# calle de tierra corre a ~1 u al oeste del tramo sur del gris (el pilar del portón peatonal toca la
# fachada) y el muro amarillo del jardín queda a ~4 m del camino de baldosa. El trazo, menos la calle,
# lo dejaba ~10 m más afuera. Polígono a recortar, en unidades de diseño del marco del gris.
CORTE_OESTE_GRIS = [(-19.6, -0.9), (16.5, -0.4), (16.5, -40.0), (-19.6, -40.0)]


def geometria_px(cortar=True):
    Polygon, LineString, unary_union = _shapely()
    rojo = Polygon(ROJO).buffer(0)
    ca = LineString(CA).buffer(CA_ANCHO / 2, cap_style=2)
    oe = LineString(OESTE).buffer(OESTE_ANCHO / 2, cap_style=2)
    lote = rojo.difference(unary_union([ca, oe]))
    corte = None
    if cortar:
        corte = Polygon([m_a_px(*local_a_m(GRIS, x, y)) for x, y in CORTE_OESTE_GRIS])
        lote = lote.difference(corte)
    if lote.geom_type != 'Polygon':
        lote = max(lote.geoms, key=lambda g: g.area)
    lote = lote.simplify(1.5)
    return dict(rojo=rojo, ca=ca, oeste=oe, lote=lote, corte=corte)


def escala_trazo():
    """Escala vieja: la que haría medir 2.500 m² al trazo sin vías (0,117 m/px)."""
    return math.sqrt(AREA_OBJETIVO / geometria_px(cortar=False)['lote'].area)


S = None
_KP = None


def s():
    return S_MEDIDA


S_DISENO = 0.11682942          # m/px con que se dibujaron los edificios (etapas 2-4); fijo desde el 01-11-2026


def kp():
    """Factor de planta: unidades de diseño de los edificios -> metros (1,2112). No depende del trazo ni de
    las calles, para que los edificios no cambien de tamaño si se corrige el lindero."""
    return S_MEDIDA / S_DISENO


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
    """Unidades de diseño del edificio -> metros del modelo (incluye el factor de planta KP)."""
    ox, oy, a = marco(E)
    k = kp()
    x, y = x * k, y * k
    return (ox + x * math.cos(a) - y * math.sin(a), oy + x * math.sin(a) + y * math.cos(a))


def m_a_local(E, X, Y):
    ox, oy, a = marco(E)
    dx, dy = X - ox, Y - oy
    k = kp()
    return ((dx * math.cos(a) + dy * math.sin(a)) / k, (-dx * math.sin(a) + dy * math.cos(a)) / k)


def m_a_px(X, Y):
    k = s()
    return (X / k + OX, -Y / k + OY)


if __name__ == '__main__':
    g = geometria_px()
    k = s()
    print('escala m/px', round(k, 4), ' escala de diseño', S_DISENO, ' KP', round(kp(), 4))
    print('lote m2', round(g['lote'].area * k * k), ' trazo rojo completo m2', round(g['rojo'].area * k * k))
    for n, E in (('casa', CASA), ('gris', GRIS)):
        print(n, [round(v, 2) for v in marco(E)[:2]], round(math.degrees(marco(E)[2]), 1))
