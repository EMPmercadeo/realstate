# Etapa 4a · Interiores amueblados y realistas (30-10-2026)

Pedido: "darle realismo… donde van las camas, que se vean reales; los snacks, la sala de atención, los baños…
sin cambiar tanto las dimensiones". Se mantuvo la distribución de la etapa 3 y se llenaron los espacios con los
usos que organizó la propietaria (`docs/contexto-proyecto.md`), tomando como guía las imágenes "así quedará" de
Antigravity y las fotos reales (sala de conferencias, biblioteca, baños, galería, cocina del gris).

## Usos corregidos (contexto actualizado el 30-10)
- **Recepción 24 h**: sigue en la entrada principal de la casa. La foto que se había usado para "recepción"
  muestra un cuarto con cama ("la recepción que pusiste no es esa"): ese cuarto es el de puertas corredizas de
  vidrio con arcos que da al comedor, y es uno de los cuartos privados.
- Casa, **4 cuartos privados** (un huésped cada uno): **semiprivado 1** (al pasillo) y **semiprivado 2** (el de
  puertas de vidrio) que comparten el baño del pasillo; **suite** con su baño; **recámara alta** con su baño
  (antes iba a ser la oficina del gerente).
- **Gerente**: se propone en el cuarto pequeño del fondo de la planta alta (por confirmar; el contexto lo deja abierto).
- Casa: **comedor y TV**, **terapia con familiares**, **talleres** detrás de la terapia, **consultorio**,
  **cocina de acero inoxidable**, **lavandería** con la **oficinita de atención psicológica**.
- Gris: **personas encamadas** (10), **salón amarillo** (4, personas con movilidad reducida), **salones grandes de
  abajo** (2 + 6, personas que deambulan), **Oficina 1 = supervisor**, **Oficina 2 = administrativa**, **acceso** sin
  recepción, **depósito y ropería** (antes biblioteca), **cocineta y área de coffee break** en la terraza de arriba,
  **baño accesible para usuarios**, **oficina del huerto y bodega**.
- Nombres según lo que pidió la propietaria: nunca "pacientes" ni "hospitalizados"; "personas encamadas",
  "personas con movilidad reducida", "área de coffee break", "baño para huéspedes o usuarios".

## Capacidad colocada: 26 camas
| Espacio | Camas | Nota |
|---|---|---|
| Personas encamadas | 10 | Caben con la estación de enfermería a la cabeza del pasillo central (donde estaba el podio), pero justas: pasillo de ~1,0 m y 25 cm entre camas del lado de la puerta (llevan mesa puente en vez de mesita). Con 8 quedaría holgada. Luz sobre cada cama. |
| Salón amarillo | 4 | Camas de hospital con mesita; puerta en la esquina para que quepan las cuatro. |
| Salón grande 1 (abajo) | 2 | Con mesita y paso libre no caben más con las medidas estimadas. |
| Salón grande 2 (abajo) | 6 | Compensa al salón 1: abajo suman 8, como pide el programa (4 + 4). |
| Casa amarilla | 4 | Semiprivado 1 + semiprivado 2 + suite + recámara alta. |

Las medidas son proporcionales al satélite, no un levantamiento: medir en sitio antes de ofrecer la capacidad.

## Qué se agregó al modelo
- **Muebles** (modelos propios, nada comprado): camas de hospital con barandales, ruedas, cabecera y piecera de
  laminado; camas tapizadas con edredón y manta; mesitas; estación de enfermería con monitor; roperos; sillones,
  sofás y sillas; comedor de 5 puestos; mostrador de recepción con frente de listones; camillas; barras paralelas;
  bicicleta; mesa de talleres, caballete y máquina de coser; cocina industrial con campana; refrigeradora;
  fregaderos de acero y granito; lavadora y secadora; inodoros, lavamanos, tocador y duchas a ras de piso con
  barras y asiento abatible; barra de coffee break con termos, frutas y vitrina; mesas redondas; dispensadores de
  agua; plantas; cuadros; silla de ruedas y sillón reclinable.
- **Acabados**: piso cerámico beige (casa) y gris claro brillante (gris); pintura crema / blanca; salón amarillo
  pintado de amarillo; azulejo rojo con celeste arriba en los baños del gris (como en las fotos); azulejo beige
  en los baños de la casa; zócalo cerámico; guardacamillas de madera en salas y pasillos del gris; cielo raso de
  losetas 60 × 60 en el gris y liso en la casa; bloques de vidrio en las ventanas del gris.
- **Luz**: lámparas de techo y abanicos con luz real, lámparas de mesa y de pie, luminaria sobre cada cama de
  encamados, aires acondicionados, cortinas en cuartos y salas, hojas de puertas abiertas.
- **Puertas**: cada puerta interior tiene lado de giro y bisagra; la del baño accesible abre hacia el pasillo; la
  del semiprivado 2 es corrediza de vidrio con arcos.

## Prueba de recorrido con los muebles puestos
- Casa: calle → recepción → comedor → escalera → recámara alta → balcón. 32,7 m, de 0,03 a 3,15 m.
  Escalón máx. 0,20 m · altura libre mín. 2,04 m · 0 choques.
- Gris: calle → acceso → escalera → personas encamadas → área de coffee break. 37,1 m, de 0,00 a 3,21 m.
  Escalón máx. 0,20 m · altura libre mín. 2,04 m · 0 choques.

## Archivos
| Archivo | Qué hace |
|---|---|
| `blender/amueblado.py` | Lista de muebles por cuarto (posición, giro, medidas), conteo de camas y validador de choques y paso de puertas (sin Blender). |
| `blender/muebles3d.py` | Modelos 3D de cada mueble y su colocación. |
| `blender/materiales.py` | Materiales realistas de interior. |
| `blender/acabados.py` | Revestimientos, zócalos, cielos, luces, abanicos, aires, cuadros, cortinas y hojas de puertas. |
| `blender/vistas_interiores.py` | Cámaras de las 21 vistas interiores. |
| `blender/render_interiores.py` | Renderiza las vistas desde `bloqueo.blend` sin reconstruir (CPU o GPU). |
| `blender/lamina_etapa4.py` | Láminas de vistas y comparación con Antigravity. |
| `build/bloqueo/int_*.png` | Vistas interiores. |
| `build/bloqueo/interiores_gris_etapa4.jpg`, `interiores_casa_etapa4.jpg`, `comparacion_antigravity.jpg` | Láminas. |
| `build/bloqueo/planos_etapa4.jpg` | Planos amueblados. |

## Volver a renderizar en la PC (RTX 3080), PowerShell dentro de `realstate`
Solo la primera vez (instala la librería que usan los scripts dentro de Blender):
```
& "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -m pip install shapely
```
Reconstruir el modelo (≈1 min) y renderizar todas las vistas con la tarjeta de video en alta calidad:
```
$b = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $b -b -P blender\bloqueo.py -- --solo ninguno
& $b -b -P blender\render_interiores.py -- --vistas todas --muestras 128 --ancho 1920 --gpu
```
Las imágenes quedan en `build\bloqueo\int_*.png`. Para una sola vista: `--vistas int_gris_hosp`.

## Pendiente
- Confirmar con la propietaria: 10 u 8 encamados, dónde va el gerente, cuál es el cuarto de la foto con puertas de
  vidrio, baño nuevo junto a la biblioteca, dónde comen los 22 del gris. Falta la foto real de la recepción.
- Ascensor o rampa para encamados entre niveles (sigue sin resolver).
- Siguiente etapa: vegetación y materiales de fachada, exteriores (gazebo, tina de hidroterapia, huerto) y la
  caminata en el navegador (computadora y celular).
