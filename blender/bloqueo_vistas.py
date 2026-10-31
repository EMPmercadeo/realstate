"""Cámaras equivalentes a las fotos de referencia (marco local de cada edificio, ver sitio.py).
Posiciones estimadas a ojo comparando foto y render; no son una restitución fotogramétrica."""

FOTOS = {
    'casa_frontal': 'web/public/fotos-reales/fachada-frontal.jpg',
    'casa_patio': 'web/public/fotos-reales/casa-amarilla-patio.jpg',
    'gris_acceso': 'web/public/fotos-reales/edificio-gris-noche.jpg',
    'gris_galeria': 'web/public/fotos-reales/edificio-gris.jpg',
}

# edificio: 'casa' o 'gris'; pos/mira en metros locales (x, y, z); lens en mm sobre sensor de 36 mm
VISTAS = {
    'casa_frontal': dict(edif='casa', pos=(5.6, -14.6, 1.5), mira=(6.2, -2.0, 3.6), lens=19, res=(2400, 1351)),
    'casa_patio': dict(edif='casa', pos=(9.6, 20.0, 1.5), mira=(6.8, 11.0, 3.4), lens=14, res=(2400, 1351)),
    'gris_acceso': dict(edif='gris', pos=(-4.6, -0.6, 1.0), mira=(2.6, 7.2, 4.4), lens=19, res=(1024, 899)),
    'gris_galeria': dict(edif='gris', pos=(7.0, 22.0, 1.0), mira=(7.0, 12.0, 5.0), lens=18, res=(2400, 1350)),
}
