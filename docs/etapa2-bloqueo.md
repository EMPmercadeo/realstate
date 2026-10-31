# Etapa 2 · Bloqueo de terreno, cubiertas y fachadas (30-10-2026)

Primer punto de revisión del encargo `INSTRUCCIONES_PARA_CLAUDE.md`. Materiales neutros a propósito:
se evalúa silueta, volúmenes, ventanas y cubiertas, no texturas. No se tocó `build.py`, `programa.py`,
la web ni el video: todo lo nuevo es aditivo y el estado anterior queda intacto.

## Archivos nuevos

| Archivo | Qué hace |
|---|---|
| `blender/sitio.py` | Trazo del lote sobre `docs/lote-satelite.png`, resta de las dos vías, escala provisional y marco local de cada edificio. |
| `blender/fachadas.py` | Exterior por volúmenes de la casa amarilla y del edificio gris, en su marco local. Reutilizable desde `build.py` en la etapa siguiente. |
| `blender/bloqueo.py` | Arma la escena de bloqueo y hace la vista cenital y las cuatro cámaras. |
| `blender/bloqueo_vistas.py` | Cámaras equivalentes a las cuatro fotos. |
| `blender/comparativas.py` | Arma las láminas de revisión (no necesita Blender). |
| `build/bloqueo/` | `bloqueo.blend`, `cenital.jpg`, `par_*.jpg`, `revision_etapa2.jpg`. |

Regenerar:
```
& $b -b -P blender\bloqueo.py -- --muestras 32 --ancho 1280
python blender\comparativas.py
```
(`$b` = ruta de `blender.exe`; `--solo cenital,casa_frontal` para rehacer solo algunas tomas.)
`sitio.py` usa la librería `shapely`. El Python de Blender no la trae; para correr el script en la PC hay que
instalarla una vez: `& "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -m pip install shapely`.
Para solo mirar el modelo no hace falta: abrir `build/bloqueo/bloqueo.blend`.

## Revisión contra las fotos (lo que coincide y lo que falta)

| Toma | Coincide | Falta o difiere |
|---|---|---|
| Casa · frente | Cochera adelantada con arco, columnas blancas y medallón; torre de dos niveles con balcón de cruces, dos columnas redondas y alero ancho ochavado; ala baja retirada a la derecha; cerca con pilares y portones de barrotes. | En la foto el techo de la cochera es más grande y baja más sobre el arco; faltan faroles, buzón, lámpara de araña y la celosía del portón se ve más densa. |
| Casa · patio | Cuerpo de dos niveles con ventana ancha + dos angostas arriba; porche de dos columnas con balaustrada; porche en arco a la derecha. | El porche de columnas de la foto tiene su propio techo a un agua hacia la izquierda; falta el toldo rojo y el ala baja de la izquierda se ve más larga. |
| Gris · acceso | Galería cerrada del norte con listones y paneles; fachada escalonada; remates altos de lámina por tramo; ventanitas de bloque de vidrio; aire acondicionado. | En la foto los remates son más altos y con nervaduras; la galería apoya en postes hasta el suelo con la planta baja más retirada. |
| Gris · galería | Galería abierta de postes delgados con baranda; planta baja blanca con ventanas de barrotes; retiro al norte con aire acondicionado y escalera. | La foto muestra 3 ventanas abajo (el modelo tiene más) y el cielo raso con abanicos. |

Las cuatro cámaras son aproximadas: sirven para comparar formas, no para medir.

## Supuestos (todos provisionales)

1. **Escala.** El trazo rojo incluye la C.A (noreste) y la calle de tierra (oeste). Se restaron con anchos
   de 44 px y 32 px. El polígono que queda se escaló de forma uniforme a 2.500 m²:
   `s = sqrt(2500 / área_px) = 0,117 m/px`. El trazo rojo completo equivaldría a ~2.900 m².
   Con esa escala los techos miden: casa ~15 × 14 m, garaje ~6,5 × 4,5 m, gris ~14,4 × 13,5 m,
   y las puertas y personas de las fotos encajan. No son cotas medidas.
2. **Orientación.** Se relacionaron las capturas de Street View con la imagen aérea leyendo su brújula
   (y asumiendo que la captura aérea de Google está con el norte arriba). Solo se usa para saber qué
   fachada da a qué calle; el modelo no afirma un norte geográfico.
   - Casa amarilla: frente (cochera con arco, torre con balcón, ala baja) hacia la **C.A**; garaje de
     piedra aparte, junto a la bifurcación, con su reja hacia la calle de tierra; fondo hacia el patio de grava.
   - Edificio gris: fachada escalonada hacia la **calle de tierra**; galería cerrada con listones en el
     **lado norte**; galería abierta (terraza) en el **lado este**; escalera metálica exterior al **sur**.
3. **Escalonamiento del gris.** Se siguió el contorno del satélite: el tramo sur de la fachada oeste es el
   más adelantado; el norte, el más retirado (unos 4 m). Las fotos son compatibles con esta lectura,
   pero conviene confirmarlo en sitio.
4. **Cochera y portón.** El techo rosado pequeño del satélite junto a la bifurcación se interpretó como el
   garaje de piedra (Street View lo muestra pegado a la calle de tierra). La cochera con medallón adelanta
   ~5,6 m del frente de la casa. La cerca del frente quedó retirada de la C.A (a ~1,8 m del arco de la
   cochera), con una rampa de baldosa afuera, como en la foto; el borde del lote calculado queda unos 5 m
   más afuera. Es lo primero a verificar en sitio.
5. **Balcón de la torre.** Losa rectangular con baranda de cruces y dos columnas redondas hasta un alero
   ancho con las esquinas frontales ochavadas, como se ve en las fotos. No se modeló un octágono completo.
6. **Planta alta de la casa.** Solo el cuerpo de la torre, de frente a fondo (la foto del patio muestra
   ese cuerpo de dos niveles llegando hasta el muro trasero, con tres ventanas y un balconcito en la
   esquina). La escalera interior no está resuelta (pendiente de la etapa 3).
7. **Lo que no está en esta etapa:** interiores, vegetación, vecinos, materiales reales, gazebo,
   hidroterapia y huerto (propuestas, no existentes), capacidad de camas (sigue pendiente: 24 + 3 ≠ 28).

## Confirmado por el propietario (30-10-2026)
- Orden del frente de la casa: cochera → torre → ala baja, garaje de piedra aparte a la derecha. ✔
- La galería cerrada con listones del gris mira hacia la casa amarilla. ✔
- La terraza alta del gris hoy está cerrada con verjas de piso a techo (la foto `edificio-gris.jpg` es
  anterior y la muestra abierta). Ya corregido en `fachadas.py`.
- La cochera está clara en las fotos; la posición del portón se mantiene como en el modelo.
- El recorrido final debe ser también por DENTRO de los dos edificios (etapas 3 y 4).
