"""Cámaras de las vistas interiores (marco local de cada edificio). Las usan bloqueo.py y render_interiores.py."""
import sitio

INTERIORES = {   # (edificio, posición local (x, y, z), mira (x, y, z), lente, exposición)
    'int_casa_recepcion': (sitio.CASA, (8.85, 0.30, 1.55), (6.8, 3.3, 1.10), 18, -0.5),
    'int_casa_comedor': (sitio.CASA, (6.35, 6.85, 1.65), (4.4, 0.5, 1.0), 18, -0.5),
    'int_casa_vip': (sitio.CASA, (6.85, 6.75, 1.60), (9.3, 4.5, 0.9), 18, -0.5),
    'int_casa_suite': (sitio.CASA, (10.05, 12.40, 1.60), (12.2, 9.2, 0.9), 18, -0.5),
    'int_casa_semipriv': (sitio.CASA, (4.10, 8.75, 1.60), (3.4, 13.3, 0.8), 18, -0.5),
    'int_casa_terapia': (sitio.CASA, (12.1, 2.90, 1.60), (9.6, 1.9, 0.75), 18, -0.5),
    'int_casa_talleres': (sitio.CASA, (10.60, 4.45, 1.70), (10.4, 6.9, 0.8), 18, -0.5),
    'int_casa_cocina': (sitio.CASA, (2.90, 6.30, 1.65), (0.3, 4.2, 1.0), 18, -0.3),
    'int_casa_consultorio': (sitio.CASA, (3.20, 3.40, 1.60), (0.4, 0.4, 0.9), 18, -0.3),
    'int_casa_bano': (sitio.CASA, (6.40, 8.65, 1.60), (6.3, 13.4, 0.9), 18, -0.5),
    'int_casa_recamara': (sitio.CASA, (6.60, 6.70, 4.75), (8.6, 2.2, 3.95), 18, -0.5),
    'int_gris_salonB': (sitio.GRIS, (12.20, 12.30, 1.65), (9.2, 7.0, 0.7), 18, -0.5),
    'int_gris_salonA': (sitio.GRIS, (13.50, 5.85, 1.65), (9.4, 1.0, 0.7), 18, -0.5),
    'int_gris_bano_acc': (sitio.GRIS, (2.10, 6.95, 1.60), (2.0, 9.9, 0.8), 16, -0.5),
    'int_gris_acceso': (sitio.GRIS, (1.75, 5.15, 1.60), (8.2, 5.9, 1.2), 16, -0.5),
    'int_gris_vestibulo': (sitio.GRIS, (4.85, 5.55, 1.60), (8.3, 11.6, 1.1), 16, -0.5),
    'int_gris_oficina2': (sitio.GRIS, (6.30, 6.95, 1.60), (5.3, 12.3, 0.8), 16, -0.5),
    'int_gris_hosp': (sitio.GRIS, (10.45, 7.10, 4.95), (11.4, 0.8, 3.9), 18, -0.5),
    'int_gris_hosp2': (sitio.GRIS, (11.23, 0.85, 4.85), (11.1, 7.2, 3.9), 18, -0.5),
    'int_gris_salon2': (sitio.GRIS, (7.55, 10.55, 4.85), (13.2, 7.8, 3.95), 18, -0.5),
    'int_gris_refrigerios': (sitio.GRIS, (3.95, 12.95, 4.80), (1.0, 5.0, 4.0), 16, -1.0),
    'int_gris_biblioteca': (sitio.GRIS, (2.85, 8.75, 4.85), (4.4, 9.6, 3.95), 14, -0.5),
    'int_gris_bano_s2': (sitio.GRIS, (6.20, 8.95, 4.80), (4.9, 10.6, 4.0), 14, -0.5),
    'int_gris_cocina': (sitio.GRIS, (4.40, 7.30, 4.90), (2.8, 6.1, 4.0), 14, -0.5),
}
