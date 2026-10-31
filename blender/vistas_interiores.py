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
    'int_gris_salonB': (sitio.GRIS, (9.90, 9.00, 1.65), (13.4, 11.9, 0.7), 18, -0.5),
    'int_gris_salonA': (sitio.GRIS, (8.30, 10.30, 1.65), (4.9, 12.2, 0.8), 18, -0.5),
    'int_gris_bano_acc': (sitio.GRIS, (5.65, 4.95, 1.60), (5.4, 2.7, 0.9), 16, -0.5),
    'int_gris_acceso': (sitio.GRIS, (8.30, 0.90, 1.60), (7.0, 8.5, 1.3), 18, -0.5),
    'int_gris_hosp': (sitio.GRIS, (10.85, 10.40, 4.85), (11.0, 4.3, 3.95), 18, -0.5),
    'int_gris_hosp2': (sitio.GRIS, (9.60, 6.90, 4.85), (13.3, 9.5, 3.9), 18, -0.5),
    'int_gris_salon2': (sitio.GRIS, (13.45, 0.95, 4.80), (9.0, 3.5, 3.95), 18, -0.5),
    'int_gris_refrigerios': (sitio.GRIS, (13.5, 12.75, 4.80), (4.8, 11.5, 4.1), 18, -1.3),
    'int_gris_deposito': (sitio.GRIS, (1.50, 6.05, 4.80), (4.5, 6.4, 4.0), 18, -0.5),
    'int_gris_cocina': (sitio.GRIS, (6.55, 7.05, 4.90), (4.9, 4.95, 4.0), 16, -0.5),
}
